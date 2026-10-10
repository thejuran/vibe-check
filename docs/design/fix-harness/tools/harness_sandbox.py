"""harness_sandbox.py — the containment policy every harness session runs under.

The harness grants the fix session every tool except questions, and a
disposable working directory by itself restricts nothing: an absolute-path
read of the answer keys or a write into the source checkout would simply
succeed. A read cannot be detected after the fact, so the boundary has to be
enforced while the session runs. This module states that policy once; the SDK
driver only wires it.

Where things live
-----------------
The disposable copy and the plugin snapshot live in a per-run workspace under
the per-user temp dir, OUTSIDE the source checkout. The checkout is denied with
`//`-anchored permission rules, and such a deny cannot be carved back open for
a subdirectory — a copy placed inside the checkout would be denied to the very
session that has to work in it. `make_workspace`, `snapshot_plugin` and
`build_session_settings` therefore refuse any placement under the checkout.

Three independent layers
------------------------
1. OS sandbox (Seatbelt on macOS) — wraps Bash and everything it spawns.
   `filesystem.denyRead` covers the checkout, the run's out dir, the answer
   keys and host credential files; `denyWrite` covers the plugin snapshot
   (load-bearing: the snapshot sits under the temp dir, which sandboxed Bash
   may otherwise write). `failIfUnavailable` and
   `allowUnsandboxedCommands: false` make a missing sandbox stop the session
   instead of silently running it unsandboxed.
2. Permission deny rules — the in-process file tools (Read/Edit/Write/Grep/
   Glob) are not wrapped by the OS sandbox. `Read(//…/**)` denies reads (and
   edits) of the same paths, `Edit(//snapshot/**)` keeps the snapshot
   read-only, and a tool-level `NotebookEdit` deny covers the one editing tool
   `Edit(...)` does not.
3. Path backstop (`path_allowed`) — the driver's `can_use_tool` callback
   denies any path that does not resolve inside the copy (or, read-only, the
   snapshot), lexically AND through symlinks. It catches whatever the first
   two layers miss, and it is the only layer whose denials the harness itself
   records.

The model API credentials are used by the Claude Code process, which runs
outside the sandbox; nothing here touches them.

Stdlib only. Git runs as an argv list with a timeout, never through a shell.
"""

import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import harness_fixture

CHECKOUT_ROOT = os.path.realpath(
    os.path.join(str(harness_fixture.PLUGIN_SCRIPTS_DIR), "..", "..", ".."))
KEYS_DIR = os.path.realpath(str(harness_fixture.KEYS_DIR))

PROTECTED_CREDENTIAL_PATHS = (
    "~/.ssh", "~/.aws", "~/.config/gh", "~/.netrc", "~/.gnupg",
    "~/.claude/.credentials.json", "~/.claude.json",
)
# Credential entries that name a single file get a plain rule, directories
# get a `/**` rule.
_CREDENTIAL_FILES = frozenset({"~/.netrc", "~/.claude/.credentials.json",
                               "~/.claude.json"})

GIT_TIMEOUT = 60
SNAPSHOT_SKIP_DIRS = frozenset({"__pycache__", ".pytest_cache", ".venv"})
SNAPSHOT_SKIP_SUFFIXES = (".pyc",)

PluginSnapshot = collections.namedtuple(
    "PluginSnapshot", "path tree_sha256 source_path git_sha dirty")
Decision = collections.namedtuple("Decision", "ok kind path")


class SandboxError(RuntimeError):
    """The containment policy cannot be established for these paths."""


def _is_under(path, root):
    """True when `path` equals `root` or lies below it (lexical, no I/O)."""
    root = root.rstrip("/") or "/"
    if root == "/":
        return path.startswith("/")
    return path == root or path.startswith(root + "/")


