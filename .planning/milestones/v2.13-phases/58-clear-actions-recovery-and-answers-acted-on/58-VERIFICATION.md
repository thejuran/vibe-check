---
phase: 58-clear-actions-recovery-and-answers-acted-on
verified: 2026-10-28T18:17:36Z
status: human_needed
score: 5/5 roadmap success criteria verified by static evidence (regression tests, mutants, fresh-shell fence walks); 1 inherent human-verification item (live-model ref extraction) keeps status at human_needed rather than passed
has_blocking_gaps: false
overrides_applied: 0
gaps: []
deferred:
  - truth: "Reviewer's safer title-match design (act only when the best row holds ALL non-filler words, else offer a one-click choice) and wordier plain-English title phrasings resolving without a follow-up (WR-02)"
    addressed_in: "Backlog 999.26 (not yet scheduled to a phase)"
    evidence: "ROADMAP.md §999.26: \"Plain-English title references: wordier phrasings ask (Phase 58 D-23 known limits) ... Not scheduled.\" Owner ruling D-23 explicitly re-opens WR-02 and the reviewer's safer design as known limits, not phase gaps."
  - truth: "Finalize's $BLOBFILE shell-variable-across-Bash-calls fragility"
    addressed_in: "Backlog 999.25 (not yet scheduled to a phase)"
    evidence: "ROADMAP.md §999.25: predates Phase 58, parked under D-22, \"Not scheduled.\" Explicitly out of this phase's must-haves per the task brief."
human_verification:
  - test: "Run `/review` or `/deep-review` against a small real repo until a fix-loop or Finalize decision card appears with several rows. Answer it in genuine plain English that mixes a title reference, a counted \"the rest\" group, and a close-out request (e.g. the iPlayarr-style \"fix the X issue, then dismiss the other N and close out\"), typed into Other."
    expected: "Claude reads the card, writes the owner's references into a refs document (not the grammar) in its own words from the actual answer text, resolves them to the correct rows via `batch_card.py resolve`, prints \"Read your answer as: <grammar> — reason: ...\", and continues the fix/dismiss/close-out workflow without re-showing the same card. A genuinely ambiguous or incomplete answer produces exactly one short follow-up naming only the unclear piece, never the full card again."
    why_human: "Every mechanism downstream of the refs document (the strict title matcher, the resolver's one/none/many/count_mismatch/count_needed statuses, the parser gate, the carrier mechanism, the recovery-pairs table) is proven by unit tests, real-file mutants and fresh-shell fence walks in this verification and in 58-REPRO.md. What none of that evidence can show is whether Claude, reading a live card and a real free-text answer in an actual session, correctly extracts the structured references the prose instructs it to write. 58-REPRO.md records this explicitly: \"Not verified: the model's own extraction of refs from free text in a live session (D-15).\" The owner's D-15 ruling scoped a live/paid run out of this phase (it needs a separately approved, priced proposal), so this is not a defect — it is the one part of the goal that only a live session can confirm."
---

# Phase 58: Clear actions, recovery and answers acted on — Verification Report

**Phase Goal:** The owner can tell what each action does and what to do after an inconclusive re-check, and a clear plain-English answer to a decision card is carried out instead of being asked again (999.13 subset)
**Verified:** 2026-10-28T18:17:36Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Preliminary note: ROADMAP.md's "§Phase 58" section no longer exists as a header

`.planning/ROADMAP.md` HEAD (`0e61169`) has no `### Phase 58` heading — a `docs(58)` commit (`7a57aa7ebc`) deleted the Phase 56/57/58 detail blocks when condensing completed phases to one-line bullets, but left Phase 58's own `Goal` / `Depends on` / `Requirements` / `Success Criteria` text out, while its `Plans` list (58-01..58-09) ended up nested, confusingly, under the surviving `### Phase 56` heading. The 5 numbered success criteria the task brief and REQUIREMENTS.md both reference still exist verbatim in git history (commit `786742bd6e0a730d429f5320c188c90696cdb209^`) and match the phase goal and requirement IDs given in this task and in `58-CONTEXT.md`. I verified against that last-known-good text, reproduced below, and flag the ROADMAP.md structural break itself as a documentation-hygiene finding (see Anti-Patterns) — it does not change any functional truth below.

