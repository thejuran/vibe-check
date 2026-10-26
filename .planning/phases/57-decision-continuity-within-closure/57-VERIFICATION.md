---
phase: 57-decision-continuity-within-closure
verified: 2026-10-26T19:56:11Z
status: gaps_found
score: 2/4 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
gaps:
  - truth: "A deferred or dismissed finding keeps its decision and recorded reason when findings are regrouped (SC-2)"
    status: failed
    severity: blocking
    reason: "CR-01 (code review), independently reproduced on HEAD: when a member of a decided row carries its own separately-owed obligation (its own stable_hash, e.g. a different reviewer's finding absorbed into the row), `_covers_of` records it in the decision's `covers` list anyway. Once that member later splits out into its own top-level row with unchanged code, `covering_decision` matches it by (agent, file, title, code) and `decision_state` returns 'current' — closing a finding the owner never decided. `finalize_counts().outstanding_cw_hashes` goes from ['hB'] to [] with no owner action. The only existing test covering this member shape (`test_member_with_own_obligation_is_not_joined`) only exercises the single-pass nested case (the member still carries `absorbed_into`, so `covering_decision`'s absorbed-guard blocks inheritance there) — it never exercises the later pass where the member becomes its own row, which is exactly where the defect fires."
    artifacts:
      - path: "plugins/vibe-check/scripts/carry_state.py"
        issue: "_covers_of (lines 552-574) lists every members[] entry including ones whose own `obligation.stable_hash` differs from the decided record's hash, with no exclusion; covering_decision (663-693) then inherits for that member once it becomes a standalone row."
    missing:
      - "Exclude from `_covers_of` (and `covered_count`) any member whose `obligation.stable_hash` names a different hash from the record's own hash — that member is owed on its own and the row decision must never cover it."
      - "A RED fixture reproducing this exact repro (row decision + obligation member + split, unchanged code) in test_decision_continuity.py or test_carry_state.py, plus a mutant restoring the old (unfiltered) loop."
  - truth: "When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence (SC-4) — wrong-keep case"
    status: failed
    severity: blocking
    reason: "CR-02 (code review), independently reproduced on HEAD: when a decided finding has no decision of its own and inherits via `covering_decision` (the member-splits-into-its-own-row path), `decision_state`'s inherited branch (lines 727-731) checks ONLY `_nearby_since` — it never runs the band-rise-with-new-corroboration check (D-05 refinement) or the joined-newcomer check (D-08 refinement) that the OWN-decision branch runs. Reproduced: a row member (no obligation) becomes its own row on a later pass with band risen to critical, a brand-new corroborating lane in `attribution`, AND a newcomer member joined to the same row — `decision_state` still returns 'current' and `outstanding_cw_hashes` stays []. The identical band-rise scenario modeled as an OWN decision (not inherited) correctly returns 'stale' (contrast confirmed), proving the gap is specific to the inheritance path, not the severity rule itself."
    artifacts:
      - path: "plugins/vibe-check/scripts/carry_state.py"
        issue: "decision_state's inherited branch (around line 727-731) and _covers_of (which stores no band/attribution on a covers entry) make the severity-rise and joined-newcomer rules unreachable for any record that only inherits a decision."
    missing:
      - "Store `band` and the reporting lanes on each `covers` entry at record time (record_decisions / _covers_of)."
      - "Run the same ordered checks (nearby, then newcomer/joined, then band-rise) against that stored entry in the inherited branch of decision_state, extending stale_cause to return 'severity'/'joined' for the inherited path."
      - "A RED fixture for the inherited band-rise case and one for the inherited joined-newcomer case."
  - truth: "When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence (SC-4) — wrong-keep via row-wide attribution"
    status: failed
    severity: blocking
    reason: "Independently reproduced (not previously filed as a CR; corresponds to code-review WR-03, re-assessed here as blocking rather than warning because the trigger condition is a common shape, not an edge case, and the failure direction is a silent wrong-keep against the explicit, locked D-05 refinement). `gained_lanes` compares the record's current `attribution` against the decision's SAVED `attribution`, and both are the ROW-WIDE site attribution (every lane in the site cluster, regardless of which concern/title each lane reports — score.py line ~1898-1899, ~2462, ~2573). Reproduced: a row decided at pass 1 already includes lane `b` in `attribution` because `b` reported a DIFFERENT concern on the same row (its own obligation). At pass 2, `b` now ALSO corroborates the decided concern itself (same title) and the band rises to critical. Because `b` was already present in the saved attribution (for the unrelated concern), `gained_lanes` returns [] and `decision_state` stays 'current' — the band rose from genuine new corroboration on the decided concern, and the decision is wrongly kept. This directly violates the owner's locked D-05 refinement: 'a rise backed by NEW CORROBORATION (another reviewer now also reports the finding) reopens'."
    artifacts:
      - path: "plugins/vibe-check/scripts/carry_state.py"
        issue: "gained_lanes (512-523) and _band_rise_reopens (526-533) compare row-wide attribution sets, not per-title/per-concern corroboration."
      - path: "plugins/vibe-check/scripts/score.py"
        issue: "Row attribution (~line 1898-1899 _group, ~2462/2573 survivor/row writers) is the union of every lane in the site cluster, not scoped to the lane(s) reporting a given title/concern."
    missing:
      - "Save and compare the lanes that report THIS concern (same title match carry_state already uses for newcomer_lanes), not the row-wide attribution, both for the reopen test and for the card's `gained` field."
      - "A RED fixture: a row with two lanes reporting two different concerns at decision time, then one lane later corroborates the OTHER (decided) concern and the band rises — must reopen."
