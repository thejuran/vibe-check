---
phase: 16-deterministic-core-script
plan: 01
subsystem: testing
tags: [python, stdlib, unittest, scoring, sha256, hashlib, ast, deterministic-core]

# Dependency graph
requires:
  - phase: 14-dogfood-critical-warning-fixes
    provides: "scoring.md as the SINGLE scoring source (DOGFIX-05); orchestrator resolves $STATE_FILE once and downstream consumers reuse it (DOGFIX-06)"
provides:
  - "plugins/vibe-check/scripts/score.py — a stdlib-only (json/hashlib/re/sys) deterministic-core scoring filter: pure functions (stable_hash, band_for, silenced_nearby, carry_forward_status, cross_confirm_group, compute_score) + a run(envelope) orchestrator + a fail-closed __main__ stdin/stdout shim"
  - "plugins/vibe-check/scripts/test_score.py — the FIRST test suite in the plugin (66 stdlib-unittest cases) pinning every band boundary, every formula modifier, the drop rule, the mutual exclusion, both per-command thresholds, the golden sha256, an AST import-set assertion, and a malformed-stdin fail-closed case"
  - "Canonical test command for .orchestrator.json test_verify_cmd: python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'"
  - "STDIN/STDOUT JSON envelope contract for the score.py batch filter (one invocation per review pass)"
affects: [16-02, "phase-17-robustness-hardening", "review.md Phase 3/4.5 orchestrator integration"]

# Tech tracking
tech-stack:
  added: ["Python 3 stdlib unittest (first test harness in the plugin)", "Python score.py (first executable code in a previously prose-only plugin)"]
  patterns: ["stdin->JSON / stdout->JSON pure-function batch filter (no I/O beyond the shim)", "AST-based import-set enforcement test", "golden-hash freezing to detect encoding/separator/order drift", "fail-closed __main__ shim (let json.JSONDecodeError propagate => non-zero exit)"]

key-files:
  created:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
  modified:
    - .gitignore

key-decisions:
  - "Behavior-preserving extraction: transcribed scoring.md formula + review.md:685,:774 byte-for-byte; no weight/bonus/band-cutoff/threshold retuned"
  - "Single-file module (not a package) exposing pure functions + a run() orchestrator + a thin stdin/stdout shim — the shim is the only I/O"
  - "Import set held to EXACTLY {json, hashlib, re, sys}; enforced by an AST walk in the test (catches `from os import path` where grep cannot)"
  - "Golden sha256 f8fe7467...062d frozen as a literal in test_score.py to detect any stable_hash drift (it keys medium_acknowledgments)"
  - "Cross-confirm stays the current case-insensitive substring rule (D-15); carry-forward stays first-line strip-both-sides compare (D-11) — Phase 17 hardens these"

patterns-established:
  - "Pure-function deterministic core: orchestrator pre-resolves all raw facts (changed_line_ranges, source_window, canonical_line_content, file_line_totals); the script only decides — no git/file/subprocess I/O"
  - "Fail-closed batch filter: unparseable stdin propagates and exits non-zero so the orchestrator's gate can fail the review closed"
  - "Locked scoring operation order: additive bonuses -> intent-doc elif penalty -> severity weight LAST -> drop-if-pre-clamp<0 -> clamp [0,100] -> band -> per-command threshold"

requirements-completed: [CORE-01, CORE-02]

# Metrics
duration: ~3min
completed: 2026-06-24
---

# Phase 16 Plan 01: Deterministic-Core Script Summary

**Stdlib-only `score.py` (json/hashlib/re/sys) extracts the orchestrator's by-hand scoring into a pure-function stdin->JSON/stdout->JSON batch filter, pinned by the plugin's first test suite (66 unittest cases incl. a frozen golden sha256, an AST import-set guard, and a fail-closed malformed-stdin case).**

## Performance

