---
phase: 66-close-out-freshness
verified: 2026-11-19T02:52:11Z
status: gaps_found
score: 15/18 must-haves verified (roadmap success criteria 4/4; 2 partial with minor severity, 1 awaiting an owner decision)
has_blocking_gaps: false
overrides_applied: 0
verified_commit: 97fbaf9f (code HEAD cb2da984; last shipped-code change e3888c9c), branch feat/v2.16-phase-66, clean tree
evidence_class: offline only (no live reviewer run, no live session)
re_verification:
  previous_status: gaps_found
  previous_score: 8/9 (roadmap success criteria 3/4)
  gaps_closed:
    - "SC3 / FRESH-03: 999.44 shape 1 (deleted-original relocation) had the outcome 'owner-accepted known limit', which is none of the three allowed outcomes. Now repaired: the fresh review re-asks the decision for defer and dismiss, Close out does not write until the owner decides again, and writes after (no loop). CLOSED, offline evidence."
  gaps_remaining: []
  regressions: []
gaps:
  - truth: "Records are truthful: ROADMAP 999.44, 66-VALIDATION.md and 66-REPLAY.md state the differences from 2.15.0 and the candidate the evidence was taken on (66-12 must-have; prior truth 9)"
    status: partial
    severity: minor
    reason: "The CR-01 review fix (e3888c9c) changed shipped code after the recorded candidate 475b2e32 and added one more difference from 2.15.0 (non-ASCII file names now appear in NEARBY_LINE_RANGES). ROADMAP 999.44 still says the intended differences are 'exactly the four named scenarios'; 66-VALIDATION.md and 66-REPLAY.md do not mention the fifth difference and name 475b2e32 as the candidate. The carried gap-closure review items (WR-01, WR-03, IN-01..04, SA-01, SA-02) are recorded only in 66-REVIEW-FIX.md; backlog 999.46 lists the earlier review's items, not these."
    artifacts:
      - path: ".planning/ROADMAP.md"
        issue: "999.44 shape 1 paragraph: 'Intended differences from 2.15.0 are exactly the four named scenarios' is no longer complete; candidate 475b2e32 predates e3888c9c. 999.46 does not hold the gap-closure review's carried items."
      - path: ".planning/phases/66-close-out-freshness/66-REPLAY.md"
        issue: "Section 5 is the 475b2e32 run; 5.4 says the first two collect lines are byte-identical to d5acc19 without the non-ASCII exception. No re-run recorded at the post-review-fix commit."
      - path: ".planning/phases/66-close-out-freshness/66-VALIDATION.md"
        issue: "Evidence paragraph and shape 1 rows name 475b2e32; no row for TestQuotedNamesCR01 / TestQuotedNamesDifferentialV215 / TestRemovedRiskyInputs; the non-ASCII difference is not listed under known behaviour."
    missing:
      - "Add the non-ASCII NEARBY_LINE_RANGES difference to ROADMAP 999.44 and 66-VALIDATION.md as a named difference (once the owner accepts it, see human_verification item 2)"
      - "Record the re-run at the post-review-fix commit in 66-REPLAY.md (numbers from this report: replay 170 compared / 0 differing; plugin suite 4337 passed, 0 xfailed)"
      - "Record WR-01, WR-03, IN-01..04, SA-01 and SA-02 of the gap-closure review in the backlog (999.46 or a new item)"
  - truth: "Ordinary line shifts are preserved by the shape 1 repair (999.44 bound: 'Preserve ordinary line shifts')"
    status: partial
    severity: minor
    reason: "Review item WR-01, reproduced here. The forced re-ask is sent as a one-line range that score.py reads with its usual 5-line window, so a second, unrelated deferred or dismissed decision within 5 lines of where the first decision's text was found is also asked again, although its own code only shifted. It never keeps a decision silently; it asks one extra question, and only in a pass where the shape 1 re-ask fires. No test or differential scenario covers it, so it is not among the named intended differences."
    artifacts:
      - path: "plugins/vibe-check/phases/review/30-collect-score.md"
        issue: "Line 110: the forced pair goes into the shared nearby_line_ranges map; the 'Why' sentence says the stamp lands 'on the moved record', which understates the effect"
      - path: "plugins/vibe-check/scripts/test_decision_continuity.py"
        issue: "SHAPE1_GRID has no scenario with a second decision near the relocated line"
    missing:
      - "Owner choice between: (1) accept and record the extra re-ask as known behaviour, with a locked grid scenario; or (2) stamp only the moved record, which needs a score.py change and an owner ruling against the 'score.py byte-identical to 2.15.0' constraint"
      - "WR-03 (test simulator records Needs-verification moves, the prose excludes them): align once the owner rules on SA-01; no user-visible effect today because no fixture carries a decided Needs-verification record"
