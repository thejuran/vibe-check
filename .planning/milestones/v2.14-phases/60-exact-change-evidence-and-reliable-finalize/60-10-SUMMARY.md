---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 10
subsystem: carry-state-helper
tags: [gap-closure, security, command-injection, CR-01, tdd]
gap_closure: true
requires: []
provides: [carry_state.py last-head-sha subcommand, _commit_sha validator, last_head_sha(state), REASON_HEAD_SHA in sealed REASONS]
affects: [60-11 (binds $LAST_REVIEWED_SHA through a printed-literal fence), 60-13 (ledger RED/GREEN SHAs)]
tech-stack:
  added: []
  patterns: [helper decides / prose never compares, refusal prints nothing on stdout, mutation subtest via mock.patch.object]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_carry_state.py
decisions:
  - "last-head-sha accepts only a str of exactly 40 or 64 lowercase hex characters (the CR-01 regex written without re, since the import set is sealed); everything else is refused with REASON_HEAD_SHA, empty stdout, exit 2"
  - "last-head-sha prints a bare line (sha + newline), not JSON, so the 60-11 fence can print it after LAST_REVIEWED_SHA= without quotes"
requirements: [EVID-03]
metrics:
  duration: ~12min
  completed: 2026-10-30
  tasks: 2
  files: 2
---

# Phase 60 Plan 10: carry_state last-head-sha (CR-01 script half) Summary

`carry_state.py last-head-sha` is now the one checked source for the last-reviewed sha that the review text substitutes into `git diff` on pass 2 and later. It prints the last pass's `head_sha` as one bare line only when the value is exactly 40 or 64 lowercase hex characters. Anything else, including the exact CR-01 payload `$(touch "$T/pwned")HEAD`, is refused: a fixed one-line reason goes to stderr, nothing goes to stdout, and it exits 2. A mutation test shows the validator is what blocks the payload. This plan does not change the review text; 60-11 binds `$LAST_REVIEWED_SHA` through this subcommand.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED: TestLastHeadSha (accept/refuse table, empty stdout on refusal, mutation test, sealed-shape checks) | 558bde3 | test_carry_state.py |
| 2 | GREEN: `last-head-sha` subcommand, `_commit_sha`, `last_head_sha`, `REASON_HEAD_SHA` | ae560fe | carry_state.py |

**RED SHA:** 558bde3. **GREEN SHA:** ae560fe.

## Evidence (observed)

RED at 558bde3:
- `pytest -q -p no:cacheprovider test_carry_state.py -k TestLastHeadSha` gave `24 failed, 2 passed, 226 deselected`. All 8 tests are red. The 2 "passed" are the parent entries of the two subtest-table tests, and every subtest under them failed: pytest-subtests counts the parent separately.
- `pytest -q -p no:cacheprovider test_carry_state.py -k "not TestLastHeadSha"` gave `226 passed, 8 deselected, 300 subtests passed`.

GREEN at ae560fe:
- `pytest -q -p no:cacheprovider test_carry_state.py` gave `234 passed, 318 subtests passed`.
- `pytest -q -p no:cacheprovider test_finalize_card.py test_nv_render.py test_decision_continuity.py test_carry_writers.py` gave `300 passed, 752 subtests passed`.
- Full suite: `pytest -q -p no:cacheprovider` in `plugins/vibe-check/scripts` gave `3794 passed, 4983 subtests passed in 175.93s`, 0 failed. It ran on the GREEN working tree, which was identical to ae560fe.

Scratch-directory CLI check, run from the session scratchpad:
```
printf '{"passes":[{"pass_number":1,"head_sha":"$(touch pwned)HEAD","findings":[]}]}' | carry_state.py last-head-sha
rc=2
stdout bytes: 0
stderr: refused: last pass head_sha is not a commit sha
ls pwned -> No such file or directory
40 x 'a' head_sha -> aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  rc=0
```

Source-level mutation check: on a scratch copy of `scripts/`, the `_commit_sha` body was replaced with `return isinstance(value, str)`. `-k TestLastHeadSha` then gave `14 failed, 6 passed`, so the guard can fail. The in-suite `test_mutant_validator_lets_the_payload_through` proves the same thing with `mock.patch.object`.

## Deviations from Plan

None. The plan was executed as written.

Minor note: in `test_mutant_validator_lets_the_payload_through`, the unpatched half patches `sys.stderr` so the in-process refusal line does not print into the test output. This has no effect on any assertion.

## Threat Flags

None. The plan adds no network, auth or file-write surface. The subcommand is read-only from stdin, and the change mitigates T-60-28 and T-60-29 and covers T-60-31 (64-hex accepted).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/carry_state.py (last-head-sha), plugins/vibe-check/scripts/test_carry_state.py (class TestLastHeadSha)
- FOUND commits: 558bde3 (RED), ae560fe (GREEN)
