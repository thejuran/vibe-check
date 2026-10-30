---
phase: 59-stale-decisions-and-lost-deferrals
reviewed: 2026-10-28T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - plugins/vibe-check/phases/review/50-fix-loop.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/batch_card.py
  - plugins/vibe-check/scripts/carry_state.py
  - plugins/vibe-check/scripts/score.py
  - plugins/vibe-check/scripts/test_card_text.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_nv_render.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 59: Code Review Report

**Reviewed:** 2026-10-28
**Depth:** standard (changed regions of `git diff 875f292..HEAD` plus direct callers)
**Files Reviewed:** 8
**Status:** issues_found

## Summary

The review covered the Phase 59 changes: evidence pooling in `score.py` (`_kept_open_rows`, the group loop's covered-member nearby check, `_nearby_spots` and `_snapshot_for` spots), the D-06 min_confidence deferral path, the read-time merge in `carry_state.py` (`_merge_nearby`, `_lifted_spots`, `stale_spots`), the card wording in `batch_card.py`, and the two prose files.

I found no silent keep and no data loss. Pooling is consistent across the index, the group loop and the kept-open path. `_current_hash` and the survivor hash use the same `_canonical_for_hash`, so a carried survivor always lands in `same_hash`. `record_decisions` stores evidence from the merged record, so a fresh decision is not immediately stale. The convention checker reported nothing (it has no rule pack for Python).

I ran two scratch experiments through the real score → state → carry_state → card chain. Each confirmed a wording defect. In both, the row still reopens or stays open, but the card tells the owner something wrong or incomplete:

- WR-01: the card leaves out the row's own line when that line and another spot both changed in the same pass.
- WR-02: the D-06 "below your min_confidence; still deferred" note shows on one pass only and is gone from the next pass on.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Card names only the other spot when the row's own line changed too

**File:** `plugins/vibe-check/scripts/score.py:671-686` (`_nearby_spots` skips `own_line`), `:2842-2846`, `:510-512`. Wording at `plugins/vibe-check/scripts/batch_card.py:571-590`. Prose at `plugins/vibe-check/phases/shared/90-finalize.md:110-111`.

**Issue:** `_nearby_spots` always leaves out the row's own line. So when one pass changes code beside both the row's own line and another copy or grouped member, `nearby_spots` names only the other spot, and the card says the reopen came from somewhere else. Reproduced on the real chain with the CR-01 shape: copies at 10 and 30, dismissed on pass 1, pass 2 diff `[[12,12],[33,33]]`:

```
#1 src/a.py:10 — Unchecked return at A (medium) — code next to line 30 (another copy of this line) changed since your decision on pass 1 (was: dismissed — ...)
```

The edit at line 12, beside the row's own line, is not mentioned. The owner is sent to line 30 and may confirm the old decision without looking at the change next to line 10. With three copies, the "and N other spots" count is also one short, because the row's own spot is not counted. The 90-finalize prose says "the spot is the lowest changed line", which is false here: 12 is lower than 30. The same gap appears on the read path. `_lifted_spots` (`carry_state.py:333-347`) lifts a source copy's `nearby_spots`, and that list never contains the source's own line, so a source whose own line also changed loses that spot.

**Fix:** Record the row's own line as a spot when it is also reached and other spots exist. For example, use a third kind `"own"` that the card renders as "code next to this line and N other spots changed". Alternatively, record nothing when the own line is reached (keep the plain wording) and append the other spots as a count. Then correct the "lowest changed line" sentence in 90-finalize.md. Add a fixture for `cr01_scenario` with ranges `[[12,12],[33,33]]` that asserts the card mentions the row's own line.

### WR-02: The D-06 "still deferred" note is gone from the second pass on

**File:** `plugins/vibe-check/scripts/score.py:2604-2609` (the reason is written only for a member with no obligation). Also `score.py:2405` (`rep.pop("kept_open")`) and `batch_card.py:563-578`.

**Issue:** The D-06 reason `below-min-confidence 45; deferred-by: <hash>` is written only while the dropped record is a covered member with no obligation of its own. On the next pass that kept-open row is carried as a lead with its own stored hash. It is now in `carried_obligations`, so it takes the `elif` branch, and the reason becomes plain `below-min-confidence`. `_deferred_below_min_note` then returns `""`. Reproduced with `deferred_covered_sub_threshold_scenario("defer", min_confidence=45, member_conf=40)` plus two quiet passes at min_confidence 45:

```
P2 kept_open: below-min-confidence 45; deferred-by: 3449f4b5…   card: "… — below your min_confidence (45); still deferred"
P3 kept_open: below-min-confidence                              card: no note
P4 kept_open: below-min-confidence                              card: no note
```

The row stays open and the gate still holds. That part is fine. But from pass 3 on, the card no longer tells the owner why a deferred finding is still listed, or that it is still deferred. D-06 asks for that note. `test_cw59_dmc_card_keeps_the_deferred_member_visible` and the `test_card_text` fixture check only the first pass, so nothing catches this.

**Fix:** In the min_confidence branch, keep the `deferred-by` link for a carried record whose prior row was a D-06 kept-open row. One way is to read `cf.get("kept_open")` before `rep.pop` at :2405, keep the parsed covering hash on the working record, and write `"below-min-confidence %d; deferred-by: %s"` again when it is present. Another way is to let `batch_card` derive the note from `carry_state._covering(record, state)` plus a plain `below-min-confidence` reason, so the note does not depend on the reason string surviving. Add a fixture that runs pass 3 at min_confidence 45 and asserts the note is still on the card.

## Info

### IN-01: The spot validator and kinds are written twice, with different rules

**File:** `plugins/vibe-check/scripts/score.py:651-668` (`_SPOT_KINDS`, `_valid_spots`) and `plugins/vibe-check/scripts/carry_state.py:308-328` (`_SPOT_KINDS`, `_well_formed_spots`)

**Issue:** The writer accepts tuples and does not sort. The reader rejects tuples and sorts. Today this is harmless because JSON round-trips tuples to lists, but adding a kind or changing a rule in one place and not the other will make the writer and reader disagree without any error.

**Fix:** Keep one `_SPOT_KINDS` and one validator. `score.py` already imports nothing from carry_state, so move the shared constant into a small shared module, or add a test asserting the two `_SPOT_KINDS` tuples are equal.

### IN-02: The D-06 kept-open row stores `orchestrator_score: 0`

**File:** `plugins/vibe-check/scripts/score.py:2605` (`_covered_entry(m, ..., 0)`)

**Issue:** `_kept_open_rows` copies the obligation's score into the row verbatim, so the D-06 row carries `orchestrator_score: 0` from then on. Any report or count that shows or sorts by the score will treat a deferred warning as a zero-score finding.

**Fix:** Pass the member's raw scored value if one can be computed before grouping, or `None`, and check that the report renders `None` cleanly. At minimum, document that 0 means "not scored".

### IN-03: Prose says the wording never depends on finding order, but R8 shows it can

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:110`

**Issue:** "the spot is the lowest changed line, so the wording does not depend on finding order". R8 in 59-REPRO.md records that a stamp tie in `_pooled_prior` makes which copy's `nearby_spots` ride forward depend on arrival order. WR-01 shows the named spot is not always the lowest changed line. The prose promises more than the code does.

**Fix:** Change the sentence to "the lowest changed line among the other spots", and either fix R8 or note it next to this sentence.

## Set aside (needs ruling)

### SA-01: Fix-loop dispatch with two same-hash kept-open rows

**Where:** `plugins/vibe-check/scripts/score.py:526` (`visible.add` removed, so one row per dropped copy) and `plugins/vibe-check/scripts/batch_card.py:349-385` (`resolve_fix_targets` keys by hash through the deduped `open_findings`)
**Why excluded:** 59-REPRO.md lists it as residual R6 (not exercised), and I found no reproduced failure. The card and dispatch see one deduped record per hash, so the fixer is given only the representative's file:line.
**Effect if left as is:** Choosing "fix" on that identity may fix only one copy. The other copy stays open and comes back on the next pass. That fails toward asking, so nothing is silently kept.
**Needs:** A ruling: accept as carried (R6), or reproduce it in a later phase.

### SA-02: D-01 later-pass over-ask

**Where:** `plugins/vibe-check/scripts/score.py:2829-2846`
**Why excluded:** It is already carried as R1 / backlog 999.23 under D-02. The exemption applies only on the pass where the new copy first appears.
**Effect if left as is:** An edit beside a copy that appeared after the decision re-asks the owner on later passes. It fails toward asking.
**Needs:** None beyond the existing carry. Listed so nothing is dropped silently.

---

_Reviewed: 2026-10-28_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
