# Phase 57: Decision continuity within closure - Pattern Map

**Mapped:** 2026-10-25
**Files analyzed:** 15 (3 scripts, 3 prose/template, 7 tests incl. 1 optional new module, 2 data/schema with no change expected)
**Analogs found:** 15 / 15. Every file extends an existing one. The main analogs are Phase 53's NV relocation and `_NV_EVIDENCE_KEYS` (for the line-free compare), Phase 56's `_independent_trigger` (for the nearby window), and Phase 46's `members[].obligation` (for coverage).

All paths are relative to `plugins/vibe-check/` unless they start with `.planning/`. Line numbers are from HEAD `032c4ac`, and they differ from the RESEARCH line numbers taken at 9be39a8 wherever both are given; use these. The Phase 56 map's import-ban, prose-lock, mutant and golden-digest patterns all still hold, and they are restated under Shared Patterns with current line numbers.

**D-05 refinement (owner ruling, binding):** a band rise reopens a decision only when a reviewer lane that was absent at decision time now reports the finding. The card names that lane. A rise from the persistence bonus or the lone-lane cap lifting, with no new lane, keeps the decision. That rules out RESEARCH Open Question 1 option (a). Option (b) needs `attribution` saved on the decision record (see carry_state below).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality | Fix (RESEARCH) |
|---|---|---|---|---|---|
| `scripts/carry_state.py` (modify) | service (single closure/decision rule + single writer) | CRUD read + one write family | its own `decision_state` :457-484, `stale_cause` :487-504, `_NV_EVIDENCE_KEYS` :393, `record_decisions` :621-657, `_check_state` :256-295 | exact | F2, F4, F5, new `decided` read subcommand (F1) |
| `scripts/score.py` (modify) | service (pure judge) | transform | `_independent_trigger` :1325-1341, `_snapshot_for` :302-330, `_refreshed_obligation` :336-350, `_kept_open_rows` :353-425, member loop :2546-2559, ingress scrub :2138-2141 | exact | F3, F6 |
| `scripts/batch_card.py` (modify) | utility (card renderer) | transform (state to rows/text) | `_same_hash_stale` :162-181, `_suffixes` :433-461, `lead_closed` note :490-491, `successor_links` :349-398 | exact | F7, D-10 note |
| `phases/review/30-collect-score.md` (modify) | orchestration prose | HEAD read to envelope | "Carried Needs-verification records (Phase 53 …)" block :44-55 | exact (generalize NV to decided) | F1 |
| `phases/review/05-state.md` (modify) | orchestration prose | state to env vars | `$TOUCHED_PATHS` bullet :62 and the `decisions` bullet :63 | role-match | F1 bind `$DECIDED_HASHES` |
| `phases/shared/90-finalize.md` (modify) | render prose (contract) | read state | "Closed =" definition :26, stale suffix bullets :101-106 | exact | F2/F4/F5/F7 wording |
| `templates/scoring.md` (modify, one sentence) | template | n/a | :122 "A carried row keeps its stored `stable_hash` verbatim" | exact | F1 (the claim must stay true for decided ordinary leads) |
| `scripts/test_carry_state.py` (modify) | test | CRUD read | `TestDecisionEvidence` :1230, fixtures `line_move_state` :1174 / `band_change_state` :1169, contrast mutants :1390-1456, `ROLLBACK_FIXTURES` :1467, `append_pass`/`e2e_gate`/`decide` :1719-1826 | exact | R1/R3b/R4/R6 RED legs |
| `scripts/test_batch_card.py` (modify) | test | transform | `test_rows_stale_decision_present_with_tag` :129, `test_rows_stale_line_move_cause_code` :143 | exact | F7 tags |
| `scripts/test_card_text.py` (modify) | test (exact wording) | transform | `test_severity_stale_suffix_exact` / `test_code_stale_suffix_exact` :89-98 | exact | F7 wording |
| `scripts/test_score.py` (modify) | test | score pipeline | `_ko_find` :5620, `_ko_next_cf` :5640, `_hl_env` :3792, `TestKeptOpen`; `GOLDEN_DIGEST` :43 | exact | F3/F6 score legs |
| `scripts/test_nv_render.py` (modify) | test (prose lock) | n/a | `RELOCATION_PHRASES` :111-118, `nv_relocation_holds` :139 | exact, **conflict** (see below) | F1 prose lock |
| `scripts/test_finalize_card.py` (modify) | test (prose lock) | n/a | `check_*` predicates + `LockCase.assert_holds` :275-291 | exact | 90-finalize wording locks |
| (recommended) new `scripts/test_decision_continuity.py` | test (multi-pass reproduction + mutants) | real `score.run` to `append_pass` to `carry_state`/`batch_card` | `scripts/test_verified_fixes.py` module layout (docstring contract, `TestIndependentRouteMutants` :1366) | exact | R1-R7 RED fixtures, N1-N6 "did not reproduce" notes |
| `scripts/fixtures/future-schema.json` / `scripts/state_shape.py` | config / utility | n/a | `_purpose` + `_rollback.phase56_added` :2, :36-40 | **expected: no change** (snapshot inner keys and decision values are not validated); touch only if a new FINDING key is added | — |

