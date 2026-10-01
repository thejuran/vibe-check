# Phase-43 measurement runbook — v2.10 (36 runs, one parameterized file)

**Purpose:** the full post-change measurement (PROVE-01), as named bash blocks: all twelve sealed
B3 diffs, three runs each, on ONE immutable snapshot of the fully changed plugin, under the
v2.9/v2.10 isolation gates. Every per-diff constant (base commit, expected tree-diff sha, touched
path, source clone) is read at block time from the diff's committed `.provenance` sidecar after the
sidecar seal gate; nothing in this file retypes them.

This is the Phase-41 runbook (`SPOT-CHECK-v2.10-phase41.md`) generalized: instead of one copied
section per diff, every block takes the diff id and the run number as arguments. The machinery is
the same: an immutable `batchsnap.py` snapshot, the harness fingerprint against the pin, `/clear`
per run (N-01), auto-memory parking (N-02), the provenance grep, the manual-permission launch line.
New here: the harness freeze (D-09), the installed-cache resync with a content-hash parity gate
(D-00b.7), the 1M-window model pin (D-03), the per-run lane and Codex archive (D-00b.2), the
voided-attempt step (D-10), the driver-contamination check (D-13) and the expected-set close
(D-01, D-06).

Scoring is NOT in this file. `score43.py` and `SCORING-v2.10-phase43.md` score the committed runs
against the sealed answer-key blobs.

---

## 1. The run budget and the order (D-01, D-02)

**36 runs, no skips.** A hole makes the sealed bar unevaluable, so no run may be skipped to save
budget. A retune (only after a missed bar, D-04) adds three runs per failed diff and nothing else.

**Diff-by-diff, in the Phase-38 order.** All three runs of one diff are consecutive, with one
`fresh` (clone prepare) and one `revert` per diff:

| # | diff | role | clone | lockfile held |
|---|---|---|---|---|
| 1 | `triggarr-secret-in-logs` | catch | `~/triggarr` | `uv.lock` |
| 2 | `triggarr-autoescape` | catch | `~/triggarr` | `uv.lock` |
| 3 | `third-organic-should-catch` | catch | `~/seedsyncarr` | none |
| 4 | `should-quiet-1` | quiet | `~/triggarr` | `uv.lock` |
| 5 | `should-quiet-2` | quiet | `~/seedsyncarr` | none |
| 6 | `should-quiet-3` | quiet | `~/roonseek` | `uv.lock` |
| 7 | `triggarr-session-rotation` | catch | `~/triggarr` | `uv.lock` |
| 8 | `triggarr-settings-form-split` | catch | `~/triggarr` | `uv.lock` |
| 9 | `should-quiet-4` | quiet | `~/triggarr` | `uv.lock` |
| 10 | `should-quiet-5` | quiet | `~/seedsyncarr` | none |
| 11 | `should-quiet-6` | quiet | `~/triggarr` | `uv.lock` |
| 12 | `should-quiet-7` | quiet | `~/triggarr` | `uv.lock` |

The clone column is informational: `fresh` maps the sidecar's `source_repo:` to the clone. The
lockfile column is informational too: `fresh` protects `uv.lock` only when the clone has one.

**Sittings.** Plan on three or four sittings, split at diff boundaries (after a `revert`). A new
sitting re-runs `preflight` (with `RESUME=1`), then `launch` and `fingerprint` for the next diff.
A sitting may also end mid-diff: the clone stays prepared, and the next sitting resumes with
`RESUME=1 p43 preflight <diff>`, a new `launch`, a new `fingerprint`, then the next `pre`.

**Where runs land.** `docs/design/b3-ground-truth/runs-v2.10-phase43/<label>/<diff>/run-<n>/`,
where `<label>` is `first` for the 36-run first pass and `retune` for the conditional retune pass.
Never in `runs/`, `runs-v2.10/`, `runs-v2.10-phase40/` or `runs-v2.10-phase41/` (all sealed).

---

## 2. What is recorded, and by whom

Every block does the mechanical part: it prints `BLOCK OK` or stops with a line ending in
`STOPPING`. Nothing in a block decides whether a finding is a false alarm or a catch.

- **Mechanical (the blocks):** the snapshot re-verified, the tree-diff sha, the touched-path set,
  `len(passes)==1` at the pinned head, the state-shape check, the Codex status, the lane and
  Codex archive, the peak context, the driver-contamination check, the commit scope.
- **Judgement (the scorer, later):** per-run false-alarm verdicts, the catch AXIS call, the bar.

---

## MEASUREMENT-RUN RULE — the `/deep-review` fix loop + N-01 + N-02 (read this FIRST)