deferred: []
---

# Phase 57: Decision continuity within closure — Verification Report

**Phase Goal:** An owner's defer/dismiss decision stays bound to its evidence — it survives regrouping and edits unrelated to the finding, and the finding reopens only when its relevant evidence changes.
**Verified:** 2026-10-26T19:56:11Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP success criterion) | Status | Evidence |
|---|---|---|---|
| 1 | SC-1 — Before any identity-rule change, a lost defer/dismiss decision on regrouping and on unrelated edits has a recorded reproduction verdict on current code (failing fixture, or "did not reproduce; dropped") | VERIFIED | `test_decision_continuity.py` (57-01) contains 10 committed RED-at-the-time fixtures (R1a-R7) plus a `DID_NOT_REPRODUCE` table for N1-N6, all landed in a plan that touched no production file. Full suite is now green (3216 passed, 4278 subtests, 0 failed — independently run), i.e. the originally reproduced paths were fixed by later plans without weakening the fixtures. |
| 2 | SC-2 — A deferred or dismissed finding keeps its decision and recorded reason when findings are regrouped | **FAILED** | CR-01 independently reproduced: a row decision silently closes a member's own, separately-owed obligation once that member splits into its own row (see gap #1 below). |
| 3 | SC-3 — A deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence | VERIFIED (with a noted minor edge case) | `_ORDINARY_COMPARE` / `decision_state` compare only file, canonical line content, `nearby_at`, newcomer status and band — nothing fires on a far, unrelated edit; confirmed by the green `TestLineShift`/`TestDidNotReproducePins` fixtures and the full suite. WR-04 (first-line-of-snippet keying for multi-line member quotes) can cause an *extra, safe* re-ask on split, not a false negative of this truth — tracked as minor below, not a blocker of SC-3's own claim. |
| 4 | SC-4 — When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence | **FAILED** | CR-02 and an independently found row-wide-attribution defect (WR-03, re-scored blocking) both reproduced: an inherited (split-member) decision never runs the severity-rise or joined-newcomer reopen checks (CR-02), and even an OWN decision can wrongly stay current when the corroborating lane was already present on the row for an unrelated concern at decision time (row-wide attribution). Both are wrong-keeps — "should reopen, does not." See gaps #2 and #3 below. |

**Score:** 2/4 truths verified (the 2 failures are both reproduced, goal-breaking wrong-keeps)

### Independent Reproduction (CR-01, CR-02, and the row-attribution defect)

Per the escalation instructions, I reproduced CR-01 and CR-02 myself against HEAD (`0c3b58d`) by calling `carry_state.py`'s real functions directly (not the plan's own fixtures), and additionally probed the `gained_lanes` row-wide-attribution concern (code review WR-03) the same way.

