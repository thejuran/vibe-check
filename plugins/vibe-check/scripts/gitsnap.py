"""gitsnap.py — read-only before/after fingerprint of a reviewed repo's git state.

A review must never change the repo it reviews. A hook blocks mutating git
commands from the review agents, but a hook only sees tool calls it is wired
to: a separate process (Codex), a stale hook path, a hook that failed open, or
the owner working in another terminal all go around it. This script is the
independent check: `take` records the git state before the review fans out,
`compare` reports exactly what changed after it.

Why the stash list is part of the snapshot: in an earlier incident a stash was
popped during a review and then "restored" by re-stashing the same content. The
stash count and the working-tree diff were identical afterwards, so a
count-or-diff check would have called it clean — but the re-stash is a NEW
stash commit, and only the list of stash commit hashes shows it.

Components recorded (each a separate `collect_*` function so tests can prove
every one is load-bearing):

- head            `rev-parse -q --verify HEAD`, null when unborn
- symref          `symbolic-ref -q HEAD` (a branch switch at the same commit)
- index_sha256    sha256 of `ls-files -s -z` — mode, blob id, stage and path of
                  every staged entry
- stash           `stash list --format=%H`, newest first
- refs            `for-each-ref` objectname/refname, minus refs/stash (the
                  stash component owns it), plus a sha256 of the listing
- head_reflog_count  `rev-list --walk-reflogs --count HEAD` (a checkout-and-back
                  round trip leaves HEAD unchanged but grows the reflog)
- in_progress     which of MERGE_HEAD, REBASE_HEAD, CHERRY_PICK_HEAD,
                  REVERT_HEAD, rebase-merge, rebase-apply exist

The raw index file in the git dir is never hashed: a plain `git status` refreshes
stat data and rewrites that file, which would raise a false alarm on every
review. Every git call also runs with `--no-optional-locks`, so taking the
snapshot never rewrites the index itself. Untracked and unstaged working-tree
files are deliberately out of scope — the review writes its own scratch under
`.turingmind/`, and unstaged edits are the owner's.

Exit codes (callers branch on the code, never on stdout):

    python3 gitsnap.py take --root <repo> --out <file>
        0 written | 2 cannot take (not a repo, git error, unwritable) — HALT
    python3 gitsnap.py compare --root <repo> --before <file>
        0 same (prints nothing) | 1 changed (one plain line per changed
        component) | 2 cannot confirm (missing/garbled before file, git
        error) — callers treat 2 as changed (fail closed)

I/O: stdlib only, imports exactly {argparse, hashlib, json, os, subprocess,
sys}; every `subprocess.run` is an argv list with `timeout=60`, never a shell.
Refusal reasons are fixed strings plus the git subcommand name; they never echo
repo content.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

IN_PROGRESS_MARKERS = ("MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD",
                       "REVERT_HEAD", "rebase-merge", "rebase-apply")

SNAPSHOT_KEYS = {
    "head": (str, type(None)),
    "symref": (str, type(None)),
    "index_sha256": (str,),
    "stash": (list,),
    "refs_sha256": (str,),
    "refs": (dict,),
    "head_reflog_count": (int,),
    "in_progress": (list,),
}


class SnapError(Exception):
    """The snapshot cannot be taken or compared — exit 2 (fail closed)."""


# ---------------------------------------------------------------------------
# git runner
# ---------------------------------------------------------------------------

def _git(root, *args):
    """Run read-only git in `root`. stdout and stderr are captured separately
    because stdout is hashed. Returns the CompletedProcess (bytes)."""
    try:
        return subprocess.run(
            ["git", "--no-optional-locks", *args], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SnapError("git %s could not run (%s)" % (args[0], type(exc).__name__))


def _git_ok(root, *args):
    proc = _git(root, *args)
    if proc.returncode != 0:
        raise SnapError("git %s failed (exit %d)" % (args[0], proc.returncode))
    return proc.stdout


def _text(raw):
    return raw.decode("utf-8", "replace").strip()


def check_repo(root):
    if not os.path.isdir(root):
        raise SnapError("root is not a directory")
    proc = _git(root, "rev-parse", "--git-dir")
    if proc.returncode != 0:
        raise SnapError("root is not inside a git repository")


# ---------------------------------------------------------------------------
# component collectors
# ---------------------------------------------------------------------------

def collect_head(root):
    """HEAD commit sha, or None when the branch is unborn."""
    proc = _git(root, "rev-parse", "-q", "--verify", "HEAD")
    if proc.returncode != 0:
        return None
    return _text(proc.stdout)


def collect_symref(root):
    """The branch HEAD points at, or None when detached."""
    proc = _git(root, "symbolic-ref", "-q", "HEAD")
    if proc.returncode == 1:
        return None
    if proc.returncode != 0:
        raise SnapError("git symbolic-ref failed (exit %d)" % proc.returncode)
    return _text(proc.stdout)


def collect_index_sha256(root):
    """sha256 over the staged entries (not the index file's bytes)."""
    return hashlib.sha256(_git_ok(root, "ls-files", "-s", "-z")).hexdigest()


def collect_stash(root):
    """Stash commit hashes, newest first."""
    out = _text(_git_ok(root, "stash", "list", "--format=%H"))
    return [line for line in out.splitlines() if line]


def collect_refs(root):
    """{refname: sha} for every ref except refs/stash."""
    out = _text(_git_ok(root, "for-each-ref",
                        "--format=%(objectname) %(refname)"))
    refs = {}
    for line in out.splitlines():
        sha, _, name = line.partition(" ")
        if name and name != "refs/stash":
            refs[name] = sha
    return refs


def collect_head_reflog_count(root):
    """Entries in HEAD's reflog; 0 when unborn or no reflog is kept."""
    proc = _git(root, "rev-list", "--walk-reflogs", "--count", "HEAD")
    if proc.returncode == 0:
        try:
            return int(_text(proc.stdout))
        except ValueError:
            raise SnapError("git rev-list returned a non-number")
    if collect_head(root) is None:
        return 0
    log_path = _text(_git_ok(root, "rev-parse", "--git-path", "logs/HEAD"))
    if not os.path.exists(os.path.join(root, log_path)):
        return 0
    raise SnapError("git rev-list failed (exit %d)" % proc.returncode)


def collect_in_progress(root):
    """Names of merge/rebase/cherry-pick/revert markers that exist."""
    found = []
    for marker in IN_PROGRESS_MARKERS:
        rel = _text(_git_ok(root, "rev-parse", "--git-path", marker))
        if os.path.exists(os.path.join(root, rel)):
            found.append(marker)
    return found


def _refs_sha256(refs):
    listing = "".join("%s %s\n" % (refs[name], name) for name in sorted(refs))
    return hashlib.sha256(listing.encode("utf-8")).hexdigest()


def take_snapshot(root):
    """Fingerprint `root`'s git state as a JSON-serialisable dict."""
    check_repo(root)
    refs = collect_refs(root)
    return {
        "head": collect_head(root),
        "symref": collect_symref(root),
        "index_sha256": collect_index_sha256(root),
        "stash": collect_stash(root),
        "refs_sha256": _refs_sha256(refs),
        "refs": refs,
        "head_reflog_count": collect_head_reflog_count(root),
        "in_progress": collect_in_progress(root),
    }


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------

def _short(sha):
    return sha[:7] if sha else "(none)"


def _branch(symref):
    if symref is None:
        return "(detached)"
    prefix = "refs/heads/"
    return symref[len(prefix):] if symref.startswith(prefix) else symref


def diff_snapshots(before, after):
    """Plain human lines, one per changed component; [] when nothing changed."""
    lines = []
    if before["head"] != after["head"]:
        lines.append("HEAD moved %s → %s" % (_short(before["head"]),
                                             _short(after["head"])))
    if before["symref"] != after["symref"]:
        lines.append("branch switched %s → %s" % (_branch(before["symref"]),
                                                  _branch(after["symref"])))
    if before["stash"] != after["stash"]:
        n_before, n_after = len(before["stash"]), len(after["stash"])
        detail = "%d → %d entries" % (n_before, n_after)
        if n_before == n_after:
            detail += "; contents differ"
        lines.append("stash list changed (%s)" % detail)
    if before["index_sha256"] != after["index_sha256"]:
        lines.append("staged files changed")
    if before["refs"] != after["refs"]:
        changes = []
        for name in sorted(set(before["refs"]) | set(after["refs"])):
            if name not in after["refs"]:
                changes.append("%s deleted" % name)
            elif name not in before["refs"]:
                changes.append("%s created" % name)
            elif before["refs"][name] != after["refs"][name]:
                changes.append("%s moved" % name)
        lines.append("branches/tags changed: %s" % ", ".join(changes))
    grew = after["head_reflog_count"] - before["head_reflog_count"]
    if grew > 0:
        lines.append("HEAD reflog grew by %d entr%s (a checkout or reset happened)"
                     % (grew, "y" if grew == 1 else "ies"))
    elif grew < 0:
        lines.append("HEAD reflog shrank by %d entr%s (the reflog was expired "
                     "or rewritten)" % (-grew, "y" if grew == -1 else "ies"))
    started = sorted(set(after["in_progress"]) - set(before["in_progress"]))
    ended = sorted(set(before["in_progress"]) - set(after["in_progress"]))
    if started:
        lines.append("a merge/rebase is now in progress (%s)" % ", ".join(started))
    if ended:
        lines.append("a merge/rebase that was in progress has ended (%s)"
                     % ", ".join(ended))
    return lines


def load_snapshot(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise SnapError("before snapshot is missing or unreadable")
    if not isinstance(data, dict):
        raise SnapError("before snapshot has the wrong shape")
    for key, types in SNAPSHOT_KEYS.items():
        if key not in data or not isinstance(data[key], types) \
                or isinstance(data[key], bool):
            raise SnapError("before snapshot has the wrong shape (%s)" % key)
    return data


def write_snapshot(path, snap):
    parent = os.path.dirname(os.path.abspath(path))
    tmp = path + ".tmp"
    try:
        os.makedirs(parent, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(snap, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except OSError:
        raise SnapError("cannot write the snapshot file")
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run(argv):
    parser = argparse.ArgumentParser(
        prog="gitsnap.py", description="Git state fingerprint (see docstring).")
    sub = parser.add_subparsers(dest="cmd")
    p_take = sub.add_parser("take")
    p_take.add_argument("--root", required=True)
    p_take.add_argument("--out", required=True)
    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("--root", required=True)
    p_cmp.add_argument("--before", required=True)

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2  # usage error -> fail closed, never exit 0
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2

    try:
        if args.cmd == "take":
            write_snapshot(args.out, take_snapshot(args.root))
            return 0
        before = load_snapshot(args.before)
        lines = diff_snapshots(before, take_snapshot(args.root))
        for line in lines:
            sys.stdout.write(line + "\n")
        return 1 if lines else 0
    except SnapError as exc:
        sys.stderr.write("gitsnap: cannot confirm git state: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
