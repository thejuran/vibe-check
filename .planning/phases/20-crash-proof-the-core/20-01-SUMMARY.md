---
phase: 20-crash-proof-the-core
plan: 01
subsystem: testing
tags: [score.py, vibe-check, input-validation, defensive-hardening, fail-closed, stdlib-only]

# Dependency graph
requires:
  - phase: 16-deterministic-core-script
    provides: score.py deterministic scorer (run/compute_score/silenced_nearby) + the frozen golden digest + the AST import-ban test
  - phase: 17-robustness-on-the-core
    provides: the in-file coerce-or-skip defensive idiom (_as_line, _first_line, stable_hash None-safety) the new guards mirror
provides:
  - "_valid_finding(member) container guard — rejects ONLY non-dict findings/carryforward (C1/C2 crash fix), returns (False, \"malformed: non-dict finding\") | (True, None)"
  - "ingress malformed filter in run() covering BOTH raw findings AND carryforward before either loop, routing rejects to the existing filtered bucket with guarded accessors (Pitfall 2)"
  - "_safe_window(x) field coercion — keeps only the STRING elements of a list else [] (fixes C3 container crash AND HOLE 1 element crash in silenced_nearby)"
  - "import-free non-finite agent_confidence guard (-1e308 < raw_conf < 1e308) in compute_score (HOLE 2: NaN/Infinity coerce to 0 instead of crashing int())"
  - "envelope-level fail-closed list-guard (D-02): isinstance(...,list) on raw findings/carryforward BEFORE the `or []` coercion, raising on a present-but-non-list value (truthy OR falsy)"
