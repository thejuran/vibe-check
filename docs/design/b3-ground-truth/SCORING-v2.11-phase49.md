# B3 v2.11 Phase-49 scoring worksheet — first pass (36 runs), release candidate

This is the scoring record for the v2.11 **release-candidate** measurement. It covers 12 sealed
diffs × 3 runs on the release candidate, which is frozen in the batch-7 snapshot
S = `e6eafbd3b8c4242064997f82fad5edd058d65a1c` (committer time 2026-10-06T20:41:53-04:00; S is
the `batch-sha:` of every fingerprint block in the committed notes blob). All runs used one pinned
harness. Every aggregate below can be re-derived from three inputs:

- the committed `runs-v2.11-phase49/first/<id>/run-<n>/state.json`;
- the two committed answer-key BLOBs;
- the hand AXIS map `first/CATCH-VERDICTS.json`.

**Scored:** 2026-10-07.

**Scoring input:** `state.passes[-1].findings[]`, never a transcript. Findings are scored against the
committed answer-key BLOBs. Carried rows score against the **v2.9 blob**
`ef0ab67cb45957167c99eff468077348432e1474`. New rows score against the **v2.10 blob**
`5f687d95f9be4fef2c0fcd78491c308d4c3861e8`. Bands are read from state with no recomputation.
The SEAL2 denominators 15/21 are read from blob `633f1dd`.

**Mechanical tool:** `plugins/vibe-check/scripts/score43.py`. It was last changed by 49-04, which
added the `phase49` profile, in commit `b8b3852187c20f441186313ec668b099cbfcd885`
(`git log -1 --format=%h -- plugins/vibe-check/scripts/score43.py` → `b8b3852`;
`git merge-base --is-ancestor b8b3852 e6eafbd` → exit 0), and it is unchanged since S (gate 7(ii)).
It produces the `ledger`, `fp`, `catch-candidates`, `codex-status`, `aggregate` and `failed-diffs`
outputs. The AXIS calls are hand judgements recorded in §3. The tool never computes them.

**Verdict rule (REL-01, `RESULTS-v2.11.md` §"Phase-49 pre-registration" 1–2):** the verdict is
decided on the CORRECTED cohort. should-quiet-7 is excluded per `SUPERSESSIONS-v2.10.md` #001,
which leaves 18 quiet runs with a bar of **≤ 3**, AND the catch bar is **15 of 15**. The two arms
combine as a single AND. This bar is the Phase-43 combined result (3/18, 15/15), carried as
REL-01's "unchanged / no worse". The sealed-literal x/21 against the pre-registered ≤ 6/21 is
printed beside the verdict and never decides it.

**HEAD at scoring time:** `e0c350c1da2708e8a091cb4227356a0642439547`.

---

## 1. Integrity gate ladder (all hard gates PASS)

Every proof below is derived from git history and committed blobs, never trusted from a live
working file. The checks were run at scoring time with HEAD = `e0c350c1da2708e8a091cb4227356a0642439547`
by one scratch script (`gates.py`, scratchpad only). It exited 0 with `FAILS: []`. Each Result
cell is its literal output line.

### (1) Seal verifier — ledger-004 hardened form + manifest derivation + sealed fields

Gate (1) executes the CURRENT verifier pin `de8633cb3e1a295208d89f5be7472e665aec7822`
(`SUPERSESSIONS-v2.10.md` entry 004). The superseded Phase-38 pin `a407539` appears below only as
the first of the two commits that ever touched the verifier path. It is never the blob executed.

| Check | Command | Result |
|---|---|---|
| (i) live verifier sha256 == pin | `shasum -a 256 docs/design/b3-ground-truth/verify-seal2-append.py` | `605e61a3deee6894ef4d30a1869d944d3685645749c601dacbefb81573d081a3` == pin — PASS |
| (ii) verifier-path commits (full-history, all refs) | `git log --format=%H --full-history --simplify-merges --topo-order --reverse --branches --tags --remotes -- docs/design/b3-ground-truth/verify-seal2-append.py` | exactly 2: `a407539115872137dc55d99aef439a9c5a4f16d9`, `de8633cb3e1a295208d89f5be7472e665aec7822`; the SECOND == pinned verifier commit — PASS |
| (iii) manifest derivation (same full-history all-ref form) | `git log --format=%H --full-history --simplify-merges --topo-order --reverse --branches --tags --remotes -- docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md` | exactly 2: SEAL1 `4c67283b46540f997b8a5c6b530996da880b53ed`, SEAL2 `633f1dd0daa24b823d8abab7cff00823a3c2b256` — PASS |
| (iii) ancestry SEAL1 → SEAL2 | `git merge-base --is-ancestor 4c67283 633f1dd` | exit 0 — PASS |
| (iii) ancestry SEAL1 → HEAD | `git merge-base --is-ancestor 4c67283 HEAD` | exit 0 — PASS |
| (iii) ancestry SEAL2 → HEAD | `git merge-base --is-ancestor 633f1dd HEAD` | exit 0 — PASS |
| (iii) manifest commits carry no runs content | `git show --name-only --format= <SEAL1\|SEAL2>` | each lists only `docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md` — PASS |
| (iv) execute the pinned blob | `git show de8633cb3e1a295208d89f5be7472e665aec7822:docs/design/b3-ground-truth/verify-seal2-append.py \| python3 - <repo>` | `SEAL2-APPEND-WHITELIST-OK`, exit 0 — PASS |

**(v) Sealed fields parsed from the SEAL2 blob** (`git show 633f1dd:docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md`):

| Check | Command | Result |
|---|---|---|
| `ANSWER_KEY_COMMIT` | `grep '^ANSWER_KEY_COMMIT:'` on the blob | `ef0ab67cb45957167c99eff468077348432e1474` — PASS |
| `ANSWER_KEY_SHA256` | same | `1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1` — PASS |
| `NEW_ANSWER_KEY_COMMIT` | same | `5f687d95f9be4fef2c0fcd78491c308d4c3861e8` — PASS |
| `NEW_ANSWER_KEY_SHA256` | same | `f58f888c9f4dc86d0e34d5a152c781cb7e9913087405e6e25980bd77e3d753d4` — PASS |
| `DENOM_CATCH_RUNS` / `DENOM_QUIET_RUNS` / `DENOM_TOTAL_RUNS` | same | **15 / 21 / 36**; 15 + 21 == 36 — PASS |

### (2) Ordering — post-change form (one snapshot S binds every run)

| Check | Command | Result |
|---|---|---|
| (i) one S in every fingerprint | `git show HEAD:…/RUN-METHOD-NOTES-phase49.md`, every `## Harness fingerprint — ` block's `batch-sha:` | `14 blocks, batch-sha set ['e6eafbd3b8c4242064997f82fad5edd058d65a1c']` — PASS |
| (ii) Phase-48 tip → S | `git merge-base --is-ancestor 3a9c819df25a7ce5a12250614017d33c3b1b3e5a e6eafbd` | exit 0 — PASS |
| (ii) every 49-01..49-04 commit → S | `git merge-base --is-ancestor <c> e6eafbd` for each commit listed under 49-01 (2), 49-02 (2), 49-03 (12), 49-04 (9) in `runs-v2.11-phase49/PLAN-COMMITS.json` | `26 commits (3a9c819 + 25 plan commits) ancestor of S, failures []` — PASS |
| (iii) S → every run commit in RUNS-COMPLETE.json | `git merge-base --is-ancestor S <rc>` × 36 | `S ancestor of 36/36 run commits` — PASS |
| (iii) fingerprint committer time < pass timestamp | `git log -1 --format=%ct <FPC>` vs `passes[-1].timestamp` × 36 | `FPC committer time < passes[-1].timestamp 36/36` — PASS |
| (iv) transcript sha binding | `shasum -a 256 transcript.jsonl` vs committed `transcript.jsonl.sha256` × 36 | `local transcripts 36/36, sha match 36, sha-only 0` — PASS |
| (iv) post-block provenance re-asserted | `grep -qE '(turingmind-code-review/plugins/vibe-check\|plugins/cache/thejuran/vibe-check)' transcript.jsonl` × 36; `grep -qF /Users/julianamacbook/.vibe-check-snapshots/batch7-e6eafbd3b8c4` × 36 | `BAD regex hits 0; transcripts naming snapshot root 36` — PASS |
| (v) parity record in the notes blob | `git show HEAD:…/RUN-METHOD-NOTES-phase49.md \| grep '^parity:'` | `parity: e6eafbd3b8c4242064997f82fad5edd058d65a1c forward=134/134 reverse=0 extra at 2026-10-06T22:06:46-0400`; `parity: restored released 2.10.0 at 2026-10-07T00:35:55-0400`; `parity: e6eafbd3b8c4242064997f82fad5edd058d65a1c forward=134/134 reverse=0 extra at 2026-10-07T06:27:03-0400`; `parity: restored released 2.10.0 at 2026-10-07T10:15:05-0400` (one forward + one restore per sitting) — PASS |

Fingerprint blocks, in session order:

