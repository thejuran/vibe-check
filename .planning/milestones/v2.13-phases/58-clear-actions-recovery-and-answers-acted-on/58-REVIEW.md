---
phase: 58-clear-actions-recovery-and-answers-acted-on
reviewed: 2026-10-27T00:00:00Z
depth: deep
files_reviewed: 18
files_reviewed_list:
  - README.md
  - plugins/vibe-check/commands/deep-review.md
  - plugins/vibe-check/commands/review.md
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/40-render.md
  - plugins/vibe-check/phases/review/50-fix-loop.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/batch_card.py
  - plugins/vibe-check/scripts/test_answer_resolve.py
  - plugins/vibe-check/scripts/test_batch_card.py
  - plugins/vibe-check/scripts/test_card_scope.py
  - plugins/vibe-check/scripts/test_confirmed_fix.py
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_fix_loop_card.py
  - plugins/vibe-check/scripts/test_pause_batching.py
  - plugins/vibe-check/scripts/test_recovery_pairs.py
  - plugins/vibe-check/scripts/test_scope_args.py
  - plugins/vibe-check/templates/output-format.md
findings:
  critical: 0
  warning: 6
  info: 5
  total: 11
status: issues_found
---

# Phase 58: Code Review Report

**Reviewed:** 2026-10-27
**Depth:** deep
**Files Reviewed:** 18
**Status:** issues_found

## Summary

I reviewed the diff `24dccdc..HEAD` (excluding `.planning/`). I traced `batch_card.py resolve` end to end and probed it directly with edge-case refs and malformed rows, refs and prior-rows files. I compared the 50-fix-loop and 90-finalize prose against the helper's actual output and CLI, ran the `00-scope.md` carrier against the spine re-entry strings, and checked the recovery table against the `score.py` constants. The phase test files pass (498 tests, 906 subtests).

What holds up:
- **Robustness.** `resolve` survived every malformed input I tried: deep nesting, wrong field types, lone surrogates, an empty `--prior-rows` path and a missing `--prior-rows`. Each one exits through a fixed refusal string with no traceback, and no refusal string contains owner text.
- **D-16 counted complement.** It is correct. A mismatched count returns `count_mismatch`, and any unclear ref blocks `remaining`.
- **Carrier stripping.** The `--close-out-after-rerun` token is stripped and detected as a whole token only. It never sets `FINALIZE_MODE`.

The defects sit at the joins between files:
- **Temp files.** They are never cleaned up, but the prose assumes they are gone. A stale `close_out` or Bottom line suggestion can be acted on.
- **Title matching.** The helper's matching rule does not match what the prose tells the model to write.
- **Unhandled `resolve` outcome.** One outcome has no branch in the prose.
- **Stale-card re-mapping (D-07).** It cannot run, because the prior rows path is never available to the model.

## Warnings

