# Replay report — baseline fidelity

- baseline: blob: b21f7f3d556e1522e9853511ed8e126057c417c0
- scorer sha256: c8c36b9c97546d2e073c179664b972bd0975a7120fe05a34e457247735099e03
- manifest: docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json
- manifest sha256: 7f5ac51140afa57d87262b89774510e4635f06cd9d9c65beb95a867124d65339
- amendments in force: 1
- HEAD: 57b912cd9c93e7e82fb760f598d941394bf916ea
- generated (UTC): 2026-09-29T21:54:08Z

_no rounding — exact fractions_

## Protected catches — 26 (D-05) — baseline reproduction

| run | status | basis | ledger entry |
|---|---|---|---|
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1 | REPRODUCED | survivor-title | — |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-2 | REPRODUCED | survivor-title | — |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-3 | REPRODUCED | survivor-title | — |
| runs-v2.10/third-organic-should-catch/run-1 | REPRODUCED | survivor-title | — |
| runs-v2.10/third-organic-should-catch/run-2 | REPRODUCED | survivor-title | — |
| runs-v2.10/third-organic-should-catch/run-3 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-autoescape/run-1 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-autoescape/run-2 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-autoescape/run-3 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-secret-in-logs/run-1 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-secret-in-logs/run-2 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-secret-in-logs/run-3 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-session-rotation/run-1 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-session-rotation/run-2 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-session-rotation/run-3 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-settings-form-split/run-1 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-settings-form-split/run-2 | REPRODUCED | survivor-title | — |
| runs-v2.10/triggarr-settings-form-split/run-3 | REPRODUCED | survivor-title | — |
| runs/third-organic-should-catch/run-1 | REPRODUCED | survivor-title | — |
| runs/third-organic-should-catch/run-2 | REPRODUCED | survivor-title | — |
| runs/third-organic-should-catch/run-3 | REPRODUCED | survivor-title | — |
| runs/triggarr-autoescape/run-2 | REPRODUCED | survivor-title | — |
| runs/triggarr-autoescape/run-3 | REPRODUCED | survivor-title | — |
| runs/triggarr-secret-in-logs/run-1 | REPRODUCED | survivor-title | — |
| runs/triggarr-secret-in-logs/run-2 | AMENDED | axis-false | 008 |
| runs/triggarr-secret-in-logs/run-3 | REPRODUCED | survivor-title | — |

REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1

## Fidelity summary

**56/66 exact** (the replay's (band, score, stable_hash) multiset equals the archive's)

## Drift runs

- runs-v2.10/should-quiet-1/run-2 — archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved
- runs-v2.10/should-quiet-7/run-1 — archived-only 1 · replay-only 0 · band-moved 0 · rows-differing 1 · cause: archived row not re-emitted
- runs-v2.10/should-quiet-7/run-2 — archived-only 1 · replay-only 0 · band-moved 0 · rows-differing 1 · cause: archived row not re-emitted
- runs-v2.10/should-quiet-7/run-3 — archived-only 1 · replay-only 0 · band-moved 0 · rows-differing 1 · cause: archived row not re-emitted
- runs-v2.10/triggarr-settings-form-split/run-2 — archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved
- runs/should-quiet-1/run-2 — archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved
- runs/should-quiet-1/run-3 — archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved
- runs/should-quiet-3/run-2 — archived-only 1 · replay-only 1 · band-moved 0 · rows-differing 1 · cause: stable_hash only (band and score multisets agree)
- runs/triggarr-secret-in-logs/run-1 — archived-only 0 · replay-only 0 · band-moved 2 · rows-differing 2 · cause: score/band moved
- runs/triggarr-secret-in-logs/run-2 — archived-only 1 · replay-only 0 · band-moved 1 · rows-differing 2 · cause: score/band moved

## Transcript coverage (disclosed)

12 / 66 runs carry a session transcript (Phase-40 archives). The other 54 runs are replayed from their state.json survivors only: findings the original scorer dropped were never archived for them.

10 / 12 transcript runs recover a return for every surviving agent.

Surviving agents with no return on any recovery channel. The survivor itself is exact from state.json, but none of that agent's non-surviving findings can be recovered. In the archived runs this happens when the agent's output reached the orchestrator only inside a file the orchestrator wrote, which is not a recovery channel:

- runs-v2.10-phase40/batch1/triggarr-secret-in-logs/run-1 — codex-adversarial
- runs-v2.10-phase40/batch2/triggarr-secret-in-logs/run-1 — codex-adversarial

## Fidelity per run

