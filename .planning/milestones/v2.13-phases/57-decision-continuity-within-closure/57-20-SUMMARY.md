---
phase: 57-decision-continuity-within-closure
plan: 20
subsystem: scoring / decision continuity (test fixtures)
tags: [reproduce-first, fixtures, same-hash-different-line, arrival-order, min-confidence-twin, in-01, d-20-deferred, lead-order-invariance, real-chain, gap-closure]
requires: ["57-19"]
provides:
  - RED real-chain fixtures for 57-REVIEW-GAPS3.md CR-01 (cross-lane + arrival order), CR-02, IN-01, far twin
  - D-20 deferred-stays-open RED fixture with the dismiss counterpart locked GREEN
  - Lead-order invariance guard widened from six to nine scenarios
  - run_pass forwards deferred_hashes once carry_state.deferred exists
affects: [57-21, 57-22, 57-23]
tech-stack:
  added: []
  patterns: [getattr-guarded harness read for a not-yet-existing carry_state API, variable-length knob tuples in the invariance table]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "57-20: arrival-order invariance scenario keeps the 'carried-leads' first label only to satisfy the coverage lock's baseline rule; both its permutations are fresh same-conf reports"
  - "57-20: run_pass sends deferred_hashes only when passes exist and carry_state.deferred returns a list, so every envelope is byte-identical on today's tree"
metrics:
  duration: ~10min
  completed: 2026-10-27
  tasks: 2
  files: 1
---

# Phase 57 Plan 20: Final-round RED fixtures (pooled evidence, prior gate, D-20) Summary

Real-chain RED fixtures pin every 57-REVIEW-GAPS3.md reproduction (CR-01 cross-lane and arrival-order, CR-02 min_confidence twin, IN-01 foreign stamp, the far-twin pooling shape) plus the D-20 deferred keep-open, and the lead-order invariance guard now permutes the three shapes it was missing. score.py and carry_state.py are untouched.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 1ff95f1 | test(57-20): failing fixtures for pooled carried evidence, prior gate and deferred keep-open |
| 2 | 9fe0e0f | test(57-20): permute same-hash other line, arrival order and dropped twin in the lead-order guard |

## Red run (HEAD, pre-fix)

### Task 1: `pytest -q test_decision_continuity.py -k "TestPooledEvidence or TestPriorGate or TestDeferredStaysOpen" -rfE --tb=line` (from plugins/vibe-check/scripts, tree at 1ff95f1, scorer = 451e84c/cf32de8)

```
F.FF..FF.                                                              [100%]
=================================== FAILURES ===================================
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}
/opt/homebrew/Cellar/python@3.12/3.12.12_2/Frameworks/Python.framework/Versions/3.12/lib/python3.12/unittest/case.py:878: AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}
/opt/homebrew/Cellar/python@3.12/3.12.12_2/Frameworks/Python.framework/Versions/3.12/lib/python3.12/unittest/case.py:878: AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}
E   AssertionError: 12 != 10 : lead depends on arrival order [12, 10]; row {'at_pass': 2, 'file': 'src/a.py', 'line': 12, 'canonical_line_content': 'return None', 'band': 'warning', 'nearby_at': 2}
/opt/homebrew/Cellar/python@3.12/3.12.12_2/Frameworks/Python.framework/Versions/3.12/lib/python3.12/unittest/case.py:878: AssertionError: 12 != 10 : lead depends on arrival order [12, 10]; row {'at_pass': 2, 'file': 'src/a.py', 'line': 12, 'canonical_line_content': 'return None', 'band': 'warning', 'nearby_at': 2}
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
/opt/homebrew/Cellar/python@3.12/3.12.12_2/Frameworks/Python.framework/Versions/3.12/lib/python3.12/unittest/case.py:878: AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : line-30 copy not stamped: {'at_pass': 2, 'file': 'src/a.py', 'line': 30, 'canonical_line_content': 'return None', 'band': 'warning'}
/opt/homebrew/Cellar/python@3.12/3.12.12_2/Frameworks/Python.framework/Versions/3.12/lib/python3.12/unittest/case.py:878: AssertionError: None != 2 : line-30 copy not stamped: {'at_pass': 2, 'file': 'src/a.py', 'line': 30, 'canonical_line_content': 'return None', 'band': 'warning'}
E   AssertionError: 'nearby_at' unexpectedly found in {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': "line_10 = 'edited'", 'band': 'warning', 'nearby_at': 2} : edited finding inherited a foreign stamp: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': "line_10 = 'edited'", 'band': 'warning', 'nearby_at': 2}
/opt/homebrew/Cellar/python@3.12/3.12.12_2/Frameworks/Python.framework/Versions/3.12/lib/python3.12/unittest/case.py:715: AssertionError: 'nearby_at' unexpectedly found in {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': "line_10 = 'edited'", 'band': 'warning', 'nearby_at': 2} : edited finding inherited a foreign stamp: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': "line_10 = 'edited'", 'band': 'warning', 'nearby_at': 2}
E   AssertionError: unexpectedly None : record 845f88b7 is not an open record (decision orphaned)
/opt/homebrew/Cellar/python@3.12/3.12.12_2/Frameworks/Python.framework/Versions/3.12/lib/python3.12/unittest/case.py:715: AssertionError: unexpectedly None : record 845f88b7 is not an open record (decision orphaned)
=========================== short test summary info ============================
FAILED test_decision_continuity.py::TestPooledEvidence::test_p1_cross_lane_same_hash_other_line_nearby_reasks
SUBFAILED(order=[10, 12]) test_decision_continuity.py::TestPooledEvidence::test_p2_same_lane_arrival_order_does_not_pick_the_outcome
SUBFAILED(order=[12, 10]) test_decision_continuity.py::TestPooledEvidence::test_p2_same_lane_arrival_order_does_not_pick_the_outcome
FAILED test_decision_continuity.py::TestPooledEvidence::test_p3_min_confidence_dropped_twin_keeps_the_reask
FAILED test_decision_continuity.py::TestPooledEvidence::test_p4_far_twin_latest_stamp_reaches_the_first_copy
FAILED test_decision_continuity.py::TestPriorGate::test_in01_edited_carried_lead_does_not_carry_its_stamp_onto_the_new_hash
FAILED test_decision_continuity.py::TestDeferredStaysOpen::test_deferred_covered_member_below_threshold_stays_open
7 failed, 4 passed, 62 deselected in 0.04s
```

