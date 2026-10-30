# Phase 61 live smoke — vibe-check 2.14.0 candidate

Status: DONE

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

## Sessions

Run 2026-10-30, 17:59–18:17 local, machine awake throughout (`pmset` showed sleep prevented by caffeinate). Each session was a fresh `claude` process (Claude Code v2.1.314, owner default model Opus 5.5, manual mode) in its own tmux session. The workspace-trust prompt was accepted once in S1. No permission prompt touched a path outside the throwaway repo, `$TMPDIR`, the snapshot or the cache. Transcript hashes cover the main transcript plus every subagent transcript the session wrote.

### S1 — `/vibe-check:review` (tmux `s61-1`, session 5caa5cec)

- Pass 1: 3 reviewers ran (bugs, security, language-python). The card showed one row: `#1 app/store.py:42 — SQL built via f-string interpolation of user-supplied search text (warning)`.
- Answer typed via Other: `defer 1 -- tracked for a follow-up change`. The decision was recorded (`defer`, `at_pass` 1). Per `50-fix-loop.md`, a typed answer with no fix target goes to the Rerun, so pass 2 ran in the same session.
- Pass 2 ran on a byte-identical working tree. `app/store.py` mtime was 17:58:36, before the session started; `git diff --stat` still showed 20 insertions; sha256 after S1 was `29f9f08829641b1fe452fb06f2634fae210b68942c2d6a443f2b526f2e5da6aa`. Pass 2 still re-asked the row (card line under Evidence, E1), and its band rose to critical. See Carried C1 and C2.
- On the pass-2 card I chose Stop here… → Abandon, which keeps the state. Then `/exit`.
- Transcript sha256 (path relative to `~/.claude/projects/-Users-julianamacbook--b3-smoke61-1793397516/`):
  - `0e15b62b36cba89fd9449cee7d2206f27a836b6dfab1c952da5af223df15ac0d  5caa5cec-cf6b-48a0-9414-e47841cf6b6d.jsonl`
  - `408bd836a32cb11934813a96a534027d6e9a0df969d440fb83c1e3b32139d13e  5caa5cec-…/subagents/agent-a0632f626a4a54273.jsonl`
  - `7996f7df41b0721ba4449b8848e8a4bfb4993d09aeb5f7331f0f4fdb0a2b7a0c  5caa5cec-…/subagents/agent-a2eff176f3dd42c8c.jsonl`
  - `b89f324ecae8494e85c661ad96c1769a39da1196bbd9f78398b437fe87e19101  5caa5cec-…/subagents/agent-a59dcacbd8f57168a.jsonl`
  - `9aac14e56c78fa46a48112bde47656dff0c168101cca6a138e066f11fdc00f7a  5caa5cec-…/subagents/agent-aa015bd1a8908b800.jsonl`
  - `31ba8ecc11c706accf78097e87cb90617eed0b9eb1fd25d95f2e4a327d0aa6cc  5caa5cec-…/subagents/agent-aa8f085479ff6a34a.jsonl`
  - `b7819aa13fc1e337779dec4d757c8c803803fcbb7e9fe0c6f08de353197ad03d  5caa5cec-…/subagents/agent-ab10e4ff70b7d17d3.jsonl`
  - `1f7d0b6bb999317e82623d5027756d16007b6497bb6dd49db47aa1cddd03fd11  5caa5cec-…/subagents/agent-ae0b0f35a02b0ec06.jsonl`
  - `7de29cfdd2a9f0c22f2d25121d0ebc5415762f95906e59759fa46c4fc362ab34  5caa5cec-…/subagents/agent-aeff7e12b138cfbec.jsonl`

### Between S1 and S2 (no model)

- Auto-memory dir (it existed, empty) moved to `~/.b3/automemory-parked-phase61-1793397516-s1`; original path asserted absent.
- Nearby edit: `app/store.py` line 39 `    max_rows = int(limit)` → `    max_rows = min(int(limit), 200)`. That is 3 lines above the flagged line 42, which was not touched. Line numbers did not shift (before = after = 39; flagged line before = after = 42). Left uncommitted.

### S2 — `/vibe-check:review` (tmux `s61-2`, session 15a3be6d)

