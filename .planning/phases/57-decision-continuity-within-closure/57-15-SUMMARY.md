---
phase: 57-decision-continuity-within-closure
plan: 15
subsystem: score
tags: [score, snapshot, nearby-at, split-pass, mutants, gap-closure]
requires:
  - phase: 57-14
    provides: real-chain RED fixtures TestSplitPassNearby s1-s4 and the split-row shape guard
provides:
  - "_snapshot_for carried arm: a split row whose lead record existed before this pass is stamped on a nearby change"
  - "lead-obligation prior seeding: an owed nearby_at and older at_pass survive the split"
  - "mutants m57-08 (unit), score_split_carried (trips s1), score_split_seed (trips s3)"
affects: [57-16, carry_state decision reads, finalize gate, batch card]
tech-stack:
  added: []
  patterns: ["carried= keyword derived from score.py-owned status (ingress strips envelope status)"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
key-decisions:
  - "D-17 applied to the owner journey: pass 7 (lead rewritten at line 13, compliance member at line 14 splits out) now re-asks with cause nearby; a quiet pass 8 under the owner's new decision writes"
duration: 11min
completed: 2026-10-26
requirements: [DECN-03]
---

# Phase 57 Plan 15: Split-pass nearby stamp Summary

**The pass a covered or absorbed finding splits into its own row now stamps `snapshot.nearby_at` when the change reaches it. A fresh finding is still never stamped. A re-ask that was owed before the split carries over to the new row.**

## Code change (score.py)

- `def _snapshot_for(row, pass_number, nearby=False, carried=False):` with the stamp condition
  `if nearby and (isinstance(prior, dict) or carried) and cur["at_pass"] is not None:`. The stamp line `cur["nearby_at"] = cur["at_pass"]` is unchanged (m57-01 anchor). The docstring covers both ways a row can have existed before this pass, plus the D-17 no-exemption rule.
- `_CARRIED_STATUSES = ("persisted", "needs-recheck")` sits above `_OBLIGATION_ROW_KEYS`.
- Group loop, after the `status` default and before the member loop:
  ```python
  if id(best_member) in carried_obligations and "snapshot" not in survivor:
      lead_obl = carried_obligations[id(best_member)]["obligation"]
      if (lead_obl.get("stable_hash") == survivor["stable_hash"]
              and isinstance(lead_obl.get("snapshot"), dict)):
          survivor["snapshot"] = lead_obl["snapshot"]
  ```
  The comment on `same_hash_prior` now says it is a no-op once the lead's own obligation has seeded the prior.
- Threshold loop: `survivor["snapshot"] = _snapshot_for(survivor, pass_number, nearby=nearby, carried=survivor.get("status") in _CARRIED_STATUSES)`. This is a single line, so the key_link grep and the "every call names `nearby=`" grep both still match.
- These were not touched: `stable_hash`, `_nearby_changed`, `_refreshed_obligation`, `_kept_open_rows`, the ingress scrub, the replay member/status anchors, and carry_state.py (byte-identical to 0fd360a).
- T-57-43 check: the ingress scrub strips `status` from fresh findings (score.py ~2190), so `carried` can only come from status that score.py set itself. `test_fresh_finding_cannot_forge_nearby_at` still passes.

## Mutant ledger

| Mutant | Anchor | Named test that fails | Observed failed set |
|---|---|---|---|
| m57-08 (unit, test_score) | `(isinstance(prior, dict) or carried)` -> `isinstance(prior, dict)` | `test_m57_08_carried_arm_removed` check raises | n/a (unit check) |
| score_split_carried (patch `score._snapshot_for`) | `(isinstance(prior, dict) or carried)` -> `isinstance(prior, dict)` | s1 | `['test_s1_']` (s2 passes because the seeded prior lets the stamp land; s3 and s4 pass) |
| score_split_seed (patch `score.run`) | `survivor["snapshot"] = lead_obl["snapshot"]` -> `pass` | s3 | `['test_s3_']` (s1, s2 and s4 pass) |

With the real scorer the failed set is `[]` for both.

## Verification (observed)

- `pytest -q test_decision_continuity.py -k "TestSplitPassNearby or test_split_row_snapshot"` -> `5 passed, 41 deselected`
- `pytest -q test_score.py -k "TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup or ImportSet or Golden"` -> `33 passed, 467 deselected, 24 subtests passed`
- `pytest -q test_score.py test_decision_continuity.py test_carry_state.py test_verified_fixes.py` -> `852 passed, 811 subtests passed` (after the journey update; before it: `1 failed` = journey pass 7, see Deviation 1)
- `pytest -q test_replay.py -k TestDiffMode` -> `16 passed, 48 deselected`
- Mutant tests: `2 passed, 46 deselected`. `-k "TestPhase57Mutants or TestSplitPassNearby"` -> `9 passed`. Full test_decision_continuity.py -> `48 passed, 60 subtests passed`
- Full suite after Task 1: `3257 passed, 4312 subtests passed`. Full suite after Task 2: `3259 passed, 4312 subtests passed in 222.12s`. 0 failed in both; test_replay.py was included.
- `golden ok`. Both ImportSet runs: `3 passed` each.
- Acceptance greps: def signature 1, `or carried` 1, `_CARRIED_STATUSES` 1, `carried=survivor.get...` 1, seed assignment 1, `_snapshot_for(` 6, `_snapshot_for(.*nearby=` 6, m57-01 anchor 1, `survivor["status"] = "new"` 1.
- I did not run the replay candidate or diff. The plan gives that to 57-16 (T-57-46).

## Commits

- 3b78957 fix(57-15): stamp nearby_at on the pass a carried finding splits into its own row
- 7e22d6d test(57-15): prove the split-pass guards with end-to-end mutants

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated the owner journey's pass 7 to D-17 behaviour**
- **Found during:** Task 1 verification. `TestPhase57EndToEnd::test_owner_is_asked_exactly_when_evidence_changes` failed at `decision_state(rec, s) == "current"`, which came back `'stale'`.
- **Issue:** Pass 7 of the journey is the D-17 shape. The lead's line 13 is rewritten with a real diff `{F: [[13, 13]]}`, which causes the compliance member at line 14 (inside the window) to split out. The 57-07 expectation, "inherited, not asked", is the pre-D-17 behaviour that the owner overruled ("no exemption for the neighbour's own fix"). The plan assumed every existing fixture would stay green and did not foresee this.
- **Fix:** Pass 7 now asserts `nearby_at == 7`, state `stale`, cause `nearby`, that the gate does not write, and that the card shows `[hD]`. The owner then dismisses hD. A new quiet pass 8 asserts `current`, gate `write`, and an empty card. The header comment changed from "seven passes" to "eight passes". Three assertions were replaced, so Task 2's `^-.*assert` grep would count 3 removed lines if it were measured against the pre-plan tree; measured against Task 1's commit it prints 0. Inheritance with no nearby edit is still covered by `split_scenario` (empty diff) and the R6 fixtures.
- **Cost if wrong:** if the owner did intend this journey pass to stay "inherited, not asked", D-17 has to be revisited. This change and the score.py arm would both need reverting.
- **Files modified:** plugins/vibe-check/scripts/test_decision_continuity.py
- **Commit:** 3b78957

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** no existing fixture changes behaviour. **Actual:** the 57-07 owner journey pinned the exact split shape D-17 rules on, so it now re-asks. **Why:** D-17 makes the ordinary split re-ask, which the verification had predicted ("D-09 inheritance becomes rare in practice"). **Cost if wrong:** one journey pass goes back to its old expectation.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py, test_score.py, test_decision_continuity.py (modified)
- FOUND: 3b78957, 7e22d6d
