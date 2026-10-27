---
phase: 57-decision-continuity-within-closure
plan: 06
subsystem: vibe-check finalize card (batch_card.py) and card prose
tags: [batch_card, card-wording, finalize, prose-lock]
requires:
  - "57-03: carry_state.newcomer_lanes / covered_count / covering_decision, joined stale cause"
  - "57-04: snapshot.nearby_at stamp, nearby stale cause"
provides:
  - "stale tag fields gained (always), covered + joined (cause joined), via covering for inherited decisions"
  - "card suffixes: code next to it changed / severity rose ... now also report(s) it / D-10 joined note (full + compact)"
  - "90-finalize.md Open/Closed contract matching the helper, locked by check_phase57_decisions"
affects: [57-07, 58]
tech-stack:
  added: []
  patterns:
    - "card values that decide a reopen are read from carry_state, never re-derived in batch_card (divergence mutant proves it)"
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/scripts/test_batch_card.py
    - plugins/vibe-check/scripts/test_card_text.py
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/scripts/test_finalize_card.py
decisions:
  - "The severity-rise wording replaces 'severity changed' only when stale.gained is non-empty; NV and pre-attribution decisions keep the old text"
  - "An inherited (covering) decision that goes stale is tagged via 'covering' with prior_hash = the decided row, so it reopens showing the earlier decision"
  - "The joined note omits '(your reason: ...)' when the decision has no reason, instead of rendering an empty parenthetical"
metrics:
  duration: "~45 min"
  completed: 2026-10-26
  tasks: 2
  files: 6
---

# Phase 57 Plan 06: Card wording for reopened decisions Summary

When a decided finding comes back, the card now says what changed: "code next to it changed", "severity rose (A → B) …: security now also reports it", or, for a row a new concern joined, "1 finding here already dismissed (your reason: …); a new concern from security joined it". The finalize prose now describes the same rules the helper applies.

**For the owner, in plain terms:** a reopened row always shows your earlier decision, your reason and the specific trigger, including which reviewer is new. Older decisions saved before reviewer lists were recorded still show the old "severity changed" wording.

## What was built

- **batch_card.py:** the stale tag gains `gained` (from `carry_state.gained_lanes`) and, for cause `joined`, `covered` (`carry_state.covered_count`) and `joined` (`carry_state.newcomer_lanes`). batch_card reads neither the coverage list nor the identity helper itself (`grep covers batch_card.py` = 0). `_suffixes` delegates to `_stale_suffix`, which has full and compact forms for nearby, severity rise, legacy severity, joined and code.
- **Tests:** whole-dict tag assertion updated (`"gained": ["security"]`, since the 57-02 fixture already carries a new lane); `test_rows_line_move_keeps_decision` renamed to `test_rows_line_move_is_not_stale` (D-01 comment kept); new tag tests for nearby, rise, joined (covered == 2) and inherited; `test_joined_lanes_come_from_carry_state` patches `carry_state.newcomer_lanes` to `[]` and shows that both the reopen and the card row disappear. Exact-string tests for every new suffix (single and plural lanes and counts, dismissed and deferred), compact forms, legacy wording and a flattening test.
- **90-finalize.md:** Open allows the one coverage-inheritance exception; Closed spells out line not compared / nearby window / joined concern / drop keeps / rise needs a new lane; three new suffix bullets; the severity bullet is annotated as the NV/legacy form. Line 106 is unchanged.
- **test_finalize_card.py:** `check_phase57_decisions` plus removal mutants for all 8 phrases, and a check that the old "equals the same four values now" rule is gone.

### `_one_line` wrap check (batch_card.py, after a08da21)

