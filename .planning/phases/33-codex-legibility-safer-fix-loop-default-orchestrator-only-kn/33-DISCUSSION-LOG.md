# Phase 33: Codex legibility + safer fix-loop default - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in 33-CONTEXT.md — this log preserves the discussion.

**Date:** 2026-07-01
**Phase:** 33-codex-legibility-safer-fix-loop-default-orchestrator-only-kn
**Mode:** discuss (default)
**Areas discussed:** LEGIBLE-03 target, off/auto/on semantics, Always-announce scope, config.py vs pure-prose (all four selected)

## Pre-discussion scouting (informed the gray areas)

- **LEGIBLE-03 surprise:** `review.md` Step A (apply-fixes menu) ALREADY has no
  "(Recommended)" — it is a documented "neutral menu." The only "(Recommended)" left in the
  fix loop is Step C option 1 (rerun-after-fixes), which is safety-positive guidance.
- **LEGIBLE-01 today:** Codex prints a line only on kickoff (launch) or on skip; there is NO
  line on the successful joined+collected path, and none for a new off-via-config case.
- **LEGIBLE-02 home:** `config.py` already hosts orchestrator-only knobs (`disabled`,
  `top_model`) and reserves the `--codex` precedence slot (line 253).

## Questions asked & selections

### Area 1 — LEGIBLE-03 target
| Options presented | Selection |
|---|---|
| Leave Step C + add guard note (Rec) / Strip Step C too / Strip + plain hint | **Leave Step C, add a guard note** |
- Notes: Step A already un-nudged → LEGIBLE-03 literal target met. Step C "(Recommended)"
  is safety-positive (verify fixes), kept. Concrete change = a guard comment at Step A so a
  future edit can't re-add an apply-all nudge. → D-05/D-06/D-07.

### Area 2 — off/auto/on semantics
| Options presented | Selection |
|---|---|
| off/auto/on with on==auto+louder (Rec) / on forces availability hard-fail / bare on-off toggle | **off/auto/on, on==auto+louder** |
- Notes: `on` must NEVER override the correctness (fail-closed) skips — forcing a
  non-representable diff would silently review the wrong code (SAFE-01 violation). `on`
  changes only the PROMINENCE of a skip, not the dispatch decision. `--codex` takes the same
  three values; precedence flag > toml > default(auto). → D-08/D-09/D-10.

### Area 3 — Always-announce scope (LEGIBLE-01)
| Options presented | Selection |
|---|---|
| One outcome line at collection (Rec) / fold into kickoff / two lines always | **One outcome line at collection** |
- Notes: true outcome known only post-collection (a launch can time out). One unconditional
  Phase-3 outcome line: joined (N/M) / skipped:<slug> / off-via-config. Existing kickoff
  progress line stays, launch-only. Reuse existing reason slugs. → D-11/D-12/D-13.

### Area 4 — config.py vs pure-prose
| Options presented | Selection |
|---|---|
| config.py-validated knob (Rec) / pure orchestrator-markdown parsing | **config.py-validated knob** |
- Notes: "prose only" = no score.py/scoring-math change, which a config.py knob honors
  (codex is orchestrator-only, never in the score.py envelope). Gets test_config.py coverage
  like every other knob; matches Phase 30 D-03. → D-14.

## Deferred ideas
- `on`-forces-availability-hard-fail (rejected Area-2 option 2) — future milestone if a hard
  "require Codex" guarantee is ever wanted.
- Temp-worktree checkout to make non-representable diffs Codex-reviewable — pre-existing
  deferred note; would let `on` genuinely run on --all/uncommitted-tail.
- Flipping Codex default to `off` — explicitly out of scope (default stays `auto`).

## Claude's discretion (locked as flexible)
- Exact glyphs/format of the outcome line + on-prominence styling.
- Exact wording of the Step A guard comment.
- Whether the off-via-config line names toml-vs-flag as the deciding source.
