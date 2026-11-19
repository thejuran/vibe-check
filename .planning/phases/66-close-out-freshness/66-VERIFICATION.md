---
phase: 66-close-out-freshness
verified: 2026-11-19T00:28:42Z
status: gaps_found
score: 8/9 must-haves verified (roadmap success criteria 3/4)
has_blocking_gaps: true
overrides_applied: 0
verified_commit: d7f43527 (code HEAD 4cee4e20), branch feat/v2.16-phase-66
evidence_class: offline only (no live reviewer run)
gaps:
  - truth: "SC3 / FRESH-03: each of the three 999.44 shapes has a recorded outcome that is a reproduced wrong keep repaired, the unsupported decision safely refused, or non-reproduction recorded with its counterexample or control"
    status: partial
    severity: blocking
    reason: "Shape 1 (deleted-original relocation) reproduces as a real wrong keep for defer and dismiss and is neither repaired nor refused: after the fresh review, the decision is carried to the identical line elsewhere and Close out writes. Its recorded outcome is 'owner-accepted known limit', which is not one of the three outcomes SC3 and FRESH-03 allow, and the milestone finish line says a waiver alone is insufficient. Shapes 2 (repaired) and 3 (safely refused) meet the criterion."
    artifacts:
      - path: "plugins/vibe-check/scripts/test_decision_continuity.py"
        issue: "TestShape1DeletedOriginal.test_shape1_deleted_original_is_reasked_at_pass2_known_limit and test_shape1_closeout_does_not_write_on_deleted_original_known_limit are expectedFailure (2 xfailed at HEAD): the wrong keep is still present by design"
      - path: ".planning/ROADMAP.md"
        issue: "999.44 closing line itself states 'FRESH-03 gate item NOT fully satisfied offline; carried to the milestone audit'"
    missing:
      - "One of: (a) an owner override recorded in this file's frontmatter accepting shape 1 as a known limit for SC3/FRESH-03; (b) the wider repair the owner declined at 66-07 Task 3 (old-side 'removed since review' lines from worktree_snap.py so a deleted original is re-asked); (c) a safe refusal for a decided line that was deleted since the review"
human_verification:
  - test: "In a live session, defer or dismiss a finding, edit the decided line, and run Close out"
    expected: "Close out prints the 'Cannot finalize' list with file:line, title, kind and cause, names the same-scope review command, says a review starts the paid reviewers, writes no REVIEW.md, and starts no reviewer"
    why_human: "The helper output and the prose are verified offline and locked by tests, but the model rendering the 90-finalize.md prose in a real session was not run. Under GATE-08 a live check needs an owner-approved bounded proposal; it stays pending for the Phase 71 release gate, not passed."
---

# Phase 66: Close out freshness — Verification Report

**Phase Goal:** Close out never completes on a deferred or dismissed decision whose reviewed code changed since the review, and the three bounded legacy wrong-keep shapes each end with an evidence-backed outcome.
**Verified:** 2026-11-19T00:28:42Z, at d7f43527 (code HEAD 4cee4e20), clean tree
**Status:** gaps_found
**Re-verification:** No — initial verification
**Evidence class:** offline only. Nothing here is a live reviewer run.

## Summary

The main repair (999.40) is real and holds: Close out refuses stale deferred and dismissed decisions, the unchanged-code path is byte-identical to 2.15.0, and every guard I mutation-tested is load-bearing. Two of the three legacy shapes meet the criterion (shape 2 repaired, shape 3 safely refused).

