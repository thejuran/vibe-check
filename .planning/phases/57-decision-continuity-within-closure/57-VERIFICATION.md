---
phase: 57-decision-continuity-within-closure
verified: 2026-10-27T20:15:00Z
status: gaps_found
score: 4/5 must-haves verified (2 clean, 2 via owner override; 1 minor gap remains)
has_blocking_gaps: false
overrides_applied: 2
overrides:
  - must_have: "SC-4 / DECN-03 — a decided finding reopens when its relevant evidence changes"
    reason: "Round-4 code review (57-REVIEW-GAPS4.md) and this verification's own independent real-chain reproduction (score.run -> append_pass -> carry_state, no fixtures/stubs read from any SUMMARY) confirm three wrong-keep shapes remain, all in code paths the group loop's carried_by_hash pooling (57-21) does not reach: CR-01 (kept-open rows below threshold judge nearby only at the one surviving copy's line; zero-config — reproduced with two identical dismissed lines where one drops below threshold), CR-02 (absorbed member obligation sidecars judge nearby only at their own line; carry_state keeps the first same-hash record and discards the rest), and CR-04 (pre-existing, outside this round's diff: a covered member with no obligation of its own is never judged for nearby at all while it stays inside its decided row, so a guard removed beside it — D-14's motivating case — never reopens the decision). Owner ruling D-19 (one final structural round, hard stop) and D-22 (apply the hard stop: close Phase 57 with the round-4 review's reproduced wrong-keeps as a documented known limit rather than a fifth round) explicitly accept these three as known limits, carried in ROADMAP.md backlog 999.23 with the review's repros as the acceptance fixtures."
    accepted_by: "owner (per .planning/phases/57-decision-continuity-within-closure/57-CONTEXT.md D-19, D-22)"
    accepted_at: "2026-10-27"
  - must_have: "D-20 — a deferred finding never leaves the owner's open list without the owner closing it"
    reason: "Independently reproduced: a deferred covered member at a confidence below a valid min_confidence setting (member conf 40, min_confidence 45 — the config ceiling is 49) is removed by the min_confidence pre-scoring filter before the sub-threshold branch's keep-open synthesis (57-22) ever sees it, so it drops with no card, no kept-open row, and the gate writes. 57-22 correctly covers the sub-threshold branch (confirmed green); this is a distinct, narrower branch (the opt-in min_confidence filter) that 57-22 was scoped to leave alone. Owner ruling D-22 explicitly parks this min_confidence edge, plus the not-yet-reproduced SA-02 `--all` not-in-reviewed-set edge, to backlog 999.23 rather than fixing it inside Phase 57."
    accepted_by: "owner (per .planning/phases/57-decision-continuity-within-closure/57-CONTEXT.md D-22)"
    accepted_at: "2026-10-27"
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "The previous VERIFICATION.md's blocking gap (SC-4/DECN-03: a same-lane fresh re-report out-ranking the carried record erases the nearby stamp, both split and non-split shapes — 57-REVIEW-GAPS2.md CR-01/SA-01) is closed, and the round-3 findings that superseded it (57-REVIEW-GAPS3.md CR-01 cross-lane-same-hash-different-line, CR-01 same-lane-arrival-order, CR-02 carried-twin-dropped-by-min_confidence, IN-01 foreign-stamp-on-edited-lead, WR-01 lead-order-invariance coverage) are all closed by 57-21. Independently confirmed: `pytest -q test_decision_continuity.py -k \"TestPooledEvidence or TestPriorGate or TestLeadOrderInvariance\"` -> all pass on HEAD; score.py's `_carried_index` (carried_by_hash, built before the NV route / min_confidence / per-member drops, score.py:581) and `_any_nearby` / `_prior_rank` / `_pooled_prior` (score.py:606-633) are present, substantive and wired into the group loop (score.py:2715-2743) exactly as described; the member sort's line tie-break (score.py:2668) makes the lead deterministic. I re-ran the module's full suite myself (not from a SUMMARY): 3311 passed, 4381 subtests passed, 0 failed."
    - "D-20 (a deferred finding disappearing on a plain sub-threshold drop, 57-REVIEW-GAPS3.md WR-02) is closed by 57-22 for the threshold-drop branch: `carry_state.py deferred` exists (carry_state.py:1042), `deferred_covered` / `_covered_entry` gate on `deferred_hashes` (score.py:2116-2118, 2397-2423), and the dismiss counterpart still drops by design. Independently confirmed with the project's own `deferred_covered_sub_threshold_scenario` fixture: no-override pass keeps the row open (outstanding_cw 1); the kind gate and the carried stamp both reproduce exactly as 57-22-SUMMARY.md describes."
  gaps_remaining:
    - "SC-3 (minor, unchanged since the second gap-closure round, 57-16): `changed_line_ranges` built from a default-context (3-line) `git diff`, not `-U0`, widens the effective nearby/in_diff window from the documented 5 lines to roughly 8 and leaves 30-collect-score.md's deletion-hunk rule unreachable against real diffs. Not part of this round's scope, not tied to D-19/D-22, and not in backlog 999.23 (it has its own untracked parking note in deferred-items.md from 57-16). Re-confirmed present by reading the unchanged prose, not re-litigated in depth this round per the task's scope."
  regressions: []
