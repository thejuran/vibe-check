# Roadmap: vibe-check

Updated 2026-10-23 (v2.13 roadmap written: three phases, 56–58, mapped to the 14 v2.13 requirements). ROI order: reliable fix closure, decision continuity, then clear actions and recovery; cost feasibility (999.12) is a separate, nonblocking check. Lower-value work is archived. Each phase begins by reproducing its failure on current code; a path that does not reproduce is recorded and dropped, never replaced with invented work.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)
- 🚧 v2.13 Reliable fix closure and recovery -- Phases 56–58 (in progress; planning)

### 🚧 v2.13 Reliable fix closure and recovery (Phases 56–58, in progress)

**Goal:** Let independently verified fixes close reliably, preserve owner decisions, and make recovery from an inconclusive check understandable.

- [x] **Phase 56: Verified fixes close** - Reproduce the closure failures, then let eligible independent evidence close fixed findings without dummy edits or repeated dismissal (completed 2026-10-25)
- [x] **Phase 57: Decision continuity within closure** - Owner defer/dismiss decisions survive regrouping and unrelated edits, and reopen only on changed evidence (completed 2026-10-27)
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

**Plans**: 9 plans

Plans:
**Wave 1**

- [ ] 58-01-PLAN.md — Helper renders "Apply all / Fix all" scope text naming excluded Needs-verification rows by number; D-12 text == behavior lock with mutants (RECV-01)
- [ ] 58-02-PLAN.md — Per-reason recovery pairs (Next run / You can) for all 12 score.py reasons; NV suffix, output template and README reconciled; prose ↔ code lock (RECV-02)
- [ ] 58-07-PLAN.md — D-17 carrier, spine side: Phase 0 recognizes the whole-token `--close-out-after-rerun` re-entry marker (strip from `$SCOPE_ARGS`, print `CLOSE_OUT_AFTER_RERUN=<0|1>`, same shape as `--finalize`); spines' no-findings skip honors it; real-fence lock under bash/zsh with mutants (ANSR-01/02)

**Wave 2** *(blocked on 58-01)*

- [ ] 58-03-PLAN.md — `batch_card.py resolve`: owner references → current rows (title/marker/counted complement/stale remap) with one/none/many/count-mismatch statuses; eight-row iPlayarr fixture; parse stays the only gate (ANSR-01, ANSR-02)

**Wave 3** *(blocked on 58-01 + 58-03 + 58-07)*

- [ ] 58-04-PLAN.md — Fix-loop prose, part 1: translate → resolve → parse with "Read your answer as:" and act (ok branch), carried close-out paragraph reading Phase 0's `CLOSE_OUT_AFTER_RERUN=1`, Bottom line suggestion slot, helper-rendered Apply all text, residue removed, bug-C lock strengthened against mutant C (ANSR-01/03, RECV-01)

**Wave 4** *(blocked on 58-04 + 58-07)*

- [ ] 58-08-PLAN.md — Fix-loop prose, part 2: ask only the gap once (D-05/D-06), D-08 fallback, D-07 stale remap, D-17 routing, Rerun appends `--close-out-after-rerun` only when close_out was true and `${original_args}` strips it (consumed once), typed "bottom line"; round-trip test reads the carrier back through the real Phase 0 fence (ANSR-01/02)

**Wave 5** *(blocked on 58-01 + 58-03 + 58-04 + 58-08 — the Finalize twin reads the landed fix-loop prose)*

- [ ] 58-05-PLAN.md — Finalize prose, part 1: accurate Q1 header and Fix all / Dismiss all / Defer all / Mixed… descriptions, Mixed…/Other translation twin (ok branch, Q2 as fallback reason), NV stop text and echo sentence reconciled, session-conditional Bottom line line (ANSR-01, RECV-01/02)

**Wave 6** *(blocked on 58-05 + 58-08)*

- [ ] 58-09-PLAN.md — Finalize prose, part 2: ask only the gap once (Q2-aware), D-08 fallback, D-07 stale remap, Card budget; neighbour suite; bug-C static trace recorded (ANSR-02/03)

