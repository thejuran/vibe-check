# Replay report — complete-output diff

- base: blob:5ca2ddd5cc9a7f88bab9bbdc0604477e8a3d0504 (sha256 660d09ef6753b5a987d948a69c891548898f35ce88053b0be77222a4f94f1089)
- candidate: rev:HEAD (sha256 525c5e838b73a4126d35cad72696b711651f04200f4e688914e95b69319dc814)
- roots: all (6 roots)
- allowances: docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json
- runs compared: 154
- runs differing: 65
- runs differing (allowed): 65
- runs with unallowed differences: 0
- allowances unused: 0
- head: ebcd3e4fded8f7793abcca005191ea2c182933f1
- generated: 2026-10-15T02:12:00Z

_no rounding — exact fractions_

## runs-v2.10-phase40/batch1/triggarr-secret-in-logs/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 233 | critical | 100 | 1b7b0aee39af |
| security | triggarr/clients/base.py | 254 | warning | 94 | 9df57cdcdad5 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 233 | critical | 100 | 1b7b0aee39af |
| security | triggarr/clients/base.py | 254 | warning | 94 | 9df57cdcdad5 |

## runs-v2.10-phase40/batch2/triggarr-secret-in-logs/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | 087270666450 |
| security | triggarr/clients/base.py | 252 | warning | 92 | 66cb504a179b |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | 087270666450 |
| security | triggarr/clients/base.py | 252 | warning | 92 | 66cb504a179b |

## runs-v2.10-phase40/batch3/triggarr-secret-in-logs/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | a3152fbf25ef |
| security | triggarr/clients/base.py | 252 | warning | 94 | c9cb8e9eb043 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | a3152fbf25ef |
| security | triggarr/clients/base.py | 252 | warning | 94 | c9cb8e9eb043 |

## runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 8f4d653e7115 |
| compliance | triggarr/clients/base.py | 254 | warning | 94 | 0fd15b2ec9c1 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 8f4d653e7115 |
| compliance | triggarr/clients/base.py | 254 | warning | 94 | 0fd15b2ec9c1 |

## runs-v2.10-phase40/final/triggarr-secret-in-logs/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/clients/base.py | 233 | critical | 100 | 0b2e8f96c286 |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | 6518d73e9ee0 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/clients/base.py | 233 | critical | 100 | 0b2e8f96c286 |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | 6518d73e9ee0 |

## runs-v2.10-phase40/final/triggarr-secret-in-logs/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 2f2682e656ae |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | 6d2c061ac11a |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 2f2682e656ae |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | 6d2c061ac11a |

## runs-v2.10-phase41/final/should-quiet-1/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | warning | 90 | 4eeb09a3403a |
| security | triggarr/web/validation.py | 89 | warning | 94 | fe9c5f7b2b2e |
| impact | triggarr/web/validation.py | 81 | warning | 85 | c00a8afaf61b |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | warning | 90 | 4eeb09a3403a |
| security | triggarr/web/validation.py | 89 | warning | 94 | fe9c5f7b2b2e |
| impact | triggarr/web/validation.py | 81 | warning | 85 | c00a8afaf61b |

## runs-v2.10-phase41/final/should-quiet-1/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/validation.py | 85 | warning | 94 | 77b0d459a9ce |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/validation.py | 85 | warning | 94 | 77b0d459a9ce |

## runs-v2.10-phase41/final/should-quiet-1/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | warning | 94 | 401d763a17d3 |
| security | triggarr/web/validation.py | 81 | warning | 94 | 38451d8da459 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | warning | 94 | 401d763a17d3 |
| security | triggarr/web/validation.py | 81 | warning | 94 | 38451d8da459 |

## runs-v2.10-phase41/final/should-quiet-3/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/roonseek/transfer.py | 204 | medium | 73 | 8e46a75cfd53 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/roonseek/transfer.py | 204 | medium | 73 | 8e46a75cfd53 |

## runs-v2.10-phase41/final/should-quiet-3/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/roonseek/transfer.py | 260 | medium | 70 | 0e7d3a536eb0 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/roonseek/transfer.py | 260 | medium | 70 | 0e7d3a536eb0 |

## runs-v2.10-phase41/final/should-quiet-3/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| language-python | src/roonseek/transfer.py | 259 | medium | 77 | 8cbd5641b201 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| language-python | src/roonseek/transfer.py | 259 | medium | 77 | 8cbd5641b201 |

## runs-v2.10-phase43/first/should-quiet-3/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| language-python | src/roonseek/transfer.py | 259 | medium | 72 | c0d55d33a6c7 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| language-python | src/roonseek/transfer.py | 259 | medium | 72 | c0d55d33a6c7 |

## runs-v2.10-phase43/first/should-quiet-4/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 108 | critical | 100 | 14f1895e7297 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 108 | critical | 100 | 14f1895e7297 |

