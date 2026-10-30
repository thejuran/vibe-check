# vibe-check

## What This Is

A Claude Code plugin for AI-powered code review of uncommitted changes. It runs
specialized per-domain reviewer agents (bugs, security, architecture, impact,
compliance, language- and framework-specific) in parallel, scores and filters their
findings, and surfaces only what's worth attention *in the diff* — not pre-existing tech
debt. It is GSD-aware (reads phase intent docs to judge implementation-vs-intent) and
falls back to plain git-diff review with zero setup. Adapted from the upstream
`turingmindai/turingmind-code-review`; published as `vibe-check@thejuran`.

## Core Value

Catch real defects in a developer's changes before they ship — with high coverage and
low noise — so a reviewer who can't manually audit the code can trust the agent's output
as their safety net.

## Current Milestone: v2.14 Decision reliability

**Goal:** Close stale-decision escape paths, preserve deferred obligations, and make Finalize dependable — without changing reviewer coverage or scoring policy.

**Target features:**
- Stale decisions and lost deferrals (999.23): reproduce CR-01, CR-02, CR-04 and the `min_confidence=45` deferred-member loss through the real score → carry → card → finalize chain; reopen with the correct reason when evidence changes, keep unchanged decisions stable; SA-02 reproduced once or recorded and dropped. One bounded implementation/review cycle, then record residuals and re-scope.
- Exact change evidence and reliable Finalize (999.24, 999.25): nearby/in-diff ranges from actual additions/deletions, not display context; Finalize's blob-file path survives fresh Bash calls via the printed-path convention.
- Release gate: targeted real-chain regressions, full offline suite, archived replay (only named reopen/retention differences allowed), mode/recovery checks; live checks only under a separately approved bounded proposal, else documented gap + waiver. Ships independently.

**Progress:** Phase 59 complete (2026-10-29) — CR-01, CR-01 multi-pass, CR-02, CR-04 and the `min_confidence=45` deferral loss fixed with red-before/green-after real-chain fixtures; SA-02 did not reproduce (dropped, pinned). Card-wording residuals WR-01/WR-02 owner-parked to 999.23. Next: Phase 60.

**Out of scope:** cost reporting, orchestration extraction, reviewer/model changes, scoring changes, 999.26. Lean orchestration (999.12 + Finalize extraction) follows; Reviewer efficiency stays conditional. Full scope: [Roadmap](ROADMAP.md).

**Codex integration (owner, 2026-10-28):** Keep the existing optional OpenAI Codex plugin/companion and the user's configured Codex default. No bundled replacement, direct adapter or model-gateway routing is planned. Dependency/setup, run/skip and model-label clarity, plus bounded companion-update compatibility checks, belong to [maintenance](backlog/MAINTENANCE.md#codex-dependency-setup-and-model-disclosure), outside v2.14 and without expanding its requirements or release gates.

## Last Milestone: v2.13 Reliable fix closure and recovery (SHIPPED 2026-10-28 as 2.13.0)

**Goal (met, with owner-accepted known limits):** Let independently verified fixes close reliably, preserve owner decisions, and make recovery from an inconclusive check understandable. 14/14 requirements (VFIX-01..06, DECN-01..03, RECV-01..02, ANSR-01..03); audit tech_debt; suite 3588/0. Not B3-measured. Known limits: 999.23 (wrong-keep shapes, D-19 hard stop), 999.24 (diff context), 999.25 ($BLOBFILE), 999.26 (wordier title references); live ref extraction unverified (D-15). Archive: `.planning/milestones/v2.13-ROADMAP.md`.

## Earlier Milestone: v2.12 Quiet without hiding (SHIPPED 2026-10-17 as 2.12.0 — UNMET, measurement incomplete; owner waiver)

**Goal:** Fewer bogus findings without losing real catches or breaking the accepted-fix workflow. Closes v2.11's false-alarm miss (5/18 vs ≤3/18) with an independent sealed holdout, not by re-tuning on B3 alone.

**Target features:**
- Sealed 6-case holdout (3 should-catch, 3 should-quiet) outside the repo, hashes committed, access split by role
- Hardening: 999.21 fix-agent edges, guard over-blocking of read-only `cd`/`grep`/`sed -n`, `--finalize` whole-token match, first-run card misfire
- Accepted-fix end-to-end harness: 16 preservation runs (with sentinels) + 2 clean-tree runs, default-diff and GSD modes
- False-alarm reduction: three-outcome reachability replaces Rule 2; evidence-based conditional suppression; "Needs verification" group that counts as an alarm
- Freeze by artifact identity (manifest), release gates + integration audit before measurement
- Measure (B3 ×3, holdout ×3 per case, accepted-fix runs), record MET/UNMET separately from shipping, publish 2.12.0

Design spec: `docs/superpowers/specs/2026-10-08-quiet-without-hiding-v2.12-design.md` (local, gitignored). Supersedes the v2.12 sketch in `milestones/v2.11-REQUIREMENTS.md`.

**Progress:** Phase 51 complete (2026-10-09): six-case holdout sealed (`SEAL.json` committed alone, a23e325; seal-order OK), HOLD-01..04 validated. Owner rule locked during the real run: a case's own source code outside tuning-side places is not a leak (all six slots cleared, none replaced). Phase 52 complete (2026-10-10; review gates closed 2026-10-12): hardening + accepted-fix harness, HARD/FLOW validated. Phase 53 complete (2026-10-15): three-outcome reachability replaces Rule 2, evidence-based suppression, never-filtered Needs-verification group that blocks finalize and counts as an alarm, per-member second-opinion (owner-approved severity correction with disclosed same-line-proxy limitation), Phase-53 state at `.turingmind/state/format-53/`; QUIET-01..09 validated; dev rehearsal on fingerprint 5bee4c11… signed off (7/7 catches; should-quiet-4 recorded residual, no exemption). Phase 54 subsequently closed under the owner-approved reduced scope; Phase 55 measurement remains deferred. See the archived v2.12 roadmap for the final release record.

## Earlier Milestone: v2.11 Quiet loop (SHIPPED 2026-10-08 as 2.11.0 + 2.11.1)

**Goal (met, except the false-alarm bar):** A deep-review pass costs the owner one decision card, a finding is asked about once, and a lane that has nothing to read does not run. Catch rate held at 15/15. False alarms came in at 5/18 against a bar of ≤3/18, a MISS the owner accepted.

