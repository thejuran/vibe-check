---
phase: 36-b3-first-measured-quality-numbers
plan: 03
subsystem: testing
tags: [efficacy, catch-rate, false-positive-rate, ground-truth, pre-registration, scoring, b3]

# Dependency graph
requires:
  - phase: 36-01
    provides: "committed B3 run-kit + pre-registered answer key (ANSWER_KEY_COMMIT ef0ab67, separate PREREGISTRATION.md manifest at cca63e2)"
  - phase: 36-02
    provides: "18/18 owner-driven /deep-review runs archived + verified (6 diffs x N=3), isolated + pinned + tree.diff-integrity-verified"
provides:
  - "SCORING-b3.md — auditable per-run SITE/AXIS/BAND worksheet headed by the full pre-registration gate results + scoreable-completeness ledger"
  - "First aggregate catch-rate (8/9) / false-positive-rate (6/9) report appended to RESULTS-v2.9.md"
  - "D-11 verdict: PROCEED on H-CORE/H-LANE/B-SEV/B-REWEIGHT; NEED MORE DATA on the coarse N=3 rate — the input to next-milestone B3-gated-challenge scoping"
affects: [phase-37-close, milestone-v2.9-close, scorer-design-challenges, next-milestone-b3-growth]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Score-from-blob provable measurement: key read ONLY from git show ANSWER_KEY_COMMIT:<key> (hash from git show MANIFEST_COMMIT:PREREGISTRATION.md), never the live file — an output-dependent key/manifest edit is structurally inert"
    - "No-aggregation-over-holes: isolation (len(passes)==1) + pin (head_sha==base_sha) + full-worktree tree.diff sha gate every run; incomplete run set EXITS NON-ZERO before aggregation (owner-waiver-only escape)"
    - "D-07 three-gate catch rule mechanized: SITE and AXIS and BAND independent; right-site-wrong-axis = detected-below-threshold MISS (the autoescape run-1 case)"

key-files:
  created:
    - "docs/design/b3-ground-truth/SCORING-b3.md"
  modified:
    - "plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md"

key-decisions:
  - "Catch-rate 8/9, FP-rate 6/9 — the first measured numbers, over FULL pre-registered denominators (9+9), zero holes, no owner waiver"
  - "autoescape run-1 scored a MISS (detected-below-threshold): SITE ok but the fleet named a deprecation/breaks-startup axis, one finding explicitly said 'NOT an XSS regression' — right-site-wrong-axis per D-07/A16"
  - "D-11 verdict = PROCEED on the FP+axis-stability challenges (H-CORE/H-LANE/B-SEV/B-REWEIGHT) AND grow the set next milestone (N=3 coarse); NOT an in-phase scorer change (formula stays frozen)"

patterns-established:
  - "Score-from-committed-blob pre-registration gate: derive MANIFEST_COMMIT (last manifest commit strictly preceding first runs/ commit), read proof from its blob, digest-verify the key blob, prove ancestry + runs-descent, EXIT NON-ZERO on any failure"
  - "Every efficacy aggregate must be re-derivable from raw state + committed key blob via an auditable per-run worksheet (SCORING-b3.md is the trail behind the headline)"

requirements-completed: [B3-02, B3-03]

# Metrics
duration: 15min
completed: 2026-07-05
---

# Phase 36 Plan 03: B3 First Measured Quality Numbers Summary

**vibe-check's first-ever aggregate quality numbers — catch-rate 8/9, false-positive-rate 6/9 — scored from 18 owner-driven /deep-review runs against a cryptographically pre-registered answer-key blob, with a D-11 verdict to PROCEED on the FP-driving design challenges.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-05T18:05Z (approx)
- **Completed:** 2026-07-05T18:20Z (approx)
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 appended)

## Accomplishments

- **Pre-registration gate PASS end-to-end** — derived FIRST_RUNS_COMMIT (`eca98ec`) and MANIFEST_COMMIT (`cca63e2`), proved no post-run/same-commit manifest edit, read ANSWER_KEY_COMMIT (`ef0ab67`) + ANSWER_KEY_SHA256 from the committed manifest blob, digest-matched the key blob, proved ancestry + runs/-clean + descent from key AND manifest, and confirmed all 6 diffs' full-worktree tree.diff shas identical across their 3 runs == kit value.
- **Security spot-check CLEAN** — the first secret-in-logs run's archived state carries no literal *arr API key (the buggy `exc=exc` captures an object, not a key).
- **Complete scoreable set, zero holes** — all 18 expected runs (6 diffs × 3) passed isolation (`len(passes)==1`) + pin (`head_sha==base_sha`) + tree.diff integrity → 3/3 scoreable per diff, aggregation authorized without any owner waiver.
- **SCORING-b3.md** written as the auditable worksheet: gate header + completeness ledger + per-run SITE/AXIS/BAND verdicts (catch/miss/detected-below-threshold/FP/noise-note/clean).
- **First aggregate report appended to RESULTS-v2.9.md** (reserved seam, no RESULTS-v3.md): catch-rate 8/9, FP-rate 6/9 as exact fractions (D-09 no rounding), per-run + per-diff tables, honest limitations, D-11 verdict, and a plain-language owner summary.
- **Scoring code stayed byte-frozen** (`score.py`/`test_score.py`/`config.py`); `pytest -q` green (356 passed, 221 subtests).

