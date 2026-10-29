# Phase 59 — Reproduction verdicts

- **Phase:** 59 — Stale decisions and lost deferrals
- **Date:** 2026-10-28
- **HEAD when recorded:** `82ec58b` (branch `feat/v2.14-phase-59`; the commit that added the red fixtures, before any phase-59 production edit)
- **Scope of evidence:** no live or paid run was performed. Every verdict below is a local pytest run on the real `score.run -> append_pass -> carry_state -> batch_card -> finalize_gate` chain, driven by the existing `test_decision_continuity.py` harness (`run_pass`, `decide_on`, `record_of`, `e2e_gate`, `fresh`, `base_file`). Nothing is stubbed. A live interactive run with a model was not done; nothing here claims one.
- **Rule applied:** reproduce first. A shape that reproduced is a failing real-chain fixture committed at `82ec58b` and mapped to the plan that fixes it. SA-02 got one attempt; a shape that does not reproduce on the real chain is recorded and dropped (D-07), backed by an executing pin.

Sources: 59-RESEARCH.md §"Reproduction Verdicts" (runs on HEAD `089f2fb`), 57-REVIEW-GAPS4.md (CR-01, CR-02, CR-04 original repros), and the pytest runs below on `82ec58b`, all from `plugins/vibe-check/scripts`.

In-suite record: `test_decision_continuity.REPRO_59` (six rows), locked by `TestRepro59Record.test_repro_59_record_is_complete`.

Full suite at `82ec58b`: `pytest -q` -> `5 failed, 3594 passed, 4772 subtests passed in 165.65s`. The five failures are exactly the five fixtures V1-V5 below.

---

## V1 — CR-01: edit beside the second kept-open copy (STALE-01 / STALE-02 / STALE-03)

**Verdict: REPRODUCED at `82ec58b` -> to be fixed by 59-02.**

**Failure as the owner would see it.** The same `return None` problem sits at lines 10 and 30; the owner dismisses it once. Next run, nobody re-reports it, and the change lands at line 33, right next to the second copy. The decision stays "current" and Finalize writes without asking again: the record read is the kept-open copy at line 10 only, and its nearby check never looks at line 30.

**Fixture.** `TestStaleDecisions59.test_cr01_edit_beside_the_second_copy_reasks`, built by `cr01_scenario(33)`: `bugs` at lines 10 and 30, conf 60, dismissed at pass 1; pass 2 has no findings and `changed_line_ranges = {src/a.py: [[33, 33]]}`.

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_cr01_edit_beside_the_second_copy_reasks
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 1, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'medium'}
1 failed, 94 deselected
```

Research run on the same shape: kept-open @10 only, `nearby_at None`, `current`, gate `write`.

Green at: _(filled by 59-06)_

---

## V2 — CR-01 multi-pass: the second copy is lost after a quiet pass (STALE-01 / STALE-03)

**Verdict: REPRODUCED at `82ec58b` -> to be fixed by 59-02.**

**Failure as the owner would see it.** Same two copies and the same dismissal. One quiet run happens first. On that run the scorer keeps only one open row for the identity (line 10), so the line-30 copy disappears from saved state. When the change beside line 30 lands on the following run, nothing can re-ask the decision any more.

**Fixture.** `TestStaleDecisions59.test_cr01_multipass_second_copy_stays_tracked`, built by `cr01_scenario(33, quiet_first=True)`: pass 2 has no findings and an empty diff; pass 3 edits line 33. The test asserts pass 2 holds two kept-open rows (lines 10 and 30) and pass 3 re-asks with `nearby_at == 3`.

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_cr01_multipass_second_copy_stays_tracked
E       AssertionError: Lists differ: [10] != [10, 30]
E       Second list contains 1 additional elements.
1 failed, 94 deselected
```

Research run on the same shape: pass 2 emits one kept-open row (@10); pass 3 -> `current`, gate `write`.

Green at: _(filled by 59-06)_

---

## V3 — CR-02: edit beside the second member sidecar (STALE-01 / STALE-02 / STALE-03)

**Verdict: REPRODUCED at `82ec58b` -> to be fixed by 59-03.**

**Failure as the owner would see it.** Same two copies, conf 75, dismissed. Next run a critical security finding leads at each line ("Injection X" @10, "Injection Y" @30), so both copies of the dismissed finding ride along as members. The change at line 33 is beside the second copy. carry_state reads the first record for the hash (the @10 sidecar), which has no nearby stamp, so the decision reads "current". The gate still stops, but only because the two injection rows are new and undecided; the dismissed finding itself is not re-asked.

**Fixture.** `TestStaleDecisions59.test_cr02_edit_beside_the_second_sidecar_reasks`, built by `cr02_scenario(33)`. The test asserts `carry_state.decision_state(record_of(s2, hA), s2) == "stale"`, not only the gate.

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_cr02_edit_beside_the_second_sidecar_reasks
E       AssertionError: 'current' != 'stale'
E        : record {'at_pass': 1, 'file': 'src/a.py', 'line': 10, 'canonical_line_content': 'return None', 'band': 'warning'}
1 failed, 94 deselected
```

Green at: _(filled by 59-06)_

---

## V4 — CR-04: removed guard beside a covered member (STALE-01 / STALE-02)

**Verdict: REPRODUCED at `82ec58b` -> to be fixed by 59-02.**

**Failure as the owner would see it.** A `bugs` finding at line 10 and a critical `security` finding at line 12 group into one row led by security; the owner dismisses it. Next run, the guard at line 6 is deleted (rewritten in place, no shift). Line 6 is inside line 10's five-line window but outside line 12's. Only the lead's line is checked, so the decision stays "current" and Finalize writes.

**Fixture.** `TestStaleDecisions59.test_cr04_removed_guard_beside_covered_member_reasks`, built by `cr04_scenario(6, 6)` (the builder asserts pass 1 produced exactly one row, led by `security`).

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_cr04_removed_guard_beside_covered_member_reasks
E   AssertionError: None != 2 : row snapshot has no owed nearby_at: {'at_pass': 2, 'file': 'src/a.py', 'line': 12, 'canonical_line_content': 'line_12 = 12', 'band': 'critical'}
1 failed, 94 deselected
```