gaps:
  - truth: "SC-3 / DECN-02 — a deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence"
    status: failed
    severity: minor
    reason: "Unchanged since 57-16 (second gap closure). `changed_line_ranges` is built from the orchestrator's actual diff commands (plain `git diff`, default 3-line context), which reports ordinary context lines around a hunk as \"changed,\" widening the effective nearby/in_diff window from 5 lines to roughly 8 and making the deletion-hunk rule in 30-collect-score.md unreachable against real diffs. Fails toward asking, never toward a silent keep; root cause predates Phase 57 and is not independently exercisable by this phase's own pytest suite (every fixture builds changed_line_ranges by hand, bypassing real git diff output). This gap is outside the owner's D-19/D-22 ruling and is not listed in ROADMAP.md backlog 999.23, so no override applies here."
    artifacts:
      - path: "plugins/vibe-check/phases/review/30-collect-score.md"
        issue: "The deletion-hunk rule (`+T,0` -> `[max(T, 1), T + 1]`) only fires under `-U0` diffs; the orchestrator never requests one."
      - path: "plugins/vibe-check/phases/review/00-scope.md"
        issue: "Diff commands (`git diff HEAD`, `git diff --staged`, `gh pr diff --patch`, `git diff <range>`) all use git's default 3-line context."
    missing:
      - "Either require `-U0`/`--unified=0` for every diff the scope phase builds changed_line_ranges from, or build ranges from the +/- line markers rather than hunk-header counts."
      - "Promote this item to a numbered ROADMAP.md backlog entry (as 999.23 was for the round-4 wrong-keeps), or fold it into 999.23's scope with an explicit owner ruling, so it is tracked the same way as the other accepted known limits."
deferred: []
---

# Phase 57: Decision continuity within closure — Re-verification Report (fourth and FINAL gap closure)

