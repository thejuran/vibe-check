---
phase: 60-exact-change-evidence-and-reliable-finalize
reviewed: 2026-10-30T19:37:04Z
depth: standard
scope: third gap-closure round (60-14..60-16), diff 2de0fc9..HEAD (129c69e)
files_reviewed: 5
files_reviewed_list:
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_diff_ranges.py
  - plugins/vibe-check/scripts/test_finalize_card.py
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 60: Code Review Report (third gap round)

**Reviewed:** 2026-10-30T19:37:04Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

This round targets the two gap-round-2 findings (`e90c6a7` numbering): WR-01, where the step-3 post-answer recount reused the pre-card BLOBFILE, and WR-02, where the `head_sha` bind fence wedged `--finalize`. Both target fixes hold:

- **90-finalize.md step 3 (WR-01).** The step now runs step 1 again: a new mktemp fence prints a NEW `BLOBFILE=`, the fingerprints are rebuilt from HEAD, the index and the working tree, and the counts are recomputed on that literal. Then a NEW `GATEFILE=` is made and the gate runs once. The claim "the fingerprints have not changed" is gone. The wording matches the rebuild-once paragraph, and the rebuild-once rule is unchanged. The "stop and write nothing" rule still holds before `record-decisions`. After `record-decisions` it is still undefined, which is the carried R24.
- **05-state.md bind fence (WR-02).** The fence fails closed. Only the literal `1` skips it. When the literal is `0`, empty, or not substituted, the fence falls through to `last-head-sha` validation. Review mode still refuses the CR-01 `$(...)` payload, `HEAD` and uppercase hex.
- **Mutation checks.** Each check was run in a scratch worktree and then discarded:
  - Reverting 90-finalize.md to `2de0fc9` makes 9 tests fail.
  - Reverting 05-state.md to `2de0fc9` makes 18 fail.
  - Changing the guard to `[ -n "$FINALIZE_MODE" ]`, which is truthy on `0`, makes 4 fail.
  - Changing the guard to `!= "0"`, which skips when the literal is not substituted, makes 10 fail.

  So the new guards are not decorative.
- **Test suite.** Bare `pytest -q` on the three changed test files gives 374 passed and 435 subtests passed.

The one new WARNING is a side effect of the WR-02 fix. In finalize mode the fence now prints no `LAST_REVIEWED_SHA=` literal. Phase 0.5 step 3 (the incremental range) still requires that literal and has no finalize exemption. This holds even for a valid state file, so every `--finalize` run now reaches a step whose only allowed input does not exist.

All findings below are **new** this round. The gap-round-2 items not fixed here are already recorded as residuals R22–R26 in 60-REPRO.md. They are listed under "Carried" and not counted again.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01 (new): Finalize mode now leaves Phase 0.5 step 3's `<last-reviewed-sha>` unbound, so the only way to fill it is the hand copy the CR-01 fix banned

**File:** `plugins/vibe-check/phases/review/05-state.md:54-63` (the skip), `:96-97` (step 3), `:99` (step 4)

**Issue:** Before this round, the bind fence always either printed `LAST_REVIEWED_SHA=<sha>` or halted. Step 3's range source `git diff … "<last-reviewed-sha>"` therefore always had a literal to substitute, on `--finalize` too.

With the `FINALIZE_MODE=1` skip, a finalize run prints no `LAST_REVIEWED_SHA=` line, even when the state file's `head_sha` is valid. Step 3 ("Narrow diff to incremental … the literal printed after `LAST_REVIEWED_SHA=` … substitute it") has no finalize exemption. Step 4 actually assumes the "incremental diff empty" check is evaluated on a finalize run: "A `FINALIZE_MODE=1` run never stops here". The spine (`commands/review.md:99`, `deep-review.md:108`) exempts only Phase 0.5's "routing into Phase 0.7, Phase 1 or the carry-forward steps". Step 3 is a computation, not routing.

An agent following the prose therefore reaches a step whose required input does not exist. It has three ways forward:
1. Skip step 3. This is benign, but no text tells it to.
2. Run `git diff … ""` or leave the placeholder unsubstituted. Git errors, and nothing defines how finalize treats that error.
3. Fill the placeholder from `state.passes[-1].head_sha` by hand. This is exactly what line 63 forbids, because a crafted value such as `"$(touch …)"` executes inside the double-quoted argument.

The CR-01 guard was made sufficient by forcing every consumer through the printed literal. On finalize runs that literal no longer exists, and the prose gives no compliant path.

The fix's own remedy line says "--finalize does not read this value and still works". That depends on step 3 being skipped, and the prose never says it is.

Graded WARNING, not BLOCKER. Option 3 requires the agent to break an explicit ban. A crafted state file also normally sits under the gitignored `.turingmind/`. The effect is still a non-deterministic step on every `--finalize`, and one of its branches reopens CR-01.

**Fix:** State the exemption where the literal is consumed, and lock it with a needle in `head_sha_binding_holds`, plus a mutant that removes it:
```markdown
3. Narrow diff to incremental: … (skip on a `FINALIZE_MODE=1` run — the step-2 fence printed no
   `LAST_REVIEWED_SHA=` literal there, Finalize reads `$STATE_FILE`, not the diff, and nothing
   may stand in for the literal; never copy `head_sha` from the state JSON to fill it).
```
Then reword step 4's finalize sentence so it does not imply step 4 evaluated an incremental diff: "A `FINALIZE_MODE=1` run does not compute the incremental diff (step 3) and never stops here."

