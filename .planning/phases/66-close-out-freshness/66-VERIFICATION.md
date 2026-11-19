---
phase: 66-close-out-freshness
verified: 2026-11-19T11:45:00Z
status: passed
score: 18/18 must-haves verified (16 verified directly, 2 passed under owner rulings; roadmap success criteria 4/4)
has_blocking_gaps: false
overrides_applied: 2
verified_commit: a6e93981 (code HEAD fa5afc55; last shipped-code change e3888c9c), branch feat/v2.16-phase-66, clean tree before and after
evidence_class: offline only (no live reviewer run, no live session)
overrides:
  - must_have: "The first two printed lines and the exit code are byte-identical to the 2.15.0 (d5acc19) helper on every route and every grid state"
    reason: "Byte-identical on all 13 grid states and for names git still quotes. Files with non-ASCII names now appear in NEARBY_LINE_RANGES (review fix CR-01, e3888c9c), so their decisions are re-asked instead of silently kept. Owner ruling: keep as an intended difference. Locked by TestQuotedNamesDifferentialV215::test_non_ascii_name_intended_second_line_difference."
    accepted_by: "owner (ruling relayed by the orchestrator and recorded in ROADMAP 999.44, the Phase 60 R7/R8/R10/R11 row, 66-VALIDATION.md and 66-REPLAY.md 6.4 at a6e93981; not confirmed with the owner by the verifier)"
    accepted_at: "2026-11-19 (time of day not recorded)"
  - must_have: "Ordinary line shifts are preserved by the shape 1 repair (999.44 bound: 'Preserve ordinary line shifts')"
    reason: "Review item WR-01: when the shape 1 re-ask fires, another deferred or dismissed decision within 5 lines of the relocated line is asked again although its code only shifted. Over-ask only, never a silent keep. Owner ruling: accept and record, no score.py change. Locked by test_wr01_neighbour_of_forced_reask_is_reasked_owner_accepted and two mutants (fa5afc55)."
    accepted_by: "owner (ruling relayed by the orchestrator and recorded in ROADMAP 999.44, 66-VALIDATION.md, 66-REPLAY.md 6.4 and commit fa5afc55; not confirmed with the owner by the verifier)"
    accepted_at: "2026-11-19 (time of day not recorded)"
re_verification:
  number: 2
  previous_status: gaps_found
  previous_score: 15/18 (roadmap success criteria 4/4; 2 minor gaps, 1 awaiting an owner decision)
  previous_commit: 97fbaf9f (report committed as 2dc3f46d)
  gaps_closed:
    - "Gap 1 (minor), records lagged the code: ROADMAP 999.44 now names the non-ASCII difference and the WR-01 behaviour and candidate fa5afc55; 66-REPLAY.md section 6 and 66-VALIDATION.md carry the fa5afc55 re-run and the new rows; the gap-closure review's carried items are in new backlog item 999.47. CLOSED."
    - "Gap 2 (minor), WR-01 neighbour over-ask: owner ruling accept and record; locked by a test and two mutants. CLOSED under owner ruling (override 2). WR-03 carried to backlog 999.47."
    - "Uncertain item, non-ASCII file names in NEARBY_LINE_RANGES versus 2.15.0: owner ruling keep as an intended difference; recorded. CLOSED under owner ruling (override 1)."
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Live shape 1 journey in a real session: Close out refuses once, the fresh review asks about the moved decision again, Close out writes only after the owner decides again"
    addressed_in: "Phase 71"
    evidence: "Phase 71 success criterion 3: 'live checks run only under an owner-approved bounded proposal, otherwise they are listed as pending or explicitly waived, never as passed; a pending required check prevents the publication-readiness claim' (GATE-08). Phase 66 records say 'no live check was run (GATE-08)' (ROADMAP 999.44) and 'Evidence class: OFFLINE' (66-VALIDATION.md, 66-REPLAY.md)."
  - truth: "Live Close out refusal in a real session: the 'Cannot finalize' list, the same-scope review command, the paid-reviewers sentence, no REVIEW.md, no reviewer started"
    addressed_in: "Phase 71"
    evidence: "Same Phase 71 success criterion 3 and GATE-08."
---

# Phase 66: Close out freshness — Verification Report (re-verification #2)

