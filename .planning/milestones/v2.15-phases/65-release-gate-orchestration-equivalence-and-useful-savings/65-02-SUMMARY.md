---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
plan: 02
subsystem: release-gate
tags: [live-smoke, owner-approval, GATE-06, spend-proposal]
requires:
  - phase: 65-01
    provides: "WR-02 verdict QUALIFYING; owner go GRANTED for the one D-08 fix round (65-03)"
provides:
  - "65-LIVE-SMOKE-PROPOSAL.md with Status: APPROVED (owner, 2026-11-16)"
affects: [65-04, 65-06]
tech-stack:
  added: []
  patterns: ["bounded spend proposal + owner ruling recorded verbatim (61 skeleton)"]
key-files:
  created:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-LIVE-SMOKE-PROPOSAL.md
  modified: []
key-decisions:
  - "Owner APPROVED the three-session live smoke of the 2.15.0 candidate (default review + Close out), est. $20-30, estimate not a cap (2026-11-16)"
  - "Stop rules state the one D-08 fix round is already used by WR-02, so a qualifying smoke failure needs the owner's explicit go for a second round (D-09)"
requirements-completed: []
duration: ~15min
completed: 2026-11-16
---

# Phase 65 Plan 02: Live-smoke proposal and owner ruling Summary

**Bounded three-session live smoke of the 2.15.0 candidate (S1 review + defer, S2 Close out, S3 Close out via the decision card; est. $20–30, no cap), approved by the owner on 2026-11-16.**

## Performance

- **Completed:** 2026-11-16
- **Tasks:** 2 of 2 (Task 1 by this executor; Task 2 ruling recorded by the main session)
- **Files:** 1 created

## Accomplishments

- Wrote 65-LIVE-SMOKE-PROPOSAL.md on the Phase 61 skeleton: Why, Scope (default review and `--finalize` live; GSD, range, PR, incremental, `--all` and fix loop offline-only, listed for waiver), Method, cost table `| Part | Estimate | Basis |` with no cap column, Stop rules, What this does NOT trigger, If declined (with the waiver sentence).
- Stop rules say directly that the 65-01 WR-02 go already used the one fix round. So a qualifying smoke failure, or a smoke re-run after a fix, each needs a separate go from the owner.
- The owner's ruling, `Status: APPROVED (owner, 2026-11-16)` with selection "Approve (Recommended)", was recorded by the main session via AskUserQuestion (commit 368ba54).

## Task Commits

1. **Task 1: Write the bounded live-smoke proposal** - `3c26d68` (docs). The Task 1 check printed `OK`.
2. **Task 2: Owner ruling** - `368ba54` (docs, committed by the main session). The Task 2 check printed `VERIFY_OK` when this executor re-ran it.

## Deviations from Plan

**1. [Rule 3 - Sequencing] Committed the proposal before the owner ruling**
- **Found during:** Task 1
- **Issue:** The plan's Task 1 says "Do not commit yet (Task 2 commits after the ruling)". The orchestrator notes said to commit the proposal with its pending status and return the checkpoint.
- **Fix:** Followed the orchestrator. Committed `Status: PROPOSED` as 3c26d68, and the main session recorded the ruling separately as 368ba54. The history now shows the proposal before the ruling, as two commits instead of one.
- **Cost if wrong:** None to behaviour. There is one extra commit in history, and the pending status was briefly the committed state. Plan 65-06 checks the current Status line, so nothing could have run on PROPOSED.
- **Files modified:** 65-LIVE-SMOKE-PROPOSAL.md
- **Commit:** 3c26d68

## Assumption Drift (advisory)

- **Found during:** Task 1
- **Planned:** the stop rules gave the second-round condition as conditional ("if 65-REPRO-WR02.md shows the fix round was already used").
- **Actual:** 65-REPRO-WR02.md shows `Owner go: GRANTED (owner, 2026-11-16)`, so the proposal states it as fact: the round is used, and any qualifying smoke failure needs the owner's D-09 go.
- **Cost if wrong:** If 65-03 were abandoned, the round would still be free. The wording would then overstate what's needed, which is the safe direction.

## Issues Encountered

None.

## Next Phase Readiness

- 65-06 may run the smoke after the free gates pass on the candidate from 65-03. It is limited to the three named sessions plus one invalid-run retry.
- 65-04 README wording: a live check is in scope for 2.15.0, covering the default route and Close out only.
- GATE-06 isn't complete until the smoke records a result (65-06), so no requirement was marked complete here.

## Self-Check: PASSED

- FOUND: 65-LIVE-SMOKE-PROPOSAL.md (tracked)
- FOUND: 3c26d68, 368ba54