## Pattern Assignments

### `scripts/carry_state.py` (service, CRUD read + single writer)

**Analog:** the same file. CONTEXT says "extend here rather than adding a second comparator". Import ban: `{json, os, sys}` exactly (`test_carry_state.py:713-728`, `TestImportSet`), and `os` may be used only for `isfile`. carry_state **cannot import score**, so any band ranking has to be mirrored, with a cross-module equality test.

**Evidence key sets, the template for F2** (lines 383-393). NV already drops `line`. The ordinary compare set should get the same treatment while `line` stays stored:
```python
EVIDENCE_KEYS = ("file", "line", "canonical_line_content", "band")
...
_NV_EVIDENCE_KEYS = ("file", "canonical_line_content", "band", "current_code")
```
Keep `EVIDENCE_KEYS` as the stored/written set. `_full_evidence` (:452-454) requires all four keys, which keeps legacy fail-closed handling intact. Add a separate compare tuple, for example `_ORDINARY_COMPARE = ("file", "canonical_line_content")`, and handle band through the direction rule. Compare `nearby_at` with `evidence.get(k) == current.get(k)` so that legacy evidence without the key reads None == None. Do NOT add `nearby_at` to `_full_evidence`, because that would make every pre-57 record stale.

**The comparator to extend** (lines 457-484, `decision_state`):
```python
    h = record["stable_hash"]
    if h in state.get("medium_acknowledgments", {}):
        return "current"
    decisions = state.get("decisions", {})
    if h not in decisions:
        return None
    decision = decisions[h]
    if not isinstance(decision, dict) or "evidence" not in decision:
        return "current"
    evidence = decision["evidence"]
    if not _full_evidence(evidence):
        return "stale"
    keys = _evidence_keys(evidence, record)
    current = _evidence_of(record, nv=keys is _NV_EVIDENCE_KEYS)
    if all(k in evidence and evidence[k] == current[k] for k in keys):
        return "current"
    return "stale"
```
The F4 insertion point comes after the code keys match. For an ordinary record whose band differs: a lower rank returns `"current"` (D-06). A higher rank returns `"stale"` only when the record's current `attribution` holds a lane that the decision's saved `attribution` lacks (D-05 refinement). A legacy decision without saved `attribution` falls back to "any rise reopens", so the failure direction is "ask". The NV branch stays unchanged (D-04). The rank mirror `{"critical": 4, "warning": 3, "medium": 2, "low": 1}` comes from `score._BAND_SEVERITY` (`score.py:700`). Pin it with an equality test against `score._BAND_SEVERITY`, minus the `None` key.

**Cause classification to extend** (lines 487-504, `stale_cause`). Today it returns `"severity"` | `"code"`, and the `same` tuple names the ordinary code keys including `line`:
```python
    same = (("file", "canonical_line_content", "current_code")
            if keys is _NV_EVIDENCE_KEYS
            else ("file", "line", "canonical_line_content"))
    if all(k in evidence and evidence[k] == current[k] for k in same):
        return "severity"
    return "code"
```
New causes per RESEARCH Pattern 6: `"nearby"` (code matches, `nearby_at` differs), `"severity"` (now only a qualifying rise), and `"joined"` (D-08 newcomer). Drop `line` from the ordinary `same` tuple together with the compare change. `batch_card._same_hash_stale` forwards whatever this returns, so a rise also needs a way to surface the lanes it gained, for example a sibling helper that returns the gained lanes so the card can name them. Never put a lane, title or hash into REASONS.