**Phase Goal:** Close out never completes on a deferred or dismissed decision whose reviewed code changed since the review, and the three bounded legacy wrong-keep shapes each end with an evidence-backed outcome.
**Verified:** 2026-11-19T11:45:00Z, at a6e93981 (code HEAD fa5afc55), clean tree before and after
**Status:** passed (offline evidence; two items passed under owner rulings; two live checks deferred to Phase 71)
**Re-verification:** Yes — #2, after the owner rulings of 2026-11-19, the WR-01 lock (fa5afc55) and the records update (a6e93981)
**Evidence class:** offline only. Nothing here is a live reviewer run or a live session.

## Summary

All three open items from the previous report are closed. Nothing regressed.

- **Records now match the code.** I read each updated record against HEAD and ran every test it names. All exist and pass, and the counts in the records match my own runs exactly.
- **The WR-01 lock is real.** In a scratch clone, four separate mutants each make it fail, including two that edit the real scorer.
- **The two owner rulings are recorded** in the roadmap, the validation file and the replay file. I applied them as overrides. I did not confirm them with the owner myself; they reached me through the orchestrator and the committed records.
- **Live checks are not Phase 66 gaps.** The phase records say no live check was run, and Phase 71 success criterion 3 (GATE-08) owns them. They are listed under Deferred Items so Phase 71 picks them up.

Three bookkeeping items for the orchestrator are listed at the end. None affects the verdict.

## Prior items: all closed

| Prior item | Now | Evidence (run by me at a6e93981) |
|------------|-----|----------------------------------|
| Gap 1 (minor): records lagged the code | CLOSED | See "Records check" below. Every named test exists and passes; every recorded count matches my run. |
| Gap 2 (minor): WR-01 neighbour over-ask, and WR-03 | CLOSED under owner ruling | Lock test and two mutants pass (3 passed, 6 subtests). My four scratch-clone mutants each fail the lock. WR-03 is in backlog 999.47. |
| Uncertain: non-ASCII names in `NEARBY_LINE_RANGES=` versus 2.15.0 | CLOSED under owner ruling | Recorded in ROADMAP 999.44, the amended Phase 60 row, 66-VALIDATION.md and 66-REPLAY.md 6.4. `TestQuotedNamesDifferentialV215`: 2 passed. |
| Owner rulings SA-01 and SA-02 (previously listed as human items) | Parked by the owner in backlog 999.47 | 999.47 lists both with "Ruling needed". Neither was reproduced. Not Phase 66 gaps. |
| Live shape 1 journey; live Close out refusal | DEFERRED to Phase 71 | Phase 71 success criterion 3 and GATE-08. |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: 999.40 reproduction fails on 2.15.0; candidate refuses for both kinds on exact-line and nearby edits, asks for a fresh review, never starts a paid reviewer | VERIFIED (regression check) | `test_closeout_fresh.py` in full: green. No shipped code changed since the previous report (`git diff --stat 97fbaf9f HEAD -- plugins` shows one test file only). |
| 2 | SC2: unchanged code closes for both kinds exactly as on 2.15.0; fix-verdict freshness, 999.28 parity, real-edit reopening pass | VERIFIED (regression check) | Full suite green. Parity grid: 284 scenarios, 198 agree, 12 D-19, 56 D-09 refusals, 0 unexpected. |
| 3 | SC3: each 999.44 shape has a repair, safe refusal or recorded non-reproduction; D-21 distinguished; no identity redesign | VERIFIED | Shape 1 repaired, shape 2 repaired, shape 3 refused. `score.py` and `diff_ranges.py` byte-identical to d5acc19 (`git diff --quiet`, exit 0). |
| 4 | SC4: replay against 2.15.0 differs only by the intended refusals | VERIFIED | Scorer replay re-run at a6e93981: 170 compared, 0 differing, base and candidate sha256 identical. `-k "DifferentialV215 or only_intended"`: 12 passed, 428 subtests. The review-side differences are all named and owner-accepted. |
| 5 | Every refusal cause is clearable | VERIFIED (regression check) | Full suite green. |
| 6 | The Close out check fails closed | VERIFIED (regression check) | Unchanged shipped code; full suite green. |
| 7 | `--all` records `reviewed_tree` (D-12) | VERIFIED (regression check) | Unchanged; full suite green. |
| 8 | No decision-closed record means no git call and the 2.15.0 result keys | VERIFIED (regression check) | Differential run above. |
| 9 | Records state the outcome truthfully (ROADMAP 999.44, 66-VALIDATION.md, 66-REPLAY.md) | VERIFIED (was PARTIAL) | See "Records check". |
| 10 | 66-10: `collect` prints exactly three lines; removed lines are exact; unknown is never printed as `{}` | VERIFIED (regression check) | `test_worktree_snap.py` in full: green. |
| 11 | 66-10: first two collect lines and the exit code byte-identical to 2.15.0 on every route and grid state | PASSED (override) | Override 1: owner ruling 2026-11-19, keep the non-ASCII difference. Holds on all 13 grid states and for still-quoted names (`test_still_quoted_name_first_two_lines_identical_third_empty`). |
| 12 | 66-11: shape 1 repaired for defer and dismiss | VERIFIED (regression check) | Named shape 1 tests: 16 passed, 18 subtests. |
| 13 | 66-11: Close out on that pass does not write and is not the code-changed refusal; after re-deciding it writes | VERIFIED (regression check) | `test_shape1_closeout_does_not_write_on_deleted_original` passes. |
| 14 | 66-11: controls unchanged and passing; ordinary line shifts preserved | PASSED (override) for the WR-01 exception; controls VERIFIED | Override 2: owner ruling 2026-11-19, accept and record. D-21, 20-line insertion and same-edit copy controls pass. The lock also asserts that a decision 20 lines away is kept. |
| 15 | 66-11: two-sided differential against literal 2.15.0 | VERIFIED (regression check) | `TestShape1DifferentialV215` in the 12-test run above. |
| 16 | Each guard is load-bearing; no `expectedFailure` on shape 1 | VERIFIED | No `expectedFailure`, skip or xfail in the four touched test files. New lock mutation-tested below. |
| 17 | 66-12: through the real prose fences, both kinds | VERIFIED (regression check) | `TestShape1ThroughFences`, `TestShape1ThroughFencesRange`, `TestShape1Clearable` pass. |
| 18 | 66-12: re-ask on missing evidence implemented and recorded | VERIFIED (regression check) | `test_shape1_no_removal_evidence_reasks`, `test_shape1_without_recorded_tree_reasks` pass; record unchanged. |

