---
phase: 14-dogfood-critical-warning-fixes
plan: 03
subsystem: api
tags: [deep-review, codex-adversarial, sanitization, prompt-injection, cross-reference, vibe-check]

# Dependency graph
requires:
  - phase: 12-dogfood
    provides: "Dogfood findings DOGFIX-02 (line-cite drift) and DOGFIX-08 (Codex title injection surface)"
provides:
  - "deep-review.md cites review.md by stable section name instead of drifting line numbers (all 3 citations)"
  - "Codex `title` sanitize-and-keep contract (single-line; neutralize fences/backticks/newlines/control chars; finding kept; `=` permitted) in codex-adversarial.md"
  - "Phase 3 translation reminder in deep-review.md deferring title sanitization to the codex-adversarial.md contract"
affects: [15-dogfood-fix-loop-and-flag-value, phase-15-DOGFIX-10, deep-review, codex-adversarial]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sanitize-and-KEEP (cosmetic field): neutralize spoofing/injection vectors in place, never drop the finding — distinct from the file-field downgrade/drop posture used for path security boundaries"
    - "Cite cross-file references by stable section-NAME anchors, not by line number, so edits to the cited file can't misdirect the orchestrator"
    - "Single insertion point at translation time (Phase 3) covers both downstream consumers (Phase 4 render + Phase 5 Step B fix agent)"

key-files:
  created: []
  modified:
    - "plugins/vibe-check/commands/deep-review.md"
    - "plugins/vibe-check/agents/codex-adversarial.md"

key-decisions:
  - "DOGFIX-02 scoped to ALL THREE line citations into review.md (line 36 x2 + line 182), per D-02 'no hardcoded line-number citations' and RESEARCH Open Question 2."
  - "DOGFIX-08 placed in BOTH files (Open Question 1: BOTH) — full spec in the codex-adversarial.md contract (spec-of-record), one-line deferral reminder in deep-review.md Phase 3 (where translation runs)."
  - "Title allowlist deliberately WIDER than the file path class `^[A-Za-z0-9._/-]+$`; `=` explicitly permitted for Phase 15 DOGFIX-10 `flag=value` titles (shell=True, verify=False)."
  - "Title gets sanitize-and-KEEP, NOT the file field's downgrade/drop-on-reject — a title is cosmetic, not a path security boundary."

patterns-established:
  - "Sanitize-and-KEEP for cosmetic untrusted fields vs. downgrade/drop for path-security fields"
  - "Section-name cross-references over line-number cross-references"

requirements-completed: [DOGFIX-02, DOGFIX-08]

# Metrics
duration: ~3min
completed: 2026-06-23
---

# Phase 14 Plan 03: Dogfood Critical + Warning Fixes (deep-review surface) Summary

**deep-review.md now cites review.md by stable section name (Selection table / `--all` per-chunk dispatch loop / branch-flip guard) instead of drifting line numbers, and Codex `title` gets a sanitize-and-KEEP pass (fences/backticks/newlines/control chars neutralized, finding kept, `=` permitted) specified in the codex-adversarial.md contract and mirrored at the Phase 3 translation step.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-23T18:58:00-04:00 (approx)
- **Completed:** 2026-06-23T19:01:08-04:00
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- **DOGFIX-02 (Critical):** All three hardcoded line-number citations into `review.md` converted to section-NAME cites — line 36's `(~line 454)` → `**Selection table** (Phase 2)`, line 36's `(~line 581)` → `**`--all` per-chunk dispatch loop** (Phase 2)`, and line 182's `, line 85` tail dropped in favor of a name-only `**branch-flip guard**` cite. Line drift can no longer misdirect the orchestrator.
- **DOGFIX-08 (Warning):** Added a `### (c) Title sanitization (sanitize-and-KEEP)` subsection to the codex-adversarial.md contract — single-line reduction + neutralize backtick/code-fence sequences, newlines, and control chars, KEEPING the finding; allowlist explicitly wider than the path class and explicitly permitting `=` for Phase 15 DOGFIX-10 compatibility. The title mapping row (line 53) flags the step; deep-review.md Phase 3 translation (line 245) carries a one-line reminder deferring to the contract.

