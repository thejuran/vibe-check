# Phase 58 — Reproduction verdicts

- **Phase:** 58 — Clear actions, recovery and answers acted on
- **Date:** 2026-10-27
- **HEAD when recorded:** `13492b7` (branch `feat/v2.13-phase-58`; last code commit 75bb831, 58-09)
- **Scope of evidence:** no live or paid run was performed (D-15). Every verdict below is a local CLI run, a local pytest run, a git-history query or a static trace of the prose. A live interactive run of the cards with a model was not done; nothing here claims one.
- **Rule applied:** reproduce first (D-14). A failure that reproduced is mapped to the plan that fixed it. A path that does not reproduce is recorded and dropped.

Sources: 58-RESEARCH.md §"Reproduction verdicts" (runs on HEAD `1211605`, before any phase-58 code) and the SUMMARYs of 58-01, 58-02, 58-03, 58-04, 58-05, 58-07, 58-08 and 58-09 (RED outputs, mutant tables, the 58-08 carrier round-trip and the 58-09 static trace). Commands marked **live (58-06)** were re-run for this document on `13492b7`.

---

## V1 — Repeated-card loop on a clear plain-English answer (ANSR-01 / ANSR-02)

**Verdict: REPRODUCED before the phase → fixed by 58-03, 58-04, 58-05, 58-07, 58-08, 58-09.**

**Failure as the owner saw it.** The owner answered the eight-row iPlayarr fix-loop card in plain English ("fix the Browse recovery one, dismiss the other 7 — they're fixed, then close out"). The strict parser refused it, and the prose turned every refusal into "re-show the SAME card once" (`50-fix-loop.md:102`, `:144`; Finalize twin `90-finalize.md:139`, `:174`). The same card came back for an answer whose meaning was clear.

**Fixture.** The eight-row iPlayarr rows doc, `test_answer_resolve.iplayarr_rows()` (58-03): rows 1-8, bands 3 critical / 4 warning / 1 medium. Row 5 is "Browse recovery leaves a stale cursor after a failed page load", and no other title contains "browse". Rows 1-4, 6 and 8 carry the real iPlayarr titles and hashes from `fixtures/iplayarr45-six-row-state.json`.

**Commands and output — live (58-06), run from `plugins/vibe-check/scripts` against that fixture written to a scratch dir:**

```
$ python3 batch_card.py parse --rows rows8.json --answer ans_plain.json
  # q1 = "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out"
exit 2
refused: answer does not match the grammar

$ python3 batch_card.py parse --rows rows8.json --answer ans_gram.json
  # q1 = "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed in review-pass commits, verified on recheck"
exit 0
fix_targets: 1 decisions: 7
fix: #5 src/browse/recovery.ts:118
dismiss: #1 src/endpoints/sabnzbd/AddFileEndpoint.ts:204, #2 src/service/browse/ArrDiscoveryHandoffService.ts:201, #3 src/utils/integrationDeadline.ts:60, #4 frontend/src/views/BrowseProgrammePage.vue:406, #6 src/service/arr/V3ArrService.ts:412, #7 src/relay/budget.ts:33, #8 src/facade/arrFacade.ts:80
Reason: fixed in review-pass commits, verified on recheck

$ python3 batch_card.py parse --rows rows8.json --answer ans_noreason.json
  # q1 = "fix 5; dismiss 1,2,3,4,6,7,8"
exit 2
refused: dismiss/defer needs a reason

$ python3 batch_card.py resolve --rows rows8.json --answer refs.json
  # refs = [fix title "Browse recovery", dismiss marker "remaining" count 7], reason "fixed (owner: \"dismiss the 7 fixed rows\")", close_out true
exit 0
{"ok": true, "stale": false, "needs_reason": false, "close_out": true,
 "refs": [{"status": "one", "rows": [5], "candidates": []}, {"status": "one", "rows": [1, 2, 3, 4, 6, 7, 8], "candidates": []}],
 "verbs": {"fix": [5], "dismiss": [1, 2, 3, 4, 6, 7, 8], "defer": []},
 "grammar": "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: \"dismiss the 7 fixed rows\")", "parse_reason": null}
```

The parser is deliberately unchanged: it still refuses the plain-English text (exit 2) and still accepts the grammar `fix 5; dismiss 1,2,3,4,6,7,8` with a reason. That is the D-01 design: the parser stays the only gate. What changed is what the prose does with the refusal.

**Before the phase (RESEARCH, HEAD 1211605).** The same three parse results; the prose then re-showed the same card on any refusal. There was no `resolve`, and the grammar had no way to carry "close out".

