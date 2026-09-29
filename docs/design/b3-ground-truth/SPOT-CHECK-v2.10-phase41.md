# Phase-41 spot-check runbook — v2.10 (6 owner runs, one file)

**Purpose:** the SCORER-05 live check, as copy-paste blocks: which two diffs, what the replay
predicts for them, which commands, and where each result lands. Every run below is an OWNER action;
the assistant never invokes `/deep-review`.

This is the Phase-40 runbook (`SPOT-CHECK-v2.10-phase40.md`) re-pointed at the Wave-1 scorer. The
machinery is copied, not reinvented (D-13): an immutable `batchsnap.py` snapshot, the harness
fingerprint against the pin, the installed-cache parity pre-flight, `/clear` per run (N-01),
auto-memory parking (N-02), the provenance grep, the manual-permission launch line and PASS.json
adjudication. Snapshot building, the commit-set tool and PLUGIN rollback live in
`BATCH-LIFECYCLE-v2.10-phase40.md` (batch 4 = the Wave-1 scorer commits); this file is the runs.

---

## 1. The run budget — 6 runs (D-10, D-11, D-12)

| Check | Runs | When | What is under test |
|---|---|---|---|
| `final` | 6 (should-quiet-3 ×3, should-quiet-1 ×3) | after 41-07 hands over | the Wave-1 scorer: 41-04 B-SEV + 41-05 B-REWEIGHT + 41-06 H-LANE |
| `final-2` | 6 more, ONLY on a D-11 miss | after ONE offline re-tune (D-12) | the re-tuned scorer, same two diffs |
| **total** | **6 (max 12)** | | |

One `final` check is 2 diffs × 3 runs. If it misses the D-11 pass rule (section 12), the assistant
makes ONE offline re-tune under the same replay guardrail and the same principled-change rule,
rebuilds a snapshot, pins it here, and you run ONE more 6-run check archived under `final-2/`. After
that Phase 41 closes and Wave 2 starts either way, with any miss disclosed. There is no third check.

Milestone budget: about 80 owner runs for v2.10, and Phase 43's full re-measure needs 30–36 of them,
which is why the miss policy caps Phase 41 at +6.

---

## 2. What you record, and what you do NOT (read this before run 1)

You are not asked to decide whether a finding counts as a false positive. Capture the report and
the transcript; the assistant scores them.

| Recorded by | What | Why |
|---|---|---|
| OWNER (mechanical) | the facts listed first below | exit codes, string equality |
| ASSISTANT (judgement) | the verdicts listed second below | needs engineering judgement |

- **OWNER (mechanical):** did the command complete; `state_shape.py` exit code; `tree.diff` sha
  match; touched-path match; `len(passes)==1`; the run's rendered report captured verbatim to
  `report.md`; the full transcript captured to `transcript.jsonl`; and the codex condition the
  post-run block prints (`joined`, `skipped` or `off`). Why: all are exit codes or string
  equality — no judgement.
- **ASSISTANT (judgement):** per-run quiet clean/FP verdict; per-run band agreement with the
  replay (informational); the check verdict under D-11.

Every block below does the mechanical part for you: it either prints `BLOCK OK` or stops with a
line ending in `STOPPING`. Your job is to run the blocks in order, do the one Claude Code action
per run, and hand the result to the assistant.

**What the assistant is going to do with what you captured** — written down here so the scoring is
fixed in advance rather than improvised:

- **FP on a quiet diff** = ANY finding at band critical OR warning (not site-gated). Medium/low
  are noise-notes: recorded, not counted. **FP is counted per RUN: a run with any critical or
  warning survivor is ONE FP run, however many such findings it has.**
- **The verdict (D-11):** over the 6 runs, the number of runs that still fire a critical/warning
  must be **≤ the replay's predicted count for the pair (section 3)**. Per-run band agreement
  with the replay is reported for information only — fresh runs produce fresh findings, so
  run-for-run matching is not the gate.
- **The codex condition is recorded per run (D-13).** Runs use codex at the shipped default. A run
  where codex SKIPS under the BashOutput launch gate is **recorded, not voided** (Phase-40
  precedent) — codex `skipped` is recorded as-is, with the note carried into PASS.json. The note
  matters: the prediction was computed from archived runs under their archived codex condition,
  and Wave 1's +10 now fires only when codex joined (D-01).

---

## 3. The replay-chosen pair, with its evidence (D-10, D-16)

**The D-16 rule, verbatim from `CALIBRATION-v2.10.md` § "Spot-check tie-break (D-16, stated before
the replay ranks)":**

> The two spot-check diffs are the eligible should-quiet diffs with the largest predicted movement.
> Predicted movement is the number of FP runs in the baseline replay minus the number in the
> combined-candidate replay, over the diff's archived triplet. A diff that is already quiet in its
> post-diet runs carries no signal and is skipped: should-quiet-5 was 0/3 in the Phase-40 final
> check. Any remaining ties go to the lower diff number. should-quiet-7 is ineligible (ledger 001).
> should-quiet-6 is codex-driven, and D-01 keeps codex as the independent voter, so Wave 1 is not
> expected to move it. If the replay agrees, that is recorded as-is, not tuned away.

**The ranking**, transcribed from `REPLAY-REPORT-phase41-combined.md` § "FP prediction — headline
quiet set" (combined Wave 1 = B-SEV + B-REWEIGHT + H-LANE, `overrides: {}`, scorer sha256
`11303a24a5f4091a5aeb8c6d6b0559bd958560fd0ace4dc0a8fd57bc24ed05ff`), over each diff's Phase-38
triplet:

| diff | baseline-replay fired /3 | combined fired /3 | movement | eligible? | picked? |
|---|---|---|---|---|---|
| should-quiet-1 | 3/3 | 3/3 | 0 | yes | **yes** (0-movement tie; lowest number) |
| should-quiet-2 | 3/3 | 3/3 | 0 | yes | no (tie lost to should-quiet-1) |
| should-quiet-3 | 3/3 | 2/3 | **1** | yes | **yes** (largest movement) |
| should-quiet-4 | 3/3 | 3/3 | 0 | yes | no (tie lost to should-quiet-1) |
| should-quiet-5 | 1/3 | 0/3 | 1 | **no** — skipped: 0/3 in the Phase-40 final (post-diet) check | no |
| should-quiet-6 | 3/3 | 3/3 | 0 | yes (codex-driven) | no (tie lost to should-quiet-1) |
| should-quiet-7 | 3/3 | 3/3 | — | **no** — ineligible per ledger 001 (informational only) | no |

Headline set: baseline **16/18** → combined **14/18**, REGRESSED 0 of the 26 protected catches.

**Pick 1 — should-quiet-3 (`~/roonseek`), predicted 2/3.**
- run-1 goes quiet: its three firing rows are all single-lane warnings just over the floor —
  `architecture` warning 80, `impact` warning 84, `impact` warning 80 (as fired under B-SEV, which
  equals the baseline firing set). B-REWEIGHT's lower-only offsets (`architecture` −6, `impact`
  −12) take all three below the warning floor, so no critical/warning survives.
- run-2 still fires: `impact` warning 93 (`src/roonseek/transfer.py`:204).
- run-3 still fires: `bugs` warning 82 (:259) and `impact` warning 87 (:204) — two sites, so
  H-LANE does not merge them.
- base_sha `10276919fc2f1123cf0d8da7c0d43488087f1bc7`, source repo `~/roonseek`,
  EXPECTED_TREE_DIFF_SHA256 `66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69`,
  EXPECTED_TOUCHED_PATHS `src/roonseek/transfer.py`.

**Pick 2 — should-quiet-1 (`~/triggarr`), predicted 3/3.**
- No run goes quiet. Every run keeps a `bugs` row at `triggarr/web/validation.py`:84-85 —
  run-1 warning 88, run-2 critical 100 (plus a separate `security` warning 94 at :80, five lines
  away, so a different site), run-3 warning 94. `bugs` gets only a −2 offset, and its precision is
  at or above the pool, so B-REWEIGHT correctly leaves it; H-LANE only merges rows, it never
  removes a run's last firing row.
- It is picked by the D-16 tie rule, not because the replay predicts movement: it is the control
  that shows whether fresh runs stay at their archived level.
- base_sha `98eb4196e2c060b38775ab40d6d23e2dc2bee024`, source repo `~/triggarr`,
  EXPECTED_TREE_DIFF_SHA256 `a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a`,
  EXPECTED_TOUCHED_PATHS `triggarr/web/validation.py`.

**Predicted FP count for the 6 runs = 2 + 3 = 5** (should-quiet-3 2/3 + should-quiet-1 3/3).
The check passes when 5 or fewer of the 6 runs fire a critical/warning.

**Honest notes.**
- should-quiet-6 is codex-driven (a byte-identical codex finding in all three baseline runs, now
  warning 94). D-01 keeps codex as the independent voter, so Wave 1 does not move it, and the
  replay agrees. That is Wave 2's codex-contract ceiling question, recorded as-is.
- should-quiet-1 and should-quiet-4 are bugs-driven, and bugs' precision is at or above the pool,
  so a principled reweight leaves them where they are.
