# Roadmap: vibe-check

Updated 2026-10-23 (v2.13 roadmap written: three phases, 56–58, mapped to the 14 v2.13 requirements). ROI order: reliable fix closure, decision continuity, then clear actions and recovery; cost feasibility (999.12) is a separate, nonblocking check. Lower-value work is archived. Each phase begins by reproducing its failure on current code; a path that does not reproduce is recorded and dropped, never replaced with invented work.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)
- 🚧 v2.13 Reliable fix closure and recovery -- Phases 56–58 (in progress; planning)

### 🚧 v2.13 Reliable fix closure and recovery (Phases 56–58, in progress)

**Goal:** Let independently verified fixes close reliably, preserve owner decisions, and make recovery from an inconclusive check understandable.

- [x] **Phase 56: Verified fixes close** - Reproduce the closure failures, then let eligible independent evidence close fixed findings without dummy edits or repeated dismissal (completed 2026-10-25)
- [ ] **Phase 57: Decision continuity within closure** - Owner defer/dismiss decisions survive regrouping and unrelated edits, and reopen only on changed evidence
- [ ] **Phase 58: Clear actions, recovery and answers acted on** - Labels match behavior, an inconclusive re-check has a bounded recovery path, and a clear owner answer is acted on instead of re-asked

**Sequence:** Reproduce the closure failure first (Phase 56), repair it with targeted validation, then align decisions (Phase 57) and actions/recovery guidance (Phase 58). If the retry failure cannot be reproduced, stop that fix effort and reassess scope rather than invent a replacement project.

**Done when:** reproduced closure/decision bugs have focused regression evidence; distinct unresolved findings remain accounted for; labels and recovery guidance match behavior. Use local tests and existing replay evidence first. Any necessary live workflow check is separately bounded and budgeted.

**Scope:** Plugin closure and recovery only. No cost-accounting infrastructure, broad deduplication rewrite, scoring retune, new reviewer lane, orchestrator implementation, full B3/holdout campaign or automatic release.

## Phase Details

### Phase 56: Verified fixes close

**Goal**: A fix that independent evidence confirms closes its finding on the next run without a dummy code change or a repeated owner confirmation, while stale evidence is still rejected and still-applicable findings stay open (remaining 999.22)
**Depends on**: Nothing in v2.13 (first phase). Builds on the v2.12 Phase 54 one-pass confirmed-fix re-check; do not rebuild the initial confirmed-fix routing already shipped in v2.12
**Requirements**: VFIX-01, VFIX-02, VFIX-03, VFIX-04, VFIX-05, VFIX-06
**Success Criteria** (what must be TRUE):

  1. Before any closure change lands, each failure path has a recorded reproduction verdict on current code — the one-pass independent re-check limit, the reported six-row case, and `/review` unable to close a `/deep-review`-only finding — either as a failing regression fixture or as a written "did not reproduce; dropped" note; no closure change ships for a path without a failing fixture
  2. After an inconclusive independent re-check, a later run on the unchanged repaired code retries the re-check and closes the finding once confirmed — the fixture asserts no code edit and no second owner confirmation were needed
  3. In the six-row regression scenario, a fix that adds code beneath an unchanged pinned line, the tests-only `arrFacade` fix, and the four Codex-origin rows all close through eligible independent evidence without a "fixed in <sha>" dismissal on the card or at close-out
  4. Under `/review`, a finding raised only by a `/deep-review` agent (e.g. `test-sufficiency`) either closes via an eligible independent recheck or shows a clear, bounded explanation of why it cannot close there — it no longer sits silently at "needs recheck" (if reproduced; otherwise the drop is recorded)
  5. Safeguards hold under the same regression coverage: evidence from changed code is rejected as stale, a "still applies" verdict keeps the finding open, and the existing test suite stays green

**Plans**: 6 plans

Plans:
**Wave 1**

