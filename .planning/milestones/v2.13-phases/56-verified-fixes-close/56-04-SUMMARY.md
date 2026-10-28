---
phase: 56-verified-fixes-close
plan: 04
subsystem: scorer and carry state (confirmed-fix closure)
tags: [one-pass-limit, confirmed-fix, carry_state, retry]
requires: ["56-02 (RED retry/finalize fixtures + docstring lock)", "56-03 (_R_CF_SETTLED, recheck_settled)", "56-05 (prose forwards applied verdicts of any age)"]
provides:
  - "score.py: previous-pass age gate applies to fix-obsolete only; confirmed-fix verdicts judged at any age, bound by verified_blob == head_blob"
  - "carry_state.py: _confirmed_fix_awaiting at any later pass; _settled_unchanged helper (fail closed on unknown HEAD blob); docstring states the any-age rule"
  - "Mutants: score_m19 (blob gate), score_m20 (settled check), cs_m7 (awaiting settled check)"
affects: [56-06 (end-to-end over the six-row fixture; VFIX-06 closure)]
tech-stack:
  added: []
  patterns: ["blob freshness as the sole staleness test for applied verdicts", "settled memory suppresses re-ask until fingerprinted code changes"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_confirmed_fix.py
decisions:
  - "A settled record whose fingerprinted path is missing from head_blobs (or head_blobs is absent) counts as unchanged: not awaiting, the owner decides"
  - "A malformed recheck_settled (not a dict, or empty/non-dict fingerprint) does not suppress awaiting"
metrics:
  duration: "~20 min"
  completed: 2026-10-23
  tasks: 2
  files: 3
---

# Phase 56 Plan 04: Remove the one-pass limit on the confirmed-fix re-check Summary

Before this plan, a confirmed fix got one chance at an independent re-check. If that rerun had no eligible reviewer or no answer, the fix verdict aged out and the item stayed open for good. The scorer now judges a confirmed-fix (`applied`) verdict at any age. The only staleness test is the blob check: the repaired blob must still be HEAD's blob. Finalize lists the item as awaiting on every later pass until a routed `resolved` closes it, or until a reviewer's still-applies settles it while the code stays unchanged. `fix-obsolete` keeps its previous-pass rule. Full suite: **3051 passed, 0 failed** (baseline 3041 passed, 6 failed; +4 new tests).

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Relax the applied-verdict age gate in score.py | 7f67f88 | score.py, test_confirmed_fix.py |
| 2 | carry_state awaiting at any later pass, settled-aware; docstring | 420112b | carry_state.py, test_confirmed_fix.py |

## What changed

- `score.py` `_accept_verdict`: `if not confirmed and v["at_pass"] != pass_number - 1:` (reason string kept). The blob gate directly below is unchanged (1 occurrence of `"verdict: evidence changed since verification"`, same as HEAD). The `_R_CF_SETTLED` rejection (56-03) is wired on the `confirmed` branch before `_confirmed_fix_recheck`. The docstring now describes the any-age rule, the retry, and the settled memory. Imports are unchanged (hashlib, json, re, sys).
- `carry_state.py`: `_confirmed_fix_awaiting(record, state, last, head_blobs=None)` no longer requires `at_pass == last pass`. It now also requires `not _settled_unchanged(record, head_blobs)`, and `finalize_counts` passes `head_blobs` in. In the module docstring, the "applied" paragraph now says "whatever its `at_pass`". Imports are still `['json', 'os', 'sys']`. The `at_pass == last pass` count went from 2 to 1, because `_fix_closes` still has it.
- `test_confirmed_fix.py`: three 56-02 staleness assertions were narrowed from "stale or changed" to `assertIn(R_EVIDENCE_CHANGED)` + `assertNotIn(R_STALE)`, and `STALE_OR_CHANGED` was removed. Added `test_mutant_applied_blob_gate_removed` (score_m19), `test_mutant_cf_settled_check_removed` (score_m20), `test_mutant_awaiting_settled_check_removed` (cs_m7) and `test_settled_unchanged_fails_closed_without_head_blobs`.

## Verification (observed)

- Task 1 verify: `pytest -q test_confirmed_fix.py -k "RetryAfterInconclusive or ScoreConfirmedFix or IndependentRecheck or Mutants"`: 44 passed. `pytest -q test_score.py -k "VerdictFixObsolete or VerdictGuard"`: 20 passed.
- Task 2 verify: the finalize/record/mutants/docstring selection had 28 passed. `test_carry_state.py`: 140 passed. `test_confirmed_fix.py -k "not TestProse56"`: 81 passed.
- Full suite (bare `pytest -q` from scripts/): 3051 passed, 4060 subtests passed, 0 failed. The 6 failures this plan owned are now green: TestFinalizeCountsConfirmedFix x3, TestRetryAfterInconclusive x2 and TestProse56::test_carry_state_docstring_says_any_age.
- Each mutant was confirmed to trip: the real code stays open (or not awaiting), and the mutant closes (or lists the item as awaiting).
- GOLDEN_DIGEST: `test_hash_and_golden_digest_unchanged` is green.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2] Fail-closed coverage for `_settled_unchanged`**
- **Found during:** Task 2
- **Issue:** the plan specifies fail-closed behavior when head_blobs is None or lacks the path, but no existing test pinned it.
- **Fix:** added `test_settled_unchanged_fails_closed_without_head_blobs` (None, {}, other-path-only).
- **Cost if wrong:** none; an extra green test.
- **Commit:** 420112b

**2. Narrowed assertions use assertIn rather than list equality**
- **Found during:** Task 1
- **Issue:** two of the three narrowed tests send a routed request, so `filtered[]` also carries the request-level `verdict: routed re-check without a confirmed fix` next to the blob rejection. The fix verdict's own reason is exactly the blob reason, so the test asserts that reason is present and `stale fix verdict` is absent.
- **Cost if wrong:** low. A regression that added a second fix-verdict-level reason on top of the blob reason would not trip these three tests.
- **Commit:** 7f67f88

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-56-14 is covered by score_m19, T-56-15 by score_m20 and cs_m7.

## Requirements

VFIX-02 is now green at the script layer: the retry tests pass. VFIX-06 is left for 56-06, as the plan says.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py, carry_state.py, test_confirmed_fix.py
- FOUND commits: 7f67f88, 420112b