| session ID (SID) | introducing commit (FPC) | `batch-sha:` | runs governed |
|---|---|---|---|
| 2026-10-06T22:07:24-0400 | `7e2be8b` | S | triggarr-secret-in-logs 1-3 |
| 2026-10-06T22:54:40-0400 | `49a1de4` | S | triggarr-autoescape 1-3 |
| 2026-10-06T23:28:31-0400 | `0e6536d` | S | third-organic-should-catch 1-3 |
| 2026-10-06T23:52:50-0400 | `0c6fea9` | S | should-quiet-1 1-3 |
| 2026-10-07T00:26:38-0400 | `ef347e9` | S | should-quiet-2 1 (and the failed run-2 attempt, sibling `run-2.failed-1791368836`) |
| 2026-10-07T06:28:02-0400 | `55acc34` | S | should-quiet-2 2-3 (sitting-2 relaunch) |
| 2026-10-07T06:42:08-0400 | `ceded68` | S | none committed. This session's only attempt is the failed sibling `should-quiet-3/run-1.failed-1791370396` |
| 2026-10-07T06:54:26-0400 | `6d83ff6` | S | should-quiet-3 1-3 (relaunch after the failed attempt) |
| 2026-10-07T07:19:27-0400 | `84fc144` | S | triggarr-session-rotation 1-3 |
| 2026-10-07T07:48:32-0400 | `dcedd23` | S | triggarr-settings-form-split 1-3 |
| 2026-10-07T08:24:23-0400 | `c34e0a7` | S | should-quiet-4 1-3 |
| 2026-10-07T08:57:42-0400 | `8a59d6c` | S | should-quiet-5 1-3 |
| 2026-10-07T09:18:42-0400 | `b518143` | S | should-quiet-6 1-3 |
| 2026-10-07T09:46:32-0400 | `a6b1078` | S | should-quiet-7 1-3 |

### (3) Dual digest gate (run TWICE) + ancestry

| Check | Command | Result |
|---|---|---|
| v2.9 key blob, pass 1 / pass 2 | `git show ef0ab67:docs/design/b3-ground-truth/ANSWER-KEY-b3.md \| shasum -a 256` | `1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1` both passes == SEAL2 `ANSWER_KEY_SHA256` — PASS |
| v2.10 key blob, pass 1 / pass 2 | `git show 5f687d9:docs/design/b3-ground-truth/ANSWER-KEY-v2.10.md \| shasum -a 256` | `f58f888c9f4dc86d0e34d5a152c781cb7e9913087405e6e25980bd77e3d753d4` both passes == SEAL2 `NEW_ANSWER_KEY_SHA256` — PASS |
| ancestry | `git merge-base --is-ancestor ef0ab67 HEAD`; `… 5f687d9 HEAD` | exit 0; exit 0 — PASS |

### (4) Score-from-blob materialization

| Check | Command | Result |
|---|---|---|
| materialize both keys to scratch | `git show ef0ab67:…/ANSWER-KEY-b3.md > answer-key-b3-scored.md`; `git show 5f687d9:…/ANSWER-KEY-v2.10.md > answer-key-v2.10-scored.md` | 150 lines; 136 lines |
| re-digest the materialized files | `shasum -a 256 answer-key-*-scored.md` | `1463…3fca1`; `f58f…53d4` == sealed — PASS |
| (4d) live-file sanity (warning-only) | `cmp` live key / live manifest vs blob | live `ANSWER-KEY-b3.md`, `ANSWER-KEY-v2.10.md` and the live manifest are byte-identical to their blobs (no drift) — PASS |

Every SITE/AXIS/BAND rule and every `base_sha` in §3/§4 was read from these materialized blobs.

### (5) Layout — 36 run dirs, fixed file set, named siblings, `state_shape`

| Check | Command | Result |
|---|---|---|
| runs tree committed clean | `git status --porcelain -- runs-v2.11-phase49/first/ RUN-METHOD-NOTES-phase49.md` | empty — PASS |
| run dirs | `ls -d first/*/run-[123] \| wc -l` | 36 — PASS |
| voided / failed siblings | `ls first/<diff>/ \| grep -vE '^run-[123]$'` over all 12 diffs | `should-quiet-2/run-2.failed-1791368836`, `should-quiet-3/run-1.failed-1791370396` (both Migration-card misfires, 49-05 Option A, each with a committed `reason.txt`). No `run-N.voided-*`. Both are excluded by name, and `score43.py ledger` reports them as `excluded` — PASS |
| tracked file set per run | `git ls-files first/<diff>/run-<n>/` × 36 vs the RUN-PHASE49 `post` block `FIXED='clear.txt context.txt lanes.json report.md session.txt state.json transcript.jsonl.sha256 tree.diff tree.diff.sha256'` + exactly one Codex disposition (`codex-payload.json codex-rc.txt` OR `codex-absent.txt`) + optional `git-guard-blocks.jsonl` | `violations []; codex variants {'payload+rc': 36}; git-guard records 0`. `transcript.jsonl` is local and untracked — PASS |
| `clear.txt` attestation | full-line `^<ISO±ZZZZ> CLEARED$` × 36 | 36/36 — PASS |
| `state_shape --schema future` | `python3 plugins/vibe-check/scripts/state_shape.py <state.json> --schema future` × 36 | `PASS=36`, rc 0 on every state — PASS |

### (6a) Sidecar seal gate — run BEFORE any sidecar value is consumed

| Check | Command | Result |
|---|---|---|
| carried six blob-equal to v2.9 | `git rev-parse HEAD:<p>` == `git rev-parse v2.9:<p>` == `git hash-object <p>` for each `.patch` + `.provenance` | `12/12 blob-equal HEAD==v2.9==worktree` — PASS |
| new six sha256 == `5f687d9` key lines | sha256 of the HEAD blob AND of the live file vs `sha256(diffs/<f>) = …` in the materialized key | `12/12 sha256 (HEAD blob and live) == 5f687d9 key lines` — PASS |

### (6b) Per-run isolation (after 6a)

| Check | Command | Result |
|---|---|---|
| `len(passes) == 1` | `state.json` | 36/36 — PASS |
| `passes[-1].head_sha == base_sha` (sidecar) | `base_sha:` line of the sealed sidecar | 36/36 — PASS |
| tree.diff triple | `sha256(tree.diff)` == `tree.diff.sha256` == sidecar `EXPECTED_TREE_DIFF_SHA256` | 36/36 — PASS |

Literal line: `len==1 36/36; head==base_sha 36/36; tree triple 36/36`. Per-diff grid: see §2.

### (7) Phase-49 gate — sealed prior archives intact + measured surface unchanged since S

| Check | Command | Result |
|---|---|---|
| (i) v2.9 runs tree | `git diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/` | exit 0 — PASS |
| (i) runs-v2.10 | `git rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10` | `82c412b6e58b5d5a1dbddca0239f0f4b26833b4a` — PASS |
| (i) runs-v2.10-phase40 | `git rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase40` | `29d1344b6b93136d1ae0273008ce34a154360e7b` — PASS |
| (i) runs-v2.10-phase41 | `git rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase41` | `50d25bb33af6a703d19a6eb4fad0e9a4991b19d9` — PASS |
| (i) runs-v2.10-phase43 | `git rev-parse HEAD:docs/design/b3-ground-truth/runs-v2.10-phase43` | `b747a9183219ea2d6f09c62bb07876ff5bf9f0a6` — PASS |
| (i) sealed trees clean | `git status --porcelain -- runs/ runs-v2.10/ runs-v2.10-phase40/ runs-v2.10-phase41/ runs-v2.10-phase43/` | empty — PASS |
| (ii) measured surface S..HEAD (W1) | `git diff --quiet e6eafbd HEAD -- plugins/vibe-check/agents plugins/vibe-check/commands plugins/vibe-check/phases plugins/vibe-check/templates plugins/vibe-check/scripts plugins/vibe-check/hooks` | exit 0 — PASS |

The scorer at HEAD and the scored build at S are the same measured surface, so nothing scored
here can differ from what S ran.

### (8) Security / privacy spot-check (before any bulk scoring)

| Check | Command | Result |
|---|---|---|
| lane + Codex archive privacy scan | `python3 plugins/vibe-check/scripts/lanearchive.py scan first/*/run-[123]/lanes.json first/*/run-[123]/codex-payload.json` | `privacy scan clean: 72 file(s)`, exit 0 — PASS |
| secret-shaped literal grep (the SCORING-v2.10-phase43 §(8) set) | `(sk-ant-…\|sk-[A-Za-z0-9]{32,}\|ghp_…\|github_pat_…\|AKIA[0-9A-Z]{16}\|xox[baprs]-…\|Bearer <20+>\|-----BEGIN … PRIVATE KEY\|api_key=<16+ literal>\|maguffynas)` over `state.json`, `lanes.json`, `codex-payload.json`, `report.md` × 36 | 0 files with a hit in each of the four file kinds — PASS |

Only counts and kinds are printed. This worksheet quotes titles only at a catch SITE (§3) and
quotes finding rows (agent/file/line/band/score/stable_hash) elsewhere.

### (9) Harness evidence — commit-anchored, pin-matched, pre-run-ordered