human_verification:
  - test: "Live shape 1 journey: defer or dismiss a finding, delete the decided line while an identical line exists elsewhere in the file, run Close out, then run the review it asks for, then Close out again"
    expected: "First Close out refuses and names the review command. The fresh review asks the owner about the decision again (it is not carried silently to the identical line). Close out does not write until the owner decides again, and writes after."
    why_human: "The repair is an instruction the model follows in 30-collect-score.md plus a helper output. Offline, the helper is real but the model's step is played by a test simulator that is locked to the prose wording. A real session was not run. Under GATE-08 a live check needs an owner-approved bounded proposal; pending for the Phase 71 release gate."
  - test: "Owner decision: accept or reject the non-ASCII file name difference from 2.15.0 introduced by review fix e3888c9c"
    expected: "Either an override recorded in this file (accept) plus the record updates listed in the first gap, or a request to restore the 2.15.0 second line for such names"
    why_human: "Product scope, not a defect a verifier can rule on. 66-10 promised the first two collect lines byte-identical to 2.15.0; they still are on every state the plan listed, but not for files with non-ASCII names. The change errs toward asking again. ROADMAP line 521 lists non-ASCII paths as a previously accepted unsupported limit, so this changes an accepted limit without a recorded owner decision."
  - test: "Owner ruling on SA-01 (gap-closure review): a deferred or dismissed Needs-verification item whose recorded snippet was deleted while an identical snippet exists elsewhere"
    expected: "Ruling: re-ask it like an ordinary decision (in scope for shape 1) or let it follow its text as designed (accept)"
    why_human: "The repair covers ordinary decided records only. The 999.44 shape 1 record and its reproduction are about ordinary findings, and Needs-verification relocation by text is deliberate earlier design, so the spec does not settle it. Not reproduced by the review or by this verification."
  - test: "Owner ruling on SA-02 (gap-closure review): a decision moves to a nearer pre-existing identical line while its own line only shifted"
    expected: "Ruling: accept under the 999.31 identity exclusion, or extend the forced re-ask"
    why_human: "Outside the three named shapes (the original is not deleted) and the roadmap excludes decision-identity redesign; whether to widen is a scope decision."
  - test: "Live Close out refusal (carried from the first verification): defer or dismiss a finding, edit the decided line, run Close out"
    expected: "'Cannot finalize' list with file:line, title, kind and cause; the same-scope review command; the paid-reviewers sentence; no REVIEW.md; no reviewer started"
    why_human: "The model rendering 90-finalize.md in a real session was not run (GATE-08); pending for Phase 71."
---

# Phase 66: Close out freshness — Verification Report (re-verification)

**Phase Goal:** Close out never completes on a deferred or dismissed decision whose reviewed code changed since the review, and the three bounded legacy wrong-keep shapes each end with an evidence-backed outcome.
**Verified:** 2026-11-19T02:52:11Z, at 97fbaf9f (code HEAD cb2da984), clean tree before and after
**Status:** gaps_found — minor gaps only (`has_blocking_gaps: false`)
**Re-verification:** Yes — after gap closure (plans 66-10, 66-11, 66-12 and the gap-closure review fixes CR-01, WR-02)
**Evidence class:** offline only. Nothing here is a live reviewer run or a live session.

