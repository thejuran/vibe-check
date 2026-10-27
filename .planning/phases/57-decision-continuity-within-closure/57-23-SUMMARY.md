---
phase: 57-decision-continuity-within-closure
plan: 23
subsystem: phase gate (decision continuity, final round)
tags: [phase-gate, ledger, replay, full-suite, requirements, d-19-hard-stop, gap-closure]
requires: ["57-22"]
provides:
  - Verbatim green gates at the final fourth-round code commit (full suite, test_replay, golden, import sets, replay candidate, replay diff)
  - Reverse-run ledger proving every 57-20 red at the pre-fix tree and green at the post-fix tree
  - DECN-03 re-marked complete on that evidence; DECN-02 traceability names D-20
  - D-19 hard stop written into STATE.md's first next step and into deferred-items.md
  - The open D-20 min_confidence edge reproduced and recorded for an owner ruling
affects: [phase-57 code review, phase-57 re-verification]
tech-stack:
  added: []
  patterns: [plugins-only git archive reverse-run, replay diff with zero allowances]
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-23-SUMMARY.md
  modified:
    - .planning/phases/57-decision-continuity-within-closure/deferred-items.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
decisions:
  - "57-23: DECN-03 re-marked complete on the 57-23 gate (all gates green, replay 0 differing, ledger matches 57-20's reds)"
  - "57-23: no ALLOWANCES-phase57-pooled.json — replay diff vs rev:24c0c00 had 0 differing runs"
  - "57-23: the D-20 min_confidence edge (deferred covered member removed by min_confidence still drops) is reproduced but not fixed; it is recorded as an open edge for the owner to rule on (fix as a silent-finding-loss class, or park as 999.x)"
metrics:
  duration: ~20min
  completed: 2026-10-27
  tasks: 2
  files: 4
---

# Phase 57 Plan 23: Final-round gate (D-19 hard stop) Summary

Every gate is green at the final fourth-round code commit. Full suite: 3311 passed, 0 failed, 0 SUBFAILED. Replay diff against rev:24c0c00: 0 of 170 runs differ, so no allowances file. Every red that 57-20 recorded fails on the pre-fix tree and passes on the post-fix tree. On that evidence DECN-03 is complete again. The owner's D-19 hard stop is now the first operator step: no fifth structural round. One D-20 edge is still open: a deferred finding that the opt-in min_confidence filter removes (rather than the threshold). It is reproduced and recorded below for the owner to rule on; it is not fixed here.

## Gates (verbatim)

