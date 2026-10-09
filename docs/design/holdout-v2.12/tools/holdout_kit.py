"""holdout_kit.py — the owner-run launch kit for the v2.12 sealed holdout.

The holdout is six review cases (three catch, three quiet) that the tuning side
must never see until the Phase-55 evaluation. Four roles touch it:

  * tuning      — this repo's ordinary sessions. They never read the holdout;
                  holdout_guard.py denies every tool call that reaches it.
  * finder      — a fresh, isolated Claude session (bin/finder) that receives
                  only the kit, searches the eligible repos and writes the
                  cases into sealed/.
  * cross-check — a second isolated session (bin/crosscheck, and one fresh
                  generation per reveal) that judges each case blind, without
                  slot, key or proof, and is then shown the key.
  * evaluation  — Phase 55 decrypts the archive and re-hashes it against the
                  committed SEAL.json.

This module is the CLI entry point and the shared helper library. `setup`
lives here; the other subcommands live in sibling modules (holdout_validate,
holdout_manifest, holdout_seal, holdout_archive, holdout_dryrun) that are
imported lazily through COMMANDS, so a kit copy missing one of them still runs
the others and says plainly which command is not installed.

Rules:
  * The holdout folder is ALWAYS an explicit --folder argument. No argument
    defaults to the holdout path (a repo tool that defaulted to it would read
    the holdout without naming it on its command line).
  * Every holdout-touching subcommand calls refuse_if_claude_spawned(folder)
    first: when CLAUDECODE is set and CLAUDE_CONFIG_DIR is not inside the
    folder, the command refuses with a fixed message. The owner runs the kit
    from a plain Terminal window.
  * I/O: stdlib only, imports exactly {argparse, hashlib, hmac, importlib,
    json, os, re, secrets, shutil, stat, subprocess, sys, tarfile, tempfile}.
    Every subprocess.run is an argv list with a timeout, never a shell.
    openssl never receives -pass or -k: the passphrase comes from its own tty
    prompt.
  * Output is one plain-language line per step ("OK: ..." / "PROBLEM: ...")
    and never echoes case content.

Exit codes: 0 success, 1 a plain-language refusal or failure ("holdout: ..."
on stderr), 2 a usage error.
"""

import argparse
import hashlib
import hmac
import importlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)


class KitError(Exception):
    """One plain-language line; the CLI prints it and exits 1."""


SLOTS = ("C1", "C2", "C3", "Q1", "Q2", "Q3")
CATCH_SLOTS = ("C1", "C2", "C3")
QUIET_SLOTS = ("Q1", "Q2", "Q3")
ID_RE = re.compile(r"^H-[0-9a-f]{8}$")
XID_RE = re.compile(r"^X-[0-9a-f]{8}$")
CASE_FILES = frozenset({"case.json", "base.tar", "change.diff"})
KEY_FILES = frozenset({"key.json", "provenance.json", "proof-results.json",
                       "xcheck-ledger.json", "crosscheck.json",
                       "resolution.md"})
# Files that live directly in sealed/ and are excluded from per-case
# serialization and the private inventory. SANDBOX-SENTINEL is a harmless
# fixed-text read target for the cross-check sandbox probe.
SEALED_PRIVATE = ("HMAC-KEY", "INVENTORY.json", "SANDBOX-SENTINEL")
# The cross-check workspace registry (holdout_seal). It is the one entry in
# sealed/keys/ that is not a case folder: validate's opaque-id check and
# build_seal skip exactly this regular file. It lives under sealed/ so no
# cross-check session can read it, and it is archived with the cases.
XCHECK_REGISTRY = "xcheck-workspaces.json"
SANDBOX_SENTINEL_TEXT = ("holdout sandbox sentinel. If a cross-check session "
                         "can print this line, its sandbox is not enforcing "
                         "denyRead. Stop.\n")

REFUSE_MSG = ("holdout: refusing to run inside a Claude-spawned shell. "
              "Open a plain Terminal window and run this again.")
NOT_INSTALLED_MSG = "command '%s' is not installed in this kit copy"
ERR_PREFIX = "holdout: "


def new_case_id():
    """A fresh opaque case id: "H-" + 8 random hex digits, never content-derived."""
    return "H-" + secrets.token_hex(4)


def new_xcheck_id():
    """A fresh opaque cross-check id: "X-" + 8 random hex digits."""
    return "X-" + secrets.token_hex(4)


# ---------------------------------------------------------------- refusal


def _inside(path, root):
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def refuse_if_claude_spawned(folder):
    """Raise KitError(REFUSE_MSG) inside a Claude-spawned shell.

    A shell is Claude-spawned when CLAUDECODE is set. The one exception is an
    isolated holdout session, whose CLAUDE_CONFIG_DIR lives inside the folder.
    """
    if not os.environ.get("CLAUDECODE"):
        return
    cfg = os.environ.get("CLAUDE_CONFIG_DIR") or ""
    if not folder or not cfg:
        raise KitError(REFUSE_MSG)
    if not _inside(os.path.realpath(cfg), os.path.realpath(folder)):
        raise KitError(REFUSE_MSG)


# ---------------------------------------------------------------- JSON


