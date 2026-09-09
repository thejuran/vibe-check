"""coverage.py — the `--all` coverage note's R/T/S arithmetic as an executable
identity.

Phase 40 (DIET-02, second tier, D-07). This is a BEHAVIOR-PRESERVING extraction
of the three bucket definitions the prose states at `commands/review.md:923-925`
and re-derives by hand at each render site.

THE ONE RULE (review.md:925):

    {{S}} (SKIPPED) = {{T}} - {{R}} — EXACTLY, so R + S = T ALWAYS holds.

`S` is DERIVED SUBTRACTION, never a count of attributed skip reasons. The two
readings diverge whenever attribution is incomplete, and incomplete attribution
is the NORMAL case: `review.md:925` says to name the buckets only "where the
skip reasons are known". Counting instead of subtracting would shrink `S`
silently, understating how much of the codebase went unreviewed — in a report
whose entire purpose is an honest audit denominator (`review.md:930`, the
coverage-overstatement anti-pattern). So attribution completeness is reported as
its OWN number, `unattributed`, and never allowed to move `S`.

The transcribed definitions:

  T (review.md:924)  the `$REVIEW_SET` (regular-files-only) size — the candidate
                     set Phase 0 selected BEFORE per-chunk triage.
  R (review.md:923)  the size of the union of the per-chunk
                     `$CHUNK_REVIEW_FILES_i` sets actually dispatched — the
                     count of files a reviewer agent actually received.
  S (review.md:925)  T - R. ONE bucket absorbing BOTH skip remainders: the
                     triage-skip remainder and the capped-skip remainder.

Symlinks sit OUTSIDE this arithmetic (review.md:926, P10-C). They were dropped
at selection before `$REVIEW_SET` was built, so they are outside `T`; folding
them into `S` would make R + S = T + symlinks > T (the internally inconsistent
"Reviewed 40 of 42, 5 skipped" bug). `non_regular_skipped` therefore rides
through untouched and is asserted never to move `S`.

WHAT THIS MODULE DOES NOT DO (D-08 keep-list). This module computes; the prose
renders — do not extract the layout. No function here returns a rendered string,
a table row, a percentage, or a template token; a test asserts it.

Fail-closed posture. A non-int count, a negative count, `R > T`, or attribution
exceeding `S` sets `identity_ok = False` with a numeric `identity_error`, and
`S` is clamped at zero so a negative skipped count can never reach a report. A
coverage note that cannot be shown to add up must be visibly broken rather than
plausibly wrong.

I/O: stdlib only, imports exactly {json, sys}. CLI:

    echo '{"total":12,"reviewed":9,"skip_reasons":{...}}' | python3 coverage.py

JSON stdin -> JSON stdout. Unparseable stdin propagates so the process exits
NON-ZERO: a helper that cannot read its own input must not print an answer.
"""

import json
import sys

# The skip-reason buckets the prose names explicitly at review.md:925 — the
# "capped-skip remainder" and the "triage-skip remainder". They are the KNOWN
# slugs; an unrecognized slug is still counted and additionally FLAGGED (a
# silently dropped skip reason is invisible under-review), never dropped.
BUCKETS = ("capped", "triage-skipped")

_ERR_BAD_TOTAL = "total is not a non-negative int"
_ERR_BAD_REVIEWED = "reviewed is not a non-negative int"
_ERR_BAD_REASONS = "skip_reasons is not a mapping of slug to non-negative int"
_ERR_BAD_NON_REGULAR = "non_regular_skipped is not a non-negative int"
_ERR_REVIEWED_GT_TOTAL = "reviewed %d exceeds total %d"
_ERR_OVER_ATTRIBUTED = "attributed skips %d exceed S %d"


def _is_count(value):
    """A count is a plain non-negative int.

    `bool` is rejected on purpose: `True` is an int in Python, so a bash site
    that emitted `true` instead of a number would otherwise silently count as
    1 and produce a coverage note that is off by one with no diagnostic.
    """
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _refused(reason, non_regular=0):
    return {
        "T": 0,
        "R": 0,
        "S": 0,
        "skip_reasons": {},
        "attributed": 0,
        "unattributed": 0,
        "unknown_reasons": [],
        "non_regular_skipped": non_regular if _is_count(non_regular) else 0,
        "identity_ok": False,
        "identity_error": reason,
    }


def compute(total, reviewed, skip_reasons, non_regular_skipped=0):
    """The R/T/S buckets, with the review.md:925 identity asserted.

    Returns a dict; never a rendered string (D-08). `S` is always `T - R`
    clamped at zero, and `identity_ok` is False whenever that subtraction, the
    inputs, or the attribution cannot be shown to be consistent.
    """
    if not _is_count(total):
        return _refused(_ERR_BAD_TOTAL, non_regular_skipped)
    if not _is_count(reviewed):
        return _refused(_ERR_BAD_REVIEWED, non_regular_skipped)
    if not _is_count(non_regular_skipped):
        return _refused(_ERR_BAD_NON_REGULAR)
    if not isinstance(skip_reasons, dict):
        return _refused(_ERR_BAD_REASONS, non_regular_skipped)
    for slug, count in skip_reasons.items():
        if not isinstance(slug, str) or not _is_count(count):
            return _refused(_ERR_BAD_REASONS, non_regular_skipped)

    identity_ok = True
    identity_error = None

    # review.md:925 — S = T - R, EXACTLY. Clamped so a bad input can never put
    # a negative skipped count into a report.
    if reviewed > total:
        identity_ok = False
        identity_error = _ERR_REVIEWED_GT_TOTAL % (reviewed, total)
        skipped = 0
    else:
        skipped = total - reviewed

    attributed = sum(skip_reasons.values())
    # Incomplete attribution is EXPECTED (review.md:925 attributes S to buckets
    # only "where the skip reasons are known"), so it is a diagnostic, not a
    # failure. Attribution EXCEEDING S is a real inconsistency: some file is
    # counted as skipped that was reviewed, or counted twice.
    if attributed > skipped and identity_ok:
        identity_ok = False
        identity_error = _ERR_OVER_ATTRIBUTED % (attributed, skipped)
        unattributed = 0
    else:
        unattributed = max(skipped - attributed, 0)

    return {
        "T": total,
        "R": reviewed,
        "S": skipped,
        "skip_reasons": {k: skip_reasons[k] for k in sorted(skip_reasons)},
        "attributed": attributed,
        "unattributed": unattributed,
        "unknown_reasons": sorted(k for k in skip_reasons if k not in BUCKETS),
        # review.md:926 (P10-C) — carried alongside, OUTSIDE the arithmetic.
        "non_regular_skipped": non_regular_skipped,
        "identity_ok": identity_ok,
        "identity_error": identity_error,
    }


def run(envelope):
    """{"total": T, "reviewed": R, "skip_reasons": {...}} -> the buckets."""
    if not isinstance(envelope, dict):
        return _refused(_ERR_BAD_REASONS)
    return compute(
        envelope.get("total"),
        envelope.get("reviewed"),
        envelope.get("skip_reasons", {}),
        envelope.get("non_regular_skipped", 0),
    )


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO.
    json.dump(run(json.load(sys.stdin)), sys.stdout, allow_nan=False)
