---
phase: 57-decision-continuity-within-closure
plan: 05
subsystem: vibe-check review prose (30-collect-score.md, 05-state.md, scoring.md)
tags: [prose, relocation, orchestrator, decided-hashes]
requires:
  - "57-02: carry_state.py decided (the helper the binding calls)"
  - "57-01: relocate_decided simulator in test_decision_continuity.py (the prose matches it)"
  - "57-04: snapshot.nearby_at stamp (the D-02 re-ask the prose points at)"
provides:
  - "30-collect-score.md 'Carried decided records' paragraph: decided ordinary leads and obligation members relocate by stored canonical line (Phase 53 cases 1-3); recheck-request line moves with them; the lead's own member record moves with the lead; case 4 stays fixed-since-last"
  - "05-state.md Phase 0.5 binding of $DECIDED_HASHES, fail-closed on any non-zero helper exit"
  - "scoring.md identity sentence true for decided and re-scored rows"
  - "test_nv_render.py locks: decided_relocation_holds, state_binding_holds, section-scoped deletion mutants"
affects: [57-06, 57-07]
tech-stack:
  added: []
  patterns:
    - "section-scoped prose lock: phrases are checked inside the new paragraph only, so a copy of a phrase elsewhere in the file (the NV block also says $RECHECK_REQUESTS, fixed-since-last) cannot keep the lock green; mutants delete inside the section only"
key-files:
  created:
    - .planning/phases/57-decision-continuity-within-closure/deferred-items.md
  modified:
    - plugins/vibe-check/phases/review/30-collect-score.md
    - plugins/vibe-check/phases/review/05-state.md
    - plugins/vibe-check/templates/scoring.md
    - plugins/vibe-check/scripts/test_nv_render.py
decisions:
  - "The decided-record relocation prose also moves the lead's own member record (no obligation, same agent/file/title/stored line) with the lead; it is locked with its own phrase, so the phantom-row defect 57-01 found cannot come back through the prose"
  - "A member's stored first line is obligation.snapshot.canonical_line_content, else the first non-blank line of its current_code, the same as the relocate_decided simulator"
  - "The decided-record locks are scoped to the new paragraph / the decisions bullet, not the whole file, because several phrases also occur in the NV block"
metrics:
  duration: "~70 min"
  completed: 2026-10-26
  tasks: 2
  files: 4
---

# Phase 57 Plan 05: Decided-record relocation prose and $DECIDED_HASHES binding Summary

The orchestrator now finds a decided ordinary finding at HEAD by its stored canonical line, using Phase 53's cases 1-3. A pure line shift above a decided finding therefore keeps the same `stable_hash`, and the owner's decision stays attached. Phase 0.5 binds `$DECIDED_HASHES` from `carry_state.py decided` and halts on any non-zero exit. Every new sentence is locked by a predicate with deletion mutants.

## What changed

- **`30-collect-score.md`**: new paragraph **Carried decided records (Phase 57, D-01 — relocation by content for decided records)**, placed right after the NV block. It covers:
  - Scope: entries whose `stable_hash` is in `$DECIDED_HASHES`, and `members[]` whose `obligation.stable_hash` is in it, when the record is not NV.
  - Stored first line: the entry's stored `canonical_line_content`. For a member it is `obligation.snapshot.canonical_line_content`, else the first non-blank line of its `current_code`. Both sides are `.strip()`ped before comparing.
  - Case 2 moves `line`, computes the canonical and the window, and moves the matching `$RECHECK_REQUESTS` entry's `line`. Otherwise the scorer would reject the request with `verdict: record not carried`.
  - **The lead's own member record moves with the lead** (57-01 carry note). Without that it would come back as a phantom row.
  - Case 3 keeps the stored line. Case 4 reads the stored line, and a null canonical there means `fixed-since-last`. This differs from NV.
  - A Why paragraph: the same canonical gives the same hash (D-01). A nearby edit is `snapshot.nearby_at` and re-asks (D-02); the prose does not detect it. Undecided rows keep the stored-line read, and general relocation stays out of scope.
