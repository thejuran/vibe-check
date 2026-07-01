---
phase: 33-codex-legibility-safer-fix-loop-default-orchestrator-only-kn
plan: 01
subsystem: infra
tags: [config, vibe-check, python, unittest, fail-safe, codex, off-auto-on]

# Dependency graph
requires:
  - phase: 30-config-surface-foundation
    provides: scripts/config.py never-raise reader + validate-then-overlay precedence API (flag > toml > default) + __main__ env-flag shim + test_config.py harness — the codex knob plugs into all of these
provides:
  - "config.py `codex` knob (LEGIBLE-02, D-14): off/auto/on enum, default auto, malformed → auto + one KEY-named warning; validated via _validate_codex (fixed-enum shape of _validate_top_model, non-None default-direction of _validate_idiom_floor)"
  - "codex in _DEFAULT_VALUES AND the load_config inline fresh-dict literal (both in lockstep, never dict(_DEFAULT_VALUES)); [noise] codex toml read; _apply_flags validators map entry"
  - "config.py __main__ reads CODEX_FLAG env → flags['codex'] (no int parse; merges with MIN_CONFIDENCE_FLAG so both coexist) — the runtime path --codex threads through"
  - "test_config.py TestCodexValidation (10 tests) + precedence + CODEX_FLAG-via-__main__ tests; the REQUIRED _DEFAULTS 'codex':'auto' edit keeping the fail-safe assertEqual(values,_DEFAULTS) tests green"
affects: [33-02-plan, orchestrator-codex-wiring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "codex is an ORCHESTRATOR-ONLY knob (like disabled/top_model): validated in config.py, consumed by the orchestrator, NEVER enters the score.py stdin envelope — GOLDEN_DIGEST stays frozen, score.py/test_score.py byte-unchanged"
    - "Warning names the KEY + a FIXED reason only (config: codex invalid — using default), never the raw config VALUE text (V5/V7 hardening); tests assert 'codex' in warning"
    - "case-insensitive round-trip (raw.lower()) mirroring _validate_idiom_floor; malformed → 'auto' (behavior-unchanged posture, D-14), NOT None"

key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/config.py
    - plugins/vibe-check/scripts/test_config.py

key-decisions:
  - "Warning string is the FIXED sibling-consistent form 'config: codex invalid — using default' (NOT the D-14 (<reason>) parenthetical) — matches min_confidence/thresholds/idiom_floor and the never-echo-raw-value security posture"
  - "Malformed codex → 'auto' default (non-None), the idiom_floor default-DIRECTION (a bad value keeps Codex running per D-14), while cloning _validate_top_model's fixed-enum SHAPE"
  - "CODEX_FLAG __main__ shim is simpler than MIN_CONFIDENCE_FLAG — no int() parse; a non-empty string flows straight into flags['codex'] and _validate_codex degrades a bogus string to auto"
  - "Both _DEFAULT_VALUES-shaped literals (module-level + load_config inline) gained codex:auto in lockstep (anti-poisoning: the code deliberately re-declares inline, not dict(_DEFAULT_VALUES))"

# Verification
verification:
  - "pytest -q from plugins/vibe-check/scripts: 311 passed (baseline was 147; codex tests added), 0 failed"
  - "pytest -q -k Codex: 13 passed (TestCodexValidation + precedence + CODEX_FLAG thread)"
  - "git diff --quiet -- plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/test_score.py: exit 0 (byte-unchanged, GOLDEN_DIGEST frozen)"
  - "config.py has 1x def _validate_codex, 2x codex:auto literals, CODEX_FLAG env read, 'codex': _validate_codex in _apply_flags map"

commits:
  - "83cbfae feat(33-01): add config.py-validated codex knob (off/auto/on, default auto)"
  - "80155e9 test(33-01): TestCodexValidation + precedence + CODEX_FLAG thread; _DEFAULTS codex:auto"

# Self-Check: PASSED

Plan 33-01 (LEGIBLE-02 config.py foundation) is complete. The `codex` off/auto/on knob is
validated in the tested config.py helper with the never-raise fail-safe, wired into the roster /
[noise] read / _apply_flags precedence / __main__ CODEX_FLAG thread, and covered by 13 codex
tests. score.py is untouched (codex is orchestrator-only). Ready for 33-02 to consume
`$CONFIG_CODEX` in review.md Phase 0.6 + deep-review.md Phase 2c/3.

**Executor note:** the Wave-1 executor completed both tasks' edits (config.py committed as 83cbfae;
test_config.py edits written) but stalled before committing the test file and writing this SUMMARY.
The orchestrator verified the work (311 tests green, score.py byte-unchanged, the required _DEFAULTS
edit present), committed test_config.py as 80155e9, and wrote this SUMMARY per the execute-phase
completion-signal fallback.
