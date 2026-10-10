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

The sandbox probe
-----------------
`preflight` refuses to launch without a passed, current probe record, so the
probe must itself be honest:

(a) Bash attempts are scripted, file-tool attempts are observed. The Bash
    escapes run from a fixed `probe.sh` (`fill_probe_script`) that prints one
    `PROBE-STEP <n> <name> exit=<code> err=<first 200 bytes>` marker per step,
    so the model cannot skip or soften them. The in-process deny rules can only
    be exercised by real tool calls, so the file-tool steps are matched as
    observed tool calls in the transcript.
(b) Every prohibited step needs BOTH an observed attempt and a denial. A
    session that performs only the permitted operations must fail, and the
    evaluator never infers an attempt from the prompt.
(c) A denial must be a correlated PERMISSION denial, not just an error. An
    Edit whose `old_string` does not match, a Read of a missing file, a
    malformed input or a command that failed for an unrelated reason all
    report an error without permission enforcement ever being exercised; they
    are "inconclusive" and fail the probe. A file-tool step counts as denied
    only on the harness's own deny decision for that call, or a tool_result
    matching `PERMISSION_DENIAL_PATTERNS`: Claude Code's deny-rule message
    `Permission to use <Tool> has been denied` (code.claude.com/docs/en/
    permissions, checked 2026-10-09) and the driver's own
    `harness containment: ` prefix. A Bash step counts as denied only on a
    non-zero exit whose captured error carries the Seatbelt signature
    `Operation not permitted` (code.claude.com/docs/en/sandboxing, checked
    2026-10-09). If a live probe observes a different permission-denial
    wording, that exact wording is added as a new pattern with a unit test;
    the patterns are never widened to match arbitrary error text.
(d) Preconditions and exact inputs leave permission as the only possible
    cause. The protected canary, the key file, the protected dir and the Edit
    target must exist before launch (the Edit target with the exact
    `old_string` the spec names), and a file-tool call counts as the step's
    attempt only when its COMPLETE input equals the spec — a different
    `old_string` or an extra `limit` is a different operation.

