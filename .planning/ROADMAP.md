# Roadmap: vibe-check

## Milestones

- ✅ **v2.1 FastAPI review agent** — Phases 1-3 (shipped 2026-06-18)
- ✅ **v2.2 Codex adversarial reviewer** — Phases 4-6 (shipped 2026-06-21)
- ✅ **v2.3 Whole-codebase review mode (`--all`)** — Phases 7-12 (shipped 2026-06-22)
- ✅ **v2.4 Dogfood-driven hardening** — Phases 13-18 (shipped 2026-06-26)
- ✅ **v2.5 Sharper, more legible reviews** — Phases 19-22 (shipped 2026-06-28)
- ✅ **v2.6 framework-skill review agent** — Phase 23 (shipped 2026-06-28)
- ✅ **v2.7 Framework coverage** — Phases 24-29 (shipped 2026-06-30)
- ✅ **v2.8 Tunable, quieter reviews** — Phases 30-34 (shipped 2026-07-01 — early manual close by owner directive; 33-02 wiring + Phase-34 smoke proofs deferred)

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

### ✅ v2.6 framework-skill review agent (Phase 23) — SHIPPED 2026-06-28

- [x] **Phase 23: framework-skill Agent — Adopt, Guardrail & Ship** — Validate the dogfooded `framework-skill` commit, add the severity-scoped low-tier noise guardrail (`≤45` cap on `low`-severity taste/differentiator checks only, never a category), gate on a clean deep-review, and ship at 2.6.0 (completed 2026-06-28)

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
The Phase-29 deep review caught + fixed 2 Warning self-contradictions in the efficacy doc.
Full details: `.planning/milestones/v2.7-ROADMAP.md`. 9 requirements, 100% covered.

</details>

### ✅ v2.8 Tunable, quieter reviews (Phases 30-34) — SHIPPED 2026-07-01 (early manual close)

