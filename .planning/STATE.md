---
gsd_state_version: 1.0
milestone: v2.13
milestone_name: Reliable fix closure and recovery
status: executing
last_updated: "2026-10-26T19:22:37.000Z"
last_activity: 2026-10-26 -- Plan 57-06 complete (card names what changed on a reopened decision; finalize Open/Closed contract matches the helper)
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 13
  completed_plans: 12
  percent: 92
---

# Project State

**Current focus:** Phase 57 — decision-continuity-within-closure

## Current Position

Phase: 57 (decision-continuity-within-closure) — EXECUTING
Plan: 7 of 7
Status: Executing Phase 57
Last activity: 2026-10-26 -- Plan 57-06 complete (card names what changed on a reopened decision; finalize Open/Closed contract matches the helper)

## Operator Next Steps

- Phase 56 merged to main (PR #1, 31b2760, 2026-10-25). Phase 57 is planned on feat/v2.13-phase-57: 7 plans in 5 waves, plan-check passed (3 rounds), owner refinements D-05 (2026-10-25) and D-08 (2026-10-26) recorded in 57-CONTEXT.md. Plan 57-01 done (49875d4, 2934031, af1c69b): 10 reproduced paths are failing fixtures in test_decision_continuity.py, N1-N6 recorded as dropped and pinned green; carry-forward notes for 57-03 (covers must not list the lead's own member twice) and 57-05 (relocation must move the lead's own member record) in 57-01-SUMMARY.md. Plan 57-02 done (0aa704b, 72eee65): carry_state compares ordinary decisions without the line (D-01), re-asks on a nearby_at change, keeps a decision on a band drop and re-asks a rise only for a new reviewer lane; decisions save attribution; new read-only `carry_state.py decided` (refusal exits 2, like every carry_state subcommand). R1a-c, R3b, R3a-persistence and the attribution record are green; Plan 57-03 done (596dd5e, 0bb69d3): decisions record `covers` (what they covered, from state only); a decided row that gains a different reviewer's new concern reopens once with cause `joined` (same-title corroboration from another lane does not; it re-asks only on a lane-backed rise); a covered finding that splits into its own row keeps the decision while its own code line matches (`covering_decision`). Public `newcomer_lanes` / `covered_count` are what 57-06's card must read. R4 and R6 green. Plan 57-04 done (04e2c65, 273a1e4): score.py stamps `snapshot.nearby_at` when an edit reaches a carried row's line or the 5 beneath it (one `_nearby_changed` window shared with the Phase 56 re-check trigger; fresh findings never stamped; stamp carried on quiet passes), and member dedup keeps a carried obligation when a fresh duplicate out-ranks it. R2 and R5 green; 7 fixtures still red, all card wording (57-06). Replay REGRESSED 0, 0 runs differing. Plan 57-05 done (c9558e1, b249e92): 30-collect-score.md relocates decided ordinary leads and obligation members by their stored canonical line (Phase 53 cases 1-3), moves the recheck request and the lead's own member record with them; 05-state.md binds `$DECIDED_HASHES` from `carry_state.py decided`, halting on any non-zero exit; prose locked with section-scoped predicates and deletion mutants. A pre-existing red surfaced: `test_replay.py::TestDiffMode::test_member_only_mutation_exits_one` (mutant anchor stale after 57-04's score.py edit; logged in the phase deferred-items.md). (test_replay mutant since re-anchored by the orchestrator, 62d901c.) Plan 57-06 done (52de114, 41899c1, a08da21): the card names what changed on a reopened decision — `code next to it changed`, `severity rose (A → B) …: <lane> now also reports it`, and the D-10 joined note — reading `gained_lanes` / `newcomer_lanes` / `covered_count` from carry_state; legacy/NV 'severity changed' unchanged; an inherited (covering) decision that reopens now shows that decision (via `covering`); 90-finalize.md Open/Closed contract and suffix bullets match the helper, locked by `check_phase57_decisions`. Full suite 3208 passed, 0 failed. DECN-02/03 marked complete (every fixture green). Next: plan 57-07 (phase gates).
- Separately assess cost attribution from existing local logs (999.12); stop with a documented limitation if reliable attribution is unavailable.
- Reopen archived duplicate-reduction or secret-check work only when its evidence gate is met.

## Deferred Items

| Kind | Item | Status |
|------|------|--------|
| Separate task | 999.12 cost visibility feasibility | Bounded local investigation; not a milestone dependency |
| Archived | Broad duplicate reduction and reviewed-set behavior | Reopen on a current-version fixture outside closure scope |
| Archived | 999.2 deterministic secret integration | Reopen on a concrete gap unmet by an existing scanner workflow |
| Deferred | Phase 55 measurement and cancelled Phase 54 sweeps | No automatic restart; v2.12 outcome remains UNMET |

## Standing Boundaries

- Milestone planning is active; implementation follows phase plans. Paid runs and publication are not started.
- One branch/PR per phase: `feat/v2.13-phase-<N>` from `main`; current branch `feat/v2.13-phase-56` (carries milestone setup + discussion). Delete each phase branch (local + GitHub) after its PR merges.
- Any paid work needs a separately bounded proposal and explicit approval; estimates are not hard spending caps.
- Reuse valid evidence for unchanged code. Keep closure and owner decisions tied to actual evidence; do not substitute automatic closure for verification.
- Each phase starts by reproducing its failure on current code; a non-reproducing path is recorded and dropped, not replaced with invented work.
- No private holdout access, hook/settings changes or cross-repo implementation is included.

## Records

- [Roadmap](ROADMAP.md): active v2.13 milestone (Phases 56–58) and separate cost feasibility task.
- [Requirements](REQUIREMENTS.md): 14 v2.13 requirements with phase traceability.
- [Maintenance](backlog/MAINTENANCE.md): opportunistic cleanup and documented residuals.
- [ROI archive](backlog/archive/2026-10-18/ROI-DEFERRED.md): lower-value work and reopening conditions.
- [Archived backlog](backlog/archive/2026-10-18/README.md): historical dispositions and parked campaigns.
- [v2.12 archived roadmap](milestones/v2.12-ROADMAP.md): shipped scope and incomplete measurement.

## Session Continuity

2026-10-23: v2.13 Reliable fix closure and recovery started (research skipped; next phase number 56). Roadmap written the same day: Phase 56 Verified fixes close (VFIX-01..06), Phase 57 Decision continuity within closure (DECN-01..03), Phase 58 Clear actions, recovery and answers acted on (RECV-01..02, ANSR-01..03). HANDOFF.json still holds the stale v2.12 Phase 54 checkpoint; left untouched.

2026-10-23: 56-01 complete (commits 7b7f0d3, d4c7822, ef1c83f, 03087a0). Six-row fixture trimmed from real iPlayarr state; P2a, P2b, P2c and P3 reproduced as failing score-level fixtures; full suite 2977 passed + 33 expected RED failures, all in test_verified_fixes.py. Decisions: contract reason strings pinned as literals; Pitfall 2 is reachable at score level (a bound plain `codex-adversarial` request closes a needs-recheck row today) and is pinned RED. Only VFIX-01 marked complete; VFIX-03..06 close with 56-03.

2026-10-23: 56-02 complete (commits b8b81c0, 3898a23). P1 (one-pass independent re-check limit) reproduced: score.py age gate (`stale fix verdict` on a pass-3 retry of the same at_pass-1 verdict), carry_state awaiting list (`[]` at a later pass), and 05-state forwarding plus every other Phase 56 prose change locked RED in TestProse56 (with a green positive-control class proving each needle load-bearing). Old one-pass tests rewritten into changed-code-at-any-age tests. Full suite 2986 passed + 46 expected RED (33 test_verified_fixes.py, 13 test_confirmed_fix.py, 0 elsewhere). VFIX-02/05 not marked; they close with 56-04/56-05.

2026-10-23: 56-03 complete (commits 0be902e, c093cce, 7f3858c). score.py gained the `route: "independent"` closure, the bound-plain persisted path, the D-04 trigger with D-06 test association, `recheck_settled` memory with fresh-start, and the D-11 no-reviewer reason (only when the envelope carries `head_blobs`); `recheck_settled` recorded in future-schema.json with `_rollback.phase56_added`. 14 mutants prove each guard. Full suite 3034 passed + 13 expected RED (all 56-04/56-05). Replay candidate REGRESSED 0; diff 170 runs, 0 differing. VFIX-03/04 marked complete; VFIX-05/06 stay pending for 56-04..56-06.

2026-10-23: 56-04 complete (commits 7f67f88, 420112b). score.py age gate now applies to fix-obsolete only; confirmed-fix verdicts are judged at any age, bound by verified_blob == head_blob. carry_state lists an applied NV item as awaiting at any later pass unless a recheck_settled fingerprint still matches HEAD (unknown HEAD blob counts as unchanged). Mutants score_m19, score_m20, cs_m7 trip. Full suite 3051 passed, 0 failed. VFIX-02 marked complete; VFIX-06 left for 56-06.

2026-10-26: 57-03 complete (commits 596dd5e, 0bb69d3, f861e83). carry_state: `covers` on every new decision (one entry per agent/file/title, lead not listed twice), `newcomer_lanes` + `covered_count` as the single readers, `joined` stale cause (priority code > nearby > joined > severity), `covering_decision` inheritance on agent+file+title+covered code line (never cross-file, never from code-less or legacy entries, never for absorbed member records). 8 new contrast mutants (12 -> 20). Full suite (minus holdout-blocked test_calibrate/test_replay) 3067 passed, 12 expected RED in test_decision_continuity.py. DECN-02/03 not marked.

2026-10-26: 57-04 complete (commits 04e2c65, 273a1e4, cfc4236). score.py: `_nearby_changed` split from `_independent_trigger` (behaviour unchanged); survivor, kept-open and obligation-member snapshots stamp `nearby_at` only on rows that existed before this pass, carried on keep/refresh; NV and audit rows pass nearby=False; member dedup moves a carried obligation onto the kept member ref (Phase 46 residual 1 closed). Mutants m57-01..07 trip. Fixtures that modelled HEAD-unchanged with non-empty ranges now use an empty incremental diff (incl. the 57-01 R5 input). Full suite (minus holdout-blocked test_calibrate/test_replay) 3090 passed, 7 expected RED (card wording, 57-06). Replay candidate REGRESSED 0; diff 170 runs, 0 differing. DECN-02/03 not marked.

2026-10-26: 57-05 complete (commits c9558e1, b249e92, 366c52e). Prose: decided-record relocation paragraph in 30-collect-score.md (incl. the lead's own member record, the 57-01 carry note), fail-closed `$DECIDED_HASHES` binding in 05-state.md (helper exits 2 on bad state; any non-zero halts), scoring.md identity sentence. 9 new tests in test_nv_render.py. Full suite (test_replay collected this time) 3191 passed, 8 RED: the 7 expected 57-06 card-wording fixtures plus the pre-existing test_replay member-mutant anchor (deferred-items.md). DECN-02/03 not marked.

2026-10-26: 57-06 complete (commits 52de114, 41899c1, a08da21, 1653eb4). batch_card stale tag gains `gained` (+ `covered`/`joined` for cause joined, all from carry_state; divergence mutant patches `newcomer_lanes`); nearby / severity-rise / joined suffixes full + compact; inherited covering-decision reopen tagged via `covering` (Rule 2). 90-finalize.md Closed rule rewritten (line not compared, nearby window, joined, drop keeps, rise needs new lane), 3 suffix bullets; 50-fix-loop.md suffix list kept in step. Full suite incl. test_replay 3208 passed, 0 failed (baseline 7 red). DECN-02/03 marked complete; progress hand-set to 12/13 = 92% (SDK miscomputes).