- The pair differs from what 41-07's plan text expected (should-quiet-2 + should-quiet-3): the
  combined replay moved only should-quiet-3 among eligible diffs, so the second pick is the D-16
  tie-break (lowest number), should-quiet-1. The research prediction for the combined headline was
  12/18; the replay measured 14/18. Both are recorded as observed, not tuned.

**Pre-diet caveat (disclosed):** the prediction comes from the Phase-38 archives of the UNCHANGED
2.9.0 plugin, re-scored offline. The Phase-40 diet has since changed the prompts and the dispatch
prose, so fresh runs may find different things for reasons unrelated to Wave 1. The D-11 rule
counts firing runs rather than matching findings, so it is robust to per-run variation — it is NOT
robust to a systematic shift the diet introduced. A miss is read with that in mind.

---

## MEASUREMENT-RUN RULE — the `/deep-review` fix loop + N-01 + N-02 (read this FIRST)

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

**N-02 — auto-memory (binding for every Phase-41 session):** `/clear` does not reset Claude
Code's per-project auto-memory, and the Phase-40 measurement sessions had written run-by-run notes
there — including the expected outcome of the diff under test. Before the first launch of a check,
`p41 park-memory` moves BOTH clones' memory directories aside:

- `~/.claude/projects/-Users-julianamacbook-roonseek/memory` (should-quiet-3)
- `~/.claude/projects/-Users-julianamacbook-triggarr/memory` (should-quiet-1)

The pre-flight and every launch block STOP while either is present, and each pre-run block moves
anything a session wrote there since launch into `~/.b3/automemory-parked-phase41-<check>/` as
evidence before the run starts. `p41 restore-memory` puts your memory back after the last
revert; what the sessions wrote is kept beside it and never merged back. A run whose session
started with the memory directory present is VOID.

**Usage limit and stalls.** A usage-limit pause that auto-resumes inside the SAME conversation
does not void the run (Phase-40 precedent): let it finish and run the post block as normal. A run
that stalls between steps — the review stops mid-way and does not continue on its own — is VOID:
run `p41 <diff>-void <n>` and redo that run from its pre block.

**Fixes are DECLINED on every one of these runs, so no fix-agent behaviour is exercised here.**

---

## 4. How to run a block (do this once per terminal window)

Blocks cannot be pasted into the terminal line by line (zsh treats `#` lines as commands and a
failed check would close the window). Instead, paste this ONCE into each new terminal window. It
defines a `p41` command that pulls one named block out of this file and runs it under bash:

```text
P41=~/turingmind-code-review/docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase41.md
p41() {
  mkdir -p ~/.b3
  awk -v b="$1" '$0=="# BLOCK: "b{f=1} f{print} $0=="# END: "b{exit}' "$P41" > ~/.b3/p41.sh
  tail -1 ~/.b3/p41.sh | grep -qx "# END: $1" || { echo "p41: no block named '$1'"; return 2; }
  RUN_N="${2:-1}" bash ~/.b3/p41.sh && echo "p41: BLOCK OK ($1)" || echo "p41: BLOCK FAILED ($1)"
}
```

Then run a block by name: `p41 preflight`. Run blocks take the run number as a second word:
`p41 sq3-pre 2`. Every block writes its scratch output to `~/.b3/p41-*.out`, and the active
check lives in `~/.b3/phase41-active.env`. If a block prints `BLOCK FAILED`, stop and paste the
whole output to the assistant.

### The order, per check

| # | Where | What you type |
|---|---|---|
| 1 | terminal | `p41 park-memory` — answer `final` (or `final-2`) |
| 2 | terminal | `p41 preflight` — answer the same label |
| 3 | terminal | `p41 sq3-fresh` then `p41 sq3-launch` |
| 4 | NEW terminal tab | paste the one launch line `sq3-launch` printed — Claude Code opens |
| 5 | terminal | `p41 fingerprint` — type the model name exactly as that session shows it |
| 6 | terminal | `p41 sq3-pre 1` — it tells you to `/clear`; do it, then type `CLEARED` |
| 7 | Claude Code tab | `/vibe-check:deep-review` — decline every fix (MEASUREMENT-RUN RULE) |
| 8 | terminal | `p41 sq3-post 1` — note the `codex` value it prints in the worklog |
| 9 | — | repeat 6-8 with `2`, then `3` |
| 10 | terminal | `p41 sq3-revert`, then close the Claude Code tab (`/exit`) |
| 11 | — | repeat 3-10 for should-quiet-1 with `sq1-` in place of `sq3-` |
| 12 | terminal | `p41 restore-memory` |
| 13 | terminal | `p41 pass-json` — then hand `PASS.json` to the assistant |

A run that stops between steps 6 and 8 is VOID, not failed: run `p41 sq3-void <n>` (or
`sq1-void`) and redo that run from step 6. A run that already committed is evidence and is never
voided.

---

## 5. STEP 0 — pre-flight (once per check)

This is the only place `SNAP_ROOT` and `PLUGIN_ROOT` are defined. `SNAP_ROOT` is the snapshot the
assistant built with `batchsnap.py build --batch 4` and pinned below; `PLUGIN_ROOT` is always
`$SNAP_ROOT/plugins/vibe-check`, the folder holding `.claude-plugin/plugin.json`, and it is the
ONLY value `--plugin-dir` ever receives. Handing `--plugin-dir` the snapshot root instead loads no
plugin at all, and the run silently measures the installed cache rather than the Wave-1 scorer —
which is why the `plugin.json` check below is a stopping gate, not a comment. Pre-flight writes
both values to `~/.b3/phase41-active.env`; every later block reads them from there and
re-verifies the snapshot before using them.

**Pinned snapshot for `final`:** `~/.vibe-check-snapshots/batch4-UNPINNED` (the `final-2`
snapshot is pinned by the assistant only after a D-11 miss and the one re-tune).

Pre-flight also checks, in order: the Phase-40 final check is adjudicated (so Phase 41 never runs
over an open Phase 40), the installed vibe-check cache has the repo's version (a stale installed
cache has poisoned pre-flights before, even though these runs load the snapshot), every sealed
archive tree is intact, both CLIs answer, both clones' auto-memory is parked (N-02), and both
clones are present and clean. The suite is not re-run here: the snapshot is read-only, and `build`
already ran the suite inside it before sealing and recorded the result in the manifest
(`suite_green`), which this block reads.

```bash
# BLOCK: park-memory
set -euo pipefail
printf 'Which check is this? Type exactly one of final or final-2: '
IFS= read -r LABEL
case "$LABEL" in final|final-2) ;; *) echo 'NOT ONE OF final, final-2 — STOPPING'; exit 1 ;; esac
PARKDIR=~/.b3/automemory-parked-phase41-$LABEL
mkdir -p "$PARKDIR"
for C in roonseek triggarr; do
  MEM=$HOME/.claude/projects/-Users-julianamacbook-$C/memory
  if test -e "$MEM"; then
    test ! -e "$PARKDIR/$C" || { echo "$PARKDIR/$C ALREADY HOLDS PARKED MEMORY — STOPPING"; exit 1; }
    mv "$MEM" "$PARKDIR/$C"
    echo "parked ~/$C auto-memory -> $PARKDIR/$C"
  else
    echo "~/$C has no auto-memory to park"
  fi
  test ! -e "$MEM" || { echo "~/$C AUTO-MEMORY STILL PRESENT — STOPPING"; exit 1; }
done
echo 'BLOCK OK'
# END: park-memory
```

