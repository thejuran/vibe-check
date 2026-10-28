---
phase: 57-decision-continuity-within-closure
plan: 22
subsystem: scoring / decision continuity (D-20 deferred stays open)
tags: [d-20, deferred-stays-open, kept-open, carry_state-deferred, envelope-key, prose-lock, mutants, gap-closure]
requires: ["57-21"]
provides:
  - carry_state.py `deferred` read-only subcommand (refuses malformed state, exit 2)
  - Phase 0.5 `$DEFERRED_HASHES` binding (fail-closed) and envelope key `deferred_hashes`
  - score.py keeps a covered member of a deferred row open under its own hash below threshold
  - section-scoped prose locks + 4 prose mutants; 3 score.py mutants
affects: [57-23]
tech-stack:
  added: []
  patterns: [owner-decision input bound like $DECIDED_HASHES, synthesized kept-open entry gated on deferral]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_carry_state.py
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/scripts/test_nv_render.py
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
    - plugins/vibe-check/scripts/test_score.py
decisions:
  - "57-22: score.py learns the owner's deferrals only from envelope key `deferred_hashes` (bound by `carry_state.py deferred`); an envelope without it scores byte-identically"
  - "57-22: a deferred covered member below threshold is a kept-open row under its own hash at the deferred row's stored band, stamped as carried so the split pass's nearby edit makes the inherited deferral stale (D-20 with D-17); a dismissed one still drops"
  - "57-22: the drop list is gated on the synthesized entry (one extend over carried_obligations), so removing the entry loses the member instead of crashing"
metrics:
  duration: ~35min
  completed: 2026-10-27
  tasks: 3
  files: 8
---

# Phase 57 Plan 22: Deferred findings stay open below threshold (D-20) Summary

A finding the owner deferred can no longer disappear on a score. The owner's deferrals now travel to the scorer: `carry_state.py deferred` reads them, Phase 0.5 binds them as `$DEFERRED_HASHES` and stops the run if the read fails, and the envelope forwards them as `deferred_hashes`. When a covered member of a deferred row splits out below threshold, score.py keeps it as a kept-open row under its own hash. The split pass's edit stamps that row, so the inherited deferral reads stale with cause nearby, the finding counts as outstanding, and Finalize blocks until the owner decides it. Dismissed findings below threshold still drop, as intended.

## carry_state read

- `deferred(state)` sits directly after `decided`. It returns the sorted `decisions` keys whose record is a defer, current or stale. It returns `[]` when there is no `decisions` family and `None` when the state is malformed (same `_check_state` refusal as `decided`). It is read-only.
- Registered in SUBCOMMANDS, `_FLAGS_BY_SUBCOMMAND` (no flags), USAGE (`| decided | deferred`), dispatch, the docstring's WHAT IT DECIDES table and the CLI block. No write path added: `grep -c "record_decisions\|record_fix_verdicts"` is 4, the same as at HEAD.
- Tests: "deferred" was added to both CLI malformed loops and to the usage-error argv list (`["deferred", "--head-blobs", "x"]`). New `TestDeferred` has 7 tests: lists current and stale defers, excludes dismiss, lists a legacy defer without evidence, is empty with no decisions, returns None on malformed state, does not mutate, and round-trips on the CLI. `decided_state()` gained an optional `kinds` map, which defaults to dismiss, so existing callers behave the same.
- A kind-gate mutant (`== "defer"` -> `in ("defer", "dismiss")`) failed test_deferred_excludes_dismiss, test_deferred_lists_current_and_stale_defers and the CLI round trip (3 failed). The file was restored afterwards.

## Prose binding and locks

- 05-state.md `decisions` bullet: a continuation paragraph and a second fenced bash block in the same if/else halt shape now bind `$DEFERRED_HASHES` from `carry_state.py" deferred < "$STATE_FILE"`. The added text includes the "Never bind `[]` on failure: an empty list lets a deferred finding that scores below threshold vanish" sentence. Every existing sentence is byte-identical.
- 30-collect-score.md step 4, CARRY-01 bullet: adds the `deferred_hashes` = `$DEFERRED_HASHES` sentence (D-20, "a kept-open row, never a drop"). The one rewritten line is the bullet line itself; its closing sentence now reads "These keys feed only the verdict guard and the D-20 keep-open — they never feed `stable_hash` or the score formula." `git diff -U0 | grep -c '^-[^-]'` returned 1.
- test_nv_render.py adds:
  - `DEFERRED_BINDING_PHRASES` / `deferred_binding_holds`, checked inside the STATE section.
  - `ENVELOPE_DEFERRED_*` / `envelope_deferred_holds`, checked inside the CARRY-01 bullet.
  - CASES entries for both.
  - 7 tests: test_deferred_binding_holds, test_deferred_binding_one_helper_call, test_envelope_deferred_holds, test_deferred_binding_deleting_mutant, test_deferred_binding_in_bullet_deleting_mutant, test_deferred_binding_empty_on_failure_inserting_mutant and test_envelope_deferred_in_bullet_deleting_mutant.
