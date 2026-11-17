---
phase: 62-baseline-and-continuous-test-run
plan: 04
subsystem: baseline-tools
tags: [finalize, capture, baseline, pinned-commit, determinism]
requires: []
provides:
  - "docs/design/lean-v2.15/tools/finalize_capture.py: SITUATIONS (five ids), materialize, normalise, canonical_sha256, extract_fences, fence_holding, run_fence, FenceWalk2141, capture_one, prepare_state, main(capture)"
affects:
  - "62-10 (adds one-rebuild, refused-close, fresh-shell-restart walks, verify and the committed record on capture_one)"
  - "Phase 63 (a helper driver must return the same outputs dict for the same SITUATIONS inputs)"
tech-stack:
  added: []
  patterns: ["git archive of the pinned commit as VC_ROOT", "child-process-only use of pinned helpers (python3 -I)", "fresh-shell fence walk with printed-literal pasting"]
key-files:
  created:
    - docs/design/lean-v2.15/tools/finalize_capture.py
    - docs/design/lean-v2.15/tools/test_finalize_capture.py
  modified: []
decisions:
  - "Both close routes are walked through the write tail (decisions report, prior-report archive fence, a stand-in REVIEW.md holding only the verdict and stamp lines, state archive fence) so files_archived and state_closed carry real values"
  - "card-first step 3 follows the 2.14.1 prose (new BLOBFILE, recount, new GATEFILE) rather than the older test's reuse of the pre-card BLOBFILE"
  - "The card the owner reads is recorded as a step with id `card` and exit null (read by the model, nothing run)"
metrics:
  duration: "~35 min"
  completed: 2026-11-14
  tasks: 2
  files: 2
---

# Phase 62 Plan 04: Finalize capture harness and the two close routes Summary

This plan adds an offline capture tool. It reads the Finalize instructions and helpers from the exact v2.14.1 commit (dd8e4ab, extracted with `git archive`), walks every bash block in a fresh shell, and produces a normalised, fingerprintable record. The clean-close and card-first routes now reproduce at the pinned commit, and two captures in different temp folders give identical records.

## What was built

- **Pinning.** `materialize(repo, commit, dest)` pipes `git archive <commit> plugins/vibe-check` into `tar -x`, with list arguments and timeouts on both calls. An unknown commit, or one that starts with `-`, raises `UsageError`, and the CLI exits 2.
- **Normalisation.** `NORMALISATION` (six rules, written into every record) replaces the work dir with `<WORK>`, the pinned tree with `<VC_ROOT>`, `vc.` mktemp suffixes with `vc.XXXXXX`, and ISO dates/date-times and 10-digit epoch stamps with `<TIME>`. Stderr is kept only as present or absent. `normalise_outputs` sorts the file-name lists after normalising.
- **Situations.** `SITUATIONS` holds the five ids in the required order. Each has its inputs: fixture, state preparation, head blobs, flags, prior REVIEW.md and owner answers. The output schema (`OUTPUT_KEYS`, `STEP_KEYS`, `TALLY_KEYS`) is defined separately from any driver.
- **Fences.** `FENCE_RE` uses the house definition and finds 18 fences in the pinned `90-finalize.md`, including the indented ones and the one four-backtick block.
- **Driver.** `FenceWalk2141.run(situation_id, vc_root, workdir)` walks clean-close and card-first. Each fence runs through `run_fence`, whose environment holds only PATH, VC_ROOT, TMPDIR and STATE_FILE, with a 60 s timeout. Printed paths are pasted over `"$NAME"` and `"$NAME.`. The driver tallies `commands_run`, `values_carried` and `writes`. The other three ids raise `UsageError` naming the id.
- **Isolation.** State preparation (dismiss-all through the pinned `record_decisions`) and the reading of the REVIEW.md verdict and stamp lines run in `python3 -I -c` child processes. No plugin module is imported in-process; an AST test and the plan's grep both confirm this.
- **Capture.** `capture_one(repo, sid, commit, driver, tmp_root)` materialises the tree, walks the situation, normalises the result and removes its scratch tree on every path. `main capture --repo --out [--commit] [--situation ...]` builds a record on top of it.

### Observed walk results (pinned dd8e4ab)

| Situation | Gate decisions | Report entries | Files archived | state_closed | Tally (commands / values / writes) |
|---|---|---|---|---|---|
| clean-close | `write` | 2 | `.turingmind/state/format-53/capture.json.archived-<TIME>` | true | 8 / 2 / 3 |
| card-first | `outstanding-to-phase-5`, then `write` | 6 | same | true | 17 / 9 / 6 |

## Verification (observed)

