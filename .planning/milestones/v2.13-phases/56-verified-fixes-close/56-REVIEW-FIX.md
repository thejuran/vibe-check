---
phase: 56-verified-fixes-close
fixed_at: 2026-10-25T16:15:00Z
review_path: .planning/phases/56-verified-fixes-close/56-REVIEW.md
iteration: 1
findings_in_scope: 14
fixed: 13
skipped: 0
rejected: 0
deferred: 1
status: partial
---

# Phase 56: Code Review Fix Report

**Fixed at:** 2026-10-25
**Source review:** .planning/phases/56-verified-fixes-close/56-REVIEW.md
**Iteration:** 1
**Branch:** feat/v2.13-phase-56 (direct mode, `workflow.use_worktrees=false`)

**Summary:**
- Findings in scope: 14. That is 2 critical, 6 warning, 3 info, and 2 set-aside items with owner rulings (SA-01 fix, SA-02 defer), plus IN-01 by owner decision.
- Fixed: 13
- Deferred: 1 (SA-02, by owner ruling)
- Skipped / rejected: 0

**Method:** reproduce first. For every finding, the test was written before the fix, run, and seen to fail on the code at that moment for the stated reason. Then the fix was applied, the test passed, and the test and fix were committed together. Every new scorer guard has a mutant test (`TestIndependentRouteMutants` m24 to m32) that shows the guard trips when it is removed. Prose guards use the existing removal-mutant lock pattern.

**Gates (after all fixes):**
- Full suite (`pytest -q` in plugins/vibe-check/scripts): **3083 passed, 0 failed** (4102 subtests). The baseline was 3055; there are 28 new tests.
- `replay.py candidate --name phase56-fix --scorer rev:HEAD`: **REGRESSED 0**, UNEVALUABLE 0, AMENDED 1 (pre-existing amendment), kept 25 / protected 26, fidelity 56/66 exact (unchanged baseline drift).
- `replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ALLOWANCES-phase53-nv.json`: 170 runs compared, **runs differing 0, unallowed 0**, differences: none.
- GOLDEN_DIGEST unchanged. score.py imports neither os nor pathlib. No existing Phase 56 contract string (R_* reasons, prose needles) was edited.
- One existing mutant target was edited: m20's target moved from `or touched):` to `or relevant):`. CR-02 renamed that term in the fresh-start condition. The mutation itself is the same (drop the touch term) and the assertion is unchanged.

## Fixed Issues

| ID | Commit | Failing-first test | Mutant test |
|----|--------|--------------------|-------------|
| CR-01 | a70a2e1 | `TestReviewFix56.test_cr01_settled_memory_survives_a_kept_open_row`, `test_cr01_fresh_start_clear_is_not_resurrected` | `test_m24_kept_open_memory_copy_removed`, `test_m25_kept_open_memory_pop_removed` |
| CR-02 | 483fe9f | `TestReviewFix56.test_cr02_unrelated_touch_keeps_the_memory` (+ `test_cr02_relevant_touch_is_a_fresh_start`), `TestReviewFix56Prose.test_cr02_dispatch_skip_rule_matches_scorer` | `test_m26_fresh_start_relevance_filter_removed` (+ m20 retargeted) |
| WR-01 | a6004be | `TestReviewFix56.test_wr01_unbound_plain_never_confirmers_rejected` | `test_m27_unbound_plain_never_confirmers_removed` |
| WR-02 | 7616ca5 | `TestReviewFix56.test_wr02_confirmed_fix_refuses_codex_as_confirmer` | `test_m28_confirmed_fix_codex_exclusion_removed` |
| WR-03 | 36161b4 | `TestReviewFix56.test_wr03_still_applies_on_one_route_blocks_another` | `test_m29_cross_route_still_applies_removed` |
| WR-04 | c0a67e6 | `TestReviewFix56.test_wr04_non_str_file_does_not_crash` | `test_m30_non_str_file_guard_removed` |
| WR-05 | e965b13 | `TestReviewFix56Prose.test_wr05_applied_forwarded_only_while_open` | removal mutants inside the same prose lock |
| WR-06 | d4d0d6f | `TestReviewFix56.test_wr06_association_needs_directory_affinity` | `test_m31_association_directory_affinity_removed` |
| SA-01 | 382b560 | `TestReviewFix56.test_sa01_nv_item_closes_on_independent_route_only_after_a_change`, `TestReviewFix56Prose.test_sa01_prose_says_why_an_nv_item_stayed_open` | `test_m32_nv_change_requirement_removed` (+ prose removal mutants) |
| IN-01 | 03ba1c0 | `TestSixRowFixtureGuards.test_fixture_is_trimmed` (fails on the old fixture) | `test_fixture_trim_check_trips` |
| IN-02 | 2fe3be9 | `TestReviewFix56Prose.test_in02_threshold_assignment_spacing` | its `assertNotIn` on the slipped text |
| IN-03 | b83f6ec | `TestReviewFix56Prose.test_in03_nv_rows_take_the_fix_not_line` | removal mutants inside the same prose lock |

