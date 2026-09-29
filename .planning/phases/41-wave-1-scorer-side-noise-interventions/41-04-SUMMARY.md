---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 04
status: complete
subsystem: scorer
tags: [b-sev, scorer-02, d-01, d-02, d-09, t1, replay-guardrail]
requires: ["41-02 replay.py guardrail + baseline report", "41-03 CALIBRATION-v2.10.md method record"]
provides:
  - "score.py: CODEX_AGENT, LONE_LANE_BAND_CEILING, _codex_joined, _codex_corroborated, _second_opinion, _lone_lane_cap; pre-band score cap"
  - "templates/scoring.md § 'Wave 1 (v2.10) — second-opinion rules' (Second opinion D-01, Lone-lane band ceiling B-SEV)"
  - "phases/review/30-collect-score.md: envelope `codex` block + dispatch-identity agent stamping"
  - "docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-sev.md (ALONE replay)"
  - "test_replay.py TestMethodRecordOrdering (D-15 ancestry lock)"
affects: [41-05 B-REWEIGHT, 41-06 H-LANE (reuse _second_opinion / LONE_LANE_BAND_CEILING=None override), 41-07 PLAN-COMMITS.json]
tech-stack:
  added: []
  patterns: ["cap the SCORE before the single band_for call instead of adding a band branch", "provenance from an orchestrator-set envelope block, never from agent self-report", "finalize cutoff judges the uncapped score so a label cap never drops a finding"]
key-files:
  created:
    - docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-sev.md
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/scripts/test_replay.py
    - plugins/vibe-check/templates/scoring.md
    - plugins/vibe-check/phases/review/30-collect-score.md
decisions:
  - "B-SEV caps a no-second-opinion group's score at critical floor - 1 (94 default) before band_for; band_for stays the single band writer"
  - "Second opinion = Codex-corroborated (envelope codex.status == joined AND a codex-adversarial member AND a str Claude-lane member) OR persisted (carry-forward identity set); Claude<->Claude agreement and in_diff are not second opinions"
  - "The per-command finalize cutoff judges the UNCAPPED score, so the ceiling lowers a label and never drops a finding (a config-tuned critical floor may sit below the /review cutoff)"
metrics:
  duration: "~35 min"
  completed: 2026-09-29
  tasks: "3/3"
  files: 6
---

# Phase 41 Plan 04: B-SEV lone-lane band ceiling — Summary

A finding group now needs a second opinion to reach the critical band. A second opinion is either
Codex agreeing at the same site, with the envelope's orchestrator-set `codex` block saying
`joined`, or persistence from a previous pass. Without one, the group's score is capped at the
critical floor minus 1 (94 by default), so it bands Warning, which still blocks finalize. Replayed
ALONE against the archived B3 runs: **REGRESSED 0 · UNEVALUABLE 0**, headline FP **16/18 → 16/18**.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 + 2 + 3 (one commit per D-09) | `c02d9b1` | score.py cap + helpers, scoring.md section, 30-collect-score.md envelope key, test_score.py re-pins + TestLoneLaneCeiling, B-SEV replay report, TestMethodRecordOrdering |

The plan asked for the three tasks to land as ONE commit (B-SEV replayed alone, D-09), so there
are no per-task commits. **B-SEV commit sha for 41-07's PLAN-COMMITS.json: `c02d9b1`**
(`git rev-parse c02d9b1` for the full sha).

## ALONE replay (observed, `replay.py candidate --name b-sev`, exit 0)

- Report header: `candidate scorer: path:…/score.py`, sha256
  `5ed2234ec650ca971fcb28f71ec306bfdf6edb4f3be0ee9bf05adfe1c664d843`. This equals
  `shasum -a 256 plugins/vibe-check/scripts/score.py` at commit time. `overrides: {}`, baseline
  `blob: b21f7f3d…`.
- Protected catches: `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`. The one AMENDED run is
  ledger 008, `runs/triggarr-secret-in-logs/run-2`, unchanged from the 41-02 baseline.
- Guardrail: `kept 25 / protected 26`, `REGRESSED 0`, `UNEVALUABLE 0`, `AMENDED 1`. Each of the 25
  kept catches moved from critical/100 to **warning/94**, which still clears its floor. The AMENDED
  run stays critical/100 because its Codex and compliance rows share one group and the replay
  envelope says Codex joined.
