---
phase: 57-decision-continuity-within-closure
plan: 10
subsystem: vibe-check carry-forward decisions (carry_state.py, batch_card.py)
tags: [carry_state, inheritance, covers, batch_card, reopen-rules, gap-closure]
requires: ["57-09"]
provides:
  - "covers entries carry `band` (row band) and `lanes` (lanes reporting that entry's concern) — six-key entry"
  - "carry_state._covering (hash, decision, entry); covering_decision unchanged; public covering_entry"
  - "carry_state._decision_for: own decision else covering decision + entry; newcomer_lanes / covered_count / gained_lanes read it"
  - "carry_state._inherited_cause / _inherited_state: nearby -> joined -> lane-backed band rise for inherited decisions (CR-02)"
  - "batch_card was_band on the covering path from carry_state.covering_entry"
  - "mutants m6-m8 (test_carry_state), m9 (test_batch_card)"
affects: ["57-11", "57-12", "57-13"]
tech-stack:
  added: []
  patterns:
    - "one ordering function (_inherited_cause) feeds both decision_state and stale_cause on the inherited path"
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/57-10-SUMMARY.md
  modified:
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_carry_state.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/scripts/test_batch_card.py
    - plugins/vibe-check/scripts/test_card_text.py
decisions:
  - "A covers entry's band is the row band for every entry (members carry no band of their own; the row band is the only band the owner saw)"
  - "Legacy covers entry without `band` compares against the covering decision's band; without `lanes` any rise re-asks"
  - "Inherited cause ordering lives in one function (_inherited_cause) read by both decision_state (via _inherited_state) and stale_cause"
  - "The inherited band check reads record['band'] (as planned), not the snapshot band the own-decision path compares"
metrics:
  duration: "~35 min"
  completed: 2026-10-26
  tasks: 2
  files: 6
---

# Phase 57 Plan 10: Inherited decisions reopen by the own-decision rules Summary

A finding that holds a decision because it was covered by another row's decision now reopens under the same rules as a finding with its own decision. Those rules, in order: a change in the code next to it, a new concern joining its row, or a band rise backed by a lane newly reporting the concern. Each `covers` entry now saves the band and the concern's lanes at decision time. The card shows the band that entry saved and names only the lanes that newly report the concern. G2a and G2b (CR-02) are green.

## What was built

### Task 1: band + lanes on covers entries; inherited ordered checks (commit 3e54c8e)
- `_covers_of` entries are now `{agent, file, title, code, band, lanes}`. `band` is the row's `band` for every entry. `lanes` is `concern_lanes(record)` for the record itself. For a member, `lanes` is the sorted agents of every member with that member's title (new helper `_member_lanes`). The docstring explains both choices.
- `covering_decision` is now built on a private `_covering(record, state)`, which returns `(hash, decision, entry)`. Its guards and sorted-hash order are unchanged, and the public signature is unchanged. New public `covering_entry(record, state)`.
- `_decision_for(record, state)` returns `(own decision, None)`, or the covering decision with its entry, or `(None, None)`. `newcomer_lanes`, `covered_count` and `gained_lanes` resolve through it. For an inherited record, `gained_lanes` diffs against the entry's `lanes`.
- `_inherited_cause` runs nearby, then joined (`newcomer_lanes`), then band. The band check compares against the entry's band (`_inherited_was_band`: the entry's `band`, or the decision's band for a legacy entry). An unknown band on either side re-asks. A drop or no change keeps the decision. A rise re-asks when the entry has no list `lanes` or `gained_lanes` is non-empty. `_inherited_state` maps it to stale/current. `decision_state`'s inherited branch calls `_inherited_state`, and `stale_cause`'s inherited branch returns `_inherited_cause`. The old unconditional `return "nearby"` and its comment are gone.
- Docstrings updated: the module "ONE inheritance path" paragraph, `decision_state`, `stale_cause`, `newcomer_lanes`, `covered_count`, `gained_lanes`.
- Tests: G2a and G2b are green. New tests:
  - `test_inherited_covering_entry_is_the_matched_entry`
  - `test_inherited_legacy_entry_without_band_uses_decision_band`: includes a non-vacuity step where a critical decision band absorbs a critical record
  - `test_inherited_legacy_entry_without_lanes_reasks_on_rise`
  - `test_inherited_band_drop_keeps`: a drop keeps the decision even when a new same-title lane reports it
  - `test_inherited_check_order_nearby_before_joined_before_severity`
  - `test_inherited_mutant_helper_is_faithful`
  
  `arch_row_covers()` computes band and lanes from the raw fixture JSON. The exact-record and `set(entry)` assertions now expect the six keys. The m1 mutant now emits the six-key shape, so it still trips on the filter and not on entry shape.

