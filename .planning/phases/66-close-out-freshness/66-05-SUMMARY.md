---
phase: 66-close-out-freshness
plan: 05
subsystem: review-prose / worktree snapshot
tags: [all-mode, reviewed_tree, worktree_snap, prose-lock]
requires: []
provides:
  - "--all route takes (00-scope-all.md step f) and collects (default fence) the working-tree snapshot, so its pass entry records reviewed_tree"
  - "explicit envelope rule: --all never sends nearby_line_ranges"
affects:
  - 66-03 / 66-04 Close-out freshness check (can now verify --all passes instead of refusing them as unverifiable)
tech-stack:
  added: []
  patterns: ["prose fence read from the .md and run in fresh bash -s shells (real chain)"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/00-scope-all.md
    - plugins/vibe-check/phases/review/00-scope.md
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/phases/review/45-persist.md
    - plugins/vibe-check/phases/review/45-persist-all.md
    - plugins/vibe-check/scripts/fixtures/future-schema.json
    - plugins/vibe-check/scripts/test_worktree_snap.py
decisions:
  - "--all reuses the DEFAULT collect fence (no range / PR-head argument), so 30-collect-score.md keeps exactly three collect fences"
  - "The --all take is a new step f in 00-scope-all.md, after $REVIEW_SET is final and before anything is dispatched"
metrics:
  duration: ~30m
  completed: 2026-11-17
  tasks: 2
  files: 7
---

# Phase 66 Plan 05: --all records reviewed_tree Summary

`--all` reviews now take the mode-1 working-tree snapshot in Phase 0 and run the default `worktree_snap.py collect` fence in Phase 3, so every `--all` pass entry can carry `reviewed_tree` like every other route; the scorer envelope on `--all` still never carries `nearby_line_ranges`.

## What changed

- **00-scope-all.md** — new step f: the exact mode-1 take fence, the `REVIEWED_SNAPSHOT=` carry rule, and "Skip it on `--finalize` (`FINALIZE_MODE=1`)" (no `--all` skip on the `--all` route itself).
- **00-scope.md** — the four take paragraphs (default, PR, range, GSD) drop "and `--all`"; the default one points to 00-scope-all.md for the `--all` snapshot. The `--finalize` skip is unchanged.
- **30-collect-score.md** — the `--all` table row now skips only the range fence; the since-review heading reads "every route, including `--all`"; `--all` reuses the default collect fence (still 3 fences); the "skips this call" sentence is replaced; step 4 states `--all` never sends `nearby_line_ranges`.
- **45-persist.md / 45-persist-all.md** — `reviewed_tree` is optional on every route; 45-persist-all.md says it is the shared optional key, not an `--all`-only key.
- **future-schema.json** — history note in `_purpose` only; `pass_optional` / `pass_all_only` structurally unchanged.
- **test_worktree_snap.py** — lock renamed to `test_every_snapshot_call_states_the_finalize_skip` (now also covers the 00-scope-all take and its position after `$REVIEW_SET`); new `test_all_route_never_sends_nearby_line_ranges`; `test_persist_names_reviewed_tree` rejects the old `--all` exclusions; new `TestAllRoute.test_all_route_records_reviewed_tree` runs the real `--all` take + default collect fences in fresh shells on a repo with an uncommitted block, and checks the recorded tree matches `OBJECT_ID_RE`, differs from `HEAD^{tree}`, reads as `tree` through the vibe-check store, passes the future schema with `all_mode=True`, and that the captured scorer envelope (pass 1 and a pass 2 where collect printed `{}`) has no `nearby_line_ranges`.

## Verification (observed)

- Task 1 verify (with `grep -F`, see deviation 1): `VERIFY_OK`; `grep -c 'worktree_snap.py" collect' 30-collect-score.md` = 3.
- RED: the new/updated tests run against the base prose (per-file checkout of e6201539, then restored): 9 failed, 4 passed.
- Mutants: removing `(FINALIZE_MODE=1)` from the 00-scope-all paragraph and removing the `--all` no-nearby sentence each tripped their lock (2 failed); prose restored afterward.
- Task 2 verify: `pytest -q -p no:cacheprovider test_worktree_snap.py -k "all_route or TestProse or schema_allows_reviewed_tree"` → 8 passed, 9 subtests passed.
- Whole file: `pytest -q test_worktree_snap.py` → 67 passed, 22 subtests passed.
- No scorer effect: `pytest -q test_decision_continuity.py -k "999_28 or Uncommitted or NearbyEdit or ReReview"` → 6 passed.
- Acceptance greps: `def test_all_route_records_reviewed_tree` = 1, `def test_all_route_never_sends_nearby_line_ranges` = 1, old lock name = 0, removed `def test_` lines in the diff = 1.
- Full scripts suite (`pytest -q` in plugins/vibe-check/scripts): 5 failed, 4126 passed, 1 skipped, 6204 subtests passed. All 5 failures are in `test_replay.py::TestPhase53SameLineRegressionCases` (replayed runs `runs-v2.10-phase43/first/should-quiet-4/run-3` and `.../triggarr-secret-in-logs/run-1` score `('critical', 100)` where `('warning', 94)` is expected). Out of scope for this plan: `test_replay.py` reads none of the seven files changed here and `score.py` is untouched. See Deferred Issues.

## Deviations from Plan

**1. [Rule 3 - Blocking] Task 1 verify command uses a BRE grep that cannot match on macOS**
- **Found during:** Task 1
- **Issue:** `grep -c 'worktree_snap.py" take --root "$GREPO"'` treats the mid-pattern `$` as an anchor under BSD grep, so it prints 0 even on 00-scope.md, which already held that fence.
- **Fix:** ran the same check with `grep -Fc`; no prose change. Also ran the verify from the worktree, not the main-checkout path the plan names.
- **Cost if wrong:** none for the product; a later verifier re-running the literal command would see a false failure.
- **Commit:** none (verification only)

**2. [Rule 1 - Bug] New collect note shadowed the range and PR fence lookups**
- **Found during:** Task 2
- **Issue:** the Task 1 sentence "no `--range`, no `--pr-head`" put the first literal occurrence of those flags above the range and PR collect fences, so `test_collect_fence_is_one_call_with_state_file` (which finds a fence by its first needle) picked the wrong text.
- **Fix:** reworded to "with no range or PR-head argument".
- **Cost if wrong:** low; wording only.
- **Files modified:** plugins/vibe-check/phases/review/30-collect-score.md
- **Commit:** 04e7136b

**3. [Rule 1 - Bug] Paragraph extraction at end of file**
- **Found during:** Task 2
- **Issue:** the new 00-scope-all step f is the last paragraph of the file, so the lock's `text.index("\n\n", at)` raised.
- **Fix:** the lock reads to end of file when no blank line follows.
- **Commit:** 2bd4d024

## TDD Gate Compliance

Task 2 was `tdd="true"`, but the plan orders the prose (Task 1, `feat`) before the tests (Task 2, `test`), so the git order is feat → fix → test rather than test → feat. RED was shown instead by running the new tests against the base prose (9 failed) and by the two mutants above.

## Deferred Issues

- `test_replay.py::TestPhase53SameLineRegressionCases` (5 failures, described under Verification). Not caused by this plan and not investigated. Whether it also fails on the base commit was not checked separately. It is recorded here, not in `deferred-items.md`, so parallel worktree agents do not collide on that file; the orchestrator should copy it there.

## Known Stubs

None.

## Commits

- ee288c4e feat(66-05): take, collect and persist reviewed_tree on the --all route
- 04e7136b fix(66-05): keep the --all collect note from shadowing the range and PR fence lookups
- 2bd4d024 test(66-05): lock the --all snapshot route and prove it records reviewed_tree

## Self-Check: PASSED

Commits ee288c4e, 04e7136b, 2bd4d024 exist; 00-scope-all.md, test_worktree_snap.py and this SUMMARY exist.
