---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 14
subsystem: fix-loop-card
tags: [gap-closure, fix-loop, temp-files, close-out, stale-card, prose-locks]
requires:
  - "58-16 (Finalize reads the fix-loop card's printed ROWSFILE= path and expects Close out to keep it)"
provides:
  - "Fix-loop prints every temp path (NAME=<path>) and reuses it only as a literal"
  - "Rerun, Close out and the D-08 fallback remove $SUGGESTFILE/$REFSFILE/$RESOLVEFILE; the rows file is kept"
  - "Close-out marker / step 2 read close_out only from this step's printed resolve output"
  - "Stale re-map source = the previous pass's printed ROWSFILE= path; no path -> D-08 fallback"
  - "Finalize-routed subset no longer prints Finalize's echo_text a second time"
affects:
  - "58-18 (gate checks 90-finalize.md and 50-fix-loop.md agree)"
tech-stack:
  added: []
  patterns: ["printed-path literal convention across Bash calls", "real-file mutant table", "fresh-shell fence walk"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/scripts/test_fix_loop_card.py
decisions:
  - "A carried close-out is valid only when the answer acted on in this step came through Translate's ok-true branch and its printed resolve output had close_out true; a close_out in an earlier answer's file is never read"
  - "The Rerun and Close out keep this pass's rows file (next pass's / Finalize's prior-rows source) and remove only the answer files"
  - "'bottom line' is accepted only for a Bottom line suggests: line printed on the card currently shown"
metrics:
  duration: "~25 min"
  completed: 2026-10-27
  tasks: 3
  files: 2
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 14: Fix-loop printed paths, answer-file lifecycle, close-out source, stale source, single echo Summary

The fix-loop card now prints every temp file path it creates (`ROWSFILE=`, `ANSWERFILE=` in both rows fences, `PARSEFILE=`, `DECFILE=`, `RESOLVEFILE=`, `PAYLOADFILE=`, alongside the already-printed `SUGGESTFILE=`, `SUBSETFILE=` and `REFSFILE=`), and one sentence says a printed path is reused only as that literal (WR-06). The Rerun, Close out and the D-08 full-card fallback remove the suggestion, refs and resolve files, so a stale `close_out` or suggestion can't be acted on later (WR-01, WR-02). The close-out marker is bound to this step's resolve output (WR-01). The stale re-map reads from the previous pass's printed `ROWSFILE=` path, which the Rerun keeps, and falls back when there is none (WR-05). Finalize's `echo_text` is printed once (IN-05). The wording matches the Finalize side that landed in 58-16 ("printed after `ROWSFILE=`", rows file kept at Close out, answer files removed).

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | RED: `printed_paths_problems`, `answer_files_problems`, `close_out_source_problems`, `stale_source_problems`, `single_echo_problems` + `TestGapRoundFixLoop` | 163de79 | scripts/test_fix_loop_card.py |
| 2 | Prose: printed paths, answer-file clears, close-out source, stale source, single echo | 2bac051 | phases/review/50-fix-loop.md |
| 3 | Real-file mutants L1-L7 + fence walk | none (all mutants killed, no needle added; see Deviations) | — |

## RED evidence (Task 1, against prose at 5041f95)

`pytest -q --tb=no scripts/test_fix_loop_card.py -k "GapRoundFixLoop or subset_no_card or typed_bottom or bottom_line"` → **28 failed, 7 passed** (counting subtests). All five `_holds` tests failed. The `_mutant` tests failed too, because their baseline needles are not in the HEAD prose yet. The three updated existing locks also failed: `test_subset_no_card`, `test_bottom_line_holds` and `test_typed_bottom_line_holds`.

Problems reported on HEAD:
- `printed_paths_problems`: unprinted ROWSFILE ×2, ANSWERFILE ×2, PARSEFILE, DECFILE, RESOLVEFILE, PAYLOADFILE; convention sentence appears 0 times
- `answer_files_problems`: Rerun/Close out/D-08 fallback do not clear answer files; suggestion read from `$SUGGESTFILE` exists for this pass; typed bottom line not tied to the card shown; question note not tied to this pass; carry paragraph still says "none of which survive it"
- `close_out_source_problems`: Rerun lacks CLOSE_OUT_SOURCE and NEVER_STALE; Rerun and step 2 still read close_out from `$RESOLVEFILE`
- `stale_source_problems`: lacks all four source needles; still names "that pass's `$ROWSFILE` path, used as is"; Rerun lacks "keep this pass's `$ROWSFILE`"
- `single_echo_problems`: subset bullet lacks the do-not-print-again sentence; card still says "Then print Finalize's `echo_text`"

## GREEN

After Task 2, `pytest -q scripts/test_fix_loop_card.py scripts/test_card_text.py scripts/test_pause_batching.py scripts/test_scope_args.py` → **209 passed, 586 subtests passed**. This includes `test_subset_no_card`, its mutants A/B/C and `TestCarrierRoundTrip`.

Acceptance greps on `50-fix-loop.md`: `printf 'RESOLVEFILE=%s` = 1; `printf 'ROWSFILE=%s` = 2; `printf 'PARSEFILE=%s` = 1; `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` = 3; forbidden residues (`none of which survive it`, `was true in `$RESOLVEFILE``, `exists for this pass`, `Then print Finalize`) = 0; `printed after `ROWSFILE=`` = 1.

Full suite: **3526 passed, 4686 subtests passed** (was 3516; +10 new tests), 0 failed.

## Real-file mutants (Task 3)

I applied each mutant to the real `50-fix-loop.md` with a scratchpad Python driver, ran `pytest -q scripts/test_fix_loop_card.py`, then ran `git checkout --` on the file and asserted `git status --porcelain` was empty after each one. The file is clean at the end.

| ID | Mutant on the real file | Result | Failing tests |
|----|-------------------------|--------|---------------|
| L1 | delete `printf 'RESOLVEFILE=%s\n' "$RESOLVEFILE"` | 2 failed | test_printed_paths_holds, test_mutant_printed_paths |
| L2 | delete the Rerun's `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` | 2 failed | test_answer_files_holds, test_mutant_answer_files |
| L3 | restore "none of which survive it" | 2 failed | test_answer_files_holds, test_mutant_answer_files |
| L4 | restore "`$SUGGESTFILE` exists for this pass" (typed path) | 3 failed | test_answer_files_holds, test_mutant_answer_files, test_typed_bottom_line_holds |
| L5 | restore "When `close_out` was true in `$RESOLVEFILE`" | 2 failed | test_close_out_source_holds, test_mutant_close_out_source |
| L6 | restore "that pass's `$ROWSFILE` path, used as is" | 2 failed | test_stale_source_holds, test_mutant_stale_source |
| L7 | restore "Then print Finalize's `echo_text` as message text, " | 4 failed | test_single_echo_holds, test_mutant_single_echo, test_subset_no_card, test_mutant_subset_asks_again |

Every mutant failed at least one test, so none survived.

## Fence walk (fresh shells, real fences extracted from 50-fix-loop.md)

The driver extracted the fences from the real file. Each step ran in its own `bash -s` with only `PATH`, `VC_ROOT` and `TMPDIR` (the scratchpad) set. No variable carried between steps. The rows doc was the eight-row `test_answer_resolve.iplayarr_rows()` fixture. The refs file was written by the driver, standing in for the Write tool, as `{"refs":[{"verb":"fix","kind":"number","n":5}],"reason":null,"close_out":true}`.

| Step | Shell | Fence | Observed |
|------|-------|-------|----------|
| A | fresh | ordinary rows fence, create+print lines (fixture copied into the printed ROWSFILE) | exit 0; printed `ROWSFILE=…/vc.tiHJBj`, `ANSWERFILE=…/vc.hLRhN6` |
| B | fresh | Translate create fence | exit 0; printed `REFSFILE=…/vc.1Ioqfd`, `RESOLVEFILE=…/vc.wdUWHj` |
| C | fresh | resolve fence, printed literals substituted | exit 0; `{"ok": true, …, "close_out": true, …, "grammar": "fix 5"}` |
| D | fresh | grammar copy fence, literals | exit 0; ANSWERFILE = `{"q1": "fix 5", "q2": null}` |
| E | fresh | parse fence, literals | exit 0; printed `PARSEFILE=…/vc.mrukgS`, `"ok": true`, `fix_targets` = [row 5 hash], `echo_text` starts `fix: #5 src/browse/recovery.ts:118` |
| F | fresh | resolve fence, **variable form** (the WR-06 failure) | `bash: line 1: : No such file or directory` then `— nothing was recorded; the answer could not be read.` The unset `$RESOLVEFILE` makes `> ""` fail before the helper runs |

Step F reproduces the reviewed symptom: without the printed literal, the separate Bash call has no path, and the answer is never read. Steps C–E show the same fences succeed across separate shells once the printed literals are substituted.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated `BOTTOM_LINE_QUESTION_NOTE`**
- **Found during:** Task 1
- **Issue:** The plan's Q-line rewording ("…printed a `SUGGESTFILE=` path created on this pass") would break the existing `bottom_line_problems` lock, which pinned the old "`$SUGGESTFILE` exists for this pass" wording. The plan listed only `SUBSET_NO_CARD` and `TYPED_BOTTOM_LINE_NEEDLES` as constants to update.
- **Fix:** Pinned the new Q-line wording in the constant during the RED commit, so `test_bottom_line_holds` was RED on HEAD and GREEN after the prose change.
- **Cost if wrong:** One constant reverts. The lock would then pin stale wording the plan explicitly removes.
- **Files modified:** plugins/vibe-check/scripts/test_fix_loop_card.py
- **Commit:** 163de79

**2. [Scope] Task 3 produced no commit**
- **Found during:** Task 3
- **Issue:** The plan's commit for Task 3 is conditional ("If any mutant survives, add the missing needle"). All seven mutants were killed on the first run.
- **Fix:** No test change was needed. The evidence is recorded here instead.
- **Cost if wrong:** None. No code was changed.

**3. [Rule 2 - Correctness] Extra residue checks**
- **Found during:** Task 1
- **Issue:** The plan required the Rerun to gain the close-out source clause. That alone would not catch the old `(`close_out` true in `$RESOLVEFILE`, D-17)` parenthetical if it stayed beside the new clause.
- **Fix:** `close_out_source_problems` also reports when "`close_out` true in `$RESOLVEFILE`" remains in the Rerun paragraph. I also wrote "substitute the printed `ROWSFILE=`, `REFSFILE=` and `RESOLVEFILE=` paths" into the resolve and grammar-copy lead-ins, mirroring 58-16.
- **Cost if wrong:** One more needle to update if the Rerun is reworded.
- **Commit:** 163de79, 2bac051

## Known Stubs

None.

## Threat Flags

None. No new surface: the change is prose plus tests. Owner text still reaches helpers only through files written with the Write tool.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/50-fix-loop.md (modified)
- FOUND: plugins/vibe-check/scripts/test_fix_loop_card.py (5 `def *_problems` helpers added)
- FOUND: 163de79, 2bac051
