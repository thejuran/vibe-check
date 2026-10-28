---
phase: 58-clear-actions-recovery-and-answers-acted-on
reviewed: 2026-10-27T23:03:22Z
depth: deep
scope: gap round only — git diff 28c4fc2..HEAD -- . ':!.planning/'
files_reviewed: 13
files_reviewed_list:
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/40-render.md
  - plugins/vibe-check/phases/review/50-fix-loop.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/batch_card.py
  - plugins/vibe-check/scripts/test_answer_resolve.py
  - plugins/vibe-check/scripts/test_batch_card.py
  - plugins/vibe-check/scripts/test_bottom_line_suggest.py
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_fix_loop_card.py
  - plugins/vibe-check/scripts/test_recovery_pairs.py
  - plugins/vibe-check/scripts/test_scope_args.py
  - plugins/vibe-check/templates/output-format.md
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 58: Code Review Report (gap round)

**Reviewed:** 2026-10-27T23:03:22Z
**Depth:** deep
**Files Reviewed:** 13
**Status:** issues_found

## Summary

This review covers only the gap-round diff (`28c4fc2..HEAD`, 13 plugin files, +1728/-63). It checks whether each 58-REVIEW.md item is closed and looks for new defects.

How I checked:
- The 7 touched test modules pass: 443 passed, 732 subtests.
- I ran `resolve` and `suggest` directly on the iPlayarr eight-row fixture, using refs files with the owner's actual wording plus edge cases.
- I ran the printed-path `resolve` fence in a fresh `bash -s` shell with literal paths, then ran the `rm -f` and `cp` steps.
- I traced the new cleanup points against every place that reads a file afterwards.

**Result.** Every prior item is closed for the scenario it described. The gap round adds three new problems at the joins between files:
1. The D-08 fallback deletes the Bottom line suggestion file but then re-shows a card that still offers that suggestion.
2. Whole-word title matching, combined with the new "verbatim, do not trim" instruction and a narrow filler list, sends very common phrasings to a follow-up question.
3. A pass can now print `ROWSFILE=` twice, so stale-card re-mapping can bind to the subset rows file. I confirmed this dismisses the wrong row.

## Closure check (prior 58-REVIEW.md items)

| Item | Verdict | Evidence on current code |
|---|---|---|
| WR-01 stale `close_out` in `$RESOLVEFILE` | **CLOSED** | `50-fix-loop.md:224`: the Rerun runs `rm -f` on SUGGESTFILE, REFSFILE and RESOLVEFILE. Close out does the same (`:220`), and so does the D-08 fallback (`:215`). The marker condition now says "the resolve output printed in this step had `close_out` true; a `close_out` found in a file written for an earlier answer is never read". Line 14 no longer claims the files "don't survive". Replaying the original 5-step path (resolve → D-08 full card → Apply all) gives no marker, because Apply all is not the `ok` true branch. |
| WR-02 `$SUGGESTFILE` survives the Rerun | **CLOSED** (but see new WR-01) | The Rerun and Close out delete it. Finalize step 2 and step 3 delete it (`90-finalize.md:244-245`). The typed path is now gated on "a `Bottom line suggests:` line was printed on the card currently shown" (`50-fix-loop.md:126`, `90-finalize.md:157`), not on whether the file exists. |
| WR-03 substring title match | **CLOSED for the two reported cases** (residual: new WR-02) | `_match_title` (`batch_card.py:945-954`) matches whole tokens. `"port"` against "import" gives `[]`. `"the Browse recovery issue"` gives `[5]`. The verbatim iPlayarr sentence resolves to `fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: "dismiss the 7 fixed rows")`, `ok` true and `close_out` true; I confirmed this in a fresh shell. |
| WR-04 `ok:false` with every ref clear | **CLOSED** | Both files now have the bullet "every ref is `one` or `bulk`, `needs_reason` is false and `parse_reason` is set" pointing to the full-card fallback (`50-fix-loop.md:212`, `90-finalize.md:213`). `test_two_uncounted_remaining_is_ok_false_with_every_ref_clear` pins the helper side. |
| WR-05 `$PRIORROWSFILE` never printed | **CLOSED for the single-fence pass** (residual: new WR-03) | Both rows fences print `ROWSFILE=` (`50-fix-loop.md:25,42`, `90-finalize.md:82`). The Rerun and Close out keep the rows file, and no `rm -f` names ROWSFILE. Finalize drops the "an earlier `--finalize`" case and falls back to the full card when no path was printed. |
| WR-06 `$RESOLVEFILE` not printed | **CLOSED** | `printf 'RESOLVEFILE=%s'` is in both create fences (`50-fix-loop.md:175`, `90-finalize.md:176`). There is a "Temp paths are literals" paragraph in both files. In my fresh-shell walk, the literal-path `resolve` returned `ok: true`. In a fresh shell, the variable form still fails with `: No such file or directory`, which is what the convention now prevents. |
| IN-01 template rewords the recovery cell | **CLOSED** | `output-format.md:70` now includes "(a run with nothing new dispatches no reviewer)." verbatim. `nv_suffix_from_table` derives the expected suffix from the parsed table row. |
| IN-02 no separator on `Fix not yet verified:` | **CLOSED** | `40-render.md:43` now reads "then ` — ` and the pair". |
| IN-03 `changed` covers `joined` | **CLOSED** | `_CHANGED_CAUSES = ("code", "nearby", "severity")` (`batch_card.py:902`, `:964-966`). |
| IN-04 decorative close-out test | **CLOSED** | `test_close_out_drops_the_marker` (`test_fix_loop_card.py:1860`) now derives `${original_args}` from `_PRIOR_RERUN` through the real fence in both shells. The in-memory strip mutant (`:1878`) shows that removing the strip carries the marker. |
| IN-05 echo printed twice | **CLOSED** | `50-fix-loop.md:35`: "Finalize already printed its `echo_text` before reading this file — do not print it again." The old "Then print Finalize's `echo_text`" sentence is gone. |
| SA-01 → D-18 | **CLOSED** | `_needs_count` (`batch_card.py:980-987`). Uncounted `dismiss band:critical` gives `count_needed`. With `count: 3` it gives `dismiss 1,2,3 -- fp`, `ok`. Uncounted `dismiss band:medium` still acts. Uncounted `defer pending` over a warning row gives `count_needed`. |
| SA-02 → D-19 | **CLOSED** | `suggest("dismiss 1-8 -- fp")` gives `dismiss 8 -- fp` with 1-7 dropped. `fix` keeps every band, including NV. When every clause is dropped, the result is `REASON_SUGGEST_EMPTY`. The fences no longer dry-run the suggestion through `parse`; they call `suggest`. |
| SA-03 → D-20 | **CLOSED** (documented, as ruled) | The `00-scope.md` carrier paragraph has the D-20 sentence: a hand-typed marker is accepted, and Finalize's gate is unchanged. |

