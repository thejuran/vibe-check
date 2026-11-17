---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
plan: 03
subsystem: release-gate
tags: [wr-02, tdd, state-key, gsd-route, mutant, named-growth]
requires:
  - "65-01: 65-REPRO-WR02.md Verdict QUALIFYING and Owner go: GRANTED (owner, 2026-11-16)"
provides:
  - "05-state.md GSD state-key block refuses an empty phase id before any path is bound"
  - "00-scope.md prints PHASE_ID= next to PHASE_DIR=; 05-state.md tells the model to substitute it"
  - "WR-02 locks with before/after cases and mutants (test_pasted_name_guard.py, test_cross_call_vars.py)"
  - "65-REPRO-WR02.md ## Fix and ## Named growth from the fix (+495 B on every path, 0 steps)"
affects:
  - "65-04 builds candidate C from b281042 (the fix changes the candidate)"
  - "65-07 must correct backlog 999.38: WR-02 WAS a regression from 2.14.1 (now fixed)"
  - "D-04 growth reconciliation: one new named-growth row pair (00-scope.md +149 B, 05-state.md +346 B)"
tech-stack:
  added: []
  patterns: ["needle-based one-line mutant (without_line) generalising unguarded()", "record row disposition per fixing plan (FIXED_DISPOSITIONS)"]
key-files:
  created:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-03-SUMMARY.md
  modified:
    - plugins/vibe-check/phases/review/00-scope.md
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/scripts/test_pasted_name_guard.py
    - plugins/vibe-check/scripts/test_cross_call_vars.py
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-REPRO-WR02.md
decisions:
  - "WR-02 fixed in the one D-08 round: empty phase id stops at 05-state.md with 'Review halted — the phase id is empty; nothing was scored.'"
  - "WR-02 was a regression from 2.14.1; backlog 999.38's 'none is a regression' line is wrong for it (65-07 carries the ROADMAP correction)"
  - "Named growth from the fix: +495 bytes on all six paths, 0 Bash steps"
metrics:
  duration: "~35 min"
  completed: 2026-11-16
  tasks: 2
  files: 5
---

# Phase 65 Plan 03: WR-02 fix round (test-first) Summary

If a GSD review runs its state-key step with an empty phase id, the review now stops at that step with one sentence and prints no state path. Two GSD phases can no longer share `.turingmind/state/format-53/.json`. `00-scope.md` now prints `PHASE_ID=` where it resolves the phase folder, and `05-state.md` tells the model to substitute that literal. Each lock was shown failing on the unfixed text and on a mutant, and passing on the fix. The full suite passes: 4599 tests, 0 skipped.

## Gate

`65-REPRO-WR02.md` reads `Owner go: GRANTED (owner, 2026-11-16)`, so the fix round ran. This uses up the one D-08 round.

## Task 1: RED (`976e3fe`)

Tests added:
- `test_pasted_name_guard.py`
  - `TestStateFileGuard` bad cases `gsd empty-id` and `gsd unset-id`. Each requires exit 1, no `STATE_FILE=` or `LEGACY_STATE_FILE=` line, and stderr exactly `Review halted — the phase id is empty; nothing was scored.`
  - `test_without_the_empty_id_refusal_the_shared_file_returns`.
  - `TestPhaseIdPrinted.test_the_phase_id_is_printed_and_carried`. It covers a flat and a milestone-nested `02-b`. The 00-scope block must print `PHASE_ID=02-b`. With that literal substituted into the 05-state block, it must print `STATE_FILE=.turingmind/state/format-53/02-b.json`.
  - `unguarded()` now uses the new `without_line(body, needle)` helper, which removes exactly one line.
- `test_cross_call_vars.py`
  - `REPRO_63` row `WR-02`: file 05-state.md, name PHASE_ID, outcome `wrong-file`, proposed `fix`, disposition `reproduced; fixed by 65-03`.
  - `TestRepro63.test_wr02_empty_phase_id`. It runs phase B's Close out, with phase A's saved progress at the shared key and the id not typed in. The run must classify `stop`. The control, with `02-b` typed in, must reach `stop-no-state`.
  - `TestCrossFile.test_mutant_phase_id_sentence_removed_trips`.
  - `test_x1_phase_dir` now expects the new `PHASE_ID=` line. This is the only change to an existing lock: it pins the exact output of the PHASE_DIR block.

RED run on the unfixed text: 8 failed, 82 passed. The failing test ids:
- `TestStateFileGuard::test_bad_names_are_refused_and_nothing_runs` [gsd empty-id], [gsd unset-id]
- `TestStateFileGuard::test_without_the_empty_id_refusal_the_shared_file_returns`
- `TestPhaseIdPrinted::test_the_phase_id_is_printed_and_carried` [flat], [milestone-nested]
- `TestCrossFile::test_mutant_phase_id_sentence_removed_trips`
- `TestRepro63::test_wr02_empty_phase_id`: `'wrong-file' != 'stop'`, the same class that 65-01's Walk B recorded
- `TestRepro63::test_x1_phase_dir`

## Task 2: GREEN (`b281042`) and named growth (`ce79e9c`)

