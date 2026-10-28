---
phase: 57-decision-continuity-within-closure
plan: 13
subsystem: vibe-check carry-forward decisions (phase gate, planning records only)
tags: [phase-gate, ledger, replay, full-suite, requirements, gap-closure]
requires: ["57-08", "57-09", "57-10", "57-11", "57-12"]
provides:
  - "Gap-closure gate numbers at the final code commit fbfa8fc (HEAD 967f545 changes no plugin file)"
  - "Red/green ledger addendum: final fixtures reverse-run against the pre-gap tree 57e93d7 and against every gap code commit"
  - "DECN-02 / DECN-03 re-marked complete in REQUIREMENTS.md on that evidence"
  - "WR-01, WR-04, IN-03 recorded in deferred-items.md for the backlog"
affects: ["57 re-verification", "58"]
tech-stack:
  added: []
  patterns:
    - "GREEN point = earliest gap commit at which the FINAL fixture file passes (57-07's definition), found by running the final tests against an archive of each commit"
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-13-SUMMARY.md
  modified:
    - .planning/phases/57-decision-continuity-within-closure/deferred-items.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
decisions:
  - "DECN-02/03 re-marked complete: every gate the phase used is green at the gap-closure code commit and every 57-08 reproduction fails again on the pre-gap tree"
  - "57-09's claim that score.py never refreshes an absorbed finding's band/attribution is confirmed in code (score.py _refreshed_obligation re-derives only `snapshot`)"
  - "Phase 57 stays unticked in ROADMAP (Executed, awaiting verification); re-verification has not run"
metrics:
  duration: "~40 min"
  completed: 2026-10-26
  tasks: 2
  files: 4
---

# Phase 57 Plan 13: Gap-closure gate Summary

Every gate Phase 57 used is green again after the gap closure. The full suite passes with 0 failures, with test_replay.py collected. Replay shows no regression and no unallowed difference against the pre-Phase-57 scorer. The golden digest and import sets are unchanged. Running the final test files against the pre-gap production tree (57e93d7) makes every 57-08 reproduction fail again. On that evidence DECN-02 and DECN-03 are complete again. WR-01, WR-04 and IN-03 are parked for the backlog.

## Gates

All commands were run from `plugins/vibe-check/scripts` at HEAD 967f545. The last plugin-code commit is fbfa8fc (57-12), and 967f545 is a docs-only commit after it. No gate command was blocked by the holdout barrier.

- `pytest -q` (full suite):
  ```
  3248 passed, 4312 subtests passed in 175.95s (0:02:55)
  ```
  0 failed, 0 subtests failed. The 57-07 baseline was 3216 passed, so the count is 32 higher. The extra tests come from 57-08 (new G1-G6 fixtures, six-above keeps, the WR-02 lock and the TestDeletionRangeLock tests), 57-09 (mutants m1-m5, lanes edge tests), 57-10 (`test_inherited_*`, mutants m6-m9), 57-11 (lower-bound mutant) and 57-12 (prose locks). I did not split the +32 per plan, because the per-plan SUMMARYs report passed+failed counts in which a SUBFAILED offset counts as a failure, so their totals are not directly comparable.
- `pytest -q test_replay.py` (proves it is collected):
  ```
  64 passed, 10 subtests passed in 13.55s
  ```
- Golden: `golden ok`.
- `pytest -q test_score.py -k ImportSet`: `3 passed, 495 deselected in 0.09s`. `pytest -q test_carry_state.py -k ImportSet`: `3 passed, 214 deselected in 0.06s`.
- `python3 replay.py candidate --name phase57-gaps-gate --scorer rev:HEAD --out $SP/phase57-gaps-gate-candidate.md` (rc=0):
  ```
  kept 25 / protected 26

  REGRESSED 0

  UNEVALUABLE 0

  AMENDED 1

  baseline **16/18** → candidate **14/18**
  ```
  AMENDED 1 is the pre-existing `triggarr-secret-in-logs/run-2` amendment. The FP headline (16/18 → 14/18) is the same as at 57-07 and 57-11.
