---
phase: 17-robustness-on-the-core
plan: 03
subsystem: orchestrator-gate
tags: [review.md, render-gate, dispatch-warn, codex-adversarial, single-writer, ROBUST-04, ROBUST-01, unittest, vibe-check]

# Dependency graph
requires:
  - phase: 16-deterministic-core-script
    provides: "score.py scored_by_script sentinel (run()) + the single-writer collapse of orchestrator_score/band/status/stable_hash/attribution; the fail-closed __main__ posture"
  - phase: 17-robustness-on-the-core
    plan: 01
    provides: "the Wave-1 matcher + attribution arrays (the cross-confirm attribution the D-09 RETURNED set reads); untouched by this plan"
  - phase: 17-robustness-on-the-core
    plan: 02
    provides: "the Wave-2 carry-forward + canonical_window edits already on the base; untouched by this plan"
provides:
  - "HARD render gate in review.md Phase 4 (ROBUST-04 D-08): absent scored_by_script sentinel (or any finding missing band/orchestrator_score) HALTS with an explicit error and renders NOTHING — no hand-scored fallback"
  - "codex-aware parallel-dispatch detect-and-WARN in review.md Phase 4 (D-09): EXPECTED = agents_run PLUS codex-adversarial IFF Codex joined (not CODEX_SKIPPED); detect-and-warn only, never halts, never drops a finding; a normal Codex deep-review never misfires"
  - "TestSingleWriterLock + has_scored_field_write_path in test_score.py (ROBUST-01 D-10): an all-prose scored-field-write-directive guard, proven sound (no SCOPE_HASH false positive) and complete (catches unfenced prose writers + hasher-tied-to-scored-field)"
  - "10 new test pins (suite 109 -> 119, all green)"