**Phase Goal:** An owner's defer/dismiss decision stays bound to its evidence — it survives regrouping and edits unrelated to the finding, and the finding reopens only when its relevant evidence changes.
**Verified:** 2026-10-27T20:15:00Z
**Status:** gaps_found (has_blocking_gaps: false — the one unresolved gap is minor and not tied to this round's work)
**Re-verification:** Yes — after the FOURTH (final, D-19 hard-stop) gap closure (plans 57-20..57-23), following up on 57-REVIEW-GAPS3.md and 57-REVIEW-GAPS4.md

## Context

The prior VERIFICATION.md (score 3/4, HEAD 1a45e10) found one blocking gap: a same-lane fresh re-report that out-ranked a carried record erased its nearby stamp, both when the row split and when it did not. Plans 57-17/57-18 closed that specific mechanism for the shapes their fixtures drove, but a round-3 code review (57-REVIEW-GAPS3.md) found the fix had moved the root cause rather than removed it — carried evidence was still read only from records that reached `scored_members`, nearby was still judged only at the lead's line, and two tied same-lane records picked their lead by arrival order. The owner ruled (D-19) ONE final structural round — pool every carried record's evidence from an index built before any filter, make the lead deterministic — with a HARD STOP: if the review after that round still finds a wrong-keep, close Phase 57 with it as a documented known limit rather than open a fifth round. Plans 57-20..57-23 implemented that pooling (57-21), added the D-20 deferred-stays-open mechanism (57-22), and ran the final gate (57-23), re-marking DECN-03 complete.

A round-4 code review (57-REVIEW-GAPS4.md, scope `cf32de8..HEAD`) ran after that gate and found the pooling mechanism itself is correct, but it only reaches the GROUP LOOP's row construction — two other paths that can carry a decided identity's evidence (`_kept_open_rows` for sub-threshold-dropped records, and the absorbed-member obligation sidecar) never consult the new index, and `carry_state`'s own per-hash read keeps only the FIRST record of a repeated hash. The review reproduced three wrong-keeps through this gap (CR-01 zero-config, CR-02, and a pre-existing CR-04), plus confirmed a D-20 min_confidence edge. Owner rulings D-21 (a brand-new occurrence of a decided identity is not itself new evidence, which reclassifies CR-03 as an accepted over-ask rather than a wrong-keep) and D-22 (apply the D-19 hard stop: close Phase 57 with CR-01/CR-02/CR-04 and the two deferral-loss edges as known limits in backlog 999.23) resolved the round. This re-verification independently reproduces every one of these claims on the real scorer — not by reading the review or any SUMMARY — and applies the owner's own pre-decided routing (do not re-litigate D-19/D-22) via explicit overrides.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP success criterion / plan must-have) | Status | Evidence |
|---|---|---|---|
| 1 | SC-1 — Before any identity-rule change, a lost defer/dismiss decision has a recorded reproduction verdict on current code | VERIFIED | Unaffected by this round. 57-01/57-08/57-14/57-17/57-20 all landed RED real-chain fixtures before their respective production fixes; 57-20-SUMMARY.md's verbatim red run and my own full-suite run (below) are consistent with every one of those fixtures now passing. |
| 2 | SC-2 — A deferred or dismissed finding keeps its decision and recorded reason when findings are regrouped | VERIFIED | The regrouping-survival mechanics (CR-01/CR-02/WR-03 from the first gap round) remain closed. My CR-02 reproduction below shows the decision itself is still correctly matched by hash after two copies are absorbed under two different fresh leads (`record_of(s2, hA)` finds the decision; it does not vanish or get misattributed) — the new round-4 defects are reopen-on-evidence failures (scored under SC-4/D-20 below), not decision-loss failures. |
| 3 | SC-3 — A deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence | **FAILED (minor, unresolved, no override)** | Unchanged since 57-16. The comparator itself (file/canonical line/snapshot/band/lanes) correctly ignores far, unrelated edits; the remaining failure is the diff-context window widening (plain `git diff`, not `-U0`), which asks slightly more often than the documented 5-line window intends. Fails toward asking, never toward a silent keep. Not covered by D-19/D-22 or backlog 999.23 — see Gaps. |
| 4 | SC-4 / DECN-03 — When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence | **PASSED (override)** | The mechanism fix (carried-by-hash pooling, deterministic lead) is implemented, substantive and correctly wired for every shape 57-20/57-21's own fixtures exercise (independently re-run, all green). THREE additional wrong-keep shapes remain in code paths the pooling never reaches (`_kept_open_rows`, member obligation sidecars, and a covered member with no obligation of its own) — independently reproduced below on the real chain, matching 57-REVIEW-GAPS4.md's CR-01/CR-02/CR-04 exactly. Owner ruling D-19 (hard stop) + D-22 (close under the hard stop) explicitly accepts these as known limits, tracked in ROADMAP.md backlog 999.23 — see Overrides. |
| 5 | D-20 (plan must-have, extends DECN-02) — A deferred finding never leaves the owner's open list on a score without the owner closing it | **PASSED (override)** | The sub-threshold branch's keep-open synthesis (`carry_state.py deferred`, `$DEFERRED_HASHES` -> `deferred_hashes`, `_covered_entry`) is implemented, substantive and wired — independently confirmed with the project's own fixture (no-override pass keeps the row open, outstanding_cw 1). A narrower, opt-in-only edge remains: the min_confidence filter (not the threshold drop) removes a deferred covered member before the keep-open logic ever runs, independently reproduced below. Owner ruling D-22 parks this (and the un-reproduced SA-02 `--all` edge) to backlog 999.23. |

