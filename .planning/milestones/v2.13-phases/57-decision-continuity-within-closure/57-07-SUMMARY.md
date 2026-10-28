---
phase: 57-decision-continuity-within-closure
plan: 07
subsystem: vibe-check carry-forward decisions (score.py / carry_state.py / batch_card.py / review prose), phase gate
tags: [phase-gate, replay, mutants, ledger, end-to-end]
requires: ["57-01", "57-02", "57-03", "57-04", "57-05", "57-06"]
provides:
  - "test_decision_continuity.py: TestCrossModuleGuards, TestPhase57EndToEnd (7-pass owner journey), TestSameHashLeadKeepsNearbyStamp, TestPhase57Mutants; the repro pin retired as the fail-closed binding rationale"
  - "score.py: a fresh same-hash lead keeps the absorbed carried record's snapshot (nearby_at survives a change of lead)"
  - "Phase 57 gate numbers: suite 3216/0, replay REGRESSED 0, diff runs differing 0, golden unchanged"
affects: ["/bm:verify-work 57", "Phase 58"]
tech-stack:
  added: []
  patterns:
    - "ledger proof by reverse run: the final fixture file run against the 57-01-era production code must fail the same assertions"
    - "test-method mutant check: run another TestCase under mock.patch and assert exactly which subTest fails"
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-07-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/score.py
    - .planning/STATE.md
    - .planning/phases/57-decision-continuity-within-closure/deferred-items.md
decisions:
  - "Rule 1 fix in score.py (outside the plan's file list): a fresh lead whose hash equals an absorbed carried record's takes that record's stored snapshot as prior; without it an owed nearby re-ask vanished (gate wrote) or the card named the wrong cause"
  - "No new replay allowances file: replay diff showed 0 differing runs, so ALLOWANCES-phase57-nearby.json was not created"
  - "End-to-end journey uses STABLE_CONF 75, not the plan's conf 70 (57-01 measured 70 as band-unstable)"
  - "Pass-6 D-10 note asserted as '2 findings here already dismissed': the decision covered two lane records (bugs, security) of the same concern; surfaced to the owner as a design call"
metrics:
  duration: "~55 min"
  completed: 2026-10-26
  tasks: 2
  files: 4
---

# Phase 57 Plan 07: Phase gate, ledger and owner journey Summary

Every reproduced decision-loss path from 57-01 is now green, proven by the same fixtures that reproduced it. A seven-pass owner journey checks that the owner is asked exactly when the evidence changes. The journey found one more silent-loss bug, which is now fixed: when a second reviewer took over a row's lead, the record of a nearby edit was lost. All Phase 57 gates are green.

## What was built

- **Repro pin retired.** It is renamed `test_without_decided_hashes_the_decision_is_lost_so_binding_must_not_degrade` and keeps the "lost without relocation" assertions. It now explains why 05-state.md halts instead of binding an empty `$DECIDED_HASHES`. The source carries a retirement comment.
- **`TestCrossModuleGuards`** (4 tests):
  - `_BAND_RANK` equals `_BAND_SEVERITY` minus `None`.
  - Simulator/prose split. The simulator docstring now says that moving the `$RECHECK_REQUESTS` line is the prose's job. Every `DECIDED_RELOCATION_PHRASES` entry is checked inside the decided paragraph of the shipped 30-collect-score.md, and `decided_relocation_holds` is checked on the whole file.
  - `decided` equals {records whose decision is current} for the R1a and R6 states. The R6 state includes an inherited member that has no decision of its own.
  - `_nearby_changed` agrees with `_independent_trigger(rec, set(), ranges)` on 20 pairs, and exactly 9 of them hit.
- **`TestPhase57EndToEnd.test_owner_is_asked_exactly_when_evidence_changes`.** Each pass is checked with `e2e_gate`, the card rows and `_assert_band`:
  - **Pass 1:** dismiss, then the gate writes.
  - **Pass 2:** 3 lines are inserted above. The finding moves to line 13 with the same hash, the owner is not asked, and the gate writes.
  - **Pass 3:** line 14 is edited. The owner is asked with cause `nearby` and the card says `code next to it changed since your decision on pass 1`. The owner dismisses again.
  - **Pass 4:** a quiet pass. The owner is not asked and `nearby_at == 3` is carried.
  - **Pass 5:** `security` reports the same finding and the band rises warning → critical. The owner is asked with cause `severity`, `gained == ["security"]`, and the card says `security now also reports it`. The owner dismisses.
  - **Pass 6:** a `compliance` concern is absorbed into the row. The owner is asked with cause `joined` and the D-10 note. The owner dismisses the row, and `covers` now includes compliance.
  - **Pass 7:** line 13 is rewritten and both lanes answer their re-check `resolved`. Compliance becomes a row of its own, inherits the row decision through `covering_decision`, is not asked, and the gate writes.
  - Run time: the whole module runs in 0.08s.