> 1. The "Fix all" label states what it actually does, and the card says which findings need individual decisions; a test locks the card text to the behavior
> 2. After an inconclusive re-check, the output states what happens next run and what the owner can do now, with no automatic closure and no new manual; existing recovery guidance and rejection/orphan explanations are reconciled to match actual behavior
> 3. An unambiguous plain-English answer to a decision card (e.g. "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out" on the eight-row card) is translated into that card's validated grammar — `fix 5; dismiss 1,2,3,4,6,7,8` with the reason preserved — and the fix/dismiss/close-out workflow continues without re-showing the card (regression test)
> 4. When a reference or reason is ambiguous or missing, or the card is stale, only the missing detail is asked — no guessing, no broadened decision, no full re-show (regression test)
> 5. Whether finalize `fix N` still re-asks Apply/Skip (bug C) has a recorded verdict on current code; if it reproduces, the decided row proceeds to fixing without re-asking and a regression fixture covers it; if not, that is recorded and not filed

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP §Phase 58 SC / REQ ID) | Status | Evidence |
|---|------|--------|----------|
| 1 | SC-1 / RECV-01: "Fix all" label states what it does; excluded NV rows named by number; text==behavior locked by test | ✓ VERIFIED | `batch_card.py` `rows`/`_bulk_fix_text` (helper lines 646-676) emits `nv_rows` + `bulk_fix_text` from the single `carry_state.NV_BAND` literal `select` uses. `90-finalize.md:122,131` and `50-fix-loop.md:75,80` render option text as `{{bulk_fix_text}}` verbatim, "this file never computes that set." Independently confirmed: `grep -c '{{bulk_fix_text}}'` = 1 in each card file; `pytest scripts/test_card_scope.py` → 15 passed (I ran this myself, not just read the SUMMARY). |
| 2 | SC-2 / RECV-02: inconclusive re-check states "what happens next run" + "what you can do now"; no automatic closure, no new manual; recovery/rejection/orphan text matches behavior | ✓ VERIFIED | `score.py` defines exactly 12 `_R_CF_*`/`_R_IR_*` reason constants (I grepped them myself); `40-render.md`'s "Recovery pairs (D-13)" table has exactly 12 rows, one `Next run:` / `You can:` pair per literal reason, "retried" only on the 2 reasons the code actually retries. `grep -c 'run /deep-review'` = 0 across `40-render.md`, `output-format.md` and both card files (I ran this). README.md:337 reconciled to "re-checked automatically on every later run that reviews changes" (no more "gets **one** automatic" claim — I grepped for it, 0 hits). |
| 3 | SC-3 / ANSR-01: unambiguous plain-English answer → translated into the card's grammar, reason preserved, workflow continues, no re-show | ✓ VERIFIED (mechanism); see human-verification note | I independently ran `batch_card.resolve_refs()` against the real `iplayarr_rows()` fixture with the exact owner refs from the incident ("fix the Browse recovery issue, then dismiss the 7 fixed rows and close out"): result was `{"ok": true, "grammar": "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: \"dismiss the 7 fixed rows\")", "close_out": true}` — the exact mapping the bug report demands. `50-fix-loop.md:172` / `90-finalize.md` carry the "Translate the answer (D-01)" paragraph → resolve → same parse fence → `Read your answer as:` echo → act, with "re-show the SAME card" removed (`grep -ci "re-show the same card"` = 0 in both files, confirmed myself). The parser remains the only gate (unchanged `batch_parse.py`, verified empty diff since `24dccdc`). |
| 4 | SC-4 / ANSR-02: ambiguous/missing/stale reference → only the missing detail asked, no guessing/broadening, no full re-show | ✓ VERIFIED (mechanism); see human-verification note | Independently ran the CR-01 adversarial sentence ("fix the option list on the browse page, then dismiss the other 7 fixed rows and close out") through the real `resolve_refs()`: result `ok: false`, the fix-title ref resolves to status `none` with candidates `[#5 Browse recovery…, #4 Gate only the option lists…]` — it asks instead of silently dismissing the row the owner meant to fix. `50-fix-loop.md:208` "Ask only what is missing (D-05, D-06)" holds the whole answer, asks one question per gap, and `:216` bounds it to one follow-up (D-08) before the full-card fallback. Stale-card remap (D-07) binds only to a `CARDROWSFILE=`-printed path; `REASON_PRIOR_SUBSET` refuses a fix-subset file as a prior card (confirmed in code at `batch_card.py:134,1184`). |
| 5 | SC-5 / ANSR-03: bug C (`fix N` re-asking Apply/Skip) has a recorded verdict | ✓ VERIFIED | `50-fix-loop.md:35` still reads "go straight to **Step B** — ask NO AskUserQuestion: the owner already chose these rows at Finalize (D-06)" for a Finalize-routed subset. `git log -S'ask NO AskUserQuestion' -- 50-fix-loop.md` → `46d78e3` (2026-10-09, shipped in v2.12, `git tag --contains` confirms). I ran `pytest scripts/test_fix_loop_card.py -k subset -v` myself: 11 passed, including the no-card lock and its mutant-trip tests. Verdict "does not reproduce — fixed by 46d78e3" is accurate and nothing was filed, matching the owner's D-15 ruling. |

