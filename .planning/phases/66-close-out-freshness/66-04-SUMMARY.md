---
phase: 66-close-out-freshness
plan: 04
subsystem: finalize / close-out
tags: [finalize, close-out, refusal, prose-lock, differential, parity-grid]
requires: [66-01, 66-02, 66-03]
provides:
  - "finalize_inputs._run refuses stale deferred/dismissed decisions (action refuse, next stop-review-again, stale list)"
  - "NEXT_ACTIONS has 8 values; REASON_STALE_DECISIONS"
  - "90-finalize.md stop-review-again bullet + retry rule; review_again_bullet_holds lock"
  - "Parity grid FRESHNESS_REFUSALS: 56 named D-09 fail-closed refusals"
  - "TestWiringMutants (M1, M8, M9a, M9b) + no-git byte-identity differential"
affects: [66-08 (touches the parity grid next)]
tech-stack:
  added: []
  patterns: [named exhaustive difference list in the parity grid, prose lock with one mutant per required phrase]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/finalize_inputs.py
    - plugins/vibe-check/scripts/closeout_fresh.py
    - plugins/vibe-check/scripts/test_finalize_inputs.py
    - plugins/vibe-check/scripts/test_finalize_parity_grid.py
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
    - plugins/vibe-check/scripts/test_closeout_fresh.py
decisions:
  - "REASON_STALE_DECISIONS is worded like finalize_gate.REASONS (no 'refused:' prefix, no line break), because TestCliDisclosure forbids any 'refused:' string constant in finalize_inputs"
  - "closeout_fresh._toplevel drops exactly one trailing line break instead of all of them, so repo folders whose names end in a line break are diffed in place"
  - "Parity-grid D-09 refusals are listed as (scenario, cause) without pinning 2.14.1's write/open, because that outcome for '-1.ts' depends on the Python version's argparse; blobs and counts must still equal 2.14.1's"
  - "Refusal prose names /review or /deep-review (whichever this run came from), because both commands finalize through 90-finalize.md"
metrics:
  duration: ~75m
  completed: 2026-11-18
  tasks: 3
  files: 7
---

# Phase 66 Plan 04: Close out refuses stale decisions (999.40 GREEN) Summary

Close out now refuses when a deferred or dismissed decision rests on code that changed since the review. It returns exit 0 with `action: refuse`, `next: stop-review-again`, the gate counts, `report: null` and a `stale` list. The prose tells the owner exactly what to run next and states that Close out never starts the paid reviewers. The 66-01 999.40 reproduction is GREEN, and unchanged code still gives byte-identical output to the d5acc19 helper.

## What was built

**Task 1 (a7b5854b, feat).**
- `finalize_inputs._run` calls `closeout_fresh.stale_decisions(state, blobs, cwd)` right after the fingerprint-file write. A non-empty result returns the refusal. `build_result` is untouched, and no `stale` key is added otherwise.
- `NEXT_ACTIONS` gains `stop-review-again` as its eighth value. The docstring is updated (refusal shape, the no-git sentence, the import set).
- Tests:
  - the eight-value tuple test was renamed
  - a `"stale refusal"` route in `TestCliWritesOnlyTheFingerprintFile`, built by `stale_refusal_state(repo)`, which binds the reviewed tree and then edits the decided line. `TestDecidedFixturesBindReviewedTree` passes unchanged.
  - `test_stale_refusal_shape` and `test_unchanged_result_has_no_stale_key`
  - `TestImportSet` now includes `closeout_fresh`
- The parity grid and `_toplevel` fixes are described under Deviations.

**Task 2 (9b0f02aa test RED → fdea2e98 feat GREEN).**
- `90-finalize.md` has a `stop-review-again` bullet after `stop-refused`. It gives:
  - the "Cannot finalize —" header
  - rows in the form `{{file}}:{{line}} — {{title}} ({{kind}}; {{cause sentence}})`, using the join rule
  - five cause sentences, at most 10 rows, then "+{{N}} more"
  - the same-scope command for each route (default/GSD, PR, range, `--all`, and `/deep-review`)
  - the untracked next step (D-13) and the PR/range next step (D-15)
  - the paid-reviewer sentence (D-02)
  - "Do NOT write REVIEW.md or archive state. No asks, no writes, and stop."
