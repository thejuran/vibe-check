# Milestone Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal Claude Code plugin (`julian-orchestrator`) that exposes a single `/milestone:run` command sequencing existing skills (superpowers:brainstorming → /gsd:* → /codex:adversarial-review → /turingmind-code-review:deep-review → walkthrough) through a complete milestone flow, without forking any of them.

**Architecture:** A thin shell — one workflow markdown file plus a plugin manifest. The wrapper reads `.planning/ROADMAP.md` and `.planning/STATE.md` to drive a loop over incomplete phases, invokes upstream skills via Claude's `Skill()` mechanism, and pauses for user input at narrowly-defined decision points. The single exception to "wrapper writes nothing" is writing `.planning/MILESTONE-CONTEXT.md` on cold start, because that's GSD's standard input contract for `/gsd:new-milestone`.

**Tech Stack:** Markdown only. Claude Code plugin format (`.claude-plugin/plugin.json` + `commands/`). No JS, no MCP server, no Python. All control flow is Claude following prose instructions.

---

## File Structure

The deliverable is a new directory outside the current repo:

```
~/code/julian-orchestrator/
├── .claude-plugin/
│   └── plugin.json                   # Plugin manifest (~20 lines)
├── README.md                         # Install + usage notes (~80 lines)
├── commands/
│   └── milestone.md                  # The orchestrator workflow (target ≤300 lines)
└── docs/
    └── validation-scenarios.md       # The 5 manual scenarios from the spec (~120 lines)
```

**Decomposition rationale:**

- `commands/milestone.md` is one file because the orchestrator is one workflow. Splitting per-phase-step would create cross-file references that fragment Claude's reading flow.
- `docs/validation-scenarios.md` is separate so it can be edited freely without bloating the orchestrator file or counting against its ~300-line budget.
- `README.md` is for future-you (or anyone else) — install command, what `.orchestrator.json` knobs do, what to expect on cold vs warm start.
- No `tests/` directory — the spec explicitly says no automated tests on Day 1.

**Working directory for this plan's tasks:** `~/code/julian-orchestrator/` (created in Task 1). All file paths below are relative to that directory unless prefixed with `<current-repo>/` (meaning `/Users/julianamacbook/turingmind-code-review/`, where the spec lives).

---

## Task 1: Bootstrap the plugin directory and manifest

**Files:**
- Create: `~/code/julian-orchestrator/.claude-plugin/plugin.json`
- Create: `~/code/julian-orchestrator/README.md`

- [ ] **Step 1: Create the directory tree**

Run:
```bash
mkdir -p ~/code/julian-orchestrator/.claude-plugin ~/code/julian-orchestrator/commands ~/code/julian-orchestrator/docs
cd ~/code/julian-orchestrator
git init
```

Expected: `Initialized empty Git repository in /Users/julianamacbook/code/julian-orchestrator/.git/`

- [ ] **Step 2: Write the plugin manifest**

Create `~/code/julian-orchestrator/.claude-plugin/plugin.json`:

```json
{
  "name": "julian-orchestrator",
  "description": "Personal milestone orchestrator: sequences brainstorming, GSD, codex adversarial review, turingmind deep-review, and walkthrough into one /milestone:run command.",
  "version": "0.1.0",
  "author": { "name": "thejuran" },
  "license": "MIT",
  "keywords": ["orchestrator", "workflow", "gsd", "milestone", "personal"]
}
```

Note: No `mcpServers` block — this plugin is markdown-only.

- [ ] **Step 3: Write the README placeholder**

Create `~/code/julian-orchestrator/README.md`:

```markdown
# julian-orchestrator

Personal Claude Code plugin that sequences existing skills (superpowers:brainstorming, /gsd:*, /codex:adversarial-review, /turingmind-code-review:deep-review, walkthrough) into a single milestone-level command: `/milestone:run`.

## Install

This is a personal, unpublished plugin. Install locally by adding it to your Claude Code plugins config.

```bash
# Adjust the exact mechanism to match how your other local plugins are wired.
# Symlinking or referencing this directory from ~/.claude/plugins/installed_plugins.json
# is one common approach.
```

## Usage

**Cold start (no `.planning/ROADMAP.md`):**
```
/milestone:run "build a thumbnail cache for the photo app"
```
Brainstorms, seeds a new GSD milestone, then drives every phase.

**Warm start (`.planning/ROADMAP.md` exists):**
```
/milestone:run
```
Skips brainstorming and drives remaining phases.

## Configuration

Optional `.orchestrator.json` at the repo root:

```json
{
  "review_tier": "deep",
  "adversarial_max_rewrites": 2,
  "skip_walkthrough": false,
  "deploy_prep_extras": []
}
```

See `commands/milestone.md` for the full key reference.

## Design

See the design spec: `<your-repo>/docs/superpowers/specs/2026-05-25-milestone-orchestrator-design.md`.
```

- [ ] **Step 4: Initial commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add .claude-plugin/plugin.json README.md
git commit -m "init: julian-orchestrator plugin scaffold"
```

Expected: a clean commit. `git log --oneline` shows one commit.

---

## Task 2: Write the orchestrator skeleton — top matter, mode detection, config loading

**Files:**
- Create: `~/code/julian-orchestrator/commands/milestone.md`

This task produces the first ~70 lines of the orchestrator: frontmatter, hard contract preamble, mode detection (cold vs warm), and config-file loading. No phase loop yet.

- [ ] **Step 1: Write the frontmatter and orchestrator preamble**

Create `~/code/julian-orchestrator/commands/milestone.md`:

```markdown
---
allowed-tools: Read, Bash(git:*), Bash(ls:*), Bash(cat:*), Bash(mkdir:*), Write, AskUserQuestion, Skill, Task
description: Run a full milestone flow — brainstorm (if cold) → GSD phases (discuss/plan/adversarial/execute/review per phase) → deploy prep → walkthrough → complete-milestone
argument-hint: '[optional one-line idea, only used on cold start]'
---

# /milestone:run — Milestone Orchestrator

## HARD CONTRACT

This command is an **orchestrator** — its only job is to invoke other skills in order. The phases below are NOT a menu. Follow them in numerical order.

**The wrapper writes nothing of its own, with ONE exception:** on cold start, it writes `.planning/MILESTONE-CONTEXT.md` as the input contract for `/gsd:new-milestone`. That is the only file this orchestrator creates. Everything else is delegated to upstream skills.