- `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_finalize_capture.py`: **40 passed** after Task 2. After Task 1 it was 28 passed.
- RED was observed for both tasks. Task 1's collection failed with `ModuleNotFoundError`. Task 2 had 4 failures and 8 errors before the driver existed.
- `grep -cE "^\s*(import|from) (carry_state|finalize_gate|batch_card)" finalize_capture.py` printed `0`.
- `grep -q "class FenceWalk2141"`: found.
- `git status --porcelain -- plugins`: empty.
- I ran the plugin's `test_finalize_card.py` and this test in one pytest process: 135 passed, with no module mixing.
- I ran the CLI against this worktree. `capture --situation clean-close --situation card-first` exited 0. The default `capture` (all five) exited 2 with `FenceWalk2141 does not walk one-rebuild yet — STOPPING`.
- Mutants were run and each tripped its check:
  - A column-0-only fence reader finds 9 fences and loses the BLOBFILE fence. The test asserts the patched pattern differs from the original.
  - With `normalise` replaced by the identity function, two clean-close captures differ, and the raw temp root shows up in the record.
  - The timeout lock trips on a `subprocess.run` with no timeout.
- I ran no mutant for the no-stray-files check. It is a direct assertion that the temp root holds only the work dir.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Sorting the file lists before normalising made card-first non-deterministic**
- **Found during:** Task 2 GREEN
- **Issue:** The file lists were sorted by raw mktemp names, so the order of `vc.XXXXXX` and `vc.XXXXXX.err` changed from run to run.
- **Fix:** Added `normalise_outputs`, which sorts `files_written` and `files_archived` after normalising.
- **Cost if wrong:** If 62-10 bypasses `normalise_outputs`, its records could differ between runs.
- **Files modified:** finalize_capture.py
- **Commit:** c5f1198

**2. [Rule 3 - Blocking] The plan's import grep matched the child-process code text**
- **Found during:** Task 2 verify
- **Issue:** The `python3 -I -c` code strings contained lines like `import carry_state`. These run in a child process, but the textual grep counted them (count 2, expected 0).
- **Fix:** The child code now loads the module with `importlib.import_module("carry_state")`. The behaviour is the same, and the grep and the AST lock both return clean.
- **Cost if wrong:** None to behaviour; this only changes how the child process names the module.
- **Files modified:** finalize_capture.py
- **Commit:** c5f1198

## Assumption Drift (advisory)

**1. card-first step 3 re-mints BLOBFILE**
- **Found during:** Task 2
- **Planned:** Copy the step sequence of `test_card_route_records_then_writes`, which recounts on the same pre-card BLOBFILE.
- **Actual:** The walk follows the 2.14.1 prose for step 3: a new BLOBFILE, recount, a new GATEFILE, and the gate once on it. The prose forbids reusing the pre-card BLOBFILE, and the newer test `test_post_decision_recount_refingerprints_head` locks that behaviour.
- **Why:** The record should capture what the instructions tell the model to do. With `head_blobs = {}` the counts are the same either way.
- **Cost if wrong:** The card-first tally would be 3 commands, 1 write and 1 carried value lower. Phase 63's helper driver must match whichever sequence is recorded.

**2. Both routes walk the write tail**
- **Found during:** Task 2
- **Planned:** The existing walks stop at the decisions report.
- **Actual:** After the gate returns `write`, the driver also runs the prior-report archive fence, writes a stand-in REVIEW.md, and runs the state archive fence. The stand-in holds only `finalize_gate.APPROVED_LINE` and `REVIEW_FORMAT_STAMP`, because the REVIEW.md prose is written by the model.
- **Why:** Without these steps, `files_archived` and `state_closed` in the fixed schema would always be empty or false, which would make them decorative.
- **Cost if wrong:** If 62-10 or Phase 63 considers the tail out of scope, it can be dropped before the record is committed. No record is committed in this plan.

## Known Stubs

- The `capture` CLI defaults to all five situations, but the driver currently walks only two, so the default exits 2 and names `one-rebuild`. This is intentional: plan 62-10 adds the other three walks, the `verify` subcommand and the committed record.
- The CLI docstring describes `verify`, but the subcommand does not exist yet. It arrives in plan 62-10.

## Threat Flags

None. The executed shell text comes only from `git archive` of the fixed commit. Each fence runs with a four-name environment, inside the temp work dir, with a 60 s timeout. This matches T-62-17, T-62-20, T-62-21 and T-62-55.

## TDD Gate Compliance

- Task 1: `91db0eb` test → `943b5b4` feat
- Task 2: `33d855b` test → `c5f1198` feat

## Self-Check: PASSED

- FOUND: docs/design/lean-v2.15/tools/finalize_capture.py
- FOUND: docs/design/lean-v2.15/tools/test_finalize_capture.py
- FOUND commits: 91db0eb, 943b5b4, 33d855b, c5f1198
