# Phase 58: Clear actions, recovery and answers acted on - Context

**Gathered:** 2026-10-27
**Status:** Ready for planning

<domain>
## Phase Boundary

The owner can tell what each card action does and what to do after an inconclusive re-check, and a clear plain-English answer to a decision card is carried out instead of being asked again (999.13 subset). Requirements RECV-01, RECV-02, ANSR-01, ANSR-02, ANSR-03. Scope: the fix-loop card (`phases/review/50-fix-loop.md`), the Finalize card (`phases/shared/90-finalize.md`), their helpers (`scripts/batch_card.py`, `scripts/batch_parse.py`), the report's recovery lines (`phases/review/40-render.md`, reasons in `scripts/score.py`), and reconciliation of existing guidance (README). No new manual, no closure-rule changes, no automatic closure.

</domain>

<decisions>
## Implementation Decisions

### Current behavior (scouted 2026-10-27 — the baseline these decisions change)
- Typed answers ("Other") go to `batch_card.py parse` → `batch_parse.py`, a strict grammar (`fix|defer|dismiss` + numbers/ranges/`rest`/`all`, `look N`, `-- reason`). It never guesses; on refusal it prints one fixed reason (never owner text), and the prose says "re-show the SAME card once" (`50-fix-loop.md:102`, `90-finalize.md:139`). That instruction caused the iPlayarr repeated-card loop.
- Accepted typed answers are already handled as "show what was recorded, then act" with no confirm card (D-06 echo-then-record): `echo_text` is printed, then `payload` → `carry_state.py record-decisions`, `fix_targets` → subset → Step B.
- Bulk rules: `rest`/`all` never reach a Needs-verification row for any verb; `dismiss/defer rest` covers mediums only; critical/warning/NV rows are dismissed/deferred only by number (`batch_parse.py:33-43`).
- Finalize Q1 "Fix all" is described as "Send every row, any band, to the fix-loop card" (`90-finalize.md:117`) but leaves NV rows out (K2, `54-RELEASE-READINESS.md:47`). It fails safe: Finalize stays blocked. The fix-loop "Apply all & rerun" also skips NV rows. It has a separate conditional note line (`50-fix-loop.md:64,66`).
- Both cards are at the 4-option limit and are deliberately NEUTRAL menus, with no "(Recommended)"/nudge (LEGIBLE-03, `50-fix-loop.md:12`, `90-finalize.md:75`). Mutation tests guard this (`test_fix_loop_card.py:671`, `test_finalize_card.py:321`).
- Inconclusive re-check: Phase 56 added `Fix not yet confirmed: <reason> — retried on the next run that reviews changes; or run /deep-review so the raising lane can answer; or dismiss it by number.` (`40-render.md:45`). The same tail is applied to every `verdict: fix not …` reason (`score.py:179-191`: no reviewer, no answer, still applies, snapshot mismatch, no trigger, settled, NV no change). It is false for still-applies / no-trigger / settled / NV-no-change, where nothing retries until the code changes (Phase 56 D-09). NV rows have a separate `Fix not yet verified:` line.
- Bug C, on paper: a Finalize-routed fix set goes "straight to Step B — ask NO AskUserQuestion" (`50-fix-loop.md:29`). A lock test exists (`test_fix_loop_card.py:399`, "A Finalize-routed subset goes straight to Step B with no card"). Not yet traced end to end against `fix N; defer M`.
- The report's **Bottom line** block is a 2–4 sentence plain-language verdict (`templates/output-format.md:20`, `40-render.md:79`), e.g. "fix the first two, ship, defer the rest".

