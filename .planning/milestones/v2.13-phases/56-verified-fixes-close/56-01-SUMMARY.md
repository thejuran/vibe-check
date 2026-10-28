---
phase: 56-verified-fixes-close
plan: 01
subsystem: scorer closure tests (reproduce-first)
tags: [reproduce-first, fixture, score, closure]
requires: []
provides:
  - "fixtures/iplayarr45-six-row-state.json (trimmed real iPlayarr phase-45 passes 1-3, six-row lineage)"
  - "test_verified_fixes.py: RED fixtures for P2a/P2b/P2c/P3 and the independent-route safeguards (VFIX-06)"
affects: [56-03 (must turn these GREEN without weakening them), 56-06 (end-to-end over the same fixture)]
tech-stack:
  added: []
  patterns: ["replay-from-real-state fixture (phase45-loop-state pattern)", "literal reason-string contract pinned in tests"]
key-files:
  created:
    - plugins/vibe-check/scripts/fixtures/iplayarr45-six-row-state.json
    - plugins/vibe-check/scripts/test_verified_fixes.py
  modified: []
decisions:
  - "Contract reason strings are pinned as literals in the test module (plus a getattr-vs-literal constants test) instead of getattr-in-every-assertion, so a renamed constant in 56-03 is caught"
  - "Fixture guard class TestSixRowFixtureGuards added: without verdicts all six rows (and the 0249b52c bugs/impact members) stay open, so 'no row left at the six sites' can never pass vacuously (mutation-checked)"
  - "Pitfall 2 IS reachable at score level: a bound plain request to codex-adversarial on a needs-recheck record closes it today (test_never_confirmers_rejected bound-plain subTest)"
metrics:
  duration: "~12 min"
  completed: 2026-10-23
  tasks: 4
  files: 2
---

# Phase 56 Plan 01: Reproduce-first closure fixtures Summary

Real iPlayarr six-row state trimmed into a schema-clean fixture, plus 35 score-level tests: 22 RED on HEAD for the reproduced reasons (`verdict: malformed`, `verdict: record not needs-recheck`, missing contract reasons) and 13 that are green today and must stay green. No score.py, carry_state.py or prose change.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Six-row fixture from real iPlayarr state | 7b7f0d3 | fixtures/iplayarr45-six-row-state.json |
| 2 | Six-row RED fixtures (P2a, P2b, P2c) | d4c7822 | test_verified_fixes.py |
| 3 | /review deep-only RED fixture (P3) | ef1c83f | test_verified_fixes.py |
| 4 | Independent-route safeguard negatives (VFIX-06) | 03087a0 | test_verified_fixes.py |

## Reproduction verdicts

| Path | Verdict | Failing layer on HEAD | Evidence (observed red-run reason) |
|------|---------|-----------------------|------------------------------------|
| P2a code added beneath an unchanged pinned line (`2a01829c`, persisted) | **REPRODUCED** | `score.py` `_accept_verdict` `status != "needs-recheck"` | `2a01829c not resolved; rejections: ['verdict: record not needs-recheck']` — identical to the 2 real rejections per pass in the fixture |
| P2b tests-only `arrFacade` fix (`7bc336e7`, persisted) | **REPRODUCED** | same gate | `7bc336e7 not resolved; rejections: ['verdict: record not needs-recheck']` |
| P2c four Codex-origin rows (`3dd41363`, `0249b52c`, `a264e9e9`, `22d360d9`) | **REPRODUCED** | no route kind for an independent confirmer; members persisted | `3dd41363 not resolved; rejections: ['verdict: malformed' x4, 'verdict: unrequested token' x4, 'verdict: record not needs-recheck' x2]` (the two persisted members of `0249b52c`) |
| P3 `/review` cannot close a deep-only finding | **REPRODUCED** | no route kind; no D-11 reason | `['verdict: malformed', 'verdict: unrequested token'] != []`; no-confirmer case: `[] != ['verdict: fix not yet confirmed: no eligible reviewer ran this pass']` |

