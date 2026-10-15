# Live check: fix-harness clean-tree runs (default-diff + GSD) on the freeze candidate

Requirement: R4 / D-27 live checks for the finalize workflow change. Both runs go through the real finalize path with the shared freeze identity check active (R7, D-12, D-13). Run by the 54-10 re-run on 2026-10-15.

This replaces the record for the superseded candidate `302df48e1097…`, which is kept unchanged in `evidence/superseded-302df48e1097/live-harness-clean-tree.md`. That record also documents the `.ruff_cache` refusal found on the first attempt there.

## Result

Both runs ended **COMPLETE**, and the identity check passed against the regenerated draft manifest on the first attempt. Both runs launched on the frozen model.

| run | mode | entry | verdict | manifest_id | model | undecided_nv at close | archived state |
|---|---|---|---|---|---|---|---|
| clean-default | default | finalize (`/vibe-check:review --finalize`) | COMPLETE, reasons [] | 98af8754d5ae… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/repo-main.json.archived-2026-10-15` |
| clean-gsd | gsd | review (`/vibe-check:review 52-harness-case`) | COMPLETE, reasons [] | 98af8754d5ae… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/52-harness-case.json.archived-2026-10-15` |

## Candidate and draft manifest

- candidate (from `evidence/CANDIDATE.json`): `24c0c00038f2d15af4b55f178ea44e680c1f2c58`
- candidate guard before the manifest was generated and the runs started:
  `CANDIDATE OK candidate=24c0c00038f2d15af4b55f178ea44e680c1f2c58 head=c3f3114260c7d2c81bc787f9de63db4173151541 descendant_commits=4 (reporting-only)`
  The same line printed again after both runs, before this record was committed.
- draft manifest. It is pre-freeze evidence only and NOT the series `FREEZE-MANIFEST-<N>.json`; `active_manifest` never picks it up:
  - `generate` refuses to overwrite an existing path. The 302df48 draft at this path was byte-identical to its copy in `evidence/superseded-302df48e1097/` (checked with `cmp`), so it was removed from the plan path and the new draft was generated there.
  - `env -u CLAUDECODE PYTHONDONTWRITEBYTECODE=1 python3 docs/design/freeze-v2.12/tools/freeze_manifest.py generate --candidate 24c0c00038f2d15af4b55f178ea44e680c1f2c58 --out docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`
    printed `wrote … (manifest_id 98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99)`, exit 0. No `--allow-missing-runner-settings` was used.
  - It was generated from the same shell environment the harness runs inherit, with `CLAUDECODE` stripped as the harness launch line strips it.
  - `python3 docs/design/freeze-v2.12/tools/freeze_manifest.py verify-self --manifest docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` printed `verify-self ok`, exit 0.
  - draft `candidate_sha` = 24c0c00038f2d15af4b55f178ea44e680c1f2c58 (equals CANDIDATE.json); lineage null/null (pre-series draft)
  - draft `runners.fix-harness.launch_model` = `{"source": "probe-record", "value": "claude-opus-5-5[1m]"}`
- Changes from the superseded draft (b6abbae38b9c…), compared key by key. All of them are expected from the 24c0c00 fix:
  - `candidate_sha`, `candidate_tree`, `generated_at`, `manifest_id`
  - the six covered freeze-kit files the fix touched (`README.md`, `freeze_check.py`, `freeze_common.py`, `freeze_manifest.py`, `test_freeze_check.py`, `test_freeze_common.py`) and the two tree hashes over them
  - the `.in_use` effect: `tree_sha256` of the 7 enabled plugins in `runners.b3` and `runners.holdout-eval`, `runners.b3.gateway.tree_sha256` and `codex.companion.tree_sha256`. These hashes no longer include the owner sessions' `.in_use/<pid>` markers.
  - Nothing else changed. The fix-harness profile, env projection, launch models, CLI versions and plugin file set are identical.

## Probe record (confirmed, not regenerated)

