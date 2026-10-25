---
name: Output Format Template
---

## Output Format

Use this template for presenting review results. Always show what was filtered to build trust.

### With Issues Found

```
## {{review_type}} Review

**Summary:** Reviewed {{file_count}} files, {{line_count}} lines changed

| Found | Reported | Filtered |
|-------|----------|----------|
| {{total_issues}} | {{reported_issues}} | {{filtered_issues}} |

### Bottom line

{{2–4 sentences, plain language, zero jargon — written for a non-engineer making the fix/skip/ship call. Answer two questions: would you ship this as-is, and what breaks for users if you do? Group findings by product consequence, not by category. e.g. "Two of these can crash the app for real users — the missing null check and the race condition — fix those before shipping. The other three won't be felt by users today but make future changes riskier. Verdict: fix the first two, ship, defer the rest."}}

---

### Critical 🔴
Must fix before commit:

| Agent(s) | File:Line | Issue | Conf | Status |
|----------|-----------|-------|------|--------|
| {{agents_csv}} | `{{file}}:{{line}}` | {{title}} | {{agent_confidence}} | {{status}} |

After the table, for each Critical finding render:

**`{{file}}:{{line}}` — {{title}}** (flagged by: {{members_list}})

Confidence: {{agent_confidence}}

*In plain terms:* {{one sentence of user/product impact — what breaks, for whom, when. No jargon, no CWE numbers, no restating the technical problem. Translate, don't summarize: "users who hit this endpoint with an expired session see a crash instead of a login prompt", not "null reference on user object". Derive from problem + why_it_matters.}}

{{problem}}

Render `{{current_code}}` in a fenced code block whose fence length you size per finding. Before emitting the snippet, scan it for the longest run of consecutive backtick characters it contains — call it N (N=0 if the snippet has no backticks). Open AND close the block with a tagless fence (no language tag) of `max(3, N+1)` backticks. Emit the snippet verbatim between those fences — do not strip, escape, or otherwise mutate it. (CommonMark: a fence of K backticks can only be closed by a run of ≥ K backticks, so a fence of N+1 backticks cannot be closed by any internal run — the snippet can't escape its block and spoof the report with fake headings, links, or approval text.)

{{#if fix_hint}}Fix direction: {{fix_hint}}{{/if}}

Why: {{why_it_matters}}

*The actual patch is produced by the `fix` agent when you accept this finding in the fix loop — it reads the file and edits it semantically, so no diff is pre-baked here.*

---

### Warning 🟠
Should fix:

[same table + per-finding format as Critical]

### Needs verification ⚠️

*Unresolved assessments — a concrete failure the change could cause that the reviewer could not confirm or rule out. Every item here is actionable: confirm (send to the fix agent), dismiss or defer it by number on the decision card. This group is never filtered.*

**SELECTION IS BY BAND LITERAL.** Render a row for each finding whose `band == "needs-verification"` — and only those; never from `filtered[]`.

| File:Line | Item | Trigger | Path | Consequence |
|-----------|------|---------|------|-------------|
| `{{file}}:{{line}}` (or `{{needs_verification.symbol}}` when `line` is null) | {{title}} | {{needs_verification.trigger}} | {{needs_verification.path}} | {{needs_verification.consequence}} |

Per-row suffix when the row's `status == "needs-recheck"`:
- ` — code changed since last pass; recheck requested from the {{agent}} lane` when that lane was dispatched this pass;
- ` — code changed since last pass; Fix not yet confirmed: no eligible reviewer ran this pass — retried on the next run that reviews changes; or run /deep-review; or dismiss` when no eligible reviewer ran (a Codex-raised item, a gated or disabled lane, with no reviewer to route it to). When one did, the lane that re-checked it is named instead. The same `Fix not yet confirmed: …` line applies to any other open row that carries a `verdict: fix not` reason, Needs-verification rows included when they carry no `verdict: confirmed fix` reason (`phases/review/40-render.md`). A Needs-verification item an independent re-check could not close because its file and tests are unchanged since it was raised shows ` — Stays open for your decision: a re-check closes a Needs-verification item only after its file or tests change` instead: one reviewer's word on unchanged code never removes it.

*{{nv_dropped_count}} item(s) not admitted at render (no location or no concrete trigger/path/consequence) and
{{nv_dropped_weak_count}} weak co-located note(s) that neither qualified as findings nor as Needs-verification items — counted, not shown.*

*Render the table only when at least one `band == "needs-verification"` finding is present; render the footer line above ALWAYS, even when both counts are 0, so the count is always published. The group is finalize-BLOCKING: an undecided Needs-verification item holds the ship verdict until it is confirmed, dismissed or deferred.*

### Medium 🟡 *(deep review only)*
Consider fixing or acknowledge in `--finalize`:

[same table + per-finding format as Critical]

**Status values:** `NEW`, `PERSISTED (pass N)`, `FIXED-SINCE-LAST`, `NEEDS-RECHECK`. Single-pass mode: always `NEW`.

**`{{agents_csv}}`:** comma-separated agents that flagged it (after dedup).

**`{{members_list}}`:** from the finding's `members` array (survivor first). ONE entry → the agent name alone (identical to the old "found by"). TWO or more → `agent — title; agent — title` in array order, every member's OWN title kept (v2.10 Wave 1 H-LANE, D-03/D-14): a collapsed site shows what each lane said, so a reader sees the security title even when another lane leads.

---

### Filtered Issues 🔇

*{{filtered_count}} issues were not reported:*

| Reason | Count |
|--------|-------|
| Pre-existing (not in diff) | {{pre_existing_count}} |
| Below confidence threshold | {{low_confidence_count}} |
| Below min_confidence | {{min_confidence_count}} |
| Linter territory | {{linter_count}} |
| Silenced by comment | {{silenced_count}} |
| Absorbed into a co-located finding | {{absorbed_count}} |
| Matches intent doc | {{intent_doc_count}} |

<details>
<summary>View filtered issues</summary>

- `{{file}}:{{line}}` - {{issue}} *({{filter_reason}})*

</details>

---

### Suppression (audit) 🔕

*Bare `// vibe-ignore` markers found with NO reason — informational, never blocking.*

