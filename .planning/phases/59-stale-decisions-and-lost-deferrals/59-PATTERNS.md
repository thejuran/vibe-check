# Phase 59: Stale decisions and lost deferrals - Pattern Map

**Mapped:** 2026-10-28
**Files analyzed:** 9 (6 modified source/test files, 2 prose files, 1 new ledger doc)
**Analogs found:** 9 / 9 (every file has an in-repo analog; most are the same file's own Phase-57 code)

All paths below are relative to `plugins/vibe-check/` unless they start with `.planning/`. Line numbers are at HEAD 62ea77e (score.py / carry_state.py / batch_card.py unchanged since 24dccdc). Re-verify before editing if any commit lands on them.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/test_decision_continuity.py` (scenarios, `TestStaleDecisions59`, p4 rewrite, `REPRO_59` + SA-02 pin, mutants, invariance rows) | test (real-chain) | batch (score → append_pass → carry_state → batch_card → finalize_gate) | same file: `far_twin_scenario` / `TestPooledEvidence` / `TestDeferredStaysOpen` / `TestPhase57Mutants` / `DID_NOT_REPRODUCE` | exact |
| `scripts/score.py` `_kept_open_rows` (pool over `carried_by_hash`, per-occurrence dedup) | service (scorer) | transform | same file: group-loop pooling block (2716-2743) | exact |
| `scripts/score.py` group loop `row_nearby` (carried copies + covered members) | service | transform | same file: 2738-2743 + `_any_nearby` (607-610) | exact |
| `scripts/score.py` min_confidence branch (D-20 synthesis, DEFR-01) | service | transform / filter | same file: threshold-drop D-20 synthesis (2803-2819) | exact |
| `scripts/score.py` `_snapshot_for` (optional `nearby_spots` key for D-04/D-05) | utility | transform | same file: `prior_nearby` carry on keep + refresh branches (354-369) | exact |
| `scripts/carry_state.py` `_check_state` (merge latest `nearby_at` per hash, CR-02) | service (single reader) | request-response (state read) | same file: `_check_state` rows-then-sidecars dedup (308-348) | exact |
| `scripts/batch_card.py` `_same_hash_stale` + `_stale_suffix` (+ new kept_open note) | component (card renderer) | transform | same file: `cause == "joined"` extra tag fields (232-236) and `nearby` suffix branch (522-527) | exact |
| `phases/shared/90-finalize.md` line 109, `phases/review/50-fix-loop.md` line 62 | config (orchestrator prose) | — | the existing `stale nearby` suffix template on those lines | exact |
| `scripts/test_card_text.py` `TestProseMatchesHelper.suffixes()` + new state builders | test (prose-lock) | — | same class (385-436) + `nearby_stale_state` (65-70) | exact |
| SA-02 prose pin on `phases/review/05-state-all.md` (read-only; the prose file is NOT edited) | test (prose-lock + deleting mutant) | — | `test_nv_render.py` `deferred_binding_holds` / `CASES` / `_delete` / `TestNvRenderMutation._deleting` | exact |
| `.planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md` | doc (verdict ledger) | — | `.planning/milestones/v2.13-phases/58-clear-actions-recovery-and-answers-acted-on/58-REPRO.md` | exact |

`scripts/test_replay.py`: no planned edit. Its `_MUTANTS["member"]` anchor (686-702) must stay unique after the group-loop edit (see Pitfall list in RESEARCH §Pitfall 4). `05-state-all.md`, `05-state.md`, `_NEARBY_LINES`, `_nearby_changed`, `stable_hash` are NOT edited.

---

## Pattern Assignments

### `scripts/test_decision_continuity.py` (test, real-chain batch)

**Analog:** the same file. Every new fixture reuses its harness; nothing is stubbed.

**Imports / harness (lines 51-63)** — already present, reuse as is:
```python
import batch_card  # noqa: E402
import carry_state  # noqa: E402
import score  # noqa: E402
from test_carry_state import append_pass, e2e_gate  # noqa: E402
from test_score import GOLDEN_DIGEST  # noqa: E402
```
Harness functions to call (do not re-write): `base_file` (76), `next_cf` (163), `fresh` (193), `run_pass` (207), `decide_on` (247), `record_of` (256), `card_rows` / `card_text_full` / `card_text_compact` (270-284), `row_of` (287), `card_row` (295), `empty_state` (318), `pass1` (322), `_Base._current` (341).

**Scenario builder pattern — copy `far_twin_scenario` (961-984)** for `cr01_scenario` (two `return None` copies at 10 and 30, both reported at pass 1):
```python
def far_twin_scenario():
    """57-REVIEW-GAPS3.md, ... -> (s2, r2, s3, hA)."""
    L0 = base_file()
    L0[9] = L0[29] = "return None"
    s1, hA = pass1(L0, conf=STABLE_CONF)
    s2, r2 = run_pass(s1, L0, [fresh("bugs", 30, L0, TITLE_A, conf=100)], 2,
                      {F: [[33, 33]]})
    s3, _ = run_pass(s2, L0, [], 3, {F: []})
    return s2, r2, s3, hA
```
Docstring convention: cite the source finding (e.g. "57-REVIEW-GAPS4.md CR-01"), describe each pass, end with `-> (tuple)`. RESEARCH §Code Examples gives the `cr01_scenario(edit, quiet_first=False)` skeleton. `cr02_scenario`: copy `cross_lane_same_hash_scenario` (886-900) for the fresh `security` / `category="injection"` lead. `cr04_scenario`: copy the A-covered-by-B setup from `deferred_covered_sub_threshold_scenario` (1006-1016), with `kind="dismiss"` and pass 2 `{F: [[6, 6]]}`.

**Knob pattern for DEFR-01 — extend `deferred_covered_sub_threshold_scenario` (997-1024)**; it already forwards `**over` to pass 2 (`min_confidence=45` goes there). Add a keyword `member_conf=STABLE_CONF` used at line 1007:
```python
    a = fresh("bugs", 10, L0, TITLE_A, conf=STABLE_CONF)   # -> conf=member_conf
    ...
    s2, r2 = run_pass(s1, L1, [], 2, {F: [[12, 12]]}, recheck_requests=[req],
                      verdicts=[verdict], **over)
```
Keep the default equal to `STABLE_CONF` so the four `TestDeferredStaysOpen` tests (1505-1583) stay byte-identical.

**Re-ask assertion pattern — copy `TestPooledEvidence._assert_reasked` (1379-1392).** It asserts the state, cause, outstanding hash and gate together, which is the fix for RESEARCH Pitfall 5 (CR-02's gate alone is not evidence):
```python
    def _assert_reasked(self, state, hA, nearby_at=2):
        rec = self._current(state, hA)
        snap = rec["snapshot"]
        self.assertEqual(snap.get("nearby_at"), nearby_at,
                         "row snapshot has no owed nearby_at: %r" % snap)
        self.assertEqual(carry_state.decision_state(rec, state), "stale",
                         "snapshot %r" % snap)
        self.assertEqual(carry_state.stale_cause(rec, state), "nearby",
                         "snapshot %r" % snap)
        self.assertIn(hA, carry_state.finalize_counts(
            state, {})["outstanding_cw_hashes"], "snapshot %r" % snap)
        self.assertNotEqual(e2e_gate(state, {}), "write",
                            "snapshot %r" % snap)
        return rec
```
Class docstring convention (1372-1377): name the source finding and state "Expected on the unfixed scorer: … fail; the controls … pass."

**Control pattern (STALE-04) — copy `test_n1_far_edit_keeps_decision` (1917-1932)**: edit outside both windows (e.g. line 45), assert `decision_state == "current"` and `e2e_gate == "write"`.

**DEFR-01 assertion pattern — copy `TestDeferredStaysOpen.test_deferred_covered_member_below_threshold_stays_open` (1505-1526)** and `test_deferred_kept_open_row_shape` (1539-1553). The min_confidence variant changes only the `kept_open` prefix:
```python
        self.assertTrue(str(row.get("kept_open", "")).startswith(
            "sub-threshold"), "row %r" % row)          # -> "below-min-confidence"
        ...
        self.assertEqual(row["kept_open"], "sub-threshold; deferred-by: " + hB)
```
The dismiss counterpart copies `test_dismissed_covered_member_below_threshold_may_drop` (1528-1537).

**p4 rewrite (D-01/D-21)** — `test_p4_far_twin_latest_stamp_reaches_the_first_copy` (1453-1470) currently asserts `rows2[1]["snapshot"].get("nearby_at") == 2` and `_assert_reasked(s3, hA)`. Rewrite it to assert `decision_state == "current"` at pass 2 and pass 3 (RESEARCH §CR-03 note).

**Invariance rows (STALE-05) — copy `_inv_different_line_same_hash_cross_lane` (1646-1650)** and the `INVARIANCE_SCENARIOS` entry format (1683-1725):
```python
def _inv_different_line_same_hash_cross_lane(sec_conf, _sev):
    """CR-01 cross-lane: the lead marker is (row agent, row line)."""
    s2, _, hA = cross_lane_same_hash_scenario(sec_conf)
    row = row_of(s2, hA)
    return s2, hA, (row["agent"], row["line"])
...
    "different_line_same_hash_cross_lane": (
        _inv_different_line_same_hash_cross_lane,
        (("carried-leads", (60, "warning"), ("bugs", 12)),
         ("fresh-leads-same-band", (100, "warning"), ("security", 10))),
        _REASK),
```
Rules enforced by the coverage lock `test_guard_covers_every_scenario_the_phase_cares_about` (1772-1785): first permutation label must be `"carried-leads"`, at least 2 permutations, and the scenario name set is listed literally, so add the new names there too.

**Did-not-reproduce record (SA-02) — copy `DID_NOT_REPRODUCE` + `TestDidNotReproduceRecord` (1849-1910)**:
```python
_DROPPED = "did not reproduce; dropped — no code change"
DID_NOT_REPRODUCE = (
    {"id": "N1", "decision": "D-03",
     "scenario": "same-file edit outside the window (line 40), no shift; ...",
     "probe_result": "decision current; the only re-ask came from band ...",
     "disposition": _DROPPED},
```
and the completeness test asserts `set(row) == {"id", "scenario", "probe_result", "decision", "disposition"}` (1908-1910). A `REPRO_59` tuple should use the same keys (`decision` = the requirement/backlog id, e.g. `"DEFR-02"`), with reproduced rows naming their fixture test.

**Mutation-check pattern (score.py) — `TestPhase57Mutants._run_mutant` + `_ROW_TESTS` (2441-2497)**:
```python
    def _run_mutant(self, name, old, new):
        from unittest import mock
        from test_confirmed_fix import SCORE_PY, _mutant
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count(old), 1, "mutation target not unique")
        mod = _mutant(SCORE_PY, name, old, new)
        self.assertEqual(self._failures(), set())
        with mock.patch.object(score, "run", mod.run):
            return self._failures()
```
Each mutant test asserts which short prefixes trip AND which stay green (2510-2521 is the model):
```python
    def test_no_synthesized_entry_drops_the_deferred_member(self):
        failed = self._run_mutant(
            "score_d20_no_entry",
            "carried_obligations[id(m)] = _covered_entry(",
            "pass  # (")
        self.assertIn("test_deferred_", failed)
        self.assertNotIn("test_dismissed_", failed)
        self.assertNotIn("test_s1_", failed)
```
Prefix rule: `_failures` keys failures by `name[:name.index("_", len("test_")) + 1]`, so new test names need a distinct short prefix (e.g. `test_cr01_`, `test_cr02_`, `test_cr04_`, `test_dmc_`). Add every new fixture to `_ROW_TESTS`.

Mutants this phase must re-anchor (RESEARCH Pitfall 4): `test_nearby_judged_at_the_lead_only_loses_the_other_copy` (2596-2610, anchor is the `row_nearby` line), `test_no_synthesized_entry_drops_the_deferred_member` (2510; anchor `carried_obligations[id(m)] = _covered_entry(` becomes non-unique once the min_confidence branch calls it, so lengthen the anchor), `test_prior_rank_first_wins_loses_the_latest_stamp` (2626) and `test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp` (2423) both `assertIn("test_p4_")`, so re-point them at a CR-01/CR-02 fixture. `test_kept_open_covered_row_without_carried_is_not_stamped` (2523-2534) becomes decorative if `carried=bool(entry.get("covered")) or bool(same)` (Pitfall 3); retire or rewrite it rather than leave it.

**Mutation-check pattern (carry_state.py)** — no mutant of `_check_state` exists in this file yet. Build on the same `_mutant` helper; `test_confirmed_fix.py` already defines the path constant (line 53) and mutates carry_state at 791-797:
```python
CARRY_STATE_PY = os.path.join(HERE, "carry_state.py")   # test_confirmed_fix.py:53
...
        mod = _mutant(CARRY_STATE_PY, "cs_m1",
                      "file not in commit.get(\"files\")", "False")
```
Patch the reader with `mock.patch.object(carry_state, "_check_state", mod._check_state)` (precedent for patching carry_state functions: `test_carry_state.py:815` patches `decided`, `:1866` patches `decision_state`). batch_card resolves `_check_state` through carry_state's module global, so one patch covers the card path.

**Function-level mutant inside a test (not whole-run) — `test_nearby_window_upper_bound_dropped_misses_offset_five` (2339-2359)**: shows the `src.count(old) == 1` uniqueness check, baseline-green check, then `mock.patch.object(score, "_nearby_changed", mod._nearby_changed)`.

---

### `scripts/score.py` `_kept_open_rows` (service, transform) — CR-01 + multi-pass

**Analog:** the group loop's pooled-prior block in the same file, lines 2716-2743:
```python
        same_hash = carried_by_hash.get(survivor["stable_hash"], ())
        own = survivor.pop("snapshot", None)
        candidates = [
            o["snapshot"] for _, o in same_hash
            if o is not None
            and o.get("stable_hash") == survivor["stable_hash"]
            and isinstance(o.get("snapshot"), dict)]
        if isinstance(own, dict) and best_member.get("stable_hash") == survivor["stable_hash"]:
            candidates.append(own)
        prior = _pooled_prior(candidates)
        if prior is not None:
            survivor["snapshot"] = prior
        row_carried = bool(same_hash)
        row_nearby = _any_nearby([survivor] + [r for r, _ in same_hash], changed_line_ranges)
```
**Current code to change** (412-489): signature `_kept_open_rows(dropped, kept, pass_number, carried_obligations, members_of, changed_line_ranges)`; hash-level dedup at 452 (`visible = {s.get("stable_hash") for s in kept}`) and 478-479 (`if obl["stable_hash"] in visible: continue`); own-line-only nearby at 471-474:
```python
        row["snapshot"] = obl.get("snapshot")
        row_nearby = _nearby_changed(row, changed_line_ranges)
        row["snapshot"] = _snapshot_for(row, pass_number, nearby=row_nearby,
                                        carried=bool(entry.get("covered")))
```
Call site 2834-2835 gains the `carried_by_hash` argument (built at 2455). Per-occurrence dedup uses the existing `_finding_identity` (already used in the same function for `kept_idents`). Docstring convention: long prose docstring ending "Pure; never raises." — update it, as the group loop's comment cites D-19 / the review finding.

### `scripts/score.py` group-loop `row_nearby` (service, transform) — D-21 first pass + CR-04

**Analog:** line 2743 (above) plus `_any_nearby` (607-610) and `_CARRIED_STATUSES` (374). `scored_members` tuples are `(c, m, _, _, _)` (see 2793 `{id(m): c for c, m, _, _, _ in scored_members}`). Keep the `test_replay._MUTANTS["member"]` anchor text `"                    changed_line_ranges)\n            members.append(ref)\n            kept_by_ident[ident] = ref\n"` unique.

### `scripts/score.py` min_confidence branch (service, filter) — DEFR-01

**Analog:** the threshold-drop D-20 synthesis, lines 2808-2819:
```python
            for m in sources:
                if id(m) in deferred_covered and id(m) not in carried_obligations:
                    carried_obligations[id(m)] = _covered_entry(m, deferred_covered[id(m)], capped_by_id[id(m)])
            dropped.extend(
                (m, ("sub-threshold; deferred-by: " + deferred_covered[id(m)]["covering"])
                 if id(m) in deferred_covered else "sub-threshold")
                for m in sources if id(m) in carried_obligations)
```
**Site to change** (2507-2522):
```python
                filtered.append({ ... "reason": "below-min-confidence", })
                if id(m) in carried_obligations:
                    dropped.append((m, "below-min-confidence"))
```
`_covered_entry(m, cov, capped)` is at 397-409. The `filtered[]` reason string `"below-min-confidence"` must stay unchanged (asserted at test_decision_continuity.py:1433 and 1666). If the D-06 note needs the number, put it in the `kept_open` reason (e.g. `"below-min-confidence 45; deferred-by: <h>"`); `min_confidence` is in scope here.

### `scripts/score.py` `_snapshot_for` (utility, transform) — spot data for D-04/D-05

**Analog:** the `prior_nearby` handling in the same function, 354-369:
```python
    prior_nearby = _as_line(prior.get("nearby_at")) if isinstance(prior, dict) else None
    if (isinstance(prior, dict) and _as_line(prior.get("at_pass")) is not None
            and all(k in prior and prior[k] == cur[k]
                    for k in ("file", "line", "canonical_line_content", "band"))):
        kept = {"at_pass": prior["at_pass"], "file": cur["file"], "line": cur["line"],
                "canonical_line_content": cur["canonical_line_content"],
                "band": cur["band"]}
        if prior_nearby is not None:
            kept["nearby_at"] = prior_nearby
        return kept
    if prior_nearby is not None:
        cur["nearby_at"] = prior_nearby
    return cur
```
Any new key must be carried on both the keep and refresh branches like this (Pitfall 8) and emitted only when a non-own spot fired, because `test_split_row_snapshot_is_the_split_pass_shape` (test_decision_continuity.py:2110-2125) locks the exact key set `{"at_pass", "file", "line", "canonical_line_content", "band", "nearby_at"}`. Use `_as_line` for int validation. Agents can't forge it: the ingress scrub strips `snapshot` (2291-2296).

---

### `scripts/carry_state.py` `_check_state` (service, single read boundary) — CR-02

**Analog / site:** lines 308-348. The first-wins loop to extend:
```python
    records = []
    seen = set()
    # Rows first, then member records in array order: a kept-open row whose own
    # sidecar repeats its hash is ONE obligation, represented by the row.
    for rec in rows + sidecars:
        if rec["stable_hash"] in seen:
            continue
        seen.add(rec["stable_hash"])
        records.append(rec)
    return last, records, None
```
Sidecar construction (322-336) builds a new dict per sidecar but rows are the state's own dicts, so the merge must copy (`dict(rec, snapshot=dict(snap, nearby_at=...))`), never mutate. Merge only `nearby_at` (and derived spot data), never `line`/`band`/`at_pass` (they feed `pending` and the band compare). `nearby_at` well-formedness: `_evidence_of` (492-511) reads it raw from the snapshot; validate as int (non-bool) the way score.py `_as_line` does. The comparator `decision_state` (905: `if evidence.get("nearby_at") != current.get("nearby_at"): return "stale"`) and `stale_cause` (944-945) stay unchanged. Return-shape convention: `(last, records, None)` or `(None, None, reason)` with fixed reason constants.

---

### `scripts/batch_card.py` `_same_hash_stale` / `_stale_suffix` (component, transform)

**Analog for extra tag fields:** the `joined` branch at the end of `_same_hash_stale` (232-237):
```python
    if cause == "joined":
        # Both values come from carry_state, the same functions the reopen
        # test reads, so the card and the comparator cannot disagree.
        tag["covered"] = carry_state.covered_count(record, state)
        tag["joined"] = carry_state.newcomer_lanes(record, state)
    return tag
```
Add `spot_line` / `spot_kind` / `other_spots` the same way under `cause == "nearby"`, read from carry_state (not recomputed in batch_card).

**Analog for the suffix:** the `nearby` branch of `_stale_suffix` (522-527):
```python
    if cause == "nearby":
        return (" — code next to it changed since your decision on pass %s"
                % at_pass if compact else
                " — code next to it changed since your decision on pass "
                "%s %s" % (at_pass, _was(stale)))
```
Same-spot reopens must keep this string byte-for-byte (locked by test_decision_continuity.py:1807-1810, 2183-2185 and test_card_text.py `suffixes()["nearby"]`). New text goes through `_one_line(...)` for any non-int value; spot values are ints. The `severity`+`gained` branch (528-536) shows a plural/count pattern to copy for "and N other spots".

**D-06 kept_open note:** batch_card has no `kept_open` read today; no direct analog. Follow `_suffixes(row, compact)` ordering (starts ~553: absorbed, pending, stale) and parse the number from the reason with a strict regex (fail soft: render without the number).

---

### `phases/shared/90-finalize.md` (line 109) and `phases/review/50-fix-loop.md` (line 62) (config, prose)

**Analog:** the existing nearby entry, 90-finalize.md:109:
```
  - stale nearby (D-02, `stale.cause == "nearby"`) — ` — code next to it changed since your decision on pass {{stale.at_pass}} (was: {{dismissed|deferred}} — {{stale.reason}})`
```
and the same template inline in 50-fix-loop.md:62 (a single long `Suffixes, in this order …` paragraph; add the new form(s) inside that paragraph, after `stale nearby`). Template variables use `{{stale.<field>}}` so `TestProseMatchesHelper.fill` can substitute them.

---

### `scripts/test_card_text.py` `TestProseMatchesHelper` (test, prose-lock)

**Analog:** `suffixes()` entries + state builders (lines 65-70, 385-436):
```python
def nearby_stale_state():
    decided = dismiss(ba_state(), HA, reason="Guarded")
    s = copy.deepcopy(decided)
    s["passes"] = ba_state(a_snapshot=dict(snap(1, line=11),
                                           nearby_at=2))["passes"]
    return s
...
            "nearby": (nearby_stale_state(),
                       " — code next to it changed since your decision on "
                       "pass {{stale.at_pass}} (was: {{dismissed|deferred}} "
                       "— {{stale.reason}})",
                       {"stale.at_pass": 2, "dismissed|deferred":
                        "dismissed", "stale.reason": "Guarded"}),
```
`test_documented_suffixes_render` asserts each template is in BOTH `FIX_LOOP_MD` and `FINALIZE_MD` and that the filled template appears in the rendered `card_text` for both modes. Each new suffix (copy spot, grouped spot, N other spots, D-06 note) gets one `suffixes()` entry plus a hand-built state builder in the `nearby_stale_state` style. The hand-built snapshot must match what score.py really emits (the split-pass shape lock at test_decision_continuity.py:2110 exists for exactly this producer/consumer drift).

---

### SA-02 prose pin on `phases/review/05-state-all.md` (test, prose-lock + deleting mutant)

**Analog:** `test_nv_render.py` phrase-lock machinery:
```python
def norm(text):                                   # 31
    return re.sub(r"\s+", " ", text)

def _all_in(text, phrases):                       # 40
    flat = norm(text)
    return all(norm(p) in flat for p in phrases)

def _section(text, start, end):                   # 178
    """The text from `start` up to the next `end` ("" when `start` is gone)."""

DEFERRED_BINDING_PHRASES = (                      # 241-255
    "Phase 0.5 also binds `$DEFERRED_HASHES`",
    ...
)
def deferred_binding_holds(text):
    return _all_in(_section(text, STATE_START, STATE_END),
                   DEFERRED_BINDING_PHRASES)

def _delete(text, phrase):                        # 330
    """Remove every occurrence of `phrase`, tolerating hard wraps."""
    pattern = r"\s+".join(re.escape(w) for w in phrase.split())
    return re.sub(pattern, "", text)
```
and the mutation half (`TestNvRenderMutation`, after 380):
```python
    def _assert_trips(self, pred, original, mutant):
        self.assertNotEqual(mutant, original, "mutant did not change the text")
        self.assertTrue(pred(original))
        self.assertFalse(pred(mutant))
```
Phrases to lock (verbatim in 05-state-all.md (ii), ~line 32): ``"`$CARRYFORWARD = []`"``, `"SKIP Phase 0.5 steps 2-5"`, `"EVEN IF a `by-mode/all/<scope-hash>.json` file already exists"`. Plus the half that makes the drop claim true: 05-state.md binds `$DEFERRED_HASHES` inside step 2 (already locked by `deferred_binding_holds`, whose section ends at `"\n3. Narrow diff"`). Either add a `CASES` row in test_nv_render.py (the predicate + `_deleting` mutant come for free) or import these helpers from `test_nv_render` the way test_decision_continuity.py:2036-2054 already does (`import test_nv_render` … `test_nv_render._read(...)`, `test_nv_render.norm(...)`).

---

### `.planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md` (doc, ledger)

**Analog:** `.planning/milestones/v2.13-phases/58-clear-actions-recovery-and-answers-acted-on/58-REPRO.md` (436 lines). Header block and per-shape section:
```
# Phase 58 — Reproduction verdicts

- **Phase:** …
- **Date:** …
- **HEAD when recorded:** `<sha>` (branch `feat/v2.13-phase-58`; last code commit …)
- **Scope of evidence:** no live or paid run was performed …
- **Rule applied:** reproduce first (D-14). A failure that reproduced is mapped to the plan that fixed it. A path that does not reproduce is recorded and dropped.

## V1 — <shape> (<REQ-IDs>)

**Verdict: REPRODUCED before the phase → fixed by <plans>.**
**Failure as the owner saw it.** …
**Fixture.** …
**Commands and output** …
```
One section per shape (CR-01, CR-01 multi-pass, CR-02, CR-04, DEFR-01@45, SA-02), each with the red/green SHAs. `.planning/` is gitignored: commit with `git add -f` (as 089f2fb / 62ea77e did).

---

## Shared Patterns

### Pool over the existing index, never a new one
**Source:** `scripts/score.py` `_carried_index` (581-604), `_any_nearby` (607-610), `_prior_rank` / `_pooled_prior` (613-633)
**Apply to:** every score.py producer edit (kept-open rows, group-loop `row_nearby`, spots)
Every prior candidate passes the hash gate `o.get("stable_hash") == <row hash>` and `isinstance(o.get("snapshot"), dict)` (2728-2731). That gate is itself mutation-locked (`test_seed_without_hash_equality_inherits_a_foreign_stamp`, 2550), so keep its anchor text unique.

### Never-raise, pure helpers
**Source:** every score.py helper docstring ends "Pure; never raises." with `isinstance` guards (`_snapshot_for` 306-369, `_prior_rank` 613-624)
**Apply to:** score.py and carry_state.py edits. Snapshots may be None or non-dict; validate ints with `_as_line` (score.py) and reject bools.

### Real-chain fixture + mutant per fix
**Source:** `TestPooledEvidence` (1371-1470) + `TestPhase57Mutants._run_mutant` (2485-2497)
**Apply to:** CR-01, CR-01 multi-pass, CR-02, CR-04, DEFR-01. Each mutant test asserts what trips (`assertIn`) and what stays green (`assertNotIn`), checks anchor uniqueness (`src.count(old) == 1`) and a green baseline.

### Helper-renders / prose-documents / test-binds
**Source:** `batch_card._stale_suffix` ↔ `90-finalize.md:109` + `50-fix-loop.md:62` ↔ `test_card_text.TestProseMatchesHelper`
**Apply to:** every new card wording (D-04, D-05, D-06). Change all three in one plan.

### Single writer for `decisions`
**Source:** `carry_state.py record_decisions` (1096-1160), which reads records through `_check_state`
**Apply to:** the `_check_state` merge (read-side copy only) and every score.py change (no `decisions` writes). Because the writer reads the same merged view, stored evidence and later comparison agree.

## No Analog Found

| File / element | Role | Data Flow | Reason |
|----------------|------|-----------|--------|
| batch_card `kept_open` note (D-06) | component | transform | batch_card has never read `kept_open`. Use the `_stale_suffix` / `_suffixes` structure and the RESEARCH Pattern 5 design. |
| carry_state `_check_state` mutant inside test_decision_continuity.py | test | — | No `_check_state` mutant exists. Combine `test_confirmed_fix._mutant(CARRY_STATE_PY, …)` with `mock.patch.object(carry_state, "_check_state", …)` as shown above. |

## Conventions

Convention derivation skipped (`no-app-files`: the bm derivation tool only inspects JS/TS, and this phase is stdlib Python plus Markdown prose). Observed local style in `plugins/vibe-check/scripts/`, to match:

| Axis | Observed style | Status |
|------|----------------|--------|
| File-name casing | `snake_case.py`; tests are `test_<module>.py` beside the module | named contract (local) |
| Identifier casing | `snake_case` functions, leading `_` for module-private helpers, `UPPER_SNAKE` module constants (`_NEARBY_LINES`, `STABLE_CONF`) | named contract (local) |
| Export style | module-level functions; tests import sibling modules after `sys.path.insert(0, HERE)` with `# noqa: E402` | named contract (local) |
| Import style | stdlib only; test helpers imported from sibling test modules (`from test_carry_state import append_pass, e2e_gate`, `from test_confirmed_fix import SCORE_PY, _mutant` imported inside the test method) | named contract (local) |

**Contested hotspots (author's choice):** the repo-wide prototype is the CJS<->SDK dual resolver (`bin/lib/**` CJS `module.exports`/`require` vs `sdk/src/**` ESM `export`/`import`), where each half is consistent in its own directory and only contested repo-wide. That split does not exist in this repo. Here, match the scripts directory's local style above. Tests are unittest classes run by bare `pytest` (not `python3 -m pytest`).

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/` (score.py, carry_state.py, batch_card.py, test_decision_continuity.py, test_card_text.py, test_confirmed_fix.py, test_nv_render.py, test_replay.py, test_carry_state.py, test_batch_card.py), `plugins/vibe-check/phases/{review,shared}/`, `.planning/milestones/v2.13-phases/58-*/58-REPRO.md`
**Files scanned:** 14
**Pattern extraction date:** 2026-10-28
