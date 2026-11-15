---
phase: 63-finalize-extraction-and-cross-call-variable-check
verified: 2026-11-15T23:15:00Z
status: gaps_found
score: 4/5 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
gaps:
  - truth: "Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline"
    status: partial
    severity: blocking
    reason: "One input class gives a different gate decision from 2.14.1 and is not on the accepted list. For a finding in a top-level file whose name starts with `-` (for example `-x.ts`) that carries a last-pass fix-obsolete verdict on unchanged code, 2.14.1 leaves the finding open (gate `outstanding-to-phase-5`, nothing written); the new helper closes it and the gate returns `write` (APPROVED). At 2.14.1 the instructions ran `python3 \"$GUARD_PY\" --root … --path \"<file>\"` and required exit 0; that command exits 2 for a name starting with `-` (argparse reads it as an option), so the file was left out, fail closed. The helper calls `guard.contained()` in-process, which accepts the name. The records state the opposite: 63-REMOVAL-LEDGER.md 'Input gaps carried', 63-RESULT.md 'Input gaps carried' and 63-01-SUMMARY.md all say the helper 'behaves as 2.14.1 does' here. The named parity test asserts only the helper's own output and never runs the 2.14.1 command, so it cannot detect the difference. Reproduced end to end on a real temporary repo (control file `x.ts`: identical on both sides; `-x.ts`: 2.14.1 counts [1,0,0] gate `outstanding-to-phase-5`, helper counts [0,0,0] gate `write`), on Python 3.9.6 and 3.14.5. Everything else under this truth verified."
    artifacts:
      - path: "plugins/vibe-check/scripts/finalize_inputs.py"
        issue: "`_head_blobs` line 173 validates with `PATH_RE.match(f)` and `guard.contained(root, f)`; neither refuses a leading `-`, which the 2.14.1 `guard.py` command line did"
      - path: "plugins/vibe-check/scripts/test_finalize_inputs.py"
        issue: "`TestParityGaps::test_gap_leading_dash_path_is_fingerprinted` is labelled a 2.14.1 parity test but compares against nothing from 2.14.1"
      - path: ".planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-RESULT.md"
        issue: "'Input gaps carried' row 1 tells the owner this is the same as 2.14.1; it is not, so the owner's 'go' did not accept it as a difference"
    missing:
      - "Either: leave a file whose name starts with `-` out of the fingerprints (matching 2.14.1), with a test that runs the 2.14.1 guard command on the same name and a mutant; or: an owner acceptance of this difference by name, recorded as an override here and corrected on the result page and in the ledger"
      - "Correct the three records that say this case matches 2.14.1"
---

# Phase 63: Finalize extraction and cross-call variable check — Verification Report