- `python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SP/phase57-gaps-gate-diff.md` (rc=0):
  ```
  - runs compared: 170
  - runs differing: 0
  - runs differing (allowed): 0
  - runs with unallowed differences: 0
  - allowances unused: 65
  - head: 967f5456d35db0d34539b6ee1402519478ac03e3
  ## Differences
  - none
  ```
  57-11 created no `ALLOWANCES-phase57-nearby.json`, and `ls` confirms it does not exist. The phase 53 allowances file was used, as the plan specifies. Nothing differed, so nothing was allowed.

## Blocked by the holdout barrier

None of the plan's gate commands was blocked. Every result above comes from the full command named in the plan.

My own ad-hoc scratch commands for the reverse run were blocked 10 times. Each time the message was exactly:

```
PreToolUse:Bash hook error: [python3 /Users/julianamacbook/turingmind-code-review/docs/design/holdout-v2.12/tools/holdout_guard.py hook]: Blocked: this tool call reaches the sealed holdout folder (v2.12 barrier).
```

The blocked commands (SP = session scratchpad, R = repo root), verbatim apart from shortening the scratchpad path:

1. `bash -s` script: `cd $R && git worktree add --detach $W 57e93d7 …` then copy the final tests in and run pytest. It was meant to be a full detached checkout of 57e93d7 so that test_score's `git cat-file` tests could run. The checkout would have included `docs/design/holdout-v2.12`.
2. `bash -s` script: `git archive 57e93d7 plugins/vibe-check | tar -x -C $SP/pre-gap; cp final tests; GIT_DIR=$R/.git pytest -q -rfE -p no:cacheprovider <8 files> > $SP/reverse.txt`. It pointed git at the real object store.
3. `bash -s` script: the same archive and copy, then `for p in score.py carry_state.py batch_card.py card_text.py finalize_card.py; do … cmp -s $p <(git -C $R show 57e93d7:…) …; done; pytest … > $SP/reverse.txt; … grep -v -c 'ReplayError\|rep'`
4. `bash -s` script: `grep -E '^(FAILED|ERROR|SUBFAILED)' $SP/reverse.txt | sed -E 's/ - .*//' > $SP/reverse-list.txt; … grep '^ERROR' … | awk -F'::' '{print $2}' | sort | uniq -c; grep -E '^E +.*(ReplayError|git)' $SP/reverse.txt | sort | uniq -c`
5. `cd $SP/pre-gap/plugins/vibe-check/scripts && pytest -q -rfE --tb=no -p no:cacheprovider <8 files> 2>&1 | grep -E '^(FAILED|ERROR|SUBFAILED)|passed|failed' | sed -E 's/ - .*//' | grep -v '^ERROR'; echo; pytest -q -rfE --tb=no -p no:cacheprovider test_score.py 2>&1 | grep '^ERROR' | awk -F'::' '{print $2}' | sort | uniq -c`
6. `cd $SP && for c in 7685907 … fbfa8fc; do echo "== $c"; (cd at-$c/plugins/vibe-check/scripts && pytest -q --tb=no -p no:cacheprovider <10 named fixtures> 2>&1 | grep -E '^(FAILED|SUBFAILED)|passed|failed' | sed 's/ - .*//'); done`
7. `bash -s` script: `git -C $R log --oneline -1 57e93d7; git -C $R merge-base --is-ancestor 57e93d7 a606a8e …; git -C $R diff --name-only 57e93d7 c8ab8f8` (no pathspec), then `git show c8ab8f8:<3 test files> > $S/v08_*`, pytest on them, `rm -f $S/v08_test_*.py`
8. The same as 7, but with `git -C $R diff --name-only 57e93d7 c8ab8f8 -- plugins` and without the log/merge-base lines.
9. `bash -s` script: a loop over the failing ids from `$SP/rr-short.txt` running `git log --format=%h --reverse -S "def $name(" 57e93d7..HEAD -- $file` and `git log … -L "/def $name(/,+1:$file"`
10. `cd $SP && grep -E '^(FAILED|SUBFAILED)' rr-short.txt | sed -E 's/ - .*//; s/^[A-Z]+(\[[^]]*\]|\([^)]*\))? //' | sort -u > rr-ids.txt; wc -l < rr-ids.txt`

I did not try to get around the barrier. The reverse run was done instead with an archive of `plugins/vibe-check` only and plain pytest commands, which the hook allowed. The 57-08 version re-run (blocks 7 and 8) was dropped. Its result is already established: `git diff --name-only 57e93d7 c8ab8f8 -- plugins/vibe-check` lists only the three test files, so 57-08's recorded red run at c8ab8f8 already ran on the 57e93d7 production tree.