```bash
# BLOCK: preflight
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
P41DIR=docs/design/b3-ground-truth/runs-v2.10-phase41
BSNAP=$REPO/plugins/vibe-check/scripts/batchsnap.py
# the pinned snapshots — final is the Wave-1 tree; final-2 stays empty until a D-12 re-tune
FINAL_SNAP="$HOME/.vibe-check-snapshots/batch4-UNPINNED"
FINAL2_SNAP=''
case "$FINAL_SNAP" in *UNPINNED*)
  echo 'THE final SNAPSHOT IS NOT PINNED YET (ask the assistant) — STOPPING'; exit 1 ;; esac
mkdir -p ~/.b3
printf 'Which check is this? Type exactly one of final or final-2: '
IFS= read -r LABEL
case "$LABEL" in
  final) SNAP_ROOT=$FINAL_SNAP
         PRIOR_PASS=docs/design/b3-ground-truth/runs-v2.10-phase40/final/PASS.json ;;
  final-2) SNAP_ROOT=$FINAL2_SNAP; PRIOR_PASS=$P41DIR/final/PASS.json ;;
  *) echo 'NOT ONE OF final, final-2 — STOPPING'; exit 1 ;;
esac
test -n "$SNAP_ROOT" \
  || { echo 'THE final-2 SNAPSHOT IS NOT PINNED (only after a D-11 miss + re-tune) — STOPPING'; exit 1; }
ARCHIVE_BATCH=$LABEL
RUNS_PER_DIFF=3
SCHEMA=future
# (a) the previous check must already be adjudicated (the same barrier Phase 40 ran)
python3 "$BSNAP" check-pass --file "$REPO/$PRIOR_PASS" > ~/.b3/p41-checkpass.out \
  || { cat ~/.b3/p41-checkpass.out; echo "PREVIOUS CHECK NOT ADJUDICATED ($PRIOR_PASS) — STOPPING"; exit 1; }
test ! -e "$REPO/$P41DIR/$ARCHIVE_BATCH/PASS.json" \
  || { echo "CHECK $ARCHIVE_BATCH IS ALREADY CLOSED (PASS.json exists) — STOPPING"; exit 1; }
# (b) the pinned snapshot is byte-identical to its manifest, and the launch argument is right
PLUGIN_ROOT="$SNAP_ROOT/plugins/vibe-check"
test -d "$SNAP_ROOT" || { echo "PINNED SNAPSHOT $SNAP_ROOT MISSING (ask the assistant) — STOPPING"; exit 1; }
python3 "$BSNAP" verify --snap "$SNAP_ROOT" > ~/.b3/p41-verify.out \
  || { cat ~/.b3/p41-verify.out; echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p41-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
# (c) the manifest's own record: batch 4, a real commit named by the folder, a green suite
mf() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' \
  "$SNAP_ROOT/MANIFEST.json" "$1"; }
test "$(mf batch)" = "4" || { echo 'SNAPSHOT IS NOT A BATCH-4 SNAPSHOT — STOPPING'; exit 1; }
BATCH_SHA=$(mf snapshot_commit)
git -C "$REPO" cat-file -e "$BATCH_SHA^{commit}" \
  || { echo 'SNAPSHOT COMMIT NOT IN THIS REPO — STOPPING'; exit 1; }
test "$(basename "$SNAP_ROOT")" = "batch4-$(printf '%s' "$BATCH_SHA" | cut -c1-12)" \
  || { echo 'SNAPSHOT FOLDER DOES NOT NAME ITS OWN COMMIT — STOPPING'; exit 1; }
SUITE=$(mf suite_green)
printf '%s' "$SUITE" | grep -q 'passed' && ! printf '%s' "$SUITE" | grep -qE 'failed|error' \
  || { echo "SNAPSHOT SUITE NOT RECORDED GREEN ($SUITE) — STOPPING"; exit 1; }
# (d) installed-cache parity: every installed vibe-check version == the repo's plugin.json version
ver() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$1"; }
REPO_VER=$(ver "$REPO/plugins/vibe-check/.claude-plugin/plugin.json")
test "$(ver "$PLUGIN_ROOT/.claude-plugin/plugin.json")" = "$REPO_VER" \
  || { echo 'SNAPSHOT plugin.json VERSION != REPO — STOPPING'; exit 1; }
FOUND=0
for PJ in "$HOME"/.claude/plugins/cache/thejuran/vibe-check/*/.claude-plugin/plugin.json; do
  test -f "$PJ" || continue
  FOUND=$((FOUND + 1))
  test "$(ver "$PJ")" = "$REPO_VER" \
    || { echo "INSTALLED CACHE IS STALE ($PJ is not $REPO_VER) — resync, relaunch — STOPPING"; exit 1; }
done
test "$FOUND" -ge 1 \
  || { echo 'NO INSTALLED vibe-check UNDER plugins/cache/thejuran/vibe-check — STOPPING'; exit 1; }
# (e) the sealed v2.9 runs/ tree equals tag v2.9 and is clean
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test -z "$(git -C "$REPO" status --porcelain docs/design/b3-ground-truth/runs/)" \
  || { echo 'SEALED v2.9 RUNS TREE DIRTY — STOPPING; report it'; exit 1; }
# (f) the sealed Phase-38 baseline and the closed Phase-40 runs: pinned trees, clean
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
test -z "$(git -C "$REPO" status --porcelain docs/design/b3-ground-truth/runs-v2.10/)" \
  || { echo 'SEALED v2.10 BASELINE TREE DIRTY — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase40)" \
   = "29d1344b6b93136d1ae0273008ce34a154360e7b" \
  || { echo 'SEALED PHASE-40 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test -z "$(git -C "$REPO" status --porcelain docs/design/b3-ground-truth/runs-v2.10-phase40/)" \
  || { echo 'SEALED PHASE-40 RUNS TREE DIRTY — STOPPING; report it'; exit 1; }
# (g) both CLIs answer (their exact versions are checked against the pin by fingerprint)
claude --version > /dev/null || { echo 'claude --version FAILED — STOPPING'; exit 1; }
codex --version > /dev/null || { echo 'codex --version FAILED — STOPPING'; exit 1; }
# (h) N-02 — both clones' auto-memory is parked
for C in roonseek triggarr; do
  test ! -e "$HOME/.claude/projects/-Users-julianamacbook-$C/memory" \
    || { echo "~/$C AUTO-MEMORY IS NOT PARKED — run p41 park-memory — STOPPING"; exit 1; }
done
# (i) both clones: present, local .turingmind/ exclude in place, uv.lock present, and either
#     clean or already prepared for THEIR diff by the fresh block
for PAIR in roonseek:should-quiet-3 triggarr:should-quiet-1; do
  C=${PAIR%%:*}; DIFF=${PAIR#*:}
  test -d "$HOME/$C/.git" || { echo "CLONE ~/$C MISSING — STOPPING"; exit 1; }
  grep -qx '.turingmind/' "$HOME/$C/.git/info/exclude" \
    || { echo "~/$C HAS NO LOCAL .turingmind/ EXCLUDE (tell the assistant) — STOPPING"; exit 1; }
  test -f "$HOME/$C/uv.lock" || { echo "~/$C/uv.lock MISSING — STOPPING"; exit 1; }
  if test -e "$HOME/$C/.turingmind/state/.b3-inprogress"; then
    grep -q "diff_id=$DIFF" "$HOME/$C/.turingmind/state/.b3-inprogress" \
      || { echo "~/$C IS IN PROGRESS FOR ANOTHER DIFF — STOPPING"; exit 1; }
  else
    test -z "$(git -C "$HOME/$C" status --porcelain)" \
      || { git -C "$HOME/$C" status --short | head -5
           echo "CLONE ~/$C NOT CLEAN — commit or move YOUR work aside first — STOPPING"; exit 1; }
    test -n "$(git -C "$HOME/$C" branch --show-current)" \
      || { echo "CLONE ~/$C IS DETACHED — switch it back to its branch — STOPPING"; exit 1; }
  fi
done
# record the active check for every later block
{
  printf 'ARCHIVE_BATCH=%q\n' "$ARCHIVE_BATCH"
  printf 'SNAP_ROOT=%q\n' "$SNAP_ROOT"
  printf 'PLUGIN_ROOT=%q\n' "$PLUGIN_ROOT"
  printf 'BATCH_SHA=%q\n' "$BATCH_SHA"
  printf 'SCHEMA=%q\n' "$SCHEMA"
  printf 'RUNS_PER_DIFF=%q\n' "$RUNS_PER_DIFF"
} > "$ENV"
echo "check:        $ARCHIVE_BATCH ($RUNS_PER_DIFF runs per diff, envelope schema $SCHEMA)"
echo "snapshot:     $SNAP_ROOT"
echo "plugin root:  $PLUGIN_ROOT"
echo "batch commit: $BATCH_SHA"
echo "installed:    vibe-check $REPO_VER (== repo)"
echo 'BLOCK OK'
# END: preflight
```

---

## 6. STEP 0.25 — harness fingerprint (after EVERY Claude Code launch)

Run this after the launch line has opened Claude Code and before that session's first run. It
appends one session block to `RUN-METHOD-NOTES-phase41.md` and commits it. It records the snapshot
(`batch-sha`, `snapshot-root`, `plugin-root`) alongside the CLI and model versions, so every run is
bound to the exact plugin tree it measured. `RUN-METHOD-NOTES-v2.10.md` (Phase 38) and
`RUN-METHOD-NOTES-phase40.md` (Phase 40) are NEVER appended to by Phase 41.

```bash
# BLOCK: fingerprint
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
NOTES=docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase41.md
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p41-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p41-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
git -C "$REPO" diff --quiet -- "$NOTES" && git -C "$REPO" diff --cached --quiet -- "$NOTES" \
  || { echo 'THE PHASE-41 NOTES FILE HAS UNCOMMITTED CHANGES — STOPPING'; exit 1; }
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
# the pin, parsed from the COMMITTED Phase-41 notes blob (never the live file)
BLOB=$(git -C "$REPO" show "HEAD:$NOTES") \
  || { echo 'PHASE-41 NOTES FILE NOT COMMITTED — STOPPING'; exit 1; }
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
# every earlier Phase-41 session must have run the same model (this file only)
printf '%s\n' "$BLOB" | { grep '^model: ' || true; } | sed 's/^model: //' > ~/.b3/p41-models.out
while IFS= read -r PRIOR; do
  test -n "$PRIOR" || continue
  PNORM=$(printf '%s' "$PRIOR" | tr 'A-Z-' 'a-z ' | tr -s ' ')
  test "$PNORM" = "$NORM" \
    || { echo "HARNESS DRIFT — an earlier session ran '$PRIOR' — STOPPING; $DRIFT"; exit 1; }
done < ~/.b3/p41-models.out
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
git -C "$REPO" commit -q --only -m "runs(41): harness fingerprint $SID_NEW" -- "$NOTES"
FPCOMMIT=$(git -C "$REPO" log -1 --format=%H -- "$NOTES")
test "$(git -C "$REPO" show --name-only --format= "$FPCOMMIT")" = "$NOTES" \
  || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
echo "session $SID_NEW fingerprinted in commit $FPCOMMIT"
echo 'BLOCK OK'
# END: fingerprint
```

