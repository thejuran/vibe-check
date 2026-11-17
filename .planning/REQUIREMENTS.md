# Requirements: vibe-check

**Defined:** 2026-11-16
**Core Value:** Catch real defects in a developer's changes before they ship — with high coverage and low noise — so a reviewer who can't manually audit the code can trust the agent's output as their safety net.

## v2.16 Requirements — Publication readiness

Requirements for this milestone. Each maps to one roadmap phase. Baseline: plugin 2.15.0 (`d5acc19`). Each phase starts by reproducing its failure on current code; a lead that does not reproduce is recorded with evidence and dropped, never replaced with invented work.

### Close out freshness (FRESH) — 999.40, 999.44

- [ ] **FRESH-01**: When a deferred or dismissed decision refers to code whose exact line or nearby lines changed since the review, Close out refuses and asks the user to run a fresh review; it never starts paid reviewers automatically.
- [ ] **FRESH-02**: When the reviewed code is unchanged, Close out still completes for both decision kinds; fix-verdict freshness, 999.28 score parity and real-edit reopening behave as in 2.15.0.
- [ ] **FRESH-03**: Each of the three bounded legacy wrong-keep shapes in 999.44 (deleted-original relocation with identical text elsewhere, an older covering decision winning over a newer one, untracked files without change ranges) has an evidence-backed outcome: a reproduced wrong keep repaired, the unsupported decision safely refused, or non-reproduction recorded with its counterexample/control. No decision-identity redesign.

### Trusted incremental scope (SCOPE) — 999.27

- [ ] **SCOPE-01**: Repository-controlled state cannot silently choose a narrower review base: a crafted valid commit ID in saved state, including the current HEAD, cannot hide a committed change from an incremental review. An ancestor check alone is insufficient; existing command-injection refusal is preserved.
- [ ] **SCOPE-02**: The user sees the effective review range for an incremental review, and a legitimate incremental resume still reviews only the new changes.

### Phase and scope binding (BIND) — 999.39 SA-01/WR-01, 999.45

- [ ] **BIND-01**: Ambiguous exact or prefix phase matches are rejected, and phase-container names are rejected even when they match only one directory. Ambiguity refusals show the candidates; every refusal happens before review state is accessed.
- [ ] **BIND-02**: Unique phases resolve in both supported layouts, and the overbroad state-isolation claim is corrected.
- [ ] **BIND-03**: Narrowed `--all`, colliding branch names (for example `feat/a` and `feat-a`), and distinct PR/range identities each have an evidence-backed outcome through resume and Close out: existing protection proven, failure repaired, or safe refusal. No general state-format migration.

### Safe helper invocation (HELP) — 999.43, promotes 999.38 R2-WR-01/02

- [ ] **HELP-01**: Ambient `PYTHONPATH`/startup imports (for example a repository `sitecustomize.py`) and empty-path execution (for example a repository `__main__.py`) cannot run repository code across the actual helper and hook invocations, while trusted sibling imports keep working. This does not require sandboxing arbitrary interpreters or the operating system.
- [ ] **HELP-02**: An empty or missing helper path refuses in the same call, and normal helper and hook calls still work.

### Submission packaging (PKG) — 999.41

- [ ] **PKG-01**: The submitted `plugins/vibe-check` folder contains a standalone README of at least 40 prose words with valid links, and meets the portal's documented README/license requirements.
- [ ] **PKG-02**: Documentation covers Python prerequisites, supported-version expectations (including the TOML fallback below 3.11), and optional Codex companion dependencies and setup (Node, authentication, watchdog).
- [ ] **PKG-03**: Labels accurately say "Codex (configured default)" or show the resolved model, and joined/skipped/failed reporting stays accurate.
- [ ] **PKG-04**: Public claims put the stricter v2.11 12/15 catch reading beside 15/15, preserve the MISS verdict and the current-release measurement limitation, and explain what estimated costs include; byte/step reductions are not presented as billing savings.
- [ ] **PKG-05**: The exact candidate's installation and portal checks are recorded as performed or still pending; affected offline compatibility checks pass.

### Release gate (GATE) — continues from v2.15 GATE-06

- [ ] **GATE-07**: Each implemented repair has a reproduction that fails on 2.15.0 and a regression that passes on the candidate; unchanged-code controls pass on both. Investigation-only leads may close with documented non-reproduction and need not fail artificially. The full applicable offline suite and replay against 2.15.0 run on the exact candidate, with intended repair differences explicitly accounted for; any unexplained difference blocks.
- [ ] **GATE-08**: Offline and live evidence are recorded separately. Live checks run only under an owner-approved bounded proposal; unapproved live checks remain pending or explicitly waived, never reported as passed. Pending required checks prevent a publication-readiness claim.
- [ ] **GATE-09**: The candidate ships through the existing close-and-publish workflow (standing directive). Claude developer-portal submission is not authorized by this milestone and requires separate owner authorization.

## Future Requirements

Deferred; tracked in ROADMAP.md backlog, not in this roadmap.

- **999.31** Decision identity design (999.23 residuals, 999.26, 999.29, `--all` decision memory)
- **999.32** Fix loop stops instead of Rerun after a typed defer / empty card
- **999.35** Finalize card temp-file plumbing shared with the fix loop's card
- **999.30** Snapshot store and temp-leftover pruning
- **999.42** Needs debugging outcome
- Reviewer efficiency (conditional milestone; needs an approved bounded comparison proposal)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Decision-identity redesign (999.31) | Separate design question; only reproduced silent keeps are actionable here |
| New reviewer lanes | Not a publication blocker |
| Scorer retuning | No evidence-backed proposal; would invalidate unchanged-code parity |
| Codex replacement or adapter redesign | Only labels/setup docs are in scope |
| Accounting infrastructure | Cost visibility was NO-GO in v2.15 |
| Broad orchestration refactor | Smallest repair wins; a new helper needs demonstrated need |
| New efficacy campaign / B3 or holdout runs | Paid; needs separate approval; not required for readiness |
| Sandboxing arbitrary interpreters, git/node config or the OS | Trusted interpreter and OS permissions remain documented prerequisites |
| General state-format migration | Prefer refusal over renaming state files |
| 999.32, 999.35, 999.30, 999.42 | Can ship later; not publication blockers |
| Paid tests | Need separate bounded approval |
| Claude developer-portal submission | Requires separate owner authorization |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|

**Coverage:**
- v2.16 requirements: 18 total
- Mapped to phases: 0 (pending roadmap)

---
*Requirements defined: 2026-11-16*
*Last updated: 2026-11-16 after owner corrections to BIND, HELP, PKG and GATE*
