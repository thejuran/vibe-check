---
phase: 60-exact-change-evidence-and-reliable-finalize
reviewed: 2026-10-30T18:34:56Z
depth: standard
scope: second gap-closure round (60-10..60-13), diff 65bb39d..HEAD
files_reviewed: 9
files_reviewed_list:
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/review/30-collect-score.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/carry_state.py
  - plugins/vibe-check/scripts/test_carry_state.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_diff_ranges.py
  - plugins/vibe-check/scripts/test_finalize_card.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 60: Code Review Report (second gap round)

**Reviewed:** 2026-10-30T18:34:56Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The review covered the round's diff (`65bb39d..HEAD`): the new `carry_state.py last-head-sha` subcommand, the 05-state.md step-2 bind fence, the PHASE_START commit-id check in 00-scope.md, the 30-collect-score.md printed-literal rule, the Finalize step-3 GATEFILE re-mint, and the tests behind them. The four test files pass (600 tests, 728 subtests).

**CR-01 (head_sha injection) is closed as far as the row goes.** `last_head_sha` accepts only a str of 40 or 64 lowercase hex characters (`_HEX` is lowercase only) and prints nothing on refusal. The bind fence halts on any non-zero exit, and the fence's own test runs it in a fresh `bash -s` with the real CR-01 payload and checks that no marker file is created. I also searched every other placeholder that takes a value from the state file or from agent output and is substituted into a command (`<file>` in `HEAD:<file>` and `git diff -- <file>`, fix-loop `commit_sha`, `<sha>`). Each is validated before any git call (PATH_RE + guard.py for files; `^[0-9a-f]{40}$` + `cat-file`/`merge-base` for shas), so there is no injection bypass. The PHASE_START regex works under both bash and zsh (checked by hand for the empty, 40-hex, 64-hex and `HEAD` cases). The prose mutant locks I checked (the reinserted `HEAD_SHA_OLD`, the reinserted quotes-alone claim, the removed check line) each trip on their own.

**WR-02 (stale GATEFILE) is closed, but the fix exposes an older defect.** Step 3 now gates on a new GATEFILE written from the recounted counts. That recount still reads this attempt's BLOBFILE. The BLOBFILE was minted before the card and the owner's answer, and its fingerprints are now trusted across the whole time the owner spends answering. Before this round, step 3 always stayed blocked, so stale fingerprints there could never lead to a `write`. Now they can (WR-01).