### Task 2: card reads the inherited entry (commit a2a7619)
- `_same_hash_stale`, on `via == "covering"`: `was_band` is `covering_entry(record, state)["band"]` when it is a str, otherwise the covering decision's `band`. It never reads the decided row's `evidence.band`. `grep -c '"covers"' batch_card.py` = 0. `grep -c "carry_state.covering_entry(" batch_card.py` = 1.
- test_batch_card: new `inherited_state("rise" | "joined")` helper, which builds the TestGapClosure57 G2a/G2b shapes. New tests:
  - `test_rows_stale_inherited_severity_rise_tag`: via covering, cause severity, was_band warning, gained [security], prior_hash HR, and the card row's tag is identical
  - `test_rows_stale_inherited_joined_tag`: cause joined, covered 1, joined [security]
  - `test_inherited_was_band_reads_covering_entry_mutant` (m9): the row's evidence band is set to medium and the tag still says warning
- test_card_text: exact strings for the inherited rise suffix are checked in full and compact form:
  - full: " — severity rose (warning → critical) since your decision on pass 1: security now also reports it (was: dismissed — not a bug)"
  - compact: " — severity rose since your decision on pass 1"
- test_card_text: exact strings for the inherited joined note, full and compact:
  - full: " — 1 finding here already dismissed (your reason: not a bug); a new concern from security joined it"
  - compact: the same note without the reason

## Mutant ledger

| ID | Mutant | Trips | Where |
|----|--------|-------|-------|
| m6 | `_inherited_state` returns "current" after nearby/joined (band step skipped) | G2a | test_carry_state TestGapClosure57 |
| m7 | `_inherited_state` skips the joined step | G2b | test_carry_state TestGapClosure57 |
| m8 | entry without list `lanes` treated as no gain | `_legacy_lanes_scenario` | test_carry_state TestGapClosure57 |
| m9a | `covering_entry` -> None | was_band falls back to the decision band ("low") | test_batch_card TestRows |
| m9b | `covering_entry` -> entry with band "low" | tag reports "low" | test_batch_card TestRows |

The m6–m8 mutants come from one parameterised copy of `_inherited_state`. `test_inherited_mutant_helper_is_faithful` runs that copy with no step changed and confirms it reproduces the real results on G2a, G2b, the legacy-lanes case and the drop case. So each mutant differs from the real function by exactly one step. Existing `_covers_entry_matches` contrast mutants still reach `_covering` and pass.

A source-level check was also run, outside the committed tests. The `if via == "covering":` branch in batch_card was disabled in-process, and `test_inherited_was_band_reads_covering_entry_mutant` then failed (1 failure observed).

`subTest("contrast` count in test_carry_state.py: 25 -> 28 (+3).

## Verification (observed)

- `pytest -q test_carry_state.py test_decision_continuity.py`: 3 failed (SUBFAILED offsets 1/3/5 of `test_r2_edit_within_five_above_reopens`, owned by 57-11), 257 passed.
- `pytest -q test_carry_state.py -k "test_g2a_ or test_g2b_ or test_inherited_"`: 9 passed.
- `pytest -q test_carry_state.py -k "TestImportSet or TestWriterLock or TestRollbackQuarantine"`: 11 passed.
- `pytest -q test_batch_card.py test_card_text.py test_finalize_card.py`: 156 passed, 0 failed.
- `pytest -q test_batch_card.py -k inherited`: 4 passed, 2 subtests passed. `pytest -q test_card_text.py -k inherited`: 2 passed.
- `pytest -q test_nv_render.py`: 1 failed (`test_deletion_range_rule_locked`, owned by 57-12).
- Full suite (`pytest -q` from plugins/vibe-check/scripts, which includes test_replay.py with 64 tests collected): **4 failed / 3246 passed**, 4298 subtests passed.
- carry_state import set: `['json', 'os', 'sys']` (unchanged).
- Grep checks: `^def covering_entry` = 1, `^def _decision_for` = 1, `^def _inherited_state` = 1. The old inherited-path comment count in stale_cause is 0. `"lanes"` = 2 and `"band"` = 4 within `_covers_of`.

