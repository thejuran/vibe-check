---
allowed-tools: Bash(git:*), Bash(gh pr diff:*), Bash(gh pr view:*), Read, Write, Grep, Glob, Task, AskUserQuestion
description: Quick code review for uncommitted local changes
---

Quick code review for the current diff. Parallel per-domain subagents return JSON findings; orchestrator merges, scores, filters, renders.

## Phase 0 — Resolve scope

Parse `$ARGUMENTS`:

1. **No args (default)**: review all uncommitted changes. Assemble diff via:
   ```bash
   git diff HEAD
   git diff --staged
   git status --short
   ```
   If empty: print "No changes to review." and stop.

2. **PR mode** — `$ARGUMENTS` matches `^[0-9]+$` or contains `/pull/`:
   ```bash
   gh pr diff <ref> --patch
   gh pr view <ref> --json title,body,author,headRefName
   ```
   Stateless. No intent context.

3. **Range mode** — `$ARGUMENTS` matches `<ref>..<ref>`:
   ```bash
   git diff <range>
   ```
   Stateless.

4. **GSD phase mode** — `$ARGUMENTS` is a phase identifier (a directory name under `.planning/phases/` like `02-code-review` or just `02`). Resolve:
   - If exact dir exists at `.planning/phases/<arg>/`, use it.
   - Else if a unique dir starts with `<arg>-`, use it (e.g. `02` → `02-code-review`).
   - Else error: "Phase '<arg>' not found under .planning/phases/. Available: <ls>".

   Compute phase commit range:
   ```bash
   PHASE_DIR=".planning/phases/<resolved-name>"
   PHASE_START=$(git log --reverse --format=%H -- "$PHASE_DIR" | head -1)
   ```
   Diff = `$PHASE_START..HEAD` + staged + unstaged.

   Set `$PHASE_ID = <resolved-name>` for state and intent context.

## Phase 0.5 — Multi-pass state check

State file path:
- GSD phase mode: `.turingmind/state/<$PHASE_ID>.json`
- Other modes (no args / PR / range): `.turingmind/state/$(git rev-parse --show-toplevel | xargs basename)-$(git branch --show-current).json`

1. If state file absent: pass 1, `$LAST_REVIEWED_SHA = null`. Proceed to Phase 0.7 (first-run setup will create `.turingmind/state/` if needed), then to Phase 1. Skip the rest of Phase 0.5.

   If state file present: skip Phase 0.7 (already initialized) and continue with step 2 below.

2. If present: parse it.
   - `$PASS_NUMBER = state.passes[-1].pass_number + 1`
   - `$LAST_REVIEWED_SHA = state.passes[-1].head_sha`
   - `$CARRYFORWARD = state.passes[-1].findings` filtered to status in `["new", "persisted", "needs-recheck"]`

3. Narrow diff to incremental: `$LAST_REVIEWED_SHA..HEAD` + staged + unstaged.

4. If incremental diff empty AND `$CARRYFORWARD` empty: print "No new changes since pass {{$PASS_NUMBER - 1}}." and stop.

5. If incremental diff empty but `$CARRYFORWARD` non-empty: skip agent dispatch, proceed directly to Phase 3 carry-forward check.

## Phase 0.7 — First-run setup

If `.turingmind/` does NOT exist in this repo, this is first use:

1. Create dirs:
   ```bash
   mkdir -p .turingmind/state .turingmind/reviews
   ```

2. Check `.gitignore` for `.turingmind/` entry. If absent, print one-line suggestion to user (do NOT auto-edit):
   ```
   ℹ Tip: add `.turingmind/` to your .gitignore (working state, not artifact). The REVIEW.md from --finalize is the only thing meant to be committed.
   ```

3. Migration check: if `.gsd/turingmind-review/` or `.gsd/reviews/` exists, surface ONE AskUserQuestion:

   Question: "Found old TuringMind state under `.gsd/`. Move to `.turingmind/`?"
   Options:
     - "Yes, move it" → `[ -d .gsd/turingmind-review ] && mv .gsd/turingmind-review .turingmind/reviews-archived-from-gsd; [ -d .gsd/reviews ] && mv .gsd/reviews .turingmind/reviews-old`
     - "No, leave it" → do nothing
     - "Delete the old state" → `rm -rf .gsd/turingmind-review .gsd/reviews`

## Phase 1 — Triage

Dispatch a single Task call to `triage` agent. Prompt:

````
You are the triage agent. Classify this diff.

<diff-stat>
{{git diff --stat <range>}}
</diff-stat>

<changed-files>
{{git diff --name-only output}}
</changed-files>

<repo-root-files>
{{ls of repo root, immediate level}}
</repo-root-files>

{{if $PHASE_ID set: <phase-dir>.planning/phases/$PHASE_ID/</phase-dir>}}

Return JSON per your subagent instructions.
````

Parse JSON. Use:
- `languages` + `frameworks` → Phase 2 agent selection
- `files_to_skip` → exclude from diff sent to other agents
- `size_tier` → large-diff auto-downgrade in Phase 2
- `intent_docs_found` → Phase 1.5 (M6)

## Phase 2 — Dispatch agents in parallel

Single assistant turn, parallel `Task` calls:

| Always | Condition | Agent |
|--------|-----------|-------|
| ✓ | — | `bugs` |
| ✓ | — | `security` |
|  | `CLAUDE.md` or `AGENTS.md` in repo root or changed dir | `compliance` |
|  | `.ts/.tsx/.js/.jsx/.mjs/.cjs` in diff | `language-typescript` |
|  | `.py` in diff | `language-python` |

