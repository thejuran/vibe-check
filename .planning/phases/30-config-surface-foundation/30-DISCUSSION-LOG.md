# Phase 30: Config surface foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions captured in CONTEXT.md — this log preserves the discussion.

**Date:** 2026-06-30
**Phase:** 30-config-surface-foundation
**Mode:** discuss (default)
**Areas surfaced:** tomllib fallback, what `thresholds` tunes, where config is read, warning verbosity/placement

## Gray Areas Presented

The design spec (`docs/superpowers/specs/2026-06-30-tunable-quieter-reviews-design.md`)
locks the milestone-level decisions (config-as-vehicle spine, enforcement-boundary
split, sequential execution, the three proving consumers, formula-untouched
constraint, precedence chain). The four open implementation gray areas were
presented as a multiSelect, each carrying a recommended default:

| Gray area | Recommendation presented |
|-----------|--------------------------|
| Python <3.11 `tomllib` fallback | Degrade-to-no-config + warning (not a bundled minimal parser) |
| What `thresholds` tunes | The `band_for()` band boundaries (critical/warning/medium), not the per-command finalize cutoffs |
| Where config is read | A small unit-testable Python helper the orchestrator calls (not Bash/prose in review.md) |
| Warning verbosity/placement | One dedicated config-health line near the report top |

## User Selection

The owner did not select any gray area to discuss interactively. On a confirm
prompt, the owner chose **"Yes, use your recommendations"** — adjudicating
implementation details is the orchestrator's job, not the owner's (consistent with
the project's division-of-labor: technical decisions are owned by Claude, framed
for product impact). All four locked to the recommended defaults.

## Decisions Recorded

- **D-01:** tomllib<3.11 → degrade-to-no-config + warning (resolves STATE.md open call).
- **D-02:** `thresholds` tunes `band_for()` band boundaries; per-command `THRESHOLDS`
  cutoffs untouched; default path stays byte-stable (formula-untouched invariant).
- **D-03:** Config read by a small unit-testable Python helper; `score.py` stays a
  pure function (no file I/O); orchestrator passes resolved values into the envelope
  / acts on dispatch knobs directly.
- **D-04:** Per-key fail-safe warnings as one dedicated config-health line near the
  report top; absent file → no warning (zero-config silent).

## Deferred Ideas

- min_confidence (Phase 31), idiom_floor + vibe-ignore (Phase 32), Codex legibility
  + fix-loop default (Phase 33) — all later phases, redirected out of Phase 30 scope.
- Formula rewrite / agent_confidence re-derivation — forbidden by spec §5.

## Claude's Discretion (handed to planner)

- Helper filename/signatures, envelope key name/shape for `thresholds`, exact
  warning wording, which `band_for` literal each `thresholds` sub-key replaces,
  README schema-doc format.
