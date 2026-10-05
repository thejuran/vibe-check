"""fixstage.py — the fix agent's trusted git path: per-attempt snapshot, seal, undo.

## What it replaces (999.15)

The fix agent used to commit with `git add <paths>` + `git commit -- <paths>`.
A pathspec commit has `--only` semantics: it commits the WORKING-TREE bytes of
each path, so any owner edit sitting in the same file was swept into the fix's
commit no matter what had been staged. And its undo was "restore from HEAD",
which erased owner work made before the fix. This module records exactly what
the fix changed, so undo (and the isolated commit built on the same state)
touches only the fix's own delta.

## The attempt lifecycle

    begin    -> a fresh attempt id (32 hex) for this finding
    snapshot -> before the FIRST edit of each path: pre-edit bytes, mode, state
    seal     -> right after the LAST edit, before any check runs: post-edit bytes
    undo | commit -> a terminal outcome; the attempt is closed

Why attempts exist (adversarial finding 3): snapshot state lives on disk across
Bash calls and across passes. A snapshot left behind by a failed earlier attempt
must never be treated as the current one by a retry. So every attempt has its
own id, every subcommand except `begin` refuses any id that is not the finding's
currently open attempt, and every terminal outcome closes the attempt into a
quarantine directory that no subcommand ever reads again. `begin` quarantines a
stale open attempt left by a crashed run before starting a fresh one.

Why `seal` exists (adversarial finding 1): the check that decides whether a fix
is kept can take a while, and the owner may keep editing meanwhile. Undo and
commit therefore work from the agent's OWN recorded post-edit bytes, never from
whatever is in the working tree at the end, so owner edits made while the check
runs are neither erased (undo) nor swept in (commit).

## State layout

All under `<repo>/.turingmind/fixstage/<id>/` (id validated `^[0-9a-f]{8,64}$`):

    open                       the one open attempt id (absent = none open)
    <attempt>/manifest.json    {"attempt", "head", "sealed", "paths": [...]}
    <attempt>/<n>.pre, <n>.post  byte copies, named by index, never by path text
    closed/<attempt>.<outcome>/  quarantine; never read again; pruned to 5

Manifest path entries: `path`, `n`, `state` (tracked | untracked | absent —
absent means not on disk before the edit), `mode`, `index_blob`, `pre_sha256`,
and after seal `post_state` (present | absent), `post_mode`, `post_sha256`.
Closing outcomes: committed (dir removed) | undone | undo-partial | refused |
not-separable | hook-rejected | hook-changed | head-moved | moved-after-commit |
stale.

## CLI and exit codes

The finding record is a JSON file the fix agent writes with its Write tool
(`{"id", "pass_number", "title", "paths"}`); attacker-influenced text never
reaches argv (FL-03, see fixcommit.py). Flags: `--root`, `--finding-json`,
`--attempt` only — any other flag is a usage error.

    begin    --root R --finding-json J
        0 `attempt=<32hex>` (preceded by `quarantined=<old>` when a stale open
          attempt was closed as `stale`) | 1 refused | 2 usage
    snapshot --root R --finding-json J --attempt A
        0 | 1 refused (attempt not open; sealed; validation) | 2 usage
    seal     --root R --finding-json J --attempt A
        0 | 1 refused (attempt not open; already sealed; a record path has no
          snapshot — the attempt is then closed as `refused`) | 2 usage
    undo     --root R --finding-json J --attempt A
        0 every path reversed, closed `undone` | 3 `not-undone: <path>` lines,
          the other paths ARE reversed, closed `undo-partial` | 1 refused
          (attempt not open; not sealed) | 2 usage
    commit   --root R --finding-json J --attempt A
        0 `commit_sha=<sha>` (+ `index-left-as-is: <path>` lines), closed
          `committed` | 1 refused (attempt not open or not sealed; title, pass
          number or path validation; git older than 2.36) | 2 usage
        3 `not-separable: <reason>` - nothing committed, fix stays applied
        4 `commit-not-created: <reason>` + hook output tail - an owner hook
          rejected the commit or signing failed; nothing published
        5 `hook-changed: <sha>` - published, but an owner hook changed the
          committed content; nothing rewritten
        6 `head-moved: <reason>` - the branch moved before publishing; nothing
          published
        7 `moved-after-commit: <sha>` - published, then HEAD moved again

Refusals print a fixed reason on stderr that names the failing rule. Callers
branch on the EXIT CODE.

## The isolated commit

`commit` never commits working-tree bytes and never commits through the real
index. It reads HEAD exactly once, at the start (BASE), and binds every later
step to that one sha: each fix path's BASE version is merged with ONLY the
sealed pre->post delta (`git merge-file`), the result is hashed into a blob, a
temporary index is built from BASE plus those blobs, the owner's commit hooks
run against that temporary index (`git hook run`, the same order and
environment `git commit` uses), and `git commit-tree -p BASE` builds the commit
object (`-S` when commit.gpgSign is set, because commit-tree does not read that
setting itself).

Publication is ONE ref compare-and-swap that only succeeds while the branch
still points at BASE (see `_publish_ref`). If anything moved the branch after
BASE was read - another terminal, an owner hook - nothing is published, so a
fix commit can never put an older tree on top of a newer parent. Nothing in
this module ever rewinds, deletes or force-moves a ref.

The real index is synced afterwards so the staging area shows no staged
reversal of the fix, but only while holding git's own `index.lock`, and only
for entries that are still exactly what they were before the commit started
(`_sync_real_index`). Anything else is printed `index-left-as-is: <path>`.

I/O: stdlib only, imports exactly {hashlib, json, os, re, shutil, subprocess,
sys, tempfile, time} plus the sibling `fixcommit` (path validation and the
commit message are single-sourced there; fixcommit itself stays
subprocess-free). Every subprocess call is an argv list with a timeout, never a
shell string, and every git call puts `--` before path arguments. Undo never
moves HEAD and never touches the index.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixcommit  # noqa: E402  (the ONE path-validation source)

ID_RE = re.compile(r"^[0-9a-f]{8,64}$")
ATTEMPT_RE = re.compile(r"^[0-9a-f]{32}$")

SUBCOMMANDS = ("begin", "snapshot", "seal", "undo", "commit")
KNOWN_FLAGS = ("--root", "--finding-json", "--attempt")

# Top-level directories a fix may never snapshot or write: git's own state and
# this tool's state (compared case-insensitively for case-insensitive filesystems).
RESERVED_TOP = (".git", ".turingmind")

CLOSED_KEEP = 5
GIT_TIMEOUT = 120
# Owner hooks (a pre-commit running a test suite) may legitimately be slow.
HOOK_TIMEOUT = 900

# `git hook run` (used to run the owner's hooks around commit-tree) needs 2.36.
MIN_GIT_FOR_HOOKS = (2, 36)

# Bounded wait for git's own index.lock before giving up on the index sync.
INDEX_LOCK_RETRIES = 20
INDEX_LOCK_WAIT = 0.05

HOOK_TAIL_LINES = 20
OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
REGULAR_MODES = ("100644", "100755")

USAGE = ("usage: fixstage.py begin --root <repo> --finding-json <file>\n"
         "       fixstage.py {snapshot|seal|undo|commit} --root <repo> "
         "--finding-json <file> --attempt <32hex>\n")

REFUSED_STALE = "refused: stale or unknown attempt"


class Refused(Exception):
    """A fixed, printable refusal reason (exit 1)."""


# ---------------------------------------------------------------- CLI parsing

def parse_argv(argv):
    """Hand-rolled (fixcommit shape) -> ((subcommand, values), None) or (None, err)."""
    if not argv:
        return None, "missing subcommand\n"
    sub = argv[0]
    if sub not in SUBCOMMANDS:
        return None, "unknown subcommand: %s\n" % sub
    values = {}
    rest = argv[1:]
    i = 0
    while i < len(rest):
        token = rest[i]
        if token not in KNOWN_FLAGS:
            return None, "unrecognized arguments: %s\n" % token
        if i + 1 >= len(rest):
            return None, "argument %s: expected one argument\n" % token
        if token in values:
            return None, "argument %s: given more than once\n" % token
        values[token] = rest[i + 1]
        i += 2
    required = ["--root", "--finding-json"]
    if sub == "begin":
        if "--attempt" in values:
            return None, "begin does not take --attempt\n"
    else:
        required.append("--attempt")
    missing = [f for f in required if f not in values]
    if missing:
        return None, ("the following arguments are required: %s\n"
                      % ", ".join(missing))
    return (sub, values), None


# ---------------------------------------------------------------- git + files

def _env(index_file=None):
    """os.environ without any inherited GIT_INDEX_FILE (the real index is
    always `git rev-parse --git-path index`), optionally pointing git at
    `index_file` instead."""
    env = dict(os.environ)
    env.pop("GIT_INDEX_FILE", None)
    if index_file is not None:
        env["GIT_INDEX_FILE"] = index_file
    return env


def _git(root, *args, binary=False, env=None):
    """git in `root` (argv list, no shell); returns the CompletedProcess."""
    return subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=not binary,
                          env=_env() if env is None else env,
                          timeout=GIT_TIMEOUT)


def _check_toplevel(root):
    if not isinstance(root, str) or not root or not os.path.isdir(root):
        raise Refused("refused: root is not an existing directory")
    proc = _git(root, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        raise Refused("refused: root is not inside a git repository")
    if os.path.realpath(proc.stdout.strip()) != os.path.realpath(root):
        raise Refused("refused: root is not the repository top level")


def _validate_paths(root, paths):
    """fixcommit.validate_paths plus normal form and reserved-directory checks."""
    ok, reason = fixcommit.validate_paths(root, paths)
    if not ok:
        raise Refused(reason)
    for path in paths:
        if os.path.normpath(path) != path:
            # `a/./b`, `a/../b` or a trailing slash would give one file two
            # manifest keys; refuse rather than canonicalize.
            raise Refused("refused: path is not in normal form")
        if path.split("/", 1)[0].lower() in RESERVED_TOP:
            raise Refused("refused: path is inside a reserved directory")


def _load_record(root, record_path):
    try:
        with open(record_path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError, UnicodeDecodeError):
        raise Refused("refused: finding record is missing or not valid JSON")
    if not isinstance(record, dict):
        raise Refused("refused: finding record is not an object")
    fid = record.get("id")
    if not isinstance(fid, str) or ID_RE.match(fid) is None:
        raise Refused("refused: finding id is not lowercase hex (8-64)")
    paths = record.get("paths")
    _validate_paths(root, paths)
    return record


def stage_dir(root, fid):
    """`<root>/.turingmind/fixstage/<fid>/`; raises Refused on a non-hex id."""
    if not isinstance(fid, str) or ID_RE.match(fid) is None:
        raise Refused("refused: finding id is not lowercase hex (8-64)")
    return os.path.join(root, ".turingmind", "fixstage", fid)


def attempt_dir(root, fid, attempt):
    """`<stage_dir>/<attempt>/`; raises Refused unless attempt is 32 hex."""
    if not isinstance(attempt, str) or ATTEMPT_RE.match(attempt) is None:
        raise Refused("refused: attempt id is not 32 lowercase hex")
    return os.path.join(stage_dir(root, fid), attempt)


def _atomic_write(path, data):
    """Write bytes via a temp file in the same directory + os.replace."""
    parent = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix=".fixstage-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.lexists(tmp):
            os.unlink(tmp)


def _read_path(abspath):
    """Current state of a path -> {present, regular, bytes, mode}.

    Never follows a symlink: a symlink, directory or other non-regular entry is
    `present` but not `regular`, and no bytes are read from it.
    """
    if not os.path.lexists(abspath):
        return {"present": False, "regular": True, "bytes": None, "mode": None}
    if os.path.islink(abspath) or not os.path.isfile(abspath):
        return {"present": True, "regular": False, "bytes": None, "mode": None}
    try:
        fd = os.open(abspath, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        # Replaced by a symlink (ELOOP) between the checks above and the open.
        return {"present": True, "regular": False, "bytes": None, "mode": None}
    try:
        mode = os.fstat(fd).st_mode & 0o7777
        chunks = []
        while True:
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(fd)
    return {"present": True, "regular": True, "bytes": b"".join(chunks),
            "mode": mode}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _read_open(sdir):
    try:
        with open(os.path.join(sdir, "open"), "r", encoding="ascii") as fh:
            return fh.read().strip()
    except (OSError, UnicodeDecodeError):
        return None


def _load_manifest(adir):
    try:
        with open(os.path.join(adir, "manifest.json"), "r",
                  encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError, UnicodeDecodeError):
        raise Refused("refused: attempt state is missing or corrupt")
    if (not isinstance(manifest, dict)
            or not isinstance(manifest.get("paths"), list)
            or not isinstance(manifest.get("sealed"), bool)):
        raise Refused("refused: attempt state is missing or corrupt")
    for entry in manifest["paths"]:
        if (not isinstance(entry, dict) or not isinstance(entry.get("n"), int)
                or isinstance(entry.get("n"), bool)
                or not isinstance(entry.get("path"), str)):
            raise Refused("refused: attempt state is missing or corrupt")
    return manifest


def _save_manifest(adir, manifest):
    _atomic_write(os.path.join(adir, "manifest.json"),
                  json.dumps(manifest, indent=1, sort_keys=True).encode("utf-8"))


# ---------------------------------------------------------- attempt lifecycle

def _require_open_attempt(root, fid, attempt):
    """The attempt dir if `attempt` is the finding's open attempt, else Refused.

    The ONE gate every subcommand except `begin` passes through. A stale id (a
    closed or quarantined attempt, or one that never existed) is refused with
    no state change.
    """
    adir = attempt_dir(root, fid, attempt)
    if _read_open(stage_dir(root, fid)) != attempt or not os.path.isdir(adir):
        raise Refused(REFUSED_STALE)
    return adir


def _close_attempt(root, fid, attempt, outcome):
    """Close `attempt`: `committed` removes its dir, any other outcome moves it
    to `closed/<attempt>.<outcome>/`, which no subcommand ever reads again.

    `open` is removed FIRST, so a crash mid-close leaves no open attempt
    pointing at a half-moved directory.
    """
    sdir = stage_dir(root, fid)
    adir = attempt_dir(root, fid, attempt)
    open_file = os.path.join(sdir, "open")
    if _read_open(sdir) == attempt and os.path.lexists(open_file):
        os.unlink(open_file)
    if not os.path.isdir(adir):
        return
    if outcome == "committed":
        shutil.rmtree(adir)
        return
    closed = os.path.join(sdir, "closed")
    os.makedirs(closed, exist_ok=True)
    target = os.path.join(closed, "%s.%s" % (attempt, outcome))
    if os.path.lexists(target):
        shutil.rmtree(target)
    os.replace(adir, target)
    # mtime = close time, so pruning keeps the most recently closed attempts.
    os.utime(target)


def _prune_closed(sdir):
    closed = os.path.join(sdir, "closed")
    if not os.path.isdir(closed):
        return
    entries = []
    for name in os.listdir(closed):
        path = os.path.join(closed, name)
        entries.append((os.lstat(path).st_mtime, name, path))
    entries.sort(reverse=True)
    for _, _, path in entries[CLOSED_KEEP:]:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)


def cmd_begin(root, record):
    fid = record["id"]
    sdir = stage_dir(root, fid)
    os.makedirs(sdir, exist_ok=True)
    out = []
    old = _read_open(sdir)
    if old is not None:
        if ATTEMPT_RE.match(old) and os.path.isdir(os.path.join(sdir, old)):
            _close_attempt(root, fid, old, "stale")
            out.append("quarantined=%s" % old)
        else:
            os.unlink(os.path.join(sdir, "open"))
    # An attempt dir with no `open` file (a crash between creating the dir and
    # writing `open`) is stale too.
    for name in sorted(os.listdir(sdir)):
        if ATTEMPT_RE.match(name) and os.path.isdir(os.path.join(sdir, name)):
            _close_attempt(root, fid, name, "stale")
            out.append("quarantined=%s" % name)
    _prune_closed(sdir)

    attempt = os.urandom(16).hex()
    adir = attempt_dir(root, fid, attempt)
    os.makedirs(adir)
    _save_manifest(adir, {"attempt": attempt, "head": None, "sealed": False,
                          "paths": []})
    _atomic_write(os.path.join(sdir, "open"), attempt.encode("ascii"))
    out.append("attempt=%s" % attempt)
    sys.stdout.write("\n".join(out) + "\n")
    return 0


def _head(root):
    proc = _git(root, "rev-parse", "-q", "--verify", "HEAD")
    return proc.stdout.strip() if proc.returncode == 0 else None


def _index_blob(root, path):
    # `:<path>` is a revision, not a pathspec, so it cannot sit after `--`;
    # the path is validated (no leading dash) and the `:` prefix keeps it from
    # ever parsing as an option.
    proc = _git(root, "rev-parse", "-q", "--verify", ":" + path)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _is_tracked(root, path):
    proc = _git(root, "--literal-pathspecs", "ls-files", "--error-unmatch",
                "--", path)
    return proc.returncode == 0


def cmd_snapshot(root, record, attempt):
    adir = _require_open_attempt(root, record["id"], attempt)
    manifest = _load_manifest(adir)
    if manifest["sealed"]:
        raise Refused("refused: attempt sealed; snapshot before editing")
    known = {entry["path"] for entry in manifest["paths"]}
    if manifest.get("head") is None and not manifest["paths"]:
        manifest["head"] = _head(root)
    for path in record["paths"]:
        if path in known:
            continue  # never overwrite a pre-edit snapshot
        current = _read_path(os.path.join(root, path))
        if not current["regular"]:
            raise Refused("refused: path is not a regular file")
        n = len(manifest["paths"])
        entry = {"path": path, "n": n, "mode": current["mode"],
                 "index_blob": _index_blob(root, path), "pre_sha256": None,
                 "post_state": None, "post_mode": None, "post_sha256": None}
        if current["present"]:
            entry["state"] = "tracked" if _is_tracked(root, path) else "untracked"
            _atomic_write(os.path.join(adir, "%d.pre" % n), current["bytes"])
            entry["pre_sha256"] = _sha(current["bytes"])
        else:
            entry["state"] = "absent"
        manifest["paths"].append(entry)
        known.add(path)
    _save_manifest(adir, manifest)
    return 0


def cmd_seal(root, record, attempt):
    fid = record["id"]
    adir = _require_open_attempt(root, fid, attempt)
    manifest = _load_manifest(adir)
    if manifest["sealed"]:
        raise Refused("refused: attempt already sealed")
    known = {entry["path"] for entry in manifest["paths"]}
    if any(path not in known for path in record["paths"]):
        _close_attempt(root, fid, attempt, "refused")
        raise Refused("refused: a path was edited without a pre-edit snapshot")
    for entry in manifest["paths"]:
        current = _read_path(os.path.join(root, entry["path"]))
        if not current["regular"]:
            _close_attempt(root, fid, attempt, "refused")
            raise Refused("refused: a path is not a regular file after the edit")
        if current["present"]:
            _atomic_write(os.path.join(adir, "%d.post" % entry["n"]),
                          current["bytes"])
            entry["post_state"] = "present"
            entry["post_mode"] = current["mode"]
            entry["post_sha256"] = _sha(current["bytes"])
        else:
            entry["post_state"] = "absent"
            entry["post_mode"] = None
            entry["post_sha256"] = None
    manifest["sealed"] = True
    _save_manifest(adir, manifest)
    return 0


def _stored(adir, n, suffix, expected_sha):
    """A stored byte copy, or None when it is missing or fails its digest."""
    if expected_sha is None:
        return None
    path = os.path.join(adir, "%d.%s" % (n, suffix))
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    return data if _sha(data) == expected_sha else None


def _undo_view(root, adir, entry):
    """The manifest entry plus its stored bytes, for `_reverse_path`.

    `intact` is False when a stored copy the entry promises is missing or does
    not match its recorded digest; such a path is never written.
    """
    view = dict(entry)
    view["root"] = root
    view["workdir"] = adir
    view["pre"] = None
    view["post"] = None
    intact = entry.get("post_state") in ("present", "absent")
    if entry.get("state") in ("tracked", "untracked"):
        view["pre"] = _stored(adir, entry["n"], "pre", entry.get("pre_sha256"))
        intact = intact and view["pre"] is not None
    elif entry.get("state") != "absent":
        intact = False
    if entry.get("post_state") == "present":
        view["post"] = _stored(adir, entry["n"], "post", entry.get("post_sha256"))
        intact = intact and view["post"] is not None
    view["intact"] = intact
    return view


def _merge_reverse(entry, current):
    """`git merge-file -p <current> <post> <pre>`: apply only post->pre onto
    what is there now. Returns the merged bytes, or None on conflict/error."""
    adir = entry["workdir"]
    n = entry["n"]
    cur_copy = os.path.join(adir, "%d.cur" % n)
    try:
        _atomic_write(cur_copy, current["bytes"])
        proc = _git(entry["root"], "merge-file", "-p", "--", cur_copy,
                    os.path.join(adir, "%d.post" % n),
                    os.path.join(adir, "%d.pre" % n), binary=True)
    finally:
        if os.path.lexists(cur_copy):
            os.unlink(cur_copy)
    # rc > 0 counts conflicts; rc < 0 (255 from the shell's view) is an error,
    # e.g. a binary file. Either way the file is left as it is.
    if proc.returncode != 0:
        return None
    return proc.stdout


def _reverse_path(entry, current):
    """Decide how to reverse ONE path -> ("restored"|"merged"|"kept", bytes|None).

    `restored` with None means delete. Undo reverses only the fix's own delta:
      (a) current == sealed post (presence and bytes) -> restore pre exactly
      (b) changed since seal, the fix created the file -> keep
      (c) changed since seal, the fix deleted the file -> keep
      (d) changed since seal, both exist -> reverse merge-file; conflict -> keep
    Never restores from HEAD and never restores pre over a changed file: that
    would erase owner edits made before the fix or while the check ran.
    """
    if not entry["intact"] or not current["regular"]:
        return ("kept", None)
    post_present = entry["post_state"] == "present"
    if current["present"] == post_present and (
            not post_present or current["bytes"] == entry["post"]):
        return ("restored", entry["pre"])
    if entry["pre"] is None or not post_present or not current["present"]:
        return ("kept", None)
    merged = _merge_reverse(entry, current)
    if merged is None:
        return ("kept", None)
    return ("merged", merged)


def _same_state(a, b):
    return (a["present"] == b["present"] and a["regular"] == b["regular"]
            and a["bytes"] == b["bytes"] and a["mode"] == b["mode"])


def _apply(abspath, current, data, mode):
    """Write `data` (None = delete) with `mode`, unless the file changed again
    since `current` was read. Returns True when applied."""
    if data is None:
        if not current["present"]:
            return True
        if not _same_state(_read_path(abspath), current):
            return False
        os.unlink(abspath)
        return True
    parent = os.path.dirname(abspath)
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix=".fixstage-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, mode)
        if not _same_state(_read_path(abspath), current):
            return False
        os.replace(tmp, abspath)
        tmp = None
        return True
    finally:
        if tmp is not None and os.path.lexists(tmp):
            os.unlink(tmp)


def cmd_undo(root, record, attempt):
    fid = record["id"]
    adir = _require_open_attempt(root, fid, attempt)
    manifest = _load_manifest(adir)
    if not manifest["sealed"]:
        raise Refused("refused: attempt not sealed")
    # The manifest is our own state, but it decides where undo writes: re-run
    # the same path validation the record passed before trusting it.
    _validate_paths(root, [entry["path"] for entry in manifest["paths"]])
    kept = []
    for entry in manifest["paths"]:
        path = entry["path"]
        abspath = os.path.join(root, path)
        try:
            current = _read_path(abspath)
            action, data = _reverse_path(_undo_view(root, adir, entry), current)
            if action == "kept":
                kept.append(path)
                continue
            if data is None:
                mode = None
            elif action == "restored" and not current["present"]:
                mode = entry["mode"]
            elif current["mode"] == entry.get("post_mode"):
                mode = entry["mode"]
            else:
                mode = current["mode"]  # the owner changed the mode since seal
            if not _apply(abspath, current, data, mode):
                kept.append(path)
        except (OSError, subprocess.SubprocessError) as exc:
            sys.stderr.write("undo: %s while reversing a path; left as is\n"
                             % type(exc).__name__)
            kept.append(path)
    for path in kept:
        # Paths passed PATH_RE validation, so they are safe to print.
        sys.stdout.write("not-undone: %s\n" % path)
    _close_attempt(root, fid, attempt, "undo-partial" if kept else "undone")
    return 3 if kept else 0


# ------------------------------------------------------------------ commit

class _Outcome(Exception):
    """A terminal commit outcome: exit code, closing outcome, stdout lines."""

    def __init__(self, code, outcome, lines):
        Exception.__init__(self, outcome)
        self.code = code
        self.outcome = outcome
        self.lines = lines


def _not_separable(reason):
    return _Outcome(3, "not-separable", ["not-separable: " + reason])


def _race_point(root, label):
    """No-op seam. Labels: after-base, after-read-tree, after-hooks, in-publish.

    Tests replace it to land a commit from "another terminal" at exactly that
    point of the transaction, so every race is reproduced deterministically.
    """
    return None


def _between_compare_and_publish(root):
    """No-op seam inside the index-lock window of `_sync_real_index`."""
    return None


def _git_version(root):
    proc = _git(root, "version")
    match = re.search(r"(\d+)\.(\d+)", proc.stdout or "")
    if proc.returncode != 0 or match is None:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def _capture_base(root):
    """BASE for one commit -> (sha | None when unborn, symref | None when
    detached). The ONLY read of HEAD before publishing: every blob read, tree
    comparison, the temporary index and the commit's parent use this literal
    sha, because each separate read of HEAD may observe a different commit."""
    proc = _git(root, "rev-parse", "-q", "--verify", "HEAD^{commit}")
    sha = proc.stdout.strip() if proc.returncode == 0 else None
    sym = _git(root, "symbolic-ref", "-q", "HEAD")
    symref = sym.stdout.strip() if sym.returncode == 0 else None
    return sha, symref


def _head_state(root):
    """HEAD now -> (sha | None, symref | None). Used only for the re-checks
    just before publishing and after the post-commit hook."""
    proc = _git(root, "rev-parse", "-q", "--verify", "HEAD^{commit}")
    sha = proc.stdout.strip() if proc.returncode == 0 else None
    sym = _git(root, "symbolic-ref", "-q", "HEAD")
    symref = sym.stdout.strip() if sym.returncode == 0 else None
    return sha, symref


def _decode(data):
    return data.decode("utf-8", "surrogateescape")


def _read_index_entries(root, index_file, paths):
    """Index entries -> {path: (mode, oid, stage) | None}.

    `index_file` None reads the real index. `paths` None returns every entry;
    otherwise exactly the given paths (None when absent). An unmerged path keeps
    an entry with stage != 0, so a caller can never mistake it for a clean one.
    """
    args = ["--literal-pathspecs", "ls-files", "-s", "-z"]
    if paths is not None:
        args += ["--"] + list(paths)
    proc = _git(root, *args, binary=True, env=_env(index_file))
    if proc.returncode != 0:
        raise Refused("refused: could not read the index")
    wanted = None if paths is None else set(paths)
    entries = {}
    for record in _decode(proc.stdout).split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        parts = meta.split(" ")
        if len(parts) != 3 or (wanted is not None and path not in wanted):
            continue
        entry = (parts[0], parts[1], int(parts[2]))
        previous = entries.get(path)
        if previous is None or entry[2] != 0:
            entries[path] = entry
    if wanted is not None:
        for path in wanted:
            entries.setdefault(path, None)
    return entries


def _entry_equal(a, b):
    """Complete index-entry comparison: mode, oid AND stage (a mode-only
    chmod is a change too)."""
    return a == b


def _base_entry(root, base, path):
    """`path` in the BASE commit -> (mode, oid) | None."""
    if base is None:
        return None
    proc = _git(root, "--literal-pathspecs", "ls-tree", "-z", base, "--", path,
                binary=True)
    if proc.returncode != 0:
        raise Refused("refused: could not read the last commit")
    for record in _decode(proc.stdout).split("\0"):
        meta, _, name = record.partition("\t")
        parts = meta.split(" ")
        if name == path and len(parts) == 3:
            return (parts[0], parts[2])
    return None


def _git_mode(perm):
    return "100755" if perm is not None and perm & 0o111 else "100644"


def _post_bytes(root, adir, entry):
    """The SEALED post-edit bytes of a path - never the working tree, so owner
    edits made after seal can never enter the commit."""
    data = _stored(adir, entry["n"], "post", entry.get("post_sha256"))
    if data is None:
        raise Refused("refused: attempt state is missing or corrupt")
    return data


def _pre_bytes(adir, entry):
    data = _stored(adir, entry["n"], "pre", entry.get("pre_sha256"))
    if data is None:
        raise Refused("refused: attempt state is missing or corrupt")
    return data


def _scratch_file(adir, scratch, name, data):
    path = os.path.join(adir, name)
    scratch.append(path)
    _atomic_write(path, data)
    return path


def _hash_blob(root, adir, scratch, entry, data):
    """Write `data` as a blob, cleaned for `path` (filters, eol)."""
    src = _scratch_file(adir, scratch, "%d.blob" % entry["n"], data)
    proc = _git(root, "hash-object", "-w", "--path=" + entry["path"], "--", src)
    oid = proc.stdout.strip()
    if proc.returncode != 0 or OID_RE.match(oid) is None:
        raise Refused("refused: git could not store the fix")
    return oid


def _working_form(root, adir, scratch, entry, rev):
    """`git cat-file --filters <rev>:<path>` (working-tree form)."""
    # `<rev>:<path>` is an object name, not a pathspec; the path is validated
    # (no leading dash) and the rev is a sha or empty (the index).
    proc = _git(root, "cat-file", "--filters", "%s:%s" % (rev, entry["path"]),
                binary=True)
    if proc.returncode != 0:
        raise Refused("refused: could not read the last commit")
    return proc.stdout


def _merge_rc_is_conflict(rc):
    """merge-file exit: 1..127 counts conflicting hunks."""
    return 0 < rc < 128


def _merge_rc_is_error(rc):
    """merge-file exit -1 (255 here): binary input or another error."""
    return rc < 0 or rc >= 128


def _merge_delta(root, adir, scratch, entry, ours, pre, post):
    """`git merge-file -p <ours> <pre> <post>`: apply ONLY pre->post onto ours
    -> merged bytes. A conflict or a binary file is not separable."""
    n = entry["n"]
    ours_f = _scratch_file(adir, scratch, "%d.ours" % n, ours)
    pre_f = _scratch_file(adir, scratch, "%d.base" % n, pre)
    post_f = _scratch_file(adir, scratch, "%d.theirs" % n, post)
    proc = _git(root, "merge-file", "-p", "--", ours_f, pre_f, post_f,
                binary=True)
    if _merge_rc_is_conflict(proc.returncode):
        raise _not_separable("the fix overlaps uncommitted edits")
    if _merge_rc_is_error(proc.returncode):
        raise _not_separable("binary or unmergeable file")
    return proc.stdout


def _target_mode(entry, base_entry):
    """Commit mode of a tracked path -> mode | None (not separable).

    The fix did not change the mode -> BASE's mode (an owner-committed chmod
    is kept). The fix changed it and BASE still has the snapshot mode -> the
    fix's mode. Both changed it -> None.
    """
    snap = _git_mode(entry.get("mode"))
    post = _git_mode(entry.get("post_mode"))
    if post == snap:
        return base_entry[0]
    if base_entry[0] == snap:
        return post
    return None


def _base_precondition(entry, base_entry, real_entry):
    """Re-validate a path's snapshot-time pre-state against BASE -> the fixed
    not-separable reason, or None when committing the path is safe.

    The snapshot recorded each path against the HEAD of snapshot time; BASE is
    read later, so another terminal may have committed the path in between.

    | path class (manifest)        | required in BASE / real index         | why it is then safe |
    |------------------------------|---------------------------------------|---------------------|
    | created by the fix (absent)  | absent from BASE ("the file now exists | the commit adds a path that exists |
    |                              | in the last commit") and from the     | nowhere in BASE, so no committed |
    |                              | real index ("the file is staged in    | version is replaced by the sealed |
    |                              | your index")                          | post bytes |
    | tracked, edited by the fix   | present in BASE ("the file is no      | merge-file applies only the sealed |
    |                              | longer in the last commit"); mode via | pre->post delta onto BASE's version, |
    |                              | `_target_mode` ("the file mode changed | so committed owner changes are kept |
    |                              | in the last commit")                  | and an overlap is a conflict |
    | tracked, deleted by the fix  | present in BASE; the pre bytes must   | a changed BASE version is never |
    |                              | equal BASE's version (checked when    | deleted |
    |                              | the removal is built)                 | |
    | untracked, symlink/submodule,| always not separable (checked before) | nothing is committed |
    | unmerged index entry         |                                       | |
    | owner-staged path            | the commit is still BASE + the delta; | the locked full-entry compare in |
    |                              | the staged merge only shapes the      | `_sync_real_index` guards the index |
    |                              | real-index target                     | |
    """
    state = entry.get("state")
    if state == "absent":
        if base_entry is not None:
            return "the file now exists in the last commit"
        if real_entry is not None:
            return "the file is staged in your index"
        return None
    if base_entry is None:
        return "the file is no longer in the last commit"
    if (entry.get("post_state") == "present"
            and _target_mode(entry, base_entry) is None):
        return "the file mode changed in the last commit"
    return None


def _path_refusal(entry, base_entry, real_entry):
    """Paths that are never separable, whatever BASE holds -> reason | None."""
    state = entry.get("state")
    if state == "untracked":
        return "file was untracked before the fix"
    if state not in ("tracked", "absent"):
        raise Refused("refused: attempt state is missing or corrupt")
    if base_entry is not None and base_entry[0] not in REGULAR_MODES:
        return "symlink or submodule"
    if real_entry is not None and real_entry[0] not in REGULAR_MODES:
        return "symlink or submodule"
    if real_entry is not None and real_entry[2] != 0:
        return "the file has an unresolved merge conflict"
    return None


def _precompute(root, base, adir, manifest, before, scratch):
    """Every blob the commit needs, built BEFORE any ref or index write, so a
    multi-path fix is all-or-nothing -> (ops, targets).

    ops: [(path, mode | None, oid | None)] for the temporary index (None =
    remove). targets: {path: (mode, oid) | None} for the real-index sync.
    Any path that cannot be separated raises not-separable (exit 3) before
    anything is written: the fix stays applied, uncommitted.
    """
    checked = []
    for entry in manifest["paths"]:
        base_entry = _base_entry(root, base, entry["path"])
        real = before.get(entry["path"])
        reason = _path_refusal(entry, base_entry, real)
        if reason is None:
            reason = _base_precondition(entry, base_entry, real)
        if reason is not None:
            raise _not_separable(reason)
        checked.append((entry, base_entry, real))

    ops = []
    targets = {}
    for entry, base_entry, real in checked:
        path = entry["path"]
        post_present = entry.get("post_state") == "present"
        if entry["state"] == "absent":
            if not post_present:
                continue  # created and removed again: nothing to commit
            post = _post_bytes(root, adir, entry)
            mode = _git_mode(entry.get("post_mode"))
            oid = _hash_blob(root, adir, scratch, entry, post)
            ops.append((path, mode, oid))
            targets[path] = (mode, oid)
            continue
        clean = real is not None and _entry_equal(real, base_entry + (0,))
        pre = _pre_bytes(adir, entry)
        ours = _working_form(root, adir, scratch, entry, base)
        if not post_present:
            if pre != ours:
                raise _not_separable(
                    "the fix deletes a file that differs from the last commit")
            if not clean:
                raise _not_separable("the file is staged in your index")
            ops.append((path, None, None))
            targets[path] = None
            continue
        post = _post_bytes(root, adir, entry)
        merged = _merge_delta(root, adir, scratch, entry, ours, pre, post)
        oid = _hash_blob(root, adir, scratch, entry, merged)
        mode = _target_mode(entry, base_entry)
        ops.append((path, mode, oid))
        if clean:
            targets[path] = (mode, oid)
            continue
        if real is None:
            raise _not_separable("the file is staged in your index")
        # The owner staged a version of this file: the same delta applied onto
        # the STAGED version is what the index should hold after the commit.
        staged = _working_form(root, adir, scratch, entry, "")
        staged_merged = _merge_delta(root, adir, scratch, entry, staged, pre,
                                     post)
        targets[path] = (real[0], _hash_blob(root, adir, scratch, entry,
                                             staged_merged))
    if not ops:
        raise _not_separable("the fix left no change to commit")
    return ops, targets


def _write_tree(root, index_file):
    proc = _git(root, "write-tree", env=_env(index_file))
    tree = proc.stdout.strip()
    if proc.returncode != 0 or OID_RE.match(tree) is None:
        raise Refused("refused: git could not build the commit")
    return tree


def _build_temp_index(root, base, adir, ops, message, scratch):
    """A temporary index = BASE + the fix blobs -> (index, tree, msgfile)."""
    index = os.path.join(adir, "tmp-index")
    scratch.extend([index, index + ".lock"])
    if os.path.lexists(index):
        os.unlink(index)
    env = _env(index)
    args = ["read-tree", base] if base is not None else ["read-tree", "--empty"]
    if _git(root, *args, env=env).returncode != 0:
        raise Refused("refused: git could not build the commit")
    _race_point(root, "after-read-tree")
    for path, mode, oid in ops:
        if mode is None:
            proc = _git(root, "update-index", "--force-remove", "--", path,
                        env=env)
        else:
            proc = _git(root, "update-index", "--add", "--cacheinfo",
                        "%s,%s,%s" % (mode, oid, path), env=env)
        if proc.returncode != 0:
            raise Refused("refused: git could not build the commit")
    tree = _write_tree(root, index)
    msgfile = _scratch_file(adir, scratch, "msg", message.encode("utf-8"))
    return index, tree, msgfile


def _tail(data):
    lines = _decode(data or b"").splitlines()
    return "\n".join(lines[-HOOK_TAIL_LINES:])


def _run_commit_hooks(root, temp_index, msgfile):
    """The owner's hooks, in git commit's order and environment -> (ok, tail).

    GIT_INDEX_FILE is the temporary index (what `git commit` sets for a commit
    built from another index) and GIT_EDITOR is `:`. No hook is ever skipped.
    """
    env = _env(temp_index)
    env["GIT_EDITOR"] = ":"
    for name, extra in (("pre-commit", []),
                        ("prepare-commit-msg", [msgfile, "message"]),
                        ("commit-msg", [msgfile])):
        argv = ["git", "hook", "run", "--ignore-missing", name]
        if extra:
            argv += ["--"] + extra
        try:
            proc = subprocess.run(argv, cwd=root, env=env,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  timeout=HOOK_TIMEOUT)
        except subprocess.TimeoutExpired:
            return False, "the %s hook timed out" % name
        if proc.returncode != 0:
            return False, _tail(proc.stdout)
    return True, ""


def _gpg_sign(root):
    proc = _git(root, "config", "--type=bool", "--get", "commit.gpgSign")
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _make_commit_object(root, tree, base, msgfile):
    """`git commit-tree [-p BASE] [-S] -F msgfile tree` -> sha | None.

    The parent is the captured BASE, never whatever HEAD is by now.
    """
    args = ["commit-tree"]
    if base is not None:
        args += ["-p", base]
    if _gpg_sign(root):
        args.append("-S")
    args += ["-F", msgfile, tree]
    proc = _git(root, *args)
    sha = proc.stdout.strip()
    if proc.returncode != 0 or OID_RE.match(sha) is None:
        return None
    return sha


def _publish_ref(root, base, base_symref, new, subject):
    """Publish `new` by ONE compare-and-swap of the branch from BASE -> bool.

    The old value is mandatory in every form (40/64 zeros when the branch is
    unborn, meaning "must not exist yet"), so git refuses the write unless the
    branch is still exactly BASE: the only possible motion is BASE -> a direct
    child of BASE, the same forward step `git commit` makes. Never a rewind, a
    delete or a forced move. This is the only ref write in this module.
    """
    if _head_state(root) != (base, base_symref):
        return False
    _race_point(root, "in-publish")
    old = base if base is not None else "0" * len(new)
    if base_symref is not None:
        target = [base_symref]
    else:
        target = ["--no-deref", "HEAD"]
    proc = _git(root, "update-ref", "-m", "commit: " + subject, *target,
                new, old)
    return proc.returncode == 0


def _tree_matches(tree, expected_tree):
    return tree == expected_tree


def _commit_tree_of(root, sha):
    proc = _git(root, "rev-parse", "-q", "--verify", sha + "^{tree}")
    return proc.stdout.strip() if proc.returncode == 0 else None


def _index_path(root):
    proc = _git(root, "rev-parse", "--git-path", "index")
    path = proc.stdout.strip()
    if proc.returncode != 0 or not path:
        return None
    return path if os.path.isabs(path) else os.path.join(root, path)


def _split_index_in_use(root, index_path):
    proc = _git(root, "config", "--type=bool", "--get", "core.splitIndex")
    if proc.returncode == 0 and proc.stdout.strip() == "true":
        return True
    parent = os.path.dirname(index_path)
    return any(name.startswith("sharedindex.") for name in os.listdir(parent))


def _acquire_index_lock(index_path):
    """git's own `<index>.lock`, created O_CREAT|O_EXCL -> (fd, lock) | None.

    While it exists every git command that writes the index refuses to run,
    so nothing can change the index between our compare and our publish.
    """
    lock = index_path + ".lock"
    for attempt in range(INDEX_LOCK_RETRIES):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
            return fd, lock
        except FileExistsError:
            if attempt + 1 < INDEX_LOCK_RETRIES:
                time.sleep(INDEX_LOCK_WAIT)
    return None


def _sync_real_index(root, before, targets, workdir):
    """Update the real index for `targets` ({path: (mode, oid) | None}) ->
    the paths left as they are.

    The ONLY real-index write in this module. The whole read-compare-publish
    happens while holding git's own index.lock: copy the index, compare each
    entry of the copy with the entry recorded before the commit started
    (complete mode + oid + stage), edit the copy only where they are equal,
    write the copy into the lock and rename it over the index - exactly how
    git publishes an index. A busy lock or a split index leaves everything as
    it is. Never touches the working tree.
    """
    paths = sorted(targets)
    if not paths:
        return []
    index_path = _index_path(root)
    if index_path is None or _split_index_in_use(root, index_path):
        return paths
    acquired = _acquire_index_lock(index_path)
    if acquired is None:
        return paths
    fd, lock = acquired
    copy = os.path.join(workdir, "index.copy")
    published = False
    left = []
    try:
        for leftover in (copy, copy + ".lock"):
            if os.path.lexists(leftover):
                os.unlink(leftover)
        if os.path.exists(index_path):
            shutil.copyfile(index_path, copy)
        now = _read_index_entries(root, copy, paths)
        env = _env(copy)
        for path in paths:
            if not _entry_equal(now.get(path), before.get(path)):
                left.append(path)
                continue
            target = targets[path]
            if target is None:
                proc = _git(root, "update-index", "--force-remove", "--", path,
                            env=env)
            else:
                proc = _git(root, "update-index", "--add", "--cacheinfo",
                            "%s,%s,%s" % (target[0], target[1], path), env=env)
            if proc.returncode != 0:
                left.append(path)
        _between_compare_and_publish(root)
        if not os.path.exists(copy):
            return paths  # nothing was written to an index that did not exist
        with open(copy, "rb") as fh:
            data = fh.read()
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(lock, index_path)
        published = True
    finally:
        if fd is not None:
            os.close(fd)
        if not published and os.path.lexists(lock):
            os.unlink(lock)  # only ever the lock this function created
        for leftover in (copy, copy + ".lock"):
            if os.path.lexists(leftover):
                os.unlink(leftover)
    return left


def _run_post_commit(root):
    """post-commit, rc ignored exactly as `git commit` ignores it."""
    try:
        subprocess.run(["git", "hook", "run", "--ignore-missing",
                        "post-commit"], cwd=root, env=_env(),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=HOOK_TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.stderr.write("commit: the post-commit hook timed out\n")


def _commit(root, record, adir, scratch):
    """One isolated commit -> _Outcome (raised or returned)."""
    manifest = _load_manifest(adir)
    if not manifest["sealed"]:
        raise Refused("refused: attempt not sealed")
    try:
        message = fixcommit.build_message(record.get("pass_number"),
                                          record.get("title"))
    except ValueError as exc:
        raise Refused(str(exc))
    _validate_paths(root, record["paths"])  # the D-15 second gate
    known = {entry["path"] for entry in manifest["paths"]}
    if not manifest["paths"] or any(p not in known for p in record["paths"]):
        raise _not_separable("a path was edited without a pre-edit snapshot")
    _validate_paths(root, sorted(known))
    if _git_version(root) < MIN_GIT_FOR_HOOKS:
        raise Refused("refused: git 2.36 or newer is needed to run your "
                      "commit hooks")
    subject = message.splitlines()[0]

    base, base_symref = _capture_base(root)
    _race_point(root, "after-base")
    before = _read_index_entries(root, None, None)
    ops, targets = _precompute(root, base, adir, manifest, before, scratch)
    temp_index, expected_tree, msgfile = _build_temp_index(
        root, base, adir, ops, message, scratch)

    ok, tail = _run_commit_hooks(root, temp_index, msgfile)
    new = None
    if ok:
        _race_point(root, "after-hooks")
        tree = _write_tree(root, temp_index)
        new = _make_commit_object(root, tree, base, msgfile)
    if new is None:
        if not ok:
            reason = "your commit hook rejected the commit"
        elif _gpg_sign(root):
            reason = "the commit could not be signed"
        else:
            reason = "git could not create the commit"
        raise _Outcome(4, "hook-rejected",
                       ["commit-not-created: " + reason]
                       + (tail.splitlines() if tail else []))
    if not _publish_ref(root, base, base_symref, new, subject):
        raise Refused("refused: the branch moved")
    _run_post_commit(root)

    left = _sync_real_index(root, before, targets, adir)
    return _Outcome(0, "committed",
                    ["commit_sha=%s" % new]
                    + ["index-left-as-is: %s" % p for p in left])


def _remove_scratch(scratch):
    for path in scratch:
        try:
            if os.path.lexists(path):
                os.unlink(path)
        except OSError as exc:
            sys.stderr.write("commit: %s removing a temporary file\n"
                             % type(exc).__name__)


def cmd_commit(root, record, attempt):
    fid = record["id"]
    adir = _require_open_attempt(root, fid, attempt)
    scratch = []
    try:
        try:
            result = _commit(root, record, adir, scratch)
        except _Outcome as raised:
            result = raised
        finally:
            _remove_scratch(scratch)
    except (Refused, OSError, subprocess.SubprocessError):
        # Every outcome past the stale-attempt gate closes the attempt.
        _close_attempt(root, fid, attempt, "refused")
        raise
    for line in result.lines:
        sys.stdout.write(line + "\n")
    _close_attempt(root, fid, attempt, result.outcome)
    return result.code


def run(argv):
    parsed, err = parse_argv(argv)
    if err is not None:
        sys.stderr.write(USAGE)
        sys.stderr.write(err)
        return 2
    sub, values = parsed
    root = values["--root"]
    try:
        _check_toplevel(root)
        root = os.path.realpath(root)
        record = _load_record(root, values["--finding-json"])
        if sub == "begin":
            return cmd_begin(root, record)
        handler = {"snapshot": cmd_snapshot, "seal": cmd_seal,
                   "undo": cmd_undo, "commit": cmd_commit}[sub]
        return handler(root, record, values["--attempt"])
    except Refused as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    except (OSError, subprocess.SubprocessError) as exc:
        # Fixed reason plus the error class only; no paths or file contents.
        sys.stderr.write("refused: %s during %s (fail closed)\n"
                         % (type(exc).__name__, sub))
        return 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
