# Roadmap: vibe-check

Updated 2026-10-28 (v2.14 Decision reliability active: Phases 59–61 mapped to its 16 requirements; Lean orchestration follows, Reviewer efficiency stays conditional; neither activated). Lower-value work stays archived. Each future phase begins by reproducing its failure on current code; a path that does not reproduce is recorded and dropped, never replaced with invented work.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)
- ✅ v2.13 Reliable fix closure and recovery -- Phases 56–58 (shipped 2026-10-28 as 2.13.0; known limits in backlog 999.23–999.26) — [archive](milestones/v2.13-ROADMAP.md)
- 🚧 v2.14 Decision reliability -- Phases 59–61 (in progress)

Active milestone: v2.14 Decision reliability (Phases 59–61). Lean orchestration and Reviewer efficiency are scoped below; backlog records remain the evidence ledger.

### 🚧 v2.14 Decision reliability (Phases 59–61, in progress)

**Goal:** Close stale-decision escape paths, preserve deferred obligations, and make Finalize dependable without changing reviewer coverage or scoring policy.

- [x] **Phase 59: Stale decisions and lost deferrals** - Reproduce CR-01/CR-02/CR-04 and the deferred-member loss on the real chain, then reopen changed decisions with the right reason and keep deferred obligations visible (999.23) (completed 2026-10-29)
- [x] **Phase 60: Exact change evidence and reliable Finalize** - Nearby/in-diff ranges come from actual added/deleted lines on every route, and Finalize's blob-file path survives fresh Bash calls (999.24, 999.25) (completed 2026-10-30)
- [ ] **Phase 61: Release gate — decision reliability** - Regressions, offline suite, archived replay and mode/recovery checks pass on the candidate; residuals and validation gaps are stated; ship through the existing close workflow

**Status:** Activated 2026-10-28 as v2.14 (scope owner-approved the same day; requirements STALE, DEFR, EVID, FINL, GATE in REQUIREMENTS.md). This is a bounded follow-up on 999.23–999.25, not a reopening of v2.13 or Phase 57's exhausted gap-closure rounds.

**Sequence:** Stale decisions are the main priority (Phase 59). Exact diff evidence supports the decision fixes, and the small Finalize path repair rides with it (Phase 60). Release this milestone independently of cost attribution, refactoring or reviewer experiments (Phase 61). Estimated size: medium–large, with uncertainty concentrated in shared decision identity and evidence pooling.

**One-cycle stop rule:** Phase 59 stops after one bounded implementation/review cycle if the shared cause is still unresolved; record residuals and re-scope rather than silently repeat four gap rounds. Unresolved silent keeps block a reliability-complete claim.

**No growth per round (owner, 2026-10-28):** a new review, gap or fix round is not a reason to add points to a task, plan, success criterion or acceptance list. A round may add work only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow — with the reproduction cited. Everything else is carried with its rationale.

**Out of scope:** Cost reporting, orchestration extraction, reviewer/model changes, scoring-formula changes and 999.26 title matching. The safe clarification behavior remains. A non-reproducing historical lead is documented and dropped; the one-cycle stopping rule prevents another open-ended repair campaign.

**Next action:** `/bm:discuss-phase 59` on branch `feat/v2.14-phase-59`. This roadmap does not authorize paid runs.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 59. Stale decisions and lost deferrals | 6/6 | Complete    | 2026-10-29 |
| 60. Exact change evidence and reliable Finalize | 16/16 | Complete    | 2026-10-30 |
| 61. Release gate — decision reliability | 0/5 | Planned | - |

## Phase Details

### Phase 59: Stale decisions and lost deferrals

