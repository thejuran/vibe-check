---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 02
subsystem: finalize
tags: [finalize, helper, cli, parity, mutants, d-18, d-19]
requires:
  - "63-01: finalize_inputs.head_blobs and _git"
provides:
  - "finalize_inputs.NEXT_ACTIONS, next_action, COUNT_KEYS, EXIT_* constants"
  - "finalize_inputs.build_result(state, blobs, switches, report_source=None)"
  - "finalize_inputs.parse_argv, run(argv, cwd=None) and the CLI shim"
  - "D-19: the three per-file fingerprint checks run from the repo root"
affects: [63-05, 63-06, 63-07, 63-08, 63-11]
tech-stack:
  added: []
  patterns: ["three library calls as the only rule source", "second read of the state for the report stage", "multi-replacement source mutants"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/finalize_inputs.py
    - plugins/vibe-check/scripts/test_finalize_inputs.py
decisions:
  - "D-19 applied: the per-file git checks run with the repo root as cwd (argv unchanged), so a file with unsaved or staged edits is never fingerprinted from a subfolder"
  - "A1: exit 5 is unreachable on current helpers through a real state (finalize_counts and decisions_report both refuse on carry_state.state_reason); the exit-5 build_result test patches decisions_report, and the CLI exit-5 tests swap the state file between the two reads"
  - "A failed write to --blob-out is a counting-stage refusal (exit 2, REASON_HEAD_BLOBS), the line 2.14.1 shows when its counts step finds the fingerprint file missing or empty"
  - "run takes an optional cwd (None = process cwd) so mutants run in-process; the shim passes none"
metrics:
  duration: "about 75 min"
  completed: 2026-11-14
---

# Phase 63 Plan 02: The Finalize helper result and command line Summary

`finalize_inputs.py` now does the whole Finalize input step in one call. It rebuilds the HEAD fingerprints into a fresh empty `--blob-out`, gets the counts from `carry_state.finalize_counts` and the decision from `finalize_gate.run` on the seven flags, and on `write` only gets the report bundle from `batch_card.decisions_report` after reading the state file a second time. It prints `{action, reason, next, counts, report}` and uses fixed exit codes 0/2/3/4/5. On stderr it prints only the 2.14.1 commands' own refusal lines. The owner's D-19 decision is also applied first: from a subfolder, the fingerprint checks now read the file from the repo root.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| D-19 (RED) | Edited/staged file not fingerprinted from a subfolder | 34fd96a | test_finalize_inputs.py |
| D-19 (GREEN) | Fingerprint checks read the file from the repo root | 4e6bfc5 | finalize_inputs.py, test_finalize_inputs.py |
| 1 (RED) | Failing tests for the result | 54bb2f9 | test_finalize_inputs.py |
| 1 (GREEN) | Result assembled from the three helpers | 184c4b2 | finalize_inputs.py, test_finalize_inputs.py |
| 2 (RED) | Failing tests for the command line | 9e518ea | test_finalize_inputs.py |
| 2 (GREEN) | Command line with fixed exit codes | 73f3ef7 | finalize_inputs.py, test_finalize_inputs.py |

## The one deliberate behaviour difference from 2.14.1 (D-19)

**Reproduction (2.14.1).** Use a temp repo with `sub/c.ts` committed, and run the session from `<repo>/sub`. Give the finding the root-relative file `sub/c.ts` and edit it without committing (or stage an edit and then restore the working copy). The three 2.14.1 calls, run as plain git from `sub`, exit `[0, 0, 0]`. `git rev-parse HEAD:sub/c.ts` reads from the root. But the pathspec after `--` in `git diff --quiet HEAD -- sub/c.ts` and `git diff --cached --quiet -- sub/c.ts` is read relative to the cwd as `sub/sub/c.ts`. It matches nothing and exits 0. So 2.14.1 fingerprints the edited file, and a fix-obsolete verdict whose `verified_blob` equals the HEAD blob closes on changed code.

**Candidate.** The helper still finds the root with `git rev-parse --show-toplevel` from the session cwd. It then runs the three per-file checks with that root as their cwd. The argv is unchanged (`rev-parse HEAD:<f>`, `diff --quiet HEAD -- <f>`, `diff --cached --quiet -- <f>`). An edited or staged file is left out, and a clean file is still fingerprinted.

**Tests:**
- `TestSubdirectoryCwd`: the clean file is fingerprinted from a subfolder. An edited file and a staged file are not, and each test also asserts the 2.14.1 plain-call exit codes `[0, 0, 0]` as the reproduction. An edit seen from a nested subfolder is also left out.
- `test_mutant_checks_in_session_folder_fingerprint_edit_from_subfolder` and `test_mutant_index_check_in_session_folder_fingerprints_staged_file`: putting either diff check back in the session folder lets the edit through.

`test_gap_subdirectory_cwd` is gone. Plans 63-08 (D-15 comparison) and 63-11 (D-14 page) should cite this section as the intended difference. The five recorded situations still match (`finalize baseline matches (5 situations)`). None of them runs from a subfolder.

## Verification (observed)

- D-19 RED: 3 failed (edited, staged, nested), 38 passed. Each failure was the expected one: the helper returned a blob where `{}` was expected. GREEN: 339 passed across finalize_inputs, finalize_gate and carry_state.
- Task 1 RED: 110 failures, all `AttributeError` for the missing API or the import-set assertion. GREEN: the Task 1 verify command printed `OK`. `-k "parity or next or mutant"` gave 24 passed. There are 0 band literals (`"critical"|"warning"|"medium"`) in the module.
- Task 2 RED: 68 failed (no CLI yet). GREEN: the Task 2 verify command printed `OK`. That run included no-state exit 0 with `stop-no-state`, exit 2 with empty stderr when `--noninteractive` is missing, the exact `REASON_HEAD_BLOBS` line for a non-empty `--blob-out`, and `34 shipped`.
- `test_finalize_inputs.py`: 94 passed, 185 subtests, none skipped (`test_named_difference_unreadable_state` ran: not root). 20 tests named `test_mutant_*`.
- Related suites: `test_finalize_inputs.py test_finalize_gate.py test_carry_state.py test_batch_card.py test_finalize_card.py .github/scripts docs/design/lean-v2.15/tools` gave 1030 passed, 1053 subtests.
- `finalize_capture.py verify` printed `finalize baseline matches (5 situations)`.
- `git diff --quiet dd8e4ab HEAD -- plugins/vibe-check/phases`: exit 0. `carry_state.py`, `finalize_gate.py` and `batch_card.py` are unchanged against the merge base.
- `grep -c "uncertain about Finalize\|Finalize stopped"` returned 0. Non-comment `print(` count: 0.
- **Not run:** the full suite (~16 min; the orchestrator runs it in the main checkout after the merge, per the worktree instructions).

## D-06 gaps

Each is a named test. The helper behaves as 2.14.1 here, though it could be stricter.

- `test_gap_leading_dash_path_is_fingerprinted` (from 63-01, unchanged): `-x.ts` is fingerprinted.
- `test_gap_at_pass_true_matches_pass_one` (from 63-01, unchanged): `at_pass: true` matches pass 1.
- `test_gap_empty_state_file_path_is_no_state` (new): `--state-file ""` is read as no state file. The result is exit 0, `next` `stop-no-state`, no git call, and `--blob-out` untouched, which matches `[ -f "" ]` being false at 2.14.1.

The subfolder gap from 63-01 was **fixed** under D-19 (see above), so it is no longer a gap.

**Stricter than 2.14.1, by contract (not a D-06 gap):** a `--blob-out` holding `{}` is refused with `REASON_HEAD_BLOBS` (exit 2), but 2.14.1's counting command accepts such a file. This follows from the plan's rule that `--blob-out` must be an empty file and the map is always rebuilt (T-63-05). There is no 2.14.1 counterpart line. Test: `test_refuse_bad_blob_out_beside_a_good_state` (subtest `empty object`).

## Named differences for the ledger

- **`test_named_difference_unreadable_state`** (`TestCliStderrParity`): the state file is present but unreadable (mode 000). At 2.14.1, the shell's own `< "$STATE_FILE"` redirect printed one line ending `Permission denied` and naming the file's path, above the counting sentence. The test runs the 2.14.1 counting command in a fresh `bash -s` and asserts that line. The helper exits 3 and writes nothing. This can't be made identical: the line belongs to the shell, carries a line number that depends on its fence, and copying it would mean echoing a path. If the second (report-stage) read hits an `OSError`, the helper exits 5 and writes nothing: a plain stop under the report sentence (`test_report_second_read_unreadable_is_a_silent_report_stop`). Plan 63-06 enters this in the ledger; plan 63-11 puts it to the owner.
- **D-19** (above) is the one deliberate behaviour difference in the fingerprints.

## A1 finding

Exit 5 is unreachable on current helpers with one consistent state. `batch_card.decisions_report` returns None only when `carry_state.state_reason(state)` is not None. That is the same check that makes `finalize_counts` return None, which the helper hits first and maps to exit 3. So `test_refuse_report_none_on_write_gives_exit_report` uses `mock.patch.object`. In the CLI, exit 5 is still reachable in practice: the report stage reads the state file a second time (D-18), and a file changed or made unreadable between the two reads gives exit 5. The report-parity tests cover this by swapping the file's content between the reads. No `test_gap_*` and no owner checkpoint were needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two 63-01 mutant tests quoted the old source text**
- **Found during:** D-19 GREEN
- **Issue:** `test_mutant_no_worktree_check_includes_dirty_file` and `test_mutant_no_index_check_includes_staged_file` substituted the text `..., f], cwd)`, which no longer exists once the checks run from `root`.
- **Fix:** the mutant text now reads `..., f], root)`. Two new mutants pin the root cwd itself.
- **Cost if wrong:** none. Each mutant still asserts that its replaced text is present before it runs.
- **Commit:** 4e6bfc5

**2. [Rule 1 - Bug] Two of my own mutant tests targeted the wrong code**
- **Found during:** Task 1 GREEN and Task 2 GREEN
- **Issue:** the report-on-non-write mutant matched the first `if action == "write":`, which is in `next_action`. The gate-stage stderr mutant targeted the catch-all, but a gate failure returns through `build_result`.
- **Fix:** the mutant text is anchored to the report block. The stderr mutant is split into a gate-stage version (inside `build_result`) and a catch-all version (an unexpected exception from `head_blobs`).
- **Cost if wrong:** a mutant that never trips would be a decorative guard. Both now trip.
- **Commits:** 184c4b2, 73f3ef7

**3. [Rule 2 - Correctness] A write failure on `--blob-out` is a counting-stage refusal**
- **Found during:** Task 2
- **Issue:** the plan doesn't say what happens if writing the fingerprint file fails. Letting it reach the catch-all would give exit 4 (the gate sentence and a rebuild).
- **Fix:** it returns exit 2 with `REASON_HEAD_BLOBS`. This is the line 2.14.1's counting step shows when the fingerprint file it reads is missing or empty.
- **Cost if wrong:** one rare path shows the counting line instead of nothing. No test drives a real write failure.
- **Commit:** 73f3ef7

**4. [Rule 3 - Blocking] `run(argv, cwd=None)`**
- **Found during:** Task 2
- **Issue:** the in-process mutant and stderr tests need git to run in the temp repo without a `chdir`.
- **Fix:** `run` takes an optional `cwd`, passed to `head_blobs`. The shim calls `run(sys.argv[1:])`, so the process cwd is used, as the contract says.
- **Cost if wrong:** none for the CLI contract.
- **Commit:** 73f3ef7

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-63-05: `--blob-out` must be empty and the map is always rebuilt, with a freshness test and two mutants. T-63-06: all five arguments are required and switches are only `true`/`false`, with a mutant for a defaulted switch. T-63-07: the marker test covers stderr and refusal stdout, the module-shape lock has a single stderr write with no constant, and the catch-all writes nothing. T-63-08: every subprocess call in `CliCase.cli` checks the state file's sha256 before and after and checks that the working tree gained no file.

## TDD Gate Compliance

- D-19: `test(63-02)` 34fd96a, then `fix(63-02)` 4e6bfc5.
- Task 1: `test(63-02)` 54bb2f9, then `feat(63-02)` 184c4b2.
- Task 2: `test(63-02)` 9e518ea, then `feat(63-02)` 73f3ef7.

## Self-Check: PASSED

Files present: finalize_inputs.py, test_finalize_inputs.py, this SUMMARY. Commits present: 34fd96a, 4e6bfc5, 54bb2f9, 184c4b2, 9e518ea, 73f3ef7.
