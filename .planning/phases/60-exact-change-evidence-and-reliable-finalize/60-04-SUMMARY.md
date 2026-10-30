---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 04
subsystem: vibe-check change evidence (route wiring)
tags: [exact-ranges, range-source, coordinate-contract, fail-closed, EVID-01, EVID-03, D-04, D-05, D-06]
requires:
  - "60-01 REPRO_60 verdicts (PR-SERIES, MIXED-COORD, DEFAULT-STAGED all reproduced at ce9f8b8)"
  - "60-02 scripts/diff_ranges.py (green 53fb637)"
provides:
  - "30-collect-score.md changed-line ranges bullet: ranges only from +/- body lines via scripts/diff_ranges.py, coordinate contract, one range source per route, fail-closed set -o pipefail fence with the halt sentence"
  - "00-scope.md (default, PR, GSD) and 05-state.md (pass >= 2) name the range source; reviewer diff commands unchanged"
  - "fixtures/pr-cumulative.diff: four verbatim file sections of gh pr diff 5 --color never"
  - "test_diff_ranges.py: TestRouteDefault, TestRouteGSD, TestRouteIncremental, TestRouteRange, TestRoutePR, TestRouteAll, TestProseRangeFence"
  - "60-REPRO.md D-04 audit (11 rows), D-05 statement, PR capture provenance; V1/V4-V7 green-at filled"
affects: [60-05]
tech-stack:
  added: []
  patterns: ["prose fence and route command both read from the markdown at test time and executed in a fresh bash -s", "documenting assertion of the old wrong reading kept beside the fixed reading in the same probe"]
key-files:
  created:
    - plugins/vibe-check/scripts/fixtures/pr-cumulative.diff
  modified:
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/phases/review/00-scope.md
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/scripts/test_nv_render.py
    - plugins/vibe-check/scripts/test_diff_ranges.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md
decisions:
  - "Default-route arm: git diff HEAD alone is the range source (DEFAULT-STAGED reproduced); reviewers keep all three commands"
  - "GSD/incremental arm: single diff git diff $PHASE_START / git diff $LAST_REVIEWED_SHA (MIXED-COORD reproduced)"
  - "PR range source is gh pr diff <ref> --color never; the agents' --patch view is unchanged"
  - "PR fixture came from gh itself (not fallback A or B), cross-checked against the local merge-base..head diff"
  - "DEFAULT-STAGED Probe B recorded as coordinate disagreement, not a lost changed line: line 48 is unchanged code on disk"
metrics:
  duration: "~35 min"
  completed: 2026-10-29
  tasks: 3
  files: 8
requirements: [EVID-01, EVID-03]
---

# Phase 60 Plan 04: Route wiring for exact ranges Summary

Every review route now builds its changed-line ranges the same way: it pipes one range-source diff through `scripts/diff_ranges.py` in a fail-closed fence. The orchestrator no longer reads ranges from hunk headers. All three coordinate shapes from 60-01 reproduced, so all three fixes shipped:
- the default route uses `git diff HEAD` alone;
- GSD and incremental passes use one diff against the base commit;
- the PR route uses the cumulative `gh pr diff <ref> --color never`, and the builder refuses a commit series.

`--all` has an asserted unsupported-fixture record. The four intentional reds are green, and the full suite is green.

## Commits

| # | Task | Commit |
|---|------|--------|
| 1 | Rewrite the `changed-line ranges` bullet, add range-source lines to 00-scope.md / 05-state.md, retarget the test_nv_render lock | `66d63de` |
| 2 | PR capture fixture, the six `TestRoute*` classes, and `TestProseRangeFence` | `39f6dbd` |
| 3 | Coordinate probes through the builder, empty pending allowlist, D-04 audit and provenance in 60-REPRO.md | `fb8b32b` |

Green SHAs for 60-05's ledger: route classes and the prose fence are green at `39f6dbd`. The four `TestCoordinateSpaces60` probes and `TestRepro60Record` (with `TestRouteAll` resolved) are green at `fb8b32b`.

## Arms chosen (from the recorded verdicts)

60-REPRO.md recorded these verdicts at `ce9f8b8`:
- V4 PR-SERIES: "REPRODUCED at `ce9f8b8` -> to be fixed by 60-04."
- V5 MIXED-COORD: "REPRODUCED at `ce9f8b8` -> to be fixed by 60-04."
- V6 DEFAULT-STAGED: "REPRODUCED at `ce9f8b8` (both probes) -> to be fixed by 60-04."

