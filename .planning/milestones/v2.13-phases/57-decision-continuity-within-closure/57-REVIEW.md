---
phase: 57-decision-continuity-within-closure
reviewed: 2026-10-26T19:44:31Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/review/30-collect-score.md
  - plugins/vibe-check/phases/review/50-fix-loop.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/batch_card.py
  - plugins/vibe-check/scripts/carry_state.py
  - plugins/vibe-check/scripts/score.py
  - plugins/vibe-check/scripts/test_batch_card.py
  - plugins/vibe-check/scripts/test_card_text.py
  - plugins/vibe-check/scripts/test_carry_state.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_nv_render.py
  - plugins/vibe-check/scripts/test_replay.py
  - plugins/vibe-check/scripts/test_score.py
  - plugins/vibe-check/templates/scoring.md
findings:
  critical: 2
  warning: 4
  info: 3
  total: 9
status: issues_found
---

# Phase 57: Code Review Report

**Reviewed:** 2026-10-26T19:44:31Z
**Depth:** standard (diff `5e33c8e..HEAD`)
**Files Reviewed:** 16
**Status:** issues_found

## Summary

The phase's own guards hold up. The 8 phase test files pass (973 tests). I mutated 19 of the new guards in `carry_state.py`, `score.py` and `batch_card.py` (absorbed-member guard, inherited nearby check, rise-needs-new-lane, title corroboration, obligation skip, nearby compare, covers file check, drop-keeps, same-hash prior, kept-by-ident obligation move, member/kept-open nearby stamps, prior-stamp carry on both branches, first-raise exclusion, window direction, covering card path, the `decided` read and its fail-closed `None`). Every mutant was killed. None of the tests is decorative. Convention checks returned no findings.

The defects are in the new inheritance path (`covers` / `covering_decision`), which the tests do not cover adversarially:

1. It closes findings the owner never decided. A member with its own open obligation is recorded in `covers` and closes as soon as it splits out of the row.
2. An inherited decision skips every Phase 57 reopen rule except "nearby". A band rise with new corroboration, or a different concern joining, never reopens it.

Both cause wrong-keeps that let the Finalize gate pass. Both reproduce on current code with plain `carry_state` calls (reproductions below).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: A row decision silently closes a member obligation the owner never decided, once that member splits out (fail-open)

**File:** `plugins/vibe-check/scripts/carry_state.py:551-571` (`_covers_of`), `:663-697` (`covering_decision`); contract text in `plugins/vibe-check/phases/shared/90-finalize.md:25`
**Issue:** `_covers_of` lists every dict member of the decided row, including members that carry their own `obligation`. Those are separately owed records. The card shows them as "absorbed … decided on its own", and 90-finalize states that "a decision … on the LEAD row closes nothing for it". While the member stays absorbed, `covering_decision` refuses it (the `absorbed_into` guard), so it stays open. When it later becomes its own row with the same hash, it has no decision of its own. `covering_decision` then matches the `covers` entry, and `decision_state` returns `"current"`. The obligation drops out of `outstanding_cw` even though the owner never decided it.

Reproduction (current HEAD):
```
pass 1: row hR (lead a/T1) + member b/T2 with obligation hB (warning)
finalize_counts -> outstanding ['hB','hR']
record_decisions(hR dismiss)          -> outstanding ['hB']   (correct)
pass 2: hB is its own row, code unchanged
decision_state(hB) -> 'current'; outstanding_cw_hashes -> []   (hB silently closed)
```
`covered_count` also counts the obligation member, so the card can say "2 findings here already dismissed" while one of them is open and undecided.

**Fix:** Leave out of `covers` (and out of `covered_count`) any member whose obligation names a different hash from the decided record. Members whose obligation hash equals the record's own hash still count: the e2e test at `test_decision_continuity.py:1143` relies on that same-hash case.
```python
for m in members if isinstance(members, list) else []:
    if not isinstance(m, dict) or _identity(m) in seen:
        continue
    obl = m.get("obligation")
    if (isinstance(obl, dict) and isinstance(obl.get("stable_hash"), str)
            and obl["stable_hash"] != record.get("stable_hash")):
        continue  # owed on its own; the row decision never covers it
    ...
```
Add a RED fixture with exactly the reproduction above, plus a mutant that restores the old loop.

