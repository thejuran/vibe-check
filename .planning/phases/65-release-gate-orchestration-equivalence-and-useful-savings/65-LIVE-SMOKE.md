# Phase 65 live smoke — vibe-check 2.15.0 candidate

Status: IN PROGRESS

Approval: `65-LIVE-SMOKE-PROPOSAL.md` read before any spend: `Status: APPROVED (owner, 2026-11-16)`; Owner ruling `Conditions: none beyond the proposal as written.` Scope: default route + `--finalize`, 3 sessions (s65-1..s65-3), one retry only for an invalid run. Gate precondition: `65-RELEASE-RECORD.md` is tracked, has no `## Gate failures` section, and rows G1a–G11 all read PASS (G12 is the CI close, pending by design).

## Setup

C: b073e31fb77f3f5ca32747f8c549ec552687b1be
- Equals `candidate:` in 65-CANDIDATE.md (asserted 40-hex). Tree identity in the main checkout: `git diff --quiet "$C" HEAD -- . ':(exclude).planning'` exit 0. The main checkout stays on `feat/v2.15-phase-65`; only the snapshot sits at C.

SNAP: /Users/julianamacbook/.vibe-check-snapshots/rel65-b073e31
- Built with `git -C <repo> worktree add --detach <SNAP> <C>`, then `chmod -R a-w <SNAP>`. `git -C <SNAP> rev-parse HEAD` = C (asserted).
- PLUGIN_ROOT: `<SNAP>/plugins/vibe-check`; `.claude-plugin/plugin.json` reads `"version": "2.15.0"` (asserted).

CACHE: /Users/julianamacbook/.claude/plugins/cache/thejuran/vibe-check/2.14.1 (installed_plugins.json: version 2.14.1, gitCommitSha eb790e4b4a7a23ef3123273314e4633d6e1f6720)
CACHE_BAK: /Users/julianamacbook/.b3/vibe-check-2.14.1.bak-pre-phase65-run1
- Backup: `cp -Rp CACHE CACHE_BAK`; `diff -rq -x .in_use CACHE CACHE_BAK` -> empty.
- Resync: `rsync -a --delete --exclude .in_use --exclude __pycache__ --exclude '*.pyc' --exclude .pytest_cache PLUGIN_ROOT/ CACHE/`; `chmod -R u+w CACHE`.
- Parity: `diff -rq -x .in_use -x __pycache__ -x '*.pyc' -x .pytest_cache` PLUGIN_ROOT→CACHE and CACHE→PLUGIN_ROOT -> both empty. Cache plugin.json now reads `"version": "2.15.0"`.

SMOKE: /Users/julianamacbook/.b3/smoke65-1794810319
- `git init -q -b main`; local user `smoke65 <smoke65@example.invalid>`; `.turingmind/` in `.git/info/exclude`.
- Base commit `store: base`: `app/store.py` (26 lines; sqlite store with `connect`, `add_user`, parameterized `get_user(conn, user_id)`).
- Uncommitted: 19 added lines, function `find_users_by_name(conn, name, limit=50)`; file sha256 `fbf8baf997050c7e9eaa1036974d31b8e357ad7fbf55ee41470b64b7105946b1`.
- Planted defect 1 (S1): `app/store.py:38` — `query = f"SELECT id, name, email FROM users WHERE name LIKE '%{cleaned}%' {order} LIMIT {max_rows}"`, executed on line 39 (SQL built from caller input). At least 4 untouched lines on each side.
- Planted defect 2 (prepared, applied only in S3): new untracked file `app/export.py` (21 lines), `read_export(report_name)` builds `os.path.join(EXPORT_ROOT, label + ".txt")` from caller input at line 15 and passes it to `open` on line 16 (path traversal). Prepared copy sha256 `64758bb38b05ef6f9d44737d91b991c8c88a6a20b39d5900f893663ae354fc18`, kept in the executor scratchpad until S3.

Auto-memory: slug `-Users-julianamacbook--b3-smoke65-1794810319`; `~/.claude/projects/-Users-julianamacbook--b3-smoke65-1794810319/memory` asserted absent before S1 (the whole project dir is absent).

Launch line (each session a fresh process in tmux; no `--model`; never bypass):
`cd /Users/julianamacbook/.b3/smoke65-1794810319 && claude --permission-mode manual --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent" --plugin-dir "/Users/julianamacbook/.vibe-check-snapshots/rel65-b073e31/plugins/vibe-check"`