P1 (one-pass NV limit) is not owned by this plan.

### Verbatim red-run tail (`pytest -q test_verified_fixes.py`, HEAD 03087a0)

```
FAILED test_verified_fixes.py::TestSixRowClosure::test_all_six_close_on_independent_evidence
FAILED test_verified_fixes.py::TestSixRowClosure::test_code_beneath_unchanged_line_closes_via_file_touch
FAILED test_verified_fixes.py::TestSixRowClosure::test_codex_rows_close_via_ladder_confirmer
FAILED test_verified_fixes.py::TestSixRowClosure::test_commit_sha_recorded_when_supplied
FAILED test_verified_fixes.py::TestSixRowClosure::test_fix_outside_pinned_file_still_closes_needs_recheck_row
FAILED test_verified_fixes.py::TestSixRowClosure::test_nearby_change_triggers_without_a_touching_commit
FAILED test_verified_fixes.py::TestSixRowClosure::test_no_decisions_needed - ...
FAILED test_verified_fixes.py::TestSixRowClosure::test_persisted_codex_blank_line_needs_trigger
FAILED test_verified_fixes.py::TestSixRowClosure::test_tests_only_fix_closes_via_associated_test
FAILED test_verified_fixes.py::TestSixRowClosure::test_tests_only_fix_needs_the_association
FAILED test_verified_fixes.py::TestReviewClosesDeepOnlyFinding::test_bugs_confirms_test_sufficiency_finding_under_review
FAILED test_verified_fixes.py::TestReviewClosesDeepOnlyFinding::test_needs_recheck_row_closes_without_trigger
FAILED test_verified_fixes.py::TestReviewClosesDeepOnlyFinding::test_no_confirmer_shows_bounded_reason
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_changed_code_is_stale
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_member_closes_only_bound
SUBFAILED(shape='bound plain', agents=['codex-adversarial']) test_verified_fixes.py::TestIndependentRouteSafeguards::test_never_confirmers_rejected
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_null_head_blob_is_inconclusive
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_null_snapshot_is_inconclusive
SUBFAILED(name='_INDEPENDENT_ROUTE') ...::test_reason_constants_match_contract
SUBFAILED(name='_NEVER_CONFIRMERS') ...::test_reason_constants_match_contract
SUBFAILED(name='_NEARBY_LINES') ...::test_reason_constants_match_contract
SUBFAILED(name='_R_IR_NO_REVIEWER') ...::test_reason_constants_match_contract
SUBFAILED(name='_R_IR_NO_ANSWER') ...::test_reason_constants_match_contract
SUBFAILED(name='_R_IR_STILL') ...::test_reason_constants_match_contract
SUBFAILED(name='_R_IR_SNAPSHOT') ...::test_reason_constants_match_contract
SUBFAILED(name='_R_IR_NO_TRIGGER') ...::test_reason_constants_match_contract
SUBFAILED(name='_R_IR_SETTLED') ...::test_reason_constants_match_contract
SUBFAILED(name='_R_CF_SETTLED') ...::test_reason_constants_match_contract
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_settled_row_not_reasked_on_unchanged_code
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_settled_row_reasked_after_code_change
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_silent_reviewer_keeps_open
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_still_applies_contradicts_resolved_on_independent
FAILED test_verified_fixes.py::TestIndependentRouteSafeguards::test_still_applies_keeps_open_and_settles
33 failed, 13 passed, 3 subtests passed in 0.45s
```

(pytest-subtests counts each SUBFAILED in "failed" and still reports the parent as PASSED: 35 test functions = 22 RED (20 FAILED + 2 RED only through subtests) + 11 green-by-design + those 2 parents.)

### Per-test failure reasons (observed, all `AssertionError`; 0 TypeError/KeyError/AttributeError/ImportError/NameError)

