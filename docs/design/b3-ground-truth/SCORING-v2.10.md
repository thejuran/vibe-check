# B3 v2.10 Scoring worksheet — per-run SITE/AXIS/BAND verdicts (Phase 38, plan 38-05)

The auditable trail behind the v2.10 **baseline** catch-rate / FP-rate: 12 diffs × 3 runs on the
**unchanged 2.9.0 plugin** under ONE pinned Claude-5 harness tuple. Every aggregate below is
re-derivable from the committed `runs-v2.10/<id>/run-<n>/state.json` plus the two committed
answer-key blobs using only the rows here.

**Scored:** 2026-09-08. **Scoring input:** `state.passes[-1].findings[]` (D-06 — never a
transcript), against the committed answer-key BLOBs (never a live working file). Carried rows score
against the **v2.9 blob** `ef0ab67cb45957167c99eff468077348432e1474`; new rows against the
**v2.10 blob** `5f687d95f9be4fef2c0fcd78491c308d4c3861e8` (two-seal independence).
**Scoring code frozen:** no band or score was recomputed — bands are read from state (ROBUST-01).

---

## 1. Integrity gate ladder results (all hard gates PASS)

Every proof value below was DERIVED from git history and committed blobs, never trusted from a live
working file. The ladder is fail-closed: any gate failure means STOP and report, never score around.

### (1) Manifest derivation + APPEND INTEGRITY

| Check | Command | Result |
|---|---|---|
| Manifest commit budget == 2 | `git rev-list --count HEAD -- …/PREREGISTRATION-v2.10.md` | `2` ✓ |
| SEAL1 = first, SEAL2 = second | `git rev-list --reverse HEAD -- <manifest>` | SEAL1 `4c67283b46540f997b8a5c6b530996da880b53ed`; SEAL2 `633f1dd0daa24b823d8abab7cff00823a3c2b256` ✓ |
| No manifest commit carries runs content | `git show --name-only --format= <SEAL1\|SEAL2>` | each lists ONLY `…/PREREGISTRATION-v2.10.md` — no `runs-v2.10/` path ✓ |

**PINNED canonical verifier** (never re-derived by hand, never the unpinned working file):

- `verifier-commit: a407539115872137dc55d99aef439a9c5a4f16d9` and
  `verifier-sha256: 7be8ed39e9ad38a521caa17316fcea8894a7f25ab54b72af7b673a9bff75daaf`,
  parsed from `git show HEAD:…/RUN-METHOD-NOTES-v2.10.md`.
- live `verify-seal2-append.py` sha256 = `7be8ed39e9ad38a521caa17316fcea8894a7f25ab54b72af7b673a9bff75daaf` == pin ✓
- `git rev-list --count HEAD -- …/verify-seal2-append.py` = `1` ✓ (exactly one commit ever touched the path)
- `git show a407539:…/verify-seal2-append.py | python3 -` → **`SEAL2-APPEND-WHITELIST-OK`**, exit 0 ✓

That proves on raw `git show` BYTES that SEAL2's blob is SEAL1's blob plus exactly the ordered
five-line whitelist suffix. A seal-2 that rewrote the already-used pass bar — or rewrote LF to CRLF —
would HARD-FAIL here even at commit count 2.

**Sealed fields parsed from the SEAL2 blob** (`git show 633f1dd:<manifest>` — never the live file):

| Field | Value | Source blob |
|---|---|---|
| `ANSWER_KEY_COMMIT` | `ef0ab67cb45957167c99eff468077348432e1474` | SEAL1 blob |
| `ANSWER_KEY_SHA256` | `1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1` | SEAL1 blob |
| `NEW_ANSWER_KEY_COMMIT` | `5f687d95f9be4fef2c0fcd78491c308d4c3861e8` | SEAL2 blob |
| `NEW_ANSWER_KEY_SHA256` | `f58f888c9f4dc86d0e34d5a152c781cb7e9913087405e6e25980bd77e3d753d4` | SEAL2 blob |
| `DENOM_CATCH_RUNS` | **15** | SEAL2 blob |
| `DENOM_QUIET_RUNS` | **21** | SEAL2 blob |
| `DENOM_TOTAL_RUNS` | **36** | SEAL2 blob |

`DENOM_TOTAL (36) == DENOM_CATCH (15) + DENOM_QUIET (21)` ✓

### (2) Ordering gates

- `FIRST_RUNS_V210_COMMIT` = `48dd571ce4af078b83eaf31d649b7cb7b5dc73c1`; SEAL1 is a strict ancestor ✓
  (the bar provably precedes every v2.10 run artifact).
- SEAL2 strictly precedes the first `runs-v2.10/<new-id>/` commit for **every** new diff ✓:

  | new diff | first run commit | descends strictly from SEAL2 |
  |---|---|---|
  | should-quiet-4 | `9155632` | ✓ |
  | should-quiet-5 | `f6503da` | ✓ |
  | should-quiet-6 | `84cf49f` | ✓ |
  | should-quiet-7 | `3ec83bb` | ✓ |
  | triggarr-session-rotation | `d10c77d` | ✓ |
  | triggarr-settings-form-split | `4f127ba` | ✓ |

- All 6 carried diffs' run commits descend from SEAL1 ✓. Zero carried run commits landed between
  SEAL1 and SEAL2 (such landings would have been LEGAL — their key sealed at the v2.9 manifest).
- All 37 `runs-v2.10/` commits descend from `ef0ab67`; every NEW-diff run commit additionally
  descends from `5f687d9` ✓. (37 = 36 run captures + 1 committed failed-run sibling, see gate 5.)
- Post-SEAL1 commits touching `plugins/vibe-check/`: 2 (`9d565f3`, `5d2173a`), both strictly after
  SEAL1 ✓. **Both touch only `plugins/vibe-check/docs/efficacy/ULTRAREVIEW-SHADOW.md`** — a
  non-executable backlog/status document. `git diff v2.9 --name-only -- plugins/vibe-check/` returns
  that one doc and nothing else, so the **measured (executable + prompt) plugin surface is
  byte-identical to shipped 2.9.0**. Independently, all 12 committed fingerprints record
  `cache-root: …/thejuran/vibe-check/2.9.0` — the runs resolved their helpers from the installed
  2.9.0 cache, not from the repo tree.

