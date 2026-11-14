---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 05
subsystem: finalize
tags: [finalize, removal-ledger, mutants, d-11, d-06, d-18]
requires:
  - "63-02: finalize_inputs CLI, build_result and their tests"
  - "63-03: test_cross_call_vars.py mutant (d)"
provides:
  - "63-REMOVAL-LEDGER.md: passages P1-P7 + P2-line/P7-line, 43 test rows, count lock, named differences, D-06 gaps"
  - "test_finalize_inputs.py: TestCliWritesOnlyTheFingerprintFile, TestLedgerReplacements (5 replacements + mutants)"
  - "test_carry_state.finalize_dirty_fingerprints helper"
affects: [63-06, 63-07, 63-11]
tech-stack:
  added: []
  patterns: ["red list = scratch run minus control run", "source-mutation run against each replacement test, file restored"]
key-files:
  created:
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REMOVAL-LEDGER.md
  modified:
    - plugins/vibe-check/scripts/test_finalize_inputs.py
    - plugins/vibe-check/scripts/test_carry_state.py
    - plugins/vibe-check/scripts/test_score.py
decisions:
  - "Locks whose needles sit in the parts of P5/P6 that 63-06 keeps (refused step, stop sentence, write boundary, answer files, echo_text, never re-show) are 'kept', not rewritten. They went red only because the scratch run blanked the whole line."
  - "The REPRO_60 fixture-name lock is a ledger row: 63-06 must re-point each removed or renamed fixture in the same commit"
  - "test_score's re-point calls the old reader's own finalize-counts command body (run([...])) rather than the live helper, because the rule is about the old reader"
metrics:
  duration: "about 70 min"
  completed: 2026-11-14
requirements: [FINX-04]
---

# Phase 63 Plan 05: Removal ledger and replacements Summary

The removal ledger was built from a real red list: four whole-suite scratch runs (a control run, all passages out, P3 only, P7 only). Every rule the extraction touches now has a helper test with a mutant that trips it. Five of those tests are new, and two prose-dependent lookups no longer read `90-finalize.md`. `90-finalize.md` is unchanged.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Red list from scratch copies; ledger with MISSING rows | afe71b8 | 63-REMOVAL-LEDGER.md |
| 2a | New helper replacements and mutants | 5f6474e | test_finalize_inputs.py |
| 2b | Re-point the two prose-independent lookups | 45af0b3 | test_carry_state.py, test_score.py |
| 2c | Ledger filled with the landed shas, no MISSING left | 624d3cc | 63-REMOVAL-LEDGER.md |

The replacements (5f6474e) come before the re-point (45af0b3) in `git log`. Nothing was removed in this plan.

## The scratch runs (observed)

Four detached worktrees of `dad2813` were created under the session scratchpad. Each ran `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools -rf`. All four were removed with `git worktree remove --force`, and `git worktree list` shows none of them.

| Copy | Result |
|------|--------|
| control (nothing changed) | 5 failed, 4481 passed, 1 skipped |
| P1, P2, P3, P4, P7 deleted; P5 and P6 lines blanked | 63 failed, 4450 passed, 1 skipped |
| only P3 deleted | 7 failed, 4479 passed |
| only P7 deleted | 9 failed, 4478 passed |

**Red list:** 41 test ids failed (as whole tests or subtests) with the passages out and did not fail in the control run. By module:
- `test_finalize_card.py`: 36 (27 whole-test failures, 9 failing only in subtests)
- `test_carry_state.py`: 1
- `test_confirmed_fix.py`: 1
- `test_cross_call_vars.py`: 1
- `test_diff_ranges.py`: 1
- `test_pause_batching.py`: 1. The research did not name this one: the `noninteractive` byte pin on P4 line 44.

**P3 only:** `test_confirmed_fix.py::TestProse::test_finalize_renders_confirmed_fix` and `test_finalize_card.py::TestFinalizeCard::test_phase57_decision_contract`. Both are 63-07's.