Delivered in Phases 45–50: lane gating on evidence; carry-forward integrity (no expiry, evidence-bound decisions); one card per fix-loop pass and one at finalize; fix-agent verify-before-commit with hunk-isolated commits; read-only git for detection agents; B3 measurement and the 2.11.0 release; and the Phase-50 gap closure (Close out and `--finalize` reach Finalize in every mode), shipped as 2.11.1. Archive: `.planning/milestones/v2.11-ROADMAP.md`.

## Earlier Milestone: v2.10 Opus 5 rebuild + quiet down (SHIPPED 2026-10-01 as 2.10.0)

**Goal:** Adapt vibe-check to the Opus 5 / Claude 5 model generation (measured baseline, prose
diet, measured cost), then cut the measured false-alarm rate (6/9) while holding the catch-rate
(8/9) on the re-baselined system — proven on a grown pre-registered ground-truth test set.

**Target features (sequenced — the order is the point):**
- **Grown B3 set + Claude-5 baseline** — 6 → 10–12 committed organic diffs (sealed answer keys,
  provenance sidecars, weighted toward the measured weak spot: clean diffs touching security/
  networking-sensitive code), baselined ×3 on the UNCHANGED v2.9.0 plugin running on the
  current Claude 5 harness — the baseline doubles as the Opus 5 re-measure. Pass bar
  pre-registered before any change: FP ≤ half baseline AND catch no worse.
- **Compatibility touch-up + measured cost (999.12 promoted)** — README model/config docs
  refreshed for the Claude 5 generation (opus/fable allowlist kept); static cost guesses
  ($2–5 brackets) replaced by measured per-pass cost reporting (output-only).
- **Prose diet** — restructure `commands/review.md` (~80K tokens) + `commands/deep-review.md`
  (~35K): cut the anti-improvisation scar tissue Opus 5's instruction adherence makes
  redundant, progressive-disclosure structure, extract remaining deterministic prose to tested
  scripts per `docs/design/prose-to-code-inventory.md`; folds in 999.8's single-writer
  verification. Guardrail: catch no worse than baseline on a B3 spot-check per cut batch.
- **Wave 1 — scorer-side noise interventions** (the formula freeze lifts, Wave-1-scoped):
  B-SEV severity-label stability, B-REWEIGHT per-agent confidence calibration, H-LANE pile-on
  collapse + correlated-agreement discount. Tuned offline by replaying run data AGAINST THE
  POST-DIET SYSTEM; zero-catch-regression guardrail; live spot-check before Wave 2.
- **Wave 2 — agent-side noise interventions** (H-CORE): safe-change recognition + confidence
  ceilings on the loud lanes (bugs, security, impact, codex contract); prompt-only.
- **Prove** — full grown set re-run (~30–36 owner runs) scored against sealed keys; bar
  evaluated honestly; at most ONE retune (failed diffs only); `RESULTS-v2.10.md`.
- **Close** — `plugin.json` → 2.10.0, annotated tag `v2.10`, README efficacy + cost numbers
  replaced, atomic hash-verified publish.

**Key context:** Re-scope (2026-07-27) of the seeded-but-unstarted v2.10 "Quiet down" —
merged with the Opus 5 adaptation plan by owner decision, so the noise-wave tuning investment
lands on the system that will actually ship (restructure-then-tune, never tune-then-
restructure). Phase numbering continues at 38. Release milestone; measurement is
owner-runtime. Measurement machinery identical to v2.9 (pre-registration, score-from-blob,
state isolation, cache-parity pre-flight). Honest tune-vs-measure-overlap caveat carried into
results + README. Backlog effects: 999.12 promoted in, 999.8 absorbed, 999.13 re-sequenced
after this milestone; gitleaks (999.2), SARIF (999.3), PR-posting (999.5) unchanged/deferred.
Original noise design spec: `docs/superpowers/specs/2026-07-08-quiet-down-v2.10-design.md`.

## Current State: v2.13 shipped (2026-10-28)

**v2.13 shipped as plugin 2.13.0** (tag `v2.13`; one squash PR per phase into main, then a release PR). Reliable fix closure and recovery: an independent re-check closes a fixed finding on a later run with no dummy edit or repeated confirmation (the six-row case incl. Codex-origin and tests-only fixes closes with no dismissal); owner defer/dismiss decisions survive regrouping and unrelated edits and reopen on changed evidence; "Fix all" names what it skips; inconclusive re-checks print per-reason recovery steps; clear plain-English card answers are acted on. Not B3-measured — v2.11 (5/18 · 15/15, MISS) remains the last measured result. Known limits in backlog 999.23–999.26. Current milestone: v2.14 Decision reliability (Phases 59–61); Lean orchestration follows; Reviewer efficiency conditional.

### Earlier: v2.12 shipped (2026-10-17)

**v2.12 shipped as plugin 2.12.0** (annotated tag `v2.12` → `a4b0c3f`; main fast-forwarded; one atomic push of main, the tag and feat/v2.12, verified on the remote). **Outcome: UNMET — measurement incomplete; shipped under owner waiver.** The noise target (B3 ≤3/18 · 15/15) was not demonstrated — the release measurement campaign was not completed (owner credit-budget decision 2026-10-17); v2.11 (5/18 · 15/15, MISS) remains the last measured result. What shipped is a reliability release: three-outcome reachability replaces the helper-gap rule, a never-filtered Needs-verification group blocks Finalize until decided, fix-loop/Finalize hardening, and format-53 state preservation with no-overwrite migration and archives. The 21-file post-review delta was independently reviewed; three follow-up fixes (88ed70e) were locally tested and replay-checked without independent re-review. Deferred: the measurement campaign, the one-pass confirmed-fix re-check behavior, the "Fix all" label. Next milestone: not scoped.

### Earlier: v2.11 shipped (2026-10-08)

**v2.11 shipped as plugin 2.11.0** (tag `v2.11` → `2a420db`), **then 2.11.1** (tag `v2.11.1` → `44c7cbf`). Each went out as one atomic, exact-hash-verified push of main, the tag and feat/v2.11, after the test, security and deep-review gates passed on the release commit. B3 first pass: false alarms 5/18 (bar ≤3/18, MISS), catches 15/15. The owner shipped as measured, and both releases are disclosed as not B3-measured (11c8afc; the three Phase-50 commits). The milestone audit caught Close out and `--finalize` broken in phase and plain mode, which shipped undisclosed in 2.11.0. Phase 50 fixed it, 2.11.1 discloses it, and the re-audit came back tech_debt with no blockers. Installed plugin: 2.11.1, with 147/147 files matching the release.