**Goal**: A decided finding whose evidence changed is asked again with the correct reason, a deliberate decision whose evidence did not change stays decided, and a deferred obligation never disappears without a card (999.23)
**Depends on**: Nothing in v2.14 (first phase). Builds on Phase 57's shipped decision continuity (carried-by-hash index, `deferred_hashes`); do not rebuild it
**Requirements**: STALE-01, STALE-02, STALE-03, STALE-04, STALE-05, STALE-06, DEFR-01, DEFR-02
**Approved scope** (owner, 2026-10-28): Reproduce CR-01, CR-02 and CR-04 against current code through the real score → carry → card → finalize chain: identical sub-threshold copies, absorbed-member sidecars, and a removed guard beside a covered member. Include the valid `min_confidence=45` deferred-member loss. Pool evidence consistently by obligation/hash at the read boundary; do not fix only the latest representative row. Preserve deliberate dismissals when their evidence is unchanged. Investigate the unreproduced SA-02 reviewed-set case once; record and drop it if it does not reproduce. Each fix has a failing-before/passing-after real-chain fixture and a mutation check.
**Success Criteria** (what must be TRUE):

  1. Before any fix lands, CR-01, CR-02, CR-04, the `min_confidence=45` deferred-member loss and SA-02 each have a recorded verdict on current code — a failing real-chain fixture, or a "did not reproduce; dropped" note (SA-02 gets one attempt)
  2. For every reproduced wrong-keep shape, the next run re-asks the decided finding and the card states the correct reopen reason; the result is the same whichever row is the representative and under reordering, lead change, split or merge
  3. A deliberate dismiss/defer stays decided and is not re-asked when an edit leaves its existing decision-evidence fingerprint unchanged; the agreed five-line invalidation rule is preserved as-is (no new semantic "related/unrelated" classification)
  4. A deferred covered member removed by a valid `min_confidence` (45) — and the SA-02 `--all` case if it reproduced — stays visible as an open deferred obligation instead of disappearing without a card
  5. The phase ends after one bounded implementation/review cycle; any unresolved silent keep is recorded as a residual and blocks a "reliability complete" claim rather than starting another repair round

**Plans**: 6 plans (6 sequential waves — every plan touches test_decision_continuity.py)

Plans:
**Wave 1**

- [x] 59-01-PLAN.md — Red real-chain fixtures for CR-01 (edit@33 + multi-pass), CR-02, CR-04, DEFR-01@45; SA-02 prose pin; REPRO_59; 59-REPRO.md ledger (no production edits)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 59-02-PLAN.md — score.py producers: kept-open pooling over carried_by_hash + per-occurrence rows (CR-01); row_nearby over carried copies + covered members (CR-04, D-21); p4 rewrite; mutants re-anchored

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 59-03-PLAN.md — DEFR-01 D-20 synthesis on the min_confidence branch (numbered reason); carry_state `_merge_nearby` read-side merge (CR-02); mutants

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 59-04-PLAN.md — Spot data: `nearby_spots` on snapshots (score.py), read-time copy spot + `carry_state.stale_spots` reader

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 59-05-PLAN.md — Card wording D-04/D-05/D-06 in batch_card + both prose files + prose-lock and real-chain card tests

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 59-06-PLAN.md — STALE-05 invariance scenarios; full suite + replay + reverse run; ledger green SHAs; residuals (D-02/D-03/D-07/D-09) to 59-REPRO.md and 999.23

### Phase 60: Exact change evidence and reliable Finalize

**Goal**: The nearby window is exactly what the decision rules say on every review route, and Finalize either completes from a fresh shell or stops safely without writing (999.24, 999.25)
**Depends on**: Phase 59 (same score → carry → card chain; one branch/PR per phase from `main`)
**Requirements**: EVID-01, EVID-02, EVID-03, FINL-01, FINL-02
**Approved scope** (owner, 2026-10-28): Build evidence ranges from actual additions/deletions, independently of human-readable diff context; test ordinary, deletion-only and insertion hunks, including relocated findings. Make Finalize's blob-file path explicit across fresh Bash calls using the established printed-path convention before broader extraction. Preserve snapshot freshness and no-write-on-failure behavior; do not weaken independent fix verification.
**Success Criteria** (what must be TRUE):

  1. An edit at the intended five-line boundary reopens a decision and an edit just outside it does not, because ranges come only from added/deleted lines, not display context
  2. Fixtures that run a real `git diff` produce correct ranges for ordinary, deletion-only and insertion hunks and for relocated findings
  3. Default, GSD, range, PR and `--all` routes each use the exact ranges or explicitly report an unsupported fixture, and nothing else in the pipeline still assumes three lines of context
  4. A fresh-shell walk through every Finalize fence reaches counts → gate → report using the printed, literally reused blob-file path
  5. A failed or refused attempt (including a missing path) stops and writes no final report; a successful retry may complete after revalidating snapshot freshness; no-write-on-failure and independent fix verification are unchanged

**Plans:** 16/16 plans complete

Plans:
**Wave 1**

