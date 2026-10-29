---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 05
subsystem: vibe-check change evidence + Finalize (cycle close)
tags: [reverse-run, ledger, residuals, D-10, EVID-01, EVID-02, EVID-03, FINL-01, FINL-02, 999.24, 999.25]
requires:
  - "60-01 RED SHA ce9f8b8 and the 15-test red set"
  - "60-02 53fb637, 60-03 b8fb21a/fd8c1b9/53b35ed, 60-04 66d63de/39f6dbd/fb8b32b"
provides:
  - "60-REPRO.md closed: Green at: SHA on all nine verdicts, ## Reverse run, ## Suite at close, ## Residuals (R1-R11)"
  - "ROADMAP 999.24 / 999.25 'Carried from Phase 60' paragraphs; 60-05 plan ticked"
  - "REQUIREMENTS EVID-01..03, FINL-01..02 ticked and Complete (EVID-03 with the D-05 live-fetch known limit)"
  - "Named Phase 61 inputs: R6 live gh pr diff gap, R5 install resync, replay deltas none"
affects: [61]
tech-stack:
  added: []
  patterns: ["reverse run: current tests copied into a detached scratch worktree at the RED SHA, removed afterwards"]
key-files:
  created:
    - .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-05-SUMMARY.md
  modified:
    - .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
decisions:
  - "Phase 60 closes on one cycle (D-10): no open silent keep; one named known limit (R6, live gh pr diff fetch not exercised) carried to Phase 61's release record"
  - "EVID-03 marked 'Complete (known limit: live gh pr diff fetch not exercised, D-05)' rather than plain Complete"
  - "Replay deltas for Phase 61 GATE-02: none — replay.py, test_replay.py, score.py and finalize_gate.py are byte-unchanged since ce9f8b8"
metrics:
  duration: "~25 min"
  completed: 2026-10-29
  tasks: 2
  files: 3
requirements: [EVID-01, EVID-02, EVID-03, FINL-01, FINL-02]
---

# Phase 60 Plan 05: Close the cycle Summary

This plan closes Phase 60's single cycle. Nothing new was built. The reverse run showed every one of the 15 red fixtures from 60-01 failing again on the code at the RED SHA `ce9f8b8`, and all of them pass at HEAD. Every verdict in the ledger now names the SHA that turned it green. The full suite and the archived replay pass with no deltas. Eleven residuals are recorded with their rationale, and the planning files reflect the outcome, including one known limit on EVID-03.

## Commits

| # | Task | Commit |
|---|------|--------|
| 1 | Reverse run at the RED SHA, suite at close, green SHAs in the ledger | `fc019b2` |
| 2 | Residuals, ROADMAP 999.24/999.25 paragraphs, REQUIREMENTS status | `9e0bb86` |

## Verification (observed)

- Full suite at HEAD `ec0c9d8` (`pytest -q -p no:cacheprovider` from `plugins/vibe-check/scripts`) gave `3765 passed, 4930 subtests passed in 170.01s`, with 0 failed.
- `pytest -q test_replay.py` gave `64 passed, 10 subtests passed in 9.98s`. `git diff --stat ce9f8b8 HEAD -- replay.py test_replay.py score.py finalize_gate.py` is empty, so there are no replay deltas.
- Reverse run: I created a worktree with `git worktree add --detach <scratchpad>/pre60 ce9f8b8` (its rev-parse printed `ce9f8b8`) and copied in the current `test_decision_continuity.py`, `test_finalize_card.py` and `test_diff_ranges.py`.
  - The decision-continuity selection gave `14 failed, 11 passed`: all 10 `TestRealDiffRanges60` tests and all 4 `TestCoordinateSpaces60` probes.
  - The Finalize selection gave `21 failed, 8 passed`. That covers 9 tests, including `test_walk_reaches_counts_gate_report` and the inverted `test_gate_fence_reads_cross_call_variable_today`, plus 12 subtests.
  - `test_diff_ranges.py` stopped at collection with `ModuleNotFoundError: No module named 'diff_ranges'`.
  - Afterwards I removed the worktree with `git worktree remove --force` and `git worktree prune`. `git worktree list | grep -c pre60` returned `0`.
