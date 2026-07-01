---
gsd_state_version: 1.0
milestone: v2.8
milestone_name: Tunable, quieter reviews
status: shipped
stopped_at: v2.8 SHIPPED 2026-07-01 (early manual close by owner directive — merge f19be14, tag v2.8, published); 33-02 wiring + Phase-34 smoke proofs deferred
last_updated: "2026-07-01T22:30:00.000Z"
last_activity: 2026-07-01 -- v2.8 merged + tagged + published; GSD docs trued up post-ship
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 12
  completed_plans: 11
  percent: 92
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-28)

**Core value:** Catch real defects in a developer's changes before they ship — high coverage, low noise — so a reviewer who can't manually audit code can trust the agent's output as their safety net.
**Current focus:** v2.8 SHIPPED — no milestone scoped. Next: 2.8.x follow-up (33-02) or /gsd:new-milestone (v2.9).

## Current Position

Milestone: **v2.8 SHIPPED 2026-07-01** — plugin 2.8.0 (`6002cae`), merge commit `f19be14` on main
(real merge, not fast-forward), annotated tag `v2.8`, main+tag+branch pushed and hash-verified.
Closed EARLY by owner directive ("merge everything and push as 2.8") — NOT via the Phase-34 close
ritual. Suite at ship: 356 tests + 221 subtests green. Install cache resynced to 2.8 post-ship.