- [x] 60-01-PLAN.md — Reproduction verdicts: red real-diff/coordinate/Finalize-walk fixtures, REPRO_60, 60-REPRO.md (RED SHA)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 60-02-PLAN.md — diff_ranges.py marker-walk range builder (D-01/D-02) + test_diff_ranges.py with mutants and the replay.hunk_ranges pin
- [x] 60-03-PLAN.md — Finalize: printed BLOBFILE=/GATEFILE= fences, rebuild-once and refused-step rules, fresh-shell walk, widened printed-path lock

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 60-04-PLAN.md — Route wiring: 30-collect-score range fence per route, PR cumulative fixture, route tests, --all record, D-04 audit, test_nv_render retarget

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 60-05-PLAN.md — Close the cycle: full suite, replay, reverse run at the RED SHA, ledger green SHAs, residuals, ROADMAP/REQUIREMENTS

**Gap closure** *(60-VERIFICATION gaps_found at 2f84d2e)*

- [x] 60-06-PLAN.md — diff_ranges reads suppressBlankEmpty context, refuses colored/non-diff text
- [x] 60-07-PLAN.md — GSD/incremental range source as a quoted literal sha; PHASE_START= printed; six fixed diff flags
- [x] 60-08-PLAN.md — Finalize rebuild re-mints GATEFILE from the rebuilt counts
- [x] 60-09-PLAN.md — gap-round ledger, record and traceability

**Gap closure, second round** *(60-VERIFICATION re-verification gaps_found at f2b58d1: CR-01, WR-02)*

- [x] 60-10-PLAN.md — carry_state last-head-sha: the substituted head_sha is a validated 40/64-hex commit id (CR-01 helper)
- [x] 60-11-PLAN.md — head_sha and PHASE_START bound through validating fences; only printed literals are substituted (CR-01 prose)
- [x] 60-12-PLAN.md — Finalize step 3 re-mints GATEFILE from the recounted counts (WR-02)
- [x] 60-13-PLAN.md — second-round ledger, record and traceability

**Gap closure, third round** *(60-VERIFICATION re-verification round 2 gaps_found at 2de0fc9: WR-01, WR-02 on FINL-02)*

- [x] 60-14-PLAN.md — Finalize step 3 re-fingerprints HEAD into a NEW BLOBFILE before the post-answer recount (WR-01)
- [x] 60-15-PLAN.md — head_sha bind fence skips on the printed FINALIZE_MODE=1 literal and names a remedy on halt (WR-02)
- [x] 60-16-PLAN.md — third-round ledger, record and traceability

### Phase 61: Release gate — decision reliability

**Goal**: The release candidate is proven against the accepted scope with nothing unrelated changed, its limits are stated plainly, and it ships through the existing close workflow without waiting for Lean orchestration
**Depends on**: Phase 60
**Requirements**: GATE-01, GATE-02, GATE-03
**Approved scope** (owner, 2026-10-28): Run targeted real-chain regressions, the full applicable offline suite, archived replay and mode/recovery integration checks against the candidate. Allow replay differences only for named, expected reopening/retention repairs. Any required live checks need a bounded approved proposal; if unavailable, document the validation gap and obtain a release waiver rather than claim end-to-end model quality.
**Success Criteria** (what must be TRUE):

  1. On the release candidate, the targeted real-chain regressions, the full offline suite and the mode/recovery integration checks pass
  2. Archived replay differs only in the named, expected reopen/retention repairs; any unrelated change in detection, filtering or closure blocks release
  3. The release record states unsupported fixtures, residuals and any validation gap explicitly; live checks ran only under an approved bounded proposal, otherwise the gap is documented with an owner waiver, and the milestone ships through the existing close workflow

**Plans:** 5 plans (3 waves)

Plans:
**Wave 1**

- [ ] 61-01-PLAN.md — Release candidate C: plugin 2.14.0 + fact-checked README release section; suite on the edited tree; candidate SHA recorded (D-12)
- [ ] 61-02-PLAN.md — Bounded live-smoke proposal and owner approve/decline before any spend (D-01/D-02)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 61-03-PLAN.md — Gates G1-G9 on C: full suite, real-chain and mode/recovery selectors, archived replay vs 2.13 (no allowances), D-03 live PR fetch, manifest, stdlib scan; D-11 route map
- [ ] 61-04-PLAN.md — Live smoke on a sealed snapshot of C (default route + --finalize, tmux, cache parity, restored after) — or NOT RUN gap for waiver

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 61-05-PLAN.md — Release record, 2.14.0 notes (Known limits), close runbook with tree-identity check, one-page owner sign-off (publish pending close)

