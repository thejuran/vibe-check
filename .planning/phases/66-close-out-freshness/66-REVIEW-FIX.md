---
phase: 66-close-out-freshness
fixed: 2026-11-18
review: 66-REVIEW.md
status: all_fixed
findings_fixed: [CR-01, WR-01, WR-02]
findings_carried: [IN-01, IN-02, IN-03, IN-04, SA-01]
base: 1007eac0
head: 4cee4e20
suite: "4729 passed, 2 xfailed, 2 warnings, 7252 subtests, 501.31 s, exit 0"
stdlib_check: "35 shipped .py files; third-party imports: none; exit 0"
---

# Phase 66: Code Review Fix Report

All three findings the orchestrator scoped (CR-01, WR-01, WR-02) are fixed. Each one has a RED test commit followed by a fix commit. Every fix was mutation-checked: I reverted it in place, showed that the named new tests fail, then restored it. IN-01..IN-04 and SA-01 are carried. They are recorded in backlog 999.46, which the orchestrator committed as 1007eac0.

## Commits (base 1007eac0 → HEAD 4cee4e20)

| Commit | Finding | What |
|--------|---------|------|
| acaa633d | CR-01 RED | Tests that decisions on special-character names are checked. Replaces `test_unverifiable_path_failing_PATH_RE`. |
| 51a57394 | CR-01 fix | Drops the PATH_RE gate, adds `core.quotePath=false`, adds a loop-freedom test |
| 3b0cd538 | WR-02 RED | A failure while finding the decided records must not let Close out write |
| 1ddfe265 | WR-02 fix | `stale_decisions` lets that failure propagate, and the helper stops at EXIT_GATE |
| f2a090bb | WR-01 RED | skip-worktree and assume-unchanged files get the cause `flagged`. Adds loop freedom and the prose lock. |
| 4cee4e20 | WR-01 fix | `flagged_files`, the new `flagged` cause, and the refusal prose in 90-finalize.md |

## CR-01: special-character names no longer refuse forever

