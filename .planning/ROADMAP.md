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
- ✅ **v2.10 Opus 5 rebuild + quiet down** — Phases 38, 40-44 (shipped 2026-10-01 — 2.10.0; untuned MISS 6/18 · 13/15, retuned PASS 3/18 · 15/15; Phase 39 dissolved)
- 🚧 **v2.11 Quiet loop** — Phases 45-50 (in progress; design `docs/superpowers/specs/2026-10-01-quiet-loop-v2.11-design.md`, branch `feat/v2.11`)

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

<details>
<summary>✅ v2.10 Opus 5 rebuild + quiet down (Phases 38, 40-44) — SHIPPED 2026-10-01</summary>

- [x] **Phase 38: Grow the B3 set + Claude-5 baseline** — Grow the committed organic test set 6 → 10–12 diffs (sealed keys, provenance sidecars), pre-register the pass bar + decision rule, and baseline every diff ×3 on the UNCHANGED v2.9.0 plugin running on the current Claude 5 harness (dual duty: the Opus 5 re-measure) (completed 2026-09-08)
- [x] **Phase 40: Prose diet — restructure for Opus 5** — Restructure `commands/review.md` (~80K) + `commands/deep-review.md` (~35K): cut anti-improvisation scar tissue, progressive disclosure, extract the ranked deterministic families to tested scripts, verify (verify-only) the Phase 4.5→5 single-writer property (999.8), move every executable helper to trusted-plugin-root resolution + pre-edit path validation in the fix agent (TRUST-01/02), correct the cost anchors to the current model lineup — each batch guardrailed by a CAPPED B3 spot-check, full ×3 once at phase end (completed 2026-09-29)
- [x] **Phase 41: Wave 1 — scorer-side noise interventions** — Lift the scoring-formula freeze (Wave-1-scoped): B-SEV severity stability, B-REWEIGHT per-agent confidence calibration, H-LANE pile-on collapse — tuned offline via a zero-catch-regression replay harness on POST-DIET run data, then confirmed by a live spot-check (completed 2026-09-30)
- [x] **Phase 42: Wave 2 — agent-side noise interventions** — Prompt-only H-CORE: safe-change recognition + confidence ceilings on the loud lanes (bugs, security, impact, codex contract), with the real B3 false alarms baked in as never-flag classes (completed 2026-09-30)
- [x] **Phase 43: Prove — full post-change measurement** — Owner re-runs the full grown set ×3, scored from state against the sealed keys, evaluated honestly against the pre-registered bar in `RESULTS-v2.10.md`, with at most one retune (completed 2026-10-01)
- [x] **Phase 44: Close — 2.10.0 release** — plugin.json → 2.10.0, README efficacy numbers replaced + README model/cost docs made current for Claude 5 (COMPAT-01, static corrected anchors — no measured-cost claim), annotated tag `v2.10`, atomic hash-verified publish (completed 2026-10-01)

Shipped as plugin v2.10.0 (annotated tag `v2.10` on `edc450e`, main+tag+branch pushed atomically and
exact-hash verified). Untuned first pass MISS on the pre-registered bar (false alarms 6/18, catches 13/15);
after the one allowed prompts-only retune, combined PASS 3/18 · 15/15 (tuned on the same set — RESULTS-v2.10.md).
Phase 39 dissolved (COMPAT-02 → backlog 999.12). Milestone audit: 21/21 requirements, tech_debt (5 items).
Full details: `.planning/milestones/v2.10-ROADMAP.md`.

</details>

## v2.11 Quiet loop (Phases 45-50) — IN PROGRESS

**Goal:** A deep-review pass costs the owner one decision card, a finding is asked about once, and a
lane that has nothing to read does not run — with no catch-rate loss. Design (owner-approved, phase
split and order FIXED): `docs/superpowers/specs/2026-10-01-quiet-loop-v2.11-design.md`. Branch
`feat/v2.11`. Regression instrument: the sealed B3 set, compared against Phase 43's retuned result
(catch 15/15 · FP 3/18). Standing constraint: NO lane-prompt change, NO scorer change, NO model-tier
change anywhere in this milestone — any of those would confound the Phase-49 comparison.