`REPRO_60` gives the disposition `reproduced; fixed by 60-04` for all three. So:
- **Default:** the range source is `git diff HEAD` alone. The text says the `git diff --staged` section reviewers also receive "is a second view of the same changes in index line numbers and is never appended to the range source". The three reviewer commands in mode 1 are byte-identical to HEAD; nothing was removed from 00-scope.md.
- **GSD pass 1:** `git diff $PHASE_START`, or `git diff HEAD` when `$PHASE_START` is empty.
- **Any stateful route, pass >= 2:** `git diff $LAST_REVIEWED_SHA`.
- **PR:** `gh pr diff <ref> --color never`.
- **Range:** `git diff <range>`.
- **`--all`:** no diff, `{}`.

Every git call carries `--no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/`.

## PR fixture provenance

The fixture came from **`gh`**, not fallback (A) or (B). The command was `gh pr diff 5 --color never`, captured 2026-10-29. The 7076-line capture was cut at `diff --git` boundaries to capture lines 4897-5182: `50-fix-loop.md`, `90-finalize.md`, `batch_card.py` and `carry_state.py`. The result is 286 lines with 4 sections, 0 mbox lines, and 0 hits for `key|token|secret|password`. As a cross-check, `git diff <flags> f2b6a36 98f63aa… -- <the four paths>` through the builder gave the identical ranges (the merge base is f2b6a36). `6dfac64^2` appears nowhere (0 in test_diff_ranges.py and 0 in 60-REPRO.md).

Revision check, observed:
```
$ git rev-parse --verify 98f63aa7834af6a04c5a38d925d8b1ca457111bc^{commit}   -> 98f63aa7834af6a04c5a38d925d8b1ca457111bc
$ git rev-parse --verify f2b6a3674d0d0dc62ab6dca3a00816c070943884^{commit}   -> f2b6a3674d0d0dc62ab6dca3a00816c070943884
$ git rev-parse --verify 6dfac6436427cc385fe1937f73ed841fef6c8ffb^{commit}   -> 6dfac6436427cc385fe1937f73ed841fef6c8ffb
$ git merge-base f2b6a36 98f63aa7834af6a04c5a38d925d8b1ca457111bc            -> f2b6a3674d0d0dc62ab6dca3a00816c070943884
```

## Verification (observed)

- Task 1 verify printed `VERIFY_OK`, and `pytest -q test_nv_render.py test_scope_args.py` gave `81 passed, 437 subtests passed`. Grep counts:
  - `start + count - 1` = 0; `set -o pipefail` = 1; `pure function` = 1 (unchanged).
  - `Range source for 30-collect-score` = 3 in 00-scope.md and 1 in 05-state.md.
  - `gh pr diff <ref> --color never` = 1 in 00-scope.md; `--patch` = 1 in 00-scope.md (unchanged from HEAD).
  - No line of 00-scope.md was removed: `git diff 8b78893 -- 00-scope.md` has 0 `-` lines.
- The retargeted lock is real:
  - `deletion_range_holds` is False on the HEAD prose and True on the new prose.
  - All 8 delete-one-phrase mutants on SYNTHETIC trip.
- Task 2 verify: the fixture checks passed, and `pytest -q test_diff_ranges.py -k "Route or ProseRangeFence"` gave `24 passed, 3 subtests passed`. The whole of test_diff_ranges.py gave `81 passed, 59 subtests passed`.
  - Greps: `^class TestRoute` = 6; `30-collect-score.md` = 3; `[[1, 10], [58, 58]]` present; `urllib|requests|"gh"` = 0.
- The prose fence tests are not decorative, checked against two temporary mutants of 30-collect-score.md (the file was restored after each, and `git diff --stat` was empty):
  - Deleting `set -o pipefail` failed 2 of 7 tests.
  - Appending `; git diff --staged` to the default source failed 3 of 7.
- Task 3 verify: `pytest -q test_decision_continuity.py -k "TestRepro60Record or TestCoordinateSpaces60"` gave `11 passed, 26 subtests passed`, followed by `1` and `AUDIT_OK`. No REPRO_60 disposition contains "to be fixed". `git diff --stat 8b78893 -- replay.py score.py diff_ranges.py` is empty.
- Plan-level selection (`-k "Route or ProseRangeFence or deletion_range or Repro60 or CoordinateSpaces60 or finalize"` over the four files) gave `57 passed, 198 subtests passed`.
- **Full suite** (`cd plugins/vibe-check/scripts && pytest -q`): **`3765 passed, 4930 subtests passed in 175.77s`, 0 failed.** The four intentional `TestCoordinateSpaces60` reds are green.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan self-contradiction] PR range-source line in 00-scope.md avoids the literal `--patch`**
- **Found during:** Task 1
- **Issue:** The behavior text asked for "(cumulative; never `--patch`)". The acceptance criterion requires `grep -c -- '--patch' 00-scope.md` to stay at its HEAD value (1). With the literal, the count became 2.
- **Fix:** The line reads "(cumulative; never the per-commit patch series the reviewers' command above prints)". The literal "never `--patch`" lives in the 30-collect-score.md table, where the prose lock pins it.
- **Cost if wrong:** None to behavior. Only the wording in 00-scope.md differs.
- **Files modified:** plugins/vibe-check/phases/review/00-scope.md
- **Commit:** 66d63de

