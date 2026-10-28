---
phase: 57-decision-continuity-within-closure
plan: 19
subsystem: phase gate (third gap closure)
tags: [phase-gate, ledger, replay, full-suite, requirements, gap-closure]
requires:
  - phase: 57-17
    provides: "TestSameLaneRereport + TestLeadOrderInvariance red run on the unfixed scorer (584f7bb)"
  - phase: 57-18
    provides: "carried-from-any-source root fix (8bd75ec) + WR-01 guards and mutants (90228be)"
provides:
  - "Verbatim green gates at the final code commit 90228be"
  - "Reverse-run ledger: 57-17 fixtures red at 584f7bb, green at 90228be"
  - "DECN-03 re-marked complete; third-round observation parked; 57-REVIEW-GAPS2 items recorded closed"
affects: [57 re-verification (/bm:verify-work 57), /bm:ship 57]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-19-SUMMARY.md
  modified:
    - .planning/phases/57-decision-continuity-within-closure/deferred-items.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
key-decisions:
  - "No ALLOWANCES-phase57-samelane.json: replay diff vs rev:24c0c00 showed 0 of 170 runs differing, so nothing needed an allowance"
  - "DECN-03 re-marked complete on the 57-19 gate (all gates green, replay unchanged)"
duration: 15min
completed: 2026-10-27
requirements: [DECN-03]
---

# Phase 57 Plan 19: Third-round gate Summary

**Every gate is green at the final code commit 90228be. The full suite is 3273 passed, 0 failed, 0 subtests failed, and test_replay.py was collected (64 passed). The replay diff against rev:24c0c00 shows 0 of 170 runs differing, so no allowances file was needed. All five 57-17 fixtures and all eight same-lane invariance subtests are red on the pre-fix tree, whose production files are byte-identical to 70346c2, and green after the fix. DECN-03 is re-marked complete. Phase 57 stays unticked until it is re-verified.**

## Gates (verbatim)

Range check. PRE = 584f7bb (57-17's last commit). POST = 90228be (57-18's last code commit). `git log --oneline 584f7bb..HEAD` lists:
```
8665faf docs(57-18): update state and roadmap after carried-from-any-source root fix
960dc3c docs(57-18): complete carried-from-any-source root fix plan
90228be test(57-18): lock WR-01 guards and the carried-from-any-source rule with mutants
8bd75ec fix(57-18): derive carried-ness and prior snapshot from any same-hash carried source
```
`git diff --name-only 584f7bb HEAD -- plugins/` lists only `plugins/vibe-check/scripts/score.py` and `plugins/vibe-check/scripts/test_decision_continuity.py`. test_score.py was not touched. HEAD 8665faf changes no plugin file after 90228be, so running the gates at HEAD is the same as running them at the final code commit. Every command below ran from `plugins/vibe-check/scripts` at HEAD.

Full suite (`pytest -q`, tail):
```
3273 passed, 4328 subtests passed in 204.07s (0:03:24)
```
The output has no `failed` and no `SUBFAILED`: 0 failed and 0 subtests failed. 3273 = 3259 (the 57-16 baseline) + 14 new tests:
- 57-17 (8): `TestSameLaneRereport::test_a_plain_row_rereported_by_own_lane_at_conf_100`, `test_a2_plain_row_rereported_by_own_lane_at_higher_band`, `test_b_inherited_split_led_by_own_lane_rereport`, `test_c_own_decision_absorbed_split_led_by_own_lane_rereport`, `test_d_owed_stamp_survives_own_lane_rereport_on_quiet_pass`, `test_control_carried_copy_leads_at_conf_75`, `TestLeadOrderInvariance::test_decision_outcome_does_not_depend_on_which_record_leads`, `test_guard_covers_every_scenario_the_phase_cares_about`
- 57-18 (6): `TestWr01Guards::test_w1_needs_recheck_split_row_keeps_its_hash_and_is_stamped`, `test_w2_edited_lead_member_does_not_inherit_the_old_stamp`, `TestPhase57Mutants::test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split`, `test_seed_without_hash_equality_inherits_a_foreign_stamp`, `test_carried_from_lead_only_loses_the_same_lane_rereport`, `test_seed_after_dedup_loses_the_dropped_duplicate_prior`

test_replay.py was collected (`pytest -q test_replay.py`):
```
64 passed, 10 subtests passed in 20.32s
```
The plan's verify command (`pytest -q test_replay.py 2>&1 | tail -1 | grep -Ec "^(6[4-9]|[7-9][0-9]) passed"`) printed `1`.

Golden:
```
golden ok
```

Import sets:
```
pytest -q test_score.py -k ImportSet       -> 3 passed, 497 deselected in 0.12s
pytest -q test_carry_state.py -k ImportSet -> 3 passed, 216 deselected in 0.08s
```

