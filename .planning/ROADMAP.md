# Roadmap: vibe-check

## Milestones

- ✅ **v2.1 FastAPI review agent** — Phases 1-3 (shipped 2026-06-18)
- ✅ **v2.2 Codex adversarial reviewer** — Phases 4-6 (shipped 2026-06-21)
- ✅ **v2.3 Whole-codebase review mode (`--all`)** — Phases 7-12 (shipped 2026-06-22)
- ✅ **v2.4 Dogfood-driven hardening** — Phases 13-18 (shipped 2026-06-26)
- ✅ **v2.5 Sharper, more legible reviews** — Phases 19-22 (shipped 2026-06-28)

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


## Progress

**Execution Order:**
Phases execute in numeric order. v2.3 continues from v2.2: 7 → 8 → 9 → 10 → 11 → 12.

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
| 22. Efficacy Test + Version Bump + Tag | v2.5 | 0/2 | Not started | - |

## Phase Details (v2.4 Dogfood-driven hardening)

> Detail sections for the in-progress v2.4 phases. Shipped milestones' detail
> sections live in their archived per-milestone ROADMAPs
> (`.planning/milestones/v2.{1,2,3}-ROADMAP.md`).

### Phase 13: Safer Fix-Loop Default
**Goal**: The autonomous apply-all-and-commit path is no longer presented as the recommended default in the fix loop — a developer choosing how to apply findings is nudged toward review-then-apply, not blind bulk-commit.
**Depends on**: Nothing (first v2.4 phase; prose-only, ~5-min edit, no dependencies)
**Requirements**: FIXLOOP-01
**Success Criteria** (what must be TRUE):
  1. The fix-loop apply-all option in `/review` and `/deep-review` no longer carries the "(Recommended)" marker.
  2. The autonomous apply-all-and-commit option is not the prose-recommended default; the recommendation (if any) points at apply-selected / apply-myself.
  3. The fix loop still offers all existing apply choices — only the recommendation framing changed, no option removed.
**Plans**: 1 plan
- [x] 13-01-PLAN.md — Strip the Step A apply-all "(Recommended)" marker and neutralize the apply-all preference prose note in `commands/review.md` (deep-review.md inherits by delegation)

### Phase 14: Dogfood Critical + Warning Fixes
**Goal**: The 3 Critical + 6 Warning defects the `--all` dogfood found in vibe-check's own orchestration prose no longer reproduce — including the `--all --finalize` wrong-state-file bug that blocked Phase 12's close.
**Depends on**: Phase 13 (sequential; lands on the corrected fix-loop prose)
**Requirements**: DOGFIX-01, DOGFIX-02, DOGFIX-03, DOGFIX-04, DOGFIX-05, DOGFIX-06, DOGFIX-07, DOGFIX-08
**Success Criteria** (what must be TRUE):
  1. The abandon/resume hint prints a copy-paste-correct command — current `/vibe-check:…` namespace, no unbound placeholder — rendered by self-identity (DOGFIX-01 no longer reproduces).
  2. `deep-review.md`'s cross-references into `review.md` cite section names, not hardcoded line numbers, so drift can't misdirect the orchestrator (DOGFIX-02); and `false-positive-rules.md` defers banding to canonical `scoring.md` with no phantom "High" band (DOGFIX-03).
  3. `--all --finalize` resolves the correct mode-aware state file (`by-mode/all/<hash>.json`) instead of an unset `$PHASE_ID` path, so a whole-codebase review can finalize (DOGFIX-06 — the bug that blocked Phase 12).
  4. The Warning defects are gone: `architecture.md` no longer contradicts the specs (DOGFIX-04); the orphaned second scoring contract is removed and `false-positive-rules.md` points at `scoring.md` as the single scoring source (DOGFIX-05); untrusted `PRIOR_PHASE` is guarded before `mv` without relying on prose-only enforcement (DOGFIX-07); Codex `title` passes a character allowlist before reaching the renderer or fix agent (DOGFIX-08).
