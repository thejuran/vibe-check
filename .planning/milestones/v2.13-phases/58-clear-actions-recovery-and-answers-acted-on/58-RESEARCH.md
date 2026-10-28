# Phase 58: Clear actions, recovery and answers acted on - Research

**Researched:** 2026-10-27
**Domain:** vibe-check decision cards (prose spine + `batch_card.py` / `batch_parse.py`), report recovery lines (`40-render.md` + `score.py` reasons), guidance reconciliation
**Confidence:** HIGH for reproductions and code facts (all run or read on HEAD `1211605`); MEDIUM for the recommended helper design and plan split

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Current behavior (scouted 2026-10-27 — the baseline these decisions change)
- Typed answers ("Other") go to `batch_card.py parse` → `batch_parse.py`, a strict grammar (`fix|defer|dismiss` + numbers/ranges/`rest`/`all`, `look N`, `-- reason`). It never guesses; on refusal it prints one fixed reason (never owner text), and the prose says "re-show the SAME card once" (`50-fix-loop.md:102`, `90-finalize.md:139`). That instruction caused the iPlayarr repeated-card loop.
- Accepted typed answers are already handled as "show what was recorded, then act" with no confirm card (D-06 echo-then-record): `echo_text` is printed, then `payload` → `carry_state.py record-decisions`, `fix_targets` → subset → Step B.
- Bulk rules: `rest`/`all` never reach a Needs-verification row for any verb; `dismiss/defer rest` covers mediums only; critical/warning/NV rows are dismissed/deferred only by number (`batch_parse.py:33-43`).
- Finalize Q1 "Fix all" is described as "Send every row, any band, to the fix-loop card" (`90-finalize.md:117`) but leaves NV rows out (K2, `54-RELEASE-READINESS.md:47`). It fails safe: Finalize stays blocked. The fix-loop "Apply all & rerun" also skips NV rows. It has a separate conditional note line (`50-fix-loop.md:64,66`).
- Both cards are at the 4-option limit and are deliberately NEUTRAL menus, with no "(Recommended)"/nudge (LEGIBLE-03, `50-fix-loop.md:12`, `90-finalize.md:75`). Mutation tests guard this (`test_fix_loop_card.py:671`, `test_finalize_card.py:321`).
- Inconclusive re-check: Phase 56 added `Fix not yet confirmed: <reason> — retried on the next run that reviews changes; or run /deep-review so the raising lane can answer; or dismiss it by number.` (`40-render.md:45`). The same tail is applied to every `verdict: fix not …` reason (`score.py:179-191`: no reviewer, no answer, still applies, snapshot mismatch, no trigger, settled, NV no change). It is false for still-applies / no-trigger / settled / NV-no-change, where nothing retries until the code changes (Phase 56 D-09). NV rows have a separate `Fix not yet verified:` line.
- Bug C, on paper: a Finalize-routed fix set goes "straight to Step B — ask NO AskUserQuestion" (`50-fix-loop.md:29`). A lock test exists (`test_fix_loop_card.py:399`, "A Finalize-routed subset goes straight to Step B with no card"). Not yet traced end to end against `fix N; defer M`.
- The report's **Bottom line** block is a 2–4 sentence plain-language verdict (`templates/output-format.md:20`, `40-render.md:79`), e.g. "fix the first two, ship, defer the rest".

#### Acting on plain-English answers (ANSR-01)
- **D-01:** When a typed answer does not parse as grammar, Claude translates it into the card's grammar and runs the translation through the SAME strict `batch_card.py parse`. The parser stays the only gate; nothing it would refuse is acted on. If the translation parses, Claude **acts immediately with no confirm card**: it prints `Read your answer as: <grammar> — reason: <reason>` (plus the normal `echo_text`) and continues the fix/dismiss/close-out workflow. This matches the existing D-06 echo-then-record rule. Rejected alternatives: a yes/no confirm every time, and confirming only critical/warning dismissals.
- **D-02:** A reference counts as clear when it resolves to exactly one set of current rows: row numbers, titles or distinctive title words ("the Browse recovery issue"), or descriptions the card itself supports ("the 7 fixed rows", when exactly 7 rows carry that marker). A stated count must equal the matched count; on a mismatch, ask. Anything matching more than one candidate set is ambiguous (→ D-05).
- **D-03:** Reason: if the owner's words imply a why ("fixed", "out of scope", "false alarm"), use it as the reason, keeping the owner's wording, e.g. `fixed (owner: "dismiss the 7 fixed rows")`. If no why is present for a dismiss/defer, ask for the reason only. An explicit `-- reason` or Q2 pick still wins as today.
- **D-04:** Applies to both the fix-loop card's Other path and the Finalize card's Mixed…/Other path. Bulk safety rules are unchanged: a translation can never make `rest`/`all` cover an NV row, or dismiss/defer a critical/warning row the owner did not name. The parser enforces this.
- Reference case for the regression test: the eight-row fix-loop card. "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out" → `fix 5; dismiss 1,2,3,4,6,7,8` with reason "fixed in review-pass commits, verified on recheck" (or the owner-quoted equivalent per D-03), then fix → rerun → close-out with no repeated card.

#### Asking only what's missing (ANSR-02)
- **D-05:** Partial clarity: **hold the whole answer and record nothing**. Ask one small question about only the unclear piece, then carry out the full answer together. Never half-apply. This matters for "fix X, then close out".
- **D-06:** Follow-up shape: one short AskUserQuestion naming only the ambiguous item. Candidate rows are buttons (`#3 auth.ts:40 — Login retry`, …). For a missing reason, offer the standard reason choices (False positive / Accepted risk / Out of scope for this milestone) plus Other. The full card is NOT re-shown.
- **D-07:** Stale card (the review re-ran, so rows were renumbered or changed): re-map the owner's references to current rows **by finding identity** (file/title/stable_hash), not by number. If every reference maps to exactly one current row, act and show the new numbers in the echo. Any reference that no longer maps (gone, merged, ambiguous) is asked about alone, per D-06.
- **D-08:** Bound: one follow-up per gap. If the reply is still unclear, record nothing and show the full card once with a note saying what could not be matched. No open-ended narrowing loop.

#### Bottom line as a pickable choice (owner addition, within ANSR scope)
- **D-09:** When the report's Bottom line recommends a course of action that translates cleanly into card grammar, the card prints it under the list in row-number form, e.g. `Bottom line suggests: fix 1,2; defer 3-5 — type "bottom line" in Other to take it`. Typing "bottom line" / "do what it says" (or similar) is handled as a plain-English answer (D-01 path, same parser gate, same bulk rules). **No button change**: the 4 options and the neutral-menu rule (LEGIBLE-03) stay. Rejected: replacing an existing button, or a typed-only shortcut with no card hint.
- If the Bottom line does not map cleanly to rows (pure prose, or "ship" with nothing to decide), omit the suggestion line. Never print a guessed one.

#### "Fix all" / "Apply all" labels (RECV-01)
- **D-10:** Keep the behavior and make the wording match. Finalize's Fix all description states what it covers and names the excluded rows by number, e.g. "Fix every critical, warning and medium row. Needs-verification rows (#4, #7) are not included — name them by number in Mixed…". Numbers come from the card's own rows. The exclusion clause is omitted when there are none. Rejected: making Fix all include NV rows, which would undo the v2.12 by-number rule.
- **D-11:** The fix-loop's "Apply all & rerun" follows the same wording rule (excluded NV rows named by number). The separate NV note line folds into it. One rule and one test cover both cards.
- **D-12:** A test locks the card text to the behavior: the rows the description says are included equal the rows the parser/payload actually sends for that option, and the named exclusions equal the NV rows left out. Mutation-test it.

