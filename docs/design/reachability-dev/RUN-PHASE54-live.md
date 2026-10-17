# Phase-54 live-check runbook — targeted live checks on the final candidate (one file)

**Label: targeted live check — not release evidence.** Every archive, every notes line and every
tally this runbook produces carries that label. Release measurement is Phase 55: the frozen
candidate through B3 x3 and the sealed holdout x3.

**Template note.** Phase 55's B3 runbook inherits this one. It keeps the same blocks and the same
committed runner layer (`docs/design/b3-ground-truth/b3-runner-v2.12/`). **Every launch-bearing
block (`preflight`, `launch`, `session`, `pre`, `post`) must keep its `b3_identity_check` call,
and `claude` starts only from `session`, after its check.**
`docs/design/freeze-v2.12/tools/test_b3_runner_layer.py` locks this: deleting the call from any one
of those blocks fails the suite.

**Purpose:** rerun each signed-off development case once on the final code candidate (D-27). The
cases are the 16 cases of the Phase-53 final sweep. The runs go through the committed B3 runner
layer, so this sweep also validates that layer live. Changed outcomes go into the R4 before/after
table. A lost catch is investigated before the freeze, never closed by rerunning.

**Isolation (as Phase 53, owner instruction 2026-10-14).**

- **Disposable clones.** Cases run in `~/.b3/phase54-clones/<repo>` (`triggarr`, `seedsyncarr`,
  `roonseek`), cloned from the owner's local repos, with the push URL disabled. No block here runs
  `checkout`, `switch`, `stash` or `revert` against `~/triggarr`, `~/seedsyncarr` or `~/roonseek`.
- **Isolated runner.** `materialize` builds the runner copy `~/.b3/phase54-runner/plugin/vibe-check`
  from the candidate commit's git objects, never from the working tree. Only the measured sessions
  load it, via `--plugin-dir "$RUNNER_PLUGIN"` plus `--settings "$RUNNER_SETTINGS"`
  (`~/.b3/phase54-runner/settings-measured.json`). Those settings disable the installed `vibe-check@thejuran` for that session alone and pin
  `DISABLE_AUTOUPDATER=1` / `DISABLE_UPDATES=1`. The owner's `~/.claude` is never written.
  `isolation_check` refuses to run if the owner's registry or settings reference the runner.
- **Containment (S5/S6, both measured runners).** The runner settings
  (`settings-measured.json`, pinned by the manifest's runner-settings hash, so the identity check
  binds them) carry:
  - an OS sandbox (Seatbelt) around every Bash command and every process it starts, `python3` and
    `node` children included: `failIfUnavailable`, no unsandboxed escape, no excluded commands;
  - network for sandboxed processes limited to the Codex endpoints (`chatgpt.com`,
    `auth.openai.com`, `api.openai.com`) with `strictAllowlist`. The model gateway
    (`ANTHROPIC_BASE_URL`, `127.0.0.1:18764`) is used by the Claude Code process itself, outside
    the sandbox, so sandboxed code cannot reach it;
  - credential paths denied to sandboxed reads AND to the Read/Edit tools: `~/.ssh`, `~/.aws`,
    `~/.config/gh`, `~/.netrc`, `~/.gnupg`, `~/Library/Keychains`, `~/.claude/.credentials.json`,
    `~/.claude.json`, the holdout folder, `.env` files and the proof canary;
  - WebFetch and WebSearch denied (in-process network the sandbox does not cover);
  - the pre-approved tool set `Bash, Read, Write, Edit, Grep, Glob, Task, Agent` (S7: the
    plugin's `python3` scorer needs Bash; holdout-eval's `dontAsk` refuses anything else);
  - the codex plugin disabled for the session only: its SessionStart hook points the companion at
    a plugin-data dir under `~/.claude`, which the sandbox never lets a command write. With the
    hook off, the companion keeps its state in the sandbox temp dir. The plugin finds the companion
    by its install path, so Codex still runs (proved by the dry smoke recorded in 54-17).
  The session process itself gets an environment allowlist (`env -i` refilled by
  `b3_session_env` from `freeze_manifest.SESSION_ENV_NAMES`), never the tmux server's environment.
- **Sandboxing is an environment change.** The Phase-53 rehearsal and the earlier 54-11 sweep ran
  without it. The restarted sweep tests compatibility and shows any outcome differences; it cannot
  attribute a single difference to the sandbox, or rule the sandbox out as its cause.
- **Identity check before every run.** `preflight`, `launch`, `session`, `pre` and `post` each run
  `b3_identity_check`, which calls `freeze_check.py verify --runner b3` against the active manifest.
  For 54-11 that is the draft manifest named in `MANIFEST`. Any difference stops the block. There
  is no override. Retries and resumed runs pass through the same blocks, so they are re-checked
  too. `session` is the process that becomes `claude`: it runs the check in its own environment
  and then `exec`s `claude`, so the environment checked is the environment the session gets.

---

## 1. Pre-registration