**Plans**: 3 plans (all Wave 1 — parallel, no file overlap)
- [x] 14-01-PLAN.md — review.md cluster: self-identity resume hint (DOGFIX-01), mode-aware `--all --finalize` state resolution (DOGFIX-06), verify the PRIOR_PHASE→mv guard (DOGFIX-07)
- [x] 14-02-PLAN.md — delete the orphan scoring contract + phantom "High" band and point at scoring.md (DOGFIX-03/05); reconcile architecture.md (DOGFIX-04)
- [x] 14-03-PLAN.md — convert deep-review.md line-cites to section names (DOGFIX-02); Codex title sanitize-and-keep (DOGFIX-08)

### Phase 15: Dogfood Medium Fixes + Fix-Agent Quick Win
**Goal**: The notable Medium injection/atomicity defects are closed and a legitimate finding whose title quotes `flag=value` (e.g. `shell=True`) can be committed by the fix agent.
**Depends on**: Phase 14 (split from it so Phase 14 stays a tight Critical/Warning unit)
**Requirements**: DOGFIX-09, DOGFIX-10
**Success Criteria** (what must be TRUE):
  1. The Codex `fix_hint`/`title` fix-agent injection path is closed, `current_code` markdown fences can no longer escape the report, and a multi-site fix commit no longer drops sibling staged files (DOGFIX-09 batch no longer reproduces).
  2. A finding whose title legitimately quotes `flag=value` (e.g. `shell=True`) can be committed by the fix agent — the commit-title allowlist is widened safely or the title is auto-sanitized for the commit while the original is preserved for display (DOGFIX-10).
**Plans**: 2 plans (both Wave 1 — parallel, no file overlap)
- [x] 15-01-PLAN.md — Defect A (DOGFIX-09): longest-run-aware fencing for the `{{current_code}}` render site in `templates/output-format.md` (close the report fence-escape)
- [x] 15-02-PLAN.md — Defects B+C (DOGFIX-09/10) in `agents/fix.md` + the `commands/review.md` ripple: make the commit pathspec the finding's full VALIDATED multi-path set (every file it touched, each validated) so a multi-site fix is atomic AND a foreign staged file is never swept in + reconcile the two review.md commit-step references to that set; widen the commit-title allowlist to permit `=` (Defect B mechanism revised 2026-06-23 after a codex CRITICAL: validated multi-path pathspec, NOT the withdrawn staged-index/clean-index approach)

### Phase 16: Deterministic-Core Script
**Goal**: A stdlib-only Python `score.py` owns the deterministic core — `in_diff`, the silenced-marker grep, the sha256 stable hash, the scoring formula, banding, per-command threshold filtering, and the carry-forward compare — as pure functions, and the orchestrator pipes findings through it so scoring is un-skippable. This introduces the first executable code into a previously prose-only plugin.
**Depends on**: Phase 14 (lands on a corrected prose baseline — including the removed orphaned scoring contract from DOGFIX-05)
**Requirements**: CORE-01, CORE-02, CORE-03
**Success Criteria** (what must be TRUE):
  1. `score.py` exists, is stdlib-only, and is a pure-function boundary: findings in → scored/banded findings + carry-forward deltas out, with no review logic or model judgment inside (CORE-01).
  2. `score.py` produces identical banding to the prior `scoring.md` prose on the pinned test cases — proven by a passing unit-test file that pins the current formula's outputs (CORE-02).
  3. The orchestrator pipes findings through `score.py` so rendered findings exist only if the script ran, and the now-redundant by-hand scoring prose is removed (CORE-03).
**Plans**: 2 plans (2 waves — script-then-wiring; the wiring edit depends on the script existing and passing tests)
- [x] 16-01-PLAN.md — Build stdlib-only score.py (deterministic core, pure functions) + pinning unittest suite [Wave 1; CORE-01, CORE-02]
- [x] 16-02-PLAN.md — Wire review.md Phase 3/4/4.5 to pipe findings through score.py (un-skippable; remove by-hand scoring prose) [Wave 2; CORE-03]

