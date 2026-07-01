---
phase: 30-config-surface-foundation
plan: 03
subsystem: orchestrator
tags: [config, vibe-check, orchestrator-wiring, review.md, deep-review.md, thresholds, disabled, top_model, degrade-not-abort]

# Dependency graph
requires:
  - phase: 30-config-surface-foundation (plan 01)
    provides: config.py load_config + the __main__ shim (REPO_ROOT env in -> {values,warnings} JSON, exit 0 always) this plan invokes; the (values,warnings) contract + the opus/fable allowlist it consumes
  - phase: 30-config-surface-foundation (plan 02)
    provides: score.py's optional `thresholds` envelope key (band_for parameterized, default-inert/byte-stable when absent) this plan injects into the Phase-3 envelope
provides:
  - "review.md Phase 0.6 — the NEW UNCONDITIONAL config-resolution step (between Phase 0.5 and 0.7): dev-safe $CONFIG_PY resolution that DEGRADES (never exit 1), binds its own CONFIG_REPO_ROOT, invokes config.py ONCE, carries $CONFIG_THRESHOLDS/$CONFIG_DISABLED/$CONFIG_TOP_MODEL/$CONFIG_WARNINGS forward on every mode + both commands"
  - "thresholds -> score.py envelope (byte-stable: key omitted on a zero-config run)"
  - "disabled -> Phase-2 dispatch subtraction (both review.md and deep-review.md), core-agent (bugs/security) disable announced on the config-health line, never silent"
  - "top_model resolved env > toml > default(opus) with the shared opus/fable allowlist at deep-review.md:55 (the authoritative top-tier site)"
  - "config-health line near the top of the Phase-4 report — renders $CONFIG_WARNINGS + disabled-core announcements, silent on empty (CONFIG-01)"
  - ".vibe-check.toml schema documented in the README (three keys + defaults + precedence + zero-config back-compat + two-layer band-vs-cutoff note)"
