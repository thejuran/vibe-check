# B3 v2.10 Phase-43 scoring worksheet — first pass (36 runs, post-change system)

This is the scoring record for the v2.10 **post-change** measurement. It covers 12 sealed diffs × 3
runs on the fully changed plugin, which is frozen in snapshot S = `be6b0fcd9a4c2794dd3351ea054a65f3ab91e536`.
All runs used one pinned harness. Every aggregate below can be re-derived from three inputs:

- the committed `runs-v2.10-phase43/first/<id>/run-<n>/state.json`;
- the two committed answer-key BLOBs;
- the hand AXIS map `first/CATCH-VERDICTS.json`.

**Scored:** 2026-10-01.

**Scoring input:** `state.passes[-1].findings[]`, never a transcript. Findings are scored against the
committed answer-key BLOBs (D-00a). Carried rows score against the **v2.9 blob**
`ef0ab67cb45957167c99eff468077348432e1474`. New rows score against the **v2.10 blob**
`5f687d95f9be4fef2c0fcd78491c308d4c3861e8`. Bands are read from state with no recomputation (D-00a).
The SEAL2 denominators 15/21 are read from blob `633f1dd`.

**Mechanical tool:** `plugins/vibe-check/scripts/score43.py` (43-02, `4a5ee6c`). It produces the
`ledger`, `fp`, `catch-candidates`, `codex-status`, `aggregate` and `failed-diffs` outputs. The
AXIS calls are hand judgements recorded in §3. The tool never computes them.

**Verdict rule (D-00a2):** the verdict is decided on the CORRECTED cohort. should-quiet-7 is
excluded per `SUPERSESSIONS-v2.10.md` #001, which leaves 18 quiet runs with a bar of ≤ 8. The
catch bar is 15/15. The two arms combine as a single AND. The sealed-literal x/21 against ≤ 9/21
is printed beside the verdict and never decides it.

---

## 1. Integrity gate ladder (all hard gates PASS)

Every proof below is derived from git history and committed blobs, never trusted from a live
working file. Each command was run at scoring time with HEAD = `7f05aea8338afe75d91320c01ba167be6273a328`.

### (1) Seal verifier — ledger-004 hardened form + manifest derivation + sealed fields

Gate (1) executes the CURRENT verifier pin `de8633cb3e1a295208d89f5be7472e665aec7822`
(`SUPERSESSIONS-v2.10.md` entry 004). The superseded Phase-38 pin `a407539` appears below only as
the first of the two commits that ever touched the verifier path. It is never the blob executed.

| Check | Command | Result |
|---|---|---|
| (i) live verifier sha256 == pin | `shasum -a 256 docs/design/b3-ground-truth/verify-seal2-append.py` | `605e61a3deee6894ef4d30a1869d944d3685645749c601dacbefb81573d081a3` == pin — PASS |
| (ii) verifier-path commits (full-history, all refs) | `git log --format=%H --full-history --simplify-merges --topo-order --reverse --branches --tags --remotes -- docs/design/b3-ground-truth/verify-seal2-append.py` | exactly 2: `a407539115872137dc55d99aef439a9c5a4f16d9`, `de8633cb3e1a295208d89f5be7472e665aec7822`; the SECOND == pinned `verifier-commit` — PASS |
| (iii) manifest derivation (same full-history all-ref form) | `git log --format=%H --full-history --simplify-merges --topo-order --reverse --branches --tags --remotes -- docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md` | exactly 2: SEAL1 `4c67283b46540f997b8a5c6b530996da880b53ed`, SEAL2 `633f1dd0daa24b823d8abab7cff00823a3c2b256` — PASS |
| (iii) ancestry SEAL1 → SEAL2 | `git merge-base --is-ancestor 4c67283 633f1dd` | exit 0 — PASS |
| (iii) ancestry SEAL1 → HEAD | `git merge-base --is-ancestor 4c67283 HEAD` | exit 0 — PASS |
| (iii) ancestry SEAL2 → HEAD | `git merge-base --is-ancestor 633f1dd HEAD` | exit 0 — PASS |
| (iii) manifest commits carry no runs content | `git show --name-only --format= <SEAL1\|SEAL2>` | each lists only `docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md` — PASS |
| (iv) execute the pinned blob | `git show de8633cb3e1a295208d89f5be7472e665aec7822:docs/design/b3-ground-truth/verify-seal2-append.py \| python3 - <repo>` | `SEAL2-APPEND-WHITELIST-OK`, exit 0 — PASS |

Why the pin moved, per entry 004: the old `rev-list HEAD` derivation passes two kinds of manifest
edit. One is an unmerged side-branch edit; the other is a `-s ours` merge. The full-history all-ref
form counts both, and the three ancestry asserts bind the seal pair to the tree being scored.

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
| (i) one S in every fingerprint | `git show HEAD:…/RUN-METHOD-NOTES-phase43.md \| grep '^batch-sha:' \| sort \| uniq -c` | `12 batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536`, across 12 `## Harness fingerprint — ` blocks — PASS |
| (ii) Phase-42 last commit → S | `git merge-base --is-ancestor cede608 be6b0fcd` | exit 0 — PASS |
| (ii) 41-08 `state_shape` fix → S | `git merge-base --is-ancestor 180e0e3 be6b0fcd` | exit 0 — PASS |
| (ii) 43-01 launch-gate fix → S | `git merge-base --is-ancestor 8ae33da be6b0fcd` | exit 0 — PASS |
| (iii) S → every run commit in RUNS-COMPLETE.json | `git merge-base --is-ancestor S <rc>` × 36 | 36/36 exit 0 — PASS |
| (iii) fingerprint committer time < pass timestamp | `git log -1 --format=%cI <FPC>` vs `passes[-1].timestamp` × 36 | 36/36 strictly earlier — PASS |
| (iv) transcript sha binding | `shasum -a 256 transcript.jsonl` vs committed `transcript.jsonl.sha256` × 36 | 36/36 match; local transcript present for all 36, so there are 0 "sha only" rows — PASS |
| (iv) post-block provenance re-asserted | `grep -qE '(turingmind-code-review/plugins/vibe-check\|plugins/cache/thejuran/vibe-check)' transcript.jsonl` × 36; `grep -qF <snapshot root>` × 36 | BAD regex hits: 0; transcripts naming the snapshot root: 36 — PASS |
| (v) parity record in the notes blob | `git show HEAD:…/RUN-METHOD-NOTES-phase43.md \| grep '^parity:'` | `parity: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536 forward=106/106 reverse=0 extra at 2026-09-30T21:26:45-0400` and `parity: restored released 2.9.0 at 2026-10-01T03:36:31-0400` — PASS |

S itself is `be6b0fcd9a4c2794dd3351ea054a65f3ab91e536` (committer time 2026-09-30T21:11:24-04:00,
`docs(43-03): RUN-PHASE43-v2.10.md — parameterized 36-run runbook`).