The 54-07 Task 3 verify one-liner was re-run with the 54-07 macOS realpath correction (`t = os.path.realpath(t)`), plus asserts for `PROBE_REQUIRED_CHECKS` and sdk 0.2.165. It printed:
`probe record current; model = claude-opus-5-5[1m] ; fingerprint = a3b4bfe03c1603dd9c9f265599a233dd704473959d4b1c28bc60a0f124fb2765`, exit 0.
`probe-sandbox` was NOT run. `git status --porcelain docs/design/fix-harness/fixtures/probe` was empty before and after the runs.

## Covered-tree hygiene before the runs

`git status --porcelain --ignored docs plugins` showed no tool caches in covered folders except `__pycache__/` and `.pytest_cache/`, which the check skips. No `.ruff_cache` or `.mypy_cache` was found (`find docs/design plugins -name .ruff_cache -o -name .mypy_cache` was empty before and after). The 302df48 run's moved `.ruff_cache` stays in the session scratchpad. The Python one-liners in this run used `PYTHONDONTWRITEBYTECODE=1`.

## Commands

From the repository root, with the harness venv python. The two runs were started sequentially by one background shell:

```
H=docs/design/fix-harness
M=docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json
env -u CLAUDECODE PYTHONDONTWRITEBYTECODE=1 $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode default --kind clean --out <scratchpad>/54-10r/clean-default --manifest $M
env -u CLAUDECODE PYTHONDONTWRITEBYTECODE=1 $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode gsd --kind clean --out <scratchpad>/54-10r/clean-gsd --manifest $M
```

`--candidate` was omitted, so it defaults to the manifest's `candidate_sha` (24c0c00…). Each run printed the line below before launching the session, on the first attempt:
`fixharness: identity manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 check_digest=9950e131764b517456f38a31c765888913aaa52b45d04fdb7948f6b9b04c346a candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58`
Both commands exited 0.

## Run records (from each `<out>/run.json`)

### clean-default

- verdict: `COMPLETE`, reasons `[]`; entry `finalize`; prompt `/vibe-check:review --finalize`
- manifest_id: `98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99` (= draft)
- check_digest: `9950e131764b517456f38a31c765888913aaa52b45d04fdb7948f6b9b04c346a`
- candidate_sha / plugin_sha: `24c0c00038f2d15af4b55f178ea44e680c1f2c58`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft `runners.fix-harness.launch_model.value`); cli_version 2.1.294
- containment: sandbox_enabled true, fail_if_unavailable true, denials 0, protected_path_denials 0, unsandboxed_retry false, probe_fingerprint a3b4bfe0…
- clean_tree_checkpoint: passed (status empty)
- decisions: cards 1, questions 2, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 2
- obligations: tracked 1, resolved 1, decided 0, fix_verified 0, regression 0, missing 0, ambiguous 0, downgraded 0, visible_open_nonblocking 0, snapshots 6
- execution_seconds: 457.692 (automated execution time)
- archived state: `<copy>/.turingmind/state/format-53/repo-main.json.archived-2026-10-15`. The archive moved the live `repo-main.json`, so it is absent.
  - passes: pass 1 had 1 finding. Pass 2 had 0 findings and resolved 1 (`944e454c9310`, agent `bugs`).
  - `finalize-counts` on the archive (candidate `carry_state.py`): `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`. The in-session gate inputs in the transcript show `"undecided_nv": 0` (4 occurrences, no other value).
- REVIEW.md: `review-closed` exit 0 (`{"closed": true}`), `**State format:** 53` stamp present
- copy repo: one `fix(review-pass-2): …` commit on top of `introduce clamp`; `git status --short` empty

### clean-gsd

