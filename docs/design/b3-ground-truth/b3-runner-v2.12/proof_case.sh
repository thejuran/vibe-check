#!/usr/bin/env bash
# proof_case.sh — the synthetic containment proof for the B3 measured session (owner condition,
# run before the sweep). It drives the runbook's proof blocks through b3_block: proof-prepare (a
# throwaway fixture repo with one synthetic defect, plus a planted fake credential canary),
# proof-launch (tmux pane running proof-session: the same identity check, env allowlist and claude
# launch line as `session`), the probe prompt, /vibe-check:deep-review, `Stop here…` then `Abandon`,
# /exit, and proof-verify (containment_proof.py verify). No holdout or B3 case is involved.
# Any failure: STOP (exit 4) with the pane tail; a failed verify prints PROOF FAIL lines.
#
# Environment: RUNBOOK (default docs/design/reachability-dev/RUN-PHASE54-live.md), MANIFEST
# (empty -> the active freeze manifest), RUNNER (default ~/.b3/phase54-runner).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
RUNBOOK=${RUNBOOK:-docs/design/reachability-dev/RUN-PHASE54-live.md}
# shellcheck source=common.sh
source "$HERE/common.sh"
# common.sh turns on errexit for the blocks; this driver handles every failure itself
set +e
export REPO RUNNER MANIFEST
LOG=$RUNNER/logs/proof-$(date +%s).log
mkdir -p "$RUNNER/logs"
exec > >(tee -a "$LOG") 2>&1
S=p54-proof
DONE_RE='✻ .+ for [0-9]+[smh].*· done'
pane() { tmux capture-pane -p -t "$S"; }
die() { echo "PROOF_CASE: STOP — $1"; pane 2> /dev/null | grep -v '^[[:space:]]*$' | tail -40; echo "PROOF_CASE_STATUS=stopped"; exit 4; }
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
# the last "done" line on screen (a finished turn leaves one; the next turn must show a new one)
last_done() { pane | grep -E "$DONE_RE" | tail -1; }
# wait until a NEW turn is done (or a card shows); stop on a permission prompt or a timeout
wait_turn() {
  local limit=$1 before=$2 t0 P
  t0=$(date +%s)
  while :; do
    sleep 10
    P=$(pane)
    if printf '%s\n' "$P" | grep -qE '^[[:space:]❯]*[0-9]+\. Stop here…[[:space:]]*$'; then return 0; fi
    if test -n "$(last_done)" && test "$(last_done)" != "$before"; then return 0; fi
    if printf '%s\n' "$P" | grep -qE 'Do you want|Yes, proceed|Yes, and don'; then die "permission prompt (a permission failure is never a pass)"; fi
    if test $(( $(date +%s) - t0 )) -gt "$limit"; then die "turn did not finish within ${limit}s"; fi
  done
}
echo "PROOF_CASE: start $(date -u +%FT%TZ)"
b3_block "$RUNBOOK" proof-prepare || die "proof-prepare"
LAUNCH_VIA_TMUX=1 b3_block "$RUNBOOK" proof-launch || die "proof-launch"
sleep 8
for i in $(seq 1 12); do
  P=$(pane)
  if printf '%s\n' "$P" | grep -q 'Yes, I trust this folder'; then
    case "$(tmux display -p -t "$S" '#{pane_current_path}')" in "$HOME/.b3/containment-proof/"*) ;; *) die "trust prompt for an unexpected folder" ;; esac
    tmux send-keys -t "$S" Down; sleep 1; tmux send-keys -t "$S" Enter; sleep 6; continue
  fi
  if printf '%s\n' "$P" | grep -q 'manual mode on'; then break; fi
  sleep 5
done
pane | grep -q 'manual mode on' || die "session did not reach the input prompt"
PROMPT=$(python3 "$FREEZE_TOOLS/containment_proof.py" prompt) || die "no probe prompt"
B=$(last_done)
tmux send-keys -t "$S" -l "$PROMPT"; sleep 1; tmux send-keys -t "$S" Enter
wait_turn 900 "$B"
B=$(last_done)
tmux send-keys -t "$S" '/vibe-check:deep-review'; sleep 1; tmux send-keys -t "$S" Enter
wait_turn 4200 "$B"
if pane | grep -qE '^[[:space:]❯]*[0-9]+\. Stop here…[[:space:]]*$'; then
  sleep 3
  pick 'Stop here…' || die "could not pick Stop here…"
  for i in $(seq 1 20); do
    sleep 3
    pane | grep -qE '^[[:space:]❯]*[0-9]+\. Abandon[[:space:]]*$' && break
  done
  B=$(last_done)
  pick 'Abandon' || die "could not pick Abandon"
  wait_turn 1200 "$B"
fi
tmux send-keys -t "$S" C-u; tmux send-keys -t "$S" '/exit' Enter; sleep 5; tmux kill-session -t "$S" 2> /dev/null || true
b3_block "$RUNBOOK" proof-verify || die "CONTAINMENT PROOF FAILED (see PROOF FAIL lines above)"
echo "PROOF_CASE_STATUS=ok $(date -u +%FT%TZ)"
