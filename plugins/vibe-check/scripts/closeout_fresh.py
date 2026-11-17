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
prefixes; `diff_ranges` strips only `b/`.

WHAT IT NEVER DOES. It prints nothing and writes nothing (no state file, no
index refresh, no store directory). It never puts a finding path on a git
argv: the whole tree is diffed and paths are looked up in the parsed map; a
path failing `fixcommit.PATH_RE` is stale with cause `unverifiable`. It never
imports `score` (the window constant is mirrored here and pinned by a lock
test). With no decision-closed record it runs no git command at all.

I/O: stdlib imports exactly {os, subprocess, sys}, plus siblings
`carry_state` (read-only: open_findings, decision_state, _fix_closes),
`diff_ranges` (ranges_from_diff, RangeError), `worktree_snap`
(OBJECT_ID_RE, STORE_REL, _git_path), `fixcommit` (PATH_RE constant only).
Every `subprocess.run` is an argv list with `timeout=GIT_TIMEOUT` and no
shell; git's stderr is captured and discarded, never returned or printed.
"""

import os
import subprocess  # noqa: F401  (the git layer's runner)
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import carry_state  # noqa: E402,F401  (which records are decision-closed, read-only)
import diff_ranges  # noqa: E402,F401  (diff text -> change ranges)
import worktree_snap  # noqa: E402,F401  (object-id rule, store location, git paths)
from fixcommit import PATH_RE  # noqa: E402,F401  (path pre-filter constant only)

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


class Unverifiable(Exception):
    """The comparison cannot be made (git, parse or shape failure); the caller
    maps it to cause `unverifiable`."""


def stale_decisions(state, blobs, cwd=None):
    """Sorted list of {"hash": str, "kind": "deferred"|"dismissed", "cause": one of CAUSES}
    for every open last-pass record closed by a CURRENT owner decision whose reviewed
    code is not provably unchanged on disk. [] when no record is decision-closed, and in
    that case NO git command runs. Never raises."""
    return []  # contract only: no freshness check yet, every decision is kept
