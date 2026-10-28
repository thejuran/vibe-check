---
phase: 57-decision-continuity-within-closure
reviewed: 2026-10-26T00:00:00Z
depth: standard
scope: "git diff 70346c2..HEAD -- plugins/ (plans 57-17..57-19)"
files_reviewed: 2
files_reviewed_list:
  - plugins/vibe-check/scripts/score.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
findings:
  critical: 2
  warning: 2
  info: 1
  total: 5
status: issues_found
---

# Phase 57: Code Review Report (third gap closure, 57-17..57-19)

**Reviewed:** 2026-10-26
**Depth:** standard (with real-chain repros against `score.run` + `carry_state`)
**Files Reviewed:** 2
**Status:** issues_found

## Summary

57-18 fixed the specific shapes that rounds 1-3 found: a fresh record at the **same line** as the carried twin now inherits carried-ness and the prior snapshot. The suite is green (62 passed, 76 subtests). The convention check found nothing.

**The root cause is not gone.** It was moved, not removed. The rule now reads carried evidence from "any same-hash record **in `scored_members`**". However:

1. **The nearby test still reads only the lead's line.** The prior seed is first-match-wins in score order, not the most conservative choice.
2. **Only records that reach `scored_members` count.** A carried record removed before grouping (min_confidence) is invisible.

Both still produce a silent wrong-keep that depends on which record leads (or on arrival order). Each is reproduced below with the test file's own harness.

## Structural Findings (fallow)

No structural pre-pass was provided.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Same-hash records at different lines: whether the owner is re-asked depends on which record leads (and, within one lane, on arrival order)