- [x] 56-01-PLAN.md — Reproduce-first: six-row fixture from real iPlayarr state + RED score fixtures (P2a/P2b/P2c/P3, VFIX-06 negatives)
- [x] 56-02-PLAN.md — Reproduce-first: one-pass limit RED in score/carry_state/prose + prose-contract locks for all Phase 56 prose changes

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 56-03-PLAN.md — Scorer: `independent` route, bound-plain members, D-04 trigger, D-06 test association, `recheck_settled`, D-11 reason, schema decision, mutants
- [x] 56-05-PLAN.md — Prose: Phase 0.5 touched paths + applied forwarding, Phase 2 independent re-check step, Phase 3 head_blobs, D-03/D-11 render wording

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 56-04-PLAN.md — Remove the one-pass limit for applied verdicts (score.py age gate + carry_state awaiting), blob-bound and settled-aware

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 56-06-PLAN.md — Phase gate: six-row end-to-end through append_pass/finalize_counts/e2e_gate; full suite, golden digest, replay diff, red/green ledger

<a id="closure-999-22"></a>

**Source context (preserved from the 2026-10-21 roadmap item 1):** First reproduce the one-pass independent re-check limit and relevant carried-Codex/general closure paths. Repair demonstrated failures with a bounded retry on current evidence, without a dummy code change or repeated owner confirmation. Preserve independent verification and reject stale evidence. Done when: focused regression scenarios cover an inconclusive check followed by a successful retry on unchanged repaired code, changed-code rejection, and a still-applies verdict remaining open.

**Reported regression example (2026-10-20):** Six open rows are already fixed, but the scorer cannot close them automatically. Each row's pinned line is unchanged: fixes added code beneath it, while the `arrFacade` fix added only tests. Four of the six findings came from Codex, which cannot be asked to recheck its own findings. The relevant reviewers and full test runs confirm each fix, yet the rows still require dismissal with a reason such as "fixed in <sha>" on the finding card or at close-out.

**Implementation coverage:** Reproduce this six-row case and cover both code added beneath an unchanged pinned line and the tests-only `arrFacade` fix, including the four Codex-origin rows. Verify that eligible independent evidence can close fixed findings without changing their pinned lines merely to trigger rechecking or requiring repetitive manual dismissal. Retain evidence freshness checks and keep unresolved or still-applicable findings open. Source: owner-provided example; row IDs, fix SHAs and test-run references were not supplied and should be recovered when building the regression fixture.

**Added closure path (owner decision 2026-10-21): `/review` cannot close a `/deep-review`-only finding.** A carried finding closes only when its own originating agent rechecks it, so a finding raised by an agent `/vibe-check:review` never dispatches (e.g. `test-sufficiency`) stays "needs recheck" under `/review` regardless of whether the code is fixed. Source: `.planning/milestones/v2.12-phases/52-hardening-accepted-fix-harness/deferred-items.md` ("From 52-11 (still open)"), previously an undecided product question. Reproduce it first alongside the six-row case; if reproduced, cover it in the same closure regression scenarios — an eligible independent recheck under `/review` (or a clear, bounded explanation of why it cannot close there) — without weakening independent verification.

### Phase 57: Decision continuity within closure

**Goal**: An owner's defer/dismiss decision stays bound to its evidence — it survives regrouping and edits unrelated to the finding, and the finding reopens only when its relevant evidence changes
**Depends on**: Phase 56 (closure path repaired first so decision binding is tested against the final closure behavior; identity rules change only for demonstrated failures)
**Requirements**: DECN-01, DECN-02, DECN-03
**Success Criteria** (what must be TRUE):

  1. Before any identity-rule change, a lost defer/dismiss decision on regrouping and on unrelated edits has a recorded reproduction verdict on current code — a failing fixture, or a written "did not reproduce; dropped" note with no rule change made
  2. A deferred or dismissed finding keeps its decision and recorded reason when findings are regrouped (regression fixture)
  3. A deferred or dismissed finding is not re-asked after an edit that does not touch the finding's evidence (regression fixture)
  4. When the finding's relevant evidence changes, the finding reopens and is presented again with the new evidence (regression fixture)

**Plans**: 7 plans

Plans:
**Wave 1**

