# Milestones

## v2.9 Prove it (Shipped: 2026-07-08)

**Phases completed:** 9 phases, 6 plans, 8 tasks

**Key accomplishments:**

- Wired the `codex` knob live end-to-end: `--codex off|auto|on` now reaches config.py in all 5 review modes via a Phase-0 `$SCOPE_ARGS` normalizer, the BashOutput smoke gate is launch-gated so a non-launching Codex never hard-blocks the native review, and every `/deep-review` run prints exactly one legible Codex-status line — prose/dispatch only, score.py byte-frozen.
- 1. [Rule 2 - Missing critical] Sentinel persists `start_branch`/`start_sha`
- Owner drove `/deep-review` N=3 across all 6 committed test diffs; every run's isolated fresh state (len(passes)==1, head_sha==base_sha) + full-worktree diff (tree.diff.sha256 == kit-build value) is committed at its run boundary — 18/18 scoreable, verified on disk, ready for Wave 3 scoring.
- vibe-check's first-ever aggregate quality numbers — catch-rate 8/9, false-positive-rate 6/9 — scored from 18 owner-driven /deep-review runs against a cryptographically pre-registered answer-key blob, with a D-11 verdict to PROCEED on the FP-driving design challenges.

---

## v2.8 Tunable, quieter reviews (Shipped: 2026-07-01 — early manual close)

**Phases completed:** 30–32 in full + 33 partial (33-01 only), 11 plans; Phase 34 superseded by a
manual close (owner directive "merge everything and push as 2.8"). plugin.json 2.8.0 (`6002cae`),
merge commit `f19be14` on main (real merge — main carried 14 Fable-findings-doc commits), annotated
tag `v2.8`, main+tag+branch pushed and hash-verified. Suite at ship: 356 tests + 221 subtests.

**Delivered (planned scope):**

- **Phase 30 — config surface**: `scripts/config.py`, the never-raise `.vibe-check.toml` reader
  (per-key degrade-to-default + warning, never aborts a review; 1-MiB pre-parse DoS guards);
  precedence CLI flag > toml > default; first consumers `thresholds` (band floors via
  `band_for(score, thresholds)`), `disabled` agent roster (core-agent disable announced),
  `top_model`. Zero-config path byte-identical to v2.7 (GOLDEN_DIGEST frozen).

- **Phase 31 — confidence axis**: `agent_confidence` visible on every rendered finding;
  `min_confidence` (config) / `--min-confidence N` (flag) filter BEFORE scoring with the dropped
  count in the honesty summary ("Below min_confidence" row). Post-ship amendment (Fable A3): the
  valid range is 0–49 — ≥ 50 is refused with a warning, because the pre-scoring filter would
  silently annihilate findings that score into the critical band.

- **Phase 32 — script-enforced noise knobs**: `idiom_floor` band cap (ACTIVE by default at
  `medium`; explicit `off` sentinel distinct from omission) and the reason-aware
  `// vibe-ignore: <reason>` marker (reasoned rides the −50 silenced path; a BARE marker does NOT
  suppress and instead emits one synthetic low "suppression without reason" audit finding).

- **Phase 33 — PARTIAL**: 33-01 shipped the config.py `codex` off/auto/on knob (validated,
  tested). 33-02 (orchestrator wiring: `--codex` flag, always-announce line, fix-loop label —
  LEGIBLE-01/02/03) was plan-approved but never executed → the knob ships validated-but-inert;
  deep-review keeps its v2.2 Codex flow. Deferred.

**Delivered (unplanned scope — the Fable second-model review remediation, buckets 1–3 of
`docs/design/FABLE-REVIEW-FINDINGS.md`):**

- Scorer fixes: absorbed dedup losers recorded in `filtered[]` as `absorbed-into: <hash>` (A2,
  + render rows); deterministic equal-score tie-break by stable_hash (A4); agent-forged
  `status:"persisted"` scrubbed at ingress (A5, security); residual malformed-input crash guards
  — non-hashable severity, lone surrogates via `surrogatepass`, string range endpoints (A6/F9);
  non-finite floats sanitized to null + `allow_nan=False` backstop (A11); case-insensitive
  silenced markers incl. `//nolint`/`#noqa` (A13); `intent-doc-match` drop reason (F8); honest
  out-of-diff docs (A12).

- `scripts/guard.py` + 22 tests: the ONE fail-closed, missing-path-tolerant path-containment
  check, replacing ≥5 drifted inline copies (four failed OPEN on empty `$ROOT` — including the
  copy guarding fix.md's auto-committing path; the realpath variants silently downgraded Codex
  findings about deleted files). All sites in review.md / deep-review.md / fix.md /
  codex-adversarial.md rewired (A7/B2, A10/B3).

