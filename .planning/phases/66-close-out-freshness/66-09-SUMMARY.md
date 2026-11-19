---
phase: 66-close-out-freshness
plan: 09
status: complete
subsystem: release evidence / Finalize differential
tags: [replay, differential, release-evidence, GATE-07, GATE-08]
requires:
  - "66-06, 66-08"
provides:
  - "TestOnlyIntendedDifferences: two-sided Finalize differential vs d5acc19 (INTENDED refusals, REPAIRED shape 2, SCORER_CHANGES)"
  - "66-REPLAY.md: offline replay + suite evidence on candidate cf1ea0bd"
  - "finalize_capture.reviewed_folder / stamp_reviewed_tree: lean-v2.15 candidate walks run on a reviewed tree"
affects:
  - "Milestone audit: FRESH-03 not fully satisfied offline (999.44 shape 1 is an owner-accepted known limit)"
tech-stack:
  added: []
  patterns: ["decision-bearing walk = git work tree with every finding file committed + last-pass reviewed_tree stamped"]
key-files:
  created:
    - .planning/phases/66-close-out-freshness/66-REPLAY.md
  modified:
    - plugins/vibe-check/scripts/test_closeout_fresh.py
    - .github/scripts/test_stdlib_only.py
    - docs/design/lean-v2.15/tools/finalize_capture.py
    - docs/design/lean-v2.15/tools/test_finalize_capture.py
    - .planning/ROADMAP.md
    - .planning/phases/66-close-out-freshness/66-VALIDATION.md
decisions:
  - "Option A (orchestrator, technical call): lean-v2.15 Finalize capture situations are re-homed onto a reviewed git tree rather than marking their refusals as expected (option B rejected; it would drop write-route coverage)"
  - "999.44 closing line takes the known-limit branch: shape 1 owner-accepted known limit, FRESH-03 gate item NOT fully satisfied offline, carried to the milestone audit"
metrics:
  completed: 2026-11-18
  tasks: "2 of 2"
  candidate_commit: cf1ea0bde6ad86cc1fae798d730d3b2d1c7fadb8
---

# Phase 66 Plan 09: Replay and Finalize differential vs 2.15.0 Summary

On candidate **cf1ea0bd**, the only differences from 2.15.0 are named ones. The scorer replay compared 170 runs with 0 differences. The Finalize differential made 312 fixture runs. Its only differences are 76 named freshness refusals and 2 differences from the owner-approved shape 2 repair, and each is checked in both directions. The full offline suite passed (4706 passed, 2 xfailed, exit 0). The stdlib check passed (35 files). All evidence is offline. 999.44 is recorded truthfully: shape 1 is an owner-accepted known limit, so the **FRESH-03 gate item is NOT fully satisfied offline**.

## Commits

| Commit | Message |
|---|---|
| 25bcbbb1 | test(66-09): Finalize differential — only intended refusals differ from 2.15.0 |
| 30517e4f | fix(66-09): count closeout_fresh.py in the shipped stdlib-only file pin |
| cf1ea0bd | test(66-09): put lean-v2.15 Finalize capture situations on a reviewed tree (D-09) |
| d53bb5dd | docs(66): replay vs 2.15.0, suite evidence and backlog outcomes |

## Task 1: only_intended differential (25bcbbb1)

`TestOnlyIntendedDifferences` in `test_closeout_fresh.py`:
- `INTENDED` has 76 entries: 6 for 999.40 (exact/nearby/untracked × defer/dismiss), 2 for shape 3 untracked, 12 result-fixture and 56 parity-grid D-09 refusals.
- `REPAIRED` has 2 entries: shape 2 `older_first` for both kinds (75e4a1da).
- `SCORER_CHANGES = ()`.

Observed on cf1ea0bd: `-k only_intended` gave 3 passed, 390 subtests (312 fixture runs plus 78 list-exhaustiveness checks).

## Task 2: replay, suite, records

All on cf1ea0bd, clean tree, observed:
- Scorer replay `replay.py diff --base rev:d5acc19`: 170 compared, 0 differing, exit 0. score.py sha256 is identical to 2.15.0. An earlier run on 25bcbbb1 also gave 170/0.
- Full suite `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`: **4706 passed, 2 xfailed, 2 warnings, 7173 subtests, 652.79 s, exit 0**. The 2 xfails are the shape 1 known-limit tests. The parity grid had 284 scenarios: 198 agree, 12 D-19, 56 D-09 refusals, 0 unexpected, 18 not creatable here.
- Stdlib check: 35 shipped .py files, no third-party imports, exit 0.
- lean-v2.15 `finalize_capture.py verify` against the committed 2.14.1 record: matches (5 situations), exit 0. `compare --driver helper`: outcome fields match (5 situations, 7 walks), exit 0.
- ROADMAP §999.40 now has a repair note (candidate cf1ea0bd). §999.44 has the three Shape outcome lines and exactly one closing line. That line names shape 1 as an owner-accepted known limit and says "FRESH-03 gate item NOT fully satisfied offline; carried to the milestone audit".
- 66-VALIDATION.md has no pending rows. The shape 1 row is ❌. `nyquist_compliant` and `wave_0_complete` stay false. The evidence class is OFFLINE.