Replay candidate (`python3 replay.py candidate --name phase57-samelane-gate --scorer rev:HEAD --out $SP/phase57-samelane-gate-candidate.md`, exit 0):
```
- candidate scorer: rev:HEAD
- candidate scorer sha256: 3efae186d38c0b54a88140f9d546aba493d5ccac8c25918e85a917c7cde611a9
- HEAD: 8665fafeaabbec6a24ad1409344caa3aa74738bb
REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1
kept 25 / protected 26

REGRESSED 0

UNEVALUABLE 0

AMENDED 1
```
The one AMENDED run is the pre-existing `runs/triggarr-secret-in-logs/run-2` (axis-false, amendment 008).

Replay diff (`python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SP/phase57-samelane-gate-diff.md`, exit 0):
```
- base: rev:24c0c00 (sha256 ea6b041779c626b40607d4ba65ee0cc1c9522d2bd0c7cdd8995be4969768c233)
- candidate: rev:HEAD (sha256 3efae186d38c0b54a88140f9d546aba493d5ccac8c25918e85a917c7cde611a9)
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

0 runs differed and 0 were unallowed, so `docs/design/b3-ground-truth/ALLOWANCES-phase57-samelane.json` was **not** created, as in 57-11, 57-13 and 57-16. None of the 170 replay runs has a carried record that a fresh same-identity re-report out-ranked, so the 57-18 rule moved no recorded output. Status, band, score, title, row count, members, nv_dropped_weak and filtered are all unchanged.

## Blocked by the holdout barrier

None. The holdout hook blocked no command in this plan.

**Holdout attestation:** both scratch trees came from `git archive <rev> plugins/vibe-check`, with that pathspec only. Each extracted tree's top level was `plugins` and nothing else. I used no `docs` pathspec, no whole-tree archive, no `git worktree` and no `GIT_DIR` override. `docs/design/holdout-v2.12` was never extracted, copied, listed or read. The only `docs/` paths touched were the replay inputs that replay.py reads itself (the manifest, and `ALLOWANCES-phase53-nv.json` through `--allow`), plus a single `ls` of the would-be `ALLOWANCES-phase57-samelane.json` path to confirm it does not exist. Both scratch trees (`$SP/pre-fix`, `$SP/post-fix`) were deleted afterwards: `ls $SP | grep -E '^(pre-fix|post-fix)$'` printed nothing, and the check echoed "no pre-fix/post-fix in scratchpad".

## Reverse-run ledger

**Method.** Each tree came from `git archive <rev> plugins/vibe-check | tar -x`. The FINAL test_decision_continuity.py and test_score.py were copied over each tree, and every selection ran with `-p no:cacheprovider`.

The PRE production tree is the tree that was re-verified (`cmp` against `git show 70346c2:plugins/vibe-check/scripts/<file>`):
```
score.py pre-fix == 70346c2
carry_state.py pre-fix == 70346c2
score.py post-fix DIFFERS from 70346c2      (the 57-18 fix)
carry_state.py post-fix == 70346c2
```

Selection `pytest -q -rfE --tb=line -p no:cacheprovider test_decision_continuity.py -k "TestSameLaneRereport or TestLeadOrderInvariance or TestWr01Guards or TestPhase57Mutants or TestSplitPassNearby"`:

PRE 584f7bb. The `unittest/case.py` echo lines and the repeated tuple-diff body lines are elided:
```
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'critical'}
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 3 : re-reported split row snapshot has no nearby_at: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: Tuples differ: ('current', None, False) != ('stale', 'nearby', True)     (x8)
E   AssertionError: 0 != 1 : mutation target not unique
E   AssertionError: Items in the first set but not the second:
    'test_b_'
    'test_d_'