- FP prediction: headline **16/18 → 16/18**, Phase-40 sq5 **0/6 → 0/6**, v2.9 quiet (informational)
  **6/9 → 6/9**. B-SEV does not change whether a run fires; it changes only the band.
- Band shift across all firing rows (84 rows before and after): baseline 44 critical / 40 warning;
  candidate **3 critical / 81 warning**. The 3 remaining criticals are all
  `runs-v2.10/should-quiet-7/run-1..3` at `triggarr/web/routes.py:550`, the Codex-corroborated
  site. Under D-01 Codex is the independent voter, so Wave 1 is not expected to move that site.
- The plan's success criteria read `REPRODUCED 26 / 26 · kept 26 / protected 26`. After ledger 008
  (41-02) the correct figures are `25 / 26 · AMENDED 1` and `kept 25 / protected 26`. The required
  values, `REGRESSED 0` and `UNEVALUABLE 0`, both hold.

## Verification (observed)

- Task 1 smoke, run with a mapped category (see deviation 2). A lone in-diff critical/100 finding
  gives warning/94. Adding a co-located Codex finding with `codex: {"status": "joined"}` gives
  critical/100. The same pair with no block gives warning. `thresholds.critical` 90 gives 89. With
  `thresholds` 72/71/70 the finding gives warning/71 and is **not** filtered under `/review`.
- `grep -c 'band_for('` is unchanged from HEAD. `min(best_score` appears on exactly one line (1401),
  which comes before `survivor["orchestrator_score"] = best_score` (1406).
  `Do NOT retune (behavior-preserving extraction)` count = 0.
- scoring.md: lines 1-64 are byte-identical to HEAD (`diff` clean), and the new section starts at
  line 66. 15 `scoring.md:NN` citations in score.py, 11 distinct. Each one was re-checked with
  `sed -n` and still points at its rule:
  `11-29` (formula block, 11 = opening fence) · `13` +20 in_diff · `14` −50 silenced · `15` +20
  compliance · `16-17` intent-doc −30/−100 · `18` +10 cross-confirm · `19` +15 persisted ·
  `21-26` severity weight · `26` unset → −8 · `37-42` Bands table · `57-64` filter thresholds.
- 30-collect-score.md: 3+ `"status": "joined|skipped|off"` hits; `DISPATCH identity` appears once.
- `pytest test_score.py -q`: **270 passed** (257 before this plan + 13 new). `GOLDEN_DIGEST` line
  unchanged. `git diff -U0` shows no hunk inside TestImportSet, TestStableHashGolden,
  TestStableHashSeparatorCollision, TestBandBoundaries, TestSingleWriterLock or TestOutputShape.
  12 added lines carry the `v2.10 Wave 1 B-SEV (D-02)` reason.
- Mutation proofs on TestLoneLaneCeiling. Each mutation was applied, run, and then reverted
  (`cmp` confirmed the restore):
  - `_codex_joined` always True: 5 failed
  - cutoff judged on the capped score: 1 failed
  - persisted ignored: 1 failed
  - no Claude lane required: 5 failed
  - cap at the floor instead of floor − 1: 16 failed
- TestMethodRecordOrdering failed before the commit (report present but uncommitted, which gives a
  vacuous check) and passed after it. `git merge-base --is-ancestor <CALIBRATION first>
  <b-sev report first>` exits 0.
- Full suite `pytest plugins/vibe-check/scripts -q`: **1073 passed**, 1160 subtests, 0 failed.
- Sealed roots (`runs`, `runs-v2.10`, `runs-v2.10-phase40`, PREREGISTRATION-v2.10): `git diff
  --quiet HEAD` confirmed unchanged.
- Exactly one commit touches score.py since plan start (`c02d9b1`).
- The plan's Task-3 `<verify>` chain prints nothing on macOS: `wc -l` pads its output with spaces,
  so `grep -qx 1` fails. Each part was run on its own and passed: the report has 1 commit, the
  Ordering test gives 1 passed, and the suite shows 0 failed.

## Re-pinned expectations (all lone-lane, reason comment on each)