```
$ python3 repro_cr01.py
pass1 outstanding_cw_hashes: ['hB', 'hR']
pass1 (post-decision) outstanding_cw_hashes: ['hB']
covers recorded on hR decision: [...{'agent': 'b', 'file': 'f.py', 'title': 'T2', 'code': 'y = 2'}]
pass2 outstanding_cw_hashes: []
decision_state(hB) on pass2 = current

CR-01 REPRODUCED: hB silently closed though the owner never decided it directly.
```

```
$ python3 repro_cr02.py
decision_state(hC) on pass2 = current
stale_cause(hC) on pass2 = None
pass2 outstanding_cw_hashes: []

CR-02 REPRODUCED: inherited decision stayed current despite band rise w/ new
corroboration AND a joined newcomer concern.

[contrast] decision_state for an OWN decision with the same band rise: stale
```

```
$ python3 repro_wr03.py
saved attribution on hR decision: ['a', 'b']
gained_lanes: []
decision_state: current
stale_cause: None
```
(`b` was present at decision time for a *different* concern; later `b` corroborates the *decided* concern and the band rises — `gained_lanes` wrongly returns `[]` because it only diffs row-wide attribution sets, not per-concern lanes.)

All three ran against the actual `carry_state.py` module on the current branch, no stubs. I also confirmed the full test suite (3216 tests / 4278 subtests) passes on HEAD with none of these three scenarios caught — consistent with the code review's statement that "the defects are in the new inheritance path, which the tests do not cover adversarially." I specifically checked `test_member_with_own_obligation_is_not_joined` (the test whose shape most resembles CR-01): it only exercises the single-pass case where the member is still nested (`absorbed_into` set, which `covering_decision`'s own guard blocks); it never exercises the later pass where that same member becomes a standalone row, which is exactly where the inheritance wrongly fires.