### WR-01: A stale `close_out` in `$RESOLVEFILE` can turn a later, unrelated answer into a close-out

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:14`, `:148`, `:213`
**Issue:** The Rerun decides whether to add `--close-out-after-rerun` from "`close_out` true in `$RESOLVEFILE`" (lines 148 and 213). Nothing ever removes `$RESOLVEFILE` or clears that value: the Rerun only does `rm -f "$SUBSETFILE"; unset SUBSETFILE`. Line 14 says the temp files written before the Rerun don't survive it ("none of which survive it"), which is false. Here is a concrete path where it goes wrong:
1. The owner types "fix the login thing and close out".
2. `resolve` returns `none`, the follow-up reply is still unclear, and D-08 shows the full card once.
3. The owner now picks **Apply all & rerun**, which D-08 treats as a new answer.
4. Step B runs, and the Rerun finds `close_out: true` still in `$RESOLVEFILE` from the abandoned translation. It appends the marker.
5. The next pass skips its card and goes straight to Finalize, which the owner never asked for in this answer.

The same leak happens one pass later, when a typed grammar answer that `parse` accepts directly follows an earlier translated close-out.
**Fix:** Tie the carry to the answer, not to the file. Clear the file at every exit and when the full-card fallback is shown, and fix the false sentence on line 14:
```bash
rm -f "<RESOLVEFILE literal>" "<REFSFILE literal>"   # at the Rerun, at Close out, and before the D-08 full-card fallback
```
Also reword lines 148 and 213 to: "when the answer acted on in THIS step came from the `ok` true branch of **Translate the answer** and its resolve output had `close_out` true". Add a prose-lock mutant for the cleanup.

### WR-02: `$SUGGESTFILE` survives the Rerun, so "bottom line" on a later pass can apply the previous pass's row numbers

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:80-98`, `:120`, `:213`; `plugins/vibe-check/phases/shared/90-finalize.md:131-153`
**Issue:**
- **Fix-loop card.** The suggestion file is removed only when the dry-run parse refuses it. The Rerun never deletes or unsets it. The typed path is gated on "`$SUGGESTFILE` exists for this pass" (line 120), a test the model can only make from its own memory. On pass N+1, the Bottom line may not map cleanly, so no new file is created and no line is shown. If the owner then types "do what it says", the model can still find pass N's file on disk and copy it into `$ANSWERFILE`. `parse` only checks that the row numbers are in range, so `fix 1,2; defer 3-5 -- …` is applied to the renumbered rows of the new card: the wrong findings get deferred or dismissed.
- **Finalize card.** Finalize's prose says a fix-loop grammar is "never reused", but the fix-loop file is still on disk after Close out.

**Fix:** At the Rerun and at Close out, add `rm -f "<SUGGESTFILE literal>"` next to the subset cleanup, and state in both files that the typed "bottom line" path applies only to a suggestion line printed on the card currently shown. Add a mutant that drops the cleanup.

### WR-03: The title matching rule doesn't match the prose: filler words make clear answers fail, and short fragments match the wrong row

**File:** `plugins/vibe-check/scripts/batch_card.py:918-923` (`_match_title`); `plugins/vibe-check/phases/review/50-fix-loop.md:162`; `plugins/vibe-check/phases/shared/90-finalize.md:166`
**Issue:** `_match_title` requires every word of `text` to appear as a substring of the title. The prose tells the model to write `"text": "<the owner's words>"`. Verified locally:
- `"the Browse recovery issue"` against "Browse recovery leaves a stale cursor after a failed page load" gives `none`. The test fixture only passes because it uses the hand-trimmed `"Browse recovery"`. If the model follows the prose for the primary iPlayarr regression, it gets a follow-up question instead of action. That is the D-01 failure this phase exists to fix, although it fails safe.
- `"port"` gives `one` for "Unused import of os", and `"on"` gives `one` for "Pagination off by one". A fragment that happens to match only one row inside an unrelated word is treated as clear and acted on with no confirm card. If the row the owner meant has already left the card (fixed, or renumbered), a different finding is fixed, dismissed or deferred.

**Fix:** Match whole words (casefolded `\b`-bounded tokens, or a token-set comparison) in `_match_title`. In both prose files, say: "`text` = only the distinctive title words the owner used, without filler such as the / issue / bug / one". Add fixtures for:
- a filler-word reference such as "the Browse recovery issue", which resolves to one row;
- an in-word fragment such as "port" against "import", which resolves to none.