**After (GREEN tests and prose):**
- 58-03: `batch_card.py resolve` maps the owner's refs to rows and builds the grammar; `test_answer_resolve.py` (`test_eight_row_grammar`, `test_eight_row_no_broadening`, `test_same_gate_as_the_v1_grammar`, `test_cli_eight_row`, count-mismatch / ambiguity / stale / conflict tests; mutants m1-m5).
- 58-04: fix-loop **Translate the answer (D-01)** → resolve → grammar copy → the SAME parse fence → `Read your answer as:` echo → act; "re-show the SAME card" removed (`translate_path_problems`, mutants T1-T4). The 58-04 SUMMARY records a manual walk of the real fences on this fixture: no second card.
- 58-05: Finalize twin of the Translate paragraph (`TestPhase58Finalize`, mutants M3, M4, M10, M11).
- 58-07: the `--close-out-after-rerun` carrier in Phase 0 and both spines (`test_scope_args.py` M4-M7).
- 58-08: fix-loop **Ask only what is missing (D-05, D-06)**, the D-08 full-card fallback, the stale `--prior-rows` twin, the Rerun's one-shot marker; `TestCarrierRoundTrip` reads the prose's own re-entry string back through the real Phase 0 fence.
- 58-09: Finalize twin of the follow-up, stale and budget paragraphs (`TestPhase58FinalizeRouting`).

Not verified: the model's own extraction of refs from free text in a live session (D-15).

---

## V2 — "Fix all" / "Apply all & rerun" label vs behavior (RECV-01, K2)

**Verdict: REPRODUCED before the phase (Finalize "Fix all" label false whenever a Needs-verification row exists) → fixed by 58-01, 58-04, 58-05.**

**Failure as the owner saw it.** Finalize option 3 said "Send every row, any band, to the fix-loop card" (`90-finalize.md:117`), but `_rest_bands_for("fix")` reaches only critical / warning / medium, so Needs-verification rows were left undecided. The fix-loop "Apply all & rerun" said only "(Needs-verification rows are not applied — confirm them by number.)" and named no rows.

**Fixture.** A 5-row NV-mixed rows doc. RESEARCH used rows 1 critical, 2 warning, 3 NV, 4 medium, 5 NV. 58-01 used `nv_card_state()`, which ranks the two NV rows as #3 and #4 (NV ranks before medium); the tests pin #3, #4 from the real fixture.

**Before (RESEARCH run, HEAD 1211605):**

| Path | Rows actually sent | NV rows |
|---|---|---|
| Finalize Q1 **Fix all** (`_BUTTON_TEXT["Fix all"] = "fix rest"`) | 1, 2, 4 | 3, 5 left `undecided` |
| Fix-loop **Apply all & rerun**, ordinary card (`select(rows, {"all": true}, subset=False)`) | 1, 2, 4 | 3, 5 not sent |
| Fix-loop subset card (Finalize-routed) | 1-5 | sent |

58-01 RED reproduced the same gap on the helper: `excluded_by_behavior == [3, 4]` on both cards, with `bulk_fix_text` / `nv_rows` absent from the rows doc (`17 failed, 7 passed`).

**After:**
- 58-01: `batch_card.py rows` emits `nv_rows` and `bulk_fix_text` from the same `carry_state.NV_BAND` literal `select` uses; `test_card_scope.py` locks text == behavior (real-file mutants m1-m5 all trip).
- 58-04: fix-loop option 1 is `{{bulk_fix_text}}` copied from the rows doc (mutant N1).
- 58-05: Finalize option 3 is `{{bulk_fix_text}}`; header counts `{{V}} needs-verification`; Dismiss/Defer all and Mixed… descriptions match `batch_parse` (mutants M1, M2, M9).

Current code (live grep, 58-06): `Send every row, any band` 0; `lowest band` 0; `{{V}} needs-verification` 1; `{{bulk_fix_text}}` 1 in each card file.

---

## V3 — Recovery tail vs each reason (RECV-02)

**Verdict: REPRODUCED before the phase (narrower than CONTEXT stated) → fixed by 58-02.**

**Failure as the owner saw it.** A not-yet-confirmed fix row ended with the shared tail "retried on the next run that reviews changes; or run /deep-review…; or dismiss it by number". On an unchanged tree no reviewer is dispatched under either command, so "/deep-review" could not help; a NO_TRIGGER row cannot close on the next run at all; confirmed-fix rows had no next-step line.

**Fixture.** The 12 reason constants in `score.py` (6 `_R_IR_*` + 5 `_R_CF_*` + `_R_IR_NV_NO_CHANGE`; RESEARCH V3 table), collected by `vars(score)` in `test_recovery_pairs.py::TestReasonInventory` (`3 passed` at RED, before any prose existed).

**Before (RESEARCH, file read):** `40-render.md:45` special-cased STILL / SETTLED / NV_NO_CHANGE; the shared tail went on the other four `fix not` reasons; `confirmed fix` rows got only `Fix not yet verified: <reason>`. 58-02 RED: `15 failed, 7 passed` (marker missing, "still says: run /deep-review" in 40-render.md and output-format.md, README lacking "every later run that reviews changes").

**After (58-02):** one **Recovery pairs (D-13).** table in `40-render.md` with a `Next run:` / `You can:` pair for every reason; retry wording only for the six reasons the code re-asks; no pair sends the owner to /deep-review; NV suffix identical in `40-render.md` and `templates/output-format.md`; README reconciled. Locked by `test_recovery_pairs.py` (real-file mutants a-l all trip, including (c) a synthetic reason added to `score.py`, reverted).

