---
phase: 57-decision-continuity-within-closure
plan: 14
subsystem: vibe-check decision continuity (test fixtures)
tags: [reproduce-first, fixtures, split-pass, nearby-at, real-chain, gap-closure]
requires: ["57-13"]
provides:
  - "split_scenario(edit_a, real_diff) and absorbed_split_scenario(owed_before_split) real-chain harness"
  - "TestSplitPassNearby s1-s3 RED + s4 green negative"
  - "TestGapClosure57 _inherited_split_pass2 + g2c/g2d (green)"
  - "TestCrossModuleGuards.test_split_row_snapshot_is_the_split_pass_shape (RED)"
affects: ["57-15 (score.py may change only against these reds)", "57-16 (ledger cites this red run)"]
tech-stack:
  added: []
  patterns: ["reproduce-first RED on the real scorer chain", "producer/consumer shape guard"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_carry_state.py
decisions:
  - "The split-pass defect is producer-only: with nearby_at injected into the real split row, decision_state/stale_cause/finalize_counts/gate/card already behave per D-17, so 57-15 needs only the score.py stamp"
metrics:
  duration: "~25 min"
  completed: 2026-10-26
  tasks: 2
  files: 2
requirements: [DECN-03]
---

# Phase 57 Plan 14: Split-pass nearby stamp reproduction Summary

Real-chain RED fixtures (score.run -> append_pass -> carry_state -> batch_card) prove that a covered or absorbed finding split into its own row by the lead's nearby fix gets no `nearby_at` stamp and its decision silently stays current (D-17), plus a producer/consumer guard pinning the split-pass snapshot shape.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 7ff4492 | test(57-14): add failing real-chain fixtures for the split-pass nearby stamp |
| 2 | 08126a8 | test(57-14): pin the split-pass snapshot shape across producer and consumer |

No production file changed: `git diff --name-only ea6fcac HEAD` lists only `test_carry_state.py` and `test_decision_continuity.py`.

## Red run (HEAD, pre-fix)

Task 1, on the unfixed tree (`pytest -q test_decision_continuity.py -k TestSplitPassNearby -rfE --tb=line`, the `/opt/homebrew/...case.py:878` location lines elided):

```
FFF.                                                                     [100%]
=================================== FAILURES ===================================
E   AssertionError: None != 2 : split row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 3 : split row snapshot has no nearby_at: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : owed nearby_at lost at the split: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
=========================== short test summary info ============================
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s1_inherited_member_split_by_nearby_fix_is_reasked
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s2_own_decision_absorbed_then_split_by_nearby_fix_is_reasked
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s3_owed_stamp_survives_the_split
3 failed, 1 passed, 41 deselected in 0.05s
```

Plan verification (`-k "TestSplitPassNearby or test_split_row_snapshot"`):

```
FFF.F                                                                    [100%]
=================================== FAILURES ===================================
E   AssertionError: None != 2 : split row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 3 : split row snapshot has no nearby_at: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : owed nearby_at lost at the split: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: Items in the second set but not the first:
    'nearby_at'
=========================== short test summary info ============================
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s1_inherited_member_split_by_nearby_fix_is_reasked
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s2_own_decision_absorbed_then_split_by_nearby_fix_is_reasked
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s3_owed_stamp_survives_the_split
FAILED test_decision_continuity.py::TestCrossModuleGuards::test_split_row_snapshot_is_the_split_pass_shape
4 failed, 1 passed, 41 deselected in 0.04s
```

Task 2 consumer side: `pytest -q test_carry_state.py -k TestGapClosure57` -> `22 passed, 197 deselected, 8 subtests passed` (was 20; g2c/g2d green). `pytest -q test_carry_state.py` -> `219 passed, 278 subtests passed`.

Full suite (from plugins/vibe-check/scripts, includes test_replay.py): `4 failed, 3251 passed, 4312 subtests passed in 237.51s`. The 4 failures are exactly s1, s2, s3 and the producibility guard; 3251 + 4 = 3255 = HEAD's 3248 + 7 new tests. Golden digest: `golden ok`.

## What each fixture drives

- **s1** (`split_scenario(real_diff=True)`): pass 1 security B (line 12) leads, bugs A (line 10) rides as a covered member, owner dismisses B's row. Pass 2 rewrites line 12, B resolves on re-check, diff `{F: [[12, 12]]}`. A's split row must carry `nearby_at == 2` and reopen via the covering decision with cause "nearby" (self-check: `score._nearby_changed(rec, {F: [[12, 12]]})` is True).
- **s2** (`absorbed_split_scenario()`): A dismissed on pass 1 (own decision); pass 2 a critical security B at line 12 absorbs A as an obligation sidecar (diff 30-31; A current); pass 3 B fixed and resolved, diff `{F: [[12, 12]]}`. A's split row must carry `nearby_at == 3` and reopen.
- **s3** (`absorbed_split_scenario(owed_before_split=True)`): the pass-2 diff names line 12 so A's obligation snapshot is stamped `nearby_at == 2` while absorbed (stale already); pass 3 splits with an empty diff. The owed stamp is dropped by the fresh split-row snapshot.
- **s4** (green negative): in the same pass 2, the fresh security lead's snapshot has no `nearby_at`; only A's obligation snapshot carries it.
- **g2c / g2d** (test_carry_state): hand-built inherited row in the split-pass shape (snapshot at_pass 2, line 12, with/without `nearby_at: 2`) -> stale/"nearby"/outstanding [HC] vs current/None/[].
- **Producibility guard**: the real split row's snapshot keys must equal `{at_pass, file, line, canonical_line_content, band, nearby_at}` with at_pass == nearby_at == 2, i.e. exactly the g2c shape.

Consumer-side check (not committed, run ad hoc): injecting `nearby_at` into the real split rows of s1/s2/s3 gives `stale nearby True outstanding-to-phase-5` for all three, and the s1 card row has `stale.cause == "nearby"`, `via == "covering"`. The defect is the producer stamp alone.

## No-weakening greps

- `git diff HEAD~1 -U0 -- test_decision_continuity.py | grep -c '^-.*assert'` -> 0 (and 0 for the Task 1 diff)
- `git diff -U0 -- test_carry_state.py | grep -c '^-.*assert'` -> 0; `grep -c '^-\s*def '` -> 0
- `grep -c "does not confound" test_decision_continuity.py` -> 0
- `pytest -q test_decision_continuity.py -k "not TestSplitPassNearby and not test_split_row_snapshot"` -> `41 passed, 5 deselected, 60 subtests passed`
- `-k "TestRegrouping or TestNearbyEdit or TestSameHashLeadKeepsNearbyStamp or TestPhase57Mutants or TestPhase57EndToEnd"` -> `17 passed, 28 deselected, 10 subtests passed`
- `split_scenario()` default and `edit_a=True` paths produce the same ranges as before (`{F: []}` / `{F: [[10, 10]]}`); r6 tests green.

## Deviations from Plan

None - plan executed exactly as written. The planner's concern about where `nearby_at` sits on the absorbed sidecar record was checked: `record_of(s2, hA)["snapshot"]["nearby_at"] == 2` holds on the real chain (the sidecar exposes the obligation snapshot under `snapshot`), so no fixture shape change was needed.

Minor ordering note: s2 and s3 assert their pass-2 self-checks (absorbed into hB / owed stamp present) before the pass-3 `nearby_at` assertion, as the behaviour block orders them; those self-checks pass, so the first failing assertion in each is the stamp, as recorded above.

## Hook blocks

None.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (class TestSplitPassNearby, absorbed_split_scenario, test_split_row_snapshot_is_the_split_pass_shape)
- FOUND: plugins/vibe-check/scripts/test_carry_state.py (_inherited_split_pass2, test_g2c_, test_g2d_)
- FOUND: 7ff4492, 08126a8