## Following milestone: Lean orchestration

**Codex integration decision (owner, 2026-10-28):** Retain the existing optional OpenAI Codex plugin/companion integration. Lean orchestration simplifies vibe-check's own mechanics; it does not replace or vendor the companion, build a direct Codex adapter, or adopt model-gateway/agent-spawn routing. Keep the user's configured Codex default, not a pinned Astra model. Small dependency/setup, run/skip disclosure, model-label and update-compatibility improvements are captured in [maintenance](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure); they add no phase, requirement, acceptance criterion or release blocker to v2.14.

**Goal:** Reduce model-interpreted mechanical instructions and fragile handoffs while preserving the behavior delivered by Decision reliability.

**Prerequisite:** Decision reliability has passed its release gate and shipped. This is the agreed second milestone, not active work. Estimated size: medium with Finalize as the initial implementation boundary.

1. [ ] **P1 — Baseline cost and quality with existing evidence (999.12, bounded feasibility).** Inspect local archives only; identify trustworthy per-run/per-lane model, input/output/cache usage, retries and elapsed time where present. Report missing attribution explicitly; do not reconstruct invented usage or treat subscription usage as a bill. Record current mode-path bytes and actual loaded-file traces separately from token and price estimates. Retain a pinned current-code behavioral baseline and archived replay results before refactoring. **Done when:** a go/no-go note names available fields, the smallest useful report, the intended comparison workload, and the improvement criterion chosen before implementation. If reliable attribution is unavailable, stop accounting work and use clearly labeled footprint/operation counts. No new telemetry service, accounting platform, paid baseline or enforceable-dollar-cap claim.

2. [ ] **Finalize extraction first.** Reuse existing stdlib helpers and the single-writer state path to assemble Finalize inputs and perform the gate/report handoff. Return compact structured results and explicit next actions. Keep judgment, owner decisions and reviewer calls in the existing host; remove superseded prose and locks while retaining behavioral invariants and recovery guidance. **Done when:** equivalent inputs produce the same gate decisions and reports as the released Decision reliability baseline; missing, malformed or stale inputs fail visibly; restart/retry works across fresh shells. Compare loaded prose and helper/tool steps on the same paths before and after. Revert the slice if it adds complexity without demonstrable benefit. No new orchestration framework, wholesale state rewrite or changed model defaults.

3. [ ] **Optional bounded extension after Finalize proves useful.** Only consider repeated evidence/envelope assembly or deterministic dispatch selection when the first extraction passes equivalence checks and the baseline identifies another worthwhile source of repeated work. Choose at most one additional family during detailed scoping; defer the remainder rather than grow the milestone. **Done when:** the selected slice preserves roster, prompts/evidence, scores, decision eligibility and recovery behavior, with demonstrated footprint/operation savings. Skip this item if the first slice is inconclusive; Finalize alone can satisfy the milestone.

4. [ ] **Release gate — orchestration equivalence and useful savings.** Run the applicable full offline suite, archived replay and mode/recovery integration checks on the exact candidate, comparing against the released reliability baseline. Unexpected behavioral differences block release. **Done when:** safeguards and independent fix verification remain intact and the included extraction demonstrably reduces loaded prose or mechanical work without an unaccounted regression. Report byte/operation savings separately from tokens or dollars; claim billing savings only with comparable usage evidence. Any approved live validation covers changed orchestration paths under the default configuration; offline parity alone does not prove live model quality. Document any unmeasured behavior and require an explicit release waiver if needed. Publish independently; reviewer-efficiency experiments are not a prerequisite.

**Out of scope:** Reviewer routing, narrower reviewer context, new agents, model downgrades, scoring retunes, new services and broad cleanup. Missing cost attribution ends accounting work, not the milestone; use labeled footprint/operation evidence instead.

## Future milestone: Reviewer efficiency (conditional)

**Goal:** Reduce review usage or latency only where a bounded experiment demonstrates that expected defect detection and false-alarm behavior are preserved.