- One run per case (`run-1`). A crashed or refused run is moved to `attempts/` (block `fail`) and
  redone with the next run number on the SAME candidate. Nothing is retuned between runs.
- Cases: `reach-new-1`, `reach-new-2`, `reach-unchanged-1`, `reach-unchanged-2`, `should-quiet-1`
  … `should-quiet-7`, `third-organic-should-catch`, `triggarr-autoescape`,
  `triggarr-secret-in-logs`, `triggarr-session-rotation`, `triggarr-settings-form-split`.
- The candidate is recorded once by `materialize`. Every run directory is stamped with the
  verified manifest identity.
- Driver: assistant-driven via tmux (`run_case.sh`), `--permission-mode manual`. The fixed
  keystroke set is the launch line, `/clear`, `/vibe-check:deep-review`, `Stop here…` then
  `Abandon` (by label), and `/exit`. An unexpected card, prompt or permission request means STOP
  and report. The owner keeps the laptop lid open.

## 2. Where things land

| What | Path |
|---|---|
| run archive | `docs/design/reachability-dev/runs-phase54-live/<case>/run-<n>/` |
| failed attempts | `docs/design/reachability-dev/runs-phase54-live/attempts/` |
| notes | `docs/design/reachability-dev/NOTES-phase54-live.md` |
| keyed sites (new-exposure cases) | `docs/design/reachability-dev/CATCH-SITES-dev.json` |
| local env file | `~/.b3/phase54-live.env` (`candidate`) |
| last identity output | `~/.b3/phase54-runner/last-identity.txt` |

Each run directory holds `clear.txt`, `fingerprint.txt` (written at `pre`), `state.json`,
`tree.diff`, `lanes.json` (and the other `lanearchive.py extract` outputs) when produced, and
`transcript.jsonl.sha256`:

```text
runtime_fingerprint: <64 hex — score43.py fingerprint over the runner copy>
manifest_id: <64 hex>
check_digest: <64 hex>
candidate_sha: <40 hex>
```

`transcript.jsonl` is copied into the run directory for the card count. It is gitignored because
it carries the owner's private instructions; only its sha is committed. The blocks never commit.

## 3. Case table

| case | kind | role |
|---|---|---|
| reach-new-1, reach-new-2 | development | catch |
| reach-unchanged-1, reach-unchanged-2 | development | quiet |
| should-quiet-1 … should-quiet-7 | B3 | quiet |
| third-organic-should-catch, triggarr-autoescape, triggarr-secret-in-logs, triggarr-session-rotation, triggarr-settings-form-split | B3 | per `score43.ROLE` |

## 4. How to run a block

Blocks cannot be pasted into zsh. Source the committed layer in a bash shell and call `b3_block`.
From the assistant's Bash tool, which runs zsh, wrap every call in `bash -s <<'BASH' … BASH`:

```text
source ~/turingmind-code-review/docs/design/b3-ground-truth/b3-runner-v2.12/common.sh
set +e
export MANIFEST=<the manifest path, empty for the active one>
B=docs/design/reachability-dev/RUN-PHASE54-live.md
b3_block "$B" <block> [args…]
```

`b3_block` runs this file's `common` block plus the named block under bash, with the arguments as
`$1`, `$2`. It refuses while this file has uncommitted changes.

### The order

| # | what | notes |
|---|---|---|
| 1 | `b3_block "$B" materialize <candidate sha>` | runner copy and runner settings from the candidate commit |
| 2 | `b3_block "$B" identity` | IDENTITY OK line, checked against each clone dir; goes into NOTES `## Candidate` |
| 3 | `b3_block "$B" park-memory` | N-02, all three disposable clones |
| 4 | per case: `run_case.sh <case> <n>` | preflight, fresh, launch (starts session), /clear, pre, review, post, /exit, revert |
| 5 | after the last case: `b3_block "$B" restore-memory` | |

`run_case.sh` lives at `docs/design/b3-ground-truth/b3-runner-v2.12/run_case.sh`. Run by hand, the
per-case steps are: `preflight <case>`, `fresh <case>`, `LAUNCH_VIA_TMUX=1 … launch <case>`,
`/clear` in the session, `printf 'CLEARED\n' | b3_block "$B" pre <case> <n>`,
`/vibe-check:deep-review`, `Stop here…` then `Abandon`, `post <case> <n>`, `/exit`,
`tmux kill-session -t p54-<case>`, `revert <case>`.

A run that crashes, stalls or is refused by `post`: `FAIL_REASON='…' b3_block "$B" fail <case> <n>`,
then redo from `preflight` with the next run number. Any change to a covered file stops the next
identity check. The remedy is to correct the install, or to issue a new manifest after the required
checks. It is never a rerun on a changed build.

---

## 5. The shared block