## Summary

**The prior blocking gap is closed.** The first verification failed SC3 because 999.44 shape 1 (the decided line is deleted while an identical line exists elsewhere) was left as a known limit. The owner chose the wider repair on 2026-11-18. At current HEAD the fresh review re-asks that decision for both defer and dismiss, Close out does not write until the owner decides again, and then writes with no loop. I ran the named tests, wrote my own probe, and mutation-tested the guards in a scratch clone. All four roadmap success criteria now hold on offline evidence, and FRESH-01, FRESH-02 and FRESH-03 are satisfied offline.

What remains is not goal-blocking:

1. **Two minor gaps.** The planning records were not updated after the review fix (they name an older candidate and say "exactly four" differences when there are now five). And the repair asks one extra question in a narrow case (review item WR-01).
2. **One owner decision on a deliberate difference.** The review fix makes files with non-ASCII names behave differently from 2.15.0 on the review side. I judge it a reasonable, tested change that errs toward asking again, but it is not owner-accepted and not in the phase records, so I have not marked it passed or failed. See "Owner decisions requested".
3. **Two owner rulings carried from the review** (SA-01, SA-02) and the live checks, which stay pending under GATE-08.

## Prior gap: closed

| Prior gap | Now | Evidence (run by me at HEAD) |
|-----------|-----|------------------------------|
| SC3 / FRESH-03 shape 1: reproduced wrong keep, neither repaired nor refused (2 `expectedFailure` tests) | CLOSED — repaired | `test_decision_continuity.py -k "Shape1 or d21_identical or p4_far_twin or ForcedReask or removed_lookup or forced_"`: 23 passed, 57 subtests, 0 xfailed. `test_worktree_snap.py test_closeout_fresh.py -k Shape1`: 10 passed. No `expectedFailure`, `_known_limit`, skip or xfail remains in the four touched test files. Own probe (below): with the removal evidence the decision is `stale` and the gate is not `write`; with the evidence withheld (the 2.15.0 outcome) it is `current` and the gate is `write`. |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: 999.40 reproduction fails on 2.15.0; candidate refuses for both kinds on exact-line and nearby edits, asks for a fresh review, never starts a paid reviewer | VERIFIED (regression check) | `test_closeout_fresh.py -k "only_intended or repro_999_40 or differential"`: 8 passed, 418 subtests. `finalize_inputs.py:465` still calls `closeout_fresh.stale_decisions` before the result is built; `90-finalize.md` still has the `stop-review-again` branch. `closeout_fresh.py`, `finalize_inputs.py`, `carry_state.py` and `90-finalize.md` are unchanged since the first verification (4cee4e20). |
| 2 | SC2: unchanged code closes for both kinds exactly as on 2.15.0; fix-verdict freshness, 999.28 parity, real-edit reopening pass | VERIFIED (regression check) | Same differential run; full suite green at HEAD including the parity grid (284 scenarios: 198 agree, 12 D-19, 56 D-09 refusals, 0 unexpected). |
| 3 | SC3: each 999.44 shape has a repair, safe refusal or recorded non-reproduction; D-21 distinguished; no identity redesign | VERIFIED (was FAILED) | Shape 1 repaired (truths 12-16). Shape 2 repaired and shape 3 refused, unchanged since the first verification and green in the full suite. D-21 control `test_d21_identical_copy_added_while_original_remains_keeps` passes with its assertions intact. `score.py` and `diff_ranges.py` byte-identical to d5acc19 (`git diff --quiet` exit 0). |
| 4 | SC4: replay against 2.15.0 differs only by the intended refusals | VERIFIED, with one review-side difference awaiting owner acceptance (truth 11) | Scorer replay re-run at 97fbaf9f: 170 runs compared, **0 differing**, exit 0, base and candidate sha256 identical. Finalize differential `-k only_intended`: passes, both directions (76 named refusals, 2 shape 2 repair differences, everything else byte-identical). Review-side differences are the four owner-approved shape 1 scenarios plus the non-ASCII one in truth 11. |
| 5 | Every refusal cause is clearable (refuse, review, re-decide, write) | VERIFIED (regression check) | Clearable classes green in the full suite; `TestShape1Clearable` adds the shape 1 journey. |
| 6 | The Close out check fails closed (missing baseline, git failure, flagged file, unkeyable name) | VERIFIED (regression check) | Unchanged code since the first verification, where each guard was mutation-tested; suite green. |
| 7 | `--all` records `reviewed_tree` (D-12) | VERIFIED (regression check) | `00-scope-all.md:96` take fence, `30-collect-score.md:95` collect fence present; suite green. |
| 8 | No decision-closed record means no git call and the 2.15.0 result keys | VERIFIED (regression check) | `test_differential_*` in the run above. |
| 9 | Records state the outcome truthfully (66-12: ROADMAP 999.44, 66-VALIDATION.md, 66-REPLAY.md) | PARTIAL — minor gap | Shape 1 is recorded as repaired with test names, offline-labelled, and the phase is not marked verified: correct. But the records predate review fix e3888c9c: see Gaps. |
| 10 | 66-10: `collect` prints exactly three lines; `REMOVED_LINE_RANGES=` is exact (only removed lines, old-side numbers); unknown is never printed as `{}` | VERIFIED | Own probe on real git trees: deleting line 10 gives nearby `[[9,10]]`, removed `[[10,10]]`. Mutants in a scratch clone: removed always `{}` fails 8 Shape1 tests; unknown printed as `{}` fails 4 tests. `test_worktree_snap.py -k "DifferentialV215 or QuotedNames or RemovedRisky or Mutants or RemovedFromDiff or CollectRemoved"`: 52 passed, 65 subtests. |
| 11 | 66-10: the first two collect lines and the exit code are byte-identical to 2.15.0 on every route and every grid state | UNCERTAIN — owner decision requested | Holds on all 13 grid states the plan listed, and in my probe for ASCII names, names with a space, and names git still quotes. Does **not** hold for non-ASCII names since e3888c9c: 2.15.0 omitted such a file from `NEARBY_LINE_RANGES=`; HEAD includes it. Deliberate, tested (`TestQuotedNamesDifferentialV215`), documented in code and 66-REVIEW-FIX.md; not owner-accepted, not in ROADMAP / VALIDATION / REPLAY. See "Owner decisions requested" item 1. |
| 12 | 66-11: shape 1 repaired for defer and dismiss: the fresh review re-asks (stale, at the line the text was found), with or without the reviewer re-reporting; also when the line was replaced in place and when evidence is missing | VERIFIED | `test_shape1_deleted_original_is_reasked_at_pass2`, `test_shape1_edited_in_place_with_copy_elsewhere_reasks`, `test_shape1_no_removal_evidence_reasks`, `test_shape1_member_move_is_reasked` pass. Own probe: decision A at old line 10, copy at 50, line 10 deleted: A is `stale` at line 49 for both kinds. |
| 13 | 66-11: Close out on that pass does not write and is not the code-changed refusal; after re-deciding it writes (no loop) | VERIFIED | `test_shape1_closeout_does_not_write_on_deleted_original` runs the real `finalize_inputs.run` and asserts `next != stop-review-again`, `action != write`, then `write` after `decide_on`. Own probe: gate `outstanding-to-phase-5` with the repair, `write` without. |
| 14 | 66-11: controls unchanged and passing: D-21 copy added keeps, 20-line insertion keeps, same-edit copy re-asks at 48, far twin test unmodified | VERIFIED on the named controls; one narrow exception is a minor gap | All four named controls pass. Own probe: a second decision 20 lines away is kept. Exception (WR-01): a second decision within 5 lines of the found copy is also re-asked. See Gaps. |
| 15 | 66-11: two-sided differential against literal 2.15.0: only `shape1_kept`, `shape1_edited`, `no_evidence_shape1`, `no_evidence_shift` differ; the forced re-ask never changes a score | VERIFIED | `TestShape1DifferentialV215` (both directions) and `test_forced_pair_never_changes_a_score` pass; `score.py` byte-identical to d5acc19. |
| 16 | 66-11 / 66-12: each new guard is load-bearing; prose phrases have deletion mutants; no `expectedFailure` on shape 1 | VERIFIED | My own mutants in a scratch clone (table below), not the SUMMARY's counts. |
| 17 | 66-12: through the real prose fences, both kinds; the 2.15.0 review-side procedure writes | VERIFIED | `TestShape1ThroughFences`, `TestShape1ThroughFencesRange`, `TestShape1Clearable` (incl. `test_shape1_old_review_procedure_writes`): 10 passed. |
| 18 | 66-12: owner-chosen "re-ask on missing evidence" is implemented and recorded as a known, intended difference | VERIFIED | Implemented: prose line 110 ("when the printed `REMOVED_LINE_RANGES=` value is empty ... must be re-asked") and `forced_reask_pairs(moves, None)`; pinned by `test_shape1_no_removal_evidence_reasks`, `test_shape1_without_recorded_tree_reasks` and the two `no_evidence_*` differential scenarios. Recorded: ROADMAP 999.44 ("Known behaviour (owner decision 2026-11-18) ... asked again, where 2.15.0 kept it") and 66-VALIDATION.md ("Known behaviour (owner decision 2026-11-18)"). |

