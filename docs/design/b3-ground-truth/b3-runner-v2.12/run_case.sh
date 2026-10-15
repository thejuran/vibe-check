#!/usr/bin/env bash
# run_case.sh <case> <run> — one measured run with the fixed driver keystroke set:
# preflight, fresh, launch (tmux), [one-time folder-trust prompt for a disposable clone], /clear,
# pre, /vibe-check:deep-review, `Stop here…` then `Abandon` (by label), post, /exit, revert.
# preflight, launch, pre and post each run the freeze identity check (b3_identity_check) and stop
# on a mismatch; this driver adds no way around it. launch starts the tmux pane on the runbook's
# `session` block, which re-runs the check inside the pane's own process and only then execs claude,
# so the checked environment is the session's even when an older tmux server hosts the pane.
# Any other card, prompt or permission request: STOP (exit 4), the session is left alive.
#
# Environment: RUNBOOK (default docs/design/reachability-dev/RUN-PHASE54-live.md), MANIFEST
# (empty -> the active freeze manifest), RUNNER (default ~/.b3/phase54-runner).
set -uo pipefail
CASE=${1:?usage: run_case.sh <case> <run>}
RUN=${2:?usage: run_case.sh <case> <run>}
HERE=$(cd "$(dirname "$0")" && pwd)
RUNBOOK=${RUNBOOK:-docs/design/reachability-dev/RUN-PHASE54-live.md}
# shellcheck source=common.sh
source "$HERE/common.sh"
# common.sh turns on errexit for the blocks; this driver handles every failure itself
set +e
export REPO RUNNER MANIFEST
LOG=$RUNNER/logs/live-$CASE-run-$RUN.log
mkdir -p "$RUNNER/logs"
exec > >(tee -a "$LOG") 2>&1
S=p54-$CASE
pane() { tmux capture-pane -p -t "$S"; }
die() { echo "RUN_CASE: STOP — $1"; pane | grep -v '^[[:space:]]*$' | tail -40; echo "RUN_CASE_STATUS=stopped"; exit 4; }
# send the number of the card line labelled exactly <label> (by label, never by position)
pick() {
  local label=$1 p n c
  p=$(pane)
  n=$(printf '%s\n' "$p" | sed -nE "s/^[[:space:]❯]*([0-9]+)\. (.*[^[:space:]])[[:space:]]*$/\1|\2/p" \
    | awk -F'|' -v l="$label" '$2==l{print $1}')
  c=$(printf '%s\n' "$n" | grep -c .)
  test "$c" = 1 || { echo "PICK: label '$label' found $c times — nothing sent"; return 1; }
  tmux send-keys -t "$S" "$n"
  echo "PICK: sent $n for '$label'"
}
echo "RUN_CASE: live $CASE run-$RUN start $(date -u +%FT%TZ)"
b3_block "$RUNBOOK" preflight "$CASE" || die "preflight"
b3_block "$RUNBOOK" fresh "$CASE" || die "fresh"
LAUNCH_VIA_TMUX=1 b3_block "$RUNBOOK" launch "$CASE" || die "launch"
sleep 8
# startup: the folder-trust prompt appears once per new clone path
for i in $(seq 1 12); do
  P=$(pane)
  if printf '%s\n' "$P" | grep -q 'Yes, I trust this folder'; then
    case "$(tmux display -p -t "$S" '#{pane_current_path}')" in "$CLONES_ROOT"/*) ;; *) die "trust prompt for an unexpected folder" ;; esac
    echo "RUN_CASE: accepting the one-time folder-trust prompt for the disposable clone"
    tmux send-keys -t "$S" Down; sleep 1; tmux send-keys -t "$S" Enter; sleep 6; continue
  fi
  if printf '%s\n' "$P" | grep -q 'manual mode on'; then break; fi
  sleep 5
done
pane | grep -q 'manual mode on' || die "session did not reach the input prompt"
tmux send-keys -t "$S" '/clear' Enter
sleep 6
printf 'CLEARED\n' | b3_block "$RUNBOOK" pre "$CASE" "$RUN" || die "pre"
tmux send-keys -t "$S" '/vibe-check:deep-review'; sleep 1; tmux send-keys -t "$S" Enter
echo "RUN_CASE: review started $(date -u +%FT%TZ)"
# wait for the fix-loop card (or anything unexpected)
t0=$(date +%s)
while :; do
  sleep 15
  P=$(pane)
  if printf '%s\n' "$P" | grep -qE '^[[:space:]❯]*[0-9]+\. Stop here…[[:space:]]*$'; then break; fi
  if printf '%s\n' "$P" | grep -qE '✻ .+ for [0-9]+[smh].*· done'; then CLEAN=1; break; fi
  if printf '%s\n' "$P" | grep -qE 'Do you want|Yes, proceed|Yes, and don|❯ [0-9]+\.'; then
    sleep 8; P=$(pane)
    if printf '%s\n' "$P" | grep -qE '^[[:space:]❯]*[0-9]+\. Stop here…[[:space:]]*$'; then break; fi
    die "unexpected card or permission prompt"
  fi
  if test $(( $(date +%s) - t0 )) -gt 4200; then die "no fix-loop card after 70 min"; fi
  if ! printf '%s\n' "$P" | grep -qiE '…[[:space:]]*\([0-9]+[smh]|Waiting for [0-9]+ background|◯ vibe-check:|Running [0-9]+ '; then
    sleep 45
    P2=$(pane)
    if test "$P" = "$P2" && ! printf '%s\n' "$P2" | grep -qiE '…[[:space:]]*\([0-9]+[smh]|Waiting for [0-9]+ background|◯ vibe-check:|Running [0-9]+ |Stop here…'; then
      die "session idle without the fix-loop card"
    fi
  fi
done
if test "${CLEAN:-0}" = 1; then
  echo "RUN_CASE: clean review (no issues, no fix-loop card) after $(( $(date +%s) - t0 ))s"
else
  echo "RUN_CASE: fix-loop card after $(( $(date +%s) - t0 ))s"
  sleep 3
  pick 'Stop here…' || die "could not pick Stop here…"
  for i in $(seq 1 20); do
    sleep 3
    pane | grep -qE '^[[:space:]❯]*[0-9]+\. Abandon[[:space:]]*$' && break
  done
  pane | grep -qE '^[[:space:]❯]*[0-9]+\. Abandon[[:space:]]*$' || die "no stop card"
  pick 'Abandon' || die "could not pick Abandon"
  # wait for the session to finish its turn
  sleep 20
  for i in $(seq 1 120); do
    P=$(pane)
    if printf '%s\n' "$P" | grep -qE 'Do you want|Yes, proceed|❯ [0-9]+\.'; then die "unexpected prompt after Abandon"; fi
    if printf '%s\n' "$P" | grep -qE '✻ .+ for [0-9]+[smh].*· done'; then break; fi
    sleep 10
  done
fi
echo "RUN_CASE: review finished $(date -u +%FT%TZ) — $(pane | grep -oE '✻ .+ for [0-9hms ]+' | tail -1)"
b3_block "$RUNBOOK" post "$CASE" "$RUN" || die "post refused"
NVW=$(grep -oE '[0-9]+ weak co-located note' "$REPO/$RD/runs-phase54-live/$CASE/run-$RUN/transcript.jsonl" 2> /dev/null | tail -1 | awk '{print $1}')
echo "RUN_CASE_NVW=${NVW:-0}"
tmux send-keys -t "$S" C-u; tmux send-keys -t "$S" '/exit' Enter; sleep 5; tmux kill-session -t "$S" 2> /dev/null || true
b3_block "$RUNBOOK" revert "$CASE" || die "revert"
# another enabled plugin (bm) writes .planning/HANDOFF.json on tool use; the clone's local exclude
# ignores it; remove the copy this session wrote when the clone does not track it
CP=$(sed -n 's/^source_repo: ~\///p' "$REPO/docs/design/"*/{diffs,cases}/"$CASE.provenance" 2> /dev/null | head -1)
H="$CLONES_ROOT/$CP"
if test -n "$CP" && test -f "$H/.planning/HANDOFF.json" && ! git -C "$H" ls-files --error-unmatch .planning/HANDOFF.json > /dev/null 2>&1; then
  rm "$H/.planning/HANDOFF.json"; echo "RUN_CASE: removed the untracked .planning/HANDOFF.json another plugin wrote"
fi
# N-02: a memory dir the measured session created for the clone path is moved aside as evidence
M="$(proj_dir "$CLONES_ROOT/$CP")/memory"
if test -n "$CP" && test -e "$M"; then
  PD=$(sed -n 's/^PARKDIR=//p' "$HOME/.b3/phase54-live-memory-park.env")
  echo "RUN_CASE: clone auto-memory dir created by the session ($(find "$M" -type f | wc -l | tr -d ' ') files) moved to evidence"
  mv "$M" "$PD/$CP-written-during-live-$CASE-run-$RUN-$(date +%s)"
fi
echo "RUN_CASE_STATUS=done $(date -u +%FT%TZ)"
