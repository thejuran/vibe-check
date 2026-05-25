# Architecture — Personal Fork (v2.0.0-local)

Local-only fork of `turingmindai/turingmind-code-review`.

## Why a fork

Upstream was active for two days in January 2026, then dormant. Useful core (per-domain agents, confidence scoring, diff-style fixes, filtered-issues transparency) but missing modern infrastructure.

## Two-layer design

- **Orchestrator** (`commands/*.md`): scope, dispatch, scoring, state, artifact writing.
- **Engine** (`agents/*.md` + `templates/*.md`): per-domain prompts, JSON schema, scoring rules.

New languages/frameworks are pure agent additions.

## Preserved from upstream

1. **Confidence-scoring rubric with asymmetric penalties** (−50 pre-existing, −50 silenced).
2. **Filtered-issues transparency.**
3. **Diff-style fixes required.**
4. **Per-domain agents.**

## New

- Real parallel `Task` dispatch.
- Model tiering: Sonnet for `/review`, Opus + thinking on architecture for `/deep-review`.
- Read intent docs from `.planning/phases/<id>/`.
- Multi-pass stateful loop (`.turingmind/state/`).
- `.turingmind/REVIEW.md` artifact (single file, fork schema).

## Namespace ownership

The tool reads from `.planning/` and the repo but **only writes to `.turingmind/`**. Never writes to `.planning/` — that belongs to GSD. `.turingmind/` is gitignored by default; the user `cp`s `REVIEW.md` somewhere persistent if they want it tracked.

## Removed

- `hooks/`, `scripts/install-hooks.sh` — fragile stdout-grep git hooks. User invokes manually.

## Cost

| Command | Per-pass | Use |
|---|---|---|
| `/review <phase>` | ~$0.50 | Iteration |
| `/deep-review <phase>` | ~$1.80 | Final pass |

Typical loop (3 quick + 1 deep) ≈ $3.30.

## Where the design lives

- Spec: `/Users/julianamacbook/docs/superpowers/specs/2026-05-24-turingmind-fork-design.md`
- Plan: `/Users/julianamacbook/docs/superpowers/plans/2026-05-24-turingmind-fork.md`
