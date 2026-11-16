---
phase: 63-finalize-extraction-and-cross-call-variable-check
verified: 2026-11-16T00:14:00Z
status: gaps_found
score: 4/5 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  previous_verified: 2026-11-15T23:50:00Z
  gaps_closed:
    - "Repo folder name ending in whitespace (D-25): the helper now reads the repo root as 2.14.1's `$(git rev-parse --show-toplevel)` does (trailing line breaks dropped, nothing else). Folder names ending in a space, tab, no-break space, carriage return, vertical tab, form feed, em space, and `repo ` beside `repo` with the real file edited after the verdict, all give the 2.14.1 decision on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5."
    - "Leading-dash file names (D-24), closed in the previous round: re-probed, still matches 2.14.1 on all four Python versions."
  gaps_remaining: []
  regressions: []
  new_gaps:
    - "The helper runs its three per-file git checks in the folder named by the root path; 2.14.1 ran them in the session folder. When those are not the same repository the decision differs, in both directions (not caused by either gap closure; present since the merge of PR #10; missed by both earlier verifications)"
    - "The helper's 60-second limit on each git call (note N-7 in the earlier reports, now reproduced; safe direction only; minor)"
gaps:
  - truth: "Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline"
    status: partial
    severity: blocking
    reason: "One mechanism still gives a different gate decision from 2.14.1 and is not on the accepted list. 2.14.1 gave the containment check the root as text and then ran `git rev-parse HEAD:<file>`, `git diff --quiet HEAD -- <file>` and `git diff --cached --quiet -- <file>` in the SESSION folder. The helper runs those three commands with the root path as their working folder (`_git(..., root)`). That was accepted under D-19 for a session in a subfolder of the repo, where the root is the same repository. When the root path is NOT the session's repository, the helper reads a different repository or none. Reproduced end to end with the session AT the repo root, on Python 3.9.6, 3.12.12, 3.13.14 and 3.14.5 (first trigger) and 3.9.6 and 3.14.5 (second trigger), and identically on the merged helper at `4ac7ee4`. Trigger 1, repo folder whose name ends in a line break (the one ending 2.14.1's shell also drops), with a folder under the trimmed name beside it: (a) the neighbour is a repo holding the same file and the real file was edited after the verdict: 2.14.1 [1,0,0] `outstanding-to-phase-5`; helper [0,0,0] `write` (an approval 2.14.1 would not give); (b) the neighbour is a plain folder and the real file is unchanged: 2.14.1 [0,0,0] `write`; helper [1,0,0] `outstanding-to-phase-5`. Trigger 2, a repo whose git setting `core.worktree` points at another folder, session in the folder holding `.git`: (c) unchanged file: 2.14.1 [0,0,0] `write`; helper [1,0,0] `outstanding-to-phase-5`; (d) the other folder is itself a separate repo and the session's repo has a staged edit: 2.14.1 [1,0,0] `outstanding-to-phase-5`; helper [0,0,0] `write`. Both triggers are very unusual set-ups on the reviewer's own machine and cannot be arranged by the author of a reviewed change. D-19 as recorded says the helper's choice means 'an edited file is never fingerprinted'; cases (a) and (d) are the opposite, so D-19 does not cover them."
    artifacts:
      - path: "plugins/vibe-check/scripts/finalize_inputs.py"
        issue: "`_head_blobs` (lines 200, 203, 205) runs the three per-file git commands with `cwd=root`, where `root` is the text handed to the containment check. 2.14.1 ran them in the session folder. No check that `root` is the repository the session is in."
      - path: "plugins/vibe-check/scripts/test_finalize_inputs.py"
        issue: "`TestRepoFolderNameParity::test_parity_other_folder_name_endings` covers folder names ending in a line break only with nothing at the trimmed name, where both sides leave the file out. No test puts a folder or repo at the trimmed name, and no test sets `core.worktree`."
      - path: ".planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REPRO.md"
        issue: "The audit table row 'Several trailing `\\n`' says a difference there cannot change a decision ('both give another folder; probed') and the row for the per-file git folder says 'not this mechanism'. With a folder at the trimmed name both statements are wrong. 63-RESULT.md ('only the repo-folder trim differed') and the ledger ('found no further difference') repeat it."
    missing:
      - "Either: run the three per-file checks against the session's own repository while keeping the D-19 subfolder behaviour (so the file name is still read from the repo root), with end-to-end tests against the 2.14.1 commands for cases (a) to (d) and a mutant for each direction; or: an owner acceptance of this difference by name, recorded as an override here and added to the result page's list of differences"
      - "Either way: correct the two audit rows in 63-REPRO.md and the 'no further difference' sentences in 63-RESULT.md and the ledger"
  - truth: "Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline"
    status: partial
    severity: minor
    reason: "The helper stops waiting for any one git command after 60 seconds and leaves that file out; the 2.14.1 commands had no limit of their own. Reproduced with real git made slow (a 65-second `core.fsmonitor` hook): the 2.14.1 commands all exit 0 and give [0,0,0] `write`; the helper gives [1,0,0] `outstanding-to-phase-5` after 60 seconds. Safe direction only (the finding stays open and the owner is asked); no unsafe direction exists. At 2.14.1 the only limit was the session's own limit on a shell call (two minutes by default), so the two differ only for a git command that takes between one and two minutes on one file. This was note N-7 in the two earlier reports; it is listed as a gap now because it is reproduced and is not on the accepted list. Graded minor: it does not on its own block the phase goal and needs only an owner acceptance by name."
    artifacts:
      - path: "plugins/vibe-check/scripts/finalize_inputs.py"
        issue: "`GIT_TIMEOUT = 60`; a timed-out call returns None and the file is left out"
    missing:
      - "An owner acceptance by name on the result page's list of differences (recommended: keep the limit; without it a stuck git would hang Finalize until the session kills it)"