Fingerprint blocks, in session order:

| session ID (SID) | introducing commit (FPC) | `batch-sha:` | runs governed |
|---|---|---|---|
| 2026-09-30T21:27:39-0400 | `3717245` | S | triggarr-secret-in-logs 1-3 |
| 2026-09-30T22:12:29-0400 | `0379a6a` | S | triggarr-autoescape 1-3 |
| 2026-09-30T22:49:28-0400 | `27ddd6d` | S | third-organic-should-catch 1-3 |
| 2026-09-30T23:18:05-0400 | `37f0c79` | S | should-quiet-1 1-3 |
| 2026-09-30T23:44:27-0400 | `089dd2e` | S | should-quiet-2 1-3 |
| 2026-10-01T00:05:02-0400 | `2788d36` | S | should-quiet-3 1-3 |
| 2026-10-01T00:32:00-0400 | `2fbb4de` | S | triggarr-session-rotation 1-3 |
| 2026-10-01T01:06:01-0400 | `80f1b87` | S | triggarr-settings-form-split 1-3 |
| 2026-10-01T01:42:04-0400 | `46697e8` | S | should-quiet-4 1-3 |
| 2026-10-01T02:15:14-0400 | `8f30bff` | S | should-quiet-5 1-3 |
| 2026-10-01T02:36:10-0400 | `510ecfc` | S | should-quiet-6 1-3 |
| 2026-10-01T03:03:58-0400 | `366141a` | S | should-quiet-7 1-3 |

### (3) Dual digest gate (run TWICE) + ancestry

| Check | Command | Result |
|---|---|---|
| v2.9 key blob, pass 1 / pass 2 | `git show ef0ab67:docs/design/b3-ground-truth/ANSWER-KEY-b3.md \| shasum -a 256` | `1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1` both passes == SEAL1 `ANSWER_KEY_SHA256` — PASS |
| v2.10 key blob, pass 1 / pass 2 | `git show 5f687d9:docs/design/b3-ground-truth/ANSWER-KEY-v2.10.md \| shasum -a 256` | `f58f888c9f4dc86d0e34d5a152c781cb7e9913087405e6e25980bd77e3d753d4` both passes == SEAL2 `NEW_ANSWER_KEY_SHA256` — PASS |
| ancestry | `git merge-base --is-ancestor ef0ab67 HEAD`; `… 5f687d9 HEAD` | exit 0; exit 0 — PASS |

### (4) Score-from-blob materialization

| Check | Command | Result |
|---|---|---|
| materialize both keys to scratch | `git show ef0ab67:…/ANSWER-KEY-b3.md > answer-key-b3-scored.md`; `git show 5f687d9:…/ANSWER-KEY-v2.10.md > answer-key-v2.10-scored.md` | 150 lines; 136 lines |
| re-digest the materialized files | `shasum -a 256 answer-key-*-scored.md` | `1463…3fca1`; `f58f…53d4` == sealed — PASS |
| (4d) live-file sanity (warning-only) | `cmp` live key / live manifest vs blob | live `ANSWER-KEY-b3.md`, `ANSWER-KEY-v2.10.md` and the live manifest are byte-identical to their blobs — PASS (no drift) |

Every SITE/AXIS/BAND rule and every `base_sha` in §3/§4 was read from these materialized blobs.

### (5) Layout — 36 run dirs, fixed file set, no siblings, `state_shape`

| Check | Command | Result |
|---|---|---|
| runs tree committed clean | `git status --porcelain -- runs-v2.10-phase43/first/`; `… RUN-METHOD-NOTES-phase43.md` | empty; empty — PASS |
| run dirs | `ls -d first/*/run-[123] \| wc -l` | 36 — PASS |
| voided / failed siblings | `ls first/<diff>/ \| grep -vE '^run-[123]$'` over all 12 diffs | none (no `run-N.voided-*`, no `run-N.failed-*`); nothing to exclude by name — PASS |
| tracked file set per run | `git ls-files first/` grouped by run dir | 36 runs × the same 11 files: `clear.txt codex-payload.json codex-rc.txt context.txt lanes.json report.md session.txt state.json transcript.jsonl.sha256 tree.diff tree.diff.sha256` (Codex variant = payload + rc in all 36; no `codex-absent.txt`); `transcript.jsonl` is local and untracked — PASS |
| `clear.txt` attestation | full-line `^<ISO±ZZZZ> CLEARED$` × 36 | 36/36 — PASS |
| `state_shape --schema future` | `python3 plugins/vibe-check/scripts/state_shape.py <state.json> --schema future` × 36 | PASS=36, rc 0 on every state (the tool prints nothing on success) — PASS |

### (6a) Sidecar seal gate — run BEFORE any sidecar value is consumed

| Check | Command | Result |
|---|---|---|
| carried six blob-equal to v2.9 | `git rev-parse HEAD:<p>` == `git rev-parse v2.9:<p>` == `git hash-object <p>` for each `.patch` + `.provenance` | 12/12 equal (e.g. secret-in-logs `.patch` `890a1f2aa71e`, `.provenance` `2ff170be452c`) — PASS |
| new six sha256 == `5f687d9` key lines | sha256 of the HEAD blob AND of the live file vs `sha256(diffs/<f>) = …` in the materialized key | 12/12 equal (e.g. session-rotation `.patch` `31bad85408ca…`, settings-form-split `.patch` `40ae123ce991…`) — PASS |

### (6b) Per-run isolation (after 6a)

| Check | Command | Result |
|---|---|---|
| `len(passes) == 1` | `state.json` | 36/36 — PASS |
| `passes[-1].head_sha == base_sha` (sidecar) | `base_sha:` line of the sealed sidecar | 36/36 — PASS |
| tree.diff triple | `sha256(tree.diff)` == `tree.diff.sha256` == sidecar `EXPECTED_TREE_DIFF_SHA256` | 36/36 — PASS |

Per-diff grid: see §2.

### (8) Security / privacy spot-check (before any bulk scoring)

| Check | Command | Result |
|---|---|---|
| lane + Codex archive privacy scan | `python3 plugins/vibe-check/scripts/lanearchive.py scan first/*/run-[123]/lanes.json first/*/run-[123]/codex-payload.json` | `privacy scan clean: 72 file(s)`, exit 0 — PASS |
| secret-shaped literal grep (the SCORING-v2.10 set, extended) | `grep -lE '(sk-ant-…\|sk-[A-Za-z0-9]{32,}\|ghp_…\|github_pat_…\|AKIA[0-9A-Z]{16}\|xox[baprs]-…\|Bearer <20+>\|-----BEGIN … PRIVATE KEY\|api_key=<16+ literal>\|maguffynas)'` over `state.json`, `lanes.json`, `codex-payload.json`, `report.md` × 36 | 0 files with a hit in each of the four file kinds — PASS |

No scrub was needed. This worksheet quotes titles only at a catch SITE (§3) and quotes finding rows
(agent/file/line/band/score/stable_hash) elsewhere (T-43-27).

