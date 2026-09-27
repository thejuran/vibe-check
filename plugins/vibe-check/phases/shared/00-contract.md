# HARD CONTRACT (read this before doing anything)

> **Shared.** Read FIRST — before any phase and before any other file — by both `/review` and `/deep-review`, from the head of the command spine.

This command is an **orchestrator** — its sole job is to execute the phases its command spine lists, in order. The phases are NOT optional, NOT a menu, and NOT a template for inspiration. If you find yourself "skipping ahead to the report" or "improvising a summary file," STOP — that is a failure mode. Follow the prose step-by-step, in numerical phase order, top to bottom.

**Output paths — non-negotiable:**

- **WRITE only to `.turingmind/`** in the user's project. Specifically: `.turingmind/state/<$PHASE_ID>.json` where `<$PHASE_ID>` is the full resolved phase directory name (Phase 4.5; see Phase 0.5 for the exact filename rule — never abbreviate), optional `.turingmind/reviews/<ISO timestamp>/` (Phase 4.5 snapshot), and `.turingmind/REVIEW.md` (only via Finalize mode).
- **NEVER write to `.planning/`** — that namespace belongs to GSD. The tool READS PLAN.md/SPEC.md/RESEARCH.md from there (Phase 1.5) but writes nothing.
- **NEVER write per-phase review files** like `.planning/phases/<id>/<NN>-REVIEW.md` or `<NN>-DEEP-REVIEW.md` even if you see GSD/other plugins creating files in that location. **This tool does not produce per-phase artifacts in `.planning/`.** The single authoritative artifact is `.turingmind/REVIEW.md`, written by `--finalize`.
- Mid-loop `/review` and `/deep-review` invocations **print findings to the chat transcript only**. No file write of the report itself. State file under `.turingmind/state/` is the only thing persisted by a non-finalize pass.

**Phase progression — non-negotiable:**

- Announce each phase as you enter it with one line: `✓ Phase N — <name>` (or `⊘ Phase N — <name> (skipped: <reason>)` if a skip condition fires). The user reads these announcements to verify the orchestrator is on track.
- Load every phase file with the **Read tool** — never with `cat`, `head`, `sed` or any other Bash command — and Read it BEFORE you announce that phase. The Read of a phase's file is the record that its instructions were loaded; an announcement line is for the human reader and is never evidence that a phase ran. Write announcements in your reply text, never inside a Bash command.
- Phase 4 (Render) MUST be followed by Phase 4.5 (Persist state). Phase 4.5 MUST be followed by Phase 5 (Interactive fix loop) UNLESS one of Phase 5's documented skip conditions applies.
- The presence of Phase 5 as the next step is non-negotiable for any stateful invocation with findings. "I already rendered the report so I'm done" is the failure mode — Phase 5 is part of the user-facing contract, not a polish step.

**If unsure, surface the uncertainty rather than improvise.** Print "I'm uncertain about <specific phase or step> — orchestrator prose is ambiguous here" and stop. That is always preferable to inventing behavior that violates the contract above.