**Range check.**
- PRE = 8a0563a, 57-20's last commit (a docs commit; its plugin files are identical to 9fe0e0f). POST = 92b135d, 57-22's last code commit.
- `git log --oneline 9fe0e0f..HEAD` lists only 57-20, 57-21 and 57-22 commits:
```
33a951e docs(57-22): complete D-20 deferred-stays-open plan
92b135d feat(57-22): keep a deferred covered member open below threshold
6626edb feat(57-22): bind $DEFERRED_HASHES fail-closed and forward deferred_hashes
70e0719 feat(57-22): carry_state deferred read lists the owner's deferrals
f5a71cf docs(57-21): complete pooled carried evidence plan
333a5cd test(57-21): re-anchor the 57-18 mutants and lock every pooled-evidence guard
1ff5702 feat(57-21): pool carried evidence from an index built before every filter
8a0563a docs(57-20): complete reproduce-first RED fixtures plan
```
- `git diff --name-only 9fe0e0f HEAD -- plugins/` lists the seven files the plan expects, plus **test_score.py**:
  - 05-state.md, 30-collect-score.md, carry_state.py, score.py
  - test_carry_state.py, test_decision_continuity.py, test_nv_render.py
  - test_score.py (not in either plan's file list):
    - 57-21 changed two fixtures: the m57-06 forge now carries the row hash, and the TestSnapshot keep fixture stores its real hash.
    - 57-22 re-anchored the m57-04 mutant.
  - All three are recorded as deviations in 57-21-SUMMARY.md and 57-22-SUMMARY.md. None of them removes an assertion.
- `git diff --quiet 92b135d HEAD -- plugins` exited 0, so running at HEAD 33a951e is the same as running at POST. `git diff --quiet 8665faf 451e84c -- plugins/` exited 0.
- Every command below ran from `plugins/vibe-check/scripts` at HEAD.

Full suite (`pytest -q`, tail; `grep -cE "FAILED|SUBFAILED|failed"` on the full output printed `0`):
```
3311 passed, 4381 subtests passed in 197.25s (0:03:17)
```
3311 = 3273 (the 57-19 gate) + 38 new tests:
- **57-20 (9):**
  - TestPooledEvidence: `test_p1_cross_lane_same_hash_other_line_nearby_reasks`, `test_p2_same_lane_arrival_order_does_not_pick_the_outcome`, `test_p3_min_confidence_dropped_twin_keeps_the_reask`, `test_p4_far_twin_latest_stamp_reaches_the_first_copy`, `test_q1_control_carried_copy_leads`, `test_q3_controls_scored_twin_and_no_rereport`
  - `TestPriorGate::test_in01_edited_carried_lead_does_not_carry_its_stamp_onto_the_new_hash`
  - TestDeferredStaysOpen: `test_deferred_covered_member_below_threshold_stays_open`, `test_dismissed_covered_member_below_threshold_may_drop`
  - The invariance guard was widened inside existing tests, so it adds no new def.
- **57-21 (9, net):**
  - TestPhase57Mutants: `test_nearby_judged_at_the_lead_only_loses_the_other_copy`, `test_line_tie_break_dropped_makes_the_lead_arrival_dependent`, `test_prior_rank_first_wins_loses_the_latest_stamp`
  - TestPooledPriorUnit (6): `test_no_candidates_is_none`, `test_stamped_snapshot_wins_over_an_unstamped_older_one`, `test_equal_stamps_take_the_oldest_at_pass`, `test_later_stamp_wins_over_an_earlier_one`, `test_non_int_nearby_at_ranks_after_a_stamped_one`, `test_prior_rank_never_raises`
  - `test_index_read_after_filtering_loses_the_dropped_twin` replaces a renamed test, so it nets 0.
- **57-22 (20):**
  - test_carry_state.py TestDeferred (7): `test_deferred_lists_current_and_stale_defers`, `test_deferred_excludes_dismiss`, `test_deferred_legacy_record_without_evidence_listed`, `test_deferred_empty_when_no_decisions`, `test_deferred_malformed_state_is_none`, `test_deferred_does_not_mutate_state`, `test_cli_deferred_round_trip`
  - test_nv_render.py (7): `test_deferred_binding_holds`, `test_deferred_binding_one_helper_call`, `test_envelope_deferred_holds`, `test_deferred_binding_deleting_mutant`, `test_deferred_binding_in_bullet_deleting_mutant`, `test_deferred_binding_empty_on_failure_inserting_mutant`, `test_envelope_deferred_in_bullet_deleting_mutant`
  - test_decision_continuity.py (6): `test_deferred_kept_open_row_shape`, `test_deferred_kept_open_row_persists_on_the_next_pass`, `test_envelope_without_deferred_hashes_scores_as_before`, `test_deferral_kind_gate_keeps_a_dismissed_member_open`, `test_no_synthesized_entry_drops_the_deferred_member`, `test_kept_open_covered_row_without_carried_is_not_stamped`

This matches the orchestrator's independent counts: 3290 passed / 1 failed after 57-21, then 3311 / 0 after 57-22.

test_replay.py was collected (`pytest -q test_replay.py`):
```
64 passed, 10 subtests passed in 15.15s
```
The plan's verify command (`pytest -q test_replay.py 2>&1 | tail -1 | grep -Ec "^(6[4-9]|[7-9][0-9]) passed"`) printed `1`.

Golden:
```
golden ok
```

Import sets:
```
pytest -q test_score.py -k ImportSet       -> 3 passed, 497 deselected in 0.10s
pytest -q test_carry_state.py -k ImportSet -> 3 passed, 223 deselected in 0.07s
```

Replay candidate (`python3 replay.py candidate --name phase57-pooled-gate --scorer rev:HEAD --out $SP/phase57-pooled-gate-candidate.md`, exit 0):
```
- candidate scorer: rev:HEAD
- candidate scorer sha256: 3504d2da79e9ebab26bfedd01c7614c9b7cc06ade99c12b7e24e90003edd22fb
- HEAD: 33a951e22fc34521d8f9d660019a474e31baccfb
REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1
kept 25 / protected 26

REGRESSED 0

UNEVALUABLE 0

AMENDED 1
```
The AMENDED run is the pre-existing `runs/triggarr-secret-in-logs/run-2` (axis-false, ledger entry 008).

Replay diff (`python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SP/phase57-pooled-gate-diff.md`, exit 0):
```
- base: rev:24c0c00 (sha256 ea6b041779c626b40607d4ba65ee0cc1c9522d2bd0c7cdd8995be4969768c233)
- candidate: rev:HEAD (sha256 3504d2da79e9ebab26bfedd01c7614c9b7cc06ade99c12b7e24e90003edd22fb)
- roots: all (7 roots)
- allowances: ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json
- runs compared: 170
- runs differing: 0
- runs differing (allowed): 0
- runs with unallowed differences: 0
- allowances unused: 65

## Differences

- none
```
`.changes.json`: `{"allow": []}`.

## Replay disposition

No run differed, so none was unallowed, and `docs/design/b3-ground-truth/ALLOWANCES-phase57-pooled.json` was **not** created (`ls` reports "No such file or directory"). That matches 57-11, 57-13, 57-16 and 57-19. Not one of the 170 recorded runs changed: no status, band, score, title, row count, members, kept_open row, filtered entry, nv_dropped_weak or snapshot field moved. This is expected:
- No archived envelope carries `deferred_hashes`, so 57-22's keep-open never fires on them.
- None of them has the multi-copy carried shapes that 57-21's pooling changes.

## Blocked by the holdout barrier

No gate command was blocked. Two diagnostic one-liners were blocked while I gathered the ledger. Both were output-filtering pipelines run inside `$SP/pre-fix`, with no `docs` path. The hook message, verbatim, both times:
```
PreToolUse:Bash hook error: [python3 /Users/julianamacbook/turingmind-code-review/docs/design/holdout-v2.12/tools/holdout_guard.py hook]: Blocked: this tool call reaches the sealed holdout folder (v2.12 barrier).
```
Both commands ended in a `sed 's/ - .*//'` filter, which the guard appears to match. I did not retry them. I re-ran the same pytest selections without that `sed` filter, and those runs are the ones recorded below. Nothing was lost: the blocked commands only reformatted pytest output.

**Holdout attestation.**
- Both scratch trees came from `git archive <rev> plugins/vibe-check`, with that pathspec only. Each extracted tree's top level was `plugins` and nothing else (`pre-fix top: plugins`, `post-fix top: plugins`).
- I used no `docs` pathspec, no whole-tree archive, no `git worktree` and no `GIT_DIR` override.
- `docs/design/holdout-v2.12` was never extracted, copied, listed or read.
- The only `docs/` paths touched were the replay inputs that replay.py reads itself (the manifest and `ALLOWANCES-phase53-nv.json` through `--allow`), plus one `ls` of the would-be `ALLOWANCES-phase57-pooled.json` to confirm it does not exist.
- Both scratch trees were deleted afterwards: `ls $SP | grep -E '^(pre-fix|post-fix)$'` printed nothing, and the check echoed "no pre-fix/post-fix in scratchpad".

## Reverse-run ledger

**Method.** Each tree came from `git archive <rev> plugins/vibe-check | tar -x`. The FINAL test_decision_continuity.py, test_score.py, test_carry_state.py and test_nv_render.py were copied over each tree, and every selection ran with `-p no:cacheprovider`. Each tree keeps its own production files and its own prose (05-state.md, 30-collect-score.md).

The PRE production tree is the reviewed tree (`cmp` against `git show 451e84c:plugins/vibe-check/scripts/<file>`):
```
score.py pre-fix == 451e84c
score.py post-fix DIFFERS from 451e84c
carry_state.py pre-fix == 451e84c
carry_state.py post-fix DIFFERS from 451e84c
```

**Selection 1:** `pytest -q -rfE --tb=line -p no:cacheprovider test_decision_continuity.py -k "TestPooledEvidence or TestPriorGate or TestDeferredStaysOpen or TestLeadOrderInvariance or TestSameLaneRereport or TestWr01Guards or TestSplitPassNearby or TestPhase57Mutants or TestPooledPriorUnit"`

PRE 8a0563a. I elided the `unittest/case.py` echo lines, the repeated tuple-diff bodies and the AttributeError path lines:
```
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}
E   AssertionError: 12 != 10 : lead depends on arrival order [12, 10]; row {'at_pass': 2, 'file': 'src/a.py', 'line': 12, 'canonical_line_content': 'return None', 'band': 'warning', 'nearby_at': 2}
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : line-30 copy not stamped: {'at_pass': 2, 'file': 'src/a.py', 'line': 30, 'canonical_line_content': 'return None', 'band': 'warning'}
E   AssertionError: 'nearby_at' unexpectedly found in {'at_pass': 3, ... 'nearby_at': 2} : edited finding inherited a foreign stamp: {...}
E   AssertionError: unexpectedly None : record 845f88b7 is not an open record (decision orphaned)
E   AssertionError: unexpectedly None : record 845f88b7 is not an open record (decision orphaned)
E   AssertionError: Lists differ: [] != ['845f88b7a682237a895e6301fee79e5fb6caf36c2a9954956d42d4faadeb4ae7']
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)  ... different_line_same_hash_cross_lane/fresh-leads-same-band
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)  ... same_lane_arrival_order/carried-leads
E   AssertionError: 12 != 10 : same_lane_arrival_order/fresh-leads-reversed-arrival did not permute the lead; row {... 'line': 12 ... 'nearby_at': 2}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)  ... min_confidence_dropped_twin/fresh-leads-twin-dropped
E   AssertionError: 0 != 1 : mutation target not unique
E   AssertionError: Items in the first set but not the second:
    'test_p4_' 'test_deferred_' 'test_p1_' 'test_p3_' 'test_in01_' 'test_p2_'
E   AssertionError: 0 != 1 : mutation target not unique      (x9 more)
E   AttributeError: module 'score' has no attribute '_pooled_prior'   (x5)
E   AttributeError: module 'score' has no attribute '_prior_rank'     (x5)
=========================== short test summary info ============================
FAILED TestPooledEvidence::test_p1_cross_lane_same_hash_other_line_nearby_reasks
SUBFAILED(order=[10, 12]) TestPooledEvidence::test_p2_same_lane_arrival_order_does_not_pick_the_outcome
SUBFAILED(order=[12, 10]) TestPooledEvidence::test_p2_same_lane_arrival_order_does_not_pick_the_outcome
FAILED TestPooledEvidence::test_p3_min_confidence_dropped_twin_keeps_the_reask
FAILED TestPooledEvidence::test_p4_far_twin_latest_stamp_reaches_the_first_copy
FAILED TestPriorGate::test_in01_edited_carried_lead_does_not_carry_its_stamp_onto_the_new_hash
FAILED TestDeferredStaysOpen::test_deferred_covered_member_below_threshold_stays_open
FAILED TestDeferredStaysOpen::test_deferred_kept_open_row_persists_on_the_next_pass
FAILED TestDeferredStaysOpen::test_deferred_kept_open_row_shape
SUBFAILED(scenario='different_line_same_hash_cross_lane', lead='fresh-leads-same-band') TestLeadOrderInvariance::...
SUBFAILED(scenario='same_lane_arrival_order', lead='carried-leads') TestLeadOrderInvariance::...
SUBFAILED(scenario='same_lane_arrival_order', lead='fresh-leads-reversed-arrival') TestLeadOrderInvariance::...
SUBFAILED(scenario='min_confidence_dropped_twin', lead='fresh-leads-twin-dropped') TestLeadOrderInvariance::...
FAILED TestPhase57Mutants::test_carried_from_lead_only_loses_the_same_lane_rereport
FAILED TestPhase57Mutants::test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split
FAILED TestPhase57Mutants::test_deferral_kind_gate_keeps_a_dismissed_member_open
FAILED TestPhase57Mutants::test_index_read_after_filtering_loses_the_dropped_twin
FAILED TestPhase57Mutants::test_kept_open_covered_row_without_carried_is_not_stamped
FAILED TestPhase57Mutants::test_line_tie_break_dropped_makes_the_lead_arrival_dependent
FAILED TestPhase57Mutants::test_nearby_judged_at_the_lead_only_loses_the_other_copy
FAILED TestPhase57Mutants::test_no_synthesized_entry_drops_the_deferred_member
FAILED TestPhase57Mutants::test_prior_rank_first_wins_loses_the_latest_stamp
FAILED TestPhase57Mutants::test_seed_without_hash_equality_inherits_a_foreign_stamp
FAILED TestPhase57Mutants::test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp
FAILED TestPooledPriorUnit::test_equal_stamps_take_the_oldest_at_pass
FAILED TestPooledPriorUnit::test_later_stamp_wins_over_an_earlier_one
FAILED TestPooledPriorUnit::test_no_candidates_is_none
FAILED TestPooledPriorUnit::test_non_int_nearby_at_ranks_after_a_stamped_one
SUBFAILED(snap={}) / (snap={'at_pass': 'x', 'nearby_at': None}) / (snap={'at_pass': 1.5, 'nearby_at': True}) / (snap=None) / (snap=[]) TestPooledPriorUnit::test_prior_rank_never_raises
FAILED TestPooledPriorUnit::test_stamped_snapshot_wins_over_an_unstamped_older_one
34 failed, 24 passed, 39 deselected, 19 subtests passed in 0.46s
```
PRE passing tests (`-rA`):
- TestSplitPassNearby s1-s4
- TestSameLaneRereport a, a2, b, c, d and control
- TestWr01Guards w1 and w2
- TestPooledEvidence q1 and q3; the p2 parent (its subtests are SUBFAILED)
- TestDeferredStaysOpen: the dismiss lock and test_envelope_without_deferred_hashes_scores_as_before
- TestLeadOrderInvariance: both tests (parents)
- The four older mutants: decided_read_returning_empty, nearby_window_lower/upper_bound, split_pass_carried_arm_dropped
- TestPooledPriorUnit::test_prior_rank_never_raises (parent; its subtests are SUBFAILED)

POST 92b135d:
```
47 passed, 39 deselected, 30 subtests passed in 0.77s
```

**Selection 2:** `pytest -q -p no:cacheprovider test_carry_state.py -k "TestDeferred or test_cli"`
```
PRE : 26 failed, 17 passed, 203 deselected, 58 subtests passed in 2.43s
POST: 23 passed, 203 deselected, 78 subtests passed in 2.78s
```
- PRE failures:
  - The six TestDeferred tests fail with `AttributeError: module 'carry_state' has no attribute 'deferred'`.
  - `test_deferred_malformed_state_is_none` gives 10 SUBFAILED.
  - The CLI malformed-states loop gives 10 SUBFAILED on its `sub='deferred'` cases. The usage message has no `deferred` subcommand at PRE: `AssertionError: 'usage: carry_state.py finalize-counts [--head-blobs PATH] | pending | decided | ...' not found in [...]`.
  - The CLI round trip fails with `2 != 0 : usage: ...`.
- This is expected: 57-22 added `deferred` to those CLI loops.

**Selection 3:** `pytest -q -p no:cacheprovider test_nv_render.py -k deferred`
```
PRE : 19 failed, 3 passed, 29 deselected in 0.03s
POST: 7 passed, 29 deselected, 15 subtests passed in 0.02s
```
- PRE: the three locks fail because the prose is absent: `test_deferred_binding_holds` and `test_envelope_deferred_holds` with `False is not true`, and `test_deferred_binding_one_helper_call` with `0 != 1`. `test_deferred_binding_empty_on_failure_inserting_mutant` fails too.
- The three deleting mutants pass as parents, with their phrase subtests SUBFAILED: the phrases are absent, so deleting them changes nothing.

**Selection 4:** `pytest -q -p no:cacheprovider test_score.py -k "TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup"`
```
PRE : 1 failed, 22 passed, 477 deselected, 24 subtests passed in 0.12s
POST: 23 passed, 477 deselected, 24 subtests passed in 0.16s
```
- The one PRE failure is `test_m57_04_kept_open_stamp_removed`: `0 != 1 : mutation target not unique: 'row["snapshot"] = _snapshot_for(row, pass_number, nearby=row_nearby,'`.
- 57-22 re-anchored that test to the first line of a call it split over two lines, and that line does not exist at PRE. This is a difference from the plan's expectation that both trees are green (see Assumption Drift).
- Every other anchor is green on both trees.

| Fixture | PRE 8a0563a (first assertion line) | POST 92b135d | Matches 57-20's red run? |
|---|---|---|---|
| p1 cross-lane (conf 100) | FAIL `None != 2 : row snapshot has no owed nearby_at` (line 10) | PASS | Yes, same message |
| p2 order [10, 12] | SUBFAILED `None != 2 : row snapshot has no owed nearby_at` | PASS | Yes |
| p2 order [12, 10] | SUBFAILED `12 != 10 : lead depends on arrival order [12, 10]` | PASS | Yes |
| p3 min_confidence 80 | FAIL `None != 2 : row snapshot has no owed nearby_at` (`line_10 = 10`) | PASS | Yes |
| p4 far twin | FAIL `None != 2 : line-30 copy not stamped` | PASS | Yes |
| in01 | FAIL `'nearby_at' unexpectedly found in {... 'nearby_at': 2}` | PASS | Yes |
| defer (D-20) | FAIL `unexpectedly None : record 845f88b7 is not an open record (decision orphaned)` | PASS | Yes |
| q1 / q3 controls | PASS | PASS | Yes (green controls) |
| dismiss lock | PASS | PASS | Yes |
| 57-22 `..._persists_on_the_next_pass` | FAIL `decision orphaned` (at the record) | PASS | n/a (57-22); as planned |
| 57-22 `..._row_shape` | FAIL `Lists differ: [] != ['845f88b7…']` (no row) | PASS | n/a (57-22, extra test) |
| 57-22 `test_envelope_without_deferred_hashes_scores_as_before` | PASS | PASS | n/a. It asserts today's behaviour: an envelope with no key scores as before |
| Invariance, 4 new-scenario subtests (cross_lane/fresh-leads-same-band; arrival_order/carried-leads; arrival_order/fresh-leads-reversed-arrival; twin_dropped/fresh-leads-twin-dropped) | SUBFAILED (same messages as 57-20) | PASS (0 SUBFAILED) | Yes, the same 4 subtests |
| Invariance, every other subtest + coverage lock | PASS | PASS | Yes |
| a, a2, b, c, d, control (TestSameLaneRereport) | PASS | PASS | Yes (57-18's fix is in PRE) |
| w1, w2 (TestWr01Guards) | PASS | PASS | Yes |
| s1-s4 (TestSplitPassNearby) | PASS | PASS | Yes |
| 10 mutants with anchors that are new or re-anchored in 57-21/57-22 (carried_from_lead_only, seed_without_hash_equality, split_pass_lead_obligation_prior_not_seeded, index_read_after_filtering, nearby_judged_at_the_lead_only, line_tie_break_dropped, prior_rank_first_wins, deferral_kind_gate, no_synthesized_entry, kept_open_covered_row_without_carried) | FAIL `0 != 1 : mutation target not unique` (anchor absent pre-fix) | PASS | Expected |
| Mutant `test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split` | FAIL at the green-unmutated precondition: `Items in the first set but not the second: test_p4_ test_deferred_ test_p1_ test_p3_ test_in01_ test_p2_` | PASS | Expected (its anchor is 57-15's constant, which exists at PRE; the precondition fails because the row tests are red there), as in 57-19 |
| Older mutants (decided_read_returning_empty, nearby_window_lower/upper_bound, split_pass_carried_arm_dropped) | PASS | PASS | Anchors unchanged |
| TestPooledPriorUnit (6) | ERROR-class: `AttributeError: module 'score' has no attribute '_pooled_prior'` / `'_prior_rank'` (helpers absent) | PASS | Expected (missing helpers, not a behavioural failure) |
| TestDeferred (7, test_carry_state.py) | FAIL `AttributeError: ... no attribute 'deferred'` / SUBFAILED | PASS | Expected |
| deferred prose locks (test_nv_render.py) | FAIL (prose absent) | PASS | Expected |
| test_score.py TestNearbyAt / TestObligationPreservingDedup | PASS | PASS | Expected |
| test_score.py m57-04 | FAIL `mutation target not unique` (re-anchored line absent at PRE) | PASS | Not expected by the plan (see Assumption Drift) |

## D-20 open edge (reproduced, not fixed)

As the orchestrator instructed, this edge is recorded rather than fixed (scope rule).
- **What happens.** The owner opts into `min_confidence` (off by default). On the split pass, that filter removes a deferred covered member before grouping, so the threshold branch never sees it. 57-22's keep-open only runs on the threshold branch, so no kept-open row is synthesized. The deferral leaves the open list and Finalize writes.
- **Why it matters.** D-20 says a deferral never disappears unless the owner closes it, so this violates D-20. It lies outside what this round reproduced: the 57-20 fixtures and the 57-22 plan cover the threshold branch only.
- **Repro.** A scratch script ran `deferred_covered_sub_threshold_scenario("defer", min_confidence=80)` at HEAD 33a951e, from plugins/vibe-check/scripts:
```
pass-2 override: {}
  rows: [('845f88b7', 'sub-threshold; deferred-by: 3449f4b5…')]
  filtered: [(10, 'sub-threshold')]
  open record for hA: True
  outstanding_cw: 1  gate: outstanding-to-phase-5
pass-2 override: {'min_confidence': 80}
  rows: []
  filtered: [(10, 'below-min-confidence')]
  open record for hA: False
  outstanding_cw: 0  gate: write
```
- **Where it is recorded.** deferred-items.md has this repro and a candidate 999.x acceptance. STATE.md's first next-step bullet names it as an open D-20 edge for the owner.
- **Owner decision needed.** It is a silent loss of a deferred finding, which is one of the scope-discipline classes that may still add work. The choice is either to fix it inside Phase 57 or to park it as 999.x.

## Requirements and state

- **deferred-items.md:** appended `## Parked by the fourth gap closure (57-20..57-23; final round, D-19)`. `git diff -U0 | grep -c '^-[^-]'` printed `0`, so no earlier section changed. The new section has four entries:
  - The D-19 hard stop, quoted verbatim, with the 999.x operating rule.
  - The 57-REVIEW-GAPS3.md resolutions, naming the plan that closed each finding:
    - CR-01 (both variants) and CR-02: closed by 57-21.
    - IN-01: closed in code by 57-21.
    - WR-01: closed by 57-20 Task 2.
    - WR-02: closed under D-20 by 57-22. The third-round parked entry is therefore resolved for defer and confirmed intended for dismiss; that entry is left as written.
  - The open D-20 min_confidence edge, with its repro.
  - "Observed, not acted on" items from 57-21 and 57-22 deviations.
- **REQUIREMENTS.md:**
  - `- [x] **DECN-03**`. The DECN-03 row reads `Complete (gap closure 57-08..57-23)`.
  - The DECN-02 row reads `Complete (gap closure 57-08..57-23; D-20 deferred stays open, 57-22)`. `grep -c "Complete (gap closure 57-08..57-23"` printed `2`.
  - The footer was refreshed.
  - **DECN-01 is unchanged** (`Complete`): it was already satisfied, and this round's reproduce-first gate was 57-20.
- **ROADMAP.md:**
  - `bm-sdk query roadmap.update-plan-progress 57 57-23 complete` returned `{"updated":true,...,"summary_count":22,"status":"In Progress"}` and changed nothing, because this SUMMARY did not exist yet.
  - I hand-set the row to `| 57. Decision continuity within closure | 23/23 | Executed, awaiting re-verification (final round, D-19) |  |`. I ticked `- [x] 57-23-PLAN.md` in this plan's docs commit, together with this SUMMARY. 57-20, 57-21 and 57-22 were already ticked, so four `- [x] 57-2[0-3]` lines now exist.
  - `**Plans**: 23 plans (7 executed + 16 gap closure)` is unchanged. The Phase 57 milestone-list line stays `- [ ]`.
- **STATE.md:** hand-edited; no SDK state-mutation call was made, so nothing was clobbered.
  - Frontmatter: status and stopped_at as the plan specifies, `last_updated` refreshed to this run's UTC time, last_activity, and progress 29/29 (100%). completed_phases stays 1.
  - Body: "Phase: 57 ... FOURTH (FINAL) GAP CLOSURE EXECUTED, AWAITING REVIEW + RE-VERIFICATION" and "Plan: 23 of 23 complete".
  - The first Operator Next Steps bullet starts with `NEXT: /bm:code-review 57`, then `/bm:verify-work 57`. It contains "HARD STOP (D-19)" verbatim plus "no fifth structural round", the gate numbers, the outcome line and the open D-20 edge.
  - A second bullet "Prior gap-closure gate (57-19): ..." keeps the 57-19 gate numbers. The older bullets are kept, and the stale "NEXT: /bm:execute-phase 57 --gaps-only" bullet is re-labelled "(done 2026-10-27)".
  - Session Continuity has a new 2026-10-27 entry for 57-20..57-23 with commit hashes.
  - `bm-sdk query state.load` returned OK.
- **Consistency:**
  - STATE `Phase: 57` matches ROADMAP `### Phase 57`.
  - STATE `milestone: v2.13` matches the 🚧 v2.13 active milestone.
  - No phase was ticked early.
  - I did not open the Roadmaps page, so I claim no UI verification.

## D-19 hard stop

This is recorded in STATE.md's first Operator Next Steps bullet and in deferred-items.md. After this round, run `/bm:code-review 57` and then `/bm:verify-work 57`. If either still reproduces a wrong-keep, Phase 57 closes with that finding as a known limit:
- Add a backlog item 999.x whose acceptance fixture is the review's repro.
- Mark DECN-03 `Complete with known limit (999.x)`.
- Open no fifth structural round.

Only a reproduced data-loss or silent-finding-loss class may still add work. The open D-20 min_confidence edge above is such a class, and that is why it goes to the owner for a ruling.

## Commits

- Task 1 (gates, replay, ledger) produced evidence only, with no file change. No allowances file was needed. Its results are recorded in this SUMMARY.
- Task 2 + SUMMARY: one docs commit (deferred-items.md, REQUIREMENTS.md, STATE.md, ROADMAP.md, 57-23-SUMMARY.md). Its hash is in the final report.

## Deviations from Plan

**1. STATE.md second bullet: a new 57-19 gate bullet instead of the prefixed previous first bullet.**
- **What the plan said:** prefix the previous first bullet "Prior gap-closure gate (57-19):".
- **Why I changed it:** the previous first bullet was the 57-22 progress note, not the 57-19 gate.
- **What I did:** added a new bullet carrying the 57-19 gate numbers under that prefix, and kept every earlier bullet unchanged except for re-labelling the stale "NEXT: /bm:execute-phase" bullet "(done 2026-10-27)".
- **Cost if wrong:** cosmetic. The Roadmaps page shows the first three bullets, which are NEXT, the 57-19 gate and 57-22.

**2. Recorded the D-20 min_confidence edge with a repro (orchestrator instruction).**
- **What was asked:** the plan's Entry 3 asks only for observed items. The orchestrator asked for this edge to be recorded with its repro.
- **What I did:** 57-22 had stated it without a repro, so I wrote and ran a scratch script that confirms it. Nothing in the product was changed.
- **Cost if wrong:** none.

## Assumption Drift (advisory)

- **Found during:** Task 1 step 4.
  - **Planned:** test_score.py `TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup` is "both green (57-21/57-22 left those anchors intact)".
  - **Actual:** PRE has 1 failure: m57-04, `mutation target not unique`. POST is green.
  - **Why:** 57-22 split the kept-open `_snapshot_for(...)` call over two lines and re-anchored m57-04 to the first line. That line does not exist at PRE (57-22 Deviation 2).
  - **Cost if wrong:** none. It is the same "anchor absent pre-fix" outcome as the other re-anchored mutants, and the mutant trips at POST.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: 57-23-SUMMARY.md, deferred-items.md (fourth-round section), REQUIREMENTS.md (`[x] **DECN-03**`), STATE.md (`HARD STOP (D-19)`), ROADMAP.md (`23/23`)
- ABSENT (as intended): docs/design/b3-ground-truth/ALLOWANCES-phase57-pooled.json
- FOUND commits referenced: 1ff95f1, 9fe0e0f, 8a0563a, 1ff5702, 333a5cd, 70e0719, 6626edb, 92b135d, 33a951e
