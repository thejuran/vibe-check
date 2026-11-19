# Phase 66 deferred items

- (found during 66-11, out of scope) `plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_a2_pair_sits_on_adjacent_lines_of_one_statement` fails on a full `scripts/` run: `('architecture', 233) not found in []`. It replays the recorded corpus `runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1` through `score.py`. Plan 66-11 does not touch it (`score.py` is byte-identical to d5acc19; test_replay imports none of the files 66-11 edits). Not fixed.

> Orchestrator note (2026-11-19): not reproducible on the main checkout. After merging 66-11 (98446eb0) the full `scripts/` suite ran 4305 passed, 0 failed, including `test_replay.py`. The 5 failures were specific to the executor worktree; no action needed.
