---
phase: 59-stale-decisions-and-lost-deferrals
verified: 2026-10-29T02:37:08Z
status: gaps_found
score: 4/5 must-haves verified (one partial)
has_blocking_gaps: true
overrides_applied: 0
gaps:
  - truth: "SC2 / STALE-02: the card states the correct reopen reason for every reproduced wrong-keep shape"
    status: partial
    severity: blocking
    reason: >
      WR-01 (59-REVIEW.md): `_nearby_spots` unconditionally excludes `own_line`
      from the spots it reports (score.py:671-686, called at :510-512 and
      :2842-2846). When a single pass edits code beside BOTH the row's own
      decided line and another copy/grouped member, the card names only the
      other spot and silently omits that the owner's own decision line also
      changed — confirmed by reading the code (the exclusion is unconditional,
      not timing-dependent) and by the reviewer's real-chain scratch run
      (cr01_scenario with diff ranges [[12,12],[33,33]]: card says "code next
      to line 30 (another copy of this line) changed", never mentions line 12
      next to the row's own line 10). The row still reopens (the asking
      decision is correct), but the STATED REASON is incomplete/misleading —
      which is the literal text of STALE-02 and the phase's own ROADMAP goal
      ("asked again with the correct reason"). 90-finalize.md:110 additionally
      asserts "the spot is the lowest changed line", which this scenario shows
      is false (12 < 30 but 12 is never named). No fixture in
      test_decision_continuity.py or test_card_text.py exercises an edit that
      lands beside both the row's own line and another spot in the same pass —
      this exact combination was never built, so nothing caught it.
    artifacts:
      - path: "plugins/vibe-check/scripts/score.py"
        issue: "_nearby_spots (671-686) always drops own_line from the spot list; call sites at 510-512 (kept-open row) and 2842-2846 (group-loop row) both pass own_line only to exclude it"
      - path: "plugins/vibe-check/scripts/batch_card.py"
        issue: "_spot_suffix (540-556) renders only what _nearby_spots/stale_spots supply, so it inherits the omission"
      - path: "plugins/vibe-check/phases/shared/90-finalize.md"
        issue: "line 110 prose claims the named spot is always the lowest changed line; false whenever the row's own line is also reached"
    missing:
      - "A third spot kind (e.g. \"own\") or equivalent so a reopen caused partly by the row's own line is reflected in the card, with a fixture for cr01_scenario at ranges [[12,12],[33,33]] asserting the row's own line is mentioned"
      - "Correction to the 90-finalize.md 'lowest changed line' sentence to 'lowest changed line among the other spots', or a fix to the ordering so the claim is true"
  - truth: "SC4 / DEFR-01: a deferred covered member removed by min_confidence stays visible as an open deferred obligation instead of disappearing without a card"
    status: partial
    severity: minor
    reason: >
      WR-02 (59-REVIEW.md), confirmed by code reading (score.py:2404-2609):
      the "below-min-confidence 45; deferred-by: <hash>" reason is written
      only while the dropped record is still a covered member with no
      obligation of its own (first pass after the drop). On the next pass
      that kept-open row is carried forward as its OWN lead (it now has a
      stored stable_hash, so `rep.pop("kept_open", None)` at :2407 strips the
      marker and the record re-enters `carried_obligations` at :2469-2474);
      when it is dropped again by the same min_confidence filter it now takes
      the plain `carried_obligations` branch at :2608-2609 ("below-min-
      confidence" with no "deferred-by" suffix), so
      `_deferred_below_min_note` (batch_card.py:566-580) returns "" from pass
      3 onward. The row ITSELF stays open and visible every pass (confirmed:
      the reviewer's own repro notes "the row stays open and the gate still
      holds. That part is fine"), and I confirmed the only fixture covering
      this path, test_cw59_dmc_card_keeps_the_deferred_member_visible, checks
      only the first post-drop pass (s2), never pass 3+. This degrades the
      explanatory text but does not reproduce the original 999.23 failure
      mode (a deferred obligation disappearing with no card at all) — the
      card and row persist with a title/file/line/band every pass, just
      without the note tying it back to the owner's deferral.
    artifacts:
      - path: "plugins/vibe-check/scripts/score.py"
        issue: "2404-2609: the deferred-by reason is written only on the first drop pass; a carried kept-open row dropped again loses the link to its covering hash"
      - path: "plugins/vibe-check/scripts/batch_card.py"
        issue: "566-580 _deferred_below_min_note depends on the reason string surviving verbatim, so it silently renders nothing once the suffix is gone"
    missing:
      - "Carry the covering hash forward on a kept-open row dropped on a later pass (e.g. read cf.get(\"kept_open\") before the :2407 pop, or derive the note from carry_state._covering independent of the reason string), with a fixture at pass 3+ asserting the note is still on the card"
---

# Phase 59: Stale decisions and lost deferrals Verification Report

**Phase Goal:** A decided finding whose evidence changed is asked again with the correct reason, a deliberate decision whose evidence did not change stays decided, and a deferred obligation never disappears without a card (999.23)
**Verified:** 2026-10-29T02:37:08Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1 — CR-01, CR-02, CR-04, the min_confidence=45 deferred-member loss, and SA-02 each have a recorded verdict before any fix lands | ✓ VERIFIED | 59-REPRO.md V1-V6; all 5 fixtures confirmed failing pre-fix (reverse run, independently spot-checked: `pytest -k "TestStaleDecisions59 or dmc or dmx or Repro59Record"` reproduced in this session against the `82ec58b` worktree history via the documented commands; commits `82ec58b`, `c46f4dc`, `25ce414`, `a56b48c`, `1927508` all exist in git history and match claimed content) |
| 2 | SC2 — every reproduced wrong-keep shape re-asks with the correct reopen reason, invariant under reorder/lead-change/split/merge | ⚠ PARTIAL (see gap, blocking) | Re-ask + invariance VERIFIED (`pytest -k TestLeadOrderInvariance` → 2 passed, 31 subtests passed, run directly in this session); **reason-correctness FAILED** for the combined own-line + other-spot scenario (WR-01) |
| 3 | SC3 — a deliberate dismiss/defer stays decided when the five-line fingerprint is unchanged | ✓ VERIFIED | Controls pass: `test_c59_cr01_edit_at_45_keeps_decision`, `test_c59_cr04_edit_at_line_20_keeps_decision`, `test_dmx_dismissed_covered_member_below_min_confidence_may_drop` — all run and passed in this session (`pytest -k "TestStaleDecisions59 or dmc or dmx"` → 35 passed, 11 subtests passed) |
| 4 | SC4 — a deferred covered member dropped by min_confidence stays visible as an open obligation with a card | ⚠ PARTIAL (see gap, minor) | Row/card visibility VERIFIED across passes (confirmed in code: the row is always re-emitted by `_kept_open_rows`, never dropped from the visible set); **explanatory note lost from pass 3 on** (WR-02), not a disappearance |
| 5 | SC5 — the phase ends after one bounded cycle; residuals recorded; no "reliability complete" claim | ✓ VERIFIED | `grep -i "reliability complete"` returns nothing in 59-REPRO.md or the Phase-59 ROADMAP hunk; 59-REPRO.md "## Residuals" has R1-R8 with repro-as-acceptance-fixture; D-09 line present ("No open silent keep at close... no second review round"); `pytest -k TestStaleDecisions59` → 27 passed confirmed in this session |

**Score:** 4/5 fully verified, 1 partial-with-blocker (SC2), 1 partial-with-minor (SC4)

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| STALE-01 | 59-01 | Reproduce CR-01/CR-02/CR-04 before any fix | ✓ SATISFIED | 59-REPRO.md V1-V4; fixtures exist and pass at HEAD, reverse-run confirms red pre-fix |
| STALE-02 | 59-02/59-03/59-05 | Re-ask with correct reopen reason | ⚠ PARTIAL | Re-ask mechanism correct; reason text incomplete in the WR-01 combined scenario (blocking gap above) |
| STALE-03 | 59-02/59-03 | Pool evidence by obligation/hash at the read boundary | ✓ SATISFIED | `_kept_open_rows` pools over `carried_by_hash` (score.py ~434-530); `carry_state._merge_nearby` merges same-hash records at the read boundary (confirmed present, carry_state.py:349-404); CR-02 fixture green |
| STALE-04 | 59-01/59-06 | Unchanged fingerprint stays decided; five-line rule preserved | ✓ SATISFIED | Controls green (see SC3 row); window constant shared with 57's trigger, unchanged |
| STALE-05 | 59-06 | Same reopen/keep result under reorder/lead-change/split/merge | ✓ SATISFIED (code); ⚠ REQUIREMENTS.md not updated | `TestLeadOrderInvariance` with `cr01_kept_open_copies`, `cr02_sidecar_order`, `cr04_lead_flip` all pass (2 passed, 31 subtests, run directly); REQUIREMENTS.md traceability table still shows STALE-05 unchecked/"Pending" — documentation lag, not a functional failure |
| STALE-06 | 59-06 | One bounded cycle; residual discipline | ✓ SATISFIED (code); ⚠ REQUIREMENTS.md not updated | 59-REPRO.md Residuals + D-09 line present; same traceability lag as STALE-05 |
| DEFR-01 | 59-03 | Deferred covered member below min_confidence stays visible with a card | ⚠ PARTIAL | Row/card persists (SATISFIED for "does not disappear"); explanatory note lost pass 3+ (WR-02, minor gap above) |
| DEFR-02 | 59-06 | SA-02 gets one reproduction attempt; fixed or dropped | ✓ SATISFIED | V6 in 59-REPRO.md: did not reproduce on the real chain, pinned by `test_nv_render.all_carryforward_bypass_holds` (2 passed, 3 subtests, run directly); mechanism in `05-state-all.md` confirmed by grep |

**Orphaned requirements:** None — all 8 phase-59 requirement IDs (STALE-01..06, DEFR-01..02) appear in REQUIREMENTS.md and map to Phase 59.

**Documentation note (non-blocking):** REQUIREMENTS.md's checkbox/traceability table (lines 20-21, 73-74) still marks STALE-05 and STALE-06 as unchecked/"Pending" even though 59-06's commits (`3721d98`, `056db86`) implement and the tests prove both. This is a stale-tracking artifact, not a functional gap — the last commit to touch REQUIREMENTS.md (`6cb7046`) predates the 59-06 work. Recommend updating the checkboxes when gaps close.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `plugins/vibe-check/scripts/score.py` | Pooled kept-open rows, row-level nearby judging, D-06 min_confidence synthesis | ✓ VERIFIED (wired, with the WR-01/WR-02 defects noted above) | `_kept_open_rows`, `_nearby_spots`, `_covered_entry`, min_confidence branch all present and exercised by passing tests; also contain the two review-identified wording defects |
| `plugins/vibe-check/scripts/carry_state.py` | Read-side `_merge_nearby`, `stale_spots`, `_lifted_spots`, `_well_formed_spots` | ✓ VERIFIED | All present (grep-confirmed at lines 308-404, 840-851); `test_cw59_card_reads_spots_from_carry_state` proves the card renders carry_state's data, not its own derivation |
| `plugins/vibe-check/scripts/batch_card.py` | Card wording for D-04/D-05/D-06 | ✓ VERIFIED (wired, with WR-01/WR-02 noted) | `_spot_suffix`, `_deferred_below_min_note` present and wired through `_stale_suffix`; 7 relevant `test_cw59_*` card-text tests pass |
| `plugins/vibe-check/phases/shared/90-finalize.md` | Prose for the stale/deferred card suffixes | ✓ VERIFIED (with IN-03 prose inaccuracy noted) | Lines 110-114 present and phrase-locked by `test_card_text.py` (32 passed, 41 subtests, run directly); line 110's "lowest changed line" claim is inaccurate per WR-01 |
| `plugins/vibe-check/scripts/test_decision_continuity.py` | CR-01/CR-02/CR-04/DEFR-01 fixtures + STALE-05 invariance + mutation guards | ✓ VERIFIED | `TestStaleDecisions59`, `TestDeferredStaysOpen`, `TestLeadOrderInvariance`, `TestPhase57Mutants` all present and green (27, 8, 2, 27 passed respectively, run directly in this session) |
| `.planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md` | Reproduction ledger with green/red SHAs, reverse run, residuals | ✓ VERIFIED | All sections present; full-suite summary (3642 passed, 0 failed, 4805 subtests) matches an independent `pytest -q` run in this session |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `score.py _kept_open_rows` | `carried_by_hash` (D-19 index) | pooled snapshot/candidates lookup | ✓ WIRED | score.py:500-508; CR-01 fixtures (V1/V2) green, confirmed passing |
| `score.py` group loop | `_nearby_spots` (row-level judging) | `row_spots` computed before snapshot write | ✓ WIRED | score.py:2841-2846; CR-04 fixture (V4) green |
| `carry_state._merge_nearby` | same-hash record set | read-boundary merge of `nearby_at`/spots | ✓ WIRED | carry_state.py:349-404; CR-02 fixture (V3) green, `decision_state` returns "stale" as expected |
| `score.py` min_confidence branch | `carried_obligations` / `deferred_covered` | `_covered_entry` synthesis (D-06) | ✓ WIRED (first pass only) | DEFR-01 fixture (V5) green for pass 2; **not re-linked on pass 3+** (WR-02 gap) |
| `batch_card.py _stale_suffix` | `carry_state.stale_spots` | card renders reader's data, not its own derivation | ✓ WIRED | `test_cw59_card_reads_spots_from_carry_state` divergence-mutant test passes |
| `_nearby_spots` output | card's "N other spots" count / named spot | `_spot_suffix` rendering | ⚠ WIRED BUT INCOMPLETE | Renders correctly for every tested combination, but the own-line exclusion means the link carries incomplete data into the card in the untested combined scenario (WR-01) |

### Data-Flow Trace

Not applicable in the Level-4 (component render) sense — this phase is an internal decision-continuity pipeline (score → carry_state → batch_card → finalize prose), not a UI. The equivalent trace is the real score→carry→card chain, which I exercised directly rather than reading it: every claimed-green fixture (CR-01, CR-01 multi-pass, CR-02, CR-04, DEFR-01, the three STALE-05 invariance scenarios, all 7 card-wording tests, all 27 mutation guards) was re-run in this session and passed, and the full offline suite (3642 passed / 0 failed / 4805 subtests) was independently reproduced. The two defects found (WR-01, WR-02) were likewise independently confirmed by reading the exact code paths named in 59-REVIEW.md, not taken on the review's word.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| STALE-05 invariance holds | `pytest -q test_decision_continuity.py -k TestLeadOrderInvariance` | 2 passed, 31 subtests passed | ✓ PASS |
| CR-01/CR-02/CR-04/DEFR-01 fixtures green at HEAD | `pytest -q test_decision_continuity.py -k "TestStaleDecisions59 or TestDeferredStaysOpen or Repro59Record"` | 35 passed, 11 subtests passed | ✓ PASS |
| Card wording (D-04/D-05/D-06) renders correctly for every existing fixture | `pytest -q test_card_text.py` | 32 passed, 41 subtests passed | ✓ PASS |
| Mutation guards for the Phase-59 pooling fixes trip correctly | `pytest -q test_decision_continuity.py -k TestPhase57Mutants` | 27 passed | ✓ PASS |
| SA-02 drop mechanism pinned against `05-state-all.md` | `pytest -q test_nv_render.py -k all_carryforward_bypass` | 2 passed, 3 subtests passed | ✓ PASS |
| Full offline suite is green at HEAD | `pytest -q` (run once, from `plugins/vibe-check/scripts`) | 3642 passed, 0 failed, 4805 subtests passed in 153.73s | ✓ PASS |
| `_nearby_spots` structurally excludes the row's own line (WR-01) | Direct read of score.py:671-688, call sites :510-512 and :2842-2846 | `line == own_line` is an unconditional skip condition; no fixture passes an own-line-reaching range alongside another spot | ✗ CONFIRMS GAP |
| D-06 deferred-by suffix is lost after the first drop pass (WR-02) | Direct read of score.py:2404-2609; confirmed no test exercises pass 3+ for `deferred_covered_sub_threshold_scenario` | `test_cw59_dmc_card_keeps_the_deferred_member_visible` asserts only against `s2` (pass 2) | ✗ CONFIRMS GAP |

### Probe Execution

SKIPPED (no runnable entry points) — Phase 59 is a library/test-suite change; no `scripts/*/tests/probe-*.sh` exist and none are declared in the PLAN/SUMMARY/REVIEW files for this phase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | No TBD/FIXME/XXX/TODO/HACK debt markers found in any Phase-59-modified file (score.py, carry_state.py, batch_card.py, test_decision_continuity.py, test_card_text.py, test_nv_render.py, 90-finalize.md, 50-fix-loop.md) | — | All "XXX" hits are `mktemp ".../vc.XXXXXX"` template characters, not debt markers; all "placeholder" hits are the pre-existing `_NV_PLACEHOLDERS` literal-value check, unrelated to Phase 59 |
| `.planning/REQUIREMENTS.md` | 20-21, 73-74 | STALE-05/STALE-06 checkboxes and traceability rows not updated after 59-06 implemented and tested them | ℹ️ Info | Documentation lag only; functional behavior verified independently in this report |

### Human Verification Required

None. This phase's surface (internal scoring/carry/card pipeline, prose files) is fully exercisable through the existing automated test harness; no UI, timing-dependent, or external-service behavior requires a human to confirm. No `<human-check>` blocks were found in any 59-0X-PLAN.md.

### Gaps Summary

Phase 59 reproduced and fixed CR-01 (both single-pass and multi-pass), CR-02, CR-04, and the DEFR-01 min_confidence=45 deferred-member loss, each with a real failing-before/passing-after fixture and a mutation guard — independently confirmed in this session by running every cited test directly, not by trusting the SUMMARY files. The STALE-05 lead-order invariance guard is real and green. SA-02 was attempted once, did not reproduce, and is pinned correctly (DEFR-02 satisfied). The one-cycle discipline (STALE-06/D-08/D-09) was followed: build → code review → this verification, with no "reliability complete" claim anywhere and all non-fixed items (R1-R8) recorded with their acceptance repro in 59-REPRO.md.

The phase's own code review (59-REVIEW.md) then surfaced two real, independently-confirmed wording defects that neither the phase's fixtures nor the invariance guard exercise:

- **WR-01 (blocking, against SC2/STALE-02):** `_nearby_spots` structurally cannot report the row's own line as a changed spot, so when one pass edits code beside both the row's own decided line and another copy/grouped member, the card names only the other spot and the owner is never told their own decision's line also changed. The decision still correctly reopens, but the STATED REASON — the exact thing STALE-02 and the phase's ROADMAP goal require to be correct — is incomplete and, per the phase's own prose claim at 90-finalize.md:110, provably wrong in this scenario ("lowest changed line" is false when the own line is lower and omitted). This is a realistic combination (editing near two previously-decided duplicate lines, or near a row's own line and a grouped member, in one pass), not an exotic edge case, and it sits squarely inside the D-04/D-05 wording machinery the phase itself built.
- **WR-02 (minor, against SC4/DEFR-01):** The "still deferred" explanatory note on a D-06 kept-open row is written only for the first pass after the drop; from pass 3 onward the row stays open and visible (confirmed: the gate still holds, the row is never dropped from the visible set) but the card no longer explains why. This degrades transparency but does not reproduce the original 999.23 failure mode (silent disappearance) — the obligation still has a card every pass.

**Recommendation:** WR-01 blocks a clean SC2 pass and should go through a bounded follow-up (one more fix pass limited to this reproduced, qualifying defect, per D-08's "broken required workflow" class — the stated reopen reason is the exact required behavior named in STALE-02). WR-02 can reasonably be carried to backlog alongside R1-R8 since it does not break SC4's literal "does not disappear without a card" guarantee, though it is worth fixing opportunistically given how small the scope is (restore the covering-hash link on a re-dropped kept-open row). Both are owner-decidable: this report classifies them by observed effect, not by assumption, and defers the routing decision (fix-now vs. backlog) to the standard gap-handling flow.

Separately, REQUIREMENTS.md's STALE-05/STALE-06 checkboxes lag the actual (verified) implementation — a documentation-only fix, not a functional gap.

---

_Verified: 2026-10-29T02:37:08Z_
_Verifier: Claude (bm-verifier)_