**Score:** 5/5 ROADMAP success criteria verified by static/mechanical evidence. One cross-cutting human-verification item (below) applies to truths 3 and 4's live-model component, so overall phase status is `human_needed`, not `passed`.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Reviewer's safer title-match design + WR-02 wordier phrasings resolving without a follow-up | Backlog 999.26 | ROADMAP.md §999.26, owner ruling D-23: explicit known limit, "Not scheduled" |
| 2 | Finalize `$BLOBFILE` cross-Bash-call shell variable fragility | Backlog 999.25 | ROADMAP.md §999.25, owner ruling D-22: predates Phase 58, "Not scheduled" |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/batch_card.py` `resolve_refs()` | Maps owner references → rows, builds grammar, dry-runs `parse` | ✓ VERIFIED | Read in full (lines 913-1223); independently executed against real fixtures (iPlayarr V1 case and CR-01 adversarial case) with results matching the documented fix exactly |
| `plugins/vibe-check/scripts/batch_card.py` `_match_title()` | Strict all-non-filler-words-required rule (D-23 rollback of the 58-19 best-unique pick) | ✓ VERIFIED | Code at lines 968-979 implements `set(...).issuperset(wanted)`, no `_TITLE_MIN_MATCH` constant present (confirmed removed via `git show 817c9f9`); `pytest -k CR01` → 5 passed, 2 subtests, run by me |
| `plugins/vibe-check/scripts/batch_card.py` `suggest()` | Bottom-line answer trimmed to fix(any)/dismiss-defer(medium-only) (D-19) | ✓ VERIFIED | Lines 1229-1260+; `pytest scripts/test_bottom_line_suggest.py` → 27 passed, run by me |
| `plugins/vibe-check/phases/review/50-fix-loop.md` | Translate/resolve/ask-only-the-gap/D-07/D-08/carrier/bug-C-lock prose | ✓ VERIFIED | Read in full; strict-rule wording present, best-match residue = 0 occurrences, bug-C bullet intact at line 35 |
| `plugins/vibe-check/phases/shared/90-finalize.md` | Finalize twin of the above + accurate Q1/option text + NV stop text | ✓ VERIFIED | Read in full; `{{bulk_fix_text}}`, `{{V}} needs-verification`, strict-rule wording all present |
| `plugins/vibe-check/scripts/score.py` reason constants | 12 `verdict:` literals, one per recovery-pair row | ✓ VERIFIED | Grepped directly: 5 `_R_CF_*` + 7 `_R_IR_*` = 12, matching the 12-row table |
| `plugins/vibe-check/phases/review/40-render.md` | Per-reason Recovery pairs (D-13) table | ✓ VERIFIED | Table present with 12 rows, each literal reason matched verbatim against score.py |
| `plugins/vibe-check/templates/output-format.md` + `README.md` | NV suffix and recovery wording reconciled, no stray "/deep-review" or "one automatic" claims | ✓ VERIFIED | Grepped directly: 0 hits for both stale phrases |
| `plugins/vibe-check/phases/review/00-scope.md` | `--close-out-after-rerun` whole-token carrier (D-17), prints `CLOSE_OUT_AFTER_RERUN=<0|1>` | ✓ VERIFIED | Fence walked by me in both `/bin/bash` and `/bin/zsh`: `CLOSE_OUT_AFTER_RERUN=1`, `FINALIZE_MODE=0`, `SCOPE_ARGS=[src/foo]` for `ARGUMENTS="src/foo --close-out-after-rerun"` |
| `plugins/vibe-check/scripts/test_answer_resolve.py`, `test_card_scope.py`, `test_recovery_pairs.py`, `test_bottom_line_suggest.py`, `test_scope_args.py`, `test_fix_loop_card.py`, `test_finalize_card.py` | Regression + mutant coverage for all of the above | ✓ VERIFIED | Ran directly: `pytest scripts/test_card_scope.py scripts/test_recovery_pairs.py scripts/test_answer_resolve.py scripts/test_bottom_line_suggest.py scripts/test_scope_args.py` → 194 passed; full suite `pytest -q` (from `plugins/vibe-check`) → **3588 passed, 4757 subtests passed, 0 failed** — matches 58-REPRO.md's final-round gate exactly |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| Owner's typed-Other text | `$REFSFILE` refs document | "Translate the answer (D-01)" paragraph (prose instruction, not executable) | ✓ WIRED (prose-level); UNCERTAIN (live model behavior) | Prose correctly instructs the translation shape; cannot verify the model follows it without a live session (see Human Verification) |
| `$REFSFILE` | `resolve_refs()` | `batch_card.py resolve --rows ... --answer ...` CLI | ✓ WIRED | Ran the CLI-equivalent function directly against real fixtures; output matches documented fix exactly |
| `resolve_refs()` grammar | `parse()` | dry-run inside `resolve_refs`, then the same parse fence the owner's grammar answers use | ✓ WIRED | `resolve_refs` calls `parse(rows_doc, {"q1": grammar, "q2": None})` (line 1212) — same function, same gate, confirmed by reading and by the `test_same_gate_as_the_v1_grammar` test passing |
| `parse()` accepted grammar | fix/dismiss/defer workflow + close-out | `echo_text`, `fix_targets`, `carry_state.py record-decisions`, Rerun carrier | ✓ WIRED | Fence-walked the carrier (`CLOSE_OUT_AFTER_RERUN=1`) myself in bash and zsh; `TestCarrierRoundTrip` (4 passed) and `TestSubsetDispatchWalk` (4 passed) independently re-run by me |
| `score.py` `verdict: ...` reason | `40-render.md` Recovery pairs table | Literal string lookup | ✓ WIRED | All 12 reasons match 1:1, confirmed by direct comparison of grep output against the table |
| `batch_card.py rows` → `nv_rows`/`bulk_fix_text` | Card option text (`50-fix-loop.md`, `90-finalize.md`) | `{{bulk_fix_text}}` template substitution, "this file never computes that set" | ✓ WIRED | Confirmed both the producer (helper) and the consumer (template placeholder) exist and the prose explicitly forbids re-deriving the set in the card file |

### Data-Flow Trace (Level 4)

This phase is prose/CLI-driven rather than UI-rendered, so the equivalent trace is: does each displayed/templated value originate from a real computation rather than a hardcoded or guessed string?

| Displayed value | Source | Produces Real Data | Status |
|---|---|---|---|
| `{{bulk_fix_text}}` (Fix all / Apply all option text) | `batch_card.py _bulk_fix_text()` reading live `rows_doc` bands | Yes — derived from `carry_state.NV_BAND` band membership of the actual rows on the card | ✓ FLOWING |
| `Next run: / You can:` recovery pair | Literal lookup of the row's own `reason` string against the Recovery pairs table | Yes — the row's `reason` field is the actual `score.py` output for that finding | ✓ FLOWING |
| `Read your answer as: <grammar>` echo | `resolve_refs()`'s `grammar` field, built from the owner's actual parsed refs | Yes — not a template, built from the specific rows the owner named | ✓ FLOWING |
| `Bottom line suggests: <grammar>` | `batch_card.py suggest()` parsing the actual rendered Bottom line text for this pass | Yes — gated by "the `suggest` fence below exited 0 for this card"; a refusal removes the file rather than guessing | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full regression suite (plugin) | `cd plugins/vibe-check && pytest -q` | `3588 passed, 4757 subtests passed in 203.18s`, 0 failed | ✓ PASS |
| Golden digest unchanged | `score.stable_hash('a.py','  x=1','title') == test_score.GOLDEN_DIGEST` | `True` | ✓ PASS |
| `score.py`/`batch_parse.py` frozen since Phase 56 | `git diff --stat 24dccdc..HEAD -- scripts/score.py scripts/batch_parse.py` | empty | ✓ PASS |
| V1 iPlayarr regression resolves correctly | `batch_card.resolve_refs()` on real `iplayarr_rows()` fixture with the owner's exact words | `ok: true`, `grammar: "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: \"dismiss the 7 fixed rows\")"`, `close_out: true` | ✓ PASS |
| CR-01 adversarial sentence asks instead of mis-acting | Same function, adversarial title text ("the option list on the browse page") | `ok: false`, status `none`, candidates include the actually-meant row (#4) | ✓ PASS |
| `--close-out-after-rerun` carrier fence, both shells | `env ARGUMENTS="src/foo --close-out-after-rerun" /bin/bash -s` and `/bin/zsh -s` on the real `00-scope.md` fence text | `CLOSE_OUT_AFTER_RERUN=1`, `FINALIZE_MODE=0`, `SCOPE_ARGS=[src/foo]` in both shells | ✓ PASS |
| Bug-C no-card lock | `pytest scripts/test_fix_loop_card.py -k subset -v` | `11 passed` | ✓ PASS |
| Debt-marker scan on touched files | `grep -nE "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER"` on the 8 core touched files | Only `mktemp ... vc.XXXXXX` template literals and `_NV_PLACEHOLDERS` (a legitimate constant name); no real debt markers | ✓ PASS |
| Live model's own ref-extraction from free text | — (no runnable entry point without a live session) | — | ? SKIP — routed to Human Verification |

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention exists in this repository and neither the PLAN/SUMMARY files nor the ROADMAP success criteria mention probes for this phase. Step 7c: **SKIPPED (no probes declared or found)**.

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| RECV-01 | 58-01, 58-04, 58-05, 58-06, 58-18, 58-22 | "Fix all" label states what it does; NV exclusions named by number | ✓ SATISFIED | `bulk_fix_text`/`nv_rows` wiring verified directly; `test_card_scope.py` 15 passed |
| RECV-02 | 58-02, 58-05, 58-06, 58-12, 58-18, 58-22 | Inconclusive re-check shows bounded recovery; no automatic closure/new manual; guidance reconciled | ✓ SATISFIED | 12-row Recovery pairs table verified 1:1 against `score.py` reasons; README/output-format grepped clean |
| ANSR-01 | 58-03, 58-04..58-23 (13 plans) | Unambiguous plain-English answer translated and acted on without re-show | ✓ SATISFIED (mechanism); live-model extraction unverified | V1 regression case executed directly with correct result |
| ANSR-02 | 58-03, 58-06..58-23 (14 plans) | Ambiguous/missing/stale → only the gap asked, no guessing/broadening/full re-show | ✓ SATISFIED (mechanism); live-model extraction unverified | CR-01 adversarial case executed directly; asked rather than mis-acted |
| ANSR-03 | 58-04, 58-06, 58-09, 58-18, 58-22 | Bug C verdict recorded on current code | ✓ SATISFIED | Git-history trace + lock test (11 passed) re-run directly |

**Orphaned requirements check:** `grep -E "Phase 58" .planning/REQUIREMENTS.md` returns only the 5 IDs above under the Traceability table; every PLAN's `requirements:` frontmatter across all 23 plans draws only from this same set of 5 IDs (confirmed by grepping all 23 `58-*-PLAN.md` files). **No orphaned requirements.**

Note: `.planning/REQUIREMENTS.md`'s own checkboxes for RECV-01/02 and ANSR-01/02/03 are still unchecked (`[ ]`) and its Traceability table still reads "Pending" — this is the expected pre-verification state (these get flipped as part of phase close-out, not before), not a functional gap.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `plugins/vibe-check/scripts/batch_card.py` | 1166-1168 (`resolve_refs()` docstring) | Stale comment: "A title reference names the single best-matching row (see `_match_title`); a tie is `many` ... and a weak or absent match is `none`" — this describes the 58-19 best-unique-pick behavior that D-23 (commit `817c9f9`) rolled back. `_match_title`'s OWN docstring was correctly updated to the strict all-words rule; this sentence inside the caller's docstring was missed. | ℹ️ Info | Misleading to a future reader of the code (not owner-facing text, no behavioral effect — the function it describes was already fixed) |
| `.planning/ROADMAP.md` | 83-89 (Progress table) | Row `58. Clear actions, recovery and answers acted on \| 0/TBD \| Not started \| -` is stale; 23 plans have in fact executed | ℹ️ Info | Documentation bookkeeping only; does not affect delivered behavior. Expected to be updated as part of phase close-out. |
| `.planning/ROADMAP.md` | n/a (missing `### Phase 58` header) | The Phase 58 Goal/Depends-on/Requirements/Success-Criteria block was deleted by commit `7a57aa7` when condensing completed phases, and its Plans list is now nested, confusingly, under the surviving `### Phase 56` heading | ⚠️ Warning (doc hygiene, not a phase-goal blocker) | A future reader of ROADMAP.md alone cannot find Phase 58's success criteria; they survive only in git history and in `58-CONTEXT.md`/`REQUIREMENTS.md`. Recommend restoring the Phase 58 header block (or moving the 58-0X plan list out from under Phase 56) in a documentation pass. |

