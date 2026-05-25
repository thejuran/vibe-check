---
allowed-tools: Bash(git:*), Bash(gh pr diff:*), Bash(gh pr view:*), Read, Write, Grep, Glob, Task, AskUserQuestion
description: Quick code review for uncommitted local changes
---

## Finalize mode

If `$ARGUMENTS` contains `--finalize`:
- Run Phase 0 and 0.5 to resolve scope and read state. Do NOT dispatch agents.
- If no state file: error "No prior review passes. Run `/review` first."
- Compute current state:
  - `outstanding_cw` = last pass's findings with band ∈ {critical, warning} AND status ≠ fixed-since-last
  - `unacknowledged_medium` = last pass's findings with band == medium AND no entry in state's `medium_acknowledgments`
- If `outstanding_cw` non-empty:
  - Print: "Cannot finalize — {{N}} Critical/Warning findings remain:"
  - List each: `{{file}}:{{line}} — {{title}}`
  - Tell user: "Fix these, re-run `/review <phase>` to verify, then `/review <phase> --finalize`."
  - Stop. No writes.
- If `unacknowledged_medium` non-empty, enter acknowledgment loop. For each:
  - AskUserQuestion: "{{title}} at {{file}}:{{line}} — action?"
    - "Will fix" → mark for fixing (treats as outstanding, blocks)
    - "Dismiss" → follow-up AskUserQuestion for reason, mark acknowledged
    - "Look again" → display `problem` + `current_code` + `suggested_fix`, then re-ask
  - After loop:
    - Any "Will fix" → block finalize, tell user to fix and re-run.
    - All dismissed/acknowledged → write `medium_acknowledgments` to state, proceed.
- Write `.turingmind/REVIEW.md` per `templates/review-md-schema.md`.
- Archive state: `mv .turingmind/state/<id>.json .turingmind/state/<id>.json.archived-$(date +%Y-%m-%d)`.
- Print summary to user: path to `.turingmind/REVIEW.md` and reminder that it's gitignored — user must `cp` if they want it tracked.

If `--finalize` NOT in `$ARGUMENTS`: proceed with normal Phase 0 → 4.5 flow.

### Writing REVIEW.md

Use Write to create `.turingmind/REVIEW.md` per `templates/review-md-schema.md`. Fill from state:

- `{{scope_label}}`: if GSD phase mode, "Phase {{$PHASE_ID}}"; else "<repo>/<branch>"
- `{{passes}}`: length of `state.passes`
- `{{deep_count}}` / `{{quick_count}}`: count passes by `mode`
- `{{commits}}`: `git rev-list --count $baseline..HEAD`
- `{{loc}}`: sum of additions+deletions across all passes
- Coverage table: aggregate `agents_run` and `findings` across passes
- "Critical issues resolved": findings with band=critical, status=fixed-since-last across all passes. Best-effort fix-commit lookup: `git log -L <line>,<line>:<file> | head -20` to find a commit that touched that line.
- "Medium findings — dismissed": from `state.passes[-1].medium_acknowledgments` with decision=dismiss

If a prior `.turingmind/REVIEW.md` exists for a DIFFERENT phase, archive it first:
````bash
PRIOR_PHASE=$(grep -oE 'Phase [^ ]+' .turingmind/REVIEW.md | head -1 | cut -d' ' -f2)
# Defense in depth: REVIEW.md is parsed input — don't trust it. Same allowlist as Phase 0.
if [[ ! "$PRIOR_PHASE" =~ ^[A-Za-z0-9._-]+$ ]]; then
  PRIOR_PHASE="unknown"
fi
if [ -n "$PRIOR_PHASE" ] && [ "$PRIOR_PHASE" != "$PHASE_ID" ]; then
  mv .turingmind/REVIEW.md ".turingmind/REVIEW-${PRIOR_PHASE}-$(date +%Y-%m-%d).md"
fi
````

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

