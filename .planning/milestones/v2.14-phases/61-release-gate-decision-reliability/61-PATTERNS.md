# Phase 61: Release gate — decision reliability - Pattern Map

**Mapped:** 2026-10-30
**Files analyzed:** 10 (2 shipped-tree edits, 8 planning/release records)
**Analogs found:** 10 / 10

This phase builds no feature. Every artifact is a version string, a README release section, or a record/proposal/notes document. The analogs are prior release and gate artifacts (v2.12 Phase 54, v2.13 release f2b6a36, Phase 49 runbook, Phase 60 records).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `plugins/vibe-check/.claude-plugin/plugin.json` | config (version) | transform (one field) | same file as bumped in f2b6a36 (2.12.0 → 2.13.0) | exact |
| `README.md` (§Measured Efficacy, §Limitations, config `min_confidence` row) | docs / release notes (test-coupled) | transform | `README.md` L28-51 + L344-352 + L152 (the v2.13 rewrite, commit f2b6a36) | exact |
| `61-RELEASE-RECORD.md` (gate results G1-G9, D-11 route map, residuals, waivers) | record | batch (gate outputs → table) | `.planning/milestones/v2.12-phases/54-freeze-release-gates-integration-audit/54-RELEASE-READINESS.md` + `60-REPRO.md` §"Suite at close" (L342-361) | exact |
| `61-SIGNOFF.md` (one plain-terms page, D-09; may be a section of the record) | record (owner checkpoint) | request-response (owner rules) | `54-RELEASE-READINESS.md` §4 "Claims that must be omitted" + `60-HUMAN-UAT.md` ruling format | role-match |
| `61-LIVE-SMOKE-PROPOSAL.md` (D-01 bounded proposal) | proposal | request-response (approval gate) | `.planning/milestones/v2.12-phases/54-freeze-release-gates-integration-audit/54-REVIEW-PROPOSAL.md` + `54-BUDGET.md` §1 unit table (L21-29) | exact |
| `61-LIVE-SMOKE.md` (procedure + evidence: snapshot, cache parity, park-memory, S1-S3, sha256s) | runbook / evidence record | event-driven (tmux sessions) | `docs/design/b3-ground-truth/RUN-PHASE49-v2.11.md` §park-memory (L526-551), §resync-cache (L622-664), §a4-smoke (L667-739) | exact |
| D-03 PR-fetch check (inline fence in a plan / recorded output in the record; no committed script needed) | utility (scripted check) | file-I/O + network | 61-RESEARCH.md §D-03 fence (verified); `diff_ranges.py` stdin→JSON CLI | exact |
| `v2.14` GitHub release notes file (scratch, `--notes-file`) | release notes | transform | `gh release view v2.13` body | exact |
| Release commit / PR #7 body | commit message | — | `git show f2b6a36` message | exact |
| `61-HUMAN-UAT.md` / `61-VERIFICATION.md` (publish = human_needed/pending close) | record | request-response | `.planning/phases/60-exact-change-evidence-and-reliable-finalize/60-HUMAN-UAT.md`; `.planning/milestones/v2.13-MILESTONE-AUDIT.md` (human_needed waiver pattern) | exact |

## Pattern Assignments

### `plugins/vibe-check/.claude-plugin/plugin.json` (config)

**Analog:** same file. Current content (whole file, 9 lines):
```json
{
  "name": "vibe-check",
  "description": "Vibe-check your diff — GSD-aware parallel code review with model tiering and intent-doc awareness.",
  "version": "2.13.0",
  ...
}
```
Change only `"version": "2.13.0"` → `"2.14.0"`. No marketplace edit (pins `ref: main`, no version field). No test asserts the version. Commit together with README (f2b6a36 precedent: "Bump plugin to 2.13.0 and add README release notes ... (fact-checked against shipped code and phase records)").

---

### `README.md` (release notes, test-coupled)