## runs-v2.10-phase43/first/should-quiet-4/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 5

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | warning | 94 | de932df74922 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | warning | 94 | de932df74922 |

## runs-v2.10-phase43/first/should-quiet-4/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 4

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | warning | 94 | fedecf9ededf |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | warning | 94 | fedecf9ededf |

## runs-v2.10-phase43/first/should-quiet-6/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 4

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.10-phase43/first/should-quiet-6/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 5

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | 92e9bcdf8831 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | 92e9bcdf8831 |

## runs-v2.10-phase43/first/should-quiet-6/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 5

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

## runs-v2.10-phase43/first/should-quiet-7/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 530fe1eb6b5d |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 21667f91c616 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 530fe1eb6b5d |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 21667f91c616 |

## runs-v2.10-phase43/first/should-quiet-7/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 234ca986d72e |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 30c1d8feff9e |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 234ca986d72e |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 30c1d8feff9e |

## runs-v2.10-phase43/first/should-quiet-7/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 550 | critical | 100 | 2b1a20a238c5 |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 86011a03320d |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 550 | critical | 100 | 2b1a20a238c5 |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 86011a03320d |

## runs-v2.10-phase43/first/third-organic-should-catch/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 2548af945a95 |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | medium | 72 | 73c2ad85e908 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 2548af945a95 |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | medium | 72 | 73c2ad85e908 |

## runs-v2.10-phase43/first/triggarr-autoescape/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/web/routes.py | 45 | warning | 94 | 52c0faec4e3b |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/web/routes.py | 45 | warning | 94 | 52c0faec4e3b |

## runs-v2.10-phase43/first/triggarr-autoescape/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 4

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 4f30f8fb283f |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 4f30f8fb283f |

## runs-v2.10-phase43/first/triggarr-autoescape/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 819009c3e634 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 819009c3e634 |

## runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 5

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 232 | warning | 94 | 13f543dd935e |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | af2794b67712 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 232 | warning | 94 | 13f543dd935e |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | af2794b67712 |

## runs-v2.10-phase43/first/triggarr-secret-in-logs/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 12fe298fc07e |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | b76221829580 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 12fe298fc07e |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | b76221829580 |

## runs-v2.10-phase43/first/triggarr-secret-in-logs/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 5718c2673139 |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | 17ab47c4de4d |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 5718c2673139 |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | 17ab47c4de4d |

## runs-v2.10-phase43/first/triggarr-session-rotation/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/web/routes.py | 1567 | warning | 94 | 91ff52630953 |
| impact | triggarr/web/routes.py | 1581 | warning | 85 | 90eb761f16d7 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/web/routes.py | 1567 | warning | 94 | 91ff52630953 |
| impact | triggarr/web/routes.py | 1581 | warning | 85 | 90eb761f16d7 |

## runs-v2.10-phase43/retune/should-quiet-4/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 4

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/models/config.py | 106 | medium | 71 | c8ab6f00b8c8 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/models/config.py | 106 | medium | 71 | c8ab6f00b8c8 |

## runs-v2.10-phase43/retune/should-quiet-4/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 4

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/models/config.py | 106 | medium | 78 | b0ff005cdf60 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/models/config.py | 106 | medium | 78 | b0ff005cdf60 |

## runs-v2.10-phase43/retune/should-quiet-4/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | medium | 70 | a297cbf58569 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | medium | 70 | a297cbf58569 |

## runs-v2.10-phase43/retune/should-quiet-6/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.10-phase43/retune/should-quiet-6/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 4

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | 4ac803dd7f3d |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | 4ac803dd7f3d |

## runs-v2.10-phase43/retune/should-quiet-6/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 5

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.10-phase43/retune/triggarr-autoescape/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | warning | 94 | 14ce70a9e263 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | warning | 94 | 14ce70a9e263 |

## runs-v2.10-phase43/retune/triggarr-autoescape/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 09946da53edd |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 09946da53edd |

## runs-v2.10-phase43/retune/triggarr-autoescape/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | warning | 94 | c2cc00804f6b |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | warning | 94 | c2cc00804f6b |

## runs-v2.10/should-quiet-1/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | warning | 88 | 8f7bdb7216cf |
| impact | triggarr/web/validation.py | 77 | medium | 70 | f9b84f7c44e5 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 85 | warning | 88 | 8f7bdb7216cf |
| impact | triggarr/web/validation.py | 77 | medium | 70 | f9b84f7c44e5 |

