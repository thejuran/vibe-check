---
gsd_state_version: 1.0
milestone: v2.14
milestone_name: Decision reliability
status: "Phase 60 verifying — all 5 plans executed, not merged"
last_updated: "2026-10-29T21:30:00.000Z"
last_activity: 2026-10-29 -- 60-05 complete (cycle closed; reverse run red at ce9f8b8, suite 3765 passed, replay no deltas; EVID-01..03 + FINL-01..02 complete)
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 11
  completed_plans: 11
  percent: 33
stopped_at: "Completed 60-05-PLAN.md — Phase 60 executed (5/5); next phase verification, then PR for feat/v2.14-phase-60"
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-28)

**Core value:** Catch real defects in a developer's changes before they ship — with high coverage and low noise — so a reviewer who can't manually audit the code can trust the agent's output as their safety net.
**Current focus:** Phase 60: exact-change-evidence-and-reliable-finalize

## Current Position

Phase: 60 (exact-change-evidence-and-reliable-finalize) — EXECUTED, AWAITING VERIFICATION
Plan: 5 of 5 complete
Status: Phase 60 verifying — all 5 plans executed, not merged
Last activity: 2026-10-29 -- 60-05 complete (cycle closed; reverse run red at ce9f8b8, suite 3765 passed, replay no deltas; EVID-01..03 + FINL-01..02 complete)

## Operator Next Steps

- Phase 60 executed (5/5 plans; ledger closed in 60-REPRO.md). Next: phase verification, then the Phase 60 PR from `feat/v2.14-phase-60`.
- Phase 61 inputs from Phase 60: R6 live `gh pr diff` fetch not exercised (EVID-03 known limit), R5 install resync before any manual check, replay deltas none.
- Phase 59 merged to `main` via PR #5 (squash 6dfac64, 2026-10-29); branch deleted. Phase 60 works on `feat/v2.14-phase-60` from that `main`.
- Phase 60 planned: 5 plans in 4 waves (60-01 reproduce → 60-02 range builder ∥ 60-03 Finalize → 60-04 route wiring → 60-05 close); all five executed 2026-10-29.
- Phase 59 starts with current-code real-chain reproductions of 999.23; Phase 60 = exact diff evidence and Finalize path recovery (999.24–999.25); Phase 61 = release gate.
- Ship Decision reliability before Lean orchestration; start the latter with bounded usage feasibility and Finalize-only extraction. Reviewer efficiency remains conditional.

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-10-28:

| Category | Item | Status |
|----------|------|--------|
| debug | dryrun-replace-retired-ignored | awaiting_human_verify (v2.12 holdout kit) |
| debug | finder-check-blocked-sandbox | awaiting_human_verify (v2.12 holdout kit) |
| debug | role-session-shared-tmp-leak | awaiting_human_verify (v2.12 holdout kit) |
| uat_gap | Phase 58 58-HUMAN-UAT.md | partial — live plain-English answer scenario pending (D-15) |
| verification_gap | Phase 57 57-VERIFICATION.md | gaps_found, non-blocking — SC-3 tracked as 999.24 |
| verification_gap | Phase 58 58-VERIFICATION.md | human_needed — owner-approved |

Carried from earlier:

| Kind | Item | Status |
|------|------|--------|
| Active milestone | 999.23–999.25 v2.13 known limits | v2.14 Phases 59 (999.23) and 60 (999.24–999.25); reproduce first |
| Backlog | 999.26 title-reference known limits | Deferred; safe follow-up remains |
| Following milestone | 999.12 cost visibility feasibility | Lean orchestration after reliability ships; bounded existing-record investigation |
| Conditional follow-up | Reviewer efficiency | After both releases and an approved evidence-backed comparison proposal |
| Archived | Broad duplicate reduction and reviewed-set behavior | Reopen on a current-version fixture outside closure scope |
| Archived | 999.2 deterministic secret integration | Reopen on a concrete gap unmet by an existing scanner workflow |
| Deferred | Phase 55 measurement and cancelled Phase 54 sweeps | No automatic restart; v2.12 outcome remains UNMET |
| Carried | General relocation of undecided carried rows by content (v2.13 RESEARCH OQ2) | No reproduced gate failure yet — reopen on one |

## Standing Boundaries

