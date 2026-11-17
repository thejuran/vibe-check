---
phase: 66-close-out-freshness
plan: 01
subsystem: finalize / close-out
tags: [finalize, close-out, freshness, reproduction, differential, tdd-red]
requires: []
provides:
  - closeout_fresh.py interface contract (GIT_TIMEOUT, _NEARBY_LINES, NEXT_REVIEW_AGAIN, CAUSES, REV_FLAGS, Unverifiable, stale_decisions)
  - test_closeout_fresh.py: FreshCase base, materialize_v215, run_old / run_new_cli / run_new, 999.40 repro grid (RED), unchanged controls (GREEN both sides)
affects: [66-03 (closeout_fresh implementation), 66-04 (wiring into finalize_inputs._run)]
tech-stack:
  added: []
  patterns: [two-sided differential against the literal d5acc19 helper materialized via git show, interface-first contract module]
key-files:
  created:
    - plugins/vibe-check/scripts/closeout_fresh.py
    - plugins/vibe-check/scripts/test_closeout_fresh.py
  modified: []
decisions:
  - "V215_MODULES is the six named siblings plus batch_parse.py (batch_card imports it at d5acc19); found by an AST scan of every import, including non-top-level ones"
  - "Each repro/control subtest builds its own repo (case<N>/repo) so subtests never share a working tree"
  - "run_both feeds byte-identical argv to both sides (same fingerprint-file path, truncated to empty before each run)"
metrics:
  duration: ~20m
  completed: 2026-11-17
  tasks: 2
  files: 2
---

# Phase 66 Plan 01: 999.40 reproduction and v2.15 differential (RED) Summary

Committed the 999.40 wrong-keep reproduction against the literal 2.15.0 helper (`d5acc19`, materialized from git history) plus the `closeout_fresh.py` interface contract. The candidate's refusal assertions fail today, as intended. The unchanged-code controls give byte-identical output from both helpers.

## What was built

**Task 1: `closeout_fresh.py` contract (commit f4b65f17).** This module holds only the contract. Its docstring covers the cause vocabulary (D-01), the reviewed-tree baseline (D-04), the window (D-05), deleted (D-06), any byte change (D-07), untracked (D-09), the swapped-prefix reason, and the "I/O: stdlib imports exactly {os, subprocess, sys}" line. It exports the exact names in the plan's `<interfaces>` block, and the sibling imports (`carry_state`, `diff_ranges`, `worktree_snap`, `fixcommit.PATH_RE`) are in place. `stale_decisions` returns `[]` and makes no git call.

**Task 2: `test_closeout_fresh.py` (commit 369996e8).**
- `materialize_v215(case)` reads each of the 7 V215_MODULES with `git show d5acc19:...` and writes it into a `mkdtemp`. Git runs under the parity grid's `clean_env` with stdin from /dev/null and a 60 s timeout. `addCleanup(shutil.rmtree)` removes the temp dir. If history is shallow the read fails with an `AssertionError` that says so.
- `run_old` and `run_new_cli` use the same subprocess recipe: same env, stdin, 120 s timeout and raw `(returncode, stdout bytes)`. `run_new` runs in-process and is used only for the candidate's parsed-JSON shape checks.
- `FreshCase.repro_state` commits src/a.py (60 lines), runs `tdc.pass1(conf=95, kind=...)`, and sets the real `head_sha` and `reviewed_tree = HEAD^{tree}`. It writes the state outside the repo, then edits the chosen line without committing.
- Every run checks that the state file's sha256 and the repo's file list are unchanged.

## Verification (observed)

| Command | Result |
|---|---|
| Task 1 python contract assertions | `ok` |
| `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | exit 0, "35 shipped .py files; third-party imports: none" |
| `pytest -q test_closeout_fresh.py -k "repro_999_40_old_helper or differential"` | 3 passed, 19 subtests passed (6 old-helper + 6 controls + 7 materializer) |
| `pytest -q test_closeout_fresh.py -k repro_999_40_candidate_refuses` | FAILS as intended: 6 subtests failed, each `AssertionError: 'write' != 'refuse'` at the action assertion (no ImportError or other exception) |
| Plan's combined `<verify>` line | exit 0 |
| `pytest -q test_finalize_inputs.py` | 124 passed, 201 subtests passed |
| Acceptance greps | `def run_new_cli` = 1; `d5acc19` = 8; `addCleanup(shutil.rmtree` = 1; no `git init`; `run_new(` used only by `run_new_case` (candidate shape test), never in a differential |

**RED status:** the candidate test fails because `stale_decisions` is still the `[]` contract and `finalize_inputs._run` does not call it yet. GREEN is planned for 66-03 (module) and 66-04 (wiring).

## TDD Gate Compliance

- RED gate: `test(66-01)` commit 369996e8 exists. It fails for the intended reason.
- GREEN gate: deferred to 66-03/66-04 by design. This is a RED-only plan, and tdd.md does not fault a missing GREEN here.
- Ordering note: the `feat(66-01)` contract commit (f4b65f17) comes BEFORE the `test(66-01)` commit, because the plan puts the interface first. It adds no behaviour (`return []`), so it is not a GREEN commit.

## Deviations from Plan

**1. [Rule 2 - CLAUDE.md/executor rule] No process metadata in product code**
- **Found during:** Task 1
- **Issue:** The plan asked for the comment `skeleton (66-01); behaviour lands in 66-03` in `stale_decisions`. The executor rules forbid phase/plan numbers in product source.
- **Fix:** The comment now describes behaviour: `contract only: no freshness check yet, every decision is kept`.
- **Cost if wrong:** A later plan grepping for "skeleton (66-01)" would not find it (none of 66-03/66-04 does, per their plans).
- **Commit:** f4b65f17

**2. [Rule 1 - Acceptance conflict] Reworded the `_NEARBY_LINES` comment**
- **Found during:** Task 1
- **Issue:** The plan's comment text "this module may not import score" made the acceptance check `grep -n "import score"` print a line.
- **Fix:** Reworded it to "this module never loads the scorer, so a lock test in test_closeout_fresh.py pins the two values together". The intent is unchanged.
- **Cost if wrong:** None; it is wording only.
- **Commit:** f4b65f17

**3. [Rule 3 - Blocking] Read `git()` output from `.stdout`**
- **Found during:** Task 2
- **Issue:** The plan's recipe wrote `git(repo, "rev-parse", "HEAD").strip()`, but `gitfixture.git` returns a `CompletedProcess`.
- **Fix:** Used `.stdout.strip()`.
- **Cost if wrong:** None.
- **Commit:** 369996e8

**4. [Rule 2] V215_MODULES has 7 entries, not 6**
- **Found during:** Task 2
- **Issue:** At d5acc19, `batch_card.py` imports `batch_parse`. An AST scan of every import (including ones inside functions) found no other non-stdlib sibling.
- **Fix:** Added `batch_parse.py`, as the plan's "transitively" instruction requires.
- **Cost if wrong:** Without it the old helper would fail with ImportError and the differential would compare a crash.
- **Commit:** 369996e8

## Known Stubs

- `plugins/vibe-check/scripts/closeout_fresh.py` `stale_decisions` returns `[]`. This is intentional: the plan delivers the contract only, so the RED test can fail. The real implementation comes in 66-03 and the wiring in 66-04.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/closeout_fresh.py
- FOUND: plugins/vibe-check/scripts/test_closeout_fresh.py
- FOUND: f4b65f17 (feat(66-01))
- FOUND: 369996e8 (test(66-01))