**SELECTION IS BY CATEGORY, NOT BY BAND.** Render a row here for each KEPT finding whose `category == "suppression"` — and ONLY those. A `low` band alone is NOT a suppression entry: an `idiom` finding capped to `low` by `idiom_floor="low"` also carries `band == "low"` but has `category == "idiom"`, so it is NOT rendered here — it renders in the Low / Informational listing below. Never select this section by band; a band-keyed selector would wrongly sweep an idiom-capped-to-low finding into this audit section (Finding NEW-2).

| File:Line | Issue |
|-----------|-------|
| `{{file}}:{{line}}` | {{title}} |

These are bare `// vibe-ignore` markers with no reason. They do not suppress the nearby finding and they never block the ship/fix verdict — they are surfaced only to keep suppressions auditable. To suppress the nearby finding, add a reason: `// vibe-ignore: <why>`. To drop the audit entry, remove the marker.

*Render this section only when at least one `category == "suppression"` finding is present (omit the empty header). It is NON-blocking: a `suppression` finding has `band == "low"`, outside both finalize gates (`outstanding_cw` = band ∈ {critical, warning}; `unacknowledged_medium` = band == medium), so it never enters the ship/fix verdict.*

---

### Low / Informational ℹ️

*Low-band findings that are NOT suppression audit entries — visible, at low band, never blocking.*

Render a row here for each KEPT finding with `band == "low"` whose `category != "suppression"` — an `idiom` finding capped to `low` by `idiom_floor="low"` is the canonical case. Use the normal finding row format (same columns as the band sections). This is where a low-band finding that is NOT a suppression audit entry lands, so it is never hidden and never mislabeled as suppression.

| Agent(s) | File:Line | Issue | Conf | Status |
|----------|-----------|-------|------|--------|
| {{agents_csv}} | `{{file}}:{{line}}` | {{title}} | {{agent_confidence}} | {{status}} |

**The two low-band kinds are disambiguated by CATEGORY:** `category == "suppression"` → the Suppression (audit) section above; every other low-band finding (`category != "suppression"`) → this Low / Informational listing. The two selectors are mutually exclusive by construction, so the two low-band kinds never collide and neither is ever hidden.

*Render this section only when at least one non-suppression low-band finding is present (omit the empty header). It is NON-blocking: a `low` band is outside `outstanding_cw` and `unacknowledged_medium`, so it never enters the ship/fix verdict.*

#### Worked render example — two DISTINCT low-band findings (Finding NEW-2 proof)

Suppose one result carries these two low-band findings:

- Finding **X** — `src/util.ts:40`, `category: "suppression"`, `band: "low"`, title `suppression without reason` (a bare `// vibe-ignore` score.py synthesized).
- Finding **Y** — `src/util.ts:12`, `category: "idiom"`, `band: "low"`, title `prefer const over let` (a real idiom finding that scored into a higher band but was CAPPED to `low` by `idiom_floor="low"`).