E   AssertionError: 0 != 1 : mutation target not unique
E   AssertionError: 0 != 1 : mutation target not unique
E   AssertionError: 0 != 1 : mutation target not unique
FAILED ...TestSameLaneRereport::test_a2_plain_row_rereported_by_own_lane_at_higher_band
FAILED ...TestSameLaneRereport::test_a_plain_row_rereported_by_own_lane_at_conf_100
FAILED ...TestSameLaneRereport::test_b_inherited_split_led_by_own_lane_rereport
FAILED ...TestSameLaneRereport::test_c_own_decision_absorbed_split_led_by_own_lane_rereport
FAILED ...TestSameLaneRereport::test_d_owed_stamp_survives_own_lane_rereport_on_quiet_pass
SUBFAILED(scenario='plain', lead='fresh-leads-same-band') ...
SUBFAILED(scenario='plain', lead='fresh-leads-higher-band') ...
SUBFAILED(scenario='inherited_split', lead='fresh-leads-same-band') ...
SUBFAILED(scenario='inherited_split', lead='fresh-leads-higher-band') ...
SUBFAILED(scenario='absorbed_split', lead='fresh-leads-same-band') ...
SUBFAILED(scenario='absorbed_split', lead='fresh-leads-higher-band') ...
SUBFAILED(scenario='owed_quiet_same_lane', lead='fresh-leads-same-band') ...
SUBFAILED(scenario='owed_quiet_same_lane', lead='fresh-leads-higher-band') ...
FAILED ...TestPhase57Mutants::test_carried_from_lead_only_loses_the_same_lane_rereport
FAILED ...TestPhase57Mutants::test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split
FAILED ...TestPhase57Mutants::test_seed_after_dedup_loses_the_dropped_duplicate_prior
FAILED ...TestPhase57Mutants::test_seed_without_hash_equality_inherits_a_foreign_stamp
FAILED ...TestPhase57Mutants::test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp
18 failed, 13 passed, 39 deselected, 8 subtests passed in 0.47s
```
POST 90228be:
```
23 passed, 39 deselected, 16 subtests passed in 0.68s
```

Selection `pytest -q -rfE --tb=line -p no:cacheprovider test_score.py -k "TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup"`:
```
PRE : 23 passed, 477 deselected, 24 subtests passed in 0.22s
POST: 23 passed, 477 deselected, 24 subtests passed in 0.23s
```
There is no PRE/POST difference here, as expected: 57-18 left those anchors intact.

| Fixture | PRE 584f7bb (first assertion line) | POST 90228be | Matches 57-17's red run? |
|---|---|---|---|
| test_a `..._at_conf_100` | FAIL `None != 2 : re-reported row snapshot has no nearby_at` (band warning) | PASS | Yes, the same message |
| test_a2 `..._at_higher_band` | FAIL `None != 2 : re-reported row snapshot has no nearby_at` (band critical) | PASS | Yes, the same message |
| test_b `test_b_inherited_split_led_by_own_lane_rereport` | FAIL `None != 2 : re-reported row snapshot has no nearby_at` | PASS | Yes, the same message |
| test_c `test_c_own_decision_absorbed_split_led_by_own_lane_rereport` | FAIL `None != 3 : re-reported split row snapshot has no nearby_at` | PASS | Yes, the same message |
| test_d `test_d_owed_stamp_survives_own_lane_rereport_on_quiet_pass` | FAIL `None != 2 : re-reported row snapshot has no nearby_at` (at_pass 3) | PASS | Yes, the same message |
| test_control `test_control_carried_copy_leads_at_conf_75` | PASS | PASS | Yes (green control) |
| Invariance, 8 same-lane fresh-leads subtests (plain, inherited_split, absorbed_split, owed_quiet_same_lane x same-band/higher-band) | SUBFAILED `Tuples differ: ('current', None, False) != ('stale', 'nearby', True)` | PASS (0 SUBFAILED) | Yes, the same 8 subtests |
| Invariance, 8 other subtests (6 carried-leads baselines, owed_quiet_different_lane, different_lane_dup_57_04) + parent + coverage test | PASS | PASS | Yes |
| w1 `test_w1_needs_recheck_split_row_keeps_its_hash_and_is_stamped` | PASS | PASS | n/a (added in 57-18). Green before the fix: WR-01 was a coverage gap, not a misbehaviour |
| w2 `test_w2_edited_lead_member_does_not_inherit_the_old_stamp` | PASS | PASS | n/a (added in 57-18). Same reason as w1 |
| s1-s4 TestSplitPassNearby | PASS (all 4) | PASS | n/a (57-15's fix is in PRE) |
| Mutant `test_carried_from_lead_only_loses_the_same_lane_rereport` | FAIL `0 != 1 : mutation target not unique` (anchor absent pre-fix) | PASS | Expected |
| Mutant `test_seed_after_dedup_loses_the_dropped_duplicate_prior` | FAIL `0 != 1 : mutation target not unique` (anchor absent pre-fix) | PASS | Expected |
| Mutant `test_seed_without_hash_equality_inherits_a_foreign_stamp` | FAIL `0 != 1 : mutation target not unique` (anchor absent pre-fix) | PASS | Expected |
| Re-anchored seed mutant `test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp` | FAIL `0 != 1 : mutation target not unique` (anchor absent pre-fix) | PASS | Expected |
| Mutant `test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split` | FAIL `Items in the first set but not the second: 'test_b_' 'test_d_'` | PASS | Expected, but not the "anchor absent" outcome (see Assumption Drift) |
| Older mutants (`decided_read_returning_empty`, `nearby_window_lower/upper_bound`, `split_pass_carried_arm_dropped`) | PASS | PASS | Unchanged anchors |

## Requirements and state

- **deferred-items.md:** appended `## Parked by the third gap closure (57-17..57-19; to backlog)`. Entry 1 is the covered low-entropy member that is filtered sub-threshold on its split pass. Its failure direction is a keep, not an ask, and the entry gives a backlog acceptance. Entry 2 records the 57-REVIEW-GAPS2.md resolutions: CR-01 + SA-01 closed by 57-18 (fixtures from 57-17), WR-01 closed by 57-18 Task 2, IN-01 resolved by docstring (quoted from 57-18), and IN-02 resolved by splitting the call. `git diff -U0 | grep -c '^-[^-]'` printed `0`, so no earlier section changed.
- **REQUIREMENTS.md:** `- [x] **DECN-03**`. The DECN-02 and DECN-03 traceability rows both read `Complete (gap closure 57-08..57-19)`, and `grep -c` printed `2`. The footer reads `*Last updated: 2026-10-27 after Phase 57 third gap closure (DECN-03 complete on the 57-19 gate)*`.
- **ROADMAP.md:** I ran `bm-sdk query roadmap.update-plan-progress 57 57-19 complete` first. It wrote `| 57. ... | 18/19 | In Progress|  |`, because this SUMMARY did not exist yet. It did not tick the phase. I hand-set the row to `| 57. Decision continuity within closure | 19/19 | Executed, awaiting re-verification |  |` and ticked `- [x] 57-19-PLAN.md` in the same commit as this SUMMARY. 57-17 and 57-18 were already ticked. `**Plans**: 19 plans (7 executed + 12 gap closure)` is unchanged. The Phase 57 milestone-list line stays `- [ ]`.
- **STATE.md:**
  - Frontmatter: status "Phase 57 third gap closure executed (57-17..57-19); re-verification next", the stopped_at the plan specifies, `last_updated` refreshed to this run's UTC time, progress 25/25 (100%) with completed_phases still 1.
  - Body: "Phase: 57 ... THIRD GAP CLOSURE EXECUTED, AWAITING RE-VERIFICATION", "Plan: 19 of 19 complete".
  - Operator Next Steps: the first bullet starts with `NEXT: /bm:verify-work 57` and carries this gate's numbers. The previous first bullet is kept as the second, prefixed "Prior gap-closure gate (57-16):".
  - Session Continuity: a new 2026-10-27 entry for 57-17..57-19 with commit hashes.
  - `bm-sdk query state.load` returned OK.