| run | exact | recovered | detail |
|---|---|---|---|
| runs-v2.10-phase40/batch1/should-quiet-5/run-1 | yes | recovered: 2 | exact |
| runs-v2.10-phase40/batch1/triggarr-secret-in-logs/run-1 | yes | recovered: 3 | exact |
| runs-v2.10-phase40/batch2/should-quiet-5/run-1 | yes | recovered: 3 | exact |
| runs-v2.10-phase40/batch2/triggarr-secret-in-logs/run-1 | yes | recovered: 3 | exact |
| runs-v2.10-phase40/batch3/should-quiet-5/run-1 | yes | recovered: 2 | exact |
| runs-v2.10-phase40/batch3/triggarr-secret-in-logs/run-1 | yes | recovered: 2 | exact |
| runs-v2.10-phase40/final/should-quiet-5/run-1 | yes | recovered: 2 | exact |
| runs-v2.10-phase40/final/should-quiet-5/run-2 | yes | recovered: 1 | exact |
| runs-v2.10-phase40/final/should-quiet-5/run-3 | yes | recovered: 2 | exact |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1 | yes | recovered: 2 | exact |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-2 | yes | recovered: 3 | exact |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-3 | yes | recovered: 1 | exact |
| runs-v2.10/should-quiet-1/run-1 | yes | — | exact |
| runs-v2.10/should-quiet-1/run-2 | no | — | archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved |
| runs-v2.10/should-quiet-1/run-3 | yes | — | exact |
| runs-v2.10/should-quiet-2/run-1 | yes | — | exact |
| runs-v2.10/should-quiet-2/run-2 | yes | — | exact |
| runs-v2.10/should-quiet-2/run-3 | yes | — | exact |
| runs-v2.10/should-quiet-3/run-1 | yes | — | exact |
| runs-v2.10/should-quiet-3/run-2 | yes | — | exact |
| runs-v2.10/should-quiet-3/run-3 | yes | — | exact |
| runs-v2.10/should-quiet-4/run-1 | yes | — | exact |
| runs-v2.10/should-quiet-4/run-2 | yes | — | exact |
| runs-v2.10/should-quiet-4/run-3 | yes | — | exact |
| runs-v2.10/should-quiet-5/run-1 | yes | — | exact |
| runs-v2.10/should-quiet-5/run-2 | yes | — | exact |
| runs-v2.10/should-quiet-5/run-3 | yes | — | exact |
| runs-v2.10/should-quiet-6/run-1 | yes | — | exact |
| runs-v2.10/should-quiet-6/run-2 | yes | — | exact |
| runs-v2.10/should-quiet-6/run-3 | yes | — | exact |
| runs-v2.10/should-quiet-7/run-1 | no | — | archived-only 1 · replay-only 0 · band-moved 0 · rows-differing 1 · cause: archived row not re-emitted |
| runs-v2.10/should-quiet-7/run-2 | no | — | archived-only 1 · replay-only 0 · band-moved 0 · rows-differing 1 · cause: archived row not re-emitted |
| runs-v2.10/should-quiet-7/run-3 | no | — | archived-only 1 · replay-only 0 · band-moved 0 · rows-differing 1 · cause: archived row not re-emitted |
| runs-v2.10/third-organic-should-catch/run-1 | yes | — | exact |
| runs-v2.10/third-organic-should-catch/run-2 | yes | — | exact |
| runs-v2.10/third-organic-should-catch/run-3 | yes | — | exact |
| runs-v2.10/triggarr-autoescape/run-1 | yes | — | exact |
| runs-v2.10/triggarr-autoescape/run-2 | yes | — | exact |
| runs-v2.10/triggarr-autoescape/run-3 | yes | — | exact |
| runs-v2.10/triggarr-secret-in-logs/run-1 | yes | — | exact |
| runs-v2.10/triggarr-secret-in-logs/run-2 | yes | — | exact |
| runs-v2.10/triggarr-secret-in-logs/run-3 | yes | — | exact |
| runs-v2.10/triggarr-session-rotation/run-1 | yes | — | exact |
| runs-v2.10/triggarr-session-rotation/run-2 | yes | — | exact |
| runs-v2.10/triggarr-session-rotation/run-3 | yes | — | exact |
| runs-v2.10/triggarr-settings-form-split/run-1 | yes | — | exact |
| runs-v2.10/triggarr-settings-form-split/run-2 | no | — | archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved |
| runs-v2.10/triggarr-settings-form-split/run-3 | yes | — | exact |
| runs/should-quiet-1/run-1 | yes | — | exact |
| runs/should-quiet-1/run-2 | no | — | archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved |
| runs/should-quiet-1/run-3 | no | — | archived-only 0 · replay-only 0 · band-moved 1 · rows-differing 1 · cause: score/band moved |
| runs/should-quiet-2/run-1 | yes | — | exact |
| runs/should-quiet-2/run-2 | yes | — | exact |
| runs/should-quiet-2/run-3 | yes | — | exact |
| runs/should-quiet-3/run-1 | yes | — | exact |
| runs/should-quiet-3/run-2 | no | — | archived-only 1 · replay-only 1 · band-moved 0 · rows-differing 1 · cause: stable_hash only (band and score multisets agree) |
| runs/should-quiet-3/run-3 | yes | — | exact |
| runs/third-organic-should-catch/run-1 | yes | — | exact |
| runs/third-organic-should-catch/run-2 | yes | — | exact |
| runs/third-organic-should-catch/run-3 | yes | — | exact |
| runs/triggarr-autoescape/run-1 | yes | — | exact |
| runs/triggarr-autoescape/run-2 | yes | — | exact |
| runs/triggarr-autoescape/run-3 | yes | — | exact |
| runs/triggarr-secret-in-logs/run-1 | no | — | archived-only 0 · replay-only 0 · band-moved 2 · rows-differing 2 · cause: score/band moved |
| runs/triggarr-secret-in-logs/run-2 | no | — | archived-only 1 · replay-only 0 · band-moved 1 · rows-differing 2 · cause: score/band moved |
| runs/triggarr-secret-in-logs/run-3 | yes | — | exact |
