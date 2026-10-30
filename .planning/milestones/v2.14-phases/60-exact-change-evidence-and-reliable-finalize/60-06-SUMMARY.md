---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 06
subsystem: review-range-builder
tags: [diff_ranges, fail-closed, gap-closure, mutation-tests]
gap_closure: true
requires: [60-02, 60-04]
provides: [diff_ranges suppressBlankEmpty context, REASON_ESCAPE, REASON_NOT_A_DIFF]
affects: [60-07, 60-09]
tech-stack:
  added: []
  patterns: [fixed-text refusal reasons, one-token source mutants]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/diff_ranges.py
    - plugins/vibe-check/scripts/test_diff_ranges.py
decisions:
  - "An empty hunk body line is a blank context line (diff.suppressBlankEmpty), not a malformed line"
  - "Any top-level line starting with ESC refuses with REASON_ESCAPE; non-empty text with no diff --/---/+++/hunk line refuses with REASON_NOT_A_DIFF; hunk-less real diffs (binary, mode-only) stay {}"
requirements: [EVID-01, EVID-03]
metrics:
  duration: ~15min
  completed: 2026-10-29
  tasks: 2
  files: 2
red_sha: 11d2b76
green_sha: b878870
---

# Phase 60 Plan 06: diff_ranges suppressBlankEmpty and fail-closed refusals Summary

`diff_ranges.py` now reads an empty hunk body line as a blank context line (so `diff.suppressBlankEmpty=true` no longer halts every pass) and refuses colored/escaped text (`colored or escaped diff`) and non-diff text (`not a unified diff`) with exit 2 instead of returning `{}` exit 0; empty, binary-only and mode-only diffs still give `{}`.

## Ledger SHAs (for 60-09)

- **RED SHA:** `11d2b76` — `test(60-06): red — suppressBlankEmpty context, colored/non-diff refusal, binary-only control`
- **GREEN SHA:** `b878870` — `fix(60-06): diff_ranges reads suppressBlankEmpty context and refuses colored or non-diff text`

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Red tests (suppressBlankEmpty, colored/non-diff refusal, binary/mode-only control, M20-M22) | 11d2b76 | test_diff_ranges.py |
| 2 | Green: empty body line is context; REASON_ESCAPE / REASON_NOT_A_DIFF; docstring | b878870 | diff_ranges.py |

## Red run (at 11d2b76, observed)

`pytest -q -p no:cacheprovider test_diff_ranges.py` tail: `12 failed, 82 passed, 60 subtests passed in 7.67s`. Failing set:

- `TestHazards::test_suppress_blank_empty_context_is_context` (default and -U10 subtests: `RangeError: unexpected line in hunk body`; -U0 passes, it has no blank context)
- `TestHazards::test_hostile_repo_config_does_not_change_ranges` (same halt; the hostile set now includes `diff.suppressBlankEmpty`)
- `TestRefusals::test_refuses_colored_diff` (RangeError not raised)
- `TestRefusals::test_refuses_non_diff_text` (error / stat / prose subtests: RangeError not raised)
- `TestRefusals::test_reasons_are_fixed_text` (AttributeError: no REASON_ESCAPE)
- `TestCli::test_colored_diff_exits_two_with_reason_only` (rc 0 != 2)
- `TestMutants::test_m20_/m21_/m22_` (anchors absent)

Controls green at RED: `test_binary_only_and_mode_only_diffs_are_empty`, `test_empty_diff_is_empty_result`.

## Green run (at b878870, observed)

- `pytest -q -p no:cacheprovider test_diff_ranges.py` → `89 passed, 65 subtests passed in 7.53s` (M1-M22 all trip)
- `pytest -q -p no:cacheprovider test_decision_continuity.py -k "TestRealDiffRanges60 or TestCoordinateSpaces60 or TestRepro60"` → `25 passed, 133 deselected, 47 subtests passed`
- Full suite `pytest -q -p no:cacheprovider` (plugins/vibe-check/scripts) → `3773 passed, 4936 subtests passed in 183.21s`, 0 failed
- Import set via `ast`: `['json', 're', 'sys']`; `^REASON_ESCAPE = |^REASON_NOT_A_DIFF = ` count 2; `REASON_` count 22
- Scratch-repo CLI (real git 2.55): suppressBlankEmpty diff → `{"f.txt": [[5, 5]]}` rc 0, identical to the unsuppressed diff; `git -c color.ui=always diff HEAD` → stderr `colored or escaped diff` rc 2; `printf 'fatal: bad revision\n'` → `not a unified diff` rc 2; empty stdin → `{}` rc 0
- `git diff --name-only 11d2b76~1..HEAD` lists only the two scripts files (no phase .md touched)

## Deviations from Plan

None in behavior. Note: the plan's named red set did not list `test_hostile_repo_config_does_not_change_ranges`, but the plan's own behavior for it (add `diff.suppressBlankEmpty` to the hostile set with a blank line next to the edit) necessarily turns it red pre-fix; it went green at b878870.
- **Cost if wrong:** none; the test is stricter than before and green at GREEN.

## Known Stubs

None.

## Threat Flags

None — T-60-13/14/15 mitigations applied as planned; T-60-16 control test (binary/mode-only `{}`) green at both SHAs.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/diff_ranges.py, plugins/vibe-check/scripts/test_diff_ranges.py
- FOUND commits: 11d2b76, b878870