**State of truth:**
- `.planning/STATE.md` — phase progress (GSD-owned)
- `.planning/ROADMAP.md` — phase list (GSD-owned)
- `.planning/phases/<N>/PLAN.md`, `RESEARCH.md`, `DISCUSSION.md` — per-phase artifacts (GSD-owned)
- `.turingmind/state/<phase>.json` — turingmind review state (turingmind-owned)

**If unsure at any step, surface the uncertainty rather than improvise.** Print "I'm uncertain about <step> — orchestrator prose is ambiguous here" and stop.
```

- [ ] **Step 2: Add Phase 0 — load configuration**

Append to `commands/milestone.md`:

```markdown
## Phase 0 — Load configuration

Read `.orchestrator.json` if it exists. Default values:

| Key | Default | Used in |
|---|---|---|
| `review_tier` | `"deep"` | Phase loop step 5 |
| `adversarial_max_rewrites` | `2` | Phase loop step 3 |
| `skip_walkthrough` | `false` | Milestone-end step 3 |
| `deploy_prep_extras` | `[]` | Milestone-end step 2 |

```bash
if [ -f .orchestrator.json ]; then
  CONFIG=$(cat .orchestrator.json)
else
  CONFIG='{"review_tier":"deep","adversarial_max_rewrites":2,"skip_walkthrough":false,"deploy_prep_extras":[]}'
  echo "ℹ No .orchestrator.json — using defaults. Create one if you want project-specific deploy notes."
fi
```

No schema validation. Typos in `.orchestrator.json` are silently ignored — personal tool, not worth the maintenance.

Announce: `✓ Phase 0 — config loaded`.
```

- [ ] **Step 3: Add Phase 1 — mode detection**

Append:

```markdown
## Phase 1 — Detect mode (cold vs warm start)

Check for `.planning/ROADMAP.md`:

```bash
if [ -f .planning/ROADMAP.md ]; then
  MODE="warm"
else
  MODE="cold"
fi
```

- **Warm start:** skip directly to Phase 3 (phase loop).
- **Cold start:** proceed to Phase 2 (brainstorm + seed milestone).

Announce: `✓ Phase 1 — mode: <cold|warm>`.
```

- [ ] **Step 4: Commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add commands/milestone.md
git commit -m "feat(milestone): scaffold orchestrator — frontmatter, hard contract, config + mode detection"
```

Expected: clean commit. `wc -l commands/milestone.md` reports ≤80.

---

## Task 3: Add cold-start flow — brainstorm + seed milestone

**Files:**
- Modify: `~/code/julian-orchestrator/commands/milestone.md` (append Phase 2)

- [ ] **Step 1: Append Phase 2**

Append to `commands/milestone.md`:

```markdown
## Phase 2 — Cold start: brainstorm + seed milestone

**Skip this phase entirely if `MODE == "warm"`.**

### 2a — Brainstorm

Invoke `superpowers:brainstorming` via `Skill()`. Pass the user's `$ARGUMENTS` as the one-line idea.

**Critical override in the prompt:** include this exact sentence in the args you pass to brainstorming:

> "ORCHESTRATOR OVERRIDE: After the user approves the written design spec, return control to the calling orchestrator. Do NOT invoke superpowers:writing-plans — the orchestrator will hand the spec to /gsd:new-milestone instead."

Brainstorming will explore, propose approaches, write the design spec to `docs/superpowers/specs/<date>-<topic>-design.md`, and get user approval. When it returns control, the spec file exists and the user has approved its content.

Read the spec file that brainstorming just wrote. The file path is the most recent file in `docs/superpowers/specs/` (sort by mtime):

```bash
SPEC_PATH=$(ls -t docs/superpowers/specs/*.md 2>/dev/null | head -1)
if [ -z "$SPEC_PATH" ]; then
  echo "✗ Brainstorming did not produce a spec file. Aborting."
  exit 1
fi
```

Announce: `✓ Phase 2a — brainstorm complete. Spec: $SPEC_PATH`.

### 2b — Seed milestone

GSD's `/gsd:new-milestone` reads `.planning/MILESTONE-CONTEXT.md` as its preferred input. Write the brainstorming spec there.

```bash
mkdir -p .planning
cp "$SPEC_PATH" .planning/MILESTONE-CONTEXT.md
```

This is the **only file the orchestrator writes.** It's narrowly scoped to GSD's documented input contract — not state, not progress tracking, not anything the orchestrator owns.

Invoke `/gsd:new-milestone` via `Skill()`. GSD will:
- Read `.planning/MILESTONE-CONTEXT.md`
- Run its roadmapper
- Write `PROJECT.md`, `ROADMAP.md`, and per-phase scaffolding under `.planning/phases/<N>/`

After GSD returns, verify the roadmap exists:

```bash
if [ ! -f .planning/ROADMAP.md ]; then
  echo "✗ /gsd:new-milestone did not produce ROADMAP.md. Aborting."
  exit 1
fi
```

Announce: `✓ Phase 2b — milestone seeded. ROADMAP.md ready.`

Proceed to Phase 3.
```

- [ ] **Step 2: Commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add commands/milestone.md
git commit -m "feat(milestone): add cold-start flow — brainstorm override + new-milestone seed"
```

Expected: clean commit. `wc -l commands/milestone.md` reports ≤140.

---

## Task 4: Add the phase loop — discuss + plan steps

**Files:**
- Modify: `~/code/julian-orchestrator/commands/milestone.md` (append Phase 3, partial)

This task adds the loop scaffolding and the first two per-phase sub-steps (DISCUSS and PLAN). The remaining sub-steps (ADVERSARIAL, EXECUTE, DEEP REVIEW) come in Tasks 5–7.

- [ ] **Step 1: Append Phase 3 scaffold and sub-step 1 (DISCUSS)**

Append to `commands/milestone.md`:

```markdown
## Phase 3 — Phase loop

Iterate until ROADMAP.md has no incomplete phases. **Re-read ROADMAP.md at the start of every iteration** to catch phases inserted mid-flight by discuss-phase or other GSD actions.

### Loop iteration

For each iteration:

1. **Re-read ROADMAP.md.** Parse it to find the next incomplete phase. GSD marks phases complete via STATE.md and ROADMAP.md conventions — use:

```bash
# Find the lowest-numbered incomplete phase
NEXT_PHASE=$(grep -E '^\| Phase ' .planning/ROADMAP.md | grep -v '✓\|completed\|done' | head -1 | awk -F'|' '{print $2}' | tr -d ' Phase')
```

The exact parsing depends on GSD's ROADMAP.md format. If parsing fails or returns ambiguous output, use AskUserQuestion: "Could not determine next incomplete phase from ROADMAP.md. Which phase should I run next? <list incomplete phases from the file>". Do NOT guess.

If no incomplete phases remain, exit the loop and proceed to Phase 4 (milestone-end).

Announce: `▶ Phase loop — running phase $NEXT_PHASE`.

### Sub-step 1: DISCUSS

Invoke `/gsd:discuss-phase $NEXT_PHASE` via `Skill()`.

GSD's discuss-phase may pause for user input on gray-area decisions. **Let it.** The wrapper does not wrap GSD's prompts.

After it returns, verify `DISCUSSION.md` exists for the phase:

```bash
PHASE_DIR=$(ls -d .planning/phases/${NEXT_PHASE}* 2>/dev/null | head -1)
if [ -z "$PHASE_DIR" ] || [ ! -f "$PHASE_DIR/DISCUSSION.md" ]; then
  echo "✗ /gsd:discuss-phase did not produce DISCUSSION.md for phase $NEXT_PHASE. Aborting."
  exit 1
fi
```

Announce: `  ✓ DISCUSS — $PHASE_DIR/DISCUSSION.md`.
```

- [ ] **Step 2: Append sub-step 2 (PLAN)**

Append to `commands/milestone.md`:

```markdown
### Sub-step 2: PLAN

Invoke `/gsd:plan-phase $NEXT_PHASE` via `Skill()`.

`/gsd:plan-phase` internally runs researcher → planner → plan-checker. It produces both `RESEARCH.md` and `PLAN.md`. **Do not call `/gsd:research-phase` separately** — research is already inside plan.

After it returns, verify both files exist:

```bash
if [ ! -f "$PHASE_DIR/PLAN.md" ] || [ ! -f "$PHASE_DIR/RESEARCH.md" ]; then
  echo "✗ /gsd:plan-phase did not produce PLAN.md and RESEARCH.md for phase $NEXT_PHASE."
  echo "  PHASE_DIR=$PHASE_DIR"
  exit 1
fi
```

Announce: `  ✓ PLAN — $PHASE_DIR/PLAN.md`.
```

- [ ] **Step 3: Commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add commands/milestone.md
git commit -m "feat(milestone): phase loop scaffold + DISCUSS and PLAN sub-steps"
```

Expected: clean commit. `wc -l commands/milestone.md` reports ≤200.

---

## Task 5: Add the adversarial sub-step with rewrite cycle

**Files:**
- Modify: `~/code/julian-orchestrator/commands/milestone.md` (append sub-step 3)

This task adds the codex adversarial review and its rewrite-up-to-twice cycle, with the user pause if criticals remain after 2 rewrites.

- [ ] **Step 1: Append sub-step 3 (ADVERSARIAL)**

Append to `commands/milestone.md`:

```markdown
### Sub-step 3: ADVERSARIAL

Run codex adversarial review against the plan. Read `adversarial_max_rewrites` from CONFIG (default 2).

Initialize:
```bash
REWRITE_COUNT=0
MAX_REWRITES=$(echo "$CONFIG" | grep -o '"adversarial_max_rewrites":[0-9]*' | cut -d: -f2)
MAX_REWRITES=${MAX_REWRITES:-2}
```

**Inner adversarial loop:**

Invoke `/codex:adversarial-review` via `Skill()`. Pass a focus argument that points codex at the phase's PLAN.md plus its supporting context:

> "--wait --scope working-tree challenge the implementation plan at $PHASE_DIR/PLAN.md against the research findings at $PHASE_DIR/RESEARCH.md and the discussion notes at $PHASE_DIR/DISCUSSION.md. Focus on: assumptions the plan depends on, where the design could fail under real-world conditions, and any research findings the plan ignored."

Codex returns its review verbatim. **Parse the output for severity terms using codex's vocabulary** (`critical`, `blocker`). If neither appears, the plan passes — proceed to EXECUTE.

If `critical` or `blocker` findings are present:

```
if [ $REWRITE_COUNT -ge $MAX_REWRITES ]; then
  # Pause for user — see "user pause" block below
else
  REWRITE_COUNT=$((REWRITE_COUNT + 1))
  # Re-run /gsd:plan-phase with the critique embedded in the args
  # Then loop back to re-run /codex:adversarial-review
fi
```

**Rewrite mechanism:** invoke `/gsd:plan-phase $NEXT_PHASE` again via `Skill()`, passing the codex critique as additional context:

> "Rewrite the existing plan at $PHASE_DIR/PLAN.md to address the following adversarial findings from codex: <paste codex's critical/blocker findings verbatim>"

After GSD's plan-phase returns, loop back to the top of this sub-step and re-run `/codex:adversarial-review`.

**User pause (cap hit):** when `REWRITE_COUNT >= MAX_REWRITES` and criticals remain, use `AskUserQuestion`:

> Question: "Codex still flags critical issues after $MAX_REWRITES rewrites of phase $NEXT_PHASE. What now?"
> Options:
>   1. "Accept plan as-is" — proceed to EXECUTE with current PLAN.md
>   2. "Edit by hand" — pause; user edits PLAN.md manually, then types "ready" to continue
>   3. "Try one more rewrite" — increment cap by 1 and run another rewrite cycle

Honor `$ORCHESTRATOR_NONINTERACTIVE` if set: skip the question, print the critique to stdout, exit with code 1.

**Severity vocabulary note:** the wrapper interprets codex's output using codex's own terms. Do not translate to turingmind's vocabulary (warning/medium) here — that's used in sub-step 5.

Announce on pass: `  ✓ ADVERSARIAL — clean (or report-only findings)`.
Announce on rewrite: `  ↻ ADVERSARIAL — rewrite $REWRITE_COUNT/$MAX_REWRITES triggered`.
```

- [ ] **Step 2: Commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add commands/milestone.md
git commit -m "feat(milestone): ADVERSARIAL sub-step with rewrite cycle (cap=2)"
```

Expected: clean commit. `wc -l commands/milestone.md` reports ≤260.

---

## Task 6: Add the execute and deep-review sub-steps

**Files:**
- Modify: `~/code/julian-orchestrator/commands/milestone.md` (append sub-steps 4 and 5)

- [ ] **Step 1: Append sub-step 4 (EXECUTE)**

Append to `commands/milestone.md`:

```markdown
### Sub-step 4: EXECUTE

Invoke `/gsd:execute-phase $NEXT_PHASE` via `Skill()`.

GSD's executor handles atomic commits, deviation handling, and its own checkpoint protocol. **The wrapper does nothing here except invoke and wait.** If execute-phase fails partway, GSD's checkpoint mechanism preserves state — re-running `/milestone:run` later will pick up exactly where GSD left off.

Capture the phase's commit range for use in sub-step 5:

```bash
# After execute-phase returns, the phase has new commits.
# Turingmind's GSD phase mode handles range resolution itself given the phase ID —
# we just pass $NEXT_PHASE through.
PHASE_HEAD=$(git rev-parse HEAD)
```

Announce: `  ✓ EXECUTE — phase commits landed (HEAD: $PHASE_HEAD)`.
```

- [ ] **Step 2: Append sub-step 5 (DEEP REVIEW)**

Append:

```markdown
### Sub-step 5: DEEP REVIEW

Invoke `/turingmind-code-review:deep-review $NEXT_PHASE` via `Skill()`. Turingmind's GSD phase mode resolves the phase directory and scopes the review to that phase's commit range automatically (see `<turingmind>/plugins/turingmind/commands/review.md` Phase 0, GSD phase mode).

**Severity gate (turingmind vocabulary: critical/warning vs medium/low):**

Turingmind's Phase 4 renders the report and Phase 4.5 persists state. Turingmind's Phase 5 then runs its **interactive fix loop** automatically. Within that loop:

- If the user (or auto-apply default) successfully fixes all critical/warning findings → turingmind commits the fixes atomically. Re-run `/turingmind-code-review:deep-review $NEXT_PHASE` to verify the second pass is clean.
- If turingmind reports drifted or no-fix-available findings → it pauses inside its own Step C with three options. The orchestrator does not need to inject its own prompt — turingmind already handles this.

The orchestrator's responsibility is to **wait for turingmind's loop to terminate** and then check the outcome. Read the most recent state file under `.turingmind/state/`:

```bash
STATE_FILE=".turingmind/state/${PHASE_DIR##*/}.json"
if [ ! -f "$STATE_FILE" ]; then
  echo "✗ Turingmind did not produce state file at $STATE_FILE."
  exit 1
