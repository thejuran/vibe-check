---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 13
subsystem: vibe-check fix loop / Phase 0 normalizer
tags: [gap-closure, tests, mutants, docs, ANSR-01]
requires: [58-07, 58-08]
provides:
  - non-decorative close-out round-trip (IN-04)
  - D-20 hand-typed marker documentation + lock (SA-03)
affects: [plugins/vibe-check/scripts/test_fix_loop_card.py, plugins/vibe-check/phases/review/00-scope.md, plugins/vibe-check/scripts/test_scope_args.py]
tech-stack:
  added: []
  patterns: [derive test inputs through the real fence, real-file mutant before/after]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_fix_loop_card.py
    - plugins/vibe-check/phases/review/00-scope.md
    - plugins/vibe-check/scripts/test_scope_args.py
decisions:
  - "IN-04: ${original_args} in the close-out round-trip is derived by the real normalizer from the Rerun's marker-carrying $ARGUMENTS, not typed in clean"
  - "D-20: hand-typed --close-out-after-rerun on a first run is documented as accepted; no behaviour change"
metrics:
  duration: ~15m
  completed: 2026-10-27
  tasks: 2
  files: 3
requirements: [ANSR-01]
---

# Phase 58 Plan 13: Carrier round-trip made real + D-20 documented Summary

`test_close_out_drops_the_marker` now builds `${original_args}` by running the real 00-scope.md fence on `49-foo --close-out-after-rerun`, so deleting the normalizer's marker strip makes it fail in bash and zsh. The D-20 acceptance of a hand-typed marker is one locked sentence in the normalizer paragraph.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | IN-04: close-out round-trip through the real normalizer + strip mutant | 0d62cd5 | scripts/test_fix_loop_card.py |
| 2 | D-20: hand-typed marker sentence + D20_NEEDLE lock + m8 mutant | dac386d | phases/review/00-scope.md, scripts/test_scope_args.py |

## Mutant evidence (all on the real files, reverted after; tree clean except the pre-existing .planning/HANDOFF.json)

| Mutant | Applied to | Test | Before change | After change |
| ------ | ---------- | ---- | ------------- | ------------ |
| Strip removed: delete `s/ --close-out-after-rerun( --close-out-after-rerun)* / /g; ` | 00-scope.md (real file) | old `test_close_out_drops_the_marker` | **PASSED** (1 passed, 2 subtests): decorative, confirmed | n/a |
| Same strip mutant | 00-scope.md (real file) | new `test_close_out_drops_the_marker` | n/a | **FAILED**: SUBFAILED shell=/bin/bash and shell=/bin/zsh |
| Same strip mutant, in memory | normalizer block | `test_mutant_strip_removed_marker_would_carry` | n/a | passes (asserts marker kept and carrier_flag != "0") |
| D-20 sentence absent (RED, before prose edit) | 00-scope.md at HEAD | `test_d20_hand_typed_marker_documented`, `test_m8_d20_sentence_deleted_trips` | **2 failed** | 2 passed after the sentence was added |
| D-20 sentence deleted after the edit | 00-scope.md (real file) | `test_d20_hand_typed_marker_documented` | n/a | **FAILED**, restored, 2 passed again |

## Verification (observed)

- `pytest -q scripts/test_fix_loop_card.py -k CarrierRoundTrip` -> 4 passed, 8 subtests passed (bash + zsh)
- `pytest -q scripts/test_scope_args.py -k "d20 or m8"` -> 2 passed
- `pytest -q scripts/test_scope_args.py scripts/test_fix_loop_card.py` -> 151 passed
- Full suite (`pytest -q` in plugins/vibe-check) -> 3485 passed, 0 failed (3482 + 3 new)
- `grep -c '(D-20)' 00-scope.md` -> 1; the 00-scope.md diff is one removed and one added line (the paragraph line, prose only; fence untouched)
- Clean-literal count `replace("${original_args}", "49-foo")`: HEAD~ 2 -> now 1 (measured with `grep -cF`; the plan's non-`-F` grep returns 0 on both because the BRE reads `{` specially)

## Deviations from Plan

- In the new test the derivation runs per shell, inside the subTest loop, so the bash and zsh fences each derive their own `${original_args}`. The plan derived it once. This is a tighter version of the same check.
  - **Cost if wrong:** none. Same assertions, run once per shell.
- The m8 lock checks for the sentence within the normalizer paragraph (the single line that starts with `**Pre-mode universal-flag normalizer`), using a new `d20_problems` helper that follows the existing `*_problems` pattern.
  - **Cost if wrong:** low. If the paragraph heading is renamed, the lock reports a problem and does not pass silently.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_fix_loop_card.py, plugins/vibe-check/phases/review/00-scope.md, plugins/vibe-check/scripts/test_scope_args.py
- FOUND commits: 0d62cd5, dac386d