def load_json(path, required=(), what="file"):
    """Strict JSON object load.

    `required` is either an iterable of keys that must be present, or a dict
    {key: type or tuple of types}. Booleans never satisfy an int requirement.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise KitError("%s is missing or unreadable" % what)
    if not isinstance(data, dict):
        raise KitError("%s has the wrong shape" % what)
    if isinstance(required, dict):
        items = required.items()
    else:
        items = ((key, None) for key in required)
    for key, types in items:
        if key not in data:
            raise KitError("%s has the wrong shape (%s)" % (what, key))
        if types is None:
            continue
        value = data[key]
        wants_bool = types is bool or (isinstance(types, tuple)
                                       and bool in types)
        if not isinstance(value, types) or (isinstance(value, bool)
                                            and not wants_bool):
            raise KitError("%s has the wrong shape (%s)" % (what, key))
    return data


def write_json_atomic(path, obj):
    """Write `obj` as sorted, indented JSON via a temp file and os.replace."""
    parent = os.path.dirname(os.path.abspath(path))
    tmp = None
    try:
        os.makedirs(parent, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=parent,
                                   prefix="." + os.path.basename(path) + ".",
                                   suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except OSError:
        raise KitError("cannot write %s" % os.path.basename(path))
    finally:
        if tmp is not None and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _write_text(path, text, mode=None):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        if mode is not None:
            os.chmod(path, mode)
    except OSError:
        raise KitError("cannot write %s" % os.path.basename(path))


# ---------------------------------------------------------------- subprocess


def run_argv(argv, cwd=None, timeout=60, stdin_bytes=None, capture=True):
    """Run an argv list (never a shell) with a timeout.

    Raises KitError naming only the program's basename when it cannot start
    or times out.
    """
    pipe = subprocess.PIPE if capture else None
    try:
        return subprocess.run(list(argv), cwd=cwd, input=stdin_bytes,
                              stdout=pipe, stderr=pipe, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise KitError("%s could not run (%s)"
                       % (os.path.basename(str(argv[0])),
                          type(exc).__name__))


# ---------------------------------------------------------------- hashing


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                digest.update(chunk)
    except OSError:
        raise KitError("cannot read %s" % os.path.basename(path))
    return digest.hexdigest()


def hmac_hex(key, data):
    return hmac.new(key, data, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------- file walks


def walk_regular(root):
    """Sorted '/'-separated relpaths of every regular file under `root`.

    Refuses (KitError) any symlink, file or directory, and any special file.
    """
    out = []
    base = os.path.basename(os.path.normpath(root))
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in list(dirnames) + list(filenames):
            full = os.path.join(dirpath, name)
            try:
                mode = os.lstat(full).st_mode
            except OSError:
                raise KitError("cannot read an entry under %s" % base)
            if stat.S_ISLNK(mode):
                raise KitError("a symbolic link was found under %s; "
                               "remove it and run this again" % base)
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise KitError("a special file was found under %s; "
                               "remove it and run this again" % base)
            rel = os.path.relpath(full, root)
            out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def safe_extract_tar(tar_path, dest):
    """Extract a tar of plain files and directories into `dest`.

    Refuses absolute member names, any `..` segment, and every member that is
    not a regular file or a directory (symlinks, hardlinks, devices, fifos).
    All members are checked before anything is written.
    """
    dest_real = os.path.realpath(dest)
    try:
        with tarfile.open(tar_path, "r:*") as tar:
            members = tar.getmembers()
            for m in members:
                name = m.name
                parts = name.replace("\\", "/").split("/")
                if name.startswith("/") or os.path.isabs(name) \
                        or ".." in parts:
                    raise KitError("the archive holds an unsafe path; "
                                   "nothing was extracted")
                if m.issym() or m.islnk() or m.isdev() \
                        or not (m.isfile() or m.isdir()):
                    raise KitError("the archive holds a link or special "
                                   "file; nothing was extracted")
                target = os.path.realpath(os.path.join(dest_real, name))
                if not _inside(target, dest_real):
                    raise KitError("the archive holds an unsafe path; "
                                   "nothing was extracted")
            for m in members:
                tar.extract(m, dest_real, filter="data")
    except (OSError, tarfile.TarError):
        raise KitError("cannot read or extract %s"
                       % os.path.basename(tar_path))


def sealed_dir(folder):
    return os.path.join(folder, "sealed")


def case_ids(folder):
    """Sorted case ids under sealed/cases; KitError on any other name."""
    cases = os.path.join(sealed_dir(folder), "cases")
    try:
        names = os.listdir(cases)
    except OSError:
        raise KitError("sealed/cases is missing or unreadable")
    for name in names:
        if not ID_RE.match(name):
            raise KitError("sealed/cases holds an entry that is not a case "
                           "id; remove it and run this again")
    return sorted(names)


def print_ok(msg):
    print("OK: %s" % msg)


def print_problem(msg):
    print("PROBLEM: %s" % msg)


# ---------------------------------------------------------------- layout

# Directories setup creates. tmp/ is only the parent of the per-role temp
# roots: tmp/finder (the finder session), tmp/owner (kit commands the owner
# runs) and tmp/crosscheck/<ws> (one per cross-check generation; the fixed
# parent tmp/crosscheck lets the finder be denied every present and future
# generation's scratch with one path). No generation-owned path is listed:
# xcheck*, cfg-xcheck*, tmp/crosscheck/xcheck* and bin/crosscheck* are created
# only by make_xcheck_workspace, which refuses if any of them already exists.
SUBDIRS = ("kit", "kit/tools", "bin", "sealed", "sealed/cases", "sealed/keys",
           "work", "cfg-finder", "tmp", "tmp/finder", "tmp/owner",
           "tmp/crosscheck", "archive")
PRIVATE_DIRS = ("tmp/finder", "tmp/owner")
SENTINEL_NAME = "SANDBOX-SENTINEL"
SENTINEL_DIRS = ("sealed", "tmp/finder", "tmp/owner")

FINDER_TEMPLATE = "finder-settings.json"
XCHECK_TEMPLATE = "crosscheck-settings.json"
B3_EXCLUSIONS = "b3-exclusions.json"
ELIGIBLE_REPOS = "eligible-repos.json"
KIT_INVENTORY = "KIT-INVENTORY.json"
KIT_INVENTORY_SCHEMA = "vibe-check-holdout-kit-inventory/1"
GUARD_NAME = "holdout_guard.py"
GUARD_REL = "kit/" + GUARD_NAME
PLACEHOLDER_TOKENS = ("<H>", "<HOME>", "<REPOS>", "<GUARD>", "<SEALED>")

# The six tuning-side paths every isolated session's sandbox denies. Both
# settings templates carry exactly these in sandbox.filesystem.denyRead.
TUNING_DENY_READ = ("~/turingmind-code-review", "~/thejuran-marketplace",
                    "~/.claude", "~/.codex", "~/.b3", "~/.vibe-check-snapshots")

# Relpaths under the folder the FINDER is denied in all three controls
# (permission deny, guard --protect, sandbox denyRead): owner scratch and the
# parent of every cross-check generation's scratch. The finder's own
# tmp/finder is never listed.
FINDER_PROTECTED_TMP = ("tmp/owner", "tmp/crosscheck")
# Relpaths the finder reads outside its work/ cwd (reads outside the working
# directories are blocked): sealed/ (it writes the cases there) and kit/
# (its brief, the case types, the rules and the repo lists). With the
# eligible repos they are the finder's extra working directories.
#
# Claude Code ignores permissions.additionalDirectories that come from a
# workspace's own .claude/settings.json for the read block and for the
# sandbox, so the grant lives in the finder's USER settings: the launcher
# sets CLAUDE_CONFIG_DIR=<H>/cfg-finder, which makes
# <H>/cfg-finder/settings.json that file. A working directory is writable
# by sandboxed commands, so kit/ and every repo are write-denied in
# sandbox.filesystem.denyWrite: in a real session (CLI 2.1.281) the
# workspace's Edit deny rules stopped Claude's Edit and Write tools but not a
# sandboxed `touch`.
FINDER_READ_DIRS = ("sealed", "kit")
FINDER_READONLY_DIRS = ("kit",)
FINDER_USER_SETTINGS = "cfg-finder/settings.json"

# Relpaths under the folder EVERY cross-check generation is denied. A
# generation's own workspace, config dir and temp root are never protected
# from itself; earlier generations' are appended per generation.
XCHECK_BASE_PROTECTED = ("sealed", "work", "cfg-finder", "kit/FINDER-BRIEF.md",
                         "tmp/finder", "tmp/owner")
XCHECK_FILE_PROTECTED = frozenset({"kit/FINDER-BRIEF.md"})
# Cross-check workspace names: "xcheck" is generation 1; "xcheck-r2",
# "xcheck-r3", ... are minted after a reveal.
XCHECK_WS_RE = re.compile(r"^xcheck(-r([2-9]|[1-9][0-9]+))?$")

LAUNCHER_REFUSAL = ('[ -z "${CLAUDECODE:-}" ] || { echo "Open a new Terminal '
                    'window (not one started by Claude) and run this again."; '
                    'exit 1; }')

FINDER_LAUNCHER = """#!/bin/bash
set -euo pipefail
%s
H=@@H@@
cd "$H/work"
export CLAUDE_CONFIG_DIR="$H/cfg-finder"
export CLAUDE_CODE_PROJECT_DIR_NAME=finder
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
export CLAUDE_CODE_TMPDIR="$H/tmp/finder" TMPDIR="$H/tmp/finder"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
exec claude "$@"
""" % LAUNCHER_REFUSAL

XCHECK_LAUNCHER = """#!/bin/bash
set -euo pipefail
%s
H=@@H@@
cd "$H/@@WS@@"
export CLAUDE_CONFIG_DIR="$H/@@CFG@@"
export CLAUDE_CODE_PROJECT_DIR_NAME=@@WS@@
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
export CLAUDE_CODE_TMPDIR="$H/@@TMP@@" TMPDIR="$H/@@TMP@@"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
exec claude "$@"
""" % LAUNCHER_REFUSAL

HOLDOUT_LAUNCHER = """#!/bin/bash
set -euo pipefail
%s
H=@@H@@
export TMPDIR="$H/tmp/owner"
export PYTHONDONTWRITEBYTECODE=1
exec python3 "$H/kit/tools/holdout_kit.py" --folder "$H" "$@"
""" % LAUNCHER_REFUSAL

# Source for <ws>/sandbox-probe.py. The owner runs `python3 sandbox-probe.py`
# as the first command of every cross-check session: its command line names
# no protected path, so only the OS sandbox can deny the reads. Every target
# inside a denied root is a sentinel or a settings file, never a key or a
# scratch file, so a probe that unexpectedly succeeds reveals nothing; it
# closes a successful open at once and never reads or prints anything.
XCHECK_SANDBOX_PROBE = '''"""Cross-check sandbox probe (generated by the holdout kit).