**Disclosure:** my first reverse-run attempt used `git archive 57e93d7 plugins/vibe-check docs | tar -x -C $SP/pre-gap`, and the hook did not block it. That extracted a copy of the whole `docs/` tree, including the sealed `docs/design/holdout-v2.12` folder, into the session scratchpad. I saw that only in a directory listing of `$SP/pre-gap/docs/design/`. I read no file from it and deleted the whole `$SP/pre-gap` directory at once (`rm -rf …/pre-gap`). Every later archive was `plugins/vibe-check` only.

## Red/green ledger addendum

**Method.** I extracted the production tree at 57e93d7 (pre-gap HEAD, the 57-07 close) with `git archive 57e93d7 plugins/vibe-check` and copied the FINAL test_carry_state.py, test_decision_continuity.py, test_nv_render.py, test_finalize_card.py, test_score.py, test_verified_fixes.py, test_batch_card.py and test_card_text.py over it. `cmp` against `git show 57e93d7:` confirmed that score.py, carry_state.py and batch_card.py are byte-identical to 57e93d7. For the GREEN column, I ran the same final tests against an archive of each gap code commit (7685907, 826ddf5, 3e54c8e, a2a7619, 31c51f6, fd36f8f, fbfa8fc). As in 57-07, GREEN is the earliest commit at which the final fixture passes.

**Reverse-run total at 57e93d7** (8 final files): `59 failed, 934 passed, 43 errors, 1013 subtests passed`. In a run of the seven files other than test_score.py, the failures are `54 failed, 482 passed`.

| Path | Fixture | RED at 57e93d7 (observed, final fixture) | Matches 57-08's record? | GREEN at |
|---|---|---|---|---|
| G1 CR-01 | `test_g1_split_obligation_member_is_not_covered_by_row_decision` | Trips first on the sibling `covers` shape check: `{… 'band': 'warning', 'lanes': ['bugs', 'security']} not found in [{'agent': 'security', …, 'code': 'x = 1'}, …]`. With that expected-entry shape relaxed (see below): `AssertionError: 'current' is not None` | Yes, at the decision assertion. The first trip moved because 57-10 added `band`/`lanes` to covers entries | 3e54c8e (57-10). The substantive CR-01 fix is 7685907 (57-09), but the final fixture's covers shape needs 57-10 |
| G2a CR-02 | `test_g2a_inherited_decision_reopens_on_lane_backed_band_rise` | Shape check trips first (`{'agent': 'c', … 'band': 'warning', 'lanes': ['c']} not found`). Relaxed: `'current' != 'stale'` | Yes, at the decision assertion | 3e54c8e (57-10) |
| G2b CR-02 | `test_g2b_inherited_decision_reopens_when_a_newcomer_joins` | Shape check trips first (same entry). Relaxed: `'current' != 'stale'` | Yes, at the decision assertion | 3e54c8e (57-10) |
| G3a WR-03 | `test_g3a_lane_present_for_another_concern_later_corroborates_and_rise_reopens` | `AssertionError: 'current' != 'stale'` | Yes, directly | 826ddf5 (57-09) |
| G3b WR-03 | `test_g3b_unrelated_concern_lane_with_persistence_rise_keeps` | `AssertionError: 'stale' != 'current'` | Yes, directly | 826ddf5 (57-09) |
| D-15 count | `test_g6_covered_count_counts_concerns_not_reports` | Shape check trips first (`{'agent': 'security', … 'band': 'warning', 'lanes': ['bugs', 'security']} not found`). Relaxed: `AssertionError: 2 != 1` | Yes, at the count assertion | 3e54c8e (57-10). The substantive count fix is 7685907 (57-09) |
| D-14 above | `test_r2_edit_within_five_above_reopens` (offset=1, 3, 5) | 3 SUBFAILED, `test_decision_continuity.py:461 AssertionError: 'current' != 'stale'` | Yes (same line, :461) | 31c51f6 (57-11) |
| D-15 pass-6 note | `test_owner_is_asked_exactly_when_evidence_changes` | `:1221 AssertionError: ' — 1 finding here already dismissed (your reason: false positive, guarded upstream); a new concern from compliance joined it' not found in '#1 src/a.py:13 — … — 2 findings here already dismissed …'` | Yes (57-08 recorded :1214; later inserts shifted the line) | 3e54c8e (57-10). The count fix is 57-09; the final journey also needs 57-10's covers shape |
| WR-02 prose | `test_deletion_range_rule_locked` | `test_nv_render.py:444 AssertionError: False is not true` | Yes (57-08 recorded :441; 57-12 added phrases above it) | fd36f8f (57-12) |
| WR-02 lock | `test_r8_guard_deleted_directly_above_reopens` | GREEN on both trees (not in the 57e93d7 failure list; passes at every gap commit). Its `mapping dropped` subtest passes, which shows the mapping is load-bearing | Lock, not a reproduction, as 57-08 recorded | green throughout |