- The NV block's closing sentence now reads "…to Needs-verification records and, per the next paragraph, to decided records only — undecided ordinary findings keep the stored-line read…". The NV heading and all `RELOCATION_PHRASES` are byte-identical, and the Phase 53 locks stay green.
- **`05-state.md`**: the `decisions` bullet now binds `$DECIDED_HASHES` using the same `if …; then … else echo "I'm uncertain …" >&2; exit 1; fi` shape as finalize-counts. It says "Never bind `[]` on failure". On pass 1 there is no state file, so the value is `[]` and the helper is not run. It cross-references 30-collect-score step 0. The D-02 sentence is kept verbatim.
- **`scoring.md:122`**: "A carried kept-open, Needs-verification or decided row keeps its stored `stable_hash` verbatim; a re-scored undecided row recomputes it … (Phase 57 D-01)."

## Locked phrases

`DECIDED_RELOCATION_PHRASES` (checked inside the decided paragraph only):
1. `Carried decided records (Phase 57, D-01`
2. ``is in `$DECIDED_HASHES` ``
3. `` `obligation.stable_hash` ``
4. ``the "stored first line" is the record's stored `canonical_line_content` ``
5. ``also sets the same `line` on the `$RECHECK_REQUESTS` entry whose `stable_hash` is this record's``
6. `` `verdict: record not carried` ``
7. `The lead's own member record moves with the lead`
8. ``a null canonical stays `fixed-since-last` for an ordinary record``
9. `` `snapshot.nearby_at` ``
10. `general relocation stays out of scope`

`DECIDED_CONTEXT_PHRASES` (whole file): `relocation by content, NV only` (the NV heading), and `to decided records only — undecided ordinary findings keep the stored-line read`.

`STATE_BINDING_PHRASES` (checked inside the 05-state `decisions` bullet only): ``Phase 0.5 binds `$DECIDED_HASHES` ``, `carry_state.py" decided < "$STATE_FILE"`, `stopping before any HEAD read`, `exit 1`, `Any non-zero exit halts the run`, ``Never bind `[]` on failure``, `relocates each entry in this list by content`, ``an owner decision never removes a finding from `$CARRYFORWARD` ``.

New tests (9):
- `test_decided_relocation_holds`, `test_state_binding_holds`, `test_state_binding_one_helper_call`
- `test_decided_relocation_deleting_mutant` (whole file), `test_decided_relocation_in_paragraph_deleting_mutant`, `test_decided_relocation_paragraph_removed_mutant`
- `test_state_binding_deleting_mutant`, `test_state_binding_in_bullet_deleting_mutant`, `test_state_binding_empty_on_failure_inserting_mutant`

Both predicates also run in the CASES table (`test_each_predicate_holds`).

## Verification (observed)

- Task 1 verify: `pytest -q test_nv_render.py test_finalize_card.py` gave 43 passed, 95 subtests. `grep -c "Carried decided records (Phase 57"` = 1, `grep -c "relocation by content, NV only"` = 1, `grep -c "Phase 57 D-01" scoring.md` = 1.
- Task 2 verify: `pytest -q test_nv_render.py` gave 25 passed, 81 subtests. `grep -c "def test_decided_relocation\|def test_state_binding"` = 9. `DECIDED_HASHES` count: 05-state 4, 30-collect-score 2. `carry_state.py" decided` = 1. `exit 1` in 05-state went from 1 at HEAD to 2. The D-02 sentence count = 1.
- `pytest -q test_nv_render.py test_finalize_card.py` after both tasks: 52 passed, 135 subtests.
- Full suite after both tasks: **3191 passed / 8 failed**. The failures are the 7 known 57-06 card-wording/R3a reds plus `test_replay.py::TestDiffMode::test_member_only_mutation_exits_one`, which was already failing before this plan (see Deferred Issues). The full run after Task 1 alone showed the same 8.