**`_evidence_of`** (lines 428-441). Today it builds `{k: source.get(k) for k in EVIDENCE_KEYS}` from the snapshot, or from the record when no snapshot exists. Add `nearby_at` from the snapshot here, so that `record_decisions` stores it (`evidence` is `_evidence_of(by_hash[h])`) and `decision_state` reads it. Exactly one place defines the evidence.

**Single writer for F5 and the D-05 refinement** (lines 621-657, `record_decisions`):
```python
        record = {
            "decision": entry["decision"],
            "reason": entry["reason"],
            "at_pass": payload["at_pass"],
            "band": by_hash[h]["band"],
            "evidence": json.loads(json.dumps(_evidence_of(by_hash[h]))),
        }
        if isinstance(prior, dict):
            hist = ([{k: v for k, v in prior.items() if k != "history"}]
                    + list(prior.get("history") or []))
            record = dict(record, history=hist)
```
Add `covers` and `attribution` alongside `evidence`. Both are derived from the STATE record (`by_hash[h]`, and for a lead, its `members`), never from the payload. `_DECISION_ENTRY_KEYS = ("stable_hash", "decision", "reason")` (:590) stays exact, so the owner payload can never inject them (RESEARCH Security V5). `covers` holds the `(agent, file, title)` triples of the lead plus every member at decision time (RESEARCH Pattern 4). Lists are JSON-safe; tuples are not, so store them as lists. Never rewrite an older record. History already preserves superseded ones.

**Record enumeration for R4/R6 coverage** (lines 256-295, `_check_state`). Sidecars are built only from members that carry an `obligation`. That is why a newcomer member (R4) is not a record:
```python
        for m, obl in obligations:
            sidecars.append({
                "stable_hash": obl["stable_hash"],
                "band": obl["band"],
                "file": m.get("file"),
                "line": m.get("line"),
                "title": m.get("title"),
                "agent": m.get("agent"),
                ...
                "absorbed_into": f["stable_hash"],
            })
```
The `(file, title, agent)` fields `covers` needs are already copied onto every sidecar, and `members` stays available on the row for the newcomer check. Do not add newcomers as records (they have no hash). Instead, the decided ROW's `decision_state` reopens with cause `"joined"` when one of its `members` lacks an obligation and its identity is not in `covers` (RESEARCH Open Question 3, recommended).

**New read subcommand `decided` (F1)**. Copy the `pending` shape (lines 563-587: `_check_state`, iterate records, sorted output, None when malformed) and its CLI wiring: `SUBCOMMANDS` :121, `_FLAGS_BY_SUBCOMMAND` :127-132 (`"decided": ((), ())`), `USAGE` :134, and the `run` dispatch :866-869 (`elif sub == "pending": result = pending(state)`). Output: the sorted hashes whose `decision_state` is `"current"`, for `05-state.md` to bind as `$DECIDED_HASHES`. If a member is relocated, the output must name member obligation hashes as well as row hashes, because the orchestrator relocates both.

**Docstring and rollback** (lines 20-83). Rewrite the "WHAT CLOSES" sentences that D-01/D-06/D-09 make false: "A same-hash band change or line move re-opens the finding" (:38-39), and "Closure is evaluated per record and is never inherited from a lead." (:61-62). Name the ONE new inheritance path, coverage recorded at decision time. Add a ROLLBACK note covering `covers`, `attribution` and `nearby_at` (RESEARCH "Persisted State Compatibility": a pre-57 reader re-asks, which fails toward asking).

---

### `scripts/score.py` (pure judge, transform)

**Hard constraint:** `TestImportSet.ALLOWED = {"json", "hashlib", "re", "sys"}`, and `os`, `pathlib`, `open` are forbidden (`test_score.py:1476-1500`). `stable_hash` (:428) and `_canonical_for_hash` (:462) do not change. `GOLDEN_DIGEST` `7a516d01…` (`test_score.py:43`).

**Window helper to split out for F3** (lines 1325-1341):
```python
def _independent_trigger(record, touched, changed_line_ranges):
    file = record.get("file")
    if not _nonempty_str(file):
        return False
    if file in touched or any(_is_associated_test(p, file) for p in touched):
        return True
    line = _as_line(record.get("line"))
    if line is None or not isinstance(changed_line_ranges, dict):
        return False
    ranges = changed_line_ranges.get(file, [])
    return any(_line_in_ranges(n, ranges) for n in range(line, line + _NEARBY_LINES + 1))
```
Extract the last four statements into `_nearby_changed(record, changed_line_ranges)`, then have `_independent_trigger` call it. Its behaviour must stay byte-for-byte equivalent: the existing m12 mutant target `'status == "persisted" and not _independent_trigger('` (`test_verified_fixes.py:1416-1419`) and `TestReviewFix56` must stay green. Keep the literal 5-beneath window (`_NEARBY_LINES = 5`, :173). It is documented in the comment block :160-170.

