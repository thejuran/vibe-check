---
allowed-tools: Bash(git:*), Bash(gh pr diff:*), Bash(gh pr view:*), Read, Write, Edit, Grep, Glob, Task, AskUserQuestion
description: Quick code review for uncommitted local changes
---

## HARD CONTRACT (read this before doing anything)

This command is an **orchestrator** — its sole job is to execute the phases below in order. The phases are NOT optional, NOT a menu, and NOT a template for inspiration. If you find yourself "skipping ahead to the report" or "improvising a summary file," STOP — that is a failure mode. Follow the prose step-by-step, in numerical phase order, top to bottom.

**Output paths — non-negotiable:**

- **WRITE only to `.turingmind/`** in the user's project. Specifically: `.turingmind/state/<id>.json` (Phase 4.5), optional `.turingmind/reviews/<timestamp>/` (Phase 4.5 snapshot), and `.turingmind/REVIEW.md` (only via Finalize mode).
- **NEVER write to `.planning/`** — that namespace belongs to GSD. The tool READS PLAN.md/SPEC.md/RESEARCH.md from there (Phase 1.5) but writes nothing.
- **NEVER write per-phase review files** like `.planning/phases/<id>/<NN>-REVIEW.md` or `<NN>-DEEP-REVIEW.md` even if you see GSD/other plugins creating files in that location. **This tool does not produce per-phase artifacts in `.planning/`.** The single authoritative artifact is `.turingmind/REVIEW.md`, written by `--finalize`.
- Mid-loop `/review` and `/deep-review` invocations **print findings to the chat transcript only**. No file write of the report itself. State file under `.turingmind/state/` is the only thing persisted by a non-finalize pass.

**Phase progression — non-negotiable:**

- Announce each phase as you enter it with one line: `✓ Phase N — <name>` (or `⊘ Phase N — <name> (skipped: <reason>)` if a skip condition fires). The user reads these announcements to verify the orchestrator is on track.
- Phase 4 (Render) MUST be followed by Phase 4.5 (Persist state). Phase 4.5 MUST be followed by Phase 5 (Interactive fix loop) UNLESS one of Phase 5's documented skip conditions applies.
- The presence of Phase 5 as the next step is non-negotiable for any stateful invocation with findings. "I already rendered the report so I'm done" is the failure mode — Phase 5 is part of the user-facing contract, not a polish step.

**If unsure, surface the uncertainty rather than improvise.** Print "I'm uncertain about <specific phase or step> — orchestrator prose is ambiguous here" and stop. That is always preferable to inventing behavior that violates the contract above.

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
  - **Route into Phase 5 Step A** with the outstanding findings as the candidate set, so the user can apply fixes (auto / selected / by hand) and then choose at Step C whether to rerun or abandon. Do NOT write REVIEW.md or archive state — finalize stays blocked until a future invocation finds `outstanding_cw` empty.
  - If Phase 5 is unavailable (e.g. `$TURINGMIND_NONINTERACTIVE` is set, or PR/range mode), fall back to the legacy behavior: tell user "Fix these, re-run with `--finalize`." and stop.
- If `unacknowledged_medium` non-empty, enter acknowledgment loop. For each:
  - AskUserQuestion: "{{title}} at {{file}}:{{line}} — action?"
    - "Will fix" → defer to Phase 5: collect all "Will fix" Medium findings, then route into Phase 5 Step A with that set as the candidates. After Phase 5's Step C, the user picks rerun (loop continues) or abandon (state preserved, no REVIEW.md).
    - "Dismiss" → follow-up AskUserQuestion for reason, write `medium_acknowledgments[stable_hash] = {decision: "dismiss", reason: "<text>", at_pass: N}` to state root.
    - "Look again" → display `problem` + `current_code` + `suggested_fix`, then re-ask.
  - After loop:
    - Any "Will fix" → routed to Phase 5 above; finalize does NOT proceed this invocation.
    - All dismissed/acknowledged → `medium_acknowledgments` written; proceed.
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

