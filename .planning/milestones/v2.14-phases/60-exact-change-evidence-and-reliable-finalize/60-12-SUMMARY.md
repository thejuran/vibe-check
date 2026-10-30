---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 12
subsystem: finalize-prose
tags: [gap-closure, finalize, WR-02, tdd, prose-lock, fresh-shell-walk]
gap_closure: true
requires: []
provides: [step-3 GATEFILE re-mint + rewrite-from-recounted-counts rule, STEP3_NEEDLES/STEP3_OLD, step3_line, step3_rerun_rule_holds, fresh-shell stale-vs-fresh post-answer gate walk]
affects: [60-13 (ledger RED/GREEN SHAs)]
tech-stack:
  added: []
  patterns: [substring prose lock with one mutant per needle, line-scoped mutant where wording repeats elsewhere, fresh-shell walk over the real fences with printed literals]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "Step 3 mirrors the rebuild-once paragraph: re-count on this attempt's BLOBFILE, run the existing gate-input fence again for a NEW GATEFILE=, write the flags from the RE-COUNTED counts, gate on that literal; no second mktemp fence"
  - "The product prose does not cite 60-REVIEW.md WR-02 (the plan's suggested parenthetical); GSD artifact references stay out of product text"
requirements: [FINL-02]
metrics:
  duration: ~10min
  completed: 2026-10-30
  tasks: 2
  files: 2
---

# Phase 60 Plan 12: Finalize step 3 re-mints GATEFILE after the card answer (WR-02) Summary

After the owner answers the Finalize card and `record-decisions` lands, step 3 now says to re-count on the same `BLOBFILE=` literal, run the gate-input fence again so it prints a NEW `GATEFILE=`, write the seven-key `flags` object from the RE-COUNTED `$COUNTS_JSON` to that path, and run the gate on that literal, never on the `GATEFILE=` the attempt's first gate run read. Before this, the text said "RE-RUN the counts step and the gate ONCE", so an agent following it gated on the pre-answer flags and reported "Finalize stays blocked" against an empty list. The owner then had to run `--finalize` a second time, which broke "Finalize costs one card".

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED: step-3 lock + mutants, answer-files anchor guard, fresh-shell stale-vs-fresh walk | 2648f2d | test_finalize_card.py |
| 2 | GREEN: step-3 line rewritten (one line changed) | c112ca6 | 90-finalize.md |

**RED SHA:** 2648f2d. **GREEN SHA:** c112ca6.

## Verification (observed)

- RED, `pytest -q -p no:cacheprovider test_finalize_card.py -k "step3 or post_decision or card_route or test_retry_rule_holds"`: `8 failed, 4 passed, 87 deselected, 2 subtests passed`. The failures are `test_step3_rerun_rule_holds`, all 6 `test_mutant_step3_rerun_rule` subtests (the needles are not in today's line), and `test_post_decision_rerun_decides_on_a_fresh_gatefile`, which failed at its final `assert_holds` after both walk subtests passed. These tests passed: `test_step3_keeps_answer_files_anchor`, `test_card_route_records_then_writes` and `test_retry_rule_holds`.
- RED, full file: `8 failed, 91 passed, 134 subtests passed`.
- The walk reproduces the bug with the real fences. The fixture counts are (5, 1, 0) and the first gate run returns `outstanding-to-phase-5`. After dismissing every row and recording the decisions, the recount is (0, 0, 0). Re-running the gate on the stale `gate1` still returns `outstanding-to-phase-5`, and `gate1` on disk still holds the pre-answer flags. A re-minted `gate2` (a different path from `gate1`) written from the recount returns `write`, with an empty `.err` and a non-empty report.
- GREEN, `pytest -q -p no:cacheprovider test_finalize_card.py`: `93 passed, 140 subtests passed`.
- GREEN, `pytest -q -p no:cacheprovider test_finalize_card.py test_pause_batching.py test_nv_render.py test_fix_loop_card.py test_carry_state.py`: `526 passed, 835 subtests passed`.
- Acceptance greps:
  - exactly one step-3 line, with all 7 required substrings in order (offsets 24 < 205 < 353 < 416 < 508 < 558 < 784)
  - `RE-RUN the counts step and the gate ONCE` occurs 0 times
  - `grep -cF 'GATEFILE=$(mktemp'` = 1
  - `git diff 2648f2d --stat` on 90-finalize.md: 1 insertion, 1 deletion
  - `git diff c0ece7e` on 90-finalize.md touches only the step-3 line (1+/1-), so the rebuild-once paragraph is byte-identical

## Deviations from Plan

**1. [Rule 2 - CLAUDE/agent convention] Dropped "(60-REVIEW.md WR-02)" from the product prose**
- **Found during:** Task 2
- **Issue:** The plan's replacement sentence ended with a reference to a GSD planning artifact. Product text must not carry GSD bookkeeping.
- **Fix:** The sentence ends at "...against a list that may now be empty." All STEP3_NEEDLES are still present verbatim.
- **Cost if wrong:** A reader loses a pointer to the review finding. The pointer lives in this SUMMARY and in 60-REVIEW.md.
- **Commit:** c112ca6

**2. [Rule 1 - test correctness] Step-3 mutants are scoped to the step-3 line**
- **Found during:** Task 1
- **Issue:** `run the gate-input fence again so it prints a NEW `GATEFILE=`` also appears in the rebuild-once paragraph, which comes first in the file. `self._mutant(needle)` would have mutated that paragraph instead, so the step-3 lock could never trip (a decorative guard).
- **Fix:** Added `_step3_mutant(old, new)`, which rewrites only the step-3 line and then goes through `_mutant`.
- **Cost if wrong:** None. The mutants are stricter than the plan's version.
- **Commit:** 2648f2d

**3. [Rule 1 - test fidelity] Fresh subtest mints GATEFILE explicitly instead of calling `_gate`**
- **Found during:** Task 1
- **Issue:** `_gate` does not return the path it mints, so the planned assertion "new GATEFILE path != gate1" could not be written against it.
- **Fix:** The subtest uses the same steps as `_gate`, written out: mint, `assertNotEqual(gate2, gate1)`, write the flags, walk the gate fence, check that `.err` is empty, and assert `write`.
- **Cost if wrong:** None. The checks are the same as `_gate`'s, plus the path inequality.
- **Commit:** 2648f2d

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md, plugins/vibe-check/scripts/test_finalize_card.py
- FOUND commits: 2648f2d, c112ca6