### (9) Harness evidence — commit-anchored, pin-matched, pre-run-ordered

| Check | Command | Result |
|---|---|---|
| pins (committed notes blob) | `git show HEAD:…/RUN-METHOD-NOTES-phase43.md \| grep '^pin-'` | `pin-claude-code: 2.1.281 (Claude Code)` · `pin-codex: codex-cli 0.153.4` · `pin-model: fable 5.1` · `pin-codex-companion: 1.0.4` · `pin-context-window: 1M` — PASS |
| pin commit precedes every fingerprint | `git log -G'^pin-' -- <notes>`; `git merge-base --is-ancestor 2b2c62b 3717245` | one pin commit `2b2c62b` (2026-09-30T20:54:40-04:00); ancestor of the first FPC — PASS |
| fingerprint fields (12 blocks) | parse the anchored `^## Harness fingerprint — <ISO>$` blocks | `claude-code: 2.1.281 (Claude Code)` 12/12 · `model: Fable 5.1` 12/12 (normalizes to EXACT `fable 5.1`, entry 003) · `context-window: 1M` 12/12 · `codex: codex-cli 0.153.4` 12/12 · `codex-companion: 1.0.4` 12/12 · `driver: assistant-tmux` 12/12 · `autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)` 12/12 · `plugin-root: …/batch5-be6b0fcd9a4c/plugins/vibe-check` 12/12; 0 duplicate SIDs — PASS |
| per-run session binding | for each run: `session.txt` = SID + FPC; FPC touches only the notes file; SID block present at FPC and absent at FPC^; field lines at FPC == field lines at HEAD; FPC ≠ RC and `merge-base --is-ancestor FPC RC`; `session: first <diff>` matches the run's diff | 36/36 — PASS |
| attestation precedes the review | `clear.txt` time < `passes[-1].timestamp` | 36/36 — PASS |

**Ladder result: gates (1)–(9) all PASS. Scoring authorized.**

---

## 2. Scoreable-completeness ledger (NO AGGREGATION OVER HOLES)

`python3 plugins/vibe-check/scripts/score43.py ledger --runs-root docs/design/b3-ground-truth/runs-v2.10-phase43/first`
→ `ledger complete: 12 diffs x 3, no holes, no extras`, exit 0.

The diff universe is the committed inventory: the 12 `diffs/*.provenance` sidecars, which also form
`RUNS-COMPLETE.json` `expected_diffs`. The ledger is asserted against that inventory by set
equality. Run commits below are from `RUNS-COMPLETE.json` (`aa14430`), and every one passed gates
(2)(iii) and (6b).

| diff-id | role | run-1 commit | run-2 commit | run-3 commit | scoreable |
|---|---|---|---|---|---|
| triggarr-secret-in-logs | should-catch | `9bccdba45e513fc61ee9edd6b00b290cecb12a7d` | `14a46f71489552bc442ad74ee176308dbc3555c3` | `28a402bf737f00b758fa2149a08d94855c0ba891` | **3/3** |
| triggarr-autoescape | should-catch | `ef86437a1a37f938c5aacca9242b7cb7795732db` | `77d1697f0464d96644845941704957d1e889f24e` | `58798145b8a2bef45098bbeee0d099031dd7e9a1` | **3/3** |
| third-organic-should-catch | should-catch | `fc9e2cf1ec5dafd3adf1f2efef6294b7454d209e` | `deba0295cd4f8c7a55d65ab348a7ef77142c9222` | `a8ef1749c73a7e1f619127ab83d207c3b77346ca` | **3/3** |
| should-quiet-1 | should-quiet | `6de81cda786c6b9b0787ce43a86a1049aff5f3fa` | `3ac94c3d7d997071f0b58e9801f7a0e5b96c6051` | `52638a1854e6fb184f136d85c079cab28d20d380` | **3/3** |
| should-quiet-2 | should-quiet | `c3aafdd4e1fe723d040bf903631d2c1c85bebb9b` | `e68f7b1cb42496c06f68f3580c76fe27a9c4eac9` | `2ed4e1109f71ee2d2a3d7ea43b9d08b7701d94fd` | **3/3** |
| should-quiet-3 | should-quiet | `12fc35b2cc2ad3951780d0d52c3ed08e434b3310` | `b3330b97212b755c8e72a4dd083f5f5173dd8eb0` | `255d0b38bee69a3f00bde2704a144b824ba520e1` | **3/3** |
| triggarr-session-rotation | should-catch | `7062d39d0c3db87ad0e1db9ed9cd9fedf077f884` | `072be721edace2e06a447fbd98388b87baa715bd` | `825bd495464954fbb0e382813146c0ea1d88e74b` | **3/3** |
| triggarr-settings-form-split | should-catch | `0f3bea5cd56365c440c24c5b5efa62c9f4788a85` | `6010fc9ddcd87ffa5fcb033b55c61bed0e347197` | `a6f6a110c30dff9ef5c557780e20d121d348b7c6` | **3/3** |
| should-quiet-4 | should-quiet | `5e8990c998d84f0aeebd00e16964ad3f1e6a20e7` | `3184820cb76d11e07765d3b7a4a1878145b48c6b` | `48dbdab16df6609a5413bddddc6f452eb471a2d8` | **3/3** |
| should-quiet-5 | should-quiet | `483c38216901edbadc8cc831b5e71599c40de205` | `fd12451d3f7239e75b112f0647fad12fcff327b6` | `37e8dabb0c8bdeba5fdb079c67ce5f2973bde3e6` | **3/3** |
| should-quiet-6 | should-quiet | `a7b8284fc0f5b6fc231ec880a624beeef52ad057` | `b456b6e19632f2947f2aea17b097e38c3cbf3ed9` | `02672ee8939908bfd3445393a708a1e6249ab79a` | **3/3** |
| should-quiet-7 | should-quiet | `7e69408e340996b6473be216e0ddcc4ca71fc97e` | `38ffe0831231ac7b8aeabfcffb9199b59e2ae307` | `e93bf552f2c85a6e77d6541bff66608b7290a91e` | **3/3** |

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

### Lane-set irregularities flagged by 43-04, and their effect on scoring

Scoring reads only `state.passes[-1].findings[]`. `lanes.json` is evidence for confound audits,
not a scoring input. Each irregularity was checked against the scored cell it could touch:

| run | irregularity (from `lanes.json`) | cause seen in the archive | effect on the scored cell |
|---|---|---|---|
| should-quiet-2/run-3 | 7 lanes dispatched vs 8 (no `framework-angular`) | the triage lane returned `frameworks: []` (run-1 returned `["angular"]`) | none. The run is QUIET (0 critical/warning rows). Runs 1 and 2 dispatched the framework lane and are also QUIET. The archive cannot prove run-3 would have stayed quiet with the lane; recorded as a fact. |
| triggarr-session-rotation/run-3 | 8 lanes vs 9 (no `framework-fastapi`) | triage returned `frameworks: []` | none. The run is a CATCH on rows from other lanes (§3.4). |
| should-quiet-7/run-1, run-2 | 8 lanes vs 9 in run-3 (framework lane only in run-3) | triage returned `frameworks: []` in run-1 and run-2 | none on the verdict. The diff is excluded (#001), and all three runs fire on codex/bugs rows either way. |
| triggarr-autoescape/run-3 | `codex_lines=2`: the Codex lane was captured twice | the archive recorded both the whole-payload return and the translated single finding | none. The state holds one codex-led surviving row (`codex_findings=1`); this duplication exists only in the archive. The run is a CATCH (§3.2). |
| triggarr-settings-form-split/run-3 | 2 lanes with `parsed=None` (triage, security returned prose) | prose returns; `malformed=0, recovered=7, unrecovered=[]` | none. The run is a CATCH on bugs/architecture/impact/codex rows. The security lane's prose mentions one behavioral regression that did not reach state as a security row. Its sibling runs' security lanes returned 0 findings, so no sibling scored cell depends on a security row either. |

Triage occasionally returns an empty `frameworks` list. That is an orchestration-nondeterminism
fact for 43-07; no scored cell in this pass moves because of it.

---

## 3. Per-run scoring — should-catch diffs (D-07 three-gate rule + ledger 007)

A **catch** requires all three gates:

- **SITE:** the right file, within the planted hunk, keyed to the row's `base_sha`. For
  session-rotation, SITE is judged in run-tree coordinates (entry 002).
- **AXIS:** the finding names the key's required MECHANISM and honors the row's NOT-clause.
- **BAND:** the rendered band is ≥ the row's floor.

SITE-only, or SITE+AXIS below band, is `detected-below-threshold`, which counts as a MISS.

**AXIS basis.** The sealed key gates AXIS on the finding's `title`, with `category` only as
corroboration (`ef0ab67` key lines 31-32). Entry 007 extends this: from H-LANE runs on, AXIS is met
when the surviving row's OWN title OR ANY `members[].title` names the mechanism. SITE and BAND are
still judged on the surviving row. `filtered[]` and the raw lane envelopes are not scoring input
(entry 008, item 4). Problem text is quoted below only where it bears on a borderline call. It is
never the basis of a call.

**Order of work (T-43-25).** The hand AXIS map was written to scratch at 2026-10-01T07:45:31Z,
before `RESULTS-v2.10.md` was opened. `SCORING-v2.10.md`, which holds the Phase-38 worksheet rows,
was read beforehand as this file's mandated template. `REPLAY-CATCH-MANIFEST-v2.10.json` was read
for its `_rules.axis_basis` and its recorded deciding phrases on the autoescape diff, which are the
precedents for the title-only basis. The autoescape axis calls below follow those recorded phrases.

The candidate tables are verbatim `score43.py catch-candidates` output: rows at SITE with band ≥
floor. The `AXIS` column of that output is blank by design, and the hand call is in the run table
beneath it. The Codex column is from `score43.py codex-status`.

### 3.1 triggarr-secret-in-logs (carried → `ef0ab67`) — SITE `triggarr/clients/base.py` : 230-238 / 249-256 · AXIS = Secret/PII (API key) leaked into logs (NOT "log formatting inconsistency") · BAND floor = warning

Candidates (run-1 / run-2 / run-3) — survivor rows at SITE ≥ warning:

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | codex-adversarial | 232 | critical | 100 | 13f543dd935e | Full HTTP exceptions leak URL credentials into logs | bugs: "full request URL (including any userinfo) reaches logs and web-UI log buffer" |
| 1 | compliance | 252 | warning | 94 | af2794b67712 | Raw pydantic ValidationError logged, bypassing established exception-sanitization pattern | bugs: "logs raw response input values into logs and the web UI" |
| 2 | codex-adversarial | 233 | critical | 100 | 12fe298fc07e | Raw HTTP exceptions leak reverse-proxy credentials | compliance: "reintroduces API key leak risk"; security: "reintroduces API key / internal-URL leakage into logs" |
| 2 | compliance | 251 | warning | 94 | b76221829580 | Logging full pydantic ValidationError reintroduces leak risk fixed by d47b4c2 | — |
| 3 | codex-adversarial | 233 | critical | 100 | 5718c2673139 | Raw HTTP exceptions leak URL credentials | security: "Re-introduces raw exception logging previously fixed as a key-leakage risk" |
| 3 | compliance | 252 | warning | 94 | 17ab47c4de4d | Logging raw pydantic ValidationError can dump the entire upstream API response body | — |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L232 [critical, 100] "Full HTTP exceptions leak URL credentials into logs" | ✓ | ✓ the title names a credential leak into logs, which is the key's mechanism and not formatting | ✓ critical | CATCH | joined |
| run-2 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L233 [critical, 100] "Raw HTTP exceptions leak reverse-proxy credentials" (+ compliance member "reintroduces API key leak risk") | ✓ | ✓ the titles name the credential/API-key leak | ✓ critical | CATCH | joined |
| run-3 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L233 [critical, 100] "Raw HTTP exceptions leak URL credentials" (+ security member "…key-leakage risk") | ✓ | ✓ the title names the credential leak | ✓ critical | CATCH | joined |

**Per-diff: 3/3 catch.** Codex dropouts: 0.

### 3.2 triggarr-autoescape (carried → `ef0ab67`) — SITE `triggarr/web/routes.py` : 42-48 (bug line 45) · AXIS = XSS surface re-enabled / autoescape not in effect — "The finding must name the escaping/XSS consequence (autoescape not in effect / XSS), not merely 'refactor reverted' or 'unused import'" · BAND floor = warning

Sealed AXIS text, quoted from the `ef0ab67` blob: "**XSS surface re-enabled by losing the
preconfigured autoescape `jinja2.Environment`** — on current Starlette,
`Jinja2Templates(directory=..., autoescape=True)` silently NO-OPs autoescape … so template
auto-escaping is OFF. The finding must name the escaping/XSS consequence (autoescape not in effect /
XSS), not merely "refactor reverted" or "unused import"."

Precedents in `REPLAY-CATCH-MANIFEST-v2.10.json`, title-only:

- **axis=true:** "risking silent XSS on future Starlette upgrade"; "forward-compat XSS regression";
  "autoescape silently drops on Starlette upgrade"; "re-arms the autoescape break".
- **axis=false:** "Reverts autoescape fix onto Starlette's deprecated env_options path"
  ("revert/deprecation, not escaping-off/XSS"); "…pattern that commit introduced to keep autoescape
  reliably enabled" ("describes the revert, not escaping-off/XSS"); "Reverts deliberate autoescape
  hardening…".

Each run has ONE surviving row at SITE; every lane collapsed into it (H-LANE). All of each row's
member titles are listed:

| run | agent | line | band | score | stable_hash | survivor title | member titles (agent · category) |
|---|---|---|---|---|---|---|---|
| 1 | compliance | 45 | warning | 94 | 52c0faec4e3b | Reverts prior fix that guaranteed Jinja2 autoescaping, restoring deprecated env_options path | compliance·rule-violation (same); architecture·dependency "Reverts to Jinja2Templates env-options kwarg form that installed starlette 0.52.1 explicitly deprecates"; framework-fastapi "Reverts prior fix, reintroducing deprecated Jinja2Templates env_options bridge"; security·xss "Revert of deliberate autoescape fix reintroduces dependency on deprecated Starlette passthrough"; bugs "Diff undoes fix e11187e by going back to Starlette's deprecated Jinja2Templates(**env_options) path"; impact·breaking-api "Reverts the e11187e fix: deprecated Jinja2Templates(**env_options) path, with an unpinned Starlette in the Docker build"; impact·blast-radius "Autoescape now depends on deprecated, version-dependent Starlette behavior instead of explicit Environment construction" |
| 2 | codex-adversarial | 45 | critical | 100 | 4f30f8fb283f | Preserve the constructor supported by Starlette 1.x | architecture "Reverts e11187e to Starlette's deprecated **env_options path; fails at import on newer Starlette"; compliance "Diff reverts the documented autoescape fix from commit e11187e without stated justification"; impact "…so the app can fail to start when Starlette is upgraded"; impact "Explicit autoescape kwarg now sends a DeprecationWarning on every import, including in tests"; bugs "Reverts to deprecated Jinja2Templates **env_options path (DeprecationWarning at import; future removal breaks module import)"; framework-fastapi "Jinja2Templates reverted to deprecated env_options passthrough for autoescape"; security·xss "Autoescape reconfigured via deprecated Jinja2Templates env_options kwarg" |
| 3 | codex-adversarial | 45 | critical | 100 | 819009c3e634 | Preserve the constructor supported by production dependencies | framework-fastapi "Diff reverts the prior fix for Jinja2Templates autoescape deprecation"; architecture "…goes back to the deprecated Jinja2Templates env_options call"; **security·xss "Revert of deliberate autoescape fix reintroduces version-fragile XSS protection"**; bugs "…passes autoescape through Jinja2Templates' deprecated **env_options"; compliance "Reverts documented autoescape fix, reintroducing deprecated passthrough"; impact "…the unpinned Docker install can crash the app when it starts"; language-python "Reverts prior fix commit back to deprecated Jinja2Templates(autoescape=) kwarg form"; impact "Autoescape now depends on Starlette's deprecated passthrough and default instead of an explicit Environment" |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=e11187e ✓ | ✓ | `compliance` L45 [warning, 94] "Reverts prior fix that guaranteed Jinja2 autoescaping, restoring deprecated env_options path" | ✓ | ✗ **axis-not-named.** No survivor or member title names escaping-off or XSS. The survivor title is a revert-plus-deprecation framing, the same class as the recorded axis=false phrase "keep autoescape reliably enabled". The security member (category `xss`) titles a "dependency on deprecated Starlette passthrough", which is deprecation; category only corroborates and cannot supply the mechanism. The impact member "Autoescape now depends on deprecated, version-dependent Starlette behavior" names a dependency, not that escaping is off. This is the borderline call; see the sensitivity note. | ✓ warning | MISS | joined (Codex verdict `approve`, 0 findings) |
| run-2 | len=1,head=e11187e ✓ | ✓ | `codex-adversarial` L45 [critical, 100] "Preserve the constructor supported by Starlette 1.x" | ✓ | ✗ **axis-not-named.** Every title is startup, deprecation or revert framing: "fails at import", "can fail to start", "DeprecationWarning", "reverts … without stated justification", "Autoescape reconfigured via deprecated … kwarg". None names escaping-off or XSS. The survivor's own problem text in state (Codex) describes a TypeError at import and is silent on escaping. | ✓ critical | MISS | joined |
| run-3 | len=1,head=e11187e ✓ | ✓ | `codex-adversarial` L45 [critical, 100]; AXIS carried by member `security` (category `xss`) "Revert of deliberate autoescape fix reintroduces version-fragile XSS protection" | ✓ | ✓ The member title names the XSS consequence of losing the guaranteed escaper (XSS protection made version-fragile). This is the same class as the recorded axis=true "risking silent XSS on future Starlette upgrade", and category `xss` corroborates. | ✓ critical | CATCH | joined |

**Per-diff: 1/3 catch** (runs 1 and 2 are `detected-below-threshold`: right site, right band,
axis not named). Codex dropouts: 0.

**Sensitivity of the run-1 call.** Two readings would credit run-1:

- the problem-text reading Phase 38 used for this diff (the state survivor's problem says a
  future upgrade "would silently disable autoescaping project-wide");
- a looser reading of "version-dependent" as naming the escaping consequence.

Under either reading the arm becomes 14/15. Run-2 is a MISS under EVERY basis: titles, members,
category, and the state survivor's problem text. 14/15 is still below the 15/15 bar, so **the
overall verdict does not depend on the run-1 call.**

**Fact recorded for 43-07 (not an excuse):** in all three runs the reviewing lanes ran the locked
dependency themselves. The bugs (run-3), security (all runs) and impact (runs 1 and 3) lanes'
agent notes record that Starlette 0.52.1 from `uv.lock` still forwards `autoescape=True`
(`env.autoescape == True`, rendering verified). They framed the risk as crash-on-upgrade or
version fragility. Codex run-1 returned `approve` with the summary "HTML autoescaping remains
enabled and verified". The sealed AXIS premise is that on current Starlette the call "silently
NO-OPs autoescape". The reviewers' empirical reading of the base tree's own lockfile differs from
that premise. The sealed key is not reopened; the verdict stands as scored.

### 3.3 third-organic-should-catch (carried → `ef0ab67`) — SITE `src/angular/src/app/services/files/view-file.service.ts` : 304-311 · AXIS = Unclamped percentage — no upper bound, >100% / missing clamp (not generic style) · BAND floor = medium

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | bugs | 308 | critical | 100 | 2d7c24c10089 | Removed clamp brings back percent values above 100% for extracted files (e.g. "199%") | impact: "Removing the Math.min(100, ...) clamp brings back progress values over 100%"; language-typescript: "reintroduces the >100% progress bug" |
| 2 | codex-adversarial | 307 | critical | 100 | 5264c4e05c7d | Restore the download percentage upper bound | impact: "Removing the Math.min(100, ...) clamp brings back over-100% progress"; bugs: "brings back progress values above 100%" |
| 3 | bugs | 308 | critical | 100 | 390c8de37fb9 | Removing the 100% clamp lets extracted files show more than 100% progress and break completion checks | impact: "brings back the >100% progress bug" |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=3db8b48 ✓ | ✓ | `bugs` L308 [critical, 100] "Removed clamp brings back percent values above 100%…" | ✓ | ✓ names the missing clamp / >100% | ✓ critical ≥ medium | CATCH | joined |
| run-2 | len=1,head=3db8b48 ✓ | ✓ | `codex-adversarial` L307 [critical, 100] "Restore the download percentage upper bound" (+ impact/bugs members ">100%") | ✓ | ✓ names the missing upper bound / >100% | ✓ critical | CATCH | joined |
| run-3 | len=1,head=3db8b48 ✓ | ✓ | `bugs` L308 [critical, 100] "Removing the 100% clamp lets extracted files show more than 100% progress…" | ✓ | ✓ names the missing clamp / >100% and the broken completion check | ✓ critical | CATCH | joined |

**Per-diff: 3/3 catch.** Codex dropouts: 0.

### 3.4 triggarr-session-rotation (new → `5f687d9`) — SITE `triggarr/web/routes.py` : 1445-1451 / 1459-1469 (patch coordinates; run-tree 1564-1588 per entry 002) · AXIS = Stale-session survival — password change no longer evicts existing sessions (NOT dead-code cleanup, NOT logging removed, NOT a response-refactor or cookie-attribute nit) · BAND floor = warning

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | codex-adversarial | 1567 | critical | 100 | 60f5b7b1f55d | Restore session revocation on password change | bugs: "sessions from before the change stay valid"; impact: "Changing your password no longer logs out other sessions"; security: "Password change no longer invalidates existing sessions" |
| 1 | architecture | 1581 | warning | 94 | 3a3adde66492 | Diff removes behavior that four existing tests require, so the suite will fail | — |
| 2 | bugs | 1567 | critical | 100 | 33941c3025c2 | Password change no longer rotates session_secret, so existing sessions stay valid | impact: "stolen or stale session cookies stay valid"; security: "no longer invalidates other sessions" |
| 3 | compliance | 1567 | critical | 100 | 91ff52630953 | change_password drops session-secret rotation, breaking the codebase's own established convention for this exact problem | bugs: "sessions on other devices stay valid"; security: "compromised/stolen sessions survive a password change"; impact: "no longer revokes existing sessions; stolen cookies stay valid for up to 30 days" |
| 3 | impact | 1581 | warning | 85 | 90eb761f16d7 | Diff breaks four existing tests that assert session rotation on password change | — |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L1567 [critical, 100] "Restore session revocation on password change" | ✓ (run-tree, entry 002) | ✓ names session revocation lost / old sessions stay valid | ✓ critical | CATCH | joined |
| run-2 | len=1,head=f4366a2 ✓ | ✓ | `bugs` L1567 [critical, 100] "Password change no longer rotates session_secret, so existing sessions stay valid" | ✓ | ✓ names old sessions surviving | ✓ critical | CATCH | joined |
| run-3 | len=1,head=f4366a2 ✓ | ✓ | `compliance` L1567 [critical, 100] (convention framing); AXIS carried by members, e.g. security "compromised/stolen sessions survive a password change" | ✓ | ✓ via members (entry 007); the lead title is a convention framing, but several members name session survival | ✓ critical | CATCH | joined |

**Per-diff: 3/3 catch.** Codex dropouts: 0. (Run-3 is the run in which the measured review's
compliance agent ran `git stash pop` in `~/triggarr`, per the 43-04 anomaly. Its post checks
passed, and it is scored as recorded.)

### 3.5 triggarr-settings-form-split (new → `5f687d9`) — SITE `triggarr/templates/settings.html` : 15-28 / 33-81 / 87-93 / 131-137 · AXIS = Silent data loss on save — General fields no longer submitted (NOT HTML restructuring, NOT duplicate form action, NOT a styling/a11y nit) · BAND floor = warning

| run | agent | line | band | score | stable_hash | survivor title | axis-relevant member titles |
|---|---|---|---|---|---|---|---|
| 1 | impact | 18 | critical | 100 | 13e74508c127 | New General-section form has no submit control, so its fields can never be submitted on their own | architecture: "Save Settings drops the General fields"; bugs: "they can never be saved" |
| 1 | bugs | 134 | warning | 94 | bc32cf1a9e88 | Save Settings resets every General setting to its hardcoded default | — |
| 2 | architecture | 18 | critical | 100 | 809b1490ed8c | Diff reverts commit 542d5dd and puts General settings back in a form with no submit button | bugs: "General fields can't be saved"; impact: "every Save Settings click resets them to handler defaults" |
| 2 | bugs | 134 | warning | 94 | f99226a665be | Each Save Settings click resets every General setting to its default | — |
| 2 | bugs | 25 | warning | 94 | 8f9b2cc744da | The regression test for the 542d5dd fix will now fail | — |
| 3 | bugs | 134 | warning | 94 | 755ed8f190dd | Saving Settings resets every General setting to its default | — |
| 3 | architecture | 18 | critical | 100 | 2fe8d7070dfa | Diff brings back the dead split-form layout that HEAD 542d5dd fixed, and drops the file's own form= attribute pattern | bugs: "General edits can never be saved"; impact: "General settings can no longer be saved" |

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| run-1 | len=1,head=542d5dd ✓ | ✓ | `impact` L18 [critical, 100] "…its fields can never be submitted on their own"; `bugs` L134 [warning, 94] "Save Settings resets every General setting to its hardcoded default" | ✓ | ✓ names fields not submitted / values reset on save | ✓ critical | CATCH | joined |
| run-2 | len=1,head=542d5dd ✓ | ✓ | `bugs` L134 [warning, 94] "Each Save Settings click resets every General setting to its default"; `architecture` L18 [critical] (members: "General fields can't be saved") | ✓ | ✓ names values lost on save | ✓ critical/warning | CATCH | joined |
| run-3 | len=1,head=542d5dd ✓ | ✓ | `bugs` L134 [warning, 94] "Saving Settings resets every General setting to its default"; `architecture` L18 [critical] (members: "General edits can never be saved") | ✓ | ✓ names values lost on save | ✓ critical/warning | CATCH | joined |

**Per-diff: 3/3 catch.** Codex dropouts: 0. In none of the three runs did a codex-led row
survive (`codex_findings=0`). Codex was joined, and its finding rides as a member of the L18 row in
all three runs.

---

## 4. Per-run scoring — should-quiet diffs (D-08 FP rule)

An **FP** on a should-quiet diff is ANY surviving finding with band **critical OR warning**. It is
not site-gated. Medium/low findings are noise-notes: recorded, not counted. A run with none of
either is QUIET. Rows are verbatim `score43.py fp` output (agent/file/line/band/score/stable_hash;
no titles). The notes column carries facts only.

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
| run-1 | len=1,head=84aff27 ✓ | ✓ | none | QUIET | joined | 0 findings; 8 lanes |
| run-2 | len=1,head=84aff27 ✓ | ✓ | none | QUIET | joined | 0 findings; 8 lanes |
| run-3 | len=1,head=84aff27 ✓ | ✓ | none | QUIET | joined | 0 findings; 7 lanes (no framework-angular; §2) |

**Per-diff: 0/3 fired.** Codex dropouts: 0.

### 4.3 should-quiet-3 (carried) — `src/roonseek/transfer.py` : 201-218, 220, 256-257 · safe ON HTTP-client / path-injection / error-handling · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=1027691 ✓ | ✓ | none | QUIET | joined | 1 medium noise-note |
| run-2 | len=1,head=1027691 ✓ | ✓ | none | QUIET | joined | 0 findings |
| run-3 | len=1,head=1027691 ✓ | ✓ | none | QUIET | joined | 1 medium noise-note |

**Per-diff: 0/3 fired.** Codex dropouts: 0.

### 4.4 should-quiet-4 (new) — `triggarr/models/config.py` : 88-115 · safe ON SSRF / input-validation (ADDS `validate_url_ssrf`, tightening the guard) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=14eecb5 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:108 [critical, 100] `14f1895e7297` | FP | joined | only critical/warning row is codex-led; members codex, security, bugs×2, impact |
| run-2 | len=1,head=14eecb5 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:107 [critical, 100] `de932df74922` | FP | joined | codex-led; members codex, bugs×2, architecture, security, impact |
| run-3 | len=1,head=14eecb5 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:107 [critical, 100] `fedecf9ededf` | FP | joined | codex-led; members codex, bugs×4, security |

**Per-diff: 3/3 fired.** Codex dropouts: 0. In all three runs the alarm is one codex-led row inside
the planted hunk. It makes a concrete-bypass claim: alternate numeric IPv4 spellings of the
metadata address get past the new block. That is a different framing from the Phase-38
startup-crash/layering alarms (§6).

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
| run-1 | len=1,head=9bfd4a6 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:139 [critical, 100] `c93be6bfe251` | FP | joined | codex-led "declared but never wired" row; members codex, impact×2, bugs×2 |
| run-2 | len=1,head=9bfd4a6 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:139 [critical, 100] `92e9bcdf8831` | FP | joined | same framing; members codex, bugs×3, architecture×2, impact |
| run-3 | len=1,head=9bfd4a6 ✓ | ✓ | codex-adversarial `triggarr/models/config.py`:139 [critical, 100] `c93be6bfe251` | FP | joined | `stable_hash` byte-identical to run-1 |

**Per-diff: 3/3 fired.** Codex dropouts: 0. This is the pre-registered expected residual
(feature-incompleteness, backlog 999.19).

### 4.7 should-quiet-7 (new) — `triggarr/web/routes.py` : 60-66, 443-449, 547-553 · safe ON settings input-parse path · any critical/warning = FP · **excluded from the verdict (#001)**

| run | isolation | tree.diff | critical/warning findings | verdict | Codex | notes |
|---|---|---|---|---|---|---|
| run-1 | len=1,head=ce567d3 ✓ | ✓ | codex-adversarial `triggarr/web/routes.py`:550 [critical, 100] `530fe1eb6b5d`; codex-adversarial `triggarr/web/routes.py`:446 [warning, 94] `21667f91c616` | FP | joined | excluded (SUPERSESSIONS #001 / D-00a2 — descriptive only); 8 lanes |
| run-2 | len=1,head=ce567d3 ✓ | ✓ | bugs `triggarr/web/routes.py`:550 [critical, 100] `234ca986d72e`; codex-adversarial `triggarr/web/routes.py`:446 [warning, 94] `30c1d8feff9e` | FP | joined | excluded (SUPERSESSIONS #001 / D-00a2 — descriptive only); 8 lanes |
| run-3 | len=1,head=ce567d3 ✓ | ✓ | codex-adversarial `triggarr/web/routes.py`:550 [critical, 100] `530fe1eb6b5d`; codex-adversarial `triggarr/web/routes.py`:446 [warning, 94] `86011a03320d` | FP | joined | excluded (SUPERSESSIONS #001 / D-00a2 — descriptive only); 9 lanes; L550 `stable_hash` byte-identical to run-1 |

**Per-diff: 3/3 fired (descriptive).** The L550 rows name the config-loss defect that #001
recorded: an absent form field resets the saved value to 60.0. These runs count only in the
sealed-literal x/21. They never count in the corrected 18, in the verdict, or in FAILED-DIFFS.

### Codex dropouts per diff (D-08)

`score43.py codex-status`: `codex.status=joined reason=null dropout=no` on **all 36 runs**. Dropouts
per diff: 0 for every one of the 12 diffs.

---

## 5. Aggregation (exact fractions, no rounding)

Command (the PINNED surface):
`python3 plugins/vibe-check/scripts/score43.py aggregate --runs-root …/first --label first --fp-bar 8 --sealed-fp-bar 9 --catch-bar 15 --catch-verdicts …/first/CATCH-VERDICTS.json --verdict-out …/first/VERDICT.json`
→ exit 0. Output line 1:
`first: MISS — quiet fired 6/18 (corrected cohort, bar <= 8; excluded: should-quiet-7); catch 13/15 (bar 15)`.

The generator's per-run fired flags equal §4 row for row: 6 fired runs among the 18 counted, and 3
fired should-quiet-7 runs. Its catch count comes only from the 15-entry hand map, which equals §3's
verdict column.

**MISS**

- **Quiet arm (corrected, deciding):** quiet fired **6 of 18** against a bar of ≤ 8, so this arm
  passes. False alarms went **16→6 of 18**: should-quiet-4 3/3, should-quiet-6 3/3, and
  should-quiet-1, -2, -3, -5 each 0/3.
- **Catch arm (deciding):** catch **13 of 15** against a bar of 15, so this arm misses. Catches went
  **15→13 of 15**: triggarr-autoescape fell to 1/3; secret-in-logs, third-organic, session-rotation
  and settings-form-split held 3/3 each.
- The bar is a single AND, so the catch arm alone decides **MISS**.

sealed literal (never deciding): quiet fired 9/21 vs the sealed bar ≤ 9/21. On the quiet arm
alone that is within the bar. With the catch arm at 13/15 the sealed-literal reading would be
**MISS** (`sealed_literal.would_be: MISS`). The sealed bar text, from blob `633f1dd`: "v2.10 FP-rate
on the full grown set ≤ ½ × the SET-03 baseline FP-rate, AND catch-rate on the same diffs no worse
than baseline." Against the sealed baseline 19/21, ½ is 9.5, so ≤ 9 of 21.

should-quiet-7: fired 3/3 (excluded from the verdict and from retune eligibility; #001).

Dropouts: 0 on all 12 diffs (36/36 Codex `joined`).

| diff-id | role | fraction | superseded/sealed baseline (SCORING-v2.10 §5) |
|---|---|---|---|
| triggarr-secret-in-logs | should-catch | 3/3 catch | 3/3 |
| triggarr-autoescape | should-catch | **1/3 catch** | 3/3 |
| third-organic-should-catch | should-catch | 3/3 catch | 3/3 |
| triggarr-session-rotation | should-catch | 3/3 catch | 3/3 |
| triggarr-settings-form-split | should-catch | 3/3 catch | 3/3 |
| should-quiet-1 | should-quiet | 0/3 fired | 3/3 |
| should-quiet-2 | should-quiet | 0/3 fired | 3/3 |
| should-quiet-3 | should-quiet | 0/3 fired | 3/3 |
| should-quiet-4 | should-quiet | 3/3 fired | 3/3 |
| should-quiet-5 | should-quiet | 0/3 fired | 1/3 |
| should-quiet-6 | should-quiet | 3/3 fired | 3/3 |
| should-quiet-7 (excluded) | should-quiet | 3/3 fired | 3/3 |

Totals:

- Corrected quiet: **6/18**.
- Sealed-literal quiet: **9 of 21**.
- Catch: **13/15**.
- Verdict: **MISS**, carried by the catch arm.

### FAILED-DIFFS (D-06) — committed in the same commit as VERDICT.json, before any retune edit

`python3 plugins/vibe-check/scripts/score43.py failed-diffs --runs-root …/first --out …/first/FAILED-DIFFS.json`
→ `excluded from retune eligibility: should-quiet-7` / `failed diffs: should-quiet-4, should-quiet-6, triggarr-autoescape`, exit 0.

`FAILED-DIFFS.json` = `["should-quiet-4", "should-quiet-6", "triggarr-autoescape"]`. It was
asserted before committing that should-quiet-7 is absent. The retune scope for 43-06 is these
three diffs × 3 runs.

---

## 6. Confound examination (D-00c) — recorded for 43-07

Order pre-registered in `RESULTS-v2.10.md` §"Pre-registered confound": any catch regression or new
quiet-diff row is examined FIRST against (a) the Phase-42 Codex focus-text change and (b) the
moved-control qualifier, before it is attributed to anything else. The evidence is the per-run
`lanes.json` and `codex-payload.json`, all committed.

**Catch regression — triggarr-autoescape runs 1 and 2:**

- **(b) Moved-control qualifier: did not fire.** The qualifier's capped-note forms were searched
  across all 36 `lanes.json` and `codex-payload.json`. The Claude-lane wording is "…covers every
  path the old check guarded" and the Codex wording is "that file:line covers every path…".
  **0 hits** in either form. The `pending: confirm …` notes present in the autoescape runs (runs 2
  and 3) are about which Starlette release removes `**env_options`. They are not replacement-coverage
  caps, and no lane claimed a same-purpose replacement.
- **(a) Codex focus-text change: does not explain the loss under the scoring basis.**
  - Clause (2) of `templates/codex-focus.txt` at S explicitly names a change that "makes it depend
    on fragile or version-dependent configuration" as a real defect at honest confidence. That
    points Codex toward this diff, not away from it.
  - Codex's role differed by run. In run-1 Codex returned `approve` with 0 findings ("HTML
    autoescaping remains enabled and verified"). In runs 2 and 3 Codex led the surviving row at
    0.99/high with startup-failure titles.
  - Under entry 007, a Codex lead cannot hide an axis-naming member, because every member title is
    judged. So Codex's own wording decides nothing unless it is the only lane naming the axis. In
    run-2 no lane names it.
  - This is the pre-registered case "Codex is the only lane that names the right axis" running in
    reverse: Codex did not name it either.
  - Whether the prior focus text would have produced an XSS-named Codex title cannot be tested
    offline (D-08 note: replays cannot re-run Codex).
- **Other contributing fact (not a pre-registered confound):** the security lane in run-2 rated
  its own finding at confidence 35 / severity low, titled "Autoescape reconfigured via deprecated
  Jinja2Templates env_options kwarg". The impact lane's version-dependence notes in runs 1 and 3
  were also 35/low. The raw text of all three says "no bypass demonstrated / forward-looking risk",
  which is the shape of the Phase-42 sensitive-area ceiling (clause 3, ≤ 0.45 / low). In run-3,
  security rated 65/high and its title names XSS. In run-1, security rated 60/medium with a
  deprecation title. Every lane empirically verified that escaping is still on under the locked
  Starlette 0.52.1 (§3.2 fact). This is the most likely proximate cause of the run-to-run axis
  variance. It is recorded for 43-06/43-07 as a candidate, not established as cause.
- **Dropouts:** none (Codex joined 3/3).

**Quiet rows — should-quiet-4 and should-quiet-6.** Neither is a NEW quiet-diff row: both fired
3/3 in the baseline.

- **should-quiet-6** is the pre-registered expected residual.
- **should-quiet-4:** the framing moved from the baseline's startup-crash/layering complaints to a
  codex-led concrete-bypass claim (numeric IPv4 aliases of the metadata address).
  - Clause (1) of the Codex focus text explicitly tells Codex to report "an input the new check is
    written to block and demonstrably fails to block" at honest confidence.
  - So the focus text is a direct, documented contributor to this row's form (confound (a)).
  - The moved-control qualifier is not involved (0 hits).
  - Whether the bypass claim is a real defect in the fixture is outside scoring. D-08 is band-only
    and the FP stands.

**Newly quiet diffs.** should-quiet-1, -2, -3 and -5 are 0/3 fired. should-quiet-2 run-3 dispatched
no framework lane (§2), and its siblings with the lane were also quiet.

---

## 7. Provenance recap

- **Seals:** SEAL1 `4c67283b46540f997b8a5c6b530996da880b53ed` and SEAL2
  `633f1dd0daa24b823d8abab7cff00823a3c2b256`, derived with the ledger-004 full-history all-ref form.
  The verifier was executed from `de8633cb3e1a295208d89f5be7472e665aec7822` (sha256 `605e61a3…081a3`).
- **Key blobs:** `ef0ab67` (sha256 `1463…3fca1`) and `5f687d9` (sha256 `f58f…53d4`). Both were
  digest-verified twice and both are ancestors of HEAD.
- **Denominators:** 15 / 21 / 36 from the `633f1dd` blob. The corrected quiet denominator is 18
  (#001).
- **Measured system:** snapshot S `be6b0fcd9a4c2794dd3351ea054a65f3ab91e536`, which descends from
  `cede608`, `180e0e3` and `8ae33da`. Install-cache parity was 106/106 forward, 0 reverse extra.
- **Harness:** Claude Code 2.1.281 · codex-cli 0.153.4 · model EXACT `fable 5.1` · 1M context ·
  codex companion 1.0.4 · driver assistant-tmux. The claude-code pin follows entry 006, and the 1M
  window is a disclosed difference from the 200k Phase-38 baseline (D-03).
- **Hand inputs:** `first/CATCH-VERDICTS.json` (15 entries, from §3). The quiet arm is fully
  mechanical.
- **Outputs:** `first/VERDICT.json`, plus `first/FAILED-DIFFS.json` (MISS). Both are committed
  together with this worksheet.
