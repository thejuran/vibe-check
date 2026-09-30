---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 08
status: complete
subsystem: measurement-adjudication
tags: [scorer-05, d-11, d-12, d-13, spot-check, state-shape, ledger-009]
requires: ["41-07 runbook + snapshot batch4-cd8f5b00de73", "owner final runs (6) + pending PASS.json a0c8e44"]
provides:
  - "final/PASS.json adjudicated: observed 3/6 FP runs vs predicted 5 -> PASS (D-11)"
  - "SUPERSESSIONS-v2.10.md entry 009 (state_shape waiver for five runs)"
  - "45-persist.md states the full future-schema root for a new state file (+ prose-lock test)"
  - "RESULTS-v2.10.md Phase-41 section"
affects: [Phase 42 (Wave 2 prompts), Phase 43 (runbook: model pin, context headroom, new snapshot after the persist fix)]
tech-stack:
  added: []
  patterns: ["prose-lock test parses a fenced JSON block out of phase prose and checks it against the schema fixture"]
key-files:
  created: []
  modified:
    - docs/design/b3-ground-truth/runs-v2.10-phase41/final/PASS.json
    - docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md
    - plugins/vibe-check/phases/review/45-persist.md
    - plugins/vibe-check/scripts/test_state_shape.py
    - plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md
    - .planning/REQUIREMENTS.md
    - .planning/phases/41-wave-1-scorer-side-noise-interventions/41-deferred-items.md
decisions:
  - "Phase-41 spot-check: observed 3/6 FP runs vs predicted 5 -> PASS (D-11); D-12 not used"
  - "Five state_shape FAILs (missing root medium_acknowledgments) counted under ledger 009 (owner decision 2026-09-29); values kept FAIL; check-pass exits 1 by design for this artifact only"
  - "medium_acknowledgments is a JSON object keyed by stable_hash; a new state file starts it as {}"
metrics:
  started: 2026-09-29T23:07:17Z
  completed: 2026-09-29
  tasks: "3/3"
---

# Phase 41 Plan 08: Spot-check adjudication + RESULTS append — Summary

**The live spot-check passed at 3/6 firing runs against a prediction of 5 (D-11). Five runs record a
`state_shape` FAIL for one reason, a missing root `medium_acknowledgments`. By owner decision they
count under ledger entry 009. The underlying persist-prose bug is fixed, with a lock test that was
mutation-tested.**

## Task 0 — barrier (re-run by the continuation agent, observed)

- 6 `state.json`, 6 `tree.diff`, 6 `transcript.jsonl` under `final/should-quiet-{1,3}/run-{1,2,3}`
- `final/PASS.json` present, all `pending-assistant`, mechanical verdict FAIL
- 2 `## Harness fingerprint — ` blocks (19:07:17 and 19:38:59 -0400). Both show Claude Code 2.1.281,
  Fable 5.1, codex-cli 0.153.4 and batch-sha `cd8f5b00`.
- Nothing uncommitted under `runs-v2.10-phase41`. The sealed roots (`runs`, `runs-v2.10`,
  `runs-v2.10-phase40`, `PREREGISTRATION-v2.10.md`) are unchanged.
- The only barrier failure is `state_shape`. `state_shape.py --schema future --all` reports exactly
  `missing required root key: medium_acknowledgments` on five runs. sq3 run-3 is clean. The owner
  waived this, so there was no other failure and no STOP.

## Task 1 — adjudication (observed)

| diff | run | bands of passes[-1].findings | adjudication | codex (pass-level) | state_shape |
|---|---|---|---|---|---|
| should-quiet-3 | 1 | impact medium 73 | clean | joined / approve | FAIL (waived, 009) |
| should-quiet-3 | 2 | bugs medium 70 | clean | skipped / unavailable | FAIL (waived, 009) |
| should-quiet-3 | 3 | language-python medium 77 | clean | skipped / unavailable | PASS |
| should-quiet-1 | 1 | bugs critical 100, security warning 88 | fp | joined / needs-attention | FAIL (waived, 009) |
| should-quiet-1 | 2 | impact critical 100 | fp | joined / needs-attention | FAIL (waived, 009) |
| should-quiet-1 | 3 | bugs warning 94, security warning 89 | fp | joined / approve | FAIL (waived, 009) |

The assistant pre-tally was verified: sq3 {medium:1} ×3 is clean, and sq1 {critical:1,warning:1},
{critical:1} and {warning:2} are fp. **Observed 3 ≤ predicted 5** (runbook line 128:
`Predicted FP count for the 6 runs = 2 + 3 = 5`), so the verdict is **PASS**. Every row carries
`members`. Both criticals include a codex-adversarial member while Codex joined.

`PASS.json` gained per-run `notes`, plus `adjudicated_by`, `adjudicated_at`, `observed_fp_runs`,
`predicted_fp_runs` and `state_shape_waiver`. `check_pass_artifact` does not reject extra keys.

`batchsnap.py check-pass` output (exit 1, by design per ledger 009):

```
state_shape recorded a failure: FAIL (run 0)
state_shape recorded a failure: FAIL (run 1)
state_shape recorded a failure: FAIL (run 3)
state_shape recorded a failure: FAIL (run 4)
state_shape recorded a failure: FAIL (run 5)
```

