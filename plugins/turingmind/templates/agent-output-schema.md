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
        "old": "string (required) — verbatim line(s) to remove",
        "new": "string (required) — replacement line(s)"
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

Orchestrator score impact: >0.7 → −30, >0.9 → −100 (filter entirely).

## Hard rules

1. **JSON only.** No findings → `{"agent":"<name>","findings":[],"agent_notes":[]}`.
2. **`suggested_fix` mandatory.** Drop findings you can't fix concretely.
3. **Agents don't band themselves.** `agent_confidence` is input; orchestrator computes band.
4. **Orchestrator verifies `in_diff` and `silenced_marker_nearby`** against the actual diff and overrides.
