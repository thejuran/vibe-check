---
phase: 57-decision-continuity-within-closure
plan: 03
subsystem: vibe-check carry-forward decisions (carry_state.py)
tags: [carry_state, coverage, regrouping, decisions]
requires:
  - "57-02: line-free, direction-aware comparator; attribution on decisions; decided read"
provides:
  - "covers on every new decision record (agent, file, title, code), written from state only"
  - "carry_state.newcomer_lanes / covered_count: the only readers of covers for the card (57-06)"
  - "joined stale cause for a decided row that gains a newcomer concern"
  - "carry_state.covering_decision: the one explicit inheritance path (split member keeps its decision)"
affects: [57-04, 57-06, 57-07]
tech-stack:
  added: []
  patterns:
    - "coverage identity = (agent, file, title), never a member's computed hash"
    - "guard mutants patch a small predicate (_covers_entry_matches, _covered_identities) with a relaxed input so the real code runs under the mutant"
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/carry_state.py
    - plugins/vibe-check/scripts/test_carry_state.py
decisions:
  - "covers lists one entry per (agent, file, title): the lead's own member record is the lead and is not listed twice (57-01 R4 fixture)"
  - "covered_count = 1 + covered members with an identity other than the lead's, so a lone decided row counts 1 even though score.py lists the lead in members[]"
  - "Same-title corroboration from another lane is not a joined newcomer; it re-asks only through the band-rise rule"
  - "An absorbed member record (absorbed_into) never inherits through covers; only a record that is its own row can"
metrics:
  duration: "~25 min"
  completed: 2026-10-26
  tasks: 2
  files: 2
---

# Phase 57 Plan 03: Decision coverage, joined reopen and split inheritance Summary

Every new decision now records which findings it covered (`covers`). A decided row that later picks up a different reviewer's new concern reopens once, with cause `joined`. A finding the decision covered that later becomes a row of its own keeps the decision while its own code line is unchanged.

**For the owner, in plain terms:** if a second reviewer repeats the same concern on a row you already decided, you are not asked again unless the severity rose and a new reviewer is behind the rise. If a reviewer raises a different concern at the same spot, the row always comes back to you, with your earlier decision shown.

## What was built

- **`covers` on decision records** (`_covers_of`). `record_decisions` writes `covers` from the state only; the payload key set is still exact, so a payload cannot set it. The decided record comes first, with its `canonical_line_content` as `code`. Each member follows, with the first non-blank line of its `current_code`, stripped, as `code` (None when there is none). Entries are de-duplicated by (agent, file, title), so the lead's own member record is not listed a second time. An older record is never rewritten.
- **`newcomer_lanes(record, state)`** (public). This is the one definition of a D-08 newcomer: a member with no obligation of its own, whose (agent, file, title) is not in `covers`, and whose title is not a covered title. It returns `[]` when there is no own decision or the decision has no `covers` (legacy). `_joined_newcomer` is exactly `return bool(newcomer_lanes(record, state))`.
- **`covered_count(record, state)`** (public). This is the D-10 count the card prints: 1 for the lead, plus each covered member whose identity differs from the lead's. It is 0 for no decision or a legacy decision. It is built on the same `_covered_identities` helper as `newcomer_lanes`.
- **`decision_state` / `stale_cause`:** `joined` sits between `nearby` and the band step, so the cause priority is code, then nearby, then joined, then severity.
- **`covering_decision(record, state)`** (public). It returns `(decided_hash, decision)` for another decision whose `covers` has an entry with the same agent, file and title as the record, and whose non-empty `code` equals the record's canonical line (both stripped). It takes the first match in sorted-hash order. It never matches across files or from an entry without code, never matches a legacy decision without `covers`, and never matches an absorbed member record. `decision_state` uses it only when the record has no decision of its own. The result is "current", or "stale" (cause `nearby`) when the record's `snapshot.nearby_at` is later than the covering decision's `at_pass`.
- **Routing:** `finalize_counts`, `pending`, `is_closed` and `decided` all route through `decision_state` via `_closed`. No change was needed, and the inheritance test asserts all four.
- **Docstrings:** "WHAT CLOSES" now describes `covers`, the joined rule and the corroboration exception. "never inherited from a lead" is replaced by the one explicit inheritance path. The ROLLBACK paragraph now covers `covers`: a pre-57 reader ignores it, so a split covered member is asked again, which fails toward asking.

## Fixtures turned green

- `test_r4_new_weaker_concern_on_decided_row_is_asked`: green end to end, including the card `stale["cause"] == "joined"` assertion. batch_card already reads `stale_cause`.
- `test_r4_covers_frozen_at_decision_time`: green.
- `test_r6_split_member_inherits_decision`: green, including the card exclusion and gate `write`.
- `test_r6_split_member_whose_code_changed_is_asked`: still green.
- TestLineShift R1a/R1b/R1c: green (already green after 57-02; re-confirmed).

## Mutant ledger

`grep -c 'subTest("contrast' test_carry_state.py`: 12 before this plan, 20 after (+8). Each mutant was observed to make its scenario raise AssertionError.

| Mutant | Scenario(s) that fail |
|---|---|
| `_joined_newcomer` always False | `_joined_scenario` |
| title exclusion removed (`_covered_identities` titles emptied) | `_same_title_scenario` |
| `newcomer_lanes` always `[]` | `_joined_scenario` AND `_newcomer_lanes_scenario` |
| `_covered_identities` returns empty sets | `_covered_count_scenario` AND `_same_title_scenario` |
| `covering_decision` always None | `_inherits_scenario` |
| code-match removed (`_covers_entry_matches` with entry code = record canonical) | `_changed_code_scenario` |
| file check removed | `_cross_file_scenario` |
| agent check removed | `_other_agent_scenario` |

