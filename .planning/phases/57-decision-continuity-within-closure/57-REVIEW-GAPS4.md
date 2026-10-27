---
phase: 57-decision-continuity-within-closure
reviewed: 2026-10-27T00:00:00Z
depth: standard
scope: "git diff cf32de8..HEAD -- plugins/ (plans 57-20..57-23, final round under D-19)"
files_reviewed: 8
files_reviewed_list:
  - plugins/vibe-check/scripts/score.py
  - plugins/vibe-check/scripts/carry_state.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_carry_state.py
  - plugins/vibe-check/scripts/test_nv_render.py
  - plugins/vibe-check/scripts/test_score.py
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/review/30-collect-score.md
findings:
  critical: 4
  warning: 2
  info: 4
  total: 10
status: issues_found
---

# Phase 57: Code Review Report (fourth and final gap closure, 57-20..57-23)

**Reviewed:** 2026-10-27 (HEAD 81bad2f)
**Depth:** standard, with real-chain repros: `score.run` → `append_pass` → `carry_state`, using `test_decision_continuity.py`'s own harness (`run_pass`, `decide_on`, `record_of`, `e2e_gate`). No stubs.
**Files Reviewed:** 8
**Status:** issues_found

## Summary

The suite is green: test_score.py has 500 passed; test_decision_continuity.py, test_carry_state.py and test_nv_render.py together have 348 passed and 493 subtests. The convention check found nothing.

**The round-3 findings are closed for the shapes they named.**
- CR-01 (both variants), CR-02, IN-01 and WR-01 are closed by 57-20/57-21.
- WR-02 is closed under D-20 by 57-22.
- I re-ran each round-3 repro, and each now re-asks.
- `carried_by_hash` is built before the NV route, min_confidence and the per-member drops. It is keyed by the same `_canonical_for_hash` the group loop uses, so index keys and row hashes cannot drift apart.

**Wrong-keep verdict: YES, wrong-keeps remain.** Three are reachable through code this round wrote, and the zero-config one is the strongest. A fourth is older. The pooling exists only inside the group loop's row construction. Two other paths emit records under a decided hash, and neither is pooled:
- kept-open rows (`_kept_open_rows`);
- member obligation sidecars (`_refreshed_obligation`).

`carry_state._check_state` then reads only the **first** record per hash (rows before sidecars) and drops the rest. So the D-19 rule "reopen if ANY carried copy's line saw a nearby change" still fails in three shapes:
- **CR-01:** both copies drop below threshold. This needs **no config**.
- **CR-02:** both copies are absorbed under other leads.
- **CR-03:** the shipped far-twin fixture itself writes at pass 2.

**CR-04** is a fourth wrong-keep, older than Phase 57's gap rounds. An edit next to a covered member that is still covered, and outside the lead's window, is never seen. D-19 pools by `stable_hash`, so it cannot reach this.

Under the owner's D-19 hard stop, CR-01..CR-04 close Phase 57 as a documented known limit, not a fifth round. CR-03's classification depends on SA-01.

**D-20:**
- **Correct:** the kept-open row is right for the planned shape (hash hA, band of the deferred row, stamp from the split edit). The `$DEFERRED_HASHES` failure modes are fail-closed (exit 2, no stdout, on every malformed input). Envelopes without `deferred_hashes` score as before.
- **Over-reach (WR-01):** it keeps open members the owner never deferred, at the deferred row's band.
- **Known edge confirmed:** the min_confidence edge is real with a *valid* config value. The recorded repro uses an invalid one (IN-03).

## Structural Findings (fallow)

No structural pre-pass was provided.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Kept-open rows are not pooled, so two same-hash carried copies that both drop below threshold keep only the first copy's evidence (WRONG-KEEP, zero-config)

