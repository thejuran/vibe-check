---
phase: 17-robustness-on-the-core
plan: 02
subsystem: scoring
tags: [score.py, carry-forward, low-entropy, canonical_window, ROBUST-03, unittest, vibe-check]

# Dependency graph
requires:
  - phase: 16-deterministic-core-script
    provides: "score.py carry_forward_status + _first_line + the frozen stable_hash golden digest"
  - phase: 17-robustness-on-the-core
    plan: 01
    provides: "the Wave-1 matcher changes already on the base (untouched by this plan)"
provides:
  - "SYMMETRIC-OR-DEGRADE low-entropy carry key in score.py (ROBUST-03): carry_forward_status widens BOTH sides or NEITHER, never window-vs-single-line"
  - "_carry_key / _nonblank_lines / _is_low_entropy helpers (first <=3 stripped non-blank lines; low-entropy = len<4 OR pure punctuation)"
  - "canonical_window envelope field resolved in review.md Phase 3 step 0 (additive, carry-forward-only, never feeds stable_hash)"
  - "18 new test pins: single-line no-churn (BLOCKER-1), multi-line disambiguation, multi-line unchanged stays persisted, degrade-when-no-window, stable_hash-unchanged"
affects: [17-03, 18-close, ROBUST-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Symmetric-or-degrade compare: widen BOTH sides to a >=2-line window or degrade to the first-line compare — never a window-vs-single-line asymmetry that would false-flip a legal single-line snippet"
    - "Low-entropy fallback (widen only when needed) keeps the distinctive-first-line common case byte-identical to today (no churn)"
    - "A new carry key (_carry_key) kept strictly SEPARATE from the canonical_for_hash path so the frozen stable_hash golden does not move (D-07)"

key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/commands/review.md

key-decisions:
  - "Low-entropy first line = len(stripped) < 4 OR re.fullmatch(r'[\\s\\W]+', first) truthy (pure punctuation/whitespace/brackets: }, );, }), ])"
  - "_carry_key = first <=3 stripped NON-BLANK lines joined with newline; blank lines skipped so cosmetic blank-line drift does not move the key"
  - "WIDEN-ELIGIBLE iff LHS first line low-entropy AND prior current_code has >=2 non-blank lines AND canonical_window has >=2 non-blank lines — else DEGRADE to today's first-line compare"
  - "_first_line and the _score_member canonical_for_hash derivation are UNTOUCHED; canonical_window is consumed ONLY by carry_forward_status (D-07)"
  - "review.md resolves canonical_window in the SAME Phase 3 step 0 HEAD read (no second read tool); additive + carry-forward-only so diff-mode envelope shape is byte-unchanged"

patterns-established:
  - "Widen-both-or-neither is the durable anti-pattern for asymmetric content compares: never compare a resolved window against an un-widened single value"

requirements-completed: [ROBUST-03]

# Metrics
duration: ~25min
completed: 2026-06-25
---

# Phase 17 Plan 02: Symmetric-or-Degrade Low-Entropy Carry Key Summary

**Hardened the carry-forward content key in `score.py` (ROBUST-03) so a low-entropy first line (`}`, `);`) is disambiguated by surrounding context WITHOUT ever churning an unchanged finding — the compare now widens BOTH sides to a >=2-line window or DEGRADES to the first-line compare, never a window-vs-single-line asymmetry; the frozen `stable_hash` golden is unmoved (D-07).**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-06-25 (worktree base 71b56b9 — Wave 1's matcher changes present)
- **Completed:** 2026-06-25
- **Tasks:** 2 (Task 1 was TDD: test -> feat)
- **Files modified:** 3

## Accomplishments
- `carry_forward_status` is now SYMMETRIC: it widens BOTH the stored `current_code` and the orchestrator-resolved `canonical_window` to a >=2-line key, OR degrades to the first-line compare — it never compares a multi-line window against a single line. This closes round-2 BLOCKER 1: a legal `current_code="}"` against an unchanged HEAD (where the orchestrator resolves `canonical_window="}\n  nextLine()"`) now stays **persisted**, instead of the round-1 fix's false flip to needs-recheck.
- The widen branch fires ONLY when ALL of: the prior first line is low-entropy (`len<4` OR pure punctuation/whitespace) AND the prior `current_code` has >=2 non-blank lines AND `canonical_window` has >=2 non-blank lines. So a distinctive first line (common case) and a legal single-line low-entropy snippet both DEGRADE to today's byte-identical first-line compare (no churn).
- The collision is gone where it matters: a multi-line low-entropy finding whose surrounding window genuinely CHANGED (`}\n  doThingA()` vs HEAD `}\n  doThingB()`) correctly flips to **needs-recheck**, while the same finding against an UNCHANGED window stays **persisted**.
- `_carry_key` / `_nonblank_lines` / `_is_low_entropy` are new helpers kept strictly SEPARATE from the `canonical_for_hash` path. `_first_line` and the `_score_member` hash derivation are untouched; the frozen `stable_hash` golden (`7a516d01...793124`) is byte-identical (verified live). The import set stays `{json,hashlib,re,sys}` (AST test green).
- `review.md` Phase 3 step 0 resolves `canonical_window` in the SAME HEAD read (no second read tool) — the line at `file:line` plus its next <=2 non-blank HEAD lines — and the envelope carries it on each carryforward entry. It is ADDITIVE and carry-forward-only: diff-mode findings carry no window (envelope shape byte-unchanged), it is consumed ONLY by `carry_forward_status`, and it never feeds `stable_hash` (D-07).
- 18 new test pins (full suite 91 -> 109, all green): `_carry_key` isolation, single-line no-churn (BLOCKER-1), multi-line disambiguation, multi-line unchanged stays persisted, degrade-when-no-window, non-str-current_code-no-raise, and three run() end-to-end pins including a `stable_hash`-unchanged golden over the low-entropy carryforward path.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): failing ROBUST-03 carry-forward windowing pins** - `7e66b4b` (test)
2. **Task 1 (GREEN): symmetric-or-degrade low-entropy carry key** - `b852fde` (feat)
3. **Task 2: resolve canonical_window in review.md Phase 3 step 0** - `5771ef5` (docs)

_TDD task 1 produced a test commit then a feat commit; no refactor commit was needed (the GREEN implementation was already clean)._

## Files Created/Modified
- `plugins/vibe-check/scripts/score.py` - Added `_nonblank_lines`, `_carry_key`, `_is_low_entropy`; rewrote `carry_forward_status(finding, canonical_line_content, canonical_window=None)` with the WIDEN-ELIGIBLE-or-DEGRADE logic; updated the `run()` call site to pass `cf.get("canonical_window")`. `_first_line` and the `_score_member` `canonical_for_hash` derivation are unchanged. Import set unchanged.
- `plugins/vibe-check/scripts/test_score.py` - Added `TestCarryForwardLowEntropyWindow` (11 status pins), `TestCarryKey` (5 helper pins), and `TestCarryForwardWindowEndToEnd` (3 run() pins incl. the stable_hash-unchanged golden). The two existing no-churn tests (`test_matching_first_line_is_persisted`, `test_whitespace_drift_both_sides_stripped_still_persisted`) and the frozen `stable_hash` golden tests are UNMODIFIED and green.
- `plugins/vibe-check/commands/review.md` - Phase 3 step 0 (line ~678) resolves `canonical_window` in the same HEAD read; the envelope-build field list (line ~718) carries it on each carryforward entry. Additive + carry-forward-only + never-feeds-hash notes added. No scoring/threshold/band edits.

## Decisions Made
- Followed the plan's locked low-entropy definition and widen-both-or-neither logic exactly. No discretionary deviations.
- Added a few extra defensive helper pins (blank-line skipping, line stripping, three-non-blank-line window keying, genuine-third-line-change detection, non-str-current_code) beyond the plan's enumerated Tests 1-7 — these strengthen the same invariant and all pass; they do not change behavior.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The plan/context files (`17-02-PLAN.md`, `17-CONTEXT.md`) are NOT carried into this worktree because `.planning/` is gitignored and the worktree was reset to the merge base; they were read from the main repo checkout at `/Users/julianamacbook/turingmind-code-review/.planning/...`. This is expected for this repo (a documented gotcha) and did not block execution.
- `.planning/` is gitignored in the worktree, but prior-phase SUMMARYs are tracked in git. This SUMMARY is therefore force-added (`git add -f`) to match the existing tracked-SUMMARY convention so it survives the worktree teardown.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ROBUST-03 is complete and pinned. 17-03 (ROBUST-04 render gate / dispatch warn) is independent of this carry-forward change and unblocked.
- Verification gate green: `cd plugins/vibe-check/scripts && python3 -m unittest` -> Ran 109 tests, OK (TestImportSet green; import set still {json,hashlib,re,sys}; stable_hash golden `7a516d01...793124` byte-identical, verified live).

## Self-Check: PASSED

- `17-02-SUMMARY.md` exists in the plan directory (force-added).
- All commits present: `7e66b4b` (test), `b852fde` (feat), `5771ef5` (docs review.md).
- `cd plugins/vibe-check/scripts && python3 -m unittest` -> Ran 109 tests, OK.
- score.py import set still exactly {json,hashlib,re,sys}; `_first_line`/`canonical_for_hash` unchanged; `stable_hash` golden unmoved.
- STATE.md / ROADMAP.md untouched by this worktree (orchestrator owns those writes after the wave).

---
*Phase: 17-robustness-on-the-core*
*Completed: 2026-06-25*
