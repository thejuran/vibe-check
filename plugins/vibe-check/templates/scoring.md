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
  + 10  if corroborated by a second opinion: a codex-adversarial member AND a Claude-lane member that EACH clear the per-command cutoff on their own lone-lane score and share the same line (provenance = envelope codex.status == "joined"); only those two members earn it; Claude↔Claude agreement earns nothing (D-01, D-05)
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

- **Codex-corroborated** — a `codex-adversarial` member AND a Claude-lane member of the group qualify as a pair (D-05, below), and the envelope's orchestrator-set `codex.status` is `"joined"`. Provenance comes from that block, never from the finding: a native agent can write `agent: "codex-adversarial"` or `category: "adversarial"` on its own finding, and that self-report earns nothing.
- **Persisted** — the finding was carried forward from a previous pass and its line is unchanged (`status == "persisted"`, set by the carry-forward compare, never by the agent).

`in_diff` is NOT a corroborator. Claude↔Claude agreement between two Claude lanes is one correlated voter, not a second opinion.

**Qualification (D-05, Phase 53).** A second opinion counts only from an independently qualifying finding:

- Each member of the pair must clear the per-command cutoff (`/review` 80, `/deep-review` 70) on its OWN lone-lane score — the B-REWEIGHT offset applied, no +10, no second-opinion credit — so two weak notes can never promote each other.
- The pair must share the same `line`. The same line is a mechanical proxy for "the same defect, not merely nearby lines". It is only a proxy: a shared line does not guarantee that the two reviewers agree on the failure. Title matching stays retired (agent titles are free text).
- **Known limitation (conservative).** When two lanes anchor one defect on different lines of a single multi-line statement, the pair is not credited. The Codex member is then a lone lane, capped at 94 (warning). It is never dropped and still fires. The rule deliberately does not widen to adjacent lines or to the whole statement. A shared location is not a shared failure: nearby lines can carry a different defect, and a reviewer at the same code can dispute the harm. Replay evidence: Phase 53 D-05, case A2 (`docs/design/b3-ground-truth/REPLAY-REPORT-phase53-d05.md`, § "Owner decision on A1–A3"). A future structured matching improvement must distinguish shared LOCATION from shared FAILURE MECHANISM; a defect-type label alone would not establish a shared mechanism.
- The credit is PER MEMBER: only the two members of a qualifying pair receive the +10 and the lone-lane cap release. Every other member of the same grouped row is scored as a lone-lane finding — a grouped row is a site, not a defect.
- A member that fails qualification (for example a capped ≤ 45 / low note) stays a listed member and stays visible; it never boosts another finding's band.
- Persistence (D-01's second arm) is unchanged and remains a row property: a persisted member gives every member of its row a second opinion.

### Lone-lane band ceiling (B-SEV, D-02)

- A member with no second opinion (no qualifying pair of its own, no persisted member in its row) has its score capped at `critical floor − 1` (94 by default; respects a config-tuned `thresholds.critical`) BEFORE banding — it may reach Warning (still finalize-blocking) but never Critical. A lone Codex finding (no Claude lane beside it) is capped too.
- The cap lowers the band only: the per-command filter threshold still judges the uncapped score, so the ceiling never drops a finding.

### Lone-lane confidence calibration (B-REWEIGHT, D-15)

- For a member with no second opinion, its `agent_confidence` is adjusted by a per-agent offset ≤ 0 BEFORE the formula (the offset joins step 1, the starting value).
- The offsets are DERIVED, not hand-picked: shrunk per-agent precision (prior strength 20, min labeled sample 5) over the labeled Claude-5-era B3 runs — method and inputs in `docs/design/b3-ground-truth/CALIBRATION-v2.10.md`; `scripts/calibrate.py --check` re-derives them and fails when the embedded constants drift.
- Agents with thin data (labeled n < 5) or precision at/above the pooled rate are identity (offset 0, absent from the table).
- The offset never raises confidence, never changes the emitted `agent_confidence`, never touches `stable_hash` inputs, and does NOT feed the `min_confidence` filter — that filter reads the raw value.
- Current offsets:
  - architecture: -6
  - bugs: -2
  - impact: -12

### Site grouping (H-LANE, D-03/D-14)

- A **site** is the same file within ±2 lines. Every lane at one site — native Claude agents and Codex alike — is ONE surviving row; category no longer affects grouping.
- The row is led by the member with the strongest EFFECTIVE band (its score after the lone-lane ceiling → `band_for` → the idiom cap by that member's OWN category), then the highest score, then the `stable_hash` tie-break, then the agent name — so an idiom-capped member never drags a co-located security warning down, and the pick never depends on arrival order. The per-command cutoff judges the uncapped score of the first member in that order whose uncapped score clears it, and that member leads the row (its score and band are the row's); when no member clears the cutoff the row drops as sub-threshold.
- **Row lead (D-06).** The lead is the most severe qualifying member. Tie-break order, fully deterministic: effective band, capped score, raw score, `stable_hash`, agent name. Owner decisions (dismiss / defer / acknowledge) bind to each member's own `stable_hash`; when regrouping demotes a former lead to an absorbed member, its member record keeps its own obligation identity, so a decision is never erased or re-targeted by a change of lead.
- `attribution` lists every lane; `members` carries every lane's own record, rendered as its title (survivor first, then the absorbed members in scored order). Members are de-duplicated by each member's own lane-aware occurrence identity `(agent, stable_hash(file, canonical, title), line)` — never by (agent, title), never by `stable_hash` alone, and never by `(stable_hash, line)` without the agent: two identical lines with one title are two members, and two lanes at one line with one title are two members. An agent-supplied `members` on a fresh finding is stripped at ingress exactly like `status`.
- On a later pass every carried row is expanded into its members first: each member is carried on its OWN HEAD read (line + window, the same `carry_forward_status` compare as any finding) and scored on its own facts, so a still-valid member outlives a lead that was fixed, suppressed at its own line or fell sub-threshold, and re-collapses with a lead that survives. A member whose line is gone is recorded in `fixed_since_last`.
- Absorbed members are recorded in `filtered[]` as `absorbed-into: <hash>` — never silently dropped.

**Freeze lift (v2.10 Wave 1):** the formula freeze lifted for exactly three changes — B-SEV, B-REWEIGHT and H-LANE; every other constant (weights, bonuses, band cutoffs, per-command thresholds) stays frozen. Each change was guarded by an offline replay against the archived B3 runs (`scripts/replay.py`, `docs/design/b3-ground-truth/REPLAY-REPORT-phase41-*.md`) with zero catch regressions on the strict-axis basis recorded in `docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md` entry 007. The B-REWEIGHT offsets are derived, not tuned (`docs/design/b3-ground-truth/CALIBRATION-v2.10.md`). Scope source: `docs/superpowers/specs/2026-07-08-quiet-down-v2.10-design.md` D-07.

### Needs verification (Phase 53)

A lane that can name a concrete trigger, path and consequence but cannot prove the failure marks its finding `needs_verification` instead of guessing a severity. `scripts/score.py` owns every rule below.

- **Band and score.** An admitted item is a row with the fixed band literal `needs-verification` and `orchestrator_score` 0. Its band is never computed by `band_for`.
- **Route.** The item is split out of the working set before the `min_confidence` filter and before site grouping. It never corroborates and is never corroborated, never absorbed into a site row, and never confidence- or threshold-filtered.
- **Admission (mechanical, fixed before measurement; frozen at Phase 54).** The item needs a location: a non-empty `file` AND (`line` ≥ 1 OR a non-empty `needs_verification.symbol`). Each of `trigger`, `path` and `consequence` must be a single-line string (only its first line counts; whitespace collapsed; capped at 300 characters) of at least `_NV_MIN` = 12 characters that is not wholly one of these hedge phrases (case-insensitive, surrounding periods ignored): `may break`, `might break`, `might break compatibility`, `could be bypassed`, `could break`, `sensitive area`, `not exhaustive`, `needs review`, `unverified`. A refused item goes to `filtered[]` with reason `nv-not-admitted` and is counted in `nv_dropped`. A fresh `needs_verification` object whose three fields are blank, `{}`, or wholly a placeholder value (`N/A`, `none`, `-`; case-insensitive, surrounding whitespace trimmed, trailing periods ignored, whole-field match only: every line of the field counts, so `None` followed by more text is a real field, and a leading period makes it real text, so `...none` is a real field that must meet admission) is not a Needs-verification claim: the key is ignored and the finding is scored normally; an object with at least one real field must meet admission or it is dropped, never promoted to a normal finding. Limitation: these presence-and-shape checks are the only mechanical test; semantic concreteness is the lane prompt's job.
- **Identity and dedupe.** `stable_hash(file, canonical, title)` is assigned once, at admission. A carried row keeps its stored `stable_hash` verbatim; it is never recomputed from a relocated or null canonical, so a recorded decision stays attached. A carried row and a fresh re-report with the same hash are one row, and the carried row wins. A carried row is never re-admitted.
- **Carry and closure (O-2).** A carried item is `persisted` only when its WHOLE recorded snippet is confirmed unchanged at HEAD. The check is the evidence fingerprint (`_nv_carry_status`): every non-blank line, with relative indentation kept and only a uniform dedent of the whole snippet ignored, compared with the HEAD window the orchestrator located. A surviving first line or symbol name is not evidence. A changed body, an unlocated item (renamed, reformatted, moved, or a deleted definition whose name survives elsewhere), an absent window or an empty snippet is `needs-recheck` — never `fixed-since-last`. When the item was located but changed, the row's `current_code` is refreshed to the HEAD window, so a decision taken before the change is asked again. The item closes only through a `resolved` recheck verdict from the lane that raised it (recorded in `resolved[]`), a fix-obsolete verdict, an owner-named confirmed fix that a reviewer other than the fix agent re-checked on the next pass (a routed recheck request bound to the item's `stable_hash` and the repaired blob; the fix agent's own check never closes it alone), or an owner decision.
- **Published counts.** `nv_dropped` (items refused admission) and `nv_dropped_weak` (weak notes, below) are output keys, absent when zero, and published at render.
- **Weak-note accounting (R5).** When a row's lead qualifies on its own, every member from another lane that does not qualify stays listed in `members[]`, never boosts, and is counted in `nv_dropped_weak`. A fully sub-threshold row (no member qualifies, nothing published) counts nothing.

**Rollback.** First, the separate state location: Phase-53 state lives at `.turingmind/state/format-53/<the shipped key>` (`statepath.resolve_current`). No shipped 2.11.x mode can resolve that path, so an older plugin's ordinary review, persist and finalize never read or write it. An undecided item cannot be rescored away by an older scorer, and an APPROVED written by an older plugin closes nothing here. Second, the marker, as defense in depth for a Phase-53 state handed to an older reader by hand: every Needs-verification row carries `members[0].obligation == "needs-verification"`, a string. A reader without Needs-verification support refuses the state, and its finalize halts without writing. The downgrade procedure (`fixtures/future-schema.json` `_rollback.phase53_nv_downgrade`) refuses while any Needs-verification item is undecided. It converts only decided rows, writes the converted copy to the OLD location, and never modifies the Phase-53 file. The OLD location is normally empty by then: the forward migration copies the pre-upgrade file into `format-53/`, verifies the copy, and only then moves the old file aside, no-clobber, as `<key>.json.migrated-format-53[-N]` (the recoverable original). So a plain reinstall of an older plugin cannot resume a review this version closed or blocked; it starts a fresh pass 1.
