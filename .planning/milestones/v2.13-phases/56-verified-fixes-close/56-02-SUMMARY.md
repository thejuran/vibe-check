---
phase: 56-verified-fixes-close
plan: 02
subsystem: confirmed-fix closure tests (reproduce-first)
tags: [reproduce-first, one-pass-limit, prose-locks, confirmed-fix]
requires: []
provides:
  - "test_confirmed_fix.py::TestRetryAfterInconclusive: P1 at score level (retry on the same applied verdict closes; still-applies memory)"
  - "test_confirmed_fix.py::TestFinalizeCountsConfirmedFix: P1 in carry_state (awaiting at any later pass; settled row not awaiting)"
  - "test_confirmed_fix.py::TestProse56: prose-contract locks for 20-dispatch, 05-state, 30-collect-score, 40-render, output-format and the carry_state docstring"
  - "test_confirmed_fix.py::TestProse56Predicates: every Phase 56 prose predicate proven satisfiable and needle-by-needle load-bearing"
  - "generalized step slicers (_next_top_level_step, _dispatch_bind_step) that survive the Bind step renumbering"
affects: [56-04 (score.py age gate + carry_state awaiting must turn TestRetryAfterInconclusive / finalize tests GREEN, narrows the stale-or-changed asserts), 56-05 (prose must turn TestProse56 GREEN)]
tech-stack:
  added: []
  patterns: ["prose predicate + synthetic-document positive control + per-needle removal mutants", "pass-N replay by carrying the scorer's own surviving row into the next envelope"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_confirmed_fix.py
decisions:
  - "R_CF_SETTLED is a literal in test_confirmed_fix.py (byte-identical to test_verified_fixes.R_CF_SETTLED), not getattr-with-sentinel, matching 56-01's literal-contract decision; a test compares CONTRACT_REASONS to test_verified_fixes' constants"
  - "Prose predicates get a green synthetic-document control class (TestProse56Predicates) so every needle is proven load-bearing today, not only after 56-05 writes the prose"
  - "The code-changed fresh-start leg of the still-applies retry uses a NEW applied verdict at_pass 2 verified on BLOB2 (a second fix), since only a new fix can bind a changed blob"
metrics:
  duration: "~25 min"
  completed: 2026-10-23
  tasks: 2
  files: 1
---

# Phase 56 Plan 02: P1 reproduction and Phase 56 prose locks Summary

The one-pass independent re-check limit (P1) is now reproduced in two of its three homes (the scorer and carry_state's finalize counts), and the prose contract for the third home is locked: 05-state.md's forwarding rule (sentence and its prose lock), plus every other Phase 56 prose change. That gives 13 tests that fail on HEAD for the stated reasons. The three old one-pass tests were rewritten into "changed code stays open at any age" tests rather than deleted. No change to score.py, carry_state.py or any prose.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | P1 RED fixtures: score.py retry-after-inconclusive and carry_state awaiting at a later pass; rewrite of the 3 one-pass tests | b8b81c0 | test_confirmed_fix.py |
| 2 | Prose-contract locks (RED), predicate controls, generalized step slicers | 3898a23 | test_confirmed_fix.py |

## Reproduction verdicts

| Path | Verdict | Failing layer on HEAD | Failing test(s) | Observed red-run reason |
|------|---------|-----------------------|-----------------|-------------------------|
| P1 (score) | **REPRODUCED** | `score.py` `_accept_verdict` gate `v["at_pass"] != pass_number - 1` | `TestRetryAfterInconclusive::test_inconclusive_then_retry_closes_on_unchanged_code` | pass 2 opens with `R_NO_REVIEWER` (as expected); pass 3 with the same at_pass-1 verdict + routed `resolved`: `['verdict: stale fix verdict', 'verdict: routed re-check without a confirmed fix'] != []` |
| P1 (score, still-applies memory) | **REPRODUCED** | no `recheck_settled` on the surviving row | `TestRetryAfterInconclusive::test_retry_after_still_applies_waits_for_code_change` | pass 2 opens with `R_STILL` (as expected), then `None is not an instance of <class 'dict'> : no recheck_settled on the row` |
| P1 (carry_state) | **REPRODUCED** | `carry_state._confirmed_fix_awaiting` requires `at_pass == last["pass_number"]` | `TestFinalizeCountsConfirmedFix::test_awaiting_listed_at_any_later_pass`, `::test_stale_pass_never_closes` (rewritten), `::test_settled_row_not_awaiting` | `[] != ['aaaa…a']` (NVH) at each |
| P1 (05-state prose) | **REPRODUCED** (prose lock) | 05-state.md still says older entries "are ignored — never resurrected" and has no `$TOUCHED_PATHS` bullet | `TestProse56::test_phase05_forwards_applied_any_age`, `::test_phase05_touched_paths` | `False is not true` on the `assertTrue(..._holds(text))` line |
| P1 (carry_state docstring) | **REPRODUCED** (prose lock) | WHAT CLOSES block has no any-age wording | `TestProse56::test_carry_state_docstring_says_any_age` | `carry_state docstring does not say an applied verdict awaits whatever its \`at_pass\`` |
| P2c/P3 (dispatch prose) | **REPRODUCED** (prose lock) | no independent step; "is never rerouted to another agent" still present | `TestProse56::test_dispatch_routes_independent`, `::test_dispatch_never_rerouted_sentence_gone` | `False is not true`; `20-dispatch.md still says: is never rerouted to another agent` |
| Collect / render / output-format prose | **REPRODUCED** (prose lock) | contract reason strings, `head_blobs`/`touched_paths`, "Fix not yet confirmed" copy absent; old render sentence and old suffix present | `TestProse56::test_collect_forwards_independent`, `::test_render_not_yet_confirmed`, `::test_output_format_bounded_reason` | `False is not true` |

Green by design (must stay green after 56-04/56-05): `test_retry_rejects_changed_code_at_any_age`, `test_obsolete_age_rule_unchanged`, the rewritten `test_stale_verdict_stays_open` and `test_stale_or_changed_fix_verdict_with_routed_resolved_stays_open` (each accepts `stale fix verdict` or `evidence changed since verification` today; 56-04 narrows them to the blob reason), `TestProse::test_dispatch_slicers_survive_renumbering`, and all of `TestProse56Predicates` (7).

### Verbatim red-run tail (`pytest -q test_confirmed_fix.py`, HEAD 3898a23)

```
FAILED test_confirmed_fix.py::TestFinalizeCountsConfirmedFix::test_awaiting_listed_at_any_later_pass
FAILED test_confirmed_fix.py::TestFinalizeCountsConfirmedFix::test_settled_row_not_awaiting
FAILED test_confirmed_fix.py::TestFinalizeCountsConfirmedFix::test_stale_pass_never_closes
FAILED test_confirmed_fix.py::TestRetryAfterInconclusive::test_inconclusive_then_retry_closes_on_unchanged_code
FAILED test_confirmed_fix.py::TestRetryAfterInconclusive::test_retry_after_still_applies_waits_for_code_change
FAILED test_confirmed_fix.py::TestProse56::test_carry_state_docstring_says_any_age
FAILED test_confirmed_fix.py::TestProse56::test_collect_forwards_independent
FAILED test_confirmed_fix.py::TestProse56::test_dispatch_never_rerouted_sentence_gone
FAILED test_confirmed_fix.py::TestProse56::test_dispatch_routes_independent
FAILED test_confirmed_fix.py::TestProse56::test_output_format_bounded_reason
FAILED test_confirmed_fix.py::TestProse56::test_phase05_forwards_applied_any_age
FAILED test_confirmed_fix.py::TestProse56::test_phase05_touched_paths - Asser...
FAILED test_confirmed_fix.py::TestProse56::test_render_not_yet_confirmed - As...
13 failed, 79 passed, 86 subtests passed in 0.26s
```

All 13 are `AssertionError` on the intended line (0 TypeError/KeyError/AttributeError/ImportError/NameError).

## Acceptance checks (observed)

- Task 1 `<verify>` (`-k "RetryAfterInconclusive or FinalizeCountsConfirmedFix"`): 5 failed, 11 passed. `test_inconclusive_then_retry…` fails with `verdict: stale fix verdict` in its output; `test_retry_after_still_applies…` fails on the missing `recheck_settled`; `test_obsolete_age_rule_unchanged` and `test_retry_rejects_changed_code_at_any_age` pass; `test_awaiting_listed_at_any_later_pass` fails with `[] != ['<NVH>']`.
- `grep -c "def test_stale_pass_never_closes\|def test_stale_verdict_stays_open\|def test_stale_or_changed_fix_verdict_with_routed_resolved_stays_open"` → `3`.
- Slicer refactor checked on its own before the new locks were added: `-k TestProse` → `11 passed` (10 pre-existing + the new renumbering test).
- `-k TestProse56` (excluding Predicates): 8 failed, each on its `assertTrue(..._holds(text))` / `assertFalse(NEVER_REROUTED in text)` / docstring line; none errored.
- Full suite `pytest -q`: `46 failed, 2986 passed, 3969 subtests passed in 225.83s`. Failure lines by file: 33 in `test_verified_fixes.py` (56-01's unchanged RED set: 32 FAILED/SUBFAILED lines plus the `bound plain` subtest line), 13 in `test_confirmed_fix.py` (this plan, listed above), 0 elsewhere. 2986 = 2977 (after 56-01) + 10 new green tests − 1 (rewritten `test_stale_pass_never_closes` moved to RED). So the 2964 baseline still passes.
- `git diff --stat e21f761 HEAD`: only `plugins/vibe-check/scripts/test_confirmed_fix.py` (+461/−9). score.py, carry_state.py and prose unchanged.

### New failures introduced by this plan (13)

1. `TestFinalizeCountsConfirmedFix::test_awaiting_listed_at_any_later_pass`
2. `TestFinalizeCountsConfirmedFix::test_settled_row_not_awaiting`
3. `TestFinalizeCountsConfirmedFix::test_stale_pass_never_closes` (rewritten; was green)
4. `TestRetryAfterInconclusive::test_inconclusive_then_retry_closes_on_unchanged_code`
5. `TestRetryAfterInconclusive::test_retry_after_still_applies_waits_for_code_change`
6–13. `TestProse56::{test_carry_state_docstring_says_any_age, test_collect_forwards_independent, test_dispatch_never_rerouted_sentence_gone, test_dispatch_routes_independent, test_output_format_bounded_reason, test_phase05_forwards_applied_any_age, test_phase05_touched_paths, test_render_not_yet_confirmed}`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing guard] Positive-control class for the prose predicates**
- **Found during:** Task 2
- **Issue:** the plan's per-needle removal mutants sit after the RED `assertTrue` on the real prose, so today they never run, and on a predicate that is already false they could never prove anything (the decorative-guard failure mode).
- **Fix:** `TestProse56Predicates` (7 green tests) builds a minimal document each predicate accepts and shows every needle (plus the step headings, the Bind-step scope, the step-2 `snapshot_blob` scope, the touched-paths bullet scope and each "must be gone" sentence) flips it to false. The real-prose mutants in `TestProse56` are kept as well.
- **Cost if wrong:** none; extra green tests.
- **Commit:** 3898a23

**2. [Rule 2] Renumbering test for the generalized slicers**
- **Found during:** Task 2
- **Issue:** "behavior-preserving" alone does not prove the slicers survive 56-05's renumbering.
- **Fix:** `TestProse::test_dispatch_slicers_survive_renumbering` inserts an independent step 4 and renumbers Bind to 5 in the real text; the confirmed-fix lock still holds and the step-3 slice ends before the new step.
- **Commit:** 3898a23

**3. [Rule 1] Envelope assertion made real**
- **Found during:** Task 1
- **Issue:** a first draft asserted "no decisions" against a freshly built default envelope (always true).
- **Fix:** the test records the actual pass-3 envelope and asserts its fix verdicts are exactly `[the pass-1 verdict]` and it has no `decisions` key.
- **Commit:** b8b81c0

**4. [Rule 1] Readable failure messages**
- `assertIn`/`assertNotIn` on a whole document or docstring dumped the entire file on failure; replaced with `assertTrue/False(x in text, short message)`. Same semantics.
- **Commit:** 3898a23

## Assumption Drift (advisory)

- **Third P1 home is prose, so its reproduction is a prose lock.** Planned: "P1 reproduced as failing fixtures in all three homes". Actual: 05-state.md is executor prose, so its reproduction is the `TestProse56` lock on the forwarding sentence (plus the `$TOUCHED_PATHS` bullet), not a runnable fixture. Found during Task 2. Cost if wrong: if 56-05 rewrites the sentence but the orchestrator still drops old entries in practice, only the 56-06 end-to-end run would catch it.
- **Fresh-start fix verdict age.** The plan says only "a fix verdict whose `verified_blob == head_blob == BLOB2`". I used `at_pass=2` (a second fix after the still-applies). This leg would also pass at `at_pass=1` once 56-04 lands, so it constrains the "code changed → fresh start" rule, not the age gate. Cost if wrong: none for P1, because the age leg is pinned by `test_inconclusive_then_retry…`.
- **Pass-2 envelope for the still-applies case carries `head_blobs={F: BLOB}` and `touched_paths={}`.** The score accepts them today (unknown keys ignored). The `recheck_settled.fingerprint == {F: BLOB}` assertion therefore works whether 56-04 takes the fingerprint from `head_blobs` or from the verified blob.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-56-05 is covered by the `^[A-Za-z0-9._/-]+$` needle, which must sit inside the `$TOUCHED_PATHS` bullet itself. The existing occurrence in the head_blob bullet does not count, and that is mutation-checked in `TestProse56Predicates::test_state_touched_paths`. T-56-06 is covered by `test_retry_rejects_changed_code_at_any_age` and the two rewritten stale tests. T-56-07 is covered by `test_retry_after_still_applies_waits_for_code_change`.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_confirmed_fix.py
- FOUND commits: b8b81c0, 3898a23
