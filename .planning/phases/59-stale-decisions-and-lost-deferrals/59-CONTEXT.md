# Phase 59: Stale decisions and lost deferrals - Context

**Gathered:** 2026-10-28
**Status:** Ready for planning

<domain>
## Phase Boundary

A decided (dismissed/deferred) finding whose evidence changed is asked again with the correct reason; a deliberate decision whose evidence did not change stays decided; a deferred obligation never disappears without a card (backlog 999.23). Requirements STALE-01..06, DEFR-01..02. Exact diff ranges (999.24) and Finalize's blob path (999.25) are Phase 60, not here. Builds on Phase 57's shipped decision continuity (carried-by-hash index, `deferred_hashes`) — do not rebuild it.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked — do not re-litigate)
- Reproduce first on current code through the real score → carry → card → finalize chain: CR-01, CR-02, CR-04, the `min_confidence=45` deferred-member loss, SA-02 (one attempt). All five verdicts are recorded before any fix lands; a non-reproducing shape is recorded and dropped, never replaced with invented work.
- Every fix: failing-before/passing-after real-chain fixture + a mutation check that trips it. `stable_hash` / GOLDEN_DIGEST frozen. Single-writer rule for `decisions` (only `carry_state.py record-decisions`).
- Nearby window = symmetric 5 lines, one constant shared with the re-check trigger (57 D-14). No new semantic "related/unrelated" classification (STALE-04).
- Inherited/covered decisions obey the same reopen rules as own decisions (D-16); a split-pass neighbour fix inside the window reopens (D-17).
- Deferred stays open below threshold; dismissed may drop (D-20). A new identical copy of a decided line is not new evidence (D-21).
- Pool evidence by obligation/hash at the read boundary (STALE-03), not by patching the representative row; results invariant under reorder, lead change, split, merge (STALE-05). Root-cause direction from 999.23: pool `carried_by_hash` into `_kept_open_rows` and the member-sidecar path; carry_state's per-hash read merges records instead of keeping the first.
- No growth per round: work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow. Live/paid checks need a separately approved bounded proposal.

### D-21 over-asks
- **D-01:** Pooling counts only the copies of a finding that existed when the decision was made. This removes over-ask #1 (an edit beside a NEW identical copy re-asks the decision; currently locked by `test_p4_far_twin_latest_stamp_reaches_the_first_copy`, which is updated to the D-21 behaviour). CR-01's case (both copies existed at decision time) still reopens.
- **D-02:** If removing over-ask #1 needs its own task beyond the pooling change, drop it and carry it to the backlog with the reason; do not grow the phase.
- **D-03:** Over-ask #2 (round-4 WR-01: a member that joined a deferred row after the deferral is kept open at the row's band) stays carried — not in this phase.

### Reopen card wording
- **D-04:** When a decision reopens because of an edit beside a different spot (another copy of the line — CR-01; a covered/grouped member — CR-04), the card names that line, e.g. "code next to line 30 (another copy of this line) changed since your decision on pass 2 (was: dismissed — reason)". Extends the existing stale suffix (57 D-12); same-spot reopens keep today's wording.
- **D-05:** Several spots changed in one pass → first spot plus a count: "code next to line 30 and 2 other spots changed". One line, deterministic choice of "first" (lowest line) so wording is stable under reorder (STALE-05).

### Deferred obligations
- **D-06:** A deferred finding removed by a valid `min_confidence` (1–49; repro at 45) is treated exactly like the shipped below-threshold deferral (57-22): kept-open row under its own hash, holds Finalize like any open deferral, with a short note "below your min_confidence (45); still deferred".
- **D-07:** If SA-02 reproduces, the same rule applies: a deferred finding left out by `--all` reviewed-set scope stays an open deferred item with a note that it is outside this review's scope. If it does not reproduce: record and drop.

