---
phase: 57-decision-continuity-within-closure
plan: 08
subsystem: vibe-check carry-forward decisions (test fixtures only)
tags: [reproduce-first, fixtures, carry_state, score, nearby-window, covers, gap-closure]
requires: ["57-07"]
provides:
  - "test_carry_state.py: TestGapClosure57 (G1 CR-01, G2a/G2b CR-02, G3a/G3b WR-03, G6 D-15), all 6 red on HEAD"
  - "test_decision_continuity.py: test_r2_edit_within_five_above_reopens (D-14, red), test_r2_edit_six_above_keeps, test_r8_guard_deleted_directly_above_reopens + deletion_hunk_ranges helper (WR-02 lock, green), pass-6 note flipped to 1 finding (D-15, red)"
  - "test_nv_render.py: DELETION_RANGE_PHRASES / deletion_range_holds lock on the changed-line ranges bullet (red until 57-12)"
  - "Verbatim red run for the 57-13 ledger"
affects: ["57-09", "57-10", "57-11", "57-12", "57-13"]
tech-stack:
  added: []
  patterns:
    - "no subTest around a RED expectation: pytest 9 reports the parent PASSED when only a subtest fails, so a red fixture that must count as a failed test asserts sequentially"
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-08-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/test_carry_state.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_nv_render.py
decisions:
  - "G6 asserts its two cases sequentially rather than in subTests, so the red case fails the test itself under pytest 9"
  - "WR-02 fixture asserts the pass-2 band is critical, not warning: the deletion range's T + 1 end is the relocated flagged line itself, which lifts the score 82 -> 100; the nearby cause still wins on the card"
  - "WR-02 prose lock is a separate TestDeletionRangeLock class, not a CASES entry, so only test_deletion_range_rule_locked is red (a CASES entry would also turn test_each_predicate_holds and the deleting mutant red)"
metrics:
  duration: "~25 min"
  completed: 2026-10-26
  tasks: 2
  files: 3
---

# Phase 57 Plan 08: Gap-closure RED fixtures Summary

Every gap-closure item now has a committed fixture that fails on the current code: the three blocking wrong-keeps (CR-01, CR-02, WR-03), the owner's rulings D-14 (window covers lines above too) and D-15 (count concerns, not reports), and the WR-02 prose rule for deletion-only hunks. No production file changed. The only existing expectations that flipped are the two the plan named.

## What was built

### Task 1: `TestGapClosure57` in test_carry_state.py (commit a606a8e)

Small builders (`g_snap`, `g_member`, `g_obligation`, `g_row`, `g_lead`) and new hashes `HR = "7"*64` and `HB2 = "2"*64`. The class reuses the existing `HC = "c"*64`. Each fixture calls the real `carry_state` functions. It checks its own shape first (bands, membership, `covers` content, saved attribution). Then it asserts both the state read and `finalize_counts(...)["outstanding_cw_hashes"]`.

- **G1 (CR-01):** b's separately-owed finding splits into its own row. It must not inherit HR's decision and must stay outstanding. Sibling check: a same-hash member is still listed in `covers`. This passes today and guards the 57-09 fix against over-excluding.
- **G2a / G2b (CR-02):** an inherited decision must reopen on a lane-backed band rise (`severity`, `gained_lanes == ["security"]`). It must also reopen on a joined newcomer (`joined`, `newcomer_lanes == ["security"]`, `covered_count == 1`).
- **G3a / G3b (WR-03):** lane b was on the row for T2 and later also reports T1, with a band rise. That must reopen (`gained_lanes == ["b"]`). Lane b present only for its own T2, with a rise from persistence alone, must keep the decision.
- **G6 (D-15):** two lanes reporting the same title count as 1 concern; a second title counts as 2.

### Task 2: end-to-end fixtures and prose lock (commit c8ab8f8)

- `test_r2_edit_two_above_keeps` is renamed `test_r2_edit_within_five_above_reopens`. It covers offsets 1/3/5 above, with the same assertions as the beneath test. New `test_r2_edit_six_above_keeps` (line 4) is green. The module and class docstrings now state the symmetric window (D-14).
- New `deletion_hunk_ranges(file, t)` returns `{file: [[max(t, 1), t + 1]]}`. New `test_r8_guard_deleted_directly_above_reopens` deletes line 9 with ranges `deletion_hunk_ranges(F, 8)`. The row keeps its hash, relocates to line 9, goes stale/nearby with `nearby_at == 2`, the gate does not write, and the card shows the "code next to it changed" line. Its `mapping dropped` subtest (`{F: []}`) gives current + write, which proves the mapping is load-bearing. As planned, this test is green now: it is a lock, not a reproduction.
- Owner journey pass 6 now expects " — 1 finding here already dismissed …", then `rows[0]["stale"]["covered"] == 1`.
- test_nv_render.py has `DELETION_RANGE_PHRASES` and `deletion_range_holds`, checked only inside the text between `**changed-line ranges**` and the next `\n   - **` bullet. It also has `TestDeletionRangeLock`: the real-file lock (red), a synthetic-holds check, one removal mutant per phrase, and a moved-to-next-bullet mutant. All three mutant/synthetic tests are green.

## Red run (verbatim, HEAD c8ab8f8, full suite from plugins/vibe-check/scripts)

`pytest -q -rfE` with test_replay.py included: **11 failed, 3220 passed, 4283 subtests passed in 221.93s**. The 11 failures are the 9 named tests; one of them fails on 3 subtests:

| Test | First failing assertion (file:line) | Observed |
|---|---|---|
| test_carry_state.py::TestGapClosure57::test_g1_split_obligation_member_is_not_covered_by_row_decision | :2395 `self.assertIsNone(carry_state.decision_state(rec, s))` | `AssertionError: 'current' is not None` |
| ...::test_g2a_inherited_decision_reopens_on_lane_backed_band_rise | :2437 `self.assertEqual(carry_state.decision_state(rec, s), "stale")` | `AssertionError: 'current' != 'stale'` |
| ...::test_g2b_inherited_decision_reopens_when_a_newcomer_joins | :2451 `self.assertEqual(carry_state.decision_state(rec, s), "stale")` | `AssertionError: 'current' != 'stale'` |
| ...::test_g3a_lane_present_for_another_concern_later_corroborates_and_rise_reopens | :2483 `self.assertEqual(carry_state.decision_state(rec, s), "stale")` | `AssertionError: 'current' != 'stale'` |
| ...::test_g3b_unrelated_concern_lane_with_persistence_rise_keeps | :2504 `self.assertEqual(carry_state.decision_state(rec, s), "current")` | `AssertionError: 'stale' != 'current'` |
| ...::test_g6_covered_count_counts_concerns_not_reports | :2524 `self.assertEqual(carry_state.covered_count(rec, s), expected)` | `AssertionError: 2 != 1` |
| test_decision_continuity.py::TestNearbyEdit::test_r2_edit_within_five_above_reopens (offset=1, 3, 5) | :461 `self.assertEqual(carry_state.decision_state(rec, s2), "stale")` | `AssertionError: 'current' != 'stale'` (x3) |
| test_decision_continuity.py::TestPhase57EndToEnd::test_owner_is_asked_exactly_when_evidence_changes | :1214 pass-6 note `assertIn(" — 1 finding here already dismissed …")` | not found in `'#1 src/a.py:13 — Unchecked return at A (critical) — unchanged since pass 5, decision pending — 2 findings here already dismissed (your reason: false positive, guarded upstream); a new concern from compliance joined it …'` |
| test_nv_render.py::TestDeletionRangeLock::test_deletion_range_rule_locked | :441 `self.assertTrue(deletion_range_holds(_read(COLLECT)))` | `AssertionError: False is not true` |

Each failure matches what the verifier/review predicts (G1 "current" where None is expected; G2a/G2b/G3a "current"; G3b "stale"; G6 2 != 1; D-14 "current"; pass 6 "2 findings").

Other checks:
- `pytest -q test_carry_state.py -k "not TestGapClosure57"`: 197 passed, the same as before this plan.
- `pytest -q test_carry_state.py -k TestGapClosure57`: 6 failed, 0 passed, 0 errors.
- `test_r2_edit_six_above_keeps`, `test_r8_guard_deleted_directly_above_reopens` (including its `mapping dropped` subtest), `test_r2_edit_within_five_beneath_reopens` and `test_r2_edit_six_beneath_keeps` pass.
- test_replay.py: 64 passed, 10 subtests passed. TestGolden and the test_score ImportSet/Golden tests passed in the full run.
- Greps: `def test_g` = 10 (6 new); `finalize_counts(` went from 69 to 77 (+8); `def deletion_hunk_ranges` = 1; `max(t, 1)` = 1; `DELETION_RANGE_PHRASES` = 3.
- `git diff -U0 -- test_decision_continuity.py | grep '^-.*assert'` lists only the pass-6 "2 findings" assertion. The two-above test's `"current"` assertion line is byte-identical to a line the new six-above test keeps, so diff aligns it as unchanged. Its removal from the two-above test is part of the rename.

**Holdout-barrier hook:** blocked nothing. No command was refused.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] G6 subTest loop would not count as a failed test**
- **Found during:** Task 1
- **Issue:** pytest 9.0.3 reports the parent test PASSED when only a subtest fails. The first run showed "6 failed, 1 passed" with G6 as SUBFAILED, which breaks the "6 failed, 0 passed" criterion.
- **Fix:** G6 asserts both cases sequentially, with no subTest. A comment says why.
- **Cost if wrong:** none for behavior; a reader loses the per-case subtest label.
- **Files modified:** plugins/vibe-check/scripts/test_carry_state.py
- **Commit:** a606a8e

**2. [Rule 1 - Bug] Pass-6 assertion order**
- **Found during:** Task 2
- **Issue:** with `covered == 1` asserted before the note, the journey failed on `2 != 1` instead of at the note assertion the criterion names.
- **Fix:** the `covered` assertion now comes after the note assertion.
- **Cost if wrong:** none; both are still asserted.
- **Commit:** c8ab8f8

## Assumption Drift (advisory)

**1. The WR-02 deletion range also lifts the band**
- **Found during:** Task 2
- **Planned:** the guard-deletion fixture reopens only through the nearby window, with the band implicitly unchanged.
- **Actual:** the mapping's `T + 1` end (line 9) is the relocated flagged line itself. The scorer's changed-line scoring therefore lifts the row from 82 to 100 (warning to critical) on pass 2. `stale_cause` is still `nearby`, because the nearby check outranks severity, and the card shows the "code next to it changed" line. The fixture asserts critical explicitly. The mapping-dropped subtest asserts warning.
- **Why:** this is real scorer behavior with the mapping the plan specifies, `[max(T, 1), T + 1]`.
- **Cost if wrong:** if 57-12 picks a different mapping (for example `[T, T]`), the critical assertion flips to warning and must be updated with the prose. A band rise on a deletion-touched line is not a silent close, so nothing fails open.

## Known Stubs

None. All files are test-only.

## Threat Flags

None. No production surface changed.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_carry_state.py (class TestGapClosure57)
- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (def deletion_hunk_ranges)
- FOUND: plugins/vibe-check/scripts/test_nv_render.py (DELETION_RANGE_PHRASES)
- FOUND: commit a606a8e
- FOUND: commit c8ab8f8