## Task Commits

Each task was committed atomically:

1. **Task 1: Pre-registration gate + score every isolated run into SCORING-b3.md** - `70db6ba` (feat)
2. **Task 2: Aggregate (D-09) + append catch/FP report to RESULTS-v2.9.md** - `0a32230` (docs)

**Plan metadata:** (final commit below — this SUMMARY + STATE + ROADMAP + REQUIREMENTS)

## Files Created/Modified

- `docs/design/b3-ground-truth/SCORING-b3.md` (created) - Per-run scoring worksheet: full pre-registration gate results (manifest ordering, MANIFEST_COMMIT derivation, key-blob digest, ancestry, runs/-clean + descent, per-diff tree.diff consistency), scoreable-completeness ledger (18/18, no waiver), and per-run SITE/AXIS/BAND verdicts.
- `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` (appended) - New top-level B3 section with the first aggregate catch-rate 8/9 / FP-rate 6/9, per-run + per-diff tables, honest limitations, D-11 verdict, plain-language owner summary. Closes the RESULTS.md:64 "no aggregate numbers" gap.

## Detailed Results

**Should-catch (catch-rate 8/9):**
- triggarr-secret-in-logs: 3/3 catch (codex named the credential leak all 3 runs)
- triggarr-autoescape: 2/3 catch — run-1 = the pre-registered SUBTLE right-site-wrong-axis MISS (fleet framed the reverted line as deprecation/breaks-startup, one finding explicitly wrote "NOT an XSS regression"); runs 2-3 named the XSS/autoescape mechanism and caught it
- third-organic-should-catch (unclamped %): 3/3 catch

**Should-quiet (FP-rate 6/9):**
- should-quiet-2 (rest.service.ts): 0/3 FP — clean all 3 runs (0 findings)
- should-quiet-1 (validation.py SSRF tightening): 3/3 FP — multi-lane critical/warning SSRF-bypass alarms, self-sufficient scores (not cross-confirm-rescued) → H-CORE + H-LANE
- should-quiet-3 (transfer.py boundary-add): 3/3 FP — cross-lane noise (coverage-gap / default-semantics / id-contract) → H-LANE + B-SEV

**Codex (D-13):** contributed a surviving finding to all 8 catches; ran `codex=auto` (shipped default, no `--codex` forcing).

## Decisions Made

- Scored autoescape run-1 as `detected-below-threshold` (MISS) rather than a catch, applying D-07/A16 strictly: SITE landed but every finding named the wrong axis (deprecation, not XSS). This is the exact subtle case the answer key pre-registered — crediting it would have inflated catch-rate to 9/9 dishonestly.
- Treated D-08 FP as NOT site-gated (any critical/warning finding on a should-quiet diff = FP), per the committed key's literal rule — including findings outside the feature hunk (e.g. should-quiet-3's L259 default-fallback warning).
- Mapped failure modes to challenges from the committed D-11 blob: should-quiet FPs are agent-self-sufficient (not +10 cross-confirm rescues), so they implicate H-CORE/H-LANE (agent-side, multi-lane), not primarily H-DUP/B-XCONF — recorded H-DUP/B-XCONF as weakly-implicated watch-fors, not triggered.
- D-11 verdict = PROCEED on the FP-driving + axis-stability challenges AND grow the set next milestone (N=3 coarse). Kept it explicitly as the INPUT to next-milestone scoping, not an in-phase scorer change (formula frozen this milestone).

## Deviations from Plan

None - plan executed exactly as written. All hard gates (0, a, b, e) held, step (f) had zero unscoreable runs, the set was complete (18/18), so no hard-stop and no owner waiver was needed. Both automated verify blocks passed; the byte-frozen assertion and pytest regression guard both held.

## Issues Encountered

- A shell `for`-loop over git commits for the tree.diff check timed out at 2 min (likely slow git/shell overhead on the large working tree). Reran the identical logic as a self-contained Python file-hash pass (no git calls) — same assertion, fast, all 6 diffs PASS. No change to the gate semantics.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **B3-02 (scoring half) and B3-03 are DONE** — the milestone now has its first measured, provable catch-rate / FP-rate.
- **Phase 37 (close) is ready:** bump plugin 2.8.0 → 2.9.0, annotated tag `v2.9`, publish, milestone audit. The B3 report is committed evidence; owner sign-off is the live checkpoint at close.
- **Feeds next-milestone scoping:** the D-11 verdict names H-CORE/H-LANE/B-SEV/B-REWEIGHT as the challenges the FP-rate implicates, and "grow the committed set" as the data next-step — the explicit input to the B3-gated scorer design work (still out of scope this milestone; formula frozen).

## Self-Check: PASSED

- FOUND: docs/design/b3-ground-truth/SCORING-b3.md
- FOUND: plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md
- FOUND: .planning/phases/36-b3-first-measured-quality-numbers/36-03-SUMMARY.md
- FOUND commit: 70db6ba (Task 1)
- FOUND commit: 0a32230 (Task 2)

---
*Phase: 36-b3-first-measured-quality-numbers*
*Completed: 2026-07-05*
