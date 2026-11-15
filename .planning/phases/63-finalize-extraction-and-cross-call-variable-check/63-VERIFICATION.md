---
phase: 63-finalize-extraction-and-cross-call-variable-check
verified: 2026-11-15T23:50:00Z
status: gaps_found
score: 4/5 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  previous_verified: 2026-11-15T23:15:00Z
  gaps_closed:
    - "Leading-dash file names (D-24): a finding in a file whose name the 2.14.1 containment command refuses (for example top-level `-x.ts`) with a last-pass fix-obsolete verdict on unchanged code now stays open, as at 2.14.1 (counts [1,0,0], gate `outstanding-to-phase-5`, empty fingerprint file, no report). No file name disagrees in either direction on Python 3.9.6, 3.12.12, 3.13.14 or 3.14.5."
  gaps_remaining: []
  regressions: []
  new_gaps:
    - "Repo folder whose name ends in whitespace (not caused by the gap closure; present since the merge of PR #10; missed by the initial verification)"
gaps:
  - truth: "Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline"
    status: partial
    severity: blocking
    reason: "One input class still gives a different gate decision from 2.14.1 and is not on the accepted list. It is not a file name: it is the repo's own folder name. When the folder the repo lives in has a name ending in whitespace (a space, a tab, a no-break space), the helper trims that whitespace from the repo root (`_toplevel` returns `result[1].strip()`); 2.14.1's `$(git rev-parse --show-toplevel)` drops only the final line break. The helper then checks a folder that is not the repo. Reproduced end to end on Python 3.9.6 and 3.14.5, clean file `x.ts` with a last-pass fix-obsolete verdict on unchanged code: (a) no folder at the trimmed path — 2.14.1 counts [0,0,0] gate `write`; helper counts [1,0,0] gate `outstanding-to-phase-5` (helper stricter; the plan's rule was that the helper is never stricter than 2.14.1). (b) a second git repo sits at the trimmed path (`repo` beside `repo `) holding the same file, and the real repo's file was edited after the verdict — 2.14.1 counts [1,0,0] gate `outstanding-to-phase-5`; helper counts [0,0,0] gate `write` (the helper fingerprints the neighbouring repo and approves). Case (b) needs a very unusual folder layout and cannot be arranged by the author of the reviewed change. Present in the merged helper at `4ac7ee4`; untouched by the gap-closure commits. Everything else under this truth is verified, including the D-24 gap."
    artifacts:
      - path: "plugins/vibe-check/scripts/finalize_inputs.py"
        issue: "`_toplevel` (line 141 at `4ac7ee4`, unchanged at `66b0429`) returns `result[1].strip()`; the 2.14.1 command substitution removes trailing line breaks only"
      - path: "plugins/vibe-check/scripts/test_finalize_inputs.py"
        issue: "`TestGuardCommandParity.fingerprint_2141` builds its 2.14.1 root with `.strip()` too, so the comparison shares the helper's reading of the root; no test puts a repo in a folder whose name ends in whitespace"
    missing:
      - "Either: make the helper read the root as the 2.14.1 command substitution does (drop trailing line breaks only), with a test on a temp repo in a folder whose name ends in a space that runs the 2.14.1 command through a shell, and a mutant; or: an owner acceptance of this difference by name, recorded as an override here and added to the result page's list of differences"
      - "If fixed: one line in the result page's correction section, since it currently says no other difference was found"
---

# Phase 63: Finalize extraction and cross-call variable check — Verification Report

