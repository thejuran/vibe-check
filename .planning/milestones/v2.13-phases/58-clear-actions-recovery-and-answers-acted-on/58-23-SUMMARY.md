---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 23
subsystem: plain-English answer resolver (batch_card.py resolve) + Translate prose
tags: [gap-closure, CR-01, D-23, rollback, title-matcher]
requires: ["58-19", "58-20", "58-21", "58-22"]
provides:
  - "batch_card._match_title back to the 58-10 strict all-words rule: a partial title match never acts"
  - "TestCR01StrictTitle: the reviewer's CR-01 phrasings ask, never act"
  - "58-REPRO.md ## CR-01 rollback (58-REVIEW-FINAL.md, D-23)"
affects: ["Phase 58 verification", "backlog: WR-02 re-opened, reviewer's safer design"]
tech-stack:
  added: []
  patterns: ["strict superset title match; ranked candidates only feed follow-up buttons"]
key-files:
  created:
    - .planning/phases/58-clear-actions-recovery-and-answers-acted-on/58-23-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/scripts/test_answer_resolve.py
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_fix_loop_card.py
    - plugins/vibe-check/scripts/test_finalize_card.py
    - .planning/phases/58-clear-actions-recovery-and-answers-acted-on/58-REPRO.md
decisions:
  - "Band words and possessive `s` stay in _TITLE_FILLER: under the strict rule filler can only drop a requirement, and no test or CR-01 fixture shows one widening a match to a wrong row"
  - "_title_scores kept (feeds _title_candidates, the likely-row follow-up buttons); _TITLE_MIN_MATCH removed"
metrics:
  duration: ~20m
  completed: 2026-10-28
  tasks: 3
  files: 7
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 23: CR-01 title-matcher rollback Summary

The title matcher is back to the 58-10 strict rule: a title reference names a row only when that row's title contains every non-filler word the owner used. With the strict rule in place, the CR-01 sentence "fix the option list on the browse page, then dismiss the other 7 fixed rows and close out" records nothing and the follow-up asks. The owner's verbatim iPlayarr sentence still gives `fix 5; dismiss 1,2,3,4,6,7,8`.

## Commits

| Task | Commit | Message |
|---|---|---|
| 1 RED | 801c3bb | test(58-23): add failing CR-01 strict-title fixtures; re-point best-match tests |
| 2 GREEN | 817c9f9 | fix(58-23): restore strict all-words title matcher (CR-01) |
| 3 Record | ac72ee9 | docs(58-23): CR-01 rollback ledger — RED, mutant r1, gate, re-opened limits |

## What changed

- `batch_card._match_title` returns the rows whose title holds every non-filler token of the reference, in row order. One row gives `one`, several give `many`, none gives `none`. Removed: the best-unique pick and `_TITLE_MIN_MATCH`. Kept: `_title_scores` and `_title_candidates`, so a `none` still lists the likely rows (best first) as follow-up buttons.
- In the Translate paragraph of `50-fix-loop.md` and `90-finalize.md`, the best-match sentence is replaced with the strict rule. Both files carry the same text: "every word the owner used for a row, filler aside, must be in that row's title … a partial match is not a match — ask, as when several rows match, with the likely rows as the buttons". `grep -ci "best-match\|best match\|most of the owner"` returns 0 for both files.
- Kept unchanged: WR-01, WR-03 (`CARDROWSFILE=`, `REASON_PRIOR_SUBSET`), IN-01, IN-03 and IN-05.

## Tests re-pointed (none deleted)

