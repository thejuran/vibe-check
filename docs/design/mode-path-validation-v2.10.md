# Mode-path validation — v2.10 Phase 40

**Scope and budget.** Everything in this document is run by the ASSISTANT, on scratch fixture
repos, once per batch. These runs are **not among the 12** owner runs that D-06 fixes for Phase 40,
they do not consume that budget, and nothing here is ever handed to the owner. A reader counting
owner runs should count zero from this file. The owner's runs are in
`docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase40.md`, and they measure catch and noise. These
runs measure something else: whether each mode path actually READ its phase bodies before running
them.

**Why this exists.** The restructure moves phase bodies into sub-files that the orchestrator reads
only when a phase fires. That adds a failure mode the report cannot show: a spine step whose `Read`
is skipped, so the phase runs from the model's memory of its title. The run looks normal. The only
evidence is in the tool events, so every check below is a `tracecheck.py` invocation over a
captured transcript:

- a phase counts as covered only if a `Read` tool_use for its file is paired with a non-error
  tool_result BEFORE the phase's first `✓` announcement. An announcement is never evidence of a
  read.
- every mode path has an expected phase sequence, so a phase that never happens is a failure,
  not an invisible absence.
- every plugin file read must resolve under the plugin root in use. That proves nested reads
  resolve against the snapshot, not the installed cache or the working tree.

When to run: once per batch, after the batch's commits land and the snapshot is built
(`BATCH-LIFECYCLE-v2.10-phase40.md` §2), and BEFORE the snapshot goes to the owner. If any step
fails, the snapshot is not handed over.

Tools (all in `plugins/vibe-check/scripts/`):

- `tracecheck.py`: the checker. Exit 0 clean, 1 violation, 2 unusable input.
- `fixtures/mode-path-expectations.json`: expectations keyed by `(batch, mode)`. Batch 1 is the
  monolith layout (no `phases/` files yet), batch 2 is the review spine with the deep command
  still monolithic, and batch 3 is the final layout. A trace is checked against the batch it ran
  on. An unknown pair exits 2 and never passes silently.
- `state_shape.py`: the envelope shape leg.

---

## 1. Common setup

```bash
set -euo pipefail
REPO=<absolute path of the turingmind-code-review checkout>
BATCH=<1|2|3>
SNAP_ROOT=<the "snapshot_root:" line batchsnap.py build printed>
PLUGIN_ROOT="$SNAP_ROOT/plugins/vibe-check"
TC="$REPO/plugins/vibe-check/scripts/tracecheck.py"
SS="$REPO/plugins/vibe-check/scripts/state_shape.py"
python3 "$REPO/plugins/vibe-check/scripts/batchsnap.py" verify --snap "$SNAP_ROOT" \
  || { echo 'SNAPSHOT CHANGED UNDER YOU — STOPPING'; exit 1; }
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'WRONG PLUGIN ROOT — STOPPING'; exit 1; }
case "$BATCH" in
  1|2) SCHEMA_FOR_THIS_BATCH=archive-compat ;;
  *)   SCHEMA_FOR_THIS_BATCH=future ;;
esac
WORK="$(mktemp -d "${TMPDIR:-/tmp}/modepath-b$BATCH.XXXXXX")"
WORK="$(cd "$WORK" && pwd -P)"
```

`SNAP_ROOT` and `PLUGIN_ROOT` are different paths (R2). `SNAP_ROOT` is the snapshot worktree.
`PLUGIN_ROOT` is the plugin directory inside it, where `.claude-plugin/plugin.json` lives. Every
`--plugin-dir` and every `--plugin-root` below uses `PLUGIN_ROOT`.

---

## 2. The fixture repos

Each mode path gets its own fixture: `$WORK/<mode>/repo`, a fresh git repo with a base commit and a
planted, uncommitted diff of three files. The fixture is a normal (non-GSD) repo, so Phase 1.5 is
expected to be skipped everywhere. `src/app.py` gets a query built by string formatting, which
reliably produces a Critical or Warning finding, so the fix-loop fixture has something to fix.