- **Fix:** `_path_ok` no longer uses `fixcommit.PATH_RE`. A record now fails closed (`unverifiable`) only when:
  - git would still C-quote its name in a diff header (`"`, `\`, control characters or DEL), or
  - the name is not a repo-relative path (empty, not a string, absolute, a `..` segment, or U+FFFD left by a failed decode).

  Every git call now runs with `-c core.quotePath=false`, so non-ASCII names come out raw. The `fixcommit` import is gone, and the module docstring has a new WHICH NAMES section. No path reaches a git argv: `TestArgvHygiene` and the new ls-files argv test both stay green.
- **Tests:** `TestSpecialNames` covers `+page.svelte`, `[slug]`, `(group)`, `@scope`, `my file.py`, `café.py` and `文件.py` with both decision kinds:
  - unchanged → kept
  - edit on line 10 → `line`
  - edit on line 14 → `nearby`

  A pin checks that the trailing tab after a space-name header is stripped. A pin checks that non-ASCII names come out raw. An end-to-end helper run gives write when unchanged and refuse `line` when edited.

  `test_unverifiable_path_git_would_quote_or_not_a_repo_path` and `test_unverifiable_quoted_name_present_and_unchanged` cover names that cannot be represented, including real files with `"`, `\`, tab or newline in the name.
- **Loop freedom:** `TestClearableSpecialName` runs `src/routes/+page.svelte` through the real 66-06 `_ClearChain` fences. Unchanged → write. Edit → refuse `line` → review again → re-decide → write. Both kinds pass.
- **Mutation:**
  - Restoring the PATH_RE gate: 37 TestSpecialNames failures, and both loop subtests fail with `unverifiable`.
  - Dropping `core.quotePath=false`: 7 failures. Without it, a non-ASCII file's edit is silently kept, which is a wrong keep.
  - Dropping the quote and containment rejection: 14 TestUnverifiable failures.
- **Accepted residual:** a decision on a file whose name holds `"`, `\` or a control character still refuses on every attempt. Reviewing again cannot clear it, because the name stays the same. The orchestrator's instruction asked for exactly this fail-closed behavior. Such names are very rare in real repos.

## WR-02: a failure while finding the decided records now fails closed

- **Fix:** `stale_decisions` no longer catches exceptions from `decided_records`. A malformed state still returns `[]` without raising, because `carry_state.open_findings` treats it as having no open record. I probed `None`, `{}`, `[]`, `{"passes": []}`, `{"passes": "x"}` and nested shapes, and none of them raise. Any other exception now propagates to `finalize_inputs.run`, which already returns `(EXIT_GATE, "")`.

  In 90-finalize.md, a non-zero exit other than 5 is retried once and then stops with "Finalize stopped — nothing was written or archived". Nothing is written.
- **Tests:** `TestCandidateFailureFailsClosed`:
  - `stale_decisions` raises when `_spots` raises.
  - End to end through the helper, patching `_spots` or `decided_records` to raise gives `(4, "")`. The same state unpatched gives `write`.
- **Mutation:** restoring the `except Exception: return []` makes 5 of these fail.
- **Logging:** nothing is logged on this path, which matches how the helper handles every other gate failure (the exit code is the diagnostic). The refusal is now loud: Finalize stops. Before the fix it was a silent write.

## WR-01: skip-worktree and assume-unchanged files refuse with clear advice (owner ruling)

- **Fix:** new `flagged_files(root)` reads `git ls-files -v -z` once, only after the candidates are known. It has no path on the argv and uses the same read-only env as the diff. Tag `S` means skip-worktree and a lowercase tag means assume-unchanged.

  New cause token `flagged` (CAUSES now has six entries). It sits after `untracked` in the cause order and before line/nearby/deleted, so a flagged file is `flagged` whether it was edited or not. It also applies when a spot's file is flagged: that spot's window check cannot see edits either, so nothing is proven unchanged. If git fails to read the flags, the result is `unverifiable`.
- **Prose (90-finalize.md):**
  - Cause sentence: "`flagged` → git is set to ignore edits to the file (skip-worktree or assume-unchanged)".
  - Next step: "When any entry's cause is `flagged`, add: "Clear the flag (`git update-index --no-skip-worktree <file>` or `git update-index --no-assume-unchanged <file>`), then review again.""
  - Both phrases are in `REVIEW_AGAIN_NEEDLES`, so the existing every-needle and cause-sentence mutants cover them. There is also a new `test_mutant_flagged_next_step`, and `test_flagged_sentence_names_every_cause` ties the prose to `closeout_fresh.CAUSES`.
- **Tests:** `TestFlaggedFiles`:
  - Same edit on line 10: unflagged → `line`, skip-worktree → `flagged`, assume-unchanged → `flagged`, for both kinds. These are subtests, each in its own repo, rather than one three-file repo.
  - Unchanged flagged file → `flagged`.
  - Both flags at once → `flagged`.
  - A flag on an unrelated file has no effect.
  - The ls-files argv carries no path.
  - An ls-files failure gives `unverifiable`.
  - Helper end to end refuses with `flagged`.
  - A flagged spot file gives `flagged`.
- **Loop freedom:** `TestClearableFlagged`, through the real fences: set the flag and edit → refuse `flagged` → `git update-index --no-…` → review again → re-decide → write. Covers both flags and both kinds.
- **Mutation:**
  - Removing the flagged check: 12 failures.
  - Matching skip-worktree only: 5 assume-unchanged failures.
  - Ignoring spot files: the spot test fails.
- **SA-01 interaction:** if the owner reviews again without clearing the flag, the review snapshot still misses the edit (SA-01, carried), and Close out refuses again with `flagged`. That is fail closed, not a write. The refusal's advice clears it.

## Locks kept green

- 2.15.0 Finalize differential (`TestOnlyIntendedDifferences`): no fixture result changed, so INTENDED and REPAIRED were not edited. No fixture uses a special-character name, a flagged file or a raising candidate step.
- Parity grid: 284 scenarios. 198 agree, 12 D-19, 56 D-09 refusals, 0 known differences, 0 unexpected, 18 not creatable here. Name-form grid: 549 scenarios, 0 unexpected.
- The `guard.py`, `finalize_gate.py` and `fixcommit.py` byte-identity pins vs dd8e4ab still hold. `git diff dd8e4ab HEAD` on those three files is empty, and fixcommit.py was not edited.
- The 999.40 repro, the 66-06 loop-freedom tests and the 2 shape-1 xfails are unchanged and in their expected states.

## Verification (observed, HEAD 4cee4e20)

- Full offline suite, `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`: **4729 passed, 2 xfailed, 2 warnings, 7252 subtests passed, 501.31 s, exit 0**. 66-09 had 4706 passed, so this run has 23 more tests. The 2 xfails are the shape-1 known-limit tests.
- Stdlib check, `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`: **35 shipped .py files; third-party imports: none; exit 0**. `closeout_fresh.py` stdlib imports are still exactly {os, subprocess, sys}.

## Carried (not fixed here)

IN-01, IN-02, IN-03, IN-04 and SA-01 are in backlog 999.46 (commit 1007eac0).

## Gap-closure review fixes (2026-11-19)

Source: the gap-closure `66-REVIEW.md` (plans 66-10..66-12, diff 65190000..HEAD). Scope set by the owner's rule: new work only for the reproduced silent finding loss (CR-01) and its direct test gap (WR-02). Base 1da712e3, head cb2da984, branch feat/v2.16-phase-66.

| Finding | Status | Commits |
|---|---|---|
| CR-01: `REMOVED_LINE_RANGES` silently dropped C-quoted (non-ASCII) paths | fixed | 9b36b954 (RED), e3888c9c (fix) |
| WR-02: parser's risky inputs untested; no mutants on quote, tab or `\` handling | fixed | cb2da984 |
| WR-01: forced pair re-asks neighbouring decided records within ±5 lines | carried to owner | none |
| WR-03: simulator records Needs-verification moves, prose excludes them | carried to owner | none |
| IN-01, IN-02, IN-03, IN-04 | carried to owner | none |
| SA-01, SA-02 | carried to owner (needs ruling) | none |

### CR-01 (fixed)

- **RED, 9b36b954 `test(66-review)`:** `TestQuotedNamesCR01` runs the production since-review call (`since_both`, tree to tree, real `git diff`) in a temp repo with global and system git config off. Result: 4 failed, 1 passed. Deleting line 10 of `café.py` gave removed `{}` ("known, nothing removed"), so the forced re-ask of a decision moved off that line returned `{}`. That is the 999.44 shape 1 silent keep, reproduced. A name git still quotes (`a"b.py`) gave a known value `{"src/a.py":[[3,3]]}` instead of unknown. The passing test is the quoted *added* file, which stays `{}`.
- **Fix, e3888c9c `fix(66-review)`:**
  1. The since-review `git diff` in `worktree_snap.since_both` now runs with `-c core.quotePath=false`. This is a flag on the existing call, following `closeout_fresh.py`. No git call was added; the `test_differential_no_extra_git_call` count is unchanged.
  2. Fail safe. `_old_path` raises a new `UndecodablePath` in two cases: an old-side `--- ` name git still quotes (`"`, `\` or a control character) and a name that is not valid UTF-8 (the decoded name contains U+FFFD). `since_both` catches it, keeps the changed ranges and returns removed `None`. `collect` then prints `REMOVED_LINE_RANGES=` empty and notes "removed lines unknown". A quoted *new-side* name on an added file is still `{}` (`--- /dev/null`, no reviewed side).
- **Invariant choice (deliberate, documented).** 66-10's contract said removed is empty *exactly* when nearby is empty. Keeping that for an undecodable name would have meant blanking `NEARBY_LINE_RANGES=`, which changes line 2 against d5acc19. I kept line 2 instead and relaxed the invariant. Removed is now empty **whenever** nearby is empty, **and also** when a reviewed-side name cannot be decoded. The forced re-ask rule already treats an empty removed value as unknown, so it re-asks every move; it never keeps one silently. The prose sentence in `30-collect-score.md` (since-review bullet) and the `worktree_snap.py` module and `collect` docstrings now say this. No locked prose phrase changed (`test_nv_render` and `test_simulator_matches_locked_prose` pass).
- **Line-2 effect against d5acc19 (`TestQuotedNamesDifferentialV215`, literal d5acc19 helper as a subprocess):**
  - Still-quoted name: the first two lines are byte-identical and the third is `REMOVED_LINE_RANGES=`.
  - Non-ASCII name: the one intended line-2 difference from the mandated flag. 2.15.0 printed `{"src/a.py":[[2,3]]}` (the café.py change was missing). Now it prints `{"café.py":[[9,10]],"src/a.py":[[2,3]]}`, and REMOVED holds `café.py [[10,10]]`. Before this change the shared `NEARBY` map was blind to such files. The new value errs toward re-asking.
  - All 13 existing `REMOVED_GRID` states are unchanged: first two lines byte-identical, third as before.
- `score.py` and `diff_ranges.py`: `git diff --quiet d5acc19 --` exits 0. No new import in `worktree_snap.py`.
- Residual note, not changed: JSON output uses `ensure_ascii`, so the printed key reads `café.py`. That is valid JSON and parses to the real name. The orchestrator compares it after parsing.

### WR-02 (fixed)

- **Tests, cb2da984:** `TestRemovedRiskyInputs`, real git through the production since-review call. Each input and its expected result:
  - Name with a space (git appends a tab): `{"has space.py": [[10,10]]}`.
  - `\ No newline at end of file` inside a hunk that also deletes lines: `[[10,10],[12,12]]`.
  - Deleted last line of a file with no final newline: `[[11,12]]`.
  - Rename with edits and `diff.renames` unset (git's default detects it): keyed by the old path, `[[10,10]]`.
  - Rename with edits and `diff.renames=false` in the repo config: the whole old file, `[[1,12]]`.
  - Binary change: `{}`.
  - Mode-only change: `{}`.
  - New file: `{}`.
  - Deleted file: every line.
  - Name that is not valid UTF-8 (byte 0xE9, trees built with `git mktree`): unknown (`None`).
  - The non-ASCII and still-quoted cases are in `TestQuotedNamesCR01`.
- **Mutants (`TestQuoteAndBodyMutants`, in-suite, plus applied in place to the real file):**

| Mutant | Change | Named test that fails with it applied in place |
|---|---|---|
| M6 | a still-quoted name is skipped (`return None`, the pre-fix behaviour) | `TestQuotedNamesCR01::test_still_quoted_name_makes_removed_unknown` |
| M7 | `-c core.quotePath=false` dropped | `TestQuotedNamesCR01::test_non_ascii_name_lists_the_removed_line` (the fail-safe then makes the value unknown, not `{}`) |
| M8 | trailing-tab strip dropped | `TestRemovedRiskyInputs::test_space_name_strips_the_trailing_tab` |
| M9 | `\` (no-newline) skip dropped | `TestRemovedRiskyInputs::test_no_newline_marker_inside_a_deleting_hunk` |
| M10 | U+FFFD name accepted | `TestRemovedRiskyInputs::test_name_not_valid_utf8_makes_removed_unknown` |

  Each mutant was written into `worktree_snap.py` by a scratch script. The script ran the named test (exit 1 each time, "1 failed"), restored the original bytes, and confirmed `git diff --quiet -- worktree_snap.py` is clean.

### Verification (observed, HEAD cb2da984)

- Full suite, `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider`: **4337 passed, 2 warnings, 7126 subtests passed, 522.92 s, exit 0**.
- 2.15.0 differentials, `pytest -q -p no:cacheprovider -k "DifferentialV215 or only_intended"`: **12 passed, 4325 deselected, 428 subtests passed, 71.44 s**. This includes the two new `TestQuotedNamesDifferentialV215` tests.
- `test_worktree_snap.py` alone: 127 passed, 87 subtests.
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`: 35 shipped .py files; third-party imports: none.
- `git diff --quiet d5acc19 -- plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/diff_ranges.py`: exit 0.
- Evidence class: offline only. There was no live reviewer run.

### Carried to owner

WR-01, WR-03, IN-01, IN-02, IN-03, IN-04, SA-01 and SA-02 are not fixed here, per the owner's scope rule. WR-03 depends on the SA-01 ruling. WR-01 has two options: document and lock the side effect, or add a per-hash key in score.py, which needs a ruling against the score.py byte-identity constraint.