**Analog:** current README (v2.13 rewrite from f2b6a36).

**Lead paragraph pattern** (L30):
```markdown
**v2.13 (this release) — fixes close reliably, decisions stick, answers are acted on. Not measured.** 2.13 is a closure-and-recovery release. ... It was not B3- or holdout-measured, so there are **no v2.13 false-alarm or catch numbers**; the last measured result is still v2.11's, below. Each change below was first reproduced as a failing test on the previous code and is covered by regression tests (3,588 passing at release).
- **Fixed findings close.** ...
```
New: add `**v2.14 (this release) — ... Not measured.**` paragraph above it with 2-4 bold-lead bullets; relabel L30 to `**v2.13 (previous release) — ...**` (as L36 did for v2.12). Fill the passing count from G1 on candidate C.

**Limitations bullet pattern** (L344-352): `- ⚠️ **Known limitations (2.13):**` with nested plain-language bullets. Per RESEARCH: drop bullets 1, 2, 3, 6 (fixed by 59/60), keep the wordy-references (999.26) and live plain-English bullets, change the downgrade bullet to "2.14 → 2.13 untested" (2.14 adds `nearby_spots`). Add 2.14 limits (R7 untracked files, R17 large PRs, R10 `--all`, R4 one re-ask after upgrade, routes not run live).

**Config row** (L152): delete the trailing `(except a finding grouped under a deferred row; see Known limitations)` clause.

**Test coupling (must stay true):** `test_recovery_pairs.py` requires "every later run that reviews changes" (present at L342) and forbids "gets **one** automatic independent re-check"; `test_gitguard.py::TestBoundaryDecision` reads the git-guard boundary sentence (L338). Do not edit those bullets. Run a README fact-check against shipped code before freezing C (v2.13 found 5 overstated claims).

---

### `61-RELEASE-RECORD.md` (record, gate results)

**Analog:** `54-RELEASE-READINESS.md` (113 lines).

**Header pattern** (L1-7): one-paragraph scope statement, then a bold "Code under consideration" line binding SHAs:
```markdown
**Code under consideration:** candidate `ddbfff4` (HEAD `50347a0`, evidence-only commits on top; `git diff ddbfff4 HEAD` on plugins and all tools is empty). ... `plugin.json` already reads `2.12.0`.
```
Use the same for C (bumped 2.14.0) and the D-12 freshness assert.

**Test-run table pattern** (L29-36):
```markdown
**Local test runs on HEAD 50347a0, 2026-10-17:**

| Suite | Result |
|---|---|
| plugin (`plugins/vibe-check/scripts`) | **2961 passed** |
```
Extend to G1-G9 rows (gate / command / result / pass-fail), from 61-RESEARCH §Gate Commands.

**Raw-output block pattern** (`60-REPRO.md` L342-361):
```
All runs are from `plugins/vibe-check/scripts` in the real checkout at HEAD `ec0c9d8`.

$ pytest -q -p no:cacheprovider
3765 passed, 4930 subtests passed in 170.01s (0:02:50)
```
followed by bullets: "0 failed", "Replay deltas ... none observed", "GOLDEN_DIGEST is unchanged (`TestGolden` passes in the full run)". Copy this for G1/G4/G5a verbatim outputs.

**Reusable-checks + omitted-claims pattern** (54-RELEASE-READINESS L50-71): a "Checks" table (`| Check | Covers | Reusable for |`) and "Claims that must be omitted" bullets. Use the latter for "not measured / routes not run live / R6 checked once".

**Carried-items pattern** (L96-104): `**Carried (maintenance/speculative, per the scope rule):**` bullet list. Use for D-07 non-qualifying items + the two thin spots (range: 1 test; pause/resume: no end-to-end walk). Link 59-REPRO R1-R8 / 60-REPRO R1-R26, do not walk them.

---

### `61-SIGNOFF.md` (plain-terms owner page, D-09)

