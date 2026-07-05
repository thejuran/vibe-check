# B3 Scoring worksheet — per-run SITE/AXIS/BAND verdicts (Wave 3, 36-03)

The auditable trail behind the headline catch-rate / FP-rate. Every aggregate in
`plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` is re-derivable from the raw
`runs/<id>/run-<n>/state.json` + the committed answer-key blob using only the rows below.

**Scored:** 2026-07-05. **Scoring input:** `state.passes[-1].findings[]` (D-06 — never a
transcript), against the committed answer-key BLOB (never the live working file).
**Scoring code frozen:** `score.py` / `test_score.py` / `config.py` byte-unchanged this phase
(no band/score was recomputed — read from state, ROBUST-01).

---

## 1. Pre-registration gate results (all hard gates PASS)

Every proof value below was DERIVED from git history and the committed manifest blob at
`MANIFEST_COMMIT`, not trusted from the live working files. The gate EXITS NON-ZERO on any
failure; it completed with all hard gates (0, a, b, e) holding and step (f) clean.

### (0) MANIFEST ORDERING + DERIVATION (codex pass-4 fix 1)

| Check | Command | Result |
|---|---|---|
| `FIRST_RUNS_COMMIT` (oldest commit touching `runs/`) | `git log --reverse --format='%H' -- docs/design/b3-ground-truth/runs/ \| head -1` | `eca98ec178209c3568088f4f630eb8882acd33d1` (short `eca98ec`) — non-empty ✓ |
| No post-run manifest edit | `git log FIRST_RUNS_COMMIT..HEAD -- …/PREREGISTRATION.md` | **EMPTY** ✓ (no manifest commit after the first runs/ commit) |
| No manifest+runs same-commit landing | `git show --name-only --format= <run-commit>` for every runs/ commit | PREREGISTRATION.md listed by **none** ✓ |
| `MANIFEST_COMMIT` (last manifest commit strictly preceding `FIRST_RUNS_COMMIT`) | `git log -1 --format='%H' "FIRST_RUNS_COMMIT^" -- …/PREREGISTRATION.md` | `cca63e27eccd4b359d27d50d344fea3925a9634e` (short `cca63e2`) — non-empty ✓ |

**Proof fields read from `git show MANIFEST_COMMIT:docs/design/b3-ground-truth/PREREGISTRATION.md`**
(the committed manifest blob whose ordering is proven — NEVER the live manifest):

- `ANSWER_KEY_COMMIT = ef0ab67cb45957167c99eff468077348432e1474`
- `ANSWER_KEY_SHA256 = 1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1`

### (a) Key ancestry

`git merge-base --is-ancestor ef0ab67 HEAD` → **exit 0** ✓ — the pre-registered key commit is an
ancestor of HEAD; scoring is provable in this history.

### (b) Key-blob digest (EXIT-NON-ZERO-on-mismatch)

`git show ef0ab67:docs/design/b3-ground-truth/ANSWER-KEY-b3.md | shasum -a 256`
= `1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1`
== manifest-blob `ANSWER_KEY_SHA256` → **DIGEST MATCH** ✓. (On mismatch the task would have
EXITED NON-ZERO and refused to score — the recorded proof matching git history is the
measurement-honesty seal, T-36-08.)

### (c) Score-from-blob

The committed key was materialized to a scratch path
(`git show ef0ab67:docs/design/b3-ground-truth/ANSWER-KEY-b3.md > <scratch>/answer-key-scored.md`,
150 lines) and EVERY scored input — the SITE/AXIS/BAND rows, each row's `base_sha`, the
D-07/D-08/D-09 rules, and the D-11 decision table — was parsed FROM THAT BLOB. The live working
`ANSWER-KEY-b3.md` was never a scoring input (T-36-03: a post-run edit to the live key is inert).

### (d) Live-file sanity (WARNING-only, does not gate)

- `git show ef0ab67:…/ANSWER-KEY-b3.md | diff - …/ANSWER-KEY-b3.md` → **EMPTY** ✓ — live key
  IDENTICAL to the pre-registered blob (no drift).