**Phase Goal:** Finalize's mechanical steps run through tested stdlib helpers and behave exactly as in 2.14.1, with less model-interpreted prose on the same paths, and a shell variable read across Bash calls is caught by one general check in any phase file.
**Verified:** 2026-11-15T23:15:00Z, against `main` at `4ac7ee4` (the squash merge of PR #10)
**Status:** gaps_found
**Re-verification:** No — initial verification

## Result in plain terms

- **4 of 5 roadmap criteria verified. 1 gap.**
- **The gap:** one kind of input now gets a different Finalize decision from 2.14.1, and it is not among the differences the owner accepted. A finding in a top-level file whose name starts with `-`, with a "fix made this obsolete" verdict on unchanged code, stayed open at 2.14.1. Now it closes and Finalize writes APPROVED. The phase records say this case is the same as 2.14.1. It is not; I reproduced the difference. It is rare (a file at the repo's top level named like `-x.ts`), and the new behaviour honours a legitimate verdict, but "same gate decisions" is the phase's contract and this difference was not put to the owner as one. It closes with a one-line code change plus a real comparison test, or with the owner's acceptance by name.
- **Counts, recounted here:** Finalize path 92 → 83 steps and 136114 → 129451 bytes on the extraction alone (`c7d92c9`); 85 steps and 130886 bytes on `main`. Both figures are below 2.14.1 at both points.
- **Same behaviour:** the five situations match 2.14.1 on every outcome field at `HEAD` (run here, 7 walks).
- **The four goal-carrying checks all fail when deliberately broken** (48 deliberate breaks in a scratch copy; 47 caught, 1 passed one of the checks and was caught by another — see "Guards that can trip").
- **Tests:** full local suite 6,510 passed, 1 failed. The one failure is caused by a setting I added to my own run, not by the code; the same test passes when run the documented way.
- **Expected and not counted as gaps:** no 63-11-SUMMARY.md, requirements and roadmap not ticked, no `## Merge` section, backlog entries not yet filed (plan 63-11 Task 3 is held for this report).

## Goal Achievement

### Observable Truths (roadmap success criteria — the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline | ✗ FAILED (partial) | Helper exists, is called by one fence, calls `carry_state.finalize_counts`, `finalize_gate.run` and `batch_card.decisions_report` in-process, and writes only the fingerprint file. Five situations match at HEAD. My independent comparison of the fingerprint step against the literal 2.14.1 procedure (24 file names: clean, edited, staged, deleted, mode change, symlink, symlink out of the repo, untracked, `..`, absolute, space, directory) agreed on all but one: a name starting with `-`. That one changes the gate decision and is not an accepted difference. See the gap. |
| 2 | Missing, malformed or stale Finalize inputs stop with a plain message; a failed or refused attempt writes no report and archives nothing; restart and retry work across fresh shell calls | ✓ VERIFIED | Ran the real fence from `90-finalize.md` as its own fresh shell, under bash and zsh, against: no state file (`stop-no-state`), state `not json`, state `{}`, unreadable state, unfilled switch slots. Each stopped with the 2.14.1 sentence and wrote nothing beside the state. Situations `one-rebuild`, `refused-close` (both walks) and `fresh-shell-restart` match the 2.14.1 record. Breaking the report exit code, the exit-5 arm, the "second failure stops" rule, or the empty-fingerprint-file rule each fails tests. |
| 3 | Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host | ✓ VERIFIED | `GATEFILE`, the counts fence, the report fence and the hand-written fingerprint step are gone from `90-finalize.md`; the rebuild rule, never-reuse rule, never-retry-a-refusal rule, the stop sentence, the write boundary and `record-decisions` are still there. The moved explanation is byte-identical to `dd8e4ab` lines 34–39 (compared here with `cmp`) and no loaded file refers to it. The card, `record-decisions` and the report fill rules differ from 2.14.1 only by the step-3 line and `-I`. All 112 test ids the ledger cites were checked against the collected suite: 104 exist; the 8 missing are exactly the 7 the ledger marks removed and the 1 it marks renamed. The helper prints no owner sentence and renders nothing. |
| 4 | Loaded prose and helper/tool steps on the same Finalize paths are compared before and after against the Phase 62 criterion; the slice is reverted if it adds complexity without a demonstrated benefit | ✓ VERIFIED | Recounted here with the unchanged `step_count.py` (rule version 1) and `footprint.py`: `dd8e4ab` 92 steps / 136114 bytes; `c7d92c9` 83 / 129451, with the six shared files byte-identical to 2.14.1 at that commit; `HEAD` 85 / 130886. Growth after the extraction adds up exactly to the named items (plain review +1210 = 609 + 601; deep review +1222; Finalize +1435). The tools, the baseline records and `CRITERION.md` are unchanged since Phase 62 closed. PASS, so no revert applies. |
| 5 | One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips; any phase file it flags is recorded with its reproduction before it is changed | ✓ VERIFIED | `test_cross_call_vars.py` walks all 27 files; same-file exceptions list is empty; cross-file list holds only C2. Seven deliberate breaks to real phase files in a scratch copy each failed the check. Putting each pre-fix file back makes its reproduction test fail (X1–X8, C1). Commit order on the PR head: X1–X6 recorded 11-14 16:10, fixed 11-15 15:04–15:06; X7 recorded 15:08, fixed 15:31. For X8 and C1 a failing reproduction test was committed before each fix (15:29 before 15:31; 16:14 before 16:15) and C1 was written up in 63-REVIEW.md at 16:06; their 63-REPRO.md sections followed the fix by minutes (note N-2). |

**Score:** 4/5 truths verified

### Plan-level truths (detail under the criteria above)

| Plan | Truths | Status | Note |
|------|--------|--------|------|
| 63-01 | 6 | 5 ✓, 1 ✗ | ✗ "Where the helper could be stricter than 2.14.1 it is not: each such case has a named parity test": the leading-`-` case is recorded as parity and is the opposite (helper looser than 2.14.1); its test compares nothing against 2.14.1. Same root cause as the gap. |
| 63-02 | 8 | 7 ✓, 1 ✗ | ✗ the repeated D-06 parity truth, same root cause. Exit codes, stderr lines, single-writer and "report failure is never rebuilt" all hold and each has a break that fails tests. |
| 63-03 | 5 | 5 ✓ | 27 files, ≥ 70 fences; indented and four-backtick fences scanned (my break m3 used one). |
| 63-04 | 4 | 4 ✓ | Each reproduction runs the real blocks as separate shells beside a one-shell control. |
| 63-05 | 5 | 4 ✓, 1 ✗ | ✗ "Each case where the helper matches 2.14.1 on an input it could have refused is listed": row 1 of that list is wrong. Same root cause. |
| 63-06 | 9 | 9 ✓ | "Six shared files byte-identical" holds at the extraction commit `c7d92c9`; later changes are the owner-decided fixes. |
| 63-07 | 5 | 5 ✓ | |
| 63-08 | 7 | 7 ✓ | With note N-1 on what the comparison does not see. |
| 63-09 | 6 | 6 ✓ | Owner's fix/pin answer taken from the record. |
| 63-10 | 5 | 5 ✓ | |
| 63-11 | 5 | 3 ✓, 2 pending | Result page, owner "go" before merge, one PR with green runs: ✓. Backlog filing and STATE/ROADMAP edits are the held Task 3 — expected, not gaps. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/finalize_inputs.py` | the one helper call | ✓ VERIFIED (one defect, see gap) | 391 lines, stdlib only, called by the fence, in-process calls to the three existing helpers |
| `plugins/vibe-check/scripts/test_finalize_inputs.py` | parity, exit codes, mutants | ✓ VERIFIED (one hollow parity test) | 13 deliberate breaks to the helper each failed it |
| `plugins/vibe-check/scripts/test_cross_call_vars.py` | the general check, exceptions, mutants, reproductions | ✓ VERIFIED | |
| `plugins/vibe-check/scripts/test_pasted_name_guard.py` | D-21 guard tests | ✓ VERIFIED | |
| `plugins/vibe-check/scripts/test_inline_python_isolated.py` | D-22 isolation tests | ✓ VERIFIED | |
| `plugins/vibe-check/phases/shared/90-finalize.md` | one Finalize-inputs fence, next-action bullets | ✓ VERIFIED | |
| `docs/design/lean-v2.15/finalize-counts-explained.md` | moved passage | ✓ VERIFIED | byte-identical to 2.14.1 lines 34–39 |
| `docs/design/lean-v2.15/tools/finalize_capture.py` | second driver and compare | ✓ VERIFIED | |
| `63-COUNTS.md`, `63-REPRO.md`, `63-EQUIVALENCE.md`, `63-REMOVAL-LEDGER.md`, `63-RESULT.md` | records | ✓ exist and substantive | One factual error (leading-`-` row) in the ledger and the result page |

The SDK's artifact check passed for every plan (21/21). Its key-link check could not parse most of the plans' patterns (escaped regexes, descriptive "from" fields), so the links were checked by hand.

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `finalize_inputs.py` | `guard.py` | `guard.contained(root, f)` before any per-file git call | ✓ WIRED |
| `finalize_inputs.py` | `fixcommit.py` | `PATH_RE` only; `validate_paths` not called | ✓ WIRED |
| `finalize_inputs.py` | `carry_state.py`, `finalize_gate.py`, `batch_card.py` | three in-process calls | ✓ WIRED |
| `90-finalize.md` | `finalize_inputs.py` | one fence, stderr left on screen, exit codes mapped to the 2.14.1 sentences | ✓ WIRED (ran it) |
| `90-finalize.md` bullets | `NEXT_ACTIONS` | prose lock | ✓ WIRED (renaming a bullet fails it) |
| `test_finalize_card.py` | design document | sha256 of the moved passage | ✓ WIRED (editing the passage fails it) |
| `finalize_capture.py compare` | 2.14.1 situations record | `OUTCOME_KEYS` | ✓ WIRED |
| `test_cross_call_vars.py` | every phase file | `os.walk` | ✓ WIRED |
| CI workflow | phase test modules | `pytest plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` | ✓ WIRED; left-out list unchanged |

### Behavioral Spot-Checks (all run by me)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Steps and bytes at 2.14.1 | `step_count.py --rev dd8e4ab --json`, `footprint.py --rev dd8e4ab --json` | 92 steps, 136114 bytes | ✓ PASS |
| Steps and bytes, extraction alone | same at `c7d92c9` | 83 steps, 129451 bytes; plain 192057, deep 268997 (unchanged) | ✓ PASS |
| Steps and bytes at HEAD | same at `HEAD` | 85 steps, 130886 bytes; plain 193267, deep 270219 | ✓ PASS |
| 2.14.1 record still reproducible | `finalize_capture.py verify` | `finalize baseline matches (5 situations)` | ✓ PASS |
| Baseline records | `baseline_records.py verify --repo .` | `baseline holds` | ✓ PASS |
| Five situations at HEAD | `finalize_capture.py compare … --driver helper --commit HEAD` and `--root plugins/vibe-check` | `finalize outcome fields match (5 situations, 7 walks)`, exit 0, both | ✓ PASS |
| Stdlib-only gate | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | `34 shipped .py files; third-party imports: none` | ✓ PASS |
| Phase test modules (scratch clone) | 9 modules | 507 passed, 677 subtests | ✓ PASS |
| Full local suite | bare `pytest -q -p no:cacheprovider` | 6,510 passed, 1 failed (my-run artefact, below) | ✓ PASS with note |
| Real fence in fresh bash and zsh, six fault cases | scratch script | 2.14.1 sentences, nothing written | ✓ PASS |
| Guard pattern under bash 3.2, zsh 5.9, sh | 16 names | 6 blocked characters halt; spaces, `'`, `;`, `&`, `[`, `]` pass | ✓ PASS |
| All paste sites double-quoted | scan of every fence | 47 sites, 0 outside double quotes | ✓ PASS |
| Leading-`-` file, end to end | scratch script | 2.14.1 `outstanding-to-phase-5`; helper `write` | ✗ FAIL (the gap) |
| CI on `main` | `gh run view 43771152210` | success, push, `4ac7ee4` | ✓ PASS |
| CI on the PR head `f8ae5ff` | `gh run list --commit` | push and pull_request both success | ✓ PASS |

**The one full-suite failure.** `test_batchsnap.py::TestSnapshotImmutable::test_verify_survives_cache_churn` failed in my run because I had set `PYTHONDONTWRITEBYTECODE=1` to keep the working tree clean; that test starts a child pytest and requires it to write `.pyc` files. Re-run alone in the scratch clone: fails with the variable, passes without it. `batchsnap.py` and its test are unchanged since 2.14.1. Not a code defect.

### Guards that can trip (deliberate breaks, scratch clone only)

| Check | Breaks tried | Caught | What was broken |
|-------|--------------|--------|-----------------|
| Cross-call check | 7 | 7 | `PHASE_DIR` print removed; new setter/reader pair in an unrelated file; indented four-backtick pair with a braced read; Close-out state sentence removed; `--all` print removed; settings block split in two; `05-state.md` prints removed |
| Reverse run of the reproductions | 6 files | 6 | each pre-fix file put back: its X/C test fails |
| Equivalence comparison | 6 | 5 | caught: helper zeroes a count before the gate; a stop sentence reworded; empty report bundle; counting refusal line silenced; non-empty fingerprint file accepted. **Not caught: helper returns `next: stop-refused` for the gate's `write`** (note N-1) |
| Pasted-name guard | 6 | 6 | guard line removed at each of the three files; backtick dropped from the character list; print moved before the guard; guard made to warn without stopping |
| Inline-Python isolation | 5 | 5 | `-I` removed in two files; new un-isolated one-liner in a phase file and in `commands/review.md`; new isolated one-liner (count lock) |
| Helper and fence | 18 | 18 | index check, working-tree check, root-vs-folder (D-19), character filter, containment, unreadable-state line, report exit code, report re-read, default switch, state write, fingerprint-file emptiness, third-party import (gate tool), extra import, exit-5 arm, hidden stderr, "second failure stops", renamed bullet, edited moved passage |

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| FINX-01 | 01, 02, 06, 07, 08 | Helpers on the single-writer path; same gate decisions and reports as the baseline | ✗ BLOCKED (one input class) | The gap |
| FINX-02 | 02, 06, 08 | Bad inputs fail visibly; a failed attempt writes and archives nothing | ✓ SATISFIED | Truth 2 |
| FINX-03 | 06, 08 | Restart and retry across fresh shells | ✓ SATISFIED | Truth 2 |
| FINX-04 | 05, 06, 07 | Superseded prose and locks removed; invariants kept; judgment stays in the host | ✓ SATISFIED | Truth 3 |
| FINX-05 | 01, 09, 10, 11 | Before/after comparison; revert if no benefit | ✓ SATISFIED | Truth 4 |
| XVAR-01 | 03, 11 | One general check with a mutant | ✓ SATISFIED | Truth 5 |
| XVAR-02 | 04, 09, 10 | Flagged files recorded with reproduction before change | ✓ SATISFIED | Truth 5, note N-2 |

All seven ids appear in plan frontmatter and in REQUIREMENTS.md under Phase 63. No orphaned requirement.

### Differences from 2.14.1 found in the code, against the accepted list

| Difference in the code | Accepted? |
|------------------------|-----------|
| Unreadable state file: shell's "Permission denied" line no longer shown | Yes — `## Your decision` item 1 |
| Unsafe folder, branch or phase names stop the review (D-21) | Yes — item 2 |
| Byte growth on every review path at phase end | Yes — item 3; adds up exactly |
| Corrupted (non-UTF-8) state file on a C locale shows a different refusal line | Yes — item 4 |
| Subfolder fix (D-19) | Yes — owner decision D-19; on the page |
| Close out and fix loop keep the state path, incl. `--all` (D-20, D-23); `--all` prints one extra line | Yes — owner decision D-20; D-23 on the page |
| Inline Python isolated (D-22), incl. two ignored encoding settings | Yes — owner decision D-22; encoding note on the page under the second review |
| X1–X6 (settings and names now carry between separate calls) | Yes — "Fix all six" |
| Fewer commands and their output on screen | Yes — the intended difference |
| A fingerprint file already holding `{}` is refused | On the page; cannot occur through the instructions |
| **A top-level file whose name starts with `-` is now fingerprinted; its fix-obsolete verdict closes the finding** | **No — the page says this is the same as 2.14.1** |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `test_finalize_inputs.py` `TestParityGaps::test_gap_leading_dash_path_is_fingerprinted` | A "parity" test that asserts only the new code's output | Blocker (part of the gap) | Could never detect the difference it is named for |
| phase-modified files | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` | none found | — |

### Notes (not gaps)

- **N-1. The five-situation comparison does not look at `next`.** The instructions tell the model to branch on the result's `next` field; the comparison driver branches on `action`. A helper that returned the wrong `next` for a `write` passed the comparison (exit 0). The same break fails 8 unit tests in `test_finalize_inputs.py` and `test_finalize_card.py`, which run in CI, so it is covered — but by the unit tests, not by the equivalence comparison. Worth carrying with the other review items.
- **N-2. X8 and C1 write-ups followed their fixes by minutes.** In both cases a failing reproduction test was committed before the fix, and C1 was described in the first review beforehand. The 63-REPRO.md prose sections came 8–10 minutes after.
- **N-3. C2 stays on the exceptions list without a reproduction attempt** (`30-collect-score.md`). It is named on the result page and was accepted as carried (item 5).
- **N-4. The result page says the 2.14.1 byte figures for `--all` and the fix loop are "not recorded".** `footprint.py --rev dd8e4ab` gives them: 284926, 361866 and 255070, equal to the extraction commit's. Nothing depends on this.
- **N-5. The check does not see names set only in prose** (18 such names, including `PHASE_ID`, `ARGUMENTS`, `NARROW`). This is the known limit already on the result page.

### Human Verification Required

None that blocks. One item is unmeasured by design and the owner has been told: no live review was run, so whether a live model fills the three switch slots, pastes the printed state path and branches on `next` as the scripted walks do has not been observed. Under the standing rule a live or paid run needs its own approved proposal; this report does not ask for one.

### Gaps Summary

One gap, one root cause. The 2.14.1 instructions validated each finding's file by running `guard.py` as a command; the helper calls the same check as a function. The command refuses a name that starts with `-` (it reads it as an option); the function accepts it. The phase recorded this case as "the helper does what 2.14.1 does" without running the 2.14.1 command, and the test written to hold that claim checks only the helper. The result is a gate decision that differs from 2.14.1 for that input — a finding that 2.14.1 kept open now closes — presented to the owner as no difference.

Two ways to close it:

1. **Match 2.14.1.** Leave such a file out of the fingerprints, add a test that runs the 2.14.1 guard command on the same name, and correct the three records. User impact: none compared with 2.14.1. Size: a one-line condition plus one test.
2. **Accept the difference.** The new behaviour honours a legitimate "fix made this obsolete" verdict that 2.14.1 ignored by accident; git cannot misread the name (`HEAD:` prefix, and after `--`). If the owner accepts it by name, record it as an override here and correct the result page and ledger to say it differs.

Which behaviour is right is a product decision for the owner. Either way the records need correcting.

---

_Verified: 2026-11-15T23:15:00Z_
_Verifier: Claude (bm-verifier)_