Those five lines are the only reasons. The rest of the plan's verify ran and passed:
`ADJUDICATION CONSISTENT 3 /6 fp; verdict PASS` and `SEALED-UNCHANGED`.

## Task 2 — RESULTS append (observed)

The Phase-41 H1 was appended to `RESULTS-v2.10.md` with the seven H2s: 211 insertions and 0
deletions. SCORER-01 and SCORER-05 were flipped (02–04 were already `[x]`), and all five
traceability rows read Complete. The deferred items gained `## From 41-08`. The verify chain
printed `RESULTS-APPENDED` and the sealed roots are unchanged.

## Commits

| hash | subject |
|---|---|
| 19bc2fe | docs(41-08): SUPERSESSIONS-v2.10 entry 009 — waive five state_shape FAILs … |
| 14efe7b | docs(41-08): Phase-41 spot-check adjudicated — observed 3/6 FP runs vs predicted 5 → PASS (D-11) |
| 180e0e3 | fix(41-08): persist prose creates the full future-schema root on a new state file |
| 7626369 | docs(41-08): RESULTS-v2.10.md Phase-41 section — … spot-check 3/6 vs 5 …; SCORER-01..05 complete |

The owner-run commits from Task 0 are e7ef25c, 6bffb79, e860a80, 37f794a, 89fdf39, b532f5e,
8d83002, 815b49e and a0c8e44.

## Deviations from Plan

**1. [Owner decision, ledger 009] `check-pass` exit 0 superseded.** The plan's Task 1 verify expects
`check-pass` to exit 0. Five runs truthfully record `state_shape: FAIL`, so it exits 1, and its only
reasons are those five. The owner chose "Count them + fix the bug" on 2026-09-29. `check-pass` and
`batch-manifest-schema.json` were not modified, and no `state_shape` value was rewritten.

**2. [Rule 1 - Bug, owner-directed] Persist prose never created the root `medium_acknowledgments`.**
- **Found during:** Task 0 (the five shape FAILs)
- **Issue:** `45-persist.md` said only "Append to `state.passes`, write to state file". The key
  `future-schema.json` `root_required` demands was therefore present only by model luck. This gap
  predates Wave 1 (the batch-3 snapshot prose had it too).
- **Fix:** A new state file now starts as `{"medium_acknowledgments": {}, "passes": []}`. Existing
  files keep their root keys, and an older file that lacks the key gains `{}`. The type is an
  object, because Finalize writes `medium_acknowledgments[stable_hash] = {...}` (90-finalize.md:39)
  and every Phase-40 state has `{}`. The `[]` in test_state_shape.py is only a key-presence
  placeholder, and state_shape does not type-check root values.
- **Lock:** `test_state_shape.py::TestPersistProseCreatesFutureRoot` (4 tests) parses the fenced
  JSON after `**New state file.**` and asserts that its keys equal `root_required`, that
  `medium_acknowledgments == {}`, that the root plus a pass passes `--schema future`, and that the
  existing-file sentences are present.
- **Mutation test (observed):** reverting the prose to HEAD failed 4/4. Dropping the key from the
  block failed 3/4. Changing it to `[]` failed 1/4 (the type test). Restoring passed 4/4.
- **Suite:** `pytest -q` gave 1124 passed, 1123 subtests passed.
- **Commit:** 180e0e3. The immutable snapshot `~/.vibe-check-snapshots/batch4-cd8f5b00de73` was
  not touched.

**3. [Fact correction] Codex skipped in 2 runs, not 1.** The owner's hand-off said Codex skipped only
in sq3 run-2. PASS.json and the state files both show sq3 run-2 AND run-3 as `skipped/unavailable`,
and commit 37f794a's subject also says "codex skipped". What is recorded is 4 joined and 2 skipped.

## Assumption Drift (advisory)

- **Found during:** Task 1
- **Planned:** should-quiet-3 fires 2/3 (runs 2 and 3), for a total of 5/6.
- **Actual:** should-quiet-3 fired 0/3, for a total of 3/6.
- **Why:** the live runs used post-diet prose plus Wave 1, while the prediction replayed pre-diet
  Phase-38 runs (Pitfall 5). The two disagreeing runs are also the two with Codex skipped, but sq3
  is not a Codex-driven diff and run-1 went quiet with Codex joined. This is disclosed in RESULTS
  and not credited to the scorer alone.

## Run-environment facts recorded (from the owner hand-off)

- Each session ran near 96–100% of the 200k context window.
- The sessions were launched with `--model claude-fable-5-1` added to the runbook launch line (the
  pin is Fable 5 and the owner's default had changed).
- sq3 run-3's first attempt was voided before any review ran (Fable credits exhausted) and redone.
  Its empty auto-memory evidence dir was renamed `roonseek-written-before-sq3-run-3-voided-attempt`.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: final/PASS.json (verdict PASS, 6 adjudicated), SUPERSESSIONS entry 009, 45-persist.md
  block, TestPersistProseCreatesFutureRoot, RESULTS Phase-41 H1
- FOUND commits: 19bc2fe, 14efe7b, 180e0e3, 7626369