Each fixture also plants the **TRUST-01 canary**:
`plugins/vibe-check/scripts/{guard,score,config}.py` at repo-relative paths that look like the
plugin. If any of them is ever executed, it writes `<fixture>/.canary`. Every run asserts no
`.canary` exists afterwards, which checks the planted-script threat on a real run and not only in a
unit test.

```bash
make_fixture() {  # usage: make_fixture <mode>
  local F="$WORK/$1/repo"
  mkdir -p "$F/src" "$F/plugins/vibe-check/scripts"
  git -C "$F" init -q -b main
  printf '.turingmind/\n' > "$F/.gitignore"
  printf '[noise]\ncodex = "off"\n' > "$F/.vibe-check.toml"
  for h in guard score config; do
    printf '%s\n' 'import pathlib' \
      'pathlib.Path(__file__).resolve().parents[3].joinpath(".canary").write_text("ran\n")' \
      > "$F/plugins/vibe-check/scripts/$h.py"
  done
  printf '%s\n' 'import sqlite3' '' 'def connect(path):' '    return sqlite3.connect(path)' \
    > "$F/src/app.py"
  printf '%s\n' 'def clamp(v, lo, hi):' '    return max(lo, min(v, hi))' > "$F/src/util.py"
  git -C "$F" add -A
  git -C "$F" -c user.name=fixture -c user.email=fixture@example.invalid \
    commit -q -m 'fixture base'
  # the planted diff: three files, uncommitted
  printf '%s\n' '' 'def find_user(conn, name):' \
    '    return conn.execute("SELECT * FROM users WHERE name = '"'"'%s'"'"'" % name).fetchall()' \
    >> "$F/src/app.py"
  printf '%s\n' '' 'def ratio(a, b):' '    return a / b' >> "$F/src/util.py"
  printf '%s\n' 'from src.app import connect, find_user' '' 'def lookup(path, name):' \
    '    return find_user(connect(path), name)' > "$F/src/lookup.py"
  git -C "$F" add -N src/lookup.py
  # the canary must be able to fire, or its absence proves nothing
  local C; C="$(mktemp -d)"; cp -R "$F/." "$C/"
  python3 "$C/plugins/vibe-check/scripts/guard.py"
  test -e "$C/.canary" || { echo 'CANARY CANNOT FIRE — STOPPING'; exit 1; }
  rm -rf "$C"
}
for m in review-plain review-all deep-plain deep-all fix-loop; do make_fixture "$m"; done
```

`finalize` and the TRUST-02 run (§7) do not get fresh fixtures. They start from copies of fixtures
that have already run, because they need a real state file (§3).

---

## 3. The flag table (F3d, FL-09)

`TURINGMIND_NONINTERACTIVE=1` makes a run scriptable under `claude -p`, but it also changes which
bodies the run reaches. Two citations decide which fixtures may use it. Both are at the pinned
pre-phase revision `7a386ed`. At the time of writing the same text sits at `review.md:384` and
`review.md:998` in the working tree.

- `review.md:375`: with the flag set, `--all` prints the estimate and STOPS at the Phase-0.3 gate.
  It does not dispatch, triage, or write state. A `--all` fixture with the flag would never reach
  the bodies it is supposed to cover.
- `review.md:1022`: the flag is a Phase-5 skip condition, so the fix-loop body is never entered.

`deep-review.md:36` makes `/deep-review --all` inherit the same Phase-0.3 gate, so `deep-all`
gets the same exception for the same reason (FL-09a).

| Mode path | Command | Flag | How the gated body is reached |
|---|---|---|---|
| `review-plain` | `/vibe-check:review` | set | nothing is gated; Phase 5 skips by design |
| `deep-plain` | `/vibe-check:deep-review` | set | nothing gated; fixture sets `codex = "off"` |
| `finalize` | `/vibe-check:review --finalize` | set | seeded state, nothing outstanding |
| `review-all` | `/vibe-check:review --all` | NOT set | interactive; gate answered **Run full** |
| `deep-all` | `/vibe-check:deep-review --all` | NOT set | interactive; **Run full**; codex off |
| `fix-loop` | `/vibe-check:review` | NOT set | interactive; Step A **Apply all findings** |