### Acting on plain-English answers (ANSR-01)
- **D-01:** When a typed answer does not parse as grammar, Claude translates it into the card's grammar and runs the translation through the SAME strict `batch_card.py parse`. The parser stays the only gate; nothing it would refuse is acted on. If the translation parses, Claude **acts immediately with no confirm card**: it prints `Read your answer as: <grammar> — reason: <reason>` (plus the normal `echo_text`) and continues the fix/dismiss/close-out workflow. This matches the existing D-06 echo-then-record rule. Rejected alternatives: a yes/no confirm every time, and confirming only critical/warning dismissals.
- **D-02:** A reference counts as clear when it resolves to exactly one set of current rows: row numbers, titles or distinctive title words ("the Browse recovery issue"), or descriptions the card itself supports ("the 7 fixed rows", when exactly 7 rows carry that marker). A stated count must equal the matched count; on a mismatch, ask. Anything matching more than one candidate set is ambiguous (→ D-05).
- **D-03:** Reason: if the owner's words imply a why ("fixed", "out of scope", "false alarm"), use it as the reason, keeping the owner's wording, e.g. `fixed (owner: "dismiss the 7 fixed rows")`. If no why is present for a dismiss/defer, ask for the reason only. An explicit `-- reason` or Q2 pick still wins as today.
- **D-04:** Applies to both the fix-loop card's Other path and the Finalize card's Mixed…/Other path. Bulk safety rules are unchanged: a translation can never make `rest`/`all` cover an NV row, or dismiss/defer a critical/warning row the owner did not name. The parser enforces this.
- Reference case for the regression test: the eight-row fix-loop card. "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out" → `fix 5; dismiss 1,2,3,4,6,7,8` with reason "fixed in review-pass commits, verified on recheck" (or the owner-quoted equivalent per D-03), then fix → rerun → close-out with no repeated card.

### Asking only what's missing (ANSR-02)
- **D-05:** Partial clarity: **hold the whole answer and record nothing**. Ask one small question about only the unclear piece, then carry out the full answer together. Never half-apply. This matters for "fix X, then close out".
- **D-06:** Follow-up shape: one short AskUserQuestion naming only the ambiguous item. Candidate rows are buttons (`#3 auth.ts:40 — Login retry`, …). For a missing reason, offer the standard reason choices (False positive / Accepted risk / Out of scope for this milestone) plus Other. The full card is NOT re-shown.
- **D-07:** Stale card (the review re-ran, so rows were renumbered or changed): re-map the owner's references to current rows **by finding identity** (file/title/stable_hash), not by number. If every reference maps to exactly one current row, act and show the new numbers in the echo. Any reference that no longer maps (gone, merged, ambiguous) is asked about alone, per D-06.
- **D-08:** Bound: one follow-up per gap. If the reply is still unclear, record nothing and show the full card once with a note saying what could not be matched. No open-ended narrowing loop.

### Bottom line as a pickable choice (owner addition, within ANSR scope)
- **D-09:** When the report's Bottom line recommends a course of action that translates cleanly into card grammar, the card prints it under the list in row-number form, e.g. `Bottom line suggests: fix 1,2; defer 3-5 — type "bottom line" in Other to take it`. Typing "bottom line" / "do what it says" (or similar) is handled as a plain-English answer (D-01 path, same parser gate, same bulk rules). **No button change**: the 4 options and the neutral-menu rule (LEGIBLE-03) stay. Rejected: replacing an existing button, or a typed-only shortcut with no card hint.
- If the Bottom line does not map cleanly to rows (pure prose, or "ship" with nothing to decide), omit the suggestion line. Never print a guessed one.

### "Fix all" / "Apply all" labels (RECV-01)
- **D-10:** Keep the behavior and make the wording match. Finalize's Fix all description states what it covers and names the excluded rows by number, e.g. "Fix every critical, warning and medium row. Needs-verification rows (#4, #7) are not included — name them by number in Mixed…". Numbers come from the card's own rows. The exclusion clause is omitted when there are none. Rejected: making Fix all include NV rows, which would undo the v2.12 by-number rule.
- **D-11:** The fix-loop's "Apply all & rerun" follows the same wording rule (excluded NV rows named by number). The separate NV note line folds into it. One rule and one test cover both cards.
- **D-12:** A test locks the card text to the behavior: the rows the description says are included equal the rows the parser/payload actually sends for that option, and the named exclusions equal the NV rows left out. Mutation-test it.