- v2.14 Decision reliability is the only active milestone. Paid runs, new agents and publication need explicit owner approval (a completed milestone always publishes — standing directive).
- One branch/PR per phase: `feat/<milestone>-phase-<N>` from `main`; delete each branch (local + GitHub) after its PR merges.
- Any paid work needs a separately bounded proposal and explicit approval; estimates are not hard spending caps.
- Reuse valid evidence for unchanged code. Keep closure and owner decisions tied to actual evidence; do not substitute automatic closure for verification.
- Each phase starts by reproducing its failure on current code; a non-reproducing path is recorded and dropped, not replaced with invented work.

## Records

- [Roadmap](ROADMAP.md): v2.14 Decision reliability active, Phases 59–61 (999.23–999.25) → Lean orchestration (999.12 plus Finalize extraction) → conditional Reviewer efficiency; 999.26 deferred.
- [v2.13 archived roadmap](milestones/v2.13-ROADMAP.md), [requirements](milestones/v2.13-REQUIREMENTS.md), [audit](milestones/v2.13-MILESTONE-AUDIT.md), phase dirs in milestones/v2.13-phases/.
- [Maintenance](backlog/MAINTENANCE.md): opportunistic cleanup and documented residuals.
- [ROI archive](backlog/archive/2026-10-18/ROI-DEFERRED.md): lower-value work and reopening conditions.
- [v2.12 archived roadmap](milestones/v2.12-ROADMAP.md): shipped scope and incomplete measurement.

## Session Continuity

2026-10-29: 60-05 complete (fc019b2 ledger, 9e0bb86 residuals/roadmap/requirements). Reverse run at RED SHA ce9f8b8 with current tests copied into a scratch worktree: all 15 60-01 red fixtures fail again (10 TestRealDiffRanges60, 4 TestCoordinateSpaces60 probes, Finalize walk), plus every 60-03 walk/lock and test_diff_ranges.py at collection; worktree removed. Suite at close 3765 passed, 0 failed; test_replay 64 passed; replay.py/test_replay.py/score.py/finalize_gate.py byte-unchanged since ce9f8b8 -> no replay deltas for GATE-02. Every verdict has a Green at: SHA. Residuals R1-R11 in 60-REPRO.md (R1 finalize_gate traceback helper-side only; R5 install resync before any manual check; R6 live gh pr diff fetch not exercised = EVID-03 known limit). No open silent keep; no second round (D-10). EVID-01..03, FINL-01..02 ticked. Next: Phase 60 verification, then PR.