### WR-04: `ok:false` with every ref clear (a parser refusal) has no branch in the prose

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:184`, `:196-202`; `plugins/vibe-check/phases/shared/90-finalize.md:188`, `:200-206`
**Issue:** `resolve` can return `ok: false` with every ref `one` or `bulk` and `needs_reason: false`, when `parse` refuses the grammar it built for a reason other than a missing reason. Two cases I verified:
- Two uncounted `remaining` refs ("dismiss the rest … defer everything else"). The grammar becomes `fix 1; dismiss rest; defer rest -- x`, and the parse reason is `'rest' may appear in only one clause`.
- A rows file whose band is not one of the four known bands. The parse reason is `rows file is missing or malformed`.

The prose sends every `ok` false result to **Ask only what is missing**, but none of its bullets (`many`/`conflict`, `none`/`count_mismatch`, `needs_reason`, `blocked`, or a `resolve`/copy refusal) covers this case. The model is told to ask one question about "only the unclear piece" when no piece is unclear, so it may improvise a question or a re-show.
**Fix:** Add a bullet to both files: "every ref is `one`/`bulk`, `needs_reason` is false and `parse_reason` is set → no piece to narrow; go straight to the full-card fallback, its note saying the answer combined two bulk groups (or could not be checked)". Optionally, have `resolve` report a `REST_TWICE` refusal as a `conflict` on the second `remaining` ref, so it becomes an askable piece.

### WR-05: Stale-card re-mapping (D-07) cannot run, because `$PRIORROWSFILE` points at a path that is never printed

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:188-194`; `plugins/vibe-check/phases/shared/90-finalize.md:192-198`
**Issue:** The prose binds `$PRIORROWSFILE` to "that pass's `$ROWSFILE` path, used as is — never retyped or rebuilt". No fence ever prints `ROWSFILE`'s path (`mktemp` output is silent; only SUBSETFILE, REFSFILE and SUGGESTFILE are printed). On top of that:
- Every pass's rows fence reassigns `ROWSFILE=$(mktemp …)`.
- Finalize's own case, "an earlier `--finalize` built a card", is a separate invocation.

So the old path is never available to the model, even when shell variables persist. In practice the fence runs with an empty or invented path, `resolve` refuses (`prior rows file is missing or malformed`), and the owner gets the full-card fallback. D-07's "act, and show the new numbers" never happens, while the tests (`test_stale_card_holds`, the `test_answer_resolve` prior-rows fixtures) give the impression that it works.
**Fix:** Have the rows fences print `ROWSFILE=%s` (as the subset fence does). Tell the model to record that literal path per pass, and to keep the previous pass's rows file when the Rerun runs (do not delete it until the next pass's card is answered). For Finalize, either drop the "earlier `--finalize`" case or persist the rows document next to the state file. Add a prose lock that the rows fence prints its path.