| Test | Observed failure |
|------|------------------|
| all_six_close | `['verdict: malformed', ... 'verdict: record not needs-recheck'] != []` |
| code_beneath (P2a) / nearby_change | `2a01829c not resolved; rejections: ['verdict: record not needs-recheck']` |
| tests_only (P2b) | `7bc336e7 not resolved; rejections: ['verdict: record not needs-recheck']` |
| tests_only_needs_association | no-trigger reason `not found in ['verdict: record not needs-recheck']` |
| codex_rows (P2c) | `3dd41363 not resolved; rejections: ['verdict: malformed' ...]` |
| persisted_codex_blank_line | no-trigger reason `not found in ['verdict: malformed']` |
| fix_outside_pinned_file / commit_sha | `... not resolved; rejections: ['verdict: malformed', 'verdict: unrequested token']` |
| no_decisions_needed | all six missing from resolved; rejections list malformed / record not needs-recheck |
| bugs_confirms_ts (P3) / needs_recheck_closes | `['verdict: malformed', 'verdict: unrequested token'] != []` |
| no_confirmer_shows_bounded_reason | `[] != ['verdict: fix not yet confirmed: no eligible reviewer ran this pass']` |
| changed_code / null_snapshot / null_head_blob | `['verdict: malformed', 'verdict: unrequested token'] != [<the reviewed code is not the code at HEAD>]` |
| still_applies_keeps_open / contradicts | malformed instead of `... says it still applies` (and no `recheck_settled`) |
| settled_not_reasked | malformed instead of `... a reviewer said it still applies and the code is unchanged since` |
| settled_reasked | `['verdict: malformed', 'verdict: unrequested token'] != []` |
| silent_reviewer | `['verdict: malformed'] != [<the routed reviewer gave no verdict>]` |
| member_closes_only_bound | bound half: `0 != 1 : rejections: ['verdict: record not needs-recheck']` |
| never_confirmers (bound-plain subTest) | `'resolved' unexpectedly found` — codex-adversarial closes a needs-recheck row today |
| reason_constants | `'<missing>' != <contract value>` for all 10 names |

## Acceptance checks (each run individually)

- Task 1 `<verify>` python one-liner: printed `['medium_acknowledgments', 'passes']`, `[]`, all asserts passed. `grep -c '"verdict: record not needs-recheck"'` → `12`. Pass 1 holds the lineage incl. `2c4fbd66`, `14c1c286`; `22d360d9` canonical `""`; `7bc336e7` passes 2/3 keep `kept_open`; no `needs_verification` on `2a01829c`. Secret-pattern grep (api key/password/secret/token/bearer) → `0`.
- Task 2: `pytest -q test_verified_fixes.py -k TestSixRowClosure` → `10 failed, 3 passed`; `grep -c expectedFailure` → `0`; all six FIX_COMMITS equal `git -C /Users/julianamacbook/iplayarr rev-parse <prefix>` (6 OK).
- Task 3: `-k TestReviewClosesDeepOnlyFinding` → `3 failed, 3 passed` (6 collected; green: ts_row_shape, absent_when_not_eligible, absent_without_head_blobs); `grep -c "def _review_pass2"` → `1`.
- Task 4: `-k TestIndependentRouteSafeguards` collects 13 tests; module total 35 (>= 28). `grep -o '"verdict: fix not [a-z :,]*"' | sort -u` is identical to the same grep over the plan's interfaces block (SAME-SET); a case-sensitive grep also matches all 7 strings incl. `_R_IR_SNAPSHOT` (contains `HEAD`) and `_R_CF_SETTLED`.
- Full suite `pytest -q`: `33 failed, 2977 passed, 3931 subtests passed in 229.47s`; all 33 failure lines are in `test_verified_fixes.py` (0 elsewhere). 2977 = 2964 baseline + 13.
- `git diff` of this plan touches only the two `files_modified` paths (score.py / carry_state.py unchanged).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Resolved-hash set assertion would crash on member resolutions**
- **Found during:** Task 2
- **Issue:** the plan's `{x["stable_hash"][:8] for x in r["resolved"]} == set(SIX)` raises TypeError once members resolve (a member without an obligation reports `stable_hash: null`, as the real pass-2 `resolved[]` shows).
- **Fix:** compare the set over string hashes only, and separately assert the two `0249b52c` member resolutions (`bugs`, `impact`).
- **Cost if wrong:** 56-03 would fight a crash, not a contract.
- **Commit:** d4c7822

