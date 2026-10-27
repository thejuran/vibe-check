---
phase: 57-decision-continuity-within-closure
plan: 21
subsystem: scoring / decision continuity (score.py mechanism)
tags: [score, carried-index, pooled-evidence, deterministic-lead, prior-gate, in-01, mutants, d-19, gap-closure]
requires: ["57-20"]
provides:
  - carried_by_hash index of every carried record, built before the NV route, min_confidence and per-member drops
  - row carried-ness, nearby and prior pooled over every carried copy of a row's identity
  - one hash gate on every prior source, the lead's own snapshot included (IN-01 closed in code)
  - deterministic lead (member sort ends with the record's line)
  - 7 mechanism mutants (4 re-anchored, 3 new) + TestPooledPriorUnit
affects: [57-22, 57-23]
tech-stack:
  added: []
  patterns: [index-before-filter evidence pooling, ranked (never positional) prior selection]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_score.py
decisions:
  - "57-21: a row's evidence (carried-ness, nearby, prior) is pooled over every carried record of its identity from carried_by_hash, built before any filter; which record leads and which filter removed a copy never decide the stamp"
  - "57-21: the pooled prior is the candidate with the latest nearby_at, then the oldest at_pass (fail toward asking); every candidate, the lead's own snapshot included, must carry the row's stable_hash"
  - "57-21: a carried snapshot whose stored stable_hash differs from the row's computed hash is no prior (test fixtures that stored a placeholder hash now store the real one)"
metrics:
  duration: ~25min
  completed: 2026-10-27
  tasks: 2
  files: 3
---

# Phase 57 Plan 21: Pooled carried evidence before every filter Summary

score.py now builds one carried-by-hash index of every carried record before any filter runs and reads a row's carried-ness, nearby check and prior from it, so neither the lead choice, the arrival order nor a min_confidence / per-member drop can take a copy's evidence away; every prior source passes one hash gate and the lead is deterministic by line. Every 57-20 red except the D-20 defer test (57-22's) is green, and every new guard has a mutant that trips a named real-chain fixture.

## Code change (score.py)

- New pure helpers beside `_finding_identity`: `_current_hash(f)` (the group loop's hash rule; `_finding_identity` and `stable_hash` untouched), `_carried_index(working, carried_obligations, nv_carried_ids)` (status persisted / needs-recheck, NV records excluded, `obligation` attached when the record was a row), `_any_nearby(records, ranges)`, `_prior_rank(snapshot)` (latest `nearby_at` first, unstamped/non-int last; then oldest `at_pass`, missing last), `_pooled_prior(candidates)` (`return min(candidates, key=_prior_rank)`).
- `carried_by_hash = _carried_index(...)` at line 2418, directly after the "verdict: record not carried" loop and above the "Needs-verification route" comment (line 2420).
- Member sort: final element `_as_line(t[1].get("line")) or 0,`; comment rewritten (CR-01 arrival order).
- Group loop: the 57-18 seed loop and multi-line `row_carried = any(...)` replaced by `same_hash = carried_by_hash.get(survivor["stable_hash"], ())`, the gated candidate list (`o.get("stable_hash") == survivor["stable_hash"]`), the lead's own popped snapshot appended only when `best_member.get("stable_hash") == survivor["stable_hash"]`, `prior = _pooled_prior(candidates)` / `survivor["snapshot"] = prior`, `row_carried = bool(same_hash)`, `row_nearby = _any_nearby([survivor] + [r for r, _ in same_hash], changed_line_ranges)`.
- `survivors.append((survivor, surface_score, row_carried, row_nearby))`; threshold loop unpacks `row_nearby` and uses `nearby = row_nearby`; the two-line `_snapshot_for(... nearby=nearby, / carried=carried)` call is byte-identical.
- `_snapshot_for` docstring: the `carried` paragraph rewritten per plan; D-17 split sentence, all-fresh sentence, stamp condition and stamp line unchanged.
- Grep invariants (observed): helper defs 5; `carried_by_hash` 3; each anchor (`same_hash = ...get`, gate fragment, `survivor["snapshot"] = prior`, `row_carried = bool(same_hash)`, `row_nearby = _any_nearby(`, `return min(candidates, key=_prior_rank)`, line tie-break) 1; removed anchors (`survivor["snapshot"] = obl["snapshot"]`, `entry = carried_obligations.get(id(m))`, `nearby = _nearby_changed(survivor, ...)`) 0; `_snapshot_for(.*nearby=` 6; `carried=carried` 1; `survivor["status"] = "new"` 1; `(isinstance(prior, dict) or carried)` 1; `ref_kept["obligation"] = _refreshed_obligation(` 1; no added line over 100 columns.

## Mutant ledger

All seven run through `_run_mutant` (anchor unique, `_failures()` == set() unmutated). Observed failed sets come from a scratch sweep over all 14 `_ROW_TESTS`.

| Mutant (test) | Anchor -> replacement | Named trip | Observed failed set | Quoted assertion |
|---|---|---|---|---|
| test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp (re-anchored) | `survivor["snapshot"] = prior` -> `pass` | s3, d, p4 | {s3, d, p4} | s3: `None != 2 : owed nearby_at lost at the split` |
| test_seed_without_hash_equality_inherits_a_foreign_stamp (re-anchored) | `o.get("stable_hash") == survivor["stable_hash"]` -> `True` | w2 AND in01 | {w2, in01} | in01: `'nearby_at' unexpectedly found in {'at_pass': 3, ... 'nearby_at': 2}` |
| test_carried_from_lead_only_loses_the_same_lane_rereport (re-anchored) | `row_carried = bool(same_hash)` -> `row_carried = survivor.get("status") in _CARRIED_STATUSES` | b | {b} | `None != 2 : re-reported row snapshot has no nearby_at` |
| test_index_read_after_filtering_loses_the_dropped_twin (re-anchored, RENAMED from test_seed_after_dedup_loses_the_dropped_duplicate_prior) | `same_hash = carried_by_hash.get(...)` -> same list filtered to records in scored_members | p3 | {p3, p4} | p3: `None != 2 : row snapshot has no owed nearby_at` |
| test_nearby_judged_at_the_lead_only_loses_the_other_copy (new, CR-01) | `row_nearby = _any_nearby(...)` -> `row_nearby = _nearby_changed(survivor, changed_line_ranges)` | p1, p2 | {p1, p2} | p1: `None != 2 : row snapshot has no owed nearby_at` |
| test_line_tie_break_dropped_makes_the_lead_arrival_dependent (new, CR-01 arrival) | `_as_line(t[1].get("line")) or 0,` -> `0,` | p2 | {p2} | `12 != 10 : lead depends on arrival order [12, 10]` |
| test_prior_rank_first_wins_loses_the_latest_stamp (new, D-19) | `return min(candidates, key=_prior_rank)` -> `return candidates[0]` | p4 | {p4} | `None != 2 : row snapshot has no owed nearby_at: {'at_pass': 1, ... 'line': 10 ...}` |

Non-trips asserted (all observed green under the mutant): prior-not-seeded s1, s4; hash gate s3, d; carried-lead-only control, d; index-after-filter d, s3; nearby-lead-only q1, s1; tie-break p1, p3; first-wins p3, d.

Observed far-twin candidate order (pass 3, line-10 row, spy on `_pooled_prior`): `[(line 10, at_pass 1, unstamped obligation), (line 30, at_pass 2, nearby_at 2), (line 10, at_pass 1, lead's own snapshot)]`. `candidates[0]` therefore loses the stamp as the plan predicted; `candidates[-1]` (the own snapshot) also loses it, observed in the sweep.

The only method-name change is the rename above. The m57-01..08 mutants in test_score.py all still trip (see Verification).

## Verification (observed)

`pytest -q test_decision_continuity.py -rfE --tb=line` (after Task 2):
```
FAILED test_decision_continuity.py::TestDeferredStaysOpen::test_deferred_covered_member_below_threshold_stays_open
1 failed, 79 passed, 90 subtests passed in 0.30s
```
The failure is at `unexpectedly None : record 845f88b7 is not an open record (decision orphaned)` — the D-20 red 57-22 owns. 0 SUBFAILED.

After Task 1 only (before re-anchoring), the same command gave `5 failed, 66 passed, 85 subtests passed`: the D-20 red plus the four 57-18 mutants failing `0 != 1 : mutation target not unique` (test_carried_from_lead_only_loses_the_same_lane_rereport, test_seed_after_dedup_loses_the_dropped_duplicate_prior, test_seed_without_hash_equality_inherits_a_foreign_stamp, test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp).

Task 1 targeted runs:
```
-k "TestPooledEvidence or TestPriorGate or TestLeadOrderInvariance or TestSameLaneRereport or TestSplitPassNearby or TestWr01Guards or TestSameHashLeadKeepsNearbyStamp or TestRegrouping or TestPhase57EndToEnd"
29 passed, 42 deselected, 28 subtests passed
-k TestDeferredStaysOpen: 1 failed, 1 passed
test_score.py -k "TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup or ImportSet or Golden or TestStatusScrubbedOnNewFindings or TestOutputShape": 43 passed, 457 deselected, 24 subtests passed (after the fixture fixes, Deviations 1-2)
test_replay.py -k TestDiffMode: 16 passed, 48 deselected
test_carry_state.py -k ImportSet: 3 passed, 216 deselected
golden ok
carry_state untouched
```
The owner journey (TestPhase57EndToEnd) is green and its outcome unchanged (no edit to it).

Task 2:
```
pytest -q test_decision_continuity.py -k "TestPhase57Mutants or TestPooledPriorUnit": 18 passed, 62 deselected, 5 subtests passed
pytest -q test_score.py -k "TestPhase57Mutants or TestNearbyAt": 19 passed, 481 deselected, 24 subtests passed
pytest -q test_replay.py -k TestDiffMode: 16 passed, 48 deselected
pytest -q test_score.py test_carry_state.py test_verified_fixes.py test_decision_continuity.py:
FAILED test_decision_continuity.py::TestDeferredStaysOpen::test_deferred_covered_member_below_threshold_stays_open
1 failed, 885 passed, 841 subtests passed in 3.68s
```

Full suite (`pytest -q` from plugins/vibe-check/scripts, incl. test_replay.py):
```
FAILED test_decision_continuity.py::TestDeferredStaysOpen::test_deferred_covered_member_below_threshold_stays_open
1 failed, 3290 passed, 4342 subtests passed in 175.46s (0:02:55)
```
3291 tests = 3273 (57-19 gate) + 9 added by 57-20 + 9 added here. Added here (9): test_index_read_after_filtering_loses_the_dropped_twin replaces a renamed test (net 0), plus test_nearby_judged_at_the_lead_only_loses_the_other_copy, test_line_tie_break_dropped_makes_the_lead_arrival_dependent, test_prior_rank_first_wins_loses_the_latest_stamp, and TestPooledPriorUnit's test_no_candidates_is_none, test_stamped_snapshot_wins_over_an_unstamped_older_one, test_equal_stamps_take_the_oldest_at_pass, test_later_stamp_wins_over_an_earlier_one, test_non_int_nearby_at_ranks_after_a_stamped_one, test_prior_rank_never_raises. Module defs 71 -> 80.

Remaining red after this plan: exactly one, TestDeferredStaysOpen.test_deferred_covered_member_below_threshold_stays_open (D-20, 57-22).

No-weakening greps (`git diff 8a0563a -U0 -- test_decision_continuity.py`):
- `^-.*assert` lines: `self.assertEqual(src.count(old), 1, "mutation target not unique")` and `self.assertEqual(self._split_failures(), set())` (prior-not-seeded mutant now goes through `_run_mutant`, which asserts the same uniqueness and a green baseline over the wider `_ROW_TESTS`, a superset of the split tests); `self.assertIn("test_d_", failed)` (the renamed index-after-filter mutant now trips p3; the plan lists d as its non-trip — d is still asserted as a trip of the prior-not-seeded mutant).
- `^-\s*def ` count 1: `test_seed_after_dedup_loses_the_dropped_duplicate_prior` (renamed).
- test_score.py removed lines: only the two fixture lines changed in Deviations 1-2 (no assertion removed).

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 1ff5702 | feat(57-21): pool carried evidence from an index built before every filter |
| 2 | 333a5cd | test(57-21): re-anchor the 57-18 mutants and lock every pooled-evidence guard |

TDD note: the RED commits for this plan are 57-20's (1ff95f1, 9fe0e0f); 1ff5702 is the GREEN commit.

## Deviations from Plan

**1. [Rule 1 - Masked guard] m57-06 forge fixture now carries the row's stable_hash (test_score.py)**
- **Found during:** Task 1
- **Issue:** `test_score.py::TestPhase57Mutants::test_m57_06_ingress_snapshot_scrub_removed` stopped tripping: the forged fresh finding had no `stable_hash`, so the new hash gate on the lead's own snapshot also rejected it and the scrub mutant was masked. The ingress scrub does not strip `stable_hash`, so a forgery carrying the row's real hash still passes the gate — the scrub stays load-bearing.
- **Fix:** `_na_forge` adds `stable_hash=score.stable_hash("src/a.py", "a_line", "inj A")`; m57-06 trips again, TestNearbyAt's forge test stays green.
- **Cost if wrong:** none for production; if the fixture were left alone m57-06 would be a decorative guard.
- **Files:** test_score.py. **Commit:** 1ff5702

**2. [Rule 1 - Fixture vs IN-01 gate] TestSnapshot keep-branch fixture stores the row's real hash (test_score.py)**
- **Found during:** Task 1 (four-module run)
- **Issue:** `TestSnapshot.test_unchanged_carried_keeps_older_snapshot` carried a placeholder stored hash (`"0" * 64`); under the one hash gate its own snapshot is no longer a prior, so at_pass refreshed to 2.
- **Fix:** that test passes `stable_hash=probe["stable_hash"]` (the hash an unchanged carried line actually stores).
- **Cost if wrong:** if real carried rows ever store a hash that differs from this pass's computed hash while the line is unchanged (e.g. a canonical-text drift between passes), their snapshot clock now resets to this pass instead of keeping the older at_pass. That fails toward asking, never toward a silent keep.
- **Files:** test_score.py. **Commit:** 1ff5702

**3. Files touched outside the plan's list.** `git diff --name-only 8a0563a..HEAD -- plugins/` lists score.py, test_decision_continuity.py AND test_score.py (plan expected the first two). The test_score.py changes are exactly Deviations 1-2.

**4. Prior-not-seeded mutant moved onto `_run_mutant`.** The plan expected its trips to include d and p3, which `_split_failures` cannot see; it now uses `_run_mutant` over all `_ROW_TESTS`. Observed set {s3, d, p4}: p3 is NOT in it (the dropped twin's re-ask comes from pooled nearby, not from the prior), so the test asserts s3, d and p4.

**5. `_prior_rank` key shape.** Each element is a `(flag, value)` pair rather than the plan's `-(nearby_at or -1)` integer, so a negative or zero `nearby_at` can never rank after an unstamped snapshot. Same ordering for every well-formed value.

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** test_score.py would need no change (the plan's file list and acceptance named score.py and test_decision_continuity.py only). **Actual:** two test_score.py fixtures depended on the old behaviour (a forged snapshot with no hash; a placeholder stored hash). **Why:** the IN-01 gate on the lead's own snapshot is new behaviour those fixtures did not model. **Cost if wrong:** low; both changes make the fixtures more realistic, and no assertion was removed.

## Known Stubs

None.

## Threat Flags

None. T-57-67 (index admits only carry-loop statuses, NV excluded; test_fresh_finding_cannot_forge_nearby_at / s4 / TestStatusScrubbedOnNewFindings green), T-57-68 (one gate on every candidate, mutant trips w2 + in01), T-57-69 (golden ok, anchors 1 each, TestDiffMode 16) and T-57-70 (ledger above) are mitigated as planned.

## Self-Check: PASSED
- FOUND: plugins/vibe-check/scripts/score.py, plugins/vibe-check/scripts/test_decision_continuity.py, 57-21-SUMMARY.md
- FOUND: 1ff5702, 333a5cd
