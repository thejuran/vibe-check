---
phase: 62-baseline-and-continuous-test-run
plan: 02
subsystem: ci
tags: [github-actions, ci, text-lock, mutation-test]
requires: []
provides:
  - ".github/workflows/offline-suite.yml — the one CI workflow (CI-01)"
  - ".github/scripts/test_workflow_shape.py — 16 check functions, 60 workflow mutants, completeness test"
affects:
  - "62-01 (stdlib_only.py, left_out_guard.py, .github/ci-left-out-tests.txt are called by the workflow)"
  - "62-08 (first real run, skip-list recording, red/green proof)"
tech-stack:
  added: ["pytest==9.0.3 on the runner (test-only)", "actions/checkout v7.0.1 and actions/setup-python v7.1.0, both pinned by commit id"]
  patterns: ["check function returning problems with clause-id prefixes", "one mutant per clause with a the-break-happened guard", "completeness test over CLAUSES/MUTANTS"]
key-files:
  created:
    - .github/workflows/offline-suite.yml
    - .github/scripts/test_workflow_shape.py
  modified: []
decisions:
  - "The deselect list goes through a captured variable, then mapfile, so a failing `args` call stops the step under bash -e instead of silently running with no deselects"
  - "The locks are stricter than the minimum in four places: PYTEST_ADDOPTS lines count as pytest options, `|| :` and `|| exit 0` count as swallowing like `|| true`, `github.head_ref` counts as an event field, and a second `permissions:` anywhere trips nothing-else"
requirements: [CI-01]
metrics:
  duration: "~25 min"
  completed: 2026-11-14
  tasks: 2
  files: 2
---

# Phase 62 Plan 02: Offline-suite workflow and shape locks Summary

One read-only GitHub Actions workflow (push to any branch, PR to main, both actions pinned to commit ids, no secrets). It runs the stdlib-only check and the left-out list guard before the suite, runs the suite from a detached linked worktree through a teed log with a PIPESTATUS check, then runs the count guard and the skip guard. Every rule is pinned by a stdlib-only text lock with its own mutant.

## What was built

- `.github/workflows/offline-suite.yml`: steps in order are Checkout (`fetch-depth: 0`, `persist-credentials: false`), Setup Python 3.14, Test-only tools (apt `zsh`, `pytest==9.0.3`), Stdlib-only check, Left-out list guard, Offline suite, Left-out count guard, Skip guard. It contains no `--deselect`, `--ignore`, `-k`, `-m`, `-x`, `continue-on-error` or `${{` expression.
- `.github/scripts/test_workflow_shape.py`: 16 check functions (15 named in the plan, plus the directory-based `one_workflow_holds`), 48 clauses and 60 mutants on the workflow or on temp trees. Each problem string starts with its clause id, and every mutant asserts that the trip names its own clause and only clauses that belong to that check. `TestEveryClauseHasAMutant` has two break tests: one with a mutant removed and one with a check left out of `CLAUSES`. `TestImportSet` limits imports to {os, re, shutil, sys, tempfile, unittest} and includes a mutant.

## Verification (observed)

- RED (Task 1, commit 88111ab): `pytest -q -p no:cacheprovider .github/scripts/test_workflow_shape.py` gave `1 failed, 7 passed, 13 errors`. The 13 errors were `AssertionError: the CI workflow file is missing: …/offline-suite.yml`. The 1 failure was `one_workflow_holds` on the missing directory. Task 1 verify checks passed: 16 `_hold(s)` defs, the required class and function names, and the `test(62-02)` commit.
- GREEN (Task 2, commit af9149c): the same command gave `21 passed, 61 subtests passed` (60 workflow mutants plus 1 import mutant).
- Hand mutation: changing `contents: read` to `contents: write` failed `TestWorkflowText::test_permissions` (`1 failed, 20 passed`). After restoring the file the result was `21 passed`, and `git diff --quiet -- .github/workflows/offline-suite.yml` exited 0.
- Task 2 verify checks, run as separate commands because the worktree sandbox refused the combined `&&` chain: 1 file in `.github/workflows`; 0 `secrets.`; 2 pinned `uses:` lines; `check-skips` present; `git ls-files` for conftest and config files printed nothing; `git status --porcelain -- plugins` printed nothing; `grep -c "import yaml"` gave 0; 0 matches for `pull_request_target|macos|continue-on-error|${{ github.event`.
- Syntax check: Ruby's YAML loader parsed the workflow into the expected structure (8 steps, triggers, `permissions: {contents: read}`). This was a one-off check and is not part of the test.
- `ruff check` on the test file: all checks passed.
- Not verified here: a real GitHub Actions run. The scripts from plan 62-01 do not exist in this worktree, and nothing was pushed. That proof belongs to plan 62-08.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The YAML-import mutant held the literal `import yaml`**
- **Found during:** Task 1 acceptance check
- **Issue:** `grep -c "import yaml"` returned 1 because the mutant string itself contained the text, which broke the acceptance criterion that requires 0.
- **Fix:** The mutant now builds the line as `"import " + "yaml"`. The mutant still trips.
- **Cost if wrong:** none; the change is cosmetic and the lock is unchanged.
- **Files modified:** .github/scripts/test_workflow_shape.py
- **Commit:** af9149c

**2. [Rule 3 - Blocking] The ruff commit hook rejected `l` loop variables (E741)**
- **Found during:** Task 2 commit
- **Fix:** Renamed them to `ln`. Tests were rerun: 21 passed, 61 subtests.
- **Cost if wrong:** none.
- **Files modified:** .github/scripts/test_workflow_shape.py
- **Commit:** af9149c

**3. [Process] Worktree base reset**
- The worktree started at eb790e4. As the spawn instructions require, it was reset to c0d33d35 before any work began.
- **Cost if wrong:** none; the plan files exist only at c0d33d35.

No lock was loosened to make the workflow pass. Nothing under `plugins/` changed.

## Known limits (for plan 62-08)

- The Left-out count guard and Skip guard steps have no `if: always()`, so neither runs when the suite step fails. The first skip list can only be printed once the suite step passes on the runner. If 62-08 needs the skip list from a red run, add `if: always()` to the Skip guard. That needs no `${{` and keeps every current lock holding.
- `no_config_file_holds` covers the repo tree only. pytest can also find a config file in a directory above the checkout on the runner, which nothing in the repo can rule out.

## TDD Gate Compliance

RED `test(62-02)` 88111ab comes before GREEN `feat(62-02)` af9149c. No refactor commit was needed.

## Threat Flags

None. The workflow adds no surface beyond what the plan's threat register covers.

## Self-Check: PASSED

- FOUND: .github/workflows/offline-suite.yml
- FOUND: .github/scripts/test_workflow_shape.py
- FOUND: 88111ab, af9149c