**File:** `plugins/vibe-check/scripts/score.py:2609-2618, 2693-2697` (seed first-wins; `_nearby_changed(survivor, ...)` on the lead's line only); sort tie-break `score.py:2547-2553`

**Issue:** `stable_hash` contains no line number. So two records with identical line text and the same title at lines 10 and 12 (for example `return None` twice) are one hash and fall in one group. Row-level `nearby` is computed only at the **lead's** line. A carried same-hash record at another line owes the re-ask in two places: on its own obligation snapshot, and through D-14 by its own line. Neither reaches the row snapshot:

- If the row already has a snapshot (a carried lead), the seed is skipped entirely.
- If the lead is fresh, the seed takes the **first** same-hash obligation in score order. It does not take the one with the latest `nearby_at`.

`carry_state._check_state` (carry_state.py:333-339) keeps the **row** and discards any member sidecar with the same hash. So the stamp on the member's obligation is dead.

Repro 1, cross-lane: carried decided `bugs`@12, fresh `security`@10 with the same title and text, diff `[[17,17]]`, which is inside line 12's window and outside line 10's.
```
sec_conf 60  lead bugs 12     rowsnap {... 'line': 12, 'nearby_at': 2}  -> decision_state stale/nearby
sec_conf 100 lead security 10 rowsnap {... 'line': 10}  (no nearby_at)  -> decision_state current
             member bugs 12 obligation snapshot {... 'nearby_at': 2}   (ignored by carry_state)
```
Repro 2, same lane, identical fresh input. Only the order in which the agent returned the two findings changes:
```
order [10,12] -> lead line 10, snapshot at_pass 1, no nearby_at -> current   (wrong-keep)
order [12,10] -> lead line 12, nearby_at 2                      -> stale
```
For two same-agent, same-hash records the sort key ties completely, so Python's stable sort keeps arrival order. This contradicts the comment at score.py:2544 ("the pick never depends on arrival order") and the 57-18 docstring ("Which record leads never decides the stamp", score.py:328).

**Fix:** Make the row's evidence a merge over every same-hash record, not a pick:
```python
same_hash = [m for _, m, d, _, _ in scored_members
             if stable_hash(m.get("file",""), d["canonical_for_hash"], m.get("title","")) == survivor["stable_hash"]]
nearby = any(_nearby_changed(m, changed_line_ranges) for m in same_hash)
# prior: merge the lead's own snapshot with every same-hash obligation snapshot,
# keeping the latest nearby_at (fail toward asking), never first-wins.
```
Carry `nearby` through `survivors` alongside `row_carried`. Add `_as_line(line)` as a final sort tie-break so the lead is deterministic. Add a different-line, same-hash shape (both variants above) to `INVARIANCE_SCENARIOS`.

### CR-02: A carried twin removed before grouping (min_confidence) takes its carried-ness with it; a fresh re-report then hides the re-ask

**File:** `plugins/vibe-check/scripts/score.py:2609-2627` (both reads iterate `scored_members`), `score.py:2384-2398` (min_confidence drop), `score.py:422-424` (`_kept_open_rows` suppressed by the visible hash)

**Issue:** `row_carried` and the seed look only at `scored_members`. The min_confidence filter (and any `_score_member` drop) removes the carried record before grouping. The carried record is added to `dropped`, but `_kept_open_rows` suppresses it because the fresh row already makes hash H visible. The row is then all-fresh: no seed and no `carried`, so the edit next to the finding is not stamped.

Repro: pass 1 `bugs` A, conf 75, dismissed. Pass 2: line 12 edited (inside A's window), the owner has raised `min_confidence` to 80, and A's lane re-reports at conf 95.
```
min_conf None, re-report  -> nearby_at 2, status new        -> stale     (correct)
min_conf 80,   re-report  -> no nearby_at, status new       -> current   (WRONG-KEEP)
min_conf 80,   no report  -> kept-open, nearby_at 2         -> stale     (correct)
```
A re-report that adds evidence silently removes the re-ask, which is the exact defect class of rounds 1-3.

**Fix:** Build a `carried_by_hash` index (current hash → carried working records, obligations included) right after the carry loop, **before** the NV/min_confidence filters. Read `row_carried` and the merged prior from that index, not from `scored_members`. When a dropped carried record's hash is made visible by a fresh row, fold its snapshot into that row's prior.

## Warnings

### WR-01: The lead-order invariance guard is narrower than its claim ("every row shape the phase cares about")

**File:** `plugins/vibe-check/scripts/test_decision_continuity.py:1204-1312`

**Issue:** Every permutation moves the lead only by changing the confidence or severity of a fresh record **at the carried record's own line**. So the nearby window and the identity are the same in every permutation. None of the following is permuted:
- a different line with the same hash (CR-01),
- arrival order,
- a carried twin filtered before grouping (CR-02).

All three still flip the outcome. The marker self-checks are real (the lead does move), so the test is not decorative. Its coverage claim, though, is what let CR-01 and CR-02 through. `test_guard_covers_every_scenario_the_phase_cares_about` locks the set at exactly six names. That makes adding the missing shapes a deliberate edit, not an automatic failure.

**Fix:** Add the `different_line_same_hash_cross_lane`, `same_lane_arrival_order` and `min_confidence_dropped_twin` scenarios from the CR repros. For arrival order, permute the order of the `findings` list, not the scores.

### WR-02: (57-19 parked observation) A covered member that drops below threshold on its split pass is lost, not filtered by design. A deferred item is closed without a card.

**File:** `plugins/vibe-check/scripts/score.py:2684-2692` (sub-threshold drop adds to `dropped` only `carried_obligations` members); `score.py:2309-2324` (a covered member never had a row, so it has no obligation)

**Issue:** Reproduced on the parked shape (`}`-line member, conf 75, covered by row B; B resolved by recheck; diff `[[12,12]]`) for both decision kinds:
```
dismiss: findings [] ; filtered [{... 'reason': 'sub-threshold'}] ; record_of(hA) None ; finalize outstanding 0
defer:   findings [] ; filtered [{... 'reason': 'sub-threshold'}] ; record_of(hA) None ; finalize outstanding 0
```
**Classification:**
- **Under `dismiss`:** this is intended threshold behaviour. An identical fresh finding also stays hidden (it surfaces 0 times), and the owner had already dismissed it.
- **Under `defer`:** this is silent finding loss. It is one of the four classes in the scope-discipline rule.

The owner asked to come back to the item. It leaves the open set with no card, no kept-open row, and a generic `sub-threshold` reason that does not name the covering decision. A carried **row** in the same situation stays open (D-02 kept-open), so the outcome depends on whether the record ever led a row. The failure direction is "keep, not ask" for the dismissal, but "lose" for the deferral.

**Fix:** When a sub-threshold row's sources include a covered member whose covering decision is still recorded, emit a kept-open row under the covering hash. Or, at minimum, use a filtered reason that names the covering decision (`"sub-threshold; covered-by: <hash> (defer)"`). Whether "defer" must keep it open is a product ruling for the owner. Backlog it with the defer repro above as the acceptance fixture.

## Info

### IN-01: A carried lead's own snapshot is used as the prior without the hash-equality check that the seed and w2 enforce

**File:** `plugins/vibe-check/scripts/score.py:2584, 2609` (`survivor = dict(best_member)` carries the old `snapshot`; the seed is skipped)

**Issue:** When a carried lead's own line is edited, it re-hashes (H→H'), but its old snapshot is still the prior. `_snapshot_for` then carries the old `nearby_at` onto the new hash. Repro (quiet diff): new row `c28a20d6` gets `nearby_at: 2`, inherited from the old hash. This is inert in practice: any decision on H' is made at a pass ≥ 3, so stamp 2 can never be later than it. But it contradicts the comment "the seed never carries a foreign stamp" (score.py:2606) and the w2 contract, which is only enforced for member sources.

**Fix:** Pop `survivor["snapshot"]` when `survivor["stable_hash"] != best_member.get("stable_hash")` (that is, when the lead's stored hash differs), so that every prior source passes the same hash gate. Otherwise, narrow the comment.

## Mutant audit (priority 4)

All four new mutants, and the edited 57-15 mutant, target unique shipped lines (`src.count(old) == 1` is asserted). Each runs against the unmutated scorer first (`_failures() == set()`). Extra check: dropping the hash-equality conjunct from `row_carried` is caught by `test_s4_` (verified by running the mutant). There is no mutant for seed `break`/first-wins. That gap is consistent with CR-01: no test distinguishes which same-hash snapshot wins.

## Set aside (needs ruling)

None.

---

_Reviewed: 2026-10-26_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
