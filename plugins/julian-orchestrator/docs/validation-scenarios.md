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