**Analog:** `54-RELEASE-READINESS.md` §4 + §5 style (L64-71, L106-113): short declarative bullets, bold verdict words, no code. Ruling capture format from `60-HUMAN-UAT.md` L20-23:
```markdown
### 2. Owner ruling: PR route fails closed on very large PRs (R17 ...)
expected: Explicit ruling — accepted limit, or fallback needed
result: pass
ruling: Accepted known limit, no fallback. ...
```
Required content (D-09): pass/fail per gate, live-smoke outcome, replay differences (expected none), user-visible limits (same 3-6 bullets as D-08), Dependabot note (D-10: alerts 403-disabled, CLI lacks scope, runtime stdlib-only per G8 scan; pytest is test runner only), waiver text for everything not proven live.

---

### `61-LIVE-SMOKE-PROPOSAL.md` (bounded proposal)

**Analog:** `54-REVIEW-PROPOSAL.md` (58 lines). Copy the skeleton:
```markdown
# Proposal: independent review of the 21 post-review files (NOT APPROVED)

Status: proposal only, 2026-10-17. Nothing runs until the owner explicitly approves this budget. Publishing remains unauthorized.

## Scope
## Method
## Fixed budget requested: $45 total (API-rate estimate)
| Part | Estimate | Cap |
**Basis:** measured from transcripts. ...
**Stop rules:**
## What this does NOT trigger
```
Adaptation: owner rule is "estimates are not spending caps" (memory: costed-decisions, caps REJECTED) — replace the `Cap` column with `Estimate` only and stop rules keyed to events (invalid-run retry once; qualifying failure → D-05; oddity → D-07). Cost basis rows from `54-BUDGET.md` L21-29:
```markdown
| Live review run (B3-style deep review, Fable top tier, ~6 subagents) | median **$7.30–9.50**, max $13.80 | the 16 runs of the 24c0c00 sweep |
| Containment proof (probe + review session) | **$6.30–8.50** | 12 proof pairs on 10-17 |
| Coordinator (main) session | $5–60 per working day | |
```
"What this does NOT trigger": no GSD/range/PR/incremental live runs (D-02), no second fix round (D-06), no publish.

---

### `61-LIVE-SMOKE.md` (runbook + evidence)

**Analog:** `docs/design/b3-ground-truth/RUN-PHASE49-v2.11.md`.

**park-memory** (L532-551) — move aside, refuse twice, assert gone:
```bash
PARKDIR=$HOME/.b3/automemory-parked-phase49-$LABEL-$(date +%s)
...
    mv "$M" "$PARKDIR/$C"
...
  test ! -e "$M" || { echo "~/$C AUTO-MEMORY STILL PRESENT — STOPPING"; exit 1; }
```
For 61: one throwaway repo, park between S1→S2→S3 (`~/.b3/automemory-parked-phase61-<epoch>-sN`).

**resync-cache** (L634-664) — backup once outside the plugin cache, rsync, chmod, parity, relaunch:
```bash
  cp -Rp "$CACHE" "$CACHE_BAK"
  diff -rq -x .in_use "$CACHE" "$CACHE_BAK" > /dev/null \
    || { echo 'CACHE BACKUP DIFFERS FROM THE CACHE — STOPPING'; exit 1; }
rsync -a --delete --exclude .in_use --exclude __pycache__ --exclude '*.pyc' \
  --exclude .pytest_cache "$PLUGIN_ROOT/" "$CACHE/"
chmod -R u+w "$CACHE"
...
echo 'RELAUNCH CLAUDE CODE (FULL PROCESS EXIT) BEFORE preflight'
```
Note L627: "A version string proves nothing here" — parity is content hashes both directions. 61 has no MANIFEST.json; use a two-direction `diff -rq` (or sha256 list) between `$PLUGIN_ROOT` and `$CACHE` with the same excludes. Backup path: `~/.b3/vibe-check-2.13.0.bak-pre-phase61`.

