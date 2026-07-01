---
phase: 30-config-surface-foundation
plan: 02
subsystem: testing
tags: [score.py, thresholds, band_for, config-surface, unittest, crash-safe]

# Dependency graph
requires:
  - phase: 30-config-surface-foundation (plan 01)
    provides: config.py load_config + the LOCKED thresholds schema ({critical,warning,medium} non-bool ints, strictly descending, medium>=70, whole-set fallback) that this plan consumes on the score.py envelope
provides:
  - "Parameterized band_for(score, thresholds=None) — reads an optional band-floor override, default-inert (byte-identical zero-config path), independently crash-safe against a malformed value"
  - "run() threads a thresholds envelope key through the SINGLE band_for call site (band_for stays the single writer of band)"
  - "_DEFAULT_BANDS module constant (95/80/70) — the built-in band floors, distinct from THRESHOLDS (the per-command finalize cutoff)"
  - "test_score.py regression locks: TestThresholdsOverride (tunable banding + byte-stable default), TestThresholdsCrashSafe (never-raise on wrong-type/missing/non-dict), TestRunThresholds (end-to-end threading + the two-layer dead-band proof)"
affects: [31-min-confidence, 32-idiom-floor, 33-orchestrator-knobs, 34-close, review.md-envelope-wiring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive default-inert envelope key: envelope.get('thresholds') (no `or {}`), threaded to a single consumer; absent/None reproduces prior output byte-for-byte"
    - "Whole-set crash-safe coercion (_usable_bands): accept a config dict ONLY when all keys present AND each is a usable non-bool int, else fall back to the WHOLE built-in default — never a per-sub-key mix, never raises"

key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py

key-decisions:
  - "band_for parameterized via a private _usable_bands(thresholds) helper returning a validated 3-int dict or the whole _DEFAULT_BANDS — keeps the banding ladder trivial and the crash-safety in one auditable place"
  - "thresholds read with envelope.get('thresholds') and NO `or {}` — absent AND explicit-None both yield None (built-in literals), so the zero-config path stays byte-identical"
  - "_DEFAULT_BANDS placed immediately after THRESHOLDS with a banner comment stating the two-layer distinction (D-02), so a future reader cannot conflate the band-label floors with the per-command finalize cutoff"

patterns-established:
  - "Default-inert envelope-key parameterization proven byte-stable at BOTH the unit level (band_for(s)==band_for(s,None)==band_for(s,_DEFAULT_BANDS)) and end-to-end through run() (same band + same stable_hash)"
  - "Crash-safe consumption of a config-produced value: score.py never trusts config.py's schema — a stale/buggy config cannot fail-close the review (whole-set fallback, locked by TestThresholdsCrashSafe)"

requirements-completed: [CONFIG-04]

# Metrics
duration: 3min
completed: 2026-07-01
---

# Phase 30 Plan 02: Script-enforced `thresholds` knob Summary

**`band_for()` parameterized with an optional, crash-safe `thresholds` band-floor override threaded through `run()`'s single call site — tunable when present, byte-identical to v2.7 when absent (GOLDEN_DIGEST + TestBandBoundaries unchanged).**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-01T00:22:19Z
- **Completed:** 2026-07-01T00:25:37Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Parameterized `band_for(score, thresholds=None)` reading an optional band-floor override, with the default (absent / None / built-in `_DEFAULT_BANDS`) path proven byte-identical to v2.7 across every score 0..100.
- Made `band_for` independently crash-safe (Finding #2 / T-30-06): a non-dict, missing sub-key, or wrong-type sub-key (string / None / float / **bool**) degrades to the WHOLE built-in default set and never raises — a stale/buggy `config.py` cannot crash the scorer.
- Threaded `thresholds = envelope.get("thresholds")` through `run()` into the SINGLE `band_for` call site, keeping `band_for` the single writer of `band`; `THRESHOLDS` (per-command cutoff) and `stable_hash` untouched.
- Added 11 regression tests (suite 180 → 191, all green) including the two-layer dead-band proof: a low-floor `{72,71,70}` score-75 finding bands `critical` and survives under `/deep-review` (>=70) but is filtered sub-threshold under `/review` (>=80).

## Task Commits

Each task was committed atomically:

1. **Task 1: Parameterize band_for + consume thresholds in run() (default-inert)** — `bf4402b` (feat)
2. **Task 2: Lock thresholds banding + the byte-stable default path in test_score.py** — `3466e47` (test)

**Plan metadata:** committed separately (docs: complete plan) with this SUMMARY + STATE/ROADMAP updates.

_Note: this is a `type: tdd` plan; Task 1's inline automated verifies (`<verify>` block) drove the RED→GREEN of the code, and Task 2 added the formal regression classes that lock it. Both landed green in one pass._

## Files Created/Modified
- `plugins/vibe-check/scripts/score.py` — Added `_DEFAULT_BANDS` constant + `_usable_bands()` crash-safe validator; replaced `band_for(score)` with `band_for(score, thresholds=None)`; `run()` reads and threads the optional `thresholds` envelope key into the single band write.
- `plugins/vibe-check/scripts/test_score.py` — Added `TestThresholdsOverride` (tunable banding + `test_default_arg_matches_no_arg`), `TestThresholdsCrashSafe` (8 malformed values × boundary scores never raise, explicit bool-rejection), and `TestRunThresholds` (zero-config byte-stability, explicit-None == absent-key via band+stable_hash, override moves band through run(), and the two-layer command-aware dead-band proof).

## Decisions Made
- **Whole-set fallback, not per-sub-key `.get`** — `band_for` accepts a `thresholds` dict only when all three floors are present and each is a usable non-bool int; any violation falls back to the entire `_DEFAULT_BANDS`. This matches `config.py`'s whole-set posture (30-01) and keeps the reasoning trivial (no mixing a validated floor with a defaulted one).
- **Bool exclusion is explicit and tested** — `isinstance(True, int)` is True, so a plain int check would wrongly accept a bool floor; `_usable_bands` rejects it and `TestThresholdsCrashSafe.test_bool_sub_key_is_rejected_not_treated_as_int` pins it.
- **`_DEFAULT_BANDS` sits next to `THRESHOLDS` with a distinguishing banner comment** — the two threshold layers (band-label floors vs per-command finalize cutoff, D-02) are the single most conflatable thing in this change; the comment makes the distinction unmissable.

## Deviations from Plan

None - plan executed exactly as written. Both LOCKED specifics (the byte-identical zero-config invariant and the whole-set crash-safe guard) were implemented verbatim; all `<verify>` and `<acceptance_criteria>` commands pass; `GOLDEN_DIGEST` was not re-pinned; the import set stayed exactly `{json, hashlib, re, sys}`.

## Issues Encountered
- One transient tooling slip: the first Task-1 commit used a repo-root-relative path while the cwd was already `plugins/vibe-check/scripts`, so `git add` doubled the path and failed. Re-ran with the correct cwd-relative path (`git add score.py`) — no code impact.

## Known Stubs
None. Both modified files are fully-wired production code + test coverage; `band_for` reads a real envelope value, and `run()` sources it from the actual stdin envelope. The orchestrator-side wiring that INJECTS `thresholds` into the envelope (from `config.py`) is Plan 30-03's review.md work — the consumer side (this plan) is complete and default-inert until that key is injected, which is the intended additive-envelope-key sequencing (CONFIG-01 back-compat).

## Next Phase Readiness
- The script-enforced side of the config surface (CONFIG-04) is proven: `thresholds` tunes banding when present and is provably inert when absent.
- Ready for Plan 30-03 (review.md/deep-review.md wiring) to source `thresholds` from `config.py`'s resolved values and inject it into the score.py envelope — the consumer contract is stable and crash-safe against any value that arrives.
- Phases 31/32 add MORE `score.py` envelope keys (`min_confidence`, `idiom_floor`); the byte-stable-default discipline demonstrated here (unit + end-to-end regression + unchanged GOLDEN_DIGEST) is the template each must follow.

## Self-Check: PASSED

- Files verified present: `score.py`, `test_score.py`, `30-02-SUMMARY.md` — all FOUND.
- Commits verified in git log: `bf4402b` (feat), `3466e47` (test), `61bc467` (docs) — all FOUND.
- Full suite `python3 -m unittest` → 191 tests OK; import set `{hashlib, json, re, sys}`; GOLDEN_DIGEST unchanged; default-inert across 0..100; `THRESHOLDS` intact.

---
*Phase: 30-config-surface-foundation*
*Completed: 2026-07-01*
