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


# ---------------------------------------------------------------- dry run

# A dry-run folder carries DRY-RUN.json at its top level, written by
# `dryrun --populate` (and by refresh-kit only when the folder is provably a
# dry run). Its content binds it to that folder's real path, so a copy in
# another folder is not a valid marker. SYNTHETIC-AGREEMENT.json is written
# only by `autopilot --dry-run` in a marked folder. LEAK-WAIVER.json is
# written only by `autopilot --dry-run` in a marked folder, after a leak scan
# named dummy cases and a later fresh scan came back clean: it keeps those
# cases (no replacement) marked `leak: waived (dry-run)`. Any one file's mere
# presence (any content) makes real sealing, publish and rehash refuse; only
# a valid marker plus an explicit dry-run mode lets the dry run seal.
# Schema strings are built from two literals, as elsewhere in the kit.
DRYRUN_MARKER = "DRY-RUN.json"
DRYRUN_MARKER_SCHEMA = "vibe-check-" "holdout-dryrun-folder/1"
SYNTHETIC_AGREEMENT = "SYNTHETIC-AGREEMENT.json"
SYNTHETIC_AGREEMENT_SCHEMA = "vibe-check-" "holdout-synthetic-agreement/1"
LEAK_WAIVER = "LEAK-WAIVER.json"
LEAK_WAIVER_SCHEMA = "vibe-check-" "holdout-leak-waiver/1"
DRY_RUN_MARKERS = (DRYRUN_MARKER, SYNTHETIC_AGREEMENT, LEAK_WAIVER)
DRY_RUN_REFUSED_MSG = ("this is a dry-run folder or a dry-run seal "
                       "(DRY-RUN.json, SYNTHETIC-AGREEMENT.json, "
                       "LEAK-WAIVER.json or a SEAL.json marked dry-run); it "
                       "is never sealed, published or verified as the real "
                       "holdout")


def dry_run_markers_present(folder):
    """The dry-run marker names present at the top of `folder` (any content,
    symlinks included)."""
    if not folder:
        return []
    return [name for name in DRY_RUN_MARKERS
            if os.path.lexists(os.path.join(folder, name))]


