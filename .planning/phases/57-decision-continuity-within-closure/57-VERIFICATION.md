---
phase: 57-decision-continuity-within-closure
verified: 2026-10-27T01:02:00Z
status: gaps_found
score: 3/4 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "Original split-row nearby_at defect (57-VERIFICATION.md gap 1, 57-REVIEW-GAPS.md Critical-1, owner ruling D-17): a covered or absorbed finding that splits into its own row on the pass whose in-window edit caused the split now carries the nearby_at stamp, for the inherited shape and the own-decision-absorbed shape, as long as no fresh re-report out-scores the carried record on that pass. Confirmed independently: `pytest -q test_decision_continuity.py -k \"TestSplitPassNearby or test_split_row_snapshot\"` -> 5 passed; full suite `pytest -q` -> 3259 passed, 0 failed; a hand-written repro (plain B-line fix, no fresh A re-report) gives nearby_at=2, decision_state=stale, gate blocked, as expected."
  gaps_remaining:
    - "SC-3 (minor): changed_line_ranges built from a default-context `git diff` (not -U0) widens the effective nearby/in_diff window from 5 lines to ~8 and makes the 30-collect-score.md deletion-hunk rule unreachable against real diffs. Unchanged since the prior round; parked to deferred-items.md by 57-16; not re-litigated here beyond confirming it is still present and still parked."
  regressions: []
