---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 06
subsystem: phase-gate / reproduction record
tags: [phase-gate, repro, bug-C, replay, mutants, ANSR-01, ANSR-02, ANSR-03, RECV-01, RECV-02]
requires:
  - "58-01..58-05, 58-07..58-09 SUMMARYs (RED outputs, mutant tables, 58-08 round-trip, 58-09 static trace)"
provides:
  - "58-REPRO.md: verdicts V1-V5, bug-C verdict with evidence, inventory I-1..I-15, Gate section"
affects: [phase 58 code review and verification]
tech-stack:
  added: []
  patterns: ["live re-run of reproduction CLI commands for the verdict record"]
key-files:
  created:
    - .planning/phases/58-clear-actions-recovery-and-answers-acted-on/58-REPRO.md
  modified: []
decisions:
  - "Bug C (ANSR-03): does not reproduce on current code — fixed by 46d78e3 (v2.12); filed nothing"
  - "Replay gate run as both test_replay.py and the replay.py candidate/diff pair, matching the 57-23 gate shape"
metrics:
  duration: ~20 min
  completed: 2026-10-27
  tasks: 2
  files: 1
requirements: [ANSR-03, ANSR-01, ANSR-02, RECV-01, RECV-02]
---

# Phase 58 Plan 06: Reproduction verdicts and phase gate Summary

`58-REPRO.md` records every verdict for the phase. V1 (repeated card), V2 (Fix all label) and V3 (recovery tail) each reproduced before the phase, and the doc maps each to the plans that fixed it. Bug C does not reproduce on current code: commit 46d78e3 fixed it and shipped in v2.12. The doc gives the evidence (static trace, git history, A/B/C mutant table) and files nothing. Inventory items I-1 to I-13 are fixed, and I-14 and I-15 were checked and are consistent with the code. The phase gate is green: 3465 passed / 0 failed, replay REGRESSED 0, golden ok, and score.py / batch_parse.py are unchanged.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 41a381f | docs(58-06): record reproduction verdicts; bug C does not reproduce (46d78e3, v2.12) |
| 2 | 7709bfd | docs(58-06): phase 58 gate — suite, replay, golden, mutants |

## Live re-runs for the verdict record (Task 1, at 13492b7)

- `batch_card.py parse` on the eight-row iPlayarr rows doc:
  - The plain-English answer exits 2 with `refused: answer does not match the grammar`.
  - `fix 5; dismiss 1,2,3,4,6,7,8 -- …` exits 0 with fix_targets 1, 7 decisions, and the full echo.
  - The same answer without a reason exits 2 with `refused: dismiss/defer needs a reason`.
- `batch_card.py resolve` on the refs for that answer exits 0 with `ok: true` and grammar `fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: "dismiss the 7 fixed rows")`.
- `git log -S'ask NO AskUserQuestion'` returns `46d78e3`, and `git tag --contains 46d78e3` returns `v2.12`.
- `pytest scripts/test_fix_loop_card.py -k subset -v` gives 7 passed (bug-C mutants A, B and C all trip).

## Gate numbers (verbatim, Task 2)

- Full suite (`pytest -q`): `3465 passed, 4608 subtests passed in 162.51s`, 0 failed. That is the 3311 baseline plus 154 new tests.
- `pytest -q scripts/test_replay.py`: `64 passed, 10 subtests passed`.
- Replay candidate:
  - `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`, `kept 25 / protected 26`, `REGRESSED 0`.
  - The one AMENDED run is the pre-existing triggarr-secret-in-logs/run-2.
  - The scorer sha256 `3504d2da…22fb` is identical to the 57-23 gate.
- Replay diff vs rev:24c0c00: 170 runs compared, 0 differing, 0 unallowed.
- Golden: `pytest -q scripts/test_score.py -k golden` gave `9 passed, 491 deselected`, and the digest check printed `golden ok`. Both ImportSet selections gave `3 passed`.
- `git diff --stat 24dccdc..HEAD -- scripts/score.py scripts/batch_parse.py` is empty.
- Mutant inventory:

  | Test file | Count | Pytest result |
  |---|---|---|
  | test_card_scope.py | 4 `subTest("mutant` | 4 passed |
  | test_answer_resolve.py | 5 `subTest("mutant` | 5 passed |
  | test_recovery_pairs.py | 5 TestLockTrips methods | 5 passed |
  | test_fix_loop_card.py | 28 `def test_mutant_` (up from 8) | 47 passed for `-k "mutant or Trips"` |
  | test_finalize_card.py | 9 `def test_mutant_` (up from 0), carrying 20 mutant subtests | 9 passed |
  | test_scope_args.py | 4 `test_m4_`..`test_m7_` | 4 passed |

- CarrierRoundTrip: 3 passed. Each test loops over /bin/bash and /bin/zsh.
- Plugin-file count `24dccdc..HEAD` was 32 before and after this plan, so no plugin file changed.

## Deviations from Plan

**1. [Rule 1 - Inventory grep shape] test_recovery_pairs.py has no `subTest("mutant`**
- **Found during:** Task 2
- **Issue:** The plan's grep `subTest("mutant` returns 0 for test_recovery_pairs.py. 58-02 wrote its mutants as five `TestLockTrips` test methods, not as subtests.
- **Fix:** I recorded both numbers (grep 0, plus 5 TestLockTrips methods that pass) instead of claiming the grep met ≥ 5.
- **Cost if wrong:** low. The mutants exist, and 58-02 also applied them to the real files.

**2. [Rule 1 - Inventory count] test_finalize_card.py gained 9 `def test_mutant_` methods, not ≥ 12**
- **Found during:** Task 2
- **Issue:** 58-05 and 58-09 put their mutants into 9 methods with 20 mutant subtests. Counted as methods, the total is 9.
- **Fix:** Recorded faithfully: 9 methods, 20 subtests. Both plans also have their real-file mutant tables, 12 for 58-05 (M1-M12) and 6 for 58-09 (M1-M6).
- **Cost if wrong:** low. Every lock in the file has at least one tripping mutant.

**3. [Rule 2 - Evidence] Replay candidate and diff run in addition to test_replay.py**
- **Found during:** Task 2
- **Issue:** The plan's replay command (`pytest -q scripts/test_replay.py`) does not print a REGRESSED / UNEVALUABLE / AMENDED ledger.
- **Fix:** I ran `replay.py candidate` and `replay.py diff` the same way the 57-23 gate did. These are local only and use archived envelopes.
- **Cost if wrong:** none.

**4. [Wording] "live run" phrase**
- The acceptance grep looks for "live run", so the closing line reads "No live run and no paid run was performed (D-15)".

## Known Stubs

None.

## Threat Flags

None. T-58-21: the doc includes the live CLI output, the git history and the before/after mutant table. T-58-22: the score.py and batch_parse.py diff is empty, the golden check is green, and the replay diff shows 0 differences.

## Self-Check: PASSED

- FOUND: .planning/phases/58-clear-actions-recovery-and-answers-acted-on/58-REPRO.md
- FOUND commits: 41a381f, 7709bfd
- STATE.md, ROADMAP.md and HANDOFF.json were not touched by this plan