### WR-06: The new fences rely on `$RESOLVEFILE` surviving across Bash calls but never print its path

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:164-180`; `plugins/vibe-check/phases/shared/90-finalize.md:168-184`
**Issue:**
- **The pattern break.** The create fence prints `REFSFILE=%s` (needed for the Write tool) but not `RESOLVEFILE`. The `resolve` fence (`> "$RESOLVEFILE"`) and the grammar copy fence (`< "$RESOLVEFILE"`) run as separate Bash calls.
- **What the same file says.** 50-fix-loop.md:18 states that a bound variable "does not survive into this separate Bash call", and that is why the subset convention prints the path and substitutes the literal.
- **What I checked.** In this environment, a variable set in one Bash call was empty in the next.
- **The effect.** Where shell state doesn't persist, `> ""` fails, the `else` arm prints "nothing was recorded", and every plain-English answer ends at the full-card fallback. That brings back the iPlayarr re-show symptom.

The older `$ROWSFILE`/`$ANSWERFILE`/`$PARSEFILE` uses follow the same unprinted pattern, so this is a long-standing convention gap. The phase-58 fences extend it, and they contradict their own REFSFILE handling.
**Fix:** Print `RESOLVEFILE=%s` in the create fence, and tell the model to substitute the literal path into the `resolve` and copy fences (the subset-fence convention). Add a prose-lock needle for the printf.

## Info

### IN-01: The template's needs-recheck suffix rewords the recovery cell the table says never to reword

**File:** `plugins/vibe-check/templates/output-format.md:70`; `plugins/vibe-check/phases/review/40-render.md:50,54`
**Issue:**
- The table cell for `verdict: fix not yet confirmed: no eligible reviewer ran this pass` reads "Next run: retried automatically on the next review of new changes (a run with nothing new dispatches no reviewer)."
- The template suffix drops the parenthetical.
- 40-render.md says "The cells are fixed text: never reword them".
- `test_recovery_pairs.NV_SUFFIX` locks in the shortened version, so the two documents disagree and the tests enforce that disagreement.

**Fix:** Copy the cell verbatim into the template, and change `NV_SUFFIX` to derive from the parsed table row instead of a separate literal.

### IN-02: The `Fix not yet verified:` line has no separator before its pair

**File:** `plugins/vibe-check/phases/review/40-render.md:43`, `:48`
**Issue:** The confirmed line ends with ` — ` before its pair. The verified line says only "then the pair", and the table rule says "separated by a space", which produces "…no eligible reviewer this pass Next run: …".
**Fix:** Use ` — ` for both lines, or name the separator explicitly for the verified line.

### IN-03: The `changed` marker covers rows whose card line never says "changed"

**File:** `plugins/vibe-check/scripts/batch_card.py:931-932`
**Issue:** `_marker_rows(…, "changed")` selects every row with a truthy `stale`, including `cause == "joined"`, whose card suffix reads "a new concern … joined it" and never mentions a change. "dismiss the changed rows" can therefore reach rows the owner did not see described that way.
**Fix:** Restrict the marker to `stale.cause in ("code", "nearby", "severity")`, or document that "changed" includes joined rows.

### IN-04: `test_close_out_drops_the_marker` cannot fail on the property its name claims

**File:** `plugins/vibe-check/scripts/test_fix_loop_card.py:1852-1862`
**Issue:** The test replaces `${original_args}` with the clean literal `49-foo`, so it passes whether or not `${original_args}` actually strips `--close-out-after-rerun`. The only real guard is the prose needle `test_original_args_holds`.
**Fix:** Build the args from a prior run that carries the marker (`_PRIOR_RUN_ON`), apply the documented strip through the real `00-scope.md` sed, and assert the result.

### IN-05: Finalize's echo is printed twice on the Finalize-to-fix-loop route

**File:** `plugins/vibe-check/phases/shared/90-finalize.md` ("otherwise" bullet); `plugins/vibe-check/phases/review/50-fix-loop.md:31`
**Issue:** 90-finalize now prints `echo_text` "before reading `50-fix-loop.md`". The subset bullet in 50-fix-loop still says "Then print Finalize's `echo_text` as message text", so the owner sees the same block twice.
**Fix:** Keep exactly one of the two instructions.

## Set aside (needs ruling)

### SA-01: Uncounted card markers decide every matching row, at any band

**Where:** `plugins/vibe-check/scripts/batch_card.py:926-937`, `:_resolve_one` marker branch
**Why excluded:** D-02/D-16 appear to allow a real card marker with no count, so this follows the letter of the rulings.
**Effect if left as is:** "dismiss the needs-verification ones -- fp" resolves to `dismiss <every NV row>` (verified: `dismiss 3 -- fp`), and "dismiss the criticals" dismisses every critical row, with no count and no confirm. This is equivalent to a bulk `all` over NV and critical rows, which the v2.12 by-number rule and D-04 forbid for `rest`/`all`.
**Needs:** A ruling from the developer: should band, pending, changed and absorbed markers require a stated count (as `remaining` effectively does for non-medium bands), or is description-by-marker acceptable?

### SA-02: The Bottom line suggestion can name critical rows for dismissal

**Where:** `plugins/vibe-check/phases/review/50-fix-loop.md:77-98`; `plugins/vibe-check/phases/shared/90-finalize.md:127-149`
**Why excluded:** The owner must type "bottom line" to accept it, and the parser gates the result.
**Effect if left as is:** The Bottom line is generated from diff-influenced report content. A suggestion such as `dismiss 1,2 -- false positive` naming critical rows is accepted by `parse` (they are named by number), so one short owner reply dismisses criticals on the strength of model-written reasoning.
**Needs:** A ruling: limit suggestions to `fix` clauses plus medium-only dismiss/defer, or accept the risk as is.

### SA-03: `--close-out-after-rerun` is an undocumented flag the user can type

**Where:** `plugins/vibe-check/phases/review/00-scope.md` (carrier `case` line)
**Why excluded:** It's an internal marker, but nothing rejects it on a first run.
**Effect if left as is:** A user who passes it by hand skips the pass-1 card and goes straight to Finalize. Finalize's gate still blocks, so nothing is lost.
**Needs:** A ruling: accept, or honor the marker only on an automatic Rerun.

---

_Reviewed: 2026-10-27_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: deep_