Run `python3 sandbox-probe.py` as the first command of the session. It tries
to open each protected path below and passes only when the sandbox denies
every one (EACCES or EPERM). A missing path or any other error is a failure.
"""

import errno
import os
import sys

TARGETS = @@TARGETS@@


def main():
    denied = 0
    for target in TARGETS:
        try:
            fd = os.open(target, os.O_RDONLY)
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EPERM):
                denied += 1
            continue
        os.close(fd)
    total = len(TARGETS)
    if denied == total:
        print("OK: sandbox denied %d/%d protected reads" % (denied, total))
        return 0
    print("PROBLEM: sandbox did not deny %d of %d protected reads. Stop. "
          "Do not type begin. Close this session and reply: blocked sandbox"
          % (total - denied, total))
    return 1


if __name__ == "__main__":
    sys.exit(main())
'''


def _sh_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def _source_kit_dir():
    """The kit directory next to this script: <tools>/../kit in the repo, or
    the parent of kit/tools inside a holdout copy."""
    repo_layout = os.path.normpath(os.path.join(TOOLS_DIR, "..", "kit"))
    if os.path.isdir(repo_layout):
        return repo_layout
    return os.path.dirname(TOOLS_DIR)


# ---------------------------------------------------------------- templates


def _all_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for v in obj:
            yield from _all_strings(v)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _all_strings(v)


def _render_template(template, folder, repos):
    """Substitute a parsed settings template.

    A list item equal to "<REPOS>" is replaced by the repo list; "<GUARD>"
    becomes <folder>/kit/holdout_guard.py and "<H>" the folder in every
    string. Any placeholder left afterwards is refused.
    """
    guard = os.path.join(folder, GUARD_REL)

    def walk(v):
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list):
            out = []
            for x in v:
                if x == "<REPOS>":
                    out.extend(repos)
                else:
                    out.append(walk(x))
            return out
        if isinstance(v, str):
            return v.replace("<GUARD>", guard).replace("<H>", folder)
        return v

    out = walk(template)
    for s in _all_strings(out):
        if any(tok in s for tok in PLACEHOLDER_TOKENS):
            raise KitError("a settings template still holds a placeholder "
                           "after substitution")
    return out


def _guard_hooks(settings):
    """Every holdout-guard hook dict under hooks.PreToolUse (matcher kept)."""
    found = []
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    groups = hooks.get("PreToolUse") if isinstance(hooks, dict) else None
    if not isinstance(groups, list):
        return found
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"),
                                                         list):
            continue
        for hook in group["hooks"]:
            args = hook.get("args") if isinstance(hook, dict) else None
            if isinstance(args, list) and args and isinstance(args[0], str) \
                    and os.path.basename(args[0]) == GUARD_NAME:
                found.append((group.get("matcher"), args))
    return found


def _add_controls(settings, paths, file_paths=()):
    """Append each path to permission deny, guard --protect and sandbox
    denyRead, deriving all three controls from the one list."""
    try:
        deny = settings["permissions"]["deny"]
        deny_read = settings["sandbox"]["filesystem"]["denyRead"]
    except (KeyError, TypeError):
        raise KitError("a settings template has the wrong shape")
    guards = _guard_hooks(settings)
    if len(guards) != 1:
        raise KitError("a settings template does not hold exactly one "
                       "guard hook")
    args = guards[0][1]
    for p in paths:
        rule = ("Read(%s)" % p) if p in file_paths else ("Read(%s/**)" % p)
        deny.append(rule)
        args.extend(["--protect", p])
        deny_read.append(p)


def _settings_gaps(settings, role, expected, file_paths):
    """Shared checker body: one plain line per gap, [] when every control
    names every expected path."""
    if not isinstance(settings, dict):
        return ["settings are not a JSON object"]
    problems = []
    if settings.get("autoMemoryEnabled") is not False:
        problems.append("auto-memory is not switched off")
    perms = settings.get("permissions")
    perms = perms if isinstance(perms, dict) else {}
    if perms.get("blockReadsOutsideWorkingDirectories") is not True:
        problems.append("reads outside the working directories are not "
                        "blocked")
    sandbox = settings.get("sandbox")
    sandbox = sandbox if isinstance(sandbox, dict) else {}
    if sandbox.get("enabled") is not True:
        problems.append("sandbox is not enabled")
    if sandbox.get("failIfUnavailable") is not True:
        problems.append("sandbox does not fail if unavailable")
    fs = sandbox.get("filesystem")
    deny_read = fs.get("denyRead") if isinstance(fs, dict) else None
    deny_read = deny_read if isinstance(deny_read, list) else []
    for p in list(TUNING_DENY_READ) + list(expected):
        if p not in deny_read:
            problems.append("sandbox denyRead is missing %s" % p)
    deny = perms.get("deny")
    deny = deny if isinstance(deny, list) else []
    for p in expected:
        rule = ("Read(%s)" % p) if p in file_paths else ("Read(%s/**)" % p)
        if rule not in deny:
            problems.append("permission deny is missing %s" % rule)
    guards = _guard_hooks(settings)
    if len(guards) != 1:
        problems.append("settings do not hold exactly one guard hook")
        return problems
    matcher, args = guards[0]
    if matcher != "*":
        problems.append("guard hook matcher is not *")
    if args[1:4] != ["hook", "--role", role]:
        problems.append("guard hook does not run with --role %s" % role)
    protects = [args[i + 1] for i in range(len(args) - 1)
                if args[i] == "--protect"]
    for p in expected:
        if p not in protects:
            problems.append("hook --protect is missing %s" % p)
    return problems


def _finder_protected_paths(folder):
    """Absolute paths of FINDER_PROTECTED_TMP under the folder: the one source
    setup uses for the finder's three controls."""
    h = os.path.realpath(folder)
    return [os.path.join(h, p) for p in FINDER_PROTECTED_TMP]