- Pass 3 card: both rows were re-asked with the nearby reopen reason (E2). The lead finding had split into two rows: the wildcard concern now leads, and the SQL-injection row is shown as an absorbed member "decided on its own" (C3).
- Answer typed via Other: `defer 1,2 -- tracked for a follow-up change`. Both decisions were recorded (`defer`, `at_pass` 3, evidence `nearby_at` 3, band critical).
- The protocol's next step was the Rerun. The model did not run it: it stopped, saying "I'm uncertain about Phase 0.5 / the Rerun", and listed choices (C4). `/exit`.
- Transcript sha256:
  - `0c749d41b1254b73bba6ec71fdc4070c7d6cdbe9f125ae114237acfdf7abab72  15a3be6d-6b1d-4254-b300-49c072864fe0.jsonl`
  - `98c3d91dfdf92d4dd91ac5ed1865830228319477bd5b2ebd493dce0bc7431664  15a3be6d-…/subagents/agent-a024c7ce76eaf0014.jsonl`
  - `04d26fbaf1084e0760467fb55caff613a08fe35547b9acefaaa9a5fb6dac2ca8  15a3be6d-…/subagents/agent-a52def55e7296b95e.jsonl`
  - `1e7f3078aa7533e537e5e0fad8da6071e687d9dbd079429091487e87e522b45c  15a3be6d-…/subagents/agent-a84a8f7f5e1a96718.jsonl`
  - `3a266aaf7d82d46b4d7a11db5af4648e94bd0ed9705c0d121005b2d641830eaa  15a3be6d-…/subagents/agent-ae61ae61738e6da6b.jsonl`
- S1 transcript hashes were re-checked after S2 and were unchanged.

### S3 — `/vibe-check:review --finalize` (tmux `s61-3`, session b1bb3036)

- The gate flags file held `outstanding_cw 0, unacknowledged_medium 0, undecided_nv 0`, and the gate returned write. No decision card was needed: the pass-3 decisions matched the pass-3 rows.
- REVIEW.md was written at `<SMOKE>/.turingmind/REVIEW.md`, 43 lines, `Final verdict: ✅ APPROVED`, `Passes: 3`. `## Findings deferred` lists both pass-3 rows (`app/store.py:42`, critical, deferred) and the superseded pass-1 deferral.
- State was archived to `.turingmind/state/format-53/smoke61-1793397516-main.json.archived-2026-10-30`; no live state file remains.
- The no-write stop sentence was never printed. It appears only inside the session's Read of `<SNAP>/plugins/vibe-check/phases/shared/90-finalize.md`, in no helper output and in no assistant text. No automatic rebuild ran: one BLOBFILE=/GATEFILE= pair.
- The printed paths were carried forward: later Write, Read and Bash tool inputs use exactly `vc.hoWcgh` (BLOBFILE) and `vc.Dh1knG` (GATEFILE).
- Transcript sha256 (S3 dispatched no subagents):
  - `f738368f39faf3590361a8ba065ec093c6d0ae9a243e6b4fe7d71552a1b648e5  b1bb3036-026b-4ad4-9857-5d8c05e716b8.jsonl`
- S1 and S2 transcript hashes were re-checked after S3 and were unchanged. Memory was parked to `…-s3`.

## Evidence

E1 — S1 pass-2 card line (no code change since the decision):
`#1 app/store.py:42 — SQL built via f-string interpolation of user-supplied search text (critical) — code next to it changed since your decision on pass 1 (was: deferred — tracked for a follow-up change)`

E2 — S2 card lines (after the nearby edit at line 39):
`#1 app/store.py:42 — LIKE wildcard metacharacters in search text are not escaped (critical) — code next to it changed since your decision on pass 1 (was: deferred — tracked for a follow-up change)`
`#2 app/store.py:42 — SQL built via f-string interpolation of user-supplied search text (critical) (absorbed into "LIKE wildcard metacharacters in search text are not escaped" — decided on its own) — code next to it changed since your decision on pass 1 (was: deferred — tracked for a follow-up change)`

E3 — S3 printed-path lines (from helper tool results; paths only):
`BLOBFILE=/var/folders/xq/3_d4916j6jl_5n6173p02lxw0000gn/T//vc.hoWcgh`
`GATEFILE=/var/folders/xq/3_d4916j6jl_5n6173p02lxw0000gn/T//vc.Dh1knG`

E4 — REVIEW.md: `41e50e41038cf19d99aac125ef1a6224f09bd08516dbc0c637482b58c11fc317  /Users/julianamacbook/.b3/smoke61-1793397516/.turingmind/REVIEW.md`

E5 — Provenance. In every session's transcripts (main + subagents), every `plugins/vibe-check/` path is under `/Users/julianamacbook/.vibe-check-snapshots/rel61-0d2be77/plugins/vibe-check/`: S1 106 references, S2 82, S3 40. There are 0 references to `/Users/julianamacbook/turingmind-code-review/plugins`. The installed cache was at content parity throughout. All three sessions are VALID.

E6 — Memory parks: `~/.b3/automemory-parked-phase61-1793397516-s1`, `…-s2`, `…-s3`. The memory dir was asserted absent before each launch.

## Carried (D-07)

Each item below was classified against the four qualifying classes: a mandatory gate failing, data loss, silent loss of a qualifying finding, or a broken required workflow. None qualifies. Each fails toward asking or toward stopping, and nothing was lost.

