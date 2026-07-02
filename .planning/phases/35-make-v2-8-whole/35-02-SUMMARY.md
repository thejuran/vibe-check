---
phase: 35-make-v2-8-whole
plan: 02
subsystem: docs
tags: [efficacy, proofs, codex, config, deep-review, evidence, prompt-only]

# Dependency graph
requires:
  - phase: 35-make-v2-8-whole
    plan: 01
    provides: "the REAL 33-02 orchestrator wiring (codex knob live in review.md/deep-review.md); phase-base sha d2ec9fcf60387119ac540a9a05d350bc7627a533"
  - phase: 30-config-surface-foundation
    provides: "config.py never-raise reader (Review B surface)"
provides:
  - "plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md — v2.9 evidence doc, verdict PROOF-01/PROOF-02 PASS (Phase 36 B3 report appends to this same doc)"
  - "PROOF-01: every v2.8 knob has a passing planted-fixture smoke proof (8 script-level rows + 3 live-run rows)"
  - "PROOF-02: the Phase-33 surface passed a clean 2-scoped-review gate (Review A = 33-02 diff range = ALSO the orchestrator Sub-step 5 gate; Review B = 33-01 config surface)"
affects: [36-b3-measurement, phase-37-close]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Script-vs-live proof split (D-04): deterministic knobs proven by one-command score.py/config.py stdin/env invocations; end-to-end config-honoring proven by in-session /deep-review live runs"
    - "Throwaway-fixture discipline (D-02): plant uncommitted → run → revert with a PER-PATH content/absence blocking gate (immune to a dirty worktree) + a secondary filtered repo-wide baseline"
    - "CONTENT-based cache pre-flight (D-08): grep the INSTALLED cache for the prose-only wiring (SCOPE_ARGS / 'Codex off via'), NOT a version check — a prose edit does not bump the version string"

key-files:
  created:
    - .planning/phases/35-make-v2-8-whole/35-02-SUMMARY.md
  modified:
    - plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md

key-decisions:
  - "L1 config fixture used [agents] disabled=[\"architecture\"] + [noise] min_confidence=40 — two knobs whose effect is observable in the RUN SHAPE (agent subtracted) and the FILTER (below-min-confidence drop), giving a crisp L1↔L2 contrast that isolates the knobs as the cause"
  - "Review A (d2ec9fc..HEAD) doubles as the orchestrator's Sub-step 5 per-phase deep-review gate — one review serves the PROOF-02 citation AND the phase's own code-review gate"
  - "All 7 reviewer-raised findings across both PROOF-02 reviews adjudicated NON-BLOCKING (4 false positives, 2 refuted-as-blocking legibility nits via adversarial verify, 1 non-blocking backlog item) — honest history recorded in RESULTS §PROOF-02, nothing papered over"
  - "sec-001 (symlinked .vibe-check.toml containment, CWE-61) filed as a hardening BACKLOG item, not an unresolved C/W: config.py is byte-frozen this phase, the config file is the owner's own-repo surface (not untrusted-PR), and there is no value-leak/exfil channel"