### Phase 17: Robustness on the Core
**Goal**: The deterministic core is hardened against the prose-can't-enforce failure modes the dogfood exposed — state is single-writer, cross-confirmation can't be gamed by title phrasing, carry-forward persistence isn't mis-tracked by low-entropy hashing, and a machine-checkable "scoring ran" invariant is in place.
**Depends on**: Phase 16 (same surface — the script; verify-not-rebuild for state because the script collapses to a single writer for free)
**Requirements**: ROBUST-01, ROBUST-02, ROBUST-03, ROBUST-04
**Success Criteria** (what must be TRUE):
  1. The Phase 4.5→5 state write is single-writer (verified gone now that scoring lives in the script), so an interruption between git-commit and state-write cannot desync git from state (ROBUST-01).
  2. The cross-confirm matcher uses category-overlap + line proximity (or token-set similarity) instead of two agents sharing a first token, so cross-confirmation can't be gamed by title phrasing (ROBUST-02).
  3. The carry-forward content compare hashes enough surrounding context (or windows) instead of keying on a low-entropy first line, so persistence isn't mis-tracked by collisions (ROBUST-03).
  4. A machine-checkable "scoring ran" invariant is in place, plus detect-and-warn for at least one other prose-unenforceable step where cheap (ROBUST-04).
**Plans**: 3 plans (3 waves — score.py + test_score.py + review.md serialize across ROBUST-02/03/04; the single-writer lock + render gate land last). Revised across TWO Codex adversarial NO-SHIP rounds: R1 closed 3 blockers (asymmetric carry, wildcard over-confirm, too-narrow lock); R2 closed their second-order holes (single-line-snippet churn, order-dependent greedy bridge, SCOPE_HASH false-positive + unfenced-prose evasion).
- [x] 17-01-PLAN.md — Replace the title-substring matcher with ORDER-INDEPENDENT category-domain confirmation + line proximity (pairwise, not greedy first-match; missing/unknown → NON-overlap; adversarial bridges ONLY an unambiguous single co-located native domain — permutation-tested); fix the 3 stale title-substring hints (codex-adversarial.md, framework-fastapi.md, deep-review.md) [Wave 1; ROBUST-02]
- [x] 17-02-PLAN.md — Low-entropy carry-forward compare that widens BOTH sides or NEITHER (never window-vs-single-line; unchanged single-line snippets never churn) using a new orchestrator-resolved canonical_window from HEAD (review.md Phase 3 step 0 ripple); _first_line/canonical_for_hash/stable_hash untouched [Wave 2; ROBUST-03]
- [x] 17-03-PLAN.md — Harden the render gate to a HARD halt (D-08) + CODEX-AWARE parallel-dispatch detect-and-warn (D-09); single-writer regression-lock scanning ALL command prose for scored-field write directives (hasher flagged only when tied to a scored field; SCOPE_HASH exempt; unfenced prose caught) (D-10) [Wave 3; ROBUST-04, ROBUST-01]

### Phase 18: Efficacy Test + Version Bump + Tag
**Goal**: The milestone is proven and shipped — the `--all` dogfood is re-run on vibe-check itself, the previously-found defects are confirmed absent with no regressions, `--all --finalize` now completes (proving DOGFIX-06), and the plugin is versioned and tagged.
**Depends on**: All prior v2.4 phases (13-17)
**Requirements**: CLOSE-01, CLOSE-02
**Success Criteria** (what must be TRUE):
  1. The re-run `--all` dogfood on vibe-check shows the previously-found Critical/Warning defects absent with no new regressions (CLOSE-01).
  2. `--all --finalize` exits cleanly on the dogfood run — empirically proving the DOGFIX-06 state-path fix (CLOSE-01).
  3. `plugin.json` is at 2.4.0 and an annotated tag `v2.4` exists (CLOSE-02).
**Plans**: 1 plan (single wave — strictly sequential tasks: bump → dogfood → tag)
- [ ] 18-01-PLAN.md — Bump plugin.json 2.3.0→2.4.0, run the single authoritative `/vibe-check:deep-review --all` self-dogfood (efficacy proof + `--all --finalize` DOGFIX-06 driver, evidence in RESULTS-v2.4.md), create the annotated un-pushed `v2.4` tag last


> Full per-phase detail for shipped v2.5 (Phases 19-22) lives in the archive:
> `.planning/milestones/v2.5-ROADMAP.md`.


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