**File:** `plugins/vibe-check/scripts/score.py:469-471` (`_kept_open_rows`: `row_nearby = _nearby_changed(row, ...)` at the emitted copy's own line; prior `obl.get("snapshot")` of that copy only), `score.py:428-438, 452` (the second copy is suppressed by `visible` / the emitted hash), `score.py:2817-2820` (sub-threshold `dropped.extend` in working order)

**Issue:** The D-19 docstring says the row's evidence is pooled "from an index built before any filter", and that "which filter removed a copy never decides the stamp". That is true only for rows built in the group loop. When every copy of an identity is dropped (sub-threshold, or min_confidence):
- `_kept_open_rows` emits **one** row per hash: the first in `dropped` order, which is the previous pass's row order.
- It judges nearby only at that copy's line.
- It takes only that copy's stored snapshot as its prior.
- `carried_by_hash` is never consulted.

The second copy's line, and any stamp it owed, are discarded. The second copy is also gone from the next carryforward, so its line is never tracked again.

Repro (zero config, deep-review, `return None` at lines 10 and 30, one lane, one title, conf 60 → medium rows that fall to 67 out of the diff):
```python
L0 = base_file(); L0[9] = L0[29] = "return None"
s1, r1 = run_pass(empty_state(), L0, [fresh("bugs", 10, L0, TITLE_A, conf=60),
                                     fresh("bugs", 30, L0, TITLE_A, conf=60)], 1, {F: [[1, 200]]})
hA = r1["findings"][0]["stable_hash"]; s1 = decide_on(s1, hA)
for edit in (12, 33):
    s2, r2 = run_pass(s1, L0, [], 2, {F: [[edit, edit]]})
```
```
pass1 rows [(10, 'e5286b9b', 70, 'medium'), (30, 'e5286b9b', 70, 'medium')]
edit@12 rows [(10, 'e5286b9b', 'sub-threshold', nearby_at 2, 'medium')]
   carry_state reads line 10 snap {... 'nearby_at': 2} -> stale        unack_medium 1
edit@33 rows [(10, 'e5286b9b', 'sub-threshold', nearby_at None, 'medium')]
   carry_state reads line 10 snap {'at_pass': 1, ... 'line': 10 ...} -> current   unack_medium 0   (WRONG-KEEP)
control (single copy @30, edit@33) -> kept-open @30 nearby_at 2 -> stale
```
The same edit that re-asks a lone copy at line 30 is lost once a twin exists at line 10. The min_confidence variant gives the same result (`edit@33 min_conf → current, outstanding 0`). It needs a carried conf below a valid `min_confidence` (≤49), so the sub-threshold variant above is the reachable one.

**Fix:** Pass `carried_by_hash` into `_kept_open_rows` and pool there, the way the group loop does:
```python
same = carried_by_hash.get(obl["stable_hash"], ())
row_nearby = _any_nearby([row] + [r for r, _ in same], changed_line_ranges)
cands = [o["snapshot"] for _, o in same if o is not None
         and o.get("stable_hash") == obl["stable_hash"] and isinstance(o.get("snapshot"), dict)]
row["snapshot"] = _pooled_prior(cands) or obl.get("snapshot")
row["snapshot"] = _snapshot_for(row, pass_number, nearby=row_nearby, carried=True if same else bool(entry.get("covered")))
```
Add the repro above as a real-chain fixture, in both edit positions, with a mutant that reverts to `_nearby_changed(row, ...)`.

### CR-02: Member obligation sidecars are not pooled; with both copies absorbed under other leads, the decision reads the first sidecar (WRONG-KEEP)

**File:** `plugins/vibe-check/scripts/score.py:2752-2756` (absorbed member `ref["obligation"] = _refreshed_obligation(...)`), `score.py:380-394` (`_refreshed_obligation`: nearby at the member's own line only); `carry_state.py:333-342` (first record per hash wins; sidecars in array order)

**Issue:** When neither copy of an identity leads a row, there is no row with that hash to pool into. Each copy rides as an absorbed member under a different lead, and its sidecar is stamped only by its own line. carry_state keeps the first sidecar and discards the second.

Repro (lines 10 and 30 `return None`, both decided rows at pass 1; at pass 2 a fresh critical `security` finding with a different title appears at each line and leads):
```python
L0 = base_file(); L0[9] = L0[29] = "return None"
s1, r1 = run_pass(empty_state(), L0, [fresh("bugs", 10, L0, TITLE_A, conf=75),
                                     fresh("bugs", 30, L0, TITLE_A, conf=75)], 1, {F: [[1, 200]]})
hA = r1["findings"][0]["stable_hash"]; s1 = decide_on(s1, hA)
f = [fresh("security", 10, L0, "Injection X", conf=95, severity="critical", category="injection"),
     fresh("security", 30, L0, "Injection Y", conf=95, severity="critical", category="injection")]
s2, r2 = run_pass(s1, L0, f, 2, {F: [[33, 33]]})
```
```
row (10, 'b183b048', members [(10,''), (10,'e5286b9b', nearby_at None)])
row (30, '0f1e5ff9', members [(30,''), (30,'e5286b9b', nearby_at 2)])
carry_state reads (10, absorbed_into b183b048) snap {'at_pass': 1, ...} -> current   (WRONG-KEEP)
edit@12 instead -> reads the line-10 sidecar, nearby_at 2 -> stale
```
The outcome depends on which copy's lead sorts first. That is the arrival/lead-order dependence D-19 was meant to end. The owner is asked about the two new injection rows, but hA's dismissal stays `current` and closes.

**Fix (covers CR-02 and CR-03 in one place):** make carry_state's dedup pool instead of taking the first record. When a hash repeats in `_check_state`, keep the representative record, but give it the snapshot with the latest `nearby_at` among every record with that hash (rows and sidecars). Alternatively, do it in score.py: after `kept` is final, write the latest `nearby_at` per hash onto every row snapshot and obligation snapshot that carries that hash. The carry_state option is one reader change and needs no score.py edits. It does not touch the single-writer rule, because `decisions` is not written.

### CR-03: The shipped far-twin fixture is itself a wrong-keep at pass 2: the stamp is on the second row, carry_state reads the first, and the gate writes (WRONG-KEEP, conditional on SA-01)

**File:** `plugins/vibe-check/scripts/score.py:2716-2721` (row-level `row_nearby` includes the row's own fresh survivor; the sibling row of the same hash does not see it); `carry_state.py:333-342`; `test_decision_continuity.py:1453-1470` (p4 asserts the pass-2 line-30 stamp but never what carry_state reads at pass 2)

**Issue:** In `far_twin_scenario()` pass 2:
- The line-30 row (fresh lead, carried twin elsewhere) is stamped `nearby_at 2`.
- The line-10 row (the carried copy) is not, because the edit at 33 is outside line 10's window and the fresh line-30 record is not in the index.

carry_state reads the line-10 row. The stamp only reaches it at pass 3, through the pooled prior. If the owner finalizes after pass 2, the decision closes.
```python
s2, r2, s3, hA = far_twin_scenario()
rec = record_of(s2, hA); carry_state.decision_state(rec, s2), e2e_gate(s2, {})
```
```
pass2 rows: line 10 {'at_pass': 1, ...} (no nearby_at); line 30 {'at_pass': 2, ..., 'nearby_at': 2}
pass2 carry_state reads 10 {'at_pass': 1, ...} current   gate: write      (WRONG-KEEP at pass 2)
pass3 carry_state reads 10 {..., 'nearby_at': 2} stale                    (re-ask arrives one pass late)
```
p4 locks "line-30 copy stamped" at pass 2 and "re-asked" at pass 3. So by the suite's own contract the stamp is owed at pass 2, and a pass-2 finalize is a wrong-keep. If the owner rules (SA-01) that a *fresh* copy's own-line edit is not owed (D-19's text says "carried copy"), this flips. Then there is no pass-2 wrong-keep, and the pass-3 re-ask is an over-ask. In either case pass 2 and pass 3 disagree on unchanged code.

**Fix:** The CR-02 carry_state pooling fix closes this as well (the pass-2 read would pick up `nearby_at 2`). Add a pass-2 `_assert_reasked(s2, hA)` (or the inverse, per SA-01) to p4.

### CR-04 (pre-existing, outside this round's diff): An edit next to a covered member that is still covered, and outside the lead's window, never re-asks the row decision (WRONG-KEEP)

**File:** `plugins/vibe-check/scripts/score.py:2716-2721` (row nearby = the survivor plus same-hash carried copies; a covered member has a different hash and no obligation, so it is in neither); `carry_state.py:333-342` (a covered member is not a record while covered)

**Issue:** D-14's motivating case is a "guarded upstream" dismissal that must be re-asked when the guard above the line is deleted. D-16 says covered findings obey the same reopen rules. While a covered member stays inside its row, nothing judges nearby at its line: it has no hash of its own in the index, and no snapshot. The row is judged only at the lead's line and at same-hash copies.
```python
L0 = base_file()
a = fresh("bugs", 10, L0, TITLE_A, conf=75)
b = fresh("security", 12, L0, "Injection at B", conf=95, severity="critical", category="injection")
s1, r1 = run_pass(empty_state(), L0, [a, b], 1, {F: [[1, 200]]})
hB = r1["findings"][0]["stable_hash"]; s1 = decide_on(s1, hB)
L1 = list(L0); L1[5] = "line_06 = 'guard removed'"
s2, r2 = run_pass(s1, L1, [], 2, {F: [[6, 6]]})
```
```
pass1 [(12, '3449f4b5', 'warning', members [(12,'Inject'), (10,'Unchec')])]
pass2 edit@6 (inside A's window 5-15, outside B's 7-17): row 3449f4b5 nearby_at None
  records [('3449f4b5', 12, 'current', None)]  gate write                 (WRONG-KEEP)
control (A decided alone, same edit): [('dee0f534', 10, 'stale', 'nearby')]
```
If A later splits out on a quiet pass, it starts with no prior, so the pass-2 edit is forgotten permanently. This predates the 57-20..57-23 diff: round 1's CR-01 fixed only the *split pass*. It is still a reproducible wrong-keep on HEAD, and it was not previously recorded in deferred-items.md.

**Fix (backlog):** Judge the row's nearby over every member that the row decision covers (its members without an obligation of their own), not only same-hash copies. In the group loop that is `row_nearby = _any_nearby([survivor] + [r for r, _ in same_hash] + [m for _, m, _, _, _ in scored_members if id(m) not in carried_obligations and m.get("status") in _CARRIED_STATUSES], ranges)`. Acceptance fixture: the repro above.

## Warnings

### WR-01: D-20 keeps open members the owner never deferred, at the deferred row's band, labelled "deferred-by"

**File:** `plugins/vibe-check/scripts/score.py:2418-2422` (`deferred_covered` marks EVERY expanded member without an obligation of a deferred row); `score.py:174-186` (`_covered_entry` band = `cov["band"]`)

**Issue:** A member that joined the row after the deferral is not in the decision's `covers`. That includes a newcomer, which is exactly the D-08 case. It is still indexed as covered by the deferral. When it later falls below threshold, it gets a kept-open row:
- under its own hash;
- at the deferred row's band (here `critical`, where its own band is `warning` and its own score is below threshold);
- with reason `sub-threshold; deferred-by: <hB>`.

carry_state finds no `covers` entry, so `decision_state` is `None`. It is counted as an outstanding critical and blocks finalize. Without `deferred_hashes`, the same input drops normally.
```
D2 pass1: row hB alone, deferred.  pass2: A (bugs, conf 75) joins hB as a newcomer.
pass3 (B resolved, edit@12), deferred_hashes sent:
  rows [(10, '845f88b7', 'critical', 'sub-threshold; deferred-by: 3449f4b5…', nearby_at 3)]
  records [('845f88b7', 10, None, None, 'critical')]  gate outstanding-to-phase-5
pass3, deferred_hashes omitted: rows []  gate write
```
This fails toward asking, so it is not a wrong-keep. But the owner is asked about a sub-threshold finding they never decided. It shows at an inflated severity, under a reason that claims a deferral covers it.

**Fix:** Limit `deferred_covered` to members the deferral actually covered. Have `carry_state.py deferred` emit each deferral's covered identities (`{hash: [[agent, file, title], ...]}` from `covers`), and match on `_identity`. Also use the matched `covers` entry's `band` (the decision-time band) instead of the row's current band (see IN-01).

### WR-02: The pooled-evidence fixtures test only the group-loop row, so the guard's coverage claim is narrower than D-19

**File:** `plugins/vibe-check/scripts/test_decision_continuity.py:1371-1470` (TestPooledEvidence), `:1683` (INVARIANCE_SCENARIOS)

**Issue:**
- Every p/q fixture, and all nine invariance scenarios, keep at least one copy as a kept group-loop row. None covers the consumers in CR-01..CR-03: kept-open rows (both copies filtered), sidecars (both copies absorbed), or what carry_state reads on the pass where the stamp lands on the second row.
- p4 asserts `rows2[1]` (line 30) is stamped at pass 2 but never asserts on `record_of(s2, hA)`. The test therefore passes on a state whose gate writes.
- There is no mutant on carry_state's first-record-wins dedup, so no test distinguishes which same-hash record carry_state reads.

The mutants that do exist are real. All anchors are unique, each runs on a green baseline over `_ROW_TESTS`, and each patches `score.run`, which `run_pass` calls. None is decorative. The gap is in scope, not in quality.

**Fix:** Add the CR-01/CR-02 repros as invariance scenarios, plus a pass-2 carry_state assertion in p4. Add a mutant that reverses `_check_state`'s dedup order, and assert that a pooled fixture still re-asks under it.

## Info

### IN-01: `_covered_entry` uses the deferred row's *current* stored band, not the band at the deferral

**File:** `plugins/vibe-check/scripts/score.py:2418-2422` (`cf.get("band")`), comment "the band the owner deferred it at"

**Issue:** `cf` is the last pass's row. If the row's band rose after the deferral (a rise with no lane gain keeps the decision `current`), the kept-open member inherits the risen band. The comment is inaccurate. The effect is presentation or count only: the `covers` entry comparison fails toward asking, not keeping.

**Fix:** Take the band from the matching `covers` entry (via the WR-01 read), or correct the comment.

### IN-02: The `id(m) not in carried_obligations` guard is unreachable, and its line is 112 columns

**File:** `plugins/vibe-check/scripts/score.py:2814-2815`

**Issue:** `deferred_covered` is only set for members without an obligation, and each record belongs to exactly one group's `sources`. So the guard can never be false. It has no mutant (a defensive dead branch). Line 2815 is 112 columns. 57-21 kept every added line under 100.

**Fix:** Either drop the guard or comment it as defensive. Wrap the call.

### IN-03: The parked D-20 min_confidence edge is real, but its recorded repro uses an invalid config value

**File:** `deferred-items.md` ("OPEN D-20 edge…"), which reproduces with `min_confidence=80`

**Issue:** `config.py:211-231` rejects `min_confidence ≥ 50`, so 80 can never reach score.py through config. I confirmed the edge with a valid value: a covered member at conf 40, deferred row, `min_confidence` 45.
```
min_conf None rows [(10, 'sub-threshold; deferred-by: 34…')]  gate outstanding-to-phase-5
min_conf 45   rows []  filtered [(10, 'below-min-confidence')]  gate write
```
Not re-reported as new.

**Fix:** Update the backlog item's acceptance fixture to a valid value (member conf < 49, `min_confidence` ≤ 49).

### IN-04: The scorer silently treats a null or non-list `deferred_hashes` as empty

**File:** `plugins/vibe-check/scripts/score.py:2113-2118`

**Issue:** The prose binds `$DEFERRED_HASHES` fail-closed, and the CLI exits 2 with empty stdout on every malformed state (checked: bad JSON, bad `passes`, list `decisions`). The scorer, though, maps `null` or a string to `frozenset()`, which is the exact "silently empty" outcome the prose forbids. This is consistent with score.py's never-raise convention and only reachable through an orchestrator bug, so it is Info.

**Fix:** None required. Optionally report a non-list, non-absent value in `filtered`/stderr so a bad binding is visible.

## Mutant audit (priority 4)

- **57-21 (7 mutants) and 57-22 (3 mutants: kind gate, no-entry, no-carried):** all anchor on unique shipped lines (`src.count(old) == 1`). Each asserts a green unmutated baseline over `_ROW_TESTS`, and each patches `score.run`, which `run_pass` reaches. So every mutant exercises the real chain.
- **Kept-open row shape:** `test_deferred_kept_open_row_shape` asserts band, hash, reason, stamp and score. A member-band mutant would therefore be caught. That test is not in `_ROW_TESTS`, but its assertions are concrete.
- **carry_state `deferred`:** covered by direct unit tests (dismiss excluded, stale defer included, malformed → None, CLI round trip). The score-side kind gate has its own mutant.
- **Prose locks:** the 05-state/30-collect-score locks have deleting and inserting mutants.
- **Gaps:**
  - No mutant on carry_state's first-record-wins dedup (WR-02).
  - No mutant on the unreachable guard (IN-02).
  - Nothing targets `_kept_open_rows`' `_nearby_changed` (CR-01): replacing it with a pooled check leaves every current test green.

No decorative test found.

## Set aside (needs ruling)

### SA-01: Does a FRESH copy's own-line edit re-ask a decided identity when a carried twin exists elsewhere in the file?

**Where:** `score.py:2716-2721` (`row_carried = bool(same_hash)` counts a carried twin in another group; `row_nearby` includes the fresh survivor's line); locked by `test_p4_far_twin_latest_stamp_reaches_the_first_copy`
**Why excluded:** D-19's text pools evidence from "ANY *carried* copy". The `_snapshot_for` docstring says the change a finding is first raised on "is the code it is about". The shipped behaviour and p4, however, treat an edit beside a newly reported copy as owed whenever any carried twin of the hash exists.
**Effect if left as is:**
- If the edit is owed (the current lock): CR-03 is a real pass-2 wrong-keep.
- If it is not owed: pass 3 re-asks the owner because someone added a new, identical line far from the decided one. That is an over-ask contrary to DECN-02, and CR-03 drops out.
**Needs:** owner ruling: is a new occurrence of a decided identity (same file, line text and title) "relevant evidence changed" for the existing decision?

### SA-02: Per-member drops other than min_confidence and sub-threshold remove a carried obligation or deferred member with no kept-open row (not reproduced)

**Where:** `score.py:2620-2627` (`_score_member` drops: `not-in-reviewed-set` in `--all`, `silenced`, `intent-doc-match`); `dropped` is fed only by the min_confidence and sub-threshold paths.
**Why excluded:**
- `silenced` is an owner action, so the drop is intended.
- `intent-doc-match` is stable across passes for a carried record.
- `not-in-reviewed-set` (an `--all` re-run whose union omits the file) could drop a decided or deferred record without a card. I did not reproduce it this round.
**Effect if left as is:** possible silent loss of a deferred finding under `--all` scope changes (the D-20 class).
**Needs:** in scope (repro then fix), or defer next to the parked min_confidence edge.

---

_Reviewed: 2026-10-27_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