**Score:** 15/18 verified; 2 partial (both minor); 1 uncertain (owner decision). Roadmap success criteria 4/4.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/worktree_snap.py` | `removed_from_diff`, `since_both`, three-line collect | VERIFIED | Real parser over the single since-review diff; no new git call or import; wired into `collect` and `run` |
| `plugins/vibe-check/phases/review/30-collect-score.md` | `$MOVED_DECIDED` in step 0, forced re-ask rule in step 2, envelope note in step 4 | VERIFIED | Lines 55, 108, 110 and the step 4 envelope bullet; deleting either paragraph fails the prose locks |
| `plugins/vibe-check/scripts/test_decision_continuity.py` | `forced_reask_pairs`, repaired shape 1 tests, differential, mutants | VERIFIED | No `expectedFailure`; tests assert real state through the real scorer and `finalize_inputs` |
| `plugins/vibe-check/scripts/test_nv_render.py` | forced re-ask prose lock | VERIFIED | 40 passed, 132 subtests |
| `plugins/vibe-check/scripts/test_worktree_snap.py` | `TestShape1ThroughFences`, collect differential, quoted-name tests | VERIFIED | |
| `plugins/vibe-check/scripts/test_closeout_fresh.py` | `TestShape1Clearable` | VERIFIED | |
| `closeout_fresh.py`, `finalize_inputs.py`, `carry_state.py`, `90-finalize.md` | 66-01..09 artifacts | VERIFIED (no regression) | Unchanged since 4cee4e20 |
| `.planning/ROADMAP.md` 999.44, `66-VALIDATION.md`, `66-REPLAY.md` | Truthful gap-closure records | PARTIAL | Correct for 475b2e32; stale after e3888c9c (see Gaps) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `worktree_snap.collect` | `removed_from_diff` | `since_both` parses the one diff twice | WIRED | Mutant "always `{}`" fails 8 Shape1 tests |
| `worktree_snap.run` | stdout | third printed line `REMOVED_LINE_RANGES=` | WIRED | Only consumer of the collect output is `30-collect-score.md`; no other file assumes two lines |
| step 0 `$MOVED_DECIDED` | step 2 forced re-ask | `REMOVED_LINE_RANGES=` value | WIRED in prose; model execution not run | Removing either sentence fails `test_nv_render.py` |
| forced pair | `score.py` `_stamp_ranges` / `snapshot.nearby_at` | envelope `nearby_line_ranges` | WIRED | `test_forced_map_is_well_formed_for_the_scorer`; own probe shows the pair `[49,49]` in the map and the decision `stale` |
| `finalize_inputs._run` | `closeout_fresh.stale_decisions` | call before the result | WIRED | Unchanged |
| `commands/review.md`, `commands/deep-review.md` | `phases/shared/90-finalize.md` | finalize route table | WIRED | Unchanged |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full plugin suite at HEAD | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider` | **4337 passed, 0 failed, 0 xfailed, 0 skipped, 2 warnings, 7126 subtests passed, 567.04 s, exit 0** (the 2 warnings are the parity-grid summaries) | PASS |
| CI-script and design-tool tests | `pytest -q -p no:cacheprovider .github/scripts docs/design/lean-v2.15/tools` | 475 passed, 274 subtests, exit 0 (4812 passed across all three paths) | PASS |
| Scorer replay vs 2.15.0 | `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>` | 170 compared, **0 differing**, exit 0, head 97fbaf9f | PASS |
| Finalize differential | `test_closeout_fresh.py -k "only_intended or repro_999_40 or differential"` | 8 passed, 418 subtests | PASS |
| Shape 1 unit, controls, mutants | `test_decision_continuity.py -k "Shape1 or d21_identical or p4_far_twin or ForcedReask or removed_lookup or forced_"` | 23 passed, 57 subtests | PASS |
| Shape 1 through the fences and Close out | `test_worktree_snap.py test_closeout_fresh.py -k Shape1` | 10 passed | PASS |
| Stdlib check | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | 35 shipped .py files; third-party imports: none; exit 0 | PASS |
| Byte identity | `git diff --quiet d5acc19 -- score.py diff_ranges.py`; `git diff --quiet dd8e4ab HEAD -- guard.py finalize_gate.py fixcommit.py` | both exit 0 | PASS |

