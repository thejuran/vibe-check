# Roadmap: vibe-check

Updated 2026-11-16 (v2.16 Publication readiness activated: Phases 66-71 roadmapped from REQUIREMENTS.md, 18/18 requirements mapped; nothing implemented. v2.15 Lean orchestration shipped as 2.15.0: PR #12 squash `d5acc19`, tag `v2.15` on origin/main, GitHub release v2.15 (Latest); audit tech_debt 17/17). Each phase begins by reproducing its failure, or recording the behaviour or measurement it intends to change, on current code. A path that does not reproduce is recorded and dropped, never replaced with invented work.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)
- ✅ v2.13 Reliable fix closure and recovery -- Phases 56–58 (shipped 2026-10-28 as 2.13.0; known limits in backlog 999.23–999.26) — [archive](milestones/v2.13-ROADMAP.md)
- ✅ v2.14 Decision reliability -- Phases 59–61 (shipped as 2.14.0; 2.14.1 patch fixed 999.28; known limits 999.23 residuals, 999.26, 999.27, 999.29, 999.30) — [archive](milestones/v2.14-ROADMAP.md) (shipped 2026-10-30)
- ✅ v2.15 Lean orchestration -- Phases 62–65 (shipped as 2.15.0; known limits 999.34–999.39) — [archive](milestones/v2.15-ROADMAP.md) (shipped 2026-11-16)
- 🚧 v2.16 Publication readiness -- Phases 66-71 (in progress)

<details>
<summary>✅ v2.14 Decision reliability (Phases 59–61) — SHIPPED 2026-10-30</summary>

- [x] Phase 59: Stale decisions and lost deferrals (6/6 plans) — completed 2026-10-29
- [x] Phase 60: Exact change evidence and reliable Finalize (16/16 plans) — completed 2026-10-30
- [x] Phase 61: Release gate — decision reliability (5/5 plans) — completed 2026-10-30

Shipped as 2.14.0 via release PR #7 (squash `ecc3299`, tag `v2.14`, GitHub release v2.14). Audit tech_debt 16/16 ([audit](milestones/v2.14-MILESTONE-AUDIT.md)). Details: [archive](milestones/v2.14-ROADMAP.md).

</details>

<details>
<summary>✅ v2.15 Lean orchestration (Phases 62–65) — SHIPPED 2026-11-16</summary>

- [x] **Phase 62: Baseline and continuous test run** - 2.14.1 baseline pinned, cost visibility NO-GO (owner), offline suite on every push and PR to `main` (11/11 plans) — completed 2026-11-14
- [x] **Phase 63: Finalize extraction and cross-call variable check** - Finalize's gate inputs from one tested stdlib helper (92 → 83 steps on the extraction alone); one general cross-call variable check (11/11 plans) — completed 2026-11-15
- [x] **Phase 64: Optional bounded extension (conditional)** - Closed as a recorded skip (owner); evidence/envelope assembly, dispatch selection and 999.32 deferred — completed 2026-11-15
- [x] **Phase 65: Release gate — orchestration equivalence and useful savings** - G1–G11 PASS on candidate `b073e31`; replay 170 runs, 0 differences; live smoke PASS; Close out 136,114 → 131,381 bytes, 92 → 85 steps (7/7 plans) — completed 2026-11-17

Audit tech_debt, 17/17 requirements, integration 7/7, flows 2/2 ([audit](milestones/v2.15-MILESTONE-AUDIT.md)). Full phase details: [archive](milestones/v2.15-ROADMAP.md). Known limits and carried review items: 999.34–999.39. Shipped as 2.15.0 via release PR #12 squash `d5acc19`, tag `v2.15` on origin/main, GitHub release v2.15 (Latest).

</details>

### 🚧 v2.16 Publication readiness (Phases 66-71, in progress)

- [ ] **Phase 66: Close out freshness** - Close out refuses stale deferred/dismissed decisions and asks for a fresh review; the three legacy wrong-keep shapes get repair, safe refusal or recorded non-reproduction (999.40, 999.44)
- [ ] **Phase 67: Trusted incremental scope** - A crafted commit id in repository state cannot hide a committed change from an incremental review; the effective range is shown (999.27)
- [ ] **Phase 68: Unambiguous phase and scope binding** - Ambiguous phase names and container names are refused before state is touched; narrowed `--all`, colliding branch keys and PR/range identities get explicit outcomes (999.39 SA-01/WR-01, 999.45)
- [ ] **Phase 69: Safe helper invocation** - Repository Python startup code cannot run through helper or hook calls; empty or missing helper paths refuse (999.43)
- [ ] **Phase 70: Submission packaging and truthful claims** - Plugin-folder README, Python and companion setup docs, configured-default Codex labels, 12/15 beside 15/15, cost-estimate clarity, candidate check record (999.41)
- [ ] **Phase 71: Release gate — publication readiness** - Reproduction/regression evidence per repair, offline suite and replay against 2.15.0 on the exact candidate, offline and live evidence recorded separately, ship via the existing close-and-publish workflow; no portal submission (GATE-07..09)

**Milestone goal:** Make Close out and review scope trustworthy before Claude developer-portal submission, with the smallest correctness and packaging changes. Owner requested the underlying roadmap update on 2026-11-16 after a read-only assessment of 2.15.0 at `c1461c5e`; activated as v2.16 the same day via `/bm:new-milestone` (baseline plugin 2.15.0, `d5acc19`). Each phase begins by reproducing its failure on 2.15.0 current code; a lead that does not reproduce is recorded with evidence and dropped, never replaced with invented work.

**Finish line:** Targeted failing reproductions pass after the repairs; unchanged-code decision/scoring behavior and affected mode/recovery paths remain covered; candidate packaging and documentation agree. The bounded checks in 999.44/999.45 must have explicit repair, safe refusal, or evidence-backed non-reproduction outcomes; a historical waiver alone is insufficient. Record offline versus live evidence separately. Portal submission is recommended only after these repairs and a successful candidate validation; submission itself is not authorized by this milestone.

**Exclusions:** No decision-identity redesign (999.31), new reviewer lanes, scorer retuning, Codex replacement, accounting infrastructure, broad orchestration refactor or new efficacy campaign. Empty-card Rerun handling (999.32), shared card plumbing (999.35), snapshot pruning (999.30), and Needs debugging (999.42) can ship later. Paid tests need separate bounded approval. Sandboxing arbitrary interpreters, git/node configuration or the OS is out of scope. No general state-format migration. Keep the shipped v2.15 milestone complete.

### Phase 66: Close out freshness

**Goal**: Close out never completes on a deferred or dismissed decision whose reviewed code changed since the review, and the three bounded legacy wrong-keep shapes each end with an evidence-backed outcome.
**Depends on**: Nothing (first phase of v2.16; branch `feat/v2.16-phase-66` from `main` at 2.15.0)
**Requirements**: FRESH-01, FRESH-02, FRESH-03
**Backlog**: 999.40, 999.44
**Success Criteria** (what must be TRUE):

  1. The 999.40 assessment reproduction (defer or dismiss a finding, change the decided source line, run Close out) is first re-created as a fixture that fails on 2.15.0 code; after the repair, Close out refuses for both decision kinds on an exact-line edit and on a nearby edit, tells the user to run a fresh review, and never starts a paid reviewer on its own.
  2. With the reviewed code unchanged, Close out still completes for both decision kinds exactly as on 2.15.0; fix-verdict freshness, 999.28 unchanged-worktree score parity and real-edit reopening tests all still pass.
  3. Each of the three 999.44 shapes (deleted-original relocation with identical text elsewhere, an older covering decision winning over a newer one, untracked files without change ranges) has a recorded outcome: a reproduced wrong keep repaired, the unsupported decision safely refused, or non-reproduction recorded with its counterexample or control. The D-21 identical-copy addition is distinguished from deleted-original relocation. No decision-identity redesign.
  4. Replay against 2.15.0 differs only by the intended refusals; every other run is unchanged.

**Plans:** 12 plans (9 executed; 3 gap-closure plans for the 999.44 shape 1 repair, planned 2026-11-18)

Plans:
**Wave 1**

- [x] 66-01-PLAN.md — RED: 999.40 reproduction fixture + v2.15 (d5acc19) materializer + closeout_fresh contract skeleton
- [x] 66-02-PLAN.md — Re-home ~48 decision-bearing Finalize fixtures and the parity grid onto real reviewed trees
- [x] 66-05-PLAN.md — --all records reviewed_tree (D-12): take/collect/persist prose + locks + real-chain test

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 66-03-PLAN.md — TDD: closeout_fresh.stale_decisions (reverse diff, window, delete/rename, untracked, fail closed) + mutation checks 2-7
- [x] 66-07-PLAN.md — 999.44 shape 1 deleted-original relocation vs D-21: repro, bounded re-ask or D-10 record (conditional owner checkpoint on BOUND-EXCEEDED)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 66-04-PLAN.md — Wire the refusal into finalize_inputs (stop-review-again), render it in 90-finalize.md, mutation checks 1/8/9
- [x] 66-08-PLAN.md — 999.44 shape 2 covering order: producibility through record_decisions, repair or counterexample (owner checkpoint before any carry_state.py edit)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 66-06-PLAN.md — Loop-freedom: every refusal cause clearable (D-16); 999.44 shape 3 untracked (D-13); PR/range disk outcome (D-15)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 66-09-PLAN.md — Replay vs 2.15.0, only_intended differential, full suite + stdlib, backlog/validation records

**Gap closure** *(SC3 / FRESH-03, 999.44 shape 1: owner chose the wider repair on 2026-11-18; runs with `/bm:execute-phase 66 --gaps-only`, one plan per wave in this order)*

- [x] 66-10-PLAN.md — `worktree_snap.py collect` also reports reviewed-side lines removed since the review; two-sided differential vs 2.15.0 and mutation checks
- [ ] 66-11-PLAN.md — Review step 0/2 prose and simulator re-ask a decision moved off a removed line; shape 1 tests pass without expectedFailure; differential vs literal 2.15.0 and mutation checks
- [ ] 66-12-PLAN.md — Shape 1 end to end through the real fences and Close out; full suite, stdlib, replay vs 2.15.0; 999.44 / validation / replay records

### Phase 67: Trusted incremental scope

**Goal**: Repository-controlled state cannot silently narrow the base of an incremental review, and the user sees the effective review range.
**Depends on**: Phase 66 (sequencing only: one branch and PR per phase, cut from `main` after the previous PR merges)
**Requirements**: SCOPE-01, SCOPE-02
**Backlog**: 999.27
**Success Criteria** (what must be TRUE):

  1. The 999.27 reproduction (a committed state file carrying a crafted valid commit id, including current HEAD, while a committed source change exists against the original base) is first a fixture that fails on 2.15.0 code; after the repair, that state cannot hide the committed change: the review covers it, or stops and asks the user to confirm the base.
  2. A fixture shows HEAD passing `merge-base --is-ancestor`, so the repair does not rest on an ancestor check alone; the existing refusal of anything but a commit id (Phase 60 CR-01) still passes.
  3. A legitimate pass >= 2 resume still reviews only the new changes, and the effective range (base..HEAD or equivalent) is stated to the user on the review output or card.

**Plans**: TBD

### Phase 68: Unambiguous phase and scope binding

**Goal**: An ambiguous phase name or a colliding scope key cannot cause a review or Close out to target the wrong phase or the wrong saved state.
**Depends on**: Phase 67 (sequencing only)
**Requirements**: BIND-01, BIND-02, BIND-03
**Backlog**: 999.39 SA-01/WR-01, 999.45
**Success Criteria** (what must be TRUE):

  1. The 999.39 reproduction (two same-named phase folders silently resolved to one; `phases` accepted as a phase id) is first a fixture that fails on 2.15.0 code; after the repair, duplicate exact or prefix matches stop and list the candidates, and container names (`phases`, `milestones`, `v1-phases`) are refused even when unique, all before any review state file is read.
  2. Unique phases still resolve in both supported layouts (fixtures for each), and the `05-state.md` state-isolation sentence claims only what the check enforces.
  3. Narrowed `--all` (narrow-A vs narrow-B vs whole tree), colliding branch names (`feat/a` vs `feat-a`) and distinct PR/range identities each have a recorded outcome through resume and Close out: existing protection proven by a journey fixture, a concrete wrong-target failure repaired, or a conservative refusal. No general state-format migration; existing state and archives are preserved.

**Plans**: TBD

### Phase 69: Safe helper invocation

**Goal**: Repository Python startup code cannot run through the plugin's helper or hook invocations, and an empty or missing helper path refuses in the same call.
**Depends on**: Phase 68 (sequencing only)
**Requirements**: HELP-01, HELP-02
**Backlog**: 999.43 (promotes 999.38 R2-WR-01/02)
**Success Criteria** (what must be TRUE):

  1. The actual helper and hook invocations are inventoried, and the 999.43 reproductions (a `PYTHONPATH` `sitecustomize.py` marker printing before a helper runs; `python3 ""` executing a repository `__main__.py`) are first fixtures that fail on 2.15.0 code across the real command forms.
  2. After the repair, the benign markers never execute through any inventoried helper or hook command form, while trusted sibling imports between the plugin's own scripts keep working and the offline suite passes.
  3. An empty or missing helper path refuses in the same call with a one-line message and runs nothing; normal helper and hook calls behave as on 2.15.0. Trusted interpreter, git/node configuration and OS permissions remain documented prerequisites, not sandboxed.

**Plans**: TBD

### Phase 70: Submission packaging and truthful claims

**Goal**: The submitted `plugins/vibe-check` folder meets the portal's documented README and license requirements, and every public setup, model-label, efficacy and cost statement is truthful for the candidate.
**Depends on**: Phases 66-69 (the claims describe what shipped)
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05
**Backlog**: 999.41
**Success Criteria** (what must be TRUE):

  1. `plugins/vibe-check/README.md` exists as a standalone document with at least 40 prose words and valid links, and the folder meets the portal's documented README/license requirements (manifest `license: MIT`); a link check and word count are recorded.
  2. Documentation states the Python prerequisites and supported-version expectations (including the TOML fallback below 3.11) and the optional Codex companion dependencies and setup (Node, authentication, watchdog).
  3. Run output and docs label the Codex lane "Codex (configured default)" or show the resolved model; joined, skipped and failed outcomes are reported accurately (fixtures).
  4. Public claims put the stricter v2.11 12/15 catch reading beside 15/15, keep the MISS verdict and the no-current-release-measurement disclosure, and say what estimated costs include; byte/step reductions are never presented as billing savings.
  5. A record for the exact candidate lists installation and portal checks as performed or still pending, and the affected offline compatibility checks pass.

**Plans**: TBD

### Phase 71: Release gate — publication readiness

**Goal**: 2.16.0 ships through the existing close-and-publish workflow with reproduction and regression evidence for every repair, offline and live evidence recorded separately, and portal submission left to separate owner authorization.
**Depends on**: Phases 66-70
**Requirements**: GATE-07, GATE-08, GATE-09
**Success Criteria** (what must be TRUE):

  1. Each implemented repair has a reproduction that fails on 2.15.0 and a regression that passes on the candidate; unchanged-code controls pass on both; investigation-only leads close with documented non-reproduction.
  2. The full applicable offline suite and the replay against 2.15.0 run on the exact candidate commit; every difference is an explicitly accounted intended repair, and any unexplained difference blocks the release.
  3. Offline and live evidence are recorded in separate sections; live checks run only under an owner-approved bounded proposal, otherwise they are listed as pending or explicitly waived, never as passed; a pending required check prevents the publication-readiness claim.
  4. The candidate ships via the existing workflow (release PR, tree-identity check, tag on `origin/main`, GitHub release, plugin update) and the record states that Claude developer-portal submission was not performed and needs separate owner authorization.

**Plans**: TBD

## Following milestone: Reviewer efficiency (conditional)

**Goal:** Reduce review usage or latency only where a bounded experiment demonstrates that expected defect detection and false-alarm behavior are preserved.

**Activation:** Publication readiness is complete; Decision reliability and Lean orchestration remain shipped; attributable costs or a reproduced repeated-work case identify a meaningful target; the owner approves a bounded comparison proposal and any paid runs. No phase numbers or implementation commitment before this gate. Size remains unknown until one experiment is selected.

1. [ ] **Select one evidence-backed experiment.** Compare architecture/impact routing, targeted fix rechecks with dependency/snapshot invalidation, OR narrower specialist context; do not bundle interventions. Preserve bugs/security coverage and independent confirmation, and fall back to existing coverage when impact is uncertain. Check actual cache-read/write fields instead of assuming parallel dispatch shares a cache. Predeclare the baseline, model/configuration/cache conditions, fresh defect/clean cases, repeats and useful savings threshold before running. Include large/cross-file changes and repair journeys; preserve sealed evaluation access boundaries.

2. [ ] **Go/no-go and release gate — measured efficiency without quality loss.** An independently scored comparison must show no lost expected catches, no added false-alarm runs and useful measured usage/latency improvement against the incumbent on the predeclared workload. Run offline and mode/recovery regressions for the candidate too. Report small-sample limits and exact artifact/model identities. Reject or defer inconclusive variants and retain the incumbent; no paid approval means no experiment and no quality-equivalence claim. Release only a passing variant through the existing close workflow. The earlier milestones remain complete regardless of this outcome.

**Out of scope:** Automatic model downgrades based only on diff size, persistence weighting or severity retunes, broader reviewer replacement and new accounting infrastructure. Persistence-as-second-opinion remains a separate hypothesis needing its own bounded proposal; this sequence does not authorize scorer changes.

## Sequence rationale and evidence

**Priority update (2026-11-16):** Publication readiness now precedes optional efficiency work. Stale Close out affects the core closure path; untrusted scope and ambiguous phase selection can hide work or target the wrong findings. Reach is unmeasured (ambiguous layouts are uncommon), but current offline reproductions support correctness repairs ahead of optional savings. The plugin-folder README is a concrete submission requirement. The smallest repair/verification scope wins; adding a helper or abstraction requires a demonstrated need. v2.15 remains worthwhile: its Close out reduction was 3.48% in instruction bytes and 92 → 85 counted steps, not measured billing savings; review paths grew slightly.

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

**Phase 63 (2026-11-15):** the general cross-call variable check now exists (`plugins/vibe-check/scripts/test_cross_call_vars.py`, every file under `phases/`); every place it flagged was fixed and its remaining exception and known limits are tracked in 999.36. Finalize's gate inputs now come from one helper call (`finalize_inputs.py`), so R1's traceback no longer reaches a Finalize fence.

### 999.26: Plain-English title references: wordier phrasings ask (Phase 58 D-23 known limits)

After the CR-01 rollback (58-REVIEW-FINAL.md), a title reference names a row only when that row's title holds every word the owner used, filler aside. Wordier but clear phrasings ("the retry budget warning", "the Browse recovery issue from earlier", inflections like "retries budget") get one follow-up question with the likely row as a button. This fails safe: nothing is acted on wrongly. The best-unique-match attempt (58-19) was rolled back because it dismissed a row the owner meant to fix. Safer design from the reviewer: act only when the best row contains ALL of the owner's non-filler words (treat small words like on/and/in as filler); otherwise offer the best partial row as a one-click choice in the follow-up. Also carried: tie candidates capped at 4 (a 5th tied row may not appear as a button); on a carried-close-out pass the Close out text points at that pass's card file rather than "the card the owner read"; the fallback note after the subset-file refusal has no specified wording; the "How many" follow-up offers single-row buttons; no Unicode normalization of titles. Reproduce first; any matcher change needs adversarial fixtures that put the target's key word next to two words from another title. Not scheduled.

### 999.27: Committed state file's `head_sha` can narrow the pass >= 2 review range (Phase 60 R25)

A well-formed but crafted 40- or 64-hex `head_sha` committed into the reviewed repo's state file passes `carry_state.py last-head-sha` and can narrow the incremental (pass >= 2) range without telling the owner. Phase 60's CR-01 fix closed command injection, not scope trust. Owner ruling 2026-10-30 (60-HUMAN-UAT test 3): status quo accepted for v2.14; hardening deferred. Candidate direction: require the stored sha to be an ancestor of HEAD and state the narrowed range on the card. Also consider R26 (no write-side format check on `head_sha`). Reproduce on a real review first. Needs exploitation by someone who can commit to the repo. Not scheduled.

**2026-11-16 reassessment:** Selected for Publication readiness (v2.16 Phase 67, SCOPE-01..02), superseding the unscheduled disposition above without changing the v2.14 waiver. At `c1461c5e`, the real `last_head_sha` helper accepted current HEAD supplied in state; a temporary Git repo had a committed source change against its original base, but the selected incremental diff was empty. HEAD also passed `merge-base --is-ancestor`, so ancestry alone cannot repair scope trust. Helper/Git reproduction only; no live model review. Relevant implementation: [SHA validation](../plugins/vibe-check/scripts/carry_state.py), [incremental selection](../plugins/vibe-check/phases/review/05-state.md). Preserve command-injection refusal while establishing trusted or owner-confirmed resume scope.

### 999.29: A decided finding re-reported under a reworded title shows as new (2.14.1 live check)

Seen in the 2.14.1 live check (default route, unchanged tree): the bugs lane re-titled the deferred SQL-injection finding on pass 2, so the row got a new stable_hash and was shown as an undecided new finding with no "(was: deferred)" context. The original decision was kept as a member obligation (no nearby stamp, not re-asked). In 2.14.0 this was masked by the false 999.28 nearby reason. Fails toward asking; nothing lost. Candidate direction: carry decision context onto a lead whose members include a decided obligation for the same file and line. Reproduce on the real chain first. Not scheduled.

### 999.30: Snapshot store and temp leftovers are never pruned (2.14.1 known limit)

`.turingmind/worktree-snap/objects` grows by the changed blobs of each default/GSD pass, and a pass that stops before Phase 3 leaves a `vc-worktree-snap-<nonce>` folder in the system temp directory (unusable by any other pass). Deleting either is safe (the next pass re-asks once). Candidate: prune store objects not reachable from the last recorded `reviewed_tree`, and sweep temp folders older than a day in `take`. Maintenance, not scheduled.

### 999.31: Decision identity design (groups the remaining decision-continuity limits)

Owner decision 2026-11-13: stop scheduling the remaining decision-continuity limits one at a time and treat them as one design question, to be taken after Lean orchestration ships. This entry commits no work, phase numbers or dates. Following the 2026-11-16 assessment, Publication readiness comes first; this design remains deferred.

The shared cause: a decision is tied to a finding by `stable_hash(file, canonical_line_content, title)` plus separate nearby-change/coverage evidence, so a reworded title or a new identical copy needs another special rule. This area was repaired in v2.11, v2.12, v2.13 (Phase 57), v2.14 (Phases 59–60) and 2.14.1 and still has open shapes. The shapes explicitly grouped below fail toward asking again. That statement does not cover all historical decision carries: the full backlog pass found relocation/cover-selection wrong-keep leads, now tracked separately in 999.44 and gated before publication.

Grouped here (each original record and repro stays where it is):

- 999.23 residuals: D-01 later-pass over-ask, WR-01 over-ask #2, and the WR-01/WR-02 card wording.
- 999.26: wordier plain-English title references ask a follow-up.
- 999.29: a decided finding re-reported under a reworded title shows as new.
- `--all` reviews keep no decisions between runs (README known limit; 999.24 R10).

Not grouped: 999.27 (`head_sha` scope trust) is a security question, and 999.30 (pruning) is maintenance.

Design question to answer before any code: what a decision is attached to (for example the file plus the code it was made on, instead of the title plus a line window), and how old decisions migrate. Reproduce each grouped shape on current code first. A reproduced silent keep or lost deferral is actionable immediately and does not wait for this item.

### 999.32: Fix loop stops instead of taking Rerun after a typed defer (C4, moved from 999.28)

Moved out of 999.28 on 2026-11-13 so it is not lost inside a shipped item. Reproduced in the Phase 61 live smoke (61-LIVE-SMOKE.md S2) and again in the 2.14.1 live check: after a typed `defer` in the fix-loop card flow (`phases/review/50-fix-loop.md`), the model stops and lists choices instead of taking the automatic Rerun step. Fails toward stopping: decisions are saved and nothing is lost, at the cost of one manual step. This is model-interpreted prose, so a fix belongs with the Lean orchestration work if the fix loop is chosen as its optional extension; otherwise reproduce first. Not scheduled.

Related observation (65-LIVE-SMOKE.md K1, 2026-11-16, candidate 2.15.0): in the default review, after every row was deferred the Rerun did run (this item did not reproduce), but pass 2 had an empty fix-loop card and the model stopped, saying the prose does not cover an empty card. Decisions and state were saved and Close out then completed. Listed as a known limit in the 2.15.0 release notes.

### 999.28: SHIPPED in 2.14.1 — Default route: decisions on uncommitted code re-asked every pass (false nearby reason) (Phase 61 C1)

Fixed in 2.14.1 (PR #8, squash dd8e4ab, tag v2.14.1) on every route except `--all`, including the same re-ask found on PR and range reviews of committed code (owner chose to fix both before release). Debug record: `.planning/debug/999-28-uncommitted-reask.md`. Live check (default route only, owner-approved): unchanged tree kept the decision; an edit 3 lines above re-asked with the true reason. PR/range/GSD live check skipped by owner decision (tests only). C4 (model stops instead of Rerun after a typed defer) reproduced again and is now tracked as 999.32.

Original record: Reproduced in the Phase 61 live smoke (61-LIVE-SMOKE.md S1, C1): on the default review of uncommitted code, a finding deferred or dismissed at pass 1 was re-asked at pass 2 on a byte-identical working tree, and the card said "code next to it changed since your decision", which was false. Cause (from 61-RELEASE-RECORD.md Carried C1): on pass >= 2 the ranges come from `git diff <last-reviewed-sha>`; before any commit that sha is still HEAD, so the whole uncommitted block counts as changed every pass. Fails toward asking: nothing is lost and Close out completes. Probably predates 2.14 (2.13 also took ranges from `git diff HEAD` each pass; inferred from the 2.13 instructions, not tested). Owner ruling 2026-10-30 (61-SIGNOFF.md Decision 1, first A, then switched the same day to B): ships in 2.14.0 as the first Known limit in the release notes and in the README's "Known limitations (2.14)" (candidate C2 47978aa, README-only change; pending owner re-sign). Also carried here (C4): in S2 the model stopped and listed choices instead of taking the fix loop's Rerun after a typed defer (fails toward stopping; decisions saved). Candidate direction: compare the working-tree content against what the decision saw (not HEAD) so an unchanged uncommitted block does not count as changed. Reproduce on the real chain first; needs a fixture and a mutant. Reopen as worse if a re-ask on unchanged committed code is reproduced. Not scheduled.

### 999.34: Phase 62 review carry: baseline checks that pass on inputs they should reject

The Phase 62 code review (`.planning/phases/62-baseline-and-continuous-test-run/62-REVIEW.md`) found six checks that cannot fail on some bad inputs, plus two items set aside for a ruling. The owner merged Phase 62 with them carried (2026-11-14). None lets a failing test run show green today. Not scheduled; this entry commits no work.

- WR-01: the CI skip guard passes when one recorded skip appears twice.
- WR-02: the step-count check accepts a step record over any file list, including an empty one.
- WR-03: the footprint, traces and step checks trust the commit written in the record instead of the 2.14.1 commit, so the verify command can say "baseline holds" for other records.
- WR-04: the proxy token figures in the footprint record are never recomputed.
- WR-05: the suite record check accepts a baseline run that had errors or skips.
- WR-06: the stdlib-only check passes imports that only newer Pythons have, and any same-named file anywhere in the plugin; it needs an owner ruling on the plugin's minimum Python version.
- SA-01: the headline replay figure is a typed string that no check re-derives.
- SA-02: the stdlib-only check does not look at Python run from the instruction files.

WR-02 and WR-03 should be closed before Phase 65's equivalence gate relies on those checks.

### 999.35: Finalize card temp-file plumbing extraction, together with the fix loop's matching card (Phase 63 D-04)

Phase 63 moved only Finalize's gate inputs into a helper; the decision card and record-decisions plumbing stayed as in 2.14.1 by owner decision (D-01, D-04). Figures from `step_count.py` (rule v1): `90-finalize.md` went from 68 to 59 model-run steps with the extraction alone (`c7d92c9`) and is 59 at phase end (`b49d40a`): 14 Bash blocks, 35 pasted names, 5 file writes, 5 inline commands. Nine of its ten printed temp-file names belong to the card and record-decisions (`ANSWERFILE`, `CARDROWSFILE`, `DECFILE`, `PARSEFILE`, `REFSFILE`, `RESOLVEFILE`, `ROWSFILE`, `SUBSETFILE`, `SUGGESTFILE`; `BLOBFILE` is the inputs step). The split of the 59 steps by name was not measured. To be weighed later with the fix loop's matching card. Not scheduled; not a Phase 64 candidate.

### 999.36: Cross-call variable check: remaining exception and known limits (Phase 63 D-08, D-10)

No place was pinned: the owner had all six flagged places fixed (63-09, "Fix all six"), and the three found later were fixed too (Close out, fix loop, `--all`). One flagged place remains on the shrink-only cross-file exceptions list: C2, `phases/review/30-collect-score.md` reads the state path without naming the printed `STATE_FILE=` line; not reproduced. Known limits: only files under `phases/` are checked (command and agent files are not); the cross-file check does not check the order in which files run; a value set only in prose, never in a command, is seen by neither check (63-REVIEW.md WR-02). Details: `.planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REPRO.md`. Not scheduled.

### 999.37: Finalize helper matches 2.14.1 on inputs it could refuse (Phase 63 D-06)

The helper behaves as 2.14.1 does on inputs a stricter helper could refuse: a fix verdict whose pass is recorded as `true` is treated as pass 1 (`test_finalize_inputs.py::TestParityGaps::test_gap_at_pass_true_matches_pass_one`); an empty state-file path reads as "no saved progress" (`test_finalize_inputs.py::TestCliRefusals::test_gap_empty_state_file_path_is_no_state`). Also a possible later improvement: honour a fix verdict for a file whose name the 2.14.1 guard command refuses (most names starting with `-`); Phase 63 matched 2.14.1 instead (D-24), and which such names are refused depends on the Python version on both sides. Not scheduled.

### 999.38: Phase 63 review carry (63-REVIEW.md, 63-REVIEW-2.md)

The owner accepted these as carried at the Phase 63 go (2026-11-15). None is a regression from 2.14.1 except WR-02 (correction, 2026-11-16, 65-REPRO-WR02.md).

**WR-02 outcome (Phase 65):** WR-02 was a regression introduced during v2.15, not present in 2.14.1: under the fresh-shell standard 2.14.1 fails closed ("No prior review passes."), while the pre-fix candidate closed phase B on phase A's saved progress (a wrong close). Fixed before release, test-first, in the one D-08 fix round (65-03: RED `976e3fe`, GREEN `b281042`; +495 bytes, 0 steps per path); it never shipped. The remaining items below stay carried.

- WR-02: if the phase id comes through empty, every phase in a repo shares one saved-progress file.
- WR-03: the unsafe-name stop blocks only characters that are live inside double quotes; it is safe only while every paste is double-quoted (`;`, `&` and `'` pass).
- WR-04: an internal fault in the Finalize helper is reported as "finalize_gate.py failed", with no detail recorded anywhere.
- SA-01: a repo folder whose name holds a space or quote gets a cut-short saved-progress file name (changing it needs a migration).
- SA-03: the first review only pattern-scanned eleven of the twenty files.
- R2-WR-01: the helper scripts (not the inline commands) still honour a `PYTHONPATH` set in the owner's own environment (about 70 call sites).
- R2-WR-02: an empty helper path would make Python run a `__main__.py` from the reviewed repo; five call sites have no emptiness check in the same command.
- R2-WR-03: the check that inline Python runs isolated recognises today's command shapes only (e.g. `python3 -X utf8 -c`, stdin scripts would be missed).
- Set aside by the second review: a narrowed `--all` run may lose its narrowing value in a fresh shell; a version manager or active virtual environment can choose `python3`; the `git` and `node` calls beside the inline commands were not assessed.
- Live smoke carry (65-LIVE-SMOKE.md K3, 2026-11-16): Close out can write REVIEW.md's audit-trail line naming the archive before the final archive name is known; in the live run the model corrected the line itself. Wording only, no state lost. K1 (empty fix-loop card after the Rerun) is noted under 999.32.
- Verifier notes: the five-situation comparison does not look at the helper's `next` field (unit tests in CI cover it); the Codex collect timing test was flaky on CI before this phase and was fixed test-only by warming node (cause best-supported, not proven).

Not scheduled.

**Full disposition pass (2026-11-16):** R2-WR-01/02 are now selected as publication blocker 999.43 (v2.16 Phase 69). Narrowed-all/scope identity requires bounded pre-submission checks in 999.45 (v2.16 Phase 68). Other carries remain deferred or accepted as indexed below; this supersedes scheduling, not the historical ship decision.

### 999.39: Phase 65 code review carry (65-REVIEW.md, owner ruling 2026-11-16)

The owner chose "Ship + backlog (Recommended)" (AskUserQuestion, main session, 2026-11-16): ship 2.15.0 as signed off, name the lookup gap as a release-notes known limit, and carry both items here. Neither is a regression from 2.14.1.

- SA-01 (lookup, pre-2.15): the GSD phase lookup in `00-scope.md` silently picks one folder when two phase folders share a name (e.g. `v1-phases/01-setup` and `v2-phases/01-setup`) instead of the "multiple matches" stop its instructions describe, and accepts a container name (`phases`, `milestones`, `v1-phases`) as a phase. Two phases can then share one saved-progress file and Close out can close on the wrong findings (wrong close, unusual layouts only). Fix: refuse multiple matches and container names in the lookup fence, test-first with mutants.
- WR-01 (wording, from the WR-02 fix): the sentence at `05-state.md:16` says "two GSD phases never share one state file"; the check only refuses an empty id. Reword to claim only that, together with the SA-01 fix.
- Info: IN-01 (cross-class helper borrow at `test_pasted_name_guard.py:400`) and IN-02 (label-suffix-gated message check at lines 334–335) are test tidiness only.
- SA-02 (no live GSD check of the printed-id substitution) is covered by the 2.15.0 waiver; if a live model drops the id, GSD reviews stop safely with "phase id is empty".

Not scheduled.

**2026-11-16 reassessment:** SA-01 and its WR-01 wording correction are selected for Publication readiness (v2.16 Phase 68, BIND-01..02); the other carries remain deferred. Executing the current `00-scope.md` lookup fence in a temporary layout selected one of two `01-setup` directories without refusing, and accepted `phases` as a phase id. This freshly verifies lookup behavior; the wrong-close consequence follows from basename-keyed state and was recorded by the Phase 65 review. No live GSD session was run. Preserve the historical ship-with-backlog ruling above.

### 999.40: Keep: Close out freshness for ordinary owner decisions

**Selected for Publication readiness (v2.16 Phase 66, FRESH-01..02); repaired in Phase 66 (offline evidence, see the repair note below).** New offline evidence from the 2026-11-16 assessment at `c1461c5e` / 2.15.0: create a temporary Git repo with `test_decision_continuity.base_file()` at `src/a.py`, commit it, build pass-1 state with `pass1(lines, conf=95, kind=...)`, and record actual HEAD and `HEAD^{tree}`. For each of `defer` and `dismiss`, change source line 10 to `line_10 = danger()` and run the real `finalize_inputs.py` CLI with that state, a fresh empty blob file and all three switches false. Both exited 0 with `action: write`, `next: write-review-md`, and all outstanding counts zero despite the source diff. Temporary fixtures were removed; this record describes an assessment reproduction, not a committed regression test or live-model run.

Mechanism: [review.md](../plugins/vibe-check/commands/review.md) skips scoring/carry-forward in Finalize; [finalize_inputs.py](../plugins/vibe-check/scripts/finalize_inputs.py) supplies stored-state counts and fix-verdict blobs; [carry_state.py](../plugins/vibe-check/scripts/carry_state.py) compares saved decision evidence with saved finding data and `_closed` accepts that decision before fix checks. The bounded repair is a freshness refusal requiring review again, with exact-line/nearby/unchanged controls for both decision kinds. Do not infer that this was introduced in 2.15 or reopen 999.28: subsequent-review snapshot/scoring tests passed, and this failure goes directly from edit to Close out.

Repaired in Phase 66 (candidate cf1ea0bd): Close out refuses stale deferred/dismissed decisions (`stop-review-again`); reproduction `test_closeout_fresh.py::TestRepro999_40`; controls byte-identical to d5acc19. Evidence is offline only (no live reviewer run); the whole Finalize differential against d5acc19 (`TestOnlyIntendedDifferences`) differs only by named refusals and the 999.44 shape 2 repair.

### 999.41: Keep: Submission packaging, prerequisites and evidence disclosure

**Selected for Publication readiness (v2.16 Phase 70, PKG-01..05); not implemented.** At `c1461c5e`, the tracked `plugins/vibe-check` folder has no README, though it contains the manifest. The [official portal checklist](https://claude.com/docs/plugins/pre-submission-checklist), checked during the 2026-11-16 assessment, requires at least 40 prose words in that folder; manifest `license: MIT` satisfies the license requirement. Add a concise standalone README with valid links. Python hooks and text files over 256 KiB may cause reviewer holds, not automatic rejection; retain the safety hook. No tracked `.DS_Store` was found. Actual portal/name validation remains unperformed.

Include only these adjacent documentation tasks: Python prerequisites (TOML falls back below 3.11), optional companion/Node/authentication/watchdog setup, configured-default model labels, accurate joined/skipped/failed outcomes, and bounded offline compatibility checks. Reuse [Codex maintenance](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure); no adapter redesign. Companion 1.0.4 was statically inspected, not authenticated or launched.

The [v2.11 report](../plugins/vibe-check/docs/efficacy/RESULTS-v2.11.md) records a stricter 12/15 catch reading versus headline 15/15 (five defect diffs, three repeats), tuning overlap and owner-only repos. Put that caveat beside the public headline; preserve historical verdict MISS and no-current-release-efficacy disclosure. Clarify main-session/cache assumptions in cost estimates; byte/step reductions are not billing measurements. No benchmark or accounting restart.

### 999.42: Deferred: Needs debugging outcome

The 2026-11-16 source assessment found no explicit Needs debugging outcome. [fix.md](../plugins/vibe-check/agents/fix.md) has `needs-human` for product/architecture decisions or changes beyond scope, plus unsuccessful repair outcomes. When a concrete repair journey needs investigation before a safe fix, consider a small investigation-required reason/outcome that keeps the finding open and explains the next diagnostic step. Existing no-fabricated-fix rules remain. No autonomous debugging pipeline or automatic paid investigation; not a publication blocker and not scheduled.

### 999.43: Block publication — safe Python helper invocation

**Selected for Publication readiness (v2.16 Phase 69, HELP-01..02); not implemented.** Promotes 999.38 R2-WR-01/02 from the historical Phase 63 waiver. Fresh offline probes on 2026-11-16: invoking the real `statepath.py` with `PYTHONPATH` pointing to a temporary repository containing a harmless `sitecustomize.py` printed its marker before helper execution; `-E -s` suppressed the marker while the helper succeeded. Separately, `python3 "" ...` in a temporary directory executed its `__main__.py`; a same-command nonempty-path guard refused instead. No malicious code, network or live model run was used. These are interpreter/command reproductions, not evidence of an exploited user session. Current printed helper calls (including `30-collect-score.md`'s `SCORE_PY`) do not uniformly enforce these boundaries in the invocation itself. Earlier fences do not retain variables in a fresh shell.

Smallest scope: inventory the actual helper and hook invocations; ignore ambient Python startup/import overrides and reject empty/missing helper paths in the same call; preserve trusted sibling modules. Test the real command forms with benign markers and normal helper fixtures. `-E -s` is a demonstrated candidate, not an approved universal patch; verify import compatibility. Trusted interpreter, git/node configuration and OS permissions remain documented prerequisites, not a promise to sandbox arbitrary repositories. Existing SHA/pasted-name/path guards remain.

### 999.44: Pre-submission decision gate — unresolved legacy wrong-keeps

**Selected for Publication readiness (v2.16 Phase 66, FRESH-03); Phase 66 outcomes recorded below (shape 1 is an owner-accepted known limit).** Source: Phase 57 `deferred-items.md`, original WR-01 (unbounded relocation) and REVIEW-GAPS IN-03 (old covering decision wins); Phase 60 `60-REPRO.md` R7 (untracked files lack change ranges). These were missing from the broad “all remaining shapes over-ask” summary. They are considered within 999.40, not a new identity milestone.

Fresh evidence: the real scorer/state chain driven by `test_decision_continuity`'s **simulated relocation** kept a dismiss current and returned `write` after deleting the decided line 10 when identical text remained at line 49. This proves the helper chain given that relocation, not live orchestrator behavior. A separate **synthetic legacy-state** probe showed `_covering`'s sorted-first choice returning `current` with an older critical cover plus a newer medium cover, versus `stale` with the newer cover alone. Real writer producibility of that overlap remains unverified. `worktree_snap.py` explicitly excludes untracked files; no fresh end-to-end wrong-keep probe was run for R7.

Bound the work to these three shapes: reproduce through current documented collection/persistence and both decision kinds; distinguish deleted-original relocation from the owner-accepted D-21 addition of an identical copy. Repair a real wrong keep or require a fresh review/refuse that unsupported decision. If a shape is not producible, record the counterexample/control and remove it from the gate. Preserve ordinary line shifts, scoring, genuine nearby-edit reopening and 999.28 unchanged-worktree behavior. No general matching redesign or scorer retune.

Shape 1 outcome (Phase 66, 2026-11-18): owner-accepted known limit — reproduced through the real flow for defer and dismiss (decided line deleted while an identical line already existed elsewhere: decision kept current at the other line, Close out writes); a correct re-ask needs old-side "removed since review" lines from worktree_snap.py, beyond the D-14 bound, and the Close out code-changed refusal does not bound it (the next review relocates again) — tests: TestShape1DeletedOriginal.test_shape1_deleted_original_is_reasked_at_pass2_known_limit, test_shape1_closeout_does_not_write_on_deleted_original_known_limit (expectedFailure), control test_shape1_copy_written_by_the_same_change_reasks_control; D-21 distinguished by test_d21_identical_copy_added_while_original_remains_keeps.

Shape 2 outcome (Phase 66, 2026-11-18): repaired — _covering prefers the newest cover (highest at_pass, hash tie-break; owner-approved at 66-08 Task 2); reproduced first through record_decisions for defer and dismiss (older critical cover kept the finding current and Close out wrote when its hash sorted first); the 2.14.1 parity side now runs carry_state.py materialized from dd8e4ab — tests: TestShape2CoveringOrder.test_shape2_two_covers_producible_covering_order, test_shape2_newest_cover_decides_covering_order, test_shape2_tie_and_uncounted_at_pass_covering_order, control test_shape2_single_cover_control_covering_order.

Shape 3 outcome (Phase 66, 2026-11-18): reproduced on 2.15.0 (Close out wrote on a deferred or dismissed decision over an untracked file, for both kinds); the candidate refuses with cause untracked, `git add -N` alone does not clear it, and the D-13 step (`git add -N`, then review again) clears it with no loop — tests: TestShape3Untracked.test_old_helper_writes_on_untracked_decided_file, test_candidate_refuses_untracked, test_git_add_n_then_review_clears, test_mutant_skip_absent_check_writes; clearing proved through the real fences by TestClearable.test_clearable_untracked.

Shape 1 recorded as an owner-accepted known limit (not a repair) — deleted-original relocation keeps the decision current at the identical line elsewhere, and the Close out code-changed refusal does not bound it; the remaining shapes have repair / safe-refusal / non-reproduction outcomes (shape 2 repaired, shape 3 safely refused). FRESH-03 gate item NOT fully satisfied offline; carried to the milestone audit.

### 999.45: Pre-submission scope gate — narrowed all-mode and colliding keys

**Selected for Publication readiness (v2.16 Phase 68, BIND-03); not implemented.** Source: 999.38 second-review SA-01 and IN-02; `statepath.py`/`05-state-all.md`. A fresh helper probe confirmed `feat/a` and `feat-a` resolve to the same branch-state path. Default/PR/range state scope and all-mode fresh-shell narrowing need explicit journey checks; key equality alone is not proof of a wrong close. The historical narrowed-`--all` carry says the printed fence consumes `${NARROW:-}` without binding the selected value in that call. No live narrowed-all journey was run in this pass.

Within the existing scope item, exercise narrow-A versus narrow-B/whole-tree, colliding branch names, and different PR/range identities through resume and Close out. Stop once each named shape has an outcome: existing guard proven, concrete wrong-target failure repaired, or conservative refusal. Do not build a general state migration just to rename filenames. Spaces/quotes in the repository folder remain cosmetic/deferred unless a wrong target is demonstrated. Preserve existing state and archives.

### 999.46: Carried: Phase 66 code-review minor items and review-side flagged-file snapshot

Source: `.planning/phases/66-close-out-freshness/66-REVIEW.md` (2026-11-18). Not scheduled; none met the add-work classes at review time. Phase 66 fixed CR-01, WR-01 (owner ruling: Close out refuses decisions on `skip-worktree`/`assume-unchanged` files with "clear the flag, then review again") and WR-02.

- **SA-01:** `worktree_snap.take` (the review's own snapshot) also misses on-disk edits to flagged files. Pre-existing. Close out's refusal bounds the effect: clearing the flag and reviewing again records a true snapshot.
- **IN-01:** the object-id regex accepts a trailing newline; git rejects it, so it is harmless.
- **IN-02:** CRLF/LF-only changes are invisible under `core.autocrlf`, although D-07 says any byte change counts.
- **IN-03:** after `git rm --cached`, the refusal says "that line changed" instead of "no longer tracked", so the advice is imprecise but still refuses.
- **IN-04:** add `--no-replace-objects` to the freshness git calls so replace refs cannot stand in for the reviewed tree.

Promote an item only if it reproduces as a wrong keep, a refusal loop or silent finding loss.

### 999.12: Narrow: Cost visibility feasibility — Lean orchestration

Inspect existing local usage records to determine whether a review's usage can be attributed reliably. Report available fields, missing data, pricing assumptions and the distinction between estimated, measured and billed cost. Do not start paid reviews to generate a baseline or invent per-agent usage.

Finish with a go/no-go recommendation for the smallest useful reporting change. Stop if reliable attribution is unavailable; document the limitation rather than build new accounting infrastructure. Existing chunk limits and estimates are not enforceable dollar caps. Scheduled as v2.15 Lean orchestration Phase 62 (BASE-01..04, activated 2026-11-13). This check does not block correctness repairs; missing attribution stops accounting work, not the reliability milestone. Budget-control implementation and cross-repo orchestration changes require their own scope.

**Outcome (2026-11-14):** the owner recorded NO-GO on cost visibility, following the note's recommendation (`.planning/phases/62-baseline-and-continuous-test-run/62-COST-NOTE.md`, `## Owner decision`). Accounting work stops; the milestone uses the labelled byte and step counts from the Phase 62 baseline as its evidence, and no usage-report backlog item is filed.

### Maintenance: Keep the Codex companion; improve setup and disclosure

Owner decision 2026-10-28: retain the existing optional Codex plugin integration. Capture dependency/setup documentation, accurate joined/skipped outcomes, configured-default model labels and bounded compatibility checks after companion updates in [the maintenance record](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure). Outside v2.14; no new milestone or integration redesign. Preserve current review targeting, guards and optional native-only behavior.

## Planning boundaries

- v2.16 Publication readiness is active (Phases 66-71; baseline 2.15.0 `d5acc19`); nothing implemented at roadmap creation. 999.31 remains deferred behind it. Paid runs, new agents, publication and Claude developer-portal submission require explicit owner approval; this roadmap does not authorize them.
- v2.15 Lean orchestration shipped 2026-11-16 as 2.15.0 (PR #12 squash `d5acc19`, tag `v2.15` on origin/main, GitHub release v2.15 (Latest)).
- v2.13 shipped as 2.13.0 with owner-accepted known limits (999.23–999.26); Phase 57 closed under the D-19 hard stop, Phase 58 with live ref extraction unverified (D-15).
- v2.12 shipped as 2.12.0 under owner waiver; outcome remains **UNMET — measurement incomplete**. Phase 55 and cancelled Phase 54 sweeps remain deferred.
- Reuse valid review evidence for unchanged code; scope new checks to changed code and affected callers. Any paid check requires an explicit bounded price proposal and owner approval.
- One branch and one PR per phase (owner decision 2026-10-23): `feat/<milestone>-phase-<N>`, each cut from `main` after the previous phase's PR merges; delete each branch locally and on GitHub after its PR merges.
- Routine cleanup remains in [maintenance](backlog/MAINTENANCE.md).
- [Lower-value ROI candidates](backlog/archive/2026-10-18/ROI-DEFERRED.md) are archived with reopening conditions, not scheduled or declared complete.

## Release records

- [v2.15 archived roadmap](milestones/v2.15-ROADMAP.md): lean orchestration (2.14.1 baseline + CI, Finalize helper extraction, cross-call variable check, release gate); known limits 999.34–999.39.
- [v2.14 archived roadmap](milestones/v2.14-ROADMAP.md): decision reliability (stale decisions, exact change evidence, reliable Finalize); known limits 999.23 residuals, 999.26–999.28.
- [v2.13 archived roadmap](milestones/v2.13-ROADMAP.md): reliable fix closure, decision continuity and recovery; known limits 999.23–999.26.
- [v2.12 archived roadmap](milestones/v2.12-ROADMAP.md): shipped reliability improvements; measurement incomplete.
- [v2.11 archived roadmap](milestones/v2.11-ROADMAP.md): last measured milestone, false alarms 5/18 and catches 15/15, with release/measurement caveats.
- [All milestone history](MILESTONES.md).
- [Archived backlog and disposition ledger](backlog/archive/2026-10-18/README.md).

## Full backlog disposition — 2026-11-16

This is the disposition of the **known repository records**, not a claim that every latent bug has been found or every old report reproduced. Baseline: `main` at `9b92a3a1`, plugin 2.15.0; source unchanged since `c1461c5e`. All five publication work items above remain bounded. **Block** means a concrete release repair; **Check** means a credible consequential lead must be reproduced/refuted before submission; **Later** means no publication gate; **Historical** means superseded or closed according to the cited records, not freshly retested; **Measurement** means no new efficacy claim without evidence. No old waiver was silently converted into a pass.

<details>
<summary>Source-indexed disposition ledger (including unnumbered carries)</summary>

### Inventory and evidence boundaries

Sources considered: current backlog and local maintenance; [archived backlog index](backlog/archive/2026-10-18/README.md) and pre-organization roadmaps; milestone audits/roadmaps v2.1–v2.15; phase review, deferred-items, verification/repro and live-smoke records, especially Phases 40–65; local codebase concerns; four open debug files; [Fable findings](../docs/design/FABLE-REVIEW-FINDINGS.md); [.turingmind deferred findings](../.turingmind/32-DEFERRED-FINDINGS.md) and REVIEW reports. Repeated records are grouped by underlying issue below; source IDs preserve distinctions. Legacy identifiers 999.11 and 999.33 were not found and are not invented. Ignored/local records remain local; this ledger is in the tracked roadmap so their dispositions survive a clone.

Fresh checks were offline, in temporary directories or helper memory: Python startup/empty-path execution, relocation-chain simulation, covering-decision helper selection, and branch-key collision. The preceding assessment supplied fresh Close out, crafted-SHA and GSD-lookup reproductions. Static source inspection and historical suite/live records are distinguished from those probes. No paid reviewers, new efficacy campaign, private holdout access, or implementation edits. TODO/FIXME source-marker search exposed no additional actionable production item. No assertion that a green historical suite proves the untested journeys below.

### Numbered backlog and archived proposals

| Item | Disposition and reason / reopening condition |
|---|---|
| 999.0, .1, .4, .6, .7, .9, .10, .14 | Historical: safe default, framework/config/test coverage, deterministic scoring, invariants, noise/Codex legibility and dogfood repairs delivered through subsequent milestones. Historical release records, not a new efficacy proof. Remaining specific issues are mapped below. |
| 999.2 | Later: deterministic secret scanner remains a coverage proposal; no observed leaked credential in this pass. Reopen with a concrete coverage gap; do not market complete secret detection. |
| 999.3, .5 | Later: SARIF and PR-comment integrations are feature work, unnecessary for portal readiness. |
| 999.8 | Historical: single-writer proposal superseded by later architecture; no new orchestration framework. |
| 999.12 | Closed NO-GO: cost-accounting feasibility rejected in Phase 62. Byte/step proxies remain estimates; no infrastructure resurrection. |
| 999.13 | Historical split/extraction work delivered; residual card duplication goes to 999.35, stale prose to 999.41 or maintenance. |
| 999.15 | Historical hunk-scoped commits delivered. Old stub's different line-fidelity title is not treated as equivalent evidence; coordinate residuals belong to 999.24/R3 below. |
| 999.16 | Later: dispatch/diff chunking needs a measured benefit and quality comparison. |
| 999.17, .18 | Measurement: model A/B and external comparisons parked; paid approval and independent holdout needed. |
| 999.19 | Historical member/noise changes delivered in Phase 53; broad noise target still unmeasured. No new milestone from duplicate records. |
| 999.20, .21, .22 | Historical: git-mutation guard, hardening and Codex fix confirmation repaired through Phases 48/52/56. Residuals below; do not reopen fixed stash-pop or one-pass confirmation defects. |
| 999.23 | Historical CR-01/02/04 and min-confidence deferral loss fixed in Phase 59. Later: D-01/WR over-asks, card wording and identity. Additional legacy wrong-keeps separated as Check 999.44. |
| 999.24 | Historical exact-change/range fixes shipped Phase 60; R1–R26 dispositions below, not all closed. |
| 999.25 | Historical printed-path, retry/recount/fingerprint repairs shipped; helper extraction supersedes old traceback path. Generic direct-helper error polish remains Later. |
| 999.26, .29, .31 | Later: conservative title matching, regrouping context and identity design. No silent-keep blanket claim; 999.44 is separate. |
| 999.27 | Block: trusted incremental base, already selected; ancestry alone does not repair repository-state trust. |
| 999.28 | Historical shipped fix retained: unchanged uncommitted work must not re-ask; score parity and reopening after real nearby edits stay acceptance controls. Debug metadata awaiting owner verification is not silently rewritten. |
| 999.30 | Later: prune snapshot/temp storage only on measured growth or a stale-file incident; no observed runtime failure. |
| 999.32 | Later: typed-defer rerun stop / empty-card stop. Latest smoke reran but then stopped at empty card; decisions preserved, manual Close out worked. |
| 999.34 | Later: baseline verifier false-acceptance debt (WR-01 duplicate skips; WR-02 empty file lists; WR-03 self-declared base; WR-04 proxy recomputation; WR-05 failed suite records; WR-06 newer-Python/same-name imports; SA-01 typed replay; SA-02 inline Python omitted). Candidate evidence must be independently checked, not certified solely by these validators. Minimum Python disclosure belongs to 999.41; no runtime quality change implied. |
| 999.35 | Later: shared card plumbing only if a concrete repeated-work saving justifies it; extraction preserves decisions/gates. |
| 999.36 | Later: C2 literal-state-path exception, cross-file order and commands/agents/prose-only scanner limits. Selected scope/helper repairs get focused tests; no general shell parser. |
| 999.37 | Later/accepted compatibility: boolean pass, empty state-file path and dash-prefixed filenames. No wrong close demonstrated from current valid inputs; revisit on producible unsafe outcome. |
| 999.38 | Split: Block 999.43; Check 999.45; fixed empty-phase regression Historical; remaining specific carries below. |
| 999.39 | Block: duplicate/container phase lookup and overbroad isolation wording. Later: test tidiness IN-01/02. Live printed-id GSD waiver is recorded unverified, not a pass. |
| 999.40, .41 | Block: stale Close out plus packaging/setup/truthful claims already selected. Optional Codex companion retained, not replaced. |
| 999.42 | Later: Needs debugging does not exist as a distinct current outcome; useful when safe repair needs investigation, but current needs-human/stop avoids automatic unsafe repair. No debug subsystem in publication scope. |
| 999.43 | Additional Block: demonstrated ambient startup-code and empty-helper execution. Narrow invocation repair, not an OS sandbox project. |
| 999.44, .45 | Check: bounded decision/scope journeys; must record repair, refusal or non-reproduction before submission. Neither authorizes broad identity redesign. |

### Unnumbered historical and phase carries

| Source / finding family | Disposition and practical consequence |
|---|---|
| Fable A1–A7, A9–A15 | Historical: v2.8 roadmap explicitly records calibration, absorb visibility, critical threshold, deterministic tie-break, forged-status scrub, crash/JSON guards, path guard, branch slug and marker fixes. Branch slug's remaining collision is Check 999.45; no claim that slugs are injective. |
| Fable A8/A16 | Historical answer-key SITE+AXIS rules incorporated in Phase 36; Measurement: does not validate current runtime quality. |
| Fable A17; security-prompt critique | Later historical lead: Codex field sanitation/confidence trust and prompt critique; current path/target/output guards retained. No fresh exploit or need to replace companion established. Reopen on a concrete prompt/output boundary bypass; do not call model output trusted. |
| Fable H-CORE, H-DUP1/2, H-LANE, H-COUPLE, B-SEV/XCONF/PROX/REWEIGHT, CATEGORY_DOMAIN | Measurement/Later: correlated reviewers, attribution, severity/confidence and tuning hypotheses. Same-site corroboration changed since the original +10 analysis; stale assumptions are not evidence for a retune. Conditional efficiency experiment only. |
| Fable O3; B3 still-owed work | Historical fix confirmation now implemented; arbitrary downstream test adequacy remains unproven. B3/independent efficacy still Measurement; no mandatory new campaign for honest publication. |
| Phase 32 bugs-003; bugs-002/impact-02; arch-001/cov-003 | Later historical suppression-audit identity/count/filter leads. Current per-token scanner differs from original; reproduce before changing. Audit-low omissions do not prove hidden critical review findings. |
| Phase 32 bugs-004/005/006; sec-001 | Later: scoped-marker syntax, line numbering, token boundaries and string-literal suppression. Existing substring suppression is an explicit source limitation; no language-parser project. Reopen on a concrete safety bypass beyond the owner-controlled suppression contract. |
| Phase 32 impact-03; cov-001/002; fs-001/002/003/004 | Later: synthetic schema/test coverage, marker docs, knob/default wording and long prose. Minimum-confidence/config docs evolved; do not assume old omissions remain. Correct current false public wording within 999.41 when encountered. |
| v2.1–v2.5 audit carries | Historical/manual evidence limits: FastAPI depth, ASYNC-01/02/03, missing old verification docs, BashOutput and old release-gate gaps. Source hardening delivered v2.5. Later: missing type hints, intentional dead title helper, residual unvalidated generic leads; no retrospective paperwork milestone. |
| v2.7/v2.9 audits | Measurement: RN dual emit/Expo live routing and old efficacy limitations. Historical stale README/tag metadata fixed forward; exact candidate checks still required. |
| Phase 35 config symlink lead | Later accepted hardening: own-repository TOML can follow a symlink; no leak/execution channel demonstrated. Reopen with a concrete boundary consequence. |
| Phases 40/41: context, permissions, harness operations | Measurement/external tooling: pinned CLI/model, invalidated attempts, context/memory pressure, failed sleep, announcement obedience, archived raw-envelope and token-accounting gaps. No runtime release blocker inferred from an invalid measurement run. |
| Phase 40 snapshot escape; Phase 41 medium_ack | Historical fixes recorded. First-pass/N shape and no-op model reports are evidence limitations, not new verified bugs. All-mode footprint growth is a cost limitation, not measured billing. |
| Phase 41 same-site arithmetic; Phase 53 +10 prose | Later stale prompt arithmetic (eight prompts/kickoff); current scoring is authoritative. Correct any published claim in 999.41; do not change scores to match stale text. |
| Phase 43 privacy placeholders; stash-pop | Historical fixes recorded; no reopened privacy incident or git-mutation repair needed. |
| Phase 46 punctuation, working-tree reads; Phase 48 allowlist | Historical later fix-stage/state hardening supersedes originals. Later: null first_pass_N / absorbed duplicate presentation metadata where no gate consequence shown. |
| v2.10 W1–W5; v2.11 audit | Historical: wait-anchor mismatch disclosed, stash safety/helper bypass superseded, finalize-token bug repaired, substring/multiline flags hardened. Later: top-model description drift, shipped dev/test scripts, dense prose. External orchestrator pass-1/archive lookup is outside plugin. Codex exact-or-skip dirty-planning behavior stays explicit. |
| Phase 51 deferred items: leak/provenance/seal operations | Historical documented fixes: finder permissions, tar filtering, encryption race, replace-retired, flaky IDs. Measurement/tooling: scrubbed evidence cannot be reconstructed, dry-run/config/auth limitations, owner-only refresh, legacy login and completed-run replacement semantics. Do not run or open sealed holdout here. |
| .turingmind/REVIEW.md deferred reseal identity | Measurement/tooling lead: exposure keyed by case ID can miss same content under new ID. Do not use affected clearance as fresh independent efficacy evidence without resolving it; not installed review runtime. Duplicate SEAL hash and containment helpers remain Later. |
| Three holdout debug sessions | Owner verification still pending: shared-temp/session isolation, finder sandbox and replace-retired. Recorded fixes/probes do not replace live owner acceptance. Gate any resumed holdout campaign, not plugin publication. |
| Phase 52 echoes/mktemp/temp-root; split card | Historical echoes/temp fixes; live split-finding card coverage remains unverified. Carry-forward deep-only lanes now fail conservatively or follow Phase 56 routing; no new lost-row evidence. |
| Phase 53 TS pointer, email/decorator filter, architecture-hooks prose | Later low-risk docs/filter maintenance. BM HANDOFF ignored-per-clone, should-quiet-4 classification and legacy URL-spec questions belong to Measurement. nv_dropped_weak labels are intentional. |
| Phase 56 CR-01/02, WR-01–06, SA-01 | Historical verification records close still-applies, any-commit clearing, Codex/plain confirmation, contradiction, malformed-file, orphan and association defects. Missing summary requirement tags are documentation debt, not failed runtime behavior. |
| Phase 56 SA-02, IN-01–03 | Later/accepted: plain needs-recheck snapshot handling needs real bypass before escalation; dispatch snapshot still protects code changes during confirmation. Synthetic broad fixtures/whitespace are test debt; reason rendering later fixed. Independent deferred-finding route fixture/live language interpretation remains unverified. |
| Phase 57 original WR-01; GAPS IN-03 | Check 999.44: deleted-original relocation to identical text and older covering decision selection. Evidence levels recorded above; no longer dismissed as harmless over-asking. |
| Phase 57 original CR-01/02, WR-02/03; GAPS2–4 criticals | Historical later fixes for member coverage, lanes, nearby/deletion, split stamps, same-hash ordering and deferral filtering. Phase 59 closed final pooled wrong-keeps. GAPS4 CR-03 new identical copy is owner-accepted D-21, distinct from deleted-original relocation. |
| Phase 57 WR-04, IN-01/02/05, final WR-01 | Later: snippet-first-line over-asks, null-band/card mismatch, covered-count undercount, identical-title/lane over-asks, newcomer-member ambiguity. Same-hash fix dispatch must retain conservative full-membership preflight. SA-02 all-mode loss did not reproduce; don't re-open it without evidence. |
| Phase 58 original WR-01–06 / IN-01–05; GAPS WR-01/03; FINAL CR | Historical stale resolution, suggestions, parsing/rows/print markers and wrong-title dismissal fixed. Best-unique matching was rolled back intentionally. Later: remaining matcher/card limits all listed in 999.26; suggestion/reason presentation hardening requires a concrete case. |
| Phase 58 SA-01–03 / D18–D20 | Accepted: bulk-count rule, neutral critical suggestions and typed Close out entry; no bypass of gate authorized. |
| Phase 59 WR-01/02; IN / SA-01 | Later wording/count/order claims, duplicate validation, conservative same-hash preflight ambiguity. Score zero kept-open is intentional so a deferred obligation cannot vanish; do not remove it as cleanup. |
| Phase 60 R1/R2/R9/R14 | Historical helper boundary/coordinates/injection fixed or superseded; obsolete research algorithm is not implementation guidance. Direct-helper error polish Later. |
| Phase 60 R3/R4/R5/R6 | Later/unverified: reviewer PR line coordinates need reproduction; old stamps over-ask; cache requires resync; live-fetch release evidence improved later but no new full PR journey here. |
| Phase 60 R7/R8/R10/R11 | Check R7 in 999.44. Accepted limits: C-quoted/non-ASCII paths unsupported; all-mode has no diff/retained decisions; replay retains context intentionally. Document unsupported boundaries, not claim universal coverage. |
| Phase 60 R12/R13/R15/R16/R17 | Later temp cleanup; unsupported SHA-256; duplicate refusal wording. Historical live Write succeeded (bypass mode only). Large-PR diff limit explicitly fails closed; no fallback project. |
| Phase 60 R18 | Later/accepted limitation: submodule diff configuration can omit/reshape ranges; no qualifying finding loss reproduced. Disclose unsupported submodule coverage with other scope limits in 999.41; do not claim full submodule review. Reopen if supported use is required. |
| Phase 60 R19/R20/R21/R22/R23/R24/R26 | Later: empty-diff wording, partial-color/mutant test weakness, overbroad SHA error, post-record failure wording, write-side SHA validation. Runtime read-side validation already stops invalid SHAs; narrow wording correction when touching closure. Escalate if a concrete false-success/unsafe write reproduces. |
| Phase 60 R25 | Block 999.27, supersedes v2.14 waiver for publication. |
| Phase 61 / 2.14.1 live C1–C5 | C1 Historical 999.28 fixed; C2 same-lane severity variation accepted; C3 identity Later; C4 typed-defer Later; C5 Write retry host-dependent. README contradictions fixed; remaining release-label/marketplace wording in 999.41 as needed. |
| Phase 62 extra infos / SA | Later: sidecar checks, TAPE failure (fails closed), future workflow env injection, privacy-checker consistency, regex/pins/casing. No present secret/execution incident demonstrated. Runtime import isolation now Block 999.43; typed replay is evidence weakness, not verified equivalence. |
| Phase 63 initial CR / WR / IN / SA | Historical inline Python isolation and printed-path repairs. Later: quote-dependent name guards (retain quoted use), generic helper error details, literal newline/path-regex limitations, temp cleanup, git-index metadata wording and C2 scanner exception. Eleven-of-twenty-file review coverage limits confidence; not proof other files are safe. |
| Phase 63 R2-WR-01/02/03 | Block first two under 999.43. Later future scanner forms; add tests for actual new invocation forms during repair, not a universal shell parser. |
| Phase 63 R2-IN-01–04, SA-01–04 | Check narrowed scope/late overwrite under 999.45. Later UTF-8 locale handling (Codex may skip honestly), guard/mkdir refusal semantics and test assertions lacking success controls. Trusted interpreter/version manager/git/node environment is a documented boundary, not freshly audited sandboxing. |
| Phase 65 K1/K3, audit metadata | Later empty-card stop and self-corrected archive reference. Historical CI/tag completion supersedes initial pending release notes. Mixed requirement tags/skip metadata are documentation debt. Live GSD/PR/range and omitted non-UTF-8 scenarios remain unverified where not explicitly recorded. |
| Maintenance / codebase concerns | Later duplicate blob prose/helpers/constants/private imports/SHA validators, unused code, stale test labels, WebFetch/MCP and signal-window polish, conservative mutation-guard overmatching. Hook-level holdout fixtures and rollback/verdict compatibility need a demonstrated break. No-CI/no-cross-call-check/Lean-not-shipped claims are superseded by Phases 62–65. “All planning untracked” is false for the tracked roadmap/state/project. No blanket missing-release-signoff claim: use exact runbook/candidate evidence. |
| Optional Codex maintenance | Selected only dependency/setup/model-label/compatibility disclosure under 999.41; keep companion. Later automatic update checks, temp-root assumptions and broad adapter changes; skipping unavailable Codex must stay explicit. |

### Updated code-map reconciliation — 2026-11-16

Reviewed the seven `.planning/codebase/` documents dated 2026-11-17 against the disposition ledger and spot-checked material assertions in implementation. The separate `.planning/intel/` refresh is dated 2026-11-14, not this new map. No additional publication work item follows from this map: its substantive risks already map to 999.27/30–45 or the maintenance/measurement rows above. Large modules, prose orchestration, duplicate grading helpers and optional dependency monitoring remain deferred absent a concrete failure or demonstrated saving.

Treat these map assertions as corrections required when the map is next maintained, not new product requirements:

- `CONCERNS.md`'s opening “all ... fails toward asking/stopping” conflicts with its own 999.40/27/39 sections. Helper execution is now Block 999.43, and decision/scope checks are 999.44/45; the map still calls those security carries merely owner-accepted. The tracked roadmap has the current disposition.
- `ARCHITECTURE.md` says scope keys never silently merge reviews. The confirmed branch-slug collision and ambiguous phase lookup contradict that guarantee (999.39/45). `statepath.resolve` computes a key; it does not prove unique review identity.
- Identity is not just title plus line numbers and is not devoid of content anchoring: `score.py:536` hashes file, canonical line content and title. Nearby/coverage decisions are separate. This sharpens 999.31's description without changing its deferred status or resolving the wrong-keep probes.
- `.turingmind/` is live review state, as `05-state.md` demonstrates; it must not be removed as “legacy orchestration.” `.orchestrator/` is distinct. `STRUCTURE.md`'s all-untracked statement is also too broad: ROADMAP/STATE/PROJECT are tracked despite ignore rules. No cleanup authorized.
- `INTEGRATIONS.md` incorrectly implies a hard Codex confidence cap of 45. The real translator maps `confidence=0.9` to `agent_confidence=90` (fresh offline probe); prompt calibration is not enforced clamping. Preserve scoring; correct disclosure under existing 999.41 if reused publicly. The actual model is the configured CLI default, not a guaranteed GPT-5-codex model.
- `STACK.md` omits `finalize_inputs.py` from its exclusive subprocess list; that module also runs bounded argv-list git commands. Its Python 3.11+ statement describes TOML support, not an already-established support policy; minimum-version declaration remains 999.41.
- Test size, prose locks and an import-only stdlib check are not proofs of semantic coverage, isolation, or absence of networking. End-to-end is not synonymous with browser testing. Keep real-chain/CLI evidence, live model journeys and per-candidate skip records distinct; map prose cannot upgrade an untested path to verified.

These are documentation accuracy corrections, not newly reproduced runtime bugs. The generated/local maps were left intact; this tracked reconciliation prevents their overclaims from silently becoming acceptance criteria. No new paid/live checks or implementation changes.

### Finish and limits

The only additional implementation work item is safe helper invocation (999.43). Legacy decision and scope leads are bounded acceptance investigations inside the already selected closure/scope repairs (999.44/45); a reproduced safety failure cannot be waived merely to keep the count small. If a safe refusal suffices, ship that rather than redesigning identity. Every other family above has a disposition/reopening trigger and stays outside the milestone.

Recommendation remains **submit after specific fixes**, with no new efficacy claim. Candidate installation, supported-route live checks, portal validation, model interpretation and real usage costs remain unverified by this disposition pass. Historical fixes/tests and offline probes do not substitute for those checks. This inventory covers available local records, not unseen external issues or unknown defects.

</details>