**P7 only:** `test_finalize_card.py::TestFinalizeCard::test_helper_calls_present`, `test_finalize_card.py::TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report`, `test_finalize_card.py::TestFinalizeFreshShellWalk::test_card_route_records_then_writes`, and one subtest of `test_post_decision_rerun_decides_on_a_fresh_gatefile`. These are 63-07's, as well as 63-06's.

**Control-run failures (not caused by the removal):** `test_replay.py::TestPhase53SameLineRegressionCases::test_a2_pair_sits_on_adjacent_lines_of_one_statement`, `::test_off_line_credit_mutation_trips` (2 subtests) and `::test_pre_same_line_scorer_gave_critical_100` (2 subtests). That is 3 ids and 5 failures, and they need local-only transcripts. `test_replay.py` does not read `90-finalize.md` (0 references), so no lock went unchecked.

**Not red but entered in the ledger:** `test_score.py::TestRollbackNeedsVerification::test_old_reader_refuses_open_nv_state` reads a pinned old blob, so it could not go red; it was re-pointed here. `test_decision_continuity.py::TestRepro60Record::test_every_fixture_exists` reads test names, so it trips only when 63-06 renames or removes a fixture.

## Replacements landed (5f6474e) and the break each one catches

Each replacement test was run once against a source-mutated `finalize_inputs.py`, with the file restored afterwards. Every run failed on an assertion:

| Replacement test | Break applied | Observed |
|------------------|---------------|----------|
| `TestLedgerReplacements::test_unsubstituted_blob_out_is_refused` | the blob-out check accepts anything, and the write's OSError goes to the catch-all | `(4, b'') != (2, b'')` |
| `TestLedgerReplacements::test_head_sha_literal_head_is_not_read` | the helper refuses a `HEAD` head_sha | `(3, b'refused: malformed state\n') != (0, b'')` |
| `TestLedgerReplacements::test_card_route_record_then_rerun_writes` | counts ignore the recorded decisions | `'outstanding-to-phase-5' != 'write'` |
| `TestCliWritesOnlyTheFingerprintFile::test_only_the_fingerprint_file_changes_on_every_route` | the helper also writes `<blob-out>.err` | 2 subtests failed (extra file) |
| `TestCliWritesOnlyTheFingerprintFile::test_missing_fingerprint_file_is_refused_and_not_created` | a missing fingerprint file is accepted and created | exit 0 with a result instead of 2 |
| `TestBuildResultFailures::test_refuse_gate_unknown_action_gives_exit_gate` (existing) | the unknown-action check is removed | `(0, {'action': 'approve', …})` |

Each break also has an in-file mutant test (`test_mutant_*`), which follows the established form: assert the real behaviour, then the substituted behaviour, and check that the substituted text was present.

## Re-pointed tests (45af0b3): the deliberate breaks tried

- **`test_carry_state.py::TestPhase45EndToEnd::test_fix_obsolete_unbound_when_working_tree_dirty`.** Its `90-finalize.md` half now calls `finalize_dirty_fingerprints()`, which runs `finalize_inputs.head_blobs` on three temp repos: clean, unsaved edit, and staged edit. It expects `{clean: True, working tree: False, index: False}`. The `05-state.md` and `50-fix-loop.md` needles are unchanged.
  - Break 1: deleted the `git diff --quiet HEAD --` check in `finalize_inputs.py`. Failed: `{'clean': True, 'working tree': True, 'index': False} != …`.
  - Break 2: deleted the `git diff --cached --quiet --` check. Failed: `{… 'index': True} != …`.
  - Both restored (`cmp` against a saved copy).
- **`test_score.py::TestRollbackNeedsVerification::test_old_reader_refuses_open_nv_state`.** The fence-text lookup on the old blob is replaced by `OLD_CS.run(["finalize-counts"], json.dumps(state))`. It asserts `(2, "")`, the obligation refusal line on stderr, and an unchanged state.
  - Break 1: patched the old reader's `state_reason` to None around the call. Failed: `'refused: malformed state\n' != 'refused: malformed state: obligation\n'`.
  - Break 2: the old reader accepts the state (`state_reason` None and `finalize_counts` returning counts). Failed: `(0, '{"outstanding_cw": 0}') != (2, '')`.
  - Both restored. The unused `OLD_FINALIZE_PROSE_BLOB` constant was removed.

