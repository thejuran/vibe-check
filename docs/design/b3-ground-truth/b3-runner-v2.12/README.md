# B3 runner identity layer (v2.12)

This directory is the committed runner layer that every v2.12 B3 measurement run goes through.
The freeze manifest covers it (`docs/design/b3-ground-truth/b3-runner-v2.12` is a covered path in
`freeze_manifest.COVERED`). Editing any file here after the freeze is an identity change: the next
`b3_identity_check` stops until a new manifest is issued.

`~/.b3/b3` and the Phase-53 runner (`~/.b3/phase53-runner/`) are superseded for v2.12 measurement.
Both were uncommitted, and both compared a cache fingerprint recorded in a local env file instead
of the manifest.

| File | What it is |
|---|---|
| `common.sh` | Sourced by a runbook's `common` block and by `run_case.sh`. Provides `b3_materialize_runner`, `b3_identity_check`, `b3_stamp_run`, `b3_block`, plus the isolation and case helpers. |
| `run_case.sh` | The tmux driver for one measured run (`run_case.sh <case> <run>`). It uses the fixed keystroke set and stops (exit 4) on any unexpected card. |
| `settings-measured.json` | The runner settings template. It disables the installed `vibe-check@thejuran`, pins `DISABLE_AUTOUPDATER=1` and `DISABLE_UPDATES=1`, and points the status line at `<RUNNER>/statusline-capture.sh`. |
| `statusline-capture.sh` | Records the session's status-line payload (model id, context window) to `statusline-payloads.jsonl` beside itself, then renders the owner's status line. |

## Contract

1. **The runner copy comes from the candidate commit.** `b3_materialize_runner <sha>` extracts
   `plugins/vibe-check` from git objects (`git archive`) into `$RUNNER/plugin/vibe-check`. It never
   copies from the working tree. The runner settings and capture script come from the same commit.
   The settings get exactly one edit: the literal `<RUNNER>` in `statusLine.command` becomes the
   runner directory. That is the single substitution the manifest's runner-settings record allows
   for.
2. **Every launch-bearing block calls `b3_identity_check`.** In a runbook, `preflight`, `launch`,
   `session`, `pre` and `post` each call it, so new runs, retries and resumed runs are all
   re-checked.
   `b3_identity_check` runs:

   ```text
   python3 "$FREEZE_TOOLS/freeze_check.py" verify --runner b3 --plugin-dir "$RUNNER_PLUGIN" \
     --settings "$RUNNER_SETTINGS" --model "$MODEL" --clone-dir "$CLONE" [--manifest "$MANIFEST"]
   ```

   It does not pass `--home`. The check compares the real user-level configuration, permissions
   included. Any exit other than 0 prints the differences and then
   `IDENTITY MISMATCH (<label>) — STOPPING`. No flag or variable skips the check. It also stops
   when the runner copy was built from a commit other than the manifest candidate.
3. **The file checked is the file loaded, in the environment checked.** `claude` starts only from
   the runbook's `session` block. `launch` hands that block to `tmux new-session` as an argument
   list (or prints it as the paste form). The block runs `b3_identity_check` inside the process
   that becomes `claude`. It requires the same `manifest_id` and `candidate_sha` that `launch`
   verified, and then runs `exec claude` with `--settings "$RUNNER_SETTINGS"` and
   `--plugin-dir "$RUNNER_PLUGIN"`, the same variables its check received. A tmux pane inherits
   the environment of whichever shell started the tmux server, not the launching block's. A check
   run only in the block shell could therefore vouch for a different environment, and this rule
   closes that gap.
4. **Every run is stamped.** `b3_stamp_run <run_dir>` writes `fingerprint.txt`:

   ```text
   runtime_fingerprint: <score43.py fingerprint over the runner copy>
   manifest_id: <64 hex>
   check_digest: <64 hex>
   candidate_sha: <40 hex>
   ```

   `post` refuses to archive a run whose stamp names a different manifest or candidate from the
   identity it just verified.
5. **Blocks run from committed runbook text only.** `b3_block <runbook> <name> [args…]` refuses a
   runbook that has uncommitted changes. It then runs the runbook's `common` block plus the named
   block under bash, with the arguments as `$1`, `$2`, and so on.

`docs/design/freeze-v2.12/tools/test_b3_runner_layer.py` locks these rules. Each rule has a test on
the real files and a mutant that shows the test would trip.

## Variables (defaults)

`REPO=~/turingmind-code-review`, `RUNNER=~/.b3/phase54-runner`, `RUNNER_PLUGIN=$RUNNER/plugin/vibe-check`,
`RUNNER_SETTINGS=$RUNNER/settings-measured.json`, `FREEZE_TOOLS=$REPO/docs/design/freeze-v2.12/tools`,
`SCRIPTS=$REPO/plugins/vibe-check/scripts`, `MANIFEST` (empty means the active manifest; a relative
path is taken from `$REPO`), `ENV=~/.b3/phase54-live.env`. The runbook's `common` block sets the
per-window values: `NOTES`, `CLONES_ROOT`, `ARCHIVE`, `ATTEMPTS`, `MEMPARK_ENV`.
