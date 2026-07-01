---
phase: 30-config-surface-foundation
plan: 01
subsystem: infra
tags: [tomllib, config, vibe-check, python, unittest, fail-safe]

# Dependency graph
requires:
  - phase: 16-deterministic-core-script
    provides: score.py module layout + house style (docstring/constants/pure-helpers/__main__ shim) and test_score.py unittest harness that config.py/test_config.py mirror and invert
provides:
  - "scripts/config.py — the never-raise .vibe-check.toml reader: load_config(path, *, flags=None) -> (values, warnings); the ONE new module allowed filesystem I/O"
  - "The (values, warnings) contract: values = {thresholds: dict|None, disabled: list[str], top_model: str|None}; warnings = list[str] (KEY + fixed reason only)"
  - "The __main__ shim: $REPO_ROOT env in -> {values, warnings} JSON on stdout -> exit 0 always (degrade, never abort)"
  - "scripts/test_config.py — 33 unit tests locking every fail-safe + precedence branch"
  - "The validate-then-overlay precedence API (flag > toml > default), unit-tested so later phases' --min-confidence/--codex flag tier is sound from day one"
affects: [30-02-plan, 30-03-plan, phase-31, phase-32, phase-33, phase-34, orchestrator-config-wiring]

# Tech tracking
tech-stack:
  added: [tomllib (stdlib, imported inside load_config)]
  patterns:
    - "Never-raise I/O boundary: config.py inverts score.py's fail-CLOSED posture — degrade per-key to defaults on every input, never raise to the orchestrator (CONFIG-03)"
    - "Coerce-or-default validators (_validate_thresholds/_validate_disabled/_validate_top_model) following score.py's _category_domain/_safe_window idiom: isinstance-guard, return (value_or_default, warning_or_None), never raise"
    - "Two ordered pre-parse guards: os.path.isfile (regular-file) BEFORE os.path.getsize (size cap) — closes the symlink->special-file DoS bypass that a size-only guard misses"
    - "Validate-then-overlay precedence: flag values run through the SAME per-key validators as toml — a flag can never bypass validation"

key-files:
  created:
    - plugins/vibe-check/scripts/config.py
    - plugins/vibe-check/scripts/test_config.py
  modified: []

key-decisions:
  - "config.py NEVER raises to its caller — inverts score.py's fail-closed __main__ (exit 0 always vs non-zero propagate)"
  - "tomllib imported INSIDE load_config wrapped in try/except ImportError (D-01) so the module still imports on a Python < 3.11 runtime and degrades"
  - "D-02 thresholds schema LOCKED: dict with EXACTLY {critical,warning,medium}, each a non-bool int in [1,100], strictly descending, medium>=70; WHOLE-SET fallback to None (band_for's built-in 95/80/70) on any violation"
  - "top_model allowlist {opus,fable} reuses the existing $VIBE_CHECK_TOP_MODEL validation so the two precedence sources cannot diverge (Pitfall 6)"
  - "disabled honors disabling any agent incl. bugs/security (returned faithfully, NOT stripped) — the orchestrator surfaces a disabled core agent on the config-health line (Pitfall 5); config.py never silences it"
  - "Warnings name the KEY + a FIXED reason string only — never the raw attacker-controlled config VALUE text (Security V5 / T-30-04)"
  - "A below-80 band floor (e.g. critical=72,warning=71,medium=70) is ACCEPTED not rejected — its observability under /review vs /deep-review is the per-command-cutoff layer (Finding #4 two-layer), proven in Plan 02's run()-level test"

patterns-established:
  - "Never-raise config helper returning (values, warnings) — the milestone keystone every later v2.8 phase assumes"
  - "Ordered regular-file-then-size pre-parse guards for DoS-hardening a repo-controlled file read"
  - "Validate-then-overlay flag precedence — the reserved slot later phases reuse for --min-confidence/--codex"

requirements-completed: [CONFIG-01, CONFIG-02, CONFIG-03]

# Metrics
duration: 3min
completed: 2026-07-01
---

# Phase 30 Plan 01: Config surface foundation Summary

**A never-raise `scripts/config.py` reader for `.vibe-check.toml` (via `tomllib`) that resolves `thresholds`/`disabled`/`top_model` through flag>toml>default and degrades per-key to defaults, plus 33 unit tests locking every fail-safe and precedence branch.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-01T00:16:46Z
- **Completed:** 2026-07-01T00:20:10Z
- **Tasks:** 2
- **Files modified:** 2 (both created)

