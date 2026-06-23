# Architecture

Adapted from the upstream `turingmindai/turingmind-code-review` project.

## Why a fork

Upstream was active for two days in January 2026, then dormant. Useful core (per-domain agents, confidence scoring, filtered-issues transparency) but missing modern infrastructure.

## Two-layer design

- **Orchestrator** (`commands/*.md`): scope, dispatch, scoring, state, artifact writing.
- **Engine** (`agents/*.md` + `templates/*.md`): per-domain prompts, JSON schema, scoring rules.

New languages/frameworks are pure agent additions.

## Preserved from upstream

1. **Confidence-scoring rubric with asymmetric penalties** (−50 pre-existing, −50 silenced).
2. **Filtered-issues transparency.**
3. **Per-domain agents.**

(Upstream's *diff-style fixes required* property was dropped in this fork: detection agents report findings only — patching is decoupled into the semantic `fix` agent (`agents/fix.md`), dispatched in Phase 5.)

## New

- Real parallel `Task` dispatch.
- Model tiering: Sonnet for `/review`; for `/deep-review`, the `<TOP>` tier (Opus by default, Fable opt-in) on the `architecture` and `bugs` agents. No thinking parameter is passed (deep-review forbids it).
- Read intent docs from the resolved phase dir (flat `.planning/phases/<id>/` or milestone-nested `.planning/milestones/<m>-phases/<id>/` — the tool resolves both layouts).
- Multi-pass stateful loop (`.turingmind/state/`).
- `.turingmind/REVIEW.md` artifact (single file, fork schema).

## Namespace ownership

The tool reads from `.planning/` and the repo but **only writes to `.turingmind/`**. Never writes to `.planning/` — that belongs to GSD. `.turingmind/` is gitignored by default; the user `cp`s `REVIEW.md` somewhere persistent if they want it tracked.

## Removed

- `hooks/`, `scripts/install-hooks.sh` — fragile stdout-grep git hooks. User invokes manually.

## Cost

| Command | Relative cost | Use |
|---|---|---|
| `/review <phase>` | cheap (single Sonnet pass) | Iteration |
| `/deep-review <phase>` | several times a quick pass (top-tier multi-agent) | Final pass |

A `/review` pass is cheap; a `/deep-review` pass costs several times more. For current dollar
figures, see the Cost note in `commands/deep-review.md` (the canonical source) — they are not
re-pinned here to avoid drift. A typical loop is a few quick passes plus one deep pass.

## Design history

This fork was designed spec-first and plan-first; those documents are kept in the
author's private notes and are not part of this repository.
