# Phase 65 release candidate
candidate: b073e31fb77f3f5ca32747f8c549ec552687b1be
parent: d31787df35a3689cfdbed36ae48e6ff84a4d3205
version: 2.15.0
suite_on_edited_tree: 4126 passed, 0 failed, 0 skipped (pytest -q -p no:cacheprovider in plugins/vibe-check/scripts)
fix_round: WR-02 (65-03)

## C (current candidate, b073e31)

`git show --stat --format=%s b073e31`:

```
release: vibe-check 2.15.0 — lean orchestration

 README.md                                     | 23 +++++++++++++++++++++--
 plugins/vibe-check/.claude-plugin/plugin.json |  2 +-
 2 files changed, 22 insertions(+), 3 deletions(-)
```

`git diff --name-only origin/main b073e31 -- plugins` (plugin.json plus the four 65-03 fix files):

```
plugins/vibe-check/.claude-plugin/plugin.json
plugins/vibe-check/phases/review/00-scope.md
plugins/vibe-check/phases/review/05-state.md
plugins/vibe-check/scripts/test_cross_call_vars.py
plugins/vibe-check/scripts/test_pasted_name_guard.py
```

Runs on the edited working tree in the main checkout, from `plugins/vibe-check/scripts`, with `PYTHONDONTWRITEBYTECODE` unset:
- `pytest -q -p no:cacheprovider test_recovery_pairs.py test_gitguard.py` → `185 passed, 708 subtests passed in 4.52s` (README holding `N_PASSING`), then again after the number was filled: `185 passed, 708 subtests passed in 4.48s`.
- `pytest -q -p no:cacheprovider -rs` → `4126 passed, 2 warnings, 6207 subtests passed in 260.19s (0:04:20)`; 0 failed, 0 errors, 0 skipped. Only the `N_PASSING` token changed after this run.

The README count (4,126) is the scripts-folder form used for every earlier README count (2.14.1: 3,886). It is lower than 65-03's 4,599, which is the repo-root G1b form that also collects `.github/scripts` and `docs/design/lean-v2.15/tools`.

## Dependabot (before the bump)

Run 2026-11-16 in the main checkout, before plugin.json was changed (HEAD `d31787df35a3689cfdbed36ae48e6ff84a4d3205`).

