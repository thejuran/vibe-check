---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 02
status: blocked
subsystem: efficacy-evidence
tags: [b3, replay, guardrail, scorer-01, d-05]
requires: ["41-01 REPLAY-CATCH-MANIFEST-v2.10.json", "SUPERSESSIONS-v2.10.md entry 007"]
provides:
  - "plugins/vibe-check/scripts/replay.py: harness complete (Task 1 committed; Tasks 2-3 code in the working tree, NOT committed per the stop rule)"
  - "plugins/vibe-check/scripts/test_replay.py: 40 tests, uncommitted; 39 pass, and the D-05 test is red on purpose"
affects: [41-03..41-08 (all candidate replays are gated on this block)]
tech-stack:
  added: []
  patterns: ["scorer loaded from a git blob via importlib spec_from_file_location", "fail-closed UNEVALUABLE status for unreproducible protected catches"]
key-files:
  created:
    - plugins/vibe-check/scripts/replay.py
    - plugins/vibe-check/scripts/test_replay.py
  modified: []
decisions:
  - "Fidelity is pinned on (band, score, stable_hash): 56/66 exact. Research's 57 was measured on (band, score); the extra drift run is runs/should-quiet-3/run-2, where one codex row's stable_hash differs and band and score agree"
  - "Channel A reads <result> bodies from user AND queue-operation records. User-only misses natives in 3 runs"
  - "Channel C decodes JSON objects at line starts, because codex output follows a label line (CODEX_TRANSLATED / === translate ===)"
metrics:
  duration: "~40 min"
  completed: 2026-09-29
  tasks: "1/3 committed; 2 and 3 built and verified, not committed (BLOCKED)"
  files: 2
---

# Phase 41 Plan 02: SCORER-01 replay harness — BLOCKED on one protected catch (D-05)

The harness is built and the guardrail works. Both mutation proofs turn it red. But the REAL
manifest reaches only **REPRODUCED 25 / 26 · UNEVALUABLE 1 · AMENDED 0** under the baseline blob.
The plan's stop rule applies. I did not commit Tasks 2-3 or the baseline report, and I wrote no
`guardrail_amendments` entry. This needs an owner decision.

## BLOCKER — the UNEVALUABLE protected catch

| run | basis |
|---|---|
| `runs/triggarr-secret-in-logs/run-2` | `axis-false` |

What happens (agent/line/band only):
- **Archive (v2.9):** two separate singleton survivors at `triggarr/clients/base.py:232`.
  - compliance, warning/90, axis=false in the manifest.
  - codex-adversarial, critical/100, axis=true. This is the recorded catch.
- **Baseline replay:** the codex finding bridges into compliance's single co-located domain
  (score.py `cross_confirm_group` STEP B). Compliance gets the +10, scores 100 critical and leads
  the row. Codex is absorbed into `filtered[]` as `absorbed-into:`.
  - The surviving row has an axis=false title.
  - The baseline scorer emits no `members`, so ledger 007's member-title rule cannot apply.
- **Likely cause:** the original run had other native findings at that site. They made the bridge
  ambiguous (2+ domains, so no bridge), then fell below threshold. v2.9 archives carry no
  `filtered[]` and no transcript, so those inputs cannot be recovered. This is the D-07 fidelity
  limit, not a harness defect.

**Repair attempted:** none is possible inside the disclosed method. Every fix would need one of
three things:
- a per-run patch;
- the archived `attribution` or recorded bands used as an input;
- invented inputs.

The plan forbids all three.

**Options for the owner** (orchestrator to bring as a SUPERSESSIONS-v2.10.md decision):
1. **Amend (recommended).** A new ledger entry (008) records that this catch is lost to
   reconstruction drift for v2.9-era inputs. Then add
   `guardrail_amendments: {"runs/triggarr-secret-in-logs/run-2": {"ledger_entry": "008", ...}}`
   to the manifest, and bump `EXPECTED_AMENDED` to 1 in `test_replay.py`. The run stays in the
   26 as AMENDED. The Phase-40 and Phase-38 secret-in-logs catches (9 runs) are still protected
   and REPRODUCED.
2. **Count absorbed members.** Extend ledger 007 so a baseline row's `filtered[]` `absorbed-into:`
   members count as members for the replay. The run then REPRODUCES as `member-title`. This
   changes the sealed "filtered[] is not scored" clause, so the owner must decide it.

After either decision, re-run:
`python3 plugins/vibe-check/scripts/replay.py baseline --out docs/design/b3-ground-truth/REPLAY-REPORT-phase41-baseline.md`.
It must exit 0. Then commit replay.py, test_replay.py and the report together.

## What was built

**Task 1** (commit `1d9cb24`): archive walk, envelope reconstruction, scorer loading from
blob/rev/path, fidelity, and CLI wiring.

**Task 2** (uncommitted, in the working tree):
- `load_manifest` / `check_manifest`: counts 29/26/21 · 18/6/9 · 3, resolution, completeness,
  and amendment ledger validation.
- `catch_status` (strict axis, D-14), `protected_status` (asserts exactly 26), `guardrail`,
  `fp_prediction`, `write_report`, `check-manifest`, `baseline` (with the protected section) and
  `candidate`.
- Two transcript fixes, both applied the same way to all 12 Phase-40 runs:
  - channel A now reads `queue-operation` records too;
  - channel C decodes objects at line starts.

**Task 3** (uncommitted): `test_replay.py`, 40 tests, 0 skips.

## Verification (observed)