**Snapshot writer, keep/refresh rule** (lines 302-330, `_snapshot_for`):
```python
    prior = row.get("snapshot")
    if (isinstance(prior, dict) and _as_line(prior.get("at_pass")) is not None
            and all(k in prior and prior[k] == cur[k]
                    for k in ("file", "line", "canonical_line_content", "band"))):
        return {"at_pass": prior["at_pass"], "file": cur["file"], "line": cur["line"],
                "canonical_line_content": cur["canonical_line_content"],
                "band": cur["band"]}
    return cur
```
Add `nearby_at`. When `_nearby_changed` is true this pass, write `nearby_at = pass_number` and a fresh `at_pass`. Otherwise carry the prior `nearby_at` forward on BOTH branches (keep and refresh). Absent stays absent. RESEARCH Anti-pattern: if the carry-forward is dropped, the finding is re-asked forever. `_snapshot_for` has no access to `changed_line_ranges` today, so thread a flag in, for example `_snapshot_for(row, pass_number, nearby=False)`, rather than handing it the ranges.

**All three snapshot writers must thread it** (RESEARCH Pitfall 5, one test plus one mutant each):
- survivor: `survivor["snapshot"] = _snapshot_for(survivor, pass_number)` (:2597)
- kept-open row: `row["snapshot"] = obl.get("snapshot"); row["snapshot"] = _snapshot_for(row, pass_number)` (:403-404)
- obligation member: `_refreshed_obligation` builds `basis = {"file", "line", "canonical_line_content", "band": obl.get("band"), "snapshot": obl.get("snapshot")}` (:347-350)

**Ingress scrub, security** (lines 2138-2141). Add `nearby_at`? No: it lives inside `snapshot`, and `snapshot` is already scrubbed from fresh findings:
```python
    findings = [{k: v for k, v in f.items()
                 if k not in ("status", "members", "snapshot", "resolution", "kept_open",
                              "recheck_settled")}
                for f in findings]
```
Because `nearby_at` is nested in `snapshot`, a fresh agent finding cannot forge it. Carryforward entries keep their snapshot by design (the comment at :2133-2137). Add a test that proves a forged `snapshot.nearby_at` on a fresh finding is dropped, plus a mutant that removes `"snapshot"` from the tuple. If the planner instead makes `nearby_at` a top-level finding key, it must go into this tuple, `FINDING_OPTIONAL_KEYS` (:250), `_MEMBER_EXCLUDED_KEYS` (:269) and `future-schema.json` `finding_optional` + `_rollback.phase57_added`. That costs more, so recommend nesting it.

**Member dedup that drops a carried obligation, F6 / R5** (lines 2546-2559):
```python
        members = []
        seen = set()
        for _, m, _, _, _ in scored_members:
            ident = _finding_identity(m)
            if ident in seen:
                continue
            seen.add(ident)
            ref = _member_ref(m)
            if m is not best_member and id(m) in carried_obligations:
                ref["obligation"] = _refreshed_obligation(
                    carried_obligations[id(m)]["obligation"], m, pass_number)
            members.append(ref)
```
Fix: keep a map `ident -> ref`. When `ident in seen` and `id(m) in carried_obligations` and the kept ref has no `obligation`, attach the skipped record's obligation to the kept ref, unless that kept ref is the lead's own record with the same hash (RESEARCH Pattern 5). Mutant target: the new attach line. This is the Phase-46 accepted residual (`46-CONTEXT.md:136`), now in scope because R5 reproduces.

**Survivor re-hash, context for R1a** (lines 2533-2538):
```python
        survivor["stable_hash"] = stable_hash(
            survivor.get("file", ""),
            best_decision["canonical_for_hash"],
            survivor.get("title", ""),
        )
```
No code change here. F1 relocation makes `canonical_for_hash` equal the stored canonical, so the recomputed hash equals the stored one. The R1a fixture must assert `rec["stable_hash"] == hA` after the shift.

---

### `scripts/batch_card.py` (card renderer, transform)

