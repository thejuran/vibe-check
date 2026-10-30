---
phase: 60-exact-change-evidence-and-reliable-finalize
plan: 02
subsystem: vibe-check change evidence (range builder)
tags: [marker-walk, exact-ranges, D-01, D-02, mutation-tested, EVID-01, EVID-02]
requires:
  - "60-01 RealDiffRepo / _builder() lazy import / TestRealDiffRanges60 red fixtures (RED SHA ce9f8b8)"
provides:
  - "plugins/vibe-check/scripts/diff_ranges.py: ranges_from_diff(text) -> {path: [[s,e],...]}, RangeError, REASON_* + REASONS, run(argv, stdin_bytes) -> int, __main__ shim"
  - "CLI: git diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ <base> | python3 diff_ranges.py (exit 0 JSON sort_keys; exit 2 reason on stderr, empty stdout; any argv -> 2)"
  - "test_diff_ranges.py: TestShapesRealGit, TestHazards, TestRefusals, TestCli, TestImportLock, TestReplayPin, TestMutants (19 mutants)"
  - "TestRealDiffRanges60 green at 53fb637 (the green SHA for 60-05's ledger)"
affects: [60-04, 60-05]
tech-stack:
  added: []
  patterns: ["budget-driven hunk body consumption", "token-swap mutants that rerun a named test against an exec'd module copy via a `dr` attribute"]
key-files:
  created:
    - plugins/vibe-check/scripts/diff_ranges.py
    - plugins/vibe-check/scripts/test_diff_ranges.py
  modified: []
decisions:
  - "Green SHA for TestRealDiffRanges60 is 53fb637 (no edit to test_decision_continuity.py)"
  - "A zero-count new side (`+T,0`, -U0 only) is numbered by the line before it, so the walk cursor starts at T+1; the research reference algorithm missed this"
  - "C-quoted `+++ \"b/...\"` paths contribute no ranges (research A5): such names can never carry a finding"
  - "Body lines left over directly after a hunk's budgets are spent refuse with REASON_LONG_BODY (otherwise an extra trailing line would be silently ignored)"
metrics:
  duration: "~10 min"
  completed: 2026-10-29
  tasks: 2
  files: 2
requirements: [EVID-01, EVID-02]
---

# Phase 60 Plan 02: Exact-range builder Summary

`diff_ranges.py` builds changed-line ranges from each hunk's `+` and `-` markers. The header supplies only the first new-side line and the body's line budgets. Pure deletions get `[max(T,1), T+1]`. A net-deletion replace also covers the line after it (D-02). Structurally bad input is refused with a fixed reason. Real `git diff` output gives identical ranges at default context, `-U0` and `-U10`. All ten 60-01 real-chain boundary fixtures now pass. Each of the 19 guards has a mutant that makes a named test fail.

## Green SHA

**`53fb637`** (`feat(60-02): exact changed-line ranges from diff markers`). At that commit `test_decision_continuity.py -k TestRealDiffRanges60` gives 10 passed. That file was not edited.

## Tasks

| # | Task | Commit |
|---|------|--------|
| 1 | test_diff_ranges.py contract tests (RED: `No module named 'diff_ranges'` at collection) | `617075f` |
| 2 | diff_ranges.py + TestMutants; 60-01 fixtures green | `53fb637` |

## Verification (observed)

- Task 1 RED: `pytest -q test_diff_ranges.py` gave `E ModuleNotFoundError: No module named 'diff_ranges'`, `1 error during collection`, and no other error. 35 `def test_` (needed ≥25). `format-patch` occurs 2 times. `@@ -2,12 +2,12 @@` occurs once. `mnemonicPrefix` occurs once and `hunk_ranges` 3 times. A grep for hand-typed `From <40hex>` lines found none.
- `pytest -q test_diff_ranges.py` → `57 passed, 56 subtests passed` (needed ≥31)
- `pytest -q test_decision_continuity.py -k "TestRealDiffRanges60 or TestRepro60Evidence or TestRepro60Record"` → `17 passed, 47 subtests passed`
- Import set printed `['json', 're', 'sys']`
- `printf '' | python3 diff_ranges.py` printed `{}` and exited `rc=0`. `python3 diff_ranges.py --help </dev/null` printed nothing to stdout and exited `rc=2`.
- `splitlines`=0, `except:`=0, `except Exception`=0 in diff_ranges.py
- `git diff --stat -- test_decision_continuity.py replay.py score.py` is empty
- Full suite (`pytest -q` from scripts/): `5 failed, 3722 passed, 4908 subtests passed in 173.24s`. The 5 failures are the four `TestCoordinateSpaces60` probes (60-04's) and `TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report` (60-03's). That leaves exactly the 60-01 red set minus the ten range-builder tests.