---

## 7. Per-diff blocks — prepare the clone, then launch

Each diff gets its clone pinned to the recorded base, the patch applied ONCE (kept until the revert
block), and every existing state file in the clone's `.turingmind/state/` parked in
`.b3-parked-phase41/`. Parking all of them (not only the expected file name) is what lets the
post-run block capture "the ONE state file this run wrote" by construction: the shipped tool has
written differently-named state files before (`<repo>-main.json`, `<repo>-HEAD.json`). The values
below (base_sha, tree-diff sha, touched paths) are copied from `diffs/<diff>.provenance` and match
the diff's `## Diff:` section of `RUN-CHECKLIST-v2.10.md`.

Both clones already carry the Phase-38 local exclude for `.turingmind/` (v2.10 STEP 0.5), and
pre-flight checks it. If the clean-tree check stops on your own work in the clone, commit it or
move it aside yourself — the runbook never touches your work.

**Why the launch line carries `--allowedTools` and `--permission-mode manual`.** The snapshot lives
outside the clone. On 2026-09-27 the first Phase-40 launch without `--allowedTools` ran under Claude
Code's auto-mode permission classifier, which blocked the orchestrator's reads of the snapshot as
"code from external" and voided the attempt. The flag pre-approves the tools the review needs.
Even so, one call (the Phase-0.6 config reader) was still denied by the auto-mode classifier, so
the line also selects `--permission-mode manual`: the classifier exists only in auto mode, and with
the tools pre-approved manual mode asks nothing. Both flags change permission handling only, never
the plugin — the Phase-40 `final` check used exactly this line.

### should-quiet-3 — prepare (once per check, before run 1)

```bash
# BLOCK: sq3-fresh
set -euo pipefail
REPO=~/turingmind-code-review
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-3.patch
test -f ~/.b3/phase41-active.env \
  || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase41
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
git switch --detach 10276919fc2f1123cf0d8da7c0d43488087f1bc7
test "$(git rev-parse HEAD)" = "10276919fc2f1123cf0d8da7c0d43488087f1bc7" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE; it stays applied until sq3-revert
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
printf 'diff_id=should-quiet-3\nbase_sha=10276919fc2f1123cf0d8da7c0d43488087f1bc7\n' \
  > "$STATE_DIR/.b3-inprogress"
printf 'had_prior_state=%s\nstart_branch=%s\nstart_sha=%s\nparked=%s\n' \
  "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" "$PARKED" >> "$STATE_DIR/.b3-inprogress"
chflags uchg ~/roonseek/uv.lock
echo "should-quiet-3 ready at $(git rev-parse HEAD), $PARKED state file(s) parked"
echo 'BLOCK OK'
# END: sq3-fresh
```

### should-quiet-3 — launch

```bash
# BLOCK: sq3-launch
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
grep -q 'diff_id=should-quiet-3' ~/roonseek/.turingmind/state/.b3-inprogress \
  || { echo 'CLONE NOT PREPARED — run p41 sq3-fresh first — STOPPING'; exit 1; }
# N-02 — a session that STARTS with the clone's auto-memory present is VOID
test ! -e "$HOME/.claude/projects/-Users-julianamacbook-roonseek/memory" \
  || { echo 'AUTO-MEMORY FOR ~/roonseek IS NOT PARKED — run p41 park-memory — STOPPING'; exit 1; }
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p41-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p41-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
echo 'Open a NEW terminal tab and paste exactly this one line:'
echo ''
echo "  cd ~/roonseek && claude --permission-mode manual --plugin-dir \"$PLUGIN_ROOT\" --allowedTools \"Bash,Read,Write,Edit,Grep,Glob,Task,Agent\""
echo ''
echo 'Then come back here and run: p41 fingerprint'
echo 'BLOCK OK'
# END: sq3-launch
```

### should-quiet-1 — prepare (once per check, before run 1)

```bash
# BLOCK: sq1-fresh
set -euo pipefail
REPO=~/turingmind-code-review
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-1.patch
test -f ~/.b3/phase41-active.env \
  || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase41
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
git switch --detach 98eb4196e2c060b38775ab40d6d23e2dc2bee024
test "$(git rev-parse HEAD)" = "98eb4196e2c060b38775ab40d6d23e2dc2bee024" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE; it stays applied until sq1-revert
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
printf 'diff_id=should-quiet-1\nbase_sha=98eb4196e2c060b38775ab40d6d23e2dc2bee024\n' \
  > "$STATE_DIR/.b3-inprogress"
printf 'had_prior_state=%s\nstart_branch=%s\nstart_sha=%s\nparked=%s\n' \
  "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" "$PARKED" >> "$STATE_DIR/.b3-inprogress"
chflags uchg ~/triggarr/uv.lock
echo "should-quiet-1 ready at $(git rev-parse HEAD), $PARKED state file(s) parked"
echo 'BLOCK OK'
# END: sq1-fresh
```

### should-quiet-1 — launch

```bash
# BLOCK: sq1-launch
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
grep -q 'diff_id=should-quiet-1' ~/triggarr/.turingmind/state/.b3-inprogress \
  || { echo 'CLONE NOT PREPARED — run p41 sq1-fresh first — STOPPING'; exit 1; }
# N-02 — a session that STARTS with the clone's auto-memory present is VOID
test ! -e "$HOME/.claude/projects/-Users-julianamacbook-triggarr/memory" \
  || { echo 'AUTO-MEMORY FOR ~/triggarr IS NOT PARKED — run p41 park-memory — STOPPING'; exit 1; }
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p41-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p41-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
echo 'Open a NEW terminal tab and paste exactly this one line:'
echo ''
echo "  cd ~/triggarr && claude --permission-mode manual --plugin-dir \"$PLUGIN_ROOT\" --allowedTools \"Bash,Read,Write,Edit,Grep,Glob,Task,Agent\""
echo ''
echo 'Then come back here and run: p41 fingerprint'
echo 'BLOCK OK'
# END: sq1-launch
```

The launch line every block prints is always `claude --plugin-dir "$PLUGIN_ROOT"` with the path
filled in, and it is only printed after the snapshot re-verified, `plugin.json` was found and the
clone's auto-memory was confirmed parked.

---

## 8. Per-run blocks

Each run is: `p41 <diff>-pre <n>` → `/clear`, type `CLEARED` → `/vibe-check:deep-review` in the
Claude Code tab, declining every fix → `p41 <diff>-post <n>`. The run number `<n>` is `1`, `2`,
`3`.

Runs land in `docs/design/b3-ground-truth/runs-v2.10-phase41/final/<diff>/run-<n>/` (or
`runs-v2.10-phase41/final-2/...` for a D-12 re-check) — NEVER in `runs-v2.10/` (the sealed Phase-38
baseline) or `runs-v2.10-phase40/` (the closed Phase-40 checks). Each committed run holds exactly
seven files: `clear.txt`, `session.txt`, `state.json`, `tree.diff`, `tree.diff.sha256`,
`report.md` (the rendered report, verbatim) and `transcript.jsonl.sha256`.

**Why the transcript itself is not committed.** `transcript.jsonl` (the session plus every review
agent's sub-transcript) is written into the run folder, stays on this machine, and is gitignored.
A Claude Code transcript carries your private global instructions and account details verbatim,
and this repository is published. The committed `transcript.jsonl.sha256` binds the local file to
the run: `pass-json` refuses a transcript that changed after capture. The post-run block checks the
transcript is gitignored BEFORE anything is staged.

**Provenance.** The post-run block voids a run whose transcript names the working repo's plugin
folder or the INSTALLED vibe-check cache (`plugins/cache/thejuran/vibe-check`), and it requires the
transcript to name `$PLUGIN_ROOT`. The pattern is deliberately narrowed to the vibe-check cache:
the Codex plugin's own cache folder is legitimately loaded by every run with a Codex pass.

**The codex condition.** The post-run block prints the pass's `codex.status` (`joined`, `skipped`
or `off`) from the committed `state.json`, puts it in the run's commit message, and `pass-json`
copies it into PASS.json. A `skipped` run is recorded, not voided (D-13).

### should-quiet-3 — before run `<n>`