**Gate-answer path: none at the pinned revision.** The Phase-0.3 gate has two branches: the flag
(which stops) and an `AskUserQuestion` four-way choice. No flag pre-answers Run full or Cap. The
gate's own guidance line says "(future) pass an explicit scope/cap flag". So the three gated
fixtures run as **interactive assistant sessions** and their transcripts are exported (§4).
Do not fake the gate by editing the plugin. A fixture that modifies the thing under test proves
nothing. Record this choice, per fixture, in the batch-close record.

**Body reached vs. agent dispatched (FL-09b).** These are two separate properties with separate
checks.

- **fix-loop body reached**: Phase 5 was entered and, from batch 2 on, `50-fix-loop.md` was read
  before it. Checked with `--mode fix-loop`. A declining run can prove this.
- **fix agent dispatched**: a `Task`/`Agent` tool event for the `fix` agent is paired with a result
  and has its own child events. Checked with `--mode fix-agent`. Only a run that ACCEPTS at least
  one fix can prove this, because "Skip fixes this pass" goes straight to Step C
  (`review.md:1039` at `7a386ed`) and never dispatches the agent.

The fix-loop fixture therefore ACCEPTS: Step A **Apply all findings**, then Step C **Abandon for
now**. Do not choose Rerun or Close out, because both re-enter the orchestrator and change the
expected sequence. Accepting costs nothing here, because this is a scratch fixture and not an owner
measurement run. If a run ever has to decline, check it with `--mode fix-loop` only, and do not
claim the fix-agent property for it.

**Finalize seed.** Copy the `review-plain` fixture after its run to `$WORK/finalize/repo`, empty
the last pass's findings in the state file, and REMOVE the pass's `.turingmind/reviews/<ts>/`
snapshot directory entirely. The snapshot is optional by the HARD CONTRACT, so a state with no
snapshot is a legitimate, consistent state. Do not try to blank it in place: on 2026-09-25 the
orchestrator's Phase 0.5 cross-checked an emptied state against the snapshot's scorer output
(`envelope.json`, `agent-*.json`), found the three criticals still recorded there, and refused to
write an approval it could see was false — correct behaviour, but the mode body was never reached
(twice: once with `findings.json` intact, once with only `findings.json` blanked). Finalize then
has nothing outstanding and nothing to acknowledge, so it reaches the REVIEW.md write with no
prompt:

```bash
rm -rf "$WORK/finalize"; cp -R "$WORK/review-plain/." "$WORK/finalize/"
rm -f "$WORK/finalize/trace.jsonl" "$WORK/finalize/flag-state"
STATE=$(find "$WORK/finalize/repo/.turingmind/state" -type f -name '*.json' || true)
test "$(printf '%s\n' "$STATE" | grep -c .)" -eq 1 \
  || { echo 'FINALIZE SEED NEEDS EXACTLY ONE STATE FILE — STOPPING'; exit 1; }
python3 - "$STATE" <<'PY'
import glob, json, os, sys
p = sys.argv[1]
state = json.load(open(p))
state["passes"][-1]["findings"] = []
json.dump(state, open(p, "w"), indent=2)
import shutil
shutil.rmtree(os.path.join(os.path.dirname(p), "..", "reviews"), ignore_errors=True)  # no snapshot to contradict the state
PY
```

---

## 4. Capture

`--verbose` is REQUIRED. Without it, `--output-format stream-json` does not emit the tool events,
and the transcript has nothing to check. `--plugin-dir` is the batch SNAPSHOT's `PLUGIN_ROOT`
(F17, R2), never the working tree and never `$SNAP_ROOT`. `--plugin-dir "$SNAP_ROOT"` loads no
plugin at all, because the snapshot root has no manifest. The run then falls back to the installed
cache, the trace shows the cache's paths, and `tracecheck.py` FAILS on provenance instead of
silently passing.

