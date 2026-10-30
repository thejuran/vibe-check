---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 11
subsystem: review-prose-range-binding
tags: [gap-closure, security, command-injection, CR-01, tdd]
gap_closure: true
requires: [60-10 (carry_state.py last-head-sha)]
provides: [05-state.md step-2 LAST_REVIEWED_SHA bind fence, 00-scope.md PHASE_START commit-id check, 30-collect-score.md printed-literal rule]
affects: [60-13 (ledger RED/GREEN SHAs)]
tech-stack:
  added: []
  patterns: [validate where the value is bound, print the literal then substitute only the printed literal, fresh-shell payload tests with on-disk markers, prose locks with mutants]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/phases/review/00-scope.md
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/scripts/test_diff_ranges.py
decisions:
  - "The value substituted for <last-reviewed-sha> / <phase-start-sha> is only the literal printed by a fence that validated it (40/64 lowercase hex); quoting in the range row is documented as not being the protection"
  - "The 00-scope.md PHASE_START check is one line so it can be dropped as a unit by the mutant test; an empty PHASE_START (no history) is still allowed and falls back to HEAD"
requirements: [EVID-03]
metrics:
  duration: ~20min
  completed: 2026-10-30
  tasks: 2
  files: 4
---

# Phase 60 Plan 11: CR-01 prose half (validated revision binding) Summary

The two revisions the review substitutes into `git diff` are now bound by fences that check them first. 05-state.md step 2 binds `$LAST_REVIEWED_SHA` with `carry_state.py last-head-sha` (added in 60-10). If the helper refuses, the fence prints no `LAST_REVIEWED_SHA=` line, writes one fixed halt sentence, and exits 1. 00-scope.md now refuses a non-empty `PHASE_START` that is not a 40- or 64-hex commit id, and it does this before the `PHASE_START=` print. 30-collect-score.md's GSD and pass ≥ 2 rows now say that only the printed literal is ever substituted. The paragraph that claimed the quotes protect the command now says the opposite: quotes do not stop `$(...)`.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED: bind-fence, PHASE_START check and printed-literal tests, plus the CR-01 row reproduction | dfca59c | test_diff_ranges.py |
| 2 | GREEN: 05-state.md fence, 00-scope.md check line, 30-collect-score.md rows and paragraph | 5d81170 | 05-state.md, 00-scope.md, 30-collect-score.md |

**RED SHA:** dfca59c. **GREEN SHA:** 5d81170.

## Evidence (observed)

RED at dfca59c:
- `pytest -q -p no:cacheprovider --tb=no test_diff_ranges.py -k "StateHeadSha or SubstitutedValue or ScopePhaseStart or printed_last_reviewed or injection_payload"` gave `16 failed, 5 passed, 98 deselected, 1 subtests passed`. These tests failed:
  - all 4 TestStateHeadShaFence tests, because no fence existed yet;
  - all 6 TestSubstitutedValueProse tests (the head_sha mutant test failed at its subtests);
  - `test_non_sha_phase_start_halts_before_printing`;
  - `test_mutant_without_the_check_prints_the_payload`;
  - `test_incremental_route_uses_the_printed_last_reviewed_sha`.
- These passed, as expected: `test_injection_payload_in_the_row_executes_so_the_bind_fence_is_the_control`, `test_sixty_four_hex_is_accepted`, and the two existing TestScopePhaseStartFence tests.
- `-k injection_payload_in_the_row` gave `1 passed`. This is the CR-01 reproduction on the old prose: the payload substituted into the row creates the marker file and returns rc 0.
- The rest of the file gave `98 passed, 17 deselected, 75 subtests passed`.

GREEN at 5d81170 (working tree identical):
- `pytest -q -p no:cacheprovider test_diff_ranges.py` gave `115 passed, 86 subtests passed`.
- `pytest -q -p no:cacheprovider test_diff_ranges.py test_nv_render.py test_finalize_card.py test_confirmed_fix.py test_decision_continuity.py test_carry_state.py test_carry_writers.py` gave `749 passed, 1284 subtests passed`.
- Full suite: `pytest -q -p no:cacheprovider` in `plugins/vibe-check/scripts` gave `3813 passed, 5002 subtests passed in 175.42s`, 0 failed. It ran on the edited working tree, which is identical to 5d81170.
- `requirements.mark-complete EVID-03` re-ticked EVID-03. Phase 60 re-verification is still pending (60-13 and then verify).