#### Recovery guidance (RECV-02)
- **D-13:** Replace the shared tail with an accurate **per-reason pair**: `Next run: <what happens automatically>` + `You can: <1–2 bounded actions>`. Examples: still-applies → "Next run: not re-checked until this code changes. You can: fix it again, or dismiss it by number." No eligible reviewer → "Next run: retried when an eligible reviewer (bugs/security) runs. You can: run /deep-review, or dismiss it by number." Cover every `verdict: fix not …` / `verdict: confirmed fix …` reason in `score.py`. A test asserts each reason has a pair and that "retried" appears only where the code actually retries. No automatic closure, no new manual.
- **D-14:** Reconcile against actual behavior: report recovery lines, Finalize "stays blocked" stop messages, rejection/orphan explanations in REVIEW.md (`90-finalize.md:218-219`, `batch_card.py` orphan status), and the README's recovery/state text. Fix any statement that disagrees with the code. No new docs page.

#### Bug C verdict (ANSR-03)
- **D-15:** Evidence = a static trace + test, **no live run**. Trace the current prose step by step for Finalize `fix N; defer M` (deep review leaves a warning → Stop → Close out → finalize answer → subset → fix loop) and confirm no Apply/Skip card is asked. Confirm the existing lock test (`test_fix_loop_card.py:399`) fails when the "ask NO AskUserQuestion" rule is removed, and strengthen or add it if not. If the trace shows no re-ask: record "does not reproduce on current code" with the evidence and file nothing. If it does reproduce: fix it under the D-01..D-08 rules (same symptom: a decided answer is asked again) with a regression fixture. A live run would need a separately approved, priced proposal and is not part of this phase.

#### Carried forward (locked from earlier phases)
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

### Deferred Ideas (OUT OF SCOPE)
- A one-click "Follow the Bottom line" button (rejected for now; it would break the neutral-menu rule and the 4-option limit). Revisit only if the D-09 typed path proves too hidden.
- A bounded live run for bug C, which requires a separately approved, priced proposal.
- Broader 999.13 documentation reconciliation (threat-model limits, configuration) stays in `.planning/backlog/MAINTENANCE.md`.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RECV-01 | "Fix all" states what it does; card says which findings need individual decisions | Verdict 2 (K2 reproduces); inventory items I-1..I-4; helper-rendered option descriptions (Pattern 3); D-12 lock design (Validation) |
| RECV-02 | Inconclusive re-check shows bounded recovery (next run / you can); guidance reconciled | Verdict 3 per-reason retry table with code cites; inventory I-5..I-14; recovery-pair table + test design (Pattern 4) |
| ANSR-01 | Unambiguous plain-English answer translated into validated grammar, workflow continues, no re-show | Verdict 1 (loop reproduces); `resolve` helper (Pattern 1); close-out intent routing (Pattern 2); Open Q1 (the "7 fixed rows" reference) |
| ANSR-02 | Ambiguous/missing/stale → ask only the missing detail | `resolve` statuses one/none/many + count check; stale re-map by `stable_hash` then (file,title); AskUserQuestion limits (Pitfall 5) |
| ANSR-03 | Bug C verdict recorded | Verdict 4: does not reproduce on the governing rule (fixed by `46d78e3`, shipped in v2.12); lock trips on removal; one surviving mutant class + two contradictory residue sentences found |
</phase_requirements>

## Reproduction verdicts

All run on HEAD `1211605` (branch `feat/v2.13-phase-58`), scratch files only; the repo tree was left unchanged (verified with `git status`). Baseline suite: **3311 passed** (`pytest -q` from `plugins/vibe-check`, 209 s). [VERIFIED: local run]

### V1 — Repeated-card loop (ANSR-01/02): **REPRODUCES**

Fixture: an eight-row fix-loop rows doc (`at_pass: 3`, row 5 titled "Browse recovery leaves stale cursor", others "Fixed A…H").

| Answer file `q1` | `batch_card.py parse` result |
|---|---|
| `fix the Browse recovery issue, then dismiss the 7 fixed rows and close out` | exit 2, stderr `refused: answer does not match the grammar` |
| `fix 5; dismiss 1,2,3,4,6,7,8 -- fixed in review-pass commits, verified on recheck` | exit 0; `fix_targets` = [row 5]; `payload` = 7 dismiss entries, each with that reason; `echo_text` = `fix: #5 …` / `dismiss: #1 …, #8 …` / `Reason: fixed in review-pass commits, verified on recheck` |
| `fix 5; dismiss 1,2,3,4,6,7,8` (no reason) | exit 2, `refused: dismiss/defer needs a reason` (fix-loop `q2` is always null, so the reason must be inline) |

Prose instruction that turns the refusal into a loop: `50-fix-loop.md:102` "On a refusal … re-show the SAME card once (D-06: an unparseable answer re-asks, never guesses)" and `50-fix-loop.md:144` card budget "(an unparseable answer … re-shows the same card once, at the owner's request)"; Finalize twin `90-finalize.md:139` "Re-show the SAME card (D-06 …)" and `:174`. [VERIFIED: file read + local run]

Additional finding the planner needs: **the grammar has no "close out" verb.** On the fix-loop Other path, `fix_targets` non-empty → subset → Step B → the Rerun; `fix_targets` empty → the Rerun (`50-fix-loop.md:121-122`). Close out exists only as the Stop here… second card (`:138`). So "…and close out" cannot be expressed in grammar today; the translation must carry a separate close-out intent (see Pattern 2). [VERIFIED: file read]

### V2 — "Fix all" / "Apply all & rerun" vs behavior (RECV-01): **K2 REPRODUCES (Finalize); fix-loop wording already roughly honest**

Rows: 1 critical, 2 warning, 3 NV, 4 medium, 5 NV.

| Path | Code path | Rows actually sent | NV rows |
|---|---|---|---|
| Finalize Q1 **Fix all** | `_BUTTON_TEXT["Fix all"] = "fix rest"` (`batch_parse.py:85-89`); `_rest_bands_for("fix")` = critical/warning/medium (`:107-111`) | 1, 2, 4 | 3, 5 left `undecided`; echo says `still open: #3, #5` and `2 needs-verification undecided — still open; finalize stays blocked` |
| Fix-loop **Apply all & rerun**, ordinary card | `select(rows, {"all": true}, subset=False)` drops `band == needs-verification` (`batch_card.py:749-753`) | 1, 2, 4 | 3, 5 not sent |
| Fix-loop subset card (Finalize-routed) | `subset=True` → every row (`batch_card.py:751`) | 1–5 | sent (owner named them) |

