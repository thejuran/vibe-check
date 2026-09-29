# Replay report — candidate combined

- candidate scorer: path:/Users/julianamacbook/turingmind-code-review/plugins/vibe-check/scripts/score.py
- candidate scorer sha256: 11303a24a5f4091a5aeb8c6d6b0559bd958560fd0ace4dc0a8fd57bc24ed05ff
- overrides: {}
- baseline: blob: b21f7f3d556e1522e9853511ed8e126057c417c0
- manifest: docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json
- manifest sha256: 7f5ac51140afa57d87262b89774510e4635f06cd9d9c65beb95a867124d65339
- amendments in force: 1
- HEAD: cedeb114f60198b543b1b43b274ab90481d87ac7
- generated (UTC): 2026-09-29T22:37:30Z

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
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1 | survivor-title | critical/100/member-title | kept |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-2 | survivor-title | critical/100/member-title | kept |
| runs-v2.10-phase40/final/triggarr-secret-in-logs/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/third-organic-should-catch/run-1 | survivor-title | critical/100/member-title | kept |
| runs-v2.10/third-organic-should-catch/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/third-organic-should-catch/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-autoescape/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-autoescape/run-2 | survivor-title | critical/100/member-title | kept |
| runs-v2.10/triggarr-autoescape/run-3 | survivor-title | critical/100/member-title | kept |
| runs-v2.10/triggarr-secret-in-logs/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-secret-in-logs/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-secret-in-logs/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-session-rotation/run-1 | survivor-title | critical/100/member-title | kept |
| runs-v2.10/triggarr-session-rotation/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-session-rotation/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-settings-form-split/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-settings-form-split/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs-v2.10/triggarr-settings-form-split/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs/third-organic-should-catch/run-1 | survivor-title | critical/100/survivor-title | kept |
| runs/third-organic-should-catch/run-2 | survivor-title | critical/100/survivor-title | kept |
| runs/third-organic-should-catch/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs/triggarr-autoescape/run-2 | survivor-title | critical/100/member-title | kept |
| runs/triggarr-autoescape/run-3 | survivor-title | critical/100/survivor-title | kept |
| runs/triggarr-secret-in-logs/run-1 | survivor-title | warning/94/survivor-title | kept |
| runs/triggarr-secret-in-logs/run-2 | axis-false | critical/100/member-title | AMENDED |
| runs/triggarr-secret-in-logs/run-3 | survivor-title | warning/94/survivor-title | kept |

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

### runs-v2.10/should-quiet-1/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | critical | 100 | 24cd061ddfe7 |
| security | triggarr/web/validation.py | 80 | warning | 94 | bd45ce6e3002 |

### runs-v2.10/should-quiet-1/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 84 | warning | 94 | c3c0262c67eb |

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
| architecture | triggarr/models/config.py | 106 | warning | 94 | 08b97add6c88 |
| impact | triggarr/models/config.py | 93 | warning | 94 | 4a6f6230e7d2 |

### runs-v2.10/should-quiet-4/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | warning | 94 | 31132adebca8 |
| impact | triggarr/models/config.py | 93 | warning | 94 | 124c1db99924 |

### runs-v2.10/should-quiet-4/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 93 | warning | 94 | 464c5f3da64d |

### runs-v2.10/should-quiet-6/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | d888cc00169f |

### runs-v2.10/should-quiet-6/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | d888cc00169f |

### runs-v2.10/should-quiet-6/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | d888cc00169f |

### runs/should-quiet-1/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 87 | critical | 100 | 37f78051c196 |

### runs/should-quiet-1/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 87 | warning | 94 | bfab50b47991 |
| codex-adversarial | triggarr/web/validation.py | 80 | warning | 94 | f2a919858f19 |

### runs/should-quiet-1/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/validation.py | 85 | critical | 100 | 0a40ea77053b |
| security | triggarr/web/validation.py | 80 | warning | 94 | 0fd4a28ca370 |

### runs/should-quiet-3/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| test-sufficiency | src/roonseek/transfer.py | 209 | warning | 94 | 8dc92303069e |

### runs/should-quiet-3/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/roonseek/transfer.py | 204 | warning | 94 | 909ad57f354f |

### runs/should-quiet-3/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/roonseek/transfer.py | 209 | warning | 93 | e72ce497e80b |

### runs-v2.10/should-quiet-7/run-1

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 9813efd219e5 |
| codex-adversarial | triggarr/web/routes.py | 446 | critical | 100 | 1b19ad4a5363 |
| impact | triggarr/templates/settings.html | 74 | warning | 80 | 403965a3ee87 |

### runs-v2.10/should-quiet-7/run-2

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 550 | critical | 100 | 795f31d1019b |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | d8487312fd9b |

### runs-v2.10/should-quiet-7/run-3

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 32f94f3fc8c6 |
| codex-adversarial | triggarr/web/routes.py | 446 | critical | 100 | 30c1d8feff9e |
| architecture | triggarr/templates/settings.html | 74 | warning | 83 | 9bded9a0fd01 |
| impact | triggarr/templates/settings.html | 78 | warning | 80 | 0c580444d1d0 |

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
