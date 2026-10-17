# Live check: fix-harness clean-tree runs (default-diff + GSD) on the freeze candidate

Requirement: R4 / D-27 live checks for the finalize workflow change. Both runs go through the real finalize path with the shared freeze identity check active (R7, D-12, D-13). Run by 54-10 re-run #6 on 2026-10-17.

This replaces the record for candidate `2a6dbb4874b7…`, which is kept unchanged in `evidence/superseded-2a6dbb4874b7/live-harness-clean-tree.md`. Earlier records are in `evidence/superseded-24c0c00038f2/` and `evidence/superseded-302df48e1097/`. The 22ef678 re-run wrote no record here: its default run FAILED on the harness turn-end classifier, and both of its runs are kept as attempt records in `evidence/attempts/` (8954c62).

The plugin is unchanged since 2a6dbb4, apart from `lanearchive.py` (follow-up 2d), which no review prose uses. What changed under this check is the harness itself. Follow-up 2e makes a turn end count as `review-written` only when the run's `.turingmind/REVIEW.md` exists, so a sentence promising a later `--finalize` write no longer blocks the `--finalize` follow-up.

## Result

Both runs ended **COMPLETE**, and both launched on the frozen model.

| run | mode | entry | verdict | manifest_id | model | undecided_nv at close | archived state |
|---|---|---|---|---|---|---|---|
| clean-default | default | finalize (`/vibe-check:review --finalize`) | COMPLETE, reasons [] | fd1d0d916fe2… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/repo-main.json.archived-2026-10-17` |
| clean-gsd | gsd | review (`/vibe-check:review 52-harness-case`) | COMPLETE, reasons [] | fd1d0d916fe2… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/52-harness-case.json.archived-2026-10-17` |

**The default run is the second attempt on this candidate.** The first attempt's session lost its login in turn 2: its result text was `Failed to authenticate: OAuth session expired and could not be refreshed`, and no review ran in that turn. The coordinator ruled it an invalid environment attempt, not a D-15 verdict. It is kept, not counted, in `evidence/attempts/harness-clean-default-ddbfff402816-auth-expired/` (c85e3b8). The default run was then run once more.

That second attempt ran before the Task 1 and Task 2 evidence commits, as an early check before the owner's holdout proof. It used the same command, candidate and draft manifest as this task. Every commit after it was reporting-only (the candidate guard printed OK), so it is recorded here as the Task 3 default run and was not run a third time.

## Candidate and draft manifest

- candidate (from `evidence/CANDIDATE.json`): `ddbfff402816805136e95393c98a3cc17196daeb`
- candidate guard immediately before each run started:
  - default: `CANDIDATE OK candidate=ddbfff402816805136e95393c98a3cc17196daeb head=c85e3b8810ce170344b5d901be7399a2ec31f35d descendant_commits=5 (reporting-only)`;
  - gsd: `CANDIDATE OK candidate=ddbfff402816805136e95393c98a3cc17196daeb head=ad9fa43d23d1f5997e50db786bdd5f9563a3ee94 descendant_commits=8 (reporting-only)`.

  The same check printed OK again after both runs, before this record was committed.
- draft manifest (pre-freeze evidence only, NOT the series `FREEZE-MANIFEST-<N>.json`; `active_manifest` never picks it up). It was regenerated at the start of re-run #6, in commit 9a2c634:
  - the 22ef678 draft was confirmed byte-identical to `evidence/superseded-22ef678fb884/FREEZE-MANIFEST-draft-54-10.json` (`cmp`) and removed with plain `rm` (`generate` refuses to overwrite);
  - `env -u CLAUDECODE PYTHONDONTWRITEBYTECODE=1 python3 docs/design/freeze-v2.12/tools/freeze_manifest.py generate --candidate ddbfff402816805136e95393c98a3cc17196daeb --out docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` printed `wrote … (manifest_id fd1d0d916fe27de81f3c697673bbce65e6ab2c201a653e49875f0d6218cc81d3)`, exit 0;
  - the shell carried the 9 `env` values of `~/.claude/settings.json`, each checked equal before generating (settings.json was not modified);
  - `verify-self --manifest docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` printed `verify-self ok`, exit 0.
- draft `candidate_sha` = ddbfff402816805136e95393c98a3cc17196daeb (equals CANDIDATE.json)
- draft `runners.fix-harness.launch_model` = `{"source": "probe-record", "value": "claude-opus-5-5[1m]"}`

## Probe record (confirmed, not regenerated)

