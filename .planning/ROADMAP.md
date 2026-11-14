# Roadmap: vibe-check

Updated 2026-11-13 (v2.15 Lean orchestration active as of 2026-11-13: Phases 62–65 mapped to its 17 requirements; requirements and roadmap defined, no code changed; Reviewer efficiency stays conditional and is not activated). v2.14 Decision reliability shipped as 2.14.0 (PR #7, squash ecc3299, tag v2.14, GitHub release), then 2.14.1 (PR #8, squash dd8e4ab, tag v2.14.1, GitHub release) fixing 999.28. Each phase begins by reproducing its failure, or recording the behaviour or measurement it intends to change, on current code. A path that does not reproduce is recorded and dropped, never replaced with invented work.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)
- ✅ v2.13 Reliable fix closure and recovery -- Phases 56–58 (shipped 2026-10-28 as 2.13.0; known limits in backlog 999.23–999.26) — [archive](milestones/v2.13-ROADMAP.md)
- ✅ v2.14 Decision reliability -- Phases 59–61 (shipped as 2.14.0; 2.14.1 patch fixed 999.28; known limits 999.23 residuals, 999.26, 999.27, 999.29, 999.30) — [archive](milestones/v2.14-ROADMAP.md) (shipped 2026-10-30)
- 🚧 v2.15 Lean orchestration -- Phases 62–65 (in progress)

Active milestone: v2.15 Lean orchestration (Phases 62–65). Reviewer efficiency is scoped below and stays conditional; backlog records remain the evidence ledger.

<details>
<summary>✅ v2.14 Decision reliability (Phases 59–61) — SHIPPED 2026-10-30</summary>

- [x] Phase 59: Stale decisions and lost deferrals (6/6 plans) — completed 2026-10-29
- [x] Phase 60: Exact change evidence and reliable Finalize (16/16 plans) — completed 2026-10-30
- [x] Phase 61: Release gate — decision reliability (5/5 plans) — completed 2026-10-30

Shipped as 2.14.0 via release PR #7 (squash `ecc3299`, tag `v2.14`, GitHub release v2.14). Audit tech_debt 16/16 ([audit](milestones/v2.14-MILESTONE-AUDIT.md)). Details: [archive](milestones/v2.14-ROADMAP.md).

</details>

### 🚧 v2.15 Lean orchestration (Phases 62–65, in progress)

- [ ] **Phase 62: Baseline and continuous test run** - A go/no-go cost and quality baseline from existing local records, the pinned 2.14.1 behavioural baseline and the improvement criterion are recorded before any extraction, and the offline suite runs on every push and pull request to `main` (999.12)
- [ ] **Phase 63: Finalize extraction and cross-call variable check** - Finalize's input assembly and gate/report handoff run through stdlib helpers with the same gate decisions and reports as 2.14.1, and one general check catches shell variables read across Bash calls
- [ ] **Phase 64: Optional bounded extension (conditional)** - After Finalize passes equivalence, a recorded decision selects at most one further family or skips; a recorded skip completes the phase (999.32 is a candidate)
- [ ] **Phase 65: Release gate — orchestration equivalence and useful savings** - Offline suite, archived replay and mode/recovery checks pass on the exact candidate against 2.14.1, and the savings in loaded prose or mechanical steps are shown separately from tokens or dollars

**Codex integration decision (owner, 2026-10-28):** Retain the existing optional OpenAI Codex plugin/companion integration. Lean orchestration simplifies vibe-check's own mechanics; it does not replace or vendor the companion, build a direct Codex adapter, or adopt model-gateway/agent-spawn routing. Keep the user's configured Codex default, not a pinned Astra model. Small dependency/setup, run/skip disclosure, model-label and update-compatibility improvements are captured in [maintenance](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure); they add no phase, requirement, acceptance criterion or release blocker to v2.14.

**Goal:** Reduce model-interpreted mechanical instructions and fragile handoffs while preserving the behavior delivered by Decision reliability.

**Status:** Activated 2026-11-13 as v2.15 via `/bm:new-milestone` (research skipped by the owner; scope is this owner-approved section; requirements BASE, CI, FINX, XVAR, EXT, GATE in REQUIREMENTS.md, 17 mapped). The prerequisite is met: Decision reliability passed its release gate and shipped (2.14.0, then 2.14.1). The equivalence baseline is plugin 2.14.1 (PR #8, squash `dd8e4ab`, tag `v2.14.1`). Estimated size: medium, with Finalize as the initial implementation boundary. Requirements and roadmap are defined; no code has changed.

**Sequence:** The baseline and the continuous test run come before any extraction (Phase 62); the test run is the standing check behind the later equivalence gate. Finalize is the first and only committed extraction, and the cross-call variable check rides with it (Phase 63). The extension is conditional and may close as a recorded skip (Phase 64). The release gate is last (Phase 65). Finalize alone can satisfy the milestone.

**No growth per round (owner, 2026-10-17, restated 2026-10-28):** a new review, gap or fix round is not a reason to add points to a task, plan, success criterion or acceptance list. A round may add work only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow. Everything else is carried.

**Out of scope:** Reviewer routing, narrower reviewer context, new agents, model downgrades, scoring retunes, new services and broad cleanup. Missing cost attribution ends accounting work, not the milestone; use labeled footprint/operation evidence instead.

**Next action:** `/bm:execute-phase 62` on branch `feat/v2.15-phase-62` (11 plans, 6 waves). This roadmap does not authorize paid runs.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 62. Baseline and continuous test run | 6/11 | In Progress|  |
| 63. Finalize extraction and cross-call variable check | 0/TBD | Not started | - |
| 64. Optional bounded extension (conditional) | 0/TBD | Not started | - |
| 65. Release gate — orchestration equivalence and useful savings | 0/TBD | Not started | - |

## Phase Details

### Phase 62: Baseline and continuous test run

**Goal**: Before any extraction starts, the owner has a go/no-go note on cost visibility built from existing records, the 2.14.1 behaviour and footprint are pinned as the comparison baseline with the improvement criterion written down, and every push and pull request to `main` runs the offline suite automatically (999.12)
**Depends on**: Nothing in v2.15 (first phase). Uses the released 2.14.1 baseline (`dd8e4ab`) and its archived replay results as they are
**Requirements**: BASE-01, BASE-02, BASE-03, BASE-04, CI-01, CI-02
**Approved scope** (owner, 2026-10-28; continuous test run added 2026-11-13): *Baseline cost and quality with existing evidence (999.12, bounded feasibility).* Inspect local archives only; identify trustworthy per-run/per-lane model, input/output/cache usage, retries and elapsed time where present. Report missing attribution explicitly; do not reconstruct invented usage or treat subscription usage as a bill. Record current mode-path bytes and actual loaded-file traces separately from token and price estimates. Retain a pinned current-code behavioral baseline and archived replay results before refactoring. **Done when:** a go/no-go note names available fields, the smallest useful report, the intended comparison workload, and the improvement criterion chosen before implementation. If reliable attribution is unavailable, stop accounting work and use clearly labeled footprint/operation counts. No new telemetry service, accounting platform, paid baseline or enforceable-dollar-cap claim. *Continuous test run.* Add one GitHub Actions workflow that runs the existing offline suite and the stdlib-only check on every push and pull request to `main`. It uses no secrets, no paid runs and no live model calls, and it changes no branch-protection setting. **Done when:** `main` shows a green run on the release baseline and a deliberately failing commit on a throwaway branch shows red. This is the standing check behind the equivalence gate in Phase 65; it does not replace the release gates or any live check.
**Success Criteria** (what must be TRUE):

  1. A go/no-go note built from existing local records only names which usage fields are trustworthy per run and per lane (model, input/output/cache usage, retries, elapsed time), states what attribution is missing, and names the smallest useful report; no usage is reconstructed or invented and no paid run is started
  2. Current mode-path bytes and actual loaded-file traces are recorded for plain review, deep review and Finalize, kept separate from any token or price estimate
  3. A pinned behavioural baseline of the 2.14.1 code and its archived replay results are retained before any refactoring starts
  4. The comparison workload and the improvement criterion for this milestone are written down before any extraction work begins; if reliable attribution is unavailable, accounting work stops and labelled footprint/operation counts are named as the evidence instead
  5. One GitHub Actions workflow runs the existing offline suite and the stdlib-only check on every push and every pull request to `main`, with no secrets, no paid runs, no live model calls and no branch-protection change; `main` shows a green run on the release baseline and a deliberately failing commit on a throwaway branch shows red

**Plans:** 6/11 plans executed

Plans:
**Wave 1**

- [x] 62-01-PLAN.md — stdlib-only check, the left-out list guard and the skip-set guard for CI, each with mutants (CI-01)
- [x] 62-02-PLAN.md — the one GitHub Actions workflow and its shape locks, one break test per rule (CI-01)
- [x] 62-03-PLAN.md — step-counting rule as a script, 2.14.1 step counts, improvement criterion and comparison workload (BASE-04)
- [x] 62-04-PLAN.md — Finalize capture harness pinned to 2.14.1 and the two close routes (BASE-03)
- [x] 62-05-PLAN.md — mode-path bytes and labelled loaded-file traces for plain review, deep review and Finalize (BASE-02)
- [x] 62-06-PLAN.md — usage-field reader and the cost visibility go/no-go note (BASE-01)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 62-10-PLAN.md — the remaining three Finalize situations and the five-situation record with a fingerprint (BASE-03)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 62-07-PLAN.md — suite and replay baseline and the manifest with one verify command (BASE-03)

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 62-11-PLAN.md — the plain-terms baseline page and kit README, figures locked to the records (BASE-03)

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 62-08-PLAN.md — CI proof before merge: recording run and pinned skip list, green on the phase branch, red on a throwaway branch (CI-02)

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 62-09-PLAN.md — pull request, owner go/no-go and merge, main's first run, phase close (CI-02)

Run order is by wave, not by plan number: wave 1 = 01–06, wave 2 = 10, wave 3 = 07, wave 4 = 11, wave 5 = 08, wave 6 = 09. Plans 08 and 09 run on the phase branch in the primary checkout, without worktree isolation.

### Phase 63: Finalize extraction and cross-call variable check

**Goal**: Finalize's mechanical steps run through tested stdlib helpers and behave exactly as in 2.14.1, with less model-interpreted prose on the same paths, and a shell variable read across Bash calls is caught by one general check in any phase file
**Depends on**: Phase 62 (the pinned baseline, the comparison workload and the improvement criterion must exist first; the continuous test run is the standing check)
**Requirements**: FINX-01, FINX-02, FINX-03, FINX-04, FINX-05, XVAR-01, XVAR-02
**Approved scope** (owner, 2026-10-28; cross-call variable check added 2026-11-13): Reuse existing stdlib helpers and the single-writer state path to assemble Finalize inputs and perform the gate/report handoff. Return compact structured results and explicit next actions. Keep judgment, owner decisions and reviewer calls in the existing host; remove superseded prose and locks while retaining behavioral invariants and recovery guidance. **Done when:** equivalent inputs produce the same gate decisions and reports as the released Decision reliability baseline; missing, malformed or stale inputs fail visibly; restart/retry works across fresh shells. Compare loaded prose and helper/tool steps on the same paths before and after. Revert the slice if it adds complexity without demonstrable benefit. Also add one general check (owner-approved 2026-11-13) that walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; today only the two repaired 999.25 cases are covered. It needs a mutant, and any phase file it flags is recorded with its repro before being changed. No new orchestration framework, wholesale state rewrite or changed model defaults.
**Success Criteria** (what must be TRUE):

  1. Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the 2.14.1 baseline
  2. Missing, malformed or stale Finalize inputs stop with a plain message; a failed or refused attempt writes no report and archives nothing; restart and retry work across fresh shell calls
  3. Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host
  4. Loaded prose and helper/tool steps on the same Finalize paths are compared before and after against the Phase 62 criterion; the slice is reverted if it adds complexity without a demonstrated benefit
  5. One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips; any phase file it flags is recorded with its reproduction before it is changed

**Plans**: TBD

### Phase 64: Optional bounded extension (conditional)

**Goal**: The owner has a recorded decision on whether one more family is worth extracting; if one is selected it behaves exactly as before with demonstrated savings, and if not, the skip is on record and the milestone proceeds on Finalize alone
**Depends on**: Phase 63. This phase activates only after the Finalize extraction has passed its equivalence checks; it does not start before that
**Requirements**: EXT-01
**Conditional**: A recorded skip satisfies EXT-01 and completes this phase. A skip changes no code. If the Finalize slice is inconclusive or was reverted, this phase closes as a recorded skip.
**Approved scope** (owner, 2026-10-28; 999.32 named as a candidate 2026-11-13): Only consider repeated evidence/envelope assembly or deterministic dispatch selection when the first extraction passes equivalence checks and the baseline identifies another worthwhile source of repeated work. Choose at most one additional family during detailed scoping; defer the remainder rather than grow the milestone. **Done when:** the selected slice preserves roster, prompts/evidence, scores, decision eligibility and recovery behavior, with demonstrated footprint/operation savings. Skip this item if the first slice is inconclusive; Finalize alone can satisfy the milestone. The 999.32 fix-loop Rerun step is a candidate family alongside these two.
**Success Criteria** (what must be TRUE):

  1. No extension work starts until Phase 63's Finalize extraction has passed its equivalence checks
  2. A recorded decision either skips the extension or selects at most one family (repeated evidence/envelope assembly, deterministic dispatch selection, or the 999.32 fix-loop Rerun step) that the Phase 62 baseline identifies as worthwhile; families not selected are deferred, not added to this milestone. A recorded skip satisfies this phase
  3. If a family is selected, its slice preserves roster, prompts/evidence, scores, decision eligibility and recovery behaviour against the 2.14.1 baseline, with demonstrated footprint/operation savings

**Plans**: TBD

### Phase 65: Release gate — orchestration equivalence and useful savings

**Goal**: The release candidate is proven equivalent to 2.14.1 in behaviour, its reduction in loaded prose or mechanical steps is shown without any unsupported cost claim, and it ships through the existing close workflow without waiting for reviewer-efficiency work
**Depends on**: Phase 63, and Phase 64 closed (as a recorded skip or a completed slice)
**Requirements**: GATE-04, GATE-05, GATE-06
**Approved scope** (owner, 2026-10-28): Run the applicable full offline suite, archived replay and mode/recovery integration checks on the exact candidate, comparing against the released reliability baseline. Unexpected behavioral differences block release. **Done when:** safeguards and independent fix verification remain intact and the included extraction demonstrably reduces loaded prose or mechanical work without an unaccounted regression. Report byte/operation savings separately from tokens or dollars; claim billing savings only with comparable usage evidence. Any approved live validation covers changed orchestration paths under the default configuration; offline parity alone does not prove live model quality. Document any unmeasured behavior and require an explicit release waiver if needed. Publish independently; reviewer-efficiency experiments are not a prerequisite.
**Success Criteria** (what must be TRUE):

  1. On the exact release candidate, the full offline suite, archived replay and mode/recovery integration checks pass against the 2.14.1 baseline; any unexpected behavioural difference blocks release
  2. The release record shows safeguards and independent fix verification intact and a demonstrated reduction in loaded prose or mechanical steps, with byte/operation savings reported separately from tokens or dollars and no billing-savings claim without comparable usage evidence
  3. Live validation of changed orchestration paths runs only under an approved bounded proposal; otherwise the unmeasured behaviour is documented and the release goes out under an explicit owner waiver

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

### 999.29: A decided finding re-reported under a reworded title shows as new (2.14.1 live check)

Seen in the 2.14.1 live check (default route, unchanged tree): the bugs lane re-titled the deferred SQL-injection finding on pass 2, so the row got a new stable_hash and was shown as an undecided new finding with no "(was: deferred)" context. The original decision was kept as a member obligation (no nearby stamp, not re-asked). In 2.14.0 this was masked by the false 999.28 nearby reason. Fails toward asking; nothing lost. Candidate direction: carry decision context onto a lead whose members include a decided obligation for the same file and line. Reproduce on the real chain first. Not scheduled.

### 999.30: Snapshot store and temp leftovers are never pruned (2.14.1 known limit)

`.turingmind/worktree-snap/objects` grows by the changed blobs of each default/GSD pass, and a pass that stops before Phase 3 leaves a `vc-worktree-snap-<nonce>` folder in the system temp directory (unusable by any other pass). Deleting either is safe (the next pass re-asks once). Candidate: prune store objects not reachable from the last recorded `reviewed_tree`, and sweep temp folders older than a day in `take`. Maintenance, not scheduled.

### 999.31: Decision identity design (groups the remaining decision-continuity limits)

Owner decision 2026-11-13: stop scheduling the remaining decision-continuity limits one at a time and treat them as one design question, to be taken after Lean orchestration ships. This entry commits no work, phase numbers or dates.

The shared cause: a decision is tied to a finding by its title-derived `stable_hash` plus nearby line numbers, so a reworded title or a new identical copy needs another special rule. This area was repaired in v2.11, v2.12, v2.13 (Phase 57), v2.14 (Phases 59–60) and 2.14.1 and still has open shapes. Every open shape fails toward asking again; none is a silent keep.

Grouped here (each original record and repro stays where it is):

- 999.23 residuals: D-01 later-pass over-ask, WR-01 over-ask #2, and the WR-01/WR-02 card wording.
- 999.26: wordier plain-English title references ask a follow-up.
- 999.29: a decided finding re-reported under a reworded title shows as new.
- `--all` reviews keep no decisions between runs (README known limit; 999.24 R10).

Not grouped: 999.27 (`head_sha` scope trust) is a security question, and 999.30 (pruning) is maintenance.

Design question to answer before any code: what a decision is attached to (for example the file plus the code it was made on, instead of the title plus a line window), and how old decisions migrate. Reproduce each grouped shape on current code first. A reproduced silent keep or lost deferral is actionable immediately and does not wait for this item.

### 999.32: Fix loop stops instead of taking Rerun after a typed defer (C4, moved from 999.28)

Moved out of 999.28 on 2026-11-13 so it is not lost inside a shipped item. Reproduced in the Phase 61 live smoke (61-LIVE-SMOKE.md S2) and again in the 2.14.1 live check: after a typed `defer` in the fix-loop card flow (`phases/review/50-fix-loop.md`), the model stops and lists choices instead of taking the automatic Rerun step. Fails toward stopping: decisions are saved and nothing is lost, at the cost of one manual step. This is model-interpreted prose, so a fix belongs with the Lean orchestration work if the fix loop is chosen as its optional extension; otherwise reproduce first. Not scheduled.

### 999.28: SHIPPED in 2.14.1 — Default route: decisions on uncommitted code re-asked every pass (false nearby reason) (Phase 61 C1)

Fixed in 2.14.1 (PR #8, squash dd8e4ab, tag v2.14.1) on every route except `--all`, including the same re-ask found on PR and range reviews of committed code (owner chose to fix both before release). Debug record: `.planning/debug/999-28-uncommitted-reask.md`. Live check (default route only, owner-approved): unchanged tree kept the decision; an edit 3 lines above re-asked with the true reason. PR/range/GSD live check skipped by owner decision (tests only). C4 (model stops instead of Rerun after a typed defer) reproduced again and is now tracked as 999.32.

Original record: Reproduced in the Phase 61 live smoke (61-LIVE-SMOKE.md S1, C1): on the default review of uncommitted code, a finding deferred or dismissed at pass 1 was re-asked at pass 2 on a byte-identical working tree, and the card said "code next to it changed since your decision", which was false. Cause (from 61-RELEASE-RECORD.md Carried C1): on pass >= 2 the ranges come from `git diff <last-reviewed-sha>`; before any commit that sha is still HEAD, so the whole uncommitted block counts as changed every pass. Fails toward asking: nothing is lost and Close out completes. Probably predates 2.14 (2.13 also took ranges from `git diff HEAD` each pass; inferred from the 2.13 instructions, not tested). Owner ruling 2026-10-30 (61-SIGNOFF.md Decision 1, first A, then switched the same day to B): ships in 2.14.0 as the first Known limit in the release notes and in the README's "Known limitations (2.14)" (candidate C2 47978aa, README-only change; pending owner re-sign). Also carried here (C4): in S2 the model stopped and listed choices instead of taking the fix loop's Rerun after a typed defer (fails toward stopping; decisions saved). Candidate direction: compare the working-tree content against what the decision saw (not HEAD) so an unchanged uncommitted block does not count as changed. Reproduce on the real chain first; needs a fixture and a mutant. Reopen as worse if a re-ask on unchanged committed code is reproduced. Not scheduled.

### 999.12: Narrow: Cost visibility feasibility — Lean orchestration

Inspect existing local usage records to determine whether a review's usage can be attributed reliably. Report available fields, missing data, pricing assumptions and the distinction between estimated, measured and billed cost. Do not start paid reviews to generate a baseline or invent per-agent usage.

Finish with a go/no-go recommendation for the smallest useful reporting change. Stop if reliable attribution is unavailable; document the limitation rather than build new accounting infrastructure. Existing chunk limits and estimates are not enforceable dollar caps. Scheduled as v2.15 Lean orchestration Phase 62 (BASE-01..04, activated 2026-11-13). This check does not block correctness repairs; missing attribution stops accounting work, not the reliability milestone. Budget-control implementation and cross-repo orchestration changes require their own scope.

### Maintenance: Keep the Codex companion; improve setup and disclosure

Owner decision 2026-10-28: retain the existing optional Codex plugin integration. Capture dependency/setup documentation, accurate joined/skipped outcomes, configured-default model labels and bounded compatibility checks after companion updates in [the maintenance record](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure). Outside v2.14; no new milestone or integration redesign. Preserve current review targeting, guards and optional native-only behavior.

## Planning boundaries

- v2.15 Lean orchestration is the only active milestone (activated 2026-11-13; requirements and roadmap defined, Phases 62–65; no code changed). Its scope includes the continuous test run and the general cross-call variable check (owner-approved 2026-11-13). Paid runs, new agents and publication require explicit owner approval; this roadmap does not authorize them.
- v2.13 shipped as 2.13.0 with owner-accepted known limits (999.23–999.26); Phase 57 closed under the D-19 hard stop, Phase 58 with live ref extraction unverified (D-15).
- v2.12 shipped as 2.12.0 under owner waiver; outcome remains **UNMET — measurement incomplete**. Phase 55 and cancelled Phase 54 sweeps remain deferred.
- Reuse valid review evidence for unchanged code; scope new checks to changed code and affected callers. Any paid check requires an explicit bounded price proposal and owner approval.
- One branch and one PR per phase (owner decision 2026-10-23): `feat/<milestone>-phase-<N>`, each cut from `main` after the previous phase's PR merges; delete each branch locally and on GitHub after its PR merges.
- Routine cleanup remains in [maintenance](backlog/MAINTENANCE.md).
- [Lower-value ROI candidates](backlog/archive/2026-10-18/ROI-DEFERRED.md) are archived with reopening conditions, not scheduled or declared complete.

## Release records

- [v2.14 archived roadmap](milestones/v2.14-ROADMAP.md): decision reliability (stale decisions, exact change evidence, reliable Finalize); known limits 999.23 residuals, 999.26–999.28.
- [v2.13 archived roadmap](milestones/v2.13-ROADMAP.md): reliable fix closure, decision continuity and recovery; known limits 999.23–999.26.
- [v2.12 archived roadmap](milestones/v2.12-ROADMAP.md): shipped reliability improvements; measurement incomplete.
- [v2.11 archived roadmap](milestones/v2.11-ROADMAP.md): last measured milestone, false alarms 5/18 and catches 15/15, with release/measurement caveats.
- [All milestone history](MILESTONES.md).
- [Archived backlog and disposition ledger](backlog/archive/2026-10-18/README.md).