### Earlier: v2.10 shipped (2026-10-01)

**v2.10 shipped as plugin 2.10.0** (tag `v2.10` → `edc450e`; main + tag + feat/v2.9 atomic push, exact-hash verified). Untuned measurement MISS on the pre-registered bar (false alarms 6/18, catches 13/15); one prompts-only retune → combined PASS 3/18 · 15/15, flagged in README and RESULTS as tuned on the same set. README discloses the measured setup (Fable 5.1, 1M context, Codex on), the 999.20 stash-pop issue and the Rule-2 helper-bypass tradeoff. Audit: 21/21 requirements, tech_debt (5 items). Next: `/bm:new-milestone`; start it on its own branch (v2.10 ran on feat/v2.9).

### Earlier: v2.9 shipped (Prove it)

**Phase 38 complete (2026-09-08) — Grow the B3 set + Claude-5 baseline.** The v2.10 anchor is
measured: 12 sealed organic diffs, 36/36 baseline runs on the unchanged 2.9.0 plugin under one
pinned Claude 5 harness tuple, scored from archived state against the sealed key blobs — catch
15/15, FP 19/21 (carried-6: catch 8/9→9/9, FP 6/9→9/9; the noise result got WORSE on identical
diffs/key/plugin, so the harness is the variable). Pass bar pre-registered and sealed; not
evaluated until Phase 43. Next: Phase 40 prose diet (Phase 39 dissolved). Live artifacts:
`docs/design/b3-ground-truth/SCORING-v2.10.md`, `plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md`.

**Phase 40 complete (2026-09-28) — Prose diet, restructure for Opus 5.** 14/14 plans; VERIFICATION passed
6/6 (DIET-01..04, TRUST-01/02). `commands/review.md` 189,625 → 16,005 bytes as a spine over lazy-loaded
`phases/**/*.md`; plain-review path footprint −41.67% (soft target 40%), deep −36.5%, finalize −66.2%,
`--all` +7.0% (disclosed); nine deterministic families extracted to tested scripts (suite 356 → 990);
DIET-03 dissolved (single writer `45-persist.md`); helpers resolve from the trusted plugin root only.
Owner evidence: 12 capped B3 runs — batches 1–3 PASS, final ×3 secret-in-logs 3/3 catch (= Phase-38
triplet, DIET-04 met), should-quiet-5 0/3 FP (informational). Deferred, recorded in the phase's
deferred-items: the Codex launch gate names a `BashOutput` tool absent in Claude Code 2.1.281 (Codex
runs only when the session improvises — fix before Phase 43); `agents/*.md` name the schema template
relatively; measurement sessions must run with the clone projects' auto-memory parked (runbook N-02).

**Phase 41 complete (2026-09-30) — Wave 1, scorer-side noise interventions.** 8/8 plans; VERIFICATION
passed (SCORER-01..05). Offline replay harness + zero-catch-regression guardrail landed before any
scorer change; B-SEV (lone-lane band ceiling), B-REWEIGHT (derived per-agent confidence offsets) and
H-LANE (proximity pile-on collapse) landed as three separately revertible commits; combined replay FP
runs 16/18 → 14/18 with no catch regressed. Live spot-check (6 assistant-driven owner runs on snapshot
batch4-cd8f5b00de73): 3/6 runs fired vs predicted 5 → PASS (D-11); should-quiet-3 went fully quiet
(0/3). Five runs' state files lacked root `medium_acknowledgments` — waived by owner in
SUPERSESSIONS-v2.10 entry 009; the persist prose now creates the full root on a new state file
(Phase 43 needs a snapshot built after that fix). Validated in Phase 41: Wave 1 — scorer-side noise
interventions. Next: Phase 42 (Wave 2 — agent-side noise interventions).


**Shipped 2026-07-08 (plugin v2.9.0, annotated tag `v2.9` on `17950c0`, main+tag+branch pushed
and exact-hash verified; docs fix-forward `8c0e8ca` on main).** v2.9 "Prove it" finished v2.8's
shipped surface and produced vibe-check's FIRST measured quality numbers. Delivered: the live
`--codex off|auto|on` / `[noise] codex` control (LEGIBLE-01/02/03) with every deferred v2.8 knob
smoke-proven (PROOF-01/02, RESULTS-v2.9.md); the committed, cryptographically pre-registered B3
organic ground-truth kit (6 diffs, reusable milestone-over-milestone); 18 owner-driven
`/deep-review` runs scored against the frozen key blob — **catch-rate 8/9, false-positive-rate
6/9** (exact fractions, honest small-N limitations); and the close (2.9.0, tag, atomic publish,
README measured-efficacy pointer). D-11 verdict: PROCEED on the FP/axis-stability scorer
challenges (H-CORE/H-LANE/B-SEV/B-REWEIGHT) at next-milestone scoping. Milestone audit 9/9.

**Validated this milestone (v2.9):** LEGIBLE-01/02/03, PROOF-01/02 (Phase 35); B3-01/02/03
(Phase 36); CLOSE-01 (Phase 37).

<details>
<summary>Previous: v2.8 shipped 2026-07-01</summary>

**Shipped 2026-07-01 (plugin v2.8.0 on bump `6002cae`, annotated tag `v2.8` on merge commit
`f19be14`, main+tag+branch pushed to `origin` and hash-verified).** v2.8 "Tunable, quieter
reviews" shipped via an EARLY MANUAL CLOSE (owner directive) — Phases 30–32 in full, Phase 33
partial (33-01 config.py `codex` knob only; the 33-02 orchestrator wiring is deferred, so the
knob is validated-but-inert), Phase 34 superseded (bump/tag/publish done manually; the
planted-fixture smoke proofs and per-phase deep-review gates were not run). Delivered: the
`.vibe-check.toml` config surface (`thresholds`/`disabled`/`top_model`), the confidence axis
(`min_confidence` 0–49 + `--min-confidence`, visible `agent_confidence`, honesty-summary counts),
the script-enforced noise knobs (`idiom_floor` cap, reason-aware `// vibe-ignore`), PLUS the
unplanned Fable second-model review remediation: scorer bug fixes (absorb-visibility,
deterministic tie-break, status-forgery scrub, crash guards, strict-JSON output), the
`min_confidence ≥ 50` critical-annihilation refusal (A3), `scripts/guard.py` replacing five
drifted inline path-containment copies, and the gen-2 calibration retrofit across the 9 gen-1
agents. Suite 356 tests + 221 subtests. Deferred: 33-02 (LEGIBLE-01/02/03, ⚠ needs rebase),
Phase-34 efficacy proofs, Fable answer-key/security.md/B3/design-challenge items — see
`.planning/STATE.md` Deferred Items and `.planning/MILESTONES.md`.

