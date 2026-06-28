---
phase: 23-framework-skill-agent-adopt-guardrail-ship
plan: 01
subsystem: vibe-check review fleet
tags: [framework-skill, noise-guardrail, severity-scoped-ceiling, version-bump, validate-and-adopt]
requires:
  - "commit 95c6834 (the dogfooded framework-skill agent + its four wiring sites)"
provides:
  - "framework-skill.md carrying the NOISE-01 severity-scoped (low-tier only) agent_confidence ≤ 45 ceiling"
  - "plugin.json at version 2.6.0"
affects:
  - plugins/vibe-check/agents/framework-skill.md
  - plugins/vibe-check/.claude-plugin/plugin.json
tech-stack:
  added: []
  patterns:
    - "Severity-scoped confidence ceiling: the ≤45 cap rides the `low` severity tier (taste/differentiator checks), never a category — mirrors framework-fastapi.md's differentiator tier"
key-files:
  created:
    - .planning/phases/23-framework-skill-agent-adopt-guardrail-ship/23-01-SUMMARY.md
  modified:
    - plugins/vibe-check/agents/framework-skill.md
    - plugins/vibe-check/.claude-plugin/plugin.json
decisions:
  - "D-01 ADOPT: Task 1 verified commit 95c6834 against the approved design rather than re-authoring it; all assertions passed with zero drift, so no file was touched in Task 1."
  - "D-03/D-04 REVISED: the ≤45 ceiling is severity-scoped (rides the `low` tier) — capped ONLY the low taste/differentiator checks (soft structure nitpicks + 4 content prose nitpicks); the 2 content safety checks (destructive/fragile workflow, missing validation loop) plus wiring/description/scripts/hard-disclosure stay uncapped at natural confidence."
  - "D-05 honored: no skill-category key added to score.py CATEGORY_DOMAIN (negative grep confirmed absent)."
  - "D-08/CLOSE-01: plugin.json bumped 2.5.0 → 2.6.0; no tag, no push (handled at milestone close)."
metrics:
  duration: "~1 task-edit pass (verify + one substantive edit + one mechanical bump)"
  tasks-completed: 3
  files-modified: 2
  completed: 2026-06-28
---

# Phase 23 Plan 01: framework-skill Agent — Adopt, Guardrail & Ship Summary

Validated-and-adopted the dogfooded `framework-skill` reviewer (commit 95c6834), added the one NOISE-01 noise guardrail — a severity-scoped `agent_confidence ≤ 45` ceiling that rides the `low` taste/differentiator tier only, never a category — and bumped the plugin to 2.6.0.

## What This Plan Did

This was a VALIDATE-AND-ADOPT phase, not a build. Task 1 verified the already-committed agent + wiring against the approved design (no re-authoring). Task 2 applied the single substantive edit (NOISE-01). Task 3 made the mechanical version bump.

## Task 1 — Verify the adopted agent + wiring (SKILL-01..04, WIRE-01, WIRE-02)

VERIFICATION only — every assertion passed against the existing tree at HEAD 95c6834, so **no file was re-authored and no residual drift was found** (nothing to commit for Task 1).

| Assertion | Result |
|-----------|--------|
| triage.md emits `"skill"` by **file shape** (SKILL.md / `agents/*.md` with `name`+`description` frontmatter / plugin manifest), explicitly NOT keyed on imports | PASS |
| index.md Agent Selection Matrix has a `framework-skill` row (`grep -c` = 1) | PASS |
| commands/review.md dispatch row present (`grep -c framework-skill` = 1) | PASS |
| commands/deep-review.md dispatch row present (`grep -c framework-skill` = 1) | PASS |
| framework-skill.md frontmatter has `name: framework-skill` AND `model: sonnet` | PASS |
| Output section names exactly the six categories `description / disclosure / structure / content / scripts / wiring` | PASS |
| References `agent-output-schema.md` AND pins `agent_confidence` as integer 0–100 | PASS |
| Plugin-wiring (half-wired-addition) Checks section present (covers missing matrix row, missing dispatch row, missing triage signal, `name:` mismatch, missing `model:`, output-contract drift, stale agent-count prose) | PASS |
| WIRE-02 agent-count prose coherent: `react / fastapi / skill` in the MAX list, `floor + 7`, `3–11` agents/chunk range — no stale pre-skill 6-agent figure | PASS |
| Task 1 `<automated>` verify block | PASS |

