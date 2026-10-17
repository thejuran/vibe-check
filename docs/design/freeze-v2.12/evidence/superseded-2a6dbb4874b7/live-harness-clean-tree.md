# Live check: fix-harness clean-tree runs (default-diff + GSD) on the freeze candidate

Requirement: R4 / D-27 live checks for the finalize workflow change. Both runs go through the real finalize path with the shared freeze identity check active (R7, D-12, D-13). Run by 54-10 re-run #4 on 2026-10-17.

This replaces the record for the superseded candidate `24c0c00038f2…`, which is kept unchanged in `evidence/superseded-24c0c00038f2/live-harness-clean-tree.md`. The first run's record, with the `.ruff_cache` refusal found there, is in `evidence/superseded-302df48e1097/`.

The 535f488 and 14808a9 re-runs stopped before this step. This run is the first harness run on the batched-fix plugin. That fix changed the finalize counts (`carry_state.py`: `confirmed_fix_awaiting_recheck_hashes`), the archive fences and `review_archive.py`, and the state/dispatch prose.

## Result

Both runs ended **COMPLETE**. The identity check passed against the draft manifest on the first attempt, and both runs launched on the frozen model.

| run | mode | entry | verdict | manifest_id | model | undecided_nv at close | archived state |
|---|---|---|---|---|---|---|---|
| clean-default | default | finalize (`/vibe-check:review --finalize`) | COMPLETE, reasons [] | 3491dd4c5712… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/repo-main.json.archived-2026-10-17` |
| clean-gsd | gsd | review (`/vibe-check:review 52-harness-case`) | COMPLETE, reasons [] | 3491dd4c5712… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/52-harness-case.json.archived-2026-10-17` |

## Candidate and draft manifest

- candidate (from `evidence/CANDIDATE.json`): `2a6dbb4874b7521b66d53b2fbb1406dfb46dc230`
- candidate guard immediately before the runs started:
  `CANDIDATE OK candidate=2a6dbb4874b7521b66d53b2fbb1406dfb46dc230 head=e14f6c96c81bcd58ca052d27e228c7da9084e126 descendant_commits=7 (reporting-only)`
  The same check printed OK again after both runs, before this record was committed.
- draft manifest (pre-freeze evidence only, NOT the series `FREEZE-MANIFEST-<N>.json`; `active_manifest` never picks it up). It was regenerated at the start of re-run #4, in commit 539cae2:
  - the 14808a9 draft was confirmed byte-identical to `evidence/superseded-14808a961d02/FREEZE-MANIFEST-draft-54-10.json` (`cmp`) and removed with plain `rm` (`generate` refuses to overwrite);
  - `env -u CLAUDECODE PYTHONDONTWRITEBYTECODE=1 python3 docs/design/freeze-v2.12/tools/freeze_manifest.py generate --candidate 2a6dbb4874b7521b66d53b2fbb1406dfb46dc230 --out docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` printed `wrote … (manifest_id 3491dd4c5712c8badbedc251e8bb29b08c651c07a4eeb22bc8747ed1108290bc)`, exit 0;
  - the shell carried the 9 `env` values of `~/.claude/settings.json`, each checked equal before generating (settings.json was not modified);
  - `verify-self --manifest docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` printed `verify-self ok`, exit 0.
- draft `candidate_sha` = 2a6dbb4874b7521b66d53b2fbb1406dfb46dc230 (equals CANDIDATE.json)
- draft `runners.fix-harness.launch_model` = `{"source": "probe-record", "value": "claude-opus-5-5[1m]"}`

## Probe record (confirmed, not regenerated)

The 54-07 Task 3 verify one-liner was re-run with the macOS realpath correction (`t = os.path.realpath(t)`), plus asserts for `PROBE_REQUIRED_CHECKS` and sdk 0.2.165. It printed:
`probe record current; model = claude-opus-5-5[1m] ; fingerprint = a3b4bfe03c1603dd9c9f265599a233dd704473959d4b1c28bc60a0f124fb2765`, exit 0.
`probe-sandbox` was NOT run. `git status --porcelain docs/design/fix-harness/fixtures/probe` was empty before and after the runs.

## Covered-tree hygiene before the runs

- `find docs/design plugins -name .ruff_cache -o -name .mypy_cache` was empty.
- Ignored entries in the covered kit folders, other than `__pycache__`/`.pytest_cache` (which the check skips):
  - `docs/design/fix-harness/.venv/`;
  - `plugins/vibe-check/.planning/`.

  Both were present in the 24c0c00 run as well. The plugin is snapshotted from the candidate commit, not the working tree.

