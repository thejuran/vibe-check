---
phase: 57-decision-continuity-within-closure
plan: 17
subsystem: decision continuity fixtures (third gap closure, reproduce-first)
tags: [reproduce-first, fixtures, same-lane-rereport, lead-order-invariance, nearby-at, real-chain, gap-closure]
requires:
  - phase: 57-16
    provides: second-round gate (suite 3259 green at HEAD), real-chain harness in test_decision_continuity.py
provides:
  - "TestSameLaneRereport: 5 real-chain RED fixtures (a, a2, b, c, d) + 1 green control for the same-lane re-report (CR-01 / SA-01)"
  - "TestLeadOrderInvariance: 6 scenarios x lead permutations; 8 SUBFAILED on HEAD, every carried-leads baseline green"
  - "plain_rereport_scenario, owed_quiet_rereport_scenario; split_scenario / absorbed_split_scenario rereport= knob (default None unchanged)"
  - "Verbatim red runs for the 57-19 ledger"
affects: [57-18 (score.py fix must turn these green), 57-19 (gate ledger cites this red run)]
tech-stack:
  added: []
  patterns: ["lead-order invariance: permute which record leads, self-check the permutation, assert the decision triple is identical"]
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-17-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
key-decisions:
  - "The higher-band re-report is (conf 100, critical), not (conf 90, critical): on HEAD conf 90/critical leads the row but stays band warning, so it would not exercise a band rise"
  - "different_lane_dup_57_04 and owed_quiet_different_lane run two permutations, not three: a higher band would change the row shape (C loses the lead / a lane-backed D-05 rise)"
duration: 25min
completed: 2026-10-27
requirements: [DECN-03]
---

# Phase 57 Plan 17: Same-lane re-report reproduction + lead-order invariance guard Summary

**Five real-chain fixtures and eight invariance subtests now fail on the unfixed scorer. Each failure is the same silent wrong-keep: when a decided finding's own lane reports it again at a score that beats the carried copy, the fresh copy leads the row, the `nearby_at` stamp is lost, and the gate writes. The conf-75 control and every carried-leads baseline stay green. Production code was not touched.**

## Red run (HEAD, pre-fix)

HEAD for both runs is the plan base b458cc6 plus this plan's test-only commits. score.py and carry_state.py are unchanged from 70346c2.

### TestSameLaneRereport

`pytest -q test_decision_continuity.py -k TestSameLaneRereport -rfE --tb=line`. The `/opt/homebrew/.../unittest/case.py:878:` echo lines are omitted. Each one repeats the E line above it.

```
FFFF.F                                                                   [100%]
=================================== FAILURES ===================================
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'critical'}
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 3 : re-reported split row snapshot has no nearby_at: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
=========================== short test summary info ============================
FAILED test_decision_continuity.py::TestSameLaneRereport::test_a2_plain_row_rereported_by_own_lane_at_higher_band
FAILED test_decision_continuity.py::TestSameLaneRereport::test_a_plain_row_rereported_by_own_lane_at_conf_100
FAILED test_decision_continuity.py::TestSameLaneRereport::test_b_inherited_split_led_by_own_lane_rereport
FAILED test_decision_continuity.py::TestSameLaneRereport::test_c_own_decision_absorbed_split_led_by_own_lane_rereport
FAILED test_decision_continuity.py::TestSameLaneRereport::test_d_owed_stamp_survives_own_lane_rereport_on_quiet_pass
5 failed, 1 passed, 48 deselected in 0.03s
```

The first failure for each test is at `nearby_at`. The failures print in this order: a2, a, b, c, d. The passing test is `test_control_carried_copy_leads_at_conf_75`. Plan verify: `tail -1 | grep -Ec "^5 failed, 1 passed"` printed `1`.

### TestLeadOrderInvariance

`pytest -q test_decision_continuity.py -k TestLeadOrderInvariance -rfE --tb=line`, with the same echo lines omitted:

