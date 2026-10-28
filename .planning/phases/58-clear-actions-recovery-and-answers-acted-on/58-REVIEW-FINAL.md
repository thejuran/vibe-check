---
phase: 58-clear-actions-recovery-and-answers-acted-on
reviewed: 2026-10-28T17:56:16Z
depth: deep
scope: final round only — git diff 54a3fe2..HEAD -- . ':!.planning/'
files_reviewed: 7
files_reviewed_list:
  - plugins/vibe-check/phases/review/50-fix-loop.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/batch_card.py
  - plugins/vibe-check/scripts/test_answer_resolve.py
  - plugins/vibe-check/scripts/test_bottom_line_suggest.py
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_fix_loop_card.py
findings:
  critical: 1
  warning: 0
  info: 3
  total: 4
status: issues_found
---

# Phase 58: Code Review Report (final round, D-21 single re-review)

**Reviewed:** 2026-10-28T17:56:16Z
**Depth:** deep
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Scope: only the final-round diff `54a3fe2..HEAD` (7 plugin files, +1023/-74).

How I checked:
- The 4 touched test modules pass: 319 passed, 356 subtests (bare `pytest`).
- I ran `resolve` and `suggest` on the iPlayarr eight-row fixture. I compared each result with the pre-round helper (`git show 54a3fe2:…/batch_card.py`, loaded side by side).
- I walked the printed fences in fresh `env -i bash -s` shells, carrying each path forward as a literal. The fences covered:
  - ordinary card, then typed `fix 2`, then the subset fence, then Step B's `payload`
  - the stale `resolve` twin, with the subset rows file and then the card rows file as prior
  - suggest, then the D-08 `rm -f`, then the typed-"bottom line" `cp`, then `parse`
- I traced every `ROWSFILE=` / `CARDROWSFILE=` / `$PRIORROWSFILE` reference in both card files.
- The convention checker returned no findings.

**Result.** All three warnings and all three info items are closed for the scenarios they described. The WR-02 fix, though, adds a new defect that is worse than the one it removed. The new best-unique title match acts on a row the owner did not name. Function words ("on", "and", "in", "is", "not", "after") count toward the score, and a one-word margin is enough to act. On the iPlayarr card this re-creates the incident sentence's exact shape, "fix X, then dismiss the other 7". The row the owner asked to fix gets **dismissed** as "fixed", with no confirm card, and close-out follows. The pre-round helper returned `none` for the same phrasings, so it asked instead.

Under D-21 this is the hard-stop case: it is recorded here and goes to the backlog as a known limit. It does not open another round.

## Closure check (58-REVIEW-GAPS.md items)

| Item | Verdict | Evidence on current code |
|---|---|---|
| WR-01: the D-08 fallback deleted the suggestion the re-shown card still offers | **CLOSED** | Both D-08 sentences now run `rm -f "$REFSFILE" "$RESOLVEFILE"` and "keep `$SUGGESTFILE`" (`50-fix-loop.md:216`, `90-finalize.md:217`). In a fresh-shell walk, `suggest` gave `{"q1": "fix 2; dismiss 6 -- out of scope"}` with stderr `suggestion trimmed: 1 serious row(s) dropped`. The D-08 `rm -f` then exited 0, and the typed-"bottom line" `cp "$SUGGESTFILE" "$ANSWERFILE"` also exited 0 (it exited 1 before). `parse` accepted the copy: `fix: #2 …`, `dismiss: #6 …`, `Reason: out of scope`. The suggestion line's condition is now "the `suggest` fence exited 0" (`50-fix-loop.md:73` / `90-finalize.md:118`). **Can a stale suggestion reach a different card?** I traced every way off the fallback card. Apply all and Apply selected… go through Step B and the Rerun (the Rerun deletes it). Skip & rerun and "fix by hand" go to the Rerun. Close out deletes it. Finalize steps 2 and 3 delete it. `look`, need_text and empty-answer re-shows show the same card. Abandon leaves the file, but every later card prints a new `SUGGESTFILE=`, and the typed path requires "a `Bottom line suggests:` line … printed on the card currently shown". No route carries it onto a different card. |
| WR-02: ordinary phrasing got a follow-up | **CLOSED for the listed phrasings**, but see **CR-01** | All 7 `REVIEWER_PHRASINGS` resolve to one row. "the retry budget warning" gives #7. "the Browse recovery issue from earlier" gives #5. Ties ("the relay one" gives `many` [1, 7]) and weak matches still ask. The verbatim iPlayarr sentence still gives `fix 5; dismiss 1,2,3,4,6,7,8`. |
| WR-03: the stale re-map could bind the subset rows file | **CLOSED** | Helper: `resolve --prior-rows <subset ROWSFILE>` gives `refused: prior rows file is a fix subset, not a card` with exit 2. With the card's rows file as prior, the same refs give `dismiss 1 -- fp`, `ok`. Prose: the ordinary fence prints `CARDROWSFILE=` (`50-fix-loop.md:43`). The subset fence does not (`:23-27`). Finalize's rows fence does (`90-finalize.md:83`). Both Stale card paragraphs bind `$PRIORROWSFILE` only to a `CARDROWSFILE=` path, "never a path printed only after `ROWSFILE=`". No remaining text binds `$PRIORROWSFILE` from `ROWSFILE=`, and nothing reads `$CARDROWSFILE`. **Step B on both subset routes:** I ran the typed-`fix 2` route as ordinary fence, then subset fence, then `payload --rows <subset ROWSFILE>`. It sent exactly one hash (`2a01829c60…`, the chosen row). The Finalize-routed route runs only the subset fence, which prints `ROWSFILE=` with no `CARDROWSFILE=`, so Step B binds the same subset file. `TestSubsetDispatchWalk` (4 tests) covers both routes and the Step-B-on-card mutant. |
| IN-01: trimmed suggestion not disclosed | **CLOSED** | Both "Exit 0" sentences append ` (N row(s) the Bottom line would dismiss or defer need your own words)`, keyed on the `SUGGEST_TRIMMED` stderr prefix, which matches the helper's string. The note gives the count only. |
| IN-03: decorative s2 mutant | **CLOSED** | `test_s2_empty_refusal_dropped` now compiles the real module source with `if not clauses:` removed and checks that `check_all_dropped_refuses` fails against it. This is no longer a self-patch. |
| IN-05: `suggest` reason not flattened | **CLOSED** | `suggest(…, "defer 8 -- line1\nline2\ttab")` gives `defer 8 -- line1 line2 tab`. |

