# Phase 0.7 — First-run setup

> **Lazy-loaded.** Read from `commands/review.md` when Phase 0.7 is entered (first run only — Phase 0.5 routes here when no state file exists).
> Announce on entry, after this Read: `✓ Phase 0.7 — First-run setup`.

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
