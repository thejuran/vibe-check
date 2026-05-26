# Milestone Orchestrator — Design Spec

**Date:** 2026-05-25
**Author:** thejuran (via brainstorming session with Claude)
**Status:** Approved, ready for implementation plan

## Problem

The user runs a stack of related but independently-developed Claude Code skills (GSD, turingmind-code-review, codex, walkthrough, superpowers/brainstorming) and wants to sequence them through a complete milestone flow:

```
brainstorm → roadmap → discuss-phase → plan-phase → codex adversarial challenge →
rewrite plan if needed → execute-phase → turingmind deep-review →
loop until all phases done → walkthrough on deployed build → fixes → complete-milestone
```

Forking GSD to bolt these steps in would mean inheriting 244k lines of code and a maintenance fork problem. The goal is to **compose existing skills as-is**, so they continue to update from their original authors.

## Constraints

1. **No fork.** Upstream skills must remain unmodified and update independently.
2. **Personal tool first.** Not optimizing for shareability or generality on Day 1; private use is fine, public later if it proves out.
3. **Stateless wrapper.** GSD's `.planning/STATE.md` is the single source of truth for *phase progress*. ROADMAP.md is the source of truth for *phase list*. Per-phase artifacts (PLAN.md, RESEARCH.md, DISCUSSION.md, commit history) are the source of truth for *intra-phase state*. The orchestrator writes nothing of its own.
4. **Empirically grounded review depth.** The user keeps finding real issues at deep-review tier, so the design always uses deep-review (not the cheaper quick `/review`).
5. **Manual NAS deploy.** Wrapper does not push code anywhere; it prepares the user with what they need to know, then pauses for the user to deploy.

## Approach

**Approach 1 (selected): Thin shell over existing skills.**

The orchestrator is a single workflow markdown file in a personal plugin. It does three kinds of things:
1. Read files to decide branches
2. Invoke other skills (`/gsd:*`, `/codex:adversarial-review`, `/turingmind-code-review:deep-review`, `walkthrough`)
3. Pause for the user at specific decision points

No business logic, no state file, no JS hooks, no MCP server. ~150–250 lines of orchestrator markdown.

**Rejected alternatives:**

- *Approach 2 (GSD-aware extension):* Modify GSD's `autonomous.md` or add hook integration points. Rejected — this is forking with extra steps.
- *Approach 3 (Imperative script):* Build a Node/Python orchestrator that drives Claude Code via CLI. Rejected — fights the skill model, requires parsing upstream output (brittle), massive over-engineering for personal use.

## Architecture & Packaging

### Plugin shape

```
~/code/julian-orchestrator/                  # personal repo, not pushed initially
├── .claude-plugin/
│   └── plugin.json                          # name, version, description
├── README.md                                # install + usage notes
└── commands/
    └── milestone.md                         # the orchestrator workflow
```

### Command

Single command: **`/milestone:run [optional one-line idea]`**

- Cold start (no `.planning/ROADMAP.md`): brainstorm → seed `/gsd:new-milestone` with the resulting design → enter phase loop
- Warm start (`.planning/ROADMAP.md` exists): skip directly to phase loop

### Composition principle

The wrapper reads three things:
- `.planning/ROADMAP.md` — to know what phases exist
- `.planning/STATE.md` — to know what's done
- Each phase dir's artifacts — to make pass/fail decisions

The wrapper writes nothing. GSD and turingmind already write everything that needs writing. Resume = re-run `/milestone:run`; it picks up wherever GSD's state says we are.

## Phase Loop Flow

This is the body of the loop the wrapper runs until every phase in `ROADMAP.md` is complete.

