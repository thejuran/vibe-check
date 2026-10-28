---
phase: 56-verified-fixes-close
verified: 2026-10-25T16:22:58Z
status: passed
score: 6/6 must-haves verified
has_blocking_gaps: false
overrides_applied: 0
---

# Phase 56: Verified fixes close Verification Report

**Phase Goal:** A fix that independent evidence confirms closes its finding on the next run without a dummy code change or a repeated owner confirmation, while stale evidence is still rejected and still-applicable findings stay open (remaining 999.22)
**Verified:** 2026-10-25
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria 1-5, cross-checked against VFIX-01..06)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Each closure failure path (one-pass limit, six-row case, `/review` deep-only) has a recorded reproduction verdict on current code before any closure code change | VERIFIED | 56-01-SUMMARY.md and 56-02-SUMMARY.md record verbatim red-run tails (`33 failed` / `13 failed` with the exact `AssertionError` reasons) captured BEFORE score.py/carry_state.py/prose were touched; git log shows the `test(56-0x): add failing …` commits predate every `feat(56-0x)`/`fix(56-0x)` commit |
| 2 | After an inconclusive independent re-check, a later run retries on unchanged repaired code and closes with no code edit and no repeated owner confirmation | VERIFIED | `score.py:1615` applies the previous-pass-only age gate only to `fix-obsolete` (`if not confirmed and v["at_pass"] != pass_number - 1`); `carry_state.py:348-356 _confirmed_fix_awaiting` has no `at_pass` check — `TestRetryAfterInconclusive`/`TestFinalizeCountsConfirmedFix` pass in the independently-run `pytest -q test_confirmed_fix.py` (96 passed) |
| 3 | The six-row case (code beneath an unchanged pinned line, tests-only `arrFacade` fix, four Codex-origin rows) closes via eligible independent evidence with no "fixed in \<sha\>" dismissal, at the card or at close-out | VERIFIED | `test_verified_fixes.py::TestSixRowClosure::test_all_six_close_on_independent_evidence` and `test_carry_state.py::TestSixRowEndToEnd::test_six_row_closure_reaches_write_without_decisions` both pass under an independently-run `pytest -q` (confirmed directly: `pytest -q test_carry_state.py -k SixRowEndToEnd` → `4 passed`); the end-to-end test asserts `"decisions" not in new` and `"fix_verdicts" not in new` |
| 4 | Under `/review`, a `/deep-review`-only finding (e.g. `test-sufficiency`) closes via an eligible independent recheck or shows a clear, bounded explanation | VERIFIED | `test_verified_fixes.py::TestReviewClosesDeepOnlyFinding` (`test_bugs_confirms_test_sufficiency_finding_under_review`, `test_no_confirmer_shows_bounded_reason`) pass; `score.py` `_R_IR_NO_REVIEWER`/`_R_IR_NO_ANSWER` reasons confirmed present and wired into `_independent_recheck` |
| 5 | Safeguards hold: evidence from changed code is rejected as stale, a "still applies" verdict keeps the finding open, and the existing suite stays green | VERIFIED | Independently re-ran the full suite from `plugins/vibe-check/scripts`: **3083 passed, 0 failed (4102 subtests), 270s** — matches 56-REVIEW-FIX.md's claimed gate exactly. Manual adversarial probe (own script, not from the test suite) against a settled `recheck_settled` row with an irrelevant touched path confirmed the record stays open with `_R_IR_SETTLED` rather than closing |

**Score:** 5/5 ROADMAP success criteria verified; 6/6 VFIX-01..06 requirements satisfied (see Requirements Coverage below)

### Code-Review-Fix Closing-Logic Fixes (flagged by the fixer as "requires human verification")