- `90-finalize.md:117` "**Fix all** — Send every row, any band, to the fix-loop card" is **false** whenever an NV row exists. [VERIFIED: local run]
- `50-fix-loop.md:66` already says "(Needs-verification rows are not applied — confirm them by number.)" and `:64` adds a conditional NV note line — true, but names no rows by number (D-11 wants the numbers). [VERIFIED: file read]
- Related false/incomplete Finalize card text found while reproducing (feed into D-10/D-14, see inventory I-2..I-4): Dismiss all says only critical/warning stay open (NV also stays open); Mixed… says "`all` means every row of the lowest band (same as `rest`)", which is false for `fix all`; the Q1 header counts `{{C}} critical/warning, {{M}} medium` and omits NV rows, so C+M ≠ N when NV rows exist.

### V3 — Recovery tail vs each reason (RECV-02): **REPRODUCES, but narrower than CONTEXT states**

Correction to the CONTEXT baseline: `40-render.md:45` already special-cases three reasons — STILL and SETTLED render "Still applies per a reviewer's independent re-check — it is re-checked again after its code changes."; NV_NO_CHANGE renders "Stays open for your decision: …". The shared "retried on the next run that reviews changes; or run /deep-review…; or dismiss it by number." tail is applied to the remaining four `verdict: fix not …` reasons. `verdict: confirmed fix …` rows get only `Fix not yet verified: <reason>` (`:43`), with no next-run/you-can pair. [VERIFIED: file read]

Two general facts that decide the wording:
- **A run with no new changes dispatches no reviewer, under `/review` or `/deep-review`.** `05-state.md:87-89` step 5: incremental diff empty + carry-forward non-empty → "skip agent dispatch and proceed directly to Phase 3". Both commands use the same state file (key by mode, not by command). So "or run /deep-review" helps only when there are new changes to review. [VERIFIED: file read]
- Requests are re-issued every pass a record is carried (`20-dispatch.md:84-106`): a plain block when the raising lane is dispatched; an independent block to the record's own agent → `bugs` → `security` → first dispatched agent when it is not. NO_REVIEWER can only occur when zero eligible native agents were dispatched. [VERIFIED: file read]

| Reason constant (`score.py`) | Emitted at | Does a later run retry it automatically? | Evidence | Today's render | True? |
|---|---|---|---|---|---|
| `_R_IR_NO_REVIEWER` "no eligible reviewer ran this pass" | `:2445` (carried lead, no matching request, status needs-recheck or trigger holds) | **Yes**, on the next run that reviews new changes and dispatches any native agent | `20-dispatch.md:96` ladder; `05-state.md:62` "no agent is dispatched on that path" | shared tail | "retried…" true; "**run /deep-review**" false on an unchanged tree |
| `_R_IR_NO_ANSWER` "the routed reviewer gave no verdict" | `:1583` | **Yes**: the request is re-issued on every dispatching run | `20-dispatch.md:100` "retried on the next run that dispatches an eligible reviewer" | shared tail | mostly true; /deep-review caveat as above |
| `_R_IR_SNAPSHOT` "the reviewed code is not the code at HEAD" | `:1589`, `:1607` | **Yes**, re-asked on every dispatching run; closes only when the file is clean (HEAD = index = worktree) when it is read | `snapshot_blob` null when dirty (`20-dispatch.md:96`) | shared tail | "retried" true, but the useful action is "commit or stash your edits to that file", which is not stated |
| `_R_IR_NO_TRIGGER` "no change near the finding or in its file since it was raised" | `:1581`, `:1601` | **Asked again, but it cannot close** until its file, a test of it, or code near the line changes | `_independent_trigger` gate before any verdict is read (`:1580-1581`, `:1600-1601`) | shared tail | **false**: "retried on the next run that reviews changes" implies it can close then. Note 999.24: the real "near" window is ~8 lines, so do not print "5 lines" |
| `_R_IR_STILL` "the routed reviewer says it still applies" | `:1585`, `:1603` | **No**, until the code it judged changes | `recheck_settled` stored (`:2231-2243`); cleared only when a fingerprinted blob or touched path changes (`:2335-2344`); dispatch skips settled rows (`20-dispatch.md:96`) | special line | true |
| `_R_IR_SETTLED` "a reviewer said it still applies and the code is unchanged since" | `:1575`, `:1599` | **No**, same as STILL | same | special line | true |
| `_R_IR_NV_NO_CHANGE` "no change to this Needs-verification item's file or tests…" | `:1578` | **No**: a `resolved` cannot close it until its file or tests change | `:1576-1578` SA-01 | special line | true |
| `_R_CF_NO_REVIEWER` "confirmed fix awaiting independent re-check: no eligible reviewer this pass" | `:1545` | **Yes**, on every later dispatching run while HEAD's blob equals the repaired blob | `05-state.md:55` "an `applied` entry is forwarded whatever its `at_pass`"; `:1765-1767` evidence check | `Fix not yet verified: <reason>` only | no pair; true otherwise |
| `_R_CF_NO_ANSWER` "…the routed reviewer gave no verdict" | `:1547` | **Yes**, same | same | reason only | no pair |
| `_R_CF_SNAPSHOT` "…the reviewed code is not the repaired code" | `:1551` | **Yes** while the repaired blob is unchanged; if the file changed, the confirmed-fix evidence is voided (`"verdict: evidence changed since verification"`, `:1765-1767`) and the item falls back to the ordinary NV re-check | `:1762-1767` | reason only | no pair |
| `_R_CF_STILL` "confirmed fix not verified: the routed reviewer says it still applies" | `:1549` | **No**, until the code changes (settled at `:2231-2243`); a code change also voids the fix evidence | `:1769-1772` | reason only | no pair |
| `_R_CF_SETTLED` "…said it still applies and the code is unchanged since" | `:1772` | **No**, same as CF_STILL | same | reason only | no pair |

Not rendered (no `fix not`/`confirmed fix` prefix), so out of D-13 scope: `_R_ROUTED_ORPHAN`, `_R_CONTRADICTED`, "record not needs-recheck", "stale fix verdict", "evidence changed since verification", "confirmed fix on a non-needs-verification record", "agent not asked", "record not carried". Observation only, do not add work for it: a confirmed-fix item whose file changed after the fix shows no recovery line. [VERIFIED: grep + file read]

### V4 — Bug C (ANSR-03): **DOES NOT REPRODUCE on the governing rule**, with two caveats the planner should handle under D-14

Static trace for Finalize `fix N; defer M` (deep review leaves a warning → fix loop Stop here… → Close out → `--finalize`):
1. `90-finalize.md:113-139`: one card; Q1 typed via Mixed… → `parse` → `payload` (defer M) + `fix_targets` [N].
2. `:146` records the defer through `carry_state.py record-decisions`.
3. `:156-166` copies `fix_targets` to `$SUBSETFILE`, Reads `50-fix-loop.md`, enters "The fix-loop card" with the subset path.
4. `50-fix-loop.md:16-29` subset fence → "print Finalize's `echo_text` … write `{"all": true}` … go straight to **Step B** — ask NO AskUserQuestion". `:144` "a Finalize-routed subset costs no card".
5. Step B `payload` with `subset: true` sends every subset row (V2 table) → fix agent → the Rerun.

No Apply/Skip card is asked. History: bug C was written up on 2026-10-09 against 2.11.x; commit `46d78e3` (2026-10-09 23:26, "feat(52-09): … skip the card for a Finalize fix set") added the rule, and it shipped in tag `v2.12` (`git tag --contains 46d78e3` → `v2.12`). [VERIFIED: git log]

Mutation check on a scratch copy of the plugin:

| Mutant | `test_fix_loop_card.py` result |
|---|---|
| A: delete " — ask NO AskUserQuestion: the owner already chose these rows at Finalize (D-06)" | **FAILS** `test_subset_no_card` |
| B: replace it with "then ask one AskUserQuestion (Apply / Skip) before Step B" | **FAILS** `test_subset_no_card` |
| C: leave the bullet intact; add "When Finalize routed a fix set, show the card below so the owner can Apply or Skip." before **Same-turn rule** | **SURVIVES**: all 71 fix-loop tests and all 437 tests in the nine card/parse/render test files pass |

Caveats:
1. **Lock gap (mutant C):** `subset_no_card_problems` (`test_fix_loop_card.py:398-415`) checks only the subset bullet and the budget line. An instruction elsewhere in the card section to show the card for a Finalize-routed set is not caught. Strengthen the lock: no sentence outside the subset bullet may tie AskUserQuestion/"show the card" to the Finalize-routed case, and the subset bullet must remain the only route for `$SUBSETFILE` set at entry.
2. **Contradictory residue in the prose:** `50-fix-loop.md:64` still defines a closing `From your finalize answer:\n<echo_text>` block in the card QUESTION "ONLY when Finalize routed here", and `90-finalize.md:145` says the echo appears "when step 2 routes to the fix-loop card, as that card's closing 'From your finalize answer:' block". Both describe a card that `:29` says is never shown. Dead text is not a re-ask (the governing rule wins and the lock holds), so record **"does not reproduce on current code — fixed by 46d78e3 (v2.12)"** and file nothing. Remove or rewrite the residue under D-14, because it disagrees with behavior. Caveat on the fix-loop Other path: `50-fix-loop.md:121` reuses the subset fence for an owner's typed `fix N` in the fix loop. There, `$SUBSETFILE` is set but nothing came from Finalize, so the "From your finalize answer" wording would be wrong there too.

### V5 — Inventory of text that disagrees with code (D-14)

| # | Where | Statement | Actual behavior (evidence) | Owner phase-58 plan |
|---|---|---|---|---|
| I-1 | `90-finalize.md:117` | Fix all: "Send every row, any band, to the fix-loop card" | NV rows excluded (V2) | finalize |
| I-2 | `90-finalize.md:115-116` | Dismiss/Defer all: "Critical/warning rows stay open unless you name them" | NV rows also stay open (`_rest_bands_for`, `batch_parse.py:107-111`) | finalize |
| I-3 | `90-finalize.md:118` | Mixed…: "`all` means every row of the lowest band (same as `rest`)" | `fix all` = critical+warning+medium; NV never; dismiss/defer all = medium (`batch_parse.py:33-43`) | finalize |
| I-4 | `90-finalize.md:113` | Q1 header "({{C}} critical/warning, {{M}} medium…)" | NV rows counted in N but not shown in the breakdown | finalize |
| I-5 | `90-finalize.md:53` | NV stop list: "the next review run re-checks it once … if that run does not close it, it stays open until you decide it" | Retried on every later dispatching run while the repaired blob is unchanged (`05-state.md:55,61`; `score.py:1765-1772`) | finalize |
| I-6 | `README.md:337` | "gets **one** automatic independent re-check, on the next review run…" | same as I-5 | recovery |
| I-7 | `40-render.md:45` | shared tail on NO_REVIEWER / NO_ANSWER / SNAPSHOT / NO_TRIGGER | V3 table: "/deep-review" false on an unchanged tree; NO_TRIGGER cannot close until a change | recovery |
| I-8 | `40-render.md:83` + `templates/output-format.md:70` | NV needs-recheck suffix "…retried on the next run that reviews changes; or run /deep-review; or dismiss" | same /deep-review caveat | recovery |
| I-9 | `40-render.md:43` | `Fix not yet verified: <reason>` only | D-13 needs a pair per CF reason | recovery |
| I-10 | `50-fix-loop.md:64` | "From your finalize answer:" block inside the card question | No card is shown on a Finalize-routed pass (V4) | fix-loop |
| I-11 | `90-finalize.md:145` | echo appears "as that card's closing … block" | same | finalize |
| I-12 | `50-fix-loop.md:73` | "A recorded dismiss or defer holds until its own line is edited or its band changes (D-12); unrelated edits elsewhere never re-ask it." | Phase 57: a nearby change reopens it, a joined concern reopens it, a band **drop** keeps the decision, a rise reopens only with a new lane; NV: any band change reopens (`carry_state.stale_cause`, `carry_state.py:918-950`) | fix-loop |
| I-13 | `50-fix-loop.md:102,144`; `90-finalize.md:139,143,174` | "re-show the SAME card" on refusal | replaced by D-01..D-08 | fix-loop / finalize |
| I-14 | `90-finalize.md:218-219`, `review-md-schema.md:66`, `batch_card.decisions_report` | orphan → `(finding no longer in the last pass)` + ` (superseded)` | **Consistent**: an orphan never has a joined record, so `file` is always null for it (`batch_card.py:950-960`). No change needed; record as checked | — |
| I-15 | `90-finalize.md:168-170` stop messages | "Finalize stays blocked — name each remaining … by number…" | **Consistent** with the gate re-run at `:167` | — |

README has no other recovery or card text: grep for Fix all, Apply all, retried, orphan and superseded finds only `:337`. `plugins/vibe-check/` has no README. `plugins/vibe-check/docs/architecture.md` has no recovery wording. [VERIFIED: grep]

## Summary

Phase 58 has three separate problems on one set of files. (1) The answer path: `batch_card.py parse` is a correct, strict gate, but the prose turns every refusal into "re-show the SAME card", so a clear plain-English answer loops. The fix is to put a translation step in front of the same gate, plus a bounded follow-up, and to drop the re-show. (2) Labels: Finalize "Fix all" claims to cover every band but sends no NV rows. Several neighbouring Finalize descriptions are also wrong or incomplete about NV and `all`. (3) Recovery lines: the Phase 56 tail promises "/deep-review" help that cannot happen on an unchanged tree, and implies a NO_TRIGGER row can close on the next run. Confirmed-fix rows have no next-step guidance at all.

The safest design makes everything the owner reads and everything a test must lock deterministic: helper output, not prose. `batch_card.py` already renders `card_text` and `echo_text` that the prose copies verbatim. Extend that pattern with (a) helper-rendered option descriptions that name the excluded NV rows (D-10/D-11/D-12), and (b) a pure `resolve` subcommand that maps owner references (numbers, title words, card markers, prior-card numbers) to current rows with a one/none/many status. That makes ambiguity (D-02/D-05), "no broadening" (D-04) and stale re-mapping (D-07) unit-testable. Claude's job shrinks to pulling reference phrases out of the owner's text. The parser stays the final gate.

Bug C does not reproduce: the no-card rule exists (since v2.12) and its lock trips. The lock has a gap (an off-bullet instruction survives), and two residue sentences still describe a card for the Finalize-routed case. Tighten the lock and remove the residue. File nothing.

**Primary recommendation:** Add `batch_card.py resolve` and helper-rendered option texts first (wave 1, alongside the recovery-line plan), then rewrite the two card prose files in parallel (wave 2) against them. Every new lock carries a mutant.

## Architectural Responsibility Map