Research run on the same shape: hB @12 `current`, `nearby_at None`, gate `write`.

Green at: _(filled by 59-06)_

---

## V5 — DEFR-01: deferred covered member dropped by min_confidence 45 (DEFR-01)

**Verdict: REPRODUCED at `82ec58b` -> to be fixed by 59-03.**

**Failure as the owner would see it.** The owner defers a row that covers a weaker `bugs` finding (conf 40). Next run the row's lead is resolved and the weaker finding splits out on its own. With a valid `min_confidence` of 45 configured, it is dropped before scoring: no row, no record, and Finalize writes. The deferral is lost silently. Without `min_confidence` the same finding stays open as a kept-open "sub-threshold; deferred-by" row (the existing D-20 behavior).

**Fixture.** `TestDeferredStaysOpen.test_dmc_deferred_covered_member_below_min_confidence_stays_open`, built by `deferred_covered_sub_threshold_scenario("defer", min_confidence=45, member_conf=40)`. The new `member_conf` keyword defaults to `STABLE_CONF`, so the five existing TestDeferredStaysOpen tests are unchanged and still pass. The config accepts `min_confidence` 0-49 only, hence 45 with a member at 40.

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_dmc_deferred_covered_member_below_min_confidence_stays_open
E       AssertionError: unexpectedly None : no row for 845f88b7; filtered [{'file': 'src/a.py', 'line': 10, 'title': 'Unchecked return at A', 'reason': 'below-min-confidence'}]
1 failed, 94 deselected
```

Green at: _(filled by 59-06)_

---

## V6 — SA-02: `--all` reviewed-set drop of a deferred member (DEFR-02)

**Verdict: DID NOT REPRODUCE on the real chain -> recorded and dropped (D-07). No code change.**

**Score-level probe (research, HEAD `089f2fb`).** Feeding `score.run` an envelope with `all_mode: True`, `reviewed_union: ["src/other.py"]`, the D-20 state carried forward and `deferred_hashes` set: the deferred member is dropped `not-in-reviewed-set` with no kept-open row. The mechanism exists in score.py (`_score_member`).

**Why the real chain never builds that envelope.**
- `phases/review/05-state-all.md` (ii) "Carry-forward bypass": `--all` forces `$PASS_NUMBER = 1`, `$LAST_REVIEWED_SHA = null`, `` `$CARRYFORWARD = []` `` and says "SKIP Phase 0.5 steps 2-5 ... EVEN IF a `by-mode/all/<scope-hash>.json` file already exists".
- `phases/review/05-state.md` binds `$DEFERRED_HASHES` inside step 2 (lines 74-83), which `--all` skips.
- So an `--all` envelope never carries a prior record or a deferred hash, and the drop cannot happen to a deferral.

**Executing evidence (green, with a deleting mutant):**
- Pin: `test_nv_render.all_carryforward_bypass_holds` over `05-state-all.md`, phrases `` `$CARRYFORWARD = []` ``, `SKIP Phase 0.5 steps 2-5`, `` EVEN IF a `by-mode/all/<scope-hash>.json` file already exists ``. Positive test `TestNvRenderLocks.test_all_carryforward_bypass_holds`; deleting mutant `TestNvRenderMutation.test_all_carryforward_bypass_deleting_mutant` (each of the three phrases deleted in turn trips the predicate).
- Companion pin (existing): `test_nv_render.deferred_binding_holds` locks that `$DEFERRED_HASHES` is bound inside step 2 of `05-state.md`.

```
$ pytest -q test_nv_render.py -k all_carryforward_bypass
2 passed, 36 deselected, 3 subtests passed
```

If either prose file changes so that `--all` carries state forward, one of these pins goes red and this verdict must be reopened.

---

## Controls (green on current code)

These pass at `82ec58b` and must stay green after the fixes. They show the fixtures discriminate (STALE-04, D-20):

- `TestStaleDecisions59.test_c59_cr01_edit_at_45_keeps_decision`: the same two copies, edit at line 45 (outside both five-line windows) -> `current`, gate `write`.
- `TestStaleDecisions59.test_c59_cr04_edit_at_line_20_keeps_decision`: the CR-04 row, edit at line 20 (outside A@10's and B@12's windows) -> `current`, gate `write`.
- `TestDeferredStaysOpen.test_dmx_dismissed_covered_member_below_min_confidence_may_drop`: the V5 shape with a DISMISS instead of a defer -> no row, gate `write`.

```
$ pytest -q test_decision_continuity.py -k "TestStaleDecisions59 or dmc or dmx"
5 failed, 3 passed, 86 deselected
```

---

## Residuals

_(filled by 59-06)_