- [x] **Phase 45: Lane gating on evidence** — `test-sufficiency` is not dispatched when Phase 1d finds no coverage artifact (announce line states why; dispatch count exactly one fewer there, unchanged everywhere else); `framework-skill`'s `frameworks`-includes-`skill` trigger pinned by a test. Deterministic — no prompt, no scorer change (completed 2026-10-01)
- [x] **Phase 46: Carry-forward integrity** — 999.8 single writer per field family across Phase 4.5→5; no automatic expiry (an unresolved finding persists until verified against HEAD or closed by an explicit owner decision with reason); per-finding decision snapshot so "unchanged since pass N, decision pending" is computable — all pinned by state-shape tests (completed 2026-10-02)
- [x] **Phase 47: Pause batching** — one combined card per fix-loop pass (apply all and rerun / apply selected… / skip and rerun / close out / abandon), one multi-select card at finalize for all unacknowledged mediums, unchanged-and-pending findings folded into the card and never re-asked; `$TURINGMIND_NONINTERACTIVE` unchanged (completed 2026-10-05)
- [x] **Phase 48: Fix-agent verification + git safety** — the fix agent verifies the cited condition no longer holds before committing (unverified ⇒ not committed, reported), one fix per hunk-isolated commit (999.15); detection agents cannot run mutating git in the reviewed repo, proven by a test (999.20); `agents/fix.md` description matches its `opus` pin (W2) (completed 2026-10-05)
- [x] **Phase 49: Measure + release 2.11.0** — full B3 ×3 on the release candidate (catch unchanged 15/15, false alarms ≤3/18), decision cards per firing counted from transcripts / gate log against the 5.5 baseline (or reported unavailable), README `214c7df` disclosure (W1), release gates before the publish plan, plugin 2.11.0 + tag `v2.11` + atomic publish (completed 2026-10-07)
- [x] **Phase 50: Finalize entry fix + 2.11.1 patch** — gap closure from the v2.11 milestone audit: `--finalize` (and the fix-loop card's Close out, which re-enters with it) reaches Finalize in GSD phase mode and default diff mode, pinned by a test; ships as plugin 2.11.1 through the standing release gates, disclosed in CHANGELOG/README (completed 2026-10-08)

### Phase 45: Lane gating on evidence

**Goal**: A deep-review lane that has nothing to read does not run — `test-sufficiency` is skipped, with a stated reason, on repos without a coverage artifact, and the `framework-skill` trigger rule is pinned — while every other lane's selection stays exactly as it was
**Depends on**: Phase 44 (v2.10 shipped; Phase 43's retuned B3 result is the comparison anchor)
**Requirements**: GATE-01, GATE-02
**Success Criteria** (what must be TRUE):

  1. On a repo where Phase 1d coverage discovery finds no coverage artifact, `/deep-review` does not dispatch `test-sufficiency`, the dispatch announce line says why in one line, and the dispatch count is exactly one fewer than the selection table would otherwise produce
  2. On a repo that does have a coverage artifact, `test-sufficiency` still dispatches and every other lane's selection and the dispatch count are unchanged — the gate removes a lane with nothing to read, never a finding
  3. `framework-skill` is dispatched only when triage's `frameworks` includes `skill`, and a mutation-tested test pins that rule (break the rule → the test fails)
  4. The phase lands no agent-prompt change and no `score.py` change — only dispatch prose/scripts and tests — so the Phase-49 B3 comparison against Phase 43 stays clean

**Plans:** 4/4 plans complete

Plans:
**Wave 1**

- [x] 45-01-PLAN.md — `scripts/coverage_gate.py` decision helper + unit tests (sealed CASES, exit-2 on malformed input, TDD)
- [x] 45-02-PLAN.md — Prose wiring: Phase 1d gate call, post-`disabled` selection gate + announce suffix, Phase 4 fixed Test Coverage note, spine/router doc updates

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 45-03-PLAN.md — `scripts/test_lane_gating.py`: golden-pinned selection tables + framework-skill rule (GATE-02), GATE-01 prose locks, in-memory + file-level mutation proofs, D-03 git-diff gate

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 45-04-PLAN.md — Live smoke on two scratch repos (no coverage vs coverage.xml) proving exactly-one-fewer; human-verify checkpoint

### Phase 46: Carry-forward integrity

**Goal**: A finding, once raised, is never silently lost and never silently kept — the review state file has one writer per field family, an unresolved finding persists until it is verified resolved or an owner decides, and each finding carries the decision snapshot the batching phase needs to say "unchanged since pass N, decision pending"
**Depends on**: Phase 45
**Requirements**: CARRY-01, CARRY-02, CARRY-03
**Success Criteria** (what must be TRUE):

  1. State-shape tests pin exactly one writer per field family across Phase 4.5→5 (999.8); introducing a second writer for any family makes the test fail (mutation-tested, not decorative)
  2. An unresolved finding from pass N is still present in pass N+1's carry-forward and in the finalize gate with no automatic expiry — it leaves only when verification against HEAD resolves it or an explicit owner decision (dismiss / defer, with a reason) closes it, recorded in the state file the way `medium_acknowledgments` are
  3. Every finding in state carries a decision snapshot (site, evidence, status at the last decision request), and "unchanged since pass N, decision pending" is computable from the state file alone — a test computes it for a fixture with changed and unchanged findings and gets the right answer for each
  4. Finalize does not write REVIEW.md while any unresolved finding has neither a verified resolution nor a recorded owner decision

**Plans:** 8/8 plans complete

Plans:
**Wave 1**

- [x] 46-01-PLAN.md — Wave 0: copy the live Phase-45 loop state into `scripts/fixtures/`, extend `future-schema.json` + `state_shape.py` with `snapshot` / `kept_open` / `resolved` / `decisions` / `fix_verdicts`; rollback procedure as schema data

**Wave 2** *(blocked on Wave 1)*

- [x] 46-02-PLAN.md — `scripts/carry_state.py` (TDD): finalize-counts, pending, record-decisions, record-fix-verdicts; legacy equality, no-expiry, gate table, orchestrator-compat tests
- [x] 46-03-PLAN.md — `score.py`: snapshot writer, ingress scrub, token/agent-guarded verdict acceptance → `resolved[]`; Phase-45 fixture replay at the scorer

**Wave 3** *(blocked on Wave 2)*

- [x] 46-04-PLAN.md — Review-pass prose: recheck tokens at dispatch, envelope wiring, `$FIX_VERDICTS_PREV`, `resolved` persisted by 4.5, render, Phase 5 `record-fix-verdicts`
- [x] 46-05-PLAN.md — Finalize prose: HEAD fingerprints + counts via helper, dismiss/defer for c/w/m via `record-decisions`, REVIEW.md Deferred + Resolved-by-verification (incl. no-rerun fix-obsolete) sections
- [x] 46-08-PLAN.md — `score.py`: kept-open obligation rows — a carried lead dropped by min_confidence / sub-threshold stays in `findings[]` with its stored scored fields (D-02 no-expiry under config or score changes)

**Wave 4** *(blocked on Wave 3)*

- [x] 46-06-PLAN.md — `test_carry_writers.py` one-writer-per-family lock (mutation-tested) + Phase-45 end-to-end replay through real modules (R1/R2/R3/R6)

**Wave 5** *(blocked on Wave 4)*

- [x] 46-07-PLAN.md — Live smoke on a scratch repo (`--plugin-dir` + `--add-dir`): raise → fix → recheck → finalize without a loop, one Defer; human-verify checkpoint

### Phase 47: Pause batching

**Goal**: A fix-loop pass costs the owner one decision card and finalize costs one, regardless of how many findings or unacknowledged mediums there are — and a finding that has not changed since it was last asked about is never asked about again on its own
**Depends on**: Phase 46 (consumes the decision snapshot and the no-expiry carry-forward)
**Requirements**: BATCH-01, BATCH-02, BATCH-03, BATCH-04
**Success Criteria** (what must be TRUE):

  1. A fix-loop pass with N findings asks the owner ONE card — apply all and rerun / apply selected… / skip and rerun / close out / abandon; the per-finding multi-select appears only after "apply selected", so a pass costs at most 2 cards for any N
  2. Finalize with M unacknowledged mediums asks ONE multi-select card (dismiss / will-fix per finding) with a single free-text reason covering the dismissed set — one card for any M
  3. Findings unchanged since their last decision request are listed inside the batch card as "unchanged since pass N, decision pending" and are never raised as a separate question
  4. With `$TURINGMIND_NONINTERACTIVE` set, the run behaves exactly as it did before this phase (pinned by a test)
  5. On a GSD-phase-mode run, the owner answers ≤2 cards per pass and ≤1 at finalize — the design spec's criterion 1, observed on a live run

**Plans**: TBD

### Phase 48: Fix-agent verification + git safety

**Goal**: A fix the owner accepts is a fix that was checked — the fix agent proves the cited condition is gone before it commits, each fix lands alone in its own commit, and no detection agent can change the reviewed repo through git
**Depends on**: Phase 47 (fixed order from the design spec; the fix agent's verified/unverified status is what the batch card reports back)
**Requirements**: FIX-01, FIX-02, FIX-03, FIX-04
**Success Criteria** (what must be TRUE):

  1. After editing, the fix agent re-checks the finding's cited condition; when it still holds, nothing is committed and the finding is reported as unverified with the reason (999.15)
  2. Each applied fix lands as its own commit containing only that fix's hunks — two accepted fixes in the same file produce two commits, each carrying only its own hunks (999.15)
  3. A detection agent that attempts a mutating git command (`stash`, `commit`, `checkout`, `reset`, `add`, …) in the reviewed repo is blocked, while read-only git (`diff`, `show`, `log`, `blame`, `status`, …) still works — proven by a mutation-tested test; mutation is confined to the fix agent's trusted commit path (999.20)
  4. `agents/fix.md`'s description states its actual `opus` pin (no `VIBE_CHECK_TOP_MODEL` claim), with a test that fails if description and frontmatter disagree (W2)
  5. After a fix commit the hand-off to the orchestrator's 999.21 revalidation (build / test / scan marked stale and re-run) is confirmed working — this phase confirms the hand-off, it does not build the orchestrator half

**Plans:** 10/10 plans complete

Plans:
**Wave 1**

- [x] 48-01-PLAN.md — `scripts/gitguard.py` pure fail-closed git classifier + DENY/ALLOW tables + mutants (FIX-03, D-08)
- [x] 48-02-PLAN.md — `scripts/fixstage.py` per-attempt lifecycle (begin/snapshot/seal, stale attempts quarantined) + undo that reverses only the fix's own delta (reverse merge; concurrent owner edits survive); `gitfixture.py` test helper (FIX-01 undo, D-04)
- [x] 48-03-PLAN.md — `scripts/fixcheck.py` baseline/after allowlisted check runner with exact labels (FIX-01, D-03/06/15)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 48-04-PLAN.md — `scripts/gitsnap.py` before/after git-state snapshot (Phase 43 stash shape) + D-16 comma titles in fixcommit
- [x] 48-05-PLAN.md — `hooks/hooks.json` PreToolUse hook + gitguard hook/notices/reset, scoped to vibe-check review agents (FIX-03, D-08/09/11/17)
- [x] 48-10-PLAN.md — `fixstage.py commit`: hunk-isolated commit of the sealed delta via merge-file + temp index, committed-tree verification (hook-altered commit withdrawn), CAS real-index sync, not-separable exit, retry-after-rejection fixture, HEAD hand-off contract (FIX-02, D-01/02/07, SC5)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 48-06-PLAN.md — `agents/fix.md` verified, hunk-isolated flow (begin/snapshot/seal/check/undo|commit with attempt id) + new statuses + W2 description; existing fix.md locks updated with mutants (FIX-01/02/04)
- [x] 48-07-PLAN.md — Phase 1 snapshot / Phase 3 entry gate + block notices + D-14 halt; contract paths; prose locks (FIX-03, D-10/11/14)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 48-08-PLAN.md — 50-fix-loop Step B: statuses, check labels, blobs rule, inline fallback via fixstage attempt flow; locks (FIX-01/02, D-05/13)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 48-09-PLAN.md — Live smokes (hook block, nested-agent deny, applied / applied-uncommitted / unverified fixes, no open attempt left, head_changed_since hand-off, hook latency) + owner checkpoint

### Phase 49: Measure + release 2.11.0

**Goal**: v2.11 is proven not to have cost any catch-rate, its pause saving is measured honestly, and it ships as plugin 2.11.0 through the standing release gates
**Depends on**: Phases 45, 46, 47, 48 (measures the complete release candidate)
**Requirements**: REL-01, REL-02, REL-03, REL-04
**Success Criteria** (what must be TRUE):

  1. A full B3 ×3 run on the release candidate — clone auto-memory parked, installed-cache parity pre-flight, scored from state against the sealed keys — shows catch-rate unchanged from Phase 43 (15/15) and false-alarm rate no worse (≤3/18), recorded in `RESULTS-v2.11.md`
  2. Owner decision cards per deep-review firing are counted from session transcripts or the orchestrator gate log's deep-review `user_interactions` and compared to the 5.5 baseline; if neither source exists the metric is reported "unavailable" — it is never inferred from pass counts
  3. The README discloses the `214c7df` post-measurement Codex-wait change (W1)
  4. `plugin.json` is 2.11.0 and an annotated tag `v2.11` exists; the release gates (test / security / deep-review) passed on the release commits BEFORE the publish plan ran; main + tag + branch were pushed in one atomic, exact-hash-verified publish

**Plans**: TBD

### Phase 50: Finalize entry fix + 2.11.1 patch

**Goal**: The fix-loop card's "Close out" and a typed `--finalize` reach Finalize mode in every scope mode, and the fix ships as plugin 2.11.1
**Depends on**: Phase 49 (2.11.0 is published; this is a patch on top of tag `v2.11`)
**Requirements**: BATCH-01, REL-05
**Gap Closure**: Closes the BATCH-01 / Close-out→Finalize integration gap from `.planning/v2.11-MILESTONE-AUDIT.md` (carried from 47-08 as "D2", dropped in Phase 48)
**Success Criteria** (what must be TRUE):

  1. `phases/review/00-scope.md`'s `$SCOPE_ARGS` normalizer removes the value-less `--finalize` token, so `<phase> --finalize` resolves GSD phase mode, bare `--finalize` resolves default diff mode, and `--all --finalize` is unchanged; `--finalize` still reaches the spine's finalize trigger from `$ARGUMENTS`
  2. A test pins all three shapes (and fails if the strip is removed — mutation-checked)
  3. `plugin.json` is 2.11.1; CHANGELOG/README disclose that 2.11.0 shipped with Close out / `--finalize` broken in phase and diff mode and that 2.11.1 fixes it
  4. Release gates (test / security / deep-review) pass on the release commits before publish; main + `feat/v2.11` + annotated tag `v2.11.1` are pushed in one atomic, exact-hash-verified publish; tag `v2.11` is not moved

**Plans**: TBD

## Progress

**Execution Order:** phases execute in numeric order; v2.11 runs 45 → 46 → 47 → 48 → 49 (order fixed by the design spec). v2.9 and v2.10 are archived — see `.planning/milestones/v2.9-ROADMAP.md`, `.planning/milestones/v2.10-ROADMAP.md`.

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
| 38. Grow the B3 set + Claude-5 baseline | v2.10 | 6/6 | Complete    | 2026-09-08 |
| 39. Claude-5 compatibility + measured cost | v2.10 | — | Dissolved 2026-09-05 — COMPAT-01 → Phase 44, COMPAT-02 → backlog 999.12 | - |
| 40. Prose diet — restructure for Opus 5 | v2.10 | 14/14 | Complete    | 2026-09-29 |
| 41. Wave 1 — scorer-side noise interventions | v2.10 | 8/8 | Complete    | 2026-09-30 |
| 42. Wave 2 — agent-side noise interventions | v2.10 | 7/7 | Complete    | 2026-09-30 |
| 43. Prove — full post-change measurement | v2.10 | 7/7 | Complete    | 2026-10-01 |
| 44. Close — 2.10.0 release | v2.10 | 2/2 | Complete   | 2026-10-01 |
| 45. Lane gating on evidence | v2.11 | 4/4 | Complete    | 2026-10-01 |
| 46. Carry-forward integrity | v2.11 | 8/8 | Complete    | 2026-10-02 |
| 47. Pause batching | v2.11 | 8/8 | Complete    | 2026-10-05 |
| 48. Fix-agent verification + git safety | v2.11 | 10/10 | Complete    | 2026-10-05 |
| 49. Measure + release 2.11.0 | v2.11 | 9/9 | Complete    | 2026-10-08 |
| 50. Finalize entry fix + 2.11.1 patch | v2.11 | 2/2 | Complete    | 2026-10-08 |

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

> **Added 2026-09-05 (external source review + model-lineup check):** **999.15**, **999.16**, **999.17**
> appended at the end of this section; **999.12** RETURNED from v2.10 (was COMPAT-02) with a
> feasibility-spike gate. Suggested v2.11 order: 999.15 → 999.16 → 999.17 — all three sit in the
> "makes MY reviews better" tier; 999.17 costs ~6 owner runs. None may land inside v2.10's measured
> window (they change what the fix loop commits / which specialists dispatch / which model judges).

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

**Returned to backlog 2026-09-05** (was v2.10 COMPAT-02 / Phase 39): NO measurement
mechanism exists — the orchestrator explicitly cannot tokenize (review.md Phase 0.2
anti-pattern) and no harness per-Task usage signal is designed or known to be readable
from command prose. **Gate: a feasibility spike before any promotion** — if a command
cannot read actual per-Task usage from the harness, this item is an estimate with a new
label and should be DROPPED, not built. The static anchors are corrected in v2.10
(Phase 40 DIET-01 + Phase 44 COMPAT-01) regardless.

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

### Phase 999.15: Fix agent — hunk-isolated commits + real verification (BACKLOG)

**Goal:** The fix agent commits ONLY the change it made for a finding, verifies the fix
with something stronger than a re-read, and never sweeps a file's pre-existing
uncommitted edits into a `fix(review-pass-N)` commit.

**Why (verified 2026-09-05 against `agents/fix.md`):** step 6 runs `git add -- <file>`
on whole files, so when the default (uncommitted-work) review mode accepts a fix in a
file that also holds unfinished edits, those edits are committed under the fix's
message — the commit lies about its contents. Step 5's verification is "re-read, confirm
syntactically plausible"; no test or type-check runs. (The path-validation-before-edit
slice of the same reviewer finding is v2.10 TRUST-02, not this item.)

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:**

- Capture `git diff -- <file>` before editing; after editing, isolate the delta and stage
  only those hunks (`git apply --cached` on the computed patch) — never the whole file.

- **Owner decision (2026-09-05):** when the fix cannot be separated cleanly from
  pre-existing edits, leave it APPLIED BUT UNCOMMITTED and say so in the fix result — do
  not refuse the fix, do not commit ambiguously.

- Replace the plausibility re-read with the cheapest relevant real check available in
  the repo (targeted test file, type-check, or lint on the touched file); report which
  check ran, or that none was available — "verified" must mean something ran.

- Off the v2.10 measured path (Phase 43 runs are report-only), so this is v2.11 work.

**Source:** external source review of the plugin, 2026-09-05 (reviewer item 2), reproduced by the reviewer.

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.16: Dispatch inputs — deterministic framework routing + bounded chunks for large diffs (BACKLOG)

**Goal:** Specialist dispatch is decided by a tested script that reads the changed files'
actual imports plus package metadata (not by a Haiku agent that is told to look for
imports but is given no diff body), and a large diff is reviewed in bounded chunks
instead of downgrading every language/framework reviewer to Haiku.

**Why (verified 2026-09-05):** `agents/triage.md` derives `frameworks` "from imports
actually present in the diff", but the Phase-1 prompt in `commands/review.md` supplies
only `git diff --stat`, `--name-only`, and a root listing — no diff content. An edit
inside an existing framework file usually carries no import in the hunk at all
(`triage.md` already patches exactly this gap per-framework for React Native rather than
structurally). The `size_tier == "large"` rule downgrades all `language-*`/`framework-*`
agents to Haiku; the 2026-09 Sonnet 5 price cut ($2/$10) shrinks what that saves from 3×
to 2× on input while still costing specialist quality. The one v2.9 miss was NOT a
routing miss (the FastAPI lane fired; the miss was wrong-axis), so this is quality work,
not an urgent fix.

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:**

- `detect_frameworks(files) -> set` as a stdlib script: scan the changed files' imports
  (whole file, not hunk) + `package.json` / `pyproject.toml` / `go.mod` metadata; cache
  per run; feed the existing Selection table. Keep the `"skill"` file-shape exception.

- Reuse the `--all` chunk planner (`$CHUNK_PLAN`, Phase 0.2) for diff-mode large diffs;
  delete the Haiku downgrade rule.

- MUST NOT land inside v2.10 — it changes which specialists fire, which would confound
  the baseline-vs-post-change measurement (the milestone's tune-vs-measure caveat).

**Source:** external source review of the plugin, 2026-09-05 (reviewer item 5); Sonnet 5 pricing verified on the live pricing page the same day.

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.17: Top-tier Fable 5.1 A/B on the B3 set (BACKLOG)

**Goal:** Decide with data whether `/deep-review`'s default `<TOP>` tier should move from
Opus 5 to Fable 5.1 for the two judgment-gating agents (`bugs` + `architecture`).

**Why:** Anthropic's guidance (verified 2026-09-05) is Opus-5-first, Fable when evals at
higher effort still fall short — and vibe-check has no eval of Fable on this fleet. Fable
5.1 is 2× Opus on base price but its cache reads are 0.025× (vs 0.1×), which matters for
the position-stable `<files>` block the chunk agents share. The security agent stays on
Sonnet in both commands, so Fable's dual-use safety measures do not bear on the default.

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:** Run the 2 known-noisy should-quiet diffs + 1 should-catch diff ×3 with
`VIBE_CHECK_TOP_MODEL=fable` against the v2.10 post-change numbers (~9 owner runs, or ~6
if the catch diff is dropped); score from state against the sealed keys; decide on FP-rate
and catch-rate, not on vibes. Do NOT change the default inside v2.10 — it would confound
Phase 43. The README's "Fable ~2× Opus, ~3.3× Sonnet" line is corrected in v2.10 Phase 44
regardless of this outcome (Sonnet 5 is now $2/$10, so Fable is 5× Sonnet on input).

**Source:** model-lineup check 2026-09-05 (live models overview + pricing pages).

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.18: Ultrareview shadow pass — external-reviewer finding-class gap analysis (BACKLOG)

**Goal:** Learn which CLASSES of finding Anthropic's `/code-review ultra` surfaces on the
B3 diffs that vibe-check structurally cannot reach — and turn those into concrete agent /
lane / prompt backlog items. NOT a precision-recall benchmark against ultrareview.

**Why:** `/code-review ultra` is the strongest general-purpose reviewer the owner already
has on hand, it reviews the same unit vibe-check does (a branch or PR diff), and it has
never been pointed at the committed ground-truth set. The B3 kit makes this cheap to do
honestly: sealed per-diff answer keys already exist, so ultrareview's output can be
adjudicated against the SAME key the vibe-check runs are scored against, with no new
ground-truth work. The v2.9 retro precedent is [[v2.5-phase21-shipped]] — the
test-sufficiency agent's own deep-review found defect classes plan-review could not reach
BY CONSTRUCTION; that structural-gap finding was worth more than any score. Same shape here.

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:**

- **Scope it as qualitative.** The deliverable is a gap table: for each ultrareview
  finding, is it (a) also caught by vibe-check, (b) a real defect in the sealed key that
  vibe-check missed, (c) a real defect OUTSIDE the sealed key (key-expansion candidate),
  or (d) a false alarm. Bucket (c) is the highest-value output — it means the answer keys
  are under-specified, which affects every future measurement.

- **Do NOT compute a catch/FP rate for ultrareview and publish it as a comparison.** The
  realistic sample is a handful of hand-driven runs vs. vibe-check's ×3-over-10-12-diffs;
  the error bars would swamp the difference. Any such number would be a
  competitive-analysis artifact, which is exactly what [[vibe-check-backlog-reweight]]
  says to deprioritize. If a number is wanted anyway, it must carry its n and its CI.

- **Different jobs, state it up front.** Ultrareview is a generalist branch/PR reviewer;
  vibe-check fans out 12+ specialists with a confidence axis and noise ceilings. On a diff
  seeded with an Electron IPC gap, a miss by ultrareview measures generalist-vs-specialist,
  not reviewer quality. The write-up must say this before any table.

- **Owner-runtime, and it cannot be automated.** `/code-review ultra` is user-triggered and
  billed; the assistant cannot invoke it via Bash or otherwise. Each arm is a manual
  invocation + a manual capture paste. Budget ~1 run per diff, not ×3.

- **MUST NOT land inside v2.10's measured window.** It changes no plugin code, so it does
  not confound Phase 43 the way 999.15/16/17 would — but it competes for the same scarce
  owner-run budget (~80 runs milestone-wide, 36 of them Phase 38). Run it AFTER Phase 44
  ships, or in a gap where no measured baseline is open.

- **Cheapest honest version:** 2 diffs (1 should-catch, 1 should-quiet — reuse the two the
  Phase-40/41 spot-checks already use, so the vibe-check side is already recorded) ×1 run
  each. ~2 owner invocations. Expand only if bucket (b)/(c) hits land.

- Capture scaffolding lives at `plugins/vibe-check/docs/efficacy/ULTRAREVIEW-SHADOW.md`
  (template committed ahead of the run; see that file for the exact procedure).

**Source:** owner question 2026-09-07 ("is there a way to test this plugin against
Anthropic's ultrareview?"); scoped to a gap analysis rather than a benchmark in the same
exchange.

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.19: H-LANE site representation under per-member caps + staged-change false-alarm classes (BACKLOG)

**Goal:** Decide, with a replay, how a collapsed H-LANE site row is represented when its members
carry different caps, and decide whether "declared but not yet wired" and "stricter validator
breaks a legacy config" become never-flag prompt classes.

**Why:** Three questions were deliberately left open (two by Phase 42, one carried through Phase 43) and must not be lost.

(1) **The scorer-side site-representation question (Phase 42 CONTEXT D-07).** Since Phase 41
(D-03, D-14) a site collapses to ONE row that carries every member lane. Once members carry
per-member caps (Phase 42's `agent_confidence ≤ 45` sensitive-area ceiling), four things about
that row are under-specified: which member is the lead, and therefore which band, score and
`stable_hash` the row shows; whether a "second opinion" is judged per-member or per-group (a ≤ 45
Claude "sensitive area" note co-located with a Codex finding while Codex is `joined` makes the
whole group Codex-corroborated, which removes the 94 lone-lane cap and adds +10 to the Codex
member, so the ceiling can RAISE a Codex lone Warning to Critical; RESEARCH Pitfall 8); and the
fact that absorbed members are absent from the fix-loop, the finalize gate and the medium
acknowledgements (a capped note carried as an absorbed member can reach 70, the Medium floor, on
the persisted-and-re-corroborated path; RESEARCH §Cap math). It was deferred because it only
misbehaves under non-default config: with `idiom_floor=low` or custom thresholds. The default
config is byte-identical across 805e6cc / 36b57e8 / cafdba2 per a 60k-case fuzz. Changing the
scorer in Phase 42 would also have broken success criterion 3 (prompt-only) and re-opened the
Phase-41 evidence the Phase-43 comparison depends on.

(2) **Two staged-change false-alarm classes the owner scoped OUT of Phase 42 (owner decision after
42-RESEARCH, Pitfalls 3-4).** "Declared but never wired" / feature-incompleteness (a config value
or field added in one step of a staged change whose consumer is not in the diff) drives
should-quiet-6 (a Codex critical, byte-identical in all 3 runs) and should-quiet-7. "A stricter
validator breaks a legacy config" (the new check rejects a value the old code accepted) drives
part of should-quiet-4; Phase 42 adds only a MEDIUM-confidence consequence-of-tightening clause
for it. Expected Phase-43 residual: should-quiet-6 likely stays 3/3 and should-quiet-4 may keep
firing. The product question is whether a value added in one step of a staged change, whose
consumer is not in the diff, is a defect.

(3) **A misjudged real replacement is nearly invisible (Phase 42 owner carry, Phase 43 R6).** A
reviewer that finds and reads a real same-purpose replacement but misjudges its coverage (misses
the path that bypasses it) leaves only a `agent_confidence ≤ 45` capped note, usually filtered —
counted in the Filtered summary, not listed — whose text survives only in the raw per-lane outputs
(now archived per run as `lanes.json` from Phase 43). Making that case visible in the report needs a
scorer or report change; it must not land inside a measured window. Evidence pointer:
RESULTS-v2.10.md Phase-42 limitations; Phase-43 `lanes.json` archives. Related Phase-43 fact: the
retune's Rule 2 (a bypass inside an unchanged reused helper is a capped pre-existing gap) puts real
reused-helper bypasses on the same filtered path (RESULTS-v2.10.md Phase-43 §Retune).

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:**

- **Scorer and prompt work ship together, in one phase, behind a replay guard.** Any change to
  row lead / band / identity or to per-member second-opinion semantics is replayed offline
  against the archived B3 runs with `scripts/replay.py` before it lands, with the same
  every-member-axis guardrail Phase 41 used (no protected catch lost).

- **MUST NOT land inside v2.10's measured window.** Either half changes what Phase 43 measures:
  schedule it after Phase 44 ships.

- **Same leakage discipline as Phase 42 (D-01).** Any new never-flag prompt class is worded as a
  generic class only (no B3 identifiers, paths or diff ids), and `scripts/test_agent_prompts.py`
  guards it: the identifier-leakage scanner plus mutation-tested prose locks.

- Default config must stay byte-identical unless the owner explicitly accepts a default-config
  behavior change on the record.

**Source:** Phase 42 CONTEXT D-07 + owner decisions after 42-RESEARCH (2026-09-30, Open Questions
1-2); Phase-41 memory detail (v2.10-phase41-owner-runs); Phase 43 CONTEXT deferred ideas (R6).

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.20: Review agents must not run state-mutating git commands in the reviewed repo (BACKLOG)

**Goal:** Guarantee that `/vibe-check:review` and `/vibe-check:deep-review` agents never change the
git state of the repo under review: no `git stash` (push/pop/apply/drop), `checkout`, `switch`,
`reset`, `restore`, `commit`, `merge`, `rebase`, `clean`, `branch -D` or similar.

**Why:** A `git stash pop` was observed in Phase 43. During first-pass
triggarr-session-rotation run 3 (run commit `825bd49`) the measured review's compliance agent ran
`git stash pop` in the reviewed clone, popping the owner's pre-existing unrelated stash, then
re-stashed identical content under a new label ("restore: undo accidental stash pop …"). Nothing
was lost, but a review tool that mutates the reviewed repo is a safety defect: on a dirty tree a pop
can conflict or mix the owner's WIP into the reviewed change. The B3 runbook's tree-diff checks
could not see it (they do not cover the stash list). Recorded in RESULTS-v2.10.md Phase-43
§"Anomaly" and 43-04 deferred item D43-04-1.

**Requirements:** TBD

**Plans:** 0 plans

**Design notes:**

- Prompt rule in every review agent (read-only git only: `diff`, `show`, `log`, `blame`,
  `rev-parse`, `ls-files`, `status`), locked by `scripts/test_agent_prompts.py` with a mutation test.

- Consider an enforced guard rather than prose only: a PreToolUse hook or a restricted Bash
  allowlist for review subagents, plus a stash-list / HEAD / index snapshot compared before and
  after a review (fail loudly on any change).

- Add a stash-list and HEAD check to the B3 runbook `post` block so a future measured run would
  catch this mechanically.

- Changes the measured surface: MUST NOT land inside a measured window.

**Source:** Phase 43 run window (43-04 SUMMARY anomaly; orchestrator carry 2026-10-01).

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.21: Fix-agent hardening carry items from v2.11 (BACKLOG)

**Goal:** Close the Phase-48 carry items and the declared Phase-49 residuals that v2.11 deliberately
did not build (CONTEXT D-02), so the fix agent's commit path and the pass-level safety checks have
no known open edges.

**Why:** v2.11 shipped only the D-01 fixes inside the measured window. These items were parked so
the measured tree would not move; they are correctness/hygiene follow-ups, not new features.

**Requirements:** TBD

**Plans:** 0 plans

**Items:**

- git < 2.36 up-front check: fixstage needs `git hook run` (≥ 2.36); today an old git is found only
  at commit time (exit 1 refused). Detect it once at pass start and say so plainly.
- `git -C <bare> remote show` / uploadpack: the bare-repo remote probe path flagged in Phase 48.
- WebFetch/MCP hook coverage: the guard hooks cover Bash/Edit/Write; WebFetch and MCP tools are not
  covered.
- Exit-table single source: the fixcommit/fixstage exit table is restated in several docs
  (agents/fix.md, 50-fix-loop.md, docstrings); generate or lock from one source.
- Blocked-notice noise allowances: tune which Blocked notices are expected vs. surfaced.
- fixcommit CLI retirement: fixstage now owns the commit path; retire the standalone fixcommit CLI.
- refs/tags fetch halting a pass (49-01 residual): gitsnap excludes only `refs/remotes/*`, so a
  `git fetch --tags` during a pass halts it. Intentional today; decide whether tags get an allowance.
- 49-03 residual windows: (a) SIGKILL and default-disposition SIGTERM/SIGHUP raise no Python
  exception; (b) a second BaseException inside the backstop arm; (c) a published candidate rewound to
  exactly `base` by another writer; (d) unborn-branch interrupt reports exit 9 conservatively.

**Design notes:** Touches the fix agent and guard surface; MUST NOT land inside a measured window.

**Source:** Phase 49 CONTEXT D-02; 49-01 SUMMARY §Residual; 49-03 SUMMARY §Residuals (filed after
PUBLISH-VERIFIED of 2.11.0, 2026-10-07).

Plans:

- [ ] TBD (promote with /bm:review-backlog when ready)