# Proof provenance (reproducibility)
proofs:
  script-level: "8 rows (min_confidence drop + honesty count, idiom_floor cap + off-sentinel, thresholds band, vibe-ignore reasoned/bare, malformed per-key degrade, codex off/auto/on + precedence) — all PASS, recipes in RESULTS §PROOF-01"
  live-runs:
    host-codex: "installed + authenticated (ready:true, codex-cli 0.133.0, ChatGPT login); timeout binary present (/opt/homebrew/bin/timeout)"
    cache-preflight: "CONTENT-asserted before run 1 — SCOPE_ARGS=13 in installed review.md, 'Codex off via'=2 in installed deep-review.md; process relaunched (the D-08 pause) + re-verified this session"
    L1: "planted .vibe-check.toml (disabled=[architecture], min_confidence=40) → architecture subtracted (5 native agents), 1 below-min-confidence drop, ✓ Codex joined — 2 findings (both targeting the proof scaffolding); PASS"
    L2: "no config → architecture NOT subtracted (6 native agents), 0 below-min-confidence drops (sub-threshold instead), no config-health line, ✓ Codex joined — 1 finding; v2.7-parity PASS"
    L3: "codex=\"off\" → Phase-2c step-0 OFF short-circuit fired FIRST, ZERO codex plumbing ran (no probe/launch/smoke), no codex-adversarial attribution in survivors, ⊘ Codex off via [noise] codex=off (quiet); PASS"
  proof-02:
    review-A: "range d2ec9fcf60387119ac540a9a05d350bc7627a533..HEAD (33-02 command-file diff) — clean, 0 blocking (arch CODEX_ON FP; bugs-001/002 refuted-as-blocking; bugs-003 FP)"
    review-B: "narrowed --all over plugins/vibe-check/scripts/config.py + test_config.py (33-01 surface, shas 83cbfae/80155e9/a1f44bc) — clean, 0 blocking (sec-001 backlog, sec-002 sub-warning, language-python clean)"
  byte-frozen: "score.py / test_score.py / config.py git diff --quiet held across all proofs; pytest -q = 356 passed, 221 subtests"
---

# 35-02 — Pay the v2.8 evidence debt (PROOF-01 knob proofs + PROOF-02 clean gate)

## What shipped

`plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` — the v2.9 milestone evidence doc, verdict
**PROOF-01/PROOF-02 PASS**. It closes the two deferred debts v2.8 shipped with: no planted-fixture
proof that each config knob works, and Phase 33's deep-review gate never running at the manual close.

## PROOF-01 — every v2.8 knob has a passing smoke proof

- **Script-level (8 rows, deterministic):** `min_confidence` pre-scoring drop + honesty count,
  `idiom_floor` cap + explicit-off sentinel, `thresholds` band parameterization, `vibe-ignore`
  reasoned-silence + bare synthetic-suppression, malformed-config per-key degrade, and `codex`
  off/auto/on + flag>config precedence — each a one-command `score.py`/`config.py` invocation with its
  exact recipe + observed output recorded (Task 1, commit c5adcc3).
- **Live (3 runs, in-session `/deep-review` against the REAL 33-02 wiring):** L1 planted config
  (knobs honored end-to-end — architecture subtracted, a finding dropped below the confidence floor,
  one Codex outcome line), L2 no config (byte-parity with v2.7 — architecture dispatched, no drops,
  no config-health line), L3 `codex="off"` (off short-circuit — zero Codex plumbing, one
  off-via-config line). All three preceded by the D-08 CONTENT-asserted cache resync + relaunch.

## PROOF-02 — the Phase-33 surface passed a clean deep-review gate

Two scoped reviews, both clean of unresolved critical/warning: **Review A** over the 33-02 diff range
`d2ec9fc..HEAD` (which also served as this phase's own Sub-step 5 gate), **Review B** a narrowed
`--all` over the 33-01 config surface (`config.py` + `test_config.py`). Seven findings were raised
across both; all seven adjudicated non-blocking (false positives, refuted-as-blocking legibility nits,
and one hardening backlog item), with the full honest adjudication recorded in the doc.

## Notable

- The L1↔L2 contrast is the load-bearing proof: the SAME fixture with vs. without a config file
  produces a different run shape (5 vs 6 agents) and a different filter outcome (1 vs 0
  below-min-confidence drops) — isolating the knobs as the cause, not some incidental effect.
- One real hardening idea surfaced (Review B sec-001): the config reader follows a symlinked
  `.vibe-check.toml` without realpath-containment against `$REPO_ROOT`. Filed for the backlog — it is
  the owner's own-repo surface (not the untrusted-PR surface guard.py already protects), has no
  value-leak channel, and config.py is byte-frozen this phase.
- Nothing was fixed during the proofs — every recipe and every review behaved as the wiring predicts.
  `score.py`/`test_score.py`/`config.py` stayed byte-frozen; the suite is green (356 + 221 subtests).
