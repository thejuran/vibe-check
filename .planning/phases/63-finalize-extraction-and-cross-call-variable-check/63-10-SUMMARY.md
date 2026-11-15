---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 10
subsystem: review instructions (shared phase files) and the cross-call check
tags: [cross-call, shell, instructions, tdd, footprint]
requires:
  - 63-09 owner decision (fix all six)
provides:
  - X1-X6 fixed; cross-call exceptions list empty
  - 63-COUNTS.md "Phase end" and "Named growth from cross-call fixes (D-09)"
  - 63-REPRO.md fix records, reverse run, open STATE_FILE item
affects:
  - every review path (plain, --all, deep, deep --all, Finalize, fix loop) loads the three changed files
tech-stack:
  added: []
  patterns:
    - printed-path rule (print NAME=<value>, later block substitutes the literal)
    - merge a setter into its only reader block when nothing sits between them
key-files:
  created:
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-10-SUMMARY.md
  modified:
    - plugins/vibe-check/phases/review/00-scope.md
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/phases/review/06-config.md
    - plugins/vibe-check/scripts/test_cross_call_vars.py
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REPRO.md
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-COUNTS.md
decisions:
  - "X1 and X2/X3 fixed by print and substitute; X4-X6 by merging the three reads into the settings-reader block (least-growth shape that applied)"
  - "05-state.md prints each FILE name with its own printf line so counting rule v1 sees and counts the pastes (a two-name printf would hide them from the counter)"
  - "The 90-finalize.md cross-file STATE_FILE read reproduces; recorded for an owner decision, not fixed"
metrics:
  duration: "about 55 minutes"
  completed: 2026-11-15
  tasks: 2
  files: 6
---

# Phase 63 Plan 10: Cross-call fixes and phase-end figures Summary

The six shell values that did not survive between separate Bash calls are now fixed. The phase dir and the two state-file names are printed and the later blocks substitute them. The repo root and both flags are read inside the block that calls the settings reader. The exceptions list is empty. Each fix is proven by a fixture that passes now and fails on the pre-fix files. Growth is +609 bytes on every review path and +2 counted steps on the Finalize path, itemised by reproduction.

## What was done