**Activation:** Decision reliability and Lean orchestration have shipped; attributable costs or a reproduced repeated-work case identify a meaningful target; the owner approves a bounded comparison proposal and any paid runs. No phase numbers or implementation commitment before this gate. Size remains unknown until one experiment is selected.

1. [ ] **Select one evidence-backed experiment.** Compare architecture/impact routing, targeted fix rechecks with dependency/snapshot invalidation, OR narrower specialist context; do not bundle interventions. Preserve bugs/security coverage and independent confirmation, and fall back to existing coverage when impact is uncertain. Check actual cache-read/write fields instead of assuming parallel dispatch shares a cache. Predeclare the baseline, model/configuration/cache conditions, fresh defect/clean cases, repeats and useful savings threshold before running. Include large/cross-file changes and repair journeys; preserve sealed evaluation access boundaries.

2. [ ] **Go/no-go and release gate — measured efficiency without quality loss.** An independently scored comparison must show no lost expected catches, no added false-alarm runs and useful measured usage/latency improvement against the incumbent on the predeclared workload. Run offline and mode/recovery regressions for the candidate too. Report small-sample limits and exact artifact/model identities. Reject or defer inconclusive variants and retain the incumbent; no paid approval means no experiment and no quality-equivalence claim. Release only a passing variant through the existing close workflow. The earlier milestones remain complete regardless of this outcome.

**Out of scope:** Automatic model downgrades based only on diff size, persistence weighting or severity retunes, broader reviewer replacement and new accounting infrastructure. Persistence-as-second-opinion remains a separate hypothesis needing its own bounded proposal; this sequence does not authorize scorer changes.

## Sequence rationale and evidence

Wrong-keeps and deferral loss undermine the core gate, so their repair ships first. Finalize recovery is a small prerequisite repair, distinct from its later extraction. Cost feasibility and a Finalize-only refactor keep the second milestone bounded. Reviewer changes have uncertain marginal value and stay conditional. Each milestone owns its verification and release; no later experiment delays earlier correctness work. Keep 999.26, generic cleanup, broad duplicate reduction and Phase 55/holdout sweeps deferred.

**Baseline evidence (2026-10-28):** Checkout `f2b6a36` / plugin 2.13.0. `footprint.py` reports plain review 176,528 bytes, plain deep review 253,468, Finalize 124,587 (mode inventories, conditional upper bounds; not billed tokens). The [v2.10 report](../docs/design/prose-diet-footprint-v2.10.md) recorded 110,616 / 173,982 / 64,015 respectively. The last measured efficacy remains v2.11's 5/18 quiet-run alarms and 15/15 catch runs, a MISS on its registered bar; repeated runs are not independent defects. No current-release accuracy or savings percentage is established.

## Backlog

### 999.23: Decision continuity known limits (Phase 57 close, D-19/D-22)

Phase 57 closed under the owner's D-19 hard stop with these reproduced defects carried, not fixed. Full repros: `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/57-REVIEW-GAPS4.md` and `deferred-items.md`.