**Score:** 4/5 must-haves verified (2 clean VERIFIED, 2 PASSED via owner override, 1 unresolved minor gap). `has_blocking_gaps: false` — the one remaining gap (SC-3) is minor and routes to backlog, not escalation.

## Independent Verification (real code, run directly in this session — not read from any SUMMARY or REVIEW)

### 1. Full suite, golden digest, replay-support gates — run myself from `plugins/vibe-check/scripts`

```
$ pytest -q
3311 passed, 4381 subtests passed in 163.97s (0:02:43)

$ pytest -q test_replay.py
64 passed, 10 subtests passed in 10.07s

$ python3 -c 'import score,test_score;assert score.stable_hash("a.py","  x=1","title")==test_score.GOLDEN_DIGEST;print("golden ok")'
golden ok

$ pytest -q test_score.py -k ImportSet
3 passed, 497 deselected in 0.07s
$ pytest -q test_carry_state.py -k ImportSet
3 passed, 223 deselected in 0.05s
```
0 failed, 0 SUBFAILED. Matches 57-23-SUMMARY.md's recorded counts exactly (3311 passed, 4381 subtests), confirming no regression and no drift between the committed SUMMARY and the actual tree. `git diff --quiet 92b135d HEAD -- plugins/` exits 0 — no plugin code changed since 57-22's last code commit, so the round-4 review and this verification examine the same code 57-23's gate certified.

### 2. Code-level confirmation that the review's named gaps are real (read, not assumed)

- `_kept_open_rows` (score.py:412-491) is called at score.py:2834 with `(dropped, kept, pass_number, carried_obligations, members_of, changed_line_ranges)` — **`carried_by_hash` is never passed in**. Inside it, line 472 computes `row_nearby = _nearby_changed(row, changed_line_ranges)` (the single-copy check), not `_any_nearby` against the pooled index. This confirms CR-01's exact code-level claim.
- The absorbed-member obligation transfer (score.py:2764-2766, inside the `kept_by_ident` dedup branch) calls `_refreshed_obligation(carried_obligations[id(m)]["obligation"], m, pass_number, changed_line_ranges)` — again the single member's own line, no pooling. Confirms CR-02's code-level claim.
- `carry_state._check_state` (carry_state.py:308-348) builds `records` by iterating `rows + sidecars` and keeping only the FIRST occurrence of each `stable_hash` (`if rec["stable_hash"] in seen: continue`). This is the exact "first wins" dedup CR-02/CR-03 depend on.
- `config.py:_validate_min_confidence` confirms the valid range is `[0, 49]` (≥50 is rejected with a distinct reason) — confirming the review's and this verification's own correction (IN-03) that a repro needs `min_confidence <= 49`.

### 3. CR-01 (zero-config wrong-keep) — independently reproduced on the real chain

Two identical `return None` lines (10 and 30) reported once, dismissed as one identity at conf 60 (both below the review threshold, so both are sub-threshold-kept-open from pass 1):

```python
L0[9] = L0[29] = "return None"
s1, r1 = run_pass(empty_state(), L0, [fresh("bugs", 10, L0, TITLE_A, conf=60),
                                     fresh("bugs", 30, L0, TITLE_A, conf=60)], 1, {F: [[1, 200]]})
hA = r1["findings"][0]["stable_hash"]; s1 = decide_on(s1, hA)
s2, r2 = run_pass(s1, L0, [], 2, {F: [[12, 12]]})   # edit near line 10
s3, r3 = run_pass(s1, L0, [], 2, {F: [[33, 33]]})   # edit near line 30 (from the same s1)
```
```
edit@12 (near the visible copy): row (line 10, kept_open sub-threshold, nearby_at 2), decision_state=stale
edit@33 (near the OTHER copy, same identity): row (line 10, kept_open sub-threshold, nearby_at None), decision_state=current
  outstanding_cw=0, outstanding_cw_hashes=[]   <- gate would write; the owner is never told
```
Only ONE kept-open row is ever emitted per hash (the first in drop order), and its own `_nearby_changed` check never sees the other copy's edit. This matches 57-REVIEW-GAPS4.md CR-01 exactly, with no config knob needed.

### 4. CR-02 (absorbed-sidecar wrong-keep) — independently reproduced