2026-10-29: 60-04 complete (66d63de prose, 39f6dbd route tests + PR fixture, fb8b32b probes + D-04 audit). 30-collect-score.md changed-line ranges: built only from +/- body lines by scripts/diff_ranges.py, never hunk headers; working-tree coordinate contract; one range source per route (default `git diff HEAD` alone, GSD `git diff $PHASE_START`, pass >= 2 `git diff $LAST_REVIEWED_SHA`, range `git diff <range>`, PR `gh pr diff <ref> --color never`, --all none) with fixed --no-color --no-ext-diff a/ b/ flags; set -o pipefail fence halts with "Review halted — the changed lines could not be read from the diff; nothing was scored.". All three coordinate arms shipped (PR-SERIES, MIXED-COORD, DEFAULT-STAGED reproduced); reviewer diff commands unchanged. PR fixture captured with gh (PR #5, 4 sections, 286 lines), cross-checked vs local f2b6a36..98f63aa. TestRoute* x6 + TestProseRangeFence (fence read from the file; pipefail mutation-checked). DEFAULT-STAGED Probe B recorded as coordinate disagreement (line 48 unchanged on disk). _REPRO_60_PENDING_FIXTURES emptied. Full suite 3765 passed, 0 failed. EVID-01/EVID-03 not ticked (60-05 closes them). Next: 60-05.

2026-10-29: 60-03 complete (b8fb21a prose, fd8c1b9 walks, 53b35ed locks). 90-finalize.md: step 1 mints and prints BLOBFILE=, counts/rows/step-3 re-run reuse that literal; the gate reads a printed GATEFILE= (helper stderr kept in <GATEFILE>.err, so a malformed input shows the owner one sentence, never a traceback); FINALIZE_GATE_INPUT_JSON gone; one rebuild with a NEW BLOBFILE= on a missing path or failed step, second failure or a refused step stops with "Finalize stopped — nothing was written or archived; run `--finalize` again."; no REVIEW.md/archive before gate `write`, record-decisions single writer unchanged. Fresh-shell walk green on the write route and the card route (rows -> parse -> DECFILE -> record-decisions -> recount same BLOBFILE -> write); retry, stale-earlier-attempt (Pitfall 5) and malformed-GATEFILE walks; check_printed_paths now whole-file; check_file_refs_created (PRIORROWSFILE exempt via its CARDROWSFILE= binding sentence); no_cross_call_gate_input; every lock mutation-tripped. finalize_gate.py unchanged (helper-side traceback = 60-05 residual R1 input). Full suite 4 failed (the TestCoordinateSpaces60 probes -> 60-04) / 3737 passed. FINL-01/02 not ticked (60-05 closes them). Next: 60-04.

2026-10-29: 60-02 complete (617075f RED test module, 53fb637 builder). diff_ranges.py walks +/- markers against the header budgets: pure deletion [max(T,1),T+1], net-deletion replace +1 (D-02), and a -U0 `+T,0` new side numbered from the line before it (missed by the research snippet; 60-04 must call the helper, not re-derive it). Refuses commit series, @@@, short/long bodies, stray body lines with fixed reasons (CLI exit 2, empty stdout). Imports {json, re, sys}; 57 tests incl. 19 mutants, one per guard. TestRealDiffRanges60 green at 53fb637 without editing test_decision_continuity.py. Full suite: 5 failed (4 TestCoordinateSpaces60 probes -> 60-04, 1 Finalize walk -> 60-03) / 3722 passed. Next: 60-03.

2026-10-29: 60-01 complete (43d1905, 2121c57, ce9f8b8 RED SHA, cda9220 60-REPRO.md). 999.24 reproduced on real git diffs: default-context header ranges are 3 lines wider each side (L+8 edit re-asks a decision), the +T,0 deletion rule never fires, IN-04 net-deletion replace is a boundary keep. Coordinate probes all reproduced -> fixed by 60-04: PR-SERIES (patch-series ranges miss the head line), MIXED-COORD (GSD/incremental concatenation silent keep), DEFAULT-STAGED (index-coordinate --staged section wrongly reopens). ALL-ROUTE recorded as unsupported fixture (TestRouteAll pending in 60-04). 999.25 reproduced: no fence prints BLOBFILE=, and the gate fence reads $FINALIZE_GATE_INPUT_JSON across calls. Full suite at ce9f8b8: 15 failed (exactly the named red set) / 3655 passed. Next: 60-02 and 60-03.

2026-10-29: Phase 60 context gathered. Owner decisions: ranges from actual +/- markers (gh pr diff has no -U0); 57 IN-04 net-deletion replace edge folded in (D-02); Finalize rebuilds HEAD fingerprints once then stops with a plain no-write message, refusals never auto-retried (D-07/D-08); PR route proven by a checked-in real patch, live fetch reported as not exercised (D-05); Phase-59 one-cycle rule (D-10). Next: /bm:plan-phase 60.

2026-10-29: 59-05 complete (05bc268, aa1d83f, 5f6d4e1). batch_card's nearby tag carries spot_line/spot_kind/other_spots from carry_state.stale_spots; the card renders "code next to line N (another copy of this line|a finding grouped here)" and "code next to line N and K other spot(s)" (full + compact); same-spot wording byte-identical. A kept_open "below-min-confidence[ N]; deferred-by: " row gets " — below your min_confidence (N); still deferred" (strict string parse, no `re`: batch_card's import allowlist forbids it). Both prose files document all forms; TestProseMatchesHelper gains 4 entries + prose-drift mutant; seven test_cw59_ real-chain card tests incl. carry_state divergence mutant; spots-not-recorded mutant now trips cw59. Full suite 3642 passed, 0 failed; replay 64 passed; GOLDEN unmoved. STALE-02 + DEFR-01 marked complete. Next: 59-06.

2026-10-29: 59-04 complete (f8b9055, 3e31654). score.py records `nearby_spots` ([line, "copy"|"grouped"], sorted, own line excluded) on a fresh nearby stamp only when another spot fired, and carries it with nearby_at on keep/refresh (own-line spots dropped on carry). carry_state: `_well_formed_spots` validator, `_merge_nearby` derives the lifted source copy's spot on the read copy (never persisted), `stale_spots(record, state)` -> {line, kind, others} is the card's single reader. Six test_sp59_ tests + TestSnapshotSpotsUnit + mutant test_spots_not_recorded_loses_the_other_copy_line; test_sp59_ joined _READ_MERGE_ONLY. Full suite 3630 passed, 0 failed; replay 64 passed; GOLDEN unmoved. Advisory: tie-broken pooled priors pick spots by carryforward order. STALE-02/05 stay pending until 59-05 wording. Next: 59-05.