Current code (live grep, 58-06): table rows `^| \`verdict: ` = 12; `run /deep-review` 0 across 40-render.md / output-format.md / the card files; README `one** automatic` 0.

---

## V4 — Bug C: Finalize `fix N` re-asks Apply/Skip (ANSR-03)

**Verdict: does not reproduce on current code — fixed by 46d78e3 (v2.12).**

Filed: nothing (owner ruling D-15/D-17 research verdicts).

**Repro steps (ROADMAP Phase 58, "Check first", owner decision 2026-10-21).** Deep review leaves a warning → fix loop **Stop here…** → **Close out** → Finalize answer `fix N; defer M`. The reported failure: the subset routed into the fix-loop card, which asked Apply/Skip again for a row the owner already decided.

**Static trace on the final tree (from the 58-09 SUMMARY, at 75bb831; line numbers for both files):**

1. `90-finalize.md:118` — Mixed… tells the owner to type the mix in Other; Q1 text plus a Q2 pick come back.
2. `90-finalize.md:153` — **Parse.** writes Q1 and Q2 verbatim to `$ANSWERFILE` with the Write tool.
3. `90-finalize.md:157` — the parse fence; a valid grammar exits 0, so no Translate or follow-up detour.
4. `90-finalize.md:210` / `:214` — **After the answer**: `echo_text` printed as message text before `50-fix-loop.md` is read; there is NO confirm card.
5. `90-finalize.md:215` / `:218`, `:251` — step 1: the `defer M` payload is recorded by `carry_state.py record-decisions`.
6. `90-finalize.md:225` / `:228` / `:229` — step 2: `fix_targets` copied file-to-file into `$SUBSETFILE`.
7. `90-finalize.md:235` — Read `50-fix-loop.md`, enter "The fix-loop card" with the literal subset path.
8. `50-fix-loop.md:18` — **Finalize routed a fix set here (D-10)**; subset fence `:20-28`.
9. `50-fix-loop.md:31` — "go straight to **Step B** — ask NO AskUserQuestion: the owner already chose these rows at Finalize (D-06)." (live grep on `13492b7`: still line 31)
10. `50-fix-loop.md:217` — **Step B — Apply fixes** runs on the owner's chosen rows. No AskUserQuestion between the Finalize answer and the fix.

**Git history — live (58-06):**

```
$ git log --oneline -S'ask NO AskUserQuestion' -- plugins/vibe-check/phases/review/50-fix-loop.md
46d78e3 feat(52-09): check git once before dispatch and skip the card for a Finalize fix set

$ git tag --contains 46d78e3
v2.12

$ git show -s --format='%h %ad %s' --date=iso 46d78e3
46d78e3 2026-10-09 23:26:10 -0400 feat(52-09): check git once before dispatch and skip the card for a Finalize fix set
```

Bug C was written up on 2026-10-09 against 2.11.x; the rule that prevents it landed the same evening and shipped in v2.12.

**Lock: `test_fix_loop_card.py` `subset_no_card_problems` (`:408`), mutants A / B / C.**

| Mutant | Before 58-04 (old lock) | After 58-04 (strengthened lock) |
|---|---|---|
| A: delete " — ask NO AskUserQuestion: the owner already chose these rows at Finalize (D-06)" | TRIPS (`test_subset_no_card` fails) | TRIPS (4 failed on the real file, mutant SA) |
| B: replace it with "then ask one AskUserQuestion (Apply / Skip) before Step B" | TRIPS (`test_subset_no_card` fails) | TRIPS (4 failed on the real file, mutant SB) |
| C: bullet intact; add "When Finalize routed a fix set, show the card below so the owner can Apply or Skip." before **Same-turn rule** | SURVIVES (RESEARCH: all 71 fix-loop tests and 437 card/parse/render tests passed; 58-04 re-confirmed by monkeypatching the HEAD-ad770bd lock body: `test_mutant_subset_off_bullet_instruction` failed with `[] == []`) | TRIPS (1 failed on the real file, mutant SC: `subset_no_card`) |

Live (58-06): `pytest scripts/test_fix_loop_card.py -k subset -v` → `7 passed, 100 deselected, 4 subtests passed`, including `test_subset_no_card`, `test_mutant_subset_a_no_ask_clause_deleted`, `test_mutant_subset_b_asks_apply_skip` and `test_mutant_subset_off_bullet_instruction`.

**Caveats handled in-phase (not a reproduction of bug C):** the lock gap (mutant C) was closed by 58-04; the residue sentences describing a "From your finalize answer:" block inside a card that is never shown (`50-fix-loop.md:64`, `90-finalize.md:145`) were removed by 58-04 (I-10) and 58-05 (I-11). Live grep: `From your finalize answer` 0.

---

## V5 — Inventory of text that disagreed with code (D-14)