**Stale tag builder** (lines 162-181, `_same_hash_stale`). It forwards `carry_state.stale_cause(record, state)` into `"cause"`. Add fields for the new causes here, for example `"gained": [lanes]` for a qualifying rise. Keep the existing seven keys in the dict, since `test_batch_card.py:136-139` asserts the whole dict for `severity`. Update that assertion deliberately if the shape grows.

**Suffix wording, F7** (lines 433-461):
```python
    stale = row.get("stale")
    if isinstance(stale, dict):
        at_pass = stale.get("at_pass")
        if stale.get("cause") == "severity":
            out.append(
                " — severity changed since your decision on pass %s" % at_pass
                if compact else
                " — severity changed (%s → %s) since your decision on pass "
                "%s %s" % (_one_line(stale.get("was_band")) or "?",
                           _one_line(row.get("band")), at_pass, _was(stale)))
        else:
            out.append(
                " — code changed since your decision on pass %s" % at_pass
                if compact else
                " — code changed since your decision on pass %s %s"
                % (at_pass, _was(stale)))
```
Add `elif` branches for `nearby`, a qualifying severity rise with the lane(s) named, and `joined` (RESEARCH Pattern 6 strings). Every branch needs a compact form, and every interpolated value goes through `_one_line`, because lane names, titles and reasons are DATA. Keep the `(was: … — reason)` tail via `_was` (:427-430). The "severity changed" branch becomes "severity rose". Under the new rules only a rise can be stale, so decide whether to rename the phrase. If it is renamed, update `test_card_text.py:89-93` and `90-finalize.md:104` in the same commit.

**D-10 row note analog** (lines 490-491). An existing row-level note already exists:
```python
    if row.get("lead_closed") is True:
        first += " (your earlier decision on this row stays)"
```
The D-10 note ("1 finding here already dismissed (your reason: …)") goes in the same place. It is set by `_row` (:184-206) from the covered members' decisions and rendered by `_row_lines`. Reasons go through `_one_line` and are cut to fit the compact budget.

**Successor link, reuse only** (lines 349-398). It already links an edited (re-hashed) finding to its orphaned decision by `(file, title)`, as annotation only. After F1, R1a stops producing an orphan, so no change is expected. Do not extend it into a coverage mechanism (CONTEXT: one comparator).

---

### `phases/review/30-collect-score.md` (orchestration prose, HEAD read)

**Analog:** the NV relocation block, lines 44-55. Cases 1-4 (lines 45-48) are the rule F1 reuses verbatim for "a carried record (lead or member obligation) whose `stable_hash` is in `$DECIDED_HASHES`":
```
1. If the HEAD line at the stored `line` still equals the stored first line, use it as for any carried finding.
2. Otherwise search the file for lines equal to the stored first line. When exactly one match exists, OR one match is nearest unique to the stored `line` ... set the carryforward entry's `line` to that line number ... Also set the same `line` on the `$RECHECK_REQUESTS` entry whose `stable_hash` is this record's ...
3. When two or more matches tie for nearest, keep the stored `line` ...
4. When NO match exists ... pass `canonical_line_content` and `canonical_window` as null/absent ...
```
For decided ordinary records the "stored first line" is the stored `canonical_line_content` (ordinary records are hashed on it), not `current_code`'s first line. Case 4 keeps the ordinary `fixed-since-last` meaning, unlike NV (RESEARCH Pattern 1, item 4). Line 55 ends "This rule applies to Needs-verification records only — ordinary findings keep the stored-line read … (general relocation is out of scope)." Rewrite it to "NV and decided records only". General relocation of undecided records stays carried (RESEARCH Open Question 2).

**Prose-lock conflict, plan for it:** `test_nv_render.py:111-118` `RELOCATION_PHRASES` requires the literal `"relocation by content, NV only"` (it is in the line-44 heading), and `test_relocation_deleting_mutant` (:263) deletes each phrase. Either keep the NV heading verbatim and add a separate decided-record paragraph that cites cases 1-3, or update the lock in the same commit. Recommend the separate paragraph, which leaves the NV lock untouched, plus a new `decided_relocation_holds` lock that includes the `$RECHECK_REQUESTS` line clause (RESEARCH Pitfall 4).

**Probe split, from RESEARCH:** relocation is prose, so a score-level R1 fixture has to simulate it inside the `next_cf` builder (`test_score._ko_next_cf` :5640 / `_carried`). Name that simulator explicitly and lock the prose separately, so the fixture does not test a rule the shipped prose never states.