- `05-state.md` changes:
  - The first line of the GSD block is now `[ -n "${PHASE_ID}" ] || { echo "Review halted — the phase id is empty; nothing was scored." >&2; exit 1; }`.
  - A sentence after the block says `${PHASE_ID}` is the literal printed after `PHASE_ID=` by `00-scope.md` and must be substituted.
  - The D-21 unsafe-name guard is byte-identical.
- `00-scope.md`: the phase-folder block runs `PHASE_ID=$(basename "$PHASE_DIR")` and `printf 'PHASE_ID=%s\n' "$PHASE_ID"`. The prose now names the printed literal.
- Targeted tests: `test_pasted_name_guard.py`, `test_cross_call_vars.py` and `test_statepath.py` gave 148 passed, 311 subtests passed.

### Mutant evidence

Each mutant was applied to the fixed files, run, then restored.

| Mutant | Result |
|---|---|
| Empty-id refusal line removed from 05-state.md | 4 failed: both empty-id subtests, the shared-file test, `test_wr02_empty_phase_id` |
| `printf 'PHASE_ID=` removed from 00-scope.md | 4 failed: both `TestPhaseIdPrinted` subtests, the cross-file whole-tree check, `test_x1_phase_dir` |
| `PHASE_ID=` substitute sentence removed from 05-state.md | 2 failed: the cross-file whole-tree check and `test_mutant_phase_id_sentence_removed_trips` |
| Restored (fixed text) | 86 passed, 191 subtests passed |

Inside the suite, `test_without_the_empty_id_refusal_the_shared_file_returns` also deletes the refusal line. It asserts exit 0 and the printed `STATE_FILE=.turingmind/state/format-53/.json`, so the lock is proven to carry weight on every run.

### After evidence

The Walk A part of the 65-01 script `wr02_repro.py` was run on the fixed tree (`env -i`, no `PHASE_ID`). It exits 1 with empty stdout and the halt sentence on stderr. The script's Walk B can't run as written: phase A's block now prints no `STATE_FILE=` line, so the script stops at its first `printed_literal`. The in-suite test `test_wr02_empty_phase_id` covers that chain and classifies it `stop`.

### Full suite

Run in the main checkout from the repo root: `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools -rs`

Result: **4599 passed, 2 warnings, 6481 subtests passed in 355.40s**. 0 failed, 0 errors, 0 skipped.

### Named growth (D-04)

Counts are from `976e3fe` to `b281042`.

| File | Δ bytes | Δ steps |
|---|---|---|
| 00-scope.md | +149 | 0 |
| 05-state.md | +346 | 0 |

Every path grows by +495 bytes (+141 tokens@3.5): finalize, review-plain, deep-plain, review-all, deep-all and fix-loop. Bash steps are unchanged on all six, because the new lines sit inside existing fences. The full table is in `65-REPRO-WR02.md` under `## Named growth from the fix`.

## Correction for 65-07 (do not lose)

Backlog 999.38 in ROADMAP.md says none of its items are regressions from 2.14.1. That is **wrong for WR-02**:
- Under the fresh-shell standard, 2.14.1 fails closed ("No prior review passes.").
- The pre-fix candidate instead closed phase B on phase A's state.

So WR-02 was a regression, and it is now fixed by `b281042`. This plan did not edit ROADMAP.md, because 65-07 owns it. The correction is also recorded in `65-REPRO-WR02.md` under `## Fix`.

## Deviations from Plan

**1. [Rule 3 - Blocking] `test_x1_phase_dir` exact-output lock updated**
- **Found during:** Task 1
- **Issue:** the test pins the PHASE_DIR block's whole stdout, so the new `PHASE_ID=` line breaks it.
- **Fix:** the expected output now includes `PHASE_ID=02-code-review\n`. The plan allows this under "a needle must follow the new fence text".
- **Cost if wrong:** low. The test still pins the exact output, now including one more line.
- **Commit:** `976e3fe`

**2. [Rule 2 - Missing lock] Disposition `reproduced; fixed by 65-03` and a cross-file sentence lock**
- **Found during:** Task 1
- **Issue:** `record_problems` accepted only the `fixed by 63-10` disposition, which would mislabel WR-02. The new prose sentence in 05-state.md also had no lock of its own.
- **Fix:** added `FIXED_65` and `FIXED_DISPOSITIONS` (the record mutant test now iterates them too). Added `test_mutant_phase_id_sentence_removed_trips`. Fix-round mutant runs showed the existing cross-file whole-tree check already trips when the sentence is removed.
- **Cost if wrong:** low. Unknown dispositions still trip.
- **Commit:** `976e3fe`

**3. Extra bad case `gsd unset-id`**
- **Found during:** Task 1
- **Issue:** the plan named only the empty value. A real fresh shell has `PHASE_ID` unset, not empty.
- **Fix:** added `gsd unset-id` alongside `gsd empty-id`.
- **Cost if wrong:** none.

## Known Stubs

None.

## Threat Flags

None. The change narrows an existing boundary (T-65-06 mitigated, T-65-07 guard line unchanged, T-65-08 gate checked).

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/00-scope.md, plugins/vibe-check/phases/review/05-state.md, plugins/vibe-check/scripts/test_pasted_name_guard.py, plugins/vibe-check/scripts/test_cross_call_vars.py, 65-REPRO-WR02.md
- FOUND commits: 976e3fe, b281042, ce79e9c