### Own probes (scratch files only, repository untouched)

**Shape 1 and its neighbour (real scorer and state, real git diff).** Decision A at line 10 with an identical line at 50; decision B elsewhere; line 10 deleted; no reviewer finding at pass 2.

| Case | A | B | Gate |
|------|---|---|------|
| B 20 lines away, repair on (defer and dismiss) | stale at 49 | current at 29 | not write |
| B 20 lines away, removal evidence withheld (2.15.0 outcome) | current at 49 | current at 29 | write |
| B at old line 53 (3 lines from the copy), repair on (dismiss) | stale at 49 | **stale at 52** | not write |
| Same, evidence withheld | current at 49 | current at 52 | write |

The third row is review item WR-01: B's code only shifted, and it is asked again.

**Collect output against the literal 2.15.0 helper** (d5acc19 `worktree_snap.py` and `diff_ranges.py` extracted to a scratch folder, same two trees):

| File names in the change | Second line (nearby) vs 2.15.0 | Removed lines at HEAD |
|--------------------------|--------------------------------|-----------------------|
| `src/a.py` | identical | `[[10,10]]` |
| + `has space.py` | identical | listed |
| + `q"uote.py` (git still quotes it) | identical | unknown (printed empty, so every move is re-asked) |
| + `café.py` | **differs**: 2.15.0 omits `café.py`, HEAD lists `[[9,10]]` | listed |
| + `文件.py` | **differs**, same way | listed |