gaps:
  - truth: "SC-4 / DECN-03 — the finding reopens and is presented again when its relevant evidence changes"
    status: failed
    severity: blocking
    reason: "New defect, surfaced by 57-REVIEW-GAPS2.md CR-01 and independently reproduced here on the real score.run -> append_pass -> carry_state chain (no fixtures, no stubs, not read from any SUMMARY). When the SAME reviewer lane re-reports the already-decided finding on the pass that also causes (or coincides with) a nearby edit, and the fresh report out-scores the carried record (reproduced at confidence 100/critical and at confidence 90/critical against a stored confidence 75; confidence alone up to 90 at the carried record's own severity does NOT trip it), the fresh record becomes `best_member`. Its status defaults to \"new\" (no prior snapshot), so 57-15's `carried=` arm never engages, and the lead-obligation prior-seed at score.py:2600-2604 never engages either because a fresh finding's id is never a key in `carried_obligations`. The carried record itself is intercepted by the member-dedup `kept_by_ident` branch (score.py:2619-2636): because the fresh lead shares the same lane-aware occurrence identity, `ref_kept is members[0]` is True, so the `ref_kept is not members[0]` guard (deliberately added by 57-04/273a1e4 to never attach an obligation to \"the lead's own ref\") blocks the obligation transfer before the hash-equality check is even reached. The result: nearby_at is never stamped, decision_state returns \"current\" instead of \"stale\", the hash drops out of outstanding_cw_hashes, and the finalize gate writes — a silent, confirmed wrong-keep. Reproduced for BOTH shapes named in the task: the split shape (B's row absorbs A, B's line is rewritten and resolved, A's own lane re-reports A fresh on the same pass) and the non-split shape (A is its own decided row from pass 1; on pass 2 an in-window edit lands and A's own lane re-reports A fresh) — identical mechanism, identical outcome, with the gate confirmed to write in both. The non-split shape is 57-REVIEW-GAPS2.md's SA-01 (set aside, needs a ruling, not resolved by D-17 — D-17 only answered the split-exemption question). This is NOT pre-Phase-57: `git log -S` on the exact `ref_kept is not members[0]` / hash-equality code confirms it was introduced in 273a1e4 (feat(57-04)), inside this phase, before the second-round work (57-14..57-16). 57-04's own SUMMARY documents the exclusion as deliberate (\"never attached to the lead's own ref\"), and the only two fixtures that exercise this family (57-04's TestObligationPreservingDedup/R5, 57-07's TestSameHashLeadKeepsNearbyStamp) both use a DIFFERENT lane than the carried record, so the same-lane case was never covered by any fixture in the suite — 57-04 did not intend to, and did not, cover this case."
    artifacts:
      - path: "plugins/vibe-check/scripts/score.py"
        issue: "Member dedup (lines ~2619-2636): the `ref_kept is not members[0]` guard, needed to avoid corrupting a genuinely different lead's row, also blocks the legitimate same-lane case where the fresh duplicate IS the carried record's own later re-report. Threshold loop (line ~2687) and the lead-obligation seed (lines ~2600-2604) only look at `best_member`/`id(best_member)`, which is the fresh finding here, not the carried record, so neither path can rescue the stamp once the dedup branch has already `continue`d past it."
      - path: ".planning/REQUIREMENTS.md"
        issue: "DECN-03 is marked `[x]` \"Complete (gap closure 57-08..57-16)\". That marking is not supported by the current code: the SC-4 failure above reproduces on HEAD (1a45e10)."
    missing:
      - "A fix that derives `carried` and seeds the prior from ANY source record sharing the row's final stable_hash (not only `best_member`), as 57-REVIEW-GAPS2.md CR-01 sketches: scan `scored_members` for a carried obligation whose hash equals `survivor[\"stable_hash\"]` and seed from it before `_snapshot_for` runs; derive `carried` the same way in the threshold loop rather than from `survivor.get(\"status\")` alone."
      - "Real-chain RED fixtures for both shapes (split and non-split) with the fresh re-report at a score that out-ranks the carried record in the SAME lane, mirroring this verification's reproduction, plus a mutant on the `ref_kept is not members[0]` guard."
      - "An owner ruling on 57-REVIEW-GAPS2.md's SA-01: fold the non-split shape into the same fix (the review's recommendation, since one code change closes both) or defer it separately — do not leave it silently unaddressed."
  - truth: "SC-3 / DECN-02 — a deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence"
    status: failed
    severity: minor
    reason: "Unchanged from the prior round. changed_line_ranges built from the orchestrator's actual diff commands (no -U0) reports ~3 lines of ordinary context as \"changed\" on each side of a hunk, widening the effective nearby/in_diff window from the documented 5 lines to roughly 8, and leaves 30-collect-score.md's deletion-hunk rule unreachable against real diffs. Fails toward asking, never toward silently dropping a decision; root cause predates Phase 57 and is not independently exercisable by this phase's own pytest suite. Already parked to deferred-items.md by 57-16 with the verification's reproduction and backlog acceptance criteria; re-confirmed present (not re-litigated in depth) in this round."
    artifacts:
      - path: "plugins/vibe-check/phases/review/30-collect-score.md"
        issue: "Deletion-hunk rule only fires under -U0 diffs; the orchestrator never requests one."
      - path: "plugins/vibe-check/phases/review/00-scope.md"
        issue: "Diff commands (git diff HEAD / --staged / gh pr diff --patch / git diff <range>) all use git's default 3-line context."
    missing:
      - "Same three items as the prior VERIFICATION.md's gap 2 (unchanged); tracked in deferred-items.md, not repeated here."
  - truth: "The second-round score.py guards (the needs-recheck arm of _CARRIED_STATUSES; the hash-equality check on the lead-obligation prior seed) are protected against silent regression by a mutation-tested fixture"
    status: failed
    severity: minor
    reason: "Independently reproduced (57-REVIEW-GAPS2.md WR-01). I mutated plugins/vibe-check/scripts/score.py twice, in place, and reverted both (git diff --stat on score.py is empty afterward): (1) `_CARRIED_STATUSES = (\"persisted\", \"needs-recheck\")` -> `(\"persisted\",)`: `pytest -q test_decision_continuity.py test_carry_state.py test_score.py test_verified_fixes.py` -> 854 passed, 0 failed (no new failure). (2) the lead-obligation seed's `lead_obl.get(\"stable_hash\") == survivor[\"stable_hash\"] and isinstance(...)` condition collapsed to just the isinstance check: same four modules -> 854 passed, 0 failed. Both guards are real in intent (the review explains the hash-preserving needs-recheck path and the lead-swap scenario each protects) but neither is currently reachable by any committed fixture, so a future edit could silently remove either with the suite staying green. This is a test-coverage gap, not a currently observed behavioral defect (no misbehavior results from either guard today); it does not block the phase goal on its own, but it directly violates this project's own standing rule to mutation-test every new guard (the same lesson the Phase-40 decorative-guard incident established), and it sits in the same code region as the SC-4 blocking gap above, so a single follow-up fix should close WR-01 alongside the CR-01 fix."
    artifacts:
      - path: "plugins/vibe-check/scripts/score.py"
        issue: "_CARRIED_STATUSES (line 362) and the lead-obligation seed's hash-equality check (line 2602) have no fixture that fails when either is removed."
    missing:
      - "A fixture driving a `needs-recheck`-status split row through a low-entropy line change (per the review's suggested recipe) with a mutant on _CARRIED_STATUSES."
      - "A fixture with a lead whose own line changed (new hash) carrying a stale obligation, asserting the new row does NOT inherit the old nearby_at/at_pass, with a mutant on the hash-equality check."