- verdict: `COMPLETE`, reasons `[]`; entry `review`; prompt `/vibe-check:review 52-harness-case`; phase_id `52-harness-case`
- manifest_id: `98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99` (= draft)
- check_digest: `9950e131764b517456f38a31c765888913aaa52b45d04fdb7948f6b9b04c346a`
- candidate_sha / plugin_sha: `24c0c00038f2d15af4b55f178ea44e680c1f2c58`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft launch model); cli_version 2.1.294
- containment: sandbox_enabled true, fail_if_unavailable true, denials 0, protected_path_denials 0, unsandboxed_retry false
- clean_tree_checkpoint: passed
- decisions: cards 1, questions 1, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 1
- obligations: tracked 1, resolved 1, decided 0, fix_verified 0, regression 0, missing 0, ambiguous 0, downgraded 0, visible_open_nonblocking 0, snapshots 6
- execution_seconds: 366.947
- archived state: `<copy>/.turingmind/state/format-53/52-harness-case.json.archived-2026-10-15`
  - passes: pass 1 had 1 finding. Pass 2 (carry-forward) had 1 finding. Pass 3 had 0 findings and resolved 1 (`944e454c9310`, agent `bugs`).
  - `finalize-counts` on the archive: `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`. The in-session gate inputs in the transcript show `"undecided_nv": 0` (2 occurrences, no other value).
- REVIEW.md: `review-closed` exit 0, stamp present
- copy repo: one `fix(review-pass-2): …` commit on top of `introduce clamp` and `docs: plan 52-harness-case`; `git status --short` empty

## Identity check: allowlisted environment keys compared (names only)

The `runners.fix-harness.env` projection in the draft compares these keys against `session_env(os.environ)`:
ANTHROPIC_BASE_URL, ANTHROPIC_DEFAULT_FABLE_MODEL, ANTHROPIC_DEFAULT_HAIKU_MODEL, ANTHROPIC_DEFAULT_OPUS_MODEL, ANTHROPIC_DEFAULT_SONNET_MODEL, ANTHROPIC_MODEL, CLAUDE_CODE_DISABLE_1M_CONTEXT, CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK, CLAUDE_CODE_EFFORT_LEVEL, CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY, CLAUDE_CODE_MAX_OUTPUT_TOKENS, CLAUDE_CODE_SUBAGENT_MODEL, DISABLE_AUTOUPDATER, DISABLE_UPDATES, ENABLE_TOOL_SEARCH, VIBE_CHECK_TOP_MODEL.

## Retained decisions and NV handling (D-27)

In both runs the seeded finding was **fixed**, and a recheck by `bugs` then resolved it. It was never dismissed or deferred, so root `decisions` is absent in both archived states, and there was no decision with a reason to preserve. **Neither fixture run produced a Needs-verification row.** What these runs prove live is the gate side: `undecided_nv` is 0 at COMPLETE, and APPROVED is written only after the gate returns `write`. The NV-handling proof is `TestFormat53State` in `docs/design/fix-harness/tools/test_harness_verdict.py`: an NV row deferred with a reason through the real finalize card, and a close-out refused while an NV item is undecided. The tests are `test_nv_row_is_deferred_through_the_real_finalize_card`, `test_undecided_nv_at_finalize_fails` and `test_mutant_nv_count_zero_certifies_a_false_close_out`.

## Comparison with the earlier clean-tree runs

The last live clean-tree runs before Phase 54 are Phase 52's (`docs/design/fix-harness/runs/phase52/RUNS.md`, plugin `b4f7212`). Phase 53 ran no clean-tree harness run.

| run | Phase 52 | superseded 302df48 (54-10 first run) | 24c0c00 candidate (this run) | changed? |
|---|---|---|---|---|
| C-D / clean-default | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 288.9 s | COMPLETE; same counts; 307.7 s | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 457.7 s | no (same outcome and owner-burden counts; now under the identity check, format-53 state path, no-clobber archive) |
| C-G / clean-gsd | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 307.4 s | COMPLETE; same counts; 440.4 s | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 366.9 s | no (same outcome and counts) |

Execution time is reported for context only. It is not a gated measure.