affects: [phase-31, phase-32, phase-33, phase-34]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dev-safe helper resolution with an INVERTED terminal arm: clone the $SCORE_PY working-tree->cache->marketplace order but DEGRADE-not-fail-closed for the OPTIONAL config reader (vs the MANDATORY scorer's exit 1) — the read+precedence+fail-safe pattern Phases 31-33 reuse"
    - "Resolve-once-carry-forward: config.py invoked ONCE in an unconditional early phase, parsed into shell vars every downstream consumer (dispatch/envelope/report) + the delegated command reads — NO second read on any path"
    - "Degrade-even-if-the-helper-misbehaves: a nonzero exit OR unparseable stdout is treated as all-defaults + one config-health warning, distinct from the mandatory-scorer fail-closed gate"

key-files:
  created:
    - .planning/phases/30-config-surface-foundation/30-03-SUMMARY.md
  modified:
    - plugins/vibe-check/commands/review.md
    - plugins/vibe-check/commands/deep-review.md
    - README.md

key-decisions:
  - "Phase 0.6 placed BETWEEN Phase 0.5 and 0.7 (both unconditional + both delegated to /deep-review) so the config read fires on EVERY mode (GSD/diff/PR/range/--all) and BOTH commands, before any dispatch decision — NOT in Phase 1.5 (GSD-only) and NOT in any $ALL_MODE/$PHASE_ID-gated block (Finding #1 r1+r2+r3)"
  - "Phase 0.6 binds its OWN CONFIG_REPO_ROOT via git rev-parse, NOT the --all-only $ROOT (empty on the common modes) — reusing $ROOT would silently degrade config to no-config on plain diff/PR/range/GSD (Finding #1a)"
  - "$CONFIG_PY terminal arm INVERTS $SCORE_PY's exit 1: a missing config reader degrades to all-defaults (the reader is optional, the scorer is mandatory) — Pitfall 4"
  - "thresholds key OMITTED on a zero-config run (byte-identical v2.7 banding); injected only for a valid non-default override (D-02)"
  - "disabled subtracted BEFORE the Dispatching-N announcement in both files; a disabled core agent (bugs/security) is announced on the config-health line, non-core disables are silent (Pitfall 5)"
  - "top_model precedence env > toml > default(opus) at deep-review.md:55, reusing the SAME opus/fable allowlist + fallback + one-time warning for BOTH sources so env and toml cannot diverge (Pitfall 6); thresholds stays review.md-only (inherited by deep via Phase-3 delegation)"
  - "deep-review.md:36 enumeration edited to include 0.6 (0.5, 0.6, 0.7) — the enumerated list is authoritative for the deep path, so adding Phase 0.6 to review.md alone would be inert on every /deep-review run (Finding #1b)"

requirements-completed: [CONFIG-01, CONFIG-02, CONFIG-04]

# Metrics
duration: 4min
completed: 2026-07-01
---

# Phase 30 Plan 03: Orchestrator config wiring Summary

**Wired the three proving consumers into the orchestrator: a NEW unconditional Phase 0.6 in `review.md` reads `.vibe-check.toml` once per run (dev-safe, degrade-not-abort), threading `thresholds` into the score.py envelope byte-stably, subtracting `disabled` agents before dispatch in both command files (core-agent disable announced), resolving `top_model` env>toml>default at `deep-review.md:55`, and rendering a config-health line that is silent on a zero-config repo — with the schema documented in the README.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-07-01T00:28:50Z
- **Completed:** 2026-07-01T00:32:40Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- **Phase 0.6 — the unconditional config read (the hardest-won fix, codex Finding #1 rounds 1-4).** Added a NEW `## Phase 0.6 — Resolve config` step in `review.md` strictly BETWEEN Phase 0.5 (:379) and Phase 0.7 (now :474) — both unconditional and both delegated to `/deep-review` — so `.vibe-check.toml` is read exactly ONCE on EVERY mode (GSD phase / plain diff / PR / range / `--all`) and BOTH commands, before any dispatch decision that consumes it. It is NOT inside Phase 1.5 (GSD-only) and NOT inside any `$ALL_MODE`/`$PHASE_ID`-gated block.
- **Own repo root (Finding #1a).** Phase 0.6 binds its OWN `CONFIG_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)` and invokes `CONFIG_JSON=$(REPO_ROOT="$CONFIG_REPO_ROOT" python3 "$CONFIG_PY")` — never the `--all`-only `$ROOT` (empty on the common modes, which would silently degrade config to no-config).
- **Dev-safe degrade-not-abort resolution (Pitfall 4).** `$CONFIG_PY` clones the `$SCORE_PY` working-tree → cache → marketplace resolution ORDER but INVERTS the terminal arm: a missing config helper degrades to all-defaults (no `exit 1`) — the config reader is optional where the scorer is mandatory. A nonzero exit OR unparseable stdout also degrades to all-defaults + one config-health warning (Finding #2 corollary), so the review never aborts on config.
- **thresholds → envelope (byte-stable).** The Phase-3 score.py envelope now sources a `thresholds` key from the carried-forward `$CONFIG_THRESHOLDS`; on a zero-config run the key is OMITTED so banding is byte-identical to v2.7 (frozen GOLDEN_DIGEST unmoved), and a non-default dict is injected only for a valid override.
- **disabled → dispatch, both files.** `$CONFIG_DISABLED` is subtracted from the Phase-2 Selection set BEFORE the `Dispatching N agents` announcement in `review.md`, and from the deep Selection set in `deep-review.md`. A disabled core agent (`bugs`/`security`) is HONORED but ANNOUNCED on the config-health line (never silent); non-core disables are silent.
- **top_model env > toml > default (deep-review.md:55).** Extended the authoritative top-tier resolution to `$VIBE_CHECK_TOP_MODEL` (env, wins) > `$CONFIG_TOP_MODEL` (toml) > `opus`, reusing the SAME opus/fable allowlist + fallback-to-opus + one-time warning for both sources. `deep-review.md:36`'s delegated-phase enumeration now includes `0.6` (Finding #1b) so `/deep-review` actually runs the read.
- **config-health line + README schema.** A one-block config-health render near the top of the Phase-4 report shows `$CONFIG_WARNINGS` + disabled-core announcements as inert display text, silent on empty warnings (CONFIG-01). The README's Configuration section documents the three keys, defaults, precedence chain, zero-config back-compat, and the two-layer band-vs-cutoff distinction; the later-phase `[noise]` keys are shown commented and marked not-yet-active.

## Task Commits

Each task was committed atomically:

1. **Task 1: Phase 0.6 config read + thresholds envelope + config-health line (review.md)** — `0118885` (feat)
2. **Task 2: disabled + top_model enforcement across review.md and deep-review.md** — `263230e` (feat)
3. **Task 3: document the .vibe-check.toml schema in the README** — `b7e6e85` (docs)

## Files Created/Modified

- `plugins/vibe-check/commands/review.md` (modified) — NEW unconditional Phase 0.6 (dev-safe degrade resolution + one-time invocation + carried-forward vars + zero-config/misbehavior degrade prose); `thresholds` key added to the Phase-3 envelope build (byte-stable when absent); `$CONFIG_DISABLED` subtraction before the Phase-2 dispatch announcement with core-agent announce; the top_model consistency note; the Phase-4 config-health line.
- `plugins/vibe-check/commands/deep-review.md` (modified) — line 36 delegated-phase enumeration extended to `0.5, 0.6, 0.7`; line 55 top-tier resolution extended to env>toml>default with the shared allowlist; the deep Selection table's `$CONFIG_DISABLED` subtraction with the explicit "thresholds is review.md-only, inherited by delegation" note.
- `README.md` (modified) — `.vibe-check.toml` schema subsection under Configuration (fenced TOML example + keys table + precedence + zero-config back-compat + two-layer note + commented not-yet-active `[noise]` keys).

## Decisions Made

None beyond the plan's locked specifics — all D-01..D-04 decisions and the four adversarial-review findings (#1 unconditional Phase-0.6 placement, #1a own-repo-root, #1b deep enumeration, #2 degrade-on-misbehavior, #4 two-layer doc) were followed exactly as written. See frontmatter `key-decisions`.

## Deviations from Plan

None - plan executed exactly as written. No script changes (those landed in Plans 01/02); the full 191-test suite is unchanged and still green. The frontmatter `allowed-tools` line in both command files is byte-unchanged (python3 runs under the existing compound-Bash convention).

## Issues Encountered

None. The 191-test baseline was green at start and end. One verification grep (`CONFIG_JSON=$(REPO_ROOT`) initially returned empty because the invocation line is indented inside an `if` block — a precise grep (`CONFIG_JSON=.*REPO_ROOT="\$CONFIG_REPO_ROOT"`) confirmed it binds `CONFIG_REPO_ROOT`, not `$ROOT`. No code impact.

## Threat Surface Scan

No new security-relevant surface beyond the plan's `<threat_model>`. The config-health line renders config.py's warning strings (KEY + fixed reason) as inert display text and does NOT re-interpolate raw config VALUE text (T-30-12/V5); `top_model` reaches a Task dispatch only through the opus/fable allowlist (config.py pre-validated it, deep-review.md re-validates both sources — T-30-09); a disabled core agent is announced, never silent (T-30-10); an unresolvable/misbehaving config helper degrades to defaults and never aborts the review (T-30-11); the zero-config path omits the thresholds key so default banding is byte-stable (T-30-13); and the config read is unconditional/every-mode/deep-reachable so no mode silently ignores `.vibe-check.toml` (T-30-14). No packages installed (prose/doc only — T-30-SC).

## Known Stubs

None. All three files are fully-wired orchestrator prose consuming the real config.py contract (Plan 01) and the real score.py envelope key (Plan 02). The `[noise]` keys shown commented in the README are explicitly marked not-yet-active (Phases 32-33) per the plan — a documented future-phase pointer, not a stub in this plan's scope.

## User Setup Required

None. `.vibe-check.toml` is entirely optional; a repo without one runs exactly as v2.7.

## Next Phase Readiness

- The read+precedence+fail-safe pattern (unconditional early read, resolve-once-carry-forward, degrade-not-abort, per-key config-health warnings) is now established end-to-end and is the template Phases 31-33 consume for `min_confidence` / `idiom_floor` / codex-legibility.
- `thresholds` proves the script-enforced path (config → score.py envelope); `disabled`/`top_model` prove the orchestrator-enforced path (config → dispatch) — both loops closed.
- The `$CONFIG_*` carried-forward vars and Phase 0.6's invocation shape are stable for later phases to extend with additional knobs (the parse step already reads the full `values` object; adding a knob is additive).

## Self-Check: PASSED

- Files verified present: review.md, deep-review.md, README.md all modified on disk; 30-03-SUMMARY.md created.
- Commits verified in git log: `0118885` (feat), `263230e` (feat), `b7e6e85` (docs) all FOUND.
- Full suite `python3 -m unittest` → 191 tests OK (no script regression — this plan touched no scripts).
- Plan verification greps: CONFIG_PY=11 (>=2); Phase 0.6 strictly between 0.5 and 0.7; invocation binds CONFIG_REPO_ROOT (not $ROOT); deep enumeration includes 0.6; disabled in both files (review=5, deep=2); deep top_model env>toml>default present; README .vibe-check.toml=4.

---
*Phase: 30-config-surface-foundation*
*Completed: 2026-07-01*
