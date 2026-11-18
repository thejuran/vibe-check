---
phase: 66-close-out-freshness
plan: 06
subsystem: finalize / close-out
tags: [loop-freedom, clearable, untracked, pr-range, all-mode, 999.44-shape-3]
requires: [66-04, 66-05]
provides:
  - "TestClearable: refuse -> fresh review (real fences) -> re-decide -> write for line, nearby, deleted (rm, mv), untracked, unverifiable (store removed) x defer/dismiss"
  - "TestAllRouteClearable: --all line and nearby edits refuse and clear"
  - "TestShape3Untracked: 999.44 shape 3 reproduced on d5acc19, refused by the candidate, cleared by git add -N + review; CLI-level mutation check 6"
  - "TestPrRangeDisk: range/PR Close out refuses a nearby disk edit; revert or checkout of the reviewed commit clears; absent reviewed commit is unverifiable"
affects: [999.44 backlog entry (shape 3 outcome, applied by the orchestrator)]
tech-stack:
  added: []
  patterns: [real-chain clearable loop per refusal cause, delegated chain test via unittest.TestResult]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_closeout_fresh.py
decisions:
  - "No refusal cause loops: closeout_fresh.py needed no change, so no RED/fix commit pair exists"
  - "On --all a nearby-only edit refuses Close out, and the fresh --all review keeps the decision (that route never sends nearby_line_ranges); Close out then writes. Locked as asserted behaviour, not a loop"
  - "Shape 3 outcome: safe refusal (cause untracked) that clears by git add -N then review again (D-13); git add -N alone does not clear"
metrics:
  duration: ~40m
  completed: 2026-11-18
  tasks: 2
  files: 1
---

# Phase 66 Plan 06: Refusals are clearable, 999.44 shape 3 settled Summary

Every Close out refusal cause now has a committed test showing the owner can clear it: refuse, run the review the refusal asks for (the real prose fences in fresh shells), re-decide what the review re-asks, persist, and Close out writes. 999.44 shape 3 (a decision on an untracked file) is reproduced as a wrong keep on 2.15.0, refused by the candidate with cause `untracked`, and cleared by the D-13 step (`git add -N`, then review again).

## What was built

**Task 1 (af1f4167).** `_ClearChain(test_worktree_snap._Chain)` adds a chosen decision kind for pass 1, keeps every reviewed tree the collect fence prints, and runs Close out through `finalize_inputs.run`. `TestClearable` covers both kinds for each cause:

| Test | Cause at first Close out | What the fresh review did | Last Close out |
|---|---|---|---|
| `test_clearable_line` | `line` | old record gone (content changed, new hash), new record undecided | write after re-decide |
| `test_clearable_nearby` | `nearby` | same record re-asked, `stale_cause` = `nearby` | write after re-decide |
| `test_clearable_deleted_rm` | `deleted` | record gone (file removed) | write |
| `test_clearable_deleted_mv` | `deleted` | accepts either outcome; observed: old record gone, re-asked as a new record at `src/b.py` | write after re-decide |
| `test_clearable_untracked` | `untracked` | after `git add -N`, the snapshot includes the file; decision re-asked | write after re-decide |
| `test_clearable_unverifiable_store_removed` | `unverifiable` | decision KEPT (`assert_keeps`, collect printed `{}`) | write, nothing re-decided |

`TestAllRouteClearable.test_all_route_refuses_then_clears` runs `pass1(route="all")` and an `--all` re-review (`changed = {}`, `_all_mode_over`) for an exact-line edit (refuse `line`, re-asked, write) and a nearby edit (refuse `nearby`, kept, write).

**Task 2 (95eda0f2).**
- `TestShape3Untracked` (on `DecidedCase`): the decided record points at `notes/new.py`, written after the commit and never added; the reviewed tree is `HEAD^{tree}`.
  - `test_old_helper_writes_on_untracked_decided_file`: the literal d5acc19 helper returns `write` / `write-review-md` (R7 wrong keep reproduced, GATE-07).
  - `test_candidate_refuses_untracked`: refuse, `stop-review-again`, cause `untracked`, no report.
  - `test_git_add_n_then_review_clears`: `git add -N` alone still refuses (the reviewed tree lacks the file), then delegates to `TestClearable.test_clearable_untracked` through a `unittest.TestResult` and asserts it passed.
  - `test_mutant_skip_absent_check_writes`: `closeout_fresh` with `if file not in reviewed_paths:` replaced by `if False:`, patched into `finalize_inputs`, brings the write back (mutation check 6 at the CLI boundary).
- `TestPrRangeDisk` (range and PR switches, both kinds): the last pass's `reviewed_tree` is the range-end commit.
  - `test_range_closeout_refuses_on_nearby_disk_edit`: writes when clean, refuses `nearby` after an uncommitted edit at line 13.
  - `test_revert_edit_clears`: `git checkout -- src/a.py` then write.
  - `test_checkout_reviewed_commit_clears`: the edit committed after the review refuses; `git checkout <end>` (detached, clean) writes.
  - `test_pr_head_absent_locally_is_unverifiable`: a well-formed id not in the repo refuses `unverifiable`.

## Verification (observed)

Run from this worktree's `plugins/vibe-check/scripts` (the plan's verify commands name the main-checkout path).