**a4-smoke throwaway repo + tmux launch** (L700-735):
```bash
A4_DIR=$HOME/.b3/a4-scratch-$(date +%s)
test ! -e "$A4_DIR" || { echo 'THE A4 SCRATCH DIR ALREADY EXISTS — STOPPING'; exit 1; }
mkdir "$A4_DIR"
git -C "$A4_DIR" init -q -b main
git -C "$A4_DIR" config user.email a4@example.invalid
git -C "$A4_DIR" config user.name a4-smoke
printf '.turingmind/\n' >> "$A4_DIR/.git/info/exclude"
...
  tmux new-session -d -s "p49-a4" -c "$A4_DIR"
  tmux send-keys -t "p49-a4" "$LAUNCH_LINE" Enter
```
For 61: `~/.b3/smoke61-<epoch>`, tmux `s61-N`, launch `claude --permission-mode manual --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent" --plugin-dir "$PLUGIN_ROOT"` (Phase 49 measured sessions used `--plugin-dir` from a sealed snapshot; a4 deliberately omitted it). Accept workspace-trust prompt once (L677-679 wording). Every block uses `STOPPING` refusal lines and ends `echo 'BLOCK OK'`.

**Evidence binding** (Phase 49 §2 + RESEARCH Pitfall 9): transcripts stay out of git; record sha256 of each `~/.claude/projects/<slug>/*.jsonl`, the captured card line, REVIEW.md sha256, BLOBFILE=/GATEFILE= lines, provenance grep (paths under `$PLUGIN_ROOT` or parity cache only). A wrong-provenance run is invalid, not a failure.

---

### D-03 live PR fetch check (scripted, free)

**Analog:** 61-RESEARCH.md §D-03 fence (L203-221), already run on PRs #4/#5/#6. Core lines:
```bash
  gh pr diff "$1" --color never > "$OUT/pr$1.diff"
  python3 "$H" < "$OUT/pr$1.diff" > "$OUT/pr$1.gh.json"
  git diff --no-color --no-ext-diff --no-textconv --no-relative --src-prefix=a/ --dst-prefix=b/ \
    "$base" "$merge" | python3 "$H" > "$OUT/pr$1.local.json"
  cmp "$OUT/pr$1.gh.json" "$OUT/pr$1.local.json" && echo "PR #$1: IDENTICAL ..."
```
Run on C for PR #6 and #4 (renames). Record output in the release record; do not commit a new script (no-growth). Offline counterpart stays `test_diff_ranges.py::TestRoutePR` on `fixtures/pr-cumulative.diff`.

---

### v2.14 GitHub release notes (`--notes-file`)

**Analog:** `gh release view v2.13` body. Structure:
```text
Closure-and-recovery release. Not measured: no B3 or holdout run, so there are no v2.13 false-alarm or catch numbers. v2.11 (5/18 · 15/15, MISS) remains the last measured result. Reviewer prompts and the scoring formula are unchanged.

Contents:
- **Fixed findings close.** ...
- **Your decisions stick.** ...

Known limitations: <one run-on sentence> ... Full list in the README.

Each change was first reproduced as a failing test on the previous code. 3,588 tests passing at release.
```
Change for 2.14 (D-08): "Known limits" becomes a short 3-6 item bullet list (not a run-on sentence), and include the live-validation statement (default route + Finalize run live; others offline; PR fetch checked once). Title pattern: `v2.14 — Decision reliability`. Use `gh release create v2.14 --verify-tag --latest --notes-file <scratch file>` (v2.13 missed this step).

---

### Release commit / PR #7 body

**Analog:** `git show f2b6a36` sub-commit message:
```text
release: vibe-check 2.13.0 — reliable fix closure and recovery

Bump plugin to 2.13.0 and add README release notes and 2.13 known
limitations (fact-checked against shipped code and phase records).
Not B3-measured; suite 3588 passed, 0 failed.
```
Archive commit pattern: `chore: archive v2.13 milestone files` with audit summary line (`Audit tech_debt: 14/14 requirements, integration 6/6, suite 3588/0.`). End with the attribution trailer from the session reminder.