```bash
# BLOCK: sq3-pre
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
NOTES=docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase41.md
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-3.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
test "$N" -le "$RUNS_PER_DIFF" \
  || { echo "CHECK $ARCHIVE_BATCH HAS $RUNS_PER_DIFF RUN(S) PER DIFF — STOPPING"; exit 1; }
D=docs/design/b3-ground-truth/runs-v2.10-phase41/$ARCHIVE_BATCH/should-quiet-3
RP=$D/run-$N
RUN_DIR=$REPO/$RP
if test "$N" -gt 1; then
  test -n "$(git -C "$REPO" log -1 --format=%H -- "$D/run-$((N - 1))/")" \
    || { echo "RUN $((N - 1)) IS NOT COMMITTED YET — STOPPING"; exit 1; }
fi
# (1) the snapshot is re-verified immediately before this run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p41-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p41-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
# (2) every sealed tree is intact
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase40)" \
   = "29d1344b6b93136d1ae0273008ce34a154360e7b" \
  || { echo 'SEALED PHASE-40 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
# (3) the clone: this diff, detached at its base, patch applied, no state file, uv.lock held
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
grep -q 'diff_id=should-quiet-3' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — run p41 sq3-fresh — STOPPING'; exit 1; }
test -z "$(git branch --show-current)" || { echo 'CLONE NOT DETACHED — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "10276919fc2f1123cf0d8da7c0d43488087f1bc7" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
test ! -e "$RUN_DIR" \
  || { echo "RUN $N ALREADY HAS A FOLDER — if unrun: p41 sq3-void $N — STOPPING"; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo "STATE NOT EMPTY — an unfinished run? p41 sq3-void — STOPPING"; exit 1; }
git apply --reverse --check "$PATCH" \
  || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
stat -f %Sf ~/roonseek/uv.lock | grep -q uchg \
  || { echo 'uv.lock UNPROTECTED — STOPPING'; exit 1; }
# (4) N-02 — anything the session wrote to auto-memory since launch is moved aside as evidence
#     BEFORE this run, so run 2/3 can never read what run 1 learned
MEM=$HOME/.claude/projects/-Users-julianamacbook-roonseek/memory
if test -e "$MEM"; then
  EVID=~/.b3/automemory-parked-phase41-$ARCHIVE_BATCH/roonseek-written-before-sq3-run-$N
  test ! -e "$EVID" || { echo "EVIDENCE DIR $EVID ALREADY EXISTS — STOPPING"; exit 1; }
  mkdir -p "$(dirname "$EVID")"
  mv "$MEM" "$EVID"
  echo "auto-memory written during this check moved aside to $EVID (evidence, never merged back)"
fi
test ! -e "$MEM" || { echo 'AUTO-MEMORY STILL PRESENT — STOPPING'; exit 1; }
# (5) N-01 conversation isolation, typed attestation
echo 'In the Claude Code tab: type /clear and press Enter. Do it now, for EVERY run.'
printf 'Type CLEARED to confirm you did this JUST NOW: '
IFS= read -r ACK
test "$ACK" = "CLEARED" || { echo 'NOT CLEARED — STOPPING'; exit 1; }
mkdir -p "$RUN_DIR"
printf '%s CLEARED\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" > "$RUN_DIR/clear.txt"
# (6) session binding from COMMITTED blobs, before the run; bound to THIS snapshot
BLOB=$(git -C "$REPO" show "HEAD:$NOTES")
HDR='^## Harness fingerprint — [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}[+-][0-9]{4}$'
SID=$(printf '%s\n' "$BLOB" | { grep -E "$HDR" || true; } | tail -1 \
  | sed 's/^## Harness fingerprint — //')
test -n "$SID" || { echo 'NO COMMITTED FINGERPRINT — run p41 fingerprint — STOPPING'; exit 1; }
FPC=$(git -C "$REPO" log --format=%H --reverse -S"## Harness fingerprint — $SID" -- "$NOTES" \
  | head -1 || true)
test -n "$FPC" || { echo 'FINGERPRINT COMMIT NOT FOUND — STOPPING'; exit 1; }
BLK=$(printf '%s\n' "$BLOB" \
  | awk -v h="## Harness fingerprint — $SID" '$0==h{f=1;next} /^## /{f=0} f')
printf '%s\n' "$BLK" | grep -qxF "batch-sha: $BATCH_SHA" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER SNAPSHOT — p41 fingerprint — STOPPING'; exit 1; }
printf '%s\n' "$BLK" | grep -qxF "plugin-root: $PLUGIN_ROOT" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER PLUGIN ROOT — STOPPING'; exit 1; }
printf '%s\n%s\n' "$SID" "$FPC" > "$RUN_DIR/session.txt"
echo "run $N ready — in the Claude Code tab type: /vibe-check:deep-review"
echo 'Decline every fix: Step A option 4 (Skip fixes), Step C option 3 (Abandon for now).'
echo "Then come back here and run: p41 sq3-post $N"
echo 'BLOCK OK'
# END: sq3-pre
```

### should-quiet-3 — after run `<n>`

```bash
# BLOCK: sq3-post
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase41/$ARCHIVE_BATCH/should-quiet-3/run-$N
RUN_DIR=$REPO/$RP
EXPECTED_HEAD=10276919fc2f1123cf0d8da7c0d43488087f1bc7
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" \
  || { echo 'HEAD MOVED DURING THE RUN (was a fix committed?) — STOPPING'; exit 1; }
# the snapshot is still byte-identical after the run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p41-verify.out || { echo 'SNAPSHOT CHANGED DURING THE RUN — STOPPING'; exit 1; }
# the pre-run records exist (this block never writes them)
test -f "$RUN_DIR/clear.txt" || { echo 'clear.txt MISSING — p41 sq3-void — STOPPING'; exit 1; }
test -f "$RUN_DIR/session.txt" \
  || { echo 'session.txt MISSING — p41 sq3-void — STOPPING'; exit 1; }
# STEP 8e — the ONE state file this run wrote (every older one was parked by sq3-fresh)
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
   = "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69" \
  || { echo 'FULL WORKTREE DIFF != THE PLANTED DIFF — STOPPING'; exit 1; }
# STEP 8f2 — the touched-path set
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/roonseek/transfer.py" \
  || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — no stray untracked files outside the state dir
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" \
  || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — STOPPING'; exit 1; }
# STEP 8g — isolation: exactly one pass, at the pinned head
python3 - "$RUN_DIR/state.json" "$EXPECTED_HEAD" <<'PY' \
  || { echo 'NOT ONE ISOLATED PASS AT THE PINNED HEAD — p41 sq3-void — STOPPING'; exit 1; }
import json, sys
s = json.load(open(sys.argv[1]))
assert len(s["passes"]) == 1, "NOT ISOLATED: passes=%d" % len(s["passes"])
assert s["passes"][-1]["head_sha"] == sys.argv[2], "HEAD MISMATCH"
print("OK one isolated pass at", sys.argv[2])
PY
# the codex condition of this run (D-13): joined / skipped / off — a SKIP is recorded, not voided
CODEX=$(python3 -c 'import json,sys; c=json.load(open(sys.argv[1]))["passes"][-1].get("codex"); print(c.get("status","absent") if isinstance(c,dict) else "absent")' "$RUN_DIR/state.json")
echo "codex this run: $CODEX   <- write it in the worklog (section 9)"
# CAPTURE — the session transcript (+ every agent sub-transcript) and the rendered report
PROJ=$HOME/.claude/projects/$(printf '%s' "$HOME/roonseek" | sed 's/[^A-Za-z0-9]/-/g')
test -d "$PROJ" \
  || { echo 'NO CLAUDE CODE TRANSCRIPT FOLDER FOR ~/roonseek — STOPPING'; exit 1; }
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
git -C "$REPO" check-ignore -q "$RP/transcript.jsonl" \
  || { echo 'transcript.jsonl IS NOT GITIGNORED — nothing committed — STOPPING'; exit 1; }
git -C "$REPO" add "$RP/"
git -C "$REPO" commit -q --only \
  -m "runs(41): $ARCHIVE_BATCH should-quiet-3 run $N (state key $STATE_KEY, codex $CODEX)" -- "$RP/"
RC=$(git -C "$REPO" log -1 --format=%H -- "$RP/")
# scope gate: EXACTLY seven files — the five Phase-38 artifacts plus report.md and
# transcript.jsonl.sha256 (transcript.jsonl itself stays local and gitignored)
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
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase40)" \
   = "29d1344b6b93136d1ae0273008ce34a154360e7b" \
  || { echo 'SEALED PHASE-40 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
echo "run $N of should-quiet-3 captured and committed ($RC), codex $CODEX"
# LAST — the envelope shape. A failure here is a RESULT, not a void run: the run is committed.
python3 "$REPO/plugins/vibe-check/scripts/state_shape.py" "$RUN_DIR/state.json" \
  --schema "$SCHEMA" \
  || { echo 'ENVELOPE SHAPE VIOLATION — do NOT re-run; tell the assistant — STOPPING'; exit 1; }
echo "state_shape PASS ($SCHEMA)"
echo 'BLOCK OK'
# END: sq3-post
```

### should-quiet-3 — void an unfinished run `<n>`

Use this only when a run STOPPED before `sq3-post` committed it, or stalled between steps. It
removes the run's uncommitted folder and any state file the run wrote, and checks the clone is still
exactly base + patch.

