---
phase: 59-stale-decisions-and-lost-deferrals
plan: 03
subsystem: vibe-check scorer + carry-forward state (decision continuity, read side)
tags: [DEFR-01, STALE-02, STALE-03, D-20, D-06, read-side-merge, mutation-lock]
requires: ["59-02 producer-side pooling at 323c0d1"]
provides:
  - "score.py min_confidence D-20 synthesis: kept_open 'below-min-confidence <N>; deferred-by: <hB>'"
  - "carry_state._merge_nearby: latest well-formed nearby_at per hash, on copies, applied once in _check_state"
  - "TestPhase59CarryStateMutants.test_first_record_per_hash_wins_loses_the_sidecar_stamp"
  - "TestPhase57Mutants.test_min_confidence_no_synthesized_entry_drops_the_deferred_member"
  - "TestPhase57Mutants._run_mutant(read_merge=False) + _READ_MERGE_ONLY"
  - "test_cr02_redecision_after_merge_reads_current, test_cr02_merge_does_not_mutate_state"
affects: [59-04, 59-05, 59-06]
tech-stack:
  added: []
  patterns: ["defense in depth with one lock per layer: producer-side mutants run with the read-side merge off when the merge would also cover them"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "DEFR-01 kept-open row scores 0 (no capped score exists before grouping; A3); the floor number rides in kept_open for 59-05's D-06 note"
  - "The min_confidence mutant replaces the synthesis with `continue` (not `pass`), so the paired deferred-reason append is skipped too and the mutant models the pre-fix drop instead of raising KeyError"
  - "carry_state stamp validity reuses _is_count plus >= 1 (no new validator)"
  - "Producer-side mutants the read-side merge also covers (kept-open own-line-only, row nearby at lead only) run with the merge off, so each layer keeps its own lock"
  - "STALE-03 and STALE-04 marked complete; STALE-02 and DEFR-01 stay pending until the card wording lands in 59-04/59-05"
metrics:
  duration: "~14 min"
  completed: 2026-10-29
  tasks: 2
  files: 3
requirements: [DEFR-01, STALE-02, STALE-03]
---

# Phase 59 Plan 03: Read-side merge and min_confidence deferral Summary

Two fixes. A deferred covered member that a valid `min_confidence` drops now stays open as a kept-open row whose reason reads `below-min-confidence 45; deferred-by: <hB>`. When carry_state reads the state, it lifts the latest `nearby_at` of every same-hash copy onto the representative record, working on copies, so CR-02 re-asks whichever record represents the decision. With this plan, all five reproduced shapes are green on the real chain and `_EXPECTED_RED_UNTIL_59_03` is gone.

## Green SHAs

| Fixture | Red at | Green at |
|---|---|---|
| test_dmc_deferred_covered_member_below_min_confidence_stays_open | 82ec58b | 1927508 |
| test_cr02_edit_beside_the_second_sidecar_reasks | 82ec58b | a56b48c |

Reverse spot-check: the tree at a56b48c with carry_state.py restored from 1af0090 (59-02) gives `test_cr02_edit_beside_the_second_sidecar_reasks` -> 1 failed (observed).

## Tasks

| Task | Name | Commit | Verify (observed) |
|------|------|--------|-------------------|
| 1 | D-20 synthesis on the min_confidence branch (DEFR-01, D-06) | 1927508 | `-k "dmc or dmx or p3 or TestDeferredStaysOpen or no_synthesized_entry"` -> 10 passed; `-k "test_dmc_ or test_dmx_"` -> 2 passed; `test_score.py -k Golden` -> 9 passed; TestGolden passed; greps `"below-min-confidence %d; deferred-by: %s"` 1, `"reason": "below-min-confidence",` 1; probe: the new mutant trips exactly `test_dmc_...` among the _ROW_TESTS |
| 2 | carry_state `_merge_nearby` at the read boundary (CR-02) + mutant | a56b48c | `pytest -q test_decision_continuity.py test_carry_state.py` -> 341 passed, 0 failed; greps `def _merge_nearby` 1, anchor line 1, `_EXPECTED_RED_UNTIL_59_03` 0, `class TestPhase59CarryStateMutants` 1, `snapshot["nearby_at"] =` none; `-k "TestPhase59CarryStateMutants or test_p4_"` -> 2 passed |

## Full offline suite (after a56b48c)

`cd plugins/vibe-check/scripts && pytest -q` -> **3619 passed, 0 failed, 4772 subtests passed in 157.63s**. That is the first fully green suite in this phase. `test_replay.py` alone -> 64 passed, 10 subtests passed (it also ran inside the full suite). GOLDEN_DIGEST did not move: `test_score.py -k Golden` -> 9 passed, and TestGolden passed.

## Mutant map (new or changed in this plan)

| Guard | Mutant test | Trips |
|---|---|---|
| min_confidence D-20 synthesis | test_min_confidence_no_synthesized_entry_drops_the_deferred_member (`continue`) | dmc only (not dmx, p3, deferred) |
| threshold D-20 synthesis | test_no_synthesized_entry_drops_the_deferred_member (anchor lengthened to the full call) | deferred (not dismissed, s1) |
| carry_state read-side merge | TestPhase59CarryStateMutants.test_first_record_per_hash_wins_loses_the_sidecar_stamp | cr02 -> current; cr01 and cr04 still stale |
| kept-open nearby over copies | test_kept_open_own_line_only_loses_the_other_copy (now `read_merge=False`) | cr01 edit@33 |
| row nearby over copies + covered | test_nearby_judged_at_the_lead_only_loses_the_other_copy (now `read_merge=False`) | p1, cr04 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The planned `pass` mutant for the min_confidence synthesis raised instead of failing**
- **Found during:** Task 1
- **Issue:** When only the assignment becomes `pass`, the paired append of the deferred reason still runs. `_kept_open_rows` then raises KeyError on the missing `carried_obligations` entry. That is an error, not the pre-fix drop, and `_failures` rejects errors.
- **Fix:** The mutant replaces the assignment with `continue`. The member is filtered and nothing keeps it, which is exactly the behavior before D-20. The probe showed it trips only test_dmc_.
- **Cost if wrong:** none for coverage. The mutant still removes exactly the synthesis.
- **Files modified:** test_decision_continuity.py
- **Commit:** 1927508

**2. [Rule 2 - Decorative guard] The read-side merge masked two producer-side mutants**
- **Found during:** Task 2
- **Issue:** Once `_merge_nearby` was in place, `test_kept_open_own_line_only_loses_the_other_copy` and `test_nearby_judged_at_the_lead_only_loses_the_other_copy` stopped tripping. The merge lifts the other copy's stamp onto the representative, so cr01 and p1 read stale even with the producer guard removed. Each of those producer guards would have become a lock that can never trip.
- **Fix:** `_run_mutant(..., read_merge=False)` runs both the baseline and the mutant with a carry_state that has the merge removed. The baseline is asserted to equal exactly `_READ_MERGE_ONLY` (cr02_edit, cr02_redecision and the `test_cr02_` prefix), and that set is subtracted. Both mutants trip their named fixtures again. The redecision test is listed in `_READ_MERGE_ONLY` because it locks the writer's merged view.
- **Cost if wrong:** if a producer mutant ever trips only a `test_cr02_*` fixture, that trip is hidden in read_merge=False runs. None of the current assertions depend on one.
- **Files modified:** test_decision_continuity.py
- **Commit:** a56b48c

**3. [Plan detail] The carry_state mutant asserts the full state triple**
- The plan asked for cr02 to read current under the mutant while cr01 and cr04 stay stale. The test asserts `("stale","stale","stale")` unpatched and `("current","stale","stale")` patched, all in one assertion.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** the read-side merge closes CR-02 only and is independent of the producer-side pooling from 59-02. **Actual:** the merge also covers the CR-01 and p1 shapes at read time, so the two layers overlap. **Why:** both layers pool the same identity's nearby stamps, one when the scorer writes them and one when carry_state reads them. **Cost if wrong:** low. Both layers are kept and each has its own lock (deviation 2). If 59-06 or review wants a single layer, the producer pooling for those shapes could be removed. That would be a scope call, not a correctness one.

## Requirements

- STALE-03 marked complete. Evidence is now pooled per hash on both the scorer side (59-02) and the state read (this plan), and the outcome no longer depends on which record represents the decision.
- STALE-04 marked complete. The c59 controls (edit outside every window keeps the decision) are green, and `_NEARBY_LINES` is unchanged.
- STALE-02 and DEFR-01 stay **pending**. The re-ask and the open deferred row work on the real chain, but the "correct reopen reason" on the card (59-04/59-05) and the D-06 card note (59-05) are not built yet.

## Known Stubs

None.

## Threat Flags

None. T-59-06: `_merge_nearby` returns copies, and `test_cr02_merge_does_not_mutate_state` asserts the stored state JSON is byte-equal after the reads. T-59-07: a stamp counts only if it is a plain int >= 1 (bools and strings are ignored). T-59-08: nothing writes `decisions` except `record_decisions`.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py (`"below-min-confidence %d; deferred-by: %s"` x1)
- FOUND: plugins/vibe-check/scripts/carry_state.py (`def _merge_nearby` x1, anchor x1)
- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (`class TestPhase59CarryStateMutants` x1, `def test_min_confidence_no_synthesized_entry_drops_the_deferred_member` x1, `_EXPECTED_RED_UNTIL_59_03` x0)
- FOUND: commits 1927508, a56b48c