### Human Verification Required

### 1. Live plain-English answer to a real decision card

**Test:** Run `/review` or `/deep-review` against a small real repo with several findings until a fix-loop or Finalize decision card appears. Type a genuine plain-English answer into Other that combines a title/row reference, an uncounted or counted bulk group, and a close-out request — ideally the exact incident shape: "fix the &lt;X&gt; issue, then dismiss the other N and close out."

**Expected:** Claude reads the rendered card, writes the owner's references into the refs document itself (not pre-written grammar), the helper resolves them to the correct rows, prints "Read your answer as: &lt;grammar&gt; — reason: ...", and the fix/dismiss/close-out workflow proceeds without re-showing the same card. If the reference is genuinely ambiguous (e.g. it could match more than one finding, or omits a required count for a serious-band group), exactly one short follow-up names only the unclear piece and nothing is recorded until it is resolved.

**Why human:** Every downstream mechanism — the strict title matcher, the resolver's status logic, the parser gate, the carrier that survives the Rerun, the recovery-pairs table — is proven here and in `58-REPRO.md` by unit tests, real-file mutants and fresh-shell fence walks (all independently re-run as part of this verification). What none of that can demonstrate is whether Claude, in an actual interactive session, correctly extracts the owner's intended references from truly free-form text and writes them into the refs document as instructed. `58-REPRO.md` states this directly: "Not verified: the model's own extraction of refs from free text in a live session (D-15)." The owner's D-15 ruling explicitly scoped a live/paid run out of this phase — a separate bounded, priced proposal is required for one — so this is not a reproduced defect, it is the one part of the stated goal that inherently requires a live session to confirm.

