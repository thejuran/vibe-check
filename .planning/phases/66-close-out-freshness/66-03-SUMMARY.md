---
phase: 66-close-out-freshness
plan: 03
subsystem: finalize / close-out
tags: [finalize, close-out, freshness, reverse-diff, window, tdd, mutation]
requires: [66-01]
provides:
  - closeout_fresh.stale_decisions implemented (decided_records, stale_from_ranges, changed_ranges, reviewed_files, _store_env_ro, _git, _toplevel, _treeish)
  - test_closeout_fresh.py behaviour spec (TestWindow, TestDeleteRename, TestUntrackedCause, TestUnverifiable, TestNoDecisionNoGit, TestFixPrecedence, TestMirrorLock, TestLineSet, TestArgvHygiene, TestOrdering, TestStorePath, TestModuleMutants)
affects: [66-04 (wires stale_decisions into finalize_inputs._run)]
tech-stack:
  added: []
  patterns: [reverse whole-tree diff in reviewed-tree numbering, read-only store env (no makedirs), source-substitution mutants]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/closeout_fresh.py
    - plugins/vibe-check/scripts/test_closeout_fresh.py
decisions:
  - "A file gone from disk is reported `deleted` only when the reverse diff also hits the record. If the diff shows no hit, the cause is `unverifiable`. This keeps --no-renames and -R testable by mutation, and it still fails closed."
  - "Spots in the line set (same-hash copies, covered members) count as cause `nearby`, even when the spot's own line changed. Only the record's own line gives `line`."
  - "_store_env_ro sets GIT_ALTERNATE_OBJECT_DIRECTORIES to the store only, and only when the store exists. The repo's own objects stay primary because GIT_OBJECT_DIRECTORY is unset. No extra `rev-parse --git-path` call is made."
  - "decided_records returns (record, decision, spots) triples. The plan said (record, decision); the spot set is computed alongside so stale_from_ranges stays pure."
metrics:
  duration: ~45m
  completed: 2026-11-17
  tasks: 3
  files: 2
---

# Phase 66 Plan 03: Close out freshness decision Summary

`closeout_fresh.stale_decisions` now decides, for every record a current deferred or dismissed decision closes, whether the reviewed code is provably unchanged on disk. It uses one reverse whole-tree diff (`git diff -R --no-renames --text <reviewed_tree> --`, prefixes swapped) at the repo top, so line numbers are in the reviewed tree's numbering. It applies the review's own ±5 window and fails closed. The wiring into `finalize_inputs._run` is left to 66-04.

## RED -> GREEN -> mutation

**RED (ecf13be5).** 12 test classes were added on a new `DecidedCase(FreshCase)` base. Each `decided()` call builds its own repo. A `Recorder` with the `(root, args, env=None)` signature is patched in with `mock.patch.object(closeout_fresh, "_git", rec)`. Run against the 66-01 contract, the selection gave 67 failed and 23 passed. The stale-expecting tests failed with `AssertionError: Lists differ: [] != [...]`. Tests that need `_git` or `stale_from_ranges` failed with AttributeError. The tests that expect `[]` (outside 4/16, unchanged, pure shift, fix precedence, the `_NEARBY_LINES` lock) passed trivially, as the plan expected. The plan's verify command (`! pytest ... -k "exact_line_is_stale or git_rm_is_deleted or absent_from_reviewed_tree or missing_reviewed_tree"`) exited 0.

**GREEN (53b2f5a4).** The module was implemented in two layers:
- **Pure layer:** `decided_records`, `_spots`, `stale_from_ranges` and `_cause`.
- **Git layer:** `_git`, `_toplevel`, `_store_env_ro`, `_reviewed_id`, `_treeish`, `changed_ranges` and `reviewed_files`.

`stale_decisions` builds the candidate list first. If there are no candidates it returns `[]` and runs no git. Any `Unverifiable` error reports every candidate as `unverifiable`, and an outer `except Exception` does the same, so the function never raises.

**Mutation checks (a95400ce).** `TestModuleMutants` has 9 `test_mutant_*` tests. Each one runs the real module and the mutant on the same fixture and asserts both results:

| Mutant | Substitution | Named behaviour that breaks |
|---|---|---|
| M2a | drop `"-R"` | git rm: real `deleted`, mutant `unverifiable` (`test_git_rm_is_deleted`) |
| M2b | drop `"-R"` + usual prefixes (true forward diff) | pure shift: real `[]`, mutant `line` (`test_window_pure_shift_of_20_lines_keeps`); git rm also loses `deleted` |
| M3 | usual `a/`/`b/` prefixes under -R | exact edit: real `line`, mutant `[]`, a silent keep (`test_window_exact_line_is_stale_cause_line`) |
| M4 | drop `"--no-renames"` | git mv: real `deleted`, mutant differs (`test_git_mv_is_deleted`) |
| M5 | `_NEARBY_LINES` 5 -> 4 / 5 -> 6 | edit at 15: real `nearby`, mutant `[]`. Edit at 16: real `[]`, mutant `nearby` (`test_window_nearby_5_and_15_cause_nearby` / `test_window_outside_4_and_16_keep`) |
| M6 | skip the reviewed-tree membership check | untracked decided file: real `untracked`, mutant `[]` (`test_decided_file_absent_from_reviewed_tree_is_untracked`) |
| M7 | inner `except Unverifiable` returns `[]` | missing reviewed_tree: real `unverifiable`, mutant `[]` (`test_unverifiable_missing_reviewed_tree`) |

No REFACTOR commit was needed. One cleanup (passing the candidates into `_stale` instead of recomputing them) went into the GREEN commit before it was made.

