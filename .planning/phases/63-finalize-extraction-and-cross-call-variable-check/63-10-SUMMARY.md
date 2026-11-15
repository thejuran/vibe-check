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

## Follow-up (D-20, D-21)

Run 2026-11-15 after the owner's D-20 decision and the orchestrator's D-21 decision (63-CONTEXT.md). Same plan scope (`63-10`); no new PLAN file.

**D-21: a pasted name is refused if it holds a shell-live character.** The `PHASE_DIR` block (`00-scope.md`) and both state-file key blocks (`05-state.md`) now stop before printing when the value holds `$`, a backtick, `"`, `\`, a newline or a carriage return. One `case` line per block (`case "$V" in *[\$\`\"\\$'\n\r']*) echo "Review halted — … nothing was scored." >&2; exit 1;; esac`), bash 3.2 safe, no `eval`, every expansion quoted. Names with spaces and ordinary punctuation still pass.

**D-20: Close out and the fix loop use the printed state path.** One sentence each in `90-finalize.md` (first bullet of `## Finalize mode`) and `50-fix-loop.md` ("Temp paths are literals" paragraph): "In every fence of this file, `"$STATE_FILE"` is the literal printed after `STATE_FILE=` by `05-state.md` — substitute it[; a shell variable does not survive into a separate Bash call]." Nothing else in `90-finalize.md` changed.

**Cross-file companion check.** `test_cross_call_vars.py::TestCrossFile` flags a read of a name only another phase file sets unless the reading file names `` `NAME=` ``, and a setter of such a name that never prints it. Bootstrap names are exempt. `CROSS_FILE_EXCEPTIONS` (can only shrink) holds two places, recorded in 63-REPRO.md as "flagged, not reproduced / not decided": **C1** `05-state-all.md` `STATE_FILE` (the `--all` key is set but never printed, so the D-20 sentences have no printed line to point at on `--all`; the value is 12-hex) and **C2** `30-collect-score.md` `STATE_FILE` (already says to substitute "the literal state path bound in Phase 0.5", but does not name `STATE_FILE=`; likely harmless).

| Task | Commit | What |
|------|--------|------|
| A (RED) | dd9db3e | `test_pasted_name_guard.py`: real blocks in fresh `/bin/bash -s` inside temp repos with bad folder/branch/phase names; paste what was printed; no marker file; good names round-trip; guard-removed mutant |
| A (GREEN) | d168b85 | guard line in `00-scope.md` (1) and `05-state.md` (2) |
| B (RED) | 25dcb9d | `TestCrossFile`, `CROSS_FILE_EXCEPTIONS`, X7 / X8 rows and fresh-shell fixtures in `test_cross_call_vars.py` |
| B (GREEN) | 9a01055 | one sentence each in `90-finalize.md` and `50-fix-loop.md` |
| C | (records commit) | 63-COUNTS.md, 63-REPRO.md, 63-REMOVAL-LEDGER.md, 63-EQUIVALENCE.md |

**Fix-loop result.** It reproduced: with no substitution sentence, the fix-loop rows block run fresh exits 1 with `batch_card.py refused — fix loop cannot render its card; nothing was changed` (stop) while the one-shell control exits 0. Fixed with the one sentence, test-first (X8).

**Close-out result.** RED at 25dcb9d: Finalize returned `stop-no-state` ("no prior review passes"), no REVIEW.md. GREEN at 9a01055: `write-review-md`, REVIEW.md written, state archived, files identical to the one-shell control (X7).

**Paste sites and the guard** (full table in 63-REPRO.md "Pasted-name guard (D-21)"). Covered at the print site: `00-scope.md` guard and phase-range blocks (`PHASE_DIR`); `05-state.md` migrate/last-commit/decided/deferred blocks; `30-collect-score.md` since-review blocks (the scoring step's state-path paste); `90-finalize.md` and `50-fix-loop.md` state-file blocks. Covered upstream only: the `${PHASE_ID}` the model types into the `05-state.md` GSD key block (PHASE_ID is part of the guarded `PHASE_DIR`; the 05-state guard runs after that assignment, so on its own it would not stop a `$(…)` typed there). **Not covered:** the owner-typed `<ref>` / `<range>` arguments (from the owner's command line, not repo/branch/PR names; outside D-21). `05-state-all.md` is not printed (C1) and its value is hex from `statepath.py`.

