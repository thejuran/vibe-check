---
phase: 66-close-out-freshness
plan: 08
status: complete
owner_decision: "Task 2: approve-repair (answered live by the owner via AskUserQuestion in the orchestrator session, 2026-11-18)"
subsystem: decision continuity / covering decisions
tags: [999.44, shape-2, covering-decision, carry_state, parity-grid]
requires:
  - "66-02, 66-07"
provides:
  - "covering_order_scenario + TestShape2CoveringOrder: real-writer reproduction of 999.44 shape 2 (defer and dismiss) and the repair's lock"
  - "carry_state._covering: the newest covering decision wins (highest at_pass, lowest hash on a tie)"
  - "test_finalize_parity_grid: materialize_dd8e4ab; the 2.14.1 side runs dd8e4ab modules from a temp folder"
affects:
  - "66-09: the v2.15 differential materializes carry_state at d5acc19, so unchanged fixtures still compare; only shape-2 fixtures (two decisions covering one record) may differ and must be listed as intended"
tech-stack:
  added: []
  patterns: ["old side of a differential materialized from a literal commit via git show into a temp folder"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_finalize_parity_grid.py
    - plugins/vibe-check/scripts/carry_state.py
decisions:
  - "Shape 2 REPRODUCED through run_pass + decide_on (record_decisions) for both kinds: the older cover won whenever its hash sorted first (wrong keep, Close out wrote)"
  - "Owner chose approve-repair; _covering now prefers the highest at_pass, ranks an uncounted at_pass lowest, and keeps the lowest hash on ties"
  - "carry_state.py left the dd8e4ab byte-identity pin; the 2.14.1 parity side now runs modules materialized from dd8e4ab (grid commit precedes the carry_state commit); guard.py, finalize_gate.py and fixcommit.py stay pinned"
metrics:
  duration: ~1h15m (including the owner checkpoint)
  completed: 2026-11-18
  tasks: "3 of 3"
  files: 3
---

# Phase 66 Plan 08: 999.44 shape 2 (covering-decision order) Summary

999.44 shape 2 reproduced through the real writer for both decision kinds. When two owner decisions both list the same finding in their `covers`, `_covering` used to pick whichever decision hash sorted first. In one ordering that was a wrong keep: the finding stayed `current`, Close out returned `write` and the card hid it. The owner approved the repair. The parity grid's 2.14.1 side now runs modules materialized from dd8e4ab, and that change was committed first. Then `_covering` was changed to pick the newest decision.

## Task 1: reproduction (commit 6d9313b0)

`covering_order_scenario(kind, order, decide)` uses only `run_pass` and `decide_on`.

1. Pass 1: `security` X1 (line 12) leads a row holding `bugs` M (line 10).
2. Pass 2: a quiet pass. The row rises to critical and X1 is decided, so its cover for M has band critical.
3. Pass 3: line 12 is rewritten (diff `[[12, 12]]`) and X1's re-check answers `resolved`. A fresh `perf` X2 leads M's row at medium and is decided, so its cover for M has band medium.
4. Pass 4: no code change. M leads its own row at critical with a newly corroborating lane.

`order` changes only X1's title, which sets whether X1's hash sorts before X2's.

Two covers form because `record_decisions` never rewrites an older decision. On the code before the repair:
- `test_shape2_newest_cover_decides_covering_order` failed in the older_first ordering for defer and dismiss. M stayed `current` where the newer cover alone gives `stale`, Close out returned `write` and the card showed no row for M.
- In the newer_first ordering it passed.
- The two-covers and single-cover control tests passed.

## Task 2: owner checkpoint (paused SUMMARY cd1ede4f)

Before asking, these checks passed: the RED commit existed, the byte-identity test passed, and `carry_state.py` matched dd8e4ab. The owner answered **approve-repair**.

## Task 3: GREEN with materialization first

**Grid, commit ce43c6e4** (lands before the carry_state commit):
- `materialize_dd8e4ab(case)` writes the four `SHARED_WITH_2141` modules from `git show dd8e4ab:...` into a temp folder. Cleanup is `addCleanup`, or `addClassCleanup` for the class-level grids.
- `side_2141` and `_counts_and_gate_2141` now take the paths from `old_side_paths(old_dir)`. That covers `GUARD_PY` for the step-1 script, `carry_state.py finalize-counts` and `finalize_gate.py`.
- The module constants `GUARD_PY`, `CARRY_STATE_PY` and `FINALIZE_GATE_PY` were removed, so the old side cannot reach the working tree.
- `run_grid`, `nf_run` and `run_one` take `old_dir`.
- The pin test now loops over `PINNED_TO_2141` (guard.py, finalize_gate.py, fixcommit.py). It asserts that `carry_state.py` is the only module left out and carries the docstring note.
- New test `test_2141_side_runs_modules_materialized_from_dd8e4ab` checks each materialized blob against dd8e4ab.
- `FRESHNESS_REFUSALS` was not touched.
- Grid result: 23 passed, 760 subtests passed. Summary: 284 scenarios, 198 agree, 12 D-19, 56 D-09 refusals, 0 unexpected, 18 not creatable here. No `vc-2141-*` temp folder was left behind.

**Repair, commit 75e4a1da:**
- `_covering` takes each decision's first matching entry and keeps the decision with the highest `at_pass`.
- A non-count `at_pass` (None, bool, negative, string) ranks as -1.
- On a tie, the lowest hash wins, which is the old order.
- Single-cover behaviour is unchanged.
- New test `test_shape2_tie_and_uncounted_at_pass_covering_order` locks the tie and uncounted rules on a copy of the real state.

**Verification observed:**
- `-k "shape2 or covering_order"`: 4 passed, 18 subtests passed.
- Plan-level set (`test_carry_state.py test_decision_continuity.py test_finalize_parity_grid.py test_finalize_inputs.py test_closeout_fresh.py`): 602 passed, 2 xfailed (the shape-1 known limits), 1623 subtests passed.
- `test_finalize_parity_grid.py -k "byte_identical or Pinned"`: 3 passed, 10 subtests passed.
- `git diff --quiet dd8e4ab -- guard.py finalize_gate.py fixcommit.py`: exit 0.
- **Mutation:** with `_covering` reverted to sorted-first, 3 subtests failed: newest_cover_decides older_first for defer and dismiss, and tie/uncounted newer_first. After restoring, all 4 tests pass.

## Deviations from Plan

**1. [Rule 3] Test names carry a `_covering_order` suffix**
- **Issue:** VALIDATION.md selects with `-k covering_order`. Neither the class name nor the plan's method names contain that substring.
- **Fix:** each method name gets the suffix. The `-k shape2`, `-k shape2_single_cover_control` and `-k covering_order` selectors all match.
- **Cost if wrong:** cosmetic.

**2. [Rule 1] Four passes, not three**
- **Issue:** a lone-lane row is capped at warning on its first pass, so the older cover reaches critical only after the pass-2 persistence rise.
- **Fix:** M's "split" is M leading its own row at pass 4, with X2 riding as a member carrying its own obligation. There is no code change, so the empty diff is realistic.
- **Cost if wrong:** low. The single-cover controls pin each cover's own outcome.

**3. [Rule 2] Uncounted `at_pass` ranks lowest, plus a tie/uncounted lock test**
- **Issue:** the plan's `max(at_pass, hash)` is undefined for a malformed `at_pass`.
- **Fix:** such a decision ranks below any counted one. That fails toward the newest valid decision and never raises. A test locks the rule.
- **Cost if wrong:** a hand-damaged state could still pick an older valid cover over a damaged newer one. The writer never produces a damaged `at_pass`.

**4. [Rule 3] Grid runners take an explicit `old_dir`**
- **Fix:** `materialize_dd8e4ab` accepts a TestCase class as well as an instance, because the grids run in `setUpClass`. `run_grid` and `nf_run` take `old_dir` as a required argument, so no caller can fall back to the working tree.
- **Cost if wrong:** none. `main --grid` runs through the same classes.

## Threat model

- **T-66-20:** mitigated by the newest-cover rule and its lock tests.
- **T-66-21:** mitigated. The old side is the literal dd8e4ab blobs, hash-checked, and the grid commit precedes the carry_state commit.

## Known Stubs

None.

## Deferred Issues

None. Full `plugins/vibe-check/scripts` suite: 4211 passed, 5 failed, 1 skipped, 2 xfailed, 6465 subtests passed. All 5 failures are the known worktree-only `test_replay.py::TestPhase53SameLineRegressionCases` artifact; `test_replay.py` run alone shows the same 5.

## ROADMAP note to apply

Do not edit ROADMAP.md in the worktree. The orchestrator appends this exact paragraph in `.planning/ROADMAP.md`, section `### 999.44: Pre-submission decision gate — unresolved legacy wrong-keeps`, as a new paragraph directly after the paragraph beginning "Shape 1 outcome (Phase 66, ...":

```
Shape 2 outcome (Phase 66, 2026-11-18): repaired — _covering prefers the newest cover (highest at_pass, hash tie-break; owner-approved at 66-08 Task 2); reproduced first through record_decisions for defer and dismiss (older critical cover kept the finding current and Close out wrote when its hash sorted first); the 2.14.1 parity side now runs carry_state.py materialized from dd8e4ab — tests: TestShape2CoveringOrder.test_shape2_two_covers_producible_covering_order, test_shape2_newest_cover_decides_covering_order, test_shape2_tie_and_uncounted_at_pass_covering_order, control test_shape2_single_cover_control_covering_order.
```

The plan's Task 3 verify (`grep -q "Shape 2 outcome" .planning/ROADMAP.md`) passes only after the orchestrator applies this note.

## Commits

- 6d9313b0 test(66-08): 999.44 shape 2 producibility attempt through record_decisions
- cd1ede4f docs(66-08): pause at owner checkpoint (paused SUMMARY)
- ce43c6e4 test(66-08): run the 2.14.1 parity side from modules materialized at dd8e4ab
- 75e4a1da feat(66-08): newest covering decision wins (999.44 shape 2, IN-03)

## Self-Check: PASSED

Commits 6d9313b0, cd1ede4f, ce43c6e4 and 75e4a1da exist. In git log, ce43c6e4 (grid) comes before 75e4a1da (carry_state). The test files contain `class TestShape2CoveringOrder`, `def covering_order_scenario` and `def materialize_dd8e4ab`. STATE.md, ROADMAP.md, closeout_fresh.py and test_closeout_fresh.py were not modified.
