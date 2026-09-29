# Replay report — candidate b-reweight

- candidate scorer: path:/Users/julianamacbook/turingmind-code-review/plugins/vibe-check/scripts/score.py
- candidate scorer sha256: a63a62fd365bc1ec2f037c35fbec5395a61e2ba0a83c8640eecf1ebb0445c56b
- overrides: {"LONE_LANE_BAND_CEILING": null}
- baseline: blob: b21f7f3d556e1522e9853511ed8e126057c417c0
- manifest: docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json
- manifest sha256: 7f5ac51140afa57d87262b89774510e4635f06cd9d9c65beb95a867124d65339
- amendments in force: 1
- HEAD: e9ee30be7f5ac8024a5d2e293b4fe7f667aa4170
- generated (UTC): 2026-09-29T22:17:47Z

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

## Guardrail — 26 protected catch runs

| run | baseline basis | candidate band/score/basis | status |
|---|---|---|---|
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/third-organic-should-catch/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/third-organic-should-catch/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/third-organic-should-catch/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-autoescape/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-autoescape/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-autoescape/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-secret-in-logs/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-secret-in-logs/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-secret-in-logs/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-session-rotation/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-session-rotation/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-session-rotation/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-settings-form-split/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-settings-form-split/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-settings-form-split/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs/third-organic-should-catch/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs/third-organic-should-catch/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs/third-organic-should-catch/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs/triggarr-autoescape/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs/triggarr-autoescape/run-3 | survivor-title | critical/98/survivor-title | kept |
| runs/triggarr-secret-in-logs/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs/triggarr-secret-in-logs/run-2 | axis-false | critical/100/axis-false | AMENDED |
| runs/triggarr-secret-in-logs/run-3 | survivor-title | critical/100/survivor-title | kept |

kept 25 / protected 26

REGRESSED 0

UNEVALUABLE 0

AMENDED 1

## FP prediction — headline quiet set (Phase-38 should-quiet-1..6 ×3)

baseline **16/18** → candidate **14/18**

| run | baseline fires | candidate fires |
|---|---|---|
| runs-v2.10/should-quiet-1/run-1 | yes | yes |
| runs-v2.10/should-quiet-1/run-2 | yes | yes |
| runs-v2.10/should-quiet-1/run-3 | yes | yes |
| runs-v2.10/should-quiet-2/run-1 | yes | yes |
| runs-v2.10/should-quiet-2/run-2 | yes | yes |
| runs-v2.10/should-quiet-2/run-3 | yes | yes |
| runs-v2.10/should-quiet-3/run-1 | yes | no |
| runs-v2.10/should-quiet-3/run-2 | yes | yes |
| runs-v2.10/should-quiet-3/run-3 | yes | yes |
| runs-v2.10/should-quiet-4/run-1 | yes | yes |
| runs-v2.10/should-quiet-4/run-2 | yes | yes |
| runs-v2.10/should-quiet-4/run-3 | yes | yes |
| runs-v2.10/should-quiet-5/run-1 | no | no |
| runs-v2.10/should-quiet-5/run-2 | yes | no |
| runs-v2.10/should-quiet-5/run-3 | no | no |
| runs-v2.10/should-quiet-6/run-1 | yes | yes |
| runs-v2.10/should-quiet-6/run-2 | yes | yes |
| runs-v2.10/should-quiet-6/run-3 | yes | yes |

## Phase-40 should-quiet-5 (6 runs)

baseline **0/6** → candidate **0/6**

| run | baseline fires | candidate fires |
|---|---|---|
| runs-v2.10-phase40/batch1/should-quiet-5/run-1 | no | no |
| runs-v2.10-phase40/batch2/should-quiet-5/run-1 | no | no |
| runs-v2.10-phase40/batch3/should-quiet-5/run-1 | no | no |
| runs-v2.10-phase40/final/should-quiet-5/run-1 | no | no |
| runs-v2.10-phase40/final/should-quiet-5/run-2 | no | no |
| runs-v2.10-phase40/final/should-quiet-5/run-3 | no | no |

## Informational — v2.9 quiet (9 runs)

baseline **6/9** → candidate **6/9**

| run | baseline fires | candidate fires |
|---|---|---|
| runs/should-quiet-1/run-1 | yes | yes |
| runs/should-quiet-1/run-2 | yes | yes |
| runs/should-quiet-1/run-3 | yes | yes |
| runs/should-quiet-2/run-1 | no | no |
| runs/should-quiet-2/run-2 | no | no |
| runs/should-quiet-2/run-3 | no | no |
| runs/should-quiet-3/run-1 | yes | yes |
| runs/should-quiet-3/run-2 | yes | yes |
| runs/should-quiet-3/run-3 | yes | yes |

## Informational — should-quiet-7 (3 runs, UNLABELED per ledger 001; not gated, not calibrated)

baseline **3/3** → candidate **3/3**

| run | baseline fires | candidate fires |
|---|---|---|
| runs-v2.10/should-quiet-7/run-1 | yes | yes |
| runs-v2.10/should-quiet-7/run-2 | yes | yes |
| runs-v2.10/should-quiet-7/run-3 | yes | yes |

## Rows that fire under the candidate


### runs-v2.10/should-quiet-1/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | warning | 88 | 8f7bdb7216cf |
| impact | triggarr/web/validation.py | 84 | warning | 83 | eac7063a7a37 |

### runs-v2.10/should-quiet-1/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | critical | 100 | c9b5a67f246c |
| bugs | triggarr/web/validation.py | 85 | warning | 88 | 24cd061ddfe7 |
| security | triggarr/web/validation.py | 80 | critical | 100 | bd45ce6e3002 |
| architecture | triggarr/web/validation.py | 85 | warning | 94 | 4454e8b3abab |
| impact | triggarr/web/validation.py | 85 | warning | 92 | f6bd250167db |
| codex-adversarial | triggarr/web/validation.py | 85 | critical | 100 | 942e4d5e8ad7 |

