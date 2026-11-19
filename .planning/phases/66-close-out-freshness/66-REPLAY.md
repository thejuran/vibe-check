# Phase 66 — Replay and differential vs 2.15.0

- **Candidate commit:** `cf1ea0bde6ad86cc1fae798d730d3b2d1c7fadb8` (cf1ea0bd, branch feat/v2.16-phase-66)
- **Latest candidate:** `475b2e32a369c1b218aa6ee88a5d85e7c1fbd4d7` (gap closure, section 5)
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

## 5. Gap closure re-run (999.44 shape 1 repair)

- **Candidate commit:** `475b2e32a369c1b218aa6ee88a5d85e7c1fbd4d7` (475b2e32, branch feat/v2.16-phase-66; the commit that ends 66-12 Task 1, clean tree)
- **Base:** `d5acc19` (2.15.0)
- **Date:** 2026-11-19 (UTC)
- **Evidence class: OFFLINE.** No live reviewer run and no live session (GATE-08). Every number below comes from a local run on the main checkout at this candidate.

Sections 1-4 above are the cf1ea0bd record and are kept as history. The 999.40 repair is re-covered by the full run on 475b2e32: ROADMAP §999.40 still names candidate cf1ea0bd, and its tests (`TestRepro999_40`, `TestOnlyIntendedDifferences`) are part of the run below.

### 5.1 Scorer replay

Command: `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>/replay-66-gap.md` (exit 0)

- base sha256 = candidate sha256 = `c648872979e9bf3fd5e5f56f64f229de783c8e47258e45651cb5a06742f5e725`
- roots: all (7 roots); allowances: none
- runs compared: **170**
- runs differing: **0** (allowed 0, unallowed 0); allowances unused: 0
- head recorded by the tool: 475b2e32a369c1b218aa6ee88a5d85e7c1fbd4d7 (generated 2026-11-19T02:02:06Z)
- `git diff --quiet d5acc19 -- plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/diff_ranges.py` → exit 0 (both byte-identical to 2.15.0)
- `git diff --stat d5acc19` on the touched helpers: `30-collect-score.md` 14 +-, `carry_state.py` 17 ++- (the earlier shape 2 repair only), `worktree_snap.py` 145 +++-- (the gap closure's removed-lines output); 3 files, 141 insertions, 35 deletions.

### 5.2 Full offline suite and stdlib check

- `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` → **4790 passed, 0 xfailed, 2 warnings, 7400 subtests passed in 617.94s, exit 0**
  - Parity grid: 284 scenarios, 198 agree, 12 D-19, 56 D-09 refusals, 0 unexpected, 18 not creatable here.
  - 0 xfailed: the two shape 1 known-limit `expectedFailure` tests were turned into passing tests by 66-11.
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` → **35 shipped .py files; third-party imports: none; exit 0**

### 5.3 Finalize differential

`cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_closeout_fresh.py -k only_intended` → **3 passed, 390 subtests passed**. The named lists are unchanged (76 intended refusals, 2 shape 2 repair differences); all other runs are byte-identical.

### 5.4 Review-side differentials against literal 2.15.0

- **Collect differential** (`TestCollectDifferentialV215`, 66-10): `worktree_snap.py` and `diff_ranges.py` materialized from d5acc19. On every one of the 13 `REMOVED_GRID` states the exit codes are equal, the first two output lines (`REVIEWED_TREE=`, `NEARBY_LINE_RANGES=`) are byte-identical to d5acc19, and the third line (`REMOVED_LINE_RANGES=`) is the added one; same number of git calls.
- **Relocation differential** (`TestShape1DifferentialV215`, 66-11): the 2.15.0 `relocate_decided` / `next_cf` / `run_pass` read from d5acc19. Of 15 scenarios × 2 kinds, every envelope, new state and score result is byte-identical except the four named scenarios `shape1_kept`, `shape1_edited`, `no_evidence_shape1` and `no_evidence_shift` (each for defer and dismiss), where 2.15.0 is `current` / write and the candidate is `stale` / not write. Checked in both directions.
- `pytest -q test_worktree_snap.py test_decision_continuity.py -k "DifferentialV215"` → 7 passed, 38 subtests passed.

### 5.5 Shape 1 end to end and mutation checks

- `pytest -q test_worktree_snap.py test_closeout_fresh.py -k Shape1` → 10 passed, 4 subtests passed: `TestShape1ThroughFences` (default route, real fences), `TestShape1ThroughFencesRange` (range route) and `TestShape1Clearable` (refuse → fresh review re-asks → Close out neither writes nor loops → re-decide → write, for defer and dismiss). The same journey with the forced re-ask off (the 2.15.0 review-side procedure) keeps the decision and Close out writes: `test_shape1_old_review_procedure_writes`.
- Mutant counts: **5 helper** (removed-lines output, 66-10), **7 rule** (forced re-ask, 66-11), **2 fence-wiring** (66-12: forced re-ask off, evidence not threaded); each fails its named test.

**Known behaviour (owner decision 2026-11-18):** when the removal evidence is missing — the code changed during the pass, or the prior pass recorded no reviewed tree, which also leaves the following pass without evidence — a deferred or dismissed decision whose line only shifted is asked again; 2.15.0 kept that decision; the owner chose the re-ask ("Re-ask them") on 2026-11-18 as a deliberate, tested difference.
