# Phase 1.5 — Load intent context

> **Lazy-loaded.** Read from the command spine (`commands/review.md` or `commands/deep-review.md`) when Phase 1.5 is entered (GSD phase mode only, when triage found intent docs).
> Announce on entry, after this Read: `✓ Phase 1.5 — Load intent context`.

Only runs if `$PHASE_ID` is set (GSD phase mode from Phase 0) and triage's `intent_docs_found` includes any of `PLAN.md`, `SPEC.md`, `RESEARCH.md`.

1. Read each from `$PHASE_DIR/<doc>` (the phase dir resolved in Phase 0 — correct for both flat and milestone-nested layouts). Cap each at 8000 chars.

   **When a doc exceeds the cap, truncate the MIDDLE, never the tail.** Keep the first ~5000 chars and the last ~3000 chars, joined with a `[…middle truncated]` marker. Rationale: GSD plans put goals/requirements at the top and verification/acceptance criteria at the bottom — both ends carry the intent signal the architecture and compliance agents align the diff against. The middle (task-by-task implementation detail) is the part the diff itself already shows, so it's the cheapest section to drop. Head-only truncation cuts off exactly the acceptance criteria, which silently degrades intent-alignment checking — the report still renders, the agents just review blind.

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