### runs-v2.10/should-quiet-1/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/web/validation.py | 85 | warning | 94 | ecf83bf3db3b |
| bugs | triggarr/web/validation.py | 84 | critical | 100 | c3c0262c67eb |
| bugs | triggarr/web/validation.py | 85 | critical | 98 | 3c30d471d109 |

### runs-v2.10/should-quiet-2/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/angular/src/app/services/settings/config.service.ts | 68 | warning | 83 | 8d5bc54bf09c |

### runs-v2.10/should-quiet-2/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/angular/src/app/services/settings/config.service.ts | 68 | warning | 80 | 60b7994873c9 |

### runs-v2.10/should-quiet-2/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/angular/src/app/services/settings/config.service.ts | 67 | warning | 83 | d98885e14a51 |

### runs-v2.10/should-quiet-3/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/roonseek/transfer.py | 204 | warning | 93 | d53e83bf3dde |

### runs-v2.10/should-quiet-3/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/roonseek/transfer.py | 259 | warning | 82 | df92f5c2cfaf |
| impact | src/roonseek/transfer.py | 204 | warning | 87 | f2b2b8911673 |

### runs-v2.10/should-quiet-4/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 110 | warning | 87 | f0d5665c101a |
| architecture | triggarr/models/config.py | 106 | warning | 94 | 08b97add6c88 |
| impact | triggarr/models/config.py | 93 | critical | 100 | 4a6f6230e7d2 |

### runs-v2.10/should-quiet-4/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/models/config.py | 106 | warning | 94 | 162b635b74eb |
| architecture | triggarr/models/config.py | 93 | warning | 88 | c012d46c3394 |
| bugs | triggarr/models/config.py | 93 | warning | 93 | 801b0c3e7928 |
| bugs | triggarr/models/config.py | 108 | critical | 97 | 31132adebca8 |
| bugs | triggarr/models/config.py | 93 | warning | 84 | f846c3c8fbb1 |
| impact | triggarr/models/config.py | 93 | critical | 97 | 124c1db99924 |

### runs-v2.10/should-quiet-4/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 93 | critical | 100 | 464c5f3da64d |
| bugs | triggarr/models/config.py | 93 | warning | 94 | e39f9b3b901a |
| impact | triggarr/models/config.py | 93 | warning | 88 | 7b609387d1f1 |

### runs-v2.10/should-quiet-6/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | d888cc00169f |

### runs-v2.10/should-quiet-6/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | d888cc00169f |

### runs-v2.10/should-quiet-6/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | d888cc00169f |

### runs/should-quiet-1/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 87 | critical | 100 | 37f78051c196 |
| security | triggarr/web/validation.py | 85 | warning | 82 | 233f03a6e0f8 |
| impact | triggarr/web/validation.py | 87 | warning | 85 | 8af66164b9dc |
| codex-adversarial | triggarr/web/validation.py | 85 | critical | 100 | 6a3d6e71ed3f |

### runs/should-quiet-1/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 87 | critical | 100 | bfab50b47991 |
| security | triggarr/web/validation.py | 85 | critical | 97 | 42b697edc7df |
| codex-adversarial | triggarr/web/validation.py | 80 | critical | 100 | f2a919858f19 |

### runs/should-quiet-1/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 87 | critical | 100 | 1953964a3c6a |
| bugs | triggarr/web/validation.py | 85 | warning | 82 | 588ebcb45032 |
| security | triggarr/web/validation.py | 80 | critical | 97 | 0fd4a28ca370 |
| codex-adversarial | triggarr/web/validation.py | 85 | critical | 100 | 0a40ea77053b |

### runs/should-quiet-3/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| test-sufficiency | src/roonseek/transfer.py | 209 | critical | 97 | 8dc92303069e |

### runs/should-quiet-3/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/roonseek/transfer.py | 204 | critical | 99 | 909ad57f354f |

### runs/should-quiet-3/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/roonseek/transfer.py | 209 | warning | 93 | e72ce497e80b |

### runs-v2.10/should-quiet-7/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | cb474c5969bd |
| bugs | triggarr/web/routes.py | 446 | critical | 98 | 74ed3db64bfd |
| impact | triggarr/templates/settings.html | 74 | warning | 80 | 403965a3ee87 |
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 9813efd219e5 |
| codex-adversarial | triggarr/web/routes.py | 446 | critical | 100 | 1b19ad4a5363 |

### runs-v2.10/should-quiet-7/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | warning | 82 | 094c32f22700 |
| impact | triggarr/web/routes.py | 550 | critical | 100 | 795f31d1019b |
| codex-adversarial | triggarr/web/routes.py | 446 | critical | 100 | d8487312fd9b |

### runs-v2.10/should-quiet-7/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 32f94f3fc8c6 |
| bugs | triggarr/web/routes.py | 446 | critical | 100 | f62247258213 |
| architecture | triggarr/templates/settings.html | 74 | warning | 83 | 9bded9a0fd01 |
| impact | triggarr/templates/settings.html | 78 | warning | 80 | 0c580444d1d0 |
| impact | triggarr/web/routes.py | 550 | critical | 100 | 40ddaaaa9697 |
| codex-adversarial | triggarr/web/routes.py | 446 | critical | 100 | 30c1d8feff9e |

## Fidelity summary

**56/66 exact** (the replay's (band, score, stable_hash) multiset equals the archive's)

## Baseline fidelity drift (disclosed — score/band drift is why comparison is baseline-relative; it never removes a run from the protected 26)

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