**Wave 7** *(blocked on everything above)*

- [ ] 58-06-PLAN.md — 58-REPRO.md: verdicts V1–V5, bug C "does not reproduce — fixed by 46d78e3 (v2.12)", inventory I-1..I-15; phase gate (full suite, replay 0 regressed, golden, mutant inventory incl. the carrier round-trip) (ANSR-03 + all)

**Source context (preserved from the 2026-10-21 roadmap item 3):** Correct the misleading "Fix all" label and explain which findings require individual decisions. Reconcile existing recovery guidance and actionable rejection/orphan explanations. Done when: labels match behavior and an inconclusive re-check has a clear, bounded recovery path without automatic closure or a new manual.

**Bug: Plain-English decision-card answers cause a repeated-card loop (2026-10-20).** During iPlayarr phase 45's vibe-check 2.12.0 deep review, the owner answered via Other: "fix the Browse recovery issue, then dismiss the 7 fixed rows and close out." `batch_card.py parse` rejected the clear request with "answer does not match the grammar". Following `phases/review/50-fix-loop.md`'s "Typed answer via Other" instruction to "re-show the SAME card once", Claude repeated the identical card instead of translating the decision. The owner responded: "i just answered you". Claude captured this as a local feedback draft titled "Re-asked a fix-loop card after the user gave a clear plain-language answer"; it was not previously a repository backlog entry.

**Expected behavior / regression coverage:** Interpret an unambiguous plain-English decision against the displayed card, translate it into the validated numbered grammar, and continue the authorized fix/dismiss/close-out workflow without asking the same question again. For this exact card the mapping was `fix 5; dismiss 1,2,3,4,6,7,8`, with reason "fixed in review-pass commits, verified on recheck". Preserve the owner's targets and reason, bind the translation to the current card, and retain normal fix verification and close-out checks. If a reference or reason is genuinely ambiguous or missing, ask only for that missing detail; do not guess, silently broaden the decision, or repeat the entire card. Cover both successful plain-English translation and ambiguous/stale-card cases in focused regression tests. Relevant paths: `plugins/vibe-check/phases/review/50-fix-loop.md` and `plugins/vibe-check/scripts/batch_card.py`; check the corresponding finalize decision flow too.