def _finder_working_dirs(folder, eligible):
    """The finder's extra working directories (user-scope
    additionalDirectories): the eligible repos, then FINDER_READ_DIRS. The
    one source the writer uses."""
    h = os.path.realpath(folder)
    return list(eligible) + [os.path.join(h, p) for p in FINDER_READ_DIRS]


def _finder_write_denied(folder, eligible):
    """Working directories sandboxed finder commands may read but never
    write (sandbox.filesystem.denyWrite): FINDER_READONLY_DIRS, then the
    eligible repos. The one source the writer uses."""
    h = os.path.realpath(folder)
    return [os.path.join(h, p) for p in FINDER_READONLY_DIRS] + list(eligible)


def _list_at(d, *keys):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
    return d if isinstance(d, list) else []


def finder_settings_problems(settings, folder, user_settings):
    """Check the finder's project settings (work/.claude/settings.json) and
    user settings (cfg-finder/settings.json); [] when every control is in
    place.

    Recomputes its expectation from FINDER_PROTECTED_TMP, FINDER_READ_DIRS
    and FINDER_READONLY_DIRS itself (never from _finder_protected_paths,
    _finder_working_dirs or _finder_write_denied), so it stays an
    independent oracle. The invariant: sealed/ and kit/ are granted, every
    granted directory except sealed/ (kit/ and each repo) is write-denied to
    sandboxed commands, and nothing write-denies sealed/.
    """
    h = os.path.realpath(folder)
    expected = [os.path.join(h, p) for p in FINDER_PROTECTED_TMP]
    problems = _settings_gaps(settings, "finder", expected, frozenset())
    deny = _list_at(settings, "permissions", "deny")
    for rel in FINDER_READONLY_DIRS:
        rule = "Edit(%s/**)" % os.path.join(h, rel)
        if rule not in deny:
            problems.append("permission deny is missing %s" % rule)
    sealed = os.path.join(h, "sealed")
    extra = _list_at(user_settings, "permissions", "additionalDirectories")
    for rel in FINDER_READ_DIRS:
        if os.path.join(h, rel) not in extra:
            problems.append("finder user settings additionalDirectories is "
                            "missing %s" % os.path.join(h, rel))
    deny_write = _list_at(settings, "sandbox", "filesystem", "denyWrite")
    must_deny = [os.path.join(h, rel) for rel in FINDER_READONLY_DIRS]
    must_deny += [p for p in extra if p != sealed and p not in must_deny]
    for p in must_deny:
        if p not in deny_write:
            problems.append("sandbox denyWrite is missing %s" % p)
    if any(_inside(sealed, p) for p in deny_write if isinstance(p, str)):
        problems.append("sandbox denyWrite blocks %s" % sealed)
    return problems