## runs-v2.10/should-quiet-2/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | src/angular/src/app/services/utils/rest.service.ts | 59 | medium | 78 | 422b5f3b755a |
| impact | src/angular/src/app/services/settings/config.service.ts | 67 | warning | 83 | d98885e14a51 |
| impact | src/e2e/tests/fixtures/seed-state.ts | 72 | medium | 73 | 2153ce6bbd39 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | src/angular/src/app/services/utils/rest.service.ts | 59 | medium | 78 | 422b5f3b755a |
| impact | src/angular/src/app/services/settings/config.service.ts | 67 | warning | 83 | d98885e14a51 |
| impact | src/e2e/tests/fixtures/seed-state.ts | 72 | medium | 73 | 2153ce6bbd39 |

## runs-v2.10/should-quiet-3/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | src/roonseek/transfer.py | 139 | medium | 74 | 9fe195ad2c2e |
| impact | src/roonseek/transfer.py | 204 | medium | 72 | 93d7b3578b5c |
| bugs | src/roonseek/transfer.py | 259 | medium | 70 | 7b3303374a94 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | src/roonseek/transfer.py | 139 | medium | 74 | 9fe195ad2c2e |
| impact | src/roonseek/transfer.py | 204 | medium | 72 | 93d7b3578b5c |
| bugs | src/roonseek/transfer.py | 259 | medium | 70 | 7b3303374a94 |

## runs-v2.10/should-quiet-3/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/roonseek/transfer.py | 259 | warning | 82 | df92f5c2cfaf |
| impact | src/roonseek/transfer.py | 204 | warning | 87 | f2b2b8911673 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/roonseek/transfer.py | 259 | warning | 82 | df92f5c2cfaf |
| impact | src/roonseek/transfer.py | 204 | warning | 87 | f2b2b8911673 |

## runs-v2.10/should-quiet-4/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/models/config.py | 106 | warning | 94 | 08b97add6c88 |
| impact | triggarr/models/config.py | 93 | warning | 94 | 4a6f6230e7d2 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/models/config.py | 106 | warning | 94 | 08b97add6c88 |
| impact | triggarr/models/config.py | 93 | warning | 94 | 4a6f6230e7d2 |

## runs-v2.10/should-quiet-4/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | warning | 94 | 31132adebca8 |
| impact | triggarr/models/config.py | 93 | warning | 94 | 124c1db99924 |
| security | triggarr/config.py | 371 | medium | 70 | 692c72e68ce1 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | warning | 94 | 31132adebca8 |
| impact | triggarr/models/config.py | 93 | warning | 94 | 124c1db99924 |
| security | triggarr/config.py | 371 | medium | 70 | 692c72e68ce1 |

## runs-v2.10/should-quiet-7/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 9813efd219e5 |
| codex-adversarial | triggarr/web/routes.py | 446 | critical | 100 | 1b19ad4a5363 |
| impact | triggarr/templates/settings.html | 74 | warning | 80 | 403965a3ee87 |
| impact | triggarr/search/scheduler.py | 81 | medium | 70 | 2ce7cff05433 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 9813efd219e5 |
| codex-adversarial | triggarr/web/routes.py | 446 | critical | 100 | 1b19ad4a5363 |
| impact | triggarr/templates/settings.html | 74 | warning | 80 | 403965a3ee87 |
| impact | triggarr/search/scheduler.py | 81 | medium | 70 | 2ce7cff05433 |

## runs-v2.10/triggarr-secret-in-logs/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 252 | warning | 82 | 7074d66fd289 |
| codex-adversarial | triggarr/clients/base.py | 233 | warning | 94 | 12fe298fc07e |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 252 | warning | 82 | 7074d66fd289 |
| codex-adversarial | triggarr/clients/base.py | 233 | warning | 94 | 12fe298fc07e |

## runs-v2.10/triggarr-session-rotation/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1564 | warning | 94 | 1978f7feb13c |
| bugs | triggarr/web/routes.py | 1581 | warning | 80 | c3a42dde79d6 |
| bugs | triggarr/web/routes.py | 1584 | medium | 78 | 48531a82fa6d |
| architecture | triggarr/web/routes.py | 1567 | critical | 100 | 218a4c801a5a |
| architecture | triggarr/web/routes.py | 1588 | warning | 91 | f9e7437c16aa |
| architecture | triggarr/web/routes.py | 1578 | medium | 76 | 292929086990 |
| impact | triggarr/web/routes.py | 1852 | medium | 70 | c0a4570ff99e |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1564 | warning | 94 | 1978f7feb13c |
| bugs | triggarr/web/routes.py | 1581 | warning | 80 | c3a42dde79d6 |
| bugs | triggarr/web/routes.py | 1584 | medium | 78 | 48531a82fa6d |
| architecture | triggarr/web/routes.py | 1567 | critical | 100 | 218a4c801a5a |
| architecture | triggarr/web/routes.py | 1588 | warning | 91 | f9e7437c16aa |
| architecture | triggarr/web/routes.py | 1578 | medium | 76 | 292929086990 |
| impact | triggarr/web/routes.py | 1852 | medium | 70 | c0a4570ff99e |

