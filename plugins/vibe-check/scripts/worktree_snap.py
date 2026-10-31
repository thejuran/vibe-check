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

- `take`, in Phase 0 BEFORE the reviewed diff is collected (the PR head is
  bound in the same call), snapshots what the reviewers are about to read
  into a private per-pass directory under the system temp dir and prints
  `REVIEWED_SNAPSHOT=<nonce>`. The 32-hex nonce is the only handle: the
  directory is derived from it, never from a path the caller passes, so a
  pass consumes only its own snapshot (overlapping passes, a halted pass's
  leftover). Nothing is written under `.turingmind/` (Phase 0.7's first-run
  check keys on it) or `.git` at this point.
- `collect`, at Phase 3, consumes that snapshot (its objects move into the
  store) and prints exactly two lines:

    REVIEWED_TREE=<object id>      what this pass reviewed, or empty
    NEARBY_LINE_RANGES=<json>      lines changed since what the last pass
                                   reviewed, or empty when that is unknown

  Both are the snapshot's, and only while the code is still the same at
  collect time. If the working tree, range end or PR head moved after the
  snapshot, or there is none, BOTH are empty: recording the newer state would
  tell the next pass "nothing changed" about code the reviewers never read,
  and ranges against the newer state are not in the line numbers the
  reviewers' findings use. Empty values make this pass and the next one stamp
  from changed_line_ranges, which can only re-ask.

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
(`<current>` is the matched tree id on the default and GSD routes, never the
live working tree), the same line
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

    python3 worktree_snap.py take --root <repo top>
        [--range <range> | --pr-head <sha>]
    python3 worktree_snap.py collect --root <repo top> [--state <state file>]
        --before <nonce> [--range <range> | --pr-head <sha>]
"""

import json
import os
import re
import secrets
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
USAGE = ("usage: worktree_snap.py take --root <repo top> "
         "[--range <range> | --pr-head <sha>]\n"
         "       worktree_snap.py collect --root <repo top> [--state <state file>] "
         "--before <nonce> [--range <range> | --pr-head <sha>]\n")


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


def _store_env(root, write_to=None):
    """Environment that reads the repo's objects (and the vibe-check store)
    and writes new objects only to `write_to` (default: the vibe-check store,
    created on demand)."""
    store = os.path.join(root, STORE_REL, "objects")
    alternates = [os.path.abspath(_git_path(root, "objects"))]
    if write_to is None:
        os.makedirs(store, exist_ok=True)
        write_to = store
    elif os.path.isdir(store):
        alternates.append(store)
    env = dict(os.environ)
    for k in ("GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
              "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(k, None)
    env["GIT_OBJECT_DIRECTORY"] = write_to
    env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.pathsep.join(alternates)
    return env


def take(root, write_to=None):
    """The tree id of the tracked working tree. New objects go to the
    vibe-check store, or to `write_to` (a pass's private directory, so the
    Phase 0 call never creates `.turingmind/`)."""
    env = _store_env(root, write_to)
    work = tempfile.mkdtemp(prefix="idx-", dir=os.path.dirname(env["GIT_OBJECT_DIRECTORY"]))
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
    """Exact changed-line ranges of `current` (a tree or commit id; None =
    the live working tree, which `collect` never uses) against `prior`. An unchanged id is `{}` with no git call,
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


SNAP_PREFIX = "vc-worktree-snap-"
NONCE_RE = re.compile(r"^[0-9a-f]{32}$")


def _snap_dir(nonce):
    """A pass's private directory, derived from its nonce (never a path the
    caller supplies, so `collect` can only consume and delete its own)."""
    if not isinstance(nonce, str) or not NONCE_RE.match(nonce):
        return None
    return os.path.join(tempfile.gettempdir(), SNAP_PREFIX + nonce)


def take_before(root, rng=None, pr_head=None):
    """Phase 0 half, run BEFORE the reviewed diff is collected: record what
    this pass is about to review in a private per-pass directory under the
    system temp dir -> (nonce or "", notes). The nonce names that directory;
    the prose carries it to `collect --before`, so overlapping passes and a
    halted pass's leftover can never be consumed by another pass. On the
    default and GSD routes the tree's new objects are written to the same
    private directory (nothing under `.turingmind/` or `.git` yet), and
    `collect` moves them into the store."""
    notes = []
    nonce = secrets.token_hex(16)
    path = _snap_dir(nonce)
    try:
        os.mkdir(path, 0o700)
        objects = os.path.join(path, "objects")
        os.mkdir(objects)
        if rng is not None:
            current = range_end(root, rng)
        elif pr_head is not None:
            if not OBJECT_ID_RE.match(pr_head):
                raise SnapUnavailable("PR head is not a commit id")
            current = pr_head
        else:
            current = take(root, write_to=objects)
        with open(os.path.join(path, "before.json"), "w", encoding="utf-8") as fh:
            json.dump({"route": _route(rng, pr_head), "id": current}, fh)
    except (SnapUnavailable, OSError) as exc:
        shutil.rmtree(path, ignore_errors=True)
        notes.append("reviewed tree not taken: %s" % exc)
        return "", notes
    return nonce, notes


