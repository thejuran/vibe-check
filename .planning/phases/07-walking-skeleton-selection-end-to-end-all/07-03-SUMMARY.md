---
phase: 07-walking-skeleton-selection-end-to-end-all
plan: 03
subsystem: review-tooling
tags: [vibe-check, deep-review, prompt-only, all-mode, files-block, delegation]

# Dependency graph
requires:
  - phase: 07-02
    provides: "review.md Phase-0 mode 5 (--all branch-flip), $ALL_MODE flag, <files> block format / $FILES_BLOCK, reserved-subdir fresh-snapshot state"
  - phase: 07-01
    provides: "templates/skip-rules.md shared skip snippet referenced by review.md mode 5"
provides:
  - "/vibe-check:deep-review --all recognized via inherited Phase-0 mode 5 (delegation note)"
  - "deep-review Phase-2.5 architecture prompt emits <files> instead of <diff> under $ALL_MODE"
affects: [08-chunking, 10-noise-and-codex-skip, 11-fix-posture, 12-dogfood]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Delegation-inheritance: deep-review recognizes --all by delegating Phase 0 to review.md (no re-authored selection)"
    - "$ALL_MODE-gated <diff>→<files> swap reusing review.md's flag + format verbatim (no redefinition)"

key-files:
  created: []
  modified:
    - plugins/vibe-check/commands/deep-review.md

key-decisions:
  - "Recognition note attached to delegation step 2 (Execute Phase 0 per review.md), the line that already establishes review.md as the single Phase-0 source"
  - "Phase-2.5 swap shown as a full $ALL_MODE variant block in-place after the diff-mode block, mirroring review.md's authoring style; diff-mode <diff> block left present as context (no-regression)"
  - "Codex blocks (113-255) left byte-untouched: REVIEW-04 (--all→Codex-skip) is Phase 10, and the existing non-representable-range gate already fails closed to native-only"

patterns-established:
  - "Pattern: smallest-additive deep-review touch = recognition note (inherited selection) + one Phase-2.5 block swap; everything else inherited via delegation"

requirements-completed: [SELECT-01, REVIEW-01]

# Metrics
duration: ~12min
completed: 2026-06-22
---

# Phase 7 Plan 03: deep-review `--all` recognition + Phase-2.5 `<files>` swap Summary

**`/vibe-check:deep-review --all` is now recognized — selection inherited from review.md Phase-0 mode 5 via the existing delegation — and deep-review's own Phase-2.5 architecture prompt swaps `<diff>`→`<files>` under `$ALL_MODE`, completing SELECT-01 on both commands and extending REVIEW-01 to deep mode's architecture agent.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-22T15:57Z (approx)
- **Completed:** 2026-06-22T16:09:32Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added a one-line `--all` recognition note to deep-review's Phase-contract delegation (step 2): the whole-tree selection (mode 5), narrow-arg containment guard, skip rules, and `$ALL_MODE`/`$REVIEW_SET` bindings are INHERITED through the existing "Execute Phase 0 per review.md" delegation — deep-review does NOT re-author selection.
- Added an `$ALL_MODE`-gated `<diff>`→`<files>` swap to deep-review's own Phase-2.5 architecture prompt (the deep-only block that carries a separate `<diff>{{git_diff}}</diff>`), in the EXACT same position (after `{{intent-context}}`, before `<related-files>`), reusing review.md's `$ALL_MODE` flag and `<files>` format/`$FILES_BLOCK` string verbatim (no redefinition).
- Noted the impact agent's `<related-files>` block stays as-is / best-effort in `--all` (its deeper `--all` behavior is a later phase).
- Left the Codex blocks (lines 113-255), the Phase-1c related-files block, and all diff-mode text byte-untouched; no Phase 8-11 scope added.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add --all recognition note and swap the Phase-2.5 architecture block to `<files>`** - `3f3863b` (feat)

**Plan metadata:** committed with this SUMMARY (docs: complete plan)

## Files Created/Modified
- `plugins/vibe-check/commands/deep-review.md` - Added the `--all` recognition note to the delegation section (step 2) and the `$ALL_MODE`-gated `<files>` swap to the Phase-2.5 architecture prompt. Diff: 19 insertions, 1 deletion (the deletion is the in-place extension of the delegation sentence — original text preserved verbatim, recognition note appended).

