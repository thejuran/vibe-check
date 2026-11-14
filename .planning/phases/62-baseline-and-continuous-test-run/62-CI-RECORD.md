# Phase 62 CI record

**Status (2026-11-14):** tree identity checked, D-18 exception reproduced, local run of the exact CI commands done. Not yet run: the recording run on GitHub's Linux machines, the pinned skip list, the green run on the phase branch, the red proof. `main`'s first run is plan 62-09.

Precondition (checked before anything else): primary checkout `/Users/julianamacbook/turingmind-code-review` (`git rev-parse --absolute-git-dir` equals the common git dir), branch `feat/v2.15-phase-62`, HEAD `776cdd9245bea6418ffa7849eabc2565e2ed9209`. The workflow, both guard scripts, `docs/design/lean-v2.15/baseline/MANIFEST.json` and `docs/design/lean-v2.15/BASELINE-v2.14.1.md` are all present on the branch.

## Tree identity (D-16)

- `git rev-parse dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4:plugins feat/v2.15-phase-62:plugins` prints:
  - 2.14.1 (`dd8e4ab`): `90e0697363ee5c09bb7942a963cf670e16717c4a`
  - phase branch (`feat/v2.15-phase-62`): `90e0697363ee5c09bb7942a963cf670e16717c4a`
- `git diff --stat dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4 feat/v2.15-phase-62 -- plugins` prints nothing.
- The plugin code on the phase branch is byte-identical to 2.14.1. Outside `.planning/`, the branch only adds files: `git diff --stat dd8e4ab… feat/v2.15-phase-62 -- . ':(exclude).planning'` gives `32 files changed, 13259 insertions(+)` (no deletions), all under `.github/` (the workflow, the left-out list, the guard scripts and their tests) and `docs/design/lean-v2.15/` (the baseline records, the tools and their tests, the baseline page).

## Owner-approved exception (D-18)

| # | Test id | Why it cannot pass on GitHub's Linux machines | Reproduction |
|---|---------|-----------------------------------------------|--------------|
| 1 | `plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_a2_pair_sits_on_adjacent_lines_of_one_statement` | Reads the gitignored Phase-43 session recordings, which exist only in the owner's primary checkout; the test has no linked-worktree guard | Re-run 2026-11-14 on the Mac in a detached linked worktree of the phase branch: `pytest -q -p no:cacheprovider -rf "plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases"` → `FAILED …::test_a2_pair_sits_on_adjacent_lines_of_one_statement`, `AssertionError: ('architecture', 233) not found in []` (test_replay.py:1049) |
| 2 | `plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_off_line_credit_mutation_trips` | Same: needs the private Phase-43 recordings | Same command: `SUBFAILED(run='runs-v2.10-phase43/first/should-quiet-4/run-3')` and `SUBFAILED(run='runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1')`, `AssertionError: 'warning' != 'critical'` (test_replay.py:1059) |
| 3 | `plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_pre_same_line_scorer_gave_critical_100` | Same: needs the private Phase-43 recordings | Same command: the same two runs `SUBFAILED`, `AssertionError: Tuples differ: ('warning', 94) != ('critical', 100)` (test_replay.py:1038). Summary of the class run: `5 failed, 3 passed, 2 subtests passed in 0.16s` (1 failed test + 4 failed subtests across these three tests) |
| 4 | `plugins/vibe-check/scripts/test_footprint.py::TestWordCountLocaleDrift::test_c_locale_wc_matches_the_recorded_number` | Asserts the macOS (BSD) `wc -w` count under `LC_ALL=C`; GNU `wc` on Linux counts differently | Re-run 2026-11-14 in Docker (`ubuntu:24.04`, non-root `--user 1000:1000`, files mounted read-only; the two files are `git show 7a386ed:plugins/vibe-check/commands/{review,deep-review}.md`, the revision the test reads): `wc (GNU coreutils) 9.4`, `LC_ALL=C wc -w` gives **26365** for review.md and **11802** for deep-review.md, where the test expects **27146** and **12132**. The Mac gives 27146 and 12132 |
| 5 | `plugins/vibe-check/scripts/test_footprint.py::TestWordCountLocaleDrift::test_utf8_locale_wc_is_the_plans_figure_and_differs_by_two` | Asserts the macOS `wc -w` count under `en_US.UTF-8` (27148 / 12134, two more than the C-locale count); GNU `wc` does not split the U+2260 character the same way | Same Docker run, re-run 2026-11-14: GNU `wc -w` under `C.UTF-8` gives **27146** and **12132**, not the **27148** and **12134** the test expects (no `+2`). The Mac gives 27148 and 12134 under `en_US.UTF-8` |

- These five keep running on the owner's Mac at every release gate.
- The left-out list guard (`left_out_guard.py check-list`) fails the run if `.github/ci-left-out-tests.txt` differs from these five in any way, and the count guard (`check-log`) fails it unless the suite summary shows exactly `5 deselected`.
- Any other test that fails only on GitHub's Linux machines is not covered by this exception: D-17 applies to it in full and it goes back to the owner.

## Skips on the runner (D-20)

Ruling, in two sentences. Tests that skip themselves on GitHub's Linux machines through their own built-in conditions are allowed only if they are on the recorded list. The list comes from the runner's first complete run, the CI check fails on any difference from it (more, fewer or different ids, or a different reason), and a skip not on the list goes back to the owner the same way as an unexpected failure.

