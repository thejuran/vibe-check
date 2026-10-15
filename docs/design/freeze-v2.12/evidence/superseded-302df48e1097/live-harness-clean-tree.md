# Live check: fix-harness clean-tree runs (default-diff + GSD) on the freeze candidate

Requirement: R4 / D-27 live checks for the finalize workflow change. Both runs go through the real finalize path with the shared freeze identity check active (R7, D-12, D-13). Run by 54-10 on 2026-10-15.

## Result

Both runs ended **COMPLETE**, with the identity check passing against the draft manifest. They are the first live proof that the fix-harness profile in the manifest matches a real environment, and that the harness launches on the frozen model.

| run | mode | entry | verdict | manifest_id | model | undecided_nv at close | archived state |
|---|---|---|---|---|---|---|---|
| clean-default | default | finalize (`/vibe-check:review --finalize`) | COMPLETE, reasons [] | b6abbae38b9c… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/repo-main.json.archived-2026-10-15` |
| clean-gsd | gsd | review (`/vibe-check:review 52-harness-case`) | COMPLETE, reasons [] | b6abbae38b9c… | claude-opus-5-5[1m] | 0 | `.turingmind/state/format-53/52-harness-case.json.archived-2026-10-15` |

## Candidate and draft manifest

- candidate (from `evidence/CANDIDATE.json`): `302df48e1097212aa334a21c8f2683ed810eb496`
- candidate guard before the runs:
  `CANDIDATE OK candidate=302df48e1097212aa334a21c8f2683ed810eb496 head=f1ba53557db61bd999e8c398d354164a12125018 descendant_commits=3 (reporting-only)`
- draft manifest. It is pre-freeze evidence only and NOT the series `FREEZE-MANIFEST-<N>.json`; `active_manifest` never picks it up:
  - `env -u CLAUDECODE python3 docs/design/freeze-v2.12/tools/freeze_manifest.py generate --candidate 302df48e1097212aa334a21c8f2683ed810eb496 --out docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`
    printed `wrote … (manifest_id b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c)`, exit 0. No `--allow-missing-runner-settings` was used.
  - It was generated from the same shell environment the harness runs inherit, with `CLAUDECODE` stripped as the harness launch line strips it (54-05 note: the manifest stores the generating process's environment).
  - `python3 docs/design/freeze-v2.12/tools/freeze_manifest.py verify-self --manifest docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` printed `verify-self ok`, exit 0.
  - draft `candidate_sha` = 302df48e1097212aa334a21c8f2683ed810eb496 (equals CANDIDATE.json)
  - draft `runners.fix-harness.launch_model` = `{"source": "probe-record", "value": "claude-opus-5-5[1m]"}`

## Probe record (confirmed, not regenerated)

The 54-07 Task 3 verify one-liner was re-run with the 54-07 macOS realpath correction (`t = os.path.realpath(t)`). It printed:
`probe record current; model = claude-opus-5-5[1m] ; fingerprint = a3b4bfe03c1603dd9c9f265599a233dd704473959d4b1c28bc60a0f124fb2765`, exit 0.
The record has `passed: true` and sdk 0.2.165, and it carries no `manifest_id`. `probe-sandbox` was NOT run. `git status --porcelain docs/design/fix-harness/fixtures/probe` was empty before and after the runs.

## Commands

From the repository root, one command per run, with the harness venv python:

```
H=docs/design/fix-harness
env -u CLAUDECODE $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode default --kind clean --out <scratchpad>/54-10/clean-default --manifest docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json
env -u CLAUDECODE $H/.venv/bin/python $H/tools/fixharness.py run --case py-clamp-01 --mode gsd --kind clean --out <scratchpad>/54-10/clean-gsd --manifest docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json
```

`--candidate` was omitted, so it defaults to the manifest's `candidate_sha` (302df48e…). Each run printed the line below before launching the session:
`fixharness: identity manifest_id=b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c check_digest=5c54debde83863703395dfb82e0d08e85be5295fb2f181ef0570d98d91c2433d candidate_sha=302df48e1097212aa334a21c8f2683ed810eb496`

## First attempt: identity check refused the launch (environment finding, no code change)

The first default-mode attempt (before any session started) exited 2 in preflight:

```
fixharness: preflight: freeze identity mismatch: file extra: fix-harness/tools/.ruff_cache/.gitignore
fixharness: preflight: freeze identity mismatch: file extra: fix-harness/tools/.ruff_cache/0.15.9/4919283520380371691
fixharness: preflight: freeze identity mismatch: file extra: fix-harness/tools/.ruff_cache/CACHEDIR.TAG
```

- **Cause:** a gitignored ruff lint cache (dated 2026-10-09/10) in the working-tree copy of the covered fix-harness kit. The kit check compares the live directory against the committed tree. `freeze_common.live_files` excludes only `__pycache__`, `.pytest_cache`, `.in_use` and `*.pyc`, so any other local file counts as extra.
- **Judgment:** the check worked as designed. Failing closed on an unknown file in a measured kit is the intended behavior, since an excluded-dirs list wide enough to hide caches could also hide a planted file. So this is environment hygiene, not a kit defect, and no covered file was changed.
- **Action:** the cache directory was moved out of the kit to the session scratchpad (not deleted). The draft manifest was NOT regenerated, because the manifest itself was correct. The run was then started again. No session had launched, so this is not a rerun of a FAILED verdict (D-15).
- **Carry for 54-11/54-14 and Phase 55:** keep lint and tool caches (`.ruff_cache`, `.mypy_cache`, …) out of covered kit trees before any identity-checked run, or the check will refuse the launch. A scan of the covered trees at this point found no other stray files beyond `__pycache__` / `.pytest_cache`, the gitignored harness `.venv` (outside the kit tree it compares), run transcripts under reporting roots, and `plugins/vibe-check/.planning/`. That last one is ignored by git and is not in the candidate-commit snapshot the harness measures, but a runner that measures a working-tree plugin copy would see it.

## Run records (from each `<out>/run.json`)

### clean-default

- verdict: `COMPLETE`, reasons `[]`; entry `finalize`; prompt `/vibe-check:review --finalize`
- manifest_id: `b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c` (= draft)
- check_digest: `5c54debde83863703395dfb82e0d08e85be5295fb2f181ef0570d98d91c2433d`
- candidate_sha / plugin_sha: `302df48e1097212aa334a21c8f2683ed810eb496`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft `runners.fix-harness.launch_model.value`); cli_version 2.1.294
- containment: sandbox_enabled true, denials 0, protected_path_denials 0, unsandboxed_retry false, probe_fingerprint a3b4bfe0…
- clean_tree_checkpoint: passed (status empty)
- decisions: cards 1, questions 2, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 2
- obligations: tracked 1, resolved 1, decided 0, fix_verified 0, regression 0, missing 0, ambiguous 0, downgraded 0, visible_open_nonblocking 0, snapshots 6
- execution_seconds: 307.654 (automated execution time)
- archived state: `<copy>/.turingmind/state/format-53/repo-main.json.archived-2026-10-15`. The live `repo-main.json` was moved away by the archive, so it is absent.
  - passes: pass 1, 1 finding. Pass 2, 0 findings and 1 resolved (`944e454c9310`, source `recheck`, at_pass 2).
  - `finalize-counts` on the archive (candidate `carry_state.py`): `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`. The in-session gate inputs in the transcript also show `"undecided_nv": 0`.
- REVIEW.md: `review-closed` exit 0 (`{"closed": true}`), `**State format:** 53` stamp present
- copy repo: one `fix(review-pass-2): …` commit on top of `introduce clamp`; `git status --short` empty

### clean-gsd

- verdict: `COMPLETE`, reasons `[]`; entry `review`; prompt `/vibe-check:review 52-harness-case`; phase_id `52-harness-case`
- manifest_id: `b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c` (= draft)
- check_digest: `5c54debde83863703395dfb82e0d08e85be5295fb2f181ef0570d98d91c2433d`
- candidate_sha / plugin_sha: `302df48e1097212aa334a21c8f2683ed810eb496`; plugin_tree_dirty `false`
- model: `claude-opus-5-5[1m]` (= draft launch model); cli_version 2.1.294
- containment: sandbox_enabled true, denials 0, protected_path_denials 0, unsandboxed_retry false
- clean_tree_checkpoint: passed
- decisions: cards 1, questions 1, turn_end_questions 0, owner_commands 1, repeats 0, deferred_non_seeded 0
- would_be_owner_questions: 1
- obligations: tracked 1, resolved 1, decided 0, regression 0, missing 0, ambiguous 0, snapshots 6
- execution_seconds: 440.427
- archived state: `<copy>/.turingmind/state/format-53/52-harness-case.json.archived-2026-10-15`
  - passes: pass 1, 1 finding. Pass 2 (carry-forward), 1 finding. Pass 3, 0 findings and 1 resolved (`944e454c9310`, source `recheck`, at_pass 3).
  - `finalize-counts` on the archive: `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`. The in-session gate inputs in the transcript also show `"undecided_nv": 0`.
- REVIEW.md: `review-closed` exit 0, stamp present
- copy repo: one `fix(review-pass-2): …` commit; `git status --short` empty

## Identity check: allowlisted environment keys compared (names only)

The `runners.fix-harness.env` projection in the draft compares these keys against `session_env(os.environ)`:
ANTHROPIC_BASE_URL, ANTHROPIC_DEFAULT_FABLE_MODEL, ANTHROPIC_DEFAULT_HAIKU_MODEL, ANTHROPIC_DEFAULT_OPUS_MODEL, ANTHROPIC_DEFAULT_SONNET_MODEL, ANTHROPIC_MODEL, CLAUDE_CODE_DISABLE_1M_CONTEXT, CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK, CLAUDE_CODE_EFFORT_LEVEL, CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY, CLAUDE_CODE_MAX_OUTPUT_TOKENS, CLAUDE_CODE_SUBAGENT_MODEL, DISABLE_AUTOUPDATER, DISABLE_UPDATES, ENABLE_TOOL_SEARCH, VIBE_CHECK_TOP_MODEL.

## Retained decisions and NV handling (D-27)

In both runs the seeded finding was **fixed**, and a recheck by `bugs` then resolved it. It was never dismissed or deferred, so root `decisions` is absent in both archived states, and there was no decision with a reason to preserve. **Neither fixture run produced a Needs-verification row.** The live proof here is the gate side: `undecided_nv` is 0 at COMPLETE, and APPROVED is written only after the gate returns `write`. The NV-handling proof (an NV row deferred with a reason through the real finalize card, and a close-out refused while an NV item is undecided) is `TestFormat53State` in `docs/design/fix-harness/tools/test_harness_verdict.py`: `test_nv_row_is_deferred_through_the_real_finalize_card`, `test_undecided_nv_at_finalize_fails`, `test_mutant_nv_count_zero_certifies_a_false_close_out`.

## Comparison with the earlier clean-tree runs

The last live clean-tree runs are Phase 52's (`docs/design/fix-harness/runs/phase52/RUNS.md`, plugin `b4f7212`). Phase 53 ran no clean-tree harness run.

| run | Phase 52 | 54-10 candidate | changed? |
|---|---|---|---|
| C-D / clean-default | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 288.9 s | COMPLETE; cards 1, questions 2, owner_commands 1, would_be 2; 307.7 s | no (same outcome and owner-burden counts; now under the identity check, format-53 state path, no-clobber archive) |
| C-G / clean-gsd | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 307.4 s | COMPLETE; cards 1, questions 1, owner_commands 1, would_be 1; 440.4 s | no (same outcome and counts) |