All of these tests are in `plugins/vibe-check/scripts/test_verified_fixes.py`. Mutant tests are in `TestIndependentRouteMutants`.

### CR-01: A still-applies memory is lost on every kept-open row
**Files modified:** `scripts/score.py`, `scripts/test_verified_fixes.py`
**Commit:** a70a2e1
**Applied fix:** `_kept_open_rows` now takes `recheck_settled` from the working record `m`. Before, it came from the carried copy. A memory written this pass survives, and a memory cleared by the fresh-start rule is not brought back.
**Status:** fixed: requires human verification (logic)

### CR-02: Any commit anywhere clears the still-applies memory
**Files modified:** `scripts/score.py`, `phases/review/20-dispatch.md`, `scripts/test_verified_fixes.py`
**Commit:** 483fe9f
**Applied fix:** a new `_settled_path(path, file, fingerprint)` helper decides which changed paths count. The fresh-start rule now clears the memory only when a changed path is the finding's file, a path in its fingerprint, or an associated test of the file. The dispatch skip rule in 20-dispatch.md uses the same filter.
**Status:** fixed: requires human verification (logic)

### WR-01: `fix` / `codex-adversarial` confirm through an unbound plain request
**Files modified:** `scripts/score.py`, `scripts/test_verified_fixes.py`
**Commit:** a6004be
**Applied fix:** an unbound plain request now returns `all(a not in _NEVER_CONFIRMERS ...)`, so these requests are rejected as `verdict: malformed`. Scope note: the existing per-branch checks (m5, m11, m19) were kept as they are. A single check at the top of the function would have made those three mutants redundant.

### WR-02: Confirmed-fix route accepts `codex-adversarial`
**Files modified:** `scripts/score.py`, `scripts/test_verified_fixes.py`
**Commit:** 7616ca5
**Applied fix:** the confirmed-fix branch now also refuses `_NEVER_CONFIRMERS - _FIXER_AGENTS`, which is Codex. The fixer term (and its v2.12 mutant m5) is unchanged. The docstring was updated.

### WR-03: A still-applies on one route does not block a resolution on another
**Files modified:** `scripts/score.py`, `scripts/test_verified_fixes.py`
**Commit:** 36161b4
**Applied fix:** `_accept_verdict` records which routes had a still-applies (plain, independent, confirmed-fix) and which route produced the resolution. A still-applies on any other route now cancels the resolution with `verdict: contradicted by still-applies`. A fix-obsolete resolution counts as "other" for every route. Each route still handles its own contradictions, so the existing mutants m3 and m13 still trip. The literal string was moved into a `_R_CONTRADICTED` constant and is unchanged.
**Status:** fixed: requires human verification (logic)

### WR-04: Crash on a carried record with a non-str `file`
**Files modified:** `scripts/score.py`, `scripts/test_verified_fixes.py`
**Commit:** c0a67e6
**Applied fix:** a new `_head_blob(head_blobs, file)` helper returns None when `file` is not a string. All five lookups now go through it. A blob-bound re-check has no blob match, so the record stays open. The unbound plain needs-recheck shape resolves exactly as it did at 8df9545, before this phase. That shape needs no blob, so "restore fail-safe" meant restoring the old outcome.

### WR-05: `applied` fix verdicts never pruned → stray `record not carried`
**Files modified:** `phases/review/05-state.md`, `scripts/test_verified_fixes.py`
**Commit:** e965b13
**Applied fix:** I picked the forwarding option. Phase 0.5 now forwards an `applied` entry only while its `stable_hash` names a finding in `state.passes[-1].findings`. That is the same lookup `head_blob` already does. The false sentence ("it leaves `fix_verdicts` only when…") was rewritten: forwarding stops when the item closes through `resolved[]`, and the root entry stays as history.
**Why not the prune option:** the pruning option would need a new write to `fix_verdicts` on every pass. 45-persist.md says Phase 4.5 "never creates, copies into, or edits" that root, and only `record-fix-verdicts` writes it. That writer runs only when the fix loop runs, so the stray reason would still appear on passes in between. The owner-decision clause was also corrected: a decided item is still carried, so its verdict is still forwarded and consumed. That is not a stray.