**When `/deep-review` finds something it enters an interactive Phase 5 fix loop. On EVERY run,
DECLINE all fixes and leave the loop without applying anything:** at Step A ("How do you want to
handle the N finding(s) above?") pick **"Skip fixes this pass"** (option 4); at Step C ("Pass N
loop — what's next?") pick **"Abandon for now"** (option 3). Never pick "Rerun review on the new
diff" (a second pass breaks `len(passes)==1`), never "Close out and document" / `--finalize`, and
never let a fix agent commit into the clone (a commit moves HEAD off the pinned base). The runs
MEASURE the tool; they do not fix the code.

**N-01 — conversation isolation (every run):** `/clear` immediately before EVERY
`/vibe-check:deep-review`, runs 2 and 3 of a diff, redone slots and resumed sessions included.
The `pre` block reads a typed `CLEARED` attestation into the run's `clear.txt` AFTER the `/clear`
has completed, then binds the run to the latest committed fingerprint in `session.txt`. The `post`
block checks both precede the review's recorded pass timestamp.

**N-02 — auto-memory (every session):** `/clear` does not reset Claude Code's per-project
auto-memory, and earlier measurement sessions wrote run-by-run notes there, including the expected
outcome of the diff under test. `park-memory` moves all three clones' memory directories aside
before the window opens; `preflight` and `launch` STOP while any is present; every `pre` moves
anything a session wrote there since launch into the park directory as evidence before the run
starts. `restore-memory` puts the owner's memory back after the last revert. A run whose session
started with the memory directory present is VOID.

**Usage limits and stalls.** A usage-limit pause that auto-resumes inside the SAME conversation
does not void the run. A run that dies BEFORE any review (credits exhausted, a launch crash, no
review started, no state written) is a voided attempt: `p43 void <diff> <n> "<reason>"`, then redo
the SAME slot from `pre`. A run that crashes or stalls MID-review (a state file may exist) is a
failed run: `p43 fail <diff> <n>`, then redo the same slot from `pre` (N-08). A run that has
committed is evidence and is never voided or failed.

## DRIVER RULE — assistant-driven via tmux (D-13, owner decision 2026-09-30)

Runs are assistant-driven via tmux, exactly as the Phase-40/41 checks were. The rule that keeps the
measurement clean:

1. **Separate processes.** Each measured session is a SEPARATE `claude` process in its own tmux
   session `p43-<diff>`, launched with the line `launch` prints, with its own context. The driving
   session never runs a review itself and is never the measured session.
2. **Pane text is read only to detect prompts** (`tmux capture-pane -p -t p43-<diff>`): is the
   session ready, has `/clear` completed, is Step A or Step C on screen, has the review finished.
3. **The FIXED KEYSTROKE SET is all the driver ever sends** to a measured session
   (`tmux send-keys -t p43-<diff> '<text>' Enter`): the launch line, `/clear`,
   `/vibe-check:deep-review`, `4` at Step A ("Skip fixes this pass"), `3` at Step C ("Abandon for
   now"), `/exit`. Never findings, hints, file names, diff ids, or an answer to any other question.
   **An unexpected question, prompt or permission request = STOP and report** — the driver does not
   improvise an answer.
4. **Typed attestations go to the blocks, not to the session.** The `pre` block's `CLEARED` and the
   `fingerprint` block's model, window and driver values are fed to the block's own stdin, e.g.
   `printf 'CLEARED\n' | p43 pre <diff> <n>`.
5. **The `post` block checks it.** It walks the run's transcript and classifies every user record by
   its RECORD PROVENANCE; every record that is driver input must belong to the fixed set, and the
   Step A / Step C answers must be the two allowed labels. Anything else is
   `DRIVER CONTAMINATION — STOPPING` and the run is `fail`ed, never deleted.
6. **The owner's only duty is to keep the laptop lid OPEN for the whole window.** A closed lid
   sleeps the Mac and killed a Phase-40 run.

Each fingerprint records `driver: assistant-tmux`, and `RUN-METHOD-NOTES-phase43.md` carries the
`run-method: assistant-driven via tmux` disclosure.

---

## 3. How to run a block (once per shell)

Blocks cannot be pasted into zsh line by line (zsh runs `#` lines as commands, and a failed check
would close the window). Paste this ONCE into each shell. It defines `p43`, which pulls the shared
`common` block plus one named block out of this file into `~/.b3/p43.sh` and runs it under bash:

```text
P43=~/turingmind-code-review/docs/design/b3-ground-truth/RUN-PHASE43-v2.10.md
p43() {
  mkdir -p ~/.b3
  { awk '$0=="# BLOCK: common"{f=1} f{print} $0=="# END: common"{exit}' "$P43"
    awk -v b="$1" '$0=="# BLOCK: "b{f=1} f{print} $0=="# END: "b{exit}' "$P43"; } > ~/.b3/p43.sh
  grep -qx '# END: common' ~/.b3/p43.sh || { echo "p43: the common block is missing"; return 2; }
  tail -1 ~/.b3/p43.sh | grep -qx "# END: $1" || { echo "p43: no block named '$1'"; return 2; }
  DIFF="${2:-}" RUN_N="${3:-}" VOID_REASON="${4:-}" LABEL="${LABEL:-first}" bash ~/.b3/p43.sh \
    && echo "p43: BLOCK OK ($1)" || { echo "p43: BLOCK FAILED ($1)"; return 1; }
}
```

Usage: `p43 <block> [diff] [n] [reason]`, e.g. `p43 fresh should-quiet-5`, `p43 pre should-quiet-5 2`,
`p43 void should-quiet-5 2 "credits exhausted"`. The window label comes from the environment:
`LABEL` defaults to `first`; the retune pass runs every block with `LABEL=retune`. Each block
validates its arguments against fixed allowlists before using them (the twelve diff ids, `1|2|3`,
`first|retune`, a character class for the void reason). If a block prints `BLOCK FAILED`, stop and
report the whole output.

### The order

**Open the window (once per label):**

| # | what | notes |
|---|---|---|
| 1 | `p43 park-memory` | N-02, all three clones |
| 2 | `p43 freeze` | D-09: records the prior auto-update state, then disables updates |
| 3 | `p43 resync-cache` | installed cache := the snapshot, two-direction hash parity |
| 4 | RELAUNCH | every measured session is a NEW `claude` process; quit any other running Claude Code fully |
| 5 | `p43 preflight` | writes `~/.b3/phase43-active.env` (the open-window marker) |

**Per diff, in the order of section 1:**

| # | what | notes |
|---|---|---|
| 6 | `p43 fresh <diff>` | prepare the clone (base + patch, state parked, lockfile held) |
| 7 | `p43 launch <diff>` | prints the launch line; `LAUNCH_VIA_TMUX=1` also opens tmux session `p43-<diff>` with it |
| 8 | `p43 fingerprint <diff>` | stdin: model as shown, `1M`, `assistant-tmux` |
| 9 | `/clear` in the session, wait for it, then `printf 'CLEARED\n' \| p43 pre <diff> <n>` | |
| 10 | `/vibe-check:deep-review` in the session; Step A `4`, Step C `3` | MEASUREMENT-RUN RULE |
| 11 | `p43 post <diff> <n>` | archives, checks and commits the run |
| 12 | repeat 9–11 for `n` = 2, 3 | |
| 13 | `/exit` in the session, `tmux kill-session -t p43-<diff>`, then `p43 revert <diff>` | |

**Close the window (once per label, after the last revert):**

| # | what | notes |
|---|---|---|
| 14 | `p43 first-pass-close` | every expected diff has exactly runs 1–3; writes `RUNS-COMPLETE.json` |
| 15 | `p43 restore-memory` | the owner's memory back; what sessions wrote kept as evidence |
| 16 | `p43 unfreeze` | restores exactly the recorded auto-update state |
| 17 | `p43 restore-cache` | installed cache back to released 2.9.0 |
| 18 | `p43 close-window` | removes the open-window marker ONLY when 14–17 all succeeded |
| 19 | RELAUNCH | so everyday sessions load the restored cache |

---

## 4. The shared block

`common` is prepended to every block by the runner. It holds the paths, the snapshot and sealed-tree
checks, the sidecar seal gate and the cache parity check, so each is defined exactly once.

```bash
# BLOCK: common
set -euo pipefail
REPO=$HOME/turingmind-code-review
DD=docs/design/b3-ground-truth
NOTES=$DD/RUN-METHOD-NOTES-phase43.md
P43ROOT=$DD/runs-v2.10-phase43
SCRIPTS=$REPO/plugins/vibe-check/scripts
BSNAP=$SCRIPTS/batchsnap.py
ENV=$HOME/.b3/phase43-active.env
FREEZE_ENV=$HOME/.b3/phase43-freeze.env
MEMPARK_ENV=$HOME/.b3/phase43-memory-park.env
CACHE=$HOME/.claude/plugins/cache/thejuran/vibe-check/2.9.0
CACHE_BAK=$HOME/.b3/vibe-check-2.9.0.bak-pre-phase43
SETTINGS=$HOME/.claude/settings.json
CODEX_CFG=$HOME/.codex/config.toml
CODEX_LINE='check_for_update_on_startup = false'
CLONES='roonseek seedsyncarr triggarr'
FIRST_FAILED=$P43ROOT/first/FAILED-DIFFS.json
mkdir -p "$HOME/.b3"
LABEL=${LABEL:-first}
case "$LABEL" in first|retune) ;; *) echo 'LABEL MUST BE first OR retune — STOPPING'; exit 1 ;; esac
RUNS=$P43ROOT/$LABEL
TIMEOUT_BIN=$(command -v timeout || command -v gtimeout || true)

# the open window, re-read by every block after preflight; the label must agree
load_env() {
  test -f "$ENV" || { echo 'NO OPEN WINDOW — run p43 preflight first — STOPPING'; exit 1; }
  local want=$LABEL
  . "$ENV"
  test "$LABEL" = "$want" \
    || { echo "THE OPEN WINDOW IS $LABEL, NOT $want — STOPPING"; exit 1; }
  RUNS=$P43ROOT/$LABEL
}

# the memory dir and transcript dir Claude Code keeps for a clone path
proj_dir() { printf '%s/.claude/projects/%s' "$HOME" "$(printf '%s' "$1" | sed 's/[^A-Za-z0-9]/-/g')"; }

# the snapshot of this label, from the COMMITTED notes blob (batch 5 = first, batch 6 = retune)
resolve_snapshot() {
  case "$LABEL" in first) BATCH=5 ;; retune) BATCH=6 ;; esac
  local nb line extra
  nb=$(git -C "$REPO" show "HEAD:$NOTES") \
    || { echo 'PHASE-43 NOTES FILE NOT COMMITTED — STOPPING'; exit 1; }
  test "$(printf '%s\n' "$nb" | grep -c "^snapshot: batch$BATCH ")" = "1" \
    || { echo "THE NOTES DO NOT RECORD EXACTLY ONE batch$BATCH SNAPSHOT — STOPPING"; exit 1; }
  line=$(printf '%s\n' "$nb" | grep "^snapshot: batch$BATCH ")
  read -r _ _ BATCH_SHA SNAP_ROOT extra <<< "$line"
  test -z "${extra:-}" || { echo 'MALFORMED snapshot: LINE — STOPPING'; exit 1; }
  printf '%s' "$BATCH_SHA" | grep -qE '^[0-9a-f]{40}$' \
    || { echo 'snapshot: LINE HAS NO 40-HEX COMMIT — STOPPING'; exit 1; }
  test "$SNAP_ROOT" = "$HOME/.vibe-check-snapshots/batch$BATCH-$(printf '%s' "$BATCH_SHA" | cut -c1-12)" \
    || { echo 'snapshot: LINE NAMES A ROOT THAT DOES NOT NAME ITS OWN COMMIT — STOPPING'; exit 1; }
  PLUGIN_ROOT=$SNAP_ROOT/plugins/vibe-check
}

# the snapshot is byte-identical to its manifest and the launch argument is right
snap_verify() {
  python3 "$BSNAP" verify --snap "$SNAP_ROOT" > "$HOME/.b3/p43-verify.out" \
    || { cat "$HOME/.b3/p43-verify.out"; echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
  test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
    || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
  test "$(tail -1 "$HOME/.b3/p43-verify.out")" = "plugin_root: $PLUGIN_ROOT" \
    || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
}

# every sealed run archive is intact and clean
sealed_trees() {
  git -C "$REPO" diff v2.9 --quiet -- "$DD/runs/" \
    || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
  test "$(git -C "$REPO" rev-parse "HEAD:$DD/runs-v2.10")" \
     = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
    || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
  test "$(git -C "$REPO" rev-parse "HEAD:$DD/runs-v2.10-phase40")" \
     = "29d1344b6b93136d1ae0273008ce34a154360e7b" \
    || { echo 'SEALED PHASE-40 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
  test "$(git -C "$REPO" rev-parse "HEAD:$DD/runs-v2.10-phase41")" \
     = "50d25bb33af6a703d19a6eb4fad0e9a4991b19d9" \
    || { echo 'SEALED PHASE-41 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
  test -z "$(git -C "$REPO" status --porcelain "$DD/runs/" "$DD/runs-v2.10/" \
      "$DD/runs-v2.10-phase40/" "$DD/runs-v2.10-phase41/")" \
    || { echo 'A SEALED RUNS TREE IS DIRTY — STOPPING; report it'; exit 1; }
}

# retune pass: the diff must be on the COMMITTED first-pass failed list (D-06)
retune_member() {
  test "$LABEL" = retune || return 0
  git -C "$REPO" ls-files --error-unmatch "$FIRST_FAILED" > /dev/null 2>&1 \
    || { echo 'FAILED-DIFFS.json IS NOT COMMITTED — no retune without it — STOPPING'; exit 1; }
  git -C "$REPO" show "HEAD:$FIRST_FAILED" > "$HOME/.b3/p43-failed-diffs.json" \
    || { echo 'FAILED-DIFFS.json NOT READABLE FROM HEAD — STOPPING'; exit 1; }
  python3 - "$HOME/.b3/p43-failed-diffs.json" "$1" <<'PY' \
    || { echo 'DIFF NOT IN FAILED-DIFFS — STOPPING'; exit 1; }
import json, sys
lst = json.load(open(sys.argv[1]))
if not (isinstance(lst, list) and all(isinstance(d, str) for d in lst)):
    sys.exit("FAILED-DIFFS.json is not a list of diff ids")
if sys.argv[2] not in lst:
    sys.exit("%s is not on the committed failed-diff list" % sys.argv[2])
PY
}

# SCORING-v2.10 gate (6a) on the sidecar, then its constants from the COMMITTED blob
sidecar() {
  local d=$1 p=$DD/diffs/$1 e s key prov
  case "$d" in
    triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3)
      for e in patch provenance; do
        test "$(git -C "$REPO" rev-parse "v2.9:$p.$e")" = "$(git -C "$REPO" rev-parse "HEAD:$p.$e")" \
          || { echo "SIDECAR SEAL BROKEN ($d.$e IS NOT BLOB-EQUAL TO TAG v2.9) — STOPPING"; exit 1; }
      done ;;
    triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7)
      key=$(git -C "$REPO" show "5f687d9:$DD/ANSWER-KEY-v2.10.md")
      for e in patch provenance; do
        s=$(git -C "$REPO" show "HEAD:$p.$e" | shasum -a 256 | awk '{print $1}')
        printf '%s\n' "$key" | grep -qxF "sha256(diffs/$d.$e) = $s" \
          || { echo "SIDECAR SEAL BROKEN ($d.$e sha256 IS NOT IN KEY BLOB 5f687d9) — STOPPING"; exit 1; }
      done ;;
    *) echo 'UNKNOWN DIFF ID — STOPPING'; exit 1 ;;
  esac
  git -C "$REPO" diff --quiet HEAD -- "$p.patch" "$p.provenance" \
    || { echo 'SIDECAR HAS UNCOMMITTED CHANGES — STOPPING'; exit 1; }
  prov=$(git -C "$REPO" show "HEAD:$p.provenance")
  for e in base_sha EXPECTED_TREE_DIFF_SHA256 EXPECTED_TOUCHED_PATHS source_repo; do
    test "$(printf '%s\n' "$prov" | grep -c "^$e: ")" = "1" \
      || { echo "SIDECAR KEY $e NOT EXACTLY ONCE — STOPPING"; exit 1; }
  done
  BASE_SHA=$(printf '%s\n' "$prov" | sed -n 's/^base_sha: //p' | tr -d '[:space:]')
  EXPECTED_SHA=$(printf '%s\n' "$prov" | sed -n 's/^EXPECTED_TREE_DIFF_SHA256: //p' | tr -d '[:space:]')
  TOUCHED=$(printf '%s\n' "$prov" | sed -n 's/^EXPECTED_TOUCHED_PATHS: //p' | sed 's/[[:space:]]*$//')
  SRC=$(printf '%s\n' "$prov" | sed -n 's/^source_repo: //p' | sed 's/[[:space:]]*$//')
  printf '%s' "$BASE_SHA" | grep -qE '^[0-9a-f]{40}$' \
    || { echo 'SIDECAR base_sha IS NOT 40-HEX — STOPPING'; exit 1; }
  printf '%s' "$EXPECTED_SHA" | grep -qE '^[0-9a-f]{64}$' \
    || { echo 'SIDECAR EXPECTED_TREE_DIFF_SHA256 IS NOT 64-HEX — STOPPING'; exit 1; }
  printf '%s' "$TOUCHED" | grep -qE '^[A-Za-z0-9._/-]+$' \
    || { echo 'SIDECAR EXPECTED_TOUCHED_PATHS IS NOT ONE PLAIN PATH — STOPPING'; exit 1; }
  case "$SRC" in
    '~/triggarr') CN=triggarr ;;
    '~/seedsyncarr') CN=seedsyncarr ;;
    '~/roonseek') CN=roonseek ;;
    *) echo 'SIDECAR source_repo IS NOT ONE OF THE THREE CLONES — STOPPING'; exit 1 ;;
  esac
  CLONE=$HOME/$CN
  STATE_DIR=$CLONE/.turingmind/state
  PARK=$STATE_DIR/.b3-parked-phase43
  PROJ=$(proj_dir "$CLONE")
  MEM=$PROJ/memory
  PATCH_FILE=$HOME/.b3/p43-$d.patch
  git -C "$REPO" show "HEAD:$p.patch" > "$PATCH_FILE"
}

# the full tracked diff of the clone, as one sha256
clone_diff_sha() { git -C "$CLONE" diff | shasum -a 256 | awk '{print $1}'; }

# installed cache vs snapshot MANIFEST: forward sha256 equality, reverse no-extras over the
# runtime roots, the manifest's own hash_exclude respected; never a version string
parity_check() {
  python3 - "$1" "$2" <<'PY'
import hashlib, json, os, sys
cache, manifest = sys.argv[1], sys.argv[2]
m = json.load(open(manifest))
files, exclude = m["files"], m.get("hash_exclude", [])
def excluded(rel):
    parts = rel.split("/")
    for pat in exclude:
        if pat.endswith("/") and pat[:-1] in parts:
            return True
        if pat.startswith("*.") and parts[-1].endswith(pat[1:]):
            return True
        if parts[-1] == pat:
            return True
    return False
def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
forward = sorted(r for r in files if not r.startswith("docs/"))
for rel in forward:
    path = os.path.join(cache, rel)
    if not os.path.isfile(path) or sha(path) != files[rel]:
        sys.exit("forward parity failed: %s" % rel)
extra = []
for root in (".claude-plugin", "agents", "commands", "scripts", "templates", "hooks", "phases"):
    top = os.path.join(cache, root)
    for dirpath, _dirs, names in os.walk(top):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), cache).replace(os.sep, "/")
            if not excluded(rel) and rel not in files:
                extra.append(rel)
if extra:
    sys.exit("reverse parity failed: %d extra runtime file(s), first %s" % (len(extra), extra[0]))
print("forward=%d/%d reverse=0 extra" % (len(forward), len(forward)))
PY
}

# insert one line at the end of a named section of the notes file (before the next ## header)
notes_append() {
  python3 - "$REPO/$NOTES" "$1" "$2" <<'PY'
import sys
path, section, line = sys.argv[1:4]
lines = open(path).read().split("\n")
head = lines.index(section)
end = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
at = end
while at > head + 1 and lines[at - 1] == "":
    at -= 1
lines[at:at] = [line] if lines[at - 1].startswith(line.split(":")[0] + ":") else ["", line]
open(path, "w").write("\n".join(lines))
PY
}

# commit ONE path and assert the commit the pathspec resolves to touches nothing else
commit_one() {
  git -C "$REPO" add -- "$2"
  git -C "$REPO" commit -q --only -m "$1" -- "$2"
  local c
  c=$(git -C "$REPO" log -1 --format=%H -- "$2")
  test "$(git -C "$REPO" show --name-only --format= "$c")" = "$2" \
    || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
  echo "committed $2 ($c)"
}
# END: common
```

---

## 5. Opening the window

### park-memory (N-02)

Moves all three clones' auto-memory directories into one park directory for this window and
records it in `~/.b3/phase43-memory-park.env`. Refuses to park twice.

```bash
# BLOCK: park-memory
set -euo pipefail
test ! -e "$MEMPARK_ENV" \
  || { echo 'MEMORY IS ALREADY PARKED FOR AN OPEN WINDOW (phase43-memory-park.env) — STOPPING'; exit 1; }
PARKDIR=$HOME/.b3/automemory-parked-phase43-$LABEL-$(date +%s)
mkdir -p "$PARKDIR"
for C in $CLONES; do
  M=$(proj_dir "$HOME/$C")/memory
  if test -e "$M"; then
    test ! -e "$PARKDIR/$C" || { echo "$PARKDIR/$C ALREADY HOLDS PARKED MEMORY — STOPPING"; exit 1; }
    mv "$M" "$PARKDIR/$C"
    echo "parked ~/$C auto-memory -> $PARKDIR/$C"
  else
    echo "~/$C has no auto-memory to park"
  fi
  test ! -e "$M" || { echo "~/$C AUTO-MEMORY STILL PRESENT — STOPPING"; exit 1; }
done
printf 'PARKDIR=%q\nPARK_LABEL=%q\n' "$PARKDIR" "$LABEL" > "$MEMPARK_ENV"
echo 'BLOCK OK'
# END: park-memory
```

### freeze (D-09)

Records the prior auto-update state of Claude Code and Codex in `~/.b3/phase43-freeze.env`, backs
up both config files (`~/.claude/settings.json.phase43-bak`, `~/.codex/config.toml.phase43-bak`),
and only then disables updates for the window. Claude Code's updater was
ALREADY disabled before this phase (`DISABLE_AUTOUPDATER=1` in `~/.claude/settings.json`), so on
this machine the Claude Code half records that and changes nothing; the Codex half adds the
top-level `check_for_update_on_startup = false` line (first line of the file, so it can never land
inside a TOML table). `unfreeze` restores exactly the recorded state; it never forces updates on.

```bash
# BLOCK: freeze
set -euo pipefail
test ! -e "$FREEZE_ENV" \
  || { echo 'ALREADY FROZEN (phase43-freeze.env exists) — run p43 unfreeze first — STOPPING'; exit 1; }
test ! -e "$SETTINGS.phase43-bak" && test ! -e "$CODEX_CFG.phase43-bak" \
  || { echo 'A phase43-bak BACKUP ALREADY EXISTS — STOPPING; report it'; exit 1; }
test -n "$TIMEOUT_BIN" || { echo 'NO timeout BINARY — STOPPING'; exit 1; }
test -f "$SETTINGS" || { echo 'NO ~/.claude/settings.json — STOPPING'; exit 1; }
test -f "$CODEX_CFG" || { echo 'NO ~/.codex/config.toml — STOPPING'; exit 1; }
DOCTOR_LINE=$("$TIMEOUT_BIN" 60 claude doctor < /dev/null 2>&1 | grep '^Auto-updates:' | head -1 || true)
test -n "$DOCTOR_LINE" || { echo 'claude doctor PRINTED NO Auto-updates LINE — STOPPING'; exit 1; }
CLAUDE_ENV_PRESENT=$(python3 - "$SETTINGS" <<'PY'
import json, sys
env = json.load(open(sys.argv[1])).get("env") or {}
print(1 if env.get("DISABLE_AUTOUPDATER") == "1" else 0)
PY
)
if grep -qE '^[[:space:]]*check_for_update_on_startup[[:space:]]*=' "$CODEX_CFG"; then
  CODEX_KEY_PRESENT=1
else
  CODEX_KEY_PRESENT=0
fi
cp -p "$SETTINGS" "$SETTINGS.phase43-bak"
cp -p "$CODEX_CFG" "$CODEX_CFG.phase43-bak"
{
  printf 'CLAUDE_AUTOUPDATE_LINE=%q\n' "$DOCTOR_LINE"
  printf 'CLAUDE_ENV_PRESENT=%q\n' "$CLAUDE_ENV_PRESENT"
  printf 'CODEX_KEY_PRESENT=%q\n' "$CODEX_KEY_PRESENT"
  printf 'FROZEN_AT=%q\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
} > "$FREEZE_ENV"
if test "$CLAUDE_ENV_PRESENT" = 0; then
  python3 - "$SETTINGS" <<'PY'
import json, sys
p = sys.argv[1]
s = json.load(open(p))
s.setdefault("env", {})["DISABLE_AUTOUPDATER"] = "1"
with open(p, "w") as fh:
    json.dump(s, fh, indent=2)
    fh.write("\n")
PY
  echo 'Claude Code: DISABLE_AUTOUPDATER=1 added to settings.json env for the window'
else
  echo 'Claude Code: auto-update already disabled before this window (recorded; nothing changed)'
fi
if test "$CODEX_KEY_PRESENT" = 0; then
  { printf '%s\n' "$CODEX_LINE"; cat "$CODEX_CFG.phase43-bak"; } > "$CODEX_CFG"
  echo 'Codex: check_for_update_on_startup = false added as the first line for the window'
else
  echo 'Codex: check_for_update_on_startup already set (recorded; nothing changed)'
fi
"$TIMEOUT_BIN" 60 claude doctor < /dev/null 2>&1 | grep '^Auto-updates:' | grep -q 'disabled' \
  || { echo 'claude doctor DOES NOT REPORT AUTO-UPDATES DISABLED — STOPPING'; exit 1; }
echo "prior state recorded in $FREEZE_ENV: $DOCTOR_LINE; codex key present=$CODEX_KEY_PRESENT"
echo 'BLOCK OK'
# END: freeze
```

### resync-cache (D-00b.7)

The measured sessions load the plugin from the snapshot (`--plugin-dir`), and the `post` block
voids any run whose transcript names the installed cache. The installed cache is still made
byte-identical to the snapshot for the window, so nothing the harness loads by a side path
differs. A version string proves nothing here (the repo and the stale release are both `2.9.0`),
so parity is content hashes in both directions against the snapshot's `MANIFEST.json`. The cache
is backed up ONCE to `~/.b3/vibe-check-2.9.0.bak-pre-phase43`, outside Claude Code's plugin cache
entirely, so the harness never sees or cleans it up. A second resync while that backup exists
(e.g. the retune snapshot) needs `RESYNC_AGAIN=1` and keeps the original backup.

```bash
# BLOCK: resync-cache
set -euo pipefail
resolve_snapshot
snap_verify
test -d "$CACHE" || { echo 'INSTALLED vibe-check 2.9.0 CACHE MISSING — STOPPING'; exit 1; }
git -C "$REPO" diff --quiet -- "$NOTES" && git -C "$REPO" diff --cached --quiet -- "$NOTES" \
  || { echo 'THE PHASE-43 NOTES FILE HAS UNCOMMITTED CHANGES — STOPPING'; exit 1; }
if test -e "$CACHE_BAK"; then
  test "${RESYNC_AGAIN:-0}" = 1 \
    || { echo 'A CACHE BACKUP ALREADY EXISTS — RESYNC_AGAIN=1 to resync over it — STOPPING'; exit 1; }
  echo "keeping the existing released-cache backup $CACHE_BAK"
else
  cp -Rp "$CACHE" "$CACHE_BAK"
  diff -rq -x .in_use "$CACHE" "$CACHE_BAK" > /dev/null \
    || { echo 'CACHE BACKUP DIFFERS FROM THE CACHE — STOPPING'; exit 1; }
  echo "released cache backed up to $CACHE_BAK"
fi
rsync -a --delete --exclude .in_use --exclude __pycache__ --exclude '*.pyc' \
  --exclude .pytest_cache "$PLUGIN_ROOT/" "$CACHE/"
# the snapshot is sealed read-only and -a copies that mode; the cache must stay writable for
# Claude Code's cache manager and for restore-cache (macOS openrsync ignores --chmod on directories)
chmod -R u+w "$CACHE"
PARITY=$(parity_check "$CACHE" "$SNAP_ROOT/MANIFEST.json") \
  || { echo 'CACHE PARITY FAILED AFTER RSYNC — STOPPING'; exit 1; }
HIGHEST=$(ls "$HOME/.claude/plugins/cache/thejuran/vibe-check" | sort -V | tail -1)
test "$HIGHEST" = "2.9.0" \
  || { echo "A NEWER CACHE DIR ($HIGHEST) WOULD SHADOW 2.9.0 — STOPPING"; exit 1; }
notes_append '## Cache parity' "parity: $BATCH_SHA $PARITY at $(date '+%Y-%m-%dT%H:%M:%S%z')"
commit_one "runs(43): installed cache at parity with batch$BATCH snapshot" "$NOTES"
echo "cache parity: $PARITY"
echo 'RELAUNCH CLAUDE CODE (FULL PROCESS EXIT) BEFORE preflight'
echo 'BLOCK OK'
# END: resync-cache
```

### preflight (once per sitting)

Writes `~/.b3/phase43-active.env`, the open-window marker every later block reads. A new sitting
of the SAME window re-runs this with `RESUME=1` (and the in-progress diff as the argument when a
clone is mid-diff). A marker left by a different label is never resumed: that window must close
first (`close-window`).

```bash
# BLOCK: preflight
set -euo pipefail
if test -n "$DIFF"; then
  case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
    *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
fi
# (a) no open window from an unfinished sitting, unless resuming the SAME label
if test -e "$ENV"; then
  OPEN_LABEL=$(sed -n 's/^LABEL=//p' "$ENV")
  test "${RESUME:-0}" = 1 && test "$OPEN_LABEL" = "$LABEL" \
    || { echo "A WINDOW ($OPEN_LABEL) IS STILL OPEN — close it (p43 close-window) or RESUME=1 for the same label — STOPPING"; exit 1; }
  echo "resuming the open $LABEL window"
fi
# (b) the snapshot this label measures, byte-identical to its manifest
resolve_snapshot
test -d "$SNAP_ROOT" || { echo "SNAPSHOT $SNAP_ROOT MISSING — STOPPING"; exit 1; }
snap_verify
# (c) the manifest's own record + the ancestry of the measured commit
mf() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' \
  "$SNAP_ROOT/MANIFEST.json" "$1"; }
test "$(mf batch)" = "$BATCH" || { echo "SNAPSHOT IS NOT A BATCH-$BATCH SNAPSHOT — STOPPING"; exit 1; }
test "$(mf snapshot_commit)" = "$BATCH_SHA" \
  || { echo 'MANIFEST COMMIT != THE NOTES snapshot: LINE — STOPPING'; exit 1; }
git -C "$REPO" cat-file -e "$BATCH_SHA^{commit}" \
  || { echo 'SNAPSHOT COMMIT NOT IN THIS REPO — STOPPING'; exit 1; }
test "$(basename "$SNAP_ROOT")" = "batch$BATCH-$(printf '%s' "$BATCH_SHA" | cut -c1-12)" \
  || { echo 'SNAPSHOT FOLDER DOES NOT NAME ITS OWN COMMIT — STOPPING'; exit 1; }
SUITE=$(mf suite_green)
printf '%s' "$SUITE" | grep -q 'passed' && ! printf '%s' "$SUITE" | grep -qE 'failed|error' \
  || { echo "SNAPSHOT SUITE NOT RECORDED GREEN ($SUITE) — STOPPING"; exit 1; }
LAUNCH_FIX=$(git -C "$REPO" show "HEAD:$P43ROOT/PLAN-COMMITS.json" | python3 -c '
import json, sys
shas = json.load(sys.stdin).get("43-01") or []
assert len(shas) == 1, "43-01 must be recorded exactly once"
print(shas[0])') || { echo 'PLAN-COMMITS.json DOES NOT RECORD THE LAUNCH-GATE FIX ONCE — STOPPING'; exit 1; }
for A in cede608 180e0e3 "$LAUNCH_FIX"; do
  git -C "$REPO" merge-base --is-ancestor "$A" "$BATCH_SHA" \
    || { echo "COMMIT $A IS NOT AN ANCESTOR OF THE SNAPSHOT COMMIT — STOPPING"; exit 1; }
done
if test "$LABEL" = retune; then
  git -C "$REPO" cat-file -e "HEAD:$P43ROOT/first/RUNS-COMPLETE.json" \
    || { echo 'THE FIRST PASS IS NOT CLOSED (no committed RUNS-COMPLETE.json) — STOPPING'; exit 1; }
  git -C "$REPO" ls-files --error-unmatch "$FIRST_FAILED" > /dev/null 2>&1 \
    || { echo 'FAILED-DIFFS.json IS NOT COMMITTED — no retune without it — STOPPING'; exit 1; }
fi
# (d) installed-cache parity: the same two-direction hash check as resync-cache, plus the record
test -d "$CACHE" || { echo 'INSTALLED vibe-check 2.9.0 CACHE MISSING — STOPPING'; exit 1; }
PARITY=$(parity_check "$CACHE" "$SNAP_ROOT/MANIFEST.json") \
  || { echo 'INSTALLED CACHE NOT AT PARITY WITH THE SNAPSHOT — run p43 resync-cache — STOPPING'; exit 1; }
LASTP=$(git -C "$REPO" show "HEAD:$NOTES" | { grep '^parity: ' || true; } | tail -1)
case "$LASTP" in "parity: $BATCH_SHA "*) ;;
  *) echo 'THE COMMITTED NOTES DO NOT RECORD PARITY WITH THIS SNAPSHOT LAST — STOPPING'; exit 1 ;; esac
HIGHEST=$(ls "$HOME/.claude/plugins/cache/thejuran/vibe-check" | sort -V | tail -1)
test "$HIGHEST" = "2.9.0" \
  || { echo "A NEWER CACHE DIR ($HIGHEST) WOULD SHADOW 2.9.0 — STOPPING"; exit 1; }
# (e)(f) every sealed run archive intact
sealed_trees
# (g) both CLIs answer and equal the pins in the COMMITTED notes blob
NB=$(git -C "$REPO" show "HEAD:$NOTES")
pin() { printf '%s\n' "$NB" | grep "^$1: " | sed "s/^$1: //"; }
CC=$(claude --version) || { echo 'claude --version FAILED — STOPPING'; exit 1; }
CX=$(codex --version) || { echo 'codex --version FAILED — STOPPING'; exit 1; }
test "$CC" = "$(pin pin-claude-code)" || { echo "HARNESS DRIFT — claude-code '$CC' — STOPPING"; exit 1; }
test "$CX" = "$(pin pin-codex)" || { echo "HARNESS DRIFT — codex '$CX' — STOPPING"; exit 1; }
# (h) N-02 — every clone's auto-memory parked, and the park recorded
test -f "$MEMPARK_ENV" || { echo 'MEMORY NOT PARKED FOR THIS WINDOW — run p43 park-memory — STOPPING'; exit 1; }
for C in $CLONES; do
  test ! -e "$(proj_dir "$HOME/$C")/memory" \
    || { echo "~/$C AUTO-MEMORY IS NOT PARKED — run p43 park-memory — STOPPING"; exit 1; }
done
# (i) the three clones: present, excluded state dir, on a branch and clean, or mid-diff for $DIFF
INPROG=0
for C in $CLONES; do
  test -d "$HOME/$C/.git" || { echo "CLONE ~/$C MISSING — STOPPING"; exit 1; }
  grep -qx '.turingmind/' "$HOME/$C/.git/info/exclude" \
    || { echo "~/$C HAS NO LOCAL .turingmind/ EXCLUDE — STOPPING"; exit 1; }
  if test -e "$HOME/$C/.turingmind/state/.b3-inprogress"; then
    INPROG=$((INPROG + 1))
    test -n "$DIFF" && grep -qx "diff_id=$DIFF" "$HOME/$C/.turingmind/state/.b3-inprogress" \
      || { echo "~/$C IS MID-DIFF FOR ANOTHER DIFF (resume with: RESUME=1 p43 preflight <that diff>) — STOPPING"; exit 1; }
  else
    test -z "$(git -C "$HOME/$C" status --porcelain)" \
      || { git -C "$HOME/$C" status --short | head -5
           echo "CLONE ~/$C NOT CLEAN — the owner must commit or move that work aside — STOPPING"; exit 1; }
    test -n "$(git -C "$HOME/$C" branch --show-current)" \
      || { echo "CLONE ~/$C IS DETACHED — switch it back to its branch — STOPPING"; exit 1; }
  fi
done
test "$INPROG" -le 1 || { echo 'MORE THAN ONE CLONE IS MID-DIFF — STOPPING'; exit 1; }
# (j) the harness freeze is recorded and in force
test -f "$FREEZE_ENV" || { echo 'NOT FROZEN — run p43 freeze — STOPPING'; exit 1; }
test -n "$TIMEOUT_BIN" || { echo 'NO timeout BINARY — STOPPING'; exit 1; }
"$TIMEOUT_BIN" 60 claude doctor < /dev/null 2>&1 | grep '^Auto-updates:' | grep -q 'disabled' \
  || { echo 'claude doctor DOES NOT REPORT AUTO-UPDATES DISABLED — STOPPING'; exit 1; }
# (k) a timeout binary for the Codex watchdog and wait (else every run skips Codex)
command -v timeout > /dev/null || command -v gtimeout > /dev/null \
  || { echo 'NO timeout/gtimeout ON PATH — STOPPING'; exit 1; }
# the open-window marker
{
  printf 'REPO=%q\n' "$REPO"
  printf 'SNAP_ROOT=%q\n' "$SNAP_ROOT"
  printf 'PLUGIN_ROOT=%q\n' "$PLUGIN_ROOT"
  printf 'BATCH_SHA=%q\n' "$BATCH_SHA"
  printf 'BATCH=%q\n' "$BATCH"
  printf 'NOTES=%q\n' "$NOTES"
  printf 'LABEL=%q\n' "$LABEL"
  printf 'OPENED_AT=%q\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
} > "$ENV"
echo "window:       $LABEL (batch $BATCH)"
echo "snapshot:     $SNAP_ROOT"
echo "plugin root:  $PLUGIN_ROOT"
echo "batch commit: $BATCH_SHA"
echo "cache parity: $PARITY"
echo 'BLOCK OK'
# END: preflight
```

---

## 6. Per diff — prepare, launch, fingerprint

### fresh `<diff>`

Pins the clone to the sidecar's base commit, applies the patch once (kept until `revert`), asserts
the full tracked diff equals the sidecar's expected sha, parks every existing state file in
`.b3-parked-phase43/`, writes the `.b3-inprogress` sentinel and holds `uv.lock` when the clone has
one. Under `LABEL=retune` the diff must be on the committed `first/FAILED-DIFFS.json` list (D-06):
a retune run for any other diff is refused here, at the source.

```bash
# BLOCK: fresh
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
retune_member "$DIFF"
load_env
sidecar "$DIFF"
test -d "$CLONE/.git" || { echo "CLONE $CLONE MISSING — STOPPING"; exit 1; }
cd "$CLONE"
# guards FIRST, so a refusal leaves the clone untouched
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
test -n "$START_BRANCH" || { echo 'CLONE IS DETACHED — switch it back to its branch first — STOPPING'; exit 1; }
mkdir -p "$STATE_DIR"
test ! -e "$STATE_DIR/.b3-inprogress" \
  || { echo 'A DIFF IS ALREADY IN PROGRESS HERE (.b3-inprogress) — STOPPING'; exit 1; }
test ! -e "$PARK" || { echo 'STALE PARK DIR WITHOUT A SENTINEL — STOPPING'; exit 1; }
test ! -e "$MEM" || { echo 'AUTO-MEMORY FOR THIS CLONE IS NOT PARKED — STOPPING'; exit 1; }
# pin to the sidecar's base; an unappliable patch puts the clone straight back
git switch -q --detach "$BASE_SHA"
test "$(git rev-parse HEAD)" = "$BASE_SHA" || { echo 'WRONG BASE — STOPPING'; exit 1; }
git apply --check "$PATCH_FILE" \
  || { git switch -q "$START_BRANCH"; echo 'PATCH DOES NOT APPLY AT base_sha — clone restored — STOPPING'; exit 1; }
git apply "$PATCH_FILE"
test "$(clone_diff_sha)" = "$EXPECTED_SHA" \
  || { echo 'FULL WORKTREE DIFF != THE SIDECAR EXPECTED SHA — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "$TOUCHED" \
  || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# park every existing state file, write the sentinel, hold the lockfile when there is one
mkdir "$PARK"
PARKED=0
for f in "$STATE_DIR"/*.json; do
  test -e "$f" || continue
  mv "$f" "$PARK/"; PARKED=$((PARKED + 1))
done
if test "$PARKED" -gt 0; then HAD_PRIOR=true; else HAD_PRIOR=false; fi
if test -f "$CLONE/uv.lock"; then LOCK=1; else LOCK=0; fi
{
  printf 'diff_id=%s\nbase_sha=%s\n' "$DIFF" "$BASE_SHA"
  printf 'had_prior_state=%s\nstart_branch=%s\nstart_sha=%s\nparked=%s\nlock=%s\nlabel=%s\n' \
    "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" "$PARKED" "$LOCK" "$LABEL"
} > "$STATE_DIR/.b3-inprogress"
if test "$LOCK" = 1; then chflags uchg "$CLONE/uv.lock"; fi
echo "$DIFF ready in $CLONE at $(git rev-parse HEAD), $PARKED state file(s) parked, lock=$LOCK"
echo 'BLOCK OK'
# END: fresh
```

### launch `<diff>`

Builds the launch line ONCE into `LAUNCH_LINE` and prints both forms from that one variable. The
model argument is single-quoted because zsh globs a bare `[1m]` and aborts with "no matches
found". `--plugin-dir` takes the snapshot's `plugins/vibe-check` folder (the one holding
`.claude-plugin/plugin.json`), never the snapshot root. `--allowedTools` pre-approves what the review
needs and `--permission-mode manual` keeps the auto-mode classifier out (Phase-40 precedent: it
blocked the orchestrator's reads of the snapshot); both change permission handling only, never the
plugin. With `LAUNCH_VIA_TMUX=1` the block also opens the driver's tmux session from the same
variable, so the line is never retyped.

```bash
# BLOCK: launch
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
load_env
sidecar "$DIFF"
grep -qx "diff_id=$DIFF" "$STATE_DIR/.b3-inprogress" 2>/dev/null \
  || { echo "CLONE NOT PREPARED — run p43 fresh $DIFF first — STOPPING"; exit 1; }
# N-02 — a session that STARTS with the clone's auto-memory present is VOID
test ! -e "$MEM" || { echo "AUTO-MEMORY FOR $CLONE IS NOT PARKED — STOPPING"; exit 1; }
snap_verify
if command -v tmux > /dev/null && tmux has-session -t "=p43-$DIFF" 2> /dev/null; then
  echo "TMUX SESSION p43-$DIFF STILL EXISTS — a previous measured session is alive; /exit it and kill it — STOPPING"
  exit 1
fi
LAUNCH_LINE="claude --permission-mode manual --plugin-dir \"$PLUGIN_ROOT\" --model 'claude-fable-5-1[1m]' --allowedTools \"Bash,Read,Write,Edit,Grep,Glob,Task,Agent\""
echo 'Paste form (a NEW terminal tab):'
echo ''
echo "  cd $CLONE && $LAUNCH_LINE"
echo ''
echo 'Driver form (D-13):'
echo ''
echo "  tmux new-session -d -s \"p43-$DIFF\" -c $CLONE"
echo "  tmux send-keys -t \"p43-$DIFF\" '<the launch line above>' Enter"
echo ''
if test "${LAUNCH_VIA_TMUX:-0}" = 1; then
  command -v tmux > /dev/null || { echo 'tmux NOT INSTALLED — STOPPING'; exit 1; }
  tmux new-session -d -s "p43-$DIFF" -c "$CLONE"
  tmux send-keys -t "p43-$DIFF" "$LAUNCH_LINE" Enter
  echo "launched in tmux session p43-$DIFF (read it with: tmux capture-pane -p -t p43-$DIFF)"
fi
echo "When the session is ready: p43 fingerprint $DIFF"
echo 'BLOCK OK'
# END: launch
```

### fingerprint `<diff>` (after EVERY launch)

Appends one session block to `RUN-METHOD-NOTES-phase43.md` and commits it (the contract is in that
file). Three values are read from stdin, one per line: the model exactly as the session shows it
(a trailing ` (1M context)` is stripped before the grammar check), the context window as `/model`
or `/context` shows it (must be `1M`), and the driver (`assistant-tmux` in Phase 43). If the 1M
launch suffix was rejected, select the 1M variant in `/model` and re-run this block.

```bash
# BLOCK: fingerprint
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
load_env
snap_verify
git -C "$REPO" diff --quiet -- "$NOTES" && git -C "$REPO" diff --cached --quiet -- "$NOTES" \
  || { echo 'THE PHASE-43 NOTES FILE HAS UNCOMMITTED CHANGES — STOPPING'; exit 1; }
test -n "$TIMEOUT_BIN" || { echo 'NO timeout BINARY — STOPPING'; exit 1; }
# the harness tuple — a failed probe is a stop, never a fallback value
CC=$(claude --version) || { echo 'claude --version FAILED — STOPPING'; exit 1; }
test -n "$CC" || { echo 'EMPTY claude VERSION — STOPPING'; exit 1; }
CX=$(codex --version) || { echo 'codex --version FAILED — STOPPING'; exit 1; }
printf '%s' "$CX" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+' \
  || { echo 'CODEX VERSION LACKS A FULL x.y.z — STOPPING'; exit 1; }
CXC=$(python3 - "$HOME/.claude/plugins/installed_plugins.json" <<'PY'
import json, sys
entries = json.load(open(sys.argv[1]))["plugins"]["codex@openai-codex"]
assert isinstance(entries, list) and len(entries) == 1, "codex companion not installed exactly once"
print(entries[0]["version"])
PY
) || { echo 'CODEX COMPANION VERSION UNREADABLE — STOPPING'; exit 1; }
AUTOUPDATE=$("$TIMEOUT_BIN" 60 claude doctor < /dev/null 2>&1 | grep '^Auto-updates:' | head -1 || true)
printf '%s' "$AUTOUPDATE" | grep -q 'disabled' \
  || { echo 'AUTO-UPDATES ARE NOT DISABLED (p43 freeze) — STOPPING'; exit 1; }
printf "model, exactly as the session shows it (e.g. 'Fable 5.1 (1M context)'): "
IFS= read -r MODEL_SHOWN
printf "context window, as /model or /context shows it (must be 1M): "
IFS= read -r WINDOW
printf "driver (assistant-tmux or owner): "
IFS= read -r DRIVER
MODEL=${MODEL_SHOWN% (1M context)}
printf '%s' "$MODEL" | grep -qiE '^(claude[- ])?(fable)[- ]5\.1$' \
  || { echo 'MODEL VALUE IS NOT EXACTLY FABLE 5.1 — STOPPING'; exit 1; }
! printf '%s' "$MODEL" | grep -qiE '<|>|record|TBD|placeholder' \
  || { echo 'MODEL VALUE IS A PLACEHOLDER — STOPPING'; exit 1; }
printf '%s' "$DRIVER" | grep -qxE 'assistant-tmux|owner' \
  || { echo 'DRIVER MUST BE assistant-tmux OR owner — STOPPING'; exit 1; }
# the pins, parsed from the COMMITTED notes blob (never the live file)
BLOB=$(git -C "$REPO" show "HEAD:$NOTES") \
  || { echo 'PHASE-43 NOTES FILE NOT COMMITTED — STOPPING'; exit 1; }
for L in pin-claude-code pin-codex pin-model pin-codex-companion pin-context-window; do
  test "$(printf '%s\n' "$BLOB" | grep -c "^$L: ")" = "1" \
    || { echo "PIN LINE $L NOT EXACTLY ONCE — STOPPING"; exit 1; }
done
pin() { printf '%s\n' "$BLOB" | grep "^$1: " | sed "s/^$1: //"; }
DRIFT='report it before running anything'
test "$CC" = "$(pin pin-claude-code)" \
  || { echo "HARNESS DRIFT — claude-code '$CC' is not the pin — STOPPING; $DRIFT"; exit 1; }
test "$CX" = "$(pin pin-codex)" \
  || { echo "HARNESS DRIFT — codex '$CX' is not the pin — STOPPING; $DRIFT"; exit 1; }
test "$CXC" = "$(pin pin-codex-companion)" \
  || { echo "HARNESS DRIFT — codex companion '$CXC' is not the pin — STOPPING; $DRIFT"; exit 1; }
test "$WINDOW" = "$(pin pin-context-window)" \
  || { echo "CONTEXT WINDOW '$WINDOW' IS NOT THE PINNED 1M — select the 1M model in /model — STOPPING"; exit 1; }
NORM=$(printf '%s' "$MODEL" | tr 'A-Z-' 'a-z ' | tr -s ' ')
EXACT=$(printf '%s' "$NORM" | sed -E 's/^claude //')
test "$EXACT" = "$(pin pin-model)" \
  || { echo "HARNESS DRIFT — model '$MODEL' is not the pin — STOPPING; $DRIFT"; exit 1; }
# every earlier Phase-43 session must have run the same model (this file only)
printf '%s\n' "$BLOB" | { grep '^model: ' || true; } | sed 's/^model: //' > "$HOME/.b3/p43-models.out"
while IFS= read -r PRIOR; do
  test -n "$PRIOR" || continue
  PNORM=$(printf '%s' "$PRIOR" | tr 'A-Z-' 'a-z ' | tr -s ' ')
  test "$PNORM" = "$NORM" \
    || { echo "HARNESS DRIFT — an earlier session ran '$PRIOR' — STOPPING; $DRIFT"; exit 1; }
done < "$HOME/.b3/p43-models.out"
SID_NEW=$(date '+%Y-%m-%dT%H:%M:%S%z')
{
  printf '\n## Harness fingerprint — %s\n' "$SID_NEW"
  printf 'claude-code: %s\n' "$CC"
  printf 'model: %s\n' "$MODEL"
  printf 'context-window: %s\n' "$WINDOW"
  printf 'codex: %s\n' "$CX"
  printf 'codex-companion: %s\n' "$CXC"
  printf 'autoupdate: %s\n' "$AUTOUPDATE"
  printf 'batch-sha: %s\n' "$BATCH_SHA"
  printf 'snapshot-root: %s\n' "$SNAP_ROOT"
  printf 'plugin-root: %s\n' "$PLUGIN_ROOT"
  printf 'driver: %s\n' "$DRIVER"
  printf 'session: %s %s\n' "$LABEL" "$DIFF"
} >> "$REPO/$NOTES"
commit_one "runs(43): harness fingerprint $SID_NEW ($LABEL $DIFF)" "$NOTES"
echo "session $SID_NEW fingerprinted"
echo 'BLOCK OK'
# END: fingerprint
```

---

## 7. Per run

Each run is: `/clear` in the session (wait until it completes) → `printf 'CLEARED\n' | p43 pre
<diff> <n>` → `/vibe-check:deep-review` in the session, Step A `4`, Step C `3` → `p43 post <diff>
<n>`. A committed run holds exactly this file set:

- `clear.txt`, `session.txt` (written by `pre`);
- `state.json`, `tree.diff`, `tree.diff.sha256`, `report.md`, `transcript.jsonl.sha256` (as in
  Phase 41);
- `lanes.json` (every dispatched lane's raw return, verbatim) and `context.txt` (the peak context of
  the session), both from `lanearchive.py`;
- exactly ONE of: `codex-payload.json` AND `codex-rc.txt` (Codex joined), or `codex-absent.txt`
  (Codex skipped or off, naming the persisted status and reason).

`transcript.jsonl` (the session plus every agent's sub-transcript) stays on this machine and is
gitignored: a Claude Code transcript carries the owner's private global instructions verbatim. The
committed `transcript.jsonl.sha256` binds the local file to the run.

### pre `<diff>` `<n>`

```bash
# BLOCK: pre
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
case "$RUN_N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
retune_member "$DIFF"
load_env
sidecar "$DIFF"
RP=$RUNS/$DIFF/run-$RUN_N
RUN_DIR=$REPO/$RP
if test "$RUN_N" -gt 1; then
  test -n "$(git -C "$REPO" log -1 --format=%H -- "$RUNS/$DIFF/run-$((RUN_N - 1))/state.json")" \
    || { echo "RUN $((RUN_N - 1)) IS NOT COMMITTED YET — STOPPING"; exit 1; }
fi
# (1) the snapshot, re-verified immediately before this run
snap_verify
# (2) every sealed tree intact
sealed_trees
# (3) the clone: this diff, detached at its base, exactly base + patch, no state file, lock held
cd "$CLONE"
grep -qx "diff_id=$DIFF" "$STATE_DIR/.b3-inprogress" 2>/dev/null \
  || { echo "CLONE NOT PREPARED FOR THIS DIFF — run p43 fresh $DIFF — STOPPING"; exit 1; }
test -z "$(git branch --show-current)" || { echo 'CLONE NOT DETACHED — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "$BASE_SHA" || { echo 'WRONG BASE — STOPPING'; exit 1; }
test "$(clone_diff_sha)" = "$EXPECTED_SHA" \
  || { echo 'CLONE IS NOT EXACTLY BASE + PATCH — STOPPING'; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo "STATE NOT EMPTY — an unfinished run? p43 fail $DIFF <n> — STOPPING"; exit 1; }
if grep -qx 'lock=1' "$STATE_DIR/.b3-inprogress"; then
  stat -f %Sf "$CLONE/uv.lock" | grep -q uchg || { echo 'uv.lock UNPROTECTED — STOPPING'; exit 1; }
fi
# only voided/failed siblings may already exist for this slot
test ! -e "$RUN_DIR" \
  || { echo "RUN $RUN_N ALREADY HAS A FOLDER — p43 void or p43 fail it first — STOPPING"; exit 1; }
# (4) N-02 — anything a session wrote to auto-memory since launch is moved aside as evidence
test -f "$MEMPARK_ENV" || { echo 'NO MEMORY PARK RECORD — STOPPING'; exit 1; }
PARKDIR=$(sed -n 's/^PARKDIR=//p' "$MEMPARK_ENV")
test -d "$PARKDIR" || { echo 'THE MEMORY PARK DIR IS MISSING — STOPPING'; exit 1; }
if test -e "$MEM"; then
  EVID=$PARKDIR/$CN-written-before-$LABEL-$DIFF-run-$RUN_N-$(date +%s)
  while test -e "$EVID"; do sleep 1; EVID=$PARKDIR/$CN-written-before-$LABEL-$DIFF-run-$RUN_N-$(date +%s); done
  mv "$MEM" "$EVID"
  echo "auto-memory written during this window moved aside to $EVID (evidence, never merged back)"
fi
test ! -e "$MEM" || { echo 'AUTO-MEMORY STILL PRESENT — STOPPING'; exit 1; }
# (5) N-01 — the typed attestation, AFTER /clear has completed in the session
echo 'In the measured session: /clear, and wait until it has completed. For EVERY run.'
printf 'Type CLEARED to confirm the /clear completed JUST NOW: '
IFS= read -r ACK
test "$ACK" = "CLEARED" || { echo 'NOT CLEARED — STOPPING'; exit 1; }
mkdir -p "$RUN_DIR"
printf '%s CLEARED\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" > "$RUN_DIR/clear.txt"
# (6) session binding from the COMMITTED notes blob: this snapshot, this window, this diff
BLOB=$(git -C "$REPO" show "HEAD:$NOTES")
HDR='^## Harness fingerprint — [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}[+-][0-9]{4}$'
SID=$(printf '%s\n' "$BLOB" | { grep -E "$HDR" || true; } | tail -1 | sed 's/^## Harness fingerprint — //')
test -n "$SID" || { echo "NO COMMITTED FINGERPRINT — p43 fingerprint $DIFF — STOPPING"; exit 1; }
FPC=$(git -C "$REPO" log --format=%H --reverse -S"## Harness fingerprint — $SID" -- "$NOTES" | head -1 || true)
test -n "$FPC" || { echo 'FINGERPRINT COMMIT NOT FOUND — STOPPING'; exit 1; }
BLK=$(printf '%s\n' "$BLOB" | awk -v h="## Harness fingerprint — $SID" '$0==h{f=1;next} /^## /{f=0} f')
printf '%s\n' "$BLK" | grep -qxF "batch-sha: $BATCH_SHA" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER SNAPSHOT — STOPPING'; exit 1; }
printf '%s\n' "$BLK" | grep -qxF "plugin-root: $PLUGIN_ROOT" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER PLUGIN ROOT — STOPPING'; exit 1; }
printf '%s\n' "$BLK" | grep -qxF "session: $LABEL $DIFF" \
  || { echo "LATEST FINGERPRINT IS NOT FOR THIS SESSION — p43 fingerprint $DIFF — STOPPING"; exit 1; }
printf '%s\n' "$BLK" | grep -qxE 'driver: (assistant-tmux|owner)' \
  || { echo 'LATEST FINGERPRINT RECORDS NO DRIVER — STOPPING'; exit 1; }
printf '%s\n%s\n' "$SID" "$FPC" > "$RUN_DIR/session.txt"
echo "run $RUN_N of $DIFF ready — in the session: /vibe-check:deep-review"
echo 'Decline every fix: Step A option 4 (Skip fixes this pass), Step C option 3 (Abandon for now).'
echo "Then: p43 post $DIFF $RUN_N"
echo 'BLOCK OK'
# END: pre
```

### post `<diff>` `<n>`

Captures, checks, archives and commits the run. The order matters: every check that can refuse
runs BEFORE anything is staged. A refusal before the commit leaves the run uncommitted on disk
(never deleted); redo it via `p43 fail <diff> <n>` (or `void` if no review ran). The state-shape
check runs LAST, after the commit: a FAIL there is a RESULT recorded on a committed run, not a void
run (Phase-41 precedent).

**The lane and Codex archive.** `lanearchive.py extract` writes `lanes.json`, `context.txt` and the
Codex files. It cross-checks the Codex disposition against the run's own `state.json` (a `joined`
run must yield the payload and an `rc` of 0) and runs its privacy scan on everything it wrote; any
refusal deletes what it wrote and exits non-zero. The block then scans every file it is about to
stage. On a privacy hit the block prints `PRIVACY SCAN REFUSED` with the token KIND only (`email`,
`token`, `nas-host`, …), never the matched text, and STOPS: nothing is staged, and nothing is ever
staged by hand to get past it.

**The driver-contamination check (D-13).** The check classifies each `user` record of the local
transcript by its RECORD PROVENANCE, never by content alone. The discriminators were read off the
local transcripts `runs-v2.10-phase41/final/should-quiet-1/run-1/transcript.jsonl` and
`runs-v2.10-phase40/final/should-quiet-5/run-1/transcript.jsonl` on 2026-09-30 (both sha-bound to
their committed `transcript.jsonl.sha256`), and the block re-asserts them on the Phase-41 one
before every use: it must still classify as `none` with at least 13 harness-skipped records, or the
block STOPS.

- **Harness-originated (skipped):** a `message.content` list made only of `tool_result` blocks; a
  sidechain record (`isSidechain` true or an `agentId` key: the subagent dispatch prompts
  `You are the … agent …`); an `isMeta` record (`<local-command-caveat>`, injected skill text); an
  async return (`origin.kind == "task-notification"`, `turnOrigin == "task_notification"` or
  `promptSource == "system"` — these arrive as STRING content `<task-notification>…<result>…`, the
  records `replay.py` recovers findings from); and, ONLY when the record carries none of the
  `origin` / `turnOrigin` / `promptSource` keys, a string starting with `<task-notification>`,
  `<result>`, `<local-command-caveat>` or `<system-reminder>`.
- **Driver input (checked):** everything else, including every `origin.kind == "human"` /
  `turnOrigin == "human"` record regardless of its content (a human-origin `<result>…` paste IS
  contamination), and records with no provenance keys at all (the shape `/clear` is recorded in).
  Each must be a `<command-name>` block for `/clear`, `/vibe-check:deep-review` or `/exit` with
  empty or absent `<command-args>`, or, trimmed, exactly `4`, `3`, `/exit`, `/clear` or
  `/vibe-check:deep-review`.
- **Fix-loop answers (checked):** every `AskUserQuestion` result must answer `Skip fixes this pass`
  or `Abandon for now` with no free-text annotation.
- **Completeness:** at least one harness-skipped async return must exist; a deep-review transcript
  without one is not complete (`driver contamination: UNVERIFIABLE (no async returns)`).

```bash
# BLOCK: post
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
case "$RUN_N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
load_env
sidecar "$DIFF"
RP=$RUNS/$DIFF/run-$RUN_N
RUN_DIR=$REPO/$RP
cd "$CLONE"
grep -qx "diff_id=$DIFF" "$STATE_DIR/.b3-inprogress" 2>/dev/null \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "$BASE_SHA" \
  || { echo 'HEAD MOVED DURING THE RUN (was a fix committed?) — STOPPING'; exit 1; }
test -z "$(git -C "$REPO" log -1 --format=%H -- "$RP/")" \
  || { echo "RUN $RUN_N IS ALREADY COMMITTED — STOPPING"; exit 1; }
# the snapshot is still byte-identical after the run
snap_verify
# the pre-run records exist (this block never writes them)
test -f "$RUN_DIR/clear.txt" || { echo "clear.txt MISSING — p43 void $DIFF $RUN_N — STOPPING"; exit 1; }
test -f "$RUN_DIR/session.txt" || { echo "session.txt MISSING — p43 void $DIFF $RUN_N — STOPPING"; exit 1; }
# the ONE state file this run wrote (every older one was parked by fresh)
NEW=$(find "$STATE_DIR" -maxdepth 1 -name '*.json' -newer "$RUN_DIR/clear.txt")
test "$(printf '%s\n' "$NEW" | grep -c .)" = "1" \
  || { echo 'EXPECTED EXACTLY ONE NEW STATE FILE (none = no review: p43 void) — STOPPING'; exit 1; }
test "$(find "$STATE_DIR" -maxdepth 1 -name '*.json' | grep -c .)" = "1" \
  || { echo 'AN OLDER STATE FILE IS PRESENT — STOPPING'; exit 1; }
STATE_FILE=$NEW
STATE_KEY=$(basename "$STATE_FILE")
cp "$STATE_FILE" "$RUN_DIR/state.json"
# ordering: clear.txt and the fingerprint commit both precede the review's pass timestamp
FPC=$(sed -n 2p "$RUN_DIR/session.txt")
FPCT=$(git -C "$REPO" log -1 --format=%ct "$FPC" || true)
test -n "$FPCT" || { echo 'FINGERPRINT COMMIT NOT IN HISTORY — STOPPING'; exit 1; }
python3 - "$RUN_DIR/clear.txt" "$FPCT" "$RUN_DIR/state.json" <<'PY' \
  || { echo 'ATTESTATION/FINGERPRINT POSTDATES THE RUN — STOPPING'; exit 1; }
import datetime as dt, json, sys
c = dt.datetime.strptime(open(sys.argv[1]).read().split()[0], "%Y-%m-%dT%H:%M:%S%z")
f = dt.datetime.fromtimestamp(int(sys.argv[2]), dt.timezone.utc)
p = json.load(open(sys.argv[3]))["passes"][-1]["timestamp"].replace("Z", "+00:00")
p = dt.datetime.fromisoformat(p)
assert c < p, "clear.txt does not precede the pass"
assert f < p, "fingerprint does not precede the pass"
print("OK pre-run records precede the pass timestamp")
PY
# the FULL tracked diff equals the planted diff and nothing else
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "$EXPECTED_SHA" \
  || { echo 'FULL WORKTREE DIFF != THE PLANTED DIFF — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "$TOUCHED" \
  || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/' || true)" \
  || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — STOPPING'; exit 1; }
# isolation: exactly one pass, at the pinned head
python3 - "$RUN_DIR/state.json" "$BASE_SHA" <<'PY' \
  || { echo 'NOT ONE ISOLATED PASS AT THE PINNED HEAD — STOPPING'; exit 1; }
import json, sys
s = json.load(open(sys.argv[1]))
assert len(s["passes"]) == 1, "NOT ISOLATED: passes=%d" % len(s["passes"])
assert s["passes"][-1]["head_sha"] == sys.argv[2], "HEAD MISMATCH"
print("OK one isolated pass at", sys.argv[2])
PY
# CAPTURE — the session transcript (+ every agent sub-transcript) and the rendered report
test -d "$PROJ" || { echo "NO CLAUDE CODE TRANSCRIPT FOLDER FOR $CLONE — STOPPING"; exit 1; }
MAIN=$(find "$PROJ" -maxdepth 1 -name '*.jsonl' -newer "$RUN_DIR/clear.txt")
test "$(printf '%s\n' "$MAIN" | grep -c .)" = "1" \
  || { echo 'EXPECTED EXACTLY ONE SESSION TRANSCRIPT SINCE /clear — STOPPING'; exit 1; }
grep -q 'vibe-check:deep-review' "$MAIN" \
  || { echo 'THE TRANSCRIPT HOLDS NO /vibe-check:deep-review — STOPPING'; exit 1; }
python3 - "$MAIN" "$RUN_DIR" <<'PY' || { echo 'TRANSCRIPT CAPTURE FAILED — STOPPING'; exit 1; }
import glob, json, os, sys
main, run_dir = sys.argv[1], sys.argv[2]
subs = sorted(glob.glob(os.path.join(main[:-len(".jsonl")], "subagents", "*.jsonl")))
texts = []
with open(os.path.join(run_dir, "transcript.jsonl"), "w") as out:
    for path in [main] + subs:
        for line in open(path):
            if not line.strip():
                continue
            out.write(line if line.endswith("\n") else line + "\n")
            if path != main:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if obj.get("type") != "assistant" or obj.get("isSidechain"):
                continue
            content = (obj.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
with open(os.path.join(run_dir, "report.md"), "w") as fh:
    fh.write("\n\n".join(texts) + "\n")
print("captured %d transcript file(s), %d report block(s)" % (1 + len(subs), len(texts)))
PY
test -s "$RUN_DIR/report.md" || { echo 'EMPTY REPORT — STOPPING'; exit 1; }
test -s "$RUN_DIR/transcript.jsonl" || { echo 'EMPTY TRANSCRIPT — STOPPING'; exit 1; }
git -C "$REPO" check-ignore -q "$RP/transcript.jsonl" \
  || { echo 'transcript.jsonl IS NOT GITIGNORED — nothing staged — STOPPING'; exit 1; }
BAD='(turingmind-code-review/plugins/vibe-check|plugins/cache/thejuran/vibe-check)'
! grep -qE "$BAD" "$RUN_DIR/transcript.jsonl" \
  || { echo 'RUN TOUCHED A NON-SNAPSHOT PLUGIN PATH — RUN IS VOID — STOPPING'; exit 1; }
grep -qF "$PLUGIN_ROOT" "$RUN_DIR/transcript.jsonl" \
  || { echo 'TRANSCRIPT NEVER NAMES THE SNAPSHOT PLUGIN — RUN IS VOID — STOPPING'; exit 1; }
shasum -a 256 "$RUN_DIR/transcript.jsonl" | awk '{print $1}' > "$RUN_DIR/transcript.jsonl.sha256"
# DRIVER CONTAMINATION — classify every user record by its provenance (D-13)
DRIVER_PY=$HOME/.b3/p43-driver-check.py
cat > "$DRIVER_PY" <<'DRIVERPY'
import json, re, sys

ALLOWED_TEXT = {"4", "3", "/exit", "/clear", "/vibe-check:deep-review"}
ALLOWED_CMDS = {"/clear", "/vibe-check:deep-review", "/exit"}
ALLOWED_ANSWERS = {"Skip fixes this pass", "Abandon for now"}
ENVELOPE_TAGS = ("<task-notification>", "<result>", "<local-command-caveat>", "<system-reminder>")
PROVENANCE_KEYS = ("origin", "turnOrigin", "promptSource")
CMD_TAG = re.compile(r"<(command-name|command-message|command-args)>(.*?)</\1>", re.DOTALL)


def human(rec):
    o = rec.get("origin")
    return (isinstance(o, dict) and o.get("kind") == "human") or rec.get("turnOrigin") == "human"


def notification(rec):
    o = rec.get("origin")
    return ((isinstance(o, dict) and o.get("kind") == "task-notification")
            or rec.get("turnOrigin") == "task_notification"
            or rec.get("promptSource") == "system")


def harness(rec, content):
    """True when the record is harness-originated by its provenance (never driver input)."""
    if human(rec):
        return False
    if rec.get("isSidechain") is True or "agentId" in rec or rec.get("isMeta") is True:
        return True
    if isinstance(content, list):
        return all(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    if notification(rec):
        return True
    if not any(k in rec for k in PROVENANCE_KEYS) and isinstance(content, str):
        return content.strip().startswith(ENVELOPE_TAGS)
    return False


def allowed(text):
    t = text.strip()
    if t in ALLOWED_TEXT:
        return True
    tags = CMD_TAG.findall(t)
    if not tags or CMD_TAG.sub("", t).strip():
        return False
    seen = {}
    for name, body in tags:
        if name in seen:
            return False
        seen[name] = body.strip()
    cmd = seen.get("command-name")
    if cmd not in ALLOWED_CMDS or seen.get("command-args", ""):
        return False
    msg = seen.get("command-message")
    return msg is None or msg == cmd.lstrip("/")


def driver_text(content):
    """The typed text of a driver record, or None when it carries a non-text block."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str):
                parts.append(b["text"])
            elif not (isinstance(b, dict) and b.get("type") == "tool_result"):
                return None
        return "\n".join(parts)
    return None


def main(path):
    typed = skipped = notes = answers = 0
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                print("driver contamination: UNVERIFIABLE (malformed line %d)" % i)
                return 1
            if not isinstance(rec, dict) or rec.get("type") != "user":
                continue
            tur = rec.get("toolUseResult")
            if isinstance(tur, dict) and "answers" in tur:
                vals = list((tur.get("answers") or {}).values())
                if any(v not in ALLOWED_ANSWERS for v in vals) or tur.get("annotations"):
                    print("DRIVER CONTAMINATION — record %d: a fix-loop answer outside the allowed two" % i)
                    return 1
                answers += len(vals)
            msg = rec.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            if harness(rec, content):
                if isinstance(content, str):
                    skipped += 1
                    if notification(rec):
                        notes += 1
                continue
            text = driver_text(content)
            if text is None or not allowed(text):
                print("DRIVER CONTAMINATION — record %d: driver input outside the fixed set (%d chars)"
                      % (i, len(text) if isinstance(text, str) else -1))
                return 1
            typed += 1
    if notes == 0:
        print("driver contamination: UNVERIFIABLE (no async returns)")
        return 1
    print("driver contamination: none (typed=%d harness-skipped=%d answers=%d)" % (typed, skipped, answers))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
DRIVERPY
REF=$REPO/$DD/runs-v2.10-phase41/final/should-quiet-1/run-1/transcript.jsonl
test -f "$REF" || { echo 'THE PHASE-41 REFERENCE TRANSCRIPT IS MISSING LOCALLY — STOPPING'; exit 1; }
test "$(shasum -a 256 "$REF" | awk '{print $1}')" \
   = "$(git -C "$REPO" show "HEAD:$DD/runs-v2.10-phase41/final/should-quiet-1/run-1/transcript.jsonl.sha256")" \
  || { echo 'THE PHASE-41 REFERENCE TRANSCRIPT CHANGED — STOPPING'; exit 1; }
REFOUT=$(python3 "$DRIVER_PY" "$REF") \
  || { echo "$REFOUT"; echo 'THE PROVENANCE SHAPE CHANGED (reference transcript no longer clean) — STOPPING'; exit 1; }
REFSKIP=$(printf '%s' "$REFOUT" | sed -n 's/.*harness-skipped=\([0-9]*\).*/\1/p')
test "${REFSKIP:-0}" -ge 13 \
  || { echo 'THE PROVENANCE SHAPE CHANGED (reference skips fewer than 13) — STOPPING'; exit 1; }
DRIVEROUT=$(python3 "$DRIVER_PY" "$RUN_DIR/transcript.jsonl") || {
  echo "$DRIVEROUT"
  case "$DRIVEROUT" in *UNVERIFIABLE*) echo 'driver contamination: UNVERIFIABLE — STOPPING' ;;
    *) echo "DRIVER CONTAMINATION — STOPPING (then: p43 fail $DIFF $RUN_N)" ;; esac
  exit 1
}
echo "$DRIVEROUT"
# the lane and Codex archive — refuses on a privacy hit or a Codex disposition that disagrees with state
refused() {  # the token KIND or the fixed extraction reason only — lanearchive never prints matched text
  sed -n 's/^privacy scan refused: /PRIVACY SCAN REFUSED — token kind: /p' "$1"
  grep -v '^privacy scan refused: ' "$1" || true
}
python3 "$SCRIPTS/lanearchive.py" extract --transcript "$RUN_DIR/transcript.jsonl" --state "$RUN_DIR/state.json" --out-dir "$RUN_DIR" 2> "$HOME/.b3/p43-lanearchive.err" \
  || { refused "$HOME/.b3/p43-lanearchive.err"; echo 'PRIVACY SCAN REFUSED OR EXTRACT FAILED — DO NOT STAGE — STOPPING'; exit 1; }
# the exact file set, with exactly one of the two Codex dispositions
FIXED='clear.txt context.txt lanes.json report.md session.txt state.json transcript.jsonl.sha256 tree.diff tree.diff.sha256'
if test -e "$RUN_DIR/codex-absent.txt"; then
  test ! -e "$RUN_DIR/codex-payload.json" && test ! -e "$RUN_DIR/codex-rc.txt" \
    || { echo 'BOTH CODEX DISPOSITIONS PRESENT — STOPPING'; exit 1; }
  WANT="$FIXED codex-absent.txt"
else
  test -f "$RUN_DIR/codex-payload.json" && test -f "$RUN_DIR/codex-rc.txt" \
    || { echo 'NEITHER CODEX DISPOSITION IS COMPLETE — STOPPING'; exit 1; }
  WANT="$FIXED codex-payload.json codex-rc.txt"
fi
WANT=$(printf '%s\n' $WANT | LC_ALL=C sort | paste -sd' ' -)
HAVE=$(cd "$RUN_DIR" && find . -mindepth 1 | sed 's|^\./||' | grep -vx 'transcript.jsonl' | LC_ALL=C sort | paste -sd' ' -)
test "$HAVE" = "$WANT" || { echo "RUN FOLDER IS NOT THE FIXED FILE SET ($HAVE) — STOPPING"; exit 1; }
# the privacy scan over EVERY file about to be staged (token kind only, never the text)
STAGE=$(printf "$RUN_DIR/%s\n" $WANT)
python3 "$SCRIPTS/lanearchive.py" scan $STAGE 2> "$HOME/.b3/p43-scan.err" \
  || { refused "$HOME/.b3/p43-scan.err"; echo 'PRIVACY SCAN REFUSED — DO NOT STAGE — STOPPING'; exit 1; }
# the Codex line of this run (D-08): status/reason from state, lanes from lanes.json
CODEX=$(python3 - "$RUN_DIR/state.json" "$RUN_DIR/lanes.json" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))["passes"][-1].get("codex")
lanes = json.load(open(sys.argv[2]))
status = c.get("status", "absent") if isinstance(c, dict) else "absent"
reason = c.get("reason") if isinstance(c, dict) else None
print("%s reason=%s lanes=%d/%d" % (status, reason if isinstance(reason, str) else "null",
                                   lanes["recovered"], lanes["dispatched"]))
PY
)
echo "codex this run: $CODEX   peak context: $(cat "$RUN_DIR/context.txt")"
# clear the state dir for the next run (the pass is archived in the run folder)
rm "$STATE_FILE"
# commit, pathspec-scoped; scope asserted on the commit the pathspec resolves to
git -C "$REPO" add -- "$RP/"
git -C "$REPO" commit -q --only -m "runs(43): $LABEL $DIFF run $RUN_N (state key $STATE_KEY, codex ${CODEX%% *})" -- "$RP/"
RC=$(git -C "$REPO" log -1 --format=%H -- "$RP/")
GOT=$(git -C "$REPO" show --name-only --format= "$RC" | sed "s|^$RP/||" | LC_ALL=C sort | paste -sd' ' -)
test "$GOT" = "$WANT" || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
test -z "$(git -C "$REPO" status --porcelain "$RP/")" \
  || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
sealed_trees
# the clone is still exactly base + patch for the next run
test "$(clone_diff_sha)" = "$EXPECTED_SHA" \
  || { echo 'CLONE DRIFTED AFTER THE RUN — STOPPING'; exit 1; }
echo "run $RUN_N of $DIFF committed ($RC), codex ${CODEX%% *}"
# LAST — the envelope shape. A failure here is a RESULT on a committed run, not a void run.
python3 "$SCRIPTS/state_shape.py" "$RUN_DIR/state.json" --schema future \
  || { echo 'ENVELOPE SHAPE VIOLATION — do NOT re-run; report it — STOPPING'; exit 1; }
echo 'state_shape PASS (future)'
if test "$RUN_N" -lt 3; then
  echo "Next: /clear in the session, then: printf 'CLEARED\\n' | p43 pre $DIFF $((RUN_N + 1))"
else
  echo "Diff done: /exit in the session, tmux kill-session -t p43-$DIFF, then p43 revert $DIFF"
fi
echo 'BLOCK OK'
# END: post
```

### void `<diff>` `<n>` `"<reason>"` (D-10)

For an attempt that died BEFORE any review: credits exhausted, a launch crash, the review never
started, no state file written. The uncommitted run folder is kept as evidence under
`run-<n>.voided-<epoch>/` with a `reason.txt`, committed, and the SAME slot is redone from `pre`.
The reason is one short line (letters, digits, spaces and `,.:()_-`, at most 200 characters). A
run whose review wrote a state file is not voidable: use `fail`.

```bash
# BLOCK: void
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
case "$RUN_N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
printf '%s' "$VOID_REASON" | grep -qE '^[A-Za-z0-9 ,.:()_-]{1,200}$' \
  || { echo 'VOID REASON MUST BE 1-200 CHARACTERS OF [A-Za-z0-9 ,.:()_-] — STOPPING'; exit 1; }
load_env
sidecar "$DIFF"
RP=$RUNS/$DIFF/run-$RUN_N
RUN_DIR=$REPO/$RP
test -z "$(git -C "$REPO" log -1 --format=%H -- "$RP/")" \
  || { echo "RUN $RUN_N IS COMMITTED — it is evidence, not voidable — STOPPING"; exit 1; }
test -d "$RUN_DIR" || { echo "RUN $RUN_N HAS NO FOLDER — nothing to void — STOPPING"; exit 1; }
grep -qx "diff_id=$DIFF" "$STATE_DIR/.b3-inprogress" 2>/dev/null \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — STOPPING'; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo "A STATE FILE EXISTS — THE REVIEW RAN — use p43 fail $DIFF $RUN_N — STOPPING"; exit 1; }
VP=$RP.voided-$(date +%s)
while test -e "$REPO/$VP"; do sleep 1; VP=$RP.voided-$(date +%s); done
mv "$RUN_DIR" "$REPO/$VP"
test ! -e "$REPO/$VP/run-$RUN_N" || { echo 'VOIDED FOLDER NESTED — STOPPING'; exit 1; }
printf '%s\n' "$VOID_REASON" > "$REPO/$VP/reason.txt"
git -C "$REPO" check-ignore -q "$VP/transcript.jsonl" \
  || { echo 'transcript.jsonl IS NOT GITIGNORED IN THE VOIDED FOLDER — STOPPING'; exit 1; }
SCAN=$(cd "$REPO" && git ls-files --others --exclude-standard -- "$VP/")
test -n "$SCAN" || { echo 'NOTHING TO COMMIT IN THE VOIDED FOLDER — STOPPING'; exit 1; }
(cd "$REPO" && python3 "$SCRIPTS/lanearchive.py" scan $SCAN 2> "$HOME/.b3/p43-scan.err") || {
  sed -n 's/^privacy scan refused: /PRIVACY SCAN REFUSED — token kind: /p' "$HOME/.b3/p43-scan.err"
  echo 'PRIVACY SCAN REFUSED — DO NOT STAGE — STOPPING'; exit 1; }
git -C "$REPO" add -- "$VP/"
git -C "$REPO" commit -q --only -m "runs(43): $LABEL $DIFF run $RUN_N VOIDED before review — $VOID_REASON" -- "$VP/"
VC=$(git -C "$REPO" log -1 --format=%H -- "$VP/")
test -z "$(git -C "$REPO" show --name-only --format= "$VC" | grep -v "^$VP/" || true)" \
  || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
git -C "$REPO" show --name-only --format= "$VC" | grep -qx "$VP/reason.txt" \
  || { echo 'reason.txt NOT IN THE VOID COMMIT — STOPPING'; exit 1; }
# the clone is still exactly base + patch, so the same slot can be redone
test "$(git -C "$CLONE" rev-parse HEAD)" = "$BASE_SHA" \
  || { echo "HEAD MOVED — p43 revert $DIFF, then p43 fresh $DIFF — STOPPING"; exit 1; }
test "$(clone_diff_sha)" = "$EXPECTED_SHA" \
  || { echo "CLONE DRIFTED — p43 revert $DIFF, then p43 fresh $DIFF — STOPPING"; exit 1; }
echo "run $RUN_N voided ($VC) — redo the same slot: /clear, then p43 pre $DIFF $RUN_N"
echo 'BLOCK OK'
# END: void
```

### fail `<diff>` `<n>` (N-08)

For a run that crashed, stalled or was refused MID-review, or that `post` refused before its commit
(driver contamination, a provenance void, a failed extract). Whatever the run left — its folder
and the state file it wrote, if any — is committed as `run-<n>.failed-<epoch>/` (pathspec-scoped,
prefix-asserted), the state dir is cleared, the patch and sentinel stay, and the SAME slot is redone
from `pre`. Its first step is DETECT-AND-FINISH: an uncommitted failed sibling left by an
interrupted earlier `fail` is committed before anything else, so re-running it is always safe.

```bash
# BLOCK: fail
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
case "$RUN_N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
load_env
sidecar "$DIFF"
DP=$RUNS/$DIFF
RP=$DP/run-$RUN_N
RUN_DIR=$REPO/$RP
commit_failed() {
  local fp=$1 scan fc
  git -C "$REPO" check-ignore -q "$fp/transcript.jsonl" \
    || { echo 'transcript.jsonl IS NOT GITIGNORED IN THE FAILED FOLDER — STOPPING'; exit 1; }
  scan=$(cd "$REPO" && git ls-files --others --exclude-standard -- "$fp/")
  test -n "$scan" || { echo "NOTHING TO COMMIT IN $fp — STOPPING"; exit 1; }
  (cd "$REPO" && python3 "$SCRIPTS/lanearchive.py" scan $scan 2> "$HOME/.b3/p43-scan.err") || {
    sed -n 's/^privacy scan refused: /PRIVACY SCAN REFUSED — token kind: /p' "$HOME/.b3/p43-scan.err"
    echo 'PRIVACY SCAN REFUSED — DO NOT STAGE — STOPPING'; exit 1; }
  git -C "$REPO" add -- "$fp/"
  git -C "$REPO" commit -q --only -m "runs(43): $LABEL $DIFF ${fp##*/} FAILED — evidence archived" -- "$fp/"
  fc=$(git -C "$REPO" log -1 --format=%H -- "$fp/")
  test -n "$fc" || { echo 'FAILED-EVIDENCE COMMIT NOT RESOLVED — STOPPING'; exit 1; }
  test -z "$(git -C "$REPO" show --name-only --format= "$fc" | grep -v "^$fp/" || true)" \
    || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
  echo "failed evidence committed: $fp ($fc)"
}
# (0) DETECT-AND-FINISH — any uncommitted failed sibling of this diff is committed first
for F in $(git -C "$REPO" status --porcelain --untracked-files=all -- "$DP/" \
    | grep -oE 'run-[0-9]+\.failed-[0-9]+' | sort -u || true); do
  commit_failed "$DP/$F"
done
# (1) the run must be uncommitted, and something must exist to archive
test -z "$(git -C "$REPO" log -1 --format=%H -- "$RP/")" \
  || { echo "RUN $RUN_N IS COMMITTED — it is evidence, never failed — STOPPING"; exit 1; }
grep -qx "diff_id=$DIFF" "$STATE_DIR/.b3-inprogress" 2>/dev/null \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — STOPPING'; exit 1; }
STATES=$(find "$STATE_DIR" -maxdepth 1 -name '*.json')
test -d "$RUN_DIR" || test -n "$STATES" \
  || { echo "RUN $RUN_N LEFT NOTHING TO ARCHIVE — STOPPING"; exit 1; }
test "$(printf '%s\n' "$STATES" | grep -c .)" -le 1 \
  || { echo 'MORE THAN ONE STATE FILE IN THE CLONE — STOPPING'; exit 1; }
# a fresh sibling name: never move INTO an existing sibling (same-second epoch)
FP=$RP.failed-$(date +%s)
while test -e "$REPO/$FP"; do sleep 1; FP=$RP.failed-$(date +%s); done
if test -d "$RUN_DIR"; then mv "$RUN_DIR" "$REPO/$FP"; else mkdir -p "$REPO/$FP"; fi
test ! -e "$REPO/$FP/run-$RUN_N" || { echo 'FAILED FOLDER NESTED — STOPPING'; exit 1; }
if test -n "$STATES"; then
  cp "$STATES" "$REPO/$FP/failed-state.json"
  rm "$STATES"
fi
commit_failed "$FP"
# the clone is still exactly base + patch, so the same slot can be redone
test "$(git -C "$CLONE" rev-parse HEAD)" = "$BASE_SHA" \
  || { echo "HEAD MOVED — p43 revert $DIFF, then p43 fresh $DIFF — STOPPING"; exit 1; }
test "$(clone_diff_sha)" = "$EXPECTED_SHA" \
  || { echo "CLONE DRIFTED — p43 revert $DIFF, then p43 fresh $DIFF — STOPPING"; exit 1; }
echo "run $RUN_N failed and archived — redo the same slot: /clear, then p43 pre $DIFF $RUN_N"
echo 'BLOCK OK'
# END: fail
```

---

## 8. revert `<diff>` (once per diff, after run 3)

Restores the clone to the branch it was on and puts the parked state files back. It does NOT need
an open window, so it is also the abandon-this-diff path. It never touches plugin code.

```bash
# BLOCK: revert
set -euo pipefail
case "$DIFF" in triggarr-secret-in-logs|triggarr-autoescape|third-organic-should-catch|should-quiet-1|should-quiet-2|should-quiet-3|triggarr-session-rotation|triggarr-settings-form-split|should-quiet-4|should-quiet-5|should-quiet-6|should-quiet-7) ;;
  *) echo 'DIFF MUST BE ONE OF THE TWELVE MEASURED DIFF IDS — STOPPING'; exit 1 ;; esac
sidecar "$DIFF"
cd "$CLONE"
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert — STOPPING'; exit 1; }
grep -qx "diff_id=$DIFF" "$STATE_DIR/.b3-inprogress" \
  || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(sed -n 's/^start_branch=//p' "$STATE_DIR/.b3-inprogress")
START_SHA=$(sed -n 's/^start_sha=//p' "$STATE_DIR/.b3-inprogress")
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo "A RUN IS UNFINISHED (state file present) — p43 fail $DIFF <n> — STOPPING"; exit 1; }
# release the lockfile FIRST (this is also the abandon-this-diff path)
if test -f "$CLONE/uv.lock"; then
  chflags nouchg "$CLONE/uv.lock"
  ! stat -f %Sf "$CLONE/uv.lock" | grep -q uchg \
    || { echo 'uv.lock STILL PROTECTED after the clear — STOPPING'; exit 1; }
fi
# scoped revert of the planted diff
git checkout -- .
git clean -fd -e .turingmind -- "$TOUCHED"
git switch -q "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN AFTER THE REVERT — STOPPING'; exit 1; }
# restore the parked state per the sentinel
if grep -qx 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then
  for f in "$PARK"/*.json; do mv -n "$f" "$STATE_DIR/"; done
fi
test -z "$(find "$PARK" -mindepth 1)" \
  || { echo 'PARKED FILES COULD NOT ALL BE RESTORED — STOPPING'; exit 1; }
rmdir "$PARK"
rm "$STATE_DIR/.b3-inprogress"
echo "$DIFF complete — $CLONE back on $START_BRANCH@$START_SHA"
if command -v tmux > /dev/null && tmux has-session -t "=p43-$DIFF" 2> /dev/null; then
  echo "tmux session p43-$DIFF is still alive: /exit it, then tmux kill-session -t p43-$DIFF"
fi
echo 'BLOCK OK'
# END: revert
```

---

## 9. first-pass-close (once per window, after the last revert)

Closes the window's runs against the EXPECTED DIFF SET of its label, never a fixed count:

- `LABEL=first`: all twelve diffs, exactly runs 1–3 each (36 runs).
- `LABEL=retune`: exactly the diffs on the committed `first/FAILED-DIFFS.json`, runs 1–3 each
  (3 × the list). A `retune/` folder for a diff not on the list, or a fourth run, is an extra and
  STOPS; the 36-slot rule is never applied to the retune label.

`score43.py ledger` decides completeness (no holes, no extras; voided and failed siblings are
excluded by name). The block then writes `RUNS-COMPLETE.json` with each run's commit and commits it.
It refuses to overwrite one.

```bash
# BLOCK: first-pass-close
set -euo pipefail
load_env
test ! -e "$REPO/$RUNS/RUNS-COMPLETE.json" \
  || { echo 'RUNS-COMPLETE.json ALREADY WRITTEN — STOPPING'; exit 1; }
for C in $CLONES; do
  test ! -e "$HOME/$C/.turingmind/state/.b3-inprogress" \
    || { echo "~/$C IS STILL MID-DIFF — p43 revert it first — STOPPING"; exit 1; }
done
test -z "$(git -C "$REPO" status --porcelain -- "$RUNS/")" \
  || { echo 'THE RUNS FOLDER HAS UNCOMMITTED CHANGES — STOPPING'; exit 1; }
EXPECT_ARGS=()
if test "$LABEL" = retune; then
  git -C "$REPO" ls-files --error-unmatch "$FIRST_FAILED" > /dev/null 2>&1 \
    || { echo 'FAILED-DIFFS.json IS NOT COMMITTED — STOPPING'; exit 1; }
  git -C "$REPO" show "HEAD:$FIRST_FAILED" > "$HOME/.b3/p43-expected-diffs.json"
  EXPECT_ARGS=(--expected-diffs "$HOME/.b3/p43-expected-diffs.json")
fi
python3 "$SCRIPTS/score43.py" ledger --runs-root "$REPO/$RUNS" ${EXPECT_ARGS[@]+"${EXPECT_ARGS[@]}"} \
  || { echo "THE $LABEL LEDGER IS NOT COMPLETE (holes or extras) — STOPPING"; exit 1; }
python3 - "$REPO" "$RUNS" "$LABEL" "$BATCH_SHA" "$HOME/.b3/p43-expected-diffs.json" <<'PY' \
  || { echo 'RUNS-COMPLETE.json NOT WRITTEN — STOPPING'; exit 1; }
import datetime, hashlib, json, os, subprocess, sys
repo, rel, label, sha, expected_path = sys.argv[1:6]
DIFFS = ["triggarr-secret-in-logs", "triggarr-autoescape", "third-organic-should-catch",
         "should-quiet-1", "should-quiet-2", "should-quiet-3", "triggarr-session-rotation",
         "triggarr-settings-form-split", "should-quiet-4", "should-quiet-5", "should-quiet-6",
         "should-quiet-7"]
if label == "first":
    expected = DIFFS
else:
    listed = json.load(open(expected_path))
    expected = [d for d in DIFFS if d in listed]
    assert expected and len(expected) == len(listed), "FAILED-DIFFS names an unknown or repeated diff"
commits = {}
for d in expected:
    commits[d] = {}
    for n in (1, 2, 3):
        run = os.path.join(rel, d, "run-%d" % n)
        log = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%H", "--",
                              os.path.join(run, "state.json")],
                             stdout=subprocess.PIPE, text=True, timeout=120)
        c = log.stdout.strip()
        assert len(c) == 40, "%s/state.json is not committed" % run
        t = os.path.join(repo, run, "transcript.jsonl")
        got = hashlib.sha256(open(t, "rb").read()).hexdigest()
        assert got == open(t + ".sha256").read().strip(), "%s transcript changed after capture" % run
        commits[d][str(n)] = c
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
out = {"label": label, "snapshot_commit": sha, "expected_diffs": expected,
       "run_commits": commits, "closed_at": now}
with open(os.path.join(repo, rel, "RUNS-COMPLETE.json"), "w") as fh:
    json.dump(out, fh, indent=2)
    fh.write("\n")
print("RUNS-COMPLETE.json: %s, %d diffs x 3 runs" % (label, len(expected)))
PY
commit_one "runs(43): $LABEL window closed — RUNS-COMPLETE.json" "$RUNS/RUNS-COMPLETE.json"
echo 'BLOCK OK'
# END: first-pass-close
```

---

## 10. Restore order after the last run

In this order, after `first-pass-close`: `restore-memory` → `unfreeze` → `restore-cache` →
`close-window` → relaunch Claude Code. `close-window` removes the open-window marker only when ALL
of the earlier steps succeeded, so an interrupted restoration leaves the marker in place: the
window can be resumed and finished, and no new window (in particular the retune window) can be
opened over it.

### restore-memory

Puts the owner's parked memory back. What the window's sessions wrote is kept beside it as
evidence and never merged back. It needs no open window, so it also undoes a `park-memory` when
`preflight` stopped.

```bash
# BLOCK: restore-memory
set -euo pipefail
test -f "$MEMPARK_ENV" || { echo 'NO MEMORY PARK RECORD — nothing to restore — STOPPING'; exit 1; }
PARKDIR=$(sed -n 's/^PARKDIR=//p' "$MEMPARK_ENV")
test -n "$PARKDIR" && test -d "$PARKDIR" || { echo 'THE PARK DIR IS MISSING — STOPPING'; exit 1; }
for C in $CLONES; do
  test ! -e "$HOME/$C/.turingmind/state/.b3-inprogress" \
    || { echo "~/$C IS STILL MID-DIFF — p43 revert it first — STOPPING"; exit 1; }
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
  test ! -e "$PARKDIR/$C" || { echo "~/$C MEMORY NOT RESTORED — STOPPING"; exit 1; }
done
rm "$MEMPARK_ENV"
echo 'BLOCK OK'
# END: restore-memory
```

### unfreeze (D-09)

Restores exactly the state `freeze` recorded (owner default: restore, never force updates on), from
the recorded backups `~/.claude/settings.json.phase43-bak` and `~/.codex/config.toml.phase43-bak`. It
removes only what `freeze` added, then requires the result to equal the recorded backup; if a file
changed during the window for any other reason, it STOPS and keeps the backup rather than
overwriting the change.

```bash
# BLOCK: unfreeze
set -euo pipefail
test -f "$FREEZE_ENV" || { echo 'NOT FROZEN (no phase43-freeze.env) — STOPPING'; exit 1; }
. "$FREEZE_ENV"
test -f "$SETTINGS.phase43-bak" && test -f "$CODEX_CFG.phase43-bak" \
  || { echo 'A phase43-bak BACKUP IS MISSING — STOPPING; report it'; exit 1; }
test -n "$TIMEOUT_BIN" || { echo 'NO timeout BINARY — STOPPING'; exit 1; }
# Codex: drop the line freeze added, then require byte-equality with the backup
if test "$CODEX_KEY_PRESENT" = 0; then
  test "$(head -1 "$CODEX_CFG")" = "$CODEX_LINE" \
    || { echo 'config.toml NO LONGER STARTS WITH THE FREEZE LINE — backup kept — STOPPING'; exit 1; }
  tail -n +2 "$CODEX_CFG" | cmp -s - "$CODEX_CFG.phase43-bak" \
    || { echo 'config.toml CHANGED DURING THE WINDOW — backup kept — STOPPING'; exit 1; }
fi
cp -p "$CODEX_CFG.phase43-bak" "$CODEX_CFG"
cmp -s "$CODEX_CFG" "$CODEX_CFG.phase43-bak" || { echo 'config.toml NOT RESTORED — STOPPING'; exit 1; }
# Claude Code: if freeze added the env key, drop it and require equality with the backup
if test "$CLAUDE_ENV_PRESENT" = 0; then
  python3 - "$SETTINGS" "$SETTINGS.phase43-bak" <<'PY' \
    || { echo 'settings.json CHANGED DURING THE WINDOW — backup kept — STOPPING'; exit 1; }
import json, sys
cur, bak = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
env = cur.get("env") or {}
env.pop("DISABLE_AUTOUPDATER", None)
if not env:
    cur.pop("env", None)
assert cur == bak
PY
  cp -p "$SETTINGS.phase43-bak" "$SETTINGS"
  cmp -s "$SETTINGS" "$SETTINGS.phase43-bak" || { echo 'settings.json NOT RESTORED — STOPPING'; exit 1; }
else
  python3 - "$SETTINGS" <<'PY' \
    || { echo 'DISABLE_AUTOUPDATER WAS REMOVED DURING THE WINDOW — STOPPING; report it'; exit 1; }
import json, sys
assert (json.load(open(sys.argv[1])).get("env") or {}).get("DISABLE_AUTOUPDATER") == "1"
PY
  echo 'Claude Code: auto-update was already disabled before the window; left as recorded'
fi
NOW_LINE=$("$TIMEOUT_BIN" 60 claude doctor < /dev/null 2>&1 | grep '^Auto-updates:' | head -1 || true)
test "$NOW_LINE" = "$CLAUDE_AUTOUPDATE_LINE" \
  || { echo "AUTO-UPDATE STATE '$NOW_LINE' IS NOT THE RECORDED '$CLAUDE_AUTOUPDATE_LINE' — STOPPING"; exit 1; }
rm "$SETTINGS.phase43-bak" "$CODEX_CFG.phase43-bak" "$FREEZE_ENV"
echo "restored the recorded state: $NOW_LINE; codex key present=$CODEX_KEY_PRESENT"
echo 'BLOCK OK'
# END: unfreeze
```

### restore-cache

Puts the released 2.9.0 cache back from the backup (owner default: the everyday reviews return to
the released plugin after the window), proves it with `diff -rq`, removes the backup and records the
restore in the notes.

```bash
# BLOCK: restore-cache
set -euo pipefail
test -d "$CACHE_BAK" || { echo 'NO CACHE BACKUP — nothing to restore — STOPPING'; exit 1; }
test -d "$CACHE" || { echo 'INSTALLED vibe-check 2.9.0 CACHE MISSING — STOPPING'; exit 1; }
git -C "$REPO" diff --quiet -- "$NOTES" && git -C "$REPO" diff --cached --quiet -- "$NOTES" \
  || { echo 'THE PHASE-43 NOTES FILE HAS UNCOMMITTED CHANGES — STOPPING'; exit 1; }
rsync -a --delete --exclude .in_use "$CACHE_BAK/" "$CACHE/"
test -z "$(diff -rq -x .in_use "$CACHE" "$CACHE_BAK" || true)" \
  || { echo 'THE RESTORED CACHE DIFFERS FROM THE BACKUP — backup kept — STOPPING'; exit 1; }
rm -rf "$CACHE_BAK"
notes_append '## Cache parity' "parity: restored released 2.9.0 at $(date '+%Y-%m-%dT%H:%M:%S%z')"
commit_one 'runs(43): installed cache restored to released 2.9.0' "$NOTES"
echo 'RELAUNCH CLAUDE CODE (FULL PROCESS EXIT) so everyday sessions load the restored cache'
echo 'BLOCK OK'
# END: restore-cache
```

### close-window

Removes `~/.b3/phase43-active.env` ONLY after the window's `RUNS-COMPLETE.json` is committed AND
`restore-memory`, `unfreeze` and `restore-cache` have all succeeded, each proven from its own end
state rather than from a flag. Any missing proof STOPS and leaves the marker in place.

```bash
# BLOCK: close-window
set -euo pipefail
load_env
git -C "$REPO" cat-file -e "HEAD:$RUNS/RUNS-COMPLETE.json" 2> /dev/null \
  || { echo "THE $LABEL RUNS-COMPLETE.json IS NOT COMMITTED — window stays open — STOPPING"; exit 1; }
test -z "$(git -C "$REPO" status --porcelain -- "$RUNS/")" \
  || { echo 'THE RUNS FOLDER HAS UNCOMMITTED CHANGES — window stays open — STOPPING'; exit 1; }
for C in $CLONES; do
  test ! -e "$HOME/$C/.turingmind/state/.b3-inprogress" \
    || { echo "~/$C IS STILL MID-DIFF — window stays open — STOPPING"; exit 1; }
done
test ! -e "$MEMPARK_ENV" \
  || { echo 'MEMORY NOT RESTORED (p43 restore-memory) — window stays open — STOPPING'; exit 1; }
test ! -e "$FREEZE_ENV" && test ! -e "$SETTINGS.phase43-bak" && test ! -e "$CODEX_CFG.phase43-bak" \
  || { echo 'NOT UNFROZEN (p43 unfreeze) — window stays open — STOPPING'; exit 1; }
test ! -e "$CACHE_BAK" \
  || { echo 'CACHE NOT RESTORED (p43 restore-cache) — window stays open — STOPPING'; exit 1; }
LASTP=$(git -C "$REPO" show "HEAD:$NOTES" | { grep '^parity: ' || true; } | tail -1)
case "$LASTP" in "parity: restored "*) ;;
  *) echo 'THE NOTES DO NOT RECORD THE CACHE RESTORE LAST — window stays open — STOPPING'; exit 1 ;; esac
rm "$ENV"
echo "window $LABEL closed; a new window may now be opened"
echo 'BLOCK OK'
# END: close-window
```

---

## 11. Your worklog — mechanical facts only

Tick each cell as the blocks report it. There is deliberately no column for how many false alarms
there were: that is the scorer's job. The committed run folders are the evidence; this table is a
worklog.

Columns: `snap` = snapshot re-verified (y/n) · `tree` = tree.diff sha matched (y/n) · `1 pass` =
`len(passes)==1` held (y/n) · `driver` = `none` as printed · `codex` = status and lanes as printed ·
`ctx` = peak context · `shape` = `state_shape` result · `commit` = the run commit.

| diff | run | snap | tree | 1 pass | driver | codex | ctx | shape | commit |
|---|---|---|---|---|---|---|---|---|---|
| triggarr-secret-in-logs | 1–3 | | | | | | | | |
| triggarr-autoescape | 1–3 | | | | | | | | |
| third-organic-should-catch | 1–3 | | | | | | | | |
| should-quiet-1 | 1–3 | | | | | | | | |
| should-quiet-2 | 1–3 | | | | | | | | |
| should-quiet-3 | 1–3 | | | | | | | | |
| triggarr-session-rotation | 1–3 | | | | | | | | |
| triggarr-settings-form-split | 1–3 | | | | | | | | |
| should-quiet-4 | 1–3 | | | | | | | | |
| should-quiet-5 | 1–3 | | | | | | | | |
| should-quiet-6 | 1–3 | | | | | | | | |
| should-quiet-7 | 1–3 | | | | | | | | |

Voided and failed attempts are listed under the slot they belong to, with their commit.

## 12. The retune window (only after a missed bar)

The retune is opened only after the first window is closed (`close-window` succeeded, so the
marker is gone) and after `FAILED-DIFFS.json` and the retune commit are committed in that order
(D-07; `score43.py retune-gate` checks it). The batch-6 snapshot is built and recorded as a
`snapshot: batch6 …` line in the notes. Then every block runs with `LABEL=retune`: `park-memory`,
`freeze`, `resync-cache`, relaunch, `preflight`, then only the failed diffs (`fresh` refuses any
other), three runs each, `first-pass-close` against the failed-diff list, and the same restore
order and `close-window`.
