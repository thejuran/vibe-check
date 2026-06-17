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
       severity == "high"     →  −3
       severity == "medium"   →  −8
       severity == "low"      →  −20
       severity unset / other →  −8   (treat as medium-equivalent fallback)
```

Clamp to `[0, 100]`. Filter entirely if pre-clamp score < 0.

**Why the severity weight:** `agent_confidence` measures *how sure the agent is that the finding is real*, NOT *how bad it is if true*. A confident catch of a code-style nit (severity=low) shouldn't score the same as a confident catch of a security vulnerability (severity=critical). Without this weight, easy-to-verify low-severity findings (e.g. "this constant is computed twice") inflate to Critical band and block `--finalize`. The agent supplies `severity` per `templates/agent-output-schema.md`; the orchestrator honors it.

**Calibration note (recovers under-reporting):** the weights are intentionally gentle for `high`/`medium` (−3 / −8) and only steep for `low` (−20). The earlier −5/−15/−25 spread pushed genuine medium-severity bugs the agent was 70–80% confident about *below* the `/review` ≥80 threshold, so they were silently filtered — the tool reported fewer real bugs than it found. The job of severity weight is to keep low-severity nits out of the Critical band, NOT to suppress real medium bugs. Only `low` should routinely fall below threshold; `medium` and `high` clear it whenever the agent's confidence is reasonable. If you find yourself wanting to re-steepen these, lower the `/review` threshold instead (see below) rather than penalizing severity.

## Bands

| Band | Score | Icon |
|------|-------|------|
| Critical | 95–100 | 🔴 |
| Warning | 80–94 | 🟠 |
| Medium | 70–79 | 🟡 |
| Filtered | <70 | 🔇 |

**Band is score-derived, NOT severity-derived.** A finding's `severity` (critical/high/medium/low) feeds the *score* via the severity weight above; it does not directly pick the band. So a medium-*severity* finding that scores ≥80 lands in the Warning *band* (and is enforced at `--finalize` with no acknowledgment path) — this is intended. "Medium severity" and "Medium band" are different axes: severity is "how bad if real," band is the final confidence-and-impact score bucket. If you want a finding to be acknowledge-able at finalize, that is governed by its *band* (Medium band, 70–79), which after the gentle medium weight (−8) corresponds to a lower-confidence medium-severity finding — exactly the "real but not certain" case the acknowledgment path exists for. Do not re-key the action policy off severity; keep it on band.

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
