# Phase 22: Efficacy Test + Version Bump + Tag - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

The **standard milestone close** for v2.5 "Sharper, more legible reviews." Two requirements:

- **CLOSE-01 — Efficacy dogfood.** Re-run the `--all` deep review on the vibe-check repo
  itself and confirm, on the real tree with **no regression to existing behavior**, that the
  three v2.5 threads work:
  - **Phase 19** (`--all` source-only selection): vibe-check's own `agents/`/`commands/`/
    `templates/` `.md` ARE reviewed; `.planning/`, `docs/`, generated/vendor dirs are EXCLUDED.
  - **Phase 21** (test-sufficiency agent): the new deep-only agent fires and behaves correctly.
  - **Phase 20** (crash-proof core): `score.py` survives malformed input.
- **CLOSE-02 — Version bump + tag.** Bump `plugins/vibe-check/.claude-plugin/plugin.json`
  from 2.4.0 → **2.5.0** and create an **annotated, un-pushed** `v2.5` git tag (project convention).

Maps to design-spec **Phase 4** (`docs/superpowers/specs/2026-06-26-v2.5-sharper-more-legible-reviews-design.md`
§2 Phase 4, §3 Phase-4 success criteria 1–2).

**NOT in scope:** pushing the tag or merging `feat/v2.5` to main (D-02 — local only); any new
feature work; re-opening Phases 19–21 (all shipped); building a coverage-command runner
(explicitly excluded by Phase 21's D-03).
</domain>

<decisions>
## Implementation Decisions

### Efficacy depth for the test-sufficiency agent (D-01)
- **D-01:** On this coverage-less repo the test-sufficiency agent's reachable behavior is
  **skip-and-note** (no coverage artifacts on disk → empty `<coverage-artifacts>` block →
  `{"agent":"test-sufficiency","findings":[],"agent_notes":["no coverage data available, skipped"]}`).
  **That clean skip IS the accepted efficacy evidence** for Phase 21's agent — it proves the
  degrade-cleanly path, which is the only path reachable here. Do NOT author a synthetic
  coverage fixture to force a finding (considered and declined). Agent-logic correctness rests
  on the unit-tested `score.py` + the Phase-21 deep review already done. This is consistent with
  Phase 21's owner-approved **D-03** (consume-only narrows TESTSUF-02: "no coverage source on
  disk → skip-and-note" is the satisfaction of the criterion), which the design spec's
  criterion 3.2 ("runs the project's coverage command") was narrowed to. So the Phase-4 efficacy
  bar inherits that narrowing: the dogfood proves **skip-and-note**, not command-running.

### Tag + push posture (D-02)
- **D-02:** Create the annotated `v2.5` tag **locally and DO NOT push it**; leave the
  `feat/v2.5` branch local too. This matches the established project convention — v2.1, v2.2,
  v2.3, v2.4 were all tagged un-pushed. Pushing/merging is an owner action taken separately, not
  part of this phase. (Publishing was offered and declined.)

### Efficacy results artifact (D-03)
- **D-03:** Record the dogfood outcome in `plugins/vibe-check/docs/efficacy/RESULTS-v2.5.md`,
  following the existing `RESULTS-v2.{2,3,4}.md` convention (those files already exist in that
  dir). The doc states what the `--all` dogfood confirmed for each of the three v2.5 threads and
  the no-regression conclusion. This is the durable proof artifact for CLOSE-01.

### Install-sync precondition (D-04)
- **D-04:** Before running the efficacy dogfood, the **registered vibe-check install must match
  the post-bump repo plugin.json (2.5.0)**. The registered install is chronically stale (it was
  pinned at 2.4.0 through v2.5 development), and a self-dogfood run against a stale install would
  exercise OLD orchestration, not the v2.5 tree under test. So: bump plugin.json → 2.5.0, sync
  the install cache + registry to 2.5.0, RELAUNCH the process to register, and verify
  `install version == repo plugin.json` before trusting any efficacy result. (See memory
  "install-chronically-stale.")

### Claude's Discretion
- Exact plan decomposition (likely a single plan: efficacy run + RESULTS doc + version bump +
  tag, given how small and mechanical the close is — mirrors prior close phases).
- Whether the dogfood runs as `/deep-review --all` (deep roster, exercises the new
  test-sufficiency agent + Phase 1d wiring) vs `/review --all` — lean `/deep-review --all`
  since that is the only mode that fires test-sufficiency, which CLOSE-01 must confirm.
- How no-regression is evidenced (compare against the v2.4 dogfood baseline in RESULTS-v2.4.md).
</decisions>

<specifics>
## Specific Ideas

- The v2.5 self-dogfood is the FIRST one that can confirm Phase 19's source-only `--all`
  selection on the real tree — the whole point of Phase 19 was to stop the "51-chunk
  planning-doc run." The dogfood should explicitly confirm `.planning/` is excluded and the
  orchestration `.md` under `agents/`/`commands/`/`templates/` is kept.
- v2.4's close (Phase 18) shipped via ONE `/julian-orchestrator:milestone` session and its
  dogfood (CLOSE-01) PASSED with `--all --finalize` clean — that is the precedent shape to follow.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & success criteria (source of record)
- `docs/superpowers/specs/2026-06-26-v2.5-sharper-more-legible-reviews-design.md` §2 (Phase 4),
  §3 (Phase-4 success criteria 1–2), §4 (Phase-4 depends on all three; the docs-filter risk the
  dogfood is the explicit proof for) — authoritative scope/criteria.
- `.planning/ROADMAP.md` → "Phase 22: Efficacy Test + Version Bump + Tag" detail section
  (CLOSE-01, CLOSE-02 and the two success criteria).

### Close-phase precedent (do this the same way)
- `plugins/vibe-check/docs/efficacy/RESULTS-v2.4.md` — the prior milestone's efficacy results
  doc; `RESULTS-v2.5.md` mirrors its shape and serves as the no-regression baseline.
- `plugins/vibe-check/docs/efficacy/RESULTS-v2.3.md`, `RESULTS-v2.2.md` — earlier precedents.

### Version + tag surfaces
- `plugins/vibe-check/.claude-plugin/plugin.json` — the `"version"` field to bump 2.4.0 → 2.5.0.

### What is being proven (the three v2.5 threads)
- Phase 19 selection logic lives in `plugins/vibe-check/commands/review.md` (Phase 0 mode 5
  `--all` selection + the docs/planning exclusion).
- Phase 20 hardening lives in `plugins/vibe-check/scripts/score.py` + `test_score.py` (140 tests).
- Phase 21 agent lives in `plugins/vibe-check/agents/test-sufficiency.md` + the `/deep-review`
  Phase 1d wiring in `plugins/vibe-check/commands/deep-review.md`.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `plugins/vibe-check/docs/efficacy/RESULTS-v2.{2,3,4}.md`: copy the structure for RESULTS-v2.5.md.
- The `/julian-orchestrator:milestone` milestone-end flow (Phase 4 of THIS orchestrator) already
  runs audit + finalize + tag — the close mechanics are precedented, not novel.

### Established Patterns
- Every prior milestone (v2.1–v2.4) ended with: efficacy dogfood → RESULTS doc → plugin.json bump
  → annotated un-pushed tag. Phase 22 repeats that exact sequence for v2.5.
- The install must be synced + the process relaunched before a trustworthy self-dogfood (the
  recurring "install chronically stale" gotcha).

### Integration Points
- `plugin.json` version is read by the plugin loader / registry; bumping it is what the install
  re-sync (D-04) propagates.
- The efficacy dogfood is `/deep-review --all` over vibe-check's own tree — it exercises Phase 19
  selection, Phase 20 score.py, and Phase 21 test-sufficiency in one run.
</code_context>

<deferred>
## Deferred Ideas

- **Synthetic-coverage efficacy fixture** (a fake lcov/coverage.xml to force test-sufficiency to
  emit a real risk-weighted finding) — considered and declined for v2.5 (D-01). Candidate if a
  future milestone wants positive-path proof of the agent on a coverage-bearing repo.
- **Pushing the tag / merging `feat/v2.5` to main** — explicitly out of scope (D-02); an owner
  action taken separately.

### Reviewed Todos (not folded)
None — no pending todos matched this phase.
</deferred>

---

*Phase: 22-efficacy-test-version-bump-tag*
*Context gathered: 2026-06-27*
