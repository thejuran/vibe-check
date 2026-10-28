---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 02
subsystem: review-render
tags: [recovery, render-prose, prose-lock, RECV-02]
requires: []
provides:
  - "Recovery pairs table in phases/review/40-render.md (12 rows, one per score.py fix-not / confirmed-fix reason)"
  - "scripts/test_recovery_pairs.py prose <-> score.py lock"
affects:
  - plugins/vibe-check/phases/review/40-render.md
  - plugins/vibe-check/templates/output-format.md
  - README.md
tech-stack:
  added: []
  patterns: ["vars(score) reason inventory cross-checked against a prose table"]
key-files:
  created:
    - plugins/vibe-check/scripts/test_recovery_pairs.py
  modified:
    - plugins/vibe-check/phases/review/40-render.md
    - plugins/vibe-check/templates/output-format.md
    - README.md
    - plugins/vibe-check/scripts/test_confirmed_fix.py
decisions:
  - "Retry wording only for the six reasons the code re-asks (IR/CF NO_REVIEWER, NO_ANSWER, SNAPSHOT); STILL/SETTLED/NO_TRIGGER/NV_NO_CHANGE say what must change instead"
  - "No pair sends the owner to /deep-review: a run with nothing new dispatches no reviewer under either command"
  - "Action count in a You can cell is split on ', or ' (not ' or '), so 'commit or stash your edits' counts as one action"
metrics:
  duration: "~25 min"
  completed: 2026-10-27
  tasks: 2
  files: 5
---

# Phase 58 Plan 02: Per-reason recovery pairs Summary

Every `verdict: fix not …` / `verdict: confirmed fix …` reason in score.py now renders a fixed `Next run:` + `You can:` pair from one table in 40-render.md, replacing the shared "retried on the next run … or run /deep-review … or dismiss" tail. The table is locked to score.py's constants by a test that has mutants, and the README, the output template and the NV suffix now match the shipped Phase 56/57 behavior.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED: test_recovery_pairs.py lock | b689638 | scripts/test_recovery_pairs.py |
| 2 | GREEN: table, NV suffix, template, README, pins | bc7b595 | 40-render.md, output-format.md, README.md, test_confirmed_fix.py, test_recovery_pairs.py |

## RED evidence (Task 1, observed)

- `pytest -q scripts/test_recovery_pairs.py -k Inventory` → `3 passed` (the collector finds 12 constants before any prose exists).
- Full file on unchanged prose → `15 failed, 7 passed`. Failure lines:
  - `AssertionError: Lists differ: ['marker not found: **Recovery pairs (D-13).**'] != []` (coverage, cells, NV row, honesty)
  - `AssertionError: 0 != 2` (rules point at the table)
  - `phases/review/40-render.md still says: run /deep-review`, `templates/output-format.md still says: run /deep-review`
  - `phases/review/40-render.md lacks the NV suffix`, `templates/output-format.md lacks the NV suffix`
  - `README lacks: every later run that reviews changes`
  - all five TestLockTrips fail in setUp (the shipped table did not exist yet)

## Final table (verbatim, 40-render.md)

| Reason (score.py literal) | Next run | You can |
|---|---|---|
| `verdict: fix not yet confirmed: no eligible reviewer ran this pass` | Next run: retried automatically on the next review of new changes (a run with nothing new dispatches no reviewer). | You can: commit further work and re-run, or dismiss/defer it by number. |
| `verdict: fix not yet confirmed: the routed reviewer gave no verdict` | Next run: retried automatically on the next review of new changes. | You can: wait for that run, or dismiss/defer it by number. |
| `verdict: fix not confirmed: the reviewed code is not the code at HEAD` | Next run: retried automatically; it can close only when the file has no uncommitted edits. | You can: commit or stash your edits to that file, or dismiss/defer it by number. |
| `verdict: fix not confirmed: no change near the finding or in its file since it was raised` | Next run: not closed until its file, a test of it, or code near it changes. | You can: fix it, or dismiss/defer it by number. |
| `verdict: fix not confirmed: the routed reviewer says it still applies` | Next run: not re-checked until this code changes. | You can: fix it again, or dismiss/defer it by number. |
| `verdict: fix not confirmed: a reviewer said it still applies and the code is unchanged since` | Next run: not re-checked until this code changes. | You can: fix it again, or dismiss/defer it by number. |
| `verdict: fix not confirmed: no change to this Needs-verification item's file or tests since it was raised; it stays open for your decision` | Next run: Stays open for your decision: a re-check closes a Needs-verification item only after its file or tests change. | You can: confirm (fix N), dismiss or defer it by number. |
| `verdict: confirmed fix awaiting independent re-check: no eligible reviewer this pass` | Next run: retried automatically on the next review of new changes (a run with nothing new dispatches no reviewer). | You can: commit further work and re-run, or dismiss/defer it by number. |
| `verdict: confirmed fix awaiting independent re-check: the routed reviewer gave no verdict` | Next run: retried automatically on the next review of new changes. | You can: wait for that run, or dismiss/defer it by number. |
| `verdict: confirmed fix not verified: the reviewed code is not the repaired code` | Next run: retried automatically while the repaired code stays as committed; a later change to the file voids the fix evidence and the item takes the ordinary re-check. | You can: commit or stash your edits to that file, or dismiss/defer it by number. |
| `verdict: confirmed fix not verified: the routed reviewer says it still applies` | Next run: not re-checked until this code changes. | You can: fix it again, or dismiss/defer it by number. |
| `verdict: confirmed fix not verified: the routed reviewer said it still applies and the code is unchanged since` | Next run: not re-checked until this code changes. | You can: fix it again, or dismiss/defer it by number. |