# ---------------------------------------------------------------- cross-check


def xcheck_names(gen):
    """Directory, config dir, temp root and launcher names of generation gen."""
    if not isinstance(gen, int) or isinstance(gen, bool) or gen < 1:
        raise KitError("cross-check generation must be 1 or more")
    suffix = "" if gen == 1 else "-r%d" % gen
    return {"workspace": "xcheck" + suffix,
            "config_dir": "cfg-xcheck" + suffix,
            "tmp_dir": "tmp/crosscheck/xcheck" + suffix,
            "launcher": "bin/crosscheck" + suffix}


def _gen_of(entry):
    ws = entry.get("workspace") if isinstance(entry, dict) else None
    if not isinstance(ws, str) or not XCHECK_WS_RE.match(ws):
        raise KitError("an earlier cross-check generation is not recognized")
    return 1 if ws == "xcheck" else int(ws[len("xcheck-r"):])


def _xcheck_protected_paths(folder, prior=()):
    """Absolute paths a cross-check generation is denied: the base list, then
    each earlier generation's workspace, config dir and temp root. The one
    source the writer uses for all three controls."""
    h = os.path.realpath(folder)
    paths = [os.path.join(h, p) for p in XCHECK_BASE_PROTECTED]
    for n in prior:
        paths.extend(os.path.join(h, n[k])
                     for k in ("workspace", "config_dir", "tmp_dir"))
    return paths


