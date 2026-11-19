---
phase: 66-close-out-freshness
reviewed: 2026-11-18T00:00:00Z
depth: standard
scope: gap closure only (plans 66-10, 66-11, 66-12) — diff 651900003041a70c25ac464e90b805525df9b98e..HEAD -- plugins/
supersedes: earlier 66-REVIEW.md (CR-01, WR-01, WR-02 fixed per 66-REVIEW-FIX.md, status all_fixed)
files_reviewed: 6
files_reviewed_list:
  - plugins/vibe-check/scripts/worktree_snap.py
  - plugins/vibe-check/phases/review/30-collect-score.md
  - plugins/vibe-check/scripts/test_worktree_snap.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_nv_render.py
  - plugins/vibe-check/scripts/test_closeout_fresh.py
findings:
  critical: 1
  warning: 3
  info: 4
  total: 8
status: issues_found
---

# Phase 66: Code Review Report (gap closure 66-10..66-12)

**Reviewed:** 2026-11-18
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

> This report supersedes the earlier Phase 66 review. That review's CR-01, WR-01 and WR-02 were fixed per `66-REVIEW-FIX.md` (status `all_fixed`) and are not repeated here. This pass covers only the gap-closure changes (`git diff 65190000..HEAD -- plugins/`).

## Summary

The gap closure adds a third collect line, `REMOVED_LINE_RANGES=`, built by a new unified-diff parser (`removed_from_diff`). It also adds a prose rule that forces a re-ask when a decided record moves off a removed line, plus a test simulator, two-sided differentials against literal d5acc19, and mutation checks. All four target test files pass (419 passed, 1104 subtests). The test work is strong: the differentials load the literal d5acc19 code (checked by blob hash), both directions of the "only intended differences" check are themselves tested, and every mutant compares against the real code first. No test I checked is decorative.

Problems found:

- **The parser reports "known, nothing removed" for files git C-quotes.** With git's default `core.quotePath=true`, that is any non-ASCII file name. This brings back the exact silent keep this repair was meant to close (reproduced).
- **The forced pair re-asks unrelated decisions.** It goes into a shared map that `score.py` reads with a ±5-line window, so a neighbouring decided record whose code only shifted is also re-asked (reproduced). The prose says the stamp lands on "the moved record".
- **The simulator and the prose disagree on Needs-verification records.** The simulator records their moves; the prose excludes them.
- **The parser edge cases named in the brief are mostly untested.** Quoted paths, space/tab paths, no-newline markers, renames and binary files have no tests, which is how the first item got through.

## Critical Issues

### CR-01: `REMOVED_LINE_RANGES` silently drops C-quoted (non-ASCII) paths and prints "known, nothing removed", so shape 1 still keeps the decision

**File:** `plugins/vibe-check/scripts/worktree_snap.py:236-244` (`_old_path`), `:319` (diff call without `core.quotePath=false`)
**Issue:** `_old_path` returns `None` for any `--- "..."` header, and `_walk_removed` then records nothing for that file. The since-review diff runs without `-c core.quotePath=false`. With git's default `core.quotePath=true` (unset in this repo and in global config), every non-ASCII path is printed C-quoted: `--- "a/caf\303\251.py"`. The output is then a well-formed `{}` (or a map without that file), which the prose defines as "known, nothing was removed". A decided record in such a file that step 0 moves off its deleted line therefore is never forced, and the decision stays `current` on other code. That is the 999.44 shape 1 silent keep, unrepaired for these files.

Reproduced (scratch repo, `café.py` and `has space.py`, line 10 deleted in both):
```
removed_from_diff(text)                                   -> {'has space.py': [[10, 10]]}
forced_reask_pairs([{file:'café.py', stored_line:10, line:19}], removed) -> {}            # kept
forced_reask_pairs([...same...], None)                    -> {'café.py': [[19, 19]]}      # what unknown would do
```
The same codebase already knows about this: `closeout_fresh.py:62,288-292` runs every git call with `core.quotePath=false` for exactly this reason. The `diff_ranges.py` docstring assumes "names git had to escape … can never carry a finding", but nothing enforces it. Any finding reported on a non-ASCII-named file can be decided and carried. (`NEARBY_LINE_RANGES` has the same blindness, which predates this change. The new value adds a second false "known" signal on top.)
**Fix:** Do two things. Make the diff print raw names, and fail closed on any name that git still quotes, so the value becomes "unknown" (which re-asks) rather than "nothing removed":
```python
# worktree_snap.py, since_both
text = _git(root, ["-c", "core.quotePath=false", "diff", *DIFF_FLAGS, *ends, "--"], env=env)

# removed_from_diff: a quoted old-side header that is not /dev/null is unknowable
if line.startswith("--- "):
    raw = line[4:].rstrip("\t")
    if raw.startswith('"'):
        raise diff_ranges.RangeError(diff_ranges.REASON_NOT_A_DIFF)  # or a new fixed reason
    path = _old_path(line)
```
Add a real-git test with a non-ASCII file name and one with a `"`/control-character name: the first should list the removed line, the second should print both values empty. Note that the `core.quotePath=false` change also changes `NEARBY_LINE_RANGES` for non-ASCII files. That is a deliberate improvement, but it should be listed in the d5acc19 differential's intended differences.