- The retry paragraph now says "A `next` of `stop-review-again` is never retried." (also added to `RETRY_NEEDLES`).
- `TestReviewAgainProse` has 13 `test_mutant_*` methods plus `test_every_needle_is_required` (one subtest per phrase). It rejects dispatch / Phase 1 / run-the-reviewers wording and a bullet placed before `stop-refused`.

**Task 3 (6f99f229, test).** `TestWiringMutants` covers these mutants:
- M1: removing the wiring call brings the write back.
- M8: when `decided_records` ignores `_fix_closes`, a fix-obsolete-closed record refuses. Both 2.15.0 and the candidate write there.
- M9a: a git call with no candidates shows up in the Recorder.
- M9b: an always-present `stale: []` key breaks d5acc19 byte identity.

It also adds `test_differential_no_git_when_no_decision_closed`, covering the phase45 fixture, six-row and the missing state file. It checks that zero freshness git calls run and that stdout bytes are identical to d5acc19.

## Verification (observed)

| Command | Result |
|---|---|
| `pytest test_closeout_fresh.py -k repro_999_40 -v` | 2 passed, 12 subtests (6 old-helper-writes + 6 candidate-refuses) |
| Plan-level: `pytest test_closeout_fresh.py test_finalize_inputs.py test_finalize_card.py test_finalize_parity_grid.py test_confirmed_fix.py` | 414 passed, 1419 subtests |
| Every test file reading 90-finalize.md (16 files) | 1202 passed, 2 xfailed (999.44 shape 1 known limit) |
| Full scripts suite `pytest -q` | 5 failed, 4206 passed, 1 skipped, 2 xfailed. All 5 failures are `test_replay.py::TestPhase53SameLineRegressionCases`, the known worktree-only artifact |
| Parity grid under Python 3.12 (pytest) | 284 scenarios: 198 agree, 12 D-19, 56 D-09 refusals, 0 unexpected, 18 not creatable |
| Parity grid under Python 3.14 (`python3 test_finalize_parity_grid.py --grid`, the CI version) | OK. 196 agree, 14 D-19, 56 D-09 refusals, 0 unexpected. Name-form grid: 0 unexpected |
| `git status --porcelain carry_state.py finalize_gate.py guard.py fixcommit.py` | empty. Byte-identity pins hold (`test_confirmed_fix` and the grid's pinned-module test pass) |
| `stdlib_only.py` | 35 files, no third-party imports |
| Acceptance greps | wiring call count 1; no `def build_result` diff; no `check_decided_fixture` removal; `stop-review-again` bullet once and after `stop-refused`; retry sentence once |

## Deviations from Plan

**1. [Rule 1 - Lock conflict] Reason constant reworded**
- **Found during:** Task 1
- **Issue:** The plan's `"refused: ...\n"` text trips `TestCliDisclosure.test_no_owner_sentence_in_the_module`, which forbids any string constant starting with `refused:` in finalize_inputs.
- **Fix:** The text is now `"a deferred or dismissed decision is stale; its reviewed code changed since the review"`, matching the style of `finalize_gate.REASONS`. It is still a fixed constant with no path, title or hash. The lock was left as it was.
- **Cost if wrong:** wording only. The prose never prints `reason`.
- **Commit:** a7b5854b

**2. [Rule 3 - Blocking, orchestrator item 2] Repo folder names ending in a line break**
- **Found during:** Task 1
- **Issue:** `closeout_fresh._toplevel` used `rstrip("\n")`. Three `TestRepoFolderNameParity` subtests failed: line break, two line breaks, and space plus line break.
- **Fix:** It now strips exactly the one line break git adds. The path still comes from the session's own git (`--show-toplevel`). I did not use `--show-cdup`, because that would put the root in the wrong place when `core.worktree` points elsewhere.
- **Files:** closeout_fresh.py (outside the plan's file list)
- **Cost if wrong:** a path that is not valid UTF-8 still fails closed (`unverifiable`), as before.
- **Commit:** a7b5854b

**3. [Rule 3 - Blocking, orchestrator item 1] Parity-grid D-09 refusals named**
- **Found during:** Task 1
- **Issue:** 56 of the 266 creatable main-grid scenarios now refuse where 2.14.1 wrote or opened the card. In all 56, the session's git cannot see the reviewed work tree: session outside the repo or inside `.git`, no-git, `core.worktree` or `GIT_DIR` pointing elsewhere, or a ceiling. I checked every one: 2.14.1 gave write or open (52 cause `unverifiable`, 4 cause `deleted`, where the session's work tree lacks the reviewed file). The fingerprints and counts match 2.14.1 exactly; only the action differs. No other difference appeared, so no checkpoint was needed.
- **Fix:**
  - Added `FRESHNESS_REFUSALS`, a named list of (scenario, cause), with a reason citing D-09 fail-closed, plus the `freshness_refusal` predicate. It requires 2.14.1 to have written or opened, the helper's blobs and counts to equal 2.14.1's, `action == refuse`, `next == stop-review-again`, and exactly the grid's dismissal as stale with that cause.
  - `classify` gained a `fresh` bucket.
  - `test_freshness_refusals_are_found_exactly` makes the list exhaustive in both directions. A refusal that is not listed is unexpected, and a listed scenario that stops refusing fails.
  - A mutant test checks that the predicate rejects other shapes.
  - `side_helper` now carries `next`/`stale` only when `stale` is present, so agreeing scenarios compare exactly as before.
  - Six worktree-folder `REGRESSION_ROWS` are in the list. For those six, `test_regression_rows_give_the_2141_decision` still asserts the 2.14.1 outcome, and asserts the named refusal instead of `new == old`.
  - `KNOWN_DIFFERENCES`, `D19_ROWS` and the byte-identity test are unchanged.
- **Cost if wrong:** if the owner did not mean D-09 to cover "session cannot see the reviewed work tree", these 56 refusals would need a different rule. They are listed by name, so they are easy to revisit.
- **Commit:** a7b5854b

**4. [Rule 1] Bullet slice in the prose lock**
- **Found during:** Task 2
- **Issue:** The new bullet is the last in its list. Slicing to the next `"\n- "` ran into the finalize card section, which contains "dispatch".
- **Fix:** The slice also ends at the blank line that closes the list.
- **Commit:** fdea2e98

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** the fixes would stay within finalize_inputs and its tests. **Actual:** closeout_fresh.py and the parity grid also changed, both directed by the orchestrator. **Why:** 66-02 carried both issues forward. **Cost if wrong:** 66-08 edits the grid next and must keep `FRESHNESS_REFUSALS` exhaustive.
- **Found during:** Task 2. **Planned:** route commands are `/review` only. **Actual:** the prose also names `/deep-review`, because 90-finalize.md is shared by both commands. **Cost if wrong:** wording only.

## TDD Gate Compliance

- The RED gate for 999.40 was in 66-01 (`test(66-01)` 369996e8). Its GREEN is `feat(66-04)` a7b5854b.
- Prose: RED `test(66-04)` 9b0f02aa (48 failed) came before GREEN `feat(66-04)` fdea2e98.
- Task 3 added only extra mutation evidence (`test(66-04)` 6f99f229). It has no feat commit because no new behaviour was added.

## Known Stubs

None.

## Threat Flags

None. T-66-14 to T-66-17 are mitigated as planned: a fixed reason, a `stale` list of tokens only, the 10-row cap, the dispatch-wording lock, and the write-only-fingerprint route.

## Self-Check: PASSED

- FOUND: all 7 modified files
- FOUND commits: a7b5854b, 9b0f02aa, fdea2e98, 6f99f229
