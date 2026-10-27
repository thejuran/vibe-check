---
phase: 57-decision-continuity-within-closure
plan: 01
subsystem: vibe-check carry-forward decisions (score.py / carry_state.py / batch_card.py), test-only
tags: [reproduce-first, fixture, carry_state, score, decisions]
requires: []
provides:
  - "plugins/vibe-check/scripts/test_decision_continuity.py: the Phase 57 harness, 10 RED reproduction fixtures (R1a-R7), 6 green pins (N1-N6), the DID_NOT_REPRODUCE record"
affects: [57-02, 57-03, 57-04, 57-05, 57-06, 57-07]
tech-stack:
  added: []
  patterns:
    - "real-chain multi-pass fixtures: score.run -> append_pass -> carry_state / batch_card / finalize_gate, nothing stubbed"
    - "later-plan names read with getattr(carry_state, name, sentinel) so the module imports on HEAD"
    - "band asserted on both passes in every code-path fixture (Pitfall 2)"
key-files:
  created:
    - plugins/vibe-check/scripts/test_decision_continuity.py
  modified: []
decisions:
  - "Band-stable confidence is 75, not 70: with pass 1 in the diff, a lone conf-70 'warning' finding drops warning -> medium on a quiet pass (R3b noise); fixtures use STABLE_CONF = 75"
  - "The relocation simulator moves the lead's own member record with the lead; otherwise it is read at the stored line and comes back as a phantom row. The 57-05 prose must say the same"
  - "R4 covers fixture expects ONE covers entry for a lone-finding row: record_decisions must not list the lead's own member record a second time"
metrics:
  duration: "~45 min"
  completed: 2026-10-26
  tasks: 3
  files: 1
---

# Phase 57 Plan 01: Decision continuity reproduction fixtures Summary

This plan adds the DECN-01 gate: `test_decision_continuity.py` runs the real scorer and state chain across passes. Ten reproduced decision-loss or wrong-keep paths are now committed as failing fixtures. Six paths did not reproduce; they are recorded as dropped and pinned green. No rule, prose or production file changed.

## What was built

- **Harness** (`F`, `base_file`, `head_read`, `relocate_decided`, `next_cf`, `fresh`, `run_pass`, `decide_on`, `record_of`, `card_rows`, plus `card_doc`, `card_text_full`, `card_text_compact`, `row_of`, `card_row`, `shift_band`, `pass1`, `target_decided`). `relocate_decided` is a named function. Its docstring cites the 30-collect-score.md step 0 cases 1-4 that Plan 57-05 writes into prose.
- **Target mode vs today mode:** `target_decided(state)` reads `carry_state.decided` through getattr. On HEAD the function does not exist, so target mode behaves like today's orchestrator. The fixtures turn green without edits once 57-02 adds `decided` and 57-05 ships the relocation prose.
- **Scenario builders shared across classes:** `new_lane_scenario`, `joined_scenario`, `nearby_scenario`, `split_scenario`.
- **`DID_NOT_REPRODUCE`:** N1-N6, all `did not reproduce; dropped — no code change`. Two more rows cover title drift (excluded by ROADMAP) and the real data (no case found; fixtures synthetic).

## Reproduction verdicts

