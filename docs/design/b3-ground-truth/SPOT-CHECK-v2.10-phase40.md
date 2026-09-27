# Phase-40 spot-check runbook — v2.10 (12 owner runs, one file)

**Purpose:** every live check Phase 40 needs, as copy-paste blocks: which two diffs, which commands,
what each run is compared against, and where each result lands. Every gate below is an OWNER action;
the assistant never invokes `/deep-review`.

Batch snapshots, barriers and PLUGIN rollback live in `BATCH-LIFECYCLE-v2.10-phase40.md`; this file
is the runs.

---

## 1. The run budget — 12 runs (D-05, D-06)

| Check | Runs | When | Plans that have landed |
|---|---|---|---|
| `batch1` | 2 (catch ×1, quiet ×1) | before 40-08 starts | 40-02..05, 40-07, 40-12, 40-13 |
| `batch2` | 2 (catch ×1, quiet ×1) | before 40-11 starts | + 40-08, 40-10 |
| `batch3` | 2 (catch ×1, quiet ×1) | before 40-14 closes the phase | + 40-11 |
| `final` | 6 (catch ×3, quiet ×3) | after batch 3, at phase exit | all of the above |
| **total** | **12** | | |

The `final` check runs against the batch-3 snapshot (nothing changes the plugin after 40-11). If a
rollback changed the plugin after batch 3, the assistant rebuilds the batch-3 snapshot first.

---

## 2. What you record, and what you do NOT (read this before run 1)

You are not asked to decide whether a finding counts as a catch. Capture the report and the
transcript; the assistant scores them against the sealed key.

| Recorded by | What | Why |
|---|---|---|
| OWNER (mechanical) | the seven facts listed first below | exit codes, string equality |
| ASSISTANT (judgement) | the four verdicts listed second below | needs engineering judgement |

- **OWNER (mechanical):** did the command complete; `state_shape.py` exit code; `tree.diff` sha
  match; touched-path match; `len(passes)==1`; the run's rendered report captured verbatim to
  `report.md`; the full transcript captured to `transcript.jsonl`. Why: all are exit codes or
  string equality — no judgement.
- **ASSISTANT (judgement):** SITE / AXIS / BAND per the sealed key incl. the NOT-clause; per-run
  catch/miss verdict; per-run quiet clean/FP verdict; the batch verdict. Why: requires reading
  findings against a sealed answer key and applying an exclusion rule; this is engineering
  judgement.

Every block below does the mechanical part for you: it either prints `BLOCK OK` or stops with a
line ending in `STOPPING`. Your job is to run the blocks in order, do the one Claude Code action
per run, and hand the result to the assistant.

**What the assistant is going to do with what you captured** — written down here so the scoring is
recorded in advance rather than improvised (from `SCORING-v2.10.md` §3 and §4):