- Counts: `grep -c DEFERRED_HASHES` gives 05-state.md 4 and 30-collect-score.md 1. `grep -c 'exit 1' 05-state.md` gives 3.

## score.py keep-open

- Envelope: `raw_deferred = envelope.get("deferred_hashes", [])` becomes a frozenset of its str items, or an empty frozenset for a non-list. It never raises.
- Carry loop: `deferred_covered[id(p)] = {"covering": stored_hash, "band": cf.get("band")}` for an expanded member with no obligation whose row's stored hash is deferred. The condition contains the anchor `and stored_hash in deferred_hashes`.
- Group loop tail: `survivor_sources` now carries `(members, {id(m): capped})`, and the threshold loop unpacks it.
- New pure `_covered_entry(m, cov, capped)` returns an obligation with the member's own `_current_hash`, this pass's capped score, the deferred row's band, its own lane and `snapshot: None`, marked `covered: True`.
- Sub-threshold branch: each source in `deferred_covered` gets `carried_obligations[id(m)] = _covered_entry(...)` (on one line). One `dropped.extend` over the members in `carried_obligations` then gives a covered member the reason `"sub-threshold; deferred-by: <hB>"` and everything else `"sub-threshold"`.
- `_kept_open_rows`: `_snapshot_for(row, pass_number, nearby=row_nearby,` / `carried=bool(entry.get("covered")))`, and the docstring now covers the D-20 case. `_snapshot_for(.*nearby=` count is 6.
- Observed pass-2 row for hA: stable_hash hA, band warning, orchestrator_score 65, status needs-recheck, `kept_open` "sub-threshold; deferred-by: 3449f4b5…", snapshot `nearby_at: 2`.
- Acceptance greps: `envelope.get("deferred_hashes"` 1; `deferred_covered` 7; kind-gate anchor 1; `def _covered_entry` 1; entry anchor 1; carried anchor 1; `sub-threshold; deferred-by: ` 1. The AST import set is ['hashlib', 'json', 're', 'sys'], with no os or pathlib.
- stable_hash, GOLDEN_DIGEST, carry_state's write paths and score.py's imports are unchanged.

## Mutant ledger

Each D-20 mutant was run through `TestPhase57Mutants._run_mutant`, and the observed failures were collected by a separate ledger run over `_ROW_TESTS`:

| Mutant | Replacement | Tripped (observed) | Stayed green |
|--------|-------------|--------------------|--------------|
| kind gate | `and stored_hash in deferred_hashes` -> `and True` | test_dismissed_: findings `[]` assertion — "Lists differ … First list contains 1 additional elements" (a dismissed member is kept open) | test_deferred_ and every other row test |
| synthesized entry | `carried_obligations[id(m)] = _covered_entry(` -> `pass  # (` | test_deferred_: "unexpectedly None : record 845f88b7 is not an open record (decision orphaned)" | test_dismissed_, test_s1_ |
| carried stamp | `carried=bool(entry.get("covered"))` -> `carried=False` | test_deferred_: decision_state assertion with message "snapshot {'at_pass': 2, … 'band': 'warning'}" (no `nearby_at`, so it reads current, not stale) | test_dismissed_, test_p3_ |

`_ROW_TESTS` gained (TestDeferredStaysOpen, test_deferred_covered_member_below_threshold_stays_open) and (TestDeferredStaysOpen, test_dismissed_covered_member_below_threshold_may_drop).

## Verification

- `pytest -q test_carry_state.py` → `226 passed, 300 subtests passed in 2.61s`; `-k ImportSet` → `3 passed, 223 deselected`
- CLI checks:
  - `printf 'not json' | carry_state.py deferred` → stderr "refused: state is not valid JSON", exit 2.
  - `deferred --head-blobs x` → usage, exit 2.
  - `deferred_state()` piped in → `["bbbb…", "cccc…"]`, exit 0.
- `pytest -q test_nv_render.py` → `36 passed, 103 subtests passed in 0.09s`
- `pytest -q test_decision_continuity.py` → `86 passed, 90 subtests passed in 0.36s` (TestDeferredStaysOpen 5 passed; the 57-20 D-20 red is green and the dismiss lock is green)
- `pytest -q test_score.py -k "TestNearbyAt or TestPhase57Mutants or TestObligationPreservingDedup or ImportSet or Golden or TestStatusScrubbedOnNewFindings or TestOutputShape"` → `43 passed, 457 deselected, 24 subtests passed`
- `pytest -q test_replay.py -k TestDiffMode` → `16 passed, 48 deselected`
- golden (test_decision_continuity -k Golden) → `1 passed`
- Full `pytest -q` → **`3311 passed, 4381 subtests passed in 196.21s`**: 0 failed, 0 SUBFAILED. The baseline was 3290 passed / 1 failed.
- Fixture flips: with `run_pass` now forwarding `deferred_hashes`, the only outcome that changed is TestDeferredStaysOpen::test_deferred_covered_member_below_threshold_stays_open (red to green, the D-20 behaviour). Every other pre-existing test was green before and is green after, TestPhase57EndToEnd included, so no journey assertion was touched.
- Tests added (20):
  - Task 1 (7): TestDeferred × 7.
  - Task 2 (7): the 7 test_nv_render tests listed above.
  - Task 3 (6):
    - test_deferred_kept_open_row_shape
    - test_deferred_kept_open_row_persists_on_the_next_pass
    - test_envelope_without_deferred_hashes_scores_as_before
    - test_deferral_kind_gate_keeps_a_dismissed_member_open
    - test_no_synthesized_entry_drops_the_deferred_member
    - test_kept_open_covered_row_without_carried_is_not_stamped

