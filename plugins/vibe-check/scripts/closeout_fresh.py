"""closeout_fresh.py — which owner decisions went stale before Close out.

WHAT IT DECIDES. A deferred or dismissed finding stays closed at Close out
only while the code the owner decided on is still the code on disk. This
module answers, for every open last-pass record that a CURRENT owner decision
closes (and that no fresh fix-obsolete verdict closes first), whether the
reviewed code is provably unchanged. The baseline is the last pass's
`reviewed_tree` (D-04): the tree (default/GSD route) or commit (PR/range
route) the reviewers actually read. The comparison end is the live working
tree, so uncommitted edits count. Any record whose code is not provably
unchanged is reported stale; one stale record refuses the whole Close out
(the caller decides that, not this module).

CAUSES. Each stale record carries exactly one cause token (D-01):

    line          the decided line itself changed since the review
    nearby        code within +/- _NEARBY_LINES of the decided line changed
                  (D-05; the same window the review's re-ask uses)
    deleted       the decided file was deleted or renamed since the review
                  (D-06)
    untracked     the decided file is absent from the reviewed tree, so
                  there is no saved copy to compare against (D-09)
    unverifiable  the comparison could not be made: missing or malformed
                  `reviewed_tree`, the vibe-check store missing, a git
                  failure or timeout, or a malformed record

ANY BYTE CHANGE COUNTS (D-07). Whitespace-only and binary changes are
changes: the diff runs with `--text` and no whitespace-ignoring flag.

HOW IT COMPARES. One reverse diff of the reviewed tree against the working
tree (`git diff -R --no-renames --text <reviewed_tree> --`), run at the
repository top, so the change ranges come out in the reviewed tree's line
numbering and a stored `line` is checked with no relocation. With `-R` the
`+++` header carries the source prefix, so REV_FLAGS swaps the usual
prefixes; `diff_ranges` strips only `b/`. A file deleted or renamed since the
review comes out of that diff as a whole-file range, so its decided line is
hit; `--no-renames` keeps a rename from pairing the old name with the new one
and hiding that range.

WHICH LINES. A record is judged at its own line and, inside the window, at
the line of every open same-hash copy and every member its row covers (no
obligation of its own): the same spot set the review stamps from
(`score._nearby_spots`), so a refusal here is one the next review re-asks.

CAUSE ORDER, per record: a decision value other than defer/dismiss, a `file`
failing `fixcommit.PATH_RE` or a `line` that is not a positive int ->
`unverifiable`; the file absent from the reviewed tree -> `untracked`; the
own line hit -> `line`, else any spot's window hit -> `nearby`; then, when
the file is gone from disk, a hit becomes `deleted` and no hit becomes
`unverifiable` (the diff and the disk disagree, so nothing is proven).

WHAT IT NEVER DOES. It prints nothing and writes nothing (no state file, no
index refresh, no store directory). It never puts a finding path on a git
argv: the whole tree is diffed and paths are looked up in the parsed map; a
path failing `fixcommit.PATH_RE` is stale with cause `unverifiable`. It never
imports `score` (the window constant is mirrored here and pinned by a lock
test). With no decision-closed record it runs no git command at all.

I/O: stdlib imports exactly {os, subprocess, sys}, plus siblings
`carry_state` (read-only: open_findings, decision_state, covering_decision,
_fix_closes), `diff_ranges` (ranges_from_diff, RangeError), `worktree_snap`
(OBJECT_ID_RE, STORE_REL), `fixcommit` (PATH_RE constant only).
Every `subprocess.run` is an argv list with `timeout=GIT_TIMEOUT` and no
shell; git's stderr is captured and discarded, never returned or printed.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import carry_state  # noqa: E402  (which records are decision-closed, read-only)
import diff_ranges  # noqa: E402  (diff text -> change ranges)
import worktree_snap  # noqa: E402  (object-id rule, store location)
from fixcommit import PATH_RE  # noqa: E402  (path pre-filter constant only)

GIT_TIMEOUT = 60

# Mirror of score._NEARBY_LINES (D-05); this module never loads the scorer,
# so a lock test in test_closeout_fresh.py pins the two values together.
_NEARBY_LINES = 5

# The `next` value a stale-decision refusal reports.
NEXT_REVIEW_AGAIN = "stop-review-again"

CAUSES = ("line", "nearby", "deleted", "untracked", "unverifiable")

# Prefixes swapped on purpose: the diff runs with `-R`, which puts the source
# prefix on the `+++` header, and diff_ranges strips only `b/` there. The
# usual `a/`/`b/` order would key every range under `a/<path>`, match no
# record, and silently keep every decision.
REV_FLAGS = ("--no-color", "--no-ext-diff", "--no-textconv", "--no-relative",
             "--src-prefix=b/", "--dst-prefix=a/")

# The decision values a record can be closed by, and the word the refusal
# reports for each. Any other value is kept as "dismissed" with cause
# `unverifiable` (the writer never produces one).
_KIND = {"defer": "deferred", "dismiss": "dismissed"}


class Unverifiable(Exception):
    """The comparison cannot be made (git, parse or shape failure); the caller
    maps it to cause `unverifiable`."""


# --------------------------------------------------------------------------- #
# Pure layer: which records, which lines, which cause.
# --------------------------------------------------------------------------- #
def _line_ok(line):
    return isinstance(line, int) and not isinstance(line, bool) and line >= 1


def _path_ok(path):
    return isinstance(path, str) and PATH_RE.match(path) is not None


def _spots(record, last):
    """[(file, line)] of the other spots whose change re-asks `record`'s
    decision in the review: every open record of the same hash (rows and
    member sidecars) and every covered member (no obligation of its own) of
    an open row of that hash. Spots without a usable file or line, and the
    record's own spot, are skipped; de-duplicated in order."""
    h = record.get("stable_hash")
    own = (record.get("file"), record.get("line"))
    found = []
    for row in last.get("findings") or []:
        if not isinstance(row, dict):
            continue
        if row.get("status") not in carry_state.OPEN_STATUSES:
            continue
        members = row.get("members")
        members = members if isinstance(members, list) else []
        if row.get("stable_hash") == h:
            found.append((row.get("file"), row.get("line")))
            found.extend((m.get("file"), m.get("line")) for m in members
                         if isinstance(m, dict) and "obligation" not in m)
        for m in members:
            obl = m.get("obligation") if isinstance(m, dict) else None
            if isinstance(obl, dict) and obl.get("stable_hash") == h:
                found.append((m.get("file"), m.get("line")))
    out = []
    for spot in found:
        if (isinstance(spot[0], str) and _line_ok(spot[1]) and spot != own
                and spot not in out):
            out.append(spot)
    return out