```
..                                                       [100%]
=================================== FAILURES ===================================
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : plain/fresh-leads-same-band: outcome depends on which record leads; row snapshot {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : plain/fresh-leads-higher-band: outcome depends on which record leads; row snapshot {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'critical'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : inherited_split/fresh-leads-same-band: outcome depends on which record leads; row snapshot {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : inherited_split/fresh-leads-higher-band: outcome depends on which record leads; row snapshot {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'critical'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : absorbed_split/fresh-leads-same-band: outcome depends on which record leads; row snapshot {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : absorbed_split/fresh-leads-higher-band: outcome depends on which record leads; row snapshot {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'critical'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : owed_quiet_same_lane/fresh-leads-same-band: outcome depends on which record leads; row snapshot {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)
    + ('stale', 'nearby', True) : owed_quiet_same_lane/fresh-leads-higher-band: outcome depends on which record leads; row snapshot {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'critical'}
=========================== short test summary info ============================
SUBFAILED(scenario='plain', lead='fresh-leads-same-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='plain', lead='fresh-leads-higher-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='inherited_split', lead='fresh-leads-same-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='inherited_split', lead='fresh-leads-higher-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='absorbed_split', lead='fresh-leads-same-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='absorbed_split', lead='fresh-leads-higher-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='owed_quiet_same_lane', lead='fresh-leads-same-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
SUBFAILED(scenario='owed_quiet_same_lane', lead='fresh-leads-higher-band') test_decision_continuity.py::TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads
8 failed, 2 passed, 54 deselected, 8 subtests passed in 0.04s
```

The excerpt keeps each failure's first and last diff lines and drops the identical `First differing element 0: 'current' 'stale'` / `- ('current', None, False)` lines between them. There are 8 SUBFAILED, every fresh-leads permutation of the four same-lane scenarios. These 8 subtests passed:
- the six carried-leads baselines
- `owed_quiet_different_lane/fresh-leads-same-band` (already fixed by 57-07)
- `different_lane_dup_57_04/fresh-leads-same-band` (already fixed by 57-04)

`test_guard_covers_every_scenario_the_phase_cares_about` passes. pytest-subtests also counts the parent test as "passed", which is why the line says `2 passed`. Plan verify `grep -Ec "SUBFAIL|failed"` printed `9`.

### Full suite (HEAD a9e6f7a, includes test_replay.py)

`pytest -q` from plugins/vibe-check/scripts: **`13 failed, 3262 passed, 4320 subtests passed in 169.32s`**. The 13 failures are exactly the 5 TestSameLaneRereport reds plus the 8 SUBFAILED above. 3262 = 3259 (prior HEAD) + the control + the coverage test + the invariance parent test. No pre-existing test failed.

## What each fixture drives

All of these run the real chain: score.run -> append_pass -> carry_state decision_state / stale_cause / finalize_counts -> e2e_gate / batch_card. Fresh findings are built only through `fresh()`, so they never carry a status or snapshot.