```python
s1, r1 = run_pass(empty_state(), L0, [fresh("bugs", 10, L0, TITLE_A, conf=75),
                                     fresh("bugs", 30, L0, TITLE_A, conf=75)], 1, {F: [[1, 200]]})
hA = r1["findings"][0]["stable_hash"]; s1 = decide_on(s1, hA)
f = [fresh("security", 10, L0, "Injection X", conf=95, severity="critical", category="injection"),
     fresh("security", 30, L0, "Injection Y", conf=95, severity="critical", category="injection")]
s2, r2 = run_pass(s1, L0, f, 2, {F: [[33, 33]]})
```
```
row(line 10, hash b183b048) members: [Injection X (no snapshot), Unchecked return at A (snapshot {at_pass 1, no nearby_at})]
row(line 30, hash 0f1e5ff9) members: [Injection Y (no snapshot), Unchecked return at A (snapshot {at_pass 2, nearby_at 2})]
record_of(s2, hA) -> line 10, decision_state = current   (WRONG-KEEP)
outstanding_cw = 2 (the two fresh injection hashes); hA is NOT among them
```
The owner is correctly asked about the two new injection findings, but the dismissed `hA` silently closes even though its line-30 twin owes a nearby stamp. Matches CR-02 exactly.

### 5. CR-03 / SA-01 (owner-reclassified: over-ask, not a wrong-keep, per D-21) — independently reproduced for completeness

```python
s1, hA = pass1 at line 10, conf=STABLE_CONF, dismissed
s2 = pass 2: fresh("bugs", 30, conf=100) + diff near line 33 (near the NEW copy only)
s3 = pass 3: quiet
```
```
pass2: record_of(s2, hA) -> line 10, decision_state = current, outstanding_cw = 0   (the pass on which the edit actually landed)
pass3: record_of(s3, hA) -> line 10, decision_state = stale                         (re-ask arrives one pass late)
```
This reproduces exactly as 57-REVIEW-GAPS4.md describes: on the pass where the edit happens (pass 2, beside a brand-new copy of the identity, not beside the decided copy), the decision silently reads current. The owner ruled (D-21) that a new occurrence of a decided identity is not itself relevant evidence, so the edit next to it was never "owed" in the first place — making this an accepted non-issue at pass 2, and the pass-3 re-ask (once the new copy itself becomes a carried record) an over-ask to be aligned later, not a wrong-keep. This governs how I scored it: no override needed because it is not treated as a failed truth under D-21.

### 6. CR-04 (pre-existing: covered member, no obligation, outside the lead's window) — independently reproduced

```python
a = fresh("bugs", 10, conf=75); b = fresh("security", 12, "Injection at B", conf=95, severity="critical")
s1, r1 = run_pass(..., [a, b], 1, {F: [[1, 200]]})   # one row, led by b (line 12), a covered inside it
hB = r1["findings"][0]["stable_hash"]; s1 = decide_on(s1, hB)
L1[5] = "line_06 = 'guard removed'"                   # inside A's window (5-15), outside B's (7-17)
s2, r2 = run_pass(s1, L1, [], 2, {F: [[6, 6]]})
```
```
pass2 row: (line 12, hash 3449f4b5, no nearby_at); record_of(s2, hB) -> decision_state = current
outstanding_cw = 0   <- gate would write
```
A covered member with no obligation of its own is never judged for nearby at all while it stays inside its row — only the lead's line and same-hash carried copies are checked. Matches CR-04 exactly; confirmed as pre-existing (the group loop's `row_nearby` computation has never considered covered-without-obligation members, independent of this round's pooling work).

### 7. D-20 min_confidence edge — independently reproduced with a config-valid value

