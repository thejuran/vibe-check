# Roadmap: vibe-check

Updated 2026-10-21 (CONCERNS.md comparison: one closure path added to item 1, one check-first bug added to item 3). ROI order: reliable fix closure, clear actions and recovery, then a separate cost feasibility check. Lower-value work is archived. No milestone is active; versions and phase plans remain unassigned. Next new phase number is 56.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)

## Next milestone: Reliable fix closure and recovery

**Goal:** Let independently verified fixes close reliably, preserve owner decisions, and make recovery from an inconclusive check understandable.

<a id="closure-999-22"></a>

1. [ ] **Verified fixes stay fixed (remaining 999.22).** First reproduce the one-pass independent re-check limit and relevant carried-Codex/general closure paths. Repair demonstrated failures with a bounded retry on current evidence, without a dummy code change or repeated owner confirmation. Preserve independent verification and reject stale evidence. Done when: focused regression scenarios cover an inconclusive check followed by a successful retry on unchanged repaired code, changed-code rejection, and a still-applies verdict remaining open. Do not rebuild initial confirmed-fix routing already shipped in v2.12.

   **Reported regression example (2026-10-20):** Six open rows are already fixed, but the scorer cannot close them automatically. Each row's pinned line is unchanged: fixes added code beneath it, while the `arrFacade` fix added only tests. Four of the six findings came from Codex, which cannot be asked to recheck its own findings. The relevant reviewers and full test runs confirm each fix, yet the rows still require dismissal with a reason such as “fixed in <sha>” on the finding card or at close-out.

   **Implementation coverage:** Reproduce this six-row case and cover both code added beneath an unchanged pinned line and the tests-only `arrFacade` fix, including the four Codex-origin rows. Verify that eligible independent evidence can close fixed findings without changing their pinned lines merely to trigger rechecking or requiring repetitive manual dismissal. Retain evidence freshness checks and keep unresolved or still-applicable findings open. Source: owner-provided example; row IDs, fix SHAs and test-run references were not supplied and should be recovered when building the regression fixture.

   **Added closure path (owner decision 2026-10-21): `/review` cannot close a `/deep-review`-only finding.** A carried finding closes only when its own originating agent rechecks it, so a finding raised by an agent `/vibe-check:review` never dispatches (e.g. `test-sufficiency`) stays “needs recheck” under `/review` regardless of whether the code is fixed. Source: `.planning/phases/52-hardening-accepted-fix-harness/deferred-items.md` (“From 52-11 (still open)”), previously an undecided product question. Reproduce it first alongside the six-row case; if reproduced, cover it in the same closure regression scenarios — an eligible independent recheck under `/review` (or a clear, bounded explanation of why it cannot close there) — without weakening independent verification.