- State-key branch slug (A9): slashed branch names no longer break the flat-filename disjointness
  proof or silently restart carry-forward.

- Gen-2 calibration retrofit on the 9 gen-1 agents (A1): off-hunk confidence ceilings +
  `pending:` notes, per-check severity tags, SAFE never-flag lists, confidence anchors — onto
  bugs (+ `logic-error` home, race-condition FP guard), architecture (testable gates, severity
  caps), compliance (+20-amplifier calibration, qualified-rule discipline), impact (notes must
  also emit findings), framework-react, and the 4 language agents (go's two deterministic FPs
  deleted/version-gated, A14; angular's :37 contradiction fixed, A15). No new checks; no scorer
  or `CATEGORY_DOMAIN` changes.

**Known deferred (recorded in STATE.md):** 33-02 wiring (⚠ needs rebase — the Fable work edited
the same review.md regions); Phase-34 planted-fixture smoke proofs + per-phase deep-review gates
(Phase 33's deep review never ran); Fable answer-key fixes (A8/A16), security.md critique pass,
B3 harness execution, design challenges, twin proposals.

---

## v2.7 Framework coverage (Shipped: 2026-06-30)

**Phases completed:** 12 phases, 7 plans, 13 tasks

**Key accomplishments:**

- Task 1 — `agents/framework-express.md` (new, 146 lines).
- framework-vue reviewer (sonnet) catching Vue 3 Composition-API defects across five categories — reactivity / composition-api / lifecycle-cleanup / template / props — with the Vue 3.5 defineProps-destructure false positive guarded out, wired across all six touchpoints plus .vue language routing, locked by a no-twin regression test (suite green at 144).
- framework-angular reviewer (sonnet) catching Angular defects across five categories — rxjs-leaks / change-detection / di-scope / lifecycle / rxjs-composition — with the modern-idiom false positive (takeUntilDestroyed/takeUntil(destroy$)/async-pipe/self-completing-sources/signals) guarded out, wired across all six touchpoints, locked by a no-twin regression test (suite green at 145).
- Security-weighted Electron reviewer agent (six CVE-class categories, renderer-XSS → Node-RCE framing) wired across six touchpoints, including the v2.7 milestone's FIRST real score.py twin (`ipc-validation` → `security`) with a broad-blast-radius cross-confirm regression test.
- RN-native reviewer (six categories, four FP-guards) dispatched DISTINCTLY from web React via a dual-emit triage rule, with the list-perf->impact twin closing WIRE-02 at the full 12-agent fleet — the LAST framework agent in v2.7.
- Proved all five v2.7 framework agents (Express, Vue, Angular, Electron, React Native) fire on their framework, catch a planted defect in an owned category, and stay silent on a no-framework diff — via seven separate scoped runs recorded in RESULTS-v2.7.md (written, UNSIGNED).
- Plan:

---

## v2.5 Sharper, more legible reviews (Shipped: 2026-06-28)

**Phases completed:** 13 phases, 8 plans, 35 tasks

**Key accomplishments:**

- Fixed the copy-paste-broken abandon/resume hint and the `--all --finalize` wrong-state-file bug in `commands/review.md`, and verified the untrusted `PRIOR_PHASE`→`mv` allowlist guard survived — restoring a working resume command and unblocking whole-codebase finalize (the exact defect that forced Phase 12 to skip `--finalize`).
- Deleted the orphaned second scoring contract (with its phantom "High" band) from false-positive-rules.md and pointed it at scoring.md, then reconciled architecture.md by fixing the forbidden "Opus + thinking"/path contradictions and de-pinning its drift-prone version and cost figures.
- deep-review.md now cites review.md by stable section name (Selection table / `--all` per-chunk dispatch loop / branch-flip guard) instead of drifting line numbers, and Codex `title` gets a sanitize-and-KEEP pass (fences/backticks/newlines/control chars neutralized, finding kept, `=` permitted) specified in the codex-adversarial.md contract and mirrored at the Phase 3 translation step.
- Stdlib-only `score.py` (json/hashlib/re/sys) extracts the orchestrator's by-hand scoring into a pure-function stdin->JSON/stdout->JSON batch filter, pinned by the plugin's first test suite (66 unittest cases incl. a frozen golden sha256, an AST import-set guard, and a fail-closed malformed-stdin case).
- review.md Phase 3 now pipes findings through `score.py` once per pass with dev-safe path resolution (working-tree first) and a fail-closed gate that HALTS the review on any scorer error; the five by-hand scoring decision blocks are deleted, Phase 4 asserts a scored_by_script + per-finding band render gate, and Phase 4.5 consumes the script's stable_hash — scoring is now structurally un-skippable, with zero deep-review.md edits.
- Replaced the gameable title-substring +10 matcher in `score.py` with an ORDER-INDEPENDENT category-domain confirmation (union-find native absorption components + an ambiguity-safe adversarial single-domain bridge), and corrected the three prose files that still coached the dead title-substring game.
- Hardened the carry-forward content key in `score.py` (ROBUST-03) so a low-entropy first line (`}`, `);`) is disambiguated by surrounding context WITHOUT ever churning an unchanged finding — the compare now widens BOTH sides to a >=2-line window or DEGRADES to the first-line compare, never a window-vs-single-line asymmetry; the frozen `stable_hash` golden is unmoved (D-07).
- Hardened the "scoring ran" invariant into an unhedged HARD render gate in `review.md` (absent `scored_by_script` ⇒ HALT, no report — ROBUST-04 D-08), added a codex-aware parallel-dispatch detect-and-WARN that never misfires on a normal Codex deep-review (D-09), and added an all-prose single-writer regression-lock to `test_score.py` that is both sound (no SCOPE_HASH false positive) and complete (catches an unfenced prose writer) — ROBUST-01 D-10. `score.py` is untouched; the suite is 109 → 119, all green.
- skip-rules.md gains a conservative docs/planning denylist category and a path-segment code-.md allowlist override (agents/commands/templates/skills) that WINS over the denylist, so a default `--all` excludes planning/docs locations while keeping vibe-check's own instructional `.md` source.
- `commands/review.md` Phase 0 now APPLIES Plan 19-01's docs/planning denylist + code-.md allowlist via an `$INCLUDE_DOCS`-branched mode-5 step d (default `--all` reviews source not docs; `--include-docs` restores the whole tree and the run reports "docs/planning" as a skip reason), accepts a bare `all` as `--all` silently, and concludes with one clean `Mode: …` line — all `$ALL_MODE`-only, with the four diff handlers and the `$NARROW` guard byte-stable, and `/deep-review --all` inheriting everything by delegation (verified, not duplicated).
- Five stdlib-only defensive guards on `score.py` so a single malformed agent finding can no longer hard-crash a review run: a `_valid_finding` non-dict container guard + ingress filter, a `_safe_window` string-element coercion (C3 + HOLE 1), an import-free non-finite `agent_confidence` guard (HOLE 2), and an envelope fail-closed list-guard (C4/C5/C6, D-02) — all 123 existing tests stay green, formula/banding/thresholds/golden-digest untouched.
- The T1-T21 malformed-shape regression suite that LOCKS the Wave-1 score.py crash guards plus the three v2.4-dogfood hygiene fixes (subprocess timeouts, single GOLDEN_DIGEST constant, tightened loose assertions) — every dogfood-named crash class and the two adversarial-found holes now have an explicit case asserting the post-hardening OUTCOME (skip+report / kept-and-degraded / fail-closed / valid-empty), not merely "did not raise"; the full suite is 140 tests green (123 prior + 17 new), score.py untouched, the golden digest frozen value preserved.
- New deep-review-only `test-sufficiency` agent that judges test adequacy by consuming an orchestrator-injected `<coverage-artifacts>` block — risk-weighting gaps by file role, surfacing branch-coverage weakness in plain language, and skipping-and-noting cleanly when no coverage data exists.
- Wires the Plan 21-01 test-sufficiency agent into `/deep-review`: a Phase 1d coverage-artifact discovery pre-step (two-stage repo-level gate + per-chunk assembly) that injects a gated `<coverage-artifacts>` block into the agent's prompt only, the dispatch-roster rows (deep-only), a budget-gate update counting the new always-on opus agent, and a surgical impact.md carve-out so the two agents don't double-report.

---

## v2.4 Dogfood-driven hardening (Shipped: 2026-06-26)

**Phases completed:** 12 phases, 12 plans, 22 tasks

**Key accomplishments:**

- Neutralized the fix loop's Step A apply-choice menu in `/review` (and `/deep-review` by delegation) — stripped the "(Recommended)" marker from "Apply all findings" and removed the prose note that framed apply-all as the user's preferred workflow, so a developer choosing how to apply review findings is no longer nudged toward blind autonomous bulk-commit.
- Fixed the copy-paste-broken abandon/resume hint and the `--all --finalize` wrong-state-file bug in `commands/review.md`, and verified the untrusted `PRIOR_PHASE`→`mv` allowlist guard survived — restoring a working resume command and unblocking whole-codebase finalize (the exact defect that forced Phase 12 to skip `--finalize`).
- Deleted the orphaned second scoring contract (with its phantom "High" band) from false-positive-rules.md and pointed it at scoring.md, then reconciled architecture.md by fixing the forbidden "Opus + thinking"/path contradictions and de-pinning its drift-prone version and cost figures.
- deep-review.md now cites review.md by stable section name (Selection table / `--all` per-chunk dispatch loop / branch-flip guard) instead of drifting line numbers, and Codex `title` gets a sanitize-and-KEEP pass (fences/backticks/newlines/control chars neutralized, finding kept, `=` permitted) specified in the codex-adversarial.md contract and mirrored at the Phase 3 translation step.
- Replaced the bare triple-backtick fence around the attacker-influenceable `{{current_code}}` snippet with a render-time CommonMark longest-run-aware fence-sizing rule (`max(3, N+1)` backticks), so an embedded ``` run can no longer close the report fence early and spoof the report.
- Stdlib-only `score.py` (json/hashlib/re/sys) extracts the orchestrator's by-hand scoring into a pure-function stdin->JSON/stdout->JSON batch filter, pinned by the plugin's first test suite (66 unittest cases incl. a frozen golden sha256, an AST import-set guard, and a fail-closed malformed-stdin case).
- review.md Phase 3 now pipes findings through `score.py` once per pass with dev-safe path resolution (working-tree first) and a fail-closed gate that HALTS the review on any scorer error; the five by-hand scoring decision blocks are deleted, Phase 4 asserts a scored_by_script + per-finding band render gate, and Phase 4.5 consumes the script's stable_hash — scoring is now structurally un-skippable, with zero deep-review.md edits.
- Replaced the gameable title-substring +10 matcher in `score.py` with an ORDER-INDEPENDENT category-domain confirmation (union-find native absorption components + an ambiguity-safe adversarial single-domain bridge), and corrected the three prose files that still coached the dead title-substring game.
- Hardened the carry-forward content key in `score.py` (ROBUST-03) so a low-entropy first line (`}`, `);`) is disambiguated by surrounding context WITHOUT ever churning an unchanged finding — the compare now widens BOTH sides to a >=2-line window or DEGRADES to the first-line compare, never a window-vs-single-line asymmetry; the frozen `stable_hash` golden is unmoved (D-07).
- Hardened the "scoring ran" invariant into an unhedged HARD render gate in `review.md` (absent `scored_by_script` ⇒ HALT, no report — ROBUST-04 D-08), added a codex-aware parallel-dispatch detect-and-WARN that never misfires on a normal Codex deep-review (D-09), and added an all-prose single-writer regression-lock to `test_score.py` that is both sound (no SCOPE_HASH false positive) and complete (catches an unfenced prose writer) — ROBUST-01 D-10. `score.py` is untouched; the suite is 109 → 119, all green.
- Outcome: v2.4 "Dogfood-driven hardening" is PROVEN, VERSIONED, and TAGGED (locally).

---

## v2.3 Whole-codebase review mode (Shipped: 2026-06-22)

**Phases completed:** 12 phases, 13 plans, 16 tasks

**Key accomplishments:**

- Task 1 (commit f3c1f42) — Phase-0 mode 5 + Phase-0.5 state branch + Phase-1 triage note:
- `/vibe-check:deep-review --all` is now recognized — selection inherited from review.md Phase-0 mode 5 via the existing delegation — and deep-review's own Phase-2.5 architecture prompt swaps `<diff>`→`<files>` under `$ALL_MODE`, completing SELECT-01 on both commands and extending REVIEW-01 to deep mode's architecture agent.
- A deterministic `--all`-gated risk-scoring + chunk-packing step that ranks `$REVIEW_SET` by path-tier (primary) and churn (within-tier), then greedily packs files into 1800-line budget chunks (riskiest seed first, same-directory neighbors filled before spill, over-budget file = own chunk), emitting the `$CHUNK_PLAN` contract with per-file and per-chunk line totals.
- Converted review.md's `--all` interior from a single whole-set dispatch into a sequential per-chunk loop over `$CHUNK_PLAN`: per-chunk triage on `$CHUNK_FILES_i` (Site B), a per-chunk one-turn fan-out building `$FILES_BLOCK_i` and binding BOTH prompt halves to chunk `i` (Site C / Site C-bind), responses accumulating into `$AGENT_RESPONSES`, and Phase 3 running EXACTLY ONCE after the loop — with `$ALL_MODE` overrides adjacent to BOTH legacy Phase-3 hand-offs so neither is reachable per-chunk.
- Closed out Phase 8's two propagation edits: Site D generalized review.md's `--all` reviewed-partial coverage note from "reviewed as a single unit" to the per-chunk oversized-single-file case, triggered DETERMINISTICALLY off `$CHUNK_PLAN`'s recorded per-chunk LINE total (not triage's `size_tier`); Site E EDITED deep-review.md's Phase-2 contract so `/deep-review --all` EXECUTES review.md's per-chunk loop with deep's agent table (architecture+impact per chunk), retiring the old single-unit Differences-table dispatch — with the Codex blocks byte-unchanged.
- `--all` audit output correctness: an `$ALL_MODE` `in_reviewed_set` finding-validity gate, a RENDER-ONLY cross-file dedup display grouping, a C+W/`--full` listing bar, and the P10-C coverage arithmetic fix — all confined to the `$ALL_MODE` branch so the diff path stays byte-stable.
- `/deep-review --all` now fail-closed skips Codex with a named `whole-repo-non-representable` arm (REVIEW-04), and two new Phase-10 notes confirm that 10-01's review.md `in_reviewed_set` / RENDER-ONLY cross-file dedup / listing-bar edits reach `/deep-review --all` by delegation with the deep ≥70 threshold left untouched.
- `--all` is now REPORT-FIRST — a plain `--all` renders the audit, persists state, and stops with a discoverable next-step line (no auto "apply all?" prompt); `--all --fix` is the deliberate opt-in into the existing, unchanged Phase-5 fix loop — implemented as four additive, `$ALL_MODE`-guarded edits to `review.md` with the diff path byte-stable.
- Date:

---

## v2.2 Codex adversarial reviewer (Shipped: 2026-06-21)

**Phases completed:** 3 phases (4-6), 6 plans, 24 commits (v2.1..v2.2)

**Delivered:** Codex (GPT-5-codex) as a second, independent adversarial reviewer in `/deep-review`, with its findings flowing through vibe-check's existing merge/dedup/score/cross-confirm pipeline like a native reviewer. Additive and prompt-only.

**Key accomplishments:**

- **Phase 4** — `agents/codex-adversarial.md`: the Codex→vibe-check translation contract (verdict rule, full field map, `agent_notes` carry, untrusted-data posture, path trust-boundary, fallback policy, worked example). The spec-of-record everything else points at.
- **Phase 5** — `commands/deep-review.md` orchestrator Codex step: `setup --json` probe (gated on `.ready`), versioned-cache plugin-path resolution, one disclosure line, exact-or-skip diff targeting, self-contained 300s `timeout` watchdog, `run_in_background` launch + `BashOutput` collection, translate + join at Phase 3 entry (cross-confirm +10), graceful skip-and-note degradation. `agents/index.md` selection-matrix row. MERGE-01 four-files-unchanged guard (review.md, scoring.md, agent-output-schema.md, triage.md byte-unchanged).
- **Phase 6** — live efficacy proof in this Codex-authenticated repo (planted SQLi + null-deref on a throwaway branch): Codex ran + attributed (EFF-01); **2 findings cross-confirmed +10 dual-attribution** (EFF-02a); de-authenticated run completed with the skip-and-note line (EFF-02b); owner sign-off recorded. Closed the carried-over T-05-09 BashOutput viability gate from the main session.
- **plugin.json bumped 2.1.0 → 2.2.0**; annotated tag `v2.2`. marketplace.json untouched.

**Process note:** Phase 6's plan went through 3 Codex adversarial-review rewrite passes that hardened the release/auth gates (recovery-first auth restore, structured cross-confirm evidence gate, tag-bound-to-commit verification). The residual critical (gitignored `.planning/` approval state can't be cryptographically bound to the tag) is covered by the live in-session human sign-off checkpoint.

**Known deferred:** ASYNC-01/02/03 (background folding, Codex in /review, configurable model/effort) → future milestone. Framework review agents (Express/Vue/Angular/Electron/React-Native) → Phase 999.1 backlog.

---

## v2.1 FastAPI review agent (Shipped: 2026-06-18)

**Phases completed:** 4 phases, 3 plans, 7 tasks

**Key accomplishments:**

- Authored `framework-fastapi.md` — an 11-category FastAPI reviewer prompt with co-located false-positive gates, a tight FastAPI-mechanism-only lane (generic IDOR/path-traversal deferred to security), and per-check severity calibrated to the orchestrator's scorer math.
- One-liner:

---