```
for each incomplete phase in ROADMAP.md:

  ┌─────────────────────────────────────────────────────────┐
  │ 1. DISCUSS       /gsd:discuss-phase <N>                 │
  │    └─ outputs: .planning/phases/<N>/DISCUSSION.md       │
  ├─────────────────────────────────────────────────────────┤
  │ 2. PLAN          /gsd:plan-phase <N>                    │
  │    └─ internally runs: researcher → planner →           │
  │       plan-checker. Produces RESEARCH.md + PLAN.md.     │
  │    └─ Wrapper does NOT call /gsd:research-phase         │
  │       separately — research is already inside plan.     │
  ├─────────────────────────────────────────────────────────┤
  │ 3. ADVERSARIAL   /codex:adversarial-review              │
  │    │              inputs: PLAN.md, RESEARCH.md,         │
  │    │              DISCUSSION.md                         │
  │    │              (richer context lets codex catch      │
  │    │              "plan ignored its own research")      │
  │    ├─ findings = critical/blocker → REWRITE             │
  │    │   ├─ re-run /gsd:plan-phase with critique          │
  │    │   ├─ re-run /codex:adversarial-review              │
  │    │   └─ max 2 rewrites; then pause for user           │
  │    └─ findings = medium/low → REPORT, continue          │
  ├─────────────────────────────────────────────────────────┤
  │ 4. EXECUTE       /gsd:execute-phase <N>                 │
  │    └─ phase work commits to git via GSD's executor      │
  ├─────────────────────────────────────────────────────────┤
  │ 5. DEEP REVIEW   /turingmind-code-review:deep-review <N>│
  │    │              (turingmind's GSD phase mode —        │
  │    │              reviews phase's commit range only)    │
  │    ├─ findings = critical/warning → BLOCK               │
  │    │   ├─ turingmind's Phase 5 fix-loop runs inline     │
  │    │   ├─ if all auto-fix → re-run review (verify)      │
  │    │   └─ if drift/no-fix → pause for user              │
  │    └─ clean → phase complete, advance                   │
  └─────────────────────────────────────────────────────────┘

  re-read ROADMAP.md (catches dynamically-inserted phases)

end loop
```

### Key behavioral rules

- **Severity gates use consistent logic but tool-native vocabulary.** Step 3 (codex adversarial) uses codex's severity terms (`critical`/`blocker` vs `medium`/`low`); step 5 (turingmind) uses turingmind's bands (`critical`/`warning` vs `medium`/`low`). The behavioral rule is the same: top-band = block-or-rewrite; lower-band = report-and-continue. The wrapper does NOT translate between the two vocabularies — each step interprets its own tool's output.
- **Re-read ROADMAP.md every iteration** (mirrors `/gsd:autonomous`). Phases can be inserted mid-flight by `discuss-phase` surfacing work.
- **Adversarial rewrite cap = 2.** Without this a nitpicky critic could grind forever. After 2 rewrites the wrapper pauses with explicit options.
- **Deep-review runs against the phase's commit range only.** Turingmind supports GSD phase mode natively (`$PHASE_ID = <resolved-name>` per `plugins/turingmind/commands/review.md`).
- **Wrapper does NOT invoke turingmind's `--finalize` mid-loop.** `--finalize` writes `.turingmind/REVIEW.md` (a milestone artifact). Called exactly once at milestone-end, before deploy.

### Failure modes