## Warnings

### WR-01: The D-08 fallback deletes the suggestion file but re-shows a card that still offers "bottom line"

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:72`, `:104`, `:126`, `:215`; `plugins/vibe-check/phases/shared/90-finalize.md:117`, `:153`, `:157`, `:216`
**Issue:** When the owner's reply is still unclear after the follow-up, the gap round's D-08 fallback runs `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` and then "show the full card once". That card is the same card. Its template condition for the suggestion line is "ONLY when the suggestion fence below printed a `SUGGESTFILE=` path created on this pass" (`:72`) / "created for this card" (Finalize `:117`), and that is still true, so the re-shown card prints `Bottom line suggests: …`. Because that condition only checks that a path was printed, it is also true after a `suggest` refusal, which contradicts the "Exit 0 → fill the slot" rule at `:104`.

The failure path:
1. Two unclear replies lead to the D-08 full card, which carries the suggestion line.
2. The owner types "bottom line".
3. The typed path's test passes ("a line was printed on the card currently shown"), so the model runs `cp "$SUGGESTFILE" "$ANSWERFILE"`. The file was just deleted, so `cp` exits 1 (I confirmed the exit code).
4. The fallback rule sends the text to Translate as plain English. "bottom line" names no row, so no valid refs doc can be written: `refs` must be non-empty, so `resolve` returns REASON_REFS.
5. A `resolve` refusal goes "straight to the full-card fallback", so the full card is shown a second time.

D-08 says the full card is shown once. This repeats the iPlayarr symptom (a decided answer met by the same card again), on the one path the owner was explicitly invited to use. The gap-round prose lock `test_answer_files_holds` requires this `rm -f` at the D-08 point, so the tests lock in the defect.
**Fix:** The re-shown card is the same card, so its suggestion is still valid. Keep the suggestion file and clear only the translation files:
```text
… still nothing is recorded; run `rm -f "$REFSFILE" "$RESOLVEFILE"` (the literal paths …) so nothing from the
abandoned translation survives — keep `$SUGGESTFILE`: the full card shown next is the same card and still offers it …
```
Alternatively, if the deletion stays, add "omit the `Bottom line suggests:` line on this fallback card". In both files, also change the template condition at `:72` / `:117` to "ONLY when `suggest` exited 0 for this card and its file still exists". Update the `test_answer_files_holds` needle, and add a mutant that re-adds `$SUGGESTFILE` to the D-08 `rm -f`.

### WR-02: Whole-word matching plus "verbatim, do not trim" text makes common clear references fail

**File:** `plugins/vibe-check/scripts/batch_card.py:896-899` (`_TITLE_FILLER`), `:938-954`; `plugins/vibe-check/phases/review/50-fix-loop.md:170`; `plugins/vibe-check/phases/shared/90-finalize.md:171`
**Issue:** The prior review recommended telling the model to pass only the distinctive title words. The gap round did the opposite. The prose now says `"text": "<the owner's words for that row, verbatim>"` and "do not trim or clean them". It relies on the helper to drop filler, but the filler list holds only determiners and card nouns. Every other word the owner adds must appear in the title as a whole token. I ran these against the eight-row fixture, where row 7 is "Retry budget is not reset after a successful relay" and row 5 is the Browse recovery row:

| Owner phrase | Result | Why |
|---|---|---|
| "the retry budget warning" | `[]` | The card line itself ends in `(warning)`. Band words are not filler. |
| "the relay failover critical" | `[]` | Same as above. |
| "the browse recovery one you flagged" | `[]` | "you" and "flagged" are not filler. |
| "the Browse recovery issue from earlier" | `[]` | "from" and "earlier" are not filler. |
| "the cursor bug in browse" | `[]` | Prepositions are deliberately not filler. |
| "Browse recovery (#5)" | `[]` | "5" is not in the title. |
| "Retry budget's reset" | `[]` | `'s` becomes a lone `s` token. |
| "retries budget" | `[]` | Inflected forms are not matched. |

