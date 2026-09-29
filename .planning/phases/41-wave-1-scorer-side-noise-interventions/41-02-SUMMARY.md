---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 02
status: complete
subsystem: efficacy-evidence
tags: [b3, replay, guardrail, scorer-01, d-05]
requires: ["41-01 REPLAY-CATCH-MANIFEST-v2.10.json", "SUPERSESSIONS-v2.10.md entry 007"]
provides:
  - "plugins/vibe-check/scripts/replay.py: offline replay harness + zero-catch-regression guardrail (check-manifest / baseline / candidate)"
  - "plugins/vibe-check/scripts/test_replay.py: 43 tests"
  - "docs/design/b3-ground-truth/REPLAY-REPORT-phase41-baseline.md: baseline fidelity + protected-catch report"
  - "SUPERSESSIONS-v2.10.md entry 008 + manifest guardrail_amendments (owner amendment of one v2.9 catch)"
affects: [41-03..41-08 (every candidate replay is gated by this harness)]
tech-stack:
  added: []
  patterns: ["scorer loaded from a git blob via importlib spec_from_file_location", "fail-closed UNEVALUABLE status for unreproducible protected catches", "owner amendments only via an append-only ledger entry the manifest must reference"]
key-files:
  created:
    - plugins/vibe-check/scripts/replay.py
    - plugins/vibe-check/scripts/test_replay.py
    - docs/design/b3-ground-truth/REPLAY-REPORT-phase41-baseline.md
  modified:
    - docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md
    - docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json
decisions:
  - "Owner amended runs/triggarr-secret-in-logs/run-2 (ledger 008): v2.9 archive cannot reproduce the catch; it stays in the 26 as AMENDED; baseline = REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1; ledger 007 NOT extended to filtered[]"
  - "Fidelity is pinned on (band, score, stable_hash): 56/66 exact (research's 57 was on (band, score); the extra drift run is runs/should-quiet-3/run-2, stable_hash only)"
  - "Channel A reads <result> bodies from user AND queue-operation records; channel C decodes JSON objects at line starts"
metrics:
  duration: "~40 min (first executor) + ~25 min (continuation)"
  completed: 2026-09-29
  tasks: "3/3"
  files: 5
---

# Phase 41 Plan 02: SCORER-01 replay harness and zero-catch-regression guardrail — Summary

The offline replay harness replays all 66 archived runs through the baseline scorer blob
(`b21f7f3d556e1522e9853511ed8e126057c417c0`) or a candidate, and gates a candidate on the 26
protected catch runs. It fails closed on any regression or unreproducible catch. The baseline reads
**REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1** and exits 0. The one AMENDED run is the v2.9
`runs/triggarr-secret-in-logs/run-2`, amended by owner decision in ledger entry 008.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | `1d9cb24` | archive walk, envelope rebuild, blob/rev/path scorer loading, baseline fidelity |
| (blocker) | `e95c8f3`, `09b0f40` | blocked SUMMARY + STATE blocker (superseded by this summary) |
| owner amendment | `3674240` | SUPERSESSIONS-v2.10.md entry 008 |
| owner amendment | `57b912c` | manifest `guardrail_amendments` for run-2 -> ledger `008` |
| 2 + 3 | `da86399` | replay.py guardrail + CLI, test_replay.py, baseline report |

## What was built

- **Task 1:** archive walk (66 scoreable runs, 3 `.failed-*` excluded), envelope reconstruction,
  scorer loading from blob/rev/path (path confined to `plugins/vibe-check/scripts`), fidelity.
- **Task 2:** `load_manifest` / `check_manifest` (29/26/21 · 18/6/9 · 3 counts, survivor
  resolution and completeness, amendment ledger validation), `catch_status` (SITE + BAND >= floor
  + AXIS on the row's own title or any `members[].title`, ledger 007), `protected_status` (asserts
  exactly 26), `guardrail`, `fp_prediction`, the report writer (never receives titles), and the
  `check-manifest` / `baseline` / `candidate` commands.
- **Task 3:** `test_replay.py`, 43 tests, 0 skips.
- **Baseline report:** the protected-catch section leads, then the fidelity summary
  (**56/66 exact**), 10 drift runs, a transcript-coverage disclosure, and the per-run table.

## Verification (observed, this session)

- `replay.py check-manifest`: exit 0.
- `replay.py baseline --out docs/design/b3-ground-truth/REPLAY-REPORT-phase41-baseline.md`: exit 0.
  First section `Protected catches — 26`; totals `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`;
  run-2 row `AMENDED | axis-false | 008`; `**56/66 exact**`; transcript coverage `12 / 66` runs
  with a transcript, `10 / 12` recover every surviving agent, the 2 gaps are
  `runs-v2.10-phase40/batch1|batch2/triggarr-secret-in-logs/run-1 — codex-adversarial`.
- Baseline vs itself (`candidate --scorer blob:b21f7f3…`): exit 0. `kept 25 / protected 26`,
  `REGRESSED 0`, `UNEVALUABLE 0`, `AMENDED 1`. Headline FP `**16/18**` -> `**16/18**`, Phase-40
  sq5 `**0/6**` -> `**0/6**`.
