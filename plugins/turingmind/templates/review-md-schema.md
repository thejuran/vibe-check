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

## Medium findings — dismissed
1. **{{file}}:{{line}}** — {{title}} ({{agent}})
   - **Decision:** dismissed
   - **Reason:** "{{user_reason}}"

## Intent doc alignment
{{architecture agent's notes about PLAN.md/SPEC.md alignment, if any}}

## Audit trail
See `.turingmind/state/<phase-id>.json.archived-{{date}}` for full per-pass history.
````

`{{scope_label}}` is the phase ID (e.g. "Phase 02 — code-review") in GSD mode, or "<repo>/<branch>" otherwise.

## Where it goes

- GSD phase mode: `.turingmind/REVIEW.md` (single artifact per repo — the latest finalize overwrites)

  Alternative for users who want per-phase history: archive previous REVIEW.md to `.turingmind/REVIEW-<phase-id>-<date>.md` before overwrite. (Implementation detail in M8.3.)

- Other modes: `.turingmind/REVIEW.md` same location.

The user is expected to `cp` this file somewhere persistent if they want to commit it to the project (typical: `cp .turingmind/REVIEW.md docs/reviews/<date>-<phase>.md && git add docs/reviews/`).