## Verification (observed)

- `pytest -q test_carry_state.py`: 197 passed, 266 subtests passed. This includes TestImportSet, TestWriterLock (`covers` lives inside `decisions`), TestRollbackQuarantine and TestReasonsSealed.
- Task 1 verify, `-k test_r4`: 2 passed.
- Task 2 verify, `-k "test_r6 or test_r4 or TestSeverityDirection or TestLineShift"`: 11 passed, 1 failed. The failure is `test_r3a_rise_with_new_lane_reopens_and_names_it` at `test_decision_continuity.py:523`, `None != ['security']`. That is the card `gained` key, which 57-06 owns, and it was already red after 57-02.
- Grep checks:
  - the five new defs: 5
  - `return bool(newcomer_lanes(record, state))`: 1
  - `_covered_identities(`: 3
  - `^def covering_decision`: 1
  - "never inherited from a lead": 0
- `test_decision_continuity.py`: 12 failed (was 15 after 57-02). Still red, as expected:
  - R2 nearby stamp (57-04)
  - R5 dedup obligation (57-04)
  - R3a card `gained` (57-06)
  - R7 / nearby / joined D-10 card wording and compact forms (57-06)
- Full suite: every `test_*.py` except `test_calibrate.py` and `test_replay.py`, in one run. Result: 3067 passed, 12 failed, 4153 subtests passed. All 12 failures are the still-red fixtures above. The holdout-barrier hook blocks `test_calibrate.py` and `test_replay.py`, so they were not run. Neither one imports the decision path.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 596dd5e | covers on decisions, newcomer_lanes / covered_count, joined cause, mutants |
| 2 | 0bb69d3 | covering_decision inheritance, nearby re-ask for inherited records, mutants |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `covers` and `covered_count` de-duplicate the lead's own member record**
- **Found during:** Task 1
- **Issue:** score.py lists a row's lead in its own `members[]`. Read literally ("record first, then each member"), the plan's `_covers_of` would list the lead twice, and `covered_count` would print 2 for a lone decided row. The 57-01 R4 fixture expects one entry, and the D-10 card test expects "1 finding here".
- **Fix:** `_covers_of` keeps one entry per (agent, file, title), lead first. `covered_count` is 1 plus the covered member identities other than the lead's.
- **Cost if wrong:** a second same-identity member (the same agent re-reporting the same title on another line) gets no `covers` entry of its own, so it cannot inherit after a split. That fails toward asking.
- **Commit:** 596dd5e

**2. [Rule 2 - Correctness] Absorbed member records never inherit**
- **Found during:** Task 2
- **Issue:** the module invariant "closing the row that absorbed it closes nothing for it" would depend only on score.py stripping `canonical_line_content` from member records.
- **Fix:** `covering_decision` returns None for a record with `absorbed_into`. This is pinned by `test_absorbed_member_record_never_inherits`.
- **Cost if wrong:** a covered finding that is later re-absorbed (with an obligation) into a different row is asked again rather than kept. That fails toward asking.
- **Commit:** 0bb69d3

**3. [Rule 2 - Correctness] Agent check mutant-tested as well (T-57-08)**
- **Found during:** Task 2
- **Issue:** the plan listed mutants for inheritance, code match and file check only. The threat register names the same agent as a spoofing guard.
- **Fix:** added `test_split_member_other_agent_never_inherits` and its contrast mutant.
- **Cost if wrong:** none. It is an additional lock.
- **Commit:** 0bb69d3

**4. [Rule 1 - Test fixture] Existing exact-record tests now include `covers`**
- **Found during:** Task 1
- **Issue:** three `TestRecordDecisions` tests pin the whole decision record.
- **Fix:** added `covers` to the expected records. The ARCH row's expected `covers` comes from the raw fixture JSON through a new `arch_row_covers()` helper (never from carry_state). The absorbed-member case expects `code: None`, because member records carry no canonical line.
- **Cost if wrong:** none. The assertions are still exact.
- **Commit:** 596dd5e

**5. [Plan wording] The (b3) mutant's second test**
- **Found during:** Task 1
- **Issue:** the plan says the empty-`_covered_identities` mutant changes the outcome of `test_joined_newcomer_reopens_row`. With empty sets, that row still goes stale, because every member becomes a newcomer.
- **Fix:** the mutant is asserted to trip `test_covered_count_counts_lead_and_covered_members` and `test_same_title_other_lane_is_not_joined`. The second one is the newcomer reader whose outcome actually flips. This still proves both public readers share the one helper.
- **Cost if wrong:** none.
- **Commit:** 596dd5e

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** the card `stale["cause"] == "joined"` assertion in R4 would stay red until 57-06. **Actual:** it is green now, because batch_card already passes `stale_cause` through. **Why:** batch_card copies the carry_state cause rather than re-deriving it. **Cost if wrong:** low. 57-06 still owns the D-10 wording (`covered_count`, `newcomer_lanes`), which is still red.

## Known Stubs

None.

## Threat Flags

None. T-57-08: agent, file, title and code must all match, never across files and never with null code, and the agent, file and code guards each have a mutant. T-57-09: `covers` is derived inside `record_decisions` from the state, and the payload key set is exact (`test_covers_source_is_state`). T-57-10: a newcomer concern reopens the row, and the title exclusion has a mutant.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/carry_state.py, plugins/vibe-check/scripts/test_carry_state.py
- FOUND: 596dd5e, 0bb69d3