**Relaxed-shape check.** In a scratch copy of the final test_carry_state.py, I removed the 8 expected-entry `"band"`/`"lanes"` keys that 57-10 added to the covers-entry literals. That is 7 regex hits plus G6's computed `lanes` expression. I then ran G1/G2a/G2b/G6 against 57e93d7. The result was `4 failed`, with `'current' is not None`, `'current' != 'stale'` (x2) and `2 != 1`. These are 57-08's four recorded messages. The scratch copy was deleted afterwards. So the final fixtures still contain the original reproductions. Only the order of their first trip changed.

**GREEN progression** (the 10 fixtures above, final versions):
```
7685907: 11 failed, 2 passed       (57-09 T1; final covers shape not yet written)
826ddf5:  9 failed, 4 passed       (57-09 T2; G3a, G3b green)
3e54c8e:  4 failed, 9 passed       (57-10; G1, G2a, G2b, G6, pass-6 green)
a2a7619:  4 failed, 9 passed
31c51f6:  1 failed, 9 passed       (57-11; D-14 offsets green)
fd36f8f: 10 passed, 4 subtests passed  (57-12; WR-02 prose lock green)
fbfa8fc: 10 passed, 4 subtests passed
```

**Every other failure at 57e93d7 is accounted for.** None is an unexplained red.
- **Tests added or rewritten by 57-09..57-12 for the new behaviour (red by construction).** TestGapClosure57 mutants m1-m8 and `test_inherited_*` (7 tests, 57-10). TestRecordDecisions ×3, `test_decision_record_saves_attribution`, `test_decision_without_lanes_reasks_on_any_rise`, `test_gained_lanes_edges`, `test_covers_source_is_state` and `test_decision_record_saves_covers`: these are exact-record assertions that now include `lanes` (57-09) or covers `band`/`lanes` (57-10). `test_r4_covers_frozen_at_decision_time` (covers shape, 57-10). test_batch_card ×4 and test_card_text ×7: same-title-member fixtures (`ba_row_state`, 57-09) and inherited-entry fixtures (57-10) read `lanes`. test_finalize_card `test_phase57_decision_contract` and `test_phase57_old_closed_rule_gone` (57-12 prose).
- **D-14 boundary pins flipped by 57-11.** `test_nearby_window_is_phase56_window` (`9 != 14`), both window mutants (`mutation target not unique`, since the target is the new expression), `TestNearbyAt::test_survivor_window_edges` (at=9, at=5), `test_obligation_member_stamps_and_carries` and `test_m57_05_obligation_stamp_removed` (both use `_na_obligation`, whose edit moved to line 5), and test_verified_fixes `TestAssociatedTest::test_trigger`.
- **Environment only (not a behaviour failure).** 43 errors and 1 failure in test_score.py (TestMembersAcrossPasses, TestRollbackStateCompat, TestSnapshotByteSafety, TestVerdictByteSafety, TestRollbackNeedsVerification, `TestPerMemberCorroboration::test_persistence_arm_is_a_row_property_unchanged`). All of them raise `replay.ReplayError: git cat-file failed (exit 128)`, because the archived tree is not a git repository. `git diff -U0 57e93d7 HEAD -- test_score.py` shows that the gap closure touched only `_na_obligation` and TestNearbyAt (lines 7497-7600), so none of these classes changed. They pass in the full suite at HEAD.