## Known behaviour (recorded, not a defect)

On `--all`, an edit near a decided line, but not on it, makes Close out refuse once. The fresh `--all` re-review then keeps the decision without re-asking, because that route sends no nearby ranges (D-12), so the next Close out writes. An edit on the decided line itself is re-asked. This is pinned by `TestAllRouteClearable.test_all_route_refuses_then_clears` (66-06) and recorded in 66-VALIDATION.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The stdlib-only file-count pin did not count closeout_fresh.py**
- **Found during:** Task 2 (full suite on 25bcbbb1)
- **Issue:** `.github/scripts/test_stdlib_only.py` pinned the shipped file count from before `closeout_fresh.py` was added. That caused 2 failures.
- **Fix:** the pin now counts 35 files.
- **Cost if wrong:** low. A wrong count only makes the pin test fail, and the stdlib check itself passed independently.
- **Files modified:** .github/scripts/test_stdlib_only.py
- **Commit:** 30517e4f

**2. [Rule 3 - Blocking] lean-v2.15 Finalize capture situations re-homed onto a reviewed tree (orchestrator option A)**
- **Found during:** Task 2 (full suite on 25bcbbb1). There were 2 failures and 23 errors in `docs/design/lean-v2.15/tools/test_finalize_capture.py`.
- **Issue:** the capture situations carry v2.14.1 dismissals, but their work folder had no reviewed baseline. The candidate helper correctly failed closed (D-09) with "a deferred or dismissed decision is stale", where the situations expect `write`.
- **Fix:** `HelperWalk.prepare` and the two candidate screen-text walks now call:
  - new `reviewed_folder()`, which uses the existing `prepare_git_folder` / `--separate-git-dir` helper to commit every file a fixture finding names, plus the `head_blobs` files;
  - new `stamp_reviewed_tree()`, which sets the last pass's `reviewed_tree` to `HEAD^{tree}`. `head_sha` is not touched.

  The 2.14.1 walk is unchanged. No assertion was weakened or deleted, and no refusal was marked as expected. Two tests were added:
  - `test_every_walk_runs_on_a_reviewed_tree` checks that every walk runs on a reviewed tree.
  - `test_mutant_without_the_reviewed_tree_stamp_refuses` patches out the stamp, and clean-close then raises the stale refusal. This proves the stamp matters.
- **Result:** the re-home restored `write` with identical outcome fields. `compare` exits 0 and `verify` against the committed 2.14.1 record exits 0. No committed record changed, so no record-update commit was needed. `test_finalize_capture.py`: 112 passed.
- **Cost if wrong:** low to medium. If a later Finalize change needs a file that no finding names to be in the reviewed tree, these walks would refuse again and show up as test failures, not as silent passes.
- **Files modified:** docs/design/lean-v2.15/tools/finalize_capture.py, docs/design/lean-v2.15/tools/test_finalize_capture.py
- **Commit:** cf1ea0bd

**3. [Rule 1 - Bug] Intended-refusal count in the carried docs draft**
- **Found during:** Task 2 records
- **Issue:** the scratch VALIDATION draft said "80 named refusals". `len(INTENDED)` is 76 (56 + 12 + 6 + 2).
- **Fix:** 66-VALIDATION.md and 66-REPLAY.md now say 76.
- **Cost if wrong:** none for behaviour. This is a records accuracy fix only.
- **Commit:** d53bb5dd

## Assumption Drift (advisory)

- **Found during:** Task 2
- **Planned:** the plan's suite list did not expect `docs/design/lean-v2.15/tools` to need any change. This plan was supposed to add no new behaviour.
- **Actual:** the lean-v2.15 capture fixtures also depended on a "no reviewed baseline still writes" assumption, the same one 66-02 removed from the plugin fixtures.
- **Why:** D-09 fails closed on a missing baseline.
- **Cost if wrong:** low. The fix is test-harness only, and outcome parity with the 2.14.1 record is proven.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: .planning/phases/66-close-out-freshness/66-REPLAY.md
- FOUND: commits 25bcbbb1, 30517e4f, cf1ea0bd, d53bb5dd