**Task 1: fixes, test-first, one group at a time.** For each group there is a RED commit (the fixture rewritten to expect the repaired behaviour, failing) and a GREEN commit (the instruction edit, the pair removed from `EXCEPTIONS`, the row's `disposition` set to `reproduced; fixed by 63-10`, and a mutant that re-breaks the file and shows the check flags it again).

| Ids | File | Fix shape | RED | GREEN |
|-----|------|-----------|-----|-------|
| X1 | phases/review/00-scope.md (`PHASE_DIR`) | print and substitute | 09b969d | c4c84a3 |
| X2, X3 | phases/review/05-state.md (`LEGACY_STATE_FILE`, `STATE_FILE`) | print and substitute, one sentence for every later block | 7722c0f | 7bd3274 |
| X4, X5, X6 | phases/review/06-config.md (`CODEX_FLAG_VAL`, `CONFIG_REPO_ROOT`, `MIN_CONFIDENCE_FLAG_VAL`) | merge (three one-line blocks moved into the reader block) | 47a2e4a | 936d29e |

The fixtures run the setter block, read its printed `NAME=` line, substitute that literal for `$NAME` in the reader blocks, run each block as its own fresh shell, and require the outcome class `harmless`: the same exit codes, output and files as the one-shell control. The settings fixtures require `--codex off`, `--min-confidence 45` and the repo's `[agents] disabled = ["style"]` to take effect.

Record lock: each `REPRO_63` row has a `disposition` field. `record_problems` now requires fixed rows to be off the list, pinned rows on it, and no unknown values. New mutants cover a dropped field, a fixed row put back on the list, a pinned row taken off it, and an unknown value. Mutant (h) uses a synthetic stale pair, so it still trips with an empty list.

**Reverse run** (recorded in 63-REPRO.md, commit 85a086c). I made a detached scratch worktree at `c7d92c9`, copied in the new test file, and ran `-k "TestRepro63 and not Record"`. Result: `9 failed, 2 passed, 57 deselected`. Every flipped fixture failed: X1, X2 (both keys), X3 (both keys and Close-out), X4, X5 and X6. The 2 passes are the X2 and X3 parent tests, whose subtests carry the failures. The scratch worktree was then removed.

**Task 2: figures** (63-COUNTS.md, commit 44a8472; E = `85a086c`):
- steps, Finalize path: 92 → 83 (extraction alone) → 85 (phase end)
- bytes, Finalize path: 136114 → 129451 → 130060
- review-plain: 192057 / 192057 / 192666; deep-plain: 268997 / 268997 / 269606 (dd8e4ab / c7d92c9 / E)
- per fix: X1 +211 bytes / 0 steps; X2 +110 / +1; X3 +82 / +4; the X2+X3 shared sentence +245 / 0; X4, X5 and X6 −13 / −1 each. Total +609 bytes, +2 steps. These match the 63-09 estimate (+600 to +1450 bytes, +2 steps).
- `git diff --stat c7d92c9 85a086c -- phases commands agents` lists only the three files. The `Verdict (extraction alone): PASS` line is unchanged.

## Verification (observed)

- `pytest -q -p no:cacheprovider test_cross_call_vars.py`: 63 passed, 78 subtests passed.
- Plan Task 1 record check: `OK 0 pinned`. `git diff --quiet c7d92c9 HEAD -- phases/shared commands agents`: exit 0 (`OK2`).
- Plan Task 2 check: `step_count.py --rev 85a086c…` prints 85, and the file has `→ 85 (phase end)` and both headings.
- `finalize_capture.py compare … --driver helper --commit 85a086cb…`: exit 0, last line `finalize outcome fields match (5 situations, 7 walks)`. `finalize_capture.py verify`: `finalize baseline matches (5 situations)`. `baseline_records.py verify --repo .`: `baseline holds`.
- D-03 files: `commands/review.md`, `phases/shared/00-contract.md` and `phases/shared/01-bootstrap.md` are byte-identical to dd8e4ab (`git diff --quiet` exit 0). `00-scope.md`, `05-state.md` and `06-config.md` changed on purpose (+11/−15 lines).
- Full suite (`plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`, run once): `5 failed, 4531 passed, 1 skipped, 5628 subtests passed in 281.10s`. The 5 failures are the known worktree-only `test_replay.py::TestPhase53SameLineRegressionCases` cases. The skip is `test_replay.py`'s linked-worktree skip, so no skip is new. No hidden lock fired, and **no test in any other module was updated**.
- Stdlib gate: `34 shipped .py files; third-party imports: none`.

## Open item: `$STATE_FILE` in 90-finalize.md (needs an owner decision)

This reproduces. The 05-state GSD-key block and the 90-finalize Finalize-inputs block were run as separate fresh calls in a temp repo holding a pass-1 state file. With no substitution instruction in `90-finalize.md`, the Finalize block gets an empty `$STATE_FILE` and returns `{"action": "error", "reason": "no prior review passes", "next": "stop-no-state"}`. The one-shell control returns `"action": "write"`. Run alone, the archive block exits 1 with "no file to archive". What the owner would see: Close out says there are no prior passes and writes nothing. `50-fix-loop.md` has the same cross-file read pattern; I did not run that one. This was not fixed (`90-finalize.md` is out of this plan's scope). It is recorded in 63-REPRO.md "Open item", with the fix shape and its counting effect. `05-state.md` now prints `STATE_FILE=`, so a fix is one substitution sentence per reading file. It would add paste steps to the Finalize count.

## Deviations from Plan

**1. [Rule 3 - Blocking] The record lock and mutant (h) were reworked so they hold with an empty exceptions list**
- **Found during:** Task 1 (X1 GREEN)
- **Issue:** `record_problems` treated any row not on the list as an error, `test_mutant_row_removed_trips` assumed X1 was listed, and mutant (h) needed at least one flagged and one listed pair. All three break once the list shrinks to empty, which the owner's decision requires.
- **Fix:** rows now carry `disposition`; fixed rows must be off the list and pinned rows on it. The row-removed mutant puts X1 back on a copy of the list. Mutant (h) uses synthetic unlisted and stale pairs.
- **Cost if wrong:** the record could accept a row whose disposition disagrees with the list. The new mutants cover both directions.
- **Commits:** 09b969d, c4c84a3

**2. [Rule 1 - Scope precision] X1 changed two short pieces of prose, not one sentence**
- **Found during:** Task 1 (X1 GREEN)
- **Issue:** the plan allows "the one sentence the fix needs", but `PHASE_DIR` has two reader blocks with separate lead-ins.
- **Fix:** one substitution sentence was added in the guard lead-in. In the range lead-in, the parenthetical "is the path resolved above" was replaced with the substitution form. Total +211 bytes.
- **Cost if wrong:** about 100 bytes more than a single sentence would add, on every path.
- **Commit:** c4c84a3

## Assumption Drift (advisory)

- **Found during:** the open-item check. **Planned:** the `$STATE_FILE` read in `90-finalize.md` might be harmless. **Actual:** it reproduces (Close out stops with "no prior review passes"). **Why:** the same-file check cannot see cross-file reads, and `90-finalize.md` has no substitution sentence. **Cost if wrong:** without a fix, Close out on a saved review can stop when the model does not carry the path on its own.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: printed-literal-substitution | phases/review/00-scope.md, phases/review/05-state.md | `PHASE_DIR` and the state-file names are now printed, and the model substitutes them inside double quotes in later blocks. Their characters come from the reviewed repo's `.planning/milestones/*` directory names, the repo folder name and the branch name. A name holding `$(...)` or `"` would be interpreted when substituted. This is the same pattern `30-collect-score.md` already uses for the state path. No allowlist was added, to keep each fix to its reproduced defect (D-08/D-09). A character filter in the setter blocks (as `PR_HEAD` has) would close it and is a candidate follow-up. |

## Known Stubs

None.

## Self-Check: PASSED

- Files: the three instruction files, `test_cross_call_vars.py`, `63-REPRO.md`, `63-COUNTS.md` and this SUMMARY are present.
- Commits: 09b969d, c4c84a3, 7722c0f, 7bd3274, 47a2e4a, 936d29e, 85a086c, 44a8472 are in `git log`.
