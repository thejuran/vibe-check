---
phase: 66-close-out-freshness
plan: 10
subsystem: review-helpers
tags: [999.44, shape-1, worktree-snap, removed-lines, gap-closure, tdd]
requires: []
provides:
  - "worktree_snap.removed_from_diff(text) — old-side removed lines from one unified diff"
  - "worktree_snap.since_both(root, prior, current) — (new-side ranges, old-side removed lines) from ONE git diff"
  - "worktree_snap collect third output line REMOVED_LINE_RANGES="
  - "test_worktree_snap.REMOVED_GRID — 13 named grid states with expected third line (reusable by 66-12)"
affects: [66-11 (step-0 prose consumes REMOVED_LINE_RANGES), 66-12]
tech-stack:
  added: []
  patterns: ["two-sided differential against literal d5acc19 blobs", "exact-once text-replacement mutants"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/worktree_snap.py
    - plugins/vibe-check/scripts/test_worktree_snap.py
decisions:
  - "Removed lines are parsed from the same since-review diff text as NEARBY_LINE_RANGES (no new git call, no new import); diff_ranges.py untouched"
  - "removed is \"\" exactly when nearby is \"\" (unknown is never printed as {})"
  - "removed_from_diff resets the old path on each `diff --` line and keys by the old-side (reviewed-side) path"
requirements: [FRESH-03]
metrics:
  completed: 2026-11-18
  tasks: 2
  commits: 3
---

# Phase 66 Plan 10: removed-since-review lines from worktree_snap collect Summary

`worktree_snap.py collect` now prints a third line, `REMOVED_LINE_RANGES=`, holding the reviewed-side (old-side) line numbers that the since-review diff deletes or replaces. It is parsed from the same single `git diff` as `NEARBY_LINE_RANGES=`, and it is empty whenever the evidence is unknown. The first two lines and the exit code are proven byte-identical to the literal 2.15.0 (d5acc19) helper on a 13-state grid.

## What changed

- `removed_from_diff(text)` walks each hunk body against the header's old and new budgets (the same walk as `diff_ranges._walk_hunk`) and records the old-side number of every `-` line under the `--- ` path. The `a/` prefix is stripped; `/dev/null` and C-quoted paths give no entry. A `\` line consumes nothing, and an empty body line counts as blank context. It raises `diff_ranges.RangeError` on a short or long body or an unknown tag. It reuses `diff_ranges._HUNK`, `_split_lines`, `_count` and `_merge`. Helpers: `_old_path` and `_walk_removed`.
- `since_both(root, prior, current)` returns `(ranges, removed)` from one `_git(... "diff", *DIFF_FLAGS, *ends, "--")` call. It keeps the same id checks and returns `({}, {})` with no git call when `current == prior`. A `RangeError` becomes `SnapUnavailable`. `since()` is now a wrapper that returns `since_both(...)[0]`, with the same signature and results.
- `collect` returns `(tree, nearby, removed, notes)`. Both JSON values use `separators=(",", ":"), sort_keys=True`. On the no-snapshot path, the code-moved path and the `except` path, all three values are `""`.
- `run` prints `REVIEWED_TREE=…\nNEARBY_LINE_RANGES=…\nREMOVED_LINE_RANGES=…\n`.
- The module docstring now says the call prints exactly three lines and describes the third: old-side numbers keyed by the reviewed-side path, `{}` for nothing removed, empty for unknown, the same single diff, used only by decided-record relocation and never sent to score.py.

## Tests (test_worktree_snap.py)

- **Harness:** `_Phases._keep_removed` keeps `collect_stdout` and `removed_printed`, which is None when the key is absent (the 2.15.0 shape). `collect_only` and `run_pass_fences` still return `(tree, nearby)`, so no caller changed. `TestCollectInternals` unpacks the new 4-tuple.
- **TestRemovedFromDiff** runs on real `git diff` text with `DIFF_FLAGS`. It covers every row of the feature table at default context, `-U0` and `-U10`: deleted, replaced, inserting 20 lines at the top, inserting one line between 9 and 10, deleting 10-12 plus 30, and inserting 20 at the top plus deleting old 30 (gives 30, not 50). It also covers a deleted file (`[[1, 60]]`), an added file (`{}`), the header look-alike lines (`--- a/other.py` / `+++ b/other.py` in the body give only `src/a.py: [[10, 10]]`) and an empty diff.
- **TestCollectRemoved** (`_Chain`, real prose fences) covers pass 1 (`""`), an identical tree (`{}`), line 38 deleted (`{"src/a.py":[[38,38]]}` with nearby `[[37,38]]`), ten lines inserted at the top (`{}`), and the unknown states (no `reviewed_tree`, an unknown tree id, an empty snapshot, an edit between take and collect), all of which print `""`. It also has `test_removed_empty_iff_nearby_empty` over the 9 default-route states and `test_cli_prints_exactly_three_lines_in_order`.
- **TestCollectRemovedRange / TestCollectRemovedPR** (`_CommittedChain`) check an unchanged end or head (`{}`), a new commit deleting line 38 (`[[38,38]]`), and a state without a snapshot (`""`).
- **TestCollectDifferentialV215** materializes `worktree_snap.py` and `diff_ranges.py` from `d5acc19:plugins/vibe-check/scripts/`, and `test_differential_materializer_is_literal_d5acc19` checks the blob ids. Each side runs its own `take` and `collect` as a subprocess with list argv, in two repos built the same way with fixed commit dates.
  - `test_differential_first_two_lines_identical_third_added`: on every `REMOVED_GRID` state the exit codes are equal, the candidate prints exactly 3 lines, its first 2 lines equal the d5acc19 stdout byte for byte, and the third line equals the expected value.
  - `test_differential_v215_prints_no_removed_line` checks that the 2.15.0 helper never prints the third line.
  - `test_differential_no_extra_git_call` checks that `collect` makes the same number of git calls in both modules on the deletion state.
- **REMOVED_GRID** (13 states): pass1_no_state `""`; identical_tree `{}`; edit_above `[[37,37]]`; line_38_deleted `[[38,38]]`; top_ten_inserted `{}`; state_without_reviewed_tree `""`; unknown_tree_id `""`; empty_snapshot `""`; edit_between_take_and_collect `""`; range_unchanged_end `{}`; range_commit_deletes_line `[[38,38]]`; pr_unchanged_head `{}`; pr_moved_head `[[43,43]]`.
- **TestRemovedMutants:** each mutant is one replacement that must occur exactly once in the source. Each test checks that the real module gives the expected value and the mutant does not.

| Mutant | Change | Observed mutant result | Named contract test that fails with the mutant applied in place |
|---|---|---|---|
| M1 | records `+` lines instead of `-` | `{}` on the line-10 deletion | `TestRemovedFromDiff::test_line_deleted` |
| M2 | numbers from the hunk's new-side start | `[[50, 50]]` on insert-20-plus-delete-30 | `TestRemovedFromDiff::test_old_side_numbers_after_an_insertion_above` |
| M3 | keys by the `+++ ` path | `{}` on the file deletion | `TestRemovedFromDiff::test_file_deleted` |
| M4 | reads a `--- ` body line as a header | `RangeError: hunk body shorter than its header` | `TestRemovedFromDiff::test_header_look_alike_body_lines` |
| M5 | `{}` for unknown evidence | removed `"{}"` with nearby `""` | `TestCollectRemoved::test_removed_empty_iff_nearby_empty` |

To get the last column, each mutant was applied in place to the real `worktree_snap.py` (scratch script, original bytes restored afterwards), and the named test was run and failed each time.

## Verification (observed)

- RED commit: the 67 existing tests passed. Every new TestRemovedFromDiff test or subtest failed with `AttributeError: … no attribute 'removed_from_diff'`. Every TestCollectRemoved* test or subtest failed because `REMOVED_LINE_RANGES` was None (the helper printed two lines). All 13 differential grid states failed on the line count. The materializer, the v215-prints-no-removed-line test and no-extra-git-call already passed. `worktree_snap.py` was untouched in that commit.
- After GREEN plus the mutants:
  - `pytest -q -p no:cacheprovider test_worktree_snap.py test_diff_ranges.py`: **218 passed, 179 subtests passed**
  - `test_worktree_snap.py` alone: 97 tests (92 after GREEN, plus 5 mutants)
- `pytest -q test_closeout_fresh.py test_diff_ranges.py test_finalize_inputs.py`: **340 passed, 911 subtests passed** (run after GREEN). `test_closeout_fresh.py -k "clearable or AllRoute"`: 10 passed.
- `git diff --quiet d5acc19 -- plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/diff_ranges.py`: exit 0.
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`: exit 0 (35 files, no third-party imports).
- No new `import` or `from` line in `worktree_snap.py` compared with d5acc19 (count 0).
- Evidence class: offline only. There was no live reviewer run.

## Deviations from Plan

**1. [Rule 3 - Blocking] Worktree base reset.** At spawn the worktree was on c1461c5e, an ancestor of the planned base, so it was reset to 65190000 as the startup check directs.
- **Cost if wrong:** none. The plan files exist only from 65190000 on.

**2. [Acceptance artefact] The class-count grep prints 5, not 3.** `grep -c "class TestRemovedFromDiff\|class TestCollectRemoved\|class TestCollectDifferentialV215"` also matches `TestCollectRemovedRange` and `TestCollectRemovedPR`. The names were kept so the plan's `-k "TestCollectRemoved"` selection includes the range and PR cases.
- **Cost if wrong:** a reviewer counting classes by grep sees 5. The three required classes exist.

**3. [Reporting note] pytest-subtests marks parent tests PASSED.** A test whose subtests all fail still shows PASSED for the parent. The RED run therefore showed "9 passed": 3 differential tests that should pass, plus 6 parents of failing subtests. Every subtest of TestRemovedFromDiff and TestCollectRemoved failed in RED.
- **Cost if wrong:** none. The failures are listed in the RED commit body.

**4. [Rule 2] `removed_from_diff` resets the path on every `diff --` line.** The plan did not ask for this. It stops a file without a `--- ` header (binary or mode-only) from inheriting the previous file's path.
- **Cost if wrong:** none observed. Git always prints `--- ` before hunks.

## Known Stubs

None.

## Threat Flags

None. The output adds only paths and line numbers (T-66-22 accepted). There is no new subprocess surface (T-66-23, checked by `test_differential_no_extra_git_call`).

## Commits

- 555510e5 test(66-10): removed-since-review output of worktree_snap collect — RED (999.44 shape 1 evidence)
- 8738c0c3 feat(66-10): worktree_snap collect reports reviewed-side lines removed since the review (999.44 shape 1)
- 0020fffa test(66-10): mutation checks for the removed-lines output

## TDD Gate Compliance

RED (`test(66-10)` 555510e5), then GREEN (`feat(66-10)` 8738c0c3), then the mutation-check `test` commit (0020fffa). No refactor commit was needed.

## Self-Check: PASSED

worktree_snap.py, test_worktree_snap.py and this SUMMARY exist; commits 555510e5, 8738c0c3 and 0020fffa are in git log.