4. **GSD phase mode** — `$ARGUMENTS` is a phase identifier (a directory name under `.planning/phases/` like `02-code-review` or just `02`).

   **Validate first (sandbox guard).** Before any path lookup, reject `$ARGUMENTS` if it does not match `^[A-Za-z0-9._-]+$` — no slashes, no `..`, no spaces, no shell metacharacters. On reject, error: "Invalid phase id — must match `[A-Za-z0-9._-]+` (no slashes, no `..`)." and stop. This prevents `../../etc/passwd`-style escapes from the `.planning/` namespace, which would otherwise be propagated into shell commands, state file paths, and intent-doc reads.

   Then resolve:
   - If exact dir exists at `.planning/phases/<arg>/`, use it.
   - Else if a unique dir starts with `<arg>-`, use it (e.g. `02` → `02-code-review`).
   - Else error: "Phase '<arg>' not found under .planning/phases/. Available: <ls>".

   **After resolution, verify containment.** Confirm the realpath of the resolved phase dir is a descendant of the realpath of `.planning/phases/`:
   ```bash
   PHASES_ROOT=$(cd .planning/phases && pwd -P)
   PHASE_REAL=$(cd ".planning/phases/<resolved-name>" && pwd -P)
   case "$PHASE_REAL/" in
     "$PHASES_ROOT/"*) : ;;  # ok, contained
     *) echo "Phase resolution escaped .planning/phases/ — refusing."; exit 1 ;;
   esac
   ```

   Compute phase commit range:
   ```bash
   PHASE_DIR=".planning/phases/<resolved-name>"
   PHASE_START=$(git log --reverse --format=%H -- "$PHASE_DIR" | head -1)
   if [ -z "$PHASE_START" ]; then
     echo "ℹ Phase dir '$PHASE_DIR' has no commit history yet — using staged + unstaged diff only for this pass."
     # Skip the $PHASE_START..HEAD portion below; fall back to staged + unstaged only.
     PHASE_RANGE=""
   else
     PHASE_RANGE="$PHASE_START..HEAD"
   fi
   ```
   Diff = `$PHASE_RANGE` (if non-empty) + staged + unstaged.

   Set `$PHASE_ID = <resolved-name>` for state and intent context. (Validated above to be a safe slug.)

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

## Phase 1.5 — Load intent context

Only runs if `$PHASE_ID` is set (GSD phase mode from Phase 0) and triage's `intent_docs_found` includes any of `PLAN.md`, `SPEC.md`, `RESEARCH.md`.

1. Read each from `.planning/phases/$PHASE_ID/<doc>`. Cap each at 3000 chars (truncate with `[…truncated]`).

2. Assemble `<intent-context>`:
   ````
   <intent-context phase="{{$PHASE_ID}}">
     <doc name="PLAN.md">
       {{plan_text_truncated}}
     </doc>
     <doc name="SPEC.md">
       {{spec_text_truncated}}
     </doc>
   </intent-context>
   ````

3. Inject into `architecture` and `compliance` prompts ONLY (Phase 2). NOT bugs/security/language — they don't benefit; tokens aren't free.

Skip Phase 1.5 entirely if not in GSD phase mode.

This is a READ-ONLY operation. The tool NEVER writes to `.planning/`.

## Phase 2 — Dispatch agents in parallel

Single assistant turn, parallel `Task` calls:

| Always | Condition | Agent |
|--------|-----------|-------|
| ✓ | — | `bugs` |
| ✓ | — | `security` |
|  | `CLAUDE.md` or `AGENTS.md` in repo root or changed dir | `compliance` |
|  | `.ts/.tsx/.js/.jsx/.mjs/.cjs` in diff | `language-typescript` |
|  | `.py` in diff | `language-python` |
|  | any `.go` in diff | `language-go` |
|  | any `.rs` in diff | `language-rust` |
|  | triage.frameworks includes "react" | `framework-react` |

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

### Intent context injection

For `architecture` and `compliance` ONLY, prepend `<intent-context>` block (from Phase 1.5) BEFORE the `<diff>` block. Other agents: omit.

Updated prompt for architecture and compliance:

````
You are the {{agent_name}} agent. Review per your subagent instructions.

{{intent_context_block_if_present}}

<diff>
{{git_diff_output}}
</diff>

<changed-files>
{{filtered_file_list}}
</changed-files>

If `<intent-context>` present, attempt `intent_doc_match` for findings the docs cover. Be conservative with confidence.

Return ONE JSON per templates/agent-output-schema.md. JSON only.
````

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

### Multi-pass status summary (only in pass >1)

If `$PASS_NUMBER > 1`:

Count carry-forward results:
- `fixed_count` = findings with status `fixed-since-last` in this pass's carry-forward
- `persisted_count` = findings with status `persisted`
- `new_count` = brand-new findings this pass

Render before the per-band sections:

````
**Pass {{$PASS_NUMBER}}** — {{fixed_count}} fixed since last, {{persisted_count}} still present, {{new_count}} new

✅ Fixed since last pass:
- `{{file}}:{{line}}` — {{title}} (was {{band}} pass {{N}})
````

Findings marked `persisted` go into the regular per-band tables with `Status: PERSISTED (pass N)` where N is when they first appeared.

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