One success criterion is not met as written. Shape 1 reproduces as a real wrong keep and was left in place as an owner-accepted known limit. SC3 and FRESH-03 list exactly three allowed outcomes (repair, safe refusal, non-reproduction) and a known limit is none of them. The phase's own records already say this ("FRESH-03 gate item NOT fully satisfied offline"). FRESH-03 is therefore reported as partially satisfied, not satisfied.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: the 999.40 reproduction fails on 2.15.0; the candidate refuses for both kinds on an exact-line and a nearby edit, tells the user to run a fresh review, never starts a paid reviewer | VERIFIED | Own probe through the real `finalize_inputs.py` CLI (subprocess), 12 variants x 2 kinds. 2.15.0 (d5acc19 scripts extracted): `write` in every case. Candidate: `refuse` / `stop-review-again` with cause `line` (line 10: unsaved, staged, committed, whitespace-only) and `nearby` (lines 5, 13, 15); state file bytes unchanged; no REVIEW.md. `90-finalize.md:67-75` prints the list, the same-scope command per route, "A review starts the (paid) reviewers; Close out never starts them", "No asks, no writes, and stop"; never retried (line 38). Locked by `test_finalize_card.py -k review_again` (2 passed). |
| 2 | SC2: with reviewed code unchanged, Close out completes for both kinds exactly as on 2.15.0; fix-verdict freshness, 999.28 parity and real-edit reopening still pass | VERIFIED | Own probe: unchanged, edits at lines 4, 16, 40 and a pure 20-line shift all `write` for both kinds. `test_differential_unchanged_controls_identical_both_sides` compares raw stdout bytes and exit code of the d5acc19 helper and the candidate (passed). Regression set at HEAD: fix-verdict freshness 31 passed; 999.28 parity + real-edit reopening 24 passed; parity grid in the full suite. |
| 3 | SC3: each 999.44 shape has a repair, a safe refusal or a recorded non-reproduction; D-21 distinguished; no identity redesign | FAILED (partial) | Shape 1: reproduced, not repaired, not refused (2 expectedFailure tests; `ROADMAP.md` 999.44 says "NOT fully satisfied"). Shape 2: repaired, 13-line change to `carry_state._covering` (newest `at_pass` wins). Shape 3: refused with cause `untracked`, clears after `git add -N` + review. D-21 control `test_d21_identical_copy_added_while_original_remains_keeps` passes. No redesign: `score.py` byte-identical to d5acc19. See Gaps. |
| 4 | SC4: replay against 2.15.0 differs only by the intended refusals | VERIFIED | Ran `replay.py diff --base rev:d5acc19` myself at HEAD: 170 compared, 0 differing, exit 0 (`score.py` is byte-identical to d5acc19 and imports stdlib only). `test_closeout_fresh.py -k only_intended` at HEAD: passes, both directions. The named differences are 76 refusals plus 2 shape 2 repair differences; the latter are not refusals but are the owner-approved SC3 repair and are listed explicitly. |
| 5 | Every refusal cause is clearable: refuse, fresh review, re-decide, Close out writes (D-16) | VERIFIED | `TestClearable`, `TestClearableSpecialName`, `TestClearableFlagged`, `TestAllRouteClearable`, `TestPrRangeDisk`, `TestShape3Untracked`: 33 passed, 91 subtests. |
| 6 | The check fails closed: missing or malformed baseline, git failure, flagged file, unkeyable name all refuse | VERIFIED | Mutants in a scratch clone: making a git failure return "nothing stale" fails 18 tests; removing the flagged check fails 13; removing the untracked check fails 10. |
| 7 | `--all` reviews record `reviewed_tree` so Close out checks freshness on `--all` (D-12) | VERIFIED | `00-scope-all.md:96` take fence, `30-collect-score.md:95` collect fence, `45-persist.md:21,39` optional on every route; `test_all_route_records_reviewed_tree` and `test_all_route_refuses_then_clears` pass. |
| 8 | No decision-closed record means no git call and exactly the 2.15.0 result keys | VERIFIED | `TestNoDecisionNoGit`, `test_differential_no_git_when_no_decision_closed` in the full suite; `closeout_fresh.stale_decisions` returns `[]` before any git call when there are no candidates. |
| 9 | The records state the outcome truthfully (offline marked offline; known limit named, gate item not claimed satisfied) | VERIFIED | `ROADMAP.md` 999.40 and 999.44, `66-VALIDATION.md` (shape 1 row red, `nyquist_compliant: false`), `66-REPLAY.md` all say offline and name shape 1 as a known limit. |

