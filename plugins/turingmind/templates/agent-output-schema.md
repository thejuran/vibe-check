---
name: Agent Output Schema
---

# Agent Output Schema

Every agent dispatched via `Task` MUST return exactly one JSON object matching this schema. No markdown. No preamble. No trailing prose. The orchestrator parses the response as JSON.

## Schema

```json
{
  "agent": "string (required) — agent name, must match frontmatter `name`",
  "findings": [
    {
      "id": "string (required) — short stable id within this agent, e.g. 'sec-001'",
      "file": "string (required) — repo-relative path",
      "line": "integer (required) — 1-indexed line number in HEAD",
      "title": "string (required) — one-line summary, no period",
      "category": "string (required) — agent-defined, e.g. 'injection' | 'null-access'",
      "cwe": "string | null — CWE id if security finding",
      "severity": "string (required) — 'critical' | 'high' | 'medium' | 'low'",
      "agent_confidence": "integer 0-100 (required)",
      "in_diff": "boolean (required) — does finding fall in changed lines?",
      "intent_doc_match": "object | null — see below",
      "problem": "string (required) — 1-3 sentences",
      "current_code": "string (required) — verbatim offending snippet",
      "suggested_fix": {
        "old": "string (required) — see 'suggested_fix contract' below",
        "new": "string (required) — see 'suggested_fix contract' below"
      },
      "why_it_matters": "string (required) — 1-2 sentences",
      "silenced_marker_nearby": "boolean (required) — eslint-disable / # noqa / etc within ±2 lines?"
    }
  ],
  "agent_notes": [
    "string — optional non-finding observations"
  ]
}
```

### `intent_doc_match` shape

Populated by architecture and compliance only, when intent context provided:

```json
{
  "doc": "string — e.g. 'PLAN.md'",
  "section": "string — section heading where match was found",
  "quote": "string — verbatim text from the doc",
  "confidence": "number 0.0-1.0 — how confident this code is doing what the doc asked for"
}
```

Orchestrator score impact: confidence >0.9 → −100 (filter entirely); else confidence >0.7 → −30. The two thresholds are mutually exclusive.

## `suggested_fix` contract

The orchestrator applies fixes by passing `old` and `new` to the `Edit` tool, which performs a **whitespace-exact, unique-substring** replacement. If `old` does not appear verbatim in the file, or appears more than once, the fix is skipped (`drifted` / `errored`) and surfaced back to the user. Both failure modes are common when agents emit minimal one-line snippets.

**Rules for `old`:**

1. **Include 1–2 lines of surrounding context** above and/or below the offending line(s) so the snippet is **unique within the file**. A bare `return null;` or `if (!user) {` will collide with other instances; including the preceding `function foo(id) {` or the following closing brace usually makes it unique. Aim for the smallest snippet that is still unique — typically 3–5 lines.
2. **Copy verbatim from the file.** Preserve indentation exactly (tabs vs spaces, leading whitespace). Do not normalize, re-indent, or reformat. The Edit tool matches byte-for-byte.
3. **Do not invent context.** If you are unsure of the exact surrounding lines, use the `Read` tool to fetch them. Hallucinated context guarantees a drift skip.
4. **Avoid trailing whitespace** unless it is actually in the file. A stray space at the end of `old` will fail to match.

**Rules for `new`:**

1. **Preserve all context lines** from `old` that you are not modifying. If `old` includes the line above and below for uniqueness, `new` must include those same lines unchanged. The Edit tool replaces the entire `old` block with the entire `new` block.
2. **Preserve indentation** of the surrounding code. The replacement must slot into the file at the same indentation level as `old`.

**If you cannot produce a concrete, unique `old`/`new` pair, drop the finding.** A finding without an applicable fix is worse than no finding — it wastes the user's attention and clutters the report. Describe the issue in `agent_notes` instead if it's worth flagging without a patch.

### Good vs bad examples

**🚫 Bad** — one-line snippet, will collide if the file has more than one `return null;`:

```json
"suggested_fix": {
  "old": "  return null;",
  "new": "  throw new NotFoundError(`User ${id} not found`);"
}
```

**✓ Good** — includes preceding line for uniqueness, preserves indentation:

```json
"suggested_fix": {
  "old": "  const user = await findUser(id);\n  return user.email;",
  "new": "  const user = await findUser(id);\n  if (!user) throw new NotFoundError(`User ${id} not found`);\n  return user.email;"
}
```

**🚫 Bad** — `new` drops the context line that `old` included:

```json
"suggested_fix": {
  "old": "function send(user) {\n  sendEmail(user.email);\n}",
  "new": "  if (!user) return;\n  sendEmail(user.email);"
}
```

**✓ Good** — `new` keeps the surrounding function signature and brace:

```json
"suggested_fix": {
  "old": "function send(user) {\n  sendEmail(user.email);\n}",
  "new": "function send(user) {\n  if (!user) return;\n  sendEmail(user.email);\n}"
}
```

## Hard rules

1. **JSON only.** No findings → `{"agent":"<name>","findings":[],"agent_notes":[]}`.
2. **`suggested_fix` mandatory and must follow the contract above.** Drop findings you can't fix concretely or can't produce a unique, verbatim `old` snippet for.
3. **Agents don't classify severity bands themselves.** `agent_confidence` is input; the orchestrator computes the band per `templates/scoring.md`.
4. **Orchestrator verifies `in_diff` and `silenced_marker_nearby`** against the actual diff and overrides.