- `census` printed:
  - `runs: 18 / runs-v2.10: 36 / runs-v2.10-phase40: 12`
  - 3 `excluded:` lines, all `.failed-*`
  - `transcripts: 12` and `scoreable: 66`
- Task 1 verify printed `ENVELOPE OK` and `T1-VERIFY-OK`. `load_scorer('path:/etc/passwd')` raised
  `ReplayError: refused: scorer path outside plugins/vibe-check/scripts`. `grep -c timeout=120` = 1
  = `grep -c 'subprocess.run('`.
- `check-manifest`: exit 0 with empty stderr. `grep -c gateable replay.py` = 0.
- Baseline vs itself (`selftest`): exit 1.
  - `REPRODUCED 25 / 26 · UNEVALUABLE 1 · AMENDED 0`, `kept 25 / protected 26`, `REGRESSED 0`,
    `UNEVALUABLE 1`.
  - Headline FP `**16/18**` → `**16/18**`; Phase-40 sq5 `**0/6**`.
  - The Protected section comes before the Guardrail section.
- Mutation proof 1 (THRESHOLDS 101): exit 1 with `REGRESSED 25`. That is every REPRODUCED run; the
  26th is the UNEVALUABLE one.
- Mutation proof 2 (planted `PLANTED/none.py` on `runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1`):
  - exit 1 with `REPRODUCED 24 / 26 · UNEVALUABLE 2`;
  - stderr names that run with `(no-row-at-site)` in the exact required line.
- `--override BROKEN` and `--override 'THRESHOLDS={bad'`: both exit 2.
- The reports contain no `"title"`, `problem` or `<result>`, and do contain
  `no rounding — exact fractions`.
- `pytest test_replay.py -q`: **1 failed, 39 passed**. The failure is
  `test_all_protected_catches_reproduced_by_baseline`, which names
  `{'runs/triggarr-secret-in-logs/run-2': 'axis-false'}`. This red test is the intended signal.
- Full suite: **1 failed, 1029 passed** (990 prior + 40 new). The only failure is the one above.
- Lock mutation: making `catch_status` always pass turned 8 tests red (5 catch_status units and
  3 guardrail proofs). Restored afterwards.
- Sealed archives + PREREGISTRATION: `git diff --quiet HEAD` printed `SEALED-UNCHANGED`.

The plan's literal verify strings `REPRODUCED 26 / 26`, `REGRESSED 26` and `UNEVALUABLE 1` did NOT
pass. The cause is the blocker above and nothing else. The mutation-proof tests are written
relative to the baseline's own reproduction count, so they stay meaningful after an amendment.

Pinned values in test_replay.py:
- `EXPECTED_EXACT_BASELINE = 56`. Research said 57. That figure was on (band, score); the pin
  includes stable_hash.
- `EXPECTED_DRIFT_RUNS`, 10 runs:
  - runs-v2.10: should-quiet-1/run-2, should-quiet-7/run-1..3, triggarr-settings-form-split/run-2
  - runs: should-quiet-1/run-2..3, should-quiet-3/run-2, triggarr-secret-in-logs/run-1..2
- `EXPECTED_AMENDED = 0`.

Import set: {argparse, hashlib, importlib, json, os, re, shutil, subprocess, sys, tempfile, time}.

`"title"` occurrences in replay.py:
- 337 and 536: match/dedup keys.
- 647, 651 and 655: axis matching.
- 755: the writer's refusal assert.

None of them is on a write or print path. `guardrail` spans lines 686-702 and never reads archived
bands.

## Deviations from Plan

1. **[Rule 1 - Bug] Transcript channel A missed native returns.** Notifications live in
   `queue-operation` records; the `user` copy exists only sometimes. I added `queue-operation` to
   the scanned records. All 12 runs now recover every surviving native agent.
2. **[Rule 1 - Bug] Codex channel C needed a lenient decode.** The translator output follows a
   label line. The fix decodes JSON objects at line starts. In 2 runs
   (`batch1`/`batch2` secret-in-logs) the codex object appears only inside an orchestrator Write
   payload, which is not a channel. They are pinned as `CODEX_WRITE_ONLY_RUNS`, and their codex
   survivors stay exact from state.json.
3. **Mutation-proof assertions are relative, not literal.** They assert "every REPRODUCED run
   REGRESSES" and "UNEVALUABLE rises by exactly 1", not the literal 26 / 1. That way they prove the
   mechanism independently of the blocker. The absolute D-05 requirement lives in its own test.
4. **Report formatting.** The `**N/66 exact**` line carries a parenthetical after the bold. The
   `^\*\*[0-9]+/66 exact\*\*` regex still matches.

## Assumption Drift (advisory)

- **Found during:** Task 2.
- **Planned:** all 26 protected catches reproduce under the baseline blob, because research found
  "all 26 resolved to existing survivors".
- **Actual:** resolving a catch to an archived survivor is not the same as reproducing it. In one
  v2.9 run the baseline scorer's codex bridge absorbs the catch row.
- **Why:** the ambiguity-causing native inputs from v2.9 are unrecoverable.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/replay.py (committed at 1d9cb24, and further edited in the
  working tree)
- FOUND: plugins/vibe-check/scripts/test_replay.py (untracked, by the stop rule)
- FOUND: commit 1d9cb24
- NOT CREATED (by the stop rule): docs/design/b3-ground-truth/REPLAY-REPORT-phase41-baseline.md.
  A scratch copy is at the session scratchpad `b2.md`.
