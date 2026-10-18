# Roadmap: vibe-check

Updated 2026-10-18. ROI order: reliable fix closure, clear actions and recovery, then a separate cost feasibility check. Lower-value work is archived. No milestone is active; versions and phase plans remain unassigned. Next new phase number is 56.

## Milestones

- ✅ v2.11 Quiet loop -- Phases 45–50 (2.11.0 and 2.11.1 shipped 2026-10-08)
- ✅ v2.12 Quiet without hiding -- Phases 51–54; Phase 55 measurement deferred, outcome UNMET under owner waiver (shipped 2026-10-17)

## Next milestone: Reliable fix closure and recovery

**Goal:** Let independently verified fixes close reliably, preserve owner decisions, and make recovery from an inconclusive check understandable.

1. [ ] **Verified fixes stay fixed (remaining 999.22).** First reproduce the one-pass independent re-check limit and relevant carried-Codex/general closure paths. Repair demonstrated failures with a bounded retry on current evidence, without a dummy code change or repeated owner confirmation. Preserve independent verification and reject stale evidence. Done when: focused regression scenarios cover an inconclusive check followed by a successful retry on unchanged repaired code, changed-code rejection, and a still-applies verdict remaining open. Do not rebuild initial confirmed-fix routing already shipped in v2.12.
2. [ ] **Decision continuity within closure.** Reproduce any lost defer/dismiss decision on regrouping or unrelated edits before changing identity rules. Fix only demonstrated failures in the closure/recovery path; keep decisions bound to their evidence. Done when: regression fixtures preserve applicable decisions and reopen findings when relevant evidence changes. Broader duplicate presentation and cross-repo gate consumers are excluded.
3. [ ] **Clear actions and recovery (999.13 subset).** Correct the misleading “Fix all” label and explain which findings require individual decisions. Reconcile existing recovery guidance and actionable rejection/orphan explanations. Done when: labels match behavior and an inconclusive re-check has a clear, bounded recovery path without automatic closure or a new manual.

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