### Recovery guidance (RECV-02)
- **D-13:** Replace the shared tail with an accurate **per-reason pair**: `Next run: <what happens automatically>` + `You can: <1–2 bounded actions>`. Examples: still-applies → "Next run: not re-checked until this code changes. You can: fix it again, or dismiss it by number." No eligible reviewer → "Next run: retried when an eligible reviewer (bugs/security) runs. You can: run /deep-review, or dismiss it by number." Cover every `verdict: fix not …` / `verdict: confirmed fix …` reason in `score.py`. A test asserts each reason has a pair and that "retried" appears only where the code actually retries. No automatic closure, no new manual.
- **D-14:** Reconcile against actual behavior: report recovery lines, Finalize "stays blocked" stop messages, rejection/orphan explanations in REVIEW.md (`90-finalize.md:218-219`, `batch_card.py` orphan status), and the README's recovery/state text. Fix any statement that disagrees with the code. No new docs page.

### Bug C verdict (ANSR-03)
- **D-15:** Evidence = a static trace + test, **no live run**. Trace the current prose step by step for Finalize `fix N; defer M` (deep review leaves a warning → Stop → Close out → finalize answer → subset → fix loop) and confirm no Apply/Skip card is asked. Confirm the existing lock test (`test_fix_loop_card.py:399`) fails when the "ask NO AskUserQuestion" rule is removed, and strengthen or add it if not. If the trace shows no re-ask: record "does not reproduce on current code" with the evidence and file nothing. If it does reproduce: fix it under the D-01..D-08 rules (same symptom: a decided answer is asked again) with a regression fixture. A live run would need a separately approved, priced proposal and is not part of this phase.

### Owner rulings after research (2026-10-27)
- **D-16 (Open Q1, complement-with-count):** A described group with a stated count (e.g. "the 7 fixed rows") resolves to the rows still unassigned after the owner's other references ONLY when exactly that many remain. It then counts as naming them by number, at any band (critical/warning/NV included), and the action proceeds immediately with the `Read your answer as: …` echo listing every row number. A count mismatch, or a description with no count that is not a real card marker, asks per D-05/D-06. A mutation test must prove a mismatch (e.g. owner says 6) asks.
- **D-17 (Open Q2):** "fix X, then close out": after the fix + rerun, go to Close out (Finalize) even if the rerun surfaces new findings. Finalize's card lists every undecided row, so nothing is skipped silently, and Finalize's gate still blocks until they are decided.
- Research verdicts (58-RESEARCH.md): the repeated-card loop, K2 and the recovery-text mismatch reproduce. **Bug C does NOT reproduce** (no-card rule since 46d78e3, v2.12). Record the verdict and file nothing. Tighten the lock against the surviving "add a show-the-card instruction" mutant and remove the stale sentences at `50-fix-loop.md:64` / `90-finalize.md:145` under D-14.

### Owner rulings after code review (2026-10-27, 58-REVIEW.md)
- **D-18 (group references to serious rows):** A described group (no row numbers or titles) that would DISMISS or DEFER any critical, warning or Needs-verification row acts only when the owner states a count and it matches exactly (same rule as D-16). Otherwise only the missing count is asked, per D-05/D-06. Medium-only groups and `fix` groups keep working without a count.
- **D-19 (Bottom line suggestion scope):** The D-09 suggestion line may include `fix` for any row but `dismiss`/`defer` for MEDIUM rows only. A suggested dismiss/defer of a critical, warning or Needs-verification row is dropped from the line, so those still need the owner's own words. Typing "bottom line" can therefore never dismiss or defer a serious row.
- **D-20 (hand-typed close-out flag):** Accepted. A hand-typed `--close-out-after-rerun` on a first run behaves like Stop here → Close out; Finalize's gate is unchanged. No extra state is needed to tell it apart from the automatic rerun.
- **Gap round (owner, 2026-10-27):** fix all 58-REVIEW.md warnings (WR-01..WR-06) and minor items now, before verification. Each is reproduced first with a failing test and mutant-checked; rulings D-18/D-19 apply; then full suite + replay, then a fresh review of only the gap changes.