def decided_records(state, blobs):
    """[(record, decision, spots)] for every open last-pass record that a
    CURRENT owner decision closes (its own `decisions` entry, else the
    covering decision) and no fresh fix-obsolete verdict on `blobs` closes
    first. Legacy medium acknowledgments carry no decision and are not
    included. [] for a malformed state. Pure."""
    records = carry_state.open_findings(state)
    if not records:
        return []
    last = state["passes"][-1]
    decisions = state.get("decisions")
    decisions = decisions if isinstance(decisions, dict) else {}
    out = []
    for rec in records:
        if carry_state.decision_state(rec, state) != "current":
            continue
        h = rec["stable_hash"]
        if h in decisions:
            decision = decisions[h]
        else:
            covering = carry_state.covering_decision(rec, state)
            if covering is None:
                continue
            decision = covering[1]
        if carry_state._fix_closes(rec, state, last, blobs):
            continue
        out.append((rec, decision, _spots(rec, last)))
    return out


def _in_ranges(line, ranges):
    return any(isinstance(r, (list, tuple)) and len(r) == 2
               and r[0] <= line <= r[1] for r in ranges)


def _window_hit(file, line, ranges):
    """The review's window (score._nearby_changed): the line and the
    _NEARBY_LINES lines above and below it, clipped at line 1."""
    rs = ranges.get(file, [])
    window = range(max(1, line - _NEARBY_LINES), line + _NEARBY_LINES + 1)
    return any(_in_ranges(n, rs) for n in window)


def _kind(decision):
    value = decision.get("decision") if isinstance(decision, dict) else None
    return _KIND.get(value, "dismissed"), value in _KIND


def _cause(record, decision, spots, ranges, reviewed_paths, on_disk):
    """The cause token for one decided record, or None when its reviewed
    code is provably unchanged (CAUSE ORDER in the module docstring)."""
    file, line = record.get("file"), record.get("line")
    if not _kind(decision)[1] or not _path_ok(file) or not _line_ok(line):
        return "unverifiable"
    if file not in reviewed_paths:
        return "untracked"
    hit = None
    if _in_ranges(line, ranges.get(file, [])):
        hit = "line"
    elif any(_window_hit(f, n, ranges) for f, n in [(file, line)] + spots):
        hit = "nearby"
    if not on_disk(file):
        return "deleted" if hit else "unverifiable"
    return hit


def _sort_key(record):
    file, line = record.get("file"), record.get("line")
    return (file if isinstance(file, str) else "",
            line if _line_ok(line) else 0,
            record.get("stable_hash") or "")


def _row(record, decision, cause):
    return {"hash": record["stable_hash"], "kind": _kind(decision)[0],
            "cause": cause}