### Live CLI check of the binding (no model calls)

State built with `test_decision_continuity.pass1(base_file())` (one dismissed row), written to the scratchpad:

```
dismissed hash: dee0f5347ac7433cd77eeb2c84df6ae4738e449ab1812a880718348ac21f1e4c
$ python3 carry_state.py decided < s.json
["dee0f5347ac7433cd77eeb2c84df6ae4738e449ab1812a880718348ac21f1e4c"]exit=0
$ python3 carry_state.py decided < empty.json      # {"passes": []}
exit=2
stdout bytes:        0
stderr:
refused: malformed state: passes
```

The refusal exits **2**, not 1 as the plan's interface note says. The prose's `if …; then … else … exit 1; fi` treats any non-zero exit as failure, so the run halts and nothing is bound.

## Deviations from Plan

**1. [Rule 2 - Missing critical] Lead's own member record moves with the lead**
- **Found during:** Task 1 (57-01 carry note)
- **Issue:** the plan's paragraph text only covered the lead and obligation-carrying members. The lead's own member record has no obligation, so it would be read at the stale line and come back as a phantom row.
- **Fix:** an added sentence plus a locked phrase (`The lead's own member record moves with the lead`) with an in-paragraph deletion mutant.
- **Cost if wrong:** one extra sentence of prose. If the rule is wrong, a lone decided row would carry its own member at the new line, which is what the simulator already does.
- **Commit:** c9558e1

**2. [Rule 2 - Stronger lock] Section-scoped predicates and 10 relocation phrases instead of 6-8**
- **Found during:** Task 2
- **Issue:** `$RECHECK_REQUESTS`, `verdict: record not carried` and `fixed-since-last` also occur in the NV block. A whole-file predicate stays green if the decided paragraph loses them, so that guard could never trip.
- **Fix:** the predicates check the new paragraph or bullet only. Extra mutants delete inside the section only, and one removes the whole paragraph. The lock list also covers the member-record clause, the scope sentence and `Any non-zero exit halts the run`. "never bind" is locked as written in the prose, `Never bind \`[]\` on failure`.
- **Cost if wrong:** if the paragraph's end marker (`**Note:**`) or the bullet's end marker (`\n3. Narrow diff`) is reworded, the section runs to the end of the file. The lock stays meaningful but less tight.
- **Commit:** b249e92

**3. [Rule 2] Member stored first line spelled out**
- The plan said only "the entry's stored `canonical_line_content`". Members have no such field, so the prose names `obligation.snapshot.canonical_line_content`, else the first non-blank line of `current_code`, the same as `relocate_decided`.
- **Cost if wrong:** prose and simulator would diverge for members. 57-07 cross-checks this.

## Assumption Drift (advisory)

- **Found during:** Task 2 live check. **Planned:** `carry_state.py decided` exits 1 on bad state. **Actual:** it exits 2, like every carry_state subcommand. **Why:** the shared CLI refusal path. **Cost if wrong:** none, because the binding treats any non-zero exit as failure.
- **Found during:** Task 1 full-suite run. **Planned:** the full suite has 7 red. **Actual:** 8 red. `test_replay.py` was collected in this run (earlier waves had it skipped by the holdout hook), and one of its mutants has a stale anchor left by 57-04's score.py edit. **Cost if wrong:** low, test-only.

## Deferred Issues

- `test_replay.py::TestDiffMode::test_member_only_mutation_exits_one` fails with `mutation anchor moved: member`. The `_MUTANTS["member"]` anchor (test_replay.py ~697) no longer matches score.py after 57-04. It is out of scope here and is logged in `deferred-items.md`. The fix is to re-anchor the mutant (test-only).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/30-collect-score.md, 05-state.md, templates/scoring.md, scripts/test_nv_render.py
- FOUND commits: c9558e1, b249e92