```bash
# BLOCK: common
set -euo pipefail
REPO=${REPO:-$HOME/turingmind-code-review}
NOTES=docs/design/reachability-dev/NOTES-phase54-live.md
CLONES_ROOT=$HOME/.b3/phase54-clones
PARK_TAG=phase54-live
# shellcheck source=/dev/null
source "$REPO/docs/design/b3-ground-truth/b3-runner-v2.12/common.sh"
STAGE=live
SITES=$RD/CATCH-SITES-dev.json
MEMPARK_ENV=$HOME/.b3/phase54-live-memory-park.env
LIVE_LABEL='targeted live check — not release evidence'
ARCHIVE=$RD/runs-phase54-live
ATTEMPTS=$RD/runs-phase54-live/attempts
CASE=${1:-}
RUN=${2:-}
TIMEOUT_BIN=$(command -v timeout || command -v gtimeout || true)
# END: common
```

---

## 6. Opening the window

### materialize `<candidate sha>`

The runner copy becomes the candidate commit's `plugins/vibe-check`, extracted from git objects.
The runner settings and the statusline capture script come from the same commit. The candidate is
an explicit argument, never `HEAD`: later reporting commits move `HEAD` past it. It is recorded in
the env file, and every identity check stops when the manifest names another candidate.

```bash
# BLOCK: materialize
set -euo pipefail
CANDIDATE=${1:-}
test -n "$CANDIDATE" || { echo 'GIVE THE CANDIDATE SHA AS THE ARGUMENT — STOPPING'; exit 1; }
b3_materialize_runner "$CANDIDATE"
isolation_check
echo "owner installed cache (untouched): $DEFAULT_CACHE"
echo 'BLOCK OK'
# END: materialize
```

### identity

Checks the identity against every disposable clone dir and prints the IDENTITY OK line for NOTES.

```bash
# BLOCK: identity
set -euo pipefail
isolation_check
resolve_model
for C in $CLONES; do
  CLONE=$CLONES_ROOT/$C
  b3_identity_check "identity $C"
done
echo "candidate (materialized): $(env_get candidate)"
echo "for NOTES ## Candidate: $IDENTITY_LINE"
echo 'BLOCK OK'
# END: identity
```

### park-memory (N-02)

```bash
# BLOCK: park-memory
set -euo pipefail
test ! -e "$MEMPARK_ENV" \
  || { echo 'MEMORY IS ALREADY PARKED (phase54-live-memory-park.env) — STOPPING'; exit 1; }
PARKDIR=$HOME/.b3/automemory-parked-phase54-live-$(date +%s)
mkdir -p "$PARKDIR"
for C in $CLONES; do
  M=$(proj_dir "$CLONES_ROOT/$C")/memory
  if test -e "$M"; then
    mv "$M" "$PARKDIR/$C"
    echo "parked $CLONES_ROOT/$C auto-memory -> $PARKDIR/$C"
  else
    echo "$CLONES_ROOT/$C has no auto-memory to park"
  fi
  test ! -e "$M" || { echo "$CLONES_ROOT/$C AUTO-MEMORY STILL PRESENT — STOPPING"; exit 1; }
done
printf 'PARKDIR=%s\n' "$PARKDIR" > "$MEMPARK_ENV"
echo 'BLOCK OK'
# END: park-memory
```

### preflight `<case>`

Run at the start of every case, retries included. The identity check covers what Phase 53 checked
by hand: the CLI and Codex versions, compared together with their binaries. A version string alone
is never the pass condition.

```bash
# BLOCK: preflight
set -euo pipefail
test -n "$CASE" || { echo 'preflight NEEDS A CASE — STOPPING'; exit 1; }
sidecar
isolation_check
b3_identity_check 'preflight'
test -z "$(git -C "$REPO" status --porcelain -- "$DD")" \
  || { echo 'docs/design/b3-ground-truth HAS CHANGES — the live path never writes there — STOPPING'; exit 1; }
test -f "$REPO/$NOTES" || { echo "NOTES FILE $NOTES MISSING — open it first — STOPPING"; exit 1; }
test -n "$TIMEOUT_BIN" || { echo 'NO timeout/gtimeout ON PATH (Codex watchdog) — STOPPING'; exit 1; }
test -f "$MEMPARK_ENV" || { echo 'MEMORY NOT PARKED — run park-memory — STOPPING'; exit 1; }
for C in $CLONES; do
  test ! -e "$(proj_dir "$CLONES_ROOT/$C")/memory" \
    || { echo "$CLONES_ROOT/$C AUTO-MEMORY IS PRESENT — run park-memory / see mem_evidence — STOPPING"; exit 1; }
done
test -d "$CLONE/.git" || { echo "CLONE $CLONE MISSING — STOPPING"; exit 1; }
grep -qx '.turingmind/' "$CLONE/.git/info/exclude" \
  || { echo "$CLONE HAS NO LOCAL .turingmind/ EXCLUDE — STOPPING"; exit 1; }
git -C "$CLONE" cat-file -e "$BASE_SHA^{commit}" || { echo 'base_sha NOT IN THE CLONE — STOPPING'; exit 1; }
if test -e "$STATE_DIR/.b3-inprogress"; then
  grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" \
    || { echo "$CLONE IS MID-DIFF FOR ANOTHER CASE — STOPPING"; exit 1; }
  echo "$CLONE is already prepared for $CASE (resuming)"
else
  test -z "$(git -C "$CLONE" status --porcelain)" || { echo "CLONE $CLONE NOT CLEAN — STOPPING"; exit 1; }
  test -n "$(git -C "$CLONE" branch --show-current)" || { echo "CLONE $CLONE IS DETACHED — STOPPING"; exit 1; }
  WT=$HOME/.b3/p54-applycheck-$CASE
  test ! -e "$WT" || { echo "STALE CHECK WORKTREE $WT — git -C $CLONE worktree remove --force $WT — STOPPING"; exit 1; }
  git -C "$CLONE" worktree add -q --detach "$WT" "$BASE_SHA"
  OK=1; git -C "$WT" apply --check "$PATCH_FILE" || OK=0
  git -C "$CLONE" worktree remove --force "$WT"
  test "$OK" = 1 || { echo 'PATCH DOES NOT APPLY AT base_sha — STOPPING'; exit 1; }
fi
echo "case: $CASE ($KIND, $ROLE) in $CLONE at base $BASE_SHA"
echo "$LIVE_LABEL"
echo 'BLOCK OK'
# END: preflight
```

