---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 19
subsystem: batch_card resolve / suggest helper
tags: [gap-closure, final-round, D-21, title-match, subset-prior, mutants]
requires: [58-10, 58-11]
provides:
  - "REASON_PRIOR_SUBSET + _is_subset_doc: resolve refuses a rows --subset document as --prior-rows (WR-03(b))"
  - "_title_scores / _match_title / _title_candidates: best-unique-match title references with margin >= 1 and _TITLE_MIN_MATCH = 2; ties ask; weak -> none with likely rows (WR-02)"
  - "suggest builds its grammar with the one-line reason (IN-05)"
  - "s2 lock mutates the real module source in memory, no wrapper stand-in (IN-03)"
affects: [58-20, 58-21, 58-22]
tech-stack:
  added: []
  patterns: ["score-based title match with explicit margin + minimum", "in-memory source mutant via compile/exec for a guard the mock layer cannot reach"]
key-files:
  created:
    - .planning/phases/58-clear-actions-recovery-and-answers-acted-on/58-19-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/scripts/test_answer_resolve.py
    - plugins/vibe-check/scripts/test_bottom_line_suggest.py
decisions:
  - "A tied title reference lists at most four tied rows as candidates (the plan's 'deadline relay' case required the cut; its behavior block said 'unchanged shape')"
  - "Band words critical/warning/medium, needs/verification and the possessive fragment s are title filler"
metrics:
  duration: ~25m
  completed: 2026-10-27
  tasks: 3
  files: 3
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 19: Final-round helper fixes Summary

`resolve` now refuses a fix-subset rows file passed as the prior card, so the reviewer's scenario can no longer record `dismiss 5`. A title reference picks the single best-matching row only when that row clearly wins, and a tie or weak match still asks. `suggest` flattens the reason to one line. The s2 lock now mutates the real source. Every new guard was RED first and is killed by a mutant applied to the real `batch_card.py`.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | c4b270f | test(58-19): final-round RED -- subset rows as prior, best-unique title match, one-line suggest reason (WR-03, WR-02, IN-05, IN-03) |
| 2 | 074fe67 | fix(58-19): resolve refuses a subset rows file as the prior card; title refs pick the single best-matching row; suggest flattens the reason (WR-03, WR-02, IN-05) |
| 3 | (none) | Every real-file mutant was killed by the Task 1 tests, so no test file changed and nothing was committed |

## RED evidence (HEAD 54a3fe2, before batch_card.py changed)

Command: `pytest -q --tb=line scripts/test_answer_resolve.py -k "FinalRound or m7 or subset_refused"`. Result: 22 failed, 10 passed (failure counts include subtests). Suggest: `pytest -q --tb=line scripts/test_bottom_line_suggest.py -k "one_line or s2 or s4"`. Result: 2 failed, 2 passed.

| Test | First failure line on HEAD |
|------|----------------------------|
| test_subset_rows_as_prior_is_refused (WR-03b) | `AssertionError: {'ok': True, 'stale': True, ... 'verbs': {'fix': [], 'dismiss': [5], ...}, 'grammar': 'dismiss 5 -- fp', ...} is not None`. This is the defect: the subset row 1 was re-mapped to card row 5 and dismissed |
| test_cli_prior_rows_subset_refused | exit 0 (ok JSON) instead of exit 2 + REASON_PRIOR_SUBSET |
| test_reviewer_phrasings_resolve (WR-02) | all 7 subtests: `Tuples differ: ('none', []) != ('one', [n])` (4x row 5, 2x row 7, 1x row 1) |
| test_weak_match_is_none_with_likely_row | `AssertionError: 0 != 1` (none came back with no candidate) |
| test_adversarial_overlap_margin | `AttributeError: module 'batch_card' has no attribute '_title_scores'`; subtest "the deadline relay": `('none', []) != ('many', [1, 3, 4, 6])` |
| test_filler_only_still_none | `AssertionError: 'one' != 'none'`: "the warning" matched a title containing "Warning" |
| TestFinalRoundLockTrips m11/m12/m13/m16 "real" subtests | AttributeError (`_title_scores`, `_is_subset_doc`, `_title_candidates` absent) or the same check failures as above |
| test_reason_is_one_line (IN-05) | `'defer 8 -- line1\nline2\ttab' != 'defer 8 -- line1 line2 tab'` |
| test_s4_reason_not_flattened | "real" subtest fails on the same line. On HEAD `suggest` does not call `_one_line`, so the mutant cannot be told apart from the real code. This is IN-05's RED |

