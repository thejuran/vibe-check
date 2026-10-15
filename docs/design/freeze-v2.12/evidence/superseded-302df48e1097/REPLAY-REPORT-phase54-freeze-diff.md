# Replay report — complete-output diff

- base: rev:ebcd3e4 (sha256 525c5e838b73a4126d35cad72696b711651f04200f4e688914e95b69319dc814)
- candidate: rev:302df48e1097212aa334a21c8f2683ed810eb496 (sha256 ea6b041779c626b40607d4ba65ee0cc1c9522d2bd0c7cdd8995be4969768c233)
- roots: all (7 roots)
- allowances: docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json
- runs compared: 170
- runs differing: 0
- runs differing (allowed): 0
- runs with unallowed differences: 0
- allowances unused: 65
- head: 9901ffe8b7a2aa4429a4c3acc2e83b2789be49ac
- generated: 2026-10-15T21:46:11Z

_no rounding — exact fractions_

## Differences

- none

## Roots compared

_Appended by the 54-10 executor; `replay.py diff` lists only differing runs, so the per-root breakdown of the 170 compared runs is recorded here. Computed from `replay.iter_runs(roots=replay.DIFF_ROOTS)` at candidate 302df48e1097212aa334a21c8f2683ed810eb496; the report body above is unedited._

| root | runs compared |
|---|---|
| runs/ | 18 |
| runs-v2.10/ | 36 |
| runs-v2.10-phase40/ | 12 |
| runs-v2.10-phase41/ | 6 |
| runs-v2.10-phase43/ | 45 |
| runs-v2.11-phase49/ | 37 |
| ../reachability-dev/runs-phase53-dev/final/ (runs-phase53-dev/final) | 16 |
| **total** | **170** |