- **Wrong-keeps (decision stays current after its evidence changed):**
  - CR-01: same-hash copies kept open below threshold are not pooled. Two identical `return None` lines at 10 and 30, dismissed; an edit at 33 leaves the decision current. Zero-config.
  - CR-02: absorbed-member obligation sidecars are not pooled; carry_state reads the first sidecar.
  - CR-04 (predates the gap rounds): removing a guard beside a covered member never re-asks the row decision while the member stays in the row (D-14's "guarded upstream" case).
- **Over-ask to align under D-21:** an edit beside a NEW identical copy re-asks the decided copy at pass 3 (test_p4 locks the old behaviour); round-4 WR-01: a member that joined a deferred row after the deferral is kept open at the deferred row's band.
- **Deferral loss (D-20 edges):** min_confidence (valid 1–49; repro must use ≤49, e.g. 45) removing a deferred covered member drops it without a card; SA-02 `--all` `not-in-reviewed-set` drop (not reproduced — reproduce first).

Root-cause direction (from the review): pool `carried_by_hash` into `_kept_open_rows` and the member-sidecar path, and make carry_state's per-hash read merge records instead of keeping the first. Reproduce first; each fix needs a real-chain fixture and a mutant. Scheduled as v2.14 Phase 59 (Decision reliability); active. Retain this record and its original evidence.

**Carried from Phase 59 (2026-10-28):** CR-01, CR-01 multi-pass, CR-02, CR-04 and the min_confidence=45 deferral loss were fixed in Phase 59 (fixtures in test_decision_continuity.TestStaleDecisions59 / TestDeferredStaysOpen; ledger 59-REPRO.md). Still carried, each with its acceptance repro:

- D-01 later-pass over-ask (D-02): pass 1 decide hA (`bugs` @10); pass 2 a NEW identical copy at line 30 (fresh) with no nearby edit; pass 3 edit@33 -> stale/nearby. Fails toward asking; a fix needs a per-copy origin marker (snapshot `since_pass` compared to the decision's `at_pass`).
- WR-01 over-ask #2 (D-03): a member that joined a deferred row after the deferral is kept open at the row's band (repro in 57-REVIEW-GAPS4.md).
- SA-02 `--all` drop (D-07): did not reproduce on the real chain; dropped, pinned by `test_nv_render.all_carryforward_bypass_holds`; reopen only if `05-state-all.md` (ii) changes.
- WR-01 card names only the other spot (owner parked 2026-10-29): when one pass edits beside BOTH the row's own decided line and another copy/grouped member, the decision reopens correctly but the card names only the other spot (`_nearby_spots` always excludes the row's own line; 90-finalize.md "lowest changed line" sentence is false in this case). Repro: cr01_scenario with diff ranges [[12,12],[33,33]] — card names line 30, never line 12. Wording only; no silent keep. See 59-REVIEW.md WR-01 / 59-VERIFICATION.md.
- WR-02 "still deferred" note drops after one pass (owner parked 2026-10-29): the D-06 `below your min_confidence (45); still deferred` note shows on the first drop pass only; from pass 3 the row stays open (Finalize still held) but carries the plain `below-min-confidence` reason. Wording only; the obligation stays visible. See 59-REVIEW.md WR-02.

### 999.24: Diff context widens the nearby window (Phase 57 SC-3 minor gap)

`changed_line_ranges` are built from default-context diffs (`git diff`, `gh pr diff --patch`; 3 context lines), not `-U0`. So the effective nearby/in_diff window is ~8 lines instead of 5, and 30-collect-score.md's deletion-hunk rule never fires on real diffs. Fails toward asking (over-asks; never a silent keep); predates Phase 57. Acceptance (from `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/deferred-items.md`): (a) use `-U0` for every range-building diff, or build ranges from `+`/`-` markers; (b) check nothing else assumes 3-line context; (c) an end-to-end fixture that runs a real `git diff` through the documented hunk rule. Scheduled as v2.14 Phase 60 (Decision reliability); active.

**Carried from Phase 60 (2026-10-29):** These shapes reproduced at the RED SHA `ce9f8b8` and were fixed in Phase 60: the ~8-line widening, the deletion rule that never fired, the net-deletion boundary keep, the PR commit-series numbering, the GSD/incremental mixed-coordinate concatenation (a silent keep) and the default route's staged index numbering. Ranges are now built only from `+`/`-` body lines by `scripts/diff_ranges.py` (53fb637). Each route has one range source through that builder (66d63de), and route tests cover default, GSD, incremental, range, PR (on a real `gh pr diff` capture) and `--all` (39f6dbd, fb8b32b). The reverse run at `ce9f8b8` fails all 14 range fixtures. At close the full suite passes and replay shows no deltas (60-REPRO.md). The verification gap round (60-06/60-07) then fixed the GSD/incremental fresh-shell range source (now a quoted literal sha, b1bc970 -> 2a63cb5) and config-altered diffs (suppressBlankEmpty, color, textconv, relative; 11d2b76 -> b878870 + 2a63cb5), 60-REPRO.md V10-V11; EVID-03 awaits re-verification. The re-verification's second gap round (60-10/60-11) closed CR-01: the GSD / pass ≥ 2 revision is bound through fences that refuse anything but a commit id, so a crafted `head_sha` in a committed state file can no longer run a command (ae560fe + 5d81170, 60-REPRO.md V13); EVID-03 awaits re-verification. EVID-03 was verified Complete on 2026-10-30. Still carried, each with its rationale in 60-REPRO.md §Residuals:

- R6 known limit: the live `gh pr diff` fetch was not exercised (D-05); the PR route is proven on a checked-in capture only. Phase 61 names it in the release record.
- R5: the installed plugin cache runs the old prose until resync and relaunch. Phase 61 checks the install (or `--plugin-dir`) before any manual check.
- R3: the agents' diff views are unchanged (PR reviewers still read `--patch`); only the range source changed. Whether reviewers number lines from commit coordinates is not reproduced; reproduce first.
- R17 owner-accepted known limit (2026-10-30, 60-HUMAN-UAT test 2): the PR route fails closed on PRs above GitHub's diff limits (about 300+ files or 20k+ lines). No fallback; Phase 61 names it in the release record.
- R4: old `nearby_at` stamps from wider ranges are not migrated (fails toward asking). R7: untracked files have no ranges (unchanged). R8: C-quoted paths give no ranges (cannot carry a finding under `PATH_RE`). R10: `--all` has no diff (an unsupported fixture, `TestRouteAll`). R11: `replay.hunk_ranges` stays context-inclusive on purpose (`TestReplayPin`, GATE-02).

### 999.25: Finalize `$BLOBFILE` relies on a shell variable across Bash calls (Phase 58 D-22)

`90-finalize.md` builds `$BLOBFILE` in one fence and reuses it as `"$BLOBFILE"` in later fences without printing its path. Shell variables do not survive between Bash calls in Claude Code, so the counts/gate step can see an empty path. Fails safe: Finalize stops and writes nothing. It predates Phase 58; found by the 58-REVIEW-GAPS.md re-review. Fix: bring it under the printed-path rule Phase 58 applied to every other temp file (print `BLOBFILE=<path>`, reuse the literal), with a fence-walk test in a fresh shell and a mutant. Part of the remaining 999.13 reconciliation. Scheduled as v2.14 Phase 60 (Decision reliability); active.

**Carried from Phase 60 (2026-10-29):** These defects reproduced at `ce9f8b8` and were fixed in Phase 60: the cross-call `$BLOBFILE` and the gate fence's cross-call `$FINALIZE_GATE_INPUT_JSON`. Step 1 now prints `BLOBFILE=`, the gate reads a printed `GATEFILE=`, and every later fence reuses the literal. A missing path or a failed step gets one rebuild with a new blob file, then stops with one sentence and writes nothing. A refused step is never retried (b8fb21a). Fresh-shell walks over the real fences reach `write` and the decisions report on both routes, with retry, stale-attempt and malformed-GATEFILE walks (fd8c1b9). The printed-path, created-before-read and no-cross-call locks have mutants (53b35ed). The reverse run at `ce9f8b8` fails the walk and every 60-03 lock. The write boundary and independent fix verification are unchanged (`write_boundary_holds`; `test_fix_loop_card.py` green). The verification gap round (60-08) made the one rebuild re-mint GATEFILE and write the flags from the rebuilt counts (f100185 -> c0ece7e), 60-REPRO.md V12; FINL-02 awaits re-verification. The second gap round (60-12) made the post-answer gate re-run write a new GATEFILE from the recounted counts, so a card answer that dismisses every obligation finalizes in the same turn (c112ca6, 60-REPRO.md V14); FINL-02 awaits re-verification. The third gap round (60-14, 60-15) made the post-answer recount re-fingerprint HEAD into a NEW BLOBFILE, so a file edited while the card was open reopens its fix-obsolete finding instead of being approved over (9b3f055, 60-REPRO.md V15), and exempted `--finalize` from the head_sha bind fence it never consumes while naming a remedy on the review-mode halt (07bb448, V16); FINL-02 awaits re-verification. Still carried:

- R1: `finalize_gate.py` itself still prints a Python traceback on empty or malformed stdin (helper unchanged). The fence keeps it in `<GATEFILE>.err`, so the owner sees only the stop sentence (`test_malformed_gatefile_shows_only_stop_sentence`). This is helper-side only. If the helper is ever called outside that fence, give it a fixed one-line refusal.
- R5: as for 999.24, the installed plugin cache runs the old Finalize prose until resync and relaunch.

### 999.26: Plain-English title references: wordier phrasings ask (Phase 58 D-23 known limits)

After the CR-01 rollback (58-REVIEW-FINAL.md), a title reference names a row only when that row's title holds every word the owner used, filler aside. Wordier but clear phrasings ("the retry budget warning", "the Browse recovery issue from earlier", inflections like "retries budget") get one follow-up question with the likely row as a button. This fails safe: nothing is acted on wrongly. The best-unique-match attempt (58-19) was rolled back because it dismissed a row the owner meant to fix. Safer design from the reviewer: act only when the best row contains ALL of the owner's non-filler words (treat small words like on/and/in as filler); otherwise offer the best partial row as a one-click choice in the follow-up. Also carried: tie candidates capped at 4 (a 5th tied row may not appear as a button); on a carried-close-out pass the Close out text points at that pass's card file rather than "the card the owner read"; the fallback note after the subset-file refusal has no specified wording; the "How many" follow-up offers single-row buttons; no Unicode normalization of titles. Reproduce first; any matcher change needs adversarial fixtures that put the target's key word next to two words from another title. Not scheduled.

### 999.27: Committed state file's `head_sha` can narrow the pass >= 2 review range (Phase 60 R25)

A well-formed but crafted 40- or 64-hex `head_sha` committed into the reviewed repo's state file passes `carry_state.py last-head-sha` and can narrow the incremental (pass >= 2) range without telling the owner. Phase 60's CR-01 fix closed command injection, not scope trust. Owner ruling 2026-10-30 (60-HUMAN-UAT test 3): status quo accepted for v2.14; hardening deferred. Candidate direction: require the stored sha to be an ancestor of HEAD and state the narrowed range on the card. Also consider R26 (no write-side format check on `head_sha`). Reproduce on a real review first. Needs exploitation by someone who can commit to the repo. Not scheduled.

### 999.12: Narrow: Cost visibility feasibility — Lean orchestration

Inspect existing local usage records to determine whether a review's usage can be attributed reliably. Report available fields, missing data, pricing assumptions and the distinction between estimated, measured and billed cost. Do not start paid reviews to generate a baseline or invent per-agent usage.

Finish with a go/no-go recommendation for the smallest useful reporting change. Stop if reliable attribution is unavailable; document the limitation rather than build new accounting infrastructure. Existing chunk limits and estimates are not enforceable dollar caps. Scheduled as Lean orchestration item 1, after Decision reliability ships; not activated. This check does not block correctness repairs; missing attribution stops accounting work, not the reliability milestone. Budget-control implementation and cross-repo orchestration changes require their own scope.

### Maintenance: Keep the Codex companion; improve setup and disclosure

Owner decision 2026-10-28: retain the existing optional Codex plugin integration. Capture dependency/setup documentation, accurate joined/skipped outcomes, configured-default model labels and bounded compatibility checks after companion updates in [the maintenance record](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure). Outside v2.14; no new milestone or integration redesign. Preserve current review targeting, guards and optional native-only behavior.

## Planning boundaries

- v2.14 Decision reliability is the only active milestone. Paid runs, new agents and publication require explicit owner approval; this roadmap does not authorize them.
- v2.13 shipped as 2.13.0 with owner-accepted known limits (999.23–999.26); Phase 57 closed under the D-19 hard stop, Phase 58 with live ref extraction unverified (D-15).
- v2.12 shipped as 2.12.0 under owner waiver; outcome remains **UNMET — measurement incomplete**. Phase 55 and cancelled Phase 54 sweeps remain deferred.
- Reuse valid review evidence for unchanged code; scope new checks to changed code and affected callers. Any paid check requires an explicit bounded price proposal and owner approval.
- One branch and one PR per phase (owner decision 2026-10-23): `feat/<milestone>-phase-<N>`, each cut from `main` after the previous phase's PR merges; delete each branch locally and on GitHub after its PR merges.
- Routine cleanup remains in [maintenance](backlog/MAINTENANCE.md).
- [Lower-value ROI candidates](backlog/archive/2026-10-18/ROI-DEFERRED.md) are archived with reopening conditions, not scheduled or declared complete.

## Release records

- [v2.13 archived roadmap](milestones/v2.13-ROADMAP.md): reliable fix closure, decision continuity and recovery; known limits 999.23–999.26.
- [v2.12 archived roadmap](milestones/v2.12-ROADMAP.md): shipped reliability improvements; measurement incomplete.
- [v2.11 archived roadmap](milestones/v2.11-ROADMAP.md): last measured milestone, false alarms 5/18 and catches 15/15, with release/measurement caveats.
- [All milestone history](MILESTONES.md).
- [Archived backlog and disposition ledger](backlog/archive/2026-10-18/README.md).
