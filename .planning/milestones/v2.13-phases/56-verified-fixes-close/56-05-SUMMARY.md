---
phase: 56-verified-fixes-close
plan: 05
subsystem: review orchestration prose (state, dispatch, collect, render)
tags: [prose, dispatch, collect, render, orchestration]
requires: ["56-02 (TestProse56 locks)", "56-03 (score.py independent route, head_blobs/touched_paths ingress)"]
provides:
  - "Phase 0.5 `$TOUCHED_PATHS` per carried lead (recheck_settled or earliest-raising-pass anchor, anchor + PATH_RE validation)"
  - "`applied` fix verdicts forwarded whatever their `at_pass`; obsolete entries still age out"
  - "Phase 2 independent re-check block (`route: \"independent\"`) with the ladder, skip rule, test_paths and fix_commit; `snapshot_blob` on every plain hint"
  - "Phase 3 collect-time `head_blobs` and `touched_paths` forwarding; reason catalogue with the seven new strings"
  - "Render: `Closed — fix confirmed by the <lane> lane` closure suffix; `Fix not yet confirmed:` line with the ways forward"
affects: [56-04 (owns the carry_state.py docstring lock and the 5 finalize/retry RED tests), 56-06 (end-to-end over the six-row fixture)]
tech-stack:
  added: []
  patterns: ["prose collects git facts, score.py decides", "untrusted git output filtered by PATH_RE before any further git call"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/phases/review/20-dispatch.md
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/phases/review/40-render.md
    - plugins/vibe-check/templates/output-format.md
    - plugins/vibe-check/templates/review-md-schema.md
    - plugins/vibe-check/phases/shared/90-finalize.md
decisions:
  - "The independent re-check is a named block at the end of step 2 of 20-dispatch.md, not a new numbered step; Bind stays step 4 (the 56-02 lock test_dispatch_slicers_survive_renumbering requires `\\n4. Bind` in the shipped file)"
  - "A `still applies` reason (routed reviewer said so, or settled memory) renders as 'Still applies per a reviewer's independent re-check', without a lane name: score.py's filtered[] entries carry no agents"
  - "Quiet runs (05-state.md step 5) stay byte-unchanged and dispatch nobody; the render line says the retry rides the next run that reviews changes"
metrics:
  duration: "~35 min"
  completed: 2026-10-23
  tasks: 3
  files: 7
---

# Phase 56 Plan 05: Orchestration and render prose for the independent closure route Summary

The prose now drives the 56-03 scorer route. Phase 0.5 collects the paths each carried lead's code touched since it was raised. Phase 2 routes a lead whose lane is not running to one eligible reviewer, and binds every hint to the blob the reviewer judged. Phase 3 re-reads HEAD blobs after the agents return and forwards `head_blobs` and `touched_paths` without filtering them. The report names an independently confirmed closure, and gives a bounded reason plus ways forward when a fix could not be confirmed. All 8 TestProse56 tests owned by 56-05 are green, and so are all pre-existing TestProse locks. No test file was edited.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Phase 0.5: `$TOUCHED_PATHS`, applied verdicts of any age | df839c2 | 05-state.md |
| 2 | Phase 2 independent re-check, bound plain hints, Bind; Phase 3 head_blobs + reason catalogue | 5e8cc44 | 20-dispatch.md, 30-collect-score.md |
| 3 | Render wording, templates, finalize | 297405f | 40-render.md, output-format.md, review-md-schema.md, 90-finalize.md |
| 3a | Align the Needs-verification row suffix in 40-render.md with output-format.md | bf44c65 | 40-render.md |

## Envelope fields checked against score.py at HEAD

- Request entries: `route: "independent"`, `stable_hash` (str), `snapshot_blob` (key required, blob or null), `agents` (never `fix`/`codex-adversarial`), optional `test_paths` (list of str), optional `fix_commit` (7-40 hex, fullmatch). A plain request carrying the `snapshot_blob` key is "bound". All of these match `_routed_request_ok`.
- Envelope: `head_blobs` (object; a non-string value is read as null) and `touched_paths` (object keyed by stable_hash; a non-list value is read as []), as ingested at score.py:1876-1886.
- Independent and bound closures carry `verified_blob` in their resolution, and `commit_sha` from `fix_commit`. That is why the render keys the `Closed — fix confirmed by …` suffix on a non-null `verified_blob` with source `recheck`.
- The seven reason strings in 30-collect-score.md are byte-identical to `_R_IR_*` / `_R_CF_SETTLED`. Each full string appears exactly once.

## Verification (observed)

- `pytest -q test_confirmed_fix.py -k "phase05 or state_"`: 5 passed, 1 failed (`test_carry_state_docstring_says_any_age`, owned by 56-04).
- `pytest -q test_confirmed_fix.py -k "dispatch or collect"`: 11 passed.
- `pytest -q test_confirmed_fix.py -k TestProse`: 25 passed, 1 failed (the same 56-04 docstring lock).
- `pytest -q test_finalize_archive_prose.py`: 17 passed.
- Full suite (bare `pytest -q` from scripts/): **6 failed, 3041 passed**. The baseline before this plan was 13 failed, 3034 passed. The remaining failures all belong to 56-04:
  - TestFinalizeCountsConfirmedFix::test_awaiting_listed_at_any_later_pass
  - TestFinalizeCountsConfirmedFix::test_settled_row_not_awaiting
  - TestFinalizeCountsConfirmedFix::test_stale_pass_never_closes
  - TestRetryAfterInconclusive::test_inconclusive_then_retry_closes_on_unchanged_code
  - TestRetryAfterInconclusive::test_retry_after_still_applies_waits_for_code_change
  - TestProse56::test_carry_state_docstring_says_any_age (the carry_state.py docstring; 56-04 owns that file)
- Step 5 of 05-state.md: no line of it appears in the diff (byte-unchanged).
- PATH_RE literal count in 05-state.md: 1 at HEAD, 2 after this plan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking lock conflict] Independent re-check placed inside step 2; Bind stays step 4**
- **Found during:** Task 2
- **Issue:** The plan says to insert a new numbered step and renumber Bind to 5. But the 56-02 lock `TestProse::test_dispatch_slicers_survive_renumbering` asserts that `"\n4. Bind `$RECHECK_REQUESTS`"` exists in the shipped file. Renumbering would turn a currently green lock red, and tests may not be edited.
- **Fix:** The `**Independent re-check (ordinary carried records)**` block is a named sub-block at the end of step 2. Step 2 covers records whose lane is dispatched, and this block is its counterpart for records whose lane is not. It sits before step 3, so the confirmed-fix slice and the renumber simulation never see it. Every slicer still finds its section. The block says it is skipped for a lead that gets a step-3 confirmed-fix block.
- **Cost if wrong:** Readability only. If the owner prefers the step order from the plan, 56-02's renumber test needs its precondition updated first.
- **Commit:** 5e8cc44