Each of these is a clear reference to one row, and each resolves to `none`. Per the prose, a `none` ref has no candidates, so the "Which rows" follow-up offers "up to 4 … rows no other ref claimed". On this card those are rows 1-4, so neither intended row (5 or 7) is even a button. The owner is asked again about an answer that was clear. That is the exact behavior ANSR-01 exists to remove. It fails safe (nothing wrong is recorded), but it defeats the phase's main outcome for ordinary phrasing. The fixtures only pass because they use phrases whose extra words happen to be on the filler list.
**Fix:**
- Keep the whole-token rule, which correctly fixes the `port`/`import` fragment case.
- Widen what is ignored. Add the band words (`critical`, `warning`, `medium`, `needs`, `verification`), common pronouns and verbs (`you`, `flagged`, `mentioned`, `raised`, `found`), and the possessive `s`.
- Either let the model pass "the distinctive title words the owner used" (the prior recommendation), or match on a majority or ≥2 of the non-filler tokens and still require the result to be unique.
- For a `none` title ref, return candidates ranked by token overlap, so the follow-up shows the likely row.
- Add fixtures for "the retry budget warning" and "the Browse recovery one you flagged", each resolving to one row.

### WR-03: Two `ROWSFILE=` lines per pass, so stale re-mapping can bind to the subset rows file and act on the wrong row

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:25`, `:42`, `:156`, `:197`, `:220`, `:224`; `plugins/vibe-check/phases/shared/90-finalize.md:198`; `plugins/vibe-check/scripts/batch_card.py:1456-1466`
**Issue:** The WR-05 fix binds `$PRIORROWSFILE` to "the literal path the previous pass's rows fence printed after `ROWSFILE=`". The Rerun keeps "this pass's `$ROWSFILE`", and Close out keeps "this pass's rows file". But a pass that acts on a typed or translated `fix` runs step 2, which runs **the subset fence** (`:156`). That fence also prints `ROWSFILE=`, for a renumbered rows document holding only the fix targets. So a pass prints two `ROWSFILE=` lines, and the later one is the subset document. A Finalize-routed pass prints only the subset one, and the owner never saw a card for it. Every D-17 "fix X, then close out" pass also ends with the subset line printed last, and that is the file Finalize's stale re-map (`90-finalize.md:198`) is told to use.

`resolve` accepts a `"subset": true` document as `--prior-rows`. I verified the effect on the iPlayarr fixture:
- Pass 3 card: the owner types `fix 5` (the Browse recovery warning). Step 2 prints a subset `ROWSFILE=` whose only row is #1 = Browse recovery.
- Pass 4: the owner answers from the old card, "dismiss 1 -- fp", meaning row 1 (relay failover, critical).
- With the card's rows file as prior: `dismiss 1 -- fp`, which is correct.
- With the subset rows file as prior (the last `ROWSFILE=` printed): `ok: true`, `dismiss 5 -- fp`. The Browse recovery warning, which the owner just asked to fix, is dismissed, and it is acted on with no confirm card.

The echo shows the site, but the decision is recorded before the owner can object.
**Fix:**
- Prose, in both files: name the source exactly, "the `ROWSFILE=` path printed by the rows fence that rendered the card the owner read (the ordinary fence, or Finalize's rows fence) — never the subset fence's". A Finalize-routed pass then has no card of its own, and its prior card is Finalize's.
- Helper: in `_run_resolve`, refuse a prior-rows document that has `"subset": true` (`REASON_PRIOR_ROWS`). That makes the wrong binding fail safe even if the prose is misread.
- Add a fixture for the subset-as-prior case, plus a mutant.

## Info

### IN-01: The card never tells the owner the Bottom line suggestion was trimmed

**File:** `plugins/vibe-check/scripts/batch_card.py:1484-1491`; `plugins/vibe-check/phases/review/50-fix-loop.md:93-104`; `plugins/vibe-check/phases/shared/90-finalize.md:142-153`
**Issue:** `suggest` reports dropped serious rows only on stderr ("suggestion trimmed: N serious row(s) dropped"), and that text sits inside a collapsed Bash output. The card shows only the trimmed grammar. For example, a Bottom line that recommends dismissing three criticals as false positives shows up as `Bottom line suggests: fix 5`. An owner who types "bottom line" expecting the report's verdict gets less than that. This fails safe: the echo lists those rows as still open.
**Fix:** When the fence's stderr has the trimmed line, append "(N row(s) the Bottom line would dismiss or defer need your own words)" to the card's suggestion line.

### IN-02: The "How many" follow-up offers single-select row buttons, so one click narrows the group to one row

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:210`; `plugins/vibe-check/phases/shared/90-finalize.md:211`
**Issue:** The question asks for a count, but the buttons are row labels, and the Ask paragraph is single-select. An owner who clicks `#1 …` to confirm "the criticals" has the completed ref rewritten to `number` refs for that one row. The other group members stay open. This fails safe (the echo shows "still open"), but the answer the owner gave is not the one carried out.
**Fix:** Make the options counts, for example the matched count ("All 3") plus "None of these", with row numbers through Other. Or state in the question that picking a row decides only that row.