## runs-v2.11-phase49/first/should-quiet-3/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| language-python | src/roonseek/transfer.py | 259 | warning | 82 | 5c905a9fc3e6 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| language-python | src/roonseek/transfer.py | 259 | warning | 82 | 5c905a9fc3e6 |

## runs-v2.11-phase49/first/should-quiet-4/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | medium | 72 | a11aff939068 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | medium | 72 | a11aff939068 |

## runs-v2.11-phase49/first/should-quiet-4/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | medium | 70 | f12fbe78be96 |
| security | triggarr/models/config.py | 93 | warning | 94 | 2da26ca95733 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | medium | 70 | f12fbe78be96 |
| security | triggarr/models/config.py | 93 | warning | 94 | 2da26ca95733 |

## runs-v2.11-phase49/first/should-quiet-6/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 135 | warning | 94 | 780e77edbe52 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 135 | warning | 94 | 780e77edbe52 |

## runs-v2.11-phase49/first/should-quiet-6/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.11-phase49/first/should-quiet-6/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | 993c32eb9391 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | 993c32eb9391 |

## runs-v2.11-phase49/first/should-quiet-7/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 4d966837bba8 |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 30c1d8feff9e |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 4d966837bba8 |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 30c1d8feff9e |

## runs-v2.11-phase49/first/should-quiet-7/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 4

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 0ceea335d7ac |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 0eeb469a0669 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | 0ceea335d7ac |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 0eeb469a0669 |

## runs-v2.11-phase49/first/should-quiet-7/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | e09c5b0965cc |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 550 | critical | 100 | e09c5b0965cc |

## runs-v2.11-phase49/first/triggarr-secret-in-logs/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 658136bf0a0d |
| security | triggarr/clients/base.py | 252 | warning | 94 | 1f05d792a41d |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 658136bf0a0d |
| security | triggarr/clients/base.py | 252 | warning | 94 | 1f05d792a41d |

## runs-v2.11-phase49/first/triggarr-secret-in-logs/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 3

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 231222c433af |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | 48ab3c20fcc2 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 231222c433af |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | 48ab3c20fcc2 |

## runs-v2.11-phase49/first/triggarr-secret-in-logs/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 5

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | 4354e34981b5 |
| security | triggarr/clients/base.py | 252 | warning | 94 | 7b65158797ac |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | 4354e34981b5 |
| security | triggarr/clients/base.py | 252 | warning | 94 | 7b65158797ac |

## runs-v2.11-phase49/first/triggarr-session-rotation/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1567 | warning | 94 | 1c14bf7ba766 |
| impact | triggarr/web/routes.py | 1581 | medium | 75 | 8d4722ed1836 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1567 | warning | 94 | 1c14bf7ba766 |
| impact | triggarr/web/routes.py | 1581 | medium | 75 | 8d4722ed1836 |

## runs-v2.11-phase49/first/triggarr-session-rotation/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1567 | warning | 94 | 2bced0bfc4e2 |
| impact | triggarr/web/routes.py | 1581 | warning | 90 | f91ec7580f99 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1567 | warning | 94 | 2bced0bfc4e2 |
| impact | triggarr/web/routes.py | 1581 | warning | 90 | f91ec7580f99 |

## runs-v2.11-phase49/first/triggarr-session-rotation/run-3

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/web/routes.py | 1567 | critical | 100 | 110bc8c4571c |
| bugs | triggarr/web/routes.py | 1581 | warning | 90 | af39099f84a2 |
| impact | tests/test_auth_routes.py | 604 | medium | 70 | c97fffd58af8 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/web/routes.py | 1567 | critical | 100 | 110bc8c4571c |
| bugs | triggarr/web/routes.py | 1581 | warning | 90 | af39099f84a2 |
| impact | tests/test_auth_routes.py | 604 | medium | 70 | c97fffd58af8 |

## runs-v2.11-phase49/first/triggarr-settings-form-split/run-2

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 1

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/templates/settings.html | 18 | warning | 94 | 09e5ac6fbd78 |
| bugs | triggarr/templates/settings.html | 134 | warning | 94 | b093c747acac |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/templates/settings.html | 18 | warning | 94 | 09e5ac6fbd78 |
| bugs | triggarr/templates/settings.html | 134 | warning | 94 | b093c747acac |

## runs-v2.11-phase49/rehearsal/rehearsal-scratch/run-1

changed paths: 1
allowed: yes

- nv_dropped_weak: (absent) -> 2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/db.py | 864 | warning | 94 | 1c9c038e1ad7 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/db.py | 864 | warning | 94 | 1c9c038e1ad7 |

## Candidate

repo_head: ebcd3e4fded8f7793abcca005191ea2c182933f1 · FINAL_FP: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26 (runner copy loaded by the measured sessions == candidate tree; development rehearsal — not release evidence)
