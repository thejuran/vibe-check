---
phase: 66-close-out-freshness
plan: 07
status: complete
owner_decision: "Task 3: known-limit (answered live by the owner via AskUserQuestion in the orchestrator session, 2026-11-18)"
subsystem: decision continuity / step-0 relocation
tags: [999.44, shape-1, relocation, D-21, D-14, decision-continuity, known-limit]
requires:
  - "66-05 (--all records reviewed_tree)"
provides:
  - "deleted_original_scenario + TestShape1DeletedOriginal: real-chain reproduction of 999.44 shape 1 for defer and dismiss, kept as owner-accepted known-limit expected failures"
  - "explicit D-21 control (test_d21_identical_copy_added_while_original_remains_keeps), pure-shift control and same-change-copy control"
affects:
  - "66-09 Task 2 (FRESH-03 verdict keys on the shape-1 outcome line: 'owner-accepted known limit')"
tech-stack:
  added: []
  patterns: ["real git diff -> exact-range builder -> relocate_decided -> score.run -> finalize_inputs CLI on a reviewed_tree-bound repo"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "Shape 1 REPRODUCED for both kinds when the identical copy was already in the reviewed file (the 999.44 record's shape); not when the same change writes the copy (passing control)"
  - "Verdict BOUND-EXCEEDED: no in-bound rule (test file + 30-collect-score.md only) tells a deleted original from a pure line shift; the correct check needs old-side 'removed since review' lines from worktree_snap.py"
  - "Owner chose known-limit: 999.44 shape 1 is an owner-accepted known limit; no production code or prose change"
metrics:
  duration: ~45m
  completed: 2026-11-18
  tasks: "3 of 3 (Task 2 verdict BOUND-EXCEEDED, no commit; Task 3 owner chose known-limit)"
  files: 1
---

# Phase 66 Plan 07: 999.44 shape 1 (deleted original vs D-21) Summary

999.44 shape 1 reproduces through the real chain for both decision kinds. When the decided line is deleted and an identical line already existed elsewhere in the reviewed file, step-0 relocation moves the decision to that other line and keeps it `current`, and Close out writes. The bounded review-side re-ask (D-14) could not be made correct inside the allowed files. At the Task 3 checkpoint the owner chose **known-limit**. The two reproduction tests stay committed as `@unittest.expectedFailure` evidence. Passing controls lock the D-21 identical-copy behaviour and ordinary line shifts.

## Task 1: reproduction (commit 43305ff2)

Added to `test_decision_continuity.py`:

- `deleted_original_scenario(test, kind, copy="kept"|"added")`, next to `far_twin_scenario`. Pass 1 decides `bugs` A at line 10, and line 10 is deleted before pass 2. Pass 2 uses:
  - the real `git diff` from a temp repo;
  - the exact-range builder (`diff_ranges.ranges_from_diff`);
  - `relocate_decided` against `carry_state.py decided`;
  - the same agent re-reporting at the line the record was read at.
- `class TestShape1DeletedOriginal(_RealChain)`. Close out runs the real `finalize_inputs.run(argv_for(...))` in the temp repo. First, `bind_reviewed_tree` binds the last pass to the post-deletion code, and `git status --porcelain` confirms disk matches the reviewed tree. The outcome therefore comes from the decision state, not from a freshness refusal.

Observed on current code:

| Test | defer | dismiss |
|------|-------|---------|
| test_shape1_deleted_original_is_reasked_at_pass2 | FAIL: kept `current` at line 49 | FAIL: same |
| test_shape1_closeout_does_not_write_on_deleted_original | FAIL: `action: write`, `next: write-review-md`, report entry line 49 `status: current` | FAIL: same |
| test_shape1_copy_written_by_the_same_change_reasks_control | pass | pass |
| test_d21_identical_copy_added_while_original_remains_keeps | pass | pass |
| test_shape1_pure_shift_keeps | pass | pass |
| test_p4_far_twin_new_copy_is_not_evidence (unmodified) | pass | |

Task 1 verify (`-k "d21_identical_copy or shape1_pure_shift or far_twin"`): the controls passed (4 passed, 6 subtests). The far-twin test is unmodified: `git diff -U0 ... | grep -c far_twin_new_copy_is_not_evidence` returned 0.

## Task 2: verdict BOUND-EXCEEDED (no commit)

I tried the smallest in-bound rule: in `relocate_decided` case 2, don't move a decided record whose stored line falls inside the pass's `changed_line_ranges`. It fixed the four shape-1 subtests, but `test_shape1_pure_shift_keeps` failed for defer and dismiss with "record dee0f534 is not an open record (decision orphaned)". Twenty lines inserted at the top give the range `[1, 20]`. That range covers stored line number 10, so the decision is not followed to line 30 and is re-asked. That is the T-66-19 over-ask.

The change ranges, including since-review `nearby_line_ranges`, record line numbers in the new version of the file only. A deletion at line 10 and an insertion covering line 10 therefore look the same. The record also stores no `canonical_window`, so the surrounding code can't tell them apart either. I reverted the experiment. `score.py`, `carry_state.py`, `worktree_snap.py` and `30-collect-score.md` were never modified.

## Task 3: owner decision — known-limit (commit dfb4291c)

The owner answered `known-limit` live via AskUserQuestion in the orchestrator session. The owner also confirmed the interpretation call. The reproduction is the 999.44-described shape: the copy was already present and the original line was deleted. The plan's same-edit variant stays as a passing control.

Applied:

- The tests were renamed `test_shape1_deleted_original_is_reasked_at_pass2_known_limit` and `test_shape1_closeout_does_not_write_on_deleted_original_known_limit` and marked `@unittest.expectedFailure`. Each docstring covers three points:
  - it names 999.44 shape 1;
  - it explains that the change ranges cannot tell a deleted original from a shift;
  - it explains why Close out's code-changed-since-review refusal does not limit the problem: the refusal applies only before a review has run on the deleted code, and that review relocates the decision again.
- Observed results:
  - `pytest -q -p no:cacheprovider -rx test_decision_continuity.py test_worktree_snap.py`: 228 passed, 2 xfailed, 226 subtests passed.
  - `python3 -m unittest test_decision_continuity.TestShape1DeletedOriginal`: OK (expected failures=2).
  - Plan Task 2 verify (`-k "Shape1 or d21_identical_copy or shape1_pure_shift or far_twin or collect_score"`): 4 passed, 2 xfailed, 6 subtests passed.
- `git status --porcelain` printed nothing for `score.py`, `carry_state.py`, `worktree_snap.py`, `30-collect-score.md`, `ROADMAP.md` and `STATE.md`.

### Evidence that was presented to the owner

- **Failure:** the decision stayed current at line 49 after line 10 was deleted, and Close out returned `write`. This held for both defer and dismiss.
- **Minimal wider change:** `worktree_snap.py collect` would also report, per file, the line numbers from the reviewed version that were removed since the review. Step 0 and `relocate_decided` would then skip case-2 relocation for a decided record whose stored line is in that set.
- **Why it exceeds D-14:** it edits a helper and adds an input to step 0.
- **Close out freshness check:** it does not limit the problem. It only delays the wrong keep by one review.

Options presented were `known-limit` and `approve-wider`. Owner answer: `known-limit`.

## Deviations from Plan

**1. [Rule 1 - Bug] The plan's own construction does not reproduce; the 999.44 shape does**
- **Found during:** Task 1
- **Issue:** `L1[48] = L0[9]; del L1[9]` writes the copy in the same change. The real diff names the copy's line, so the relocated record is already re-asked on current code. The 999.44 record says the text "remained at line 49", meaning it was already in the reviewed file at old line 50.
- **Fix:** `copy="kept"` (the default) is the reproduction. The plan's construction is kept as `test_shape1_copy_written_by_the_same_change_reasks_control`. The owner confirmed this call.
- **Cost if wrong:** shape 1 would have been "not reproduced" (D-10) instead.
- **Commit:** 43305ff2

**2. [Rule 1] The re-ask assertion is "not kept current + not write" instead of `assert_reopens`**
- **Issue:** a record left at its deleted line re-hashes into a new undecided `needs-recheck` row. The decided identity is then no longer an open record, so `assert_reopens` could never hold, even for a correct repair.
- **Cost if wrong:** low. The Close out test separately asserts no `write` through the real CLI.

**3. [Rule 3] The scenario takes the test instance**
- `deleted_original_scenario(test, kind, copy)` takes the test instance because `RealDiffRepo` registers its cleanup on it. The acceptance grep still holds.

## Assumption Drift (advisory)

- **Found during:** Task 2.
  - **Planned:** the check for a deleted stored line could use the pass `ranges`.
  - **Actual:** those ranges hold new-side line numbers only, so they cannot detect a deletion.
  - **Cost if wrong:** none. This drift is what routed the plan to the checkpoint.
- **Found during:** Task 3.
  - **Planned:** known-limit was recommended "when the freshness refusal already catches it".
  - **Actual:** the refusal only delays the wrong keep by one review. The owner was told this before choosing.
  - **Cost if wrong:** none remaining, because the decision was made with the correct facts.

## TDD Gate Compliance

The RED commit is present (43305ff2, `test(66-07)`). There is no GREEN commit, by design: the verdict was BOUND-EXCEEDED and the owner chose known-limit, so the RED tests are kept as expected failures (dfb4291c).

## Deferred Issues

None new. The known worktree-only `test_replay.py::TestPhase53SameLineRegressionCases` failure was not run in this plan.

## Known Stubs

None.

## ROADMAP note to apply

The owner chose known-limit at Task 3. Do not edit ROADMAP.md in the worktree. The orchestrator appends this exact line to `.planning/ROADMAP.md`, in the section `### 999.44: Pre-submission decision gate — unresolved legacy wrong-keeps`. It goes in as a new paragraph after the section's last paragraph, which begins "Bound the work to these three shapes: …".

```
Shape 1 outcome (Phase 66, 2026-11-18): owner-accepted known limit — reproduced through the real flow for defer and dismiss (decided line deleted while an identical line already existed elsewhere: decision kept current at the other line, Close out writes); a correct re-ask needs old-side "removed since review" lines from worktree_snap.py, beyond the D-14 bound, and the Close out code-changed refusal does not bound it (the next review relocates again) — tests: TestShape1DeletedOriginal.test_shape1_deleted_original_is_reasked_at_pass2_known_limit, test_shape1_closeout_does_not_write_on_deleted_original_known_limit (expectedFailure), control test_shape1_copy_written_by_the_same_change_reasks_control; D-21 distinguished by test_d21_identical_copy_added_while_original_remains_keeps.
```

The line contains the literal phrase "owner-accepted known limit", which 66-09 Task 2 keys on. The plan's Task 3 verify (`grep -q "Shape 1 outcome (Phase 66" .planning/ROADMAP.md`) passes only after the orchestrator applies this note.

## Commits

- 43305ff2 test(66-07): 999.44 shape 1 reproduction through the real chain + D-21 control
- aaa3ef92 docs(66-07): pause at owner checkpoint (paused SUMMARY)
- dfb4291c test(66-07): keep 999.44 shape 1 reproduction as an owner-accepted known limit

## Self-Check: PASSED

Commits 43305ff2, aaa3ef92 and dfb4291c exist. `test_decision_continuity.py` contains `def deleted_original_scenario` (1), `class TestShape1DeletedOriginal` (1), and two `_known_limit` tests under `@unittest.expectedFailure`. STATE.md and ROADMAP.md were not modified.
