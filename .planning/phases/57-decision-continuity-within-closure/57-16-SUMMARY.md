---
phase: 57-decision-continuity-within-closure
plan: 16
subsystem: phase gate (second gap closure)
tags: [phase-gate, ledger, replay, full-suite, requirements, gap-closure]
requires:
  - phase: 57-14
    provides: real-chain RED fixtures s1-s4, g2c/g2d, producibility guard (red run recorded)
  - phase: 57-15
    provides: score.py split-pass nearby_at stamp (carried arm + lead-obligation prior seeding), 2 e2e mutants
provides:
  - "Second-round gate evidence at the final code commit 7e22d6d (full suite, test_replay, golden, import sets, replay candidate/diff)"
  - "Reverse-run ledger: 57-14 fixtures red at 08126a8, green at 7e22d6d"
  - "DECN-03 re-marked complete; diff-context gap and IN-01..IN-05 parked"
affects: [re-verification (/bm:verify-work 57), /bm:ship 57]
tech-stack:
  added: []
  patterns: ["reverse run via git archive <rev> plugins/vibe-check only"]
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-16-SUMMARY.md
  modified:
    - .planning/phases/57-decision-continuity-within-closure/deferred-items.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
key-decisions:
  - "Replay diff showed 0 differing runs, so no ALLOWANCES-phase57-split.json was created (as in 57-11 and 57-13)"
  - "DECN-03 re-marked complete on the 57-16 gate; Phase 57 stays unticked until re-verification"
duration: 15min
completed: 2026-10-26
requirements: [DECN-03]
---

# Phase 57 Plan 16: Second-round gate Summary

**Every gate is green at the final code commit 7e22d6d. The 57-14 fixtures fail on the pre-fix tree and pass on the fixed one. Replay shows no difference at all, so DECN-03 is complete again and Phase 57 now waits for re-verification.**

## Gates (verbatim)

Range check: `git log --oneline 08126a8..HEAD` lists 0fd360a (docs 57-14), 3b78957, 7e22d6d (57-15 code/test) and 34e1d3e (docs 57-15). `git diff --name-only 08126a8 HEAD` lists only the .planning files, `score.py`, `test_decision_continuity.py` and `test_score.py`. HEAD 34e1d3e changes no plugin file after 7e22d6d, so running the gates at HEAD is the same as running them at the final code commit.

All commands were run from `plugins/vibe-check/scripts` at HEAD.

Full suite (`pytest -q`, tail):
```
3259 passed, 4312 subtests passed in 209.49s (0:03:29)
```
0 failed and 0 subtests failed (no `failed` or `SUBFAILED` in the output). 3259 = 3248 (57-13 baseline) + 11 new tests:
- 57-14 (7): `TestSplitPassNearby::test_s1_inherited_member_split_by_nearby_fix_is_reasked`, `test_s2_own_decision_absorbed_then_split_by_nearby_fix_is_reasked`, `test_s3_owed_stamp_survives_the_split`, `test_s4_fresh_lead_over_a_carried_member_is_not_stamped`, `TestCrossModuleGuards::test_split_row_snapshot_is_the_split_pass_shape`, `TestGapClosure57::test_g2c_inherited_split_pass_with_nearby_stamp_reopens`, `test_g2d_inherited_quiet_split_keeps`
- 57-15 (4): `TestNearbyAt::test_snapshot_for_carried_arm`, `TestPhase57Mutants::test_m57_08_carried_arm_removed` (test_score.py), `TestPhase57Mutants::test_split_pass_carried_arm_dropped_loses_the_split_edit`, `test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp` (test_decision_continuity.py)

test_replay.py was collected (`pytest -q test_replay.py`):
```
64 passed, 10 subtests passed in 15.38s
```
The plan's verify command (`... | grep -Ec "^(6[4-9]|[7-9][0-9]) passed"`) printed `1`.

Golden:
```
golden ok
```

Import sets:
```
pytest -q test_score.py -k ImportSet       -> 3 passed, 497 deselected in 0.09s
pytest -q test_carry_state.py -k ImportSet -> 3 passed, 216 deselected in 0.08s
```

Replay candidate (`python3 replay.py candidate --name phase57-split-gate --scorer rev:HEAD --out $SP/phase57-split-gate-candidate.md`, exit 0):
```
- candidate scorer: rev:HEAD
- candidate scorer sha256: d1b30649fc841cf3275c2bf655d3a3d9e2a31648ca1ba02b1be43af61f7279eb
- HEAD: 34e1d3eddfd95df116495aa82a4713993059e6c0
REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1
kept 25 / protected 26

REGRESSED 0

UNEVALUABLE 0

AMENDED 1
```
The one AMENDED run is the pre-existing `runs/triggarr-secret-in-logs/run-2` (amendment 008).