- **C1 — A decision on uncommitted code is re-asked on every pass, even with no change (default route).** Reproduced in S1: a deferral at pass 1 was re-asked at pass 2 on a byte-identical working tree. The card said "code next to it changed since your decision", which was not true.
  - Mechanism (read, not changed): on the default route, pass ≥ 2 builds its ranges from `git diff <last-reviewed-sha>` (`30-collect-score.md` L72). Before any commit, that SHA is still HEAD, so every pass sees the whole uncommitted block as changed again. `score.py` `_snapshot_for` then re-stamps `nearby_at` on every carried row inside it.
  - User impact: on the default route, a dismiss or defer of a finding in not-yet-committed code holds only until the next pass. In the fix loop, a typed defer is followed by a Rerun that asks again, so decisions stick only at Close out. Close out still completes (S3).
  - It also means S2's re-ask does not isolate the nearby edit. S2 would have re-asked without it.
  - It fails toward asking and loses nothing, so it is carried as a known limit. The owner should see it at 61-05 sign-off, because it touches the headline 2.14 promise ("asked again when the code next to it changes").
- **C2 — The band rose from warning to critical between pass 1 and pass 2 with no code change.** The S1 session's own summary put it down to the finding carrying over and being re-confirmed by both reviewers. A severity rise re-asks; it never hides a finding.
- **C3 — The row was regrouped between passes.** In S2 (pass 3), the lead changed from the SQL-injection title to the wildcard title, under a new stable hash, and the SQL-injection concern became an absorbed member decided on its own. Both rows carried the deferral context and were re-asked; REVIEW.md lists both, plus the superseded pass-1 entry.
- **C4 — In S2 the model did not take the protocol's Rerun after the typed defer.** It stopped and said it was uncertain how to proceed. This is a model deviation from `50-fix-loop.md` that fails toward stopping: no spend, no loss, and the decisions were already saved.
- **C5 — Harmless harness retries.** In S1 and S3, the first Write to a fresh `mktemp` file failed ("Error writing file") and succeeded after a Read. This is Claude Code's read-before-write rule on an existing empty file. The printed paths were still carried correctly.

## Verdict

PASS

S2 re-asked the deferred finding with the reopen reason `code next to it changed since your decision on pass 1`. S3's `--finalize` carried the printed BLOBFILE=/GATEFILE= paths across steps and wrote REVIEW.md listing the deferred findings, without the "Finalize stopped" sentence. All three sessions provably ran the candidate snapshot.

User impact: Close out now completes in a real session, and a decided finding is asked again when nearby code changes. However, on the default route a decision on uncommitted code is also asked again on every pass when nothing changed (C1). That is extra questions, not lost findings.

## Cache restored

`rsync -a --delete --exclude .in_use CACHE_BAK/ CACHE/`, then `diff -rq -x .in_use /Users/julianamacbook/.b3/vibe-check-2.13.0.bak-pre-phase61 /Users/julianamacbook/.claude/plugins/cache/thejuran/vibe-check/2.13.0` → empty. The cache plugin.json reads `"version": "2.13.0"` again.
- tmux sessions `s61-1`, `s61-2` and `s61-3` were killed.
- Snapshot removed with `chmod -R u+w` + `git worktree remove --force` + `git worktree prune`; `git worktree list` no longer shows `rel61-0d2be77`.
- `CACHE_BAK` is kept at `~/.b3/vibe-check-2.13.0.bak-pre-phase61`. `$SMOKE` and the three memory parks are kept on disk as local evidence and are not committed.

## Carry-over to candidate C2 (47978aa)

The sessions above ran on 0d2be77. After the owner switched Decision 1 to B (2026-10-30, "Switch to B (Recommended)"), the release candidate became C2 = 47978aad41eccc13c594820a8ab8386904439f31, which changes only `README.md`. The sessions loaded the plugin from `<SNAP>/plugins/vibe-check`, and that tree is byte-identical in C2:

```
$ git diff --quiet 0d2be77 47978aa -- plugins/ ; echo $?
0
$ git diff --stat 0d2be77 47978aa -- plugins/
(empty)
$ git rev-parse 0d2be77:plugins 47978aa:plugins
9387dcd3858160c44c0970fcb6a4621e223b7d4e
9387dcd3858160c44c0970fcb6a4621e223b7d4e
$ git diff --name-only 0d2be77 47978aa -- . ':(exclude).planning'
README.md
```

The repo-root README sits outside the plugin directory the sessions loaded (`--plugin-dir <SNAP>/plugins/vibe-check`), and nothing under `plugins/vibe-check` reads it at review time (its `README` mentions are about the reviewed repo's files), so the verdict above (PASS, with C1-C5 carried) applies to C2 unchanged. No session was re-run and nothing was spent.