## Task 2 — NOISE-01 severity-scoped confidence ceiling (the one substantive edit)

**Commit:** `b6760c3` (`feat(23-01): add NOISE-01 severity-scoped confidence ceiling to framework-skill`)

Added to `framework-skill.md`, mirroring framework-fastapi.md's differentiator tier (the cue rides the severity bullet, not the category name):

1. **Top-of-Checks ceiling note** — states the cap is severity-scoped, rides the `low` tier only, cues `agent_confidence ≤ 45` on each low-tier bullet, and explicitly says it NEVER touches a finding emitted at `medium`/`high`. (Split into two paragraphs so the `≤ 45` token-bearing sentence carries no category word — see invariant note below.)

2. **Inline `[low — cue ≤ 45]` markers** on the soft `structure` nitpicks (ref file >100 lines without a TOC; verbose re-explanation of what Claude already knows) and the four `content` prose nitpicks (time-sensitive-info placement, inconsistent terminology, Windows backslash paths, many-interchangeable-options-vs-one-default).

3. **The two `content` safety checks left UNCAPPED** with explicit `[medium/high — natural confidence, NOT capped]` markers: "Workflow steps without a clear sequence, or a fragile/destructive operation given high freedom" and "Critical/destructive operations lacking a validation or feedback loop."

4. **New `## Severity calibration` section** with the scoring policy table:

   | severity | weight | example check | confidence policy | in-diff score | clears ≥ 70? |
   |----------|--------|---------------|-------------------|---------------|--------------|
   | low | −20 | terminology inconsistency; ref >100 lines, no TOC | cue ≤ 45 | 45 | no — filtered-to-count |
   | medium | −8 | critical op missing a validation/feedback loop | natural (aim ≥ 58) | ≥ 70 | yes |
   | high | −3 | destructive/fragile workflow given high freedom | natural (aim ≥ 53) | ≥ 70 | yes |

   The section also names the high-value classes that stay uncapped regardless of category: `wiring` (Uncapped), `description` (Uncapped), `disclosure` hard limits (Uncapped), `scripts` hygiene (Uncapped), and the two `content` safety checks (Uncapped, natural medium/high). It explains WHY severity-scoped not category-wide: the cap is on `agent_confidence` while severity weight is added separately, so a blanket cap could not be escaped by raising severity, and with no CATEGORY_DOMAIN twin there is no cross-confirm rescue.

### Exact NOISE-01 ceiling wording added (the operative cap-token lines)

- `**Confidence ceiling (severity-scoped — rides the \`low\` tier only).** Taste-level / differentiator nitpicks are emitted at severity \`low\`; cue \`agent_confidence ≤ 45\` on every such low-tier bullet (the inline \`[low — cue ≤ 45]\` markers below).`
- inline: `\`[low — cue ≤ 45]\` Reference file >100 lines without a table of contents at the top.`
- inline: `\`[low — cue ≤ 45]\` Verbose re-explanation of things Claude already knows ...`
- intro line: `The first four bullets are taste-level differentiator nitpicks — emit them at severity \`low\` with the \`≤ 45\` cue. The last two are genuine safety checks — emit them at \`medium\`/\`high\` with NATURAL confidence; they are never capped ...`
- inline: `\`[low — cue ≤ 45]\` Time-sensitive info in the main body ...` / `Inconsistent terminology ...` / `Windows-style backslash paths ...` / `Offering many interchangeable options ...`
- table row: `| low | −20 | terminology inconsistency; ref >100 lines, no TOC | cue ≤ 45 | 45 | no — filtered-to-count |`

### Invariant compliance (the fixture-proven pre-filter)