**Score:** 8/9 (roadmap success criteria 3/4)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/closeout_fresh.py` | Freshness decision | VERIFIED | 408 lines, real reverse diff against `reviewed_tree`, six causes, fail closed |
| `plugins/vibe-check/scripts/finalize_inputs.py` | Refusal wired into Close out | VERIFIED | `_run` calls `closeout_fresh.stale_decisions(state, blobs, cwd)` at line 465 before `build_result`; `NEXT_ACTIONS` includes `stop-review-again` |
| `plugins/vibe-check/phases/shared/90-finalize.md` | User-facing refusal | VERIFIED | `stop-review-again` branch, lines 67-75; reached from `commands/review.md:68` and `commands/deep-review.md:71` |
| `plugins/vibe-check/scripts/carry_state.py` | Shape 2 repair | VERIFIED | `_covering` prefers highest `at_pass`; only change vs d5acc19 (+13/-4) |
| `plugins/vibe-check/scripts/test_closeout_fresh.py` | Repro, controls, mutants, differential | VERIFIED | 2225 lines; `TestRepro999_40`, `TestOnlyIntendedDifferences`, `TestClearable`, `TestShape3Untracked` |
| `plugins/vibe-check/scripts/test_decision_continuity.py` | Shapes 1 and 2 | VERIFIED (shape 1 = known-limit xfails) | `TestShape1DeletedOriginal`, `TestShape2CoveringOrder` |
| `plugins/vibe-check/scripts/test_finalize_parity_grid.py` | 2.14.1 side materialized from dd8e4ab | VERIFIED | `materialize_dd8e4ab`; `guard.py`, `finalize_gate.py`, `fixcommit.py`, `score.py` still byte-identical to dd8e4ab |
| `plugins/vibe-check/phases/review/00-scope-all.md` | `--all` snapshot take | VERIFIED | line 96 |
| `.planning/phases/66-close-out-freshness/66-REPLAY.md` | Replay record | VERIFIED (stale by count) | Taken at cf1ea0bd, before the review fixes; re-run here at HEAD with the same result |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `finalize_inputs._run` | `closeout_fresh.stale_decisions` | call before `build_result` | WIRED | Replacing the call with `[]` in a scratch clone: probe returns `write` on stale decisions and 184 tests fail |
| `closeout_fresh.changed_ranges` | `git diff -R --no-renames --text <reviewed_tree>` | `_git` with read-only store env | WIRED | Exact, nearby, staged, committed, whitespace-only edits all detected |
| `closeout_fresh.decided_records` | `carry_state.decision_state` / `_fix_closes` | same record set as `finalize_counts` | WIRED | Rows and absorbed members; fix-obsolete precedence kept |
| `90-finalize.md` | `finalize_inputs.NEXT_ACTIONS` | `stop-review-again` bullet | WIRED | Prose locks pass |
| `commands/review.md`, `commands/deep-review.md` | `phases/shared/90-finalize.md` | finalize route table | WIRED | |
| `00-scope-all.md` / `30-collect-score.md` | `worktree_snap.py take` / `collect` | bash fences | WIRED | real-chain `--all` test passes |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 999.40 on candidate, both kinds | own probe, real CLI subprocess | refuse on line 10 (unsaved/staged/committed/whitespace) and lines 5/13/15; write on unchanged, 4, 16, 40, pure shift | PASS |
| 999.40 on 2.15.0 | same probe on d5acc19 scripts | write in all 24 cases | PASS (reproduction confirmed) |
| Full offline suite | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` | 4729 passed, 2 xfailed, 7252 subtests, exit 0 (688 s) | PASS |
| Shapes | `test_decision_continuity.py -k "Shape1 or Shape2 or d21 or p4_far_twin"` | 8 passed, 2 xfailed (the two shape 1 known-limit tests) | PASS for shapes 2 and D-21; shape 1 xfail = gap |
| Scorer replay vs 2.15.0 | `replay.py diff --base rev:d5acc19` | 170 compared, 0 differing | PASS |
| Stdlib check | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | 35 files, no third-party imports, exit 0 | PASS |