2026-10-29: 59-03 complete (1927508, a56b48c). DEFR-01 green at 1927508: the min_confidence branch keeps a deferred covered member open as kept_open 'below-min-confidence <N>; deferred-by: <hB>' (score 0). CR-02 green at a56b48c: carry_state._merge_nearby lifts the latest well-formed nearby_at per hash onto the representative, on copies, once in _check_state, so record_decisions stores the merged view. _EXPECTED_RED_UNTIL_59_03 removed. Full suite 3619 passed, 0 failed; replay 64 passed; GOLDEN unmoved. Decision: the merge also covers CR-01/p1 at read time, so two producer mutants now run with read_merge=False (each layer keeps its own lock). STALE-03/04 marked complete; STALE-02 and DEFR-01 wait for the card work in 59-04/05. Next: 59-04.

2026-10-29: 59-02 complete (c46f4dc, 25ce414, 323c0d1). CR-01, CR-01 multi-pass green at c46f4dc; CR-04 green at 25ce414; full suite 2 failed / 3613 passed, the two red are the 59-03 fixtures (cr02_edit, dmc). Decisions: kept-open rows pool prior + nearby over carried_by_hash and emit one row per dropped record, carried=bool(same) (covered arm dropped); group-loop row_nearby = carried copies + carried members without their own obligation, a fresh survivor line is not judged (D-21; p4 rewritten); three decorative arms removed (emitted set, best_member arm, kept-open fallback) and every remaining arm mutation-locked (g59/k59/l59/m59/n59 + cr02 pooled). 59-03 must empty _EXPECTED_RED_UNTIL_59_03. Next: 59-03.

2026-10-29: 59-01 complete (82ec58b red fixtures, ca9834d 59-REPRO.md). Five shapes red on the real chain (CR-01 edit@33, CR-01 multi-pass, CR-02, CR-04, DEFR-01 min_confidence=45); controls green; full suite 5 failed / 3594 passed. Decisions: RED SHA for the 59-06 reverse run is 82ec58b; SA-02 did not reproduce on the real chain and is dropped, pinned by test_nv_render.all_carryforward_bypass_holds + deleting mutant. STALE-01 and DEFR-02 marked complete; DEFR-01 waits for its fix (59-03). Next: 59-02.

2026-10-28: v2.14 roadmap written: Phase 59 Stale decisions and lost deferrals (STALE-01..06, DEFR-01..02), Phase 60 Exact change evidence and reliable Finalize (EVID-01..03, FINL-01..02), Phase 61 Release gate (GATE-01..03). 16/16 mapped (REQUIREMENTS.md said 18; corrected — 16 IDs are defined). Awaiting owner approval; uncommitted.

2026-10-28: Activated v2.14 Decision reliability via /bm:new-milestone (research skipped; scope = approved roadmap split). Branch feat/v2.14-phase-59 from main f2b6a36.

2026-10-28: Owner approved splitting the proposed combined milestone: Decision reliability first, Lean orchestration next, Reviewer efficiency as a conditional follow-up. Each owns its release gate; cost/experiments cannot delay reliability. Lean orchestration starts with Finalize and permits at most one evidence-backed extension. No activation, version/phase assignment, runtime changes or paid runs.

2026-10-28: Owner requested a prioritized reliability-and-cost release plan. Added the next-milestone scope to ROADMAP.md without activation or phase/version assignment: stale decisions → exact evidence/Finalize → bounded baseline → incremental orchestration extraction → optional measured efficiency experiments → release gates. Preserved shipped milestones, paid-run boundaries, archived work and the existing HANDOFF.json modification.

2026-10-28: v2.13 closed. Audit tech_debt (14/14, integration 6/6, suite 3588/0). Six open artifacts acknowledged as deferred. Phase dirs moved to milestones/v2.13-phases/. Released as 2.13.0 via a release PR from feat/v2.13-release; tag v2.13. Next: /bm:new-milestone.