| Check | Command | Result |
|---|---|---|
| pins (committed notes blob) | `git show HEAD:…/RUN-METHOD-NOTES-phase49.md \| grep '^pin-'` | `pin-claude-code: 2.1.281 (Claude Code)` · `pin-codex: codex-cli 0.153.4` · `pin-model: fable 5.1` · `pin-codex-companion: 1.0.4` · `pin-context-window: 1M` — PASS (no re-pin) |
| pin commit precedes every fingerprint | `git log --format=%H -G'^pin-' -- <notes>`; `git merge-base --is-ancestor 855e8a0 7e2be8b` | one pin commit `855e8a0` (2026-10-06T19:28:31-04:00); ancestor of the first FPC `7e2be8b`, exit 0 — PASS |
| fingerprint fields (14 blocks) | parse the anchored `^## Harness fingerprint — <ISO>$` blocks | `claude-code: 2.1.281 (Claude Code)` 14/14 · `model: Fable 5.1` 14/14 (normalizes to EXACT `fable 5.1`, entry 003) · `context-window: 1M` 14/14 · `codex: codex-cli 0.153.4` 14/14 · `codex-companion: 1.0.4` 14/14 · `driver: assistant-tmux` 14/14 · `autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)` 14/14 · `plugin-root: …/batch7-e6eafbd3b8c4/plugins/vibe-check` 14/14; 0 duplicate SIDs — PASS |
| per-run session binding | for each run: `session.txt` = SID + FPC; FPC touches only the notes file; SID block present at FPC and absent at FPC^; FPC ≠ RC and `merge-base --is-ancestor FPC RC` | 36/36 — PASS |
| driver check (re-derived from the COMMITTED runbook) | the `cat > "$DRIVER_PY" <<'DRIVERPY'` … `DRIVERPY` body extracted from `git show HEAD:docs/design/b3-ground-truth/RUN-PHASE49-v2.11.md` into the scratchpad (never `~/.b3/p49-driver-check.py`); `python3 <it> transcript.jsonl` × 36 local sha-matched transcripts | `none 36/36; fail []; sha-only 0`. Each run's output line equals, character for character, the `driver contamination: none (typed=… harness-skipped=… answers=…)` line in the 49-05-SUMMARY per-run table (36/36 match). `ALLOWED_ANSWERS = {"Stop here…", "Abandon"}`, equal to the Phase-47 labels 49-04 captured live — PASS |
| attestation precedes the review | `clear.txt` time < `passes[-1].timestamp` | 36/36 — PASS |

**Ladder result: gates (1)–(9) all PASS. Scoring authorized.**

---

## 2. Scoreable-completeness ledger (NO AGGREGATION OVER HOLES)

`python3 plugins/vibe-check/scripts/score43.py ledger --runs-root docs/design/b3-ground-truth/runs-v2.11-phase49/first`
→ exit 0:

```
triggarr-secret-in-logs: scoreable [1, 2, 3]
triggarr-autoescape: scoreable [1, 2, 3]
third-organic-should-catch: scoreable [1, 2, 3]
should-quiet-1: scoreable [1, 2, 3]
should-quiet-2: scoreable [1, 2, 3] excluded ['run-2.failed-1791368836']
should-quiet-3: scoreable [1, 2, 3] excluded ['run-1.failed-1791370396']
triggarr-session-rotation: scoreable [1, 2, 3]
triggarr-settings-form-split: scoreable [1, 2, 3]
should-quiet-4: scoreable [1, 2, 3]
should-quiet-5: scoreable [1, 2, 3]
should-quiet-6: scoreable [1, 2, 3]
should-quiet-7: scoreable [1, 2, 3]
ledger complete: 12 diffs x 3, no holes, no extras
```

The diff universe is the committed inventory: the 12 `diffs/*.provenance` sidecars, which also form
`RUNS-COMPLETE.json` `expected_diffs`. Run commits below are from `RUNS-COMPLETE.json` (`e4b8237`),
and every one passed gates (2)(iii) and (6b).

| diff-id | role | run-1 commit | run-2 commit | run-3 commit | scoreable |
|---|---|---|---|---|---|
| triggarr-secret-in-logs | should-catch | `55cc775ba52f5fd44771986902baf0747152a21a` | `604251f831aa60f462b3fe82f15e523896130d30` | `876ce174a62a514b104a97840e2580496a886753` | **3/3** |
| triggarr-autoescape | should-catch | `41cf188eae66c7217be7954c9909f317087ccfee` | `e50e912b0d3045d489806fa085e508dfe9e5e775` | `dbeacbcaa343377163b0180371fcd142ce1105f5` | **3/3** |
| third-organic-should-catch | should-catch | `34505b0ba7646f821653c23bd115e7013bdd52e5` | `dc64ec0367803211425b0cc697289b2485f05c81` | `d2277703b73b4f77d75af30bd0d4a6fc4205f7d6` | **3/3** |
| should-quiet-1 | should-quiet | `13b850a122259aad2ae8664811866147d6503f14` | `2e8376acc4dcab619d343ba524315bb736a3dfe3` | `52127ab6188a527e30b615eb136586711a8ac918` | **3/3** |
| should-quiet-2 | should-quiet | `11138013a394a854fe2e718051e3d71b1d1838d1` | `4561136334014e3eb8b33fcc2a5e183aca2c9a19` | `748a0b6818dbea084fa2aab67f38b4bf89b24187` | **3/3** |
| should-quiet-3 | should-quiet | `9db56e7e8188d72d228f1a067ab7e2b43f0b6786` | `97c7928e4359d0150aafcf10c43419c4723e930c` | `6793e4015b811a6206663b94e751d3e374e4bac2` | **3/3** |
| triggarr-session-rotation | should-catch | `e24e652c1b542a982fcea282bbee0369fc850d80` | `07d88e27bb06e3a806b95ffb2c200b5eeff02b55` | `143f425b7a29208fc621299eb9fe5df7a36e178c` | **3/3** |
| triggarr-settings-form-split | should-catch | `901f2dae6369f62206f04d83de0a79d2d9aef1c4` | `48190937d8e59925d654dad54f97d6d1c5c2943e` | `2c3626c76265e3783368dfe516cdd259b729cf1b` | **3/3** |
| should-quiet-4 | should-quiet | `e86c8ede568ca993adf4b61cab9d2ec178d0e787` | `dd49a9e3178e837b4bf1e1d59c813c5da92bb9af` | `a9e1ddf3a9c81c509b76c8381431c6b5ca35f9f8` | **3/3** |
| should-quiet-5 | should-quiet | `540d3f51676430b2e4d50e882b9e4a511a133ef0` | `b87dd30c4378c1f20ca0030360c9f0949eeaa1df` | `af24c77c3b04229a187366c465dea60afc49977b` | **3/3** |
| should-quiet-6 | should-quiet | `727c7920fc5a342638f3900c7b1124d2176e86ea` | `cc2bb5713171ad97ba4e67e3aaa49f2fd7e3fa7e` | `a704eb4976d4e804b258da344b1209ba64f7ca4c` | **3/3** |
| should-quiet-7 | should-quiet | `0c30f86fe3ccc52c77a63775eb417343a0845a94` | `3d89175becc8c596a806354eda7697dab2805f9c` | `b6270edd7062efbe230099ea86efe0cf9ca1e74e` | **3/3** |

Isolation and tree.diff grid (gate 6b). The sealed sidecar `base_sha` and
`EXPECTED_TREE_DIFF_SHA256` are shown as prefixes:

| diff-id | base_sha | EXPECTED_TREE_DIFF_SHA256 | run-1 | run-2 | run-3 |
|---|---|---|---|---|---|
| triggarr-secret-in-logs | `f4366a2` | `f0c70a02…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| triggarr-autoescape | `e11187e` | `4fdadb70…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| third-organic-should-catch | `3db8b48` | `d9918036…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| should-quiet-1 | `98eb419` | `a8137f5d…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| should-quiet-2 | `84aff27` | `3cb198dc…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| should-quiet-3 | `1027691` | `66fe1425…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| triggarr-session-rotation | `f4366a2` | `a924c819…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| triggarr-settings-form-split | `542d5dd` | `40ae123c…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| should-quiet-4 | `14eecb5` | `f71a7730…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| should-quiet-5 | `7035477` | `8af04cc6…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| should-quiet-6 | `9bfd4a6` | `75704ed5…` | len=1,head ✓,tree ✓ | ✓ | ✓ |
| should-quiet-7 | `ce567d3` | `d94fb90d…` | len=1,head ✓,tree ✓ | ✓ | ✓ |