**2. [Rule 2 - Missing guard] Fixture guard class**
- **Found during:** Task 2
- **Issue:** `_rows_at_six_sites(r) == []` could pass vacuously if the rows fell below threshold.
- **Fix:** `TestSixRowFixtureGuards` (3 green tests); mutation-checked: nulling one lead's HEAD read makes the guard fail. Lives outside `TestSixRowClosure`, so that class still reports exactly 3 passed.
- **Cost if wrong:** none; extra green tests.
- **Commit:** d4c7822

**3. [Rule 1 - Bug] `_review_pass2` member HEAD reads**
- **Found during:** Task 4
- **Issue:** the row's own member ref had no `canonical_line_content`, so a spurious fixed-since-last stub appeared in every /review envelope.
- **Fix:** set each member's canonical to the lead's (same recipe as `_p45_carryforward`).
- **Commit:** 03087a0

**4. [Rule 1 - Contradiction] `test_settled_row_reasked_after_code_change` case (a)**
- **Found during:** Task 4
- **Issue:** the plan's case (a) ("same" as not-reasked: persisted, `touched_paths` empty, far ranges) plus blob B2 expects closure, but the interfaces require a trigger for a persisted record, so 56-03 could not make it GREEN without breaking the no-trigger tests.
- **Fix:** case (a) uses a needs-recheck row (no trigger needed) with the blob changed to B2 and `touched_paths` empty, isolating "fingerprint differs → fresh start". Case (b) (new touching commit, unchanged blob, persisted) is as planned.
- **Cost if wrong:** if the owner intended a blob change alone to trigger a persisted record, 56-03 would need an extra trigger leg; the test can be widened then.
- **Commit:** 03087a0

**5. [Rule 2] Contract strings asserted as literals**
- **Issue:** the plan asked for `getattr(score, name, "<missing>")` in assertions; that would let 56-03 pass with any spelling it chose.
- **Fix:** literal constants in the test module (they also satisfy the Task-4 grep), plus `test_reason_constants_match_contract` comparing `getattr(score, ...)` with each literal.
- **Commit:** 03087a0

## Assumption Drift (advisory)

- **Codex lead `current_code`:** planned "`current_code: null`"; actual: the key is ABSENT on the Codex leads in the real state (the scorer reads it via `.get`, so equivalent). Kept the real shape rather than inventing a key. Found during Task 1. Cost if wrong: none for the scorer; a reader that requires the key would differ.
- **Scrub test:** `test_recheck_settled_scrubbed_from_new_findings` is GREEN today (the output shaper drops the unknown key); it becomes a real guard once 56-03 adds `recheck_settled` to the known finding keys.
- **Independent-route stable_hash test:** GREEN today because the route itself is unknown (`malformed`); it stays green after for the right reason.
- **Pitfall 2 reachability:** RESEARCH said a `codex-adversarial` confirmer on the plain path is unreachable (prose never issues it). At score level it is reachable: a bound plain request naming `codex-adversarial` closes a needs-recheck row today. The plan scoped the bound-plain exclusion in, so the subTest pins it RED.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register (T-56-01 accepted: fixture holds owner-approved real paths, titles, problem text and member records; `why_it_matters`/`fix_hint`/`needs_verification`/`cwe` dropped from leads, members kept whole per the MEMBER_KEYS contract).

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/fixtures/iplayarr45-six-row-state.json
- FOUND: plugins/vibe-check/scripts/test_verified_fixes.py
- FOUND commits: 7b7f0d3, d4c7822, ef1c83f, 03087a0