2026-10-27: Phase 57 fourth (final, D-19) gap closure 57-20..57-23 executed. 57-20 (1ff95f1, 9fe0e0f): real-chain RED fixtures for CR-01/CR-02/IN-01/far twin and D-20 defer; invariance guard six -> nine shapes. 57-21 (1ff5702, 333a5cd): carried-by-hash index before every filter, pooled nearby and prior, one hash gate, deterministic lead; 4 mutants re-anchored + 3 new. 57-22 (70e0719, 6626edb, 92b135d): `carry_state.py deferred`, `$DEFERRED_HASHES` / `deferred_hashes`, deferred covered member kept open below threshold; 3 mutants. 57-23: all gates green at HEAD (3311 passed, 0 failed; replay 0 differing), reverse-run ledger matches every 57-20 red; DECN-03 re-marked complete; D-19 hard stop recorded in STATE and deferred-items.md; open D-20 min_confidence edge reproduced and recorded for an owner ruling. Next: /bm:code-review 57, then /bm:verify-work 57.

2026-10-27: 57-22 complete (70e0719, 6626edb, 92b135d). Decisions: score.py learns the owner's deferrals only from envelope key `deferred_hashes` (bound fail-closed by `carry_state.py deferred` as `$DEFERRED_HASHES`); a deferred covered member below threshold is a kept-open row under its own hash, stamped as carried (D-20 with D-17); a dismissed one still drops; the drop list is gated on the synthesized entry. Full suite 3311 passed, 0 failed. Next: 57-23.

2026-10-27: Phase 57 third gap closure 57-17..57-19 executed. 57-17 (cedc7a1, a9e6f7a): same-lane out-ranking re-report reproduced red on the real chain + lead-order invariance guard. 57-18 (8bd75ec, 90228be): carried-ness and the prior snapshot come from any same-hash carried source, read before dedup; WR-01 mutants. 57-19: every gate green at 90228be (3273 passed, 0 failed; replay 0 differing, no allowances), reverse-run ledger red at 584f7bb / green at 90228be, DECN-03 re-marked complete, sub-threshold covered-member observation parked, 57-REVIEW-GAPS2 items recorded closed. Next: /bm:verify-work 57.

2026-10-27: 57-18 complete (8bd75ec, 90228be). score.py: a row's carried status and prior snapshot derive from any source record carried under the row's stable_hash (lead, absorbed member, or deduped same-identity twin), read before dedup; same_hash_prior and the lead-only seed removed. WR-01 locked (w1/w2 + 4 mutants). Full suite 3273 passed, 0 failed. Next: 57-19.

2026-10-27: 57-17 complete (cedc7a1, a9e6f7a). Same-lane out-ranking re-report reproduced red on the real chain in plain, inherited-split, absorbed-split and owed-quiet shapes; lead-order invariance guard (6 scenarios x lead permutations) red for every same-lane fresh-leads permutation. Decision: higher-band permutation uses conf 100/critical; the 57-04 dup scenario runs 2 permutations (a higher band takes the lead from C). Next: 57-18.

2026-10-26: Phase 57 second gap closure 57-14..57-16 executed. 57-14 (7ff4492, 08126a8): real-chain RED fixtures for the split-pass nearby stamp + producibility guard. 57-15 (3b78957, 7e22d6d): score.py stamps nearby_at on the pass a carried finding splits into its own row (D-17); owner journey pass 7 now re-asks (deliberate D-17 expectation change). 57-16: every gate green at 7e22d6d (3259 passed, 0 failed; replay 0 differing), reverse-run ledger red at 08126a8 / green at 7e22d6d, DECN-03 re-marked complete, diff-context gap and IN-01..IN-05 parked. Next: /bm:verify-work 57.

2026-10-26: 57-09 complete (commits 7685907, 826ddf5, c870227). Decisions: decisions save `lanes` (concern_lanes: record agent + same-title members) and the band-rise rule diffs them instead of row-wide attribution; a sidecar's lanes are its own agent only (score.py freezes sidecar band/attribution); `covers` never lists a member with a foreign obligation hash; covered_count counts distinct titles. Full suite 6 failed / 3230 passed, red set owned by 57-10/57-11/57-12. Holdout hook blocked one `sed -i` command (false positive; recorded in 57-09-SUMMARY.md).