```bash
# BLOCK: sq3-void
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-3.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase41/$ARCHIVE_BATCH/should-quiet-3/run-$N
test -z "$(git -C "$REPO" log -1 --format=%H -- "$RP/")" \
  || { echo "RUN $N IS COMMITTED — it is evidence, not voidable — STOPPING"; exit 1; }
rm -rf "${REPO:?}/$RP"
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
grep -q 'diff_id=should-quiet-3' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — STOPPING'; exit 1; }
find "$STATE_DIR" -maxdepth 1 -name '*.json' -print -delete
test "$(git rev-parse HEAD)" = "10276919fc2f1123cf0d8da7c0d43488087f1bc7" \
  || { echo 'HEAD MOVED — run p41 sq3-revert, then p41 sq3-fresh — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" \
   = "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69" \
  || { echo 'CLONE DRIFTED — p41 sq3-revert, then p41 sq3-fresh — STOPPING'; exit 1; }
echo "run $N voided — redo it: p41 sq3-pre $N"
echo 'BLOCK OK'
# END: sq3-void
```

### should-quiet-1 — before run `<n>`

```bash
# BLOCK: sq1-pre
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
NOTES=docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase41.md
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-1.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
test "$N" -le "$RUNS_PER_DIFF" \
  || { echo "CHECK $ARCHIVE_BATCH HAS $RUNS_PER_DIFF RUN(S) PER DIFF — STOPPING"; exit 1; }
D=docs/design/b3-ground-truth/runs-v2.10-phase41/$ARCHIVE_BATCH/should-quiet-1
RP=$D/run-$N
RUN_DIR=$REPO/$RP
if test "$N" -gt 1; then
  test -n "$(git -C "$REPO" log -1 --format=%H -- "$D/run-$((N - 1))/")" \
    || { echo "RUN $((N - 1)) IS NOT COMMITTED YET — STOPPING"; exit 1; }
fi
# (1) the snapshot is re-verified immediately before this run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p41-verify.out || { echo 'SNAPSHOT DRIFTED OR MISSING — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'PLUGIN ROOT HAS NO plugin.json — WRONG --plugin-dir ARGUMENT — STOPPING'; exit 1; }
test "$(tail -1 ~/.b3/p41-verify.out)" = "plugin_root: $PLUGIN_ROOT" \
  || { echo 'verify PRINTED A DIFFERENT PLUGIN ROOT — STOPPING'; exit 1; }
# (2) every sealed tree is intact
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase40)" \
   = "29d1344b6b93136d1ae0273008ce34a154360e7b" \
  || { echo 'SEALED PHASE-40 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
# (3) the clone: this diff, detached at its base, patch applied, no state file, uv.lock held
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
grep -q 'diff_id=should-quiet-1' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — run p41 sq1-fresh — STOPPING'; exit 1; }
test -z "$(git branch --show-current)" || { echo 'CLONE NOT DETACHED — STOPPING'; exit 1; }
test "$(git rev-parse HEAD)" = "98eb4196e2c060b38775ab40d6d23e2dc2bee024" \
  || { echo 'WRONG BASE — STOPPING'; exit 1; }
test ! -e "$RUN_DIR" \
  || { echo "RUN $N ALREADY HAS A FOLDER — if unrun: p41 sq1-void $N — STOPPING"; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo "STATE NOT EMPTY — an unfinished run? p41 sq1-void — STOPPING"; exit 1; }
git apply --reverse --check "$PATCH" \
  || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
stat -f %Sf ~/triggarr/uv.lock | grep -q uchg \
  || { echo 'uv.lock UNPROTECTED — STOPPING'; exit 1; }
# (4) N-02 — anything the session wrote to auto-memory since launch is moved aside as evidence
#     BEFORE this run, so run 2/3 can never read what run 1 learned
MEM=$HOME/.claude/projects/-Users-julianamacbook-triggarr/memory
if test -e "$MEM"; then
  EVID=~/.b3/automemory-parked-phase41-$ARCHIVE_BATCH/triggarr-written-before-sq1-run-$N
  test ! -e "$EVID" || { echo "EVIDENCE DIR $EVID ALREADY EXISTS — STOPPING"; exit 1; }
  mkdir -p "$(dirname "$EVID")"
  mv "$MEM" "$EVID"
  echo "auto-memory written during this check moved aside to $EVID (evidence, never merged back)"
fi
test ! -e "$MEM" || { echo 'AUTO-MEMORY STILL PRESENT — STOPPING'; exit 1; }
# (5) N-01 conversation isolation, typed attestation
echo 'In the Claude Code tab: type /clear and press Enter. Do it now, for EVERY run.'
printf 'Type CLEARED to confirm you did this JUST NOW: '
IFS= read -r ACK
test "$ACK" = "CLEARED" || { echo 'NOT CLEARED — STOPPING'; exit 1; }
mkdir -p "$RUN_DIR"
printf '%s CLEARED\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" > "$RUN_DIR/clear.txt"
# (6) session binding from COMMITTED blobs, before the run; bound to THIS snapshot
BLOB=$(git -C "$REPO" show "HEAD:$NOTES")
HDR='^## Harness fingerprint — [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}[+-][0-9]{4}$'
SID=$(printf '%s\n' "$BLOB" | { grep -E "$HDR" || true; } | tail -1 \
  | sed 's/^## Harness fingerprint — //')
test -n "$SID" || { echo 'NO COMMITTED FINGERPRINT — run p41 fingerprint — STOPPING'; exit 1; }
FPC=$(git -C "$REPO" log --format=%H --reverse -S"## Harness fingerprint — $SID" -- "$NOTES" \
  | head -1 || true)
test -n "$FPC" || { echo 'FINGERPRINT COMMIT NOT FOUND — STOPPING'; exit 1; }
BLK=$(printf '%s\n' "$BLOB" \
  | awk -v h="## Harness fingerprint — $SID" '$0==h{f=1;next} /^## /{f=0} f')
printf '%s\n' "$BLK" | grep -qxF "batch-sha: $BATCH_SHA" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER SNAPSHOT — p41 fingerprint — STOPPING'; exit 1; }
printf '%s\n' "$BLK" | grep -qxF "plugin-root: $PLUGIN_ROOT" \
  || { echo 'LATEST FINGERPRINT IS FOR ANOTHER PLUGIN ROOT — STOPPING'; exit 1; }
printf '%s\n%s\n' "$SID" "$FPC" > "$RUN_DIR/session.txt"
echo "run $N ready — in the Claude Code tab type: /vibe-check:deep-review"
echo 'Decline every fix: Step A option 4 (Skip fixes), Step C option 3 (Abandon for now).'
echo "Then come back here and run: p41 sq1-post $N"
echo 'BLOCK OK'
# END: sq1-pre
```

### should-quiet-1 — after run `<n>`

```bash
# BLOCK: sq1-post
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase41/$ARCHIVE_BATCH/should-quiet-1/run-$N
RUN_DIR=$REPO/$RP
EXPECTED_HEAD=98eb4196e2c060b38775ab40d6d23e2dc2bee024
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" \
  || { echo 'HEAD MOVED DURING THE RUN (was a fix committed?) — STOPPING'; exit 1; }
# the snapshot is still byte-identical after the run
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  > ~/.b3/p41-verify.out || { echo 'SNAPSHOT CHANGED DURING THE RUN — STOPPING'; exit 1; }
# the pre-run records exist (this block never writes them)
test -f "$RUN_DIR/clear.txt" || { echo 'clear.txt MISSING — p41 sq1-void — STOPPING'; exit 1; }
test -f "$RUN_DIR/session.txt" \
  || { echo 'session.txt MISSING — p41 sq1-void — STOPPING'; exit 1; }
# STEP 8e — the ONE state file this run wrote (every older one was parked by sq1-fresh)
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
   = "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a" \
  || { echo 'FULL WORKTREE DIFF != THE PLANTED DIFF — STOPPING'; exit 1; }
# STEP 8f2 — the touched-path set
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/validation.py" \
  || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — no stray untracked files outside the state dir
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" \
  || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — STOPPING'; exit 1; }
# STEP 8g — isolation: exactly one pass, at the pinned head
python3 - "$RUN_DIR/state.json" "$EXPECTED_HEAD" <<'PY' \
  || { echo 'NOT ONE ISOLATED PASS AT THE PINNED HEAD — p41 sq1-void — STOPPING'; exit 1; }
import json, sys
s = json.load(open(sys.argv[1]))
assert len(s["passes"]) == 1, "NOT ISOLATED: passes=%d" % len(s["passes"])
assert s["passes"][-1]["head_sha"] == sys.argv[2], "HEAD MISMATCH"
print("OK one isolated pass at", sys.argv[2])
PY
# the codex condition of this run (D-13): joined / skipped / off — a SKIP is recorded, not voided
CODEX=$(python3 -c 'import json,sys; c=json.load(open(sys.argv[1]))["passes"][-1].get("codex"); print(c.get("status","absent") if isinstance(c,dict) else "absent")' "$RUN_DIR/state.json")
echo "codex this run: $CODEX   <- write it in the worklog (section 9)"
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
git -C "$REPO" check-ignore -q "$RP/transcript.jsonl" \
  || { echo 'transcript.jsonl IS NOT GITIGNORED — nothing committed — STOPPING'; exit 1; }
git -C "$REPO" add "$RP/"
git -C "$REPO" commit -q --only \
  -m "runs(41): $ARCHIVE_BATCH should-quiet-1 run $N (state key $STATE_KEY, codex $CODEX)" -- "$RP/"
RC=$(git -C "$REPO" log -1 --format=%H -- "$RP/")
# scope gate: EXACTLY seven files — the five Phase-38 artifacts plus report.md and
# transcript.jsonl.sha256 (transcript.jsonl itself stays local and gitignored)
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
git -C "$REPO" diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/ \
  || { echo 'SEALED v2.9 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10)" \
   = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a" \
  || { echo 'SEALED v2.10 BASELINE TREE DIFFERS — STOPPING; report it'; exit 1; }
test "$(git -C "$REPO" rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase40)" \
   = "29d1344b6b93136d1ae0273008ce34a154360e7b" \
  || { echo 'SEALED PHASE-40 RUNS TREE DIFFERS — STOPPING; report it'; exit 1; }
echo "run $N of should-quiet-1 captured and committed ($RC), codex $CODEX"
# LAST — the envelope shape. A failure here is a RESULT, not a void run: the run is committed.
python3 "$REPO/plugins/vibe-check/scripts/state_shape.py" "$RUN_DIR/state.json" \
  --schema "$SCHEMA" \
  || { echo 'ENVELOPE SHAPE VIOLATION — do NOT re-run; tell the assistant — STOPPING'; exit 1; }
echo "state_shape PASS ($SCHEMA)"
echo 'BLOCK OK'
# END: sq1-post
```