fi
```

Parse the latest pass from the state file. If any `band: critical` or `band: warning` findings remain with status != `fixed-since-last` and no acknowledgment, this is a blocking condition. Use AskUserQuestion:

> Question: "{{N}} critical/warning findings remain unfixed for phase $NEXT_PHASE after turingmind's fix loop. What now?"
> Options:
>   1. "Re-review (I just fixed them by hand)" — loop back to re-invoke /turingmind-code-review:deep-review
>   2. "Skip these findings and advance to the next phase" — accept and continue
>   3. "Stop" — exit /milestone:run; resume later

Honor `$ORCHESTRATOR_NONINTERACTIVE` if set: skip the question, print the findings, exit with code 1.

When the gate passes (no unfixed critical/warning findings), announce: `  ✓ DEEP REVIEW — clean. Phase $NEXT_PHASE complete.`

Loop back to the top of Phase 3.
```

- [ ] **Step 3: Commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add commands/milestone.md
git commit -m "feat(milestone): EXECUTE and DEEP REVIEW sub-steps + per-phase quality gate"
```

Expected: clean commit. `wc -l commands/milestone.md` reports ≤340. **If this is over 300, that's the signal to consider trimming repetitive prose now**, not later.

---

## Task 7: Add the milestone-end flow

**Files:**
- Modify: `~/code/julian-orchestrator/commands/milestone.md` (append Phase 4)

- [ ] **Step 1: Append Phase 4 — milestone-end**

Append to `commands/milestone.md`:

```markdown
## Phase 4 — Milestone-end

Reached when the phase loop exits because no incomplete phases remain.

### 4a — Finalize turingmind review

Invoke `/turingmind-code-review:deep-review --finalize` via `Skill()`. This writes `.turingmind/REVIEW.md` (the milestone artifact) and runs turingmind's medium-acknowledgment loop for any unacknowledged medium findings.

After it returns:
```bash
if [ ! -f .turingmind/REVIEW.md ]; then
  echo "⚠ Turingmind --finalize did not produce .turingmind/REVIEW.md."
  echo "  This may mean unfinalized C/W findings remain. Check turingmind output above."
  # Do not auto-abort — turingmind's --finalize has its own gate.
fi
```

Announce: `✓ Phase 4a — turingmind finalized.`

### 4b — Deploy prep & pause

If `skip_walkthrough` from CONFIG is `true`, skip directly to 4e (complete milestone).

Otherwise, build and print the deploy prep summary. Gather:

```bash
BRANCH=$(git branch --show-current)
HEAD_SHA=$(git rev-parse --short HEAD)
COMMITS_AHEAD=$(git rev-list --count main..HEAD 2>/dev/null || echo "?")
BUILD_CMD=$(grep -oE '"build"\s*:\s*"[^"]+"' package.json 2>/dev/null | head -1 || echo "(not detected)")
MIGRATIONS_NEW=$(git diff --name-only main..HEAD 2>/dev/null | grep -cE '(migrations?/|db/migrate)' || echo 0)
ENV_VARS_NEW=$(git diff main..HEAD -- '*.env.example' '.env*' 2>/dev/null | grep -cE '^\+[A-Z_]+=' || echo 0)
FILES_CHANGED=$(git diff --name-only main..HEAD 2>/dev/null | wc -l | tr -d ' ')
```

