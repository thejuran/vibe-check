---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 09
subsystem: measurement / owner decision
tags: [finalize, step-count, footprint, cross-call, owner-decision]
requires: ["63-08", "63-04"]
provides:
  - "63-COUNTS.md '## After the extraction alone (commit c7d92c9)': verdict PASS, figures, maintenance added, same-behaviour checks, extraction commits, revert state"
  - "63-REPRO.md '## What each fix would add' and '## Owner decision' (X1-X6 all fix)"
affects: ["63-10", "63-11", "Phase 65 D-14 page"]
tech-stack:
  added: []
  patterns: ["figures taken with step_count.py / footprint.py --rev at both commits (D-13)"]
key-files:
  created: []
  modified:
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-COUNTS.md
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REPRO.md
key-decisions:
  - "Finalize extraction judged alone at c7d92c9: PASS (steps 92 -> 83, bytes 136114 -> 129451)"
  - "Owner: \"Fix all six (Recommended)\" — X1-X6 fixed in 63-10, none pinned"
requirements-completed: [FINX-05, XVAR-02]
metrics:
  duration: "~45 min"
  completed: 2026-11-15
---

# Phase 63 Plan 09: Extraction figures and the owner's fix/pin decision Summary

The Finalize extraction passes on its own at `c7d92c9`. Steps the model runs on the Finalize path went from 92 to 83 and bytes loaded from 136,114 to 129,451, with all five Finalize situations, the baseline records and the archived replay matching 2.14.1. The owner chose to fix all six reproduced cross-call places.

## Figures (taken in this plan, `--rev` at both commits)

| | 2.14.1 `dd8e4ab` | extraction-only `c7d92c9` |
|--|--|--|
| steps, Finalize path (rule v1) | 92 | 83 |
| steps, 90-finalize.md alone | 68 | 59 |
| bytes, Finalize path | 136114 | 129451 |
| bytes, plain review / deep review | 192057 / 268997 | 192057 / 268997 |

The six files that ordinary reviews also load are byte-identical to `dd8e4ab` at `c7d92c9`. What went away: 4 Bash blocks, 2 Write-tool writes, 3 copied paths and the `GATEFILE` printed name.

Same-behaviour results:
- `compare --commit c7d92c9`: exit 0, "finalize outcome fields match (5 situations, 7 walks)".
- `verify`: "finalize baseline matches (5 situations)".
- `baseline_records.py verify`: "baseline holds", both with and without `--scripts-dir plugins/vibe-check/scripts`.
- `score.py` and `replay.py` are byte-identical to `dd8e4ab`.
- Fingerprints: 10 of 10 match MANIFEST.json.

Maintenance added: helper 391 lines, its tests 1841 lines, `finalize_capture.py` +635/−12. 24 extraction commits are listed for a revert; none is mixed.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Figures and verdict at the extraction-only commit | `6698d30` |
| 2a | "What each fix would add" (before the pause) | `974137a` |
| 2b | Owner decision recorded | `2ffefef` |

## Verification (run, observed)

- Task 1: the plan's verify logic, run as a Python script because the harness refuses the multi-git `bash -c` one-liner, printed `OK`. It recomputes the step figure from the recorded commit, checks the six files, the section headings, the fingerprint line, and that every extraction commit's short sha is listed.
- Task 2: the plan's Python check (every `EXCEPTIONS` id has a fix/pin row under `## Owner decision`) printed `OK`. `git diff --quiet c7d92c9 HEAD -- plugins/ docs/` exited 0, so no product file changed in this plan.

## Deviations from Plan

**1. [Rule 3 - Blocking] Task 1 verify run as a Python port**
- **Issue:** the worktree harness refuses `bash -c` commands that combine several git calls.
- **Fix:** the same checks ran as a Python script with structured `subprocess` arguments, and it printed OK.
- **Cost if wrong:** low. The checks are one-for-one, and the step figure is recomputed from the commit.

**2. [Orchestrator instruction] Full suite not re-run at c7d92c9**
- **Issue:** the plan asks for the full-suite line at X. The orchestrator assigned that run to itself.
- **What was done:** 63-COUNTS.md records the orchestrator's main-checkout result (6478 passed, 0 failed) and notes that it used a wider command. It also records the last same-command run from 63-07 (4498 passed, 5 known worktree-only failures) against `## Before` (4329 passed).
- **Cost if wrong:** a regression introduced only by the 63-08 tool commits would not show in the same-command line. The tools folder itself passed in 63-08 (355 passed).

**3. Owner decision arrived relayed**
- **What happened:** the decision was relayed by the phase coordinator with the owner's exact words, "Fix all six (Recommended)". The plan says an agent message is not the decision on its own, so 63-REPRO.md records where the answer came from: the owner's answer to the coordinator's question, quoted.
- **Cost if wrong:** if the relay misquoted the owner, 63-10 would fix X4-X6, which the owner might have pinned. The owner can check the quote on the D-14 page.

## Open item for 63-10 (not a decided fix)

`phases/shared/90-finalize.md` reads `"$STATE_FILE"` in its own Bash blocks (the Finalize-inputs call, `batch_card.py rows`, `record-decisions`, the state archive). The variable is set in `phases/review/05-state.md`. The cross-call check is same-file only, so this cross-file read was never flagged or reproduced. 63-10 should look at whether it behaves correctly when blocks run as separate calls. The X3 fix (printing `STATE_FILE=`) would give those blocks a value to substitute. Nothing is decided here.

## Known Stubs

None.

## Self-Check: PASSED

- 63-COUNTS.md, 63-REPRO.md and this SUMMARY exist.
- Commits 6698d30, 974137a and 2ffefef are in `git log`.