The second warning is that the new bind fence also runs on `--finalize`. It turns any non-sha `head_sha` into a hard stop for Finalize, even though Finalize never uses that value (WR-02).

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Step 3's recount reuses the pre-card BLOBFILE, so a fix-obsolete verdict can close on code edited while the card was open (now reachable as a `write`)

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:272` (with the retry rule at `:67`)
**Issue:** Step 3 now says: "RE-RUN the counts step ONCE (the same `BLOBFILE=` literal this attempt printed) — the fingerprints have not changed, only the decisions have". That justification does not hold. The BLOBFILE was written in step 1, before the card was shown. Between then and step 3 is a human-length wait while the owner reads and answers the card, and the working tree can change during that wait. Only re-reading HEAD, the index and the working tree can show that the fingerprints are unchanged. The file's own retry rule (line 67) states the invariant this breaks: "Never reuse a `BLOBFILE=` printed by an earlier attempt… its blobs may predate a later edit and would let a fix-obsolete verdict close on changed code."
Before this round the breach was harmless, because step 3 always gated on the stale GATEFILE and therefore always stayed blocked. With WR-02 fixed, the recount drives the gate. Here is the path:
1. A fix-obsolete verdict's file is edited during the card wait.
2. The stale BLOBFILE still holds the old blob, which equals `verified_blob`.
3. The verdict is honoured, the recount drops to `(0,0,0)`, and the gate returns `write`.
4. REVIEW.md is written APPROVED and the state is archived, over code that no fingerprint ever judged.

The new walk test `test_post_decision_rerun_decides_on_a_fresh_gatefile` writes `{}` to the BLOBFILE, so it cannot see this.
**Fix:** In step 3, rebuild the fingerprints before the recount, the same way the rebuild-once rule does. Replace the parenthetical and the claim with:
```text
Then run step 1 again — a new mktemp fence printing a NEW `BLOBFILE=`, fingerprints rebuilt from the current HEAD, index and working tree — re-run the counts step with that new literal, then run the gate-input fence again so it prints a NEW `GATEFILE=` …
```
Then update `STEP3_NEEDLES[0]` in `test_finalize_card.py`, and add a walk subtest in which a fix-obsolete verdict's file is edited after the first BLOBFILE is written: the step-3 recount must not count that verdict as closed.

### WR-02: The new head_sha bind fence also blocks `--finalize`, with no recovery instruction

**File:** `plugins/vibe-check/phases/review/05-state.md:52-61` (with step 4 at `:97`; `scripts/carry_state.py:1528-1534`)
**Issue:** Step 2 runs on every run that has a state file, including `FINALIZE_MODE=1` (step 4 says a finalize run "continues to Phase 0.6 and Finalize", so it passes through step 2). Finalize reads `$STATE_FILE`, not the diff, and never uses `$LAST_REVIEWED_SHA`. Yet a last pass whose `head_sha` is anything other than full lowercase hex now stops Finalize with "Review halted — … nothing was scored."
- **Why this can happen in normal use.** `head_sha` is typed by the agent from `"<current HEAD>"` in 45-persist.md. The schema (`future-schema.json`) requires the key but not its form, so a short sha or `HEAD` written by the agent is a plausible slip.
- **Why it is new.** `state_reason` accepts such a state, so the `decided`/`deferred` fences did not stop on it before this round.
- **What the owner sees.** The message gives no way out: it does not say which file to fix, and it does not say that deleting the state file throws away every recorded decision. The result is a stuck Finalize — the "broken required workflow" class.
**Fix:** Bind `$LAST_REVIEWED_SHA` only when the run needs the incremental range. Wrap the fence in `FINALIZE_MODE=0`, or state in step 2 that a `FINALIZE_MODE=1` run skips this binding. Also make the halt sentence name the cause and a remedy, for example: "… the last pass in `<STATE_FILE>` has no full commit sha; run `/review` once to record a new pass, or restore the file from git." Add a fence test in which a finalize-mode run with `head_sha: "HEAD"` reaches the counts step.

## Info

### IN-01: The step-3 "old GATEFILE" mutant does not isolate the `STEP3_OLD` check

**File:** `plugins/vibe-check/scripts/test_finalize_card.py:1420-1424`
**Issue:** The mutant replaces `STEP3_NEEDLES[0]` with `STEP3_OLD + …`. The check therefore trips because needle 0 is missing, whether or not the `if STEP3_OLD in line` branch exists. You could delete that branch from `step3_rerun_rule_holds` and the test would still pass. The other two mutant suites in this round (`test_head_sha_mutants_trip` reinserted, `test_substituted_value_mutants_trip` reinserted) do isolate their checks correctly. This is the same weakness R21 records for an earlier check.
**Fix:** Build the mutant by appending `" " + STEP3_OLD` to the intact line, so every needle is still present and only the old-wording check can trip.

### IN-02: The bind fence's halt sentence blames `head_sha` for every helper failure

**File:** `plugins/vibe-check/phases/review/05-state.md:57`; `scripts/carry_state.py:1529-1531`
**Issue:** These cases all end in the same sentence, "the state file's last-pass head_sha is not a commit sha":
- a missing state file (`test_missing_state_file_halts`)
- invalid JSON
- an empty `passes` list (`REASON_PASSES`)

The helper's real reason does appear on the line above, but the owner-facing sentence is wrong for these cases.
**Fix:** Use a neutral sentence ("Review halted — the state file's last pass could not be read as a commit sha (the line above says why); nothing was scored."), and update `HEAD_SHA_HALT` in the test.

### IN-03: Step 3 does not say what happens if its recount or gate fails, and its stop sentence would be false

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:67,272`
**Issue:** Step 3 adds a second mktemp, Write and gate sequence after the card, but does not say whether the rebuild-once rule applies to it. If the agent applies that rule, its only stop sentence is "nothing was written or archived". By step 3 that is false, because `record-decisions` has already changed the state file.
**Fix:** Add one clause to step 3: a failure here is not retried, and the stop sentence is "Finalize stopped — your decisions were recorded; nothing else was written or archived; run `--finalize` again."

## Set aside (needs ruling)

### SA-01: A well-formed but crafted `head_sha` can still narrow the incremental range

**Where:** `plugins/vibe-check/scripts/carry_state.py:1193-1207`; `phases/review/05-state.md:52-61`
**Why excluded:** CR-01 was about command injection, and the format check closes that. Whether the state file is trusted for scope is a broader question that predates this round.
**Effect if left as is:** Anyone who can commit the state file into the reviewed repo can set `head_sha` to a real 40-hex commit such as their branch tip. The pass-≥2 range then covers only changes after that commit, so code they already committed is never reviewed — the owner gets a smaller review without being told. `50-fix-loop.md:307` already holds agent-supplied shas to `git cat-file -e "<sha>^{commit}"` + `git merge-base --is-ancestor`. That check would not stop `head_sha = HEAD`, though; only binding the value to something outside the repo (for example, a copy kept outside the working tree) would.
**Needs:** A ruling from the developer: is the state file's `head_sha` trusted for scope (accept), or should scope binding be planned as a hardening item (defer)?

---

_Reviewed: 2026-10-30T18:34:56Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
