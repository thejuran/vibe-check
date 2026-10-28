---
phase: 57-decision-continuity-within-closure
plan: 11
subsystem: vibe-check scorer nearby window (score.py) and its tests
tags: [score, nearby-window, symmetric, replay, allowances, gap-closure]
requires: ["57-10"]
provides:
  - "score._nearby_changed: window max(1, line - 5)..line + 5 (symmetric, clipped at line 1), shared with _independent_trigger"
  - "lower-bound mutant (test_nearby_window_lower_bound_dropped_misses_edits_above) and retargeted upper-bound mutant"
  - "TestNearbyAt / test_trigger / cross-module pairs pinned at the symmetric boundary"
affects: ["57-12", "57-13"]
tech-stack:
  added: []
  patterns:
    - "one constant + one function define the window for both the decision re-ask stamp and the Phase 56 re-check trigger"
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-11-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/scripts/test_verified_fixes.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/carry_state.py
decisions:
  - "Nearby window is symmetric (5 above, 5 below, clipped at line 1) and the re-check trigger widens with it (D-14)"
  - "No ALLOWANCES-phase57-nearby.json: replay diff showed 0 runs differing after the widening, so nothing was allowed"
metrics:
  duration: "~10 min"
  completed: 2026-10-26
  tasks: 2
  files: 5
---

# Phase 57 Plan 11: Symmetric Nearby Window Summary

The nearby window in `score._nearby_changed` now covers the flagged line plus 5 lines above and 5 below it, with the start clipped at line 1. The Phase 56 re-check trigger uses the same function and the same `_NEARBY_LINES` constant, so it widened too. Deleting a guard just above a "guarded upstream" dismissal now re-asks the owner (D-14, SA-01). Both ends of the window have a mutant that makes the end-to-end fixtures fail. Replay is unchanged: 0 differing runs, REGRESSED 0.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Symmetric window, flipped expectations, lower-bound mutant, wording | 31c51f6 | score.py, test_score.py, test_verified_fixes.py, test_decision_continuity.py, carry_state.py |
| 2 | Replay candidate + diff after widening | (no file output: 0 differing, no allowances file) | none |

## Code change

- `score.py::_nearby_changed`: `window = range(max(1, line - _NEARBY_LINES), line + _NEARBY_LINES + 1)`. The call wiring is unchanged: `_independent_trigger` still ends with `return _nearby_changed(record, changed_line_ranges)`.
- Updated wording: the comment block above `_NEARBY_LINES` (removed "never above"), plus the `_independent_trigger`, `_nearby_changed` and survivor `nearby` docstrings.
- `carry_state.py` (wording only): the module docstring, the `_evidence_of` comment and the `_nearby_since` docstring.
- Grep checks: `grep -c beneath score.py carry_state.py` gives 0/0, `grep -ci "never above" score.py` gives 0, `grep -c "max(1, line - _NEARBY_LINES)" score.py` gives 1 and `grep -c "range(line, line + _NEARBY_LINES + 1)" score.py` gives 0.

## Flipped / replaced assertions

This command lists the removed assertion lines: `git diff -U0 -- test_score.py test_verified_fixes.py test_decision_continuity.py | grep '^-.*assert'`. It printed exactly three lines:

| Removed | Replacement (new boundary pinned) |
| ------- | --------------------------------- |
| `assertEqual(len(pairs), 20)` | `assertEqual(len(pairs), 22)`. Added pairs `(3, [[1,1]])` (line-1 clip hit) and `(10, [[4,4]])` (6 above, miss) |
| `assertEqual(len(hits), 9, hits)` | `assertEqual(len(hits), 14, hits)`. A comment lists all 14 hits: line 10 with an edit at 7..15 (9), `[[1,9]]`, `[[1,10]]`, `[[15,40]]`, line 1 with `[[6,6]]`, line 3 with `[[1,1]]` |
| `assertFalse(_independent_trigger(rec, [], {f: [[70, 79]]}))` | `assertFalse(... [[70, 74]])` (6 above misses) + `assertTrue(... [[75, 75]])` + `assertTrue(... [[75, 79]])` (5 above hits) |

Changes to subTest tables (the assertions themselves did not change):
- `TestNearbyAt.test_survivor_window_edges`: `(8, False), (9, False)` became `(9, True), (5, True), (4, False)`, with a D-14 comment.
- `TestNearbyAt.test_survivor_no_stamp_outside_window`: `[[8,8]]` became `[[4,4]]`.
- `TestNearbyAt.test_independent_trigger_unchanged`: added `[[5,5]]` (hit from above), `[[4,4]]` (miss) and the clip case (line 3, `[[1,1]]`). This stays a contract test (trigger == touched or `_nearby_changed`).
- `test_decision_continuity` upper-bound mutant: the target string moved to the new expression.

