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
  + 10  if corroborated by a second opinion: a codex-adversarial member AND a Claude-lane member at the same site (provenance = envelope codex.status == "joined"); Claude↔Claude agreement earns nothing (D-01)
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

## Wave 1 (v2.10) — second-opinion rules

The formula freeze lifted for v2.10 Wave 1, scoped to the three changes below; each was replayed offline against the archived B3 runs with zero catch regressions before it landed — `scripts/replay.py`, `docs/design/b3-ground-truth/REPLAY-REPORT-phase41-*.md`.

### Second opinion (D-01)

A finding group has a **second opinion** when either holds:

- **Codex-corroborated** — the group holds a `codex-adversarial` member AND a Claude-lane member at the same site, and the envelope's orchestrator-set `codex.status` is `"joined"`. Provenance comes from that block, never from the finding: a native agent can write `agent: "codex-adversarial"` or `category: "adversarial"` on its own finding, and that self-report earns nothing.
- **Persisted** — the finding was carried forward from a previous pass and its line is unchanged (`status == "persisted"`, set by the carry-forward compare, never by the agent).

`in_diff` is NOT a corroborator. Claude↔Claude agreement between two Claude lanes is one correlated voter, not a second opinion.

### Lone-lane band ceiling (B-SEV, D-02)

- A group with no second opinion has its score capped at `critical floor − 1` (94 by default; respects a config-tuned `thresholds.critical`) BEFORE banding — it may reach Warning (still finalize-blocking) but never Critical. A lone Codex finding (no Claude lane beside it) is capped too.
- The cap lowers the band only: the per-command filter threshold still judges the uncapped score, so the ceiling never drops a finding.

### Lone-lane confidence calibration (B-REWEIGHT, D-15)

- For a group with no second opinion, each member's `agent_confidence` is adjusted by a per-agent offset ≤ 0 BEFORE the formula (the offset joins step 1, the starting value).
- The offsets are DERIVED, not hand-picked: shrunk per-agent precision (prior strength 20, min labeled sample 5) over the labeled Claude-5-era B3 runs — method and inputs in `docs/design/b3-ground-truth/CALIBRATION-v2.10.md`; `scripts/calibrate.py --check` re-derives them and fails when the embedded constants drift.
- Agents with thin data (labeled n < 5) or precision at/above the pooled rate are identity (offset 0, absent from the table).
- The offset never raises confidence, never changes the emitted `agent_confidence`, never touches `stable_hash` inputs, and does NOT feed the `min_confidence` filter — that filter reads the raw value.
- Current offsets:
  - architecture: -6
  - bugs: -2
  - impact: -12

### Site grouping (H-LANE, D-03/D-14)

- A **site** is the same file within ±2 lines. Every lane at one site — native Claude agents and Codex alike — is ONE surviving row; category no longer affects grouping.
- The row is led by the member with the strongest EFFECTIVE band (its score after the lone-lane ceiling → `band_for` → the idiom cap by that member's OWN category), then the highest score, then the `stable_hash` tie-break, then the agent name — so an idiom-capped member never drags a co-located security warning down, and the pick never depends on arrival order.
- `attribution` lists every lane; `members` carries every lane's own record, rendered as its title (survivor first, then the absorbed members in scored order). Members are de-duplicated by each member's own lane-aware occurrence identity `(agent, stable_hash(file, canonical, title), line)` — never by (agent, title), never by `stable_hash` alone, and never by `(stable_hash, line)` without the agent: two identical lines with one title are two members, and two lanes at one line with one title are two members. An agent-supplied `members` on a fresh finding is stripped at ingress exactly like `status`.
- On a later pass every carried row is expanded into its members first: each member is carried on its OWN HEAD read (line + window, the same `carry_forward_status` compare as any finding) and scored on its own facts, so a still-valid member outlives a lead that was fixed, suppressed at its own line or fell sub-threshold, and re-collapses with a lead that survives. A member whose line is gone is recorded in `fixed_since_last`.
- Absorbed members are recorded in `filtered[]` as `absorbed-into: <hash>` — never silently dropped.

**Freeze lift (v2.10 Wave 1):** the formula freeze lifted for exactly three changes — B-SEV, B-REWEIGHT and H-LANE; every other constant (weights, bonuses, band cutoffs, per-command thresholds) stays frozen. Each change was guarded by an offline replay against the archived B3 runs (`scripts/replay.py`, `docs/design/b3-ground-truth/REPLAY-REPORT-phase41-*.md`) with zero catch regressions on the strict-axis basis recorded in `docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md` entry 007. The B-REWEIGHT offsets are derived, not tuned (`docs/design/b3-ground-truth/CALIBRATION-v2.10.md`). Scope source: `docs/superpowers/specs/2026-07-08-quiet-down-v2.10-design.md` D-07.
