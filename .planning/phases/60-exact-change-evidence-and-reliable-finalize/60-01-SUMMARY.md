---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 01
subsystem: vibe-check change evidence + Finalize (tests + verdict ledger)
tags: [reproduce-first, real-diff-fixtures, fresh-shell-walk, EVID-01, EVID-02, FINL-01]
requires: []
provides:
  - "header_rule_ranges: executable twin of the current 30-collect-score.md header rule (999.24 evidence)"
  - "RealDiffRepo temp-repo helper (make/write/read/stage/commit/git/diff) and RANGE_GIT_FLAGS"
  - "_builder() lazy import of diff_ranges.ranges_from_diff; scored_in_diff() real-scorer in_diff observation"
  - "_RealChain base (decision at 40, assert_reopens / assert_keeps)"
  - "TestRepro60Evidence (4 green documenting repros)"
  - "TestRealDiffRanges60 (10 red, five boundary pairs + context-independence subtests)"
  - "TestCoordinateSpaces60 (4 probes, all reproduced; 4 green controls)"
  - "TestFinalizeFreshShellWalk (walk red; empty-BLOBFILE refusal and cross-call gate input green)"
  - "REPRO_60 + TestRepro60Record + _REPRO_60_PENDING_FIXTURES = {TestRouteAll}"
  - "60-REPRO.md verdict ledger V1..V9 citing RED SHA ce9f8b8"
affects: [60-02, 60-03, 60-04, 60-05]
tech-stack:
  added: []
  patterns: ["reproduce-first red fixtures committed before any fix", "lazy import keeps only the builder-dependent tests red", "fresh-shell fence walk with printed-path literals"]
key-files:
  created:
    - .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "RED SHA for the 60-05 reverse run is ce9f8b8 (test files only)"
  - "PR-SERIES, MIXED-COORD and DEFAULT-STAGED all reproduced on the real chain; disposition 'reproduced; fixed by 60-04' for each"
  - "in_diff is observed through the real scorer's +20 score difference (the serialized in_diff field is the agent's value, not the recomputed one)"
metrics:
  duration: "~35 min"
  completed: 2026-10-29
  tasks: 3
  files: 3
requirements: [EVID-01, EVID-02, FINL-01]
---

# Phase 60 Plan 01: Reproduction verdicts Summary

999.24 and 999.25 are reproduced on current code as executing evidence, before any production edit. Real `git diff` text from throwaway repos, run through a twin of the documented header rule, shows three things: ranges three lines wider on each side than the edit, a deletion rule that never fires, and a decision 8 lines away being re-asked. Ten real-diff boundary fixtures stay red until the range builder exists. All three coordinate-space probes reproduced. The Finalize fresh-shell walk is red because no fence prints `BLOBFILE=`.

## RED SHA and the exact failure list

RED SHA: **`ce9f8b8`** (`test(60-01): red real-diff, coordinate and Finalize-walk fixtures for 999.24/999.25`, test files only). The fixtures were added in `43d1905` (Task 1) and `2121c57` (Task 2). `ce9f8b8` adds `REPRO_60` and completes the red set.

Full suite at `ce9f8b8` (`cd plugins/vibe-check/scripts && pytest -q`): **15 failed, 3655 passed, 4832 subtests passed in 172.55s**. The 15 failures:

1-10. `TestRealDiffRanges60::test_rd60_{ordinary,deletion,insertion,net_deletion,relocated}_{reopens,keeps}`: all `ModuleNotFoundError: No module named 'diff_ranges'`
11. `TestCoordinateSpaces60::test_cs60_pr_series_probe`: `False is not true : the head-file line of commit A's edit (15) is not in the patch-series ranges`
12. `TestCoordinateSpaces60::test_cs60_mixed_concat_probe`: `'current' != 'stale'`
13. `TestCoordinateSpaces60::test_cs60_default_staged_concat_probe`: `'stale' != 'current'`
14. `TestCoordinateSpaces60::test_cs60_default_staged_finding_probe`: `False is not true : line 48 (the staged section's own numbering) is not in the working-tree ranges`
15. `test_finalize_card.py::TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report`: `unexpectedly None : no Finalize fence prints BLOBFILE= (D-09) ...`