Green at RED (regression pins, recorded rather than claimed as reproductions):
- `test_verbatim_sentence_still_end_to_end` and `test_single_token_exact_still_matches`: green, as the plan expected.
- `test_multi_token_tie_is_many`: green. The plan expected a failure, but the old superset rule already returned `many` for "browse recovery" when two titles held both words. It stays as the tie pin, and m10/m16 kill it.
- `test_m7_filler_not_stripped` (re-pointed): green. Its subject, the filler-only rule, was already in place.
- `test_s2_empty_refusal_dropped` (rewritten): green. IN-03 was a flaw in the test, not in the code. What matters is that the rewritten lock now trips on a mutant of the real source (see below).

GREEN: `pytest -q scripts/test_answer_resolve.py scripts/test_bottom_line_suggest.py scripts/test_batch_card.py`: 209 passed, 201 subtests passed, 0 failed.

## Real-file mutants (Task 3)

The driver is `scratchpad/mutants.py`. It applies each edit to the real `plugins/vibe-check/scripts/batch_card.py` and runs `pytest -q -rA scripts/test_answer_resolve.py scripts/test_bottom_line_suggest.py`. It then runs `git checkout --` on the file and asserts `git status --porcelain` is empty before the next mutant. Final status: clean, and the file is byte-identical to 074fe67.

| ID | Edit on the real file | Failed (incl. subtests) | Failing tests |
|----|----------------------|-------------------------|---------------|
| m10 | tie broken by first row: `return best[:1]` when `len(best) >= 2` | 11 | test_adversarial_overlap_margin, test_multi_token_tie_is_many, test_m10, test_m16, test_ambiguous_title_many, test_m2_many_treated_as_one |
| m11 | minimum dropped: unique top accepted when `top >= 1` | 3 | test_weak_match_is_none_with_likely_row, test_m11, test_m13 |
| m12 | subset prior accepted: `_is_subset_doc` returns False | 3 | test_subset_rows_as_prior_is_refused, test_m12, test_cli_prior_rows_subset_refused |
| m13 | none candidates dropped: `_title_candidates` returns `[]` | 3 | test_weak_match_is_none_with_likely_row, test_m11, test_m13 |
| m14 | suggest reason not flattened: `_one_line(` removed | 2 | test_reason_is_one_line, test_s4_reason_not_flattened |
| m15 | band words removed from filler (`critical`, `warning`, `medium`) | 1 | test_filler_only_still_none |
| m16 | tie broken by overlap ratio: single tied row with max `score / len(title tokens)` | 11 | **test_adversarial_overlap_margin**, test_multi_token_tie_is_many, test_m10, test_m16, test_ambiguous_title_many, test_m2_many_treated_as_one |

m15: following the plan checker's note, `test_filler_only_still_none` includes a fixture whose titles literally contain the band words: row 4 "Warning text duplicated in banner", row 3 "Critical section lock is never released" and row 2 "Medium-size buffer overflows on resize". With the band words filtered out, "the warning" names no row. With m15 applied, it resolves to `one [4]` and the test fails. The kill was observed on the real file in the first run, so the band-word filler is load-bearing, not decorative.