## Verification (observed)

| Command | Result |
|---|---|
| `pytest -q test_closeout_fresh.py -k "not candidate_refuses"` | 43 passed, 88 subtests passed |
| `pytest -q test_closeout_fresh.py -k Mutants` | 9 passed |
| `pytest -q test_closeout_fresh.py -k candidate_refuses` | 6 subtests fail as before (still RED; the wiring is 66-04) |
| `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | exit 0, "35 shipped .py files; third-party imports: none" |
| Acceptance greps | `import score`: none; `makedirs`: 0; `"-R"`: 1; `"--no-renames"`: 1; `"--text"`: 1; `--no-optional-locks`: 2; 355 lines; `class Test`: 13; `def test_mutant_`: 9 |
| Full scripts suite (`pytest -q`) | 11 failed, 4178 passed, 1 skipped. All 11 are accounted for: 5 are in `test_replay.py` (the known worktree-only `TestPhase53SameLineRegressionCases` artifact; `pytest test_replay.py` alone also gives 5 failed), and 6 are the expected `test_repro_999_40_candidate_refuses_*` RED subtests (`pytest test_closeout_fresh.py` alone gives 6 failed) |
| `pytest -q test_finalize_inputs.py test_worktree_snap.py test_diff_ranges.py` | 317 passed, 329 subtests passed |

The verify commands in the plan use the main-checkout path. I ran them from this worktree's `plugins/vibe-check/scripts`.

## Deviations from Plan

**1. [Rule 1 - Testability] `deleted` is decided after the range check (plan rule 6 put it first)**
- **Found during:** Task 3 design
- **Issue:** With "file missing from disk -> deleted" checked before the ranges, the `-R` and `--no-renames` guards could never be observed. Mutants M2 and M4 would trip nothing, which makes them decorative guards.
- **Fix:** A hit plus a missing file gives `deleted`. No hit plus a missing file gives `unverifiable`. Real git produces the same `deleted` in both orders (a reverse whole-file range always covers the decided line). The new order also fails closed.
- **Cost if wrong:** If some real deletion produced no reverse-diff hit, the cause token would read `unverifiable` instead of `deleted`. The refusal still happens; only the cause sentence differs.
- **Commit:** 53b2f5a4

**2. [Rule 1 - Plan expectation] M2 is two mutants**
- **Issue:** Dropping `-R` while keeping the swapped prefixes does not refuse a pure shift. Instead it keys every range under `a/`. That mutant trips the git rm test (and exact edits). A pure-shift refusal needs a true forward diff: `-R` dropped AND the usual prefixes.
- **Fix:** Added both mutants. The forward diff refuses the pure shift with cause `line`, because lines 1-20 in working-tree numbering cover line 10.
- **Cost if wrong:** None. Both mutants are extra evidence.

**3. [Rule 3 - Simplification] `_store_env_ro` does not add the repo objects dir as an alternate**
- **Issue:** The plan asked for "repo objects dir plus the store". With `GIT_OBJECT_DIRECTORY` unset, the repo's own objects are already primary, so the extra `rev-parse --git-path` call adds nothing.
- **Fix:** The store is the only alternate, set only when it exists. `test_unverifiable_tree_not_in_store` and `test_real_chain_store_tree_*` cover both paths. The store-removed test also checks that `.turingmind` is not recreated.
- **Cost if wrong:** If some layout needed the explicit repo alternate, store-path tests would fail; they pass.

**4. [Rule 3 - Blocking] Test env patch renamed in `TestStorePath`**
- **Issue:** `_Chain` already defines a `_env` method. Assigning `self._env` broke its fence runner.
- **Fix:** Used a local patcher with `addCleanup`.
- **Commit:** ecf13be5

**5. [Rule 2] Extra tests beyond the plan list**
- Added: unchanged keeps; a stale-decision-is-not-a-candidate test (no git); malformed states return `[]` with no git; fix-precedence control without the verdict (the same edit is `line`); the exact diff argv; the store unchanged-keeps control. `-x.py` was dropped from the PATH_RE bad list because `PATH_RE` allows `-`. Such a name is never put on argv, so it is harmless.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** `decided_records` returns `(record, decision)` and `stale_from_ranges` derives the line set. **Actual:** `decided_records` returns `(record, decision, spots)`, because the spot set needs the state and `stale_from_ranges` must stay pure. **Why:** it keeps the pure layer testable (`TestMirrorLock` calls it directly). **Cost if wrong:** 66-04 calls only `stale_decisions`, so nothing downstream reads the tuple shape.

## Known Stubs

None. `stale_decisions` is fully implemented. It is not called by `finalize_inputs` yet; that is 66-04's job, so `test_repro_999_40_candidate_refuses_*` stays RED by design.

## Threat Flags

None beyond the plan's register. The mitigations for T-66-08, -10, -11, -12 and -13 are in place and tested: `TestArgvHygiene`, REV_FLAGS with `--no-renames --text`, `--no-optional-locks`, no makedirs, `timeout=GIT_TIMEOUT` mapped to unverifiable, and nothing printed.

## TDD Gate Compliance

RED `test(66-03)` ecf13be5 -> GREEN `feat(66-03)` 53b2f5a4 -> extra evidence `test(66-03)` a95400ce. There is no refactor commit.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/closeout_fresh.py
- FOUND: plugins/vibe-check/scripts/test_closeout_fresh.py
- FOUND: ecf13be5 (test(66-03) RED)
- FOUND: 53b2f5a4 (feat(66-03) GREEN)
- FOUND: a95400ce (test(66-03) mutation checks)