- **`TestSameHashLeadKeepsNearbyStamp`:** a regression test for the bug below.
- **`TestPhase57Mutants`:**
  - (a) `carry_state.decided` patched to return `[]`: the journey's pass 2 no longer relocates. The row is pinned at line 10 and the decision is no longer current at line 13.
  - (b) A source mutant drops the `+ 1` upper bound of `_nearby_changed`. Running `TestNearbyEdit.test_r2_edit_within_five_beneath_reopens` under it fails exactly one subTest, `offset=5`, and the same test passes on the real code.

## Red/green ledger

GREEN plan = the earliest phase commit at which the final fixture file passes for that path. I found it by running the final `test_decision_continuity.py` against archived production trees at each plan's last code commit.

| path | fixture(s) | RED at 57-01 (reason) | GREEN at |
|------|-----------|------------------------|----------|
| R1a | `test_r1a_shift_above_threshold_keeps_decision_and_hash` | stored-line read re-hashed the row; decision orphaned | 57-02 (72eee65; scorer/state side, with 57-05 shipping the relocation prose the simulator models) |
| R1b | `test_r1b_shift_sub_threshold_keeps_decision` | kept-open row `stale` (cause `code`) | 57-02 |
| R1c | `test_r1c_shift_with_rereport_is_one_decided_row` | re-reported row `stale`; phantom row at line 10 | 57-02 |
| R2 | `test_r2_edit_within_five_beneath_reopens` (1/3/5), `test_nearby_at_carries_forward_on_quiet_pass` | decision wrongly kept; `nearby_at` missing | 57-04 (273a1e4) |
| R3a-refined | `test_r3a_persistence_rise_without_new_lane_keeps`, `test_r3_decision_record_saves_attribution`, `test_r3a_rise_with_new_lane_reopens_and_names_it` | persistence rise reopened; `gained_lanes` / `attribution` missing | 57-02 (persistence keeps, attribution saved); rise-with-new-lane fully green at 57-06 (52de114: card `stale.gained`) |
| R3b | `test_r3b_band_drop_keeps_decision` (dismiss, defer) | band drop reopened | 57-02 |
| R4 | `test_r4_new_weaker_concern_on_decided_row_is_asked`, `test_r4_covers_frozen_at_decision_time` | newcomer silently covered (gate wrote); `covers` missing | 57-03 (0bb69d3) |
| R5 | `test_r5_fresh_duplicate_outranking_decided_record_keeps_its_obligation` | dedup dropped the carried obligation; decision orphaned | 57-04 (273a1e4) |
| R6 | `test_r6_split_member_inherits_decision` | split member asked as brand new | 57-03 (0bb69d3) |
| R7 | `test_r7_rise_card_names_the_new_lane`, `test_nearby_card_wording`, `test_joined_card_wording_d10`, `test_compact_forms_fit_budget` (3) | card had no lane / no row | 57-06 (52de114) |

