---
phase: 60-exact-change-evidence-and-reliable-finalize
verified: 2026-10-30T18:47:39Z
status: gaps_found
score: 5/6 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/6
  gaps_closed:
    - "Every route reliably uses the exact-range builder from a genuinely fresh Bash call, with no way to subvert the substituted value (EVID-03) — CR-01 head_sha command injection, closed by 60-10 + 60-11, independently re-reproduced below (fresh-shell fence halts, marker never created)"
    - "A failed or refused Finalize attempt stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness (FINL-02) — the original stale-GATEFILE post-decision re-run, closed by 60-12, independently re-reproduced below"
  gaps_remaining: []
  regressions:
    - "WR-01 (90-finalize.md step 3, reported in the fresh gap-round-2 review 60-REVIEW.md, commit e90c6a7): the post-decision recount that 60-12's own fix made load-bearing reuses the pre-card BLOBFILE instead of re-fingerprinting HEAD, so a fix-obsolete verdict can still close over code edited during the human-length card-answer wait, and Finalize can write REVIEW.md APPROVED over code nothing re-verified. Independently reproduced with the real `carry_state.finalize_counts` helper below — this is a NEW defect, introduced by 60-12's fix, not one of the two gaps this round closed."
    - "WR-02 (05-state.md step 2 / carry_state.py last-head-sha, review's numbering, same commit): the validating head_sha bind fence that 60-10 + 60-11 added to close CR-01 runs unconditionally whenever a state file is present, including every `--finalize` run — even though Finalize never reads `$LAST_REVIEWED_SHA`. A pre-existing non-sha `head_sha` (unvalidated at write time in 45-persist.md) now wedges Finalize permanently with no stated remedy. Independently confirmed by code tracing below — also a NEW defect, introduced by 60-10/60-11's fix."