Print the summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DEPLOY PREP — milestone ready to ship
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Branch:       <BRANCH>  (<COMMITS_AHEAD> commits ahead of main)
 Last SHA:     <HEAD_SHA>
 Build cmd:    <BUILD_CMD>
 Files changed: <FILES_CHANGED>
 Migrations:   <MIGRATIONS_NEW>  <if >0, append "⚠">
 New env vars: <ENV_VARS_NEW>    <if >0, append "⚠">

 Project-specific:
   <for each item in deploy_prep_extras: "   • <item>">
   <if empty: "   (none — add via .orchestrator.json's deploy_prep_extras)">
```

Then pause with `AskUserQuestion`:

> Question: "Deploy this build to your NAS, then paste the URL it's accessible at (or 'skip' to skip walkthrough)."
> Options:
>   1. (Open input — user types the URL or "skip")

Honor `$ORCHESTRATOR_NONINTERACTIVE`: stop here after printing the prep summary, exit with code 0.

If user types "skip", proceed to 4e. Otherwise, save the URL as `DEPLOY_URL` and proceed to 4c.

### 4c — Walkthrough

Invoke the `walkthrough` skill via `Skill()`, passing `DEPLOY_URL` and a brief description ("walk through the just-completed milestone on the deployed build at $DEPLOY_URL — exercise the golden paths and any new flows from this milestone").

Walkthrough drives its own fix-cycle:
- Finds bug → fixes locally → commits → asks "redeploy done?"
- The orchestrator's role here is only to let walkthrough run. The user's "redeploy done?" answers go to walkthrough directly.

When walkthrough returns, capture whether commits were made during the walkthrough:

```bash
COMMITS_BEFORE_WALKTHROUGH="<HEAD_SHA captured at start of 4b>"
COMMITS_AFTER_WALKTHROUGH=$(git rev-parse --short HEAD)
WALKTHROUGH_COMMITTED=0
if [ "$COMMITS_BEFORE_WALKTHROUGH" != "$COMMITS_AFTER_WALKTHROUGH" ]; then
  WALKTHROUGH_COMMITTED=1
fi
```

Announce: `✓ Phase 4c — walkthrough complete. Fixes committed: <yes|no>.`

### 4d — Post-walkthrough deep review (conditional)

**Only runs if `WALKTHROUGH_COMMITTED == 1`.**

If walkthrough produced any commits, those commits bypassed the per-phase deep-review gate. Run one final review against just those commits.

Invoke `/turingmind-code-review:deep-review` via `Skill()` with a range argument like `$COMMITS_BEFORE_WALKTHROUGH..HEAD`. Apply the same critical/warning blocking gate as sub-step 5: turingmind's Phase 5 fix loop will run inline; only proceed past this step when no unfixed critical/warning findings remain.

If clean, announce: `✓ Phase 4d — post-walkthrough review clean.`

### 4e — Complete milestone

Invoke `/gsd:complete-milestone` via `Skill()`. GSD archives the milestone and updates project state.

Print final summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 MILESTONE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Phases completed: <count from ROADMAP.md>
 Adversarial rewrites total: <sum across phases>
 Deep-review passes total: <sum across phases>
 Walkthrough fixes: <yes|no>
 Final commit: <git rev-parse --short HEAD>
 Review artifact: .turingmind/REVIEW.md
```

Done.
```

- [ ] **Step 2: Commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add commands/milestone.md
git commit -m "feat(milestone): milestone-end flow — finalize, deploy prep, walkthrough, post-review, complete"
```

Expected: clean commit. `wc -l commands/milestone.md` final count reports a number. **Record this number** — if it exceeds ~300, the next task starts with a trim pass before declaring done.

---

## Task 8: Write the validation-scenarios doc

**Files:**
- Create: `~/code/julian-orchestrator/docs/validation-scenarios.md`

This file is the Day-1 quality gate from the spec, made runnable. It lives outside the orchestrator file so the orchestrator stays focused on prose Claude follows, not on documentation Claude reads.

- [ ] **Step 1: Write the validation scenarios**

Create `~/code/julian-orchestrator/docs/validation-scenarios.md`:

```markdown
# Validation Scenarios

Manual scenarios to run before declaring the orchestrator "done enough to use." Run them on a throwaway project, not your real work.

## Scenario 1: Warm start, happy path, single phase

**Setup:**
- Project with `.planning/ROADMAP.md` containing one trivial phase (e.g., "add a CHANGELOG.md")
- `.orchestrator.json` exists with `"skip_walkthrough": true`

**Run:** `/milestone:run`

**Expect:** discuss → plan → adversarial (clean) → execute → deep-review (clean) → finalize → deploy prep prints → walkthrough skipped → complete-milestone

**Check:**
- Each step invoked the right skill (visible in output)
- No file writes outside `.planning/` and `.turingmind/` (verify: `git status`)
- The wrapper wrote only `.planning/MILESTONE-CONTEXT.md` if it was a cold start; on warm start it wrote nothing
- Final state: `.planning/ROADMAP.md` shows phase complete; `.turingmind/REVIEW.md` exists

## Scenario 2: Adversarial rewrite cycle

**Setup:** A phase whose plan will plausibly draw a critical adversarial finding (e.g., a phase that touches auth but omits input validation in its plan).

**Run:** `/milestone:run`

**Expect:** adversarial flags critical → rewrite #1 → still critical → rewrite #2 → still critical → pause with 3-option AskUserQuestion.

**Check:**
- Rewrite cap fires at 2 rewrites
- Pause prompt matches the spec's "User Interaction Points" table
- Picking "Try one more rewrite" actually does one more rewrite (cap incremented)
- Picking "Accept plan as-is" proceeds to EXECUTE
- Picking "Edit by hand" pauses cleanly; resuming after the user types "ready" continues to EXECUTE

## Scenario 3: Deep-review drift

**Setup:**
- Phase produces code turingmind will flag (e.g., a SQL injection pattern)
- Before running deep-review, manually edit the offending file to misalign with what turingmind's `suggested_fix.old` will look for (add a comment line above the offending line, change indentation)

**Run:** `/milestone:run` (or trigger just the review step)

**Expect:** deep-review reports drifted findings; turingmind's Phase 5 surfaces them; the wrapper waits for turingmind's loop to terminate; the wrapper then pauses with the "address them, then..." question.

**Check:**
- Drift is correctly detected as unfixable (turingmind's own logic)
- Orchestrator did NOT force-apply any fix
- Picking "I've fixed them, re-review" loops back into `/turingmind-code-review:deep-review`

## Scenario 4: Cold start end-to-end

**Setup:** Empty repo, no `.planning/`, fresh git init.

**Run:** `/milestone:run "tiny CLI tool that prints uptime"`

**Expect:** brainstorm runs → design spec written under `docs/superpowers/specs/` → user approves → orchestrator writes `.planning/MILESTONE-CONTEXT.md` → `/gsd:new-milestone` invoked → phase loop runs to completion → milestone-end runs.

**Check:**
- Brainstorming did NOT invoke `superpowers:writing-plans` (the override worked)
- `.planning/MILESTONE-CONTEXT.md` was created with the design spec's content
- The loop drove the milestone to "complete" status

## Scenario 5: Resume from interruption

**Setup:** Run Scenario 1 partway. Kill the process mid-execute (e.g., Ctrl+C during `/gsd:execute-phase`).

**Run:** `/milestone:run` again.

**Expect:** wrapper detects mode=warm, reads `.planning/STATE.md`, identifies the in-progress phase, re-enters the loop at the right sub-step (likely re-runs execute via GSD's checkpoint).

**Check:**
- No duplicate commits
- No skipped phases
- No state corruption
- Walking through the loop a second time produces the same final outcome as if uninterrupted

## Day-1 quality gate

The orchestrator is "done enough to use" when:
- Scenarios 1, 4, and 5 pass cleanly on a throwaway project
- The orchestrator works against an existing real project with prior GSD state (picks up next phase from real `STATE.md` without breaking anything)
- Deploy prep summary contains information the user actually wants for their NAS deploys — if not, signal to add `deploy_prep_extras`

Scenarios 2 and 3 are nice-to-have for confidence but not blockers — discovered organically during real use.
```

