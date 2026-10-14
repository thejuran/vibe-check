# Phase-53 development runbook — reachability rehearsal (one parameterized file)

**Label: development rehearsal — not release evidence (D-09).** Every archive, every notes line
and every tally this runbook produces carries that label. Release measurement is Phase 55: the
frozen candidate through B3 x3 and the sealed holdout x3. Nothing here is a release number, and
no run under `runs-phase53-dev/` is ever read by `score43.py aggregate`, `ledger` or the replay
census.

**Purpose:** live development runs of `/vibe-check:deep-review` while the Phase-53 rules change,
on (a) the owner-approved reachability cases (`docs/design/reachability-dev/README.md`, approval
record) and (b) the B3 cases each rule aims at, then one complete sweep on the finished candidate.
This is the Phase-49 method (`docs/design/b3-ground-truth/RUN-PHASE49-v2.11.md`) cut down to what a
rehearsal needs, with one change of substance: **the installed plugin cache is what runs** (no
`--plugin-dir`), so every run is bound to a content fingerprint of that cache.

---

## 1. Budget and order (D-08)

**Stage `targeted`** (fixes and generic rule rewordings allowed between runs), one run per case:

1. the approved reachability cases, both shapes: `reach-new-1`, `reach-new-2`,
   `reach-unchanged-1`, `reach-unchanged-2`;
2. the B3 cases the rules aim at: `should-quiet-4` (legacy value), `should-quiet-6` and
   `should-quiet-7` (staged value), plus the B3 catch cases whose keyed defect sits in a reused,
   unchanged helper (named in NOTES before the runs, from the B3 answer keys).

A case re-run after a fix uses the next run number (`run-2`, …); the failed attempt is kept under
`runs-phase53-dev/attempts/` (block `fail`).

**Stage `final`:** every id in `score43.DIFFS` AND every approved reachability case, once, all on
ONE fingerprint (`FINAL_FP`, see the Final candidate rule below).

## 2. Where things land

| What | Path |
|---|---|
| run archive | `docs/design/reachability-dev/runs-phase53-dev/<stage>/<case>/run-<n>/` (stage ∈ {targeted, final}) |
| failed attempts | `docs/design/reachability-dev/runs-phase53-dev/attempts/` |
| notes | `docs/design/reachability-dev/NOTES-phase53-dev.md` (opened by 53-14 with the label) |
| keyed sites (new-exposure cases) | `docs/design/reachability-dev/CATCH-SITES-dev.json` |
| fingerprints | `~/.b3/phase53-dev.env` (`CACHE_FP`, `CACHE_PATH`, `FINAL_FP`, `FINAL_HEAD`) |

`runs-phase53-dev/` sits outside every `docs/design/b3-ground-truth/runs-*` measurement root; no
block here writes anything under `docs/design/b3-ground-truth/`.

Each run directory holds `state.json`, `lanes.json` (and the other `lanearchive.py extract`
outputs) when produced, `tree.diff`, `clear.txt`, `transcript.jsonl.sha256` and `fingerprint.txt`:

```text
runtime_fingerprint: <64 hex — score43.py fingerprint over the INSTALLED cache>
repo_head: <40 hex>
repo_dirty: yes|no            (uncommitted changes under plugins/vibe-check)
stage: targeted|final
label: development rehearsal
```