- **Duration:** ~3 min (TDD: RED at 19:03, GREEN + gitignore by 19:05)
- **Started:** 2026-06-24T19:03:23-04:00
- **Completed:** 2026-06-24T19:05:44-04:00
- **Tasks:** 3 (two TDD-structured + one housekeeping)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments
- Created `score.py` — the FIRST executable code in this previously prose-only plugin: pure functions for the score formula, banding, per-command threshold filter, silenced-marker grep (±2 window), sha256 stable hash, carry-forward compare, and cross-confirm grouping, plus a `run(envelope)` orchestrator and a fail-closed `__main__` shim.
- Created `test_score.py` — the FIRST test suite in the plugin: 66 stdlib-unittest cases pinning every band boundary (95/94/80/79/70/69), every severity branch (incl. the −8 unset fallback), every additive modifier in isolation, the intent-doc mutual exclusion (elif, strictly greater-than), the drop-if-pre-clamp<0 rule, both per-command thresholds, the carry-forward and cross-confirm logic, the golden sha256, an AST import-set assertion, and a malformed-stdin fail-closed test.
- Froze the golden digest `f8fe7467da9406d41884788810d99b9c5800f9134b46fce10a82bda35258062d` for `stable_hash("a.py", "  x=1", "title")` so any encoding/separator/field-order drift fails the suite (this hash keys `medium_acknowledgments`).
- Held the import set to exactly `{json, hashlib, re, sys}` (no os/pathlib/subprocess/open/eval/exec/compile/__import__), enforced structurally by an AST walk.
- Gitignored `plugins/vibe-check/scripts/__pycache__/` while keeping `score.py` and `test_score.py` tracked (they ship with the plugin).

## Task Commits

Each task was committed atomically (TDD: test -> feat):

1. **Task 1: Write the failing pinning test suite** - `c6b6bee` (test) — RED, 66 cases bound to the not-yet-written `score` module
2. **Task 2: Implement score.py to GREEN** - `21306ce` (feat) — all 66 tests pass
3. **Task 3: Gitignore __pycache__ + confirm canonical test command** - `d254701` (chore)

_Note: the two TDD tasks produced a `test(...)` RED commit then a `feat(...)` GREEN commit; no REFACTOR commit was needed (implementation passed clean on first write)._

## Files Created/Modified
- `plugins/vibe-check/scripts/score.py` (created, 423 lines) - the deterministic-core scoring filter: pure functions + `run()` orchestrator + fail-closed stdin/stdout shim; imports ONLY json/hashlib/re/sys.
- `plugins/vibe-check/scripts/test_score.py` (created, 613 lines) - stdlib unittest suite pinning the formula, bands, thresholds, drop rule, mutual exclusion, carry-forward, cross-confirm, the golden sha256, the AST import-set guard, and the fail-closed malformed-stdin case.
- `.gitignore` (modified, +4 lines) - excludes `__pycache__/`; `score.py`/`test_score.py` remain tracked.

## Output Contract (recorded per plan <output>)

- **Public functions exported by score.py:** `stable_hash(file, canonical_line_content, title)`, `band_for(score)`, `silenced_nearby(source_window)`, `carry_forward_status(finding, canonical_line_content)`, `cross_confirm_group(findings)`, `compute_score(finding, *, in_diff, silenced, cross_confirmed, persisted)`, `run(envelope)`. (Internal helpers: `_first_line`, `_intent_doc_penalty`, `_titles_match`, `_line_in_ranges`, `_score_member`.)
- **STDIN envelope keys chosen:** `command` ("review"|"deep-review"), `all_mode` (bool), `pass_number` (int), `changed_line_ranges` ({file: [[start,end],...]}), `reviewed_union` ([file], --all), `file_line_totals` ({file: N}, --all), `carryforward` ([prior-pass findings, each carrying `canonical_line_content`]), `findings` ([agent-output-schema findings + per-finding raw facts `agent`, `source_window`, `canonical_line_content`]).
- **STDOUT envelope keys:** `scored_by_script` (true — the D-10 pass-level sentinel), `findings` (survivors with input fields preserved verbatim + ADDED `orchestrator_score`, `band`, `status`, `stable_hash`, `attribution`), `fixed_since_last` ([{file,line,title,band,first_pass_N}]), `filtered` ([{file,line,title,reason}], reason ∈ {silenced, sub-threshold, not-in-reviewed-set}).
- **Frozen golden-hash test value:** `f8fe7467da9406d41884788810d99b9c5800f9134b46fce10a82bda35258062d` (= `sha256(("a.py"+"\n"+"  x=1"+"\n"+"title").encode()).hexdigest()`).
- **Exact import set:** `{json, hashlib, re, sys}` — nothing else.
- **Fail-closed behavior on bad stdin:** `json.load(sys.stdin)` is NOT wrapped in a swallowing try/except; on unparseable stdin the `json.JSONDecodeError` propagates and the process exits non-zero (verified: `printf 'not json' | python3 score.py` => exit 1; empty stdin => exit 1).
- **Canonical test command for `.orchestrator.json` `test_verify_cmd`:** `python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'` (runs from repo root, exits 0).