### Remaining red set (expected, owned elsewhere)
- `test_decision_continuity.py::TestNearbyEdit::test_r2_edit_within_five_above_reopens`, offsets 1, 3, 5 (3 SUBFAILED). Owned by 57-11.
- `test_nv_render.py::TestDeletionRangeLock::test_deletion_range_rule_locked`. Owned by 57-12.

That is exactly the target from the prior-wave notes: 2 tests, 4 failed counts, and no new reds.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] test_decision_continuity.py exact `covers` assertions updated**
- **Found during:** Task 1
- **Issue:** `test_r4_covers_frozen_at_decision_time` and the pass-6 `assertIn` in `test_owner_is_asked_exactly_when_evidence_changes` pinned the four-key entry shape. The file was not in the plan's `files_modified`, but the plan's acceptance requires that module to be green.
- **Fix:** Added the expected `band` and `lanes` values to both assertions: `warning`/`["bugs"]` and `critical`/`["compliance"]`. Pass 7 of the owner journey, where the compliance member splits out and inherits, still keeps the decision. The medium compliance row is at or below the critical entry band.
- **Cost if wrong:** low. These are test expectations of the new writer's output, read from that output.
- **Files modified:** plugins/vibe-check/scripts/test_decision_continuity.py
- **Commit:** 3e54c8e

**2. [Rule 1 - Correctness] One ordering function for inherited causes**
- **Found during:** Task 1
- **Issue:** As planned, `_inherited_state` (stale/current) and `stale_cause` (cause) would each re-implement the nearby/joined/band order, and the two could drift apart.
- **Fix:** Added `_inherited_cause`, which returns the cause or None. `_inherited_state` maps it to stale/current, and `stale_cause` returns it directly. As a result, `grep -c 'return "nearby"' carry_state.py` is 2, not the plan's 1. The second hit is the conditional, ordered inherited cause, which the plan itself asks for. The unconditional return and its comment are gone (sub-check = 0).
- **Cost if wrong:** low. Mutants patch `_inherited_state`, which `decision_state` gates on, so `stale_cause` returns None whenever a mutant says "current".
- **Files modified:** plugins/vibe-check/scripts/carry_state.py
- **Commit:** 3e54c8e

**3. [Rule 2 - Test strength] m1 mutant updated to the six-key entry shape**
- **Found during:** Task 1
- **Issue:** After the shape change, the m1 mutant (unfiltered covers) would trip on missing `band`/`lanes` keys instead of on the filter.
- **Fix:** The mutant now emits the six-key shape, so it trips only on the filter. G1 fails because HB2 inherits through the unfiltered covers.
- **Cost if wrong:** none for production; a test-strength fix only.
- **Commit:** 3e54c8e

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** the inherited band check uses `record.get("band")`. **Actual:** implemented as planned. The own-decision path compares the snapshot band instead (`_evidence_of`). For score.py rows the two are equal, because the snapshot band is written from the row band. **Why:** this follows the plan text. **Cost if wrong:** if a row's band and snapshot band ever diverge, the inherited and own paths could judge one rise differently. Each path still fails toward asking on an unknown band.

## Hook blocks

None. All edits were made with Python edit scripts in the scratchpad or with the Edit tool. No holdout-hook block was hit.

## Threat Flags

None. No new I/O, network or file surface. T-57-27/28/29 are mitigated with mutants m6/m7, m8 and m9.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/carry_state.py (`def covering_entry`, `def _decision_for`, `def _inherited_state`, `def _inherited_cause`)
- FOUND: plugins/vibe-check/scripts/batch_card.py (`carry_state.covering_entry(`)
- FOUND: plugins/vibe-check/scripts/test_carry_state.py (`test_contrast_m6`..`m8`)
- FOUND: plugins/vibe-check/scripts/test_batch_card.py (`test_inherited_was_band_reads_covering_entry_mutant`)
- FOUND: commit 3e54c8e
- FOUND: commit a2a7619