def xcheck_settings_problems(settings, folder, prior=()):
    """Check cross-check settings; [] when every control is in place.

    Builds its expected list itself from XCHECK_BASE_PROTECTED and
    xcheck_names(k) for each earlier generation (never by calling
    _xcheck_protected_paths), so it stays an independent oracle.
    """
    h = os.path.realpath(folder)
    expected = [os.path.join(h, p) for p in XCHECK_BASE_PROTECTED]
    for entry in prior:
        n = xcheck_names(_gen_of(entry))
        expected.extend([os.path.join(h, n["workspace"]),
                         os.path.join(h, n["config_dir"]),
                         os.path.join(h, n["tmp_dir"])])
    file_paths = frozenset(os.path.join(h, p) for p in XCHECK_FILE_PROTECTED)
    return _settings_gaps(settings, "xcheck", expected, file_paths)


def _probe_targets(h, prior):
    targets = []
    for p in XCHECK_BASE_PROTECTED:
        if p in SENTINEL_DIRS:
            targets.append(os.path.join(h, p, SENTINEL_NAME))
        else:
            targets.append(os.path.join(h, p))
    for n in prior:
        targets.append(os.path.join(h, n["workspace"], ".claude",
                                    "settings.json"))
        targets.append(os.path.join(h, n["config_dir"]))
        targets.append(os.path.join(h, n["tmp_dir"], SENTINEL_NAME))
    return targets


def _remove(path):
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def make_xcheck_workspace(folder, gen, prior=()):
    """Mint cross-check generation `gen`: its workspace (settings + sandbox
    probe), empty config dir, private temp root (with a sentinel) and
    launcher. `prior` must be xcheck_names(k) for every k < gen.

    The settings are self-checked after they are written; on any problem, or
    any error at all, everything this call created is removed (fail closed).
    """
    names = xcheck_names(gen)
    prior = list(prior)
    if prior != [xcheck_names(k) for k in range(1, gen)]:
        raise KitError("cross-check generation %d must list every earlier "
                       "generation" % gen)
    h = os.path.realpath(folder)
    ws = os.path.join(h, names["workspace"])
    cfg = os.path.join(h, names["config_dir"])
    tmp_root = os.path.join(h, names["tmp_dir"])
    launcher = os.path.join(h, names["launcher"])
    if any(os.path.lexists(p) for p in (ws, cfg, tmp_root, launcher)):
        raise KitError("cross-check workspace %s already exists"
                       % names["workspace"])
    template = load_json(os.path.join(h, "kit", XCHECK_TEMPLATE),
                         what="the cross-check settings template")
    created = []
    try:
        settings = _render_template(template, h, [])
        file_paths = frozenset(os.path.join(h, p)
                               for p in XCHECK_FILE_PROTECTED)
        _add_controls(settings, _xcheck_protected_paths(h, prior), file_paths)
        created.append(ws)
        os.makedirs(os.path.join(ws, ".claude"))
        settings_path = os.path.join(ws, ".claude", "settings.json")
        write_json_atomic(settings_path, settings)
        problems = xcheck_settings_problems(
            load_json(settings_path, what="the cross-check settings"),
            h, prior)
        if problems:
            raise KitError("cross-check settings failed their self-check: %s"
                           % problems[0])
        probe = XCHECK_SANDBOX_PROBE.replace(
            "@@TARGETS@@", json.dumps(_probe_targets(h, prior), indent=4))
        _write_text(os.path.join(ws, "sandbox-probe.py"), probe, 0o700)
        created.append(cfg)
        os.makedirs(cfg)
        os.chmod(cfg, 0o700)
        created.append(tmp_root)
        os.makedirs(tmp_root)
        os.chmod(tmp_root, 0o700)
        _write_text(os.path.join(tmp_root, SENTINEL_NAME),
                    SANDBOX_SENTINEL_TEXT)
        text = (XCHECK_LAUNCHER.replace("@@H@@", _sh_quote(h))
                .replace("@@WS@@", names["workspace"])
                .replace("@@CFG@@", names["config_dir"])
                .replace("@@TMP@@", names["tmp_dir"]))
        created.append(launcher)
        os.makedirs(os.path.dirname(launcher), exist_ok=True)
        _write_text(launcher, text, 0o700)
    except BaseException:
        for path in reversed(created):
            try:
                _remove(path)
            except OSError:
                pass
        raise
    return names


def write_kit_inventory(folder):
    """kit/KIT-INVENTORY.json: sha256 of every file under kit/ that setup
    copied from the repo (everything but eligible-repos.json and itself)."""
    kit = os.path.join(os.path.realpath(folder), "kit")
    files = {}
    for rel in walk_regular(kit):
        if rel in (KIT_INVENTORY, ELIGIBLE_REPOS):
            continue
        files[rel] = sha256_file(os.path.join(kit, rel))
    inventory = {"schema": KIT_INVENTORY_SCHEMA, "files": files}
    write_json_atomic(os.path.join(kit, KIT_INVENTORY), inventory)
    return inventory