def _git(checkout_root, *args):
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        proc = subprocess.run(["git", "-C", checkout_root, *args], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=GIT_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SandboxError("git %s could not run: %s" % (args[0], exc)) from exc
    if proc.returncode != 0:
        raise SandboxError("git %s failed: %s" % (args[0], proc.stderr.strip()))
    return proc.stdout


# ---------------------------------------------------------------------------
# Workspace and plugin snapshot
# ---------------------------------------------------------------------------

def make_workspace(prefix="fixharness-"):
    """Create a per-run workspace under the temp dir; return its realpath.

    On macOS the temp dir is under `/var/folders`, which resolves to
    `/private/var/...`; the realpath is what the session's cwd, the plugin's
    repo-root lookup and the path backstop all see.
    """
    path = os.path.realpath(tempfile.mkdtemp(prefix=prefix,
                                             dir=tempfile.gettempdir()))
    claude_home = os.path.realpath(os.path.expanduser("~/.claude"))
    if _is_under(path, CHECKOUT_ROOT) or _is_under(path, claude_home):
        shutil.rmtree(path, ignore_errors=True)
        raise SandboxError("workspace would sit inside a protected tree: %s"
                           % path)
    return path


def _snapshot_ignore(_dir, names):
    return [n for n in names
            if n in SNAPSHOT_SKIP_DIRS or n.endswith(SNAPSHOT_SKIP_SUFFIXES)]


def _tree_sha256(top):
    entries = []
    for root, dirs, files in os.walk(top):
        dirs.sort()
        for name in files:
            full = os.path.join(root, name)
            entries.append((os.path.relpath(full, top).replace(os.sep, "/"),
                            full))
    digest = hashlib.sha256()
    for rel, full in sorted(entries):
        with open(full, "rb") as fh:
            data = fh.read()
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(str(len(data)).encode("ascii") + b"\0")
        digest.update(data)
    return digest.hexdigest()


def tree_sha256(top):
    """sha256 over the sorted (relative path, bytes) pairs under `top`."""
    return _tree_sha256(top)


def snapshot_plugin(source_dir, dest, checkout_root=None):
    """Copy the plugin to `<dest>/plugin` and record where it came from."""
    checkout_root = checkout_root or CHECKOUT_ROOT
    source_dir = os.path.realpath(source_dir)
    path = os.path.join(os.path.realpath(dest), "plugin")
    if _is_under(path, os.path.realpath(checkout_root)):
        raise SandboxError("plugin snapshot would sit inside the checkout: %s"
                           % path)
    git_sha = _git(checkout_root, "rev-parse", "HEAD").strip()
    dirty = bool(_git(checkout_root, "status", "--porcelain", "--",
                      source_dir).strip())
    shutil.copytree(source_dir, path, ignore=_snapshot_ignore)
    return PluginSnapshot(path, _tree_sha256(path), source_dir, git_sha, dirty)


# ---------------------------------------------------------------------------
# Session settings
# ---------------------------------------------------------------------------

def _check_path(value, what):
    if (not isinstance(value, str) or not os.path.isabs(value)
            or os.path.normpath(value) != value
            or os.path.realpath(value) != value):
        raise SandboxError("%s must be an absolute, normalised realpath: %r"
                           % (what, value))
    return value


def _abs_rule(tool, path):
    return "%s(//%s/**)" % (tool, path.lstrip("/"))


def _credential_rule(entry):
    if entry in _CREDENTIAL_FILES:
        return "Read(%s)" % entry
    return "Read(%s/**)" % entry


def build_session_settings(copy_root, snapshot_path, out_dir,
                           checkout_root=None, keys_dir=None):
    """Return the settings dict passed inline to the session (flag layer).

    `autoAllowBashIfSandboxed` is false on purpose: every Bash call still
    reaches `can_use_tool`, so the driver logs the full tool transcript (the
    sandbox enforces; the callback records).
    """
    checkout_root = checkout_root or CHECKOUT_ROOT
    keys_dir = keys_dir or KEYS_DIR
    for value, what in ((copy_root, "copy_root"),
                        (snapshot_path, "snapshot_path"),
                        (out_dir, "out_dir"),
                        (checkout_root, "checkout_root"),
                        (keys_dir, "keys_dir")):
        _check_path(value, what)
    for value, what in ((copy_root, "copy_root"),
                        (snapshot_path, "snapshot_path")):
        if _is_under(value, checkout_root):
            raise SandboxError("%s is inside the checkout, which is denied "
                               "and cannot be carved open: %s" % (what, value))
    return {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": False,
            "excludedCommands": [],
            "filesystem": {
                "denyRead": [checkout_root, out_dir, keys_dir,
                             *PROTECTED_CREDENTIAL_PATHS],
                "allowRead": [copy_root, snapshot_path],
                "denyWrite": [snapshot_path],
            },
            "network": {"allowedDomains": [], "strictAllowlist": True},
        },
        "permissions": {
            "deny": [
                _abs_rule("Read", checkout_root),
                _abs_rule("Read", out_dir),
                _abs_rule("Read", keys_dir),
                *[_credential_rule(e) for e in PROTECTED_CREDENTIAL_PATHS],
                _abs_rule("Edit", snapshot_path),
                "NotebookEdit",
            ],
            "defaultMode": "default",
        },
    }


def _policy_paths(settings):
    """Recover the run-specific paths from a settings dict built above."""
    fs = settings["sandbox"]["filesystem"]
    return {"checkout": fs["denyRead"][0], "out": fs["denyRead"][1],
            "keys": fs["denyRead"][2], "copy": fs["allowRead"][0],
            "snapshot": fs["allowRead"][1]}


