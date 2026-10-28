---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 15
subsystem: fix-loop-card
tags: [gap-closure, fix-loop, translate, title-matching, count-needed, bottom-line, suggest, prose-locks]
requires:
  - "58-10 (whole-token filler-insensitive title rule, count_needed status, WR-04 REST_TWICE pin)"
  - "58-11 (batch_card.py suggest --rows --answer)"
  - "58-14 (printed paths, answer-file lifecycle)"
provides:
  - "Translate writes the owner's title words verbatim and states the helper's whole-word / filler rule (WR-03 prose half)"
  - "Ask only what is missing: parser-refusal bullet (every ref clear, parse_reason set) -> full-card fallback (WR-04)"
  - "Ask only what is missing: count_needed bullet, header \"How many\" (D-18)"
  - "D-09 Bottom line goes through batch_card.py suggest; dismiss/defer kept for medium rows only (D-19)"
affects:
  - "58-17 (Finalize side of the same four changes; test_finalize_card.py still pins Finalize's parse dry-run)"
  - "58-18 (gate checks 90-finalize.md and 50-fix-loop.md agree)"
tech-stack:
  added: []
  patterns: ["RED prose locks then prose", "real-file mutant table", "fresh-shell fence walk with printed literals"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/scripts/test_fix_loop_card.py
decisions:
  - "The filler words named in the Translate prose are cross-checked against batch_card._TITLE_FILLER, so the prose can never list a word the helper does not ignore"
  - "The WR-04 bullet names the exact batch_parse.REASON_REST_TWICE text as the 'combined two bulk groups' case; any other parse_reason gets 'could not be checked'"
  - "A count_needed ref is completed by keeping its marker and adding \"count\": C, or by number refs when the owner gave row numbers"
metrics:
  duration: ~20m
  completed: 2026-10-27
  tasks: 3
  files: 2
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 15: Fix-loop Translate / Ask / Bottom line in line with the helper Summary

The fix-loop prose now matches what the helper does after 58-10 and 58-11:

- **Title words (WR-03).** Translate passes the owner's title words as `text` verbatim. It states the helper's rule: whole words only, with filler such as "the" or "issue" ignored. So "the Browse recovery issue" names the Browse recovery row, and `port` never matches `import`.
- **Parser refusal (WR-04).** Some answers resolve every reference clearly, but the parser still refuses the grammar built from them. "Ask only what is missing" now sends those straight to the full-card fallback.
- **Serious groups (D-18).** A described group that would dismiss or defer critical, warning or Needs-verification rows gets a "How many" question.
- **Bottom line (D-19).** The suggestion line is built by `batch_card.py suggest`. It keeps `dismiss`/`defer` for medium rows only, so typing "bottom line" can never dismiss or defer a serious row.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | RED: `title_rule_problems`, `parse_refusal_branch_problems`, `count_needed_problems`, `suggest_fence_problems` + `TestGapRoundTranslate`; `bottom_line_problems` needle -> suggest; `FOLLOWUP_HEADERS` + `header "How many"` | 1e63a4c | scripts/test_fix_loop_card.py |
| 2 | Prose: verbatim title text, parser-refusal bullet, How many bullet, suggest fence | 0911d07 | phases/review/50-fix-loop.md |
| 3 | Real-file mutants T5-T8 + verbatim V1 walk | none (all mutants killed, no needle added; see Deviations) | — |

## RED evidence (Task 1, prose at 96ad122)

`pytest -q --tb=no scripts/test_fix_loop_card.py -k "GapRoundTranslate or bottom_line or followup"` gave **15 failed, 6 passed** (subtests counted). The failures:

- all four new `_holds` tests: title_rule, parse_refusal_branch, count_needed, suggest_fence
- all four `_mutant` tests, because their baseline text is not in the prose yet
- `TestPhase58Prose::test_bottom_line_holds` (the suggest needle)
- `TestPhase58Routing::test_followup_holds` (the How many header)

Problems the locks reported on the unchanged prose:
- `title_rule_problems`: every TITLE_RULE needle missing; the unqualified `"text": "<the owner's words>"}` form still present; no filler list
- `parse_refusal_branch_problems`: Ask paragraph lacks the parser-refusal bullet
- `count_needed_problems`: Ask paragraph lacks the count_needed bullet
- `suggest_fence_problems`:
  - the D-09 paragraph lacks the suggest call
  - it lacks the D-19 scope sentence and "still needs your own words"
  - the parse dry-run of the suggestion is still there

## GREEN (Task 2)

- `pytest -q scripts/test_fix_loop_card.py scripts/test_card_text.py scripts/test_pause_batching.py`: **174 passed, 265 subtests passed**.
- All 11 test files that read `50-fix-loop.md` (carry_state, carry_writers, card_text, confirmed_fix, fixcommit, finalize_card, fix_loop_card, foreground_dispatch, scope_args, pause_batching, tracecheck): **721 passed, 1614 subtests passed**.
- Acceptance greps on `50-fix-loop.md`:

| Grep | Count |
|---|---|
| `suggest --rows "$ROWSFILE" --answer "$SUGGESTFILE"` | 1 |
| `parse --rows "$ROWSFILE" --answer "$SUGGESTFILE"` | 0 |
| `` `count_needed` `` | 2 |
| `` parse_reason` is set `` | 1 |
| `the Browse recovery issue` | 1 |

The suggest fence as landed:

```bash
if python3 "$VC_ROOT/scripts/batch_card.py" suggest --rows "$ROWSFILE" --answer "$SUGGESTFILE" > "$SUGGESTFILE.tmp" && mv "$SUGGESTFILE.tmp" "$SUGGESTFILE"; then
  cat "$SUGGESTFILE"
else
  rm -f "$SUGGESTFILE" "$SUGGESTFILE.tmp"
  echo "Bottom line suggestion refused — the card shows no suggestion line" >&2
fi
```

## Real-file mutants (Task 3)

Driver: `scratchpad/mutants_58_15.py`. For each mutant it wrote the edit to the real `50-fix-loop.md` and ran `pytest -q --tb=no scripts/test_fix_loop_card.py`. It then ran `git checkout --` on the file and asserted `git status --porcelain` was empty. The file was clean after every mutant and at the end.

| ID | Mutant on the real file | Result | Failing tests |
|----|-------------------------|--------|---------------|
| T5 | restore `"text": "<the owner's words>"}` (drops the verbatim rule clause) | 4 failed | test_title_rule_holds, test_mutant_title_rule[old text form], [rule dropped], [filler the helper keeps] |
| T6 | delete the WR-04 parser-refusal bullet | 2 failed | test_parse_refusal_branch_holds, test_mutant_parse_refusal_branch |
| T7 | delete the `count_needed` bullet | 3 failed | test_count_needed_holds, test_followup_holds, test_mutant_count_needed |
| T8 | restore the `parse … > /dev/null` dry-run call in the D-09 fence | 4 failed | test_suggest_fence_holds, test_bottom_line_holds, test_mutant_suggest_fence, test_mutant_suggest_fence[parse dry-run restored] |

Every mutant failed at least one test, so none survived. The in-file `_mutant` tests also cover these edits on a copy of the card: a filler word the helper keeps (`of`), the else arm leaving the tmp file behind, and the D-19 scope sentence being dropped.

## V1 walk: the owner's verbatim sentence, no follow-up

Driver: `scratchpad/walk_58_15.py`. It took the fences from the real `50-fix-loop.md` and ran each in its own `bash -s`, with only `PATH`, `VC_ROOT` and `TMPDIR` (the scratchpad) set. It substituted the printed `NAME=` literals for `"$NAME"`. The rows doc was the eight-row `test_answer_resolve.iplayarr_rows()` fixture. The driver wrote the answer and refs files with Python, standing in for the Write tool, so no owner text went on a command line.

Owner's Other text (verbatim): `fix the Browse recovery issue, then dismiss the 7 fixed rows and close out`

| Step | Fence | Observed |
|------|-------|----------|
| A | ordinary rows fence, create+print lines | exit 0; `ROWSFILE=…/vc.voLjv5`, `ANSWERFILE=…/vc.HpFK4Q` (fixture copied into ROWSFILE) |
| B | parse fence on `{"q1": <owner text>, "q2": null}` | `refused: answer does not match the grammar` → "nothing was recorded" (not `empty answer`, so → Translate) |
| C | Translate create fence | exit 0; `REFSFILE=…/vc.4Gusfu`, `RESOLVEFILE=…/vc.gyBj71` |
| D | refs as the new prose instructs: `{"refs": [{"verb": "fix", "kind": "title", "text": "the Browse recovery issue"}, {"verb": "dismiss", "kind": "marker", "marker": "remaining", "count": 7}], "reason": "fixed (owner: \"dismiss the 7 fixed rows\")", "close_out": true}` → resolve fence | exit 0; `"ok": true`, `"close_out": true`, refs `one [5]` and `one [1,2,3,4,6,7,8]`, `"grammar": "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: \"dismiss the 7 fixed rows\")"`, `parse_reason` null |
| E | grammar copy fence | exit 0; ANSWERFILE = `{"q1": "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: \"dismiss the 7 fixed rows\")", "q2": null}` |
| F | the same parse fence | exit 0; `"ok": true`; one fix target, seven dismiss hashes |

The echo for the ok-true branch, built from `echo_text`:

```
Read your answer as: fix: #5 src/browse/recovery.ts:118
dismiss: #1 src/endpoints/sabnzbd/AddFileEndpoint.ts:204, #2 src/service/browse/ArrDiscoveryHandoffService.ts:201, #3 src/utils/integrationDeadline.ts:60, #4 frontend/src/views/BrowseProgrammePage.vue:406, #6 src/service/arr/V3ArrService.ts:412, #7 src/relay/budget.ts:33, #8 src/facade/arrFacade.ts:80
Reason: fixed (owner: "dismiss the 7 fixed rows")
```

`ok` was true and `close_out` was true in this step's printed resolve output, so the answer is acted on with no confirm card and no second card. It goes to step 2 (Step B, then the Rerun with the close-out marker).

## Full suite

A bare `pytest -q` from `plugins/vibe-check` gave **3534 passed, 4692 subtests passed**, 0 failed. That is 3526 before plus the 8 new `TestGapRoundTranslate` tests. `git diff --stat 24dccdc..HEAD -- batch_parse.py score.py` is empty.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Consistency] WR-04 bullet reads "When every ref is …" instead of "Every ref is …"**
- **Found during:** Task 2
- **Issue:** Task 1's lock needle is lowercase ("every ref is `one` or `bulk`, …"). The Task 2 prose text started the bullet with "Every". The two could not both hold exactly.
- **Fix:** I kept the lock needle as specified and wrote the bullet as "- When every ref is …". The parse_reason note quotes the exact `refused: 'rest' may appear in only one clause` text, and the lock pins it to `batch_parse.REASON_REST_TWICE`.
- **Cost if wrong:** one word of prose. The meaning is unchanged.
- **Commit:** 0911d07

**2. [Rule 2 - Correctness] Extra cross-checks in the locks**
- **Found during:** Task 1
- **Issue:** The planned needles would not catch two drifts. The prose could list a filler word the helper still matches. The WR-04 bullet could drop the exact refusal it describes.
- **Fix:** `title_rule_problems` checks every word in the prose's filler list is in `batch_card._TITLE_FILLER`, which needs a new `import batch_card` in the test file. `parse_refusal_branch_problems` requires `REASON_REST_TWICE` text in the bullet. `count_needed_problems` requires the completed-refs sentence to say how a `count_needed` ref is completed. `suggest_fence_problems` also requires the fence to `cat` the trimmed file. Each check has a subtest mutant, or is covered by T5-T8.
- **Cost if wrong:** more needles to update if the wording changes.
- **Commit:** 1e63a4c

**3. [Scope] Task 3 produced no commit**
- **Found during:** Task 3
- **Issue:** Like 58-14, Task 3 only adds a needle when a mutant survives. All four were killed on the first run. The walk is evidence recorded in this SUMMARY, not a test.
- **Fix:** No test change. Evidence is recorded here.
- **Cost if wrong:** none. No code changed.

## Known Stubs

None. The Finalize side (`90-finalize.md` and its `test_finalize_card.py` pin of `parse --rows "$ROWSFILE" --answer "$SUGGESTFILE"`) is 58-17's scope and was left untouched.

## Threat Flags

None. This change is prose and tests only. Owner text still reaches helpers only through files written with the Write tool.

| Threat | Disposition | Evidence |
|---|---|---|
| T-58-46 | mitigated | verbatim rule + helper whole-word matching; mutant T5 |
| T-58-47 | mitigated | WR-04 bullet → fallback; mutant T6 |
| T-58-48 | mitigated | How many (D-18), suggest fence (D-19); mutants T7, T8 |

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/50-fix-loop.md (modified)
- FOUND: plugins/vibe-check/scripts/test_fix_loop_card.py (4 `def *_problems` helpers added: grep count 4)
- FOUND: 1e63a4c, 0911d07
- STATE.md / ROADMAP.md / HANDOFF.json not touched by this plan