- **Consistency:** STATE `Phase: 57` matches ROADMAP `### Phase 57`. STATE `milestone: v2.13` matches the 🚧 v2.13 active milestone. No phase was ticked early. The Roadmaps page itself was not opened, so no UI verification is claimed.

## Commits

- Task 1 (gates, replay, ledger) produced evidence only, with no file change: no allowances file was needed. Its results are recorded in this SUMMARY.
- Task 2 + SUMMARY: one docs commit (deferred-items.md, REQUIREMENTS.md, STATE.md, ROADMAP.md, 57-19-SUMMARY.md). Its hash is in the final report.

## Deviations from Plan

**1. [Rule 3 - Sequencing] Task 1 has no commit of its own.** Its only file output was the conditional allowances file, which the 0-differing diff made unnecessary, as in 57-16. Cost if wrong: none. The evidence is in this SUMMARY.

**2. [Rule 3 - Tooling] The ROADMAP progress row was hand-set to 19/19.** The SDK counts SUMMARY files, and this SUMMARY lands in the same commit. Cost if wrong: none. The row matches the on-disk state at commit time.

## Assumption Drift (advisory)

- **Found during:** Task 1 step 3.
  - **Planned:** "the four new mutants and the re-anchored seed mutant fail [at PRE] with `0 != 1 : mutation target not unique` (anchor absent pre-fix)".
  - **Actual:** four of the five do. `test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split` anchors on `_CARRIED_STATUSES = ("persisted", "needs-recheck")`, which already exists at PRE (`grep -c` printed `1`). It fails one step later, at `_run_mutant`'s precondition that the row tests are green unmutated (`self.assertEqual(self._failures(), set())`, line 2051). They are not green at PRE, because test_b and test_d are red there.
  - **Why:** that anchor is 57-15's constant, not a 57-18 line.
  - **Cost if wrong:** none. The mutant still cannot pass on the pre-fix tree, and it passes at POST.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: .planning/phases/57-decision-continuity-within-closure/57-19-SUMMARY.md
- FOUND: deferred-items.md section "Parked by the third gap closure" (1)
- FOUND: REQUIREMENTS.md `[x] **DECN-03**` (1), "Complete (gap closure 57-08..57-19)" (2)
- FOUND: commits 584f7bb, 8bd75ec, 90228be (PRE/POST references)
- CONFIRMED absent: docs/design/b3-ground-truth/ALLOWANCES-phase57-samelane.json (not needed)