NV needs-recheck suffix (identical in 40-render.md and templates/output-format.md):
` — code changed since last pass; Fix not yet confirmed: no eligible reviewer ran this pass — Next run: retried automatically on the next review of new changes. You can: commit further work and re-run, or dismiss/defer it by number`

README limitation bullet now reads: "a Needs-verification item you had fixed is re-checked automatically on every later run that reviews changes while the repaired code is unchanged. … the item stays open until a reviewer confirms the fix or you decide it."

## Mutants (each applied, observed failing, reverted)

Plan mutants a-e were applied to the real files (40-render.md, and for (c) score.py itself), the tests were run with `-k "not Trips"` so the in-file TestLockTrips copies did not mask the result, and then the files were restored from a scratchpad backup. The same five also live in-file as `TestLockTrips`.

| # | Mutant | Observed failure |
|---|--------|------------------|
| a | " It is retried next run." appended to IR_STILL Next run cell | `FAILED TestRetryHonesty::test_retry_word_iff_retrying` |
| b | IR_NO_TRIGGER row deleted | `FAILED TestPairsCoverage::test_every_reason_has_one_row` |
| c | `_R_IR_SYNTHETIC = "verdict: fix not confirmed: synthetic"` appended to score.py | `FAILED TestReasonInventory::test_twelve_reasons`, `FAILED TestPairsCoverage::test_every_reason_has_one_row` |
| d | " or run /deep-review" added to the IR_NO_ANSWER You can cell | `SUBFAILED(40-render.md) test_no_deep_review_promise_anywhere`, `FAILED test_retry_word_iff_retrying` |
| e | marker `**Recovery pairs (D-13).**` removed | 4 FAILED (coverage, cells, NV row, honesty) |
| f | README reverted to "gets **one** automatic independent re-check" | `FAILED TestReconciled::test_readme_says_every_later_run` |
| g | output-format NV suffix reverted to the old /deep-review tail | `SUBFAILED(output-format.md)` in `test_no_deep_review_promise_anywhere` and `test_nv_suffix_in_both_files` |
| h | "The row stays in its section — it is still open." removed | `FAILED TestReconciled::test_rows_stay_open` |
| i | `## Recovery` heading inserted above the table | `FAILED TestReconciled::test_no_new_heading` |
| j | "by number" dropped from the NO_TRIGGER You can cell | `FAILED TestPairsCoverage::test_cells_well_formed` |
| k | third action ", or wait," added to a You can cell | `FAILED TestPairsCoverage::test_cells_well_formed` |
| l | CF rule no longer says "then the pair for that reason from the table below" | `FAILED TestPairsCoverage::test_rules_point_at_the_table` |

After the revert, `pytest -q scripts/test_recovery_pairs.py` → `18 passed, 8 subtests passed`, and `git diff --name-only` did not list score.py.

The updated `RENDER_NEEDLES` in test_confirmed_fix.py are covered by that file's existing `test_render_not_yet_confirmed`, which removes each needle from the real 40-render.md and asserts the predicate goes false (it passed, so each new needle is present in the file and load-bearing).

## Verification (observed)

- Quick set `pytest -q scripts/test_recovery_pairs.py scripts/test_confirmed_fix.py scripts/test_verified_fixes.py scripts/test_nv_render.py scripts/test_score.py` → `737 passed, 704 subtests passed`.
- Grep gates: marker count 1; `^| \`verdict: ` rows 12; `deep-review` in 40-render.md 17 (was 19), `run /deep-review` 0; output-format.md `deep-review` 2 (was 3), `run /deep-review` 0; old tail count 0 in both files; README `one** automatic` 0, `every later run that reviews changes` 1; no new untracked `.md` under plugins/vibe-check.
- score.py not modified; test_score.py (GOLDEN_DIGEST) green.
- test_verified_fixes.py pins (`NV_RENDER_LINE`, `NV_OUTPUT_LINE`) were not changed: the stays-open sentence is kept verbatim in the NV_NO_CHANGE row and in output-format.md.
- Full suite (`pytest -q` from plugins/vibe-check, after bc7b595): `3344 passed, 4404 subtests passed` (3326 before + 18 new, 0 failed).

## Deviations from Plan

**1. [Rule 1 - Bug] "At most two actions" split on ", or " instead of " or "**
- **Found during:** Task 1
- **Issue:** The plan's draft cell "commit or stash your edits to that file, or dismiss/defer it by number" splits into three parts on " or ", so the plan's own wording would fail the plan's own check.
- **Fix:** `cell_problems` counts actions by splitting on ", or ". Mutant k shows a real third action still trips.
- **Cost if wrong:** a cell could join a third action without a comma and pass the lock; the wording is still owner-visible in review.
- **Commit:** b689638

**2. [Rule 2 - Clarity] Rule text for a reason missing from the table**
- **Found during:** Task 2
- **Issue:** The IR rule now ends the line with ` — ` before the pair. A reason missing from the table would leave a dangling dash.
- **Fix:** The marker paragraph says such a row "renders the reason line alone, without the trailing ` — `". The coverage test makes the case unreachable for current constants.
- **Cost if wrong:** cosmetic only.
- **Commit:** bc7b595

**3. Test-message hygiene (no behavior change):** assertions on whole files use `assertTrue(x in text, msg)` so a failure prints the needle, not the whole README. One part went into the RED commit and the rest into bc7b595.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_recovery_pairs.py
- FOUND: b689638, bc7b595