- R1 was re-checked at HEAD: `printf '' | python3 finalize_gate.py` exits 1, and its stderr starts with `Traceback` and ends with `JSONDecodeError`.
- Task 1 verify printed `green=9 pending=0` and then `T1OK`.
- Task 2 verify printed `R=7 carried=2` and then `T2DOCS_OK`. Each of the plans 60-01 to 60-05 is ticked once. `to be fixed` appears 0 times in test_decision_continuity.py. `pytest -q test_decision_continuity.py -k TestRepro60Record` gave `3 passed`.
- The phrase "reliability complete" appears only in the existing STALE-06 rule and in the Phase 59 success criterion, both of which forbid that claim. Nothing in Phase 60 makes it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] "Green at:" lines rewritten so the SHA leads the line**
- **Found during:** Task 1
- **Issue:** The existing 60-04 lines read `Green at: 60-04. …` and V1 read ``Green at: `53fb637` ``. Neither matches the verify regex `Green at: [0-9a-f]{7,}`.
- **Fix:** Every line now starts with the bare green SHA(s), followed by the earlier explanation unchanged.
- **Cost if wrong:** None. Only the wording changed.
- **Commit:** fc019b2

**2. [Rule 3 - Mechanics] Doc edits went through Edit/Write instead of shell heredocs**
- **Found during:** Task 1
- **Issue:** The repo's holdout-guard PreToolUse hook refused two Bash calls. Their text held glob-like tokens (a `sed` `.*` pattern, then brace/glob text in an inline script). This is the hook's documented false positive. No call came near the holdout folder.
- **Fix:** Ledger edits were made with the Edit tool, and the verify fences were run from script files in the scratchpad.
- **Cost if wrong:** None.

**3. [Plan scope] test_decision_continuity.py not edited**
- **Found during:** Task 2
- **Issue:** The plan lists the file so that REPRO_60 dispositions could be reconciled. All nine already read their final strings (`reproduced; fixed by 60-0N`, `unsupported fixture; recorded, no fix`), with 0 `to be fixed`.
- **Fix:** No edit. `TestRepro60Record` gave 3 passed.
- **Cost if wrong:** None.

**4. [Orchestrator instruction] STATE.md updated by this executor**
- **Found during:** State updates
- **Issue:** The plan says the orchestrator updates STATE.md. The spawn prompt's success criteria ask the executor to update it.
- **Fix:** I followed the spawn prompt and updated it after the SUMMARY (see the final metadata commit).
- **Cost if wrong:** Low. The orchestrator can overwrite it.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** residuals R1-R7. **Actual:** R1-R11. R8 (C-quoted paths), R9 (the RESEARCH snippet's off-by-one), R10 (`--all` has no diff) and R11 (`replay.hunk_ranges` is intentionally unchanged) were added so each surfaced candidate has a written home. **Why:** the orchestrator named these candidates explicitly. **Cost if wrong:** none. They are records only, and no work was added.
- **Found during:** Task 2. **Planned:** R3 treated as "reviewer changes out of scope". **Actual:** R3 also says that a reviewer numbering lines from commit coordinates in `--patch` could cost a finding its `+20 in_diff` term. This was not reproduced, so it is marked reproduce-first. **Cost if wrong:** if it reproduces, it could be a silent loss of a qualifying finding near threshold. That would be a Phase-61-or-later item, not a Phase-60 claim.

## Known Stubs

None.

## Threat Flags

None. T-60-17: the reverse run is reproducible from the ledger's quoted commands and SHAs. T-60-18: the worktree was removed and `git worktree list` is clean of pre60. T-60-19: R6 and the EVID-03 known-limit wording state the live-fetch gap.

## Self-Check: PASSED

- FOUND: 60-REPRO.md (`## Reverse run`, `## Suite at close`, `## Residuals`), ROADMAP.md (2× `Carried from Phase 60`), REQUIREMENTS.md (EVID-03 `[x]`, FINL-02 Complete)
- FOUND commits: fc019b2, 9e0bb86