Before each run, the 54-07 Task 3 verify one-liner was re-run with the macOS realpath correction (`t = os.path.realpath(t)`), plus the sdk 0.2.165 assert. It printed:
`probe record current; model = claude-opus-5-5[1m] ; fingerprint = a3b4bfe03c1603dd9c9f265599a233dd704473959d4b1c28bc60a0f124fb2765`, exit 0. All 37 `PROBE_REQUIRED_CHECKS` were true.
`probe-sandbox` was NOT run. `git status --porcelain docs/design/fix-harness/fixtures/probe` was empty before and after the runs.

## Covered-tree hygiene before the runs

- `find docs/design plugins -name .ruff_cache -o -name .mypy_cache` was empty before each run.
- Ignored entries in the covered kit folders, other than `__pycache__`/`.pytest_cache` (which the check skips):
  - `docs/design/fix-harness/.venv/`;
  - `plugins/vibe-check/.planning/`.

  Both were present in the earlier runs too. The plugin is snapshotted from the candidate commit, not the working tree.

## Commands

These were run from the repository root with the harness venv python, one command per run:

```
H=docs/design/fix-harness
M=docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json
PYTHONDONTWRITEBYTECODE=1 $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode default --kind clean --out <scratchpad>/54-10r6/clean-default-2 --manifest $M
PYTHONDONTWRITEBYTECODE=1 $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode gsd --kind clean --out <scratchpad>/54-10r6/clean-gsd --manifest $M
```

`--candidate` was omitted, so it defaults to the manifest's `candidate_sha` (ddbfff4…). Each run printed its identity line before launching its session:

- default: `fixharness: identity manifest_id=fd1d0d916fe27de81f3c697673bbce65e6ab2c201a653e49875f0d6218cc81d3 check_digest=2dcb29bfc3b2652824031c4c940b8f07fd73428451a974025b07994a0911463a candidate_sha=ddbfff402816805136e95393c98a3cc17196daeb`
- gsd: `fixharness: identity manifest_id=fd1d0d916fe27de81f3c697673bbce65e6ab2c201a653e49875f0d6218cc81d3 check_digest=0f100a05e995bb3e577e6378d3f16591e800cc376a378d325c68c5c9e24d4f0d candidate_sha=ddbfff402816805136e95393c98a3cc17196daeb`

Both commands exited 0.

## Run records (from each `<out>/run.json`)

### clean-default

- verdict: `COMPLETE`, reasons `[]`; entry `finalize`; prompt `/vibe-check:review --finalize`
- manifest_id: `fd1d0d916fe27de81f3c697673bbce65e6ab2c201a653e49875f0d6218cc81d3` (= draft)
- check_digest: `2dcb29bfc3b2652824031c4c940b8f07fd73428451a974025b07994a0911463a`
- candidate_sha / plugin_sha: `ddbfff402816805136e95393c98a3cc17196daeb`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft `runners.fix-harness.launch_model.value`); cli_version 2.1.294
- containment: sandbox_enabled true, fail_if_unavailable true, denials 0, protected_path_denials 0, unsandboxed_retry false, probe_fingerprint a3b4bfe0…
- clean_tree_checkpoint: passed (status empty)
- decisions: cards 1, questions 2, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 2
- obligations: tracked 1, resolved 1, decided 0, fix_verified 0, regression 0, missing 0, ambiguous 0, downgraded 0, visible_open_nonblocking 0, snapshots 6
- execution_seconds: 401.558 (automated execution time)
- turn ends:
  - Turn 1 ended on the `No issues to fix.` one-liner plus "No `.turingmind/REVIEW.md` has been written yet… running `/vibe-check:review --finalize` again should write it". It classified as `no-issues`, and the harness sent `--finalize`.
  - Turn 2 ended on the written-report text with `.turingmind/REVIEW.md` on disk. It classified as `review-written` → done.
- archived state: `<copy>/.turingmind/state/format-53/repo-main.json.archived-2026-10-17`. The live `repo-main.json` was moved by the archive, so it is absent.
  - passes: pass 1 had 1 finding. Pass 2 had 0 findings and resolved 1 (`944e454c9310`, agent `bugs`).
  - `finalize-counts` on the archive (candidate `carry_state.py`): `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`, `confirmed_fix_awaiting_recheck_hashes []`.
  - The in-session gate inputs in the transcript show `undecided_nv` with a value 4 times, always 0.
- REVIEW.md: `review-closed` exit 0 (`{"closed": true}`); the `**State format:** 53` stamp is present.
- copy repo: one `fix(review-pass-2): …` commit on top of `introduce clamp`; `git status --short` empty.

### clean-gsd

