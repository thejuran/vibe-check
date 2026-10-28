---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 09
subsystem: decision-cards / finalize prose
tags: [finalize, follow-up, stale-card, card-budget, bug-C, ANSR-02, ANSR-03]
requires:
  - "58-03 (batch_card.py resolve contract, --prior-rows)"
  - "58-05 (Finalize Translate paragraph pointing at **Ask only what is missing (D-05, D-06)**)"
  - "58-08 (fix-loop Stale card and Ask only what is missing paragraphs — mirrored)"
provides:
  - "90-finalize.md **Stale card (D-07).** paragraph with the --prior-rows twin resolve fence"
  - "90-finalize.md **Ask only what is missing (D-05, D-06).** paragraph (Finalize form: Q2 is the second reason source) incl. the D-08 full-card fallback"
  - "90-finalize.md Card budget naming the follow-up and the fallback; the open-ended unparseable re-ask removed"
  - "test_finalize_card.py: check_followup / check_stale / check_budget + TestPhase58FinalizeRouting"
  - "Bug-C static trace (D-15 evidence for 58-06)"
affects: [58-06]
tech-stack:
  added: []
  patterns: ["problem-list prose lock + in-memory mutant", "real-file mutant driver in scratchpad"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "On Finalize the Reason follow-up is asked only when both the owner's inline why and the Q2 pick are absent; a Q2 pick is never asked for again"
  - "Finalize's stale case covers both a re-run review pass and an earlier `--finalize` card; $PRIORROWSFILE is that card's own $ROWSFILE path, used as is (same call as 58-08)"
  - "check_translate_path now counts only the plain resolve fence (no --prior-rows), so the stale twin belongs to check_stale and the plan's grep count of 2 holds"
metrics:
  duration: ~25 min
  completed: 2026-10-27
  tasks: 3
  files: 2
  suite: "3465 passed / 0 failed (was 3459; +6 tests)"
requirements: [ANSR-02, ANSR-03]
---

# Phase 58 Plan 09: Finalize asks only the gap, once; stale cards re-mapped; budget reconciled Summary

Finalize now handles a plain-English answer that it can only partly read the same way the fix loop does. It holds the whole answer, records nothing, and asks one short question about only the unclear piece. It asks for a reason only when neither the owner's text nor the Q2 pick supplied one. If the reply is still unclear, it shows the full card once with a note saying what could not be matched, then stops asking. Answers to an older card (from before a rerun, or from an earlier `--finalize`) are re-mapped by finding identity through the `--prior-rows` twin fence, and the echo shows the new numbers. The Card budget line now names both extra cards. The old "or an unparseable answer adds another" is gone. The dangling reference that 58-05 left is now resolved.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | 79d402a | test(58-09): add failing Finalize locks for the missing-piece follow-up (Q2-aware), the D-08 fallback, the stale --prior-rows re-map and the reconciled card budget |
| 2 | 75bb831 | fix(58-09): Finalize asks only the missing piece once (Q2-aware), falls back once, re-maps stale cards; budget reconciled (D-05..D-08) |
| 3 | — | No pin needed changing, so there is no commit (the plan makes this one conditional) |

## RED (Task 1, observed)

- `pytest -q scripts/test_finalize_card.py -k "Phase58FinalizeRouting"` gave `10 failed, 3 passed`.
  - All three `_holds` failed: followup, stale and budget.
  - All 7 mutant subtests failed, because the needles they mutate were not in the file yet.
  - The 3 "passed" are the parent mutant methods. Their failures show up as SUBFAILED.
- `-k "not Phase58FinalizeRouting"` gave `40 passed, 79 subtests passed`, so everything from 58-05 still passed.

## What changed in 90-finalize.md

- The `ok` false bullet of **Translate the answer** now points to **Ask only what is missing (D-05, D-06)** "below" instead of "(the next paragraph)". The Stale card paragraph now sits between the two.
- **Stale card (D-07)** mirrors 58-08, with two Finalize differences:
  - The stale case is "a review pass re-ran, or an earlier `--finalize` built a card the owner is still answering".
  - `$PRIORROWSFILE` is bound to that card's `$ROWSFILE` path as is. The twin fence is the same `if … else … fi` form with only `"$…FILE"` paths. When `stale` is true, ` (your numbers re-mapped to the current card)` is appended to `Read your answer as:`.
- **Ask only what is missing (D-05, D-06)** mirrors 58-08, with these Finalize differences:
  - "recorded, or sent to the fix-loop card".
  - The Reason bullet adds: "On Finalize the reason has two sources — the owner's inline why and the Q2 pick — so this question is asked only when both are absent: a Q2 pick is already the reason and is never asked for again."
  - The `ok` true path is "the grammar copy, the SAME parse fence, `Read your answer as:`", then continue at **After the answer** with the whole answer together; the gate re-runs there.
  - D-08: "show the full card once, its Q1 question led by a note built from the resolve output that says what could not be matched … then stop asking".
- **Card budget:** "Finalize costs one card. Only `look N`, a bare Mixed…, a plain-English answer that needs one detail (at most one follow-up card per gap, D-06) or a second unclear reply (which shows the full card once, D-08) adds another, each at the owner's request. A bare Mixed… buys exactly one clarification. Nothing else in this file asks a question."
- Unchanged and still locked: "never re-show the card after recording", "there is NO confirm card", the bare-Mixed… `need_text` "re-show the same card ONCE" bullet, and `close_out` always false. The `--close-out-after-rerun` marker is never written on Finalize (grep count 0).

## Verification (observed)

- **Task 2 verify:** `pytest -q scripts/test_finalize_card.py scripts/test_card_text.py scripts/test_pause_batching.py` gave `94 passed, 232 subtests passed`.
- **Grep gates on 90-finalize.md:**

  | Pattern | Count | Required |
  |---|---|---|
  | `resolve --rows "$ROWSFILE" --answer "$REFSFILE"` | 2 | 2 |
  | `record nothing` | 1 | ≥ 1 |
  | `or an unparseable answer adds another` | 0 | 0 |
  | `re-show the same card ONCE` | 1 | 1 |
  | `close-out-after-rerun` | 0 | 0 (Finalize never writes the marker) |

- **`pytest scripts/test_finalize_card.py -k mutant -v`:**
  ```
  TestPhase58Finalize::test_mutant_bottom_line PASSED
  TestPhase58Finalize::test_mutant_echo_visible PASSED
  TestPhase58Finalize::test_mutant_nv_stop_reconciled PASSED
  TestPhase58Finalize::test_mutant_option_descriptions PASSED
  TestPhase58Finalize::test_mutant_q1_header PASSED
  TestPhase58Finalize::test_mutant_translate_path PASSED
  TestPhase58FinalizeRouting::test_mutant_budget PASSED
  TestPhase58FinalizeRouting::test_mutant_followup PASSED
  TestPhase58FinalizeRouting::test_mutant_stale PASSED
  9 passed, 37 deselected, 20 subtests passed
  ```
- **Task 3 neighbour set:** `test_finalize_card`, `test_fix_loop_card`, `test_card_text`, `test_pause_batching`, `test_finalize_archive_prose`, `test_carry_writers`, `test_fixcommit`, `test_tracecheck` and `test_scope_args` gave `385 passed, 1156 subtests passed`. No pin in any of these files needed an edit.
- **Bug-C lock:** `pytest -q scripts/test_fix_loop_card.py -k subset -v` gave `7 passed`. That includes `test_subset_no_card`, `test_mutant_subset_a_no_ask_clause_deleted`, `test_mutant_subset_b_asks_apply_skip` and `test_mutant_subset_off_bullet_instruction`.
- **Frozen files:** `git diff --name-only 24dccdc..HEAD -- plugins/vibe-check/scripts/batch_parse.py plugins/vibe-check/scripts/score.py` is empty.
- **Full suite:** bare `pytest -q` from plugins/vibe-check gave `3465 passed, 4608 subtests passed in 162.37s`, 0 failed. That is 3459 plus the 6 new TestPhase58FinalizeRouting tests.

## Mutant table (owner rule: applied to the REAL file, observed, reverted)

The driver is `scratchpad/mutants_5809.py`. For each mutant it rewrites `plugins/vibe-check/phases/shared/90-finalize.md`, runs `pytest -q scripts/test_finalize_card.py -k <test>`, and then restores the original bytes in a `finally`. It printed `restored: True` (sha256 match), and `git status` showed the file unchanged afterwards.

| # | Mutant on 90-finalize.md | Test | Observed |
|---|---|---|---|
| M1 | follow-up without "record nothing" (deleted) | followup_holds | 1 failed |
| M2 | stale fence without ` --prior-rows "$PRIORROWSFILE"` | stale_holds | 1 failed |
| M3 | budget clause back to "or an unparseable answer adds another" | budget_holds | 1 failed |
| M4 | "asked only when both are absent" deleted (Q2-aware reason) | followup_holds | 1 failed |
| M5 | D-08 "show the full card once" replaced by "re-ask" | followup_holds | 1 failed |
| M6 | "so the echo shows the new numbers" deleted | stale_holds | 1 failed |

The same mutants also exist as in-memory subtests in `TestPhase58FinalizeRouting.test_mutant_*`: followup ×3, stale ×2 and budget ×2 (old clause restored, D-08 dropped).

## Bug-C static trace (D-15 evidence for 58-06; final working tree at 75bb831)

The owner answers the Finalize card with the typed grammar `fix N; defer M -- <reason>`:

1. `90-finalize.md:118` — the Mixed… option tells the owner to type the mix in Other (`fix 2,5; defer 3; dismiss rest`). The answer comes back as Q1 text plus a Q2 pick.
2. `90-finalize.md:153` — **Parse.** writes the FULL Q1 string and Q2, verbatim, to `$ANSWERFILE` with the Write tool. Owner text never goes on a command line.
3. `90-finalize.md:157` — the parse fence runs `batch_card.py parse --rows "$ROWSFILE" --answer "$ANSWERFILE" > "$PARSEFILE"`. The grammar is valid, so it exits 0 and there is no Translate or follow-up detour.
4. `90-finalize.md:210`/`:214` — **After the answer**, `otherwise` bullet. `echo_text` must be visible on screen. When step 2 routes to the fix-loop card, that card is not shown, so `echo_text` is printed as message text before `50-fix-loop.md` is read. There is NO confirm card.
5. `90-finalize.md:215`/`:218` — step 1: `payload` is non-null and holds the `defer M` decision. It is copied file-to-file into `$DECFILE`, and then `90-finalize.md:251` runs `carry_state.py record-decisions --decisions-file "$DECFILE"`, which records the defer.
6. `90-finalize.md:225`/`:228`/`:229` — step 2: `fix` is non-empty. `fix_targets` is copied file-to-file into `$SUBSETFILE`, and `SUBSETFILE=<path>` is printed.
7. `90-finalize.md:235` — the agent Reads `50-fix-loop.md` and enters "The fix-loop card" with the literal subset path. REVIEW.md is not written and nothing is archived.
8. `50-fix-loop.md:18` — **Finalize routed a fix set here (D-10)**. The subset fence (`:20-28`) runs `batch_card.py rows --mode fix-loop --subset "<subset path>"`. If the path is missing, the step refuses rather than falling back to every open row.
9. `50-fix-loop.md:31` — "print Finalize's `echo_text` as message text, write `{"all": true}` to `$ANSWERFILE` with the Write tool, and go straight to **Step B** — ask NO AskUserQuestion".
10. `50-fix-loop.md:217` — **Step B — Apply fixes** runs on the owner's chosen rows. **Step B — no AskUserQuestion** is asked anywhere between the Finalize answer and the fix.

Lock evidence: `test_fix_loop_card.py:408` `subset_no_card_problems` (strengthened by 58-04) trips on bug-C mutants A, B and C:
- A deletes the no-ask clause.
- B asks Apply/Skip.
- C is the off-bullet "show the card below" instruction. It is the one the pre-58-04 lock missed.

The 58-04 SUMMARY records each of these against the real file, and the three tests pass on this tree.

Not verified: a live interactive run with a model. D-15 puts paid runs out of scope without an approved proposal. This trace is static, and it covers only the prose and the locks.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Lock conflict] `check_translate_path` required exactly one resolve fence**
- **Found during:** Task 1
- **Issue:** 58-05's lock counted fences containing `resolve --rows "$ROWSFILE" --answer "$REFSFILE"` and required exactly 1. The planned `--prior-rows` twin also contains that string, which would make the count 2 and contradict the plan's grep gate of 2.
- **Fix:** The lock now counts only fences without `--prior-rows`, and `check_stale` owns the twin. 58-05's "resolve fence removed" mutant still trips, because the replacement removes both occurrences.
- **Cost if wrong:** low. If the plain fence were deleted while the twin stayed, the plain count would drop to 0 and the lock would still trip.
- **Files modified:** test_finalize_card.py
- **Commit:** 79d402a

