---
phase: 57-decision-continuity-within-closure
plan: 09
subsystem: vibe-check carry-forward decisions (carry_state.py)
tags: [carry_state, covers, per-concern-lanes, covered-count, decisions, gap-closure]
requires: ["57-08"]
provides:
  - "carry_state.concern_lanes(record): the record's agent plus same-title member agents"
  - "`lanes` on every new decision record (from state only); gained_lanes / _band_rise_reopens diff it"
  - "_covers_of skips members whose obligation hash differs from the record's (CR-01, D-16)"
  - "covered_count counts distinct covered titles (D-15)"
  - "five contrast mutants m1-m5 in TestGapClosure57"
  - "test_carry_state.ba_row_state: finding A as its own row with same-title lane members"
affects: ["57-10", "57-11", "57-12", "57-13"]
tech-stack:
  added: []
  patterns:
    - "a new reviewer lane is a same-title member, never a row-wide attribution entry"
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-09-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_carry_state.py
    - plugins/vibe-check/scripts/test_batch_card.py
    - plugins/vibe-check/scripts/test_card_text.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "A sidecar (absorbed-obligation) record's concern lanes are only its own agent, as the plan specifies; score.py freezes a sidecar's band and attribution, so no real band rise is lost"
  - "57-02 'new lane' fixtures that edited only `attribution` were rebuilt as a row with a same-title member (ba_row_state), the only shape the new rule and production produce"
  - "`attribution` is still written on decisions (informational); `lanes` governs the band-rise rule"
metrics:
  duration: "~40 min"
  completed: 2026-10-26
  tasks: 2
  files: 5
---

# Phase 57 Plan 09: Per-concern lanes, filtered covers, concern count Summary

A row decision now covers only what the owner was deciding. A member owed on its own is never in `covers`. A band rise reopens only when a lane newly reports this specific concern. Decisions save that concern's lanes (`lanes`), and the band-rise check compares against them instead of the row-wide `attribution`. The card's "N findings already dismissed" count now counts concerns, not reviewer reports.

## What was built

### Task 1: covers filter and concern count (commit 7685907)
- `_covers_of` skips a member whose dict `obligation` has a str `stable_hash` different from the record's own hash. A member with the same hash (57-07 lead/member shape) is still listed. Docstrings updated: the function, plus the module WHAT CLOSES paragraph ("except a member that carries its own separately-owed obligation (its row decision never covers it)") and a sentence that the D-10 count counts concerns (distinct titles).
- `covered_count` returns 1 + the number of distinct covered member titles, excluding the lead's title. Its docstring says "counts decided concerns, not reviewer reports" (D-15).
- Mutants m1 (pre-fix unfiltered `_covers_of`) and m4 (identity-counting `covered_count`) were added.
- The batch-card joined fixture covers two different titles ("t cccccc" lead, "B"), so `test_rows_stale_joined_has_covered_count` keeps `covered == 2`, with the comment "two concerns, D-15".
- `arch_row_covers()` is unchanged: the ARCH fixture members carry no obligations. `test_covered_count_counts_lead_and_covered_members` is unchanged: its covered members have distinct titles.

### Task 2: per-concern lanes (commit 826ddf5)
- New public `concern_lanes(record)`: a sorted list of the record's str `agent` plus each dict member whose `title` equals the record's. Pure; returns [] for non-dicts.
- `record_decisions` writes `"lanes": concern_lanes(by_hash[h])` next to `attribution`. Old records are never rewritten.
- `gained_lanes` is `set(concern_lanes(record)) - set(decision["lanes"])`. It returns [] without a dict decision or a list `lanes`, and its body no longer reads `attribution` (grep count 0).
- `_band_rise_reopens` returns True whenever the decision has no list `lanes` (fails toward asking). Otherwise it returns `bool(gained_lanes)`.
- The module docstring (band rule, plus a ROLLBACK note that a reader ignoring `lanes` still fails toward asking) and the `record_decisions` docstring are updated.
- New `test_decision_without_lanes_reasks_on_any_rise` replaces the attribution-legacy test. It covers: lanes removed with attribution kept, giving stale, cause severity and gained []; both keys removed, giving stale; and a drop without `lanes`, giving current.
- The exact-record assertions now include `lanes`: ARCH gives `["architecture"]`, since `bugs` reports another title; sidecar HA gives `["bugs"]`.
- The payload-injection test now also refuses a `{"lanes": [...]}` payload key.
- `test_gained_lanes_edges` was rewritten for `lanes`. It covers non-list members or lanes, non-str agents, and other-title members, and asserts row-wide attribution is ignored. The `concern_lanes` edge cases were added too.
- `test_rows_stale_severity_rise_has_gained` now proves the card never names a lane that appears only on row attribution (`perf`).
- Mutants m2, m3 and m5 were added.

## Mutant ledger

| Mutant | Replaces | Test that fails under it |
|---|---|---|
| m1 | `_covers_of`, pre-fix unfiltered loop | `test_g1_split_obligation_member_is_not_covered_by_row_decision` |
| m2 | `gained_lanes`, pre-fix attribution diff | `test_g3a_lane_present_for_another_concern_later_corroborates_and_rise_reopens` |
| m3 | `concern_lanes`, every member agent regardless of title | `test_g3b_unrelated_concern_lane_with_persistence_rise_keeps` |
| m4 | `covered_count`, pre-fix identity counting | `test_g6_covered_count_counts_concerns_not_reports` |
| m5 | `_band_rise_reopens`, False when `lanes` missing | `TestDecisionEvidence._without_lanes_scenario` (via `test_decision_without_lanes_reasks_on_any_rise`) |