- `git show cca63e2:…/PREREGISTRATION.md | diff - …/PREREGISTRATION.md` → **EMPTY** ✓ — live
  manifest IDENTICAL to the `MANIFEST_COMMIT` blob (no drift).

(Scoring reads only the blobs, so even a drifted live file would not invalidate the numbers — the
gate records that here regardless.)

### (e) Runs-clean + run-descent (codex pass-3 fix 2 + pass-4 fix 1)

- `git status --porcelain docs/design/b3-ground-truth/runs/` → **EMPTY** ✓ — no uncommitted run
  artifacts (T-36-16).
- Every commit touching `runs/` (19 commits) descends from BOTH `ANSWER_KEY_COMMIT` (ef0ab67) AND
  `MANIFEST_COMMIT` (cca63e2): `git merge-base --is-ancestor <key|manifest> <run-commit>` → exit 0
  for all ✓.
- Equivalence: `git log ef0ab67 --oneline -- docs/design/b3-ground-truth/runs/` → **prints
  nothing** ✓ — no runs/ content existed at or before the key commit (pre-registration ordering
  intact).

### (f) Per-diff FULL-worktree tree.diff integrity (codex pass-3 fix 3 + pass-5 fix 1)

`tree.diff` is the FULL tracked diff (`git diff`, NO pathspec). For each diff, all three per-run
`tree.diff.sha256` are IDENTICAL to each other AND equal the kit-build `EXPECTED_TREE_DIFF_SHA256`
from the diff's `.provenance` sidecar (each sidecar also matches the SHA-256 of its own archived
`tree.diff` blob). Result: **all 6 diffs PASS, 0 unscoreable from tree.diff** (T-36-13).

| diff-id | kit EXPECTED_TREE_DIFF_SHA256 | run-1 | run-2 | run-3 |
|---|---|---|---|---|
| triggarr-secret-in-logs | `f0c70a02…0424ff2` | ✓ | ✓ | ✓ |
| triggarr-autoescape | `4fdadb70…70bb89a` | ✓ | ✓ | ✓ |
| third-organic-should-catch | `d9918036…b1ad7790` | ✓ | ✓ | ✓ |
| should-quiet-1 | `a8137f5d…a17d37a` | ✓ | ✓ | ✓ |
| should-quiet-2 | `3cb198dc…d731f0d` | ✓ | ✓ | ✓ |
| should-quiet-3 | `66fe1425…8dfeae69` | ✓ | ✓ | ✓ |

### Security spot-check (T-36-05)

The FIRST secret-in-logs run's archived state (`runs/triggarr-secret-in-logs/run-1/state.json`)
was scanned for a literal *arr API key in the captured `current_code` snippets before bulk-scoring.
The buggy line is `logger.warning(..., exc=exc)` — `exc` is an exception OBJECT, so no literal key
should be captured. **Result: CLEAN** — zero 20+-char tokens in any `current_code`, zero
`api_key=<literal>` assignments in the state file. No scrub needed.

---

## 2. Scoreable-completeness ledger (T-36-20, codex pass-5 fix 3 — NO AGGREGATION OVER HOLES)

Isolation + pin gate applied to every run: `len(state['passes']) == 1` AND
`state['passes'][-1]['head_sha'] == the row's base_sha`. A run failing either — or failing the (f)
tree.diff check — is `unscoreable` and BLOCKS aggregation. **All 18 expected runs (6 diffs × 3)
passed both checks and the tree.diff check → 3/3 scoreable per diff, ZERO holes.** Aggregation is
authorized WITHOUT any owner waiver.

