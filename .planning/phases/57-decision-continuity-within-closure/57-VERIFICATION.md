---
phase: 57-decision-continuity-within-closure
verified: 2026-10-26T23:40:00Z
status: gaps_found
score: 3/4 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2/4
  gaps_closed:
    - "CR-01 (original) — a row decision's covers list no longer includes a member carrying its own separately-owed obligation; confirmed via TestGapClosure57::test_g1_* and an independent full-suite run"
    - "CR-02 (original) — an inherited (covered-member) decision now runs the same ordered nearby/joined/severity checks as an own decision; confirmed via TestGapClosure57::test_g2a_*/test_g2b_*"
    - "WR-03 (original, row-wide attribution wrong-keep) — gained_lanes now diffs per-concern lanes, not row-wide attribution; confirmed via TestGapClosure57::test_g3a_*/test_g3b_*"
  gaps_remaining: []
  regressions: []
gaps:
  - truth: "When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence (SC-4 / DECN-03) — a covered member that splits into its own row on the very pass whose edit caused the split"
    status: failed
    severity: blocking
    reason: "New defect, surfaced by the post-gap-closure code review (57-REVIEW-GAPS.md Critical-1) and independently reproduced here against the real score.run -> append_pass -> carry_state chain (no fixtures, no stubs). When a covered member (or a member holding its own absorbed decision) splits into its own top-level row, score.py builds the new row as `survivor = dict(best_member)`, which has no top-level `snapshot` key (the member's prior evidence, if any, lives nested under `obligation.snapshot`, which score.py never reads back onto the row). score.py's `_snapshot_for(survivor, pass_number, nearby=nearby)` only stamps `nearby_at` when `nearby and isinstance(prior, dict)`, and `prior = survivor.get('snapshot')` is None on this first split pass, so the stamp is silently skipped even though `_nearby_changed` correctly returned True. carry_state.py's `_nearby_since` / `_inherited_cause` then read `record['snapshot'].get('nearby_at')`, find nothing, and the decision stays 'current'. The edit that caused the split — which is also the common, ordinary cause of a split (the lead's own nearby line gets fixed) — is lost for good; only a SECOND, later edit near the member re-asks. This is a silent wrong-keep, the most dangerous failure direction for this phase's own goal, and it is not a narrow edge case: it is the ordinary shape a split takes."
    artifacts:
      - path: "plugins/vibe-check/scripts/score.py"
        issue: "_snapshot_for (score.py:306-351) stamps nearby_at only when the row already carries a prior snapshot dict; the threshold loop (score.py:2660-2661) calls it with nearby=True on a freshly split survivor that has no such prior, so the stamp never lands. _refreshed_obligation / the same_hash_prior transplant (score.py:2614-2628) only rescues the Phase-46 'identical hash lead swap' shape, never a split where the new row's own stable_hash differs from any carried obligation's."
      - path: "plugins/vibe-check/scripts/carry_state.py"
        issue: "_nearby_since (carry_state.py:804-810) and _inherited_cause (carry_state.py:821-843) trust record['snapshot']['nearby_at'] as the sole nearby signal; they have no fallback for a just-split row whose carried obligation snapshot was never carried onto the new row's top-level snapshot."
    missing:
      - "Stamp nearby_at on a survivor built from a carried member/obligation even without a prior top-level snapshot (e.g. seed the prior from the carried obligation's own snapshot before calling _snapshot_for, mirroring the existing same_hash_prior transplant, but keyed on the member's own obligation rather than on hash equality with the new lead)."
      - "A RED fixture that drives the REAL chain (score.run -> append_pass -> carry_state, not a hand-built TestGapClosure57 state) for both shapes the review names: an inherited (covered, no own decision) member splitting out on the pass whose real diff rewrote the lead's nearby line, and an own-decision member absorbed as an obligation sidecar then split out the same way. The existing e2e fixture (split_scenario) must stop sending an empty diff on the split pass (`ranges={F: []}`) for at least one committed test, since that omission is what currently hides this defect."
      - "An owner ruling on SA-01 (57-REVIEW-GAPS.md): once nearby_at is correctly stamped on a split caused by the lead's own nearby edit, D-09 inheritance becomes rare in practice (most splits will now re-ask). The owner needs to decide whether that is the intended, stricter behavior or whether the lead's own resolved line should be exempted from the member's nearby check on the split pass."
  - truth: "A deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence (SC-3 / DECN-02)"
    status: failed
    severity: minor
    reason: "Independently reproduced (corresponds to 57-REVIEW-GAPS.md Warning WR-01). 30-collect-score.md's changed-line-ranges bullet (written in 57-12) builds changed_line_ranges from each diff hunk's new-side header, including the new deletion-only-hunk rule ('+T,0' -> [max(T,1), T+1]) that D-14's motivating case depends on. That construction assumes a zero-context diff (-U0). None of the diff commands the orchestrator's scope phase actually runs do that: `git diff HEAD`, `git diff --staged`, `gh pr diff <ref> --patch` and `git diff <range>` (phases/review/00-scope.md:36-51) all use git's default 3-line context. I reproduced the shape directly: a single-line deletion in a 30-line file produces hunk header `@@ -6,7 +6,6 @@` under default `git diff` (new-side count 6, non-zero) versus `@@ -9 +8,0 @@` under `-U0` (new-side count 0). Two effects follow: (1) the new deletion-only-hunk rule is dead code against real orchestrator diffs — a pure deletion is reported as an ordinary 6-line hunk, never a `+T,0` header; (2) the 3 lines of unrelated context on each side of every ordinary hunk are reported as 'changed' lines, which widens the effective nearby/in_diff trigger distance from the documented 5 lines to roughly 8, so a decided finding 6-8 lines from a genuinely unrelated edit can be re-asked even though D-14 says only 5 lines above/below should. Failure direction is fail-safe (re-asks, never silently drops), the root cause (diff commands have no -U0, and nothing upstream ever specified how ranges should be built from hunks) predates Phase 57 — the same commands were already in use for the Phase 56 independent re-check trigger — and the defect is not independently exercisable by this phase's own pytest suite (every committed fixture builds changed_line_ranges by hand, never from a real git diff), the same class of limitation the original verification assigned to WR-01/WR-02. Phase 57's own changes make the practical exposure wider, not narrower: 57-11's D-14 symmetric window means context-line inflation now matters on BOTH sides of an edit, not only beneath it, and 57-12 added prose that explicitly (and incorrectly) claims the deletion case is handled."
    artifacts:
      - path: "plugins/vibe-check/phases/review/30-collect-score.md"
        issue: "The changed-line-ranges bullet (step 2, line ~64) specifies a hunk-header-based range construction that only behaves as documented under -U0 diffs; the orchestrator never requests -U0."
      - path: "plugins/vibe-check/phases/review/00-scope.md"
        issue: "Diff commands at lines 36-37, 44, 51 (git diff HEAD / --staged / gh pr diff --patch / git diff <range>) all use git's default context (3 lines), none pass --unified=0."
    missing:
      - "Either require -U0/--unified=0 for every diff the scope phase builds changed_line_ranges from, or derive ranges from '+' and '-' line markers directly rather than from hunk-header counts (so ordinary context lines never enter in_diff or the nearby window)."
      - "If -U0 is adopted, re-check whether any other prose or scoring step assumes the default 3-line context (e.g. silenced-marker windows), since changing the orchestrator's diff invocation is a wider change than this phase's scope."
      - "A way to prove the real construction end-to-end (today it can only be proven by hand, as done here) — e.g. a small integration fixture that runs git diff through the documented hunk-parsing rule and asserts the resulting ranges, not a hand-built changed_line_ranges dict."