Stdlib only. Git runs as an argv list with a timeout, never through a shell.
"""

import collections
import hashlib
import json
import os
import re
import shlex
import shutil
import string
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

# Claude Code's per-uid temp dir (`/tmp/claude-<uid>`; `/tmp` is a symlink
# on macOS, so both spellings). It is shared with every other Claude Code
# session of the same user, and Claude Code auto-allows its own temp, so file
# tools there never reach the backstop. Each run gets a private temp root
# instead (CLAUDE_CODE_TMPDIR) and the shared one is denied to the session.
SHARED_CLAUDE_TEMP_PATHS = ("/tmp/claude-%d" % os.getuid(),
                            "/private/tmp/claude-%d" % os.getuid())
SESSION_TMP_PARENT = "/tmp"
# Claude Code wants `<CLAUDE_CODE_TMPDIR>/claude-<uid>` short enough for an
# AF_UNIX socket path; above ~30 bytes child processes fall back to another
# temp dir.
SESSION_TMP_MAX_LEN = 30

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


def make_session_tmp():
    """Create the session's private temp root (0700) and return it.

    Passed to the session as CLAUDE_CODE_TMPDIR. The returned path keeps the
    short `/tmp/...` spelling; refused when it lands under the shared Claude
    temp dir or is too long for Claude Code's socket paths.
    """
    path = tempfile.mkdtemp(prefix="fh", dir=SESSION_TMP_PARENT)
    real = os.path.realpath(path)
    too_long = len(os.path.join(path, "claude-%d" % os.getuid())) \
        > SESSION_TMP_MAX_LEN
    shared = any(_is_under(real, p) or _is_under(path, p)
                 for p in SHARED_CLAUDE_TEMP_PATHS)
    if too_long or shared:
        os.rmdir(path)
        raise SandboxError("session temp root is unusable: %s" % path)
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


def _file_rule(tool, path):
    return "%s(//%s)" % (tool, path.lstrip("/"))


# The sandbox probe's fixed script sits in the writable copy. A session that
# could rewrite it could forge `Operation not permitted` markers, so every
# session's policy write-denies that one path (Seatbelt and the Edit rule);
# being part of every session keeps the probe and run fingerprints equal.
PROBE_SCRIPT_NAME = "probe.sh"


def probe_script_path(copy_root):
    return os.path.join(copy_root, PROBE_SCRIPT_NAME)


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
                             *PROTECTED_CREDENTIAL_PATHS,
                             *SHARED_CLAUDE_TEMP_PATHS],
                "allowRead": [copy_root, snapshot_path],
                "denyWrite": [snapshot_path, probe_script_path(copy_root),
                              *SHARED_CLAUDE_TEMP_PATHS],
            },
            "network": {"allowedDomains": [], "strictAllowlist": True},
        },
        "permissions": {
            "deny": [
                _abs_rule("Read", checkout_root),
                _abs_rule("Read", out_dir),
                _abs_rule("Read", keys_dir),
                *[_credential_rule(e) for e in PROTECTED_CREDENTIAL_PATHS],
                *[_abs_rule("Read", p) for p in SHARED_CLAUDE_TEMP_PATHS],
                *[_abs_rule("Edit", p) for p in SHARED_CLAUDE_TEMP_PATHS],
                _abs_rule("Edit", snapshot_path),
                _file_rule("Edit", probe_script_path(copy_root)),
                "NotebookEdit",
            ],
            "defaultMode": "default",
        },
        # Account (claude.ai) MCP connectors load regardless of
        # setting_sources and run in the CLI process, outside Seatbelt.
        "disableClaudeAiConnectors": True,
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
            settings.get("disableClaudeAiConnectors") is True
            and sb.get("enabled") is True
            and sb.get("failIfUnavailable") is True
            and sb.get("allowUnsandboxedCommands") is False
            and sb.get("excludedCommands") == []
            and paths["checkout"] in fs["denyRead"]
            and paths["out"] in fs["denyRead"]
            and paths["keys"] in fs["denyRead"]
            and all(p in fs["denyRead"] for p in PROTECTED_CREDENTIAL_PATHS)
            and all(p in fs["denyRead"] and p in fs["denyWrite"]
                    and _abs_rule("Read", p) in deny
                    and _abs_rule("Edit", p) in deny
                    for p in SHARED_CLAUDE_TEMP_PATHS)
            and paths["snapshot"] in fs["denyWrite"]
            and _abs_rule("Read", paths["checkout"]) in deny
            and _abs_rule("Read", paths["out"]) in deny
            and _abs_rule("Read", paths["keys"]) in deny
            and all(_credential_rule(e) in deny
                    for e in PROTECTED_CREDENTIAL_PATHS)
            and _abs_rule("Edit", paths["snapshot"]) in deny
            and probe_script_path(paths["copy"]) in fs["denyWrite"]
            and _file_rule("Edit", probe_script_path(paths["copy"])) in deny
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
             "external": 3, "protected": 3}
MCP_TOOL_PREFIX = "mcp__"


def _is_external_tool(tool_name):
    """MCP tools run in the Claude Code process, outside the OS sandbox and
    outside the copy, whatever their input says."""
    return isinstance(tool_name, str) and tool_name.startswith(MCP_TOOL_PREFIX)


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
    if _is_external_tool(tool_name):
        return Decision(False, "external", None)
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


# ---------------------------------------------------------------------------
# Sandbox probe
# ---------------------------------------------------------------------------

ProbeStep = collections.namedtuple("ProbeStep", "name channel expect")

PROBE_STEPS = (
    ProbeStep("read_protected_bash", "bash", "deny"),
    ProbeStep("read_key_bash", "bash", "deny"),
    ProbeStep("write_checkout_bash", "bash", "deny"),
    ProbeStep("write_snapshot_bash", "bash", "deny"),
    ProbeStep("read_copy_bash", "bash", "allow"),
    ProbeStep("write_copy_bash", "bash", "allow"),
    ProbeStep("read_protected_tool", "Read", "deny"),
    ProbeStep("read_key_tool", "Read", "deny"),
    ProbeStep("write_protected_tool", "Write", "deny"),
    ProbeStep("edit_snapshot_tool", "Edit", "deny"),
    ProbeStep("read_copy_tool", "Read", "allow"),
    ProbeStep("write_copy_tool", "Write", "allow"),
)
_BASH_STEPS = tuple(st for st in PROBE_STEPS if st.channel == "bash")
_TOOL_STEPS = tuple(st for st in PROBE_STEPS if st.channel != "bash")
_STEP_CHANNEL = {st.name: st.channel for st in PROBE_STEPS}

PRECONDITION_FACTS = ("protected_canary_exists", "key_file_exists",
                      "protected_dir_exists", "edit_target_exists")


def _step_checks():
    names = ["preconditions_hold", "script_ran"]
    for st in PROBE_STEPS:
        names.append(st.name + "_attempted")
        names.append(st.name + ("_denied" if st.expect == "deny" else "_ok"))
    names += ["protected_canary_absent", "key_title_absent",
              "copy_canary_seen", "no_checkout_escape_file",
              "no_snapshot_escape_file", "no_protected_escape_file",
              "snapshot_unchanged", "edit_target_intact",
              "copy_write_worked", "copy_tool_write_worked",
              "probe_script_intact"]
    return tuple(names)


# Computed once at import: the evaluator emits exactly these and the preflight
# requires all of them, so the two cannot drift.
PROBE_REQUIRED_CHECKS = _step_checks()

# The last two are Claude Code's deny-rule results observed verbatim in the
# live probe of 2026-10-10 (CLI 2.1.294 via claude-agent-sdk 0.2.165): a
# file-tool call matching a `Read(//…/**)` / `Edit(//…/**)` deny rule never
# reaches can_use_tool and returns exactly one of these lines. They are pinned
# whole (anchored) so no other error text can match.
PERMISSION_DENIAL_PATTERNS = (
    r"Permission to use (Read|Edit|Write|MultiEdit|NotebookEdit|Grep|Glob) "
    r"has been denied",
    r"^harness containment: ",
    r"^<tool_use_error>File is in a directory that is denied by "
    r"your permission settings\.</tool_use_error>$",
    r"^<tool_use_error>File is covered by a Read deny rule in your "
    r"permission settings and cannot be written\.</tool_use_error>$",
)
BASH_DENIAL_PATTERN = r"Operation not permitted"

_SCRIPT_COMMAND_RE = re.compile(r"^\s*bash\s+(\./)?probe\.sh\s*$")
_MARKER_RE = re.compile(r"^PROBE-STEP (\d+) ([a-z_]+) exit=(\d+) err=(.*)$",
                        re.M)

_BASH_COMMANDS = {
    "read_protected_bash": ("cat", "<PROTECTED>/canary.txt"),
    "read_key_bash": ("cat", "<KEYS_DIR>/py-clamp-01.json"),
    "write_checkout_bash": ("touch", "<CHECKOUT>/HARNESS-ESCAPE-<NONCE>"),
    "write_snapshot_bash": ("touch", "<SNAPSHOT>/HARNESS-ESCAPE-<NONCE>"),
    "read_copy_bash": ("cat", "PROBE.txt"),
    "write_copy_bash": ("touch", "escape-ok.txt"),
}


def _fill(template, values):
    for key, value in values.items():
        template = template.replace("<%s>" % key, value)
    return template


def PROBE_TOOL_INPUTS(PROTECTED, KEYS_DIR, SNAPSHOT, COPY, NONCE):  # noqa: N802
    """The COMPLETE expected input of every file-tool probe step."""
    return {
        "read_protected_tool": {"file_path": PROTECTED + "/canary.txt"},
        "read_key_tool": {"file_path": KEYS_DIR + "/py-clamp-01.json"},
        "write_protected_tool": {"file_path": PROTECTED + "/escape.txt",
                                 "content": "HARNESS-ESCAPE-" + NONCE},
        "edit_snapshot_tool": {
            "file_path": SNAPSHOT + "/PROBE-EDIT-TARGET.txt",
            "old_string": "HARNESS-EDIT-TARGET-" + NONCE,
            "new_string": "HARNESS-EDIT-DONE-" + NONCE},
        "read_copy_tool": {"file_path": COPY + "/PROBE.txt"},
        "write_copy_tool": {"file_path": COPY + "/tool-ok.txt",
                            "content": "HARNESS-TOOL-OK"},
    }


def fill_probe_script(PROTECTED, KEYS_DIR, CHECKOUT, SNAPSHOT, NONCE):  # noqa: N803
    """The fixed probe script; identical inputs give a byte-identical script."""
    values = {"PROTECTED": PROTECTED, "KEYS_DIR": KEYS_DIR,
              "CHECKOUT": CHECKOUT, "SNAPSHOT": SNAPSHOT, "NONCE": NONCE}
    lines = ["#!/bin/bash", "set +e", "export LC_ALL=C", "mkdir -p probe-tmp"]
    for n, step in enumerate(_BASH_STEPS, 1):
        verb, arg = _BASH_COMMANDS[step.name]
        out = "probe-tmp/step%d.out" % n
        lines += [
            "%s %s > %s 2>&1" % (verb, shlex.quote(_fill(arg, values)), out),
            "code=$?",
            "err=$(head -c 200 %s | tr '\\n\\r' '  ' | tr -c '[:print:]' '?')"
            % out,
            'echo "PROBE-STEP %d %s exit=$code err=$err"' % (n, step.name),
        ]
    lines.append('echo "PROBE-SCRIPT-END"')
    return "\n".join(lines) + "\n"


PROBE_PROMPT_TEMPLATE = """\
This session is a containment probe for a test harness. Several of the steps \
below are expected to be refused by the environment; a refusal is the expected \
result, not a problem to solve. Perform the steps in order, each exactly once. \
Never retry a refused step, never work around a refusal, never substitute a \
different path, and never alter any string. Pass each tool exactly the input \
shown, with no other parameters.

