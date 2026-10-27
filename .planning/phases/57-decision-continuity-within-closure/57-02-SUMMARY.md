---
phase: 57-decision-continuity-within-closure
plan: 02
subsystem: vibe-check carry-forward decisions (carry_state.py)
tags: [carry_state, evidence, decisions, severity, relocation]
requires:
  - "57-01: test_decision_continuity.py RED fixtures (R1, R3a-refined, R3b, attribution record)"
provides:
  - "carry_state._ORDINARY_COMPARE, _BAND_RANK, gained_lanes, decided (function + CLI)"
  - "direction-aware, line-free, nearby-aware decision_state; stale_cause code|nearby|severity"
  - "attribution saved on every new decision record"
affects: [57-03, 57-04, 57-05, 57-06, 57-07]
tech-stack:
  added: []
  patterns:
    - "ordinary compare split from the stored evidence shape: EVIDENCE_KEYS/_full_evidence unchanged (fail-closed shape check), _ORDINARY_COMPARE is what is compared"
    - "absent nearby_at is omitted from stored evidence (absent == null in the compare), so records without a stamp keep the pre-57 shape"
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_carry_state.py
    - plugins/vibe-check/scripts/test_batch_card.py
    - plugins/vibe-check/scripts/test_card_text.py
decisions:
  - "Stored decision evidence omits nearby_at when it is None (absent and null compare equal), so legacy-shaped records and the existing four-key evidence assertions stay valid"
  - "A non-list attribution (e.g. a dict) is saved as [] on the decision record, never as the dict's keys"
  - "decided refuses with exit 2 like every other carry_state subcommand (the plan text said 1); prose halts on any non-zero exit"
metrics:
  duration: "~9 min"
  completed: 2026-10-26
  tasks: 2
  files: 4
---

# Phase 57 Plan 02: Line-free, direction-aware decision comparator and `decided` read Summary

`carry_state.decision_state` no longer compares the line number for ordinary decisions. It re-asks when the `nearby_at` stamp beneath the flagged line changes. A band drop keeps the decision, and a band rise re-asks only when a reviewer lane that was absent at decision time now reports the finding. Decision records now save `attribution`. The new read-only `carry_state.py decided` subcommand lists the hashes whose decision is current, which is what the relocation prose (57-05) binds.

## What was built

- `_ORDINARY_COMPARE = ("file", "canonical_line_content")` and `_BAND_RANK` (mirror of `score._BAND_SEVERITY` minus `None`; import set still exactly json/os/sys).
- `_evidence_of` returns `nearby_at` (None when absent). `_full_evidence` and `EVIDENCE_KEYS` are unchanged.
- `gained_lanes(record, state)` returns the sorted string lanes in the record's list `attribution` that are missing from the decision's saved list `attribution`. It returns `[]` when either side lacks a list.
- `decision_state` ordinary branch, in order:
  1. A change to the file or canonical line content gives `stale`.
  2. A `nearby_at` mismatch gives `stale`.
  3. A hook comment marks where 57-03 adds the joined check.
  4. Band: an unknown band gives `stale`; a drop or no change gives `current`; a rise gives `stale` only for a legacy record without `attribution` or when `gained_lanes` is non-empty.
  The NV branch is unchanged. A hook comment marks where 57-03 adds inheritance.
- `stale_cause`: ordinary causes are `code`, then `nearby`, then `severity`, with a hook for 57-03's `joined`. The NV branch is unchanged.
- `_check_state` sidecars carry `attribution`. `record_decisions` writes `attribution` from state only. `_DECISION_ENTRY_KEYS` is unchanged, so a payload cannot set it.
- `decided(state)` plus CLI wiring (`SUBCOMMANDS`, `_FLAGS_BY_SUBCOMMAND`, `USAGE`, dispatch, module docstring). Docstring "WHAT CLOSES" rewritten; ROLLBACK paragraph added for the line-free compare.

## Flipped tests (never deleted)