### (3) Dual digest gate (run TWICE) + ancestry

| Blob | Recomputed sha256 (pass 1 == pass 2) | Sealed value | Result |
|---|---|---|---|
| `git show ef0ab67:…/ANSWER-KEY-b3.md` | `146354…3fca1` | SEAL1 `ANSWER_KEY_SHA256` | **DIGEST MATCH** ✓ |
| `git show 5f687d9:…/ANSWER-KEY-v2.10.md` | `f58f88…753d4` | SEAL2 `NEW_ANSWER_KEY_SHA256` | **DIGEST MATCH** ✓ |

`git merge-base --is-ancestor ef0ab67 HEAD` → exit 0 ✓; `… 5f687d9 HEAD` → exit 0 ✓.
On either mismatch this task would have EXITED NON-ZERO and refused to score.

### (4) Score-from-blob materialization

Both keys were materialized with `git show` into the scratchpad
(`answer-key-b3-scored.md`, 150 lines; `answer-key-v2.10-scored.md`, 136 lines) and re-digested to
the sealed values. Every scored input — SITE/AXIS/BAND rows, each row's `base_sha`, the D-07/D-08/D-09
rules — was parsed FROM THOSE BLOBS. No live key file was a scoring input.

**(4d) Live-file sanity (WARNING-only, does not gate):** live `ANSWER-KEY-b3.md`, live
`ANSWER-KEY-v2.10.md`, and the live manifest are each byte-IDENTICAL to their sealed blobs — no
drift ✓. (Scoring reads only blobs, so even a drifted live file would not invalidate the numbers.)

### (5) Runs-clean + five-file layout + failed siblings + sealed v2.9 tree

- `git status --porcelain …/runs-v2.10/` → **EMPTY** ✓; `… runs/` → **EMPTY** ✓;
  `… RUN-METHOD-NOTES-v2.10.md` → **EMPTY** ✓ (notes committed clean).
- `git diff v2.9 --quiet -- …/runs/` → exit 0 ✓ — the **sealed v2.9 archive is byte-identical to tag
  v2.9** at scoring time (verified, not assumed).
- All **36** run dirs contain exactly the FIVE v2.10 files (`clear.txt`, `session.txt`, `state.json`,
  `tree.diff`, `tree.diff.sha256`) ✓.
- All 36 `clear.txt` files full-line match `<ISO-timestamp±ZZZZ> CLEARED` ✓ — the N-01
  conversation-boundary attestation exists per run.
