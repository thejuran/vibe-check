---
phase: 62-baseline-and-continuous-test-run
plan: 08
subsystem: ci (offline-suite workflow proof)
tags: [CI-02, CI-01, D-15, D-16, D-17, D-18, D-20, github-actions, skip-list]
requires:
  - "62-01: left_out_guard.py (check-list, args, check-log, check-skips, skip_list_problems), stdlib_only.py"
  - "62-02: .github/workflows/offline-suite.yml"
  - "62-06, 62-07, 62-11: baseline records, cost note, baseline page (all in the suite the runner ran)"
provides:
  - .planning/phases/62-baseline-and-continuous-test-run/62-CI-RECORD.md (tree identity, D-18 exception with reproductions, D-20 skip list, local pre-check, recording run, green run, runner findings, red proof)
  - RECORDED_SKIPS pinned in .github/scripts/left_out_guard.py (2 entries from the runner's recording run)
  - TestPinnedSkipList in .github/scripts/test_left_out_guard.py (recorded check plus four break tests)
affects: [62-09 (opens the phase PR, records main's first run, closes CI-02)]
tech-stack:
  added: []
  patterns: [record-pin-then-green bootstrapping for a runner-derived allow-list]
key-files:
  created:
    - .planning/phases/62-baseline-and-continuous-test-run/62-CI-RECORD.md
  modified:
    - .github/scripts/left_out_guard.py
    - .github/scripts/test_left_out_guard.py
decisions:
  - "Runner skip list pinned as exactly the two skips the recording run printed (lane-archive sandbox-root test, replay linked-worktree test); skip_list_problems returned []"
  - "The changed-reason break test checks both layers: the runtime approved-reason rule trips first, and with that rule patched to the changed reason the set comparison still reports unexpected and missing for the id"
  - "The three docs commits after the green run were left unpushed so the only runs on the phase branch are the two recorded ones; plan 62-09 pushes them with the PR"
metrics:
  duration: ~60 min
  completed: 2026-11-14
  tasks: 3
  files: 3
---

# Phase 62 Plan 08: CI proof on GitHub's runners Summary

**The offline-suite workflow was run on GitHub's Linux runners. The first full run printed the runner's own 2 skips, and those were pinned. The pinned commit then ran green (`4324 passed, 2 skipped, 5 deselected`) with the plugin tree still identical to 2.14.1. A one-line broken test on a throwaway branch turned it red in the suite step, and that branch was then deleted.**

## Runs on GitHub (all from `gh run view … --json conclusion,url,headSha,jobs` and the run logs)

| Role | Branch | Commit | Run | Conclusion | Suite summary |
|------|--------|--------|-----|------------|---------------|
| Recording run (not green) | feat/v2.15-phase-62 | 385cbab | https://github.com/thejuran/vibe-check/actions/runs/43566043041 | failure, at `Skip guard` only (`SKIP LIST NOT YET RECORDED`) | `4319 passed, 2 skipped, 5 deselected, 5298 subtests passed in 209.65s (0:03:29)` |
| Green on the pinned commit | feat/v2.15-phase-62 | 4231836 | https://github.com/thejuran/vibe-check/actions/runs/43567045328 | success, every step; `skipped set matches the recorded 2` | `4324 passed, 2 skipped, 5 deselected, 5300 subtests passed in 176.29s (0:02:56)` |
| Red proof | ci-red-proof (deleted) | 29f9acd | https://github.com/thejuran/vibe-check/actions/runs/43568391505 | failure, at `Offline suite`; stdlib and list guard `success` | `1 failed, 4323 passed, 2 skipped, 5 deselected, 5300 subtests passed in 245.12s (0:04:05)`; `AssertionError: 84534 != 84535` in `TestPinnedRev.test_deep_review_pinned_numbers` |

Pinned skip list (D-20), both in the owner-approved groups:
1. `plugins/vibe-check/scripts/test_lanearchive.py::TestSandboxTempRoot::test_real_sandbox_root_tmp_and_private_tmp_forms`: `no sandbox temp root on this machine`
2. `plugins/vibe-check/scripts/test_replay.py::TestReconstruction::test_transcript_recovery_covers_survivor_agents`: `Phase-40 transcripts are local-only (gitignored); a linked worktree has none to recover from`

## Verification actually run

- Task 1: step 0 checks passed (primary checkout, branch `feat/v2.15-phase-62`, all five required files present). Both plugin tree ids were `90e0697363ee5c09bb7942a963cf670e16717c4a`, and the plugins diff against `dd8e4ab` was empty. The local CI commands were run from a scratch linked worktree: stdlib exit 0, list guard exit 0, suite `4320 passed, 1 skipped, 5 deselected, 5298 subtests passed`, count guard exit 0, and skip guard exit 1 with `SKIP LIST NOT YET RECORDED` (the expected result). The Phase-53 reproduction in the worktree gave `5 failed, 3 passed, 2 subtests passed`, with the three left-out ids failing. Docker `ubuntu:24.04` was run as a non-root user with GNU coreutils 9.4. Under `LC_ALL=C` it counted 26365 and 11802 words where the test expects 27146 and 12132. Under `C.UTF-8` it counted 27146 and 12132 where the test expects 27148 and 12134. The Task 1 verify command printed `OK`.
- Task 2: `pytest -q -p no:cacheprovider .github/scripts` gave 118 passed, 72 subtests passed, 0 failed. The six `TestPinnedSkipList` tests passed. A scratch mutant with one pinned pair removed gave `2 failed, 4 passed`. `test_workflow_shape.py` gave 21 passed, and `check-list` exited 0. The Task 2 verify command printed `OK`.
- Task 3: the local break gave `1 failed, 22 passed`. On the runner, all four red-proof checks held. After clean-up, `ls-remote` and `branch --list` for `ci-red-proof` both printed nothing, `gh pr list --head ci-red-proof --state all` printed `[]`, and `origin/main` was `eb790e4` both before and after. The Task 3 verify command printed `OK`.

## Runner findings

- None beyond the recorded five and the recorded skips. 0 of the 3 allowed class S/T attempts were used. There were no class P, G or K findings.
- A1 held: Python 3.14 is available (`CPython (3.14.10)`). A2 held: 0 failed with the five left out, and the same two skips as the container.
- Linux determinism: `docs/design/lean-v2.15/tools` passed in full on the runner in both runs. That includes `test_finalize_capture.py`, which re-derives the committed Finalize captures (until now only checked on macOS), and `test_baseline_records.py`, which re-derives the 0-recording replay report. The runner did not disagree with any committed record.

## Commits

- `385cbab` docs(62-08): CI record — tree identity, D-18 exception, local pre-check (pushed)
- `4231836` feat(62-08): pin the runner's skip set from the recording run (D-20) (pushed)
- `1295b8a` docs(62-08): recording run and green phase-branch run recorded (local)
- `ada0935` docs(62-08): CI red proof recorded; throwaway branch deleted (local)
- `29f9acd` test: deliberate failure for the CI red proof (do not merge): on `ci-red-proof` only. It was pushed and then deleted with the branch, and it is not on the phase branch.

## Deviations from Plan

**1. [Rule 3 - Blocking] Changed-reason break test patches the approved-reason rule as well**
- **Found during:** Task 2, step c.
- **Issue:** Plan 62-01 added a runtime check that refuses any pinned reason that is not its file's approved reason. With that check in place, a pinned reason changed by one character stops at that check, so the run never reaches the `unexpected`/`missing` comparison the plan asks this test to show.
- **Fix:** The test first asserts that the runtime rule trips (`RECORDED SKIP LIST BREAKS THE APPROVED-GROUP RULE`). It then patches `APPROVED_SKIP_REASONS` to the changed reason and asserts that both an `unexpected` line and a `missing` line name the id. Both layers are shown to be load-bearing.
- **Cost if wrong:** low. This is one test's structure, and the guard's behaviour is unchanged.
- **Files modified:** .github/scripts/test_left_out_guard.py
- **Commit:** 4231836

**2. [Rule 3 - Blocking] Tree ids in the record put on separate lines**
- **Found during:** Task 1 verify.
- **Issue:** The verify command counts lines that contain the tree id, and the record first had both ids on one line.
- **Fix:** Each id now has its own bullet. The content is unchanged.
- **Commit:** 385cbab

Not a deviation: the `gh run list --workflow offline-suite.yml` call immediately after the first push returned `HTTP 404 … not found on the default branch`. A retry seconds later found the run. This is noted in the record.

## Known Stubs

None.

## Next

Plan 62-09 opens the phase PR, which pushes `1295b8a` and `ada0935`, and records `main`'s first run. CI-02 stays open until then and was not marked complete here.

## Self-Check: PASSED
- 62-CI-RECORD.md and the two modified scripts exist.
- Commits 385cbab, 4231836, 1295b8a and ada0935 are in `git log`. 29f9acd is reachable only as the deleted branch's former tip, which is intended.