## Accomplishments
- `config.py` — the ONE new module allowed filesystem I/O: `load_config(path, *, flags=None) -> (values, warnings)` that NEVER raises, inverting score.py's fail-CLOSED posture so a missing/malformed config never breaks a review (CONFIG-03).
- Two ordered pre-parse guards (`os.path.isfile` regular-file, then `os.path.getsize` 1-MiB cap) close the symlink→FIFO/char-device and oversized-file DoS bypasses (Finding #2 round-3/4) — degrade WITHOUT opening/parsing.
- The locked D-02 thresholds schema (3 sub-keys, strict descent, medium>=70, whole-set fallback), the opus/fable `top_model` allowlist, and the container+element `disabled` double-guard — each validated independently (per-key fail-safe).
- Validate-then-overlay flag precedence (`flag > toml > default`): a flag value runs through the same per-key validator as a toml value, so the reserved flag tier later phases reuse is sound from day one (Finding #3).
- `test_config.py` — 33 tests; whole-dir suite 147 → 180, score.py's suite untouched and still green (including its frozen `{json,hashlib,re,sys}` import-set test).

## Task Commits

Each task was committed atomically:

1. **Task 1: Author config.py — the never-raise I/O boundary helper** - `3201334` (feat)
2. **Task 2: Author test_config.py — lock every fail-safe + precedence branch** - `28f7df5` (test)

_Note: this plan's two tasks are `tdd="true"`; config.py's behavior was verified via the plan's inline automated checks + spot-check harness at Task 1 (RED/GREEN collapsed into the author-then-verify commit), and the full test_config.py locks every branch at Task 2._

## Files Created/Modified
- `plugins/vibe-check/scripts/config.py` (created) - The `.vibe-check.toml` I/O boundary: `load_config`, the three per-key validators, `_apply_flags` (validate-then-overlay), and the degrade-not-abort `__main__` shim. Import set = `{json, os, sys, tomllib}` (tomllib imported inside load_config).
- `plugins/vibe-check/scripts/test_config.py` (created) - 33 unit tests: `TestFailSafe` (absent/unparseable/non-UTF-8/oversized/non-regular/one-bad-key/no-tomllib + symlink→regular honored), `TestThresholdsValidation`, `TestTopModel`, `TestDisabled`, `TestPrecedence`, `TestDegradeNotAbort` (subprocess, exit 0), `TestImportSet` (separate class, wider allowlist).

## Decisions Made
None beyond the plan's locked specifics — all D-01..D-04 decisions and the four adversarial-review findings (#2 round-3/4 DoS guards, #3 flag validation, #4 two-layer acceptance) were followed exactly as written. See frontmatter `key-decisions` for the enforced locks.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. Python 3.14.5 (tomllib present) and the 147-test baseline were green at start; both new files passed on first run of their verify blocks.

## Threat Surface Scan
No new security-relevant surface beyond the plan's `<threat_model>`. config.py opens ONLY the fixed `$REPO_ROOT/.vibe-check.toml` path (never a config-supplied path), tomllib does not execute TOML, no config value flows into subprocess/exec, and warnings never echo raw config VALUE text (T-30-03/04 honored). No new endpoints, auth paths, or schema changes.

## Known Stubs
None. Both files are fully wired: `load_config` reads real files and returns real resolved values; every branch is exercised by a passing test. The orchestrator wiring that consumes `(values, warnings)` is Plan 03's scope (by design), not a stub in this plan.

## User Setup Required
None - no external service configuration required (all dependencies are Python stdlib).

## Next Phase Readiness
- The `(values, warnings)` contract and the `$REPO_ROOT → stdout-JSON, exit-0` `__main__` shape are stable and locked for Plan 02 (score.py `band_for` parameterization) and Plan 03 (orchestrator wiring) to consume.
- Zero modifications to score.py / test_score.py / any orchestrator prose — this plan is purely additive (two new files), so it introduces no cross-file drift for the sequential phases that follow.
- The keystone per-key fail-safe (CONFIG-03) is now proven by 33 tests; later v2.8 knobs (Phases 31-33) can assume a missing/malformed config degrades without aborting.

## Self-Check: PASSED

- Files: config.py, test_config.py, 30-01-SUMMARY.md all FOUND on disk.
- Commits: 3201334 (config.py), 28f7df5 (test_config.py), 8ccc6ca (SUMMARY) all FOUND in git log.

---
*Phase: 30-config-surface-foundation*
*Completed: 2026-07-01*