**2. [Rule 2 - No decorative locks] Added a pipefail test to TestProseRangeFence**
- **Found during:** Task 2
- **Issue:** The planned failure cases (a helper that exits 2, and mbox input) halt even without `set -o pipefail`, because the helper itself fails. Nothing would catch removing pipefail.
- **Fix:** Added `test_failing_range_source_halts_through_pipefail`. A failing git revision gives the helper empty stdin, so it prints `{}` and exits 0, and only pipefail turns that into a halt. The test also shows that the unguarded fence returns `{}`.
- **Cost if wrong:** None. This is an extra test.
- **Commit:** 39f6dbd

**3. [Rule 1 - Plan check wording] The literal `gh ` string**
- **Found during:** Task 2
- **Issue:** One acceptance bullet bans the substring `gh ` from test_diff_ranges.py. The same plan requires the docstring to name the exact command `gh pr diff 5 --color never`, and ordinary words like "through " also contain it.
- **Fix:** Interpreted the check as "no gh invocation". There is no `subprocess` call to `gh`, and the module has no `urllib` or `requests`; the grep for `urllib|requests|"gh"` gives 0.
- **Cost if wrong:** None. No test touches the network.

**4. [Rule 3 - Mechanics] Planning file staged with `git add -f`**
- **Found during:** Task 3 commit
- **Issue:** `.planning` is matched by .gitignore, so a plain `git add` of the tracked 60-REPRO.md was refused.
- **Fix:** Ran `git add -f` on that one path only. The owner's HANDOFF.json and PROJECT.md were left unstaged.
- **Cost if wrong:** None.

**5. [Rule 2 - Correctness] Probe B asserts the coordinate contract**
- **Found during:** Task 3
- **Issue:** The 60-01 caution applied here. Probe B's original assertion (that line 48 is in the diff) would be wrong to satisfy, because line 48 on disk is unchanged code.
- **Fix:** The probe now asserts that line 48 equals the old line 38 and is out of the ranges, and that the staged edit at working-tree line 58 is in them. 60-REPRO.md V6 and the docstring call it what it is: coordinate disagreement between the two sections, not a lost changed line.
- **Cost if wrong:** Low. If a reviewer quotes index numbers, the finding scores as off-diff. The contract sentence tells the orchestrator that findings use working-tree line numbers.
- **Commit:** fb8b32b

## Assumption Drift (advisory)

- **Found during:** Task 2
- **Planned:** The capture might need an offline fallback.
- **Actual:** `gh` was reachable. The fixture is the real `gh pr diff` output, and the local merge-base→head reconstruction (fallback A) served only as a cross-check.
- **Why:** Network and auth were available.
- **Cost if wrong:** None.

## TDD Gate Compliance

Task 1's RED evidence: the retargeted `deletion_range_holds` is False on the pre-edit prose. Task 3's RED evidence: the four `TestCoordinateSpaces60` probes committed red at `ce9f8b8` (60-01). The Task 2 route tests were written against the already-edited prose, so they have no separate failing commit. Their RED evidence is the two prose mutants above, which failed 2 and 3 tests.

## Known Stubs

None.

## Threat Flags

None. Mitigations by threat:
- **T-60-13:** fixed flags on every range call, plus `test_hostile_external_diff_config_changes_nothing`.
- **T-60-14:** pipefail and the halt sentence. The failure paths assert empty stdout, and the pipefail test makes the guard load-bearing.
- **T-60-15:** `REASON_MBOX` refusal, `TestRoutePR.test_commit_series_is_refused`, `test_commit_series_halts`, and the `--color never` lock phrase.
- **T-60-16:** the fixture was scanned and had 0 hits.
- **T-60-17:** `TestRouteDefault`.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/fixtures/pr-cumulative.diff, plugins/vibe-check/scripts/test_diff_ranges.py, plugins/vibe-check/phases/review/30-collect-score.md, .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md
- FOUND commits: 66d63de, 39f6dbd, fb8b32b