### Mutation Checks (scratch clone, repository untouched)

| Mutant | Result | Verdict |
|--------|--------|---------|
| Freshness call in `finalize_inputs.py` replaced by `[]` | probe writes on stale decisions; 184 failed | Guard is load-bearing |
| `carry_state.py` reverted to 2.15.0 | 3 shape 2 tests fail | Repair is load-bearing |
| Untracked check removed | 10 failed | Load-bearing |
| Git failure treated as "nothing stale" | 18 failed | Load-bearing |
| Flagged-file check removed | 13 failed | Load-bearing |

The working tree was clean before and after (`git status --short` empty, HEAD d7f43527).

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| FRESH-01 | 66-01, 03, 04, 05, 06 | Close out refuses stale deferred/dismissed decisions, asks for a fresh review, never starts paid reviewers | SATISFIED (offline) | Truths 1, 5, 6, 7 |
| FRESH-02 | 66-01, 02, 04, 09 | Unchanged code still closes; fix-verdict freshness, 999.28 parity, real-edit reopening as in 2.15.0 | SATISFIED (offline) | Truths 2, 4, 8 |
| FRESH-03 | 66-03, 06, 07, 08, 09 | Each of the three 999.44 shapes has a repair, safe refusal or recorded non-reproduction | PARTIAL — not satisfied as written | Shape 2 repaired, shape 3 refused, shape 1 owner-accepted known limit |

No orphaned requirements: REQUIREMENTS.md maps only FRESH-01..03 to Phase 66 and all three are claimed by plans. REQUIREMENTS.md still shows all three unchecked and "Pending"; that file was not edited here.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `test_decision_continuity.py` | 4189, 4206 | `expectedFailure` on the two shape 1 tests | Blocker for SC3 (see Gaps) | The wrong keep is pinned as present, not fixed |
| `closeout_fresh.py` | 183, 199-201 | Legacy `medium_acknowledgments` entries are not freshness candidates | Info | An old state closed only by a legacy medium acknowledgment still closes after a code change. The family is read-only and no current flow writes it, and FRESH-01 names deferred/dismissed decisions, so this is outside the requirement. |
| `66-REPLAY.md`, `ROADMAP.md` 999.40 | — | Evidence and candidate id recorded at cf1ea0bd, before the three review-fix commits | Info | Re-run at HEAD here gives the same result; the recorded suite count (4706) is now 4729 |

No TBD, FIXME, XXX, TODO or HACK markers were added by this phase.

### Notes for the owner (recorded behaviour, not gaps)

- On `--all`, an edit near (not on) a decided line refuses once; the fresh `--all` review then keeps the decision without asking again, because `--all` sends no nearby ranges (D-12). Other routes ask again in the same situation. Pinned by `TestAllRouteClearable.test_all_route_refuses_then_clears` and recorded in 66-VALIDATION.md.
- 56 parity-grid scenarios and 12 result fixtures now refuse where 2.15.0 wrote. These are fail-closed cases where the reviewed code cannot be proven unchanged (no git, run outside the repo, untracked or unkeyable names), not ordinary unchanged-code journeys. Each is named and checked in both directions.
- Review items IN-01..04 and SA-01 are in backlog 999.46.

### Human Verification Required

### 1. Live Close out refusal

