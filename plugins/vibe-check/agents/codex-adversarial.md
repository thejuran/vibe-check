---
name: codex-adversarial
description: Contract agent for Codex (GPT-5-codex) adversarial review — defines how the orchestrator translates Codex's review-output findings into the vibe-check schema for /deep-review. Not a Task reviewer; a translation contract.
---

This is a **contract document**, not a `Task` reviewer. Unlike the native vibe-check agents (`security`, `bugs`, `framework-react`, …), this file does not reason over a `<diff>` block and it never shells out. It is the **spec-of-record** for treating Codex as one more reviewer: the orchestrator wired in Phase 5 (`commands/deep-review.md`) runs Codex's `adversarial-review` on this agent's behalf, then translates the output into the vibe-check finding schema exactly as documented below. Phase 5 implements against this written contract so the mapping is never re-derived ad hoc. The selection matrix (`agents/index.md`) points here for the same reason.

Codex is a **second model** (GPT-5-codex) whose review prompt is explicitly adversarial — "break confidence in the change, not validate it" — so it weights auth/trust boundaries, data loss, rollback safety, races, partial failure, and schema drift. It runs **only in `/deep-review`** (never the fast `/review` path) and its findings flow through the existing merge / dedup / score / render pipeline like any native reviewer. No scoring, triage, or schema changes accompany it.

## Identity and role

- **Name:** `codex-adversarial` (matches the frontmatter `name`, and is the literal value of the top-level `agent` key in the translated output).
- **What runs it:** the **orchestrator**, not this doc. The orchestrator probes Codex availability, runs `adversarial-review --json --wait` against the diff range it already resolved in Phase 0, parses the `--json` payload (conforming to Codex's `schemas/review-output.schema.json`), and applies the translation table here.
- **What this doc owns:** the Codex→vibe-check field mapping, the verdict rule, the `agent_notes` carry decision, the orchestrator-backfill delegation, the untrusted-data posture (including the path trust boundary on `file`), the unavailable/timeout fallback contract, and one worked example.
- **What this doc does NOT own:** any runtime mechanics — plugin-path resolution, the exact timeout value, the probe/run sequencing, the skip-line wording. Those are Phase 5. This phase writes the contract; no code executes here.

## Verdict handling

Codex returns a top-level `verdict`. The orchestrator maps it before translating any finding:

| Codex `verdict`   | Result                                                                 |
|-------------------|------------------------------------------------------------------------|
| `approve`         | Emit **zero** findings: `findings: []`. Codex found nothing blocking.   |
| `needs-attention` | **Translate all** of Codex's `findings` per the table below.           |

There is no partial/threshold verdict — Codex either approves (no findings) or flags attention (translate every finding it returned, letting the vibe-check scorer band them as usual).

## agent_notes carry

Codex's top-level payload also carries `summary` (a one-line ship/no-ship read) and `next_steps` (an array of follow-up strings).

- **`summary` → `agent_notes` (carry verbatim).** The second model's overall read is useful, low-noise context for the owner. It is carried, unaltered, into the top-level `agent_notes` array of the translated object.
- **`next_steps` → dropped.** It is largely redundant with the per-finding `fix_hint`/`recommendation` and would bloat the report. The translation discards it.