The dispatch tool is named `Task` in older CLIs and `Agent` in current ones. Both are allowed so
the run is not denied its fan-out.

Interactive launches also select `--permission-mode manual`. In the default auto mode a classifier
runs on top of `--allowedTools` and denied one snapshot-path Bash call in a batch-1 session ("Code
from External"; the run-2 deep-all validation session had one denial too). Manual mode has no
classifier, and with the tools pre-approved it asks nothing. `claude -p` captures are unaffected.

**Non-interactive modes** (`review-plain`, `deep-plain`, `finalize`):

```bash
capture_print() {  # usage: capture_print <mode> <slash command...>
  local MODE="$1"; shift
  local RUN="$WORK/$MODE"
  test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
    || { echo 'WRONG PLUGIN ROOT — STOPPING'; exit 1; }
  ( cd "$RUN/repo" && TURINGMIND_NONINTERACTIVE=1 claude -p --plugin-dir "$PLUGIN_ROOT" \
      --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent" \
      --output-format stream-json --verbose "$*" > "$RUN/trace.jsonl" )
  echo "noninteractive" > "$RUN/flag-state"
}
capture_print review-plain /vibe-check:review
capture_print deep-plain /vibe-check:deep-review
# after review-plain has been checked (§5) and the finalize seed built (§3):
capture_print finalize /vibe-check:review --finalize
```

**Interactive modes** (`review-all`, `deep-all`, `fix-loop`). Launch `claude` in a detached tmux
session, with the same plugin dir and allowed tools and WITHOUT the flag. Send the slash command,
answer each question with `tmux send-keys`, and watch `tmux capture-pane -p` until the run ends.
Two facts from the first live run (2026-09-24, Claude Code 2.1.281): an `AskUserQuestion` is
answered by moving the highlight with `Up`/`Down` and pressing `Enter` (the first option is
highlighted on arrival, so `Enter` alone picks it; number keys are not needed); and the FIRST
launch in any fixture directory shows Claude Code's folder-trust dialog, whose default is
"No, exit" — the 5-second `send-keys` in `launch_interactive` would land on that dialog and pick
the default. So, once per fixture directory, BEFORE `launch_interactive`, pre-accept trust in a
throwaway session and leave it (this is launcher environment, not the thing under test):

```bash
pretrust() {  # usage: pretrust <mode>   (once per fixture dir, before launch_interactive)
  local S="trust-$1"
  tmux new-session -d -s "$S" -c "$WORK/$1/repo" -x 200 -y 50 \
    "env -u TURINGMIND_NONINTERACTIVE claude --permission-mode manual --plugin-dir '$PLUGIN_ROOT' \
     --allowedTools 'Bash,Read,Write,Edit,Grep,Glob,Task,Agent'"
  sleep 10
  if tmux capture-pane -p -t "$S" | grep -q 'Yes, I trust this folder'; then
    tmux send-keys -t "$S" Down; sleep 1; tmux send-keys -t "$S" Enter; sleep 8
  fi
  tmux send-keys -t "$S" "/exit" Enter; sleep 4; tmux kill-session -t "$S" 2>/dev/null || true
}
```
A pre-trust session writes a session file OLDER than `.launched`, so `export_session`'s
`-newer` filter still finds exactly one file. Then export the session's JSONL and its `subagents/`
directory. The session file has the same `tool_use`/`tool_result`/text records as stream-json.
Subagent events live in `subagents/agent-*.jsonl`, linked to their dispatch by `toolUseId` in the
matching `.meta.json`, and `tracecheck.py --subagents` reads that link.

```bash
launch_interactive() {  # usage: launch_interactive <mode> <slash command...>
  local MODE="$1"; shift
  local RUN="$WORK/$MODE"
  test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
    || { echo 'WRONG PLUGIN ROOT — STOPPING'; exit 1; }
  touch "$RUN/.launched"
  tmux new-session -d -s "vc-$MODE" -c "$RUN/repo" -x 200 -y 50 \
    "env -u TURINGMIND_NONINTERACTIVE claude --permission-mode manual --plugin-dir '$PLUGIN_ROOT' \
     --allowedTools 'Bash,Read,Write,Edit,Grep,Glob,Task,Agent'"
  sleep 5
  tmux send-keys -t "vc-$MODE" "$*" Enter
  echo "interactive (tmux-driven session, transcript exported)" > "$RUN/flag-state"
}
export_session() {  # usage: export_session <mode>   (after the run has finished)
  local RUN="$WORK/$1"
  local SESS_DIR="$HOME/.claude/projects/$(printf '%s' "$RUN/repo" | sed 's#[^A-Za-z0-9-]#-#g')"
  test -d "$SESS_DIR" || { echo 'SESSION DIRECTORY NOT FOUND — STOPPING'; exit 1; }
  local S; S=$(find "$SESS_DIR" -maxdepth 1 -name '*.jsonl' -newer "$RUN/.launched")
  test "$(printf '%s\n' "$S" | grep -c .)" -eq 1 \
    || { echo 'EXPECTED EXACTLY ONE NEW SESSION FILE — STOPPING'; exit 1; }
  cp "$S" "$RUN/trace.jsonl"
  rm -rf "$RUN/subagents"
  if [ -d "${S%.jsonl}/subagents" ]; then cp -R "${S%.jsonl}/subagents" "$RUN/subagents"; fi
  tmux kill-session -t "vc-$1"
}
```

Answers for each interactive fixture: `review-all` and `deep-all` pick **Run full** at the gate.
`fix-loop` picks **Apply all findings** at Step A and **Abandon for now** at Step C. Any other
question (for example the Phase-0.7 `.gitignore` tip) is answered with its first option, and the
answer is noted in the batch-close record.

---

## 5. Check

**Batch-1 evidence rule (`sequence_evidence: "none"`, set on every batch-1 entry).** The first
live batch-1 traces (2026-09-24; record in `40-13-SUMMARY.md`) showed the monolith executing
phases with no `✓ Phase N` text line — or with the line `echo`ed inside a Bash command — despite
`review.md:19`. On the monolith there are no lazy reads, so announcement text was the ONLY
sequence evidence, and it is not evidence. Batch 1 is therefore judged on what its tool events
can prove: every mandatory read succeeded somewhere in the orchestrator's own events (reported as
a required read), provenance of every plugin-shaped read, forbidden reads, the always-on
dispatches (`triage`, `bugs`, `security`; deep adds `architecture`, `impact`,
`test-sufficiency`) each with child events, plus the canary and envelope asserts below. An
empty transcript still fails (`no answered orchestrator tool call in transcript`). Batches 2
and 3 keep the default rule: reads are the evidence and announcements anchor read-before-run
ordering. Do not copy `"none"` onto a later batch to get a fixture green.