def settings_is_fail_closed(settings):
    """True only when every containment lock is present in `settings`."""
    try:
        sb = settings["sandbox"]
        fs = sb["filesystem"]
        deny = settings["permissions"]["deny"]
        paths = _policy_paths(settings)
        for key in ("checkout", "out", "keys", "copy", "snapshot"):
            if not isinstance(paths[key], str) or not os.path.isabs(paths[key]):
                return False
        return bool(
            sb.get("enabled") is True
            and sb.get("failIfUnavailable") is True
            and sb.get("allowUnsandboxedCommands") is False
            and sb.get("excludedCommands") == []
            and paths["checkout"] in fs["denyRead"]
            and paths["out"] in fs["denyRead"]
            and paths["keys"] in fs["denyRead"]
            and all(p in fs["denyRead"] for p in PROTECTED_CREDENTIAL_PATHS)
            and paths["snapshot"] in fs["denyWrite"]
            and _abs_rule("Read", paths["checkout"]) in deny
            and _abs_rule("Read", paths["out"]) in deny
            and _abs_rule("Read", paths["keys"]) in deny
            and all(_credential_rule(e) in deny
                    for e in PROTECTED_CREDENTIAL_PATHS)
            and _abs_rule("Edit", paths["snapshot"]) in deny
            and "NotebookEdit" in deny
            and not _is_under(paths["copy"], paths["checkout"])
            and not _is_under(paths["snapshot"], paths["checkout"]))
    except (KeyError, IndexError, TypeError, AttributeError):
        return False