## Mutant ledger

| Mutant | Target (count 1 in score.py) | Real code | Under mutant |
| ------ | ---------------------------- | --------- | ------------ |
| upper bound dropped | `range(max(1, line - _NEARBY_LINES), line + _NEARBY_LINES + 1)` -> `... line + _NEARBY_LINES)` | `test_r2_edit_within_five_beneath_reopens` 0 failures | 1 failure (offset=5) |
| lower bound dropped (new) | `max(1, line - _NEARBY_LINES)` -> `line` | `test_r2_edit_within_five_above_reopens` 0 failures | 3 failures (offset=1, 3, 5) |

## Verification (observed)

- `pytest -q test_score.py test_verified_fixes.py test_decision_continuity.py test_carry_state.py` gave **843 passed, 811 subtests passed**.
- `pytest -q test_decision_continuity.py -k "TestNearbyEdit or TestCrossModuleGuards or TestPhase57Mutants"` gave 13 passed, 44 subtests passed. These include `test_r2_edit_within_five_above_reopens` (now green), `test_r2_edit_six_above_keeps`, `test_r2_edit_six_beneath_keeps`, both window mutants and `test_r8_guard_deleted_directly_above_reopens`.
- `pytest -q test_score.py -k "TestNearbyAt or ImportSet or Golden"` gave 21 passed. `pytest -q test_verified_fixes.py` gave 87 passed, 102 subtests passed.
- Golden digest check printed `golden ok`.
- `pytest -q test_replay.py` gave 64 passed, 10 subtests passed. The holdout hook did not block anything.
- Full suite (`pytest -q` from plugins/vibe-check/scripts, includes test_replay.py) gave **1 failed, 3247 passed, 4307 subtests passed**. The one failure is `test_nv_render.py::TestDeletionRangeLock::test_deletion_range_rule_locked`, which 57-12 owns and was expected to stay red. Before this plan the suite had 4 failed / 3246 passed. The three `test_r2_edit_within_five_above_reopens` offsets now pass, and the new lower-bound mutant test accounts for the +1 passed.
- The 57-08 WR-02 deletion fixture (`test_r8_guard_deleted_directly_above_reopens`) still passes as written. Its expectations did not need to change.

## Replay

Both commands were run from `plugins/vibe-check/scripts` at commit 31c51f6 (SP = the session scratchpad).

```
python3 replay.py candidate --name phase57-gaps --scorer rev:HEAD --out $SP/phase57-gaps-candidate.md   # rc=0
```
Result: kept 25 / protected 26 · REGRESSED 0 · UNEVALUABLE 0 · AMENDED 1 (the existing triggarr-secret-in-logs/run-2 amendment). The FP headline went from baseline 16/18 to candidate 14/18, the same as 57-07.

```
python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SP/phase57-gaps-diff.md   # rc=0
```
Result: runs compared 170 · runs differing 0 · runs differing (allowed) 0 · runs with unallowed differences 0.

**Runs differing 0, so nothing was allowed.** `docs/design/b3-ground-truth/ALLOWANCES-phase57-nearby.json` was not created and is dropped from this plan's outputs, the same as in 57-07.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_na_obligation` fixture assumed the one-sided window**
- **Found during:** Task 1
- **Issue:** The fixture changed line 10 so the change would land "inside A's window (10..15), outside B's (11..16)". Under the symmetric window, B's window (line 11) is 6..16, which contains line 10. That would break `test_obligation_member_stamps_and_carries`'s `assertNotIn("nearby_at", lead3["snapshot"])`.
- **Fix:** The pass-3 edit moved to line 5, which is inside A's window (5..15) and outside B's (6..16). The docstring was updated to cite D-14. No assertion changed.
- **Cost if wrong:** If line 5 were inside B's window, the test would no longer separate the member stamp from the lead stamp. It still asserts both sides, so a wrong fixture would show up as a red test, not a hollow one.
- **Files modified:** plugins/vibe-check/scripts/test_score.py
- **Commit:** 31c51f6

**2. [Rule 1 - Plan arithmetic] Cross-module hit count is 14, not 15**
- **Found during:** Task 1
- **Issue:** The plan listed 9 + 5 named hits but said 15. The real count is 14.
- **Fix:** The test asserts 14, and the comment lists every hit (the plan allowed correcting the number after running).
- **Cost if wrong:** None. The assertion matches observed behaviour and every hit is listed.
- **Commit:** 31c51f6

**3. Long line wrapped** in `_nearby_changed` (`window = range(...)` then `any(... for n in window)`). The mutation target string is still on one line and occurs once.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py (contains `max(1, line - _NEARBY_LINES)`)
- FOUND: commit 31c51f6
- ABSENT, as intended: docs/design/b3-ground-truth/ALLOWANCES-phase57-nearby.json (0 differing runs)
