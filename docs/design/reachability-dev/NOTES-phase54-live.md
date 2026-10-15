# Phase-54 live-check notes — targeted live check — not release evidence

**Label: targeted live check — not release evidence.** Every number in this file comes from one
live run per signed-off development case on the final code candidate (D-27). Release measurement
is Phase 55 (the frozen candidate through B3 x3 and the sealed holdout x3). Nothing under
`runs-phase54-live/` is read by `score43.py aggregate`, `ledger` or the replay censuses.

Runbook: `docs/design/reachability-dev/RUN-PHASE54-live.md` (blocks run through the committed B3
runner layer `docs/design/b3-ground-truth/b3-runner-v2.12/`). Transcripts stay local (gitignored);
only `transcript.jsonl.sha256` is committed.

## Harness pins

pin-claude-code: 2.1.281 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: claude-fable-5-1[1m]

The pins equal the Phase-53 rehearsal (`NOTES-phase53-dev.md` `## Harness pins`). The model value
is the one the identity check compares with the manifest's B3 launch model
(`launch_model.b3.value` = `claude-fable-5-1[1m]` in the draft manifest). `claude --version` and
`codex --version` were checked live on 2026-10-15T22:08Z; the identity check compares the binaries
themselves, not only the version strings.

## Pre-registration — 2026-10-15T22:20Z (before the first run)

- **Candidate:** `302df48e1097212aa334a21c8f2683ed810eb496`, read from
  `docs/design/freeze-v2.12/evidence/CANDIDATE.json` (never `HEAD`).
- **Manifest:** the draft `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`,
  `manifest_id` `b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c`, used as
  `MANIFEST` for the whole sweep (the series file does not exist yet).
- **Disposable clones:** `~/.b3/phase54-clones/{roonseek,seedsyncarr,triggarr}`, cloned fresh from
  the owner's local repos at `main`, push URL disabled (`no-push-disposable-clone`), local exclude
  `.turingmind/` and `.planning/HANDOFF.json`. Environment folders built before the first run as in
  Phase-53 entry 3: triggarr `.venv` (Python 3.11) and roonseek `.venv` (Python 3.13) from the
  clone's committed `uv.lock` (`uv sync --frozen --all-extras --all-groups`); the triggarr package
  set equals the owner's; roonseek lacks the one package the owner installed outside the lock
  (`musicbrainzngs`), left uninstalled as in Phase 53; seedsyncarr `src/angular/node_modules` is a
  copy-on-write copy of the owner's. All three clones `git status` clean after provisioning. No
  block runs `checkout`, `switch`, `stash` or `revert` against the owner's repos.
- **Isolated runner:** `~/.b3/phase54-runner/plugin/vibe-check`, materialized from the candidate
  commit's git objects (`materialize` block). Only measured sessions load it (`--plugin-dir` +
  `--settings ~/.b3/phase54-runner/settings-measured.json`, which disables the installed
  `vibe-check@thejuran` for that session).
- **Owner cache untouched:** the installed `vibe-check@thejuran` cache is never resynced. Its
  fingerprint is recorded before and after the sweep under `## Cache`.
- **Auto-memory parked** for the three clone paths (`park-memory` block) before the first run and
  restored after the last (`restore-memory`).
- **One run per case** (`run-1`), in the Phase-53 final-sweep order: `reach-new-1`, `reach-new-2`,
  `reach-unchanged-1`, `reach-unchanged-2`, `triggarr-secret-in-logs`, `triggarr-autoescape`,
  `third-organic-should-catch`, `should-quiet-1`, `should-quiet-2`, `should-quiet-3`,
  `triggarr-session-rotation`, `triggarr-settings-form-split`, `should-quiet-4`, `should-quiet-5`,
  `should-quiet-6`, `should-quiet-7`. A crashed or refused run goes to `attempts/` (`fail`) and is
  redone with the next run number on the same candidate; a completed run is never rerun for a
  better outcome. No retune.
- **Keystrokes fixed:** launch (the `session` block via tmux), `/clear`, `/vibe-check:deep-review`,
  `Stop here…` then `Abandon` (by label), `/exit`. Driver: `run_case.sh`, assistant-driven via
  tmux, `--permission-mode manual`. An unexpected card, prompt or permission request = STOP.
- **Comparison:** each outcome against the Phase-53 signed-off final run
  (`NOTES-phase53-dev.md` `## Tally`); every changed outcome goes into the R4 before/after table.
  A lost catch is investigated, never rerun.

## Candidate

(filled from the `candidate-guard` and `identity` block output)

## Cache

owner installed cache (before the sweep, 2026-10-15T22:10Z):
`~/.claude/plugins/cache/thejuran/vibe-check/2.11.1` fingerprint
`f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3` (= the v2.11.1 release).
Owner config sha256 before: `installed_plugins.json` `6a9cd0aa…`, `known_marketplaces.json`
`eafbfd5e…`, `settings.json` `3297ded3…`.

## Deviations

(filled during the sweep)

## Runs