```python
a = fresh("bugs", 10, conf=40); b = fresh("security", 12, "Injection at B", conf=95, severity="critical")
s1, hB = pass1 (dismiss replaced with defer); pass 2 resolves B, edits line 12, a splits out
for min_confidence in (None, 45):
    ...
```
```
min_confidence=None : row kept open (sub-threshold; deferred-by: hB), outstanding_cw=1   (D-20 intended behaviour)
min_confidence=45    : rows=[], filtered=[(10, 'below-min-confidence')], record=None, outstanding_cw=0   (SILENT LOSS of a deferred finding)
```
Confirms the review's and 57-23's own recorded repro, using a config-valid `min_confidence` (45 <= the 49 ceiling) against a covered member below it (conf 40) — the earlier recorded repro in deferred-items.md used an invalid 80, corrected per IN-03.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `plugins/vibe-check/scripts/score.py` | `_carried_index`/`carried_by_hash`, `_any_nearby`, `_prior_rank`, `_pooled_prior`, deterministic line tie-break, D-20 `_covered_entry`/`deferred_covered` | VERIFIED for the group-loop row path; **confirmed incomplete** for `_kept_open_rows` and the absorbed-member sidecar path (never consult `carried_by_hash`) — this is the CR-01/CR-02/CR-04 gap, accepted via override. |
| `plugins/vibe-check/scripts/carry_state.py` | `deferred(state)` read-only subcommand | VERIFIED — present (line 1042), read-only, exit-2 fail-closed on malformed state (confirmed by code read; no new write path: `record_decisions`/`record_fix_verdicts` call count unchanged). Its per-hash dedup (`_check_state`, first-record-wins) is the read-side half of CR-02/CR-03, confirmed by direct code read. |
| `plugins/vibe-check/scripts/test_decision_continuity.py` | `TestPooledEvidence`, `TestPriorGate`, `TestDeferredStaysOpen`, 9-scenario `TestLeadOrderInvariance` | VERIFIED — present, substantive, wired; `pytest -q -k "TestPooledEvidence or TestPriorGate or TestDeferredStaysOpen or TestLeadOrderInvariance"` all pass on HEAD (independently re-run). No fixture in the suite exercises the kept-open-row or sidecar shapes the round-4 review found (confirmed by reading the file — WR-02 of 57-REVIEW-GAPS4.md is accurate). |
| `.planning/REQUIREMENTS.md` | DECN-01/02/03 status | DECN-01/02 reasonable as marked. **DECN-03 wording gap:** marked `[x]` "Complete (gap closure 57-08..57-23)" with no "known limit" annotation, even though the owner's own D-19 operating rule (57-CONTEXT.md, deferred-items.md) explicitly instructs `Complete with known limit (999.x)` once a post-round review still finds a wrong-keep. The round-4 review did find wrong-keeps; the REQUIREMENTS.md row was never updated to say so. Not edited here per instruction — reported as a discrepancy. |
| `.planning/ROADMAP.md` backlog 999.23 | Known-limits entry covering the round-4 review's findings | VERIFIED — present, specific (names CR-01/CR-02/CR-04, the D-21 over-ask, and both deferral-loss edges with concrete repro parameters and a root-cause fix direction). Adequate as the override's tracking anchor. |
| `.planning/phases/.../deferred-items.md` | "Parked by the fourth gap closure" + "Phase close" sections | VERIFIED — present, quotes D-19/D-21/D-22 verbatim, matches ROADMAP 999.23. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `score.py` group loop | `carried_by_hash` index | pooled nearby/prior over every carried same-hash record | WIRED — confirmed for the row survivor path (score.py:2715-2743); independently re-run (p1-p4, in01 all pass). |
| `score.py` `_kept_open_rows` | `carried_by_hash` index | — | **NOT WIRED** — the function signature never receives the index (score.py:412, call site score.py:2834); nearby is judged only at the one emitted copy's own line. This is CR-01, accepted via override. |
| `score.py` member dedup (`kept_by_ident`) | `carried_by_hash` index | absorbed-member obligation refresh | **NOT WIRED** — `_refreshed_obligation` (score.py:2764-2766) reads only the member's own line. This is CR-02, accepted via override. |
| `score.py` group loop | covered members without their own obligation | row-level nearby check | **NOT WIRED** — `row_nearby` is computed only from the survivor and same-hash carried copies (score.py:2743), never from a covered member's own line. This is CR-04, accepted via override (pre-existing). |
| `carry_state.py deferred` | `05-state.md` `$DEFERRED_HASHES` -> `30-collect-score.md` envelope `deferred_hashes` | fail-closed prose binding | WIRED — confirmed by code read and by the project's own full-suite green run (prose-lock tests pass). |
| `score.py` sub-threshold branch | `deferred_covered` / `_covered_entry` | keep-open synthesis gated on `deferred_hashes` | WIRED for the threshold-drop branch; **NOT WIRED** for the min_confidence branch (independently reproduced above) — accepted via override. |
| `carry_state._check_state` | first-record-wins per-hash dedup | `records` built from `rows + sidecars`, keeping only the first `stable_hash` | Confirmed by code read (carry_state.py:339-348) — this is the read-side mechanism behind CR-02/CR-03's silent keep. |

