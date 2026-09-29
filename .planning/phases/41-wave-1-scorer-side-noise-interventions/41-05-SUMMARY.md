---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 05
status: complete
subsystem: scorer
tags: [b-reweight, scorer-03, d-15, d-06, d-08, d-09, t3, replay-guardrail]
requires: ["41-03 calibrate.py derive/--check + CALIBRATION-v2.10.md", "41-04 _second_opinion + LONE_LANE_BAND_CEILING (None override)"]
provides:
  - "score.py: AGENT_CONFIDENCE_OFFSET literal (== calibrate.derive), _agent_offset, compute_score(confidence_offset=0), _score_member(second_opinion=True)"
  - "templates/scoring.md § 'Lone-lane confidence calibration (B-REWEIGHT, D-15)'"
  - "test_calibrate.py TestEmbeddedEqualsDerived (fail-never-skip, perturbed-label mutation proof)"
  - "test_score.py TestAgentConfidenceOffset + BUGS_OFF re-pin helper"
  - "docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-reweight.md (ALONE replay)"
affects: [41-06 H-LANE (replay ALONE must override AGENT_CONFIDENCE_OFFSET={} as well as LONE_LANE_BAND_CEILING=null), 41-07 PLAN-COMMITS.json]
tech-stack:
  added: []
  patterns: ["derived constant embedded as a literal and bound to its derivation by a fail-never-skip test", "second opinion computed once per group before scoring and shared by the offset and the ceiling", "non-B-REWEIGHT test expectations compensate by the derived offset (BUGS_OFF) instead of hard-coding it"]
key-files:
  created:
    - docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-reweight.md
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/scripts/test_calibrate.py
    - plugins/vibe-check/templates/scoring.md
decisions:
  - "Embedded offsets are exactly calibrate.py derive: {architecture: -6, bugs: -2, impact: -12}; nothing tuned after the gate"
  - "The offset applies only when the group has no second opinion; the min_confidence filter, emitted agent_confidence and stable_hash read raw values"
  - "_agent_offset is coerce-or-default: non-str agent, unknown agent, non-int/bool/positive table value => 0"
metrics:
  duration: "~30 min"
  completed: 2026-09-29
  tasks: "3/3"
  files: 5
---

# Phase 41 Plan 05: B-REWEIGHT lone-lane confidence offsets — Summary

When a finding group has no second opinion (no joined Codex agreement, not carried forward from
an earlier pass), each member's starting confidence is now lowered by a per-agent offset derived
from the labeled B3 runs: architecture −6, bugs −2, impact −12. Every other agent gets no offset.
Replayed ALONE with the B-SEV ceiling switched off: **REGRESSED 0 · UNEVALUABLE 0**, and the
headline FP went from **16/18 to 14/18**.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 + 2 + 3 (one commit per D-09) | `0ee3818` | score.py literal + application, scoring.md block, test_calibrate + test_score locks and re-pins, B-REWEIGHT ALONE replay report |

The plan asked for a single commit so that B-REWEIGHT lands and is replayed by itself (D-09),
the same arrangement as 41-04. **B-REWEIGHT commit sha for 41-07's PLAN-COMMITS.json:
`0ee38186a0c5caba0fb22ad03b768415262bd5fd`.**

## Embedded offsets