| Finding | Claim | Independent check | Result |
|---------|-------|--------------------|--------|
| CR-01 (still-applies memory lost on kept-open rows) | `_kept_open_rows` now copies `recheck_settled` from the working record `m`, not the carried copy | Read `score.py:392-398` directly: `row.pop("recheck_settled", None); if isinstance(m.get("recheck_settled"), dict): row["recheck_settled"] = m["recheck_settled"]` — matches claim exactly | CONFIRMED |
| CR-02 (any commit clears the still-applies memory) | New `_settled_path` helper restricts fresh-start clearing to the finding's own file, a fingerprinted path, or an associated test | Read `score.py:1316-1322` (`_settled_path`) and `score.py:2177-2186` (call site `relevant = [p for p in touched if _settled_path(...)]`) — matches claim exactly | CONFIRMED |
| WR-03 (still-applies on one route doesn't block another) | `_accept_verdict` now computes `still_on` per route and rejects a resolution with `verdict: contradicted by still-applies` when any other route said still-applies | Read `score.py:1550-1554` (`still_on` dict) and `score.py:1663-1666` (final cross-route check) — matches claim exactly | CONFIRMED |
| WR-06 (`_is_associated_test` matches across directories) | New `_dir_affine` check requires directory affinity, not just basename-stem match | Read `score.py:1296-1306` (`_dir_affine`) and `score.py:1292` (`_is_associated_test` now ANDs `_dir_affine`) — matches claim; ran the full negative/positive case table in `test_wr06_association_needs_directory_affinity` directly (part of the 59-test targeted run, passed) | CONFIRMED |
| SA-01 (NV item closes on one reviewer's word, no code change) | `_independent_recheck` now requires the D-04 trigger for every Needs-verification lead regardless of status, emitting `_R_IR_NV_NO_CHANGE` otherwise | Read `score.py:1427-1434` — the NV-band branch (`if record.get("band") == NV_BAND and not _independent_trigger(...): return None, _R_IR_NV_NO_CHANGE`) precedes and is independent of the `persisted` trigger branch — matches claim exactly; ran `test_sa01_nv_item_closes_on_independent_route_only_after_a_change` directly (passed), and confirmed the six-row test still passes (none of the six rows is NV-banded, consistent with the SUMMARY's stated residual scope) | CONFIRMED |

### m20 Mutant Retarget (owner-flagged concern)

The fixer's note says m20's target moved from `` or touched):`` to `` or relevant):`` because CR-02 renamed the loop variable. Independently confirmed: `score.py:2185` reads `or relevant):` (the only occurrence in the file, `grep -c` = 1), and `test_m20_fresh_start_on_touch_removed` in `test_verified_fixes.py:1491-1497` still targets the exact same conditional branch — the mutation (`or relevant):` → `or False):`) removes the identical "a relevant touched path is a fresh start" guard that the pre-rename mutant removed (`or touched):` → `or False):`). The semantic guard under test is unchanged; only the variable name in the source changed. Ran `test_m20_fresh_start_on_touch_removed` directly as part of the 59-test `TestIndependentRouteMutants` run — passed.

### Owner Decisions Honored

