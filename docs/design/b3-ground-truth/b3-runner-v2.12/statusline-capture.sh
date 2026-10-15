#!/usr/bin/env bash
# Measured-session status line: records Claude Code's own status-line payload (model id and
# context-window fields) to a local log beside this script (the runner dir), then renders the
# owner's normal status line from it. Local evidence only; never committed.
input=$(cat)
log="$(dirname "$0")/statusline-payloads.jsonl"
printf '%s' "$input" | jq -c '{ts: (now | todate), session_id, cwd, model, context_window, exceeds_200k_tokens}' >> "$log" 2>/dev/null || true
printf '%s' "$input" | bash "$HOME/.claude/statusline.sh"
