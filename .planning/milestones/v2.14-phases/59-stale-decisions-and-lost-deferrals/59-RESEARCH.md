# Phase 59: Stale decisions and lost deferrals - Research

**Researched:** 2026-10-28
**Domain:** vibe-check decision continuity: the score.py → append_pass → carry_state → batch_card → finalize_gate chain (pure Python stdlib, prose-driven orchestrator)
**Confidence:** HIGH. Every shape was run on current code (HEAD 089f2fb; score.py and carry_state.py are unchanged since the 2.13.0 merge 24dccdc). Each candidate fix was also tried in a throwaway scratch copy.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Carried forward (locked — do not re-litigate)
- Reproduce first on current code through the real score → carry → card → finalize chain: CR-01, CR-02, CR-04, the `min_confidence=45` deferred-member loss, SA-02 (one attempt). All five verdicts are recorded before any fix lands; a non-reproducing shape is recorded and dropped, never replaced with invented work.
- Every fix: failing-before/passing-after real-chain fixture + a mutation check that trips it. `stable_hash` / GOLDEN_DIGEST frozen. Single-writer rule for `decisions` (only `carry_state.py record-decisions`).
- Nearby window = symmetric 5 lines, one constant shared with the re-check trigger (57 D-14). No new semantic "related/unrelated" classification (STALE-04).
- Inherited/covered decisions obey the same reopen rules as own decisions (D-16); a split-pass neighbour fix inside the window reopens (D-17).
- Deferred stays open below threshold; dismissed may drop (D-20). A new identical copy of a decided line is not new evidence (D-21).
- Pool evidence by obligation/hash at the read boundary (STALE-03), not by patching the representative row; results invariant under reorder, lead change, split, merge (STALE-05). Root-cause direction from 999.23: pool `carried_by_hash` into `_kept_open_rows` and the member-sidecar path; carry_state's per-hash read merges records instead of keeping the first.
- No growth per round: work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow. Live/paid checks need a separately approved bounded proposal.

#### D-21 over-asks
- **D-01:** Pooling counts only the copies of a finding that existed when the decision was made. This removes over-ask #1 (an edit beside a NEW identical copy re-asks the decision; currently locked by `test_p4_far_twin_latest_stamp_reaches_the_first_copy`, which is updated to the D-21 behaviour). CR-01's case (both copies existed at decision time) still reopens.
- **D-02:** If removing over-ask #1 needs its own task beyond the pooling change, drop it and carry it to the backlog with the reason; do not grow the phase.
- **D-03:** Over-ask #2 (round-4 WR-01: a member that joined a deferred row after the deferral is kept open at the row's band) stays carried — not in this phase.

#### Reopen card wording
- **D-04:** When a decision reopens because of an edit beside a different spot (another copy of the line — CR-01; a covered/grouped member — CR-04), the card names that line, e.g. "code next to line 30 (another copy of this line) changed since your decision on pass 2 (was: dismissed — reason)". Extends the existing stale suffix (57 D-12); same-spot reopens keep today's wording.
- **D-05:** Several spots changed in one pass → first spot plus a count: "code next to line 30 and 2 other spots changed". One line, deterministic choice of "first" (lowest line) so wording is stable under reorder (STALE-05).

#### Deferred obligations
- **D-06:** A deferred finding removed by a valid `min_confidence` (1–49; repro at 45) is treated exactly like the shipped below-threshold deferral (57-22): kept-open row under its own hash, holds Finalize like any open deferral, with a short note "below your min_confidence (45); still deferred".
- **D-07:** If SA-02 reproduces, the same rule applies: a deferred finding left out by `--all` reviewed-set scope stays an open deferred item with a note that it is outside this review's scope. If it does not reproduce: record and drop.

#### One-cycle stop (STALE-06)
- **D-08:** One cycle = build → one review (code-review + verify) → ONE fix pass limited to reproduced findings in the four qualifying classes → confirmation by each fix's before/after fixture, its mutant, and the full offline suite. No second review round. Everything else the review surfaces is recorded on the carried list with rationale.
- **D-09:** If a wrong-keep (silent keep) is still open at the end, Phase 59 closes "with known limit", the residual is recorded (backlog entry with its repro as acceptance fixture), Phase 61's release record names it, and no "reliability complete" claim is made. The milestone may still ship under an owner waiver (as v2.13 did). Do not hold the phase for another round.

### Claude's Discretion
- How pooling is implemented (index shape, where records merge, how "existed at decision time" is recorded/derived) within the single-writer rule and frozen hash; legacy records keep reading correctly.
- Where reproduction verdicts are recorded (e.g. a 59-REPRO.md ledger) and fixture layout.
- Exact note phrasing beyond the examples above.

### Deferred Ideas (OUT OF SCOPE)
- Over-ask #2 (WR-01: member joined a deferred row after the deferral, kept at the row's band) — stays in backlog 999.23.
- Over-ask #1 — carried to backlog only if it needs its own task beyond pooling (D-02).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STALE-01 | Reproduce CR-01, CR-02, CR-04 on current code as failing real-chain fixtures before any fix | All three reproduce today. The exact repro code and outputs are in "Reproduction Verdicts". CR-01 also has a multi-pass variant the original review missed. |
| STALE-02 | A decided finding whose evidence changed is re-asked next run, with the correct reopen reason | Fix sites: `_kept_open_rows`, the group-loop `row_nearby`, and `carry_state._check_state`. The card reason is the D-04/D-05 spot wording (see "Card wording"). |
| STALE-03 | Evidence pooled consistently by obligation/hash wherever it is read | Two read boundaries: score.py `carried_by_hash` (the producer side) and carry_state `_check_state` (the single reader that finalize-counts, pending, decided, batch_card and record-decisions all use). |
| STALE-04 | A deliberate decision stays decided when its evidence fingerprint is unchanged; the 5-line rule is preserved | `_NEARBY_LINES = 5` and `_nearby_changed` are untouched. The controls in "Validation Architecture" cover this: an edit at line 45, an edit outside both windows, and the N1 pin. |
| STALE-05 | Same result under reorder, lead change, split, merge | Add the CR-01, CR-02 and CR-04 shapes to `INVARIANCE_SCENARIOS` and update the coverage lock. |
| STALE-06 | One bounded cycle; unresolved silent keep → residual, no "reliability complete" | Plan shape is under "Recommended plan shape". D-08 and D-09 are the closing rules. |
| DEFR-01 | A deferred covered member removed by valid min_confidence (45) stays open | Reproduced: the member drops, the record disappears, and the gate writes. The fix site is the min_confidence branch at score.py:2507-2522. |
| DEFR-02 | SA-02 `--all` reviewed-set drop: one attempt, fix or record + drop | **Did not reproduce on the real chain.** score.py has the drop mechanism, but `05-state-all.md` (ii) forces `$CARRYFORWARD = []` and skips the step that binds `$DEFERRED_HASHES`. Recommendation: record and drop, with a pin. |
</phase_requirements>

