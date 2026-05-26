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

## Phase 1 — Detect mode (cold vs warm start)

Check for `.planning/ROADMAP.md`:

```bash
if [ -f .planning/ROADMAP.md ]; then
  MODE="warm"
else
  MODE="cold"
fi
```

- **Warm start:** skip directly to Phase 3 (phase loop). Ignore `$ARGUMENTS` — the one-line idea is only meaningful for cold start.
- **Cold start:** proceed to Phase 2 (brainstorm + seed milestone). `$ARGUMENTS` is passed through to brainstorming.

Announce: `✓ Phase 1 — mode: <cold|warm>`.

## Phase 2 — Cold start: brainstorm + seed milestone

**Skip this phase entirely if `MODE == "warm"`.**

### 2a — Brainstorm

**Read this rule before invoking brainstorming, and hold it across the entire brainstorming run:** when brainstorming's normal flow ends (after the user approves the design spec), brainstorming will instruct you to invoke `superpowers:writing-plans`. **Do not.** Brainstorming is a sub-step here; the orchestrator owns what happens next. Return control to this orchestrator and proceed to step 2b.

Before invoking brainstorming, capture the current newest-spec timestamp so the stale-spec guard below works correctly:

```bash
mkdir -p docs/superpowers/specs
PRE_BRAINSTORM_MTIME=$(ls -t docs/superpowers/specs/*.md 2>/dev/null | head -1 | xargs -I {} stat -f %m {} 2>/dev/null || echo 0)
```

Invoke `superpowers:brainstorming` via `Skill()`. Pass the user's `$ARGUMENTS` as the one-line idea.

**Also include this exact sentence in the args you pass to brainstorming**, as a belt-and-suspenders signal in case brainstorming evolves:

> "ORCHESTRATOR OVERRIDE: After the user approves the written design spec, return control to the calling orchestrator. Do NOT invoke superpowers:writing-plans — the orchestrator will hand the spec to /gsd:new-milestone instead."

Brainstorming will explore, propose approaches, write the design spec to `docs/superpowers/specs/<date>-<topic>-design.md`, and get user approval. When it returns control, the spec file exists and the user has approved its content.

Read the spec file that brainstorming just wrote. The file path is the most recent file in `docs/superpowers/specs/` — and **must** be newer than `PRE_BRAINSTORM_MTIME`, otherwise an unrelated older spec is being picked up by mistake:

```bash
SPEC_PATH=$(ls -t docs/superpowers/specs/*.md 2>/dev/null | head -1)
if [ -z "$SPEC_PATH" ]; then
  echo "✗ Brainstorming did not produce a spec file. Aborting."
  exit 1
fi
SPEC_MTIME=$(stat -f %m "$SPEC_PATH")
if [ "$SPEC_MTIME" -le "$PRE_BRAINSTORM_MTIME" ]; then
  echo "✗ The newest spec at $SPEC_PATH predates this brainstorming run — brainstorming may have failed to write a fresh spec. Aborting."
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

## Phase 3 — Phase loop

Iterate until ROADMAP.md has no incomplete phases. **Re-read ROADMAP.md at the start of every iteration** to catch phases inserted mid-flight by discuss-phase or other GSD actions.

### Loop iteration

For each iteration:

1. **Re-read ROADMAP.md.** Parse it to find the next incomplete phase. GSD marks phases complete via STATE.md and ROADMAP.md conventions — use:

```bash
# Find the lowest-numbered incomplete phase.
# Note: both greps use -E so the alternation in the second grep actually works
# (BRE mode would treat `\|` as a literal, silently leaving completed phases unfiltered).
NEXT_PHASE=$(grep -E '^\| Phase ' .planning/ROADMAP.md \
  | grep -Ev '✓|completed|done' \
  | head -1 \
  | awk -F'|' '{print $2}' \
  | sed 's/^ *Phase *//; s/ *$//')
