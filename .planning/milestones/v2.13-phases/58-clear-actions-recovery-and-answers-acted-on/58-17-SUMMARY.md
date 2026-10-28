---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 17
subsystem: finalize-card
tags: [gap-closure, finalize, translate, title-matching, count-needed, bottom-line, suggest, prose-locks]
requires:
  - "58-10 (whole-word, filler-ignoring title rule; count_needed status; REASON_REST_TWICE)"
  - "58-11 (batch_card.py suggest --rows --answer)"
  - "58-15 (the fix-loop wording this plan copies)"
  - "58-16 (Finalize printed paths and answer-file lifecycle)"
provides:
  - "Finalize Translate writes the owner's title words verbatim and states the helper's whole-word / filler rule (WR-03 prose half)"
  - "Finalize Ask only what is missing: parser-refusal bullet -> full-card fallback (WR-04)"
  - "Finalize Ask only what is missing: count_needed bullet, header \"How many\", a Q2 pick never supplies a count (D-18)"
  - "Finalize D-09 Bottom line goes through batch_card.py suggest (D-19)"
affects:
  - "58-18 (gate checks that 90-finalize.md and 50-fix-loop.md agree)"
tech-stack:
  added: []
  patterns: ["RED prose locks then prose", "real-file mutant table", "twin-wording diff against the fix loop"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "The four Finalize passages are copied byte-for-byte from 50-fix-loop.md. The one Finalize-only addition is \"(a Q2 pick never supplies a count)\" at the end of the count_needed bullet. The needs_reason bullet keeps its existing Q2 sentence."
  - "Finalize's title rule says \"a title or title words\", the same as the fix loop. The old \"distinctive title words\" wording is gone."
metrics:
  duration: ~15m
  completed: 2026-10-27
  tasks: 3
  files: 2
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 17: Finalize Translate / Ask / Bottom line twin of the fix loop Summary

When the owner types a plain-English answer on the Finalize card (Mixed… or Other), it is now handled the same way as on the fix-loop card:

- **Title words (WR-03).** The words the owner uses to name a row are passed on exactly as typed. The helper matches whole words and ignores filler such as "the" or "issue". So `port` never matches `import`.
- **Parser refusal (WR-04).** Sometimes every reference in the answer is clear but the parser still refuses the result. That case now goes straight to the full card, with a note saying why.
- **Serious groups (D-18).** If a described group would dismiss or defer critical, warning or Needs-verification rows, Finalize asks "How many" first. A Q2 pick never counts as that number.
- **Bottom line (D-19).** The suggestion line is now built by `batch_card.py suggest`. It keeps dismiss/defer for medium rows only.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | RED: `check_title_rule`, `check_parse_refusal_branch`, `check_count_needed`, `check_suggest_fence` + `TestGapRoundFinalizeTranslate`. `BOTTOM_NEEDLES` now pins `suggest` instead of `parse`. `FOLLOWUP_NEEDLES` gains `header "How many"` | 2e81b59 | scripts/test_finalize_card.py |
| 2 | Prose: verbatim title text, parser-refusal bullet, How many bullet, suggest fence | 140219f | phases/shared/90-finalize.md |
| 3 | Real-file mutants M13-M16 | none (all four failed the tests on the first run, so no needle was added; see Deviations) | — |

## RED evidence (Task 1, prose at ad94887)

`pytest -q --tb=no scripts/test_finalize_card.py -k "GapRoundFinalizeTranslate or bottom_line or followup"` gave **15 failed, 3 passed**. Subtest failures are included in the 15. The failures:

- All four new `_holds` tests: title_rule, parse_refusal_branch, count_needed, suggest_fence.
- All four `_mutant` tests. Their baseline text was not in the prose yet. This includes subtests [old text form], [rule dropped], [filler the helper keeps], [parse dry-run restored], [else keeps the tmp file] and [scope sentence dropped].
- `TestPhase58Finalize::test_bottom_line_holds`: the needle now pins `suggest`.
- `TestPhase58FinalizeRouting::test_followup_holds`: the How many header was missing.

`90-finalize.md` was not changed in commit 2e81b59.

## GREEN (Task 2)

- `pytest -q scripts/test_finalize_card.py scripts/test_card_text.py scripts/test_pause_batching.py scripts/test_finalize_archive_prose.py` gave **125 passed, 250 subtests passed**.
- I also ran all 11 test files that read `90-finalize.md`: card_text, carry_state, confirmed_fix, finalize_card, fixcommit, carry_writers, scope_args, finalize_archive_prose, score, pause_batching, tracecheck. Result: **1116 passed, 1873 subtests passed**.
- Acceptance greps on `90-finalize.md`:

| Grep | Count |
|---|---|
| `suggest --rows "$ROWSFILE" --answer "$SUGGESTFILE"` | 1 |
| `parse --rows "$ROWSFILE" --answer "$SUGGESTFILE"` | 0 |
| `` `count_needed` `` | 2 |
| `` parse_reason` is set `` | 1 |
| `the Browse recovery issue` | 1 |

- Twin diffs against `50-fix-loop.md` (58-15 has landed). Each one was empty:
  - `ignoring filler.*names the Browse recovery row`
  - the WR-04 bullet
  - the `count_needed` bullet up to `number` refs for the chosen rows
  - the D-19 sentence `then run it through \`suggest\`…never which):`
  - the suggest fence plus the six lines after it

  The only wording difference is the Finalize-only clause "(a Q2 pick never supplies a count)".
- Two Finalize-only sentences in D-09 are unchanged: "re-translated against THIS card's rows" and "ONLY when THIS session rendered the last pass's Bottom line". Finalize still never writes the close-out marker; the `check_translate_path` close-out lock still passes.

## Real-file mutants (Task 3)

The driver is `scratchpad/mutants_58_17.py`. For each mutant it:

1. wrote the edit to the real `90-finalize.md`
2. ran `pytest -q --tb=no -rf scripts/test_finalize_card.py`
3. ran `git checkout --` on the file in a `finally` block
4. asserted that `git status --porcelain` for the file was empty

The file was clean after every mutant. At the end the only change in the tree was the pre-existing `.planning/HANDOFF.json`.

| ID | Mutant on the real file | Result | Failing tests |
|----|-------------------------|--------|---------------|
| M13 | restore `"text": "<the owner's words>"}` and drop the rule clause | 4 failed | test_title_rule_holds, test_mutant_title_rule [old text form], [rule dropped], [filler the helper keeps] |
| M14 | delete the WR-04 parser-refusal bullet | 2 failed | test_parse_refusal_branch_holds, test_mutant_parse_refusal_branch |
| M15 | delete the `count_needed` bullet | 3 failed | test_count_needed_holds, test_followup_holds, test_mutant_count_needed |
| M16 | restore the `parse … > /dev/null` dry-run fence | 5 failed | test_suggest_fence_holds, test_bottom_line_holds, test_mutant_suggest_fence [parse dry-run restored], [else keeps the tmp file] |

Each mutant failed at least one test. The in-file `_mutant` tests also cover three edits made on a copy of the card:

- a filler word the helper keeps (`of`)
- the else arm leaving the tmp file behind
- the D-19 scope sentence or the Q2 count clause dropped

## Full suite

A bare `pytest -q` from `plugins/vibe-check` gave **3542 passed, 4699 subtests passed**, 0 failed. That is the 3534 from before plus the 8 new `TestGapRoundFinalizeTranslate` tests. `git diff --stat 24dccdc..HEAD -- batch_parse.py score.py` is empty.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] The locks check more than the plan's needles**
- **Found during:** Task 1
- **Issue:** The planned needles would miss three drifts:
  - the filler list naming a word the helper still matches
  - the WR-04 bullet dropping the exact refusal it describes
  - the completed-refs sentence not saying how a count_needed ref is completed