| path | fixture | status on HEAD | observed reason |
|------|---------|----------------|-----------------|
| R1a | `TestLineShift::test_r1a_shift_above_threshold_keeps_decision_and_hash` | REPRODUCED — RED | `record dee0f534 is not an open record (decision orphaned)`: the stored-line read re-hashed the row to `ec3d5f64` |
| R1b | `TestLineShift::test_r1b_shift_sub_threshold_keeps_decision` | REPRODUCED — RED | kept-open row keeps `dee0f534` but `decision_state` is `'stale' != 'current'` (cause `code`) |
| R1c | `TestLineShift::test_r1c_shift_with_rereport_is_one_decided_row` | REPRODUCED — RED | the re-reported row at line 13 is `'stale' != 'current'`; a phantom row also sits at line 10 |
| R2 | `TestNearbyEdit::test_r2_edit_within_five_beneath_reopens` (offsets 1/3/5), `test_nearby_at_carries_forward_on_quiet_pass` | REPRODUCED — RED | `'current' != 'stale'` (decision wrongly kept, all three offsets); `snapshot.nearby_at` missing (`None != 2`) |
| R3a-refined | `TestSeverityDirection::test_r3a_persistence_rise_without_new_lane_keeps`, `test_r3a_rise_with_new_lane_reopens_and_names_it`, `test_r3_decision_record_saves_attribution` | REPRODUCED — RED | forced rise with no new lane: `'stale' != 'current'`; `gained_lanes` missing (`['<missing>'] != ['security']`); decision `attribution` not saved (`None != ['bugs']`) |
| R3b | `TestSeverityDirection::test_r3b_band_drop_keeps_decision` (dismiss, defer) | REPRODUCED — RED | warning -> medium drop: `'stale' != 'current'` for both kinds |
| R4 | `TestRegrouping::test_r4_new_weaker_concern_on_decided_row_is_asked`, `test_r4_covers_frozen_at_decision_time` | REPRODUCED — RED | B is confirmed as a member with no obligation, and the decision stays `'current' != 'stale'` (counts 0/0/0, gate writes: silent finding loss); `covers` not recorded (`None != [...]`) |
| R5 | `TestRegrouping::test_r5_fresh_duplicate_outranking_decided_record_keeps_its_obligation` | REPRODUCED — RED | C leads (asserted); `record dee0f534 is not an open record (decision orphaned)`: the dedup dropped the carried obligation |
| R6 | `TestRegrouping::test_r6_split_member_inherits_decision` | REPRODUCED — RED | A splits into its own row `dee0f534` with `decision_state` `None != 'current'` and is asked as brand new |
| R7 | `TestCardWording::test_r7_rise_card_names_the_new_lane`, `test_nearby_card_wording`, `test_joined_card_wording_d10`, `test_compact_forms_fit_budget` (3 subtests) | REPRODUCED — RED | the card says `severity changed (warning → critical)` with no lane; no row at all for nearby/joined (`not found in ''`) |
| N1 | `TestDidNotReproducePins::test_n1_far_edit_keeps_decision` (with and without re-report) | did not reproduce; dropped — GREEN pin | decision `current`, gate `write` |
| N2 | `TestDidNotReproducePins::test_n2_stronger_lead_keeps_decided_member` | did not reproduce; dropped — GREEN pin | A keeps obligation `dee0f534` under C's row; only C is on the card |
| N3 | `TestDidNotReproducePins::test_n3_edited_flagged_line_is_linked_not_closed` | did not reproduce; dropped — GREEN pin | new hash, undecided, successor link to `dee0f534`, cause `code` |
| N4 | `TestDidNotReproducePins::test_n4_nv_rules_unchanged` | did not reproduce; dropped — GREEN pin | `_NV_EVIDENCE_KEYS` unchanged; behaviour in `TestNeedsVerificationDecisionEvidence` |
| N5 | `TestDidNotReproducePins::test_n5_no_expiry_many_quiet_passes` | did not reproduce; dropped — GREEN pin | deferral `current` after pass 6 |
| N6 | `TestDidNotReproducePins::test_n6_deferred_then_fixed_closes_normally` | did not reproduce; dropped — GREEN pin | `dee0f534` in `resolved[]`, counts 0/0/0, gate `write` |

Other green tests that must stay green: `test_stable_hash_and_golden_digest_unchanged`, the REPRO PIN `test_today_orchestrator_without_relocation_is_the_reproduced_failure` (57-07 retires it explicitly), `test_r2_edit_six_beneath_keeps`, `test_r2_edit_two_above_keeps`, `test_r6_split_member_whose_code_changed_is_asked`, `test_covers_cannot_be_injected_by_payload`, and `test_did_not_reproduce_record_is_complete`.

### Red-run tail (verbatim, `pytest -q test_decision_continuity.py -rA`, HEAD af1c69b)