2026-10-23: v2.13 Reliable fix closure and recovery started (research skipped; next phase number 56). Roadmap written the same day: Phase 56 Verified fixes close (VFIX-01..06), Phase 57 Decision continuity within closure (DECN-01..03), Phase 58 Clear actions, recovery and answers acted on (RECV-01..02, ANSR-01..03). HANDOFF.json still holds the stale v2.12 Phase 54 checkpoint; left untouched.

2026-10-23: 56-01 complete (commits 7b7f0d3, d4c7822, ef1c83f, 03087a0). Six-row fixture trimmed from real iPlayarr state; P2a, P2b, P2c and P3 reproduced as failing score-level fixtures; full suite 2977 passed + 33 expected RED failures, all in test_verified_fixes.py. Decisions: contract reason strings pinned as literals; Pitfall 2 is reachable at score level (a bound plain `codex-adversarial` request closes a needs-recheck row today) and is pinned RED. Only VFIX-01 marked complete; VFIX-03..06 close with 56-03.

2026-10-23: 56-02 complete (commits b8b81c0, 3898a23). P1 (one-pass independent re-check limit) reproduced: score.py age gate (`stale fix verdict` on a pass-3 retry of the same at_pass-1 verdict), carry_state awaiting list (`[]` at a later pass), and 05-state forwarding plus every other Phase 56 prose change locked RED in TestProse56 (with a green positive-control class proving each needle load-bearing). Old one-pass tests rewritten into changed-code-at-any-age tests. Full suite 2986 passed + 46 expected RED (33 test_verified_fixes.py, 13 test_confirmed_fix.py, 0 elsewhere). VFIX-02/05 not marked; they close with 56-04/56-05.

2026-10-23: 56-03 complete (commits 0be902e, c093cce, 7f3858c). score.py gained the `route: "independent"` closure, the bound-plain persisted path, the D-04 trigger with D-06 test association, `recheck_settled` memory with fresh-start, and the D-11 no-reviewer reason (only when the envelope carries `head_blobs`); `recheck_settled` recorded in future-schema.json with `_rollback.phase56_added`. 14 mutants prove each guard. Full suite 3034 passed + 13 expected RED (all 56-04/56-05). Replay candidate REGRESSED 0; diff 170 runs, 0 differing. VFIX-03/04 marked complete; VFIX-05/06 stay pending for 56-04..56-06.

2026-10-23: 56-04 complete (commits 7f67f88, 420112b). score.py age gate now applies to fix-obsolete only; confirmed-fix verdicts are judged at any age, bound by verified_blob == head_blob. carry_state lists an applied NV item as awaiting at any later pass unless a recheck_settled fingerprint still matches HEAD (unknown HEAD blob counts as unchanged). Mutants score_m19, score_m20, cs_m7 trip. Full suite 3051 passed, 0 failed. VFIX-02 marked complete; VFIX-06 left for 56-06.

2026-10-26: 57-03 complete (commits 596dd5e, 0bb69d3, f861e83). carry_state: `covers` on every new decision (one entry per agent/file/title, lead not listed twice), `newcomer_lanes` + `covered_count` as the single readers, `joined` stale cause (priority code > nearby > joined > severity), `covering_decision` inheritance on agent+file+title+covered code line (never cross-file, never from code-less or legacy entries, never for absorbed member records). 8 new contrast mutants (12 -> 20). Full suite (minus holdout-blocked test_calibrate/test_replay) 3067 passed, 12 expected RED in test_decision_continuity.py. DECN-02/03 not marked.

2026-10-26: 57-04 complete (commits 04e2c65, 273a1e4, cfc4236). score.py: `_nearby_changed` split from `_independent_trigger` (behaviour unchanged); survivor, kept-open and obligation-member snapshots stamp `nearby_at` only on rows that existed before this pass, carried on keep/refresh; NV and audit rows pass nearby=False; member dedup moves a carried obligation onto the kept member ref (Phase 46 residual 1 closed). Mutants m57-01..07 trip. Fixtures that modelled HEAD-unchanged with non-empty ranges now use an empty incremental diff (incl. the 57-01 R5 input). Full suite (minus holdout-blocked test_calibrate/test_replay) 3090 passed, 7 expected RED (card wording, 57-06). Replay candidate REGRESSED 0; diff 170 runs, 0 differing. DECN-02/03 not marked.