- **Failed-run siblings: 1** — `runs-v2.10/should-quiet-1/run-2.failed-1788703614/` (the N-08
  interrupted run). It is **COMMITTED** (`0c0e09a`, "runs(38): should-quiet-1 run 2 FAILED — evidence
  archived"), and that commit touched only the 4 paths under its own failed dir ✓. No untracked
  evidence and no ad hoc cleanup commit (v2.9 needed `4eff2aa`; the self-committing recovery block
  removed that class). Failed siblings are excluded from the 36-run set by construction — only
  `run-1/run-2/run-3` are enumerated.

### (6) SIDECAR SEAL GATE, then per-run isolation

**(6a) Sidecar seal — run BEFORE any sidecar value is consumed:**

- All **12** `sha256(diffs/…)` lines in the materialized NEW key blob match BOTH the HEAD blob AND
  the live file of each new-kit `.patch`/`.provenance` ✓ — a kit rewritten after sealing would
  HARD-FAIL here.
- All 6 CARRIED diffs: `git rev-parse HEAD:<path>` == `git rev-parse v2.9:<path>` for both
  `.patch` and `.provenance` ✓ — carried kits are v2.9-blob-equal.

Only after that gate were the sidecars' `EXPECTED_TREE_DIFF_SHA256` values consumed.

**(6b) Per-run isolation:** for every diff × run 1-3 — `len(passes) == 1`,
`passes[-1].head_sha == the sealed base_sha`, and `sha256(tree.diff)` == the run's
`tree.diff.sha256` file == the proven-sealed sidecar's `EXPECTED_TREE_DIFF_SHA256`. See §2 for the
full grid. **36/36 pass all three.**

### (8) Security spot-check (before any bulk scoring)

The FIRST archived state of every NEW diff was scanned for echoed runtime secrets (20+-char literal
grep plus eyeball of each hit) in `current_code`/`source_window` fields:

| new diff | run-1 findings | 20+-char tokens found | verdict |
|---|---|---|---|
| triggarr-session-rotation | 13 | none | CLEAN |
| triggarr-settings-form-split | 11 | `border-triggarr-border` (CSS class) | CLEAN |
| should-quiet-4 | 4 | `validate_arr_url_config` (identifier) | CLEAN |
| should-quiet-5 | 0 | none | CLEAN |
| should-quiet-6 | 2 | `max_consecutive_failures`, `shutdown_drain_timeout` (identifiers) | CLEAN |
| should-quiet-7 | 7 | `_SHUTDOWN_DRAIN_TIMEOUT`, `_read_shutdown_drain_timeout`, `max_consecutive_failures`, `shutdown_drain_timeout` (identifiers) | CLEAN |

Zero secret-shaped literals, zero `api_key=<literal>` assignments. **No scrub needed.**

### (9) Harness evidence — COMMIT-ANCHORED, PIN-MATCHED, PRE-RUN-ORDERED

The notes file is mutable, so a live-file timestamp match would prove nothing. Every check below
reads committed blobs and binds **per run**, never a count.

**(9a)** 12 fingerprint sessions parse from the committed HEAD notes blob by the anchored header
`^## Harness fingerprint — <ISO±ZZZZ>$`; **zero duplicate session IDs** ✓. The seeded plural
`## Harness fingerprints` header and the `$(date …)` template line inside the documented append
command both fall outside the anchor, so a zero-fingerprint file could not have passed.

**(9d) HARNESS PIN (parsed from the committed HEAD notes blob):**

| pin line | value |
|---|---|
| `pin-claude-code` | `2.1.261 (Claude Code)` |
| `pin-codex` | `codex-cli 0.153.4` |
| `pin-model` | `fable 5` |

Commits that ever changed a `pin-*` line: `0d5b677`, `62419f9` (the original pin plus the
2026-09-05 codex correction from 0.145.0, made while zero fingerprints and zero run commits
existed). **Both are ancestors of the first fingerprint commit AND of every one of the 36
run-capture commits** ✓ — the pin provably predates all evidence, so the pre-run-only correction
rule is enforced from history rather than asserted.

**(9b)(c)(e) Per-run results — 36/36 PASS:**

- every `session.txt` is exactly SID + 40-hex FPC;
- the FPC commit touched **only** the notes file;
- the SID block is PRESENT at FPC and **ABSENT at FPC^** (FPC INTRODUCED it — a backfilled
  fingerprint fails here);
- the block's `claude-code:`/`model:`/`codex:` lines at the FPC blob **byte-equal** the same lines at
  the HEAD blob (a later edit to a referenced block fails);
- FPC != the run-capture commit, exactly one commit captured each run dir, and
  `git merge-base --is-ancestor FPC RC` holds;
- every `model:` value FULL-LINE matches the exact grammar
  `^(claude[- ])?(fable|opus|sonnet|haiku)[- ]5(\.[0-9]+)?(-[0-9]{8})?$`; every `claude-code:` and
  `codex:` value **byte-equals its pin line** (`unknown` rejected), and the `codex:` line carries a
  full semver;
- **the normalized model value is IDENTICAL across all sessions: `fable 5.1`** — the baseline
  provably measures ONE model + CLI harness, no cohort split, no silent aggregation;
- both the `clear.txt` timestamp AND the FPC committer time strictly precede
  `state.passes[-1].timestamp` for every run — an attestation typed, or a fingerprint committed,
  after the review ran cannot certify that run.

**Session → run coverage (10 governing sessions, 36 runs):**

| session ID (SID) | introducing commit (FPC) | runs governed |
|---|---|---|
| 2026-09-05T18:09:56-0400 | `0559abc` | triggarr-secret-in-logs 1-3, triggarr-autoescape 1-3 (6) |
| 2026-09-05T22:17:54-0400 | `93b42fa` | third-organic-should-catch 1-3 (3) |
| 2026-09-05T23:13:29-0400 | `62c2c6a` | should-quiet-1 run-1 (1) |
| 2026-09-07T19:03:13-0400 | `25959f4` | should-quiet-1 run-2, run-3 (2) |
| 2026-09-07T19:42:21-0400 | `0f7d643` | should-quiet-2 1-3 (3) |
| 2026-09-07T21:24:50-0400 | `ccf3f4b` | should-quiet-3 1-3 (3) |
| 2026-09-07T22:03:31-0400 | `155cff0` | triggarr-session-rotation 1-3, triggarr-settings-form-split 1-2 (5) |
| 2026-09-08T12:39:46-0400 | `f52a8e1` | should-quiet-4 1-3, triggarr-settings-form-split run-3 (4) |
| 2026-09-08T13:34:07-0400 | `4cf30a7` | should-quiet-5 1-3 (3) |
| 2026-09-08T14:10:42-0400 | `0108fd4` | should-quiet-6 1-3, should-quiet-7 1-3 (6) |

Two of the 12 committed fingerprints govern no run (the 2026-09-05T18:04:05 and 2026-09-06T10:07:19
sessions). Both correspond to recorded recovery events — the N-08 interrupted run and the N-09
attest-before-launch correction — whose pre-run artifacts were removed under the PRE-RUN (0)
not-triggered rule. An unreferenced fingerprint cannot certify anything; the gate binds runs → blocks,
never blocks → runs.

**Ladder result: ALL GATES (1-9) PASS. Scoring authorized.**

---

## 2. Scoreable-completeness ledger (NO AGGREGATION OVER HOLES)

The diff universe is the **committed inventory** — every `diffs/*.provenance` basename — asserted by
set-equality against the archive, never a universe derived from `runs-v2.10/` globs (which would
silently pass a diff with zero runs). Isolation gate per run: `len(passes)==1` AND
`passes[-1].head_sha == the sealed row's base_sha` AND the tree.diff triple match. A run failing any
of these is `unscoreable` and BLOCKS aggregation.

**All 36 expected runs (12 diffs × 3) passed → 3/3 scoreable per diff, ZERO holes.** Aggregation is
authorized WITHOUT any owner waiver.

| diff-id | role | origin | base_sha (sealed row) | run-1 | run-2 | run-3 | scoreable |
|---|---|---|---|---|---|---|---|
| triggarr-secret-in-logs | should-catch | carried | `f4366a2` | len=1,head=f4366a2 ✓ | ✓ | ✓ | **3/3** |
| triggarr-autoescape | should-catch | carried | `e11187e` | len=1,head=e11187e ✓ | ✓ | ✓ | **3/3** |
| third-organic-should-catch | should-catch | carried | `3db8b48` | len=1,head=3db8b48 ✓ | ✓ | ✓ | **3/3** |
| triggarr-session-rotation | should-catch | new | `f4366a2` | len=1,head=f4366a2 ✓ | ✓ | ✓ | **3/3** |
| triggarr-settings-form-split | should-catch | new | `542d5dd` | len=1,head=542d5dd ✓ | ✓ | ✓ | **3/3** |
| should-quiet-1 | should-quiet | carried | `98eb419` | len=1,head=98eb419 ✓ | ✓ | ✓ | **3/3** |
| should-quiet-2 | should-quiet | carried | `84aff27` | len=1,head=84aff27 ✓ | ✓ | ✓ | **3/3** |
| should-quiet-3 | should-quiet | carried | `1027691` | len=1,head=1027691 ✓ | ✓ | ✓ | **3/3** |
| should-quiet-4 | should-quiet | new | `14eecb5` | len=1,head=14eecb5 ✓ | ✓ | ✓ | **3/3** |
| should-quiet-5 | should-quiet | new | `7035477` | len=1,head=7035477 ✓ | ✓ | ✓ | **3/3** |
| should-quiet-6 | should-quiet | new | `9bfd4a6` | len=1,head=9bfd4a6 ✓ | ✓ | ✓ | **3/3** |
| should-quiet-7 | should-quiet | new | `ce567d3` | len=1,head=ce567d3 ✓ | ✓ | ✓ | **3/3** |

Per-diff `tree.diff` integrity (FULL tracked diff, no pathspec): all three per-run
`tree.diff.sha256` are identical to each other AND equal the sealed sidecar's
`EXPECTED_TREE_DIFF_SHA256`, for all 12 diffs — **0 unscoreable from tree.diff**.

| diff-id | sealed EXPECTED_TREE_DIFF_SHA256 (prefix) | run-1 | run-2 | run-3 |
|---|---|---|---|---|
| triggarr-secret-in-logs | `f0c70a02…` | ✓ | ✓ | ✓ |
| triggarr-autoescape | `4fdadb70…` | ✓ | ✓ | ✓ |
| third-organic-should-catch | `d9918036…` | ✓ | ✓ | ✓ |
| triggarr-session-rotation | `a924c819…` | ✓ | ✓ | ✓ |
| triggarr-settings-form-split | `40ae123c…` | ✓ | ✓ | ✓ |
| should-quiet-1 | `a8137f5d…` | ✓ | ✓ | ✓ |
| should-quiet-2 | `3cb198dc…` | ✓ | ✓ | ✓ |
| should-quiet-3 | `66fe1425…` | ✓ | ✓ | ✓ |
| should-quiet-4 | `f71a7730…` | ✓ | ✓ | ✓ |
| should-quiet-5 | `8af04cc6…` | ✓ | ✓ | ✓ |
| should-quiet-6 | `75704ed5…` | ✓ | ✓ | ✓ |
| should-quiet-7 | `d94fb90d…` | ✓ | ✓ | ✓ |

Role denominators derived from the inventory (5 should-catch × 3 = 15; 7 should-quiet × 3 = 21;
total 36) **match the sealed `DENOM_*` lines exactly**.

**Rule: NO AGGREGATION OVER HOLES.** A missing or unscoreable run leaves its denominator slot
explicitly open — repeated or disclosed, never silently dropped.
**Owner waiver: NONE** (and none needed — the set is complete).

---

## 3. Per-run scoring — should-catch diffs (D-07 three-gate rule)

A **catch** requires SITE (right file + within the planted hunk, keyed to the row's base_sha) AND
AXIS (the finding names the key's required MECHANISM, honoring the row's NOT-clause) AND BAND
(rendered band ≥ the row's floor). SITE-only, or SITE+AXIS-below-band, = `detected-below-threshold`
= a MISS in the headline. Codex participation is recorded from finding attribution
(`findings[].agent == codex-adversarial`) — the pass-level codex record proved
schema-nondeterministic across the campaign (≥6 shapes, including a plain string and outright
absence), so it is not the evidence source.

### 3.1 triggarr-secret-in-logs (carried → v2.9 blob) — SITE `triggarr/clients/base.py` : 230-238 / 249-256 · AXIS = secret/API-key/PII leaked into logs (NOT "log formatting") · BAND floor = warning

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L233 [critical, 100] "Raw HTTP exceptions leak reverse-proxy credentials"; `bugs` L252 [warning, 72] "ValidationError interpolated into log **leaks *arr API response payload values**"; `impact` L252 [warning, 82] "echoes raw *arr response payload into web-exposed log buffer" | ✓ | ✓ (credential/payload leak) | ✓ (critical) | **catch** | ✓ |
| 2 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L233 [critical, 99] "Full HTTP exceptions **leak credentials** embedded in configured URLs"; `impact` L252 [critical, 88] "ValidationError str() embeds raw *arr response body into the web-UI log buffer" | ✓ | ✓ (credential leak) | ✓ (critical) | **catch** | ✓ |
| 3 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L252 [critical, 96] "Validation error formatting can **bypass secret redaction**"; `impact` L233 [critical, 85] "puts the full instance URL (including **userinfo credentials**) into the web log viewer" | ✓ | ✓ (secret/credential leak) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 3/3 catch.**

### 3.2 triggarr-autoescape (carried → v2.9 blob) — SITE `triggarr/web/routes.py` : 42-48 (line 45) · AXIS = XSS surface re-enabled / autoescape NO-OPs (must name escaping/XSS; NOT "deprecation"/"refactor"/"breaks startup") · BAND floor = warning

This is v2.9's pre-registered right-site-wrong-axis case (it scored 2/3 there, with run-1 the MISS).
Because the axis call is the delicate one, each run's winning finding was **hand-verified by reading
the full `problem` text**, not accepted from a title keyword.

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=e11187e ✓ | ✓ | `security/xss` L45 [critical, 85] "Revert to deprecated Jinja2Templates env_options passthrough for autoescape, **undoing prior XSS-autoescape fix**" | ✓ | ✓ — names XSS explicitly in the title and category | ✓ (critical) | **catch** | ✓ |
| 2 | len=1,head=e11187e ✓ | ✓ | `bugs` L45 [warning, 82] "autoescape silently drops on Starlette upgrade" — problem text: "accepted and ignored … **the guarantee is no longer expressed by this code**" and "**Autoescape is the XSS defense for the dashboard templates, which render user-controlled instance names**"; `compliance` L45 [critical, 80] invokes the CLAUDE.md never-disable-autoescaping rule | ✓ | ✓ — names escaping-off + the XSS consequence (verified in full problem text) | ✓ (warning ≥ warning; compliance critical corroborates) | **catch** | ✓ |
| 3 | len=1,head=e11187e ✓ | ✓ | `impact` L45 [critical, 92] "re-arms the autoescape break" — problem text: "ignored without the setdefault (**autoescape off = stored-XSS across all 10 TemplateResponse call sites** rendering user-controlled instance names and config values)" | ✓ | ✓ — names escaping-off + stored-XSS (verified in full problem text) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 3/3 catch** (v2.9 scored 2/3 on this diff — see §5).
Honest note: in runs 2 and 3 the XSS/escaping framing lives in the finding's **problem body**, while
several titles at the same site still lead with deprecation/startup framing. The axis is met — the
key requires the finding to name the mechanism, not to headline it — but this is a weaker, less
legible catch than run 1's explicit `security/xss` title.

### 3.3 third-organic-should-catch (carried → v2.9 blob) — SITE `src/angular/src/app/services/files/view-file.service.ts` : 304-311 · AXIS = unclamped percentage / missing `Math.min(100,…)` clamp / >100% · BAND floor = medium

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=3db8b48 ✓ | ✓ | `bugs` L307 [critical, 88] "Removing **Math.min(100, …)** reintroduces **>100% progress** for extracted files"; `codex-adversarial` L307 [critical, 100] "Restore the 100% cap for extracted files" | ✓ | ✓ (missing clamp / >100%) | ✓ (critical ≥ medium) | **catch** | ✓ |
| 2 | len=1,head=3db8b48 ✓ | ✓ | `impact` L307 [critical, 95] "Removing the Math.min(100, …) clamp reverts shipped fix 879266c — **extracted files render >100% progress again**"; `codex-adversarial` L307 [critical, 100] "Removing the clamp breaks completed-file progress" | ✓ | ✓ (missing clamp / >100%) | ✓ (critical) | **catch** | ✓ |
| 3 | len=1,head=3db8b48 ✓ | ✓ | `bugs` L307 [critical, 92] "**Removed 100% clamp** lets extracted files report **>100% progress**"; `codex-adversarial` L307 [critical, 100] "Preserve the 100% cap for extracted files" | ✓ | ✓ (missing clamp / >100%) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 3/3 catch.**

### 3.4 triggarr-session-rotation (new → v2.10 blob) — SITE `triggarr/web/routes.py` : 1445-1451 / 1459-1469 (planted hunks; findings land at 1564-1588 in the run tree) · AXIS = stale-session survival, password change no longer evicts existing sessions (NOT "dead code cleanup", NOT "logging removed", NOT a response-refactor or cookie-attribute nit) · BAND floor = warning

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=f4366a2 ✓ | ✓ | `bugs` L1564 [critical, 92] "Password change no longer rotates session_secret — **other sessions survive**"; `codex-adversarial` L1567 [critical, 100] "Restore session revocation on password change" ("a **stolen cookie remains usable after the owner changes their password**, for up to its remaining 30-day lifetime") | ✓ | ✓ (session eviction/invalidation lost) | ✓ (critical) | **catch** | ✓ |
| 2 | len=1,head=f4366a2 ✓ | ✓ | `bugs` L1567 [critical, 95] "Password change no longer rotates session_secret; **old sessions survive**"; `security` L1571 [warning, 95] "Password change no longer invalidates existing sessions (**stolen-cookie persistence**)" | ✓ | ✓ (session eviction lost) | ✓ (critical) | **catch** | ✓ |
| 3 | len=1,head=f4366a2 ✓ | ✓ | `bugs` L1564 [critical, 93] "Password change no longer rotates session_secret, **leaving all old sessions valid**"; `security` L1567 [critical, 92] "**session-fixation / stale-cookie persistence**" | ✓ | ✓ (session eviction lost) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 3/3 catch.**

### 3.5 triggarr-settings-form-split (new → v2.10 blob) — SITE `triggarr/templates/settings.html` : 15-28 / 33-81 / 87-93 / 131-137 · AXIS = silent data loss on save, General fields no longer submitted (NOT "HTML restructuring", NOT "duplicate form action", NOT a styling/a11y nit) · BAND floor = warning

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=542d5dd ✓ | ✓ | `bugs` L18 [critical, —] "General settings form has no submit button — General fields are **unsavable** from the UI"; `security` L18 [critical] "**silently resetting settings to defaults on save**"; `codex-adversarial` L18 [critical] "Restore General controls' association with Save Settings" | ✓ | ✓ (fields not submitted / silently reset) | ✓ (critical) | **catch** | ✓ |
| 2 | len=1,head=542d5dd ✓ | ✓ | `bugs` L18 [critical] "General settings fields are in a form with no submit button, so they **can never be saved**"; `impact` L18 [critical] "every General field is unsavable and **silently resets on each save**" | ✓ | ✓ (fields not submitted / silently reset) | ✓ (critical) | **catch** | ✓ |
| 3 | len=1,head=542d5dd ✓ | ✓ | `bugs` L18 [critical] "General settings form has no submit button — General fields **can never be saved**"; `security` L18 [critical] "**silently resets General config**"; `codex-adversarial` L18 [critical] "Restore General controls' association with the Save Settings form" | ✓ | ✓ (fields not submitted / silently reset) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 3/3 catch.**

---

## 4. Per-run scoring — should-quiet diffs (D-08 FP rule)

An **FP** on a should-quiet diff = ANY finding with band **critical OR warning** (the tool's own
action bar — NOT site-gated). **Medium/low** = noise-notes (recorded, not counted).
**clean** = no critical/warning findings.

### 4.1 should-quiet-1 (carried) — `triggarr/web/validation.py` : 79-91 · Safe ON: SSRF / input-validation (the diff TIGHTENS the host block-list) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=98eb419 ✓ | ✓ | bugs L85 [warning, 78] "IPv4-mapped IPv6 bypasses the BLOCKED_HOSTS metadata check"; impact L84 [critical, 95] "IPv4-mapped IPv6 block is dead code"; impact L77 [warning, 90] "BLOCKED_HOSTS string match bypassed" (+1 medium noise-note, empty title) | **FP** |
| 2 | len=1,head=98eb419 ✓ | ✓ | bugs L85 [critical, 88]; bugs L85 [warning, 90] "Redundant double evaluation"; security L80 [warning, 90] "SSRF bypass via alternate IPv4 hostname encodings"; architecture L85 [critical, 88]; impact L85 [critical, 92]; codex L85 [critical, 99] "Apply the explicit blocklist to mapped IPv4 addresses" (+1 medium) | **FP** |
| 3 | len=1,head=98eb419 ✓ | ✓ | security L85 [warning, 82]; bugs L84 [critical, 93] "dead code"; bugs L85 [critical, 88]; impact L77 [warning, 92]; impact L85 [warning, 88] | **FP** |

**Per-diff: 3/3 FP.** Same pattern as v2.9: multiple independent lanes (bugs/security/impact/codex)
fire self-sufficiently at 78-99 on the same SSRF site of a diff that TIGHTENS the block-list.

### 4.2 should-quiet-2 (carried) — `src/angular/src/app/services/utils/rest.service.ts` : 53-63 · Safe ON: API contract / typing (`post(url)` widened to `post(url, body?)`) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=84aff27 ✓ | ✓ | bugs `config.service.ts`:68 [warning, 88]; impact `config.service.ts`:66 [warning, 88] "config saving is broken"; impact `rest.service.ts`:60 [warning, 72] "`body ?? null` erases the Content-Type header"; impact `mock-rest.service.ts`:5 [warning, 90]; impact `rest.service.spec.ts`:92 [warning, 92] "zero direct coverage" | **FP** |
| 2 | len=1,head=84aff27 ✓ | ✓ | impact `config.service.ts`:68 [warning, 92]; impact `rest.service.spec.ts`:1 [warning, 88] (+2 medium noise-notes) | **FP** |
| 3 | len=1,head=84aff27 ✓ | ✓ | architecture `rest.service.ts`:59 [warning, 72] "no direct unit test"; impact `config.service.ts`:67 [critical, 95] "Settings save is fully broken in-tree"; impact `seed-state.ts`:72 [warning, 88] (+2 medium) | **FP** |

**Per-diff: 3/3 FP.** **This is the sharpest regression from v2.9**, where should-quiet-2 produced
**0 findings on all 3 runs** (clean 0/3). The fleet now reaches beyond the diff into the caller
(`config.service.ts` still GETs a removed route) and into test-coverage gaps on the changed method.

### 4.3 should-quiet-3 (carried) — `src/roonseek/transfer.py` : 201-218, 220, 256-257 · Safe ON: HTTP-client / path-injection / error-handling · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=1027691 ✓ | ✓ | architecture L139 [warning, 88] "docstring declares a closed API surface"; impact L204 [warning, 72] "raises on HTTP 404"; impact L259 [warning, 80] "success_statuses override widens the contract" (+2 medium) | **FP** |
| 2 | len=1,head=1027691 ✓ | ✓ | impact L204 [critical, 88] "transfer_id contract has no producer"; impact L259 [warning, 82] (+1 medium, empty title) | **FP** |
| 3 | len=1,head=1027691 ✓ | ✓ | bugs L259 [warning, 72] "Falsy-default … silently restores {200, 201}"; impact L204 [critical, 82] "will be called with the local SQLite transfers.id" (+2 medium) | **FP** |

**Per-diff: 3/3 FP.** Cross-lane and diverse per run — the H-LANE / B-SEV pattern, as in v2.9.

### 4.4 should-quiet-4 (new) — `triggarr/models/config.py` : 88-115 · Safe ON: SSRF / input-validation (ADDS `validate_url_ssrf`, tightening the guard) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=14eecb5 ✓ | ✓ | bugs L110 [warning, 72] "turns an existing config into an uncaught-traceback startup crash"; architecture L106 [critical, 88] "Domain model layer reaches up into the web layer"; impact L93 [critical, 95] "unrecoverable startup crash" (+1 medium) | **FP** |
| 2 | len=1,head=14eecb5 ✓ | ✓ | architecture L106 [critical, 88] "Package-level import cycle"; architecture L93 [warning, 82]; bugs L93 [critical, 78]; bugs L108 [critical, 82]; bugs L93 [warning, 74]; impact L93 [critical, 92]; impact L106 [warning, 80] (+2 medium) | **FP** |
| 3 | len=1,head=14eecb5 ✓ | ✓ | bugs L93 [critical, 88] "crashes startup with an uncaught ValidationError"; bugs L93 [critical, 84]; impact L93 [critical, 88] "unrecoverable via UI" | **FP** |

**Per-diff: 3/3 FP.** The recurring framing is second-order: the added validator is judged for what
it does to a *pre-existing bad config* (startup crash, no UI recovery) and for the local import
crossing a layering boundary — both real design observations, neither a defect in the shipped
feature. Same class as should-quiet-1: the SSRF/input-validation axis remains the measured weak spot.

### 4.5 should-quiet-5 (new) — `src/python/model/model.py` : 3-9, 78-84, 94-100, 109-115 · Safe ON: log-sanitization / secret-handling (wraps file-name interpolation in `sanitize_log_value`) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=7035477 ✓ | ✓ | 0 findings | **clean** |
| 2 | len=1,head=7035477 ✓ | ✓ | impact `test_lftp_log_sanitization.py`:11 [warning, 92] "CI lint gate (ruff, whole-tree) fails on unused imports in Phase-101 sanitization test f…" | **FP** |
| 3 | len=1,head=7035477 ✓ | ✓ | 0 findings | **clean** |

**Per-diff: 1/3 FP.** The only should-quiet diff on which the tool stayed silent in any run — and the
single FP is not about the diff's own lines at all, but an unused-import lint concern in a
neighbouring test file.

### 4.6 should-quiet-6 (new) — `triggarr/models/config.py` : 132-142 · Safe ON: input-validation / config bounds (`shutdown_drain_timeout` with `ge=1.0, allow_inf_nan=False`) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=9bfd4a6 ✓ | ✓ | impact `routes.py`:540 [warning, 88] "Settings POST whitelist omits shutdown_drain_timeout — any settings save silently resets…"; codex `config.py`:139 [critical, 100] "Wire the configured timeout into the shutdown drain" | **FP** |
| 2 | len=1,head=9bfd4a6 ✓ | ✓ | impact `routes.py`:541 [warning, 88]; codex `config.py`:139 [critical, 100] "Wire the configured timeout into the shutdown drain" | **FP** |
| 3 | len=1,head=9bfd4a6 ✓ | ✓ | impact `routes.py`:539 [warning, 88]; codex `config.py`:139 [critical, 100] "Wire the configured timeout into the shutdown drain" | **FP** |

**Per-diff: 3/3 FP**, and notably the **most stable FP in the set**: byte-identical codex title at
critical/100 in all three runs, plus the same impact warning at 88. The complaint is
incompleteness-of-feature (the new field is declared but not yet consumed) rather than a defect —
this diff is deliberately the first half of a two-commit feature whose second half is should-quiet-7.

### 4.7 should-quiet-7 (new) — `triggarr/web/routes.py` : 60-66, 443-449, 547-553 · Safe ON: settings input-parse path (bounded `safe_float`, mirroring the adjacent `safe_int` parses) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=ce567d3 ✓ | ✓ | bugs L550 [critical, 92] "Absent drain-timeout form field silently resets a saved custom value to 60.0"; bugs L446 [critical, 88]; impact `settings.html`:74 [warning, 95]; impact `scheduler.py`:81 [warning, 90] "config value is never consumed"; codex L446 [critical, 100]; codex L550 [critical, 100] (+1 medium) | **FP** |
| 2 | len=1,head=ce567d3 ✓ | ✓ | bugs L550 [warning, 72]; impact L550 [critical, 95] "Persisted shutdown_drain_timeout is inert"; impact `settings.html`:78 [warning, 97]; codex L550 [critical, 100]; codex L446 [critical, 100] | **FP** |
| 3 | len=1,head=ce567d3 ✓ | ✓ | bugs L550 [critical, 88]; bugs L446 [critical, 90]; architecture `settings.html`:74 [warning, 92] "Half-migrated config knob"; impact `settings.html`:78 [warning, 95]; impact L550 [critical, 90]; codex L550 [critical, 100]; codex L446 [critical, 100] | **FP** |

**Per-diff: 3/3 FP.** Same incompleteness axis as should-quiet-6 (the knob is parsed and rendered but
not yet consumed by the scheduler), at high volume (5-7 action-bar findings per run) with Codex
contributing two criticals at confidence 100 in every run.

---

## 5. Aggregation (D-09, exact fractions, no rounding)

Denominators are exactly the sealed literals parsed from the SEAL2 blob in §1 —
`DENOM_CATCH_RUNS: 15`, `DENOM_QUIET_RUNS: 21`, `DENOM_TOTAL_RUNS: 36`. All 36 slots are filled;
no hole, no waiver.

### Full grown set (12 diffs)

**Headline catch-rate = 15/15** — secret-in-logs 3/3 + autoescape 3/3 + third-organic 3/3 +
session-rotation 3/3 + settings-form-split 3/3.

**Headline FP-rate = 19/21** — should-quiet-1 3/3 + -2 3/3 + -3 3/3 + -4 3/3 + -5 **1/3** + -6 3/3 +
-7 3/3.

> Superseded 2026-09-08 — should-quiet-7 excluded by recorded supersession: FP **16/18** over the
superseded quiet denominator (the sealed 19/21 above is the sealed literal and stands); see
`docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md` #001.

Zero `detected-below-threshold`, zero `miss`, zero `unscoreable`.

| diff-id | role | fraction |
|---|---|---|
| triggarr-secret-in-logs | should-catch | 3/3 catch |
| triggarr-autoescape | should-catch | 3/3 catch |
| third-organic-should-catch | should-catch | 3/3 catch |
| triggarr-session-rotation | should-catch | 3/3 catch |
| triggarr-settings-form-split | should-catch | 3/3 catch |
| should-quiet-1 | should-quiet | 3/3 FP |
| should-quiet-2 | should-quiet | 3/3 FP |
| should-quiet-3 | should-quiet | 3/3 FP |
| should-quiet-4 | should-quiet | 3/3 FP |
| should-quiet-5 | should-quiet | **1/3 FP** |
| should-quiet-6 | should-quiet | 3/3 FP |
| should-quiet-7 | should-quiet | 3/3 FP |

### Carried-6 only — the model-shift re-measure input (v2.9 vs Claude-5)

These are the SAME six diffs, the SAME sealed v2.9 key blob, and the SAME unchanged 2.9.0 plugin as
the v2.9 baseline; the harness (model + CLI) is what changed. 38-06 titles this comparison
family-conditionally from the pinned tuple.

| measure | v2.9 baseline (2026-07) | v2.10 baseline (Claude-5 harness) |
|---|---|---|
| catch-rate (carried 6) | **8/9** | **9/9** |
| FP-rate (carried 6) | **6/9** | **9/9** |

Per-diff movement on the carried set:

| diff-id | v2.9 | v2.10 (this run) | movement |
|---|---|---|---|
| triggarr-secret-in-logs | 3/3 catch | 3/3 catch | unchanged |
| triggarr-autoescape | 2/3 catch | **3/3 catch** | +1 (the v2.9 right-site-wrong-axis MISS did not recur) |
| third-organic-should-catch | 3/3 catch | 3/3 catch | unchanged |
| should-quiet-1 | 3/3 FP | 3/3 FP | unchanged |
| should-quiet-2 | **0/3 FP** (clean, 0 findings all runs) | **3/3 FP** | +3 FP — the largest single movement in the set |
| should-quiet-3 | 3/3 FP | 3/3 FP | unchanged |

**Codex contribution (D-13):** a codex-attributed finding is present in **all 15** should-catch runs
and in **7 of the 21** should-quiet runs. Runs measured the shipped default (`codex=auto`, no
`--codex` forcing). Absence of a codex-attributed finding is NOT skip evidence — several runs record
a codex `verdict: approve` with 0 findings. Participation is read from finding attribution, not the pass-level record — see the
schema-nondeterminism note in §6.

### Observed failure modes (input to 38-06, not a verdict here)

| Observed | Note |
|---|---|
| FP-rate 19/21 on a set built to be quiet, with 6/7 quiet diffs FP'ing 3/3 | the noise problem the v2.10 milestone exists to fix is confirmed, larger and more consistent than v2.9's 6/9 |
| should-quiet-2 moving 0/3 → 3/3 | same diff, same key, same plugin — the shift is attributable to the harness (model + codex-cli), and it moves in the *noisier* direction |
| should-quiet-6/-7 FP'ing on feature-incompleteness ("declared but not wired") | the fleet reaches past the diff into whether the surrounding feature is finished — a scope/axis question, not a defect judgment |
| should-quiet-2/-5 FPs landing on *neighbouring* files (caller, test file, mock) rather than the diff's own lines | out-of-diff reach is a recurring FP source in this baseline |
| catch-rate 15/15 with zero detected-below-threshold | the axis-instability that produced v2.9's autoescape miss did not reproduce under this harness |

---

## 6. Provenance recap

- **Seals.** SEAL1 = `4c67283b46540f997b8a5c6b530996da880b53ed`;
  SEAL2 = `633f1dd0daa24b823d8abab7cff00823a3c2b256`. Manifest commit budget == 2, and the pinned
  canonical verifier (`verify-seal2-append.py` @ `a407539115872137dc55d99aef439a9c5a4f16d9`,
  sha256 `7be8ed39…75daaf`, executed from its introducing-commit blob) proved on raw bytes that
  SEAL2 is SEAL1 plus exactly the ordered five-line whitelist suffix.
- **Key blobs.** Carried rows scored from
  `git show ef0ab67cb45957167c99eff468077348432e1474:docs/design/b3-ground-truth/ANSWER-KEY-b3.md`
  (sha256 `1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1`); new rows from
  `git show 5f687d95f9be4fef2c0fcd78491c308d4c3861e8:docs/design/b3-ground-truth/ANSWER-KEY-v2.10.md`
  (sha256 `f58f888c9f4dc86d0e34d5a152c781cb7e9913087405e6e25980bd77e3d753d4`). Both digest-verified
  twice, both key commits ancestors of HEAD. No live key file was a scoring input.
- **Denominators.** `DENOM_CATCH_RUNS: 15`, `DENOM_QUIET_RUNS: 21`, `DENOM_TOTAL_RUNS: 36`, parsed
  from the SEAL2 blob only.
- **Run inputs.** Every scored value came from `runs-v2.10/<id>/run-<n>/state.json`
  `passes[-1].findings[]` — no transcript, no recomputed band or score. All 36 runs are isolated
  (`len(passes)==1`), pinned (`head_sha == sealed base_sha`), and full-diff-integrity-verified
  against proven-sealed sidecars.
- **PINNED HARNESS TUPLE.** `pin-claude-code: 2.1.261 (Claude Code)` · `pin-codex: codex-cli 0.153.4`
  · `pin-model: fable 5`. Every one of the 12 committed fingerprints byte-equals the claude-code and
  codex pins, and the **normalized model value is `fable 5.1` across ALL sessions** — one model, one
  CLI harness, no cohort split. The two commits that ever set a `pin-*` line (`0d5b677`, `62419f9`)
  precede the first fingerprint and every run capture.
- **Sealed v2.9 archive.** `git diff v2.9 --quiet -- docs/design/b3-ground-truth/runs/` → exit 0, and
  porcelain clean, at scoring time.
- **Measured plugin.** The executable/prompt surface of `plugins/vibe-check/` is byte-identical to
  tag v2.9; the only post-SEAL1 change under that path is the non-executable
  `docs/efficacy/ULTRAREVIEW-SHADOW.md`. All fingerprints record the installed
  `…/thejuran/vibe-check/2.9.0` cache-root the runs resolved helpers from.
- **Session → run coverage.** See the §1(9) table: 10 governing sessions, each named by its SID and
  its introducing-commit sha, covering all 36 runs; 2 further committed fingerprints govern no run
  (recorded N-08 / N-09 recovery events).
- **Parser notes (campaign-discovered, recorded for re-derivation).** The pass-level codex record is
  schema-nondeterministic across passes of the same shipped command — observed as a `codex_joined`
  bool, a `codex` object in several field shapes (`joined`/`status` × `verdict` × `findings` ×
  `cross_confirmed`), a plain string, and outright absence *with* a codex-adversarial finding
  present. Codex participation here is therefore inferred from
  `findings[].agent == "codex-adversarial"`. Pass timestamps appear in two formats (`…Z` and
  microseconds + explicit offset); both are parsed offset-aware. One archived finding carries an
  empty `title` (should-quiet-3 run-2, `transfer.py`:259) and is scored on file:line + explanation.
  These are Phase-40 orchestration-nondeterminism inputs, not scoring defects.
- **Driver split (recorded for the limitations section of 38-06).** Runs 1-10 were owner-pasted from
  `RUN-CHECKLIST-v2.10.md`; for runs 11-36 the assistant executed the checklist blocks
  (fence-validated, byte-exact) at owner direction, with the owner performing session launch,
  `/model`, `/clear`, `/deep-review`, and the fix-loop decline. The only block deviations are the
  N-06/N-07/N-10 one-line `STATE_FILE` substitutions, each logged per occurrence. The artifacts are
  identical in form either way, and this gate ladder is the independent check.
