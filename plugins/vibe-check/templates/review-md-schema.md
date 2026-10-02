---
name: REVIEW Artifact Schema
---

# REVIEW.md Schema

Written by `--finalize` to `.turingmind/REVIEW.md` (single file, fork schema only — no GSD-compat dual-write).

## Format

````markdown
# Code Review — {{scope_label}}

**Reviewed:** {{ISO date}}
**Baseline:** {{baseline_sha_short}} → {{head_sha_short}} ({{commits}} commits, {{loc}} LOC changed)
**Passes:** {{N}} ({{deep_count}}× deep-review, {{quick_count}}× review)
**Final verdict:** ✅ APPROVED

## Coverage
| Agent | Mode | Findings raised | Outstanding |
|---|---|---|---|
| security | deep | 2 | 0 |
| ... |

## Critical issues resolved
1. **{{file}}:{{line}}** — {{title}} ({{agent}}) — fixed in commit `{{sha_short}}`
...

## Warning issues resolved
[same format]

## Resolved by verification
1. **{{file}}:{{line}}** — {{title}} ({{agent}})
   - **Verified by:** {{resolution.source}} ({{resolution.agents}}) at pass {{resolution.at_pass}}, HEAD `{{head_sha_short}}`
   - **Reason:** "{{resolution.reason}}"

## Medium findings — dismissed
1. **{{file}}:{{line}}** — {{title}} ({{agent}}, {{band}})
   - **Decision:** dismissed
   - **Reason:** "{{user_reason}}"

## Findings deferred
1. **{{file}}:{{line}}** — {{title}} ({{agent}}, {{band}})
   - **Decision:** deferred
   - **Reason:** "{{user_reason}}"

## Intent doc alignment
{{architecture agent's notes about PLAN.md/SPEC.md alignment, if any}}

## Audit trail
See `.turingmind/state/<phase-id>.json.archived-{{date}}` for full per-pass history.
````

Section notes:

- **Coverage → Outstanding** counts open findings not closed by an owner decision or a verified resolution, so it reads 0 on a written REVIEW.md.
- **Resolved by verification** lists, for audit, every recheck- or fix-obsolete-resolved finding of ANY band: each `passes[].resolved[]` entry with its `resolution` evidence, AND each fix-obsolete verdict the owner finalized on without a rerun (its only record is root `fix_verdicts` — there is no `resolved[]` entry, so without this rule the resolution would vanish from REVIEW.md). Listed once per finding.
- **Medium findings — dismissed** (heading kept for continuity) lists every dismissal of any band: root `decisions` entries with `decision == "dismiss"` (the band is shown after the agent) UNION legacy root `medium_acknowledgments` entries.
- **Findings deferred** lists root `decisions` entries with `decision == "defer"`. Deferred findings did not block this REVIEW.md and remain the owner's to schedule.

`{{scope_label}}` is `"Phase <PHASE_ID>"` in GSD mode (e.g. `"Phase 02-code-review"` for phase dir `02-code-review`), or `"<repo>/<branch>"` otherwise. The PHASE_ID is the raw directory name under `.planning/phases/` — not a human-formatted title — so the cross-phase archive logic in `commands/review.md` can round-trip it via regex.

## Where it goes

- GSD phase mode: `.turingmind/REVIEW.md` (single artifact per repo — the latest finalize overwrites)

  Alternative for users who want per-phase history: archive previous REVIEW.md to `.turingmind/REVIEW-<phase-id>-<date>.md` before overwrite. The Writing-REVIEW.md subsection in `commands/review.md` implements this (cross-phase auto-archive on finalize).

- Other modes: `.turingmind/REVIEW.md` same location.

The user is expected to `cp` this file somewhere persistent if they want to commit it to the project (typical: `cp .turingmind/REVIEW.md docs/reviews/<date>-<phase>.md && git add docs/reviews/`).
