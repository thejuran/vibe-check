# Roadmap: vibe-check

## Milestones

- ✅ **v2.1 FastAPI review agent** — Phases 1-3 (shipped 2026-06-18)
- ✅ **v2.2 Codex adversarial reviewer** — Phases 4-6 (shipped 2026-06-21)
- ✅ **v2.3 Whole-codebase review mode (`--all`)** — Phases 7-12 (shipped 2026-06-22)
- ✅ **v2.4 Dogfood-driven hardening** — Phases 13-18 (shipped 2026-06-26)
- ✅ **v2.5 Sharper, more legible reviews** — Phases 19-22 (shipped 2026-06-28)
- ✅ **v2.6 framework-skill review agent** — Phase 23 (shipped 2026-06-28)
- ✅ **v2.7 Framework coverage** — Phases 24-29 (shipped 2026-06-30)
- ✅ **v2.8 Tunable, quieter reviews** — Phases 30-34 (shipped 2026-07-01 — early manual close by owner directive; 33-02 wiring + Phase-34 smoke proofs deferred into v2.9)
- ✅ **v2.9 Prove it** — Phases 35-37 (shipped 2026-07-08 — codex knob live end-to-end + vibe-check's first measured numbers: catch 8/9 · FP 6/9)
- 🚧 **v2.10 Opus 5 rebuild + quiet down** — Phases 38-44 (in progress)

## Phases

<details>
<summary>✅ v2.1 FastAPI review agent (Phases 1-3) — SHIPPED 2026-06-18</summary>

- [x] Phase 1: Agent Authoring (1/1 plan) — completed 2026-06-18
- [x] Phase 2: Dispatch Wiring & Documentation (1/1 plan) — completed 2026-06-18
- [x] Phase 3: Efficacy Test & Milestone Close (1/1 plan) — completed 2026-06-18

Full details: `.planning/milestones/v2.1-ROADMAP.md`

</details>

<details>
<summary>✅ v2.2 Codex adversarial reviewer (Phases 4-6) — SHIPPED 2026-06-21</summary>

- [x] Phase 4: Codex Contract Agent & Translation (1/1 plan) — completed 2026-06-18
- [x] Phase 5: Orchestrator Dispatch & Merge Wiring (2/2 plans) — completed 2026-06-21
- [x] Phase 6: Efficacy Test & Milestone Close (3/3 plans) — completed 2026-06-21

Full details: `.planning/milestones/v2.2-ROADMAP.md`

</details>

<details>
<summary>✅ v2.3 Whole-codebase review mode (`--all`) (Phases 7-12) — SHIPPED 2026-06-22</summary>

- [x] Phase 7: Walking Skeleton — Selection & End-to-End `--all` (3/3 plans) — completed 2026-06-22
- [x] Phase 8: Risk-Rank, Chunk & Per-Chunk Triage (3/3 plans) — completed 2026-06-22
- [x] Phase 9: Estimate-and-Confirm Budget Gate (2/2 plans) — completed 2026-06-22
- [x] Phase 10: Reviewed-Set Filter, Cross-Chunk Merge & Noise Control (2/2 plans) — completed 2026-06-22
- [x] Phase 11: Report-First / Opt-In Fixes (1/1 plan) — completed 2026-06-22
- [x] Phase 12: Dogfood Efficacy Test & Milestone Close (2/2 plans) — completed 2026-06-22

Shipped as plugin v2.3.0 (annotated tag `v2.3`). Dogfood efficacy: all 5 §6 criteria PASS, owner sign-off.
Full details: `.planning/milestones/v2.3-ROADMAP.md`. Dogfood findings deferred to v2.4 backlog:
`.planning/phases/12-dogfood-efficacy-test-milestone-close/12-DOGFOOD-FINDINGS-BACKLOG.md`.

</details>

<details>
<summary>✅ v2.4 Dogfood-driven hardening (Phases 13-18) — SHIPPED 2026-06-26</summary>

- [x] Phase 13: Safer fix-loop default (1/1 plan) — completed 2026-06-23
- [x] Phase 14: Dogfood Critical + Warning fixes (3/3 plans) — completed 2026-06-23
- [x] Phase 15: Dogfood Medium fixes + fix-agent quick win (2/2 plans) — completed 2026-06-24
- [x] Phase 16: Deterministic-core script (2/2 plans) — completed 2026-06-24
- [x] Phase 17: Robustness on the core (3/3 plans) — completed 2026-06-25
- [x] Phase 18: Efficacy test + version bump + tag (1/1 plan) — completed 2026-06-26

Shipped as plugin v2.4.0 (annotated tag `v2.4`, un-pushed). Dogfood efficacy: CLOSE-01 PASS
(old-class DOGFIX/ROBUST defects confirmed absent, `--all --finalize` clean / DOGFIX-06 proven),
owner sign-off approved. Full details: `.planning/milestones/v2.4-ROADMAP.md`. Dogfood findings
(no-CI + 10 Mediums) deferred to a v2.5 hardening candidate:
`plugins/vibe-check/docs/efficacy/RESULTS-v2.4.md`.

</details>

<details>
<summary>✅ v2.5 Sharper, more legible reviews (Phases 19-22) — SHIPPED 2026-06-28</summary>

- [x] Phase 19: `--all` does the right thing (2/2 plans) — completed 2026-06-26
- [x] Phase 20: Crash-proof the core (2/2 plans) — completed 2026-06-26
- [x] Phase 21: Test-sufficiency agent (2/2 plans) — completed 2026-06-27
- [x] Phase 22: Efficacy test + version bump + tag (2/2 plans) — completed 2026-06-28

Shipped as plugin v2.5.0 (annotated tag `v2.5` on `feat/v2.5`, un-pushed). Dogfood efficacy:
CLOSE-01 PASS (all three threads confirmed on the real tree — source-only `--all` selection,
crash-proof `score.py`, test-sufficiency skip-and-note — owner sign-off approved). The dogfood
caught two cross-file-drift defects in vibe-check's OWN contracts; both fixed in-milestone, the
Phase-22 review tightened the React cross-confirm fix, and a regression lock was added.
Full details: `.planning/milestones/v2.5-ROADMAP.md`. 13 requirements, 100% covered.

</details>

<details>
<summary>✅ v2.6 framework-skill review agent (Phase 23) — SHIPPED 2026-06-28</summary>

- [x] **Phase 23: framework-skill Agent — Adopt, Guardrail & Ship** — Validate the dogfooded `framework-skill` commit, add the severity-scoped low-tier noise guardrail (`≤45` cap on `low`-severity taste/differentiator checks only, never a category), gate on a clean deep-review, and ship at 2.6.0 (completed 2026-06-28)

Shipped as plugin v2.6.0 (annotated tag `v2.6` on `a169429`, pushed to `origin/main`).
VERIFY-01 deep-review gate clean; audit 9/9. Clears the framework-skill-reviewer backlog item.
Full details: `.planning/milestones/v2.8-ROADMAP.md` (Phase 23 detail).

</details>

<details>
<summary>✅ v2.7 Framework coverage (Phases 24-29) — SHIPPED 2026-06-30</summary>

- [x] Phase 24: framework-express agent (1/1 plan) — completed 2026-06-28
- [x] Phase 25: framework-vue agent (1/1 plan) — completed 2026-06-29
- [x] Phase 26: framework-angular agent (1/1 plan) — completed 2026-06-30
- [x] Phase 27: framework-electron agent (security-weighted) (1/1 plan) — completed 2026-06-30
- [x] Phase 28: framework-react-native agent (1/1 plan) — completed 2026-06-30
- [x] Phase 29: Efficacy test + version bump + tag (CLOSE) (2/2 plans) — completed 2026-06-30

Shipped as plugin v2.7.0 (annotated tag `v2.7` on bump commit `3501545`, pushed to `origin/main`).
Five framework reviewer agents (express, vue, angular, electron [security-weighted], react-native)
authored + wired across six touchpoints; the fleet grew to 12 language+framework agents; two new
`score.py` twins (`ipc-validation`→security, `list-perf`→impact) with regression locks. Dogfood
efficacy: CLOSE-01 PASS — all five agents proven via seven scoped runs, owner sign-off recorded.
Full details: `.planning/milestones/v2.8-ROADMAP.md` (Phase 24-29 detail).

</details>

<details>
<summary>✅ v2.8 Tunable, quieter reviews (Phases 30-34) — SHIPPED 2026-07-01 (early manual close)</summary>

- [x] **Phase 30: Config surface foundation** — Build the `.vibe-check.toml` reader (resolved once per run), the precedence chain (flag > toml > default), and the per-key fail-safe; prove the surface with the three simplest consumers (`thresholds`, `disabled`, `top_model`) (completed 2026-07-01)
- [x] **Phase 31: Confidence axis** — Surface `agent_confidence` on every rendered finding; add `min_confidence`/`--min-confidence N` that filters BEFORE scoring, with the dropped-count in the honesty summary (completed 2026-07-01; post-ship amendment: Fable A3 narrowed the valid range to 0–49 — ≥ 50 is refused because the pre-scoring filter would silently drop criticals)
- [x] **Phase 32: Idiom floor + `vibe-ignore` marker** — `idiom_floor` band cap (default `medium`) + `// vibe-ignore: <reason>` suppression marker (bare marker → low finding); both script-enforced in `score.py` (completed 2026-07-01)
- [x] **Phase 33: Codex legibility + safer fix-loop default** — **PARTIAL.** 33-01 (config.py `codex` off/auto/on knob + tests) shipped 2026-07-01. 33-02 (the review.md/deep-review.md orchestrator wiring: `--codex` flag parse, always-announce line, fix-loop label, LEGIBLE-01/02/03) was plan-approved but NEVER EXECUTED — the knob validates in config but nothing consumes it yet (inert config key). **33-02 rebases + executes in v2.9 Phase 35.**
- [x] **Phase 34: Efficacy test + version bump + tag (CLOSE)** — **SUPERSEDED by manual close** (owner directive, 2026-07-01): plugin.json bumped 2.8.0 (`6002cae`), merge commit `f19be14` on main, annotated tag `v2.8`, main+tag+branch pushed and hash-verified. The planted-fixture smoke proofs per knob and the per-phase deep-review gates (incl. Phase 33's) were NOT run — **deferred into v2.9 Phase 35.**

Shipped as plugin v2.8.0 (annotated tag `v2.8` on merge commit `f19be14`, main+tag+branch pushed,
hash-verified). What shipped vs. plan: Phases 30–32 in full; 33-01 only; Phase 34's bump/tag/publish
via manual close without its efficacy proofs. PLUS unplanned scope in the same release — the **Fable
second-model review remediation** (buckets 1–3 of `docs/design/FABLE-REVIEW-FINDINGS.md`): scorer bug
fixes, the `min_confidence ≥ 50` refusal (A3), the state-key branch slug (A9), `scripts/guard.py`
extracting the drifted path-containment family (A7/B2, A10/B3), and the gen-2 calibration retrofit
across the 9 gen-1 agents (A1/A14/A15). Suite at ship: 356 tests + 221 subtests green.
Full per-phase detail: `.planning/milestones/v2.8-ROADMAP.md`. Deferred into v2.9: 33-02 wiring
(⚠ needs rebase), the Phase-34 smoke proofs, and the A8/A16 answer-key fixes (folded into B3).

</details>

<details>
<summary>✅ v2.9 Prove it (Phases 35-37) — SHIPPED 2026-07-08</summary>

- [x] **Phase 35: Make v2.8 whole** - 33-02 wiring live (LEGIBLE-01/02/03) + deferred v2.8 smoke proofs PASS (PROOF-01/02) (completed 2026-07-02)
- [x] **Phase 36: B3 — first measured quality numbers** - committed pre-registered organic test set, 18 owner runs, catch-rate 8/9 / FP-rate 6/9 + D-11 verdict (completed 2026-07-05)
- [x] **Phase 37: Close** - 2.9.0 bump, README measured-efficacy pointer, annotated tag `v2.9`, atomic publish hash-verified (completed 2026-07-08)

Shipped as plugin v2.9.0 (annotated tag `v2.9` on `17950c0`, main+tag+branch pushed and
exact-hash verified; docs fix-forward `8c0e8ca` on main). First measured quality numbers:
catch-rate 8/9, false-positive-rate 6/9 (RESULTS-v2.9.md §B3); D-11 verdict: PROCEED on
H-CORE/H-LANE/B-SEV/B-REWEIGHT at next-milestone scoping. Milestone audit passed 9/9.
Full details: `.planning/milestones/v2.9-ROADMAP.md`.

</details>

## v2.10 Opus 5 rebuild + quiet down (Phases 38-44) — IN PROGRESS

- [ ] **Phase 38: Grow the B3 set + Claude-5 baseline** — Grow the committed organic test set 6 → 10–12 diffs (sealed keys, provenance sidecars), pre-register the pass bar + decision rule, and baseline every diff ×3 on the UNCHANGED v2.9.0 plugin running on the current Claude 5 harness (dual duty: the Opus 5 re-measure)
- [ ] **Phase 39: Claude-5 compatibility + measured cost** — README/config docs made current for the Claude 5 generation (opus/fable allowlist kept + documented), and every review pass prints measured token cost instead of the static $0.50/$1.80/$2–5 estimates (999.12)
- [ ] **Phase 40: Prose diet — restructure for Opus 5** — Restructure `commands/review.md` (~80K) + `commands/deep-review.md` (~35K): cut anti-improvisation scar tissue, progressive disclosure, extract the ranked deterministic families to tested scripts, verify the Phase 4.5→5 single-writer property (999.8) — each batch guardrailed by a B3 spot-check against the Phase-38 baseline
- [ ] **Phase 41: Wave 1 — scorer-side noise interventions** — Lift the scoring-formula freeze (Wave-1-scoped): B-SEV severity stability, B-REWEIGHT per-agent confidence calibration, H-LANE pile-on collapse — tuned offline via a zero-catch-regression replay harness on POST-DIET run data, then confirmed by a live spot-check
- [ ] **Phase 42: Wave 2 — agent-side noise interventions** — Prompt-only H-CORE: safe-change recognition + confidence ceilings on the loud lanes (bugs, security, impact, codex contract), with the real B3 false alarms baked in as never-flag classes
- [ ] **Phase 43: Prove — full post-change measurement** — Owner re-runs the full grown set ×3, scored from state against the sealed keys, evaluated honestly against the pre-registered bar in `RESULTS-v2.10.md`, with at most one retune
- [ ] **Phase 44: Close — 2.10.0 release** — plugin.json → 2.10.0, README efficacy AND measured-cost numbers replaced, annotated tag `v2.10`, atomic hash-verified publish

### Phase 38: Grow the B3 set + Claude-5 baseline

**Goal**: The committed ground-truth set is grown to 10–12 organic diffs with sealed answer keys, the v2.10 pass bar is pre-registered before any change, and the whole set has a clean ×3 baseline on the UNCHANGED v2.9.0 plugin running on the current Claude 5 harness — the anchor every later comparison is measured against
**Depends on**: Phase 37 (v2.9 shipped — the existing committed 6-diff B3 kit + its 18 recorded baseline runs)
**Requirements**: SET-01, SET-02, SET-03
**Success Criteria** (what must be TRUE):

  1. The committed set contains 10–12 organic diffs — 4–6 new (≥1–2 should-catch, the rest should-quiet, weighted toward clean-but-security/networking-sensitive changes), each with a patch + provenance sidecar + sealed per-diff answer key, all passing the unchanged v2.9 fail-closed sourcing rules (organic-only, no vibe-check-found bugs, reversed-fix should-catches, line-survival-proven should-quiets)
  2. The v2.10 pass bar and decision rule (FP-rate ≤ half the pre-change baseline AND catch-rate no worse; at most one retune on failed diffs only) are pre-registered in the sealed manifest, provably ordered before any COMPAT/DIET/SCORER/AGENT change lands
  3. Every diff — new AND carried-over — has an owner-driven ×3 pre-change baseline recorded on the unchanged v2.9.0 plugin on the current Claude 5 harness, captured under installed-cache parity pre-flight and the v2.9 state-isolation gates (fresh state, `len(passes)==1`, full-worktree tree-diff equality)
  4. That same baseline is written up as the Opus 5 re-measure: the v2.9-vs-Claude-5 catch/FP comparison on the identical unchanged plugin is stated explicitly, so the model-generation shift is separated from every later intervention

**Plans:** 4/6 plans executed

Plans:
**Wave 1**

- [x] 38-01-PLAN.md — Seal-1: pre-register the v2.10 pass bar + decision rule (PREREGISTRATION-v2.10.md) + seed RUN-METHOD-NOTES-v2.10.md (harness fingerprint machinery)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 38-02-PLAN.md — RUN-CHECKLIST-v2.10.md part A (carried 6, runs-v2.10/ targets, 2.9.0 cache parity) — opens owner WAIT 1 (18-run re-measure)
- [x] 38-03-PLAN.md — Mine the four repos, owner confirms picks (checkpoint; D-04 STOP branch), build 4-6 new kits (patch + provenance)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 38-04-PLAN.md — ANSWER-KEY-v2.10.md + seal-2 (single follow-up manifest commit) + checklist part B — opens owner WAIT 2 (new-diff baselines)

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 38-05-PLAN.md — Owner runs checkpoint (~30-36 runs) + integrity gate ladder + SCORING-v2.10.md (scored from state vs both sealed blobs)

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 38-06-PLAN.md — RESULTS-v2.10.md baseline + explicit Opus 5 re-measure (v2.9 8/9 · 6/9 vs Claude-5 on the carried 6) + phase-exit integrity checks

> **Owner-runtime**: the ×3 baseline runs are `/deep-review` invocations the OWNER drives — the assistant cannot invoke them. The phase delivers the run-checklist with exact commands; runs are resumable across days.

### Phase 39: Claude-5 compatibility + measured cost

**Goal**: A user reading the docs sees what actually runs on the Claude 5 generation, and every review pass reports what it actually cost instead of a stale guess
**Depends on**: Phase 38 (SET-02 pre-registration must be sealed before any change lands)
**Requirements**: COMPAT-01, COMPAT-02
**Success Criteria** (what must be TRUE):

  1. The README model table, tiering rationale, and configuration section describe the Claude 5 generation as it actually runs; the `opus`/`fable` `top_model` allowlist is kept and documented as supported
  2. Every review pass ends by printing measured token usage/cost from the runs it actually performed, and the static `$0.50` / `$1.80` / `$2–5` estimates no longer appear as the user-facing cost story anywhere in docs or command output
  3. The change is output-only — the review pipeline's findings, scoring, and state are unaffected (`score.py` / `config.py` behavior unchanged, suite green)

**Plans**: TBD

### Phase 40: Prose diet — restructure for Opus 5

**Goal**: The two orchestrator files are rebuilt for a model that follows instructions — each rule stated once, scar tissue gone, deterministic logic in tested scripts — with a materially smaller per-invocation context footprint and no loss of catch-rate
**Depends on**: Phase 39 (COMPAT-02's cost-reporting block lands first so the restructure carries it, not the other way round)
**Requirements**: DIET-01, DIET-02, DIET-03, DIET-04
**Success Criteria** (what must be TRUE):

  1. `commands/review.md` (~80K tokens) and `commands/deep-review.md` (~35K) are restructured for the Opus 5 generation — each rule stated once, anti-improvisation scar tissue removed, progressive-disclosure layout — with the before/after measured token count recorded and materially reduced
  2. The ranked deterministic prose families from `docs/design/prose-to-code-inventory.md` are extracted into tested stdlib-Python scripts, and the inventory's deliberate keep-list is honored (the blocks it judged not worth extracting are still prose)
  3. The Phase 4.5→5 state single-writer property is verified on the restructured flow: either the fix-loop desync class is structurally gone, or its recovery is deterministic and tested (absorbs backlog 999.8)
  4. Every restructure batch is validated before the next lands — behavior contract preserved (phase sequence, output paths, fail-closed guards) and catch-rate no worse than the Phase-38 baseline on a B3 spot-check

**Plans**: TBD

> **Owner-runtime**: the per-batch B3 spot-check runs are owner-driven `/deep-review` invocations.

### Phase 41: Wave 1 — scorer-side noise interventions

**Goal**: The scoring formula freeze lifts (Wave-1-scoped): the scorer becomes less noisy on self-declared severity labels and overconfident agents, same-site lane pile-on collapses, and no change costs an owner run until it is proven not to silence a known catch
**Depends on**: Phase 40 (SCORER-01 replays POST-DIET run data — tuning must target the system that ships)
**Requirements**: SCORER-01, SCORER-02, SCORER-03, SCORER-04, SCORER-05
**Success Criteria** (what must be TRUE):

  1. An offline replay harness re-scores archived + Phase-38 baseline + post-diet run data under each candidate scorer change and rejects — before any owner run is spent — any candidate that would silence one of the baseline catches (zero-catch-regression guardrail holds)
  2. B-SEV, B-REWEIGHT, and H-LANE all land in `score.py` with regression-locking tests and a documented, updated golden digest: a borderline finding needs corroborating signal to reach critical/warning, habitual per-agent overconfidence no longer maps 1:1 into banding, and same-site cross-lane / same-model agreement stops counting as independent corroboration
  3. Per-agent confidence calibration is derived from the accumulated ground-truth run data — not hand-picked constants — and the derivation is recorded so it can be re-derived next milestone
  4. A live spot-check (the 2 known-noisy should-quiet diffs ×3) confirms the shipped Wave-1 behavior matches what the replay harness predicted, before Wave 2 begins

**Plans**: TBD

> **Owner-runtime**: the SCORER-05 live spot-check (2 diffs ×3) is owner-driven.

### Phase 42: Wave 2 — agent-side noise interventions

**Goal**: The loud lanes stop firing on safe, control-tightening changes and stop escalating "sensitive area, no demonstrated defect" observations into alarms — prompt-only, building on the scorer changes proven in Phase 41
**Depends on**: Phase 41 (Wave 2 starts only after the Wave-1 live spot-check confirms the replay prediction)
**Requirements**: AGENT-01, AGENT-02
**Success Criteria** (what must be TRUE):

  1. The loud lanes (bugs, security, impact + the codex translation contract) treat a diff that tightens a control — narrows an allowlist, adds validation, adds a clamp — as presumptively safe on that axis unless a concrete bypass is named
  2. The same lanes carry confidence ceilings for "sensitive area, no demonstrated defect" findings, with the actual B3 false alarms baked in as never-flag exemplar classes
  3. The changes are prompt-only — no scoring surface (`score.py` / `test_score.py` / `config.py`) is touched in this phase

**Plans**: TBD

### Phase 43: Prove — full post-change measurement

**Goal**: The full grown set is honestly re-measured against the sealed keys on the fully changed system, and the pre-registered pass bar is evaluated pass-or-miss with its limitations disclosed
**Depends on**: Phase 42 (measures the system after the diet and both intervention waves land)
**Requirements**: PROVE-01, PROVE-02, PROVE-03
**Success Criteria** (what must be TRUE):

  1. The owner re-runs the full grown set ×3 post-change (~30–36 runs); every run is scored from state (not the transcript) against the sealed keys, with complete pre-registered denominators, no holes, under the v2.9 isolation gates
  2. `RESULTS-v2.10.md` evaluates the pre-registered bar honestly (pass or miss) and carries the honest-limitations section, including the tune-vs-measure overlap caveat and the note that baseline and post-change runs are both on the Claude 5 harness so the comparison is clean across the model-generation shift
  3. At most one retune is used — failed diffs only, ×3 — and whether it was used or not is recorded

**Plans**: TBD

> **Owner-runtime**: the ~30–36 post-change runs (plus any retune re-runs) are owner-driven `/deep-review` invocations.

### Phase 44: Close — 2.10.0 release

**Goal**: v2.10 ships as a published plugin release carrying the new measured efficacy AND cost numbers
**Depends on**: Phase 43 (ships the proven numbers)
**Requirements**: CLOSE-01
**Success Criteria** (what must be TRUE):

  1. plugin.json is bumped to 2.10.0 and an annotated tag `v2.10` is created
  2. The README efficacy section AND the measured-cost numbers are replaced with the v2.10 measurements plus their caveats
  3. main + tag + branch are pushed in one atomic, exact-hash-verified publish

**Plans**: TBD

## Progress

**Execution Order:** phases execute in numeric order; v2.9 (35 → 36 → 37) is archived — see `.planning/milestones/v2.9-ROADMAP.md`.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Agent Authoring | v2.1 | 1/1 | Complete | 2026-06-18 |
| 2. Dispatch Wiring & Documentation | v2.1 | 1/1 | Complete | 2026-06-18 |
| 3. Efficacy Test & Milestone Close | v2.1 | 1/1 | Complete | 2026-06-18 |
| 4. Codex Contract Agent & Translation | v2.2 | 1/1 | Complete | 2026-06-18 |
| 5. Orchestrator Dispatch & Merge Wiring | v2.2 | 2/2 | Complete | 2026-06-21 |
| 6. Efficacy Test & Milestone Close | v2.2 | 3/3 | Complete | 2026-06-21 |
| 7. Walking Skeleton — Selection & End-to-End `--all` | v2.3 | 3/3 | Complete | 2026-06-22 |
| 8. Risk-Rank, Chunk & Per-Chunk Triage | v2.3 | 3/3 | Complete | 2026-06-22 |
| 9. Estimate-and-Confirm Budget Gate | v2.3 | 2/2 | Complete | 2026-06-22 |
| 10. Reviewed-Set Filter, Cross-Chunk Merge & Noise Control | v2.3 | 2/2 | Complete | 2026-06-22 |
| 11. Report-First / Opt-In Fixes | v2.3 | 1/1 | Complete | 2026-06-22 |
| 12. Dogfood Efficacy Test & Milestone Close | v2.3 | 2/2 | Complete | 2026-06-22 |
| 13. Safer Fix-Loop Default | v2.4 | 1/1 | Complete | 2026-06-23 |
| 14. Dogfood Critical + Warning Fixes | v2.4 | 3/3 | Complete | 2026-06-23 |
| 15. Dogfood Medium Fixes + Fix-Agent Quick Win | v2.4 | 2/2 | Complete | 2026-06-24 |
| 16. Deterministic-Core Script | v2.4 | 2/2 | Complete | 2026-06-24 |
| 17. Robustness on the Core | v2.4 | 3/3 | Complete | 2026-06-25 |
| 18. Efficacy Test + Version Bump + Tag | v2.4 | 1/1 | Complete | 2026-06-26 |
| 19. `--all` Does the Right Thing | v2.5 | 2/2 | Complete | 2026-06-26 |
| 20. Crash-Proof the Core | v2.5 | 2/2 | Complete | 2026-06-26 |
| 21. Test-Sufficiency Agent | v2.5 | 2/2 | Complete | 2026-06-27 |
| 22. Efficacy Test + Version Bump + Tag | v2.5 | 2/2 | Complete | 2026-06-28 |
| 23. framework-skill Agent — Adopt, Guardrail & Ship | v2.6 | 1/1 | Complete | 2026-06-28 |
| 24. framework-express agent | v2.7 | 1/1 | Complete | 2026-06-28 |
| 25. framework-vue agent | v2.7 | 1/1 | Complete | 2026-06-29 |
| 26. framework-angular agent | v2.7 | 1/1 | Complete | 2026-06-30 |
| 27. framework-electron agent (security-weighted) | v2.7 | 1/1 | Complete | 2026-06-30 |
| 28. framework-react-native agent | v2.7 | 1/1 | Complete | 2026-06-30 |
| 29. Efficacy Test + Version Bump + Tag | v2.7 | 2/2 | Complete | 2026-06-30 |
| 30. Config surface foundation | v2.8 | 3/3 | Complete | 2026-07-01 |
| 31. Confidence axis | v2.8 | 2/2 | Complete | 2026-07-01 |
| 32. Idiom floor + `vibe-ignore` marker | v2.8 | 3/3 | Complete | 2026-07-01 |
| 33. Codex legibility + safer fix-loop default | v2.8 | 1/2 | Partial — 33-01 shipped; 33-02 deferred to v2.9 Phase 35 | 2026-07-01 |
| 34. Efficacy test + version bump + tag (CLOSE) | v2.8 | 0/? | Superseded — manual close (bump+tag+publish done; smoke proofs deferred to v2.9 Phase 35) | 2026-07-01 |
| 35. Make v2.8 whole | v2.9 | 2/2 | Complete   | 2026-07-02 |
| 36. B3 — first measured quality numbers | v2.9 | 3/3 | Complete | 2026-07-05 |
| 37. Close | v2.9 | 1/1 | Complete | 2026-07-08 |
| 38. Grow the B3 set + Claude-5 baseline | v2.10 | 4/6 | In Progress|  |
| 39. Claude-5 compatibility + measured cost | v2.10 | 0/? | Not started | - |
| 40. Prose diet — restructure for Opus 5 | v2.10 | 0/? | Not started | - |
| 41. Wave 1 — scorer-side noise interventions | v2.10 | 0/? | Not started | - |
| 42. Wave 2 — agent-side noise interventions | v2.10 | 0/? | Not started | - |
| 43. Prove — full post-change measurement | v2.10 | 0/? | Not started | - |
| 44. Close — 2.10.0 release | v2.10 | 0/? | Not started | - |

> Full per-phase detail for shipped milestones lives in the archives under
> `.planning/milestones/` (e.g. `v2.4-ROADMAP.md`, `v2.5-ROADMAP.md`, `v2.8-ROADMAP.md`).

## Backlog

> **Pruned 2026-07-08 (post-v2.9 retro):** shipped items removed; full write-ups live in
> git history (pre-prune tip: `745da96`) and the milestone archives. Shipped: **999.0**
> (neutral fix menu — v2.9 LEGIBLE-03 D-07), **999.1** (framework agents — fleet 7→12,
> v2.7), **999.4** (tunable config + confidence axis + noise knobs — v2.8), **999.6**
> (test-sufficiency agent — v2.5), **999.7** (score.py deterministic core — v2.4, crash-
> proof v2.5), **999.9** (ROBUST-01/03/04 — v2.5; cross-confirm regression test v2.7),
> **999.10** (NOISE-01 ceiling v2.6, noise knobs v2.8, Codex legibility v2.9), **999.14**
> (dogfood-found defects — v2.4). Still open below: **999.2**, **999.3**, **999.5**,
> **999.8**, **999.12** (D-01 estimate *brackets* shipped in v2.8; the measured-actuals
> half remains), **999.13** (architecture.md + README efficacy exist; the threat-model /
> honesty / lifecycle pass remains). The 2026-06-22 tier journal below is retained as a
> dated historical record — its item states are superseded by this note.

> **Priority order (re-prioritized 2026-06-22, correctness-first lens).**
> Phase *numbers* are stable identifiers, not sequence. The intended order of
> attack is the tiers below. Rationale: lens = **build-for-myself**
> ([[vibe-check-backlog-reweight]]) with a **correctness-first freeze** — the
> external-review correctness block (999.7 → 999.8 → 999.9) is treated as a
> single must-do unit at the top, and feature work waits behind it. CI-facing
> items (999.3 SARIF, 999.5 PR-posting) sink to the bottom because the tool is
> local-first and solo-used.
>
> | Tier | Phases (in order) | Why |
> |------|-------------------|-----|
> | **0 — Ship now (quick win)** | **999.0** | ~5-min safety edit, no dependencies. Strip apply-all "(Recommended)". |
> | **0.5 — Dogfood bug fixes** | **999.14** (incl. 3 Critical) | Concrete defects the `--all` dogfood found in vibe-check's OWN prose — one is user-facing (a copy-paste-broken resume command it prints). Real bugs outrank all feature work; some empirically prove the 999.7/999.8 thesis. |
> | **1 — Correctness freeze** | **999.7 → 999.8 → 999.9** | The keystone. 999.7 (deterministic-core script) unblocks the other two and makes scoring un-skippable. The dogfood (999.14) found the exact prose-can't-enforce failures these fix — strong empirical backing. Freeze feature work until this tier is solid. |
> | **2 — Self-value features** | **999.6** (test-sufficiency) → **999.1** (framework agents) → **999.10** (noise/Codex legibility) → **999.2** (gitleaks) | Highest "makes MY reviews better" payoff. 999.6 + 999.1 cover the author's own repos; 999.10 cuts noise; 999.2 closes the conceded LLM-security gap. |
> | **3 — Ergonomics & honesty** | **999.4** (tunable config) → **999.12** (measured cost) → **999.13** (docs pass) | Reduce fork pressure, replace cost guesses with measurement, then document — 999.13 last so it describes post-999.10/999.12 behavior. |
> | **4 — CI reach (deferred)** | **999.3** (SARIF) → **999.5** (PR-posting) | Low personal value, local-first tension; 999.5 is highest-risk (SaaS pull) and depends on 999.3. Only if/when sharing demands it. |
>
> Quick wins that can jump their tier when convenient: **999.0** (already Tier 0)
> and the **suppression-marker** sub-feature of 999.10 (cheapest item in it).

> **Milestone-sizing note (2026-06-22) — planning only, not a commitment.**
> Each backlog item is sized like **one phase**, not a milestone. This project's
> shipped milestones run **3–6 phases**, where the last phase is always
> "efficacy test + version bump + tag" — so the real feature budget is **2–5
> phases of actual work per milestone**, grouped around one nameable capability
> (v2.1 = FastAPI agent, v2.2 = Codex reviewer, v2.3 = `--all` mode). So **~3–5
> backlog items fit one milestone, IF they share a theme.** The four priority
> tiers above already cluster that way — they were cut on the same theme axis
> milestones are. A *possible* future grouping (do NOT treat as locked; the next
> milestone gets cut with `/gsd:new-milestone` — v2.3 has now shipped):
>
> | Candidate | Items | Work phases (+close) | Theme |
> |-----------|-------|----------------------|-------|
> | **v2.4 (next)** | 999.0, **999.14**, 999.7, 999.8, 999.9 | 5 (+1) | **Dogfood-driven hardening** — fix what the tool found in itself + the deterministic-core/state-safety work it proves is needed |
> | v2.5 | 999.6, 999.1, 999.10 | 3 (+1) | Sharper, less-noisy reviews |
> | v2.6 | 999.4, 999.12, 999.13 (± 999.2) | 3–4 (+1) | Configurable & honest |
> | v2.7 | 999.3, 999.5 | 2 (+1) | CI reach (deferred) |
>
> **v2.4 updated (2026-06-22) after the Phase-12 `--all` dogfood:** the dogfood
> found ~13 real defects in vibe-check's own orchestration prose (3 Critical) —
> captured as **999.14**. They share a theme with the correctness-core work
> (999.7/999.8/999.9 = the prose-can't-enforce class) and *empirically validated*
> that thesis, so they belong in the same milestone. v2.4 is now "fix what the
> dogfood found, and build the structure that prevents the class." 5 work phases —
> top of the project's 3–6 range, sizeable but fits; if it feels heavy, split
> 999.14 (pure bug fixes) into its own fast v2.4 and push the core-refactor to
> v2.5. Bug source:
> `.planning/phases/12-dogfood-efficacy-test-milestone-close/12-DOGFOOD-FINDINGS-BACKLOG.md`.
>
> Open calls left for `/gsd:new-milestone` time: **999.2 (gitleaks)** is the
> swing item — fits "sharper reviews" or "configurable & honest" equally.
> **999.7** alone could justify a tiny standalone milestone if you want the
> deterministic-core refactor to ship and prove itself before 999.8/999.9 build
> on it. Don't make any other single item its own milestone.

### Phase 999.2: Gitleaks deterministic secret-scan pre-pass (BACKLOG)

**Goal:** Run gitleaks before the AI agent fan-out and feed CONFIRMED secret hits to the security agent for severity/explanation, instead of having the LLM detect secrets from scratch. Closes the pure-LLM security gap the README concedes; deterministic ground truth with zero hallucination.

**Requirements:** TBD

**Plans:** 0 plans

**Design decisions (from competitive analysis, D1 + D4):**

- **Scope follows the mode's resolved file set** — diff set in diff mode, PR files in PR mode, whole tree in `--all`. Do NOT hardcode "the diff." This single scope-aware integration also absorbs the history scan below.
- **Diff/staged hits are blocking** Critical findings (slot into the existing pipeline where the diff anchor lives).
- **Full-history hits are a non-blocking advisory** rendered in the transparency/filtered section ("predate your diff; rotate + scrub separately") — never block a future commit over a leak unfixable in this diff.
- **Degrade cleanly** (skip-and-note) if the gitleaks binary is absent, matching the proven Codex-integration posture.
- MIT, zero-config, ms-fast. Recommended **roadmap step 1** — best trust-per-effort.

**Source:** `docs/superpowers/specs/2026-06-22-competitive-analysis-and-feature-gaps.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.3: SARIF findings output for CI code-scanning (BACKLOG)

**Goal:** Emit findings as SARIF 2.1.0 so vibe-check drops into GitHub code-scanning / CI gates alongside deterministic tools (Semgrep, Snyk, Gitleaks). One normalized schema; pure output serializer with no change to review logic.

**Requirements:** TBD

**Plans:** 0 plans

**Design decisions (from competitive analysis):**

- Recommended **roadmap step 2** — low risk (output-only), and a **prerequisite for the CI/PR-posting mode** (999.5).
- Sequenced before the confidence axis because it is purely additive and unlocks CI adoption without touching the review itself.
- Also the bridge to a future GitHub check-run-with-annotations posting shape (see 999.5, D3).

**Source:** `docs/superpowers/specs/2026-06-22-competitive-analysis-and-feature-gaps.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.5: CI / PR-comment posting mode (BACKLOG)

**Goal:** An additive opt-in mode (`/vibe-check:review --pr <n>`) that posts threshold-filtered, already-scored findings to a GitHub PR. The biggest reach expansion — meets teams where their PRs live.

**Requirements:** TBD

**Plans:** 0 plans

**Design decisions (from competitive analysis, D3 + the "additive, not a pivot" guardrail):**

- **Local inner-loop stays the default.** PR-posting is explicit opt-in, never the primary path. Reuses the existing scored-findings pipeline (same agents, scoring, threshold filtering) — adds a *sink*, not a new review engine. Shells out to `gh` at the user's invocation; **no server, webhook app, or persisted state** (preserves the no-SaaS-dependency moat).
- **Posting shape order: summary comment → inline → check-run.**
  1. **Single summary comment first** — one `gh pr comment` reusing Phase 4 render output near-verbatim. No line-anchoring, no Checks API.
  2. **Inline comments second** — needs exact `(path, line, commit-SHA)` anchoring (where line-drift bugs live).
  3. **Check-run with annotations last (if ever)** — needs the Checks API + GitHub App token; most server-shaped, most in tension with local-first. SARIF output (999.3) is the bridge.
- Recommended **roadmap step 4**; **highest risk** of the recommended set (pulls toward SaaS territory) — guardrail above is load-bearing. **Depends on SARIF output (999.3).**

**Source:** `docs/superpowers/specs/2026-06-22-competitive-analysis-and-feature-gaps.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

---

> **Phases 999.8 / 999.12 / 999.13 below** (the rest of that set — 999.7, 999.9, 999.10 — has shipped; see prune note above) — they come from an independent external engineering
> review (2026-06-22). The reviewer's overall read: "the engineering quality is
> real, so most of this is sharpening rather than rescue." Three items were
> flagged as highest-leverage and are marked **[TOP-3]**. Full review and the
> cluster→phase mapping live in
> `docs/superpowers/specs/2026-06-22-external-review-triage.md`.

### Phase 999.8: State single-writer for the fix loop **[TOP-3 #2]** (BACKLOG)

**Goal:** Fix the Phase 4.5 → 5 state double-write. State is written in 4.5, then
re-read-modify-written in 5 to append fix SHAs; the spec admits an interruption
between git-commit and state-write desyncs git from state. Make it single-writer,
or at minimum make recovery deterministic instead of best-effort prose.

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:**

- **Largely dissolved by 999.7** — the script refactor collapses to a single
  writer for free. If 999.7 ships first, this phase may shrink to a verification
  that the desync is gone. Re-scope at promotion time.

- The fix-loop *default* safety change that used to live here is now its own
  front-of-queue quick win, **999.0**.

**Source:** `docs/superpowers/specs/2026-06-22-external-review-triage.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.12: Measured cost reporting per pass (BACKLOG)

**Goal:** Print measured token cost at the end of a review pass instead of only
citing static estimates ($0.50 / $1.80 / $2–4). Closes the estimate-vs-reality
gap — and the reality is that the estimates currently disagree across docs (see
the cost-reconciliation item in 999.13).

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:** Small, output-only — render actual usage from the agent runs
the pass already performed. Complements 999.13's "pick one source of truth" by
replacing the guess with a measurement.

**Source:** `docs/superpowers/specs/2026-06-22-external-review-triage.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.13: Documentation pass — threat model, honesty, reconciliation, lifecycle (BACKLOG)

**Goal:** A bundled documentation phase addressing the reviewer's full doc
cluster. Mostly README + spec edits; no pipeline risk.

**Requirements:** TBD

**Plans:** 0 plans

**Checklist (each a small edit):**

- **Surface the threat model in the README** — the untrusted-diff /
  prompt-injection hardening (temp-file commit messages, `--` guards, realpath
  containment, the title allowlist blocking `Co-Authored-By:` forging) is a
  genuine differentiator buried in agent files. Lead with it.

- **Disclose Codex's silent-degradation honestly** — "only if installed and
  authenticated; otherwise native-only." (Pairs with the 999.10 opt-in flag.)

- **Reconcile the cost numbers** — `deep-review.md` says ~$2–4; `architecture.md`
  says ~$1.80. One source of truth. (999.12 makes it measured.)

- **Reframe the efficacy docs as smoke tests** — N=3 on planted fixtures with a
  self-authored sign-off isn't a benchmark; either broaden it (more fixtures,
  real repos, measured false-positive rate, S4-type blind spots as known
  limitations) or rename it. Carry the existing honest tone throughout.

- **Translate /review vs /deep-review into user terms** — what extra findings
  you'll actually see, not phase names.

- **Make the non-GSD experience legible** — document the non-GSD path as
  first-class ("full-featured minus intent-alignment"), not a footnote.

- **Document the `.turingmind/` lifecycle in one place** — what's safe to delete,
  how to resume a paused review, what `--finalize` produces, what's gitignored vs
  committed.

- **Document known orchestration failure modes for users** — what a drifted run
  looks like and how to recover ("if the fix loop didn't appear, re-run with the
  same args; state persists").

**Design notes:** Sequence LAST — several items reference behavior that 999.10
(Codex opt-in) and 999.12 (cost reporting) change, so writing the docs after
those lands avoids documenting soon-to-be-stale behavior.

**Source:** `docs/superpowers/specs/2026-06-22-external-review-triage.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)