Replay diff (`python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SP/phase57-split-gate-diff.md`, exit 0):
```
- base: rev:24c0c00 (sha256 ea6b041779c626b40607d4ba65ee0cc1c9522d2bd0c7cdd8995be4969768c233)
- candidate: rev:HEAD (sha256 d1b30649fc841cf3275c2bf655d3a3d9e2a31648ca1ba02b1be43af61f7279eb)
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

0 runs differing and 0 unallowed, so `docs/design/b3-ground-truth/ALLOWANCES-phase57-split.json` was **not** created, as in 57-11 and 57-13. The split-pass stamp did not move any recorded run. None of the 170 replay runs has a carried finding that splits on the pass of a nearby edit, which is why there was nothing to allow for D-17.

## Blocked by the holdout barrier

None. The holdout hook blocked no command in this plan.

**Holdout attestation:** both scratch trees came from `git archive <rev> plugins/vibe-check`, with that pathspec only. I used no `docs` pathspec, no whole-tree archive, no `git worktree` and no `GIT_DIR` override. `docs/design/holdout-v2.12` was never extracted, copied, listed or read. The only `docs/` paths this plan touched are the replay inputs that replay.py reads itself (the manifest and `ALLOWANCES-phase53-nv.json`, through `--allow`). Both scratch trees (`$SP/pre-fix`, `$SP/post-fix`) were deleted afterwards. `ls $SP | grep -E '^(pre-fix|post-fix)$'` printed nothing ("no pre-fix/post-fix in scratchpad").

## Reverse-run ledger

**Method.** PRE = 08126a8 (57-14's last commit). POST = 7e22d6d (57-15's last code commit). Each tree came from `git archive <rev> plugins/vibe-check | tar -x`. The FINAL test_decision_continuity.py, test_carry_state.py and test_score.py were copied over each tree, and the selection ran with `-p no:cacheprovider`.

The PRE production tree is the tree that was re-verified:
```
score.py PRE == d419dc2
carry_state.py PRE == d419dc2
```
(`cmp` against `git show d419dc2:plugins/vibe-check/scripts/<file>`; both identical.)

Selection `pytest -q -rfE --tb=line -p no:cacheprovider test_decision_continuity.py test_carry_state.py -k "TestSplitPassNearby or TestCrossModuleGuards or TestPhase57Mutants or TestGapClosure57"`:

PRE (location lines elided):
```
E   AssertionError: None != 2 : split row snapshot has no nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 3 : split row snapshot has no nearby_at: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: None != 2 : owed nearby_at lost at the split: {'at_pass': 3, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
E   AssertionError: Items in the second set but not the first:
    'nearby_at'
E   AssertionError: 0 != 1 : mutation target not unique
E   AssertionError: 0 != 1 : mutation target not unique
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s1_inherited_member_split_by_nearby_fix_is_reasked
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s2_own_decision_absorbed_then_split_by_nearby_fix_is_reasked
FAILED test_decision_continuity.py::TestSplitPassNearby::test_s3_owed_stamp_survives_the_split
FAILED test_decision_continuity.py::TestCrossModuleGuards::test_split_row_snapshot_is_the_split_pass_shape
FAILED test_decision_continuity.py::TestPhase57Mutants::test_split_pass_carried_arm_dropped_loses_the_split_edit
FAILED test_decision_continuity.py::TestPhase57Mutants::test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp
6 failed, 30 passed, 231 deselected, 45 subtests passed in 0.39s
```
POST:
```
36 passed, 231 deselected, 45 subtests passed in 0.56s
```

Selection `pytest -q -rfE --tb=line -p no:cacheprovider test_score.py -k "TestNearbyAt or TestPhase57Mutants"`:

PRE:
```
E   TypeError: _snapshot_for() got an unexpected keyword argument 'carried'
FAILED test_score.py::TestNearbyAt::test_snapshot_for_carried_arm - TypeError...
FAILED test_score.py::TestPhase57Mutants::test_m57_08_carried_arm_removed - T...
2 failed, 17 passed, 481 deselected, 24 subtests passed in 0.16s
```
POST:
```
19 passed, 481 deselected, 24 subtests passed in 0.20s
```

Negatives checked by name on both trees (`-v -k "test_s4_ or test_g2c_ or test_g2d_"`): all 3 PASSED at PRE and at POST.

| Fixture | PRE 08126a8 (first assertion line) | POST 7e22d6d | Matches 57-14's red run? |
|---|---|---|---|
| s1 `test_s1_inherited_member_split_by_nearby_fix_is_reasked` | FAIL `None != 2 : split row snapshot has no nearby_at` | PASS | Yes, the same message |
| s2 `test_s2_own_decision_absorbed_then_split_by_nearby_fix_is_reasked` | FAIL `None != 3 : split row snapshot has no nearby_at` | PASS | Yes, the same message |
| s3 `test_s3_owed_stamp_survives_the_split` | FAIL `None != 2 : owed nearby_at lost at the split` | PASS | Yes, the same message |
| Producibility guard `test_split_row_snapshot_is_the_split_pass_shape` | FAIL `Items in the second set but not the first: 'nearby_at'` | PASS | Yes, the same message |
| s4 `test_s4_fresh_lead_over_a_carried_member_is_not_stamped` | PASS | PASS | Yes (green negative) |
| g2c `test_g2c_inherited_split_pass_with_nearby_stamp_reopens` | PASS | PASS | Yes (consumer side was already correct) |
| g2d `test_g2d_inherited_quiet_split_keeps` | PASS | PASS | Yes |
| Mutant `test_split_pass_carried_arm_dropped_loses_the_split_edit` | FAIL `0 != 1 : mutation target not unique` (anchor absent pre-fix: 0 matches) | PASS | Not in 57-14 (added in 57-15). Expected |
| Mutant `test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp` | FAIL `0 != 1 : mutation target not unique` (anchor absent pre-fix: 0 matches) | PASS | Not in 57-14 (added in 57-15). Expected |
| `TestNearbyAt::test_snapshot_for_carried_arm` | FAIL `TypeError: _snapshot_for() got an unexpected keyword argument 'carried'` | PASS | Not in 57-14 (57-15 unit pin). Expected |
| `TestPhase57Mutants::test_m57_08_carried_arm_removed` | FAIL `TypeError: ... unexpected keyword argument 'carried'` | PASS | Not in 57-14 (57-15 unit mutant). Expected |

Wording note: the plan predicted that the two e2e mutants would fail at PRE with "mutation target not found". The helper actually reports `0 != 1 : mutation target not unique`. The count is 0, so the anchor is absent from the pre-fix code, which is the outcome the plan expected.

## Requirements and state

- `deferred-items.md`: appended `## Parked by the second gap closure (57-14..57-16; to backlog)`. It holds the diff-context gap, with the `@@ -6,7 +6,6 @@` vs `-U0` `@@ -9 +8,0 @@` reproduction, its failure direction (asks, never drops), why it is outside this round and the three backlog acceptance items. It also lists IN-01..IN-05, one line each with a failure direction (57-15 touched none of them), and says "SA-01 — resolved by owner ruling D-17". Earlier sections are unchanged: `git diff -U0 | grep -c '^-[^-]'` printed 0.
- `REQUIREMENTS.md`: `[x] **DECN-03**`. The DECN-02 and DECN-03 rows both read `Complete (gap closure 57-08..57-16)` (grep count 2), and the footer was refreshed. I made this change only after every gate above was green.
- `STATE.md`: status "Phase 57 second gap closure executed (57-14..57-16); re-verification next". stopped_at names `/bm:verify-work 57`. last_updated is refreshed and progress is 22/22 (100%). The first Operator Next Steps bullet starts `NEXT:` and gives the gate numbers. The previous bullet is kept as "Prior gap-closure gate (57-13): …". A Session Continuity entry was added. `bm-sdk query state.load` parses it ("state.load OK").
- `ROADMAP.md`: Progress row `16/16 | Executed, awaiting re-verification`. The second-round block already existed with 57-14/57-15 ticked, and 57-16 is ticked in the final docs commit together with this SUMMARY. `bm-sdk query roadmap.update-plan-progress 57 57-16 complete` ticked the 57-16 plan line, but it also marked Phase 57 `[x] … (completed 2026-10-27)` and set the Progress row to `Complete`. I reverted those two lines by hand, so the phase stays `[ ]` with `16/16 | Executed, awaiting re-verification` until re-verification passes. STATE progress was set by hand to 22/22 (100%). The Phase 57 line in the milestone list stays `- [ ]`. `**Plans**: 16 plans (7 executed + 9 gap closure)` was already correct.
- Consistency: the STATE `Phase: 57` line matches `### Phase 57`, and the ROADMAP active milestone 🚧 v2.13 matches STATE `milestone: v2.13`. No phase was ticked early. I did not open the Roadmaps page, so no UI verification is claimed.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | — | Gates and ledger only. No tracked file changed: replay showed 0 differing, so there is no allowances file. The evidence is in this SUMMARY |
| 2 | 1fe602d | docs(57-16): park the diff-context gap and re-mark DECN-03 on the second-round gate |

## Deviations from Plan

None. The plan was executed as written. Task 1 produced no commit because the only file it could create (the allowances file) is required only when replay differs, and replay did not differ.

The owner-journey pass-7 expectation change from 57-15 is recorded here as a deliberate D-17 expectation change, not a weakening. The owner chose D-17 "re-ask on split". Pass 7 (lead rewritten at line 13, compliance member at line 14 splits out) now expects a re-ask with cause nearby, and a quiet pass 8 expects the new decision to hold. Inheritance with no nearby edit is still pinned by `split_scenario` (empty diff), g2d and the R6 fixtures.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: .planning/phases/57-decision-continuity-within-closure/57-16-SUMMARY.md
- FOUND: 1fe602d (Task 2), 3b78957 / 7e22d6d (POST), 08126a8 (PRE)
- NOT CREATED (by design): docs/design/b3-ground-truth/ALLOWANCES-phase57-split.json
