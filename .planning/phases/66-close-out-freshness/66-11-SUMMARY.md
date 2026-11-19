---
phase: 66-close-out-freshness
plan: 11
subsystem: review-orchestration
tags: [999.44, shape-1, relocation, forced-re-ask, D-21, gap-closure, tdd]
requires:
  - "66-10: worktree_snap collect prints REMOVED_LINE_RANGES= (removed_from_diff)"
provides:
  - "30-collect-score.md: `$MOVED_DECIDED` (step 0), the forced re-ask rule (step 2), envelope note (step 4)"
  - "test_decision_continuity: forced_reask_pairs, stamp_map_with_pairs, removed-aware run_pass, SHAPE1_GRID, SHAPE1_INTENDED"
  - "test_nv_render: FORCED_REASK_PHRASES, forced_reask_holds + CASES row"
affects: [66-12, FRESH-03, 66-VERIFICATION SC3]
tech-stack:
  added: []
  patterns: ["two-sided differential against the literal d5acc19 functions (git show + ast + exec)", "mutants patched onto the simulator, each run unpatched first"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_nv_render.py
decisions:
  - "Relocation stays exactly as on 2.15.0; a move off a removed (or possibly removed) line is re-asked by adding a one-line pair [line, line] to nearby_line_ranges, so score.py stamps snapshot.nearby_at"
  - "Owner decision 2026-11-18 (Re-ask them): empty REMOVED_LINE_RANGES= re-asks every decision step 0 moved"
  - "changed_line_ranges is never changed by the rule; score.py, carry_state.py, diff_ranges.py, worktree_snap.py untouched"
requirements: [FRESH-03]
metrics:
  completed: 2026-11-18
  tasks: 3
  commits: 3
---

# Phase 66 Plan 11: forced re-ask of a decided record moved off a removed line Summary

A deferred or dismissed decision whose own line was removed since the last review is no longer carried silently onto identical text elsewhere. Step 0 still relocates it exactly as 2.15.0 did, but it now records the move. Step 2 then adds a one-line pair for the relocated line to the map the decision stamp reads. `score.py` stamps `snapshot.nearby_at`, so the decision is re-asked on its own row (`stale` / `nearby`) and Close out does not write until the owner decides again.

## The rule as shipped (30-collect-score.md)

- **Step 0, decided-record paragraph:** every case-2 move of a decided record (an entry or an obligation member) is also remembered in `$MOVED_DECIDED` as `{file, stored_line, line}`. `$MOVED_DECIDED` is empty at the start of each pass. Cases 1-4 are unchanged.
- **Step 2, since-review bullet:**
  - "Each prints exactly three lines".
  - "ALL THREE values are EMPTY" when the code moved or there is no snapshot.
  - `REMOVED_LINE_RANGES=<json>` is described: last-reviewed-side line numbers, `{}` = nothing removed, empty exactly when `NEARBY_LINE_RANGES=` is empty, "is never sent in the envelope".
  - The "never build it by hand" sentence now names the forced pairs as its only exception.
- **New paragraph "Forced re-ask of a moved decided record (999.44 shape 1)."** It sits directly after that bullet's text and says:
  - For each `$MOVED_DECIDED` entry, the move is re-asked when the printed `REMOVED_LINE_RANGES=` value is empty, or when one of its ranges for the entry's `file` contains the entry's `stored_line`.
  - To re-ask, add `[<line>, <line>]` under that file to the stamp map, unless a range there already contains that line.
  - The stamp map is the printed `NEARBY_LINE_RANGES` value (every range kept, pairs appended). When that value is empty, `nearby_line_ranges` is sent as `changed_line_ranges` plus the forced pairs.
  - `changed_line_ranges` is never changed. With no forced pair, nothing changes.
  - The paragraph gives the reason in one sentence and notes that `--all` has no carried records.
- **Step 4:** `nearby_line_ranges` is sent when `NEARBY_LINE_RANGES=` is non-empty or at least one pair was forced.
- The three collect fences are unchanged (`grep -c 'worktree_snap.py" collect'` = 3 before and after), and the `--all` sentence locked by test_worktree_snap is still verbatim.

## Tests

**Simulator (test_decision_continuity.py):**
- `next_cf(..., moves=None)` records lead and member moves. It adds a simulator-only `member` flag and does not record the lead's own member twice.
- `forced_reask_pairs(moves, removed)` decides which moves are forced.
- `stamp_map_with_pairs(env, pairs)` merges the pairs into `nearby_line_ranges`, or into a copy of `changed_line_ranges` when the caller sent none. It leaves `env` untouched when no pair remains.
- `run_pass(..., removed=NOTHING_REMOVED)`: `removed` is never an envelope key.
- `relocate_decided` is not edited.
- Helpers: `real_pass2` (ranges and removed lines from one real `git diff`, with the envelope captured), `shape1_case`, `SHAPE1_GRID`, `two_decisions_scenario`, `member_move_scenario`.

**TestShape1DeletedOriginal.** The bodies live in the `_Shape1Bodies` mixin. There is no `expectedFailure` and no `_known_limit`. Every test runs for defer and dismiss:
- `test_shape1_deleted_original_is_reasked_at_pass2`: run with the finding re-reported at the line it was read at (`read_at`) and with no pass-2 finding (`none`). Removed = `{F: [[10, 10]]}`; the decision reopens at 49.
- `test_shape1_closeout_does_not_write_on_deleted_original`: the real `finalize_inputs` CLI. The result is not write and not `stop-review-again`. After `decide_on`, Close out writes.
- `test_shape1_edited_in_place_with_copy_elsewhere_reasks`: reopens at 50.
- `test_shape1_no_removal_evidence_reasks`: reopens at 49 (shape 1) and at 30 (pure shift).
- `test_removed_lookup_uses_the_stored_line`: keeps at 30.
- `test_shape1_forced_pair_merges_with_other_reasks`: A reopens at 49 and B at 29.
- `test_shape1_member_move_is_reasked`: the decided obligation member moved 10 to 49, the move is recorded with `member: True`, and the decision is not current.
- `test_forced_pair_never_changes_a_score`
- `test_forced_map_is_well_formed_for_the_scorer`: `score._stamp_ranges` returns the built map.
- Three controls, with their assertion lines byte-identical to the pre-plan commit. Their pass-2 feed now carries real `removed=` and `nearby_line_ranges=ranges`:
  - `test_d21_identical_copy_added_while_original_remains_keeps`
  - `test_shape1_pure_shift_keeps`
  - `test_shape1_copy_written_by_the_same_change_reasks_control`
- `test_p4_far_twin_new_copy_is_not_evidence` is unmodified and passes.
- `test_simulator_matches_locked_prose` now also checks the `forced_reask_pairs` docstring phrases and `forced_reask_holds`.

**test_nv_render.py:**
- `FORCED_REASK_PHRASES` (8 phrases, checked inside the paragraph) and `FORCED_REASK_CONTEXT_PHRASES` (3 phrases, whole file).
- `forced_reask_holds` with its `CASES` row.
- `test_forced_reask_deleting_mutant` and `test_forced_reask_in_paragraph_deleting_mutant`.
- `` `$MOVED_DECIDED` `` was added to `DECIDED_RELOCATION_PHRASES` in the GREEN commit.

## Differential against literal 2.15.0 (TestShape1DifferentialV215)

The old side is the `relocate_decided`, `next_cf` and `run_pass` source read from `d5acc19:plugins/vibe-check/scripts/test_decision_continuity.py`. It is fetched with `git show` (list argv, clean git env), parsed with `ast`, and run with `exec` in a copy of this module's globals. `test_differential_old_procedure_is_literal_d5acc19` checks that the bytes parsed have the blob id `git rev-parse` reports. Before writing, the three functions at d5acc19 were also compared with the pre-plan versions and are identical.

The grid has 15 scenarios, each run for defer and dismiss: unchanged, pure_shift, d21_copy_added, far_edit, nearby_edit, decided_line_edited_no_copy, decided_line_deleted_no_copy, same_edit_copy, tie, lookup_stored_line, no_evidence_unchanged, shape1_kept, shape1_edited, no_evidence_shape1 and no_evidence_shift. For each, the test compares the canonical JSON of the envelope, the new state and the score result.

**SHAPE1_INTENDED = (shape1_kept, shape1_edited, no_evidence_shape1, no_evidence_shift).** Every other scenario is byte-identical. On each intended scenario, 2.15.0 is `current` with gate `write` and the repair is `stale` / `nearby` with gate not write.

The check works in both directions:
- Inside the test, `assert_only_intended` is shown to raise when one name is dropped from the tuple and when `pure_shift` is added.
- Removing `shape1_kept` from the real `SHAPE1_INTENDED` in the file made the test fail with `unlisted differences ['shape1_kept']`. The file was then restored.

`test_differential_closeout_only_shape1_differs` runs the real CLI on shape1_kept: the 2.15.0 state writes, and the repaired state does not and is not `stop-review-again`.

## Mutant table (TestForcedReaskMutants)

Each test runs the body unpatched (it must pass), then patched inside `assertRaises(AssertionError)`, for both kinds.

| Mutant | Patched | Body that fails |
|---|---|---|
| Ma never forces | `forced_reask_pairs` returns `{}` | `_body_reasked` (shape1_kept) |
| Mb None read as `{}` | `forced_reask_pairs` with `removed or {}` | `_body_no_evidence` |
| Mc forces every move | `forced_reask_pairs(moves, None)` | `_body_pure_shift`; the differential on {pure_shift, lookup_stored_line, intended} trips `assert_only_intended` |
| Md looks up the relocated line | moves with `stored_line = line` | `_body_lookup` and `_body_reasked` |
| Me pair into `changed_line_ranges` | `stamp_map_with_pairs` also extends `changed_line_ranges` | `_body_score` |
| Mf pairs replace the base map | `stamp_map_with_pairs` sets `nearby_line_ranges` = pairs only | `_body_two_decisions`; asserted direction: B comes back `current` (wrong keep) |
| Mg member moves not recorded | `next_cf` wrapper drops `member: True` moves | `_body_member` (member decision stays current) |

Every new prose phrase has a deletion mutant through the `forced_reask_holds` CASES row and the in-paragraph deleting test.

## Harness audit (run_pass default temporarily `None`)

The audit ran on a scratch copy of the plugin, with the default changed only in that copy. 19 tests failed. Four of them only failed because the scratch copy is not a git repo, so `git show d5acc19:…` could not run:
- `TestShape1DifferentialV215` (3 tests)
- `TestForcedReaskMutants::test_mutant_c_forces_every_move`

The remaining 15 failing tests are all `shift` fixtures:

| Test | Fixture change | Class |
|---|---|---|
| TestLineShift::test_r1a_shift_above_threshold_keeps_decision_and_hash | 3 lines inserted above | shift |
| TestLineShift::test_r1b_shift_sub_threshold_keeps_decision | 3 lines inserted above | shift |
| TestLineShift::test_r1c_shift_with_rereport_is_one_decided_row | 3 lines inserted above | shift |
| TestNearbyEdit::test_r8_guard_deleted_directly_above_reopens (`mapping dropped` subtest) | line 9 deleted, decided line 10 survives (moved to 9) | shift |
| TestCrossModuleGuards::test_decided_subcommand_matches_decision_state | INSERTED + L0 | shift |
| TestPhase57EndToEnd::test_owner_is_asked_exactly_when_evidence_changes | INSERTED + L0 (e2e_pass2) | shift |
| TestPhase57Mutants::test_decided_read_returning_empty_loses_the_relocation | INSERTED + L0 (e2e_pass2) | shift |
| TestRepro60Evidence::test_net_deletion_keeps_under_header_rule_even_at_u0 | lines 32-34 replaced by one line; decided line 40 survives (moved to 38) | shift |
| TestRealDiffRanges60::test_rd60_deletion_keeps | line 33 deleted; line 40 survives | shift |
| TestRealDiffRanges60::test_rd60_net_deletion_keeps | lines 31-33 replaced by one line; line 40 survives | shift |
| TestRealDiffRanges60::test_rd60_relocated_keeps | TOP_TEN inserted | shift |
| TestCoordinateSpaces60::test_cs60_default_head_only_control | TOP_TEN inserted (+ edit at 35) | shift |
| TestCoordinateSpaces60::test_cs60_default_staged_concat_probe | TOP_TEN inserted (+ edit at 35) | shift |
| TestCoordinateSpaces60::test_cs60_mixed_concat_probe | TOP_TEN inserted (+ edit at 35) | shift |

There are no `removal` fixtures, so no existing test was edited. In every fixture the stored line survives, so real evidence would never list it. The `{}` default is therefore truthful for the forced re-ask rule, even where the fixture removes another line. The default was restored: `grep -c "removed=None, \*\*over"` = 0.

Known behaviour (owner decision 2026-11-18): when the removal evidence is missing — the code changed during the pass, or the prior pass recorded no reviewed tree, which also leaves the following pass without evidence — a deferred or dismissed decision whose line only shifted is asked again; 2.15.0 kept that decision; the owner chose the re-ask ("Re-ask them") as a deliberate, tested difference.

Known side effect (stamp window): the forced pair is an ordinary range in the stamp map. Another decided record within 5 lines of the relocated line (D-14 window) is therefore re-asked too. This can only add a question; it never keeps a decision.

Out of scope and unchanged: a tie between identical copies (case 3, no move) behaves exactly as on 2.15.0 (differential scenario `tie`). `--all` has no carried records, so `$MOVED_DECIDED` is empty there.

## Verification (observed)

- RED (a866e00c): 17 failed and 13 passed in the shape 1 selection. The failing tests were the 6 repaired-behaviour tests named in the commit body plus `test_forced_map_is_well_formed_for_the_scorer`. The controls, `far_twin` and `removed_lookup` passed. The not-Shape1 selection passed 162, the same count as before. test_nv_render had 13 failures, all forced_reask.
- GREEN (b508c96c):
  - shape 1 selection: 13 passed
  - `test_decision_continuity.py -rx`: 174 passed, 0 xfailed
  - `test_nv_render.py`: 40 passed
  - `test_worktree_snap.py`: 97 passed. Its `-k "TestProse or AllRoute"` selection: 8 passed.
  - Every other test file that names 30-collect-score.md (test_agent_prompts, test_confirmed_fix, test_diff_ranges, test_cross_call_vars, test_git_safety_prose, test_score, test_verified_fixes, plus nv_render): 1128 passed.
- Task 3 (c54697eb): `pytest -q test_decision_continuity.py test_nv_render.py -rx`: 224 passed, 411 subtests passed, 0 xfailed.
- `git diff --quiet d5acc19 -- plugins/vibe-check/scripts/score.py` exits 0. `git status --porcelain` on score.py, carry_state.py, diff_ranges.py and worktree_snap.py prints nothing.
- Full `scripts/` suite (`pytest -q`, run on the Task 3 tree): 4303 passed, 1 skipped, 5 failed, 7118 subtests passed. All 5 failures are in `test_replay.py::TestPhase53SameLineRegressionCases`, which replays the recorded `runs-v2.10-phase43` corpus. They are unrelated to this plan; see Deferred Issues.
- Evidence class: offline only. There was no live reviewer run (GATE-08).

## Deviations from Plan

**1. [Rule 3 - Blocking] Worktree base reset.** At spawn the worktree was on c1461c5e, so it was reset to 8a7c61ea as the startup check directs.
- **Cost if wrong:** none; the plan files exist only from that base.

**2. [Acceptance artefact] The literal control-assert `sed` range for `test_shape1_pure_shift_keeps`.** After Task 3, the plan's `sed -n "/def T/,/^    def /p"` range runs past the end of the class into the new module-level code. It picks up `assert` lines that are not in the test (the differential helpers), and before the plan it picked up shape 2 helper asserts. With the range bounded at the next top-level line (`/^[^ ]/`), the test's own 3 assert lines are identical to the pre-plan commit. The other two controls pass the literal command unchanged, and all three passed it after the RED commit.
- **Cost if wrong:** none; the assertions are byte-identical.

**3. [Design detail] `stamp_map_with_pairs(env, pairs)` takes the envelope, not a map.** This lets mutant Me move a pair into `changed_line_ranges` without relying on dict aliasing. The merge semantics are the ones the plan specified.
- **Cost if wrong:** none; the simulator only.

**4. [Design detail] Envelope capture uses a `side_effect` spy that deep-copies at the call,** instead of `wraps=score.run`. This keeps the capture safe if `score.run` mutates its input.
- **Cost if wrong:** none.

## Deferred Issues

- On the full suite, `test_replay.py::TestPhase53SameLineRegressionCases` fails in three tests:
  - `test_a2_pair_sits_on_adjacent_lines_of_one_statement` (`('architecture', 233) not found in []`)
  - `test_off_line_credit_mutation_trips` (2 subtests)
  - `test_pre_same_line_scorer_gave_critical_100` (2 subtests)

  The class replays a recorded run corpus (`runs-v2.10-phase43/...`) through `score.py`. This plan does not touch it: `score.py` is byte-identical to d5acc19, and test_replay imports none of the edited files. It is logged in deferred-items.md and is out of scope.

## Known Stubs

None.

## Threat Flags

None. T-66-18, T-66-19, T-66-24 and T-66-25 are mitigated by the tests and mutants above. There is no new subprocess surface in product code: the `git show` / `rev-parse` / `hash-object` calls are in test code, use list argv and a clean env.

## Commits

- a866e00c test(66-11): 999.44 shape 1 repaired-behaviour tests and prose lock — RED
- b508c96c feat(66-11): re-ask a decision moved off a removed line instead of keeping it (999.44 shape 1)
- c54697eb test(66-11): two-sided 2.15.0 differential and mutation checks for the shape 1 repair

## TDD Gate Compliance

RED (`test(66-11)` a866e00c), then GREEN (`feat(66-11)` b508c96c), then the differential and mutation `test` commit (c54697eb). No refactor commit was needed.

## Self-Check: PASSED

The three modified files and this SUMMARY exist; commits a866e00c, b508c96c and c54697eb are in git log.
