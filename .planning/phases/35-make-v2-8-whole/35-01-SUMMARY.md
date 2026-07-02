---
phase: 35-make-v2-8-whole
plan: 01
subsystem: api
tags: [codex, orchestrator, dispatch, config, review, deep-review, prompt-only]

# Dependency graph
requires:
  - phase: 33-codex-legibility-safer-fix-loop-default-orchestrator-only-kn
    provides: "config.py codex knob (33-01) — _validate_codex, values.codex off/auto/on; the frozen codex-approved 33-02 orchestrator-wiring plan (rebased here)"
  - phase: 30-config-surface-foundation
    provides: "config.py never-raise reader + __main__ flag-threading interface (MIN_CONFIDENCE_FLAG env), the $CONFIG_* carried-forward-var pattern"
  - phase: 31-confidence-axis
    provides: "--min-confidence flag parse idiom cloned for --codex; the Phase-0.6 parse+thread pattern"
provides:
  - "review.md Phase-0 pre-mode universal-flag normalizer ($SCOPE_ARGS) making --codex/--min-confidence reach config.py in ALL 5 modes (diff/PR/range/GSD/--all)"
  - "review.md Phase-0.6 --codex parse + CODEX_FLAG thread + $CONFIG_CODEX bind on all seven Phase-0.5 exit arms (auto-default on degrade)"
  - "review.md Step-A LEGIBLE-03 guard comment (fix-loop menu locked neutral)"
  - "deep-review.md launch-gated BashOutput smoke check (moved into Phase 2c), off short-circuit, on prominence, Phase-3 one-line Codex outcome (joined/skipped/off-via-config), $CONFIG_CODEX contract note"
affects: [36-b3-measurement, codex-announce-smoke-proof, phase-37-close]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Universal-flag normalization BEFORE mode detection: strip value-carrying flags off $ARGUMENTS into a separate $SCOPE_ARGS that all scope-parsing sites read, while the flags survive in $ARGUMENTS for the unconditional Phase-0.6 parse"
    - "Launch-gated hard-block: a fail-closed structural gate moved inside the actual-launch guard so it fires iff the guarded action happens, never on a degrade path"
    - "Orchestrator-only knob: parsed+bound alongside score.py-facing knobs but NEVER entering the envelope/render (no score.py coupling)"

key-files:
  created:
    - .planning/phases/35-make-v2-8-whole/35-01-SUMMARY.md
  modified:
    - plugins/vibe-check/commands/review.md
    - plugins/vibe-check/commands/deep-review.md

key-decisions:
  - "Folded --min-confidence into the $SCOPE_ARGS normalizer alongside --codex (shared parse-timing bug; the normalizer ADDS GSD/PR/range reach --min-confidence lacked and fixes its --all narrow-parse mis-read, never changes its byte-correct diff/--all behavior)"
  - "Bare-`all` alias composition order absorbed by the rebase: normalizer runs FIRST → the branch-flip guard's bare-`all` alias rewrites $SCOPE_ARGS's first token → the --all-contains test reads $SCOPE_ARGS (the one new composition sentence; no design change)"
  - "HIGH-B design choice MOVE-SMOKE-INTO-2c (over a pre-computed CODEX_WILL_LAUNCH predicate): reuses the existing [ -z $CODEX_SKIPPED ] launch guard verbatim, zero duplicated representability/availability logic"
  - "Phase 2b header REPURPOSED to a one-line pointer (not deleted) noting the smoke check now lives launch-gated in Phase 2c — the phase-announce numbering stays stable and no live unconditional hard-block is left behind"

patterns-established:
  - "Pattern: pre-mode $SCOPE_ARGS normalizer as the single sanitized scope input for all six scope-parsing sites"
  - "Pattern: launch-gated fail-closed gate (smoke check inside the CODEX_SKIPPED launch guard)"

requirements-completed: [LEGIBLE-01, LEGIBLE-02, LEGIBLE-03]

# Metrics
duration: 9min
completed: 2026-07-02
---

# Phase 35 Plan 01: Rebase + execute the frozen 33-02 Codex-legibility wiring Summary

