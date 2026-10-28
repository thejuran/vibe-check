---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 11
subsystem: batch-card
tags: [d-19, sa-02, bottom-line, suggest, gap-closure]
requires: [58-10]
provides:
  - "batch_card.py suggest --rows R --answer S (D-19 trim of the Bottom line answer)"
  - "batch_card.suggest(rows_doc, answer) -> ((suggestion, dropped), None) | (None, reason)"
  - "REASON_SUGGEST_EMPTY, SUGGEST_TRIMMED"
affects: [58-15, 58-17]
tech-stack:
  added: []
  patterns: ["parse before and after trimming: the parser stays the only gate", "bulk-safety bands from batch_parse._rest_bands_for only"]
key-files:
  created:
    - plugins/vibe-check/scripts/test_bottom_line_suggest.py
  modified:
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/scripts/test_batch_card.py
    - plugins/vibe-check/scripts/test_answer_resolve.py
decisions:
  - "suggest keeps dismiss/defer only for bands batch_parse._rest_bands_for(verb) returns (medium only); fix keeps every band including needs-verification"
  - "A q2 reason is folded into q1 as ` -- reason`; the output always has q2 null"
  - "The reason is kept only when a dismiss/defer clause survives; a fix-only suggestion carries none"
metrics:
  duration: ~25m
  completed: 2026-10-27
  tasks: 3
  files: 4
requirements: [ANSR-01]
---

# Phase 58 Plan 11: Bottom line suggest helper (D-19) Summary

`batch_card.py suggest` takes the report's model-written Bottom line answer and trims it to what one typed "bottom line" may apply. `fix` keeps every row. `dismiss`/`defer` keep medium rows only, `rest`/`all` become explicit numbers, and the trimmed grammar is checked by `parse` again before it is printed. This closes SA-02: typing "bottom line" can no longer dismiss or defer a critical, warning or needs-verification row.

## What was built

- `suggest(rows_doc, answer)` in `batch_card.py`:
  1. `parse` the answer first. Its refusal (grammar, missing reason, range, malformed) is passed through unchanged.
  2. Map hashes to row numbers. `fix_targets` are all kept. For `dismiss`/`defer`, a row is kept only if its band is in `batch_parse._rest_bands_for(verb)`, the one bulk-safety source. Every other row goes into `dropped`, sorted and without duplicates.
  3. If no clause is left, refuse with `REASON_SUGGEST_EMPTY`. This covers all-dropped, NV-only and `look N`.
  4. Rebuild the grammar with `_grammar_for`. The reason is kept only when a dismiss/defer clause survives.
  5. Run `parse` again on `{"q1": grammar, "q2": null}`. If it refuses, that refusal is returned, so a grammar the gate would refuse is never printed.
- CLI: `suggest --rows PATH --answer PATH` prints `{"q1", "q2"}` only. When rows were dropped, it also writes one fixed stderr line: `suggestion trimmed: N serious row(s) dropped — dismiss or defer those in your own words`. That line has a count and no titles. The command reads no stdin and is not a state subcommand.

### CLI table diff

| Table | Before | After |
|---|---|---|
| `SUBCOMMANDS` | `(..., "decisions-report", "resolve")` | `(..., "decisions-report", "resolve", "suggest")` |
| `_FLAGS_BY_SUBCOMMAND` | no `suggest` | `"suggest": (("--rows", "--answer"), ())` |
| `USAGE` | `... \| resolve --rows PATH --answer PATH [--prior-rows PATH]` | `+ " \| suggest --rows PATH --answer PATH"` |
| `REASONS` | ends `REASON_PRIOR_NEEDED` | `+ REASON_SUGGEST_EMPTY` |
| `_STATE_SUBCOMMANDS` | `("rows", "payload", "decisions-report")` | unchanged |
| `KNOWN_FLAGS` | unchanged | unchanged |

The module docstring now lists `suggest` among the subcommands and in the CLI synopsis.

## RED (Task 1, commit aab19b2)

`pytest -q scripts/test_bottom_line_suggest.py scripts/test_batch_card.py -k "Suggest or sealed"` on HEAD before the fix gave **30 failed, 4 passed**. Every `TestSuggest*` behavior test failed with `AttributeError: module 'batch_card' has no attribute 'suggest'` / `REASON_SUGGEST_EMPTY`. The CLI tests failed with exit 2 and USAGE, because `suggest` was an unknown subcommand. `test_sealed_tuples` failed on the tuple mismatch.

Four tests passed on HEAD, as expected:
- `test_fixture_bands` checks the fixture, not the feature.
- `test_usage_refusals` holds both before and after, since an unknown subcommand also gets USAGE.
- `test_output_passes_parse_unchanged` and `test_parser_refusals_pass_through` passed as parent tests, but every one of their subtests failed.

## GREEN (Task 2, commit 4e1fe8a)

- `pytest -q scripts/test_bottom_line_suggest.py scripts/test_batch_card.py scripts/test_answer_resolve.py`: **190 passed, 169 subtests passed**
- Every test file that imports `batch_card` (10 files): **616 passed, 709 subtests passed**
- `python3 scripts/batch_card.py suggest` (no flags): prints USAGE only, exit 2
- `git diff --stat 24dccdc..HEAD -- batch_parse.py score.py`: empty
- No new imports in `batch_card.py`. The import allowlist still holds.