## Task Commits

Each task was committed atomically:

1. **Task 1: DOGFIX-02 — convert all three line-number citations into review.md to section-name cites** - `5f215a2` (fix)
2. **Task 2: DOGFIX-08 — Codex title sanitize-and-keep (contract + executor mirror)** - `f3de191` (fix)

_Note: `.planning/` is gitignored by repo convention (see commit `2e9d61d`). This SUMMARY is force-added into the worktree branch so the orchestrator's merge carries it; STATE.md/ROADMAP.md updates are the orchestrator's to make after the wave merges._

## Files Created/Modified
- `plugins/vibe-check/commands/deep-review.md` - Section-name cross-references into review.md (3 sites); Phase 3 title-sanitization reminder.
- `plugins/vibe-check/agents/codex-adversarial.md` - Title sanitize-and-KEEP contract (`### (c)` subsection) + title mapping row flag.

## Decisions Made
- **DOGFIX-02 scope = all three citations.** RESEARCH found a THIRD line citation (deep-review.md:182, `, line 85`) that CONTEXT.md did not name. D-02's intent is "no hardcoded line-number citations," so all three were converted (RESEARCH Open Question 2 resolved IN scope). The only remaining `lines NNN` mention in the file is `lines 187-188`, a self-reference to deep-review.md's own default-fallback sentence — not a citation into review.md — correctly left untouched.
- **DOGFIX-08 placement = BOTH files.** The contract (codex-adversarial.md) owns the field mapping, so the full spec lives there; the executor (deep-review.md Phase 3) is what actually runs translation, so it carries a one-line deferral reminder. This single insertion point at translation time covers both downstream consumers (Phase 4 render + Phase 5 Step B fix agent).
- **Title allowlist permits `=` (hard constraint).** The class is deliberately wider than the file path class `^[A-Za-z0-9._/-]+$`; only fences/backticks, newlines, and control chars are neutralized. This keeps `flag=value` titles (e.g. `shell=True`, `verify=False`) usable for Phase 15 DOGFIX-10.
- **Sanitize-and-KEEP, not downgrade/drop.** The file field's downgrade/drop-on-reject posture (a path security boundary) was deliberately NOT copied onto title — a title is cosmetic, so the finding is always kept and only its dangerous characters are neutralized.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- **SUMMARY.md / `.planning/` is gitignored.** The `parallel_execution` directive requires SUMMARY.md to be committed before return (the orchestrator force-removes the worktree), but `.planning/` is gitignored by established repo convention (commit `2e9d61d` deliberately untracked a prior SUMMARY). Resolution: the SUMMARY was force-added (`git add -f`) into the worktree branch so the orchestrator's merge carries it, satisfying the "committed before return" requirement without changing the repo's gitignore convention.

## User Setup Required
None - no external service configuration required. Prose-only edits to two `.md` files; no package installs (Package Legitimacy Gate correctly skipped).

## Next Phase Readiness
- The title sanitize-and-keep rule's `=`-survives property is a read-check on the stated allowlist; the LIVE fix-agent commit of a `flag=value` title is exercised in **Phase 15 (DOGFIX-10)** — the contract is now in place for that to build on.
- Both fixes are contract/prose hardenings on the `/deep-review` surface; no runtime/test regression risk. No blockers.

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/commands/deep-review.md`
- FOUND: `plugins/vibe-check/agents/codex-adversarial.md`
- FOUND: `.planning/phases/14-dogfood-critical-warning-fixes/14-03-SUMMARY.md`
- FOUND commit: `5f215a2` (Task 1, DOGFIX-02)
- FOUND commit: `f3de191` (Task 2, DOGFIX-08)

---
*Phase: 14-dogfood-critical-warning-fixes*
*Completed: 2026-06-23*