## Decisions Made
- Followed the plan and locked CONTEXT decisions (D-01..D-15) exactly. Notable confirmations during execution:
  - **D-12 mutual exclusion** implemented as `elif` with strictly greater-than thresholds; pinned that 0.95 => −100 only (not −130), 0.9 => −30 (partial, since 0.9 is NOT > 0.9), 0.7 => no penalty.
  - **D-14 drop-vs-clamp ordering**: `compute_score` returns `None` (the drop signal) when pre-clamp < 0; `run()` records the dropped finding in `filtered[]` and never emits it — pinned via the `conf=40, silenced −50, severity −8 => −18 => DROP` case.
  - **D-13 ±2 window** inclusive both directions; pinned markers at both window edges.
  - **D-05 boundary**: `run()` recomputes `in_diff` from `changed_line_ranges` and `silenced` from `source_window`, overriding agent self-reports (agent-output-schema hard rule #4) — pinned via an out-of-diff finding whose agent claimed in_diff=true.
  - **--all mode**: `in_reviewed_set` (membership in `reviewed_union` AND 1<=line<=N) is a TRANSIENT keep/drop boolean, not serialized onto the finding; `in_diff` +20 never fires in --all (correct).
- Did NOT pre-build Phase 17 work: no Jaccard, no windowed hash, no full machine-checkable invariant. Cross-confirm stays substring; carry-forward stays first-line strip-both-sides.

## Deviations from Plan

None - plan executed exactly as written. (One documentation-only adjustment, not a behavior deviation: see Issues Encountered.)

## Issues Encountered
- **Belt-and-suspenders forbidden-call grep false-positive on the module docstring.** The plan's acceptance-criteria grep (`\bsubprocess\b|\bos\b|...`, excluding only `#`-prefixed comment lines) matched the prose words "subprocess I/O" and "no os, no pathlib" inside score.py's module docstring — not actual calls. The authoritative AST import-set test (which ignores string-literal/docstring tokens by design) passed. To keep the grep gate cleanly green for any downstream verifier, the docstring was reworded ("filesystem, git, or shell-out I/O"; "the AST import-set test enforces this") with zero behavior change. After the reword: the forbidden-call grep returns nothing, all 66 tests still pass, fail-closed still exits 1.

## Verification Results
- `python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'` => OK (66 tests), exit 0.
- Import-set grep (`^(import|from)` lines minus json/hashlib/re/sys) => empty (PASS).
- Forbidden-call grep (os./subprocess/pathlib/eval(/exec(/compile(/__import__/open(, comments excluded) => empty (PASS).
- Fail-closed: `printf 'not json' | python3 score.py` => exit 1; empty stdin => exit 1.
- Golden-hash literal present in test (`grep -c` => 1).
- `git check-ignore score.py` / `test_score.py` => exit 1 (they ship); `__pycache__/` IS ignored; no `__pycache__` tracked.
- Smoke: a minimal valid envelope yields stdout JSON with `"scored_by_script": true` and a survivor carrying `orchestrator_score`/`band`/`stable_hash`/`attribution` with all input fields preserved.

## Threat Surface Scan
No new security-relevant surface beyond the plan's `<threat_model>`. The script introduces NO network endpoint, NO filesystem/auth path, and NO subprocess — its import set is structurally restricted to {json,hashlib,re,sys} (AST-enforced), and the stdin/stdout shim is the only I/O. The mitigations for T-16-01 (golden-hash freeze), T-16-02 (defensive coercion of garbage severity / malformed intent_doc_match + fail-closed stdin), and T-16-03 (no shell/eval/os; AST import guard) are all implemented and tested.

## Next Phase Readiness
- **16-02 (CORE-03 orchestrator integration)** is unblocked: the stdin/stdout envelope contract, the `scored_by_script` sentinel, and the fail-closed non-zero exit are all in place. 16-02 wires `review.md` Phase 3/4.5 to pipe findings through `score.py` (resolved by the cache-glob path pattern), deletes the five by-hand Phase-3 scoring prose blocks + the Phase-4.5 stable_hash line, and adds the render-gate sentinel assertion.
- **Phase 17 (ROBUST-02/03/04)** now hardens executable code with tests rather than prose: the cross-confirm substring matcher and the carry-forward first-line compare are isolated, tested pure functions ready to harden, and the `scored_by_script` sentinel is the seam for the full machine-checkable invariant.
- **TEST-VERIFY gate** now has tests to run: record `python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'` as `.orchestrator.json`'s `test_verify_cmd` if auto-detect misses it (D-08).

## Self-Check: PASSED

- Created files exist: `plugins/vibe-check/scripts/score.py`, `plugins/vibe-check/scripts/test_score.py`, `.planning/phases/16-deterministic-core-script/16-01-SUMMARY.md` — all FOUND.
- Task commits exist: `c6b6bee` (test/RED), `21306ce` (feat/GREEN), `d254701` (chore/gitignore) — all FOUND.

---
*Phase: 16-deterministic-core-script*
*Completed: 2026-06-24*