What shipped: Phases 30–32 in full; Phase 33 PARTIAL (33-01 config.py `codex` knob only — 33-02
orchestrator wiring never executed, so the knob is a validated-but-inert config key); Phase 34
SUPERSEDED (bump/tag/publish done manually; planted-fixture smoke proofs + per-phase deep-review
gates, incl. Phase 33's, never ran). PLUS unplanned scope: the Fable second-model review
remediation (buckets 1–3 of `docs/design/FABLE-REVIEW-FINDINGS.md`) — scorer fixes, the
`min_confidence` 0–49 refusal (A3), `scripts/guard.py` containment extraction, and the gen-2
calibration retrofit across the 9 gen-1 agents.

Status: idle between milestones
Last activity: 2026-07-01 -- v2.8 shipped + GSD docs trued up

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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work (v2.8):

- v2.8 spine: a repo-level `.vibe-check.toml` **config surface** is the milestone's vehicle; the noise controls are its first consumers. Phase 30 builds the reader/precedence/fail-safe; Phases 31-33 plug knobs into it. 4 work phases + 1 close (Phases 30-34), continuing numbering from v2.7's Phase 29.
- Phases are grouped by **enforcement boundary**: script-enforced knobs (`min_confidence`, `idiom_floor`, `thresholds`, `vibe-ignore`) land in `score.py` via new envelope keys; orchestrator-enforced knobs (`disabled` agents, `top_model`, `codex`, the fix-loop label) act in dispatch/prose. 32 (script noise knobs) and 33 (orchestrator knobs) are split on this boundary so each deep-reviews coherently.
- Execution is **SEQUENTIAL (30→31→32→33→34)** — the shared files (`commands/review.md`, `commands/deep-review.md`, `scripts/score.py`, `scripts/test_score.py`) are touched by multiple phases; same serialization discipline v2.7 used for shared wiring files. 34 depends on all four work phases (it exercises every knob).
- **The scoring FORMULA stays untouched** throughout: `min_confidence` *filters before scoring*, `thresholds` *parameterize* existing cutoffs, `idiom_floor` *caps* an existing category — no re-weighting. Re-deriving `agent_confidence` is explicitly out of scope.
- Load-bearing invariant: a missing/malformed/partial config degrades **per-key** to its built-in default with a warning and **never breaks a review** — zero-config back-compat == v2.7 behavior (CONFIG-01/CONFIG-03).
- Precedence is **CLI flag > `.vibe-check.toml` > built-in default**, resolved per knob by the orchestrator before passing into the envelope (script-enforced) or acting directly (orchestrator-enforced).
- `tomllib` (Python 3.11+) with graceful degradation; the exact Python<3.11 fallback (degrade-to-no-config vs minimal parser) is a Phase-30 plan-time decision — either way a missing parser must not break the review.
- Deferred this milestone: gitleaks (999.2), SARIF/PR-posting (999.3/999.5), measured cost (999.12), docs pass (999.13), and the remaining v2.4/v2.5 dogfood Mediums.

Earlier decisions (v2.6) still on record:

- v2.6 scope: ONE phase (Phase 23) — validate-and-adopt the existing `framework-skill` agent (commit `95c6834` on `feat/framework-skill-reviewer`) plus one new noise-guardrail edit. NOT a build-from-scratch; the agent is already authored and dogfooded.
- The phase's executed change is the noise guardrail: a SEVERITY-SCOPED `agent_confidence ≤ 45` ceiling on the `low`-severity taste/differentiator checks ONLY (the prose nitpicks in `content` + the soft `structure` nitpicks) — the cap rides the `low` tier, NOT the category. Medium/high findings stay uncapped in every category (incl. genuine `content` safety checks), as do `wiring`/`description`/`scripts`/hard-`disclosure` — reuses the differentiator-tier pattern from `framework-fastapi.md`. (Revised from an earlier category-wide framing after codex adversarial review showed a category-wide cap would suppress medium/high content safety findings below the deep-review threshold.)
- `"skill"` is detected by file SHAPE (SKILL.md / agent prompt with `name:`+`description:` frontmatter / plugin manifest), not by imports — the one framework keyed off file presence; documented as the deliberate exception in `triage.md`.
- Add NO `score.py` cross-confirm entry for `framework-skill` categories — per the established twin policy, the agent's categories have no cross-agent twin, so they correctly stand alone. Adding entries would be the bug.
- Wiring = same convention as `framework-react`/`framework-fastapi`: `triage.md` file-shape detection emitting `"skill"`, dispatch rows in `index.md` / `commands/review.md` / `commands/deep-review.md`, agent-range bump (floor/max 6→7) and updated cost-estimate figures. Auto-discovery makes those the complete wiring set.
- Deep-review is the real quality gate (VERIFY-01); `plugin.json` 2.5.0 → 2.6.0 at close (CLOSE-01). Research skipped — settled design against a known reference (Anthropic Agent Skills best-practices).
- [Phase ?]: Phase 27: framework-electron is security-weighted — explicit unsafe flags fire headline CRITICAL; omitted flags are version-gated hedges (>=5/>=12/>=20); centralizable guards are medium confirm-not-central (D-03)
- [Phase ?]: Phase 27: score.py gains the milestone's FIRST real twin (ipc-validation->security, D-06); the other five electron categories stay None; the twin inherits the full security-domain blast radius (intended, test-pinned)
- [Phase ?]: Phase 27: six-touchpoint wiring incl. the index.md matrix row; count prose bumped 10->11; plugin.json NOT bumped (that is Phase 29)
- [Phase ?]: Phase 28: framework-react-native triages via DUAL-EMIT (react + react-native) — FIRST agent additive to another framework agent; web-React-only diffs (react-dom/DOM-tags/expo-server-sdk) emit react ONLY
- [Phase ?]: Phase 28: list-perf->impact is the milestone's SECOND real score.py twin; the other five RN categories stay None and expo-config is DELIBERATELY NOT twinned to security (D-06); twin test asserts overlap against the impact CATEGORY KEYS not the bare 'impact' domain value
- [Phase ?]: Phase 28: WIRE-02 closed — count prose coherent at the full 12-agent fleet (floor + 12); v2.7 framework fleet complete; plugin.json NOT bumped (Phase 29)
- [Phase ?]: Phase 29 P01: proved all five v2.7 framework agents via SEVEN scoped runs (5 framework + control-only + web-React negative) — triage emits one run-level frameworks array per diff, so silence and the RN react-only negative come from their own isolated runs, never a combined diff
- [Phase ?]: Phase 29 P01: RESULTS-v2.7.md written UNSIGNED, DOGFOOD_HEAD anchored to RN-wiring commit 7c77e4e (not docs commit c0bb779); both D-06 deferred notes carried; plan-02 bump-provenance placeholder reserved; OWNER-SIGNOFF is plan-02's job
- [Phase ?]: Phase 30 P01: config.py is the never-raise .vibe-check.toml I/O boundary (load_config -> (values,warnings)); inverts score.py's fail-closed posture — degrades per-key to defaults, __main__ exits 0 always (CONFIG-03); the ONE new module allowed filesystem I/O so score.py stays pure
- [Phase ?]: Phase 30 P01: D-02 thresholds schema LOCKED — {critical,warning,medium} non-bool ints in [1,100], strictly descending, medium>=70, whole-set fallback to None; two ordered pre-parse DoS guards (os.path.isfile regular-file BEFORE os.path.getsize 1-MiB cap); catch (TOMLDecodeError,UnicodeDecodeError,OSError)+ImportError degrade (D-01)
- [Phase ?]: Phase 30 P01: validate-then-overlay flag precedence (flag>toml>default), flags run same validators never bypass (Finding #3); top_model opus/fable allowlist reuses $VIBE_CHECK_TOP_MODEL; disabled honors core-agent disable; below-80 band floor ACCEPTED (Finding #4). test_config.py 33 tests, suite 147->180, score.py untouched
- [Phase ?]: Phase 30 P02: band_for parameterized to band_for(score, thresholds=None) via _usable_bands whole-set crash-safe guard (all-three-non-bool-ints-or-whole-default); run() threads envelope.get('thresholds') (no or-empty) into the SINGLE band write; _DEFAULT_BANDS 95/80/70 added next to THRESHOLDS with a two-layer banner (D-02); default path byte-identical, GOLDEN_DIGEST + TestBandBoundaries UNCHANGED, import set frozen, suite 180->191, two-layer dead-band proof pinned
- [Phase ?]: Phase 0.6 config read is unconditional (between review.md Phase 0.5 and 0.7), runs on every mode + both commands, degrades-not-aborts
- [Phase ?]: top_model resolves env>toml>default(opus) at deep-review.md:55; disabled subtracted before dispatch in both files (core-agent disable announced); thresholds stays review.md-only
- [Phase ?]: Phase 32-01: idiom_floor cap ACTIVE by default at medium (A1) — absent envelope key defaults to medium cap INSIDE score.py so idioms never block finalize
- [Phase ?]: Phase 32-01: explicit off/none returns the literal 'off' sentinel (NOT None) end-to-end so absent != off is provable at the scorer; malformed fails SAFE to medium (cap stays active)
- [Phase ?]: Phase 32-01: idiom band cap is a single POST-band adjustment (band_for stays the single writer); idiom_floor='low' writes literal 'low' and keeps category=='idiom' (Finding NEW-2)
- [Phase ?]: Phase 32-02: vibe-ignore reasoned marker (within +/-2) rides the existing -50 silenced path; bare marker does NOT suppress but emits ONE synthetic low 'suppression' finding per bare occurrence (NOISE-02/03)
- [Phase ?]: Phase 32-02: synthetic bare-marker finding carries the FULL survivor shape (band 'low' + fixed non-null orchestrator_score + stable_hash), appended to kept AFTER the sub-threshold loop (A2 exempt -> visible) so review.md Phase 3/4 gates never halt (Finding #1); marker-line via _as_line -> null/odd line = line:null no crash (NEW-1)

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work — planning details, not blockers]

- [Phase 30] The per-key fail-safe is the load-bearing invariant for the WHOLE milestone — every later knob assumes a missing/malformed config degrades to its default without aborting. Phase 30 must lock this with `test_score.py` cases (unparseable file, invalid key type, out-of-range value, unknown band name) before the knobs that depend on it are built.
- [Phase 30] The Python<3.11 `tomllib`-unavailable path is an open plan-time call (degrade-to-no-config + warning vs a minimal fallback parser). Decide at Phase-30 plan time; the only hard requirement is that a missing parser never breaks a review.
- [Phases 31/32] `min_confidence`, `idiom_floor`, `thresholds`, and `vibe-ignore` all add NEW `score.py` envelope keys and MUST NOT move the frozen `GOLDEN_DIGEST` / banding math for the no-config default path — each phase needs a regression case proving default behavior is byte-stable.
- [All phases] SEQUENTIAL execution is mandatory: `score.py`/`test_score.py`/`commands/review.md`/`commands/deep-review.md` are shared across phases; a deep-review gate runs per phase (CLOSE-01 criterion 2 requires every phase clean before the bump).

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Framework agents | Express, Vue, Angular, Electron, React-Native agents (backlog Phase 999.1) | Deferred | v2.1 scoping |
| FastAPI depth | OpenAPI/contract checks; upload streaming/chunking refinements | Deferred | v2.1 scoping |
| Codex async | Background + second-pass folding (ASYNC-01) | Deferred | v2.2 scoping |
| Codex reach | Codex in `/review` via opt-in flag (ASYNC-02); configurable model/effort (ASYNC-03) | Deferred | v2.2 scoping |
| Whole-repo enhancements | Baseline-aware suppression (BASELINE-01), snapshot carry-forward (SNAPSHOT-01), Codex-over-whole-repo (CODEX-ALL-01) | Deferred | v2.3 scoping |
| Configurable & honest | Tunable config (CONFIG-01 / 999.4), measured cost (COST-01 / 999.12), docs pass (DOCS-01 / 999.13) | Deferred | v2.6 scoping |
| Dogfood hardening | Remaining v2.4/v2.5 Mediums — fix-agent prompt-injection hardening, `.planning/*-SUMMARY.md` force-tracking hygiene (HARDEN-01) | Deferred | v2.6 scoping |
| CI reach | gitleaks (SECRET-01 / 999.2), SARIF (SARIF-01 / 999.3), PR-posting (PRPOST-01 / 999.5) | Deferred | v2.6 scoping |
| Verification scaffold | Phase 24 `24-VERIFICATION.md` shows `human_needed` — stale gsd-verifier scaffold; EXPRESS-01 confirmed satisfied via 3-source audit + clean deep-review gate + integration check. Not a coverage gap. | Acknowledged | v2.7 close |
| v2.7 D-06 spot-checks | RN triage dual-emit (Haiku-prose) + expo-server-sdk carve-out — worth a live spot-check on real diffs | Deferred | v2.7 close |
| **33-02 orchestrator wiring** | LEGIBLE-01/02/03: `--codex` flag parse, always-announce Codex line, fix-loop label; plan is codex-APPROVED and frozen but NEVER EXECUTED — the config.py `codex` knob ships inert. ⚠ Plan needs REBASING before execution: the Fable remediation edited the same review.md regions 33-02 targets (Phase 0 gained the `$GUARD_PY` resolution block near the mode/scope sites the `$SCOPE_ARGS` normalizer rewrites; Phase 0.6's `--min-confidence` parse prose changed). | Deferred | v2.8 manual close |
| **Phase-34 efficacy proofs** | Planted-fixture smoke proof per v2.8 knob + per-phase deep-review gates (Phase 33's deep review also never ran) — the milestone shipped without its close-ritual evidence. | Deferred | v2.8 manual close |
| **Fable findings — remaining** | Answer-key fixes (A8 `/health` name-exemption, A16 axis-vs-site ambiguity); `security.md` critique pass (needs Opus); B3 product-quality harness execution (owner runtime, ~30 `/deep-review` runs — run against the FIXED system for a before/after story); all design challenges (H-CORE/H-DUP/H-LANE/B-SEV/B-XCONF/B-PROX/B-REWEIGHT) — no scorer restructuring until B3 measures; `CATEGORY_DOMAIN` twin proposals (ts `async-discipline`→correctness, express `input-validation`→security) — twin-policy calls, not calibration. | Deferred | v2.8 manual close |

## Session Continuity

Last session: 2026-07-01 (v2.8 ship + docs truth-up)
Stopped at: v2.8 SHIPPED (early manual close); no milestone scoped
Resume file: none — the Phase-33 `.continue-here.md` / HANDOFF.json are ANNOTATED as superseded
by the ship (do NOT blind-resume the milestone orchestrator; 33-02 needs a rebase first).

## Operator Next Steps

- **Option A (2.8.x follow-up):** rebase + execute 33-02 (LEGIBLE-01/02/03 wiring) against the
  post-Fable review.md/deep-review.md, run its deep-review gate, then optionally the Phase-34
  smoke proofs — ships as 2.8.1.
- **Option B (fold into v2.9):** /gsd:new-milestone scoping 33-02 + the Phase-34 proofs alongside
  the deferred Fable items (answer-key A8/A16, security.md pass, B3 execution) and the 999.x
  backlog.
- Either way, B3 (the catch-rate/FP-rate harness) is the highest-information next measurement —
  it now measures the FIXED system.