def dry_run_marker_ok(folder):
    """True only when <folder>/DRY-RUN.json is a regular file holding exactly
    this kit's marker for this folder's real path."""
    if not folder:
        return False
    path = os.path.join(folder, DRYRUN_MARKER)
    if os.path.islink(path) or not os.path.isfile(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return False
    return (isinstance(data, dict)
            and set(data) == {"schema", "mode", "folder", "created_at"}
            and data["schema"] == DRYRUN_MARKER_SCHEMA
            and data["mode"] == "dry-run"
            and data["folder"] == os.path.realpath(folder)
            and isinstance(data["created_at"], str))


def write_dry_run_marker(folder, created_at):
    """Write DRY-RUN.json for `folder` (`created_at`: an ISO timestamp
    string); return its path."""
    h = os.path.realpath(folder)
    path = os.path.join(h, DRYRUN_MARKER)
    if os.path.islink(path):
        raise KitError("DRY-RUN.json is a symbolic link; remove it and run "
                       "this again")
    write_json_atomic(path, {
        "schema": DRYRUN_MARKER_SCHEMA, "mode": "dry-run", "folder": h,
        "created_at": str(created_at)})
    return path


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

# Claude Code's shared per-user temp directories. A sandboxed role command
# gets $TMPDIR (and Claude Code writes its cwd-tracking file) under
# <CLAUDE_CODE_TMPDIR>/claude-<uid> only while that path is at most 44
# bytes; any longer override, which every role temp root under the holdout
# folder is, falls back to the shared /tmp/claude-<uid>. That directory is
# writable by sandboxed commands by default and holds every other Claude
# session's scratch (the tuning side's included), so a role session that
# exported a proof there leaked case text out of the folder (51-09 dry run,
# CLI 2.1.281). Every role session is therefore denied these directories in
# all three controls (sandbox read and write, permission Read and Edit for
# the unsandboxed file tools, guard --protect). /tmp/claude is the sandbox
# runtime's own built-in writable path; it is denied the same way.
SHARED_TMP_NAMES = ("claude-%d", "claude")
SHARED_TMP_PARENT = "/tmp"


def shared_tmp_dirs(uid=None):
    """Real paths of the shared temp directories every role session is
    denied (uid: default this process's). The one source the writers use."""
    uid = os.getuid() if uid is None else uid
    base = os.path.realpath(SHARED_TMP_PARENT)
    return [os.path.join(base, n % uid if "%" in n else n)
            for n in SHARED_TMP_NAMES]


def _shared_tmp_rule_paths(uid=None):
    """shared_tmp_dirs plus their /tmp spellings, for the permission rules
    (which match the path a tool names, not its real path)."""
    real = shared_tmp_dirs(uid)
    base = os.path.realpath(SHARED_TMP_PARENT)
    out = list(real)
    for p in real:
        alias = SHARED_TMP_PARENT + p[len(base):]
        if alias not in out:
            out.append(alias)
    return out


def _abs_rule(tool, path):
    """A permission rule for an absolute path: Claude Code reads `//path` as
    absolute (a single leading slash anchors at the settings file)."""
    return "%s(//%s/**)" % (tool, path.lstrip("/"))


# The file every role launcher names in CLAUDE_ENV_FILE. Claude Code reads
# it in the (unsandboxed) parent and runs it inside every Bash command after
# it has pointed $TMPDIR at the shared fallback above, so it puts $TMPDIR
# (and zsh's here-document prefix) back in the role's own temp root:
# Claude Code sets CLAUDE_CODE_TMPDIR to <role temp root>/claude-<uid> for
# sandboxed commands. Static text: the same file serves every role.
ROLE_ENV_REL = "bin/role-env.sh"
ROLE_ENV_TEXT = """\
# Generated by the holdout kit. Every role session runs this inside each Bash
# command (CLAUDE_ENV_FILE): scratch files go to the session's own temp root,
# never to the shared /tmp/claude-<uid>, which the sandbox denies.
if [ -n "${CLAUDE_CODE_TMPDIR:-}" ]; then
  export TMPDIR="$CLAUDE_CODE_TMPDIR" TMPPREFIX="$CLAUDE_CODE_TMPDIR/zsh"
fi
# The judge re-runs proofs whose exits validate recorded in the owner's
# Terminal: keep that Terminal's PATH (the launcher saved it), whatever
# PATH the session's shell set up.
if [ -n "${HOLDOUT_ROLE_PATH:-}" ]; then
  export PATH="$HOLDOUT_ROLE_PATH"
fi
"""
ROLE_PATH_LINE = 'export HOLDOUT_ROLE_PATH="$PATH"'
ROLE_ENV_LINE = '%s\nexport CLAUDE_ENV_FILE="$H/%s"' % (ROLE_PATH_LINE,
                                                       ROLE_ENV_REL)

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
%s
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
exec claude "$@"
""" % (LAUNCHER_REFUSAL, ROLE_ENV_LINE)

XCHECK_LAUNCHER = """#!/bin/bash
set -euo pipefail
%s
H=@@H@@
cd "$H/@@WS@@"
export CLAUDE_CONFIG_DIR="$H/@@CFG@@"
export CLAUDE_CODE_PROJECT_DIR_NAME=@@WS@@
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
export CLAUDE_CODE_TMPDIR="$H/@@TMP@@" TMPDIR="$H/@@TMP@@"
%s
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
exec claude "$@"
""" % (LAUNCHER_REFUSAL, ROLE_ENV_LINE)

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
# WRITE_TARGETS are the shared temp directory Claude Code points sandboxed
# commands at (it exists whenever a sandboxed command has run): the probe
# tries to create an empty directory in it, and removes it at once if the
# sandbox let it through.
XCHECK_SANDBOX_PROBE = '''"""Cross-check sandbox probe (generated by the holdout kit).

Run `python3 sandbox-probe.py` as the first command of the session. It tries
to open each protected path below, and to create an empty directory in each
shared temp directory, and passes only when the sandbox denies every one
(EACCES or EPERM). A missing path or any other error is a failure.
"""

import errno
import os
import sys

TARGETS = @@TARGETS@@
WRITE_TARGETS = @@WRITE_TARGETS@@


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
    for target in WRITE_TARGETS:
        probe = os.path.join(target, ".holdout-probe-%d" % os.getpid())
        try:
            os.mkdir(probe)
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EPERM):
                denied += 1
            continue
        os.rmdir(probe)
    total = len(TARGETS) + len(WRITE_TARGETS)
    if denied == total:
        print("OK: sandbox denied %d/%d protected reads and writes"
              % (denied, total))
        return 0
    print("PROBLEM: sandbox did not deny %d of %d protected reads and "
          "writes. Stop. Do not type begin. Close this session and reply: "
          "blocked sandbox" % (total - denied, total))
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


def _add_shared_tmp_controls(settings):
    """Deny the shared temp directories (shared_tmp_dirs) in every control:
    sandbox denyRead and denyWrite, permission Read and Edit (the file tools
    are not sandboxed; both the real and the /tmp spelling), guard
    --protect. Used for the finder and every cross-check generation."""
    try:
        deny = settings["permissions"]["deny"]
        fs = settings["sandbox"]["filesystem"]
        deny_read = fs["denyRead"]
    except (KeyError, TypeError):
        raise KitError("a settings template has the wrong shape")
    deny_write = fs.setdefault("denyWrite", [])
    guards = _guard_hooks(settings)
    if len(guards) != 1:
        raise KitError("a settings template does not hold exactly one "
                       "guard hook")
    args = guards[0][1]
    for p in shared_tmp_dirs():
        deny_read.append(p)
        deny_write.append(p)
        args.extend(["--protect", p])
    for p in _shared_tmp_rule_paths():
        deny.extend([_abs_rule("Read", p), _abs_rule("Edit", p)])


def _shared_tmp_gaps(settings):
    """Gaps in the shared-temp controls; [] when all are in place.

    Recomputes the paths from SHARED_TMP_NAMES and SHARED_TMP_PARENT itself
    (never through shared_tmp_dirs or _add_shared_tmp_controls), so it stays
    an independent oracle."""
    uid = os.getuid()
    base = os.path.realpath(SHARED_TMP_PARENT)
    names = [n % uid if "%" in n else n for n in SHARED_TMP_NAMES]
    real = [base + "/" + n for n in names]
    spelled = real + [SHARED_TMP_PARENT + "/" + n for n in names]
    deny_read = _list_at(settings, "sandbox", "filesystem", "denyRead")
    deny_write = _list_at(settings, "sandbox", "filesystem", "denyWrite")
    deny = _list_at(settings, "permissions", "deny")
    guards = _guard_hooks(settings)
    args = guards[0][1] if len(guards) == 1 else []
    protects = [args[i + 1] for i in range(len(args) - 1)
                if args[i] == "--protect"]
    problems = []
    for p in real:
        if p not in deny_read:
            problems.append("sandbox denyRead is missing the shared temp "
                            "directory %s" % p)
        if p not in deny_write:
            problems.append("sandbox denyWrite is missing the shared temp "
                            "directory %s" % p)
        if p not in protects:
            problems.append("hook --protect is missing the shared temp "
                            "directory %s" % p)
    for p in spelled:
        for tool in ("Read", "Edit"):
            rule = "%s(//%s/**)" % (tool, p.lstrip("/"))
            if rule not in deny:
                problems.append("permission deny is missing %s" % rule)
    return problems


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
    problems.extend(_shared_tmp_gaps(settings))
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


def role_env_problems(folder, gens=()):
    """Check that bin/role-env.sh holds ROLE_ENV_TEXT and that bin/finder and
    the launcher of each generation in `gens` name it in CLAUDE_ENV_FILE and
    set their own temp root; [] when all are in place. Without these a
    sandboxed role command's $TMPDIR stays the shared temp directory the
    sandbox denies (scratch files fail instead of landing in the role's own
    temp root)."""
    h = os.path.realpath(folder)
    problems = []
    env_path = os.path.join(h, "bin", "role-env.sh")
    if os.path.islink(env_path) \
            or _read_bytes_or_none(env_path) != ROLE_ENV_TEXT.encode("utf-8"):
        problems.append("bin/role-env.sh is missing or not the kit's")
    line = 'export CLAUDE_ENV_FILE="$H/bin/role-env.sh"'
    checks = [("bin/finder", 'CLAUDE_CODE_TMPDIR="$H/tmp/finder" '
                             'TMPDIR="$H/tmp/finder"')]
    for gen in gens:
        suffix = "" if gen == 1 else "-r%d" % gen
        tmp = "$H/tmp/crosscheck/xcheck" + suffix
        checks.append(("bin/crosscheck" + suffix,
                       'CLAUDE_CODE_TMPDIR="%s" TMPDIR="%s"' % (tmp, tmp)))
    for rel, tmp_line in checks:
        data = _read_bytes_or_none(os.path.join(h, *rel.split("/")))
        lines = (data or b"").decode("utf-8", "replace").splitlines()
        if line not in lines:
            problems.append("%s does not set CLAUDE_ENV_FILE to "
                            "bin/role-env.sh" % rel)
        if ROLE_PATH_LINE not in lines:
            problems.append("%s does not keep the owner's PATH" % rel)
        if "export " + tmp_line not in lines:
            problems.append("%s does not set its own temp root" % rel)
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
    # The shared per-user temp directory Claude Code points sandboxed
    # commands at (it always exists by the time the probe runs).
    targets.append(shared_tmp_dirs()[0])
    return targets


def _probe_write_targets():
    """Directories the probe must fail to create an entry in: the shared
    per-user temp directory (the 51-09 leak's landing place)."""
    return [shared_tmp_dirs()[0]]


def _xcheck_probe_text(h, prior):
    """<ws>/sandbox-probe.py for a generation whose earlier generations are
    `prior`."""
    return (XCHECK_SANDBOX_PROBE
            .replace("@@TARGETS@@", json.dumps(_probe_targets(h, prior),
                                               indent=4))
            .replace("@@WRITE_TARGETS@@",
                     json.dumps(_probe_write_targets(), indent=4)))


def _xcheck_settings_object(h, prior):
    """The settings make_xcheck_workspace writes for a generation whose
    earlier generations are `prior` (xcheck_names dicts). The one source the
    writer and refresh-kit use."""
    template = load_json(os.path.join(h, "kit", XCHECK_TEMPLATE),
                         what="the cross-check settings template")
    settings = _render_template(template, h, [])
    file_paths = frozenset(os.path.join(h, p) for p in XCHECK_FILE_PROTECTED)
    _add_controls(settings, _xcheck_protected_paths(h, prior), file_paths)
    _add_shared_tmp_controls(settings)
    return settings


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
    created = []
    try:
        settings = _xcheck_settings_object(h, prior)
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
        _write_text(os.path.join(ws, "sandbox-probe.py"),
                    _xcheck_probe_text(h, prior), 0o700)
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


def kit_inventory(folder):
    """The KIT-INVENTORY.json object for kit/ as it is now: sha256 of every
    file under kit/ but eligible-repos.json and the inventory itself."""
    kit = os.path.join(os.path.realpath(folder), "kit")
    files = {}
    for rel in walk_regular(kit):
        if rel in (KIT_INVENTORY, ELIGIBLE_REPOS):
            continue
        files[rel] = sha256_file(os.path.join(kit, rel))
    return {"schema": KIT_INVENTORY_SCHEMA, "files": files}


def write_kit_inventory(folder):
    """kit/KIT-INVENTORY.json: sha256 of every file under kit/ that setup
    copied from the repo (everything but eligible-repos.json and itself)."""
    inventory = kit_inventory(folder)
    write_json_atomic(os.path.join(os.path.realpath(folder), "kit",
                                   KIT_INVENTORY), inventory)
    return inventory


# ---------------------------------------------------------------- setup


def add_parser(sub, name):
    if name == "refresh-kit":
        sub.add_parser(
            "refresh-kit", help="re-copy the repo's current kit and tools "
                                "into an existing holdout folder (run it "
                                "from the repo's tools; state, logins and "
                                "sealed content are never touched)")
        return
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
    if args.cmd == "refresh-kit":
        # Every Claude-spawned shell is refused, isolated holdout sessions
        # included: only the owner changes the kit a session runs under.
        refuse_if_claude_spawned(None)
        return refresh_kit(args.folder)
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


def _kit_sources(h):
    """[(source path, destination path)] of every file setup copies into
    the folder's kit/: the kit docs and templates, the non-test tools, and
    the guard."""
    src_kit = _source_kit_dir()
    kit = os.path.join(h, "kit")
    pairs = []
    for name in sorted(os.listdir(src_kit)):
        if name.endswith((".md", ".json")) \
                and name not in (KIT_INVENTORY, ELIGIBLE_REPOS):
            pairs.append((os.path.join(src_kit, name),
                          os.path.join(kit, name)))
    for name in sorted(os.listdir(TOOLS_DIR)):
        if name.endswith(".py") and not name.startswith("test_"):
            pairs.append((os.path.join(TOOLS_DIR, name),
                          os.path.join(kit, "tools", name)))
    pairs.append((os.path.join(TOOLS_DIR, GUARD_NAME),
                  os.path.join(h, GUARD_REL)))
    return pairs


def _copy_kit(h):
    for src, dst in _kit_sources(h):
        _copy(src, dst)


def _finder_settings_objects(h, eligible):
    """(project settings, user settings) setup writes for the finder."""
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
    _add_shared_tmp_controls(settings)
    return settings, {"permissions": {
        "additionalDirectories": _finder_working_dirs(h, eligible)}}


def _write_finder_settings(h, eligible):
    settings, user = _finder_settings_objects(h, eligible)
    path = os.path.join(h, "work", ".claude", "settings.json")
    user_path = os.path.join(h, *FINDER_USER_SETTINGS.split("/"))
    write_json_atomic(path, settings)
    write_json_atomic(user_path, user)
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
    _write_text(os.path.join(h, *ROLE_ENV_REL.split("/")), ROLE_ENV_TEXT,
                0o600)
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


# ---------------------------------------------------------------- refresh

REFRESH_SOURCE_MSG = (
    "refresh-kit copies the repo's kit into the folder, so it must run from "
    "the repo's own tools: python3 ~/turingmind-code-review/docs/design/"
    "holdout-v2.12/tools/holdout_kit.py --folder <the holdout folder> "
    "refresh-kit")
REFRESH_SETUP_MSG = ("the holdout folder is not set up (kit/, kit/tools/, "
                     "bin/holdout and kit/KIT-INVENTORY.json must exist); "
                     "nothing was changed")
REFRESH_USER_SETTINGS_MSG = ("cfg-finder/settings.json is not a JSON object; "
                             "nothing was changed in the finder settings")
REFRESH_TOUCHED_MSG = ("refresh-kit changed a file outside kit/, the "
                       "launchers and the session settings (%d file(s)); "
                       "stop and report it")
# What refresh-kit may write, as folder relpaths. Everything else under the
# folder (sealed/, work/ but its settings, every cfg-*/ but the finder's
# settings file, archive/, tmp/, the xcheck workspaces but their settings
# and sandbox probe, the journal, the LEAKSCAN/RETIRED ledgers, SEAL.json,
# the dry-run repos) must keep its exact lstat identity, which refresh_kit
# checks before it returns.
REFRESH_WRITABLE_FILES = ("bin/finder", "bin/holdout", ROLE_ENV_REL,
                          "work/.claude/settings.json",
                          FINDER_USER_SETTINGS, DRYRUN_MARKER)
REFRESH_WRITABLE_RE = re.compile(
    r"^(kit/(?!%s$).+|bin/crosscheck(-r[0-9]+)?"
    r"|xcheck(-r[0-9]+)?/(\.claude/settings\.json|sandbox-probe\.py))$"
    % re.escape(ELIGIBLE_REPOS))


def _refresh_writable(rel):
    return rel in REFRESH_WRITABLE_FILES or bool(REFRESH_WRITABLE_RE.match(rel))


def _identity_snapshot(h):
    """{relpath: lstat identity} of every entry under the folder that
    refresh-kit must not write (symlinks included, never followed)."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(h, followlinks=False):
        for name in list(dirnames) + list(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, h).replace(os.sep, "/")
            try:
                st = os.lstat(full)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode) or _refresh_writable(rel):
                continue
            out[rel] = (st.st_mode, st.st_size, st.st_mtime_ns, st.st_ino)
    return out


def _read_bytes_or_none(path):
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def _write_text_if_changed(path, text, mode):
    """Write `text` (mode `mode`) only when the file differs; True when it
    was written."""
    if os.path.islink(path):
        raise KitError("%s is a symbolic link; remove it and run this again"
                       % os.path.basename(path))
    if _read_bytes_or_none(path) == text.encode("utf-8"):
        if stat.S_IMODE(os.stat(path).st_mode) != mode:
            os.chmod(path, mode)
            return True
        return False
    _write_text(path, text, mode)
    return True


def _json_or_none(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _refresh_eligible(h):
    """The eligible repos setup wrote the finder settings for: the finder's
    current grant minus sealed/ and kit/ (user settings, or the project
    settings of a folder set up before the grant moved), else
    kit/eligible-repos.json."""
    inside = {os.path.join(h, p) for p in FINDER_READ_DIRS}
    for rel in (FINDER_USER_SETTINGS, "work/.claude/settings.json"):
        dirs = _list_at(_json_or_none(os.path.join(h, *rel.split("/"))),
                        "permissions", "additionalDirectories")
        if dirs:
            return [d for d in dirs if isinstance(d, str) and d not in inside]
    return list(load_json(os.path.join(h, "kit", ELIGIBLE_REPOS),
                          required={"repos": list},
                          what="kit/eligible-repos.json")["repos"])


def _refresh_finder_settings(h):
    """Rewrite the finder's settings only where setup's output differs, then
    self-check both files; restore both on a failed self-check. Returns
    "rewritten" or "unchanged"."""
    path = os.path.join(h, "work", ".claude", "settings.json")
    user_path = os.path.join(h, *FINDER_USER_SETTINGS.split("/"))
    want, want_user = _finder_settings_objects(h, _refresh_eligible(h))
    old, old_user = _read_bytes_or_none(path), _read_bytes_or_none(user_path)
    user = {} if old_user is None else _json_or_none(user_path)
    if not isinstance(user, dict):
        raise KitError(REFRESH_USER_SETTINGS_MSG)
    changed = False
    if _json_or_none(path) != want:
        write_json_atomic(path, want)
        changed = True
    dirs = want_user["permissions"]["additionalDirectories"]
    perms = user.get("permissions")
    if not isinstance(perms, dict) \
            or perms.get("additionalDirectories") != dirs:
        # Only the grant is set; every other key Claude Code or the owner
        # keeps in this file stays as it is.
        user = dict(user)
        user["permissions"] = dict(perms) if isinstance(perms, dict) else {}
        user["permissions"]["additionalDirectories"] = dirs
        write_json_atomic(user_path, user)
        changed = True
    problems = finder_settings_problems(_json_or_none(path), h,
                                        _json_or_none(user_path))
    if problems:
        for target, data in ((path, old), (user_path, old_user)):
            if data is None:
                if os.path.lexists(target):
                    os.remove(target)
            else:
                with open(target, "wb") as fh:
                    fh.write(data)
        raise KitError("the finder settings failed their self-check after "
                       "refresh-kit (%s); the previous files were restored"
                       % problems[0])
    return "rewritten" if changed else "unchanged"


def _refresh_xcheck_generation(h, gen):
    """Regenerate generation `gen`'s settings and sandbox probe through the
    same generators make_xcheck_workspace uses (only where they differ),
    then self-check the settings; on a failed self-check restore both files
    and print one PROBLEM line. Returns "rewritten", "unchanged" or None
    (failed). Nothing else in the workspace is touched."""
    names = xcheck_names(gen)
    prior = [xcheck_names(k) for k in range(1, gen)]
    ws = os.path.join(h, names["workspace"])
    path = os.path.join(ws, ".claude", "settings.json")
    probe_path = os.path.join(ws, "sandbox-probe.py")
    for target in (os.path.dirname(path), path, probe_path):
        if os.path.islink(target):
            raise KitError("%s in %s is a symbolic link; remove it and run "
                           "this again" % (os.path.basename(target),
                                           names["workspace"]))
    old, old_probe = _read_bytes_or_none(path), _read_bytes_or_none(probe_path)
    want = _xcheck_settings_object(h, prior)
    changed = False
    if _json_or_none(path) != want:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_json_atomic(path, want)
        changed = True
    if _write_text_if_changed(probe_path, _xcheck_probe_text(h, prior),
                              0o700):
        changed = True
    if xcheck_settings_problems(_json_or_none(path), h, prior):
        for target, data, mode in ((path, old, None),
                                   (probe_path, old_probe, 0o700)):
            if data is None:
                if os.path.lexists(target):
                    os.remove(target)
                continue
            with open(target, "wb") as fh:
                fh.write(data)
            if mode is not None:
                os.chmod(target, mode)
        print_problem("cross-check settings of %s failed their self-check "
                      "after refresh-kit; the previous files were restored; "
                      "run setup again in a fresh folder" % names["workspace"])
        return None
    return "rewritten" if changed else "unchanged"


def _generations_present(h):
    gens = []
    for name in sorted(os.listdir(h)):
        m = XCHECK_WS_RE.match(name)
        if m and os.path.isdir(os.path.join(h, name)) \
                and not os.path.islink(os.path.join(h, name)):
            gens.append(1 if m.group(2) is None else int(m.group(2)))
    return sorted(gens)


def _refresh_dry_run_marker(h):
    """Add DRY-RUN.json to an existing folder only when the autopilot's
    mechanical proof (holdout_autopilot.dry_run_folder_problems) says it is
    a dry run; never to any other folder. Returns True (never a PROBLEM:
    a folder that is not a provable dry run is simply left unmarked)."""
    if dry_run_marker_ok(h):
        print_ok("dry-run marker present")
        return True
    if os.path.lexists(os.path.join(h, DRYRUN_MARKER)):
        print_problem("DRY-RUN.json exists but is not a valid marker for "
                      "this folder; it was not changed")
        return False
    autopilot = _load_module("holdout_autopilot")
    dryrun = _load_module("holdout_dryrun")
    if autopilot is None or dryrun is None:
        print_ok("dry-run marker: not added (autopilot or dryrun not "
                 "installed)")
        return True
    problems = autopilot.dry_run_folder_problems(h)
    if problems:
        print_ok("dry-run marker: not added (not a provable dry run: %s)"
                 % problems[0])
        return True
    write_dry_run_marker(h, dryrun._now_iso())
    print_ok("dry-run marker added (journal, dry-run repos and every case "
             "prove this folder is a dry run)")
    return True


def refresh_kit(folder):
    """Bring an existing holdout folder's kit up to the repo's current one.

    Re-copies the kit docs, templates and tools (only files whose bytes
    differ), rewrites kit/KIT-INVENTORY.json when it changed, rewrites
    bin/finder, bin/holdout, each existing bin/crosscheck[-rN] and
    bin/role-env.sh only when setup's text for it changed, the finder
    settings only where setup's output changed (cfg-finder/settings.json:
    only its grant key), and each existing cross-check generation's
    .claude/settings.json and sandbox-probe.py only where
    make_xcheck_workspace's generators now differ. Every settings file is
    self-checked after it is written (restored on a failure). Then adds
    DRY-RUN.json only to a folder the autopilot's mechanical proof shows is
    a dry run, and verifies nothing else under the folder changed (session
    state, logins, packets, ledgers and sealed content).
    Idempotent. Returns the exit code: 0 when every line is OK, 1 when any
    is a PROBLEM."""
    refuse_if_claude_spawned(None)
    if not folder:
        raise KitError("the holdout folder must be given explicitly")
    repo_kit = os.path.normpath(os.path.join(TOOLS_DIR, "..", "kit"))
    if not os.path.isdir(repo_kit):
        raise KitError(REFRESH_SOURCE_MSG)
    h = os.path.realpath(folder)
    for rel in ("kit", "kit/tools", "bin"):
        path = os.path.join(h, *rel.split("/"))
        if os.path.islink(path) or not os.path.isdir(path):
            raise KitError(REFRESH_SETUP_MSG)
    for rel in ("bin/holdout", "kit/" + KIT_INVENTORY):
        if not os.path.isfile(os.path.join(h, *rel.split("/"))):
            raise KitError(REFRESH_SETUP_MSG)
    if os.path.realpath(TOOLS_DIR) == os.path.join(h, "kit", "tools") \
            or os.path.realpath(repo_kit) == os.path.join(h, "kit"):
        raise KitError(REFRESH_SOURCE_MSG)
    before = _identity_snapshot(h)
    ok = True

    updated = kept = 0
    for src, dst in _kit_sources(h):
        if os.path.islink(dst):
            raise KitError("kit file %s is a symbolic link; remove it and run "
                           "this again" % os.path.basename(dst))
        if os.path.islink(src) or not os.path.isfile(src):
            raise KitError("kit file %s is missing or not a regular file"
                           % os.path.basename(src))
        if _read_bytes_or_none(dst) == _read_bytes_or_none(src):
            kept += 1
            continue
        _copy(src, dst)
        updated += 1
    print_ok("kit: %d file(s) updated, %d already current" % (updated, kept))

    inventory = kit_inventory(h)
    inv_path = os.path.join(h, "kit", KIT_INVENTORY)
    if _json_or_none(inv_path) != inventory:
        write_json_atomic(inv_path, inventory)
        print_ok("kit inventory rewritten (%d file(s))"
                 % len(inventory["files"]))
    else:
        print_ok("kit inventory already current (%d file(s))"
                 % len(inventory["files"]))

    # Only launchers that exist are refreshed: scrub removes all but
    # bin/holdout, and refresh-kit never recreates what scrub removed.
    quoted = _sh_quote(h)
    launchers = [(os.path.join(h, "bin", "holdout"),
                  HOLDOUT_LAUNCHER.replace("@@H@@", quoted))]
    if os.path.isfile(os.path.join(h, "bin", "finder")):
        launchers.append((os.path.join(h, "bin", "finder"),
                          FINDER_LAUNCHER.replace("@@H@@", quoted)))
    gens = _generations_present(h)
    for gen in gens:
        names = xcheck_names(gen)
        path = os.path.join(h, *names["launcher"].split("/"))
        if os.path.isfile(path):
            launchers.append((path, XCHECK_LAUNCHER
                              .replace("@@H@@", quoted)
                              .replace("@@WS@@", names["workspace"])
                              .replace("@@CFG@@", names["config_dir"])
                              .replace("@@TMP@@", names["tmp_dir"])))
    role_launchers = len(launchers) > 1
    rewritten = sum(1 for path, text in launchers
                    if _write_text_if_changed(path, text, 0o700))
    print_ok("launchers: %d rewritten, %d already current"
             % (rewritten, len(launchers) - rewritten))

    if os.path.isfile(os.path.join(h, "work", ".claude", "settings.json")):
        state = _refresh_finder_settings(h)
        print_ok("finder settings %s; self-check passed" % state)
    else:
        print_ok("finder settings absent (folder already scrubbed); skipped")

    if role_launchers:
        state = ("rewritten" if _write_text_if_changed(
            os.path.join(h, *ROLE_ENV_REL.split("/")), ROLE_ENV_TEXT, 0o600)
            else "already current")
        print_ok("role session environment (%s) %s" % (ROLE_ENV_REL, state))

    changed = 0
    for gen in gens:
        state = _refresh_xcheck_generation(h, gen)
        if state is None:
            ok = False
        elif state == "rewritten":
            changed += 1
    if gens:
        print_ok("cross-check settings and sandbox probes: %d generation(s) "
                 "rewritten, %d already current; self-check run on each"
                 % (changed, len(gens) - changed))

    ok = _refresh_dry_run_marker(h) and ok

    after = _identity_snapshot(h)
    touched = sorted(set(before) ^ set(after)
                     | {r for r in before if after.get(r) != before[r]})
    if touched:
        print_problem(REFRESH_TOUCHED_MSG % len(touched))
        return 1
    print_ok("state untouched: sealed/, work/, logins, archive/, journal, "
             "ledgers and cross-check workspaces (%d file(s) checked)"
             % len(before))
    return 0 if ok else 1


# ---------------------------------------------------------------- CLI

COMMANDS = {
    "setup": "holdout_kit",
    "refresh-kit": "holdout_kit",
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
    "diagnose": "holdout_seal",
    "encrypt": "holdout_archive",
    "decrypt": "holdout_archive",
    "leakscan": "holdout_archive",
    "scrub": "holdout_archive",
    "dryrun": "holdout_dryrun",
    "autopilot": "holdout_autopilot",
    "denials": "holdout_autopilot",
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