## Decisions Made
- **Recognition-note placement:** attached to delegation step 2 ("Execute Phase 0, 0.5, 0.7, 1, 1.5 per `commands/review.md`") rather than as a new standalone paragraph — that line already establishes review.md as the single Phase-0 source, so the inheritance claim is closest to where selection is delegated. Mirrors deep-review's existing "Execute Phase 0 … per review.md" phrasing.
- **Phase-2.5 swap shape:** authored as a full `$ALL_MODE` variant block (with the swapped `<files>` prompt shown verbatim) placed immediately after the existing diff-mode block, mirroring review.md's base/intent-template swap style. The diff-mode `<diff>{{git_diff}}</diff>` block is left present as context, so a plain `/deep-review` still emits `<diff>` (no regression).
- **Format reuse, not redefinition:** the note explicitly says to reuse review.md's `$ALL_MODE` flag and `<files>` block format/`$FILES_BLOCK` string verbatim and NOT redefine the format in deep-review — honoring D-06's single-source-of-truth lock and the plan's critical note.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The plan file and `.planning/` tree live in the main repo checkout, not the worktree (`.planning/` is gitignored, so it is not present in the worktree at spawn). Read the plan/context/research/patterns from the main-repo absolute paths; wrote and force-added the SUMMARY under the worktree's `.planning/` path so it persists on the worktree branch (orchestrator rescues + untracks on merge, as with 07-01/07-02). No impact on the deliverable.
- First Edit attempt used the shared-checkout absolute path and was rejected (worktree isolation); re-issued against the worktree-copy absolute path. No content impact.

## Verification Performed
- **PLAN `<verify>` automated:** `grep -q -- '--all'` && `grep -q '<files>'` && `grep -qE 'ALL_MODE'` → PASS.
- **SELECT-01 (recognition note):** present in the Phase-contract region (line 36), original delegation sentence preserved verbatim.
- **REVIEW-01 (`<files>` swap):** `$ALL_MODE`-gated `<files>` block present in the Phase-2.5 region (lines 113-129).
- **Codex byte-untouched:** `git diff` hunks are at original lines 33 and 110 only; no Codex / Phase-2b / Phase-2c / adversarial / watchdog line appears as `+`/`-`; the Phase-2b heading (original line 113) and the whole Codex region (113-255) are unmodified context.
- **No-regression (additive):** the diff-mode `<diff>{{git_diff}}</diff>` architecture block survives as context (a plain `/deep-review` still emits `<diff>`).
- **Scope guard:** no NEW `chunk` / `budget` / `in_reviewed_set` / `CODEX_SKIPPED.*all` / `cross-file dedup` tokens in added lines (pre-existing Codex-block occurrences of `CODEX_SKIPPED`/`budget` are untouched context).
- **Behavioral (deferred to wave merge / human):** `/vibe-check:deep-review --all` recognized (branches to inherited mode-5 selection) and dispatches architecture with a `<files>` block; a plain `/deep-review` is byte-for-byte unchanged in behavior; Codex still fail-closed degrades to native-only on a non-representable range.

## Known Stubs
None — the edit is a complete, self-contained additive touch. The `<related-files>` best-effort note in `--all` and the formal `--all`→Codex-skip wiring are explicitly deferred to later phases per the plan (NOT stubs introduced here).

## Next Phase Readiness
- SELECT-01 fully satisfied: `--all` is now recognized on BOTH `/vibe-check:review` (plan 02) and `/vibe-check:deep-review` (this plan).
- REVIEW-01 extended to deep mode's architecture agent.
- Phase 8 (risk-ranked chunking) can build on the `<files>` block / `$FILES_BLOCK` format both commands now carry.
- Phase 10 owns the formal `--all`→Codex-skip wiring (REVIEW-04) and the impact agent's deeper `--all` `<related-files>` behavior — both correctly left untouched here.

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/commands/deep-review.md` (modified)
- FOUND: `.planning/phases/07-walking-skeleton-selection-end-to-end-all/07-03-SUMMARY.md` (created, force-added)
- FOUND commit: `3f3863b` (Task 1 — feat)
- FOUND commit: `73a723e` (SUMMARY — docs)

---
*Phase: 07-walking-skeleton-selection-end-to-end-all*
*Completed: 2026-06-22*