`python3 plugins/vibe-check/scripts/calibrate.py derive` printed
`{"architecture": -6, "bugs": -2, "impact": -12}`. That output was embedded byte-for-byte as
`AGENT_CONFIDENCE_OFFSET`. `calibrate.py --check` exits 0 at the commit ("OK score.py
AGENT_CONFIDENCE_OFFSET equals the derivation").

## ALONE replay (observed, `replay.py candidate --name b-reweight --override 'LONE_LANE_BAND_CEILING=null'`, exit 0)

- Header: `overrides: {"LONE_LANE_BAND_CEILING": null}`. Scorer sha256 is
  `a63a62fd365bc1ec2f037c35fbec5395a61e2ba0a83c8640eecf1ebb0445c56b`, which matches
  `git show 0ee3818:plugins/vibe-check/scripts/score.py | shasum -a 256`. Baseline
  `blob: b21f7f3d…`.
- Protected catches: `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`. The AMENDED run is ledger
  008, unchanged.
- Guardrail: `kept 25 / protected 26 · REGRESSED 0 · UNEVALUABLE 0 · AMENDED 1`. Every kept catch
  stays critical. 24 of them score 100 and `runs/triggarr-autoescape/run-3` scores 98.
- Headline FP (should-quiet-1..6 ×3): **16/18 → 14/18**.
  - should-quiet-1: 3/3 → 3/3
  - should-quiet-2: 3/3 → 3/3
  - should-quiet-3: 3/3 → 2/3 (run-1 goes quiet)
  - should-quiet-4: 3/3 → 3/3
  - should-quiet-5: 1/3 → 0/3 (run-2 goes quiet)
  - should-quiet-6: 3/3 → 3/3
- Phase-40 should-quiet-5: **0/6 → 0/6**. v2.9 quiet (informational): **6/9 → 6/9**.
  should-quiet-7 (unlabeled, informational): 3/3 → 3/3.
- **No parameter was changed after seeing the gate.** α = 20 and MIN_LABELED = 5 were not
  touched, and the literal is exactly what `derive` printed.

## Verification (observed)

- Task 1 `<verify>` chain printed `B-REWEIGHT SMOKE OK {'architecture': -6, 'bugs': -2, 'impact': -12}`.
  A lone architecture finding at raw confidence 80, in the diff, scores 94 = min(94, 100 − 6).
  Its emitted `agent_confidence` is 80, and with `min_confidence: 79` it is not filtered.
- `grep -c '^import' score.py` = 4. `git diff` has no added or removed line that touches
  `stable_hash(` or `canonical_for_hash`. scoring.md lines 1–82 are byte-identical to HEAD; the
  new block starts at line 84. The new citation `scoring.md:86` points at the B-REWEIGHT
  "adjusted by a per-agent offset" line. No existing citation moved.
- Task 2 `<verify>` chain printed `B-REWEIGHT-TESTS-OK`.
  - `-k Embedded`: 3 passed, 0 skipped.
  - `-k TestAgentConfidenceOffset`: 14 passed, 13 subtests.
  - `skipTest|unittest.skip` count in test_calibrate.py: 0.
  - The `GOLDEN_DIGEST = ` line is not in the diff.
- Mutation proofs. Each was applied to score.py, run, and restored; `cmp` confirmed the restore.
  - Literal hand-edited to impact −13: Embedded tests 3 failed, and `--check` printed MISMATCH.
  - Offset applied even with a second opinion: 3 failed.
  - `min_confidence` filter made to read the offset: 1 failed.
  - Positive table values allowed: 1 failed.
  - Offset never applied: 6 failed.
- Perturbed-label test: flipping one impact `axis: true` in a calibration run moves the derivation
  off the literal, and the same method asserts the untouched manifest still equals it.
- Task 3: the report has exactly 1 commit. `test_replay.py -k Ordering` gives 1 passed with 2
  subtests (both reports). Before the commit it failed, as expected, because the report was
  uncommitted, the same pre-commit state 41-04 recorded. `calibrate.py --check` exits 0 at HEAD.
- Full suite `pytest plugins/vibe-check/scripts -q` after the commit: **1090 passed, 1174
  subtests, 0 failed**.
- The sealed roots (`runs`, `runs-v2.10`, `runs-v2.10-phase40`, PREREGISTRATION-v2.10.md) are
  unchanged (`git diff --quiet HEAD`).
- Exactly one commit in this plan touches score.py (`0ee3818`).

## Re-pinned expectations

The default agent in `make_finding` is `"bugs"`, which is now a keyed agent at −2. That touched
more tests than the plan expected: the plan only anticipated impact and architecture fixtures.
Instead of hard-coding −2, the re-pins use a module constant,
`BUGS_OFF = score.AGENT_CONFIDENCE_OFFSET.get("bugs", 0)`, so they stay correct after a
re-derivation. Each re-pin carries the comment `v2.10 Wave 1 B-REWEIGHT (D-15): lone bugs offset
BUGS_OFF`.

- **TestThresholds boundary envelope:** the input is compensated (`conf − BUGS_OFF`), so each
  boundary still sits exactly on 79/80 and 69/70.
- **TestRunEndToEnd `test_in_diff_recomputed_overrides_agent_claim`:** expects `85 + BUGS_OFF`.
- **TestRunThresholds envelope:** the input is compensated, so the score is still exactly 80.
- **TestRunMinConfidence dropped-neighbour:** expects `85 + BUGS_OFF` and `min(94, 95 + BUGS_OFF)`.
- **TestRunMinConfidence `test_exactly_n_survives`:** gets an in-diff range for the raw-70
  finding. The filter still reads the raw 70, and the +20 keeps the finding clear of the
  post-scoring cutoff.
- **TestStatusScrubbedOnNewFindings forged-persisted:** expects `85 + BUGS_OFF`.
- **TestMalformedResidualCrashSurfaces string-range:** the input is compensated, so the score is
  still 80. A wrong +20 would read 94.

## Deviations from Plan

1. **[Plan inaccuracy] The predicted FP and offsets differ from research's indicative values.**
   - Planned (research): offsets `{architecture: −11, impact: −18}` and headline 16/18 → 12/18,
     driven by should-quiet-2 (3→1) and should-quiet-3 (3→2).
   - Actual: the committed-manifest derivation (41-03) gives smaller offsets and keys `bugs`.
     should-quiet-2 does not move, should-quiet-3 goes 3→2, and should-quiet-5 goes 1→0. The
     result is 14/18.
   - Recorded as observed per D-08, with no retuning. The plan explicitly said to embed whatever
     `derive` printed.
2. **[Rule 3 - Blocking] 10 existing run()-level tests moved because the default fixture agent
   is `bugs`.** They were re-pinned with the offset-relative `BUGS_OFF` described above. No test
   was loosened: each still asserts an exact score or an exact boundary.
3. **[Rule 2] `_agent_offset` also treats a `bool` or positive table value as identity.** The
   plan asked for non-int ⇒ 0. The code additionally enforces lower-only on the table value,
   locked by `test_malformed_table_value_is_identity` (mutation: 1 failed).
4. The plan's Task-3 `<verify>` line `wc -l | grep -qx 1` fails on macOS because `wc` pads its
   output with spaces, as 41-04 also noted. Each part was run on its own and passed: the report
   has 1 commit, the Ordering test gives 1 passed, and `--check` exits 0.

## Assumption Drift (advisory)

- **Found during:** Task 3.
- **Planned:** "Research says this is the only Wave-1 lever that moves the per-run FP rate
  (16/18 → 12/18 predicted)."
- **Actual:** B-REWEIGHT moves the rate to 14/18 on its own. The drop comes from should-quiet-3
  and should-quiet-5, not should-quiet-2.
- **Why:** the derivation over the committed manifest gives impact −12, not the indicative −18,
  and adds bugs −2. A smaller impact offset does not quiet should-quiet-2's surviving rows.

## Threat model

- **T-41-20** (hand-edited literal): mitigated by TestEmbeddedEqualsDerived and `--check`. The
  mutation was demonstrated.
- **T-41-22** (malformed agent): mitigated by `_agent_offset` coerce-or-default and the crash rows.
- **T-41-23** (import set): 4 imports, and TestImportSet is unchanged.
- **T-41-24** (retune after the gate): no retune. The ordering test covers both reports.

No new threat surface.

## Self-Check: PASSED

- FOUND: docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-reweight.md
- FOUND: plugins/vibe-check/scripts/score.py (AGENT_CONFIDENCE_OFFSET)
- FOUND: commit 0ee3818