Marker evidence from the fresh-shell payload tests:
- `test_injection_payload_halts_without_executing` sets the state's last `head_sha` to `$(touch "$T/pwned")HEAD`. The run gives rc 1, no `LAST_REVIEWED_SHA=` line, and stderr exactly `refused: last pass head_sha is not a commit sha` followed by the halt sentence. `<T>/pwned` does not exist.
- `test_non_sha_phase_start_halts_before_printing` runs the same payload as `PHASE_START`. The run gives rc 1, no `PHASE_START=` line, stderr equal to the halt sentence, and no marker file.
- Mutant: with the check line removed, the fence prints `PHASE_START=$(touch "$T/pwned")HEAD` with rc 0, so the line is what blocks it.
- End to end: the bind fence prints the sha, that printed literal is put into the pass ≥ 2 row, and the range fence returns `{"f.txt": [[3, 3], [5, 5]]}`.
- The tests run under `/bin/bash` 3.2.57, and the `[[ =~ ^[0-9a-f]{40}([0-9a-f]{24})?$ ]]` regex behaves correctly there: 64-hex is accepted and 41-hex is refused (checked by hand).

Acceptance greps:
- 05-state.md has 1 `last-head-sha < "$STATE_FILE"` match. Checked with `grep -F`, because BSD grep treats `$S` in a basic regex as an anchor and returns 0.
- 05-state.md has 1 `printf 'LAST_REVIEWED_SHA=%s\n'` and 0 `` state.passes[-1].head_sha` ``.
- In 00-scope.md the check line (90) comes before the `printf 'PHASE_START=` line (98).
- 30-collect-score.md has 1 `` printed after `LAST_REVIEWED_SHA=` ``, 1 printed-literal rule sentence, and 0 copies of the old quotes claim.
- There are 4 range-source lines in total.
- `git diff dfca59c --stat -- plugins/vibe-check/phases/` shows only the three intended files.

## Deviations from Plan

**1. [Rule 1 - Test contract] The bind-fence halt test checks the last stderr line, not all of stderr.**
- **Found during:** Task 1
- **Issue:** The plan asked for `stderr.strip() == HEAD_SHA_HALT`. The fence the plan specifies does not redirect the helper's stderr, so `carry_state.py`'s own refusal line (`refused: last pass head_sha is not a commit sha`) comes first. Hiding it with `2>/dev/null` would lose the diagnostic.
- **Fix:** The shared halt assertion checks that the last stderr line is `HEAD_SHA_HALT`. The payload test checks the exact two lines: the helper's reason, then the halt sentence. The missing-state-file test also uses the last-line check, because bash writes its own redirect error first.
- **Cost if wrong:** low. If the owner wants a single-line stderr, the fence would need a `2>/dev/null` and the test would go back to an equality check.
- **Files modified:** test_diff_ranges.py
- **Commit:** dfca59c

**2. [Minor] Removed a stray space before a period.**
- `head_sha_binding_holds` reads the step-3 range-source line from the text it is given, not from `range_source_lines((STATE_MD,))`. This lets the mutants run on edited text. TestRangeSourceLines still reads the file.
- The 30-collect-score.md paragraph edit left a stray space before the period, and it was fixed before the GREEN commit.

## Threat Flags

None. The plan adds no network, auth, or file-access paths. T-60-32 to T-60-35 are mitigated as the threat register describes, and T-60-36 is accepted (40- and 64-hex accepted; an empty PHASE_START still falls back to HEAD).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: 05-state.md (last-head-sha fence), 00-scope.md (check line), 30-collect-score.md (rule sentence), test_diff_ranges.py (class TestStateHeadShaFence, class TestSubstitutedValueProse)
- FOUND commits: dfca59c (RED), 5d81170 (GREEN)
