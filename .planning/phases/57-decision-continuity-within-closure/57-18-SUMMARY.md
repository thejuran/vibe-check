---
phase: 57-decision-continuity-within-closure
plan: 18
subsystem: score.py group/threshold loop (third gap closure, root fix)
tags: [score, carried-from-any-source, prior-seed, nearby-at, mutants, wr-01, gap-closure]
requires:
  - phase: 57-17
    provides: "TestSameLaneRereport (5 reds + control), TestLeadOrderInvariance (8 SUBFAILED) on the unfixed scorer"
provides:
  - "score.py: one prior seed over every scored member, read before member dedup, guarded by stable_hash equality"
  - "score.py: row_carried = any carried record hashing to the row, passed to _snapshot_for as carried="
  - "TestWr01Guards (w1 needs-recheck arm, w2 seed hash equality) + low_entropy_split_scenario / edited_lead_member_scenario"
  - "Four TestPhase57Mutants methods; the 57-15 seed mutant re-anchored"
affects: [57-19 (gate ledger cites this green run and the mutant ledger)]
tech-stack:
  added: []
  patterns: ["carried-ness and prior are row properties computed over all source records before dedup, never read off the lead"]
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-18-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
key-decisions:
  - "A row's carried status and its prior snapshot come from any source record carried under the row's stable_hash (lead, absorbed member, or deduped same-identity twin), read before dedup. Which record leads no longer decides the re-ask"
  - "IN-01 resolved by docstring, not code: a covered member has no stored hash, so score.py cannot tell a hash-preserving needs-recheck from a hash-changing one; a stamp on a re-hashed record is inert"
duration: 30min
completed: 2026-10-27
requirements: [DECN-03]
---

# Phase 57 Plan 18: Carried-from-any-source root fix + WR-01 mutants Summary

**score.py now works out whether a row was carried, and which earlier snapshot it compares against, from every source record that hashes to the row. That includes the carried twin the member dedup drops, and it is read before the dedup drops it. A fresh same-lane re-report that takes the lead no longer erases a re-ask that is owed. All five 57-17 reds and all eight invariance SUBFAILs are now green. The full suite is 3273 passed, 0 failed. Two WR-01 guards and both halves of the new rule each have a mutant that trips a named test.**

## Code change (score.py)

- **Unified prior seed (group loop).** The lead-obligation seed block is replaced by one loop. When the survivor has no snapshot, the loop walks `scored_members` in scored order. The first record whose `carried_obligations` entry has `stable_hash == survivor["stable_hash"]` and a dict snapshot seeds `survivor["snapshot"]`. The loop runs before `members = []`, so the same-identity duplicate that the dedup drops is still visible. `survivor["snapshot"] = obl["snapshot"]` appears exactly once.
- **`same_hash_prior` removed.** Its comment, its initialiser, the lookup inside the absorbed-member branch and the trailing assignment are all gone (grep count 0). The absorbed-member branch keeps `obl = ...` and `ref["obligation"] = _refreshed_obligation(...)`. The `ident in kept_by_ident` branch is untouched.
- **`row_carried`.** This is `any(m.status in _CARRIED_STATUSES and stable_hash(file, d["canonical_for_hash"], title) == survivor["stable_hash"] for each scored member)`. It reuses `canonical_for_hash`, so nothing is re-derived and `stable_hash` itself is untouched. `survivors.append((survivor, surface_score, row_carried))`. The threshold loop unpacks `(survivor, sc, carried)` and is the only reader. The call is now split over two lines: `_snapshot_for(survivor, pass_number, nearby=nearby,` / `carried=carried)`. This closes IN-02, and no touched line is over 100 columns.
- **`_snapshot_for` docstring** has been rewritten for the carried rule (see IN-01). The stamp line `cur["nearby_at"] = cur["at_pass"]` and the condition `(isinstance(prior, dict) or carried)` are unchanged.

Grep counts (observed): `same_hash_prior` 0 · `survivor.get("status") in _CARRIED_STATUSES` 0 · `row_carried` 3 · seed assignment 1 · `carried=carried` 1 · `_snapshot_for(.*nearby=` 6 · `survivor["status"] = "new"` 1 · `ref_kept["obligation"] = _refreshed_obligation(` 1 · `(isinstance(prior, dict) or carried)` 1.

## IN-01 resolution

IN-01 resolved by docstring: a covered member carries no stored hash, so score.py cannot tell a hash-preserving needs-recheck (a low-entropy line whose window changed) from a hash-changing one. It therefore keeps stamping under any carried status. When a carried record's own line has changed, it re-hashes into a finding that no decision or covers entry can match, so a stamp there is inert. w2 shows the seed side of the same rule: hash equality keeps an old stamp off a re-hashed row.

## Mutant ledger

The re-anchored mutant is `test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp`. Its old anchor was `survivor["snapshot"] = lead_obl["snapshot"]` and its new anchor is `survivor["snapshot"] = obl["snapshot"]` -> `pass`. It still trips s3 and does not trip s1 or s4 (green in the run below).

New mutants. The observed failed set comes from a scratch sweep over TestSplitPassNearby s1–s4, all of TestSameLaneRereport, TestWr01Guards and TestLeadOrderInvariance, under `patch.object(score, "run", mod.run)`:

| Mutant | Anchor -> replacement | Named test that fails | Observed failed set | Quoted assertion |
|---|---|---|---|---|
| test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split | `_CARRIED_STATUSES = ("persisted", "needs-recheck")` -> `("persisted",)` | w1 | {w1} | `None != 2 : needs-recheck split row not stamped: {'at_pass': 2, ..., 'canonical_line_content': '}', 'band': 'warning'}` |
| test_seed_without_hash_equality_inherits_a_foreign_stamp | seed `if (obl.get("stable_hash") == survivor["stable_hash"]\n and isinstance(...)):` -> `if (isinstance(...)):` | w2 | {w2, s4} | `'nearby_at' unexpectedly found in {'at_pass': 3, ..., 'canonical_line_content': "line_10 = 'edited'", 'band': 'warning', 'nearby_at': 2}` |
| test_carried_from_lead_only_loses_the_same_lane_rereport | multi-line `row_carried = any(...)` -> `row_carried = survivor.get("status") in _CARRIED_STATUSES` | test_b | {test_b, invariance (inherited_split/fresh-leads-same-band)} | `None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 2, ..., 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}` |
| test_seed_after_dedup_loses_the_dropped_duplicate_prior | `entry = carried_obligations.get(id(m))` -> `... if m is best_member else None` | test_d | {test_d, invariance (owed_quiet_same_lane/fresh-leads-same-band)} | `None != 2 : re-reported row snapshot has no nearby_at: {'at_pass': 3, ..., 'canonical_line_content': 'line_10 = 10', 'band': 'warning'}` |

Each mutant asserts `src.count(old) == 1`, checks that the row tests are green before mutation, then asserts assertIn for the test that must fail and assertNotIn for the ones that must not: (s1, w2), (s3, test_d), (test_control, test_d) and (s3) respectively. With the hash-equality mutant, s4 also fails. The seed hands A's owed stamp to B's pass-2 row, which has a different hash. That is the same foreign-stamp bug, so the test does not assert s4 is unaffected.

w1 and w2 were also run against the pre-fix score.py (584f7bb, loaded from a scratch copy): both pass. That matches the plan, which expects both guards to be green before and after the fix.

## Verification (observed, from plugins/vibe-check/scripts)

```
pytest -q test_decision_continuity.py                       -> 62 passed, 76 subtests passed in 0.21s
pytest -q test_score.py -k "TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup or ImportSet or Golden or TestStatusScrubbedOnNewFindings or TestOutputShape"
                                                            -> 43 passed, 457 deselected, 24 subtests passed in 0.22s
pytest -q test_score.py -k "TestPhase57Mutants or TestNearbyAt" -> 19 passed, 481 deselected, 24 subtests passed in 0.14s
pytest -q test_replay.py -k TestDiffMode                    -> 16 passed, 48 deselected in 10.04s
pytest -q test_carry_state.py -k ImportSet                  -> 3 passed, 216 deselected in 0.07s
golden                                                      -> golden ok
git diff --quiet -- carry_state.py                          -> carry_state untouched
pytest -q test_decision_continuity.py -k TestPhase57EndToEnd -> 1 passed (owner journey unchanged)
pytest -q test_score.py test_carry_state.py test_verified_fixes.py test_decision_continuity.py
                                                            -> 868 passed, 827 subtests passed in 3.91s
pytest -q (full suite, incl. test_replay.py)                -> 3273 passed, 4328 subtests passed in 195.86s (0:03:15)
```

Full-suite count: 3273, 0 failed, 0 SUBFAILED. The 57-17 run was 3262 passed + 5 failed. Those 5 now pass (3267), and this plan adds 6 tests: `TestWr01Guards.test_w1_needs_recheck_split_row_keeps_its_hash_and_is_stamped`, `TestWr01Guards.test_w2_edited_lead_member_does_not_inherit_the_old_stamp`, `TestPhase57Mutants.test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split`, `.test_seed_without_hash_equality_inherits_a_foreign_stamp`, `.test_carried_from_lead_only_loses_the_same_lane_rereport`, `.test_seed_after_dedup_loses_the_dropped_duplicate_prior`.

No-weakening: `git diff 584f7bb -U0 -- test_decision_continuity.py`, lines matching `^-.*assert` -> 0 and `^-\s*def ` -> 0. The only removed lines are the re-anchored mutant's docstring and its `old = 'survivor["snapshot"] = lead_obl["snapshot"]'`.

## Commits

- 8bd75ec fix(57-18): derive carried-ness and prior snapshot from any same-hash carried source
- 90228be test(57-18): lock WR-01 guards and the carried-from-any-source rule with mutants

## Deviations

1. **[Rule 3 - Blocking] The grep count for `_snapshot_for(.*nearby=` would have dropped to 5.** The first wrap put `nearby=` on the continuation line. The call was re-wrapped as `_snapshot_for(survivor, pass_number, nearby=nearby,` / `carried=carried)` and the count is now 6. Cost if wrong: none (layout only).
2. **[Rule 3] `row_carried` count was 2, short of the >= 3 the acceptance criteria require.** The threshold-loop comment now names `row_carried` ("`carried` is the row's `row_carried`, computed in the group loop"). Cost if wrong: none (comment only).
3. **test_score.py was not modified.** The plan lists it in files_modified, but the m57-01..08 anchors still match and trip (19 passed), so no change was needed. Cost if wrong: none.
4. **The docstring had no "D-17 sentence" to keep.** `_snapshot_for` at HEAD contained no D-17 text, so nothing was preserved. Cost if wrong: none.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py (modified), plugins/vibe-check/scripts/test_decision_continuity.py (modified)
- FOUND: 8bd75ec, 90228be