**All 36 slots are filled; zero holes, zero unscoreable.** The role denominators by construction
are 5 × 3 = 15 catch and 7 × 3 = 21 quiet. They equal the sealed `DENOM_*` lines. The corrected
quiet denominator is 21 − 3 (should-quiet-7, #001) = 18.
**Rule: NO AGGREGATION OVER HOLES.** **Owner waiver: NONE** (none needed).

### Failed attempts, gitsnap halts and git-guard blocks in the window

| event | slot | evidence | effect on scoring |
|---|---|---|---|
| failed attempt (Migration card fired before the review; owner Option A) | should-quiet-2/run-2 | sibling `run-2.failed-1791368836` (`392c111`) with `reason.txt`; slot redone in sitting 2 as run commit `4561136` | none. The sibling is excluded by name, and the redone run-2 is the scored run |
| failed attempt (same Migration card) | should-quiet-3/run-1 | sibling `run-1.failed-1791370396` (`9625395`) with `reason.txt`; its session `ceded68` governs no committed run; slot redone under the relaunch fingerprint `6d83ff6` as run commit `9db56e7` | none. The sibling is excluded by name, and the redone run-1 is the scored run |
| gitsnap halt | — | 0 in the window (49-05) | none |
| git-guard block | — | 0 (`git-guard-blocks.jsonl` tracked on 0 runs, gate 5) | none |

The Migration-card defect (07-first-run step 3 fires although `.turingmind/` exists) is pre-existing
in 2.10.0. It ended both attempts before any review ran, so neither attempt produced a pass.

### Lane-set irregularities, and their effect on scoring

Scoring reads only `state.passes[-1].findings[]`. `lanes.json` is evidence for confound audits,
not a scoring input. Every run has `malformed=0` and `recovered == dispatched`. Each irregularity
was checked against the scored cell it could touch:

| run | irregularity (from `lanes.json`) | effect on the scored cell |
|---|---|---|
| triggarr-session-rotation/run-1 | 7 lanes dispatched vs 8 in runs 2-3 (no `framework-fastapi`) | none. The run is a CATCH on the bugs-led row (§3.4) |
| should-quiet-7/run-1 | 7 lanes vs 8 in runs 2-3 (no `framework-fastapi`) | none on the verdict. The diff is excluded (#001), and all three runs fire either way |
| triggarr-secret-in-logs/run-1 | `codex_lines=2`: the Codex lane was captured twice | none. The state holds one codex-led surviving row (`codex_findings=1`). The duplication exists only in the archive |
| should-quiet-6/run-2 | `codex_lines=2` | none. The state holds one codex-led row (`codex_findings=1`), and the run fires on it |
| should-quiet-6/run-3 | 1 lane with `parsed=None` (a prose return; `malformed=0`) | none. The run fires on its codex-led row regardless |

Triage still varies in whether it dispatches the FastAPI framework lane on triggarr diffs. That is an
orchestration-nondeterminism fact. No scored cell in this pass moves because of it.

---

## 3. Per-run scoring — should-catch diffs (three-gate rule)

A **catch** requires all three gates:

- **SITE:** the right file, within the planted hunk, keyed to the row's `base_sha`. For
  session-rotation, SITE is judged in run-tree coordinates (entry 002).
- **AXIS:** the finding names the key's required MECHANISM and honors the row's NOT-clause.
- **BAND:** the rendered band is ≥ the row's floor.

SITE-only, or SITE+AXIS below band, is `detected-below-threshold`, which counts as a MISS.

**AXIS basis (pre-registered, `RESULTS-v2.11.md` §"Phase-49 pre-registration" 4).** The sealed key
gates AXIS on the finding's `title`, with `category` only as corroboration (`ef0ab67` key, "The
three-gate catch rule", gate 2). Entry 007 extends this: AXIS is met when the surviving row's OWN
title OR ANY `members[].title` names the mechanism. SITE and BAND are still judged on the
surviving row. `filtered[]` and the raw lane envelopes are not scoring input. This is the same
title/member-title basis Phase 43 used, so the numbers stay comparable.

**Order of work.** The hand AXIS column below was written on 2026-10-07 (from 16:27Z on), from the
`score43.py catch-candidates` output and the two materialized key blobs. It was written before
`runs-v2.10-phase43/retune/COMBINED-VERDICT.json` and the Phase-43 retune/combined per-run tables
(`SCORING-v2.10-phase43.md` §7.x) were opened. Disclosure, as facts:

- `SCORING-v2.10-phase43.md` lines 1-560, which include its FIRST-PASS §3/§4 tables, were read
  beforehand as this file's mandated template.
- The quiet arm (§4) was computed mechanically before the AXIS calls. It already stands at 5 of
  18 against a bar of ≤ 3, so the verdict does not depend on any AXIS call made below.

The candidate tables are verbatim `score43.py catch-candidates` output: rows at SITE with band ≥
floor. The `AXIS` column of that output is blank by design, and the hand call is in the run table
beneath it. The Codex column is from `score43.py codex-status`.

### 3.1 triggarr-secret-in-logs (carried → `ef0ab67`) — SITE `triggarr/clients/base.py` : 230-238 / 249-256 · AXIS = Secret/PII (API key) leaked into logs (NOT "log formatting inconsistency") · BAND floor = warning

Sealed AXIS text (`ef0ab67`): "**Secret/PII (API key) leaked into logs** — `logger.warning(...,
exc=exc)` interpolates the full exception … into log output. NOT "log formatting inconsistency"".

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | codex-adversarial | 233 | critical | 100 | 658136bf0a0d | HTTP error logging exposes reverse-proxy credentials | security: "re-logs raw httpx exception (key-leakage risk)"; bugs: "the full request URL (and any ?apikey= query value), is now logged" |
| 1 | security | 252 | warning | 94 | 1f05d792a41d | Diff reverts CodeQL-flagged fix, re-logs raw pydantic ValidationError | bugs: "the full pydantic ValidationError text, including raw response input values, is now logged" |
| 2 | codex-adversarial | 233 | critical | 100 | 231222c433af | HTTP failure logging exposes reverse-proxy credentials | security: "bypasses established _sanitize_exc redaction pattern, can leak API key via URL"; impact: "Credential exposure: … basic-auth userinfo in the instance URL reaches logs" |
| 2 | compliance | 251 | warning | 94 | 48ab3c20fcc2 | Raw pydantic.ValidationError logged, reverting a prior CodeQL-flagged fix | bugs: "dumps upstream response input values into logs" |
| 3 | codex-adversarial | 233 | critical | 100 | 4a44f13b760e | HTTP error logging exposes reverse-proxy passwords | security: "raw exception logged, may leak API key via request URL"; impact: "exposing request URL (incl. any userinfo credentials …)" |
| 3 | security | 252 | warning | 94 | 7b65158797ac | Reverts prior security fix: raw ValidationError logged instead of sanitized error count | bugs: "upstream response values are written to the logs" |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L233 [critical, 100] "HTTP error logging exposes reverse-proxy credentials" | ✓ | ✓ the survivor title names credentials exposed through log output, and the security member names the API-key leak. Not a formatting framing | ✓ critical | CATCH | joined |
| run-2 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L233 [critical, 100] "HTTP failure logging exposes reverse-proxy credentials" (+ security member "can leak API key via URL") | ✓ | ✓ the titles name the credential/API-key leak into logs | ✓ critical | CATCH | joined |
| run-3 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L233 [critical, 100] "HTTP error logging exposes reverse-proxy passwords" (+ security member "may leak API key via request URL") | ✓ | ✓ the titles name the credential leak into logs | ✓ critical | CATCH | joined |

Three-gate reason for all three runs: CATCH. **Per-diff: 3/3 catch.** Codex dropouts: 0.

### 3.2 triggarr-autoescape (carried → `ef0ab67`) — SITE `triggarr/web/routes.py` : 42-48 (bug line 45) · AXIS = XSS surface re-enabled / autoescape not in effect — "The finding must name the escaping/XSS consequence (autoescape not in effect / XSS), not merely 'refactor reverted' or 'unused import'" · BAND floor = warning

Sealed AXIS text, quoted from the `ef0ab67` blob: "**XSS surface re-enabled by losing the
preconfigured autoescape `jinja2.Environment`** — on current Starlette,
`Jinja2Templates(directory=..., autoescape=True)` silently NO-OPs autoescape … so template
auto-escaping is OFF. The finding must name the escaping/XSS consequence (autoescape not in effect /
XSS), not merely "refactor reverted" or "unused import"."

Precedents applied (`REPLAY-CATCH-MANIFEST-v2.10.json`, title-only): axis=true for titles naming an
XSS risk that the autoescape loss opens ("risking silent XSS on future Starlette upgrade",
"forward-compat XSS regression"). axis=false for revert/deprecation framing that does not name
escaping-off or XSS ("Reverts autoescape fix onto Starlette's deprecated env_options path").

Each run has ONE surviving row at SITE, and every lane collapsed into it (H-LANE). All member titles:

| run | agent | line | band | score | stable_hash | survivor title | member titles (agent) |
|---|---|---|---|---|---|---|---|
| 1 | codex-adversarial | 45 | critical | 100 | a698a47ec342 | XSS protection now depends on deprecated environment options | language-python "Diff reverts the just-made jinja2.Environment fix, undoing documented autoescape remediation"; bugs "…HTML escaping (protection against injected scripts, XSS) now depends on the installed Starlette version, and the module can crash at import"; architecture "Reverts HEAD's fix and goes back to the deprecated Jinja2Templates env_options passthrough…"; impact "Revert puts XSS autoescaping back on Starlette's deprecated env_options path…"; **security "Autoescape guarantee downgraded from explicit jinja2.Environment to deprecated Starlette passthrough, risking stored/reflected XSS on a routine dependency bump"**; framework-fastapi "Reverts prior fix, reintroducing deprecated Jinja2Templates env_options kwarg" |
| 2 | architecture | 45 | critical | 100 | 54fb2407ec58 | Diff reverts the previous commit's switch to a preconfigured jinja2.Environment and goes back to the deprecated **env_options passthrough | **security "Autoescape protection downgraded to a deprecated, version-fragile Starlette path (stored/reflected XSS risk)"**; codex-adversarial "Preserve explicit escaping against cross-site scripting"; impact "Revert puts the HTML autoescape setting (the XSS guard) back on Starlette's deprecated **env_options path…"; bugs "…makes template autoescape (XSS protection) and app startup depend on the Starlette version"; framework-fastapi "Diff reverts the dedicated fix for Starlette's deprecated Jinja2Templates env_options passthrough"; compliance "…re-exposing Jinja2 autoescape to dependency drift" |
| 3 | security | 45 | critical | 100 | 88415c2446d7 | Autoescape guarantee downgraded from explicit jinja2.Environment to deprecated Starlette kwarg passthrough, reopening XSS risk on future upgrades | codex-adversarial "XSS protection now depends on deprecated environment options"; architecture "Diff reverts commit e11187e and goes back to the deprecated Jinja2Templates env_options API"; impact "…with unpinned Docker builds this risks a startup outage or lost escaping"; bugs "Revert puts template autoescaping (the XSS guard) on Starlette's deprecated env_options path"; framework-fastapi "Diff reverts the deliberate autoescape fix…" |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=e11187e ✓ | ✓ | `codex-adversarial` L45 [critical, 100] "XSS protection now depends on deprecated environment options"; AXIS also carried by member `security` "…risking stored/reflected XSS on a routine dependency bump" | ✓ | ✓ The security member title names the XSS consequence of losing the guaranteed escaper. It is the same class as the recorded axis=true "risking silent XSS on future Starlette upgrade". The survivor title also names XSS protection as what is lost, not merely the revert | ✓ critical | CATCH | joined |
| run-2 | len=1,head=e11187e ✓ | ✓ | `architecture` L45 [critical, 100] (revert/deprecation framing; alone it would be axis=false); AXIS carried by member `security` "…version-fragile Starlette path (stored/reflected XSS risk)" | ✓ | ✓ via members (entry 007). The security member names stored/reflected XSS as the consequence. The codex member "Preserve explicit escaping against cross-site scripting" and the bugs member "(XSS protection)" corroborate | ✓ critical | CATCH | joined (Codex verdict carried as a member; `codex_findings=0` survived as lead) |
| run-3 | len=1,head=e11187e ✓ | ✓ | `security` L45 [critical, 100] "…reopening XSS risk on future upgrades" | ✓ | ✓ The survivor title names the XSS risk reopened by the escaper downgrade, the axis=true class ("forward-compat XSS regression") | ✓ critical | CATCH | joined (`codex_findings=0` as lead) |

Three-gate reason for all three runs: CATCH. **Per-diff: 3/3 catch.** Codex dropouts: 0.

**Sensitivity.** Every crediting title frames the XSS risk as version-dependent ("on a routine
dependency bump", "version-fragile", "on future upgrades"). The sealed premise is that escaping is
off on current Starlette. The recorded precedent ("risking silent XSS on future Starlette upgrade"
= axis=true) treats the forward-risk framing as naming the XSS consequence, and that precedent
decides here. A stricter reading that requires "escaping is off now" would give 0/3 on this diff
and a catch arm of 12/15. That reading is not the pre-registered basis, and it could not change
the verdict: the quiet arm already misses (§4). Under either reading the verdict is MISS.

### 3.3 third-organic-should-catch (carried → `ef0ab67`) — SITE `src/angular/src/app/services/files/view-file.service.ts` : 304-311 · AXIS = Unclamped percentage — no upper bound, >100% / missing clamp (not generic style) · BAND floor = medium

Sealed AXIS text (`ef0ab67`): "**Unclamped percentage — `percentDownloaded` computed as
`Math.trunc(100 * local / remote)` with NO upper bound** … The finding must name the missing clamp
/ out-of-range value, not generic style."

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | bugs | 308 | critical | 100 | 3cd35f3c5a22 | Removing the 100% cap lets extracted files show more than 100% progress (e.g. "199%") and drop their success/Done state | impact: "Removing the percent clamp brings back the >100% progress bug"; codex-adversarial: "Completed extracted files display over 100%…" |
| 2 | bugs | 308 | critical | 100 | 42c92424be1e | Clamp removed: extracted files show over 100% progress and lose their 'Done' and success states | language-typescript: "Removed clamp lets percentDownloaded exceed 100"; impact: "brings back the >100% progress bug" |
| 3 | bugs | 308 | critical | 100 | 0909ed738eaf | Removing the 100% clamp brings back progress labels like "199%" for extracted files | language-typescript: "reintroduces the >100% progress display bug"; impact: "brings back the '199%' progress display" |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=3db8b48 ✓ | ✓ | `bugs` L308 [critical, 100] "Removing the 100% cap lets extracted files show more than 100% progress…" | ✓ | ✓ names the missing cap / >100% and the lost Done state | ✓ critical ≥ medium | CATCH | joined |
| run-2 | len=1,head=3db8b48 ✓ | ✓ | `bugs` L308 [critical, 100] "Clamp removed: extracted files show over 100% progress…" | ✓ | ✓ names the missing clamp / >100% | ✓ critical | CATCH | joined |
| run-3 | len=1,head=3db8b48 ✓ | ✓ | `bugs` L308 [critical, 100] "Removing the 100% clamp brings back progress labels like "199%"…" | ✓ | ✓ names the missing clamp / out-of-range value | ✓ critical | CATCH | joined |

Three-gate reason for all three runs: CATCH. **Per-diff: 3/3 catch.** Codex dropouts: 0.

### 3.4 triggarr-session-rotation (new → `5f687d9`) — SITE `triggarr/web/routes.py` : 1445-1451 / 1459-1469 (patch coordinates; run-tree 1564-1588 per entry 002) · AXIS = Stale-session survival — password change no longer evicts existing sessions (NOT dead-code cleanup, NOT logging removed, NOT a response-refactor or cookie-attribute nit) · BAND floor = warning

Sealed AXIS text (`5f687d9`): "**Stale-session survival — password change no longer evicts existing
sessions** … The finding must name the session-eviction/invalidation consequence (old sessions
remain valid / compromised session survives). NOT "dead code or comment cleanup", NOT "logging
removed", NOT a response-refactor or cookie-attribute nit".

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | bugs | 1567 | critical | 100 | 1c14bf7ba766 | Password change no longer rotates session_secret, so stolen or other-device session cookies stay valid (session-hijack persistence) | security: "leaving stolen/compromised sessions valid after a password change"; impact: "Changing the password no longer logs out other sessions"; codex-adversarial: "Stolen session cookies retain access after password changes" |
| 2 | bugs | 1567 | critical | 100 | 2bced0bfc4e2 | Changing the password no longer rotates session_secret, so stolen or other-device session cookies stay valid (session-hijack persistence) | impact: "hijacked sessions survive the change"; security: "Password change no longer invalidates other sessions" |
| 2 | impact | 1581 | warning | 90 | f91ec7580f99 | Removal breaks four existing tests that assert rotation, cookie re-issue and eviction of other devices | — |
| 3 | codex-adversarial | 1567 | critical | 100 | 29044f82a356 | Stolen session cookies remain usable after password changes | bugs: "stolen or stale session cookies stay valid after the change"; impact: "Password change no longer logs out other sessions"; security: "no longer invalidates other active sessions" |
| 3 | bugs | 1581 | warning | 90 | af39099f84a2 | Existing tests that assert rotation and cookie re-issue on password change will now fail | — |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=f4366a2 ✓ | ✓ | `bugs` L1567 [critical, 100] "…stolen or other-device session cookies stay valid (session-hijack persistence)" | ✓ (run-tree, entry 002) | ✓ names old sessions remaining valid after the password change | ✓ critical | CATCH | joined |
| run-2 | len=1,head=f4366a2 ✓ | ✓ | `bugs` L1567 [critical, 100] "…stolen or other-device session cookies stay valid…" | ✓ | ✓ names old sessions surviving | ✓ critical | CATCH | joined |
| run-3 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L1567 [critical, 100] "Stolen session cookies remain usable after password changes" | ✓ | ✓ names compromised sessions surviving the password change | ✓ critical | CATCH | joined |

Three-gate reason for all three runs: CATCH. **Per-diff: 3/3 catch.** Codex dropouts: 0.

### 3.5 triggarr-settings-form-split (new → `5f687d9`) — SITE `triggarr/templates/settings.html` : 15-28 / 33-81 / 87-93 / 131-137 · AXIS = Silent data loss on save — General fields no longer submitted (NOT HTML restructuring, NOT duplicate form action, NOT a styling/a11y nit) · BAND floor = warning

Sealed AXIS text (`5f687d9`): "**Silent data loss on save — General settings fields are no longer
submitted** … The finding must name the broken form association / fields-not-submitted /
values-lost-on-save consequence. NOT "HTML restructuring", NOT "duplicate form action", NOT a
styling or accessibility nit".

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | bugs | 134 | warning | 94 | 5a398c7f3153 | Save Settings now resets every General setting to its hardcoded default | architecture: "instance saves reset General settings to defaults" |
| 1 | impact | 18 | critical | 100 | 346b34a613ea | Reverting the form association makes every Save silently reset all General settings to defaults (config data loss) | codex-adversarial: "Splitting the forms drops General fields and resets saved limits"; bugs: "its changes can never be saved" |
| 2 | bugs | 18 | critical | 100 | 09e5ac6fbd78 | General settings fields are in a form with no submit button, so Save never sends them | impact: "every Save Settings resets all General settings to defaults"; codex-adversarial: "Split forms cause every settings save to overwrite General configuration" |
| 2 | bugs | 134 | warning | 94 | b093c747acac | Saving instance settings resets all General config to hardcoded defaults and turns off skip_unreleased | — |
| 3 | bugs | 134 | warning | 94 | 18252571b234 | Save Settings silently resets all General settings to defaults (reverts fix 542d5dd) | impact: "Saving settings quietly resets every General setting to its hard-coded default" |
| 3 | architecture | 18 | critical | 100 | 09b7f41531dd | Diff reverts fix 542d5dd: two sibling save_settings forms split one logical submission | bugs: "General edits can never be saved"; codex-adversarial: "Splitting the forms drops General fields on every settings save"; impact: "General changes cannot be saved" |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=542d5dd ✓ | ✓ | `impact` L18 [critical, 100] "Reverting the form association makes every Save silently reset all General settings to defaults (config data loss)" | ✓ | ✓ names the broken association and the values lost on save | ✓ critical | CATCH | joined |
| run-2 | len=1,head=542d5dd ✓ | ✓ | `bugs` L18 [critical, 100] "General settings fields are in a form with no submit button, so Save never sends them" | ✓ | ✓ names the fields not submitted | ✓ critical | CATCH | joined |
| run-3 | len=1,head=542d5dd ✓ | ✓ | `bugs` L134 [warning, 94] "Save Settings silently resets all General settings to defaults"; `architecture` L18 [critical] (members: "General edits can never be saved") | ✓ | ✓ names values lost on save | ✓ critical/warning | CATCH | joined |

Three-gate reason for all three runs: CATCH. **Per-diff: 3/3 catch.** Codex dropouts: 0. In none
of the three runs did a codex-led row survive (`codex_findings=0`). Codex was joined, and its
finding rides as a member of the L18 row in all three runs.

**Catch arm (hand column): 15 CATCH, 0 MISS.**

---

## 4. Per-run scoring — should-quiet diffs (D-08 FP rule)

An **FP** on a should-quiet diff is ANY surviving finding with band **critical OR warning**. It is
not site-gated. Medium/low findings are noise-notes: recorded, not counted. A run with no
critical/warning row is QUIET. Rows are verbatim `score43.py fp` output (agent/file/line/band/score/
stable_hash; no titles). The notes column carries facts only.

### 4.1 should-quiet-1 (carried) — `triggarr/web/validation.py` : 79-91 · safe ON SSRF / input-validation (the diff TIGHTENS the host block-list) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=98eb419 ✓ | ✓ | none (`fired: False (0 critical/warning rows)`) | QUIET | joined | 0 findings |
| run-2 | len=1,head=98eb419 ✓ | ✓ | none | QUIET | joined | 0 findings |
| run-3 | len=1,head=98eb419 ✓ | ✓ | none | QUIET | joined | 0 findings |

**Per-diff: 0/3 fired.** Codex dropouts: 0.

### 4.2 should-quiet-2 (carried) — `src/angular/src/app/services/utils/rest.service.ts` : 53-63 · safe ON API contract / typing · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=84aff27 ✓ | ✓ | none | QUIET | joined | 0 findings; 7 lanes |
| run-2 | len=1,head=84aff27 ✓ | ✓ | none | QUIET | joined | 0 findings; 7 lanes; the redone slot (the failed sibling is excluded, §2) |
| run-3 | len=1,head=84aff27 ✓ | ✓ | none | QUIET | joined | 0 findings; 7 lanes |

**Per-diff: 0/3 fired.** Codex dropouts: 0.

### 4.3 should-quiet-3 (carried) — `src/roonseek/transfer.py` : 201-218, 220, 256-257 · safe ON HTTP-client / path-injection / error-handling · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=1027691 ✓ | ✓ | language-python `src/roonseek/transfer.py`:259 [warning, 82] `5c905a9fc3e6` | FP | joined | one warning row, category `optional-handling`, lead `language-python`; members language-python, bugs, impact, architecture; L259 is 2 lines past the planted hunk's 256-257 (FP is not site-gated); the redone slot (§2); `codex_findings=0` |
| run-2 | len=1,head=1027691 ✓ | ✓ | none | QUIET | joined | 0 findings |
| run-3 | len=1,head=1027691 ✓ | ✓ | none | QUIET | joined | 0 findings |

**Per-diff: 1/3 fired.** Codex dropouts: 0. This is a new alarm on a diff that the pre-registration
expected to stay quiet.

### 4.4 should-quiet-4 (new) — `triggarr/models/config.py` : 88-115 · safe ON SSRF / input-validation (ADDS `validate_url_ssrf`, tightening the guard) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=14eecb5 ✓ | ✓ | none | QUIET | joined | 1 medium noise-note (bugs L108, `a11aff939068`) |
| run-2 | len=1,head=14eecb5 ✓ | ✓ | security `triggarr/models/config.py`:93 [warning, 94] `2da26ca95733` | FP | joined | one warning row, category `ssrf`, single-member (security only), inside the planted hunk; plus 1 medium noise-note (bugs L108, `f12fbe78be96`); `codex_findings=0` |
| run-3 | len=1,head=14eecb5 ✓ | ✓ | none | QUIET | joined | 0 findings |

**Per-diff: 1/3 fired.** Codex dropouts: 0. In none of the three runs did a codex-led row survive.

### 4.5 should-quiet-5 (new) — `src/python/model/model.py` : 3-9, 78-84, 94-100, 109-115 · safe ON log-sanitization / secret-handling · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=7035477 ✓ | ✓ | none | QUIET | joined | 0 findings |
| run-2 | len=1,head=7035477 ✓ | ✓ | none | QUIET | joined | 0 findings |
| run-3 | len=1,head=7035477 ✓ | ✓ | none | QUIET | joined | 0 findings |

**Per-diff: 0/3 fired.** Codex dropouts: 0.

### 4.6 should-quiet-6 (new) — `triggarr/models/config.py` : 132-142 · safe ON input-validation / config bounds · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=9bfd4a6 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:135 [critical, 100] `780e77edbe52` | FP | joined | codex-led row; members codex, architecture |
| run-2 | len=1,head=9bfd4a6 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:139 [critical, 100] `c93be6bfe251` | FP | joined | codex-led row; members codex, bugs×2, impact; `codex_lines=2` (§2) |
| run-3 | len=1,head=9bfd4a6 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:139 [critical, 100] `993c32eb9391` | FP | joined | codex-led row; members codex, bugs×2, impact; one lane `parsed=None` (§2) |

**Per-diff: 3/3 fired.** Codex dropouts: 0. This is the pre-registered expected residual ("declared
but never wired", backlog 999.19).

### 4.7 should-quiet-7 (new) — `triggarr/web/routes.py` : 60-66, 443-449, 547-553 · safe ON settings input-parse path · any critical/warning = FP · **excluded from the verdict (#001)**

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=ce567d3 ✓ | ✓ | bugs `triggarr/web/routes.py`:550 [critical, 100] `4d966837bba8`; codex-adversarial `triggarr/web/routes.py`:446 [warning, 94] `30c1d8feff9e` | FP | joined | excluded (SUPERSESSIONS #001 — descriptive only); 7 lanes |
| run-2 | len=1,head=ce567d3 ✓ | ✓ | codex-adversarial `triggarr/web/routes.py`:550 [critical, 100] `0ceea335d7ac`; codex-adversarial `triggarr/web/routes.py`:446 [warning, 94] `0eeb469a0669` | FP | joined | excluded (SUPERSESSIONS #001 — descriptive only); 8 lanes |
| run-3 | len=1,head=ce567d3 ✓ | ✓ | codex-adversarial `triggarr/web/routes.py`:550 [critical, 100] `e09c5b0965cc` | FP | joined | excluded (SUPERSESSIONS #001 — descriptive only); 8 lanes |

**Per-diff: 3/3 fired (descriptive).** These runs count only in the sealed-literal x/21. They never
count in the corrected 18, in the verdict, or in FAILED-DIFFS.

### Codex dropouts per diff (D-08)

`score43.py codex-status`: `codex.status=joined reason=null dropout=no` on **all 36 runs**.

| diff-id | runs | Codex joined | dropouts |
|---|---|---|---|
| triggarr-secret-in-logs | 3 | 3 | 0 |
| triggarr-autoescape | 3 | 3 | 0 |
| third-organic-should-catch | 3 | 3 | 0 |
| should-quiet-1 | 3 | 3 | 0 |
| should-quiet-2 | 3 | 3 | 0 |
| should-quiet-3 | 3 | 3 | 0 |
| triggarr-session-rotation | 3 | 3 | 0 |
| triggarr-settings-form-split | 3 | 3 | 0 |
| should-quiet-4 | 3 | 3 | 0 |
| should-quiet-5 | 3 | 3 | 0 |
| should-quiet-6 | 3 | 3 | 0 |
| should-quiet-7 | 3 | 3 | 0 |

**Quiet arm (mechanical): fired runs among the corrected 18 = should-quiet-3/run-1,
should-quiet-4/run-2, should-quiet-6/run-1, run-2, run-3 → 5. should-quiet-7 fired 3/3 (excluded).**

The §3 AXIS column was written before the Phase-43 per-run tables and COMBINED-VERDICT.json were opened (2026-10-07; the Phase-43 retune/combined tables and `runs-v2.10-phase43/retune/COMBINED-VERDICT.json` were first opened after this sentence was written).

### Comparison vs Phase-43 combined

Descriptive only. It never feeds a verdict cell. The Phase-43 column is `per_diff` from
`runs-v2.10-phase43/retune/COMBINED-VERDICT.json` (combined PASS: 3/18, 15/15, sealed literal 6/21).
That combined result is itself a mix: the retuned diffs (should-quiet-4, should-quiet-6,
triggarr-autoescape) are from the S2 retune, and the rest are from the Phase-43 first pass.

| diff-id | role | v2.11 first pass | Phase-43 combined | direction |
|---|---|---|---|---|
| triggarr-secret-in-logs | should-catch | 3/3 catch | 3/3 catch | same |
| triggarr-autoescape | should-catch | 3/3 catch | 3/3 catch | same |
| third-organic-should-catch | should-catch | 3/3 catch | 3/3 catch | same |
| triggarr-session-rotation | should-catch | 3/3 catch | 3/3 catch | same |
| triggarr-settings-form-split | should-catch | 3/3 catch | 3/3 catch | same |
| should-quiet-1 | should-quiet | 0/3 fired | 0/3 fired | same |
| should-quiet-2 | should-quiet | 0/3 fired | 0/3 fired | same |
| should-quiet-3 | should-quiet | **1/3 fired** | 0/3 fired | worse (+1) |
| should-quiet-4 | should-quiet | **1/3 fired** | 0/3 fired | worse (+1) |
| should-quiet-5 | should-quiet | 0/3 fired | 0/3 fired | same |
| should-quiet-6 | should-quiet | 3/3 fired | 3/3 fired | same (expected residual) |
| should-quiet-7 (excluded) | should-quiet | 3/3 fired | 3/3 fired | same (descriptive) |
| **corrected quiet** | | **5/18** | 3/18 | worse (+2) |
| **catch** | | **15/15** | 15/15 | same |
| sealed literal | | 8/21 | 6/21 | worse (+2) |

---

## 5. Aggregation (exact fractions, no rounding)

Command (the PINNED surface):
`python3 plugins/vibe-check/scripts/score43.py aggregate --profile phase49 --runs-root docs/design/b3-ground-truth/runs-v2.11-phase49/first --label first --fp-bar 3 --sealed-fp-bar 6 --catch-bar 15 --catch-verdicts docs/design/b3-ground-truth/runs-v2.11-phase49/first/CATCH-VERDICTS.json --verdict-out docs/design/b3-ground-truth/runs-v2.11-phase49/first/VERDICT.json`
→ exit 0. Output line 1:
`first: MISS — quiet fired 5/18 (corrected cohort, bar <= 3; excluded: should-quiet-7); catch 15/15 (bar 15)`.

The generator's per-run fired flags equal §4 row for row. The 5 fired runs among the 18 counted are
should-quiet-3/run-1, should-quiet-4/run-2 and should-quiet-6/run-1, run-2 and run-3. The 3 fired
should-quiet-7 runs are counted separately. Its `catch_hit` (15) comes only from the 15-entry hand
map, which equals §3's verdict column (15 CATCH, 0 MISS).

**MISS**

- **Quiet arm (corrected, deciding):** quiet fired **5/18** against a bar of ≤ 3, so this arm
  misses. False alarms went **3→5 of 18 (corrected cohort, bar ≤ 3)**:
  - should-quiet-6 3/3 (the pre-registered residual);
  - should-quiet-3 1/3 (new);
  - should-quiet-4 1/3 (new);
  - should-quiet-1, -2, -5 each 0/3.
- **Catch arm (deciding):** catch **15/15** against a bar of 15, so this arm passes. Catches went
  **15→15 of 15 (bar 15)**. All five catch diffs held 3/3.
- The bar is a single AND, so the quiet arm alone decides **MISS**.

sealed literal (never deciding): quiet fired 8/21 vs the pre-registered ≤ 6/21 — would be MISS
(`sealed_literal.would_be: MISS`). The sealed bar text, from blob `633f1dd`: "v2.10 FP-rate on the
full grown set ≤ ½ × the SET-03 baseline FP-rate, AND catch-rate on the same diffs no worse than
baseline." The literal 6 was fixed by `RESULTS-v2.11.md` §"Phase-49 pre-registration" 2: "The
sealed-literal figure over all 21 quiet runs (should-quiet-7 included) is reported beside the
verdict against a pre-registered bar of ≤ 6, which is Phase 43's combined literal (6/21). It NEVER
decides the verdict".

should-quiet-7: fired 3/3 (excluded from the verdict and from retune eligibility; #001).

Dropouts: 0 on all 12 diffs (36/36 Codex `joined`).

| diff-id | role | fraction |
|---|---|---|
| triggarr-secret-in-logs | should-catch | 3/3 catch |
| triggarr-autoescape | should-catch | 3/3 catch |
| third-organic-should-catch | should-catch | 3/3 catch |
| triggarr-session-rotation | should-catch | 3/3 catch |
| triggarr-settings-form-split | should-catch | 3/3 catch |
| should-quiet-1 | should-quiet | 0/3 fired |
| should-quiet-2 | should-quiet | 0/3 fired |
| should-quiet-3 | should-quiet | **1/3 fired** |
| should-quiet-4 | should-quiet | **1/3 fired** |
| should-quiet-5 | should-quiet | 0/3 fired |
| should-quiet-6 | should-quiet | 3/3 fired |
| should-quiet-7 (excluded) | should-quiet | 3/3 fired |

Totals:

- Corrected quiet: **5/18**.
- Sealed-literal quiet: **8/21**.
- Catch: **15/15**.
- Verdict: **MISS**, carried by the quiet arm.

### Pre-registered expectations

| pre-registered expectation (`RESULTS-v2.11.md` §"Phase-49 pre-registration") | observed | held? |
|---|---|---|
| §5: should-quiet-6 fires 3/3 ("declared but never wired", 999.19), using the whole ≤ 3 budget | should-quiet-6 3/3 (codex-led rows at config.py L135/L139) | held |
| §5: zero headroom — one new false alarm anywhere else is a MISS | two new alarms: should-quiet-3/run-1 (language-python warning L259) and should-quiet-4/run-2 (security warning L93) | held as stated: MISS |
| §5: a regression would show up first among the nine diffs not retuned in Phase 43 | should-quiet-3 is one of those nine. should-quiet-4 was retuned in Phase 43, so the second alarm falls outside the predicted set | partly held |
| §1: catches 15 of 15 (keep every catch) | 15/15 | held |
| §2: sealed literal ≤ 6/21 (never deciding) | 8/21 | not held (disclosed; never decides) |
| §3 (D-04): on a miss, one targeted fix → S2, all 12 diffs × 3 re-run, scored as `retune-full` | MISS → 49-07 triggered | rule engaged |

### Borderline AXIS calls that could flip the verdict

None. The only borderline reading is the stricter "escaping is off now" reading on
triggarr-autoescape (§3.2 sensitivity). It would give catch 12/15. That reading is not the
pre-registered basis, and the verdict is MISS under both readings because the quiet arm (5/18 > 3)
already decides it.

### Mutation check (scratch, not committed)

Run in `…/scratchpad/p49-06-mut/` with scratch `--verdict-out` paths. Nothing here touched the
committed map or verdict.

| mutant | command | result |
|---|---|---|
| catch arm: first CATCH (sorted) flipped to MISS | `cp first/CATCH-VERDICTS.json p49-06-mut/`; flip `third-organic-should-catch/run-1`; `score43.py aggregate --profile phase49 --label first --fp-bar 3 --sealed-fp-bar 6 --catch-bar 15 --catch-verdicts p49-06-mut/CATCH-VERDICTS.json --verdict-out p49-06-mut/V-catch.json` | `first: MISS — quiet fired 5/18 (…); catch 14/15 (bar 15)`, rc 0; `catch_hit 14` (= 15 − 1), `verdict MISS` — PASS |
| catch arm, decisive control (the real verdict is already MISS, so the mutant above flips nothing by itself) | in-process `score43.PROFILES["phase49"]["fp_bar"] = 5`, `score43.run(["aggregate", … "--fp-bar", "5", …])` with the REAL map, then with the flipped map | real map: `verdict PASS catch_hit 15`; flipped map: `verdict MISS catch_hit 14`. The catch map alone flips the verdict — PASS |
| bar pin | `score43.py aggregate --profile phase49 --label first --fp-bar 2 --sealed-fp-bar 6 --catch-bar 15 … --verdict-out p49-06-mut/V-bar.json` | `bars must be --fp-bar 3 --sealed-fp-bar 6 --catch-bar 15`, rc 1, no verdict written — PASS |
| fp arm (quiet_fired 5 → bar 4) | in-process `score43.PROFILES["phase49"]["fp_bar"] = 4`; `score43.run(["aggregate", "--profile", "phase49", "--runs-root", <first>, "--label", "first", "--fp-bar", "4", "--sealed-fp-bar", "6", "--catch-bar", "15", "--catch-verdicts", <real map>, "--verdict-out", <scratch>])` | `rc 0 verdict MISS fp_bar 4 quiet_fired 5` — PASS |
| fp arm, decisive control | same call with `fp_bar` 5 (= quiet_fired) | `rc 0 verdict PASS fp_bar 5 quiet_fired 5`. The fp bar alone flips the verdict — PASS |

Neither bar is decorative. The catch map and the fp bar each decide the verdict on their own.

### FAILED-DIFFS (D-04) — committed in the same commit as VERDICT.json, before any retune edit

`python3 plugins/vibe-check/scripts/score43.py failed-diffs --runs-root docs/design/b3-ground-truth/runs-v2.11-phase49/first --out docs/design/b3-ground-truth/runs-v2.11-phase49/first/FAILED-DIFFS.json`
→ `excluded from retune eligibility: should-quiet-7` / `failed diffs: should-quiet-3, should-quiet-4, should-quiet-6`, exit 0.

`FAILED-DIFFS.json` = `["should-quiet-3", "should-quiet-4", "should-quiet-6"]`. Before committing,
a check confirmed that should-quiet-7 is absent. Under D-04 this list drives the 49-07 diagnosis
and the retune-gate consistency check. It is NOT the retune run set: if the owner applies the one
targeted fix, the retune re-runs all 12 diffs × 3 on S2, scored as `retune-full`.

---

## 6 Retune diagnosis

Written 2026-10-07 by 49-07 Task 1, after the first-pass verdict commit `14fded8` and before any
fix exists. Evidence is quoted by run id and `file:line` only, never lane text.

**Eligibility (D-04).** `git show HEAD:…/first/FAILED-DIFFS.json` parsed via `python3 -c` from
`plugins/vibe-check/scripts`: the list is `["should-quiet-3", "should-quiet-4", "should-quiet-6"]`,
non-empty, every entry is in `score43.DIFFS`, `should-quiet-7` is absent, and
`git log --format=%H -- …/first/FAILED-DIFFS.json` has exactly one commit
(`14fded8c863cbe3fd8b8d516831a722302b70d75`). All asserts passed.

**Method (Phase-42 confound order).** For each failed run, in order: (a) Codex focus text,
(b) the moved-control qualifier (`pending:` notes), (c) Codex dropouts, and only then (d) a v2.11
code path. Score arithmetic is reproduced from the unchanged formula
(`scripts/score.py` `compute_score` :1099-1150, `SEVERITY_WEIGHT` :41,
`AGENT_CONFIDENCE_OFFSET` :123, `_lone_lane_cap` :506, `band_for` :519; warning floor 80,
critical floor 95, lone-lane cap 94).

**v2.11 code paths, checked once for all three diffs (d).**
- `git diff main..e6eafbd -- plugins/vibe-check/scripts/score.py` adds the carried-finding
  machinery (`_snapshot_for`, `_kept_open_rows`, `_accept_verdict`) and does not touch
  `compute_score`, `SEVERITY_WEIGHT`, `AGENT_CONFIDENCE_OFFSET`, `_lone_lane_cap` or `band_for`.
- Every fired row has `status: new` in a single-pass state (`passes[-1].pass_number` = 1), so
  the Phase-46 kept-open / carried-finding path is not engaged.
- The Phase-47 fix-loop card path runs after scoring and writes no finding.
- The Phase-48 guard/gitsnap path snapshots git state and never edits findings.
- One v2.11 change does alter the lane set: the diff-mode coverage gate
  (`phases/deep-review/20-selection.md` GATE-01, `agents/index.md:31`) no longer dispatches
  `test-sufficiency` when no coverage artifact exists, so every v2.11 run here has one lane fewer
  than its Phase-43 counterpart. That cannot raise a row: `test-sufficiency` is a member of none
  of the fired rows, and Claude-to-Claude agreement earns no bonus (`score.py:1188-1208`), so
  removing a Claude lane can only remove members.
- Conclusion: no failed row is attributable to a v2.11 code path.

| failed run | lane that fired (lead) | row | (a) Codex | (b) moved-control | (c) dropout | arithmetic | implicated |
|---|---|---|---|---|---|---|---|
| should-quiet-3/run-1 | language-python | `src/roonseek/transfer.py:259` [warning, 82], category `optional-handling`, members bugs/impact/architecture/language-python | not implicated: `codex_findings=0` in all 3 runs | not implicated: the lead lane's row carries no `pending:` note; the lanes that do (bugs L212/L270, architecture L261, impact L212) stay sub-band | 0 | 70 + 20 (in diff) − 8 (medium) = 82 → warning by 2 points. Runs 2-3 of the same lane emit the same site at severity `low` (sub-band). Phase-43 first run-3 had the same site at confidence 60 → 72, medium | sampling variance in one lane's severity on an unchanged hypothetical-input class (an optional-default coalescing note), sitting 2 points over the warning floor. Lane prompt `agents/language-python.md` |
| should-quiet-4/run-2 | security (single member) | `triggarr/models/config.py:93` [warning, 94], category `ssrf` | not implicated: `codex_findings=0` in all 3 runs (the Phase-43 retune of the Codex helper-bypass class holds) | not engaged on the lead row: the security row carries no `pending:` note | 0 | 90 + 20 − 8 = 102 → lone-lane cap 94 → warning. Run 1: security emits L106 at `low`; run 3: security emits nothing. Phase-43 first + retune: the L91-L94 site was filtered `sub-threshold` in all 6 runs | the deferred backlog class 999.19 (b) "a stricter validator rejects a value a legacy config may hold, traced to a startup failure". `agents/security.md:87-95` deliberately reports that class at honest confidence, so this is a 1-in-3 sampling of a rule kept on purpose in Phases 42-43 |
| should-quiet-6/run-1 | codex-adversarial | `triggarr/models/config.py:135` [critical, 100], members codex + architecture | IMPLICATED: Codex is the lead in all 3 runs at confidence 0.99, severity medium (`codex-payload.json` `result.findings`, L135 / L139 / L139) | the Claude members do carry `pending:` notes (architecture L135/L139, bugs L139); the Claude-only group at L139 in run-1 is filtered `sub-threshold` | 0 | 99 + 20 − 8 + 10 (Codex + Claude corroboration) = 121 → 100, critical. Without corroboration Codex alone still scores 94 (lone-lane cap) → warning | the deferred backlog class 999.19 (a) "a new setting is declared but not yet read by runtime code". Codex focus text `templates/codex-focus.txt` carries no rule for this class |
| should-quiet-6/run-2 | codex-adversarial | `triggarr/models/config.py:139` [critical, 100], members codex + bugs×2 + impact | as run-1 | as run-1 | 0 | as run-1. The best Claude member (bugs, confidence 55, medium) would score 55 − 2 + 20 − 8 = 65 without Codex: below the medium floor | as run-1 |
| should-quiet-6/run-3 | codex-adversarial | `triggarr/models/config.py:139` [critical, 100], members codex + bugs×2 + impact | as run-1 | as run-1 | 0 | as run-2 (best Claude member: bugs confidence 40, low) | as run-1 |

**Fix candidates and the passing diffs that share their surface.** Any fix is measured on all
12 diffs × 3 on S2, so a fix's shared surface is what could regress.

1. **Codex focus text, class 999.19 (a) "declared but not yet wired"** (`templates/codex-focus.txt`).
   It would remove the should-quiet-6 residual, 3 of the 5 fired runs. Codex runs on every diff,
   so all 11 other diffs share this surface. The closest catch neighbour is
   triggarr-settings-form-split, whose AXIS is existing form fields that stop being submitted.
   The rule must cover only NEW settings no runtime code reads yet, never existing behaviour that
   stops working; triggarr-session-rotation and triggarr-autoescape are removal classes the rule
   must leave alone too.
2. **Security lane, class 999.19 (b) "stricter validator breaks a legacy config"**
   (`agents/security.md`; the same clause sits in the bugs/impact Safe-change block and in the
   Codex focus text). It would remove the should-quiet-4 single. It reverses a rule the
   Phase-42/43 design deliberately kept at honest confidence. Shared with should-quiet-1 and
   should-quiet-4's tightening axis and with every catch diff the security lane reviews.
3. **language-python lane, hypothetical-future-input class** (`agents/language-python.md`).
   It would remove the should-quiet-3 single. That lane ran on 9 of the 12 diffs in the first pass (every diff
   with Python), including triggarr-secret-in-logs, triggarr-autoescape and triggarr-session-rotation.

**Selected fix (exactly one, D-04): candidate 1, PROMPT class.** It is the only single change
that can bring the quiet arm under the bar on its own. With should-quiet-6 quiet, the observed
first-pass rows give 2/18 (the two singles) against a bar of 3. Candidates 2 and 3 each remove
one run at most and leave 4/18, so neither can pass alone. All three failed diffs are lane-prompt
behaviour unchanged by v2.11, so no CODE-class fix exists.

**Plain-language statement for the owner (Task 2).** The fix adds one sentence to the fixed
instruction Codex receives on every review: a change that adds a new setting which nothing reads
yet is staged work, not a defect, and should be left as a quiet note unless the change also
claims the setting is in effect. What a user would see: Codex stops raising a loud alarm on
half-finished "new option added, not hooked up yet" changes. The risk: a real "you added the
option but forgot to wire it" mistake would also become a quiet note, and in a review of your own
work that is sometimes exactly the bug you want flagged. The diffs it could affect: every diff,
because Codex reads the instruction on every review. The catch most at risk is
triggarr-settings-form-split (fields that stop being saved), which the rule must not cover.