2026-10-26: 57-05 complete (commits c9558e1, b249e92, 366c52e). Prose: decided-record relocation paragraph in 30-collect-score.md (incl. the lead's own member record, the 57-01 carry note), fail-closed `$DECIDED_HASHES` binding in 05-state.md (helper exits 2 on bad state; any non-zero halts), scoring.md identity sentence. 9 new tests in test_nv_render.py. Full suite (test_replay collected this time) 3191 passed, 8 RED: the 7 expected 57-06 card-wording fixtures plus the pre-existing test_replay member-mutant anchor (deferred-items.md). DECN-02/03 not marked.

2026-10-26: 57-06 complete (commits 52de114, 41899c1, a08da21, 1653eb4). batch_card stale tag gains `gained` (+ `covered`/`joined` for cause joined, all from carry_state; divergence mutant patches `newcomer_lanes`); nearby / severity-rise / joined suffixes full + compact; inherited covering-decision reopen tagged via `covering` (Rule 2). 90-finalize.md Closed rule rewritten (line not compared, nearby window, joined, drop keeps, rise needs new lane), 3 suffix bullets; 50-fix-loop.md suffix list kept in step. Full suite incl. test_replay 3208 passed, 0 failed (baseline 7 red). DECN-02/03 marked complete; progress hand-set to 12/13 = 92% (SDK miscomputes).

2026-10-26: 57-07 complete (commits ea3dab1, 387e2bb). Ledger: all 10 reproduced paths (R1a-R7) green by the 57-01 fixtures; the same test file run against 57-01-era production code still fails the same 22 assertions (no weakened reproduction; 57-04's R5 input edit re-checked against pre-57-04 score.py: still fails with `decision orphaned`). Repro pin retired as the rationale for the fail-closed `$DECIDED_HASHES` binding. New: cross-module guards, a 7-pass end-to-end journey, 2 mutants. Rule 1 fix in score.py: a fresh same-hash lead inherits the absorbed carried record's snapshot (nearby_at kept). Full suite 3216 passed, 0 failed; replay REGRESSED 0, runs differing 0; golden unchanged. Carried: general relocation of undecided carried rows. Progress hand-set to 13/13 = 100% (SDK miscomputes).

2026-10-26: 57-08 complete (commits a606a8e, c8ab8f8, c29e5ae). Test-only: TestGapClosure57 (CR-01 split obligation member, CR-02 inherited band rise + joined newcomer, WR-03 both directions, D-15 concern count) 6 red; D-14 above-window reopen red on offsets 1/3/5, six-above keeps green; WR-02 `deletion_hunk_ranges` fixture green with a load-bearing mapping-dropped subtest (pass-2 band is critical because the T+1 end is the relocated flagged line — advisory drift in the SUMMARY); pass-6 note flipped to 1 finding (red); WR-02 prose lock red until 57-12. Full suite incl. test_replay: 11 failed (exactly the named red set), 3220 passed. Holdout hook blocked nothing. DECN-02/03 stay unchecked (57-13). Progress hand-set to 14/19 = 74% (SDK miscomputes).

2026-10-26: 57-12 complete (commits fd36f8f, fbfa8fc). Prose only + locks: deletion-hunk and ordinary-hunk range rules in the changed-line ranges bullet (57-08 lock now green; ordinary phrase added to DELETION_RANGE_PHRASES); 'within 5 lines above or below' in 30-collect-score.md and 90-finalize.md; IN-01/D-16 wording in the Open/Closed contract; IN-02 fix; scoring.md had no window wording (unchanged). Full suite incl. test_replay 3248 passed, 0 failed. DECN-02/03 stay unchecked (57-13). Progress hand-set to 18/19 = 95% (SDK miscomputes).

2026-10-26: 57-13 complete (gap-closure gate). Gates at fbfa8fc/967f545: full suite 3248 passed, 0 failed (test_replay 64 collected); golden ok; ImportSet 3+3 passed; replay REGRESSED 0; diff 0 differing / 0 unallowed. Reverse run at 57e93d7: all 9 named 57-08 reds fail again (G1/G2a/G2b/G6 now first trip a covers-shape check added by 57-10; with that check relaxed they fail on 57-08's exact assertions), plus tests added by 57-09..57-12 for the new behaviour; WR-02 lock green on both trees. DECN-02/03 re-marked complete. Holdout hook blocked several of my ad-hoc scratch commands (none of the gate commands); recorded verbatim in 57-13-SUMMARY.md. Progress hand-set to 19/19 = 100%; ROADMAP Phase 57 left unticked ("Executed, awaiting verification").
