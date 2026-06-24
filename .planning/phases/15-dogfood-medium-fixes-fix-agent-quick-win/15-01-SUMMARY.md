---
phase: 15-dogfood-medium-fixes-fix-agent-quick-win
plan: 01
subsystem: report-rendering
tags: [commonmark, markdown-fence, prompt-injection, display-integrity, vibe-check, output-format]

# Dependency graph
requires:
  - phase: 14-dogfood-critical-warning-fixes
    provides: Phase-14-corrected prose baseline (DOGFIX-04/08 + Unicode title sanitization) that this lands on
provides:
  - "Longest-run-aware fence-sizing rule at the output-format.md {{current_code}} render site — closes the report-spoofing fence-escape (Defect A / DOGFIX-09)"
affects: [16-deterministic-core-score, 18-rerun-dogfood-finalize]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Render-time longest-run-aware code fencing (CommonMark): size the fence by max(3, longest-internal-backtick-run + 1) so an untrusted snippet renders verbatim and cannot escape its block"

key-files:
  created:
    - .planning/phases/15-dogfood-medium-fixes-fix-agent-quick-win/15-01-SUMMARY.md
  modified:
    - plugins/vibe-check/templates/output-format.md

key-decisions:
  - "D-01: longest-run-aware fencing (not strip/escape, not indented blocks) — renders verbatim, zero visual change for normal code"
  - "D-01a: deterministic per-finding prose rule lives ONLY at the {{current_code}} render site; surrounding template structure preserved byte-identical"

patterns-established:
  - "Untrusted-snippet render path: structural CommonMark fence-sizing guard instead of mutating the displayed code"

requirements-completed: [DOGFIX-09]

# Metrics
duration: 4min
completed: 2026-06-23
---

# Phase 15 Plan 01: Defect A — `{{current_code}}` Fence-Escape Fix Summary

**Replaced the bare triple-backtick fence around the attacker-influenceable `{{current_code}}` snippet with a render-time CommonMark longest-run-aware fence-sizing rule (`max(3, N+1)` backticks), so an embedded ``` run can no longer close the report fence early and spoof the report.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-06-24T00:06:00Z
- **Completed:** 2026-06-24T00:10:34Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Closed DOGFIX-09 Defect A: the `{{current_code}}` render site (output-format.md L41-43) no longer uses a bare 3-backtick fence pair that a snippet-internal ``` run could close early.
- Installed a deterministic per-finding rule the orchestrator LLM applies: scan the snippet for the longest run of consecutive backticks (N, 0 if none), open AND close with a tagless fence of `max(3, N+1)` backticks, render the snippet verbatim.
- Preserved display integrity: the rule explicitly forbids strip/escape/mutate, so a snippet legitimately containing a fence still renders truthfully (the reviewer sees exactly the reviewed code).
- One-clause CommonMark rationale embedded inline (a fence of K backticks closes only on a run of ≥ K backticks → a fence of N+1 cannot be closed by any internal run).

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace the bare `{{current_code}}` fence with a render-time longest-run fence-sizing rule (D-01 / D-01a)** - `055f6f5` (fix)

## Files Created/Modified
- `plugins/vibe-check/templates/output-format.md` - Replaced the bare ` ``` `/`{{current_code}}`/` ``` ` trio (old L41-43) with a single-line deterministic fence-sizing rule; `{{problem}}` (unfenced), `{{#if fix_hint}}Fix direction: {{fix_hint}}{{/if}}`, the `Why:` line, and the `---` separators are unchanged; the outer documentation-example fences are untouched.

## Decisions Made
- None beyond the locked D-01/D-01a. The exact prose wording (D-01a discretion) was authored to read as a per-finding algorithm rather than a vague "escape the snippet", per the RESEARCH §"Defect A" guidance. The fence was kept tagless (no language tag) to match the prior template and keep the info-string backtick-free.

## Deviations from Plan

None - plan executed exactly as written. The single task verified clean (rule present, `{{#if fix_hint}}` structure intact, no bare-fence wrapper remains, `{{current_code}}` referenced exactly once) with no auto-fixes required.

## Issues Encountered
- `grep -P` is unavailable on this macOS/BSD grep, so the "bare fence gone" verification was re-run with a portable `awk` check (confirmed PASS). No impact on the change itself.

## Scope Note
This plan covered **Defect A only** (the `output-format.md` fence-escape). Defects B (multi-site fix commit pathspec) and C (commit-title `=` allowlist) from the same CONTEXT/DOGFIX-09 batch live in plan **15-02** (a sibling worktree agent in this wave) — not touched here.

## Known Stubs
None — this is a complete prose rule, fully wired into the existing Critical-finding render block (and inherited by Warning/Medium via "[same table + per-finding format as Critical]").

## User Setup Required
None - no external service configuration required. This is an instruction-prose-only edit with no new input path; it reduces attack surface (removes an escapable delimiter from the renderer).

## Next Phase Readiness
- Defect A's fence-escape sub-defect of DOGFIX-09 is closed on the Phase-14-corrected baseline.
- No runtime/agent-dispatch/state-schema changes — Phase 16's `score.py` extraction is unaffected.
- Phase human gate (`/gsd:verify-work`) can confirm the rendered Critical-finding block still reads coherently and the snippet renders verbatim.

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/templates/output-format.md` (modified, L41 rule present)
- FOUND: `.planning/phases/15-dogfood-medium-fixes-fix-agent-quick-win/15-01-SUMMARY.md`
- FOUND: commit `055f6f5` (Task 1)

---
*Phase: 15-dogfood-medium-fixes-fix-agent-quick-win*
*Completed: 2026-06-23*
