# Phase 66 — Replay and differential vs 2.15.0

- **Candidate commit:** `cf1ea0bde6ad86cc1fae798d730d3b2d1c7fadb8` (cf1ea0bd, branch feat/v2.16-phase-66)
- **Gap-closure candidate:** `475b2e32a369c1b218aa6ee88a5d85e7c1fbd4d7` (gap closure, section 5)
- **Latest candidate:** `fa5afc559e509a838acd29c12487d1b0e6ac44b5` (after the gap-closure review fixes and the WR-01 lock, section 6)
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

## 6. Re-run after the gap-closure review fixes and owner rulings (2026-11-19)

- **Candidate commit:** `fa5afc559e509a838acd29c12487d1b0e6ac44b5` (fa5afc55, branch feat/v2.16-phase-66; HEAD after `test(66): lock owner-accepted neighbour re-ask (WR-01)`, clean tree). It includes review fixes e3888c9c (CR-01) and cb2da984 (WR-02), made after the 475b2e32 run in section 5.
- **Base:** `d5acc19` (2.15.0)
- **Date:** 2026-11-19
- **Evidence class: OFFLINE.** No live reviewer run and no live session (GATE-08). Every number below comes from a local run on the main checkout at this candidate.

Section 5 is the 475b2e32 record and is kept as history. Its statement in 5.4 that the first two collect lines are byte-identical to d5acc19 holds on the 13 `REMOVED_GRID` states, but no longer for files with non-ASCII names; see 6.4.

### 6.1 Scorer replay

Command: `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>/replay-66-fa5afc55.md` (exit 0)

- base sha256 = candidate sha256 = `c648872979e9bf3fd5e5f56f64f229de783c8e47258e45651cb5a06742f5e725`
- roots: all (7 roots); allowances: none
- runs compared: **170**
- runs differing: **0** (allowed 0); allowances unused: 0
- head recorded by the tool: fa5afc559e509a838acd29c12487d1b0e6ac44b5 (generated 2026-11-19T11:23:49Z)
- `git diff --quiet d5acc19 -- plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/diff_ranges.py` → exit 0 (both byte-identical to 2.15.0)

### 6.2 Plugin suite and stdlib check

- `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider` → **4340 passed, 0 xfailed, 2 warnings, 7132 subtests passed in 438.70s, exit 0**
  - Scope: the plugin scripts directory only (the command 66-REVIEW-FIX.md used at cb2da984: 4337 passed, 7126 subtests). The 3 extra tests and 6 extra subtests are the WR-01 lock and its two mutants. This is not the three-root command of sections 3 and 5.2; `.github/scripts` and `docs/design/lean-v2.15/tools` were not re-run here.
  - Parity grid: 284 scenarios, 198 agree, 12 D-19, 56 D-09 refusals, 0 known differences, 0 unexpected, 18 not creatable here.
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` → **35 shipped .py files; third-party imports: none; exit 0**

### 6.3 2.15.0 differentials

`cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider -k "DifferentialV215 or only_intended"` → **12 passed, 4328 deselected, 428 subtests passed** (48.84s; run while the full suite was also running). This covers `TestOnlyIntendedDifferences` (Finalize: 76 named refusals and 2 shape 2 repair differences, all else byte-identical), `TestCollectDifferentialV215`, `TestShape1DifferentialV215` (only `shape1_kept`, `shape1_edited`, `no_evidence_shape1`, `no_evidence_shift` differ) and `TestQuotedNamesDifferentialV215`.

### 6.4 Owner-accepted differences recorded on this candidate (2026-11-19)

- **Non-ASCII names (review fix e3888c9c, owner: keep).** The since-review diff runs with `core.quotePath=false`, so `NEARBY_LINE_RANGES=` and `REMOVED_LINE_RANGES=` list a non-ASCII file under its real name; 2.15.0 omitted it from `NEARBY_LINE_RANGES=`. Locked by `TestQuotedNamesDifferentialV215::test_non_ascii_name_intended_second_line_difference` (2.15.0 `{"src/a.py":[[2,3]]}`, candidate adds `café.py` `[[9,10]]`). Names git still quotes (quotes, backslashes, control characters) and names that are not valid UTF-8 stay unsupported and fail safe: the first two lines stay byte-identical and `REMOVED_LINE_RANGES=` prints empty (unknown), so the moved decision is re-asked (`test_still_quoted_name_first_two_lines_identical_third_empty`, `TestQuotedNamesCR01`, `TestRemovedRiskyInputs`).
- **WR-01 neighbour re-ask (owner: accept and record).** When a moved decision is force-re-asked, another deferred or dismissed decision within 5 lines of the relocated line is also re-asked although its code only shifted. Over-ask only; no `score.py` change. Locked by `TestShape1DeletedOriginal::test_wr01_neighbour_of_forced_reask_is_reasked_owner_accepted` (decision 3 lines away re-asked, 20 lines away kept, both kinds). Mutation: `test_mutant_moved_record_only_trips_the_neighbour_lock` simulates the rejected alternative (stamp only the moved record) in-process by patching `score._nearby_changed` so the forced ranges count only at their exact line, and the lock fails with the neighbour `current`; `test_mutant_a_never_forces_trips_the_neighbour_lock` shows it also fails when the forced pair is never added (all three decisions `current`). 3 passed, 6 subtests.

## 7. Linux CI fix before merge (candidate `07df668d`, 2026-11-19)

**Evidence class: OFFLINE.** The first CI run of PR #13 (Linux, the first time this branch ran outside macOS) failed 2 tests in `test_finalize_parity_grid.py` (16 grid rows) and 7 subtests of `TestOnlyIntendedDifferences`. All of them were grid scenarios where the repo folder name ends in byte 0xff. macOS cannot create that folder, so it never ran locally ("not creatable here").

- **Cause, reproduced in a Linux container (python:3.14).** `closeout_fresh._git` decoded git output with U+FFFD replacement. `git rev-parse --show-toplevel` then named a folder that does not exist, and every deferred or dismissed decision refused `unverifiable`, even after the requested fresh review. That breaks D-16 (every refusal is clearable).
- **Fix.** Decode with `os.fsdecode`, which leaves valid UTF-8 output unchanged. The new test `TestClearableNonUtf8Folder` (unchanged code writes; an edit refuses `line` and the fresh review clears it, both kinds) fails on the old decode and passes on the fix in the Linux container. On macOS it skips, because the filesystem refuses the name.
- **Remaining 7 grid rows.** After the fix, 16 unexpected rows dropped to 7. Each of the 7 was run again with every other folder ending in the Linux container, and every one gives the same result: 2.14.1 opens the card, the helper refuses `unverifiable` (D-09: the session's git cannot see the reviewed work tree). They were added to `FRESHNESS_REFUSALS`, and the exactness test now excuses listed rows that the filesystem cannot create, as the grid already does.
- **Suites on `07df668d`.** Mac: `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider` → 4340 passed, 2 skipped (the new Linux-only tests), 7139 subtests. Linux container, the CI recipe run as a non-root user from a detached worktree with node installed: 4808 passed, 2 failed, 2 skipped. The 2 failures are `test_fixcheck.py` process-group timeout tests. The phase does not touch that code (unchanged since `d5acc19`) and they passed in the real CI run, so they are a container artifact. The real CI run on the pushed commit is the gate.
- `score.py` is unchanged, so the scorer replay result (170 runs, 0 differing) stands.