gaps:
  - truth: "A failed or refused Finalize attempt stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness (FINL-02)"
    status: failed
    severity: blocking
    reason: >
      The original gap this field tracked (the post-decision gate re-run deciding
      on a stale GATEFILE) is genuinely fixed by 60-12 — independently
      re-reproduced below. But the fresh gap-round-2 code review (60-REVIEW.md,
      commit e90c6a7) found two further, NEW defects in the exact mechanisms
      this round's own fixes touched, and I independently reproduced both —
      not just read the review's prose.

      WR-01: step 3's "fix empty" branch (the line 60-12 rewrote) now says
      verbatim "RE-RUN the counts step ONCE (the same `BLOBFILE=` literal this
      attempt printed) — the fingerprints have not changed, only the decisions
      have". That claim is false whenever time passes between the card being
      shown and the owner answering it: BLOBFILE is minted and fingerprinted in
      step 1, BEFORE the card is rendered, and the owner's read-and-answer wait
      is a human-length gap during which the working tree can change. Before
      60-12 this was harmless, because step 3 always gated on the stale
      GATEFILE and could never return `write`. Now that 60-12 made the
      post-decision gate decide on the recounted counts (the whole point of its
      fix), the stale BLOBFILE becomes load-bearing: a fix-obsolete verdict
      whose file is edited during the card wait is still honoured, because the
      step-3 recount reads the SAME pre-card blob snapshot instead of
      re-fingerprinting HEAD the way the separate rebuild-once (failure-retry)
      paragraph already does 15 lines above. I reproduced this directly against
      the real `carry_state.finalize_counts` helper (not a mock): with a
      `fix_verdicts` "obsolete" entry whose `verified_blob` matches the stale
      BLOBFILE snapshot, `outstanding_cw` stays 0 (closed) even when the
      simulated real HEAD blob has since changed to a value the stale snapshot
      never saw; re-fingerprinting at step 3 correctly flips it back to 1
      (reopened). The new walk test `test_post_decision_rerun_decides_on_a_fresh_gatefile`
      cannot see this because it writes `{}` to BLOBFILE (no fix_verdicts in
      play), so the gap is real and untested.

      WR-02 (review's numbering — distinct from the ORIGINAL WR-02 this gap
      used to track, which is now closed): the `LAST_REVIEWED_SHA` bind fence
      05-state.md step 2 gained in this round (to close CR-01) has no
      `FINALIZE_MODE` conditional, and step 2 itself is not conditioned on
      finalize mode — it is part of "2. If present: parse it.", which runs
      whenever a state file exists. I confirmed by reading the command spine
      (`commands/review.md`/`deep-review.md`) that only Phase 0.5's ROUTING
      (steps 1/4/5's branch target) is skipped on `--finalize`; step 2's
      bindings are not exempted. I confirmed by grepping `90-finalize.md` that
      it never references `LAST_REVIEWED_SHA`, `CARRYFORWARD` or `PASS_NUMBER`
      at all — Finalize genuinely never needs the value the fence computes.
      `future-schema.json` requires the `head_sha` key but imposes no format
      check, and `45-persist.md` has the agent fill it from the literal
      template `"<current HEAD>"` with no write-time validation, so a short
      sha, a literal `HEAD`, or any other slip is a plausible way for an
      existing state file to end up with a non-sha `head_sha`. On the next
      `--finalize` (or even the next plain review pass, which hits the same
      fence), the run now hard-stops with "Review halted — the state file's
      last-pass head_sha is not a commit sha; nothing was scored." with no
      named remedy — before this round, this exact value was bound unchecked
      and simply ignored by Finalize, so this stop did not exist. The owner's
      only paths out are to hand-edit internal JSON they are not told about,
      or discard the state file (losing every recorded decision) — a broken
      required workflow by this project's own standing rule for what counts as
      in-scope (data loss / broken required workflow), introduced by this
      round's own CR-01 fix.
    artifacts:
      - path: "plugins/vibe-check/phases/shared/90-finalize.md"
        issue: "step 3's rewritten line (60-12) asserts the pre-card BLOBFILE's fingerprints 'have not changed' without re-verifying that, unlike the rebuild-once paragraph which explicitly re-fingerprints"
      - path: "plugins/vibe-check/phases/review/05-state.md"
        issue: "step 2's head_sha bind fence (60-10/60-11) has no FINALIZE_MODE=1 exemption, so a stored head_sha's format can hard-stop a --finalize run that never consumes the value it validates"
      - path: "plugins/vibe-check/scripts/test_finalize_card.py"
        issue: "test_post_decision_rerun_decides_on_a_fresh_gatefile writes {} to BLOBFILE, so it cannot exercise the fix-obsolete / stale-blob path WR-01 describes"
    missing:
      - "Step 3 must re-fingerprint HEAD into a NEW BLOBFILE before its recount (mirroring the rebuild-once paragraph's wording exactly), plus a fresh-shell walk test with a fix-obsolete verdict whose file is edited between the card being minted and step 3 running, proving the edit reopens the finding instead of silently closing it"
      - "05-state.md step 2's head_sha bind fence must be skipped (or made non-fatal) on a FINALIZE_MODE=1 run, since Finalize never reads $LAST_REVIEWED_SHA, with a fence test proving a finalize-mode run with a non-sha head_sha (e.g. the literal \"HEAD\") still reaches the counts/gate step; the halt sentence (for the remaining review-mode case) should also name a remedy instead of a bare refusal"
deferred: []
human_verification:
  - test: "Confirm whether Claude Code's Write tool refuses the first write to a path that `mktemp` just created but the agent never Read (SA-01, carried as R16 in 60-REPRO.md)"
    expected: "Either the Write succeeds (the existing ROWSFILE/SUGGESTFILE/REFSFILE pattern already relies on this), or it is refused and every --finalize attempt (and its one retry) fails at the BLOBFILE/GATEFILE write step"
    why_human: "Depends on live Claude Code harness Write-tool behavior that cannot be exercised from a pytest fixture"
  - test: "Decide whether the PR route's hard failure on very large PRs (SA-02: gh pr diff over ~300 files / 20k lines) needs a fallback or is an accepted limit"
    expected: "An owner ruling, not a reproduction — the reviewer notes failing closed is the intended behavior here"
    why_human: "Product/scope decision, not a code defect"
  - test: "Rule on 60-REVIEW.md's second-round SA-01 (distinct from the item above): is a state file's head_sha trusted to scope the incremental range (accept), or should scope binding be hardened against a crafted-but-well-formed 40/64-hex head_sha that narrows what gets reviewed (defer as a hardening item)?"
    expected: "An explicit owner ruling. CR-01's fix (format validation) closes the command-injection path but does not address whether a committed state file should be allowed to narrow review scope at all."
    why_human: "Product/scope/trust-boundary decision, not a code defect — the reviewer explicitly set this aside pending a ruling"
---

# Phase 60: Exact change evidence and reliable Finalize Verification Report

**Phase Goal:** The nearby window is exactly what the decision rules say on every review route, and Finalize either completes from a fresh shell or stops safely without writing (999.24, 999.25)
**Verified:** 2026-10-30
**Status:** gaps_found
**Re-verification:** Yes — after the second gap-closure round (plans 60-10, 60-11, 60-12, 60-13), re-verifying against the 2 blocking gaps found at the prior re-verification (`f2b58d1`), plus the second round's own code review (`60-REVIEW.md`, commit `e90c6a7`)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1/EVID-01 core: ranges are built only from a hunk's `+`/`-` body markers, not display context | ✓ VERIFIED (regression-checked) | `diff_ranges.py`'s marker-walk core is untouched by this round; `pytest -q test_diff_ranges.py` full file (run by me just now): `115 passed, 86 subtests passed`, 0 failed |
| 2 | SC2/EVID-02: fixtures that run a real `git diff` produce correct ranges for ordinary, deletion-only, insertion and relocated-finding shapes | ✓ VERIFIED (regression-checked) | Same run as above; unaffected by this round |
| 3 | SC3/EVID-03: every route reliably uses the exact-range builder from a genuinely fresh Bash call, including the value substituted into it | ✓ VERIFIED | CR-01 (head_sha command injection) is closed. I independently re-ran the EXACT 05-state.md step-2 fence in a genuinely fresh `bash -s`, with the state's last `head_sha` set to the CR-01 payload `$(touch "$T/pwned")HEAD`: it halted (rc 1), printed no `LAST_REVIEWED_SHA=` line, and the marker file was never created. `carry_state.py last-head-sha` accepts only 40/64 lowercase hex (confirmed by reading `_commit_sha`); 00-scope.md's `PHASE_START` fence has the symmetric check. No EVID-03-specific defect remains (see Gaps for a side effect of this fix that lands on FINL-02 instead). |
| 4 | Range mechanism fails closed (halts, never silently empties) when the diff text is altered by a legitimate repo-local git setting (T-60-13) | ✓ VERIFIED (regression-checked) | `TestHazards`/`TestRefusals`/`TestMutants` M20-M22 are unaffected by this round and green in the full-file run above |
| 5 | SC4/FINL-01: a fresh-shell walk through every Finalize fence reaches counts → gate → report using the printed, literally reused `BLOBFILE=` path | ✓ VERIFIED (regression-checked) | `pytest -q test_finalize_card.py` full file (run by me just now): `93 passed, 140 subtests passed`, 0 failed. `TestFinalizeFreshShellWalk`'s own first-attempt walk is unaffected by this round. (WR-01 below is a distinct, newly-reproduced staleness bug in a LATER step — step 3's post-decision re-run — not in this truth's first-attempt path.) |
| 6 | SC5/FINL-02: a failed or refused attempt stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness | ✗ FAILED | The gap this truth tracked at the prior re-verification (the stale-GATEFILE post-decision re-run) is genuinely fixed by 60-12 — independently re-reproduced below. But the fresh gap-round-2 review (`60-REVIEW.md`, `e90c6a7`) found two NEW defects in the same mechanisms, and I independently reproduced both with working code, not by reading the review's prose: WR-01 (stale pre-card BLOBFILE can let a fix-obsolete verdict close over code edited during the card wait) and WR-02/review (the new head_sha bind fence wedges `--finalize` with no remedy, even though Finalize never reads that value). See `gaps` above. |

**Score:** 5/6 truths verified (up from 4/6 at the prior re-verification; both original blocking gaps — CR-01 and the stale-GATEFILE re-run — are genuinely closed, but the round's own fixes opened two new, independently-reproduced defects, both landing on truth 6)

### Independent re-reproduction of the two prior-round gaps (both CLOSED)

**CR-01 — head_sha command injection (60-10 + 60-11).** I built a scratch repo and ran the EXACT text of 05-state.md's step-2 fence in a genuinely fresh `bash -s`, with `STATE_FILE` holding `{"passes":[{"pass_number":1,"head_sha":"$(touch \"$T/pwned\")HEAD","findings":[]}]}`:
```
refused: last pass head_sha is not a commit sha
Review halted — the state file's last-pass head_sha is not a commit sha; nothing was scored.
rc=1
marker exists: NO
```
The payload did not execute, no `LAST_REVIEWED_SHA=` line was printed, and the fence halted. I also read `carry_state.py`'s `_commit_sha` (accepts only `str` of length 40/64, every char in `_HEX` — the lowercase-hex-only form of `^[0-9a-f]{40}([0-9a-f]{24})?$` without `re`, since the import set is sealed) and `last_head_sha`/`run()`'s `last-head-sha` branch, which refuses with nothing on stdout on any other value. Matches 60-10-SUMMARY.md and 60-11-SUMMARY.md.

**Stale-GATEFILE post-decision re-run (60-12).** Read 90-finalize.md step 3's current text: it now says to re-count on the SAME BLOBFILE, then run the gate-input fence again for a NEW `GATEFILE=`, write the seven-key flags from the RE-COUNTED `$COUNTS_JSON` to that new path, and gate on that literal — "never on the GATEFILE= this attempt's first gate run read." `git diff c0ece7e -- plugins/vibe-check/phases/shared/90-finalize.md` shows exactly one line changed (the step-3 line); the rebuild-once (failure-retry) paragraph 15 lines above is byte-identical to the 60-08 close. `pytest -q test_finalize_card.py -k "step3 or post_decision"` (run by me): `4 passed, 89 deselected, 8 subtests passed`, 0 failed — including `test_post_decision_rerun_decides_on_a_fresh_gatefile`, which walks the real fences and shows the stale-GATEFILE-still-blocked / fresh-GATEFILE-writes contrast. Matches 60-12-SUMMARY.md and 60-REPRO.md V14.

### New findings on the fixed code (60-REVIEW.md, commit `e90c6a7`; independently reproduced by me)

**WR-01 — step 3's post-decision recount reuses the pre-card BLOBFILE, so a fix-obsolete verdict can close over code edited during the card wait.**

I reproduced this directly against the real `carry_state.finalize_counts` helper (not a mock or a narrative description):
```
step1 (pre-card) outstanding_cw: 0
step3 (post-card, STALE BLOBFILE) outstanding_cw: 0
  -> treated as CLOSED (fix-obsolete honoured) even though real HEAD blob is now BLOB_NEW, never fingerprinted
step3 (post-card, FRESH re-fingerprint) outstanding_cw: 1
  -> correctly REOPENED: the edit after the verdict's snapshot is caught
```
With a `fix_verdicts` "obsolete" entry whose `verified_blob` equals the file's blob at the time BLOBFILE was minted (step 1, before the card is shown), reusing that SAME BLOBFILE at step 3 (exactly as 90-finalize.md's current text instructs: "the fingerprints have not changed, only the decisions have") keeps the finding closed even when the file changed in between. Only re-fingerprinting HEAD at step 3 — the way the separate rebuild-once (failure-retry) paragraph already does — correctly reopens it. Before 60-12, this was harmless because step 3 always stayed blocked regardless of the recount; 60-12's own fix is what made this staleness load-bearing. I confirmed the new walk test cannot see this: `test_post_decision_rerun_decides_on_a_fresh_gatefile` writes `{}` to BLOBFILE (no `fix_verdicts` in play), so no fixture exercises the fix-obsolete path.

**WR-02 (review's numbering) — the new head_sha bind fence also runs on `--finalize` and wedges it with no remedy.**

I confirmed this by code tracing, not by taking the review's narrative at face value:
- `05-state.md` step 2 ("If present: parse it.") has no `FINALIZE_MODE` conditional of its own; the fence binding `$LAST_REVIEWED_SHA` via `carry_state.py last-head-sha` sits inside it unconditionally.
- `commands/review.md`/`commands/deep-review.md` say Finalize mode runs "Phase 0.5 — which binds `$STATE_FILE` and reads the state; its routing into Phase 0.7, Phase 1 or the carry-forward steps does not apply here" — only the ROUTING (steps 1/4/5's branch target) is exempted, not step 2's bindings.
- `grep -n "DECIDED_HASHES\|CARRYFORWARD\|LAST_REVIEWED_SHA\|PASS_NUMBER" plugins/vibe-check/phases/shared/90-finalize.md` returns nothing: Finalize genuinely never consumes the value this fence computes and validates.
- `fixtures/future-schema.json` requires the `head_sha` key but has no format constraint on it, and `45-persist.md` has the agent fill it from the literal template `"<current HEAD>"` with no write-time check — a plausible slip (short sha, the literal string `HEAD`, etc.) that the schema does not catch.

The net effect: an existing state file with a non-sha `head_sha` (however it got there) now hard-stops every subsequent `--finalize` (and every subsequent plain review pass, which hits the same fence) with "Review halted — the state file's last-pass head_sha is not a commit sha; nothing was scored." and no stated remedy — before this round, the same value was bound unchecked and simply never read by Finalize, so this stop could not happen. The owner's only ways out are an undocumented hand-edit of internal JSON, or discarding the state file and losing every recorded decision.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/carry_state.py` | `last-head-sha` subcommand, `_commit_sha` validator, `REASON_HEAD_SHA` sealed, no `re` import | ✓ VERIFIED | Read in full; `SUBCOMMANDS`, `_FLAGS_BY_SUBCOMMAND`, `USAGE`, `REASONS` all updated; `run()` branches to `last_head_sha` and refuses with nothing on stdout |
| `plugins/vibe-check/scripts/test_carry_state.py` | `TestLastHeadSha` (accept/refuse table incl. CR-01 payload, mutation subtest) | ✓ VERIFIED | `pytest -q test_carry_state.py -k TestLastHeadSha` → 8 passed, 18 subtests passed (run by me); full file 234 passed, 318 subtests, 0 failed |
| `plugins/vibe-check/phases/review/05-state.md` | step-2 fence binds `$LAST_REVIEWED_SHA` through the validated subcommand; halts on refusal | ⚠️ PARTIAL | Fence present and correct for review-mode halting (confirmed by fresh-shell repro above); unconditionally also runs on `--finalize`, which Finalize never needs — WR-02 (review) |
| `plugins/vibe-check/phases/review/00-scope.md` | `PHASE_START` fence refuses a non-commit-id value before printing | ✓ VERIFIED | Check line present, confirmed by `sed`/`grep`, precedes the `printf 'PHASE_START=%s\n'` line |
| `plugins/vibe-check/phases/review/30-collect-score.md` | Rows name only the printed `PHASE_START=`/`LAST_REVIEWED_SHA=` literals; quotes-alone claim removed | ✓ VERIFIED | Read in full; paragraph now correctly says quotes stop word-splitting, not `$(...)` |
| `plugins/vibe-check/scripts/test_diff_ranges.py` | `TestStateHeadShaFence`, `TestSubstitutedValueProse`, `TestScopePhaseStartFence` additions | ✓ VERIFIED | `pytest -q test_diff_ranges.py -k "StateHeadSha or SubstitutedValue or ScopePhaseStart or printed_last_reviewed or injection_payload"` → 17 passed, 11 subtests passed (run by me); full file 115 passed, 86 subtests, 0 failed |
| `plugins/vibe-check/phases/shared/90-finalize.md` | Step 3 re-mints GATEFILE from recounted counts | ⚠️ PARTIAL | GATEFILE re-mint fix (60-12) confirmed correct and matches the exact diff recorded in 60-12-SUMMARY.md (`git diff <RED>` 1 line changed); the SAME line's BLOBFILE-reuse assumption is false under a mid-card edit — WR-01 |
| `plugins/vibe-check/scripts/test_finalize_card.py` | `step3_rerun_rule_holds`, `test_post_decision_rerun_decides_on_a_fresh_gatefile` | ✓ VERIFIED for its own scope | `pytest -q test_finalize_card.py -k "step3 or post_decision"` → 4 passed, 8 subtests passed (run by me); full file 93 passed, 140 subtests, 0 failed. Does not cover the fix-obsolete/stale-blob path (WR-01 is outside this plan's own must-haves) |
| `plugins/vibe-check/scripts/test_decision_continuity.py` | `REPRO_60` at 14 rows, `_suite_defines` covers `test_carry_state.py` | ✓ VERIFIED | `pytest -q test_decision_continuity.py -k TestRepro60Record` → 3 passed, 54 subtests passed (run by me) |
| `.planning/phases/.../60-REPRO.md` | V13/V14 ledger, reverse run at `f2b58d1`, suite at close, R14 closed | ✓ VERIFIED (internally consistent) | Matches git history; predates the fresh review `e90c6a7`, so it does not (and could not) cover WR-01/WR-02 (review) — these are new findings this verification surfaces |
| `.planning/phases/.../60-REVIEW.md` | Second gap-round code review | ✓ VERIFIED | Present at commit `e90c6a7`; WR-01 and WR-02 independently re-reproduced by me above, CR-01-closure confirmation also independently re-checked, not taken on faith |
| `.planning/REQUIREMENTS.md` / `.planning/ROADMAP.md` | EVID-03/FINL-02 marked "awaiting re-verification", not Complete; no orphaned requirement IDs | ✓ VERIFIED | Both checkboxes unchecked, traceability rows match 60-13's claims exactly; EVID-01/EVID-02/FINL-01 are Complete; all 5 of EVID-01, EVID-02, EVID-03, FINL-01, FINL-02 appear in at least one plan's `requirements:` frontmatter (60-01..60-13) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `05-state.md` step-2 fence | `carry_state.py last-head-sha` | `if LAST_REVIEWED_SHA=$(python3 ... last-head-sha < "$STATE_FILE")` | ✓ WIRED (review mode) / ⚠️ OVER-WIRED (also gates finalize mode, which never reads the value) | Fresh-shell repro confirms the halt; WR-02 (review) is the over-wiring |
| `00-scope.md` phase-range fence | `30-collect-score.md` GSD row | printed `PHASE_START=` literal, check before print | ✓ WIRED | Confirmed by reading and line-order check |
| `90-finalize.md` step 1 (HEAD fingerprints) | `90-finalize.md` step 3 recount | reuse of `BLOBFILE=` literal, asserted (not re-verified) unchanged | ✗ UNSAFE | WR-01: the reuse is correct for the no-time-elapsed case the new walk test covers, but not for a mid-card edit to a fix-obsolete-verified file |
| `90-finalize.md` step 3 | gate-input fence + `finalize_gate.py` | NEW `GATEFILE=` built from the RE-COUNTED `$COUNTS_JSON` | ✓ WIRED | Confirmed by reading + green test suite; this is the part 60-12 fixed correctly |
| `05-state.md` step 2 | `90-finalize.md` entry | unconditional (no `FINALIZE_MODE` gate on step 2 itself) | ✗ NOT EXEMPTED | WR-02 (review): Finalize is reachable only after step 2's validation passes, even though Finalize's own file never reads what step 2 validates |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `test_diff_ranges.py` full file | `pytest -q test_diff_ranges.py` | `115 passed, 86 subtests passed` | ✓ PASS |
| `test_finalize_card.py` full file | `pytest -q test_finalize_card.py` | `93 passed, 140 subtests passed` | ✓ PASS |
| `test_carry_state.py` full file | `pytest -q test_carry_state.py` | `234 passed, 318 subtests passed` | ✓ PASS |
| `test_carry_state.py -k TestLastHeadSha` | `pytest -q test_carry_state.py -k TestLastHeadSha` | `8 passed, 18 subtests passed` | ✓ PASS |
| `test_diff_ranges.py` CR-01 classes | `pytest -q test_diff_ranges.py -k "StateHeadSha or SubstitutedValue or ScopePhaseStart or printed_last_reviewed or injection_payload"` | `17 passed, 11 subtests passed` | ✓ PASS |
| `test_finalize_card.py` step3/post-decision classes | `pytest -q test_finalize_card.py -k "step3 or post_decision"` | `4 passed, 8 subtests passed` | ✓ PASS |
| `test_decision_continuity.py -k TestRepro60Record` | `pytest -q test_decision_continuity.py -k TestRepro60Record` | `3 passed, 54 subtests passed` | ✓ PASS |
| CR-01 payload, genuinely fresh `bash -s`, real 05-state.md fence text | manual real-shell repro (shown above) | rc 1, no `LAST_REVIEWED_SHA=` line, marker never created | ✓ PASS (fix holds) |
| WR-01 stale-vs-fresh BLOBFILE, real `carry_state.finalize_counts` helper | manual repro (shown above) | stale blob → `outstanding_cw` 0 (wrongly closed); fresh blob → 1 (correctly reopened) | ✗ FAIL (defect confirmed, real) |
| WR-02 (review) finalize-wedge, code trace of 05-state.md / 90-finalize.md / command spine | manual trace (shown above) | step 2's bind fence is unconditional; 90-finalize.md never reads `LAST_REVIEWED_SHA`/`CARRYFORWARD`/`PASS_NUMBER` | ✗ FAIL (defect confirmed, real) |
| Full repo suite at HEAD `e90c6a7` | `pytest -q` (plugins/vibe-check/scripts) | `3813 passed, 0 failed` (orchestrator-run, cited per the "run the full suite at most once" constraint — not re-run by me) | ✓ PASS |

### Probe Execution

SKIPPED — no `scripts/*/tests/probe-*.sh` convention in this repo and none declared by the Phase 60 PLAN/SUMMARY files; verification used the project's own `pytest` suite and direct reproduction (shown above) instead, consistent with the prior verification's approach.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| EVID-01 | 60-01, 60-02, 60-04, 60-06, 60-07 | Ranges from added/deleted lines only, boundary-exact, fails closed on hostile-but-legitimate config | ✓ SATISFIED | Truths 1, 4 |
| EVID-02 | 60-01, 60-02 | Correct ranges for ordinary/deletion/insertion/relocated shapes via real git diff | ✓ SATISFIED | Truth 2 |
| EVID-03 | 60-04, 60-07, 60-10, 60-11 | Every route uses exact ranges reliably from a fresh Bash call, with no way to subvert the substituted value | ✓ SATISFIED | Truth 3 (CR-01 closed; the side effect of its fix lands on FINL-02, not EVID-03) |
| FINL-01 | 60-03 | Printed BLOBFILE literal reused; fresh-shell walk reaches write/report | ✓ SATISFIED | Truth 5 |
| FINL-02 | 60-03, 60-05, 60-08, 60-12 | No-write-on-failure; a later retry/re-run may complete; revalidates freshness | ✗ BLOCKED | Truth 6; WR-01, WR-02 (review) |

No orphaned requirement IDs: REQUIREMENTS.md maps exactly EVID-01, EVID-02, EVID-03, FINL-01, FINL-02 to Phase 60; all five appear in at least one plan's `requirements:` frontmatter across 60-01 through 60-13.

**On REQUIREMENTS.md's current wording:** it correctly says EVID-03 and FINL-02 are "Gap closure landed... awaiting re-verification" (not Complete). This re-verification finds EVID-03 now holds (the gap it tracked is closed and no EVID-03-specific defect remains), so EVID-03 can move to Complete. FINL-02 cannot: the gap it originally tracked is closed, but two new, independently-reproduced defects in the very mechanisms this round touched (WR-01, WR-02/review) keep it open. FINL-02 should stay unchecked.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No `TBD`/`FIXME`/`XXX` debt markers in any file touched by 60-10..60-13 (`vc.XXXXXX` mktemp templates are not debt markers) | — | checked directly, none found |
| `plugins/vibe-check/phases/shared/90-finalize.md` | step 3 ("fix empty" branch) | Recount asserts fingerprint freshness ("the fingerprints have not changed") without re-verifying it | 🛑 blocking | WR-01 — stale-evidence approval, reproduced |
| `plugins/vibe-check/phases/review/05-state.md` | step 2 bind fence | No `FINALIZE_MODE` exemption on a validation Finalize never consumes | 🛑 blocking | WR-02 (review) — finalize-wedge with no remedy, reproduced |
| `plugins/vibe-check/scripts/test_finalize_card.py` | `test_mutant_step3_rerun_rule` (`IN-01` in 60-REVIEW.md) | A mutant check that trips on a missing needle regardless of whether the branch it names exists | ℹ️ info | documentation-strength test, carried per the review; not independently re-scored here |
| `plugins/vibe-check/phases/review/05-state.md` | bind-fence halt sentence (`IN-02` in 60-REVIEW.md) | One sentence used for several distinct causes (missing state file, bad JSON, empty passes, bad head_sha) | ℹ️ info | misleading diagnostics, not a functional break; carried |
| `plugins/vibe-check/phases/shared/90-finalize.md` | step 3 (`IN-03` in 60-REVIEW.md) | No stated behavior if the post-decision recount/gate itself fails after decisions were already recorded | ℹ️ info | the generic "nothing was written" stop sentence would be misleading there; carried |
| `plugins/vibe-check/phases/review/05-state.md` / `carry_state.py` | `SA-01` in 60-REVIEW.md (new, scope question) | A well-formed 40/64-hex `head_sha` committed into the reviewed repo can still narrow the incremental range | — (owner ruling) | moved to Human Verification below; not a code defect |
| `plugins/vibe-check/phases/review/30-collect-score.md` | `diff.submodule` not neutralized (60-REPRO.md R18, carried) | not independently re-opened here; outside this verification's assigned scope | warning | false refusal / silent range loss on submodule-only or mixed changes |
| `plugins/vibe-check/phases/shared/90-finalize.md` | temp files never `rm -f`'d (60-REPRO.md R12, carried) | not independently re-opened here | info/minor | resource hygiene, not a functional break |

### Human Verification Required

### 1. Write-tool refusal risk on freshly-minted temp files (SA-01, carried as R16)

**Test:** Run a live `--finalize` in Claude Code and observe whether the Write tool accepts the first write to the path printed after `BLOBFILE=`/`GATEFILE=` (a file `mktemp` just created but the agent never `Read`).
**Expected:** The write succeeds (consistent with the pre-existing ROWSFILE/SUGGESTFILE/REFSFILE pattern), or — if refused — every `--finalize` attempt and its one retry both fail at the same step.
**Why human:** Harness Write-tool behavior cannot be exercised from a pytest fixture.

### 2. PR size-limit fallback decision (SA-02, carried as R17)

**Test:** None — this is a scope/product decision.
**Expected:** An explicit owner ruling on whether `gh pr diff` failing closed on very large PRs (~300+ files / 20k+ lines) is an accepted limit or needs a fallback.
**Why human:** Not a code defect; the reviewer calls the current fail-closed behavior intended.

### 3. State-file `head_sha` trust boundary for scope (60-REVIEW.md second-round SA-01, new)

**Test:** None — this is a scope/product/trust-boundary decision.
**Expected:** An explicit owner ruling: is a committed state file's `head_sha` trusted to scope the incremental range (accept the status quo), or should scope binding be hardened against a well-formed-but-crafted value that narrows review coverage without telling the owner (plan as a hardening item)?
**Why human:** CR-01's fix closes the command-injection path but does not, and was not meant to, settle this separate trust question; the reviewer explicitly set it aside pending a ruling.

### Gaps Summary

This second gap round did what it set out to do for the two gaps it targeted: I independently re-reproduced both closures rather than trusting the SUMMARYs. CR-01 (the head_sha command-injection hole the first re-verification found) is genuinely closed — a fresh-shell run of the exact 05-state.md fence with the exact payload halts, prints nothing, and leaves no marker file. The original stale-GATEFILE post-decision re-run is also genuinely closed — 90-finalize.md step 3 now re-mints GATEFILE from the recounted counts, confirmed by reading the one changed line and by a green, fence-driven walk test.

However, the phase cannot close yet. The round's own fresh code review (`60-REVIEW.md`, commit `e90c6a7` — the current HEAD) found two further problems in the exact mechanisms this round touched, and I independently reproduced both with working code and direct tracing, not by reading the review's prose:

1. **WR-01.** 60-12's fix made the step-3 post-decision recount decide the gate's outcome — correctly, for the GATEFILE half. But the recount still reads the SAME BLOBFILE minted before the card was ever shown, on the unverified assumption that "the fingerprints have not changed, only the decisions have." I reproduced with the real `carry_state.finalize_counts` helper that a fix-obsolete verdict stays "closed" against a stale blob even when the real HEAD blob has since changed, while re-fingerprinting (as the separate rebuild-once paragraph already does) correctly reopens it. This is a regression introduced by this round's own 60-12 fix, not a pre-existing residual: before 60-12, step 3 could never reach `write`, so the staleness was inert.
2. **WR-02 (review's numbering).** The validating head_sha bind fence 60-10/60-11 added to close CR-01 has no exemption for `FINALIZE_MODE=1`, even though I confirmed by reading 90-finalize.md end to end that Finalize never consumes the value the fence validates. A pre-existing non-sha `head_sha` — plausible, since nothing validates the field's format when it is written — now wedges every subsequent `--finalize` (and every subsequent review pass) with no stated remedy, where before this round the same value was silently bound and ignored.

Both are concrete, independently reproduced with working code against the real helpers and real prose (not assumed from the review's narrative), and both are fixable with a scoped follow-up in the same shape as 60-10/60-11/60-12's own closures: re-fingerprint HEAD at step 3 before the recount (mirroring the rebuild-once paragraph), and exempt (or make non-fatal) the head_sha bind fence on a `FINALIZE_MODE=1` run.

**Recommendation:** route to a follow-up gap-closure round before closing FINL-02 as Complete. EVID-03 can move to Complete now (CR-01 is closed and no EVID-03-specific defect remains). These are not candidates for a waiver/override: WR-01 is a path to Finalize silently writing REVIEW.md APPROVED over code nothing re-verified, and WR-02 is a broken required workflow (Finalize permanently unable to complete) introduced by this round's own fix — exactly the class of defect this phase exists to close.

---

_Verified: 2026-10-30_
_Verifier: Claude (bm-verifier)_
