---
phase: 10-reviewed-set-filter-cross-chunk-merge-noise-control
plan: 02
subsystem: review-tooling
tags: [deep-review, codex, all-mode, representable-range-gate, in_reviewed_set, cross-file-dedup, listing-bar, fail-closed, prompt-spec]

# Dependency graph
requires:
  - phase: 10-reviewed-set-filter-cross-chunk-merge-noise-control (plan 10-01)
    provides: "review.md Phase-3 in_reviewed_set filter, Phase-4 RENDER-ONLY cross-file dedup grouping (occurrence_count/occurrences), the $ALL_MODE && !--full listing bar, and the P10-C coverage fix — all inherited by /deep-review --all via delegation"
provides:
  - "/deep-review --all Codex fail-closed skip arm (slug whole-repo-non-representable) — REVIEW-04"
  - "Two Phase-10 confirmation notes in deep-review.md: inheritance (REVIEW-02/03 + OUTPUT-01-04 reach deep by delegation) and render-narrowing (deep's C+W default comes from the render-time listing bar, not a threshold change)"
affects: [phase-11-fix-loop, phase-12-dogfood-efficacy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Branch-flip-evaluated-FIRST: the $ALL_MODE Codex arm is placed first in the Phase-2c consequence list so an --all run short-circuits before reaching per-mode diff detectors (mirrors review.md Phase 0 line 85)"
    - "Belt-and-suspenders named arm OVER an unchanged catch-all default-fallback: the new arm makes REVIEW-04 dogfood-verifiable without removing the implicit fallback"
    - "Inheritance-by-delegation confirmation notes: deep-review confirms (does NOT re-author) review.md's numbered-phase edits reach /deep-review --all"

key-files:
  created:
    - .planning/phases/10-reviewed-set-filter-cross-chunk-merge-noise-control/10-02-SUMMARY.md
  modified:
    - plugins/vibe-check/commands/deep-review.md

key-decisions:
  - "D-04: named $ALL_MODE skip arm (slug whole-repo-non-representable) added BESIDE the existing arms and OVER the unchanged default-fallback — not a replacement"
  - "D-05: deep inherits review.md's Phase 2/3/4 $ALL_MODE edits by delegation; no re-author — confirmed in a new Phase-10 inheritance note"
  - "D-02: deep's ≥70 threshold left byte-unchanged; the --all C+W default comes from review.md's RENDER-time listing bar (narrow at render, not threshold)"

patterns-established:
  - "Pattern 5 (RESEARCH): the $ALL_MODE Codex arm shape — FAIL CLOSED, set CODEX_SKIPPED, do NOT launch, native-only never blocked, evaluated first, do-not-remove-fallback"
  - "Verify-gate hardening: replace OR-grep with AND-of-Phase-10-tokens scoped to the correct region + a separate assertion that the 10-01 dependency landed in review.md (no false-green on pre-existing 'inheritance' wording)"

requirements-completed: [REVIEW-04, REVIEW-02, REVIEW-03, OUTPUT-01, OUTPUT-02, OUTPUT-03, OUTPUT-04]

# Metrics
duration: ~12min
completed: 2026-06-22
---

# Phase 10 Plan 02: deep-review --all Codex fail-closed skip + Phase-10 inheritance/render confirmation Summary

**`/deep-review --all` now fail-closed skips Codex with a named `whole-repo-non-representable` arm (REVIEW-04), and two new Phase-10 notes confirm that 10-01's review.md `in_reviewed_set` / RENDER-ONLY cross-file dedup / listing-bar edits reach `/deep-review --all` by delegation with the deep ≥70 threshold left untouched.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-22T21:03:30Z
- **Completed:** 2026-06-22T21:15:33Z
- **Tasks:** 1
- **Files modified:** 1 (source) + 1 (SUMMARY)

## Accomplishments

- **REVIEW-04 — the deep-specific arm of the milestone.** Added a NEW `$ALL_MODE` arm FIRST in deep-review.md's Phase-2c representable-range consequence list (between the list header and the existing "default mode" arm). When `$ALL_MODE` is set: a whole-repo file set is not a representable diff range (Codex represents only `--scope working-tree` or `--base <ref> --scope branch`; a whole-tree selection is neither) → FAIL CLOSED, reason slug `whole-repo-non-representable`, set `CODEX_SKIPPED`, do NOT launch, native-only — and the `--all` native per-chunk review completes normally / is never blocked (SAFE-01/SAFE-02). Evaluated first because `--all` is a branch-flip that wins over every per-mode diff detector (mirrors review.md Phase 0 line 85). Belt-and-suspenders OVER the unchanged default-fallback; the fallback is explicitly NOT removed (D-04).
- **Phase-10 inheritance confirmation note** (new, distinct text at the delegation contract, carrying a `Plan 10-01`/`Phase 10` marker plus the literal tokens `in_reviewed_set` and `cross-file`): confirms `/deep-review --all` inherits review.md's Phase-2/3/4 `$ALL_MODE` edits by delegation — the `in_reviewed_set` filter (REVIEW-02), the cross-chunk merge + RENDER-ONLY `cross-file` dedup display grouping (REVIEW-03/OUTPUT-03), and the Critical+Warning listing bar + coverage line (OUTPUT-01/02/04) — and that deep-review does NOT re-author them. The cross-file dedup is described as RENDER-ONLY (a display grouping, NOT a Phase-3 step / not a collapse of canonical findings).
- **Phase-10 render-narrowing confirmation note** (new, distinct text at the deep ≥70 threshold, carrying a `Phase 10`/`render` marker plus `--full`): confirms the ≥70 filter is intentionally left byte-unchanged and that `/deep-review --all`'s C+W default comes from review.md's `$ALL_MODE && !--full` RENDER-time listing bar (narrow at `render`, not at the threshold); Medium is counted-not-listed in plain `--all`, revealed by `--all --full` (OUTPUT-01/02, D-02).
- **Milestone bar held.** Diff-mode `/deep-review` is byte-stable: the diff contains ZERO deletion lines (pure additions). The default-fallback sentence, the existing slugs (`phase-diff-has-uncommitted-tail` / `range-not-identical` / `head-not-at-target`), the ≥70 threshold line, all diff-mode Codex arms, and the `allowed-tools` frontmatter line are byte-unchanged. No fenced code block introduced (fence count 16 = 16, HEAD vs working tree). `review.md` and `templates/scoring.md` untouched (asserted by the verify gate's `git diff --quiet`).

## Inheritance confirmation (REVIEW-02/03 + OUTPUT-01-04 reach /deep-review --all)

These requirements are satisfied for `/deep-review` BY INHERITANCE — no re-authoring in deep-review.md:

- **REVIEW-02 (`in_reviewed_set`)** — review.md Phase 3 step 2 (confirmed present at review.md line 683): gates on the dispatched union `$REVIEWED_UNION`. Reaches deep because deep executes review.md's Phase 3 by delegation.
- **REVIEW-03 (cross-chunk merge)** — review.md's accumulate→`AGENT_RESPONSES`→Phase-3-once seam (Phase 8) is intact; the cross-file dedup is RENDER-ONLY and does not re-author the merge (review.md line 757).
- **OUTPUT-03 (cross-file dedup)** — review.md Phase 4 RENDER grouping with `occurrence_count`/`occurrences` as render-local display variables (confirmed present at review.md line 753), preserving every `file:line`.
- **OUTPUT-01/02 (Critical+Warning default + `--full`)** — review.md Phase 4 `$ALL_MODE && !--full` listing bar (review.md lines 745-747); narrows deep's default-Medium at render.
- **OUTPUT-04 (coverage line)** — review.md Phase 4 coverage note with the P10-C fix (review.md lines 726-727).

The ONLY deep-specific `--all` touches in this plan are the Codex `$ALL_MODE` skip arm (EDIT A) and the two confirmation notes (EDIT B inheritance, EDIT C render-narrowing).

## Task Commits

Each task was committed atomically:

1. **Task 1: Codex `$ALL_MODE` skip arm + two Phase-10 confirmation notes** - `359abfd` (feat)

**Plan metadata (SUMMARY):** committed in this plan's docs commit.

## Files Created/Modified

- `plugins/vibe-check/commands/deep-review.md` - Added the `$ALL_MODE` Codex skip arm (slug `whole-repo-non-representable`) first in the Phase-2c consequence list; added a Phase-10 inheritance note at the delegation contract; added a Phase-10 render-narrowing note at the deep ≥70 threshold.
- `.planning/phases/10-reviewed-set-filter-cross-chunk-merge-noise-control/10-02-SUMMARY.md` - This summary.

## Decisions Made

None beyond the plan — followed 10-02-PLAN.md and the locked decisions D-04/D-05/D-02 as specified.

## Verify Gate

The plan's tightened `<verify>` automated gate PASSED. Notable hardening honored:

- The OR-grep that would false-pass on deep-review.md's pre-existing line-36 "inheritance/INHERITED" wording is replaced by SCOPED AND-checks requiring the SPECIFIC new note content: `Phase 10` AND `in_reviewed_set` AND `cross-file` co-occurring within the `## Phase contract`…`## Differences from` region; and `Phase 10` AND `render` AND `--full` co-occurring within the `### Phase 3 — Filter threshold`…`### Phase 3 — Codex collection` region.
- A SEPARATE assertion confirms Plan 10-01 landed in review.md before 10-02 is accepted: review.md Phase-3 region contains `in_reviewed_set` AND Phase-4 region contains `occurrence_count`.
- Placement check: list header < `whole-repo-non-representable` arm < "default mode" arm (the `--all` arm is FIRST).
- Scope isolation: `git diff --quiet -- review.md scoring.md` passes (deep-review.md only).

Both 10-01 dependency edits were independently confirmed present in review.md (line 683 `in_reviewed_set`; lines 753/757 `occurrence_count`) so the inheritance notes are accurate.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `.planning/` is gitignored and does not exist in the executor worktree (it lives in the main checkout). The SUMMARY was written into the worktree's `.planning/` path and force-staged (`git add -f`) so it commits on the worktree branch before the orchestrator force-removes the worktree, per the spawn instructions. No impact on the source edit, which is tracked normally.

## Known Stubs

None — this is a prompt-spec (markdown command-spec) edit; no code stubs, no hardcoded empty values, no placeholder data sources.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `/deep-review --all` now produces the same correct, merged, noise-controlled report as `/review --all` (by inheritance) PLUS a cleanly-named Codex fail-closed skip — the deep arm of the Phase-10 milestone is complete.
- Ready for Phase 11 (report-first / opt-in `--all --fix` governance) and Phase 12 (the dogfood efficacy run, where the named `whole-repo-non-representable` slug makes REVIEW-04 directly verifiable in a live `/deep-review --all`).
- No blockers.

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/commands/deep-review.md`
- FOUND: `.planning/phases/10-reviewed-set-filter-cross-chunk-merge-noise-control/10-02-SUMMARY.md`
- FOUND commit: `359abfd` (feat task)
- FOUND commit: `2a4798d` (docs summary)
- Plan `<verify>` automated gate: PASS (re-confirmed post-commit)

---
*Phase: 10-reviewed-set-filter-cross-chunk-merge-noise-control*
*Completed: 2026-06-22*