---

## 7. Per case

### fresh `<case>`

```bash
# BLOCK: fresh
set -euo pipefail
sidecar
isolation_check
test -d "$CLONE/.git" || { echo "CLONE $CLONE MISSING — STOPPING"; exit 1; }
cd "$CLONE"
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
test -n "$START_BRANCH" || { echo 'CLONE IS DETACHED — STOPPING'; exit 1; }
mkdir -p "$STATE_DIR"
test ! -e "$STATE_DIR/.b3-inprogress" || { echo 'A CASE IS ALREADY IN PROGRESS HERE — STOPPING'; exit 1; }
test ! -e "$PARK" || { echo 'STALE PARK DIR WITHOUT A SENTINEL — STOPPING'; exit 1; }
mem_evidence fresh
git switch -q --detach "$BASE_SHA"
test "$(git rev-parse HEAD)" = "$BASE_SHA" || { echo 'WRONG BASE — STOPPING'; exit 1; }
git apply --check "$PATCH_FILE" \
  || { git switch -q "$START_BRANCH"; echo 'PATCH DOES NOT APPLY AT base_sha — clone restored — STOPPING'; exit 1; }
git apply "$PATCH_FILE"
test "$(clone_diff_sha)" = "$EXPECTED_SHA" \
  || { echo 'FULL WORKTREE DIFF != EXPECTED_TREE_DIFF_SHA256 — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "$TOUCHED" \
  || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
mkdir "$PARK"
PARKED=0
for f in "$STATE_DIR"/*.json; do
  test -e "$f" || continue
  mv "$f" "$PARK/"; PARKED=$((PARKED + 1))
done
mkdir "$PARK/format-53"
for f in "$STATE53"/*.json; do
  test -e "$f" || continue
  mv "$f" "$PARK/format-53/"; PARKED=$((PARKED + 1))
done
test -z "$(state_files)" || { echo 'A STATE FILE IS STILL PRESENT AFTER PARKING — STOPPING'; exit 1; }
if test "$PARKED" -gt 0; then HAD_PRIOR=true; else HAD_PRIOR=false; fi
if test -f "$CLONE/uv.lock"; then LOCK=1; else LOCK=0; fi
{
  printf 'diff_id=%s\nbase_sha=%s\n' "$CASE" "$BASE_SHA"
  printf 'had_prior_state=%s\nstart_branch=%s\nstart_sha=%s\nparked=%s\nlock=%s\nstage=%s\n' \
    "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" "$PARKED" "$LOCK" "$STAGE"
} > "$STATE_DIR/.b3-inprogress"
if test "$LOCK" = 1; then chflags uchg "$CLONE/uv.lock"; fi
echo "$CASE ready in $CLONE at $(git rev-parse HEAD), $PARKED state file(s) parked, lock=$LOCK"
echo 'BLOCK OK'
# END: fresh
```

### launch `<case>`

`launch` checks the identity, then starts the session. It never starts `claude` itself. The tmux
pane (or the paste form) runs the `session` block. That block runs the identity check again inside
the very process that then `exec`s `claude`, and stops unless it verified the same manifest and
candidate as `launch`. A tmux pane takes its environment from whichever shell started the tmux
server, not from this block's shell. The check that counts is therefore the one in the session
process, and that check sees exactly the environment `claude` inherits. The pane's own command is
the session block, passed to `tmux new-session` as an argument list, so no login shell or tmux
config runs between the check and `claude`.