deferred: []
---

# Phase 57: Decision continuity within closure — Re-verification Report

**Phase Goal:** An owner's defer/dismiss decision stays bound to its evidence — it survives regrouping and edits unrelated to the finding, and the finding reopens only when its relevant evidence changes.
**Verified:** 2026-10-26T23:40:00Z
**Status:** gaps_found
**Re-verification:** Yes — after gap closure (plans 57-08..57-13), following up on 57-REVIEW-GAPS.md

## Context

The prior VERIFICATION.md (score 2/4) found three blocking wrong-keeps (CR-01, CR-02, WR-03). Plans 57-08..57-13 closed all three, re-ran every gate, and re-marked DECN-02/DECN-03 complete in REQUIREMENTS.md. After that gate closed, a gap-closure code review (57-REVIEW-GAPS.md, timestamped AFTER 57-13's last commit, scope `57e93d7..HEAD`) found one new Critical and reclassified one Warning as effectively blocking in practice. No plan after 57-13 exists; the review itself is the last commit on the branch (`7b5feda`, docs-only). This re-verification independently confirms the three original closures and independently reproduces (not merely reads) the two review findings the task asked about.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP success criterion) | Status | Evidence |
|---|---|---|---|
| 1 | SC-1 — Before any identity-rule change, a lost defer/dismiss decision on regrouping and on unrelated edits has a recorded reproduction verdict on current code | VERIFIED | 57-01 (original) and 57-08 (gap closure) both landed RED fixtures before any production file changed; 57-08-SUMMARY.md records the verbatim red run, confirmed consistent with the full-suite behavior observed here. |
| 2 | SC-2 — A deferred or dismissed finding keeps its decision and recorded reason when findings are regrouped | VERIFIED | Original CR-01 (row decision silently covering a separately-owed member on split) is closed: `_covers_of` (carry_state.py:600) now skips a member whose `obligation.stable_hash` differs from the record's own hash. Confirmed by direct test run: `pytest -q test_carry_state.py -k TestGapClosure57` → 20 passed, 0 failed (includes `test_g1_split_obligation_member_is_not_covered_by_row_decision`). |
| 3 | SC-3 — A deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence | VERIFIED, with a minor confirmed gap (see gaps) | The decision-state comparator itself (file/canonical line/snapshot/band/lanes) correctly ignores far, unrelated edits — confirmed by the green suite. However, the orchestrator's real diff commands (no `-U0`) make the *reported* changed-line ranges wider than the documented 5-line window by about 3 lines of diff context on each side, which can cause an edit 6-8 lines away to be treated as "nearby." I independently reproduced the underlying git-diff behavior (see below). This is a fail-safe-direction, pre-existing, not-independently-pytest-testable gap — recorded as minor, not blocking. |
| 4 | SC-4 — When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence | **FAILED** | Original CR-02 (inherited decision skipping severity/joined checks) and the row-wide-attribution wrong-keep (WR-03) are both closed and confirmed by direct test run (`test_g2a_*`, `test_g2b_*`, `test_g3a_*`, `test_g3b_*` — all pass). **But** a new, independently reproduced defect means a covered/absorbed member that splits into its own row on the very pass whose real edit caused the split never gets its `nearby_at` stamp, so the decision wrongly stays "current" through exactly the edit that should reopen it. See the reproduction below and the first gap. |

**Score:** 3/4 truths verified (up from the prior 2/4 — the three originally reported blockers are closed; one new blocker surfaced by the post-closure code review remains).

## Independent Verification (real code, not SUMMARY claims)

All of the following were run directly against HEAD (`7b5feda`) in this session; none of it is read from a SUMMARY or REVIEW file.

### 1. Full regression suite

```
$ cd plugins/vibe-check/scripts && pytest -q
3248 passed, 4312 subtests passed in 163.53s (0:02:43)
```
0 failed. Matches 57-12/57-13's recorded count; confirms no regression and that the originally-reported gaps' fixtures are green.

### 2. The three original gaps' own fixtures, run directly

```
$ pytest -q test_carry_state.py -k TestGapClosure57
20 passed, 197 deselected, 8 subtests passed in 0.05s

$ pytest -q test_decision_continuity.py test_nv_render.py test_batch_card.py test_card_text.py test_finalize_card.py
226 passed, 323 subtests passed in 3.43s

$ python3 -c 'import score,test_score;assert score.stable_hash("a.py","  x=1","title")==test_score.GOLDEN_DIGEST;print("golden ok")'
golden ok
```
G1 (CR-01), G2a/G2b (CR-02), G3a/G3b (WR-03) and G6 (D-15) all pass. Golden digest unchanged.

### 3. New defect — independent reproduction, real chain, no stubs

Built from the project's own `test_decision_continuity.py` helpers (`fresh`, `run_pass`, `decide_on`, `record_of`), driving `score.run` across three real passes with a REAL diff on the split pass (not the fixture's deliberately empty `ranges={F: []}`):

