---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 01
subsystem: decision-cards
tags: [batch_card, fix-loop, finalize, needs-verification, RECV-01, K2]
requires: []
provides:
  - "rows doc keys nv_rows + bulk_fix_text (both card modes)"
  - "batch_card.option_texts(rows, mode, subset)"
affects: [58-04, 58-05]
tech-stack:
  added: []
  patterns: ["text == behavior lock with mock mutants + real-file mutants"]
key-files:
  created:
    - plugins/vibe-check/scripts/test_card_scope.py
  modified:
    - plugins/vibe-check/scripts/batch_card.py
decisions:
  - "Option labels unchanged (FIX_LOOP_OPTIONS / FINALIZE_Q1); only the description is rendered by the helper"
  - "Singular form: one NV row renders 'Needs-verification row #N ... it' (fix-loop) / 'row (#N) is not included — name it' (finalize)"
metrics:
  duration: ~25 min
  completed: 2026-10-27
  tasks: 2
  files: 2
---

# Phase 58 Plan 01: Bulk-fix scope text names excluded NV rows Summary

`batch_card.py rows` now emits `nv_rows` and `bulk_fix_text` for both cards, built from the same `carry_state.NV_BAND` literal `select` uses. A mutation-tested lock pins the numbers in the text to the rows that `select(all)` and Finalize `Fix all` actually leave out (closes K2).

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | 8a0df28 | test(58-01): add failing text == behavior lock for bulk-fix scope (K2) |
| 2 (GREEN) | c58512e | feat(58-01): helper renders Apply all / Fix all scope text naming excluded NV rows (D-10..D-12) |

## Exact `bulk_fix_text` strings (for 58-04 / 58-05 to pin)

Pinned as constants in `test_card_scope.py`:

- fix-loop, NV rows #3 and #4: ``every listed row except Needs-verification rows #3, #4 — confirm, dismiss or defer those by number in Other (`fix N`, `dismiss N -- reason`, `defer N -- reason`)``
- fix-loop, one NV row #2: ``every listed row except Needs-verification row #2 — confirm, dismiss or defer it by number in Other (`fix N`, `dismiss N -- reason`, `defer N -- reason`)``
- fix-loop, no NV row / subset card: `every listed row`
- finalize, NV rows #3 and #4: `Fix every critical, warning and medium row. Needs-verification rows (#3, #4) are not included — name them by number in Mixed…`
- finalize, one NV row #2: `Fix every critical, warning and medium row. Needs-verification row (#2) is not included — name it by number in Mixed…`
- finalize, no NV row: `Fix every critical, warning and medium row.`

The fix-loop text is lowercase-led because it is designed to follow "Apply all & rerun:"-style wording in the option description. 58-04 decides the surrounding prose.

## RED output (Task 1, before batch_card.py changed)

`pytest -q scripts/test_card_scope.py` gave `17 failed, 7 passed, 4 subtests passed`. The failures counted subtests. Verbatim failure lines included:
```
E       KeyError: 'bulk_fix_text'
E               KeyError: 'nv_rows'
E               AssertionError: 'bulk_fix_text' not found in {'at_pass': 2, 'mode': 'fix-loop', 'rows': [...]}
E       AttributeError: module 'batch_card' has no attribute 'option_texts'
FAILED scripts/test_card_scope.py::TestScopeTextEqualsBehavior::test_exact_text_two_nv_rows
FAILED scripts/test_card_scope.py::TestScopeTextEqualsBehavior::test_finalize_equality
FAILED scripts/test_card_scope.py::TestScopeTextEqualsBehavior::test_fix_loop_equality
FAILED scripts/test_card_scope.py::TestScopeTextEqualsBehavior::test_mode_prefixes
FAILED scripts/test_card_scope.py::TestScopeTextEqualsBehavior::test_subset_card_excludes_nothing
FAILED scripts/test_card_scope.py::TestScopeLockTrips::test_m1..m4 (4 tests)
```
The remaining TestScopeTextEqualsBehavior tests (one_nv_row, no_nv_card, carries_scope_keys, numbers_and_literals_only) failed in every subtest. Only the fixture tests and the K2 reproduction passed: `-k "fixture or behavior_already or k2"` gave 3 passed. That reproduction showed `excluded_by_behavior == [3, 4]` on both cards, with `bulk_fix_text` and `nv_rows` absent from the doc. In Task 2 the reproduction test was removed and its inverse became `test_rows_doc_carries_scope_keys`, which asserts the keys are present and the behavior still excludes [3, 4].

## GREEN

- `pytest -q scripts/test_card_scope.py`: 15 passed, 15 subtests passed
- Quick set (scope, batch_card, card_text, fix_loop_card, finalize_card): 242 passed, 272 subtests passed. No existing test changed.
- Full suite: **3326 passed** (3311 baseline + 15 new), 0 failed, 174.6 s
- CLI: `batch_card.py rows --mode fix-loop` fed `nv_card_state()` exited 0 with `nv_rows [3, 4]` and the fix-loop text above
- `grep -c "def option_texts"` gave 1 and `grep -c "doc.update(option_texts"` gave 1. `score.py` and `batch_parse.py` were not changed.

## Mutants (all applied and observed failing)

Mock mutants live in `TestScopeLockTrips`. Each one first asserts that the mutated artifact differs from the real one, then asserts that `lock_holds` is False. All four pass on GREEN.

The same mutants were also applied to the real files with sed, then restored from a backup. Restoration was checked with `cmp` (rerun gave 15 passed):

| Mutant | Real-file edit | Observed |
|--------|----------------|----------|
| m1 `_rest_bands_for('fix')` reaches NV | `batch_parse.py`: `_FIX_REST_BANDS = ("critical", "warning", _NV_BAND, "medium")` | 5 failed. Includes `test_finalize_equality`, `test_behavior_already_drops_nv`, plus the finalize subtests of `test_exact_text_one_nv_row` / `test_rows_doc_carries_scope_keys` |
| m2 `select(all)` keeps NV | `batch_card.py` select: `if True]` | 5 failed |
| m3 number dropped from text | `option_texts`: `for n in nv_rows[:-1]` | 7 failed |
| m4 subset card names NV rows | `option_texts`: `[] if False else [...]` | 2 failed |
| m5 (extra) text built from the wrong band | `option_texts`: `r["band"] == "medium"` | 9 failed |

## Threat model

- T-58-01: the text is composed only of `row["n"]` integers and literals. `test_text_is_numbers_and_literals_only` asserts the text is a single line and contains no row title or file.
- T-58-02: the m1/m2 equality locks hold.
- T-58-03: the subset card gives `nv_rows == []` and the plain text. m4 trips.

## Deviations from Plan

None. The plan was executed as written, with these notes:
- The plan cited the RESEARCH table's NV rows #3, #5. The `nv_card_state()` fixture actually ranks them as rows #3 and #4, because NV ranks before medium. The tests pin #3, #4 from the real fixture.
- I added a fifth real-file mutant (m5, wrong band) beyond the four the plan required.

## Self-Check: PASSED
- FOUND: plugins/vibe-check/scripts/test_card_scope.py
- FOUND: plugins/vibe-check/scripts/batch_card.py (`def option_texts`)
- FOUND: 8a0df28, c58512e