The project is a Claude Code plugin, so the usual web tiers map to: **Prose spine** (LLM-executed `phases/**/*.md`), **Deterministic helper** (`scripts/*.py`, pure, tested), **State** (JSON under `.turingmind/state/format-53/`, single writer per family), **Owner UI** (AskUserQuestion card + message text).

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Extract reference phrases + intent (fix/dismiss/defer/close out, reason words) from owner text | Prose (Claude) | — | Natural-language reading; cannot be deterministic |
| Map references → current row numbers; ambiguity/count/stale checks | Helper (`batch_card.py resolve`) | Prose fallback | Must be testable (CONTEXT discretion note); title text is untrusted diff data |
| Validate grammar + bulk safety | Helper (`batch_parse.py` via `parse`) | — | Already the only gate (D-01) |
| Record decisions | Helper (`carry_state.py record-decisions`) | — | Single writer (locked) |
| Option descriptions naming excluded NV rows | Helper (rows doc field, copied verbatim) | Prose template | D-12 requires text == behavior; the helper already owns numbering |
| Bottom line → grammar suggestion | Prose (Claude translation) | Helper (`parse` dry-run validation) | Bottom line is LLM prose, not state |
| Per-reason recovery pairs | Prose table in `40-render.md` | Test cross-checks against `score.py` constants | Phase 4 render is prose; reasons are `score.py` constants (frozen output) |
| Close-out after a translated answer | Prose routing | Finalize gate (`finalize_gate.py`) | Gate keeps the verification and close-out checks |

## Standard Stack

No new external dependencies. The stack is fixed by the repo.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.14.5 (local) | helpers (`batch_card.py` is "stdlib only", docstring `:67-68`) | repo rule |
| pytest | 9.0.3 (local) | test runner; bare `pytest` from `plugins/vibe-check` | project instruction |
| unittest | stdlib | test style used by every `test_*.py` (`TestCase`, `subTest` mutants) | existing convention |

**Installation:** none.

## Package Legitimacy Audit

No external packages are installed by this phase, so slopcheck is not applicable. **Packages removed:** none. **Packages flagged:** none.

## Architecture Patterns

### System Architecture Diagram

```
 owner answers card ──► AskUserQuestion result
        │
        ├─ button (Apply all / Fix all / …) ─► existing routing (unchanged; descriptions now helper-rendered)
        │
        └─ Other / Mixed… text ─► Write {"q1": text} ─► batch_card.py parse
                                                     │
                                  ok ◄───────────────┤ refused (fixed reason)
                                  │                  ▼
                                  │      Claude: extract refs + intent from OWNER TEXT ONLY
                                  │      ("bottom line" → copy validated $SUGGESTFILE)
                                  │                  │ write refs file
                                  │                  ▼
                                  │      batch_card.py resolve --rows CUR [--prior-rows OLD] --refs F
                                  │        per ref: one | none | many (+ candidates) ; count check ; stale remap
                                  │                  │
                                  │     all "one" + reason present?
                                  │        │yes                         │no (≤1 follow-up per gap, D-05/06)
                                  │        ▼                            ▼
                                  │  write grammar ─► parse ◄── AskUserQuestion (candidates / reason only)
                                  │        │ ok                          │ still unclear
                                  ▼        ▼                             ▼
                     print "Read your answer as: …" + echo_text      D-08: record nothing, full card once + note
                                  │
                     payload ─► carry_state.py record-decisions (single writer)
                     fix_targets ─► subset fence ─► Step B (no card) ─► Rerun
                     close-out intent ─► (after rerun, or directly when nothing to fix) ─► --finalize ─► finalize_gate
```

### Recommended file ownership (avoids parallel-edit conflicts)

```
plugins/vibe-check/
├── scripts/batch_card.py          # Plan A only: resolve subcommand + option-text rendering
├── scripts/batch_parse.py         # Plan A only, if a label or constant changes (prefer no change)
├── scripts/test_answer_resolve.py # Plan A (new): resolve fixtures incl. eight-row iPlayarr card
├── scripts/test_card_scope.py     # Plan A (new): D-12 text == behavior for both cards
├── phases/review/40-render.md     # Plan B only
├── templates/output-format.md     # Plan B only
├── README.md (repo root)          # Plan B only (I-6)
├── scripts/test_recovery_pairs.py # Plan B (new); Plan B also updates test_confirmed_fix.py RENDER_NEEDLES
├── phases/review/50-fix-loop.md   # Plan C only (+ test_fix_loop_card.py)
└── phases/shared/90-finalize.md   # Plan D only (+ test_finalize_card.py)
```

### Pattern 1: Deterministic reference resolution (`batch_card.py resolve`), recommended over prose-only

**What:** a pure function `resolve_refs(rows_doc, refs, prior_rows_doc=None)` plus CLI `resolve --rows ROWS --answer REFS [--prior-rows OLD]`. Owner-derived text arrives only through the `--answer` file, the same rule as `parse`. `REFS` is written by Claude with the Write tool, e.g.
`{"refs": [{"verb": "fix", "kind": "title", "text": "Browse recovery"}, {"verb": "dismiss", "kind": "marker", "marker": "rest-of-card", "count": 7}], "reason": "…" | null}`.
Kinds (Claude's discretion on the exact set): `number` (current card) · `prior_number` (remapped by `stable_hash`, then by unique (file, title) like `successor_links`, `batch_card.py:374-420`) · `title` (case-folded word containment over `_one_line(title)`) · `marker` (`band:<name>`, `pending`, `changed` (stale), `absorbed`, and a complement marker; see Open Q1).
Output per ref: `{"status": "one"|"none"|"many", "rows": [n…], "candidates": [{"label": "#n file:line", "title": …}]}`, plus a top-level `stale: bool` (prior and current rows differ), `count_mismatch`, and a ready `grammar` string built only from "one" refs (explicit numbers, never `rest`/`all`). The pure-function output contains no owner text, which keeps the same posture as REASONS. The CLI refuses with fixed reasons.

**Why the helper wins over prose-only:** (a) D-02 "exactly one set" and "count must equal" become assertions; (b) D-04 "no broadening" becomes testable: the grammar's row set == union of resolved refs; (c) D-07 re-map reuses the shipped identity rule; (d) it lowers the prompt-injection surface, because finding titles (attacker-authored diff data) are matched as data by code rather than read and reasoned over by the translating model. Prose-only leaves all four as untestable LLM behavior. Cost: one ~150-line subcommand + tests, in a file whose CLI/flag table (`SUBCOMMANDS`, `_FLAGS_BY_SUBCOMMAND`, `KNOWN_FLAGS`, `USAGE`, `_STATE_SUBCOMMANDS`) must be extended together. `TestCliContract` likely pins these.

**Testing:** pure-function fixtures (the eight-row card, ambiguous title, count mismatch, prior-card remap with a renumbered card, a ref to a row gone from the current card) + CLI contract + a mutant per check (drop the count check → mismatch fixture passes → test trips).

### Pattern 2: Close-out intent carried outside the grammar

The grammar has no close-out (V1). Recommended routing for a translated answer carrying "close out":
- `fix_targets` non-empty → record the payload → subset → Step B → Rerun → after the rerun's report, **go to Stop here → Close out with no fix-loop card** (Finalize's own gate and card handle anything still open, so "retain normal fix verification and close-out checks" holds). If the rerun hits the spine's no-findings skip, continue to `--finalize` instead of stopping.
- `fix_targets` empty → record → Close out directly (no Rerun).
- The echo states it: `Read your answer as: fix 5; dismiss 1,2,3,4,6,7,8 -- <reason>; then close out`.
Prose-lock this in `50-fix-loop.md`, and give the Finalize Other path the analogous "then finish" behavior if needed (it already re-runs the gate at `:167`).