**Score:** 18/18 (16 verified, 2 passed under owner rulings). Roadmap success criteria 4/4.

### Deferred Items

Not yet met, and explicitly owned by a later phase.

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Live shape 1 journey in a real session | Phase 71 | Success criterion 3: live checks run only under an owner-approved bounded proposal, otherwise listed as pending or waived, never as passed (GATE-08) |
| 2 | Live Close out refusal in a real session | Phase 71 | Same |

Both stay pending. They are not reported as passed here. Under GATE-08 a pending required live check prevents the publication-readiness claim at Phase 71, not the completion of Phase 66.

### Records check (prior gap 1)

| Record | Claim | Checked against HEAD | Result |
|--------|-------|----------------------|--------|
| ROADMAP 999.44, shape 1 paragraph | Four named scenarios plus the owner-accepted non-ASCII difference; WR-01 known behaviour; candidate fa5afc55; `score.py` byte-identical to d5acc19 | "exactly the four" wording is gone. Named tests exist and pass. Byte identity confirmed. | TRUE |
| ROADMAP 999.44, closing line | Satisfied offline on 475b2e32, re-run on fa5afc55, pending re-verification, no live check | Matches the evidence | TRUE |
| ROADMAP 999.47 (new) | WR-03, IN-01..04, SA-01, SA-02 of the gap-closure review, not scheduled | Item list matches the headings in 66-REVIEW.md. IN-01 (`since()` has no caller) and IN-02 (docstring says "with both empty") confirmed in `worktree_snap.py`. | TRUE |
| ROADMAP 999.47 format | Consistent with 999.46 and PLANNING-FORMAT.md | `### 999.47: Carried: ...` under `## Backlog`, same shape as 999.46, same closing "Promote an item only if" line. PLANNING-FORMAT.md accepts any `###` heading under Backlog as a tile. | CONSISTENT (see note 3) |
| ROADMAP Phase 60 R7/R8/R10/R11 row | Original accepted limit kept with its date; amendment dated 2026-11-19; still-quoted and non-UTF-8 names remain unsupported and fail safe | History preserved, amendment matches the code and `TestQuotedNamesCR01` / `TestRemovedRiskyInputs` | TRUE |
| 66-REPLAY.md section 6.1 | Replay 170 compared, 0 differing, sha256 `c6488729...` both sides | My re-run: identical numbers and hash | TRUE |
| 66-REPLAY.md section 6.2 | Plugin suite 4340 passed, 0 xfailed, 2 warnings, 7132 subtests; stdlib check 35 files, none third-party; states that the three-root command was not re-run | My full run at a6e93981: 4340 passed, 2 warnings, 7132 subtests, exit 0. Stdlib check: same. | TRUE |
| 66-REPLAY.md section 6.3 | `-k "DifferentialV215 or only_intended"`: 12 passed, 4328 deselected, 428 subtests | My run: identical | TRUE |
| 66-REPLAY.md section 6.4 | The two owner-accepted differences and their tests | Tests exist and pass | TRUE |
| 66-VALIDATION.md new rows | `TestQuotedNamesCR01` 5 passed; `TestRemovedRiskyInputs` 10 passed; `TestQuotedNamesDifferentialV215` 2 passed; `TestQuoteAndBodyMutants` 5 passed; WR-01 lock 3 passed, 6 subtests | My runs: 5, 10, 2, 5, and 3 passed with 6 subtests | TRUE |
| 66-VALIDATION.md evidence paragraph and known-behaviour notes | fa5afc55 run, both owner-accepted behaviours | Match | TRUE |