### Mutation Checks (scratch clone at 97fbaf9f; working tree clean before and after)

| Mutant | Result | Verdict |
|--------|--------|---------|
| `removed_from_diff` always returns `{}` | 8 Shape1 tests fail | Load-bearing |
| Unknown removed lines printed as `{}` | 4 tests fail | Load-bearing |
| `core.quotePath=false` dropped | 3 tests fail | Load-bearing |
| Forced re-ask paragraph deleted from the prose | 14 tests fail | Prose is locked |
| `$MOVED_DECIDED` sentence deleted from step 0 | 27 tests fail | Prose is locked |
| Test simulator never forces a re-ask | 28 tests fail | The shape 1 tests are not vacuous |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| FRESH-01 | 66-01, 03, 04, 05, 06 | Close out refuses stale deferred/dismissed decisions, asks for a fresh review, never starts paid reviewers | SATISFIED (offline) | Truths 1, 5, 6, 7 |
| FRESH-02 | 66-01, 02, 04, 09 | Unchanged code still closes; fix-verdict freshness, 999.28 parity, real-edit reopening as in 2.15.0 | SATISFIED (offline) | Truths 2, 4, 8. Note: FRESH-02 is about unchanged code; the owner-approved re-ask on missing evidence and WR-01 both occur only when code changed or evidence is missing |
| FRESH-03 | 66-03, 06, 07, 08, 09, 10, 11, 12 | Each of the three 999.44 shapes has a repair, safe refusal or recorded non-reproduction | SATISFIED (offline) — was PARTIAL | Shape 1 repaired (truths 12-17), shape 2 repaired, shape 3 safely refused |

