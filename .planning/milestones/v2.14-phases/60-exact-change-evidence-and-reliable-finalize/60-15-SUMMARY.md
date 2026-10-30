---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 15
subsystem: review-prose / multi-pass state
tags: [finalize, carry-state, cr-01, wr-02, gap-closure]
requires:
  - 60-10/60-11 head_sha bind fence (CR-01)
  - 00-scope.md printed `FINALIZE_MODE=<0|1>` literal
provides:
  - step-2 bind fence that skips on the substituted FINALIZE_MODE=1 literal
  - remedy-bearing review-mode halt line
  - fresh-shell finalize-mode fence tests reaching the real 90-finalize.md counts fence
affects:
  - plugins/vibe-check/phases/review/05-state.md step 2
tech-stack:
  added: []
  patterns: [printed-literal substitution across Bash calls, fail-closed on unsubstituted value]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/scripts/test_diff_ranges.py
decisions:
  - "WR-02: the head_sha bind fence's first branch skips on the substituted FINALIZE_MODE=1 literal; literal 0, empty or unsubstituted takes the validating branch (fail closed)"
  - "WR-02: the review-mode halt names the remedy (set head_sha to the full 40-hex sha or restore the state file from git; --finalize unaffected)"
requirements: [FINL-02]
metrics:
  duration: ~4 min
  completed: 2026-10-30
  red_sha: 3c7814e
  green_sha: 07bb448
---

# Phase 60 Plan 15: head_sha bind fence skips on FINALIZE_MODE=1 and names a remedy (WR-02) Summary

A `--finalize` run no longer validates a `head_sha` it never reads. The step-2 bind fence in 05-state.md now skips when Phase 0 printed `FINALIZE_MODE=1`. Review mode still refuses the CR-01 payload, and the halt line now tells the owner how to repair the value.

## What changed

- **05-state.md step 2 (only change to product prose):** the fence has three branches.
  - `if [ "$FINALIZE_MODE" = "1" ]; then :`: binds nothing and prints nothing.
  - `elif LAST_REVIEWED_SHA=$(… last-head-sha …)`: the existing validated print.
  - `else`: halts. The halt line is the original sentence plus "Set that pass's head_sha to the full 40-hex sha of the last reviewed commit (or restore the state file from git) and re-run; --finalize does not read this value and still works."

  The paragraph after the fence now opens with the finalize-skip sentence, which covers both substitution and fail-closed behaviour. A remedy sentence follows "Any non-zero exit halts the run." The three existing locked sentences and the `(60-REVIEW.md CR-01)` parenthetical are unchanged.
- **test_diff_ranges.py:**
  - New constants: `HEAD_SHA_HALT_OLD`, the remedy-bearing `HEAD_SHA_HALT`, `FINALIZE_MODE_REF`, `FINALIZE_SKIP_SENTENCE` (added as the 4th `HEAD_SHA_NEEDLES` entry), `COUNTS_CALL`, `FINALIZE_MD` and `SIX_ROW_FIXTURE`.
  - `head_sha_binding_holds` gained two new checks. One fails if the fence does not reference `FINALIZE_MODE`; the other fails if the old halt sentence without the remedy comes back.
  - Six new fresh-shell tests in `TestStateHeadShaFence`.
  - Two new mutant subtests in `test_head_sha_mutants_trip`.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | 3c7814e | test(60-15): red — the head_sha bind fence must skip on FINALIZE_MODE=1 and name a remedy; finalize-mode fresh-shell fence tests |
| 2 (GREEN) | 07bb448 | fix(60-15): head_sha bind fence skips on the printed FINALIZE_MODE=1 literal and names a remedy on halt (WR-02) |

## Verification (observed output)