- verdict: `COMPLETE`, reasons `[]`; entry `review`; prompt `/vibe-check:review 52-harness-case`; phase_id `52-harness-case`
- manifest_id: `fd1d0d916fe27de81f3c697673bbce65e6ab2c201a653e49875f0d6218cc81d3` (= draft)
- check_digest: `0f100a05e995bb3e577e6378d3f16591e800cc376a378d325c68c5c9e24d4f0d`
- candidate_sha / plugin_sha: `ddbfff402816805136e95393c98a3cc17196daeb`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft launch model); cli_version 2.1.294
- containment: sandbox_enabled true, fail_if_unavailable true, denials 0, protected_path_denials 0, unsandboxed_retry false
- clean_tree_checkpoint: passed
- decisions: cards 1, questions 1, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 1
- obligations: tracked 1, resolved 1, decided 0, fix_verified 0, regression 0, missing 0, ambiguous 0, downgraded 0, visible_open_nonblocking 0, snapshots 6
- execution_seconds: 383.174
- archived state: `<copy>/.turingmind/state/format-53/52-harness-case.json.archived-2026-10-17`
  - passes: pass 1 had 1 finding. Pass 2 (carry-forward) had 1 finding. Pass 3 had 0 findings and resolved 1 (`944e454c9310`, agent `bugs`).
  - `finalize-counts` on the archive: `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`, `confirmed_fix_awaiting_recheck_hashes []`.
  - The in-session gate inputs show `undecided_nv` with a value 2 times, always 0.
- REVIEW.md: `review-closed` exit 0; the stamp is present.
- copy repo: one `fix(review-pass-2): …` commit on top of `introduce clamp` and `docs: plan 52-harness-case`; `git status --short` empty.

## Identity check: allowlisted environment keys compared (names only)

The `runners.fix-harness.env` projection in the draft compares these 16 keys against `session_env(os.environ)`:
ANTHROPIC_BASE_URL, ANTHROPIC_DEFAULT_FABLE_MODEL, ANTHROPIC_DEFAULT_HAIKU_MODEL, ANTHROPIC_DEFAULT_OPUS_MODEL, ANTHROPIC_DEFAULT_SONNET_MODEL, ANTHROPIC_MODEL, CLAUDE_CODE_DISABLE_1M_CONTEXT, CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK, CLAUDE_CODE_EFFORT_LEVEL, CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY, CLAUDE_CODE_MAX_OUTPUT_TOKENS, CLAUDE_CODE_SUBAGENT_MODEL, DISABLE_AUTOUPDATER, DISABLE_UPDATES, ENABLE_TOOL_SEARCH, VIBE_CHECK_TOP_MODEL.

## Retained decisions and NV handling (D-27)

In both runs the seeded finding was **fixed**, and a re-check by `bugs` then resolved it. It was never dismissed or deferred, so neither archived state has root `decisions` or `fix_verdicts`, and there was no decision with a reason to preserve. **Neither fixture run produced a Needs-verification row.** The confirmed-fix path (54-16) was therefore not reached either: `confirmed_fix_awaiting_recheck_hashes` is empty in both runs.

What these runs prove live is the gate side: `undecided_nv` is 0 at COMPLETE, and APPROVED is written only after the gate returns `write`. Tests prove the rest:

- NV handling: `TestFormat53State` in `docs/design/fix-harness/tools/test_harness_verdict.py`. Its tests are `test_nv_row_is_deferred_through_the_real_finalize_card`, `test_undecided_nv_at_finalize_fails` and `test_mutant_nv_count_zero_certifies_a_false_close_out`.
- The confirmed-fix closure: `TestFinalizeCountsConfirmedFix` and `TestIndependentRecheck` in `plugins/vibe-check/scripts/test_confirmed_fix.py`.

## Comparison with the earlier clean-tree runs

The last live clean-tree runs before Phase 54 are Phase 52's (`docs/design/fix-harness/runs/phase52/RUNS.md`, plugin `b4f7212`). Phase 53 ran no clean-tree harness run.

| run | Phase 52 | 2a6dbb4 (54-10 re-run #4) | 22ef678 (re-run #5, attempts/) | ddbfff4 candidate (this run) | changed? |
|---|---|---|---|---|---|
| C-D / clean-default | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 288.9 s | COMPLETE; same counts; 324.7 s | FAILED: harness turn-end classifier (two-kind match), owner_commands 0 | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 401.6 s (second attempt; the first was an invalid auth-expired attempt) | no (same outcome and owner-burden counts as Phase 52 and 2a6dbb4) |
| C-G / clean-gsd | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 307.4 s | COMPLETE; same counts; 465.5 s | COMPLETE; same counts; 387.3 s | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 383.2 s | no (same outcome and counts) |

Execution time is reported for context only. It is not a gated measure.