# ---------------------------------------------------------------- setup


def add_parser(sub, name):
    if name == "setup":
        p = sub.add_parser(
            "setup", help="create the isolated holdout folder, launchers "
                          "and session settings")
        p.add_argument("--repo", action="append", required=True,
                       metavar="PATH",
                       help="an eligible source repo (repeat for each)")
        p.add_argument("--skip-system-exclusions", action="store_true",
                       help="do not run tmutil (tests only)")


def cmd(args):
    if args.cmd == "setup":
        refuse_if_claude_spawned(args.folder)
        setup(args.folder, args.repo,
              skip_system_exclusions=args.skip_system_exclusions)
        return 0
    raise KitError("unknown command")


def _check_repos(repos, exclusions):
    eligible, exposed = [], []
    for repo in repos:
        real = os.path.realpath(repo)
        base = os.path.basename(real)
        if base in exclusions["exclude_all_slots"]:
            raise KitError("%s is the tuning repo or its mirror and can never "
                           "be a holdout source" % base)
        if not os.path.exists(os.path.join(real, ".git")):
            raise KitError("%s is not a git repository" % base)
        if real in eligible:
            continue
        eligible.append(real)
        if base in exclusions["repos"]:
            exposed.append(base)
    return eligible, exposed


def _copy(src, dst):
    if os.path.islink(src) or not os.path.isfile(src):
        raise KitError("kit file %s is missing or not a regular file"
                       % os.path.basename(src))
    try:
        shutil.copy2(src, dst, follow_symlinks=False)
    except OSError:
        raise KitError("cannot copy %s" % os.path.basename(src))


def _copy_kit(h):
    src_kit = _source_kit_dir()
    kit = os.path.join(h, "kit")
    for name in sorted(os.listdir(src_kit)):
        if name.endswith((".md", ".json")) \
                and name not in (KIT_INVENTORY, ELIGIBLE_REPOS):
            _copy(os.path.join(src_kit, name), os.path.join(kit, name))
    for name in sorted(os.listdir(TOOLS_DIR)):
        if name.endswith(".py") and not name.startswith("test_"):
            _copy(os.path.join(TOOLS_DIR, name),
                  os.path.join(kit, "tools", name))
    _copy(os.path.join(TOOLS_DIR, GUARD_NAME), os.path.join(h, GUARD_REL))


def _write_finder_settings(h, eligible):
    template = load_json(os.path.join(h, "kit", FINDER_TEMPLATE),
                         what="the finder settings template")
    settings = _render_template(template, h, eligible)
    try:
        deny = settings["permissions"]["deny"]
        deny_write = settings["sandbox"]["filesystem"]["denyWrite"]
    except (KeyError, TypeError):
        raise KitError("the finder settings template has the wrong shape")
    for repo in eligible:
        deny.append("Edit(%s/**)" % repo)
    deny_write.extend(_finder_write_denied(h, eligible))
    _add_controls(settings, _finder_protected_paths(h))
    path = os.path.join(h, "work", ".claude", "settings.json")
    user_path = os.path.join(h, *FINDER_USER_SETTINGS.split("/"))
    write_json_atomic(path, settings)
    write_json_atomic(user_path, {"permissions": {
        "additionalDirectories": _finder_working_dirs(h, eligible)}})
    problems = finder_settings_problems(
        load_json(path, what="the finder settings"), h,
        load_json(user_path, what="the finder user settings"))
    if problems:
        os.remove(path)
        os.remove(user_path)
        raise KitError("finder settings failed their self-check: %s"
                       % problems[0])