The plan's INVARIANT requires EVERY line carrying a `≤ 45`/`<= 45` token to (a) name the low/differentiator/taste tier AND (b) NOT mention `content`/`structure`/`subjective`/`categor*`/`findings` on that same line. The first draft of the top-of-Checks note tripped this because it contained the word "category" twice on a `≤ 45` line; it was split so the cap-token sentence carries no category word and the "do not bind to a whole bucket" caveat lives on a separate (token-free) line. Final invariant check: **PASS** (zero violations across all nine cap-token lines).

### Task 2 acceptance / verify results

| Check | Result |
|-------|--------|
| `≤ 45` cue tied to low-severity/differentiator/taste language (not a "cap the category" statement) | PASS |
| medium/high subjective findings stated to use NATURAL confidence + NOT capped, naming the 2 content safety examples | PASS |
| high-value classes (`wiring`/`description`) co-occur with uncapped language | PASS |
| six category names still present (22 occurrences) + Output line lists exactly the six, unchanged | PASS |
| Output contract unchanged: schema ref + integer 0–100 pin + empty-JSON fallback `{"agent":"framework-skill","findings":[],"agent_notes":[]}` | PASS |
| **score.py NOT modified** — no skill-category key in CATEGORY_DOMAIN (negative grep ABSENT) [D-05] | PASS |
| only framework-skill.md changed by this task (`git diff --name-only`) | PASS |
| INVARIANT per-line check (positive + negative) | PASS |
| Task 2 `<automated>` verify block | PASS |

## Task 3 — Version bump 2.5.0 → 2.6.0 (CLOSE-01)

**Commit:** `62f1915` (`chore(23-01): bump plugin to 2.6.0 (CLOSE-01)`)

- **Before:** `"version": "2.5.0"` → **After:** `"version": "2.6.0"`
- Single-line diff; no other manifest field changed (name, description, author, repository, license, keywords all intact).
- `python3 json.load` parse + `assert version == "2.6.0"`: PASS. JSON remains valid.
- No tag created, no push performed (the `v2.6` tag + publish are handled at milestone close).

## score.py non-modification confirmation (D-05)

`scripts/score.py` was NOT touched in any task. Negative grep confirms none of the six skill categories (`description`, `disclosure`, `structure`, `content`, `scripts`, `wiring`) appear as a `CATEGORY_DOMAIN` key — these categories correctly stand alone with no cross-agent twin. Adding any entry would have been the bug; absence confirmed.

## Deviations from Plan

None — plan executed exactly as written. Task 1 found zero drift (so no file change was needed for it, as the plan anticipated). The only adjustment during Task 2 was the two-paragraph split of the ceiling note to satisfy the per-line INVARIANT (a wording arrangement the plan's execution rule explicitly directs: "write every ≤45 line so it names the low/differentiator/taste tier and does NOT mention content/structure/subjective/category/findings on that same line"). This is conformance to the plan's invariant, not a deviation.

## Authentication Gates

None.

## Known Stubs

None.

## Phase-level verification (all PASS)

1. Wiring complete in all four sites (triage file-shape / index / review / deep-review): PASS
2. NOISE-01 severity-scoped ceiling present (≤45 tied to low/differentiator/taste; medium/high uncapped, naming validation-loop/destructive/fragile-workflow): PASS
3. Category set + output contract intact (empty-JSON fallback + six categories on the Output line): PASS
4. D-05 non-change — no skill twin in score.py: PASS
5. Version bumped to 2.6.0 (json.load assert): PASS

## Notes for the downstream deep-review (VERIFY-01)

The wiring was left genuinely complete (WIRE-02 prose coherent, all four dispatch sites present), so the orchestrator's `/vibe-check:deep-review` over this phase's own changes should not self-flag the agent as a half-wired addition. Treat any self-flag from that gate as a real defect to fix, not a false positive.

## Self-Check: PASSED

- framework-skill.md exists and was modified: FOUND
- plugin.json exists at 2.6.0: FOUND
- Commit b6760c3 (Task 2): FOUND
- Commit 62f1915 (Task 3): FOUND