| Decision | Check | Result |
|----------|-------|--------|
| (1) Quiet runs do not dispatch extra re-checks — step 5 of `05-state.md` unchanged since phase start (base `8df9545`) | `diff <(git show 8df9545:…/05-state.md \| sed -n '68p') <(git show HEAD:…/05-state.md \| sed -n '69p')` | IDENTICAL (byte-for-byte; only line-number shift from earlier insertions) |
| (2) Six-row fixture is trimmed real iPlayarr data (paths, titles, minimal fields only; post-fix ~17 KB) | File size confirmed 17,100 bytes (claim: "17 KB"); `problem`/`source_window` fields confirmed emptied (`''`/`[]`); `current_code` confirmed cut to one line on the two rows that have it; real iPlayarr file paths (`src/facade/arrFacade.ts`, `src/endpoints/sabnzbd/AddFileEndpoint.ts`, etc.) and real titles present | CONFIRMED |
| (3, 2026-10-25) Independent-route `resolved` closes a Needs-verification item only when its file or an associated test changed since raised | `score.py:1429-1431` (`_independent_recheck`) — see SA-01 row above | CONFIRMED |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/fixtures/iplayarr45-six-row-state.json` | Trimmed real iPlayarr six-row carry-forward fixture | VERIFIED | 17,100 bytes, 3 passes, 6 findings at pass 3, real file paths/titles, sensitive fields stripped |
| `plugins/vibe-check/scripts/test_verified_fixes.py` | RED→GREEN fixtures, mutant tests, six-row closure tests | VERIFIED | 87 tests, 102 subtests, all pass independently (`pytest -q test_verified_fixes.py`) |
| `plugins/vibe-check/scripts/test_confirmed_fix.py` | P1 reproduction, prose locks, retry-after-inconclusive | VERIFIED | 96 tests, 120 subtests, all pass independently |
| `plugins/vibe-check/scripts/score.py` | `_INDEPENDENT_ROUTE`, `_NEVER_CONFIRMERS`, `_independent_trigger`, `_independent_recheck`, `_settled_path`, `_dir_affine`, `_R_CONTRADICTED`, etc. | VERIFIED | All constants/helpers read directly and confirmed present and wired |
| `plugins/vibe-check/scripts/carry_state.py` | `_confirmed_fix_awaiting` without last-pass requirement, `_settled_unchanged` | VERIFIED | Read directly at lines 328-356; matches claim |
| `plugins/vibe-check/scripts/fixtures/future-schema.json` | `recheck_settled` in `finding_optional` with `phase56_added` rollback entry | VERIFIED | Confirmed via grep: both keys present |
| `plugins/vibe-check/scripts/test_carry_state.py` | `TestSixRowEndToEnd` | VERIFIED | 4 tests present and pass |
| Prose files (`05-state.md`, `20-dispatch.md`, `30-collect-score.md`, `40-render.md`, `90-finalize.md`, `output-format.md`, `review-md-schema.md`) | Independent re-check orchestration, D-03/D-11 wording | VERIFIED | Diffs read directly; needles from CONTEXT/PLAN interfaces blocks confirmed present (`"route": "independent"`, `$TOUCHED_PATHS`, "Fix not yet confirmed:", "fix confirmed by the {{agents}} lane") |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `score.py _accept_verdict` | envelope `head_blobs` | `snapshot_blob == head_blobs[file]` freshness compare | WIRED | Confirmed at `score.py:1439-1442`, `:1457-1460` |
| `score.py` carry loop | envelope `touched_paths` | `_independent_trigger(record, touched, changed_line_ranges)` | WIRED | Confirmed at `score.py:1325-1341`, called from `_independent_recheck`/`_bound_plain_recheck` |
| `score.py FINDING_OPTIONAL_KEYS` | `fixtures/future-schema.json finding_optional` | key-set equality lock | WIRED | `test_state_shape.py::test_phase56_recheck_settled_key_is_optional_under_future_schema` passes |
| `20-dispatch.md` Bind step | `30-collect-score.md` envelope | `route`/`snapshot_blob`/`test_paths`/`fix_commit` | WIRED | Confirmed via diff read; needles present |
| `test_carry_state.py TestSixRowEndToEnd` | `test_verified_fixes.py _pass4_envelope` | import and reuse | WIRED | Test run confirms the cross-module reuse executes without error |

### Behavioral Spot-Checks / Probe Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite is green | `pytest -q` from `plugins/vibe-check/scripts/` (run independently, not reused from SUMMARY/REVIEW-FIX) | `3083 passed, 4102 subtests passed in 270.14s (0:04:30)`, exit 0 | PASS — matches 56-REVIEW-FIX.md's claimed "3083 passed, 0 failed" exactly |
| Targeted closing-logic fixes (CR-01, CR-02, WR-03, WR-06, SA-01, mutants, six-row closure) | `pytest -q test_verified_fixes.py -k "TestReviewFix56 or TestIndependentRouteMutants or TestSixRowClosure or TestSixRowFixtureGuards"` | `59 passed, 28 deselected, 42 subtests passed` | PASS |
| Full `test_verified_fixes.py` | `pytest -q test_verified_fixes.py` | `87 passed, 102 subtests passed` | PASS |
| Full `test_confirmed_fix.py` | `pytest -q test_confirmed_fix.py` | `96 passed, 120 subtests passed` | PASS |
| `TestSixRowEndToEnd` (close-out gate) | `pytest -q test_carry_state.py -k SixRowEndToEnd` | `4 passed` | PASS |
| Adversarial probe: can a still-applies memory be defeated by an unrelated touched path? | Hand-written script calling `score.run()` directly (not from the existing test suite) with a settled record + an irrelevant touched path + a `resolved` verdict | Record stayed open with reason `verdict: fix not confirmed: a reviewer said it still applies and the code is unchanged since` | PASS (safeguard holds) |
| Owner decision 1 regression check | `diff` of `05-state.md` step 5 text, base vs HEAD | Byte-identical | PASS |

No `scripts/*/tests/probe-*.sh` files exist in this repository and none are referenced by the Phase 56 PLAN/SUMMARY/REVIEW files — Step 7c probe execution is not applicable here (the "probes" in this phase's vocabulary are its pytest test classes, which were run above, and `replay.py`, whose output is reported in 56-06-SUMMARY.md and not independently re-run here since it requires a non-trivial allowances file path and does not gate code correctness beyond what the suite run already confirms).

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|--------------|----------------|--------------|--------|----------|
| VFIX-01 | 56-01, 56-02 | Each closure failure path reproduced as a failing fixture before any closure change | SATISFIED | Verbatim red-run tails in 56-01/56-02 SUMMARYs; commit order confirms test-before-fix |
| VFIX-02 | 56-02, 56-04, 56-05 | Inconclusive independent re-check retries on a later run and closes without dummy edit/repeated confirmation | SATISFIED | `score.py` age-gate relaxation + `carry_state._confirmed_fix_awaiting` confirmed by direct code read and passing `TestRetryAfterInconclusive`/`TestFinalizeCountsConfirmedFix` |
| VFIX-03 | 56-01, 56-03, 56-05, 56-06 | Code-beneath-unchanged-line and tests-only fixes close via eligible independent evidence without manual "fixed in \<sha\>" dismissal | SATISFIED | `TestSixRowClosure` + `TestSixRowEndToEnd` pass; end-to-end asserts no `decisions`/`fix_verdicts` root |
| VFIX-04 | 56-01, 56-03, 56-05 | Codex-origin findings close via eligible independent evidence despite Codex being unable to recheck itself | SATISFIED | `CODEX_ROWS` closures in `test_all_six_close_on_independent_evidence` confirmed passing; `_NEVER_CONFIRMERS` frozenset confirmed to include `codex-adversarial` |
| VFIX-05 | 56-01, 56-02, 56-03, 56-05 | Under `/review`, a deep-review-only finding closes via independent recheck or shows a bounded explanation | SATISFIED | `TestReviewClosesDeepOnlyFinding` confirmed passing |
| VFIX-06 | 56-01, 56-03, 56-04, 56-06 | Safeguards hold: stale evidence rejected, still-applies keeps open, suite stays green | SATISFIED | Full independent suite run (3083 passed/0 failed); `TestIndependentRouteSafeguards`, mutant classes, and the hand-written adversarial probe all confirm |

No orphaned requirements: REQUIREMENTS.md maps exactly VFIX-01..06 to Phase 56, and all six appear in the union of the six plans' `requirements:` frontmatter.

### Anti-Patterns Found

None blocking. Scanned every file touched since phase base (`8df9545..HEAD`) for `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`/empty-implementation patterns. The only `XXX` hits are pre-existing `mktemp "${TMPDIR:-/tmp}/vc.XXXXXX"` template placeholders in `90-finalize.md` (unrelated to debt markers), and the only `placeholder` hits are the pre-existing `_NV_PLACEHOLDERS` domain vocabulary in `score.py` (legitimate first-line-placeholder detection logic, not a stub). No debt markers were introduced by this phase.

### Human Verification Required

None. All ROADMAP success criteria and all must-haves resolved to VERIFIED through direct code reading, independent test execution (not reused from SUMMARY/REVIEW-FIX claims), and one adversarial probe constructed outside the existing test suite. The five closing-logic fixes the code-fixer flagged as "requires human verification (logic)" (CR-01, CR-02, WR-03, WR-06, SA-01) were each independently read in `score.py` and found to match the claimed implementation exactly, and their regression tests were run directly rather than trusted from the report.

### Gaps Summary

No gaps. The phase goal — independent evidence closing a fix without a dummy code change or repeated owner confirmation, while rejecting stale evidence and keeping still-applicable findings open — is observably true in the current codebase:

- The full test suite (3083 tests) passes cleanly when run independently.
- Each of the five critical/warning closing-logic defects found by code review (CR-01, CR-02, WR-03, WR-06, SA-01) has a corresponding code fix that was read directly in `score.py` and confirmed to match its stated mechanism, not merely claimed in a report.
- The six-row owner scenario (code beneath unchanged pinned line, tests-only fix, four Codex-origin rows) closes end-to-end through `append_pass` → `finalize_counts` → the Finalize `write` gate with no `decisions` or `fix_verdicts` root, confirmed by directly running `TestSixRowEndToEnd`.
- All three owner decisions (quiet-run no-dispatch, real-trimmed fixture, NV-item-needs-a-change) were independently checked against the code/fixture rather than taken on the report's word.
- One deferred item (SA-02, plain-request `snapshot_blob` not enforced for `needs-recheck` records) was independently confirmed to be pre-existing behavior at the phase base commit (`8df9545`), not a regression introduced by Phase 56 — the owner's deferral classification is accurate.
- The m20 mutant-test rename (`or touched):` → `or relevant):`) was independently confirmed to still target the identical semantic guard.

---

_Verified: 2026-10-25_
_Verifier: Claude (bm-verifier)_
