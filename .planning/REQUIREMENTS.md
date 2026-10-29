# Requirements: vibe-check v2.14 Decision reliability

**Defined:** 2026-10-28
**Core Value:** Catch real defects in a developer's changes before they ship — with high coverage and low noise — so a reviewer who can't manually audit the code can trust the agent's output as their safety net.

**Working rule:** reproduce each failure on current code through the real score → carry → card → finalize chain before fixing it. A path that does not reproduce is recorded and dropped — never replaced with invented work. Every fix lands with a failing-before/passing-after real-chain fixture and a mutation check. Local tests and archived replay first; any live check needs a separately approved bounded proposal.

**No growth per round (owner, 2026-10-28):** a new review, gap or fix round is not a reason to add points to a task, plan, success criterion or acceptance list. A round may add work only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow — with the reproduction cited. Everything else a round surfaces is recorded on the carried list with its rationale, and the task's points stay as planned.

**Source context:** ROADMAP.md "Next milestone: Decision reliability" (owner-approved 2026-10-28) and backlog records 999.23–999.25, which keep their original evidence (`.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/deferred-items.md`, 58-REVIEW-GAPS.md).

## v2.14 Requirements

### Stale decisions (STALE) — 999.23

- [ ] **STALE-01**: Each wrong-keep shape — CR-01 (identical sub-threshold copies), CR-02 (absorbed-member sidecars), CR-04 (a removed guard beside a covered member) — is reproduced on current code as a failing real-chain fixture before any fix; a shape that does not reproduce is recorded and dropped
- [ ] **STALE-02**: A decided finding whose evidence changed is asked again on the next run, and the card states the correct reopen reason, for every reproduced shape
- [ ] **STALE-03**: Evidence for a finding is pooled consistently by obligation/hash wherever it is read, so the outcome does not depend on which row happens to be the representative
- [ ] **STALE-04**: A deliberate dismiss/defer whose evidence is unchanged, or whose only nearby edits are unrelated, stays decided and is not re-asked
- [ ] **STALE-05**: Reordering rows, changing the lead, or splitting/merging groups gives the same reopen/keep result
- [ ] **STALE-06**: The work stops after one bounded implementation and review cycle; any unresolved silent keep is recorded as a residual and blocks a "reliability complete" claim instead of starting another repair round

### Deferred obligations (DEFR) — 999.23 D-20 edges

- [ ] **DEFR-01**: A deferred covered member removed by a valid `min_confidence` (reproduced at 45) stays visible as an open deferred obligation instead of disappearing without a card
- [ ] **DEFR-02**: The SA-02 `--all` "not in reviewed set" deferral drop gets one reproduction attempt on current code; it is fixed under DEFR-01's rule if it reproduces, otherwise recorded and dropped

### Exact change evidence (EVID) — 999.24

- [ ] **EVID-01**: Nearby/in-diff ranges come only from lines actually added or deleted, not the surrounding display context, so an edit at the intended five-line boundary reopens a decision and an edit outside it does not
- [ ] **EVID-02**: Ordinary, deletion-only and insertion hunks, and relocated findings, each produce correct ranges under a fixture that runs a real `git diff`
- [ ] **EVID-03**: Default, GSD, range, PR and `--all` routes each use the exact ranges or explicitly report an unsupported fixture, and nothing else in the pipeline still assumes three lines of context

### Reliable Finalize (FINL) — 999.25

- [ ] **FINL-01**: Finalize's blob-file path is printed and reused literally, so a fresh-shell walk through every fence reaches counts → gate → report with a valid path
- [ ] **FINL-02**: When the path is missing or a step is refused or retried, Finalize stops safely and writes nothing, keeping snapshot freshness and the no-write-on-failure behavior; independent fix verification is not weakened

### Release gate (GATE)

- [ ] **GATE-01**: On the release candidate, the targeted real-chain regressions, full offline suite, and mode/recovery integration checks pass
- [ ] **GATE-02**: Archived replay differs only in the named, expected reopen/retention repairs; any unrelated change in detection, filtering or closure blocks release
- [ ] **GATE-03**: The release record states the unsupported fixtures, residuals and any validation gap explicitly; live checks run only under an approved bounded proposal, otherwise the gap is documented and an owner waiver obtained, and the milestone ships through the existing close workflow without waiting for Lean orchestration

## Future Requirements

Scheduled as later milestones (ROADMAP.md), not this one:

- **Lean orchestration:** bounded cost-visibility feasibility from existing records (999.12); Finalize-first extraction of mechanical steps; at most one evidence-backed extension.
- **Reviewer efficiency (conditional):** one predeclared comparison experiment, only after both releases and an approved proposal.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cost reporting / usage attribution (999.12) | Lean orchestration milestone; must not delay correctness repairs |
| Orchestration extraction / Finalize refactor | Lean orchestration; this milestone repairs Finalize's path only |
| Reviewer routing, model or prompt changes | Reviewer efficiency (conditional) |
| Scoring-formula or severity retunes | Not a decision-reliability problem |
| 999.26 wordier title references | Fails safe (asks); deferred |
| Another open-ended gap-closure campaign | STALE-06 one-cycle stop rule; Phase 57 already ran four rounds |
| Points added to tasks because a new round started | No-growth-per-round rule above; carry non-qualifying items |
| B3 / holdout measurement campaign, paid runs | Needs a separately approved bounded proposal |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|

**Coverage:**
- v2.14 requirements: 18 total
- Mapped to phases: 0 (filled by roadmap)

---
*Requirements defined: 2026-10-28*
*Last updated: 2026-10-28 after initial definition*