### WR-06: `_is_associated_test` matches across directories
**Files modified:** `scripts/score.py`, `phases/review/20-dispatch.md`, `scripts/test_verified_fixes.py`
**Commit:** d4d0d6f
**Applied fix:** a new `_dir_affine` check, using only string operations. It drops test segments (`test`, `tests`, `__tests__`, `spec`) and source roots (`src`, `lib`, `app`) from each directory. The two directories must then be equal, or one must be a non-empty suffix of the other. All existing positive pairs still match. New negatives include `tests/b/index.test.ts` vs `src/a/index.ts`.
**Known narrowing:** a top-level `tests/test_config.py` no longer associates with `pkg/sub/config.py`. Such a record still triggers when its own file is touched or a change is made nearby.
**Status:** fixed: requires human verification (logic)

### SA-01 (owner decision 2026-10-25): NV item closed by one reviewer without a code change
**Files modified:** `scripts/score.py`, `phases/review/20-dispatch.md`, `phases/review/30-collect-score.md`, `phases/review/40-render.md`, `templates/output-format.md`, `scripts/test_verified_fixes.py`
**Commit:** 382b560
**Applied fix:** `_independent_recheck` now requires the D-04 trigger (`_independent_trigger`) for every Needs-verification lead, whatever its status. A failed relocation reads as needs-recheck, but it is not a code change. Without the trigger, the item stays open with the new reason `verdict: fix not confirmed: no change to this Needs-verification item's file or tests since it was raised; it stays open for your decision`. The render shows "Stays open for your decision: a re-check closes a Needs-verification item only after its file or tests change — confirm, dismiss or defer it by number." **Six-row check:** all six still close (`test_all_six_close_on_independent_evidence` passes). None of the six is a Needs-verification row, so the guard does not apply to them.
**Residual (not changed):** the D-11 "no eligible reviewer ran this pass" reason still appears on a no-trigger Needs-verification needs-recheck row when no reviewer was dispatched. An existing Phase 56 test (`test_no_confirmer_reason_not_doubled_under_a_confirmed_fix`) pins this behavior, so I left it.
**Status:** fixed: requires human verification (logic)

### IN-01 (owner decision): trim the iPlayarr fixture
**Files modified:** `scripts/fixtures/iplayarr45-six-row-state.json`, `scripts/test_verified_fixes.py`
**Commit:** 03ba1c0
**Applied fix:** the file went from 90 KB to 17 KB. Pass 3 keeps the six rows with file paths, titles, the pinned line, scores, `members`/`snapshot`/`kept_open`, and the keys the schema requires. `problem` and `source_window` were emptied, `current_code` was cut to its first line, and `why_it_matters`, `fix_hint`, `intent_doc_match` and `cwe` were dropped. Passes 1 and 2 keep only their recorded rejections and codex blocks. Timestamps were normalized. The pass `head_sha`/`diff_range` values were kept because the schema requires them. Fix commit SHAs remain only in `FIX_COMMITS` in the test module. The test docstring was updated. All tests pass on the trimmed fixture, including `test_carry_state.py`.

### IN-02: `threshold =THRESHOLDS` spacing
**Files modified:** `scripts/score.py`, `scripts/test_verified_fixes.py`
**Commit:** 2fe3be9

### IN-03: Render prose unclear for Needs-verification rows with a `verdict: fix not …` reason
**Files modified:** `phases/review/40-render.md`, `templates/output-format.md`, `scripts/test_verified_fixes.py`
**Commit:** b83f6ec
**Applied fix:** 40-render.md now says that a Needs-verification row with no `verdict: confirmed fix` reason counts as an "OTHER open row" and gets the `Fix not yet confirmed:` line. A row that has a confirmed-fix reason shows only `Fix not yet verified:`. output-format.md says the same.

## Deferred Issues

### SA-02: Plain re-checks of `needs-recheck` records ignore `snapshot_blob`
**File:** `plugins/vibe-check/scripts/score.py` (the plain-request path in `_accept_verdict`)
**Reason:** deferred by owner ruling (2026-10-25). This behavior existed before Phase 56 and was not introduced by it. Under the scope-discipline rule, new work is added only for a reproduced gate failure, data loss, silent finding loss, or a broken required workflow. This finding is none of those.
**Original issue:** a `needs-recheck` record can close on a plain `resolved` while the file is dirty or differs from what the reviewer read, even though the prose says every plain entry carries `snapshot_blob`.

---

_Fixed: 2026-10-25_
_Fixer: Claude (bm-code-fixer)_
_Iteration: 1_