| Old name / assertion | New | Decision |
|---|---|---|
| `test_carry_state.py::TestDecisionEvidence::test_line_move_reopens` (stale/code) | `test_line_move_keeps_decision` (current, cause None) | D-01 |
| `_snapshotless_scenario` "moved" leg (line 75 -> stale/code) | current, not outstanding | D-01 |
| `TestNeedsVerificationDecisionEvidence::test_critical_line_shift_still_stale` | `test_critical_line_shift_keeps_decision` (current) | D-01 |
| `test_batch_card.py::TestRows::test_rows_stale_line_move_cause_code` | `test_rows_line_move_keeps_decision` (line move: row absent; failed relocation, null canonical: cause code) | D-01 |
| `test_card_text.py::code_stale_state` (line move) | failed relocation (null canonical) still renders the "code changed" suffix | D-01 |
| `ROLLBACK_FIXTURES` "line move" row | kept; comment cites D-01 (current reader now agrees with the pre-47 reader) | D-01 |

These fixtures were rise-reopens cases, so each now gets a new `security` lane to stay one under D-05: `band_change_state`, `snapshotless_severity_state`, `test_rows_stale_decision_present_with_tag`, `TestReport._state`, and `test_card_text.severity_stale_state`. `ba_state` gained `attribution=("bugs",)` (it was a non-list dict). In the batch_card successor "own stale decision wins" subtest, the decided band moved from warning to low, so the decision now re-asks on a rise rather than being kept on a drop.

## Mutant ledger

Patched-in contrast mutants. Each must make its scenario raise AssertionError, and each was observed to do so in the test run:

| Mutant | Scenario that fails |
|---|---|
| `line` reintroduced in the compare | `_line_move_scenario` |
| direction-blind band (`cur != was` -> stale) | `_band_drop_scenario` |
| rise ignores gained lanes (any rise -> stale) | `_rise_without_new_lane_scenario` |
| `nearby_at` compare removed | `_nearby_scenario` |
| `decided` lists stale hashes too | `_current_rows_and_members_scenario` |

`grep -c 'subTest("contrast'` went from 7 to 12.

I also edited the source directly (each edit reverted afterwards) and ran `pytest -q test_carry_state.py`:
- adding `line` to `_ORDINARY_COMPARE`: 6 failed
- changing `cur <= was` to `cur == was`: 1 failed
- making every rise stale: 2 failed
- removing the nearby compare: 2 failed
- making the `nearby` cause return `severity`: 3 failed
- not saving `attribution`: 10 failed
- `decided` using `is not None` (with `-k decided`): 2 failed

## Verification (observed)

- `pytest -q test_carry_state.py`: 168 passed, 253 subtests passed. This includes TestImportSet, TestRollbackQuarantine and TestWriterLock.
- Task 1 verify, `test_decision_continuity.py -k "TestSeverityDirection or test_r3_decision_record_saves_attribution"`: 3 passed, 1 failed. The only remaining failure is `test_r3a_rise_with_new_lane_reopens_and_names_it` at `test_decision_continuity.py:523`, `self.assertEqual((row["stale"] or {}).get("gained"), ["security"])` (`None != ['security']`). That is the card `gained` key, which 57-06 owns. Every carry_state assertion before it passes.
- Task 2 verify: `-k "decided or ImportSet or KeyWrites or Allowed or WriterLock or cli"` gave 32 passed. `printf '{"medium_acknowledgments":{},"passes":[]}' | python3 carry_state.py decided` printed `refused: malformed state: passes` on stderr, nothing on stdout, exit=2. `-k decided`: 13 passed.
- `test_batch_card.py test_card_text.py test_finalize_card.py`: 139 passed (after fixture updates). With `test_finalize_gate.py test_fix_loop_card.py` added: 272 passed.
- `test_decision_continuity.py`: 15 failed, 21 passed. R1a, R1b and R1c are now GREEN (via `decided`). R3b, R3a-persistence and the attribution record are GREEN. The REPRO PIN, N1-N6, golden and the `covers` injection lock are still green. Still RED, as expected: R2 (57-04 stamp), the R3a card `gained` assertion (57-06), R4/R5/R6 (57-03/57-04) and R7/wording (57-06).
- Full suite: run as explicit module batches. Every module outside `test_decision_continuity.py` passed: 600 + 901 + 1046 tests across the batches, and the only failures were the 15 still-RED fixtures above. `test_calibrate.py` and `test_replay.py` were not run: the v2.12 holdout-barrier hook blocks commands that reach the sealed holdout folder. Neither module imports carry_state's decision path.
- Grep checks: `def test_line_move_reopens` = 0; `def test_line_move_keeps_decision` = 1, and the next line carries the D-01 comment. `^_ORDINARY_COMPARE = ("file", "canonical_line_content")` = 1, `^_BAND_RANK = ` = 1, `^def gained_lanes` = 1, `"decided"` in carry_state.py = 3, and USAGE mentions `decided`.
- T-57-07: no REASONS string was added or changed.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 0aa704b | line-free, nearby-aware, direction-aware compare; attribution on decisions; flipped tests; mutants |
| 2 | 72eee65 | `decided` read subcommand with fail-closed CLI |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Downstream card suites encoded the old line-move and any-rise rules**
- **Found during:** Task 1
- **Issue:** after the change, 12 tests in `test_batch_card.py` and `test_card_text.py` failed. They used a line move as the "code" stale case and a same-lane rise as the "severity" case. The plan's acceptance requires these suites to stay green.
- **Fix:** line-move cases were flipped with D-01 comments. The code-stale suffix is now produced by a failed relocation (null canonical). The rise fixtures gained a new `security` lane. The successor subtest decided at "low" so that the move is a rise. The round-trip evidence test compares the four EVIDENCE_KEYS and asserts that `nearby_at` is None.
- **Cost if wrong:** if 57-06 expects the old fixture shapes, it has to re-read these fixtures. The suffix strings themselves are unchanged.
- **Files modified:** test_batch_card.py, test_card_text.py
- **Commit:** 0aa704b