**→ Proceed immediately to Phase 4.5 (Persist pass state). Do not stop here. The report you just rendered is NOT a complete output — Phase 4.5 writes the state file, and Phase 5 drives the fix loop. Both are mandatory.**

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

**→ Proceed immediately to Phase 5 (Interactive fix loop). Do not stop here. State has been persisted; the user is still in the conversation waiting for the AskUserQuestion that Phase 5 dispatches. Skipping Phase 5 means the user has to manually invoke the command again to engage the fix workflow — that's a contract violation.**

## Phase 5 — Interactive fix loop

After Phase 4 renders the report and Phase 4.5 persists state, run an interactive loop so the user can iterate without re-typing the slash command. The loop terminates on "close out" (routes to `--finalize`) or "abandon" (stops, leaves state for later resume).

### Skip conditions

Phase 5 runs ONLY when ALL of these are true:

- `$ARGUMENTS` does NOT contain `--finalize` (finalize has its own dedicated flow above)
- At least one finding was reported in Phase 4 (no findings → nothing to fix; print "✅ No issues to fix. Re-run when you've changed code, or run with `--finalize` to ship." and stop)
- Scope mode is `default` (uncommitted) or `GSD phase mode` — stateful modes where rerun-with-carry-forward makes sense. **Skip Phase 5 entirely in PR mode and range mode** (both are stateless — print a one-liner pointing the user at `--finalize` if they want a REVIEW.md artifact, then stop)
- The `$TURINGMIND_NONINTERACTIVE` env var is NOT set to a truthy value (CI / scripted runs disable the loop; print a one-line summary instead)

If any skip condition fires, print the contextual one-liner and stop normally.

### Step A — Decide how fixes will be applied

