---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
plan: 05
subsystem: release-gate
tags: [release-gate, equivalence, replay, recount, fingerprints]
requires:
  - "65-04: release candidate C = b073e31 recorded in 65-CANDIDATE.md"
  - "65-03: WR-02 fix b281042 and its named growth rows"
provides:
  - "65-RELEASE-RECORD.md: G1-G11 PASS on C with raw output; G12 PENDING (runbook step 4)"
  - "Direct recount at dd8e4ab and C with D-09 reconciliation, Unitemised growth: 0"
affects:
  - "65-06 (paid live smoke) may run: its precondition (record with G1-G11 PASS) is met"
  - "65-07 / close runbook: G12 CI check on the PR head"
tech-stack:
  added: []
  patterns: ["candidate preamble asserts tree == C outside .planning, not HEAD == C"]
key-files:
  created:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-RELEASE-RECORD.md
  modified: []
decisions:
  - "G1-G11 PASS on candidate b073e31; no fix round needed after WR-02"
  - "Review-path growth on C is +0.54% to +0.89% bytes and +2 steps per path, fully itemised (Phase 63 D-09 rows + 65-03 +495 bytes)"
metrics:
  duration: "~55 min"
  completed: 2026-11-16
  tasks: 3
  files: 1
---

# Phase 65 Plan 05: Release gates G1–G11 on C Summary

All eleven free gates pass on candidate C (`b073e31`). The suite has 0 failed, 0 errors and 0 skipped in both forms. The archived replay shows no scoring differences from 2.14.1. All five Close-out situations match 2.14.1 except for the intended command lists. The direct recount confirms Close out shrank (136,114 → 131,381 bytes, 92 → 85 steps), and every byte and step of review-path growth traces to a named item. G12, CI on the PR head, stays PENDING until close.

## Results (all run in the main checkout on a tree equal to C outside `.planning`)

| Gate | Result |
|------|--------|
| G1a scripts-folder suite | `4126 passed … in 246.50s`, junit skipped 0; equals the README count |
| G1b repo-root suite | `4599 passed … in 451.99s`, junit skipped 0 |
| G2 Mac-only 7 by id | `7 passed`, no skips |
| G3 route selector | `898 passed`, 0 failed |
| G4a replay diff vs v2.14.1 | 170 compared, 0 differing, 0 unallowed |
| G4b guardrail | kept 25/26, `REGRESSED 0`, AMENDED 1 (standing 008) |
| G4c census | transcripts 12, scoreable 66 |
| G4d / G5a | `baseline holds`; `finalize baseline matches (5 situations)` |
| G5b situations on C | `finalize outcome fields match (5 situations, 7 walks)`, 0 `differs` lines |
| G6 recount | Finalize −4,733 bytes / −7 steps; review paths +1,705 to +1,966 bytes, +2 steps; Unitemised growth 0 |
| G7 | 10 of 10 fingerprints; baseline folder unchanged since d0adb5b; GOLDEN_DIGEST equal |
| G8 / G9 | stdlib-only (34 files); left-out list = five; `✔ Validation passed`, version 2.15.0 |
| G10 / G11 | scorer/replay identical to v2.14.1; exactly the 9 D-09 instruction files |
| Fix verification | `test_verified_fixes`/`test_confirmed_fix`/`test_fixcheck`: 248 passed |

## Task commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1–3 | Suite gates, equivalence/safeguard gates, recount + record (single record committed in Task 3 as the plan specifies) | `511a351` | 65-RELEASE-RECORD.md |

## Deviations from Plan

None. The plan was executed as written. Environment notes, also recorded in the release record:
- G11's file list was sorted with `LC_ALL=C sort`, the known Mac locale quirk.
- One G6 attempt was refused by the preamble with `DIRTY TREE — STOPPING`. It had been started while G1a was running, and a test briefly placed a temporary file under the shipped tree. G6 was re-run after G1a finished and passed the full preamble. Every later gate ran on its own.
- **Cost if wrong:** none. The refusal shows the guard working, and every recorded result comes from a clean-preamble run.

## Known Stubs

None.

## Next

65-06 (owner-approved paid live smoke) can run now that the record shows G1–G11 PASS. G12 is checked at close (runbook step 4) once the branch is pushed.

## Self-Check: PASSED

- FOUND: .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-RELEASE-RECORD.md (tracked)
- FOUND: commit 511a351