### One-cycle stop (STALE-06)
- **D-08:** One cycle = build → one review (code-review + verify) → ONE fix pass limited to reproduced findings in the four qualifying classes → confirmation by each fix's before/after fixture, its mutant, and the full offline suite. No second review round. Everything else the review surfaces is recorded on the carried list with rationale.
- **D-09:** If a wrong-keep (silent keep) is still open at the end, Phase 59 closes "with known limit", the residual is recorded (backlog entry with its repro as acceptance fixture), Phase 61's release record names it, and no "reliability complete" claim is made. The milestone may still ship under an owner waiver (as v2.13 did). Do not hold the phase for another round.

### Claude's Discretion
- How pooling is implemented (index shape, where records merge, how "existed at decision time" is recorded/derived) within the single-writer rule and frozen hash; legacy records keep reading correctly.
- Where reproduction verdicts are recorded (e.g. a 59-REPRO.md ledger) and fixture layout.
- Exact note phrasing beyond the examples above.

</decisions>

<specifics>
## Specific Ideas

- CR-01 repro anchor: two identical `return None` lines at 10 and 30, dismissed; edit at 33 leaves the decision current (orchestrator re-run: edit@12 → nearby_at 2, edit@33 → None).
- min_confidence repro anchor: `test_decision_continuity.py` `deferred_covered_sub_threshold_scenario("defer", min_confidence=...)` with ≤49 (e.g. 45) and member conf below it (57 round-4 IN-03 — the earlier repro used 80, which is above the config max).
- CR-04: removing a guard beside a covered member never re-asks the row decision while the member stays in the row (57 D-14 "guarded upstream" case).

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and rules
- `.planning/REQUIREMENTS.md` — STALE-01..06, DEFR-01..02, working rule, no-growth-per-round rule, out-of-scope table
- `.planning/ROADMAP.md` §"Phase 59" and §"999.23" — approved scope, success criteria, root-cause direction

### Original evidence (Phase 57)
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/57-CONTEXT.md` — decisions D-01..D-22 (reopen rules, window, D-16/D-17/D-19/D-20/D-21)
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/57-REVIEW-GAPS4.md` — CR-01, CR-02, CR-04 repros, WR-01, IN-03
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/deferred-items.md` — min_confidence repro, SA-02, parked items and failure directions
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/57-REVIEW-GAPS3.md` — how the round-4 carried-by-hash index came to be

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `plugins/vibe-check/scripts/score.py` — `_carried_index` / `carried_by_hash` (~2455, built before filters per D-19), `_kept_open_rows` (~412), `below-min-confidence` drop (~2517), same-hash survivor lookup (~2716)
- `plugins/vibe-check/scripts/carry_state.py` — `decision_state` (~858), `deferred` (~1042), per-hash record reads (merge, don't keep first)
- `plugins/vibe-check/scripts/test_decision_continuity.py` — end-to-end journeys, `deferred_covered_sub_threshold_scenario`, `test_p4_far_twin_latest_stamp_reaches_the_first_copy`, lead-order invariance guard
- `plugins/vibe-check/scripts/test_replay.py` — `_MUTANTS` anchor pattern for mutation checks; `test_nv_render.py` phrase locks

### Established Patterns
- Mutation tests anchor on exact source text; re-anchor when rewriting a region (57-05 lesson).
- Card wording lives in `phases/shared/90-finalize.md` (stale suffix) and is phrase-locked by tests.
- Envelope key `deferred_hashes` via `carry_state.py deferred` → `$DEFERRED_HASHES` carries deferrals into scoring.

### Integration Points
- `phases/review/30-collect-score.md` (scoring + changed ranges), `phases/review/00-scope-all.md` (`--all` reviewed set, SA-02), `phases/shared/90-finalize.md` (reopen card, gate).

</code_context>

<deferred>
## Deferred Ideas

- Over-ask #2 (WR-01: member joined a deferred row after the deferral, kept at the row's band) — stays in backlog 999.23.
- Over-ask #1 — carried to backlog only if it needs its own task beyond pooling (D-02).

</deferred>

---

*Phase: 59-stale-decisions-and-lost-deferrals*
*Context gathered: 2026-10-28*