- TestRunEndToEnd survivor → 94/warning.
- TestRunThresholds: override → 79/warning (the tuned floor minus 1, which also proves the key
  reaches run()); two-layer → 71/warning under deep-review, still sub-threshold under `/review`.
- TestRunMinConfidence: the dropped-neighbour Claude↔Claude +10 → 94, which still differs from 85;
  zero-config → 94/warning.
- TestIdiomFloor: off/none/non-idiom → warning, still above the medium cap; byte-stable default →
  warning/94.
- TestIdiomFloorEnvelopeIntegration: explicit off → warning; absent vs off stays distinct (medium vs
  warning).
- The two Codex-bridge tests in TestCrossConfirmGroup now include `codex: {"status": "joined"}`
  because their purpose is the Codex path. They still assert 95.
- TestMalformedResidualCrashSurfaces string-range: confidence 100 → 80, so the no-`in_diff` proof is
  not hidden by the cap (a wrong +20 would read 94; the correct score reads 80).

## Deviations from Plan

1. **[Rule 1 - Bug] The cap would have silently dropped findings under a low tuned critical floor.**
   - Found during: Task 1.
   - Issue: config.py accepts floors like `{critical:72, warning:71, medium:70}`. The cap (71) sits
     below the `/review` cutoff (80), and the threshold loop filtered on `best_score`. A capped
     finding was therefore dropped as `sub-threshold`, which breaks D-02 ("may reach Warning").
   - Fix: the threshold loop now judges `surface_score`, the uncapped score. Locked by
     `test_cap_never_drops_a_finding_under_a_low_tuned_floor` (mutation: 1 failed). Documented in
     scoring.md.
   - Commit: `c02d9b1`.
2. **[Plan inaccuracy] The verify smoke used `category: "bug"`, which is not in `CATEGORY_DOMAIN`.**
   A Codex finding bridges only into a mapped single-domain component, so the plan's
   "codex + Claude → critical" assertion could never pass as written. The smoke and the tests use
   `null-access` (correctness domain). The code was not changed for this.
3. **[CLAUDE/executor rule — no plan ids in product code] The header docstring does not name
   "41-05"/"41-06" or "(this commit)".** It lists only the change that exists, the B-SEV lone-lane
   ceiling, and points at the scoring.md section. Later Wave-1 plans extend that list when their
   changes land.
4. **[Rule 2] Two extra locks beyond the plan's list:** the agent-written `status: "persisted"`
   cannot lift the cap (Fable A5 surface), and Claude↔Claude agreement is not a second opinion.
   TestLoneLaneCeiling has 13 methods.

## Assumption Drift (advisory)

- Found during Task 3. Planned: the replay would have to discover Codex provenance. Actual:
  replay.py (41-02) already rebuilds the envelope with
  `codex: {"status": "joined" if any survivor agent == codex-adversarial else "skipped"}`. Why it
  matters: archived runs carry no orchestrator block, so replay infers "joined" from the survivors.
  That is sound for the archives, which contain only real Codex output, but it is an inference, not
  the live orchestrator's value.
- Found during Task 3. Planned: `REPRODUCED 26 / 26`. Actual: `25 / 26 · AMENDED 1` (ledger 008,
  41-02). Why: that amendment was already in force before this plan.

## Deferred Items

- `phases/deep-review/30-codex-collect.md` still says "No Codex special-casing anywhere downstream"
  (header and item 4). That is now slightly stale: the orchestrator must also inject the envelope
  `codex` block, which 30-collect-score.md, read at the same Phase-3 entry, now documents. The file
  was outside this plan's list; flagged for 41-06, which rewrites the cross-confirm prose.

## Threat model check

- T-41-15 (codex self-label spoof): `_codex_corroborated` requires `_codex_joined(envelope)`; tests
  assert that absent, skipped and off blocks all stay capped.
- T-41-16 (second band writer): the `band_for(` count is unchanged.
- T-41-17 (malformed block / agent): coerce-or-default helpers; 6 malformed `codex` shapes and 4
  non-str agents never raise and never lift the cap.
- T-41-18 (imports): no new imports; TestImportSet is green and unchanged.
- T-41-19 (evidence): the report is in the same commit; the ordering test binds it after the method
  record.

## Self-Check: PASSED

- FOUND: docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-sev.md
- FOUND: commit c02d9b1