## Mutants (each one first passes the named test on the real module, then fails it on the swapped module)

| # | Guard removed | Named test it trips |
|---|---------------|---------------------|
| M1 | marker walk → header counts | `TestShapesRealGit.test_delete_one_line` (also: synthetic default "delete 9" gives `[[6,11]]`) |
| M2 | D-02 `deleted > added` extension | `test_net_deletion_replace_extends_one_line` (direct: `[[10,10]]` vs `[[10,11]]`) |
| M3 | budget consumption (body stops at `+++ `) | `TestHazards.test_content_lines_that_look_like_file_headers` |
| M4 | mbox refusal | `TestRefusals.test_refuses_commit_series` |
| M5 | `split("\n")` → `splitlines()` | `test_form_feed_and_line_separator_do_not_desync` |
| M6 | pure deletion `[s-1, s]` → `[s, s]` | `test_delete_one_line` |
| M7 | zero-count new-side cursor | `test_delete_one_line` (-U0 subtest) |
| M8 | combined `@@@` refusal | `test_refuses_combined_diff` |
| M9 | short-body refusal | `test_refuses_short_body` |
| M10 | in-walk budget overflow refusal | `test_refuses_extra_deleted_line_inside_budget` |
| M11 | leftover-body-line refusal | `test_refuses_long_body` |
| M12 | bad-body-line refusal | `test_refuses_unexpected_body_line` |
| M13 | `\` marker skip inside body | `test_no_newline_marker_consumes_no_budget` |
| M14 | `\` marker skip after a hunk | `test_refuses_long_body_after_no_newline_marker` |
| M15 | trailing-tab strip | `test_path_with_space_trailing_tab` |
| M16 | quoted-path skip | `test_quoted_path_is_skipped` |
| M17 | `/dev/null` → no path | `test_deleted_file_has_no_key` |
| M18 | merge of touching ranges | `test_adjacent_blocks_merge` |
| M19 | sorted keys | `test_two_files_both_keys_sorted` (reordered real input) |

Each mutant's anchor is asserted to occur exactly once in the source. A refactor that moves the anchor makes the mutant test fail instead of silently doing nothing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A `-U0` pure deletion was off by one**
- **Found during:** Task 2 (first green run: 5 `-U0` subtests failed)
- **Issue:** When the new side is empty, git numbers it by the line *before* the deletion: `@@ -9 +8,0 @@` follows line 8. The reference algorithm in research started the cursor at `new_start` and so returned `[7,8]`. The default diff gives `[8,9]`, which broke the three-context equivalence.
- **Fix:** `cursor = new_start + 1 if new_count == 0 else new_start`. The docstring now records it, and mutant M7 covers it.
- **Cost if wrong:** Low. The real-git shape table pins `[[8,9]]`, `[[9,10]]`, `[[1,1]]` and `[[28,29]]` under all three contexts.
- **Files modified:** plugins/vibe-check/scripts/diff_ranges.py
- **Commit:** 53fb637

**2. [Rule 1 - Bug] The empty piece after the final newline was read as a body line**
- **Found during:** Task 2 (`test_refuses_short_body` got REASON_BAD_BODY_LINE)
- **Issue:** `text.split("\n")` on newline-terminated text leaves a trailing `""`. A truncated body then read that `""` as a bad body line instead of hitting end of input.
- **Fix:** `_split_lines` drops the one trailing empty piece. An empty line in the middle of a body is still refused.
- **Cost if wrong:** Low. A truncated body would give the wrong reason, but it would still be refused.
- **Commit:** 53fb637

**3. [Rule 2 - Correctness] Lines left over after a hunk refuse with REASON_LONG_BODY**
- **Found during:** Task 2
- **Issue:** Budget overflow only raises while the other budget is still open. An extra `+` line after both budgets reach 0 went to the outer loop and was silently ignored, so the plan's long-body fixture would not have refused.
- **Fix:** The line directly after a completed hunk is checked, skipping `\` markers. If it starts with `+`, `-` or a space and is not a `+++ `/`--- ` header, the input is refused. Mutants M11 and M14 cover this check.
- **Cost if wrong:** If some real producer emits such a line between hunks, the review halts with "hunk body longer than its header" (fail closed). Git and gh do not emit one.
- **Commit:** 53fb637

**4. [Rule 2 - Correctness] C-quoted paths are skipped instead of being keyed by quoted text**
- **Found during:** Task 1 (hazard design)
- **Issue:** The plan's `_file_path` spec has no quote handling. Without it, `+++ "b/\303\251.txt"` becomes a junk key that includes the quotes.
- **Fix:** A path starting with `"` → None, which contributes no ranges (research A5: such names never carry a finding). Covered by `test_quoted_path_is_skipped` (real git, `é.txt`) and mutant M16.
- **Cost if wrong:** If findings could ever sit on non-ASCII paths, those files would lose their in-diff bonus. Today PATH_RE excludes them.
- **Commit:** 617075f, 53fb637