def settings_fingerprint(settings):
    """sha256 of the policy with the run-specific paths replaced by tokens.

    Stable across runs; changes whenever the policy itself changes. The probe
    record pins it so a policy change invalidates the probe.
    """
    text = json.dumps(settings, sort_keys=True)
    try:
        paths = _policy_paths(settings)
    except (KeyError, IndexError, TypeError):
        paths = {}
    tokens = {"copy": "<COPY>", "snapshot": "<SNAPSHOT>", "out": "<OUT>",
              "checkout": "<CHECKOUT>"}
    pairs = [(paths[k], tokens[k]) for k in tokens
             if isinstance(paths.get(k), str) and len(paths[k]) > 1]
    # Longest first: the out dir sits inside the checkout.
    for value, token in sorted(pairs, key=lambda p: -len(p[0])):
        bare = re.escape(value.lstrip("/"))
        text = re.sub(r"/{1,2}" + bare + r'(?=[/"*)]|$)', token, text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Path backstop for file tools
# ---------------------------------------------------------------------------

READ_ONLY_TOOLS = frozenset({"Read", "Grep", "Glob"})
_PATH_FIELD = {"Read": "file_path", "Edit": "file_path", "Write": "file_path",
               "MultiEdit": "file_path", "NotebookEdit": "notebook_path",
               "Grep": "path", "Glob": "path"}
_GENERIC_PATH_FIELDS = ("file_path", "path", "notebook_path")
_GLOB_CHARS = re.compile(r"[*?\[{]")
_SEVERITY = {"copy": 0, "snapshot": 0, "invalid": 1, "outside": 2,
             "protected": 3}


def protected_roots(out_dir, checkout_root=None, keys_dir=None):
    """The roots the backstop treats as protected for one run."""
    return (checkout_root or CHECKOUT_ROOT, out_dir, keys_dir or KEYS_DIR,
            *[os.path.expanduser(p) for p in PROTECTED_CREDENTIAL_PATHS])


def _normalise(raw, copy_root):
    """Absolute, lexically normalised form of a tool path (no I/O)."""
    path = os.path.expanduser(raw) if raw.startswith("~") else raw
    if not os.path.isabs(path):
        path = os.path.join(copy_root, path)
    return os.path.normpath(path)


def _glob_prefix(base, pattern):
    """The literal directory a Glob search starts from."""
    joined = _normalise(pattern, base)
    parts = joined.split("/")
    for i, part in enumerate(parts):
        if _GLOB_CHARS.search(part):
            return "/".join(parts[:i]) or "/"
    return joined


def _classify_path(tool_name, lexical, copy_root, snapshot_path, roots):
    real = os.path.realpath(lexical)
    for root in roots:
        root_lex = os.path.normpath(os.path.expanduser(root))
        for candidate_root in {root_lex, os.path.realpath(root_lex)}:
            if _is_under(lexical, candidate_root) \
                    or _is_under(real, candidate_root):
                return Decision(False, "protected", lexical)
    if _is_under(lexical, copy_root) \
            and _is_under(real, os.path.realpath(copy_root)):
        return Decision(True, "copy", lexical)
    if _is_under(lexical, snapshot_path) \
            and _is_under(real, os.path.realpath(snapshot_path)):
        return Decision(tool_name in READ_ONLY_TOOLS, "snapshot", lexical)
    return Decision(False, "outside", lexical)


def path_allowed(tool_name, input_data, copy_root, snapshot_path,
                 protected_roots):
    """Bound a file tool's path to the copy (or, read-only, the snapshot).

    Both the lexical `normpath` and the `realpath` must resolve inside the
    allowed tree, so `..` traversal and symlinks planted in the copy cannot
    escape. Anything under a protected root on EITHER side is `protected`.
    Metadata only: nothing is read beyond `realpath`.
    """
    data = input_data if isinstance(input_data, dict) else {}
    if tool_name in _PATH_FIELD:
        fields = (_PATH_FIELD[tool_name],)
    else:
        fields = tuple(f for f in _GENERIC_PATH_FIELDS if f in data)
        if not fields:
            return Decision(True, "no-path", None)
    candidates = []
    for field in fields:
        raw = data.get(field)
        if raw is None and tool_name in ("Grep", "Glob"):
            raw = copy_root
        if not isinstance(raw, str) or not raw:
            return Decision(False, "invalid", None)
        candidates.append(_normalise(raw, copy_root))
    if tool_name == "Glob":
        pattern = data.get("pattern")
        if not isinstance(pattern, str):
            return Decision(False, "invalid", candidates[0])
        candidates.append(_glob_prefix(candidates[0], pattern))
    decisions = [_classify_path(tool_name, c, copy_root, snapshot_path,
                                protected_roots) for c in candidates]
    worst = decisions[0]
    for d in decisions[1:]:
        if not d.ok and (worst.ok or _SEVERITY[d.kind] > _SEVERITY[worst.kind]):
            worst = d
    if worst.ok:
        return decisions[0]
    return Decision(False, worst.kind, decisions[0].path)


# ---------------------------------------------------------------------------
# Launch preflight
# ---------------------------------------------------------------------------

SEATBELT = "/usr/bin/sandbox-exec"
UNSUPPORTED_HOST_PROBLEM = "unsupported host for the enforced sandbox"
SEATBELT_MISSING_PROBLEM = "Seatbelt (/usr/bin/sandbox-exec) is not available"
SETTINGS_OPEN_PROBLEM = "session settings are not fail-closed"
SETTINGS_MISMATCH_PROBLEM = ("session settings were built for a different "
                             "copy or plugin snapshot")
PROBE_STALE_PROBLEM = ("sandbox probe missing or stale — run fixharness.py "
                       "probe-sandbox")

# Replaced below by the probe section; preflight reads it at call time.
PROBE_REQUIRED_CHECKS = ("preconditions_hold", "script_ran")


def _fingerprint_matches(record, settings):
    return record.get("settings_fingerprint") == settings_fingerprint(settings)


def _probe_record_ok(record_path, settings, sdk_version):
    try:
        with open(record_path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError):
        return False
    if not isinstance(record, dict):
        return False
    checks = record.get("checks")
    return bool(
        record.get("passed") is True
        and record.get("sdk_version") == sdk_version
        and _fingerprint_matches(record, settings)
        and isinstance(checks, dict) and checks
        and set(checks) >= set(PROBE_REQUIRED_CHECKS)
        and all(v is True for v in checks.values()))


def preflight(copy_root, snapshot_path, settings, probe_record_path,
              sdk_version):
    """Return the reasons a session must not launch ([] = launch)."""
    problems = []
    if sys.platform != "darwin":
        problems.append(UNSUPPORTED_HOST_PROBLEM)
    elif not os.access(SEATBELT, os.X_OK):
        problems.append(SEATBELT_MISSING_PROBLEM)
    if not settings_is_fail_closed(settings):
        problems.append(SETTINGS_OPEN_PROBLEM)
    else:
        paths = _policy_paths(settings)
        if paths["copy"] != copy_root or paths["snapshot"] != snapshot_path:
            problems.append(SETTINGS_MISMATCH_PROBLEM)
    for value, what in ((copy_root, "copy"), (snapshot_path, "plugin snapshot")):
        if not isinstance(value, str) or not os.path.isabs(value) \
                or os.path.realpath(value) != value:
            problems.append("%s path is not a realpath: %r" % (what, value))
        elif _is_under(value, CHECKOUT_ROOT):
            problems.append("%s is inside the checkout: %s" % (what, value))
    if not _probe_record_ok(probe_record_path, settings, sdk_version):
        problems.append(PROBE_STALE_PROBLEM)
    return problems
