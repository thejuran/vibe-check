---
phase: 32-idiom-floor-vibe-ignore-marker-script-enforced-noise-knobs
plan: 01
subsystem: scoring
tags: [idiom_floor, noise-controls, band-cap, config-surface, score.py, config.py, vibe-check, NOISE-01]

# Dependency graph
requires:
  - phase: 30-config-surface-foundation
    provides: "config.py never-raise reader + [noise] section + per-key fail-safe validators + _apply_flags precedence + the thresholds envelope-key template"
  - phase: 31-confidence-axis
    provides: "min_confidence [noise] knob — the VERBATIM validator + envelope-key + byte-stable-default pattern idiom_floor mirrors"
provides:
  - "config.py [noise] idiom_floor knob: _validate_idiom_floor (band names incl. 'low' → lowercased band; 'off'/'none' → literal 'off' sentinel NOT None; malformed → 'medium' default + warning) wired into defaults + [noise] parse + _apply_flags slot"
  - "score.py idiom band cap: _BAND_SEVERITY ordering + _usable_idiom_floor 3-state resolver (absent/None→medium cap ACTIVE; off/none→disabled; valid band→that band; else→medium fail-safe) + _cap_idiom_band (lower-only, category=='idiom'-scoped) applied as the ONE post-band adjustment at the single band-write site"
  - "idiom findings capped at medium BY DEFAULT (A1) on a zero-config run — idioms never block finalize out of the box"
  - "explicit off/none genuinely DISABLES the cap and is distinct from omission end-to-end (config.py literal 'off' sentinel → envelope → score.py disabled; absent key → medium cap)"
affects: [phase-33-codex-legibility-fix-loop, phase-34-efficacy-close, render-layer-suppression-split]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-category band cap as a clearly-commented POST-band adjustment at the single band-write site (band_for stays the single band WRITER; the cap only re-labels, never re-computes)"
    - "Self-describing disable sentinel: config.py returns the literal 'off' string (NOT None) so the explicit-disable provenance survives onto the envelope and absent≠off is provable at the scorer"
    - "Inverted default-direction knob: idiom_floor defaults to 'medium' (cap ACTIVE) where thresholds/min_confidence default to None (no effect) — malformed also fails SAFE to medium, not to disabled"

key-files:
  created: []
  modified:
    - "plugins/vibe-check/scripts/config.py — _validate_idiom_floor + _IDIOM_FLOOR_* constants + default-medium in _DEFAULT_VALUES/load_config literal + [noise] parse + _apply_flags slot"
    - "plugins/vibe-check/scripts/score.py — _BAND_SEVERITY + _usable_idiom_floor + _cap_idiom_band + envelope read + the single post-band cap application"
    - "plugins/vibe-check/scripts/test_config.py — TestIdiomFloorValidation (14 cases) + _DEFAULTS shape updated to include idiom_floor:'medium'"
    - "plugins/vibe-check/scripts/test_score.py — TestIdiomFloor (19 cases) + TestIdiomFloorEnvelopeIntegration (absent≠off proof) + config/tempfile test imports"

key-decisions:
  - "A1 default-active: an absent idiom_floor envelope key defaults to 'medium' INSIDE score.py (_usable_idiom_floor state 1), so the orchestrator MAY omit the key on zero-config while the cap still applies"
  - "Finding #2 Option A: config.py returns the literal 'off' sentinel (NOT None) for explicit off/none; 'none' normalizes to canonical 'off'; score.py reads three distinct envelope states so absent≠off≠band"
  - "Malformed idiom_floor fails SAFE to 'medium' (cap stays ACTIVE) in BOTH config.py and score.py — the OPPOSITE direction from min_confidence's malformed→None (ROADMAP criterion 4)"
  - "Finding NEW-2: 'low' is a VALID cap band (writes literal 'low'), the finding STAYS category=='idiom' (never re-categorized) — the render split (Plan 03) disambiguates by category, never band"

patterns-established:
  - "Three-state envelope resolution centralized in ONE helper (_usable_idiom_floor) rather than split with an `x if x is not None else default` in run() — keeps the off-sentinel semantics unambiguous in exactly one place"
  - "Scorer re-validates the envelope value independent of config.py ('don't trust your input', mirrors _usable_bands) so a stale/buggy config can never crash the scorer nor silently disable the cap"

requirements-completed: [NOISE-01]

# Metrics
duration: 6min
completed: 2026-07-01
---

# Phase 32 Plan 01: Idiom-floor band cap Summary