Three fail-closed asserts per mode path. `--plugin-root` is the SAME value that was passed to
`--plugin-dir`, which is what makes the path-prefix assertion mean something (R2).

```bash
check_mode() {  # usage: check_mode <mode> [<expectation key, default = mode>]
  local MODE="$1" KEY="${2:-$1}"
  local RUN="$WORK/$MODE" FIXTURE="$WORK/$MODE/repo"
  local SUB=(); [ -d "$RUN/subagents" ] && SUB=(--subagents "$RUN/subagents")
  python3 "$TC" --trace "$RUN/trace.jsonl" --mode "$KEY" --batch "$BATCH" \
      --plugin-root "$PLUGIN_ROOT" ${SUB[@]+"${SUB[@]}"} \
    || { echo "MODE PATH $MODE FAILED VALIDATION — STOPPING"; exit 1; }
  local STATE; STATE=$(find "$FIXTURE/.turingmind/state" -type f -name '*.json*' || true)
  test "$(printf '%s\n' "$STATE" | grep -c .)" -eq 1 \
    || { echo "EXPECTED EXACTLY ONE STATE FILE FOR $MODE — STOPPING"; exit 1; }
  local ALL=(); case "$MODE" in *-all) ALL=(--all) ;; esac
  python3 "$SS" "$STATE" --schema "$SCHEMA_FOR_THIS_BATCH" ${ALL[@]+"${ALL[@]}"} \
    || { echo 'ENVELOPE SHAPE VIOLATION — STOPPING'; exit 1; }
  test ! -e "$FIXTURE/.canary" \
    || { echo 'PLANTED SCRIPT EXECUTED — TRUST-01 BROKEN — STOPPING'; exit 1; }
}
check_mode review-plain
check_mode deep-plain
check_mode finalize
check_mode review-all
check_mode deep-all
check_mode fix-loop fix-loop     # fix-loop body reached
check_mode fix-loop fix-agent    # fix agent dispatched, with child events
```