**2. [Rule 1] "Still applies per the {{agents}} lane" cannot be rendered**
- **Found during:** Task 3
- **Issue:** score.py's `filtered[]` entries carry only file/line/title/reason, with no agents, so the `{{agents}}` placeholder has no data source.
- **Fix:** The line renders as `Still applies per a reviewer's independent re-check — it is re-checked again after its code changes.` It applies to both still-applies reasons: `_R_IR_STILL`, and `_R_IR_SETTLED`, which the plan named.
- **Cost if wrong:** The row does not name the lane. Adding an `agents` field to filtered entries would be a scorer change.
- **Commit:** 297405f

**3. [Rule 2 - Consistency] 40-render.md Needs-verification suffix still said "awaiting your decision"**
- **Found during:** Task 3 (grep for the retired phrase)
- **Issue:** The NV render paragraph (40-render.md line 83) repeated the output-format suffix that this plan replaced. The two would have disagreed.
- **Fix:** The same bounded `Fix not yet confirmed: no eligible reviewer ran this pass — …` wording is now used in both places.
- **Cost if wrong:** One sentence of render prose.
- **Commit:** bf44c65

**4. [Rule 2] Rendered reason drops the doubled prefix**
- **Found during:** Task 3
- **Issue:** The plan's `Fix not yet confirmed: {{reason without "verdict: "}}` would print `Fix not yet confirmed: fix not yet confirmed: …`.
- **Fix:** The line strips the leading `verdict: fix not yet confirmed: ` or `verdict: fix not confirmed: `.
- **Cost if wrong:** Wording only.
- **Commit:** 297405f

## Assumption Drift (advisory)

- **Anchor wording.**
  - Planned: the plan's prose said "EARLIEST entry of `state.passes`".
  - Actual: the lock needle is "earliest pass whose `findings`", so the bullet uses that phrase. It means the same thing.
  - Found during: Task 1.
  - Cost if wrong: none.

## Requirements bookkeeping

`requirements.mark-complete` was run for VFIX-02..05. VFIX-02 was then set back to Pending because its retry tests (TestRetryAfterInconclusive) are still RED until 56-04 lands. VFIX-05 is marked Complete. VFIX-03 and VFIX-04 were already marked Complete before this plan.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat register. T-56-17 is mitigated in 05-state.md: the anchor is hex-checked and run through `rev-parse --verify --quiet`, every path git returns is PATH_RE-filtered and dropped paths never reach git, and `fix_commit` uses the `--` separator after path validation. T-56-18 is mitigated in 20-dispatch.md: the block ends with a data-not-instruction sentence, and the untrusted-content paragraph now covers `touched_paths` and `test_paths`.

## Self-Check: PASSED