2. [ ] **Decision continuity within closure.** Reproduce any lost defer/dismiss decision on regrouping or unrelated edits before changing identity rules. Fix only demonstrated failures in the closure/recovery path; keep decisions bound to their evidence. Done when: regression fixtures preserve applicable decisions and reopen findings when relevant evidence changes. Broader duplicate presentation and cross-repo gate consumers are excluded.
3. [ ] **Clear actions and recovery (999.13 subset).** Correct the misleading “Fix all” label and explain which findings require individual decisions. Reconcile existing recovery guidance and actionable rejection/orphan explanations. Done when: labels match behavior and an inconclusive re-check has a clear, bounded recovery path without automatic closure or a new manual.


   **Bug: Plain-English decision-card answers cause a repeated-card loop (2026-10-20).** During iPlayarr phase 45's vibe-check 2.12.0 deep review, the owner answered via Other: “fix the Browse recovery issue, then dismiss the 7 fixed rows and close out.” `batch_card.py parse` rejected the clear request with “answer does not match the grammar”. Following `phases/review/50-fix-loop.md`'s “Typed answer via Other” instruction to “re-show the SAME card once”, Claude repeated the identical card instead of translating the decision. The owner responded: “i just answered you”. Claude captured this as a local feedback draft titled “Re-asked a fix-loop card after the user gave a clear plain-language answer”; it was not previously a repository backlog entry.

   **Expected behavior / regression coverage:** Interpret an unambiguous plain-English decision against the displayed card, translate it into the validated numbered grammar, and continue the authorized fix/dismiss/close-out workflow without asking the same question again. For this exact card the mapping was `fix 5; dismiss 1,2,3,4,6,7,8`, with reason “fixed in review-pass commits, verified on recheck”. Preserve the owner's targets and reason, bind the translation to the current card, and retain normal fix verification and close-out checks. If a reference or reason is genuinely ambiguous or missing, ask only for that missing detail; do not guess, silently broaden the decision, or repeat the entire card. Cover both successful plain-English translation and ambiguous/stale-card cases in focused regression tests. Relevant paths: `plugins/vibe-check/phases/review/50-fix-loop.md` and `plugins/vibe-check/scripts/batch_card.py`; check the corresponding finalize decision flow too.

   **Related issue:** [Verified fixes stay fixed — 999.22](#closure-999-22). That issue leaves already-fixed rows awaiting owner decisions; this bug makes those decisions unnecessarily repetitive even after the owner clearly supplies them. The six-row closure example above is from the earlier pass; this later decision card contained seven already-fixed rows plus the Browse recovery finding.

   **Check first (owner decision 2026-10-21): finalize `fix N` re-asks Apply/Skip (bug C from the unfiled 2026-10-09 write-up).** Close-out's finalize answer `fix N` routes the subset into the fix-loop card, which asks Apply/Skip again for a row the owner already decided. Repro: deep review leaves a warning → fix loop Stop → Close out → finalize `fix N; defer M`. Two other vibe-check causes from that write-up — trailing `-- <reason>` refused and fix commits refused over apostrophes/semicolons in finding titles — are confirmed fixed in current code (`phases/shared/90-finalize.md`, `scripts/fixcommit.py` D-08); C was not re-verified. As the first reproduction step of this item, confirm whether C still occurs on current code. If it does, fix it with the plain-English repeated-card bug (same symptom: a decided answer is asked again) and add a regression fixture; if it does not, record that and do not file it. Relevant paths: `plugins/vibe-check/phases/shared/90-finalize.md` and `plugins/vibe-check/phases/review/50-fix-loop.md`.

**Sequence:** Reproduce the closure failure first, repair it with targeted validation, then align actions and recovery guidance. If the retry failure cannot be reproduced, stop that fix effort and reassess scope rather than invent a replacement project.

**Done when:** reproduced closure/decision bugs have focused regression evidence; distinct unresolved findings remain accounted for; labels and recovery guidance match behavior. Use local tests and existing replay evidence first. Any necessary live workflow check is separately bounded and budgeted.

**Scope:** Plugin closure and recovery only. No cost-accounting infrastructure, broad deduplication rewrite, scoring retune, new reviewer lane, orchestrator implementation, full B3/holdout campaign or automatic release.

## Backlog

### 999.12: Narrow: Cost visibility feasibility — separate task

Inspect existing local usage records to determine whether a review's usage can be attributed reliably. Report available fields, missing data, pricing assumptions and the distinction between estimated, measured and billed cost. Do not start paid reviews to generate a baseline or invent per-agent usage.

Finish with a go/no-go recommendation for the smallest useful reporting change. Stop if reliable attribution is unavailable; document the limitation rather than build new accounting infrastructure. Existing chunk limits and estimates are not enforceable dollar caps. This check is independent of, and does not block, Reliable fix closure and recovery. Budget-control implementation and cross-repo orchestration changes require their own scope.

## Planning boundaries

- This update authorizes planning changes, not implementation, paid runs, new agents, commits or publication.
- v2.12 shipped as 2.12.0 under owner waiver; outcome remains **UNMET — measurement incomplete**. Its noise target was not demonstrated. Phase 55 and cancelled Phase 54 sweeps remain deferred.
- Reuse valid review evidence for unchanged code; scope new checks to changed code and affected callers. Any paid check requires an explicit bounded price proposal and owner approval.
- Routine cleanup remains in [maintenance](backlog/MAINTENANCE.md).
- [Lower-value ROI candidates](backlog/archive/2026-10-18/ROI-DEFERRED.md) are archived with reopening conditions, not scheduled or declared complete.

## Release records

- [v2.12 archived roadmap](milestones/v2.12-ROADMAP.md): shipped reliability improvements; measurement incomplete.
- [v2.11 archived roadmap](milestones/v2.11-ROADMAP.md): last measured milestone, false alarms 5/18 and catches 15/15, with release/measurement caveats.
- [All milestone history](MILESTONES.md).
- [Archived backlog and disposition ledger](backlog/archive/2026-10-18/README.md).