def setup(folder, repos, skip_system_exclusions=False):
    """Create the isolated holdout folder at the explicit `folder`."""
    refuse_if_claude_spawned(folder)
    if not folder:
        raise KitError("the holdout folder must be given explicitly")
    if os.path.lexists(folder) and (not os.path.isdir(folder)
                                    or os.listdir(folder)):
        raise KitError("folder already exists and is not empty")
    exclusions = load_json(
        os.path.join(_source_kit_dir(), B3_EXCLUSIONS),
        required={"repos": list, "exclude_all_slots": list},
        what="the B3 exclusions file")
    eligible, exposed = _check_repos(repos, exclusions)
    for base in exposed:
        print_ok("%s (previously exposed during B3 development; not "
                 "eligible for C1/Q2)" % base)

    os.makedirs(folder, exist_ok=True)
    h = os.path.realpath(folder)
    os.chmod(h, 0o700)
    for rel in SUBDIRS:
        os.makedirs(os.path.join(h, rel), exist_ok=True)
    for rel in PRIVATE_DIRS:
        os.chmod(os.path.join(h, rel), 0o700)
    print_ok("created the holdout folder (private to you)")
    _write_text(os.path.join(h, ".metadata_never_index"), "")
    print_ok("Spotlight will not index the folder")
    for rel in SENTINEL_DIRS:
        _write_text(os.path.join(h, rel, SENTINEL_NAME), SANDBOX_SENTINEL_TEXT)
    print_ok("wrote the sandbox probe targets")

    _copy_kit(h)
    write_json_atomic(os.path.join(h, "kit", ELIGIBLE_REPOS),
                      {"repos": eligible})
    write_kit_inventory(h)
    print_ok("copied the kit and listed %d eligible repo(s)" % len(eligible))

    _write_finder_settings(h, eligible)
    print_ok("wrote the finder session settings")
    make_xcheck_workspace(h, 1)
    print_ok("created the cross-check workspace")
    _write_text(os.path.join(h, "bin", "finder"),
                FINDER_LAUNCHER.replace("@@H@@", _sh_quote(h)), 0o700)
    _write_text(os.path.join(h, "bin", "holdout"),
                HOLDOUT_LAUNCHER.replace("@@H@@", _sh_quote(h)), 0o700)
    print_ok("wrote the finder, cross-check and holdout launchers")

    if skip_system_exclusions:
        print_ok("skipped the Time Machine exclusion (--skip-system-exclusions)")
    else:
        try:
            proc = run_argv(["tmutil", "addexclusion", h], timeout=60)
            ok = proc.returncode == 0
        except KitError:
            ok = False
        if ok:
            print_ok("Time Machine will not back up the folder")
        else:
            print_problem("Time Machine exclusion failed. Run this in a plain "
                          "Terminal window: tmutil addexclusion %s" % h)
    print_ok("holdout folder ready at %s. Next: %s/bin/finder" % (h, h))


# ---------------------------------------------------------------- CLI

COMMANDS = {
    "setup": "holdout_kit",
    "validate": "holdout_validate",
    "seal-build": "holdout_manifest",
    "rehash": "holdout_manifest",
    "extract": "holdout_manifest",
    "seal-order": "holdout_manifest",
    "publish": "holdout_manifest",
    "retire": "holdout_manifest",
    "resume-check": "holdout_manifest",
    "crosscheck-prepare": "holdout_seal",
    "crosscheck-reveal": "holdout_seal",
    "crosscheck-reset": "holdout_seal",
    "seal": "holdout_seal",
    "encrypt": "holdout_archive",
    "decrypt": "holdout_archive",
    "leakscan": "holdout_archive",
    "scrub": "holdout_archive",
    "dryrun": "holdout_dryrun",
    "autopilot": "holdout_autopilot",
}
# The ONLY commands run() dispatches without --folder. seal-order and publish
# take --repo; resume-check reads a checkpoint reply from stdin.
NO_FOLDER_COMMANDS = frozenset({"seal-order", "publish", "resume-check"})
# Commands whose cmd() does not call refuse_if_claude_spawned: they touch no
# holdout content. publish still refuses (it reads the holdout SEAL.json).
NO_REFUSAL_COMMANDS = frozenset({"seal-order", "resume-check"})


def _load_module(name):
    """Import a command module; None when that module is not in this kit copy."""
    if name == "holdout_kit":
        return sys.modules[__name__]
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            return None
        raise


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="holdout",
        description="Owner-run launch kit for the v2.12 sealed holdout. "
                    "Run it from a plain Terminal window.")
    parser.add_argument("--folder", metavar="PATH",
                        help="the holdout folder, always explicit")
    sub = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    modules, missing = {}, set()
    loaded = {}
    for name, modname in COMMANDS.items():
        if modname not in loaded:
            loaded[modname] = _load_module(modname)
        module = loaded[modname]
        if module is None:
            p = sub.add_parser(name, help="(not installed in this kit copy)")
            p.add_argument("rest", nargs=argparse.REMAINDER)
            missing.add(name)
            continue
        module.add_parser(sub, name)
        modules[name] = module
    return parser, modules, missing


def _command_and_folder(argv):
    """(command, folder given?) from the top-level arguments, without parsing
    the subcommand's own options."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--folder")
    pre.add_argument("cmd", nargs="?")
    pre.add_argument("rest", nargs=argparse.REMAINDER)
    try:
        ns, _ = pre.parse_known_args(argv)
    except SystemExit:
        return None, False
    return ns.cmd, ns.folder is not None


def _err(msg):
    text = str(msg)
    if not text.startswith(ERR_PREFIX):
        text = ERR_PREFIX + text
    sys.stderr.write(text + "\n")


def run(argv):
    parser, modules, missing = _build_parser()
    command, has_folder = _command_and_folder(argv)
    if command in COMMANDS and not has_folder \
            and command not in NO_FOLDER_COMMANDS:
        parser.print_usage(sys.stderr)
        sys.stderr.write("holdout: error: --folder PATH is required for "
                         "'%s'\n" % command)
        return 2
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    if args.cmd in missing:
        _err(NOT_INSTALLED_MSG % args.cmd)
        return 1
    try:
        return modules[args.cmd].cmd(args)
    except KitError as exc:
        _err(exc)
        return 1


if __name__ == "__main__":
    # Sibling modules import `holdout_kit`; make that the running module so
    # they share one KitError class and one set of helpers.
    sys.modules.setdefault("holdout_kit", sys.modules[__name__])
    sys.exit(run(sys.argv[1:]))