- [x] **Phase 30: Config surface foundation** — Build the `.vibe-check.toml` reader (resolved once per run), the precedence chain (flag > toml > default), and the per-key fail-safe; prove the surface with the three simplest consumers (`thresholds`, `disabled`, `top_model`) (completed 2026-07-01)
- [x] **Phase 31: Confidence axis** — Surface `agent_confidence` on every rendered finding; add `min_confidence`/`--min-confidence N` that filters BEFORE scoring, with the dropped-count in the honesty summary (completed 2026-07-01; post-ship amendment: Fable A3 narrowed the valid range to 0–49 — ≥ 50 is refused because the pre-scoring filter would silently drop criticals)
- [x] **Phase 32: Idiom floor + `vibe-ignore` marker** — `idiom_floor` band cap (default `medium`) + `// vibe-ignore: <reason>` suppression marker (bare marker → low finding); both script-enforced in `score.py` (completed 2026-07-01)
- [x] **Phase 33: Codex legibility + safer fix-loop default** — **PARTIAL.** 33-01 (config.py `codex` off/auto/on knob + tests) shipped 2026-07-01. 33-02 (the review.md/deep-review.md orchestrator wiring: `--codex` flag parse, always-announce line, fix-loop label, LEGIBLE-01/02/03) was plan-approved but NEVER EXECUTED — the knob validates in config but nothing consumes it yet (inert config key; deep-review keeps its v2.2 Codex flow). 33-02 is deferred (see STATE.md Deferred Items).
- [x] **Phase 34: Efficacy test + version bump + tag (CLOSE)** — **SUPERSEDED by manual close** (owner directive "merge everything and push as 2.8", 2026-07-01): plugin.json bumped 2.8.0 (`6002cae`), merge commit `f19be14` on main (real merge, NOT fast-forward — main carried 14 Fable-findings-doc commits), annotated tag `v2.8`, main+tag+branch pushed and hash-verified. The planted-fixture smoke proofs per knob and the per-phase deep-review gates (incl. Phase 33's) were NOT run — deferred.

**What v2.8 actually shipped (vs. plan):** Phases 30–32 in full; 33-01 only; Phase 34's
bump/tag/publish via manual close without its efficacy proofs. PLUS unplanned scope shipped
inside the same release: the **Fable second-model review remediation** (buckets 1–3 of
`docs/design/FABLE-REVIEW-FINDINGS.md`) — scorer bug fixes (absorb-visibility, deterministic
tie-break, status-forgery scrub, crash guards, strict-JSON output, silenced-marker spellings,
drop-reason labels), the `min_confidence ≥ 50` refusal (A3), the state-key branch slug (A9),
`scripts/guard.py` extracting the drifted path-containment family (A7/B2, A10/B3), and the
gen-2 calibration retrofit across the 9 gen-1 agents (A1/A14/A15). Suite at ship: 356 tests +
221 subtests green. Deferred out of the Fable set: answer-key fixes (A8/A16), the security.md
critique pass, B3 harness execution, all design challenges, any `CATEGORY_DOMAIN` twin changes.

## Progress

**Execution Order:**
Phases execute in numeric order. v2.3 continues from v2.2: 7 → 8 → 9 → 10 → 11 → 12.
v2.6 continues from v2.5: 22 → 23.
v2.7 continues from v2.6: 23 → 24 → 25 → 26 → 27 → 28 → 29 (sequential — Phases 24-28 share wiring files).
v2.8 continues from v2.7: 29 → 30 → 31 → 32 → 33 → 34 (SEQUENTIAL). 30 is the foundation every
later knob reads. 31-33 each take a clean slice that deep-reviews independently; 32 and 33 are
split by ENFORCEMENT BOUNDARY (score.py-enforced vs orchestrator-enforced) so each phase's review
is coherent and its blast radius tight. The shared files (`commands/review.md`,
`commands/deep-review.md`, `scripts/score.py`, `scripts/test_score.py`) are touched by multiple
phases, so phases execute sequentially — the same serialization discipline v2.7 used for shared
wiring files. 34 (close) depends on all four work phases; it exercises every knob.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Agent Authoring | v2.1 | 1/1 | Complete | 2026-06-18 |
| 2. Dispatch Wiring & Documentation | v2.1 | 1/1 | Complete | 2026-06-18 |
| 3. Efficacy Test & Milestone Close | v2.1 | 1/1 | Complete | 2026-06-18 |
| 4. Codex Contract Agent & Translation | v2.2 | 1/1 | Complete | 2026-06-18 |
| 5. Orchestrator Dispatch & Merge Wiring | v2.2 | 2/2 | Complete | 2026-06-21 |
| 6. Efficacy Test & Milestone Close | v2.2 | 3/3 | Complete | 2026-06-21 |
| 7. Walking Skeleton — Selection & End-to-End `--all` | v2.3 | 3/3 | Complete   | 2026-06-22 |
| 8. Risk-Rank, Chunk & Per-Chunk Triage | v2.3 | 3/3 | Complete   | 2026-06-22 |
| 9. Estimate-and-Confirm Budget Gate | v2.3 | 2/2 | Complete   | 2026-06-22 |
| 10. Reviewed-Set Filter, Cross-Chunk Merge & Noise Control | v2.3 | 2/2 | Complete   | 2026-06-22 |
| 11. Report-First / Opt-In Fixes | v2.3 | 1/1 | Complete   | 2026-06-22 |
| 12. Dogfood Efficacy Test & Milestone Close | v2.3 | 0/? | Not started | - |
| 13. Safer Fix-Loop Default | v2.4 | 1/1 | Complete   | 2026-06-23 |
| 14. Dogfood Critical + Warning Fixes | v2.4 | 3/3 | Complete   | 2026-06-23 |
| 15. Dogfood Medium Fixes + Fix-Agent Quick Win | v2.4 | 2/2 | Complete   | 2026-06-24 |
| 16. Deterministic-Core Script | v2.4 | 2/2 | Complete   | 2026-06-24 |
| 17. Robustness on the Core | v2.4 | 3/3 | Complete   | 2026-06-25 |
| 18. Efficacy Test + Version Bump + Tag | v2.4 | 1/1 | Complete   | 2026-06-26 |
| 19. `--all` Does the Right Thing | v2.5 | 2/2 | Complete   | 2026-06-26 |
| 20. Crash-Proof the Core | v2.5 | 2/2 | Complete   | 2026-06-26 |
| 21. Test-Sufficiency Agent | v2.5 | 2/2 | Complete   | 2026-06-27 |
| 22. Efficacy Test + Version Bump + Tag | v2.5 | 2/2 | Complete   | 2026-06-28 |
| 23. framework-skill Agent — Adopt, Guardrail & Ship | v2.6 | 1/1 | Complete   | 2026-06-28 |
| 24. framework-express agent | v2.7 | 1/1 | Complete    | 2026-06-28 |
| 25. framework-vue agent | v2.7 | 1/1 | Complete   | 2026-06-29 |
| 26. framework-angular agent | v2.7 | 1/1 | Complete   | 2026-06-30 |
| 27. framework-electron agent (security-weighted) | v2.7 | 1/1 | Complete   | 2026-06-30 |
| 28. framework-react-native agent | v2.7 | 1/1 | Complete   | 2026-06-30 |
| 29. Efficacy Test + Version Bump + Tag | v2.7 | 2/2 | Complete   | 2026-06-30 |
| 30. Config surface foundation | v2.8 | 3/3 | Complete   | 2026-07-01 |
| 31. Confidence axis | v2.8 | 2/2 | Complete   | 2026-07-01 |
| 32. Idiom floor + `vibe-ignore` marker | v2.8 | 3/3 | Complete   | 2026-07-01 |
| 33. Codex legibility + safer fix-loop default | v2.8 | 1/2 | Partial — shipped 33-01 only; 33-02 deferred | 2026-07-01 |
| 34. Efficacy test + version bump + tag (CLOSE) | v2.8 | 0/? | Superseded — manual close (bump+tag+publish done; smoke proofs deferred) | 2026-07-01 |

> Full per-phase detail for shipped v2.4 (Phases 13-18) lives in the archive:
> `.planning/milestones/v2.4-ROADMAP.md`.

> Full per-phase detail for shipped v2.5 (Phases 19-22) lives in the archive:
> `.planning/milestones/v2.5-ROADMAP.md`.

## Phase Details (v2.6 framework-skill review agent)

> Detail section for the in-progress v2.6 phase. This is a VALIDATE-AND-ADOPT
> milestone: a complete, dogfooded implementation already exists as commit
> `95c6834` on the working branch `feat/framework-skill-reviewer`. Phase 23's
> job is to verify that commit against the approved design, apply the one new
> noise-guardrail edit, gate on a clean deep-review, and ship at 2.6.0 — NOT to
> author the agent from scratch.

### Phase 23: framework-skill Agent — Adopt, Guardrail & Ship

**Goal**: vibe-check gains a `framework-skill` reviewer that catches skill-authoring-quality problems and half-wired plugin additions — by adopting the existing dogfooded commit (`95c6834`), verifying it against the approved design, adding a severity-scoped low-tier noise guardrail (the `≤45` cap rides the `low` severity tier — taste/differentiator checks — NOT a category), gating on a clean deep-review, and shipping at plugin v2.6.0.
**Depends on**: Phase 22 (v2.5 ships first; the agent builds on the crash-proofed `score.py` core and the established framework-agent wiring convention)
**Requirements**: SKILL-01, SKILL-02, SKILL-03, SKILL-04, WIRE-01, WIRE-02, NOISE-01, VERIFY-01, CLOSE-01
**Success Criteria** (what must be TRUE):

  1. **Triggers correctly.** On a diff that touches a `SKILL.md`, an agent prompt (`agents/*.md` with `name:`+`description:` frontmatter), or a plugin manifest, the `framework-skill` reviewer dispatches in both `/review` and `/deep-review`; on a diff with no such file it stays silent — proving the `triage.md` file-shape detection of `"skill"` and the `index.md`/`review.md`/`deep-review.md` dispatch rows (SKILL-01, WIRE-01).
  2. **Reviews the two surfaces.** The adopted agent reviews skill-authoring quality (discoverability / progressive disclosure / structure / content / bundled-script hygiene) AND flags the half-wired-addition class (missing index/dispatch/triage row, `name:` mismatch, missing `model:`, output-contract drift, stale agent-count prose), emitting one schema-valid JSON object (categories from `description`|`disclosure`|`structure`|`content`|`scripts`|`wiring`, detection-only) — verified against the approved design, not rebuilt (SKILL-02, SKILL-03, SKILL-04).
  3. **Wiring is internally consistent.** After the fleet grows by one, the agent-count prose in `commands/review.md` is coherent (floor/max 6→7; agents/chunk, estimated-dispatch figures, and the illustrative cost bracket all updated to match) — the agent's own wiring check finds no half-wired residue on this very change (WIRE-02).
  4. **Low-tier taste findings carry the ceiling; medium/high and objective ones don't.** The new noise guardrail caps `agent_confidence ≤ 45` ONLY on the `low`-severity taste/differentiator checks (the prose nitpicks in `content` + the soft `structure` nitpicks) so borderline prose-style findings filter out by default — the cap rides the `low` severity tier, NOT the category. Medium/high findings stay uncapped in EVERY category, including genuine `content` safety checks (a destructive/fragile workflow, a critical op missing a validation loop), as do `wiring`, `description`/discoverability, `scripts`, and the hard `disclosure` limits — reusing the differentiator-tier pattern from `framework-fastapi.md` (NOISE-01).
  5. **Gated and shipped.** A `/vibe-check:deep-review` pass over the phase's changes is clean (no unresolved critical/warning findings) and `plugin.json` is bumped to `2.6.0` (VERIFY-01, CLOSE-01).

**Plans**: 1 plan (single wave)
Plans:

- [x] 23-01-PLAN.md — Verify the adopted framework-skill agent + wiring, add the NOISE-01 severity-scoped ≤45 confidence ceiling (low-tier taste/differentiator checks only, never category-wide; medium/high stay uncapped), bump plugin.json to 2.6.0

**UI hint**: no

## Phase Details (v2.7 Framework coverage)

> Detail section for the in-progress v2.7 milestone. Each of Phases 24-28 authors
> ONE new framework reviewer agent following the `framework-react.md` pattern
> (~60 lines, `model: sonnet`, layered *in addition to* the matching language
> agent), wires it across the 5 touchpoints, and gates on a clean deep-review.
> **Sequential execution is required:** all five touch the SAME shared wiring
> files (`triage.md`, `commands/review.md`, `commands/deep-review.md`,
> `scripts/score.py`), so concurrent edits would collide on the agent-count prose
> and the dispatch tables — there is no hard *capability* dependency between the
> agents, only this shared-file serialization. WIRE-01 and VERIFY-01 are
> exercised in EVERY agent phase (24-28); WIRE-02 (the agent-count prose fully
> coherent at 12) is closed in Phase 28, the last agent to land. The v2.6
> `framework-skill` reviewer's half-wired-addition check runs on the very files
> each phase adds, so incomplete wiring is caught automatically (this milestone
> exercises its own v2.6 deliverable five times).

### Phase 24: framework-express agent

**Goal**: vibe-check gains a `framework-express` reviewer that catches real Express defects — middleware ordering, unhandled async route errors, the error-middleware arity footgun, missing security headers, route-level input-validation gaps, and request-lifecycle bugs — fully wired across the 5 touchpoints and gated on a clean deep-review. Phase 24 establishes the wiring pattern the next four agents follow.
**Depends on**: Phase 23 (v2.6 ships first; the agent builds on the crash-proofed `score.py` core and the established framework-agent wiring convention). First v2.7 phase — establishes the shared-file wiring pattern.
**Requirements**: EXPRESS-01, WIRE-01, VERIFY-01
**Success Criteria** (what must be TRUE):

  1. **Triggers correctly.** On a diff that imports `express` or uses Express idioms (`app.use`, `req`/`res`/`next` handlers, `Router()`), the `framework-express` reviewer dispatches in both `/review` and `/deep-review`; on a diff with no Express signal it stays silent (EXPRESS-01, WIRE-01).
  2. **Reviews real Express defects.** The agent emits one schema-valid JSON object with categories from `middleware-order` | `async-errors` | `error-handling` | `security-headers` | `input-validation` | `request-lifecycle`, covering the error-middleware 3-vs-4-arg footgun, error-handler-before-routes ordering, unvalidated `req.body`/`req.params`/`req.query` into a SQL/exec/fs/fetch sink, stack-leak-to-client, and double-`res.send`/missing-`return` lifecycle bugs (EXPRESS-01).
  3. **Hedges on invisible context.** Express v4-vs-v5 async behavior (v4 hangs, v5 auto-forwards), "missing global middleware" absence-of-evidence, off-hunk middleware order, and off-hunk route-array validators all reduce confidence with a `pending:` note rather than asserting a confident HIGH (EXPRESS-01).
  4. **`error-handling` naming collision resolved.** Because the literal category `error-handling` already maps to `correctness` (owned by `bugs`) in `score.py`'s `CATEGORY_DOMAIN`, the security-intended stack-leak finding is emitted under a distinct security-domain category (e.g. routed under `security-headers`/`input-validation`, not `error-handling`) so it lands in the right twin bucket — the convention is fixed before authoring (WIRE-01).
  5. **Wired and gated.** All 5 touchpoints are complete — `triage.md` Express detection emitting `express` in `frameworks`, dispatch rows in `commands/review.md` and `commands/deep-review.md` (with model column), no spurious `score.py` twin (all six Express categories stand alone as `None` per the non-twin policy this phase), and the agent-count prose bumped (7→8) — and a `/vibe-check:deep-review` pass over the phase's changes is clean, with `framework-skill` confirming no half-wired residue (WIRE-01, VERIFY-01).

**Plans**: 1 plan (single wave)
Plans:

- [x] 24-01-PLAN.md — Author `agents/framework-express.md` (6 categories, fastapi-discipline hedging), wire all 5 touchpoints atomically (triage `express` detection + dispatch rows in both modes + count prose 7→8), add the score.py no-twin regression-lock test

**UI hint**: no

### Phase 25: framework-vue agent

**Goal**: vibe-check gains a `framework-vue` reviewer that catches real Vue 3 (Composition API) defects — reactivity loss, Composition-API misuse, lifecycle/cleanup leaks, template correctness, and direct prop mutation — wired across the 5 touchpoints and gated on a clean deep-review, while NOT shipping the Vue 3.5 reactive-props-destructure false positive.
**Depends on**: Phase 24 (no capability dependency — but shares the wiring files `triage.md`/`review.md`/`deep-review.md`/`score.py`, so executes after 24 to avoid prose collisions, following the pattern 24 established).
**Requirements**: VUE-01, WIRE-01, VERIFY-01
**Success Criteria** (what must be TRUE):

  1. **Triggers correctly.** On a diff that imports `vue` / `@vue/*` or touches a `.vue` SFC, the `framework-vue` reviewer dispatches in both modes; otherwise it stays silent (VUE-01, WIRE-01).
  2. **Reviews real Vue 3 defects.** The agent emits one schema-valid JSON object with categories from `reactivity` | `composition-api` | `lifecycle-cleanup` | `template` | `props`, covering `reactive()`-object destructure, a `ref` read in `<script>` without `.value`, conditional/looped ref/watch creation, `onMounted` listeners with no `onUnmounted` teardown, missing/`index` `:key`, `v-if`+`v-for` on the same element, and direct prop mutation (VUE-01).
  3. **Does NOT ship the 3.5 props-destructure false positive.** The agent does not flag `const { x } = defineProps(...)` as a defect (reactive since Vue 3.5+) — only `reactive()`-object destructure is flagged; off-hunk `reactive()`/`ref` provenance and off-hunk `onUnmounted` teardown are hedged, not asserted (VUE-01).
  4. **Wired and gated.** All 5 touchpoints complete (`triage.md` Vue detection; both dispatch rows; all five Vue categories stand alone as `None` in `score.py` per the non-twin policy this milestone; agent-count prose bumped 8→9), and a `/vibe-check:deep-review` pass over the phase's changes is clean, with `framework-skill` confirming no half-wired residue (WIRE-01, VERIFY-01).

**Plans**: 1 plan (single wave)
Plans:

- [x] 25-01-PLAN.md — Author `agents/framework-vue.md` (5 categories, fastapi-discipline hedging, the Vue 3.5 defineProps-destructure FP-guard), wire all SIX touchpoints atomically (triage `vue`/`.vue` detection + dispatch rows in both modes + index.md matrix row + count prose 8→9), add the score.py no-twin regression-lock test

**UI hint**: yes

### Phase 26: framework-angular agent

**Goal**: vibe-check gains a `framework-angular` reviewer that catches real Angular defects — RxJS subscription leaks, change-detection misuse, DI scope errors, lifecycle-hook bugs, and RxJS composition pitfalls — wired across the 5 touchpoints and gated on a clean deep-review.
**Depends on**: Phase 25 (no capability dependency — shares the wiring files, so executes after 25 to avoid prose collisions).
**Requirements**: ANGULAR-01, WIRE-01, VERIFY-01
**Success Criteria** (what must be TRUE):

  1. **Triggers correctly.** On a diff that imports `@angular/*` or touches Angular component/service/module files, the `framework-angular` reviewer dispatches in both modes; otherwise it stays silent (ANGULAR-01, WIRE-01).
  2. **Reviews real Angular defects.** The agent emits one schema-valid JSON object with categories from `rxjs-leaks` | `change-detection` | `di-scope` | `lifecycle` | `rxjs-composition`, covering `.subscribe()` with no `unsubscribe`/`takeUntil`/`takeUntilDestroyed`/async-pipe, in-place `@Input` mutation under `OnPush`, nested subscribes vs `switchMap`/`mergeMap`, `@Input`-read-in-constructor / `@ViewChild`-in-`ngOnInit`, and `providedIn`/`providers:[]` scope errors (ANGULAR-01).
  3. **Hedges on invisible context.** Change-detection findings are hedged when the `OnPush` decorator is off-hunk; leak claims are medium-confidence when `ngOnDestroy`/`destroy$` teardown is outside the hunk; both `takeUntilDestroyed()` and `takeUntil(destroy$)` are accepted as legitimate (ANGULAR-01).
  4. **Wired and gated.** All 5 touchpoints complete (`triage.md` Angular detection; both dispatch rows; all five Angular categories stand alone as `None` in `score.py` per the non-twin policy this milestone; agent-count prose bumped 9→10), and a `/vibe-check:deep-review` pass over the phase's changes is clean, with `framework-skill` confirming no half-wired residue (WIRE-01, VERIFY-01).

**Plans**: 1 plan (single wave)
Plans:

- [x] 26-01-PLAN.md — Author `agents/framework-angular.md` (5 categories rxjs-leaks / change-detection / di-scope / lifecycle / rxjs-composition, fastapi-discipline hedging + the D-03 modern-idiom SAFE guard: takeUntilDestroyed / takeUntil(destroy$) / async-pipe / self-completing sources / signals never flagged), wire all 6 touchpoints atomically (triage `@angular/*` import-gated detection + dispatch rows in both modes + index.md matrix row + count prose 9→10 across three anchors), add the score.py no-twin regression-lock test

**UI hint**: yes

### Phase 27: framework-electron agent (security-weighted)

**Goal**: vibe-check gains a security-weighted `framework-electron` reviewer that leads with CVE-class misconfiguration — `webPreferences` hardening, preload over-exposure, IPC input validation, navigation safety, content loading, and process hardening — wired across the 5 touchpoints (including the one genuine `ipc-validation`→security twin in `score.py`) and gated on a clean deep-review.
**Depends on**: Phase 26 (no capability dependency — shares the wiring files, so executes after 26 to avoid prose collisions). This is the first phase that adds a `score.py` `CATEGORY_DOMAIN` twin, so it also touches the `score.py` unit tests.
**Requirements**: ELECTRON-01, WIRE-01, VERIFY-01
**Success Criteria** (what must be TRUE):

  1. **Triggers correctly.** On a diff that imports `electron` or touches main-process / preload / `webPreferences` config, the `framework-electron` reviewer dispatches in both modes; otherwise it stays silent (ELECTRON-01, WIRE-01).
  2. **Leads with CVE-class misconfiguration.** The agent emits one schema-valid JSON object with categories from `webpreferences-hardening` | `preload-exposure` | `ipc-validation` | `navigation-safety` | `content-loading` | `process-hardening`, flagging `nodeIntegration: true`/`contextIsolation: false` as headline CRITICALs, raw-`ipcRenderer`/bare-`invoke` preload exposure, unvalidated IPC args into fs/shell/SQL sinks, `shell.openExternal`/missing-navigation-guards, and `http:`/missing-CSP content loading — each mapping the attack path (renderer XSS → Node RCE) and the safe form (ELECTRON-01).
  3. **Version-gated hedging on omitted flags.** Explicit unsafe flags are flagged with high confidence; *omitted* flags are hedged with a version note (secure defaults: `nodeIntegration` ≥5, `contextIsolation` ≥12, `sandbox` ≥20) rather than asserted "insecure"; centralizable guards (`will-navigate`, CSP, sender checks) are phrased "no guard visible here; confirm not applied centrally" at medium (ELECTRON-01).
  4. **The `ipc-validation`→security twin is mapped (and ONLY that one).** `score.py`'s `CATEGORY_DOMAIN` maps `ipc-validation` → `security`'s domain (the earned twin — an IPC handler flowing a renderer arg into a sink co-locates with `security`'s `injection`/`path-traversal`), with a regression-lock unit test; `webpreferences-hardening`, `preload-exposure`, and the rest stand alone as `None` (mapping them would spuriously confirm unrelated co-located security findings) (WIRE-01).
  5. **Wired and gated.** All 5 touchpoints complete (`triage.md` Electron detection; both dispatch rows; the single `ipc-validation` twin + test; agent-count prose bumped 10→11), and a `/vibe-check:deep-review` pass over the phase's changes is clean, with `framework-skill` confirming no half-wired residue (WIRE-01, VERIFY-01).

**Plans**: 1 plan

- [x] 27-01-PLAN.md — Author security-weighted framework-electron + wire 6 touchpoints (first real score.py twin: ipc-validation→security)

**UI hint**: no

### Phase 28: framework-react-native agent

**Goal**: vibe-check gains a `framework-react-native` reviewer that catches RN-specific defects `framework-react` does NOT — list perf, platform branching, native listener cleanup, Reanimated worklet rules, Expo/config gaps, and native-component crashes — triaged DISTINCTLY from web React (emits BOTH `react` and `react-native`), wired across the 5 touchpoints (including the `list-perf`→impact twin), and gated on a clean deep-review. As the last agent to land, this phase closes the agent-count prose coherence at 12 (WIRE-02).
**Depends on**: Phase 27 (no capability dependency — shares the wiring files, so executes after 27 to avoid prose collisions). Last agent phase; the fleet is complete (12 language+framework agents) after this lands, so WIRE-02 is fully realized here.
**Requirements**: RN-01, WIRE-01, WIRE-02, VERIFY-01
**Success Criteria** (what must be TRUE):

  1. **Triggers correctly AND distinctly from React.** On a diff that imports `react-native` / `expo` / `expo-*` / `@react-navigation/*` / `react-native-reanimated` (or native primitives like `View`/`FlatList`), triage emits BOTH `react` AND `react-native` (so `framework-react` keeps covering the shared JSX/hook surface and this agent is additive, not a replacement); on a plain web-React diff (`react-dom` / DOM tags / `react`-only hooks) it is NOT dispatched (RN-01, WIRE-01).
  2. **Reviews RN-specific defects only.** The agent emits one schema-valid JSON object with categories from `list-perf` | `platform` | `native-cleanup` | `reanimated` | `expo-config` | `native-component`, covering `.map()`/`ScrollView` over an unbounded list, `Platform.OS` gaps, native listeners (`AppState`/`Linking`/`BackHandler`) without `.remove()` teardown, worklet `runOnJS` boundary errors, AsyncStorage-for-secrets vs SecureStore, and native-component traps (unwrapped text, `onClick` vs `onPress`) — staying in the RN-native lane and NOT re-emitting generic hook/key/dep-array checks `framework-react` already owns (RN-01).
  3. **Hedges on invisible context.** List-perf is not flagged on a tiny static list (only potentially-unbounded collections); listener-leak is hedged when the effect's cleanup `return` is below the diff window; the Reanimated missing-`'worklet'`-directive check is hedged (Babel plugin auto-injects); `app.json` platform/permission checks are hedged when the manifest is off-hunk (RN-01).
  4. **The `list-perf`→impact twin is mapped (and ONLY the new one).** `score.py`'s `CATEGORY_DOMAIN` maps `list-perf` → `impact`'s domain (the earned `perf` twin), with a regression-lock unit test; `platform`, `native-cleanup`, `reanimated`, `expo-config`, `native-component` stand alone as `None` (`expo-config` secret-storage is deliberately NOT twinned to `security` this milestone) (WIRE-01).
  5. **Agent-count prose fully coherent at 12, wired and gated.** With the fifth and final agent landed, `commands/review.md`'s `framework-*` list, the `floor + N` math, the agents/chunk range, the estimated-dispatch upper bound, and the illustrative cost bracket are all internally consistent at the full 12-agent (7→12) fleet; `framework-skill`'s own wiring check finds no half-wired residue; and a `/vibe-check:deep-review` pass over the phase's changes is clean (RN-01, WIRE-01, WIRE-02, VERIFY-01).

**Plans**: 1 plan (single wave)
Plans:

- [x] 28-01-PLAN.md — Author `agents/framework-react-native.md` (six RN-native categories: list-perf / platform / native-cleanup / reanimated / expo-config / native-component, fastapi-discipline hedging + the four D-04 FP-guards), wire all 6 touchpoints atomically (triage DUAL-EMIT react+react-native import-gated detection + dispatch rows in both modes + index.md matrix row + count prose 11→12 across the four anchors, CLOSING WIRE-02 at 12), add the score.py `list-perf`→impact twin + its regression-lock test

**UI hint**: yes

### Phase 29: Efficacy Test + Version Bump + Tag (CLOSE)

**Goal**: Prove all five new agents work via the project's established planted-fixture N=3 smoke pattern (each fires on its framework, stays silent on a no-framework diff, and catches a planted defect), bump `plugin.json` 2.6.0→2.7.0, tag `v2.7`, and publish — closing the milestone.
**Depends on**: Phases 24, 25, 26, 27, 28 (ALL five agents must be authored, wired, and gated before the efficacy test can exercise the full fleet and the version can bump).
**Requirements**: CLOSE-01
**Success Criteria** (what must be TRUE):

  1. **Each agent triggers and catches.** A planted-fixture smoke test per agent proves it fires on its own framework, stays silent on a no-framework diff, and catches at least one planted defect — five passing smoke tests (CLOSE-01).
  2. **Versioned.** `plugins/vibe-check/plugin.json` is bumped `2.6.0` → `2.7.0` (CLOSE-01).
  3. **Tagged and published.** An annotated tag `v2.7` is created and the milestone is published (fast-forward `main` + push main + tag + branch) (CLOSE-01).

**Plans**: 2 plans (2 waves — efficacy proof, then sign-off + bump + tag + publish)
Plans:

- [x] 29-01-PLAN.md — Run the dogfood-RESULTS efficacy proof for all five framework agents (six planted fixtures: five framework + one no-framework control; fires/silent/catches) and author the UNSIGNED RESULTS-v2.7.md
- [x] 29-02-PLAN.md — Owner sign-off checkpoint -> write the single OWNER-SIGNOFF marker, bump .claude-plugin/plugin.json 2.6.0->2.7.0, annotated tag v2.7, publish (ff main + push main+tag+branch)

**UI hint**: no

## Phase Details (v2.8 Tunable, quieter reviews)

> Detail section for the in-progress v2.8 milestone. The spine is a repo-level
> `.vibe-check.toml` **config surface**, with the noise controls as its first real
> consumers — config is the vehicle; every knob reads from one schema. **Phase 30
> is the keystone** (the reader, the precedence chain, the per-key fail-safe); the
> remaining knobs plug into it. Phases are grouped by **enforcement boundary** —
> script-enforced knobs (`min_confidence`, `idiom_floor`, `thresholds`,
> `vibe-ignore`) land in `score.py` via new envelope keys; orchestrator-enforced
> knobs (`disabled` agents, `top_model`, `codex`, the fix-loop label) act in the
> dispatch/prose. **The scoring FORMULA is untouched throughout** — `min_confidence`
> *filters*, `thresholds` *parameterize* existing cutoffs, `idiom_floor` *caps* an
> existing category; no re-weighting. **Execution is SEQUENTIAL (30→31→32→33→34):**
> the shared files (`commands/review.md`, `commands/deep-review.md`,
> `scripts/score.py`, `scripts/test_score.py`) are touched by multiple phases, so
> concurrent edits would collide — the same serialization discipline v2.7 used for
> shared wiring files. The load-bearing invariant across every phase: a missing,
> malformed, or partially-invalid config degrades **per-key** to its built-in
> default with a warning and **never breaks a review** (zero-config back-compat ==
> v2.7 behavior). Design spec:
> `docs/superpowers/specs/2026-06-30-tunable-quieter-reviews-design.md`.

### Phase 30: Config surface foundation

**Goal**: vibe-check gains a repo-level `.vibe-check.toml` config surface — the orchestrator resolves the repo-root path once per run (`tomllib` with graceful degradation), applies the precedence chain (CLI flag > toml > built-in default) per knob, and degrades a missing/malformed/partial config per-key to defaults with a warning, never fatally. The three simplest consumers are wired to prove the surface end-to-end: `thresholds` (a `score.py` envelope key read by `band_for()`), and `disabled` agents + `top_model` (orchestrator dispatch decisions).
**Depends on**: Phase 29 (v2.7 ships first; this builds on the crash-proofed `score.py` envelope and the established orchestrator→`score.py` boundary). First v2.8 phase — establishes the config-read pattern the next three phases consume.
**Requirements**: CONFIG-01, CONFIG-02, CONFIG-03, CONFIG-04
**Success Criteria** (what must be TRUE):

  1. **Zero-config back-compat.** A repo with NO `.vibe-check.toml` runs exactly as v2.7 — all built-in defaults, no warning, no behavior change (CONFIG-01).
  2. **Read once, precedence honored.** The orchestrator reads the repo-root `.vibe-check.toml` a single time per run and resolves each knob's effective value as CLI flag > toml > default; a value set in the file overrides the default, and a flag overrides both (CONFIG-01, CONFIG-02).
  3. **Per-key fail-safe, never fatal.** An absent file → silent defaults; an unparseable file → all defaults + one warning line; a parseable file with one invalid key (wrong type / out-of-range / unknown band name) → THAT key falls back to default + a warning naming it while other valid keys still apply; an unavailable `tomllib` (Python < 3.11) degrades gracefully — in every case the review completes (CONFIG-03).
  4. **The three proving consumers work.** `thresholds` set in config changes banding (`band_for()` reads the envelope key, not literals); `disabled` agents are skipped at dispatch (the script never sees agents that did not run); `top_model` selects the model alongside `$VIBE_CHECK_TOP_MODEL` — each honored at scoring and dispatch respectively (CONFIG-04).
  5. **Schema documented.** The `.vibe-check.toml` schema (`[review]`/`[agents]`/`[noise]` sections, the keys above, defaults) is documented in the README, and `score.py`'s new `thresholds` envelope key is locked by a `test_score.py` unit test (CONFIG-04).

**Plans**: 3 plans (2 waves — Wave 1: the config.py helper + the score.py thresholds key, in parallel; Wave 2: orchestrator wiring + docs)
Plans:
**Wave 1**

- [x] 30-01-PLAN.md — Author `scripts/config.py` (the never-raise I/O-boundary reader: tomllib, per-key fail-safe, opus/fable + 3-sub-key strict-descent thresholds validation) + `scripts/test_config.py` locking every fail-safe/precedence branch [CONFIG-01/02/03]
- [x] 30-02-PLAN.md — Parameterize `score.py`'s `band_for(score, thresholds=None)` (default-inert) + thread an optional `thresholds` envelope key through its single call site; add `test_score.py` override + default-byte-stable regression locks (GOLDEN_DIGEST unchanged) [CONFIG-04]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 30-03-PLAN.md — Wire the three proving consumers in `review.md`/`deep-review.md` (dev-safe degrade config read, thresholds→envelope byte-stable, disabled→dispatch with core-agent announce, top_model env>toml>default) + config-health line + README schema doc [CONFIG-01/02/04]

**UI hint**: no

### Phase 31: Confidence axis

**Goal**: vibe-check surfaces the confidence axis — `agent_confidence` becomes a visible field on every rendered finding, and a new `min_confidence` (config) / `--min-confidence N` (flag) knob drops findings below N **before** scoring (a new `score.py` envelope key), with the dropped count shown in the honesty summary so nothing silently vanishes. The scoring formula is untouched: this is a pre-scoring filter, not a re-weight.
**Depends on**: Phase 30 (consumes the config surface — `min_confidence` is resolved by the precedence chain and passed into the `score.py` envelope; no capability dependency beyond that, but shares `score.py`/`test_score.py`/`commands/*.md` so executes after 30).
**Requirements**: CONF-01, CONF-02, CONF-03
**Success Criteria** (what must be TRUE):

  1. **Confidence is visible.** Every rendered finding shows its `agent_confidence` as a visible field in the report output (CONF-01).
  2. **Filters before scoring.** With `--min-confidence N` or `min_confidence = N`, findings with `agent_confidence < N` are dropped in `score.py` BEFORE scoring — they get no band, do not cross-confirm, and do not influence any other finding's score; the formula and band math are byte-unchanged (CONF-02).
  3. **Nothing vanishes silently.** The count of confidence-filtered findings appears in the honesty/filtered summary, so a developer always sees how many findings the threshold removed (CONF-03).
  4. **Precedence + default hold.** `--min-confidence` (flag) overrides `min_confidence` (config) overrides the default (no filtering); the new envelope key is locked by `test_score.py` cases proving sub-N findings are dropped pre-scoring and that the default leaves behavior unchanged (CONF-02).

**Plans**: TBD
**UI hint**: no

### Phase 32: Idiom floor + `vibe-ignore` marker (script-enforced noise knobs)

**Goal**: vibe-check gains the two script-enforced noise knobs. `idiom_floor` caps the `idiom` category at a tunable max band (default `medium`, so idioms never block finalize) via the existing category-aware capping in `score.py`. `// vibe-ignore: <reason>` joins the existing ±2 silenced-marker grep in `silenced_nearby()`: a marker with a non-empty reason suppresses the nearby finding, while a bare `// vibe-ignore` (no reason) is itself flagged as a low finding ("suppression without reason") to keep an audit trail. Both read config and are enforced in `score.py`.
**Depends on**: Phase 31 (no capability dependency — shares `score.py`/`test_score.py`/`commands/review.md`, so executes after 31 to avoid collisions on the envelope-key and silenced-marker edits, following the serialization the milestone uses).
**Requirements**: NOISE-01, NOISE-02, NOISE-03
**Success Criteria** (what must be TRUE):

  1. **Idioms are floored, tunable.** An `idiom` finding never exceeds the `idiom_floor` band (default `medium`) — so idioms never block finalize; setting `idiom_floor` higher/lower (or off) moves the cap, reusing the existing category-aware capping mechanism without touching the formula (NOISE-01).
  2. **`vibe-ignore` suppresses with a reason.** A `// vibe-ignore: <reason>` marker within ±2 lines of a finding suppresses that finding, riding the existing silenced-marker grep in `silenced_nearby()` (NOISE-02).
  3. **A bare marker is itself flagged.** A `// vibe-ignore` with no reason does NOT suppress; instead it surfaces as a low "suppression without reason" finding, keeping suppressions auditable (NOISE-03).
  4. **Locked by unit tests.** `test_score.py` proves: `idiom_floor` caps the band tunably (up/down/off); a reasoned `vibe-ignore` suppresses within ±2 and not outside it; a bare marker yields a low finding; and a malformed `idiom_floor` value falls back to the `medium` default per the per-key fail-safe (NOISE-01, NOISE-02, NOISE-03).

**Plans**: TBD
**UI hint**: no

### Phase 33: Codex legibility + safer fix-loop default (orchestrator-only knobs)

**Goal**: vibe-check gains the two orchestrator-enforced knobs, both pure prose/dispatch edits with NO `score.py` change. Codex stays `auto` by default but every run now prints one legible line stating what Codex did (joined / skipped-with-reason / off-via-config), controlled by a `--codex` flag and a `[noise] codex` config override (`off` | `auto` | `on`). The fix loop's apply-all option no longer carries the "(Recommended)" label — an autonomous committer making semantic edits should not nudge toward blind apply-all.
**Depends on**: Phase 32 (no capability dependency — shares `commands/deep-review.md`/`commands/review.md`, so executes after 32; the Codex knob reads the config surface from Phase 30).
**Requirements**: LEGIBLE-01, LEGIBLE-02, LEGIBLE-03
**Success Criteria** (what must be TRUE):

  1. **Codex is always legible.** Every run prints one clear line about what Codex did — joined, skipped-with-reason, or off-via-config — so the user never silently gets native-only without knowing; the default behavior stays `auto` (LEGIBLE-01).
  2. **Codex is controllable.** A `--codex off|auto|on` flag and a `[noise] codex` config key control Codex invocation, resolved by the precedence chain (flag > config > the `auto` default) (LEGIBLE-02).
  3. **Fix loop no longer nudges.** The fix loop's apply-all option is no longer labeled "(Recommended)" in `/review` (and `/deep-review` by delegation) (LEGIBLE-03).
  4. **No core regression.** `score.py` and `test_score.py` are byte-unchanged this phase (these are orchestrator-only knobs); the diff- and `--all`-mode dispatch contracts are non-regressed (LEGIBLE-01, LEGIBLE-02, LEGIBLE-03).

**Plans**: TBD
**UI hint**: no

### Phase 34: Efficacy test + version bump + tag (CLOSE)

**Goal**: Prove every v2.8 knob works via the project's established planted-fixture smoke pattern (config read honored; `--min-confidence` filters before scoring; idiom floored; `vibe-ignore` suppresses with a reason and a bare marker self-flags; Codex announces; fix-loop default safe; malformed config degrades per-key), bump `plugins/vibe-check/.claude-plugin/plugin.json` 2.7.0 → 2.8.0, create the annotated tag `v2.8`, and publish — closing the milestone.
**Depends on**: Phases 30, 31, 32, 33 (ALL four work phases must be built and gated before the smoke proof can exercise every knob and the version can bump). It exercises every knob, so it is the last phase.
**Requirements**: CLOSE-01
**Success Criteria** (what must be TRUE):

  1. **Every knob is proven.** A planted-fixture smoke proof per knob passes: a `.vibe-check.toml` repo has its knobs honored while a no-config repo behaves as v2.7; `--min-confidence` drops sub-N findings before scoring with the count in the honesty summary; `idiom` is capped at `idiom_floor`; a reasoned `vibe-ignore` suppresses within ±2 and a bare marker self-flags; every run prints a legible Codex line; the fix loop no longer says "(Recommended)"; and a malformed config degrades per-key to defaults with a warning, never fatally (CLOSE-01).
  2. **Deep-review clean on every phase.** A `/vibe-check:deep-review` pass came back clean (no unresolved critical/warning) on each of Phases 30-33 — the milestone's own quality gate (CLOSE-01).
  3. **Versioned.** `plugins/vibe-check/.claude-plugin/plugin.json` is bumped `2.7.0` → `2.8.0` (CLOSE-01).
  4. **Tagged and published.** An annotated tag `v2.8` is created and the milestone is published (fast-forward `main` + push main + tag + branch) (CLOSE-01).

**Plans**: TBD
**UI hint**: no

## Backlog

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

### Phase 999.0: Safer fix-loop default — strip apply-all "(Recommended)" **[TOP-3 #3] [QUICK WIN]** (BACKLOG)

**Goal:** Change the fix-loop default away from "Apply all findings
(Recommended)." The fix loop is an autonomous committer making semantic edits to
things like race conditions; apply-all-and-commit is too aggressive even with the
good injection hardening. Default to "Apply selected" / "I'll apply them myself,"
or at minimum strip "(Recommended)" from the all-apply option.

**Requirements:** TBD

**Plans:** 0 plans

**Why 999.0 / why split out:** Pure UX/safety, ~5-minute edit, independent of the
deterministic-core work. Pulled out of 999.8 as a standalone immediate quick win
(Tier 0) so it ships before the larger correctness block. Numbered 999.0 to mark
it front-of-queue.

**Source:** `docs/superpowers/specs/2026-06-22-external-review-triage.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.1: Framework review agents — FastAPI, Express, Vue, Angular (BACKLOG)

**Goal:** Add framework-specific review agents to vibe-check so reviews of framework code get framework-aware checks (today only `framework-react` exists). Priority order is by actual repo usage across the user's projects.

**Requirements:** TBD

**Plans:** 0 plans

**Priority order (by repo count):**

1. ✅ **framework-fastapi** — 5 repos (dashboard, gsdboard, roonseek, triggarr, VolvLog). Highest impact. SHIPPED in milestone v2.1 (see milestones/v2.1-ROADMAP.md). Checks: dependency-injection misuse, missing async discipline, Pydantic/validation gaps, wrong status codes.
2. **framework-express** — 3 repos (iPlayarr, iviewarr, ytfortv). Checks: middleware ordering, unhandled async route errors, missing error-handling middleware, security header defaults.
3. **framework-vue** — 2 repos (iPlayarr frontend, VolvLog). Checks: reactivity pitfalls (ref vs reactive), Composition API misuse, lifecycle/cleanup, key props.
4. **framework-angular** — 1 repo (seedsync). Checks: RxJS subscription leaks, change-detection, DI, lifecycle hooks.
5. **framework-electron** — 1 repo (sonoscrub; its React side is already covered by framework-react). Checks: main-vs-renderer process boundary, `nodeIntegration`/`contextIsolation` security settings (CVE-class — misconfiguration is a real vuln), IPC input validation, `webPreferences` hardening, preload-script exposure. Security-heavy — arguably higher value per build than its 1-repo count suggests.
6. **framework-react-native** — 0 of the author's repos; **driven by shared-user need** (mageema's `templepocus-new` is React Native 0.81 / Expo 54 / React Navigation). NOT covered by `framework-react` (shares JSX+hooks but different surface: no DOM, native components, FlatList perf, Platform.OS, native listener cleanup, Reanimated rules, Expo SDK/permissions, app.json config). Prioritize as "shared-tool value for the one other user," not by author-repo count. Triage must distinguish react-native from react (presence of `react-native`/`expo` deps).

**Implementation notes:**

- Each agent is a self-contained file following the `plugins/vibe-check/agents/framework-react.md` pattern.
- Add a trigger-condition row to the dispatch tables in `commands/review.md` and `commands/deep-review.md` (e.g. "triage.frameworks includes fastapi").
- `agents/triage.md` likely needs to detect these frameworks so the dispatch conditions fire.
- Additive — no risk to existing agents. Languages are already fully covered (TS + Python); no language-agent gaps.

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

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

### Phase 999.6: Test-sufficiency agent — risk-weighted coverage judgment (BACKLOG)

**Goal:** A `/deep-review` agent that judges whether changed code is *adequately* tested — the judgment layer raw coverage tooling can't provide. It does NOT recompute coverage; it **consumes the project's own coverage output** (or runs the project's existing coverage command when present) and reasons about *which gaps are dangerous*, flagging them in plain language. Today vibe-check has NO dedicated coverage agent — only an incidental "Test coverage gaps" bullet in `impact.md`, which has no rubric and competes with blast-radius analysis.

**Requirements:** TBD

**Plans:** 0 plans

**Why (motivating evidence — bridgarr, measured 2026-06-22):** ran vitest coverage on `thejuran/bridgarr` (TS monorepo, Vitest). Headline ~86% stmts / ~72% branch / 278 tests passing — looks reassuring and would let a non-engineer stop looking. But the table told a different story the % hides: `core/src/sabnzbd/router.ts` (a REQUEST ROUTER — high-risk) sat at **46% stmt / 26% branch**, the worst-covered file in the repo, while low-risk files were near 100%. Branch coverage (54% in core) meant >half the conditional/error paths never execute in a test. **A coverage tool gives the number; it does NOT say "the one request-handling file is half-tested and that's the scary gap."** That judgment is the agent's job.

**Design constraints:**

- **Don't recompute, consume.** Lean on the project's coverage tool (vitest/pytest-cov/go test -cover/etc.) for raw numbers; the agent adds the risk-weighting + plain-language verdict on top — same "deterministic tool detects, AI adjudicates" division as the Gitleaks/SARIF items (999.2/999.3).
- **Risk-weight the gaps.** A 46% router > a 0% healthz. Weight by what the file DOES (request handling, auth, input parsing, money/data mutation) not just by the raw %. Surface branch-coverage weakness explicitly (happy-path-tested / failure-path-untested is the classic trap).
- **deep-review only** (judgment-tier, like architecture/impact). Plain `/review` stays fast.
- **Non-engineer framing** — output should read "your X handles requests but only 26% of its branches are tested; the error paths at L146–208 are unguarded," not a bare coverage table. High value under the build-for-myself lens ([[vibe-check-backlog-reweight]]): catches the "high coverage so I'm fine" trap a PM-not-coder is most likely to fall into.
- **Complements, doesn't duplicate, GSD:** `gsd:add-tests` / `gsd:validate-phase` (Nyquist) cover the *phase/requirement* level; this is the *diff* level inside a review pass.

**Source:** observed during competitive-analysis discussion; see `docs/superpowers/specs/2026-06-22-competitive-analysis-and-feature-gaps.md` (§ test-coverage gap).

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.4: Tunable config — confidence axis, `--min-confidence`, thresholds & agent roster (BACKLOG)

**Goal:** Make vibe-check's review knobs first-class and tunable per-repo without
forking the plugin. Two strands, one config surface:

1. **Confidence axis** — surface `agent_confidence` as a visible, filterable
   field plus an optional `--min-confidence N` knob, matching the false-positive
   control every serious competitor exposes (Greptile 0–5, Qodo 0–10,
   Anthropic 0–100).

2. **Repo-level config** — the 80/70 band thresholds, the enabled-agent roster,
   and top-model selection, configurable via a `.vibe-check.toml` (or a CLAUDE.md
   block) instead of baked into templates. Today tuning means editing plugin
   internals — real fork pressure for a solo project.

*(Merged 2026-06-22: the external-review item "configurable thresholds & agent
roster" was folded in here rather than kept as a separate phase — both touch the
same knob surface, so they should ship as one config schema, not two
mechanisms.)*

**Requirements:** TBD

**Plans:** 0 plans

**Design decisions:**

- **Supplement, do NOT rewrite the formula** (from competitive analysis, D2).
  `agent_confidence` is already computed and folded into `scoring.md` via a
  carefully calibrated formula — re-deriving it re-opens the painful
  severity-weight tuning. Instead **surface** it as a filterable field and add
  `--min-confidence N` that filters *before* scoring. Keeps the band math
  untouched.

- **One config schema for all knobs** — `--min-confidence`, thresholds, agent
  roster, and top-model live in the same `.vibe-check.toml`, not separate
  mechanisms. Naturally consumes the deterministic core (999.7): thresholds are
  an input to the scoring script, so this is cleaner to build once 999.7 exists.

- **Low risk** — surfacing and parameterizing, not rewiring. The confidence
  strand is the only part that touches the core pipeline; the config strand is
  pure input-plumbing.

**Source:** `docs/superpowers/specs/2026-06-22-competitive-analysis-and-feature-gaps.md`
(confidence axis) + `docs/superpowers/specs/2026-06-22-external-review-triage.md`
(config surface)

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

> **Phases 999.7–999.13 below** come from an independent external engineering
> review (2026-06-22). The reviewer's overall read: "the engineering quality is
> real, so most of this is sharpening rather than rescue." Three items were
> flagged as highest-leverage and are marked **[TOP-3]**. Full review and the
> cluster→phase mapping live in
> `docs/superpowers/specs/2026-06-22-external-review-triage.md`.

### Phase 999.7: Extract deterministic core into a script **[TOP-3 #1]** (BACKLOG)

**Goal:** Move the pure functions the orchestrator currently asks the model to
compute by hand on every run — `in_diff`, the silenced-marker grep, the sha256
stable hash, the scoring formula, banding, and the carry-forward compare — into
one `score.py`/`.mjs` that the orchestrator pipes findings through. Makes them
exact, identical run-to-run, and unit-testable.

**Requirements:** TBD

**Plans:** 0 plans

**Why this is #1:** Single biggest correctness win in the review. Most of the
robustness cluster (999.9) is downstream of it — once scoring lives in a script
the model *cannot* silently skip it (rendered findings only exist if the script
ran), which is a stronger enforcement mechanism than the prose "HARD CONTRACT."
Extracting it also shrinks the orchestrator prose enough that much of that
scaffolding becomes unnecessary, and it dissolves the 999.8 state double-write
for free by collapsing to a single writer.

**Design notes:**

- Pure-function boundary: the script takes findings in, emits scored/banded
  findings + carry-forward deltas out. No review logic, no model judgment moves
  into it — only the arithmetic and string-matching that's deterministic anyway.

- Treat "the script ran" as the machine-checkable invariant (see 999.9).
- Sequence FIRST among the review phases — 999.8 and 999.9 both lean on it.

**Source:** `docs/superpowers/specs/2026-06-22-external-review-triage.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

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

### Phase 999.9: Robustness — cross-confirm matcher, carry-forward hash, invariants (BACKLOG)

**Goal:** Three correctness hardenings the reviewer grouped together:

1. **Harden the cross-confirm matcher.** Today it's first-token substring +
   line ±2 — fragile enough that `codex-adversarial.md` tells Codex to "phrase
   titles plainly" to game it (a code smell). Move to category-overlap + line
   proximity, or token-set Jaccard, so cross-confirmation doesn't hinge on two
   agents sharing a word.

2. **Fix the carry-forward content compare keying on `current_code`'s first
   line.** A generic first line (`}`, a common call, a closing paren) causes hash
   collisions and mis-tracked persistence. Hash more surrounding context, or fall
   back to a window when the first line is low-entropy.

3. **Add machine-checkable invariants where cheap.** Detect-and-warn after the
   fact for things prose can't enforce (e.g. parallel-dispatch). The scoring-ran
   invariant comes free with 999.7.

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:** Partly downstream of 999.7 — the matcher and hash are pure
functions that belong in the same script, and the invariants are easiest to
enforce once the deterministic core exists. **Sequence after 999.7.**

**Source:** `docs/superpowers/specs/2026-06-22-external-review-triage.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.10: Noise & Codex legibility — opt-in Codex, idiom floor, suppression marker (BACKLOG)

**Goal:** Three signal-to-noise / legibility changes:

1. **Make Codex opt-in, not auto-probed.** The probe path silently degrades in
   many ways (not installed, not authed, no timeout binary, non-representable
   diff) so most users get native-only and never know. An explicit `--codex`
   flag or `VIBE_CHECK_CODEX=1` makes it legible and removes a brittle surface
   from the default path. (The fallback engineering is good; the auto-discovery
   is where it leaks. Pairs with the 999.13 honesty-disclosure doc.)

2. **Tame idiom noise.** Taste-level idiom findings (Go CamelCase, Rust
   combinators / `&str` over `String`, Python `if __name__`) currently rely on
   severity weight to filter what the agent is told to report. Give idiom/style a
   hard floor that keeps it out of Medium, add an always-informational "style"
   tier that never blocks finalize, or split idioms into an opt-in agent.

3. **Add a persistent suppression marker** (`// vibe-ignore: <reason>`). The
   pipeline already greps `eslint-disable` / `# noqa` / `#[allow(`; a native
   marker stops an accepted-but-unfixable finding from resurfacing every pass.

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:** Three independent sub-features — can be split into separate
plans or promoted individually. The Codex-opt-in change is the largest surface
reduction; the suppression marker is the cheapest win.

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

### Phase 999.14: Dogfood-found defects — fix what `--all` caught in itself **[BUGS]** (BACKLOG)

**Goal:** Fix the concrete defects the Phase-12 `/vibe-check:deep-review --all`
dogfood found in vibe-check's **own** orchestration prose. Unlike every other
backlog item (which is *improve / add / configure*), these are **real bugs** —
the tool caught them in itself. Phase 12 deliberately left them unfixed (fixing
orchestration code was out of close-phase scope), so they land here as the
v2.4 head.

**Requirements:** TBD

**Plans:** 0 plans

**Critical (3) — fix first:**

1. `commands/review.md:893` — abandon-resume hint prints the OLD namespace
   (`/turingmind-code-review:…`) **and** an unbound `{{command}}` placeholder →
   the resume command it prints is copy-paste-broken. User-facing. (Line 827 in
   the same file already shows the correct self-identity render.)

2. `commands/deep-review.md:36` — stale hardcoded line-number citations into
   `review.md` (cites ~454/~581; real ~524/~646), off 70–80 lines → the
   orchestrator silently follows them to the wrong place at runtime. Fix: cite
   section names, not line numbers.

3. `templates/false-positive-rules.md:48` — band table keys off raw confidence
   and invents a phantom "High" band, contradicting `scoring.md`'s
   score-derived banding. (Cross-confirmed bugs + architecture + impact.)

**Warning (6):** architecture.md spec contradictions (#4, → feeds 999.13);
orphaned second scoring contract in `false-positive-rules.md` (#5/#7, → feeds
999.7's "one source of truth"); `--all --finalize` archives the wrong/nonexistent
state file (#6, the exact bug that made Phase 12 skip `--finalize`, → adjacent to
999.8); untrusted `PRIOR_PHASE` → `mv` with a prose-only allowlist (#8, → the
literal 999.7 thesis); Codex `title` carried without a char-allowlist (#9).

**Notable Medium / bonus:** Codex `fix_hint`/`title` injection path; markdown
fence-escape in `current_code`; multi-site fix commit drops sibling staged files;
version-header drift. **Quick win:** the fix-agent commit-title allowlist rejects
`=`, so a legitimate finding quoting `flag=value` (`shell=True`) can never be
committed — widen safely or auto-sanitize the commit title.

**Why this is the v2.4 head, not a feature:** these are defects of the
*cross-file-drift / prose-can't-enforce* class — the exact class 999.7
(deterministic core) and 999.8 (single-writer state) exist to eliminate. The
dogfood didn't just find bugs; it **empirically validated the correctness-core
thesis**, which is why v2.4 pairs the fixes (999.14) with the structural work
(999.7→999.9) in one milestone. Several findings explicitly feed those phases
(annotated above) — fix the instance in 999.14, prevent the class in 999.7/999.8,
fold the doc-drift items into 999.13.

**Source:** `.planning/phases/12-dogfood-efficacy-test-milestone-close/12-DOGFOOD-FINDINGS-BACKLOG.md`

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)
