---
phase: 63-finalize-extraction-and-cross-call-variable-check
verified: 2026-11-16T03:38:17Z
status: passed
score: 5/5 must-haves verified
has_blocking_gaps: false
overrides_applied: 0
verifier_model: "Opus 5.5 (claude-opus-5-5); this round ran on Opus 5.5 instead of the configured Fable because of an account rate limit"
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  previous_verified: 2026-11-16T01:43:00Z
  gaps_closed:
    - "Gap 5 (D-28): a file name starting with ./ or ../, session in a subfolder. Fixed at 7079ab0 (`_pathspec_for_blob`: such a name goes to the two git diff checks as written; every other name gets the ../ lift). My own literal-2.14.1 harness, 513 comparisons (3 session folders x 19 name forms x 9 content changes) per Python version: 499 the same, 10 the D-19 shape, 4 the N-13 shape, 0 an edited file fingerprinted from a subfolder, identical on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5. The same harness against the pre-fix helper (29e1664) finds 12 edited files fingerprinted (wrong approvals) and 13 safe-direction differences, so it can see the defect."
    - "Gaps 1 (D-24), 2 (D-25), 3 (D-26): one end-to-end probe each (plus a twin) re-run on four Python versions; all give the 2.14.1 decision."
    - "Gap 4 (D-27): still an accepted difference; GIT_TIMEOUT = 60 unchanged."
  gaps_remaining: []
  regressions: []
  new_gaps: []
---

# Phase 63: Finalize extraction and cross-call variable check — Verification Report

