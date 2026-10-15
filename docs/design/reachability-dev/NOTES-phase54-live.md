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

candidate-guard (2026-10-15T22:08Z, before any block):

```text
CANDIDATE OK candidate=302df48e1097212aa334a21c8f2683ed810eb496 head=bd5884c3c6d6eba11678d4fd98dbda70cd184891 descendant_commits=4 (reporting-only)
```

`materialize 302df48e1097212aa334a21c8f2683ed810eb496`: runner copy
`~/.b3/phase54-runner/plugin/vibe-check` := `302df48e…:plugins/vibe-check` (git archive); runner
settings from the same commit (`<RUNNER>` -> `~/.b3/phase54-runner`). `identity` (all three clone
dirs, first attempt, no refusal):

```text
IDENTITY OK manifest_id=b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c check_digest=3ce2bac84c3831cc74b538874ddaab0e7c96e539f3b37fb68f3a953c55650f5c candidate_sha=302df48e1097212aa334a21c8f2683ed810eb496
```

`park-memory`: none of the three fresh clone paths had auto-memory; park record
`~/.b3/automemory-parked-phase54-live-1792102177`.

## Cache

owner installed cache (before the sweep, 2026-10-15T22:10Z):
`~/.claude/plugins/cache/thejuran/vibe-check/2.11.1` fingerprint
`f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3` (= the v2.11.1 release).
Owner config sha256 before: `installed_plugins.json` `6a9cd0aa…`, `known_marketplaces.json`
`eafbfd5e…`, `settings.json` `3297ded3…`.

## Deviations

### SWEEP STOPPED — 2026-10-15T22:11Z — identity check refuses every run once the session is alive

**What happened (first case, `reach-new-1` run-1).** `preflight`, `fresh`, `launch` and the
in-session `session` check all printed IDENTITY OK (so the 54-09 session-process check works
live). Claude started in the tmux pane; the one-time folder-trust prompt was accepted for the
disposable clone; `/clear` was sent. The next check, at `pre`, refused:

```text
setting differs: enabled_plugins.bm@gsd-plugin
setting differs: enabled_plugins.codex@openai-codex
setting differs: enabled_plugins.frontend-design@claude-plugins-official
setting differs: enabled_plugins.model-gateway@eigenwise-toolshed
setting differs: enabled_plugins.phi-compli@thejuran
setting differs: enabled_plugins.superpowers@claude-plugins-official
setting differs: gateway.tree_sha256
file differs: codex-companion (manifest 91961610b8da live f88f408c53dd)
IDENTITY MISMATCH — STOPPING
IDENTITY MISMATCH (pre) — STOPPING
```

`run_case.sh` stopped (exit 4 path, `RUN_CASE: STOP — pre`). No keystroke reached a review, no
run directory was created (`pre` refuses before `mkdir`), so there is nothing to `fail`.

**Cause (investigated, reproduced).** Claude Code 2.1.281 writes a runtime marker
`.in_use/<pid>` (a directory holding one 52-byte file per running claude process) into the
install directory of every enabled plugin while a session runs. The measured session (pid 42926)
added `.in_use/42926` to all six enabled plugins plus the codex companion and the gateway. The
identity check hashes each enabled plugin's install tree with `freeze_common.live_files`.
`freeze_common.EXCLUDED_NAMES = (".in_use",)` intends to exclude that marker, but `live_files`
applies `EXCLUDED_NAMES` to file names only. The directory form `.in_use/` is walked and every
`.in_use/<pid>` file is hashed. The unit test (`test_freeze_common.py::test_live_files_honors_excludes`)
writes `.in_use` as a plain file, so it never exercised the real directory shape.

Reproduction: with the measured session exited (`/exit`, pid gone) its marker disappeared and the
`identity` block printed IDENTITY OK again (same manifest_id/check_digest). Three other
long-running owner claude processes (pids 44375, 48371, 51562, started 2026-10-12/14) have their
own markers in the same directories, and these were already present when the draft manifest was
generated. The identity therefore depends on which claude processes are running: every measured
session makes `pre` and `post` refuse, and any owner session that starts or exits does too.

**Scope.** The runner copy is not affected: `~/.b3/phase54-runner/plugin/vibe-check` received no
marker, because the `--plugin-dir` copy is not an installed plugin. `score43.runtime_fingerprint`
is not affected in practice: it walks only the runtime subfolders, and the marker sits at the
install root. Only the user-level `enabled_plugins`, gateway and codex-companion identities are
affected (all three go through `freeze_manifest._plugin_identity` -> `freeze_common.live_files`).

**Not done (D-23 / D-27).** No code change was made. The check was not bypassed. No marker was
deleted (they belong to live owner sessions). Making the check pass needs a change to a covered
file (`docs/design/freeze-v2.12/tools/freeze_common.py`: prune `.in_use` directories as well as
files), so the sweep is stopped and reported. That fix means a new candidate, a regenerated draft
manifest and a restart from 54-10 Task 1.

**Clean-up.** The measured session was exited (`/exit`) and its tmux session killed. `revert
reach-new-1` returned the triggarr clone to `main@4a154be`, status clean. No `.planning/HANDOFF.json`
and no clone auto-memory dir were written. `restore-memory` closed the window (nothing had been
parked; the park record was removed so a restart can run `park-memory` again). Owner cache at the
stop (2026-10-15T22:12Z): fingerprint `f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3`,
equal to the value before; config sha256 `6a9cd0aa…`, `eafbfd5e…`, `3297ded3…`, unchanged.

## Runs