```bash
# BLOCK: launch
set -euo pipefail
sidecar
isolation_check
resolve_model
b3_identity_check 'launch'
test -n "${B3_RUNBOOK:-}" || { echo 'launch RUNS THROUGH b3_block ONLY (no runbook path) — STOPPING'; exit 1; }
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" 2> /dev/null \
  || { echo "CLONE NOT PREPARED — run fresh $CASE first — STOPPING"; exit 1; }
mem_evidence launch
test ! -e "$MEM" || { echo "AUTO-MEMORY FOR $CLONE IS NOT PARKED — STOPPING"; exit 1; }
if command -v tmux > /dev/null && tmux has-session -t "=p54-$CASE" 2> /dev/null; then
  echo "TMUX SESSION p54-$CASE STILL EXISTS — /exit it and kill it — STOPPING"; exit 1
fi
SESSION_SHELL='source "$1"; set +e; b3_block "$2" session "$3"; echo "b3 session ended (exit $?) — Enter closes this pane"; read -r _ || true'
SESSION=(env "REPO=$REPO" "MANIFEST=$MANIFEST" "RUNNER=$RUNNER" "RUNNER_PLUGIN=$RUNNER_PLUGIN"
  "RUNNER_SETTINGS=$RUNNER_SETTINGS" "ENV=$ENV" "FREEZE_TOOLS=$FREEZE_TOOLS"
  "EXPECT_MANIFEST_ID=$(identity_field manifest_id)" "EXPECT_CANDIDATE_SHA=$(identity_field candidate_sha)"
  bash -c "$SESSION_SHELL" b3-session "$REPO/$LAYER_REL/common.sh" "$B3_RUNBOOK" "$CASE")
echo "Paste form (checks the identity in the session process, then starts claude):"
echo "  $(printf '%q ' "${SESSION[@]}")"
if test "${LAUNCH_VIA_TMUX:-0}" = 1; then
  command -v tmux > /dev/null || { echo 'tmux NOT INSTALLED — STOPPING'; exit 1; }
  tmux new-session -d -s "p54-$CASE" -c "$CLONE" "${SESSION[@]}"
  echo "launched in tmux session p54-$CASE (read it with: tmux capture-pane -p -t p54-$CASE)"
fi
echo "Next: /clear in the session, then printf 'CLEARED\\n' | b3_block \"\$B\" pre $CASE <n>"
echo 'BLOCK OK'
# END: launch
```

### session `<case>` (started by `launch`, never by hand)

This block runs inside the tmux pane, or in the terminal the paste form was pasted into. It loads
the runner copy (`--plugin-dir "$RUNNER_PLUGIN"`) with the runner settings
(`--settings "$RUNNER_SETTINGS"`), under `env -i` refilled only with the allowlisted environment
`b3_session_env` builds. These are the same two variables its own identity check just
verified, in the same process, so the file checked is the file loaded. The model is NOTES
`pin-model:`, the value the check compares with the manifest's launch model. A refusal leaves the
pane open with the differences on screen; `run_case.sh` then stops on "session did not reach the
input prompt".

```bash
# BLOCK: session
set -euo pipefail
sidecar
isolation_check
resolve_model
b3_identity_check 'session'
test "$(identity_field manifest_id)" = "${EXPECT_MANIFEST_ID:-}" \
  && test "$(identity_field candidate_sha)" = "${EXPECT_CANDIDATE_SHA:-}" \
  || { echo 'THE SESSION PROCESS VERIFIED ANOTHER MANIFEST OR CANDIDATE THAN launch — STOPPING'; exit 1; }
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" 2> /dev/null \
  || { echo "CLONE NOT PREPARED — run fresh $CASE first — STOPPING"; exit 1; }
test ! -e "$MEM" || { echo "AUTO-MEMORY FOR $CLONE IS NOT PARKED — STOPPING"; exit 1; }
cd "$CLONE"
b3_session_env
exec env -i "${B3_SESSION_ENV[@]}" claude --permission-mode manual --plugin-dir "$RUNNER_PLUGIN" --settings "$RUNNER_SETTINGS" --model "$MODEL" --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent"
# END: session
```

### pre `<case> <n>`

This block reads the typed `CLEARED` attestation from stdin AFTER `/clear` has completed. It
re-runs the identity check, writes the run's `clear.txt` (its mtime is the run's start marker for
`post`) and stamps the run with the verified identity.

```bash
# BLOCK: pre
set -euo pipefail
check_run
sidecar
isolation_check
b3_identity_check 'pre'
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" 2> /dev/null \
  || { echo 'CLONE NOT PREPARED FOR THIS CASE — STOPPING'; exit 1; }
test ! -e "$RUN_DIR" || { echo "$RP ALREADY EXISTS — use the next run number or fail — STOPPING"; exit 1; }
test -z "$(state_files)" \
  || { echo 'A STATE FILE IS ALREADY PRESENT (an unfinished run) — fail it — STOPPING'; exit 1; }
mem_evidence pre
read -r ATT || true
test "${ATT:-}" = CLEARED || { echo 'NO CLEARED ATTESTATION ON STDIN — STOPPING'; exit 1; }
mkdir -p "$RUN_DIR"
date -u '+%Y-%m-%dT%H:%M:%S+0000 CLEARED' > "$RUN_DIR/clear.txt"
b3_stamp_run "$RUN_DIR"
echo "run $RP open — now /vibe-check:deep-review in the session"
echo 'BLOCK OK'
# END: pre
```