## Data-Flow Trace (Level 4)

Not applicable in the usual UI-rendering sense — this phase's artifacts are a deterministic scoring/state pipeline, not a UI component. The equivalent trace (does the data the owner sees reflect real evidence, not a hardcoded/stale value) is exactly what sections 3-7 above exercise end to end: `score.run` -> `append_pass` -> `carry_state.decision_state`/`finalize_counts` -> the finalize gate, with every value read from the real pipeline output, never forged.

## Behavioral Spot-Checks

| Behavior | Command / Script | Result | Status |
|---|---|---|---|
| Full suite green on HEAD | `pytest -q` (plugins/vibe-check/scripts) | 3311 passed, 4381 subtests, 0 failed | PASS |
| test_replay.py collected | `pytest -q test_replay.py` | 64 passed, 10 subtests | PASS |
| Golden digest | inline python check | `golden ok` | PASS |
| Import sets | `pytest -q test_score.py -k ImportSet` / `test_carry_state.py -k ImportSet` | 3 passed / 3 passed | PASS |
| 57-20/57-21 fixtures (round-3 mechanism) pass | `pytest -q -k "TestPooledEvidence or TestPriorGate or TestLeadOrderInvariance"` | all pass | PASS |
| CR-01 (zero-config) reproduces | ad-hoc script, real chain | `decision_state=current`, `outstanding_cw=0` | FAIL (confirms the accepted known limit) |
| CR-02 reproduces | ad-hoc script, real chain | `decision_state=current`, hA absent from outstanding | FAIL (confirms the accepted known limit) |
| CR-03/SA-01 reproduces (reclassified, D-21) | ad-hoc script, real chain | pass-2 `current`/gate-write; pass-3 `stale` | Reproduces as described; not a failing truth under D-21 |
| CR-04 reproduces (pre-existing) | ad-hoc script, real chain | `decision_state=current`, `outstanding_cw=0` | FAIL (confirms the accepted known limit) |
| D-20 min_confidence edge reproduces | ad-hoc script, real chain, config-valid value | `record=None`, `outstanding_cw=0` | FAIL (confirms the accepted known limit) |
| D-20 control (no min_confidence) stays correct | same script | row kept open, `outstanding_cw=1` | PASS |
| `carried_by_hash` never passed into `_kept_open_rows` | code read, score.py:412/2834 | confirmed absent from signature and call | Confirms CR-01's code-level root cause |
| `carry_state._check_state` keeps only the first same-hash record | code read, carry_state.py:339-348 | confirmed | Confirms CR-02/CR-03's read-side root cause |

## Probe Execution

Not applicable — this phase has no `scripts/*/tests/probe-*.sh` convention; verification used the project's `pytest` suite plus direct function/chain-level reproduction (recorded above), consistent with every prior round of this phase.

## Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| DECN-01 | 57-01, 57-08, 57-14, 57-20 | Reproduce lost/wrongly-kept decisions before any rule change | SATISFIED | RED fixtures landed before each production change in every round, confirmed by the recorded red runs and the current green state. |
| DECN-02 | 57-02, 57-03, 57-05, 57-09, 57-10, 57-22 | Decisions survive regrouping and edits unrelated to the finding's evidence | SATISFIED, with one confirmed minor gap | Regrouping-survival mechanics remain closed (confirmed). D-20 (deferred stays open) is satisfied for the threshold branch, with the min_confidence edge accepted as a known limit via override. The diff-context minor gap (SC-3) remains unresolved and uncovered by any override — see Gaps. |
| DECN-03 | 57-02, 57-03, 57-04, 57-06, 57-09, 57-10, 57-11, 57-15, 57-18, 57-21 | A decided finding reopens when its relevant evidence changes | **SATISFIED WITH KNOWN LIMITS (via owner override, not a clean pass)** | The pooling mechanism closes every shape its own fixtures (and three full rounds of prior review) targeted. Three additional wrong-keep shapes (CR-01, CR-02, CR-04) remain in code paths outside that pooling, independently reproduced here, and are accepted as documented known limits under owner rulings D-19/D-22, tracked in ROADMAP.md backlog 999.23. |

