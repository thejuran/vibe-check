---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
plan: 01
subsystem: release-gate
tags: [wr-02, reproduction, fresh-shell, state-key, gsd-route]
requires: []
provides:
  - "65-REPRO-WR02.md: WR-02 walked on the candidate and on 2.14.1, Verdict QUALIFYING (wrong close), Owner go GRANTED"
affects:
  - "65-03 (conditional WR-02 fix) now runs: Owner go: GRANTED (owner, 2026-11-16)"
  - "Backlog 999.38 wording (WR-02 is a regression from 2.14.1)"
tech-stack:
  added: []
  patterns: ["fresh-shell walk with classify() against a one-shell control (test_cross_call_vars helpers)"]
key-files:
  created:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-REPRO-WR02.md
  modified: []
decisions:
  - "WR-02 is QUALIFYING (wrong close, with data loss alongside): with an empty phase id, phase B's Finalize returns write-review-md on phase A's saved progress"
  - "WR-02 is a regression from 2.14.1 under the fresh-shell standard: 2.14.1 prints no path and its close-out stops (no prior review passes)"
  - "Owner granted the one D-08 fix round (go (Recommended), 2026-11-16); 65-03 runs and the candidate is rebuilt after it"
metrics:
  duration: "~40 min (including the owner pause)"
  completed: 2026-11-16
  tasks: 2
  files: 1
---

# Phase 65 Plan 01: WR-02 reproduction and verdict Summary

WR-02 reproduces on the release candidate as a wrong close. If the GSD state-key fence in `05-state.md` runs without the phase name, it prints `STATE_FILE=.turingmind/state/format-53/.json` for every phase. Phase B's Finalize then returns `write-review-md` from phase A's decided findings. 2.14.1 under the same standard fails closed. The owner granted the one D-08 fix round.

## What was done

- **Branch:** the orchestrator had already created `feat/v2.15-phase-65`. Checked that it is the current branch and contains a6d29d2 and `main`.
- **Walk A (mechanism):** ran the GSD fence verbatim under `env -i` with no `PHASE_ID`.
  - Candidate: exit 0, prints `LEGACY_STATE_FILE=.turingmind/state/.json` and `STATE_FILE=.turingmind/state/format-53/.json`.
  - v2.14.1: exit 0, prints nothing.
- **Walk B (two-phase chain):** temp repo with `01-a` and `02-b`. Phase A's state is `phase45-loop-state.json` with its decisions recorded through `carry_state.record_decisions`.
  - Candidate, all of A's findings decided: phase B's Finalize-inputs returns `write`/`write-review-md` with counts 0/0/0, built from A's state.
  - Candidate, one of A's findings decided: B gets `finalize-card` showing A's medium finding.
  - Candidate, both variants: B's printed path is A's file, so any write by B overwrites A's state. `classify` gives `wrong-file`. The control (phase names filled in) returns `stop-no-state` for B.
  - v2.14.1: `[ -f "$STATE_FILE" ]` comes back absent and the gate returns "no prior review passes". The counts fence exits 1 with the uncertain sentence. No wrong close.
- **Verdict:** `Verdict: QUALIFYING — wrong close — owner D-08 go required`. The record includes the 2.14.1 comparison, the carry-entry form, `**Reopens if:**` and `**Backlog:** 999.38`.
- **Owner ruling:** the main session asked the owner directly with AskUserQuestion. The owner chose "go (Recommended)". The coordinator recorded `Owner go: GRANTED (owner, 2026-11-16)` and committed it as f3f8a6b. This executor did not write or edit that line.

## Verification (observed)

- Task 1's automated check printed `OK`: on the branch, contains `main`, all five sections present, no changes under `plugins/`, `README.md`, `docs/` or `.github`.
- Task 2's automated check, re-run after f3f8a6b, printed `OK`: one `Verdict:` line, one `Owner go: GRANTED (owner, 2026-11-16)` line, the file is tracked, and the last commit ends with the Co-Authored-By line.
- `git status --porcelain -- plugins README.md docs .github` is empty.

## Follow-up the owner should know about

**Backlog 999.38 is wrong about WR-02.** ROADMAP.md says of the 999.38 items: "None is a regression from 2.14.1." Under the fresh-shell standard WR-02 is a regression. 2.14.1 printed no `STATE_FILE=` literal, so an empty id made close-out stop. The candidate's printed literal, added by the Phase 63 cross-call fixes, turns the empty id into a shared file and a wrong close. That line needs correcting. This plan does not touch ROADMAP.md (orchestrator instruction), so the correction belongs to 65-03 or the release-record plan.

## Deviations from Plan

- **[Rule 3 - Mechanics] The branch step was already done.** The orchestrator had created and switched to the branch, so I only checked it. The plan's assertion that `main` is checked out before branching no longer applied. **Cost if wrong:** none; the ancestry check passed.
- **[Mechanics] Two commits for the record instead of one.** Task 1 committed the walks (6340672) and Task 2 committed the verdict (a641778), following the one-commit-per-task protocol. The plan named only the Task 2 subject `docs(65): WR-02 reproduction and verdict`, which is used. **Cost if wrong:** cosmetic only.
- **[Mechanics] The owner ruling was recorded by the coordinator, not by a continuation executor.** Commit f3f8a6b carries the line and the selection "go (Recommended)". **Cost if wrong:** if the ruling were not the owner's own, 65-03 would open the fix round without authority. The coordinator states it came from AskUserQuestion in the main session.

## Assumption Drift (advisory)

- **Found during:** Task 1, 2.14.1 walk. **Planned:** backlog 999.38 (and the plan's own framing) treated WR-02 as not a regression from 2.14.1. **Actual:** it is a regression under the fresh-shell standard. **Why:** 2.14.1's GSD fence printed nothing and its later fences read an empty shell variable, so it fails closed. **Cost if wrong:** the release notes or backlog would understate a 2.15 regression.
- **Found during:** Task 1, realism. A live model following `00-scope.md:125` normally fills in the phase id, so the walk is the worst case. The D-02 smoke does not run the GSD route. This is recorded in the Realism caveat section.

## Known Stubs

None.

## Commits

- 6340672 docs(65): WR-02 reproduction walks on candidate and 2.14.1
- a641778 docs(65): WR-02 reproduction and verdict
- f3f8a6b docs(65): owner ruling on WR-02 fix round (coordinator)

## Self-Check: PASSED

- FOUND: 65-REPRO-WR02.md (tracked)
- FOUND: 6340672, a641778, f3f8a6b in `git log`
- Scratch script `wr02_repro.py` sha256 78e0d2fd…1732, in the session scratchpad, not in the repo