First failing assertion per red, in order:

| Test | First failing line |
|------|--------------------|
| p1 cross-lane (conf 100) | `None != 2 : row snapshot has no owed nearby_at` (row led by security at line 10) |
| p2 order [10, 12] | `None != 2 : row snapshot has no owed nearby_at` |
| p2 order [12, 10] | `12 != 10 : lead depends on arrival order [12, 10]` |
| p3 min_confidence 80 | `None != 2 : row snapshot has no owed nearby_at` |
| p4 far twin | `None != 2 : line-30 copy not stamped` (pass 2, the first of the p4 assertions to fail; the pass-3 line-10 assertions sit after it) |
| in01 | `'nearby_at' unexpectedly found in {... 'nearby_at': 2}` |
| defer (D-20) | `unexpectedly None : record 845f88b7 is not an open record (decision orphaned)` |

Green on HEAD (`-rA`): test_q1_control_carried_copy_leads, test_q3_controls_scored_twin_and_no_rereport, test_dismissed_covered_member_below_threshold_may_drop. pytest-subtests also reports the p2 parent as PASSED; its two subtests are the SUBFAILED entries above.

### Task 2: `pytest -q test_decision_continuity.py -k TestLeadOrderInvariance -rfE --tb=line` (tree at 9fe0e0f's predecessor edit, same scorer)

```
=========================== short test summary info ============================
SUBFAILED(scenario='different_line_same_hash_cross_lane', lead='fresh-leads-same-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='same_lane_arrival_order', lead='carried-leads') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='same_lane_arrival_order', lead='fresh-leads-reversed-arrival') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='min_confidence_dropped_twin', lead='fresh-leads-twin-dropped') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
4 failed, 2 passed, 69 deselected, 19 subtests passed in 0.08s
```

Failing assertions (verbatim):
- different_line_same_hash_cross_lane/fresh-leads-same-band: `Tuples differ: ('current', None, False) != ('stale', 'nearby', True)`, row snapshot `{'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}`
- same_lane_arrival_order/carried-leads: `Tuples differ: ('current', None, False) != ('stale', 'nearby', True)`, row snapshot at line 10, no nearby_at
- same_lane_arrival_order/fresh-leads-reversed-arrival: `12 != 10 : same_lane_arrival_order/fresh-leads-reversed-arrival did not permute the lead` (marker self-check: the lead follows arrival order)
- min_confidence_dropped_twin/fresh-leads-twin-dropped: `Tuples differ: ('current', None, False) != ('stale', 'nearby', True)`, row snapshot `{'at_pass': 2, ..., 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}`

All subtests of the six pre-existing scenarios, the new scenarios' other permutations, and test_guard_covers_every_scenario_the_phase_cares_about pass.

## What each fixture drives

All through the real chain (score.run -> append_pass -> carry_state decision_state / stale_cause / finalize_counts -> e2e_gate, plus batch_card where a card row is asserted); findings built only via `fresh()`; no forged status, snapshot or kept-open rows.

