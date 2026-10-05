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
    commit   (built separately; exit 2 until then)

Refusals print a fixed reason on stderr that names the failing rule. Callers
branch on the EXIT CODE.

I/O: stdlib only, imports exactly {hashlib, json, os, re, shutil, subprocess,
sys, tempfile} plus the sibling `fixcommit` (path validation is single-sourced
there; fixcommit itself stays subprocess-free). Every subprocess call is an argv
list with `timeout=120`, never a shell string, and every git call puts `--`
before path arguments. Undo never moves HEAD and never touches the index.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

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

def _git(root, *args, binary=False):
    """git in `root` (argv list, no shell); returns the CompletedProcess."""
    return subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=not binary,
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


def cmd_undo(root, record, attempt):
    adir = _require_open_attempt(root, record["id"], attempt)
    manifest = _load_manifest(adir)
    if not manifest["sealed"]:
        raise Refused("refused: attempt not sealed")
    sys.stderr.write("undo: not implemented\n")
    return 2


def run(argv):
    parsed, err = parse_argv(argv)
    if err is not None:
        sys.stderr.write(USAGE)
        sys.stderr.write(err)
        return 2
    sub, values = parsed
    if sub == "commit":
        sys.stderr.write("commit: not implemented\n")
        return 2
    root = values["--root"]
    try:
        _check_toplevel(root)
        root = os.path.realpath(root)
        record = _load_record(root, values["--finding-json"])
        if sub == "begin":
            return cmd_begin(root, record)
        handler = {"snapshot": cmd_snapshot, "seal": cmd_seal,
                   "undo": cmd_undo}[sub]
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