- **Fix:** I added the same cross-checks 58-15 uses:
  - the filler list is checked against `batch_card._TITLE_FILLER`
  - the bullet must contain the `batch_parse.REASON_REST_TWICE` text
  - the WR-04 bullet must come before the `blocked` bullet
  - the completed-refs sentence must mention `count_needed`
  - the suggest fence must `cat` the trimmed file

  `FOLLOWUP_NEEDLES` also gains `header "How many"`, as 58-15 did on its side. Each extra check has a subtest mutant or is covered by M13-M16.
- **Cost if wrong:** more needles to update when the wording changes.
- **Commit:** 2e81b59

**2. [Scope] Task 3 produced no commit**
- **Found during:** Task 3
- **Issue:** The plan named a `test(58-17): real-file mutants M13-M16` commit. Task 3 only adds a needle when a mutant survives, and all four failed the tests on the first run. That left nothing to commit, the same as 58-14 and 58-15.
- **Fix:** No test change. The evidence is the table above.
- **Cost if wrong:** none. No code changed.

**3. [Plan line refs] Anchors moved**
- The plan cited `check_bottom_line` at :1268 and `followup_paragraph` at :1295. They are at :409 and :436. I edited by symbol name, so nothing else changed.

## Known Stubs

None.

## Threat Flags

None. This plan changes prose and tests only. Owner text still reaches the helpers only through files written with the Write tool.

| Threat | Disposition | Evidence |
|---|---|---|
| T-58-49 | mitigated | verbatim rule + the helper's whole-word matching; mutant M13 |
| T-58-50 | mitigated | WR-04 bullet sends the answer to the fallback; mutant M14 |
| T-58-51 | mitigated | How many (D-18) and the suggest fence (D-19); mutants M15, M16 |

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md (modified)
- FOUND: plugins/vibe-check/scripts/test_finalize_card.py (`grep -c` for the 4 new `def check_*` helpers returns 4)
- FOUND: 2e81b59, 140219f
- This plan did not touch STATE.md, ROADMAP.md or HANDOFF.json.