**2. [Rule 1 - Wording] "(the next paragraph)" → "below"**
- **Found during:** Task 2
- **Issue:** The Stale card paragraph now sits between Translate and Ask only what is missing, so "the next paragraph" would point at the wrong paragraph.
- **Fix:** Changed it to "below", matching the fix-loop twin. No lock pinned the old words.
- **Cost if wrong:** none.
- **Commit:** 75bb831

**3. [Plan line drift] The fix-loop subset instruction is at `:31`, not `:29`**
- The plan cited `50-fix-loop.md:29`. On the final tree the same text is at `:31`, and the trace cites the real line numbers.

## Known Stubs

None. The dangling "Ask only what is missing (D-05, D-06)" reference and the old budget line, both left by 58-05, are now resolved. 58-05 also deferred the stale note on the echo line, and that is added.

## Threat Flags

None beyond the register.
- **T-58-16:** one follow-up per gap, the full card once, then stop. Locked by M1, M4, M5 and the budget lock (M3).
- **T-58-20:** the follow-up continues at **After the answer**, so the gate re-runs.
- **T-58-27:** the `--prior-rows` twin, and the echo shows the new numbers. Locked by M2 and M6.

The new fence takes only `"$…FILE"` paths. The follow-up note shows only the verb, the ref position and the match count, never owner text.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md (`**Ask only what is missing (D-05, D-06).**`, `--prior-rows "$PRIORROWSFILE"`)
- FOUND: plugins/vibe-check/scripts/test_finalize_card.py (`def check_followup` ×1)
- FOUND commits: 79d402a, 75bb831
- STATE.md / ROADMAP.md / HANDOFF.json untouched
