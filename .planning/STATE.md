---
gsd_state_version: 1.0
milestone: v2.9
milestone_name: Prove it
status: planning
stopped_at: Phase 37 planned (1 plan, checker passed iter 1)
last_updated: "2026-07-05T21:43:02.015Z"
last_activity: 2026-07-05
progress:
  total_phases: 17
  completed_phases: 2
  total_plans: 6
  completed_plans: 5
  percent: 12
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-01)

**Core value:** Catch real defects in a developer's changes before they ship — high coverage, low noise — so a reviewer who can't manually audit code can trust the agent's output as their safety net.
**Current focus:** Phase 999.1 — framework review agents fastapi express vue angular

## Current Position

Phase: 999.1
Plan: Not started
Status: Ready to plan
Last activity: 2026-07-05

## Performance Metrics

**Velocity:**

- Total plans completed (all milestones): 6
- Average duration: — min
- Total execution time: — hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 09 | 2 | - | - |
| 24 | 1 | - | - |
| 36 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 05 P01 | 5min | 3 tasks | 1 files |
| Phase 05 P02 | 4min | 2 tasks | 1 files |
| Phase 13 P01 | 5min | 1 tasks | 1 files |
| Phase 19 P01 | 14 | 1 tasks | 1 files |
| Phase 19 P02 | 10min | 3 tasks | 1 files |
| Phase 27 P01 | 3min | 3 tasks | 7 files |
| Phase 28 P01 | 12min | 2 tasks | 7 files |
| Phase 29 P01 | 7min | 2 tasks | 1 files |
| Phase 30 P01 | 3min | 2 tasks | 2 files |
| Phase 30 P02 | 3min | 2 tasks | 2 files |
| Phase 30 P03 | 4min | 3 tasks | 3 files |
| Phase 32 P01 | 6min | 2 tasks | 4 files |
| Phase 32 P02 | 8min | 2 tasks | 2 files |
| Phase 32 P03 | 5min | 2 tasks | 4 files |
| Phase 33 P01 | 4min | 2 tasks | 2 files |
| Phase 35 P01 | 9min | 3 tasks | 2 files |
| Phase 36 P01 | 21min | 5 tasks | 19 files |
| Phase 36 P03 | 15min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Decisions affecting current work (v2.9 "Prove it" — from the owner-approved design spec
`docs/superpowers/specs/2026-07-01-prove-it-v2.9-design.md`):

- v2.9 = 3 SEQUENTIAL phases (35 → 36 → 37) continuing numbering from v2.8's Phase 34. Goal: finish
  v2.8's shipped-but-unproven surface (no inert config keys), produce vibe-check's FIRST measured
  catch-rate / false-positive-rate from a committed reusable organic test set, and close. Release
  milestone (plugin 2.8.0 → 2.9.0).

- D-01: branch base is `main`; work on new branch `feat/v2.9`; the old `feat/framework-skill-reviewer`
  branch RETIRES (main is ahead of it after the v2.8 merge + all Fable docs live there).

- D-02: version 2.9.0, not 2.8.1 — `--codex` is a new user-facing capability and the milestone adds a
  new efficacy-artifact class.

- D-03: B3 sourcing stays ORGANIC-ONLY (no vibe-check-found bugs — no circular self-testing) and the
  test set is COMMITTED (reusable milestone-over-milestone regression check).

- D-04: WIRING BEFORE PROOFS inside Phase 35 — the frozen 33-02 orchestrator wiring lands first so the
  codex-announce smoke proof tests the REAL wiring, not the inert v2.8 state.

- D-05: scorer design challenges (H-CORE/H-DUP/H-LANE/B-SEV/B-XCONF/B-PROX/B-REWEIGHT) stay OUT of
  scope — they are explicitly gated on B3's numbers; acting before measuring inverts the milestone's
  own logic. The scoring FORMULA is untouched throughout (standing constraint since v2.8).