### IN-03: `test_s2_empty_refusal_dropped`'s mutant subtest patches the function under test

**File:** `plugins/vibe-check/scripts/test_bottom_line_suggest.py:225-240`
**Issue:** The "mutant" replaces `batch_card.suggest` with a wrapper and then asserts that the wrapper's own output fails the check. It would pass whether or not the real `if not clauses` guard exists, so it is decorative. The real protection is `check_all_dropped_refuses`. Without the guard, `parse("")` returns REASON_EMPTY, not REASON_SUGGEST_EMPTY, and that check catches the difference. The gap ledger's real-file s2 mutant confirms this.
**Fix:** Mutate the guard itself, for example by patching `_grammar_for` to return `""` for empty clauses with the guard removed via source edit. Or drop the subtest and cite the real-file mutant.

### IN-04: Title tokens are not Unicode-normalized

**File:** `plugins/vibe-check/scripts/batch_card.py:938-942`
**Issue:**
- `_title_tokens` casefolds but does not apply NFC/NFKC. An owner's NFC "café" does not match a title stored as NFD "café": the combining mark is not alnum, so the title tokenizes to `cafe`.
- Scripts written without spaces (CJK) form one maximal token, so a partial phrase never matches.

Both fail safe (`none`).
**Fix:** Apply `unicodedata.normalize("NFKC", …)` before casefolding, on both sides.

### IN-05: `suggest` does not flatten the reason to one line

**File:** `plugins/vibe-check/scripts/batch_card.py:1215-1216`
**Issue:** `resolve` passes its reason through `_one_line`, but `suggest` embeds `result["reason"]` raw. `suggest("defer 8 -- line1\nline2")` returns `q1 = "defer 8 -- line1\nline2"`, and the prose copies that verbatim into the card's one-line `Bottom line suggests:` slot. The text is model-written, so the risk is low, but a newline breaks the card line and is recorded verbatim as the decision reason.
**Fix:** Use `_one_line(result["reason"])` when building the trimmed grammar.

## Set aside (needs ruling)

### SA-01: `$BLOBFILE` still crosses Bash calls as a shell variable with no printed path

**Where:** `plugins/vibe-check/phases/shared/90-finalize.md:13-16`, `:84`, `:245`
**Why excluded:** This predates the gap round, and the diff does not touch it. The new "Temp paths are literals" paragraph covers files "this card creates", and `$BLOBFILE` is created by the earlier counts step.
**Effect if left as is:** Where shell state does not persist between Bash calls, the rows fence and the step-3 re-count would run `--head-blobs ""`. The helper then refuses, and Finalize stops with "I'm uncertain about Finalize mode". This fails closed: nothing is written.
**Needs:** A ruling from the developer: bring the counts step under the printed-path convention now, or carry it to the 999.13 backlog.

---

_Reviewed: 2026-10-27T23:03:22Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: deep_