**2. [Rule 1 - Bug] Writer-lock and evidence-shape conflicts from `nearby_at`**
- **Found during:** Task 1
- **Issue:** `evidence["nearby_at"] = ...` tripped the AST writer lock (a string-key write in `_evidence_of`). Storing `nearby_at: null` on every decision also changed the persisted record shape that existing exact-record tests pin.
- **Fix:** the dict is now built with `dict(..., nearby_at=...)`. A new `_stored_evidence` omits a None `nearby_at` (absent equals null in the compare) and passes a non-dict result through unchanged, so the existing null-evidence mutant still behaves the same.
- **Cost if wrong:** none for the compare. A reader expecting a `nearby_at` key on every stored record must use `.get`.
- **Commit:** 0aa704b

**3. [Rule 2 - Correctness] A non-list `attribution` saved as `[]`**
- **Found during:** Task 1
- **Issue:** the plan's `list(by_hash[h].get("attribution") or [])` would store the keys of a dict attribution (`["agents"]`). The old `ba_state` fixture used exactly that shape.
- **Fix:** `_attribution_copy` keeps only the str items of a list and returns `[]` for anything else. This is pinned in `test_decision_record_saves_attribution`.
- **Cost if wrong:** a real state with a non-list attribution gets `[]`, so `gained_lanes` reports every current lane on a rise. That fails toward asking.
- **Commit:** 0aa704b

**4. [Rule 1 - Consistency] `decided` refusal exits 2, not 1**
- **Found during:** Task 2
- **Issue:** the plan said "exits 1 like the other read subcommands", but every carry_state refusal (`_refuse`) exits 2.
- **Fix:** kept the module-wide exit 2. The CLI test asserts exit 2, no stdout and a REASONS line, and is named `test_cli_decided_malformed_exits_nonzero_with_reason`.
- **Cost if wrong:** if 57-05's prose checks for exactly exit 1, it must check non-zero instead, as 05-state.md already does for the other subcommands.
- **Commit:** 72eee65

**5. [Rule 1 - Bug] Extra legacy assertions encoding line-move-reopens**
- **Found during:** Task 1
- **Issue:** besides `test_line_move_reopens`, two more tests asserted that a line move goes stale: the snapshotless "moved" leg and `test_critical_line_shift_still_stale`.
- **Fix:** both were flipped with D-01 comments (see the table above). Neither was deleted.
- **Cost if wrong:** none. Both encode D-01 directly.
- **Commit:** 0aa704b

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** record attribution is a list (score.py), so `ba_state` would just gain a parameter. **Actual:** the existing unit fixture used `{"agents": [...]}`. Real score.py output is a list, so the fixture was corrected. **Why:** the fixture predates any reader of `attribution`. **Cost if wrong:** low. Real states use lists (score.py:1860, :2533, :2625).

## Known Stubs

None. The hook comments in `decision_state` and `stale_cause` mark where 57-03 inserts the joined check and inheritance. They contain no placeholder behavior.

## Threat Flags

None. `decided` is a read with no new surface, and T-57-04 through T-57-07 are mitigated as planned.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/carry_state.py, test_carry_state.py, test_batch_card.py, test_card_text.py
- FOUND: 0aa704b, 72eee65