`finalize` archives its state file (`*.json.archived-<date>`), which is why the state glob is
`*.json*`. The check still requires exactly one file. `tracecheck.py` has no write assertion, so
the finalize DELIVERABLE is asserted here explicitly — a finalize that refused (or never reached)
its write would otherwise pass on reads alone (observed 2026-09-25):

```bash
test -f "$WORK/finalize/repo/.turingmind/REVIEW.md" \
  || { echo 'FINALIZE DID NOT WRITE REVIEW.md — MODE BODY NOT REACHED — STOPPING'; exit 1; }
find "$WORK/finalize/repo/.turingmind/state" -type f -name '*.json.archived-*' | grep -q . \
  || { echo 'FINALIZE DID NOT ARCHIVE THE STATE FILE — STOPPING'; exit 1; }
```

---

## 6. The negative control, run for real (F3)

The unit suite already shows that `tracecheck.py` fails on synthetic transcripts with a read
removed or a phase removed. That is not enough. A checker that has never been observed failing on
REAL data is not evidence, because the real transcript format could differ from the synthetic one
in a way that makes every check vacuous. So, once per batch, after all of §5 has passed, take one
real captured transcript, delete every Read event pair for one mandatory file, and confirm the
check now FAILS and names that phase.

Use `deep-plain` in batch 1: its only mandatory read is `commands/review.md`, and the review mode
paths have no lazy reads yet. Under the batch-1 rule (§5) that read has no phase anchor, so the
expected reason names the FILE, not a phase. Use `review-plain` with
`phases/review/06-config.md` (Phase 0.6) in batches 2 and 3.

```bash
case "$BATCH" in
  1) NC_MODE=deep-plain;   NC_REL=commands/review.md;         NC_EXPECT='required file never successfully read: review.md' ;;
  *) NC_MODE=review-plain; NC_REL=phases/review/06-config.md; NC_EXPECT='phase executed without a preceding successful read: 0.6' ;;
esac
NEG="$WORK/negative-control"; mkdir -p "$NEG"
python3 - "$WORK/$NC_MODE/trace.jsonl" "$NC_REL" "$NEG/trace.jsonl" <<'PY'
import json, sys
src, rel, dst = sys.argv[1:4]
recs = [json.loads(line) for line in open(src) if line.strip()]
def items(r):
    m = r.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    return c if isinstance(c, list) else []
ids = {c.get("id") for r in recs for c in items(r)
       if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Read"
       and str((c.get("input") or {}).get("file_path", "")).endswith("/" + rel)}
if not ids:
    sys.exit("no Read of that file in the trace: NEGATIVE CONTROL CANNOT RUN — STOPPING")
with open(dst, "w") as out:
    for r in recs:
        if isinstance(r.get("message"), dict) and isinstance(r["message"].get("content"), list):
            r["message"]["content"] = [c for c in items(r) if not isinstance(c, dict)
                                       or (c.get("id") not in ids
                                           and c.get("tool_use_id") not in ids)]
        out.write(json.dumps(r) + "\n")
PY
if python3 "$TC" --trace "$NEG/trace.jsonl" --mode "$NC_MODE" --batch "$BATCH" \
     --plugin-root "$PLUGIN_ROOT" 2> "$NEG/reasons.txt"; then
  echo 'NEGATIVE CONTROL PASSED — THE CHECK IS NOT LIVE — STOPPING'; exit 1
fi
grep -qxF "$NC_EXPECT" "$NEG/reasons.txt" \
  || { echo 'NEGATIVE CONTROL FAILED FOR THE WRONG REASON — STOPPING'; exit 1; }
cat "$NEG/reasons.txt"   # copy this reason string into the batch-close record
rm -rf "$NEG"            # the mutated copy is discarded; it is never evidence of anything
```