### Model tiering for `/review`

All agents in `/review` use the model from their frontmatter (`model: sonnet`). No extended thinking. No Opus. Cheap iteration — typical pass ~$0.50.

For Opus on `architecture` + thinking on `security`/`architecture`/`impact`, use `/deep-review`.

Per-call override (e.g. large-diff Haiku downgrade in M5): pass `model: "haiku"` in the Task call. Otherwise omit — agent frontmatter wins.

### Large-diff auto-downgrade

If `triage.size_tier == "large"`, override `model` in Task calls for `language-typescript`, `language-python` (and any other `language-*`/`framework-*`) to `"haiku"`. Tell the user once: "⚠ Large diff (>2000 LOC) — language agents downgraded to Haiku. Bugs, security, compliance keep Sonnet."

Bugs, security, compliance keep Sonnet regardless of size.

Per-agent prompt template:
```
You are the {{agent_name}} agent. Review this diff per your subagent instructions.

<diff>
{{git_diff_output}}
</diff>

<changed-files>
{{filtered_file_list}}
</changed-files>

Use Read if you need full file context. Return ONE JSON object per templates/agent-output-schema.md. JSON only.
```

**Substitution bindings:**
- `{{agent_name}}` — name of the agent receiving this prompt (e.g. `bugs`, `security`).
- `{{git_diff_output}}` — the resolved diff from Phase 0 with `files_to_skip` from Phase 1 removed.
- `{{filtered_file_list}}` — `git diff --name-only` output with `files_to_skip` removed.

`<diff>` block is IDENTICAL across all agent calls (position-stable for prompt caching). Only the agent-name sentence differs.

ALL Task calls in ONE assistant message → parallel execution.

## Phase 3 — Collect, verify, merge, score

0. **Carry-forward check (multi-pass only).** For each finding in `$CARRYFORWARD`:
   - Compute canonical line content at `finding.file:finding.line` in HEAD (strip trailing whitespace).
   - File/line gone → `status: "fixed-since-last"`, exclude from this pass's reported findings.
   - Canonical content matches `finding.details.current_code` first line → `status: "persisted"`, +15 score, include in reported findings.
   - File:line exists but content changed → `status: "needs-recheck"`, add hint to relevant agent's prompt: `<recheck>Previously flagged {{title}} at {{file}}:{{line}}. Verify it still applies.</recheck>`. Include in this pass's dispatch.

   **Note:** Persisted findings still flow through steps 2 (verify in_diff / silenced_marker_nearby), 3 (scoring), and 5 (filter) below. The +15 persistence modifier stacks with the rest of the score formula; persisted findings can still drop below threshold or get silenced.

1. Parse each agent response as JSON. Malformed → log "Agent {name} returned unparseable: {first 200 chars}" and skip.

2. For each finding, verify orchestrator-side:
   - `in_diff`: is `line` in changed-line ranges? Override agent claim if wrong.
   - `silenced_marker_nearby`: grep for `eslint-disable`, `# noqa`, `// nolint`, `@SuppressWarnings`, `#[allow(` within ±2 lines.

3. Apply scoring per `templates/scoring.md`.

4. Cross-agent dedup: group by `(file, line ±2)` AND title substring match. Keep highest-scored, set `attribution = [agents]`. The +10 cross-confirmation bonus is then applied per `templates/scoring.md` (apply once during scoring; not added separately here).

5. Filter `orchestrator_score < 80`. Track filtered counts by reason (silenced, intent-doc-match, sub-threshold).

## Phase 4 — Render results

Per `templates/output-format.md`:

```
## Code Review

**Summary:** Reviewed {{N}} files, {{L}} lines changed

| Found | Reported | Filtered |
|-------|----------|----------|
| {{total}} | {{reported}} | {{filtered}} |
```

Then Critical and Warning sections. Always include "Filtered Issues 🔇" summary.

If zero findings after filtering:
```
✅ No significant issues found.

### Filtered Issues 🔇
[counts and reasons]
```

## Phase 4.5 — Persist pass state

Compute `stable_hash = sha256(file + "\n" + canonical_line_content + "\n" + title)`.

Build pass entry:

````json
{
  "pass_number": $PASS_NUMBER,
  "head_sha": "<current HEAD>",
  "timestamp": "<ISO 8601 UTC>",
  "mode": "review",
  "diff_range": "<resolved range>",
  "agents_run": [<dispatched agents>],
  "findings": [...]
}
````

Append to `state.passes`, write to state file. Create parent dirs as needed (`.turingmind/state/`).

Optional: snapshot this run for debugging:
```bash
RUN_DIR=".turingmind/reviews/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN_DIR"
# Write: diff.patch, agents-dispatched.txt, findings.json
```

Then prune: keep last 10 dirs under `.turingmind/reviews/`, delete older:
```bash
ls -t .turingmind/reviews/ 2>/dev/null | tail -n +11 | xargs -I {} rm -rf ".turingmind/reviews/{}"
```

## Output rules

- Always include filtered-issues summary
- Always show per-agent attribution
- Diff-style fixes only — never prose
- Never report pre-existing (orchestrator verifies in_diff)
- Mid-loop /review prints findings, NEVER writes REVIEW.md — that's --finalize's job
