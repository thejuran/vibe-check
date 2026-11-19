---
phase: 66-close-out-freshness
plan: 12
subsystem: review-orchestration
tags: [999.44, shape-1, real-chain, replay, release-evidence, gap-closure]
requires:
  - "66-10: worktree_snap collect prints REMOVED_LINE_RANGES="
  - "66-11: step-0 moved-decision forced re-ask (30-collect-score.md) and its simulator"
provides:
  - "test_worktree_snap: the printed REMOVED_LINE_RANGES= value threaded into _Chain.pass2, _pass2_with, _CommittedChain.pass2; _Chain.pass1(base=); _CommittedChain.base_lines(); _ReportAt; _shape1_base"
  - "TestShape1ThroughFences, TestShape1ThroughFencesRange"
  - "test_closeout_fresh: TestShape1Clearable; _ClearChain.review_again threads removed (non --all); decided_pass1(base=)"
  - "66-REPLAY.md section 5, 66-VALIDATION.md shape 1 rows, ROADMAP 999.44 shape 1 outcome: repaired (offline)"
affects: [66-VERIFICATION (re-verification), FRESH-03]
tech-stack:
  added: []
  patterns: ["journey test plus the same journey with the repair switched off", "fence-wiring mutants via mock.patch.object on the simulator module"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_worktree_snap.py
    - plugins/vibe-check/scripts/test_closeout_fresh.py
    - .planning/ROADMAP.md
    - .planning/phases/66-close-out-freshness/66-VALIDATION.md
    - .planning/phases/66-close-out-freshness/66-REPLAY.md
decisions:
  - "Candidate for the gap-closure evidence is 475b2e32 (end of Task 1); every recorded number was run there, offline"
  - "No pre-existing real-chain test changed outcome when the printed removal evidence was threaded in"
requirements: [FRESH-03]
metrics:
  completed: 2026-11-19
  tasks: 2
  commits: 2
---

# Phase 66 Plan 12: shape 1 end to end through the real fences and Close out Summary

The 999.44 shape 1 repair is now proven as the user journey the verification gap describes. The setup: the owner defers or dismisses the finding at line 40, then deletes that line while the identical text is committed at line 55 (54 after the deletion). Close out refuses once with cause `line` and asks for a fresh review. That review runs through the real `worktree_snap.py` fences, and the step-0 simulator receives the `REMOVED_LINE_RANGES=` value the collect fence actually printed. The review re-asks the decision at line 54 (`stale`). Close out then neither writes nor loops back to "review again". After the owner decides again, it writes. With the forced re-ask switched off (the 2.15.0 review-side procedure), the same journey keeps the decision and Close out writes. That is the GATE-07 reproduction. Evidence on candidate **475b2e32** is offline only.

## Tests added (Task 1, 475b2e32)

**test_worktree_snap.py**
- Evidence threading: `_Chain.pass2`, `TestReReview999_28._pass2_with` and `_CommittedChain.pass2` now pass `removed=tdc.removed_arg(self.removed_printed)` to `tdc.run_pass`. Return tuples are unchanged.
- Hooks: `_Chain.pass1(base=None)` keeps `tdc.base_file()` as the default. `_CommittedChain.base_lines()` lets a subclass commit a different base.
- `_shape1_base(text)` commits the decided text at line 55. `_ReportAt` re-reports the finding at `self.report_line`.
- `TestShape1ThroughFences` (default route, real fences):
  - `test_shape1_through_fences_reasks` and `..._without_rereport`: collect prints `{"src/a.py":[[40,40]]}` and the decision reopens at 54 with the nearby card text.
  - `test_shift_through_fences_keeps`: ten lines inserted at the top. Collect prints `{}` and the decision is kept at 50, even though the identical committed copy is at 65.
  - `test_shape1_without_recorded_tree_reasks`: collect prints all three values empty. The decision is re-asked at 54, and with the forced re-ask off it is kept.
  - `test_mutant_forced_reask_off_keeps_through_fences` and `test_mutant_evidence_not_threaded_keeps`: each runs the shape 1 body unpatched (passes), then patched inside `assertRaises(AssertionError)`, then shows that the patched run keeps the decision at 54.
- `TestShape1ThroughFencesRange` (range route): a new commit deletes line 40 while `committed_40 = query(user_input)` is committed at 55. `test_shape1_range_commit_deletes_decided_line_reasks` reopens at 54. `test_shape1_range_forced_reask_off_keeps` keeps.

**test_closeout_fresh.py**
- `_ClearChain.review_again` passes `removed=tdc.removed_arg(self.removed_printed)` on the non-`--all` routes. The `--all` branch is unchanged. `decided_pass1` forwards `base`.
- `TestShape1Clearable`, both kinds:
  - `test_shape1_refuse_review_reask_redecide_write`:
    1. Close out refuses with `refuse` / `stop-review-again` and one stale row (hash, kind word, cause `line`).
    2. The fence-driven fresh review prints `{"src/a.py":[[40,40]]}`, and `undecided(s2) == [h]` with the record at 54 `stale`.
    3. The pass-2 state is persisted with `self.trees[-1]` (asserted non-empty). Close out then gives an action other than write and a next step other than `stop-review-again`.
    4. `redecide_persist_close` writes.
  - `test_shape1_old_review_procedure_writes`: the same journey with `tdc.forced_reask_pairs` patched to `{}`. Nothing is left undecided, the record at 54 is `current`, and Close out writes.

**Pre-existing tests whose expectation changed: none.** After the threading, `test_worktree_snap.py` ran 97 passed (the same set as before the new classes), and the plan-level run below passed.

## Candidate evidence (Task 2, all offline, on 475b2e32 with a clean tree)

1. Full offline suite `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`: **4790 passed, 0 xfailed, 2 warnings, 7400 subtests passed in 617.94s, exit 0**
2. `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`: "35 shipped .py files; third-party imports: none", exit 0.
3. `replay.py diff --base rev:d5acc19`: 170 runs compared, **0 differing** (0 allowed, 0 unallowed). Base and candidate `score.py` sha256 are both `c648872979e9bf3fd5e5f56f64f229de783c8e47258e45651cb5a06742f5e725`.
4. `test_closeout_fresh.py -k only_intended`: 3 passed, 390 subtests passed.
5. `git diff --quiet d5acc19 -- score.py diff_ranges.py` exits 0. Stat against d5acc19: `30-collect-score.md` 14 +-, `carry_state.py` 17 ++- (shape 2 repair only), `worktree_snap.py` 145 +++--.

Other observed runs:
- Task verify selection: 20 passed, 26 subtests.
- Plan-level `test_worktree_snap.py test_closeout_fresh.py test_decision_continuity.py -rx`: 379 passed, 972 subtests, **0 xfailed**.
- `-k Shape1` on the two files: 10 passed, 4 subtests.
- `-k DifferentialV215`: 7 passed, 38 subtests.
- The five shape 1 / control tests in test_decision_continuity: 5 passed, 12 subtests.

## Record edits

- **66-REPLAY.md:** a "Latest candidate" line was added under the header list, and section 5, "Gap closure re-run (999.44 shape 1 repair)", was appended. It records CAND, the date, "Evidence class: OFFLINE", the replay, suite, stdlib and only_intended results, the collect and relocation differentials, and the mutant counts (5 helper, 7 rule, 2 fence-wiring). It says sections 1-4 are the cf1ea0bd history and that 999.40 is re-covered by the full run on CAND, and it includes the known-behaviour sentence.
- **66-VALIDATION.md:**
  - The shape 1 row is now green with the repaired and control tests.
  - Two rows were added: the end-to-end `-k Shape1` row and the `DifferentialV215` row.
  - Mutation checks 10-12 were added.
  - The "Red rows" paragraph now says none, and that the known-limit record is superseded.
  - The evidence-class paragraph was extended with the CAND run.
  - The "Known behaviour (owner decision 2026-11-18)" paragraph was added.
  - The frontmatter and sign-off boxes are untouched.
- **ROADMAP.md §999.44 only:**
  - The header sentence now says shape 1 was repaired in the Phase 66 gap closure.
  - "Shape 1 outcome (Phase 66 gap closure, 2026-11-19): repaired — …" gives the test names, controls, intended differences, out-of-scope items and the known-behaviour sentence.
  - The closing line now reads "FRESH-03 gate item satisfied offline on candidate 475b2e32, pending phase re-verification; no live check was run (GATE-08)."
  - The Phase 66 checkbox is not ticked. STATE.md, REQUIREMENTS.md and 66-VERIFICATION.md are untouched.

Known behaviour (owner decision 2026-11-18): when the removal evidence is missing — the code changed during the pass, or the prior pass recorded no reviewed tree, which also leaves the following pass without evidence — a deferred or dismissed decision whose line only shifted is asked again; 2.15.0 kept that decision; the owner chose the re-ask ("Re-ask them") as a deliberate, tested difference.

## Roadmaps page check

http://localhost:8088 answered with HTTP 200. The page builds its view in the browser (from the GitHub API and a local source), so a plain fetch does not show whether a "Planning files disagree" warning is displayed. No UI check was performed, and none is claimed.

## Deviations from Plan

**1. [Rule 3 - Blocking] The range-route case was split into two tests.** Running the deleted-line journey twice in one test failed: `_CommittedChain.setUp` builds the repo once, so the second `move_end` had nothing to commit. The re-ask and the forced-re-ask-off keep are now two tests (`test_shape1_range_commit_deletes_decided_line_reasks`, `test_shape1_range_forced_reask_off_keeps`).
- **Cost if wrong:** none. Each test gets its own repo.

**2. [Rule 2 - Strength] The mutant and no-tree tests also check the direction of the failure.** Under each patch they assert `assert_keeps` at 54 (the 2.15.0 wrong keep), not just "some AssertionError".
- **Cost if wrong:** none. It only makes the checks stricter.

## Known Stubs

None.

## Threat Flags

None. These are test and record changes only. T-66-26: every number was run on CAND and labelled offline. T-66-27: the journey with the repair off writes, and the two fence-wiring mutants fail. T-66-28: no reviewer and no live session were started.

## Commits

- 475b2e32 test(66-12): 999.44 shape 1 end to end through the real fences and Close out (both kinds)
- cbdf7298 docs(66): shape 1 gap-closure evidence and records (offline)

## Self-Check: PASSED

The two modified test files, 66-REPLAY.md, 66-VALIDATION.md, ROADMAP.md and this SUMMARY exist. Commits 475b2e32 and cbdf7298 are in git log, and `git cat-file -t 475b2e32…` reports `commit`.
