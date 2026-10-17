# Replay report — complete-output diff

- base: rev:ebcd3e4 (sha256 525c5e838b73a4126d35cad72696b711651f04200f4e688914e95b69319dc814)
- candidate: rev:ddbfff402816805136e95393c98a3cc17196daeb (sha256 8b8839a4c25aa0dc9f4218fad13af578010692d8db092d4cd3d336384ba7088e)
- roots: all (7 roots)
- allowances: docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json
- runs compared: 170
- runs differing: 0
- runs differing (allowed): 0
- runs with unallowed differences: 0
- allowances unused: 65
- head: ed3f9f8029f1d80062e8687329f34413fc777164
- generated: 2026-10-17T17:30:39Z

_no rounding — exact fractions_

## Differences

- none

## Roots compared

_Appended by the 54-10 executor (re-run #6). `replay.py diff` lists only differing runs, so the per-root breakdown of the 170 compared runs is recorded here. It was computed from `replay.iter_runs(roots=replay.DIFF_ROOTS)` at candidate ddbfff402816805136e95393c98a3cc17196daeb. The report body above is unedited. Earlier runs are kept in `docs/design/freeze-v2.12/evidence/superseded-302df48e1097/`, `superseded-24c0c00038f2/`, `superseded-2a6dbb4874b7/` and `superseded-22ef678fb884/` (the 535f488 and 14808a9 re-runs stopped before this step)._

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
