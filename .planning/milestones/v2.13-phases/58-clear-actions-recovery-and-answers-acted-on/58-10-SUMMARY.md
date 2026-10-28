---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 10
subsystem: vibe-check batch_card resolve
tags: [gap-closure, resolve, title-matching, D-18, WR-03, WR-04, IN-03]
requires: [58-03 resolve contract]
provides: [whole-token filler-insensitive _match_title, cause-restricted changed marker, count_needed status, WR-04 REST_TWICE fixture]
affects: [58-15, 58-17 prose branches (count_needed, ok:false with every ref clear)]
tech-stack:
  added: []
  patterns: [RED-then-GREEN, real-file mutants]
key-files:
  modified:
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/scripts/test_answer_resolve.py
decisions:
  - "Title tokens are built with str.isalnum, not `re`: batch_card's import allowlist lock (test_batch_card TestReadOnly.test_import_set) forbids new imports"
  - "D-18 check lives in _needs_count and reuses batch_parse._rest_bands_for(verb) as the single source of the bulk-safe bands"
metrics:
  duration: ~20m
  completed: 2026-10-27
  tasks: 3
  files: 2
---

# Phase 58 Plan 10: resolve gap round (WR-03, IN-03, D-18, WR-04) Summary

`resolve` now matches titles by whole tokens with filler ignored, so the owner's verbatim words `the Browse recovery issue` resolve to row 5. It no longer matches fragments inside words (`port`, `on`). `changed` excludes `joined` rows. An uncounted described group that would dismiss or defer a critical, warning or needs-verification row returns the new `count_needed` status.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 RED | b648294 | test(58-10): reproduce WR-03, IN-03, D-18 and pin WR-04 on resolve (RED) |
| 2 GREEN | c3f401e | fix(58-10): whole-token title matching, changed excludes joined, counted serious groups |
| 3 mutants | cfb1edd | test(58-10): mutants m6-m9 for title tokens, changed marker and count_needed |

## RED run (Task 1, batch_card.py at HEAD 2cdfea8)

`pytest -q scripts/test_answer_resolve.py -k TestGapRound` gave `9 failed, 6 passed, 2 subtests passed` (failures include subtests). `-k "not TestGapRound"` gave `54 passed`.

| Test | RED line |
|------|----------|
| test_v1_verbatim_title_clause_resolves | `AssertionError: False is not true` (ok false; title ref none) |
| test_filler_words_do_not_block_match [the Browse recovery bug], [that browse recovery one] | `Tuples differ: ('none', []) != ('one', [5])` |
| test_fragment_inside_a_word_is_none | `Tuples differ: ('one', [2]) != ('none', [])` (`port` matched "import") |
| test_filler_only_text_is_none [a] | `'many' != 'none'` |
| test_title_tokens_are_punctuation_insensitive [browse-recovery], [Browse, recovery.] | `Tuples differ: ('none', []) != ('one', [5])` |
| test_changed_marker_excludes_joined | `Lists differ: [1, 2, 3, 4] != [1, 3, 4]` |
| test_dismiss_serious_group_without_count_needs_count | `'one' != 'count_needed'` |

These already passed at HEAD, as the plan allowed: test_counted_serious_group_matches, test_medium_and_fix_groups_without_count_still_one, test_two_uncounted_remaining_is_ok_false_with_every_ref_clear (WR-04 is a pin: the helper already returns ok false, every ref one/bulk, needs_reason false, parse_reason == REASON_REST_TWICE), and test_filler_only_text_is_none for `the issue` (no title contains "issue"). For that last one I added the `a` and `this one` subtests so the filler-only rule has a case that fails at HEAD (`a` gave `many`).

## GREEN (Task 2)