def stale_from_ranges(candidates, ranges, reviewed_paths, on_disk):
    """Sorted stale rows for `candidates` ([(record, decision, spots)]) given
    the reverse-diff `ranges` ({file: [[start, end], ...]} in reviewed-tree
    numbering), the set of paths in the reviewed tree and `on_disk(file)`
    (is the file present in the working tree). Pure."""
    out = []
    for rec, decision, spots in sorted(candidates, key=lambda c: _sort_key(c[0])):
        cause = _cause(rec, decision, spots, ranges, reviewed_paths, on_disk)
        if cause is not None:
            out.append(_row(rec, decision, cause))
    return out


def _all_unverifiable(candidates):
    return [_row(rec, decision, "unverifiable") for rec, decision, _
            in sorted(candidates, key=lambda c: _sort_key(c[0]))]


# --------------------------------------------------------------------------- #
# Git layer: read-only, at the repository top.
# --------------------------------------------------------------------------- #
def _git(root, args, env=None):
    """`git <args>` in `root` -> stdout text; Unverifiable on any failure.
    `--no-optional-locks` and `core.fsmonitor=false` keep git from refreshing
    the index or starting a monitor: Close out writes nothing."""
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *args],
            cwd=root, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unverifiable("git %s could not run (%s)"
                           % (args[0], type(exc).__name__))
    if proc.returncode != 0:
        raise Unverifiable("git %s failed (exit %d)"
                           % (args[0], proc.returncode))
    return proc.stdout.decode("utf-8", "replace")


def _toplevel(cwd):
    """The repo top as `git rev-parse --show-toplevel` prints it (only the
    trailing line break dropped); Unverifiable when git gives nothing."""
    top = _git(cwd, ["rev-parse", "--show-toplevel"]).rstrip("\n")
    if not top:
        raise Unverifiable("no repository top")
    return top


def _store_env_ro(root):
    """Environment that reads the repo's own objects plus, when it exists,
    the vibe-check store (where a reviewed tree of uncommitted code lives).
    Never creates the store: a missing store leaves a store-only tree
    unreadable, which fails closed."""
    env = dict(os.environ)
    for k in ("GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
              "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(k, None)
    store = os.path.join(root, worktree_snap.STORE_REL, "objects")
    if os.path.isdir(store):
        env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = store
    return env


def _reviewed_id(state):
    """The last pass's `reviewed_tree` when it is a well-formed object id."""
    value = state["passes"][-1].get("reviewed_tree")
    if not isinstance(value, str) or not worktree_snap.OBJECT_ID_RE.match(value):
        raise Unverifiable("last pass has no reviewed_tree")
    return value


def _treeish(root, env, oid):
    if not worktree_snap.OBJECT_ID_RE.match(oid or ""):
        raise Unverifiable("not an object id")
    if _git(root, ["cat-file", "-t", oid], env=env).strip() not in ("tree", "commit"):
        raise Unverifiable("not a tree or commit")


def changed_ranges(root, reviewed_id):
    """{file: [[start, end], ...]} of what differs between the reviewed tree
    (or commit) and the working tree, in the reviewed tree's numbering."""
    env = _store_env_ro(root)
    _treeish(root, env, reviewed_id)
    text = _git(root, ["diff", "-R", "--no-renames", "--text", *REV_FLAGS,
                       reviewed_id, "--"], env=env)
    try:
        return diff_ranges.ranges_from_diff(text)
    except diff_ranges.RangeError as exc:
        raise Unverifiable(str(exc))


def reviewed_files(root, reviewed_id):
    """The set of repo-relative paths in the reviewed tree (or commit)."""
    out = _git(root, ["ls-tree", "-r", "-z", "--name-only", reviewed_id],
               env=_store_env_ro(root))
    return {p for p in out.split("\0") if p}


def _stale(state, candidates, cwd):
    try:
        reviewed_id = _reviewed_id(state)
        top = _toplevel(cwd)
        ranges = changed_ranges(top, reviewed_id)
        paths = reviewed_files(top, reviewed_id)
    except Unverifiable:
        return _all_unverifiable(candidates)
    return stale_from_ranges(
        candidates, ranges, paths,
        lambda f: os.path.isfile(os.path.join(top, f)))


def stale_decisions(state, blobs, cwd=None):
    """Sorted list of {"hash": str, "kind": "deferred"|"dismissed", "cause": one of CAUSES}
    for every open last-pass record closed by a CURRENT owner decision whose reviewed
    code is not provably unchanged on disk. [] when no record is decision-closed, and in
    that case NO git command runs. Never raises: any failure after the candidates are
    known reports every candidate with cause `unverifiable` (fail closed)."""
    try:
        candidates = decided_records(state, blobs)
    except Exception:  # a state carry_state cannot read closes nothing here
        return []
    if not candidates:
        return []
    try:
        return _stale(state, candidates, cwd)
    except Exception:  # never raise; nothing proven unchanged -> refuse
        return _all_unverifiable(candidates)