### CR-02: An inherited (`covers`) decision ignores band rise with new corroboration (D-05) and joined newcomers (D-08)

**File:** `plugins/vibe-check/scripts/carry_state.py:727-731` (`decision_state` inherited branch), `:551-571` (`_covers_of` stores no band or attribution)
**Issue:** For a record without its own decision, `decision_state` returns `"current"` unless `_nearby_since` holds. None of the rules the phase locked for ordinary decisions run on this path:
- a band rise backed by a new reviewer lane (D-05 refinement)
- a newcomer concern from an uncovered lane joining (D-08 refinement)

The `covers` entry stores no band and no attribution, so the comparison cannot be made at all. A covered member may have been a sub-threshold note the owner never saw as its own card line. If it later splits into its own critical row, corroborated by a new lane and joined by a different concern, it closes silently.

Reproduction (current HEAD):
```
pass 1: row hR (a/T1) with plain member c/T3 'z = 3'; owner dismisses hR
pass 2: hC = c/T3 own row, band critical, attribution [c, security, codex-adversarial],
        plus member security/'SQL injection'
decision_state(hC) -> 'current'; outstanding_cw_hashes -> []
```
**Fix:** Store `band` (the member's effective band, or the row band when unknown) and the reporting lanes in each `covers` entry at record time. In the inherited branch, run the same ordered checks as the own-decision branch against that entry: nearby, then `newcomer_lanes` (using the covers list), then the band rule with `gained` computed against the entry's lanes. Any field missing from the entry should fail toward asking, the way a legacy rise does. Extend `stale_cause` so it can return `"severity"` / `"joined"` for the inherited path, and add a fixture for each.

## Warnings

### WR-01: Relocating a decided ordinary record to a duplicate line elsewhere in the file keeps the decision on the wrong code and blocks fix closure (D-13)

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:55` (decided-record relocation reusing cases 1-3); simulator at `test_decision_continuity.py:107-160`
**Issue:** For decided ordinary records, case 2 searches the whole file for the stripped canonical line and moves the record to the single, or nearest-unique, match, with no distance bound. Needs-verification records have a whole-snippet fingerprint behind the same search; ordinary records do not. `decision_state` compares only file plus canonical text.

Example: the flagged line is deleted by a real fix, and an identical line exists elsewhere (`return None`, `pass`, `}`, a repeated call). The decision then jumps to unrelated code and stays `"current"`, and the finding persists instead of going `fixed-since-last`. This breaks D-13: a deferred finding that gets fixed must close through the Phase 56 path. The nearby window (D-02) is then watched at the wrong site.

**Fix:** Bound case 2 for ordinary decided records. Either require the match to fall within the shifted-hunk distance (for example, no more than the net lines inserted or removed above the stored line in this pass's diff), or require the stored `canonical_window` (the line plus up to 2 lines) to match at the candidate as well. Otherwise use case 4 (read the stored line → `fixed-since-last`). Mirror the rule in `relocate_decided` and add a "deleted line with a duplicate elsewhere" fixture.

### WR-02: Deleting code beneath a decided line (for example removing a guard) never stamps `nearby_at`

**File:** `plugins/vibe-check/scripts/score.py:1368-1379` (`_nearby_changed`); range construction is unspecified in `30-collect-score.md:64`
**Issue:** `_nearby_changed` tests whether any new-side line in `[line, line+5]` falls inside `changed_line_ranges`. A pure deletion hunk (`@@ -20,2 +19,0 @@`) has no new-side lines. The prose that builds `{file: [[start,end]]}` does not say how a zero-count hunk is represented, so it is almost certainly dropped. Removing the guard or validation directly beneath a dismissed line is the textbook "relevant evidence changed" case for D-02. As written, it keeps the dismissal (wrong-keep). Phase 56's recheck trigger had the same blind spot, but it also had a "file touched" fallback. The decision re-ask has no fallback, by design (D-03).
**Fix:** Specify in `30-collect-score.md` that a zero-count new-side hunk `+S,0` contributes the range `[S, S+1]`, covering the lines on either side of the deletion point. Alternatively, pass a separate `deleted_at` list that `_nearby_changed` also checks. Add a score.py fixture for a pure deletion beneath a decided line.

### WR-03: `gained_lanes` reads the row-wide site `attribution`, so the D-05 rise test both over-asks with a false card and under-asks

**File:** `plugins/vibe-check/scripts/carry_state.py:512-532`; `score.py:2462,2573` (row `attribution` = every lane in the site group); `batch_card.py:488-497`
**Issue:** Row `attribution` is the union of every lane in the site cluster. It includes lanes reporting a *different* concern and weak sub-threshold notes that "never boost". This causes errors in both directions:
- **Over-ask.** Lane `b` adds an unrelated concern that carries its own obligation (so it is not a newcomer), and the band rises from the persistence bonus alone. The decision reopens, and the card says "b now also reports it", which is false. This is a re-ask without new evidence, which the v2.11/D-05 refinement forbids.
- **Wrong-keep.** Lane `b` was present at decision time with a different concern, so it is in the saved `attribution`. Later `b` corroborates *this* concern and the band rises. `gained_lanes` returns `[]` and the decision is kept, which violates D-05 ("another reviewer now also reports the finding").

**Fix:** Save and compare the lanes that report *this* concern: members whose title matches the record's title (the same corroboration notion `newcomer_lanes` already uses), excluding non-qualifying weak notes if score.py can mark them. Use that set both for the reopen and for the card's `gained`.

### WR-04: D-09 inheritance keys member code on the first line of the agent's quoted snippet, not the flagged line

**File:** `plugins/vibe-check/scripts/carry_state.py:537-571` (`_first_code_line` → `covers[].code`), `:647-660` (`_covers_entry_matches`)
**Issue:** Member records carry no `canonical_line_content` (`score._MEMBER_EXCLUDED_KEYS`), so `covers[].code` is the first non-blank line of `current_code`. Lanes often quote context above the flagged line, such as a signature or an `if`. In that case the entry never equals the split-out row's canonical line, and D-09 silently stops working: the covered finding is asked again. This fails toward asking, but the D-09 promise only holds for one-line snippets, and the tests use only one-line `current_code`. It could also match a different line by the same agent, file and title if the quoted first line happens to be another flagged line.
**Fix:** Record the member's HEAD canonical line at decision time. The orchestrator already computes `canonical_line_content` for carried members in step 0, so have `score.py` keep it on the member, or on its obligation snapshot. Fall back to `current_code` only when it is absent. Add a multi-line-snippet fixture.

## Info

### IN-01: 90-finalize's newcomer rule doesn't match the code

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:26`
**Issue:** The doc says "no member with a different concern from a lane the decision did not cover". `newcomer_lanes` also reopens for a *covered* lane that adds a new title, because it tests the (agent, file, title) identity, not the lane. The `carry_state` docstring states this correctly.
**Fix:** Reword to "a member with a concern (lane + title) the decision did not cover and whose title is not a covered title".