| diff-id | role | base_sha (row) | run-1 | run-2 | run-3 | scoreable |
|---|---|---|---|---|---|---|
| triggarr-secret-in-logs | should-catch | `f4366a2` | len=1,head=f4366a2 ✓ | len=1,head=f4366a2 ✓ | len=1,head=f4366a2 ✓ | **3/3** |
| triggarr-autoescape | should-catch | `e11187e` | len=1,head=e11187e ✓ | len=1,head=e11187e ✓ | len=1,head=e11187e ✓ | **3/3** |
| third-organic-should-catch | should-catch | `3db8b48` | len=1,head=3db8b48 ✓ | len=1,head=3db8b48 ✓ | len=1,head=3db8b48 ✓ | **3/3** |
| should-quiet-1 | should-quiet | `98eb419` | len=1,head=98eb419 ✓ | len=1,head=98eb419 ✓ | len=1,head=98eb419 ✓ | **3/3** |
| should-quiet-2 | should-quiet | `84aff27` | len=1,head=84aff27 ✓ | len=1,head=84aff27 ✓ | len=1,head=84aff27 ✓ | **3/3** |
| should-quiet-3 | should-quiet | `1027691` | len=1,head=1027691 ✓ | len=1,head=1027691 ✓ | len=1,head=1027691 ✓ | **3/3** |

**Owner waiver:** NONE (and none needed — the set is complete). The two archived
`should-quiet-1/run-2.failed-*` directories are Wave-2 D-06 recovery artifacts (unscoreable runs
that were repeated), NOT part of the expected 18-run set; they are excluded here by construction
(only `run-1/run-2/run-3` are enumerated per diff).

---

## 3. Per-run scoring — should-catch diffs (D-07 three-gate rule)

