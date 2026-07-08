# Requirements: vibe-check — Milestone v2.9 (Prove it)

**Defined:** 2026-07-01
**Core Value:** Catch real defects in a developer's changes before they ship — with high coverage and low noise — so a reviewer who can't manually audit the code can trust the agent's output as their safety net.

## v1 Requirements

Requirements for milestone v2.9. Each maps to exactly one roadmap phase (35–37).

> **ID note:** LEGIBLE-01/02/03 deliberately REUSE the v2.8 Phase-33 IDs — they were defined
> there, plan-approved (the frozen 33-02 plan targets them), and never shipped. Keeping the IDs
> preserves traceability to that plan. The archived copy lives at
> `.planning/milestones/v2.8-phases/33-codex-legibility.../33-02-PLAN.md` (⚠ needs a rebase over
> the Fable remediation before execution).

### Legibility (finish 33-02)

- [x] **LEGIBLE-01**: Every `/deep-review` run prints exactly one legible line stating what
  Codex did — joined / skipped-with-reason / off-via-config — so the user never silently gets
  native-only; default behavior stays `auto`
- [x] **LEGIBLE-02**: A `--codex off|auto|on` flag and the `[noise] codex` config key control
  Codex invocation, resolved by the precedence chain (flag > config > `auto` default) — the
  shipped-but-inert config knob becomes live
- [x] **LEGIBLE-03**: The fix loop's apply-all option no longer carries the "(Recommended)"
  label in `/review` (and `/deep-review` by delegation)

### Proof (v2.8 evidence debt)

- [x] **PROOF-01**: Every v2.8 knob has a passing planted-fixture smoke proof: a
  `.vibe-check.toml` repo has its knobs honored while a no-config repo behaves as v2.7;
  `--min-confidence` drops sub-N findings before scoring with the count in the honesty summary;
  `idiom` is capped at `idiom_floor`; a reasoned `vibe-ignore` suppresses within ±2 and a bare
  marker self-flags; the Codex line announces (tested against the REAL 33-02 wiring); a
  malformed config degrades per-key with a warning, never fatally
- [x] **PROOF-02**: The Phase-33 surface (33-01 shipped diff + 33-02 new diff) passes a clean
  `/vibe-check:deep-review` gate — no unresolved critical/warning findings

### B3 (first measured quality numbers)

- [x] **B3-01**: A committed ground-truth test set exists: ≥3 should-catch + ≥2 should-quiet
  reviewable diffs, ORGANIC-ONLY sourcing (no vibe-check-found bugs), with a per-diff answer key
  (expected finding + expected band) that folds in the deferred A8 (`/health` name-exemption)
  and A16 (axis-vs-site ambiguity) answer-key fixes
- [x] **B3-02**: The owner runs `/deep-review` on each test diff (N=3 per diff) and every run
  is scored against the answer key
- [x] **B3-03**: A catch-rate / false-positive-rate report lands in
  `plugins/vibe-check/docs/efficacy/` with limitations stated honestly (small N, four repos,
  organic-only) and an explicit statement of what the numbers imply for the B3-gated design
  challenges (proceed / don't / need more data)

### Close

- [x] **CLOSE-01**: `plugins/vibe-check/.claude-plugin/plugin.json` is bumped 2.8.0 → 2.9.0,
  an annotated tag `v2.9` is created, and the milestone is published (merge/ff `main`, push
  main + tag + branch)

## v2 Requirements

Deferred to future milestones. Tracked but not in the current roadmap.

### Scorer design (gated on B3)

- **DESIGN-01**: Adjudicate the scorer design challenges (H-CORE/H-DUP/H-LANE/B-SEV/B-XCONF/B-PROX/B-REWEIGHT) using B3's measured numbers
- **DESIGN-02**: `CATEGORY_DOMAIN` twin proposals (ts `async-discipline`→correctness, express `input-validation`→security)

### Deterministic security

- **SECRET-01**: Gitleaks deterministic secret-scan pre-pass (999.2)

### Honesty & docs

- **COST-01**: Measured token cost per pass (999.12)
- **DOCS-01**: Documentation pass — threat model, honesty, reconciliation, lifecycle (999.13)
- **SECREV-01**: `security.md` critique pass (needs a dedicated Opus session)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Scorer restructuring / design challenges | Explicitly gated on B3's numbers — acting before measuring inverts this milestone's logic |
| `CATEGORY_DOMAIN` twin changes | Twin-policy calls, not calibration; deferred with the design challenges |
| gitleaks (999.2), SARIF (999.3), PR-posting (999.5) | Feature work deferred until the system's efficacy is measured; CI items are bottom-tier under the build-for-myself lens |
| Measured cost (999.12), docs pass (999.13) | Polish, not capability; docs should describe post-v2.9 behavior |
| Roonseek walkthrough-transcript mining for B3 | Highest-quality but laborious; B3-STATUS defers it — the committed set is sufficient for first numbers |
| Re-deriving `agent_confidence` / scoring formula changes | Standing constraint since v2.8: the formula is untouched; measurement first |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LEGIBLE-01 | Phase 35 | Complete |
| LEGIBLE-02 | Phase 35 | Complete |
| LEGIBLE-03 | Phase 35 | Complete |
| PROOF-01 | Phase 35 | Complete |
| PROOF-02 | Phase 35 | Complete |
| B3-01 | Phase 36 | Complete |
| B3-02 | Phase 36 | Complete |
| B3-03 | Phase 36 | Complete |
| CLOSE-01 | Phase 37 | Complete |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9 ✓
- Unmapped: 0 ✓

Per-phase distribution:
- Phase 35 (Make v2.8 whole): LEGIBLE-01, LEGIBLE-02, LEGIBLE-03, PROOF-01, PROOF-02 (5)
- Phase 36 (B3 — first measured quality numbers): B3-01, B3-02, B3-03 (3)
- Phase 37 (Close): CLOSE-01 (1)

---
*Requirements defined: 2026-07-01*
*Last updated: 2026-07-01 after roadmap creation (100% coverage, phases 35–37)*