| Value | Line | Wrapped |
|---|---|---|
| `stale.get("reason")` in `_was` | 447 | `_one_line(...)` |
| lane names (`_lanes`, used for gained + joined) | 454 | `_one_line(v)` per element |
| `stale.get("joined")` | 464 | via `_lanes` |
| `stale.get("reason")` in the joined note | 471 | `_one_line(...)` |
| `stale.get("gained")` | 480 | via `_lanes` |
| `stale.get("was_band")` rise / legacy | 492 / 499 | `_one_line(...)` |

`at_pass` and the integer `covered` count are formatted as before (not strings from the diff). The flattening test fails when `_lanes` drops `_one_line`; I ran that mutant and saw it fail.

### Lock phrases (`check_phase57_decisions`)

`the line number is stored, not compared` · `snapshot.nearby_at` · `a drop keeps the decision` · `re-asks only with new corroboration` · `recorded as covered at decision time` · `stale.cause == "nearby"` · `now also report(s) it` · `joined it`

## Verification (observed)

- `pytest -q test_batch_card.py test_card_text.py`: 121 passed after Task 1. `test_decision_continuity.py`: 30 passed (TestCardWording 4/4, R2/R3a/R4/R7 green).
- `pytest -q test_finalize_card.py test_card_text.py`: 54 passed after Task 2.
- Acceptance greps: `code next to it changed since your decision on pass` 2; `now also report` 1; `joined it` 2; `carry_state.newcomer_lanes(` 1; `carry_state.covered_count(` 1; `covers|_covered_identities|covered titles` 0; legacy `severity changed (%s → %s)` 1; in 90-finalize.md the `stale.cause == "nearby"` / `"joined"` count is 1 each, `equals the same four values now` 0, `helper links an edited finding` 1.
- **Full suite (incl. test_replay.py):** baseline before this plan had 7 failed (all card wording). Final run: **3208 passed, 0 failed**, 4243 subtests passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Inherited decision reopened as a brand-new row**
- **Found during:** writing the SUMMARY (probe of the 57-03 covering path)
- **Issue:** a finding that inherits a decision through `covering_decision` and then goes stale (nearby) appeared on the card with `stale = None`, so it had no earlier-decision suffix. That breaks this plan's truth that a reopened row is never shown as brand new.
- **Fix:** `_same_hash_stale` falls back to `carry_state.covering_decision`, sets `via: "covering"` and `prior_hash` to the decided row, and documents this in 50-fix-loop.md. The fix includes a test and a mutant.
- **Cost if wrong:** a cosmetic annotation on one rare path. The reopen itself is still decided by carry_state.
- **Commit:** a08da21

**2. [Rule 2 - Prose/helper agreement] 50-fix-loop.md suffix list updated**
- **Issue:** the fix-loop card prose documents the same suffixes and `TestProseMatchesHelper` checks both files. Without an update, its "severity changed" line would be wrong for a lane-backed rise.
- **Fix:** added the nearby / rise / joined forms to the one-line suffix list, plus a pointer to 90-finalize.md. Added a nearby entry to `TestProseMatchesHelper`. Its severity entry now uses a legacy-decision state.
- **Cost if wrong:** the documentation for one prose file needs a rewording.
- **Commit:** 41899c1

**3. [Convention] No "Phase 57" in product prose**
- The plan text put "Phase 57 D-01/D-09" into 90-finalize.md. The prose already uses bare D-xx tags, and "Phase N" there means pipeline phases (Phase 0, 0.5, 5), so I wrote D-01/D-02/D-05/D-06/D-08/D-09 without the GSD phase number. No locked phrase depends on it.
- **Cost if wrong:** a one-word wording change.

**4. [Plan-text drift] Tag dict `"gained"` value**
- The plan said to add `"gained": []` to the whole-dict assertion, but 57-02 already gave that fixture a new `security` lane, so the true value is `["security"]`, and that is what the test asserts.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/batch_card.py, test_batch_card.py, test_card_text.py, test_finalize_card.py, phases/shared/90-finalize.md, phases/review/50-fix-loop.md
- FOUND commits: 52de114, 41899c1, a08da21