AskUserQuestion (one question, 4 options — "auto-apply all" listed first per the user's stated workflow preference):

> **Question:** "How do you want to handle the {{reported_count}} finding(s) above?"
> **Options:**
> 1. **Apply all auto-fixable findings (Recommended)** — Tool dispatches a fix-implementer subagent that applies every finding's `suggested_fix.old/new` diff and commits each fix atomically with message `fix(review-pass-{{$PASS_NUMBER}}): {{title}}`. Findings without a complete `suggested_fix` are skipped and reported.
> 2. **Apply selected findings only** — Follow-up AskUserQuestion (multiSelect=true) lets the user pick a subset. Subagent applies only those.
> 3. **I'll apply them myself** — Tool pauses. User edits + commits in their own session/tools, then comes back to Step C.
> 4. **Skip fixes this pass** — No fixes applied. Skip directly to Step C (typical when the user wants to acknowledge-and-move-on without changes).

### Step B — Apply fixes (if Step A chose 1 or 2)

**Default: orchestrator applies fixes directly inline** (the orchestrator's `allowed-tools` includes `Edit` and `Bash(git:*)` exactly so this can happen without a Task hop).

For each selected finding, in order:

1. **Pre-flight check.** If the finding has no concrete `suggested_fix.old` or `suggested_fix.new` populated → record `no-fix-available`, skip.
2. **Drift check.** Read `finding.file`. If `suggested_fix.old` does not appear verbatim in the file (whitespace-exact substring match) → record `drifted` with the file path and the first 80 chars of `suggested_fix.old`, skip. Do NOT attempt to interpret or repair intent — the safer outcome is to surface the drift back to the user.
3. **Apply.** Use the `Edit` tool with `file_path = finding.file`, `old_string = finding.suggested_fix.old`, `new_string = finding.suggested_fix.new`. If the edit fails (multiple matches, file changed since read, etc.) → record `errored` with the error message, skip.
4. **Commit.** Run:
   ```bash
   git add "<finding.file>"
   git commit -m "fix(review-pass-<$PASS_NUMBER>): <finding.title>"
   ```
   Do NOT use `--no-verify`. If a pre-commit hook fails, fix the complaint and create a NEW commit (don't amend). Capture the resulting commit SHA for reporting.

**Fallback: dispatch a Task subagent for large batches.** If the selected set has more than 8 findings, OR if any finding's `suggested_fix.new` exceeds ~200 lines, OR if multiple findings touch the same file in interleaved ways (apply-order matters), prefer dispatching a single `general-purpose` Task call with this prompt to keep the orchestrator's context lean:

```
You are the fix-implementer for the turingmind-code-review tool, working in {{repo_root}}.

For each finding below, apply the `suggested_fix.old` → `suggested_fix.new` transformation EXACTLY using the Edit tool (whitespace-exact substring match — do not normalize). Skip with reason 'drifted' if `old` does not appear verbatim. Skip with reason 'no-fix-available' if `suggested_fix` fields are incomplete.

After each successful edit, commit atomically: `git add <file>; git commit -m "fix(review-pass-{{$PASS_NUMBER}}): <title>"`. No --no-verify. On hook failure, fix and NEW commit (no amend).

<findings>
{{JSON array of selected findings — each has id/file/line/title/suggested_fix/why_it_matters}}
</findings>

Report back as JSON:
{
  "applied":  [{"id": "<id>", "commit_sha": "<sha>"}],
  "drifted":  [{"id": "<id>", "reason": "<truncated old substring>"}],
  "no_fix":   [{"id": "<id>"}],
  "errored":  [{"id": "<id>", "error": "<message>"}]
}
```

**Render results either way.** Render the applied/drifted/no_fix/errored arrays verbatim under a `### Fixes applied` heading. For each applied entry, link the commit SHA. For each drifted/errored entry, briefly explain so the user can pick "I'll apply them myself" at the next Step A iteration if they want to address them by hand.

Append applied commit SHAs to `state.passes[-1].fixes_applied[]` so Phase 0.5 carry-forward sees them on next pass.

### Step C — Decide what to do next

Regardless of Step A's choice, end the iteration with AskUserQuestion:

> **Question:** "Pass {{$PASS_NUMBER}} loop — what's next?"
> **Options:**
> 1. **Rerun review on the new diff (Recommended if any fixes were applied)** — Re-enter the orchestrator at Phase 0 with the SAME `$ARGUMENTS` (minus any `--finalize`). State file persists; Phase 0.5 detects new commits since last pass's `head_sha`; Phase 3 carry-forward marks fixed findings as `fixed-since-last`; M7 multi-pass summary shows the diff.
> 2. **Close out and document** — Re-enter the orchestrator with `$ARGUMENTS = "${original_args} --finalize"`. The Finalize mode section at the top of this file takes over: blocks on outstanding C/W (loop returns to Step A so user can address them), AskUserQuestion loop on unacknowledged Medium, writes `.turingmind/REVIEW.md`, archives state.
> 3. **Abandon for now** — Stop. State file remains at `.turingmind/state/<id>.json` for resume. Print: "Paused. Resume with `/turingmind-code-review:{{command}} {{original_args}}` or close out later with `--finalize`."

If the user picked option 1, loop back to Phase 0 of the current command (do not re-run Phase 0.7 first-run setup since state exists). If option 2, route to Finalize mode. If option 3, stop.

### Loop termination guarantees

- Loop terminates on user choice (option 2 or 3) or on Finalize mode's natural completion (REVIEW.md written → done).
- Loop does NOT terminate just because a pass had zero new findings — the skip condition in Phase 5 step "Skip conditions" handles that case by printing the no-findings one-liner once per pass.
- Loop has no fixed iteration cap — the user controls when to stop. If a runaway scenario seems possible (e.g. fixes keep introducing new findings), tell the user at the start of pass 5+: "ℹ This is pass {{N}}. If findings keep regenerating, consider abandoning and re-scoping."

## Output rules

- Always include filtered-issues summary
- Always show per-agent attribution
- Diff-style fixes only — never prose
- Never report pre-existing (orchestrator verifies in_diff)
- Mid-loop /review prints findings, NEVER writes REVIEW.md — that's --finalize's job
- Phase 5 fix-loop runs after every non-finalize, non-stateless invocation that has at least one finding