**Phase Goal:** Finalize's mechanical steps run through tested stdlib helpers and behave exactly as in 2.14.1, with less model-interpreted prose on the same paths, and a shell variable read across Bash calls is caught by one general check in any phase file.
**Verified:** 2026-11-16T03:38:17Z, against branch `feat/v2.15-phase-63-gap` at `679648a` (three commits on top of the fourth verification commit `c5c642a`; `main` is at `4ac7ee4`; follow-up pull request #11 open, not merged; both CI runs on `679648a` green)
**Status:** passed
**Re-verification:** Yes — fifth round, after the fourth gap closure
**Verifier model:** this round ran on Opus 5.5, not the configured Fable, because of an account rate limit.

## Result in plain terms

- **Gap 5 is closed.** With the session in a subfolder and a finding whose file name starts with `./` or `../`, the helper now asks git about the same file in all three questions, as 2.14.1 did. The two rows from last round now match 2.14.1: session in `dir`, finding `./y.ts`, `dir/y.ts` edited or staged afterwards: both keep the finding open; only the top-level `y.ts` edited: both approve. Same result on Python 3.9, 3.12, 3.13 and 3.14.
- **Your D-19 promise holds.** Across about 2,700 comparisons of my own (four Python versions, odd file names, odd folder names, symlinks, case differences, git index settings), the helper never fingerprinted an edited or staged file from a subfolder. Every difference from 2.14.1 I found is one of the two D-19 shapes already on the result page: an edited file that 2.14.1 fingerprinted and the helper leaves out, or N-13 (a clean named file approved while a same-named file in the session folder was edited). At the repo top nothing differs from 2.14.1.
- **Gaps 1 to 3 stay closed and gap 4 stays accepted.** Re-probed on four Python versions.
- **The strengthened side-by-side test is a real safeguard.** I broke the helper three ways in a scratch copy and the test failed every time: putting the gap 5 defect back (38 differences, 15 of them wrong approvals: the executor's figures exactly), removing the D-19 fix, and putting the gap 3 defect back. Its D-19 allowance is as narrow as claimed.
- **CI now shows the grid's figures.** Both CI runs print the two summary lines. On Linux: 549 name scenarios (508 agree, 35 D-19, 6 N-13, 0 unexpected) and 284 scenarios (269 agree, 15 D-19, 0 unexpected, **0 not creatable**). So the 18 scenarios this Mac cannot create did run in CI.
- **Nothing else regressed.** Five situations match 2.14.1; Finalize is still 85 steps and 130,886 bytes; the stdlib-only gate reports 34 shipped files; the two test files pass under the default locale and `LC_ALL=C` on Python 3.12 and 3.9.
- **The records are accurate.** Every item I checked in the final section of the result page is true now, and since `main` the page has only had lines added, all in that section.
- **Score: 5 of 5. Status: passed.**
- **Expected and not counted as gaps:** no 63-11-SUMMARY.md, no `## Merge` section, the `Follow-up pull request:` placeholder line, backlog entries not filed, ROADMAP/STATE/REQUIREMENTS not ticked, pull request #11 not merged.

## Re-verification summary

| Item | Round 1 (`4ac7ee4`) | Round 2 (`66b0429`) | Round 3 (`48b307f`) | Round 4 (`29e1664`) | Now (`679648a`) |
|------|------|------|------|------|------|
| Status | gaps_found | gaps_found | gaps_found | gaps_found | **passed** |
| Score | 4/5 | 4/5 | 4/5 | 4/5 | **5/5** |
| Gap 1: leading-dash file names (D-24) | open | closed | closed | closed | closed (re-probed) |
| Gap 2: repo folder name ending in whitespace (D-25) | not found | open | closed | closed | closed (re-probed) |
| Gap 3: per-file git checks run in the root path (D-26) | not found | not found | open | closed | closed (re-probed) |
| Gap 4: 60-second limit per git call (D-27) | not noted | note | open, minor | accepted by name | accepted by name |
| Gap 5: `./` file names from a subfolder (D-28) | absent | absent | absent | open (regression) | **closed** |

### What I ran now and what I carried

| Criterion | Now | How |
|-----------|-----|-----|
| 1 (same decisions as 2.14.1) | **Re-ran** | Everything in "Gap closure evidence", "Attack on the new rule", "The strengthened grid as a safeguard" and "Regression checks" below |
| 2 (bad inputs stop; nothing written; restart works) | **Carried**, partial re-run | The diff since `c5c642a` touches only `_head_blobs`'s pathspec choice and two test files. Re-ran: the five-situation comparison (includes `one-rebuild`, `refused-close`, `fresh-shell-restart`, and the refusal lines) and all of `test_finalize_inputs.py` |
| 3 (superseded prose removed, invariants kept) | **Carried** | `git diff c5c642a 679648a --stat` outside `.planning`: `finalize_inputs.py`, `test_finalize_inputs.py`, `test_finalize_parity_grid.py` only. No instruction file changed |
| 4 (before/after counts, revert rule) | **Re-ran the counts**, carried the rest | 85 steps and 130,886 bytes at `679648a` |
| 5 (the general cross-call check) | **Carried** | No phase file and no check file changed |

I did not run the full suite (the main session's run on `679648a`: 6545 passed, 0 failed; CI as below).

## Goal Achievement

### Observable Truths (roadmap success criteria — the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline | ✓ VERIFIED | Gaps 1, 2, 3 and 5 closed; gap 4 accepted (D-27). Every remaining difference I could produce is D-19 (with N-13), on the accepted list. Five situations match. |
| 2 | Missing, malformed or stale Finalize inputs stop with a plain message; a failed or refused attempt writes no report and archives nothing; restart and retry work across fresh shell calls | ✓ VERIFIED (carried; partial re-run) | Five-situation comparison and its refusal lines identical to 2.14.1 at `679648a`; helper tests pass. |
| 3 | Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host | ✓ VERIFIED (carried) | No file under this truth changed. |
| 4 | Loaded prose and helper/tool steps on the same Finalize paths are compared before and after against the Phase 62 criterion; the slice is reverted if it adds complexity without a demonstrated benefit | ✓ VERIFIED (counts re-run) | `step_count.py --rev HEAD --json`: 85 steps (35 fences, 5 inline commands, 5 Write-tool writes, 40 paste sites). `plugins/vibe-check/scripts/footprint.py --rev HEAD --json`: Finalize 130,886 bytes. |
| 5 | One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips; any phase file it flags is recorded with its reproduction before it is changed | ✓ VERIFIED (carried) | No file under this truth changed. |

**Score:** 5/5 truths verified

### Deferred Items

None.

### How the comparison was made (all run by me, scratch only)

Under the session scratch folder (`…/scratchpad/v6`): a fresh clone at `679648a`, and `git archive` copies of `dd8e4ab` (2.14.1) and `29e1664` (the pre-fix helper, as a control). Nothing in the working checkout was touched. `guard.py`, `carry_state.py`, `finalize_gate.py`, `batch_card.py` and `fixcommit.py` are byte-identical between `dd8e4ab` and `679648a`.

- **2.14.1 side** (my own harness, written fresh this round, not the project's test code or its fixture script): the `^[A-Za-z0-9._/-]+$` filter, then one `/bin/sh -c` in the session folder running the dd8e4ab line 13 text with `<file>` substituted as written: `python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"`, `blob=$(git rev-parse "HEAD:<file>")`, `git diff --quiet HEAD -- <file>` (unquoted, as in the text), `git diff --cached --quiet -- <file>`; kept only when all exit 0; then `carry_state.py finalize-counts` and `finalize_gate.py` from `dd8e4ab`. The guard's stdout is discarded; only its exit code counts, as the text says.
- **Helper side:** `finalize_inputs.py` at `679648a` run as a command from the same session folder, same interpreter, same environment.
- **An independent dirty check:** for every comparison the harness works out which file `HEAD:<name>` read, by git's own rule (a `./` or `../` name from the session folder, any other name from the top), and asks `git status -- ':(top,literal)<that file>'` whether it is edited or staged. A helper fingerprint of such a file from a subfolder is flagged whatever 2.14.1 did.
- A case is "same" only when the fingerprint map, the three counts and the gate action are all equal.
- I checked `fixtures/finalize_step1_2141.sh` against `git show dd8e4ab:plugins/vibe-check/phases/shared/90-finalize.md` lines 13–22 myself: same filter, same guard line, the same three git commands, kept only when all three exit 0, no change of folder. It is faithful (its only liberty, quoting `<file>`, cannot matter for names that pass the filter). My harness does not use it.

### Gap closure evidence (step 1 of the request)

**Gap 5, the rows from round 4** (repo with `y.ts`, `dir/y.ts`, `dir/deep/y.ts` and others with different content; fix-obsolete verdict on the blob `git rev-parse HEAD:<name>` gives in the session folder):

| Session | Finding file | Change after the verdict | 2.14.1 | Helper at `679648a` | Pre-fix helper `29e1664` (control) |
|---------|--------------|--------------------------|--------|---------------------|------------------------------|
| `dir` | `./y.ts` | none | [0,0,0] `write` | same | same |
| `dir` | `./y.ts` | `dir/y.ts` edited | [1,0,0] `outstanding-to-phase-5` | **same** | [0,0,0] `write` (wrong approval) |
| `dir` | `./y.ts` | `dir/y.ts` staged | [1,0,0] `outstanding-to-phase-5` | **same** | [0,0,0] `write` (wrong approval) |
| `dir` | `./y.ts` | top-level `y.ts` edited, `dir/y.ts` unchanged | [0,0,0] `write` | **same** | [1,0,0] (safe direction) |
| `dir/deep` | `./y.ts`, `.//y.ts`, `./k.ts`, `./deep/../y.ts` | the session folder's file edited | [1,0,0] | **same** | [0,0,0] `write` |
| `dir` | `./deep/y.ts`, `./n.ts`, `.//y.ts`, `./deep/../y.ts` | the file they name edited or staged | [1,0,0] | **same** | [0,0,0] `write` |

**The matrix:** sessions top / `dir` / `dir/deep` × 19 names (`y.ts`, `./y.ts`, `../y.ts`, `dir/y.ts`, `./dir/y.ts`, `../dir/y.ts`, `./deep/y.ts`, `../repo/y.ts`, `../repo/dir/y.ts`, `./../y.ts`, `.//y.ts`, `./k.ts`, `n.ts`, `./n.ts`, `dir/../y.ts`, `dir/./y.ts`, `./deep/../y.ts`, `../../y.ts`, `../deep/y.ts`) × 9 changes (none; top `y.ts` edited / staged; `dir/y.ts` edited / staged; `dir/deep/y.ts` edited; `dir/n.ts`, `n.ts`, `dir/deep/k.ts` edited) = 513 comparisons.

| Helper | Python | Same | D-19 shape | N-13 shape | Edited file fingerprinted from a subfolder | Other |
|--------|--------|------|------------|------------|------|------|
| `679648a` | 3.9.6, 3.12.12, 3.13.14, 3.14.5 (output byte-identical across the four) | 499 | 10 | 4 | **0** | 0 |
| `29e1664` (control) | 3.14.5 | 474 | 10 | 4 | 12 | 13 (safe direction, same mechanism) |

All 14 non-identical rows at `679648a` are plain names (`y.ts`, `n.ts`, `dir/y.ts`) with the session below the top. Every `./` and `../` name, from every session, gives the 2.14.1 result. **At the repo top every comparison is the same.**

**Gaps 1, 2, 3, one probe each plus a twin, identical on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5:**

| Probe | 2.14.1 | Helper |
|-------|--------|--------|
| Gap 1: top-level `-x.ts`, unchanged | [1,0,0] `outstanding-to-phase-5` | same |
| Gap 1 control: `x.ts`, unchanged | [0,0,0] `write` | same |
| Gap 2: repo `repo ` beside repo `repo`, real file edited | [1,0,0] `outstanding-to-phase-5` | same |
| Gap 2: repo folder ending in a tab, unchanged | [0,0,0] `write` | same |
| Gap 3: `core.worktree` → another repo, staged edit in the session's repo | [1,0,0] `outstanding-to-phase-5` | same |
| Gap 3: folder name ending in a line break beside repo `repo`, real file edited | [1,0,0] `outstanding-to-phase-5` | same |

**Is an edited file ever fingerprinted from a subfolder?** Not by the helper's mechanism, in any comparison I ran (about 2,700 across this section and the next, counting each Python version). The only edited files fingerprinted by both sides are ones git itself has been told to ignore (note N-17). **Does anything at the repo top differ from 2.14.1?** No.

### Attack on the new rule (step 2 of the request)

The rule: a name starting with `./` or `../` goes to the two checks as written; anything else gets one `../` per folder level. It is right exactly when git reads `HEAD:<name>` relative to the session folder for those names and from the top for all others. git's source (`resolve_relative_path` in `object-name.c`) applies the relative reading only to names starting with `./` or `../`, so `.` and `..` alone are read from the top. Every case below was run end to end against the literal 2.14.1 procedure on Python 3.14.5 (git 2.55.0, case-insensitive APFS).

| Set-up | Runs | Result against 2.14.1 | D-19 promise held? |
|--------|------|-----------------------|--------------------|
| Session `dir`: `.//n.ts`, `.`, `..`, `./`, `./.`, `./-x.ts`, `./.../x`, `./..x/y`, `./dir/.`, `./dir`, `./x.ts/`, `../dir/n.ts`, `../repo/dir/n.ts`; session top: `.`, `./` | 3 to 5 each (clean; the file named and its twin edited, staged) | same in every run (the directory-naming forms fail or agree on both sides) | yes |
| Session `dir/deep`: `./../n.ts`, `./../dir/n.ts`, `.././n.ts` | 5 each | same | yes |
| `./` or `../` only in the middle (`dir/./n.ts`, `dir/../n.ts`, `dir//n.ts`), trailing `/.` (`dir/.`), trailing `/` (`x.ts/`) | 5 each | same (git cannot read these from HEAD; left out on both sides) | yes |
| Plain names with dots: `.../x`, `..x/y` (folders `...` and `..x` exist at the top and in `dir`) | 5 each | top file edited: D-19 shape; twin in `dir` edited: N-13 shape; otherwise same | yes |
| A name equal to the session folder (`dir`, `dir/`, session in `dir`; git gives a tree id) | 5 each | `dir/n.ts` edited: D-19 shape (2.14.1 checks `dir/dir`); otherwise same | yes |
| Session folders named `*`, `?`, `[ab]`, `[`, `*x*`, `:x`, `:`, `a:b`, `--`, `-p` (and `a`, a control), names `y.ts`, `./y.ts`, `../y.ts`, six changes each | 216 | every `./` and `../` name the same; `y.ts`: D-19 shape (top edited) or N-13 shape (twin in the folder edited) | yes |
| Session reached through a symlink from outside the repo, and through a symlink inside it (`ldir` → `dir`); `y.ts`, `./y.ts`, `../y.ts`, `./deep/y.ts` | 40 | `./` and `../` names the same; `y.ts` D-19 / N-13 shapes | yes |
| Case: session folder typed `DIR` for `dir`; names `./y.ts`, `./Y.ts`, `y.ts`, `Y.ts`, `DIR/y.ts`, `dir/Y.ts` | 24 | same, except `y.ts` D-19 / N-13 shapes | yes |
| Case twins across levels: top `Y.ts`, `dir/y.ts`, session `dir`, `./y.ts`, `./Y.ts`, `Y.ts`, `y.ts` | 12 | same, except `Y.ts` with `Y.ts` edited (D-19 shape) | yes |
| Case collision: `dir/y.ts` and `dir/Y.ts` both committed (one file on this disk), session top and `dir` | 16 | `./` names the same; plain `dir/Y.ts`, `dir/y.ts` from `dir`: D-19 shape (git reports the named file modified) | yes |
| `GIT_LITERAL_PATHSPECS`, `GIT_GLOB_PATHSPECS`, `GIT_NOGLOB_PATHSPECS`, `GIT_ICASE_PATHSPECS` with `./y.ts`, `../y.ts`, `./deep/y.ts` from `dir` | 48 | same | yes |
| `assume-unchanged` / `skip-worktree` on `y.ts` or `dir/y.ts`; sessions top and `dir`; `y.ts`, `./y.ts`, `dir/y.ts` | 72 | same, except plain names from `dir` in the D-19 shape | yes, see N-17 |
| Intent-to-add entries (`z.ts`, `dir/z.ts` added with `-N`), sessions top and `dir` | 20 | same | yes |
| Sparse checkout (only `/y.ts`; only `/dir/`), sessions top and `dir` | 18 | same, except `dir/y.ts` from `dir` edited (D-19 shape) | yes |

Totals for this section: 595 runs; 512 the same; 83 differ, every one a plain name with the session below the top in the D-19 shape (2.14.1 fingerprints an edited file, the helper leaves it out) or the N-13 shape (the named file clean, a same-named file in the session folder edited). **No new mechanism. No helper fingerprint of an edited or staged file from a subfolder.**

Not probed: a session folder whose name is not valid UTF-8 (this disk refuses it; CI's grid covers the folder-name case on Linux), Windows, a network disk.

### The strengthened grid as a safeguard (step 3 of the request)

| Question | Finding |
|----------|---------|
| Is the D-19 allowance as narrow as claimed? | Yes. Name-form grid (`nf_classify`): a difference is allowed only when the session is below the top, the name does not start with `./` or `../`, the file git reads from HEAD and the file the 2.14.1 checks address both exist and differ, the helper's whole outcome equals the exact D-19 prediction (map and decision), and either the named file (D-19) or the session folder's twin (N-13) is the one changed. First grid (`d19_difference`): session below the top, content edited, not a `./`/`../` name, 2.14.1 fingerprints exactly that file with its HEAD blob, the helper leaves exactly that file out, everything else equal, and both decisions as D-19 predicts. `test_session_relative_names_never_differ` and `test_no_difference_at_the_repo_top` add flat asserts. |
| N-13 as asserted rows | Yes: three rows in `NF_D19_ROWS` (`sub` edited / staged with the session in `dir`; `deep` edited with the session in `dir/deep`), each asserting both maps and both decisions, plus at least 3 N-13 scenarios overall. |
| Name forms my step 2 found that the grid lacks | Names that name a folder (`dir`, `dir/`, `./`, `.`), `.//`, `.../x`, `..x/y`, `./-x.ts`, session folders with pathspec characters, index flags. None of them broke the rule, so I do not count any as an obvious missing class; folder-naming names and `.//` would be the cheapest additions if the grid is ever widened. |
| Always lift (gap 5 restored) | **Fails.** Name grid `470 agree, 35 D-19, 6 N-13, 38 unexpected`; failing: the agreement test, 9 regression rows, 18 `./`-name subtests; `--grid` exit 1. Against the actual pre-fix helper `29e1664` I counted 38 unexpected, **15 wrong approvals** — the executor's figures. |
| Never lift (D-19 removed) | **Fails.** Both grids agree everywhere (549 and 266 agree, 0 D-19), so only the D-19 rows catch it: 7 name-grid and 7 first-grid D-19 subtests fail; `--grid` exit 1. |
| Root as cwd (gap 3 restored) | **Fails.** Name grid 84 unexpected; first grid 18 unexpected (the records say 20 for their version of this mutant; mine also drops the D-19 lift, which is the pre-`08f0018` shape); `--grid` exit 1. |
| Unmodified | pytest: 19 passed, 692 subtests; `--grid` exit 0. |
| `--grid` exits 1 on any grid assertion failure | Yes for all three mutants. |
| Not creatable on Linux must be empty | `test_everything_is_creatable_on_linux` asserts it on Linux. On this Mac 18 scenarios are not creatable (the folder name holding a byte that is not valid text), as before. |
| **CI evidence** | `gh run view 43791899524 --log` (push) and `43791905432` (pull request), both on `679648a92c6a`, both `success`, Ubuntu, Python 3.14, git 2.56.1. Each warnings section prints `GridSummary: 549 name-form scenarios … 508 agree, 35 D-19, 6 D-19 second direction (N-13), 0 unexpected, 0 off the git model` and `GridSummary: 284 scenarios … 269 agree, 15 D-19, 0 known differences, 0 unexpected, 0 not creatable here`. Totals: `4588 passed, 2 skipped, 5 deselected, 2 warnings, 6464 subtests passed` (the two warnings are those lines). **So the 18 Mac-uncreatable scenarios ran on Linux in CI and agreed.** |

### Regression checks (step 4; scratch clone at `679648a`)

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 2.14.1 record reproducible | `finalize_capture.py verify --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json` | `finalize baseline matches (5 situations)`, exit 0 | ✓ PASS |
| Five situations, by commit | `finalize_capture.py compare … --driver helper --commit HEAD` on Python 3.14.5 and 3.9.6 | `finalize outcome fields match (5 situations, 7 walks)`, exit 0, both; refusal lines identical to 2.14.1 | ✓ PASS |
| Five situations, by folder | the same with `--root plugins/vibe-check` | the same line, exit 0 | ✓ PASS |
| Helper and grid tests, default locale | bare `pytest test_finalize_inputs.py test_finalize_parity_grid.py` (pytest on Python 3.12.12) | 143 passed, 893 subtests; 549: 508/35/6/0; 284: 254/12/0 unexpected/18 not creatable | ✓ PASS |
| The same, `LC_ALL=C` | the same | 143 passed, same figures | ✓ PASS |
| The same, Python 3.9.6 | `/usr/bin/python3 -m unittest test_finalize_inputs test_finalize_parity_grid`, default and `LC_ALL=C` | 143 tests OK, both, same figures | ✓ PASS |
| Stdlib-only gate | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | `34 shipped .py files; third-party imports: none`, exit 0 | ✓ PASS |
| Shipped-module count lock | `pytest .github/scripts/test_stdlib_only.py` | 21 passed | ✓ PASS |
| Finalize steps | `step_count.py --rev HEAD --json` | 85 | ✓ PASS |
| Finalize bytes | `plugins/vibe-check/scripts/footprint.py --rev HEAD --json` | 130,886 | ✓ PASS |
| Files changed outside `.planning` since `c5c642a` | `git diff --stat` | `finalize_inputs.py`, `test_finalize_inputs.py`, `test_finalize_parity_grid.py` | ✓ PASS |

### Records, checked against what is true now (step 5)

`git diff 4ac7ee4 HEAD -- …/63-RESULT.md`: one hunk (`@@ -325,3 +325,94 @@`), 91 lines added, 0 removed, all after line 325, which is inside the post-merge section ("Correction after the merge" and its subsections). Additions only, as required.

| Record | Claim | Check | Holds? |
|--------|-------|-------|--------|
| "Third correction" | the corrected sentence: the lift applied to every name in `08f0018`, wrong for `./`/`../` names, now given as written | code at `679648a` and my matrix | Yes |
| "Fourth correction" | mechanism; session `dir`, `./y.ts`, `dir/y.ts` edited or staged: 2.14.1 and `main` open, helper approved; only top `y.ts` edited: helper kept open | my control run on `29e1664` | Yes |
| "Fourth correction" | fix `7079ab0`: `./`/`../` names as written, every other name lifted; five situations still match; 85 steps, 130,886 bytes | code; my re-runs | Yes |
| "Fourth correction" | pre-fix: 38 differences, 15 wrong approvals, all `./`/`../` names from a subfolder | my run of the name grid against `29e1664`: 38 unexpected, 15 wrong approvals | Yes |
| "Fourth correction" | 17 name shapes, three session levels, 549 more scenarios; checks real git for which file each question reads | `NF_FORMS` + `NF_SECONDARY_FORMS` + `NF_REENTRY_FORMS` = 17 distinct; 315 + 180 + 54 = 549; `test_model_is_what_git_does` present | Yes |
| "The side-by-side test", N-13 sentence | D-19's second direction described; `main` behaves so; held as D-19 rows | my matrix (4 N-13 shapes); `NF_D19_ROWS` has three such rows | Yes |
| "The side-by-side test" | 833 scenarios; known-differences list empty | 284 + 549; `KNOWN_DIFFERENCES = ()` | Yes |
| "The side-by-side test" | fails if anything is not creatable on Linux | `test_everything_is_creatable_on_linux`; CI prints 0 not creatable | Yes |
| "The side-by-side test" | Linux container: all 833 created, none outside D-19 | not re-run by me; CI on Linux shows the same (0 unexpected, 0 not creatable, 0 off the git model) | Yes (by CI evidence) |
| "The side-by-side test" | summary lines shown as warnings in test output | both CI logs | Yes |
| "The side-by-side test" | timing: each grid 15 to 25 s | my runs 14 to 23 s | Yes |
| 63-REPRO.md gap 5 section | mutation matrix: always lift 38, never lift 0 unexpected and D-19 rows fail, root as cwd 20 / 84 | mine: 38; never-lift as stated; root as cwd 18 / 84 (my mutant shape differs slightly) | Yes (minor count variance for one mutant) |
| `finalize_inputs.py` docstring | `HEAD:<file>` relative for `./`/`../` names, from the top otherwise; per-form table | matches git's source rule and my runs | Yes (corrected since round 4) |

### Differences from 2.14.1 found in the code, against the accepted list

| Difference in the code | Accepted? |
|------------------------|-----------|
| Unreadable state file: shell's "Permission denied" line no longer shown | Yes — `## Your decision` item 1 |
| Unsafe folder, branch or phase names stop the review (D-21) | Yes — item 2 |
| Byte growth on every review path at phase end | Yes — item 3 |
| Corrupted (non-UTF-8) state file on a C locale shows a different refusal line | Yes — item 4 |
| Subfolder fix (D-19), both directions (N-13 written on the page) | Yes — D-19, D-28 |
| Close out and fix loop keep the state path (D-20, D-23); inline Python isolated (D-22) | Yes |
| 60-second limit per git call | Yes — D-27 |
| ~~Leading-dash names~~, ~~folder name ending in whitespace~~, ~~per-file checks in the root path~~, ~~`./` names from a subfolder~~ | Removed by D-24, D-25, D-26, D-28: the helper matches 2.14.1 |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/finalize_inputs.py` | the one helper call | ✓ VERIFIED | `_pathspec_for_blob` used by both `git diff` checks; all three per-file calls in the session folder |
| `plugins/vibe-check/scripts/fixtures/finalize_step1_2141.sh` | the literal 2.14.1 step | ✓ VERIFIED | faithful; pinned |
| `plugins/vibe-check/scripts/test_finalize_parity_grid.py` | the side-by-side test | ✓ VERIFIED | 833 scenarios; fails on all three mutants; CI prints its figures |
| `plugins/vibe-check/scripts/test_finalize_inputs.py` | parity, exit codes, mutants | ✓ VERIFIED | `TestSessionRelativeNames` and the lift-every-name mutant added |
| Other artifacts | as before | ✓ VERIFIED (carried; unchanged) | |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `finalize_inputs.py` | per-file git | `_git(..., cwd)` in the session folder | ✓ WIRED |
| `finalize_inputs.py` | the D-19 lift | `_pathspec_for_blob(f, up)` in both `git diff` calls | ✓ WIRED (plain names lifted, `./`/`../` names as written; the three mutants fail the grid) |
| `finalize_inputs.py` | `guard.py`, `carry_state.py`, `finalize_gate.py`, `batch_card.py` | in-process calls | ✓ WIRED (five situations re-run) |
| `test_finalize_parity_grid.py` | the 2.14.1 text | `TestStep1ScriptIsPinned` | ✓ WIRED (carried; passes) |
| CI workflow | the grid module | collected; summary lines in both logs | ✓ WIRED |

### Data-Flow Trace, Spot-Checks, Probes

Not applicable (no artifact renders dynamic data; no `scripts/*/tests/probe-*.sh` probes are declared). The comparisons above are the spot-checks.

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| FINX-01 | Helpers on the single-writer path; same gate decisions and reports as the baseline | ✓ SATISFIED | Truth 1 |
| FINX-02 | Bad inputs fail visibly; a failed attempt writes and archives nothing | ✓ SATISFIED | Truth 2 (carried, partial re-run) |
| FINX-03 | Restart and retry across fresh shells | ✓ SATISFIED | Truth 2 |
| FINX-04 | Superseded prose and locks removed; invariants kept | ✓ SATISFIED | Truth 3 (carried) |
| FINX-05 | Before/after comparison; revert if no benefit | ✓ SATISFIED | Truth 4 |
| XVAR-01 | One general check with a mutant | ✓ SATISFIED | Truth 5 (carried) |
| XVAR-02 | Flagged files recorded with reproduction before change | ✓ SATISFIED | Truth 5 (carried) |

No orphaned requirement.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| files changed since `c5c642a` | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` | none found | — |
| `test_finalize_parity_grid.py` | the `--grid` exit-0-when-D-19-rows-vanish weakness from round 4 | resolved | `--grid` now runs the D-19 row tests; never-lift exits 1 |
| `test_finalize_parity_grid.py` | no Linux assertion on the not-creatable list (round 4 warning) | resolved | `test_everything_is_creatable_on_linux` |

### Notes (not gaps)

- **N-1 to N-16** are carried from the earlier reports (N-7 is the accepted D-27; N-13 is now on the result page as part of D-19).
- **N-17. Git index flags that hide edits.** With `assume-unchanged` or `skip-worktree` set on the file, git reports an edited file as unchanged, so both 2.14.1 and the helper fingerprint it and approve, at the top and from a subfolder alike. This is git doing what the user told it, identical to 2.14.1, and not the subfolder mechanism D-19 is about; not a difference.
- **N-18. Names that name a folder** (`dir`, `dir/`, `./`, `.` where git resolves it) give a tree id rather than a file's blob. The verdict comparison then works on that id. Both sides behave identically except the plain-name D-19 shape; recorded only because the grid does not include such names.
- **N-19. Root-as-cwd mutant count.** My version of that mutant gives 18 unexpected in the first grid where the records give 20; mine also removes the lift. Both fail the grid; the difference is in the mutant, not the test.

### Human Verification Required

None. Carried from the first report, as an observation and not a request: no live review was run, so a live model filling the three switch slots, pasting the printed state path and branching on `next` has been observed only in scripted walks. Under the standing rule a live or paid run needs its own approved proposal; this report does not ask for one.

### Gaps Summary

None open. Gap 5 is closed: the helper sends a `./` or `../` name to the two change checks as written, so all three git questions are about one file, as at 2.14.1, and plain names keep the D-19 lift. My own harness, independent of the project's tests, finds no difference from 2.14.1 outside D-19 (with N-13) on four Python versions, including the forms the request named to attack. The pre-fix helper fails the same harness, so the harness can see the defect. The strengthened grid fails on the three mutants it should, its D-19 allowance is narrow, and CI now prints its figures, including 0 not creatable on Linux. The records describe what is true.

### Residual risk (my judgement, separate from the status)

The per-file step is now literally 2.14.1's at the repo top. From a subfolder it differs only by a one-condition rule that follows git's own source rule for `HEAD:<name>` (`./` and `../` only). I attacked that rule from every angle the request named and found nothing outside D-19. The remaining exposure is new git versions changing how names are read (the grid's `test_model_is_what_git_does` would catch that in CI), and set-ups nobody has named. I put the chance of a further decision difference of this kind at about one in ten, lower than last round. The chance that one would touch a real review is very low, because every trigger found in five rounds has needed an unusual file name or folder set-up together with an edit after the fix verdict.

---

## History: fourth verification (2026-11-16T01:43:00Z, `29e1664`)

**Status then:** gaps_found. **Score then:** 4/5. Gaps 1 to 3 closed, gap 4 accepted (D-27). One gap open then: gap 5 (blocking: `./` file names from a subfolder, a regression from the gap 3 fix; closed in round 5 by D-28 / `7079ab0`). The frontmatter of that round recorded the gap with its artifacts and fixes; the report of that round follows unchanged, with its headings moved one level down.

That round's frontmatter `gaps:` entry, kept for the record:

```yaml
gaps:
  - truth: "Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline"
    status: partial
    severity: blocking
    reason: "The new D-19 mechanism (ask git how many folder levels the session is below the top, put that many ../ before the file name in the two git diff checks) is wrong for a file name that starts with ./ (or ../). git reads `HEAD:./y.ts` relative to the session folder, so the blob is the session folder's y.ts; the helper then checks `.././y.ts`, the file at the top, for changes. The blob comes from one file and the changed-check looks at another. At 2.14.1 all three commands ran in the session folder with the same name, so they agreed with each other. Reproduced end to end on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5 (macOS, git 2.55.0) and on Linux (Ubuntu 24.04, Python 3.12.3, git 2.43.0). (a) Unsafe direction: session in `dir`, finding file `./y.ts`, fix-obsolete verdict on the HEAD blob, `dir/y.ts` then edited or staged: 2.14.1 [1,0,0] `outstanding-to-phase-5`; helper [0,0,0] `write`, an approval 2.14.1 would not give. The merged helper at 4ac7ee4 and the helper at 48b307f both give [1,0,0] `outstanding-to-phase-5` here, so this is a regression introduced by 08f0018. (b) Safe direction: the same with `dir/y.ts` unchanged and a top-level `y.ts` edited: 2.14.1 [0,0,0] `write`; helper [1,0,0] `outstanding-to-phase-5`. (c) Safe direction: finding file `../repo/y.ts` from a subfolder, unchanged: 2.14.1 [0,0,0] `write`; helper [1,0,0] (the lifted name points outside the repository and git refuses it). In my matrix 26 of 369 comparisons (plain) and 32 of 312 (with GIT_* pathspec variables, GIT_PREFIX, GIT_DIR+GIT_WORK_TREE) are an edited file fingerprinted; every one is a ./ name from a subfolder. At the repo top the three calls are 2.14.1's own and nothing differs. This is not D-19 (D-19 is recorded as 'an edited file is never fingerprinted'; here one is) and not on the accepted list."
    artifacts:
      - path: "plugins/vibe-check/scripts/finalize_inputs.py"
        issue: "`_head_blobs` lines 222-228: `rev-parse HEAD:<f>` is run with the name as given (session-relative when it starts with ./ or ../), but both `git diff` checks are given `up + f`. The docstring line 'git reads HEAD:<file> from the top of the work tree whatever the cwd' is not true for such names."
      - path: "plugins/vibe-check/scripts/test_finalize_parity_grid.py"
        issue: "The grid cannot see this. Its only ./ name is `./x.ts` and no fixture folder below the top holds an `x.ts`, so `HEAD:./x.ts` fails from every subfolder and both sides leave the file out. A helper with the defect and a helper with it fixed give the identical grid result (252 agree, 14 D-19, 0 unexpected)."
      - path: "plugins/vibe-check/scripts/test_finalize_inputs.py"
        issue: "The subfolder tests (`TestSubdirectoryCwd`, `test_exact_git_calls_from_a_nested_subfolder`) use plain names only; no test uses a ./ name from a subfolder."
      - path: ".planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-RESULT.md"
        issue: "'Third correction' says the two checks 'still read the file from the top' and that the D-19 rule is kept; line 170 (owner-approved section, left as approved) says 'Now that cannot happen'. For a ./ name from a subfolder it can at 29e1664. 63-REPRO.md says 'the grid's ./x.ts row agrees with 2.14.1 because both read it in the session folder', which holds only at the repo top."
    missing:
      - "In `_head_blobs`, give the two git diff checks the name unchanged when git reads it relative to the session folder (it starts with ./ or ../), and the lifted name otherwise. In a scratch copy this one-condition change makes every ./ row equal 2.14.1 (matrix of 369: 269 same, 96 D-19, 4 note N-13, 0 edited files fingerprinted) and leaves the grid result unchanged."
      - "Grid: a fixture file with the same name at the top and in the session folder (for example `dir/x.ts` beside `x.ts`), `./y.ts` as a name with a session in `dir`, and named rows for (a), (b) and (c) with their 2.14.1 outcomes; a mutant that lifts every name must fail them."
      - "A ./ name case from a subfolder in `test_finalize_inputs.py` with fixed expected results."
      - "Records: correct the 'still read the file from the top' sentence in the result page's third correction, the 63-REPRO.md sentence about the ./x.ts row, and the helper docstring."
```

### Result in plain terms

- **Gap 3 is closed.** The three "is this file unchanged" git questions are asked in the session's own folder again, as at 2.14.1. All four rows I reported last round now give the 2.14.1 decision, on four Python versions. Nothing in that class disagrees in either direction.
- **Gap 4 is settled.** The 60-second limit is still in the code and is on the result page as a sixth accepted difference, with your words quoted. It is no longer a gap.
- **Gaps 1 and 2 are still closed.** Re-probed on four Python versions: 72 cases each, no disagreement.
- **One new blocking gap, and this one was introduced by the gap 3 fix.** It is not on `main`; it exists only on the open pull request #11. To keep your D-19 rule the fix puts `../` in front of the file name in two of the three git questions when the session is in a subfolder. That is right for an ordinary name like `dir/y.ts`. It is wrong for a name written with a leading `./`, because git reads such a name relative to the session's folder, not the repo top. The helper then takes the fingerprint from one file and checks a different file for changes. Result, with the session in a subfolder and a finding whose file is written `./y.ts`: after the file is edited, 2.14.1 keeps the finding open and the helper approves the review. That is an edited file being fingerprinted from a subfolder, the thing D-19 exists to prevent, and the helper on `main` does not do it.
- **How much it matters.** It needs three things together: a review session started in a subfolder of the repo, a finding whose file name was recorded with a leading `./`, and an edit to that file after the "fix made this obsolete" verdict. I did not see the plugin write a `./` name, and nothing in this path strips one. The file name comes from the reviewed change (the 2.14.1 instructions themselves call it untrusted), so unlike gaps 2 and 3 it does not depend only on the reviewer's own folder names. It is graded blocking by the standard you set for this round: an edited file fingerprinted from a subfolder.
- **The side-by-side test is a real safeguard, with one blind spot that hid this gap.** Its 2.14.1 script is a faithful copy of the 2.14.1 text and the pin fails on every edit I tried. Root-as-cwd restored, the `../` removed, and "fingerprint everything" all fail it. But its test repos have no file with the same name at the top and in a subfolder, so its one `./` name never resolves from a subfolder. A helper with this defect and a helper without it produce the identical grid result.
- **The Linux-only scenarios.** The CI logs cannot show whether the 18 scenarios this Mac cannot create ran: the log has only the totals line, and the grid's own report is not printed for a passing test. I ran the grid myself in an Ubuntu container: 284 scenarios, 0 not creatable, 0 unexpected. So they do run and pass on Linux; that is my run, not CI evidence.
- **Nothing else has regressed.** Five situations match 2.14.1; Finalize is 85 steps and 130,886 bytes; the stdlib-only gate reports 34 shipped files; the two test files pass under the default locale and `LC_ALL=C` on Python 3.14 and 3.9.
- **Score: 4 of 5.**
- **Expected and not counted as gaps:** no 63-11-SUMMARY.md, no `## Merge` section, the `Follow-up pull request:` placeholder line, backlog entries not filed, ROADMAP/STATE/REQUIREMENTS not ticked, pull request #11 not merged.

### Re-verification summary

| Item | Round 1 (`4ac7ee4`) | Round 2 (`66b0429`) | Round 3 (`48b307f`) | Now (`29e1664`) |
|------|---------------------|---------------------|---------------------|-----------------|
| Status | gaps_found | gaps_found | gaps_found | gaps_found |
| Score | 4/5 | 4/5 | 4/5 | 4/5 |
| Gap 1: leading-dash file names (D-24) | open, blocking | closed | closed | closed (re-probed) |
| Gap 2: repo folder name ending in whitespace (D-25) | not found | open, blocking | closed | closed (re-probed) |
| Gap 3: per-file git checks run in the root path (D-26) | not found | not found | open, blocking | **closed** |
| Gap 4: 60-second limit per git call (D-27) | not noted | note | open, minor | **accepted by name** |
| Gap 5: `./` file names from a subfolder | absent | absent | absent | **open, blocking (regression from the gap 3 fix)** |

#### What I ran now and what I carried

| Criterion | Now | How |
|-----------|-----|-----|
| 1 (same decisions as 2.14.1) | **Re-ran** | Everything in "Gap closure evidence", "The D-19 mechanism under attack", "The side-by-side test as a safeguard" and "Regression checks" below |
| 2 (bad inputs stop; nothing written; restart works) | **Carried**, with a partial re-run | The diff touches only the fingerprint step. Re-ran: the five-situation comparison (includes `one-rebuild`, `refused-close`, `fresh-shell-restart`) and all of `test_finalize_inputs.py`. Not re-run: the real fence under bash and zsh against the six fault cases |
| 3 (superseded prose removed, invariants kept) | **Carried** | `git diff 38ed24f 29e1664 -- plugins docs .github` touches `finalize_inputs.py`, `test_finalize_inputs.py`, and the two new test files only |
| 4 (before/after counts, revert rule) | **Re-ran the counts**, carried the rest | 85 steps and 130,886 bytes at `29e1664` |
| 5 (the general cross-call check) | **Carried** | No phase file and no check file changed |

The full local suite was not run by me (one was in progress in the working checkout, per instruction).

### Goal Achievement

#### Observable Truths (roadmap success criteria — the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline | ✗ FAILED (partial) | Gaps 1 to 3 are closed and gap 4 is accepted. One mechanism differs and is not on the accepted list: gap 5. |
| 2 | Missing, malformed or stale Finalize inputs stop with a plain message; a failed or refused attempt writes no report and archives nothing; restart and retry work across fresh shell calls | ✓ VERIFIED (carried; partial re-run) | Earlier evidence stands. The five-situation comparison and the helper tests pass at `29e1664`. |
| 3 | Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host | ✓ VERIFIED (carried) | No file under this truth changed. |
| 4 | Loaded prose and helper/tool steps on the same Finalize paths are compared before and after against the Phase 62 criterion; the slice is reverted if it adds complexity without a demonstrated benefit | ✓ VERIFIED (counts re-run) | `step_count.py --rev HEAD --json`: 85 steps (35 fences, 5 inline commands, 5 Write-tool writes, 40 paste sites). `footprint.py --rev HEAD --json`: Finalize 130,886 bytes. |
| 5 | One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips; any phase file it flags is recorded with its reproduction before it is changed | ✓ VERIFIED (carried) | No file under this truth changed. |

**Score:** 4/5 truths verified

#### Deferred Items

None. Phase 65 (release gate) names nothing about this mechanism.

#### How the comparison was made (all run by me, scratch only)

A fresh clone at `29e1664` and `git archive` copies of `dd8e4ab` (2.14.1), `4ac7ee4` (merged helper) and `48b307f` (round 3 helper), all under the session scratch folder. Nothing in the working checkout was touched. `guard.py`, `carry_state.py`, `finalize_gate.py`, `batch_card.py` and `fixcommit.py` are byte-identical between `dd8e4ab` and `29e1664`.

- **2.14.1 side:** my own harness from round 3, not the project's test code and not the new fixture script. For each last-pass fix verdict: the character filter; the literal guard line `python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"` through `/bin/sh` in the session folder with the `dd8e4ab` `guard.py`; the three git commands in the session folder; a file kept only when all exit 0; then `carry_state.py finalize-counts` and `finalize_gate.py` from `dd8e4ab`.
- **Helper side:** `finalize_inputs.py` at `29e1664`, run as a command from the same session folder, same interpreter, same environment.
- A case is "same" only when the fingerprint set, the three counts and the gate action are all equal.

#### Gap closure evidence (step 1 of the request)

**Gap 3, the four rows from round 3 and their neighbours. Identical on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5:**

| Set-up (session at the repo top, `x.ts`, fix-obsolete verdict on the HEAD blob) | 2.14.1 | Helper now | Same? |
|------|--------|--------|-------|
| folder `repo⏎` beside repo `repo`, real file edited after the verdict | [1,0,0] `outstanding-to-phase-5` | [1,0,0] `outstanding-to-phase-5` | yes (was `write`) |
| folder `repo⏎` beside a plain folder `repo`, file unchanged | [0,0,0] `write` | [0,0,0] `write` | yes (was open) |
| the same two with `repo⏎⏎` beside `repo`, and `repo ⏎` beside `repo ` | as above | as above | yes |
| `core.worktree` → plain folder, unchanged | [0,0,0] `write` | [0,0,0] `write` | yes (was open) |
| `core.worktree` → separate repo, the session's repo has a staged edit | [1,0,0] `outstanding-to-phase-5` | [1,0,0] `outstanding-to-phase-5` | yes (was `write`) |
| `core.worktree` → plain folder, work tree copy edited / session copy edited; → separate repo unchanged; session in the other repo | each as 2.14.1 | the same | yes |

**Gap 2 (D-25):** 18 folder-name endings and the 24 neighbour cases: no disagreement. **Gap 1 (D-24):** the 24 file names: no disagreement. **Total: 72 cases per Python version, 0 disagreements, on four versions.**

#### Gap 5 in detail (new, blocking, a regression from the gap 3 fix)

**What differs.** git has two ways of reading a file name after `HEAD:`. A plain name (`dir/y.ts`) is read from the top of the repo wherever the session is. A name that starts with `./` or `../` is read relative to the session's folder. The helper's new rule adds `../` (once per folder level) to the name in the two "is it changed" checks, which assumes the first kind. For the second kind the fingerprint is taken from the session folder's file and the two checks look at a different file at the top.

**Reproduced** (repo with `x.ts`, `y.ts`, `dir/y.ts`, `dir/x.ts`, `dir/deep/k.ts`; fix-obsolete verdict on the blob `git rev-parse HEAD:<name>` prints in the session folder):

| Session | Finding file | Change after the verdict | 2.14.1 | Helper at `29e1664` | Helper on `main` (`4ac7ee4`) |
|---------|--------------|--------------------------|--------|---------------------|------------------------------|
| `dir` | `./y.ts` | none | [0,0,0] `write` | [0,0,0] `write` | [1,0,0] open |
| `dir` | `./y.ts` | `dir/y.ts` edited | [1,0,0] `outstanding-to-phase-5` | **[0,0,0] `write`** | [1,0,0] `outstanding-to-phase-5` |
| `dir` | `./y.ts` | `dir/y.ts` staged | [1,0,0] `outstanding-to-phase-5` | **[0,0,0] `write`** | [1,0,0] `outstanding-to-phase-5` |
| `dir` | `./y.ts` | top-level `y.ts` edited, `dir/y.ts` unchanged | [0,0,0] `write` | **[1,0,0] `outstanding-to-phase-5`** (safe) | — |
| `dir/deep` | `./k.ts` | `dir/deep/k.ts` edited or staged | [1,0,0] | **[0,0,0] `write`** | — |
| `dir` | `./deep/k.ts`, `./deep`, `./deep/` | `dir/deep/k.ts` edited or staged | [1,0,0] | **[0,0,0] `write`** | — |
| `repo` or `dir` (repo folder itself named `repo`) | `../repo/y.ts` | none | [0,0,0] `write` | **[1,0,0]** (safe) | — |

The first three rows were run on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5 on this Mac (git 2.55.0) and on Ubuntu 24.04 (Python 3.12.3, git 2.43.0); the helpers at `4ac7ee4` and `48b307f` were run on Python 3.14.5. The unsafe rows are new at `08f0018`: both earlier helpers keep the finding open there.

**Size in my matrix.** 7 session folders (top, `dir`, `dir/deep`, a folder with a space, a non-ASCII folder, a folder starting with `-`, a folder whose name ends in a line break) × 23 file names × unchanged / edited / staged / a same-named file elsewhere edited: 369 comparisons; 233 the same, 96 the accepted D-19 shape, 26 an edited file fingerprinted (all `./` names from a subfolder), 10 the safe direction of the same mechanism (a `./` name, the same-named file at the top edited), 4 note N-13. With `GIT_LITERAL_PATHSPECS`, `GIT_GLOB_PATHSPECS`, `GIT_NOGLOB_PATHSPECS`, `GIT_ICASE_PATHSPECS`, `GIT_PREFIX` (two values), and `GIT_DIR`+`GIT_WORK_TREE` (two forms): 312 comparisons; 184 the same, 96 D-19, 32 an edited file fingerprinted (again all `./` names). At the repo top every comparison is the same.

**Why it is graded blocking.** By the rule set for this round: an edited file fingerprinted from a subfolder is a D-19 regression. It is also a plain 2.14.1 difference in the unsafe direction that the owner has not been shown, and unlike gaps 2 and 3 the trigger is partly in the finding's file name, which comes from the reviewed change.

**What I could not establish.** Whether any reviewer in the plugin ever records a file name with a leading `./`. I found no code on this path that removes one; the character filter and the containment check both accept it.

**The fix is small.** Tried in a scratch copy only: give the two checks the name unchanged when it starts with `./` or `../`, the lifted name otherwise. Every `./` row then equals 2.14.1 (369 comparisons: 269 the same, 96 D-19, 4 note N-13, 0 edited files fingerprinted). The grid result is unchanged by that fix (252 agree, 14 D-19, 0 unexpected), which is the evidence that the grid cannot currently see this gap.

#### The D-19 mechanism under attack (step 2 of the request)

"D-19" below means the accepted shape: session below the top, the file edited or staged, 2.14.1 fingerprints it, the helper leaves it out.

| Set-up | Result against 2.14.1 | D-19 promise held? |
|--------|-----------------------|--------------------|
| Session in `dir`, `dir/deep`, a folder with a space, a non-ASCII folder, a folder starting with `-`, a folder whose name ends in a line break; plain names | same when unchanged; D-19 when edited or staged | yes |
| The same sessions; names starting with `./` | **edited file fingerprinted — gap 5** | **no** |
| Names with `..` inside (`dir/../x.ts`, `repo/../x.ts`), `dir/./y.ts`, `./../x.ts` | same (git refuses them on both sides) | yes |
| `../repo/y.ts` (leaves and re-enters the tree) from a subfolder | unchanged: 2.14.1 `write`, helper open (safe; gap 5 mechanism). Edited: both open | yes |
| Subfolder reached through a symlink inside the repo, with `PWD` set to the link path and unset | same / D-19 | yes |
| Session entered through a symlink from outside the repo into `repo/dir` | same / D-19 | yes |
| A symlink in the repo pointing out to a plain folder, and into another repo's subfolder; session through it | same (git works in the place the link really leads, on both sides) | n/a |
| Session in a submodule's subfolder | same / D-19 | yes |
| Session in a linked worktree's subfolder | same / D-19 | yes |
| Session folder typed in the wrong case (`DIR/DEEP`) on this case-insensitive disk | same / D-19 | yes |
| `core.worktree` → other folder, session in a subfolder of that folder (with `GIT_DIR`) | same / D-19 | yes |
| `core.worktree` → other folder, session in a subfolder beside `.git` | same | n/a |
| `GIT_DIR` + `GIT_WORK_TREE` on the repo, and with a `..` in the work tree path; session in `dir`, `dir/deep` | same / D-19 (plain names) | yes |
| `GIT_WORK_TREE` set to a subfolder of the repo, session one level below it | 2.14.1 `write`, helper open for `x.ts` and `dir/y.ts` | yes — in this set-up git itself sees the file as different from HEAD, so this is the D-19 shape |
| `GIT_PREFIX=dir/` and a nonsense `GIT_PREFIX` | same / D-19: git ignores the variable for this query | yes |
| `GIT_LITERAL_PATHSPECS`, `GIT_GLOB_PATHSPECS`, `GIT_NOGLOB_PATHSPECS`, `GIT_ICASE_PATHSPECS` | same / D-19 (plain names): `../` works under all four | yes |
| The folder-level query failing (a wrapper that fails only `--show-prefix`) | helper leaves every file out (safe). No natural set-up found where this query fails and the 2.14.1 root query succeeds | yes |
| `x.ts` marked assume-unchanged or skip-worktree, session at the top and in `dir` | same | — |
| Everything above with the session at the repo top | same in every case | n/a |

Not probed: a folder name that is not valid UTF-8 as the session subfolder; Windows; a repo owned by another user; a network disk.

#### The side-by-side test as a safeguard (step 3 of the request)

| Question | Finding |
|----------|---------|
| Is `finalize_step1_2141.sh` a faithful copy of the `dd8e4ab` text? | Yes. Compared by me against `git show dd8e4ab:plugins/vibe-check/phases/shared/90-finalize.md` lines 13 and 22: the pattern, the guard line, `git rev-parse "HEAD:<file>"`, `git diff --quiet HEAD -- <file>`, `git diff --cached --quiet -- <file>`, kept only when all exit 0, nothing changes folder. One transcription choice goes beyond the text: `<file>` is unquoted in the text and quoted in the script; these can differ only for a name ending in a line break (note N-8, unchanged). |
| Does the pin fail when the script is edited? | Yes. Ten edits, each fails `test_script_lines_are_the_dd8e4ab_commands`: `--cached` dropped; a `cd` to the top added; `HEAD:./$f`; the root piped through `tr`; the guard's failure ignored; a trailing command after a check; `:/` pathspec; `f` rewritten; the blob written with a line break; the filter admitting a space. A comment-only edit passes, as it should. |
| Root-as-cwd restored | Grid fails: 20 unexpected; the agreement test and 19 subtests (named rows and a D-19 row) fail. |
| `../` removed | The D-19 test fails on all 7 rows. Note: the `--grid` command itself exits 0 for this mutant; only the pytest class catches it. |
| A helper that fingerprints every validated file | Fails: 23 unexpected, 0 D-19; the agreement test and the D-19 test fail. |
| Is the D-19 exception as narrow as claimed? | Yes. It needs all of: session below the top, the named file edited / staged / staged-then-restored / deleted, 2.14.1 fingerprinting exactly that file with its HEAD blob, the helper leaving exactly that file out, and the two decisions following from that. Further mutants: a helper that leaves out every file below the top fails (4 unexpected); the lift on one of the two checks only, and a lift of one level only, each fail the D-19 test. |
| Its blind spot | The fixture repos have no file with the same name at the top and in a session subfolder, and the only `./` name is `./x.ts`. So no scenario has a `./` name that resolves from a subfolder, and none has the opposite D-19 direction (note N-13). Gap 5 passes the grid unseen. |
| Can the "not creatable here" list hide a real failure? | Only for the two axis values the test allows (a folder name with a byte that is not valid text; a file name ending in a line break), and only on a disk that refuses them; the test asserts both conditions and that at least 150 scenarios were created. On this Mac that is 18 scenarios, all the non-UTF-8 folder name. Weakness: nothing asserts the list is empty on Linux, so if CI's disk ever began refusing those names the 18 would stop running without any test failing. |
| Did the 18 Linux-only scenarios run and pass in CI? | **The CI logs cannot show it.** Both runs on `29e1664` (43784252263 push, 43784256308 pull request) print only `4572 passed, 2 skipped, 5 deselected`; the two skips are `test_lanearchive.py` and `test_replay.py`, the five left-out tests are in `test_replay.py` and `test_footprint.py`. `pytest -q` prints no per-test line, the grid's own report is captured for a passing test, and no junit file is uploaded. What the logs do show: the module was collected and none of its tests failed or skipped. **My own run** in an Ubuntu 24.04 container (Python 3.12.3, git 2.43.0, clone at `29e1664`): `284 scenarios in 4.9 s: 272 agree, 12 D-19, 0 known differences, 0 unexpected, 0 not creatable here`. So the 18 run and agree on Linux; CI's Python 3.14 was not reproduced. |

#### Regression checks (step 4; run by me in the scratch clone at `29e1664`)

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 2.14.1 record still reproducible | `finalize_capture.py verify --repo . --record …finalize-situations-v2.14.1.json` | `finalize baseline matches (5 situations)`, exit 0 | ✓ PASS |
| Five situations, by commit | `finalize_capture.py compare … --driver helper --commit HEAD` (Python 3.14.5 and 3.9.6) | `finalize outcome fields match (5 situations, 7 walks)`, exit 0, both | ✓ PASS |
| Five situations, by folder | the same with `--root plugins/vibe-check` | the same line, exit 0 | ✓ PASS |
| Helper and grid tests, default locale | bare `pytest test_finalize_inputs.py test_finalize_parity_grid.py` | 127 passed, 283 subtests | ✓ PASS |
| The same, `LC_ALL=C` | the same | 127 passed, 283 subtests | ✓ PASS |
| The same, Python 3.9.6 | `/usr/bin/python3 -m unittest test_finalize_inputs test_finalize_parity_grid`, default locale and `LC_ALL=C` | 127 tests OK, both; grid 254 agree, 12 D-19, 0 unexpected, 18 not creatable | ✓ PASS |
| Grid figures | `python3 test_finalize_parity_grid.py --grid` (3.14.5) | `284 scenarios: 252 agree, 14 D-19, 0 known differences, 0 unexpected, 18 not creatable here` | ✓ PASS (matches the record) |
| Stdlib-only gate | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | `34 shipped .py files; third-party imports: none` | ✓ PASS |
| Shipped-module count lock | `pytest .github/scripts/test_stdlib_only.py` | 21 passed (the lock is 34; the new `.sh` fixture and the new test file are not counted) | ✓ PASS |
| Finalize steps | `step_count.py --rev HEAD --json` | 85 | ✓ PASS |
| Finalize bytes | `footprint.py --rev HEAD --json` | 130,886 | ✓ PASS |
| Files changed under `plugins/`, `docs/`, `.github/` since `38ed24f` | `git diff --stat` | `finalize_inputs.py`, `test_finalize_inputs.py`, `fixtures/finalize_step1_2141.sh`, `test_finalize_parity_grid.py` | ✓ PASS |
| CI on the follow-up pull request head | `gh pr view 11`, `gh run view` | open, not merged; head `29e1664`; both `offline-suite` runs success, every step success | ✓ PASS |

#### Records, checked against what is true now (step 5)

| Record | Claim | Check | Holds? |
|--------|-------|-------|--------|
| 63-RESULT.md, sections above "Correction after the merge" | unaltered since the owner's "go" | `git diff main HEAD -- 63-RESULT.md`: one hunk, 77 added lines after line 325, no removed line | Yes |
| "Correction after the merge (D-24)" | as in round 2, plus a pointer to the second and third corrections | read; re-probed | Yes |
| "Second correction (D-25)" | the audit's 21 cases; "The audit did not try a second folder beside one whose name ends in a line break, or a repo whose git settings point its files elsewhere" | read; this is the correction round 3 asked for | Yes |
| "Third correction (gap 3, D-26)" | what differed, the four cases, how it was found, the owner's words | matches round 3's report and my re-run | Yes |
| "Third correction" | "Your D-19 rule is kept a different way … so they still read the file from the top" | Not for a name starting with `./` (gap 5) | **No** |
| "Third correction" | "its final version disagrees with 2.14.1 in 20 scenarios" on the old helper | my root-as-cwd mutant: 20 unexpected | Yes |
| "Accepted difference: a 60-second limit (gap 4, D-27)" | what differs, safe side only, the reproduction, the owner's words "Keep the limit, accept by name (Recommended)", "a sixth accepted difference" | read; `GIT_TIMEOUT = 60` at line 108 of the helper, used at line 136 | Yes |
| "The side-by-side test" | 284 scenarios; the pin; the axes; D-19 the only allowed difference; empty known-differences list; 18 not creatable; the limit not exercised | re-run; `KNOWN_DIFFERENCES = ()` in the file | Yes |
| "The side-by-side test" | "after the fix the grid found none" | True as written. It claims nothing about differences the grid cannot build; one exists (gap 5) | True; needs a line once gap 5 is settled |
| "The side-by-side test" | "the Linux CI machine can create it, and there it must agree like any other" | True of Linux (my container run). That CI ran them is not shown by any CI output | Partly: nothing in the test enforces that they run there |
| 63-REPRO.md audit row "Several trailing `\n`" | corrected: "wrong when a folder exists at the trimmed name" | read | Yes (corrected) |
| 63-REPRO.md audit row "Folder the three per-file git calls run in" | corrected: "this row stopped too early" | read | Yes (corrected) |
| 63-REPRO.md "No disagreement with a different mechanism was found" | now followed by "True of the cases this audit ran. A different mechanism existed" | read | Yes (corrected) |
| 63-REPRO.md gap 3 section, mutation matrix | root-as-cwd 20 unexpected; lift removed 0 unexpected and all 7 D-19 rows fail | my runs: the same | Yes |
| 63-REPRO.md gap 3 section | "`HEAD:./x` would be cwd-relative, and the grid's `./x.ts` row agrees with 2.14.1 because both read it in the session folder" | True at the repo top. From a subfolder the helper's two checks do not read it in the session folder | **Incomplete — gap 5 sits behind this sentence** |
| 63-REMOVAL-LEDGER.md third and fourth items | mechanism, four cases, fix and test commits; the limit accepted | read | Yes |
| `finalize_inputs.py` docstring | "git reads `HEAD:<file>` from the top of the work tree whatever the cwd" | false for `./` and `../` names | **No** |

#### Differences from 2.14.1 found in the code, against the accepted list

| Difference in the code | Accepted? |
|------------------------|-----------|
| Unreadable state file: shell's "Permission denied" line no longer shown | Yes — `## Your decision` item 1 |
| Unsafe folder, branch or phase names stop the review (D-21) | Yes — item 2 |
| Byte growth on every review path at phase end | Yes — item 3 |
| Corrupted (non-UTF-8) state file on a C locale shows a different refusal line | Yes — item 4 |
| Subfolder fix (D-19): with the session in a subfolder, a file with unsaved or staged edits is not fingerprinted | Yes — owner decision D-19 |
| Close out and fix loop keep the state path (D-20, D-23) | Yes |
| Inline Python isolated (D-22) | Yes |
| X1–X6; fewer commands on screen; a fingerprint file already holding `{}` is refused | Yes / on the page |
| Each git call is given 60 seconds; a slower one leaves the file out | Yes — owner decision D-27, on the page |
| ~~Leading-dash names~~, ~~folder name ending in whitespace~~, ~~per-file checks in the root path~~ | Removed by D-24, D-25, D-26: the helper matches 2.14.1 |
| **A file name starting with `./` (or `../`), session in a subfolder: the fingerprint is read from the session folder's file and the two change checks from a file at the top; the decision differs both ways, including a wrong approval** | **No — not on the page; the opposite of what D-19 promises** |

#### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/finalize_inputs.py` | the one helper call | ✓ exists, substantive, wired; one defect (gap 5) | per-file git in the session folder; `_up_to_top` counts folder levels from `git rev-parse --show-prefix` |
| `plugins/vibe-check/scripts/fixtures/finalize_step1_2141.sh` | the literal 2.14.1 step | ✓ VERIFIED | faithful; pinned |
| `plugins/vibe-check/scripts/test_finalize_parity_grid.py` | the side-by-side test | ✓ VERIFIED, with a blind spot | 9 tests; fails on every mutant I tried except the one behind gap 5 |
| `plugins/vibe-check/scripts/test_finalize_inputs.py` | parity, exit codes, mutants | ✓ VERIFIED | 118 tests in this file; no `./` name from a subfolder |
| Other artifacts (cross-call check, guard tests, `90-finalize.md`, the moved passage, `finalize_capture.py`, the records) | as before | ✓ VERIFIED (carried; unchanged) | |

#### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `finalize_inputs.py` | `git rev-parse --show-toplevel` | `_toplevel`, `.rstrip("\n")`, used only as the guard's root | ✓ WIRED |
| `finalize_inputs.py` | `guard.py` | `guard.main(["--root", root, "--path", f]) == 0` | ✓ WIRED (carried) |
| `finalize_inputs.py` | per-file git | `_git(..., cwd)` in the session folder | ✓ WIRED (gap 3 closed; root-as-cwd mutant fails 20 scenarios) |
| `finalize_inputs.py` | the D-19 lift | `up + f` in the two `git diff` calls | PARTIAL — right for plain names, wrong for `./` and `../` names (gap 5) |
| `test_finalize_parity_grid.py` | the 2.14.1 text | `TestStep1ScriptIsPinned` reads `dd8e4ab` with `git show` | ✓ WIRED (ten script edits fail it) |
| `finalize_inputs.py` | `carry_state.py`, `finalize_gate.py`, `batch_card.py` | three in-process calls | ✓ WIRED (five situations re-run) |
| CI workflow | the new test module | collected under `plugins/vibe-check/scripts`; not on the left-out list | ✓ WIRED (green on `29e1664`; per-scenario evidence not in the log) |

#### Data-Flow Trace, Spot-Checks, Probes

Not applicable (no artifact renders dynamic data; no `scripts/*/tests/probe-*.sh` probes are declared). The comparisons above are the spot-checks.

#### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| FINX-01 | Helpers on the single-writer path; same gate decisions and reports as the baseline | ✗ BLOCKED (gap 5) | Gaps 1 to 3 closed; gap 4 accepted |
| FINX-02 | Bad inputs fail visibly; a failed attempt writes and archives nothing | ✓ SATISFIED | Truth 2 (carried) |
| FINX-03 | Restart and retry across fresh shells | ✓ SATISFIED | Truth 2 (carried) |
| FINX-04 | Superseded prose and locks removed; invariants kept | ✓ SATISFIED | Truth 3 (carried) |
| FINX-05 | Before/after comparison; revert if no benefit | ✓ SATISFIED | Truth 4 (counts re-run) |
| XVAR-01 | One general check with a mutant | ✓ SATISFIED | Truth 5 (carried) |
| XVAR-02 | Flagged files recorded with reproduction before change | ✓ SATISFIED | Truth 5 (carried) |

No orphaned requirement.

#### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `finalize_inputs.py` `_head_blobs` | the blob and the change checks can address different files (`HEAD:<f>` as given, `up + f` in the checks) | Blocker (gap 5) | An edited file fingerprinted from a subfolder for `./` names |
| `test_finalize_parity_grid.py` | no assertion that the not-creatable list is empty on Linux | Warning | The 18 Linux-only scenarios could stop running unnoticed |
| `test_finalize_parity_grid.py` `main --grid` | exits 0 when the D-19 rows vanish (lift removed) | Info | Only the pytest class catches that mutant; the records already say so |
| files changed by the gap closure | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` | none found | — |

#### Notes (not gaps)

- **N-1 to N-12** are carried unchanged from the earlier reports (N-7 is now the accepted D-27).
- **N-13. D-19 has a second direction that the page does not describe, and I did not report it in rounds 1 to 3.** Session in `dir`, finding file `x.ts` (the top-level file, unchanged), and a different file with the same name in the session folder (`dir/x.ts`) edited. 2.14.1 reads the name relative to the session folder, sees the edit to the wrong file and keeps the finding open; the helper reads the file the finding names, finds it unchanged and approves (`write`). Reproduced (4 of 369 comparisons; the same on the merged helper at `4ac7ee4`). This is the helper being right and 2.14.1 being strict by accident, it follows from the mechanism D-19 accepted ("reads the file from the repo root"), and it fits the promise as stated for this round ("a clean file still is" fingerprinted), so I have not graded it a gap. But it is a case where the helper approves and 2.14.1 does not, and the D-19 text shown to the owner describes only the other direction. One sentence on the result page would close it. The grid does not hold this direction either (same fixture blind spot).
- **N-14. `GIT_WORK_TREE` set to a subfolder of the repo.** With the session one level below that folder the helper leaves out files 2.14.1 fingerprints. In that set-up git itself reports the file as different from HEAD, so it is the D-19 shape, not a new mechanism.
- **N-15. The folder-level query.** If `git rev-parse --show-prefix` fails the helper leaves every remaining file out. I found no natural set-up where it fails while 2.14.1's own root query succeeds; forced with a wrapper, the result is the safe direction.
- **N-16. Gap 4 is recorded as an accepted difference, not as an override in this file's frontmatter.** An override here would be matched against the whole first criterion and would also mask gap 5.

#### Human Verification Required

None that blocks. Carried from the first report: no live review was run, so whether a live model fills the three switch slots, pastes the printed state path and branches on `next` as the scripted walks do has not been observed. Under the standing rule a live or paid run needs its own approved proposal; this report does not ask for one.

#### Gaps Summary

What this round was asked to check holds: gap 3 is closed on all four reproduced rows, gap 4 is accepted and recorded in the owner's words with the limit still in the code, gaps 1 and 2 stay closed, the two overclaiming audit rows are corrected, the owner-approved sections of the result page are untouched, and the side-by-side test is faithful to 2.14.1 and fails when it should.

The attack on the replacement D-19 mechanism found one defect, introduced by the gap 3 fix and present only on pull request #11. Adding `../` to the file name is right for a name git reads from the top and wrong for a name git reads relative to the session folder (`./name`, `../name`). From a subfolder, with such a name, the helper fingerprints the session folder's file while checking a different file for changes: an edited file is fingerprinted and the review is approved where 2.14.1, and the helper on `main`, keep the finding open. The fix is one condition in the same function. The side-by-side test needs one more fixture file and three named rows to hold it, because today it cannot tell a helper with this defect from one without.

#### Residual risk (my judgement, separate from the status)

Four rounds, four exotic-input differences, all in the same thirty lines, and this time the new one was created by the fix for the last one and passed a 284-scenario test written to prevent exactly that. The lesson is that the grid is only as wide as its fixture repos: it varies folder names and git settings thoroughly, but file names and file layout thinly (one `./` name, no same-named files at two levels), and that is where this round's defect and note N-13 both sit. Once gap 5 is fixed and the grid has those rows, my estimate that a further decision difference of this kind remains is about one in six on macOS and Linux, lower than last round because the per-file step is now literally 2.14.1's at the repo top and I have attacked the subfolder path from every side I could name; the chance that any remaining one would touch a real review stays very low.

---

## History: third verification (2026-11-16T00:14:00Z, `48b307f`)

**Status then:** gaps_found. **Score then:** 4/5. Gaps 1 (D-24) and 2 (D-25) closed. Two gaps open then: gap 3 (blocking: the folder the per-file git checks run in; closed in round 4) and gap 4 (minor: the 60-second limit per git call; accepted by the owner as D-27). The report of that round follows unchanged, with its headings moved one level down.

### Result in plain terms

- **The gap from the second report is closed.** A repo kept in a folder whose name ends in a space, a tab or another blank character now gets the same Finalize decision as at 2.14.1, including the contrived `repo ` beside `repo` case that used to approve wrongly. I re-ran my own comparison against the literal 2.14.1 steps on four Python versions. Nothing in that class disagrees in either direction.
- **The gap from the first report is still closed.** 24 file names starting with `-` (and controls) re-run on four Python versions: no disagreement.
- **The new tests are real.** Putting the old trim back fails 8 checks. Making the test's 2.14.1 side share the same wrong trim still fails 8, because the tests also check fixed expected results.
- **Nothing I verified before has regressed.** Five situations still match 2.14.1; Finalize is still 85 steps and 130,886 bytes; the stdlib-only gate passes; the helper tests pass under the default locale and `LC_ALL=C`, on Python 3.14 and 3.9.
- **One new blocking gap, found by the independent challenge. It is not caused by either fix; it has been in the helper since pull request #10 merged, and I missed it twice.** 2.14.1 ran its three "is this file unchanged" git commands in the folder the session is in. The helper runs them in the folder it believes is the repo root. Normally these are the same repository. In two very unusual set-ups they are not, and then the helper reads the wrong repository or none:
  - a repo folder whose name ends in a line break, with another folder beside it under the same name minus the line break;
  - a repo whose git setting `core.worktree` points at a different folder.
  In each set-up there is a safe direction (the helper leaves a finding open that 2.14.1 would close) and an unsafe one (the helper approves a review that 2.14.1 would keep open, because it found the file unchanged in the other repository). The author of a reviewed change cannot arrange either; both depend on folder names or git settings on the reviewer's machine. This is rarer than the trailing-space case. I have graded it blocking by the same standard as the two earlier rounds: a reproduced different decision that the owner has not been shown. It sits next to the accepted D-19 change (same line of code), but D-19 was accepted on the statement that an edited file is never fingerprinted, and here one is.
- **One minor gap, previously a note.** The helper gives each git command 60 seconds; 2.14.1 had no limit of its own. I have now reproduced a different decision with git made deliberately slow. It can only err on the safe side. It needs an owner acceptance by name, nothing more.
- **Score: 4 of 5**, the same number, for a third and smaller reason.
- **The records are accurate about what was fixed, and claim slightly more than was shown in one place:** the audit says a folder name ending in a line break cannot change a decision. It can, when a folder exists under the trimmed name.
- **Expected and not counted as gaps:** no 63-11-SUMMARY.md, no `## Merge` section, the `Follow-up pull request:` placeholder line, backlog entries not filed, ROADMAP/STATE/REQUIREMENTS not ticked, pull request #11 not merged.

### Re-verification summary

| Item | Round 1 (23:15Z, `4ac7ee4`) | Round 2 (23:50Z, `66b0429`) | Now (`48b307f`) |
|------|------------------------------|------------------------------|-----------------|
| Status | gaps_found | gaps_found | gaps_found |
| Score | 4/5 | 4/5 | 4/5 |
| Gap 1: leading-dash file names (D-24) | open, blocking | closed | closed (re-probed) |
| Gap 2: repo folder name ending in whitespace (D-25) | not found (was present) | open, blocking | **closed** |
| Gap 3: per-file git runs in the root path, not the session folder, when these are different repositories | not found (was present) | not found (was present) | **open, blocking** |
| Gap 4: 60-second limit per git call | not noted | note N-7 (not reproduced) | **open, minor** (reproduced) |
| Regressions | — | none | none |

#### What I ran now and what I carried

| Criterion | Now | How |
|-----------|-----|-----|
| 1 (same decisions as 2.14.1) | **Re-ran** | Everything in "Second gap closure evidence", "Independent challenge" and "Regression checks" below |
| 2 (bad inputs stop; nothing written; restart works) | **Carried**, with a partial re-run | This diff changes one line in `_toplevel`. Re-ran: the five-situation comparison (includes `one-rebuild`, `refused-close`, `fresh-shell-restart`), all of `test_finalize_inputs.py`, and 34 malformed-state shapes through both sides (both stop on the same ones). Not re-run: the real fence under bash and zsh against the six fault cases |
| 3 (superseded prose removed, invariants kept) | **Carried** | `git diff 66b0429 48b307f -- plugins docs .github` touches `finalize_inputs.py` and `test_finalize_inputs.py` only |
| 4 (before/after counts, revert rule) | **Re-ran the counts**, carried the rest | 85 steps and 130,886 bytes at `48b307f` |
| 5 (the general cross-call check) | **Carried** | No phase file and no check file changed |

### Goal Achievement

#### Observable Truths (roadmap success criteria — the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline | ✗ FAILED (partial) | Gaps 1 and 2 are closed. One mechanism still differs (the folder the per-file git commands run in, when it is not the session's repository), plus the 60-second limit. See the gaps. |
| 2 | Missing, malformed or stale Finalize inputs stop with a plain message; a failed or refused attempt writes no report and archives nothing; restart and retry work across fresh shell calls | ✓ VERIFIED (carried; partial re-run) | Earlier evidence stands. The five-situation comparison and the 114 helper tests pass at `48b307f`. |
| 3 | Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host | ✓ VERIFIED (carried) | No file under this truth changed. |
| 4 | Loaded prose and helper/tool steps on the same Finalize paths are compared before and after against the Phase 62 criterion; the slice is reverted if it adds complexity without a demonstrated benefit | ✓ VERIFIED (counts re-run) | `step_count.py --rev HEAD --json`: 85 steps (35 fences, 5 inline commands, 5 Write-tool writes, 40 paste sites). `footprint.py --rev HEAD --json`: Finalize 130,886 bytes. Both identical to `4ac7ee4` and `66b0429`. |
| 5 | One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips; any phase file it flags is recorded with its reproduction before it is changed | ✓ VERIFIED (carried) | No file under this truth changed. |

**Score:** 4/5 truths verified

#### Deferred Items

None. Phase 65 (release gate) checks equivalence in general terms but names nothing about this mechanism, so the gaps are not deferred to it.

#### How the comparison was made (all run by me, scratch only)

A fresh clone at `48b307f` and a `git archive` of `dd8e4ab` (2.14.1), both under the session scratch folder; nothing in the working checkout was touched. `guard.py`, `carry_state.py`, `finalize_gate.py`, `batch_card.py` and `fixcommit.py` are byte-identical between the two.

- **2.14.1 side:** my own script, not the project's test code. For each last-pass fix verdict: the character filter; then the literal guard line `python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"` run through `/bin/sh` in the session folder with the `dd8e4ab` `guard.py`; then the three git commands in the session folder; a file kept only when all exit 0; then `carry_state.py finalize-counts` and `finalize_gate.py` from `dd8e4ab`.
- **Helper side:** `finalize_inputs.py` at `48b307f`, run as a command from the same session folder, same interpreter, same environment.
- A case is "same" only when the fingerprint set, the three counts and the gate action are all equal.

#### Second gap closure evidence

**Folder names, clean `x.ts`, last-pass fix-obsolete verdict on its HEAD blob. Identical on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5:**

| Repo folder (session in it) | 2.14.1 | Helper | Same? |
|-----------------------------|--------|--------|-------|
| `repo` (control), `my repo`, ` repo` (leading space) | [0,0,0] `write` | [0,0,0] `write` | yes |
| ends with a space, two spaces, a tab, a no-break space, a carriage return, a vertical tab, a form feed, an em space | [0,0,0] `write` | [0,0,0] `write` | yes (was different for all of these) |
| folder named only ` ` (one space) | [0,0,0] `write` | [0,0,0] `write` | yes |
| line break inside the name; line break then a space | [0,0,0] `write` | [0,0,0] `write` | yes |
| ends with a line break, two line breaks, space + line break, CR + line break; nothing at the trimmed name | [1,0,0] `outstanding-to-phase-5` | the same | yes |

**The unsafe direction of gap 2, and its neighbours (four Python versions):**

| Set-up | 2.14.1 | Helper | Same? |
|--------|--------|--------|-------|
| `repo ` beside repo `repo`, real `x.ts` edited after the verdict | [1,0,0] `outstanding-to-phase-5` | [1,0,0] `outstanding-to-phase-5` | yes (was `write`) |
| the same with a tab, a no-break space, a carriage return | [1,0,0] `outstanding-to-phase-5` | the same | yes |
| each of those four, real file unchanged | [0,0,0] `write` | the same | yes |
| each of those four, neighbour a plain folder holding the file | [0,0,0] `write` | the same | yes |

**First gap (D-24), re-probed on four Python versions:** `x.ts`, `-x.ts`, `sub/-x.ts`, `-d/x.ts`, `--`, `-`, `-1`, `-1.ts`, `-1e5`, `-1_0`, `-h`, `--help`, `--root`, `--path`, `--pa`, `--ro`, `-x`, `-hx`, `--pathx`, `---`, `-.5`, `-0x10`, `-r`, `-p`, each end to end. 0 disagreements. As before, `-1.ts`, `-1e5` and `-0x10` are accepted by both sides on 3.14 and refused by both on 3.9, 3.12 and 3.13.

**Total for these two classes:** 66 cases per Python version, 60 the same; the 6 that differ are all the new gap below (folder name ending in a line break with a folder at the trimmed name), not gap 1 or gap 2.

#### The new tests can fail (scratch copies of `plugins/vibe-check` at `48b307f`, bare `pytest test_finalize_inputs.py`)

| Change | Result |
|--------|--------|
| None | 114 passed, 201 subtests passed |
| A. Helper `.strip()` restored | 8 failed: `TestGuardCommandParity::test_parity_names_in_a_repo_folder_ending_in_a_space`, `TestRepoFolderNameParity::test_folder_ending_in_a_space_beside_its_trimmed_name_is_not_approved`, and 6 subtests (space, tab, no-break space, carriage return, vertical tab, form feed) |
| B. Helper `.strip()` restored AND the test's 2.14.1 side made to trim in Python the same way (both sides share the bug) | the same 8 failed. The tests do not depend on the two sides disagreeing: they also assert fixed results (`{"x.ts": <blob>}`, [0,0,0], `write`; and "not `write`" for the neighbour case) |
| B2. Only the test's 2.14.1 side trims in Python, helper fixed | 7 failed: the test notices its own 2.14.1 side is wrong |
| C. Helper `.rstrip()` (all trailing whitespace) | 8 failed |
| D. Helper drops exactly one final line break | 3 subtests failed (line break, two line breaks, space + line break) |
| E. Helper `.rstrip("\r\n")` | 1 subtest failed (carriage return) |

The executor's recorded figures (8, 8, 3, 8, 7) match mine.

**What the tests do not cover:** a folder at the trimmed name when the real name ends in a line break, and `core.worktree`. That is why they pass while the new gap exists.

#### Independent challenge (step 2 of the request)

I did not start from the executor's audit table. I listed every place where the helper's fingerprint step could take a different input from the literal 2.14.1 procedure (the root text, the folder git runs in, the file name, the blob text, which verdicts and rows are selected, the environment, the time limit) and probed each. 102 cases on Python 3.14.5, repeated on 3.9.6 with the same outcome.

| Area | What I ran | Result |
|------|-----------|--------|
| **Root / working folder** | folder name ending in a line break with a repo, or a plain folder, at the trimmed name | **Differs both ways — gap 3** |
| | `core.worktree` pointing at another folder; at another repo with a staged edit in the session's repo | **Differs both ways — gap 3** |
| | linked worktree (`git worktree add`): clean, edited there, and the main checkout while the linked one is edited | same |
| | session in a bare repo, inside `.git`, in a non-repo folder, in a repo with no commits, on a detached HEAD | same |
| | session inside a submodule | same |
| **GIT_* environment and settings** | `GIT_DIR` absolute and relative; `GIT_DIR` with the session in an unrelated folder; `GIT_DIR` + `GIT_WORK_TREE`; `GIT_WORK_TREE` elsewhere; `GIT_CEILING_DIRECTORIES` (parent, and the repo itself); `GIT_INDEX_FILE` at an empty index; `GIT_OBJECT_DIRECTORY` bogus; `GIT_PREFIX`; `GIT_LITERAL_PATHSPECS`; `GIT_ICASE_PATHSPECS`; `GIT_EXTERNAL_DIFF`; `GIT_TRACE`; `core.quotepath=true`; `LC_ALL=C`; no git on `PATH` | same (19 cases) |
| | `safe.directory` refusal, forced with `GIT_TEST_ASSUME_DIFFERENT_OWNER=1` | same (both leave the file out). A repo really owned by another user was not set up |
| | SHA-256 repo; `core.autocrlf=true` with the working copy rewritten in CRLF; `core.filemode` on and off with a mode-only change | same |
| **File name** | `./x.ts`, `sub/../x.ts`, a folder (`dir`), trailing slash (`dir/`, `x.ts/`), `.`, `./`, `dir//y.ts`, `dir/./y.ts`, `.git`, `.git/config`, `.git/HEAD`, a symlink to a file, a symlink to a folder and a file through it, `a..b`, `x..HEAD` (git reads these as a range), a missing file, `..`, `../repo/x.ts`, the absolute path, `/etc/hosts`, `HEAD`, `x.ts.`, wrong-case `X.TS` and `DIR/y.ts` (case-insensitive disk); 10 of them again with the content edited | same (37 cases) |
| | a submodule path as the finding's file (clean, and dirty inside); a file inside a submodule named from the outer repo | same |
| | staged change with the working copy put back; file deleted in the working copy | same |
| | how 2.14.1 quoted and split the per-file loop | Not a difference: the character filter admits no space, quote, `*`, `?`, `[` or `$`, so an unquoted `-- <file>` cannot split or expand; the helper passes one argument |
| **Blob id** | recorded blob null, missing, a number, a list, upper-case, with a trailing line break, with a trailing space, shortened to 7 characters, empty; four of these again with the file edited | same (13 cases) |
| **State contents** | recorded pass as `2.0`, `true`, `"2"`, an earlier pass; last pass number as `2.0`; file null, missing, a number, empty, with a trailing space, with a trailing line break; a duplicate row for the same finding naming another file (before and after the real row); verdict as a list; `fix_verdicts` a list, null, missing; verdict `applied`, `OBSOLETE`; a verdict for an unknown finding; a non-text finding id; a non-object row; no passes; no pass number | Same decision in every case. For the 12 shapes 2.14.1 refuses, both stop and write nothing (2.14.1's counting command exits 2, the helper exits 3, which the instructions map to the same sentence) |
| | finding `file` given as a list | Both stop and write nothing. The sentence differs: 2.14.1's counting command crashes, so the owner reads "carry_state.py failed"; the helper exits 4, so the owner reads "finalize_gate.py failed". Not a decision difference; the plugin never writes such a state. Note N-9 |
| **Time limit** | real git made slow with a `core.fsmonitor` hook: 2 seconds (control) and 65 seconds | 2 s: same. 65 s: 2.14.1 commands [0,0,0] `write` (65 s per diff command); helper [1,0,0] `outstanding-to-phase-5` after 60 s. **Gap 4 (minor)** |

**Not probed (stated so nothing is implied):** a folder name that is not valid UTF-8 (this Mac's disk refuses it; a Linux host could differ); Windows; a repo truly owned by another user; a repo on a network disk.

#### Gap 3 in detail

**What differs.** At 2.14.1 the root from git was only *text* handed to the containment check. The three git commands then ran wherever the session was. In the helper the same text is also the *folder the three git commands run in*. D-19 accepted this for one purpose: when the session sits in a subfolder of the repo, the file name is read from the top of the same repo, so an edited file is never missed. It was not looked at for the case where the root text names a different place from the session's repository.

**Reproduced, session at the repo root, file `x.ts`, fix-obsolete verdict on the HEAD blob:**

| Set-up | 2.14.1 | Helper | Direction |
|--------|--------|--------|-----------|
| folder `repo⏎` (name ends in a line break) beside repo `repo` holding the same file; real `x.ts` edited after the verdict | [1,0,0] `outstanding-to-phase-5` | **[0,0,0] `write`** | unsafe: an approval 2.14.1 would not give |
| folder `repo⏎` beside a plain or empty folder `repo`; real file unchanged | [0,0,0] `write` | **[1,0,0] `outstanding-to-phase-5`** | safe |
| the same two with `repo⏎⏎` beside `repo`, and `repo ⏎` beside `repo ` | as above | as above | both |
| `core.worktree` set to another folder holding the same file; session in the folder with `.git`; file unchanged | [0,0,0] `write` | **[1,0,0] `outstanding-to-phase-5`** | safe |
| `core.worktree` set to a folder that is itself a separate repo; the session's repo has a staged edit to `x.ts` | [1,0,0] `outstanding-to-phase-5` | **[0,0,0] `write`** | unsafe |
| `core.worktree` elsewhere, the work tree's copy edited | [1,0,0] `outstanding-to-phase-5` | the same | — |

The line-break rows were run on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5; the `core.worktree` rows on 3.9.6 and 3.14.5. The first, second, third and fourth distinct set-ups were also run against the merged helper at `4ac7ee4`, with the same result: this predates both gap closures.

**How much it matters.** Less than gap 2 did. A folder name ending in a line break is close to impossible to create by accident, and `core.worktree` pointing at a folder that is not the session's own checkout is a deliberate, unusual git set-up (ordinary submodules and `git worktree` checkouts are unaffected; I tested both). The unsafe direction needs, in addition, a second repository at the other location with the same file at the verdict's version. The author of a reviewed change controls none of this.

**Why it is graded blocking.** The same test as rounds 1 and 2: a reproduced, deterministic gate decision that differs from 2.14.1, in both directions, not on the list the owner accepted. I considered whether D-19 already covers it, since it is the same line of code. It does not: D-19's recorded effect is "an edited file is never fingerprinted", and the two unsafe rows are an edited (or staged) file being fingerprinted from somewhere else. The owner may still decide that D-19 should be extended to cover this by name; that is a product decision, not mine.

**Two ways to close it.**
1. **Match 2.14.1.** Make the three checks read the session's own repository while still reading the file name from the top of the repo (the D-19 behaviour). Tests: the six rows above against the 2.14.1 commands, with a mutant for each direction. User impact: none compared with 2.14.1. Size: small, in the same function; it can ride in pull request #11.
2. **Accept the difference by name.** Record it as an override here and add it to the result page's differences, beside D-19.

To accept, add to this file's frontmatter:

```yaml
overrides:
  - must_have: "equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline"
    reason: "The helper runs its per-file git checks in the root path (D-19). When that path is not the session's repository (folder name ending in a line break beside a folder of the trimmed name; core.worktree pointing elsewhere) the decision can differ from 2.14.1 in either direction. Accepted as an extension of D-19."
    accepted_by: "{owner}"
    accepted_at: "{ISO timestamp}"
```

#### Gap 4 in detail (minor)

The helper gives each git command 60 seconds, then leaves the file out. Reproduced with a hook that makes git wait 65 seconds: every 2.14.1 command exits 0 and the decision is `write`; the helper returns `outstanding-to-phase-5` after 60 seconds. There is no unsafe direction: a timed-out file is only ever left out. At 2.14.1 the only limit was the session's own limit on a shell call (two minutes unless changed), so the two can differ only for a git command that takes between one and two minutes on a single file. I recommend accepting it by name and keeping the limit; removing it would let a stuck git hang Finalize.

#### Regression checks (run by me in the scratch clone at `48b307f`)

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| 2.14.1 record still reproducible | `finalize_capture.py verify --repo . --record …finalize-situations-v2.14.1.json` | `finalize baseline matches (5 situations)`, exit 0 | ✓ PASS |
| Five situations, by commit | `finalize_capture.py compare … --driver helper --commit HEAD` (Python 3.14.5 and 3.9.6) | `finalize outcome fields match (5 situations, 7 walks)`, exit 0, both | ✓ PASS |
| Five situations, by folder | the same with `--root plugins/vibe-check` | the same line, exit 0 | ✓ PASS |
| Helper tests, default locale | bare `pytest test_finalize_inputs.py` | 114 passed, 201 subtests | ✓ PASS |
| Helper tests, `LC_ALL=C` | the same | 114 passed, 201 subtests | ✓ PASS |
| Helper tests, Python 3.9.6 | `/usr/bin/python3 -m unittest test_finalize_inputs`, default locale and `LC_ALL=C` | 114 tests OK, both | ✓ PASS |
| Stdlib-only gate | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | `34 shipped .py files; third-party imports: none` | ✓ PASS |
| Finalize steps | `step_count.py --rev HEAD --json` | 85 (35 fences, 5 inline commands, 5 Write-tool writes, 40 paste sites) | ✓ PASS |
| Finalize bytes | `footprint.py --rev HEAD --json` | 130,886 | ✓ PASS |
| Files changed under `plugins/`, `docs/`, `.github/` since `66b0429` | `git diff --stat` | `finalize_inputs.py` (+5/−2) and `test_finalize_inputs.py` only | ✓ PASS |
| CI on the follow-up pull request head | `gh pr view 11` | open, not merged; head `48b307f`; both `offline-suite` runs success | ✓ PASS |

The full local suite was not run by me (one was in progress in the working checkout, per instruction). The round-1 full-suite figure is carried, not re-measured.

#### Corrected records, checked against what is true now

| Record | Claim | Check | Holds? |
|--------|-------|-------|--------|
| 63-RESULT.md "Second correction" | What differed; the two reproduced cases; found by re-verification; present since PR #10; the first correction's test trimmed the same way | Reproduced in round 2; test diff read | Yes |
| 63-RESULT.md | Fix `92ae038` removes only trailing line breaks; five situations still match; 85 steps and 130,886 bytes stand | Diff read; re-run | Yes |
| 63-RESULT.md | Tests written first at `5fe021c`, failed on the old helper | Commit order confirmed; break A | Yes |
| 63-RESULT.md | "With the old trim put back on the test's 2.14.1 side as well, the space, tab and neighbouring-repo tests still fail" | Break B | Yes |
| 63-RESULT.md | "No other file name differed" (the amended sentence in the first correction) | 24 names re-run now; 131 in round 2 | Yes |
| 63-RESULT.md "Audit" | "only the repo-folder trim differed, and all 21 now match" | The 21 listed rows do match (my folder table agrees). **But a difference outside those rows exists: gap 3** | True of the 21 rows; "only … differed" claims more than was shown |
| 63-REPRO.md audit table, row "Several trailing `\n`" | a difference there cannot change a decision ("both give another folder; probed") | **Wrong when a folder exists at the trimmed name** (gap 3, first four rows) | **No** |
| 63-REPRO.md audit table, row "Folder the three per-file git calls run in" | "accepted D-19 difference … Not this mechanism; unchanged" | The row names the right mechanism and stops there; this is the mechanism of gap 3 | Incomplete |
| 63-REPRO.md | "No disagreement with a different mechanism was found" | True as a statement of what the audit found; one exists | Needs a line once gap 3 is fixed or accepted |
| 63-REPRO.md mutation table | 8 / 8 / 3 / 8 / 7 failures | Breaks A, C, D, B, B2: the same figures | Yes |
| 63-REPRO.md | 114 tests after the fix | Re-run | Yes |
| 63-REPRO.md | Docstring corrected to "3.14 accepts `-1.ts`; 3.9, 3.12 and 3.13 refuse it" | Read; matches my runs | Yes (the round-2 info item is fixed) |
| 63-REMOVAL-LEDGER.md second correction | Mechanism, both cases, fix and test commits, three `TestRepoFolderNameParity` tests | Confirmed | Yes |
| 63-REMOVAL-LEDGER.md | "The audit of every other … site in the helper found no further difference" | As above | True as written; needs a line once gap 3 is settled |
| 63-CONTEXT.md D-25 | The D-24 ruling applied by the main session; owner informed and may overrule | The record says so; whether the owner was told cannot be checked from the files | Recorded |

#### Plan-level truths (carried, updated where this round changes them)

| Plan | Truths | Status | Note |
|------|--------|--------|------|
| 63-01 | 6 | 5 ✓, 1 ✗ | ✗ "Where the helper could be stricter than 2.14.1 it is not: each such case has a named parity test". The leading-dash and folder-whitespace cases are fixed and tested. Gap 3 (safe-direction rows) and gap 4 are further instances with no test. |
| 63-02 | 8 | 7 ✓, 1 ✗ | ✗ the repeated D-06 parity truth, same root cause as gap 3. |
| 63-03 | 5 | 5 ✓ | carried |
| 63-04 | 4 | 4 ✓ | carried |
| 63-05 | 5 | 5 ✓ | carried |
| 63-06 | 9 | 9 ✓ | carried |
| 63-07 | 5 | 5 ✓ | carried |
| 63-08 | 7 | 7 ✓ | carried, with note N-1 |
| 63-09 | 6 | 6 ✓ | carried |
| 63-10 | 5 | 5 ✓ | carried |
| 63-11 | 5 | 3 ✓, 2 pending | Backlog filing and STATE/ROADMAP edits are held for this report — expected, not gaps. |

#### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/finalize_inputs.py` | the one helper call | ✓ VERIFIED (one defect, see gap 3) | `_toplevel` now returns `result[1].rstrip("\n")`; stdlib imports unchanged |
| `plugins/vibe-check/scripts/test_finalize_inputs.py` | parity, exit codes, mutants | ✓ VERIFIED | 114 tests; `TestRepoFolderNameParity` (3 tests) is end to end against the 2.14.1 commands; `TestGuardCommandParity`'s 2.14.1 side runs the guard line through `/bin/sh` |
| `plugins/vibe-check/scripts/test_cross_call_vars.py` | the general check | ✓ VERIFIED (carried) | |
| `plugins/vibe-check/scripts/test_pasted_name_guard.py` | D-21 guard tests | ✓ VERIFIED (carried) | |
| `plugins/vibe-check/scripts/test_inline_python_isolated.py` | D-22 isolation tests | ✓ VERIFIED (carried) | |
| `plugins/vibe-check/phases/shared/90-finalize.md` | one Finalize-inputs fence | ✓ VERIFIED (carried; unchanged) | |
| `docs/design/lean-v2.15/finalize-counts-explained.md` | moved passage | ✓ VERIFIED (carried; unchanged) | |
| `docs/design/lean-v2.15/tools/finalize_capture.py` | second driver and compare | ✓ VERIFIED (re-run) | |
| `63-COUNTS.md`, `63-REPRO.md`, `63-EQUIVALENCE.md`, `63-REMOVAL-LEDGER.md`, `63-RESULT.md` | records | ✓ exist and substantive | Two audit rows in 63-REPRO.md need correcting (table above) |

#### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `finalize_inputs.py` | `git rev-parse --show-toplevel` | `_toplevel`, `.rstrip("\n")` | ✓ WIRED (breaks A, C, D, E fail tests) |
| `finalize_inputs.py` | `guard.py` | `guard.main(["--root", root, "--path", f]) == 0` | ✓ WIRED (carried from round 2) |
| `finalize_inputs.py` | per-file git | `_git(..., root)` | ⚠ PARTIAL — wired, but to the root path rather than the session's repository (gap 3) |
| `finalize_inputs.py` | `fixcommit.py` | `PATH_RE` only | ✓ WIRED (carried) |
| `finalize_inputs.py` | `carry_state.py`, `finalize_gate.py`, `batch_card.py` | three in-process calls | ✓ WIRED (five situations re-run) |
| `90-finalize.md` | `finalize_inputs.py` | one fence | ✓ WIRED (carried) |
| `test_finalize_inputs.py::fingerprint_2141` | the 2.14.1 guard line | `/bin/sh -c '"$0" "$1" --root "$(git rev-parse --show-toplevel)" --path "$2"'` | ✓ WIRED (breaks B, B2 fail it) |
| `finalize_capture.py compare` | 2.14.1 situations record | `OUTCOME_KEYS` | ✓ WIRED (re-run) |
| CI workflow | phase test modules | unchanged | ✓ WIRED (green on `48b307f`) |

#### Data-Flow Trace (Level 4)

Not applicable: no artifact in this phase renders dynamic data. The helper's data flow (state file → fingerprints → counts → gate → result) is exercised end to end by the comparisons above.

#### Behavioral Spot-Checks and Probe Execution

The comparisons and regression checks above are the spot-checks. No `scripts/*/tests/probe-*.sh` probes are declared by this phase.

#### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| FINX-01 | 01, 02, 06, 07, 08 | Helpers on the single-writer path; same gate decisions and reports as the baseline | ✗ BLOCKED (gap 3; gap 4 minor) | The D-24 and D-25 input classes are now satisfied. |
| FINX-02 | 02, 06, 08 | Bad inputs fail visibly; a failed attempt writes and archives nothing | ✓ SATISFIED | Truth 2 (carried; 34 malformed shapes re-run) |
| FINX-03 | 06, 08 | Restart and retry across fresh shells | ✓ SATISFIED | Truth 2 (carried) |
| FINX-04 | 05, 06, 07 | Superseded prose and locks removed; invariants kept | ✓ SATISFIED | Truth 3 (carried) |
| FINX-05 | 01, 09, 10, 11 | Before/after comparison; revert if no benefit | ✓ SATISFIED | Truth 4 (counts re-run) |
| XVAR-01 | 03, 11 | One general check with a mutant | ✓ SATISFIED | Truth 5 (carried) |
| XVAR-02 | 04, 09, 10 | Flagged files recorded with reproduction before change | ✓ SATISFIED | Truth 5 (carried) |

All seven ids appear in plan frontmatter and in REQUIREMENTS.md under Phase 63. No orphaned requirement.

#### Differences from 2.14.1 found in the code, against the accepted list

| Difference in the code | Accepted? |
|------------------------|-----------|
| Unreadable state file: shell's "Permission denied" line no longer shown | Yes — `## Your decision` item 1 |
| Unsafe folder, branch or phase names stop the review (D-21) | Yes — item 2 |
| Byte growth on every review path at phase end | Yes — item 3 |
| Corrupted (non-UTF-8) state file on a C locale shows a different refusal line | Yes — item 4 |
| Subfolder fix (D-19): with the session in a subfolder of the repo, the file is read from the repo root | Yes — owner decision D-19 |
| Close out and fix loop keep the state path (D-20, D-23) | Yes — owner decision D-20; D-23 on the page |
| Inline Python isolated (D-22) | Yes — owner decision D-22 |
| X1–X6 (settings and names now carry between separate calls) | Yes — "Fix all six" |
| Fewer commands and their output on screen | Yes — the intended difference |
| A fingerprint file already holding `{}` is refused | On the page; cannot occur through the instructions |
| ~~A top-level file whose name starts with `-` is now fingerprinted~~ | Removed by D-24: the helper matches 2.14.1 |
| ~~A repo folder whose name ends in whitespace: the helper checks the trimmed path~~ | Removed by D-25: the helper matches 2.14.1 |
| **The per-file git checks run in the root path; when that is not the session's repository (folder name ending in a line break beside a folder of the trimmed name; `core.worktree` elsewhere) the decision differs, both ways** | **No — not on the page; outside what D-19 describes** |
| **Each git call is given 60 seconds; a slower one leaves the file out** | **No — not on the page (safe direction only)** |

#### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `finalize_inputs.py` `_head_blobs` | per-file git run with `cwd=root`, where `root` is text from a shell-style trim and may not be the session's repository | Blocker (gap 3) | Wrong repository read in two unusual set-ups |
| `finalize_inputs.py` `GIT_TIMEOUT` | a limit 2.14.1 did not have, not on the accepted list | Minor (gap 4) | Safe direction only |
| files changed by the gap closure | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` | none found | — |

#### Notes (not gaps)

- **N-1 to N-6 and N-8** are carried unchanged from the earlier reports. **N-7** (the 60-second limit) is now gap 4.
- **N-9. A state whose finding `file` is a list.** Both sides stop and write nothing, but the stop sentence names a different script (2.14.1: "carry_state.py failed"; helper: "finalize_gate.py failed"). The plugin never writes such a state; found only by feeding malformed shapes. Not a decision difference.
- **N-10. Names git reads as a range.** For a file literally named like `x..HEAD`, `git rev-parse "HEAD:x..HEAD"` prints two lines on both sides. The helper keeps both lines as the blob text; what a model would have written at 2.14.1 from that output cannot be determined. With a verdict recorded from the same output both sides agree (probed). Theoretical only.
- **N-11. Duplicate rows for one finding id naming different files.** The helper takes the first row. 2.14.1's instruction ("find its finding by `stable_hash`") does not say which. The two cases I ran agree with 2.14.1 read as "first match"; the instruction itself is not specific enough to test further.
- **N-12. Non-UTF-8 folder names and other hosts** were not probed (see "Not probed").

#### Human Verification Required

None that blocks. Carried from the first report: no live review was run, so whether a live model fills the three switch slots, pastes the printed state path and branches on `next` as the scripted walks do has not been observed. Under the standing rule a live or paid run needs its own approved proposal; this report does not ask for one.

#### Gaps Summary

The gap this round was asked to check is closed: the helper now reads the repo root exactly as the 2.14.1 shell did, the tests compare against the real 2.14.1 command line through a shell and fail when they should (including when both sides are made to share the old mistake), and nothing I verified earlier has regressed.

The independent challenge found one more difference of the same family, older than both fixes. 2.14.1 ran its three per-file git commands in the session folder; the helper runs them in the root path. When the root path is not the session's own repository — a repo folder whose name ends in a line break with a folder of the trimmed name beside it, or a repo whose `core.worktree` points elsewhere — the helper reads the wrong repository or none, and the decision differs from 2.14.1 in both directions. It is rarer than either earlier gap and cannot be set up by the author of a reviewed change. It needs the owner's decision: match 2.14.1 (small; can ride in pull request #11) or accept it by name as an extension of D-19.

The 60-second limit on each git call, a note in the earlier reports, is now reproduced and listed as a minor gap that needs only an acceptance by name.

Both gaps come from one root cause: the helper re-does a shell procedure in-process and differs from it in small ways at the edges (how the root is found and used, how long git may take).

#### Residual risk (my judgement, separate from the status)

Three rounds have each found one exotic-input difference: how the file name is parsed, how the root text is trimmed, where the per-file git commands run. All three live in the same ~30 lines (the fingerprint step) and all three were present from the merge. This round I compared that step line by line with the 2.14.1 procedure and probed each remaining point of contact (about 170 end-to-end cases per Python version across rounds 2 and 3), so the easy candidates are used up. My estimate that another difference of this kind exists on macOS once gap 3 is settled: roughly one in five. On a host I could not test (Linux with a folder name that is not valid text, Windows): higher, perhaps one in three, and unknown in kind. The chance that any such remaining difference would affect a real review is very low; every one found so far needs a deliberately odd set-up on the reviewer's machine.

The single check that would reduce this most: keep the literal 2.14.1 step 1 as a small shell script in the test folder (the guard line and the three git commands, run in the session folder, exactly as the old instructions wrote them) and add one test that runs it beside the helper over a generated grid — folder-name endings × what sits at the trimmed name × git settings and `GIT_*` variables × session folder × file-name shapes × clean, edited and staged. My scratch probes for this round are a prototype of that grid. As a permanent test it would have caught all three gaps, and it would catch a fourth introduced by any later change to the helper. It is roughly a day of work and adds perhaps 20 to 30 seconds to the test run. Whether to commission it is the owner's call; I have not done it.

---

## History: second verification (2026-11-15T23:50:00Z, `66b0429`)

**Status then:** gaps_found. **Score then:** 4/5. Gap 1 (leading-dash file names, D-24) closed; one new blocking gap, now closed:

> One input class still gives a different gate decision from 2.14.1 and is not on the accepted list. It is not a file name: it is the repo's own folder name. When the folder the repo lives in has a name ending in whitespace (a space, a tab, a no-break space), the helper trims that whitespace from the repo root (`_toplevel` returns `result[1].strip()`); 2.14.1's `$(git rev-parse --show-toplevel)` drops only the final line break. The helper then checks a folder that is not the repo. Reproduced end to end on Python 3.9.6 and 3.14.5, clean file `x.ts` with a last-pass fix-obsolete verdict on unchanged code: (a) no folder at the trimmed path — 2.14.1 counts [0,0,0] gate `write`; helper counts [1,0,0] gate `outstanding-to-phase-5`. (b) a second git repo sits at the trimmed path (`repo` beside `repo `) holding the same file, and the real repo's file was edited after the verdict — 2.14.1 counts [1,0,0] gate `outstanding-to-phase-5`; helper counts [0,0,0] gate `write`.

That report also said: "Folder names ending in a line break were compared too and agree (both leave the file out)." That was true only with nothing at the trimmed name; with a folder there it is gap 3 of this report. My miss.

Evidence from that report, carried and not re-run now except where the tables above say so:

**Gap 1 closure, end to end (fix-obsolete verdict on unchanged code), Python 3.9.6, 3.12.12, 3.13.14, 3.14.5:**

| File | 2.14.1 | Helper | Same? |
|------|--------|--------|-------|
| `x.ts` (control) | [0,0,0] `write` | [0,0,0] `write` | yes |
| `-x.ts` | [1,0,0] `outstanding-to-phase-5` | [1,0,0] `outstanding-to-phase-5`, `next` = `finalize-card`, fingerprint file `{}`, stderr empty | yes |
| `sub/-x.ts` | [0,0,0] `write` | [0,0,0] `write` | yes |
| `-d/x.ts`, `--`, `-h`, `--pa`, `--root` | [1,0,0] `outstanding-to-phase-5` | the same | yes |
| `-`, `-1` | [0,0,0] `write` | the same | yes |
| `-1.ts`, `-1e5`, `-1_0` | 3.9 / 3.12 / 3.13: [1,0,0] `outstanding-to-phase-5`. 3.14: [0,0,0] `write` | the same as 2.14.1 on each version | yes |

**File names, fingerprint step only:** 131 names per Python version, 4 versions, 0 disagreements, 0 helper crashes (every abbreviation of `--root`, `--path`, `--help`; number look-alikes; 200- and 300-character names; a 40-folder-deep path; names the character filter refuses; trailing-slash, `./`, `..` and absolute forms).

**In-process versus command:**

| Risk | What I ran | Result |
|------|-----------|--------|
| The in-process parser differs from the command's | 300 random leading-dash names per version | 0 disagreements on all four versions |
| Output or state leaks between files | One state listing all 130 names once, twice, reversed, and `-x.ts`/`x.ts` alternating 50 times | Equal to the 2.14.1 set each time; stderr empty |
| stdout/stderr left replaced | Checked after every call | Always restored |
| Environment | `COLUMNS=1`, forced colour, `LC_ALL=C`, `PYTHONWARNINGS=error`, `PYTHONOPTIMIZE=2`, `PYTHONUTF8=1`, `-I`, `-S -E` | All the same as 2.14.1 |
| stderr closed or discarded | `2>&-` and `2>/dev/null` on `-x.ts` | Exit 0, `outstanding-to-phase-5`, `{}` |
| Names too long for a command line | 1.1 MB and 300 KB names | Both sides leave the file out |

**The D-24 test can fail (scratch clone):** fix line put back → both `TestGuardCommandParity` tests fail; the test at `c1541b1` fails; its 2.14.1 side swapped for the helper's old in-process check → both fail, with the helper fixed or unfixed; "starts with `-`" rule → fails; any-exit-except-1 → fails; stdout/stderr not restored → 5 fail; output not captured → 5 fail; containment removed → 7 fail; import set changed either way → `test_stdlib_import_set_is_exact` fails.

**Regression checks then (at `66b0429`):** `finalize_capture.py verify` and `compare` (Python 3.14 and 3.9, by commit and by folder) passed; 110 helper tests passed under the default locale, `LC_ALL=C` and Python 3.9.6; stdlib-only gate passed; 85 steps; 130,886 bytes; CI green on `66b0429`.

**Records then:** the leading-dash error corrected in the ledger, the result page, 63-01-SUMMARY and 63-REPRO; one docstring inaccuracy ("3.13+"), since corrected.

**Notes then:** N-6 (which leading-dash names are refused depends on the Python version, on both sides alike); N-7 (the 60-second limit; now gap 4); N-8 (a file name ending in a line break is fingerprinted by the helper; 2.14.1's own tool reads the pattern the same way).

---

## History: first verification (2026-11-15T23:15:00Z, `main` at `4ac7ee4`)

**Status then:** gaps_found. **Score then:** 4/5. **One blocking gap**, closed in round 2:

> For a finding in a top-level file whose name starts with `-` (for example `-x.ts`) that carries a last-pass fix-obsolete verdict on unchanged code, 2.14.1 leaves the finding open (gate `outstanding-to-phase-5`, nothing written); the new helper closes it and the gate returns `write` (APPROVED). At 2.14.1 the instructions ran `python3 "$GUARD_PY" --root … --path "<file>"` and required exit 0; that command exits 2 for a name starting with `-`, so the file was left out, fail closed. The helper calls `guard.contained()` in-process, which accepts the name. The records state the opposite. The named parity test asserts only the helper's own output and never runs the 2.14.1 command. Reproduced end to end on Python 3.9.6 and 3.14.5.

Evidence from that report that is carried and was not re-run in rounds 2 or 3:

- **Criterion 2:** the real fence from `90-finalize.md` run as its own fresh shell under bash and zsh against no state file, `not json`, `{}`, an unreadable state and unfilled switch slots; each stopped with the 2.14.1 sentence and wrote nothing.
- **Criterion 3:** `GATEFILE`, the counts fence, the report fence and the hand-written fingerprint step are gone; the rebuild, never-reuse and never-retry rules, the stop sentence, the write boundary and `record-decisions` remain; the moved explanation is byte-identical to `dd8e4ab` lines 34–39; all 112 cited test ids checked against the collected suite.
- **Criterion 4:** `c7d92c9` (extraction alone) 83 steps / 129,451 bytes; growth after it adds up exactly to the named items; tools, baseline records and `CRITERION.md` unchanged since Phase 62.
- **Criterion 5:** the check walks all 27 files; seven deliberate breaks to real phase files each failed it; each pre-fix file put back fails its reproduction test (X1–X8, C1); recorded-before-fixed order confirmed from commit times.
- **Guards that can trip:** 48 deliberate breaks in a scratch copy, 47 caught by the check they targeted, 1 (wrong `next` for `write`) passed the five-situation comparison and was caught by 8 unit tests (note N-1).
- **Full local suite:** 6,510 passed, 1 failed; the failure was caused by `PYTHONDONTWRITEBYTECODE=1` in my own run (`test_batchsnap.py::TestSnapshotImmutable::test_verify_survives_cache_churn`), and passes without it.
- **Spot-checks:** baseline records hold; guard pattern under bash 3.2, zsh 5.9 and sh; all 47 paste sites double-quoted; CI green on `main` (`4ac7ee4`) and on the PR #10 head.
- **Notes N-1 to N-5:** the five-situation comparison does not look at `next`; X8 and C1 write-ups followed their fixes by minutes; C2 stays on the exceptions list; the result page's "not recorded" byte figures are recoverable; names set only in prose are not seen by the check.

---

_Verified: 2026-11-16T01:43:00Z_
_Verifier: Claude (bm-verifier)_
