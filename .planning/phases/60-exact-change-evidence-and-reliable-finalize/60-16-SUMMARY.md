---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 16
subsystem: reproduction-ledger / traceability
tags: [gap-closure, close-out, repro-ledger, reverse-run, FINL-02, EVID-03]
gap_closure: true
requires:
  - 60-14 (WR-01 step-3 BLOBFILE re-mint; RED 7796476, GREEN 9b3f055)
  - 60-15 (WR-02 head_sha bind fence finalize-skip; RED 3c7814e, GREEN 07bb448)
provides:
  - REPRO_60 at sixteen rows (STALE-BLOBFILE-RECOUNT, FINALIZE-HEAD-SHA-WEDGE) with a mutation-tested lock
  - 60-REPRO.md third gap round section (V15, V16, red/green table, reverse run at 2de0fc9, suite at close)
  - Residuals R22-R26
  - EVID-03 Complete per the 2026-10-30 re-verification; FINL-02 awaiting re-verification
affects: [Phase 60 re-verification, Phase 60 PR]
tech-stack:
  added: []
  patterns: [in-suite reproduction record resolved through _suite_defines, reverse run in a detached throwaway worktree]
key-files:
  created:
    - .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-16-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
decisions:
  - "60-15's write-side head_sha residual (45-persist.md writes head_sha with no format check) is carried as R26, not fixed (owner scope rule)"
  - "EVID-03 marked Complete citing 60-VERIFICATION.md truth 3 (2026-10-30); FINL-02 stays unchecked pending re-verification"
requirements: [FINL-02, EVID-03]
metrics:
  duration: ~25min
  completed: 2026-10-30
  tasks: 3
  files: 4
---

# Phase 60 Plan 16: Third gap round close-out (REPRO_60 at 16 rows, V15-V16, reverse run at 2de0fc9) Summary

This plan records the third gap round. The in-suite reproduction record now covers both third-round findings, the ledger has repro-then-green evidence with SHAs that resolve, the current tests fail against the pre-round prose at `2de0fc9` while the six controls pass there, and the full suite is clean at close. EVID-03 is marked Complete because the 2026-10-30 re-verification cleared it. FINL-02 is not claimed complete; it waits for re-verification.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Register STALE-BLOBFILE-RECOUNT and FINALIZE-HEAD-SHA-WEDGE in REPRO_60; lock sixteen rows | cef9a1e | test_decision_continuity.py |
| 2 | Full suite, replay, reverse run at 2de0fc9, 60-REPRO.md third-round section and R22-R26 | 0d06540 | 60-REPRO.md |
| 3 | REQUIREMENTS / ROADMAP: third round landed, EVID-03 Complete, FINL-02 awaiting re-verification | 48a95e0 | REQUIREMENTS.md, ROADMAP.md |

## Verification (observed)

**Task 1:**
- `pytest -q -p no:cacheprovider test_decision_continuity.py -k TestRepro60Record` printed `3 passed, 155 deselected, 67 subtests passed`.
- The python acceptance check printed `16 True True`. `grep -c "self.assertEqual(len(REPRO_60), 16)"` printed `1`.
- I mutation-tested the lock on a full scratch copy of the plugin, then deleted the copy:
  - Control: `3 passed`.
  - M1, FINALIZE-HEAD-SHA-WEDGE disposition changed to `recorded; no fix`: `1 failed`.
  - M2, a typo in a STALE-BLOBFILE-RECOUNT fixture name: `1 failed`.
  - M3, the STALE-BLOBFILE-RECOUNT row removed: `1 failed`.