### should-quiet-1 — void an unfinished run `<n>`

Use this only when a run STOPPED before `sq1-post` committed it, or stalled between steps. It
removes the run's uncommitted folder and any state file the run wrote, and checks the clone is still
exactly base + patch.

```bash
# BLOCK: sq1-void
set -euo pipefail
N="${RUN_N:-1}"
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
PATCH=$REPO/docs/design/b3-ground-truth/diffs/should-quiet-1.patch
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
case "$N" in 1|2|3) ;; *) echo 'RUN NUMBER MUST BE 1, 2 OR 3 — STOPPING'; exit 1 ;; esac
RP=docs/design/b3-ground-truth/runs-v2.10-phase41/$ARCHIVE_BATCH/should-quiet-1/run-$N
test -z "$(git -C "$REPO" log -1 --format=%H -- "$RP/")" \
  || { echo "RUN $N IS COMMITTED — it is evidence, not voidable — STOPPING"; exit 1; }
rm -rf "${REPO:?}/$RP"
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
grep -q 'diff_id=should-quiet-1' "$STATE_DIR/.b3-inprogress" \
  || { echo 'CLONE NOT PREPARED FOR THIS DIFF — STOPPING'; exit 1; }
find "$STATE_DIR" -maxdepth 1 -name '*.json' -print -delete
test "$(git rev-parse HEAD)" = "98eb4196e2c060b38775ab40d6d23e2dc2bee024" \
  || { echo 'HEAD MOVED — run p41 sq1-revert, then p41 sq1-fresh — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" \
   = "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a" \
  || { echo 'CLONE DRIFTED — p41 sq1-revert, then p41 sq1-fresh — STOPPING'; exit 1; }
echo "run $N voided — redo it: p41 sq1-pre $N"
echo 'BLOCK OK'
# END: sq1-void
```

---

## 9. Your worklog — mechanical facts only

Tick each cell as the blocks report it (`y`/`n`, the exit code, or the printed codex value). There
is deliberately no column for how many false positives there were: that is the assistant's call
(section 2). `pass-json` re-derives every column from the committed artifacts, so this table is
your worklog, not the evidence.

Columns: `snap` = the snapshot re-verified before the run (y/n) · `shape` = the `state_shape.py`
exit code · `tree` = tree.diff sha matched (y/n) · `paths` = touched-path set matched (y/n) ·
`1 pass` = `len(passes)==1` held (y/n) · `codex` = `joined` / `skipped` / `off` as printed ·
`report` / `transcript` = captured (y/n).

| check | diff | run | snap | shape | tree | paths | 1 pass | codex | report | transcript |
|---|---|---|---|---|---|---|---|---|---|---|
| final | should-quiet-3 | 1 | | | | | | | | |
| final | should-quiet-3 | 2 | | | | | | | | |
| final | should-quiet-3 | 3 | | | | | | | | |
| final | should-quiet-1 | 1 | | | | | | | | |
| final | should-quiet-1 | 2 | | | | | | | | |
| final | should-quiet-1 | 3 | | | | | | | | |

(A `final-2` check, if D-12 calls for one, gets the same six rows.)

---

## 10. Writing `PASS.json` (once per check, after both diffs are reverted)

`p41 pass-json` writes `docs/design/b3-ground-truth/runs-v2.10-phase41/final/PASS.json` (or
`final-2/PASS.json`) from the committed run folders and commits it. It fills only the mechanical
fields plus each run's `codex_status`. Every `adjudication` field is left as the literal
`"pending-assistant"`, and `trace_validation` as `"not-applicable"`. The shape it writes:

```json
{
  "batch": "final",
  "snapshot_commit": "<batch-sha from pre-flight>",
  "verdict": "PASS",
  "recorded_by": "owner",
  "recorded_at": "<UTC time of writing>",
  "runs": [
    {
      "diff": "should-quiet-3",
      "run_index": 1,
      "state_shape": "PASS",
      "tree_diff_sha_match": true,
      "codex_status": "joined",
      "report_path": "should-quiet-3/run-1/report.md",
      "transcript_path": "should-quiet-3/run-1/transcript.jsonl",
      "trace_validation": "not-applicable",
      "adjudication": "pending-assistant"
    }
  ]
}
```

(six run objects: should-quiet-3 runs 1-3, then should-quiet-1 runs 1-3.) `verdict` here is the
MECHANICAL verdict (`FAIL` if any run recorded a shape failure or a tree.diff mismatch). The
assistant sets the final verdict after adjudicating each run (`clean` / `fp`) and applying D-11.

Hand this file to the assistant. `batchsnap.py check-pass` refuses an artifact that still says
`pending-assistant`, so a `final-2` check cannot start until `final` is adjudicated.

```bash
# BLOCK: pass-json
set -euo pipefail
REPO=~/turingmind-code-review
ENV=~/.b3/phase41-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — run p41 preflight first — STOPPING'; exit 1; }
. "$ENV"
REL=docs/design/b3-ground-truth/runs-v2.10-phase41/$ARCHIVE_BATCH
test ! -e "$REPO/$REL/PASS.json" || { echo 'PASS.json ALREADY WRITTEN — STOPPING'; exit 1; }
test ! -e ~/roonseek/.turingmind/state/.b3-inprogress \
  || { echo 'should-quiet-3 NOT REVERTED — p41 sq3-revert — STOPPING'; exit 1; }
test ! -e ~/triggarr/.turingmind/state/.b3-inprogress \
  || { echo 'should-quiet-1 NOT REVERTED — p41 sq1-revert — STOPPING'; exit 1; }
python3 - "$REPO" "$REL" "$ARCHIVE_BATCH" "$BATCH_SHA" "$SCHEMA" "$RUNS_PER_DIFF" <<'PY' \
  || { echo 'PASS.json NOT WRITTEN — STOPPING'; exit 1; }
import datetime, glob, hashlib, json, os, subprocess, sys
repo, rel, label, sha, schema, per = sys.argv[1:7]
per = int(per)
top = os.path.join(repo, rel)
shape = os.path.join(repo, "plugins/vibe-check/scripts/state_shape.py")
expect = {
    "should-quiet-3": "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69",
    "should-quiet-1": "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a",
}
runs, failed = [], False
for diff in ("should-quiet-3", "should-quiet-1"):
    found = sorted(glob.glob(os.path.join(top, diff, "run-*")))
    if len(found) != per:
        sys.exit("%s has %d run folder(s), this check needs %d" % (diff, len(found), per))
    for n in range(1, per + 1):
        sub = "%s/run-%d" % (diff, n)
        run = os.path.join(top, sub)
        log = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%H", "--",
                              os.path.join(rel, sub)], stdout=subprocess.PIPE, text=True,
                             timeout=120)
        if not log.stdout.strip():
            sys.exit("%s is not committed" % sub)
        rc = subprocess.run([sys.executable, shape, os.path.join(run, "state.json"),
                             "--schema", schema], timeout=120).returncode
        tree = open(os.path.join(run, "tree.diff.sha256")).read().strip() == expect[diff]
        tpath = os.path.join(run, "transcript.jsonl")
        if not os.path.isfile(tpath) or not os.path.isfile(os.path.join(run, "report.md")):
            sys.exit("%s is missing report.md or transcript.jsonl" % sub)
        got = hashlib.sha256(open(tpath, "rb").read()).hexdigest()
        if got != open(tpath + ".sha256").read().strip():
            sys.exit("%s/transcript.jsonl changed after capture" % sub)
        codex = json.load(open(os.path.join(run, "state.json")))["passes"][-1].get("codex")
        codex = codex.get("status", "absent") if isinstance(codex, dict) else "absent"
        failed = failed or rc != 0 or not tree
        runs.append({"diff": diff, "run_index": n,
                     "state_shape": "PASS" if rc == 0 else "FAIL",
                     "tree_diff_sha_match": tree,
                     "codex_status": codex,
                     "report_path": sub + "/report.md",
                     "transcript_path": sub + "/transcript.jsonl",
                     "trace_validation": "not-applicable",
                     "adjudication": "pending-assistant"})
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
art = {"batch": label, "snapshot_commit": sha, "verdict": "FAIL" if failed else "PASS",
       "recorded_by": "owner", "recorded_at": now, "runs": runs}
with open(os.path.join(top, "PASS.json"), "w") as fh:
    json.dump(art, fh, indent=2)
    fh.write("\n")
print("PASS.json written: %d run(s), mechanical verdict %s" % (len(runs), art["verdict"]))
PY
# the barrier must REFUSE this artifact until the assistant adjudicates it
! python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" check-pass \
  --file "$REPO/$REL/PASS.json" > ~/.b3/p41-checkpass.out \
  || { echo 'check-pass ACCEPTED AN UNADJUDICATED ARTIFACT — STOPPING'; exit 1; }
grep -q 'pending-assistant' ~/.b3/p41-checkpass.out \
  || { cat ~/.b3/p41-checkpass.out; echo 'check-pass REFUSED, OTHER REASON — STOPPING'; exit 1; }
git -C "$REPO" add "$REL/PASS.json"
git -C "$REPO" commit -q --only -m "runs(41): $ARCHIVE_BATCH PASS.json (pending assistant)" \
  -- "$REL/PASS.json"
PC=$(git -C "$REPO" log -1 --format=%H -- "$REL/PASS.json")
test "$(git -C "$REPO" show --name-only --format= "$PC")" = "$REL/PASS.json" \
  || { echo 'COMMIT SCOPE VIOLATION — STOPPING'; exit 1; }
echo "committed $REL/PASS.json ($PC) — hand it to the assistant"
echo 'BLOCK OK'
# END: pass-json
```