**On DECN-03 specifically (asked explicitly):** DECN-03 is **met with known limits**, not fully/cleanly met. The core reopen mechanism works correctly for the row-construction path, which is the majority of real-world cases (a decided finding that still leads or is absorbed into one row). It does not yet work when a decided identity's second copy is dropped by the sub-threshold filter before any row exists for it (CR-01), when two copies are absorbed under two different unrelated leads (CR-02), or when a covered member with no obligation of its own sits beside an edited guard outside its row lead's window (CR-04, pre-existing). All three fail toward a silent keep (the worse of the two failure directions this project tracks), and the owner has explicitly chosen — after four structural rounds and the D-19 hard stop — to accept them as documented backlog items (999.23) rather than open a fifth round. REQUIREMENTS.md's current wording ("Complete (gap closure 57-08..57-23)") does not reflect this nuance; the owner's own D-19 operating rule calls for "Complete with known limit (999.x)" and that edit has not yet been made (reported, not corrected, per instruction).

## Anti-Patterns Found

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers in any file touched by 57-20..57-23 (`git diff 9fe0e0f HEAD -- plugins/` checked directly). No blocker from the debt-marker gate.

## Human Verification Required

None. Every item in this report — the closed mechanism, the three accepted wrong-keep shapes, the D-20 min_confidence edge, and the diff-context minor gap — is deterministic and was reproduced here at the function/chain level, without a live orchestrator run, a UI, or an external service.

## Gaps Summary

The fourth and final gap-closure round (57-20..57-23) did what it set out to do: the pooling mechanism the owner specified in D-19 (collect every carried record before any filter, pool evidence, make the lead deterministic) is implemented, substantive, and correctly wired into the score.py group loop, closing every shape targeted by three full rounds of prior review (57-REVIEW-GAPS.md through 57-REVIEW-GAPS3.md) and independently confirmed here by driving the real scorer myself. The D-20 deferred-stays-open mechanism is implemented and wired for its intended branch (the sub-threshold drop).

A fourth-round review (57-REVIEW-GAPS4.md) correctly found that the pooling mechanism is narrower than its own stated scope: it covers the group loop's row construction, but two other paths that can carry a decided identity's evidence — the sub-threshold "kept-open row" synthesis and the absorbed-member obligation sidecar — never consult the new index, and `carry_state`'s own read keeps only the first record of a repeated hash. I independently reproduced all three resulting wrong-keeps (CR-01 zero-config, CR-02, and the pre-existing CR-04) plus the D-20 min_confidence edge, on the real chain, matching the review's claims exactly. The owner applied the D-19 hard stop (ruling D-22): these are now documented known limits in ROADMAP.md backlog 999.23 rather than a fifth structural round, and CR-03 was separately reclassified (ruling D-21) from a wrong-keep into an accepted over-ask.

Because these four items are explicitly pre-decided by the owner and tracked in backlog 999.23, this report applies overrides for them rather than blocking the phase on them — consistent with the instruction not to re-litigate that routing. The ONE item left unresolved and uncovered by any override is the diff-context window-widening gap (SC-3/DECN-02), unchanged since the second gap-closure round (57-16), minor, fail-safe-direction (it over-asks, never silently drops), but not part of D-19/D-22's scope and not yet promoted to a numbered backlog entry the way 999.23 was for the round-4 findings.

**Recommendation:** Treat this phase as ready to close under the owner's own D-19/D-22 decisions (no further code work), with two small housekeeping items for the owner/orchestrator to pick up when convenient, neither of which requires new code:
1. Update REQUIREMENTS.md's DECN-03 traceability row to `Complete with known limit (999.23)`, per the owner's own D-19 operating rule (not done in this verification per instruction — reported only).
2. Either promote the diff-context gap (SC-3) to its own numbered backlog item (as 999.23 was created for the round-4 findings) or fold it explicitly into 999.23's scope, so every known Phase 57 limitation is tracked the same way. Until that happens, this report's `status` stays `gaps_found` (non-blocking, minor) rather than `passed`, strictly because this one item has no override on record.

---

*Verified: 2026-10-27T20:15:00Z*
*Verifier: Claude (bm-verifier)*