### post `<case> <n>`

Every check that can refuse runs before anything is written to NOTES. The identity check runs
FIRST. The run's stamp must then name the identity just verified (the same `manifest_id` and
`candidate_sha`). Otherwise nothing is archived: `fail` the run and rerun it on a build that
passes the check.

```bash
# BLOCK: post
set -euo pipefail
check_run
sidecar
isolation_check
b3_identity_check post
test -f "$RUN_DIR/fingerprint.txt" || { echo 'THE RUN WAS NEVER STAMPED (pre) — fail — STOPPING'; exit 1; }
test "$(sed -n 's/^manifest_id: //p' "$RUN_DIR/fingerprint.txt")" = "$(identity_field manifest_id)" \
  && test "$(sed -n 's/^candidate_sha: //p' "$RUN_DIR/fingerprint.txt")" = "$(identity_field candidate_sha)" \
  || { echo 'RUN STAMP DOES NOT MATCH THE ACTIVE MANIFEST — p54 fail — STOPPING'; exit 1; }
cd "$CLONE"
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" 2> /dev/null \
  || { echo 'CLONE NOT PREPARED FOR THIS CASE — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "$BASE_SHA" || { echo 'HEAD MOVED DURING THE RUN — fail — STOPPING'; exit 1; }
test -f "$RUN_DIR/clear.txt" || { echo 'clear.txt MISSING (pre never ran) — STOPPING'; exit 1; }
test ! -e "$RUN_DIR/state.json" || { echo "$RP IS ALREADY ARCHIVED — STOPPING"; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo 'A FLAT (PRE-format-53) STATE FILE WAS WRITTEN — not the candidate build — fail — STOPPING'; exit 1; }
NEW=$(find "$STATE53" -maxdepth 1 -name '*.json' -newer "$RUN_DIR/clear.txt" 2> /dev/null || true)
test "$(printf '%s\n' "$NEW" | grep -c .)" = "1" \
  || { echo 'EXPECTED EXACTLY ONE NEW format-53 STATE FILE — fail — STOPPING'; exit 1; }
test "$(state_files | grep -c .)" = "1" \
  || { echo 'AN OLDER STATE FILE IS PRESENT — STOPPING'; exit 1; }
cp "$NEW" "$RUN_DIR/state.json"
python3 - "$RUN_DIR/state.json" "$BASE_SHA" <<'PY' || { echo 'NOT ONE ISOLATED PASS AT THE PINNED HEAD — fail — STOPPING'; exit 1; }
import json, sys
s = json.load(open(sys.argv[1]))
assert len(s["passes"]) == 1, "passes=%d" % len(s["passes"])
assert s["passes"][-1]["head_sha"] == sys.argv[2], "head mismatch"
print("OK one isolated pass at", sys.argv[2])
PY
git diff > "$RUN_DIR/tree.diff"
test "$(shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}')" = "$EXPECTED_SHA" \
  || { echo 'FULL WORKTREE DIFF != THE CASE DIFF — fail — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/' || true)" \
  || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — STOPPING'; exit 1; }
# the session transcript (+ agent sub-transcripts): local only, sha-bound
test -d "$PROJ" || { echo "NO TRANSCRIPT FOLDER FOR $CLONE — STOPPING"; exit 1; }
MAIN=$(find "$PROJ" -maxdepth 1 -name '*.jsonl' -newer "$RUN_DIR/clear.txt")
test "$(printf '%s\n' "$MAIN" | grep -c .)" = "1" \
  || { echo 'EXPECTED EXACTLY ONE SESSION TRANSCRIPT SINCE /clear — STOPPING'; exit 1; }
python3 - "$MAIN" "$RUN_DIR/transcript.jsonl" <<'PY' || { echo 'TRANSCRIPT CAPTURE FAILED — STOPPING'; exit 1; }
import glob, os, sys
main, out_path = sys.argv[1], sys.argv[2]
subs = sorted(glob.glob(os.path.join(main[:-len(".jsonl")], "subagents", "*.jsonl")))
with open(out_path, "w") as out:
    for path in [main] + subs:
        for line in open(path):
            if line.strip():
                out.write(line if line.endswith("\n") else line + "\n")
print("captured %d transcript file(s)" % (1 + len(subs)))
PY
git -C "$REPO" check-ignore -q "$RP/transcript.jsonl" \
  || { rm -f "$RUN_DIR/transcript.jsonl"; echo 'transcript.jsonl IS NOT GITIGNORED — STOPPING'; exit 1; }
grep -q 'vibe-check:deep-review' "$RUN_DIR/transcript.jsonl" \
  || { echo 'THE TRANSCRIPT HOLDS NO /vibe-check:deep-review — STOPPING'; exit 1; }
grep -qF "$CACHE" "$RUN_DIR/transcript.jsonl" \
  || { echo 'THE TRANSCRIPT NEVER NAMES THE RUNNER COPY — not the checked build — STOPPING'; exit 1; }
! grep -qF "$DEFAULT_CACHE" "$RUN_DIR/transcript.jsonl" \
  || { echo 'THE RUN LOADED THE OWNER INSTALLED RELEASE CACHE, NOT THE RUNNER COPY — fail — STOPPING'; exit 1; }
! grep -qF "$PLUGIN_ROOT" "$RUN_DIR/transcript.jsonl" \
  || { echo 'THE RUN LOADED THE REPO PLUGIN TREE, NOT THE RUNNER COPY — fail — STOPPING'; exit 1; }
shasum -a 256 "$RUN_DIR/transcript.jsonl" | awk '{print $1}' > "$RUN_DIR/transcript.jsonl.sha256"
# lane archive (lanes.json when produced) with its own privacy scan; matched text is never printed
python3 "$SCRIPTS/lanearchive.py" extract --transcript "$RUN_DIR/transcript.jsonl" \
    --state "$RUN_DIR/state.json" --out-dir "$RUN_DIR" 2> "$HOME/.b3/p54-lanearchive.err" \
  || { tail -1 "$HOME/.b3/p54-lanearchive.err" | cut -c1-80; echo 'LANE ARCHIVE REFUSED OR FAILED — STOPPING'; exit 1; }
FP_RUN=$(sed -n 's/^runtime_fingerprint: //p' "$RUN_DIR/fingerprint.txt")
# burden (R13) and, for a catch-role case, the listing for the hand AXIS call
REC=$HOME/.b3/p54-notes-record.md
{
  echo ''
  echo "### $STAGE/$CASE/run-$RUN — $LIVE_LABEL"
  echo ''
  echo "fingerprint: $FP_RUN"
  echo "identity: manifest_id=$(identity_field manifest_id) candidate_sha=$(identity_field candidate_sha)"
  echo ''
  python3 "$SCORE43" dev-burden --state "$RUN_DIR/state.json"
  if test "$KIND" = dev && test "$ROLE" = catch; then
    echo ''
    python3 "$SCORE43" dev-catch-candidates --state "$RUN_DIR/state.json" --id "$CASE" \
      --sites "$REPO/$SITES"
  elif test "$KIND" = b3 && test "$ROLE" = catch; then
    echo ''
    python3 "$SCORE43" catch-candidates --state "$RUN_DIR/state.json" --diff "$CASE"
  fi
  if test "$ROLE" = catch; then
    echo ''
    echo 'AXIS: <credit | no credit> — row <stable_hash[:12]> (<alarm | needs-verification>) — <reason against the keyed defect>'
  fi
} > "$REC"
# tree.diff is not rescanned: its sha256 equals the case's EXPECTED_TREE_DIFF_SHA256 (checked
# above), so it is byte-identical to the committed, seal-checked case patch
SCAN="$REC $RUN_DIR/state.json $RUN_DIR/fingerprint.txt"
python3 "$SCRIPTS/lanearchive.py" scan $SCAN 2> "$HOME/.b3/p54-scan.err" \
  || { tail -1 "$HOME/.b3/p54-scan.err" | cut -c1-80; echo 'PRIVACY SCAN REFUSED — NOTHING APPENDED — STOPPING'; exit 1; }
cat "$REC" >> "$REPO/$NOTES"
rm -f "$NEW"
cat "$REC"
echo ''
echo "archived $RP — fill in the AXIS line in NOTES by hand for a catch-role case"
echo 'BLOCK OK'
# END: post
```