deferred: []
---

# Phase 57: Decision continuity within closure — Re-verification Report (second gap closure)

**Phase Goal:** An owner's defer/dismiss decision stays bound to its evidence — it survives regrouping and edits unrelated to the finding, and the finding reopens only when its relevant evidence changes.
**Verified:** 2026-10-27T01:02:00Z
**Status:** gaps_found
**Re-verification:** Yes — after the SECOND gap closure (plans 57-14..57-16), following up on 57-REVIEW-GAPS2.md

## Context

The prior VERIFICATION.md (score 3/4, HEAD 7b5feda) found one new blocking gap — a covered/absorbed finding splitting into its own row got no `nearby_at` stamp on the pass whose real edit caused the split — plus one pre-existing minor gap (diff-context window widening). Plans 57-14..57-16 closed the blocking gap for the shapes their fixtures drive (a plain nearby edit causing the split, no competing fresh re-report), re-ran every gate, and re-marked DECN-02/DECN-03 complete in REQUIREMENTS.md. A code review run after that gate closed (57-REVIEW-GAPS2.md, scope `d419dc2..HEAD`, last commit `1a45e10`) found a new Critical (CR-01: a same-lane fresh re-report that out-scores the carried record erases the stamp regardless of whether the row splits) and a Warning (WR-01: two of the new guards survive mutation). This re-verification independently reproduces both — not by reading the review, but by driving the real scorer myself — and independently confirms the original closure is real for the shapes it actually covers.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP success criterion) | Status | Evidence |
|---|---|---|---|
| 1 | SC-1 — Before any identity-rule change, a lost defer/dismiss decision on regrouping and on unrelated edits has a recorded reproduction verdict on current code | VERIFIED | Unaffected by this round. 57-01/57-08/57-14 all landed RED fixtures before any production change (57-14-SUMMARY.md's verbatim red run, confirmed consistent with the green state observed here). |
| 2 | SC-2 — A deferred or dismissed finding keeps its decision and recorded reason when findings are regrouped | VERIFIED | The regrouping-survival mechanics (CR-01/CR-02/WR-03 from the first round) remain closed — confirmed by direct run: `pytest -q test_carry_state.py -k TestGapClosure57` -> 22 passed, 0 failed (includes the new g2c/g2d). The new SC-4 gap below is a reopen-on-evidence-change failure (the decision IS still recognized and matched by hash), not a regrouping-survival failure, so it is scored against SC-4. |
| 3 | SC-3 — A deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence | VERIFIED, with a minor confirmed gap (unchanged from the prior round) | The comparator itself (file/canonical line/snapshot/band/lanes) correctly ignores far, unrelated edits. The diff-context window-widening gap (plain `git diff`, not `-U0`) is unchanged, still present, and remains parked to the backlog — see gaps. |
| 4 | SC-4 — When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence | **FAILED** | The ORIGINAL blocker (plain split-pass nearby stamp) is closed and independently confirmed. A **different, new** mechanism silently defeats the same reopen contract: when the finding's own lane re-reports it fresh on the pass of a nearby/joining edit and out-scores the carried record, the decision wrongly stays "current" and the gate writes. Reproduced independently on the real chain for both the split and non-split shapes — see below. |

**Score:** 3/4 truths verified (same count as the prior round — the specific defect behind the SC-4 failure changed from "plain split, no competing report" (now closed) to "same-lane fresh re-report out-scoring the carried record" (new, still open)).

## Independent Verification (real code, run directly in this session, not read from any SUMMARY or REVIEW)

### 1. The previous blocker is closed for the shapes 57-14's fixtures cover

```
$ cd plugins/vibe-check/scripts && pytest -q test_decision_continuity.py -k "TestSplitPassNearby or test_split_row_snapshot"
..... [100%]
5 passed, 43 deselected in 0.05s

$ pytest -q   (full suite)
3259 passed, 4312 subtests passed in 193.55s (0:03:13)
```
0 failed. Matches 57-16's recorded count exactly; confirms no regression.

A hand-written repro of the plain (no competing re-report) split, run directly against HEAD:
```
pass1 lead hash ... member A hash ...
pass2: security B's line 12 rewritten, resolved via recheck; A splits out with NO fresh re-report
record_of(s2, hA)["snapshot"]["nearby_at"] == 2
decision_state(rec, s2) == "stale"
e2e_gate(s2, {}) != "write"
```
This confirms the carried arm + lead-obligation seed in score.py (3b78957) do what 57-15/57-16 claim, for exactly the shapes their fixtures exercise.

### 2. 57-REVIEW-GAPS2.md CR-01 — independently reproduced for BOTH shapes, not read from the review

**Split shape** (B leads, absorbs A, B's line is rewritten and resolved; A's own `bugs` lane ALSO re-reports A fresh on the split pass):

```python
# myrepro_split2.py / myrepro_split3.py (built from this project's own test harness:
# F, TITLE_A, STABLE_CONF, base_file, fresh, run_pass, decide_on, record_of, row_of, empty_state)
conf=75  severity=warning  -> row.status=persisted nearby_at=2   decision_state=stale   (carried copy still leads — correct)
conf=80  severity=warning  -> row.status=persisted nearby_at=2   decision_state=stale   (correct)
conf=90  severity=warning  -> row.status=persisted nearby_at=2   decision_state=stale   (ties the +15 persisted bonus — carried wins)
conf=90  severity=critical -> row.status=new       nearby_at=None decision_state=current (DEFECT)
conf=85  severity=critical -> row.status=new       nearby_at=None decision_state=current (DEFECT — confidence alone did not need to rise, severity did)
conf=100 severity=critical -> row.status=new       nearby_at=None decision_state=current (DEFECT)
```

Gate check on the conf=100/critical case: `e2e_gate(s2, {}) == "write"` and `hA not in finalize_counts(s2, {})["outstanding_cw_hashes"]` — the owner is never told, and the run proceeds as if settled.

**Non-split shape** (A is its own decided row from pass 1 — no B at all; pass 2 edits beside it and A's own lane re-reports fresh at higher score):

```python
# repro4.py (the pre-existing scratchpad script named in the task) and an
# independent variant I wrote myself (myrepro_nonsplit_gate.py), both run directly:
re-report conf=75,  warning  -> status=persisted snap={..., 'nearby_at': 2} state=stale    (correct)
re-report conf=100, critical -> status=new        snap={... no nearby_at}   state=current  (DEFECT)
gate check: decision_state=current, outstanding_has_hA=False, gate=write
```

Both shapes fail identically and for the identical root cause (confirmed by reading score.py, not guessed): a fresh same-lane re-report that out-scores the carried record becomes `best_member`/`survivor` with status `"new"` (no prior snapshot) — so 57-15's `carried=` arm (keyed on `survivor.get("status")`) never fires, and the lead-obligation seed (keyed on `id(best_member) in carried_obligations`) never fires either, because the fresh finding's `id()` was never recorded in `carried_obligations`. The carried record is then intercepted in the member-dedup loop at the `ident in kept_by_ident` branch (score.py:2619-2636): because the fresh lead shares the SAME lane-aware occurrence identity as the carried record, `ref_kept is members[0]` is True, and the guard `ref_kept is not members[0]` — added specifically to never attach an obligation onto "the lead's own ref" — blocks the transfer before the hash-equality check downstream is even reached.

**Is this pre-Phase-57, and did 57-04 intend to cover it?**

```
$ git log -S"ref_kept is not members\[0\]" --oneline -- plugins/vibe-check/scripts/score.py
273a1e4 feat(57-04): keep a carried obligation when a fresh duplicate out-ranks it
```

This is NOT pre-Phase-57: the exact exclusionary guard was introduced by 57-04, inside this phase, well before the second-round work (57-14..57-16). 57-04's own SUMMARY documents the exclusion as deliberate ("it is never attached to the lead's own ref, and never when the obligation's hash is the row's own hash"), and the only two fixtures anywhere in the suite that exercise this family of behavior — 57-04's `TestObligationPreservingDedup`/R5 and 57-07's `TestSameHashLeadKeepsNearbyStamp` (added at `387e2bb`, not `273a1e4`) — both use a DIFFERENT lane than the carried record's own lane. No fixture in the suite ever drives the SAME-lane case. 57-04 did not intend to, and did not, cover this case; it is a genuine, previously-untested gap in 57-04's own fix, not a regression introduced by 57-14/57-15/57-16 and not something outside Phase 57's responsibility.

**Does it break SC-4?** Yes, unambiguously: in both shapes, relevant evidence genuinely changed (a nearby edit and/or a fresh, higher-scoring re-report of the exact finding), `decision_state` should be "stale" and is "current," `outstanding_cw_hashes` drops the hash, and the finalize gate writes. This is the project's own most-feared failure direction (silent wrong-keep) and is classified **blocking**.

### 3. WR-01 — both guards independently confirmed to survive mutation

Mutated `plugins/vibe-check/scripts/score.py` in place (not committed; reverted immediately after, confirmed byte-identical via `md5` before/after):

```
Mutation 1: _CARRIED_STATUSES = ("persisted", "needs-recheck")  ->  ("persisted",)
$ pytest -q test_decision_continuity.py test_carry_state.py test_score.py test_verified_fixes.py
854 passed, 811 subtests passed   (0 failed — survives)

Mutation 2 (reverted mutation 1 first): the lead-obligation seed's
  if (lead_obl.get("stable_hash") == survivor["stable_hash"] and isinstance(lead_obl.get("snapshot"), dict)):
  collapsed to:
  if isinstance(lead_obl.get("snapshot"), dict):
$ pytest -q test_decision_continuity.py test_carry_state.py test_score.py test_verified_fixes.py
854 passed, 811 subtests passed   (0 failed — survives)
```

Both mutations confirmed to leave the full relevant-module suite green, matching the review exactly. `git diff --stat -- score.py` was empty after reverting both. This is a test-coverage gap on two guards, not a currently observed misbehavior (no fixture exercises either path today, so nothing is currently broken by their absence of coverage) — classified **minor**, but flagged because this project has a standing rule (from the Phase-40 decorative-guard incident) that every new guard must be mutation-tested, and because both guards sit in the exact code region the SC-4 fix will need to touch.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `plugins/vibe-check/scripts/score.py` | `_snapshot_for` carried arm, lead-obligation prior seed, member dedup | PARTIALLY VERIFIED | The carried arm and lead-obligation seed are present, substantive and correctly wired for the shapes 57-14 tests (confirmed). The member-dedup branch (`ref_kept is not members[0]`) has a confirmed, independently-reproduced gap for the same-lane re-report case (see gaps). |
| `plugins/vibe-check/scripts/test_decision_continuity.py` | `TestSplitPassNearby`, `absorbed_split_scenario`, 2 e2e mutants | VERIFIED | Present, substantive, wired; all pass (`pytest -q` on the file: 0 failed). No fixture exercises the same-lane-rereport shape found by the review — confirmed absent by reading the file and by the fact this round's reproduction is not duplicated anywhere in it. |
| `plugins/vibe-check/scripts/test_carry_state.py` | `TestGapClosure57` g2c/g2d, split-pass shape | VERIFIED | 22 passed, 0 failed, includes g2c/g2d. |
| `.planning/REQUIREMENTS.md` | DECN-02/DECN-03 status | DECN-02 reasonable as marked (minor gap tracked separately); **DECN-03 marking not supported** — `[x]` "Complete (gap closure 57-08..57-16)" contradicts the reproduced SC-4 failure above. |
| `.planning/phases/.../deferred-items.md` | Parked items from the second gap closure | VERIFIED for what it covers (diff-context gap, IN-01..IN-05, SA-01-from-first-review) but written BEFORE 57-REVIEW-GAPS2.md existed (git log: `1fe602d` precedes `1a45e10`), so it does not yet carry CR-01(second)/WR-01/SA-01(second review). Not a defect in the file — it simply predates the finding this report confirms. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `score.py` threshold loop | `_snapshot_for(..., carried=survivor.get("status") in _CARRIED_STATUSES)` | stamps when the survivor's own status shows it existed before this pass | WIRED for a carried `best_member`; **NOT WIRED** when a fresh same-lane re-report becomes `best_member` instead (status defaults to "new") — this is the gap. |
| `score.py` group loop | lead-obligation prior seed (`carried_obligations[id(best_member)]`) | hash-equality seed before `_snapshot_for` | WIRED only when `best_member` IS the carried record itself; **NOT WIRED** when a fresh re-report displaces it as `best_member`. |
| `score.py` member dedup (`kept_by_ident`) | obligation transfer onto a non-lead kept ref | `ref_kept is not members[0]` guard | WIRED correctly for a DIFFERENT-lane fresh duplicate; **NOT WIRED**, by design, for a SAME-lane fresh duplicate — the guard cannot distinguish "a different finding that happens to coincide" from "the same finding's own lane re-reporting itself," and 57-04 chose to always exclude the lead's own ref, which blocks the legitimate case too. |
| `carry_state.decision_state` | `_nearby_since` / `_inherited_cause` | reads `record["snapshot"]["nearby_at"]` | WIRED and correct given a correctly-stamped snapshot; the gap is entirely upstream in score.py's stamping, confirmed again this round. |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite green on HEAD | `pytest -q` (plugins/vibe-check/scripts) | 3259 passed, 0 failed | PASS |
| 57-14/57-15 fixtures pass (original blocker closed) | `pytest -q test_decision_continuity.py -k "TestSplitPassNearby or test_split_row_snapshot"` | 5 passed | PASS |
| CR-01 (second round) reproduces, split shape | ad-hoc script on real chain, same-lane re-report conf=90/critical and conf=100/critical | `decision_state == "current"`, gate writes, hash dropped from outstanding | FAIL (confirms the new gap) |
| CR-01 (second round) reproduces, non-split shape (SA-01) | ad-hoc script + the pre-existing scratchpad repro | `decision_state == "current"`, gate writes | FAIL (confirms the new gap) |
| Control: lower-score same-lane re-report does NOT trip it | same script, conf=75/80/90-warning | `nearby_at` stamped, `decision_state == "stale"` | PASS (as expected — isolates the exact threshold) |
| WR-01 mutation 1 (`_CARRIED_STATUSES` drop needs-recheck) survives | in-place mutation + revert, `pytest -q` on 4 modules | 854 passed, 0 failed | FAIL (confirms the coverage gap — no test trips) |
| WR-01 mutation 2 (hash-equality check on lead-obligation seed) survives | in-place mutation + revert, `pytest -q` on 4 modules | 854 passed, 0 failed | FAIL (confirms the coverage gap — no test trips) |
| score.py restored byte-identical after both mutations | `md5` before/after | identical hash | PASS |

## Probe Execution

Not applicable — this phase has no `scripts/*/tests/probe-*.sh` convention; verification used the project's `pytest` suite plus direct function/chain-level reproduction (recorded above).

## Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| DECN-01 | 57-01, 57-08, 57-14 | Reproduce lost/wrongly-kept decisions before any rule change | SATISFIED | RED fixtures landed before each production change in every round, confirmed by the recorded red runs and the current green state. |
| DECN-02 | 57-02, 57-03, 57-05, 57-09, 57-10 | Decisions survive regrouping and edits unrelated to the finding's evidence | SATISFIED, with one confirmed minor gap (diff-context, unchanged, tracked in deferred-items.md) | Regrouping-survival mechanics (CR-01/CR-02/WR-03 first round) remain closed, confirmed by direct test run (22 passed in TestGapClosure57). The new SC-4 failure is scored against DECN-03, not DECN-02 — the decision is still correctly matched to its finding by hash; it simply fails to reopen when it should. |
| DECN-03 | 57-02, 57-03, 57-04, 57-06, 57-09, 57-10, 57-11, 57-15 | A decided finding reopens when its relevant evidence changes | **BLOCKED** | The original split-pass blocker (plain split, no competing report) is closed and confirmed. A new, independently reproduced defect (same-lane fresh re-report out-scoring the carried record, both split and non-split shapes) remains open and silently defeats the reopen contract. |

REQUIREMENTS.md currently marks DECN-03 `[x]` "Complete (gap closure 57-08..57-16)". That marking is **not supported** by the current state of the code — it should be reopened pending a fix for the same-lane re-report stamp loss (57-REVIEW-GAPS2.md CR-01/SA-01). DECN-02 can reasonably stay marked complete with its known minor gap tracked separately, consistent with how both the first and second rounds treated comparably-shaped fail-safe, not-independently-testable gaps.

## Anti-Patterns Found

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in any production or test file touched by 57-14..57-16 (checked directly). No blocker from the debt-marker gate. The score.py mutations I ran to confirm WR-01 were made, tested, and fully reverted in-place — no residual diff.

## Human Verification Required

None. Both outstanding items are deterministic and were reproduced here at the function/chain level, without needing a live orchestrator run, a UI, or external services.

## Gaps Summary

The second gap-closure plans (57-14..57-16) did exactly what they set out to do for the shapes their own fixtures drive: the originally-reported split-pass `nearby_at` loss (57-REVIEW-GAPS.md Critical-1) is closed and independently confirmed here by driving the real scorer, not by reading a SUMMARY. The minor diff-context gap from the prior round is unchanged and remains correctly parked.

However, a code review run after that gate closed (57-REVIEW-GAPS2.md, the last commit on the branch) found a new Critical that I independently reproduced on the real chain, for both shapes the task asked about:

1. **New blocking gap (CR-01 / SA-01, second review):** when the finding's own reviewer lane re-reports it fresh on the pass of a nearby or joining edit, and that fresh report out-scores the carried record (confirmed at confidence 90-100 with severity critical, and at confidence 100 at the carried record's own severity), the member-dedup guard that 57-04 added to protect a DIFFERENT case ("never attach an obligation to the lead's own ref") also blocks this legitimate same-lane case. The decision silently stays "current," the gate writes, and the owner is never told — reproduced identically whether the finding's row splits or not. This is not a regression from 57-14/57-15/57-16; it is a pre-existing gap in 57-04's own dedup fix (introduced at `273a1e4`, within Phase 57) that no fixture in the suite has ever exercised.
2. **Minor, confirmed coverage gap (WR-01):** two of the guards 57-15 added (the `needs-recheck` arm of `_CARRIED_STATUSES`; the hash-equality check on the lead-obligation seed) survive direct mutation with zero test failures. Neither is currently causing a wrong answer, but neither is protected against a future regression, and this project has a standing rule to mutation-test every new guard.
3. **Unchanged minor gap (diff-context):** correctly carried forward and parked; not re-litigated in depth this round.

**Recommendation:** route the new blocking gap (CR-01/SA-01 same-lane re-report stamp loss) to a follow-up phase via `/bm:plan-phase --gaps` before shipping Phase 57, since this is the third round this exact failure direction (silent wrong-keep on reopen) has surfaced and Phase 58's recovery/clear-actions work assumes decision binding is already correct. Fold WR-01's two coverage gaps into the same follow-up (the review's own suggestion — one code change and a shared set of fixtures can close CR-01, SA-01-second, and WR-01 together, since they all sit in the same ~40 lines of score.py's group loop and member dedup). Reopen DECN-03 in REQUIREMENTS.md pending that fix. The diff-context gap stays in the backlog as before.

---

*Verified: 2026-10-27T01:02:00Z*
*Verifier: Claude (bm-verifier)*
