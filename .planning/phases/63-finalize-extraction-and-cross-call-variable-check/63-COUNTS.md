# Phase 63 — Finalize counts

This file holds the before and after figures for the Phase 62 criterion: how many steps the model runs and how many bytes it loads on the Finalize path, taken straight from the commits with the counting tools, plus the checks that the 2.14.1 baseline records are still intact.

## Before

Recorded 2026-11-14. Every figure below was printed by the tools at the named commit (D-13); the two weak Phase 62 checks were not relied on.

2.14.1 (`dd8e4ab`, tag `v2.14.1`):

- steps (rule v1), Finalize path, dd8e4ab: 92
- steps (rule v1), 90-finalize.md alone, dd8e4ab: 68
- bytes, Finalize path, dd8e4ab: 136114

Branch commit (`2a468a8`, "docs(63): begin phase execution"):

- steps (rule v1), Finalize path, 2a468a8: 92
- steps (rule v1), 90-finalize.md alone, 2a468a8: 68
- bytes, Finalize path, 2a468a8: 136114

Checks:

- instruction files unchanged since 2.14.1: yes (`git diff --quiet dd8e4ab HEAD -- plugins/vibe-check/phases` exited 0)
- finalize capture verify: `finalize baseline matches (5 situations)`
- baseline records verify: `baseline holds`
- baseline record fingerprints: 10 of 10 match MANIFEST.json (sha256 of each file named in MANIFEST.json `files`, computed and compared directly)
- full suite (`pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`): `5 failed, 4329 passed, 1 skipped, 5306 subtests passed in 274.62s (0:04:34)` — the 5 failures are all in `test_replay.py::TestPhase53SameLineRegressionCases` (`test_pre_same_line_scorer_gave_critical_100` ×2, `test_off_line_credit_mutation_trips` ×2, `test_a2_pair_sits_on_adjacent_lines_of_one_statement`); they fail at this commit with no change made and touch none of the Finalize files (see `deferred-items.md`)
- Finalize tests (`test_finalize_card.py test_finalize_gate.py test_finalize_archive_prose.py`): `174 passed, 208 subtests passed`

Commands used:

```
python3 docs/design/lean-v2.15/tools/step_count.py --rev <sha> --json      # totals.model_run_steps; files[].model_run_steps for phases/shared/90-finalize.md
python3 plugins/vibe-check/scripts/footprint.py --rev <sha> --json          # finalize.bytes
python3 docs/design/lean-v2.15/tools/finalize_capture.py verify --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json
python3 docs/design/lean-v2.15/tools/baseline_records.py verify --repo .
```

## After the extraction alone (commit c7d92c9)

Verdict (extraction alone): PASS

- steps (rule v1), Finalize path: 92 → 83
- steps (rule v1), 90-finalize.md alone: 68 → 59
- bytes, Finalize path: 136114 → 129451

Recorded 2026-11-15 at `c7d92c93f319a5685c4e8fe999089f259744cf74` ("docs(phase-63): update tracking after wave 6"), which holds plans 63-01 to 63-08 and no cross-call fix. The six files ordinary reviews also load (`commands/review.md`, `phases/shared/00-contract.md`, `phases/shared/01-bootstrap.md`, `phases/review/00-scope.md`, `05-state.md`, `06-config.md`) are byte-identical to `dd8e4ab` at this commit (`git diff --quiet dd8e4ab c7d92c9 -- <six files>` exited 0). Every figure below was printed in this task by `step_count.py --rev <sha> --json` and `footprint.py --rev <sha> --json` at the two commits; none is copied from an earlier summary. Pass rule (Phase 62 D-01/D-02): steps 83 ≤ 92 and bytes 129451 ≤ 136114, both strictly lower, and the same-behaviour checks below hold.

| File on the Finalize path | steps dd8e4ab | steps c7d92c9 | bytes dd8e4ab | bytes c7d92c9 |
|---------------------------|---------------|---------------|---------------|---------------|
| commands/review.md | 1 | 1 | 16724 | 16724 |
| phases/shared/00-contract.md | 0 | 0 | 3811 | 3811 |
| phases/shared/01-bootstrap.md | 1 | 1 | 4621 | 4621 |
| phases/review/00-scope.md | 10 | 10 | 20088 | 20088 |
| phases/review/05-state.md | 7 | 7 | 19484 | 19484 |
| phases/review/06-config.md | 5 | 5 | 15463 | 15463 |
| phases/shared/90-finalize.md | 68 | 59 | 55923 | 49260 |
| **Total** | **92** | **83** | **136114** | **129451** |