Bootstrapping order: record, pin, then call green. The first run on the runner in which the suite completes is the recording run; it is red by design at the `Skip guard` step and is never counted as green. Its skips are checked mechanically against the two approved groups (`skip_list_problems`) and, if all pass, copied into `RECORDED_SKIPS` character for character. Only a later run on the commit that holds the pinned list can be recorded as green. The list is pinned once and never edited to match a later run.

The recorded tests still run on the owner's Mac at every release gate, where the 2.14.1 baseline has 0 skips (primary checkout, with the private recordings).

| # | Test id | Reason | Group |
|---|---------|--------|-------|
| 1 | `plugins/vibe-check/scripts/test_lanearchive.py::TestSandboxTempRoot::test_real_sandbox_root_tmp_and_private_tmp_forms` | `no sandbox temp root on this machine` | lane-archive (the test's own `skipTest` when `/tmp/claude-<uid>` is absent; test_lanearchive.py:415-416) |
| 2 | `plugins/vibe-check/scripts/test_replay.py::TestReconstruction::test_transcript_recovery_covers_survivor_agents` | `Phase-40 transcripts are local-only (gitignored); a linked worktree has none to recover from` | replay (the test's own `skipIf(IN_LINKED_WORKTREE)`; test_replay.py:281-282) |

Count: **2**, taken from the recording run https://github.com/thejuran/vibe-check/actions/runs/43566043041 and pinned in `RECORDED_SKIPS` in `.github/scripts/left_out_guard.py`. `skip_list_problems` on the observed pairs returned `[]` (both inside the two approved groups, each with its file's exact reason).

Difference from the owner's Mac: in a linked worktree on the Mac (local run below) only the replay test skips, because the Mac has a `/tmp/claude-<uid>` sandbox root and the lane-archive test runs. In the primary checkout on the Mac, where the 2.14.1 baseline was taken, both tests run and the baseline has 0 skips.

## Local run of the CI commands

Run 2026-11-14 on the owner's Mac (Darwin 27.2.0, Python 3.14.5, pytest 9.0.3) from a detached linked worktree of `feat/v2.15-phase-62` at `776cdd9` created under the session scratchpad and removed afterwards. Commands, in workflow order:

```
python3 -I .github/scripts/stdlib_only.py plugins/vibe-check
python3 -I .github/scripts/left_out_guard.py check-list .github/ci-left-out-tests.txt
left_out="$(python3 -I .github/scripts/left_out_guard.py args .github/ci-left-out-tests.txt)"
pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools <the five --deselect=… args> -rs --junitxml=<scratch>/suite.xml > <scratch>/suite.log
python3 -I .github/scripts/left_out_guard.py check-log <scratch>/suite.log
python3 -I .github/scripts/left_out_guard.py check-skips <scratch>/suite.xml <scratch>/suite.log
```

| Step | Output | Exit |
|------|--------|------|
| Stdlib-only check | `33 shipped .py files; third-party imports: none` | 0 |
| Left-out list guard | `left-out list matches the recorded five` | 0 |
| Offline suite | `4320 passed, 1 skipped, 5 deselected, 5298 subtests passed in 259.93s (0:04:19)` | 0 |
| Left-out count guard | `suite log: 5 deselected, no failure (…)` | 0 |
| Skip guard | `SKIP LIST NOT YET RECORDED — THIS IS A RECORDING RUN, NOT A GREEN RUN — STOPPING`, `OBSERVED-SKIP-COUNT 1` | 1 (expected: no list recorded yet) |

Skips seen on the owner's Mac in a linked worktree (for comparison only; never pinned, because D-20 takes the list from the real runner):

- `plugins/vibe-check/scripts/test_replay.py::TestReconstruction::test_transcript_recovery_covers_survivor_agents` — `Phase-40 transcripts are local-only (gitignored); a linked worktree has none to recover from`

## Recording run (D-20)

| Branch | Commit | Run | Conclusion | Failing step | Suite summary |
|--------|--------|-----|------------|--------------|---------------|
| `feat/v2.15-phase-62` | `385cbab119064c4c610dcd41c318046c0fe3080c` | https://github.com/thejuran/vibe-check/actions/runs/43566043041 | failure | Skip guard | `4319 passed, 2 skipped, 5 deselected, 5298 subtests passed in 209.65s (0:03:29)` |

This is the recording run. It is red by design at the skip guard step because no skip list existed yet. It is not a green run and is not counted as one.

Checks (from `gh run view 43566043041 --json conclusion,url,headSha,jobs` and the run log):
- Steps: Checkout, Setup Python (`Successfully set up CPython (3.14.10)`), Test-only tools, Stdlib-only check (`33 shipped .py files; third-party imports: none`), Left-out list guard (`left-out list matches the recorded five`), Offline suite and Left-out count guard (`suite log: 5 deselected, no failure (…)`) all `success`; Skip guard `failure`, the only failing step.
- Skip guard output: `SKIP LIST NOT YET RECORDED — THIS IS A RECORDING RUN, NOT A GREEN RUN — STOPPING`.
- Suite summary: `5 deselected`, no `failed` or `error`.
- `-rs` lines: `SKIPPED [1] plugins/vibe-check/scripts/test_lanearchive.py:413: no sandbox temp root on this machine` and `SKIPPED [1] plugins/vibe-check/scripts/test_replay.py:281: Phase-40 transcripts are local-only (gitignored); a linked worktree has none to recover from`.
- `OBSERVED-SKIP` lines: 2; `OBSERVED-SKIP-COUNT 2`; summary `2 skipped`. All three agree.

## Green run on the phase branch

(Not yet run.)

## Runner findings

(Not yet run.)

## Red proof

(Not yet run.)
