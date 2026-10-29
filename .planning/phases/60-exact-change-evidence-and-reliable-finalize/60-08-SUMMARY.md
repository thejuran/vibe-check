---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 08
subsystem: finalize
tags: [finalize, rebuild-once, gatefile, gap-closure, mutation-tests, fresh-shell-walk]
gap_closure: true
requires: [60-03, 60-05]
provides: [GATEFILE trigger + re-mint + rewrite-from-rebuilt-counts in the rebuild-once rule, RETRY_NEEDLES GATEFILE needles, fresh-shell GATEFILE failure-then-retry walk]
affects: [60-09]
tech-stack:
  added: []
  patterns: [prose substring lock with presence-asserting mutants, fresh-shell fence walk with printed-path literals]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "Finalize's one automatic rebuild re-runs the existing gate-input mktemp fence (a NEW GATEFILE=) and writes the flags from the rebuilt COUNTS_JSON; no second GATEFILE fence is added"
  - "A GATEFILE= from an earlier attempt or session is never reused (mirrors the BLOBFILE rule)"
requirements: [FINL-02]
metrics:
  duration: ~5min
  completed: 2026-10-29
  tasks: 2
  files: 2
red_sha: f100185
green_sha: c0ece7e
---

# Phase 60 Plan 08: Finalize rebuild re-mints GATEFILE Summary

Finalize's "One automatic rebuild, then stop" rule now names a missing or empty `GATEFILE=` as a trigger, and on the single retry re-runs the gate-input fence for a NEW `GATEFILE=`, writes the seven-key flags from the REBUILT `$COUNTS_JSON`, and never reuses an earlier attempt's or session's `GATEFILE=`. A fresh-shell walk proves recovery from an empty gate input and shows that re-running the gate on the stale file fails the same way.

## Ledger SHAs (for 60-09)

- **RED SHA:** `f100185` — `test(60-08): red — rebuild-once rule must re-mint GATEFILE; fresh-shell GATEFILE failure-then-retry walk`
- **GREEN SHA:** `c0ece7e` — `fix(60-08): Finalize rebuild re-mints GATEFILE and rewrites the flags from the rebuilt counts`

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Red: GATEFILE needles, mutants, fresh-shell GATEFILE failure-then-retry walk | f100185 | plugins/vibe-check/scripts/test_finalize_card.py |
| 2 | Green: rebuild-once paragraph names the GATEFILE trigger, re-mint and rewrite | c0ece7e | plugins/vibe-check/phases/shared/90-finalize.md |

## Observed results

**At RED (f100185):**
- `pytest -q -p no:cacheprovider test_finalize_card.py -k "retry or gatefile"` -> `5 failed, 3 passed, 83 deselected, 7 subtests passed`.
  - Failed: `test_retry_rule_holds`, `test_mutant_retry_rule` (both new GATEFILE subtests: `_mutant` presence assertion fails on the old text), `test_retry_mints_new_gatefile_after_gate_input_failure` (only at the final `assert_holds(retry_rule_holds)` — 4 missing needles; every walk step before it passed), `test_gatefile_missing_path_is_a_named_trigger`.
  - Passed: `test_retry_mints_new_blobfile_after_missing_path`, `test_malformed_gatefile_shows_only_stop_sentence` (unchanged, as planned).
- Full file: `6 failed, 85 passed, 130 subtests passed` — the sixth is `test_stale_earlier_attempt_file_does_not_govern` (it calls `retry_rule_holds`; not matched by the `-k` filter).
- `len(RETRY_NEEDLES)` = 9.

**At GREEN (c0ece7e):**
- `pytest -q -p no:cacheprovider test_finalize_card.py` -> `89 passed, 132 subtests passed`.
- `pytest -q -p no:cacheprovider test_pause_batching.py test_nv_render.py test_fix_loop_card.py` -> `199 passed, 377 subtests passed`.
- `-k "retry or gatefile or stale"` -> `14 passed, 19 subtests passed` (both GATEFILE mutants found their sentence on the real text and removing it tripped the lock).
- `git diff 2f84d2e --numstat -- 90-finalize.md` -> `1 1` (one line changed). `grep -cF 'GATEFILE=$(mktemp'` -> 1 (no second fence). The rebuild paragraph is still one line and carries all four new needles plus the BLOBFILE never-reuse, "A second failure stops.", refused-step and write-boundary sentences (each grep -cF = 1).

## Deviations from Plan

None in behavior. Two notes:
- The plan's acceptance grep `grep -c 'GATEFILE=$(mktemp'` prints 0 on macOS BSD grep (the `$` is treated as a regex anchor); the fixed-string form `grep -cF` prints 1. Cost if wrong: none — it is a check-command quirk, the fence count is 1.
- The walk's flags come from `counts2` via `_flags`, and the GATEFILE mutant subtest labels are "earlier attempt's GATEFILE may be reused" and "rebuild does not re-mint GATEFILE". The walk's documenting subtest is labelled "old rule: same GATEFILE reused fails identically".

## Known Stubs

None.

## Threat Flags

None — prose and test changes only; T-60-21/T-60-22 mitigated as planned, T-60-23/T-60-24 unchanged and their locks still green.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md, plugins/vibe-check/scripts/test_finalize_card.py
- FOUND commits: f100185, c0ece7e