## Critical Issues

### CR-01: The best-unique title match acts on the wrong row. In the incident sentence's shape, it dismisses the row the owner asked to fix

**File:** `plugins/vibe-check/scripts/batch_card.py:898-903` (`_TITLE_FILLER` comment: "prepositions are not filler and count as words"), `:961-990` (`_title_scores`, `_match_title`), `:1095-1103`; prose `50-fix-loop.md:171`, `90-finalize.md:172`

**Issue:** `_match_title` acts when one row has the highest score, is at least 1 ahead of the next row, and the score is at least 2. The score counts every distinct non-filler word, and the filler list leaves out prepositions, conjunctions and auxiliaries ("on", "and", "in", "is", "not", "after"). It also never checks how many of the owner's words the picked row lacks. So when the owner's distinctive words miss their row by inflection or synonym ("list" vs "lists", "gating" vs "gate"), a different row whose title shares two incidental or location words wins outright. A `one` title ref names its row by number, so it acts at **any band** (D-18 covers only described groups), and the `ok` branch acts with no confirm card.

Reproduced on the iPlayarr eight-row fixture. The pre-round helper (54a3fe2) returns `none` for each of these, so it asked:

| Owner's words (title ref) | Meant | Scores | Picked |
|---|---|---|---|
| "the option list on the browse page" | #4 "Gate only the option lists required by the selected operation" (`BrowseProgrammePage.vue`) | #4=1 (option), #5=2 (browse, page) | **#5** "Browse recovery leaves a stale cursor…" |
| "the deadline expiry on add and search" | #6 "Handle search-existing deadline expiry as an uncertain write" | #6=3, #8=4 (deadline, **add**, **and**, search) | **#8** (medium test-gap row) |

End-to-end in a fresh `bash -s`, using the printed resolve fence, then the grammar copy, then `parse`: refs `dismiss` / "the option list on the browse page" gives `ok: true`, grammar `dismiss 5 -- false alarm (…)`. `parse` accepts it with payload `1 dismiss`, echo `dismiss: #5 src/browse/recovery.ts:118`. A warning the owner never mentioned is recorded as dismissed.

The incident shape is worse. With refs `fix` title + `remaining` count 7, `close_out` true, as in "fix the option list on the browse page, then dismiss the other 7 fixed rows and close out":

```
the option list on the browse page     -> ok True  fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (…)  close_out True
the deadline expiry on add and search  -> ok True  fix 8; dismiss 1,2,3,4,5,6,7 -- fixed (…)  close_out True
```