- Phase 35 rebases the frozen 33-02 plan (archived at
  `.planning/milestones/v2.8-phases/33-codex-legibility-safer-fix-loop-default-orchestrator-only-kn/33-02-PLAN.md`)
  against the post-Fable `commands/review.md` / `commands/deep-review.md` (the Fable remediation edited
  the same regions: Phase 0 gained the `$GUARD_PY` resolution block near the `$SCOPE_ARGS` normalizer
  sites; Phase 0.6's `--min-confidence` parse prose changed). The rebased plan re-passes the codex
  adversarial gate before execution. 33-02 is prose/dispatch only — `score.py`/`test_score.py`
  byte-unchanged.

- Phase 36 resumes `docs/design/b3-ground-truth/B3-STATUS.md`: build the run-kit (3rd should-catch diff
  = triggarr secret-in-logs, fix `d47b4c2` reversed — the subtle high-value case; ≥2 should-quiet
  diffs; per-diff answer key folding in A8 `/health` name-exemption + A16 axis-vs-site ambiguity; owner
  run-checklist). Owner drives `/deep-review` N=3 per diff (~15–18 runs, resumable across days —
  `/deep-review` is user-triggered, the assistant CANNOT invoke it); assistant scores vs key and writes
  the catch/FP report into `plugins/vibe-check/docs/efficacy/`.

- Recurring-risk pre-flight (Phases 35 + 36): the installed-plugin cache must equal repo `plugin.json`
  before any dogfood/smoke run — a stale cache poisoned 4 of the last 5 milestones.

Earlier decisions (v2.8) still on record:

- v2.8 spine: a repo-level `.vibe-check.toml` **config surface** was the milestone's vehicle; the noise controls were its first consumers. Phase 30 built the reader/precedence/fail-safe; Phases 31-33 plugged knobs into it. SHIPPED early-manual-close 2026-07-01 (Phases 30–32 full, 33-01 only, Phase 34 superseded).
- Phases grouped by **enforcement boundary**: script-enforced knobs (`min_confidence`, `idiom_floor`, `thresholds`, `vibe-ignore`) land in `score.py` via envelope keys; orchestrator-enforced knobs (`disabled` agents, `top_model`, `codex`, the fix-loop label) act in dispatch/prose.
- **The scoring FORMULA stays untouched**: `min_confidence` *filters before scoring*, `thresholds` *parameterize* existing cutoffs, `idiom_floor` *caps* an existing category — no re-weighting. Re-deriving `agent_confidence` is explicitly out of scope.
- Load-bearing invariant: a missing/malformed/partial config degrades **per-key** to its built-in default with a warning and **never breaks a review** — zero-config back-compat == v2.7 behavior.
- Precedence is **CLI flag > `.vibe-check.toml` > built-in default**, resolved per knob by the orchestrator before passing into the envelope (script-enforced) or acting directly (orchestrator-enforced).
- Phase 30 P01: config.py is the never-raise .vibe-check.toml I/O boundary (load_config -> (values,warnings)); inverts score.py's fail-closed posture — degrades per-key to defaults, __main__ exits 0 always (CONFIG-03).
- Phase 30 P01: D-02 thresholds schema LOCKED — {critical,warning,medium} non-bool ints in [1,100], strictly descending, medium>=70, whole-set fallback to None; two ordered pre-parse DoS guards (regular-file BEFORE 1-MiB cap).
- Phase 30 P02: band_for parameterized to band_for(score, thresholds=None); default path byte-identical, GOLDEN_DIGEST unchanged.
- Phase 32-01: idiom_floor cap ACTIVE by default at medium (A1); explicit off/none returns the literal 'off' sentinel (NOT None) end-to-end so absent != off is provable at the scorer; malformed fails SAFE to medium.
- Phase 32-02: vibe-ignore reasoned marker (within +/-2) rides the existing -50 silenced path; bare marker does NOT suppress but emits ONE synthetic low 'suppression' finding per bare occurrence.
- [Phase 35]: 35-01: --min-confidence folded into the Phase-0 $SCOPE_ARGS normalizer alongside --codex — Shared parse-timing bug; the normalizer ADDS GSD/PR/range reach + fixes the --all narrow-parse mis-read, never changes byte-correct diff/--all behavior
- [Phase 35]: 35-01: HIGH-B MOVE-SMOKE-INTO-2c — BashOutput smoke gate relocated inside the launch guard — So a non-launching Codex never hard-blocks the native review (SAFE-01/SAFE-02); Phase 2b header repurposed to a pointer, not deleted
- [Phase 35]: 35-01: rebase discipline held (D-06) — Executed diff deviates from frozen 33-02 ONLY by re-anchored line numbers + the one bare-all alias composition sentence; no design change
- [Phase 36]: 36-01: third organic should-catch = seedsyncarr 879266c (unclamped >100% progress); dashboard 052845e excluded per D-12 (DR3m-01 regex hit)
- [Phase 36]: 36-01: should-quiet picks owner-confirmed (confirm-all): triggarr 1a8c9f9, seedsyncarr 3c27e17, roonseek 2a6bbd9; 355c57f rejected by the line-survival gate
- [Phase 36]: 36-01: answer key pre-registered at ANSWER_KEY_COMMIT ef0ab67 with digest in the separate PREREGISTRATION.md manifest (key blob never contains its own hash)
- [Phase 36]: 36-02: owner drove /deep-review N=3 across all 6 diffs — 18/18 SCOREABLE runs committed + verified (len(passes)==1, head_sha==base_sha, tree.diff.sha256==kit EXPECTED value); pre-registration ordering intact (ANSWER_KEY_COMMIT ef0ab67 ancestor of HEAD, committed-blob digest == PREREGISTRATION.md ANSWER_KEY_SHA256, manifest touched once at cca63e2 strictly before first runs/ commit eca98ec)
- [Phase 36]: 36-02: D-06 exercised — should-quiet-1 run-2 captured, marked unscoreable, repeated (2 archived run-2.failed-* dirs; N-01/N-04 uv.lock mid-review rewrites → chflags immutable-flag prevention @ 4eff2aa); every diff has exactly 3 scoreable runs, no holes
- [Phase 36]: 36-02: Codex outcome recorded honestly from state attribution — codex-adversarial finding present in 16/18 runs; should-quiet-2 produced 0 findings all 3 runs (nothing to attribute, NOT skip evidence); should-quiet-3 run-1 had Codex in agents_run but no surviving codex-attributed finding. Runs measured shipped codex=auto (no --codex forcing)
- [Phase 36]: 36-03: FIRST measured numbers — catch-rate 8/9, FP-rate 6/9 (exact fractions D-09, FULL 9+9 pre-registered denominators, 18/18 scoreable, zero holes, no owner waiver). Scored from state.passes[-1].findings[] vs the committed key blob at ef0ab67 (score-from-blob gate: MANIFEST_COMMIT cca63e2 ordering proven, digest match, ancestry, runs/-clean + descent, per-diff FULL-worktree tree.diff consistency); score.py/test_score.py/config.py byte-frozen; pytest 356+221 green
- [Phase 36]: 36-03: autoescape run-1 = the pre-registered right-site-wrong-axis MISS (detected-below-threshold) — SITE ok but fleet named deprecation/breaks-startup, one finding explicitly "NOT an XSS regression"; runs 2-3 named XSS/autoescape → 2/3. should-quiet-2 clean 0/3; should-quiet-1 + -3 = 3/3 FP each. Codex contributed all 8 catches (codex=auto)
- [Phase 36]: 36-03: D-11 verdict = PROCEED on H-CORE/H-LANE/B-SEV/B-REWEIGHT (FP + axis-stability challenges this run implicates; should-quiet FPs are agent-self-sufficient not +10-cross-confirm-rescued → H-CORE/H-LANE not primarily H-DUP/B-XCONF) AND grow the committed set next milestone (N=3 coarse). Input to next-milestone B3-gated-challenge scoping, NOT an in-phase scorer change (formula frozen). Report appended to RESULTS-v2.9.md (no RESULTS-v3.md)

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work — planning details, not blockers]

