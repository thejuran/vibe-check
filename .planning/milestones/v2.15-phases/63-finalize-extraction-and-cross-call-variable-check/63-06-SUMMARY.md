---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 06
subsystem: finalize
tags: [finalize, extraction, fresh-shell-walk, removal-ledger, d-01, d-05, d-07, d-18]
requires:
  - "63-02: finalize_inputs CLI (exit codes 0/2/3/4/5, NEXT_ACTIONS, stderr contract)"
  - "63-05: removal ledger and landed replacements"
provides:
  - "90-finalize.md: one Finalize-inputs fence calling finalize_inputs.py; branch bullets headed by next values"
  - "test_finalize_card.py: inputs_block_holds, fresh-shell walks over the new fence, _stand_in_root for 63-07"
  - "test_finalize_inputs.py: TestNextVocabularyProse (bullets == NEXT_ACTIONS)"
  - "63-REMOVAL-LEDGER.md: 63-06 rows filled, hidden-lock rows, named differences (1)-(4)"
affects: [63-07, 63-08, 63-09, 63-11]
tech-stack:
  added: []
  patterns: ["PATH-shim mktemp to remove or pre-fill the printed file before the helper reads it", "stand-in helper under a temp VC_ROOT to drive a chosen exit code through the real fence"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
    - plugins/vibe-check/scripts/test_finalize_inputs.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_diff_ranges.py
    - plugins/vibe-check/scripts/test_pause_batching.py
    - plugins/vibe-check/scripts/test_confirmed_fix.py
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REMOVAL-LEDGER.md
decisions:
  - "The medium fallback bullet is `- stop-fallback-medium:` with the byte-pinned `- fallback with outstanding_cw empty …` line nested under it, so the NONINTERACTIVE pin stays byte-identical"
  - "REPRO_60 fixtures re-pointed in the same commit as the removal (orchestrator note), to tests in the four modules _suite_defines searches"
  - "The `$COUNTS_JSON` name used by the unchanged REVIEW.md section is defined as the result's `counts` object"
metrics:
  duration: "about 95 min"
  completed: 2026-11-14
requirements: [FINX-01, FINX-02, FINX-03, FINX-04]
---

# Phase 63 Plan 06: Finalize extraction Summary

Finalize's gate inputs now come from one fence that calls `finalize_inputs.py`. The fence mints and prints `BLOBFILE=`, leaves the helper's stderr on screen, and maps exit 4, 5 and any other code to the three 2.14.1 sentences byte for byte. The model branches on the result's `next`. The per-file git checks, the two Write-tool writes and the gate fence are gone from the instructions. The rule-v1 step count falls from 92 to 84.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Finalize walks and locks against the new block; REPRO_60 fixtures re-pointed | 36612af | test_finalize_card.py, test_finalize_inputs.py, test_decision_continuity.py |
| 2 (RED) | Re-point the diff-ranges walk and the noninteractive pin | 41de3c5 | test_diff_ranges.py, test_pause_batching.py |
| 3a (RED) | Two hidden locks re-pointed | e9dc275 | test_finalize_card.py, test_confirmed_fix.py |
| 3 (GREEN) | Gate-input part of 90-finalize.md rewritten | 1ced383 | 90-finalize.md |
| 3b | Ledger filled; named differences | 2e4bae5 | 63-REMOVAL-LEDGER.md |

## Tests removed or renamed in Task 1

| Old name | New name or outcome |
|----------|---------------------|
| `TestFinalizeFreshShellWalk::test_gate_fence_reads_cross_call_variable_today` | removed (REPRO_60 GATE-INPUT-CROSS-CALL → `test_walk_reaches_counts_gate_report + test_inputs_block_holds`) |
| `TestFinalizeFreshShellWalk::test_retry_mints_new_gatefile_after_gate_input_failure` | removed (REPRO_60 GATEFILE-RETRY → `test_retry_mints_new_blobfile_after_missing_path + test_retry_rule_holds`) |
| `TestFinalizeFreshShellWalk::test_gatefile_missing_path_is_a_named_trigger` | removed (same REPRO_60 row) |
| `TestFinalizeFreshShellWalk::test_post_decision_rerun_decides_on_a_fresh_gatefile` | renamed `test_post_decision_rerun_decides_on_fresh_counts` (REPRO_60 STALE-GATEFILE-RERUN re-pointed) |
| `TestFinalizeFreshShellWalk::test_malformed_gatefile_shows_only_stop_sentence` | removed |
| `TestGapRoundFinalize::test_no_cross_call_gate_input_holds`, `test_mutant_cross_call_gate_input` (and `no_cross_call_gate_input`) | removed |
| `TestNeedsVerificationFinalizeProse::test_seven_key_flags` (and `seven_key_flags_holds`) | removed |
| `TestGapRoundFinalize::test_mutant_printed_paths` | GATEFILE subtest dropped |

Rewritten with names kept: `test_walk_reaches_counts_gate_report` (clean route), `test_card_route_records_then_writes`, `test_counts_fence_without_literal_exits_two` (unsubstituted switches fail closed; stderr is the sentence alone), `test_retry_mints_new_blobfile_after_missing_path` (rebuild), `test_stale_earlier_attempt_file_does_not_govern`, `test_post_decision_recount_refingerprints_head` (edit during the card on a real repo), `test_retry_rule_holds`, `test_mutant_retry_rule`, `test_step3_rerun_rule_holds`, `test_mutant_step3_rerun_rule`, `test_mutant_step3_reinserts_stale_fingerprint_claim`.

New: `TestFinalizeInputsBlock::test_inputs_block_holds` / `test_mutant_inputs_block` (no-redirect mutant, reason-clause mutants, defaulted slot, GATEFILE/COUNTS fence put back, helper called twice); `TestFinalizeFreshShellWalk::test_counting_line_stays_on_screen` (D-18, compares stderr with `carry_state.REASON_HEAD_BLOBS` / `REASON_STATE_JSON`); `test_report_failure_stops_at_once` (stand-in helper via `_stand_in_root(code, line)`; mutants: `5)` arm removed, `5)` mapped to the counting sentence); `test_finalize_inputs.py::TestNextVocabularyProse` (3 tests).

## Red set (Task 2, observed)

Full suite after 41de3c5: `36 failed, 4474 passed, 1 skipped`. Failing ids, all rewritten in Task 1/2 and failing because the new fence or wording was absent:
- `test_diff_ranges.py::TestStateHeadShaFence::test_finalize_mode_skips_the_bind_and_reaches_the_counts_step`
- `test_finalize_card.py::TestFinalizeCard::test_pins_still_exactly_once` (new pin)
- `test_finalize_card.py::TestGapRoundFinalize::` `test_mutant_retry_rule`, `test_mutant_step3_reinserts_stale_fingerprint_claim`, `test_mutant_step3_rerun_rule`, `test_retry_rule_holds`, `test_step3_rerun_rule_holds`
- `test_finalize_card.py::TestFinalizeInputsBlock::` `test_inputs_block_holds`, `test_mutant_inputs_block`
- `test_finalize_card.py::TestFinalizeFreshShellWalk::` `test_card_route_records_then_writes`, `test_counting_line_stays_on_screen`, `test_counts_fence_without_literal_exits_two`, `test_post_decision_recount_refingerprints_head`, `test_post_decision_rerun_decides_on_fresh_counts`, `test_report_failure_stops_at_once`, `test_retry_mints_new_blobfile_after_missing_path`, `test_stale_earlier_attempt_file_does_not_govern`, `test_walk_reaches_counts_gate_report`
- `test_finalize_inputs.py::TestNextVocabularyProse::` all three
- `test_pause_batching.py::TestNoninteractiveBytePin::test_each_pin_present_exactly_once`
- plus the known worktree-only `test_replay.py` failures (3 ids, 5 failures)

Two hidden locks went red only once the instruction file changed (see Deviations); both were re-pointed in e9dc275 before the instruction commit and entered in the ledger.

## Figures (as the tools printed them, at 1ced383)

- `step_count.py --root plugins/vibe-check --json`: `totals.model_run_steps` **84** (bash_fences 39, carried_paste_sites 35, inline_commands 5, write_tool_writes 5). Before: 92. Keeping the counting line on screen cost no counted step.
- `footprint.py --json`: `finalize.bytes` **133387** (before: 136114).

## Verification (observed)

- Task 1 verify: FreshShell tests failed; both modules parse; `no_cross_call_gate_input` gone; the three kept helpers present; `REASON_HEAD_BLOBS` used; 90-finalize.md identical to dd8e4ab.
- Task 2 verify: `TestRepro60Record` 3 passed; diff-ranges walk failed; 90-finalize.md still identical.
- Task 3 checks: no `GATEFILE`, `FINALIZE_GATE_JSON` or `BLOBFILE.err`; the helper call appears once with no `2>`; the three sentences and the stop sentence present; six D-03 files identical to dd8e4ab; the card section equal to dd8e4ab except the step-3 line and the `### Writing REVIEW.md` tail equal (CARD-OK); named modules `test_finalize_inputs test_cross_call_vars test_finalize_card test_finalize_gate test_finalize_archive_prose test_confirmed_fix test_pause_batching` all pass; `TestRepro60Record` and the diff-ranges walk pass.
- `finalize_capture.py verify`: `finalize baseline matches (5 situations)`.
- **Full suite at 1ced383 (+ledger): `5 failed, 4492 passed, 1 skipped, 5580 subtests passed`.** The 5 failures are the known worktree-only `test_replay.py::TestPhase53SameLineRegressionCases` ones (`test_a2_pair_sits_on_adjacent_lines_of_one_statement`, `test_off_line_credit_mutation_trips` ×2 subtests, `test_pre_same_line_scorer_gave_critical_100` ×2 subtests). `test_cross_call_vars.py` green.
- Mutants: every new or rewritten lock is run against a mutant inside its own test (redirect appended, `5)` arm removed or remapped, each step-3/retry needle dropped, forbidden phrases put back, a bullet removed or an unknown value added); all trip.

## Deviations from Plan

**1. [Rule 3 - Blocking] REPRO_60 fixtures re-pointed in Task 1, not Task 2.** The orchestrator's note requires the REPRO_60 entry to change in the same commit as the rename or removal; the plan put it in Task 2. Only `fixture` values changed (3 rows; count stays 16). **Cost if wrong:** none; the lock stays green at every commit.

**2. [Rule 3 - Blocking] REPRO_60 replacements named in test_finalize_card.py, not the ledger's helper tests.** `_suite_defines` only searches four modules, so the ledger's replacements in `test_finalize_inputs.py` / `test_cross_call_vars.py` cannot be named there without changing more than `fixture` values. The rows name the new-block walks and locks that cover the same scenario. **Cost if wrong:** a reader following REPRO_60 lands on the walk, not the helper test; the ledger still names both.

**3. [Rule 1 - Hidden locks] Two locks not in the red set.** `test_finalize_card.py::TestNeedsVerificationFinalizeProse::test_review_stamp_written` found the `write` bullet by its 2.14.1 head; `test_confirmed_fix.py::TestProse::test_finalize_renders_confirmed_fix` needed the quoted key from the removed P2 comment. Re-pointed in e9dc275 (the second now reads `finalize_inputs.COUNT_KEYS`, with a new mutant) and entered in the ledger. **Cost if wrong:** none for behaviour; the ledger's red list was incomplete by two.

**4. [Rule 3 - Blocking] Lint hook.** Two unused imports (`re`, `unittest.mock`) removed from `test_confirmed_fix.py`; the module's tests pass (96 passed).

**5. `test_pause_batching.py` changed in Task 2** though not in `files_modified`: the ledger assigns its noninteractive pin to this plan.

## Assumption Drift (advisory)

- **Found during:** Task 3. **Planned:** the medium fallback bullet heads with its `next` value. **Actual:** the byte-pinned line starts `- \`fallback\` with`, so it is nested under `- \`stop-fallback-medium\`:` to keep the pin byte-identical. **Cost if wrong:** one extra list level on screen for the model; no owner-facing text changed.

## Known Stubs

None.

## Threat Flags

None. T-63-16: unsubstituted slots walk-tested (exit non-zero, sentence alone). T-63-17: stale-attempt and edit-during-card walks. T-63-18: stderr asserted line-exact with no traceback. T-63-19: write boundary kept. T-63-20: no git on a finding's file remains in the instructions.

## TDD Gate Compliance

RED: 36612af, 41de3c5, e9dc275 (`test(63-06)`). GREEN: 1ced383 (`feat(63-06)`).

## Self-Check: PASSED

Commits present: 36612af, 41de3c5, e9dc275, 1ced383, 2e4bae5. Files present: all listed in key-files.
