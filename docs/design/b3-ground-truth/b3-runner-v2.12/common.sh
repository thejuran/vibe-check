# shellcheck shell=bash
# B3 runner identity layer for v2.12 measurement. Sourced by the `common` block of a B3 runbook
# (docs/design/reachability-dev/RUN-PHASE54-live.md and the runbooks built from it) and by
# run_case.sh. The freeze manifest hashes this directory, so an edit here is an identity change.
#
# Contract: every launch-bearing runbook block (preflight, launch, pre, post) calls
# b3_identity_check before it does anything else that matters. The check compares the runner copy,
# the runner settings, the launch model, the CLI binaries, the user-level configuration and the
# repo state against the active freeze manifest (freeze_check.py verify --runner b3). There is no
# flag or variable that skips it: a mismatch prints the differences and stops the block.
#
# The runner copy is built from the candidate commit's git objects (git archive), never from the
# working tree, and every run directory is stamped with the verified identity (b3_stamp_run).
set -euo pipefail
export LC_ALL=C

REPO=${REPO:-$HOME/turingmind-code-review}
RD=${RD:-docs/design/reachability-dev}
DD=${DD:-docs/design/b3-ground-truth}
LAYER_REL=docs/design/b3-ground-truth/b3-runner-v2.12
PLUGIN_ROOT=$REPO/plugins/vibe-check
SCRIPTS=${SCRIPTS:-$REPO/plugins/vibe-check/scripts}
SCORE43=$SCRIPTS/score43.py
FREEZE_TOOLS=${FREEZE_TOOLS:-$REPO/docs/design/freeze-v2.12/tools}
# empty -> freeze_check.py resolves the active manifest itself
MANIFEST=${MANIFEST:-}
case "$MANIFEST" in '' | /*) ;; *) MANIFEST=$REPO/$MANIFEST ;; esac
# the isolated runner: the candidate copy only the measured sessions load (--plugin-dir)
RUNNER=${RUNNER:-$HOME/.b3/phase54-runner}
RUNNER_PLUGIN=${RUNNER_PLUGIN:-$RUNNER/plugin/vibe-check}
RUNNER_SETTINGS=${RUNNER_SETTINGS:-$RUNNER/settings-measured.json}
ENV=${ENV:-$HOME/.b3/phase54-live.env}
NOTES=${NOTES:-$RD/NOTES-phase54-live.md}
DEFAULT_REG=$HOME/.claude/plugins/installed_plugins.json
CLONES=${CLONES:-'roonseek seedsyncarr triggarr'}
CLONES_ROOT=${CLONES_ROOT:-$HOME/.b3/phase54-clones}
DEV_SEAL=${DEV_SEAL:-917bde2}
mkdir -p "$HOME/.b3"

# the ~/.b3 env file: plain KEY=VALUE lines, read with sed, never sourced
env_get() { if test -f "$ENV"; then sed -n "s/^$1=//p" "$ENV" | tail -1; fi; }
env_set() {
  local tmp
  tmp=$(mktemp "$HOME/.b3/b3-env.XXXXXX")
  { if test -f "$ENV"; then grep -v "^$1=" "$ENV" || true; fi; printf '%s=%s\n' "$1" "$2"; } > "$tmp"
  mv "$tmp" "$ENV"
}

# run one named block of a runbook (with its common block first) under bash; replaces ~/.b3/b3.
# Usage: b3_block <runbook> <name> [args...]   — the args reach the block as $1, $2, ...
# The runbook must be committed as is: a block never runs from uncommitted runbook text.
b3_block() {
  local book=$1 name=$2 script
  shift 2
  case "$book" in /*) ;; *) book=$REPO/$book ;; esac
  test -f "$book" || { echo "b3_block: runbook $book not found — STOPPING"; return 2; }
  printf '%s' "$name" | grep -qE '^[a-z0-9-]+$' || { echo "b3_block: bad block name '$name' — STOPPING"; return 2; }
  git -C "$REPO" diff --quiet HEAD -- "$book" \
    || { echo "b3_block: $book HAS UNCOMMITTED CHANGES — blocks run from committed text only — STOPPING"; return 2; }
  script=$(awk '$0=="# BLOCK: common"{f=1} f{print} $0=="# END: common"{exit}' "$book"
    awk -v b="$name" '$0=="# BLOCK: "b{f=1} f{print} $0=="# END: "b{exit}' "$book")
  printf '%s\n' "$script" | grep -qx '# END: common' || { echo 'b3_block: the common block is missing — STOPPING'; return 2; }
  printf '%s\n' "$script" | tail -1 | grep -qx "# END: $name" || { echo "b3_block: no block named '$name' — STOPPING"; return 2; }
  # bash -c (not bash -s): the block's stdin stays free for typed attestations such as CLEARED
  if bash -c "$script" "b3:$name" "$@"; then
    echo "b3: BLOCK OK ($name)"
  else
    echo "b3: BLOCK FAILED ($name)"
    return 1
  fi
}

# the launch model: NOTES `pin-model:`, the same value the identity check compares to the manifest
resolve_model() {
  test -f "$REPO/$NOTES" || { echo "NOTES FILE $NOTES MISSING — STOPPING"; exit 1; }
  MODEL=$(sed -n 's/^pin-model: //p' "$REPO/$NOTES" | tail -1)
  printf '%s' "$MODEL" | grep -qE '^[A-Za-z0-9._-]+(\[1m\])?$' \
    || { echo 'NOTES pin-model: IS MISSING OR NOT A MODEL ID — STOPPING'; exit 1; }
}

# runner copy := the candidate commit's plugins/vibe-check, from git objects. The runner settings
# and the statusline capture script come from the same commit; the settings get exactly one edit:
# the literal <RUNNER> in statusLine.command becomes $RUNNER (the substitution the manifest pins).
b3_materialize_runner() {
  local cand=${1:-} sha
  test -n "$cand" || { echo 'b3_materialize_runner: NO CANDIDATE GIVEN — STOPPING'; exit 1; }
  printf '%s' "$cand" | grep -qE '^[0-9a-f]{7,40}$' || { echo 'CANDIDATE MUST BE A COMMIT SHA — STOPPING'; exit 1; }
  sha=$(git -C "$REPO" rev-parse --verify "$cand^{commit}") \
    || { echo "CANDIDATE $cand IS NOT A COMMIT IN $REPO — STOPPING"; exit 1; }
  isolation_check_owner
  mkdir -p "$RUNNER"
  rm -rf "$RUNNER/plugin"
  mkdir -p "$RUNNER/plugin"
  git -C "$REPO" archive "$sha" plugins/vibe-check | tar -x -C "$RUNNER/plugin" --strip-components=1
  test -f "$RUNNER_PLUGIN/.claude-plugin/plugin.json" \
    || { echo "RUNNER COPY $RUNNER_PLUGIN HAS NO PLUGIN MANIFEST AFTER THE ARCHIVE — STOPPING"; exit 1; }
  git -C "$REPO" show "$sha:$LAYER_REL/statusline-capture.sh" > "$RUNNER/statusline-capture.sh" \
    || { echo "statusline-capture.sh ABSENT AT $sha — STOPPING"; exit 1; }
  git -C "$REPO" show "$sha:$LAYER_REL/settings-measured.json" > "$RUNNER/settings-template.json" \
    || { echo "settings-measured.json ABSENT AT $sha — STOPPING"; exit 1; }
  python3 - "$RUNNER/settings-template.json" "$RUNNER" "$RUNNER_SETTINGS" <<'PY' \
    || { echo 'RUNNER SETTINGS COULD NOT BE INSTALLED — STOPPING'; exit 1; }
import json, sys
src, runner, dst = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src, encoding="utf-8") as fh:
    d = json.load(fh)
cmd = d["statusLine"]["command"]
if cmd.count("<RUNNER>") != 1:
    sys.exit("statusLine.command must hold <RUNNER> exactly once")
d["statusLine"]["command"] = cmd.replace("<RUNNER>", runner)
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(d, fh, indent=2)
    fh.write("\n")
PY
  rm -f "$RUNNER/settings-template.json"
  env_set candidate "$sha"
  echo "runner copy $RUNNER_PLUGIN := $sha:plugins/vibe-check (git archive)"
  echo "runner settings $RUNNER_SETTINGS := $sha:$LAYER_REL/settings-measured.json (<RUNNER> -> $RUNNER)"
}

# the pre-run identity check against the active freeze manifest. Needs MODEL (resolve_model) and
# CLONE (the disposable clone the session runs in). Exit != 0 from freeze_check = STOP, no override.
b3_identity_check() {
  local label=${1:?b3_identity_check needs a label} rc want
  test -n "${MODEL:-}" || resolve_model
  test -n "${CLONE:-}" || { echo "NO CLONE DIR FOR THE IDENTITY CHECK ($label) — STOPPING"; exit 1; }
  mkdir -p "$RUNNER"
  rc=0
  python3 "$FREEZE_TOOLS/freeze_check.py" verify --runner b3 --plugin-dir "$RUNNER_PLUGIN" \
    --settings "$RUNNER_SETTINGS" --model "$MODEL" --clone-dir "$CLONE" \
    ${MANIFEST:+--manifest "$MANIFEST"} > "$RUNNER/last-identity.txt" 2>&1 || rc=$?
  if test "$rc" != 0; then
    cat "$RUNNER/last-identity.txt"
    echo "IDENTITY MISMATCH ($label) — STOPPING"
    exit 1
  fi
  IDENTITY_LINE=$(grep '^IDENTITY OK ' "$RUNNER/last-identity.txt" | tail -1)
  printf '%s' "$IDENTITY_LINE" | grep -qE '^IDENTITY OK manifest_id=[0-9a-f]{64} check_digest=[0-9a-f]{64} candidate_sha=[0-9a-f]{40}$' \
    || { cat "$RUNNER/last-identity.txt"; echo "IDENTITY CHECK PRINTED NO IDENTITY OK LINE ($label) — STOPPING"; exit 1; }
  want=$(env_get candidate)
  test -n "$want" || { echo "NO MATERIALIZED CANDIDATE RECORDED IN $ENV — run materialize ($label) — STOPPING"; exit 1; }
  test "$(identity_field candidate_sha)" = "$want" \
    || { echo "THE RUNNER COPY WAS BUILT FROM $want, NOT THE MANIFEST CANDIDATE $(identity_field candidate_sha) ($label) — STOPPING"; exit 1; }
  export IDENTITY_LINE
  echo "$IDENTITY_LINE ($label)"
}

# one field (manifest_id | check_digest | candidate_sha) of IDENTITY_LINE
identity_field() { printf '%s\n' "$IDENTITY_LINE" | tr ' ' '\n' | sed -n "s/^$1=//p"; }

# the run's eligibility record: the runtime fingerprint of the runner copy plus the three stamps
b3_stamp_run() {
  local run_dir=${1:?b3_stamp_run needs a run dir} fp
  test -n "${IDENTITY_LINE:-}" || { echo 'NO VERIFIED IDENTITY TO STAMP (b3_identity_check first) — STOPPING'; exit 1; }
  test -d "$run_dir" || { echo "RUN DIR $run_dir MISSING — STOPPING"; exit 1; }
  test ! -e "$run_dir/fingerprint.txt" || { echo "$run_dir IS ALREADY STAMPED — STOPPING"; exit 1; }
  fp=$(python3 "$SCORE43" fingerprint --root "$RUNNER_PLUGIN") \
    || { echo 'RUNTIME FINGERPRINT FAILED — STOPPING'; exit 1; }
  printf 'runtime_fingerprint: %s\nmanifest_id: %s\ncheck_digest: %s\ncandidate_sha: %s\n' \
    "$fp" "$(identity_field manifest_id)" "$(identity_field check_digest)" \
    "$(identity_field candidate_sha)" > "$run_dir/fingerprint.txt"
  echo "stamped $run_dir/fingerprint.txt"
}

# the owner's installed vibe-check@thejuran cache dir, from Claude Code's own registry (read only)
default_cache() {
  python3 - "$DEFAULT_REG" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d = d.get("plugins", d)
paths = [e.get("installPath") for e in d.get("vibe-check@thejuran") or []
         if isinstance(e, dict) and e.get("installPath")]
if len(paths) != 1:
    sys.exit("expected one vibe-check@thejuran install, found %d" % len(paths))
print(paths[0])
PY
}

# the owner's default config never references the runner (the candidate stays out of everyday sessions)
isolation_check_owner() {
  local dc
  dc=$(default_cache) || { echo 'CANNOT RESOLVE THE OWNER INSTALLED vibe-check@thejuran CACHE — STOPPING'; exit 1; }
  case "$dc" in "$RUNNER"*) echo 'THE OWNER REGISTRY POINTS AT THE RUNNER COPY — STOPPING'; exit 1 ;; esac
  ! grep -qF "$RUNNER" "$DEFAULT_REG" "$HOME/.claude/settings.json" \
    || { echo 'THE OWNER DEFAULT CONFIG REFERENCES THE RUNNER — STOPPING'; exit 1; }
  DEFAULT_CACHE=$dc
}

# owner isolation plus the installed runner settings disabling the installed vibe-check@thejuran
isolation_check() {
  isolation_check_owner
  test -f "$RUNNER_SETTINGS" || { echo "RUNNER SETTINGS $RUNNER_SETTINGS MISSING — run materialize — STOPPING"; exit 1; }
  python3 -c 'import json,sys; s=json.load(open(sys.argv[1])); sys.exit(0 if s["enabledPlugins"]["vibe-check@thejuran"] is False else 1)' \
    "$RUNNER_SETTINGS" || { echo 'RUNNER SETTINGS DO NOT DISABLE THE INSTALLED vibe-check@thejuran — STOPPING'; exit 1; }
  test -f "$RUNNER_PLUGIN/.claude-plugin/plugin.json" \
    || { echo "RUNNER COPY $RUNNER_PLUGIN MISSING — run materialize — STOPPING"; exit 1; }
  CACHE=$RUNNER_PLUGIN
}

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
  case "${RUN:-}" in [1-9]) ;; *) echo 'RUN MUST BE 1-9 — STOPPING'; exit 1 ;; esac
}

# the memory dir and transcript dir Claude Code keeps for a clone path
proj_dir() { printf '%s/.claude/projects/%s' "$HOME" "$(printf '%s' "$1" | sed 's/[^A-Za-z0-9]/-/g')"; }

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
  # the disposable measurement clone of source_repo, never the owner's repo itself
  CLONE=$CLONES_ROOT/$CN
  STATE_DIR=$CLONE/.turingmind/state
  # the candidate keeps live review state under format-53/; a new flat file means an older build ran
  STATE53=$STATE_DIR/format-53
  PARK=$STATE_DIR/.b3-parked-${PARK_TAG:-phase54-live}
  PROJ=$(proj_dir "$CLONE")
  MEM=$PROJ/memory
  PATCH_FILE=$HOME/.b3/b3-$CASE.patch
  git -C "$REPO" show "HEAD:$p.patch" > "$PATCH_FILE"
  RP=$ARCHIVE/$CASE/run-${RUN:-0}
  RUN_DIR=$REPO/$RP
}

# N-02 — clone auto-memory a session re-created after park-memory is moved aside as evidence
mem_evidence() {
  test -e "$MEM" || return 0
  test -f "$MEMPARK_ENV" || { echo "AUTO-MEMORY FOR $CLONE IS NOT PARKED (run park-memory) — STOPPING"; exit 1; }
  local pd ev
  pd=$(sed -n 's/^PARKDIR=//p' "$MEMPARK_ENV")
  test -n "$pd" && test -d "$pd" || { echo 'THE MEMORY PARK DIR IS MISSING — STOPPING'; exit 1; }
  ev=$pd/$CN-written-before-${STAGE:-live}-${CASE:-window}-$1-$(date +%s)
  mv "$MEM" "$ev"
  echo "auto-memory re-created by a session moved aside to $ev (evidence, never merged back)"
}

# every top-level review state file, at the flat (pre-format-53) location and under format-53/
state_files() { find "$STATE_DIR" "$STATE53" -maxdepth 1 -name '*.json' 2> /dev/null || true; }

# the full tracked diff of the clone, as one sha256
clone_diff_sha() { git -C "$CLONE" diff | shasum -a 256 | awk '{print $1}'; }
