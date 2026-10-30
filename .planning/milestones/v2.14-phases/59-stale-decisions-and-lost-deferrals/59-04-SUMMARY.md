---
phase: 59-stale-decisions-and-lost-deferrals
plan: 04
subsystem: vibe-check scorer + carry-forward state (reopen-reason data for the card)
tags: [STALE-02, STALE-05, D-04, D-05, nearby_spots, stale_spots, mutation-lock]
requires: ["59-03 read-side merge at a56b48c"]
provides:
  - "score._nearby_spots(own_line, copies, grouped, changed_line_ranges)"
  - "score._valid_spots; _snapshot_for(..., spots=None) records/carries nearby_spots"
  - "carry_state._well_formed_spots, carry_state._lifted_spots"
  - "carry_state.stale_spots(record, state) -> {line, kind, others} | None (the card's single reader)"
  - "cr01_three_copies_scenario(); six test_sp59_ real-chain tests; TestSnapshotSpotsUnit"
  - "TestPhase57Mutants.test_spots_not_recorded_loses_the_other_copy_line"
affects: [59-05, 59-06]
tech-stack:
  added: []
  patterns: ["producer records presentation data on the stamp; reader derives read-time-only data on copies; one validated reader for the card"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "A carried spot at the row's own line is dropped (a prior pooled from another copy can name the row itself)"
  - "A lifted stamp's derived spots are the SOURCE copy's spots when it has any, else the source's line as a copy (not the representative's stale spots)"
  - "spots= is passed before carried= in _kept_open_rows so the existing `carried=bool(same))` mutant anchor stays unique"
  - "test_sp59_ prefix and the cr02 spot test join _READ_MERGE_ONLY (they need the read-side merge)"
  - "STALE-02 and STALE-05 stay pending until 59-05 renders the wording"
metrics:
  duration: "~20 min"
  completed: 2026-10-29
  tasks: 2
  files: 3
requirements: [STALE-02, STALE-05]
---

# Phase 59 Plan 04: Reopen-spot data for the card Summary

When a decision reopens because code changed beside a different spot, the stamped snapshot now records which spot it was. That spot is either another copy of the line (`"copy"`) or a finding grouped in the row (`"grouped"`). The list is sorted by line and survives quiet passes. carry_state derives the CR-02 spot at read time, without writing it to the state, and exposes one reader, `stale_spots`, which 59-05's card wording will render from.

## Tasks

| Task | Name | Commit | Verify (observed) |
|------|------|--------|-------------------|
| 1 | score.py records `nearby_spots` on stamped snapshots and carries them | f8b9055 | `pytest -q test_decision_continuity.py test_score.py` -> 615 passed, 0 failed; probe printed `ok` (line-10 row `[[30,"copy"]]`, line-30 row has no key); `-k "split_row_snapshot_is_the_split_pass_shape or TestGolden or TestSplitPassNearby"` -> 6 passed; `test_score.py -k Golden` -> 9 passed; greps `def _nearby_spots` 1, `spots=None` 1, `nearby_spots` 11; test_replay member anchor count 1 |
| 2 | carry_state `stale_spots` + derived CR-02 spot; sp59 tests + mutant | 3e31654 | plan verify `-k "sp59 or Mutants or TestStaleDecisions59"` -> 48 passed; `-k test_sp59_` -> 6 passed; `-k spots_not_recorded` -> 1 passed; `test_decision_continuity.py test_carry_state.py test_score.py test_batch_card.py test_card_text.py` -> 979 passed, 0 failed; greps `def stale_spots` 1, `def _well_formed_spots` 1 |

Observed shapes on the real chain:
- CR-01 edit@33: `{"line": 30, "kind": "copy", "others": 0}`
- CR-04: `{"line": 10, "kind": "grouped", "others": 0}`
- CR-02: `{"line": 30, "kind": "copy", "others": 0}`. The representative is still the line-10 sidecar, and `json.dumps(s2["passes"])` contains no `nearby_spots`.
- Three copies (10/30/50, edits at 33 and 53): stored `[[30,"copy"],[50,"copy"]]`, read as `{"line": 30, "kind": "copy", "others": 1}`
- Quiet pass after CR-01 edit@33: `nearby_at` 2 and `[[30,"copy"]]` both carried. The line-30 row does not name itself.

## Full offline suite (after 3e31654)

`cd plugins/vibe-check/scripts && pytest -q` -> **3630 passed, 0 failed, 4772 subtests passed in 156.24s**. `pytest -q test_replay.py` -> 64 passed, 10 subtests passed, with no replay delta. GOLDEN_DIGEST is unchanged (`7a516d01…`; test_score.py was not touched), and `test_score.py -k Golden` -> 9 passed.

## Mutant map (new in this plan)

All of these were probed by hand, each run against the named tests and observed to trip:

| Guard | Lock | Observed trip |
|---|---|---|
| `cur["nearby_spots"] = spots` (fresh stamp) | test_spots_not_recorded_loses_the_other_copy_line | sp59 cr01, cr04, three_copies, quiet_pass. cr02 spot, malformed, test_cr01_ and test_cr04_ are not tripped (asserted) |
| keep-branch carry | test_sp59_quiet_pass_keeps_the_spots | 1 failed |
| refresh-branch carry | TestSnapshotSpotsUnit.test_refresh_branch_carries_the_spots | 1 failed |
| score `_valid_spots` | test_malformed_prior_spots_are_not_carried | 1 failed |
| spots carried only with a stamp | test_spots_without_a_stamp_are_not_carried | 1 failed |
| own-line drop on carry | test_sp59_quiet_pass_keeps_the_spots (line-30 row) | 1 failed |
| own line excluded in `_nearby_spots` | sp59 cr01 + split-pass key-set lock | 2 failed |
| grouped kind | sp59 cr04 + unit | 2 failed |
| carry_state derived spot (`_lifted_spots`) | test_sp59_cr02_merged_stamp_names_the_other_sidecar | 1 failed |
| reader sort | test_sp59_malformed_spots_read_as_none | 1 failed |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A carried spot could name the row's own line**
- **Found during:** Task 1 (quiet-pass probe)
- **Issue:** On the quiet pass, the line-30 kept-open row pooled the line-10 copy's prior, which had the same stamp and the earlier arrival. Its refresh branch then carried `[[30,"copy"]]`, so the row named itself as "another copy".
- **Fix:** On the keep and refresh branches, carried spots at `cur["line"]` are dropped. This is locked by the line-30 assertion in test_sp59_quiet_pass_keeps_the_spots.
- **Cost if wrong:** low. A self-reference could only reach the card if that row became the representative.
- **Files modified:** score.py
- **Commit:** f8b9055

**2. [Rule 1 - Bug] The plan's derived-spot rule mixed in stale spots**
- **Found during:** Task 2
- **Issue:** The plan said to derive spots as "the representative's spots plus `[source_line, "copy"]`". But the representative's spots describe its own older stamp, not the lifted one. The source copy's line also did not necessarily change when that source's own stamp named other spots.
- **Fix:** `_lifted_spots` uses the SOURCE copy's well-formed spots when it has any, else `[[source_line, "copy"]]`. It drops the representative's own line and sorts by line. CR-02 reads the same (`line 30, copy`) under either rule.
- **Cost if wrong:** low. This only matters when a lifted source already carries spots, which no current producer path writes onto member sidecars.
- **Files modified:** carry_state.py
- **Commit:** 3e31654

**3. [Rule 3 - Blocking] A mutant anchor moved**
- Adding `spots=` after `carried=bool(same)` broke the existing `test_kept_open_covered_row_without_carried_is_not_stamped` anchor, which became non-unique. The fix was argument order: `spots=row_spots, carried=bool(same))`. The anchor and its test are unchanged.

**4. [Rule 2 - Decorative-guard prevention] Extra locks beyond the plan's six tests**
- The refresh-branch carry, the score-side validator and the stamp gate had no test that could trip them. I added `TestSnapshotSpotsUnit` (4 unit tests) instead of adding to the sp59 prefix, so `-k test_sp59_` still counts exactly 6.
- `"test_sp59_"` and the cr02 spot test are added to `_READ_MERGE_ONLY`, because they need the read-side merge. Without that, the `read_merge=False` baseline check would fail for the two producer mutants from 59-03.
- **Cost if wrong:** in those two `read_merge=False` mutant runs, an sp59 trip is hidden. Neither run asserts on sp59.

**5. [Plan detail] The mutant's cr02 check uses full names**
- `_failures` already runs every `_ROW_TESTS` method and records full names. The mutant test therefore asserts the full sp59 names directly (four In, cr02 and malformed NotIn) instead of running them a second time.

**6. [Acceptance grep] Filter line in carry_state**
- The no-in-place-write grep returns 3 docstring lines and one dict-comprehension filter (`{k: v for k, v in lifted.items() if k != "nearby_spots"}`). None of them writes into a stored dict. `test_cr02_merge_does_not_mutate_state` and the sp59 cr02 JSON assertion both stay green.

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** spots carried with `nearby_at` are always about the row they ride on. **Actual:** the pooled prior can come from another copy of the same identity (D-19). When stamps tie, `_pooled_prior` picks the earliest arrival, so which copy's spots ride is decided by carryforward order. **Why:** `_pooled_prior` ranks by stamp, then by oldest `at_pass`. It does not know the row's line. **Cost if wrong:** low to medium. Carryforward order is deterministic for a given state, so results are stable, and the representative row is first in order. But a state where a different copy precedes the representative could, on a quiet pass, read the same-spot wording instead of naming the other copy. 59-05 or 59-06 could make the tie-break prefer the candidate at the row's own line if STALE-05 review wants it.

## Requirements

STALE-02 and STALE-05 stay **pending**. This plan produces the data and the reader, and 59-05 renders the D-04/D-05 card wording from `stale_spots`. ROADMAP.md and PROJECT.md were not touched, because they hold the owner's uncommitted edits.

## Known Stubs

None. `stale_spots` has no caller yet, by design. 59-05's batch_card wording binds to it.

## Threat Flags

None new. T-59-10: `_well_formed_spots` and `_valid_spots` accept only `[int>=1 non-bool, "copy"|"grouped"]`, and the malformed test covers bool, str, unknown kind, 0, a 1-item list and a non-list. T-59-11: the CR-02 test asserts no `nearby_spots` in the stored passes. T-59-12: the list is bounded by the copies and members in a row, and is carried, not appended.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py (`def _nearby_spots` x1, `spots=None` x1)
- FOUND: plugins/vibe-check/scripts/carry_state.py (`def stale_spots` x1, `def _well_formed_spots` x1)
- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (6 `test_sp59_` tests, `test_spots_not_recorded_loses_the_other_copy_line`)
- FOUND: commits f8b9055, 3e31654