### fail `<case> <n>`

A crashed, stalled or refused run is moved, never deleted, to
`runs-phase54-live/attempts/live-<case>-run-<n>-<epoch>/`, together with any state file it wrote.
The slot is then redone with the next run number. `FAIL_REASON` (letters, digits, spaces and
`.,:-` only) is recorded in `reason.txt`.

```bash
# BLOCK: fail
set -euo pipefail
check_run
sidecar
printf '%s' "${FAIL_REASON:-}" | grep -qE '^[A-Za-z0-9 .,:-]{3,120}$' \
  || { echo 'FAIL_REASON MUST BE 3-120 CHARS OF [A-Za-z0-9 .,:-] — STOPPING'; exit 1; }
test -d "$RUN_DIR" || { echo "$RP DOES NOT EXIST — STOPPING"; exit 1; }
DEST=$REPO/$ATTEMPTS/$STAGE-$CASE-run-$RUN-$(date +%s)
mkdir -p "$REPO/$ATTEMPTS"
mv "$RUN_DIR" "$DEST"
for f in $(state_files); do
  mv "$f" "$DEST/"
done
printf 'reason: %s\nlabel: targeted live check\n' "$FAIL_REASON" > "$DEST/reason.txt"
echo "failed attempt kept at ${DEST#"$REPO"/}"
echo 'BLOCK OK'
# END: fail
```

### revert `<case>`