- [x] 57-01-PLAN.md — Reproduce-first: harness + RED fixtures for R1a/R1b/R1c, R2, R3a-refined, R3b, R4, R5, R6, R7; "did not reproduce; dropped" record for N1-N6 (DECN-01 gate)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 57-02-PLAN.md — carry_state: line-free ordinary compare (D-01), nearby_at evidence (D-02), direction-aware band with gained-lane rule (D-05 refined/D-06/D-07), attribution on decisions, `decided` subcommand; flipped legacy tests

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 57-03-PLAN.md — carry_state: `covers` at decision time, `joined` reopen for a newcomer concern (D-08), inheritance for a covered member that splits (D-09)
- [ ] 57-04-PLAN.md — score.py: shared `_nearby_changed` window, `nearby_at` through all three snapshot writers, obligation-preserving member dedup (R5), mutants, replay numbers
- [ ] 57-05-PLAN.md — Prose: decided-record relocation by content in 30-collect-score.md, `$DECIDED_HASHES` fail-closed binding in 05-state.md, scoring.md identity sentence, prose locks

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 57-06-PLAN.md — Card: nearby / severity-rose-with-lane / D-10 joined suffixes (D-05, D-10, D-12), 90-finalize.md contract, exact-wording tests and locks

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 57-07-PLAN.md — Phase gate: ledger green, cross-module guards, end-to-end owner journey, full suite + golden + replay, STATE.md and carried item

**Source context (preserved from the 2026-10-21 roadmap item 2):** Reproduce any lost defer/dismiss decision on regrouping or unrelated edits before changing identity rules. Fix only demonstrated failures in the closure/recovery path; keep decisions bound to their evidence. Done when: regression fixtures preserve applicable decisions and reopen findings when relevant evidence changes. Broader duplicate presentation and cross-repo gate consumers are excluded.

### Phase 58: Clear actions, recovery and answers acted on

**Goal**: The owner can tell what each action does and what to do after an inconclusive re-check, and a clear plain-English answer to a decision card is carried out instead of being asked again (999.13 subset)
**Depends on**: Phase 56 (recovery guidance must describe the repaired closure behavior) and Phase 57 (decision cards reflect preserved decisions)
**Requirements**: RECV-01, RECV-02, ANSR-01, ANSR-02, ANSR-03
**Success Criteria** (what must be TRUE):

  1. The "Fix all" label states what it actually does, and the card says which findings need individual decisions; a test locks the card text to the behavior
  2. After an inconclusive re-check, the output states what happens next run and what the owner can do now, with no automatic closure and no new manual; existing recovery guidance and rejection/orphan explanations are reconciled to match actual behavior
  3. An unambiguous plain-English answer to a decision card (e.g. "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out" on the eight-row card) is translated into that card's validated grammar — `fix 5; dismiss 1,2,3,4,6,7,8` with the reason preserved — and the fix/dismiss/close-out workflow continues without re-showing the card (regression test)
  4. When a reference or reason is ambiguous or missing, or the card is stale, only the missing detail is asked — no guessing, no broadened decision, no full re-show (regression test)
  5. Whether finalize `fix N` still re-asks Apply/Skip (bug C) has a recorded verdict on current code; if it reproduces, the decided row proceeds to fixing without re-asking and a regression fixture covers it; if not, that is recorded and not filed

**Plans**: TBD

**Source context (preserved from the 2026-10-21 roadmap item 3):** Correct the misleading "Fix all" label and explain which findings require individual decisions. Reconcile existing recovery guidance and actionable rejection/orphan explanations. Done when: labels match behavior and an inconclusive re-check has a clear, bounded recovery path without automatic closure or a new manual.

**Bug: Plain-English decision-card answers cause a repeated-card loop (2026-10-20).** During iPlayarr phase 45's vibe-check 2.12.0 deep review, the owner answered via Other: "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out." `batch_card.py parse` rejected the clear request with "answer does not match the grammar". Following `phases/review/50-fix-loop.md`'s "Typed answer via Other" instruction to "re-show the SAME card once", Claude repeated the identical card instead of translating the decision. The owner responded: "i just answered you". Claude captured this as a local feedback draft titled "Re-asked a fix-loop card after the user gave a clear plain-language answer"; it was not previously a repository backlog entry.