## Verification (observed)

- Task 1 checks: all four sections present, all nine passage rows, `test_finalize_card.py::` and `test_decision_continuity.py::` present (run as a Python script; see Deviations). `git diff --quiet HEAD -- plugins/vibe-check/phases` exit 0.
- Task 2: `MISSING` count 0 in the ledger. `pytest -q -p no:cacheprovider test_finalize_inputs.py test_carry_state.py test_score.py` gave 839 passed, 879 subtests passed. `git diff --quiet dd8e4ab… HEAD -- plugins/vibe-check/phases/shared/90-finalize.md` exit 0.
- All 101 `module.py::Class::test` ids named in the ledger exist (AST check).
- Related modules `test_finalize_card.py test_decision_continuity.py test_confirmed_fix.py test_diff_ranges.py test_pause_batching.py test_cross_call_vars.py` gave 549 passed, 763 subtests passed.
- **Not run here:** the full suite after the changes (it takes about 17 minutes, and the worktree lacks the replay transcripts). The orchestrator runs it in the main checkout after the merge. The control run above is the full suite at the base.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pre-existing ruff findings blocked the re-point commit**
- **Found during:** Task 2 (commit 45af0b3)
- **Issue:** the commit hook runs ruff on whole staged files, and `test_carry_state.py`/`test_score.py` already had 13 findings at the base (10 E731 lambda assignments, 2 E702 semicolons, 1 E741 `l`).
- **Fix:** E731 converted with `ruff --fix --unsafe-fixes --select E731`, the semicolon lines split, and `l` renamed to `ln`. No behaviour change: the three files gave 839 passed.
- **Cost if wrong:** a converted lambda that captured differently would fail its test, and none did. The diff in `test_score.py` is wider than the re-point.
- **Commit:** 45af0b3

**2. [Rule 3 - Blocking] Plan verify commands run in split form**
- The harness refuses `bash -c` strings that mention git, and some grep pipelines over the scratch logs, in this worktree. The ledger grep checks ran as a Python script with the same conditions, and the git checks ran as plain commands. Same checks, same results.
- **Cost if wrong:** none.

**3. [Rule 2 - Correctness] Ledger built in two states**
- The plan asks for MISSING rows that task 2 then fills. Task 1's commit (afe71b8) marks the five planned replacements `MISSING (planned: …)`, and 624d3cc fills them with 5f6474e. This keeps the history honest about when each replacement landed.

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** P5 and P6 are "rewritten", so their locks are rewritten. **Actual:** 11 locks that went red read needles in the parts of the P5/P6 lines that 63-06 keeps: the refused-step and stop sentences, the write boundary, `rm -f` answer files, `echo_text`, and "never re-show the card". They are marked **kept**, not rewritten. **Why:** the scratch run blanked whole lines. **Cost if wrong:** if 63-06 drops one of those phrases, a kept lock goes red. That is the intended alarm, not a silent loss.
- **Found during:** Task 1. **Planned:** `test_score.py` is in the red list. **Actual:** it reads a pinned old blob, so it never goes red. It was re-pointed anyway, as the plan asked.

## Known Stubs

None.

## Threat Flags

None. T-63-14: the ledger comes from a real red list, the replacements landed first, and each has a tripping mutant. T-63-15: the deliberate breaks for both re-pointed tests are recorded above.

## TDD Gate Compliance

This plan adds tests for behaviour that already exists, so there is no implementation step. The `test(63-05)` commits are 5f6474e and 45af0b3. Each new lock was shown to fail under a deliberate break (tables above) instead of a RED commit.

## Self-Check: PASSED

- FOUND: .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REMOVAL-LEDGER.md
- FOUND: plugins/vibe-check/scripts/test_finalize_inputs.py (TestLedgerReplacements, TestCliWritesOnlyTheFingerprintFile)
- FOUND commits: afe71b8, 5f6474e, 45af0b3, 624d3cc