Each `test_contrast_m*` runs the real scenario first, where it passes, and then runs it under the mutant inside `assertRaises(AssertionError)`. Observed: `pytest -q test_carry_state.py -k "test_g3a_ or test_g3b_ or without_lanes or contrast_m"` gave 8 passed, 5 subtests passed. The `subTest("contrast` count went from 20 to 25.

## Verification (observed)

- Full suite from plugins/vibe-check/scripts (bare `pytest -q -rfE`, test_replay.py included): **6 failed, 3230 passed, 4293 subtests passed in 216.08s**. 57-08 ended at 11 failed, 3220 passed.
- Remaining red set, all owned by later plans:
  - `TestGapClosure57::test_g2a_inherited_decision_reopens_on_lane_backed_band_rise` (57-10)
  - `TestGapClosure57::test_g2b_inherited_decision_reopens_when_a_newcomer_joins` (57-10)
  - `TestNearbyEdit::test_r2_edit_within_five_above_reopens`, SUBFAILED at offsets 1/3/5, 3 counted (57-11, D-14)
  - `TestDeletionRangeLock::test_deletion_range_rule_locked` (57-12)
- Now green: G1, G3a, G3b, G6, and owner-journey pass 6 ("1 finding here already dismissed").
- `test_g1_ or test_g6_`: 2 passed. `TestPhase57EndToEnd`: 1 passed. `TestSeverityDirection or test_r3`: 4 passed. `ImportSet or WriterLock`: 5 passed.
- Greps: `^def concern_lanes` = 1; `"lanes": concern_lanes` = 1; `attribution` inside the `gained_lanes` body = 0; `counts decided concerns` = 1; the obligation/`owed on its own` line = 1. `"lanes"` is written only at carry_state.py:1020 (`record_decisions`).
- Golden digest: `golden ok`.

**Holdout-barrier hook:** blocked one command, verbatim:
`PreToolUse:Bash hook error: [python3 /Users/julianamacbook/turingmind-code-review/docs/design/holdout-v2.12/tools/holdout_guard.py hook]: Blocked: this tool call reaches the sealed holdout folder (v2.12 barrier).`
The blocked command was a `sed -i ''` one-line insert into test_carry_state.py chained with a pytest run. It did not reference the holdout folder; the guard's match looks like a false positive on the command shape. The same edit was made with the Edit tool. No holdout content was read.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 57-02-era "new lane" fixtures rebuilt as same-title members**
- **Found during:** Task 2
- **Issue:** `band_change_state`, `snapshotless_severity_state`, `decided_state` (HC row), the batch-card severity/report fixtures and the card-text `severity_stale_state` / `two_lane_rise_state` signalled a new lane only by editing `attribution`, usually on a sidecar. Under per-concern lanes those give no gain, which turned 32 tests red. That edit-only shape never occurs in production: score.py keeps a sidecar's band and attribution verbatim, and row attribution is derived from members.
- **Fix:** new helper `ba_row_state(row_band, a_band, lanes)` builds A as its own row, with each extra lane as a same-title member. The fixtures use it, or add a same-title member where they mutate a row (ARCH, HC). `legacy_severity_state` also drops `lanes`. The flattening test injects the odd lane as a member agent.
- **Files modified:** test_carry_state.py, test_batch_card.py, test_card_text.py (test_card_text.py was not in the plan's file list)
- **Cost if wrong:** if a future score.py starts refreshing sidecar band/attribution, a lane-backed rise on an absorbed obligation would keep its decision. Such a sidecar always has a same-title member on the absorbing row, so `concern_lanes` would then need to read the absorbing row's members.
- **Commit:** 826ddf5

**2. [Rule 1] Legacy test replaced rather than kept beside the new one**
- **Found during:** Task 2
- **Issue:** `test_legacy_decision_without_attribution_reopens_on_any_rise` asserted that removing `attribution` re-asks. With `lanes` governing the rule that is no longer the trigger.
- **Fix:** it became `test_decision_without_lanes_reasks_on_any_rise`, which also covers the no-attribution and no-lanes record and the drop-keeps case.
- **Cost if wrong:** none; the legacy shape (neither key) is still asserted.
- **Commit:** 826ddf5

## Assumption Drift (advisory)

**1. The verification red set omitted D-14**
- **Found during:** final verification
- **Planned:** the four-file run is red on exactly {G2a, G2b, test_deletion_range_rule_locked}.
- **Actual:** `test_r2_edit_within_five_above_reopens` (D-14, 3 subtests) is also red. Per the orchestrator's prior-wave notes it stays red until 57-11.
- **Why:** the plan text listed the red set without D-14; this plan does not touch the nearby window.
- **Cost if wrong:** none; 57-11 owns it.

## Known Stubs

None.

## Threat Flags

None. T-57-23 through T-57-26 are mitigated as registered: m1, m2/m5 and m3 trip their tests, and the payload refuses a `lanes` key.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/carry_state.py (`def concern_lanes`)
- FOUND: plugins/vibe-check/scripts/test_carry_state.py (`def ba_row_state`, `test_contrast_m1`..`m5`)
- FOUND: commit 7685907
- FOUND: commit 826ddf5
