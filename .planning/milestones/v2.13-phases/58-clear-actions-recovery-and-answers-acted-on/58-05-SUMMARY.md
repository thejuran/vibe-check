---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 05
subsystem: decision-cards / finalize prose
tags: [finalize, plain-english-answers, needs-verification, bottom-line, ANSR-01, RECV-01, RECV-02]
requires:
  - "58-01 (rows doc bulk_fix_text, finalize form)"
  - "58-03 (batch_card.py resolve contract)"
  - "58-04 (fix-loop **Translate the answer (D-01).** twin, Bottom line paragraph)"
  - "58-08 (typed \"bottom line\" handling, Ask only what is missing paragraph name)"
provides:
  - "90-finalize.md Q1 header counting Needs-verification rows ({{V}})"
  - "Option 3 Fix all = {{bulk_fix_text}} verbatim; Dismiss/Defer all and Mixed… descriptions true to batch_parse"
  - "90-finalize.md **Translate the answer (D-01).** ok branch: refs -> resolve -> grammar copy -> same parse -> `Read your answer as:` -> After the answer"
  - "90-finalize.md **Bottom line as a choice (D-09).** session-conditional slot + parse dry run"
  - "NV stop text reconciled with Phase 56 D-07; echo sentence no longer refers to a 'From your finalize answer:' block"
