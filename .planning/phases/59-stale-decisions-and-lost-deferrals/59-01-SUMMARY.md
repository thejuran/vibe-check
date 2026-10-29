---
phase: 59-stale-decisions-and-lost-deferrals
plan: 01
subsystem: vibe-check decision continuity (tests + verdict ledger)
tags: [reproduce-first, real-chain-fixtures, prose-pin, STALE-01, DEFR-01, DEFR-02]
requires: []
provides:
  - "cr01_scenario / cr02_scenario / cr04_scenario real-chain builders"
  - "member_conf knob on deferred_covered_sub_threshold_scenario"
  - "TestStaleDecisions59 (4 red + 2 controls), test_dmc_ (red) / test_dmx_ (control)"
  - "REPRO_59 + TestRepro59Record"
  - "test_nv_render.all_carryforward_bypass_holds pin + deleting mutant"
  - "59-REPRO.md verdict ledger citing RED SHA 82ec58b"
affects: [59-02, 59-03, 59-04, 59-05, 59-06]
tech-stack:
  added: []
  patterns: ["reproduce-first red fixtures committed before any fix", "prose pin + deleting mutant backs a did-not-reproduce claim"]
key-files:
  created:
    - .planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_nv_render.py
decisions:
  - "RED SHA for the 59-06 reverse run is 82ec58b (test files only)"
  - "SA-02 recorded as did not reproduce on the real chain; dropped, backed by all_carryforward_bypass_holds"
metrics:
  duration: "~25 min"
  completed: 2026-10-28
  tasks: 3
  files: 3
requirements: [STALE-01, DEFR-01, DEFR-02]
---

# Phase 59 Plan 01: Reproduction verdicts Summary

Five wrong-keep and lost-deferral shapes (CR-01 edit@33, CR-01 multi-pass, CR-02, CR-04, min_confidence=45 deferred member) are committed as failing real-chain fixtures at RED SHA `82ec58b`, before any production edit. Three controls pass. SA-02 is recorded as "did not reproduce on the real chain; dropped", backed by a green prose pin on `05-state-all.md` with a deleting mutant.

## RED SHA and the exact failure list

RED SHA: **`82ec58b`** (`test(59-01): red real-chain fixtures ...`, the two test files only).

Full suite at `82ec58b` (`cd plugins/vibe-check/scripts && pytest -q`): **5 failed, 3594 passed, 4772 subtests passed in 165.65s**. The five failures:

1. `TestStaleDecisions59::test_cr01_edit_beside_the_second_copy_reasks`: `None != 2 : row snapshot has no owed nearby_at` (record @10, at_pass 1)
2. `TestStaleDecisions59::test_cr01_multipass_second_copy_stays_tracked`: `Lists differ: [10] != [10, 30]` (pass 2 keeps one copy)
3. `TestStaleDecisions59::test_cr02_edit_beside_the_second_sidecar_reasks`: `'current' != 'stale'` (the @10 sidecar is read)
4. `TestStaleDecisions59::test_cr04_removed_guard_beside_covered_member_reasks`: `None != 2 : row snapshot has no owed nearby_at` (row @12)
5. `TestDeferredStaysOpen::test_dmc_deferred_covered_member_below_min_confidence_stays_open`: `no row for 845f88b7; filtered [... 'below-min-confidence']`

Controls green: `test_c59_cr01_edit_at_45_keeps_decision`, `test_c59_cr04_edit_at_line_20_keeps_decision`, `test_dmx_dismissed_covered_member_below_min_confidence_may_drop`.

## Tasks

| Task | Name | Commit | Verify (observed) |
|------|------|--------|-------------------|
| 1 | Red real-chain fixtures + controls | 82ec58b | `-k "TestStaleDecisions59 or dmc or dmx"` -> `5 failed, 3 passed, 86 deselected` |
| 2 | REPRO_59 record + SA-02 prose pin | 82ec58b | `test_nv_render.py -k all_carryforward_bypass` -> `2 passed, 3 subtests`; `-k Repro59Record` -> `1 passed, 11 subtests`; `len(REPRO_59)==6` ok |
| 3 | 59-REPRO.md ledger | ca9834d | 6 `## V` sections, `## Controls`, `## Residuals`; force-added; `git ls-files` lists it |

Tasks 1 and 2 share one commit, as the plan's Task 3 directs.

Other checks run:
- `git diff --stat -- score.py carry_state.py batch_card.py ../phases/review/05-state-all.md ../phases/review/05-state.md` is empty: no production or prose file changed.
- `pytest -q test_decision_continuity.py -k "TestDeferredStaysOpen and not dmc and not dmx"` -> 5 passed. The `member_conf` default left the existing tests unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] A pre-staged STATE.md was swept into the first test commit; the commit was redone**
- **Found during:** Task 3 (first commit)
- **Issue:** The orchestrator had left `.planning/STATE.md` staged in the index. A plain `git commit` after `git add` of the two test files also committed STATE.md (first attempt, f648a63, never pushed).
- **Fix:** `git reset --soft HEAD~1`, then `git commit -- <two test files>`, so only the test files are committed. STATE.md stays staged exactly as the orchestrator left it. The final RED commit is 82ec58b.
- **Cost if wrong:** none for the code. If anything had referenced f648a63 it would dangle, but nothing did.
- **Files modified:** none (commit contents only)
- **Commit:** 82ec58b

**1b. [Rule 3 - Blocking] Unrelated owner edits kept out of the plan-metadata commit**
- **Found during:** final metadata commit
- **Issue:** While this plan ran, owner-authored "Codex integration decision" paragraphs appeared as uncommitted edits in `.planning/ROADMAP.md` (+6 lines) and `.planning/PROJECT.md` (+2 lines). Force-adding ROADMAP.md swept them into the docs commit.
- **Fix:** I amended the docs commit so its ROADMAP.md diff holds only the 59-01 progress row and checkbox. The owner's edits are back as uncommitted working-tree changes in both files, untouched.
- **Cost if wrong:** none. The owner commits those edits whenever they choose.

**2. [Plan count] TestDeferredStaysOpen has 5 pre-existing tests, not 4**
- **Found during:** Task 1 acceptance
- **Issue:** The plan's acceptance line expects "4 passed". The class has five pre-existing tests, including `test_envelope_without_deferred_hashes_scores_as_before`.
- **Fix:** None needed. All 5 pass.
- **Cost if wrong:** none.

### Minor implementation choices
- I added a small shared helper, `_two_copy_lines()`, that returns `base_file()` with lines 10 and 30 set to `return None`. `cr01_scenario` and `cr02_scenario` both use it.
- `test_cr01_multipass_*` reads pass 2's rows from `s3["passes"][-2]` instead of re-running pass 2 separately.
- The REPRO_59 completeness test also checks that the SA-02 fixture resolves to a callable in `test_nv_render`. `test_nv_render` is imported at module top, following the file's import convention.

## Known Stubs

59-REPRO.md has "Green at: _(filled by 59-06)_" lines and an empty "## Residuals" heading. Both are intentional; the plan assigns them to 59-06.

## Threat Flags

None. These changes are test-only and add no new surface.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py (TestStaleDecisions59, REPRO_59, TestRepro59Record)
- FOUND: plugins/vibe-check/scripts/test_nv_render.py (all_carryforward_bypass_holds x5 occurrences)
- FOUND: .planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md (166 lines, tracked)
- FOUND: commit 82ec58b, commit ca9834d