**No reproduction was weakened. I checked this observationally:**
- I ran the final `test_decision_continuity.py` against the production tree at af1c69b (57-01). It produced the same 22 failures as 57-01's red-run tail, line for line, with `22 failed, 16 passed, 10 subtests passed`.
- `git diff -U0 af1c69b -- test_decision_continuity.py | grep '^-.*assert'` lists one line: `-        self._assert_band(s2, hC, "critical")`. That is 57-04's R5 edit (the band of C, the competing lead, moved to `warning` once pass 2's diff became empty). It is a fixture-shape assertion, not the R5 obligation assertion.
- I ran the edited R5 fixture against score.py at 04e2c65 (just before 57-04's dedup fix) and at af1c69b. Both fail with `record dee0f534 is not an open record (decision orphaned)`, the original R5 reason, so 57-04's input edit did not weaken the reproduction.
- The retired pin's body removed no assert line: its two original assertions are kept verbatim, and two more were added.
- 57-02's flipped line-move tests live in test_carry_state.py. They were not 57-01 fixtures, so the no-weakening rule above does not apply to them.

**57-04 regression caught late:** 57-04 changed the `changed_line_ranges` argument on the member-append line in score.py. That moved the anchor of the `"member"` mutant in `test_replay._MUTANTS`. Waves 2-3 never saw the failure because the holdout-barrier hook did not run test_replay.py in those waves. The orchestrator re-anchored it in 62d901c (deferred-items.md, RESOLVED). This plan's score.py fix keeps the re-anchored lines byte-identical; test_replay passes.

## Did not reproduce

`DID_NOT_REPRODUCE` in test_decision_continuity.py lists N1-N6 as `did not reproduce; dropped — no code change`. It also lists title-drift (excluded by ROADMAP) and real-data (no real case; fixtures are synthetic). The six green pins `TestDidNotReproducePins::test_n1..n6` and `test_did_not_reproduce_record_is_complete` all pass at HEAD.

## Gates

Run from `plugins/vibe-check/scripts` at 387e2bb (final code commit). The holdout-barrier hook did not block any command.

- `pytest -q` (full suite):
  ```
  3216 passed, 4278 subtests passed in 161.00s (0:02:40)
  ```
  Phase 56 close was 3083, so Phase 57 added 133 tests (57-01..57-06 brought the suite to 3208; 57-07 added 8). 0 failed.
- Golden: `golden ok` (`score.stable_hash("a.py","  x=1","title") == test_score.GOLDEN_DIGEST`).
- Import sets: `pytest -q test_score.py -k ImportSet` gave `3 passed, 495 deselected in 0.08s`; `pytest -q test_carry_state.py -k ImportSet` gave `3 passed, 194 deselected in 0.05s`.
- `pytest -q test_verified_fixes.py`: `87 passed, 102 subtests passed in 0.24s`.
- `python3 replay.py candidate --name phase57-gate --scorer rev:HEAD --out $SCRATCHPAD/phase57-candidate.md` (rc=0):
  ```
  kept 25 / protected 26

  REGRESSED 0

  UNEVALUABLE 0

  AMENDED 1

  ## FP prediction — headline quiet set (Phase-38 should-quiet-1..6 ×3)

  baseline **16/18** → candidate **14/18**
  ```
  AMENDED 1 (`triggarr-secret-in-logs/run-2`) predates this phase. 57-04 recorded the same amendment.
- `python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SCRATCHPAD/phase57-diff.md` (rc=0):
  ```
  - runs compared: 170
  - runs differing: 0
  - runs differing (allowed): 0
  - runs with unallowed differences: 0
  - allowances unused: 65
  - head: 387e2bbeb2ccfaa075bdab0c28f550418e81320b
  ## Differences
  - none
  ```
  Nothing differed, so no `ALLOWANCES-phase57-nearby.json` was created (T-57-20: nothing allowed).

## Design calls surfaced to the owner

These are plain-terms choices the phase made. Each matches the locked decisions; they are listed so you can disagree.

1. **When a second reviewer reports the same concern, you are asked again only if its severity rose** (D-05 as refined). If another reviewer agrees with a finding you dismissed, and that agreement does not push it into a higher severity band, your decision stands and you are not asked. On pass 5 of the journey, `security` agreeing pushed the finding from warning to critical, so you were asked, and the card named `security`.
2. **Your decision on a row covers every finding that was on the row when you decided** (D-09 as written, Research Q4). If such a finding later becomes a row of its own and its code has not changed, it keeps your decision without asking. Pass 7 shows this for the compliance concern. A finding whose own line changed is asked again.
3. **Relocation applies to decided findings only.** Findings you have decided follow their code when lines shift. Undecided findings are still read at their stored line number, which can produce a "phantom" row of whatever code now sits there (seen in R1a/R1c). The general version is carried, not built (STATE.md Deferred Items).
4. **New, from the journey: the "already dismissed" count counts reviewers, not concerns.** After `security` and `bugs` both reported the same finding, the pass-6 note reads "**2** findings here already dismissed", although it is one concern reported twice. The plan's example said "1 finding". The count is 57-06's `covered_count`, which counts one per reviewer record. Changing it is wording only (no finding is lost), so it falls outside the scope rule and is left for you to decide.

The rule that a newcomer concern reopens the whole row is not a design call. It is your D-08 refinement of 2026-10-26, and the journey's pass 6 exercises it.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 (Rule 1 fix) | ea3dab1 | fix(57-07): keep an owed nearby re-ask when another lane takes the lead |
| 1 | 387e2bb | test(57-07): close the ledger with cross-module guards and the owner journey |
| 2 | (docs commit) | STATE.md, SUMMARY, deferred-items.md |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A fresh same-hash lead dropped the row's `nearby_at` stamp (silent finding loss)**
- **Found during:** Task 1, while building the end-to-end journey at pass 5.
- **Issue:** a second lane re-reported a decided finding on the same code, which gives the same `stable_hash`, and out-scored the carried row. It became the lead with a fresh snapshot, and the carried record's `nearby_at` was dropped. In the journey this made the card say "code next to it changed" instead of "severity rose … security now also reports it". A probe with the owner not yet answering a nearby re-ask showed worse: with security at confidence 95 or 100 (warning band, no rise), the decision went back to `current` and the gate returned `write`, so the owed re-ask disappeared. Confidence 75-90 kept bugs as lead and was unaffected.
- **Fix:** in score.py's member loop, if the survivor is fresh and an absorbed carried record's obligation has the survivor's own hash, that obligation's stored snapshot becomes the survivor's prior snapshot. `_snapshot_for` then carries `nearby_at`, and the older `at_pass` when the evidence is equal. The check sits before `_refreshed_obligation`, so the re-anchored test_replay `"member"` mutant lines stay byte-identical.
- **Evidence:** before the fix, the new `TestSameHashLeadKeepsNearbyStamp` failed (`None != 2`) and the journey failed (`None != 3`); after it, both pass. Replay diff was 0 runs differing, and REGRESSED 0.
- **Cost if wrong:** if a same-hash fresh lead should start a clean snapshot, an owner could be re-asked once more than intended after a nearby edit. That errs toward asking, never toward silent closure.
- **Files modified:** plugins/vibe-check/scripts/score.py
- **Commit:** ea3dab1

**2. [Rule 3 - Blocking] Pass-7 re-check needs one request per lane**
- **Found during:** Task 1, journey pass 7.
- **Issue:** after pass 5 the row holds `security` (lead) and `bugs` (member obligation with the same hash). A hash-bearing request reaches only the lead (`_request_matches`). With a security-only request, bugs' rewritten line came back as a successor row asked with "code changed", so compliance never stood alone.
- **Fix:** pass 7 sends the security request with the hash and a hash-less request for bugs, and both answer `resolved`. Compliance (confidence 55, chosen so it is absorbed on pass 6 yet stays above threshold alone on pass 7) then splits out and inherits. I logged the shared-hash shape in deferred-items.md.
- **Cost if wrong:** the journey models a re-check in which both lanes were asked. If the orchestrator asks only the lead's lane, the bugs record is asked again as changed code. That errs toward asking.

**3. [Plan count] 38 tests collected, below the plan's ">= 45"**
- The plan's own additions (4 cross-module tests, 1 journey, 2 mutants) bring 30 to 37, and the regression test makes 38. With subtests, pytest reports `38 passed, 53 subtests passed`. I did not add filler tests to reach 45.
- **Cost if wrong:** none for coverage. The number in the plan was arithmetic, not a requirement.

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** journey at "conf 70". **Actual:** `STABLE_CONF = 75`. **Why:** 57-01 measured conf 70 dropping warning → medium on a quiet pass. **Cost if wrong:** none; the band is asserted on every pass.
- **Found during:** Task 1, pass 6. **Planned:** D-10 note `1 finding here already dismissed`. **Actual:** `2 findings here already dismissed`. **Why:** by pass 6 the decision covered two reviewer records of one concern, and `covered_count` counts per reviewer. **Cost if wrong:** wording only; surfaced as design call 4.
- **Found during:** Task 1, pass 6. **Observed:** the reopened row also shows the existing "unchanged since pass 5, decision pending" suffix before the joined note. This is pre-existing `pending` behaviour; I logged it in deferred-items.md and did not change it.

## Known Stubs

None. The getattr sentinels from 57-01 are still in the module; every name they guard now exists.

## Threat Flags

None. T-57-20: I added no allowances because nothing differed. T-57-21: the removed-assert list is above and contains only 57-04's C-band shape line, re-verified.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (classes TestCrossModuleGuards, TestPhase57EndToEnd present; grep count 2)
- FOUND: plugins/vibe-check/scripts/score.py (`same_hash_prior`)
- FOUND: ea3dab1, 387e2bb
- FOUND: .planning/STATE.md `General relocation` Deferred Items row