```
FAILED test_decision_continuity.py::TestLineShift::test_r1a_shift_above_threshold_keeps_decision_and_hash
FAILED test_decision_continuity.py::TestLineShift::test_r1b_shift_sub_threshold_keeps_decision
FAILED test_decision_continuity.py::TestLineShift::test_r1c_shift_with_rereport_is_one_decided_row
FAILED test_decision_continuity.py::TestNearbyEdit::test_nearby_at_carries_forward_on_quiet_pass
SUBFAILED(offset=1) test_decision_continuity.py::TestNearbyEdit::test_r2_edit_within_five_beneath_reopens
SUBFAILED(offset=3) test_decision_continuity.py::TestNearbyEdit::test_r2_edit_within_five_beneath_reopens
SUBFAILED(offset=5) test_decision_continuity.py::TestNearbyEdit::test_r2_edit_within_five_beneath_reopens
FAILED test_decision_continuity.py::TestSeverityDirection::test_r3_decision_record_saves_attribution
FAILED test_decision_continuity.py::TestSeverityDirection::test_r3a_persistence_rise_without_new_lane_keeps
FAILED test_decision_continuity.py::TestSeverityDirection::test_r3a_rise_with_new_lane_reopens_and_names_it
SUBFAILED(kind='dismiss') test_decision_continuity.py::TestSeverityDirection::test_r3b_band_drop_keeps_decision
SUBFAILED(kind='defer') test_decision_continuity.py::TestSeverityDirection::test_r3b_band_drop_keeps_decision
FAILED test_decision_continuity.py::TestRegrouping::test_r4_covers_frozen_at_decision_time
FAILED test_decision_continuity.py::TestRegrouping::test_r4_new_weaker_concern_on_decided_row_is_asked
FAILED test_decision_continuity.py::TestRegrouping::test_r5_fresh_duplicate_outranking_decided_record_keeps_its_obligation
FAILED test_decision_continuity.py::TestRegrouping::test_r6_split_member_inherits_decision
SUBFAILED(cause='nearby') test_decision_continuity.py::TestCardWording::test_compact_forms_fit_budget
SUBFAILED(cause='severity') test_decision_continuity.py::TestCardWording::test_compact_forms_fit_budget
SUBFAILED(cause='joined') test_decision_continuity.py::TestCardWording::test_compact_forms_fit_budget
FAILED test_decision_continuity.py::TestCardWording::test_joined_card_wording_d10
FAILED test_decision_continuity.py::TestCardWording::test_nearby_card_wording
FAILED test_decision_continuity.py::TestCardWording::test_r7_rise_card_names_the_new_lane
22 failed, 16 passed, 10 subtests passed in 0.19s
```

(pytest-subtests counts a parent test whose subtests failed as PASSED and counts each failed subtest separately. The module has 30 test methods. All 22 failures are `AssertionError`; none is an `ImportError`, `AttributeError` or `TypeError` from the module.)

### Verification run (observed)

- Task 1 verify (`-k "TestLineShift or TestNearbyEdit or TestSeverityDirection or golden"`): 13 tests collected. Green: golden, REPRO PIN, six-beneath, two-above. Everything else failed with AssertionError.
- Task 2 verify (`-k "TestRegrouping or TestCardWording"`): 10 tests collected. Green: `test_r6_split_member_whose_code_changed_is_asked`, `test_covers_cannot_be_injected_by_payload`. Everything else failed with AssertionError.
- Task 3 verify: `-k "TestDidNotReproducePins or did_not_reproduce"` gave 7 passed, 8 subtests passed. The `DID_NOT_REPRODUCE` id check exited 0. `pytest -q test_carry_state.py test_batch_card.py test_card_text.py` gave 256 passed, 320 subtests passed.
- Grep checks: `grep -c expectedFailure` = 0; `def relocate_decided` = 1, and its docstring names `30-collect-score.md`; `_assert_band(` lines = 27 (26 calls); the iPlayarr path appears 0 times. The wording-prefix grep yields only prefixes of the interface strings.
- `git status --porcelain -- plugins/` before each commit showed only `test_decision_continuity.py`. No production file and no prose changed.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 49875d4 | harness + RED fixtures for line shift, nearby edit, severity direction |
| 2 | 2934031 | RED fixtures for regrouping (R4/R5/R6) and card wording (R7, D-10, D-12) |
| 3 | af1c69b | DID_NOT_REPRODUCE record + N1-N6 green pins |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's fixture inputs did not produce the shapes they claimed; values re-picked by measurement**
- **Found during:** Tasks 1-2 (exploration runs on HEAD before writing assertions)
- **Issue:**
  - `fresh` default conf 70 is not band-stable here (warning -> medium on a quiet pass).
  - R1a at conf 70 lands kept-open, not re-hashed.
  - R1b conf 55 is dropped on pass 1.
  - R3b conf 85 is capped at warning on pass 1, not critical.
  - The R3a new-lane finding at conf 90 / severity "warning" scores 82 and never rises.
  - In R6 with A=95 / B=80, A leads, so A is not a member.
  - R5's "Injection at C" sorts after A and does not lead.
