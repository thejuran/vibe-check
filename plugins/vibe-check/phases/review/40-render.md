# Phase 4 — Render results

> **Lazy-loaded.** Read from the command spine (`commands/review.md` or `commands/deep-review.md`) when Phase 4 is entered (every review, after Phase 3).
> Announce on entry, after this Read: `✓ Phase 4 — Render results`.

**Render gate (scoring-ran sentinel — HARD HALT, ROBUST-04 D-08; D-10, CORE-03).** BEFORE reading any finding's `band` to render the band tables below, assert BOTH: (i) the pass carries the script's pass-level `scored_by_script: true` sentinel (the top-level field `scripts/score.py` stamped in Phase 3 / `score.py:run()`), AND (ii) EVERY finding about to be rendered carries both `band` and `orchestrator_score`. **This is a HARD render gate, not a soft check.** If EITHER assertion fails — no `scored_by_script: true` on the pass, OR any to-be-rendered finding lacks `band`/`orchestrator_score` — the orchestrator HALTS, emits the explicit error **`scoring did not run — review halted; no report produced`**, and renders NOTHING: NO findings, NO summary table, NO band sections, NO partial output. A review either ran the deterministic core or it produces no report — there is no hand-scored fallback (CORE-03 / D-09 forbids one). This is the render-time twin of the Phase-3 fail-closed check (step 5 above, "FAIL-CLOSED check"): rendered findings exist ONLY because the script ran and stamped them — a finding that never went through the script has no `band`, so it cannot be rendered. The posture matches `score.py`'s own `__main__`, which already exits non-zero on unparseable stdin; the gate extends that fail-closed contract to "scored output is structurally required at render." The pass-level `resolved[]` entries are NOT findings and are outside this gate — they render only in the multi-pass `Resolved on recheck` list below.