---

## 11. Revert once per diff (fixtures and your own state only)

Run after the diff's LAST run of the check. This restores the B3 fixture clone to the branch it was
on and puts your parked state files back. It does NOT roll back plugin commits: plugin rollback is
the revert section of `BATCH-LIFECYCLE-v2.10-phase40.md`, never this block.

**Plugin rollback (batch 4) — order and state handling:** if the Wave-1 scorer has to come out,
(1) **ORDER — code first:** follow `BATCH-LIFECYCLE-v2.10-phase40.md` §7 with
`python3 plugins/vibe-check/scripts/batchsnap.py commit-set --batch 4 --recorded docs/design/b3-ground-truth/runs-v2.10-phase41/PLAN-COMMITS.json`,
which emits newest-first 41-06 (`ccf69fc`), 41-05 (`0ee3818`), 41-04 (`c02d9b1`); revert them as
ONE revert commit, then rebuild and verify the snapshot. The 41-06 sha carries the scorer, the
`members` schema allowance (`fixtures/future-schema.json` + `test_state_shape.py`) and the
`30-collect-score.md` member HEAD-read paragraph TOGETHER, so the tree is never half-reverted.
(2) **STATE — `.turingmind/state/*.json` files need NO rewrite**, backup or downgrade procedure
(the two clones' and any of your own repos'): the pre-H-LANE scorer reads a new-version state file
without error — `05-state.md` forwards findings whole, `_shape_finding` drops the `members` key,
and the representative carries forward exactly as before — and the next pass writes old-shape
state. (3) **CAVEAT — an accepted downgrade**, measured by 41-06's `TestRollbackStateCompat`:
absorbed-member titles and the member-promotion path are LOST on rollback; a member whose
representative is later fixed vanishes as it did before Wave 1. This is disclosed, not a crash.
(4) **EVIDENCE — runs already archived under `runs-v2.10-phase41/` are never reverted**
(lifecycle §7 item 3) and are validated under the tree that produced them (the batch-4 snapshot),
never under a rolled-back tree.

```bash
# BLOCK: sq3-revert
set -euo pipefail
cd ~/roonseek
# N-04 — clear the uv.lock protection FIRST (this is also the abandon-this-diff path)
chflags nouchg ~/roonseek/uv.lock
! stat -f %Sf ~/roonseek/uv.lock | grep -q uchg \
  || { echo 'uv.lock STILL PROTECTED after the clear — STOPPING'; exit 1; }
STATE_DIR=~/roonseek/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase41
test -e "$STATE_DIR/.b3-inprogress" \
  || { echo 'NO SENTINEL — nothing to revert — STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-3' "$STATE_DIR/.b3-inprogress" \
  || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo 'A RUN IS UNFINISHED (state file present) — p41 sq3-void <n> — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd src/roonseek/transfer.py
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
echo "should-quiet-3 complete — clone back on $START_BRANCH@$START_SHA"
echo 'Close the Claude Code tab for this diff (/exit).'
echo 'BLOCK OK'
# END: sq3-revert
```

```bash
# BLOCK: sq1-revert
set -euo pipefail
cd ~/triggarr
# N-04 — clear the uv.lock protection FIRST (this is also the abandon-this-diff path)
chflags nouchg ~/triggarr/uv.lock
! stat -f %Sf ~/triggarr/uv.lock | grep -q uchg \
  || { echo 'uv.lock STILL PROTECTED after the clear — STOPPING'; exit 1; }
STATE_DIR=~/triggarr/.turingmind/state
PARK=$STATE_DIR/.b3-parked-phase41
test -e "$STATE_DIR/.b3-inprogress" \
  || { echo 'NO SENTINEL — nothing to revert — STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-1' "$STATE_DIR/.b3-inprogress" \
  || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
test -z "$(find "$STATE_DIR" -maxdepth 1 -name '*.json')" \
  || { echo 'A RUN IS UNFINISHED (state file present) — p41 sq1-void <n> — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd triggarr/web/validation.py
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
echo "should-quiet-1 complete — clone back on $START_BRANCH@$START_SHA"
echo 'Close the Claude Code tab for this diff (/exit).'
echo 'BLOCK OK'
# END: sq1-revert
```

After BOTH reverts, put your auto-memory back. Anything the check's sessions wrote to memory is
kept beside the parked copy as evidence and never merged back.

```bash
# BLOCK: restore-memory
set -euo pipefail
ENV=~/.b3/phase41-active.env
test -f "$ENV" || { echo 'NO ACTIVE CHECK — STOPPING'; exit 1; }
. "$ENV"
test ! -e ~/roonseek/.turingmind/state/.b3-inprogress \
  || { echo 'should-quiet-3 NOT REVERTED — p41 sq3-revert first — STOPPING'; exit 1; }
test ! -e ~/triggarr/.turingmind/state/.b3-inprogress \
  || { echo 'should-quiet-1 NOT REVERTED — p41 sq1-revert first — STOPPING'; exit 1; }
PARKDIR=~/.b3/automemory-parked-phase41-$ARCHIVE_BATCH
mkdir -p "$PARKDIR"
STAMP=$(date '+%Y%m%dT%H%M%S')
for C in roonseek triggarr; do
  MEM=$HOME/.claude/projects/-Users-julianamacbook-$C/memory
  if test -e "$MEM"; then
    mv "$MEM" "$PARKDIR/$C-written-during-$ARCHIVE_BATCH-$STAMP"
    echo "memory written during the check kept as evidence: $PARKDIR/$C-written-during-$ARCHIVE_BATCH-$STAMP"
  fi
  if test -e "$PARKDIR/$C"; then
    mv "$PARKDIR/$C" "$MEM"
    echo "restored ~/$C auto-memory"
  fi
done
echo 'BLOCK OK'
# END: restore-memory
```

---

## 12. The phase-exit judgment

The SCORER-05 gate is **D-11: the FP count is at or under the prediction.** Over the 6 `final`
runs, the number of runs that still fire a critical/warning must be **≤ 5**, the replay's predicted
count for this pair (section 3). Per-run band agreement with the replay is reported for information
only. The codex condition of each run is reported beside it.

The assistant adjudicates each run from its committed `state.json` and `report.md`, writes the
per-run `clean` / `fp` adjudications and the verdict into `runs-v2.10-phase41/final/PASS.json`, and
confirms the artifact with `batchsnap.py check-pass`. The owner reviews it.

**On a miss — D-12:** ONE offline re-tune (same replay guardrail, same principled-change rule —
never a per-diff patch), a rebuilt snapshot pinned in section 5 as `final-2`, then ONE more 6-run
check (max +6 owner runs) under `runs-v2.10-phase41/final-2/`. After that Phase 41 closes and Wave
2 starts either way; a remaining miss is disclosed in the phase record, not re-tried.