`transcript.jsonl` is copied into the run directory for `dev-tally`'s card count and is gitignored
(it carries the owner's private instructions); only its sha is committed. The blocks never commit:
53-14 commits NOTES + archives in its own scoped commits.

## 3. Driver rule (D-13, as Phase 49)

Assistant-driven via tmux, `--permission-mode manual`. Each measured session is a separate
`claude` process in tmux session `p53-<case>`. Pane text is read only to detect prompts. The
fixed keystroke set is all the driver ever sends: the launch line, `/clear`,
`/vibe-check:deep-review`, on the "Pass N" card the number of the line labelled exactly
`Stop here…`, on the "Stop here" card the number of the line labelled exactly `Abandon` (BY
LABEL, never by position), `/exit`. The owner answers no cards. An unexpected card, prompt or
permission request = STOP and report. Typed attestations go to the blocks' stdin, never to the
session. The owner keeps the laptop lid OPEN.

## 4. How to run a block

Blocks cannot be pasted into zsh. `~/.b3/b3` is hard-wired to `RUN-CHECKLIST-v2.10.md` and cannot
run this file; use `p53`, defined ONCE per bash shell (from the assistant's Bash tool, which runs
zsh, wrap every call in `bash -s <<'BASH' … BASH` with this definition at the top). `p53` pulls
`common` plus one named block out of this file into `~/.b3/p53.sh` and runs it under bash:

```text
P53=~/turingmind-code-review/docs/design/reachability-dev/RUN-PHASE53-dev.md
p53() {
  mkdir -p ~/.b3
  { awk '$0=="# BLOCK: common"{f=1} f{print} $0=="# END: common"{exit}' "$P53"
    awk -v b="$1" '$0=="# BLOCK: "b{f=1} f{print} $0=="# END: "b{exit}' "$P53"; } > ~/.b3/p53.sh
  grep -qx '# END: common' ~/.b3/p53.sh || { echo "p53: the common block is missing"; return 2; }
  tail -1 ~/.b3/p53.sh | grep -qx "# END: $1" || { echo "p53: no block named '$1'"; return 2; }
  STAGE="${STAGE:-}" CASE="${2:-}" RUN="${3:-}" bash ~/.b3/p53.sh \
    && echo "p53: BLOCK OK ($1)" || { echo "p53: BLOCK FAILED ($1)"; return 1; }
}
```

Usage: `STAGE=targeted p53 <block> [case] [run]`, e.g. `STAGE=targeted p53 fresh reach-new-1`,
`printf 'CLEARED\n' | STAGE=targeted p53 pre reach-new-1 1`. `STAGE` is required for every block.

### The order

| # | what | notes |
|---|---|---|
| 1 | `p53 park-memory` | N-02, all three clones |
| 2 | `p53 resync-cache` | installed cache := candidate tree, compared by content hash |
| 3 | RELAUNCH | quit every Claude Code process; measured sessions are new processes |
| 4 | `p53 fingerprint` | `CACHE_FP == TREE_FP`; in stage `final` records `FINAL_FP` |
| 5 | `p53 preflight <case>` | cache fingerprint unchanged, pins, memory parked, patch applies |
| 6 | `p53 fresh <case>` | clone at base_sha + case patch, tree-diff sha checked |
| 7 | `LAUNCH_VIA_TMUX=1 p53 launch <case>` | tmux session `p53-<case>` |
| 8 | `/clear` in the session, then `printf 'CLEARED\n' \| p53 pre <case> <n>` | |
| 9 | `/vibe-check:deep-review`; `Stop here…` then `Abandon` (by label) | |
| 10 | `p53 post <case> <n>` | archive + fingerprint.txt + burden + catch listing into NOTES |
| 11 | `/exit`, `tmux kill-session -t p53-<case>`, `p53 revert <case>` | |
| 12 | after the last case: `p53 restore-memory`, `p53 restore-cache`, RELAUNCH | |

A run that crashes, stalls or is refused by `post`: `p53 fail <case> <n>` (moves the partial run
to `attempts/`), then redo from step 8 with the next run number. After ANY change under
`plugins/vibe-check/`: `resync-cache`, RELAUNCH, `fingerprint`, and rerun the affected cases from
`preflight` — in stage `final` that is the Final candidate rule.

---

## 5. The shared block

```bash
# BLOCK: common
set -euo pipefail
export LC_ALL=C
REPO=$HOME/turingmind-code-review
RD=docs/design/reachability-dev
DD=docs/design/b3-ground-truth
PLUGIN_ROOT=$REPO/plugins/vibe-check
SCRIPTS=$PLUGIN_ROOT/scripts
SCORE43=$SCRIPTS/score43.py
NOTES=$RD/NOTES-phase53-dev.md
SITES=$RD/CATCH-SITES-dev.json
DEV_SEAL=917bde2
ENV=$HOME/.b3/phase53-dev.env
MEMPARK_ENV=$HOME/.b3/phase53-dev-memory-park.env
CACHE_BAK=$HOME/.b3/vibe-check-cache-bak-pre-phase53-dev
CLONES='roonseek seedsyncarr triggarr'
REHEARSAL_LABEL='development rehearsal — not release evidence'
mkdir -p "$HOME/.b3"
case "${STAGE:-}" in targeted|final) ;;
  *) echo 'STAGE MUST BE targeted OR final — STOPPING'; exit 1 ;; esac
ARCHIVE=$RD/runs-phase53-dev/$STAGE
ATTEMPTS=$RD/runs-phase53-dev/attempts
CASE=${CASE:-}
RUN=${RUN:-}
TIMEOUT_BIN=$(command -v timeout || command -v gtimeout || true)

# the ~/.b3 env file: plain KEY=VALUE lines, read with sed, never sourced
env_get() { if test -f "$ENV"; then sed -n "s/^$1=//p" "$ENV" | tail -1; fi; }
env_set() {
  local tmp
  tmp=$(mktemp "$HOME/.b3/p53-env.XXXXXX")
  { if test -f "$ENV"; then grep -v "^$1=" "$ENV" || true; fi; printf '%s=%s\n' "$1" "$2"; } > "$tmp"
  mv "$tmp" "$ENV"
}

# the installed vibe-check@thejuran cache dir, from Claude Code's own registry (never a typed version)
resolve_cache() {
  CACHE=$(python3 -c '
import json, os, sys
d = json.load(open(os.path.expanduser("~/.claude/plugins/installed_plugins.json")))
d = d.get("plugins", d)
paths = [e.get("installPath") for e in d.get("vibe-check@thejuran") or []
         if isinstance(e, dict) and e.get("installPath")]
if len(paths) != 1:
    sys.exit("expected one vibe-check@thejuran install, found %d" % len(paths))
print(paths[0])') || { echo 'CANNOT RESOLVE THE INSTALLED vibe-check@thejuran CACHE — STOPPING'; exit 1; }
  test -d "$CACHE" || { echo "THE REGISTERED CACHE DIR IS MISSING: claude plugin uninstall vibe-check@thejuran && claude plugin install vibe-check@thejuran, RELAUNCH, then resync-cache — STOPPING"; exit 1; }
}

# sha256 over the runtime roots' file contents (score43.py fingerprint; caches and .in_use excluded)
rfp() { python3 "$SCORE43" fingerprint --root "$1"; }

# the case allowlist: the README approval record (committed) plus score43.DIFFS — never retyped
check_case() {
  local dev_ids b3_ids
  printf '%s' "$CASE" | grep -qE '^[a-z0-9-]+$' || { echo 'CASE MUST BE A CASE ID — STOPPING'; exit 1; }
  dev_ids=$(git -C "$REPO" show "HEAD:$RD/README.md" | grep -A1 '^\*\*Approved ids' \
    | grep -oE 'reach-(new|unchanged)-[0-9]+' | sort -u | tr '\n' ' ') \
    || { echo 'THE README APPROVAL RECORD LISTS NO APPROVED IDS — STOPPING'; exit 1; }
  b3_ids=$(python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import score43; print(" ".join(score43.DIFFS))' "$SCRIPTS")
  case " $dev_ids " in
    *" $CASE "*) KIND=dev ;;
    *) case " $b3_ids " in
         *" $CASE "*) KIND=b3 ;;
         *) echo "CASE $CASE IS NEITHER AN APPROVED DEVELOPMENT CASE NOR AN ID IN score43.DIFFS — STOPPING"; exit 1 ;;
       esac ;;
  esac
}
check_run() {
  case "$RUN" in [1-9]) ;; *) echo 'RUN MUST BE 1-9 — STOPPING'; exit 1 ;; esac
}

# the case files from the COMMITTED blobs (seal-gated), and every per-case constant read from them
sidecar() {
  local p e s key prov
  check_case
  if test "$KIND" = dev; then
    p=$RD/cases/$CASE
    for e in patch provenance; do
      test "$(git -C "$REPO" rev-parse "$DEV_SEAL:$p.$e")" = "$(git -C "$REPO" rev-parse "HEAD:$p.$e")" \
        || { echo "CASE FILE $CASE.$e IS NOT BLOB-EQUAL TO THE APPROVAL COMMIT $DEV_SEAL — STOPPING"; exit 1; }
    done
    case "$CASE" in reach-new-*) ROLE=catch ;; *) ROLE=quiet ;; esac
  else
    p=$DD/diffs/$CASE
    case "$CASE" in
      triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3)
        for e in patch provenance; do
          test "$(git -C "$REPO" rev-parse "v2.9:$p.$e")" = "$(git -C "$REPO" rev-parse "HEAD:$p.$e")" \
            || { echo "SIDECAR SEAL BROKEN ($CASE.$e IS NOT BLOB-EQUAL TO TAG v2.9) — STOPPING"; exit 1; }
        done ;;
      *)
        key=$(git -C "$REPO" show "5f687d9:$DD/ANSWER-KEY-v2.10.md")
        for e in patch provenance; do
          s=$(git -C "$REPO" show "HEAD:$p.$e" | shasum -a 256 | awk '{print $1}')
          printf '%s\n' "$key" | grep -qxF "sha256(diffs/$CASE.$e) = $s" \
            || { echo "SIDECAR SEAL BROKEN ($CASE.$e sha256 IS NOT IN KEY BLOB 5f687d9) — STOPPING"; exit 1; }
        done ;;
    esac
    ROLE=$(python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import score43; print(score43.ROLE[sys.argv[2]])' "$SCRIPTS" "$CASE")
  fi
  git -C "$REPO" diff --quiet HEAD -- "$p.patch" "$p.provenance" \
    || { echo 'CASE FILES HAVE UNCOMMITTED CHANGES — STOPPING'; exit 1; }
  prov=$(git -C "$REPO" show "HEAD:$p.provenance")
  for e in base_sha EXPECTED_TREE_DIFF_SHA256 EXPECTED_TOUCHED_PATHS source_repo; do
    test "$(printf '%s\n' "$prov" | grep -c "^$e: ")" = "1" \
      || { echo "PROVENANCE KEY $e NOT EXACTLY ONCE — STOPPING"; exit 1; }
  done
  BASE_SHA=$(printf '%s\n' "$prov" | sed -n 's/^base_sha: //p' | tr -d '[:space:]')
  EXPECTED_SHA=$(printf '%s\n' "$prov" | sed -n 's/^EXPECTED_TREE_DIFF_SHA256: //p' | tr -d '[:space:]')
  TOUCHED=$(printf '%s\n' "$prov" | sed -n 's/^EXPECTED_TOUCHED_PATHS: //p' | sed 's/[[:space:]]*$//')
  SRC=$(printf '%s\n' "$prov" | sed -n 's/^source_repo: //p' | sed 's/[[:space:]]*$//')
  printf '%s' "$BASE_SHA" | grep -qE '^[0-9a-f]{40}$' || { echo 'base_sha IS NOT 40-HEX — STOPPING'; exit 1; }
  printf '%s' "$EXPECTED_SHA" | grep -qE '^[0-9a-f]{64}$' \
    || { echo 'EXPECTED_TREE_DIFF_SHA256 IS NOT 64-HEX — STOPPING'; exit 1; }
  printf '%s' "$TOUCHED" | grep -qE '^[A-Za-z0-9._/-]+( [A-Za-z0-9._/-]+)*$' \
    || { echo 'EXPECTED_TOUCHED_PATHS IS NOT A SPACE-SEPARATED PATH LIST — STOPPING'; exit 1; }
  case "$SRC" in
    '~/triggarr') CN=triggarr ;;
    '~/seedsyncarr') CN=seedsyncarr ;;
    '~/roonseek') CN=roonseek ;;
    *) echo 'source_repo IS NOT ONE OF THE THREE CLONES — STOPPING'; exit 1 ;;
  esac
  CLONE=$HOME/$CN
  STATE_DIR=$CLONE/.turingmind/state
  PARK=$STATE_DIR/.b3-parked-phase53-dev
  PROJ=$(proj_dir "$CLONE")
  MEM=$PROJ/memory
  PATCH_FILE=$HOME/.b3/p53-$CASE.patch
  git -C "$REPO" show "HEAD:$p.patch" > "$PATCH_FILE"
  RP=$ARCHIVE/$CASE/run-${RUN:-0}
  RUN_DIR=$REPO/$RP
}

# the memory dir and transcript dir Claude Code keeps for a clone path
proj_dir() { printf '%s/.claude/projects/%s' "$HOME" "$(printf '%s' "$1" | sed 's/[^A-Za-z0-9]/-/g')"; }

# N-02 — clone auto-memory a session re-created after park-memory is moved aside as evidence
mem_evidence() {
  test -e "$MEM" || return 0
  test -f "$MEMPARK_ENV" || { echo "AUTO-MEMORY FOR $CLONE IS NOT PARKED (run p53 park-memory) — STOPPING"; exit 1; }
  local pd ev
  pd=$(sed -n 's/^PARKDIR=//p' "$MEMPARK_ENV")
  test -n "$pd" && test -d "$pd" || { echo 'THE MEMORY PARK DIR IS MISSING — STOPPING'; exit 1; }
  ev=$pd/$CN-written-before-$STAGE-${CASE:-window}-$1-$(date +%s)
  mv "$MEM" "$ev"
  echo "auto-memory re-created by a session moved aside to $ev (evidence, never merged back)"
}

# the full tracked diff of the clone, as one sha256
clone_diff_sha() { git -C "$CLONE" diff | shasum -a 256 | awk '{print $1}'; }

# the cache that runs is still the fingerprinted one (and, in stage final, the final one)
cache_unchanged() {
  local now want
  resolve_cache
  want=$(env_get CACHE_FP)
  test -n "$want" || { echo 'NO RECORDED CACHE_FP — run p53 fingerprint — STOPPING'; exit 1; }
  test "$(env_get CACHE_PATH)" = "$CACHE" \
    || { echo 'THE REGISTERED CACHE DIR CHANGED SINCE fingerprint — STOPPING'; exit 1; }
  now=$(rfp "$CACHE")
  test "$now" = "$want" \
    || { echo "INSTALLED CACHE FINGERPRINT CHANGED ($now != recorded $want) — $1 — STOPPING"; exit 1; }
  if test "$STAGE" = final; then
    test "$now" = "$(env_get FINAL_FP)" \
      || { echo "CACHE FINGERPRINT != FINAL_FP — apply the Final candidate rule — $1 — STOPPING"; exit 1; }
  fi
  FP_NOW=$now
}
# END: common
```

---

## 6. Opening the window

### park-memory (N-02)

```bash
# BLOCK: park-memory
set -euo pipefail
test ! -e "$MEMPARK_ENV" \
  || { echo 'MEMORY IS ALREADY PARKED (phase53-dev-memory-park.env) — STOPPING'; exit 1; }
PARKDIR=$HOME/.b3/automemory-parked-phase53-dev-$STAGE-$(date +%s)
mkdir -p "$PARKDIR"
for C in $CLONES; do
  M=$(proj_dir "$HOME/$C")/memory
  if test -e "$M"; then
    mv "$M" "$PARKDIR/$C"
    echo "parked ~/$C auto-memory -> $PARKDIR/$C"
  else
    echo "~/$C has no auto-memory to park"
  fi
  test ! -e "$M" || { echo "~/$C AUTO-MEMORY STILL PRESENT — STOPPING"; exit 1; }
done
printf 'PARKDIR=%s\n' "$PARKDIR" > "$MEMPARK_ENV"
echo 'BLOCK OK'
# END: park-memory
```

### resync-cache

The installed cache is made content-identical to the candidate tree (`plugins/vibe-check/` in this
repo, committed or not). Parity is the `score43.py fingerprint` value over the runtime roots on
both sides — **a version string is never compared** (the candidate and the stale release can
carry the same version). The thejuran marketplace installs from GitHub `main`, so `claude plugin
uninstall` + `install` would bring back the released build, not the candidate; it is used only to
re-materialize a missing registered cache dir (see `resolve_cache`). The candidate is copied in
with `rsync` (the Phase-49 method), after a one-time backup that `restore-cache` puts back.

```bash
# BLOCK: resync-cache
set -euo pipefail
resolve_cache
TREE_FP=$(rfp "$PLUGIN_ROOT")
CACHE_FP=$(rfp "$CACHE")
if test "$CACHE_FP" = "$TREE_FP"; then
  echo "installed cache already at content parity with the candidate tree"
else
  if test -e "$CACHE_BAK"; then
    test "$(cat "$CACHE_BAK.path")" = "$CACHE" \
      || { echo 'THE EXISTING CACHE BACKUP IS FOR ANOTHER CACHE DIR — STOPPING'; exit 1; }
    echo "keeping the existing released-cache backup $CACHE_BAK"
  else
    cp -Rp "$CACHE" "$CACHE_BAK"
    printf '%s\n' "$CACHE" > "$CACHE_BAK.path"
    diff -rq -x .in_use "$CACHE" "$CACHE_BAK" > /dev/null \
      || { echo 'CACHE BACKUP DIFFERS FROM THE CACHE — STOPPING'; exit 1; }
    echo "released cache backed up to $CACHE_BAK"
  fi
  rsync -a --delete --exclude .in_use --exclude __pycache__ --exclude '*.pyc' \
    --exclude .pytest_cache --exclude .planning "$PLUGIN_ROOT/" "$CACHE/"
  chmod -R u+w "$CACHE"
  CACHE_FP=$(rfp "$CACHE")
  test "$CACHE_FP" = "$TREE_FP" || { echo 'CACHE NOT AT CONTENT PARITY AFTER RSYNC — STOPPING'; exit 1; }
fi
echo "content parity over the runtime roots: cache $CACHE_FP == tree $TREE_FP"
echo "cache dir: $CACHE (resolved from installed_plugins.json; a version string is never compared)"
echo 'RELAUNCH CLAUDE CODE (FULL PROCESS EXIT) BEFORE fingerprint — sessions load the cache at start'
echo 'BLOCK OK'
# END: resync-cache
```

### fingerprint

Records `CACHE_FP` (the installed cache that will run) after asserting it equals `TREE_FP` (the
candidate tree). In stage `final` it also records `FINAL_FP` + `FINAL_HEAD` — once. A second
`final` fingerprint on a changed candidate STOPS; `RESET_FINAL=1` is the explicit "restart the
sweep" act (the Final candidate rule below): it refuses while `runs-phase53-dev/final/` still exists and
prints the old value so NOTES can record the invalidation.

```bash
# BLOCK: fingerprint
set -euo pipefail
resolve_cache
CACHE_FP=$(python3 "$PLUGIN_ROOT/scripts/score43.py" fingerprint --root "$CACHE")
TREE_FP=$(python3 "$PLUGIN_ROOT/scripts/score43.py" fingerprint --root "$PLUGIN_ROOT")
test "$CACHE_FP" = "$TREE_FP" \
  || { echo "CACHE_FP $CACHE_FP != TREE_FP $TREE_FP — run p53 resync-cache and RELAUNCH — STOPPING"; exit 1; }
if test "$STAGE" = final; then
  test -z "$(git -C "$REPO" status --porcelain -- plugins/vibe-check)" \
    || { echo 'THE FINAL CANDIDATE MUST BE COMMITTED (plugins/vibe-check has changes) — STOPPING'; exit 1; }
  OLD=$(env_get FINAL_FP)
  if test -z "$OLD"; then
    env_set FINAL_FP "$CACHE_FP"
    env_set FINAL_HEAD "$(git -C "$REPO" rev-parse HEAD)"
    echo "FINAL_FP recorded: $CACHE_FP at $(git -C "$REPO" rev-parse HEAD)"
  elif test "${RESET_FINAL:-0}" = 1; then
    test ! -e "$REPO/$ARCHIVE" \
      || { echo "MOVE $ARCHIVE TO $ATTEMPTS/final-${OLD:0:12}/ BEFORE A RESET — STOPPING"; exit 1; }
    echo "FINAL_FP RESET: old $OLD (head $(env_get FINAL_HEAD)) is invalidated — record it in NOTES"
    env_set FINAL_FP "$CACHE_FP"
    env_set FINAL_HEAD "$(git -C "$REPO" rev-parse HEAD)"
    echo "FINAL_FP recorded: $CACHE_FP at $(git -C "$REPO" rev-parse HEAD)"
  elif test "$OLD" != "$CACHE_FP"; then
    echo "THE CANDIDATE CHANGED SINCE FINAL_FP $OLD — apply the Final candidate rule (move final/, RESET_FINAL=1) — STOPPING"
    exit 1
  else
    echo "FINAL_FP unchanged: $OLD"
  fi
fi
env_set CACHE_FP "$CACHE_FP"
env_set CACHE_PATH "$CACHE"
echo "fingerprint: $CACHE_FP"
echo 'BLOCK OK'
# END: fingerprint
```

### preflight `[case]`

Re-run at the start of every case and every sitting. NOTES must carry the harness pins
(`pin-claude-code: <claude --version>`, `pin-codex: <codex --version>`, `pin-model: <model id>`);
the block prints the current values when a pin is missing.

```bash
# BLOCK: preflight
set -euo pipefail
cache_unchanged 'resync, RELAUNCH and fingerprint again'
TREE_FP=$(rfp "$PLUGIN_ROOT")
test "$TREE_FP" = "$FP_NOW" \
  || { echo 'THE CANDIDATE TREE CHANGED SINCE resync-cache — resync, RELAUNCH, fingerprint — STOPPING'; exit 1; }
test -z "$(git -C "$REPO" status --porcelain -- "$DD")" \
  || { echo 'docs/design/b3-ground-truth HAS CHANGES — the dev path never writes there — STOPPING'; exit 1; }
test -f "$REPO/$NOTES" || { echo "NOTES FILE $NOTES MISSING — open it first (53-14) — STOPPING"; exit 1; }
pin() { sed -n "s/^$1: //p" "$REPO/$NOTES" | tail -1; }
CC=$(claude --version) || { echo 'claude --version FAILED — STOPPING'; exit 1; }
CX=$(codex --version) || { echo 'codex --version FAILED — STOPPING'; exit 1; }
if test -z "$(pin pin-claude-code)" || test -z "$(pin pin-codex)" || test -z "$(pin pin-model)"; then
  echo "add to NOTES: pin-claude-code: $CC"
  echo "add to NOTES: pin-codex: $CX"
  echo 'add to NOTES: pin-model: <the model id every measured session is launched with>'
  echo 'HARNESS PINS NOT RECORDED — STOPPING'; exit 1
fi
test "$CC" = "$(pin pin-claude-code)" || { echo "HARNESS DRIFT — claude-code '$CC' — STOPPING"; exit 1; }
test "$CX" = "$(pin pin-codex)" || { echo "HARNESS DRIFT — codex '$CX' — STOPPING"; exit 1; }
test -n "$TIMEOUT_BIN" || { echo 'NO timeout/gtimeout ON PATH (Codex watchdog) — STOPPING'; exit 1; }
test -f "$MEMPARK_ENV" || { echo 'MEMORY NOT PARKED — run p53 park-memory — STOPPING'; exit 1; }
for C in $CLONES; do
  test ! -e "$(proj_dir "$HOME/$C")/memory" \
    || { echo "~/$C AUTO-MEMORY IS PRESENT — run p53 park-memory / see mem_evidence — STOPPING"; exit 1; }
done
if test -n "$CASE"; then
  sidecar
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
    WT=$HOME/.b3/p53-applycheck-$CASE
    test ! -e "$WT" || { echo "STALE CHECK WORKTREE $WT — git -C $CLONE worktree remove --force $WT — STOPPING"; exit 1; }
    git -C "$CLONE" worktree add -q --detach "$WT" "$BASE_SHA"
    OK=1; git -C "$WT" apply --check "$PATCH_FILE" || OK=0
    git -C "$CLONE" worktree remove --force "$WT"
    test "$OK" = 1 || { echo 'PATCH DOES NOT APPLY AT base_sha — STOPPING'; exit 1; }
  fi
  echo "case: $CASE ($KIND, $ROLE) in $CLONE at base $BASE_SHA"
fi
echo "stage: $STAGE — $REHEARSAL_LABEL"
echo "cache fingerprint: $FP_NOW"
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
cache_unchanged 'nothing prepared'
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

No `--plugin-dir`: the session loads the installed cache, which is what the fingerprint covers.
The model comes from NOTES `pin-model:` and is single-quoted (zsh globs a bare `[1m]`).

```bash
# BLOCK: launch
set -euo pipefail
sidecar
cache_unchanged 'not launched'
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" 2> /dev/null \
  || { echo "CLONE NOT PREPARED — run p53 fresh $CASE first — STOPPING"; exit 1; }
mem_evidence launch
test ! -e "$MEM" || { echo "AUTO-MEMORY FOR $CLONE IS NOT PARKED — STOPPING"; exit 1; }
MODEL=$(sed -n 's/^pin-model: //p' "$REPO/$NOTES" | tail -1)
printf '%s' "$MODEL" | grep -qE '^[A-Za-z0-9._-]+(\[1m\])?$' \
  || { echo 'NOTES pin-model: IS MISSING OR NOT A MODEL ID — STOPPING'; exit 1; }
if command -v tmux > /dev/null && tmux has-session -t "=p53-$CASE" 2> /dev/null; then
  echo "TMUX SESSION p53-$CASE STILL EXISTS — /exit it and kill it — STOPPING"; exit 1
fi
LAUNCH_LINE="claude --permission-mode manual --model '$MODEL' --allowedTools \"Bash,Read,Write,Edit,Grep,Glob,Task,Agent\""
echo "Paste form:  cd $CLONE && $LAUNCH_LINE"
if test "${LAUNCH_VIA_TMUX:-0}" = 1; then
  command -v tmux > /dev/null || { echo 'tmux NOT INSTALLED — STOPPING'; exit 1; }
  tmux new-session -d -s "p53-$CASE" -c "$CLONE"
  tmux send-keys -t "p53-$CASE" "$LAUNCH_LINE" Enter
  echo "launched in tmux session p53-$CASE (read it with: tmux capture-pane -p -t p53-$CASE)"
fi
echo "Next: /clear in the session, then printf 'CLEARED\\n' | STAGE=$STAGE p53 pre $CASE <n>"
echo 'BLOCK OK'
# END: launch
```

### pre `<case> <n>`

Reads the typed `CLEARED` attestation from stdin AFTER `/clear` completed and writes the run's
`clear.txt` (its mtime is the run's start marker for `post`).

```bash
# BLOCK: pre
set -euo pipefail
check_run
sidecar
cache_unchanged 'run not started'
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" 2> /dev/null \
  || { echo 'CLONE NOT PREPARED FOR THIS CASE — STOPPING'; exit 1; }
test ! -e "$RUN_DIR" || { echo "$RP ALREADY EXISTS — use the next run number or p53 fail — STOPPING"; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo 'A STATE FILE IS ALREADY PRESENT (an unfinished run) — p53 fail — STOPPING'; exit 1; }
mem_evidence pre
read -r ATT || true
test "${ATT:-}" = CLEARED || { echo 'NO CLEARED ATTESTATION ON STDIN — STOPPING'; exit 1; }
mkdir -p "$RUN_DIR"
date -u '+%Y-%m-%dT%H:%M:%S+0000 CLEARED' > "$RUN_DIR/clear.txt"
echo "run $RP open — now /vibe-check:deep-review in the session"
echo 'BLOCK OK'
# END: pre
```

### post `<case> <n>`

Every check that can refuse runs before anything is written to NOTES. The cache fingerprint is
recomputed FIRST: when it differs from the value `fingerprint`/`preflight` recorded (or, in stage
`final`, from `FINAL_FP`), nothing is archived — `p53 fail` the run and rerun it on the current
build.

```bash
# BLOCK: post
set -euo pipefail
check_run
sidecar
cache_unchanged 'NOTHING ARCHIVED — p53 fail this run'
cd "$CLONE"
grep -qx "diff_id=$CASE" "$STATE_DIR/.b3-inprogress" 2> /dev/null \
  || { echo 'CLONE NOT PREPARED FOR THIS CASE — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "$BASE_SHA" || { echo 'HEAD MOVED DURING THE RUN — p53 fail — STOPPING'; exit 1; }
test -f "$RUN_DIR/clear.txt" || { echo 'clear.txt MISSING (pre never ran) — STOPPING'; exit 1; }
test ! -e "$RUN_DIR/state.json" || { echo "$RP IS ALREADY ARCHIVED — STOPPING"; exit 1; }
NEW=$(find "$STATE_DIR" -maxdepth 1 -name '*.json' -newer "$RUN_DIR/clear.txt")
test "$(printf '%s\n' "$NEW" | grep -c .)" = "1" \
  || { echo 'EXPECTED EXACTLY ONE NEW STATE FILE — p53 fail — STOPPING'; exit 1; }
test "$(find "$STATE_DIR" -maxdepth 1 -name '*.json' | grep -c .)" = "1" \
  || { echo 'AN OLDER STATE FILE IS PRESENT — STOPPING'; exit 1; }
cp "$NEW" "$RUN_DIR/state.json"
python3 - "$RUN_DIR/state.json" "$BASE_SHA" <<'PY' || { echo 'NOT ONE ISOLATED PASS AT THE PINNED HEAD — p53 fail — STOPPING'; exit 1; }
import json, sys
s = json.load(open(sys.argv[1]))
assert len(s["passes"]) == 1, "passes=%d" % len(s["passes"])
assert s["passes"][-1]["head_sha"] == sys.argv[2], "head mismatch"
print("OK one isolated pass at", sys.argv[2])
PY
git diff > "$RUN_DIR/tree.diff"
test "$(shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}')" = "$EXPECTED_SHA" \
  || { echo 'FULL WORKTREE DIFF != THE CASE DIFF — p53 fail — STOPPING'; exit 1; }
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
  || { echo 'THE TRANSCRIPT NEVER NAMES THE INSTALLED CACHE — not the fingerprinted build — STOPPING'; exit 1; }
! grep -qF "$PLUGIN_ROOT" "$RUN_DIR/transcript.jsonl" \
  || { echo 'THE RUN LOADED THE REPO PLUGIN TREE, NOT THE INSTALLED CACHE — p53 fail — STOPPING'; exit 1; }
shasum -a 256 "$RUN_DIR/transcript.jsonl" | awk '{print $1}' > "$RUN_DIR/transcript.jsonl.sha256"
# lane archive (lanes.json when produced) with its own privacy scan; matched text is never printed
python3 "$SCRIPTS/lanearchive.py" extract --transcript "$RUN_DIR/transcript.jsonl" \
    --state "$RUN_DIR/state.json" --out-dir "$RUN_DIR" 2> "$HOME/.b3/p53-lanearchive.err" \
  || { tail -1 "$HOME/.b3/p53-lanearchive.err" | cut -c1-80; echo 'LANE ARCHIVE REFUSED OR FAILED — STOPPING'; exit 1; }
# the binding of this run to the build that produced it
if test -z "$(git -C "$REPO" status --porcelain -- plugins/vibe-check)"; then DIRTY=no; else DIRTY=yes; fi
printf 'runtime_fingerprint: %s\nrepo_head: %s\nrepo_dirty: %s\nstage: %s\nlabel: development rehearsal\n' \
  "$FP_NOW" "$(git -C "$REPO" rev-parse HEAD)" "$DIRTY" "$STAGE" > "$RUN_DIR/fingerprint.txt"
# burden (R13) and, for a catch-role case, the listing for the hand AXIS call
REC=$HOME/.b3/p53-notes-record.md
{
  echo ''
  echo "### $STAGE/$CASE/run-$RUN — $REHEARSAL_LABEL"
  echo ''
  echo "fingerprint: $FP_NOW"
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
SCAN="$REC $RUN_DIR/state.json $RUN_DIR/tree.diff $RUN_DIR/fingerprint.txt"
python3 "$SCRIPTS/lanearchive.py" scan $SCAN 2> "$HOME/.b3/p53-scan.err" \
  || { tail -1 "$HOME/.b3/p53-scan.err" | cut -c1-80; echo 'PRIVACY SCAN REFUSED — NOTHING APPENDED — STOPPING'; exit 1; }
cat "$REC" >> "$REPO/$NOTES"
rm -f "$NEW"
cat "$REC"
echo ''
echo "archived $RP — fill in the AXIS line in NOTES by hand for a catch-role case"
echo 'BLOCK OK'
# END: post
```

### fail `<case> <n>`

A crashed, stalled or refused run is moved — never deleted — to
`runs-phase53-dev/attempts/<stage>-<case>-run-<n>-<epoch>/` together with any state file it wrote,
so the slot can be redone from `pre` with the next run number. `FAIL_REASON` (letters, digits,
spaces and `.,:-` only) is recorded in `reason.txt`.

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
for f in "$STATE_DIR"/*.json; do
  test -e "$f" || continue
  mv "$f" "$DEST/"
done
printf 'reason: %s\nlabel: development rehearsal\n' "$FAIL_REASON" > "$DEST/reason.txt"
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
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo 'A RUN IS UNFINISHED (state file present) — p53 post or p53 fail — STOPPING'; exit 1; }
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
  for f in "$PARK"/*.json; do mv -n "$f" "$STATE_DIR/"; done
fi
test -z "$(find "$PARK" -mindepth 1)" || { echo 'PARKED FILES COULD NOT ALL BE RESTORED — STOPPING'; exit 1; }
rmdir "$PARK"
rm "$STATE_DIR/.b3-inprogress"
echo "$CASE complete — $CLONE back on $START_BRANCH@$START_SHA"
if command -v tmux > /dev/null && tmux has-session -t "=p53-$CASE" 2> /dev/null; then
  echo "tmux session p53-$CASE is still alive: /exit it, then tmux kill-session -t p53-$CASE"
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
  test ! -e "$HOME/$C/.turingmind/state/.b3-inprogress" \
    || { echo "~/$C IS STILL MID-CASE — p53 revert it first — STOPPING"; exit 1; }
done
STAMP=$(date '+%Y%m%dT%H%M%S')
for C in $CLONES; do
  M=$(proj_dir "$HOME/$C")/memory
  if test -e "$M"; then
    mv "$M" "$PARKDIR/$C-written-during-window-$STAMP"
    echo "memory written during the window kept as evidence: $PARKDIR/$C-written-during-window-$STAMP"
  fi
  if test -e "$PARKDIR/$C"; then
    mv "$PARKDIR/$C" "$M"
    echo "restored ~/$C auto-memory"
  fi
done
rm "$MEMPARK_ENV"
echo 'BLOCK OK'
# END: restore-memory
```

### restore-cache (optional)

Puts the released build back in the installed cache dir. Run it when the development window
closes; skip it between the targeted and final stages.

```bash
# BLOCK: restore-cache
set -euo pipefail
test -d "$CACHE_BAK" || { echo 'NO CACHE BACKUP — nothing to restore — STOPPING'; exit 1; }
CACHE=$(cat "$CACHE_BAK.path")
test -d "$CACHE" || { echo "THE BACKED-UP CACHE DIR $CACHE IS GONE — STOPPING"; exit 1; }
rsync -a --delete --exclude .in_use "$CACHE_BAK/" "$CACHE/"
test -z "$(diff -rq -x .in_use "$CACHE" "$CACHE_BAK" || true)" \
  || { echo 'THE RESTORED CACHE DIFFERS FROM THE BACKUP — backup kept — STOPPING'; exit 1; }
rm -rf "$CACHE_BAK" "$CACHE_BAK.path"
echo "restored the released build into $CACHE (fingerprint $(rfp "$CACHE"))"
echo 'RELAUNCH CLAUDE CODE (FULL PROCESS EXIT) so everyday sessions load the restored cache'
echo 'BLOCK OK'
# END: restore-cache
```

---

## Tally

Targeted stage (development progress; several fingerprints are expected and listed):

```text
python3 plugins/vibe-check/scripts/score43.py dev-tally \
  --runs-root docs/design/reachability-dev/runs-phase53-dev/targeted
```

Final stage (the numbers 53-14 reports; every run must come from `FINAL_FP`):

```text
python3 plugins/vibe-check/scripts/score43.py dev-tally \
  --runs-root docs/design/reachability-dev/runs-phase53-dev/final --require-fingerprint "$FINAL_FP"
```

`--require-fingerprint` exits 1 on any `stale` run (a `fingerprint.txt` missing or naming another
build) or any `missing` run (a run directory without `state.json`); a non-zero exit means the
final tally is not a result. Alarms (critical/warning rows), Needs-verification items and owner
questions (`count_cards.py` cards per run) are reported separately and never summed (R13).

**Verdict rules (development rehearsal — not release evidence):**

- A should-quiet-shaped case (B3 quiet role, `reach-unchanged-*`) **fires** iff alarms > 0 OR
  Needs-verification items > 0 (`dev-burden`'s `fired`). A rendered NV item is an alarm here.
- A new-exposure case (`reach-new-*`) counts as a **catch** only when a row listed by
  `score43.py dev-catch-candidates` — alarm or Needs-verification row alike — identifies the keyed
  defect printed above the table: its location AND its causal failure (R13). An NV mention of the
  area without the causal failure earns nothing. Record which row earned it and whether it was an
  alarm or an NV row. `reach-new-2` is credited for the demonstrated HTML injection; it does not
  require, and the key does not claim, anything beyond that (owner condition, README approval
  record).
- A B3 catch case counts as a catch only when a `score43.py catch-candidates --state … --diff …`
  row does the same against the B3 answer key.
- A keyed site names one file (the sealed-manifest shape). A row filed in another file of the
  reached path (for `reach-new-1`, the unchanged sink in `triggarr/logging.py`) is not listed; if
  the report carries one, record it by hand under the case with the same location + causal
  failure standard.

## Final candidate rule

`FINAL_FP` is recorded (`STAGE=final p53 fingerprint`) after the last implementation or prompt
change, with `plugins/vibe-check/` committed. On that one fingerprint: the archived replay guard,
the allowance-gated complete-output diff, and EVERY B3 case (`score43.DIFFS`) plus every approved
reachability case, once each. Any change under `plugins/vibe-check/` after the final sweep begins
restarts it in full:

1. move `runs-phase53-dev/final/` to `runs-phase53-dev/attempts/final-<FINAL_FP first 12 hex>/`;
2. `resync-cache`, RELAUNCH, then `RESET_FINAL=1 STAGE=final p53 fingerprint` (prints the old
   value; record the invalidation and the reason in NOTES `## Final candidate`);
3. rerun the replay checks and the COMPLETE sweep on the new `FINAL_FP`.

A failed case is never rerun alone on a changed candidate, and a replay re-score of old state
files never substitutes for a live rerun (D-08). `post` and `preflight` refuse in stage `final`
whenever the installed cache's fingerprint differs from `FINAL_FP`.

## Lost catch rule

Any B3 catch lost on the completed candidate (a catch case whose `catch-candidates` rows do not
identify the keyed defect) is investigated and recorded in NOTES — cause, the rule involved, and
the decision — before the freeze (D-08). A lost catch is never closed by rerunning until it lands.

## Pitfall 11 note

The orchestrator plugin's `count_unfixed_cw` ignores Needs-verification obligations, so a review
whose finalize is blocked only by undecided NV items can look "clean" to the orchestrator. Any run
where finalize was blocked by NV items is flagged in the phase summary, not silently passed.
