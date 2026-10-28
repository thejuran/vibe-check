---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 16
subsystem: finalize-card
tags: [gap-closure, finalize, temp-files, stale-card, prose-locks]
requires: []
provides:
  - "Finalize card prints every temp path (NAME=<path>) and reuses it only as a literal"
  - "Finalize clears $SUGGESTFILE/$REFSFILE/$RESOLVEFILE once the answer is acted on"
  - "Stale re-map source = the fix-loop card's printed ROWSFILE= path; no path -> D-08 fallback"
affects:
  - "58-14 (must make 50-fix-loop.md rows fences print ROWSFILE= and Close out keep that file + remove its suggestion file)"
  - "58-18 (gate checks 90-finalize.md and 50-fix-loop.md agree)"
tech-stack:
  added: []
  patterns: ["printed-path literal convention across Bash calls", "real-file mutant table"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "The stale-card source is only the fix-loop card shown before Close out in THIS session; with no printed ROWSFILE= path the answer goes to the full-card fallback with a 'no longer available' note"
  - "'bottom line' is accepted only for a Bottom line suggests: line printed on the card currently shown"
metrics:
  duration: "~15 min"
  completed: 2026-10-27
  tasks: 3
  files: 2
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 16: Finalize printed paths, answer-file cleanup, reachable stale source Summary

The Finalize card now prints every temp file path (`ROWSFILE=`, `ANSWERFILE=`, `PARSEFILE=`, `RESOLVEFILE=`, `DECFILE=`, plus the already-printed `SUGGESTFILE=`, `REFSFILE=`, `SUBSETFILE=`) and states once that a printed path is reused only as that literal (WR-06). It removes the suggestion/refs/resolve files once the answer is acted on (WR-02). Its stale-card re-map now reads from the fix-loop card's printed `ROWSFILE=` path, replacing the "earlier `--finalize`" case that could never be reached (WR-05).

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | RED: locks `check_printed_paths`, `check_answer_files`, updated `check_stale` + `TestGapRoundFinalize` | 2510f9c | scripts/test_finalize_card.py |
| 2 | Prose: printed paths, answer-file cleanup, fix-loop card as prior card | 3bce0f4 | phases/shared/90-finalize.md |
| 3 | Real-file mutants F1-F5 | none (no code change needed, see Deviations) | — |

## RED evidence (Task 1, against HEAD 6f41a9f prose)

`pytest -q scripts/test_finalize_card.py -k "GapRoundFinalize or stale"` → **11 failed, 5 passed**. Failing: `TestPhase58FinalizeRouting::test_stale_holds` (expected; the needle set changed), `TestGapRoundFinalize::test_{printed_paths,answer_files,stale_source}_holds`, and the `test_mutant_*` subtests (their `_mutant` anchors do not exist in the HEAD prose yet). Problems that the checks reported against HEAD:
- printed_paths: ROWSFILE, ANSWERFILE, PARSEFILE, RESOLVEFILE, DECFILE unprinted; convention sentence 0 times
- answer_files: no `rm -f` in step 2 / step 3 / D-08; Parse trusts any existing `$SUGGESTFILE`; Q1 and D-09 lines not tied to this card
- stale: 3 new needles missing; "an earlier `--finalize`" and "used as is" present

## GREEN (Task 2)

`pytest -q scripts/test_finalize_card.py scripts/test_card_text.py scripts/test_pause_batching.py scripts/test_finalize_archive_prose.py` → **117 passed, 243 subtests passed** (this includes every 58-05/58-09 `test_mutant_*`).
Acceptance greps on 90-finalize.md: `printf 'RESOLVEFILE=%s` 1, `printf 'ROWSFILE=%s` 1, `printf 'PARSEFILE=%s` 1, `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` 3, old phrases 0.
`an earlier \`--finalize\`` appears once in test_finalize_card.py, as the first entry of the `STALE_FORBIDDEN` constant (the forbidden-phrase list). The in-test mutant reuses it from there.

Full suite (`pytest -q` from plugins/vibe-check): **3491 passed, 0 failed** (3485 before, plus 6 new tests).

## Real-file mutants (Task 3)

Each mutant was applied to the real `90-finalize.md` by a scratchpad Python script, followed by `pytest -q scripts/test_finalize_card.py`, then a restore. `git checkout -- …90-finalize.md` ran afterwards and the tree was clean (only the pre-existing `.planning/HANDOFF.json` modification remained).

| Mutant | Change to the real file | Failing tests | Result |
|--------|-------------------------|---------------|--------|
| F1 | delete `printf 'RESOLVEFILE=%s\n' "$RESOLVEFILE"` | TestGapRoundFinalize::test_printed_paths_holds | killed (2 failed) |
| F2 | delete step 2's `rm -f …` sentence | TestGapRoundFinalize::test_answer_files_holds | killed (1 failed) |
| F3 | restore "`$SUGGESTFILE` exists for this card" in Parse | TestGapRoundFinalize::test_answer_files_holds | killed (2 failed) |
| F4 | restore "(a review pass re-ran, or an earlier `--finalize` built a card …)" | test_stale_holds, test_stale_source_holds | killed (3 failed) |
| F5 | restore "that card's `$ROWSFILE` path, used as is" | test_stale_holds, test_stale_source_holds | killed (3 failed) |

In-test mutants in `TestGapRoundFinalize` (all observed tripping on the fixed text): RESOLVEFILE printf removed; convention sentence dropped; step 2 `rm -f` replaced; `SUGGEST_OLD` re-added to Parse; D-09 "was removed at Close out" dropped; "an earlier `--finalize`" re-added; "used as is" re-added; "no longer available" dropped.

## Cross-file contract (58-14)

The Finalize stale paragraph says `$PRIORROWSFILE` is the literal path that the fix-loop card's rows fence "printed after `ROWSFILE=`" (Close out keeps that file). The D-09 paragraph says the fix-loop's suggestion file "was removed at Close out". **As of this commit, `plugins/vibe-check/phases/review/50-fix-loop.md` does not print `ROWSFILE=` yet** (its rows fences at :21 and :36 create it without printing), and it does not remove its suggestion file at Close out. Plan 58-14 must add both. 58-18's gate checks that the two files agree.

## Deviations from Plan

**1. [Process] Task 3 produced no commit**
- **Found during:** Task 3
- **Issue:** The plan named a `test(58-16): real-file mutants F1-F5` commit, but all five real-file mutants were killed by the Task 1 locks. No needle was missing, so there was no file change to commit.
- **Fix:** Recorded the mutant table here instead of making an empty commit.
- **Cost if wrong:** One missing commit in the history. The evidence lives in this SUMMARY.

**2. [Rule 2 - Correctness] `rm -f` wording covers files that were never printed**
- **Found during:** Task 2
- **Issue:** The suggestion file is optional (pure-prose Bottom line, or a separate `--finalize`), and refs/resolve exist only when a translation ran. A literal-substitution `rm -f` therefore has no path for a file that was never created.
- **Fix:** Each of the 3 `rm -f` sentences says "the literal paths this card printed; omit any never printed, a missing file is fine".
- **Cost if wrong:** Slightly longer prose. If wrong, the model passes an empty argument to `rm -f`, which is harmless.

Also added (within plan intent): the Parse `cp` sentence and the resolve/copy fences name which printed paths to substitute. Q1's slot and BOTTOM_NEEDLES were unchanged (BOTTOM_NEEDLES did not pin "`$SUGGESTFILE` exists").

## Known Stubs

None.

## Self-Check: PASSED
- FOUND: plugins/vibe-check/phases/shared/90-finalize.md, plugins/vibe-check/scripts/test_finalize_card.py
- FOUND commits: 2510f9c, 3bce0f4