```

The exact parsing depends on GSD's ROADMAP.md format. If parsing fails or returns ambiguous output, use AskUserQuestion: "Could not determine next incomplete phase from ROADMAP.md. Which phase should I run next? <list incomplete phases from the file>". Do NOT guess.

If no incomplete phases remain, exit the loop and proceed to Phase 4 (milestone-end).

Announce: `▶ Phase loop — running phase $NEXT_PHASE`.

### Sub-step 1: DISCUSS

Invoke `/gsd:discuss-phase $NEXT_PHASE` via `Skill()`.

GSD's discuss-phase may pause for user input on gray-area decisions. **Let it.** The wrapper does not wrap GSD's prompts.

After it returns, verify `DISCUSSION.md` exists for the phase:

```bash
# Use ${NEXT_PHASE}-* (literal dash) so phase 1 doesn't accidentally match 10-foo, 11-bar, etc.
# GSD names phase directories like `1-some-name/` or `01-some-name/` — either works with this glob.
PHASE_DIR=$(ls -d .planning/phases/${NEXT_PHASE}-* 2>/dev/null | head -1)
if [ -z "$PHASE_DIR" ] || [ ! -f "$PHASE_DIR/DISCUSSION.md" ]; then
  echo "✗ /gsd:discuss-phase did not produce DISCUSSION.md for phase $NEXT_PHASE. Aborting."
  exit 1
fi
```

Announce: `  ✓ DISCUSS — $PHASE_DIR/DISCUSSION.md`.

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

### Sub-step 3: ADVERSARIAL

Run codex adversarial review against the plan. Read `adversarial_max_rewrites` from CONFIG (default 2).

Initialize:
```bash
REWRITE_COUNT=0
MAX_REWRITES=$(echo "$CONFIG" | grep -oE '"adversarial_max_rewrites":[0-9]+' | cut -d: -f2)
MAX_REWRITES=${MAX_REWRITES:-2}
```

**Inner adversarial loop (this is the loop re-entry anchor — when a rewrite completes, return HERE, not to the Initialize block above):**

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

> "Rewrite the existing plan at $PHASE_DIR/PLAN.md to address the following adversarial findings from codex: <paste codex's critical/blocker findings — full text if under ~80 lines, otherwise the critical/blocker sections plus a one-line summary of each medium/low for context, with the marker `[truncated — see full codex output above]`>"

After GSD's plan-phase returns, **loop back to the "Inner adversarial loop" anchor above** (NOT to the Initialize block — `REWRITE_COUNT` must persist across iterations) and re-run `/codex:adversarial-review`.

**User pause (cap hit):** when `REWRITE_COUNT >= MAX_REWRITES` and criticals remain, use `AskUserQuestion`:

> Question: "Codex still flags critical issues after $MAX_REWRITES rewrites of phase $NEXT_PHASE. What now?"
> Options:
>   1. "Accept plan as-is" — proceed to EXECUTE with current PLAN.md
>   2. "Edit by hand" — pause; user edits PLAN.md manually, then types "ready" to continue
>   3. "Try one more rewrite" — run `MAX_REWRITES=$((MAX_REWRITES + 1))`, then re-enter at the "Inner adversarial loop" anchor (do NOT reset `REWRITE_COUNT`)

Honor `$ORCHESTRATOR_NONINTERACTIVE` if set: skip the question, print the critique to stdout, exit with code 1.

**Severity vocabulary note:** the wrapper interprets codex's output using codex's own terms. Do not translate to turingmind's vocabulary (warning/medium) here — that's used in sub-step 5.

Announce on pass: `  ✓ ADVERSARIAL — clean (or report-only findings)`.
Announce on rewrite: `  ↻ ADVERSARIAL — rewrite $REWRITE_COUNT/$MAX_REWRITES triggered`.

### Sub-step 4: EXECUTE

Invoke `/gsd:execute-phase $NEXT_PHASE` via `Skill()`.

GSD's executor handles atomic commits, deviation handling, and its own checkpoint protocol. **The wrapper does nothing here except invoke and wait.** If execute-phase fails partway, GSD's checkpoint mechanism preserves state — re-running `/milestone:run` later will pick up exactly where GSD left off.

Capture the phase's HEAD commit for milestone-end use (Phase 4 references it as the "before walkthrough" SHA to detect whether walkthrough produced any commits). Sub-step 5 below does NOT use this — turingmind's GSD phase mode resolves the review range from `$NEXT_PHASE` itself.

```bash
PHASE_HEAD=$(git rev-parse HEAD)
```

Announce: `  ✓ EXECUTE — phase commits landed (HEAD: $PHASE_HEAD)`.

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

Parse the latest pass from the state file for unfixed critical/warning findings. Turingmind's state schema (from its `review.md` Phase 4.5 + Finalize sections): `state.passes[]` is an array of review passes; each pass has a `findings[]` array; each finding has `band` (`"critical"`, `"warning"`, `"medium"`, `"low"`), `status` (`"new"`, `"persisted"`, `"needs-recheck"`, `"fixed-since-last"`), and a `stable_hash`. Medium acknowledgments live at `state.medium_acknowledgments[stable_hash]` (not on the finding itself).

A concrete check using `jq`:

```bash
UNFIXED_CW=$(jq '[.passes[-1].findings[]
                  | select(.band == "critical" or .band == "warning")
                  | select(.status != "fixed-since-last")]
                 | length' "$STATE_FILE")