## Mutants (Task 3, commit 353a780)

Each mutant was applied to the real `batch_card.py` with the Edit tool and run with `pytest -q scripts/test_bottom_line_suggest.py`, then reverted with `git checkout --`. `git status --porcelain batch_card.py` was empty after each revert.

| Mutant | Edit to real file | Result | Failing tests (real file) |
|---|---|---|---|
| s1 band filter dropped | `bands = batch_parse._rest_bands_for(verb)` → `bands = batch_parse._BANDS` | 12 failed | `test_dismiss_critical_dropped`, `test_defer_warning_dropped`, `test_all_dropped_refuses`, `test_nv_row_dropped`, `test_output_passes_parse_unchanged[dismiss 1,2 / defer 4,8]`, `test_s1[real]`, `test_s2[real]`, CLI `test_prints_trimmed_object`, `test_all_dropped_exit_2_with_empty_reason`, `test_refusals...[all dropped]` |
| s2 empty refusal dropped | removed `if not clauses: return None, REASON_SUGGEST_EMPTY` | 6 failed | `test_all_dropped_refuses`, `test_look_only_refuses_empty`, `test_nv_row_dropped`, `test_s2[real]`, `test_s2[mutant]`, CLI `test_all_dropped_exit_2_with_empty_reason` |
| s3 final parse dry-run dropped | removed the post-trim `parse(rows_doc, suggestion)` + refusal return | 2 failed | `test_s3_final_dry_run_dropped[real]`, `[mutant]` |

Under s2 the post-trim `parse` still refuses the empty grammar, but with batch_parse's `REASON_EMPTY` instead of `REASON_SUGGEST_EMPTY`. So the fixed-reason contract is what catches it.

Under s3 nothing in normal input reaches a refused trimmed grammar. I probed odd q2 reasons (`--`, `a\nb`, `x -- y`, `; fix 1`) and every one re-parsed. That makes the dry-run defense in depth, and its lock uses a seam: `_grammar_for` is patched to emit a refused grammar.

The in-file lock tests `test_s1_*`, `test_s2_*` and `test_s3_*` show each mutant at the seam (`mock.patch`). `pytest -k "s1 or s2 or s3"`: **3 passed, 6 subtests passed**.

## Full suite

`pytest -q` from `plugins/vibe-check`: **3516 passed, 4664 subtests passed**. That is 3491 before plus 25 new.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_answer_resolve.py::TestResolveCli::test_sealed_tuples` pinned `resolve` as the LAST subcommand**
- **Found during:** Task 2 (GREEN run)
- **Issue:** `assertEqual(batch_card.SUBCOMMANDS[-1], "resolve")` fails once `suggest` is added after it, which the plan requires.
- **Fix:** changed it to `assertIn("resolve", batch_card.SUBCOMMANDS)`. The full ordered tuple is still pinned in `test_batch_card.py::test_sealed_tuples`, so the guard is no weaker.
- **Cost if wrong:** none in practice. Order is still locked by the other test.
- **Files modified:** plugins/vibe-check/scripts/test_answer_resolve.py
- **Commit:** 4e1fe8a

**2. [Rule 2 - Extra coverage] Tests beyond the listed behavior**
- Added `test_defer_warning_dropped`, `test_fix_rest_expanded_to_numbers`, `test_q2_reason_folded_into_grammar`, `test_nv_row_fix_kept`, `test_look_only_refuses_empty`, `test_untrimmed_has_quiet_stderr` and `test_output_file_is_a_valid_parse_answer`. The last one checks the `cp "$SUGGESTFILE" "$ANSWERFILE"` path end to end through the CLI.
- **Cost if wrong:** none. Tests only.

## Assumption Drift (advisory)

- **Found during:** Task 1
- **Planned:** "row 7 is the medium" in `iplayarr_rows()`. The plan's fixtures used `dismiss 7 -- noise` and `defer 7 -- later`.
- **Actual:** the fixture has rows 1-3 critical, 4-7 warning, and row 8 medium. Row 7 is the synthetic warning. The plan itself said to confirm by reading the fixture.
- **Why:** the order is `real[0:4] + [browse, real[4], synth, real[5]]`, and `real[5]` is the medium.
- **Effect:** fixtures use row 8 as the medium. `test_fixture_bands` pins the band layout so this cannot drift silently.
- **Cost if wrong:** none. The test pins the fixture.

## Threat model

- T-58-33: mitigated (band filter, empty refusal; mutants s1 and s2)
- T-58-34: mitigated (post-trim parse dry-run; mutant s3)
- T-58-35: mitigated. The stderr line has a count only, and the CLI contract test checks refusals for owner words.

No new threat surface. `suggest` is read-only and pure over two files.

## Known Stubs

None. The prose call sites (50-fix-loop.md, 90-finalize.md) still use the `parse` dry-run. Plans 58-15 and 58-17 switch them to `suggest`.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_bottom_line_suggest.py
- FOUND: aab19b2, 4e1fe8a, 353a780
- batch_card.py clean after the mutants; STATE.md / ROADMAP.md / HANDOFF.json not touched by this plan