All three IDs are claimed by plans and all three are accounted for. No orphaned requirements: REQUIREMENTS.md maps only FRESH-01..03 to Phase 66. REQUIREMENTS.md still shows them unchecked and "Pending"; that file was not edited here.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `30-collect-score.md` | 110 | Forced pair shares the 5-line window (WR-01) | Minor | One extra re-ask of a neighbouring decision; never a silent keep |
| `test_decision_continuity.py` | 126-217 | Simulator records Needs-verification moves; prose excludes them (WR-03) | Minor | Test-side drift only; no fixture exercises it; resolution depends on SA-01 |
| `worktree_snap.py` | `since()` | Wrapper with no caller (IN-01); `collect` docstring says "both empty" (IN-02) | Info | None for users |
| `worktree_snap.py` | `DIFF_FLAGS` | Rename detection follows the user's git config (IN-03) | Info | Can cause extra re-asks on some machines; never a silent keep |
| ROADMAP 999.44, 66-REPLAY.md, 66-VALIDATION.md | — | Records taken at 475b2e32, before shipped-code change e3888c9c | Minor | See Gaps |

No TBD, FIXME, XXX, TODO or HACK markers were added by this phase (diff d5acc19..HEAD scanned). No `expectedFailure`, skip or xfail in the touched test files.

## Owner decisions requested

These are product calls. I have not marked any of them passed or failed.

### 1. The non-ASCII file name difference (review fix e3888c9c)

**What changed.** On 2.15.0, when a file with a non-ASCII name (for example `café.py`) changed between two reviews, the review did not see that change when deciding whether to re-ask a deferred or dismissed decision in that file. The decision was kept. At HEAD the change is seen, so such a decision is asked again when code within 5 lines of it changed, and the shape 1 repair works for those files too.

**Why it was done.** Without it, the shape 1 repair silently did nothing for these files (review item CR-01, reproduced by the reviewer and confirmed by my probe).

**Why it needs you.** Plan 66-10 promised the first two collect lines byte-identical to 2.15.0. That still holds on every state the plan listed, but not for non-ASCII names. ROADMAP line 521 lists "C-quoted/non-ASCII paths unsupported" as an accepted limit, so this changes behaviour under a limit you had accepted, and the phase records do not mention it.

**My assessment.** Option (a), an acceptable intended difference, is the better reading: it only ever causes an extra question, it removes a silent keep, it is locked by a two-sided test against the literal 2.15.0 helper, and the scorer replay is unaffected (0 of 170 runs differ). It is not a silent pass because it lacks your acceptance and the records are incomplete. The alternative, restoring the 2.15.0 line for these names, would leave shape 1 unrepaired for non-ASCII files unless handled another way.

To accept it, add to this file's frontmatter (and update the records as listed in the first gap):