## Warnings

### WR-01: The forced pair also re-asks unrelated decided records within ±5 lines of the relocated line

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:110`; simulator `plugins/vibe-check/scripts/test_decision_continuity.py:260` (`stamp_map_with_pairs`)
**Issue:** The forced re-ask inserts `[line, line]` into the shared `nearby_line_ranges` map. `score.py` (`_nearby_changed`, used via `_any_nearby` at `score.py:2871-2907`) stamps `snapshot.nearby_at` on every record whose line is within `_NEARBY_LINES` (5) of any range. Any other decided record near the copy's location is therefore re-asked, even when its own code only shifted. The prose's "Why" says "`score.py` stamps `snapshot.nearby_at` on the moved record", which is not the actual effect.

Reproduced with the real simulator and scorer. A is decided at line 10 with a copy at old line 50. B is decided at old line 53 with different text. Line 10 is deleted, so B only shifts to 52:
```
forced : removed {'src/a.py': [[10,10]]}  nearby sent {'src/a.py': [[9,10],[49,49]]}
         A @49 nearby_at=2   B @52 nearby_at=2   gate outstanding-to-phase-5
2.15   : A @49 nearby_at=None B @52 nearby_at=None gate write
```
B's re-ask is collateral. It errs toward asking again (it never silently keeps a decision), but the owner is shown a decision as changed when its code did not change. No test or differential scenario covers a second decision near the copy, so the side effect is invisible to the "only intended differences" guarantee.
**Fix:** Pick one of two options:
- Keep score.py untouched and document the side effect in the forced re-ask paragraph and in the 999.44 record. Add a grid scenario (a decided neighbour within 5 lines of the relocated line) to `SHAPE1_GRID`/`SHAPE1_INTENDED` so the extra re-ask is an explicit, locked difference.
- Add a narrow per-hash envelope key (for example `force_reask_hashes`) so only the moved record is stamped. This changes score.py and needs an owner ruling against the "score.py byte-identical to d5acc19" constraint.

### WR-02: The new diff parser's risky inputs are untested (quoted, space/tab, no-newline, rename, binary, mode-only)

**File:** `plugins/vibe-check/scripts/test_worktree_snap.py` (`TestRemovedFromDiff`, `TestRemovedMutants`)
**Issue:** `TestRemovedFromDiff` covers deletions, replacements, insertions, whole-file add/delete, header look-alike body lines and context widths, and those are good. It has no case for:
- a C-quoted path (CR-01 got through because of this);
- a path containing a space, which git prints with a trailing `\t` (`_old_path` strips it; I checked by hand that it works, but no test locks it);
- a `\ No newline at end of file` marker inside a hunk that also deletes lines (the budget-skip branch at `_walk_removed` `tag == "\\"`);
- a rename with edits (keying on the old path, which depends on the user's `diff.renames`);
- a binary or mode-only change (no hunk).

No mutant targets the trailing-tab strip, the `"` check or the `\` skip, so any of them could be removed without a failing test.
**Fix:** Add real-git cases to `_changes()`/`TestRemovedFromDiff` for each input above, with expected values (quoted path: both values empty after the CR-01 fix; space path: `{"has space.py": [[n, n]]}`; no-newline: the deleted last line listed; rename: keyed by the old path, or a full-file removal under `--no-renames`; binary/mode-only: `{}`). Add mutants that drop the `\t` strip and the `\` skip.

### WR-03: The simulator records Needs-verification moves in `$MOVED_DECIDED`; the prose excludes them

**File:** `plugins/vibe-check/scripts/test_decision_continuity.py:126-166` (`relocate_decided`), `:182-217` (`next_cf` move recording); prose `30-collect-score.md:55`
**Issue:** The prose fills `$MOVED_DECIDED` only from the decided-records paragraph, which applies "when the record's band is not `needs-verification`". The simulator's `relocate_decided` never checks `band`, and `next_cf` now appends every move it returns to `moves`. A decided Needs-verification record that relocates would therefore get a forced pair in the simulator but not under the prose, so the two answer differently on the same input. None of the current fixtures carries a decided NV record, so no test catches it today. This is exactly the kind of quiet prose/simulator drift that `test_simulator_matches_locked_prose` is meant to prevent.
**Fix:** In `next_cf`, record a move only when `e.get("band") != "needs-verification"`, and do the same for members. Alternatively, make `relocate_decided` return the stored line for an NV band, matching the prose. Then add one fixture with a decided NV record moved off a removed line that asserts the prose's behaviour, whichever the owner rules it should be (see SA-01).

## Info

### IN-01: `since()` is now a wrapper with no caller

**File:** `plugins/vibe-check/scripts/worktree_snap.py:326-329`
**Issue:** `collect` now calls `since_both` directly. A search of the scripts and their tests finds no remaining caller of `since()`.
**Fix:** Remove it, or note in its docstring which external caller keeps it alive.

### IN-02: The `collect` docstring still says "with both empty"

**File:** `plugins/vibe-check/scripts/worktree_snap.py:452`
**Issue:** The rest of the docstring was updated to "ALL values"/three lines, but this sentence still reads "with both empty, this pass and the next stamp from changed_line_ranges".
**Fix:** Change it to "with all three empty".

### IN-03: Diff output depends on the user's `diff.renames` / copy-detection config

**File:** `plugins/vibe-check/scripts/worktree_snap.py:114-115` (`DIFF_FLAGS`), `:319`
**Issue:** `DIFF_FLAGS` does not pin rename handling. With `diff.renames=copies` in the user's config, a copy target's hunks are listed as removals from the unchanged source path. That forces re-asks on pure shifts in the source file. It errs toward asking again, but whether a re-ask happens then depends on the machine running the review.
**Fix:** Add `--no-renames` to the since-review diff, so a rename shows as a whole-file delete plus add (and a carried record on the old path fails closed). Alternatively, document the dependence.

### IN-04: Cross-module use of `diff_ranges` private helpers

**File:** `plugins/vibe-check/scripts/worktree_snap.py:255-282`
**Issue:** `removed_from_diff` and `_walk_removed` use `diff_ranges._count`, `_merge`, `_split_lines`, `_HUNK` and the `REASON_*` constants. A refactor of `diff_ranges` (whose stated contract is only `ranges_from_diff`) could break `worktree_snap` without warning. Separately, the body-walk logic is duplicated between the two modules.
**Fix:** Move `removed_from_diff` into `diff_ranges.py` as a second public contract function (it is pure and needs only `re`), or promote the shared helpers to public names.

## Set aside (needs ruling)

### SA-01: Decided Needs-verification records are outside the forced re-ask

**Where:** `plugins/vibe-check/phases/review/30-collect-score.md:55,110`
**Why excluded:** The gap plans scope the repair to decided ordinary records. NV relocation is designed to follow the recorded snippet ("a move to another file can preserve the failure"), so following the text may be the intended behaviour for NV.
**Effect if left as is:** Suppose the owner defers or dismisses an NV item, then its snippet's lines are deleted while an identical snippet exists elsewhere (likely with a one-line snippet). The NV fingerprint is confirmed at the copy and the decision is kept without asking.
**Needs:** A ruling from the developer on whether a decided NV record moved off a removed line should be re-asked (in scope) or follow its text (accept). Resolving WR-03 depends on this.

### SA-02: Step 0 can relocate to a nearer pre-existing identical line while the original only shifted

**Where:** `30-collect-score.md` step 0 case 2; `test_decision_continuity.py:126` (`relocate_decided`)
**Why excluded:** It needs two identical lines with the same title, which already share one `stable_hash` (D-21 / 999.31 identity, out of scope by the roadmap).
**Effect if left as is:** Example: the decided text is at old line 10 and also at old line 8. Three lines are inserted at the top, putting the original at 13 and the copy at 11. The copy is nearest-unique to stored line 10, so the decision moves to it. Old line 10 was not removed, so nothing is forced, and the edit is more than 5 lines away, so there is no nearby stamp. The decision is kept on other code. The removal evidence could rule this out cheaply: the diff gives where old line 10 went, so a move to any other line could be forced.
**Needs:** A ruling: accept as part of the 999.31 identity limit, or extend the forced rule to "relocated line ≠ the stored line's new-side position".

---

_Reviewed: 2026-11-18_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
