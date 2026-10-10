# Phase 0.7 — First-run setup

> **Lazy-loaded.** Read from the command spine (`commands/review.md` or `commands/deep-review.md`) when Phase 0.7 is entered (Phase 0.5 routes here when no state file exists for this scope — which is also true on every new branch or phase of a repo that already uses vibe-check, so this file gates itself first).
> Announce on entry, after this Read and the gate fence below: `✓ Phase 0.7 — First-run setup` on `FIRST_RUN=1`; on `FIRST_RUN=0` the skip line below is the only announcement.

First, before anything else, decide whether this is the repo's first use. `.turingmind/` is checked at the repo top, never relative to the current directory:

```bash
GREPO=$(git rev-parse --show-toplevel); if [ -d "$GREPO/.turingmind" ]; then echo FIRST_RUN=0; else echo FIRST_RUN=1; fi
```

**FIRST_RUN=0** → print `⊘ Phase 0.7 — First-run setup (skipped: .turingmind/ exists)` as message text and return to the spine — no gitignore tip, no migration card, no AskUserQuestion, and none of the steps below.

**FIRST_RUN=1** → first use of vibe-check in this repo. Run these steps, in order (every path is under the repo top `$GREPO`; each fence re-derives it because shell state does not survive between Bash calls):

   1. Create dirs:
      ```bash
      GREPO=$(git rev-parse --show-toplevel); mkdir -p "$GREPO/.turingmind/state" "$GREPO/.turingmind/reviews"
      ```

   2. Check the repo-top `.gitignore` for a `.turingmind/` entry. If absent, print one-line suggestion to user (do NOT auto-edit):
      ```
      ℹ Tip: add `.turingmind/` to your .gitignore (working state, not artifact). The REVIEW.md from --finalize is the only thing meant to be committed.
      ```

   3. Migration check: if `$GREPO/.gsd/turingmind-review/` or `$GREPO/.gsd/reviews/` exists, surface ONE AskUserQuestion:

      Question: "Found old TuringMind state under `.gsd/`. Move to `.turingmind/`?"
      Options:
        - "Yes, move it" → `GREPO=$(git rev-parse --show-toplevel); [ -d "$GREPO/.gsd/turingmind-review" ] && mv "$GREPO/.gsd/turingmind-review" "$GREPO/.turingmind/reviews-archived-from-gsd"; [ -d "$GREPO/.gsd/reviews" ] && mv "$GREPO/.gsd/reviews" "$GREPO/.turingmind/reviews-old"`
        - "No, leave it" → do nothing
        - "Delete the old state" → `GREPO=$(git rev-parse --show-toplevel); rm -rf "$GREPO/.gsd/turingmind-review" "$GREPO/.gsd/reviews"`