| Command | Result |
|---|---|
| `pytest -q -p no:cacheprovider test_closeout_fresh.py -k "clearable or AllRouteClearable"` | 7 passed, 16 subtests passed |
| `pytest -q -p no:cacheprovider test_closeout_fresh.py -k "untracked or Shape3 or PrRangeDisk"` | 11 passed, 28 subtests passed |
| `pytest -q -p no:cacheprovider test_closeout_fresh.py` | 64 passed, 145 subtests passed |
| `grep -c "def test_clearable_"` | 6 |
| `grep -c "class TestAllRouteClearable"` | 1 |
| `grep -c "def test_mutant_skip_absent_check_writes"` | 1 |
| Full scripts suite (`pytest -q -p no:cacheprovider`) | 5 failed, 4221 passed, 1 skipped, 2 xfailed, 6481 subtests passed. All 5 failures are `test_replay.py::TestPhase53SameLineRegressionCases` (known worktree-only artifact); the 2 xfails are the 999.44 shape 1 known limit |

The ROADMAP grep (`grep -q "Shape 3 outcome" .planning/ROADMAP.md`) was not run here: the orchestrator applies the ROADMAP note below.

## ROADMAP note to apply

In `.planning/ROADMAP.md`, `### 999.44` section, add this as a new paragraph after the last "Shape N outcome (Phase 66 ..." paragraph (after the Shape 1 paragraph, or after the Shape 2 paragraph if 66-08's lands first):

```
Shape 3 outcome (Phase 66, 2026-11-18): reproduced on 2.15.0 (Close out wrote on a deferred or dismissed decision over an untracked file, for both kinds); the candidate refuses with cause untracked, `git add -N` alone does not clear it, and the D-13 step (`git add -N`, then review again) clears it with no loop — tests: TestShape3Untracked.test_old_helper_writes_on_untracked_decided_file, test_candidate_refuses_untracked, test_git_add_n_then_review_clears, test_mutant_skip_absent_check_writes; clearing proved through the real fences by TestClearable.test_clearable_untracked.
```

## Deviations from Plan

**1. [Orchestrator directive] ROADMAP.md not edited**
- **Found during:** Task 2
- **Issue:** The plan has Task 2 append the shape-3 note to ROADMAP §999.44 and commit it. The orchestrator forbids ROADMAP edits in this worktree (its merge would drop them).
- **Fix:** The exact text and placement are in "ROADMAP note to apply" above.
- **Cost if wrong:** If the orchestrator does not apply it, the 999.44 entry lacks the shape-3 outcome and the plan's ROADMAP grep fails.

**2. [Rule 3 - Test harness] Pass 2 for deleted, moved and `--all` cases uses a `review_again` helper**
- **Found during:** Task 1
- **Issue:** `_Chain.pass2` writes and re-reads `src/a.py` and always uses the default/GSD range row, so it cannot run when the file is deleted or moved, or on `--all`.
- **Fix:** `review_again` runs the same fences (the incremental range row, the take + collect fence) and `tdc.run_pass`, with `changed = {}` and `_all_mode_over` on `--all`. `pass2(` is still used for line, nearby, untracked and store-removed.
- **Cost if wrong:** If the real `--all` or deleted-file pass differed from this harness, those tests would prove less than they claim; the fences themselves are the real prose ones.

**3. [Rule 3 - Test fixture] A second tracked file for the deleted and untracked cases**
- **Found during:** Task 1
- **Issue:** `_Chain`'s repo holds only `src/a.py`. Removing or untracking it leaves an empty tree, and the collect fence then prints no reviewed tree.
- **Fix:** A committed `README` keeps the tree non-empty, as in any real repo.
- **Cost if wrong:** None for the product; the empty-repo case is not a realistic review target.

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** on `--all`, the fresh review re-asks after an edit (`pass2(route="all") -> re-ask -> write`). **Actual:** an exact-line edit is re-asked, but a nearby-only edit is KEPT by the `--all` review, because `--all` never sends `nearby_line_ranges` (66-05, D-12 "no scorer effect"). Close out still refused first and writes after the fresh review, so no loop. **Why:** the `--all` scorer has no nearby input by design. **Cost if wrong:** if the owner expects `--all` to re-ask nearby edits like other routes, that is a scorer change outside this phase's no-scorer-effect rule; the test asserts the keep so any change is visible.
- **Found during:** Task 1. **Planned:** the "line" cause is "re-asked". **Actual:** the line edit changes the content, so the re-reported finding has a new hash and the old record is gone; the new record is undecided and is decided. The plan allowed "re-asked or record gone".

## TDD Gate Compliance

The plan is `type: tdd`, but no refusal cause looped, so `closeout_fresh.py` needed no change and no `fix`/`feat` commit follows the `test(66-06)` commits. Both commits are evidence-only test commits that passed on first run against the 66-04 module. The RED state for shape 3 is the d5acc19 helper's write (`test_old_helper_writes_on_untracked_decided_file`) plus the CLI mutant that restores it.

## Known Stubs

None.

## Threat Flags

None. T-66-22 (no untracked copies: the refusal asks the owner to add the file), T-66-23 (clearable test per cause) and T-66-24 (absent reviewed commit fails closed, no fetch) are covered by the tests above.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_closeout_fresh.py
- FOUND commits: af1f4167, 95eda0f2