```
pass1 lead hash 3449f4b5 member A hash dee0f534
pass2 findings: [('bugs', 10, 'dee0f534', {'at_pass': 2, 'file': 'src/a.py', 'line': 10,
                   'canonical_line_content': 'line_10 = 10', 'band': 'warning'})]
recA is None? False
recA snapshot: {'at_pass': 2, 'file': 'src/a.py', 'line': 10,
                'canonical_line_content': 'line_10 = 10', 'band': 'warning'}
score._nearby_changed(A, ranges2) = True
decision_state(A) = current
stale_cause(A) = None
pass2 outstanding_cw_hashes: []

pass3 recA snapshot: {..., 'nearby_at': 3}
pass3 decision_state(A) = stale
pass3 outstanding_cw_hashes: ['dee0f534...']
```

Pass 1: row B (`security`, line 12) leads a group that absorbs member A (`bugs`, line 10). The owner dismisses B. Pass 2: B's own line (12) is rewritten and resolved via a recheck verdict — the SAME diff that causes A to split out of B's dissolved row is `{F: [[12, 12]]}`, which `score._nearby_changed` correctly says IS within A's 5-line window (confirmed True). But A's newly-split row carries no `nearby_at` stamp (confirmed by printing the snapshot), so `decision_state(A)` stays `"current"` and A silently drops out of `outstanding_cw_hashes` — the owner is never told. Only on pass 3, a SECOND, separate edit near A, does the stamp finally land and the decision correctly go `stale`. This matches 57-REVIEW-GAPS.md Critical-1 exactly and confirms it is real, not a reviewer artifact.