### Pattern 3: Helper-rendered option descriptions (D-10/D-11/D-12)

Add rows-doc fields rendered by `batch_card.py` (like `card_text`), e.g. `bulk_fix_text` (fix-loop: "the `fix` agent applies every listed row except Needs-verification rows #3, #5 — confirm those by number"; Finalize: "Fix every critical, warning and medium row. Needs-verification rows (#3, #5) are not included — name them by number in Mixed…"), plus `nv_rows: [3, 5]`. Omit the clause when there are none. The prose copies them verbatim into the option description. D-12 test: for random/band-mixed rows, the set the text names as excluded == `[r.n for r in rows if band == NV]` == rows missing from `select({"all":true})` (fix-loop) and from `parse("Fix all").fix` (finalize). Mutant: change `_rest_bands_for("fix")` to include NV, or drop a number from the text, and the test must trip.
Labels: keep `FIX_LOOP_OPTIONS` / `FINALIZE_Q1` strings unchanged (recommended). A label change ripples to `_BUTTON_TEXT` keys (`batch_parse.py:85-90`), `test_batch_parse.py:69-75,106,121,429-432,515`, `test_batch_card.py:823,1307`, `test_card_text.py:380`, `test_fix_loop_card.py:646-672`, `test_finalize_card.py:99,321-323`, and both prose files.

### Pattern 4: Recovery pairs as a table locked to `score.py`

Put the 12 reasons in one table in `40-render.md` (reason literal → `Next run:` → `You can:`). The render rule: under the row, `Fix not yet confirmed:` / `Fix not yet verified:` + the reason, then the pair. New test `test_recovery_pairs.py`: import `score`, collect every module constant whose value starts with `verdict: fix not` or `verdict: confirmed fix`, and assert (1) each has exactly one row; (2) the word "retried"/"retries" appears only in rows for the RETRYING set {IR_NO_REVIEWER, IR_NO_ANSWER, IR_SNAPSHOT, CF_NO_REVIEWER, CF_NO_ANSWER, CF_SNAPSHOT}, citing V3; (3) "/deep-review" never appears without "after new changes" (or drop it entirely); (4) `README.md` and `90-finalize.md` no longer say "once"/"one automatic". Mutants: add "retried" to the STILL row; delete a row; add a synthetic constant. Also update `test_confirmed_fix.py` `RENDER_NEEDLES` (`:1171-1174`, currently pins "retried on the next run that reviews changes" and "run /deep-review") and check `test_verified_fixes.py:1271-1273` (pins the NV_NO_CHANGE line).