**Verdict: both CR-01 and CR-02 are CONFIRMED real defects on current code, not false positives from the review.** I additionally confirmed a third, related wrong-keep (row-wide attribution in `gained_lanes`) that the code review filed as WR-03/Warning; I am escalating it to blocking here because my reproduction shows the trigger (two lanes on one row reporting different concerns, one later corroborating the other's concern) is an ordinary multi-reviewer shape, not a narrow edge case, and the failure is a silent wrong-keep against the owner's explicitly locked D-05 refinement — the same class of harm as CR-02, just reached through the ordinary (non-inherited) decision path instead of the covers-inheritance path.

### Weighing WR-01, WR-02, WR-04 (code review warnings)

| ID | Confirmed? | Reasoning | Severity assigned |
|----|-----------|-----------|--------------------|
| WR-01 | Confirmed by reading `30-collect-score.md:55` (reuses cases 1-3's whole-file nearest-unique search for decided records with no distance bound) | Real gap, but orchestrator-prose-level (not independently executable in this repo without the live orchestrator) and requires a specific combinatorial trigger (deleted decided line + a duplicate identical line elsewhere in the same file, no nearby edit). | minor — backlog candidate |
| WR-02 | Plausible but not confirmed as an actual defect — the review itself calls it "almost certainly dropped," and the hunk-range representation for pure deletions is genuinely unspecified in the prose (interacts with the already-raised SA-01 "needs ruling" item) | Speculative pending the owner's SA-01 ruling on window symmetry; not independently reproducible without the orchestrator's diff-range construction. | minor — tie to SA-01 ruling |
| WR-04 | Confirmed by reading `_first_code_line` (carry_state.py:536-544): it takes the first non-blank line of a member's `current_code`, which may not be the flagged line for a multi-line lane quote | Fails toward asking (re-asks the owner, does not silently close) — annoying, not a safety or binding violation. | minor — backlog candidate |

None of WR-01/02/04 are added to the blocking gap list; they are real but either narrower-trigger, prose-only, or fail-safe. They should be captured for backlog/follow-up rather than blocking this phase's gate, independent of the CR-01/CR-02/WR-03 blockers above.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `plugins/vibe-check/scripts/test_decision_continuity.py` | Phase 57 harness, RED fixtures R1-R7, N1-N6 pins, DID_NOT_REPRODUCE table, 7-pass owner journey | VERIFIED (exists, substantive, wired) | Confirmed by direct read; all referenced classes (`TestLineShift`, `TestNearbyEdit`, `TestSeverityDirection`, `TestRegrouping`, `TestCardWording`, `TestDidNotReproduceRecord/Pins`, `TestCrossModuleGuards`, `TestPhase57EndToEnd`, `TestSameHashLeadKeepsNearbyStamp`, `TestPhase57Mutants`) present and running against the real `score.py`/`carry_state.py` chain. |
| `plugins/vibe-check/scripts/carry_state.py` | `_ORDINARY_COMPARE`, `_BAND_RANK`, `gained_lanes`, `decided`, `covers`, `covering_decision`, `newcomer_lanes`, `covered_count`, direction-aware `decision_state`/`stale_cause` | VERIFIED to exist/be substantive; **wrong-keep defects confirmed in the `covers`/`covering_decision`/`gained_lanes` logic** (see gaps). |
| `plugins/vibe-check/scripts/score.py` | `_nearby_changed`, nearby-aware snapshot writers, obligation-preserving member dedup | VERIFIED (exists, substantive, wired; full suite green including `TestNearbyAt`/`TestObligationPreservingDedup`). |
| `plugins/vibe-check/scripts/batch_card.py` | reopen-cause card suffixes reading `carry_state.gained_lanes`/`newcomer_lanes`/`covered_count` | VERIFIED wired (greps confirm `carry_state.gained_lanes(`, `carry_state.newcomer_lanes(`, `carry_state.covered_count(` all present); inherits the same CR-01/02/WR-03 upstream defects since it reads straight from `carry_state`. |
| `plugins/vibe-check/phases/review/30-collect-score.md`, `05-state.md`, `templates/scoring.md` | decided-record relocation prose, `$DECIDED_HASHES` binding | VERIFIED present (prose paragraph "Carried decided records" confirmed at line 55); WR-01 edge case noted above. |
| `plugins/vibe-check/phases/shared/90-finalize.md` | Open/Closed contract matching the helper | VERIFIED present; IN-01 (code review) notes a wording-only mismatch on the newcomer rule, not functional. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `carry_state.decision_state` | `carry_state.covering_decision` | inheritance lookup for records with no own decision | WIRED, **but the comparator it hands off to is incomplete** (nearby-only; CR-02) |
| `carry_state.record_decisions` | `_covers_of` | builds `covers` at decision-record write time | WIRED, **but does not exclude separately-owed obligation members** (CR-01) |
| `batch_card.py` | `carry_state.gained_lanes` / `newcomer_lanes` / `covered_count` | card renders the comparator's own values, never re-derives | WIRED correctly (no divergence between card and comparator); the defect is upstream in `carry_state`, not in the card. |
| `05-state.md` Phase 0.5 | `carry_state.py decided` | `$DECIDED_HASHES` binding, fail-closed on non-zero exit | VERIFIED present in prose (not independently executed against a live orchestrator run; this is an inherent limitation of static verification for prose-driven steps, consistent with IN-03 in the code review). |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full regression suite is green on HEAD | `pytest -q` (run once, from `plugins/vibe-check/scripts`) | `3216 passed, 4278 subtests passed in 172.33s` | PASS (confirms the suite doesn't already catch CR-01/CR-02/WR-03 — consistent with the code review, not contradicting it) |
| CR-01 reproduces on HEAD via direct `carry_state` calls | ad-hoc script calling `finalize_counts`/`record_decisions`/`decision_state` | `outstanding_cw_hashes` goes `['hB','hR'] -> ['hB'] -> []` across passes, with `hB` never decided | FAIL (confirms the gap) |
| CR-02 reproduces on HEAD via direct `carry_state` calls | ad-hoc script, inherited vs. own-decision contrast | inherited: `decision_state == 'current'`; own-decision contrast on identical band rise: `'stale'` | FAIL (confirms the gap) |
| Row-wide attribution wrong-keep (WR-03) reproduces on HEAD | ad-hoc script | `gained_lanes == []` despite genuine new corroboration on the decided concern | FAIL (confirms the gap) |

### Probe Execution

Not applicable — this phase has no `scripts/*/tests/probe-*.sh` convention; verification used the project's `pytest` suite plus direct function-level reproduction scripts instead (recorded above).

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| DECN-01 | 57-01 | Reproduce lost decisions before any rule change; drop non-reproducing paths | SATISFIED | 10 RED fixtures + `DID_NOT_REPRODUCE` table landed before any production file changed (57-01), confirmed by reading the plan/summary and the test module structure. |
| DECN-02 | 57-02, 57-03, 57-05 | Decisions survive regrouping and edits unrelated to the finding's evidence | **BLOCKED** | CR-01 independently reproduced: regrouping (a member splitting out of a decided row) silently closes a finding the owner never decided — the opposite failure of "losing" a decision, but still a binding-contract break ("stays bound to ITS evidence," not to a different finding's evidence). |
| DECN-03 | 57-02, 57-03, 57-04, 57-06 | A decided finding reopens when its relevant evidence changes | **BLOCKED** | CR-02 and the row-wide-attribution wrong-keep both independently reproduced: a decided finding fails to reopen when its relevant evidence (severity + new corroboration, or a joined newcomer) genuinely changes, specifically on the inherited-decision path and on multi-concern rows. |

REQUIREMENTS.md currently marks all three as `[x]` / "Complete" in its traceability table. **That marking is not supported by the current state of the code** — DECN-02 and DECN-03 should be reopened pending a fix for CR-01, CR-02, and the row-attribution defect.

### Anti-Patterns Found

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in any file this phase modified (`carry_state.py`, `score.py`, `batch_card.py`, the review-prose files, `scoring.md`, or the new/modified test modules). No blocker from the debt-marker gate.

### Human Verification Required

None. All findings here are deterministic, reproducible at the function-call level without needing a live orchestrator run, a UI, or external services.

### Gaps Summary

The phase's committed regression fixtures (R1-R7, N1-N6, the 7-pass owner journey) are real and all green, and they correctly lock the mechanics the plans originally targeted: pure line shifts, the 5-line nearby window, band-drop-keeps/band-rise-with-new-lane-reopens for an **own** decision, joined-newcomer reopening for a **newcomer**-shaped member, and D-09 inheritance for the one shape the plans tested (a plain newcomer member splitting out with unchanged code).

The code review's own adversarial pass (19 mutation tests on the phase's own guards, all killed) found two things the phase's fixtures never modeled, and I independently reproduced both directly against HEAD:

1. **CR-01 (blocking):** a row decision's `covers` list does not exclude members that carry their own, separately-owed `obligation` hash. Once such a member splits into its own row, it silently inherits the row's decision and drops out of `outstanding_cw_hashes` — a finding the owner never decided closes itself. This breaks the explicit CONTEXT/90-finalize.md promise that "a decision on the LEAD row closes nothing for [separately-owed member obligations]."
2. **CR-02 (blocking):** the inherited-decision branch of `decision_state` only checks the nearby-edit window — it skips the severity-rise-with-new-corroboration (D-05) and joined-newcomer (D-08) reopen rules entirely for any finding that holds its decision by inheritance rather than its own record. An identical band-rise scenario modeled as an own decision correctly reopens; the same scenario through inheritance does not.
3. **A third wrong-keep (blocking), independently found during this verification** (corresponds to the code review's WR-03, escalated from Warning to blocking here): `gained_lanes` diffs row-wide `attribution` sets rather than per-concern reporting lanes, so a lane already present on a row for an unrelated concern can later corroborate the DECIDED concern and the decision still wrongly stays current — a direct violation of the owner's locked D-05 refinement, in an ordinary (not exotic) multi-reviewer shape.

All three are silent wrong-keeps: the owner is never asked again even though the phase's own locked rules (D-05, D-08, D-09/covers scoping) say the finding should reopen or should never have been covered. This is the most dangerous failure direction for this phase's stated goal — a defer/dismiss decision is supposed to stay bound to ITS OWN evidence, not quietly absorb or outlive a different finding's evidence.

The code review's three remaining warnings (WR-01, WR-02, WR-04) are real but narrower or fail-safe (re-ask rather than silent close) and are recorded above as backlog candidates, not phase blockers.

**Recommendation:** route the three blocking gaps (CR-01, CR-02, row-attribution wrong-keep) to a follow-up phase via `/bm:plan-phase --gaps` before closing Phase 57 or advancing to Phase 58, since Phase 58's recovery/clear-actions work builds on the assumption that decision binding is already correct. WR-01/02/04 can go to backlog independently.

---

*Verified: 2026-10-26T19:56:11Z*
*Verifier: Claude (bm-verifier)*