| Command | Exit | First output line |
|---|---|---|
| `gh api repos/thejuran/vibe-check/dependabot/alerts --jq '[.[] \| select(.state=="open")] \| length'` | 1 | `{"message":"Dependabot alerts are disabled for this repository.", … "status":"403"}` then `gh: Dependabot alerts are disabled for this repository. (HTTP 403)` and `gh: This API operation needs the "admin:repo_hook" scope. …` |
| `gh pr list --author app/dependabot --state open` | 0 | (no output: no open Dependabot pull requests) |
| `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | 0 | `34 shipped .py files; third-party imports: none` |

Dependabot alerts are disabled on this repository, and the CLI lacks the scope (`admin:repo_hook`) the alerts call asks for. The pull-request listing ran and found no open Dependabot pull requests. The shipped scripts use only Python's standard library (pytest is test-only). No setting was changed.

## Recount at the pre-C HEAD (D-06)

Counted at `d31787df35a3689cfdbed36ae48e6ff84a4d3205` (its `plugins/` instruction files equal C's; C changes only plugin.json under `plugins/`) against 2.14.1 `dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4`, with `footprint.py --rev --json` and `step_count.py --rev --mode <m> --json` (`totals.model_run_steps`).

| Path | Bytes 2.14.1 | Bytes C | Δ bytes | Δ % | Steps 2.14.1 | Steps C | Δ steps |
|---|---|---|---|---|---|---|---|
| Finalize | 136,114 | 131,381 | −4,733 | −3.48% | 92 | 85 | −7 |
| Plain review | 192,057 | 193,762 | +1,705 | +0.89% | 36 | 38 | +2 |
| Deep review | 268,997 | 270,714 | +1,717 | +0.64% | 42 | 44 | +2 |
| Plain review `--all` | 284,926 | 286,880 | +1,954 | +0.69% | 45 | 47 | +2 |
| Deep review `--all` | 361,866 | 363,832 | +1,966 | +0.54% | 51 | 53 | +2 |
| Fix loop | 255,070 | 256,939 | +1,869 | +0.73% | 112 | 114 | +2 |

Per changed instruction file (bytes 2.14.1 → C, Δ): `01d-coverage.md` 26021 → 26024 (+3); `2c-codex-kickoff.md` 17667 → 17673 (+6); `30-codex-collect.md` 13440 → 13443 (+3); `00-scope.md` 20088 → 20617 (+529); `05-state-all.md` 5753 → 6002 (+249); `05-state.md` 19484 → 20699 (+1215); `06-config.md` 15463 → 15424 (−39); `50-fix-loop.md` 63013 → 63177 (+164); `90-finalize.md` 55923 → 49485 (−6438).

Reconciliation: the 65-RESEARCH figures at Phase 63 end plus the 65-03 named growth (+495 bytes on every path, 0 steps; `00-scope.md` +149, `05-state.md` +346) equal this recount on every path (for example plain review 193,267 + 495 = 193,762; Finalize 130,886 + 495 = 131,381). `00-scope.md` +380 + 149 = +529 and `05-state.md` +869 + 346 = +1215.

## README fact-check

| README claim (short) | Evidence | Result (kept / reworded / removed) |
|---|---|---|
| plugin.json `"version": "2.15.0"` | `plugins/vibe-check/.claude-plugin/plugin.json` L4; only version field (65-RESEARCH §Release mechanics); 2.14.1 mentions in `finalize_inputs.py` and `fixtures/finalize_step1_2141.sh` left unchanged | kept |
| Header: "Close out works out its inputs in one tested helper. Not measured." | `phases/shared/90-finalize.md` L5 and L11-L19 (one `finalize_inputs.py` call; "this file runs no git command for the fingerprints … does not run the gate itself"); `scripts/finalize_inputs.py` docstring; `test_finalize_inputs.py` | reworded: the planned "runs as one checked step" overstated it (Close out still has 85 counted steps) |
| Lean-orchestration release; Claude used to run each fingerprint, counting and decision command; one helper now does it and returns one result | 63-RESULT "The two counts" (92 → 83 steps on the extraction alone); `90-finalize.md` L5 "Who owns what"; `finalize_inputs.py` stdout = one JSON object | kept |
| Does not change what reviewers look for, the scoring formula or any score; archived replay of 170 runs re-scores with no differences | `git diff --quiet v2.14.1 HEAD -- scripts/carry_state.py scripts/score.py` exit 0 (this session); 65-RESEARCH G4a `runs compared: 170`, `runs differing: 0` on the same scorer; 65-05 G4a re-confirms on C | kept ("no differences", not "identical") |
| Not B3- or holdout-measured; v2.11 still last measured | 65-CONTEXT (no paid or measurement run in this gate); README v2.11 paragraph | kept |
| "(4,126 passing at release)" | `pytest -q -p no:cacheprovider -rs` in `plugins/vibe-check/scripts` on the edited tree: `4126 passed` | kept (filled from the run) |
| Except 1: unreadable state file, stop sentence alone, no "Permission denied" line; stop and one retry unchanged | 63-RESULT L133, decision item 1; 63-EQUIVALENCE L132; `test_finalize_inputs.py::TestCliStderrParity::test_named_difference_unreadable_state` | kept |
| Except 2: name with `$`, backtick, `"`, `\` or line break stops before scoring with one "Review halted" line | `phases/review/00-scope.md` L93; `05-state.md` L12, L25; `05-state-all.md` L23; 63-RESULT L204 (D-21); `test_pasted_name_guard.py` | kept |
| Except 3: empty GSD phase id stops with one "Review halted" line; a pre-release 2.15 build could share one file; fixed before release, never shipped | `05-state.md` L9; 65-REPRO-WR02.md "## Fix" (b281042) and Walk B (pre-fix `wrong-file`); 2.14.1 failed closed (65-REPRO-WR02 Verdict); `TestStateFileGuard` `gsd empty-id`/`gsd unset-id`, `TestRepro63::test_wr02_empty_phase_id` | kept; worded as a fix, not a limit |
| Except 4: on C / POSIX / C.UTF-8 locales a non-UTF-8 state file is refused with `state is not valid JSON` instead of `malformed state`; refusal and stop unchanged | 63-RESULT L146 item 4; `carry_state.py` L196 `REASON_STATE_JSON`; `test_finalize_inputs.py::TestCliStderrParity::test_named_difference_non_utf8_state_under_c_locale` | reworded: first draft omitted the locale condition |
| Except 5: each fingerprint git call has a 60-second limit; slower → file left out, finding stays open | `finalize_inputs.py` L138 `GIT_TIMEOUT = 60`, `_git` returns None on `TimeoutExpired`; `90-finalize.md` L19 (a file that fails a check is left out, its fix-obsolete verdict closes nothing); 63-RESULT D-27 | kept |
| Except 6: from a subfolder, a file with unsaved or staged edits is no longer fingerprinted, so "fix obsolete" no longer closes on changed code | `finalize_inputs.py` L96-L104 (D-19, `--show-prefix` lift); 63-RESULT D-19 | kept |
| Except 7: inline Python runs isolated; a planted `json.py` no longer runs; hole present in 2.14.1 | 63-RESULT L206 (D-22, CR-01); `test_inline_python_isolated.py` | added (user-visible security difference not in the planned list; true and evidenced) |
| Size: Close out 136,114 → 131,381 bytes, 92 → 85 steps | Recount table above (`footprint.py`, `step_count.py` at d31787d vs dd8e4ab) | kept |
| Size: each review path +0.5% to +0.9% bytes, +2 counted steps; per path +1,705 / +1,717 / +1,954 / +1,966 / +1,869 bytes | Recount table above; attribution: 65-RESEARCH reconciliation (D-09 items X2/X3/X4-X6, D-20..D-23) plus 65-REPRO-WR02 "Named growth from the fix" (+495 bytes, 0 steps) | reworded: the plan's "+0.4% to +0.6%" came from the pre-fix code; the recount gives +0.54% to +0.89% |
| Size block uses bytes and steps only; no tokens or money words | `sed -n '/What changed in size/,/^$/p' README.md \| grep -Eic '\$\|token\|cheaper\|cost\|billing'` → 0 | kept |
| Limit: only default review and Close out in scope for a live check; others tests only; release notes say how it went | 65-LIVE-SMOKE-PROPOSAL.md `Status: APPROVED (owner, 2026-11-16)`; 65-CONTEXT D-02 | kept (APPROVED wording) |
| Limit: git call slower than 60 s leaves the file out; each `--finalize` run fingerprints again from scratch | `finalize_inputs.py` L138, L160-L168; docstring "always rebuilt from the current HEAD, index and working tree" | reworded from "run again once git responds" to the evidenced rebuild fact |
| Limit: helper failure shows "…finalize_gate.py failed…" with no detail recorded | `90-finalize.md` L24 (exit 4); `finalize_inputs.py` exit 4 = gate stage or internal failure, git stderr dropped; ROADMAP 999.38 WR-04 | kept |
| Limit: unsafe-name stop covers `$`, backtick, `"`, `\`, line break only; `;`, `&`, `'` pass; safe only while every pasted name stays double-quoted | ROADMAP 999.38 WR-03; 63-RESULT L222 | reworded to the record's "safe only while" (first draft asserted every command quotes them) |
| Limit: 2.15.0 → 2.14.1 downgrade untested; no saved-progress field added (`carry_state.py`, `score.py` unchanged) | `git diff --quiet v2.14.1 HEAD -- …/carry_state.py …/score.py` exit 0; only new non-test script is `finalize_inputs.py`, which writes only `--blob-out` | kept as "no effect is expected" (untested) |
| Relabels: v2.14.1 "(previous release)"; "(previous release)" removed from v2.13 | Ordering only; `grep -c "this release)"` = 1, `grep -c "previous release)"` = 1 | kept |
| Untouched test-coupled text: "every later run that reviews changes"; git-guard boundary sentence | `test_recovery_pairs.py`, `test_gitguard.py`: 185 passed on the edited tree | kept unchanged |
