---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 14
subsystem: finalize-prose
tags: [gap-closure, finalize, WR-01, tdd, prose-lock, fresh-shell-walk]
gap_closure: true
requires: []
provides: [step-3 BLOBFILE re-mint (re-fingerprint HEAD) before the post-answer recount, STEP3_NEEDLES (8), STEP3_STALE_OLD, isolated stale-claim mutant, fresh-shell stale/fresh/control blob walk]
affects: [60-16 (ledger RED/GREEN SHAs)]
tech-stack:
  added: []
  patterns: [substring prose lock with one mutant per needle, isolated append-mutant for an absence check, fresh-shell walk over the real fences with printed literals]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "Step 3 runs step 1's existing BLOBFILE fence again (no second mktemp fence), in the rebuild-once paragraph's words, then recounts on that NEW literal before the GATEFILE re-mint"
requirements: [FINL-02]
metrics:
  duration: ~15min
  completed: 2026-10-30
  tasks: 2
  files: 2
---

# Phase 60 Plan 14: Finalize step 3 re-fingerprints HEAD before the post-answer recount (WR-01) Summary

After the owner answers the Finalize card, step 3 now says to run step 1 again, which means a new mktemp fence printing a NEW `BLOBFILE=` with the fingerprints rebuilt from the current HEAD, index and working tree. It then re-runs the counts step once with that new literal, before the GATEFILE re-mint that 60-12 added. Before this, step 3 recounted on the pre-card BLOBFILE because "the fingerprints have not changed". So if a file was edited while the owner answered, a last-pass fix-obsolete verdict still matched the stale blob, the recount dropped to zero, and the gate returned `write` (APPROVED) over code nothing had re-verified.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED: BLOBFILE re-mint needles + mutants, stale-claim append-mutant, fresh-shell stale/fresh/control walk | 7796476 | test_finalize_card.py |
| 2 | GREEN: step-3 line rewritten (one line changed) | 9b3f055 | 90-finalize.md |

**RED SHA:** 7796476. **GREEN SHA:** 9b3f055.

## Verification (observed)

RED at 7796476, `pytest -q -p no:cacheprovider test_finalize_card.py -k "step3 or post_decision or refingerprint"`:
`9 failed, 2 passed, 89 deselected, 9 subtests passed`. These are the failures:
- `test_step3_rerun_rule_holds`
- `test_mutant_step3_rerun_rule`: 5 subfailures (the four new needles fail the `_step3_mutant` presence assertion on today's line, plus the `STEP3_OLD` reinsertion at `STEP3_NEEDLES[3]`)
- `test_mutant_step3_reinserts_stale_fingerprint_claim` (`STEP3_STALE_OLD` found in today's line)
- `test_post_decision_recount_refingerprints_head`: its stale, fresh and control subtests passed and it failed only at the final `assert_holds` (line 2484)
- `test_post_decision_rerun_decides_on_a_fresh_gatefile`: failed only at its final `assert_holds` (line 2380), as the plan expected

`test_step3_keeps_answer_files_anchor` passed.

Walk mutant (scratch copy, deleted afterwards): writing PRE instead of POST to the re-minted BLOBFILE makes the `fresh` subtest fail. The walk tells the edited blob apart from the unchanged one.

GREEN at 9b3f055:
- `pytest -q -p no:cacheprovider test_finalize_card.py`: `95 passed, 146 subtests passed`
- `pytest -q -p no:cacheprovider test_pause_batching.py test_nv_render.py test_fix_loop_card.py test_carry_state.py`: `433 passed, 695 subtests passed`
- Full suite at 9b3f055 (`pytest -q -p no:cacheprovider` in plugins/vibe-check/scripts): `3815 passed, 5020 subtests passed`, 0 failed

Grep acceptance checks:
- "the fingerprints have not changed": 0
- "RE-RUN the counts step and the gate ONCE": 0
- `BLOBFILE=$(mktemp`: 1
- `GATEFILE=$(mktemp`: 1
- step-3 line count: 1, with the eight anchors in the required order (checked by script)
- `git diff 7796476 --stat` on 90-finalize.md: 1 insertion, 1 deletion
- `git diff c112ca6` on 90-finalize.md: only the step-3 line changed, so the rebuild-once paragraph is byte-identical

## Deviations from Plan

**1. [Rule 3 - Blocking] `_flags` takes the state file**
- **Found during:** Task 1
- **Issue:** The plan's behavior text wrote `_flags(counts1)`, but the harness signature is `_flags(counts, state_file)`.
- **Fix:** The test calls `self._flags(counts1, state)`, the same way the 60-12 model walk does.
- **Cost if wrong:** None. This is a test-call signature only.
- **Commit:** 7796476

**2. [Rule 2 - Guard isolation] The append-mutant also asserts every needle is still present**
- **Found during:** Task 1
- **Issue:** The plan says the mutant isolates the new check. Without an assertion, that isolation was only an assumption.
- **Fix:** The test asserts all `STEP3_NEEDLES` are still on the mutant line, so only the `STEP3_STALE_OLD` check can trip it.
- **Cost if wrong:** None. The assertion only makes the test stricter.
- **Commit:** 7796476

## Known Stubs

None.

## Residuals

- The prose rule is locked and the walk proves the mechanics. Whether a live agent actually re-runs step 1 at step 3 has not been checked. That needs a live Finalize run, which this plan did not exercise.

## Requirements

FINL-02 was not ticked. It stays unchecked until the 60-16 close-out and re-verification, the same convention 60-12 and 60-13 followed.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md, plugins/vibe-check/scripts/test_finalize_card.py
- FOUND commits: 7796476 (test), 9b3f055 (fix)