**5. [Rule 2 - No decorative locks] 13 mutants beyond the six the plan listed, plus 3 supporting tests**
- **Found during:** Task 2
- **Issue:** The plan's must-have is "every guard in the builder has a mutant". Its six named mutants left nine guards untested: combined, short/long/bad body, `\` handling, tab, quote, `/dev/null`, merge, sort, and the M7 cursor fix.
- **Fix:** Added M7 to M19, plus `test_adjacent_blocks_merge`, `test_refuses_extra_deleted_line_inside_budget` and `test_refuses_long_body_after_no_newline_marker`, so that those guards have a test to trip.
- **Cost if wrong:** None. These are extra tests.
- **Commit:** 53fb637

**6. [Executor rule - no process metadata in product code] The replay pin docstring describes behavior, not a phase number**
- **Found during:** Task 1
- **Issue:** The plan asked the pin docstring to say "Phase 61's replay gate depends on it".
- **Fix:** The docstring now explains the dependency itself: replay rebuilds envelopes of recorded runs whose ranges were read from headers with context, and the replay gate compares against those recordings. It does not name a phase.
- **Cost if wrong:** None.
- **Commit:** 617075f

## Assumption Drift (advisory)

- **Found during:** Task 2
- **Planned:** The 60-RESEARCH.md "Builder core" reference algorithm is a correct starting shape. Its note says the pure-deletion `blk_s` "equals `[max(T,1), T+1]`".
- **Actual:** That holds for context diffs only. Under `-U0` the zero-count header shifts the cursor by one (deviation 1). The 60-01 prototype that proved the fixtures satisfiable must have handled this, but the research text does not.
- **Why:** git's unified-diff convention for an empty range.
- **Cost if wrong:** If 60-04 copies the research snippet into prose or anywhere else, it reintroduces the bug. 60-04 should call `diff_ranges.py` and not re-derive it.

## Known Stubs

None.

## Threat Flags

None. The threat register's mitigations are in place. T-60-04: budget-driven consumption, the hazard test and M3. T-60-05: the mbox refusal and M4. T-60-06: reasons are only the fixed constants, and `_refusal` asserts each reason is in REASONS and does not contain the path. T-60-08: the import lock is `{json, re, sys}`, with no `os`/`subprocess`/`open`/`exec` names. The module adds no new I/O surface; it reads stdin and writes stdout/stderr only.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/diff_ranges.py
- FOUND: plugins/vibe-check/scripts/test_diff_ranges.py
- FOUND commits: 617075f, 53fb637