affects: [18-close, ROBUST-04, ROBUST-01, deep-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Render-time fail-closed twin of the Phase-3 scoring fail-closed check: rendered findings exist ONLY because the script stamped them"
    - "Codex-aware EXPECTED set keyed on JOIN-vs-CODEX_SKIPPED (a verdict-approve zero-finding object counts as joined), so a legibility check never misfires on the one non-native agent"
    - "Clause-scoped all-prose write-path detector: split on newline/;/. so negation-exemption and hasher-tie are LOCAL — same-clause co-occurrence is what keeps the SCOPE_HASH line exempt"
    - "Machine-assignment form requires a COMPUTED value (quote / shell-sub / hasher) after `field=`, so `band=critical` (a bare-word read filter) and `band == medium` (comparison) and `medium_acknowledgments[stable_hash] =` (key-write of a different field) are all exempt"

key-files:
  created: []
  modified:
    - plugins/vibe-check/commands/review.md
    - plugins/vibe-check/scripts/test_score.py

key-decisions:
  - "Render gate is an UNHEDGED hard halt — removed the 'Keep this LIGHT … the full machine-checkable detect-and-warn invariant is Phase 17' seam sentence entirely (D-08)"
  - "D-09 EXPECTED set adds codex-adversarial ONLY when Codex joined (a codex-adversarial agent-response object was appended at Phase 3 entry, including a verdict-approve zero-finding object); CODEX_SKIPPED appends nothing, so codex-adversarial is absent from EXPECTED and a normal run produces zero dispatch warnings"
  - "deep-review.md NOT edited — it inherits review.md Phase 4 verbatim; its Phase-4 override (deep-review.md:282) only ADDS Architectural Notes + Impact Analysis"
  - "The single-writer detector requires the scored field as the DIRECT OBJECT of an imperative write verb (or a computed assignment), NOT mere co-occurrence — so 'the row's band derives from', 'write medium_acknowledgments[stable_hash]', and 'computes the canonical line content' are not false positives"
  - "Negated/forbidding clauses (do not / never / no longer / without / would create) are exempt — a negated directive is the OPPOSITE of a reintroduced writer (review.md:676/830)"
  - "score.py NOT modified; stable_hash golden unmoved; score.py import set untouched (only the TEST file gained `re`)"

patterns-established:
  - "All-prose write-path guard with same-clause tie + negation exemption is the durable lock pattern for 'single-writer of a scored field, enforced against prose the orchestrator follows'"
  - "Soundness is proven on the REAL files AND at unit level (the exact SCOPE_HASH line as a negative fixture); completeness is proven by synthetic positive fixtures incl. the unfenced-prose evasion hole — never by editing the real files"

requirements-completed: [ROBUST-04, ROBUST-01]

# Metrics
duration: ~30min
completed: 2026-06-25
---

# Phase 17 Plan 03: Hard Render Gate + Codex-Aware Dispatch Warn + Single-Writer Lock Summary

**Hardened the "scoring ran" invariant into an unhedged HARD render gate in `review.md` (absent `scored_by_script` ⇒ HALT, no report — ROBUST-04 D-08), added a codex-aware parallel-dispatch detect-and-WARN that never misfires on a normal Codex deep-review (D-09), and added an all-prose single-writer regression-lock to `test_score.py` that is both sound (no SCOPE_HASH false positive) and complete (catches an unfenced prose writer) — ROBUST-01 D-10. `score.py` is untouched; the suite is 109 → 119, all green.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-06-25 (worktree base ad80314 — Waves 1+2 present)
- **Completed:** 2026-06-25
- **Tasks:** 2 (both `type=auto`)
- **Files modified:** 2

## Accomplishments

- **ROBUST-04 D-08 — hard render gate.** The Phase-4 render gate in `review.md` is now an unhedged HARD halt: if the pass lacks `scored_by_script: true`, OR any to-be-rendered finding lacks `band`/`orchestrator_score`, the orchestrator HALTS, emits `scoring did not run — review halted; no report produced`, and renders NOTHING (no findings, no summary table, no band sections, no partial output). The `Keep this LIGHT … the full machine-checkable detect-and-warn invariant is Phase 17 / ROBUST-04` hedge sentence is removed entirely. Framed as the render-time twin of the Phase-3 fail-closed check — consistent with `score.py`'s `__main__` non-zero-on-bad-stdin posture.
- **ROBUST-04 D-09 — codex-aware dispatch detect-and-WARN.** Added a Phase-4 step (after the gate passes) comparing EXPECTED vs RETURNED agents. EXPECTED = the dispatched native `agents_run` (cross-chunk union in `--all`) PLUS `codex-adversarial` IFF Codex actually JOINED this pass (a `codex-adversarial` agent-response object was appended at Phase 3 entry — a `verdict: "approve"` zero-finding object COUNTS as joined; a `CODEX_SKIPPED` run appends nothing, so `codex-adversarial` is NOT in EXPECTED). RETURNED = the `agent` values across parsed responses UNION the `attribution` arrays on surviving findings. A mismatch emits a `⚠ Dispatch check:` note and CONTINUES — it never halts and never drops a finding. The codex-awareness is load-bearing: without it every normal Codex `/deep-review` would misfire as a foreign-agent mismatch.
- **deep-review.md inherits the gate verbatim — no edit.** Confirmed `deep-review.md:40` executes `review.md` Phase 4 by delegation, and its Phase-4 override (`deep-review.md:282`) only ADDS Architectural Notes + Impact Analysis. `git diff` shows deep-review.md unchanged since base.
- **ROBUST-01 D-10 — single-writer regression-lock.** Added `TestSingleWriterLock` + `has_scored_field_write_path(text)` to `test_score.py`. The guard scans the FULL text of `review.md`/`deep-review.md` (resolved relative to `os.path.dirname(SCORE_PY)` as `../commands/*.md`) — NOT fenced-only — and FAILS the lock iff EITHER (a) a scored-field SYNTHESIS exists (an imperative write verb directed AT a scored field, OR a machine-assignment form `field="..."`/`field=$((...))`) OR (b) a hasher token is TIED to a scored field (same-clause co-occurrence). Negated/forbidding clauses are exempt.
  - **Soundness proven** on the REAL files today (both return False) AND at unit level: the EXACT `SCOPE_HASH=$(... | shasum | cut -c1-12)` line, `band == medium`, `findings with band=critical, status=fixed-since-last`, `consume the stable_hash`, `the row's band derives from`, the `medium_acknowledgments[stable_hash] =` key-write, and the forbidding prose (`do NOT recompute the sha256 by hand`, `does NOT assign status`) all return False.
  - **Completeness proven** by synthetic positive fixtures: unfenced prose writers (`Compute stable_hash with sha256`, `set band to critical`, `Recompute the orchestrator_score by hand`, `Assign attribution …`), fenced machine writers (`band="critical"`, `orchestrator_score=$((conf + 20))`, `stable_hash=$(shasum -a 256 …)`), and a hasher-tied-to-stable_hash fixture all return True.
- **Suite 109 → 119, all green.** `cd plugins/vibe-check/scripts && python3 -m unittest` → Ran 119 tests, OK. `TestImportSet` green (score.py import set untouched); `TestStableHashGolden` green (golden unmoved). The test file gained `import re`; `score.py` is unchanged.

## Task Commits

Each task was committed atomically:

1. **Task 1: hard render gate (D-08) + codex-aware dispatch warn (D-09)** — `c5ea2d3` (feat)
2. **Task 2: single-writer regression-lock over all command prose (D-10)** — `7f09de4` (test)

## Files Created/Modified

- `plugins/vibe-check/commands/review.md` — Phase 4 render gate (line ~739) rewritten as an unhedged HARD halt (D-08), hedge sentence removed; added the codex-aware parallel-dispatch detect-and-WARN (D-09) with the EXPECTED = `agents_run` ∪ joined-Codex rule, the RETURNED = `agent` ∪ `attribution` rule, the two `⚠ Dispatch check:` warn forms, and the `--all` cross-chunk-union note. No scoring/threshold/band edits; no other phase touched.
- `plugins/vibe-check/scripts/test_score.py` — added `import re`; added `has_scored_field_write_path` (clause-scoped detector: `_DIRECTIVE_RE` / `_ASSIGN_RE` synthesis, `_HASHER_RE` + `_SCORED_FIELD_RE` same-clause tie, `_NEG_RE` negation exemption, `_writer_clauses` splitter) and `TestSingleWriterLock` (10 pins: 3 soundness-on-real-files incl. a non-vacuous "files were actually read + mention scored fields + contain SCOPE_HASH" guard, 3 completeness, 4 soundness-at-unit-level). `score.py` NOT modified.

## Decisions Made

- Followed the plan's locked D-08/D-09/D-10 design exactly. The one discretionary call: the machine-assignment form requires a COMPUTED value (quote / shell-sub / hasher) after `field=` rather than a bare word — this is what cleanly distinguishes the positive `band="critical"` from the legitimate read filter `band=critical` (review.md:64) without needing a separate read-context allowlist. Verified empirically against the real file before writing the test.
- The hasher-tie is same-clause (split on `;`/`.`/newline), per the plan's "same-line/same-sentence co-occurrence" — this is precisely what keeps the SCOPE_HASH line (whose clause references `SCOPE_HASH`/`ALL_STATE_FILE`, never `stable_hash`) exempt. A cross-clause `H=$(shasum …); stable_hash="$H"` is still caught — by the ASSIGN arm on the second clause, not the tie arm.
- Negation exemption (`do not`/`never`/`no longer`/`without`/`would create`) is deliberately broad on the safe side: it can let a writer phrased WITH a negation slip through, but a realistic by-hand reintroduction is an affirmative directive, and the alternative (false-positiving on the file's own forbidding prose) would make the lock fail today. The plan explicitly sanctions exempting negated clauses.

## Deviations from Plan

None — plan executed exactly as written. (Both tasks were `type=auto`, not TDD; no RED/GREEN split required by the plan. The detector was validated against the real files via a scratch probe before the test was written, so the committed test passed first-run after the `import re` fix.)

## Issues Encountered

- First suite run failed with `NameError: name 're' is not defined` — the test file imported `ast/itertools/os/subprocess/sys/unittest` but not `re`, which the new detector uses. Fixed by adding `import re` to the test-file imports (the import ban is on `score.py` only; `TestImportSet` reads `score.py`, not the test file, so it stays green). Rule 3 (blocking issue) auto-fixed.
- One new pin (`test_catches_hasher_tied_to_scored_field`) initially used a cross-clause fixture (`H=$(shasum …); … stable_hash …`) that the same-clause tie correctly did NOT match; corrected the FIXTURE to a same-clause form (the detector behavior is right — the tie is same-clause by design). Not a deviation; a fixture fix during Task 2.
- The plan/context files (`17-03-PLAN.md`, `17-CONTEXT.md`) are NOT in this worktree because `.planning/` is gitignored and the worktree was reset to the merge base; they were read from the main checkout at `/Users/julianamacbook/turingmind-code-review/.planning/...` (a documented repo gotcha). Did not block execution.
- `.planning/` is gitignored in the worktree, but prior-phase SUMMARYs are tracked in git. This SUMMARY is therefore force-added (`git add -f`) to match the existing tracked-SUMMARY convention so it survives the worktree teardown.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- ROBUST-04 and ROBUST-01 are complete and pinned. With ROBUST-01/02/03/04 all landed, Phase 17 (robustness on the core) is fully implemented; Phase 18 (CLOSE-01/02 — efficacy/version/tag close) is unblocked.
- Verification gate green: `cd plugins/vibe-check/scripts && python3 -m unittest` → Ran 119 tests, OK. `score.py` untouched (import set `{json,hashlib,re,sys}`, stable_hash golden unmoved); `deep-review.md` unchanged (inherits Phase 4 verbatim).

## Self-Check: PASSED

- `17-03-SUMMARY.md` exists in the plan directory (force-added).
- Both task commits present: `c5ea2d3` (feat), `7f09de4` (test).
- `cd plugins/vibe-check/scripts && python3 -m unittest` → Ran 119 tests, OK.
- review.md: hedge count 0; hard halt present (`review halted; no report`); codex-aware dispatch warn present.
- The single-writer guard returns False on the real review.md/deep-review.md (no SCOPE_HASH false positive) AND True on the unfenced-prose positive fixtures.
- `score.py` untouched; `deep-review.md` unchanged since base; STATE.md / ROADMAP.md NOT modified by this worktree (orchestrator owns those writes after the wave).

---
*Phase: 17-robustness-on-the-core*
*Completed: 2026-06-25*