**Phase Goal:** Finalize's mechanical steps run through tested stdlib helpers and behave exactly as in 2.14.1, with less model-interpreted prose on the same paths, and a shell variable read across Bash calls is caught by one general check in any phase file.
**Verified:** 2026-11-15T23:50:00Z, against branch `feat/v2.15-phase-63-gap` at `66b0429` (three commits on top of the first verification commit `78ce8d0`; `main` is at `4ac7ee4`; follow-up pull request #11 open, not merged, both CI runs green on `66b0429`)
**Status:** gaps_found
**Re-verification:** Yes — after gap closure

## Result in plain terms

- **The gap from the first report is closed.** A finding in a file such as `-x.ts`, with a "fix made this obsolete" verdict on unchanged code, now stays open exactly as at 2.14.1. I re-ran my own comparison against the literal 2.14.1 steps on four Python versions and widened it to 131 file names. No file name disagrees in either direction.
- **The new test is real.** It runs the actual 2.14.1 check command beside the helper. Putting the old line back makes it fail; swapping its 2.14.1 side for the helper's old check makes it fail.
- **Nothing I verified before has regressed.** Five situations still match 2.14.1; Finalize is still 85 steps and 130,886 bytes; the stdlib-only gate and the import-set test agree on the new `io` import.
- **One new gap, found while testing around the fix. It is not caused by the fix and I missed it the first time.** If the folder a repo lives in has a name ending in a space (or tab), the helper trims that space and looks at the wrong folder. In the ordinary case the helper leaves a finding open that 2.14.1 would have closed. In a contrived case (a second repo sitting beside it under the trimmed name, holding the same file) the helper approves a review that 2.14.1 would have kept open. This is far rarer than the `-x.ts` case, and the author of a reviewed change cannot set it up. It is a one-line change plus a test, or an owner acceptance by name. I have graded it blocking because the phase's contract is "same gate decisions as 2.14.1" and this is a reproduced different decision that the owner has not been shown; whether to fix it in pull request #11 or accept it is the owner's decision.
- **Score: 4 of 5**, the same number as before, for a different and smaller reason.
- **Expected and not counted as gaps:** no 63-11-SUMMARY.md, no `## Merge` section, backlog entries not filed, ROADMAP/STATE/REQUIREMENTS not ticked, pull request #11 not merged.

## Re-verification summary

| Item | First report (23:15Z, `4ac7ee4`) | Now (`66b0429`) |
|------|----------------------------------|-----------------|
| Status | gaps_found | gaps_found |
| Score | 4/5 | 4/5 |
| Gap 1: leading-dash file names differ from 2.14.1 | open, blocking | **closed** |
| Records saying the leading-dash case matches 2.14.1 | wrong in three places | **corrected** (ledger row 1, result page correction section, 63-01-SUMMARY note, 63-REPRO section) |
| Hollow parity test | `TestParityGaps::test_gap_leading_dash_path_is_fingerprinted` | **removed**, replaced by `TestGuardCommandParity` (two tests) |
| Regressions | — | none |
| New gap: repo folder name ending in whitespace | not found (was present) | **open, blocking** |

### What I ran now and what I carried

| Criterion | Now | How |
|-----------|-----|-----|
| 1 (same decisions as 2.14.1) | **Re-ran** | Everything in "Gap closure evidence" and "Regression checks" below |
| 2 (bad inputs stop; nothing written; restart works) | **Carried**, with a partial re-run | The diff touches only the per-file containment line in `_head_blobs`. Re-ran: the five-situation comparison (which includes `one-rebuild`, `refused-close`, `fresh-shell-restart`) and the whole of `test_finalize_inputs.py`. Not re-run: the real fence under bash and zsh against the six fault cases |
| 3 (superseded prose removed, invariants kept) | **Carried** | No instruction file, design document or lock changed (`git diff 4ac7ee4 66b0429` touches two files under `plugins/`, both scripts) |
| 4 (before/after counts, revert rule) | **Re-ran the counts**, carried the rest | 85 steps and 130,886 bytes at `4ac7ee4` and at `66b0429`; 92 steps at `dd8e4ab` |
| 5 (the general cross-call check) | **Carried** | No phase file and no check file changed |

## Goal Achievement

### Observable Truths (roadmap success criteria — the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline | ✗ FAILED (partial) | The D-24 gap is closed: 131 file names on four Python versions, 0 disagreements; `-x.ts` end to end matches 2.14.1. One other input class differs: a repo folder whose name ends in whitespace. See the gap. |
| 2 | Missing, malformed or stale Finalize inputs stop with a plain message; a failed or refused attempt writes no report and archives nothing; restart and retry work across fresh shell calls | ✓ VERIFIED (carried; partial re-run) | First report's evidence stands. The five-situation comparison and the 110 helper tests pass at `66b0429`. |
| 3 | Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host | ✓ VERIFIED (carried) | No file under this truth changed. |
| 4 | Loaded prose and helper/tool steps on the same Finalize paths are compared before and after against the Phase 62 criterion; the slice is reverted if it adds complexity without a demonstrated benefit | ✓ VERIFIED (counts re-run) | `step_count.py`: 92 steps at `dd8e4ab`, 85 at `4ac7ee4`, 85 at `66b0429`. `footprint.py`: Finalize 130,886 bytes at `4ac7ee4` and at `66b0429`. |
| 5 | One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips; any phase file it flags is recorded with its reproduction before it is changed | ✓ VERIFIED (carried) | No file under this truth changed. |

**Score:** 4/5 truths verified

### Gap closure evidence (all run by me, in a scratch clone at `66b0429` and a `git archive` of `dd8e4ab`)

The 2.14.1 side is the literal step 1 of `dd8e4ab:plugins/vibe-check/phases/shared/90-finalize.md`: the character filter, `guard.py` from `dd8e4ab` run as a command, then the three git commands, a file kept only when all exit 0; then `carry_state.py finalize-counts` and `finalize_gate.py` from `dd8e4ab`. The helper side is `finalize_inputs.py` at `66b0429`. Both sides use the same interpreter.

**End to end (fix-obsolete verdict on unchanged code), identical on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5 unless shown:**

| File | 2.14.1 | Helper | Same? |
|------|--------|--------|-------|
| `x.ts` (control) | [0,0,0] `write` | [0,0,0] `write` | yes |
| `-x.ts` | [1,0,0] `outstanding-to-phase-5` | [1,0,0] `outstanding-to-phase-5`, `next` = `finalize-card`, fingerprint file `{}`, stderr empty | yes |
| `sub/-x.ts` | [0,0,0] `write` | [0,0,0] `write` | yes |
| `-d/x.ts`, `--`, `-h`, `--pa`, `--root` | [1,0,0] `outstanding-to-phase-5` | the same | yes |
| `-`, `-1` | [0,0,0] `write` | the same | yes |
| `-1.ts`, `-1e5`, `-1_0` | 3.9 / 3.12 / 3.13: [1,0,0] `outstanding-to-phase-5`. 3.14: [0,0,0] `write` | the same as 2.14.1 on each version | yes |

**File names, fingerprint step only:** 131 names per Python version, 4 versions, 0 disagreements, 0 helper crashes. 78 of the names were real committed files. Beyond the executor's 51-name matrix I added: every abbreviation of `--root`, `--path` and `--help`; `-r`, `-p`, `-v`, `-V`, `--version`; `---`; number look-alikes (`-0x10`, `-1j`, `-1e-5`, `-1.`, `-.5.5`, `-1__0`, `-inf`, `-nan`, a 22-digit number); option names with a file ending or as a folder (`--root.ts`, `-h.ts`); 200- and 300-character names; a 40-folder-deep path; names the character filter refuses that argparse treats specially (`--path=x.ts`, `--root=x`, `@file`, the empty string, non-ASCII, a lone surrogate, a NUL character, full-width and minus-sign dashes); and trailing-slash, `./`, `..` and absolute forms.

**In-process versus command, the specific risks named in the request:**

| Risk | What I ran | Result |
|------|-----------|--------|
| The in-process parser differs from the command's | 300 random leading-dash names per version, helper's check versus the `dd8e4ab` command | 0 disagreements on all four versions |
| Output or state leaks between files | One state listing all 130 names once, twice (260), reversed, and `-x.ts`/`x.ts` alternating 50 times, run in a child process | Result equal to the 2.14.1 set each time; stdout is only the result; stderr empty |
| stdout/stderr left replaced | Checked after every call | Always restored |
| Something other than a clean exit escapes `guard.main` | 131 names × 4 versions, plus the oversized names below | No exception reached the caller |
| Environment | End to end for `x.ts`, `-x.ts`, `-1.ts` under `COLUMNS=1`, forced colour, `LC_ALL=C`, `PYTHONWARNINGS=error`, `PYTHONOPTIMIZE=2`, `PYTHONUTF8=1`, and interpreter flags `-I` and `-S -E` | All the same as 2.14.1 |
| stderr closed or discarded | Helper run with `2>&-` and `2>/dev/null` on `-x.ts` | Exit 0, `outstanding-to-phase-5`, `{}` |
| Working folder | Helper and 2.14.1 from a non-repo folder and from a subfolder | Agree (the subfolder case is the accepted D-19 difference and was compared from the root as well) |
| Names too long for a command line | 1.1 MB names (plain and leading-dash), 300 KB name | 2.14.1's command cannot start, file left out; helper leaves it out too. Same outcome |
| `sys.argv[0]` | Read the code | `guard.main` sets `prog="guard.py"` itself and takes its arguments as a parameter; nothing reads `sys.argv` |

**The new test can fail (scratch clone only):**

| Break | Result |
|-------|--------|
| A. Fix line put back to `guard.contained(root, f)[0]` | Both `TestGuardCommandParity` tests fail (Python 3.14 and 3.9); the other 108 tests pass |
| The test at `c1541b1` (test-first commit, helper not yet fixed) | Both fail, as the record says |
| B1. The test's 2.14.1 side swapped for the helper's old in-process check, helper fixed | Both fail |
| B2. Same swap, helper unfixed (both sides the same wrong logic) | Both fail — the test's fixed expectations (`-x.ts`, `-d/x.ts`, `--`, `--root`, `--path`, `-h`, `--help` left out; `-`, `-1` and the controls kept) catch it |
| C. Helper uses a plain "starts with `-`" rule | The 22-name test fails (`-` and `-1` are kept by 2.14.1) |
| D. Helper accepts any guard exit except 1 | Both fail |
| E. Helper does not restore stdout/stderr | 5 tests fail |
| F. Helper does not capture the guard's output | 5 tests fail |
| G. Containment removed entirely | 7 tests fail |
| H. `io` removed from the import-set test's expected set | `test_stdlib_import_set_is_exact` fails |
| I. Helper gains one more stdlib import | `test_stdlib_import_set_is_exact` fails |

One thing the test cannot show, by construction: if its 2.14.1 side is swapped for the helper's *current* check, it still passes, because that check is now the command's own code. This is the point of the fix, not a weakness: the fixed expectations in B2 and C are what keep the test honest.

### Regression checks (run by me at `66b0429`)

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 2.14.1 record still reproducible | `finalize_capture.py verify` | `finalize baseline matches (5 situations)` | ✓ PASS |
| Five situations, by commit | `finalize_capture.py compare … --driver helper --commit HEAD` (Python 3.14 and 3.9) | `finalize outcome fields match (5 situations, 7 walks)`, exit 0 | ✓ PASS |
| Five situations, by folder | same with `--root plugins/vibe-check` | the same line, exit 0 | ✓ PASS |
| Helper tests, default locale | bare `pytest plugins/vibe-check/scripts/test_finalize_inputs.py` | 110 passed, 191 subtests | ✓ PASS |
| Helper tests, `LC_ALL=C` | same | 110 passed, 191 subtests | ✓ PASS |
| Helper tests, Python 3.9.6 | same | 110 passed | ✓ PASS |
| Stdlib-only gate | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | `34 shipped .py files; third-party imports: none` | ✓ PASS |
| Import-set test agrees with the gate | breaks H and I above | each fails the test | ✓ PASS |
| Finalize steps | `step_count.py --rev HEAD --json` | 85 (35 fences, 5 inline commands, 5 Write-tool writes, 40 paste sites) — identical to `4ac7ee4` | ✓ PASS |
| Finalize bytes | `footprint.py --rev HEAD --json` | 130,886 — identical to `4ac7ee4` | ✓ PASS |
| Files changed under `plugins/`, `docs/`, `.github/` since `4ac7ee4` | `git diff --stat` | `finalize_inputs.py` and `test_finalize_inputs.py` only | ✓ PASS |
| CI on the follow-up pull request head | `gh pr view 11` | open, not merged; both `offline-suite` runs success on `66b0429` | ✓ PASS |

The full local suite was not run by me (one was in progress in the working checkout, per instruction). The first report's full-suite figure (6,510 passed, 1 failure caused by a setting in my own run) is carried, not re-measured.

### The new gap in detail

**What differs.** 2.14.1 passed the repo root to its check as `"$(git rev-parse --show-toplevel)"`. A shell drops only the final line break from that. The helper's `_toplevel` trims all whitespace from both ends. For a repo in a folder named, say, `repo ` (ending in a space), the helper's root is `…/repo`, which is a different path.

**Reproduced (Python 3.9.6 and 3.14.5, identical), clean `x.ts`, fix-obsolete verdict on unchanged code:**

| Repo folder | 2.14.1 | Helper |
|-------------|--------|--------|
| `repo` (control) | [0,0,0] `write` | [0,0,0] `write` |
| `my repo` (space inside) | [0,0,0] `write` | [0,0,0] `write` |
| `repo ` (ends with a space) | [0,0,0] `write` | **[1,0,0] `outstanding-to-phase-5`** |
| ends with a tab | [0,0,0] `write` | **[1,0,0] `outstanding-to-phase-5`** |
| ends with a no-break space | [0,0,0] `write` | **[1,0,0] `outstanding-to-phase-5`** |
| `repo ` beside a second repo `repo` holding the same file; the real repo's `x.ts` edited after the verdict | [1,0,0] `outstanding-to-phase-5` | **[0,0,0] `write`** |

**How much it matters.** A folder name ending in whitespace is very unusual and hard to create by accident. In the ordinary case the helper is the safer side: the finding stays open and the owner is asked. The last row is the unsafe direction (an approval 2.14.1 would not give) and needs a neighbouring repo under the trimmed name with the same file at the verdict's version; the author of a reviewed change does not control the reviewer's folder names. Folder names ending in a line break were compared too and agree (both leave the file out).

**Why it is graded blocking.** Same test as the first report: a reproduced, deterministic gate decision that differs from 2.14.1, in both directions, not on the list the owner accepted. The plan's own rule (63-01, 63-02) is that the helper is never stricter than 2.14.1 without a named test.

**Two ways to close it.**
1. **Match 2.14.1.** Read the root as the shell does (drop trailing line breaks only), add a temp-repo test in a folder ending in a space that runs the 2.14.1 command through a shell, with a mutant. User impact: none compared with 2.14.1. Size: one line plus one test; it can ride in pull request #11.
2. **Accept the difference by name.** Record it as an override here and add it to the result page's differences.

### Corrected records, checked against what is true now

| Record | Claim | Check | Holds? |
|--------|-------|-------|--------|
| 63-REMOVAL-LEDGER.md row 1 and correction note | 2.14.1 left the file out; the merged helper closed the finding; fixed at `72a2f94`, test first at `c1541b1`; original text kept struck through | Reproduced both; commit order confirmed; the test at `c1541b1` fails | Yes |
| 63-REMOVAL-LEDGER.md | "22 names" in the comparison test | 19 leading-dash + 3 controls | Yes |
| 63-RESULT.md correction section | Five situations still match; 85 steps and 130,886 bytes | Re-run | Yes |
| 63-RESULT.md correction section | The test "failed before the fix", "fails if its 2.14.1 side is swapped for the helper's own check" | Breaks A, B1, B2 | Yes (for the helper's old check; see the note under the break table) |
| 63-RESULT.md, 63-REPRO.md | `-1.ts`, `-1_0`, `-1e5` accepted on 3.14.5 and refused on 3.9.6 | Reproduced | Yes |
| 63-RESULT.md, 63-REPRO.md | 51 names, 102 comparisons, 28 disagreements before the fix, 0 after | "0 after" confirmed on a larger set; the "28 before" count was not recounted | Not contradicted |
| 63-RESULT.md correction section | "No other difference was found" | True of the 51-name matrix. A further difference exists outside it (this report's gap) | True as written; needs a line if the gap is fixed or accepted |
| 63-REPRO.md | A name ending in a line break passes the filter on both sides; whether a model reading the prose would have accepted it cannot be determined | Reproduced: the helper fingerprints a file literally named `x.ts` + line break. 2.14.1's own tool (`fixcommit.py`) uses the same pattern the same way | Yes; stated without overclaiming |
| 63-01-SUMMARY.md | Correction note pointing at the ledger and D-24 | Read | Yes |
| 63-CONTEXT.md D-24 | Owner decision "Match 2.14.1 (Recommended)" | Read; the code now does this for file names | Yes |

One inaccuracy, in a code comment only: the `TestGuardCommandParity` docstring says Python "3.13+" reads `-1.ts` as a negative number. On 3.13.14 the command still refuses it; 3.14.5 accepts it. The records give the right versions. Info only.

### Plan-level truths (carried from the first report, updated where this diff changes them)

| Plan | Truths | Status | Note |
|------|--------|--------|------|
| 63-01 | 6 | 5 ✓, 1 ✗ | ✗ "Where the helper could be stricter than 2.14.1 it is not: each such case has a named parity test". The leading-dash case under this truth is now fixed and has a real comparison test. The folder-name case is a second instance, with no test. |
| 63-02 | 8 | 7 ✓, 1 ✗ | ✗ the repeated D-06 parity truth, same root cause as the new gap. |
| 63-03 | 5 | 5 ✓ | carried |
| 63-04 | 4 | 4 ✓ | carried |
| 63-05 | 5 | 5 ✓ | Row 1 of the "input gaps carried" list is corrected. (Was 4 ✓, 1 ✗.) |
| 63-06 | 9 | 9 ✓ | carried |
| 63-07 | 5 | 5 ✓ | carried |
| 63-08 | 7 | 7 ✓ | carried, with note N-1 |
| 63-09 | 6 | 6 ✓ | carried |
| 63-10 | 5 | 5 ✓ | carried |
| 63-11 | 5 | 3 ✓, 2 pending | Backlog filing and STATE/ROADMAP edits are held for this report — expected, not gaps. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/finalize_inputs.py` | the one helper call | ✓ VERIFIED (one defect, see gap) | Containment now runs `guard.main` in-process; stdlib imports `io`, `json`, `os`, `subprocess`, `sys` |
| `plugins/vibe-check/scripts/test_finalize_inputs.py` | parity, exit codes, mutants | ✓ VERIFIED | 110 tests; the hollow parity test is gone; `TestGuardCommandParity` is two-sided |
| `plugins/vibe-check/scripts/test_cross_call_vars.py` | the general check | ✓ VERIFIED (carried) | |
| `plugins/vibe-check/scripts/test_pasted_name_guard.py` | D-21 guard tests | ✓ VERIFIED (carried) | |
| `plugins/vibe-check/scripts/test_inline_python_isolated.py` | D-22 isolation tests | ✓ VERIFIED (carried) | |
| `plugins/vibe-check/phases/shared/90-finalize.md` | one Finalize-inputs fence | ✓ VERIFIED (carried; unchanged) | |
| `docs/design/lean-v2.15/finalize-counts-explained.md` | moved passage | ✓ VERIFIED (carried; unchanged) | |
| `docs/design/lean-v2.15/tools/finalize_capture.py` | second driver and compare | ✓ VERIFIED (re-run) | |
| `63-COUNTS.md`, `63-REPRO.md`, `63-EQUIVALENCE.md`, `63-REMOVAL-LEDGER.md`, `63-RESULT.md` | records | ✓ exist and substantive | The leading-dash error is corrected in all of them |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `finalize_inputs.py` | `guard.py` | `guard.main(["--root", root, "--path", f]) == 0` before any per-file git call (was `guard.contained`) | ✓ WIRED (breaks A, D, G fail tests) |
| `finalize_inputs.py` | `fixcommit.py` | `PATH_RE` only | ✓ WIRED (carried) |
| `finalize_inputs.py` | `carry_state.py`, `finalize_gate.py`, `batch_card.py` | three in-process calls | ✓ WIRED (carried; five situations re-run) |
| `90-finalize.md` | `finalize_inputs.py` | one fence | ✓ WIRED (carried) |
| `test_finalize_inputs.py::TestGuardCommandParity` | `guard.py` as a command | `subprocess.run([sys.executable, GUARD_PY, …])`; `guard.py` is byte-identical to `dd8e4ab` | ✓ WIRED (breaks B1, B2 fail it) |
| `finalize_capture.py compare` | 2.14.1 situations record | `OUTCOME_KEYS` | ✓ WIRED (re-run) |
| CI workflow | phase test modules | unchanged | ✓ WIRED (carried; green on `66b0429`) |

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| FINX-01 | 01, 02, 06, 07, 08 | Helpers on the single-writer path; same gate decisions and reports as the baseline | ✗ BLOCKED (one input class: repo folder name ending in whitespace) | The gap. The D-24 input class is now satisfied. |
| FINX-02 | 02, 06, 08 | Bad inputs fail visibly; a failed attempt writes and archives nothing | ✓ SATISFIED | Truth 2 (carried) |
| FINX-03 | 06, 08 | Restart and retry across fresh shells | ✓ SATISFIED | Truth 2 (carried) |
| FINX-04 | 05, 06, 07 | Superseded prose and locks removed; invariants kept | ✓ SATISFIED | Truth 3 (carried) |
| FINX-05 | 01, 09, 10, 11 | Before/after comparison; revert if no benefit | ✓ SATISFIED | Truth 4 (counts re-run) |
| XVAR-01 | 03, 11 | One general check with a mutant | ✓ SATISFIED | Truth 5 (carried) |
| XVAR-02 | 04, 09, 10 | Flagged files recorded with reproduction before change | ✓ SATISFIED | Truth 5 (carried) |

All seven ids appear in plan frontmatter and in REQUIREMENTS.md under Phase 63. No orphaned requirement.

### Differences from 2.14.1 found in the code, against the accepted list

| Difference in the code | Accepted? |
|------------------------|-----------|
| Unreadable state file: shell's "Permission denied" line no longer shown | Yes — `## Your decision` item 1 |
| Unsafe folder, branch or phase names stop the review (D-21) | Yes — item 2 |
| Byte growth on every review path at phase end | Yes — item 3 |
| Corrupted (non-UTF-8) state file on a C locale shows a different refusal line | Yes — item 4 |
| Subfolder fix (D-19) | Yes — owner decision D-19 |
| Close out and fix loop keep the state path (D-20, D-23) | Yes — owner decision D-20; D-23 on the page |
| Inline Python isolated (D-22) | Yes — owner decision D-22 |
| X1–X6 (settings and names now carry between separate calls) | Yes — "Fix all six" |
| Fewer commands and their output on screen | Yes — the intended difference |
| A fingerprint file already holding `{}` is refused | On the page; cannot occur through the instructions |
| ~~A top-level file whose name starts with `-` is now fingerprinted~~ | **Removed by D-24: the helper now matches 2.14.1** |
| **A repo folder whose name ends in whitespace: the helper checks the trimmed path instead of the repo** | **No — not on the page** |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `finalize_inputs.py` `_toplevel` | `.strip()` where the 2.14.1 shell drops trailing line breaks only | Blocker (the gap) | Wrong repo root for a folder name ending in whitespace |
| `test_finalize_inputs.py` `TestGuardCommandParity` docstring | "3.13+" should read 3.14 | Info | Comment only |
| files changed by the gap closure | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` | none found | — |

### Notes (not gaps)

- **N-1 to N-5** from the first report are carried unchanged (the five-situation comparison does not look at `next`; X8 and C1 write-ups followed their fixes by minutes; C2 stays on the exceptions list; the result page's "not recorded" byte figures are recoverable; names set only in prose are not seen by the check).
- **N-6. Which leading-dash names are refused depends on the Python version, on both sides alike.** On 3.14 the 2.14.1 command accepts anything starting with `-` and a digit; on 3.9 to 3.13 it accepts only plain negative numbers. The helper follows the interpreter that runs it, and the instructions start the helper with the same `python3` that 2.14.1 used for its check, so the two agree on any one machine.
- **N-7. The helper gives each git call 60 seconds and leaves the file out if git takes longer.** 2.14.1 had no limit of its own. This fails closed and needs a git call on one file to take over a minute; it is not on the result page. Not a gap.
- **N-8. A file whose name ends in a line break is fingerprinted by the helper.** 63-REPRO.md records this accurately. 2.14.1's own tool reads the pattern the same way, so I count it as matching.

### Human Verification Required

None that blocks. Carried from the first report: no live review was run, so whether a live model fills the three switch slots, pastes the printed state path and branches on `next` as the scripted walks do has not been observed. Under the standing rule a live or paid run needs its own approved proposal; this report does not ask for one.

### Gaps Summary

The gap this re-verification was asked to check is closed, with a test that genuinely compares against the 2.14.1 command and fails when it should, and with the records corrected to say what is true.

One gap remains under the same criterion, from a different cause that predates the gap closure: the helper trims whitespace from the repo's folder path where the 2.14.1 shell did not, so a repo in a folder whose name ends in a space gets a different Finalize decision. It is rare, mostly errs on the safe side, and is a one-line change plus a test. It needs the owner's decision: match 2.14.1 (it can ride in pull request #11) or accept it by name.

---

## History: first verification (2026-11-15T23:15:00Z, `main` at `4ac7ee4`)

**Status then:** gaps_found. **Score then:** 4/5. **One blocking gap**, now closed:

> For a finding in a top-level file whose name starts with `-` (for example `-x.ts`) that carries a last-pass fix-obsolete verdict on unchanged code, 2.14.1 leaves the finding open (gate `outstanding-to-phase-5`, nothing written); the new helper closes it and the gate returns `write` (APPROVED). At 2.14.1 the instructions ran `python3 "$GUARD_PY" --root … --path "<file>"` and required exit 0; that command exits 2 for a name starting with `-`, so the file was left out, fail closed. The helper calls `guard.contained()` in-process, which accepts the name. The records state the opposite. The named parity test asserts only the helper's own output and never runs the 2.14.1 command. Reproduced end to end on Python 3.9.6 and 3.14.5.

Evidence from that report that is carried and was not re-run now:

- **Criterion 2:** the real fence from `90-finalize.md` run as its own fresh shell under bash and zsh against no state file, `not json`, `{}`, an unreadable state and unfilled switch slots; each stopped with the 2.14.1 sentence and wrote nothing.
- **Criterion 3:** `GATEFILE`, the counts fence, the report fence and the hand-written fingerprint step are gone; the rebuild, never-reuse and never-retry rules, the stop sentence, the write boundary and `record-decisions` remain; the moved explanation is byte-identical to `dd8e4ab` lines 34–39; all 112 cited test ids checked against the collected suite.
- **Criterion 4:** `c7d92c9` (extraction alone) 83 steps / 129,451 bytes; growth after it adds up exactly to the named items; tools, baseline records and `CRITERION.md` unchanged since Phase 62.
- **Criterion 5:** the check walks all 27 files; seven deliberate breaks to real phase files each failed it; each pre-fix file put back fails its reproduction test (X1–X8, C1); recorded-before-fixed order confirmed from commit times.
- **Guards that can trip:** 48 deliberate breaks in a scratch copy, 47 caught by the check they targeted, 1 (wrong `next` for `write`) passed the five-situation comparison and was caught by 8 unit tests (note N-1).
- **Full local suite:** 6,510 passed, 1 failed; the failure was caused by `PYTHONDONTWRITEBYTECODE=1` in my own run (`test_batchsnap.py::TestSnapshotImmutable::test_verify_survives_cache_churn`), and passes without it.
- **Spot-checks:** baseline records hold; guard pattern under bash 3.2, zsh 5.9 and sh; all 47 paste sites double-quoted; CI green on `main` (`4ac7ee4`) and on the PR #10 head.

---

_Verified: 2026-11-15T23:50:00Z_
_Verifier: Claude (bm-verifier)_
