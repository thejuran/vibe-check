---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 01
subsystem: finalize
tags: [finalize, fingerprints, git, parity, mutants]
requires: []
provides:
  - "finalize_inputs.head_blobs(state, cwd=None) and finalize_inputs._git(args, cwd)"
  - "63-COUNTS.md ## Before (92 steps / 68 in 90-finalize.md / 136114 bytes at dd8e4ab and 2a468a8)"
affects: [63-02, 63-05]
tech-stack:
  added: []
  patterns: ["fail closed by omission", "validate (PATH_RE then guard.contained) before any git argv", "source-substituted mutant modules via importlib"]
key-files:
  created:
    - plugins/vibe-check/scripts/finalize_inputs.py
    - plugins/vibe-check/scripts/test_finalize_inputs.py
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-COUNTS.md
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/deferred-items.md
  modified:
    - .github/scripts/test_stdlib_only.py
decisions:
  - "head_blobs keeps 2.14.1 parity in a subdirectory cwd, which fingerprints a file with an uncommitted edit (reproduced); owner checkpoint raised under D-06 before any change"
  - "git stdout decoded with os.fsdecode so a non-UTF-8 repo path cannot raise"
metrics:
  duration: "about 45 min"
  completed: 2026-11-14
---

# Phase 63 Plan 01: Starting figures and HEAD fingerprint helper Summary

The 2.14.1 Finalize figures were recounted straight from the commits (92 steps, 68 in `90-finalize.md`, 136114 bytes, unchanged at the branch base), and `finalize_inputs.head_blobs` now works out the HEAD fingerprints exactly as the 2.14.1 instructions do: validate each file name before git, three argv-list git calls in the session cwd, keep a file only when all three exit 0.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Record the starting figures | f0dcbdf | 63-COUNTS.md, deferred-items.md |
| 2 (RED) | Failing tests for HEAD fingerprints | 2de7214 | test_finalize_inputs.py |
| 2 (GREEN) | HEAD fingerprint helper | 78fbdeb | finalize_inputs.py, test_finalize_inputs.py, test_stdlib_only.py |

## Verification (observed)

- Task 1 verify command: printed `OK`.
- Tool output at dd8e4ab and 2a468a8: 92 / 68 / 136114 at both; `git diff --quiet dd8e4ab HEAD -- plugins/vibe-check/phases` exit 0; `finalize baseline matches (5 situations)`; `baseline holds`; 10 of 10 MANIFEST fingerprints recomputed and matching.
- Task 2 verify command: printed `OK` (finalize_inputs + finalize_gate + carry_state tests pass, stdlib test 21 passed, `34 shipped .py files; third-party imports: none`, no `shell=`, no `validate_paths(`).
- `test_finalize_inputs.py`: 38 passed, 19 subtests passed; 5 tests named `test_mutant_*`.
- `git diff --quiet 2a468a8 HEAD -- carry_state.py finalize_gate.py phases`: exit 0.
- After the change, `finalize_capture.py verify` still prints `finalize baseline matches (5 situations)`.
- Full suite after the change: `5 failed, 4367 passed, 1 skipped, 5325 subtests passed` (before: 5 failed, 4329 passed; the 38 added tests account for the difference; the 5 failures are the same pre-existing `test_replay.py` ones).

## Self-Check: PASSED

Files present: finalize_inputs.py, test_finalize_inputs.py, 63-COUNTS.md, deferred-items.md, this SUMMARY. Commits present: f0dcbdf, 2de7214, 78fbdeb.

## D-06 gaps

Each is a named parity test; the helper behaves as 2.14.1 and could be stricter.

- `test_gap_leading_dash_path_is_fingerprinted` — a file name starting with `-` (`-x.ts`) passes PATH_RE and containment and is fingerprinted. Harmless as argv (`HEAD:`-prefixed and after `--`), but a stricter helper could refuse it.
- `test_gap_at_pass_true_matches_pass_one` — a verdict with `at_pass: true` matches pass number 1 (JSON `true == 1` under Python equality, as a model reading the rule would also treat it loosely).
- `test_gap_subdirectory_cwd` — **reproduces as a wrong close; owner checkpoint raised.** With the session cwd in a subdirectory (`<repo>/sub`) and a root-relative file name (`sub/c.ts`), the three 2.14.1 calls run as plain git from that subdirectory give exit codes `[0, 0, 0]` both for the clean file and for the same file with an uncommitted edit. `git rev-parse HEAD:sub/c.ts` reads root-relative, but the pathspec after `--` in the two `git diff` calls is read relative to the cwd (`sub/sub/c.ts`), matches nothing and exits 0. So 2.14.1 fingerprints a dirty file, and a fix-obsolete verdict whose `verified_blob` equals the HEAD blob is honoured while the working tree has changed. The helper matches this exactly (reproduction: `{'sub/c.ts': 'ae93045…'}` for both cases). Not changed, per D-06: the owner decides under the four-class rule.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two of my own RED tests were wrong**
- **Found during:** Task 2 GREEN
- **Issue:** `git rev-parse HEAD:<missing>` echoes its argument to stdout, so asserting empty stdout was wrong; the root-query mutant used a state with no `fix_verdicts` key, which returns `{}` before the mutated line runs, so the mutant could not trip.
- **Fix:** the runner test now asserts git's stderr text is absent from the return; the mutant (and the no-verdict tests) also use a state whose only verdict is at an earlier pass.
- **Cost if wrong:** a mutant that never trips would be a decorative guard; now checked to trip.
- **Files modified:** test_finalize_inputs.py
- **Commit:** 78fbdeb

**2. [Rule 2 - Correctness] git stdout decoded with `os.fsdecode`**
- **Found during:** Task 2
- **Issue:** `text=True` would raise `UnicodeDecodeError` on a repo path that is not valid UTF-8, breaking "never raises".
- **Fix:** capture bytes and decode with `os.fsdecode`.
- **Cost if wrong:** none for valid paths; an odd path still fails containment and is omitted.
- **Commit:** 78fbdeb

**3. [Rule 2 - Correctness] Malformed rows are skipped, not fatal**
- **Found during:** Task 2
- **Issue:** indexing every row by `stable_hash` would let one hashless row empty the whole map; the model applying the 2.14.1 rule would simply look up its hash.
- **Fix:** non-dict or hashless rows are skipped when indexing; the first row with a hash wins.
- **Cost if wrong:** a file fingerprinted that a stricter reading would drop; the gate still re-checks `verified_blob`.
- **Commit:** 78fbdeb

### Out of scope

- `test_replay.py::TestPhase53SameLineRegressionCases` has 5 failures in this worktree at the untouched branch base; logged in `deferred-items.md`. None involves Finalize.

## Known Stubs

None. (`json` is imported but unused, as the plan's exact import set requires; plan 63-02 adds the command line that uses it.)

## Threat Flags

None beyond the plan's register: T-63-01..04 are mitigated (argv lists, `HEAD:` prefix and `--`, PATH_RE then containment with mutants, `timeout=GIT_TIMEOUT`, stderr dropped).

## TDD Gate Compliance

`test(63-01)` 2de7214 precedes `feat(63-01)` 78fbdeb. RED was a collection error (module absent).