affects: [58-09 (writes **Ask only what is missing (D-05, D-06)**, the stale --prior-rows twin, and the Card budget line in 90-finalize.md)]
tech-stack:
  added: []
  patterns: ["problem-list prose lock + in-memory mutant", "real-file mutant driver in scratchpad"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "The bulk_fix_text explanation sentence names the field without the {{bulk_fix_text}} slot, so the slot appears exactly once (same call 58-04 made for the fix loop)"
  - "Finalize's refs `reason` = owner's inline why, else the Q2 pick verbatim, else null; resolve appends it to the grammar, so the copied answer file keeps q2 null like the fix-loop twin"
  - "`close_out` is always false on Finalize; the --close-out-after-rerun marker is never written there (grep gate 0)"
  - "The Translate paragraph sits between the parse fence and **After the answer**, and the lock enforces that order"
metrics:
  duration: ~15 min (20:16Z start)
  completed: 2026-10-27
---

# Phase 58 Plan 05: Finalize card tells the truth and acts on plain English — Summary

The Finalize card's header now counts Needs-verification rows, its Fix all description is the helper's `bulk_fix_text` (which names the NV rows it leaves out), Dismiss/Defer all and Mixed… say exactly what the parser does, and a Mixed…/Other answer the grammar refuses is translated through `batch_card.py resolve` and the same parse gate, echoed as `Read your answer as:` and acted on with no confirm card, the twin of the fix loop.

## Tasks

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | 776e56c | test(58-05): add failing Finalize locks for parser-true option descriptions, the NV header count, the translated Mixed…/Other path, the reconciled NV stop text and the Bottom line slot |
| 2 | e414508 | fix(58-05): Finalize card descriptions match the parser (Fix all names excluded NV rows); NV stop text and echo sentence reconciled (D-10, D-14, I-1..I-5, I-11) |
| 3 | 2859d4f | fix(58-05): Finalize Mixed…/Other answers are translated through the strict parser and acted on with an echo (D-01..D-04, D-16) |

## What changed in 90-finalize.md

- **:53 NV stop text (I-5).** "the next review run re-checks it once …" is now "it is re-checked automatically on every later run that reviews changes while the repaired code is unchanged, and closes when an independent lane verifies the repaired code; until then it stays open for your decision (Phase 56 D-07)". "awaiting an independent re-check" (pinned by test_confirmed_fix) is kept.
- **Q1 header (I-4).** `({{C}} critical/warning, {{V}} needs-verification, {{M}} medium{{; P …}})`, with "`C` / `V` / `M` = rows by band; C + V + M = N (`V` = rows whose band is `needs-verification`)". The Bottom line slot `{{\n\nBottom line suggests: <grammar> — type "bottom line" in Other to take it}}` follows `{{card_text}}`.
- **Options (I-1..I-3).** Labels unchanged (`FINALIZE_Q1`). Dismiss all: "Critical, warning and Needs-verification rows stay open unless you name them by number in Mixed…". Defer all: "same rule for critical, warning and Needs-verification rows". Fix all: `"{{bulk_fix_text}}"`. Mixed…: adds "or plain English naming the rows", and "`fix all` covers critical, warning and medium rows; `dismiss all` / `defer all` cover medium rows only; a Needs-verification row is never reached by `all` or `rest` — name it by number". "lowest band" is gone.
- **After Q2:** "Option 3's description is copied from the rows doc: it is the `bulk_fix_text` field of `$ROWSFILE`, verbatim — the helper names the Needs-verification rows Fix all leaves out by number (D-10, D-12); this file never computes that set."
- **Bottom line as a choice (D-09).** Offered only when THIS session rendered the last pass's Bottom line. A separate `--finalize` invocation renders no report, so the line is omitted. The verdict is re-translated against THIS card's rows (Finalize numbering differs from the fix-loop card) and checked by a `parse --rows "$ROWSFILE" --answer "$SUGGESTFILE"` dry run. A refusal means `rm -f "$SUGGESTFILE"` and no line; never print a guessed one. No button change.
- **Parse.** Typed "bottom line" with `$SUGGESTFILE` present means `cp "$SUGGESTFILE" "$ANSWERFILE"`, then the parse fence.
- **Refusal (I-13).** "Re-show the SAME card (D-06 …)" is gone. Now: "On `refused: empty answer` re-show the card once (nothing to translate). On any other refusal go to **Translate the answer (D-01)**."
- **Translate the answer (D-01).** This mirrors the 58-04 paragraph verbatim (same ref kinds and markers, the "OWNER's text only" rule, and the same three fences in `mktemp` / `if … else … fi` form with only `"$…FILE"` paths). The Finalize differences:
  - reason: "otherwise the Q2 pick still supplies the reason when the owner's text gave none"
  - "`close_out` is always false here: Finalize has no Rerun to carry it through — after recording, the gate re-runs and decides"
  - ok branch: "print `Read your answer as: <grammar>` as message text, then continue at **After the answer** exactly as a typed answer does (its `otherwise` bullet prints `echo_text`) — no confirm card"
  - ok false: "→ **Ask only what is missing (D-05, D-06)** (the next paragraph)"
- **Echo sentence (I-11).** Now reads: "… and when step 2 routes to the fix-loop card, that card is not shown (the subset goes straight to its Step B), so print `echo_text` as message text before reading `50-fix-loop.md`."
- **Left untouched as planned.** The stop messages, the REVIEW.md orphan/superseded rendering, the `need_text` "re-show the same card ONCE" bullet and the Card budget line (58-09 owns it).

## Verification (observed)

- **RED (Task 1):** `pytest -q scripts/test_finalize_card.py` gave `18 failed, 34 passed, 64 subtests passed`.
  - All 5 `test_*_holds` failed, plus `test_list_and_echo_visible_on_screen` (the new ECHO_VISIBLE needle).
  - Each `test_mutant_*` subtest errored because its needle was absent.
  - `bare_mixed`, `same_turn`, `no_nudge` and `q1_q2_labels` passed unchanged.
- **Task 2:** `pytest -q scripts/test_finalize_card.py scripts/test_card_text.py scripts/test_pause_batching.py scripts/test_confirmed_fix.py -k "not translate"` gave `182 passed, 2 deselected, 341 subtests passed`.
- **Task 2 grep gates** (all as required):

  | Pattern | Count |
  |---|---|
  | `Send every row, any band` | 0 |
  | `{{bulk_fix_text}}` | 1 |
  | `lowest band` | 0 |
  | `{{V}} needs-verification` | 1 |
  | `re-checks it once` | 0 |
  | `From your finalize answer` | 0 |
  | `Recommended` | 0 |

  The `git diff -U0` hunks are at 53, 113, 115-118, +126-150 and 145→170 only. There is no hunk at the stop messages or the orphan/superseded lines.
- **Task 3:** `pytest -q` over `test_finalize_card`, `test_card_text`, `test_pause_batching`, `test_finalize_archive_prose`, `test_carry_writers`, `test_fixcommit`, `test_tracecheck` and `test_confirmed_fix` gave `327 passed, 853 subtests passed`. No pin outside `test_finalize_card.py` needed an edit.
- **Task 3 grep gates:**

  | Pattern | Count |
  |---|---|
  | `Re-show the SAME card` | 0 |
  | `re-show the same card ONCE` | 1 |
  | `resolve --rows "$ROWSFILE" --answer "$REFSFILE"` | 1 |
  | `Read your answer as: ` | 1 |
  | `close-out-after-rerun` | 0 |

- **Mutant tests:** `pytest -q scripts/test_finalize_card.py -k mutant -v` gave `6 passed, 34 deselected`. That is the six `test_mutant_*` methods; their subtests all pass.
- **Full suite:** `pytest -q` (bare, from plugins/vibe-check) gave `3459 passed, 4601 subtests passed in 163.58s`, with 0 failed. That is 3448 + the 11 new TestPhase58Finalize tests.

## Mutant table (owner rule: applied to the REAL file, observed, reverted)

Driver: `scratchpad/mutants_5805.py` rewrites `90-finalize.md`, runs `pytest -q scripts/test_finalize_card.py`, and restores the original in a `finally`. It printed `restored: True`, and `git status` was clean for the file afterwards.

| # | Mutant on 90-finalize.md | Result | Tripped |
|---|---|---|---|
| M1 | Fix all back to "Send every row, any band, to the fix-loop card" | 2 failed | option_descriptions holds + mutant |
| M2 | `{{V}} needs-verification, ` dropped from the header | 2 failed | q1_header holds + mutant |
| M3 | "Re-show the SAME card (D-06 …)" back in place of the translate routing | 2 failed | translate_path holds + mutant |
| M4 | "the Q2 pick still supplies the reason …" deleted | 2 failed | translate_path holds + mutant |
| M5 | "re-checks it once …" restored | 2 failed | nv_stop_reconciled holds + mutant |
| M6 | old "as that card's closing \"From your finalize answer:\" block" restored | 2 failed | list_and_echo_visible_on_screen, mutant_echo_visible |
| M7 | "; never print a guessed one" deleted | 2 failed | bottom_line holds + mutant |
| M8 | " (Recommended)" appended to the suggestion slot | 3 failed | no_nudge, bottom_line holds + mutant |
| M9 | Mixed… back to "`all` means every row of the lowest band" | 2 failed | option_descriptions holds + mutant |
| M10 | `--close-out-after-rerun` written into the Translate paragraph | 1 failed | translate_path holds |
| M11 | resolve fence loses `--answer "$REFSFILE"` | 2 failed | translate_path holds + mutant |
| M12 | session condition "THIS session rendered the last pass's Bottom line" replaced | 2 failed | bottom_line holds + mutant |

The same mutants also run in memory as `TestPhase58Finalize.test_mutant_*` subtests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan inconsistency] `{{bulk_fix_text}}` count 1 vs a sentence that "says `{{bulk_fix_text}}` is the field"**
- **Found during:** Task 1
- **Issue:** Task 2 step 3 wrote the explanation sentence with the `{{bulk_fix_text}}` slot in it, but the grep gate requires the slot to appear exactly once.
- **Fix:** The sentence names the field ("it is the `bulk_fix_text` field of `$ROWSFILE`, verbatim") without the slot. This is the same resolution 58-04 used in the fix loop. The lock checks the slot count is 1.
- **Cost if wrong:** Low. The wording changes slightly; no behavior depends on it.
- **Files modified:** 90-finalize.md, test_finalize_card.py
- **Commit:** e414508, 776e56c