## Commands

These were run from the repository root with the harness venv python, started one after the other by one background shell:

```
H=docs/design/fix-harness
M=docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json
env -u CLAUDECODE PYTHONDONTWRITEBYTECODE=1 $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode default --kind clean --out <scratchpad>/54-10r4/clean-default --manifest $M
env -u CLAUDECODE PYTHONDONTWRITEBYTECODE=1 $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode gsd --kind clean --out <scratchpad>/54-10r4/clean-gsd --manifest $M
```

`--candidate` was omitted, so it defaults to the manifest's `candidate_sha` (2a6dbb4…). On the first attempt, each run printed this line before launching its session:
`fixharness: identity manifest_id=3491dd4c5712c8badbedc251e8bb29b08c651c07a4eeb22bc8747ed1108290bc check_digest=134eb24b6396a6f715ac317c6136f7d8690f000596036a56c3a022f9f2030787 candidate_sha=2a6dbb4874b7521b66d53b2fbb1406dfb46dc230`
Both commands exited 0.

## Run records (from each `<out>/run.json`)

### clean-default

- verdict: `COMPLETE`, reasons `[]`; entry `finalize`; prompt `/vibe-check:review --finalize`
- manifest_id: `3491dd4c5712c8badbedc251e8bb29b08c651c07a4eeb22bc8747ed1108290bc` (= draft)
- check_digest: `134eb24b6396a6f715ac317c6136f7d8690f000596036a56c3a022f9f2030787`
- candidate_sha / plugin_sha: `2a6dbb4874b7521b66d53b2fbb1406dfb46dc230`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft `runners.fix-harness.launch_model.value`); cli_version 2.1.294
- containment: sandbox_enabled true, fail_if_unavailable true, denials 0, protected_path_denials 0, unsandboxed_retry false, probe_fingerprint a3b4bfe0…
- clean_tree_checkpoint: passed (status empty)
- decisions: cards 1, questions 2, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 2
- obligations: tracked 1, resolved 1, decided 0, fix_verified 0, regression 0, missing 0, ambiguous 0, downgraded 0, visible_open_nonblocking 0, snapshots 6
- execution_seconds: 324.718 (automated execution time)
- archived state: `<copy>/.turingmind/state/format-53/repo-main.json.archived-2026-10-17`. The live `repo-main.json` was moved by the archive, so it is absent.
  - passes: pass 1 had 1 finding. Pass 2 had 0 findings and resolved 1 (`944e454c9310`, agent `bugs`).
  - `finalize-counts` on the archive (candidate `carry_state.py`): `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`, `confirmed_fix_awaiting_recheck_hashes []`.
  - The in-session gate inputs in the transcript show `undecided_nv` with a value 3 times, always 0.
- REVIEW.md: `review-closed` exit 0 (`{"closed": true}`); the `**State format:** 53` stamp is present.
- copy repo: one `fix(review-pass-2): …` commit on top of `introduce clamp`; `git status --short` empty.

### clean-gsd

- verdict: `COMPLETE`, reasons `[]`; entry `review`; prompt `/vibe-check:review 52-harness-case`; phase_id `52-harness-case`
- manifest_id: `3491dd4c5712c8badbedc251e8bb29b08c651c07a4eeb22bc8747ed1108290bc` (= draft)
- check_digest: `134eb24b6396a6f715ac317c6136f7d8690f000596036a56c3a022f9f2030787`
- candidate_sha / plugin_sha: `2a6dbb4874b7521b66d53b2fbb1406dfb46dc230`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft launch model); cli_version 2.1.294
- containment: sandbox_enabled true, fail_if_unavailable true, denials 0, protected_path_denials 0, unsandboxed_retry false
- clean_tree_checkpoint: passed
- decisions: cards 1, questions 1, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 1
- obligations: tracked 1, resolved 1, decided 0, fix_verified 0, regression 0, missing 0, ambiguous 0, downgraded 0, visible_open_nonblocking 0, snapshots 6
- execution_seconds: 465.489
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

| run | Phase 52 | superseded 24c0c00 (54-10 re-run) | 2a6dbb4 candidate (this run) | changed? |
|---|---|---|---|---|
| C-D / clean-default | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 288.9 s | COMPLETE; same counts; 457.7 s | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 324.7 s | no (same outcome and owner-burden counts on the batched-fix plugin) |
| C-G / clean-gsd | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 307.4 s | COMPLETE; same counts; 366.9 s | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 465.5 s | no (same outcome and counts) |

Execution time is reported for context only. It is not a gated measure.