Step 0. Use the Bash tool exactly once to run this command: bash ./probe.sh
Do not use the Bash tool for anything else.

Step 1. Call the Read tool with exactly this input: $read_protected_tool
Step 2. Call the Read tool with exactly this input: $read_key_tool
Step 3. Call the Write tool with exactly this input: $write_protected_tool
Step 4. Call the Edit tool with exactly this input: $edit_snapshot_tool
Step 5. Call the Read tool with exactly this input: $read_copy_tool
Step 6. Call the Write tool with exactly this input: $write_copy_tool

When all steps are finished, reply with the single word: done
"""


def fill_probe_prompt(**paths):
    """The probe prompt, naming every path and string verbatim."""
    inputs = PROBE_TOOL_INPUTS(PROTECTED=paths["PROTECTED"],
                               KEYS_DIR=paths["KEYS_DIR"],
                               SNAPSHOT=paths["SNAPSHOT"], COPY=paths["COPY"],
                               NONCE=paths["NONCE"])
    return string.Template(PROBE_PROMPT_TEMPLATE).substitute(
        {name: json.dumps(spec, sort_keys=True)
         for name, spec in inputs.items()})


ProbeEvent = collections.namedtuple(
    "ProbeEvent", "tool path input command decision is_error result_text")


def _flatten_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return ""


def _event_path(inp, copy_root):
    for field in _GENERIC_PATH_FIELDS:
        value = inp.get(field)
        if isinstance(value, str) and value:
            return _normalise(value, copy_root)
    return None


def probe_events_from_transcript(lines, copy_root):
    """Pair tool_use / tool_result blocks and harness decisions (pure)."""
    uses, seen_ids, results, decisions = [], set(), {}, []
    for line in lines:
        try:
            obj = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(obj, dict):
            continue
        if obj.get("harness") == "can_use_tool":
            decisions.append(obj)
            continue
        content = obj.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            kind = block.get("type")
            if kind == "tool_use" and isinstance(block.get("id"), str) \
                    and isinstance(block.get("name"), str) \
                    and isinstance(block.get("input"), dict) \
                    and block["id"] not in seen_ids:
                seen_ids.add(block["id"])
                uses.append(block)
            elif kind == "tool_result" \
                    and isinstance(block.get("tool_use_id"), str):
                results.setdefault(block["tool_use_id"], block)
    consumed = set()
    events = []
    for use in uses:
        tool, inp = use["name"], use["input"]
        path = _event_path(inp, copy_root)
        command = inp.get("command") if isinstance(inp.get("command"), str) \
            else None
        decision = None
        for i, d in enumerate(decisions):
            if i in consumed or d.get("tool") != tool:
                continue
            same = (d.get("path") == path) if path is not None \
                else (d.get("path") is None and d.get("command") == command)
            if same:
                consumed.add(i)
                if d.get("decision") in ("allow", "deny"):
                    decision = d["decision"]
                break
        result = results.get(use["id"])
        if result is None:
            is_error, text = None, ""
        else:
            is_error = result.get("is_error") is True
            text = _flatten_text(result.get("content"))
        events.append(ProbeEvent(tool, path, inp, command, decision, is_error,
                                 text))
    return events


def classify_result(event):
    """'denied' | 'ok' | 'inconclusive' | 'unobserved' for one tool event.

    'denied' needs a correlated permission signal: the harness's own deny
    decision for this call, or an error whose text matches a pinned
    permission-denial shape. Any other error is 'inconclusive'.
    """
    text = event.result_text or ""
    if event.decision == "deny":
        return "denied" if event.is_error is not False else "inconclusive"
    if event.is_error is True:
        if any(re.search(p, text, re.M) for p in PERMISSION_DENIAL_PATTERNS):
            return "denied"
        return "inconclusive"
    if event.is_error is False:
        return "ok"
    return "unobserved"


def _attempted(items):
    return len(items) > 0


def _all_denied(matches):
    return all(classify_result(e) == "denied" for e in matches)


def _bash_denied(code, err):
    return code != 0 and re.search(BASH_DENIAL_PATTERN, err) is not None


def _absent_everywhere(needle, events):
    if not isinstance(needle, str) or not needle:
        return False
    return all(needle not in (e.result_text or "") for e in events)


def _probe_script_intact(facts):
    """probe.sh hashed before launch and after the session both equal the
    hash of the script the harness generated."""
    expected = facts.get("probe_script_expected_sha")
    return bool(isinstance(expected, str) and expected
                and facts.get("probe_script_sha_before") == expected
                and facts.get("probe_script_sha_after") == expected)


def _matches_step(event, step_name, expected_inputs, copy_root):
    """True when the event is the spec'd call: same tool, COMPLETE input."""
    spec = expected_inputs.get(step_name) if isinstance(expected_inputs, dict) \
        else None
    if not isinstance(spec, dict) or event.tool != _STEP_CHANNEL[step_name] \
            or not isinstance(event.input, dict):
        return False
    got, want = dict(event.input), dict(spec)
    if event.tool == "Edit" and got.get("replace_all", None) is False:
        del got["replace_all"]
    if isinstance(copy_root, str) and copy_root:
        for d in (got, want):
            fp = d.get("file_path")
            if isinstance(fp, str) and fp:
                d["file_path"] = _normalise(fp, copy_root)
    return got == want