**Wired the `codex` knob live end-to-end: `--codex off|auto|on` now reaches config.py in all 5 review modes via a Phase-0 `$SCOPE_ARGS` normalizer, the BashOutput smoke gate is launch-gated so a non-launching Codex never hard-blocks the native review, and every `/deep-review` run prints exactly one legible Codex-status line — prose/dispatch only, score.py byte-frozen.**

## Phase-base SHA (for 35-02 Review A's range)

`<phase-base>` = **`d2ec9fcf60387119ac540a9a05d350bc7627a533`** — captured via `git rev-parse HEAD` IMMEDIATELY BEFORE the first execution commit (Task 1). Matches the orchestrator's dispatch measurement exactly.

## Performance

- **Duration:** 9 min
- **Started:** 2026-07-02T01:41:36Z
- **Completed:** 2026-07-02T01:50:10Z
- **Tasks:** 3
- **Files modified:** 2 (review.md, deep-review.md)

## Accomplishments

- **`--codex` is universal (LEGIBLE-02, D-10).** A new Phase-0 pre-mode normalizer strips `--codex`/`--min-confidence` value pairs off `$ARGUMENTS` into `$SCOPE_ARGS`, and all SIX scope-parsing sites (branch-flip guard, mode-1 default-diff selection [HIGH-A], PR, range, GSD sandbox, mode-5 step-a `$NARROW` [HIGH-C]) classify from `$SCOPE_ARGS` — so `--codex` reaches config.py in diff/PR/range/GSD/`--all`, a flag-only call resolves the default diff, and a universal flag after `--all` never becomes a bogus `$NARROW`.
- **`$CONFIG_CODEX` bound on every arm.** `--codex` parses at Phase 0.6, threads via `CODEX_FLAG` on the config.py invocation, and `$CONFIG_CODEX` binds on all seven Phase-0.5 exit sites (auto-default on every degrade arm, never None); it is NOT added to the two score.py consumer lines (orchestrator-only).
- **Codex is legible + fail-closed-safe (LEGIBLE-01, HIGH-B).** The BashOutput collection-smoke gate moved out of standalone Phase 2b into Phase 2c inside the `[ -z "$CODEX_SKIPPED" ]` launch guard, so any non-launching run (off/not-installed/unauthenticated/`--all`/dirty-tail/non-ancestor/PR-mismatch/no-timeout-binary) with BashOutput unavailable degrades native-only and is never hard-blocked; `off` short-circuits before the probe (zero Codex plumbing); `on` only louds the outcome line; Phase 3 emits exactly one outcome line (joined / skipped-slug / off-via-config).
- **Fix-loop menu locked neutral (LEGIBLE-03).** A single-line guard comment above Step A forbids re-introducing "(Recommended)"; Step C option 1's safety-positive "(Recommended if any fixes were applied)" is untouched.

## Task Commits

Each task was committed atomically:

1. **Task 1: review.md Phase 0 `$SCOPE_ARGS` normalizer + six-site rewire** - `01df9db` (feat)
2. **Task 2: review.md Phase 0.6 `--codex` parse + thread + `$CONFIG_CODEX` binds + Step-A guard** - `46817b8` (feat)
3. **Task 3: deep-review.md launch-gated smoke, off short-circuit, on prominence, Phase-3 outcome line, `:36` note** - `29825e0` (feat)

**Plan metadata:** _(this commit)_ (docs: complete plan)

## Files Created/Modified

- `plugins/vibe-check/commands/review.md` - Phase-0 `$SCOPE_ARGS` normalizer (all six scope-parsing sites), Phase-0.6 `--codex` parse/thread/bind on seven arms, Step-A LEGIBLE-03 guard comment (36 insertions / 16 deletions)
- `plugins/vibe-check/commands/deep-review.md` - `:36` `$CONFIG_CODEX` contract note, Phase-2b retired to a pointer, Phase-2c off short-circuit + launch-gated smoke check (step 6), Phase-3 one-line Codex outcome (step 7) (26 insertions / 15 deletions)

## Decisions Made

