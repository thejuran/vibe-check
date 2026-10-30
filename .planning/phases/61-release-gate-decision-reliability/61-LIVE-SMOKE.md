# Phase 61 live smoke — vibe-check 2.14.0 candidate

Status: IN PROGRESS

Approval: `61-LIVE-SMOKE-PROPOSAL.md` read before any spend: `Status: APPROVED (owner, 2026-10-30)`; Owner ruling lists no additional conditions. Scope: default route + `--finalize`, 3 sessions, one retry only for an invalid run.

## Setup

C: 0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d (equals `candidate:` in 61-CANDIDATE.md)
SNAP: /Users/julianamacbook/.vibe-check-snapshots/rel61-0d2be77
- Built with `git -C <repo> worktree add --detach <SNAP> <C>`, then `chmod -R a-w <SNAP>`. `git -C <SNAP> rev-parse HEAD` = C (asserted).
- PLUGIN_ROOT: `<SNAP>/plugins/vibe-check`; `.claude-plugin/plugin.json` reads `"version": "2.14.0"` (asserted).

CACHE: /Users/julianamacbook/.claude/plugins/cache/thejuran/vibe-check/2.13.0 (installed_plugins.json: version 2.13.0, gitCommitSha f2b6a3674d0d0dc62ab6dca3a00816c070943884)
CACHE_BAK: /Users/julianamacbook/.b3/vibe-check-2.13.0.bak-pre-phase61
- Backup: `cp -Rp CACHE CACHE_BAK`; `diff -rq -x .in_use CACHE CACHE_BAK` -> empty.
- Resync: `rsync -a --delete --exclude .in_use --exclude __pycache__ --exclude '*.pyc' --exclude .pytest_cache PLUGIN_ROOT/ CACHE/`; `chmod -R u+w CACHE`.
- Parity: `diff -rq -x .in_use -x __pycache__ -x '*.pyc' -x .pytest_cache PLUGIN_ROOT CACHE` -> empty (two-direction: `diff -rq` reports files only on either side). Cache plugin.json now reads 2.14.0.

SMOKE: /Users/julianamacbook/.b3/smoke61-1793397516
- `git init -b main`; local user `smoke61 <smoke61@example.invalid>`; `.turingmind/` in `.git/info/exclude`.
- Base commit `store: base`: `app/store.py` (26 lines; sqlite store with parameterized `get_user(conn, user_id)`, `connect`, `add_user`).
- Uncommitted: 20 added lines, function `find_users_by_name(conn, name, limit=50)`.
- Planted defect: `app/store.py:42` — `query = f"SELECT id, name, email FROM users WHERE name LIKE '%{cleaned}%' {order} LIMIT {max_rows}"`, executed on line 43 (SQL built from caller input). Line 15 of the added block; at least 4 untouched lines on each side.

Auto-memory: slug `-Users-julianamacbook--b3-smoke61-1793397516`; `~/.claude/projects/-Users-julianamacbook--b3-smoke61-1793397516/memory` asserted absent before S1 (the whole project dir is absent).

Launch line (each session a fresh process in tmux; no `--model`; never bypass):
`cd /Users/julianamacbook/.b3/smoke61-1793397516 && claude --permission-mode manual --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent" --plugin-dir "/Users/julianamacbook/.vibe-check-snapshots/rel61-0d2be77/plugins/vibe-check"`