```bash
# BLOCK: revert
set -euo pipefail
sidecar
cd "$CLONE"
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert — STOPPING'; exit 1; }
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT CASE — STOPPING'; exit 1; }
START_BRANCH=$(sed -n 's/^start_branch=//p' "$STATE_DIR/.b3-inprogress")
START_SHA=$(sed -n 's/^start_sha=//p' "$STATE_DIR/.b3-inprogress")
test -n "$START_BRANCH" && test -n "$START_SHA" || { echo 'SENTINEL INCOMPLETE — STOPPING'; exit 1; }
test -z "$(state_files)" \
  || { echo 'A RUN IS UNFINISHED (state file present) — post or fail it — STOPPING'; exit 1; }
if test -f "$CLONE/uv.lock"; then
  chflags nouchg "$CLONE/uv.lock"
  ! stat -f %Sf "$CLONE/uv.lock" | grep -q uchg || { echo 'uv.lock STILL PROTECTED — STOPPING'; exit 1; }
fi
git checkout -- .
# shellcheck disable=SC2086  # TOUCHED is a validated space-separated path list
git clean -fd -e .turingmind -- $TOUCHED
git switch -q "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN AFTER THE REVERT — STOPPING'; exit 1; }
if grep -qx 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then
  for f in "$PARK"/*.json; do test -e "$f" || continue; mv -n "$f" "$STATE_DIR/"; done
  if test -d "$PARK/format-53"; then
    for f in "$PARK"/format-53/*.json; do
      test -e "$f" || continue
      mkdir -p "$STATE53"; mv -n "$f" "$STATE53/"
    done
  fi
fi
if test -d "$PARK/format-53"; then rmdir "$PARK/format-53" 2> /dev/null || true; fi
test -z "$(find "$PARK" -mindepth 1)" || { echo 'PARKED FILES COULD NOT ALL BE RESTORED — STOPPING'; exit 1; }
rmdir "$PARK"
rm "$STATE_DIR/.b3-inprogress"
echo "$CASE complete — $CLONE back on $START_BRANCH@$START_SHA"
if command -v tmux > /dev/null && tmux has-session -t "=p54-$CASE" 2> /dev/null; then
  echo "tmux session p54-$CASE is still alive: /exit it, then tmux kill-session -t p54-$CASE"
fi
echo 'BLOCK OK'
# END: revert
```

---

## 8. Closing the window

### restore-memory

```bash
# BLOCK: restore-memory
set -euo pipefail
test -f "$MEMPARK_ENV" || { echo 'NO MEMORY PARK RECORD — nothing to restore — STOPPING'; exit 1; }
PARKDIR=$(sed -n 's/^PARKDIR=//p' "$MEMPARK_ENV")
test -n "$PARKDIR" && test -d "$PARKDIR" || { echo 'THE PARK DIR IS MISSING — STOPPING'; exit 1; }
for C in $CLONES; do
  test ! -e "$CLONES_ROOT/$C/.turingmind/state/.b3-inprogress" \
    || { echo "$CLONES_ROOT/$C IS STILL MID-CASE — revert it first — STOPPING"; exit 1; }
done
STAMP=$(date '+%Y%m%dT%H%M%S')
for C in $CLONES; do
  M=$(proj_dir "$CLONES_ROOT/$C")/memory
  if test -e "$M"; then
    mv "$M" "$PARKDIR/$C-written-during-window-$STAMP"
    echo "memory written during the window kept as evidence: $PARKDIR/$C-written-during-window-$STAMP"
  fi
  if test -e "$PARKDIR/$C"; then
    mv "$PARKDIR/$C" "$M"
    echo "restored $CLONES_ROOT/$C auto-memory"
  fi
done
rm "$MEMPARK_ENV"
echo 'BLOCK OK'
# END: restore-memory
```

The runner copy is isolated, and the owner's installed cache is never touched, so there is no
cache-restore step. The runner copy stays at `~/.b3/phase54-runner/` until the next `materialize`.

---

## Tally

```text
python3 docs/design/freeze-v2.12/tools/freeze_tally.py dev-tally \
  --runs-root docs/design/reachability-dev/runs-phase54-live --manifest "$MANIFEST"
```

The tally counts only runs whose stamps match the manifest. A stale or missing run makes it
refuse, and a non-zero exit means the tally is not a result. Alarms (critical/warning rows),
Needs-verification items and owner questions are reported separately and never summed (R13).

**Verdict rules (targeted live check — not release evidence):** as Phase 53
(`RUN-PHASE53-dev.md`, Tally).

- A should-quiet-shaped case **fires** iff alarms > 0 OR Needs-verification items > 0.
- A new-exposure case counts as a **catch** only when a `dev-catch-candidates` row identifies the
  keyed defect: its location AND its causal failure.
- A B3 catch case counts as a catch only when a `catch-candidates` row does the same against the
  B3 answer key.

## Lost catch rule

Any catch lost on the candidate is investigated and recorded in NOTES before the freeze. NOTES
records the cause, the rule involved and the decision. A lost catch is never closed by rerunning
until it lands, and never dismissed as model variability (D-27).