**Task 2:** all runs below are at HEAD `cef9a1e` in the real checkout.
- Full suite, `pytest -q -p no:cacheprovider`: `3821 passed, 5039 subtests passed in 174.64s`, 0 failed.
- `test_replay.py`: `64 passed, 10 subtests passed`.
- The five-helper diff-stat against `2de0fc9` was empty, and so was the non-test `scripts/*.py` name list. The `plugins/` diff-stat lists exactly 05-state.md, 90-finalize.md, test_decision_continuity.py, test_diff_ranges.py and test_finalize_card.py. The planning commits `2de0fc9..712ba40` change nothing under `plugins/`.
- Reverse run at `2de0fc9` (worktree at `<scratchpad>/pre60round3`, with the three current test files copied in):
  - The `-k` run printed `27 failed, 10 passed, 194 deselected, 16 subtests passed`. Failures from both 60-14 (`test_finalize_card.py`) and 60-15 (`test_diff_ranges.py`) are present.
  - Of the 10 passed, 4 are subtest-table parents whose subtests failed, 2 are unchanged second-round locks, and 4 are controls.
  - All six named controls passed when run by name: `6 passed`.
  - The worktree was removed and pruned. `git worktree list | grep -c pre60round3` printed `0`.
- Acceptance greps: the section/V15/V16/R22/R25 grep printed `5`; `(R2[2-5])` printed `4`; `FINL-02 awaits re-verification` printed `1`.
- All ten cited SHAs passed `git cat-file -e`: 7796476, 9b3f055, 3c7814e, 07bb448, 2de0fc9, e90c6a7, 270f922, 712ba40, cef9a1e, c112ca6.

**Task 3:**
- `awaiting re-verification` in REQUIREMENTS.md: `1`.
- `[x] EVID-03`: `1`.
- `[ ] FINL-02`: `1`.
- `60-1[4-6]-PLAN.md` in ROADMAP.md: `3`.
- Unchecked 60-14..16 entries: `0`.
- Overview row `| 16/16`: `1`.
- `**Plans:** 16/16 plans executed` is on line 97.
- The Task 3 commit does not touch STATE.md.

## Deviations from Plan

**1. [Orchestrator instruction] Added R26 for the 60-15 write-side head_sha residual**
- **Found during:** Task 2
- **Issue:** The plan listed R22-R25 only. The orchestrator asked for 60-15's residual (45-persist.md writes `head_sha` with no format check) to be recorded as a carried residual and not fixed.
- **Fix:** Added it as R26 with its rationale and the condition that would reopen it. The `(R2[2-5])` count stays `4`, as the plan requires.
- **Cost if wrong:** One extra ledger line. Nothing in the product changes.
- **Commit:** 0d06540

**2. [Rule 1 - Accuracy] Attributed the stale fingerprint claim to c112ca6 only**
- **Found during:** Task 2
- **Issue:** My first draft said the claim came from the 60-08/60-12 line. `git log -S "the fingerprints have not changed"` shows that `c112ca6` (60-12) introduced it.
- **Fix:** The ledger now cites `c112ca6` and `git log -S` as the source.
- **Cost if wrong:** None. The ledger text is now backed by git.
- **Commit:** 0d06540

**3. [Rule 3 - Blocking] Mutation scratch copy needed the whole plugin tree**
- **Found during:** Task 1
- **Issue:** Copying only `scripts/` failed at collection, because the tests read `fixtures/future-schema.json`.
- **Fix:** Copied the whole `plugins/vibe-check` tree into the scratchpad and deleted it afterwards.
- **Cost if wrong:** None. The mutation check runs outside the repo.

The ROADMAP overview row read `15/16` (not `13/16`) when this plan started. It was set to `16/16`.

## Known Stubs

None.

## Residuals

All of these are recorded in 60-REPRO.md:
- R22 to R25: gap-round-2 IN-01, IN-02 and IN-03, plus SA-01, which needs an owner ruling.
- R26: 45-persist.md does not check the format of `head_sha` when it writes it.
- Neither third-round fix has been exercised in a live Claude Code `--finalize` session; R5 applies to any live check.

## Requirements

- EVID-03 is ticked Complete, citing 60-VERIFICATION.md truth 3 from 2026-10-30.
- FINL-02 is still unchecked. Its traceability row reads "Gap closure landed (... third round 60-14, 60-15: 9b3f055, 07bb448); awaiting re-verification".

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py, .planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md, .planning/REQUIREMENTS.md, .planning/ROADMAP.md
- FOUND commits: cef9a1e, 0d06540, 48a95e0
