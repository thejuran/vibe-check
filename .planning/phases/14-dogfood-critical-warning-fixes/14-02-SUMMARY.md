---
phase: 14-dogfood-critical-warning-fixes
plan: 02
subsystem: docs
tags: [scoring, banding, architecture-doc, drift-reduction, single-source-of-truth]

# Dependency graph
requires:
  - phase: 12-dogfood-and-release-v2.3
    provides: "the --all whole-codebase dogfood review that surfaced these defects (DOGFIX-03/04/05)"
provides:
  - "false-positive-rules.md reduced to the qualitative 'Always Filter Out' list + a single pointer to scoring.md as the canonical scoring source (DOGFIX-03 + DOGFIX-05)"
  - "architecture.md reconciled — no 'Opus + thinking' claim, version de-pinned, intent-doc path generalized to both layouts, cost figures softened (DOGFIX-04)"
affects: [16-deterministic-core-score-py, scoring.md consumers, architecture.md readers, orchestrator model-tiering claims]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Drift-surface removal over copy-resync: delete the duplicate/drift surface (orphan scoring contract, pinned cost/version) rather than re-syncing a second copy that re-rots"
    - "Single-source-of-truth pointer: a doc that no longer owns a concept points at the canonical owner (false-positive-rules.md -> scoring.md) instead of restating it"

key-files:
  created: []
  modified:
    - plugins/vibe-check/templates/false-positive-rules.md
    - plugins/vibe-check/docs/architecture.md

key-decisions:
  - "D-05/D-03: deleted both scoring sections (Confidence Scoring Guide table + Scoring Criteria point-values) as ONE atomic deletion and added a single pointer to scoring.md — not a corrected copy, which would re-rot"
  - "D-04: de-pinned version and cost figures (qualitative range + pointer to deep-review.md's Cost note) rather than re-pinning today's exact numbers, which would re-create the drift bug"
  - "D-04: fixed the substantive contradictions precisely — dropped forbidden '+ thinking', corrected to <TOP> (Opus default / Fable opt-in) on architecture+bugs, generalized intent-doc path to both flat and milestone-nested layouts; kept the correct 'Sonnet for /review' claim"

patterns-established:
  - "Pointer-not-copy: when a value's canonical owner exists elsewhere, point at it; never keep a second copy that can drift"
  - "De-pin drift-prone specifics: versions and cost figures that change on every release are described qualitatively or by reference, not hardcoded"

requirements-completed: [DOGFIX-03, DOGFIX-05, DOGFIX-04]

# Metrics
duration: ~8min
completed: 2026-06-23
---

# Phase 14 Plan 02: Dogfood Critical + Warning Fixes (cross-file drift) Summary

**Deleted the orphaned second scoring contract (with its phantom "High" band) from false-positive-rules.md and pointed it at scoring.md, then reconciled architecture.md by fixing the forbidden "Opus + thinking"/path contradictions and de-pinning its drift-prone version and cost figures.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-23T22:52:00Z
- **Completed:** 2026-06-23T23:00:02Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- **DOGFIX-03 + DOGFIX-05:** Removed the entire orphan scoring contract from `false-positive-rules.md` — both the "Confidence Scoring Guide" table (which held the phantom non-canonical "High" band, DOGFIX-03) and the "Scoring Criteria" `+20`/`-50` point-value section (DOGFIX-05) — in one atomic deletion. Kept only the qualitative "Always Filter Out" list (all 6 categories) and added a single pointer to `scoring.md` as the canonical scoring/banding source. No non-canonical band name survives anywhere in the file.
- **DOGFIX-04:** Reconciled `architecture.md` against the authoritative specs without re-pinning drift-prone specifics: de-pinned the `(v2.1.0)` H1 version; corrected the model-tiering line to `<TOP>` (Opus default, Fable opt-in) on `architecture`+`bugs` for `/deep-review` and dropped the forbidden "+ thinking" (deep-review.md forbids any thinking parameter), while keeping the correct "Sonnet for `/review`"; generalized the intent-doc path to both `.planning/phases/` and milestone-nested `.planning/milestones/<m>-phases/` layouts; softened the pinned cost figures (~$0.50 / ~$1.80 / ≈ $3.30) to a qualitative range plus a pointer to deep-review.md's canonical Cost note.

## Task Commits

Each task was committed atomically:

1. **Task 1: DOGFIX-03 + DOGFIX-05 — delete orphan scoring contract, point at scoring.md** - `7b27a6d` (fix)
2. **Task 2: DOGFIX-04 — reconcile architecture.md (fix contradictions, soften drift-prone specifics)** - `2398bdd` (fix)

_STATE.md/ROADMAP.md are orchestrator-owned and intentionally NOT touched here (worktree/parallel execution). The orchestrator updates them centrally after the wave merges._

## Files Created/Modified
- `plugins/vibe-check/templates/false-positive-rules.md` - Deleted the Confidence Scoring Guide table + Scoring Criteria point-value section; kept the qualitative "Always Filter Out" list; added a single pointer to `scoring.md` (net 6 insertions, 35 deletions)
- `plugins/vibe-check/docs/architecture.md` - De-pinned version; fixed model-tiering line (<TOP>, no "+ thinking"); generalized intent-doc path; softened cost figures to a range + pointer (9 insertions, 7 deletions)

## Decisions Made
- Followed the plan's locked decisions exactly (D-03, D-04, D-05). The pointer wording (Task 1) and the qualitative cost phrasing (Task 2(d)) were the only Claude's-discretion items, both bounded by the plan: the pointer directs all banding/scoring questions to `scoring.md`; the cost note gives a relative-cost framing and points at deep-review.md's canonical Cost note rather than re-pinning dollars.
- Left out-of-scope line 18 (`−50 pre-existing, −50 silenced`) intact per RESEARCH (descriptive, not a contradiction with scoring.md).

## Deviations from Plan

None - plan executed exactly as written. No bugs, missing functionality, blockers, or architectural changes encountered (both edits are documentation prose with no executable change). No package installs. No authentication gates.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The orphan scoring contract is gone, so Phase 16's `score.py` has one fewer prose scoring surface to reconcile — banding now lives only in `scoring.md`.
- `architecture.md` no longer misdirects the orchestrator on model tiering or the intent-doc path, and its version/cost claims are de-pinned so they won't re-drift on the next release (Phase 18's version bump won't re-stale the H1).
- No blockers. This plan (14-02) is wave 1, independent of 14-01 and 14-03 (no shared files).

## Self-Check: PASSED

- `plugins/vibe-check/templates/false-positive-rules.md` — FOUND (modified, committed in 7b27a6d)
- `plugins/vibe-check/docs/architecture.md` — FOUND (modified, committed in 2398bdd)
- Commit `7b27a6d` — FOUND in git log
- Commit `2398bdd` — FOUND in git log
- All plan `<verification>` grep assertions PASS (no Confidence Scoring Guide, no "Include as High", scoring.md pointer present, no v2.1.0, no "Opus + thinking")

---
*Phase: 14-dogfood-critical-warning-fixes*
*Completed: 2026-06-23*