affects: [phase 20-02 (authors the malformed-shape pinning test suite that LOCKS these guards), phase 21 (test-sufficiency agent whose findings pipe through this hardened scorer)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Container-level coerce-or-skip guard (_valid_finding) — the _as_line field idiom raised one level to the finding dict itself"
    - "Field coercion that filters to the SAFE element type (_safe_window keeps only str elements), so the downstream consumer (silenced_nearby) stays a pure substring scan over strings"
    - "Import-free non-finite float guard via a bounded comparison (-1e308 < x < 1e308) — NaN/Infinity rejection WITHOUT import math, preserving the {json,hashlib,re,sys} import set"
    - "Envelope fail-closed list-guard placed BEFORE the `or []` coercion so a FALSY non-list cannot be silently masked into a fake 0-findings clean review"

key-files:
  created: []
  modified:
    - "plugins/vibe-check/scripts/score.py — _valid_finding + ingress filter, _safe_window + consumption swap, non-finite confidence guard, envelope fail-closed guard (+122/-3 net)"

key-decisions:
  - "_valid_finding rejects ONLY non-dict members. Per orchestrator correction (mid-execution), missing/None/non-str file/title/category is NOT a malformed-reject — score.py is already null-safe for those fields (stable_hash/_first_line coerce None->\"\") and two frozen tests deliberately assert such findings SURVIVE. Rejecting them was out-of-scope policy tightening that broke deliberate behavior; the 'keep 123 green' constraint won over the earlier (now-corrected) 'non-str required key = malformed' ruling."
  - "Non-finite confidence guard is import-free (-1e308 < raw_conf < 1e308), NOT math.isfinite — adding `import math` would fail the AST import-ban test (TestImportSet, ALLOWED={json,hashlib,re,sys})."
  - "Envelope guard scope is findings/carryforward ONLY (D-02 literal scope); changed_line_ranges/reviewed_union/file_line_totals stay unguarded (orchestrator-controlled context)."
  - "_safe_window/_valid_finding bad-input paths are KEPT-and-degraded, not rejects: a bad window => silenced=False (finding kept); a non-finite confidence => scored as 0 (finding kept). Only a non-dict container is a reject; only a present-but-non-list ENVELOPE fails closed."

patterns-established:
  - "Pattern: container guard mirrors the field guard one level up (_valid_finding ~ _as_line)"
  - "Pattern: coerce at a single chokepoint to the type the consumer assumes (_safe_window -> str-only list -> silenced_nearby pure substring scan)"
  - "Pattern: validate envelope shape BEFORE the falsy-coalescing `or []` so falsy-non-list cannot mask as empty"

requirements-completed: [HARDEN-01]

# Metrics
duration: ~3min (execution); full session longer due to mid-plan policy checkpoint
completed: 2026-06-26
---

# Phase 20 Plan 01: Crash-Proof the Core (score.py defensive hardening) Summary

**Five stdlib-only defensive guards on `score.py` so a single malformed agent finding can no longer hard-crash a review run: a `_valid_finding` non-dict container guard + ingress filter, a `_safe_window` string-element coercion (C3 + HOLE 1), an import-free non-finite `agent_confidence` guard (HOLE 2), and an envelope fail-closed list-guard (C4/C5/C6, D-02) — all 123 existing tests stay green, formula/banding/thresholds/golden-digest untouched.**

## Performance

- **Duration:** ~3 min between the two task commits (18:10:43 -> 18:13:23 local); total session wall-clock longer due to a mid-plan checkpoint (see Deviations).
- **Started:** 2026-06-26T22:00Z (approx, plan load)
- **Completed:** 2026-06-26T22:13:53Z
- **Tasks:** 2
- **Files modified:** 1 (`plugins/vibe-check/scripts/score.py`, +122/-3 net)

## Accomplishments
- `_valid_finding(member)` + ingress malformed filter: a non-dict finding OR carryforward entry (str/None/list/int) is skipped-and-reported to the existing `filtered` bucket and never reaches the crash-prone `.get` paths (C1 in `cross_confirm_group`/`_score_member`, C2 upstream at `cf.get(...)`). Good siblings survive. Reject accessors are guarded with `isinstance(m, dict)` (Pitfall 2) so the defensive code does not re-introduce the AttributeError.
- `_safe_window(x)` field coercion + `_score_member` consumption swap: closes BOTH the container crash (C3 — `source_window=99` -> `TypeError: 'int' object is not iterable`) AND the element crash (HOLE 1 — `source_window=[1,2,3]` -> `marker in 1` `TypeError`) by keeping only the string elements of a list. Mixed windows like `['real line', 7, None, '# noqa: x']` still detect the marker (silenced=True) over their string elements; str/dict windows normalize to "no window" (silenced=False). KEPT-and-degraded — never a reject.
- Import-free non-finite `agent_confidence` guard in `compute_score`: `NaN`/`Infinity`/`-Infinity` (bare floats `json.load` accepts that pass the `isinstance(int,float) and not bool` check) now coerce to 0 via the bounded comparison `-1e308 < raw_conf < 1e308` instead of crashing `int()` (HOLE 2 — was `ValueError`/`OverflowError`). No `import math`; the AST import-ban test stays green.
- Envelope fail-closed list-guard (D-02): `isinstance(..., list)` on the RAW `findings`/`carryforward` BEFORE the `or []` coercion. A present-but-non-list value raises `TypeError("malformed envelope: '<key>' must be a list, got <type>")` — for TRUTHY non-lists (C4/C5) and, critically, FALSY non-lists (`{}`/`""`/`0`, C6) that previously got silently masked into a fake clean "0 findings" review. The raise propagates through the unchanged `__main__` shim to a non-zero exit. Absent/None/empty stays a legal empty review.

## Task Commits

Each task was committed atomically:

1. **Task 1: _valid_finding container guard + ingress malformed filter** - `9513e25` (feat)
2. **Task 2: _safe_window + non-finite confidence guard + envelope fail-closed guard** - `f5abbf8` (feat)

_Note: both tasks are `tdd="true"`. RED was established by running each task's inline `<verify>` probe against the pre-task code and confirming the documented crash (C1/C2 AttributeError; C3/HOLE1 TypeError; HOLE2 ValueError; C6 silent-empty). GREEN = the probe passing post-implementation + the full 123-test suite. No NEW tests were added here — that is plan 20-02's job; this plan only adds the score.py guards and keeps the existing suite green._

## Files Created/Modified
- `plugins/vibe-check/scripts/score.py` — added `_valid_finding`, `_safe_window`, the ingress malformed filter in `run()`, the non-finite confidence bound in `compute_score`, and the envelope fail-closed list-guard in `run()`. `_REQUIRED_KEYS` added as documentation-only (gates nothing). No new import; no try/except for control flow.

## EXACT reason-string vocabulary (READ THIS, plan 20-02)

`_valid_finding` emits exactly ONE reject reason string (recorded verbatim so 20-02's assertions match):

- **`"malformed: non-dict finding"`** — the ONLY malformed-reject reason. Emitted for a non-dict member (str/None/list/int) in either `findings` or `carryforward`. Routed to `filtered` as `{file: None, line: None, title: None, reason: "malformed: non-dict finding"}` (all three positional fields are `None` because a non-dict member has no `.get`; the accessor is guarded `m.get(k) if isinstance(m, dict) else None`).

The envelope fail-closed guard raises (does NOT route to `filtered`) with these two messages:
- `"malformed envelope: 'findings' must be a list, got <typename>"`
- `"malformed envelope: 'carryforward' must be a list, got <typename>"`

### CRITICAL NOTE for plan 20-02's malformed-shape test matrix

Per the orchestrator correction applied mid-execution, the required-key string-check was REMOVED from `_valid_finding`. Therefore:

- **Missing/None/non-str `file`/`title`/`category` findings are NOT rejected** — they flow through and SCORE (score.py is null-safe for these via `stable_hash`/`_first_line` coercing `None`->`""`). So 20-02's **T6/T7/T8** (finding missing file / title / category) MUST assert the finding is **KEPT (scored, survives in `result["findings"]`)**, NOT rejected-to-`filtered`. (This also matches the two frozen tests `TestStableHashNoneSafe.test_null_title_finding_flows_through_run_without_raising` and `TestCrossConfirmGroup.test_none_category_flows_through_run_without_raising`, which deliberately assert such findings survive.)
- **T1–T4** (non-dict findings: string/None/list/int) still assert **reject-to-`filtered`** with reason containing `"malformed"` (exact string `"malformed: non-dict finding"`).
- **T5** (non-dict carryforward entry) still asserts **reject-to-`filtered`** (same reason), good carryforward/finding kept.
- **T9 / empty `{}` dict finding** asserts **KEPT** — an empty `{}` IS a dict, so it flows through `_valid_finding` and scores with coerced-empty fields (it will typically be dropped later by the normal scoring path, e.g. out-of-diff or sub-threshold, NOT by `_valid_finding`). It is NOT a malformed-reject.
- **T11 / source_window=99** and the new **T20 / source_window=[1,2,3]** (non-string elements): KEPT, `silenced=False`, no crash.
- **T21 / non-finite agent_confidence** (NaN/Infinity/-Infinity): KEPT, scored as if confidence were 0 (no ValueError/OverflowError). NOTE: with confidence coerced to 0, an in-diff critical finding scores 20, which is BELOW the deep-review threshold of 70 — so it lands in `filtered` as `sub-threshold`, NOT in `result["findings"]`. "Kept" here means "not crashed / not lost", scored exactly like any confidence-0 finding. (See Deviations — the plan's Task 2 probe over-asserted this case.)
- **T14–T17 / envelope present-but-non-list findings or carryforward** (truthy `{...}`/`"oops"`/`5`/`{"x":1}` AND falsy `{}`/`""`/`0`): **fail closed (raise)**; `python3 score.py` fed such an envelope exits non-zero.
- **Absent/None/empty findings or carryforward**: legal empty review (`{scored_by_script: True, findings: []}`), must NOT fail closed.

## Decisions Made
- **Narrowed `_valid_finding` to non-dict-only** (orchestrator correction, see checkpoint below): the earlier "non-str required key = malformed" ruling was over-broad — it conflated crash-safety (this phase's actual HARDEN-01 mandate) with validity policy. Only a non-dict CONTAINER is a real crash; missing/null/non-str required fields are harmless (already null-safe) and two frozen tests lock their survival.
- Non-finite confidence guard is the import-free bounded comparison, not `math.isfinite` — the AST import-ban test forbids `import math`.
- Envelope guard scoped to `findings`/`carryforward` only.

## Deviations from Plan

### 1. [Rule 4 - Architectural/Policy] Narrowed `_valid_finding` reject policy to non-dict-only (resolved via checkpoint)
- **Found during:** Task 1 (implementing the required-key reject per the plan's literal `<action>`).
- **Issue:** The plan's Task 1 `<action>` + `must_haves` directed rejecting findings with missing/non-str `file`/`title`/`category` (citing an orchestrator ruling that a non-str required key = malformed). Implementing that exactly broke TWO pre-existing frozen tests — `TestStableHashNoneSafe.test_null_title_finding_flows_through_run_without_raising` and `TestCrossConfirmGroup.test_none_category_flows_through_run_without_raising` — which deliberately assert that null-`title`/null-`category` findings SURVIVE. The plan's two binding constraints ("implement the reject policy exactly" and "the 123 existing tests stay green") were mutually unsatisfiable for `title`/`category` (the conflict was NOT about `file` — no test asserts a bad `file` survives). This is a policy conflict, not a crash fix (RESEARCH Pitfall 5 itself flags missing-required-key handling as D-01 *policy*, not a crash fix).
- **Fix:** STOPPED and returned a `checkpoint:decision` (auto mode was off) rather than unilaterally breaking frozen tests OR silently narrowing the spec. The coordinator decided Option B-refined: `_valid_finding` rejects ONLY non-dict members; the `_REQUIRED_KEYS` string-check was dropped (the tuple kept as documentation only). This keeps all 123 tests green and stays inside the genuine crash-proofing mandate. The decision corrected the earlier over-broad orchestrator ruling. No `test_score.py` edits (that is 20-02's job).
- **Files modified:** plugins/vibe-check/scripts/score.py
- **Verification:** full suite 123 OK; Task 1 verify probe passes; both previously-conflicting tests pass; empty `{}` dict confirmed to flow through (not a malformed-reject).
- **Committed in:** `9513e25` (Task 1 commit).

### 2. [Rule 1 - Plan-probe defect] Task 2 verify probe over-asserts the HOLE 2 (non-finite confidence) case
- **Found during:** Task 2 (running the plan's inline Task 2 `<verify>` probe).
- **Issue:** The probe asserts `'nf' in [g['id'] for g in r['findings']]` for a finding whose `agent_confidence` is the non-finite value itself. But the plan's own stated semantics are "scored as if confidence were 0", and a confidence-0 in-diff critical finding scores 20, which is BELOW the deep-review threshold of 70 — so it is correctly filtered `sub-threshold` and is NOT in `result["findings"]`. The probe's assertion is mathematically incompatible with the plan's "scored as 0" semantics (0 + 20 in-diff max = 20 < 70). The CODE is correct (no crash; coerced to exactly 0, identical score to confidence=0).
- **Fix:** Did NOT change the code or inflate the test confidence (that would mask, not fix). Verified the REAL HOLE 2 fix directly: no ValueError/OverflowError, and `compute_score(...NaN...) == compute_score(...0...)` for all three non-finite values; the finding is visible in `filtered` (not lost). Documented the probe defect here and flagged it in the 20-02 note (T21) so the pinning suite asserts the correct outcome (no-crash + scored-as-0 + lands in filtered, not in findings).
- **Files modified:** none (probe defect, not a code defect).
- **Verification:** corrected probe (asserting no-crash + scored-as-0) passes `OK window+confidence+envelope-guard`; `__main__` exits 1 on a non-list-findings envelope and 0 on a valid empty envelope.
- **Committed in:** n/a (no code change; behavior is in `f5abbf8`).

---

**Total deviations:** 2 (1 Rule 4 policy conflict resolved via checkpoint; 1 Rule 1 plan-probe defect documented, no code impact).
**Impact on plan:** No scope creep. Deviation 1 narrowed the reject policy to exactly the crash-safety mandate (the phase's actual goal) and preserved the frozen suite. Deviation 2 is a plan-artifact bug, not a behavior change — the implemented behavior matches the plan's own stated semantics. Formula, banding, thresholds, cross-confirm/carry-forward semantics, the frozen golden digest, and the `scored_by_script` contract are all unchanged.

## Issues Encountered
- The `.planning/` directory is gitignored in this repo; this SUMMARY was force-added to commit it (mirroring how prior-phase SUMMARYs are tracked in the worktree).

## Known Stubs
None. The change is purely additive untrusted-input hardening; no placeholder data, no unwired components.

## Threat Flags
None. This plan REMOVES attack surface (DoS-via-malformed-finding) rather than adding any. The threat register's T-20-01..T-20-04 are all `mitigate` dispositions now satisfied; T-20-SC (`accept`) is N/A (zero package installs; import set unchanged).

## Next Phase Readiness
- score.py is now crash-hardened against the C1–C6 inventory + the two adversarial-found holes (non-string source_window elements, non-finite confidence). This is the floor plan 20-02 builds its malformed-shape pinning suite on (Wave 2, depends on this plan) — see the EXACT reason-string vocabulary + the CRITICAL 20-02 matrix note above. 20-02 must align T6/T7/T8 to KEPT (not reject) and T21 to no-crash/scored-as-0/filtered.
- No blockers.

## Self-Check: PASSED
- FOUND: `.planning/phases/20-crash-proof-the-core/20-01-SUMMARY.md`
- FOUND: `plugins/vibe-check/scripts/score.py`
- FOUND commit `9513e25` (Task 1), `f5abbf8` (Task 2), `fe11488` (SUMMARY)
- `cd plugins/vibe-check/scripts && python3 -m unittest` -> 123 tests OK (exit 0)
- This agent modified ONLY score.py + the new SUMMARY (no STATE.md/ROADMAP.md writes — orchestrator owns those)

---
*Phase: 20-crash-proof-the-core*
*Completed: 2026-06-26*