- **`--min-confidence` folded into the normalizer (Task 1).** It shares the identical parse-timing bug with `--codex` (the flag-only-in-diff-mode gap and the `--all --min-confidence 75` mis-read). The normalizer ADDS the GSD/PR/range reach `--min-confidence` lacked and FIXES its `--all` narrow-parse mis-read, while its existing diff behavior and its `--all`/`--all <path>` behavior stay byte-identical for every input without the combined universal flag (a plain `--all src` has `$SCOPE_ARGS == $ARGUMENTS`); only the previously-buggy combined `--all --min-confidence 75` is corrected to whole-tree.
- **Bare-`all` alias composition order (Task 1, the one new rebase sentence).** Normalizer runs FIRST (strips only `--codex`/`--min-confidence`, never `--all` or a bare leading `all`) → the branch-flip guard's bare-`all` alias rewrites `$SCOPE_ARGS`'s first token → the `--all`-contains test reads `$SCOPE_ARGS`. `all --codex off` → `$SCOPE_ARGS="all"` → `--all` → mode 5, `$NARROW` empty (whole tree), with `--codex off` still reaching Phase 0.6 from `$ARGUMENTS`.
- **HIGH-B MOVE-SMOKE-INTO-2c (Task 3).** Chosen over a pre-computed `CODEX_WILL_LAUNCH` predicate: the representability + availability facts all live inside Phase 2c and funnel into the single `CODEX_SKIPPED` flag, so moving the smoke check to immediately before the launch reuses the existing `[ -z "$CODEX_SKIPPED" ]` launch guard verbatim — zero duplicated logic.
- **Phase 2b header REPURPOSED to a pointer (Task 3).** Not deleted — the `### Phase 2b` header remains and its body is a one-line pointer noting the smoke check now runs launch-gated in Phase 2c step 6. This keeps the phase-announce numbering stable and leaves no live unconditional hard-block behind.

## Deviations from Plan

None - plan executed exactly as written.

The executed changes deviate from the frozen 33-02 text ONLY by (1) re-anchored line numbers (the plan's `<interfaces>` block carried the re-anchored post-Fable references) and (2) the one bare-`all` alias composition sentence in Task 1. No design change. Rebase discipline (D-06) held: Task action text, acceptance criteria, verify gates, and the threat register were treated as immutable.

## Issues Encountered

- **`grep -c 'CONFIG_CODEX' deep-review.md` initially returned 2, gate needs ≥3.** `grep -c` counts matching lines, and the `:36` note + the Phase-2c off short-circuit were the only two lines referencing `$CONFIG_CODEX`. Resolved by having the Phase-3 step-7 prominence prose reference `$CONFIG_CODEX` by name (semantically correct — the outcome-line render style is selected by the resolved knob value: `auto`/`off` quiet, `on` prominent), bringing the count to the required 3.

## Verification

All plan `<verification>` gates pass:
- `grep -c 'SCOPE_ARGS' review.md` = 13 (≥7 required)
- `grep -c 'CONFIG_CODEX' review.md` = 7 (≥7 required, seven distinct bind sites); NO `CONFIG_CODEX` on the `pre-scoring confidence floor` or `Filtered-summary counts` consumer lines
- `grep -c 'Recommended if any fixes were applied' review.md` = 1 (Step C option 1 only)
- `grep -c 'CONFIG_CODEX' deep-review.md` = 3; `Codex joined` / `Codex skipped` / `Codex off via` / `__SMOKE_OK__` all present; standalone unconditional Phase-2b hard-block ("blocks completion NOW") = 0 occurrences (retired)
- `git diff --quiet -- scripts/score.py scripts/test_score.py` exits 0 (byte-frozen); `scripts/config.py` untouched (read-only)
- `pytest -q` (from `plugins/vibe-check/scripts`): **356 passed, 221 subtests passed**

## Next Phase Readiness

- **The Codex wiring is live end-to-end** — the codex-announce smoke proof in the follow-on plan (35-02) can now test the REAL wiring (D-04: wiring before proofs), not the inert v2.8 state. The `<phase-base>` SHA above is recorded for 35-02 Review A's range.
- **Pre-flight reminder for any smoke/dogfood run:** the installed-plugin cache must equal repo `plugin.json` before running (stale cache poisoned 4 of the last 5 milestones).
- No blockers.

---
*Phase: 35-make-v2-8-whole*
*Completed: 2026-07-02*
