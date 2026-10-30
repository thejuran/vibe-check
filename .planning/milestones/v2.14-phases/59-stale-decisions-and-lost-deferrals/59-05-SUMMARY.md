---
phase: 59-stale-decisions-and-lost-deferrals
plan: 05
subsystem: vibe-check card wording (batch_card + prose)
tags: [STALE-02, DEFR-01, D-04, D-05, D-06, card-text, prose-lock, mutation-lock]
requires: ["59-04 carry_state.stale_spots at 3e31654", "59-03 kept_open 'below-min-confidence N; deferred-by:' reason"]
provides:
  - "batch_card stale tag fields spot_line / spot_kind / other_spots (cause nearby, from carry_state.stale_spots)"
  - "batch_card._spot_suffix (other copy / grouped / several spots, full + compact)"
  - "batch_card._deferred_below_min_note (' — below your min_confidence (N); still deferred')"
  - "row field kept_open on card rows"
  - "prose templates for the four new forms in 90-finalize.md and 50-fix-loop.md"
  - "TestProseMatchesHelper entries nearby_copy / nearby_grouped / nearby_many / deferred_min_confidence + prose-drift mutant"
  - "seven test_cw59_ real-chain card tests (incl. carry_state divergence mutant)"
affects: [59-06]
tech-stack:
  added: []
  patterns: ["card renders only carry_state's reader data; strict string parse (no re) for owner-visible text built from state strings"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/scripts/test_card_text.py
    - plugins/vibe-check/scripts/test_decision_continuity.py
decisions:
  - "kept_open is parsed with string operations, not re: test_batch_card's read-only import allowlist forbids new imports; the parse accepts ASCII digits only"
  - "The deferred-below-min_confidence prose bullet sits at the END of the 90-finalize.md suffix list (after stale joined), matching render order, not directly after stale nearby"
  - "test_cw59_ prefix and the cr02 card test join _READ_MERGE_ONLY (the cr02 spot needs the read-side merge)"
  - "STALE-02 and DEFR-01 marked complete: every reproduced shape (CR-01, CR-02, CR-04, multi-spot, DEFR-01) now renders its reopen reason / still-deferred note from the real chain"
metrics:
  duration: "~35 min"
  completed: 2026-10-29
  tasks: 3
  files: 5
requirements: [STALE-02, DEFR-01]
---

# Phase 59 Plan 05: Reopen-reason and still-deferred card wording Summary

The card now names the other spot that caused a reopen. A change beside another copy reads "code next to line 30 (another copy of this line)". A change beside a grouped finding reads "code next to line 10 (a finding grouped here)". When several spots changed, it shows the lowest line plus a count ("code next to line 30 and 1 other spot"). A deferred member kept open below min_confidence gets " — below your min_confidence (45); still deferred". When the change is beside the row's own line, the wording is byte-for-byte the same as before. Both prose files document every form, and tests tie the prose, the helper and the real score.py chain together.

## Tasks

| # | Task | Commit | Verified (observed) |
|---|------|--------|---------------------|
| 1 | batch_card renders spot forms + deferred note | 05bc268 | `pytest -q test_batch_card.py test_card_text.py test_decision_continuity.py` -> 253 passed, 0 failed; greps: "another copy of this line" 1, "a finding grouped here" 1, "still deferred" 2, both same-spot literals 1 each, `carry_state.stale_spots(record, state)` 1; manual parse probe on 8 kept_open shapes rendered only the two valid forms |
| 2 | Prose in 90-finalize.md and 50-fix-loop.md | aa1d83f | plan verify loop printed `ok` (all 3 templates in both files); existing nearby template count 1 in each file; `pytest -q test_nv_render.py test_card_text.py` -> 65 passed |
| 3 | Prose-lock entries, real-chain card tests, mutants | 5f6d4e1 | plan verify `-k "TestProseMatchesHelper or cw59 or spots_not_recorded or Mutants"` -> 42 passed, 0 failed; `test_card_text.py` 32 passed; patching `_spot_suffix` -> None fails the render test 6x, `_deferred_below_min_note` -> "" fails it 2x |

## Final verification

- `cd plugins/vibe-check/scripts && pytest -q` -> **3642 passed, 0 failed, 4797 subtests passed in 156.34s**. 59-04 ended at 3630, so this plan added 12 tests: 7 cw59 plus 5 card_text.
- `pytest -q test_replay.py` -> 64 passed, 10 subtests passed. No replay delta.
- GOLDEN_DIGEST unchanged: score.py and test_score.py were not touched (`git diff 40f12ef -- score.py test_score.py` is empty), and `test_score.py -k Golden` -> 9 passed.
- The real-chain card text was observed directly:
  - cr01@33: "code next to line 30 (another copy of this line) …"
  - cr04: "code next to line 10 (a finding grouped here) …"
  - cr02: line 30 copy, on the absorbed sidecar row
  - three copies: "line 30 and 1 other spot"
  - cr01@12: "code next to it changed …", the unchanged same-spot form
  - dmc: "… (was: deferred — …) — below your min_confidence (45); still deferred"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] kept_open parsed without `re`**