---

### `61-HUMAN-UAT.md` / verification

**Analog:** `60-HUMAN-UAT.md` (41 lines): YAML frontmatter (`status`, `phase`, `source`, `started`, `updated`), `## Tests` numbered `### N.` items with `expected:` / `result:` / `evidence:` or `ruling:`, `## Summary` counts, `## Gaps`. Publish/"ships" clause of GATE-03 recorded as human_needed / pending close, mirroring `v2.13-MILESTONE-AUDIT.md` L67 ("human_needed, owner-approved") and its `judgement_calls` frontmatter (L15-23) for any strict-vs-audit reading.

## Shared Patterns

### Fences
**Source:** memory (orchestrator-fences-zsh-wordsplit) + 61-RESEARCH §Gate Commands.
**Apply to:** every command in every plan.
- Wrap in `bash -s <<'BASH' … BASH`, `set -euo pipefail`.
- Bare `pytest -q -p no:cacheprovider` from `plugins/vibe-check/scripts` (never `python3 -m pytest`).

### SHA binding of every verdict
**Source:** `54-RELEASE-READINESS.md` L7, `60-REPRO.md` L344.
**Apply to:** release record, sign-off, smoke evidence. State the commit each result ran on ("at HEAD `<sha>`"), the D-12 assert `git diff --quiet C HEAD -- . ':(exclude).planning'`, and post-squash tree identity (61-RESEARCH §Code Examples).

### STOPPING refusals
**Source:** `RUN-PHASE49-v2.11.md` blocks (e.g. L637, L688-694).
**Apply to:** smoke and release-mechanics fences: `test … || { echo '<REASON IN CAPS> — STOPPING'; exit 1; }`. Never proceed on a failed precondition.

### Plain-terms owner pages
**Source:** `54-RELEASE-READINESS.md` §4/§5, v2.13 release body.
**Apply to:** sign-off page, proposal, release notes, README. Pass/fail + user impact; no code; "Not measured" stated explicitly; never claim live coverage that did not happen.

### Planning-file commits
`.planning/` is gitignored: `git add -f <path>`; commit one path at a time (Phase 49 `commit_one` idea, L509). No transcripts committed — sha256 only.

## Conventions

Convention derivation skipped (no-app-files): `verify conventions --derive --scope plugins/vibe-check/scripts` returned `{"skipped":true,"reason":"no-app-files"}` — the scope is Python/markdown. No new code files are expected this phase, so it does not matter here; any fix-round code (D-05) matches the local style of the file it touches (stdlib-only, `unittest`-based tests, snake_case).

Contested hotspots (author's choice): the CJS<->SDK dual-resolver split (`bin/lib/**` CJS vs `sdk/src/**` ESM) belongs to the bm tooling, not this repo; nothing in Phase 61 touches it.

## No Analog Found

None. Every artifact has a direct precedent. Differences from the analogs to watch:
- No `MANIFEST.json` for the snapshot (Phase 49 had one) → use a direct two-direction diff for parity.
- Proposal has no spending cap column (owner rejected caps).
- Tag goes on `origin/main` after the squash, not on the branch tip (complete-milestone's `git_tag` step would tag the wrong commit).

## Metadata

**Analog search scope:** `.planning/milestones/v2.12-phases/54-*`, `.planning/milestones/v2.13-*`, `.planning/phases/60-*`, `docs/design/b3-ground-truth/RUN-PHASE49-v2.11.md`, `README.md`, `plugins/vibe-check/.claude-plugin/plugin.json`, commit f2b6a36, `gh release view v2.13`
**Files scanned:** 10
**Pattern extraction date:** 2026-10-30
