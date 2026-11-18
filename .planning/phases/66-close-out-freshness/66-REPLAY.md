# Phase 66 — Replay and differential vs 2.15.0

- **Candidate commit:** `cf1ea0bde6ad86cc1fae798d730d3b2d1c7fadb8` (cf1ea0bd, branch feat/v2.16-phase-66)
- **Base:** `d5acc19` (2.15.0)
- **Date:** 2026-11-18
- **Evidence class: OFFLINE.** No live reviewer run (GATE-08). Every number below comes from a local run on the main checkout at the candidate commit.

## 1. Scorer replay (SC4)

Command: `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>/replay-66-cf1ea0bd.md` (exit 0)

- base sha256 = candidate sha256 = `c648872979e9bf3fd5e5f56f64f229de783c8e47258e45651cb5a06742f5e725` (score.py unchanged since 2.15.0)
- roots: all (7 roots); allowances: none
- runs compared: **170**
- runs differing: **0** (allowed 0, unallowed 0); allowances unused: 0
- head recorded by the tool: cf1ea0bde6ad86cc1fae798d730d3b2d1c7fadb8 (generated 2026-11-18T23:36:33Z)

### Differences

- none

(An earlier run on 25bcbbb1 gave the same result, 170 compared / 0 differing. Commits after 25bcbbb1 touch only `.github/scripts/test_stdlib_only.py` and `docs/design/lean-v2.15/tools/`. The rerun above is the one on record.)

## 2. Finalize differential (SC4, `TestOnlyIntendedDifferences`)

Command: `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_closeout_fresh.py -k only_intended` on cf1ea0bd: **3 passed, 390 subtests passed**.

For each fixture run, the 2.15.0 helper (materialized from d5acc19) and the candidate helper either give byte-identical output, or the difference is on a named list. Both lists are checked in both directions: every listed entry must actually differ, and no unlisted entry may differ.

- 312 fixture runs: 66-02 result fixtures, parity-grid scenarios, 66-01 controls and 66-06/66-08 shape fixtures, each in the unchanged / exact / nearby / outside / untracked variants.
- **76 intended refusals** (`INTENDED`: 6 for 999.40, 2 for shape 3, 12 result-fixture, 56 parity-grid). 2.15.0 wrote or opened the card. The candidate refuses with `stop-review-again` and the listed cause (999.40 exact/nearby/untracked for both kinds, shape 3 untracked, result fixtures, and the parity grid's 56 named D-09 refusals).
- **2 repair differences** (`REPAIRED`). These are the 999.44 shape 2 fixture (`shape2:older_first:both`) for defer and dismiss. The change comes from commit `75e4a1da` (newest covering decision wins, owner-approved).
- All other runs are byte-identical.
- `score.py` is byte-identical to `d5acc19:plugins/vibe-check/scripts/score.py` (`SCORER_CHANGES = ()`).

## 3. Full offline suite and stdlib check (GATE-07)

On cf1ea0bd, clean tree:

- `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` → **4706 passed, 2 xfailed, 2 warnings, 7173 subtests passed in 652.79s, exit 0**
  - The 2 xfails are the 999.44 shape 1 known-limit tests (`test_shape1_*_known_limit`, expectedFailure). Shape 1 is an owner-accepted known limit, not a repair.
  - Parity grid summary: 284 scenarios: 198 agree, 12 D-19, 56 D-09 refusals, 0 known differences, 0 unexpected, 18 not creatable here.
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` → **35 shipped .py files; third-party imports: none; exit 0**

The FRESH-02 regression set (fix-verdict freshness, 999.28 parity, real-edit reopening, parity grid) is part of that run and is green.

## 4. lean-v2.15 Finalize capture (2.14.1 record)

- `finalize_capture.py verify --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json` → "finalize baseline matches (5 situations)", exit 0. The committed record is unchanged.
- `finalize_capture.py compare --driver helper --root plugins/vibe-check` → "finalize outcome fields match (5 situations, 7 walks)", exit 0. Only `steps` and `tally` differ, as before. The refusal lines are identical.
- Since cf1ea0bd the candidate walks run on a reviewed git tree with `reviewed_tree` stamped. Without one, Close out fails closed under D-09 (see 66-09-SUMMARY deviations).
