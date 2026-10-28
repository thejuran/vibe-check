---
phase: 56-verified-fixes-close
plan: 06
subsystem: phase gate (end-to-end closure, suite, golden, replay)
tags: [phase-gate, end-to-end, finalize, replay]
requires: ["56-03 (independent route)", "56-04 (any-age confirmed-fix re-check)", "56-05 (orchestration and render prose)"]
provides:
  - "test_carry_state.py::TestSixRowEndToEnd: fixture -> score.run -> append_pass -> check_state -> finalize_counts -> e2e_gate, with no decisions written"
  - "Phase 56 red/green ledger (below)"
affects: ["/bm:verify-work 56"]
tech-stack:
  added: []
  patterns: ["end-to-end replay of the real owner state through the scorer, the state write and the Finalize gate"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_carry_state.py
decisions:
  - "The end-to-end tests also assert that `fix_verdicts` is absent, so closure cannot have come from a fix-loop obsolete verdict either"
metrics:
  duration: "~15 min"
  completed: 2026-10-23
  tasks: 2
  files: 1
---

# Phase 56 Plan 06: Six-row end-to-end and phase gates Summary

The owner's six already-fixed iPlayarr rows now close at close-out with no dismissal. The pass-4 result is written to state schema-clean, `finalize_counts` reports 0 outstanding, 0 medium, 0 NV and 0 awaiting, and the Finalize gate returns `write`. The state has no `decisions` root and no `fix_verdicts` root. Two negative variants keep the gate shut: a still-applies answer, and a HEAD blob that moved since review. All phase gates pass at HEAD d0f38a8: 3055 passed and 0 failed, the golden digest is unchanged, and the replay diff shows 0 differing runs.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | TestSixRowEndToEnd: closure persists and clears the finalize gate with no decision | d0f38a8 | test_carry_state.py |
| 2 | Phase gates at HEAD and the red/green ledger | (no code change; outputs below) | — |

## Task 1: TestSixRowEndToEnd (observed)

- `pytest -q test_carry_state.py -k "SixRowEndToEnd or Phase45EndToEnd"` gave `19 passed, 125 deselected, 30 subtests passed`. That covers the 4 new tests plus all of TestPhase45EndToEnd.
- `test_six_row_fixture_is_blocked_today_without_closure`: on the raw fixture, the open hashes are 5 critical/warning plus 1 medium, which together are exactly the six leads. The gate result is not `write`, either with or without head_blobs.
- `test_six_row_closure_reaches_write_without_decisions`:
  - `r["filtered"] == []`.
  - `passes[3].resolved` holds exactly the six lead hashes plus the `bugs` and `impact` members. Every entry has `source: recheck` and `verified_blob == BLOBS[file]`.
  - `passes[3].findings == []`.
  - Counts are (0, 0, 0) and awaiting is `[]`. The gate returns `write`.
  - Neither `decisions` nor `fix_verdicts` is present, and passes 1-3 are byte-identical (`passes_json`).
- `test_six_row_still_applies_blocks_write_and_settles`:
  - With R7 (compliance on `2a01829c`) answering still-applies, `2a01829c` stays in `passes[3].findings` with a `recheck_settled` dict (`verdict: still-applies`), and `R_IR_STILL` appears in `filtered[]`.
  - The other five close. `outstanding_cw_hashes == [2a01829c…]` and the gate is not `write`.
  - After `decide(new, 4, (h, "dismiss"))` the gate returns `write` and the passes are unchanged.
- `test_six_row_stale_blob_blocks_write`: HEAD's blob for `src/utils/integrationDeadline.ts` differs from the reviewed snapshot.
  - `22d360d9` stays open with `R_IR_SNAPSHOT` at its site, and the other five close.
  - `outstanding_cw_hashes == [22d360d9…]` and the gate is not `write`.

### Proof that the new tests can fail (run in a scratchpad copy of scripts/)

| Scorer under test | Result |
|---|---|
| phase-base `score.py` + `carry_state.py` (8df9545, before 56-01) | 3 failed, 1 passed. The closure test fails with `filtered` non-empty. Stale-blob fails because `R_IR_SNAPSHOT` is not found in `['verdict: malformed']`. Still-applies fails because `recheck_settled` is None. The blocked-today test passes, as designed. |
| HEAD `score.py` with the independent blob check in `_independent_recheck` (`snapshot_blob != head_blob for v in independent`, the m10 target) replaced by `False` | 1 failed: `test_six_row_stale_blob_blocks_write` |
| HEAD `score.py` with the `still-applies -> _R_IR_STILL` guard in `_bound_plain_recheck` removed | 1 failed: `test_six_row_still_applies_blocks_write_and_settles` |

## Task 2: Phase gates at HEAD (d0f38a8), observed tails

1. Full suite (bare `pytest -q` from `plugins/vibe-check/scripts/`):
   ```
   3055 passed, 4060 subtests passed in 201.78s (0:03:21)
   ```
   That is 0 failed. 3055 = 3051 (after 56-04) + the 4 new tests, which is at least 2964 (the baseline) + 91 phase-56 tests. Collected per file: test_verified_fixes.py 59, test_confirmed_fix.py 96, test_carry_state.py 144.
2. Golden digest:
   - `pytest -q test_score.py -k "golden or Golden"` gave `7 passed, 470 deselected`.
   - `grep -n 'GOLDEN_DIGEST = ' test_score.py` gave `43:GOLDEN_DIGEST = "7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124"`.
   - The exact-value grep count was `1`.
3. Replay (`$SCRATCHPAD` = session scratchpad; the allowances file exists at `../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json`):
   - `python3 replay.py candidate --name phase56-gate --scorer rev:HEAD --out $SCRATCHPAD/phase56-candidate.md` exited 0 with `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1` and **`REGRESSED 0`**. The candidate header records HEAD d0f38a8 and scorer sha256 `1c791f99…`.
   - `python3 replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SCRATCHPAD/phase56-diff.md` exited 0:
     ```
     - runs compared: 170
     - runs differing: 0
     - runs differing (allowed): 0
     - runs with unallowed differences: 0
     ```
4. Import bans: `pytest -q test_score.py -k ImportSet` gave `3 passed`, and `pytest -q test_carry_state.py -k Import` gave `4 passed`.
5. Quiet run (owner decision 1): `git diff 8df9545..HEAD -- plugins/vibe-check/phases/review/05-state.md | grep -c '^[-+].*incremental diff empty but'` printed `0`. The only 05-state.md hunk is at lines 52-65, and step 5 is at line 69, so step 5 is byte-identical to the phase base.

No allowance, golden or fixture was edited, and the working tree holds no change besides the untracked-by-rule `.planning/HANDOFF.json`.

## Red/green ledger (Phase 56)

The phase base is 8df9545 (`docs(56): create phase plan`).

| Path | RED test(s) | RED commit | GREEN commit | Mutant(s) proving the guard trips |
|------|-------------|------------|--------------|-----------------------------------|
| P1 (score): confirmed fix gets one re-check pass only | `TestRetryAfterInconclusive::test_inconclusive_then_retry_closes_on_unchanged_code`, `::test_retry_after_still_applies_waits_for_code_change` | b8b81c0 (56-02) | 7f67f88 (56-04) | score_m19 (applied blob gate), score_m20 (`_R_CF_SETTLED` check); 56-03 m22 |
| P1 (carry_state): awaiting only at the last pass | `TestFinalizeCountsConfirmedFix::test_awaiting_listed_at_any_later_pass`, `::test_settled_row_not_awaiting`, `::test_stale_pass_never_closes` (rewritten) | b8b81c0 (56-02) | 420112b (56-04) | cs_m7 (awaiting settled check) |
| P1 (05-state prose + carry_state docstring) | `TestProse56::test_phase05_forwards_applied_any_age`, `::test_phase05_touched_paths`, `::test_carry_state_docstring_says_any_age` | 3898a23 (56-02) | df839c2 (56-05); docstring 420112b (56-04) | `TestProse56Predicates` per-needle removal mutants (incl. touched-paths bullet scope, PATH_RE needle) |
| P2a: code added beneath an unchanged pinned line (`2a01829c`) | `TestSixRowClosure::test_code_beneath_unchanged_line_closes_via_file_touch`, `::test_nearby_change_triggers_without_a_touching_commit` | d4c7822 (56-01) | c093cce (56-03) | m16 (bound-plain trigger), m15 (bound-plain blob binding), m19 (bound-plain never-confirmers); 56-06 bound-plain still-applies e2e mutant |
| P2b: tests-only fix (`7bc336e7`) | `TestSixRowClosure::test_tests_only_fix_closes_via_associated_test`, `::test_tests_only_fix_needs_the_association` | d4c7822 (56-01) | c093cce (56-03) | m16 (trigger); the association negative (`R_IR_NO_TRIGGER` with an unrelated test path) |
| P2c: four Codex-origin rows | `TestSixRowClosure::test_codex_rows_close_via_ladder_confirmer`, `::test_all_six_close_on_independent_evidence`, `::test_persisted_codex_blank_line_needs_trigger`, `::test_fix_outside_pinned_file_still_closes_needs_recheck_row`, `::test_commit_sha_recorded_when_supplied`, `::test_no_decisions_needed` | d4c7822 (56-01) | c093cce (56-03) | m10 (independent blob binding), m11 (never-confirmers), m12 (independent trigger), m13 (still-applies), m14 (settled memory); 56-06 independent blob e2e mutant (R4 on `22d360d9`) |
| P3: `/review` cannot close a deep-only finding | `TestReviewClosesDeepOnlyFinding::test_bugs_confirms_test_sufficiency_finding_under_review`, `::test_needs_recheck_row_closes_without_trigger`, `::test_no_confirmer_shows_bounded_reason` | ef1c83f (56-01) | c093cce (56-03) | m21 (D-11 `head_blobs` gate), m10 |
| VFIX-06 negatives (stale, still-applies, settled, silent, never-confirmers, member binding, forged memory) | `TestIndependentRouteSafeguards::*` (13; RED ones listed in 56-01) plus the reason-constants subtests; stale-at-any-age leg: 56-02's rewritten `test_stale_verdict_stays_open` / `test_stale_or_changed_fix_verdict_with_routed_resolved_stays_open` | 03087a0 (56-01); b8b81c0 (56-02) | c093cce (56-03); narrowed to the blob reason at 7f67f88 (56-04) | m10, m11, m13, m14, m17 (NEW-finding scrub), m18, m19, m20, m22, m23; score_m19; at close-out, `TestSixRowEndToEnd` still-applies / stale-blob variants (d0f38a8) plus the two scratch mutants above |
| Quiet run (owner decision 1: step 5 of 05-state.md unchanged) | No RED test exists, because the requirement is "no change". The 05-state.md prose locks were added at 3898a23 and leave step 5 alone. | 3898a23 (56-02, prose locks; step 5 deliberately not locked to new text) | df839c2 (56-05); verified at d0f38a8 | `git diff 8df9545..HEAD -- 05-state.md \| grep -c '^[-+].*incremental diff empty but'` printed `0` |
| Close-out (ROADMAP criterion 3, "or at close-out") | `TestSixRowEndToEnd::test_six_row_closure_reaches_write_without_decisions` (+2 negatives); RED against the phase-base scorer, proven in scratch | d0f38a8 (56-06; RED shown against 8df9545 scorer) | c093cce + 420112b (already green when added) | the scratch mutants in the table above |

## ROADMAP success criteria at HEAD

1. Retry after an inconclusive re-check closes on unchanged code (P1). Evidence: TestRetryAfterInconclusive is green, and so is TestFinalizeCountsConfirmedFix.
2. Independent evidence closes the persisted and Codex rows (P2a/b/c, P3). Evidence: TestSixRowClosure and TestReviewClosesDeepOnlyFinding are green.
3. No "fixed in <sha>" dismissal on the card or at close-out. Evidence: TestSixRowEndToEnd reaches `write` with no `decisions` root.
4. Stale or contradicted evidence never closes (VFIX-06). Evidence: the safeguard tests, the mutants, and the negative end-to-end variants.
5. The existing suite stays green. Evidence: 3055 passed and 0 failed, golden unchanged, replay 0 differing and REGRESSED 0.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2] Extra assertions in the closure test**
- **Found during:** Task 1
- **Issue:** The plan's assertions would not catch closure that came from a fix-loop `obsolete` verdict, or a row that survived silently with an empty `filtered`.
- **Fix:** The test also asserts that `fix_verdicts` is absent, that `r["filtered"] == []`, that `passes[3].findings == []`, and that the two `0249b52c` members are among the resolved entries. The blocked-today test asserts that the open set is exactly the six leads.
- **Cost if wrong:** none. These assertions are strictly tighter.
- **Commit:** d0f38a8

## TDD Gate Compliance

Task 1 is `tdd="true"`, but the behaviour it exercises was implemented by 56-03 and 56-04, so the new tests passed at HEAD when they were added. There is no separate `test(...)` RED commit followed by a `feat(...)` commit in this plan. RED was demonstrated instead by running the four tests against the phase-base `score.py` and `carry_state.py` (8df9545) in a scratchpad copy, which gave 3 failed and 1 passed for the stated reasons. Two targeted mutants of HEAD's `score.py` each tripped one test. This plan has no implementation step, by design: "do not modify carry_state.py or score.py".

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-56-21 is covered by the still-applies and stale-blob end-to-end tests. T-56-22 is covered by `resolved[]` entries carrying `verified_blob`, which the closure test asserts. For T-56-23, no allowance, golden or fixture was edited.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_carry_state.py (class TestSixRowEndToEnd, load_six_row)
- FOUND commit: d0f38a8
