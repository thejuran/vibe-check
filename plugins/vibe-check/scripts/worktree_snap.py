"""worktree_snap.py — what changed since the last pass reviewed the working tree.

Why (999.28, Phase 61 live smoke C1): on the default and GSD routes, pass >= 2
builds `changed_line_ranges` from `git diff <last head_sha>`. Before anything
is committed that sha is still HEAD, so the whole uncommitted block is in the
ranges on every pass, and score.py stamped every owner decision inside it as
"code next to it changed since your decision" although nothing had changed.
`changed_line_ranges` must stay as it is (it drives the +20 in-diff term and
the persisted re-check trigger); the decision stamp needs a second input: the
lines that changed since the working tree the last pass reviewed.

`collect` does both halves in one call and prints exactly two lines:

    REVIEWED_TREE=<object id>      what this pass reviews, or empty
    NEARBY_LINE_RANGES=<json>      lines changed since what the last pass
                                   reviewed, or empty when that is unknown

What "reviewed" means depends on the route (the PR and range routes had the
same defect on committed code: their range source is the same fixed diff on
every pass):

- default and GSD (no route flag): the working tree, recorded as a tree id;
- range (`--range <range>`): the commit the range ends at (`a..b` -> b; an
  empty end is HEAD, as for `git diff`), recorded as its commit id;
- PR (`--pr-head <sha>`): the PR's head commit, recorded as its commit id. The
  head commit need not exist locally: an unchanged head gives `{}` by id alone,
  and a changed head is diffed only when both commits are present locally.

In every case the ranges are new-side lines of ONE `git diff <prior> <current>`
(`<current>` is the working tree on the default and GSD routes), the same line
space as that route's `changed_line_ranges`. A prior recorded by another route
on the same branch state (they share the state file) is diffed the same way.

- The reviewed tree is the tree of every tracked file as it is on disk (staged
  and unstaged edits; untracked files are out of scope, as they are for
  `git diff HEAD`). It is built with a temporary index and written to a
  vibe-check-owned object store, `.turingmind/worktree-snap/objects`, whose
  alternate is the repo's own object store. Nothing is written to `.git`: no
  object, no ref, no index, and the real index file is only read.
- The prior tree id is the last pass's `reviewed_tree` in the state file. It
  is passed to git only when it is a 40- or 64-hex id that names a tree in the
  store. The ranges come from ONE `git diff <prior tree>` (working tree vs that
  tree, the prose's flags) through `diff_ranges.ranges_from_diff`, so they are
  exact and in working-tree line numbers like `changed_line_ranges`.
- Every failure is advisory and prints the key with an empty value: a state
  written before this key (2.14.0 and older), a pass that could not record its
  tree, a missing or unreadable tree, or any git error. score.py then falls
  back to `changed_line_ranges` for the stamp, which is the old behavior and
  fails toward asking. Exit 0 in all those cases; exit 2 only on bad usage.

CLI:

    python3 worktree_snap.py collect --root <repo top> [--state <state file>]
        [--range <range> | --pr-head <sha>]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import diff_ranges

STORE_REL = os.path.join(".turingmind", "worktree-snap")
OBJECT_ID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
# The flags every range-building git call in the review prose passes
# (30-collect-score.md), so a repo-local setting cannot change the text read.
DIFF_FLAGS = ("--no-color", "--no-ext-diff", "--no-textconv", "--no-relative",
              "--src-prefix=a/", "--dst-prefix=b/")
GIT_TIMEOUT = 120
USAGE = ("usage: worktree_snap.py collect --root <repo top> "
         "[--state <state file>] [--range <range> | --pr-head <sha>]\n")


class SnapUnavailable(Exception):
    """This half cannot be produced; print the key with an empty value."""


def _git(root, args, env=None, stdin=None):
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *args],
            cwd=root, env=env, input=stdin, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SnapUnavailable("git %s could not run (%s)"
                              % (args[0], type(exc).__name__))
    if proc.returncode != 0:
        raise SnapUnavailable("git %s failed (exit %d)"
                              % (args[0], proc.returncode))
    return proc.stdout.decode("utf-8", "replace")


def _git_path(root, name):
    out = _git(root, ["rev-parse", "--git-path", name]).strip()
    if not out:
        raise SnapUnavailable("git rev-parse --git-path gave nothing")
    return os.path.join(root, out)


def _store_env(root):
    """Environment that reads the repo's objects and writes only to the
    vibe-check store."""
    store = os.path.join(root, STORE_REL, "objects")
    os.makedirs(store, exist_ok=True)
    env = dict(os.environ)
    for k in ("GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
              "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(k, None)
    env["GIT_OBJECT_DIRECTORY"] = store
    env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.path.abspath(
        _git_path(root, "objects"))
    return env


def take(root):
    """The tree id of the tracked working tree, written to the store only."""
    env = _store_env(root)
    work = tempfile.mkdtemp(prefix="idx-", dir=os.path.join(root, STORE_REL))
    try:
        idx = os.path.join(work, "index")
        real = _git_path(root, "index")
        env["GIT_INDEX_FILE"] = idx
        if os.path.isfile(real):
            shutil.copyfile(real, idx)
        else:
            _git(root, ["read-tree", "HEAD"], env=env)
        _git(root, ["add", "-u", "--", "."], env=env)
        tree = _git(root, ["write-tree"], env=env).strip()
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if not OBJECT_ID_RE.match(tree):
        raise SnapUnavailable("write-tree did not print a tree id")
    return tree


def prior_tree(state_path):
    """The last pass's `reviewed_tree` when it is a well-formed object id."""
    if not state_path:
        raise SnapUnavailable("no state file")
    try:
        with open(state_path, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError) as exc:
        raise SnapUnavailable("state unreadable (%s)" % type(exc).__name__)
    passes = state.get("passes") if isinstance(state, dict) else None
    if not isinstance(passes, list) or not passes or not isinstance(passes[-1], dict):
        raise SnapUnavailable("state has no last pass")
    value = passes[-1].get("reviewed_tree")
    if not isinstance(value, str) or not OBJECT_ID_RE.match(value):
        raise SnapUnavailable("last pass has no reviewed_tree")
    return value


