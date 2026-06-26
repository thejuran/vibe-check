---
phase: 20-crash-proof-the-core
plan: 02
subsystem: testing
tags: [test_score.py, vibe-check, regression-lock, malformed-input, fail-closed, stdlib-only, golden-digest]

# Dependency graph
requires:
  - phase: 20-crash-proof-the-core
    plan: 01
    provides: "the Wave-1 score.py guards these tests LOCK — _valid_finding (non-dict reject), _safe_window (str-element coercion), import-free non-finite confidence guard, envelope fail-closed list-guard — plus the exact reject-reason vocabulary 'malformed: non-dict finding'"
provides:
  - "TestMalformedInputMatrix — the T1-T21 malformed-shape regression suite that pins each crash class's post-hardening outcome (REJECT-to-filtered / KEPT-and-degraded / envelope-fail-closed / valid-empty-review), never merely 'did not raise'"
  - "Gap A: timeout= on every TestFailClosed + black-box subprocess.run call so a hung scorer child fails the test instead of stalling the suite (T-20-05)"
  - "Gap C: a single module-level GOLDEN_DIGEST literal constant (frozen value preserved byte-for-byte, NOT recomputed) referenced by both golden-digest tests (T-20-06)"
  - "Gap B: the two flagged loose 'no-crash-only' assertions tightened to assert the KEPT outcome (finding survives in result['findings'])"