---

### `phases/review/05-state.md` (orchestration prose, state to env vars)

**Analog:** line 63, the `decisions` bullet ("Phase 0.5 reads it for nothing here …"), and the helper-binding style used for `carry_state.py` elsewhere. Change line 63 so that Phase 0.5 binds `$DECIDED_HASHES` from `python3 "$CARRY_STATE_PY" decided < "$STATE_FILE"` (the helper decides currency; the prose never re-derives it). Keep the D-02 sentence "an owner decision never removes a finding from `$CARRYFORWARD`". Cross-check the exact helper variable name against how `finalize-counts` is invoked in `90-finalize.md` (the fenced block ending :20) and copy its fail-closed `exit 1` branch. A refusal must halt, not bind an empty list silently, because an empty list would quietly revert to today's behaviour.

---

### `phases/shared/90-finalize.md` (render prose, contract)

**Analog:** line 26 "**Closed** = …" and the suffix bullets at lines 101-104:
```
  - stale code (D-13, `stale.cause == "code"`) — ` — code changed since your decision on pass {{stale.at_pass}} (was: {{dismissed|deferred}} — {{stale.reason}})`
  - stale severity (D-13, `stale.cause == "severity"`, a band-only change) — ` — severity changed ({{stale.was_band}} → {{band}}) since your decision on pass {{stale.at_pass}} (was: {{dismissed|deferred}} — {{stale.reason}})`
```
Add one bullet per new cause (`nearby`, the severity rise with the lane, `joined`/D-10) in the same `{{…}}` template form. Rewrite line 26's "equals the same four values now" for ordinary findings: the line is not compared, a nearby change reopens, a drop keeps, and only a rise with a new reviewer reopens. Line 25's "a decision … on the LEAD row closes nothing for it" needs the coverage exception. Line 106 ("the helper links an edited finding …") stays. Locks live in `test_finalize_card.py` (`check_*` + `LockCase.assert_holds`, :275-291).

### `templates/scoring.md` (line 122)

"A carried row keeps its stored `stable_hash` verbatim" is true today only for kept-open and NV rows (RESEARCH mechanism note R1a). After F1 it also holds for decided ordinary leads. Narrow or extend the sentence to match the shipped behaviour. Wording only.

---

### `scripts/test_carry_state.py` (test, CRUD read)

**Fixtures to change deliberately, citing D-01 (RESEARCH Pitfall 1):**
```python
def line_move_state():                       # :1174
    decided = dismiss(ba_state(a_snapshot=snap(1, line=11)), HA)
    return with_passes(decided, ba_state(a_snapshot=snap(1, line=14)))
```
`test_line_move_reopens` (:1283-1290) asserts `"stale"`/`"code"`. Flip it to `"current"` with a D-01 comment. Never delete it. `ROLLBACK_FIXTURES` (:1467-1475) row `("line move", line_move_state)` becomes a disagreement-free row; re-check `TestRollbackQuarantine` (:1494). `band_change_state` (:1169, medium to warning, a RISE on the same lane) is affected by the D-05 refinement: with no new lane, a rise now KEEPS the decision. Either give the fixture a gained lane (change `attribution` on the pass-2 obligation) so it stays a valid "rise reopens" case, or add a separate no-new-lane rise fixture that asserts `"current"`. `_band_change_scenario` feeds three contrast mutants (:1390-1424), so keep it a reopening scenario. Add a `band_drop_state` (warning to medium) that asserts `"current"` (D-06).