- `_TITLE_FILLER` (determiners and card nouns only), `_title_tokens` (maximal letter/digit runs, case-folded), `_match_title` (token superset, order-free, empty wanted → []).
- `_CHANGED_CAUSES = ("code", "nearby", "severity")` used by `_marker_rows(..., "changed")`.
- `_needs_count(ref, matched)`: for an uncounted dismiss/defer marker where any matched band falls outside `batch_parse._rest_bands_for(verb)`, `_resolve_one` returns `count_needed` (rows [], candidates = matched rows) before any claim. `REF_STATUSES` and the `resolve_refs` docstring list it.
- `pytest -q scripts/test_answer_resolve.py scripts/test_batch_card.py scripts/test_fix_loop_card.py scripts/test_finalize_card.py`: `317 passed, 315 subtests passed`.
- Acceptance checks: `"count_needed"` count 2 and `_TITLE_FILLER` count 2 in batch_card.py; `_match_title([... "Unused import of os"], "port")` prints `[]`; `git diff --stat 24dccdc..HEAD -- batch_parse.py score.py` empty; `-k refusals_are_reasons` 1 passed.

### Pin changes

- `TestResolveGaps.test_changed_and_absorbed_markers`: the fixture's row 1 `stale` was `{"decision": "dismiss"}` with no `cause`. Real rows always carry a cause (`batch_card.py` stale builder). It is now `{"cause": "code", "decision": "dismiss"}`, and the expected rows are unchanged ([1]).
- `test_title_words_in_any_order_case_folded` needed no change.

## Real-file mutants (Task 3)

Each mutant was applied to the real `batch_card.py` from a scratchpad Python script, then I ran `pytest -q scripts/test_answer_resolve.py` and reverted with `git checkout --`. `git diff --stat` was asserted empty after each revert.

| Mutant | Edit to batch_card.py | Result | Failing tests |
|--------|-----------------------|--------|---------------|
| m6 | `_match_title` returns substring containment of each wanted token | 2 failed | test_fragment_inside_a_word_is_none, test_m6_substring_matching_restored |
| m7 | filler not stripped (`wanted = [t for t in _title_tokens(text)]`) | 5 failed | test_v1_verbatim_title_clause_resolves, test_filler_words_do_not_block_match, test_filler_only_text_is_none, test_m7_filler_not_stripped |
| m8 | `changed` → `r.get("stale")` (includes joined) | 3 failed | test_changed_marker_excludes_joined, test_dismiss_serious_group_without_count_needs_count, test_m8_changed_includes_joined |
| m9 | D-18 `_needs_count` early return removed | 2 failed | test_dismiss_serious_group_without_count_needs_count, test_m9_serious_group_without_count_acts |

The in-test mock mutants (`TestGapRoundLockTrips`, test_m6..m9) gave `4 passed, 8 subtests passed`. The full `test_answer_resolve.py` gave `68 passed, 53 subtests passed`. `git status --porcelain batch_card.py` was empty at the end.

## Full suite

A bare `pytest -q` from plugins/vibe-check at cfb1edd gave `3479 passed, 4625 subtests passed in 175.32s`, with 0 failed. The baseline was 3465, and this plan added 14 tests: 10 in TestGapRound and 4 in TestGapRoundLockTrips.

## Deviations from Plan

**1. [Rule 3 - Blocking] Tokenizer without `re`**
- **Found during:** Task 2
- **Issue:** The plan said to add `_TITLE_TOKEN_RE = re.compile(r"[^\W_]+")` and import `re`. `test_batch_card.py::TestReadOnly::test_import_set` locks batch_card's imports to {json, os, sys, carry_state, batch_parse} and failed.
- **Fix:** `_title_tokens` maps every non-`str.isalnum` character to a space and splits. No `re` import, and the lock is unchanged.
- **Cost if wrong:** `isalnum` and `[^\W_]` differ only on rare Unicode combining marks inside a title word, which would split such a word into two tokens. Matching stays whole-token and conservative.
- **Commit:** c3f401e

**2. [Rule 2] Filler-only test strengthened**
- **Found during:** Task 1
- **Issue:** `the issue` already resolved to none at HEAD because no title contains "issue", so the test could not show the filler rule.
- **Fix:** Added subtests `a` (many at HEAD) and `this one`.
- **Cost if wrong:** none. The assertions are only stricter.
- **Commit:** b648294

## Threat surface

T-58-30 is covered by whole-token matching plus m6. T-58-31 is covered by count_needed plus m9. T-58-32 needed no new refusal string, and refusals_are_reasons stays green. No new surface.

## Known Stubs

None.

## Self-Check: PASSED