## Info

### IN-01 (new): The halt's remedy offers "restore the state file from git", but the plugin tells owners to gitignore `.turingmind/`

**File:** `plugins/vibe-check/phases/review/05-state.md:59` and `:63`; `plugins/vibe-check/scripts/test_diff_ranges.py` (`HEAD_SHA_HALT`, `test_halt_names_a_remedy`)

**Issue:** `07-first-run.md:21-23` tells every owner to add `.turingmind/` to `.gitignore` ("working state, not artifact"). The state file lives at `.turingmind/state/format-53/…`, so in the recommended setup there is no git copy to restore. The remedy also says "the full 40-hex sha". `last-head-sha` accepts only lowercase ids, and in a SHA-256 repository it requires 64 hex digits. An owner who pastes an uppercase sha, or a 40-hex value in a SHA-256 repo, re-runs into the same halt.

The remedy does not send the owner into the same halt in the common case. Hand-editing to the `git rev-parse HEAD` output works, and the `--finalize` way out is real once WR-01 is addressed. The test pins the exact sentence, so the inaccuracy is locked in.

**Fix:** "Set that pass's `head_sha` to the output of `git rev-parse <last reviewed commit>` (a lowercase full commit id) and re-run; `--finalize` does not read this value." Drop the "restore from git" clause, or limit it to "if you track `.turingmind/`". Update `HEAD_SHA_HALT` to match.

### IN-02 (new): The `FINALIZE_MODE` literal is not tied to the current pass, and the bind fence is now security-relevant

**File:** `plugins/vibe-check/phases/review/05-state.md:63`

**Issue:** The prose says to substitute "the literal Phase 0 printed after `FINALIZE_MODE=`". A Finalize-routed fix (`90-finalize.md` step 2 → `50-fix-loop.md` The Rerun) loops back to Phase 0 in the same session with `--finalize` stripped. The transcript then holds both `FINALIZE_MODE=1` (from the finalize invocation) and `FINALIZE_MODE=0` (from the rerun).

If the agent substitutes the stale `1` on the rerun, which is a real review pass, the bind is skipped. That pass then has no `LAST_REVIEWED_SHA=` literal, and WR-01's three options apply to a pass that does need the range. Other literals in these files are already pinned ("the most recent `ROWSFILE=` line on this pass", "printed by THIS attempt's fence"). This one is not.

The fence still fails closed for an empty or unsubstituted value. The risk is only a stale `1`.

**Fix:** "substitute the literal printed after `FINALIZE_MODE=` by THIS pass's Phase 0 (the most recent such line — a Finalize-routed Rerun reprints `FINALIZE_MODE=0`)".

### IN-03 (new): `test_post_decision_recount_refingerprints_head` proves the helper, not the step-3 prose; the prose side is needle-only

**File:** `plugins/vibe-check/scripts/test_finalize_card.py` (`test_post_decision_recount_refingerprints_head`)

**Issue:** The walk writes `{ARCH_FILE: "blob-pre-card"}` and `{ARCH_FILE: "blob-post-card"}` into the minted BLOBFILEs by hand. It never runs step 1's `git rev-parse` / `git diff --quiet` fingerprinting against a real edited file. Its stale, fresh and control subtests therefore show how `finalize-counts` behaves on different blob maps. That part is correct and useful. They do not show that the step-3 prose makes a new BLOBFILE.

The only link to the prose is the final `assert_holds(step3_rerun_rule_holds, …)`, a needle and stale-claim check. That check is not decorative: reverting the prose fails 9 tests, and `test_mutant_step3_reinserts_stale_fingerprint_claim` is properly isolated. Still, the test's docstring ("Step 3 must say to re-fingerprint") and REPRO_60's `STALE-BLOBFILE-RECOUNT` fixture list claim more than the test checks. A rewording that keeps the four needles but adds, for example, "reuse the pre-card blob map if HEAD is unchanged" would pass.

**Fix:** None required for this round. Either change the docstring to "the helper reopens on a new blob map; step 3's wording is locked by `step3_rerun_rule_holds`", or have the walk make a real commit in a `gitfixture` repo and fingerprint it the way step 1 says.

## Carried (not re-counted)

These were confirmed still present at 129c69e and are already recorded in 60-REPRO.md. They are not new findings:

- **R22**: the pre-existing step-3 "old GATEFILE" mutant is still needle-replacement. This round moved it from `STEP3_NEEDLES[0]` to `[3]` and it still does not isolate the `STEP3_OLD` branch. The new stale-claim mutant is isolated.
- **R23**: the halt still blames `head_sha` for a missing or malformed state file. The new remedy now gives the head_sha way out in those cases too, and it does not apply there.
- **R24**: step 3 still does not say whether a failure of its new step-1 / counts / gate re-run after `record-decisions` gets the one automatic rebuild. The generic "nothing was written or archived" stop sentence would be false there. Step 3 now runs more fences after the write (mktemp and fingerprinting as well as counts and gate), so there are slightly more ways for it to fail there than in round 2.
- **R25**: a well-formed but crafted `head_sha` can narrow the range. This awaits an owner ruling.
- **R26**: `45-persist.md` still writes `head_sha` with no format check.

## Set aside (needs ruling)

None.

---

_Reviewed: 2026-10-30T19:37:04Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