### IN-02: 50-fix-loop says "Both render the same suffix" after adding a third `via`

**File:** `plugins/vibe-check/phases/review/50-fix-loop.md:54`
**Fix:** Change "Both" to "All three".

### IN-03: The decided-record relocation is checked only against a Python re-implementation in test code

**File:** `plugins/vibe-check/scripts/test_decision_continuity.py:107` (`relocate_decided`)
**Issue:** The end-to-end journey exercises the test's own simulation of the prose relocation, including moving the lead's own member ref. Drift between `30-collect-score.md` and this simulator is caught only by the phrase-lock tests, and a missed lead-member move produces a phantom row in production. This is inherent to prose-driven steps, but worth recording.
**Fix:** Phrase-lock the simulator's case list against the prose (one needle per case), or move relocation into a script helper that both use.

## Set aside (needs ruling)

### SA-01: The nearby window watches only the 5 lines *beneath* the flagged line

**Where:** `plugins/vibe-check/scripts/score.py:1379`, `carry_state.py` docstring (lines ~44-46)
**Why excluded:** The owner's discretion in CONTEXT allowed "literally Phase 56's 5-line-beneath window", and the implementation chose that.
**Effect if left as is:** The CONTEXT card example is "false positive, guarded upstream". Removing that upstream guard one line *above* the flagged line counts as a line shift (D-01), so the dismissal stays. The most common justification for a dismissal is therefore never re-checked when the code it rests on is deleted.
**Needs:** A ruling from the owner: keep beneath-only (accept), or widen to a symmetric window shared with the re-check trigger (in scope; one constant plus fixtures).

---

_Reviewed: 2026-10-26T19:44:31Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
