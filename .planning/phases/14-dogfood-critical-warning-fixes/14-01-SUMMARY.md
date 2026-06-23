---
phase: 14-dogfood-critical-warning-fixes
plan: 01
subsystem: orchestration-prose
tags: [review.md, finalize, state-file, self-identity-render, untrusted-input-guard, dogfood]

# Dependency graph
requires:
  - phase: 13-safer-fix-loop-default
    provides: the Phase 5 fix-loop prose (Step A/B/C) this plan's DOGFIX-01 edits
provides:
  - "Copy-paste-correct abandon/resume hint rendered by command self-identity (/vibe-check:review | /vibe-check:deep-review)"
  - "Phase 0.5 binds one canonical $STATE_FILE per mode; Finalize consumes it (mode-aware --all --finalize)"
  - "Verified the PRIOR_PHASE→mv allowlist guard survives the file's other edits (DOGFIX-07 satisfied, no rewrite)"
affects: [phase-18-close, CLOSE-01, deep-review-finalize, "--all --finalize"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-source-of-truth: one Phase-0.5-bound $STATE_FILE handle consumed by Finalize (no second resolver)"
    - "Self-identity slash-command render (positional, never a $COMMAND/{{command}} variable)"

key-files:
  created: []
  modified:
    - plugins/vibe-check/commands/review.md

key-decisions:
  - "DOGFIX-06 binds $STATE_FILE in all three Phase 0.5 mode branches (additive) rather than adding a Finalize-local if/else resolver — single source of truth, can't re-drift (D-06)"
  - "DOGFIX-06a: archive mv source AND destination derive from the same resolved $STATE_FILE; the by-mode/all/<scope-hash>.json form keeps --all archived names unique"
  - "DOGFIX-07 treated as verify-not-rebuild: the existing guard already meets the acceptance bar; strengthening was declined to avoid regression (D-07, RESEARCH)"
  - "Reworded the line-827 prohibition phrase to drop the literal {{command}} token (kept its meaning) so the plan's file-wide ! grep {{command}} verify passes without weakening the prohibition"

patterns-established:
  - "Mode-aware path resolution lives in Phase 0.5; every downstream consumer reads the one bound $STATE_FILE variable"
  - "deep-review.md inherits Phase 5 + Finalize + Phase 0.5 by delegation, so fixing review.md fixes /deep-review for all three defects — no separate deep-review.md edit"

requirements-completed: [DOGFIX-01, DOGFIX-06, DOGFIX-07]

# Metrics
duration: 18min
completed: 2026-06-23
---

# Phase 14 Plan 01: Dogfood Critical + Warning Fixes (review.md) Summary

**Fixed the copy-paste-broken abandon/resume hint and the `--all --finalize` wrong-state-file bug in `commands/review.md`, and verified the untrusted `PRIOR_PHASE`→`mv` allowlist guard survived — restoring a working resume command and unblocking whole-codebase finalize (the exact defect that forced Phase 12 to skip `--finalize`).**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-06-23 (worktree agent-a59655ae82899f4f6)
- **Completed:** 2026-06-23
- **Tasks:** 3 (2 edit + 1 verify-only checkpoint)
- **Files modified:** 1 (`plugins/vibe-check/commands/review.md`)

## Accomplishments
- **DOGFIX-01 (Critical):** Step C option 3 "Abandon for now" now prints a resume command rendered by command self-identity — `/vibe-check:review ${original_args}` under `/review`, `/vibe-check:deep-review ${original_args}` under `/deep-review` — replacing the OLD `/turingmind-code-review:` namespace and the unbound `{{command}}`/`{{original_args}}` mustache placeholders.
- **DOGFIX-06 (Warning, HEADLINE):** Phase 0.5 now binds one canonical `$STATE_FILE` in each of its three mode branches (GSD `<$PHASE_ID>.json`, other-modes `<repo>-<branch>.json`, `--all` alias `STATE_FILE="$ALL_STATE_FILE"`). Finalize consumes only `$STATE_FILE` at all three sites (no-state check, state read, archive `mv`), with no Finalize-local resolver. `--all --finalize` now resolves the `by-mode/all/<scope-hash>.json` key instead of an unset `<$PHASE_ID>` path.
- **DOGFIX-07 (Warning, verify-only):** Confirmed the executable `PRIOR_PHASE` allowlist (`^[A-Za-z0-9._-]+$`) survived Tasks 1-2 — present inside a real bash fence, fails closed to `PRIOR_PHASE="unknown"`, precedes the only untrusted-consuming `mv` (line 71 < line 75), and the mv-sweep confirms no second unguarded untrusted→`mv` flow. No rewrite performed. Human sign-off received.

## Task Commits

Each task was committed atomically:

1. **Task 1: DOGFIX-01 — self-identity resume hint (Step C option 3)** — `9e52f81` (fix)
2. **Task 2: DOGFIX-06 — mode-aware Finalize state file via Phase 0.5 `$STATE_FILE`** — `841df69` (fix)
3. **Task 3: DOGFIX-07 — verify the `PRIOR_PHASE`→`mv` guard** — verify-only checkpoint, approved, no commit (no edit made)

_Note: STATE.md and ROADMAP.md are owned by the orchestrator post-merge and were NOT touched._

## Files Created/Modified
- `plugins/vibe-check/commands/review.md` — (1) Step C option 3 resume hint rendered by self-identity; (2) Phase 0.5 binds `$STATE_FILE` in all three mode branches and Finalize consumes it (no-state check, state read, archive mv); (3) line-827 prohibition phrase reworded to drop the literal `{{command}}` token while keeping its meaning. The DOGFIX-07 guard block (lines 67-77) was left unchanged (verified).

## Verification

All seven plan-level checks pass against the post-edit file:

| # | Check | Result |
| - | ----- | ------ |
| 1 | `! grep -q 'turingmind-code-review:'` (DOGFIX-01) | PASS |
| 2 | `! grep -q '{{command}}'` (DOGFIX-01) | PASS |
| 3 | `grep -cE '(^|[^A-Z_])STATE_FILE='` ≥ 3 (DOGFIX-06 bindings) | PASS (3) |
| 4 | `grep -qF 'STATE_FILE="$ALL_STATE_FILE"'` (DOGFIX-06 --all alias) | PASS |
| 5 | Finalize block has `mv "$STATE_FILE"` and NOT the hardcoded `<$PHASE_ID>.json` archive | PASS |
| 6 | `grep -q 'scope_label'` (DOGFIX-06: correct line-58 use preserved) | PASS |
| 7 | `grep -qF '^[A-Za-z0-9._-]+$'` (DOGFIX-07 guard present) | PASS |

DO-NOT-TOUCH assertions also confirmed: line 58 `{{scope_label}}` "Phase {{$PHASE_ID}}" and line 74 `[ "$PRIOR_PHASE" != "$PHASE_ID" ]` are both unchanged.

**Live end-to-end proof of DOGFIX-06** (`--all --finalize` actually completes) is deferred to Phase 18 CLOSE-01 — it depends on the installed plugin cache being in sync (RESEARCH Runtime State Inventory). Phase 14 self-verifies by grep only, as the plan specifies.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded the line-827 prohibition to clear a self-tripping file-wide verify**
- **Found during:** Task 1
- **Issue:** The plan's Task-1 verify (`! grep -q '{{command}}'`, file-wide) and acceptance criterion ("does NOT contain the string `{{command}}`") require ZERO occurrences of `{{command}}` in the file. But line 827 (a `--all` skip-condition prose block, NOT the defect site) legitimately contained `{{command}}` inside a *prohibition* phrase: "each rendered hint names ONE command (its own) … never a `$COMMAND`/`{{command}}` variable." RESEARCH knew line 827 mentions the token but the plan's verify was authored file-wide, so removing only line 893's placeholder would have left the verify failing.
- **Fix:** Reworded line 827's prohibition to `$COMMAND`/mustache-style command variable — dropping the literal `{{...}}` token while preserving the prohibition's exact intent (don't use a command-name variable). Minimal change, in the file I own.
- **Files modified:** plugins/vibe-check/commands/review.md (line 827)
- **Commit:** `9e52f81` (folded into the Task-1 commit)
- **Sign-off:** Acknowledged and accepted at the Task-3 checkpoint.

## Known Stubs

None — the edits are complete prose changes; no placeholders, TODOs, or unwired data introduced.

## Threat Flags

None — no new security-relevant surface. DOGFIX-06 changes WHICH existing state key Finalize reads/archives (the deterministic scope-hash path, not user-supplied input); DOGFIX-07 verified the existing `PRIOR_PHASE`→`mv` mitigation (threat T-14-01) survived. Both align with the plan's threat register.

## Self-Check: PASSED

- `plugins/vibe-check/commands/review.md` — FOUND
- `.planning/phases/14-dogfood-critical-warning-fixes/14-01-SUMMARY.md` — FOUND
- Commit `9e52f81` (Task 1, DOGFIX-01) — FOUND
- Commit `841df69` (Task 2, DOGFIX-06) — FOUND
- Commit `0017ef4` (SUMMARY) — FOUND
