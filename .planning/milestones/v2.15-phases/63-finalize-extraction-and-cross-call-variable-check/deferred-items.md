# Deferred items — Phase 63

## Found during 63-01 (out of scope, not fixed)

- **`test_replay.py::TestPhase53SameLineRegressionCases` fails locally in a git worktree (5 failures).** `test_pre_same_line_scorer_gave_critical_100` and `test_off_line_credit_mutation_trips` (two runs each: `runs-v2.10-phase43/first/should-quiet-4/run-3`, `runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1`) get `('warning', 94)` where they expect `('critical', 100)`; `test_a2_pair_sits_on_adjacent_lines_of_one_statement` finds no architecture lane at line 233. Reproduced at the branch base `2a468a8` with no change made, inside the agent worktree `.claude/worktrees/agent-ab7beaa11da958a2b`. Phase 62 recorded CI green on main, so this looks environment-dependent (the old scorer is loaded from `blob:d4f9fb14…`, the worktree's object store or path may differ). None of the Finalize files are involved. Worth re-running in the main checkout before Phase 63 closes.