- **catch** = SITE (right file, within the planted hunk, keyed to the row's base_sha) AND AXIS
  (names the required MECHANISM, honoring the row's NOT-clause) AND BAND (rendered band ≥ the
  row's floor). SITE-only, or SITE+AXIS-below-band, = `detected-below-threshold` = a MISS.
  For `triggarr-secret-in-logs`: SITE `triggarr/clients/base.py` : 230-238 / 249-256 · AXIS =
  secret/API-key/PII leaked into logs, **NOT** "log formatting" · BAND floor = warning.
- **FP on a quiet diff** = ANY finding at band critical OR warning (not site-gated). Medium/low
  are noise-notes: recorded, not counted. **The quiet FP rate counts RUNS WITH ANY
  critical/warning finding — not the number of findings.** A run with three warnings is ONE FP
  run, not three.

---

## 3. The sensitivity pair, with its evidence (D-05)

- **should-catch = `triggarr-secret-in-logs`** — LEAST HEADROOM. In all three Phase-38 baseline
  runs the top finding was codex-adversarial (critical 96-100), and the best NATIVE finding
  cleared the warning floor (80) by the smallest margin in the whole set: `impact` warning **82**
  in run 1 (`bugs` 72 was sub-floor), 88 in run 2, 85 in run 3. It is codex-led, so it also
  directly exercises the Family-3 extraction (40-04) and the deep-review Phase-3 rewrite (40-11).
  Baseline: **3/3 catch**.
  base_sha `f4366a261fcf9bab01b48ad89279aac973a7d9b1`, source repo `~/triggarr`,
  EXPECTED_TREE_DIFF_SHA256 `f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2`,
  EXPECTED_TOUCHED_PATHS `triggarr/clients/base.py`.
  (Runner-up, NOT selected: `triggarr-autoescape` — the only diff with a historical miss (v2.9:
  2/3), native winners 82-92. Recorded in ledger entry 005 so the choice is auditable.)
- **should-quiet = `should-quiet-5`** — MOST LIKELY TO FLIP. The ONLY quiet diff not at 3/3 FP:
  **1/3** (clean, FP, clean). Its single FP is the "out-of-diff reach" class (a `warning 92` on a
  neighbouring test file) — governed by exactly the in_diff / reviewed-set prose 40-08 rewrites.
  Baseline: **1/3 FP**. base_sha `70354771a331f7def6c8116556f58d865f644cd9`, source repo
  `~/seedsyncarr`, EXPECTED_TREE_DIFF_SHA256
  `8af04cc658b5a672d2d6be7af9fc042aae81742c56a01a5d030e4d86ea630060`,
  EXPECTED_TOUCHED_PATHS `src/python/model/model.py`.
  (NOT selected: `should-quiet-7` is EXCLUDED per D-01 / ledger entry 001; `should-quiet-6` is
  the most STABLE FP — byte-identical codex title at critical/100 ×3 — and cannot get worse, so
  it carries no signal.)

**Comparison rule (D-05):** each diff is judged against its OWN Phase-38 triplet. "Catch-rate no
worse" = `triggarr-secret-in-logs` stays 3/3 at phase end. The FP direction is informational at ×1
per batch and judged at ×3 at phase end; Phase 43 remains the real proof.

---

## MEASUREMENT-RUN RULE — the `/deep-review` fix loop + N-01 (read this FIRST)

**When `/deep-review` finds something it will enter an interactive Phase 5 fix loop. On EVERY
run you DECLINE/SKIP all fixes and EXIT the loop WITHOUT applying:** at Step A ("How do you
want to handle the N finding(s) above?") pick **"Skip fixes this pass"** (option 4); at Step C
("Pass N loop — what's next?") pick **"Abandon for now"** (option 3). Do NOT pick "Rerun
review on the new diff" (a re-run appends a second pass and breaks the `len(passes)==1`
sample). Do NOT pick "Close out and document" / `--finalize`. Do NOT let the fix agent commit
anything into the source repo (a commit moves HEAD off the pinned base_sha and fails the head
assert). You are MEASURING the tool, not fixing the code.

**N-01 — conversation isolation (mandatory, per run):** `/clear` (or a fresh conversation)
immediately before EVERY `/deep-review` run — run 2 and 3 of a diff, retries after a failed
run, and resumed sessions included. Clearing state.json does not erase model memory; a
same-conversation replicate can leak earlier findings while every state-level gate still
passes. Each per-run block runs a fixed PRE-RUN sequence — state-fresh check first, then a
typed CLEARED attestation into the run's clear.txt, then the session binding into
session.txt — ALL before the run may be triggered: the session fingerprint proves the
harness, clear.txt proves each run's conversation boundary, and the ordering (checked at
archival) proves both existed BEFORE the review ran.

**Fixes are DECLINED on every one of these twelve runs, so no fix-agent behaviour is exercised
here.** The fix-agent proofs are assistant-side, in plan 40-13.

---

## 4. How to run a block (do this once per terminal window)

Blocks cannot be pasted into the terminal line by line (zsh treats `#` lines as commands and a
failed check would close the window). Instead, paste this ONCE into each new terminal window. It
defines a `p40` command that pulls one named block out of this file and runs it under bash:

```text
P40=~/turingmind-code-review/docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase40.md
p40() {
  mkdir -p ~/.b3
  awk -v b="$1" '$0=="# BLOCK: "b{f=1} f{print} $0=="# END: "b{exit}' "$P40" > ~/.b3/p40.sh
  tail -1 ~/.b3/p40.sh | grep -qx "# END: $1" || { echo "p40: no block named '$1'"; return 2; }
  RUN_N="${2:-1}" bash ~/.b3/p40.sh && echo "p40: BLOCK OK ($1)" || echo "p40: BLOCK FAILED ($1)"
}
```

Then run a block by name: `p40 preflight`. Run blocks take the run number as a second word:
`p40 sil-pre 2`. If a block prints `BLOCK FAILED`, stop and paste the whole output to the
assistant.

### The order, per check

| # | Where | What you type |
|---|---|---|
| 1 | terminal | `p40 preflight` — answer `1`, `2`, `3` or `final` |
| 2 | terminal | `p40 sil-fresh` then `p40 sil-launch` |
| 3 | NEW terminal tab | paste the one launch line `sil-launch` printed — Claude Code opens |
| 4 | terminal | `p40 fingerprint` — type the model name exactly as that session shows it |
| 5 | terminal | `p40 sil-pre 1` — it tells you to `/clear`; do it, then type `CLEARED` |
| 6 | Claude Code tab | `/vibe-check:deep-review` — decline every fix (MEASUREMENT-RUN RULE) |
| 7 | terminal | `p40 sil-post 1` |
| 8 | — | `final` only: repeat 5-7 with `2`, then `3` |
| 9 | terminal | `p40 sil-revert`, then close the Claude Code tab (`/exit`) |
| 10 | — | repeat 2-9 for should-quiet-5 with `sq5-` in place of `sil-` |
| 11 | terminal | `p40 pass-json` — then hand `PASS.json` to the assistant |

A run that stops between steps 5 and 7 is VOID, not failed: run `p40 sil-void <n>` (or
`sq5-void`) and redo that run from step 5. A run that already committed is evidence and is never
voided.

---

## 5. STEP 0 — pre-flight (once per check)

This is the only place `SNAP_ROOT` and `PLUGIN_ROOT` are defined. `SNAP_ROOT` is the snapshot the
assistant's `batchsnap.py build` printed as `snapshot_root:`; `PLUGIN_ROOT` is always
`$SNAP_ROOT/plugins/vibe-check`, the folder holding `.claude-plugin/plugin.json`, and it is the
ONLY value `--plugin-dir` ever receives. Handing `--plugin-dir` the snapshot root instead loads no
plugin at all, and the run silently measures the installed cache rather than the batch under test
— which is why the `plugin.json` check below is a stopping gate, not a comment. Pre-flight writes
both values to `~/.b3/phase40-active.env`; every later block reads them from there and
re-verifies the snapshot before using them.

Removed from the v2.10 STEP 0, and why: 0(a)/(b) (installed-cache parity against tag `v2.9`) and
0(c) (`plugin.json` says 2.9.0) — a Phase-40 run never loads the installed cache, it loads a
snapshot, and `plugin.json` stays 2.9.0 until Phase 44 anyway; 0(e) (the highest-version cache
resolution check) — TRUST-01 removed that resolution from the plugin, so there is nothing left to
reproduce. 0(d), the sealed v2.9 `runs/` guard, is KEPT.

The suite is not re-run here: the snapshot is read-only, and `build` already ran the suite inside
it before sealing and recorded the result in the manifest (`suite_green`), which this block reads.

```bash
# BLOCK: preflight
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
P40DIR=docs/design/b3-ground-truth/runs-v2.10-phase40
BSNAP=$REPO/plugins/vibe-check/scripts/batchsnap.py
printf 'Which check is this? Type exactly one of 1, 2, 3 or final: '
IFS= read -r LABEL
case "$LABEL" in
  1|2|3) ARCHIVE_BATCH="batch$LABEL"; SNAP_BATCH="$LABEL"; RUNS_PER_DIFF=1 ;;
  final) ARCHIVE_BATCH=final; SNAP_BATCH=3; RUNS_PER_DIFF=3 ;;
  *) echo 'NOT ONE OF 1, 2, 3, final — STOPPING'; exit 1 ;;
esac
# batches 1 and 2 precede the D-16 removal; batch 3 and final follow it
case "$LABEL" in 1|2) SCHEMA=archive-compat ;; *) SCHEMA=future ;; esac
# (a) the previous check must already be adjudicated (the same barrier the plans run)
case "$LABEL" in 1) PRIOR='' ;; 2) PRIOR=batch1 ;; 3) PRIOR=batch2 ;; final) PRIOR=batch3 ;; esac
if test -n "$PRIOR"; then
  python3 "$BSNAP" check-pass --file "$REPO/$P40DIR/$PRIOR/PASS.json" \
    || { echo "PREVIOUS CHECK ($PRIOR) NOT ADJUDICATED OR NOT VALID — STOPPING"; exit 1; }
fi
test ! -e "$REPO/$P40DIR/$ARCHIVE_BATCH/PASS.json" \
  || { echo "CHECK $ARCHIVE_BATCH IS ALREADY CLOSED (PASS.json exists) — STOPPING"; exit 1; }
# (b) exactly one snapshot exists for this batch
SNAPS=$(ls -d ~/.vibe-check-snapshots/batch"$SNAP_BATCH"-*/ 2>/dev/null || true)
test "$(printf '%s\n' "$SNAPS" | grep -c .)" = "1" \
  || { echo "NEED EXACTLY ONE batch$SNAP_BATCH SNAPSHOT (ask the assistant) — STOPPING"; exit 1; }
SNAP_ROOT="${SNAPS%/}"
PLUGIN_ROOT="$SNAP_ROOT/plugins/vibe-check"
# (c) the snapshot is byte-identical to its manifest, and the launch argument is right
python3 "$BSNAP" verify --snap "$SNAP_ROOT" > ~/.b3/p40-verify.out \
  || { cat ~/.b3/p40-verify.out; echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p40-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
# (d) the manifest's own record: right batch, a real commit, a green suite
mf() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' \
  "$SNAP_ROOT/MANIFEST.json" "$1"; }
test "$(mf batch)" = "$SNAP_BATCH" \
  || { echo 'SNAPSHOT IS FOR A DIFFERENT BATCH — STOPPING'; exit 1; }
BATCH_SHA=$(mf snapshot_commit)
git -C "$REPO" cat-file -e "$BATCH_SHA^{commit}" \
  || { echo 'SNAPSHOT COMMIT NOT IN THIS REPO — STOPPING'; exit 1; }
SUITE=$(mf suite_green)
printf '%s' "$SUITE" | grep -q 'passed' && ! printf '%s' "$SUITE" | grep -qE 'failed|error' \
  || { echo "SNAPSHOT SUITE NOT RECORDED GREEN ($SUITE) — STOPPING"; exit 1; }
# (e) 0(d) kept — the sealed v2.9 runs/ tree equals tag v2.9 and is clean
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test -z "$(git -C "$REPO" status --porcelain docs/design/b3-ground-truth/runs/)" \
  || { echo 'SEALED v2.9 RUNS TREE DIRTY — STOPPING; report it'; exit 1; }
# (f) the sealed Phase-38 baseline: its git TREE equals the pinned tree, and it is clean
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
test -z "$(git -C "$REPO" status --porcelain docs/design/b3-ground-truth/runs-v2.10/)" \
  || { echo 'SEALED v2.10 BASELINE TREE DIRTY — STOPPING; report it'; exit 1; }
# (g) both CLIs answer (their exact versions are checked against the pin by fingerprint)
claude --version > /dev/null || { echo 'claude --version FAILED — STOPPING'; exit 1; }
codex --version > /dev/null || { echo 'codex --version FAILED — STOPPING'; exit 1; }
# record the active check for every later block
{
  printf 'ARCHIVE_BATCH=%q\n' "$ARCHIVE_BATCH"
  printf 'SNAP_ROOT=%q\n' "$SNAP_ROOT"
  printf 'PLUGIN_ROOT=%q\n' "$PLUGIN_ROOT"
  printf 'BATCH_SHA=%q\n' "$BATCH_SHA"
  printf 'SCHEMA=%q\n' "$SCHEMA"
  printf 'RUNS_PER_DIFF=%q\n' "$RUNS_PER_DIFF"
} > "$ENV"
echo "check:        $ARCHIVE_BATCH ($RUNS_PER_DIFF run(s) per diff, envelope schema $SCHEMA)"
echo "snapshot:     $SNAP_ROOT"
echo "plugin root:  $PLUGIN_ROOT"
echo "batch commit: $BATCH_SHA"
# END: preflight
```

---

## 6. STEP 0.25 — harness fingerprint (after EVERY Claude Code launch)

Run this after the launch line has opened Claude Code and before that session's first run. It
appends one session block to `RUN-METHOD-NOTES-phase40.md` and commits it. It records the snapshot
(`batch-sha`, `snapshot-root`, `plugin-root`) alongside the CLI and model versions, so every run is
bound to the exact plugin tree it measured. `RUN-METHOD-NOTES-v2.10.md` (the Phase-38 notes) is
NEVER appended to by Phase 40: Phase-38 scoring reads it.

```bash
# BLOCK: fingerprint
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
NOTES=docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase40.md
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p40-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p40-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
git -C "$REPO" diff --quiet -- "$NOTES" && git -C "$REPO" diff --cached --quiet -- "$NOTES" \
  || { echo 'THE PHASE-40 NOTES FILE HAS UNCOMMITTED CHANGES — STOPPING'; exit 1; }
# capture the harness tuple — a failed CLI probe is a stop, never a fallback value
CC=$(claude --version) || { echo 'claude --version FAILED — STOPPING'; exit 1; }
test -n "$CC" || { echo 'EMPTY claude VERSION — STOPPING'; exit 1; }
CX=$(codex --version) || { echo 'codex --version FAILED — STOPPING'; exit 1; }
printf '%s' "$CX" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+' \
  || { echo 'CODEX VERSION LACKS A FULL x.y.z — STOPPING'; exit 1; }
printf "model, exactly as the Claude Code session shows it (e.g. 'Fable 5.1'): "
IFS= read -r MODEL
MODEL_RE='^(claude[- ])?(fable|opus|sonnet|haiku)[- ]5(\.[0-9]+)?(-[0-9]{8})?$'
printf '%s' "$MODEL" | grep -qiE "$MODEL_RE" \
  || { echo 'MODEL VALUE FAILS THE CLAUDE-5 GRAMMAR — STOPPING'; exit 1; }
! printf '%s' "$MODEL" | grep -qiE '<|>|record|TBD|placeholder' \
  || { echo 'MODEL VALUE IS A PLACEHOLDER — STOPPING'; exit 1; }
# the pin, parsed from the COMMITTED Phase-40 notes blob (never the live file)
BLOB=$(git -C "$REPO" show "HEAD:$NOTES") \
  || { echo 'PHASE-40 NOTES FILE NOT COMMITTED — STOPPING'; exit 1; }
for L in pin-claude-code pin-codex pin-model; do
  test "$(printf '%s\n' "$BLOB" | grep -c "^$L: ")" = "1" \
    || { echo "PIN LINE $L NOT EXACTLY ONCE — STOPPING"; exit 1; }
done
pin() { printf '%s\n' "$BLOB" | grep "^$1: " | sed "s/^$1: //"; }
PIN_CC=$(pin pin-claude-code); PIN_CX=$(pin pin-codex); PIN_MODEL=$(pin pin-model)
DRIFT='report it to the assistant before running anything'
test "$CC" = "$PIN_CC" \
  || { echo "HARNESS DRIFT — claude-code '$CC' is not the pin — STOPPING; $DRIFT"; exit 1; }
test "$CX" = "$PIN_CX" \
  || { echo "HARNESS DRIFT — codex '$CX' is not the pin — STOPPING; $DRIFT"; exit 1; }
NORM=$(printf '%s' "$MODEL" | tr 'A-Z-' 'a-z ' | tr -s ' ')
FAMGEN=$(printf '%s' "$NORM" | sed -E 's/^(claude )?((fable|opus|sonnet|haiku) 5).*$/\2/')
test "$FAMGEN" = "$PIN_MODEL" \
  || { echo "HARNESS DRIFT — model '$MODEL' is not the pin — STOPPING; $DRIFT"; exit 1; }
# every earlier Phase-40 session must have run the same model (this file only)
printf '%s\n' "$BLOB" | { grep '^model: ' || true; } | sed 's/^model: //' > ~/.b3/p40-models.txt
while IFS= read -r PRIOR; do
  test -n "$PRIOR" || continue
  PNORM=$(printf '%s' "$PRIOR" | tr 'A-Z-' 'a-z ' | tr -s ' ')
  test "$PNORM" = "$NORM" \
    || { echo "HARNESS DRIFT — an earlier session ran '$PRIOR' — STOPPING; $DRIFT"; exit 1; }
done < ~/.b3/p40-models.txt
# append the session block and commit it — pathspec-scoped, scope asserted from the pathspec
SID_NEW=$(date '+%Y-%m-%dT%H:%M:%S%z')
{
  printf '\n## Harness fingerprint — %s\n' "$SID_NEW"
  printf 'claude-code: %s\n' "$CC"
  printf 'model: %s\n' "$MODEL"
  printf 'codex: %s\n' "$CX"
  printf 'batch: %s\n' "$ARCHIVE_BATCH"
  printf 'batch-sha: %s\n' "$BATCH_SHA"
  printf 'snapshot-root: %s\n' "$SNAP_ROOT"
  printf 'plugin-root: %s\n' "$PLUGIN_ROOT"
} >> "$REPO/$NOTES"
git -C "$REPO" commit -q --only -m "runs(40): harness fingerprint $SID_NEW" -- "$NOTES"
FPCOMMIT=$(git -C "$REPO" log -1 --format=%H -- "$NOTES")
test "$(git -C "$REPO" show --name-only --format= "$FPCOMMIT")" = "$NOTES" \
  || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
echo "session $SID_NEW fingerprinted in commit $FPCOMMIT"
# END: fingerprint
```

---

## 7. Per-diff blocks — prepare the clone, then launch

Each diff gets its clone pinned to the recorded base, the patch applied ONCE (kept until the revert
block), and every existing state file in the clone's `.turingmind/state/` parked in
`.b3-parked-phase40/`. Parking all of them (not only the expected file name) is what lets the
post-run block capture "the ONE state file this run wrote" by construction: the shipped tool has
written differently-named state files before (`<repo>-main.json`, `<repo>-HEAD.json`).

Both clones already carry the Phase-38 local exclude for `.turingmind/` (v2.10 STEP 0.5). If the
clean-tree check below stops on `.turingmind/`, that exclude is missing: tell the assistant.

**Why the launch line carries `--allowedTools`.** The snapshot lives outside the clone, and on
2026-09-27 the first batch-1 launch without that flag ran under Claude Code's auto-mode permission
classifier, which blocked the orchestrator's seat line and its read of the snapshot's `review.md`
as "code from external" before Phase 0 — the review never ran and the attempt was voided. The
flag pre-approves the tools the review needs, exactly as the assistant-side validation launches do
(`mode-path-validation-v2.10.md` §4). It changes permission handling only, never the plugin.

### triggarr-secret-in-logs — prepare (once per check, before run 1)

```bash
# BLOCK: sil-fresh
set -euo pipefail
REPO=~/turingmind-code-review
PATCH=$REPO/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch
test -f ~/.b3/phase40-active.env \
  || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase40
# guards FIRST, so a refusal leaves the clone untouched
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
test -n "$START_BRANCH" \
  || { echo 'CLONE IS DETACHED — switch it back to its branch first — STOPPING'; exit 1; }
mkdir -p "$STATE_DIR"
test ! -e "$STATE_DIR/.b3-inprogress" \
  || { echo 'A DIFF IS ALREADY IN PROGRESS HERE (.b3-inprogress) — STOPPING'; exit 1; }
test ! -e "$PARK" || { echo 'STALE PARK DIR WITHOUT A SENTINEL — STOPPING'; exit 1; }
# STEP 3 — pin the clone to the recorded base_sha
git switch --detach f4366a261fcf9bab01b48ad89279aac973a7d9b1
test "$(git rev-parse HEAD)" = "f4366a261fcf9bab01b48ad89279aac973a7d9b1" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE; it stays applied until sil-revert
git apply --check "$PATCH"
git apply "$PATCH"
# STEP 5/6 — park every existing state file, write the sentinel, protect uv.lock
mkdir "$PARK"
PARKED=0
for f in "$STATE_DIR"/*.json; do
  test -e "$f" || continue
  mv "$f" "$PARK/"; PARKED=$((PARKED + 1))
done
if test "$PARKED" -gt 0; then HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=triggarr-secret-in-logs\nbase_sha=f4366a261fcf9bab01b48ad89279aac973a7d9b1\n' \
  > "$STATE_DIR/.b3-inprogress"
printf 'had_prior_state=%s\nstart_branch=%s\nstart_sha=%s\nparked=%s\n' \
  "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" "$PARKED" >> "$STATE_DIR/.b3-inprogress"
chflags uchg ~/triggarr/uv.lock
echo "triggarr-secret-in-logs ready at $(git rev-parse HEAD), $PARKED state file(s) parked"
# END: sil-fresh
```

### triggarr-secret-in-logs — launch

```bash
# BLOCK: sil-launch
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
grep -q 'diff_id=triggarr-secret-in-logs' ~/triggarr/.turingmind/state/.b3-inprogress \
  || { echo 'CLONE NOT PREPARED — run p40 sil-fresh first — STOPPING'; exit 1; }
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p40-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p40-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
echo 'Open a NEW terminal tab and paste exactly this one line:'
echo ''
echo "  cd ~/triggarr && claude --plugin-dir \"$PLUGIN_ROOT\" --allowedTools \"Bash,Read,Write,Edit,Grep,Glob,Task,Agent\""
echo ''
echo 'Then come back here and run: p40 fingerprint'
# END: sil-launch
```

### should-quiet-5 — prepare (once per check, before run 1)

```bash
# BLOCK: sq5-fresh
set -euo pipefail
REPO=~/turingmind-code-review
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-5.patch
test -f ~/.b3/phase40-active.env \
  || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase40
# guards FIRST, so a refusal leaves the clone untouched
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
test -n "$START_BRANCH" \
  || { echo 'CLONE IS DETACHED — switch it back to its branch first — STOPPING'; exit 1; }
mkdir -p "$STATE_DIR"
test ! -e "$STATE_DIR/.b3-inprogress" \
  || { echo 'A DIFF IS ALREADY IN PROGRESS HERE (.b3-inprogress) — STOPPING'; exit 1; }
test ! -e "$PARK" || { echo 'STALE PARK DIR WITHOUT A SENTINEL — STOPPING'; exit 1; }
# STEP 3 — pin the clone to the recorded base_sha
git switch --detach 70354771a331f7def6c8116556f58d865f644cd9
test "$(git rev-parse HEAD)" = "70354771a331f7def6c8116556f58d865f644cd9" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE; it stays applied until sq5-revert
git apply --check "$PATCH"
git apply "$PATCH"
# STEP 5/6 — park every existing state file, write the sentinel
mkdir "$PARK"
PARKED=0
for f in "$STATE_DIR"/*.json; do
  test -e "$f" || continue
  mv "$f" "$PARK/"; PARKED=$((PARKED + 1))
done
if test "$PARKED" -gt 0; then HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=should-quiet-5\nbase_sha=70354771a331f7def6c8116556f58d865f644cd9\n' \
  > "$STATE_DIR/.b3-inprogress"
printf 'had_prior_state=%s\nstart_branch=%s\nstart_sha=%s\nparked=%s\n' \
  "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" "$PARKED" >> "$STATE_DIR/.b3-inprogress"
echo "should-quiet-5 ready at $(git rev-parse HEAD), $PARKED state file(s) parked"
# END: sq5-fresh
```

### should-quiet-5 — launch

```bash
# BLOCK: sq5-launch
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
grep -q 'diff_id=should-quiet-5' ~/seedsyncarr/.turingmind/state/.b3-inprogress \
  || { echo 'CLONE NOT PREPARED — run p40 sq5-fresh first — STOPPING'; exit 1; }
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p40-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p40-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
echo 'Open a NEW terminal tab and paste exactly this one line:'
echo ''
echo "  cd ~/seedsyncarr && claude --plugin-dir \"$PLUGIN_ROOT\" --allowedTools \"Bash,Read,Write,Edit,Grep,Glob,Task,Agent\""
echo ''
echo 'Then come back here and run: p40 fingerprint'
# END: sq5-launch
```

The launch line every block prints is always `claude --plugin-dir "$PLUGIN_ROOT"` with the path
filled in, and it is only printed after the snapshot re-verified and `plugin.json` was found.

---

## 8. Per-run blocks

Each run is: `p40 <diff>-pre <n>` → `/clear`, type `CLEARED` → `/vibe-check:deep-review` in the
Claude Code tab, declining every fix → `p40 <diff>-post <n>`. The run number `<n>` is `1` for a
batch check and `1`, `2`, `3` for `final`.

Runs land in `docs/design/b3-ground-truth/runs-v2.10-phase40/<check>/<diff>/run-<n>/` — NEVER in
`runs-v2.10/`, which is the sealed Phase-38 baseline. Each committed run holds exactly seven files:
the five the Phase-38 checklist captured (`clear.txt`, `session.txt`, `state.json`, `tree.diff`,
`tree.diff.sha256`) plus `report.md` (the rendered report, verbatim) and `transcript.jsonl.sha256`.

**Why the transcript itself is not committed.** `transcript.jsonl` (the session plus every review
agent's sub-transcript) is written into the run folder, stays on this machine, and is gitignored.
A Claude Code transcript carries your private global instructions and account details verbatim,
and this repository is published. The committed `transcript.jsonl.sha256` binds the local file to
the run: `pass-json` refuses a transcript that changed after capture. `report.md` and the local
transcript are what the assistant adjudicates from; a run missing either is not scoreable and is
re-run.

The post-run block also re-runs the provenance check from `BATCH-LIFECYCLE-v2.10-phase40.md` §4,
narrowed: it voids a run whose transcript names the working repo's plugin folder or the INSTALLED
vibe-check cache, and it requires the transcript to name `$PLUGIN_ROOT`. (The lifecycle doc's
broader `plugins/cache/` pattern also matches the Codex plugin's own cache folder, which every run
with a Codex pass legitimately loads, so it would void valid runs.)

### triggarr-secret-in-logs — before run `<n>`

```bash
# BLOCK: sil-pre
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
NOTES=docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase40.md
PATCH=$REPO/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
test "$N" -le "$RUNS_PER_DIFF" \
  || { echo "CHECK $ARCHIVE_BATCH HAS $RUNS_PER_DIFF RUN(S) PER DIFF — STOPPING"; exit 1; }
D=docs/design/b3-ground-truth/runs-v2.10-phase40/$ARCHIVE_BATCH/triggarr-secret-in-logs
RP=$D/run-$N
RUN_DIR=$REPO/$RP
if test "$N" -gt 1; then
  test -n "$(git -C "$REPO" log -1 --format=%H -- "$D/run-$((N - 1))/")" \
    || { echo "RUN $((N - 1)) IS NOT COMMITTED YET — STOPPING"; exit 1; }
fi
# (1) the snapshot is re-verified immediately before this run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p40-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p40-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
# (2) both sealed trees are intact
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
# (3) the clone: this diff, detached at its base, patch applied, no state file, uv.lock held
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
grep -q 'diff_id=triggarr-secret-in-logs' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — run p40 sil-fresh — STOPPING'; exit 1; }
test -z "$(git branch --show-current)" || { echo 'CLONE NOT DETACHED — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "f4366a261fcf9bab01b48ad89279aac973a7d9b1" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
test ! -e "$RUN_DIR" \
  || { echo "RUN $N ALREADY HAS A FOLDER — if unrun: p40 sil-void $N — STOPPING"; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo "STATE NOT EMPTY — an unfinished run? p40 sil-void — STOPPING"; exit 1; }
git apply --reverse --check "$PATCH" \
  || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
stat -f %Sf ~/triggarr/uv.lock | grep -q uchg \
  || { echo 'uv.lock UNPROTECTED — STOPPING'; exit 1; }
# (4) N-01 conversation isolation, typed attestation
echo 'In the Claude Code tab: type /clear and press Enter. Do it now, for EVERY run.'
printf 'Type CLEARED to confirm you did this JUST NOW: '
IFS= read -r ACK
test "$ACK" = "CLEARED" || { echo 'NOT CLEARED — STOPPING'; exit 1; }
mkdir -p "$RUN_DIR"
printf '%s CLEARED\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" > "$RUN_DIR/clear.txt"
# (5) session binding from COMMITTED blobs, before the run; bound to THIS snapshot
BLOB=$(git -C "$REPO" show "HEAD:$NOTES")
HDR='^## Harness fingerprint — [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}[+-][0-9]{4}$'
SID=$(printf '%s\n' "$BLOB" | { grep -E "$HDR" || true; } | tail -1 \
  | sed 's/^## Harness fingerprint — //')
test -n "$SID" || { echo 'NO COMMITTED FINGERPRINT — run p40 fingerprint — STOPPING'; exit 1; }
FPC=$(git -C "$REPO" log --format=%H --reverse -S"## Harness fingerprint — $SID" -- "$NOTES" \
  | head -1 || true)
test -n "$FPC" || { echo 'FINGERPRINT COMMIT NOT FOUND — STOPPING'; exit 1; }
BLK=$(printf '%s\n' "$BLOB" \
  | awk -v h="## Harness fingerprint — $SID" '$0==h{f=1;next} /^## /{f=0} f')
printf '%s\n' "$BLK" | grep -qxF "batch-sha: $BATCH_SHA" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER SNAPSHOT — p40 fingerprint — STOPPING'; exit 1; }
printf '%s\n' "$BLK" | grep -qxF "plugin-root: $PLUGIN_ROOT" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER PLUGIN ROOT — STOPPING'; exit 1; }
printf '%s\n%s\n' "$SID" "$FPC" > "$RUN_DIR/session.txt"
echo "run $N ready — in the Claude Code tab type: /vibe-check:deep-review"
echo 'Decline every fix: Step A option 4 (Skip fixes), Step C option 3 (Abandon for now).'
echo "Then come back here and run: p40 sil-post $N"
# END: sil-pre
```

### triggarr-secret-in-logs — after run `<n>`

```bash
# BLOCK: sil-post
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase40/$ARCHIVE_BATCH/triggarr-secret-in-logs/run-$N
RUN_DIR=$REPO/$RP
EXPECTED_HEAD=f4366a261fcf9bab01b48ad89279aac973a7d9b1
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" \
  || { echo 'HEAD MOVED DURING THE RUN (was a fix committed?) — STOPPING'; exit 1; }
# the snapshot is still byte-identical after the run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p40-verify.out || { echo 'SNAPSHOT CHANGED DURING THE RUN — STOPPING'; exit 1; }
# the pre-run records exist (this block never writes them)
test -f "$RUN_DIR/clear.txt" || { echo 'clear.txt MISSING — p40 sil-void — STOPPING'; exit 1; }
test -f "$RUN_DIR/session.txt" \
  || { echo 'session.txt MISSING — p40 sil-void — STOPPING'; exit 1; }
# STEP 8e — the ONE state file this run wrote (every older one was parked by sil-fresh)
NEW=$(find "$STATE_DIR" -maxdepth 1 -name '*.json' -newer "$RUN_DIR/clear.txt")
test "$(printf '%s\n' "$NEW" | grep -c .)" = "1" \
  || { echo 'EXPECTED EXACTLY ONE NEW STATE FILE — STOPPING'; exit 1; }
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
# STEP 8f1 — the FULL tracked diff equals the planted diff and nothing else
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" \
   = "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2" \
  || { echo 'FULL WORKTREE DIFF != THE PLANTED DIFF — STOPPING'; exit 1; }
# STEP 8f2 — the touched-path set
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/clients/base.py" \
  || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — no stray untracked files outside the state dir
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" \
  || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — STOPPING'; exit 1; }
# STEP 8g — isolation: exactly one pass, at the pinned head
python3 - "$RUN_DIR/state.json" "$EXPECTED_HEAD" <<'PY' \
  || { echo 'NOT ONE ISOLATED PASS AT THE PINNED HEAD — p40 sil-void — STOPPING'; exit 1; }
import json, sys
s = json.load(open(sys.argv[1]))
assert len(s["passes"]) == 1, "NOT ISOLATED: passes=%d" % len(s["passes"])
assert s["passes"][-1]["head_sha"] == sys.argv[2], "HEAD MISMATCH"
print("OK one isolated pass at", sys.argv[2])
PY
# CAPTURE — the session transcript (+ every agent sub-transcript) and the rendered report
PROJ=$HOME/.claude/projects/$(printf '%s' "$HOME/triggarr" | sed 's/[^A-Za-z0-9]/-/g')
test -d "$PROJ" \
  || { echo 'NO CLAUDE CODE TRANSCRIPT FOLDER FOR ~/triggarr — STOPPING'; exit 1; }
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
BAD='(turingmind-code-review/plugins/vibe-check|plugins/cache/thejuran/vibe-check)'
! grep -qE "$BAD" "$RUN_DIR/transcript.jsonl" \
  || { echo 'RUN TOUCHED A NON-SNAPSHOT PLUGIN PATH — RUN IS VOID — STOPPING'; exit 1; }
grep -qF "$PLUGIN_ROOT" "$RUN_DIR/transcript.jsonl" \
  || { echo 'TRANSCRIPT NEVER NAMES THE SNAPSHOT PLUGIN — RUN IS VOID — STOPPING'; exit 1; }
shasum -a 256 "$RUN_DIR/transcript.jsonl" | awk '{print $1}' \
  > "$RUN_DIR/transcript.jsonl.sha256"
# STEP 8h — clear the state dir for the next run (the pass is archived in the run folder)
rm "$STATE_FILE"
# STEP 8i — commit this run, pathspec-scoped, scope asserted on the commit the pathspec resolves
git -C "$REPO" add "$RP/"
git -C "$REPO" commit -q --only \
  -m "runs(40): $ARCHIVE_BATCH triggarr-secret-in-logs run $N (state key $STATE_KEY)" -- "$RP/"
RC=$(git -C "$REPO" log -1 --format=%H -- "$RP/")
# scope gate: EXACTLY seven files — the five Phase-38 artifacts plus the two this runbook adds,
# report.md and transcript.jsonl.sha256 (transcript.jsonl itself stays local and gitignored)
EXPECT=''
for f in clear.txt report.md session.txt state.json transcript.jsonl.sha256 tree.diff \
    tree.diff.sha256; do EXPECT="$EXPECT $RP/$f"; done
GOT=$(git -C "$REPO" show --name-only --format= "$RC" | LC_ALL=C sort | paste -sd' ' -)
test "$(git -C "$REPO" show --name-only --format= "$RC" | grep -c .)" -eq 7 \
  || { echo 'COMMIT SCOPE VIOLATION (not exactly 7 files) — STOPPING'; exit 1; }
test "$GOT" = "${EXPECT# }" || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
# end of scope gate
test -z "$(git -C "$REPO" status --porcelain "$RP/")" \
  || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
git -C "$REPO" check-ignore -q "$RP/transcript.jsonl" \
  || { echo 'transcript.jsonl IS NOT GITIGNORED — STOPPING'; exit 1; }
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
echo "run $N of triggarr-secret-in-logs captured and committed ($RC)"
# LAST — the envelope shape. A failure here is a RESULT, not a void run: the run is committed.
python3 "$REPO/plugins/vibe-check/scripts/state_shape.py" "$RUN_DIR/state.json" \
  --schema "$SCHEMA" \
  || { echo 'ENVELOPE SHAPE VIOLATION — do NOT re-run; tell the assistant — STOPPING'; exit 1; }
echo "state_shape PASS ($SCHEMA)"
# END: sil-post
```

### triggarr-secret-in-logs — void an unfinished run `<n>`

Use this only when a run STOPPED before `sil-post` committed it. It removes the run's uncommitted
folder and any state file the run wrote, and checks the clone is still exactly base + patch.

```bash
# BLOCK: sil-void
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
PATCH=$REPO/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase40/$ARCHIVE_BATCH/triggarr-secret-in-logs/run-$N
test -z "$(git -C "$REPO" log -1 --format=%H -- "$RP/")" \
  || { echo "RUN $N IS COMMITTED — it is evidence, not voidable — STOPPING"; exit 1; }
rm -rf "${REPO:?}/$RP"
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
grep -q 'diff_id=triggarr-secret-in-logs' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — STOPPING'; exit 1; }
find "$STATE_DIR" -maxdepth 1 -name '*.json' -print -delete
test "$(git rev-parse HEAD)" = "f4366a261fcf9bab01b48ad89279aac973a7d9b1" \
  || { echo 'HEAD MOVED — run p40 sil-revert, then p40 sil-fresh — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" \
   = "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2" \
  || { echo 'CLONE DRIFTED — p40 sil-revert, then p40 sil-fresh — STOPPING'; exit 1; }
echo "run $N voided — redo it: p40 sil-pre $N"
# END: sil-void
```

### should-quiet-5 — before run `<n>`

```bash
# BLOCK: sq5-pre
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
NOTES=docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase40.md
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-5.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
test "$N" -le "$RUNS_PER_DIFF" \
  || { echo "CHECK $ARCHIVE_BATCH HAS $RUNS_PER_DIFF RUN(S) PER DIFF — STOPPING"; exit 1; }
D=docs/design/b3-ground-truth/runs-v2.10-phase40/$ARCHIVE_BATCH/should-quiet-5
RP=$D/run-$N
RUN_DIR=$REPO/$RP
if test "$N" -gt 1; then
  test -n "$(git -C "$REPO" log -1 --format=%H -- "$D/run-$((N - 1))/")" \
    || { echo "RUN $((N - 1)) IS NOT COMMITTED YET — STOPPING"; exit 1; }
fi
# (1) the snapshot is re-verified immediately before this run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p40-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p40-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
# (2) both sealed trees are intact
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
# (3) the clone: this diff, detached at its base, patch applied, no state file
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
grep -q 'diff_id=should-quiet-5' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — run p40 sq5-fresh — STOPPING'; exit 1; }
test -z "$(git branch --show-current)" || { echo 'CLONE NOT DETACHED — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "70354771a331f7def6c8116556f58d865f644cd9" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
test ! -e "$RUN_DIR" \
  || { echo "RUN $N ALREADY HAS A FOLDER — if unrun: p40 sq5-void $N — STOPPING"; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo "STATE NOT EMPTY — an unfinished run? p40 sq5-void — STOPPING"; exit 1; }
git apply --reverse --check "$PATCH" \
  || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
# (4) N-01 conversation isolation, typed attestation
echo 'In the Claude Code tab: type /clear and press Enter. Do it now, for EVERY run.'
printf 'Type CLEARED to confirm you did this JUST NOW: '
IFS= read -r ACK
test "$ACK" = "CLEARED" || { echo 'NOT CLEARED — STOPPING'; exit 1; }
mkdir -p "$RUN_DIR"
printf '%s CLEARED\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" > "$RUN_DIR/clear.txt"
# (5) session binding from COMMITTED blobs, before the run; bound to THIS snapshot
BLOB=$(git -C "$REPO" show "HEAD:$NOTES")
HDR='^## Harness fingerprint — [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}[+-][0-9]{4}$'
SID=$(printf '%s\n' "$BLOB" | { grep -E "$HDR" || true; } | tail -1 \
  | sed 's/^## Harness fingerprint — //')
test -n "$SID" || { echo 'NO COMMITTED FINGERPRINT — run p40 fingerprint — STOPPING'; exit 1; }
FPC=$(git -C "$REPO" log --format=%H --reverse -S"## Harness fingerprint — $SID" -- "$NOTES" \
  | head -1 || true)
test -n "$FPC" || { echo 'FINGERPRINT COMMIT NOT FOUND — STOPPING'; exit 1; }
BLK=$(printf '%s\n' "$BLOB" \
  | awk -v h="## Harness fingerprint — $SID" '$0==h{f=1;next} /^## /{f=0} f')
printf '%s\n' "$BLK" | grep -qxF "batch-sha: $BATCH_SHA" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER SNAPSHOT — p40 fingerprint — STOPPING'; exit 1; }
printf '%s\n' "$BLK" | grep -qxF "plugin-root: $PLUGIN_ROOT" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER PLUGIN ROOT — STOPPING'; exit 1; }
printf '%s\n%s\n' "$SID" "$FPC" > "$RUN_DIR/session.txt"
echo "run $N ready — in the Claude Code tab type: /vibe-check:deep-review"
echo 'Decline every fix: Step A option 4 (Skip fixes), Step C option 3 (Abandon for now).'
echo "Then come back here and run: p40 sq5-post $N"
# END: sq5-pre
```

### should-quiet-5 — after run `<n>`

```bash
# BLOCK: sq5-post
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase40/$ARCHIVE_BATCH/should-quiet-5/run-$N
RUN_DIR=$REPO/$RP
EXPECTED_HEAD=70354771a331f7def6c8116556f58d865f644cd9
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" \
  || { echo 'HEAD MOVED DURING THE RUN (was a fix committed?) — STOPPING'; exit 1; }
# the snapshot is still byte-identical after the run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p40-verify.out || { echo 'SNAPSHOT CHANGED DURING THE RUN — STOPPING'; exit 1; }
# the pre-run records exist (this block never writes them)
test -f "$RUN_DIR/clear.txt" || { echo 'clear.txt MISSING — p40 sq5-void — STOPPING'; exit 1; }
test -f "$RUN_DIR/session.txt" \
  || { echo 'session.txt MISSING — p40 sq5-void — STOPPING'; exit 1; }
# STEP 8e — the ONE state file this run wrote (every older one was parked by sq5-fresh)
NEW=$(find "$STATE_DIR" -maxdepth 1 -name '*.json' -newer "$RUN_DIR/clear.txt")
test "$(printf '%s\n' "$NEW" | grep -c .)" = "1" \
  || { echo 'EXPECTED EXACTLY ONE NEW STATE FILE — STOPPING'; exit 1; }
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
# STEP 8f1 — the FULL tracked diff equals the planted diff and nothing else
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" \
   = "8af04cc658b5a672d2d6be7af9fc042aae81742c56a01a5d030e4d86ea630060" \
  || { echo 'FULL WORKTREE DIFF != THE PLANTED DIFF — STOPPING'; exit 1; }
# STEP 8f2 — the touched-path set
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/python/model/model.py" \
  || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — no stray untracked files outside the state dir
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" \
  || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — STOPPING'; exit 1; }
# STEP 8g — isolation: exactly one pass, at the pinned head
python3 - "$RUN_DIR/state.json" "$EXPECTED_HEAD" <<'PY' \
  || { echo 'NOT ONE ISOLATED PASS AT THE PINNED HEAD — p40 sq5-void — STOPPING'; exit 1; }
import json, sys
s = json.load(open(sys.argv[1]))
assert len(s["passes"]) == 1, "NOT ISOLATED: passes=%d" % len(s["passes"])
assert s["passes"][-1]["head_sha"] == sys.argv[2], "HEAD MISMATCH"
print("OK one isolated pass at", sys.argv[2])
PY
# CAPTURE — the session transcript (+ every agent sub-transcript) and the rendered report
PROJ=$HOME/.claude/projects/$(printf '%s' "$HOME/seedsyncarr" | sed 's/[^A-Za-z0-9]/-/g')
test -d "$PROJ" \
  || { echo 'NO CLAUDE CODE TRANSCRIPT FOLDER FOR ~/seedsyncarr — STOPPING'; exit 1; }
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
BAD='(turingmind-code-review/plugins/vibe-check|plugins/cache/thejuran/vibe-check)'
! grep -qE "$BAD" "$RUN_DIR/transcript.jsonl" \
  || { echo 'RUN TOUCHED A NON-SNAPSHOT PLUGIN PATH — RUN IS VOID — STOPPING'; exit 1; }
grep -qF "$PLUGIN_ROOT" "$RUN_DIR/transcript.jsonl" \
  || { echo 'TRANSCRIPT NEVER NAMES THE SNAPSHOT PLUGIN — RUN IS VOID — STOPPING'; exit 1; }
shasum -a 256 "$RUN_DIR/transcript.jsonl" | awk '{print $1}' \
  > "$RUN_DIR/transcript.jsonl.sha256"
# STEP 8h — clear the state dir for the next run (the pass is archived in the run folder)
rm "$STATE_FILE"
# STEP 8i — commit this run, pathspec-scoped, scope asserted on the commit the pathspec resolves
git -C "$REPO" add "$RP/"
git -C "$REPO" commit -q --only \
  -m "runs(40): $ARCHIVE_BATCH should-quiet-5 run $N (state key $STATE_KEY)" -- "$RP/"
RC=$(git -C "$REPO" log -1 --format=%H -- "$RP/")
# scope gate: EXACTLY seven files — the five Phase-38 artifacts plus the two this runbook adds,
# report.md and transcript.jsonl.sha256 (transcript.jsonl itself stays local and gitignored)
EXPECT=''
for f in clear.txt report.md session.txt state.json transcript.jsonl.sha256 tree.diff \
    tree.diff.sha256; do EXPECT="$EXPECT $RP/$f"; done
GOT=$(git -C "$REPO" show --name-only --format= "$RC" | LC_ALL=C sort | paste -sd' ' -)
test "$(git -C "$REPO" show --name-only --format= "$RC" | grep -c .)" -eq 7 \
  || { echo 'COMMIT SCOPE VIOLATION (not exactly 7 files) — STOPPING'; exit 1; }
test "$GOT" = "${EXPECT# }" || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
# end of scope gate
test -z "$(git -C "$REPO" status --porcelain "$RP/")" \
  || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
git -C "$REPO" check-ignore -q "$RP/transcript.jsonl" \
  || { echo 'transcript.jsonl IS NOT GITIGNORED — STOPPING'; exit 1; }
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
echo "run $N of should-quiet-5 captured and committed ($RC)"
# LAST — the envelope shape. A failure here is a RESULT, not a void run: the run is committed.
python3 "$REPO/plugins/vibe-check/scripts/state_shape.py" "$RUN_DIR/state.json" \
  --schema "$SCHEMA" \
  || { echo 'ENVELOPE SHAPE VIOLATION — do NOT re-run; tell the assistant — STOPPING'; exit 1; }
echo "state_shape PASS ($SCHEMA)"
# END: sq5-post
```

### should-quiet-5 — void an unfinished run `<n>`

```bash
# BLOCK: sq5-void
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-5.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase40/$ARCHIVE_BATCH/should-quiet-5/run-$N
test -z "$(git -C "$REPO" log -1 --format=%H -- "$RP/")" \
  || { echo "RUN $N IS COMMITTED — it is evidence, not voidable — STOPPING"; exit 1; }
rm -rf "${REPO:?}/$RP"
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
grep -q 'diff_id=should-quiet-5' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — STOPPING'; exit 1; }
find "$STATE_DIR" -maxdepth 1 -name '*.json' -print -delete
test "$(git rev-parse HEAD)" = "70354771a331f7def6c8116556f58d865f644cd9" \
  || { echo 'HEAD MOVED — run p40 sq5-revert, then p40 sq5-fresh — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" \
   = "8af04cc658b5a672d2d6be7af9fc042aae81742c56a01a5d030e4d86ea630060" \
  || { echo 'CLONE DRIFTED — p40 sq5-revert, then p40 sq5-fresh — STOPPING'; exit 1; }
echo "run $N voided — redo it: p40 sq5-pre $N"
# END: sq5-void
```

---

## 9. Your worklog — mechanical facts only

Tick each cell as the blocks report it (`y`/`n`, or the exit code). There is deliberately no
column for whether a finding was caught or how many false positives there were: those are the
assistant's calls (section 2). `pass-json` re-derives every column from the committed artifacts,
so this table is your worklog, not the evidence.

Columns: `snap` = the snapshot re-verified before the run (y/n) · `shape` = the `state_shape.py`
exit code · `tree` = tree.diff sha matched (y/n) · `paths` = touched-path set matched (y/n) ·
`1 pass` = `len(passes)==1` held (y/n) · `report` / `transcript` = captured (y/n).

| check | diff | run | snap | shape | tree | paths | 1 pass | report | transcript |
|---|---|---|---|---|---|---|---|---|---|
| batch1 | triggarr-secret-in-logs | 1 | | | | | | | |
| batch1 | should-quiet-5 | 1 | | | | | | | |
| batch2 | triggarr-secret-in-logs | 1 | | | | | | | |
| batch2 | should-quiet-5 | 1 | | | | | | | |
| batch3 | triggarr-secret-in-logs | 1 | | | | | | | |
| batch3 | should-quiet-5 | 1 | | | | | | | |
| final | triggarr-secret-in-logs | 1 | | | | | | | |
| final | triggarr-secret-in-logs | 2 | | | | | | | |
| final | triggarr-secret-in-logs | 3 | | | | | | | |
| final | should-quiet-5 | 1 | | | | | | | |
| final | should-quiet-5 | 2 | | | | | | | |
| final | should-quiet-5 | 3 | | | | | | | |

---

## 10. Writing `PASS.json` (once per check, after both diffs are reverted)

`p40 pass-json` writes `docs/design/b3-ground-truth/runs-v2.10-phase40/batch<N>/PASS.json` (or
`final/PASS.json`) from the committed run folders and commits it. It fills only the mechanical
fields. Every `adjudication` field is left as the literal `"pending-assistant"`, and
`trace_validation` as `"not-applicable"` (the assistant sets it if it runs the 40-13 read-trace
checker on the transcript). The shape it writes, for a batch check:

```json
{
  "batch": 1,
  "snapshot_commit": "<batch-sha from pre-flight>",
  "verdict": "PASS",
  "recorded_by": "owner",
  "recorded_at": "<UTC time of writing>",
  "runs": [
    {
      "diff": "triggarr-secret-in-logs",
      "run_index": 1,
      "state_shape": "PASS",
      "tree_diff_sha_match": true,
      "report_path": "triggarr-secret-in-logs/run-1/report.md",
      "transcript_path": "triggarr-secret-in-logs/run-1/transcript.jsonl",
      "trace_validation": "not-applicable",
      "adjudication": "pending-assistant"
    },
    {
      "diff": "should-quiet-5",
      "run_index": 1,
      "state_shape": "PASS",
      "tree_diff_sha_match": true,
      "report_path": "should-quiet-5/run-1/report.md",
      "transcript_path": "should-quiet-5/run-1/transcript.jsonl",
      "trace_validation": "not-applicable",
      "adjudication": "pending-assistant"
    }
  ]
}
```

`verdict` here is the MECHANICAL verdict (`FAIL` if any run recorded a shape failure or a tree.diff
mismatch). The assistant sets the final verdict after adjudicating. The `final` check writes
`"batch": "final"` and six runs.

Hand this file to the assistant. `batchsnap.py check-pass` refuses an artifact that still says
`pending-assistant`, so the next batch cannot start until the adjudication is done.

```bash
# BLOCK: pass-json
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase40-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p40 preflight first — STOPPING'; exit 1; }
. "$ENV"
REL=docs/design/b3-ground-truth/runs-v2.10-phase40/$ARCHIVE_BATCH
test ! -e "$REPO/$REL/PASS.json" || { echo 'PASS.json ALREADY WRITTEN — STOPPING'; exit 1; }
test ! -e ~/triggarr/.turingmind/state/.b3-inprogress \
  || { echo 'triggarr-secret-in-logs NOT REVERTED — p40 sil-revert — STOPPING'; exit 1; }
test ! -e ~/seedsyncarr/.turingmind/state/.b3-inprogress \
  || { echo 'should-quiet-5 NOT REVERTED — p40 sq5-revert — STOPPING'; exit 1; }
python3 - "$REPO" "$REL" "$ARCHIVE_BATCH" "$BATCH_SHA" "$SCHEMA" "$RUNS_PER_DIFF" <<'PY' \
  || { echo 'PASS.json NOT WRITTEN — STOPPING'; exit 1; }
import datetime, glob, hashlib, json, os, subprocess, sys
repo, rel, label, sha, schema, per = sys.argv[1:7]
per = int(per)
top = os.path.join(repo, rel)
shape = os.path.join(repo, "plugins/vibe-check/scripts/state_shape.py")
expect = {
    "triggarr-secret-in-logs":
        "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2",
    "should-quiet-5":
        "8af04cc658b5a672d2d6be7af9fc042aae81742c56a01a5d030e4d86ea630060",
}
runs, failed = [], False
for diff in ("triggarr-secret-in-logs", "should-quiet-5"):
    found = sorted(glob.glob(os.path.join(top, diff, "run-*")))
    if len(found) != per:
        sys.exit("%s has %d run folder(s), this check needs %d" % (diff, len(found), per))
    for n in range(1, per + 1):
        sub = "%s/run-%d" % (diff, n)
        run = os.path.join(top, sub)
        log = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%H", "--",
                              os.path.join(rel, sub)], stdout=subprocess.PIPE, text=True)
        if not log.stdout.strip():
            sys.exit("%s is not committed" % sub)
        rc = subprocess.run([sys.executable, shape, os.path.join(run, "state.json"),
                             "--schema", schema]).returncode
        tree = open(os.path.join(run, "tree.diff.sha256")).read().strip() == expect[diff]
        tpath = os.path.join(run, "transcript.jsonl")
        if not os.path.isfile(tpath) or not os.path.isfile(os.path.join(run, "report.md")):
            sys.exit("%s is missing report.md or transcript.jsonl" % sub)
        got = hashlib.sha256(open(tpath, "rb").read()).hexdigest()
        if got != open(tpath + ".sha256").read().strip():
            sys.exit("%s/transcript.jsonl changed after capture" % sub)
        failed = failed or rc != 0 or not tree
        runs.append({"diff": diff, "run_index": n,
                     "state_shape": "PASS" if rc == 0 else "FAIL",
                     "tree_diff_sha_match": tree,
                     "report_path": sub + "/report.md",
                     "transcript_path": sub + "/transcript.jsonl",
                     "trace_validation": "not-applicable",
                     "adjudication": "pending-assistant"})
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
art = {"batch": int(label[5:]) if label.startswith("batch") else label,
       "snapshot_commit": sha, "verdict": "FAIL" if failed else "PASS",
       "recorded_by": "owner", "recorded_at": now, "runs": runs}
with open(os.path.join(top, "PASS.json"), "w") as fh:
    json.dump(art, fh, indent=2)
    fh.write("\n")
print("PASS.json written: %d run(s), mechanical verdict %s" % (len(runs), art["verdict"]))
PY
# the barrier must REFUSE this artifact until the assistant adjudicates it
! python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" check-pass \
  --file "$REPO/$REL/PASS.json" > ~/.b3/p40-checkpass.out \
  || { echo 'check-pass ACCEPTED AN UNADJUDICATED ARTIFACT — STOPPING'; exit 1; }
grep -q 'pending-assistant' ~/.b3/p40-checkpass.out \
  || { cat ~/.b3/p40-checkpass.out; echo 'check-pass REFUSED, OTHER REASON — STOPPING'; exit 1; }
git -C "$REPO" add "$REL/PASS.json"
git -C "$REPO" commit -q --only -m "runs(40): $ARCHIVE_BATCH PASS.json (pending assistant)" \
  -- "$REL/PASS.json"
PC=$(git -C "$REPO" log -1 --format=%H -- "$REL/PASS.json")
test "$(git -C "$REPO" show --name-only --format= "$PC")" = "$REL/PASS.json" \
  || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
echo "committed $REL/PASS.json ($PC) — hand it to the assistant"
# END: pass-json
```

---

## 11. Revert once per diff (fixtures and your own state only)

Run after the diff's LAST run of the check. This restores the B3 fixture clone to the branch it was
on and puts your parked state files back. It does NOT roll back plugin commits: plugin rollback is
the revert section of `BATCH-LIFECYCLE-v2.10-phase40.md`, never this block.

```bash
# BLOCK: sil-revert
set -euo pipefail
cd ~/triggarr
# N-04 — clear the uv.lock protection FIRST (this is also the abandon-this-diff path)
chflags nouchg ~/triggarr/uv.lock
! stat -f %Sf ~/triggarr/uv.lock | grep -q uchg \
  || { echo 'uv.lock STILL PROTECTED after the clear — STOPPING'; exit 1; }
STATE_DIR=~/triggarr/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase40
test -e "$STATE_DIR/.b3-inprogress" \
  || { echo 'NO SENTINEL — nothing to revert — STOPPING'; exit 1; }
grep -q 'diff_id=triggarr-secret-in-logs' "$STATE_DIR/.b3-inprogress" \
  || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo 'A RUN IS UNFINISHED (state file present) — p40 sil-void <n> — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd triggarr/clients/base.py
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore your parked state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then
  for f in "$PARK"/*.json; do mv -n "$f" "$STATE_DIR/"; done
fi
test -z "$(find "$PARK" -mindepth 1)" \
  || { echo 'PARKED FILES COULD NOT ALL BE RESTORED — STOPPING'; exit 1; }
rmdir "$PARK"
rm "$STATE_DIR/.b3-inprogress"
echo "triggarr-secret-in-logs complete — clone back on $START_BRANCH@$START_SHA"
echo 'Close the Claude Code tab for this diff (/exit).'
# END: sil-revert
```

```bash
# BLOCK: sq5-revert
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase40
test -e "$STATE_DIR/.b3-inprogress" \
  || { echo 'NO SENTINEL — nothing to revert — STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-5' "$STATE_DIR/.b3-inprogress" \
  || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo 'A RUN IS UNFINISHED (state file present) — p40 sq5-void <n> — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd src/python/model/model.py
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore your parked state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then
  for f in "$PARK"/*.json; do mv -n "$f" "$STATE_DIR/"; done
fi
test -z "$(find "$PARK" -mindepth 1)" \
  || { echo 'PARKED FILES COULD NOT ALL BE RESTORED — STOPPING'; exit 1; }
rmdir "$PARK"
rm "$STATE_DIR/.b3-inprogress"
echo "should-quiet-5 complete — clone back on $START_BRANCH@$START_SHA"
echo 'Close the Claude Code tab for this diff (/exit).'
# END: sq5-revert
```

---

## 12. The phase-exit judgment

The DIET-04 gate is **catch-rate no worse**: `triggarr-secret-in-logs` holds **3/3** at the `final`
×3 check, judged against its own Phase-38 triplet (3/3 catch). The should-quiet-5 FP count at ×3
is recorded against its own triplet (1/3 FP) and reported, but it is not the gate: the quiet side
is informational here, and Phase 43's full re-measure is the real proof.

The assistant writes that verdict into `runs-v2.10-phase40/final/PASS.json` after adjudicating the
six `final` runs, and the owner reviews it. Plan 40-14's barrier consumes that artifact.
