---
phase: 57-decision-continuity-within-closure
plan: 04
subsystem: vibe-check scorer (score.py)
tags: [score, nearby-window, snapshot, member-dedup, obligation]
requires:
  - "57-02: carry_state compares snapshot.nearby_at (the comparator this plan feeds)"
  - "57-01: R2 / R5 fixtures in test_decision_continuity.py"
provides:
  - "score._nearby_changed: the one nearby window (pinned line + 5 beneath), shared by _independent_trigger and the reopen stamp"
  - "snapshot.nearby_at stamped by survivor, kept-open row and obligation-member snapshot writers; carried forward on keep and refresh branches"
  - "obligation-preserving member dedup (Phase 46 residual 1 closed)"
affects: [57-05, 57-06, 57-07]
tech-stack:
  added: []
  patterns:
    - "nearby stamp only on a row that arrives with a prior snapshot (existed before this pass); a fresh finding is never stamped"
    - "source-text mutants run a scenario function against the mutated module and expect AssertionError"
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/scripts/test_carry_state.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "nearby_at is stamped only on a row that existed before this pass (arrives with a prior snapshot): the change a finding is first raised on is the code it is about, not a change since"
  - "Needs-verification rows and synthetic audit rows pass nearby=False: an NV decision compares its own code fingerprint, never nearby_at; audit rows are never decided"
  - "Fixtures that model 'HEAD unchanged' get an empty incremental diff (changed_line_ranges={}); a non-empty range at the pinned window is a nearby change and now rightly re-stamps"
metrics:
  duration: "~20 min"
  completed: 2026-10-26
  tasks: 2
  files: 4
---

# Phase 57 Plan 04: Nearby-change stamp and obligation-preserving dedup Summary

The scorer now stamps `snapshot.nearby_at` when an edit lands on a flagged line, or in the 5 lines beneath it, after that finding was raised. The stamp uses the same window that Phase 56 uses to trigger a re-check, and it is carried forward on later quiet passes. Member dedup also no longer loses a carried record's obligation when a fresh duplicate out-ranks it inside a row led by a third finding.

**For the owner, in plain terms:** if code right next to a finding you already decided changes, the finding comes back to you once, and it stays decided after that until something changes again. An edit elsewhere in the file does not bring it back. And if a reviewer re-reports a finding you decided while a different finding leads the group, your decision is no longer silently lost.

## What was built

- **`_nearby_changed(record, changed_line_ranges)`**: the last part of `_independent_trigger`, split out. `_independent_trigger` now ends with `return _nearby_changed(record, changed_line_ranges)`, and its behaviour is unchanged (pinned by a table test and by `test_verified_fixes.py`, 87 passed). The comment on `_NEARBY_LINES` records that the reopen stamp shares this window.
- **`_snapshot_for(row, pass_number, nearby=False)`**:
  - On a row that arrives with a prior snapshot, `nearby=True` writes a fresh snapshot with `nearby_at = at_pass`.
  - Otherwise, a prior `nearby_at` is copied forward on both the keep branch and the refresh branch. A row that never had a stamp stays without one.
- **All three writers pass the flag:**
  - the survivor, for its own line
  - `_kept_open_rows`, which gains a `changed_line_ranges` parameter, for the row's line
  - `_refreshed_obligation`, which gains `changed_line_ranges`, for the member's own line rather than the lead's

  Needs-verification rows and audit rows pass `nearby=False` explicitly. Every `_snapshot_for(` call names `nearby=` (grep: 6 of 6, counting the def).
- **Ingress scrub:** no code change. `snapshot` is still stripped, which now also drops a forged `nearby_at`. A comment says so.
- **Member dedup:** `kept_by_ident` maps each kept occurrence identity to its member ref. When a later member with the same identity is a carried record with an obligation, the obligation is attached to the kept ref, using a snapshot refreshed for this pass. Two exceptions: it is never attached to the lead's own ref, and never when the obligation's hash is the row's own hash.

## Mutant ledger (TestPhase57Mutants, test_score.py)

Every target string is asserted to occur exactly once in score.py. Each mutant was observed to make its scenario raise AssertionError, while the real scorer passes the same scenario.

| Mutant | Change | Scenario that fails |
|---|---|---|
| m57-01 | stamp `cur["nearby_at"] = cur["at_pass"]` removed | survivor stamp (`_na_survivor_stamp`) |
| m57-02 | keep-branch carry removed | quiet pass 3 keep (`_na_keep_carry`) |
| m57-03 | refresh-branch carry removed | band-moved quiet pass 3 (`_na_refresh_carry`) |
| m57-04 | kept-open row passes `nearby=False` | kept-open stamp (`_na_kept_open`) |
| m57-05 | obligation passes `nearby=False` | member-line stamp (`_na_obligation`) |
| m57-06 | `"snapshot"` dropped from the ingress scrub | forged `nearby_at` (`_na_forge`) |
| m57-07 | dedup obligation attach removed | carried obligation kept (`_od_check`) |

## Verification (observed)

- Task 1 verify:
  - `test_score.py -k "TestNearbyAt or TestPhase57Mutants or ImportSet or Golden"`: 26 passed, 20 subtests
  - `test_verified_fixes.py`: 87 passed, which includes TestReviewFix56 and the m10-m13 mutants. The m12 target is still unique.
  - `test_decision_continuity.py -k TestNearbyEdit`: 4 passed (offsets 1/3/5 reopen with cause `nearby`; 6 beneath and 2 above keep; a quiet pass carries `nearby_at == 2`)
- Task 2 verify:
  - `-k "TestObligationPreservingDedup or TestPhase57Mutants or ImportSet"`: 14 passed
  - `-k test_r5`: 1 passed, card assertions included