## Gaps Summary

No blocking gaps. All 5 ROADMAP success criteria (RECV-01, RECV-02, ANSR-01, ANSR-02, ANSR-03) are backed by code that exists, is substantive, is wired end-to-end, and passes an independently re-run regression suite (3588 passed, 0 failed) plus mutation evidence and fresh-shell fence walks that I executed myself rather than only reading from SUMMARY.md/58-REPRO.md claims. The one critical finding surfaced by the final review round (CR-01: the 58-19 best-unique title matcher could silently act on the wrong row) was rolled back in commit `817c9f9` under owner ruling D-23, and I independently reproduced both the adversarial failure case (asks safely under current code) and the original regression fixture (still resolves correctly) using the real `resolve_refs()` function.

Status is `human_needed` rather than `passed` for exactly one reason: ROADMAP success criteria 3 and 4 (ANSR-01/ANSR-02) describe behavior of a live model reading a card and writing structured references from free text, and that specific step cannot be verified without an interactive session — which the owner's own D-15 ruling explicitly deferred out of this phase's budget. This is a known, accepted, and correctly-documented limitation of static verification, not a code defect; the recommended action is the human UAT test above, at the owner's convenience, rather than a new plan or backlog item.

Two items are deliberately parked and are NOT gaps, per the owner's own backlog entries: 999.25 ($BLOBFILE shell-variable fragility, predates Phase 58, D-22) and 999.26 (wordier plain-English title phrasings still ask rather than act, and the reviewer's safer matching design, both re-opened by the CR-01 rollback under D-23). Two informational documentation findings (a stale docstring sentence in `batch_card.py`, and ROADMAP.md's missing Phase 58 header / stale Progress row) are noted for cleanup but do not block the phase goal.

---

*Verified: 2026-10-28T18:17:36Z*
*Verifier: Claude (bm-verifier)*
