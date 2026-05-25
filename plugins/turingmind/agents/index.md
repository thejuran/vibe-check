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
| Any code | `@agents/bugs.md`, `@agents/security.md` |
| Has CLAUDE.md | `@agents/compliance.md` |
| TypeScript/JavaScript | `@agents/language-typescript.md` |
| Python | `@agents/language-python.md` |
| Deep review mode | `@agents/architecture.md` |

## Core Agents (Always Load)

These agents apply to all code reviews:

1. **`bugs.md`** - Logic errors, null access, race conditions
2. **`security.md`** - OWASP Top 10, injection, XSS, secrets

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
Load when: Deep review mode (`/turingmind-code-review:deep-review`)

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