Root cause traced in score.py: `survivor = dict(best_member)` (score.py:2566) carries no top-level `snapshot` key for a freshly split row (a member's prior evidence lives only in `obligation.snapshot`, which is never copied onto the new row). `_snapshot_for(survivor, pass_number, nearby=nearby)` (score.py:306, called at score.py:2661) only stamps `nearby_at` when `nearby and isinstance(prior, dict)` where `prior = survivor.get("snapshot")` — which is `None` here, so the stamp is dropped regardless of `nearby`.

### 4. WR-01 (diff context) — independent reproduction

```
$ seq 1 30 > a.txt && sed '9d' a.txt > b.txt
$ git diff --no-index a.txt b.txt
@@ -6,7 +6,6 @@
 6
 7
 8
-9
 10
 11
 12
$ git diff --no-index -U0 a.txt b.txt
@@ -9 +8,0 @@
-9
```

This confirms 57-REVIEW-GAPS.md WR-01: a default `git diff` (what `phases/review/00-scope.md` actually runs — `git diff HEAD`, `git diff --staged`, `gh pr diff --patch`, `git diff <range>`, none with `-U0`) reports a pure-deletion hunk as `@@ -6,7 +6,6 @@` (new-side count 6, not 0), never the `+T,0` header the 30-collect-score.md deletion rule (added in 57-12) requires to fire. The 6-line reported range also includes 5 lines of pure, unrelated context around the one real deletion.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `plugins/vibe-check/scripts/carry_state.py` | `concern_lanes`, filtered `_covers_of`, `_decision_for`, `_covering`/`covering_entry`, `_inherited_cause`/`_inherited_state`, `_nearby_since` | VERIFIED present, substantive, wired (direct grep + read); the inherited ordered checks (nearby → joined → severity) are real and correct **given a correctly-stamped snapshot** — the remaining gap is upstream in score.py's stamping, not in this ordering logic. |
| `plugins/vibe-check/scripts/score.py` | `_snapshot_for`, `_nearby_changed` (symmetric window), survivor/member construction | VERIFIED present and wired; **confirmed defect** in how a freshly split survivor's snapshot is seeded (see reproduction above). |
| `plugins/vibe-check/scripts/batch_card.py` | reads `carry_state.covering_entry`/`gained_lanes`/`newcomer_lanes`/`covered_count`, never `covers` directly | VERIFIED (`grep -c '"covers"' batch_card.py` = 0; `grep -c "carry_state.covering_entry("` = 1). |
| `plugins/vibe-check/phases/review/30-collect-score.md` | deletion-hunk range rule, symmetric-window wording | VERIFIED present as written, but the rule is **not reachable** under the orchestrator's actual diff commands (see gap 2). |
| `plugins/vibe-check/scripts/test_carry_state.py`, `test_decision_continuity.py`, `test_nv_render.py`, `test_finalize_card.py` | gap-closure fixtures (G1-G6, D-14, D-15, WR-02 lock) | VERIFIED — all pass directly (20 + 226 = 246 relevant tests, 0 failed). None of them drive the real scorer across a split pass with a real diff, which is why the new defect went uncaught (confirmed by reading `split_scenario`'s deliberately empty `ranges={F: []}`). |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `carry_state.decision_state` (inherited branch) | `carry_state._inherited_cause` | nearby → joined → severity, in order | WIRED and correctly ordered, but the `nearby` leg is fed stale/empty data by score.py for a just-split row — see gap 1 |
| `score.py` threshold loop | `_snapshot_for(survivor, pass_number, nearby=nearby)` | stamps `nearby_at` only when a prior snapshot dict exists | WIRED, but the condition excludes every freshly split survivor, which is the gap |
| `00-scope.md` diff commands | `30-collect-score.md` changed-line-ranges construction | hunk-header parsing assuming `-U0` | **NOT WIRED as documented** — the diff commands never produce the zero-context headers the rule needs; confirmed independently |
| `batch_card.py` | `carry_state.gained_lanes`/`newcomer_lanes`/`covered_count`/`covering_entry` | card renders the comparator's own values | WIRED correctly; no divergence found |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite green on HEAD | `pytest -q` (plugins/vibe-check/scripts) | 3248 passed, 0 failed | PASS |
| Original CR-01/CR-02/WR-03 fixtures pass | `pytest -q test_carry_state.py -k TestGapClosure57` | 20 passed, 0 failed | PASS |
| Golden digest unchanged | `python3 -c '...GOLDEN_DIGEST...'` | `golden ok` | PASS |
| New defect reproduces on real chain (split + real nearby diff) | ad-hoc script, `score.run`/`append_pass`/`carry_state` | `decision_state(A) == "current"` on the split pass despite a real, in-window edit; only a second edit (pass 3) reopens it | FAIL (confirms the gap) |
| WR-01 diff-context mismatch reproduces | `git diff --no-index` vs `git diff --no-index -U0` on a synthetic single-line deletion | default diff reports a 6-line, non-`+T,0` hunk; `-U0` reports the `+T,0` the prose assumes | FAIL (confirms the gap) |

## Probe Execution

Not applicable — this phase has no `scripts/*/tests/probe-*.sh` convention; verification used the project's `pytest` suite plus direct function/chain-level reproduction (recorded above).

## Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| DECN-01 | 57-01, 57-08 | Reproduce lost/wrongly-kept decisions before any rule change | SATISFIED | Both rounds landed RED fixtures before any production change; confirmed by the recorded red runs and the current green state. |
| DECN-02 | 57-02, 57-03, 57-05, 57-09, 57-10 | Decisions survive regrouping and edits unrelated to the finding's evidence | SATISFIED, with one confirmed minor gap | The original CR-01 regrouping loss is closed and confirmed. WR-01 (diff context) means an edit 6-8 lines away can be wrongly treated as "not unrelated," but this fails toward asking, not toward losing the decision — tracked as minor, not blocking. |
| DECN-03 | 57-02, 57-03, 57-04, 57-06, 57-09, 57-10, 57-11 | A decided finding reopens when its relevant evidence changes | **BLOCKED** | The original CR-02/WR-03 wrong-keeps are closed and confirmed. A new wrong-keep (covered/absorbed member splitting out on the pass whose real, in-window edit caused the split) is independently reproduced on the real chain and remains unfixed. |

REQUIREMENTS.md currently marks all three `[x]` / "Complete (gap closure 57-08..57-13)". That marking is **not supported** by the current state of the code for DECN-03 — it should be reopened pending a fix for the split-row `nearby_at` stamping defect. DECN-02 can reasonably stay marked complete with the WR-01 gap tracked separately in the backlog, consistent with how the original verification treated comparably-shaped fail-safe, not-independently-testable gaps.

## Anti-Patterns Found

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in any production or test file touched by 57-08..57-13 (the only `XXXXXX` hits are `mktemp` template placeholders in `90-finalize.md`/`50-fix-loop.md`, not debt markers). No blocker from the debt-marker gate.

## Human Verification Required

None. Both outstanding items are deterministic and were reproduced here at the function/chain level, without needing a live orchestrator run, a UI, or external services. (A live orchestrator run would additionally help confirm the real-world frequency of the WR-01 diff-context effect, but its mechanism is already conclusively demonstrated above without one.)

## Gaps Summary

The gap-closure plans (57-08..57-13) did exactly what they set out to do: all three originally reported blockers (CR-01, CR-02, WR-03) are closed, independently confirmed here by running the project's own fixtures and a full suite — not by reading SUMMARYs. D-14 (symmetric window) and D-15 (concern counting) are implemented and green.

However, a code review run AFTER that gate closed (57-REVIEW-GAPS.md, the last commit on the branch) found a new Critical and a Warning that the gate's own evidence never exercised, because every committed fixture for the inherited/split path hand-builds state rather than driving the real scorer across a split pass with a real diff. Both independently reproduce here:

1. **New blocking gap:** when a covered or absorbed member splits into its own row on the pass whose real diff caused the split — the ordinary, common shape a split takes — the new row never receives a `nearby_at` stamp even when the causing edit is genuinely inside its 5-line window, because `score.py`'s survivor construction has no top-level prior snapshot to stamp onto. The decision silently stays "current" through exactly the edit that should reopen it. This is a silent wrong-keep against SC-4/DECN-03, the project's own most-feared failure direction, and it is not a corner case.
2. **Minor, but real and systemic gap:** the orchestrator's actual diff commands never use `-U0`, so the deletion-only-hunk rule 57-12 wrote into the prose is dead against real diffs, and ordinary context lines (3 on each side of every hunk) get reported as "changed," widening the effective nearby/in_diff trigger from 5 lines to roughly 8. This fails toward asking (not toward silently dropping), its root cause predates Phase 57, and it cannot be exercised by this phase's own pytest suite — consistent with how the original verification classified similarly-shaped gaps as minor/backlog, not blocking.

**Recommendation:** route the new blocking gap (split-row `nearby_at` stamping) to a follow-up phase via `/bm:plan-phase --gaps` before shipping Phase 57 or starting Phase 58, since Phase 58's recovery/clear-actions work assumes decision binding is already correct. The minor gap (diff-context range construction) can go to the backlog, but flag it for priority attention given its breadth (it affects every diff the orchestrator ever builds, not an edge case) — ideally bundled into the same follow-up phase since both gaps touch the same `changed_line_ranges`/`nearby_at` machinery.

---

*Verified: 2026-10-26T23:40:00Z*
*Verifier: Claude (bm-verifier)*
