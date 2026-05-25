---
name: Orchestrator Scoring Rules
---

# Scoring Rules

Applied by the orchestrator after agents return findings.

## Score formula

```
orchestrator_score = agent_confidence
  + 20  if in_diff (orchestrator-verified)
  − 50  if silenced_marker_nearby (orchestrator-verified)
  + 20  if finding.agent == "compliance"  (rule-citation bonus — the compliance agent quotes the rule in `problem`)
  − 30  if intent_doc_match.confidence > 0.7  (intent-doc partial match)
  − 100 if intent_doc_match.confidence > 0.9  (intent-doc strong match — REPLACES the −30 above, does not stack)
  + 10  if cross-confirmed by 2+ agents
  + 15  if persisted from previous pass

  + severity weight (applied last, before clamp):
       severity == "critical" →  +0
       severity == "high"     →  −5
       severity == "medium"   →  −15
       severity == "low"      →  −25
       severity unset / other →  −10  (treat as medium-equivalent fallback)
```

Clamp to `[0, 100]`. Filter entirely if pre-clamp score < 0.

**Why the severity weight:** `agent_confidence` measures *how sure the agent is that the finding is real*, NOT *how bad it is if true*. A confident catch of a code-style nit (severity=low) shouldn't score the same as a confident catch of a security vulnerability (severity=critical). Without this weight, easy-to-verify low-severity findings (e.g. "this constant is computed twice") inflate to Critical band and block `--finalize`. The agent supplies `severity` per `templates/agent-output-schema.md`; the orchestrator honors it.

## Bands

| Band | Score | Icon |
|------|-------|------|
| Critical | 95–100 | 🔴 |
| Warning | 80–94 | 🟠 |
| Medium | 70–79 | 🟡 |
| Filtered | <70 | 🔇 |

## Action policy (enforced by `--finalize`)

| Band | Policy |
|------|--------|
| Critical | enforce — blocks finalize, no acknowledgment path |
| Warning | enforce — blocks finalize, no acknowledgment path |
| Medium | require_review — blocks finalize until fixed OR acknowledged |
| Filtered | not reported |

Mid-loop `/review` doesn't enforce — only `--finalize` does.

## Filter thresholds per command

| Command | Reports | Notes |
|---------|---------|-------|
| `/review` | ≥80 | Critical + Warning |
| `/deep-review` | ≥70 | + Medium |

"Filtered Issues" summary always shows counts and reasons regardless of threshold.