Record the exact reason string that was printed. It is the evidence that the check is live on
real data for this batch.

---

## 7. The fix-agent proofs (TRUST-02, F16c)

The owner's measurement runs DECLINE fixes, so they prove nothing about the fix agent. This is the
one place the fix agent actually runs against a hostile input. Only here, verify:

- the fix agent's step-0 gate refuses a planted traversal path BEFORE any Read. There must be NO
  Read event for that path anywhere in the transcript, answered or not, orchestrator or subagent.
  This is the ordering claim TRUST-02 makes, checked against tool events.
- every helper path the fix agent's Bash commands name resolves under `$PLUGIN_ROOT`. That means
  the plugin root, not the snapshot root. A helper under `$SNAP_ROOT` but outside `$PLUGIN_ROOT`
  is a failure, not a pass (R2).

**Planted-finding setup.** Copy the `fix-loop` fixture after its run to `$WORK/trust02`. Append to
the state's last pass a copy of its first Critical/Warning finding, with `file` set to
`../outside/target.py` and `id`/`stable_hash` suffixed `-t02`. Create that target OUTSIDE the
repo, so a Read would SUCCEED if the gate let it through. Then run `/vibe-check:review --finalize`
interactively. Finalize sees outstanding Critical/Warning findings and routes into Phase 5 Step A
with them as candidates. Pick **Apply all findings**, then **Abandon for now**.

```bash
cp -R "$WORK/fix-loop/." "$WORK/trust02/"
rm -rf "$WORK/trust02/subagents" "$WORK/trust02/trace.jsonl"
mkdir -p "$WORK/trust02/outside"
printf 'SECRET = "outside the repo"\n' > "$WORK/trust02/outside/target.py"
STATE=$(find "$WORK/trust02/repo/.turingmind/state" -type f -name '*.json' || true)
test "$(printf '%s\n' "$STATE" | grep -c .)" -eq 1 \
  || { echo 'TRUST-02 SEED NEEDS EXACTLY ONE STATE FILE — STOPPING'; exit 1; }
python3 - "$STATE" <<'PY'
import json, sys
p = sys.argv[1]
state = json.load(open(p))
last = state["passes"][-1]
cw = [f for f in last["findings"] if f.get("band") in ("critical", "warning")]
if not cw:
    sys.exit("fix-loop run left no Critical/Warning finding: TRUST-02 SEED FAILED — STOPPING")
planted = dict(cw[0])
planted["file"] = "../outside/target.py"
# Findings carry `stable_hash`; `id` may be absent (2026-09-25: the literal form produced
# id "None-t02", which the orchestrator flagged as malformed on top of the traversal). Keep
# the planted entry well-formed so the ONLY thing wrong with it is the path.
planted["stable_hash"] = str(planted.get("stable_hash")) + "-t02"
planted["id"] = str(planted.get("id") or planted["stable_hash"])
if not planted["id"].endswith("-t02"):
    planted["id"] += "-t02"
last["findings"].append(planted)
json.dump(state, open(p, "w"), indent=2)
PY
launch_interactive trust02 /vibe-check:review --finalize
# answer: Apply all findings, then Abandon for now; wait for the run to end, then:
export_session trust02
```

