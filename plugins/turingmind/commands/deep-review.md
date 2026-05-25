---
allowed-tools: Bash(git:*), Bash(gh pr diff:*), Bash(gh pr view:*), Read, Write, Grep, Glob, Task, AskUserQuestion
description: Deep comprehensive code review with full context analysis
---

Comprehensive review with architecture + impact analysis + intent-doc alignment. Use for pre-PR or final-pass review.

Shares Phases 0, 0.5, 0.7, 1, 1.5, 3, 4, 4.5, 5 (interactive fix loop), and finalize with `commands/review.md`. Differences below.

Phase 5 is shared verbatim — when the loop's "rerun" option fires, it re-enters this command (`/deep-review`), not `/review`. State carry-forward + finalize work identically.

## Differences from /review

### Phase 2 — agent selection (deep adds architecture + impact)

| Always | Condition | Agent | Model | Thinking |
|--------|-----------|-------|-------|----------|
| ✓ | — | `bugs` | sonnet | none |
| ✓ | — | `security` | sonnet | medium |
| ✓ | — | `architecture` | **opus** | **high** |
| ✓ | — | `impact` | sonnet | medium |
|  | `CLAUDE.md`/`AGENTS.md` exists | `compliance` | sonnet | low |
|  | TS/JS in diff | `language-typescript` | sonnet | none |
|  | Python in diff | `language-python` | sonnet | none |
|  | Go in diff | `language-go` | sonnet | none |
|  | Rust in diff | `language-rust` | sonnet | none |
|  | React imports | `framework-react` | sonnet | none |

Pass thinking budget explicitly in Task calls:

```
Task(
  subagent_type: "architecture",
  description: "Deep architectural review",
  prompt: <full prompt with intent context>,
  thinking_budget: "high"
)
```

(If `thinking_budget` unsupported in current Claude Code: omit. Opus still applies via frontmatter.)

### Phase 1c — Related files (for impact agent)

After Phase 1.5, before Phase 2, for impact agent only:

For each diff file:
- `git grep -l "from.*<basename>"` → importers
- Parse diff's import statements → importees
- Find test files: `<basename>.test.*`, `test_<basename>.*`, `__tests__/<basename>.*`

Assemble `<related-files>`:

```
<related-files>
  <file path="src/users.ts">
    <imported-by>src/api/handlers.ts, src/admin/routes.ts</imported-by>
    <imports>src/db/client.ts, src/lib/email.ts</imports>
    <test-file>src/users.test.ts</test-file>
  </file>
</related-files>
```

Inject into impact agent's prompt only.

### Phase 2.5 — Architecture prompt enhancement

Architecture prompt includes `<intent-context>` AND directive to use thinking:

```
You are the architecture agent. Use extended thinking — reason about cross-file implications, intent alignment, pattern consistency.

{{intent-context}}

<diff>
{{git_diff}}
</diff>

<related-files>
{{from Phase 1c}}
</related-files>
```

### Phase 3 — Filter threshold

Use ≥70 (Critical + Warning + Medium) instead of ≥80.

### Phase 4 — Output

In addition to standard sections:

```markdown
### Architectural Notes 📐
{{architecture's agent_notes as bullets}}

### Impact Analysis 💥
{{impact's agent_notes as bullets}}
- **Files affected:** {{count from related-files}}
- **Breaking changes detected:** {{yes/no based on impact findings with category=breaking-api}}
```

### Phase 4.5 — State

`mode: "deep"` in pass entry.

### --finalize

Same flow as review.md.

## Cost note

Typical deep pass ~$1.80 (Opus + thinking on architecture is the driver). Use sparingly — final pass before PR/finalize. Mid-loop should use `/review`.