- Golden digest and import set: `TestImportSet` is green, and `stable_hash("a.py", "  x=1", "title") == GOLDEN_DIGEST` holds in both new classes.
- Full suite: every `test_*.py` except `test_calibrate.py` / `test_replay.py`, which the holdout-barrier hook blocks. Result: **3090 passed, 7 failed**, 4176 subtests passed. All 7 failures are in `test_decision_continuity.py` and are card wording owned by 57-06:
  - `test_r3a_rise_with_new_lane_reopens_and_names_it` (card `gained`)
  - `test_compact_forms_fit_budget` (3 subtests: nearby / severity / joined)
  - `test_joined_card_wording_d10`
  - `test_nearby_card_wording`
  - `test_r7_rise_card_names_the_new_lane`

  This was 12 failed after 57-03. R2 (4 fixtures) and R5 are now green.
- Replay at the final code commit 273a1e4:
  - `replay.py candidate --name phase57-04 --scorer rev:HEAD`: **REGRESSED 0**, UNEVALUABLE 0 (kept 25 / protected 26; AMENDED 1, which predates this plan)
  - `replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ALLOWANCES-phase53-nv.json`: 170 runs compared, **runs differing 0**, allowed 0, unallowed 0
  - No allowance edits.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 04e2c65 | `_nearby_changed`, nearby_at through all snapshot writers, TestNearbyAt, m57-01..06 |
| 2 | 273a1e4 | obligation-preserving member dedup, TestObligationPreservingDedup, m57-07, R5 fixture input |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stamp only rows that existed before this pass**
- **Found during:** Task 1
- **Issue:** Read literally, the plan ("stamp when the window intersects this pass's ranges") would stamp `nearby_at = 1` on every pass-1 finding, because a finding is raised on changed lines. The decision would then carry that stamp forever. `test_r2_edit_six_beneath_keeps` (57-01) asserts that a pass-1 row has no `nearby_at`.
- **Fix:** `nearby` stamps only when the row arrives with a prior snapshot. That covers carried leads, kept-open rows (from the obligation snapshot) and obligation sidecars. A fresh finding has its snapshot scrubbed at ingress, so it is never stamped.
- **Cost if wrong:** a carried record that has no prior snapshot (legacy, pre-46 state) gets its first snapshot without a stamp, so one nearby edit on that first carried pass is not seen. Such records' decisions predate evidence binding and already read as "current".
- **Commit:** 04e2c65

**2. [Rule 1 - Test inputs] Fixtures that modelled "HEAD unchanged" with non-empty change ranges**
- **Found during:** Task 1 and Task 2
- **Issue:** Several earlier fixtures re-sent the pass-1 change ranges on later passes even though the code was unchanged. Under the new stamp, that input is a nearby edit, so their snapshot or pending expectations changed:
  - TestSnapshot keep tests
  - TestKeptOpenMembers sidecar tests
  - TestKeptOpenMultiPass min-confidence test
  - test_carry_state TestPhase45EndToEnd: three tests
  - the 57-01 R5 fixture, which sent `{F: [[1, 200]]}` on unchanged code, so its decided row read `stale` with cause `nearby`
- **Fix:** where the scenario is "code unchanged", the later pass gets `changed_line_ranges={}`. In those tests the realistic incremental diff is empty and scoring does not affect the assertion. Where the change is real (B's new line 11 lands inside A's window), the expectation now names the stamp: `nearby_at == 2`, and `pending == []` for A at pass 2.
- **R5 fixture:** C still leads. Its self-check band is now `warning` (it was `critical`, which came from the whole-file in-diff bonus). I added an assertion that the fresh duplicate and the carried A share one occurrence identity.
- **Cost if wrong:** if the owner wants a decided row that regroups to keep its decision even when the same pass edits beside it, that conflicts with D-02 and would need a decision. Today D-02 wins.
- **Commits:** 04e2c65, 273a1e4

**3. [Rule 2 - Correctness] NV and audit snapshot writers pass `nearby=False` explicitly**
- **Found during:** Task 1
- **Issue:** The plan named three writers. Two more `_snapshot_for` call sites exist: the Needs-verification rows and the synthetic suppression audit rows.
- **Fix:** both pass `nearby=False`, with a comment. NV decisions compare `_NV_EVIDENCE_KEYS`, which never include `nearby_at`, and audit rows are regenerated every pass and never decided. This keeps replay output unchanged (runs differing 0).
- **Cost if wrong:** if NV decisions should later re-ask on a nearby edit, both the writer and `_NV_EVIDENCE_KEYS` need to change together.
- **Commit:** 04e2c65

**4. [Rule 2 - Coverage] Extra tests**
- `test_survivor_window_edges` (lines 11/13/15 stamp; 16/8/9 do not)
- a cross-file case in `test_survivor_no_stamp_outside_window`
- `test_fresh_finding_cannot_forge_nearby_at`, run both with and without a window hit
- **Cost if wrong:** none. These are test-only additions.

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** the stamp fires whenever the window intersects this pass's ranges. **Actual:** it fires only for a row that existed before this pass. **Why:** a finding's own first-pass diff is not "a change since it was raised". **Cost if wrong:** see Deviation 1.

## Known Stubs

None.

## Threat Flags

None. No new surface: `nearby_at` lives inside `snapshot`, which the ingress scrub already strips (T-57-11, mutant m57-06).

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py (`def _nearby_changed`: 1)
- FOUND: plugins/vibe-check/scripts/test_score.py (`class TestNearbyAt`, `class TestObligationPreservingDedup`, `class TestPhase57Mutants`)
- FOUND: commit 04e2c65
- FOUND: commit 273a1e4
