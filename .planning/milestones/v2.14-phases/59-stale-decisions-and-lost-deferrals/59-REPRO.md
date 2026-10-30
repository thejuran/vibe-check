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

Green at: c46f4dc (59-02 Task 1: `_kept_open_rows` pools over `carried_by_hash`, one kept-open row per occurrence). Red at `82ec58b`, green at `c46f4dc`.

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

Green at: c46f4dc (59-02 Task 1: the same per-occurrence kept-open change keeps the line-30 copy tracked through the quiet pass). Red at `82ec58b`, green at `c46f4dc`.

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

Green at: a56b48c (59-03 Task 2: carry_state `_merge_nearby` merges the latest stamp across same-hash records at the read boundary). Red at `82ec58b`, green at `a56b48c`.

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

Green at: 25ce414 (59-02 Task 2: the group loop's `row_nearby` judges copies and covered members at their own lines). Red at `82ec58b`, green at `25ce414`.

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

Green at: 1927508 (59-03 Task 1: D-20 synthesis on the min_confidence branch keeps the deferred member open as a kept-open row). Red at `82ec58b`, green at `1927508`.

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

## Reverse run

The current tests were run against the production code from before the fix. Run on 2026-10-28 from HEAD `3721d98`.

- Worktree: `git worktree add --detach <scratchpad>/pre59 82ec58b`. The worktree SHA is `82ec58b`, the RED SHA, so score.py, carry_state.py and batch_card.py are the pre-fix versions.
- Copied in from HEAD `3721d98`: `test_decision_continuity.py`, `test_card_text.py` and `test_nv_render.py`. At `82ec58b`, test_nv_render.py was already identical to HEAD (`git diff --stat`: 2 files changed).
- Afterwards: `git worktree remove --force <scratchpad>/pre59`. `git worktree list` no longer shows it.

```
$ pytest -q -p no:cacheprovider test_decision_continuity.py -k "TestStaleDecisions59 or dmc or dmx or Repro59Record"
19 failed, 11 passed, 103 deselected, 11 subtests passed in 0.79s
```

Red fixtures. "fail" means an assertion failed; "error" means an AttributeError because a 59-04 helper is missing, which also counts as red.

| Fixture | Pre-fix result | Reason (one line) |
|---|---|---|
| test_cr01_edit_beside_the_second_copy_reasks | fail | `None != 2 : row snapshot has no owed nearby_at` (@10, band medium) |
| test_cr01_multipass_second_copy_stays_tracked | fail | `Lists differ: [10] != [10, 30]` |
| test_cr02_edit_beside_the_second_sidecar_reasks | fail | `'current' != 'stale'` |
| test_cr02_pooled_prior_carries_the_latest_owed_stamp | fail | `[(10, 'sub-threshold')] != [(10, 'sub-threshold'), (30, 'sub-threshold')]` |
| test_cr02_redecision_after_merge_reads_current | fail | `None != 2` (decision evidence has no stamp) |
| test_cr04_removed_guard_beside_covered_member_reasks | fail | `None != 2 : row snapshot has no owed nearby_at` (@12, critical) |
| test_cw59_card_reads_spots_from_carry_state | error | `carry_state` has no attribute `stale_spots` |
| test_cw59_cr01_card_names_the_other_copy | fail | the "line 30 (another copy of this line)" text is not on the card (card empty) |
| test_cw59_cr02_card_names_the_other_sidecar | fail | the "line 30 (another copy of this line)" text is not on the card |
| test_cw59_cr04_card_names_the_grouped_member | fail | the "line 10 (a finding grouped here)" text is not on the card (card empty) |
| test_cw59_dmc_card_keeps_the_deferred_member_visible | fail | `845f88b7… not found in []` |
| test_cw59_three_copies_card_names_lowest_line_and_count | fail | the "line 30 and 1 other spot" text is not on the card (card empty) |
| test_sp59_cr01_spot_is_the_other_copy | error | no `stale_spots` |
| test_sp59_cr02_merged_stamp_names_the_other_sidecar | error | no `stale_spots` |
| test_sp59_cr04_spot_is_the_grouped_member | error | no `stale_spots` |
| test_sp59_malformed_spots_read_as_none | error | no `_well_formed_spots` |
| test_sp59_quiet_pass_keeps_the_spots | error | no `stale_spots` |
| test_sp59_three_copies_lowest_line_plus_count | error | no `stale_spots` |
| test_dmc_deferred_covered_member_below_min_confidence_stays_open | fail | `no row for 845f88b7; filtered [... 'below-min-confidence']` |

The 11 that pass pre-fix are expected to. They are the controls and the guards against over-asking or mutating state: test_c59_cr01_edit_at_45_keeps_decision, test_c59_cr04_edit_at_line_20_keeps_decision, test_cr02_merge_does_not_mutate_state, test_cw59_same_spot_reopen_keeps_the_plain_wording, test_g59_kept_open_copy_from_another_identity_lends_no_stamp, test_k59_edited_kept_open_row_keeps_its_own_owed_stamp, test_l59_edited_kept_open_row_is_judged_at_its_own_line, test_m59_member_with_own_obligation_reasks_itself_not_the_row, test_n59_fresh_member_is_not_evidence_for_the_row, test_dmx_dismissed_covered_member_below_min_confidence_may_drop, and test_repro_59_record_is_complete.

The STALE-05 invariance guard was run in the same worktree:

```
$ pytest -q -p no:cacheprovider test_decision_continuity.py -k TestLeadOrderInvariance
SUBFAILED(scenario='cr01_kept_open_copies', lead='carried-leads')
SUBFAILED(scenario='cr02_sidecar_order', lead='carried-leads')
SUBFAILED(scenario='cr02_sidecar_order', lead='lead-flip')
SUBFAILED(scenario='cr04_lead_flip', lead='carried-leads')
4 failed, 2 passed, 131 deselected, 27 subtests passed in 0.15s
```

Before the fix, the result depended on order. It failed when the edit was beside the second kept-open copy, when the stamp sat on the second sidecar (under either injection lead), and when the covered member was not the lead. The mirrored permutations passed: reversed-arrival, both stamp-on-first-sidecar permutations, and the CR-04 lead-flip. The nine pre-Phase-59 scenarios stay green pre-fix. At HEAD, all 31 subtests pass.

---

## Suite at close

All runs are from `plugins/vibe-check/scripts` in the real checkout at HEAD `3721d98`.

```
$ pytest -q
3642 passed, 4805 subtests passed in 160.18s (0:02:40)

$ pytest -q test_replay.py
64 passed, 10 subtests passed in 9.80s
```

- 0 failed. The 4805 subtests are 59-05's 4797 plus 8 new invariance permutations (2 for cr01, 4 for cr02, 2 for cr04).
- **Replay deltas for Phase 61 GATE-02: none observed.** test_replay.py passed unchanged after every Phase-59 plan (59-02 through 59-05 and this close), with no change to the expected values. None of the archived envelopes holds any of the four shapes that would move: CR-01 kept-open copies per occurrence, D-21 stamp removal on a fresh far copy, the CR-04 covered-member stamp, and the DEFR-01 kept-open row below min_confidence. If Phase 61 sees replay drift, it is not explained by any of these four named repairs and must be treated as a finding.
- GOLDEN_DIGEST unchanged (`TestGolden` passes in the full run).

---

## Residuals

None of these is fixed in Phase 59. Each one names the repro that would serve as its acceptance fixture.

- **(R1) D-01 later-pass over-ask (D-02 carry).** Repro, re-checked at HEAD `3721d98`: pass 1 decide hA (`bugs` @10, conf 75); pass 2 a NEW identical copy at line 30 (fresh, conf 100) with no nearby edit; pass 3 edit@33 -> stale/nearby, and the gate does not write. At pass 2 and on a quiet pass 3 the identity correctly reads `current` (`test_p4_far_twin_new_copy_is_not_evidence`). This fails toward asking. A fix needs a per-copy origin marker, such as a snapshot `since_pass` compared to `decision.at_pass`, carried on keep, refresh, kept-open and sidecar. That is a task of its own, so under D-02 it is not built here.
- **(R2) WR-01, over-ask #2 (D-03).** A member that joined a deferred row after the deferral is kept open at the row's band. Unchanged and carried. The acceptance fixture is the round-4 WR-01 repro in 57-REVIEW-GAPS4.md.
- **(R3) SA-02 (D-07).** Did not reproduce on the real chain; dropped. Pinned by `test_nv_render.all_carryforward_bypass_holds` (positive test plus deleting mutant). Reopen only if `05-state-all.md` (ii) changes so that `--all` carries state forward.
- **(R4) Observation (no-growth rule, RESEARCH OQ2).** Other per-member drop reasons, such as `sub-threshold` from a negative pre-clamp score or `intent-doc-match`, can drop a deferred covered member inside a surviving row without a kept-open row. Not reproduced, and outside the approved list. Reproduce first before any work.
- **(R5) Observation (A2).** The CR-04 split variant was not exercised: a covered member splitting out after the stamp. The split and merge shapes the invariance guard covers are the existing `inherited_split` and `absorbed_split`.
- **(R6) Observation (A4).** The fix-loop subset/dispatch with two same-hash kept-open rows (59-02's per-occurrence rows) was not exercised.
- **(R7) D-09 close line.** `pytest -q test_decision_continuity.py -k TestStaleDecisions59` -> 27 passed at HEAD `3721d98`, with no wrong-keep fixture still red. No open silent keep at close. The D-08 one-cycle rule applies: the code-review/verify round that follows may add ONLY reproduced qualifying findings (mandatory-gate failure, data loss, silent loss of a qualifying finding, broken required workflow) to this list. There is no second review round.
- **(R8) Observation: card wording only (the 59-04 tie note).** When two copies' stamps tie, `_pooled_prior` takes the earliest carryforward arrival, so which copy's `nearby_spots` ride forward depends on input order (deterministic for a given state). In an unusual state where a different copy precedes the representative, a quiet pass could show the same-spot wording instead of naming the other copy. Checked against STALE-05: this does not violate any STALE-05 scenario. The decision result (`stale`/`nearby`, gate list) is the same in both orders, and `cr01_kept_open_copies` proves it with the arrival order reversed. Only the explanatory text could differ, so no fix was made. A possible fix: make the tie-break prefer the candidate at the row's own line. The acceptance fixture is a state with the far copy first in carryforward, then a quiet pass, and the card must name the other copy.