```yaml
overrides:
  - must_have: "The first two printed lines and the exit code are byte-identical to the 2.15.0 (d5acc19) helper on every route and every grid state"
    reason: "Byte-identical on all 13 grid states; files with non-ASCII names now appear in NEARBY_LINE_RANGES (review fix CR-01, e3888c9c) so their decisions are re-asked instead of silently kept; tested by TestQuotedNamesDifferentialV215"
    accepted_by: "<owner>"
    accepted_at: "<ISO timestamp>"
```

### 2. SA-01: deferred or dismissed Needs-verification items

The repair covers ordinary findings. A Needs-verification item follows its recorded snippet by design. If its snippet is deleted and an identical snippet exists elsewhere, the decision may be kept without asking. Neither the reviewer nor I reproduced this. The 999.44 shape 1 record and reproduction concern ordinary findings, so the spec does not say whether this is in scope. Ruling needed: re-ask, or accept.

### 3. SA-02: move to a nearer identical line while the original only shifted

Outside the three named shapes and inside the decision-identity exclusion (999.31). Ruling needed: accept, or widen the forced re-ask.

### 4. WR-01: accept the extra re-ask, or narrow it

Accepting costs nothing now (record it and lock a test scenario). Narrowing means changing `score.py`, which the phase has kept byte-identical to 2.15.0 and which SC4's replay depends on.

## Human Verification Required

### 1. Live shape 1 journey

**Test:** Defer or dismiss a finding, delete the decided line while an identical line exists elsewhere in the file, run Close out, run the review it asks for, run Close out again.
**Expected:** Close out refuses once; the fresh review asks about the decision again; Close out does not write until the owner decides again, then writes.
**Why human:** The model following the new prose in a real session was not run. Offline, that step is a simulator locked to the prose wording. Pending under GATE-08 for Phase 71.

### 2. Live Close out refusal (carried)

**Test:** Defer or dismiss a finding, edit the decided line, run Close out.
**Expected:** The "Cannot finalize" list, the same-scope review command, the paid-reviewers sentence, no REVIEW.md, no reviewer started.
**Why human:** As above; pending for Phase 71.

## Gaps Summary

No blocking gap. Two minor gaps:

**1. Records lag the code (minor).** The gap-closure records were written at 475b2e32. The review fix then changed shipped code (`worktree_snap.py`, one prose sentence) and added a fifth difference from 2.15.0. ROADMAP 999.44 still says "exactly the four named scenarios"; 66-REPLAY.md and 66-VALIDATION.md carry the older candidate and counts; the gap-closure review's carried items are not in the backlog. The numbers to record are in this report: at 97fbaf9f the replay is 170 compared / 0 differing and the plugin suite is 4337 passed, 0 xfailed. This is a documentation fix, but it should be done before the Phase 71 release gate reads these records.

**2. One extra re-ask next to a relocated decision (minor, WR-01), and the related test drift (WR-03).** When the shape 1 re-ask fires, another deferred or dismissed decision within 5 lines of where the text was found is asked again too, although its code only shifted. It errs toward asking and never keeps a decision silently, so it does not block the goal. It is not in the named differences and no test covers it. WR-03 is a mismatch between the test simulator and the prose for Needs-verification records, with no user-visible effect today.

Neither is covered by a later phase: Phases 67-70 are unrelated and Phase 71 is the release gate. They are not deferred items.

Per the owner's scope rule (new work only for a reproduced gate failure, data loss, silent finding loss or a broken required workflow), neither gap is in a class that adds work to this phase: both err toward asking or are record updates.

## Owner decisions already on record (carried from the first report, not re-confirmed by me)

- **2026-11-18, the gap:** the owner chose the wider repair for shape 1, replacing the 66-07 known-limit choice. No override applied.
- **2026-11-18, missing evidence:** asked whether a moved decision should be re-asked or kept when removal evidence is missing, the owner answered "Re-ask them". A decision whose line only shifted is then asked again in those passes; 2.15.0 kept it.

---

_Verified: 2026-11-19T02:52:11Z_
_Verifier: Claude (bm-verifier)_