The row the owner asked to fix (#4, or #6, both warnings) is **dismissed** with the reason "fixed". The fix agent works on a different row, and the D-17 carry takes the session straight to Close out. The dismissal is recorded before the echo is seen. Under Phase 57 it does not reopen while the code is unchanged, so Finalize's gate counts that warning as decided and can write REVIEW.md with it unfixed. Two things carry the "fix X, dismiss the other N" pattern: the D-16 counted remainder, which names rows by number at any band, and the count check. Because the title ref claimed the wrong row, the count still matches. This is the D-02/D-05 failure the phase was meant to remove, a misread answer acted on, and it is worse than a repeated card.

The tests pass because every fixture phrase either contains the target's words exactly or ties. None places the target's distinctive word next to two words from another title.

**Fix:** Keep WR-02's aim (likely row first, few follow-ups), but act only on a match that cannot be another row's:
```python
# act on a title ref only when the best row holds EVERY non-filler word
# (the old superset rule, with band words / possessive `s` / function
# words now in _TITLE_FILLER); a best-but-partial row becomes the follow-up's
# first candidate instead of a pick.
_TITLE_FILLER |= {"on", "in", "at", "of", "to", "for", "and", "or", "is",
                  "are", "not", "after", "before", "with", "from", "by",
                  "you", "flagged", "mentioned", "earlier", "about"}
def _match_title(rows, text):
    wanted = _title_wanted(text)
    if not wanted:
        return []
    return [r for r in rows if wanted <= set(_title_tokens(r.get("title")))]
# and in _resolve_one, for `none`: candidates=_title_candidates(rows, text)
# (best partial row first; with exactly one, the D-06 "Which row" card adds
# "None of these", so the likely row is a single click).
```
At minimum, if the scoring rule stays, do not act on a non-superset pick when the answer also holds a `dismiss`/`defer` clause or a `remaining` ref. Return it as `none` with the picked row as the first candidate. Add fixtures for both rows above, the `fix` + `remaining` count 7 shape included, and a mutant that restores the margin-1 pick.

## Info

### IN-01: Title-ref ties are cut to 4 candidates, so the prose's ">4 → list the labels" rule never fires and tied rows are dropped silently

**File:** `plugins/vibe-check/scripts/batch_card.py:1100-1102`; `50-fix-loop.md:209` / `90-finalize.md:210` ("More than 4 candidates → list the labels in the question text")
**Issue:** `many` returns `matched[:_TITLE_CANDIDATES_MAX]`. In the repo's own overlap fixture, "the deadline relay" ties six rows (1, 3, 4, 6, 7, 8) and lists only [1, 3, 4, 6]. If the owner meant #7 or #8, that row is not a button and is not named in the question. The owner can still type it through Other, so this fails safe.
**Fix:** Return every tied row, as `_resolve_one` does for other `many` results, and let the prose's >4 rule list them. Or note in the question that more rows matched.

### IN-02: On a D-17 carried pass, Close out's "this pass's rows file, whose printed `CARDROWSFILE=` path is Finalize's source" points at a card that was never shown

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:221` (Close out), `:14` (D-17 carry)
**Issue:** On a carried close-out pass the card is not rendered, and the owner last read the previous pass's card. The Close out sentence still names "this pass's" `CARDROWSFILE=` as Finalize's re-map source. If the model runs the ordinary rows fence on that pass, it prints a `CARDROWSFILE=` for an unrendered card, and the two files disagree. Finalize's own Stale card text ("the ordinary fence that rendered the card the owner read", `90-finalize.md:199`) settles it correctly, so this is a wording inconsistency rather than a reproduced misbinding.
**Fix:** Change Close out's sentence to "keep the rows file of the card the owner last read (its `CARDROWSFILE=` path)". Optionally, in the D-17 paragraph, add "do not run the rows fence on this pass".

### IN-03: The `REASON_PRIOR_SUBSET` refusal reaches a full-card fallback whose note has no source

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:209-216`; `plugins/vibe-check/phases/shared/90-finalize.md:210-217`
**Issue:** A `resolve` refusal goes "straight to the full-card fallback", whose note is "built from the resolve output". A refusal produces no output, so the note is unspecified. The no-prior-path case has its own note ("your numbers refer to an earlier card that is no longer available"); the subset refusal, which also means "no usable prior card", does not. The refusal string itself contains no owner text, and nothing is recorded, so this fails safe.
**Fix:** Route a `refused: prior rows file is a fix subset, not a card` refusal to the same "earlier card … no longer available" note.

## Set aside (needs ruling)

None. As instructed, I did not re-report the declared known limits (IN-02 "How many" buttons, IN-04 Unicode normalization, inflected words, 999.25 `$BLOBFILE`).

**D-21 disposition:** CR-01 is at or above warning level, so under D-21 Phase 58 closes with CR-01 documented as a known limit in the backlog, and no further round runs. Recommended backlog wording: *"A title reference can pick a row that shares only incidental or location words with the owner's phrase. In a 'fix X, dismiss the other N' answer, the row the owner asked to fix is then dismissed with no confirm. Pre-round behavior (ask) is safe; fix by restoring the superset rule for acting and offering the best partial row as a one-click candidate."*

---

_Reviewed: 2026-10-28T17:56:16Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: deep_