In-test mutants (mock layer, inside `TestFinalRoundLockTrips`): m10, m11, m12, m13 and m16 each assert that the real check passes and the mutated check raises. s2 is now an in-memory source mutant: the real `batch_card.py` source with the `if not clauses:` guard removed, compiled into its own namespace. That mutated `suggest` returns `(None, batch_parse.REASON_EMPTY)` and trips `check_all_dropped_refuses`. s4 patches `_one_line` to leave line breaks in place.

## Safety property (WR-02)

`_match_title` returns one row only when the top score beats the runner-up by at least 1 AND reaches `_TITLE_MIN_MATCH` (2), or covers every word of a one-word reference. A tie returns the tied rows (`many`), and nothing breaks it. On the adversarial pair (row 4 retitled "Relay budget reset after failover"), every overlap with margin 0 asks: "the relay budget reset" (3 vs 3), "a relay after" (2 vs 2 vs 2), "relay reset" and "the deadline relay" (six rows at 1, four listed). Margin-1 cases pick the row a person would mean: "the retry relay budget reset" picks 7, and "failover budget" and "the relay failover budget" pick 4. The test checks the property generically via `_title_scores`.

## Verification

- Full suite (`pytest -q` from plugins/vibe-check): **3558 passed, 0 failed** (was 3542, +16 tests).
- `grep -c REASON_PRIOR_SUBSET scripts/batch_card.py` = 3. No `import re` or `import unicodedata`; `test_import_set` passes.
- `git diff --stat 24dccdc..HEAD -- scripts/score.py scripts/batch_parse.py`: empty.
- The earlier title tests (`test_ambiguous_title_many`, `test_title_none`, `test_title_words_in_any_order_case_folded`, `test_filler_words_do_not_block_match`, `test_fragment_inside_a_word_is_none`, `test_filler_only_text_is_none`, `test_title_tokens_are_punctuation_insensitive`) pass without changes.
- STATE.md and ROADMAP.md were not touched.

## Deviations from Plan

**1. [Rule 1 - Bug] A tied title reference lists at most four candidates**
- **Found during:** Task 2
- **Issue:** The plan conflicted with itself. The behavior block said a `many` result keeps its candidates in the "unchanged shape" (every tied row), but the adversarial "the deadline relay" case required the list cut to 4 (`[1, 3, 4, 6]`).
- **Fix:** `many` title results list the tied rows, in order, capped at `_TITLE_CANDIDATES_MAX = 4`. `prior_number` and marker results are unchanged.
- **Cost if wrong:** on a tie across more than 4 rows, the follow-up lists only the first 4. `ok` is still false, so nothing is acted on; the owner just sees a shorter list.
- **Files modified:** plugins/vibe-check/scripts/batch_card.py
- **Commit:** 074fe67

**2. [Plan adaptation] The CLI helper is `_resolve`, not `_run`**
- **Found during:** Task 1. The plan called `TestResolveCli._run`, but that class's helper is `_resolve`; `_run` belongs to `TestResolveCliContract`. The new CLI test uses `_resolve` with `rows=iplayarr_rows(at_pass=4)`.
- **Cost if wrong:** none. The test exercises the same CLI path.

**3. [Test shape] Many/none assertions go through candidates**
- Following the checker's note, `title_status` returns `rows == []` for `many`/`none`, so the adversarial cases compare `candidate_numbers(ref)` rather than a literal `("many", [4, 7])` tuple.
- **Cost if wrong:** none.

## Assumption Drift (advisory)

- **Found during:** Task 1 RED. **Planned:** every TestFinalRound test except two would fail, and the rewritten s2 would fail. **Actual:** `test_multi_token_tie_is_many`, the re-pointed m7 and the rewritten s2 were already green on HEAD. **Why:** the superset rule already reported two-title ties as `many`, and IN-03 was about how well the test guarded, not about a code defect. **Cost if wrong:** low. Each of these tests is now proven by a mutant: m10/m16 kill the tie pin, the source mutant trips s2, and the filler mutant trips m7.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/batch_card.py, test_answer_resolve.py, test_bottom_line_suggest.py
- FOUND: c4b270f, 074fe67
