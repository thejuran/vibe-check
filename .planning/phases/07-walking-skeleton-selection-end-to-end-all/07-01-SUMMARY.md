---
phase: 07-walking-skeleton-selection-end-to-end-all
plan: 01
subsystem: vibe-check-plugin / --all whole-codebase selection
tags: [skip-rules, single-source-of-truth, D-06, SELECT-03, prompt-only, template-snippet]
dependency_graph:
  requires: []
  provides:
    - "plugins/vibe-check/templates/skip-rules.md — canonical skip-pattern list for --all selection"
  affects:
    - "plan 02 (review.md mode 5) — will reference this snippet via prose-pointer"
    - "plan 03 (deep-review.md) — will reference this same snippet (D-06 drift-proof)"
tech_stack:
  added: []
  patterns:
    - "Template snippet anatomy mirrored from templates/scoring.md & output-format.md (YAML frontmatter single name: key + heading + 'Applied by the orchestrator' framing)"
    - "Prose-pointer single-source-of-truth convention (D-06) — no @-import, no inline duplication"
key_files:
  created:
    - "plugins/vibe-check/templates/skip-rules.md"
  modified: []
decisions:
  - "Chose templates/ snippet home (over a canonical inline block) — matches every other shared template in the plugin and the prose-pointer convention deep-review already uses for review.md"
  - "Left agents/triage.md byte-untouched; named its line-29 files_to_skip as the baseline floor this snippet supersedes/extends — consolidation deferred as a later-cleanup discretion item (RESEARCH Open-Q2)"
  - "Picked a reasonable binary/image extension set (added *.jpeg/*.gif/*.ico/*.woff/*.woff2/*.ttf/*.zip/*.gz/*.tar/*.so/*.dylib/*.exe/*.wasm beyond triage's *.bin/*.png/*.jpg/*.pdf) — the lock is the category, not the exact list (CONTEXT.md Claude's-Discretion)"
metrics:
  duration: ~6 min
  completed: 2026-06-22
  tasks: 1
  files: 1
---

# Phase 7 Plan 01: Shared Skip-Rules Snippet Summary

Created the single canonical skip-pattern list (`templates/skip-rules.md`) that both `--all` command branches will reference, so a skip-rule change lands in one place and cannot drift between `review.md` and `deep-review.md` (D-06).

## What Was Built

A new prompt-only template snippet at `plugins/vibe-check/templates/skip-rules.md` (95 lines). It mirrors the existing `templates/scoring.md` / `templates/output-format.md` anatomy: YAML frontmatter with a single `name: Skip Rules` key, a `# Skip Rules` heading, and an "Applied by the orchestrator during `--all` whole-tree selection" framing sentence.

The body:
- Declares itself the **single source of truth / canonical** skip list for `--all` selection, applied by both commands via the prose-pointer convention, with an explicit "do NOT duplicate this list inline" instruction.
- Names `agents/triage.md` line 29 (`files_to_skip`) as the **baseline floor** it supersedes/extends, and states triage.md is left untouched in Phase 7 (consolidation is a later-cleanup discretion item).
- Enumerates the skip patterns under the **four D-05 category headings** (vendored/dependency dirs, generated/minified, lockfiles, binary/image/font/archive) so the list is human-auditable — the stated reason a markdown denylist was chosen over opaque git `:(exclude)` pathspec magic.
- States plainly that it is a **static pattern list only** — no chunking, no file-count cap, no `git ls-files` invocation, no selection logic (that lives in plan 02's review.md mode 5).

## Task Completion

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Author the shared skip-rules snippet | 935c473 | plugins/vibe-check/templates/skip-rules.md |

## Verification

Plan `<verify>` automated check — **PASS**:
```
test -f skip-rules.md && grep node_modules|vendor|.venv && grep -i single source|canonical && grep -i triage  → PASS
```

Acceptance criteria (all met):
- Frontmatter with `name:` key, matching scoring.md/output-format.md anatomy — confirmed.
- At least one pattern from EACH D-05 category present: vendored (`node_modules`) HIT, generated/minified (`*.min.js`) HIT, lockfile (`*.lock`/`package-lock.json`) HIT, binary/image (`*.png`/`*.bin`) HIT.
- Single-source-of-truth / canonical prose line — present (grep `single source|canonical` HIT).
- References `triage` as the baseline floor — present (grep `triage` HIT).
- NO chunking / file-count-cap / `git ls-files` invocation logic — confirmed: the only mentions of `git ls-files` are (a) a framing sentence stating *when* the rules apply and (b) an explicit negation ("carries no chunking, file-count cap, `git ls-files` invocation, or any other selection logic"). No executable selection logic exists.
- `min_lines: 15` — file is 95 lines.

Scope guard (no-regression floor): `git status --short` showed exactly ONE new file added (skip-rules.md) and no other file touched. triage.md, review.md, deep-review.md are byte-untouched by this plan.

Note: the BEHAVIORAL acceptance criterion (a `/vibe-check:review --all` run applying these skip rules) is explicitly deferred to the Phase 7 wave merge, once plans 02/03 land and wire the commands to this snippet.

## Deviations from Plan

None — plan executed exactly as written. The skip-pattern extension set (binary/image extras) was chosen at the discretion CONTEXT.md explicitly grants (the lock is the four categories, not the exact extensions); this is authored discretion, not a deviation.

## Known Stubs

None. This snippet is a complete static pattern list; it is intentionally consumed by plans 02/03 (which wire the commands to it) — that is the planned interface-first sequencing, not a stub.

## Threat Flags

None. This plan creates a static markdown pattern list with no user input, no shell execution, and no path resolution (per the plan's threat model T-07-01 mitigated by D-06's single-source-of-truth design; T-07-SC accepted — no package installs). The user-supplied path/glob surface (SELECT-04) is introduced in plan 02, not here.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/templates/skip-rules.md (committed in 935c473)
- FOUND: commit 935c473 in git log
