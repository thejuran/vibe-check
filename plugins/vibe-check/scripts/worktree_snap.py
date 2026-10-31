"""worktree_snap.py — what changed since the last pass reviewed the working tree.

Why (999.28, Phase 61 live smoke C1): on the default and GSD routes, pass >= 2
builds `changed_line_ranges` from `git diff <last head_sha>`. Before anything
is committed that sha is still HEAD, so the whole uncommitted block is in the
ranges on every pass, and score.py stamped every owner decision inside it as
"code next to it changed since your decision" although nothing had changed.
`changed_line_ranges` must stay as it is (it drives the +20 in-diff term and
the persisted re-check trigger); the decision stamp needs a second input: the
lines that changed since the working tree the last pass reviewed.

Two calls per pass:

- `take`, BEFORE any reviewer runs (Phase 1 next to the git-safety snapshot;
  on the PR route in Phase 0, before the reviewed diff is fetched), writes
  what this pass is about to review to `--out` (`{"route", "id"}`) and prints
  `REVIEWED_TREE_BEFORE=<id>` (informational).
- `collect`, at Phase 3, consumes that file and prints exactly two lines:

    REVIEWED_TREE=<object id>      what this pass reviewed, or empty
    NEARBY_LINE_RANGES=<json>      lines changed since what the last pass
                                   reviewed, or empty when that is unknown

  REVIEWED_TREE is the pre-dispatch id, and only while the code is still the
  same at collect time. If the working tree, range end or PR head moved
  during the pass, it is empty: recording the newer state would tell the next
  pass "nothing changed" about code the reviewers never read (fail-open). An
  empty value makes the next pass stamp from changed_line_ranges (re-asks).

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
  alternate is the repo's own object store. vibe-check writes nothing to
  `.git`: no object, ref or index (the temporary index lives in the store and
  is never split, `core.splitIndex=false`), and the real index file is only
  read. One exception is outside its control: `git add` runs the repo's
  configured clean filters, as `git diff` against the working tree already
  does. Filters cannot be switched off as a whole (only per driver, and
  turning them off would make filtered files always differ), so a clean
  filter such as Git LFS may store content in its own area (`.git/lfs/`)
  exactly as it would for an ordinary `git add`.
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

    python3 worktree_snap.py take --root <repo top> --out <file>
        [--range <range> | --pr-head <sha>]
    python3 worktree_snap.py collect --root <repo top> [--state <state file>]
        --before <file> [--range <range> | --pr-head <sha>]
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
# The temporary index is a plain, self-contained file: never split, so no
# sharedindex.* file is written into (or expired out of) the git dir.
TEMP_INDEX_CFG = ("-c", "core.splitIndex=false")
USAGE = ("usage: worktree_snap.py take --root <repo top> --out <file> "
         "[--range <range> | --pr-head <sha>]\n"
         "       worktree_snap.py collect --root <repo top> [--state <state file>] "
         "--before <file> [--range <range> | --pr-head <sha>]\n")


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
            _git(root, [*TEMP_INDEX_CFG, "read-tree", "HEAD"], env=env)
        _git(root, [*TEMP_INDEX_CFG, "add", "-u", "--", "."], env=env)
        tree = _git(root, [*TEMP_INDEX_CFG, "write-tree"], env=env).strip()
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


def _route(rng, pr_head):
    if rng is not None:
        return "range"
    if pr_head is not None:
        return "pr"
    return "worktree"


def take_before(root, out_path, rng=None, pr_head=None):
    """Pre-dispatch half: record what this pass is about to review in
    `out_path` as {"route", "id"} -> (id or "", notes). Any stale file is
    removed first, so a failure leaves no file and the pass records nothing."""
    notes = []
    try:
        os.remove(out_path)
    except FileNotFoundError:
        pass
    try:
        current = _current(root, rng, pr_head)
    except (SnapUnavailable, OSError) as exc:
        notes.append("reviewed tree not taken: %s" % exc)
        return "", notes
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"route": _route(rng, pr_head), "id": current}, fh)
    os.replace(tmp, out_path)
    return current, notes


def _read_before(path, route):
    """The pre-dispatch id for `route`, consuming the file (a later pass can
    never reuse it). None when absent, unreadable, or for another route."""
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if (not isinstance(data, dict) or data.get("route") != route
            or not isinstance(data.get("id"), str)
            or not OBJECT_ID_RE.match(data["id"])):
        return None
    return data["id"]


def collect(root, state_path, rng=None, pr_head=None, before_path=None):
    """Collect-time half -> (reviewed id or "", nearby ranges JSON or "",
    notes).

    The reviewed id is the one `take` recorded BEFORE the reviewers ran, and
    only while what is there now is still the same: the same working tree,
    range end or PR head. If it moved during the pass (an edit, a commit, a
    push), the reviewers may have read the older code, so nothing is recorded:
    the next pass then has no prior id and stamps from changed_line_ranges,
    which can only re-ask. Recording the newer id instead would let the next
    pass see "nothing changed" for code the reviewers never saw (fail-open).
    The nearby ranges compare the PRIOR pass's id with what is there now."""
    notes = []
    route = _route(rng, pr_head)
    try:
        current = _current(root, rng, pr_head)
    except (SnapUnavailable, OSError) as exc:
        current = None
        notes.append("current tree unknown: %s" % exc)
    before = _read_before(before_path, route)
    if before is None:
        reviewed = ""
        notes.append("reviewed tree not recorded: no pre-dispatch snapshot")
    elif before != current:
        reviewed = ""
        notes.append("reviewed tree not recorded: the code changed during "
                     "this pass")
    else:
        reviewed = before
    try:
        if current is None:
            raise SnapUnavailable("this pass's tree is unknown")
        nearby = json.dumps(
            since(root, prior_tree(state_path),
                  None if route == "worktree" else current),
            separators=(",", ":"), sort_keys=True)
    except (SnapUnavailable, OSError) as exc:
        nearby = ""
        notes.append("nearby ranges unavailable: %s" % exc)
    return reviewed, nearby, notes


def run(argv):
    if not argv or argv[0] not in ("take", "collect"):
        sys.stderr.write(USAGE)
        return 2
    cmd = argv[0]
    opts = {}
    rest = argv[1:]
    known = ("--root", "--state", "--range", "--pr-head", "--before", "--out")
    while rest:
        if rest[0] in known and len(rest) >= 2:
            opts[rest[0]] = rest[1]
            rest = rest[2:]
        else:
            sys.stderr.write(USAGE)
            return 2
    root = opts.get("--root")
    if (not root or not os.path.isdir(root)
            or ("--range" in opts and "--pr-head" in opts)
            or (cmd == "take" and not opts.get("--out"))):
        sys.stderr.write(USAGE)
        return 2
    root = os.path.abspath(root)
    if cmd == "take":
        tree, notes = take_before(root, opts["--out"], opts.get("--range"),
                                  opts.get("--pr-head"))
        for note in notes:
            sys.stderr.write(note + "\n")
        sys.stdout.write("REVIEWED_TREE_BEFORE=%s\n" % tree)
        return 0
    state_path = opts.get("--state")
    if state_path and not os.path.isfile(state_path):
        state_path = None  # pass 1: no state file yet
    tree, nearby, notes = collect(root, state_path, opts.get("--range"),
                                  opts.get("--pr-head"), opts.get("--before"))
    for note in notes:
        sys.stderr.write(note + "\n")
    sys.stdout.write("REVIEWED_TREE=%s\nNEARBY_LINE_RANGES=%s\n" % (tree, nearby))
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