The render MUST place them in DIFFERENT sections, keyed on category:

- **X** renders in **Suppression (audit) 🔕** (its `category == "suppression"`).
- **Y** renders in **Low / Informational ℹ️** (its `category == "idiom"` ≠ `"suppression"`), VISIBLE at its `low` band — it is NOT in the Suppression section and is NOT mislabeled as a bare-marker audit entry.

Assert-by-reading: Y is present, at `low` band, OUTSIDE the Suppression section; X is present, INSIDE the Suppression section. This is the render-level proof that a documented `idiom_floor="low"` value does not break the report — the category-vs-band discriminant keeps the two low-band kinds correctly routed.

---

### Architectural Notes 📐 *(deep review only)*

- Pattern consistency: {{icon}} {{observation}}
- Documentation: {{icon}} {{observation}}
- Dependencies: {{icon}} {{observation}}

<!-- Test coverage is NOT shown here: the test-sufficiency agent owns coverage display (its scored findings render in the Critical/Warning/Medium tables, and its agent_notes render in the deep-review "Test Coverage 🧪" section per commands/deep-review.md Phase 4). Keeping a coverage line under Architectural Notes too would double-report it under two owners. -->


### Impact Analysis 💥 *(deep review only)*

- **Affected files:** {{affected_files}}
- **Blast radius:** {{blast_radius}}
- **Breaking changes:** {{breaking_changes}}
```

### Icons

- ✅ Good / Passes
- ⚠️ Warning / Needs attention
- ❌ Problem / Fails
- ℹ️ Informational
- 🔇 Filtered / Not reported

### No Issues Found

```
## {{review_type}} Review

**Summary:** Reviewed {{file_count}} files, {{line_count}} lines changed

✅ **No significant issues found. Code looks good for commit.**

### What Was Checked
- 🐛 Bugs & Logic: null access, race conditions, resource leaks
- 🔐 Security: injection, XSS, hardcoded secrets, auth bypass
- 📋 Compliance: CLAUDE.md rules, team conventions
- 📐 Architecture: patterns, coupling, dependencies *(deep only)*

### Filtered Issues 🔇

*{{filtered_count}} potential issues were filtered:*

| Reason | Count |
|--------|-------|
| Pre-existing (not in diff) | {{pre_existing_count}} |
| Below confidence threshold | {{low_confidence_count}} |
| Below min_confidence | {{min_confidence_count}} |
| Linter territory | {{linter_count}} |
| Absorbed into a co-located finding | {{absorbed_count}} |
| Matches intent doc | {{intent_doc_count}} |

> These were excluded because they don't meet the confidence threshold or are outside your changes.
```

### Section Inclusion Rules

| Section | Quick Review | Deep Review |
|---------|--------------|-------------|
| Bottom line (plain language) | ✅ | ✅ |
| Critical (95-100) | ✅ | ✅ |
| Warning (80-94) | ✅ | ✅ |
| Medium (70-79) | ❌ | ✅ |
| Filtered Issues Summary | ✅ | ✅ |
| Filtered Issues Details | ❌ | ✅ |
| Needs verification | ✅ (when ≥1 present; footer always) | ✅ (when ≥1 present; footer always) |
| Suppression (audit) | ✅ (when ≥1 present) | ✅ (when ≥1 present) |
| Low / Informational | ✅ (when ≥1 present) | ✅ (when ≥1 present) |
| Architectural Notes | ❌ | ✅ |
| Impact Analysis | ❌ | ✅ |

**Suppression (audit)** and **Low / Informational** are both shown in BOTH Quick and Deep review (a bare marker or a low-capped idiom should surface even on a quick review), each rendered only when at least one matching finding is present. **Both are NON-blocking:** neither participates in the ship/fix verdict — they are audit / informational surfaces (a `low`-band finding is outside `outstanding_cw` and `unacknowledged_medium`). The Suppression section selects by `category == "suppression"`; the Low / Informational listing selects the OTHER low-band findings (`band == "low"` AND `category != "suppression"`). **Needs verification** is also shown in BOTH Quick and Deep review, but unlike Suppression and Low / Informational it IS finalize-blocking: an undecided Needs-verification item holds the ship verdict. It is never filtered, it is selected by `band == "needs-verification"`, and its dropped-count footer renders on every report.

### Filter Transparency

**Always show filtered count.** This builds trust by explaining:
1. The tool found X issues total
2. Y were reported (meet confidence threshold)
3. Z were filtered (with reasons why)

Users can expand to see filtered issues if they want second opinions.