**No reproduction was weakened.** `git diff -U0 57e93d7 -- test_decision_continuity.py test_carry_state.py | grep '^-.*assert'` printed:
```
-        self.assertEqual(carry_state.gained_lanes(
-            self.assertEqual(set(entry), {"agent", "file", "title", "code"})
-        self.assertEqual(len(pairs), 20)
-        self.assertEqual(len(hits), 9, hits)
-        self.assertIn(" — 2 findings here already dismissed (your reason: "
```
and the same grep over test_score.py and test_verified_fixes.py printed:
```
-        self.assertFalse(score._independent_trigger(rec, [], {f: [[70, 79]]}))
```
- `— 2 findings here already dismissed`: the pass-6 flip that 57-08 named (D-15).
- `len(pairs), 20`, `len(hits), 9` and `_independent_trigger … [[70, 79]]`: the three D-14 boundary flips that 57-11 named.
- The two-above `"current"` keep is not listed. 57-08 explained why: diff aligns that line with the identical line kept in `test_r2_edit_six_above_keeps`.
- Two lines are not among the flips 57-08/57-11 named, so I checked both. Neither is a 57-08 fixture, and neither is weaker:
  - `assertEqual(carry_state.gained_lanes(dict(rec, attribution=[…]), s), ["abc", "security"])` was rewritten by 826ddf5 (57-09) to reach the same expected `["abc", "security"]` through members. It also asserts that row-wide attribution is ignored.
  - `set(entry) == {"agent","file","title","code"}` became the six-key set in 3e54c8e (57-10). That is a stricter shape check.
- 57-11's subTest-table edits in test_score (`TestNearbyAt`) change table rows, not assert lines. 57-11-SUMMARY.md lists them.

**57-09's score.py claim is confirmed.** 57-09 rebuilt 32 fixtures on `ba_row_state` because score.py never refreshes an absorbed finding's band or attribution. The code agrees:
- `score.py:355` defines `_OBLIGATION_ROW_KEYS = ("stable_hash", "orchestrator_score", "band", "attribution")`.
- `_refreshed_obligation` (score.py:358-376) returns `dict(obl, snapshot=_snapshot_for(...))`. Only `snapshot` is re-derived, and its docstring says the stored identity and scored fields "stay verbatim".
- Every sidecar write goes through that function (score.py:435, 443, 2609, 2622), copies the carried record's stored keys (2275: `{k: cf.get(k) for k in _OBLIGATION_ROW_KEYS + ("snapshot",)}`), or passes the stored sidecar through unchanged (1262: `rec["obligation"] = raw["obligation"]`). The NV marker at 2705 is a constant.
- No path re-scores a sidecar's band or attribution.

## Requirements and state

- **REQUIREMENTS.md changed.** `- [x] **DECN-02**` and `- [x] **DECN-03**`, and both traceability rows now read `Complete (gap closure 57-08..57-13)`. `grep -c "\[x\] \*\*DECN-0[23]\*\*"` gives 2, and `grep -c "In Progress (verification gaps)"` gives 0. The evidence: every gate above passed, unblocked and on the full command, and the reverse run makes every 57-08 reproduction fail on the pre-gap tree. The footer date is refreshed.
- **STATE.md.**
  - Frontmatter: `last_updated` 2026-10-26T21:54:39Z. `status` "Phase 57 gap closure executed (57-08..57-13); re-verification next". `stopped_at` "Phase 57 gap closure complete — next /bm:verify-work 57 (re-verification), then /bm:ship 57". Progress was hand-set to 19/19 = 100%: all 19 plans in the milestone (Phase 56 has 6, Phase 57 has 13) now have a SUMMARY.
  - The first Operator Next Steps bullet now holds the gate numbers, the one-line outcome per gap, the parked items and the next command.
  - A Session Continuity entry was added.
  - `bm-sdk query state.load` parses the file.
