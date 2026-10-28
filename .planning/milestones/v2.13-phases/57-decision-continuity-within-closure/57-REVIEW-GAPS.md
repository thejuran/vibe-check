---
phase: 57-decision-continuity-within-closure
scope: gap-closure (git diff 57e93d7..HEAD, plans 57-08..57-13)
reviewed: 2026-10-26T22:07:52Z
depth: standard
files_reviewed: 14
files_reviewed_list:
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
  - plugins/vibe-check/scripts/test_score.py
  - plugins/vibe-check/scripts/test_verified_fixes.py
findings:
  critical: 1
  warning: 2
  info: 5
  total: 8
status: issues_found
---

# Phase 57: Code Review Report (gap closure 57-08..57-13)

**Reviewed:** 2026-10-26T22:07:52Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Scope: the gap-closure diff `57e93d7..HEAD`. The 8 reviewed test modules pass (1028 tests, 1074 subtests). I mutation-tested 11 of the new guards against the full reviewed suite, and every mutant was killed:
- CR-01 skip
- inherited joined
- inherited nearby
- legacy entry with no lanes
- legacy entry band fallback
- covered_count lead-title discard
- member lanes
- concern_lanes title filter
- line-1 clip
- above-window width
- card `was_band` source

Closure status of the four first-review findings:

| Finding | Status | Evidence |
|---|---|---|
| CR-01 (row decision covered a separately-owed member) | **Closed** | `_covers_of` skips a member whose obligation hash differs from the row's. Fixture g1 reproduces the original case, and the mutant is killed. |
| CR-02 (inherited decisions skipped reopen rules) | **Partly closed** | The band-rise and joined checks now run on the inherited path. The nearby check runs too, but the scorer never stamps `nearby_at` on the pass where a covered member splits into its own row. A split is usually *caused* by an edit next to the member (the lead's fix), so that edit is lost. See CR-01 below. |
| WR-02 (a deletion-only hunk never stamps `nearby_at`) | **Closed only under `-U0`** | The new range rule reads hunk headers, but the scope phase produces default `git diff` output (3 context lines). Under that format the `+T,0` branch never fires, and context lines enter the ranges. See WR-01. |
| WR-03 (row-wide lanes) | **Closed** | `lanes` is now per-concern, matched on exact title. A same-concern report from a lane that words the title differently re-asks as "joined" (fails toward asking; IN-05). |

`covered_count` by title, the legacy fallbacks and the symmetric window look correct for the shapes the scorer writes. The parked items (WR-01, WR-04 and IN-03 in the first review) are not made worse by the gap changes.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: An edit next to a covered (or separately decided) member is never seen on the pass where that member splits into its own row, so the decision stays closed

**File:** `plugins/vibe-check/scripts/score.py:2659-2660` (survivor snapshot), `:306-337` (`_snapshot_for` stamps `nearby_at` only when the row arrives with a prior snapshot); consumed by `plugins/vibe-check/scripts/carry_state.py:804-810` (`_nearby_since`) and `:821-843` (`_inherited_cause`)

**Issue:** D-16 says an inherited decision reopens on a nearby edit. D-14 says an edit within 5 lines above or below re-asks.

When a covered member splits out of its decided row, it becomes a new survivor. A covered member has no obligation, so its working record has no `snapshot`. `_snapshot_for(..., nearby=True)` stamps `nearby_at` only when a prior snapshot dict exists ("only on a row that existed before this pass"). So the split row gets a fresh snapshot with no `nearby_at`, and `_nearby_since` is false. Later passes stamp only edits made *in those passes*, so the split-pass edit is lost for good.

The usual cause of a split is an edit near the member: the lead's line is fixed and resolved. That edit is within the member's window, so in the common case the inherited decision closes silently even though the D-14/D-16 rule says it must be re-asked.

The same mechanism affects a member that has its **own** decision. A decided record absorbed as an obligation member, then split out by a nearby edit, gets a fresh snapshot with no `nearby_at`. `evidence.nearby_at == current.nearby_at`, so it stays `current`.

Reproduced on the real chain (`score.run -> append_pass -> carry_state`, harness from `test_decision_continuity.py`):

```
# Inherited case (split_scenario, but with the REAL diff that rewrote B's line 12)
pass 1: row B (security, line 12) with covered member A (bugs, line 10); owner dismisses B
pass 2: line 12 rewritten, B re-check -> resolved, changed_line_ranges {F: [[12, 12]]}
  A snapshot: {'at_pass': 2, ..., 'line': 10, 'band': 'warning'}   # no nearby_at
  score._nearby_changed(A, {F: [[12, 12]]}) -> True
  decision_state(A) -> 'current'; outstanding_cw_hashes -> []; A not on the card
pass 3: unrelated edit at line 13 -> nearby_at 3 -> 'stale'  (only a SECOND edit re-asks)

# Own-decision case
pass 1: A dismissed (own decision hA)
pass 2: critical B at line 12 absorbs A as an obligation member (A still 'current')
pass 3: B fixed and resolved, diff {F: [[12, 12]]} -> A is its own row again
  A snapshot has no nearby_at; decision_state(A) -> 'current'; outstanding_cw_hashes -> []
```

The fixtures hide this. `split_scenario` says: "The diff omits B's rewritten line so the nearby-change rule (D-02) does not confound the inheritance check". The `TestGapClosure57` inherited rows are hand-built with a pass-1 prior snapshot, a shape the scorer never writes for a newly split row. See WR-02.

**Fix:** Stamp `nearby_at` on a survivor that came from a carried record even without a prior snapshot. One option is to key on the source member's carry status, since a covered member is expanded as `persisted`/`needs-recheck` and is never `new`:

```python
# score.py, threshold loop
nearby = _nearby_changed(survivor, changed_line_ranges)
carried_src = any(m.get("status") in ("persisted", "needs-recheck")
                  for m in sources)
survivor["snapshot"] = _snapshot_for(survivor, pass_number, nearby=nearby,
                                     carried=carried_src)
# _snapshot_for: stamp when nearby and (isinstance(prior, dict) or carried)
```

For the own-decision sidecar case, also seed the survivor's prior snapshot from `obligation.snapshot` when `best_member` carries an obligation. This mirrors the existing `same_hash_prior` path.

Add both reproductions above as fixtures. Use `split_scenario` with `ranges={F: [[12, 12]]}`, expect `stale`/`nearby`, and add a mutant that drops the `carried` arm.

See SA-01: this fix changes how often D-09 holds in practice.

## Warnings

### WR-01: The new range rule is only right for `--unified=0` diffs. The scope phase emits default 3-context diffs, so the `+T,0` rule never fires and unchanged context lines become "changed"

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:64`; diff sources at `phases/review/00-scope.md:36-37,51` (`git diff HEAD`, `git diff --staged`, `git diff <range>`, `gh pr diff --patch`)

**Issue:** The new bullet says to build ranges from "each hunk's new-side header `+start,count`". None of the diff commands the orchestrator runs pass `-U0`, and nothing in the plugin mentions `--unified`. In default output, every hunk header counts 3 context lines on each side:

```
seq 1 30 > a; sed '9d' a > b
git diff --no-index a b      -> @@ -6,7 +6,6 @@   -> range [6, 11]  (6 unchanged lines)
git diff --no-index -U0 a b  -> @@ -9 +8,0 @@     -> range [8, 9]
```

Effects:
1. **Dead rule.** Under the diffs the orchestrator actually reads, a deletion-only hunk never has a `+T,0` header, so the WR-02 rule never fires. The guard deletion is caught only incidentally, through context lines.
2. **Wider nearby window.** Context lines count as changes, so `nearby_at` and the Phase 56 re-check trigger reach about 8 lines from the edit, not 5. A decided finding 6–8 lines from an edit is re-asked, which contradicts D-03 and D-14 ("6 above/below keeps") and the "never re-ask without new evidence" rule.
3. **Score inflation.** `in_diff` reads the same ranges, so findings on unchanged context lines get the +20 term. That can lift a finding over the threshold or raise its band; a warning can become a critical that blocks finalize.

Even under `-U0`, the `[max(T,1), T+1]` rule marks the two unchanged lines around a deletion as `in_diff`. `test_r8_guard_deleted_directly_above_reopens` documents the effect: "the scorer's changed-line scoring lifts the band (warning -> critical)" on an unchanged line.

**Fix:** In the bullet, require zero-context hunks, for example "read the hunks of `git diff --unified=0 …` (for PR mode, recompute with `-U0` or count only `+` lines)". Alternatively, derive ranges from `+` lines plus deletion points, not from header counts.

Consider keeping the deletion-point lines out of `in_diff`: pass them as a separate `deleted_at` list that only `_nearby_changed` reads. That way the D-14 re-ask does not also inflate scores. Add a phrase lock for the zero-context requirement next to `DELETION_RANGE_PHRASES`.

### WR-02: The inherited-path fixtures use shapes the scorer never writes, so they cannot catch CR-01

**File:** `plugins/vibe-check/scripts/test_decision_continuity.py:645-676` (`split_scenario`), `plugins/vibe-check/scripts/test_carry_state.py:2494-2506` (`_inherited_pass2`), `:2398-2406` (`g_row`)

**Issue:** The inherited tests are not realistic about the split pass:
- **`split_scenario` drops the diff.** It deliberately sends `ranges={F: []}` even though line 12 was rewritten. The only realistic diff it uses (`edit_a=True`) edits A's own line, which re-hashes A and never reaches the inherited path.
- **`_inherited_pass2` invents a prior snapshot.** It builds row HC with `g_snap(at_pass=1, ...)`. A newly split row from `score.run` has a fresh snapshot at the split pass and no prior. So "inherited reopens on nearby" is only tested on a synthetic row that already carries a stamp.

The 57-09 `ba_row_state` rebuild itself is sound: its fixtures assert the shapes their names claim, and the per-concern exclusion (`perf` on attribution only) is exercised. The weakness is the inherited/split shape.

**Fix:** Add an end-to-end inherited-nearby fixture that runs `split_scenario` with the real diff (`{F: [[12, 12]]}`) and asserts `stale`/`nearby` (red today; see CR-01). Assert the split row's snapshot shape (`'nearby_at' in snapshot`) instead of hand-writing it.

## Info

### IN-01: The card and the comparator disagree on an inherited entry whose `band` is null

**File:** `plugins/vibe-check/scripts/carry_state.py:813-818` vs `plugins/vibe-check/scripts/batch_card.py:182-185`
**Issue:** `_inherited_was_band` uses `entry["band"]` whenever the key exists, even when it is `None`, and so re-asks with cause `severity`. The card falls back to `decision["band"]` unless the value is a str. `_covers_of` writes `band: None` when the row band is not a str, so in that case the card prints "severity changed (warning → …)" for a comparison that was made against an unknown band.
**Fix:** Use the same predicate in both: `isinstance(entry.get("band"), str)` in `_inherited_was_band`, or expose `carry_state.inherited_was_band()` and have the card read it.

### IN-02: `covered_count` by title merges distinct concerns that share a generic title

**File:** `plugins/vibe-check/scripts/carry_state.py:715-733`
**Issue:** Two different covered concerns that happen to share a title are counted once. Example: lane `bugs` "Missing null check" at line 10, and lane `security` "Missing null check" at line 11. The card under-counts the dismissed findings. This is presentation only; nothing closes.
**Fix:** Count distinct `(title, code)` pairs from the matched `covers` entries, or accept the risk and say so in the docstring.

### IN-03: `_covering` picks the first matching decision in sorted-hash order, which now decides keep vs ask

**File:** `plugins/vibe-check/scripts/carry_state.py:776-785`
**Issue:** Now that the matched entry's `band`, `lanes` and the decision's `at_pass` drive the reopen, the choice among several covering decisions matters. Which one wins depends on hash order, not recency, so an older decision taken at a higher band can mask a rise against a newer one. The setup needs re-decided overlapping rows, so this is unlikely.
**Fix:** Prefer the covering decision with the highest `at_pass`, with hash order as the tie-break.

### IN-04: A replace hunk with net deletion does not get the deletion-point treatment

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:64`
**Issue:** Under `-U0`, `@@ -10,3 +10,1 @@` maps to `[10, 10]`. The removed lines sat between new-side lines 10 and 11, but line 11 is not covered the way the pure-deletion rule covers `T+1`. A flagged line exactly 5 below line 11 (line 16) misses the window by one.
**Fix:** For hunks with `old_count > new_count`, also add `start + new_count` (the line after the hunk), or adopt the `deleted_at` list suggested in WR-01.

### IN-05: The D-05 "now also reports it" path needs byte-identical titles across lanes

**File:** `plugins/vibe-check/scripts/carry_state.py:525-545` (`concern_lanes`)
**Issue:** Corroboration counts only when another lane's title equals the record's exactly. Separate lanes word their titles independently, so a second lane confirming the same defect usually shows up as a newcomer instead. The card then says "a new concern from X joined it" when X is corroborating. This fails toward asking, so it is not a wrong-keep, but the D-05 card wording will rarely appear.
**Fix:** Document it as known behaviour, or match on `(file, line, category)` in addition to title.

## Set aside (needs ruling)

### SA-01: Applying D-14/D-16 strictly to splits will make D-09 inheritance rare in practice

**Where:** `plugins/vibe-check/scripts/score.py:2659-2660`; `plugins/vibe-check/scripts/carry_state.py:821-843`
**Why excluded:** This is a product-rule tension, not a code defect. A covered member usually splits out because its lead was fixed a line or two away, and that fix is a "nearby edit" under D-14. Once CR-01 is fixed, most split members will be re-asked instead of silently inheriting (D-09).
**Effect if left as is:** Today the inherited decision holds through the very edit that caused the split, which is a silent keep that contradicts D-16. After the fix, the owner will see more re-asks of members whose own code did not change.
**Needs:** A ruling from the owner. Either (a) a nearby edit on the split pass re-asks (strict D-16; implement CR-01 as written), or (b) the lead's own resolved line is exempt from the member's nearby check on the split pass. Option (b) must be written down as an explicit exception to D-14 and given its own fixture.

---

_Reviewed: 2026-10-26T22:07:52Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