**2. [Rule 2 - Lock strength] Order check anchored on the After-the-answer heading**
- **Found during:** Task 3
- **Issue:** The Translate paragraph itself contains "continue at **After the answer**". An ordering check on that bare string would have matched the paragraph itself and could never trip.
- **Fix:** The check now anchors on "**After the answer** (branch on" and requires parse fence < Translate < After the answer.
- **Cost if wrong:** Low. The lock is stricter, nothing more.
- **Files modified:** test_finalize_card.py
- **Commit:** 2859d4f

**3. [Scope] Stale note on the echo line not added**
- **Found during:** Task 3
- **Issue:** The plan's action mentions "(with the stale note when `stale` is true)". Without `--prior-rows`, `stale` is always false, and the `--prior-rows` twin fence belongs to 58-09.
- **Fix:** Left it to 58-09 together with the twin fence.
- **Cost if wrong:** Low. 58-09 adds the note when it adds the fence.

## Known Stubs

- `90-finalize.md` Translate paragraph: the `ok` false sentence points to "**Ask only what is missing (D-05, D-06)** (the next paragraph)". That paragraph is written by 58-09 (next wave, same file), and until then the reference dangles. The plan intends this ("the sentence must already name it").
- The **Card budget** line still says "an unparseable answer adds another". 58-09 rewrites the budget line.

## Threat Flags

None. All new fences take only `"$…FILE"` paths. Owner text reaches helpers only through Write-tool files (T-58-18). Refs are read from the owner's text only (T-58-17). Translated answers re-enter **After the answer**, so the gate still decides `write` (T-58-20).

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md, plugins/vibe-check/scripts/test_finalize_card.py, this SUMMARY
- FOUND commits: 776e56c, e414508, 2859d4f
- STATE.md / ROADMAP.md untouched (orchestrator-owned)
