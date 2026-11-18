---
phase: 66-close-out-freshness
plan: 08
status: paused
paused_at: "Task 2 (checkpoint:decision, owner approval before any carry_state.py edit)"
subsystem: decision continuity / covering decisions
tags: [999.44, shape-2, covering-decision, carry_state, checkpoint]
requires:
  - "66-02, 66-07"
provides:
  - "covering_order_scenario + TestShape2CoveringOrder: real-writer reproduction of 999.44 shape 2 for defer and dismiss"
affects:
  - "66-09 (FRESH-03 verdict needs the shape-2 outcome line)"
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "Shape 2 REPRODUCED through run_pass + decide_on (record_decisions) for both kinds: two covers name one finding, and the older one wins when its hash sorts first"
  - "Task 2 reached: awaiting owner choice approve-repair / known-limit; carry_state.py untouched"
metrics:
  completed: "paused 2026-11-18"
  tasks: "1 of 3 (paused at Task 2)"
  files: 1
---

# Phase 66 Plan 08: 999.44 shape 2 (covering-decision order) Summary (PAUSED)

999.44 shape 2 reproduces through the real writer for both decision kinds. When two owner decisions both list the same finding in their `covers`, `_covering` picks whichever decision hash sorts first, not the newest decision. In the older-first ordering this is a wrong keep: the finding stays `current`, Close out returns `write`, and the card hides it. Under the newer decision alone it would be re-asked. The plan is paused at the Task 2 owner checkpoint. `carry_state.py` is untouched.

## Task 1: producibility attempt (commit 6d9313b0)

`covering_order_scenario(kind, order, decide)` uses only `run_pass` and `decide_on`. Nothing in `decisions` or `covers` is written by hand.

1. Pass 1: `security` X1 (line 12) leads a row holding `bugs` M (line 10).
2. Pass 2: a quiet pass. The row rises to critical and the owner decides X1, so X1's cover for M has band critical.
3. Pass 3: line 12 is rewritten (diff `[[12, 12]]`) and X1's re-check answers `resolved`. A fresh `perf` X2 (line 11) leads M's row at medium and the owner decides X2, so X2's cover for M has band medium.
4. Pass 4: no code change. M's lane re-reports it at conf 95 critical, and `security` corroborates it. M leads its own row at critical with a lane neither cover recorded.

`order` changes only X1's title. That decides whether X1's decision hash sorts before X2's (`older_first`: 3449f4b5 < a73b3ca7) or after (`newer_first`: be1928f3 > a73b3ca7).

Observed on current code:

| Test | defer | dismiss |
|------|-------|---------|
| test_shape2_two_covers_producible_covering_order (both orders) | pass: 2 covers name M (at_pass 2 and 3) | pass |
| test_shape2_newest_cover_decides_covering_order, newer_first | pass: `stale`, gate not write | pass |
| test_shape2_newest_cover_decides_covering_order, older_first | **FAIL: `current` != `stale`** | **FAIL: same** |
| test_shape2_single_cover_control_covering_order (older only -> current, newer only -> stale) | pass | pass |

Run: `pytest -q -p no:cacheprovider test_decision_continuity.py -k covering_order` gave 2 failed and 3 passed, with 14 subtests passed. The 2 failures are exactly the older_first subtests. Task 1 verify (`-k shape2_single_cover_control`) gave 1 passed, with 8 subtests passed. Scratch probe, older_first: `e2e_gate` = `write` and card rows `[]`. The same probe, newer_first: `outstanding-to-phase-5` and card row `dee0f534`.

Why it is producible: `record_decisions` writes each decision's `covers` from the state at decision time and never rewrites an older decision. X1's decision therefore keeps naming M after X2's decision names it too.

## Task 2: CHECKPOINT REACHED (awaiting owner)

Before pausing, these checks were run:
- The RED commit 6d9313b0 exists.
- `pytest test_finalize_parity_grid.py -k byte_identical` gave 1 passed, with 4 subtests passed.
- `git diff --quiet dd8e4ab -- carry_state.py` exited 0.
- `git status --porcelain carry_state.py` was empty.

Options presented:
- **approve-repair**: change `_covering` so it picks the cover with the highest `at_pass`, using the hash only as a tie-break. This is the fix the Phase 57 GAPS review proposed. The parity grid's 2.14.1 side would first be switched to modules materialized from `dd8e4ab`. Only the byte-identity pin for `carry_state.py` is dropped; the pins for guard.py, finalize_gate.py and fixcommit.py stay.
- **known-limit**: keep `test_shape2_newest_cover_decides_covering_order` as an `@unittest.expectedFailure` known-limit test. No change to `carry_state.py` or the grid.

Owner answer: _pending_.

## Deviations from Plan

**1. [Rule 3] Test names carry a `_covering_order` suffix**
- **Found during:** Task 1
- **Issue:** VALIDATION.md selects these tests with `-k covering_order`. The class name `TestShape2CoveringOrder` does not contain that substring, and the plan's method names don't either.
- **Fix:** the methods are `test_shape2_two_covers_producible_covering_order`, `test_shape2_newest_cover_decides_covering_order` and `test_shape2_single_cover_control_covering_order`. Kinds are subtests. The `-k shape2_single_cover_control`, `-k shape2` and `-k covering_order` selectors all match.
- **Cost if wrong:** cosmetic only (test names).

**2. [Rule 1] The sequence takes four passes, not three**
- **Issue:** a lone-lane row is capped at warning on its first pass. The older cover only reaches the critical band IN-03 describes after the quiet pass-2 persistence rise. So X1 is decided at pass 2 and X2 at pass 3. The "split" is M leading its own row at pass 4. X2 stays on that row as a member with its own obligation, and there is no code change, so pass 4's empty diff is realistic.
- **Cost if wrong:** low. The single-cover controls show each cover alone gives the expected state.

## ROADMAP note to apply

Not applicable yet. The text depends on the owner's Task 2 answer. The continuation agent will put it here once that answer is in. The planned wording (orchestrator applies it to `### 999.44` as a new paragraph after "Shape 1 outcome (Phase 66 ..."):

- approve-repair: `Shape 2 outcome (Phase 66, 2026-11-DD): repaired — _covering prefers the newest cover (highest at_pass, hash tie-break; owner-approved at 66-08 Task 2); reproduced first through record_decisions for defer and dismiss — tests: TestShape2CoveringOrder.test_shape2_two_covers_producible_covering_order, test_shape2_newest_cover_decides_covering_order, test_shape2_single_cover_control_covering_order.`
- known-limit: `Shape 2 outcome (Phase 66, 2026-11-DD): reproduced; owner-accepted known limit — two decisions' covers name one finding through record_decisions and the older cover wins when its hash sorts first (wrong keep, Close out writes), for defer and dismiss — tests: TestShape2CoveringOrder.test_shape2_newest_cover_decides_covering_order (expectedFailure), test_shape2_two_covers_producible_covering_order, control test_shape2_single_cover_control_covering_order.`

## Known Stubs

None.

## Commits

- 6d9313b0 test(66-08): 999.44 shape 2 producibility attempt through record_decisions

## Self-Check: PASSED

Commit 6d9313b0 exists. `test_decision_continuity.py` contains `class TestShape2CoveringOrder` (1) and `def covering_order_scenario` (1). `carry_state.py`, STATE.md and ROADMAP.md were not modified.