Draft pairs (wording at Claude's discretion; behavior must match V3):
- IR_NO_REVIEWER / CF_NO_REVIEWER: `Next run: retried automatically on the next review of new changes.` `You can: commit further work and re-run, or dismiss/defer it by number.` (A /deep-review with no new changes dispatches nobody.)
- IR_NO_ANSWER / CF_NO_ANSWER: `Next run: asked again on the next review of new changes.` `You can: wait for that run, or dismiss/defer it by number.`
- IR_SNAPSHOT / CF_SNAPSHOT: `Next run: asked again; it can close only when the file has no uncommitted edits.` `You can: commit or stash your edits to <file>, or dismiss/defer it by number.` (CF: "…while the fixed code stays as committed".)
- IR_NO_TRIGGER: `Next run: not closed until its file, a test of it, or code near it changes.` `You can: fix it, or dismiss/defer it by number.`
- IR_STILL / IR_SETTLED / CF_STILL / CF_SETTLED: `Next run: not re-checked until this code changes.` `You can: fix it again, or dismiss/defer it by number.`
- IR_NV_NO_CHANGE: `Next run: a re-check can close it only after its file or tests change.` `You can: confirm (fix N), dismiss or defer it by number.`

### Anti-Patterns to Avoid
- **Translating bulk phrases into explicit numbers:** "dismiss the rest/everything else" → explicit numbers would dismiss c/w/NV rows the owner did not name. Bulk phrases without a count must become `rest`/`all`, so the parser's bulk rules apply. Only references that resolve to exactly the stated count become numbers (D-02/D-04).
- **Half-applying:** recording the clear part, then asking (violates D-05). Write nothing before every gap is closed.
- **Reading titles as instructions:** titles are diff data and may be hostile. Refs come from owner text only.
- **Putting owner text or the reason on a command line** (locked). Refs and grammar go through files written with the Write tool.
- **Re-showing the full card as the first response to a refusal** (the bug). The full card is allowed only as the D-08 fallback.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Grammar validation / bulk safety | a second parser or prose rules | `batch_card.py parse` (unchanged) | one gate (D-01); its bulk rules are already tested |
| Stale re-map identity | new matching logic | `stable_hash` equality, then the `successor_links` (file, title) unique-candidate rule | shipped, tested precedent (`batch_card.py:374-420`) |
| Candidate buttons | ad-hoc labels | `_label(row)` `#n file:line` (`batch_card.py:661-665`); `select-questions` shape for >4 | labels never contain commas; parse-by-leading-number already tested |
| Decision writes | prose edits to state | `carry_state.py record-decisions` | single writer (locked) |
| Retry claims | reasoning from prose | `score.py` reason constants imported in the test | D-13 "retried only where the code retries" |
| One-line flattening of titles in new text | new sanitizer | `_one_line` / `_cut` | prevents fake rows in card text |

## Common Pitfalls

### Pitfall 1: Decorative locks
**What goes wrong:** a prose lock passes but cannot trip (6 of 8 Phase-40 plans shipped one; mutant C above shows the subset lock's gap).
**How to avoid:** every new check gets a `subTest` mutant that is asserted to differ from the source and to trip. Assert that fixtures contain what you think (e.g. assert the eight-row fixture really has 8 rows and row 5's title contains "Browse").

### Pitfall 2: The "7 fixed rows" has no card marker
**What goes wrong:** D-02 says descriptions must be card-supported, but no card suffix says "fixed" (suffixes are absorbed / pending / stale / routed only, `batch_card.py:519-534`). A naive marker-only resolver returns `none` and the regression case asks a question instead of acting.
**How to avoid:** decide Open Q1 before writing the resolver.

### Pitfall 3: Breaking existing prose pins
Pins that will change: `test_finalize_card.py:164` ("never re-show the card after recording", which should be kept), `:416-433` ("re-show the same card ONCE" for `need_text`); `test_fix_loop_card.py:299-303,398-415,774` (subset bullet text, budget sentence "A pass costs one card"), `:623-624` (`NV_APPLY_ALL_NOTE`, which D-11 folds away); `test_confirmed_fix.py:1171-1174`; `test_verified_fixes.py:1271-1273`. Update them in the same plan that edits the prose, and re-run the full suite (3311).

### Pitfall 4: Card budget text
Both files enumerate every extra card (`50-fix-loop.md:144`, `90-finalize.md:174`). Add the D-06 follow-up (one per gap) and the D-08 fallback, and remove "an unparseable answer … re-shows". `count_cards.py` (REL-02 metric) counts every main-session AskUserQuestion, so follow-ups count as cards. Keep them bounded.

### Pitfall 5: AskUserQuestion limits
1–4 questions, 2–4 options each, header ≤ 12 chars; Other is added by the tool (codebase constants `batch_card.py:126-129`, pinned by `test_card_headers_pinned_and_short`). [VERIFIED: codebase] [ASSUMED: tool limits unchanged in the current Claude Code release] A D-06 follow-up with 1 candidate still needs ≥2 options (e.g. "#3 …" / "None of these"). With >4 candidates, list them in the question text and take the number through Other.

### Pitfall 6: Stale detection does not exist today
`parse` reads only the rows file, not the state, so it accepts an answer against an outdated rows doc. Staleness is caught only later: `payload` refuses with REASON_ROWS_STATE (`batch_card.py:882-890`, at_pass/hash check), and `record-decisions` refuses a hash that is not open (`carry_state.py:1084-1094`, generic "malformed decisions payload"). The rows doc carries `at_pass`, `mode` and per-row `stable_hash`/`file`/`line`/`title`/`band`/`agent`. A cross-run stale card arises when the owner refers to a card from before a rerun or an earlier `--finalize`, whose numbers have since shifted (decided rows drop out of the Finalize card). The resolver should compare the prior rows doc (the temp path is still in context, or reconstruct from the card text the owner saw) to the current one.

### Pitfall 7: Bottom line availability
The Bottom line is rendered in Phase 4 as message text and is **not persisted** (`45-persist.md` stores `filtered[]` etc., not the Bottom line). On the fix-loop card it is in the same conversation. A separate `--finalize` invocation renders no report. Recommend: print the D-09 line on the Finalize card only when this session rendered the last pass's Bottom line, and omit it otherwise. Validate the translated suggestion with a `parse` dry run (parse writes nothing: `batch_card.py:27-28` "This module never writes a file"; CLI only prints). A suggestion with dismiss/defer and no reason returns `REASON_NO_REASON`. Either supply the Bottom line's own why or treat that refusal as "valid, reason to be asked when taken". Keep the validated grammar in a file and copy it file-to-file when the owner types "bottom line", so it stays bound to the rows it was checked against.

### Pitfall 8: Line 73 decision-hold text is stale
See I-12. It is easy to miss because it sits in an NV paragraph.

## Code Examples

Reproduction commands (record them in the plan's repro note):
```bash
# Source: run in this research session (scratch dir)
python3 "$VC/scripts/batch_card.py" parse --rows rows8.json --answer ans_plain.json   # exit 2: does not match the grammar
python3 "$VC/scripts/batch_card.py" parse --rows rows8.json --answer ans_gram.json    # exit 0: fix 5; dismiss 1-4,6-8 + reason
```
Existing fixture worth extending for the eight-row case: `scripts/fixtures/iplayarr45-six-row-state.json` (real iPlayarr titles, 3 critical / 2 warning / 1 medium; used by `test_verified_fixes.py`, `test_carry_state.py`). Builders: `test_batch_card.py` `synth_rows`, `rows_of`, `dismiss`, `nv_card_state`; `test_carry_state.py` `mk_finding`, `mk_pass`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Finalize-routed fix set re-asked on the fix-loop card (bug C) | subset goes straight to Step B | `46d78e3`, v2.12 | bug C does not reproduce |
| CF item re-checked once, on the next run | forwarded and retried every later dispatching run while the repaired blob is unchanged | Phase 56 | README:337 and 90-finalize:53 are stale |
| Decision holds until own line/band changes | nearby change / joined concern / lane-backed rise reopen; drop keeps | Phase 57 | 50-fix-loop:73 is stale |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | AskUserQuestion limits (1–4 questions, 2–4 options, header ≤12) still hold | Pitfall 5 | follow-up card rejected by the tool; low (the limits are pinned by existing passing tests and used in production cards) |
| A2 | A rerun on an unchanged tree under `/deep-review` uses the same state file as `/review` and dispatches no agents | V3 | if wrong, "/deep-review" advice could stay; medium. Verified from prose (`05-state.md:87-89`, key by mode), not from a live run |
| A3 | Complement-with-count reading of "the 7 fixed rows" is acceptable to the owner | Open Q1 | owner may consider it guessing; this decides whether the reference case acts or asks |

## Open Questions (RESOLVED)

1. **How does "the 7 fixed rows" resolve? (blocks the ANSR-01 regression test)**
   - What we know: the card has no "fixed" marker. On the eight-row card, after "the Browse recovery issue" resolves to #5, exactly 7 rows remain, and the owner stated 7.
   - Options: (a) a **complement-with-count** rule: "the N <words> rows" resolves to the remaining unassigned rows only when there are exactly N of them (no count → bulk `rest` semantics); (b) add a card-visible fix-status suffix (from the last pass's persisted `filtered[]` `verdict: fix not…`/`confirmed fix…` reasons, `45-persist.md:36`) so "fixed" becomes a real marker. Option (b) changes card text, and in iPlayarr 2.12.0 those rows carried no such reason anyway.
   - Recommendation: (a), with the count as the safety condition, tested with a mismatch mutant (owner says 6 → ask). The planner should state it in the plan as the D-02 marker choice (CONTEXT lists marker choice as Claude's discretion) and surface it to the owner at plan review, because it lets a description dismiss critical rows by implication.
   - RESOLVED: owner ruling D-16 (58-CONTEXT.md, 2026-10-27) — complement-with-count, at any band, with a count-mismatch mutant; implemented by 58-03 (`remaining` marker with `count`).
2. **Close-out after rerun when the rerun surfaces new findings.** Recommendation: go to Close out anyway. Finalize's card shows every undecided row, so nothing is skipped silently. Confirm with the owner only if the plan reviewer objects.
   - RESOLVED: owner ruling D-17 — go to Close out anyway. Durable carrier across the automatic Rerun = the whole-token `--close-out-after-rerun` re-entry marker (58-07 spine side, 58-08 fix-loop side), mirroring how Close out appends `--finalize`; no new state-file field.
3. **Fix-loop typed `fix N` path reuses the subset fence (`50-fix-loop.md:121`).** It is fine behaviorally; just make sure the residue cleanup (I-10) does not reintroduce Finalize-specific wording there.
   - RESOLVED: moot once the I-10 residue ("From your finalize answer:" block, `<echo_text>` slot) is fully removed by 58-04 Task 2; the `list_in_card_problems` lock asserts both needles are absent from the whole file.

## Environment Availability

Step 2.6: SKIPPED for external services. Only local Python 3.14.5 and pytest 9.0.3 are needed (both present). No live review, no paid runs, no installed-plugin sync (out of scope).

## Validation Architecture

(`workflow.nyquist_validation` is `false` in `.planning/config.json`. This section is included because the orchestrator asked for it.)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | unittest-style tests run by pytest 9.0.3 |
| Config file | none (tests in `plugins/vibe-check/scripts/test_*.py`) |
| Quick run command | `cd plugins/vibe-check && pytest -q scripts/test_batch_card.py scripts/test_batch_parse.py scripts/test_card_text.py scripts/test_fix_loop_card.py scripts/test_finalize_card.py scripts/test_confirmed_fix.py scripts/test_verified_fixes.py` (~6 s) |
| Full suite command | `cd plugins/vibe-check && pytest -q` (3311 passed, ~210 s). Never `python3 -m pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANSR-01 | eight-row plain answer → resolve → grammar `fix 5; dismiss 1,2,3,4,6,7,8 -- …` → parse ok, payload 7 + fix_targets [5] | unit + CLI | `pytest -q scripts/test_answer_resolve.py` | ❌ Wave 1 |
| ANSR-01 | prose: refusal → translate (no "re-show the SAME card"); echo "Read your answer as:"; close-out routing | prose lock + mutants | `pytest -q scripts/test_fix_loop_card.py scripts/test_finalize_card.py` | ✅ extend |
| ANSR-02 | ambiguous title → `many` + candidates; count mismatch; missing reason; prior-card remap; gone row → `none`; nothing recorded on partial | unit | `pytest -q scripts/test_answer_resolve.py` | ❌ Wave 1 |
| ANSR-02 | prose: one follow-up per gap, D-08 fallback, budget lines | prose lock | card tests | ✅ extend |
| ANSR-03 | subset no-card lock trips on mutants A, B **and C** | prose lock | `pytest -q scripts/test_fix_loop_card.py -k subset` | ✅ strengthen |
| RECV-01 | option text names exactly the NV rows that `select(all)` / `parse("Fix all")` leave out | unit (text == behavior) | `pytest -q scripts/test_card_scope.py` | ❌ Wave 1 |
| RECV-02 | every `score.py` fix-not/confirmed-fix reason has a pair; "retried" only for the retrying set; README/finalize no "once" | prose ↔ code | `pytest -q scripts/test_recovery_pairs.py scripts/test_confirmed_fix.py` | ❌ Wave 1 |

### Sampling Rate
- **Per task commit:** quick run command above
- **Per wave merge:** full suite (`pytest -q`) + replay gate (part of the suite: `test_replay.py`)
- **Phase gate:** full suite green; GOLDEN_DIGEST unchanged (no `score.py` output change, so do not edit `score.py` beyond, at most, no-op constants)

### Wave 0 Gaps
- [ ] `scripts/test_answer_resolve.py`: eight-row fixture (extend `fixtures/iplayarr45-six-row-state.json` or build from `synth_rows`), ambiguous/stale/count fixtures
- [ ] `scripts/test_card_scope.py`: D-12 lock for both cards
- [ ] `scripts/test_recovery_pairs.py`: D-13 lock

## Recommended Plan Breakdown

Order follows the owner rule (reproduce first): each plan opens with a RED test reproducing its failure on current code (V1/V2/V3/V4 above give the exact inputs).

| Wave | Plan | Owns (exclusive) | Content |
|------|------|------------------|---------|
| 1 | **A: helper** | `batch_card.py` (+ `batch_parse.py` only if unavoidable), `test_answer_resolve.py`, `test_card_scope.py`, `test_batch_card.py`, `test_card_text.py` | `resolve` subcommand (Pattern 1); option-text fields `bulk_*_text` + `nv_rows` in the rows doc (Pattern 3); CLI contract updates; D-12 lock; mutants |
| 1 | **B: recovery** | `40-render.md`, `templates/output-format.md`, `README.md` (root), `test_recovery_pairs.py`, `test_confirmed_fix.py`, `test_verified_fixes.py` (pins only) | per-reason table (Pattern 4), I-6..I-9; lock + mutants |
| 2 | **C: fix-loop prose** (after A) | `50-fix-loop.md`, `test_fix_loop_card.py` | Other path: translate → resolve → parse; D-05/06/08; close-out intent (Pattern 2); D-09 suggestion line; D-11 Apply all text from the helper; NV note folded; I-10, I-12, I-13; budget; bug-C lock strengthened (mutant C) |
| 2 | **D: finalize prose** (after A; parallel with C) | `90-finalize.md`, `test_finalize_card.py` | Mixed…/Other translation (same rules); Fix all / Dismiss all / Defer all / Mixed… / Q1 count text (I-1..I-4) from the helper; I-5, I-11, I-13; budget; D-09 line (session-conditional) |
| 3 | **E: verdicts + close** | `58-REPRO.md` (phase dir), no plugin files | Record V1–V5 verdicts with commands; bug C "does not reproduce — fixed by 46d78e3 (v2.12)"; full suite + replay; confirm I-14/I-15 checked-consistent |

E can instead be folded into the start of A/B (record the repro first). Either way, keep the bug-C verdict text and its evidence (commit, mutants A/B/C) in a committed phase doc.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | owner text and refs only through files written with the Write tool; `batch_parse` strict grammar; fixed refusal strings; `_one_line` flattening of diff-authored titles |
| V6 Cryptography | no | — |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Hostile finding title steers translation ("dismiss 1-8") | Tampering | refs extracted from owner text only; deterministic `resolve` matches titles as data; translated row set must equal the union of resolved refs (test); echo printed before acting |
| Owner text / reason on a command line | Tampering / injection | file-only transport (existing rule); prose-lock that new fences take only file paths |
| Broadened decision via bulk translation | Elevation (of decision scope) | bulk phrase → `rest`/`all` (parser bulk rules); explicit numbers only for count-matched references; mutant-tested |
| Refusal leaks owner text | Information disclosure | new resolve refusals drawn from a fixed REASONS tuple (existing test pattern `TestCliContract`) |

## Project Constraints (from CLAUDE.md)

- No project `./CLAUDE.md` in the repo root. Global rules apply: never pass user input to subprocess without structured args (owner text stays in files); never log sensitive data; guard nullable returns; don't swallow exceptions; follow existing repo conventions (stdlib-only helpers, fixed-reason refusals, verbatim-copied helper text, `bash -s <<'BASH'` fences under zsh).
- Bare `pytest` from `plugins/vibe-check`; suite currently 3311; mutation-test every new lock; reproduce before fixing; no paid/live runs; no installed-plugin sync; one branch/PR per phase (`feat/v2.13-phase-58`).

## Sources

### Primary (HIGH confidence)
- Codebase on HEAD `1211605`: `scripts/batch_parse.py` (full), `scripts/batch_card.py` (full), `scripts/score.py:130-215, 1520-1830, 2200-2460`, `scripts/carry_state.py:1080-1160, 918-950`, `phases/review/50-fix-loop.md` (full), `phases/shared/90-finalize.md` (full), `phases/review/40-render.md` (full), `phases/review/05-state.md:55-100`, `phases/review/20-dispatch.md:84-106`, `templates/output-format.md:1-75`, `README.md`, tests listed above
- Local runs: V1/V2 parse/select reproductions; mutants A/B/C; baseline suite 3311 passed
- `git log -S` / `git tag --contains` for bug-C history

### Secondary / Tertiary
- None. No web sources were needed: this phase is entirely internal to the repo.

## Metadata

**Confidence breakdown:**
- Reproductions / code facts: HIGH (run or read directly)
- Per-reason retry semantics: HIGH for score.py paths; MEDIUM for the "unchanged tree dispatches nothing" claim (prose-verified, not run live)
- Helper recommendation / plan split: MEDIUM (design judgment)

**Research date:** 2026-10-27
**Valid until:** until any of `batch_card.py`, `batch_parse.py`, `50-fix-loop.md`, `90-finalize.md`, `40-render.md`, `score.py` change (fast-moving branch; re-check line numbers before planning edits)