**`idiom_floor` per-category band cap — `idiom` findings are capped at a tunable max band, ACTIVE BY DEFAULT at `medium` (A1) so idioms never block finalize, tunable up/down/off with the explicit `off`/`none` disable provably distinct from omission (literal `"off"` sentinel end-to-end), scoring formula byte-stable.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-07-01T16:23:27Z
- **Completed:** 2026-07-01T16:28:35Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `config.py` gains the validated `[noise] idiom_floor` knob: band names (incl. `low`) round-trip; `off`/`none` → the literal `"off"` sentinel (NOT None); malformed → the `medium` default + one key-named warning. Wired into `_DEFAULT_VALUES`, the anti-poisoning `load_config` fresh-dict literal, the `[noise]` parse block, and the `_apply_flags` precedence slot.
- `score.py` gains the idiom band cap: `_BAND_SEVERITY` ordering, the three-state `_usable_idiom_floor` resolver, and `_cap_idiom_band` (lower-only, scoped to `category=="idiom"`), applied as the ONE clearly-commented post-band adjustment immediately after the single `band_for(...)` write site. `band_for` remains the single band writer.
- Zero-config default (A1): with no `idiom_floor` key, score.py internally defaults the cap to `medium`, so a would-be-critical idiom is floored at `medium` out of the box.
- Explicit disable (Finding #2): the literal `"off"`/`"none"` sentinel disables the cap and is DISTINCT on the envelope from an absent key — proven end-to-end by `TestIdiomFloorEnvelopeIntegration` (config.py → envelope → score.py).
- `idiom_floor="low"` (Finding NEW-2) writes the literal `"low"` band and keeps `category=="idiom"` (no re-categorization) — the knob's full range is preserved for the Plan 03 render split.
- GOLDEN_DIGEST + TestBandBoundaries + the AST import-set are all unchanged — the scoring math and score.py's stdlib-only boundary stay byte-stable. Full suite 257 passed (was 224 baseline; +33 new).

## Task Commits

Each task was committed atomically (TDD: RED test + GREEN implementation folded per task):

1. **Task 1: config.py `_validate_idiom_floor` + `[noise]` parse + default-medium wiring** — `31e79bd` (feat)
2. **Task 2: score.py idiom band cap (`_BAND_SEVERITY` + `_usable_idiom_floor` + `_cap_idiom_band`) + config→envelope→score integration** — `f28633c` (feat)

_Note: each TDD task committed the failing test and its implementation together in one atomic commit._

## Files Created/Modified
- `plugins/vibe-check/scripts/config.py` — `_validate_idiom_floor` validator + `_IDIOM_FLOOR_BANDS`/`_DISABLE`/`_OFF`/`_DEFAULT_IDIOM_FLOOR` constants; `idiom_floor: "medium"` default in `_DEFAULT_VALUES` and the `load_config` fresh-dict literal; `[noise]` parse entry; `_apply_flags` validator slot.
- `plugins/vibe-check/scripts/score.py` — `_BAND_SEVERITY` ordering, `_usable_idiom_floor` (three-state), `_cap_idiom_band` (lower-only, idiom-scoped); `idiom_floor = envelope.get("idiom_floor")` read; the single post-band cap application at the band-write site.
- `plugins/vibe-check/scripts/test_config.py` — `TestIdiomFloorValidation` (14 cases) + `_DEFAULTS` shape updated to include `idiom_floor: "medium"`.
- `plugins/vibe-check/scripts/test_score.py` — `TestIdiomFloor` (19 cases) + `TestIdiomFloorEnvelopeIntegration` (3 cases, the absent≠off provenance proof); added `config`/`tempfile` test-only imports.

## Decisions Made
None beyond the plan — the CONTEXT/plan-locked resolutions (A1 default-active, Finding #2 self-describing `"off"` sentinel, Finding NEW-2 `low` preserved, malformed→medium fail-safe) were implemented exactly as specified.

## Deviations from Plan

None - plan executed exactly as written.

One benign necessary adjustment inside plan scope (NOT a deviation): the shared `_DEFAULTS` constant in `test_config.py` (used by ~10 pre-existing `assertEqual(values, _DEFAULTS)` assertions) had to gain `idiom_floor: "medium"` in lockstep with the new `config.py` default, or those existing tests would have failed. This is the direct, expected consequence of adding a new default key and is covered by the plan's "TestIdiomFloorValidation ... no regression in the other validators" acceptance criterion.

## Issues Encountered
- The plan's `<automated>` verify blocks use `python3 -m unittest`, which the plan-level executor instructions flag as non-working on this machine. Used the sanctioned `pytest -q` equivalent (from `plugins/vibe-check/scripts`) for every verification, as directed. All plan verification commands pass under pytest.

## Verification Evidence
- Full config+score suite: `pytest -q test_config.py test_score.py` → **257 passed, 198 subtests passed**.
- Provenance proof (absent≠off): `pytest -q test_score.py::TestIdiomFloorEnvelopeIntegration` → 3 passed.
- Byte-stability anchors: `pytest -q test_score.py::TestStableHashGolden test_score.py::TestBandBoundaries` → 11 passed (GOLDEN_DIGEST unmoved).
- Import ban: `pytest -q test_score.py::TestImportSet` → 3 passed (score.py stays stdlib-only, no new imports).
- No stray harness tags; all four modules `ast.parse` clean.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- NOISE-01 satisfied and locked by tests. The `idiom_floor` cap is live, script-enforced, formula-untouched, and tunable up/down/off.
- Plan 02 (NOISE-02/03 `vibe-ignore` marker + bare-marker low finding) can proceed — it shares `score.py`/`test_score.py`/`config.py` but touches a disjoint surface (`silenced_nearby()` + a synthetic-finding path), no collision with this plan's band-cap edits.
- Plan 03 (render split) owns disambiguating a low-band idiom finding from the synthetic `suppression` finding by CATEGORY — this plan deliberately kept a low-capped idiom `category=="idiom"` to preserve that boundary.

## Self-Check: PASSED

- `32-01-SUMMARY.md` present.
- Both task commits exist in history: `31e79bd` (Task 1), `f28633c` (Task 2).
- All four modified source files present; key artifacts verified: `config._validate_idiom_floor`, `score._cap_idiom_band`, `test_config.TestIdiomFloorValidation`, `test_score.TestIdiomFloor`.
- Full suite green under `pytest -q`: 257 passed, 198 subtests passed.

---
*Phase: 32-idiom-floor-vibe-ignore-marker-script-enforced-noise-knobs*
*Completed: 2026-07-01*