def range_end(root, rng):
    """The commit id the range `rng` ends at (`a..b` / `a...b` -> b; an
    empty end is HEAD). The end is resolved with --end-of-options, and an end
    that starts with `-` is refused, so it can never be read as an option."""
    if not isinstance(rng, str) or ".." not in rng:
        raise SnapUnavailable("not a range")
    end = rng.rsplit("..", 1)[1].lstrip(".") or "HEAD"
    if end.startswith("-"):
        raise SnapUnavailable("range end looks like an option")
    out = _git(root, ["rev-parse", "--verify", "--quiet", "--end-of-options",
                      end + "^{commit}"]).strip()
    if not OBJECT_ID_RE.match(out):
        raise SnapUnavailable("range end is not a commit")
    return out


def _treeish(root, env, oid):
    if not OBJECT_ID_RE.match(oid or ""):
        raise SnapUnavailable("not an object id")
    if _git(root, ["cat-file", "-t", oid], env=env).strip() not in ("tree", "commit"):
        raise SnapUnavailable("not a tree or commit")


def since(root, prior, current=None):
    """Exact changed-line ranges of `current` (a commit id; None = the
    working tree) against `prior`. An unchanged id is `{}` with no git call,
    so an unchanged PR head needs no local objects."""
    if not OBJECT_ID_RE.match(prior or ""):
        raise SnapUnavailable("not an object id")
    if current is not None and current == prior:
        return {}
    env = _store_env(root)
    _treeish(root, env, prior)
    ends = [prior]
    if current is not None:
        _treeish(root, env, current)
        ends.append(current)
    text = _git(root, ["diff", *DIFF_FLAGS, *ends, "--"], env=env)
    try:
        return diff_ranges.ranges_from_diff(text)
    except diff_ranges.RangeError as exc:
        raise SnapUnavailable(str(exc))


def _current(root, rng=None, pr_head=None):
    """The id this pass reviews: the working tree's tree (default/GSD), the
    range's end commit, or the PR head commit."""
    if rng is not None:
        return range_end(root, rng)
    if pr_head is not None:
        if not OBJECT_ID_RE.match(pr_head):
            raise SnapUnavailable("PR head is not a commit id")
        return pr_head
    return take(root)


def collect(root, state_path, rng=None, pr_head=None):
    """(reviewed id or "", nearby ranges JSON or "", notes)."""
    notes = []
    try:
        current = _current(root, rng, pr_head)
    except (SnapUnavailable, OSError) as exc:
        current = None
        notes.append("reviewed tree not recorded: %s" % exc)
    worktree = rng is None and pr_head is None
    try:
        if current is None and not worktree:
            raise SnapUnavailable("this pass's reviewed id is unknown")
        nearby = json.dumps(
            since(root, prior_tree(state_path), None if worktree else current),
            separators=(",", ":"), sort_keys=True)
    except (SnapUnavailable, OSError) as exc:
        nearby = ""
        notes.append("nearby ranges unavailable: %s" % exc)
    return current or "", nearby, notes


def run(argv):
    if not argv or argv[0] != "collect":
        sys.stderr.write(USAGE)
        return 2
    opts = {}
    rest = argv[1:]
    while rest:
        if rest[0] in ("--root", "--state", "--range", "--pr-head") and len(rest) >= 2:
            opts[rest[0]] = rest[1]
            rest = rest[2:]
        else:
            sys.stderr.write(USAGE)
            return 2
    root = opts.get("--root")
    if not root or not os.path.isdir(root):
        sys.stderr.write(USAGE)
        return 2
    state_path = opts.get("--state")
    if state_path and not os.path.isfile(state_path):
        state_path = None  # pass 1: no state file yet
    if "--range" in opts and "--pr-head" in opts:
        sys.stderr.write(USAGE)
        return 2
    tree, nearby, notes = collect(os.path.abspath(root), state_path,
                                  opts.get("--range"), opts.get("--pr-head"))
    for note in notes:
        sys.stderr.write(note + "\n")
    sys.stdout.write("REVIEWED_TREE=%s\nNEARBY_LINE_RANGES=%s\n" % (tree, nearby))
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
