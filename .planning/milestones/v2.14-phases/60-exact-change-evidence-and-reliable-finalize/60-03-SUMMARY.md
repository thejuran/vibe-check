---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 03
subsystem: vibe-check Finalize (fresh-shell path reliability)
tags: [printed-path, fresh-shell-walk, retry-once, D-07, D-08, D-09, FINL-01, FINL-02, 999.25]
requires:
  - "60-01 TestFinalizeFreshShellWalk red walk + 999.25 / Pitfall 6 repros (RED SHA ce9f8b8)"
provides:
  - "90-finalize.md: BLOBFILE= mktemp/print fence (step 1), GATEFILE= mktemp/print fence, gate reads < \"$GATEFILE\" with stderr kept in <GATEFILE>.err"
  - "90-finalize.md: rebuild-once / refused-step / write-boundary paragraph with the exact stop sentence"
  - "Literal-reuse sentences at the counts fence, the rows fence and the step-3 re-run"
  - "TestFinalizeFreshShellWalk: write route, card route (parse -> DECFILE -> record-decisions -> recount -> write), retry, stale earlier attempt, malformed GATEFILE (7 tests)"
  - "Module predicates: retry_rule_holds, refused_rule_holds, write_boundary_holds, check_file_refs_created, no_cross_call_gate_input; check_printed_paths widened to the whole file"