**Builder pattern** (lines 98-122 and 143-147): `snap(at_pass, file, line, band)`, `ba_state(row_band, a_band, a_snapshot)` (row B carrying A's obligation, hashes HA/HB), and `dismiss(state, h, at_pass, reason)`. For the D-05 refinement, add an `attribution` parameter to `ba_state`'s obligation (today hard-coded `{"agents": ["bugs"]}` at :113).

**Contrast-mutant pattern for carry_state guards** (lines 1404-1424). Use `mock.patch.object(carry_state, "decision_state", mutant)` and require the scenario to fail:
```python
        with self.subTest("contrast: band-blind"):
            self.assertEqual(real(rec, s), "stale")
            self.assertEqual(mutant(rec, s), "current")
            with mock.patch.object(carry_state, "decision_state", mutant):
                with self.assertRaises(AssertionError):
                    self._band_change_scenario()
```
New guards that each need a contrast or source mutant: line-free compare (reintroduce `line`), drop keeps (direction-blind), rise needs a gained lane, `nearby_at` compare, `covers` newcomer reopen, split inheritance, and a payload that cannot inject `covers`. The source-text mutant `_mutant(path, name, old, new)` (`test_confirmed_fix.py:775-784`) also works on `carry_state.py` when a guard is a literal expression.

**End-to-end chain** (lines 1719-1826): `append_pass(state, scored, n, head_sha)`, `e2e_gate(state, head_blobs)`, and `decide(state, at_pass, *(hash, decision))`. `ab_pipeline` (:1829-1856) is the closest existing multi-pass, multi-member site scenario. R6 (lead B resolved on recheck, member A splits off) is ab_pipeline's pass 3 with A decided as a member of B's row on pass 2. Copy it.

**Write-family lock:** `ALLOWED_KEY_WRITES = {"record_decisions": {"decisions"}, …}` (:1538). `covers`/`attribution` live inside `decisions` records, so no new root family and no lock change.

### `scripts/test_batch_card.py` / `scripts/test_card_text.py` (test, transform)

`test_rows_stale_line_move_cause_code` (`test_batch_card.py:143-149`) asserts that a line move is cause `"code"`. Flip it per D-01 (the row is absent from finalize rows). The exact-wording analogs are `test_card_text.py:89-98`:
```python
    def test_severity_stale_suffix_exact(self):
        text = doc_of(severity_stale_state())["card_text"]
        self.assertIn(
            " — severity changed (medium → warning) since your decision on "
            "pass 2 (was: dismissed — Accepted risk)", text)
```
Add one exact-string test per new suffix and for the D-10 note, in full and compact form. The compact budget test (`card_texts`, `CARD_TEXT_MAX_CHARS`) must still pass with the longer suffixes.

### `scripts/test_score.py` (test, score pipeline)

Builders: `_ko_find(id_, agent, line, conf, title, code, category, **over)` (:5620), `_hl_env(findings, ranges, carryforward, **over)` (:3792), `_ko_next_cf(result, heads, windows)` (:5640), `_ko_req` (:5647), `_KO_RANGES = {"src/a.py": [[8, 14]]}` (:5615). Band-stable inputs (RESEARCH Pitfall 2): conf 70, with pass-2 `changed_line_ranges` that exclude the flagged line. Assert the band on BOTH passes ("assert fixtures contain what you think"). Add `test_hash_and_golden_digest_unchanged` to every new class (`self.assertEqual(score.stable_hash("a.py", "  x=1", "title"), GOLDEN_DIGEST)`, as at `test_verified_fixes.py:508`).

### New `scripts/test_decision_continuity.py` (recommended)

**Analog:** `test_verified_fixes.py`. Its module docstring states the contract and the fixture provenance (:1-35). The header follows (:37-49):
```python
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import score  # noqa: E402
import state_shape  # noqa: E402
from test_score import GOLDEN_DIGEST, _verdict_rejections, make_finding  # noqa: E402
```
Import `carry_state`, `batch_card`, and `from test_carry_state import append_pass, decide, e2e_gate`. Structure: one RED-first test per reproduced row (R1a, R1b, R1c, R2, R3b, the D-05 refinement for R3a/R7, R4, R5, R6), then a module-level `DID_NOT_REPRODUCE` table or docstring section recording N1-N6 as "did not reproduce; dropped" with the probe result. Pin N1 and N2 as green regression tests (they pass today and must keep passing). Mutant class: copy `TestIndependentRouteMutants` (:1366-1395), including the uniqueness assert `self.assertEqual(self.src.count(old), 1, ...)` and the `_trips`/`_blocks` pair. Use unique module names (`score_m57_*`).

Fixture data: RESEARCH found no real lost-decision case in the iPlayarr state, so all fixtures are synthetic. Do not copy owner data (owner ruling 2026-10-25).

## Shared Patterns

### One comparator, one window, one writer
**Source:** `carry_state.decision_state`/`stale_cause` (:457-504), `score._independent_trigger` (:1325), and `carry_state.record_decisions` (:621).
**Apply to:** every currency, reopen and coverage rule. No prose step, card helper or scorer branch re-derives decision currency. batch_card reads `decision_state`/`stale_cause` only.

### Legacy reads unchanged, fail toward asking
**Source:** `decision_state` legacy branch (`"evidence" not in decision` returns `"current"`), `_full_evidence` fail-closed (:452).
**Apply to:** `covers` absent (today's per-record rule), `attribution` absent (any rise reopens), `nearby_at` absent on both sides (None == None). Never rewrite stored records.

### Untrusted text is data
**Source:** `batch_card._one_line` (:401-408); REASONS never name a hash, title or path (`carry_state.py` docstring "FAIL CLOSED"); payload key sets exact (`_DECISION_ENTRY_KEYS` :590).
**Apply to:** lane names and reasons in new suffixes, `covers` identities, and anything written by `record-decisions`.

### Import bans (AST-tested)
`score.py` `{json, hashlib, re, sys}` (`test_score.py:1476-1500`). `carry_state.py` `{json, os, sys}` (`test_carry_state.py:713`). The band rank is mirrored and pinned by an equality test, never imported.

### Mutation-test every guard
**Source:** `_mutant` (`test_confirmed_fix.py:775-784`, raises if the target is not found), the uniqueness assert in `TestIndependentRouteMutants._mod` (`test_verified_fixes.py:1376-1380`), and the contrast-mutant style (`test_carry_state.py:1390-1456`). Prose locks: a `*_holds(text)` predicate plus one deletion mutant per phrase (`test_nv_render.py:139`, :190 table, :263).

### Golden digest and replay gate
`GOLDEN_DIGEST` (`test_score.py:43`) re-asserted per new class. Replay gate per RESEARCH Pitfall 8: `replay.py candidate … --scorer rev:HEAD` shows REGRESSED 0, and `replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json` shows 0 differing. If `nearby_at` or the F6 dedup moves replay output, record an allowances entry; never waive it silently.

## Conventions

`gsd-tools verify conventions --derive --scope plugins/vibe-check/scripts` returned `{"skipped": true, "reason": "no-app-files"}`, because the module analyzes JS/TS only. These conventions come from reading the touched files:

| Axis | Dominant | Share | Entropy | Status |
|---|---|---|---|---|
| File-name casing | `snake_case.py`; tests `test_<module>.py`; fixtures kebab-case `.json` | ~100% in scope | low | named contract |
| Identifier casing | `snake_case` functions, `_private` helpers, `UPPER_SNAKE` constants, `_UPPER` private constants (`_NV_EVIDENCE_KEYS`, `_NEARBY_LINES`) | ~100% | low | named contract |
| Export style | module-level functions; CLI via `run(argv, stdin_text)`; tests import modules (plus named `test_score` builders) | ~100% | low | named contract |
| Import style | stdlib only, frozen per-module sets, AST-enforced | 100% | none | named contract |

Contested hotspots (author's choice): none in this scope. The repo-wide CJS<->SDK dual-resolver split (`bin/lib/**` CJS vs `sdk/src/**` ESM) is the standard example of an intentional per-directory split, but it does not apply to this Python plugin. Match each file's local style.

## No Analog Found

None outright. Three pieces have no exact precedent and should lean on RESEARCH.md:

| Piece | Role | Data Flow | Reason |
|---|---|---|---|
| Decision `covers` list and split inheritance (D-08/D-09) | service rule | CRUD read | First inheritance path in carry_state. The nearest analogs are `members[].obligation` (Phase 46) and `(agent, file, title)` identity in `05-state.md:62`. Follow RESEARCH Pattern 4 |
| Direction-aware band plus gained-lane check (D-05 refinement) | service rule | CRUD read | No existing rank compare in carry_state. Mirror `score._BAND_SEVERITY` (:700) and read lane sets from `attribution` (a list, `score.py:2422`) |
| `carry_state.py decided` subcommand | CLI read | CRUD read | New subcommand, shaped exactly like `pending` |

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/` (carry_state.py, score.py, batch_card.py, test_carry_state.py, test_batch_card.py, test_card_text.py, test_score.py, test_verified_fixes.py, test_confirmed_fix.py, test_nv_render.py, test_finalize_card.py, fixtures/future-schema.json), `phases/review/30-collect-score.md`, `phases/review/05-state.md`, `phases/shared/90-finalize.md`, `templates/scoring.md`, `.planning/phases/56-verified-fixes-close/56-PATTERNS.md`
**Files scanned:** 18
**Pattern extraction date:** 2026-10-25 (HEAD 032c4ac)