What went away, all in `90-finalize.md`, from the tool's JSON: Bash blocks 18 → 14 (4 fewer), Write-tool writes 7 → 5 (2 fewer), copied paths 38 → 35 (3 fewer); commands run inline stay at 5. The printed names drop from 11 to 10 (`GATEFILE` is gone). The per-file git and path-guard calls the model used to run for each finding's file were never counted by rule v1 (they sat inside a loop in one Bash block), and they are also gone: the helper runs them now. The plain and deep review paths are unchanged at this commit: review-plain 192057 → 192057 bytes, deep-plain 268997 → 268997 bytes (`footprint.py`).

### Maintenance added (labelled; does not decide pass or fail)

From `git diff --numstat ff8ab99 c7d92c9` (`ff8ab99` = `git merge-base main HEAD`) and the files at `c7d92c9`:

- `plugins/vibe-check/scripts/finalize_inputs.py` (new helper): 391 lines, 15092 bytes
- `plugins/vibe-check/scripts/test_finalize_inputs.py` (new tests): 1841 lines, 83451 bytes
- `docs/design/lean-v2.15/tools/finalize_capture.py`: +635 / −12 lines
- `docs/design/lean-v2.15/tools/test_finalize_capture.py`: +486 / −0 lines
- the three Finalize test files: `test_finalize_card.py` +806 / −576 (net +230); `test_finalize_gate.py` and `test_finalize_archive_prose.py` unchanged; net +230 lines
- other re-pointed tests: `test_carry_state.py` +45/−6, `test_score.py` +42/−28, `test_confirmed_fix.py` +37/−8, `test_diff_ranges.py` +17/−12, `test_decision_continuity.py` +5/−4, `test_pause_batching.py` +4/−2, `.github/scripts/test_stdlib_only.py` +2/−2 (module count 33 → 34)
- design document `docs/design/lean-v2.15/finalize-counts-explained.md` (moved text, not loaded during a review): +14 lines; `docs/design/lean-v2.15/README.md` +1/−1
- separately, the cross-call check (not part of the extraction): `plugins/vibe-check/scripts/test_cross_call_vars.py`, 1195 lines, 51398 bytes

### Same behaviour

- five Finalize situations, `finalize_capture.py compare --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json --driver helper --commit c7d92c9`: exit 0, last line `finalize outcome fields match (5 situations, 7 walks)`
- finalize capture verify: `finalize baseline matches (5 situations)`
- baseline records verify (`baseline_records.py verify --repo .`): `baseline holds`
- archived replay: `plugins/vibe-check/scripts/score.py` and `replay.py` are byte-identical to `dd8e4ab` (`git diff --quiet` exit 0 for each); the baseline kit's replay re-check for a candidate scripts directory (`baseline_records.py verify --repo . --scripts-dir plugins/vibe-check/scripts`, which re-derives the replay report from that directory and compares its fingerprint) exit 0: `baseline holds`
- baseline record fingerprints: 10 of 10 match MANIFEST.json (sha256 of each file named in MANIFEST.json `files`, computed and compared directly; D-13)
- full suite: not re-run by this plan's executor at `c7d92c9` (the run was assigned to the orchestrator). The orchestrator's run of the whole suite in the main checkout at `c7d92c9` reported `6478 passed, 0 failed`; that run used a wider command than the `## Before` line, so the two totals are not like for like. The last run with the `## Before` command (`pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`) is 63-07's, on the final instruction text: `5 failed, 4498 passed, 1 skipped, 5604 subtests passed`, against `5 failed, 4329 passed, 1 skipped, 5306 subtests passed` in `## Before`. The same 5 known worktree-only `test_replay.py::TestPhase53SameLineRegressionCases` failures appear in both; the passing count rose by 169, which is the new helper tests (`test_finalize_inputs.py`) and the cross-call check, less the removals. Per the removal ledger, of the 46 test rows touched: 14 kept as they are, 25 rewritten or re-pointed, 7 removed as no longer applying (there is no gate input file). 63-08 then added the `compare`/`HelperWalk` tests to `docs/design/lean-v2.15/tools` (that folder: 355 passed, 202 subtests passed).

