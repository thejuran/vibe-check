---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 03
subsystem: test-suite / instruction lint
tags: [xvar, cross-call, lint, mutants, tdd]
requires: []
provides:
  - "test_cross_call_vars.py: bash_fences, assignments, reads, printed_names, cross_call_reads, flagged_pairs, phase_files, check_exceptions, EXCEPTIONS, KNOWN_LIMITS"
affects: [63-04, 63-06, 63-10]
tech-stack:
  added: []
  patterns: ["whole-tree walk (test_mktemp_template)", "LockCase assert_holds/assert_trips", "set-equality exceptions (shrink-only by name)"]
key-files:
  created:
    - plugins/vibe-check/scripts/test_cross_call_vars.py
  modified: []
decisions:
  - "A reassignment earlier on the same line counts as before the read only when a command separator (; && || then do) sits between; X=$(f \"$X\") and X=1 cmd \"$X\" stay reads-before-assignment"
  - "Cross-call check flags exactly six (file, NAME) pairs today, held as EXCEPTIONS X1-X6"
metrics:
  duration: "~35 min"
  completed: 2026-11-14
requirements: [XVAR-01]
---

# Phase 63 Plan 03: Cross-call variable check Summary

One stdlib-only test module scans every Bash fence of all 27 phase files and fails when a fence reads a variable that an earlier fence of the same file set without printing it. Today's six flagged places sit on a named, shrink-only exceptions list. Mutants (a), (c), (d) and (h) each trip the check.

## Flagged pairs (EXCEPTIONS)

| Id | File | Variable | Sites (setter fence, reader fence) |
|----|------|----------|-------|
| X1 | phases/review/00-scope.md | PHASE_DIR | (7,8), (7,9) |
| X2 | phases/review/05-state.md | LEGACY_STATE_FILE | (1,2) |
| X3 | phases/review/05-state.md | STATE_FILE | (1,2), (1,3), (1,4), (1,5) |
| X4 | phases/review/06-config.md | CODEX_FLAG_VAL | (2,4) |
| X5 | phases/review/06-config.md | CONFIG_REPO_ROOT | (0,4) |
| X6 | phases/review/06-config.md | MIN_CONFIDENCE_FLAG_VAL | (1,4) |

10 sites in 6 pairs, exactly what the research probe found. **No difference from the six expected pairs.** (A first draft of the scanner also flagged `phases/review/07-first-run.md` `GREPO`. That was a scanner false flag, not a real case: line 18 sets and reads it on one line, `GREPO=$(…); mkdir -p "$GREPO/…"`. It was fixed in the scanner before the exceptions were set. See Deviations.)

Walk floor observed: 27 files, 91 Bash fences. Indented and four-backtick fences are both present and both scanned. The fence list on live `90-finalize.md` is equal, body for body, to `step_count.fences`.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Scanner: fences, assignments, reads, printed names, the cross-call rule | 9d5e2f9 (test, RED), cb7c8b0 (feat, GREEN) |
| 2 | Whole-tree check, named exceptions, live-file mutants | 1fda4cc (test, RED), f2c34f0 (feat, GREEN) |

## Verification (observed)

- `pytest -q -p no:cacheprovider test_cross_call_vars.py`: 44 passed, 73 subtests passed.
- Task 2 assertion: `flagged_pairs()==set(EXCEPTIONS)`, unique ids, `phase_files()` gives 27 files. Printed `6 pairs [...]`.
- `git diff --quiet dd8e4ab… HEAD -- plugins/vibe-check/phases` exits 0. No instruction file was changed.
- Full suite `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`: 4373 passed, 1 skipped, 5 failed. All 5 failures are subtests of the three `test_replay.py::TestPhase53SameLineRegressionCases` tests already listed in `.github/ci-left-out-tests.txt`. They need local-only transcripts that a linked worktree lacks. The 1 skip is the existing `test_replay.py:281` transcript skip. This plan added no skip decorator.
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`: "33 shipped .py files; third-party imports: none", exit 0.
- RED runs failed on NameError for the missing names, as intended. `TestImportSet` passed at RED because it does not depend on the scanner.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Same-line reassignment produced a false flag**
- **Found during:** Task 1, probing the live tree before the GREEN commit.
- **Issue:** The behavior list only said "assigned on an earlier line", so `GREPO=$(…); mkdir -p "$GREPO/…"` in `07-first-run.md` was flagged although it is safe.
- **Fix:** Views are now column-aligned. An assignment earlier on the same line counts as before the read when a command separator (`;`, `&&`, `||`, `then`, `do`) sits between them. `X=$(cmd "$X")` and `X=1 cmd "$X"` remain violations. Tests were added for both directions. These tests landed in the GREEN commit, not the RED one.
- **Cost if wrong:** A real cross-call read hidden behind a same-line separator in an unusual form could be missed. The cases are narrow and pinned by tests.
- **Commit:** cb7c8b0

**2. [Rule 3 - Blocking] Verify commands split**
- The harness refuses `git` inside `bash -c`/`bash -s` in this worktree, so each `<verify>` was run as plain commands with the same content. Results are above.
- **Cost if wrong:** none. The same checks ran.

## Known Stubs

None.

## TDD Gate Compliance

`test(63-03)` 9d5e2f9 → `feat(63-03)` cb7c8b0 → `test(63-03)` 1fda4cc → `feat(63-03)` f2c34f0. RED came before GREEN for both tasks.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_cross_call_vars.py
- FOUND commits: 9d5e2f9, cb7c8b0, 1fda4cc, f2c34f0