## Coordinate-probe dispositions (for 60-04)

| id | Outcome | Disposition |
|----|---------|-------------|
| PR-SERIES | series ranges `[[10,10],[1,5]]`; finding at head line 15 scores 70, not 90 (off-diff) | `reproduced; fixed by 60-04` |
| MIXED-COORD | concatenation `[[35,35],[1,10]]`; the decision (now line 50) stays `current` although the committed edit is at 45 (silent keep) | `reproduced; fixed by 60-04` |
| DEFAULT-STAGED | Probe A: `[[1,10],[58,58],[48,48]]` gives `stale` (wrong reopen from index line 48). Probe B: a finding at 48 is off-diff under `git diff HEAD` ranges | `reproduced; fixed by 60-04` |
| ALL-ROUTE | no diff (`05-state-all.md` (ii)) | `unsupported fixture; recorded, no fix` (`TestRouteAll` pending, 60-04) |

The controls pass, so one diff in one coordinate space gives the right answer in every case: cumulative `git diff <base> HEAD`, `git diff <base>` (commit vs working tree), `git diff HEAD` alone, plus the `git diff HEAD` boundary at 45 (55 on disk).

## Tasks

| # | Task | Commit |
|---|------|--------|
| 1 | Real-diff helpers, header-rule twin, 999.24 documenting repros, red boundary fixtures | `43d1905` |
| 2 | Coordinate-space probes and the Finalize fresh-shell walk | `2121c57` |
| 3 | REPRO_60 + TestRepro60Record (RED SHA) and 60-REPRO.md | `ce9f8b8`, `cda9220` |

## Verification (observed)

- `pytest -q test_decision_continuity.py -k TestRepro60Evidence` -> `4 passed`
- `pytest -q test_decision_continuity.py -k TestRealDiffRanges60` -> `10 failed`, every one `ModuleNotFoundError: No module named 'diff_ranges'`
- `pytest -q test_decision_continuity.py -k TestCoordinateSpaces60` -> `4 failed, 4 passed` (4 probes fail = reproduced; 4 controls pass)
- `pytest -q test_finalize_card.py -k TestFinalizeFreshShellWalk` -> `1 failed, 2 passed` (the walk, naming `BLOBFILE=`)
- `pytest -q test_decision_continuity.py -k TestRepro60Record` -> `3 passed`
- `pytest -q test_decision_continuity.py -k "TestNearbyEdit or TestRepro59Record or TestGolden"` -> `8 passed` (GOLDEN_DIGEST untouched)
- `pytest -q test_finalize_card.py -k "not TestFinalizeFreshShellWalk"` -> `70 passed`
- Ledger check -> `LEDGER_OK`, 9 `## V` sections, 0 occurrences of "reliability complete"
- Satisfiability check (outside the repo): with a throwaway marker-walk prototype `diff_ranges.py` on `PYTHONPATH`, `TestRealDiffRanges60` -> `10 passed, 20 subtests passed`. The walk was also run against an in-memory corrected `90-finalize.md` (a `BLOBFILE=` fence plus a printed gate-input file) and passed. Both checks prove only that the red fixtures can go green. Neither prototype is committed, and neither verifies the 60-02 / 60-03 implementations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in plan expectation] Counts fence exit code is 1, not 2**
- **Found during:** Task 2
- **Issue:** The plan wanted `test_counts_fence_without_literal_exits_two` to assert exit code 2 for the fence. That is wrong for the fence. The helper does exit 2 with `REASON_HEAD_BLOBS`, but the fence's own `else` branch prints the uncertain sentence and runs `exit 1`.
- **Fix:** The test checks three things. The fence run fresh exits non-zero with `REASON_HEAD_BLOBS` and the `carry_state.py failed` halt sentence on stderr. Running the helper directly with `--head-blobs ""` exits exactly 2 with stderr equal to `REASON_HEAD_BLOBS`. The test name is kept as the plan specified.
- **Cost if wrong:** Low. If 60-03 changes the halt's exit code, only the `assertNotEqual(rc, 0)` line is involved, and it still holds.
- **Files modified:** plugins/vibe-check/scripts/test_finalize_card.py
- **Commit:** 2121c57