## Summary

All four reproducible shapes fail on current code exactly as backlog 999.23 says (repro output below). SA-02 cannot be reached through the real chain. The root cause is that score.py pools evidence in one place only: the group loop's row construction. Two other producers (kept-open rows and member obligation sidecars) and the single reader (`carry_state._check_state`, which keeps the first record per hash) do not pool. On top of that, CR-04's covered members are never judged at their own lines at all.

The CR-01 multi-pass variant was not in the round-4 review. `_kept_open_rows` drops every same-hash copy except the first, so after one quiet pass the far copy is gone from state. A later edit beside it can then never re-ask. Run 2026-10-28: pass 2 quiet, pass 3 edit@33 → `current`, gate `write`. Pooling at a single pass is therefore not enough. Every carried copy of a decided identity must stay tracked: dedup kept-open rows by occurrence, not by hash.

**I ran a prototype in a scratch copy, not the repo.** It had six changes:
1. `_kept_open_rows` pools over `carried_by_hash` and dedups by occurrence.
2. The group loop's `row_nearby` judges carried copies only (the D-21 first-pass rule) plus covered carried members that have no obligation of their own (CR-04).
3. `_check_state` merges the latest `nearby_at` per hash onto the representative.
4. The min_confidence branch synthesizes the D-20 covered entry.
5. Every shape flipped: CR-01 at edit@33 and the multi-pass variant, CR-02 at edit@33, CR-04, and min_conf=45.
6. Controls held: an edit at line 45 stays `current`, and the far-twin pass 2/pass 3 is `current` (D-21).

In the decision-continuity suite, only p4 (an intended change) and five Phase-57 mutant tests failed (re-anchoring, plus one now-decorative guard; see Pitfalls). The card, carry_state, NV and fix-loop suites stayed green. The prototype is evidence of feasibility, not code to copy verbatim.

**Over-ask #1 (D-01) can be fixed only at its first pass without an extra mechanism.** Excluding fresh copies from `row_nearby` removes the pass-2/3 over-ask that p4 locks. Once the new copy becomes carried, though, a later edit beside it still re-asks: run at pass 3, edit@33 → `stale`. To tell "existed at decision time" apart from "joined later", each copy needs an origin marker carried across passes, such as a snapshot `since_pass`, compared against `decision.at_pass` in carry_state. No such field exists today; `first_pass_N` is not on findings. That is its own task, so under D-02 the planner should carry the multi-pass residual to backlog. The residual fails toward asking.

**Primary recommendation:**
1. Plan 1 (Wave 1): commit the five verdicts and red real-chain fixtures.
2. Fix the producer side in score.py: kept-open pooling plus per-occurrence rows, `row_nearby` over carried copies plus covered members, and the min_confidence D-20 synthesis.
3. Fix the reader side in `_check_state`: merge the latest `nearby_at` and derive the spot.
4. Change the card wording (D-04/D-05/D-06 note) in batch_card plus both prose files.
5. Close with one review and one qualifying fix pass.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Nearby-change detection (5-line window) | score.py (`_nearby_changed`, `_NEARBY_LINES`) | — | One constant is shared with the re-check trigger (D-14). Do not change it. |
| Evidence pooling at write time (stamp `nearby_at` on emitted rows/sidecars) | score.py `run()` group loop + `_kept_open_rows` + `_refreshed_obligation` | — | Only score.py sees the changed ranges and every copy's line. |
| Keeping every carried copy tracked across passes | score.py `_kept_open_rows` | 30-collect-score.md (carry-forward reads every open finding) | A copy missing from `findings` is gone from the next carryforward. |
| Pooling at read time (one record per hash) | carry_state.py `_check_state` | batch_card.py (via `open_findings`/`finalize_counts`) | This is the single reader: finalize-counts, pending, decided, record-decisions and batch_card all go through it. |
| Decision currency (current/stale + cause) | carry_state.py `decision_state` / `stale_cause` | — | The single comparator. Do not add a second one. |
| Writing decisions | carry_state.py `record-decisions` | — | Single-writer rule. This phase writes no decisions. |
| Deferral transport | carry_state.py `deferred` → 05-state.md `$DEFERRED_HASHES` → envelope `deferred_hashes` | score.py `deferred_covered` | Already shipped in 57-22. Reuse it. |
| Card wording | batch_card.py `_same_hash_stale` / `_stale_suffix` | phases/shared/90-finalize.md + phases/review/50-fix-loop.md (prose bound by `TestProseMatchesHelper`) | The helper renders; the prose documents; a test binds the two. |
| `--all` scope (SA-02) | phases/review/05-state-all.md (ii) | score.py `_score_member` all_mode gate | The prose guarantees no carryforward in `--all`. |

## Standard Stack

No new libraries. This phase changes existing stdlib-only Python modules and Markdown prose.

### Core
| Component | Version | Purpose | Why |
|-----------|---------|---------|-----|
| Python | 3.14.5 (local) | score.py / carry_state.py / batch_card.py | Existing runtime [VERIFIED: `python3 --version`] |
| pytest | 9.0.3 | Test runner (unittest-style tests) | Existing [VERIFIED: `pytest --version`] |
| unittest + `unittest.mock` | stdlib | Mutant patching (`mock.patch.object(score, "run", mod.run)`) | The existing mutant pattern [VERIFIED: test_decision_continuity.py:2485] |
| `test_confirmed_fix._mutant(path, name, old, new)` | in-repo | Exec a source-text-mutated module | Used by every Phase-57 mutant [VERIFIED: test_confirmed_fix.py:775] |

