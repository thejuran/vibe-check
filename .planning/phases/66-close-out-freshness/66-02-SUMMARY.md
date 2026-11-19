---
phase: 66-close-out-freshness
plan: 02
subsystem: finalize-tests
tags: [finalize, fixtures, reviewed_tree, parity]
requires: []
provides:
  - "test_finalize_inputs.bind_reviewed_tree / decided_files / open_files / reviewed_files / check_decided_fixture / expects_unchanged"
  - "TestDecidedFixturesBindReviewedTree (tier A everywhere, tier B for write-path routes; route keys containing 'stale' are tier A only)"
  - "test_decision_bearing_states_bind_reviewed_tree in test_finalize_card.py, test_confirmed_fix.py, test_finalize_parity_grid.py"
affects: [66-04]
tech-stack:
  added: []
  patterns: ["decision-bearing fixtures committed in a temp repo with passes[-1].reviewed_tree = HEAD^{tree}", "AST locks that make an unbound decision-bearing CLI fixture a test failure"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_finalize_inputs.py
    - plugins/vibe-check/scripts/test_finalize_card.py
    - plugins/vibe-check/scripts/test_confirmed_fix.py
    - plugins/vibe-check/scripts/test_finalize_parity_grid.py
decisions:
  - "bind_reviewed_tree stages and commits only the given paths (not `git add -A`), so it never sweeps a test's other work into the reviewed commit"
  - "Builders take an optional repo; pure build_result tests keep calling them bare, and an AST lock requires every CLI test class to pass one"
  - "fix_obsolete_state carries a current dismissal (BUGS_HASH), so it is a decision-bearing fixture and is bound; the no-decision example is load_fixture()/load_six_row()"
metrics:
  duration: "~23 min"
  completed: 2026-11-17
  tasks: 2
  files: 4
---

# Phase 66 Plan 02: Re-home decision-bearing Finalize fixtures onto reviewed trees Summary

Every Finalize test fixture that reaches the helper with a current defer/dismiss decision now sits on a temp repo whose last pass carries a real `reviewed_tree`. The decided file is in that tree and unchanged on disk. Lock tests in all four files fail if a fixture loses this. No test or assertion was removed or loosened.

## What was built

- **`test_finalize_inputs.py`**: added the helpers
  - `bind_reviewed_tree(repo, state, files=None)` writes and commits the files, then stamps `head_sha` and `reviewed_tree` from `HEAD`/`HEAD^{tree}`.
  - `decided_files`, `open_files`, `reviewed_files` and `synthetic_text` build the file set and its text.
  - `check_decided_fixture(repo, state, *, expect_unchanged=True)` checks the result, and `expects_unchanged(route_key)` returns False for any key containing "stale".

  `TestDecidedFixturesBindReviewedTree` has the four planned behaviours, plus an AST lock (`test_cli_tests_build_decided_states_on_a_repo`, mutation-checked). The lock requires every CLI test class to build decided states on a repo.
- **`test_finalize_card.py`**: added `_write_route_state` (now returns `(path, repo)`), `_bound_six_row` and `_verdict_route_state`. The fresh-shell Finalize-inputs fence runs inside that repo. Added `test_decision_bearing_states_bind_reviewed_tree`, which covers the write route, the answered six-row card and the answered verdict card, plus a mutant.
- **`test_confirmed_fix.py`**: added `test_decision_bearing_states_bind_reviewed_tree`, an AST lock with three mutants. It proves no decision-bearing state in this file reaches the helper (they only go to `carry_state.finalize_counts`).
- **`test_finalize_parity_grid.py`**: added the `DECIDED_FILE`/`DECIDED_TEXT` constants and `reviewed_of`. `fixture_state(..., reviewed)` gives each scenario repo in both grid classes the committed `20-selection.md`, and the state carries that review. Added `TestGridStatesBindReviewedTree` (builds every scenario and checks it, plus a mutant). `SHARED_WITH_2141`, `SOURCE_COMMIT`, `KNOWN_DIFFERENCES` and the byte-identity test were not edited.

### Fixtures re-homed per file

| File | Re-homed |
|------|----------|
| test_finalize_inputs.py | 4 builders (`dismissed_all_state`, `nv_open_state`, `medium_only_state`, `fix_obsolete_state`) gained `repo=None`. 4 `prepared()` states. 17 CLI call sites: 8 `fix_obsolete_state(ARCH)`, 6 `dismissed_all_state`, the `-x.ts` and folder-name `x.ts` states, and the ledger card route (six files committed) |
| test_finalize_card.py | 3 state builders used at 6 call sites in `TestFinalizeFreshShellWalk`: the write route x3 incl. the counting-line case, the six-row card x2, and the verdict recount x1 |
| test_confirmed_fix.py | 0. No decision-bearing state reaches the helper, and the new lock keeps it that way |
| test_finalize_parity_grid.py | `fixture_state` in both grids: 284 main-grid scenarios (266 creatable here) and 549 name-form scenarios |

## Verification (observed)

- `pytest -q -p no:cacheprovider test_finalize_inputs.py test_finalize_card.py test_confirmed_fix.py test_finalize_parity_grid.py`: **345 passed**, 1208 subtests (baseline before this plan: 337 passed; +8 new tests). Grid summaries are unchanged from baseline: main 254 agree / 12 D-19 / 0 unexpected / 18 not creatable; name-form 508 agree / 35 D-19 / 6 N-13 / 0 unexpected.
- `pytest -q test_finalize_parity_grid.py -k byte_identical`: 1 passed. `git status --porcelain` on carry_state.py, finalize_gate.py, guard.py, fixcommit.py and finalize_inputs.py printed nothing.
- No `def test_` lines and no `assert` lines were removed in any of the four files. Checked with `git diff -U0 e6201539`: 0 matching removed lines.
- RED was observed before GREEN. The lock failed on 6 fixtures (prepared dismissed-all/nv-open/medium-only/fix-obsolete, route write, card route recorded), and the AST lock failed too. Commit 19801b11 holds the failing lock and 1fae5ec5 holds the fix.
- **Scratch freshness mutant (never committed):** a copy of `_run` was set to refuse when a current, not-fix-closed decision has no well-formed `reviewed_tree`, a decided file is missing from it, or the file differs on disk. Results:
  - Before re-homing: 30 tests and 617 subtests failed across inputs, card and grid.
  - After: test_finalize_inputs 129/129 pass and test_finalize_card 99/99 pass. The name-form grid is 0 unexpected. The main grid still has 56 differences (see Assumption Drift).

## Deviations from Plan

**1. [Rule 1 - Bug] `bind_reviewed_tree` stages only the paths it was given**
- **Found during:** Task 1
- **Issue:** The plan's `git add -A` would commit any unrelated test work in the repo into the "reviewed" commit.
- **Fix:** `git add -- <paths>`, and commit `-- <paths>` only when something is staged.
- **Cost if wrong:** low. A fixture that relies on other files being in the reviewed tree would need them passed explicitly.
- **Commit:** 19801b11

**2. [Rule 3 - Blocking] ResultCase's ARCH_FILE text is now the bind's synthetic text**
- **Found during:** Task 1
- **Issue:** `prepared()` builds the fix-obsolete state from ARCH_FILE's blob, then binds `dismissed-all`, which decides ARCH_FILE. Rewriting that file would have invalidated the verdict's blob.
- **Fix:** ResultCase commits ARCH_FILE with `synthetic_text(80)`. A bind keeps a committed, unchanged, long-enough file as it is. No test read the old `"coverage\n"` text.
- **Cost if wrong:** low. Only blob values computed at runtime change.
- **Commit:** 1fae5ec5

**3. [Rule 2] Extra AST lock in test_finalize_inputs.py**
- **Found during:** Task 1
- **Issue:** The lock only checks states the way the lock itself builds them. On its own, a new CLI test calling `dismissed_all_state()` without a repo would slip through.
- **Fix:** Added `test_cli_tests_build_decided_states_on_a_repo` (mutation-checked).
- **Cost if wrong:** none. It is test-only.

**4. Lock class base is `CliCase`, not `ResultCase`**
- **Found during:** Task 1
- **Issue:** Iterating the ledger card route needs CliCase's runners.
- **Fix:** Based the class on `CliCase`, which is a ResultCase subclass.
- **Cost if wrong:** none.

## Assumption Drift (advisory)

**1. `fix_obsolete_state` is decision-bearing**
- **Found during:** Task 1
- **Planned:** the plan's `test_fixture_without_decisions_needs_no_tree` example was `fix_obsolete_state`.
- **Actual:** it dismisses BUGS_HASH (a current decision), so it is bound. The no-decision test uses `load_fixture()` and `load_six_row()` instead. Its semantics (verdict precedence) are unchanged: the bind does not touch ARCH_FILE or the verdict.
- **Cost if wrong:** 66-04's mutation check 8 should not treat it as a "no decision" fixture.

**2. test_confirmed_fix.py has no helper-run fixtures**
- **Found during:** Task 2
- **Planned:** "every fixture in these three files is a write-path fixture" to re-home.
- **Actual:** test_confirmed_fix.py never runs finalize_inputs (it calls only `COUNT_KEYS` and `carry_state.finalize_counts`), so nothing there needed binding. Its lock is structural instead.
- **Cost if wrong:** low.

**3. Main parity grid: 56 of 266 creatable scenarios diverge from 2.14.1 under any "unverifiable means refuse" check, whatever the fixtures (carry for 66-04)**
- **Found during:** Task 2, from the scratch-mutant probe.
- **Planned:** with fixtures bound, the grid would stay in 2.14.1 agreement once the check lands.
- **Actual:** with the reviewed tree bound and the decided file present, scenarios whose session cannot see the reviewed work tree still refuse under the mutant. Those sessions are: outside the repo (`outside`), `no-git` on PATH, inside `.git` (`inside-git`), `worktree-folder` (core.worktree set elsewhere), `ceiling-repo`, and `GIT_DIR` with an outside session. 2.14.1 writes or opens the card there.
- **Detail:** the name-form grid was fully clean. The mutant locates the repo with `rev-parse --show-cdup` from the session. Some `worktree-folder`/`inside-git` cases may behave differently under 66-04's real `git diff` at the repo top, but outside / no-git cannot be verified by any check.
- **Cost if wrong:** 66-04 Task 1/3 will see `TestParityGrid.test_every_scenario_agrees_except_d19_and_known` and `test_regression_rows_give_the_2141_decision` fail. That needs an explicit decision, not a fixture change:
  - (a) an owner-ruled named difference ("a decision-bearing Close out outside the reviewed work tree refuses as unverifiable"), or
  - (b) grid states that carry the dismissal only where the session is inside the repo work tree.

  This plan was told not to edit `KNOWN_DIFFERENCES`, so it was left for 66-04.

**4. Folder names ending in a line break (carry for 66-04)**
- **Found during:** Task 1
- **Detail:** with a toplevel-based mutant (`_toplevel` trims line breaks, as 2.14.1 did), `TestRepoFolderNameParity.test_parity_other_folder_name_endings` fails three subtests: "line break", "two line breaks" and "space, line break". A cwd-relative mutant passes them all.
- **Cost if wrong:** if 66-04 resolves the repo top through `_toplevel`, those three cases refuse instead of `outstanding-to-phase-5`. 66-04 should resolve the top from the session's own git (e.g. `--show-cdup`) or record the difference.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_finalize_inputs.py (bind_reviewed_tree x1, decided_files x1, check_decided_fixture x1 with `expect_unchanged=True`, TestDecidedFixturesBindReviewedTree x1)
- FOUND: test_decision_bearing_states_bind_reviewed_tree in test_finalize_card.py, test_confirmed_fix.py, test_finalize_parity_grid.py
- FOUND commits: 19801b11, 1fae5ec5, a528a126