**2. [Rule 1 - Harness fact] in_diff read from the score difference, not the serialized field**
- **Found during:** Task 2
- **Issue:** The finding's serialized `in_diff` keeps the agent-supplied value (False). score.py recomputes in_diff only internally, for the +20 term.
- **Fix:** `scored_in_diff()` scores a conf-80 finding with and without the ranges and returns whether the difference is the +20 term (90 vs 70). It asserts that the difference is 0 or 20.
- **Cost if wrong:** Low. If the +20 weight ever changes, the helper's `delta in (0, 20)` assertion fails loudly.
- **Files modified:** plugins/vibe-check/scripts/test_decision_continuity.py
- **Commit:** 2121c57

**3. [Rule 2 - Evidence] Added a green documenting repro for IN-04**
- **Found during:** Task 3
- **Issue:** The plan gave IN-04 only a red fixture. The ledger claim that the header rule keeps the decision even at `-U0` had no test running it.
- **Fix:** Added `TestRepro60Evidence.test_net_deletion_keeps_under_header_rule_even_at_u0`. Header `@@ -32,3 +32 @@` gives `[[32,32]]`: the decision at 38 stays `current` and the gate writes. The REPRO_60 IN-04 fixture field names both tests.
- **Cost if wrong:** None. This is an extra green test.
- **Files modified:** plugins/vibe-check/scripts/test_decision_continuity.py
- **Commit:** ce9f8b8

**4. [Rule 3 - Mechanics] REPRO_60 `fixture` may name several tests joined by " + "**
- **Found during:** Task 3
- **Issue:** Several rows have more than one fixture (WIDEN, DEFAULT-STAGED, 999.25-BLOBFILE), and the plan's `test_rd60_deletion_*` is a glob.
- **Fix:** Fixture names are joined by `" + "` and each is resolved by a `def`/`class` regex over both test modules. A third test proves the lookup fails on a missing name.
- **Cost if wrong:** Low. 60-05 reads the same field.
- **Commit:** ce9f8b8

**5. [Rule 2 - Truthful state] EVID-01, EVID-02 and FINL-01 are not marked complete**
- **Found during:** State updates
- **Issue:** The `requirements.mark-complete` step for the plan's `requirements:` list ticked EVID-01, EVID-02 and FINL-01. This plan only records red fixtures. No exact ranges and no printed `BLOBFILE=` exist yet, so none of the three requirements is met.
- **Fix:** Reverted REQUIREMENTS.md, which was clean before this step. The three stay Pending until 60-02, 60-03 and 60-04 turn their fixtures green.
- **Cost if wrong:** Low. A later plan's state step ticks them.

## Assumption Drift (advisory)

- **Found during:** Task 2 (DEFAULT-STAGED Probe B)
- **Planned:** Probe B shows "a finding on changed code treated as off-diff."
- **Actual:** In the working tree, line 48 is unchanged code (old line 38). The probe shows that the index and working-tree numbering disagree. It does not show that a working-tree line on changed code goes unscored. The ledger records this note for 60-04.
- **Why:** The `--staged` section numbers lines in index coordinates, and the unstaged insertion above shifts the working tree.
- **Cost if wrong:** 60-04 might count Probe B as a second, independent defect. Probe A alone is enough to justify the default-route fix.

## Known Stubs

None. `_REPRO_60_PENDING_FIXTURES = {"TestRouteAll"}` is a documented forward reference. `TestRepro60Record` fails once `TestRouteAll` exists while the allowlist still names it.

## Threat Flags

None. All diff text comes from temp repos the tests build with null global and system git config (T-60-02). Every temp repo and temp directory is removed through `TemporaryDirectory` / `addCleanup` / `rmtree` (T-60-03). The walk runs with an explicit four-variable env. `replay.py` and `score.py` were not edited.

## Self-Check: PASSED

- FOUND: .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md
- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py, plugins/vibe-check/scripts/test_finalize_card.py
- FOUND commits: 43d1905, 2121c57, ce9f8b8, cda9220
