"""finalize_gate.py — the Finalize-mode preconditions as an executable decision.

Phase 40 (DIET-02, second tier, D-07). A BEHAVIOR-PRESERVING extraction of the
branch structure in `commands/review.md` Finalize mode (`:29-48`).

THE BRANCH ORDER, transcribed in the prose's own sequence:

  review.md:31  no state file
                -> error: "No prior review passes. Run `/review` first."
  review.md:35  `outstanding_cw` non-empty (band ∈ {critical, warning} AND
                status ≠ fixed-since-last, per :33)
                -> :38 enter the finalize card (90-finalize.md "### The
                   finalize card") with the outstanding critical/warning rows
                   listed first; rows the owner marks fix route into the
                   fix-loop card. ":38 — Do NOT write REVIEW.md or
                   archive state — finalize stays blocked until a future
                   invocation finds `outstanding_cw` empty."
  review.md:39    ...unless Phase 5 is unavailable ("$TURINGMIND_NONINTERACTIVE
                  is set, or PR/range mode") -> fall back to the legacy
                  behavior: "Fix these, re-run with `--finalize`." and stop.
  review.md:40  `unacknowledged_medium` non-empty (band == medium AND no entry
                in `medium_acknowledgments`, per :34)
                -> enter the same finalize card. Its exits — any row marked
                   fix routes to the fix-loop card and finalize does NOT
                   proceed this invocation; everything decided proceeds —
                   depend on ANSWERS THE USER HAS NOT GIVEN YET, so they are
                   outside a pure precondition gate. Entering the card is the
                   decision this module owns.
  review.md:48  otherwise -> write `.turingmind/REVIEW.md`.

WHY THE VOCABULARY IS SIX AND NOT THREE. Fix-list FL-07 (finding R11) caught a
draft limited to `write` / `fallback` / `refuse`, which cannot represent either
interactive route. The distinction is real, not cosmetic: `fallback` (:39) is
the NON-interactive path and tells the user to re-run later, whereas
`outstanding-to-phase-5` (:38) keeps going in the SAME invocation with a fix
loop. Collapsing them would misclassify live behavior in the direction that
matters — a run that should have offered fixes would instead stop.

Neither added outcome is a sub-state of an existing one: `outstanding-to-phase-5`
and `medium-ack-loop` differ from each other in candidate set (Critical/Warning
vs Medium) and from `fallback` in interactivity. The action names
`outstanding-to-phase-5` and `medium-ack-loop` are historical — both now enter
the ONE finalize card; they stay distinct because their candidate sets differ
and renaming them would break every caller.

PHASE-5 AVAILABILITY GATES THE FIX ROUTES, NOT FINALIZATION. `:39` scopes the
fallback to the outstanding-findings branch, and the card's fix choice defers
to Phase 5, so the medium branch is interactive by construction too. But a CLEAN
state has nothing to fix, so a non-interactive, PR or range run with no
outstanding findings reaches `:48` and writes — the fallback never fires.

WHAT THIS MODULE DOES NOT DO (D-08 keep-list). It returns a DECISION — an action
and a fixed reason — never REVIEW.md content, never the "{{N}} Critical/Warning
findings remain" line, never the finding list at `:37`. This module decides; the
prose renders. A test asserts it.

FAIL CLOSED. Counts arrive as ints and switches as bools; `1`, `"true"` and
`"false"` are all truthy in Python, so a bash site that emitted a string instead
of a bool would silently decide `write` on a blocked review. Unknown, missing,
or wrongly-typed input returns `refuse`.

Reasons are drawn from the module-level REASONS tuple and never carry a count or
a finding title — findings are produced by agents reading the reviewed diff, so
their text is attacker-influenced, and a count belongs to the render.

I/O: stdlib only, imports exactly {json, sys}. CLI:

    echo '{"flags": {...}}' | python3 finalize_gate.py

JSON stdin -> JSON stdout. Unparseable stdin propagates so the process exits
NON-ZERO.
"""

import json
import sys

# The outcomes, in the prose's evaluation order (:31, :35/:38, :40, :39, :48),
# plus the fail-closed refusal. Never invent a seventh.
ACTIONS = (
    "write",
    "outstanding-to-phase-5",
    "medium-ack-loop",
    "fallback",
    "error",
    "refuse",
)

