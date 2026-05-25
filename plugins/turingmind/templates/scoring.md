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
```

Clamp to `[0, 100]`. Filter entirely if pre-clamp score < 0.

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