affects: [phase 21 (test-sufficiency agent whose findings pipe through this now-regression-locked scorer)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "2-finding envelope per malformed case (the shape + a high-confidence good sibling) asserting BOTH the shape's disposition AND D-03 no-good-sibling-drop"
    - "subTest fan-out over a shape family (str/None/list/int; NaN/Inf/-Inf; {}/''/0) so one test method pins a whole equivalence class with per-shape failure isolation"
    - "Single source-of-truth frozen literal hoisted to a module constant (GOLDEN_DIGEST) — independently hard-coded, never recomputed (anti-tautology, Pitfall 4)"
    - "Black-box exit-code assertion (subprocess.run on score.py with timeout=) mirrors TestFailClosed to prove the envelope fail-closed raise propagates to a non-zero process exit"

key-files:
  created: []
  modified:
    - "plugins/vibe-check/scripts/test_score.py — +GOLDEN_DIGEST constant, +timeout= on both TestFailClosed calls, tightened 2 loose assertions, +TestMalformedInputMatrix (17 new test methods covering T1-T21) (+300/-4 net across two commits)"

key-decisions:
  - "Followed the 20-01-SUMMARY alignment note (authoritative) over the 20-02 PLAN's T-row paraphrase where they differ: T6/T7/T8 (missing file/title/category) and T9 (empty {} dict) are KEPT-shapes, NOT malformed-rejects — score.py is null-safe for those fields and _valid_finding rejects ONLY a non-dict container. Asserting them as rejects would have contradicted the live code + two frozen tests."
  - "T21 (non-finite confidence) asserts the finding is NOT in result['findings'] (it scores 0+20=20 < 70 deep-review threshold -> sub-threshold-filtered), NOT present. The plan's own Task-2 probe over-asserted this (flagged in 20-01-SUMMARY Deviation 2); the test asserts the mathematically-true outcome: no-crash + scored-exactly-as-confidence-0 + sibling survives."
  - "New cases live in a dedicated TestMalformedInputMatrix class (not extending the existing robustness classes) so the T1-T21 matrix reads as one self-documenting regression block with a HARDEN-02 banner, matching the file's class-per-concern convention."
  - "Golden digest de-dup hoists to an independently hard-coded literal, NOT score.stable_hash(...) (which would make the freeze tautological) and NOT a re-pin (it keys persisted dismissals). Frozen value 7a516d...793124 preserved byte-for-byte; appears exactly once in non-comment code."

requirements-completed: [HARDEN-02]

# Metrics
duration: ~10min
completed: 2026-06-26
---

# Phase 20 Plan 02: Crash-Proof the Core (test_score.py malformed-shape pinning) Summary

**The T1-T21 malformed-shape regression suite that LOCKS the Wave-1 score.py crash guards plus the three v2.4-dogfood hygiene fixes (subprocess timeouts, single GOLDEN_DIGEST constant, tightened loose assertions) — every dogfood-named crash class and the two adversarial-found holes now have an explicit case asserting the post-hardening OUTCOME (skip+report / kept-and-degraded / fail-closed / valid-empty), not merely "did not raise"; the full suite is 140 tests green (123 prior + 17 new), score.py untouched, the golden digest frozen value preserved.**

## Performance
- **Duration:** ~10 min across the two task commits.
- **Completed:** 2026-06-26T22:23Z
- **Tasks:** 2
- **Files modified:** 1 (`plugins/vibe-check/scripts/test_score.py`)
- **Test count:** 123 -> **140** (17 new test methods; several fan out over shape families via `subTest`)

## Accomplishments

### Task 1 — the three HARDEN-02 hygiene gaps (commit `e478fb6`)
- **Gap A (DoS bound, T-20-05):** added `timeout=30` to BOTH `TestFailClosed` `subprocess.run` calls (`test_invalid_json_stdin_exits_nonzero`, `test_empty_stdin_exits_nonzero`) so a hung scorer child fails the test instead of stalling the suite/CI.
- **Gap C (freeze integrity, T-20-06):** hoisted the frozen golden sha256 to ONE module-level `GOLDEN_DIGEST = "7a516d...793124"` literal constant near the top of the file; referenced it from `test_golden_digest_frozen` AND `test_new_golden_digest_pinned` (each keeps its distinct intent docstring). The literal is independently hard-coded — NOT recomputed via `score.stable_hash(...)` (tautology) and NOT re-pinned (it keys persisted dismissals). The 64-hex literal now appears exactly ONCE in non-comment code.
- **Gap B (outcome assertions):** tightened the two flagged loose tests — `test_numeric_current_code_finding_flows_through_run` and `test_null_line_finding_flows_through_run_without_raising` — to assert the KEPT outcome (`assertIn(id, result["findings"])`), modeled on `test_all_mode_null_line_not_in_reviewed_set`, rather than only `scored_by_script` truthy.

### Task 2 — the T1-T21 malformed-shape matrix (commit `3520f7d`)
New `TestMalformedInputMatrix` class (HARDEN-02 banner). Each per-finding case feeds a 2-finding envelope (the malformed shape + a high-confidence good `keep` sibling) and asserts BOTH the shape's disposition AND that the good sibling survives (D-03 no-good-sibling-drop):
- **REJECT (non-dict container):** T1-T4 findings (str/None/list/int) and T5 carryforward (str/None/list) route to `result["filtered"]` with a `"malformed"` reason; the malformed entry is absent from `findings`; good sibling (and good carryforward) survive. (C1/C2)
- **KEPT (null-safe, NOT a reject):** T6/T7/T8 missing `file`/`title`/`category` survive in `findings` and assert NO `"malformed"` reason; T9 empty `{}` dict flows through `_valid_finding` (a dict) and is NOT a malformed-reject. (Aligned to 20-01 orchestrator correction.)
- **KEPT-and-degraded:** T10 odd line types (str/float/bool), T11 `source_window=99`, T12 `source_window` str/dict, T13 numeric `current_code` (sibling variant), all survive with no crash; **T20** `source_window=[1,2,3]` (a genuine list with non-string elements — HOLE 1) is KEPT with `silenced=False`; **T21** `agent_confidence=float('nan')/float('inf')/float('-inf')` (HOLE 2, produced at runtime not as literals) does NOT crash and scores exactly as confidence 0.
- **Envelope FAIL CLOSED:** T14 (`findings={...}`), T15 (truthy non-list `"oops"`/`5`/`{"x":1}`), T16 (the critical C6 falsy `{}`/`""`/`0`), T17 (non-list `carryforward`) all assert `score.run` raises; plus a black-box subprocess test (`test_t16_black_box_non_list_findings_exits_nonzero`) asserting `python3 score.py` exits non-zero on non-list-findings stdin, WITH `timeout=`.
- **VALID empty review:** T18 (empty `{}` envelope) and T19 (findings absent / explicitly None) assert `scored_by_script` True and `findings == []`, no raise.

## Task Commits
1. **Task 1: Hygiene fixes (Gap A/B/C)** — `e478fb6` (test)
2. **Task 2: T1-T21 malformed-shape matrix** — `3520f7d` (test)

## Files Created/Modified
- `plugins/vibe-check/scripts/test_score.py` — added `GOLDEN_DIGEST` module constant, `timeout=30` on both `TestFailClosed` subprocess calls, tightened `test_numeric_current_code_finding_flows_through_run` + `test_null_line_finding_flows_through_run_without_raising` to assert the kept outcome, and the new `TestMalformedInputMatrix` (17 test methods, T1-T21). `score.py` UNCHANGED; STATE.md/ROADMAP.md NOT touched (orchestrator owns those).

## Deviations from Plan

### 1. [Rule 1 - Plan/handoff alignment] T6/T7/T8 and T9 asserted as KEPT, not REJECT
- **Found during:** Task 2 (building the per-finding matrix).
- **Issue:** The 20-02 PLAN's Task-2 `<action>` groups T6/T7/T8 (missing file/title/category) and T9 (empty `{}`) under "PER-FINDING REJECT cases (T1-T9)" and says to assert a `"malformed"` filtered reason naming the key. But the 20-01-SUMMARY alignment note (declared AUTHORITATIVE by the handoff) and the live `score.py` show `_valid_finding` rejects ONLY a non-dict container; missing/null required keys are null-safe and flow through to scoring (two frozen tests already lock null-title/null-category survival). Asserting them as rejects would have failed against the real code.
- **Fix:** Followed the SUMMARY + live code. T6/T7/T8 assert the finding is KEPT in `result["findings"]` with NO `"malformed"` reason; T9 (a dict) asserts it is NOT a malformed-reject. Verified by direct probe against the hardened `score.py` before writing the assertions.
- **Files modified:** plugins/vibe-check/scripts/test_score.py (test-only; no code change).
- **Committed in:** `3520f7d`.

### 2. [Rule 1 - Plan-probe defect carried forward] T21 NaN finding asserted NOT in findings
- **Found during:** Task 2 (T21 case).
- **Issue:** The plan's own Task-2 behavior/probe text could be read as "the NaN finding is KEPT in result['findings']". The 20-01-SUMMARY (Deviation 2) already flagged this as mathematically incompatible: a non-finite confidence coerces to 0, so an in-diff critical finding scores 0+20=20, BELOW the deep-review threshold of 70 — it is sub-threshold-filtered, NOT in `findings`.
- **Fix:** Asserted the true outcome: `score.run` does NOT raise, the NaN/Inf/-Inf finding is NOT in `result["findings"]`, `compute_score(...non-finite...) == compute_score(...confidence=0...)` (proving "scored exactly as 0"), and the high-confidence sibling survives. "Kept" is asserted as "no-crash + scored-as-0", per the handoff override.
- **Files modified:** plugins/vibe-check/scripts/test_score.py (test-only; no code change).
- **Committed in:** `3520f7d`.

**Total deviations:** 2 (both Rule 1 — aligning assertions to the authoritative 20-01-SUMMARY + live code over the PLAN's looser/over-asserting paraphrase). No scope change; no code change to score.py; no existing assertion loosened; golden value unchanged.

## Issues Encountered
- A first run errored (14 errors) from a `make_finding() got multiple values for keyword argument 'id'` kwarg collision: `_good_sibling` passed `id="keep"` as a positional default while callers also passed `id=` via `**over`. Fixed by building a `defaults` dict and `.update(over)` so an overridden `id` wins. Suite then 140 OK. (Caught and fixed before the Task 2 commit.)
- `.planning/` is gitignored in this repo; the plan/research/patterns files live only in the main checkout (not copied into the worktree), so they were read from the main repo absolute paths. This SUMMARY is force-added to commit it (mirroring how 20-01-SUMMARY is tracked).

## Known Stubs
None. The change is purely additive regression-test coverage; no placeholder data, no unwired components.

## Threat Flags
None. This plan adds regression locks that REMOVE the risk of a silent re-opening of the C1-C6 + HOLE-1/HOLE-2 crash surface. The threat register's T-20-05/06/07/08 are all `mitigate` dispositions now satisfied; T-20-SC (`accept`) is N/A (zero package installs; `test_score.py` is stdlib-only).

## Self-Check: PASSED
- FOUND: `.planning/phases/20-crash-proof-the-core/20-02-SUMMARY.md`
- FOUND: `plugins/vibe-check/scripts/test_score.py`
- FOUND commit `e478fb6` (Task 1), `3520f7d` (Task 2)
- `cd plugins/vibe-check/scripts && python3 -m unittest` -> 140 tests OK (exit 0)
- Golden digest literal appears exactly ONCE in non-comment code as `GOLDEN_DIGEST = "7a516d...793124"` (frozen value preserved)
- score.py UNCHANGED across both commits; STATE.md/ROADMAP.md NOT modified (orchestrator owns those)

---
*Phase: 20-crash-proof-the-core*
*Completed: 2026-06-26*
