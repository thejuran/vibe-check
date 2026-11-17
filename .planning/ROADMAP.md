# Roadmap: vibe-check

Updated 2026-11-16 (v2.15 Lean orchestration closed and archived: Phases 62–65 complete, audit tech_debt 17/17; publishing as 2.15.0 through the release PR per 65-CLOSE-RUNBOOK.md — not yet merged, tagged or released). Each phase begins by reproducing its failure, or recording the behaviour or measurement it intends to change, on current code. A path that does not reproduce is recorded and dropped, never replaced with invented work.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)
- ✅ v2.13 Reliable fix closure and recovery -- Phases 56–58 (shipped 2026-10-28 as 2.13.0; known limits in backlog 999.23–999.26) — [archive](milestones/v2.13-ROADMAP.md)
- ✅ v2.14 Decision reliability -- Phases 59–61 (shipped as 2.14.0; 2.14.1 patch fixed 999.28; known limits 999.23 residuals, 999.26, 999.27, 999.29, 999.30) — [archive](milestones/v2.14-ROADMAP.md) (shipped 2026-10-30)
- 🚧 v2.15 Lean orchestration -- Phases 62–65 (in progress: closed and archived, release PR in review; 2.15.0 not yet published) — [archive](milestones/v2.15-ROADMAP.md)

<details>
<summary>✅ v2.14 Decision reliability (Phases 59–61) — SHIPPED 2026-10-30</summary>

- [x] Phase 59: Stale decisions and lost deferrals (6/6 plans) — completed 2026-10-29
- [x] Phase 60: Exact change evidence and reliable Finalize (16/16 plans) — completed 2026-10-30
- [x] Phase 61: Release gate — decision reliability (5/5 plans) — completed 2026-10-30

Shipped as 2.14.0 via release PR #7 (squash `ecc3299`, tag `v2.14`, GitHub release v2.14). Audit tech_debt 16/16 ([audit](milestones/v2.14-MILESTONE-AUDIT.md)). Details: [archive](milestones/v2.14-ROADMAP.md).

</details>

### 🚧 v2.15 Lean orchestration (Phases 62–65, in progress: closing — release PR in review)

- [x] **Phase 62: Baseline and continuous test run** - 2.14.1 baseline pinned, cost visibility NO-GO (owner), offline suite on every push and PR to `main` (11/11 plans) — completed 2026-11-14
- [x] **Phase 63: Finalize extraction and cross-call variable check** - Finalize's gate inputs from one tested stdlib helper (92 → 83 steps on the extraction alone); one general cross-call variable check (11/11 plans) — completed 2026-11-15
- [x] **Phase 64: Optional bounded extension (conditional)** - Closed as a recorded skip (owner); evidence/envelope assembly, dispatch selection and 999.32 deferred — completed 2026-11-15
- [x] **Phase 65: Release gate — orchestration equivalence and useful savings** - G1–G11 PASS on candidate `b073e31`; replay 170 runs, 0 differences; live smoke PASS; Close out 136,114 → 131,381 bytes, 92 → 85 steps (7/7 plans) — completed 2026-11-17

Audit tech_debt, 17/17 requirements, integration 7/7, flows 2/2 ([audit](milestones/v2.15-MILESTONE-AUDIT.md)). Full phase details: [archive](milestones/v2.15-ROADMAP.md). Known limits and carried review items: 999.34–999.39. Remaining close steps (runbook 4–10): release PR + CI on its head (G12), owner merge OK, squash merge, tree-identity check, tag `v2.15` on `origin/main`, GitHub release, plugin update.

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

**Phase 63 (2026-11-15):** the general cross-call variable check now exists (`plugins/vibe-check/scripts/test_cross_call_vars.py`, every file under `phases/`); every place it flagged was fixed and its remaining exception and known limits are tracked in 999.36. Finalize's gate inputs now come from one helper call (`finalize_inputs.py`), so R1's traceback no longer reaches a Finalize fence.

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

### 999.39: Phase 65 code review carry (65-REVIEW.md, owner ruling 2026-11-16)

The owner chose "Ship + backlog (Recommended)" (AskUserQuestion, main session, 2026-11-16): ship 2.15.0 as signed off, name the lookup gap as a release-notes known limit, and carry both items here. Neither is a regression from 2.14.1.

- SA-01 (lookup, pre-2.15): the GSD phase lookup in `00-scope.md` silently picks one folder when two phase folders share a name (e.g. `v1-phases/01-setup` and `v2-phases/01-setup`) instead of the "multiple matches" stop its instructions describe, and accepts a container name (`phases`, `milestones`, `v1-phases`) as a phase. Two phases can then share one saved-progress file and Close out can close on the wrong findings (wrong close, unusual layouts only). Fix: refuse multiple matches and container names in the lookup fence, test-first with mutants.
- WR-01 (wording, from the WR-02 fix): the sentence at `05-state.md:16` says "two GSD phases never share one state file"; the check only refuses an empty id. Reword to claim only that, together with the SA-01 fix.
- Info: IN-01 (cross-class helper borrow at `test_pasted_name_guard.py:400`) and IN-02 (label-suffix-gated message check at lines 334–335) are test tidiness only.
- SA-02 (no live GSD check of the printed-id substitution) is covered by the 2.15.0 waiver; if a live model drops the id, GSD reviews stop safely with "phase id is empty".

Not scheduled.

### 999.12: Narrow: Cost visibility feasibility — Lean orchestration

Inspect existing local usage records to determine whether a review's usage can be attributed reliably. Report available fields, missing data, pricing assumptions and the distinction between estimated, measured and billed cost. Do not start paid reviews to generate a baseline or invent per-agent usage.

Finish with a go/no-go recommendation for the smallest useful reporting change. Stop if reliable attribution is unavailable; document the limitation rather than build new accounting infrastructure. Existing chunk limits and estimates are not enforceable dollar caps. Scheduled as v2.15 Lean orchestration Phase 62 (BASE-01..04, activated 2026-11-13). This check does not block correctness repairs; missing attribution stops accounting work, not the reliability milestone. Budget-control implementation and cross-repo orchestration changes require their own scope.

**Outcome (2026-11-14):** the owner recorded NO-GO on cost visibility, following the note's recommendation (`.planning/phases/62-baseline-and-continuous-test-run/62-COST-NOTE.md`, `## Owner decision`). Accounting work stops; the milestone uses the labelled byte and step counts from the Phase 62 baseline as its evidence, and no usage-report backlog item is filed.

### Maintenance: Keep the Codex companion; improve setup and disclosure

Owner decision 2026-10-28: retain the existing optional Codex plugin integration. Capture dependency/setup documentation, accurate joined/skipped outcomes, configured-default model labels and bounded compatibility checks after companion updates in [the maintenance record](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure). Outside v2.14; no new milestone or integration redesign. Preserve current review targeting, guards and optional native-only behavior.

## Planning boundaries

- v2.15 Lean orchestration (Phases 62–65) is closed and archived; 2.15.0 is publishing through the release PR per `65-CLOSE-RUNBOOK.md`. No next milestone is scoped; 999.31 (decision identity design) waits for it. Paid runs, new agents and publication require explicit owner approval; this roadmap does not authorize them.
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