## Commits

- 70e0719 feat(57-22): carry_state deferred read lists the owner's deferrals
- 6626edb feat(57-22): bind $DEFERRED_HASHES fail-closed and forward deferred_hashes
- 92b135d feat(57-22): keep a deferred covered member open below threshold

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The existing decided "Never bind" inserting mutant stopped tripping**
- **Found during:** Task 2
- **Issue:** The new deferred paragraph adds a second "Never bind `[]` on failure" in the same bullet. `test_state_binding_empty_on_failure_inserting_mutant` changes only the first occurrence, so the second one kept `state_binding_holds` green and the mutant no longer tripped (observed failure: `True is not false`).
- **Fix:**
  - The STATE_BINDING_PHRASES entry and that mutant now target the decided-specific sentence "Never bind `[]` on failure: an empty list silently reverts".
  - DEFERRED_BINDING_PHRASES gains "Never bind `[]` on failure: an empty list lets a deferred", so the plan's deferred inserting mutant can trip. Without it, the remaining phrase "lets a deferred finding … vanish" would survive that replacement.
- **Cost if wrong:** One prose lock phrase is now longer. If the decided sentence is reworded later, that lock must be updated with it.
- **Files modified:** test_nv_render.py
- **Commit:** 6626edb

**2. [Rule 3 - Blocking] m57-04 mutant anchor broken by the planned snapshot-call split**
- **Found during:** Task 3
- **Issue:** The plan's own step 5 splits `_snapshot_for(row, pass_number, nearby=row_nearby)` across two lines. test_score.py's `test_m57_04_kept_open_stamp_removed` anchored the whole one-line call and failed with "mutation target not unique" (0 != 1).
- **Fix:** Re-anchored it to the first line, `...nearby=row_nearby,` -> `...nearby=False,`. The mutant tests the same behaviour and passes. As a result, test_score.py is an eighth modified file beyond the plan's list of seven.
- **Cost if wrong:** None. The mutant tests the same stamp and still trips.
- **Files modified:** test_score.py
- **Commit:** 92b135d

**3. [Rule 1 - Bug] The planned drop structure made the entry mutant crash instead of fail**
- **Found during:** Task 3
- **Issue:** As planned, the separate `dropped.append` after the entry assignment meant the `pass  # (` mutant left a dropped member with no entry. `_kept_open_rows` then raised KeyError, and `_run_mutant` asserts no errors.
- **Fix:** The loop now only assigns the entry. A single `dropped.extend` over members in `carried_obligations` picks the reason per member. With the entry removed, the member simply drops (the real WR-02 defect).
- **Cost if wrong:** Low. The drop order within a group is now source order rather than covered-first. Reasons and rows are the same.
- **Files modified:** score.py
- **Commit:** 92b135d

### Plan inconsistencies resolved

- The acceptance criterion `printf '{"medium_acknowledgments":{},"passes":[]}' | carry_state.py deferred` exits 0 contradicts the behaviour spec, which requires the same `_check_state` refusal as `decided`. The existing test `test_cli_decided_malformed_exits_nonzero_with_reason` uses exactly that state and expects exit 2. I followed the behaviour spec: observed exit 2, "refused: malformed state: passes". Pass 1 never runs the helper (no state file), so this has no runtime effect.
- The plan expected `grep -c "def test_deferred_binding_\|def test_envelope_deferred_"` == 6 but itself lists 7 tests. The observed count is 7.
- TestDeferredStaysOpen has 5 tests, not 4: test_deferred_kept_open_row_shape was added to pin the row's band, score and reason exactly.

## Known residual (not fixed; scope)

- A deferred covered member removed by the **min_confidence** filter (rather than the sub-threshold drop) is not synthesized. The plan scopes D-20 to the threshold branch, and min_confidence is opt-in and off by default. This is recorded here for 57-23 review. Under the scope rule it does not justify new work unless reproduced.

## Threat Flags

None. No new network, file or auth surface. `deferred_hashes` is coerced and never raises (T-57-72), and an envelope without the key synthesizes nothing (T-57-76, test_envelope_without_deferred_hashes_scores_as_before).

## Self-Check: PASSED

- Files: all 8 modified files exist and are committed.
- Commits: 70e0719, 6626edb and 92b135d were found in `git log`.