- `same_hash_lines()`: base file with lines 10 and 12 both `return None`.
- `cross_lane_same_hash_scenario(sec_conf)`: bugs A at 12 dismissed; security reports the same title at 10; diff [[17,17]] (inside 12's D-14 window only). p1 at conf 100 (security leads at 10), q1 control at 60 (bugs leads at 12).
- `arrival_order_scenario(order)`: bugs re-reports at 10 and 12 at conf 100 in the given arrival order; p2 requires a line-10 lead and the re-ask in both orders.
- `min_conf_twin_scenario(min_confidence, rereport)`: line 12 edited; the re-report at 95 with `min_confidence` 80 drops the carried twin before grouping (p3). Controls q3: no min_confidence key (absent, not null), and min_confidence 80 with no re-report (kept-open row).
- `edited_carried_lead_scenario()`: conf 90 lead owes nearby_at 2 after pass 2; pass 3 edits its own line on a quiet diff; the re-hashed needs-recheck row must not carry nearby_at (in01).
- `far_twin_scenario()`: lines 10 and 30 both `return None`; pass 2 fresh conf-100 copy at 30 with diff [[33,33]]; pass 3 quiet. p4 checks two rows of one hash on pass 2 and 3, the line-30 stamp, and that carry_state's first (line-10) record carries the stamp and re-asks.
- `deferred_covered_sub_threshold_scenario(kind)`: the low_entropy_split shape at conf 75. defer: the `}` member must stay open (kept_open sub-threshold, stale/nearby, covered by hB, outstanding, gate blocks, card row). dismiss: drops (findings [], filtered sub-threshold at line 10/TITLE_A, no record, outstanding_cw 0, gate write).
- Harness: `target_deferred()` / `_deferred_read()` and `run_pass` adding `deferred_hashes` only when passes exist and `carry_state.deferred` returns a list. Absent on today's tree, so every existing envelope is unchanged. Note for 57-22: once `carry_state.deferred` lands, every run_pass call site (every defer fixture, the owner journey included) gets the key; run the whole module and record any flip.
- Invariance: `_inv_different_line_same_hash_cross_lane`, `_inv_same_lane_arrival_order`, `_inv_min_confidence_dropped_twin`; loop now `for label, knobs, marker in perms` / `build(*knobs)`; existing six entries' knobs unchanged.

## No-weakening greps

- `pytest -q test_decision_continuity.py -k "not TestPooledEvidence and not TestPriorGate and not TestDeferredStaysOpen"` after Task 1: `62 passed, 9 deselected, 76 subtests passed` (62 before this plan).
- `pytest -q test_decision_continuity.py -k "not TestLeadOrderInvariance and not TestPooledEvidence and not TestPriorGate and not TestDeferredStaysOpen"` after Task 2: `60 passed, 11 deselected, 60 subtests passed`.
- `pytest -q test_score.py -k "TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup"`: `23 passed, 477 deselected, 24 subtests passed`.
- Task 1 diff: `grep -c '^-.*assert'` = 0, `grep -c '^-\s*def '` = 0.
- Task 2 diff removed lines (complete list): the two-line table comment (`build(conf, severity)` / `(label, (conf, severity), ...)`), the loop header `for label, (conf, sev), marker in perms:`, the call `state, hA, got_marker = build(conf, sev)`, and the closing line `"different_lane_dup_57_04"})` of the coverage-lock set. `grep '^-.*assert'` matched 0 lines (the plan expected 1; the six-name set's `assertEqual(` line itself was not touched, only its closing line was extended).
- Coverage lock, the only edit to an existing test: before `{plain, inherited_split, absorbed_split, owed_quiet_same_lane, owed_quiet_different_lane, different_lane_dup_57_04}`; after the same six plus `{different_line_same_hash_cross_lane, same_lane_arrival_order, min_confidence_dropped_twin}`. LEAD_PERMUTATIONS length 3 / STABLE_CONF first / first label carried-leads / >= 2 permutations are still asserted.
- `git diff --quiet -- score.py carry_state.py`: exit 0 (untouched). Only the test file was committed (.planning/HANDOFF.json and STATE.md were already modified before this plan and are not in the task commits).
- Full module after both tasks: `11 failed, 66 passed, 79 subtests passed` (the 11 are exactly the reds above).

## Deviations from Plan

**1. [Rule 3 - Blocking] `far_twin_scenario` reads pass-3 rows from the state**
- **Found during:** Task 1
- **Issue:** The plan's signature `(s2, r2, s3, hA)` has no r3, but p4 asserts two pass-3 rows.
- **Fix:** Kept the planned signature and read the rows from `s3["passes"][-1]["findings"]` (the same rows append_pass stores from the result).
- **Cost if wrong:** none; the rows are identical objects of the score result.
- **Commit:** 1ff95f1

**2. [Rule 3 - Blocking] `build(*knobs)` grep count**
- **Found during:** Task 2
- **Issue:** The updated table comment also contained `build(*knobs)`, making the acceptance grep 2 instead of 1.
- **Fix:** Reworded the comment to `build(<knobs unpacked>)`.
- **Cost if wrong:** none (comment only).
- **Commit:** 9fe0e0f

**3. `^-.*assert` count is 0, not the expected 1** (see No-weakening greps). Stricter than planned; no assertion text was removed.

**4. Helper `_deferred_read()` added** beside `target_deferred()` so run_pass can tell "read missing" (None) from "empty list". Counted inside the planned target_deferred harness read.

## Known Stubs

None.

## Self-Check: PASSED
- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (3 new classes, 7 new defs)
- FOUND: 1ff95f1, 9fe0e0f