```

If `UNFIXED_CW > 0`, this is a blocking condition. Use AskUserQuestion:

> Question: "{{N}} critical/warning findings remain unfixed for phase $NEXT_PHASE after turingmind's fix loop. What now?"
> Options:
>   1. "Re-review (I just fixed them by hand)" — loop back to re-invoke /turingmind-code-review:deep-review
>   2. "Skip these findings and advance to the next phase" — accept and continue
>   3. "Stop" — exit /milestone:run; resume later

Honor `$ORCHESTRATOR_NONINTERACTIVE` if set: skip the question, print the findings, exit with code 1.

When the gate passes (no unfixed critical/warning findings), announce: `  ✓ DEEP REVIEW — clean. Phase $NEXT_PHASE complete.`

Loop back to the top of Phase 3.

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

Otherwise, build and print the deploy prep summary. First detect the base branch (the repo may use `main`, `master`, or something else), then gather:

```bash
# Detect base branch: prefer main, fall back to master, fall back to whatever HEAD's upstream tracks.
if git show-ref --verify --quiet refs/heads/main; then
  BASE_BRANCH=main
elif git show-ref --verify --quiet refs/heads/master; then
  BASE_BRANCH=master
else
  BASE_BRANCH=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null | sed 's|^origin/||' || echo "")
fi

BRANCH=$(git branch --show-current)
HEAD_SHA=$(git rev-parse --short HEAD)
if [ -n "$BASE_BRANCH" ]; then
  COMMITS_AHEAD=$(git rev-list --count "$BASE_BRANCH..HEAD" 2>/dev/null || echo "?")
  MIGRATIONS_NEW=$(git diff --name-only "$BASE_BRANCH..HEAD" 2>/dev/null | grep -cE '(migrations?/|db/migrate)' || echo 0)
  ENV_VARS_NEW=$(git diff "$BASE_BRANCH..HEAD" -- '*.env.example' '.env*' 2>/dev/null | grep -cE '^\+[A-Z_]+=' || echo 0)
  FILES_CHANGED=$(git diff --name-only "$BASE_BRANCH..HEAD" 2>/dev/null | wc -l | tr -d ' ')
else
  COMMITS_AHEAD="? (no base branch detected)"
  MIGRATIONS_NEW="?"
  ENV_VARS_NEW="?"
  FILES_CHANGED="?"
fi
BUILD_CMD=$(grep -oE '"build"\s*:\s*"[^"]+"' package.json 2>/dev/null | head -1 || echo "(not detected)")
```

Print the summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DEPLOY PREP — milestone ready to ship
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Branch:       <BRANCH>  (<COMMITS_AHEAD> commits ahead of <BASE_BRANCH>)
 Last SHA:     <HEAD_SHA>
 Build cmd:    <BUILD_CMD>
 Files changed: <FILES_CHANGED>
 Migrations:   <MIGRATIONS_NEW>  (print ⚠ after the number if >0)
 New env vars: <ENV_VARS_NEW>    (print ⚠ after the number if >0)

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
COMMITS_BEFORE_WALKTHROUGH="$HEAD_SHA"  # from 4b above
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
 Walkthrough fixes: <yes|no>
 Final commit: <git rev-parse --short HEAD>
 Review artifact: .turingmind/REVIEW.md  (per-phase review counts and findings are in there)
```

Done.