### Owner rulings after the gap-round re-review (2026-10-27, 58-REVIEW-GAPS.md)
- **D-21 (final round, HARD STOP):** One final round fixes 58-REVIEW-GAPS.md WR-01 (second full card on the bottom-line path), WR-02 (ordinary phrasing gets a follow-up) and WR-03 (stale re-map can read the subset rows file and dismiss the wrong finding), plus the cheap info items. Each is reproduced first with a failing test and mutant-checked. WR-02 approach (Claude's technical call, accepted by the owner): title matching picks the single best-matching row, so extra words do not block a clear match; a tie or weak match still asks. WR-03: the prose names the CARD's rows file as the stale source, and the helper refuses a subset rows file as the prior card. WR-01: the suggestion file is kept while the same card is re-shown. Then ONE re-review. HARD STOP: if that re-review finds anything at warning level or above, Phase 58 closes with it documented as a known limit in the backlog. No further rounds.
- **D-22 (BLOBFILE):** Finalize's `$BLOBFILE` cross-call shell variable predates Phase 58 and fails safe. It is parked in the 999.13 backlog, not fixed here.

### Owner ruling after the final re-review (2026-10-28, 58-REVIEW-FINAL.md)
- **D-23 (CR-01 rollback, then close):** The final round's best-unique title matcher can act on a row the owner did not mean, at any band, with no confirm card. Reproduced: "fix the option list on the browse page, then dismiss the other 7 fixed rows and close out" became `fix 5; dismiss 1,2,3,4,6,7,8`. Roll back ONLY the title matcher to the 58-10 strict rule: every non-filler whole token of the ref must appear in the title; anything else asks. Keep every other final-round change: WR-01 suggestion kept on the D-08 fallback, WR-03 CARDROWSFILE + REASON_PRIOR_SUBSET, IN-01, IN-03, IN-05, and the extended band-word filler only if it cannot broaden a match. Revert the "best-match" sentences in 50-fix-loop.md / 90-finalize.md to the strict-rule wording. Add CR-01 regression fixtures: the reviewer's phrasings must ASK, never act. This is a rollback, not a new round; D-21's hard stop still holds. Re-opened as known limits in the backlog: WR-02 (wordier phrasings get a follow-up) and the reviewer's safer design (act only when the best row contains all of the owner's non-filler words; otherwise offer it as a one-click choice).

### Carried forward (locked from earlier phases)
- Reproduce first: each failure (repeated-card loop, misleading label, wrong recovery text, bug C) is reproduced or traced on current code before it is fixed. A non-reproducing path is recorded and dropped, never replaced with invented work.
- Never re-ask without new evidence (v2.11; Phase 56 D-09). NV rows are decided only by number (v2.12). Cards stay neutral menus (LEGIBLE-03). Owner text never goes on a command line and refusal strings never contain owner text.
- Single-writer: only `carry_state.py record-decisions` writes `decisions`. `stable_hash` / GOLDEN_DIGEST stay frozen. Existing suite (3311) and replay gate stay green. Mutation-test every new guard.
- Recovery wording must describe Phase 56/57 behavior as shipped (incl. known limits 999.23/999.24). Do not change closure or decision rules here.

### Claude's Discretion
- Whether the plain-English translation is purely prose-driven (Claude writes grammar into `$ANSWERFILE`) or assisted by a helper (e.g. a `batch_card.py` subcommand that resolves title/description references to candidate rows deterministically). Either way, the strict parser is the final gate, and ambiguity detection must be testable.
- Exact echo wording ("Read your answer as: …"), follow-up question text, and the note shown on the D-08 full-card fallback.
- Which row markers count as "card-supported descriptions" for D-02 (e.g. fixed / pending / Needs-verification / band).
- Whether "Fix all" keeps its label and only the description changes, or the label text changes too. If the label string changes, update `FINALIZE_Q1` / `FIX_LOOP_OPTIONS` and their tests together.
- Exact per-reason recovery wording within D-13.
- How the regression tests exercise LLM-performed translation (prose-lock tests + parser fixtures on the translated grammar for the eight-row case + ambiguous/stale fixtures).

</decisions>

<specifics>
## Specific Ideas

- The iPlayarr incident (2026-10-20, vibe-check 2.12.0 deep review, eight-row card): owner typed "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out"; the parser refused it ("answer does not match the grammar"); Claude re-showed the identical card; owner: "i just answered you". The expected mapping is `fix 5; dismiss 1,2,3,4,6,7,8`, reason "fixed in review-pass commits, verified on recheck". This is the primary regression fixture.
- Owner (this discussion): "often there is a recommendation of what to do in the 'bottom Line' section of the report - that should be a choice I can pick" → D-09.
- Recovery lines should read as "what happens next run" + "what you can do now", so a non-engineer owner can act without reading the technical sections.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` §"Phase 58" — success criteria, the iPlayarr bug write-up, bug C repro steps
- `.planning/REQUIREMENTS.md` — RECV-01/02, ANSR-01/02/03
- `.planning/milestones/v2.12-phases/54-freeze-release-gates-integration-audit/54-RELEASE-READINESS.md` §K2 (line 47) — origin of the "Fix all" label defect

### Decision cards and parsing
- `plugins/vibe-check/phases/review/50-fix-loop.md` — fix-loop card, Other path, Finalize-routed subset (no card), card budget
- `plugins/vibe-check/phases/shared/90-finalize.md` — Finalize card (Q1/Q2 options, Fix all text), parse/after-answer flow, stop messages, REVIEW.md dismissed/deferred/orphan rendering
- `plugins/vibe-check/scripts/batch_parse.py` — grammar, bulk rules, refusal reasons, option label constants
- `plugins/vibe-check/scripts/batch_card.py` — rows/parse/payload/select-questions, orphan/stale linking
- `plugins/vibe-check/scripts/test_fix_loop_card.py`, `test_finalize_card.py`, `test_batch_parse.py`, `test_batch_card.py`, `test_card_text.py` — existing locks (neutral menu, no-card subset, Fix all parsing)

### Recovery guidance
- `plugins/vibe-check/phases/review/40-render.md` (lines ~40-50, 79) — "Fix not yet confirmed/verified" lines, Bottom line placement
- `plugins/vibe-check/scripts/score.py` lines ~150-195 — `verdict: fix not …` / `confirmed fix …` reason constants
- `plugins/vibe-check/templates/output-format.md` §"Bottom line"
- `README.md` (repo root) — recovery/state text to reconcile

### Prior phase decisions
- `.planning/phases/56-verified-fixes-close/56-CONTEXT.md` — D-07..D-11 retry/still-applies/recovery behavior the guidance must describe
- `.planning/phases/57-decision-continuity-within-closure/57-CONTEXT.md` — decision reopen rules, stale suffixes, known limits (999.23/999.24)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `batch_card.py parse` + `batch_parse.py`: the strict validator every translated answer must pass. Already returns `echo_text`, `payload`, `fix_targets`, `need_text`, `look`.
- `batch_card.py` successor/orphan linking (`~line 375`): precedent for matching by finding identity rather than row number (useful for D-07 stale re-mapping).
- `select-questions` (multiselect of `#n file:line` labels): precedent for the D-06 candidate-row buttons.
- Card-text tests that mutation-check the prose (`test_fix_loop_card.py`, `test_finalize_card.py`): the pattern for D-12 and the D-01/D-05 prose locks.

### Established Patterns
- Echo-then-record with no confirm card (D-06 from v2.11), which D-01 extends.
- Owner text goes into files via the Write tool, never onto a command line; refusal strings are fixed and owner-free.
- Fixed option-label constants in `batch_parse.py` (`FIX_LOOP_OPTIONS`, `FINALIZE_Q1`), with tests pinning them.
- Bash fences run under bash (zsh word-split gotcha); subset paths are passed as literals.

### Integration Points
- Other/Mixed… branches in `50-fix-loop.md` (line ~93-102) and `90-finalize.md` (line ~128-141): where translation, the D-05/D-06 follow-up and the D-08 fallback replace "re-show the SAME card".
- Card question text in both files: where the D-09 Bottom line suggestion line and the D-10/D-11 exclusion wording go.
- `40-render.md:45` + `score.py` reason constants: where the D-13 per-reason pairs live.

</code_context>

<deferred>
## Deferred Ideas

- A one-click "Follow the Bottom line" button (rejected for now; it would break the neutral-menu rule and the 4-option limit). Revisit only if the D-09 typed path proves too hidden.
- A bounded live run for bug C, which requires a separately approved, priced proposal.
- Broader 999.13 documentation reconciliation (threat-model limits, configuration) stays in `.planning/backlog/MAINTENANCE.md`.

</deferred>

---

*Phase: 58-clear-actions-recovery-and-answers-acted-on*
*Context gathered: 2026-10-27*