**Test:** In a live session, defer or dismiss a finding, edit the decided line, run Close out.
**Expected:** The "Cannot finalize" list with file:line, title, kind and cause; the same-scope review command; the paid-reviewers sentence; no REVIEW.md; no reviewer started.
**Why human:** The model following the prose in a real session was not run. Under GATE-08 this needs an owner-approved bounded proposal and stays pending for Phase 71.

### Gaps Summary

One gap, one root cause.

**Shape 1 (deleted-original relocation) is a reproduced wrong keep that was left in place.** What a user sees: they defer or dismiss a finding, later delete that line, and an identical line exists elsewhere in the file. Close out now refuses once (the line changed). After the fresh review it asked for, the decision is silently moved to the identical line elsewhere and kept, and Close out writes. The owner was not asked again about code they never decided on. The Close out refusal delays this by one review but does not prevent it.

SC3 and FRESH-03 allow three outcomes: repair, safe refusal, or non-reproduction with a control. "Owner-accepted known limit" is a fourth. The milestone finish line also says the 999.44 checks need one of those three and that a waiver alone is insufficient. The phase records agree with this reading and say the gate item is not fully satisfied.

No later phase covers it: Phases 67-70 are unrelated, and Phase 71 is the release gate, which checks evidence and does not repair decision carrying. It is not a deferred item.

This is a product decision, not a missing implementation. The bounded repair (D-14) was tried and broke the ordinary line-shift case; the correct fix needs old-side "removed since review" lines from `worktree_snap.py`, which the owner declined at 66-07 Task 3 according to 66-07-SUMMARY.md. That acceptance is recorded in the planning files but I cannot confirm it from this session.

**This looks intentional.** To accept the deviation, the owner adds to this file's frontmatter:

```yaml
overrides:
  - must_have: "Each of the three 999.44 shapes has a recorded outcome: a reproduced wrong keep repaired, the unsupported decision safely refused, or non-reproduction recorded with its counterexample or control"
    reason: "Shape 1 (deleted-original relocation) accepted as a known limit: the bounded repair broke ordinary line shifts and the correct repair needs removed-line evidence beyond the D-14 bound; reproduced and pinned by two expectedFailure tests"
    accepted_by: "<owner>"
    accepted_at: "<ISO timestamp>"
```

With that override the phase would be 9/9 with one human item pending (status `human_needed`). Without it, the alternatives are the wider repair or a safe refusal when a decided line was deleted since the review. Because the milestone finish line says a waiver alone is insufficient for 999.44, an override here should be paired with an explicit owner decision on that finish-line wording before the Phase 71 release gate.

---

_Verified: 2026-11-19T00:28:42Z_
_Verifier: Claude (bm-verifier)_

## Owner decision on the gap (2026-11-18)

The owner chose **(b) the wider repair** (answered live in the execute-phase orchestrator session), replacing the 66-07 known-limit choice. Scope as found by 66-07: `worktree_snap.py collect` also reports the reviewed-side lines removed since the review; the review step-0 prose and the test simulator then re-ask a decision whose original line was removed instead of relocating it to identical text elsewhere (as when a decided line is deleted with no copy). Keep the D-21 identical-copy-added control, the 20-line insertion control and the same-edit control passing; turn the two `_known_limit` xfail tests into passing tests; include a 2.15.0 (d5acc19) differential for the change and mutation checks. No override applied. Next: `/bm:plan-phase 66 --gaps`.

## Owner decision on the no-evidence fallback (2026-11-18, during gap planning)

Asked at `/bm:plan-phase 66 --gaps`: when removal evidence is missing (the code changed during the fresh review, or the prior state has no reviewed tree), should a decision that step 0 moved be re-asked, or kept as on 2.15.0? The owner answered **"Re-ask them"**. A deferred or dismissed decision whose line only shifted is then asked again in those passes; 2.15.0 kept it. This is locked scope in 66-11 (`no_evidence_shape1`, `no_evidence_shift` intended differences) and is recorded in ROADMAP 999.44 and 66-VALIDATION.md by 66-12.
