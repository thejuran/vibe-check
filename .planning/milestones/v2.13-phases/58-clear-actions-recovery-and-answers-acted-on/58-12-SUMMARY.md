---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 12
subsystem: review-render-prose
tags: [recovery-pairs, gap-closure, RECV-02, IN-01, IN-02]
requires: [58-02]
provides:
  - "NV needs-recheck suffix identical to the Recovery pairs cells in both 40-render.md and output-format.md"
  - "explicit ` — ` separator on the Fix not yet verified line"
  - "nv_suffix_from_table: expectation derived from the parsed table row"
affects: [phases/review/40-render.md, templates/output-format.md]
tech-stack:
  added: []
  patterns: ["derive cross-file expectations from the parsed source table instead of a duplicated literal"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_recovery_pairs.py
    - plugins/vibe-check/templates/output-format.md
    - plugins/vibe-check/phases/review/40-render.md
decisions:
  - "The needs-recheck suffix copies the table cells verbatim, parenthetical and trailing period included; the table is the single source"
  - "The Fix not yet verified line uses the same ` — ` separator as the Fix not yet confirmed line"
metrics:
  duration: ~12m
  completed: 2026-10-27
  tasks: 2
  files: 3
requirements: [RECV-02]
---

# Phase 58 Plan 12: Recovery-text joins reconciled (IN-01, IN-02) Summary

The no-eligible-reviewer needs-recheck suffix now equals the Recovery pairs table cells word for word in every file that copies it, and the test derives that expectation from the parsed table row, so rewording the cell or a copy fails the test. The `Fix not yet verified:` rule now names ` — ` as its separator.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED: derive NV suffix from the table; lock the verified-line separator | 37453ca | scripts/test_recovery_pairs.py |
| 2 | GREEN: copy the cell verbatim; name the separator | af6df2e | templates/output-format.md, phases/review/40-render.md |

## RED run (before the fix, observed)

`pytest -q scripts/test_recovery_pairs.py` → `5 failed, 20 passed`:
- `TestReconciled::test_nv_suffix_in_both_files` [file=phases/review/40-render.md]
- `TestReconciled::test_nv_suffix_in_both_files` [file=templates/output-format.md]
- `TestReconciled::test_verified_line_names_its_separator`
- `TestLockTrips::test_m_template_suffix_without_parenthetical` (mutant equal to HEAD text)
- `TestLockTrips::test_n_verified_rule_without_separator` (mutant equal to HEAD text)

## GREEN (observed)

- `pytest -q scripts/test_recovery_pairs.py scripts/test_verified_fixes.py scripts/test_confirmed_fix.py scripts/test_card_text.py` → 231 passed
- Full suite `pytest -q` from plugins/vibe-check → 3482 passed, 0 failed (was 3479; +3 new tests)
- Acceptance greps: parenthetical in output-format.md = 1; separator rule in 40-render.md = 1; `run /deep-review` = 0 in both; `^NV_SUFFIX = ` = 0; `def nv_suffix_from_table` = 1

## Mutants applied to the real files (scratchpad script mut12.py; each restored, tree clean)

| Mutant | Edit to real file | Observed failing tests |
|--------|-------------------|------------------------|
| m | output-format.md suffix reverted to HEAD wording (no parenthetical, no trailing period) | `test_nv_suffix_in_both_files`[output-format.md], `test_m_template_suffix_without_parenthetical` (2 failed) |
| n | 40-render.md verified rule: `then ` — ` and the pair` → `then the pair` | `test_verified_line_names_its_separator`, `test_n_verified_rule_without_separator` (2 failed) |
| o | 40-render.md table cell parenthetical dropped (both rows that carry it) | `test_nv_suffix_in_both_files`[40-render.md] and [output-format.md], `test_m_template_suffix_without_parenthetical` (3 failed) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 40-render.md :100 carried the same shortened suffix**
- **Found during:** Task 1 RED (the `[40-render.md]` subtest failed too)
- **Issue:** The plan's interfaces listed only output-format.md :70 as holding the shortened suffix, but the test checks both files and the Needs-verification render rule in 40-render.md :100 had the same truncated text.
- **Fix:** Applied the same verbatim-cell replacement at 40-render.md :100.
- **Cost if wrong:** One sentence of render prose reverts; no code or score.py behavior depends on it.
- **Files modified:** plugins/vibe-check/phases/review/40-render.md
- **Commit:** af6df2e

**2. [Rule 1 - Precision] Mutant o edits both table rows that carry the parenthetical**
- **Found during:** Task 2 mutants
- **Issue:** The parenthetical cell text appears in the `_R_IR_NO_REVIEWER` and `_R_CF_NO_REVIEWER` rows; a single replace targets both identical strings.
- **Fix:** Mutated both; the derived expectation reads the `_R_IR_NO_REVIEWER` row, so the outcome is the one the plan named.
- **Cost if wrong:** None; the mutant still exercises the derived-from-table path.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_recovery_pairs.py, templates/output-format.md, phases/review/40-render.md
- FOUND commits: 37453ca, af6df2e
