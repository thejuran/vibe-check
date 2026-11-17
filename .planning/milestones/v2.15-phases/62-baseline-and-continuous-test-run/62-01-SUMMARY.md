---
phase: 62-baseline-and-continuous-test-run
plan: 01
subsystem: testing
tags: [ci, stdlib-only, pytest, junit, guard, mutation-testing]

requires: []
provides:
  - ".github/scripts/stdlib_only.py: whole-tree stdlib-only import gate (exit 0/1/2), 33 shipped files at 2.14.1"
  - ".github/scripts/left_out_guard.py: check-list / args / check-log / check-skips subcommands, RECORDED_FIVE, RECORDED_SKIPS = None, APPROVED_SKIP_REASONS"
  - ".github/ci-left-out-tests.txt: the five D-18 left-out test ids"
affects: [62-02 workflow, 62-08 skip-list pinning]

tech-stack:
  added: []
  patterns:
    - "CI gate scripts live in .github/scripts as single stdlib files run with python3 -I"
    - "Every guard rule has a test mutant AND was checked with an out-of-tree source mutant run"

key-files:
  created:
    - .github/scripts/stdlib_only.py
    - .github/scripts/test_stdlib_only.py
    - .github/scripts/left_out_guard.py
    - .github/scripts/test_left_out_guard.py
    - .github/ci-left-out-tests.txt
  modified: []

key-decisions:
  - "Stdlib scan reports 33 files (gitfixture.py included), not Phase 61's 32"
  - "check-skips also enforces skip_list_problems on RECORDED_SKIPS at runtime, so a widened list is refused even when the sets match"
  - "Skip count from the log ignores 'N subtests skipped'; only test-level 'N skipped' is compared with the result file"

patterns-established:
  - "Recording-run state: RECORDED_SKIPS = None makes check-skips print OBSERVED-SKIP lines and exit 1"

requirements-completed: [CI-01]

duration: ~35min
completed: 2026-11-14
---

# Phase 62 Plan 01: CI gate scripts Summary

**Stdlib-only import gate over all 33 shipped plugin modules, plus a guard that pins the five left-out tests, requires exactly 5 deselected in the suite log, and fails closed on any skipped (test id, reason) set that differs from a recorded list that does not exist yet.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-11-14
- **Tasks:** 2 of 2
- **Files created:** 5 (all under `.github/`; nothing under `plugins/` changed)

## Accomplishments

- `stdlib_only.py`: AST scan of every non-`test_*.py` module under the plugin root against `sys.stdlib_module_names` plus sibling basenames. Real tree: `33 shipped .py files; third-party imports: none`, exit 0. Planted imports in a plain module and in `gitfixture.py` exit 1 and name file and module. A plant in `test_x.py` does not trip (scope lock). Empty, missing or unparseable input exits 2 with `— STOPPING`.
- `left_out_guard.py`:
  - `check-list` / `args` accept only `RECORDED_FIVE`. `args` prints the `--deselect=` lines from the constant, never from the file text.
  - `check-log` reads the last pytest summary line and requires `5 deselected` with no `failed`/`error`.
  - `check-skips` reads pytest's `--junitxml` file and prints `OBSERVED-SKIP` lines. With `RECORDED_SKIPS = None` it exits 1 as a recording run. Otherwise it checks the class rule, compares the log and result-file skip counts, and compares the `(id, reason)` sets.
- `ci-left-out-tests.txt` holds the five ids. All five class and function names were confirmed with grep and an AST lookup in `test_replay.py` and `test_footprint.py`, and match the plan character for character. Both approved skip reasons were confirmed as string constants in `test_replay.py:281` and `test_lanearchive.py:416`, also matching the plan.

## Observed verification results