**Installation:** none.

## Package Legitimacy Audit

Not applicable. The phase installs no external packages, so slopcheck was not run.

## Reproduction Verdicts (run 2026-10-28 on HEAD 089f2fb)

Scratch scripts were run from `plugins/vibe-check/scripts`, importing `test_decision_continuity`'s own harness (`run_pass`, `decide_on`, `record_of`, `e2e_gate`, `fresh`, `base_file`). Nothing was stubbed. [VERIFIED: executed]

| Shape | Inputs | Current result | Verdict |
|-------|--------|----------------|---------|
| **CR-01** (zero-config) | `return None` at 10 and 30; bugs conf 60 both, deep-review; dismiss hA at pass 1; pass 2 no findings | edit@12 → kept-open @10 `nearby_at 2`, stale. **edit@33 → kept-open @10 only, `nearby_at None`, `current`, gate `write`** | REPRODUCED (wrong-keep) |
| **CR-01 multi-pass** (new) | Same pass 1; pass 2 quiet (`{F: []}`); pass 3 edit@33 | pass 2 emits ONE kept-open row (@10); the @30 copy is gone from state. pass 3 → `current`, gate `write` | REPRODUCED (wrong-keep; the second copy is lost from tracking) |
| **CR-02** | Same lines, conf 75 both, dismiss hA; pass 2: critical `security` "Injection X"@10 and "Injection Y"@30 lead, edit@33 | The hA record read is the @10 sidecar (absorbed_into b183b048), `nearby_at None` → `current`. edit@12 → stale. The gate is `outstanding-to-phase-5` only because the two new injection rows are undecided | REPRODUCED (assert `decision_state`, not just the gate) |
| **CR-04** | A bugs@10 conf 75 + B security critical@12 conf 95 → one row hB (A covered, no obligation); dismiss hB; pass 2 delete guard at line 6, `{F: [[6, 6]]}` | hB @12 `current`, `nearby_at None`, gate `write` | REPRODUCED (wrong-keep) |
| **DEFR-01** min_confidence=45 | `deferred_covered_sub_threshold_scenario("defer", min_confidence=45)` with member A conf **40** (the scenario hard-codes `STABLE_CONF`=75 today; add a `member_conf` knob) | no override → kept-open `sub-threshold; deferred-by: 3449f4b5…`, gate `outstanding-to-phase-5`. **min_confidence 45 → rows [], filtered `below-min-confidence`, NO RECORD, gate `write`** | REPRODUCED (silent loss of a deferral) |
| **SA-02** `--all` not-in-reviewed-set | Score-level probe: the D-20 state carried into an envelope with `all_mode: True`, `reviewed_union: ["src/other.py"]`, `deferred_hashes` set | score.py drops the member `not-in-reviewed-set` with no kept-open row. **But the real chain never builds this envelope:** `05-state-all.md:32` (ii) forces `$PASS_NUMBER = 1`, `$CARRYFORWARD = []` and SKIPs Phase 0.5 steps 2-5. `$DEFERRED_HASHES` is bound in step 2 (`05-state.md:74-83`). So an `--all` envelope never carries a record or a deferred hash | DID NOT REPRODUCE on the real chain → record and drop (D-07). Keep the score-level probe as the evidence that the mechanism exists. Add a pin on the prose bypass (see "Recording verdicts") |

**CR-03 (round-4) is not a defect under D-21.** The pass-2 "stamp on the line-30 row" came from a fresh copy. Under D-01/D-21 that copy is not evidence. With the D-21 first-pass rule, the far-twin at pass 2 and pass 3 reads `current` (verified in the prototype). p4 is rewritten to assert that.

## Architecture Patterns

### System Architecture Diagram

```
 Phase 0.5 (05-state.md)                       30-collect-score.md step 4
 carry_state.py decided  ──> $DECIDED_HASHES ──┐
 carry_state.py deferred ──> $DEFERRED_HASHES ─┼─> envelope {carryforward, findings,
 last pass findings ──> $CARRYFORWARD (+HEAD    │      changed_line_ranges, deferred_hashes,
   reads, relocation of decided records) ──────┘      min_confidence, all_mode, reviewed_union}
                                                              │
                                                              v
 score.run():
  carry loop: expand rows -> members; carried_obligations (leads + sidecar members);
              deferred_covered (members w/o obligation of a deferred row)
        │
        ├─> carried_by_hash = _carried_index(working)     [BEFORE any filter, D-19]
        │
        ├─> min_confidence filter ──> dropped[] (only if id in carried_obligations)  <-- DEFR-01 site
        ├─> group loop: per-member drops (silenced / intent-doc / not-in-reviewed-set) <-- SA-02 site
        │     row: prior = _pooled_prior(same_hash copies); row_nearby = _any_nearby(...) <-- CR-04 + D-21 site
        │     absorbed members: ref.obligation = _refreshed_obligation (own line only)   <-- CR-02 producer
        ├─> threshold filter ──> dropped[] (+ D-20 _covered_entry synthesis)
        └─> _kept_open_rows(dropped): ONE row per hash, nearby at own line only      <-- CR-01 site
                                                              │
                                                              v
 45-persist.md append_pass ──> state.passes[-1].findings (rows; members[].obligation sidecars)
                                                              │
                                                              v
 carry_state._check_state: rows then sidecars, FIRST record per hash wins       <-- CR-02 read site
   ├─> decision_state / stale_cause (evidence.nearby_at != current.nearby_at -> "nearby")
   ├─> finalize_counts ──> finalize_gate.decide ──> write | outstanding | medium-ack-loop
   ├─> record_decisions (evidence from the same representative record)
   └─> batch_card._same_hash_stale ──> _stale_suffix ──> card_text (90-finalize.md / 50-fix-loop.md)
```