| Fixture | Shape | Lead self-check | Expectation |
|---|---|---|---|
| test_a | plain row; pass 2 edits line 12 (inside A's D-14 window); `bugs` A re-reported at conf 100 / warning | status `new`, agent bugs, 1 member (twin deduped) | nearby_at 2, at_pass 2, stale/nearby, outstanding, gate != write, card cause nearby |
| test_a2 | same; re-report at conf 100 / critical (band rises to critical) | status `new`, band critical | same, cause still nearby (same-lane rise not lane-backed, D-05) |
| test_b | split_scenario(real_diff=True, rereport=(100, warning)) | status `new`, hB resolved | nearby_at 2, stale/nearby, covering_decision == hB, outstanding, gate, card |
| test_c | absorbed_split_scenario(rereport=(100, warning)) | pass 2 absorbed_into hB and current; pass 3 status `new` | nearby_at 3, absorbed_into None, stale/nearby, outstanding, gate |
| test_d | owed_quiet_rereport_scenario(100, warning): owed nearby_at 2, then quiet pass 3 with a same-lane re-report | pass 2 cause nearby; pass 3 status `new` | nearby_at 2 and at_pass 2 kept, stale/nearby, outstanding, gate |
| control | plain at conf 75 | status `persisted` | stale/nearby re-ask (green on HEAD) |
| TestLeadOrderInvariance | 6 scenarios x permutations | status (same lane), agent (different lane), or (C leads, kept A member conf) for 57-04 | triple identical across permutations; ("stale", "nearby", True) for 5 scenarios; for 57-04, equal to its carried-leads baseline and never None |

The guard is not decorative. Each permutation checks that the lead really moved: a fresh-leads permutation that stopped permuting would fail on its marker. The guard is red on HEAD, and every carried-leads baseline is green.

## No-weakening greps

- `pytest -q test_decision_continuity.py -k "not TestSameLaneRereport and not TestLeadOrderInvariance"` -> `48 passed, 8 deselected, 60 subtests passed`
- `git diff b458cc6 -U0 -- test_decision_continuity.py | grep -c '^-.*assert'` -> 0 (checked after each task: 0 and 0)
- `grep -c '^-\s*def '` on the Task 1 diff -> 2. These are the two changed signatures, `split_scenario(..., rereport=None)` and `absorbed_split_scenario(..., rereport=None)`. Both lines are replaced, not deleted, and no test def was removed. `rereport=None` reproduces the previous inputs byte-for-byte (the split pass still sends `[]`).
- `git diff --name-only` (code) -> only `plugins/vibe-check/scripts/test_decision_continuity.py`. score.py and carry_state.py are untouched. `.planning/HANDOFF.json` was modified before this plan started and was left alone.
- Acceptance greps: `class TestSameLaneRereport` 1; `def plain_rereport_scenario|def owed_quiet_rereport_scenario` 2; `rereport=None` 2; `class TestLeadOrderInvariance` 1; `INVARIANCE_SCENARIOS\b` 4; `LEAD_PERMUTATIONS` 6.

## Task Commits

1. **Task 1: RED same-lane re-report fixtures + control**: `cedc7a1` (test)
2. **Task 2: lead-order invariance guard**: `a9e6f7a` (test)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Fixture input] The higher-band re-report uses conf 100 / critical, not conf 90 / critical**
- **Found during:** Task 1 (probe before writing a2)
- **Issue:** The plan's a2 expects "the row band is now critical". On HEAD, conf 90 / critical does take the lead (status `new`, nearby_at dropped), but the band stays `warning`. With those inputs a2 would have duplicated test_a and never exercised a band rise.
- **Fix:** a2 is now `test_a2_plain_row_rereported_by_own_lane_at_higher_band` with input (100, "critical"). It asserts band `critical` as a fixture self-check, which keeps the plan's assertion meaning. `LEAD_PERMUTATIONS`' fresh-leads-higher-band entry is (100, "critical") for the same reason, and its row snapshots show band `critical`.
- **Cost if wrong:** conf 90 / critical (a severity-only rise that keeps the band) is no longer pinned by its own fixture. It hits the same lead path as test_a, so 57-18's fix would cover it, but nothing locks that.
- **Files modified:** test_decision_continuity.py
- **Commit:** cedc7a1

**2. [Rule 1 - Fixture shape] different_lane_dup_57_04 runs two permutations instead of three**
- **Found during:** Task 2 (probe)
- **Issue:** At (100, critical), the fresh `bugs` A duplicate takes the row's lead from C. The shape becomes D-08's joined row (`stale`/`joined`, covered by TestRegrouping r4), so it is no longer the 57-04 shape. Its self-check (C leads) would fail, and the triple would differ for a reason that is not this guard's subject.
- **Fix:** The scenario uses `LEAD_PERMUTATIONS[0]` and `[1]`. The lead marker is (C leads, the kept A member's `agent_confidence`): 60 means the carried A was kept, 100 means the fresh duplicate won. The coverage test still requires every scenario to start with carried-leads and to have at least 2 permutations.
- **Cost if wrong:** None on HEAD. If a later change makes the joined-row reopen depend on the lead, this guard would not see it. r4 locks that contract instead.
- **Files modified:** test_decision_continuity.py
- **Commit:** a9e6f7a

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** "(90, critical) -> ... (DEFECT; band critical)". **Actual:** band `warning` at (90, critical) and `critical` at (100, critical) and (95, critical). **Why:** the conf-90 score stays below the critical band floor. **Cost if wrong:** low. Deviation 1 keeps the band-rise coverage.
- **Found during:** Task 2. **Planned:** the behavior bullet lists "same_lane_dup" among the HEAD-failing scenarios. **Actual:** the scenario table has no separate same-lane dup. The `plain` scenario is the same-lane duplicate (the twin is deduped into the lead's own ref). **Cost if wrong:** none. The plan's own six-name table is implemented exactly.

## Issues Encountered

None.

## Known Stubs

None.

## Next Phase Readiness

57-18 may change score.py only against these reds. When it lands, TestSameLaneRereport should read 6 passed, TestLeadOrderInvariance should have 0 SUBFAILED, and the full suite should be 0 failed. Phase 57 is not complete, and DECN-03 stays unchecked.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py
- FOUND: commits cedc7a1, a9e6f7a