- `pytest -q -p no:cacheprovider .github/scripts/test_stdlib_only.py`: **21 passed**
- `pytest -q -p no:cacheprovider .github/scripts/test_left_out_guard.py`: **71 passed, 9 subtests passed**
- `pytest -q -p no:cacheprovider .github/scripts`: **92 passed, 9 subtests passed**
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`: printed `33 shipped .py files; third-party imports: none`, exit 0
- `python3 -I .github/scripts/stdlib_only.py /nonexistent`: `PLUGIN ROOT NOT FOUND: /nonexistent — STOPPING`, exit 2
- `left_out_guard.py check-list .github/ci-left-out-tests.txt`: exit 0. `args` printed 5 `--deselect=plugins/vibe-check/scripts/test_` lines.
- `grep '^RECORDED_SKIPS = None'`: 1 match. `check-skips /nonexistent.xml /nonexistent.log`: exit 2.
- `git status --porcelain -- plugins`: empty
- Mutant counts in the tests:
  - 6 list mutants and 10 log mutants
  - 7 skip-set mutants, 3 count cross-check tests and 6 class-rule mutants (2 on the reason)
  - the reason fixture check with its break test, and the ignore-reasons and six-item `RECORDED_FIVE` mutants
- **Source-mutant runs (beyond the plan).** A scratch script applied each mutant to the real module, ran its tests, then restored the module. `git diff` was clean afterwards.
  - `stdlib_only.py`: 6 of 6 mutants tripped (scan test files, never flag, pass on empty, ignore from-imports, scan `__pycache__`, swallow parse errors).
  - `left_out_guard.py`: 21 of 21 tripped after the fix noted below.

## Task Commits

1. **Task 1 RED:** `5d1fcee` test(62-01): add failing tests for the stdlib-only check
2. **Task 1 GREEN:** `a61112d` feat(62-01): stdlib-only check script (33 shipped files, gitfixture.py included)
3. **Task 2 RED:** `0cacc2c` test(62-01): add failing tests for the left-out list guard
4. **Task 2 GREEN:** `b657d6b` feat(62-01): left-out list guard (D-18) and skip-set guard (D-20) for CI

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Three decorative tests in test_left_out_guard.py**
- **Found during:** Task 2, source-mutant run
- **Issue:** Three source mutants survived, so three tests could never fail:
  - Removing the 50 MB size check still gave exit 2, because the truncated read then failed to parse.
  - Removing the empty-reason rule was hidden by the wrong-reason rule.
  - Counting `N subtests skipped` as test skips was hidden by match order.
- **Fix:**
  - The size test now asserts `RESULT FILE OVER` and the absence of `CANNOT PARSE`.
  - The empty-reason test asserts the `empty reason:` problem text.
  - The subtests test uses a log with no test-level skips and `4 subtests skipped`.
- **Cost if wrong:** Low. These are tighter assertions only, and all 21 mutants now trip.
- **Files modified:** .github/scripts/test_left_out_guard.py
- **Commit:** b657d6b

**2. [Rule 2 - Missing check] Runtime class rule in check-skips**
- **Found during:** Task 2
- **Issue:** The plan applied `skip_list_problems` only through a test on the constant. A hand-edited `RECORDED_SKIPS` holding an out-of-group entry would still pass `check-skips` if the runner really skipped it.
- **Fix:** `check-skips` runs `skip_list_problems(RECORDED_SKIPS)` and exits 1 with `RECORDED SKIP LIST BREAKS THE APPROVED-GROUP RULE — STOPPING`. This is tested in `TestRecordedListRuleAtRuntime`.
- **Cost if wrong:** Low. It is an extra refusal path, and a valid list is unaffected.
- **Commit:** b657d6b

**3. [Rule 1 - Bug] Test-helper `%` escape**
- **Found during:** Task 2 GREEN. The `[ 99%]` literal in the synthetic log broke `%` formatting, so it was escaped. This was test-only and is in commit b657d6b.

### Other notes
- `check-log` accepts a bordered summary line (`=== … ===`) and uses `(?<!\d)5 deselected`, so `15 deselected` is rejected. Both are tested.
- No summary line in `check-log` gives exit 1 (`DESELECT COUNT IS NOT 5`). In `check-skips`, a log with no summary line is unusable input (exit 2), because the skip count cannot be cross-checked.

## TDD Gate Compliance

Both tasks have a `test(62-01)` RED commit (5d1fcee, 0cacc2c) before the matching `feat(62-01)` GREEN commit (a61112d, b657d6b). RED failures were observed: `ModuleNotFoundError: No module named 'stdlib_only'` and `ImportError` for `left_out_guard`.

## Known Stubs

- `RECORDED_SKIPS = None` in `.github/scripts/left_out_guard.py`. This is intentional (D-20 bootstrapping): `check-skips` exits 1 until plan 62-08 pins the runner's observed set. `test_skip_list_is_not_yet_recorded` asserts it and is meant to be replaced by 62-08.

## Next Phase Readiness

- The workflow plan can call `stdlib_only.py plugins/vibe-check`, `left_out_guard.py args`, `check-log` and `check-skips <junit> <log>`. Pytest must be run with `--junitxml` for `check-skips`.
- Until 62-08 pins the list, the first runner run is red at the skip-guard step by design.

## Self-Check: PASSED

- FOUND: .github/scripts/stdlib_only.py, .github/scripts/test_stdlib_only.py, .github/scripts/left_out_guard.py, .github/scripts/test_left_out_guard.py, .github/ci-left-out-tests.txt
- FOUND commits: 5d1fcee, a61112d, 0cacc2c, b657d6b