| Test | Was | Now |
|---|---|---|
| `TestFinalRound.test_reviewer_phrasings_resolve` | all 7 phrasings resolve to one row | only the 3 whose every word is in one title resolve ("the retry budget warning" gives 7, "the relay failover critical" gives 1, "Retry budget's reset" gives 7) |
| new `TestFinalRound.test_partial_phrasings_ask_with_likely_row_first` | (the other 4 phrasings were in the test above) | "the browse recovery one you flagged", "the Browse recovery issue from earlier", "the cursor bug in browse" and "Browse recovery (#5)" each give `none`, `ok: false`, no grammar, and #5 as the first candidate |
| `OVERLAP_CASES` / `check_adversarial_overlap` / `test_adversarial_overlap_margin` | asserted a score margin and `_TITLE_MIN_MATCH`; "the deadline relay" gave `many` | the margin column is dropped. Each case now checks that the status equals the number of rows whose title contains every word. "the deadline relay" gives `none` with candidates [1,3,4,6] |
| `TestFinalRoundLockTrips._mutant_match` | built on scores plus a minimum | built on the strict rule, with `on_tie` and a `partial_acts` switch |
| `test_m11_minimum_dropped` → `test_m11_partial_match_acts` | mutant: a unique score of 1 matches | mutant: a unique best partial row matches. "retries budget" then gives #7 and `check_weak_match` trips |
| `test_m10`, `test_m16` | tie-break mutants on the score helper | the same tie-break mutants on the strict helper. Both still trip |
| `test_fix_loop_card.py` / `test_finalize_card.py` `BEST_MATCH`, `TIE_ASKS` | pinned the best-match wording | `STRICT_MATCH`, `PARTIAL_ASKS` pin the strict wording. The `test_mutant_title_rule` subtests are renamed to "strict rule dropped" and "partial asks dropped" |

New: `TestCR01StrictTitle` has 5 tests: CR-01 phrasings ask, the meant row is listed and not picked, the full sentence records nothing, the verbatim iPlayarr sentence still resolves, and an in-test best-unique mutant trips.

## Verification (observed)

- **RED, at HEAD after 801c3bb:** `pytest -q scripts/test_answer_resolve.py -k CR01` gave `4 failed, 3 passed`. First failure at `:972`: `AssertionError: 'one' not found in ('none', 'many') : the option list on the browse page`.
- **GREEN:** `pytest -q scripts/test_answer_resolve.py` gave `88 passed`. Resolve plus the fix-loop and finalize card tests gave `298 passed`. The kept-fix selection (`-k "SubsetDispatchWalk or FinalRound or card_rows or PRIOR"`) gave `25 passed`.
- **Mutant r1 on the real file:** with the best-unique pick restored, `-k CR01` gave `4 failed`. After `git checkout`, `git status --porcelain plugins/` was empty.
- **Gate at 817c9f9:**
  - Full suite: `3588 passed, 4757 subtests passed` (0 failed).
  - `test_replay.py`: `64 passed`.
  - Replay candidate: exit 0, `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`, `kept 25 / protected 26`, `REGRESSED 0`, scorer sha256 `3504d2da…22fb` (unchanged).
  - Replay diff against rev:24c0c00: exit 0, 170 runs compared, 0 differing, 0 unallowed.
  - Golden: `9 passed`, `golden ok`.
  - score.py and batch_parse.py: diff against 24dccdc is empty.

## Deviations from Plan

None. The plan was executed as written. One addition: I put a mutant check (best-unique pick restored) inside `TestCR01StrictTitle` as well as the real-file mutant r1. The in-test mutant patches `_match_title`, so it passes whatever the real file holds. Mutant r1 on the real file is the evidence that the lock works.

## Known limits (re-opened, recorded in 58-REPRO.md)

- WR-02: wordier phrasings ask again, with the likely row listed first.
- The reviewer's safer design (offer the best partial row as a one-click choice, plus a broader function-word filler list) is not built.
- IN-01 (follow-up capped at 4 tied rows), IN-02 (close-out card pointer) and IN-03 (subset-refusal note wording) are carried as is.

D-21's hard stop holds: there will be no further review round.

## Self-Check: PASSED

- Files exist: batch_card.py, test_answer_resolve.py, both prose files, both card test files, 58-REPRO.md (contains `## CR-01 rollback` exactly once).
- Commits exist: 801c3bb, 817c9f9, ac72ee9.
