---
phase: 59-stale-decisions-and-lost-deferrals
plan: 02
subsystem: vibe-check scorer (score.py decision continuity, producer side)
tags: [STALE-02, STALE-03, STALE-04, pooled-evidence, kept-open, mutation-lock, D-21]
requires: ["59-01 red fixtures at 82ec58b"]
provides:
  - "_kept_open_rows(..., carried_by_hash=None): pooled prior + nearby over every carried copy, one row per dropped record"
  - "group-loop row_nearby over carried same-hash copies + covered members (no fresh survivor line)"
  - "test_p4_far_twin_new_copy_is_not_evidence (D-21)"
  - "pooled_prior_scenario, foreign_copy_scenario, edited_kept_open_scenario, covered_scope_scenario builders"
  - "_EXPECTED_RED_UNTIL_59_03 (59-03 empties it)"
affects: [59-03, 59-06]
tech-stack:
  added: []
  patterns: ["probe every guard arm with an in-place mutant before writing mutant tests; drop arms nothing can trip"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "Task 1 landed carried=bool(same) alone; the covered arm is gone (the D-20 covered member is indexed in carried_by_hash)"
  - "Kept-open rows dedup per dropped working record (the existing `done` set); the planned _finding_identity `emitted` set was decorative and was removed"
  - "covered_m drops the `m is not best_member` arm (a carried lead is already in same_hash); keeps the obligation and status arms, each locked"
  - "Kept-open prior is _pooled_prior(candidates) with the row's own obligation always a candidate; the obl.get('snapshot') fallback was redundant and removed"
  - "Members carrying their own obligation do not re-ask the row (D-16 scope), locked by test_m59_"
metrics:
  duration: "~16 min"
  completed: 2026-10-29
  tasks: 3
  files: 2
requirements: [STALE-02, STALE-03, STALE-04]
---

# Phase 59 Plan 02: Producer-side pooled evidence Summary

Kept-open rows now pool their prior and nearby check over every carried copy of the decided identity and emit one row per dropped copy. The group loop judges a row at its carried copies and covered members, not at a fresh survivor's own line. CR-01, CR-01 multi-pass and CR-04 are green. Every new or changed guard arm has a mutant that trips a named fixture.

## Green SHAs

| Fixture | Red at | Green at |
|---|---|---|
| test_cr01_edit_beside_the_second_copy_reasks | 82ec58b | c46f4dc |
| test_cr01_multipass_second_copy_stays_tracked | 82ec58b | c46f4dc |
| test_cr04_removed_guard_beside_covered_member_reasks | 82ec58b | 25ce414 |
| test_cr02_edit_beside_the_second_sidecar_reasks | 82ec58b | still red (59-03) |
| test_dmc_deferred_covered_member_below_min_confidence_stays_open | 82ec58b | still red (59-03) |

Controls still green: test_c59_cr01_edit_at_45_keeps_decision, test_c59_cr04_edit_at_line_20_keeps_decision, test_dmx_dismissed_covered_member_below_min_confidence_may_drop, test_s4_, test_p1_/p2_/p3_/q1_/q3_, TestDeferredStaysOpen (other than dmc).

`carried=` form landed: **`carried=bool(same)`**. TestDeferredStaysOpen stayed green without the `covered` arm, so the arm was dropped. Its mutant (`carried=bool(same))` -> `carried=False)`) trips three test_deferred_ fixtures.

## Tasks

| Task | Name | Commit | Verify (observed) |
|------|------|--------|-------------------|
| 1 | _kept_open_rows pools over carried_by_hash, one row per occurrence | c46f4dc | `-k "cr01 or c59_cr01 or TestDeferredStaysOpen or p3 or TestGolden"` -> 11 passed, 1 failed (test_dmc_, expected red until 59-03); `test_score.py -k Golden` -> 9 passed; greps: `carried_by_hash=None` 1, `carried_by_hash=carried_by_hash` 1, `visible.add(obl["stable_hash"])` 0, `^_NEARBY_LINES = 5` 1 |
| 2 | Group-loop row_nearby over copies + covered members; p4 rewritten | 25ce414 | targeted `-k` -> 10 passed; `TestSplitPassNearby or TestPooledEvidence or TestSameLaneRereport or TestWr01Guards` -> 18 passed; new row_nearby line count 1, `_any_nearby([survivor]` 0; replay member anchor count 1 |
| 3 | Re-anchor moved mutants, add mutants for every new guard | 323c0d1 | `-k TestPhase57Mutants` -> 25 passed; `test_decision_continuity.py` -> 2 failed (cr02_edit, dmc), 109 passed; `test_replay.py -k member_only` -> 1 passed; `assertIn("test_p4_"` count 1 |

## Full offline suite (after 323c0d1)

`cd plugins/vibe-check/scripts && pytest -q` -> **2 failed, 3613 passed, 4772 subtests passed in 160.72s**. The two failures are exactly the 59-03 fixtures: test_cr02_edit_beside_the_second_sidecar_reasks and test_dmc_deferred_covered_member_below_min_confidence_stays_open. test_replay.py ran inside the full suite and passed. GOLDEN_DIGEST did not change (TestGolden and test_score Golden both pass).

## Mutant map (each probed in place first, then written as a test)

| Guard | Mutant test | Trips |
|---|---|---|
| kept-open per-record emit (no hash-level dedup) | test_kept_open_hash_dedup_loses_the_second_copy | cr01 multipass |
| kept-open nearby over copies | test_kept_open_own_line_only_loses_the_other_copy | cr01 edit@33 |
| kept-open nearby at own line | test_kept_open_copies_only_loses_an_edited_row_own_line | l59 |
| kept-open pooled prior | test_kept_open_prior_not_pooled_loses_the_latest_stamp | cr02 pooled |
| kept-open own obligation as candidate | test_kept_open_own_obligation_not_a_candidate_loses_its_stamp | k59 |
| kept-open hash gate (T-59-04) | test_kept_open_seed_without_hash_equality_inherits_a_foreign_stamp | g59 |
| kept-open `carried=bool(same)` | test_kept_open_covered_row_without_carried_is_not_stamped (re-anchored) | test_deferred_ |
| prior rank (latest stamp wins) | test_prior_rank_first_wins_loses_the_latest_stamp (re-pointed) | cr02 pooled |
| row_nearby covered members | test_covered_members_not_judged_loses_the_covered_guard | cr04 |
| covered_m obligation arm | test_covered_members_with_own_obligation_judged_reasks_the_row | m59 |
| covered_m status arm (D-21) | test_fresh_members_judged_reasks_on_first_raise | n59 |
| no fresh survivor line (D-21) | test_survivor_own_line_judged_stamps_a_new_copy | p4 |
| row_nearby as a whole | test_nearby_judged_at_the_lead_only_loses_the_other_copy (re-anchored) | p1, cr04 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 59-01's TestStaleDecisions59._assert_reasked checked the wrong gate list for medium rows**
- **Found during:** Task 1
- **Issue:** After the fix, the CR-01 row was stamped, `stale`/`nearby`, with gate `medium-ack-loop`. The helper still required the hash in `outstanding_cw_hashes`. The CR-01 copies score medium (conf 60), so they are listed in `unacknowledged_medium_hashes` instead.
- **Fix:** The helper now checks the gate list for the record's own band. The `gate != "write"` assertion is unchanged.
- **Cost if wrong:** if CR-01 was meant to be a warning-band shape, the fixture would need conf 75 instead. The re-ask itself is still proven either way.
- **Files modified:** test_decision_continuity.py
- **Commit:** c46f4dc

**2. [Rule 2 - Decorative guard] The planned `emitted` identity set was removed**
- **Found during:** Task 3 (in-place mutant probe across the full suite)
- **Issue:** Disabling the `_finding_identity(m) in emitted` check left the full suite at the same failure set. The existing `done` set already dedups per working record, and two distinct dropped carried records cannot share one occurrence identity.
- **Fix:** Removed the set. Per-record emission is now locked by the "hash-level dedup restored" mutant, which trips cr01 multipass.
- **Cost if wrong:** if some future path drops two working records with the same occurrence identity, they get two kept-open rows. carry_state collapses same-hash rows, so the effect would be cosmetic.
- **Commit:** 323c0d1

**3. [Rule 2 - Decorative guard] Removed the `m is not best_member` arm in covered_m and the kept-open `obl.get("snapshot")` fallback**
- **Found during:** Task 3 probe
- **Issue:** Neither change tripped any fixture. A carried lead is already in `same_hash` under the row hash. The fallback duplicated the own-obligation candidate.
- **Fix:** Removed both. The own-obligation candidate is now the only path, locked by k59.
- **Cost if wrong:** none observed. The suite results are identical with and without each removed arm.
- **Commit:** 323c0d1

**4. [Rule 2 - Missing lock] Five new guard arms had no fixture; added g59/k59/l59/m59/n59**
- **Found during:** Task 3 probe
- **Issue:** The kept-open hash gate (T-59-04), the kept-open own-line nearby, the own-obligation candidate, and the covered_m obligation and status arms tripped nothing in the existing suite.
- **Fix:** Added the builders `foreign_copy_scenario`, `edited_kept_open_scenario` and `covered_scope_scenario`, plus five fixtures, each tripped by its own mutant.
- **Cost if wrong:** m59 encodes a product reading of D-16: a member with its own decision re-asks only that decision, not the covered row. If the owner wants the row re-asked too, flip m59 and drop the obligation arm.
- **Commit:** 323c0d1

**5. [Plan detail] The cr02 pooled-prior fixture uses a CR-02 variant, and its prior is pooled at the kept-open site**
- **Found during:** Task 3
- **Issue:** Using `cr02_scenario` itself for pass 3 doesn't work. Its injections share lines 10/30 with the hA copies, so they can't be rewritten without re-hashing hA, and a plain re-check of a `persisted` lead is rejected ("record not needs-recheck").
- **Fix:** `pooled_prior_scenario` puts the injections one line below each copy (11, 31, still grouped) and uses conf 60. Pass 3 rewrites 11/31 and resolves both via re-check verdicts, so both hA copies become kept-open rows. The test asserts the @10 row has `nearby_at == 2`. It passes on this commit.
- **Cost if wrong:** none for coverage. Both prior-rank mutants now point at it by full test name.

**6. [Plan detail] The split-seed mutant no longer trips the cr02 fixture; its p4 assertion was dropped**
- **Issue:** `survivor["snapshot"] = prior` is only on the group-loop path, and the cr02 pooled fixture goes through the kept-open path. The plan's direction to point "both prior-rank mutants" at cr02 holds for `_pooled_prior` first-wins but not for split-seed.
- **Fix:** The split-seed mutant keeps its s3 and d assertions, which still trip, and the p4 assertion is gone. The kept-open equivalent ("prior not pooled") has its own mutant that trips cr02 pooled.

**7. [Plan detail] `_EXPECTED_RED_UNTIL_59_03` holds full test names and `_failures` skips them**
- **Issue:** The plan proposed subtracting prefixes. `test_cr02_` is shared by the red cr02_edit fixture and the green cr02_pooled fixture, so with prefix subtraction any `assertIn("test_cr02_")` would pass trivially, which would make it a decorative assertion.
- **Fix:** The set holds full names and `_failures` skips them. `_failures` also reports full names, and the cr02 pooled mutants assert on the full name. 59-03 empties the set (comment in place).

**8. [Re-anchor] The lead-only mutant now asserts p1 and cr04 (p2 dropped)**
- p2 no longer trips under `_any_nearby([survivor])`, because the same-lane carried copy is the lead. p1 and cr04 both trip, as the plan specified.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** the `id(m) not in carried_obligations` arm keeps s4 green. **Actual:** s4's row has a fresh lead, so `_snapshot_for` never stamps it whatever covered_m holds. s4 does not depend on the arm. **Why:** an uncarried row needs a prior or `carried` before it can be stamped. **Cost if wrong:** none. The arm is now locked by m59.

## Residuals for 59-06 / Phase 61

- D-02 accepted residual, unchanged: once a new identical copy is carried (pass 3 and later), an edit beside it still re-asks. No origin marker was added.
- test_replay.py passed in the full suite. No replay delta was observed.

## Known Stubs

None.

## Threat Flags

None. T-59-03 (ingress scrub) is untouched. T-59-04 (hash gate) is kept at both pooling sites and is mutation-locked at each: `test_seed_without_hash_equality_inherits_a_foreign_stamp` for the group loop and `test_kept_open_seed_without_hash_equality_inherits_a_foreign_stamp` for kept-open rows. T-59-05: every snapshot read is behind an `isinstance(..., dict)` guard. `_NEARBY_LINES`, `_nearby_changed`, `stable_hash` and `_refreshed_obligation` are unchanged.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py (`carried_by_hash=None` x1, `carried_by_hash=carried_by_hash` x1, new row_nearby line x1)
- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (`def test_p4_far_twin_new_copy_is_not_evidence` x1, `def test_cr02_pooled_prior_carries_the_latest_owed_stamp` x1)
- FOUND: commits c46f4dc, 25ce414, 323c0d1
