---
phase: 10-reviewed-set-filter-cross-chunk-merge-noise-control
plan: 01
subsystem: api
tags: [vibe-check, review.md, all-mode, prompt-engineering, in_reviewed_set, cross-file-dedup, coverage-line, output-noise-bar]

# Dependency graph
requires:
  - phase: 07-walking-skeleton-selection-end-to-end-all
    provides: "$REVIEW_SET / $ALL_MODE / <files> block, mode-5 selection"
  - phase: 08-risk-rank-chunk-per-chunk-triage
    provides: "$CHUNK_PLAN per-file wc -l/wc -c columns, $CHUNK_REVIEW_FILES_i dispatched union, accumulate→Phase-3-once merge"
  - phase: 09-estimate-and-confirm-budget-gate
    provides: "in-memory cap run-state (cap_applied=K, chunk_total=N), {{S}}={{T}}−{{R}} coverage bucket, Phase-4.5 cap-field persistence"
provides:
  - "$ALL_MODE in_reviewed_set finding-validity filter (Phase 3 step 2): file ∈ $REVIEWED_UNION AND 1 ≤ line ≤ N (REVIEW-02)"
  - "$ALL_MODE RENDER-ONLY cross-file dedup display grouping (Phase 4): one row + (+N more occurrences) + full file:line list, canonical findings untouched (OUTPUT-03)"
  - "$ALL_MODE listing bar (Phase 4): C+W default, --full reveals Medium, narrowed at render not threshold (OUTPUT-01/02)"
  - "P10-C coverage arithmetic fix: {{S}}={{T}}−{{R}} exact (R+S=T), symlinks reported separately, cap/triage attribution + chunk clause (OUTPUT-04)"
  - "REVIEW-03 merge confirmed (not re-authored); finding shape stays diff-mode-identical"
affects: [10-02-deep-review-codex-arm, 11-report-first-opt-in-fixes, 12-dogfood-efficacy-run]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RENDER-ONLY cross-file dedup: collapse is a Phase-4 display grouping over individual findings, never a Phase-3 transform — the single-location finding contract the fix loop consumes stays intact"
    - "$ALL_MODE-guarded additive sibling blocks beside diff-mode lines (milestone bar: diff path byte-stable)"
    - "single-source coverage: $REVIEWED_UNION feeds both the in_reviewed_set membership test and the {{R}} coverage count (no drift)"

key-files:
  created:
    - .planning/phases/10-reviewed-set-filter-cross-chunk-merge-noise-control/10-01-SUMMARY.md
  modified:
    - plugins/vibe-check/commands/review.md

key-decisions:
  - "Cross-file dedup is RENDER-ONLY (Phase-4 display grouping), NOT a Phase-3 step 4b — adversarial-pass correction; preserves the per-location fix-loop contract and improves REVIEW-03 alignment"
  - "D-01 title-similarity rule: identical category AND (normalized-token Jaccard ≥ 0.7 OR one normalized title a substring of the other after stripping file-specific tokens) — conservative same-KIND"
  - "D-02 render mechanism: $ALL_MODE && !--full lists C+W only (Medium suppressed for both /review and /deep-review at render), --full reveals Medium; thresholds/scoring/bands untouched"
  - "P10-C fix #1: keep {{S}}={{T}}−{{R}} exact, report dropped symlinks as a separate {{non_regular_skipped}} count from $SELECTION_SKIPPED_SYMLINK outside R/T/S"
  - "P10-A and P10-B deliberately deferred AGAIN (only P10-C addressed) — this plan does not touch the Phase 0.2 packer or $CHUNK_PLAN serialization"

patterns-established:
  - "Render-only display grouping over individual canonical findings (occurrence_count/occurrences are render-local variables, never serialized onto the finding or the pass entry)"
  - "Coverage honesty: R+S=T invariant held exactly; non-regular exclusions tracked as a distinct category, not folded into the skipped bucket"

requirements-completed: [REVIEW-02, REVIEW-03, OUTPUT-01, OUTPUT-02, OUTPUT-03, OUTPUT-04]

# Metrics
duration: ~20min
completed: 2026-06-22
---

# Phase 10 Plan 01: Reviewed-Set Filter, Cross-Chunk Merge & Noise Control Summary

**`--all` audit output correctness: an `$ALL_MODE` `in_reviewed_set` finding-validity gate, a RENDER-ONLY cross-file dedup display grouping, a C+W/`--full` listing bar, and the P10-C coverage arithmetic fix — all confined to the `$ALL_MODE` branch so the diff path stays byte-stable.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-22 (worktree base 09a2624)
- **Completed:** 2026-06-22T17:08:46-04:00
- **Tasks:** 2
- **Files modified:** 1 source file (`plugins/vibe-check/commands/review.md`)