def _import_objects(root, src):
    """Move a pass's loose objects into the vibe-check store."""
    dst = os.path.join(root, STORE_REL, "objects")
    for d, _, files in os.walk(src):
        rel = os.path.relpath(d, src)
        for f in files:
            target = os.path.join(dst, rel, f)
            if os.path.exists(target):
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            # Copy to a temporary name in the same directory, then rename:
            # an interrupted copy never leaves a truncated object under its
            # final name in the shared store.
            tmp = "%s.tmp-%d-%s" % (target, os.getpid(), secrets.token_hex(4))
            try:
                shutil.copyfile(os.path.join(d, f), tmp)
                os.replace(tmp, target)
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)


def _consume_before(root, nonce, route):
    """This pass's pre-dispatch id for `route`, consuming its directory (its
    objects move into the store first). None when absent, unreadable, or for
    another route."""
    path = _snap_dir(nonce)
    if path is None or not os.path.isdir(path):
        return None
    try:
        with open(os.path.join(path, "before.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        if (not isinstance(data, dict) or data.get("route") != route
                or not isinstance(data.get("id"), str)
                or not OBJECT_ID_RE.match(data["id"])):
            return None
        _import_objects(root, os.path.join(path, "objects"))
        return data["id"]
    except (OSError, ValueError):
        return None
    finally:
        shutil.rmtree(path, ignore_errors=True)


def collect(root, state_path, rng=None, pr_head=None, nonce=None):
    """Phase 3 half -> (reviewed id or "", nearby ranges JSON or "", notes).

    The reviewed id is the one `take` recorded before the reviewed diff was
    collected, and only while what is there now is still the same: the same
    working tree, range end or PR head. If it moved during the pass (an edit,
    a commit, a push), or this pass's snapshot is missing, BOTH values are
    empty. Recording the newer id would let the next pass see "nothing
    changed" for code the reviewers never read, and ranges computed against
    the newer state are not in the line numbers the reviewers' findings use;
    with both empty, this pass and the next stamp from changed_line_ranges,
    which can only re-ask. Otherwise the nearby ranges compare the PRIOR
    pass's id with what is there now (the same state the reviewers read)."""
    notes = []
    route = _route(rng, pr_head)
    before = _consume_before(root, nonce, route)
    try:
        current = _current(root, rng, pr_head)
    except (SnapUnavailable, OSError) as exc:
        current = None
        notes.append("current tree unknown: %s" % exc)
    if before is None:
        notes.append("nothing recorded: no snapshot taken for this pass")
        return "", "", notes
    if before != current:
        notes.append("nothing recorded: the code changed during this pass")
        return "", "", notes
    try:
        nearby = json.dumps(
            # Tree to tree, on every route: `current` is the id just matched
            # against the snapshot. Diffing the live working tree instead
            # would read whatever lands on disk after that match.
            since(root, prior_tree(state_path), current),
            separators=(",", ":"), sort_keys=True)
    except (SnapUnavailable, OSError) as exc:
        nearby = ""
        notes.append("nearby ranges unavailable: %s" % exc)
    return before, nearby, notes


def run(argv):
    if not argv or argv[0] not in ("take", "collect"):
        sys.stderr.write(USAGE)
        return 2
    cmd = argv[0]
    opts = {}
    rest = argv[1:]
    known = ("--root", "--state", "--range", "--pr-head", "--before")
    while rest:
        if rest[0] in known and len(rest) >= 2:
            opts[rest[0]] = rest[1]
            rest = rest[2:]
        else:
            sys.stderr.write(USAGE)
            return 2
    root = opts.get("--root")
    if (not root or not os.path.isdir(root)
            or ("--range" in opts and "--pr-head" in opts)):
        sys.stderr.write(USAGE)
        return 2
    root = os.path.abspath(root)
    if cmd == "take":
        nonce, notes = take_before(root, opts.get("--range"), opts.get("--pr-head"))
        for note in notes:
            sys.stderr.write(note + "\n")
        sys.stdout.write("REVIEWED_SNAPSHOT=%s\n" % nonce)
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
