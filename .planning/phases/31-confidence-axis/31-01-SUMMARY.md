---
phase: 31-confidence-axis
plan: 01
subsystem: testing
tags: [python, score.py, config.py, confidence-filter, envelope-key, min_confidence, pytest, tomllib]

# Dependency graph
requires:
  - phase: 30-config-surface-foundation
    provides: "config.py never-raise .vibe-check.toml reader + validated-knob pattern (_validate_top_model/_apply_flags) + thresholds envelope-key twin + GOLDEN_DIGEST byte-stable contract"
provides:
  - "score.py min_confidence envelope key: drops findings with coerced agent_confidence < N BEFORE cross_confirm_group, routing each to filtered[] with reason 'below-min-confidence'"
  - "config.py [noise] min_confidence knob: int [0,100] validator + [noise] section parse + _apply_flags precedence slot + MIN_CONFIDENCE_FLAG env threading through __main__"
  - "module-level _coerce_confidence(raw) helper in score.py (single source of truth for garbage->0, reused by compute_score + the filter)"
  - "The three contracts 31-02 depends on: envelope key name 'min_confidence', reason string 'below-min-confidence', MIN_CONFIDENCE_FLAG env-var contract"
affects: [31-02-confidence-render-wiring, review.md Phase 0.6, deep-review.md, output-format.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optional envelope key mirrors thresholds VERBATIM: envelope.get(key) with NO or-coercion; isinstance gate = crash-safe no-filter default; byte-stable when absent"
    - "Flag threading option (a): --min-confidence -> MIN_CONFIDENCE_FLAG env -> __main__ parses defensively -> flags={} -> _apply_flags runs the SAME validator (a bad flag degrades identically to a bad toml value)"
    - "Coercion extracted to a shared module-level helper so the filter and scoring can never drift"

key-files:
  created: []
  modified:
    - "plugins/vibe-check/scripts/config.py — _validate_min_confidence, [noise] parse, _apply_flags slot, __main__ MIN_CONFIDENCE_FLAG threading"
    - "plugins/vibe-check/scripts/score.py — _coerce_confidence helper, min_confidence envelope read, pre-cross_confirm filter"
    - "plugins/vibe-check/scripts/test_config.py — TestMinConfidenceValidation, TestPrecedence additions, MIN_CONFIDENCE_FLAG subprocess tests, _DEFAULTS update"
    - "plugins/vibe-check/scripts/test_score.py — TestRunMinConfidence, TestCoerceConfidence"

key-decisions:
  - "Envelope key name: min_confidence (scalar int); reason string: below-min-confidence (distinct from sub-threshold / not-in-reviewed-set)"
  - "Flag threading via option (a) — MIN_CONFIDENCE_FLAG env into the tested _apply_flags path (no duplicated validation, bad flag degrades with warning)"
  - "Strict < so a finding at exactly min_confidence SURVIVES; carryforward included in the drop with no carve-out (D-03)"

patterns-established:
  - "Confidence filter is a pre-scoring DROP, not a re-weight: it precedes cross_confirm_group so a dropped finding supplies no +10 and never becomes a survivor"
  - "isinstance(min_confidence, int) and not isinstance(..., bool) gate keeps working untouched on the default path — GOLDEN_DIGEST byte-stable"

requirements-completed: [CONF-02]

# Metrics
duration: ~40min
completed: 2026-07-01
---

# Phase 31 Plan 01: Confidence-axis script core Summary

**Script-enforced min_confidence filter — a new optional `score.py` envelope key drops sub-N findings into `filtered[]` (reason `below-min-confidence`) BEFORE cross-confirm, plus a validated `[noise] min_confidence` config knob with `--min-confidence` flag threading; zero-config path proven byte-identical (GOLDEN_DIGEST unmoved).**

## Performance

- **Duration:** ~40 min
- **Started:** 2026-07-01T~11:30:00Z
- **Completed:** 2026-07-01T12:09:43Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 4

## Accomplishments
- `config.py`: `_validate_min_confidence` (int [0,100], bool/out-of-range/non-int degrade to `None` + one warning naming the key), `[noise]` section parse, `_apply_flags` precedence slot, and `MIN_CONFIDENCE_FLAG` env threading through `__main__` (flag > config > default; a bad flag runs the SAME validator, never bypasses; shim always exits 0).
- `score.py`: extracted `_coerce_confidence` (single source of truth for garbage→0), read `min_confidence = envelope.get("min_confidence")` with NO `or 0`, and inserted the pre-scoring filter strictly between `working.extend(findings)` and `cross_confirm_group(working)` — dropping coerced `agent_confidence < N` to `filtered[]` with reason `below-min-confidence`.
- Proven byte-stable default path: GOLDEN_DIGEST literal unchanged, `TestBandBoundaries` + `TestStableHashGolden` green as-is, both `TestImportSet` classes still frozen (`{json,hashlib,re,sys}` for score.py; `{json,os,sys,tomllib}` for config.py).
- Full suite 192 → 224 tests green (17 new config, 15 new score/coerce).

## Task Commits

Each task was committed atomically (TDD RED then GREEN):

1. **Task 1 RED: failing config tests** - `035bf29` (test)
2. **Task 1 GREEN: min_confidence config knob + flag threading** - `272ebc1` (feat)
3. **Task 2 RED: failing score-filter tests** - `9329a5c` (test)
4. **Task 2 GREEN: pre-scoring min_confidence filter** - `f39bda4` (feat)

_No separate refactor commits — the `_coerce_confidence` extraction landed inside the Task 2 GREEN commit with tests proving compute_score behavior preserved._

## Files Created/Modified
- `plugins/vibe-check/scripts/config.py` - `_MIN_CONFIDENCE_MIN/_MAX` bounds, `_validate_min_confidence`, `min_confidence` in `_DEFAULT_VALUES` + the inline fresh-dict (both literals — lang-py-001), `[noise]` dict-guarded section parse + per-key validation, `_apply_flags` validators slot, `__main__` `MIN_CONFIDENCE_FLAG` parse/forward.
- `plugins/vibe-check/scripts/score.py` - `_coerce_confidence(raw)` module-level helper (called from `compute_score`), `min_confidence` envelope read (no `or 0`), the pre-`cross_confirm_group` filter loop routing drops to `filtered[]`.
- `plugins/vibe-check/scripts/test_config.py` - `TestMinConfidenceValidation` (round-trip / range / bool / absent-silent / direct validator), `TestPrecedence` flag-over-toml + bad-flag-degrade, `TestDegradeNotAbort` `MIN_CONFIDENCE_FLAG` subprocess tests (override / degrade / non-int-no-crash / empty-no-op / empty-REPO_ROOT), `_DEFAULTS` updated with `min_confidence: None`.
- `plugins/vibe-check/scripts/test_score.py` - `TestRunMinConfidence` (below-N drop, no-cross-confirm-leak twin + sanity +10, ==N survives, byte-stable, explicit-None==absent, min_confidence=0 drops nothing, reason-distinct-from-subthreshold, malformed-no-filter, missing/garbage-coerces-zero-dropped, carryforward-dropped) and `TestCoerceConfidence`.

## Contracts for Plan 31-02 (per plan `<output>`)
- **Envelope key name:** `min_confidence` (scalar int on the stdin envelope; omit the key on a zero-config run).
- **Reason string:** `below-min-confidence` (the `filtered[]` entry's `reason`; distinct from `sub-threshold` and `not-in-reviewed-set` so 31-02's separate filtered-summary row can count it).
- **Flag env-var contract:** `__main__` reads `MIN_CONFIDENCE_FLAG` (a parseable int string); non-empty+parseable → `flags={"min_confidence": <int>}` into `load_config`; unset/empty/non-int → no flag override (byte-identical to today). Validation (0-100 bound) is owned by `_validate_min_confidence` inside `_apply_flags`, so a flag like 999 degrades to `None` + one warning.

## Decisions Made
- Chose flag-threading **option (a)** (RESEARCH Open Question 1, RESOLVED at plan time): thread `--min-confidence` through `config.py` `__main__` via `MIN_CONFIDENCE_FLAG` into the tested `_apply_flags` validator, rather than re-implementing the 0-100 bound in orchestrator prose. No duplicated validation; a bad flag degrades exactly like a bad config value.
- Strict `<` comparison and carryforward-included (no carve-out) per D-03; `min_confidence=0` drops nothing (a coerced-≥0 value is never `< 0`), consistent with "default = no filtering".

## Deviations from Plan

None — plan executed exactly as written. All implementation followed the RESEARCH Insertion Recipe and CONTEXT D-03/D-04 verbatim.

_(Two of my own RED-phase test cases (`test_exactly_n_survives`, the +10 sanity sub-case of `test_dropped_neighbor_supplies_no_cross_confirm`) were tightened before their GREEN commit: my first draft conflated the PRE-scoring confidence filter with the POST-scoring per-command sub-threshold cutoff — exactly the two-layer trap RESEARCH Pitfall 4 / D-02 warned about. Fixes: use `command="deep-review"` (finalize cutoff 70) to isolate a conf-70 finding's survival, and a `null-access`→correctness-domain category so the twin actually cross-confirms. These were test-authoring corrections within Task 2's TDD loop, not changes to the implementation or the plan — the filter code was correct as first written.)_

## Issues Encountered
- `pytest` is not a python3.14 module (`python3 -m pytest` fails) but the `pytest` CLI (v9.0.3 at `~/.local/bin/pytest`) runs the suite fine. Used `pytest -q` (the project gate per the plan's `<critical_invariants>`), NOT `python3 -m unittest`. Baseline confirmed 192 green before starting.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 31-02 (render + review.md/deep-review.md wiring) can proceed: the three contracts above are locked and tested. 31-02 threads `--min-confidence` at review.md Phase 0.6 (setting `MIN_CONFIDENCE_FLAG` / a `$CONFIG_MIN_CONFIDENCE` var), sources the `min_confidence` envelope key in Phase 3 (omitting it on zero-config), rebinds the `Conf` column to `agent_confidence`, and adds the `Below min_confidence` filtered-summary row counting `reason == "below-min-confidence"`.
- No blockers. Formula/GOLDEN_DIGEST untouched; import sets frozen.

## Self-Check: PASSED

All modified files exist on disk (config.py, score.py, test_config.py, test_score.py) and this SUMMARY.md. All four task commits verified present in git log (035bf29, 272ebc1, 9329a5c, f39bda4). Full suite 224 tests green; GOLDEN_DIGEST literal unchanged; both import-set guards green.

---
*Phase: 31-confidence-axis*
*Completed: 2026-07-01*