| Failure | Behavior |
|---|---|
| `/gsd:discuss-phase` blocks on a gray area | Surface to user (GSD's normal behavior). Wrapper waits. |
| Codex still flags critical issues after 2 rewrites | Pause; user picks: accept-as-is / edit-by-hand / try one more rewrite. |
| Deep-review has drifted findings the auto-fix can't apply | Pause; show drift report; user fixes by hand, then types "ready" to re-review. |
| `/gsd:execute-phase` fails partway | GSD's own checkpoint takes over. Wrapper exits cleanly. Resume picks up at the same phase. |
| User interrupts mid-loop | Stateless; `/milestone:run` resumes from GSD state next invocation. |

## Entry & Milestone Boundaries

### Cold-start (no `.planning/ROADMAP.md`)

```
/milestone:run "build a thumbnail cache for the photo app"
   │
   ├─ 1. BRAINSTORM
   │     Invoke superpowers:brainstorming with the one-liner.
   │     OVERRIDE: do NOT auto-hand-off to writing-plans.
   │     Output: design spec at docs/superpowers/specs/<date>-<topic>-design.md
   │
   ├─ 2. SEED MILESTONE
   │     Invoke /gsd:new-milestone, passing the design spec as the
   │     "what we're building" input. GSD's roadmapper produces
   │     PROJECT.md, ROADMAP.md, and per-phase scaffolding.
   │
   └─ 3. ENTER PHASE LOOP
```

**The brainstorming override is the integration point.** Brainstorming's normal terminal state is invoking `superpowers:writing-plans`. The orchestrator instead intercepts at the "design doc written + user-approved" gate and feeds that doc into `/gsd:new-milestone`. Writing-plans is not invoked — GSD's roadmapper is the planning layer for this flow.

**Mechanism:** when `/milestone:run` invokes brainstorming, it sets a sentinel in the prompt: "after the user approves the spec, return control to the orchestrator rather than invoking writing-plans."

### Warm-start (`.planning/ROADMAP.md` exists)

```
/milestone:run
   │
   └─ ENTER PHASE LOOP
```

No re-brainstorm, no re-roadmap. Existing roadmap drives. New phases mid-flight: add via `/gsd:add-phase` or `/gsd:insert-phase`, loop's re-read-ROADMAP picks them up.

### Milestone-end (loop exits — all phases complete)

```
  ├─ 1. FINALIZE TURINGMIND REVIEW
  │     /turingmind-code-review:deep-review --finalize
  │     Writes .turingmind/REVIEW.md (the milestone artifact).
  │     Any unacknowledged medium findings get the user prompt loop.
  │
  ├─ 2. DEPLOY PREP & PAUSE
  │     Print prep summary:
  │       - Branch, last SHA, build cmd
  │       - Changed file counts by area
  │       - Migrations present? (⚠ warning marker)
  │       - New env vars? (⚠ warning marker)
  │       - Test status
  │       - Project-specific items from .orchestrator.json
  │     Pause: "Deploy to NAS, then paste URL (or 'skip' to skip walkthrough)."
  │
  ├─ 3. WALKTHROUGH
  │     Invoke walkthrough skill with the URL.
  │     Walkthrough's own fix-cycle takes over:
  │       - finds bug → orchestrator helps fix locally → commit
  │       - asks "redeploy done? (y/n)" → resume walkthrough
  │       - repeats until walkthrough reports clean
  │
  ├─ 4. POST-WALKTHROUGH DEEP REVIEW (only if fixes were committed)
  │     If walkthrough produced any commits, run one final
  │     /turingmind-code-review:deep-review on those commits.
  │     Block-and-fix gate same as per-phase rule.
  │
  └─ 5. COMPLETE MILESTONE
        /gsd:complete-milestone
        Archives the milestone. Wrapper exits with summary line.
```

**Why a second deep-review after walkthrough (step 4):** walkthrough fixes are real code commits and shouldn't bypass the same quality gate every phase got. Skipped if walkthrough committed nothing.

**Deploy prep summary intent:** tell the user everything they'd grep for themselves before a manual deploy. Migrations and new env vars get `⚠` markers because those are the deploy-killers.

## Configuration

The wrapper reads **one optional file**: `.orchestrator.json` at the repo root. Everything has a default.

```json
{
  "review_tier": "deep",
  "adversarial_max_rewrites": 2,
  "skip_walkthrough": false,
  "deploy_prep_extras": []
}
```

| Key | Default | Purpose |
|---|---|---|
| `review_tier` | `"deep"` | `"deep"` / `"quick"` / `"escalate"`. Locked to `"deep"` by current decision; key exists for future flexibility. |
| `adversarial_max_rewrites` | `2` | Hard cap before pausing for user. |
| `skip_walkthrough` | `false` | For projects without a deployable surface (e.g., a library). When true, milestone-end skips step 3 and goes to complete-milestone. |
| `deploy_prep_extras` | `[]` | Free-form strings, printed verbatim under "Project-specific:" in the prep output. Example: `["check Portainer stack name", "verify nginx config reload"]`. |

**Missing file:** wrapper uses defaults, prints `ℹ No .orchestrator.json — using defaults. Create one if you want project-specific deploy notes.`

**No schema validation.** Personal tool; typos get silently ignored. Not worth the maintenance.

## User Interaction Points

The wrapper pauses for the user in exactly these moments, using `AskUserQuestion` with explicit options.

| Where | Question | Options |
|---|---|---|
| Cold-start brainstorm complete | (Brainstorming's own gate — spec approved before orchestrator continues) | Approved / changes requested |
| `/gsd:discuss-phase` blocks on gray area | (GSD's own prompt — wrapper just waits) | — |
| Adversarial findings, after 2 rewrites still critical | "Codex still flags critical issues after 2 rewrites. What now?" | Accept plan as-is / Edit by hand / Try one more rewrite |
| Deep-review has drifted findings the auto-fix can't apply | "{{N}} findings need manual attention (drift/no-fix). Address them, then..." | I've fixed them, re-review / Skip these findings / Stop |
| Loop complete — deploy prep | "Deploy to NAS, then paste URL (or 'skip' to skip walkthrough)" | URL text input / "skip" |
| Walkthrough fix-loop — redeploy needed | "Redeploy done?" | Yes / No (still working) / Stop |
| Walkthrough finds nothing fixable autonomously | (Walkthrough's own prompt — wrapper just waits) | — |

**Principle:** the wrapper only adds pauses where it has unique information to surface (rewrite cap hit, drift, deploy prep). It does NOT wrap GSD's or walkthrough's own prompts — those pass through to the user directly.

## Non-Interactive Mode

Honor `$ORCHESTRATOR_NONINTERACTIVE=1` (mirrors `$TURINGMIND_NONINTERACTIVE`). In non-interactive mode:

- Adversarial rewrite cap hit → stop with error code, log state
- Drifted findings → stop with error code, log findings
- Deploy prep → stop after printing the prep summary; don't try to walkthrough

Not a Day-1 requirement. Design accommodates it without baking it in.

## Testing & Validation

### Approach

**No automated tests on Day 1.** The wrapper's correctness is a function of:
1. Markdown prose being clear enough for Claude to follow
2. Sub-skills behaving the way their docs claim

Both are validated by running the thing, not by mocks.

### Validation scenarios (manual, run in order on a throwaway project)

**Scenario 1: Warm start, happy path, single phase**
- Setup: project with `.planning/ROADMAP.md` containing one trivial phase (e.g., "add a CHANGELOG.md")
- Run: `/milestone:run`
- Expect: discuss → plan → adversarial (clean) → execute → deep-review (clean) → finalize → deploy prep prints → walkthrough skipped (config) → complete-milestone
- Check: each step invoked the right skill; no writes outside `.planning/` and `.turingmind/`; final state "milestone complete"

**Scenario 2: Adversarial rewrite cycle**
- Setup: phase whose plan will plausibly draw a critical adversarial finding (e.g., auth-touching phase that omits input validation)
- Run: `/milestone:run`
- Expect: adversarial flags critical → rewrite #1 → still critical → rewrite #2 → still critical → pause with 3-option question
- Check: rewrite cap fires; pause prompt matches Section "User Interaction Points"

**Scenario 3: Deep-review drift**
- Setup: phase produces code turingmind flags; manually edit file to misalign with turingmind's `suggested_fix.old`
- Run: `/milestone:run` (or just review step)
- Expect: deep-review reports drifted findings → wrapper pauses with "address them, then..."
- Check: drift correctly detected as unfixable; orchestrator did not force-apply

**Scenario 4: Cold start end-to-end**
- Setup: empty repo, no `.planning/`
- Run: `/milestone:run "tiny CLI tool that prints uptime"`
- Expect: brainstorm → design spec written → user approves → `/gsd:new-milestone` seeded → phase loop runs → milestone-end
- Check: brainstorming did NOT invoke `superpowers:writing-plans` (override worked); design spec content was input to `/gsd:new-milestone`; loop drove to completion

**Scenario 5: Resume from interruption**
- Setup: run Scenario 1 partway, kill mid-execute
- Run: `/milestone:run` again
- Expect: wrapper detects phase in progress via `.planning/STATE.md`, picks up next sub-step (likely re-runs execute via GSD's checkpoint)
- Check: no duplicate commits, no skipped phases, no state corruption

### Day-1 quality gate

- Scenarios 1, 4, and 5 pass cleanly on a throwaway project
- Orchestrator works against an existing project with prior GSD state (i.e., picks up next phase from real `STATE.md` without breaking anything)
- Deploy prep summary contains information the user actually wants for NAS deploys — if not, signal to add `deploy_prep_extras`

Scenarios 2 and 3 are nice-to-have for confidence but not blockers — discovered organically during real use.

### Out of scope

- Sub-skill internals — not the wrapper's job
- Exact prompt phrasings — markdown evolves, tying tests to prose is brittle
- Performance — personal tool, loop runs as fast as underlying skills

## Open Questions for Implementation

These are not blockers for the plan but should be resolved during implementation:

1. **Brainstorming override mechanism specifics.** The "do not invoke writing-plans" sentinel needs concrete wording the brainstorming skill will respect. Worth checking brainstorming's source to see if there's a clean prompt-level signal vs. needing the orchestrator to intercept post-hoc.
2. **Adversarial review skill interface.** Need to confirm `/codex:adversarial-review` accepts `PLAN.md` + `RESEARCH.md` + `DISCUSSION.md` as inputs and returns findings in a format the orchestrator can severity-parse.
3. **GSD's `STATE.md` parse contract.** The wrapper reads it to know what's done. Need to confirm format stability across GSD versions or build a thin tolerance for variation.
4. **Walkthrough skill's redeploy hook.** Need to confirm walkthrough exposes a way to be told "redeploy done, resume" without restarting from scratch.

## Success Definition

The orchestrator is "done enough to use" when:

1. A cold-start invocation produces a completed milestone artifact (PROJECT.md, ROADMAP.md, per-phase artifacts, `.turingmind/REVIEW.md`) without manual intervention beyond the documented pause points.
2. A warm-start invocation on an existing real project completes at least one phase end-to-end through the full pipeline.
3. The wrapper file itself stays under ~300 lines of markdown — if it grows past that, the design has drifted from "thin shell."

## Non-Goals

- Sharing or publishing the plugin (private use first; share only if it proves out)
- Replacing or competing with `/gsd:autonomous` (this is a superset for users who want the extra steps)
- Generality across non-GSD workflows
- Pretty UI / rich output formatting beyond what the underlying skills already produce