| # | Where (pre-phase) | Statement | Disposition |
|---|---|---|---|
| I-1 | `90-finalize.md:117` | Fix all: "Send every row, any band, to the fix-loop card" | Fixed in 58-05 (option 3 = `{{bulk_fix_text}}`; mutant M1) |
| I-2 | `90-finalize.md:115-116` | Dismiss/Defer all: only critical/warning stay open | Fixed in 58-05 (NV rows named as staying open; `option_descriptions` lock) |
| I-3 | `90-finalize.md:118` | Mixed…: "`all` means every row of the lowest band" | Fixed in 58-05 (parser-true `all` wording; mutant M9) |
| I-4 | `90-finalize.md:113` | Q1 header omits NV rows from the breakdown | Fixed in 58-05 (`{{V}} needs-verification`, C + V + M = N; mutant M2) |
| I-5 | `90-finalize.md:53` | NV stop list: "re-checks it once" | Fixed in 58-05 (every later run while the repaired code is unchanged; mutant M5) |
| I-6 | `README.md:337` | "gets **one** automatic independent re-check" | Fixed in 58-02 (README reconciled; mutant f) |
| I-7 | `40-render.md:45` | shared tail on NO_REVIEWER / NO_ANSWER / SNAPSHOT / NO_TRIGGER | Fixed in 58-02 (per-reason Recovery pairs table; mutants a, b, d, e) |
| I-8 | `40-render.md:83` + `templates/output-format.md:70` | NV suffix "…or run /deep-review…" | Fixed in 58-02 (suffix identical in both files, no /deep-review; mutant g) |
| I-9 | `40-render.md:43` | `Fix not yet verified: <reason>` only | Fixed in 58-02 (a pair per confirmed-fix reason; mutant l) |
| I-10 | `50-fix-loop.md:64` | "From your finalize answer:" block in the card question | Fixed in 58-04 (block removed; mutant R1) |
| I-11 | `90-finalize.md:145` | echo appears "as that card's closing … block" | Fixed in 58-05 (echo printed as message text, the card is not shown; mutant M6) |
| I-12 | `50-fix-loop.md:73` | decision "holds until its own line is edited or its band changes" | Fixed in 58-04 (Phase 57 hold sentence; mutant H1) |
| I-13 | `50-fix-loop.md:102,144`; `90-finalize.md:139,143,174` | "re-show the SAME card" on refusal | Fixed in 58-04 (fix loop; mutants T1, G1), 58-05 (Finalize refusal; mutant M3) and 58-09 (Finalize budget; mutant M3) — follow-up/fallback rules from 58-08 and 58-09 |
| I-14 | `90-finalize.md:218-219`, `review-md-schema.md:66`, `batch_card.decisions_report` | orphan → `(finding no longer in the last pass)` + ` (superseded)` | Checked — consistent with code, no change: an orphan has no open last-pass record, so `_report_entry` sets `file` to null (`batch_card.py:1237`, status `orphan` at `:1264`), which is exactly the case the REVIEW.md rule renders (now `90-finalize.md:287-288`) |
| I-15 | `90-finalize.md:168-170` stop messages | "Finalize stays blocked — name each remaining … by number…" | Checked — consistent with code, no change: the messages follow the counts-and-gate re-run in step 3 (the `:167` re-run in the pre-phase file; now `90-finalize.md:236-239`) |

Current code (live grep, 58-06) for the removed text: `re-checks it once` 0, `holds until its own line is edited` 0, `re-show the SAME card` / `Re-show the SAME card` 0, `an unparseable answer` 0.

---

## What was not done

- No live run and no paid run was performed (D-15). The cards were not driven by a model in an interactive session; prose behavior is evidenced by locks, mutants, real-fence runs and static traces only.
- Nothing was filed in the backlog for bug C.

---

## Gap round (58-REVIEW.md)

The owner ruled on 2026-10-27 (58-CONTEXT.md, "Gap round") that every 58-REVIEW.md warning and info item is fixed before verification. Each one was reproduced first with a failing test and then mutant-checked. The rulings D-18, D-19 and D-20 settle the three set-aside items.

Every cell below comes from the closing plan's SUMMARY. In the commit column, the RED commit comes first and the GREEN commit second. A real-file mutant is an edit applied to the real plugin file, a run of the named tests, and then a revert. Each mutant listed failed at least one test, meaning it was killed. Gate numbers are in **Gap round gate** at the end of this file.

