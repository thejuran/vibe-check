---
phase: 57-decision-continuity-within-closure
plan: 12
subsystem: orchestration-prose
tags: [prose, 30-collect-score, 90-finalize, 50-fix-loop, prose-lock, deletion-hunk, gap-closure]
requires: ["57-08", "57-11"]
provides:
  - "fully specified hunk -> changed_line_ranges construction (ordinary and deletion-only hunks)"
  - "symmetric nearby-window wording in all prose"
  - "Finalize Open/Closed contract matching carry_state (IN-01, D-16)"
affects: [plugins/vibe-check/phases/review/30-collect-score.md, plugins/vibe-check/phases/shared/90-finalize.md, plugins/vibe-check/phases/review/50-fix-loop.md]
tech-stack:
  added: []
  patterns: ["phrase lock + per-phrase removal mutant (LockCase / _delete)"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/scripts/test_nv_render.py
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "Ordinary-hunk range rule added to the existing DELETION_RANGE_PHRASES tuple (same scoped predicate), so the existing removal-mutant and outside-bullet tests cover it"
  - "Header with no count is stated as count 1 (unified-diff convention), so the construction is complete"
metrics:
  duration: "~4 min"
  completed: 2026-10-26
  tasks: 2
  files: 5
---

# Phase 57 Plan 12: Prose aligned with D-14/D-16 and deletion-hunk range rule Summary

The orchestrator prose now fully specifies how diff hunks become `changed_line_ranges` (ordinary hunk `[start, start + count - 1]`, deletion-only `+T,0` -> `[max(T, 1), T + 1]`), says "within 5 lines above or below" everywhere the nearby window is described, and states the same newcomer, covers and inherited-reopen rules carry_state.py applies; every new phrase is locked with a removal mutant.

## Prose lines changed

| File:line | Before | After |
|-----------|--------|-------|
| 30-collect-score.md:57 (step 0 Why) | "An edit to the code within the window beneath the line is reported" | "An edit within 5 lines above or below the line (D-14) is reported" |
| 30-collect-score.md:64 (changed-line ranges bullet) | ends after the `in_diff` sentence | + "Build the ranges from each hunk's new-side header `+start,count` (a header with no count means count 1): every hunk with new-side lines contributes `[start, start + count - 1]`. A hunk that only deletes (new-side count 0, header `+T,0`) has no new-side lines; it contributes the range `[max(T, 1), T + 1]` — the two new-side lines on either side of the deletion point — so a deleted guard directly above or below a flagged line counts as a nearby change (D-14, `_nearby_changed`), the same ranges `score.py` uses for `in_diff` and `snapshot.nearby_at`." |
| 90-finalize.md:25 (Open) | "...which stays decided when it later splits into its own row (D-09)." | + "; a member that carries its own separately-owed obligation is never covered by the row decision (D-16); a covered finding that is now its own row reopens under the same rules as an own decision — nearby change, joined concern, lane-backed severity rise." |
| 90-finalize.md:26 (Closed) | "no change landed in the 5-line window beneath the flagged line since the decision (`snapshot.nearby_at`, D-02)" | "no change landed within 5 lines above or below the flagged line since the decision (`snapshot.nearby_at`, D-02/D-14)" |
| 90-finalize.md:26 (Closed, IN-01) | "the row gained no member with a different concern from a lane the decision did not cover (D-08)" | "the row gained no member with a concern (lane + title) the decision did not cover and whose title is not a covered title (D-08)" |
| 90-finalize.md:26 (Closed) | "the band did not rise with a reviewer lane absent at decision time" | "the band did not rise with a reviewer lane that did not report this concern at decision time (D-16)" |
| 50-fix-loop.md:54 (IN-02) | "Both render the same suffix" | "All three render the same suffix" |

**scoring.md:** no window wording; unchanged (grep for "beneath" returned nothing; the "nearby" hits at lines 82-83 describe Codex pair matching, not the nearby-change window).

No test pinned "Both render"; no pin needed updating.

## Lock phrases added

- `test_nv_render.py::DELETION_RANGE_PHRASES` + "`[start, start + count - 1]`" (SYNTHETIC fixture extended; covered by `test_deletion_range_removal_mutants` and `test_deletion_range_outside_bullet_mutant`).
- `test_finalize_card.py::PHASE57_DECISIONS` (8 -> 12): "within 5 lines above or below", "whose title is not a covered title", "separately-owed obligation is never covered", "did not report this concern at decision time"; each gets a removal mutant via the existing loop in `test_phase57_decision_contract`.
- Negative check in `test_phase57_old_closed_rule_gone`: "5-line window beneath" absent from 90-finalize.md.

## Verification (observed)

- `pytest -q test_nv_render.py` -> 29 passed, 86 subtests passed (includes `test_deletion_range_rule_locked`, now green, and the `decided_relocation_holds` locks).
- `pytest -q test_finalize_card.py test_card_text.py test_batch_card.py` -> 156 passed, 177 subtests passed.
- Targeted six-file run (nv_render, finalize_card, card_text, batch_card, carry_state, decision_continuity) -> 443 passed, 601 subtests passed.
- Full suite (bare `pytest -q` from scripts/, includes test_replay.py) -> 3248 passed, 4312 subtests passed, 0 failed (was 1 failed / 3247 after 57-11).
- grep counts: "A hunk that only deletes" 1, `[max(T, 1), T + 1]` 1, "start + count - 1" 1, "window beneath" 0, "above or below the line (D-14)" 1 in 30-collect-score.md; "beneath" 0 in 90-finalize.md, 50-fix-loop.md, 30-collect-score.md, carry_state.py, score.py.
- No hook-blocked commands.

## Commits

- fd36f8f docs(57-12): specify hunk-to-range mapping and symmetric nearby window in collect-score
- fbfa8fc docs(57-12): align finalize Open/Closed contract and fix-loop suffix note with carry_state

## Deviations from Plan

None - plan executed exactly as written. (The ordinary-hunk sentence also states that a header without a count means count 1, which the plan left implicit; Cost if wrong: one clause of prose, no behavior.)

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: all five modified files
- FOUND: fd36f8f, fbfa8fc