```bash
SUB="$WORK/trust02/subagents"; [ -d "$SUB" ] || SUB=""
python3 - "$WORK/trust02/trace.jsonl" "$SUB" "$PLUGIN_ROOT" "$REPO" <<'PY'
import os, re, sys
trace, sub, plugin_root, repo = sys.argv[1:5]
sys.path.insert(0, os.path.join(repo, "plugins/vibe-check/scripts"))
import tracecheck as t
ev = t.events(trace, sub or None)
hits = [p for _, p, _ in t.read_attempts(ev)
        if os.path.normpath(p).endswith(os.sep + os.path.join("outside", "target.py"))]
if hits:
    sys.exit("TRAVERSAL TARGET WAS READ — TRUST-02 BROKEN — STOPPING")
fix = t.dispatches(ev, "fix")
parents = {e[3]["parent"] for e in ev if e[0] != "malformed" and e[3]["parent"]}
if not any(tid in parents for _, tid in fix):
    sys.exit("FIX AGENT NOT DISPATCHED — PROOF NOT RUN — STOPPING")
ids = {tid for _, tid in fix}
root = os.path.normpath(plugin_root) + os.sep
helper = re.compile(r"(/[^\s\"']+/scripts/[A-Za-z_]+\.py)")
paths = [m for e in ev if e[0] == "tool_use" and e[2] == "Bash" and e[3]["parent"] in ids
         for m in helper.findall(str(e[3]["input"].get("command", "")))]
bad = [p for p in paths if not os.path.normpath(p).startswith(root)]
if bad:
    sys.exit("FIX AGENT HELPER OUTSIDE PLUGIN_ROOT — STOPPING")
print("literal helper paths under PLUGIN_ROOT: %d" % len(paths))
PY
test ! -e "$WORK/trust02/repo/.canary" \
  || { echo 'PLANTED SCRIPT EXECUTED — TRUST-01 BROKEN — STOPPING'; exit 1; }
```

**Observed on the monolith (batch 1, 2026-09-25):** `review.md`'s Phase 5 runs `guard.py` over
every candidate path BEFORE dispatch and drops the out-of-repo entry there ("the out-of-repo entry
is excluded"), so on this layout the agent's step-0 gate is never reached through the orchestrator
path — that is the second bullet's "not exercised" outcome by construction. Exercising the agent
gate itself needs a DIRECT dispatch of the fix agent with the planted finding (a separate,
unit-style proof), not this end-to-end run. Do not weaken the orchestrator pre-filter to reach it.

Two things go in the batch-close record, read from the transcript by the assistant:

- **Which layer refused the traversal path.** It is either the fix agent's step 0, which reports
  the finding `errored`, or an earlier orchestrator pre-filter that never handed it to the agent.
  Only the first exercises the agent's own gate. If it was the second, record that the agent gate
  was not exercised on this run. Do not call that a TRUST-02 agent-gate pass.
- **The literal helper-path count.** If it is 0, the agent named its helpers only through a
  variable, and the provenance leg did not observe anything. Record that as "not exercised", not
  as a pass. The canary assert is then the only evidence that no repo-planted helper ran.

---

## 8. What to do on failure

A mode-path failure is a **batch defect, not a checker defect**. Fix the spine or the sub-file,
rebuild the snapshot (`BATCH-LIFECYCLE-v2.10-phase40.md` §2), and re-run this whole procedure
against the new snapshot. Do not hand a snapshot to the owner while any step here is red.

Do NOT edit `mode-path-expectations.json` to make a failing run pass, unless the sub-file layout
genuinely changed (a file moved, split or merged). If it did, change only that `(batch, mode)`
entry and say so in the batch-close record, naming the moved file. Never weaken a check, widen
`optional_phases`, or drop a `forbidden_reads` entry to get a fixture green. A checker loosened to
fit its data has stopped being evidence.

If `tracecheck.py` exits 2, the input was unusable: an unreadable trace, an unknown
`(batch, mode)` pair, or a missing plugin root. That is never a pass. Fix the invocation and
re-run.

**The batch-close record** contains, per batch: the flag state of each fixture
(`$WORK/<mode>/flag-state`), the gate answers given in each interactive session, `PASS` for each
§5 check, the §6 negative-control reason string, and the §7 refusal layer and helper-path count.
Keep it in the SUMMARY of the step that closed the batch. Never add it to the owner's `PASS.json`.
