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

---

### Critical 🔴
Must fix before commit:

| Agent(s) | File:Line | Issue | Conf | Status |
|----------|-----------|-------|------|--------|
| {{agents_csv}} | `{{file}}:{{line}}` | {{title}} | {{score}} | {{status}} |

After the table, for each Critical finding render:

**`{{file}}:{{line}}` — {{title}}** (found by: {{agents_csv}})

{{problem}}

```diff
- {{suggested_fix.old}}
+ {{suggested_fix.new}}
```

Why: {{why_it_matters}}

---

### Warning 🟠
Should fix:

[same table + per-finding format as Critical]

### Medium 🟡 *(deep review only)*
Consider fixing or acknowledge in `--finalize`:

[same table + per-finding format as Critical]

**Status values:** `NEW`, `PERSISTED (pass N)`, `FIXED-SINCE-LAST`, `NEEDS-RECHECK`. Single-pass mode: always `NEW`.

**`{{agents_csv}}`:** comma-separated agents that flagged it (after dedup).

---

### Filtered Issues 🔇

*{{filtered_count}} issues were not reported:*

| Reason | Count |
|--------|-------|
| Pre-existing (not in diff) | {{pre_existing_count}} |
| Below confidence threshold | {{low_confidence_count}} |
| Linter territory | {{linter_count}} |
| Silenced by comment | {{silenced_count}} |

<details>
<summary>View filtered issues</summary>

- `{{file}}:{{line}}` - {{issue}} *({{filter_reason}})*

</details>

---

### Architectural Notes 📐 *(deep review only)*

- Pattern consistency: {{icon}} {{observation}}
- Test coverage: {{icon}} {{observation}}
- Documentation: {{icon}} {{observation}}
- Dependencies: {{icon}} {{observation}}

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
| Linter territory | {{linter_count}} |

> These were excluded because they don't meet the confidence threshold or are outside your changes.
```

### Section Inclusion Rules

| Section | Quick Review | Deep Review |
|---------|--------------|-------------|
| Critical (95-100) | ✅ | ✅ |
| Warning (80-94) | ✅ | ✅ |
| Medium (70-79) | ❌ | ✅ |
| Filtered Issues Summary | ✅ | ✅ |
| Filtered Issues Details | ❌ | ✅ |
| Architectural Notes | ❌ | ✅ |
| Impact Analysis | ❌ | ✅ |

### Filter Transparency

**Always show filtered count.** This builds trust by explaining:
1. The tool found X issues total
2. Y were reported (meet confidence threshold)
3. Z were filtered (with reasons why)

Users can expand to see filtered issues if they want second opinions.