a6e93981 is documents only: `git diff --stat fa5afc55 a6e93981` lists ROADMAP.md, 66-REPLAY.md and 66-VALIDATION.md, nothing else.

### WR-01 lock: mutation checks (prior gap 2)

The lock is `TestShape1DeletedOriginal::test_wr01_neighbour_of_forced_reask_is_reasked_owner_accepted`. It builds three decided findings, deletes one decided line so that decision moves, and runs the real scorer and state chain for both decision kinds. It asserts the moved decision and the one 3 lines away are asked again and the one 20 lines away is kept.

My own mutants, in a scratch clone at a6e93981 (repository untouched):

| Mutant | Result | Verdict |
|--------|--------|---------|
| Real `score.py`: window 5 lines changed to 2 | Lock fails | Load-bearing against a scorer change |
| Real `score.py`: window changed to 0 (exact line only, the rejected alternative applied to every range) | Lock fails | Load-bearing |
| Test simulator never adds the forced pair | Lock fails | Not vacuous |
| Neighbour moved out of the window (old line 53 to 60) | Lock fails | The distance assertions are real |

The two committed mutant tests are sound: `test_mutant_moved_record_only_trips_the_neighbour_lock` first runs the lock unpatched (passes), then patches the scorer's window in-process and shows both that the lock fails and that the neighbour comes back `current`, which proves the patch took effect. `score.py` on disk is not edited.

One limit, unchanged from before: the model's step (adding the forced pair) is played by a test simulator locked to the prose wording. The scorer and state code are real. That is why the live journey stays deferred.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/test_decision_continuity.py` | `neighbour_scenario`, the WR-01 lock, two mutants | VERIFIED | Added in fa5afc55 (112 lines); whole file green |
| `plugins/vibe-check/scripts/worktree_snap.py`, `phases/review/30-collect-score.md`, `closeout_fresh.py`, `finalize_inputs.py`, `carry_state.py`, `90-finalize.md` | Phase 66 shipped code | VERIFIED (no regression) | Unchanged since the previous report |
| `.planning/ROADMAP.md` 999.44, 999.47, Phase 60 row | Truthful records | VERIFIED | Records check above |
| `66-REPLAY.md` section 6, `66-VALIDATION.md` | Truthful records | VERIFIED | Records check above |

### Key Link Verification

