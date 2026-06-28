---
name: Agent Router
description: Routes to appropriate agents based on detected context
---

# Agent Router

This file helps select the right agents based on the code being reviewed.
Only load agents that are relevant to reduce context and improve accuracy.

## Agent Selection Matrix

| Detected | Load Agents |
|----------|-------------|
| Always (Phase 1, before others) | `triage` |
| Any code | `@agents/bugs.md`, `@agents/security.md` |
| Has CLAUDE.md | `@agents/compliance.md` |
| TypeScript/JavaScript | `@agents/language-typescript.md` |
| Python | `@agents/language-python.md` |
| `.go` files | `language-go` |
| `.rs` files | `language-rust` |
| React imports detected | `framework-react` |
| FastAPI imports detected | `framework-fastapi` |
| `SKILL.md` / agent `.md` / plugin manifest (triage.frameworks "skill") | `framework-skill` |
| Deep review mode | `@agents/architecture.md` |
| Deep review mode | `@agents/test-sufficiency.md` |
| Deep review mode + Codex available | codex-adversarial (orchestrator-run) |

## Core Agents (Always Load)

These agents apply to all code reviews:

1. **`bugs.md`** - Logic errors, null access, race conditions
2. **`security.md`** - OWASP Top 10, injection, XSS, secrets

> **`fix.md` is not a detection agent** and is never dispatched in Phase 2. It runs only in Phase 5 (interactive fix loop) on findings the user accepts — it reads the file and applies the change semantically, then commits. Detection agents only *find* and optionally leave a one-line `fix_hint`; they never produce patches.

> **`codex-adversarial` is orchestrator-run, not a `Task` dispatch.** It is a contract agent, not a native reviewer: the orchestrator runs Codex (`adversarial-review`) on its behalf in `/deep-review` when Codex is available, then translates the output into the vibe-check schema per `agents/codex-adversarial.md`. It is never one of the parallel Phase 2 `Task` calls.

## Conditional Agents (Load When Relevant)

### Compliance Agent
Load when: `CLAUDE.md` exists in project root or modified directories

```
@agents/compliance.md
```

### Language Agents
Load based on file extensions detected in diff:

| Extensions | Agent |
|------------|-------|
| `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs` | `@agents/language-typescript.md` |
| `.py` | `@agents/language-python.md` |

### Architecture Agent
Load when: Deep review mode (`/vibe-check:deep-review`)

```
@agents/architecture.md
```

## Dispatch Pattern

The orchestrator command dispatches agents via the `Task` tool — one parallel call per agent — in a single assistant turn. Each agent runs in its own context window and returns a JSON findings object per `templates/agent-output-schema.md`. The orchestrator merges, scores, filters, and renders.

This file is the routing reference: which agents load under which conditions. The orchestrator reads this matrix at Phase 2 of every review.

## Why Per-Domain Subagents?

| Approach | Quality | Cost | Attribution |
|----------|---------|------|-------------|
| One mega-prompt | Generalist | Low | Conflated |
| Per-domain subagent (Task dispatch) | Specialist per domain | Higher | Per-agent attribution in output |

Each subagent has its own checklist, examples, and scoring norms. Cross-agent dedup is handled by the orchestrator (see scoring.md +10 cross-confirmation bonus).

## Adding New Agents

1. Create `agents/language-{name}.md` or `agents/framework-{name}.md`
2. Add entry to the Agent Selection Matrix
3. Update `commands/review.md` Phase 2 dispatch table (and deep-review.md if applicable)

Template:
```markdown
---
name: language-{name}
description: {Language}-specific review — [key checks]. Returns JSON findings.
model: sonnet
---

[Agent prompt body — see bugs.md for the full template including JSON output schema reference.]
```