</details>

<details>
<summary>Previous: v2.7 shipped 2026-06-30</summary>

**Shipped 2026-06-30 (plugin v2.7.0, annotated tag `v2.7` on bump commit `3501545`, pushed to `origin/main`).**
v2.7 "Framework coverage" added FIVE framework reviewer agents — `framework-express`, `framework-vue`,
`framework-angular`, `framework-electron` (security-weighted), `framework-react-native` — each authored
to the proven `framework-react.md` pattern and wired across six touchpoints (triage detection, both
dispatch tables, `index.md` matrix row, the agent-count prose, and `score.py` twins where a genuine
cross-agent twin exists). The language+framework fleet grew from 7 to 12. Two new `score.py`
`CATEGORY_DOMAIN` twins landed with regression locks: `ipc-validation`→security (Electron, the
milestone's first real twin) and `list-perf`→impact (React Native); react-native dual-emits `react` +
`react-native` in triage so it layers on top of `framework-react` rather than replacing it.
Dogfood efficacy (CLOSE-01) PASSED — all five agents proven via seven scoped runs (fire / catch /
stay-silent), owner sign-off recorded; the Phase-29 deep review caught and fixed two Warning
self-contradictions in the efficacy doc. Milestone audit clean 9/9; integration check fully coherent.
Clears backlog item 999.1.

**Validated this milestone (v2.7):** EXPRESS-01, VUE-01, ANGULAR-01, ELECTRON-01, RN-01 (the five
framework reviewers), WIRE-01/WIRE-02 (six-touchpoint wiring + 12-agent count coherence), VERIFY-01
(clean deep-review gate every agent phase), CLOSE-01 (efficacy + 2.7.0 bump + tag + publish).

</details>

<details>
<summary>Previous: v2.6 shipped 2026-06-28</summary>

**Shipped 2026-06-28 (plugin v2.6.0, annotated tag `v2.6` on `a169429`, pushed to `origin/main`).**
v2.6 "framework-skill review agent" added the `framework-skill` reviewer (skill-authoring quality +
half-wired-addition wiring check) plus the NOISE-01 severity-scoped `≤45` low-tier confidence ceiling.
Validate-and-adopt of dogfooded commit `95c6834`; deep-review gate (VERIFY-01) PASSED (1 Warning fixed
@ a169429, 1 Medium deferred to a fleet-wide hardening follow-up); milestone audit clean 9/9.

</details>

**Shipped 2026-06-28 (plugin v2.5.0, annotated tag `v2.5` un-pushed on `feat/v2.5`).** v2.5
"Sharper, more legible reviews" made vibe-check's `--all` review *source, not noise*, crash-proofed
the deterministic scoring core, and added a deep-review test-sufficiency agent. Proven by a live
`--all` self-dogfood (CLOSE-01 PASS — all three threads confirmed on the real tree, owner sign-off,
`plugins/vibe-check/docs/efficacy/RESULTS-v2.5.md`). The dogfood caught two cross-file-drift defects
in vibe-check's OWN contracts (the exact bug class the tool exists to catch); both fixed
in-milestone, the close-review tightened the React cross-confirm fix, and a regression lock was
added. 142-test suite green, golden digest frozen.

**Validated this milestone (v2.5):**
- ✓ `--all` reviews source not docs — `.planning/`/`docs/` denylist + code-`.md` allowlist override; bare `all` accepted; one-line `Mode:` conclusion — SELECT-01/02/03, LEGIBLE-01/02
- ✓ Crash-proof `score.py` against malformed findings + the T1-T21 malformed-shape test matrix — HARDEN-01/02
- ✓ Deep-review test-sufficiency agent (consume-only coverage reader, risk-weighted, skip-and-note) + impact.md carve-out — TESTSUF-01/02/03/04
- ✓ Efficacy proof + 2.5.0 bump + `v2.5` tag — CLOSE-01/02

## Last Milestone: v2.8 Tunable, quieter reviews (SHIPPED 2026-07-01 — early manual close; scope below is the original definition, see Current State for what actually shipped)

**Goal:** vibe-check gains a repo-level `.vibe-check.toml` config surface, with the noise controls
as its first consumers — config is the vehicle, every knob reads from one schema. Consumes backlog
999.4 (tunable config / confidence axis) + 999.10 (noise & Codex legibility) + 999.0 (safer
fix-loop default). The scoring formula is untouched throughout.

**Target features:**
- **`.vibe-check.toml` config surface** — the orchestrator reads one well-known repo-root path once
  per run; precedence is CLI flag > toml > built-in default; a missing/malformed/partial config
  degrades **per-key** to defaults with a warning and **never breaks a review** (999.4)
- **Confidence axis** — surface `agent_confidence` as a visible field on every rendered finding +
  `min_confidence` (config) / `--min-confidence N` (flag) that filters **before** scoring; the
  dropped-count stays in the honesty summary (nothing silently vanishes) (999.4)
- **Idiom band floor** — `score.py` caps the `idiom` category at a tunable max band (default
  `medium`, so idioms never block finalize), reusing the existing category-aware capping (999.10)
- **Codex legibility** — default stays `auto` but every run prints one legible line about what Codex
  did (joined / skipped-with-reason / off-via-config); adds a `--codex` flag + `[noise] codex`
  override (`off`/`auto`/`on`) (999.10)
- **`// vibe-ignore: <reason>` marker** — joins the existing ±2 silenced-marker grep; a non-empty
  reason is required (a bare marker is itself flagged as a low finding) (999.10)
- **Safer fix-loop default** — strip the apply-all "(Recommended)" label from the fix loop (999.0)
- `plugin.json` → 2.8.0 at close; annotated tag `v2.8`

**Key context:** Build-for-myself lens. Config-read is the orchestrator's job; enforcement is split
by knob nature — script-math knobs (`min_confidence`, `idiom_floor`, `thresholds`, `vibe-ignore`)
are enforced in `score.py` via new envelope keys; dispatch/prose knobs (`disabled` agents,
`top_model`, `codex`, the fix-loop label) are enforced by the orchestrator. Phases are grouped by
**enforcement boundary** (script vs orchestrator) so each phase deep-reviews coherently — the same
serialization discipline v2.7 used for shared wiring files. Phase numbering continues from 29 →
Phases 30–34 (4 work phases + close). The scoring formula stays untouched: `min_confidence`
*filters*, `thresholds` parameterize existing cutoffs, `idiom_floor` caps an existing category — no
re-weighting. gitleaks (999.2), SARIF/PR-posting (999.3/999.5), measured cost (999.12), docs pass
(999.13) explicitly deferred. Design spec:
`docs/superpowers/specs/2026-06-30-tunable-quieter-reviews-design.md`.

<details>
<summary>Previous: v2.7 Framework coverage (shipped 2026-06-30)</summary>

**plugin v2.7.0, tag `v2.7` on `3501545`, pushed to `origin/main`.** Added five framework reviewer
agents (Express, Vue, Angular, Electron [security-weighted], React-Native) wired across six
touchpoints; the language+framework fleet grew 7→12; two new `score.py` twins (`ipc-validation`→
security, `list-perf`→impact) with regression locks. Clears backlog 999.1. CLOSE-01 PASS (five
agents proven via seven scoped runs, owner sign-off); audit 9/9. Design spec:
`docs/superpowers/specs/2026-06-28-framework-coverage-agents-design.md`.

</details>

<details>
<summary>Previous: v2.4 Dogfood-driven hardening (shipped 2026-06-26)</summary>

**plugin v2.4.0, tag `v2.4` un-pushed.** Fixed the real defects vibe-check's own `--all` dogfood
found in its orchestration prose and built the deterministic-core Python `score.py` + state-safety
hardening that makes that whole defect class structurally impossible (CLOSE-01 PASS, owner sign-off,
`RESULTS-v2.4.md`). Validated: FIXLOOP-01, DOGFIX-01..10, CORE-01..03, ROBUST-01..04, CLOSE-01/02.

</details>

**Key context:** Prompt-only plugin — most code is Markdown orchestration prose; v2.4 introduced
the *first* executable code (`score.py`, stdlib-only Python 3, no new user dependency), which v2.5
crash-proofed and built the test-sufficiency agent on top of.

---
*Last updated: 2026-10-15 after Phase 53 (false-alarm reduction)*

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Two review modes: `/review` (fast pre-commit) and `/deep-review` (thorough pre-PR) — shipped (plugin v2.0.0)
- ✓ Parallel domain reviewer agents with model tiering — shipped (plugin v2.0.0)
- ✓ Language agents: TypeScript, Python, Go, Rust — shipped (plugin v2.0.0)
- ✓ Framework agent: React — shipped (plugin v2.0.0)
- ✓ Confidence scoring + false-positive filtering with transparency section — shipped (plugin v2.0.0)
- ✓ Interactive fix loop (dedicated `fix` agent, atomic commits) — shipped (plugin v2.0.0)
- ✓ GSD intent-doc awareness; writes only to `.turingmind/` — shipped (plugin v2.0.0)
- ✓ Comprehensive `framework-fastapi` review agent (11 categories: DI, async, Pydantic/validation, response/status, data exposure, auth, lifecycle, routing, OpenAPI honesty, file-upload, settings) with 5 inline false-positive gates — shipped (plugin v2.1.0)
- ✓ Dispatch wiring in `/review` and `/deep-review` (both modes, Sonnet) + docs parity — shipped (plugin v2.1.0)
- ✓ Efficacy test against a real FastAPI codebase (dashboard slice, 11 planted items, N=3): caught all 3 criticals 3/3, 0/5 bait false-fires 3/3, owner sign-off — shipped (plugin v2.1.0, EFF-02 PASS)
- ✓ Codex (GPT-5-codex) runs as a second, independent adversarial reviewer in `/deep-review` — shipped (plugin v2.2.0)
- ✓ Codex findings flow through the existing merge/dedup/score/render pipeline like a native reviewer (no scoring/schema changes) — shipped (plugin v2.2.0, MERGE-01)
- ✓ Cross-model confirmation: Codex + a native agent on the same site fires the +10 cross-confirm bonus — shipped (plugin v2.2.0, proven live EFF-02a)
- ✓ Graceful degradation: skip-and-note one-liner when Codex is unavailable/unauthenticated — never blocks the review — shipped (plugin v2.2.0, proven live EFF-02b)
- ✓ Whole-codebase review mode (`--all`) on `/review` and `/deep-review`: whole-tree selection + skip rules, risk-ranked budget-fitting chunking, per-chunk triage, estimate-and-confirm budget gate, `in_reviewed_set` filter, Critical/Warning bar + `--full` + cross-file dedup + coverage line, Codex fail-closed skip, report-first / opt-in (`--all --fix`) fixes — additive and prompt-only, diff-mode non-regressed — shipped (plugin v2.3.0; dogfood efficacy all 5 §6 criteria PASS, owner sign-off)
- ✓ Dogfood-driven hardening: ~13 self-found orchestration-prose defects fixed (incl. the `--all --finalize` state-path bug), safer fix-loop default, the deterministic-core Python `score.py` (stdlib-only, 123-test pinning suite, un-skippable) + state-safety hardening (single-writer, category-domain cross-confirm, low-entropy carry-forward, hard-halt scoring-ran gate) — shipped (plugin v2.4.0; CLOSE-01 PASS, owner sign-off)
- ✓ Sharper, more legible reviews: `--all` reviews source not docs (denylist + code-`.md` allowlist + bare-`all` + one-line `Mode:`), crash-proof `score.py` + T1-T21 matrix, the deep-review test-sufficiency agent (consume-only, risk-weighted, skip-and-note) — shipped (plugin v2.5.0; CLOSE-01 PASS, owner sign-off; dogfood caught + fixed two self cross-file-drift defects)
- ✓ `framework-skill` review agent: skill-authoring quality (discoverability / progressive disclosure / structure / content / bundled-script hygiene) + the half-wired-addition wiring check, file-shape `"skill"` triage detection, full dispatch wiring, and the NOISE-01 severity-scoped `≤45` ceiling on low-tier taste/differentiator checks only — shipped (plugin v2.6.0, tag `v2.6` pushed to `origin/main`; VERIFY-01 deep-review gate clean, audit 9/9)
- ✓ Framework coverage: five framework reviewer agents (`framework-express`, `framework-vue`, `framework-angular`, `framework-electron` [security-weighted], `framework-react-native`) authored to the `framework-react.md` pattern and wired across six touchpoints; fleet 7→12; two new `score.py` twins (`ipc-validation`→security, `list-perf`→impact) with regression locks; react-native dual-emits in triage — shipped (plugin v2.7.0, tag `v2.7` pushed to `origin/main`; CLOSE-01 five-agent efficacy PASS, audit 9/9; clears backlog 999.1)
- ✓ Prove it: the `codex` knob live end-to-end (`--codex off|auto|on` + `[noise] codex`, one legible Codex-status line per run — LEGIBLE-01/02/03); every v2.8 knob smoke-proven (PROOF-01/02); the committed cryptographically pre-registered B3 organic ground-truth kit (6 diffs); first measured quality numbers — catch-rate 8/9, FP-rate 6/9 from 18 owner runs — with the D-11 PROCEED verdict on H-CORE/H-LANE/B-SEV/B-REWEIGHT — shipped (plugin v2.9.0, tag `v2.9`, audit 9/9)

- ✓ B3 set grown to 12 organic diffs (6 carried + 6 new; sealed per-diff answer keys + provenance sidecars; two-commit seal chain with a pinned byte-exact append verifier), the v2.10 pass bar pre-registered in `PREREGISTRATION-v2.10.md` (seal-1 before any change), and the whole set baselined ×3 — 36/36 owner-driven runs under ONE pinned harness tuple (Claude Code 2.1.261 / codex-cli 0.153.4 / Fable 5.1) — on the UNCHANGED v2.9.0 plugin on the Claude 5 harness: catch 15/15, FP 19/21; carried-6 re-measure catch 8/9→9/9, FP 6/9→9/9 (noisier under Claude 5 — the harness is the variable) — Validated in Phase 38: Grow the B3 set + Claude-5 baseline (`SCORING-v2.10.md`, `RESULTS-v2.10.md` baseline section)

- ✓ README/config docs current for the Claude 5 generation (Sonnet 5 / Opus 5 / Haiku 4.5; Fable 5.1 opt-in; opus/fable allowlist) with labeled static cost estimates — v2.10 (measured cost stays backlog 999.12)
- ✓ Prose diet: review/deep-review restructured into phase files, deterministic families extracted to tested scripts, 999.8 single-writer verified, helpers from the trusted plugin root (TRUST-01/02) — v2.10
- ✓ Wave 1 scorer interventions (B-SEV, B-REWEIGHT, H-LANE) via a zero-catch-regression replay harness + live spot-check — v2.10
- ✓ Wave 2 agent-side safe-change recognition + confidence ceilings on bugs/security/impact/codex — v2.10
- ✓ Full post-change measurement evaluated honestly: untuned MISS (6/18 · 13/15), one retune → combined PASS 3/18 · 15/15 (tuned on same set) — v2.10
- ✓ Shipped plugin 2.10.0, annotated tag `v2.10`, atomic hash-verified publish — v2.10
- ✓ Lanes with nothing to read are not dispatched, and the reason is stated (test-sufficiency without coverage artifacts) — v2.11
- ✓ Unresolved findings never expire; a finding is not re-asked without new evidence (evidence-bound owner decisions) — v2.11
- ✓ One decision card per fix-loop pass and one at finalize, regardless of finding count — v2.11 (Close out reachable in every mode as of 2.11.1)
- ✓ Fix agent verifies its edit before committing; one hunk-isolated commit per fix — v2.11
- ✓ Detection agents cannot mutate the reviewed repo via git (PreToolUse guard plus before/after snapshot) — v2.11
- ⚠ B3 catch rate unchanged (15/15), but false alarms 5/18 vs ≤3/18: MISS, shipped as measured by owner decision — v2.11
- ✓ Shipped 2.11.0 + 2.11.1 through gates-first atomic, hash-verified publishes — v2.11
- ✓ Independently verified fixes close without dummy code changes or repetitive manual dismissal; stale or still-applicable findings stay open — v2.13
- ⚠ Owner defer/dismiss decisions survive regrouping and unrelated edits and reopen on changed evidence — v2.13, with known limits (999.23 wrong-keep shapes, 999.24 over-asks)
- ✓ Action labels match behavior; an inconclusive re-check has a clear, bounded recovery path — v2.13
- ✓ A clear owner answer is acted on, not asked again; an unclear one gets one follow-up — v2.13 (live model extraction unverified; wordier phrasings ask, 999.26)

### Active

<!-- v2.14 Decision reliability — full REQ-IDs in REQUIREMENTS.md. -->

- [ ] Stale decisions reopen with the correct reason when evidence changes; deferred obligations survive filtering (999.23)
- [ ] Nearby/in-diff evidence uses only actually changed lines (999.24) — Phase 60 complete 2026-10-30, ships with v2.14; known limits R6 (live PR fetch unexercised) and R17 (PRs over GitHub's diff limits fail closed, owner-accepted)
- [ ] Finalize works across fresh shell calls (999.25) — Phase 60 complete 2026-10-30, ships with v2.14; state-file scope trust deferred as 999.27
- [ ] Release gate passes with only named replay differences

(v2.13 Active items shipped — see Validated; v2.12 items shipped or were deferred as recorded in MILESTONES.md; measurement remains UNMET/deferred.)


Deferred to a later milestone: gitleaks deterministic secret-scan (999.2 — owner-deferred at
v2.10 scoping), CI reach (999.3 SARIF, 999.5 PR-posting), docs pass (999.13 — re-sequenced
AFTER this milestone since half of what it documents changes here), the remaining v2.4/v2.5
dogfood Mediums (fix-agent prompt-injection hardening, `.planning/*-SUMMARY.md` hygiene), the
`security.md` critique pass, and any re-measure beyond the single pre-registered retune.

## Prior Ships (history — the live status is "Current State" at the top of this doc)

**Shipped v2.5** (2026-06-28): plugin at **2.5.0**, annotated tag `v2.5` (un-pushed on `feat/v2.5`).
`--all` reviews *source, not noise* (a default whole-tree run excludes `.planning/`/`docs/`/specs/
READMEs/lockfiles/generated while keeping the plugin's own `agents/`/`commands/`/`templates/` `.md`),
the orchestrator resolves arg-mode quietly (bare `all` → `--all`, one-line `Mode:` conclusion), the
deterministic scoring core `score.py` is crash-proofed against malformed findings (T1-T21 matrix),
and a deep-review-only **test-sufficiency agent** judges whether changed code is adequately tested
(consume-only coverage, risk-weighted, skip-and-note). Proven by an `--all` self-dogfood (CLOSE-01
PASS, owner sign-off) that itself caught two cross-file-drift defects in vibe-check's own contracts
— both fixed in-milestone, the close-review tightening the React cross-confirm fix, regression lock
added. 142-test suite green.

**Shipped v2.4** (2026-06-26): plugin at 2.4.0, tag `v2.4`. Fixed the real defects the `--all`
dogfood found in the plugin's own prose and built the deterministic-core `score.py` + state-safety
hardening (CLOSE-01 PASS, owner sign-off).

**Current milestone:** v2.12 Quiet without hiding — see Current Milestone at the top.

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Deepening/reworking existing agents (bugs, security, language-python, etc.) — already tuned and working; touching them is regression risk.
- Codex in the fast `/review` path — a multi-minute Codex run doesn't belong on the seconds-fast pass; deep-review only (ASYNC-02 if ever revisited).
- A Codex *fix* path — Codex is detection-only; the existing `fix` agent applies fixes.
- Lane prompt changes in v2.11 (incl. Rule-2 helper-bypass quieting) — v2.11 measures its loop changes against Phase 43 B3; a lane-prompt change would confound that comparison (→ backlog / v2.13).
- Moving measurement-only scripts out of the install in v2.11 (W3) — owned by v2.12's test/script trim.
- Editing review.md / scoring.md / agent-output-schema.md / triage.md — the integration is additive in deep-review; touching these is regression risk (MERGE-01). (superseded 2026-09-29: the v2.10 Wave-1 freeze lift, Phase 41, deliberately edits score.py / scoring.md under the zero-catch-regression guardrail)

## Context

- Prompt-only plugin: Markdown agent specs (`plugins/vibe-check/agents/*.md`) + command
  dispatch orchestration (`commands/review.md`, `commands/deep-review.md`) + templates
  (scoring, false-positive rules, output schema). No compiled code / unit-test suite for
  agent behavior; verification is structural + behavioral (run the agent, judge findings).
- New framework agents follow the `framework-react.md` pattern: self-contained file,
  frontmatter (`name`/`description`/`model`), a checklist, the "Coverage, not filtering"
  instruction, and the JSON output contract. They run *in addition to* the matching
  language agent.
- The owner has a product (not software-dev) background and relies on agent coverage as
  the safety net — hence the comprehensive-coverage requirement for new agents.
- The owner uses FastAPI across 5 repos: dashboard, gsdboard, roonseek, triggarr, VolvLog.
- **Shipped v2.1** (2026-06-18): plugin at 2.1.0; agents now cover TS/Python languages + React/FastAPI frameworks. Efficacy evidence for the FastAPI agent lives at `plugins/vibe-check/docs/efficacy/RESULTS.md`.
- **Shipped v2.2** (2026-06-21): plugin at 2.2.0; `/deep-review` runs Codex (GPT-5-codex) as a second adversarial reviewer with cross-confirm + graceful degradation. Efficacy evidence at `plugins/vibe-check/docs/efficacy/RESULTS-v2.2.md` (EFF-01/EFF-02 PASS, owner sign-off). Operational note: openai-codex companion de-auth/restore requires clearing the per-project broker pin under `~/.claude/plugins/data/codex-openai-codex/state/` (not just moving `~/.codex/auth.json`).

## Constraints

- **Tech stack**: Claude Code plugin (Markdown agents + slash-command orchestration). No build step for agent prompts.
- **Compatibility**: Must not regress existing agents or the dispatch contract (the "MANDATORY DISPATCH SHAPE" parallelism rule in `commands/review.md`).
- **Design philosophy**: Coverage-first — agents surface everything (incl. low-confidence); the orchestrator's scoring layer ranks/filters. Agents report defects, not style/taste.
- **Versioning**: GSD milestone labels track the plugin semver (`plugin.json`), currently **2.9.0** (v2.9 shipped 2026-07-08). marketplace.json carries no per-plugin version — only plugin.json is bumped.

## Key Decisions

<!-- Decisions that constrain future work. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Scope v2.1 to FastAPI agent only (not all 5 framework agents) | Tight, shippable milestone; FastAPI is highest-priority by repo count (5) | ✓ Good — shipped clean in one milestone |
| Build the agent comprehensively (11 check categories, not 7) | Owner relies on coverage; scoring layer handles resulting noise | ✓ Good — efficacy 0/5 false-fires confirms the scoring layer holds the noise |
| Run FastAPI agent in both `/review` and `/deep-review` (Sonnet) | Mirrors `framework-react`; maximum coverage (checks every review, not just pre-PR) | ✓ Good |
| Efficacy test = real-codebase review with planted ground truth, owner judges findings | Right bar for a prompt-only agent; owner can assess usefulness without reading code | ✓ Good — caught 3/3 criticals, owner signed off (EFF-03) |
| GSD milestone version = v2.1 (match plugin semver) | Keep planning label in sync with the plugin's real published version | ✓ Good — plugin.json bumped 2.0.0→2.1.0 at close |
| Efficacy fixture must expose enclosing `async def` in the diff hunk | A blocking-call-in-async seed went 2/3 when the signature sat outside the hunk; agent correctly hedged | ✓ Good — fixed fixture (not agent), re-ran to 3/3 |
| v2.2: Codex as an orchestrator-driven step (not a Task subagent) | A multi-minute blocking Codex call would stall the parallel native fan-out; orchestrator step runs around it and collects via BashOutput | ✓ Good — native agents + Codex ran concurrently in the live test |
| v2.2: exact-or-skip Codex diff targeting (run only when Codex's representable range == Phase-0 diff) | Avoids silently reviewing a partial/wrong diff; a non-representable range fails closed to skip-and-note | ✓ Good — branch mode matched exactly, Codex ran on the right diff |
| v2.2: de-auth proof via broker-teardown + auth move-aside (NOT `codex logout`) | Reversible without a browser re-login; logout deletes creds | ✓ Good — but restore also needs the per-project broker.json pin cleared (captured to memory) |
| v2.2: efficacy on a throwaway branch in THIS repo with a planted SQLi | Guarantees a cross-confirmable defect vs hoping a real diff has one; branch never merged | ✓ Good — both planted defects cross-confirmed +10 on the first run |
| v2.2: release gates hardened via 3 Codex adversarial-review passes on the plan | Catches accidental false-greens on irreversible auth/tag ops before execution | ✓ Good — closed real holes; residual (gitignored approval state) covered by live human sign-off |
| v2.3: `--all` is additive + prompt-only — a Phase-0 branch-flip that rejoins the existing pipeline; every change `$ALL_MODE`-guarded | Keeps the proven diff-mode path byte-stable while adding whole-codebase audit; no scoring/schema rewrite | ✓ Good — diff-mode non-regression confirmed in the dogfood (criterion 2) |
| v2.3: dogfood = run the tool on its OWN codebase, owner judges findings | Truest efficacy test for a prompt-only tool; the tool reviewing itself is the strongest proof | ✓ Good — found 9 real defects in its own prose (the drift class it exists to catch); owner signed off |
| v2.3: dogfood findings deferred to v2.4, NOT fixed in the close phase | Fixing `--all`/orchestration code is out of scope for "prove + ship"; fixing would expand the close into a fix milestone | ✓ Good — shipped the feature proven-working; findings logged for v2.4 |
| v2.3: skipped turingmind `--finalize` at close (would block on the 9 deferred findings) | Forcing it green would fake fixes or fix out-of-scope code; the committed RESULTS-v2.3.md is the shipped efficacy record (.turingmind/ is gitignored working state) | ✓ Good — honest deferral, findings preserved in backlog |
| v2.6: validate-and-adopt the existing `framework-skill` commit (`95c6834`) rather than re-implement | The agent is already built and dogfooded; a brainstorm pressure-test confirmed the design sound. Rebuilding would discard working code to regenerate near-identical output | — Pending (deep-review pass is the gate) |
| v2.6: `"skill"` is detected by file shape (SKILL.md / agent prompt / manifest), not imports — the one framework keyed off file presence | Skills/agents/manifests have no import statement to key off; documented as the deliberate exception in `triage.md` | ✓ Good — shipped in 2.10.0 (TRUST-01/02 live; Phase 39 dissolution held) |
| v2.6: add NO `score.py` cross-confirm entry for `framework-skill` categories | Per the established twin policy, only genuine cross-agent twins are mapped; `framework-skill`'s categories have no twin (nothing else reviews skill authoring), so they correctly stand alone. Adding entries would be the bug | — Pending |
| v2.6: add a severity-scoped noise guardrail (a `≤45` cap on `low`-severity taste/differentiator checks only — the prose nitpicks in `content` + soft `structure`; never category-wide) as the phase's executed change | The agent fires on most plugin/skill self-reviews and reviews subjective prose; the guardrail protects the "low noise" core value while keeping objective `wiring`/`description` defects AND medium/high `content` safety findings full-confidence | — Pending |
| v2.10 re-scope (2026-09-05): dissolve Phase 39 (measured cost → backlog 999.12 behind a feasibility spike; Claude-5 docs → Phase 44), add TRUST-01/02 to Phase 40 (helpers resolve from the trusted plugin install, fix agent validates paths pre-edit), cap DIET-04 spot-checks, hold DIET-03 verify-only, keep every model default; backlog 999.15/999.16/999.17 | An external source review, verified line-by-line: the repo-first helper resolver lets a reviewed PR plant code that Phase 3 executes unprompted (in-threat-model); measured cost has no mechanism (the orchestrator cannot tokenize) and is off the quiet-down path; the ~80-owner-run budget is the milestone's real constraint; a live model-lineup check showed every alias already resolves to the current generation, while the cost anchors were stale (Sonnet 5 $2/$10, new tokenizer) | — Pending |
| v2.11: ship 2.11.0 as measured despite the B3 false-alarm MISS (5/18 vs ≤3/18); decline the one PROMPT-class retune | Catches held 15/15. The miss traced to pre-existing lane behaviour, not v2.11 code, and a retune would have confounded the regression comparison | ⚠️ Revisit — the false-alarm bar is still unmet; carry into the next noise work |
| v2.11: release waivers instead of re-measuring post-measurement commits (11c8afc; Phase-50 fix commits) | The changes touch no reviewer, scorer or detection path, B3 runs never exercise them, and a re-run costs ~3–4 owner-hours | ✓ Good — disclosed in README, tag bodies and RUN-METHOD-NOTES; parity-checked |
| v2.11: fix the audit-found Close-out/`--finalize` defect as a 2.11.1 patch before archiving | v2.11's headline feature was unreachable in the orchestrator's own mode; the fix was small and low-risk | ✓ Good — shipped same day; audit re-run clean |
| v2.11: leave the command spines' finalize trigger unchanged (D-01) and strip `--finalize` only in Phase 0 | Smallest change that fixes every documented shape | ⚠️ Revisit — the spine's substring reading vs the whole-token strip is tech debt |
| v2.13: reproduce every failure on current code before fixing; drop non-reproducing paths | Avoid invented work; each fix needs a failing fixture | ✓ Good — 57 N1–N6 and 58 bug C dropped with records; every change landed behind a red fixture |
| v2.13 (D-19/D-22): hard stop Phase 57 after four structural rounds; carry remaining wrong-keeps as 999.23 | Each "root fix" round moved the pooling gap to the next unpooled path; diminishing returns | ⚠️ Revisit — 999.23 shapes can silently keep a decided finding; a fix must merge at carry_state's per-hash read |
| v2.13 (D-23): roll back the best-unique title matcher; strict all-words match, else ask | The looser matcher misdirected a dismissal in review | ✓ Good — fails safe; wordier phrasings ask (999.26) |
| v2.13: one branch and one PR per phase | Smaller reviewable units than one milestone branch | ✓ Good — three clean squash merges |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-30 after Phase 60 (exact change evidence and reliable Finalize)*