- **Fix:** `fresh` keeps the interface default (conf 70). The fixtures use measured constants instead:
  - `STABLE_CONF = 75`, `REHASH_CONF = 80` (R1a, R1c), `KEPT_OPEN_CONF = 60` (R1b).
  - R3b uses conf 85 and asserts the actual band, warning.
  - The R3a new lane is conf 100 / severity "critical", which scores 100 and lifts the lone-lane cap so the band rises warning -> critical.
  - R6 uses A=75 / B=80, so B leads.
  - R5 and N2 use the title "SQL injection at C", which sorts first.
  - Each value is commented in the module, and each fixture asserts the shape it depends on: C leads, B is a member with no obligation, the band on both passes, `kept_open` present.
- **Cost if wrong:** a later plan's fixture could pass or fail for band-noise reasons rather than the code path. The both-pass band assertions are there to catch that.
- **Files modified:** plugins/vibe-check/scripts/test_decision_continuity.py
- **Commits:** 49875d4, 2934031

**2. [Rule 1 - Bug] Relocation simulator left the lead's own member record behind**
- **Found during:** Task 1 (target-mode simulation with `decided={hA}`)
- **Issue:** a row's `members[]` includes the lead's own record, which has no obligation. Relocating only the lead and members with obligations (the literal 57-05 wording) left that record at line 10. The scorer then emitted it as a phantom row (`ec3d5f64`) of whatever code sits there.
- **Fix:** `next_cf` moves a member that is the lead's own record (same agent/file/title/stored line, no obligation) together with the lead. With that, target-mode R1a/R1c produce exactly one row at line 13 under `dee0f534`. The only remaining difference is the `line` evidence key, which 57-02 drops.
- **Cost if wrong:** if 57-05's prose does not also move the lead's own member record, the shipped orchestrator keeps the phantom row even though these fixtures pass. **57-05 must add this clause** (and 57-07 should cross-check it).
- **Commit:** 49875d4

**3. [Rule 3 - Blocking] R6 fail-toward-asking leg needed realistic diff ranges**
- **Found during:** Task 2
- **Issue:** with `ranges={F: []}`, the edited A scores 67, below threshold. It is filtered, not asked, so the "must stay green" lock failed on HEAD.
- **Fix:** with `edit_a`, the diff names A's own line (`[[10, 10]]`), as a real incremental diff would. The inheritance leg keeps `ranges={F: []}`, which leaves B's rewritten line out of the diff so the nearby rule does not confound it. This choice is documented in `split_scenario`.
- **Cost if wrong:** the inheritance leg does not model the diff entry for B's edit. If 57-04's `nearby_at` reaches a covered member through B's diff range in real runs, that interaction is untested here.
- **Commit:** 2934031

## Assumption Drift (advisory)

- **Found during:** Task 1. **Planned:** "conf 70, band-stable per RESEARCH Pitfall 2". **Actual:** conf 70 at severity "warning" is not band-stable when pass 1 is in the diff. The research probe used severity "critical" at conf 90. **Why:** the -8 severity fallback puts conf 70 at the warning/medium boundary on a quiet pass. **Cost if wrong:** none for these fixtures, which assert bands. Later plans that write new fixtures should use `STABLE_CONF`.
- **Found during:** Task 2. **Planned:** `covers` = "first the record itself, then one entry per `members[]` of the row". **Actual:** on HEAD, a lone-finding row's `members[]` already holds the lead's own record. Read literally, that rule writes A twice, while the R4 fixture (the plan's own wording) expects exactly one entry. **Why:** the H-LANE member list includes the survivor. **Cost if wrong:** 57-03 either dedups (and R4 passes) or must justify editing a RED assertion, which 57-07 forbids. 57-03 should dedup on `(agent, file, title)`.

## Known Stubs

None. This is a test-only module. The getattr sentinels (`decided` -> None, `gained_lanes` -> `["<missing>"]`, `covering_decision` -> None) are deliberate: they keep the module importable until 57-02 and 57-03 land.

## Threat Flags

None. The change is test-only, and every fixture is synthetic (T-57-02). T-57-01 is pinned by `test_covers_cannot_be_injected_by_payload`, which also covers `attribution`.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_decision_continuity.py
- FOUND: 49875d4, 2934031, af1c69b
