---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 13
subsystem: phase-ledger
tags: [gap-closure, ledger, repro-record, traceability, CR-01, WR-02]
gap_closure: true
requires: [60-10, 60-11, 60-12]
provides: [REPRO_60 at fourteen rows (HEAD-SHA-INJECTION, STALE-GATEFILE-RERUN), _suite_defines over four test modules, 60-REPRO.md second-round section V13-V14 + reverse run at f2b58d1 + suite at close, residuals R14 closed + R18-R21, REQUIREMENTS/ROADMAP second-round notes]
affects: [Phase 60 re-verification (EVID-03, FINL-02)]
tech-stack:
  added: []
  patterns: [in-suite repro record locked by fixture resolution, reverse run in a detached worktree at the pre-round base]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
decisions:
  - "EVID-03 checkbox un-ticked in REQUIREMENTS.md (60-11's mark-complete had ticked it); re-verification, not an executor, decides completion"
  - "The pre-round base for the reverse run is f2b58d1 (per plan); 65bb39d is the same production tree (git diff --stat f2b58d1 65bb39d -- plugins/ is empty)"
  - "carry_state.py's one additive read-only subcommand (last-head-sha) is recorded beside the empty replay diff-stat, not hidden"
requirements: [EVID-03, FINL-02]
metrics:
  duration: ~25min
  completed: 2026-10-30
  tasks: 3
  files: 4
---

# Phase 60 Plan 13: Second gap round close-out Summary

The second gap round now has the same evidence as the first. REPRO_60 holds fourteen rows: HEAD-SHA-INJECTION (EVID-03, fixed by 60-10 + 60-11) and STALE-GATEFILE-RERUN (FINL-02, fixed by 60-12) were added. Every named fixture resolves across four test modules. 60-REPRO.md gained V13/V14, a red/green table, a reverse run at `f2b58d1` and the suite at close. R14 is marked closed and R18-R21 are carried. REQUIREMENTS and ROADMAP say the round landed and that EVID-03/FINL-02 await re-verification. The plan claims no completion.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Register the two second-round reproductions in REPRO_60; `_suite_defines` covers test_carry_state.py; lock fourteen rows | 84b5e27 | test_decision_continuity.py |
| 2 | Full suite, replay check, reverse run at f2b58d1, 60-REPRO.md second-round section and residuals | c9fbb8e | 60-REPRO.md |
| 3 | REQUIREMENTS traceability + ROADMAP plan list and 999.24/999.25 notes | 84cd096 | REQUIREMENTS.md, ROADMAP.md |

## Evidence (observed)

- Task 1: `pytest -q -p no:cacheprovider test_decision_continuity.py -k TestRepro60Record` gave `3 passed, 155 deselected, 54 subtests passed`. The acceptance one-liner printed `14 True True`. `grep -c "self.assertEqual(len(REPRO_60), 14)"` returned 1, and `grep -c '"test_carry_state.py"'` returned 1. `TestLastHeadSha` is defined only in test_carry_state.py, so the widened module tuple is what lets that row resolve.
- Full suite at HEAD 84b5e27, run from plugins/vibe-check/scripts: `3813 passed, 5014 subtests passed in 180.43s (0:03:00)`, 0 failed.
- `pytest -q -p no:cacheprovider test_replay.py`: `64 passed, 10 subtests passed in 10.38s`.
- `git diff --stat f2b58d1 HEAD -- replay.py test_replay.py score.py finalize_gate.py`: empty. `carry_state.py` diff-stat: `1 file changed, 42 insertions(+), 2 deletions(-)` (the 60-10 subcommand), recorded in the ledger.
- Reverse run in the worktree at f2b58d1 with the current four test files: `48 failed, 9 passed, 413 deselected, 3 subtests passed`. There are failures from test_carry_state.py (60-10), test_diff_ranges.py (60-11) and test_finalize_card.py (60-12). Of the 9 passed, 4 are parent entries of subtest tables whose subtests failed, 1 is `test_sixty_four_hex_is_accepted` (the old prose had no check to refuse it) and 4 are controls. All five named controls, run by name, gave `5 passed, 437 deselected`. The worktree was removed and pruned, and `git worktree list | grep -c pre60round2` returned 0. It was made twice, the second time only to list the passed tests with `-rA`, and the count was 0 after each.
- Task 2 acceptance:
  - the section grep returned 5;
  - `CLOSED at` occurs 1 time;
  - `Complete` occurs 1 time, the same as at f2b58d1;
  - every 7-hex token in the new section passes `git cat-file -e <sha>^{commit}`: 2648f2d, 43ae166, 558bde3, 5d81170, 65bb39d, 84b5e27, ae560fe, c0ece7e, c112ca6, cfa473a, dfca59c, f2b58d1.
- Task 3 acceptance:
  - `awaiting re-verification` occurs 2 times;
  - the unchecked EVID-03/FINL-02 grep returned 2;
  - `60-1[0-3]-PLAN.md` occurs 4 times, and 0 of those entries are unchecked;
  - the Plans line reads `13/13`;
  - the 999.24 paragraph contains V13 and the 999.25 paragraph contains V14;
  - the Task 3 commit touches only REQUIREMENTS.md and ROADMAP.md.

## Deviations from Plan

**1. [Rule 1 - Traceability reconcile] Un-ticked the EVID-03 checkbox.**
- **Found during:** Task 3
- **Issue:** 60-11 ran `requirements.mark-complete EVID-03`, which ticked `[x] **EVID-03**`. The plan requires it to stay unchecked until re-verification.
- **Fix:** Set it back to `[ ]`. The acceptance grep now returns 2.
- **Cost if wrong:** Low. The re-verification ticks it if it passes.
- **Files modified:** .planning/REQUIREMENTS.md
- **Commit:** 84cd096

**2. [Minor] The ROADMAP Plans line already read `12/13 plans executed`, not the plan's quoted `9/13 ... planned` text.** The prior executors had already advanced it. It is set to `13/13 plans executed` as the plan intends.

**3. [Minor] 60-REPRO.md residual intro sentences were adjusted.** The Residuals header said "None of these is fixed in Phase 60", and the R12-R17 lead-in said none was in a qualifying class. Both now note that R14 was reproduced as CR-01 and closed in the second round, so the file does not contradict itself.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** the orchestrator named `65bb39d` as the pre-round base, while the plan names `f2b58d1`. **Actual:** the reverse run used `f2b58d1`, per the plan. `git diff --stat f2b58d1 65bb39d -- plugins/` is empty, because the two commits between them are planning-only, so the production tree is identical. **Why:** both refer to the same code. **Cost if wrong:** none for the verdicts.

## Known Stubs

None.

## Threat Flags

None. This plan changed only test-record data and planning documents. T-60-41 to T-60-44 are mitigated as listed above (SHAs checked, fixtures resolved, carry_state diff recorded, worktree pruned).

## Self-Check: PASSED

- FOUND: test_decision_continuity.py (STALE-GATEFILE-RERUN), 60-REPRO.md (## V13, ## V14, R18-R21), REQUIREMENTS.md (60-10), ROADMAP.md (60-13-PLAN.md)
- FOUND commits: 84b5e27, c9fbb8e, 84cd096
