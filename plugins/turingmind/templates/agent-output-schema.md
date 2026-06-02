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
      "fix_hint": "string | null — OPTIONAL one-line sketch of the fix direction (e.g. 'guard user before .email access; throw NotFoundError'). NOT an Edit-ready patch. Leave null if the direction isn't obvious. The fix agent (Phase 5) produces the actual patch.",
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

## `fix_hint` — detection agents do NOT write patches

**Detection is decoupled from patching.** Your job as a detection agent is to *find the problem*, not to produce an `Edit`-ready patch. Do not emit `old`/`new` substring pairs. If the corrective direction is obvious, put a one-line sketch in `fix_hint` (e.g. `"guard user before .email access; throw NotFoundError on miss"`); otherwise set `fix_hint` to `null`. Either is fine — a fix-less finding is fully scored, banded, and reported.

When the user accepts a finding in the interactive fix loop, the orchestrator dispatches a dedicated **`fix` agent** (`agents/fix.md`) that reads the file and applies the change *semantically* with its own `Edit` calls — it locates the right spot itself, so there is no byte-exact-substring requirement and no `drifted`/`errored` skip path on the detection side.

**Never drop a finding because it's hard to patch.** Race conditions, architectural problems, and bugs spanning multiple call sites are often the highest-value findings precisely *because* they don't reduce to one tidy substring. Those used to be silently discarded under the old "drop if you can't produce a unique old/new pair" rule — that rule is gone. Drop a finding ONLY when you no longer believe it is real.

## Hard rules

1. **JSON only.** No findings → `{"agent":"<name>","findings":[],"agent_notes":[]}`.
2. **Report real findings regardless of fix difficulty.** `fix_hint` is optional and never gates emission. The `fix` agent produces the actual patch later, only for findings the user accepts.
3. **Agents don't classify severity bands themselves.** `agent_confidence` is input; the orchestrator computes the band per `templates/scoring.md`.
4. **Orchestrator verifies `in_diff` and `silenced_marker_nearby`** against the actual diff and overrides.
