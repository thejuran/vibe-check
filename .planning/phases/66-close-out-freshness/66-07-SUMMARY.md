---
phase: 66-close-out-freshness
plan: 07
status: paused
paused_at: "Task 3 (checkpoint:decision, owner) — verdict BOUND-EXCEEDED"
subsystem: decision continuity / step-0 relocation
tags: [999.44, shape-1, relocation, D-21, D-14, decision-continuity]
requires:
  - "66-05 (--all records reviewed_tree)"
provides:
  - "deleted_original_scenario + TestShape1DeletedOriginal: real-chain reproduction of 999.44 shape 1 for defer and dismiss (RED, committed)"
  - "explicit D-21 control (test_d21_identical_copy_added_while_original_remains_keeps) and pure-shift control"
affects:
  - "66-09 Task 2 (FRESH-03 verdict keys on the shape-1 outcome line)"
tech-stack:
  added: []
  patterns: ["real git diff -> exact-range builder -> relocate_decided -> score.run -> finalize_inputs CLI on a reviewed_tree-bound repo"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "Shape 1 REPRODUCED for both kinds when the identical copy was already in the reviewed file (the 999.44 record's shape); not when the same change writes the copy"
  - "Verdict BOUND-EXCEEDED: no in-bound rule (test file + 30-collect-score.md only) tells a deleted original from a pure line shift; the correct check needs old-side diff lines from a helper"
metrics:
  duration: ~35m
  completed: 2026-11-17
  tasks: "1 of 3 complete (Task 2 verdict recorded, no commit; Task 3 awaiting owner)"
  files: 1
---

# Phase 66 Plan 07: 999.44 shape 1 (deleted original vs D-21) Summary (PAUSED at owner checkpoint)

999.44 shape 1 reproduces through the real chain for both decision kinds: when the decided line is deleted and an identical line was already elsewhere in the reviewed file, step-0 relocation moves the decision to that other line, keeps it `current`, and Close out writes. The bounded review-side re-ask (D-14) cannot be made correct inside the allowed files, so the plan stopped at the Task 3 owner checkpoint.

## Task 1: reproduction (commit 43305ff2)

Added to `test_decision_continuity.py`:

- `deleted_original_scenario(test, kind, copy="kept"|"added")` next to `far_twin_scenario`. Pass 1 decides `bugs` A at line 10. Between passes line 10 is deleted. Pass 2 uses the real `git diff` from a temp repo, the exact-range builder (`diff_ranges.ranges_from_diff`), `relocate_decided` against `carry_state.py decided`, and the same agent re-reporting at the line the record was read at.
- `class TestShape1DeletedOriginal(_RealChain)`. Close out runs the real `finalize_inputs.run(argv_for(...))` in the temp repo after `bind_reviewed_tree` binds the last pass to the post-deletion code (disk == reviewed tree, checked with `git status --porcelain`). The outcome therefore comes from the decision state, not from a freshness refusal.

Observed on current code:

| Test | defer | dismiss |
|------|-------|---------|
| test_shape1_deleted_original_is_reasked_at_pass2 | FAIL: kept `current` at line 49 | FAIL: same |
| test_shape1_closeout_does_not_write_on_deleted_original | FAIL: `action: write`, `next: write-review-md`, report entry line 49 `status: current` | FAIL: same |
| test_shape1_copy_written_by_the_same_change_reasks_control | pass | pass |
| test_d21_identical_copy_added_while_original_remains_keeps | pass | pass |
| test_shape1_pure_shift_keeps | pass | pass |
| test_p4_far_twin_new_copy_is_not_evidence (unmodified) | pass | |

Task 1 verify (`pytest -q -p no:cacheprovider test_decision_continuity.py -k "d21_identical_copy or shape1_pure_shift or far_twin"`): the controls passed (4 passed, 6 subtests passed; the run included the same-change control). The far-twin test was unmodified: the `git diff -U0 ... | grep -c far_twin_new_copy_is_not_evidence` check returned 0.

## Task 2: verdict BOUND-EXCEEDED (no commit)

I tried the smallest in-bound rule ("rule R"). In `relocate_decided` case 2 it does not move a decided record when its stored line lies inside the pass's `changed_line_ranges` (threaded through `next_cf` / `run_pass`). With rule R in place, `pytest -q test_decision_continuity.py` gave 4 failed, 163 passed:

- The four shape-1 RED subtests now passed. The record stays at line 10, is re-hashed into an undecided `needs-recheck` row, and the gate is `outstanding-to-phase-5`. This is the same outcome as deleting the decided line when no copy exists.
- **`test_shape1_pure_shift_keeps` failed (defer and dismiss)**: "record dee0f534 is not an open record (decision orphaned)". Inserting 20 lines at the top gives the range `[1, 20]`, which covers stored line number 10, so the decision is not followed to line 30 and is re-asked. That is the T-66-19 over-ask the plan forbids.
- `test_shape1_copy_written_by_the_same_change_reasks_control` also failed, but only because its `assert_reopens(..., 48)` names the relocated line. The outcome was still not `write`, so this was a fixture detail, not a regression.

Why no in-bound rule works: `changed_line_ranges` and the since-review `nearby_line_ranges` hold **new-side line numbers only**. A deletion at line 10 (`[9, 10]`) and an insertion covering line 10 (`[1, 20]`) look the same at stored line 10. The record keeps no `canonical_window`, so content cannot tell them apart either. A correct check needs to know that **old** line 10 was removed between the previous review's tree and the current code. Neither the exact-range builder (`diff_ranges.py`) nor `worktree_snap.py collect` emits that.

I reverted the experimental edit with `git checkout -- test_decision_continuity.py`. `score.py`, `carry_state.py`, `worktree_snap.py` and `30-collect-score.md` are unmodified (`git status --porcelain` on them printed nothing). The plan-level run `pytest -q test_decision_continuity.py test_worktree_snap.py` gave 4 failed (exactly the four RED shape-1 subtests), 230 passed, 226 subtests passed.

## Task 3: CHECKPOINT (awaiting owner)

**Evidence for the owner:**

- **RED tests:** `TestShape1DeletedOriginal.test_shape1_deleted_original_is_reasked_at_pass2` and `.test_shape1_closeout_does_not_write_on_deleted_original`, for both defer and dismiss. Failure: the decision stayed `current` at line 49 after line 10 was deleted, and Close out returned `action: write`.
- **Minimal extra change needed:** `worktree_snap.py` `collect` (the since-review diff from the last pass's `reviewed_tree` to the current code) would also report, per file, the old-side line numbers removed since the review. Step 0 of `30-collect-score.md` and `relocate_decided` would then skip case-2 relocation for a decided record whose stored line is in that set. The record stays at its stored line and is re-asked, as for a deletion with no copy. An alternative is a removed-lines output in `diff_ranges.py`, but that diff is against the route's base (for example HEAD), not against the previous review, so it misses a deletion committed between passes.
- **Why it exceeds D-14:** it edits a helper (`worktree_snap.py`, which the plan names as out of bound) and adds an envelope or prose input. The plan allowed only the step-0 sentence and the simulator. The in-bound rule over-asks on ordinary insertions of six or more lines that cover the stored line number. Shorter insertions already re-ask through the nearby window.
- **Does the Close out freshness check (66-03/66-04) catch it?** Only partly. If the line is deleted after the last review and the owner goes straight to Close out, the freshness check sees changed code and asks for a fresh review. That fresh review relocates and keeps the decision again, and the next Close out writes. Once a review has run after the deletion, freshness sees nothing to refuse, which is the state the Close-out test above binds. So the refusal does not limit the damage. It only delays the wrong keep by one review. This comes from the fixture plus RESEARCH §shape 1. 66-04 is not wired yet, so it was not run end to end.
- **Failure direction today:** the finding stays open as `persisted` (nothing is closed), but the owner's earlier defer or dismiss stays attached to the surviving identical line without being asked again.

**Options (from the plan):**

1. `known-limit`: keep the RED tests as evidence. They get renamed with `_known_limit` and marked `@unittest.expectedFailure`, and the docstring names 999.44 shape 1. The 999.44 outcome line then reads "owner-accepted known limit". No out-of-bound code change. Con: the review side keeps relocating a deleted-original decision, and the Close out refusal only delays it by one review (see above).
2. `approve-wider`: authorise the named wider change. The likely file is `worktree_snap.py collect`, plus the step-0 sentence and the simulator. It needs its own RED/GREEN plan and a differential against d5acc19. It is not implemented here.

Resume signal: `known-limit` or `approve-wider` (name the authorised file(s)).

## Deviations from Plan

**1. [Rule 1 - Bug] Plan-literal construction does not reproduce; the 999.44 shape does**
- **Found during:** Task 1
- **Issue:** The plan builds L1 with `L1[48] = L0[9]; del L1[9]`. That writes the copy in the same change, so the real diff names line 48, and score.py stamps the relocated record `nearby` (re-asked) on current code. The 999.44 evidence says the identical text "remained at line 49", which means it was already in the reviewed file at old line 50.
- **Fix:** `deleted_original_scenario(copy="kept")` (the default) uses the existing copy at old line 50. The plan-literal shape is kept as `test_shape1_copy_written_by_the_same_change_reasks_control`.
- **Cost if wrong:** if the owner meant only the same-change shape, shape 1 would be "not reproduced" (D-10) rather than reproduced.
- **Commit:** 43305ff2

**2. [Rule 1] The re-ask assertion uses "not kept current + not write" instead of `assert_reopens`**
- **Found during:** Task 1/2
- **Issue:** A record left at its deleted stored line re-hashes into a new undecided `needs-recheck` row. The decided identity is then no longer an open record, so `assert_reopens` (which needs that record `stale`/`nearby`) can never hold, even for a correct repair.
- **Fix:** `_not_kept` asserts that the decided identity is not `current` at pass 2 and that `e2e_gate` is not `write`.
- **Cost if wrong:** low. The Close out test separately asserts no `write` through the real CLI.

**3. [Rule 3] Scenario signature takes the test instance**
- `deleted_original_scenario(test, kind, copy)` instead of `(kind)`, because `RealDiffRepo` registers its temp-dir cleanup on the test. The acceptance grep `def deleted_original_scenario` = 1 still holds.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** the stored-line-deleted check could use "the `ranges` passed to the pass". **Actual:** those ranges are new-side only and cannot tell a deletion from an insertion covering the same line number. **Why:** diff_ranges and worktree_snap emit new-side ranges only. **Cost if wrong:** none. This is what routed the plan to the checkpoint.
- **Found during:** Task 3 context. **Planned:** known-limit was recommended "when the freshness refusal already catches it". **Actual:** the refusal only delays the wrong keep by one review, because the next review relocates and keeps again. **Cost if wrong:** the owner weighs known-limit on an overstated safety net.

## TDD Gate Compliance

RED commit present (43305ff2, `test(66-07)`). No GREEN commit: the plan paused at BOUND-EXCEEDED by design.

## Deferred Issues

None new. The known worktree-only `test_replay.py::TestPhase53SameLineRegressionCases` failure was not run here.

## Known Stubs

None.

## ROADMAP note to apply

Do not apply yet. On the BOUND-EXCEEDED path the line is written **after the owner's Task 3 answer**. Append one line to `.planning/ROADMAP.md`, section `### 999.44: Pre-submission decision gate — unresolved legacy wrong-keeps`, after its last paragraph ("Bound the work to these three shapes: …"):

- If **known-limit**:
  `Shape 1 outcome (Phase 66, 2026-11-DD): owner-accepted known limit — reproduced through the real flow for defer and dismiss (decided line deleted while an identical line already existed elsewhere: decision kept current at the other line, Close out writes); a correct re-ask needs old-side "removed since review" lines from worktree_snap.py, beyond the D-14 bound — tests: TestShape1DeletedOriginal.test_shape1_deleted_original_is_reasked_at_pass2_known_limit, test_shape1_closeout_does_not_write_on_deleted_original_known_limit (expectedFailure), control test_shape1_copy_written_by_the_same_change_reasks_control; D-21 distinguished by test_d21_identical_copy_added_while_original_remains_keeps.`
- If **approve-wider**:
  `Shape 1 outcome (Phase 66, 2026-11-DD): reproduced through the real flow for defer and dismiss; owner approved a wider repair (<authorised file(s)>) planned separately with a d5acc19 differential — tests: TestShape1DeletedOriginal.test_shape1_deleted_original_is_reasked_at_pass2, test_shape1_closeout_does_not_write_on_deleted_original (RED until that plan); D-21 distinguished by test_d21_identical_copy_added_while_original_remains_keeps.`

The plan's Task 2 and Task 3 verify (`grep -q "Shape 1 outcome (Phase 66" .planning/ROADMAP.md`) passes only after the orchestrator applies this note.

## Commits

- 43305ff2 test(66-07): 999.44 shape 1 reproduction through the real chain + D-21 control

## Self-Check: PASSED

Commit 43305ff2 exists. `test_decision_continuity.py` contains `def deleted_original_scenario` (1) and `class TestShape1DeletedOriginal` (1). STATE.md and ROADMAP.md were not modified.
