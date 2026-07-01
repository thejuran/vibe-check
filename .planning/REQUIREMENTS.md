# Requirements: vibe-check — Milestone v2.8 (Tunable, quieter reviews)

**Defined:** 2026-06-30
**Core Value:** Catch real defects in a developer's changes before they ship — with high coverage and low noise — so a reviewer who can't manually audit the code can trust the agent's output as their safety net.

## v1 Requirements

Requirements for milestone v2.8. Each maps to exactly one roadmap phase (30–34).

### Config

The repo-level `.vibe-check.toml` surface — the milestone's keystone. Every knob reads from it.

- [x] **CONFIG-01**: vibe-check reads a repo-root `.vibe-check.toml` once per run; a repo *without* one behaves exactly as v2.7 (zero-config back-compat).
- [x] **CONFIG-02**: Config resolution follows precedence CLI flag > `.vibe-check.toml` > built-in default, per knob.
- [x] **CONFIG-03**: A missing, unparseable, or partially-invalid config degrades **per-key** to defaults with a warning and never aborts a review (fail-safe).
- [x] **CONFIG-04**: The config can set band `thresholds`, the `disabled` agent roster, and `top_model` — honored at scoring and dispatch respectively (the first consumers that prove the surface).

### Confidence

Surface the confidence axis and add the filter-before-scoring knob. The scoring formula is untouched.

- [ ] **CONF-01**: Every rendered finding shows its `agent_confidence` as a visible field.
- [ ] **CONF-02**: `--min-confidence N` (flag) and `min_confidence` (config) drop findings below N **before** scoring — the formula is untouched.
- [ ] **CONF-03**: The count of confidence-filtered findings appears in the honesty/filtered summary (nothing silently vanishes).

### Noise

The two script-enforced noise knobs (idiom floor + suppression marker), both in `score.py`.

- [x] **NOISE-01**: The `idiom` category is capped at a tunable max band (default `medium`); idioms never block finalize.
- [x] **NOISE-02**: A `// vibe-ignore: <reason>` marker within ±2 lines of a finding suppresses it (rides the existing silenced-marker grep).
- [x] **NOISE-03**: A bare `// vibe-ignore` with no reason is itself flagged as a low finding ("suppression without reason").

### Legibility

The two orchestrator-enforced knobs (Codex legibility + safer fix-loop default), prose-only.

- [ ] **LEGIBLE-01**: Every run prints one legible line stating what Codex did (joined / skipped-with-reason / off-via-config); default behavior stays `auto`.
- [ ] **LEGIBLE-02**: `--codex` flag and `[noise] codex` (`off`/`auto`/`on`) control Codex invocation.
- [ ] **LEGIBLE-03**: The fix loop no longer labels the apply-all option "(Recommended)".

### Close

- [ ] **CLOSE-01**: A planted-fixture smoke proof per knob (config read, min-confidence filter, idiom floor, vibe-ignore, Codex announce, safe fix-loop default) passes; `plugins/vibe-check/.claude-plugin/plugin.json` is bumped 2.7.0 → 2.8.0; an annotated tag `v2.8` is created and the milestone is published.

## v2 Requirements

Deferred to future milestones. Tracked, not in this roadmap.

### Deterministic security
- **SECRET-01** (999.2): Gitleaks deterministic secret-scan pre-pass feeding confirmed hits to the security agent.

### CI reach
- **SARIF-01** (999.3): Emit findings as SARIF 2.1.0 for CI code-scanning.
- **PRPOST-01** (999.5): Opt-in PR-comment posting mode.

### Honesty & docs
- **COST-01** (999.12): Replace cost guesses with measurement.
- **DOCS-01** (999.13): Documentation pass.

## Out of Scope

Explicitly excluded from v2.8. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Rewriting the scoring formula / `agent_confidence` derivation | The formula is carefully calibrated; re-deriving re-opens painful severity-weight tuning. `min_confidence` *filters*, `thresholds` *parameterize* existing cutoffs, `idiom_floor` *caps* an existing category — none re-weight. |
| Gitleaks secret-scan (999.2) | Different theme (deterministic tooling, not noise/config) — deserves its own milestone. |
| SARIF / PR-posting (999.3 / 999.5) | CI reach; local-first tension; low personal value under the build-for-myself lens. |
| Making Codex default-off | Decided to keep `auto` default + always-announce (lowest disruption); flipping the default is a separate call if ever wanted. |
| Confidence filter at render-time (keep-the-count-but-hide) | Chose filter-*before*-scoring per the backlog design; render-time filtering was the rejected alternative. |

## Traceability

Which phases cover which requirements. Confirmed/owned by the roadmapper.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONFIG-01 | Phase 30 | Complete |
| CONFIG-02 | Phase 30 | Complete |
| CONFIG-03 | Phase 30 | Complete |
| CONFIG-04 | Phase 30 | Complete |
| CONF-01 | Phase 31 | Pending |
| CONF-02 | Phase 31 | Pending |
| CONF-03 | Phase 31 | Pending |
| NOISE-01 | Phase 32 | Complete |
| NOISE-02 | Phase 32 | Complete |
| NOISE-03 | Phase 32 | Complete |
| LEGIBLE-01 | Phase 33 | Pending |
| LEGIBLE-02 | Phase 33 | Pending |
| LEGIBLE-03 | Phase 33 | Pending |
| CLOSE-01 | Phase 34 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-30*
*Last updated: 2026-06-30 after v2.8 milestone definition*