A **catch** requires SITE (right file + within the planted hunk, keyed to the row's base_sha) AND
AXIS (the finding names the key's required MECHANISM — not merely a defect at the right location)
AND BAND (rendered band ≥ the row's floor). SITE-only, or SITE+AXIS-below-band, =
`detected-below-threshold` = a MISS in the headline (A16). `attribution` records whether Codex
contributed each catch (D-13).

### 3.1 triggarr-secret-in-logs — SITE `triggarr/clients/base.py` : 230-238 / 249-256 · AXIS = secret/API-key/PII leaked into logs (NOT "log formatting") · BAND floor = warning

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=f4366a2 ✓ | ✓ | `security/data-exposure` L250 [warning] "ValidationError logged raw, embedding untrusted API response content"; `codex-adversarial` L232 [warning] "exception strings can leak URLs and response data into logs" | ✓ | ✓ (response/URL secret leak) | ✓ (warning ≥ warning) | **catch** | ✓ |
| 2 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L232 [critical] "Raw HTTPStatusError logging can leak URL credentials" (compliance L232 [warning] corroborates) | ✓ | ✓ (credential leak) | ✓ (critical) | **catch** | ✓ |
| 3 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L232 [critical] "leak URL credentials and response contents" (architecture L252 [critical] "bypasses _sanitize_exc convention" corroborates) | ✓ | ✓ (credential/response leak) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 3/3 catch.**

### 3.2 triggarr-autoescape — SITE `triggarr/web/routes.py` : 42-48 (line 45) · AXIS = XSS surface re-enabled / autoescape NO-OPs (must name escaping/XSS; NOT "deprecation"/"refactor"/"breaks startup") · BAND floor = warning

| run | isolation | tree.diff | finding(s) at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=e11187e ✓ | ✓ | architecture L45 [critical] "reverts fix to **deprecated env_options pattern**"; impact L45 [warning] — its problem text EXPLICITLY states **"this is NOT an XSS regression"**, frames it as deprecation/TypeError-on-removal; compliance/framework name "deprecated pattern"; codex L45 [critical] "**unsupported keyword breaks startup**" | ✓ | ✗ — every finding names deprecation/refactor/startup, NONE names the autoescape-off / XSS mechanism | (band n/a — axis failed) | **detected-below-threshold (MISS)** — right-site-wrong-axis (D-07/A16) | ✓ (but wrong axis) |
| 2 | len=1,head=e11187e ✓ | ✓ | `security/xss` L45 [critical] "reintroduces fragile autoescape config, risking silent **XSS** on future Starlette upgrade" | ✓ | ✓ (XSS / autoescape) | ✓ (critical) | **catch** | ✓ |
| 3 | len=1,head=e11187e ✓ | ✓ | `impact/breaking-api` L45 [critical] "reverts autoescape fix … forward-compat **XSS regression**"; framework-fastapi [warning] names the autoescape fragility | ✓ | ✓ (XSS / autoescape) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 2/3 catch** (run-1 = detected-below-threshold MISS — the pre-registered subtle
right-site-wrong-axis case: the fleet saw the reverted line but framed it as a deprecation nit, not
the XSS surface. This is the axis-instability signal, see §5.)

### 3.3 third-organic-should-catch — SITE `src/angular/src/app/services/files/view-file.service.ts` : 304-311 (307-309) · AXIS = unclamped percentage / missing `Math.min(100,…)` clamp / >100% · BAND floor = medium

| run | isolation | tree.diff | winning finding at SITE | SITE | AXIS | BAND | verdict | Codex |
|---|---|---|---|---|---|---|---|---|
| 1 | len=1,head=3db8b48 ✓ | ✓ | `bugs/logic-error` L308 [critical] "label exceed 100% for extracted files"; `language-typescript` L307 [critical] "removed Math.min(100,…) clamp reintroduces >100% bug" | ✓ | ✓ (missing clamp / >100%) | ✓ (critical ≥ medium) | **catch** | ✓ |
| 2 | len=1,head=3db8b48 ✓ | ✓ | `bugs/logic-error` L308 [critical] "percentDownloaded exceed 100%"; impact L307 [critical] "removing Math.min(100) clamp lets percentDownloaded exceed 100" | ✓ | ✓ (missing clamp / >100%) | ✓ (critical) | **catch** | ✓ |
| 3 | len=1,head=3db8b48 ✓ | ✓ | `bugs/logic-error` L308 [critical] "progress percent can exceed 100% after clamp removal"; language-typescript [critical] names the reverted clamp fix | ✓ | ✓ (missing clamp / >100%) | ✓ (critical) | **catch** | ✓ |

**Per-diff: 3/3 catch.**

---

## 4. Per-run scoring — should-quiet diffs (D-08 FP rule)

An **FP** on a should-quiet diff = ANY finding with band **critical OR warning** (the tool's own
action bar — NOT site-gated). **Medium/low** findings = noise-notes (recorded, not counted).
**clean** = no critical/warning findings.

### 4.1 should-quiet-1 — `triggarr/web/validation.py` : 79-91 · Safe ON: SSRF / input-validation (the diff TIGHTENS the host block-list) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=98eb419 ✓ | ✓ | bugs L87 [critical, score 100] "IPv4-mapped IPv6 bypass of BLOCKED_HOSTS"; security/ssrf L85 [warning, 82]; impact L87 [critical, 97]; codex L85 [critical, 100] | **FP** |
| 2 | len=1,head=98eb419 ✓ | ✓ | bugs L87 [critical, 100]; security/ssrf L85 [critical, 97]; codex L80 [warning, 90] | **FP** |
| 3 | len=1,head=98eb419 ✓ | ✓ | bugs L87 [critical, 100]; bugs L85 [warning, 84]; codex L85 [critical, 100, attr security+codex]; impact/quality L87 [warning, 90] | **FP** |

**Per-diff: 3/3 FP.** Honest note: these fire at score 82-100, mostly single-lane
self-sufficient (bugs alone = 100) — NOT band crossings rescued by the +10 cross-confirm. Multiple
independent lanes (bugs / security / impact / codex) all flag the same SSRF site as a *remaining*
bypass on a diff that TIGHTENS the block-list. See §5 (H-CORE / H-LANE).

### 4.2 should-quiet-2 — `src/angular/src/app/services/utils/rest.service.ts` : 53-63 · Safe ON: API contract / typing (`post(url)` widened to `post(url, body?)`) · any critical/warning = FP

| run | isolation | tree.diff | findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=84aff27 ✓ | ✓ | 0 findings | **clean** |
| 2 | len=1,head=84aff27 ✓ | ✓ | 0 findings | **clean** |
| 3 | len=1,head=84aff27 ✓ | ✓ | 0 findings | **clean** |

**Per-diff: 0/3 FP** (0 findings all 3 runs — the tool stayed silent as pre-registered).

### 4.3 should-quiet-3 — `src/roonseek/transfer.py` : 201-218, 220, 256-257 · Safe ON: HTTP-client / path-injection / error-handling (URL-encodes both segments, preserves default status set, API key never logged) · any critical/warning = FP

| run | isolation | tree.diff | critical/warning findings | verdict |
|---|---|---|---|---|
| 1 | len=1,head=1027691 ✓ | ✓ | impact L259 [warning] "empty success_statuses falls back to {200,201}"; test-sufficiency L209 [critical] "cancel_download only tested for HTTP 204 — the 200/202 cases untested" | **FP** |
| 2 | len=1,head=1027691 ✓ | ✓ | codex L204 [critical] "unvalidated identifier does not match slskd's transfer id contract" | **FP** |
| 3 | len=1,head=1027691 ✓ | ✓ | impact L259 [warning] "success_statuses=set() silently falls back to {200,201}"; codex L209 [warning] "202 Accepted treated as terminal cancel success" | **FP** |

**Per-diff: 3/3 FP.** These are cross-lane and diverse per run (test-sufficiency coverage-gap,
impact default-fallback semantics, codex id-contract/status-semantics) — the H-LANE / B-SEV
pattern rather than one correlated twin. See §5.

---

## 5. Aggregation (D-09, no rounding) + failure-mode → challenge mapping

**Headline catch-rate = 8/9** (should-catch runs): secret-in-logs 3/3 + autoescape 2/3 +
unclamped-% 3/3 = 8 catches / 9 should-catch runs.

**Headline FP-rate = 6/9** (should-quiet runs): should-quiet-1 3/3 + should-quiet-2 0/3 +
should-quiet-3 3/3 = 6 FP runs / 9 should-quiet runs.

**Codex contribution (D-13):** Codex contributed a surviving finding to all 8 catches (present in
the catch's finding set). Codex ran `codex=auto` (shipped default — no `--codex` forcing).

**Failure-mode → pre-registered challenge (from the D-11 table in the committed blob):**

| Observed failure mode | Pre-registered challenge |
|---|---|
| autoescape catch fraction 2/3 with the miss = right-site-wrong-axis / axis-below-the-XSS-framing (band was above floor but the *axis* the fleet named was deprecation, not XSS) — an unstable per-diff fraction on the same planted item | **B-REWEIGHT** (unstable per-diff catch fractions) **with B-SEV** (label/axis instability near the threshold) |
| should-quiet-1 FP 3/3 — multiple independent lanes (bugs/security/impact/codex) all fire critical/warning on the same SSRF site; self-sufficient scores (not cross-confirm-rescued) | **H-CORE** (agents emit the finding at the source — filtering is agent-side) + **H-LANE** (one item multi-lane-reported) |
| should-quiet-3 FP 3/3 — cross-lane noise (test-coverage / default-semantics / id-contract) on a clean boundary-add | **H-LANE** + **B-SEV** (borderline warnings crossing the action bar) |

(The full verdict — proceed / don't / need-more-data — is computed in RESULTS-v2.9.md against the
same D-11 table.)

---

## 6. Provenance recap

- Key rows, base_shas, and the D-07/D-08/D-09/D-11 rules were parsed from
  `git show ef0ab67:docs/design/b3-ground-truth/ANSWER-KEY-b3.md` (digest-verified), NOT the live
  file.
- Every scored value came from `runs/<id>/run-<n>/state.json` `passes[-1].findings[]` — no
  transcript, no recomputed band/score.
- All 18 expected runs are isolated (len(passes)==1) and pinned (head_sha == base_sha) and
  full-diff-integrity-verified; the set is complete (3/3 per diff), so the headline numbers span
  the FULL pre-registered denominators (9 catch runs, 9 quiet runs) with no owner waiver.