- [Phase 35] The 33-02 plan is codex-APPROVED and frozen but NEEDS REBASING before execution — the Fable remediation edited the same review.md/deep-review.md regions (Phase 0 `$GUARD_PY` resolution near the `$SCOPE_ARGS` normalizer sites; Phase 0.6 `--min-confidence` parse prose). Do NOT blind-resume the old Phase-33 orchestrator resume files; the rebased plan must re-pass the codex adversarial gate.
- [Phase 35] WIRING BEFORE PROOFS: execute 33-02 first, THEN run the v2.8 smoke proofs — the codex-announce proof must test the real wiring, not the inert v2.8 state (D-04).
- [Phase 36] B3 needs OWNER RUNTIME (~15–18 `/deep-review` runs; the skill is user-triggered — the assistant cannot run it). The phase delivers a run-checklist with exact commands; runs are resumable and spreadable across days.
- [Phases 35/36] Stale installed-plugin cache poisons dogfood/smoke runs (recurred in 4 of the last 5 milestones) — pre-flight: installed version must equal repo `plugin.json` before any run.
- [Phase 37] The v2.8 evidence debt needs NO separate retroactive audit — it became v2.9 requirements (Phase 35), so the v2.9 milestone audit covers it.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Framework agents | Express, Vue, Angular, Electron, React-Native agents (backlog Phase 999.1) | Shipped v2.7 | v2.1 scoping |
| FastAPI depth | OpenAPI/contract checks; upload streaming/chunking refinements | Deferred | v2.1 scoping |
| Codex async | Background + second-pass folding (ASYNC-01) | Deferred | v2.2 scoping |
| Codex reach | Codex in `/review` via opt-in flag (ASYNC-02); configurable model/effort (ASYNC-03) | Deferred | v2.2 scoping |
| Whole-repo enhancements | Baseline-aware suppression (BASELINE-01), snapshot carry-forward (SNAPSHOT-01), Codex-over-whole-repo (CODEX-ALL-01) | Deferred | v2.3 scoping |
| Configurable & honest | Tunable config (shipped v2.8), measured cost (COST-01 / 999.12), docs pass (DOCS-01 / 999.13) | Partially deferred | v2.6 scoping |
| Dogfood hardening | Remaining v2.4/v2.5 Mediums — fix-agent prompt-injection hardening, `.planning/*-SUMMARY.md` force-tracking hygiene (HARDEN-01) | Deferred | v2.6 scoping |
| CI reach | gitleaks (SECRET-01 / 999.2), SARIF (SARIF-01 / 999.3), PR-posting (PRPOST-01 / 999.5) | Deferred | v2.6 scoping |
| **33-02 orchestrator wiring** | LEGIBLE-01/02/03 — NOW SCHEDULED as v2.9 Phase 35 (rebase + execute against post-Fable review.md/deep-review.md). ⚠ Plan needs REBASING before execution. | **Scheduled (v2.9 Phase 35)** | v2.8 manual close |
| **Phase-34 efficacy proofs** | Planted-fixture smoke proof per v2.8 knob + Phase 33's deep-review gate — NOW SCHEDULED as v2.9 Phase 35 (PROOF-01, PROOF-02). | **Scheduled (v2.9 Phase 35)** | v2.8 manual close |
| **Fable — answer-key fixes (A8/A16)** | A8 (`/health` name-exemption), A16 (axis-vs-site ambiguity) — NOW SCHEDULED into v2.9 Phase 36's per-diff answer key (B3-01). | **Scheduled (v2.9 Phase 36)** | v2.8 manual close |
| **B3 harness execution** | Catch-rate/FP-rate against the FIXED post-Fable system — NOW SCHEDULED as v2.9 Phase 36 (B3-01/02/03). | **Scheduled (v2.9 Phase 36)** | v2.8 manual close |
| **Fable — remaining** | `security.md` critique pass (needs Opus); all design challenges (H-CORE/H-DUP/H-LANE/B-SEV/B-XCONF/B-PROX/B-REWEIGHT) — gated on B3's numbers (v2.9 Phase 36 report states proceed/don't/need-more-data); `CATEGORY_DOMAIN` twin proposals (ts `async-discipline`→correctness, express `input-validation`→security). | Deferred (post-v2.9) | v2.8 manual close |

## Session Continuity

Last session: 2026-07-05T21:43:02.004Z
Stopped at: Phase 37 planned (1 plan, checker passed iter 1)
STATE + REQUIREMENTS traceability updated. Ready to plan Phase 35.
Resume: `/gsd:plan-phase 35` (Make v2.8 whole — rebase + execute 33-02, then the v2.8 smoke proofs).
Do NOT blind-resume the old Phase-33 orchestrator resume files — 33-02 needs a rebase first.

## Operator Next Steps

- **Next:** `/gsd:plan-phase 35` — Make v2.8 whole. First step is rebasing the frozen 33-02 plan
  against the post-Fable `commands/review.md` / `commands/deep-review.md`; the rebased plan re-passes
  the codex adversarial gate before execution. Wiring lands BEFORE the smoke proofs (D-04).

- Then Phase 36 (B3 — first measured quality numbers; owner drives ~15–18 `/deep-review` runs) and
  Phase 37 (close — bump 2.8.0→2.9.0, tag `v2.9`, publish, audit).

- Pre-flight before any dogfood/smoke run in Phases 35–36: installed-plugin cache must equal repo
  `plugin.json`.