affects: [60-05]
tech-stack:
  added: []
  patterns: ["fresh-shell fence walk with a closure assertion (every path read was minted by a walked fence)", "owner-view predicate run on real text and on a redirect-removal mutant"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "The prose fix b8fb21a turns the 60-01 walk green; the full walk set is green at fd8c1b9 and the widened locks land in 53b35ed (green SHAs for 60-05's ledger: V8 and V9 -> b8fb21a / fd8c1b9)"
  - "finalize_gate.py is unchanged: on empty or malformed input it still prints a traceback, which the fence keeps in <GATEFILE>.err. 60-05 residual R1 is helper-side only and never reaches the owner"
  - "The fences' stop sentence uses single-quoted echo so the backticks around --finalize print literally (the plan's escaped-backtick form would not match the exact sentence)"
  - "PRIORROWSFILE is the one fence-read path besides STATE_FILE that this file does not mint: it is bound to the fix-loop card's printed CARDROWSFILE= path, and the lock requires that binding sentence"
metrics:
  duration: "~30 min"
  completed: 2026-10-29
  tasks: 3
  files: 2
requirements: [FINL-01, FINL-02]
---

# Phase 60 Plan 03: Reliable Finalize from fresh shells Summary

Finalize now prints every temp path it creates and reuses each one only as that printed literal. Step 1 mints and prints `BLOBFILE=`. The gate reads a printed `GATEFILE=` in place of the cross-call `$FINALIZE_GATE_INPUT_JSON`, and its traceback goes to `<GATEFILE>.err`. A missing path or a failed step gets one rebuild with a new blob file, then stops with one plain sentence. A fresh-shell walk over the real fences now reaches `write` and the decisions report on both routes. This closes 999.25 and Pitfalls 5 and 6.

## Commits

| # | Task | Commit |
|---|------|--------|
| 1 | 90-finalize.md: BLOBFILE / GATEFILE printed-path fences, literal reuse at counts / rows / step-3 re-run, rebuild-once and refused-step rules | `b8fb21a` |
| 2 | Fresh-shell walk green on both routes; retry, stale-attempt and malformed-GATEFILE walks; retry / refused / write-boundary prose locks | `fd8c1b9` |
| 3 | Printed-path lock over the whole file; `check_file_refs_created`; `no_cross_call_gate_input`; D-09 mutants | `53b35ed` |

## Verification (observed)

- Task 1 automated verify -> `PROSE_OK` and `21 passed, 56 deselected, 90 subtests passed`. Greps: `FINALIZE_GATE_INPUT_JSON` 0, stop sentence 3, `2>"$GATEFILE.err"` 1, `are not shown` 1, BLOBFILE / GATEFILE mktemp 1 each, `head-blobs "$BLOBFILE"` 2, `same \`BLOBFILE=\` literal this attempt printed` 1, the only-state-write sentence 1 (unchanged).
- `pytest -q test_mktemp_template.py` -> `4 passed`.
- Task 2 verify (`-k "TestFinalizeFreshShellWalk or retry_rule or refused_rule or write_boundary or malformed_gatefile"`) -> `13 passed, 70 deselected, 11 subtests passed`. `-k TestFinalizeFreshShellWalk` -> `7 passed`.
- The new tests are not decorative. With the pre-fix `90-finalize.md` restored temporarily, the same selection gave `18 failed, 5 passed`: every walk, every holds test and the write-boundary mutants failed. The file was then restored with `git checkout -- <file>`.
- Malformed GATEFILE (empty, and `not json`): exit 1, empty stdout, stderr exactly `I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived.`, no `Traceback` or `json` on either stream, and `<GATEFILE>.err` contains `Traceback`. Removing the redirect puts `Traceback` on the owner's stderr, and the mutant subtest catches it.
- Task 3: `pytest -q test_finalize_card.py` -> `87 passed, 129 subtests passed`. `pytest -q test_fix_loop_card.py` -> `140 passed, 137 subtests passed`. Against the pre-fix prose, `check_file_refs_created` returns `['BLOBFILE read but never created by a fence']` and `no_cross_call_gate_input` returns both problems.
- `pytest -q test_decision_continuity.py -k TestRepro60Record` -> `3 passed` (fixture names kept).
- Full suite (`cd plugins/vibe-check/scripts && pytest -q`): **4 failed, 3737 passed, 4924 subtests passed in 168.47s**. The 4 failures are exactly the intentional `TestCoordinateSpaces60` probes that 60-04 fixes. The Finalize walk red from 60-01 is green.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Gate-input sentence does not repeat the `{"flags": {…}}` literal**
- **Found during:** Task 1
- **Issue:** `seven_key_flags_holds` requires exactly one backticked `{"flags": {…}}` literal in the file. The plan's wording "Write the one-key `{"flags": {…}}` object" added a second one and failed `test_seven_key_flags`.
- **Fix:** Reworded to "Write the one-key object above (`flags` holding the seven keys) to the printed `GATEFILE=` path".
- **Cost if wrong:** None to behaviour. Only the wording differs.
- **Files modified:** plugins/vibe-check/phases/shared/90-finalize.md
- **Commit:** b8fb21a

**2. [Rule 1 - Bug] The fence walker leaked `.err` into the scripts directory**
- **Found during:** Task 1 commit
- **Issue:** The cross-call test runs the gate fence with `"$GATEFILE"` left unsubstituted. The new `2>"$GATEFILE.err"` then resolves to `.err` in the test's cwd, which is `scripts/`.
- **Fix:** Deleted the stray file. `_run_fresh` now runs every fence with `cwd` set to its scratch tmpdir.
- **Cost if wrong:** Low. Without the fix, a stray untracked file appears after each test run.
- **Files modified:** plugins/vibe-check/scripts/test_finalize_card.py
- **Commit:** fd8c1b9

**3. [Rule 3 - Mechanics] The card route walks the parse fence to produce DECFILE**
- **Found during:** Task 2
- **Issue:** The prose's DECFILE fence copies `payload` from `"$PARSEFILE"`, so `_mint("DECFILE")` cannot run alone. The plan had the payload written by hand.
- **Fix:** The walk writes the owner's answer to the printed ANSWERFILE (`dismiss <every row> -- walk`), runs the real parse fence (PARSEFILE), then runs the real DECFILE fence with the PARSEFILE literal. The test asserts that the payload hashes equal the rows' hashes. That makes two more real fences part of the walk.
- **Cost if wrong:** Low. The walk is more faithful than a hand-built payload.
- **Commit:** fd8c1b9

**4. [Rule 1 - Plan expectation] The retry case asserts a non-zero exit, not 2**
- **Found during:** Task 2
- **Issue:** This is the same fact 60-01 recorded. The helper exits 2, but the counts fence's `else` branch exits 1.
- **Fix:** `assertNotEqual(rc, 0)` plus `REASON_HEAD_BLOBS` on stderr and empty stdout.
- **Cost if wrong:** None.
- **Commit:** fd8c1b9

**5. [Rule 2 - Correctness] `check_file_refs_created` names one external path**
- **Found during:** Task 3
- **Issue:** The Stale card twin fence reads `"$PRIORROWSFILE"`. That path is minted by the fix-loop card (`CARDROWSFILE=`), not by this file, so the plan's rule (everything except STATE_FILE is minted here) failed on the real text.
- **Fix:** `EXTERNAL_FILE_REFS` exempts STATE_FILE and PRIORROWSFILE. The PRIORROWSFILE exemption holds only while its binding sentence ("bind `$PRIORROWSFILE` to the path the fix-loop card's rows fence printed after `CARDROWSFILE=`") is present. A mutant that drops that sentence trips the lock.
- **Cost if wrong:** Low. If a future edit adds another file read from outside, the lock fails loudly and names it.
- **Commit:** 53b35ed

**6. [Rule 1 - Plan template] The stop sentence in the fences uses single-quoted echo**
- **Found during:** Task 1
- **Issue:** The plan's fence template escapes the backticks inside double quotes. In the file text that reads `\`--finalize\``, which does not match the exact stop sentence the acceptance grep counts (>= 3).
- **Fix:** `echo 'Finalize stopped — nothing was written or archived; run `--finalize` again.' >&2`. Inside single quotes the backticks print literally, and the file holds the exact sentence 3 times.
- **Cost if wrong:** None.
- **Commit:** b8fb21a

## TDD Gate Compliance

The RED gate for this plan is 60-01's committed red walk (`ce9f8b8`, `test_walk_reaches_counts_gate_report`). Task 1 (`feat`, b8fb21a) turned it green. The Task 2 and Task 3 tests were written after the prose fix, so they passed on first run. Their RED evidence is the temporary run against the pre-fix prose (18 failed) and the tripping mutants. They have no separate failing `test(...)` commit.

## Known Stubs

None.

## Threat Flags

None. T-60-09 is covered by the stale-attempt walk and the retry-rule prose lock with mutants. T-60-10 is covered by `write_boundary_holds` (three mutants) and by the failure-path walks asserting empty stdout. T-60-11 is covered by the malformed-GATEFILE owner-view test and the redirect-removal mutant. T-60-12 is unchanged: `helper_flag_violations` still holds. The walk env is exactly PATH, VC_ROOT, TMPDIR and STATE_FILE, every scratch dir is removed by `addCleanup`, and no subprocess uses `shell=True`.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/shared/90-finalize.md, plugins/vibe-check/scripts/test_finalize_card.py
- FOUND commits: b8fb21a, fd8c1b9, 53b35ed