REASON_NO_STATE = "no prior review passes"
REASON_OUTSTANDING_CW = "outstanding critical/warning findings route to the fix loop"
REASON_PHASE5_UNAVAILABLE = "fix loop unavailable; user must re-run with --finalize"
REASON_UNACKNOWLEDGED_MEDIUM = "medium findings await acknowledgement"
REASON_CLEAN = "no outstanding findings; finalization may proceed"
REASON_MALFORMED = "malformed gate input"

REASONS = (
    REASON_NO_STATE,
    REASON_OUTSTANDING_CW,
    REASON_PHASE5_UNAVAILABLE,
    REASON_UNACKNOWLEDGED_MEDIUM,
    REASON_CLEAN,
    REASON_MALFORMED,
)

# The exact flag set, transcribed. `state_file_present` is :31; the two counts
# are the :33/:34 computations; the three switches are :39's three named
# conditions for "Phase 5 is unavailable".
_BOOL_FLAGS = ("state_file_present", "noninteractive", "pr_mode", "range_mode")
_COUNT_FLAGS = ("outstanding_cw", "unacknowledged_medium")
FLAGS = _BOOL_FLAGS + _COUNT_FLAGS


def _decision(action, reason):
    return {"action": action, "reason": reason}


def _is_bool(value):
    return isinstance(value, bool)


def _is_count(value):
    """A count is a plain non-negative int; `bool` is an int in Python and is
    rejected so `True` can never be read as "one finding"."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def decide(flags):
    """The finalize preconditions. Returns `{"action", "reason"}`.

    Branch order is transcribed from review.md:31 -> :35 -> :39 -> :40 -> :48.
    Returns a DECISION, never REVIEW.md content (D-08).
    """
    if not isinstance(flags, dict):
        return _decision(ACTIONS[5], REASON_MALFORMED)
    # An unknown key means the caller and this gate disagree about the contract;
    # deciding anyway would be deciding on an input we do not understand.
    if set(flags) != set(FLAGS):
        return _decision(ACTIONS[5], REASON_MALFORMED)
    for name in _BOOL_FLAGS:
        if not _is_bool(flags[name]):
            return _decision(ACTIONS[5], REASON_MALFORMED)
    for name in _COUNT_FLAGS:
        if not _is_count(flags[name]):
            return _decision(ACTIONS[5], REASON_MALFORMED)

    # :31 — no state file at all. Evaluated before any finding is inspected.
    if not flags["state_file_present"]:
        return _decision(ACTIONS[4], REASON_NO_STATE)

    # :39 — the three conditions under which Phase 5 is unavailable.
    phase5_available = not (flags["noninteractive"]
                            or flags["pr_mode"]
                            or flags["range_mode"])

    # :35 — outstanding Critical/Warning is evaluated BEFORE :40's Medium branch.
    # Swapping these would adjudicate Mediums while Criticals sit unfixed, and
    # could reach :48 and write REVIEW.md for a review :38 says stays blocked.
    if flags["outstanding_cw"] > 0:
        if not phase5_available:
            return _decision(ACTIONS[3], REASON_PHASE5_UNAVAILABLE)
        return _decision(ACTIONS[1], REASON_OUTSTANDING_CW)

    # The medium branch. The finalize card's fix choice defers to Phase 5, so the
    # branch needs the same interactivity the fallback at :39 tests for.
    if flags["unacknowledged_medium"] > 0:
        if not phase5_available:
            return _decision(ACTIONS[3], REASON_PHASE5_UNAVAILABLE)
        return _decision(ACTIONS[2], REASON_UNACKNOWLEDGED_MEDIUM)

    # :48 — write .turingmind/REVIEW.md.
    return _decision(ACTIONS[0], REASON_CLEAN)


def run(envelope):
    """{"flags": {...}} -> the decision. Fails closed."""
    if not isinstance(envelope, dict):
        return _decision(ACTIONS[5], REASON_MALFORMED)
    return decide(envelope.get("flags"))


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO.
    json.dump(run(json.load(sys.stdin)), sys.stdout, allow_nan=False)