---

# Phase 63: Finalize extraction and cross-call variable check — Verification Report

**Phase Goal:** Finalize's mechanical steps run through tested stdlib helpers and behave exactly as in 2.14.1, with less model-interpreted prose on the same paths, and a shell variable read across Bash calls is caught by one general check in any phase file.
**Verified:** 2026-11-16T00:14:00Z, against branch `feat/v2.15-phase-63-gap` at `48b307f` (three commits on top of the second verification commit `b43054d`; `main` is at `4ac7ee4`; follow-up pull request #11 open, not merged, both CI runs green on `48b307f`)
**Status:** gaps_found
**Re-verification:** Yes — third round, after the second gap closure

## Result in plain terms

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

## Re-verification summary

| Item | Round 1 (23:15Z, `4ac7ee4`) | Round 2 (23:50Z, `66b0429`) | Now (`48b307f`) |
|------|------------------------------|------------------------------|-----------------|
| Status | gaps_found | gaps_found | gaps_found |
| Score | 4/5 | 4/5 | 4/5 |
| Gap 1: leading-dash file names (D-24) | open, blocking | closed | closed (re-probed) |
| Gap 2: repo folder name ending in whitespace (D-25) | not found (was present) | open, blocking | **closed** |
| Gap 3: per-file git runs in the root path, not the session folder, when these are different repositories | not found (was present) | not found (was present) | **open, blocking** |
| Gap 4: 60-second limit per git call | not noted | note N-7 (not reproduced) | **open, minor** (reproduced) |
| Regressions | — | none | none |

### What I ran now and what I carried

| Criterion | Now | How |
|-----------|-----|-----|
| 1 (same decisions as 2.14.1) | **Re-ran** | Everything in "Second gap closure evidence", "Independent challenge" and "Regression checks" below |
| 2 (bad inputs stop; nothing written; restart works) | **Carried**, with a partial re-run | This diff changes one line in `_toplevel`. Re-ran: the five-situation comparison (includes `one-rebuild`, `refused-close`, `fresh-shell-restart`), all of `test_finalize_inputs.py`, and 34 malformed-state shapes through both sides (both stop on the same ones). Not re-run: the real fence under bash and zsh against the six fault cases |
| 3 (superseded prose removed, invariants kept) | **Carried** | `git diff 66b0429 48b307f -- plugins docs .github` touches `finalize_inputs.py` and `test_finalize_inputs.py` only |
| 4 (before/after counts, revert rule) | **Re-ran the counts**, carried the rest | 85 steps and 130,886 bytes at `48b307f` |
| 5 (the general cross-call check) | **Carried** | No phase file and no check file changed |

## Goal Achievement

### Observable Truths (roadmap success criteria — the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline | ✗ FAILED (partial) | Gaps 1 and 2 are closed. One mechanism still differs (the folder the per-file git commands run in, when it is not the session's repository), plus the 60-second limit. See the gaps. |
| 2 | Missing, malformed or stale Finalize inputs stop with a plain message; a failed or refused attempt writes no report and archives nothing; restart and retry work across fresh shell calls | ✓ VERIFIED (carried; partial re-run) | Earlier evidence stands. The five-situation comparison and the 114 helper tests pass at `48b307f`. |
| 3 | Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host | ✓ VERIFIED (carried) | No file under this truth changed. |
| 4 | Loaded prose and helper/tool steps on the same Finalize paths are compared before and after against the Phase 62 criterion; the slice is reverted if it adds complexity without a demonstrated benefit | ✓ VERIFIED (counts re-run) | `step_count.py --rev HEAD --json`: 85 steps (35 fences, 5 inline commands, 5 Write-tool writes, 40 paste sites). `footprint.py --rev HEAD --json`: Finalize 130,886 bytes. Both identical to `4ac7ee4` and `66b0429`. |
| 5 | One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips; any phase file it flags is recorded with its reproduction before it is changed | ✓ VERIFIED (carried) | No file under this truth changed. |

**Score:** 4/5 truths verified

### Deferred Items

None. Phase 65 (release gate) checks equivalence in general terms but names nothing about this mechanism, so the gaps are not deferred to it.

### How the comparison was made (all run by me, scratch only)

A fresh clone at `48b307f` and a `git archive` of `dd8e4ab` (2.14.1), both under the session scratch folder; nothing in the working checkout was touched. `guard.py`, `carry_state.py`, `finalize_gate.py`, `batch_card.py` and `fixcommit.py` are byte-identical between the two.

- **2.14.1 side:** my own script, not the project's test code. For each last-pass fix verdict: the character filter; then the literal guard line `python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"` run through `/bin/sh` in the session folder with the `dd8e4ab` `guard.py`; then the three git commands in the session folder; a file kept only when all exit 0; then `carry_state.py finalize-counts` and `finalize_gate.py` from `dd8e4ab`.
- **Helper side:** `finalize_inputs.py` at `48b307f`, run as a command from the same session folder, same interpreter, same environment.
- A case is "same" only when the fingerprint set, the three counts and the gate action are all equal.

### Second gap closure evidence

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

### The new tests can fail (scratch copies of `plugins/vibe-check` at `48b307f`, bare `pytest test_finalize_inputs.py`)

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

### Independent challenge (step 2 of the request)

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

### Gap 3 in detail

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

### Gap 4 in detail (minor)

The helper gives each git command 60 seconds, then leaves the file out. Reproduced with a hook that makes git wait 65 seconds: every 2.14.1 command exits 0 and the decision is `write`; the helper returns `outstanding-to-phase-5` after 60 seconds. There is no unsafe direction: a timed-out file is only ever left out. At 2.14.1 the only limit was the session's own limit on a shell call (two minutes unless changed), so the two can differ only for a git command that takes between one and two minutes on a single file. I recommend accepting it by name and keeping the limit; removing it would let a stuck git hang Finalize.

### Regression checks (run by me in the scratch clone at `48b307f`)

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

### Corrected records, checked against what is true now

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

### Plan-level truths (carried, updated where this round changes them)

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

### Required Artifacts

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

### Key Link Verification

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

### Data-Flow Trace (Level 4)

Not applicable: no artifact in this phase renders dynamic data. The helper's data flow (state file → fingerprints → counts → gate → result) is exercised end to end by the comparisons above.

### Behavioral Spot-Checks and Probe Execution

The comparisons and regression checks above are the spot-checks. No `scripts/*/tests/probe-*.sh` probes are declared by this phase.

### Requirements Coverage

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

### Differences from 2.14.1 found in the code, against the accepted list

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

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `finalize_inputs.py` `_head_blobs` | per-file git run with `cwd=root`, where `root` is text from a shell-style trim and may not be the session's repository | Blocker (gap 3) | Wrong repository read in two unusual set-ups |
| `finalize_inputs.py` `GIT_TIMEOUT` | a limit 2.14.1 did not have, not on the accepted list | Minor (gap 4) | Safe direction only |
| files changed by the gap closure | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` | none found | — |

### Notes (not gaps)

- **N-1 to N-6 and N-8** are carried unchanged from the earlier reports. **N-7** (the 60-second limit) is now gap 4.
- **N-9. A state whose finding `file` is a list.** Both sides stop and write nothing, but the stop sentence names a different script (2.14.1: "carry_state.py failed"; helper: "finalize_gate.py failed"). The plugin never writes such a state; found only by feeding malformed shapes. Not a decision difference.
- **N-10. Names git reads as a range.** For a file literally named like `x..HEAD`, `git rev-parse "HEAD:x..HEAD"` prints two lines on both sides. The helper keeps both lines as the blob text; what a model would have written at 2.14.1 from that output cannot be determined. With a verdict recorded from the same output both sides agree (probed). Theoretical only.
- **N-11. Duplicate rows for one finding id naming different files.** The helper takes the first row. 2.14.1's instruction ("find its finding by `stable_hash`") does not say which. The two cases I ran agree with 2.14.1 read as "first match"; the instruction itself is not specific enough to test further.
- **N-12. Non-UTF-8 folder names and other hosts** were not probed (see "Not probed").

### Human Verification Required

None that blocks. Carried from the first report: no live review was run, so whether a live model fills the three switch slots, pastes the printed state path and branches on `next` as the scripted walks do has not been observed. Under the standing rule a live or paid run needs its own approved proposal; this report does not ask for one.

### Gaps Summary

The gap this round was asked to check is closed: the helper now reads the repo root exactly as the 2.14.1 shell did, the tests compare against the real 2.14.1 command line through a shell and fail when they should (including when both sides are made to share the old mistake), and nothing I verified earlier has regressed.

The independent challenge found one more difference of the same family, older than both fixes. 2.14.1 ran its three per-file git commands in the session folder; the helper runs them in the root path. When the root path is not the session's own repository — a repo folder whose name ends in a line break with a folder of the trimmed name beside it, or a repo whose `core.worktree` points elsewhere — the helper reads the wrong repository or none, and the decision differs from 2.14.1 in both directions. It is rarer than either earlier gap and cannot be set up by the author of a reviewed change. It needs the owner's decision: match 2.14.1 (small; can ride in pull request #11) or accept it by name as an extension of D-19.

The 60-second limit on each git call, a note in the earlier reports, is now reproduced and listed as a minor gap that needs only an acceptance by name.

Both gaps come from one root cause: the helper re-does a shell procedure in-process and differs from it in small ways at the edges (how the root is found and used, how long git may take).

### Residual risk (my judgement, separate from the status)

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

_Verified: 2026-11-16T00:14:00Z_
_Verifier: Claude (bm-verifier)_