**RED at 3c7814e**, `pytest -q -p no:cacheprovider test_diff_ranges.py -k "StateHeadSha or SubstitutedValue"`:
```
18 failed, 8 passed, 105 deselected, 7 subtests passed in 0.78s
```
The failures, all expected by the plan:
- **Failed outright:** `test_finalize_mode_never_runs_the_payload`, `test_finalize_mode_skips_the_bind_and_reaches_the_counts_step`, `test_finalize_mode_still_prints_a_valid_sha_in_review_mode_only`, `test_halt_names_a_remedy`, `test_injection_payload_halts_without_executing`, `test_missing_state_file_halts`, `test_unsubstituted_mode_fails_closed` and `test_head_sha_binding_holds`.
- **Failed subtests:**
  - `test_other_non_sha_values_halt`: all 4 subtests.
  - `test_review_mode_literal_zero_still_halts`: all 3 subtests.
  - `test_head_sha_mutants_trip`: 3 subtests. These are the new needle, the `"$FINALIZE_MODE"` removal and the old halt line put back.

`test_prints_the_validated_sha` passed. The four pre-existing CR-01 tests went red only because `HEAD_SHA_HALT` changed, which the plan expected.

**GREEN at 07bb448:**
- `test_diff_ranges.py`: `121 passed, 92 subtests passed in 9.32s`
- `test_diff_ranges.py test_carry_state.py`: `355 passed, 410 subtests passed`
- `test_carry_state.py test_decision_continuity.py -k "LastHeadSha or Repro60 or state_md or StateMd or 05"`: `15 passed, 377 deselected, 73 subtests passed`
- Every test module that names `05-state.md` (11 modules) passed with 0 failures: carry_state 234, confirmed_fix 96, carry_writers 15, decision_continuity 158, diff_ranges 121, git_safety_prose 37, nv_render 38, scope_args 43, verified_fixes 87, score 500, statepath 62.
- All acceptance greps returned the expected counts: the `if`/`elif` lines 1 each, the remedy on the same line as the halt sentence and `>&2` 1, the finalize-skip sentence 1, the existing needle 1, and the step-1/4 and TOUCHED_PATHS/DECIDED_HASHES diff check 0.
- The GREEN commit changes only `05-state.md` (5 insertions, 3 deletions, all inside step 2).

**Extra mutation test (not in plan):** I changed the fence to fail open with `[ "$FINALIZE_MODE" != "0" ]`. Five tests went red: `test_unsubstituted_mode_fails_closed`, `test_halt_names_a_remedy`, `test_injection_payload_halts_without_executing`, `test_missing_state_file_halts` and `test_prints_the_validated_sha`. The file was then restored with `git checkout -- <file>`. This shows the fail-closed rule is guarded and the guard can actually fail.

**Finalize-mode check:** the test uses the six-row fixture with the last `head_sha` set to `HEAD`, and asserts that the fixture copy really holds `HEAD`. The fence with `"1"` substituted exited with rc 0, no stdout line and empty stderr. Then the real counts fence from 90-finalize.md ran on the same state file with `BLOBFILE` set to `{}`. It returned `outstanding_cw=5, unacknowledged_medium=1, undecided_nv=0`.

**Not verified here:** a live `/vibe-check:review --finalize` session in Claude Code. The check covers the fence text run in a fresh `bash -s`, not the model reading the prose and substituting the literal itself.

## Deviations from Plan

None. The plan was executed as written. The fail-open mutation run is extra verification and changes nothing in the repo.

## Threat model

- **T-60-49 (Finalize wedged):** mitigated. The finalize-mode test reaches the counts fence.
- **T-60-50 (review mode stops validating):** mitigated. The CR-01 payload with literal `0` and with no substitution is tested, and the marker file is never created.
- **T-60-51 (payload runs in finalize mode):** mitigated by `test_finalize_mode_never_runs_the_payload`.
- **T-60-52 (halt gives no fix):** mitigated. The remedy text is pinned, and putting the old line back trips the check.
- **T-60-53 (guard that can never fail):** mitigated. The `"0"`/`"1"` controls and the fail-open mutant above both turn tests red.

No new security surface beyond the threat model.

## Residuals (carried, not fixed — scope rule)

- 45-persist.md still writes `head_sha` with no format check at write time, and `future-schema.json` has no format constraint. A non-sha value can therefore still be stored. Review mode now halts on it with a stated fix, and Finalize ignores it. A write-side check would be new scope. 60-16 can record it in the ledger.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/05-state.md (modified, 07bb448)
- FOUND: plugins/vibe-check/scripts/test_diff_ranges.py (modified, 3c7814e)
- FOUND: commit 3c7814e
- FOUND: commit 07bb448