**Expected behavior / regression coverage:** Interpret an unambiguous plain-English decision against the displayed card, translate it into the validated numbered grammar, and continue the authorized fix/dismiss/close-out workflow without asking the same question again. For this exact card the mapping was `fix 5; dismiss 1,2,3,4,6,7,8`, with reason "fixed in review-pass commits, verified on recheck". Preserve the owner's targets and reason, bind the translation to the current card, and retain normal fix verification and close-out checks. If a reference or reason is genuinely ambiguous or missing, ask only for that missing detail; do not guess, silently broaden the decision, or repeat the entire card. Cover both successful plain-English translation and ambiguous/stale-card cases in focused regression tests. Relevant paths: `plugins/vibe-check/phases/review/50-fix-loop.md` and `plugins/vibe-check/scripts/batch_card.py`; check the corresponding finalize decision flow too.

**Related issue:** [Verified fixes stay fixed — 999.22](#closure-999-22) (Phase 56). That issue leaves already-fixed rows awaiting owner decisions; this bug makes those decisions unnecessarily repetitive even after the owner clearly supplies them. The six-row closure example in Phase 56 is from the earlier pass; this later decision card contained seven already-fixed rows plus the Browse recovery finding.

**Check first (owner decision 2026-10-21): finalize `fix N` re-asks Apply/Skip (bug C from the unfiled 2026-10-09 write-up).** Close-out's finalize answer `fix N` routes the subset into the fix-loop card, which asks Apply/Skip again for a row the owner already decided. Repro: deep review leaves a warning → fix loop Stop → Close out → finalize `fix N; defer M`. Two other vibe-check causes from that write-up — trailing `-- <reason>` refused and fix commits refused over apostrophes/semicolons in finding titles — are confirmed fixed in current code (`phases/shared/90-finalize.md`, `scripts/fixcommit.py` D-08); C was not re-verified. As the first reproduction step of this item, confirm whether C still occurs on current code. If it does, fix it with the plain-English repeated-card bug (same symptom: a decided answer is asked again) and add a regression fixture; if it does not, record that and do not file it. Relevant paths: `plugins/vibe-check/phases/shared/90-finalize.md` and `plugins/vibe-check/phases/review/50-fix-loop.md`.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 56. Verified fixes close | 6/6 | Complete    | 2026-10-25 |
| 57. Decision continuity within closure | 3/7 | In Progress|  |
| 58. Clear actions, recovery and answers acted on | 0/TBD | Not started | - |

## Backlog

### 999.12: Narrow: Cost visibility feasibility — separate task

Inspect existing local usage records to determine whether a review's usage can be attributed reliably. Report available fields, missing data, pricing assumptions and the distinction between estimated, measured and billed cost. Do not start paid reviews to generate a baseline or invent per-agent usage.

Finish with a go/no-go recommendation for the smallest useful reporting change. Stop if reliable attribution is unavailable; document the limitation rather than build new accounting infrastructure. Existing chunk limits and estimates are not enforceable dollar caps. This check is independent of, and does not block, Reliable fix closure and recovery. Budget-control implementation and cross-repo orchestration changes require their own scope.

## Planning boundaries

- v2.13 is the active milestone; implementation follows its phase plans. Paid runs, new agents and publication still require explicit owner approval; this roadmap does not authorize them.
- v2.12 shipped as 2.12.0 under owner waiver; outcome remains **UNMET — measurement incomplete**. Its noise target was not demonstrated. Phase 55 and cancelled Phase 54 sweeps remain deferred.
- Reuse valid review evidence for unchanged code; scope new checks to changed code and affected callers. Any paid check requires an explicit bounded price proposal and owner approval.
- One branch and one PR per phase (owner decision 2026-10-23): `feat/v2.13-phase-<N>`, each cut from `main` after the previous phase's PR merges. Milestone setup and phase discussion sit with Phase 56's branch. After a phase PR merges, delete its branch locally and on GitHub once `main` is confirmed to contain it.
- Routine cleanup remains in [maintenance](backlog/MAINTENANCE.md).
- [Lower-value ROI candidates](backlog/archive/2026-10-18/ROI-DEFERRED.md) are archived with reopening conditions, not scheduled or declared complete.

## Release records

- [v2.12 archived roadmap](milestones/v2.12-ROADMAP.md): shipped reliability improvements; measurement incomplete.
- [v2.11 archived roadmap](milestones/v2.11-ROADMAP.md): last measured milestone, false alarms 5/18 and catches 15/15, with release/measurement caveats.
- [All milestone history](MILESTONES.md).
- [Archived backlog and disposition ledger](backlog/archive/2026-10-18/README.md).
