---
phase: 61-release-gate-decision-reliability
plan: 02
subsystem: release
tags: [release, live-smoke, spend-approval, proposal]
requires: []
provides:
  - "61-LIVE-SMOKE-PROPOSAL.md with `Status: APPROVED (owner, 2026-10-30)` and an `## Owner ruling` section (gate input for 61-04 Task 1)"
affects: [61-04, 61-05]
tech-stack:
  added: []
  patterns: ["paid/live work runs only behind a bounded proposal whose Status line the owner sets (D-01)"]
key-files:
  created:
    - .planning/phases/61-release-gate-decision-reliability/61-LIVE-SMOKE-PROPOSAL.md
  modified: []
decisions:
  - "Owner APPROVED the three-session live smoke of candidate 0d2be77 on 2026-10-30 (est. $20–30, not a cap), with no conditions beyond the proposal"
  - "GATE-03 is not marked complete by this plan: the approval enables the live check, and the requirement is met only when 61-04 runs the smoke (or the owner waives it at sign-off)"
metrics:
  duration: "~5 min (resume after checkpoint; Task 1 written earlier in the session)"
  completed: 2026-10-30
  tasks: 2
  files: 1
requirements: [GATE-03]
---

# Phase 61 Plan 02: Bounded live-smoke proposal + owner ruling Summary

A plain-terms proposal for a three-session live smoke of the 2.14.0 candidate `0d2be77` (default review route plus Close out only, est. $20–30 with no cap, stop rules tied to D-05/D-07). The owner approved it on 2026-10-30, so plan 61-04 is now cleared to run the smoke. Nothing paid ran in this plan.

## Tasks

| Task | Name | Commit | Files |
|---|---|---|---|
| 1 | Write the bounded live-smoke proposal | 81069b0 | 61-LIVE-SMOKE-PROPOSAL.md |
| 2 | Owner approves or declines (checkpoint:decision) | a638f34 | 61-LIVE-SMOKE-PROPOSAL.md |

## Owner ruling

- Selection, verbatim: "Approve (Recommended)"
- Date and channel: 2026-10-30, the owner's own AskUserQuestion selection in the main orchestrator session (not relayed by another agent).
- Conditions: none beyond the proposal as written.

## Verification (observed)

- Task 1 verify (sections present, `Status: PROPOSED`, no Cap column): passed when Task 1 was committed (81069b0).
- Task 2 verify `grep -Eq "^Status: (APPROVED|DECLINED) \(owner, YYYY-MM-DD\)"`: printed `VERIFY_OK`.
- `## Owner ruling` heading present: printed `RULING_OK`.
- `git log -1 --format='%h %s' -- 61-LIVE-SMOKE-PROPOSAL.md` returned `a638f34 docs(61): record live-smoke proposal ruling`.
- Title now reads `(APPROVED)`. No live or paid session was run.

## Deviations from Plan

None in the tasks themselves; both were executed as written.

One bookkeeping call: the plan's frontmatter lists `requirements: [GATE-03]`, but the requirements file was **not** checked off for GATE-03 here. This plan only approves the live check. The check itself happens in 61-04, or the owner waives it at sign-off.
- **Cost if wrong:** GATE-03 stays unchecked until 61-04/61-05 marks it. If the owner reads approval alone as meeting it, one checkbox needs flipping.

## Known Stubs

None.

## Next

61-04 Task 1 reads the `Status: APPROVED` line as its gate and runs the smoke per the proposal's Method and Stop rules.

## Self-Check: PASSED