## Accomplishments

- **REVIEW-02** — Phase 3 step 2 now carries an `$ALL_MODE`-guarded `in_reviewed_set` sibling bullet replacing the `in_diff` membership check in `--all`: a finding survives iff `finding.file ∈ $REVIEWED_UNION` (the dispatched per-chunk `$CHUNK_REVIEW_FILES_i` union, = the `{{R}}` coverage set, NOT the pre-triage `$REVIEW_SET`) AND `1 ≤ finding.line ≤ N` where N is the per-file `wc -l` total already on `$CHUNK_PLAN` (no re-measure). Drop-and-count for hallucinated files / out-of-range lines; no re-anchoring.
- **OUTPUT-03** — Phase 4 render carries an `$ALL_MODE` RENDER-ONLY cross-file dedup grouping: same-`category` + similar-`title` findings spanning 2+ distinct files DISPLAY as one band-table row (primary `file:line` + `(+ N more occurrences)`) with the full `file:line` list in the detail block. The canonical findings stay individual through persistence → finalize → the fix loop.
- **OUTPUT-01/02** — Phase 4 render carries an `$ALL_MODE` listing bar: `!--full` lists Critical + Warning only (Medium suppressed for both `/review` and `/deep-review`, with an explicit "N Medium not shown — re-run with `--full`" line); `--full` also lists Medium. Narrowing at render, not at the threshold; Medium/Low still counted.
- **OUTPUT-04 + P10-C** — coverage line fixed so `R + S = T` holds exactly: `{{S}} = {{T}} − {{R}}` kept exact, the buggy "PLUS the tracked symlinks" clause removed, dropped symlinks reported as a separate `{{non_regular_skipped}}` count from `$SELECTION_SKIPPED_SYMLINK` outside the R/T/S arithmetic; `{{S}}` consumes both capped and triage skips in one bucket with attribution; a "reviewed top {{K}} of {{chunk_total}} chunks" clause reads the in-memory cap run-state.
- **REVIEW-03** — confirmed (not re-authored): the accumulate→`AGENT_RESPONSES`→Phase-3-once merge stays intact; the scored `--all` finding is byte-shape-identical to a diff-mode finding.

## Task Commits

Each task was committed atomically:

1. **Task 1: `$ALL_MODE` `in_reviewed_set` verify bullet + RENDER-only cross-file dedup grouping** — `895f308` (feat)
2. **Task 2: `$ALL_MODE` listing bar + P10-C coverage arithmetic fix** — `4ca4acd` (feat)

**Plan metadata:** committed separately with this SUMMARY (worktree mode — orchestrator merges).

## Files Created/Modified

- `plugins/vibe-check/commands/review.md` — Phase 3 step 2 `in_reviewed_set` sibling bullet; mode-5 step-e placeholder annotated as superseded; Phase 4 render listing bar + cross-file dedup grouping note; Phase 4 coverage line P10-C fix + cap/triage attribution + chunk clause. All additions `$ALL_MODE`-guarded.
- `.planning/phases/10-reviewed-set-filter-cross-chunk-merge-noise-control/10-01-SUMMARY.md` — this summary.

## Decisions Made

All four below were either the adversarial-pass-mandated interpretation or a Claude's-discretion choice the plan delegated:

1. **Cross-file dedup is RENDER-ONLY (adversarial-pass correction).** The original framing (a Phase-3 "step 4b" that collapsed multiple per-file findings into ONE canonical finding carrying `occurrence_count`/`occurrences`) was rejected: it broke the single-location finding contract (the Phase-5 fix-agent prompt passes each finding as an `id/file/line/...` object — a collapsed canonical finding would get only its primary occurrence fixed). The adopted design makes cross-file dedup a Phase-4 RENDER-TIME DISPLAY grouping only. The canonical findings stay individual through scoring → within-file dedup → filter → Phase-4.5 persistence (`stable_hash` per individual finding) → finalize → the Phase-5 fix loop. `occurrence_count`/`occurrences` are render-local display variables, never serialized onto the finding or the pass entry. This is a strictly safer interpretation of D-01 (every occurrence remains an independent, fixable, carry-forwardable finding) and it IMPROVES REVIEW-03 alignment (the canonical finding is now truly byte-shape-identical to a diff-mode finding). D-01's intent is preserved in full: one readable report row per cross-file pattern + an occurrence count + every `file:line` visible.
2. **D-01 title-similarity rule (Claude's discretion).** Group iff IDENTICAL `category` AND a conservative normalized-title match: lowercase both titles, strip file-specific tokens (paths, identifiers, quoted symbols, line numbers), then require normalized-token Jaccard ≥ 0.7 OR one normalized title is a substring of the other after the strip. Deliberately conservative so two distinct bugs sharing a category are never merged; the owner can tune the threshold after the Phase-12 dogfood.
3. **D-02 render mechanism (Claude's discretion).** A render-time band-listing filter keyed on `$ALL_MODE && !--full`: list C+W only by default (Medium suppressed for BOTH commands, narrowing `/deep-review`'s default-Medium back at RENDER), `--full` reveals Medium. The ≥70 / `<80` pipeline thresholds, the scoring formula, and the band math are all byte-unchanged.
4. **P10-C fix #1 (RESEARCH recommendation).** Keep `{{S}} = {{T}} − {{R}}` exact and report dropped symlinks as a separate `{{non_regular_skipped}}` count from `$SELECTION_SKIPPED_SYMLINK` outside the R/T/S arithmetic (rather than fix #2, folding symlinks into the denominator). This keeps `{{T}}` meaning "candidate source files the tool can actually review" — the honest audit denominator.

## Deviations from Plan

None - plan executed exactly as written.

Both per-task `<verify>` automated gates PASSED. No bugs, missing functionality, or blocking issues were encountered (prompt-engineering edits; no build/test harness for the prose). No CLAUDE.md-driven adjustments were needed (markdown command-spec edits introduce no new shell interpolation, SQL, secrets, or user-input surface — the only untrusted input touching these edits is finding data, handled by `in_reviewed_set`, threat T-10-01 mitigate).

## Deferred (deliberately, recorded so not lost)

- **P10-A** (chunk budget ignores rendered `<files>` prompt overhead; review.md Phase 0.2 packer ~lines 277-287) — **deferred again.** This plan's edits do not touch the Phase 0.2 packer. D-07 makes P10-A Claude's discretion; only P10-C is required for OUTPUT-04 coverage honesty.
- **P10-B** (`$CHUNK_PLAN` tab/newline serialization not path-safe for exotic filenames; review.md ~lines 263/291-304) — **deferred again.** This plan's edits do not touch `$CHUNK_PLAN` serialization. D-07 makes P10-B Claude's discretion.

Both remain candidates for a future hardening pass; neither is a milestone-bar blocker. P10-C (the coverage arithmetic fix) was the only one of the three required this phase, and it landed in Task 2.

## Issues Encountered

- `.planning/` is gitignored in this repo, so the phase directory did not exist in the worktree — created it and staged the SUMMARY with `git add -f`. The source edit (`review.md`) is tracked normally.
- The RESEARCH.md Pattern 3 / Code Examples still frame cross-file dedup as a Phase-3 "step 4b"; the PLAN's ADVERSARIAL-PASS REWRITE explicitly supersedes that (render-only). Followed the PLAN as authoritative.

## Milestone-Bar Verification

- Every addition is reachable ONLY when `$ALL_MODE` is set; no diff-mode line was edited in place — each `--all` block is an additive sibling beside the diff-mode line.
- Byte-unchanged anchors confirmed present after both edits: the diff-mode `in_diff` bullet, the within-file dedup line (step 4), the `5. Filter orchestrator_score < 80.` line, the fix-agent prompt object line (`id/file/line/title/problem/current_code/fix_hint/why_it_matters`), the Phase-4.5 `stable_hash` line, the coverage-overstatement anti-pattern, and the reviewed-partial overflow note.
- `templates/scoring.md`, `templates/output-format.md`, and the `allowed-tools` frontmatter line are byte-unchanged (verified via `git diff --quiet` / diff scan).
- No `^4b` line exists anywhere in review.md (cross-file dedup is render-only, not a Phase-3 step).

## Next Phase Readiness

- review.md's `--all` Phase 2/3/4 changes are landed; Plan 10-02 (deep-review.md Codex `$ALL_MODE` skip arm, REVIEW-04) can now confirm `/deep-review --all` inherits REVIEW-02/03/OUTPUT-01–04 by delegation and that the listing bar narrows deep's Medium default.
- No blockers. P10-A / P10-B remain deferred (non-blocking).

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/commands/review.md`
- FOUND: `.planning/phases/10-reviewed-set-filter-cross-chunk-merge-noise-control/10-01-SUMMARY.md`
- FOUND commit: `895f308` (Task 1)
- FOUND commit: `4ca4acd` (Task 2)
- Both per-task `<verify>` automated gates returned PASS.

---
*Phase: 10-reviewed-set-filter-cross-chunk-merge-noise-control*
*Completed: 2026-06-22*