- **ROADMAP.md.** `bm-sdk query roadmap.update-plan-progress 57 57-13 complete` returned `{"updated":true,…,"summary_count":12,"status":"In Progress","complete":false}`, but the file did not change (it ran before this SUMMARY existed). I hand-set the 57-13 plan line to `[x]` and the progress row to `13/13 | Executed, awaiting verification`. The Phase 57 line in the phase list stays `[ ]`, because re-verification has not run.
- **deferred-items.md.** A new section, "Parked by the gap closure", lists WR-01, WR-04 and IN-03 with their failure direction. The plan framed all three as fail-safe ("re-ask, not silent close"), and that holds for WR-04 only. WR-01 never closes a finding silently, but it keeps the decision on the wrong code without re-asking, which I flagged there. IN-03 is a test-coverage gap guarded by phrase locks, not a proven fail-safe.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 1340c8d | docs(57-13): park WR-01, WR-04 and IN-03 for the backlog after the gap-closure gate |
| 2 | acdfa04 | docs(57-13): re-mark DECN-02/03 complete and record the gap closure in state |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reverse-run recipe adjusted for the holdout barrier and git-dependent tests**
- **Found during:** Task 1
- **Issue:** The plan's recipe archives only `plugins/vibe-check/scripts`, but test_nv_render and test_finalize_card read `../phases/*.md`, so the archive had to be `plugins/vibe-check`. 44 test_score.py tests need `git cat-file` on a blob, which fails in a non-repo archive. Both ways to give them a git repo (a detached worktree, and `GIT_DIR` pointed at the real store) were blocked by the holdout barrier.
- **Fix:** I archived `plugins/vibe-check` and classified the 44 git-dependent test_score results as environment-only. They are in classes the gap closure did not touch, and they pass at HEAD.
- **Cost if wrong:** if one of those 44 tests depended on gap-closure behaviour, the ledger would miss a red. That is ruled out because their classes have no diff between 57e93d7 and HEAD.
- **Commit:** n/a (scratch work)

**2. [Rule 1 - Plan expectation] Reverse run fails more than "exactly the 57-08 reds plus the D-14 pins"**
- **Found during:** Task 1
- **Issue:** The acceptance criterion expects nothing else to fail at 57e93d7. But 57-09/57-10/57-12 added tests for new behaviour and rewrote exact-record and shape assertions, which are necessarily red on the pre-gap tree.
- **Fix:** Every extra failure is listed above, with the plan that introduced it. For the four fixtures whose first trip moved to the 57-10 covers shape, a relaxed-shape run shows they still fail on 57-08's exact assertions.
- **Cost if wrong:** none for behaviour. A reader who expected a pure 9-test red set gets a classified 59 + 43.

**3. [Rule 1 - Bookkeeping] ROADMAP progress tool did not update**
- **Found during:** Task 2
- **Issue:** `roadmap.update-plan-progress` counts SUMMARY files, and this SUMMARY did not exist yet.
- **Fix:** I hand-set the 57-13 plan line and the progress row. Phase 57 was deliberately left unticked.
- **Cost if wrong:** the Roadmaps page could show 12/13 if the tool is re-run before this SUMMARY is committed. It is committed with this plan.

## Assumption Drift (advisory)

**1. Final G1/G2a/G2b/G6 first-trip moved**
- **Found during:** Task 1
- **Planned:** each RED cell matches 57-08's recorded first failing assertion.
- **Actual:** four fixtures now trip first on a covers-entry shape check that 57-10 extended (`band`, `lanes`). 57-08's assertion is the second trip, and the relaxed-shape run shows it is still there.
- **Why:** 57-10 changed what a covers entry is, and the fixtures assert the new shape before the decision.
- **Cost if wrong:** none for coverage, since the decision assertions are intact. A future reader reading only the first trip could think the reproduction changed.

**2. WR-01 is not "fail-safe (re-ask)"**
- **Found during:** Task 1 (deferred-items)
- **Planned:** all three parked items fail toward re-asking.
- **Actual:** WR-01 keeps the finding open (no silent close) but does not re-ask. The decision stays on duplicate code.
- **Cost if wrong:** the owner could carry a stale decision on a deleted line until the duplicate line changes. It is flagged in deferred-items.md so the backlog item carries it.

## Known Stubs

None. This plan changed no product file.

## Threat Flags

None. No product surface changed. T-57-35 is mitigated by the reverse run, the quoted failure list and the weakened-assertion grep. T-57-36 is mitigated because the status flip followed all-green, unblocked gates.

## Self-Check: PASSED

- FOUND: .planning/phases/57-decision-continuity-within-closure/deferred-items.md (section "Parked by the gap closure")
- FOUND: .planning/REQUIREMENTS.md (2 x `[x] **DECN-0[23]**`)
- FOUND: .planning/STATE.md ("gap closure", completed_plans 19)
- FOUND: commit 1340c8d
- FOUND: commit acdfa04