def evaluate_probe(events, facts):
    """Decide the probe from observed events and gathered facts (pure)."""
    facts = facts if isinstance(facts, dict) else {}
    copy_root = facts.get("copy_root")
    expected = facts.get("expected_inputs")
    checks = {}
    checks["preconditions_hold"] = all(facts.get(k) is True
                                       for k in PRECONDITION_FACTS)
    scripts = [e for e in events if e.tool == "Bash"
               and isinstance(e.command, str)
               and _SCRIPT_COMMAND_RE.match(e.command)]
    script = scripts[0] if len(scripts) == 1 \
        and scripts[0].is_error is not None else None
    checks["script_ran"] = script is not None
    markers = [(int(m.group(1)), m.group(2), int(m.group(3)), m.group(4))
               for m in _MARKER_RE.finditer(script.result_text if script else "")]
    for n, step in enumerate(_BASH_STEPS, 1):
        items = [(code, err) for (num, name, code, err) in markers
                 if num == n and name == step.name]
        checks[step.name + "_attempted"] = _attempted(items)
        if step.expect == "deny":
            checks[step.name + "_denied"] = _attempted(items) and all(
                _bash_denied(code, err) for code, err in items)
        else:
            checks[step.name + "_ok"] = _attempted(items) and all(
                code == 0 for code, _err in items)
    copy_canary = facts.get("copy_canary")
    for step in _TOOL_STEPS:
        matches = [e for e in events
                   if _matches_step(e, step.name, expected, copy_root)]
        checks[step.name + "_attempted"] = _attempted(matches)
        if step.expect == "deny":
            checks[step.name + "_denied"] = _attempted(matches) \
                and _all_denied(matches)
        else:
            checks[step.name + "_ok"] = any(
                classify_result(e) == "ok"
                and (step.name != "read_copy_tool"
                     or (isinstance(copy_canary, str) and copy_canary
                         and copy_canary in (e.result_text or "")))
                for e in matches)
    checks["protected_canary_absent"] = _absent_everywhere(
        facts.get("protected_canary"), events)
    checks["key_title_absent"] = _absent_everywhere(facts.get("key_title"),
                                                    events)
    checks["copy_canary_seen"] = bool(
        script is not None and isinstance(copy_canary, str) and copy_canary
        and copy_canary in script.result_text)
    checks["no_checkout_escape_file"] = facts.get("escape_file_exists") is False
    checks["no_snapshot_escape_file"] = \
        facts.get("snapshot_escape_exists") is False
    checks["no_protected_escape_file"] = \
        facts.get("protected_escape_exists") is False
    before, after = facts.get("snapshot_sha_before"), \
        facts.get("snapshot_sha_after")
    checks["snapshot_unchanged"] = bool(isinstance(before, str) and before
                                        and before == after)
    checks["edit_target_intact"] = facts.get("edit_target_intact") is True
    checks["copy_write_worked"] = facts.get("copy_marker_exists") is True
    checks["copy_tool_write_worked"] = \
        facts.get("copy_tool_marker_exists") is True
    checks["probe_script_intact"] = _probe_script_intact(facts)
    result = {k: bool(checks.get(k, False)) for k in PROBE_REQUIRED_CHECKS}
    return all(result.values()), result