### Key code locations (HEAD 089f2fb) [VERIFIED: read]

| Location | What | Phase-59 relevance |
|----------|------|--------------------|
| score.py:168-177 | `_NEARBY_LINES = 5` and the comment that names it the shared D-14 window | **The five-line invalidation rule. Do not touch.** |
| score.py:1475-1488 | `_nearby_changed`: `range(max(1, line - 5), line + 5 + 1)` | Same rule. Locked by `test_nearby_window_is_phase56_window` (test_decision_continuity.py:2082) and two bound mutants (:2339, :2361) |
| score.py:306-369 | `_snapshot_for`: stamps `nearby_at` only when `nearby and (prior dict or carried)`; carries `prior_nearby` on the keep and refresh branches | Any new snapshot key (e.g. a spot list) must be carried on BOTH branches, like `nearby_at` |
| score.py:377-394 | `_refreshed_obligation`: sidecar nearby judged at the member's own line only | CR-02 producer. Can stay as is if carry_state merges |
| score.py:397-409 | `_covered_entry(m, cov, capped)` | Reuse for DEFR-01 |
| score.py:412-489 | `_kept_open_rows`: `visible` = hash set (452); `row_nearby = _nearby_changed(row, …)` (472); prior = this copy's `obl["snapshot"]` only (471) | CR-01 and CR-01 multi-pass |
| score.py:581-633 | `_carried_index`, `_any_nearby`, `_prior_rank`, `_pooled_prior` | Reuse; do not rebuild |
| score.py:2316, 2418-2423 | `deferred_covered` index (every expanded member without an obligation of a deferred row; this is the WR-01 over-reach, kept per D-03) | DEFR-01 input |
| score.py:2455 | `carried_by_hash = _carried_index(...)` | Pass this into `_kept_open_rows` |
| score.py:2507-2522 | min_confidence filter; `dropped.append` only `if id(m) in carried_obligations` | **DEFR-01 fix site** |
| score.py:2609-2621 | per-member drops in the group loop (never appended to `dropped`) | SA-02 site (unreachable via prose) |
| score.py:2716-2743 | row prior pooling + `row_carried = bool(same_hash)` + `row_nearby = _any_nearby([survivor] + copies)` | **CR-04 + D-21 first-pass fix site** |
| score.py:2797-2827 | threshold drop + D-20 `_covered_entry` synthesis | Pattern to mirror for DEFR-01 |
| score.py:2834 | `_kept_open_rows(...)` call | Add the `carried_by_hash` argument |
| score.py:2291-2296 | ingress scrub strips `snapshot` from fresh findings | Any new snapshot sub-key is automatically unforgeable by agents |
| score.py:3082-3093 | `not-in-reviewed-set` drop in `_score_member` | SA-02 mechanism |
| carry_state.py:308-348 | `_check_state`: rows then sidecars; `if rec["stable_hash"] in seen: continue` (first wins) | **CR-02 read-boundary fix site** |
| carry_state.py:492-511 | `_evidence_of`: `nearby_at` from the snapshot | Reads the merged snapshot. Consistent for writer and reader |
| carry_state.py:810-816, 858-915, 918-950 | `_nearby_since` (inherited), `decision_state` (905: `evidence.nearby_at != current.nearby_at`), `stale_cause` | Unchanged comparator |
| carry_state.py:1042-1061 | `deferred()` | Unchanged |
| carry_state.py:1096-1160 | `_stored_evidence`, `record_decisions` (uses `_check_state` records) | Writer and reader share the merged view. No change to the single writer |
| batch_card.py:193-235 | `_same_hash_stale` builds the `stale` tag | Add the spot fields here |
| batch_card.py:519-551 | `_stale_suffix`: the "nearby" branch at 522-527 | D-04/D-05 wording |
| phases/shared/90-finalize.md:109; phases/review/50-fix-loop.md:62 | stale nearby suffix prose | Add the new suffix form(s) to BOTH files |
| test_card_text.py:385-428 | `TestProseMatchesHelper.suffixes()` binds prose templates to helper output in both modes | Add the spot suffix here |
| 05-state-all.md:32 | `--all` (ii): `$CARRYFORWARD = []`, skip steps 2-5 | SA-02 evidence |
| 05-state.md:74-83 | `$DEFERRED_HASHES` binding (inside step 2) | SA-02 evidence |

### Pattern 1: Pool at the producer with the existing index (CR-01)

**What:** `_kept_open_rows` takes `carried_by_hash`. For each emitted row:
- the candidate priors are every same-hash carried copy's obligation snapshot (gated on stored hash == row hash), ranked by `_pooled_prior`;
- nearby is `_any_nearby([row] + copies)`;
- `carried` is true when copies exist.

Also change the emit dedup from hash-level to occurrence-level. Skip a dropped copy only when the same occurrence (`_finding_identity`) is already visible. Otherwise a far copy disappears from state after one pass.

**Prototype shape (scratch, verified flips CR-01 and the multi-pass variant):**
```python
# _kept_open_rows(..., changed_line_ranges, carried_by_hash=None)
same = (carried_by_hash or {}).get(obl["stable_hash"], ())
cands = [o["snapshot"] for _, o in same if o is not None
         and o.get("stable_hash") == obl["stable_hash"]
         and isinstance(o.get("snapshot"), dict)]
row["snapshot"] = _pooled_prior(cands) or obl.get("snapshot")
row_nearby = _any_nearby([row] + [r for r, _ in same], changed_line_ranges)
row["snapshot"] = _snapshot_for(row, pass_number, nearby=row_nearby,
                                carried=bool(entry.get("covered")) or bool(same))
# emit dedup: skip only if the hash is visible from a KEPT row/sidecar, or this
# occurrence (_finding_identity(m)) was already emitted
```
Two same-hash kept-open rows (lines 10 and 30) are fine downstream. The group loop already emits same-hash rows at different lines (the far twin). `_check_state` collapses them into one card row (verified: one card row, cause `nearby`).

### Pattern 2: Judge nearby only at carried copies plus covered carried members (D-21 first pass + CR-04)