**Related issue:** [Verified fixes stay fixed — 999.22](#closure-999-22) (Phase 56). That issue leaves already-fixed rows awaiting owner decisions; this bug makes those decisions unnecessarily repetitive even after the owner clearly supplies them. The six-row closure example in Phase 56 is from the earlier pass; this later decision card contained seven already-fixed rows plus the Browse recovery finding.

**Check first (owner decision 2026-10-21): finalize `fix N` re-asks Apply/Skip (bug C from the unfiled 2026-10-09 write-up).** Close-out's finalize answer `fix N` routes the subset into the fix-loop card, which asks Apply/Skip again for a row the owner already decided. Repro: deep review leaves a warning → fix loop Stop → Close out → finalize `fix N; defer M`. Two other vibe-check causes from that write-up — trailing `-- <reason>` refused and fix commits refused over apostrophes/semicolons in finding titles — are confirmed fixed in current code (`phases/shared/90-finalize.md`, `scripts/fixcommit.py` D-08); C was not re-verified. As the first reproduction step of this item, confirm whether C still occurs on current code. If it does, fix it with the plain-English repeated-card bug (same symptom: a decided answer is asked again) and add a regression fixture; if it does not, record that and do not file it. Relevant paths: `plugins/vibe-check/phases/shared/90-finalize.md` and `plugins/vibe-check/phases/review/50-fix-loop.md`.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 56. Verified fixes close | 6/6 | Complete    | 2026-10-25 |
| 57. Decision continuity within closure | 23/23 | Complete    | 2026-10-27 |
| 58. Clear actions, recovery and answers acted on | 0/TBD | Not started | - |

## Backlog

### 999.23: Decision continuity known limits (Phase 57 close, D-19/D-22)

Phase 57 closed under the owner's D-19 hard stop with these reproduced defects carried, not fixed. Full repros: `.planning/phases/57-decision-continuity-within-closure/57-REVIEW-GAPS4.md` and `deferred-items.md`.

- **Wrong-keeps (decision stays current after its evidence changed):**
  - CR-01: same-hash copies kept open below threshold are not pooled. Two identical `return None` lines at 10 and 30, dismissed; an edit at 33 leaves the decision current. Zero-config.
  - CR-02: absorbed-member obligation sidecars are not pooled; carry_state reads the first sidecar.
  - CR-04 (predates the gap rounds): removing a guard beside a covered member never re-asks the row decision while the member stays in the row (D-14's "guarded upstream" case).
- **Over-ask to align under D-21:** an edit beside a NEW identical copy re-asks the decided copy at pass 3 (test_p4 locks the old behaviour); round-4 WR-01: a member that joined a deferred row after the deferral is kept open at the deferred row's band.
- **Deferral loss (D-20 edges):** min_confidence (valid 1–49; repro must use ≤49, e.g. 45) removing a deferred covered member drops it without a card; SA-02 `--all` `not-in-reviewed-set` drop (not reproduced — reproduce first).

Root-cause direction (from the review): pool `carried_by_hash` into `_kept_open_rows` and the member-sidecar path, and make carry_state's per-hash read merge records instead of keeping the first. Reproduce first; each fix needs a real-chain fixture and a mutant. Not scheduled; promote via `/bm:review-backlog`.

### 999.24: Diff context widens the nearby window (Phase 57 SC-3 minor gap)

`changed_line_ranges` are built from default-context diffs (`git diff`, `gh pr diff --patch`; 3 context lines), not `-U0`. So the effective nearby/in_diff window is ~8 lines instead of 5, and 30-collect-score.md's deletion-hunk rule never fires on real diffs. Fails toward asking (over-asks; never a silent keep); predates Phase 57. Acceptance (from `.planning/phases/57-decision-continuity-within-closure/deferred-items.md`): (a) use `-U0` for every range-building diff, or build ranges from `+`/`-` markers; (b) check nothing else assumes 3-line context; (c) an end-to-end fixture that runs a real `git diff` through the documented hunk rule. Not scheduled.

### 999.25: Finalize `$BLOBFILE` relies on a shell variable across Bash calls (Phase 58 D-22)

`90-finalize.md` builds `$BLOBFILE` in one fence and reuses it as `"$BLOBFILE"` in later fences without printing its path. Shell variables do not survive between Bash calls in Claude Code, so the counts/gate step can see an empty path. Fails safe: Finalize stops and writes nothing. It predates Phase 58; found by the 58-REVIEW-GAPS.md re-review. Fix: bring it under the printed-path rule Phase 58 applied to every other temp file (print `BLOBFILE=<path>`, reuse the literal), with a fence-walk test in a fresh shell and a mutant. Part of the remaining 999.13 reconciliation. Not scheduled.

### 999.26: Plain-English title references: wordier phrasings ask (Phase 58 D-23 known limits)

After the CR-01 rollback (58-REVIEW-FINAL.md), a title reference names a row only when that row's title holds every word the owner used, filler aside. Wordier but clear phrasings ("the retry budget warning", "the Browse recovery issue from earlier", inflections like "retries budget") get one follow-up question with the likely row as a button. This fails safe: nothing is acted on wrongly. The best-unique-match attempt (58-19) was rolled back because it dismissed a row the owner meant to fix. Safer design from the reviewer: act only when the best row contains ALL of the owner's non-filler words (treat small words like on/and/in as filler); otherwise offer the best partial row as a one-click choice in the follow-up. Also carried: tie candidates capped at 4 (a 5th tied row may not appear as a button); on a carried-close-out pass the Close out text points at that pass's card file rather than "the card the owner read"; the fallback note after the subset-file refusal has no specified wording; the "How many" follow-up offers single-row buttons; no Unicode normalization of titles. Reproduce first; any matcher change needs adversarial fixtures that put the target's key word next to two words from another title. Not scheduled.

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
