---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 21
subsystem: Finalize card prose (90-finalize.md) + its prose locks
tags: [gap-closure, D-21, WR-01, WR-03, WR-02, IN-01, mutants]
requires: ["58-19 (REASON_PRIOR_SUBSET, best-unique title match)", "58-20 (fix-loop side: CARDROWSFILE= on the ordinary card fence)"]
provides:
  - "Finalize D-08 fallback keeps $SUGGESTFILE (removes refs/resolve only)"
  - "Finalize rows fence prints CARDROWSFILE= for the same path; Stale card binds only the fix-loop card's printed CARDROWSFILE="
  - "TestFinalRoundFinalize locks + mutants"
affects: ["Phase 58 verification (final gap round D-21 closed on both card files)"]
tech-stack:
  added: []
  patterns: ["second printed name for the same path (card vs. dispatch)", "pinned helper-call counts on --rows \"$ROWSFILE\""]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "Finalize mirrors 58-20 word for word: no fence renamed, its rows fence additionally prints CARDROWSFILE=, and $CARDROWSFILE is never consumed by any fence"
  - "Finalize's Stale card names the fix-loop card's printed CARDROWSFILE= as its only source and forbids both a 'last printed' rule and a ROWSFILE=-only source (checked on the Stale paragraph only, since the ordinary 'substitute the printed ROWSFILE=' sentence is legitimate)"
metrics:
  duration: "~20 min"
  completed: 2026-10-27
  tasks: 3
  files: 2
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 21: Finalize final round (suggestion kept on fallback, CARDROWSFILE=, best-match rule, trimmed count) Summary

This plan does for the Finalize card what 58-20 did for the fix-loop card. Before, Finalize's D-08 full-card fallback deleted the suggestion file. It now removes only the refs and resolve files and keeps `$SUGGESTFILE`, so typing "bottom line" on the re-shown card still works (WR-01). Q1's `Bottom line suggests:` line is now tied to the `suggest` fence exiting 0. Finalize's rows fence now also prints `CARDROWSFILE=` for the same path. The Stale card binds `$PRIORROWSFILE` only to the fix-loop card's printed `CARDROWSFILE=` and says a path printed only after `ROWSFILE=` is never that source (WR-03(a)). Every helper call still reads `--rows "$ROWSFILE"`. Translate now states the best-match title rule (WR-02), and a trimmed suggestion ends with a note that gives the count only (IN-01).

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | RED: re-pointed locks, final-round locks + mutants | 3074258 | scripts/test_finalize_card.py |
| 2 | Prose: D-08 keeps the suggestion, CARDROWSFILE=, best-match rule, trimmed note | 925b7c6 | phases/shared/90-finalize.md |
| 3 | Real-file mutants F6-F14 | none (all killed, no needle added) | — |

## Reproduction (before any change)

WR-01, in a fresh `env -i bash -s` with TMPDIR set to the scratchpad: I created SUGGESTFILE, ANSWERFILE, REFSFILE and RESOLVEFILE with mktemp and wrote `{"q1": "fix 1,2", "q2": null}` to SUGGESTFILE. I then ran Finalize's D-08 line as it stood at 326d35f (`rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"`), followed by the Parse step's copy for a typed "bottom line", `cp "$SUGGESTFILE" "$ANSWERFILE"`:

```
cp: …/scratchpad/wr01f/vc.XuMevB: No such file or directory
cp exit=1
```

WR-03 shape at 326d35f: `grep -c "printf 'ROWSFILE=%s"` = 1 and `grep -c CARDROWSFILE` = 0. The Stale card's source was "that card's rows fence printed after `ROWSFILE=`". After a D-17 "fix X, then close out" pass, the last such print is the subset fence's.

## RED evidence (Task 1, prose at 326d35f)

`pytest -q scripts/test_finalize_card.py -k "FinalRound or GapRoundFinalize"` → **18 failed, 15 passed**. The plan's verify `-k FinalRoundFinalize` → **14 failed, 4 passed**.

Problem strings on HEAD:
- `check_answer_files`: "D-08 fallback: refs/resolve files not cleared before the full card", "D-08 fallback: keep sentence missing", "D-08 fallback still removes the suggestion file", "Q1 suggestion line not tied to the suggest exit", "Q1 suggestion line still keyed to a printed path". The old `_clear_before(para[d08:], …, "D-08 fallback")` clause had locked the defect in place. `d08_fallback_problems` replaces it.
- `check_stale`: it lacks "printed after `CARDROWSFILE=`", "never a path printed only after `ROWSFILE=`" and "the ordinary fence that rendered the card the owner read", and reports "stale source binds 'rows fence printed after `ROWSFILE=`'".
- `check_card_rows_print`: "rows fence prints no CARDROWSFILE= after ROWSFILE=" and "printf 'CARDROWSFILE=%s printed 0 times". The `--rows "$ROWSFILE"` pins (suggest 1, parse 1, resolve 1, twin 1, total 4) **matched HEAD**.
- `check_trim_note`: it lacks `need your own words)` and `the count only, never which rows`.
- `check_title_rule`: it lacks BEST_MATCH and TIE_ASKS.

## GREEN

After Task 2, `pytest -q scripts/test_finalize_card.py scripts/test_card_text.py scripts/test_pause_batching.py scripts/test_finalize_archive_prose.py` → **135 passed, 262 subtests passed**, 0 failed. `test_fix_loop_card.py` and `test_batch_card.py` → 240 passed.

Acceptance greps on `90-finalize.md`:

| grep | count | want |
|---|---|---|
| `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` | 2 (steps 2, 3) | 2 |
| `rm -f "$REFSFILE" "$RESOLVEFILE"` | 1 (D-08) | 1 |
| ``printed after `CARDROWSFILE=` `` | 1 | 1 |
| ``never a path printed only after `ROWSFILE=` `` | 1 | 1 |
| `rm -f[^`]*ROWSFILE` | 0 | 0 |
| `SUBSETROWSFILE` | 0 | 0 |
| ``the last `ROWSFILE=` line`` | 0 | 0 |
| `printf 'ROWSFILE=%s` | 1 | 1 |
| `printf 'CARDROWSFILE=%s` | 1 | 1 |
| `$CARDROWSFILE` | 0 | 0 |

Full suite (`pytest -q` from plugins/vibe-check): **3582 passed, 4755 subtests passed**, 0 failed. That is up from 3572, with 10 new tests in TestFinalRoundFinalize. score.py, batch_parse.py and GOLDEN_DIGEST were not touched.

## Real-file mutants (Task 3)

A scratchpad Python driver (`mutants_5821.py`, explicit paths) applied each mutant to the real `90-finalize.md` and ran `pytest -q scripts/test_finalize_card.py`. It then ran `git checkout --` on the file and asserted `git status --porcelain` was empty, after every mutant. The file is clean at the end.

| ID | Mutant on the real file | Result | Failing tests |
|----|------|--------|------|
| F6 | D-08 back to `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` | 3 failed | FinalRound + GapRound `test_answer_files_holds`, FinalRound `test_mutant_answer_files` |
| F7 | "keep `$SUGGESTFILE`: …" clause deleted | 3 failed | FinalRound + GapRound `test_answer_files_holds`, FinalRound `test_mutant_answer_files` |
| F8 | Q1 condition back to "printed a `SUGGESTFILE=` path created for this card" | 3 failed | FinalRound + GapRound `test_answer_files_holds`, FinalRound `test_mutant_answer_files` |
| F9 | "never a path printed only after `ROWSFILE=` (…)" deleted | 4 failed | FinalRound + GapRound `test_stale_source_holds`, Phase58Routing `test_stale_holds`, FinalRound `test_mutant_stale_source` |
| F10 | stale source → "the last `ROWSFILE=` line printed in this session" | 6 failed | FinalRound/GapRound `test_stale_source_holds` + `test_mutant_stale_source`, Phase58Routing `test_stale_holds` |
| F11 | trimmed-count note deleted | 3 failed | FinalRound `test_trim_note_holds`, `test_mutant_trim_note` |
| F12 | best-match rule ("and picks the single row … the buttons") deleted | 4 failed | FinalRound + GapRoundTranslate `test_title_rule_holds`, FinalRound `test_mutant_title_rule` |
| F13 | rows fence loses `printf 'CARDROWSFILE=%s\n' "$ROWSFILE"` | 2 failed | FinalRound `test_card_rows_print_holds`, `test_mutant_card_rows_print` |
| F14 | stale source back to "the literal path that card's rows fence printed after `ROWSFILE=`" | 6 failed | FinalRound/GapRound `test_stale_source_holds` + `test_mutant_stale_source`, Phase58Routing `test_stale_holds` |

Every mutant was killed. No needle was added, so Task 3 has no commit. The in-test mutant "twin reads `$CARDROWSFILE`" (`resolve --rows "$CARDROWSFILE" … --prior-rows`) trips `check_card_rows_print` through both the `$CARDROWSFILE is consumed` check and the twin-call pin.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] GapRound stale mutant re-pointed to the new source wording**
- **Found during:** Task 1
- **Issue:** `TestGapRoundFinalize.test_mutant_stale_source` ("'used as is' source restored") anchored on "printed after `ROWSFILE=`". That phrase is gone from the fixed prose, which says "printed only after `ROWSFILE=`", so the anchor would fail `assertIn`.
- **Fix:** The test now anchors on `STALE_CARD_SOURCE`. It was RED on HEAD and passes on the fixed prose. F10 and F14 still kill it.
- **Cost if wrong:** Low. It is a test anchor that follows the planned prose change.
- **Files modified:** scripts/test_finalize_card.py
- **Commit:** 3074258

**2. Extra checks beyond the plan's list:** `check_answer_files` also forbids the old Q1 wording (`Q1_SUGGEST_OLD`), and `check_card_rows_print` also runs `check_printed_paths` in its holds test. Both were RED or neutral on HEAD as expected and are killed by F8 and F13.

**3. Not applicable:** the plan's pin list included `select-questions`. Finalize has no `select-questions` call (count 0 at HEAD), so the pins cover suggest, parse, resolve, the twin and the total of 4.

## Known Stubs

None.

## Threat Flags

None. No new network, auth or file-access surface; the change is prose plus tests. T-58-21-01 is mitigated: the Stale card binds only from `CARDROWSFILE=`, and F9, F10 and F14 are killed. T-58-21-04 is mitigated: the `--rows "$ROWSFILE"` counts are pinned and `$CARDROWSFILE` is never consumed. T-58-21-02 is mitigated by F6 and F7. T-58-21-03 is mitigated: the note gives the count only.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md (CARDROWSFILE print = 1)
- FOUND: plugins/vibe-check/scripts/test_finalize_card.py (`class TestFinalRoundFinalize`)
- FOUND: 3074258, 925b7c6 in `git log`
- STATE.md / ROADMAP.md / HANDOFF.json untouched by this plan