- Mutation proof 1 (`THRESHOLDS` 101): exit 1, `REGRESSED 25` (every REPRODUCED run).
- Mutation proof 2 (planted `PLANTED/none.py`): covered by
  `test_mutation_planted_unreproducible_catch_fails_closed` (exit 1, UNEVALUABLE +1,
  basis `no-row-at-site`).
- Amendment locks: `test_dropping_a_real_amendment_fails_closed` (removing the real amendment ->
  run-2 UNEVALUABLE, candidate exit 1); `test_real_amendments_are_amended_with_their_ledger_entry`;
  `test_amendment_pin_matches_manifest` (manifest amendments == `{run-2: "008"}`, 008 is a ledger
  heading).
- Report-order lock mutation: putting the protected section back after the fidelity summary
  turned `test_baseline_report` red (1 failed, 42 passed). Restored: 43 passed.
- `pytest -q test_replay.py`: **43 passed**. Full suite from `plugins/vibe-check/scripts`:
  **1033 passed**, 1146 subtests passed.
- Sealed roots (`runs`, `runs-v2.10`, `runs-v2.10-phase40`, PREREGISTRATION-v2.10, SCORING-b3,
  SCORING-v2.10): `git diff --quiet HEAD` -> `SEALED-UNCHANGED`. `runs-v2.10` tree is
  `82c412b6e58b5d5a1dbddca0239f0f4b26833b4a` (the ledger-005 integrity value).

Pinned values in test_replay.py:
- `EXPECTED_EXACT_BASELINE = 56`
- `EXPECTED_DRIFT_RUNS` (10): runs-v2.10 should-quiet-1/run-2, should-quiet-7/run-1..3,
  triggarr-settings-form-split/run-2; runs should-quiet-1/run-2..3, should-quiet-3/run-2,
  triggarr-secret-in-logs/run-1..2
- `EXPECTED_AMENDED = 1`, `EXPECTED_AMENDMENTS = {"runs/triggarr-secret-in-logs/run-2": "008"}`
- `CODEX_WRITE_ONLY_RUNS` (2): Phase-40 batch1 and batch2 secret-in-logs run-1
- the protected count is `replay.EXPECTED_PROTECTED` (26); no smaller "gateable" number exists

## Deviations from Plan

1. **[Owner amendment, D-05 stop rule] One protected catch is AMENDED, not REPRODUCED.**
   - Found during: Task 2 (first executor), which stopped at the stop rule.
   - Issue: `runs/triggarr-secret-in-logs/run-2` (v2.9) replays `axis-false`. The archive holds
     `state.json` only, with two rows at L232. The baseline scorer bridges the codex catch into the
     co-located compliance row, whose title is axis=false, and absorbs codex into `filtered[]`. The
     original separating inputs were never archived.
   - Resolution: owner chose Option 1 (amend) on 2026-09-29. Ledger entry 008 was appended, and
     the manifest's `guardrail_amendments` references it. The run stays in the 26 as AMENDED, and
     ledger 007 is not extended. The plan's literal `REPRODUCED 26 / 26 · AMENDED 0` and
     `EXPECTED_AMENDED = 0` became `25 / 26 · AMENDED 1` and `EXPECTED_AMENDED = 1`.
   - Commits: `3674240`, `57b912c`.
2. **[Rule 1 - Bug] Transcript channel A missed native returns.** Notifications live in
   `queue-operation` records. They are now scanned too, and all 12 transcript runs recover every
   surviving native agent.
3. **[Rule 1 - Bug] Codex channel C needed a lenient decode.** The codex translator output follows
   a label line, so JSON objects are decoded at line starts. In 2 runs the codex object exists only
   inside an orchestrator Write payload, which is not a channel. The baseline report now names them
   (Transcript coverage section).
4. **[Rule 2] Baseline report ordering and coverage disclosure.** The protected-catch section now
   leads the baseline report, as it already did in the candidate report. A computed
   "Transcript coverage (disclosed)" section was added, and `test_baseline_report` locks both.
5. **Tests that plant an amendment merge into the real `guardrail_amendments`, not replace it.**
   Otherwise the real run-2 would silently turn UNEVALUABLE inside those tests.
6. **Mutation-proof assertions are relative** ("every REPRODUCED run REGRESSES", "UNEVALUABLE
   rises by exactly 1"), so they stay meaningful with an amendment in force.
7. **Report formatting.** The `**N/66 exact**` line carries a parenthetical after the bold.

## Assumption Drift (advisory)

- **Found during:** Task 2.
- **Planned:** all 26 protected catches reproduce under the baseline blob, because research found
  "all 26 resolved to existing survivors".
- **Actual:** resolving a catch to an archived survivor is not the same as reproducing it. One v2.9
  run's catch is absorbed by the baseline scorer's codex bridge.
- **Why:** the ambiguity-causing native inputs from v2.9 are unrecoverable. The owner amended the
  run (ledger 008).

## Known Stubs

None.

## Threat Flags

None. The harness reads the committed archives and writes one report path given on the CLI.
Scorer path loading is confined to `plugins/vibe-check/scripts` (symlink escape refused, tested).

## Self-Check: PASSED

- FOUND: replay.py, test_replay.py, REPLAY-REPORT-phase41-baseline.md
- FOUND commits: 1d9cb24, e95c8f3, 09b0f40, 3674240, 57b912c, da86399
