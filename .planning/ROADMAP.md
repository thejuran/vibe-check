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
- ✅ **v2.11 Quiet loop** — Phases 45-50 (shipped 2026-10-08 — 2.11.0 + 2.11.1 patch; B3 MISS 5/18 · 15/15 shipped as measured under owner waiver)
- ✅ **v2.12 Quiet without hiding** — Phases 51-55 (shipped 2026-10-17 — 2.12.0 under owner waiver; OUTCOME: UNMET — measurement incomplete; noise target not demonstrated; Phase 55 measurement deferred)

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

<details>
<summary>✅ v2.11 Quiet loop (Phases 45-50) — SHIPPED 2026-10-08</summary>

- [x] **Phase 45: Lane gating on evidence** (4/4 plans) — completed 2026-10-01
- [x] **Phase 46: Carry-forward integrity** (8/8 plans) — completed 2026-10-02
- [x] **Phase 47: Pause batching** (8/8 plans) — completed 2026-10-05
- [x] **Phase 48: Fix-agent verification + git safety** (10/10 plans) — completed 2026-10-05
- [x] **Phase 49: Measure + release 2.11.0** (9/9 plans) — completed 2026-10-07
- [x] **Phase 50: Finalize entry fix + 2.11.1 patch** (2/2 plans, gap closure) — completed 2026-10-08

Shipped as plugin v2.11.0 (annotated tag `v2.11` on `2a420db`) and the 2.11.1 patch (annotated tag
`v2.11.1` on `44c7cbf`). Each was published as one atomic, exact-hash-verified push of main, the tag and the branch.
First-pass B3 MISS on false alarms (5/18 vs ≤3/18), catches 15/15. The owner shipped as measured, and both
releases are disclosed as not B3-measured (owner waivers). The milestone audit found the Close-out/`--finalize`
entry broken in phase and plain mode; Phase 50 closed it. Re-audit: tech_debt, no blockers.
Full details: `.planning/milestones/v2.11-ROADMAP.md`.

</details>

<details>
<summary>✅ v2.12 Quiet without hiding (Phases 51-55) — SHIPPED 2026-10-17 — UNMET, measurement incomplete (owner waiver)</summary>

- [x] **Phase 51: Seal the holdout** (10/10 plans) — completed 2026-10-09
- [x] **Phase 52: Hardening + accepted-fix harness** (14/14 plans) — completed 2026-10-10
- [x] **Phase 53: False-alarm reduction** (14/14 plans) — completed 2026-10-15
- [x] **Phase 54: Freeze + release gates + integration audit** (14/15 plans + follow-ups 54-16/54-17) — closed 2026-10-17; 54-11 re-sweep cancelled, 54-13 delta review replaced by an owner-approved 21-file review, 54-14 not run
- ⏸ **Phase 55: Measure + ship 2.12.0** — measurement campaign DEFERRED (owner, 2026-10-17); the publish step ran under owner waiver

Shipped as plugin v2.12.0 (annotated tag `v2.12` on `a4b0c3f`), published as one atomic push of main
(fast-forward), the tag and `feat/v2.12`, verified on the remote. Outcome **UNMET — measurement incomplete**:
the noise target (B3 ≤3/18 · 15/15) was not demonstrated because the release measurement campaign was not
completed; v2.11 remains the last measured result. Ships reliability fixes (three-outcome reachability,
never-filtered Needs verification, fix-loop/Finalize hardening, format-53 state preservation). Known gaps:
FRZ-01–04, MEAS-01–05 (MEAS-06 under waiver). Full details: `.planning/milestones/v2.12-ROADMAP.md`.

</details>

## Progress

**Execution Order:** phases execute in numeric order. v2.9, v2.10, v2.11 and v2.12 are archived — see `.planning/milestones/v2.9-ROADMAP.md`, `.planning/milestones/v2.10-ROADMAP.md`, `.planning/milestones/v2.11-ROADMAP.md`. v2.12 is archived — see `.planning/milestones/v2.12-ROADMAP.md`. No milestone is in progress.

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
| 51. Seal the holdout | v2.12 | 10/10 | Complete    | 2026-10-09 |
| 52. Hardening + accepted-fix harness | v2.12 | 14/14 | Complete    | 2026-10-10 |
| 53. False-alarm reduction | v2.12 | 14/14 | Complete    | 2026-10-15 |
| 54. Freeze + release gates + integration audit | v2.12 | 14/15 | Closed (partial) | 2026-10-17 |
| 55. Measure + ship 2.12.0 | v2.12 | 0/? | Deferred (publish under waiver) | 2026-10-17 |

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

### Phase 999.22: Codex-led carried findings can never close on recheck (BACKLOG)

**Goal:** A carried finding whose lead agent is `codex-adversarial` can be resolved on a later pass
when its defect is fixed, instead of staying `needs-recheck` (often Critical) forever.

**Why:** Recheck hints (`20-dispatch.md` § Recheck hints, rule 3) go only to the agent that raised a
carried record, and `codex-adversarial` is not a Task agent, so a Codex-led row gets no hint and no
verdict — "the record simply stays carried". Seen on triggarr Phase 78 (2026-10-09, deep pass 2):
the cutoff-fault defect was reported at :698 (codex lead + impact member) and :704 (bugs). The fix
landed; bugs' R1 recheck resolved :704 and Codex's own pass-2 verdict was `approve` with 0 findings,
yet :698 stayed Critical `needs-recheck` because nobody was asked about it. The only closure paths
left are a fix-agent `obsolete` round-trip or an owner decision at Finalize — pure bookkeeping for
an already-fixed defect, and it can block Finalize's outstanding-C/W gate.

**Requirements:** TBD

**Plans:** 0 plans

**Candidate approaches (pick at planning):**

- Route a Codex-led record's hint to a native member of the same row (e.g. `impact` here), or to
  `bugs` as the default verifier, when the row has no native lead.

- Ask Codex itself: include carried Codex-led records in the next Codex launch's focus as recheck
  tokens and translate its verdicts through `codex_translate.py`.

- Let a same-site native `resolved` verdict (a different record within ±2 lines, same defect class)
  resolve a co-located Codex-led record — weakest; needs a guard against over-closing.

**Design notes:** Touches the `score.py` verdict guard (token/agent/carried checks) and Phase 2
dispatch; MUST NOT land inside a measured window. Pairs with 999.19 (H-LANE site representation).

**Source:** triggarr v2.12 Phase 78 deep-review, pass 2 (2026-10-09).

Plans:

- [ ] TBD (promote with /bm:review-backlog when ready)