```python
# group loop, replacing score.py:2743
covered_m = [m for _, m, _, _, _ in scored_members
             if m is not best_member and id(m) not in carried_obligations
             and m.get("status") in _CARRIED_STATUSES]
row_nearby = _any_nearby([r for r, _ in same_hash] + covered_m, changed_line_ranges)
```
- A carried survivor is already in `same_hash`: the index holds every carried working record under `_current_hash`, the same hash the row computes.
- A fresh survivor's own line no longer stamps, which is D-21's first-pass case.
- Covered members (carried, no obligation of their own) are exactly the findings the row decision covers (D-16).
- Members that carry their own obligation are excluded, so `test_s4_fresh_lead_over_a_carried_member_is_not_stamped` stays green (verified).

### Pattern 3: Merge at the single reader (CR-02)

In `_check_state`, keep the representative record (rows first, then sidecars: today's order). Then overwrite only its snapshot's `nearby_at` with the latest well-formed `nearby_at` among every open record of that hash, on a **copy** (never mutate the state).
- Do **not** swap the whole snapshot. Its `line` and `band` feed `pending` and the band comparison.
- Optionally skip Needs-verification rows; their comparator ignores `nearby_at`.

Because `record_decisions` also reads `_check_state`, the stored decision evidence and the later comparison see the same merged value. Legacy states with diverging same-hash stamps now re-ask, which is the fail-toward-asking direction.

### Pattern 4: D-20 synthesis on the min_confidence branch (DEFR-01)

Mirror score.py:2812-2819 inside the min_confidence loop:
```python
if id(m) in deferred_covered and id(m) not in carried_obligations:
    carried_obligations[id(m)] = _covered_entry(m, deferred_covered[id(m)], <score>)
    dropped.append((m, "below-min-confidence; deferred-by: " + deferred_covered[id(m)]["covering"]))
elif id(m) in carried_obligations:
    dropped.append((m, "below-min-confidence"))
```
`<score>`: no capped score exists before grouping.
- The prototype used 0, and it worked through the chain.
- Better: the member's own `_score_member(..., second_opinion=False)` score, falling back to 0 when None.
- This is a discretion item. The kept-open row's `orchestrator_score` is not shown on the card.

### Pattern 5: Card spot wording (D-04/D-05/D-06)

- **score.py (stamp time):** when `row_nearby` is true because of spots other than the row's own line, record them on the stamped snapshot, e.g. `nearby_spots: [[line, "copy"|"grouped"], …]` sorted by line. Carry it alongside `nearby_at` on the keep and refresh branches of `_snapshot_for`, or it vanishes on the next quiet pass.
- **carry_state (`_check_state` merge):** if the latest stamp came from a different same-hash record (CR-02 sidecar at another line), add that record's line as a `"copy"` spot. This is derived at read time and never persisted.
- **batch_card `_same_hash_stale`:** expose `spot_line` (lowest), `spot_kind`, `other_spots` (count) on the `stale` tag when the cause is `nearby` and spots exist.
- **`_stale_suffix`:**
  - " — code next to line 30 (another copy of this line) changed since your decision on pass N (was: …)"
  - " — code next to line 30 and 2 other spots changed since your decision on pass N (was: …)"
  - "a finding grouped here" for kind `grouped` (phrasing is discretion)
  - The compact form likewise.
  - Same-spot reopens keep today's string byte-for-byte.
- **D-06 note:** the card does not render `kept_open` today (batch_card has no `kept_open` read). It needs a new suffix keyed on a `kept_open` value starting with `below-min-confidence…; deferred-by:`. Put the number in the reason string ("below-min-confidence 45; deferred-by: <h>") or pass it some other way; Finalize does not have `$CONFIG_MIN_CONFIDENCE` in state. Parse strictly; with no number, render without it (fail soft).
- **Prose:** add the new form(s) to 90-finalize.md and 50-fix-loop.md, plus `TestProseMatchesHelper.suffixes()` entries.

### Anti-Patterns to Avoid
- **Patching only the representative row:** forbidden by STALE-03. Fix both the producers and the reader.
- **Replacing the whole snapshot when merging:** changes `line`/`band`/`at_pass`, so `pending` and band compares move. Merge `nearby_at` (and spots) only.
- **Changing `_NEARBY_LINES`, `_nearby_changed` or `stable_hash`:** STALE-04 and GOLDEN_DIGEST forbid it.
- **Writing `decisions` from score.py or from the merge:** single-writer rule.
- **Keeping the `covered` arm and the new `bool(same)` arm both in `carried=`:** the `covered` arm becomes unreachable and its mutant no longer trips (see Pitfall 3).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Every carried copy of an identity | A new index | `carried_by_hash` / `_carried_index` (score.py:581) | Built before every filter (D-19) with the same `_current_hash` the rows use |
| Choosing the prior among copies | First-wins / positional | `_pooled_prior` + `_prior_rank` | Latest owed stamp, then oldest at_pass; already unit-tested |
| Window test | Inline line arithmetic | `_nearby_changed` / `_any_nearby` | The shared D-14 rule |
| D-20 kept-open entry | A new row builder | `_covered_entry` + `_kept_open_rows` | 57-22 shape is locked by `test_deferred_kept_open_row_shape` |
| Mutation runs | Ad-hoc file edits | `_run_mutant(name, old, new)` (score) / `test_confirmed_fix._mutant` + `mock.patch.object(carry_state, "_check_state", mod._check_state)` (carry_state) | Asserts the anchor is unique and the baseline green; exercises the real chain |
| Did-not-reproduce record | Free prose | The `DID_NOT_REPRODUCE` tuple + `TestDidNotReproducePins` pattern (test_decision_continuity.py:1849-2020) | Every "dropped" claim is backed by a green executing pin |
| Real-chain harness | New harness | `run_pass`, `decide_on`, `record_of`, `card_rows`, `e2e_gate`, `next_cf` | Already score → append_pass → carry_state → batch_card → finalize_gate |

**Key insight:** every pooling primitive already exists. The defects are places that bypass them: `_kept_open_rows`, `_refreshed_obligation` sidecars, `_check_state`, and the min_confidence branch.

## Common Pitfalls

### Pitfall 1: CR-02's merge alone makes over-ask #1 worse
**What goes wrong:** today the fresh far copy's row (line 30) is stamped at pass 2. With a `_check_state` merge, that stamp is read at pass 2, so the D-21 over-ask arrives a pass earlier.
**How to avoid:** land the group-loop `row_nearby` change (carried copies only, Pattern 2) together with or before the merge, and assert far-twin pass 2 = `current`.
**Warning sign:** the updated p4 fails at pass 2 with `stale`.

### Pitfall 2: Pooling at one pass does not fix CR-01
**What goes wrong:** with hash-level dedup in `_kept_open_rows`, the far copy is gone from state after one pass, and a pass-3 edit beside it is a wrong-keep (verified).
**How to avoid:** dedup kept-open rows by occurrence. Add the multi-pass fixture (pass 2 quiet, pass 3 edit@33) and a mutant that restores hash-level dedup.

### Pitfall 3: Decorative guards after the pooling change (known failure mode)
**What goes wrong:** with `carried=bool(entry.get("covered")) or bool(same)`, the existing mutant `test_kept_open_covered_row_without_carried_is_not_stamped` no longer trips. The covered member is carried and is itself in `carried_by_hash`, so `bool(same)` covers the `covered` arm.
**How to avoid:** either drop the redundant arm and retire or rewrite that mutant, or prove a case where only `covered` matters. Do not leave an untrippable guard.

### Pitfall 4: Existing mutants are anchored on text this phase rewrites
**What breaks** (prototype run):
- `test_nearby_judged_at_the_lead_only_loses_the_other_copy`: the anchor is the `row_nearby` line.
- `test_no_synthesized_entry_drops_the_deferred_member`: its anchor text becomes non-unique once the min_confidence branch also calls `_covered_entry`.
- `test_prior_rank_first_wins_loses_the_latest_stamp` and `test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp`: both assert p4 trips. After D-21 p4 no longer exercises pooled-prior ranking. Re-point them at a CR-01/CR-02 pooled fixture where two carried copies carry different stamps.
- `_ROW_TESTS` must include the new fixtures.
- `test_replay._MUTANTS["member"]` anchors on `changed_line_ranges)\n            members.append(ref)\n` in the group loop. Keep that text unique, or the replay mutant breaks.
**Warning sign:** `AssertionError: mutation target not unique` / `0 != 1`.

### Pitfall 5: The CR-02 fixture asserting only the gate passes before the fix
**What goes wrong:** the gate is already `outstanding-to-phase-5` because the two new injection rows are undecided.
**How to avoid:** assert `decision_state(record_of(s2, hA), s2) == "stale"`, `stale_cause == "nearby"`, and `hA in outstanding_cw_hashes`.

### Pitfall 6: The min_confidence scenario uses an invalid config or the wrong member confidence
**What goes wrong:** `config.py` accepts `min_confidence` 0-49 only. The 57-23 repro used 80 (IN-03). `deferred_covered_sub_threshold_scenario` hard-codes member conf `STABLE_CONF`=75, which 45 does not filter.
**How to avoid:** add a member-confidence knob (e.g. 40) and use 45.

### Pitfall 7: The D-01 multi-pass residual
**What goes wrong:** after the first-pass rule, a new copy that has become carried still re-asks the old decision on a later nearby edit (verified: pass 3 edit@33 → `stale`). Fixing it needs a per-copy origin marker (`since_pass`-style snapshot key, carried on keep/refresh/kept-open/sidecar) compared to `decision.at_pass` in carry_state.
**How to avoid:** under D-02, record it as a carried backlog item (fails toward asking). Do not grow the phase.

### Pitfall 8: Card spot data lost on quiet passes
**What goes wrong:** `_snapshot_for`'s keep branch rebuilds the dict from explicit keys (score.py:359-365). A new spot key is dropped unless it is copied the way `prior_nearby` is.
**Also:** `test_split_row_snapshot_is_the_split_pass_shape` locks the split-pass snapshot key set exactly. Emit spots only when a non-own spot fired, so that lock stays valid.

### Pitfall 9: Replay drift (Phase 61 GATE-02)
**What changes:** per-occurrence kept-open rows and the changed `row_nearby` alter outputs for archived envelopes with these shapes.
**How to handle:** record the expected replay deltas as named repairs (CR-01 kept-open copies, D-21 stamp removal, CR-04 stamp) for Phase 61. Run `test_replay.py` in the real git checkout; it needs `git cat-file` and fails in a non-git copy.

## Code Examples

### Real-chain fixture skeleton (pattern from TestPooledEvidence)
```python
# Source: plugins/vibe-check/scripts/test_decision_continuity.py (harness lines 156-330)
def cr01_scenario(edit, quiet_first=False):
    L0 = base_file(); L0[9] = L0[29] = "return None"
    s1, r1 = run_pass(empty_state(), L0,
                      [fresh("bugs", 10, L0, TITLE_A, conf=60),
                       fresh("bugs", 30, L0, TITLE_A, conf=60)], 1, {F: [[1, 200]]})
    hA = r1["findings"][0]["stable_hash"]; s1 = decide_on(s1, hA)
    if quiet_first:
        s1, _ = run_pass(s1, L0, [], 2, {F: []})
    n = s1["passes"][-1]["pass_number"] + 1
    s, r = run_pass(s1, L0, [], n, {F: [[edit, edit]]})
    return s, r, hA
# assert: decision_state == "stale", stale_cause == "nearby", the gate is not "write"
# (zero-config medium → "medium-ack-loop"), and the card row's stale spot line == 30 for edit@33
```

### carry_state mutant (no existing example; build on `_mutant`)
```python
from test_confirmed_fix import _mutant
CARRY_PY = os.path.join(HERE, "carry_state.py")
mod = _mutant(CARRY_PY, "carry_first_wins", "<merge line(s)>", "")
with mock.patch.object(carry_state, "_check_state", mod._check_state):
    ...  # the CR-02 fixture must now read `current` (red)
```
batch_card calls `carry_state.open_findings` / `finalize_counts`, and both resolve `_check_state` through the module global, so patching the one function covers the whole read path.

## Recording verdicts (discretion; recommendation)

- **Ledger:** `.planning/phases/59-…/59-REPRO.md` with one row per shape: inputs, current output, verdict, fixture name, and the red commit SHA. `.planning` is gitignored, but this repo force-adds phase docs (089f2fb). Commit it with `bm-sdk query commit`, or `git add -f`.
- **In-suite record:** a `REPRO_59` tuple modelled on `DID_NOT_REPRODUCE`, with SA-02 as `"did not reproduce on the real chain; dropped"`. Back it with a green pin that reads `phases/review/05-state-all.md` and asserts that the `$CARRYFORWARD = []` bypass and the "SKIP Phase 0.5 steps 2-5" phrase are present, plus a deleting mutant. That keeps the drop claim evidence-backed if the prose ever changes.
- **Failing-before evidence:** follow 57-19/57-23. Commit the red fixtures first, then the fixes, and record "red at <sha>, green at <sha>" via a reverse run (check out the fixture commit's test file against pre-fix score.py/carry_state.py).

## Recommended plan shape (planner's call; same-file edits mean sequential waves)

1. **59-01 Repro and verdicts:** red fixtures for CR-01 (edit@33, multi-pass), CR-02, CR-04, DEFR-01@45; SA-02 probe + pin; the 59-REPRO.md ledger; commit while red. No production edits (success criterion 1).
2. **59-02 score.py producers:**
   - kept-open pooling + per-occurrence rows (CR-01);
   - `row_nearby` over carried copies + covered members (D-21 first pass + CR-04);
   - min_confidence D-20 synthesis (DEFR-01);
   - p4 rewritten to D-21;
   - mutants re-anchored and new mutants added;
   - the decorative `covered` arm resolved.
3. **59-03 carry_state reader:** the `_check_state` nearby merge (CR-02) + its mutant.
4. **59-04 Card wording:** spots (score.py snapshot + carry_state derivation), `_stale_suffix`, the D-06 note, both prose files, and `TestProseMatchesHelper`.
5. **59-05 Invariance:** add the CR-01/CR-02/CR-04 scenarios (arrival order, lead flip, split) to `INVARIANCE_SCENARIOS` and update the coverage lock.
6. **Cycle close (D-08/D-09):**
   - one `/bm:code-review 59` + one verify;
   - ONE fix pass for reproduced qualifying findings only;
   - record residuals: the D-01 multi-pass over-ask (D-02), WR-01 (D-03), and anything else the review raises;
   - no second review.

Plans 3 and 4 can merge if the planner prefers. Plans 2-5 all touch test_decision_continuity.py, so keep them sequential.

## State of the Art (in this repo)

| Old | Current (after 57) | Phase 59 change |
|-----|--------------------|-----------------|
| Row evidence from the lead only | Pooled over `carried_by_hash` in the group loop (D-19) | Extend to kept-open rows; judge only carried copies; add covered members |
| carry_state first record per hash | Same | Merge the latest `nearby_at` per hash |
| D-20 keep-open on sub-threshold only | Same | Also on the min_confidence drop |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Making CR-04's "covered member" = carried member without an obligation of its own (and not the lead) matches D-16's "findings the decision covered" closely enough. A member that joined after the decision also counts; that is an over-ask in the WR-01 family | Pattern 2 | Over-asks (never wrong-keeps); carried under D-03 if seen |
| A2 | A CR-04 split variant (covered member splits out after the row was stamped) may lose the stamp on the split row, because the member's own snapshot has no prior. Not exercised | Validation | If it reproduces in the STALE-05 split permutation, the planner records it per D-09 or folds it into the same fix |
| A3 | `orchestrator_score` for a min_confidence-dropped deferred member can be any int (0 or its own score); nothing on the card renders it | Pattern 4 | Presentation/count only |
| A4 | Per-occurrence kept-open rows produce no visible duplicate on the card (verified for CR-01). The fix-loop subset/dispatch paths were not exercised with two same-hash kept-open rows | Pattern 1 | The fix-loop could target one copy only. Check in the fix-loop card tests |

## Open Questions

1. **D-01 multi-pass residual.** Known: the first-pass rule removes p4's over-ask. Unclear: whether the owner accepts that the later-pass over-ask stays. Recommendation: per D-02, carry it to 999.23 with the repro "pass 2 new far copy, pass 3 edit beside it → stale".
2. **Per-member drop reasons other than min_confidence/sub-threshold** (`_score_member` returning `sub-threshold` on a negative pre-clamp score, `intent-doc-match`) also drop a deferred covered member inside a surviving row without a kept-open row. Not reproduced and outside the approved list. Record as an observation only (no-growth rule).
3. **The `--all` state file across runs.** `05-state-all.md` treats every `--all` run as a fresh snapshot. Whether a deferral recorded in one `--all` run survives the next `--all` run's write was not investigated: it is a different mechanism from SA-02 and outside scope.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | all scripts/tests | ✓ | 3.14.5 | — |
| pytest | test runner | ✓ | 9.0.3 | — |
| git | test_replay.py (archived replay), reverse-run evidence | ✓ | (repo) | — |

No missing dependencies. No live or paid checks are needed; everything is offline.

## Validation Architecture

(`workflow.nyquist_validation` is `false` in `.planning/config.json`; this section is included because the orchestrator requested it.)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 running unittest-style classes |
| Config file | none (run from `plugins/vibe-check/scripts`) |
| Quick run command | `cd plugins/vibe-check/scripts && pytest -q test_decision_continuity.py test_carry_state.py test_card_text.py test_batch_card.py` (439 passed in ~6 s today) |
| Full suite command | `cd plugins/vibe-check/scripts && pytest -q` (3588 passed, 4757 subtests, ~167 s on 2026-10-28) |
| Gotchas | Use bare `pytest`, not `python3 -m pytest`. test_replay needs the real git checkout. Run shell fences as `bash -s <<'BASH' … BASH` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STALE-01 | Red fixtures for CR-01 (edit@33 + multi-pass), CR-02, CR-04 | real-chain | `pytest -q test_decision_continuity.py -k "cr01 or cr02 or cr04"` | ❌ Wave 0 (new class, e.g. `TestStaleDecisions59`) |
| STALE-02 | Re-asked next run + card reason (spot wording) | real-chain + card | same `-k`, plus `card_rows(s)[..]["stale"]` and `card_text_full` assertions | ❌ |
| STALE-03 | Same outcome whichever record is read (row vs sidecar; first vs second copy) | real-chain + carry_state mutant | `pytest -q test_decision_continuity.py -k "Mutants"` | partial (TestPhase57Mutants exists) |
| STALE-04 | Controls: edit at line 45 / outside both windows stays `current`; N1 pin; dismissed sub-threshold may drop; far twin (D-21) `current` at pass 2 and 3 | real-chain | `pytest -q test_decision_continuity.py -k "control or n1 or p4 or dismissed"` | partial (N1, dismiss lock, p4 to be rewritten) |
| STALE-05 | Invariance: CR-01 arrival order, CR-02 which lead sorts first (swap titles/confs), CR-04 lead flip / split | real-chain | `pytest -q test_decision_continuity.py -k "LeadOrderInvariance"` | ✅ guard exists; add scenarios + update the coverage lock |
| STALE-06 | Residual recorded; no "complete" claim | manual/doc | review of 59-REPRO.md / VERIFICATION, backlog entry | n/a |
| DEFR-01 | min_confidence 45 deferred member → kept-open, note on card, gate holds; dismiss variant still drops | real-chain + card | `pytest -q test_decision_continuity.py -k "min_conf"` | ❌ (scenario needs a member-conf knob) |
| DEFR-02 | SA-02 recorded as did-not-reproduce, with a prose pin + mutant | pin | `pytest -q test_decision_continuity.py -k "sa02 or DidNotReproduce"` | ❌ |
| (all) | Each fix's mutant trips its fixture; anchors unique; baseline green | mutation | `pytest -q test_decision_continuity.py -k Mutants` | partial |

### Sampling Rate
- **Per task commit:** the quick run command above.
- **Per wave merge:** the full suite (`pytest -q`).
- **Phase gate:** the full suite green, plus a reverse run (fixtures red against the pre-fix code, green after), recorded in 59-REPRO.md before `/bm:verify-work`.

### Wave 0 Gaps
- [ ] New fixture class(es) + scenarios in `test_decision_continuity.py` (`cr01_scenario`, `cr02_scenario`, `cr04_scenario`, `deferred_covered_sub_threshold_scenario(..., member_conf=)`)
- [ ] carry_state mutant helper (path `carry_state.py` + `mock.patch.object(carry_state, "_check_state", …)`)
- [ ] `REPRO_59` record + SA-02 prose pin
- [ ] `TestProseMatchesHelper.suffixes()` entries for the spot wording and the D-06 note

## Security Domain

`security_enforcement` is absent from config (treated as enabled). This is a local CLI plugin: no authentication, sessions or network surface is involved in this phase.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Ingress scrub strips `snapshot`/`kept_open`/`status` from agent findings (score.py:2291-2296), so new snapshot sub-keys are unforgeable. `deferred_hashes` is typed and filtered. carry_state refuses malformed state with fixed reasons |
| V6 Cryptography | no | `stable_hash` (sha256) is frozen and untouched |

| Threat Pattern | STRIDE | Mitigation |
|----------------|--------|------------|
| An agent forges `nearby_at`/spots to force or suppress a re-ask | Tampering | Already stripped at ingress. Keep any new key inside `snapshot` |
| A crafted title/reason injected into card text | Tampering | batch_card `_one_line` flattening. Spot values are ints; parse the `kept_open` number with a strict regex |
| The merge mutating persisted state | Tampering / data loss | Merge on copies only. Never write `decisions` (single writer) |

## Project Constraints (from CLAUDE.md)

There is no project CLAUDE.md. The global user instructions that apply:
- Security rules are absolute: no secrets, and no logging of sensitive data. Not relevant to this code.
- Follow existing codebase patterns before introducing new ones: the existing pooling primitives, `_mutant`, the phrase-lock pattern.
- Guard nullable returns: `snapshot` may be None or a non-dict, so use the `isinstance` checks already present. Release resources. Do not swallow exceptions. score.py's never-raise convention applies.
- Owner = product decisions; technical decisions are Claude's. D-02's residual carry and the replay-delta naming are reported in product terms.
- Repo memory: one branch/PR per phase (`feat/v2.14-phase-59`). `.planning` is gitignored but phase docs are force-added. No paid runs.

## Sources

### Primary (HIGH confidence)
- Code read at HEAD 089f2fb: score.py, carry_state.py, batch_card.py, test_decision_continuity.py, test_carry_state.py, test_card_text.py, test_confirmed_fix.py, test_replay.py, state_shape.py, phases/review/05-state.md, 05-state-all.md, 30-collect-score.md, 45-persist-all.md, phases/shared/90-finalize.md, phases/review/50-fix-loop.md
- Executed repros (scratch scripts using the repo harness) for CR-01, CR-01 multi-pass, CR-02, CR-04, min_confidence 45, and the SA-02 score-level probe
- Scratch prototype of the fixes, run against the decision-continuity, carry_state, card, NV, finalize and fix-loop suites (868 tests: 856 passed; 12 failures from p4 plus mutants that cascade from it)
- Baseline full suite: 3588 passed

### Secondary
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/57-REVIEW-GAPS4.md`, `deferred-items.md`, `57-CONTEXT.md`; ROADMAP.md 999.23; REQUIREMENTS.md

## Metadata

**Confidence breakdown:**
- Reproduction verdicts: HIGH. Executed on current code.
- Fix locations and approach: HIGH. Prototyped; all shapes flip; collateral test impact enumerated.
- Card wording / D-06 note design: MEDIUM. Designed, not prototyped.
- D-01 multi-pass residual: HIGH that it exists (executed); its disposition is the planner's call under D-02.

**Research date:** 2026-10-28
**Valid until:** until score.py, carry_state.py or batch_card.py change (re-verify line numbers before planning if any commit lands on them).