### Extraction commits

The exact set a revert would undo, built by rule: every commit in `git log --oneline --reverse ff8ab99..c7d92c9` that changes at least one file outside `.planning/` other than `plugins/vibe-check/scripts/test_cross_call_vars.py`. Oldest first. No commit is mixed (none changes `test_cross_call_vars.py` together with another file outside `.planning/`). Merge commits change nothing of their own and are not listed.

63-01 (the helper's fingerprint half, its tests, the module-count lock 33 → 34; not the `## Before` record):
- `2de7214` test(63-01): add failing tests for Finalize HEAD fingerprints
- `78fbdeb` feat(63-01): add Finalize HEAD fingerprint helper

63-02 (the rest of the helper):
- `34fd96a` test(63-02): edited or staged file is not fingerprinted from a subfolder
- `4e6bfc5` fix(63-02): fingerprint checks read the file from the repo root
- `54bb2f9` test(63-02): add failing tests for the Finalize result
- `184c4b2` feat(63-02): assemble the Finalize result from the three helpers
- `9e518ea` test(63-02): add failing tests for the Finalize helper command line
- `73f3ef7` feat(63-02): Finalize helper command line with fixed exit codes

63-05 (the replacement tests, and the re-point commit for `test_carry_state.py` and `test_score.py`):
- `5f6474e` test(63-05): helper-level replacements for the Finalize text locks
- `45af0b3` test(63-05): re-point two locks off the Finalize instruction text

63-06 (the rewritten walks and locks, the re-pointed `test_diff_ranges.py`, `test_decision_continuity.py` and `test_confirmed_fix.py`, the instruction file):
- `36612af` test(63-06): Finalize walks and locks against the one-helper inputs block
- `41de3c5` test(63-06): re-point the diff-ranges walk and the noninteractive pin
- `e9dc275` test(63-06): re-point two hidden locks off the removed Finalize text
- `1ced383` feat(63-06): Finalize gate inputs run through one finalize_inputs.py call

63-07 (the design document, the instruction file, the re-pointed locks):
- `2414bad` test(63-07): lock the counts passage word for word in its design document
- `8d395f5` feat(63-07): move the "What the helper counts" explanation to a design document
- `59feb98` test(63-07): report data from the Finalize-inputs result; report line stays on screen
- `c337e63` feat(63-07): REVIEW.md fill reads the report data from the Finalize-inputs result

63-08 (`HelperWalk`, `compare`, `TestHelperWalk` and the README row under `docs/design/lean-v2.15/`):
- `e149bb0` test(63-08): the five Finalize situations driven on the new instructions
- `e119633` feat(63-08): HelperWalk drives the five Finalize situations on the new instructions
- `36fb368` test(63-08): compare, the like-for-like 2.14.1 run and the refusal lines
- `f8f655e` feat(63-08): compare the new instructions with the 2.14.1 Finalize record

mixed — cannot be reverted whole: none.

### What stays after a revert

- The 63-03 and 63-04 commits (the cross-call check and its reproductions; they touch `test_cross_call_vars.py` only): `9d5e2f9`, `cb7c8b0`, `1fda4cc`, `f2c34f0`, `7a520bb`, `2aa59df`, `c34bad8`, `9efb67d`.
- Every phase record under `.planning/`, kept as history.
- Later, the 63-10 cross-call fixes.

Once the listed commits are reverted the tree must show: `plugins/vibe-check/phases/shared/90-finalize.md`, `test_carry_state.py`, `test_score.py`, every other test module those commits touched (`test_finalize_card.py`, `test_confirmed_fix.py`, `test_diff_ranges.py`, `test_decision_continuity.py`, `test_pause_batching.py`, `.github/scripts/test_stdlib_only.py`) and `docs/design/lean-v2.15/tools/` plus `docs/design/lean-v2.15/README.md` equal to the branch base `ff8ab99`; no `finalize_inputs.py`, no `test_finalize_inputs.py`, no `finalize-counts-explained.md`; and the module count back at 33.
