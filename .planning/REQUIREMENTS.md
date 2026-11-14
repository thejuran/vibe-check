# Requirements: vibe-check v2.15 Lean orchestration

**Defined:** 2026-11-13
**Core Value:** Catch real defects in a developer's changes before they ship — with high coverage and low noise — so a reviewer who can't manually audit the code can trust the agent's output as their safety net.

**Working rule:** each phase starts by recording the current behaviour or measurement it intends to change, on current code. A path that does not reproduce is recorded and dropped, never replaced with invented work. Every lock lands with a mutant that trips it.

**No growth per round (owner, 2026-10-17, restated 2026-10-28):** a new review, gap or fix round is not a reason to add points to a task, plan, success criterion or acceptance list. A round may add work only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow. Everything else is carried.

**Equivalence baseline:** plugin 2.14.1 (PR #8, squash `dd8e4ab`, tag `v2.14.1`). "Same behaviour" in this file means the same as that release.

**Source context:** ROADMAP.md "Next milestone: Lean orchestration" (owner-approved 2026-10-28; continuous test run and cross-call variable check added 2026-11-13) and backlog records 999.12 and 999.32. Research was skipped by the owner on 2026-11-13.

## v2.15 Requirements

### Cost and quality baseline (BASE) — 999.12

- [x] **BASE-01**: A go/no-go note, built from existing local records only, names which usage fields are trustworthy per run and per lane (model, input/output/cache usage, retries, elapsed time), states what attribution is missing, and names the smallest useful report
- [x] **BASE-02**: Current mode-path bytes and actual loaded-file traces are recorded for plain review, deep review and Finalize, kept separate from any token or price estimate
- [x] **BASE-03**: A pinned behavioural baseline of the 2.14.1 code and its archived replay results are retained before any refactoring starts
- [x] **BASE-04**: The comparison workload and the improvement criterion for this milestone are written down before any extraction work begins; if reliable attribution is unavailable, accounting work stops and labelled footprint/operation counts are used instead

### Continuous test run (CI)

- [x] **CI-01**: One GitHub Actions workflow runs the existing offline suite and the stdlib-only check on every push and every pull request to `main`, with no secrets, no paid runs, no live model calls and no branch-protection change
- [x] **CI-02**: `main` shows a green run on the release baseline, and a deliberately failing commit on a throwaway branch shows red

### Finalize extraction (FINX)

- [ ] **FINX-01**: Finalize's input assembly and gate/report handoff run through stdlib helpers on the existing single-writer state path, and equivalent inputs produce the same gate decisions and reports as the baseline
- [ ] **FINX-02**: Missing, malformed or stale Finalize inputs fail visibly with a plain message, and a failed or refused attempt writes no report and archives nothing
- [ ] **FINX-03**: Finalize restart and retry work across fresh shell calls
- [ ] **FINX-04**: Superseded Finalize prose and locks are removed while behavioural invariants and recovery guidance are kept; judgment, owner decisions and reviewer calls stay in the existing host
- [ ] **FINX-05**: Loaded prose and helper/tool steps on the same Finalize paths are compared before and after; the slice is reverted if it adds complexity without a demonstrated benefit against the BASE-04 criterion

### Cross-call variable check (XVAR)

- [ ] **XVAR-01**: One general check walks every phase file and fails when a fence reads a shell variable set in an earlier fence without the printed-path rule; a mutant proves the check trips
- [ ] **XVAR-02**: Any phase file the check flags is recorded with its reproduction before it is changed

### Optional bounded extension (EXT) — conditional

- [ ] **EXT-01**: After Finalize passes its equivalence checks, a recorded decision either selects at most one further family (repeated evidence/envelope assembly, deterministic dispatch selection, or the 999.32 fix-loop Rerun step) backed by the baseline, or skips the extension; a selected slice preserves roster, prompts/evidence, scores, decision eligibility and recovery behaviour with demonstrated footprint/operation savings. A recorded skip satisfies this requirement

### Release gate (GATE)

- [ ] **GATE-04**: On the exact release candidate, the full offline suite, archived replay and mode/recovery integration checks pass against the 2.14.1 baseline; any unexpected behavioural difference blocks release
- [ ] **GATE-05**: The release record shows safeguards and independent fix verification intact and a demonstrated reduction in loaded prose or mechanical steps, with byte/operation savings reported separately from tokens or dollars and no billing-savings claim without comparable usage evidence
- [ ] **GATE-06**: Live validation of changed orchestration paths runs only under an approved bounded proposal; otherwise the unmeasured behaviour is documented and released under an explicit owner waiver

## Future Requirements

Scheduled later (ROADMAP.md), not this milestone:

- **999.31 Decision identity design:** one design question covering the remaining decision-continuity limits (999.23 residuals, 999.26, 999.29, `--all` decision memory); taken after this milestone ships.
- **Reviewer efficiency (conditional):** one predeclared comparison experiment, only after this release and an approved proposal.
- **Extension families not selected under EXT-01:** deferred, not grown into this milestone.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reviewer routing, narrower reviewer context, new agents | Reviewer efficiency (conditional); uncertain value without a bounded experiment |
| Model downgrades or changed model defaults | Not an orchestration-mechanics change |
| Scoring-formula or severity retunes | Would change review behaviour; this milestone must preserve it |
| New telemetry service, accounting platform or dollar-cap claim | 999.12 is a feasibility check from existing records only |
| Paid baseline runs | Need a separately approved bounded proposal |
| New orchestration framework or wholesale state rewrite | Finalize is the bounded first slice |
| Replacing or vendoring the Codex companion | Owner decision 2026-10-28: keep the optional integration as is |
| Branch-protection changes | CI-01 adds a check only; enforcement is a separate owner decision |
| 999.27, 999.30, broad cleanup | Carried in backlog/maintenance; not reproduced gate failures |
| Points added to tasks because a new round started | No-growth-per-round rule above |

## Traceability

Which phases cover which requirements. Filled in during roadmap creation (2026-11-13). EXT-01 is conditional: a recorded skip satisfies it.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BASE-01 | Phase 62 | Complete |
| BASE-02 | Phase 62 | Complete |
| BASE-03 | Phase 62 | Complete |
| BASE-04 | Phase 62 | Complete |
| CI-01 | Phase 62 | Complete |
| CI-02 | Phase 62 | Complete |
| FINX-01 | Phase 63 | Pending |
| FINX-02 | Phase 63 | Pending |
| FINX-03 | Phase 63 | Pending |
| FINX-04 | Phase 63 | Pending |
| FINX-05 | Phase 63 | Pending |
| XVAR-01 | Phase 63 | Pending |
| XVAR-02 | Phase 63 | Pending |
| EXT-01 | Phase 64 | Pending |
| GATE-04 | Phase 65 | Pending |
| GATE-05 | Phase 65 | Pending |
| GATE-06 | Phase 65 | Pending |

**Coverage:**
- v2.15 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-11-13*
*Last updated: 2026-11-13 after roadmap creation (traceability filled)*