- [ ] **Step 2: Commit**

Run:
```bash
cd ~/code/julian-orchestrator
git add docs/validation-scenarios.md
git commit -m "docs: validation scenarios (Day-1 quality gate)"
```

Expected: clean commit.

---

## Task 9: Install the plugin locally and verify it loads

**Files:**
- Modify: `~/.claude/plugins/installed_plugins.json` (or your installation mechanism's equivalent)

This task makes the plugin actually invocable from Claude Code. The exact mechanism depends on how your machine's Claude Code is configured — these steps describe the most common path; adjust if your setup differs.

- [ ] **Step 1: Inspect current plugin install config**

Run:
```bash
cat ~/.claude/plugins/installed_plugins.json 2>/dev/null | head -40
ls ~/.claude/plugins/
```

Expected: you see the existing plugin install config and existing plugin directories.

- [ ] **Step 2: Register the local plugin**

Two common patterns — pick the one matching your existing setup:

**Pattern A: Symlink into the plugins cache.**
```bash
ln -s ~/code/julian-orchestrator ~/.claude/plugins/cache/julian-orchestrator
```

**Pattern B: Add to `installed_plugins.json`.**
Edit `~/.claude/plugins/installed_plugins.json` to add an entry referencing `~/code/julian-orchestrator`. Use the same shape as an existing local entry.

If neither pattern fits your machine's config, follow whatever pattern your other local-development plugins (e.g., the turingmind plugin at `<repo>/plugins/turingmind`) use.

- [ ] **Step 3: Restart Claude Code (or reload plugins)**

Whatever mechanism your Claude Code instance uses to pick up new plugins — usually a restart of the CLI/editor. Confirm the command is available by checking the user-invocable skills list (it should show `julian-orchestrator:milestone:run` or similar, depending on your install).

- [ ] **Step 4: Smoke test — print-only invocation**

In a throwaway directory (NOT `~/code/julian-orchestrator/` itself, NOT `<repo>/turingmind-code-review/`):

```bash
mkdir -p /tmp/orchestrator-smoke && cd /tmp/orchestrator-smoke
git init
# Don't run /milestone:run yet — just verify the command is registered.
```

Then in Claude Code, type `/milestone:` and confirm tab-completion or the menu shows the command. **Do not invoke it yet** — Task 10 is the first real run.

- [ ] **Step 5: Commit (if any wiring files changed)**

If you edited `~/.claude/plugins/installed_plugins.json` or similar, commit changes to wherever those are tracked (often nowhere, since they're machine-local). If purely symlink-based, no commit needed.

---

## Task 10: Day-1 validation — run Scenario 1

**Files:**
- Throwaway project: `/tmp/orchestrator-test-s1/`

This is the first real end-to-end run.

- [ ] **Step 1: Set up the throwaway project**

```bash
rm -rf /tmp/orchestrator-test-s1
mkdir -p /tmp/orchestrator-test-s1 && cd /tmp/orchestrator-test-s1
git init
git commit --allow-empty -m "init"
```

Manually create a minimal GSD state. The cleanest way: invoke `/gsd:new-project "scratch project for orchestrator test"` first to bootstrap, then `/gsd:new-milestone "add a CHANGELOG"` to get a trivial single-phase milestone. (Yes, this means running GSD twice manually before the orchestrator — it's a controlled setup, not a flaw in the orchestrator.)

Verify state:
```bash
ls .planning/
cat .planning/ROADMAP.md
```

Expected: a `ROADMAP.md` exists with one incomplete phase.

Create config to skip walkthrough:
```bash
cat > .orchestrator.json <<'EOF'
{
  "review_tier": "deep",
  "adversarial_max_rewrites": 2,
  "skip_walkthrough": true,
  "deploy_prep_extras": []
}
EOF
```

- [ ] **Step 2: Run the orchestrator**

In Claude Code, in `/tmp/orchestrator-test-s1`:

```
/milestone:run
```

- [ ] **Step 3: Observe and check**

Watch the output. The expected sequence:

```
✓ Phase 0 — config loaded
✓ Phase 1 — mode: warm
▶ Phase loop — running phase 1
  ✓ DISCUSS — .planning/phases/1-add-changelog/DISCUSSION.md
  ✓ PLAN — .planning/phases/1-add-changelog/PLAN.md
  ✓ ADVERSARIAL — clean (or report-only findings)
  ✓ EXECUTE — phase commits landed (HEAD: <sha>)
  ✓ DEEP REVIEW — clean. Phase 1 complete.
✓ Phase 4a — turingmind finalized.
[deploy prep prints]
[walkthrough skipped]
[complete-milestone]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 MILESTONE COMPLETE
...
```

**Pass conditions:**
- The orchestrator drove all five sub-steps for the phase without manual intervention beyond GSD's own pauses
- `.turingmind/REVIEW.md` exists at the end
- `git status` shows no orchestrator-authored writes outside `.planning/` and `.turingmind/` (and the CHANGELOG the phase was supposed to add)
- `wc -l ~/code/julian-orchestrator/commands/milestone.md` ≤ 300 (if not, schedule a trim pass — but do not block on it)

**If anything fails:** the orchestrator's prose was ambiguous somewhere. Read the output for "I'm uncertain about <step>" lines. Adjust the orchestrator file's prose at that step, commit, and re-run.

- [ ] **Step 4: Mark Scenario 1 as passing**

Update `~/code/julian-orchestrator/docs/validation-scenarios.md` — add at the bottom of Scenario 1:

```markdown
**Last passed:** YYYY-MM-DD (replace with actual date)
```

Run:
```bash
cd ~/code/julian-orchestrator
git add docs/validation-scenarios.md
git commit -m "validation: Scenario 1 (warm-start happy path) passing"
```

---

## Task 11: Day-1 validation — run Scenario 5 (resume)

**Files:**
- Throwaway project: `/tmp/orchestrator-test-s5/`

- [ ] **Step 1: Set up**

```bash
rm -rf /tmp/orchestrator-test-s5
mkdir -p /tmp/orchestrator-test-s5 && cd /tmp/orchestrator-test-s5
# Same setup as Scenario 1.
git init
git commit --allow-empty -m "init"
# Bootstrap GSD as in Task 10 Step 1.
# Add .orchestrator.json with skip_walkthrough=true.
```

- [ ] **Step 2: Run /milestone:run and interrupt mid-execute**

In Claude Code:
```
/milestone:run
```

When you see `  ✓ PLAN — ...` and the orchestrator is about to invoke `/gsd:execute-phase`, interrupt the session (Ctrl+C or close the conversation).

- [ ] **Step 3: Inspect state**

```bash
cat .planning/STATE.md
ls .planning/phases/*/
git log --oneline
```

Note: there's likely partial state — GSD's checkpoint may have committed something, or nothing, depending on where exactly you killed it.

- [ ] **Step 4: Re-run /milestone:run**

In a fresh Claude Code session in the same directory:
```
/milestone:run
```

- [ ] **Step 5: Observe and check**

**Pass conditions:**
- Wrapper detects mode=warm (ROADMAP.md exists)
- The loop identifies the same phase as still incomplete
- It re-enters at sub-step DISCUSS or PLAN or EXECUTE — wherever GSD's STATE.md says the phase is
- No duplicate commits (verify: `git log --oneline` doesn't show two commits for the same phase work)
- Final outcome matches Scenario 1's: milestone complete, REVIEW.md exists

- [ ] **Step 6: Mark Scenario 5 as passing**

```bash
cd ~/code/julian-orchestrator
# Update validation-scenarios.md with "Last passed: <date>" under Scenario 5
git add docs/validation-scenarios.md
git commit -m "validation: Scenario 5 (resume from interruption) passing"
```

---

## Task 12: Day-1 validation — run Scenario 4 (cold start end-to-end)

**Files:**
- Throwaway project: `/tmp/orchestrator-test-s4/`

This is the most expensive scenario — it runs brainstorming, GSD new-milestone, and at least one full phase loop. Budget 20–40 minutes of wall-clock plus Claude API cost.

- [ ] **Step 1: Set up empty repo**

```bash
rm -rf /tmp/orchestrator-test-s4
mkdir -p /tmp/orchestrator-test-s4 && cd /tmp/orchestrator-test-s4
git init
git commit --allow-empty -m "init"

# Skip walkthrough to keep the test bounded
cat > .orchestrator.json <<'EOF'
{
  "review_tier": "deep",
  "adversarial_max_rewrites": 2,
  "skip_walkthrough": true,
  "deploy_prep_extras": []
}
EOF
```

- [ ] **Step 2: Run with a tiny idea**

In Claude Code:
```
/milestone:run "tiny CLI tool that prints uptime in human-readable format"
```

- [ ] **Step 3: Walk through brainstorming**

Brainstorming will ask clarifying questions. Answer them quickly. Approve the design spec when prompted.

- [ ] **Step 4: Observe and check the override**

**Critical check:** when brainstorming finishes (after spec approval), it should hand control back to the orchestrator — NOT invoke `superpowers:writing-plans`. The override sentence in Task 3 is what enforces this.

If you see writing-plans being invoked, the override didn't work. Stop the run, adjust the override sentence in `commands/milestone.md` Phase 2a, commit, and restart from Step 2 (in a fresh `/tmp/orchestrator-test-s4-v2/` directory).

- [ ] **Step 5: Observe seed and loop**

After the override holds, expected output:

```
✓ Phase 2a — brainstorm complete. Spec: docs/superpowers/specs/<date>-<topic>-design.md
✓ Phase 2b — milestone seeded. ROADMAP.md ready.
▶ Phase loop — running phase 1
  [sub-steps...]
[milestone-end]
```

**Pass conditions:**
- `.planning/MILESTONE-CONTEXT.md` exists and contains the brainstorming spec's content
- `.planning/ROADMAP.md` was generated by GSD (not by the orchestrator)
- At least one phase ran end-to-end through the loop
- Final state: milestone complete

- [ ] **Step 6: Mark Scenario 4 as passing**

```bash
cd ~/code/julian-orchestrator
# Update validation-scenarios.md
git add docs/validation-scenarios.md
git commit -m "validation: Scenario 4 (cold-start end-to-end) passing"
```

---

## Task 13: Polish — line-count check and trim pass

**Files:**
- Modify: `~/code/julian-orchestrator/commands/milestone.md` (only if over 300 lines)

- [ ] **Step 1: Check final line count**

Run:
```bash
wc -l ~/code/julian-orchestrator/commands/milestone.md
```

If the count is ≤300, skip to Step 3.

- [ ] **Step 2: Trim if over 300 lines**

If over 300, the spec's success criterion 3 ("under ~300 lines") is breached. Trim by:

- Merging adjacent code blocks where the prose between them is redundant
- Removing announce lines that are obvious from context
- Consolidating "Honor `$ORCHESTRATOR_NONINTERACTIVE`" notes into a single Phase 0 rule rather than repeating per step
- Cutting any prose that says what Claude is about to do *and* what just happened — keep one

Do NOT cut behavioral rules, severity gates, or the verification checks. Those are load-bearing.

Re-run `wc -l`. If still over 300, accept it but flag in the commit message.

- [ ] **Step 3: Commit**

```bash
cd ~/code/julian-orchestrator
git add commands/milestone.md  # only if trimmed
LINE_COUNT=$(wc -l < commands/milestone.md)
git commit -m "chore: orchestrator at $LINE_COUNT lines (target: ≤300)" --allow-empty
```

The `--allow-empty` is for the case where no trimming was needed but you still want a final-state commit marking Day-1 done.

---

## Task 14: Update the design spec's status and link to the plan

**Files:**
- Modify: `<current-repo>/docs/superpowers/specs/2026-05-25-milestone-orchestrator-design.md`

This is a tiny housekeeping task to close the loop with the spec document.

- [ ] **Step 1: Update spec status**

In `<current-repo>/docs/superpowers/specs/2026-05-25-milestone-orchestrator-design.md`, change the Status line near the top:

From:
```markdown
**Status:** Approved, ready for implementation plan
```

To:
```markdown
**Status:** Implemented (Day-1). See docs/superpowers/plans/2026-05-25-milestone-orchestrator.md and ~/code/julian-orchestrator/.
```

- [ ] **Step 2: Commit**

```bash
cd <current-repo>
git add docs/superpowers/specs/2026-05-25-milestone-orchestrator-design.md
git commit -m "docs: mark milestone-orchestrator spec implemented"
```

---

## Self-Review

### Spec coverage check

Walked through each section of the spec and mapped to tasks:

| Spec section | Task(s) |
|---|---|
| Problem / Constraints / Approach | Task 1 (manifest), Task 2 (preamble) |
| Architecture: Plugin shape | Task 1 |
| Architecture: Command | Task 2 (frontmatter) |
| Architecture: Composition principle | Task 2 (preamble), Task 9 (state file checks) |
| Phase Loop: 1. DISCUSS | Task 4 |
| Phase Loop: 2. PLAN | Task 4 |
| Phase Loop: 3. ADVERSARIAL + rewrites | Task 5 |
| Phase Loop: 4. EXECUTE | Task 6 |
| Phase Loop: 5. DEEP REVIEW + gate | Task 6 |
| Re-read ROADMAP every iteration | Task 4 |
| Adversarial rewrite cap = 2 | Task 5 |
| Severity vocabulary note | Task 5 (codex) + Task 6 (turingmind) |
| Wrapper does NOT invoke --finalize mid-loop | Task 6 (implicit — only invoked in Task 7) |
| Failure modes table | Tasks 4–7 each handle their relevant row |
| Entry: Cold-start | Task 3 |
| Entry: Warm-start | Task 2 (mode detection) |
| Milestone-end: 1. Finalize | Task 7 |
| Milestone-end: 2. Deploy prep | Task 7 |
| Milestone-end: 3. Walkthrough | Task 7 |
| Milestone-end: 4. Post-walkthrough review | Task 7 |
| Milestone-end: 5. Complete | Task 7 |
| Configuration table | Task 2 (loading) |
| User Interaction Points table | Tasks 5, 6, 7 (each pause is in the right task) |
| Non-Interactive Mode | Tasks 5, 6, 7 (each honored locally) |
| Validation Scenarios 1, 4, 5 | Tasks 10, 12, 11 |
| Validation Scenarios 2, 3 (nice-to-have) | Documented in Task 8's doc; not run on Day 1 |
| Day-1 quality gate | Tasks 10, 11, 12 |
| Success Definition: cold-start produces milestone | Task 12 |
| Success Definition: warm-start completes one phase | Task 10 |
| Success Definition: under ~300 lines | Task 13 |

No spec sections without a task. ✓

### Placeholder scan

- No "TBD", "TODO", "implement later", "fill in details", "add appropriate error handling", "similar to Task N" — checked.
- Every step that describes code shows the code.
- Every step that describes a command shows the command and expected output.

✓

### Type/identifier consistency

- `NEXT_PHASE`, `PHASE_DIR`, `STATE_FILE`, `CONFIG`, `MAX_REWRITES`, `REWRITE_COUNT` used consistently across tasks.
- `$ORCHESTRATOR_NONINTERACTIVE` (with `$`) used consistently for the env-var reference.
- `/gsd:discuss-phase`, `/gsd:plan-phase`, `/gsd:execute-phase`, `/gsd:complete-milestone`, `/gsd:new-milestone`, `/codex:adversarial-review`, `/turingmind-code-review:deep-review`, `walkthrough` — exact upstream skill names used consistently (verified against `~/.claude/plugins/cache/` and the user-invocable skills list).
- `.orchestrator.json`, `.planning/`, `.turingmind/` paths consistent.

✓

### Notes worth surfacing during execution

1. **GSD ROADMAP.md parse format is GSD-version-dependent.** Task 4's grep command makes a best-effort parse but is the most likely place for upstream-format drift to bite. If it returns nothing or returns the wrong phase, the wrapper falls back to AskUserQuestion (per the prose in Task 4 Step 1). That's intentional — better to ask than guess.

2. **Brainstorming override mechanism is unverified.** Task 12 explicitly checks whether the override sentence works. If it doesn't, the fix is one-line prose adjustment, then re-run. This is the only spec "open question" that's a real risk on Day 1; the others are minor.

3. **Walkthrough integration is the thinnest part of the plan.** Tasks 7 (4c) and 12 don't exercise it (Scenario 4 skips walkthrough). The first real walkthrough run will be the first time the redeploy hook is exercised. That's acceptable for Day 1 since Scenario 1, 4, 5 all skip walkthrough, but worth flagging that walkthrough end-to-end won't be validated until first real use.

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-25-milestone-orchestrator.md`.**

## Execution Handoff

Two execution options:

**1. Subagent-Driven (recommended)** — A fresh subagent per task, with review between tasks and fast iteration. Best for this plan because each task produces a self-contained deliverable (a file written, a commit landed, or a validation scenario run), making the per-task review natural.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

Which approach?
