---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 20
subsystem: fix-loop card prose (50-fix-loop.md) + its prose locks
tags: [gap-closure, D-21, WR-01, WR-03, WR-02, IN-01, fence-walk, mutants]
requires: ["58-19 (REASON_PRIOR_SUBSET, best-unique title match)"]
provides:
  - "D-08 fallback keeps $SUGGESTFILE (removes refs/resolve only)"
  - "CARDROWSFILE= printed by the ordinary card fence only; the only stale-card source"
  - "TestSubsetDispatchWalk: real subset/ordinary/Step B fences in fresh shells"
affects: ["58-21 (Finalize side prints CARDROWSFILE= and names it as its stale source)"]
tech-stack:
  added: []
  patterns: ["second printed name for the same path (card vs. dispatch)", "byte-for-byte fence pin", "fresh-shell fence walk inside the test suite"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/scripts/test_fix_loop_card.py
decisions:
  - "The subset fence is not renamed: ROWSFILE= stays the one name every rows fence prints and Step B reads; the ordinary card fence also prints CARDROWSFILE= for the same path, and the stale re-map binds only from that"
  - "The D-08 full-card fallback keeps the suggestion file because the card shown next is the same card; only the Rerun and Close out remove it"
  - "The card's Bottom line line is tied to the suggest fence exiting 0 on this pass, not to a printed path"
metrics:
  duration: "~30 min"
  completed: 2026-10-27
  tasks: 3
  files: 2
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 20: Fix-loop final round (suggestion kept on fallback, CARDROWSFILE=, best-match rule, trimmed count) Summary

The fix loop's D-08 full-card fallback now removes only the refs and resolve files. It keeps `$SUGGESTFILE`, because the card shown next is the same card, so typing "bottom line" on it still works (WR-01). The ordinary card fence now also prints `CARDROWSFILE=` for its rows file. The Stale card, Close out and the Rerun name that print as the only prior-card source, and the prose says a path printed only after `ROWSFILE=` is never that source (WR-03(a)). The subset fence and the Step B payload fence are byte-identical to before. A new fresh-shell walk test shows that on both subset routes, Step B still sends exactly the rows the owner chose. Translate now states the helper's best-match title rule (WR-02). A trimmed suggestion ends with a note that gives the count only, never which rows (IN-01).

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | RED: re-pointed locks, final-round locks + mutants, subset-dispatch fence walk | ea6880f | scripts/test_fix_loop_card.py |
| 2 | Prose: D-08 keeps the suggestion, CARDROWSFILE=, best-match rule, trimmed note | 2b74d36 | phases/review/50-fix-loop.md, scripts/test_fix_loop_card.py (one earlier pin re-pointed) |
| 3 | Real-file mutants N1-N10 + by-hand walk of both subset routes | none (all killed, no needle added) | — |

## Reproduction (before any change)

WR-01, in a fresh `env -i bash -s` with TMPDIR set to the scratchpad: I created SUGGESTFILE, ANSWERFILE, REFSFILE and RESOLVEFILE with mktemp and wrote `{"q1": "fix 5", "q2": null}` to SUGGESTFILE. I then ran the D-08 line as it stood, `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"`, followed by the typed-"bottom line" copy `cp "$SUGGESTFILE" "$ANSWERFILE"`:

```
cp: …/scratchpad/wr01/vc.WdklVr: No such file or directory
cp exit=1
```

So the re-shown card offered a `Bottom line suggests:` line that could not be taken.

WR-03 shape on HEAD 8e40f4e: `grep -c "printf 'ROWSFILE=%s"` = **2** and `grep -c CARDROWSFILE` = **0**. Nothing told the card's print apart from the subset's.

## RED evidence (Task 1, prose at 8e40f4e)

`pytest -q scripts/test_fix_loop_card.py -k "FinalRound or GapRoundFixLoop or SubsetDispatchWalk or GapRoundTranslate"` → **27 failed, 24 passed** (subtests counted). The plan's verify gave `-k FinalRoundFixLoop` → 19 failed, 5 passed, and `-k SubsetDispatchWalk` → **4 passed**.

Problems reported on HEAD:
- `answer_files_problems`: "D-08 fallback: refs/resolve files not cleared before the full card", "D-08 fallback: does not keep the suggestion", "D-08 fallback: removes the suggestion the re-shown card still offers", "question note not tied to this pass's suggestion". The old `_cleared_before(…, "D-08 fallback")` clause had locked the defect in place; it is replaced by `d08_fallback_problems`.
- `trim_note_problems`: the Exit 0 sentence lacks `need your own words)` and `the count only, never which rows`.
- `stale_source_problems`: it lacks STALE_CARD_SOURCE and STALE_NEVER_SUBSET, still names "the previous pass's rows fence printed after `ROWSFILE=`", the Rerun lacks the new KEEP_ROWS and still keeps `$ROWSFILE`, and Close out lacks CLOSE_OUT_KEEPS and still names the `ROWSFILE=` print.
- `title_rule_problems`: it lacks BEST_MATCH and TIE_ASKS.
- `card_rows_name_problems`: the ordinary fence does not print CARDROWSFILE=, `printf 'CARDROWSFILE=%s` is printed 0 times, the subset bullet lacks both new sentences, and step 2 lacks both new clauses. The STEP_B_FENCE pin **matched HEAD**, so the pinned fence is the real one.

The walk passed on HEAD (4 tests): CHOSEN = {`a264e9e9…`}, and the D-10 and step-2 routes each sent exactly that one hash. The Step B-on-card mutant sent six hashes. So Step B's binding was already correct, and this plan keeps it that way.

## GREEN

After Task 2, `pytest -q scripts/test_fix_loop_card.py scripts/test_card_text.py scripts/test_pause_batching.py scripts/test_scope_args.py` → **231 passed, 610 subtests passed**, 0 failed. `TestSubsetDispatchWalk` → 4 passed on the fixed prose. On the step-2 route, shell 1 now prints `CARDROWSFILE=`, and the test asserts it equals `ROWSFILE=`.

Acceptance greps on `50-fix-loop.md`:

| grep | count | want |
|---|---|---|
| `printf 'ROWSFILE=%s` | 2 | 2 |
| `printf 'CARDROWSFILE=%s` | 1 | 1 |
| `SUBSETROWSFILE` | 0 | 0 |
| `payload --rows "$ROWSFILE" --answer "$ANSWERFILE"` | 1 | 1 |
| `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` | 2 (Close out, Rerun) | 2 |
| `rm -f "$REFSFILE" "$RESOLVEFILE"` | 1 (D-08) | 1 |
| `rm -f[^`]*ROWSFILE` | 0 | 0 |
| ``printed after `CARDROWSFILE=` `` (lines) | 2 | ≥ 2 |
| ``never a path printed only after `ROWSFILE=` `` | 1 | 1 |

Full suite (`pytest -q` from plugins/vibe-check): **3572 passed, 4743 subtests passed**, 0 failed. That is up from 3558, with 14 new tests: 10 in TestFinalRoundFixLoop and 4 in TestSubsetDispatchWalk. score.py, batch_parse.py and GOLDEN_DIGEST were not touched.

## Real-file mutants (Task 3)

A scratchpad Python driver (`mutants_5820.py`) applied each mutant to the real `50-fix-loop.md` and ran `pytest -q scripts/test_fix_loop_card.py`. It then ran `git checkout --` on the file and asserted `git status --porcelain` was empty, after every mutant. The file is clean at the end.

| ID | Mutant on the real file | Result | Failing tests (prose locks / walk) |
|----|------|--------|------|
| N1 | D-08 back to `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` | 4 failed | FinalRound + GapRound `test_answer_files_holds`, `test_mutant_answer_files` |
| N2 | drop "keep `$SUGGESTFILE`: … (the Rerun, Close out)" | 3 failed | FinalRound + GapRound `test_answer_files_holds`, FinalRound `test_mutant_answer_files` |
| N3 | question condition back to "printed a `SUGGESTFILE=` path created on this pass" | 6 failed | both `test_answer_files_holds`/`test_mutant_answer_files`, `test_suggest_fence_holds`, `test_bottom_line_holds` |
| N4 | ordinary fence loses `printf 'CARDROWSFILE=%s\n' "$ROWSFILE"` | 2 failed | `test_card_rows_name_holds`, `test_mutant_card_rows_name` |
| N5 | subset fence gains a `CARDROWSFILE=` print | 6 failed | `test_card_rows_name_holds`, `test_mutant_card_rows_name` / all 4 walk tests (subset shell must print no CARDROWSFILE=) |
| N6 | subset print renamed `SUBSETROWSFILE=` (rejected option (a)) | 6 failed | `test_card_rows_name_holds`, `test_printed_paths_holds` / all 4 walk tests incl. `test_d10_route_dispatches_only_the_subset` (no `ROWSFILE=` printed) |
| N7 | Step B `payload --rows "$CARDROWSFILE"` | 7 failed | `test_card_rows_name_holds` (PAYLOAD_CALL count + STEP_B_FENCE pin), `test_mutant_card_rows_name`, `test_helper_calls` / all 4 walk tests (substitution assertion: fence does not read `"$ROWSFILE"`) |
| N8 | stale source back to "the previous pass's rows fence printed after `ROWSFILE=`", never-clause gone | 4 failed | FinalRound + GapRound `test_stale_source_holds`, `test_mutant_stale_source` |
| N9 | trimmed-count note deleted | 2 failed | `test_trim_note_holds`, `test_mutant_trim_note` |
| N10 | best-match rule ("and picks the single row … still asks, with the likely rows as the buttons") deleted | 3 failed | FinalRound + GapRoundTranslate `test_title_rule_holds`, FinalRound `test_mutant_title_rule` |

Every mutant was killed. N6 and N7 were each killed by at least one walk test as well as a prose lock. No needle was added, so Task 3 has no commit.

## Fence walk (by hand, fresh shells, fixed prose)

The driver (`walk_5820.py`) pulled the subset, ordinary and Step B fences out of the real file. It ran each one in its own `bash -s` with only PATH, VC_ROOT, TMPDIR and STATE_FILE set; STATE_FILE was the six-row `iplayarr45-six-row-state.json`. The subset file was `["a264e9e9…"]`, and `{"all": true}` was written to the printed ANSWERFILE, standing in for the Write tool.

| Route | Shell | Printed | Observed |
|---|---|---|---|
| D-10 | subset fence | ANSWERFILE, ROWSFILE (no CARDROWSFILE) | rows doc `subset: true`, 1 row |
| D-10 | Step B on subset `ROWSFILE=` | PAYLOADFILE | `sent` = [a264e9e9], 1 finding |
| step 2 | ordinary fence | ANSWERFILE, CARDROWSFILE, ROWSFILE (CARDROWSFILE == ROWSFILE) | 6 rows, no `subset` key |
| step 2 | subset fence | ANSWERFILE, ROWSFILE (no CARDROWSFILE) | `subset: true`, 1 row |
| step 2 | Step B on subset `ROWSFILE=` | PAYLOADFILE | `sent` = [a264e9e9], 1 finding |
| mutant | Step B on the `CARDROWSFILE=` path | PAYLOADFILE | `sent` = [0249b52c, 2a01829c, 22d360d9, 3dd41363, a264e9e9, 7bc336e7]: **6 hashes**, 6 findings |

The last row shows what goes wrong if Step B is bound to the card's rows instead of the subset's: `{"all": true}` on the card doc sends every row, including the five the owner did not choose.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Subset-bullet sentences placed after the (D-06) sentence, not before "Write `{"all": true}`"**
- **Found during:** Task 2
- **Issue:** The earlier pin `SUBSET_NO_CARD` expects "…do not print it again. Write `{"all": true}` … (D-06)." as one unbroken run. Putting the new sentences in the middle broke `test_subset_no_card`, `test_mutant_subset_asks_again` and `test_mutant_single_echo`.
- **Fix:** The two new sentences now follow "(D-06)." in the same subset-bullet tail. `card_rows_name_problems` checks the tail after the fence, so it is satisfied either way.
- **Cost if wrong:** Nothing. The wording is the same and only its position in the bullet moved.
- **Files modified:** phases/review/50-fix-loop.md
- **Commit:** 2b74d36

**2. [Rule 1 - Bug] Earlier pin `BOTTOM_LINE_QUESTION_NOTE` re-pointed to the exit-0 condition**
- **Found during:** Task 2
- **Issue:** `BOTTOM_LINE_QUESTION_NOTE` (in `bottom_line_problems`) pinned the old "printed a `SUGGESTFILE=` path created on this pass" wording, which the plan replaces. It failed `test_bottom_line_holds` and `test_suggest_fence_holds`.
- **Fix:** The pin now reads "…appears ONLY when the `suggest` fence below exited 0 on this pass". N3 shows it still trips when the old wording comes back.
- **Cost if wrong:** Low. It is a test constant that follows the planned prose change.
- **Files modified:** scripts/test_fix_loop_card.py
- **Commit:** 2b74d36

**3. [Rule 3] `card_rows_name_problems` takes the full file text, not the card section**
- **Found during:** Task 1
- **Issue:** The Step B fence and `PAYLOAD_CALL` sit in the Step B section, outside `card_section`. A card-only argument could never see the fence it is meant to pin.
- **Fix:** The function takes `text` and slices the card section itself.
- **Cost if wrong:** None. The checks are the same as specified.

**4. Extra checks beyond the plan's list:** `stale_source_problems` also forbids the old Close out wording (`CLOSE_OUT_KEEPS_OLD`) and the old Rerun wording (`KEEP_ROWS_OLD`). The GapRound stale mutants gained a "subset print bound" case. Each was RED on HEAD and is killed by N8 or its own mutant.

## Known Stubs

None.

## Threat Flags

None. No new network, auth or file-access surface; the change is prose plus tests.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/50-fix-loop.md (CARDROWSFILE print = 1)
- FOUND: plugins/vibe-check/scripts/test_fix_loop_card.py (`class TestSubsetDispatchWalk`, `class TestFinalRoundFixLoop`)
- FOUND: ea6880f, 2b74d36 in `git log`
- STATE.md / ROADMAP.md / HANDOFF.json untouched by this plan