No shipped code changed since the previous report, so the six key links verified there are carried forward unchanged (collect to removed-lines parser, collect output to the prose, step 0 to the forced re-ask, forced pair to the scorer stamp, Finalize to the freshness check, command files to 90-finalize.md). The full suite, which includes the prose locks, is green.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full plugin suite at a6e93981 | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider` | **4340 passed, 0 failed, 2 warnings, 7132 subtests passed, 405.77 s, exit 0** | PASS |
| 2.15.0 differentials | `pytest -q -k "DifferentialV215 or only_intended"` | 12 passed, 4328 deselected, 428 subtests | PASS |
| Three phase test files | `pytest -q test_decision_continuity.py test_worktree_snap.py test_closeout_fresh.py` | 404 passed, 978 subtests | PASS |
| WR-01 lock and mutants | `pytest -q test_decision_continuity.py -k "test_wr01_neighbour or trips_the_neighbour_lock"` | 3 passed, 6 subtests | PASS |
| Named shape 1 tests and controls | nine names from ROADMAP 999.44 by `-k` | 16 passed, 18 subtests | PASS |
| Scorer replay vs 2.15.0 | `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>` | 170 compared, 0 differing, head a6e93981 | PASS |
| Byte identity | `git diff --quiet d5acc19 HEAD -- score.py diff_ranges.py`; `git diff --quiet dd8e4ab HEAD -- guard.py finalize_gate.py fixcommit.py` | both exit 0 | PASS |
| Stdlib check | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | 35 shipped .py files, third-party imports: none, exit 0 | PASS |

Not re-run here: `.github/scripts` and `docs/design/lean-v2.15/tools` tests (475 passed at 97fbaf9f). No file under those paths changed since.

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| FRESH-01 | Close out refuses stale deferred or dismissed decisions, asks for a fresh review, never starts paid reviewers | SATISFIED (offline) | Truths 1, 5, 6, 7 |
| FRESH-02 | Unchanged code still closes; fix-verdict freshness, 999.28 parity, real-edit reopening as in 2.15.0 | SATISFIED (offline) | Truths 2, 4, 8. The three owner-accepted differences occur only when code changed or evidence is missing. |
| FRESH-03 | Each of the three 999.44 shapes has an evidence-backed outcome | SATISFIED (offline) | Shape 1 repaired, shape 2 repaired, shape 3 safely refused |

No orphaned requirements: REQUIREMENTS.md maps only FRESH-01..03 to Phase 66.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `phases/review/30-collect-score.md` | 110 | The "Why" sentence says the stamp lands "on the moved record"; a neighbour within 5 lines is stamped too (WR-01) | Info | Model-facing explanation only. The behaviour is owner-accepted and recorded in the planning files. No user-visible effect. |
| `test_decision_continuity.py` | simulator | Records Needs-verification moves that the prose excludes (WR-03) | Info | In backlog 999.47; no fixture exercises it |
| `worktree_snap.py` | `since()`, `collect` docstring, `DIFF_FLAGS` | IN-01, IN-02, IN-03 | Info | In backlog 999.47 |

No TBD, FIXME, XXX, TODO or HACK marker, and no skip or `expectedFailure`, was added by fa5afc55.

### Human Verification Required

None for this phase. The two live checks are deferred to Phase 71 (see Deferred Items).

### Gaps Summary

No gaps. The phase goal is achieved on offline evidence: Close out refuses a deferred or dismissed decision whose reviewed code changed, unchanged code closes as on 2.15.0, each of the three 999.44 shapes has a tested outcome, and the differences from 2.15.0 are all named and owner-accepted.

## Notes for the orchestrator (bookkeeping, not gaps)

1. **STATE.md is stale.** It says "Plan: 10 of 12", `completed_plans: 9`, and the next step is still `/bm:execute-phase 66 --gaps-only`. All twelve plans are checked in ROADMAP. Update at phase close.
2. **ROADMAP line 65** still reads "12 plans (9 executed; 3 gap-closure plans ... planned 2026-11-18)" although all twelve are checked. **REQUIREMENTS.md** still shows FRESH-01..03 unchecked and "Pending".
3. **Backlog heading prefix.** `Carried:` (999.46 and 999.47) is not one of the status prefixes PLANNING-FORMAT.md recognises (`Keep:`, `Narrow:`, `Retired:`, `Deferred:`), so the Roadmaps page will show these two tiles without a status and with "Carried:" as part of the title. 999.47 is consistent with 999.46. I could not check the Roadmaps page from here.

## Owner decisions on record

- **2026-11-18:** wider repair for shape 1; re-ask on missing removal evidence.
- **2026-11-19:** keep the non-ASCII file name difference from 2.15.0 (override 1).
- **2026-11-19:** accept and record the WR-01 neighbour re-ask, no scorer change (override 2).
- **2026-11-19:** WR-03, IN-01..04, SA-01 and SA-02 of the gap-closure review carried to backlog 999.47.

The 2026-11-19 rulings reached me through the orchestrator and the committed records. I did not confirm them with the owner.

---

_Verified: 2026-11-19T11:45:00Z_
_Verifier: Claude (bm-verifier)_