- **Found during:** Task 1
- **Issue:** The plan said to `import re`. test_batch_card `TestReadOnly.test_import_set` limits batch_card's imports to json/os/sys/carry_state/batch_parse, so the new import failed it.
- **Fix:** `_deferred_below_min_note` parses with startswith/partition and checks for ASCII digits only. It accepts exactly `below-min-confidence[ <digits>]; deferred-by: ` and is stricter than `\d`, which also matches Unicode digits.
- **Cost if wrong:** Little. If the import allowlist is widened later, the parse could switch to a regex with the same accepted shapes.
- **Files modified:** batch_card.py
- **Commit:** 05bc268

**2. [Rule 1 - Bug] Deferred-note bullet placed in render order**
- **Found during:** Task 2
- **Issue:** The plan put the deferred bullet directly after "stale nearby". The list is documented as "in this order when they apply", but the note renders after the stale suffix, after stale joined too. Following the plan would have described the order wrongly.
- **Fix:** In 90-finalize.md the two spot bullets go after stale nearby and the deferred bullet goes last. 50-fix-loop.md follows the same order, as the plan specified.
- **Cost if wrong:** Prose ordering only; no test depends on bullet position.
- **Commit:** aa1d83f

**3. [Rule 1 - Bug] Replaced a tautological prose-drift check**
- **Found during:** Task 3
- **Issue:** My first draft of `test_agreement_trips_on_prose_drift` asserted that a template was absent from text it had just been removed from. That assertion could never fail.
- **Fix:** The test now runs `test_documented_suffixes_render` against each prose file with the template removed (patching `read`) and requires that run to fail.
- **Cost if wrong:** None; the lock is strictly stronger.
- **Commit:** 5f6d4e1

### Additional tests beyond the plan
These were added to test_card_text.py: compact forms drop "(was: …)", "1 other spot" is singular, a nearby reopen without spots keeps the plain wording in both modes, and the deferred note requires the exact kept_open shape (malformed, forged-newline and sub-threshold variants render no note).

## TDD Gate Compliance

Tasks 1 and 3 were tagged tdd. The plan put the implementation (Task 1) before its tests (Task 3), so the commits are ordered feat -> docs -> test, with no separate RED commit. To get equivalent evidence that the tests can fail, I ran mutants after the fact: patching out `_spot_suffix` or `_deferred_below_min_note` makes the render test fail, the carry_state divergence mutant flips the cr01 card text, and the spots-not-recorded scorer mutant trips the cw59 cr01, cr04 and three-copies tests.

## Known Stubs

None.

## Threat Flags

None. T-59-13 is mitigated by the strict kept_open parse: only the captured ASCII digits are rendered, and the spot line comes from `_well_formed_spots` ints. T-59-14 is mitigated by the divergence mutant plus TestProseMatchesHelper.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/batch_card.py, phases/shared/90-finalize.md, phases/review/50-fix-loop.md, scripts/test_card_text.py, scripts/test_decision_continuity.py
- FOUND commits: 05bc268, aa1d83f, 5f6d4e1