**Figures** (63-COUNTS.md "Phase end after the D-20 / D-21 follow-up", at 9a01055). Finalize path steps 85 → 85; bytes 130060 → 130846. review-plain 192666 → 193267; deep-plain 269606 → 270207. Growth by item: D-21 guard `00-scope.md` +169 bytes / 0 steps, `05-state.md` +432 (216 × 2) / 0; D-20 sentence `90-finalize.md` +185 / 0, `50-fix-loop.md` +124 / 0; total +910 bytes, 0 counted steps. Rule v1 counts a `FILE` paste only when the same file prints the name, so the D-20 pastes are not counted (63-10 expected some); recorded as it fell.

**Verification (observed).**
- `pytest test_pasted_name_guard.py test_cross_call_vars.py`: 69 passed at d168b85 (guard); after 9a01055 the related modules (`test_cross_call_vars`, `test_pasted_name_guard`, `test_finalize_card`, `test_finalize_archive_prose`, `test_finalize_inputs`, `test_fix_loop_card`, `test_card_text`, `test_pause_batching`, `test_tracecheck`, `test_fixcommit`): 603 passed, 971 subtests passed. Fill-rules checksum and moved-passage pin in `test_finalize_card.py` pass.
- RED runs observed: guard tests 24 failed / 5 passed at dd9db3e; cross-file + X7/X8 5 failed at 25dcb9d (exactly the expected flags: 50-fix-loop and 90-finalize `STATE_FILE`).
- `finalize_capture.py compare … --driver helper --commit 9a01055`: `finalize outcome fields match (5 situations, 7 walks)` (also `--root plugins/vibe-check`). `verify`: `finalize baseline matches (5 situations)`. `baseline_records.py verify --repo .`: `baseline holds`. `docs/design/lean-v2.15/tools` tests: 355 passed. `finalize_capture.py` needed no change.
- Full suite, once: `5 failed, 4544 passed, 1 skipped, 5680 subtests passed in 325.33s`. The 5 failures are the known worktree-only `test_replay.py::TestPhase53SameLineRegressionCases` cases.
- `step_count.py` / `footprint.py` at 85a086c and 9a01055 as above; `git diff --stat 85a086c 9a01055 -- phases commands agents` lists only the four files.

**Named differences.** Added to 63-REMOVAL-LEDGER.md "Named differences from 2.14.1" as (6) the D-21 stop on an unsafe name (new behaviour; not exercised by any of the five situations) and (7) the D-20 repair (no change to the five situations); mirrored in 63-EQUIVALENCE.md "Named differences" item 2.

### Deviations (follow-up)

**1. [Scope note] The fix-loop sentence covers every block of the file, but only the rows block was run.** The record-decisions, payload and record-fix-verdicts blocks read the same name and are covered by the same sentence; building fixtures for them would need a full fix-loop answer set. Cost if wrong: a fix-loop block with a different failure mode stays untested in a fresh shell.

**2. [Test design] The GSD-key injection tests supply `${PHASE_ID}` from the environment instead of typing it into the block.** Typing a `$(…)` name into the block would run it at assignment, before any guard in that block; that path is covered upstream by the `PHASE_DIR` guard. Supplying it raw tests the 05-state guard itself. Cost if wrong: none for the shipped files; the table in 63-REPRO.md names the upstream-only coverage.

**3. [Rule 3 - Tooling] The known limit text in `test_cross_call_vars.py` was reworded** to describe the new companion (it still names "another file", which its lock requires). Cost if wrong: one sentence of test documentation.

### Assumption Drift (advisory, follow-up)

- **Found during:** figures. **Planned:** 63-10 expected the D-20 sentence to add paste steps on the Finalize path. **Actual:** 0 steps (rule v1 counts only pastes of names the same file prints). **Why:** the counter is per file. **Cost if wrong:** the step figure understates the model's pastes by the four `"$STATE_FILE"` uses in 90-finalize and four in 50-fix-loop; the bytes are counted.
- **Found during:** cross-file check. **Planned:** D-20 is about `05-state.md`'s printed path. **Actual:** on `--all`, `05-state-all.md` sets `STATE_FILE` and prints nothing, so the new sentences point at a line `--all` never prints (C1, not decided). **Cost if wrong:** `--all` Close out / fix loop may still hit the D-20 gap when the model does not carry the path itself.

### Self-Check (follow-up): PASSED

- Files present: `plugins/vibe-check/scripts/test_pasted_name_guard.py`, the four instruction files, `test_cross_call_vars.py`, and the four records.
- Commits in `git log`: dd9db3e, d168b85, 25dcb9d, 9a01055.
- STATE.md and ROADMAP.md not modified.