**Parallel-dispatch detect-and-WARN (ROBUST-04 D-09 — codex-aware; a NOTE, NEVER a halt).** AFTER the gate passes (the pass IS scored), reconcile the agents that were dispatched/joined against the agents that actually contributed, as a legibility check. This NEVER halts and NEVER drops a finding — it only emits `⚠` notes alongside the report.
  - **EXPECTED set** = the dispatched native agents `agents_run` (the union written to the pass entry — Phase 4.5:`agents_run`; in `--all` mode this is the cross-chunk union of every chunk's dispatched agents, Phase 2 Site C / loop-exit) **PLUS `codex-adversarial` IFF Codex actually JOINED this pass** (NOT `CODEX_SKIPPED`). Codex joined ⟺ a `codex-adversarial` agent-response object was appended to the agent-response set at Phase 3 entry (per `deep-review.md` Phase 3 — a `verdict: "approve"` run appends a ZERO-finding `codex-adversarial` object and so COUNTS as joined-and-expected; a `CODEX_SKIPPED` run appends NOTHING and so `codex-adversarial` is NOT in EXPECTED). **`codex-adversarial` is NOT a native `Task` agent — it is never in `agents_run`; it is added to EXPECTED only when it joined.** This codex-awareness is load-bearing: without it, EVERY normal Codex `/deep-review` would misfire here as a foreign-agent mismatch (a finding attributed to `codex-adversarial`, an agent "not dispatched"). A normal Codex deep-review must produce ZERO dispatch warnings.
  - **RETURNED set** = every distinct `agent` value across the parsed agent responses, UNION every agent named in the surviving findings' `attribution` arrays (the script-set cross-confirm attribution).
  - **WARN on mismatch (note + continue):**
    * An EXPECTED agent (dispatched native agent, or joined Codex) that returned nothing parseable / contributed no finding → `⚠ Dispatch check: {name} was dispatched but returned no parseable findings`.
    * A RETURNED/attributed agent OUTSIDE the EXPECTED set → `⚠ Dispatch check: a finding is attributed to {name}, which was not in the expected (dispatched + joined-Codex) set`.
  - **`--all` note:** the comparison uses the cross-chunk UNION of `agents_run`; a flat union can mask a per-chunk silent miss (a per-chunk EXPECTED-vs-RETURNED reconciliation is a permitted refinement). The minimum bar is the codex-aware EXPECTED set above, so a normal `--all` deep-review never misfires. Per D-09 this is detect-and-WARN ONLY — never a halt, never a dropped finding.

**Command → threshold (the bands you see depend on which command ran).** The threshold that filtered these findings was selected in Phase 3 by the envelope `command` field — `"review"` ⇒ ≥80 (Critical + Warning only), `"deep-review"` ⇒ ≥70 (Critical + Warning + Medium). `command` is set from this command's active-command self-identity, so `/deep-review`'s Medium findings (70–79) reach render and are NOT silently filtered; `/review` never produced them (they scored below its ≥80). No deep-review.md scoring edit is needed — it delegates this Phase verbatim and review.md self-identifies the active command.

### Multi-pass status summary (only in pass >1)

If `$PASS_NUMBER > 1`:

Count carry-forward results:
- `fixed_count` = findings with status `fixed-since-last` in this pass's carry-forward
- `persisted_count` = findings with status `persisted`
- `new_count` = brand-new findings this pass
- `resolved_count` = entries in this pass's `resolved[]` (0 when the key is absent)
- `kept_open_count` = findings in this pass carrying `kept_open`

Render before the per-band sections:

````
**Pass {{$PASS_NUMBER}}** — {{fixed_count}} fixed since last, {{resolved_count}} resolved on recheck, {{persisted_count}} still present, {{new_count}} new, {{kept_open_count}} kept open below this pass's filters

✅ Fixed since last pass:
- `{{file}}:{{line}}` — {{title}} (was {{band}} pass {{N}})

✅ Resolved on recheck:
- `{{file}}:{{line}}` — {{title}} (was {{band}}; {{resolution.source}} by {{resolution.agents}} at {{resolution.head_sha}})
````

Omit the `✅ Resolved on recheck:` list when `resolved_count` is 0, and omit the `kept open below this pass's filters` clause of the headline when `kept_open_count` is 0. `resolved[]` entries are NOT findings — they are not subject to the render gate's band/orchestrator_score check and are rendered only in the list above.

Findings marked `persisted` go into the regular per-band tables with `Status: PERSISTED (pass N)` where N is the finding's `snapshot.at_pass`.

A finding carrying `kept_open` renders in the band table of its (carried) `band` with `Status: PERSISTED|NEEDS-RECHECK (pass N) — kept open: {{kept_open}} this pass (D-02: an unresolved finding never expires because a confidence or threshold filter moved; resolve it or decide it at Finalize)`; it is never hidden.

Per `templates/output-format.md`:

```
## Code Review

**Summary:** Reviewed {{N}} files, {{L}} lines changed

| Found | Reported | Filtered |
|-------|----------|----------|
| {{total}} | {{reported}} | {{filtered}} |
```

**Config-health line (D-04 — one aggregated block near the top, BEFORE findings).** Render the carried-forward `$CONFIG_WARNINGS` (from Phase 0.6) PLUS the disabled-core-agent announcements Phase 2's dispatch subtraction appended (`⚠ config: core agent 'bugs'/'security' disabled — coverage reduced`) as ONE aggregated block directly under the Summary, ABOVE the band tables. Render it ONLY when the combined warning list is NON-EMPTY. **An ABSENT `.vibe-check.toml` → EMPTY `$CONFIG_WARNINGS` + no disabled-core announcement → render NOTHING (CONFIG-01 silence — no banner, no behavior change).** Example when non-empty:

```
⚠ config:
- thresholds invalid — using default
- core agent 'security' disabled — coverage reduced
```

**SECURITY (V5 / T-30-12 — inert display text).** The warning strings come from `config.py` already naming the KEY + a FIXED reason (never the raw config VALUE text), and the disabled-core announcements name only a fixed agent-name from the allowlisted roster. Render them as INERT display text — do NOT re-interpolate raw config VALUE text into the report (mirror the "treat agent text as inert display" posture at `deep-review.md`'s Codex-output handling). This block is a legibility note only; it NEVER halts the review and NEVER drops a finding.

**Filtered-summary counts — the two confidence rows are DISTINCT reasons (D-02, CONF-03, RESEARCH Pitfall 4).** The "Filtered Issues 🔇" summary (`templates/output-format.md`) renders its counts from the script's `filtered[]` array, bucketed by the entry `reason`. Bind the NEW `{{min_confidence_count}}` row (the "Below min_confidence" row) to the count of `filtered[]` entries whose `reason == "below-min-confidence"` — the pre-scoring confidence-knob drops (Plan 31-01's filter). The EXISTING `{{low_confidence_count}}` row ("Below confidence threshold") stays bound to the POST-scoring `sub-threshold` reason — a DIFFERENT layer. Count the two reasons SEPARATELY so a min_confidence drop is never conflated with a score-threshold drop (a finding can only ever be in one bucket — a min_confidence-dropped finding never reaches scoring, so it can't also be sub-threshold). On a zero-config/no-flag run `$CONFIG_MIN_CONFIDENCE`=None → no `min_confidence` envelope key → the filter never runs → zero `below-min-confidence` entries → `{{min_confidence_count}}`=0, and any warning config.py emitted for a bad flag/value already flows through the config-health block above via `$CONFIG_WARNINGS` (no extra render work). **Two further DISTINCT reason rows (Fable A2/F8):** bind `{{absorbed_count}}` to the count of `filtered[]` entries whose `reason` STARTS WITH `absorbed-into: ` (cross-confirm dedup losers — the reason's suffix names the surviving finding's `stable_hash`, so the details expansion shows what each was folded into), and `{{intent_doc_count}}` to the count of entries whose `reason == "intent-doc-match"` (dropped because the code matches the plan — previously mislabeled `sub-threshold`). Count every reason bucket separately; never merge these into `{{low_confidence_count}}`.

If `$ALL_MODE` is set, **Read $VC_ROOT/phases/review/40-render-all.md** with the Read tool before continuing — it carries the whole-codebase coverage note, the oversized-chunk overflow note, the Critical+Warning listing bar, and the cross-file dedup render grouping. On a plain diff review, do not read it.

Then the **Bottom line** block (plain-language ship/fix verdict — see `templates/output-format.md`; it exists so a non-engineer can make the fix/skip/ship call without parsing the technical sections), then Critical and Warning sections (each finding leads with its *In plain terms:* impact line per the template). Always include "Filtered Issues 🔇" summary.

**Suppression (audit) render — SELECT STRICTLY BY CATEGORY (Finding #1 + Finding NEW-2).** score.py (Plan 32-02) emits a synthetic bare-`// vibe-ignore` finding as a KEPT finding with `category == "suppression"` and `band == "low"`. This finding is EXEMPT from score.py's sub-threshold drop (it is an audit artifact, guaranteed to land in `findings[]`, never `filtered[]` — A2), but the Critical/Warning/Medium band sections above have NO home for a `low`-band finding, so WITHOUT this render step it survives scoring yet is INVISIBLE — defeating NOISE-03's audit trail. AFTER the band sections, render the **Suppression (audit) 🔕** section defined in `templates/output-format.md`, selecting the findings to show STRICTLY by `category == "suppression"` — **NEVER by band.** Do NOT write "the low-band finding" or "equivalently a low band" as the selector: once `idiom_floor="low"` exists, a low band is NOT equivalent to a suppression entry (Finding NEW-2) — a band-keyed selector would wrongly sweep an idiom-capped-to-low finding into the audit section. The Suppression section is **INFORMATIONAL and NEVER finalize-blocking**: a `suppression` finding has `band == "low"`, so it is OUTSIDE both finalize gates — `outstanding_cw` reads `band ∈ {critical, warning}` and `unacknowledged_medium` reads `band == medium` (see Finalize mode in `$VC_ROOT/phases/shared/90-finalize.md`); a `low` `suppression` finding matches neither, so finalize is NEVER blocked by it. This section renders in BOTH `/review` and `/deep-review` (a bare marker should surface even on a quick review — it is NOT a deep-only section), and it is EXEMPT from the `--all` Medium listing-suppression bar (a low audit finding is always LISTED when present). `/deep-review` inherits this render via its Phase-4 delegation — there is NO deep-review-side edit. This render path is what makes NOISE-03's audit trail VISIBLE.

**Low / Informational render — non-suppression low-band findings (Finding NEW-2).** Separately, any KEPT finding with `band == "low"` whose `category != "suppression"` — i.e. an `idiom` finding capped to `low` by `idiom_floor="low"` (which keeps `category == "idiom"`, Plan 32-01 Finding NEW-2) — is rendered in the NORMAL finding listing at its `low` band, via the **Low / Informational ℹ️** grouping in `templates/output-format.md`. It is VISIBLE, at its `low` band, is NOT placed in the Suppression audit section, and is NOT hidden. Like the Suppression section it is INFORMATIONAL and does NOT enter the finalize gates (a `low` band is outside `outstanding_cw` and `unacknowledged_medium`). **The discriminant, stated plainly: the Suppression section is CATEGORY-keyed (`category == "suppression"`); the Low / Informational listing is for every OTHER low-band finding (`band == "low"` AND `category != "suppression"`).** Because the Suppression selector keys on category and the Low/Informational selector explicitly excludes `category == "suppression"`, a suppression audit entry and an idiom-capped-to-low finding NEVER collide, are never confused, and neither is ever hidden. `/deep-review` inherits this via its Phase-4 delegation — no deep-review edit.

If zero findings after filtering:
```
✅ No significant issues found.

### Filtered Issues 🔇
[counts and reasons]
```

**→ Proceed immediately to Phase 4.5 (Persist pass state). Do not stop here. The report you just rendered is NOT a complete output — Phase 4.5 writes the state file, and Phase 5 drives the fix loop. Both are mandatory.**