| Finding | Plan | Reproduced by (failing test + RED line) | Fixed by (commit) | Mutant(s) on the real file |
|---|---|---|---|---|
| WR-01 (a stale `close_out` in `$RESOLVEFILE` turns a later answer into a close-out) | 58-14 | `TestGapRoundFixLoop::test_answer_files_holds`, `test_close_out_source_holds`. RED at 5041f95: "Rerun/Close out/D-08 fallback do not clear answer files"; "Rerun lacks CLOSE_OUT_SOURCE and NEVER_STALE; Rerun and step 2 still read close_out from `$RESOLVEFILE`"; carry paragraph "still says 'none of which survive it'" | 163de79 → 2bac051 | L2 (Rerun `rm -f` deleted): 2 failed. L3 ("none of which survive it" restored): 2 failed. L5 ("When `close_out` was true in `$RESOLVEFILE`" restored): 2 failed |
| WR-02 (`$SUGGESTFILE` survives the Rerun; "bottom line" applies the previous pass's numbers) | 58-14, 58-16 | Fix loop: `test_answer_files_holds`. RED: "suggestion read from `$SUGGESTFILE` exists for this pass; typed bottom line not tied to the card shown". Finalize: `TestGapRoundFinalize::test_answer_files_holds`. RED at 6f41a9f: "no `rm -f` in step 2 / step 3 / D-08; Parse trusts any existing `$SUGGESTFILE`" | 163de79 → 2bac051; 2510f9c → 3bce0f4 | L2: 2 failed. L4 ("`$SUGGESTFILE` exists for this pass" restored): 3 failed. F2 (Finalize step 2 `rm -f` deleted): 1 failed. F3 ("`$SUGGESTFILE` exists for this card" restored): 2 failed |
| WR-03 (title matching: filler words block clear answers; in-word fragments match the wrong row) | 58-10 (helper); 58-15 / 58-17 (prose) | Helper: `TestGapRound::test_v1_verbatim_title_clause_resolves`, RED `AssertionError: False is not true`. `test_filler_words_do_not_block_match`, RED `Tuples differ: ('none', []) != ('one', [5])`. `test_fragment_inside_a_word_is_none`, RED `Tuples differ: ('one', [2]) != ('none', [])` (`port` matched "import"). Prose: `test_title_rule_holds` failed in both card files ("every TITLE_RULE needle missing; the unqualified `"text": "<the owner's words>"}` form still present"). 58-15 V1 walk with the owner's verbatim `fix the Browse recovery issue, then dismiss the 7 fixed rows and close out`: resolve `"ok": true`, grammar `fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: "dismiss the 7 fixed rows")`, parse `"ok": true`, no follow-up | b648294 → c3f401e (+ cfb1edd in-test mutants); 1e63a4c → 0911d07; 2e81b59 → 140219f | m6 (substring matching restored): 2 failed. m7 (filler not stripped): 5 failed. T5 (old `text` form, fix loop): 4 failed. M13 (same, Finalize): 4 failed |
| WR-04 (`ok:false` with every ref clear has no prose branch) | 58-10 (fixture); 58-15 / 58-17 (bullet) | Helper pin: `test_two_uncounted_remaining_is_ok_false_with_every_ref_clear` already passed at HEAD, as the plan allowed (ok false, every ref one/bulk, needs_reason false, `parse_reason == REASON_REST_TWICE`). Prose: `test_parse_refusal_branch_holds` failed in both card files ("Ask paragraph lacks the parser-refusal bullet") | b648294 (pin); 1e63a4c → 0911d07; 2e81b59 → 140219f | T6 (parser-refusal bullet deleted, fix loop): 2 failed. M14 (same, Finalize): 2 failed |
| WR-05 (stale re-map: `$PRIORROWSFILE` points at a path that is never printed) | 58-14, 58-16 | Fix loop: `test_stale_source_holds`. RED: "lacks all four source needles; still names 'that pass's `$ROWSFILE` path, used as is'; Rerun lacks 'keep this pass's `$ROWSFILE`'". Finalize: `test_stale_holds`, `test_stale_source_holds`. RED: "3 new needles missing; 'an earlier `--finalize`' and 'used as is' present" | 163de79 → 2bac051; 2510f9c → 3bce0f4 | L6 ("that pass's `$ROWSFILE` path, used as is" restored): 2 failed. F4 ("an earlier `--finalize` built a card" restored): 3 failed. F5 ("that card's `$ROWSFILE` path, used as is" restored): 3 failed |
| WR-06 (fences rely on `$RESOLVEFILE` across Bash calls but never print it) | 58-14, 58-16 | `test_printed_paths_holds` in both card files. RED: "unprinted ROWSFILE ×2, ANSWERFILE ×2, PARSEFILE, DECFILE, RESOLVEFILE, PAYLOADFILE; convention sentence appears 0 times" (fix loop); "ROWSFILE, ANSWERFILE, PARSEFILE, RESOLVEFILE, DECFILE unprinted" (Finalize). 58-14 fence walk, step F (variable form in a fresh shell): `bash: line 1: : No such file or directory` → "nothing was recorded". Steps C-E with printed literals: exit 0 | 163de79 → 2bac051; 2510f9c → 3bce0f4 | L1 (`printf 'RESOLVEFILE=%s'` deleted, fix loop): 2 failed. F1 (same, Finalize): 2 failed |
| IN-01 (template needs-recheck suffix rewords the recovery cell) | 58-12 | `TestReconciled::test_nv_suffix_in_both_files`, failing for both `40-render.md` and `output-format.md` (5 failed, 20 passed at RED). `NV_SUFFIX` literal replaced by `nv_suffix_from_table` | 37453ca → af6df2e | m (template suffix reverted to the shortened wording): 2 failed. o (table-cell parenthetical dropped): 3 failed |
| IN-02 (`Fix not yet verified:` line has no separator) | 58-12 | `TestReconciled::test_verified_line_names_its_separator` failed at RED | 37453ca → af6df2e | n (`then ` — ` and the pair` → `then the pair`): 2 failed |
| IN-03 (`changed` marker covers `joined` rows) | 58-10 | `test_changed_marker_excludes_joined`, RED `Lists differ: [1, 2, 3, 4] != [1, 3, 4]` | b648294 → c3f401e | m8 (`changed` → any truthy `stale`): 3 failed |
| IN-04 (`test_close_out_drops_the_marker` could not fail) | 58-13 | Before/after strip mutant (delete the normalizer's `--close-out-after-rerun` strip in the real `00-scope.md`). The OLD test **passed** (1 passed, 2 subtests), so it was decorative. The NEW test, which derives `${original_args}` through the real fence, **failed** in both `/bin/bash` and `/bin/zsh` | 0d62cd5 | Strip removed in real `00-scope.md`: old test passed, new test failed in both shells. In-memory twin `test_mutant_strip_removed_marker_would_carry` |
| IN-05 (Finalize's echo printed twice on the Finalize → fix-loop route) | 58-14 | `test_single_echo_holds`. RED: "subset bullet lacks the do-not-print-again sentence; card still says 'Then print Finalize's `echo_text`'" | 163de79 → 2bac051 | L7 ("Then print Finalize's `echo_text` as message text, " restored): 4 failed |
| SA-01 → D-18 (uncounted serious groups need a count) | 58-10, 58-15, 58-17 | Helper: `test_dismiss_serious_group_without_count_needs_count`, RED `'one' != 'count_needed'`. Prose: `test_count_needed_holds` failed in both card files ("Ask paragraph lacks the count_needed bullet"). `test_followup_holds` failed on the missing `header "How many"` | b648294 → c3f401e; 1e63a4c → 0911d07; 2e81b59 → 140219f | m9 (D-18 `_needs_count` early return removed): 2 failed. T7 (count_needed bullet deleted, fix loop): 3 failed. M15 (same, Finalize): 3 failed |
| SA-02 → D-19 (Bottom line suggestion: dismiss/defer medium rows only) | 58-11, 58-15, 58-17 | Helper: `TestSuggest*` failed with `AttributeError: module 'batch_card' has no attribute 'suggest'`, and the CLI tests failed with exit 2 and USAGE (30 failed, 4 passed). Prose: `test_suggest_fence_holds` and `test_bottom_line_holds` failed in both card files ("the D-09 paragraph lacks the suggest call … the parse dry-run of the suggestion is still there") | aab19b2 → 4e1fe8a (+ 353a780 in-test mutants); 1e63a4c → 0911d07; 2e81b59 → 140219f | s1 (band filter → `_BANDS`): 12 failed. s2 (empty refusal removed): 6 failed. s3 (post-trim parse removed): 2 failed. T8 (parse dry-run restored, fix loop): 4 failed. M16 (same, Finalize): 5 failed |
| SA-03 → D-20 (hand-typed `--close-out-after-rerun`: accepted and documented, no behaviour change) | 58-13 | D-20 needle `(D-20)` in the 00-scope.md normalizer paragraph. `test_d20_hand_typed_marker_documented` and `test_m8_d20_sentence_deleted_trips` failed before the sentence was added (2 failed). The fence is untouched | dac386d | D-20 sentence deleted in the real `00-scope.md`: `test_d20_hand_typed_marker_documented` FAILED, then restored, 2 passed |

**Cross-file contract (58-16 ↔ 58-14).** 58-16 wrote the Finalize side first and left a requirement for 58-14. The fix-loop card must print its rows path and keep that file at Close out, because Finalize uses it to re-map a stale answer. Checked at HEAD f62468e:
- `grep -c "printf 'ROWSFILE=%s" phases/review/50-fix-loop.md` = 2 (both rows fences, lines 25 and 42).
- ``grep -c 'printed after `ROWSFILE=`' phases/shared/90-finalize.md`` = 1 (Stale card, line 198).
- `grep -c 'rm -f[^`]*ROWSFILE'` = 0 in both files. No fence or instruction removes the rows file.

The 50-fix-loop.md Close out line (220) reads:

> Before re-entering, run `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` (the literal paths this pass printed; omit any never printed, a missing file is fine) — this card's answer files are consumed; keep this pass's rows file, whose printed `ROWSFILE=` path is Finalize's source for re-mapping a stale answer.

The Rerun (line 224) also keeps it: "… and keep this pass's `$ROWSFILE`: it is the next pass's `$PRIORROWSFILE`". The contract holds.

### What was not done (gap round)

- There was no live or paid run (D-15). The gap fixes are evidenced only by unit tests, prose locks, real-file mutants and fresh-shell fence walks. The walks used fixture rows and Python standing in for the Write tool.
- The model's own ref extraction is still unverified live. The walks show the helper and fences produce the right result from the refs the prose tells the model to write, e.g. the verbatim title text. They do not show that a model reading the card actually writes those refs.
- The 58-14 / 58-15 / 58-16 / 58-17 Task 3 steps produced no commit. Every real-file mutant was killed on the first run, so no needle had to be added, and the evidence lives only in those SUMMARYs.

### What changed for the owner

- **Plain English is acted on.** The actual iPlayarr sentence, "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out", now resolves without a follow-up question. The card fixes row 5, dismisses the other seven with your words as the reason, and closes out after the rerun.
- **Short fragments no longer hit the wrong row.** A word fragment such as "port" no longer silently matches an unrelated finding like "import".
- **Old answers can't come back.** A suggestion line or a "close out" from an earlier answer or an earlier pass can no longer be acted on later, because those answer files are deleted as soon as they are used.
- **Serious rows need a count or your own words.** To dismiss or defer critical, warning or needs-verification rows as a group, you now give a count ("How many?"). Typing "bottom line" can only fix rows or dismiss/defer medium ones.
- **Smaller fixes.**
  - The recovery text on the report matches its table word for word.
  - Finalize's echo prints once.
  - Typing the internal close-out flag by hand is documented as the same as choosing Close out.

---

## Gate

Run on 2026-10-27 at HEAD `41a381f` (the Task-1 doc commit; no plugin file differs from the last code commit 75bb831). Commands from `plugins/vibe-check` unless noted; bare `pytest`.

| Check | Command | Result |
|---|---|---|
| Full suite | `pytest -q` | `3465 passed, 4608 subtests passed in 162.51s` — 0 failed, 0 skipped reported. Baseline 3311 (Phase 57 gate) + 154 new tests from 58-01..58-05, 58-07..58-09 |
| Replay tests | `pytest -q scripts/test_replay.py` | `64 passed, 10 subtests passed` |
| Replay candidate | `python3 replay.py candidate --name phase58-gate --scorer rev:HEAD` (from `scripts/`) | exit 0; `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`; `kept 25 / protected 26`; **REGRESSED 0**; UNEVALUABLE 0; AMENDED 1 (unchanged from the 57-23 baseline: the pre-existing `triggarr-secret-in-logs/run-2`). Candidate scorer sha256 `3504d2da79e9ebab26bfedd01c7614c9b7cc06ade99c12b7e24e90003edd22fb`, identical to 57-23's |
| Replay diff | `python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json` | exit 0; 170 runs compared, 0 differing, 0 unallowed; Differences: none |
| Golden | `pytest -q scripts/test_score.py -k golden` | `9 passed, 491 deselected` |
| Golden digest | `score.stable_hash('a.py','  x=1','title') == test_score.GOLDEN_DIGEST` (from `scripts/`) | `golden ok` |
| Import sets | `pytest -q test_score.py -k ImportSet`; `pytest -q test_carry_state.py -k ImportSet` | `3 passed` each |
| Frozen files | `git diff --stat 24dccdc..HEAD -- scripts/score.py scripts/batch_parse.py` | empty |
| Carrier round-trip | `pytest -q scripts/test_fix_loop_card.py -k CarrierRoundTrip -v` | `3 passed` — each test loops over `SHELLS` = `/bin/bash` and `/bin/zsh` (both present) |

**Mutant inventory** (every new test module carries at least one tripping mutant):

| Module | Grep count | `-k "mutant or Trips" -v` | Plan |
|---|---|---|---|
| `test_card_scope.py` | `subTest("mutant` = 4 | 4 passed, 5 subtests | 58-01 (+ real-file m1-m5) |
| `test_answer_resolve.py` | `subTest("mutant` = 5 | 5 passed, 10 subtests | 58-03 (+ real-file m1-m5) |
| `test_recovery_pairs.py` | `subTest("mutant` = 0; `TestLockTrips` has 5 test methods (one per mutant) | 5 passed, 4 subtests | 58-02 (+ real-file a-l) |
| `test_fix_loop_card.py` | `def test_mutant_` = 28 (24dccdc: 8, gained 20) | 47 passed, 29 subtests | 58-04, 58-08 |
| `test_finalize_card.py` | `def test_mutant_` = 9 (24dccdc: 0, gained 9 methods carrying 20 mutant subtests) | 9 passed, 20 subtests | 58-05 (+ real-file M1-M12), 58-09 (+ real-file M1-M6) |
| `test_scope_args.py` | `def test_m[4-7]_` = 4 (24dccdc: 0) | 4 passed | 58-07 |

A passing mutant test asserts the lock *trips* on its mutant, so "passed" here means every mutant is caught. Each plan also applied its mutants to the real files and recorded the failing tests (tables in the SUMMARYs and in V1-V5 above).

No plugin file was modified by 58-06: `git log --name-only --format= 24dccdc..HEAD -- plugins | grep -c .` = 32 before and after this plan's commits.

---

## Gap round gate

Run on 2026-10-27 at HEAD `f62468e` (the 58-17 docs commit; the last plugin change is 140219f). This is the first run after every gap plan, 58-10 through 58-17, had landed. Commands were run from `plugins/vibe-check` unless noted, in one `bash -s` fence, with bare `pytest`. Replay reports were written to the session scratchpad. `replay.py` requires `--out`.

| Check | Command | Result |
|---|---|---|
| Full suite | `pytest -q` | `3542 passed, 4699 subtests passed in 160.08s`: 0 failed. 3465 (58-06 gate) + 77 new tests from 58-10..58-17 (per SUMMARYs: 58-10 +14, 58-12 +3, 58-13 +3, 58-16 +6, 58-11 +25, 58-14 +10, 58-15 +8, 58-17 +8) |
| Replay tests | `pytest -q scripts/test_replay.py` | `64 passed, 10 subtests passed` |
| Replay candidate | `python3 replay.py candidate --name phase58-gap-gate --scorer rev:HEAD --out <scratchpad>/phase58-gap-candidate.md` (from `scripts/`) | exit 0. `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`; `kept 25 / protected 26`; **REGRESSED 0**; UNEVALUABLE 0; AMENDED 1. The amended run is the pre-existing `runs/triggarr-secret-in-logs/run-2`, ledger 008, unchanged. Candidate scorer sha256 `3504d2da79e9ebab26bfedd01c7614c9b7cc06ade99c12b7e24e90003edd22fb`, identical to 58-06 / 57-23 |
| Replay diff | `python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out <scratchpad>/phase58-gap-diff.md` | exit 0; 170 runs compared, 0 differing, 0 differing (allowed), 0 unallowed; Differences: none |
| Golden | `pytest -q scripts/test_score.py -k golden` | `9 passed, 491 deselected` |
| Golden digest | `score.stable_hash('a.py','  x=1','title') == test_score.GOLDEN_DIGEST` (from `scripts/`) | `golden ok` |
| Import sets | `pytest -q test_score.py -k ImportSet`; `pytest -q test_carry_state.py -k ImportSet` | `3 passed` each |
| Frozen files | `git diff --stat 24dccdc..HEAD -- plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/batch_parse.py` | empty |
| Carrier round-trip | `pytest -q scripts/test_fix_loop_card.py -k CarrierRoundTrip -v` | `4 passed, 122 deselected`. 58-06 had 3; 58-13 rebuilt `test_close_out_drops_the_marker` and added the in-memory strip mutant. Each test loops over `SHELLS` = `/bin/bash` and `/bin/zsh` |

**Mutant inventory, gap round.** Counts are taken at the 58-06 gate commit `41a381f` (with `git show 41a381f:<file> | grep -c`) and at HEAD:

| Module | Grep | 41a381f → HEAD | Run (HEAD) | Gap plans |
|---|---|---|---|---|
| `test_answer_resolve.py` | `def test_m[0-9]*_\|subTest("mutant` | 10 → 18 (+8) | `-k "mutant or m6 or m7 or m8 or m9 or Trips"`: 9 passed, 18 subtests | 58-10 (in-test m6-m9; real-file m6-m9) |
| `test_bottom_line_suggest.py` (new) | `def test_s[1-3]_` | 0 → 3 | `-k "s1 or s2 or s3"`: 3 passed, 6 subtests | 58-11 (real-file s1-s3) |
| `test_fix_loop_card.py` | `def test_mutant_` | 28 → 38 (+10) | `-k mutant`: 57 passed, 59 subtests | 58-13 (+1), 58-14 (+5; real-file L1-L7), 58-15 (+4; real-file T5-T8) |
| `test_finalize_card.py` | `def test_mutant_` | 9 → 16 (+7) | `-k mutant`: 16 passed, 35 subtests | 58-16 (+3; real-file F1-F5), 58-17 (+4; real-file M13-M16) |
| `test_recovery_pairs.py` | `def test_` / `def test_[mn]_` | 18 → 21 / 0 → 2 (trip tests m, n) | `-k Trips`: 7 passed, 6 subtests | 58-12 (real-file m, n, o) |
| `test_scope_args.py` | `def test_m[0-9]*_` | 7 → 8 (+1, m8) | `-k test_m`: 11 passed, 80 subtests | 58-13 (D-20 sentence-deletion mutant m8) |

A passing mutant test asserts that the lock trips on its mutant, so "passed" means every mutant was caught. Each gap plan also applied its mutants to the real file, recorded the failing tests and reverted. The SUMMARYs of 58-10..58-17 and the ledger below hold those tables. The finalize-card gain is +7 methods, below the "≥ 9" the 58-18 plan estimated. Its nine real-file mutants (F1-F5, M13-M16) were all killed per 58-16 / 58-17.

Plugin history since 24dccdc: `git log --name-only --format= 24dccdc..HEAD -- plugins | grep -c .` = 55 before this plan's commits (18 distinct files). 58-18 changes no plugin file.
