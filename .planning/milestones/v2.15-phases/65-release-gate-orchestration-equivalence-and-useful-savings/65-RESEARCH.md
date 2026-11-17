# Phase 65: Release gate — orchestration equivalence and useful savings - Research

**Researched:** 2026-11-15
**Domain:** Release gating of a stdlib-only Claude Code plugin (offline equivalence checks against a pinned baseline, byte/step recount, one bounded live smoke, publish via the existing close workflow)
**Confidence:** HIGH (every command below was run in this session on `main` at `6d9bae3`, whose `plugins/` tree equals the Phase 63 code; the only unverified parts are the live smoke and the future candidate commit, which do not exist yet)

## Summary

Phase 65 builds no feature. It re-runs checks that already exist on one exact commit (the 2.15.0 candidate C: `main` plus a version bump in `plugins/vibe-check/.claude-plugin/plugin.json` and a rewritten README release block), writes a release record and a one-page sign-off, runs one owner-approved live smoke (default review + `--finalize`, 3 sessions), and publishes through the same 10-step close runbook used for 2.14.0. The v2.14 Phase 61 gate is a direct template: its plan split (candidate → proposal → free gates → live smoke → sign-off and runbook), its smoke mechanics (sealed read-only worktree snapshot, cache backup + rsync + two-direction parity diff, `--plugin-dir`, tmux, manual permission mode, parked auto-memory) and its runbook all carry over with path and version substitutions.

Every offline check was dry-run in this session on today's `main` and passes: replay diff against `v2.14.1` (170 runs, 0 differing), replay guardrail (REGRESSED 0), `check-manifest`, `baseline_records.py verify --scripts-dir` (`baseline holds`), `finalize_capture.py verify` and `compare --driver helper` (`finalize outcome fields match (5 situations, 7 walks)`), the 10 MANIFEST fingerprints (10 of 10 match), the stdlib-only check (34 files, none third-party), the left-out list guard, and `claude plugin validate`. The direct recount (D-06) of 2.14.1 and HEAD gives, for the first time, 2.14.1 figures for all six paths. Every byte of review-path growth at HEAD reconciles exactly to the itemised Phase 63 D-09 rows (table below); the review paths also grew by **+2 counted steps each**, which the D-09 rows explain (X2 +1, X3 +4, X4–X6 −3) but which the owner has so far seen only as "Finalize path" steps. The release notes block (D-05) must show those step increases, not only the bytes.

Two findings change how the planner should set things up. (1) The full suite must run in the **main checkout** on the Mac, not in an executor's linked worktree (`use_worktrees: true` in config). In a worktree, 5 replay tests fail and 1 skips because the private recordings are local-only (Phase 63 hit this in every executor run). (2) D-07's WR-02 reproduces mechanically in one fresh-shell fence walk (shown below: `STATE_FILE=.turingmind/state/format-53/.json`). Whether it qualifies under the four-class rule depends on showing the chain to a wrong close, and on comparing with 2.14.1 the same way. That reproduction should run **before** candidate C is built, because a qualifying result opens the one fix round and changes C.

**Primary recommendation:** Copy Phase 61's five-plan shape, with the D-07 reproduction added to wave 1. Run every gate fence from the main checkout as `bash -s <<'BASH' … BASH` on the 40-hex candidate SHA read from `65-CANDIDATE.md`. Report counts from a direct recount of `dd8e4ab` and C, never from records.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Candidate build (version bump, README release block) | Repo (git, plugin manifest) | — | `plugin.json` is the one version field Claude Code reads; README is outside `plugins/` and not loaded at review time |
| Offline equivalence (suite, replay, five situations, mode/recovery) | Local test tooling (pytest, `replay.py`, `finalize_capture.py`, `baseline_records.py`) | CI (`offline-suite.yml`) as the standing check | Must run on the owner's Mac main checkout (private recordings, Mac-only tests); CI cannot cover the D-18/D-20 tests |
| Byte/step counts | `footprint.py` + `step_count.py` reading git objects at a revision | — | Read-only; `--rev` reads committed blobs, so working-tree noise cannot leak in |
| Live smoke | Installed plugin cache + fresh `claude` processes in tmux | Throwaway repo under `~/.b3/` | Only a real model session shows that the model follows the rewritten Finalize and printed-state-path instructions |
| Release record / sign-off / notes | `.planning/` (gitignored, committed via `bm-sdk query commit` / `git add -f`) | GitHub release body | Owner reads one page; ledgers linked |
| Publish | GitHub (`gh pr`, tag on `origin/main`, `gh release create`) | Marketplace pins `ref: main`; `claude plugin update` | Squash merge means the tag must go on `origin/main`, never on the branch tip |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Carried forward (locked — do not re-litigate)
- **Pass rule (Phase 62 D-01–D-03):** at least one of the two Finalize-path counts (`footprint.py` bytes loaded; `step_count.py` rule v1 model-run steps) drops and neither grows. No percentage target; nothing is cut to reach a number. Helper code and tests are a separate "maintenance added" figure. Byte/step figures are always reported separately from tokens or dollars; no billing-savings claim without comparable usage evidence (Phase 62 cost note D-12).
- **Same behaviour (Phase 62 D-07/D-08, Phase 63 D-15):** the five Finalize situations (`clean-close`, `card-first`, `one-rebuild`, `refused-close`, `fresh-shell-restart`), the full offline suite and the archived replay match the pinned 2.14.1 baseline (`docs/design/lean-v2.15/baseline/`) on every outcome field; the recorded command lists are the intended difference. Any other difference is named and explained or it blocks. `stable_hash` / GOLDEN_DIGEST frozen.
- **Accepted differences (Phase 63 owner go + D-19, D-24–D-28):** the deliberate differences already accepted by name in `63-RESULT.md` ("Your decision" items 1–5, the D-27 60-second git limit as the sixth, and the D-19 subfolder behaviour) are expected and do not block. Anything not on that list does.
- **Mac-only tests (Phase 62 D-18/D-20):** the five CI-deselected tests and the Linux self-skipping tests run on the owner's Mac at this gate, where the baseline has 0 skips.
- **Gate placement and candidate:** every gate check runs on the final release commit (version already bumped to 2.15.0, the commit that will be tagged); any later production-code change re-runs all checks (Phase 61 D-12 pattern). Gates run before the publish plan (owner, 2026-10-01). Install resync to the candidate + relaunch before any manual/live check.
- **Release mechanics:** a completed milestone always publishes (ff/merge `main`, push main + tag, `gh release create`; marketplace pins `ref: main`). One branch/PR: `feat/v2.15-phase-65` from `main`, deleted locally and on GitHub after merge. Dependabot alerts are disabled on thejuran/vibe-check and `gh` lacks the scope; the release record states this plus that shipped scripts are stdlib-only (test tooling such as pytest separated), no setting change.
- **Standing rules:** no growth per round; work added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow; each check starts by recording current behaviour; every lock lands with a mutant; paid/live runs need a separately approved bounded proposal.

#### Live validation (GATE-06)
- **D-01:** The gate includes one bounded live smoke run, under a written proposal the owner approves before anything is spent. Shape as in 2.14 (Phase 61 D-01): about 3 sessions, est. $20–30 (unit cost ~$6–9 per review session, 54-BUDGET.md). Purpose: prove the model follows the rewritten Finalize instructions (call the helper, act on its structured result) and the shared state-path printing from fresh shells — which offline tests cannot show.
- **D-02:** Smoke scope is the **default route + Finalize** only: resync install → on a throwaway repo, review → decide a finding → `--finalize` writes REVIEW.md. The fix loop (X8), `--all` (C1) and the other routes rest on offline proof; the release record and notes name them as not run live, under an explicit owner waiver.
- **D-03:** The assistant drives the sessions via tmux, manual permission mode, with the clone's auto-memory parked before any measurement session (Phase 61 D-04 pattern). The owner approves the proposal and sees the results.

#### Review-path growth
- **D-04:** The plain/deep review (and other review-path) growth from the Phase 63 owner-chosen fixes (plain 192,057 → 193,267 bytes; deep 268,997 → 270,219 at `d56232b`) is **accepted as named growth**, not a block. Phase 62 D-06's "prove they did not grow" check becomes: re-measure every review path on the candidate and show it grew by nothing beyond the itemised Phase 63 D-09 items (file, bytes, steps, commit, reason). Any unitemised growth blocks. The owner signs it on the sign-off page.
- **D-05:** The release notes carry one short "What changed in size" block showing both sides: the Finalize drop (steps and bytes, 2.14.1 → candidate) and every review path's ~0.6% growth from the named safety/state-path fixes. Labelled as bytes and steps, not tokens or cost.

#### Carried review items
- **D-06 (999.34 WR-02/WR-03):** Bypass and carry. The gate does not rely on the two lenient Phase 62 checks: it recounts 2.14.1 and the candidate directly from their commits with `step_count.py` and `footprint.py` and confirms the fingerprints in `docs/design/lean-v2.15/baseline/MANIFEST.json` are unchanged (same method as Phase 63 D-13). The two checks stay in backlog.
- **D-07 (999.38):** One offline attempt to reproduce WR-02 (an empty phase id making every phase in a repo share one saved-progress file), by the Phase 60 fresh-shell standard. If it reproduces as data loss or a wrong close, it qualifies under the four-class rule and goes to the owner as the D-08 fix round. Otherwise it is carried. WR-03, WR-04, SA-01, SA-03 are carried as accepted at the Phase 63 go; any that a user can see is named as a known limit.

#### Gate failure handling
- **D-08:** A qualifying failure (four classes) in any gate check — offline suite, archived replay, the five Finalize situations, mode/recovery checks, review-path growth, or the live smoke — gets ONE fix round: a before/after case plus a mutant per fix, then a full gate re-run on the new candidate. If it still fails, do not ship; record and re-scope.
- **D-09 (hard cap):** No second fix round without the owner's explicit go, given with the reproduction in front of them. The workflow never opens one on its own.
- **D-10:** Anything outside the four classes is carried as a named known limit in the release record and backlog, and the release continues.

#### Release record and sign-off
- **D-11:** The 2.15.0 release notes say "same behaviour as 2.14.1 except:" followed by the user-visible accepted differences in plain words (e.g. a review on a folder/branch name containing `$`, a backtick, `"` or `\` now stops with a message; Finalize from a subfolder now closes findings correctly; a git call slower than 60 seconds leaves a finding open; one "Permission denied" line no longer shows), plus a 3–6 bullet "Known limits" section (e.g. fix loop and `--all` not run live). The full difference and residual lists live in the release record.
- **D-12:** Before release the owner signs off on one plain-terms page: pass/fail per gate check, the live-smoke outcome, the two counts (Finalize down; review paths' named growth), replay and situation differences (expected: only the accepted ones), the D-07 outcome, user-visible limits, the Dependabot/stdlib note, and waiver text for routes not run live. Detailed ledgers are linked, not walked through. The owner gives go or no-go.

### Claude's Discretion
- Throwaway-repo design for the smoke and what the smoke checks to call it a pass (e.g. REVIEW.md written, gate result and card behaviour as expected, no stop).
- Which existing tests make up the mode/recovery integration checks (default, GSD, range, PR, `--all` recorded status, incremental pass ≥2, `--finalize` incl. one rebuild and the no-write stop, pause/resume, fix loop) and how results are grouped.
- Release record file name/layout (e.g. `65-RELEASE-RECORD.md`), sign-off page wording, release-notes wording.
- How the version bump and release PR ride with the close workflow, provided every check runs on the commit that is tagged.
- Plan count and split (gates-first, publish plan last with the owner's pre-push checkpoint).

### Deferred Ideas (OUT OF SCOPE)
- 999.34 WR-02/WR-03 tightening of the lenient baseline checks — carried (D-06).
- 999.38 WR-03, WR-04, SA-01, SA-03 — carried; WR-02 carried unless D-07 reproduces it.
- Live runs of the fix loop and `--all` — not in this smoke (D-02); waived.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GATE-04 | On the exact release candidate, the full offline suite, archived replay and mode/recovery integration checks pass against the 2.14.1 baseline; any unexpected behavioural difference blocks release | §Gate Commands G1–G5, G10; §Mode/recovery map; §Pitfall 1 (main checkout); accepted-difference list in §Accepted differences |
| GATE-05 | The release record shows safeguards and independent fix verification intact and a demonstrated reduction in loaded prose or mechanical steps, with byte/operation savings reported separately from tokens or dollars and no billing-savings claim without comparable usage evidence | §Gate Commands G6–G9; §Counts and D-09 reconciliation; §"What changed in size" block; safeguards = GOLDEN_DIGEST, replay guardrail, fix-verification tests (`test_verified_fixes.py`, `test_confirmed_fix.py`, `test_fixcheck.py`) |
| GATE-06 | Live validation of changed orchestration paths runs only under an approved bounded proposal; otherwise the unmeasured behaviour is documented and released under an explicit owner waiver | §Live smoke (proposal, mechanics, pass criteria, evidence, restore); §Waiver text |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

No `./CLAUDE.md` in the repo. No `.claude/skills/` or `.agents/skills/`. Directives in force come from the owner's global CLAUDE.md and the project memory:

- **Security (absolute):** no secrets hardcoded; never log tokens or PII. Session transcripts hold the owner's global instructions, so **never commit `.jsonl` transcripts**; record only their sha256 (Phase 61 Pitfall 9).
- **Releases:** before the version bump, review open Dependabot alerts/PRs. On this repo that review cannot run (verified this session: alerts API returns HTTP 403 "Dependabot alerts are disabled for this repository"; `gh pr list --author app/dependabot` needs `admin:repo_hook`). Record this and the stdlib-only note; change no setting (memory: vibe-check-dependabot-disabled).
- **Division of labour:** owner approval is not code review. Verification comes from tests and live runs. Owner decisions (smoke spend, fix round, waiver, go/no-go) go through AskUserQuestion in the main session. Never relay them from an agent.
- **Planning format:** keep STATE.md authoritative (`last_updated` refreshed); follow `~/Documents/Codex/planning/PLANNING-FORMAT.md` when editing STATE/ROADMAP.
- **Memory rules that bind this phase:** milestone close always publishes (and `gh release create` — a tag alone leaves the page stale); gates run before the publish plan; one branch/PR per phase `feat/v2.15-phase-65`, deleted after merge; orchestrator fences run as `bash -s <<'BASH' … BASH` (zsh does not word-split); bare `pytest` works, `python3 -m pytest` does not (verified: Homebrew Python 3.14 has no pytest module; `pytest` is a pipx install on Python 3.12.12); park auto-memory before measurement sessions; install is chronically stale (verify content parity, then relaunch); a release needs `gh release create`; scope discipline (four classes only); executors refuse relayed push approval, so publish from the main session.

## Standard Stack

No new packages. Everything is in the repo or already installed.

### Core (in-repo tools)
| Tool | Location | Purpose | Verified this session |
|------|----------|---------|-----------------------|
| `step_count.py` (rule v1) | `docs/design/lean-v2.15/tools/` | model-run steps per path/file at `--rev` | dd8e4ab: finalize 92; HEAD: 85 |
| `footprint.py` | `plugins/vibe-check/scripts/` | declared bytes per mode path at `--rev` | dd8e4ab finalize 136114; HEAD 130886 |
| `finalize_capture.py` | `docs/design/lean-v2.15/tools/` | five Finalize situations: `verify` (record intact) and `compare --driver helper --commit <sha>` | both pass at HEAD in ~2 s each |
| `baseline_records.py` | `docs/design/lean-v2.15/tools/` | `verify --repo . [--scripts-dir …]` → `baseline holds` | pass, 3 s |
| `replay.py` | `plugins/vibe-check/scripts/` | `diff --base rev:v2.14.1`, `candidate`, `check-manifest`, `census` | 170/0, REGRESSED 0, exit 0, 12 transcripts |
| `stdlib_only.py`, `left_out_guard.py` | `.github/scripts/` | stdlib-only runtime; left-out list = recorded five | `34 shipped .py files; third-party imports: none`; `left-out list matches the recorded five` |

### Environment tools
| Tool | Version (verified) | Use |
|------|--------------------|-----|
| pytest | 9.0.3 (pipx, Python 3.12.12 — same as baseline record) | suite; call bare `pytest` |
| python3 | 3.14.5 (Homebrew) | run the tools (stdlib only) |
| git | 2.55.0 | recount at revisions, worktree snapshot |
| tmux | 3.7c | drive live sessions |
| gh | 2.86.0 | PR, merge, tag check, release |
| claude | 2.1.325 | `plugin validate`, `plugin update`, live sessions |

**Installation:** none.

## Package Legitimacy Audit

Not applicable: this phase installs no external package. pytest 9.0.3 is already installed and is test-only, and the shipped plugin is stdlib-only (verified: `stdlib_only.py` → 34 files, no third-party imports).

## Architecture Patterns

### System Architecture Diagram

```
 main (6d9bae3, plugins == Phase 63 code)
   │  branch feat/v2.15-phase-65
   ▼
 [D-07 WR-02 fresh-shell repro] ──qualifies?──yes──► owner go (D-08) ─► one fix round ─┐
   │ no → carried as known limit                                                        │
   ▼                                                                                    │
 [Candidate C] plugin.json 2.15.0 + README 2.15.0 block ──► 65-CANDIDATE.md (40-hex) ◄──┘
   │
   ├──► [Free gates on C, main checkout]  G1 suite · G2 Mac-only ids · G3 mode/recovery
   │        G4 replay vs v2.14.1 · G5 five situations · G6 recount dd8e4ab vs C
   │        G7 fingerprints/GOLDEN · G8 stdlib+left-out · G9 manifest valid · G10 frozen files
   │        G11 instruction-diff surface · G12 CI green on PR head
   │        └─► 65-RELEASE-RECORD.md (raw output blocks, D-09 reconciliation)
   │
   ├──► [Smoke proposal] ──owner APPROVED?──no──► waiver text
   │                        │yes
   │                        ▼
   │     [Live smoke on sealed snapshot of C] cache backup → rsync → parity → tmux S1..S3
   │        (review → decide → --finalize) → evidence (sha256s, printed lines, provenance)
   │        → restore cache → 65-LIVE-SMOKE.md (PASS / QUALIFYING FAILURE / INVALID)
   │
   ▼
 [Sign-off] 65-SIGNOFF.md + 65-RELEASE-NOTES.md + 65-CLOSE-RUNBOOK.md ──owner go/no-go──►
   ▼
 [Close] verify-work → audit-milestone → complete-milestone (skip its tag) → freshness assert
   → PR (owner OK) → squash → tree-identity assert → tag v2.15 on origin/main → gh release
   → remote verify → claude plugin update + relaunch → branch cleanup → STATE/ROADMAP
```

### Recommended plan split (mirrors Phase 61, adds D-07)

| Plan | Wave | Autonomous | Content |
|------|------|-----------|---------|
| 65-01 | 1 | yes | D-07 WR-02 reproduction (offline, fresh shell, both 2.14.1 and HEAD), classify against the four classes; writes `65-REPRO-WR02.md`. A qualifying result stops with a checkpoint for the owner's D-08 go. |
| 65-02 | 1 | no (owner checkpoint) | `65-LIVE-SMOKE-PROPOSAL.md` and the owner's approve/decline (AskUserQuestion in the main session). Does not need C. |
| 65-03 | 2 | yes | Candidate C: create `feat/v2.15-phase-65` from `main`, bump `plugin.json` to 2.15.0, write README 2.15.0 block (D-11 differences, known limits, "What changed in size", test count), fact-check table, README-coupled tests + full suite on the edited tree, commit exactly those two files, `65-CANDIDATE.md` (`candidate: <40-hex>`). Depends on 65-01 so the known limits reflect D-07. |
| 65-04 | 3 | yes | Free gates G1–G12 on C → `65-RELEASE-RECORD.md` |
| 65-05 | 3 | yes (gated on APPROVED) | Live smoke on a sealed snapshot of C → `65-LIVE-SMOKE.md`, cache restored |
| 65-06 | 4 | no (owner sign-off) | Release notes, close runbook, sign-off page, owner go/no-go, STATE update |

Publish runs at milestone close from `65-CLOSE-RUNBOOK.md`, as in Phase 61. `/bm:complete-milestone` needs every phase complete, so it cannot run inside the phase. If the planner prefers a 65-07 publish plan, it must be `autonomous: false` with the owner's pre-push checkpoint, and it must run from the main session: executors refuse relayed push approval (memory v2.11).

**Branch note:** the Phase 65 context commit `6d9bae3` is already on `main`. Create `feat/v2.15-phase-65` from `main` before the first code commit (the C commit). Planning-only commits can ride on the branch.

### Pattern 1: Every gate fence reads C from the candidate file and runs under bash
**What:** The Bash tool here is zsh. Each fence runs as `bash -s <<'BASH' … BASH` with `set -euo pipefail`, and each reads C from `65-CANDIDATE.md` and never retypes it. Lookups tolerate the moved-phase path with `|| true` (a Phase 61 close hit a silent abort under pipefail).
```bash
# Source: 61-CLOSE-RUNBOOK.md preamble (adapted)
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
CAND=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md \
          .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md 2>/dev/null || true; } | head -1)
test -n "$CAND" || { echo "65-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
test "$(git rev-parse HEAD)" = "$C" || { echo "HEAD IS NOT THE CANDIDATE — STOPPING"; exit 1; }
test -z "$(git status --porcelain -- plugins README.md docs .github)" || { echo "DIRTY TREE — STOPPING"; exit 1; }
echo "on candidate $C"
BASH
```

### Pattern 2: Recount both commits directly (D-06, Phase 63 D-13)
Never copy a figure from a record. Print each figure from the tool at the commit.

### Anti-Patterns to Avoid
- **Running the suite in a linked worktree** (executor default with `use_worktrees: true`): 5 `test_replay.py::TestPhase53SameLineRegressionCases` failures and 1 skip appear that are not real. Run G1/G2 in the main checkout.
- **`python3 -m pytest`:** Homebrew `python3` (3.14.5) has no pytest. Use bare `pytest`.
- **Comparing pass counts with the baseline's 3886:** the candidate adds tests (Phase 63: helper, parity grid, cross-call, name guard, isolated-Python). Equivalence for the suite means **0 failed, 0 errors, 0 skipped**, not equal pass counts. State the pass-count change and why.
- **Tagging the branch tip:** a squash merge leaves it off `main`. Tag `origin/main` after the tree-identity check, and skip complete-milestone's own tag step.
- **Building the smoke snapshot from the working tree:** use `git worktree add --detach <SNAP> <C>`, then `chmod -R a-w`.
- **Trusting a version string for cache parity:** only `diff -rq` both ways counts.

## Gate Commands (verified this session on `main` = Phase 63 code)

Run from the main checkout `/Users/julianamacbook/turingmind-code-review` unless stated. Each in `bash -s <<'BASH' … BASH`.

| # | Gate | Command | Result today (HEAD 6d9bae3) | Pass condition on C |
|---|------|---------|-------------------------------|---------------------|
| G1a | Full suite, README/baseline form | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider` | *(see G1 note)* | 0 failed, 0 errors, **0 skipped**; count goes into README "N passing at release" |
| G1b | Full suite, CI set without the deselect | from repo root: `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools -rs --junitxml=<scratch>/suite.xml` | *(see G1 note)* | 0 failed, 0 errors, 0 skipped |
| G2 | Mac-only tests by id (D-18 five + D-20 two) | `pytest -q -p no:cacheprovider -rs $(cat .github/ci-left-out-tests.txt) 'plugins/vibe-check/scripts/test_lanearchive.py::TestSandboxTempRoot::test_real_sandbox_root_tmp_and_private_tmp_forms' 'plugins/vibe-check/scripts/test_replay.py::TestReconstruction::test_transcript_recovery_covers_survivor_agents'` | — | 7 passed, 0 skipped (proves they ran, not skipped) |
| G3 | Mode/recovery integration | selector in §Mode/recovery map | — | 0 failed |
| G4a | Replay complete-output diff vs 2.14.1 | `cd plugins/vibe-check/scripts && python3 replay.py diff --base rev:v2.14.1 --scorer path:$PWD/score.py --out <scratch>/diff.md` (no `--allow`) | exit 0; `runs compared: 170`, `runs differing: 0`, `runs with unallowed differences: 0` | same |
| G4b | Replay catch guardrail | `python3 replay.py candidate --name gate65 --scorer path:$PWD/score.py --out <scratch>/cand.md` | exit 0; `REGRESSED 0` under "Guardrail — 26 protected catch runs" | same |
| G4c | Replay manifest + census | `python3 replay.py check-manifest`; `python3 replay.py census` | exit 0; `transcripts: 12`, `scoreable: 66` | same (12 = main-checkout condition) |
| G4d | Baseline kit replay re-derive | `python3 docs/design/lean-v2.15/tools/baseline_records.py verify --repo . --scripts-dir plugins/vibe-check/scripts` | `baseline holds` | same |
| G4e | Replay tests | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_replay.py` | (inside G1) | 0 failed, 0 skipped |
| G5a | Five situations: record intact | `python3 docs/design/lean-v2.15/tools/finalize_capture.py verify --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json` | `finalize baseline matches (5 situations)` | same |
| G5b | Five situations on C's instructions | `python3 docs/design/lean-v2.15/tools/finalize_capture.py compare --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json --driver helper --commit "$C"` | exit 0; last line `finalize outcome fields match (5 situations, 7 walks)`; intended differences = command lists only | same; any `differs` line not in the accepted list blocks |
| G6 | Direct recount, six paths, both commits | §Counts fence below | see table | Finalize: steps 92→85, bytes 136114→130886 (both down); review paths: growth == itemised D-09 sum exactly |
| G7 | Fingerprints (D-06) | §Fingerprint fence below; `git diff --quiet d0adb5b "$C" -- docs/design/lean-v2.15/baseline`; GOLDEN_DIGEST literal equals `git show v2.14.1:…/test_score.py` | 10 of 10 match; folder unchanged since Phase 62 merge (exit 0); `7a516d01…3124` in both | same |
| G8 | Stdlib-only + left-out list | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`; `python3 -I .github/scripts/left_out_guard.py check-list .github/ci-left-out-tests.txt` | `34 shipped .py files; third-party imports: none`; `left-out list matches the recorded five` | same |
| G9 | Plugin manifest valid | `claude plugin validate plugins/vibe-check` | `✔ Validation passed` | same; version reads 2.15.0 |
| G10 | Frozen scorer/replay | `git diff --quiet v2.14.1 "$C" -- plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/test_replay.py` | exit 0 (identical) | exit 0 |
| G11 | Instruction-diff surface | `git diff --name-only v2.14.1 "$C" -- plugins/vibe-check/phases plugins/vibe-check/commands plugins/vibe-check/agents plugins/vibe-check/templates` | exactly the 9 files in §Counts | same 9 files, nothing else |
| G12 | CI on the PR head | `gh pr checks <PR>` / `gh run list --branch feat/v2.15-phase-65` | — | `offline-suite` green on the head commit (standing check; expect `… passed, 2 skipped, 5 deselected`) |

**G1 note:** G1b today in the main checkout: `4595 passed, 2 warnings, 6474 subtests passed in 359.99s`, 0 skipped, 0 failed (details in §Validation Architecture).

Not needed this time: Phase 61's live PR-fetch gate (G6 there). `diff_ranges.py` is unchanged since 2.14.1 (absent from `git diff --stat v2.14.1 HEAD -- plugins/`), so its live check from 2.14.0 still stands. State that in the record rather than re-running it.

### Fingerprint fence (D-06; same method as 63-COUNTS "10 of 10")
```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
python3 -I - <<'PY'
import hashlib, json, os, sys
base = "docs/design/lean-v2.15/baseline"
m = json.load(open(os.path.join(base, "MANIFEST.json")))
ok = 0
for name, want in sorted(m["files"].items()):
    got = hashlib.sha256(open(os.path.join(base, name), "rb").read()).hexdigest()
    ok += got == want
    print("match" if got == want else "DIFFERS", name)
print("%d of %d match MANIFEST.json" % (ok, len(m["files"])))
sys.exit(0 if ok == len(m["files"]) else 1)
PY
git diff --quiet d0adb5b HEAD -- docs/design/lean-v2.15/baseline && echo "baseline folder unchanged since Phase 62 merge d0adb5b"
BASH
```
Verified today: 10 of 10 match. Folder unchanged since `d0adb5b`. `baseline_commit` in MANIFEST = `dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4`.

### Counts fence (D-06 direct recount, D-04 every review path)
```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
C=<read from 65-CANDIDATE.md as in Pattern 1>
for r in dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4 "$C"; do
  echo "== $r"
  python3 plugins/vibe-check/scripts/footprint.py --rev "$r" --json \
    | python3 -I -c 'import json,sys; d=json.load(sys.stdin); print({k: v["bytes"] for k, v in d.items()})'
  for m in finalize review-plain deep-plain review-all deep-all fix-loop; do
    printf '%s steps: ' "$m"
    python3 docs/design/lean-v2.15/tools/step_count.py --rev "$r" --mode "$m" --json \
      | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["totals"]["model_run_steps"])'
  done
done
# per-file bytes for every changed instruction file
for f in $(git diff --name-only dd8e4ab "$C" -- plugins/vibe-check/phases plugins/vibe-check/commands plugins/vibe-check/agents plugins/vibe-check/templates); do
  a=$(git show "dd8e4ab:$f" | wc -c); b=$(git show "$C:$f" | wc -c); echo "$f $a $b $((b-a))"
done
BASH
```
(Per-file steps: `step_count.py --rev <r> --mode finalize --json` → `files[].path / files[].model_run_steps`.)

### Counts today (HEAD = Phase 63 code; C should equal these because it changes only plugin.json + README)

| Path | Bytes 2.14.1 | Bytes HEAD | Δ bytes | Δ % | Steps 2.14.1 | Steps HEAD | Δ steps |
|------|-------------|-----------|---------|-----|-------------|-----------|---------|
| Finalize | 136,114 | 130,886 | **−5,228** | −3.8% | 92 | 85 | **−7** |
| Plain review | 192,057 | 193,267 | +1,210 | +0.63% | 36 | 38 | +2 |
| Deep review | 268,997 | 270,219 | +1,222 | +0.45% | 42 | 44 | +2 |
| Plain review `--all` | 284,926 | 286,385 | +1,459 | +0.51% | 45 | 47 | +2 |
| Deep review `--all` | 361,866 | 363,337 | +1,471 | +0.41% | 51 | 53 | +2 |
| Fix loop | 255,070 | 256,444 | +1,374 | +0.54% | 112 | 114 | +2 |

[VERIFIED: footprint.py/step_count.py --rev, this session] The 2.14.1 figures for `--all`, fix loop and every review-path step count were "not recorded" in 63-RESULT. They are recounted here for the first time.

**Reconciliation with the Phase 63 D-09 items (per file, bytes 2.14.1 → HEAD):**

| File | Δ bytes measured | Itemised D-09 rows (63-COUNTS) | Sum | Match |
|------|------------------|--------------------------------|-----|-------|
| phases/review/00-scope.md | +380 | X1 +211, D-21 +169 | +380 | yes |
| phases/review/05-state.md | +869 | X2 +110, X3 +82, X2+X3 +245, D-21 +432 | +869 | yes |
| phases/review/06-config.md | −39 | X4/X5/X6 −13 each | −39 | yes |
| phases/review/05-state-all.md | +249 | D-22 +6, D-23 +243 | +249 | yes |
| phases/review/50-fix-loop.md | +164 | D-20 +124, D-22 +9, D-23 +31 | +164 | yes |
| phases/shared/90-finalize.md | −6,438 | extraction −6,663, D-20 +185, D-22 +9, D-23 +31 | −6,438 | yes |
| phases/deep-review/2c-codex-kickoff.md | +6 | D-22 +6 | +6 | yes |
| phases/deep-review/30-codex-collect.md | +3 | D-22 +3 | +3 | yes |
| phases/deep-review/01d-coverage.md | +3 | D-22 +3 | +3 | yes |

Steps: every path that loads `05-state.md` and `06-config.md` (all six) gets X2 +1, X3 +4 and X4–X6 −3, net **+2**. The Finalize path is −9 (extraction) + 2 = −7. No other step changed. **Nothing is unitemised today.** On C, G6 passes if these figures are unchanged (C should touch only `plugin.json` under `plugins/`; assert `git diff --name-only HEAD-at-branch-point "$C" -- plugins` lists only `plugins/vibe-check/.claude-plugin/plugin.json`).

**D-05 wording consequence:** "~0.6% growth" is accurate only for the plain review (0.63%). The other paths are 0.41–0.54%, and every review path also gained **2 counted steps** (plain review 36 → 38 is +5.6% in steps). The "What changed in size" block should give a range ("+0.4% to +0.6% bytes and +2 counted steps on each review path") or a per-path line. Otherwise the notes understate the step growth. Flag this on the sign-off page (the owner signs D-04 knowing the step figure).

### Suite run (G1b form, main checkout, this session)
`4595 passed, 2 warnings, 6474 subtests passed in 359.99s (0:05:59)`, 0 skipped, 0 failed. See §Validation Architecture.

## Mode/recovery map (GATE-04 "mode/recovery integration checks")

Every class below was confirmed to exist at HEAD (`grep "^class <Name>"`). Phase 61's selectors still resolve. Two Finalize helper files from Phase 63 belong in the Finalize rows now, because Finalize's mechanics moved into `finalize_inputs.py`.

| Route / path | Tests (file::class) | Strength |
|---|---|---|
| Default (uncommitted) | `test_diff_ranges.py::TestRouteDefault`, `test_diff_ranges.py::TestShapesRealGit`, `test_statepath.py::TestDefaultModes` | Good; also the live-smoke route |
| GSD | `test_diff_ranges.py::TestRouteGSD`, `test_diff_ranges.py::TestScopePhaseStartFence`, `test_statepath.py::TestGsdMode`, `test_codex_gate.py::TestGsdRange`, `test_pasted_name_guard.py` (GSD key) | Adequate |
| Range (`A..B`) | `test_diff_ranges.py::TestRouteRange` (1 test), `test_codex_gate.py::TestRange` | **Thin** (stated limit, unchanged since 2.14) |
| PR | `test_diff_ranges.py::TestRoutePR`, `test_diff_ranges.py::TestRefusals` | Good (live fetch checked at 2.14.0; `diff_ranges.py` unchanged) |
| `--all` (recorded status) | `test_diff_ranges.py::TestRouteAll`, `test_statepath.py::TestAllMode`, `test_state_shape.py::TestAllOnlyKeys`, `test_nv_render.py`, `test_cross_call_vars.py::TestRepro63::test_c1_all_mode_close_out_state_file`, `…::test_c1_all_mode_fix_loop_state_file` | Unsupported fixture: `--all` keeps no decisions (stated limit) |
| Incremental pass ≥2 | `test_diff_ranges.py::TestRouteIncremental`, `test_diff_ranges.py::TestStateHeadShaFence`, `test_carry_state.py::TestLastHeadSha` | Good |
| `--finalize` happy path | `test_finalize_card.py` (all classes), `test_finalize_gate.py`, `test_finalize_archive_prose.py`, `test_finalize_inputs.py`, `test_finalize_parity_grid.py`, `test_scope_args.py::TestFinalizeMode`, `test_scope_args.py::TestFinalizeStrip` | Good |
| `--finalize` one rebuild | `test_finalize_card.py::TestFinalizeFreshShellWalk::test_retry_mints_new_blobfile_after_missing_path`, `…::test_stale_earlier_attempt_file_does_not_govern`, `…::test_post_decision_rerun_decides_on_fresh_counts`, `…::test_post_decision_recount_refingerprints_head` | Good (fresh-shell walks) |
| `--finalize` no-write stop | `TestFinalizeFreshShellWalk::test_counts_fence_without_literal_exits_two`, `…::test_counting_line_stays_on_screen`, `…::test_report_failure_stops_at_once`, `test_carry_state.py::TestNoWritePath`, `test_state_shape.py::TestNoWritePath` | Good. (Phase 61's `test_malformed_gatefile_shows_only_stop_sentence` no longer exists: the gate file is gone. Its replacements are the three walk tests above, per 63-REMOVAL-LEDGER.) |
| Pause/resume | `test_fix_loop_card.py::TestFixLoopCard` (incl. `test_paused_lines_exactly_once`), `test_fix_loop_card.py::TestCarrierRoundTrip`, `test_pause_batching.py` | **Thin** (stated limit, unchanged) |
| Fix loop | `test_fix_loop_card.py`, `test_confirmed_fix.py`, `test_verified_fixes.py`, `test_fixcheck.py`, `test_fixcommit.py`, `test_fixstage.py`, `test_cross_call_vars.py::TestRepro63::test_x8_fix_loop_state_file` | Good |
| Cross-call / printed state path | `test_cross_call_vars.py`, `test_inline_python_isolated.py`, `test_pasted_name_guard.py` | Good |

**G3 selector (run from `plugins/vibe-check/scripts`):**
```
pytest -q -p no:cacheprovider test_statepath.py test_scope_args.py test_finalize_card.py \
  test_finalize_gate.py test_finalize_archive_prose.py test_finalize_inputs.py test_finalize_parity_grid.py \
  test_fix_loop_card.py test_pause_batching.py test_recovery_pairs.py \
  test_carry_state.py::TestNoWritePath test_carry_state.py::TestLastHeadSha \
  test_state_shape.py::TestNoWritePath test_state_shape.py::TestAllOnlyKeys test_nv_render.py test_first_run.py \
  test_diff_ranges.py test_codex_gate.py::TestGsdRange test_codex_gate.py::TestRange \
  test_cross_call_vars.py test_pasted_name_guard.py test_inline_python_isolated.py
```
G3 overlaps G1, which is the binding gate. G3 exists so the record can report pass/fail per route. Safeguards and independent fix verification (GATE-05) are shown by `test_verified_fixes.py`, `test_confirmed_fix.py`, `test_fixcheck.py` (inside G1) plus G4b/G7. Name them in the record.

## Accepted differences (do not block) — the list the gate checks against

From 63-RESULT "Your decision" 1–5, D-27 and D-19 (owner go 2026-11-15):
1. Unreadable state file: the shell's "Permission denied" line no longer shows; the stop sentence shows alone.
2. Unsafe-name stop (D-21): a folder, branch or phase name with `$`, a backtick, `"`, `\` or a line break stops the review with one "Review halted" line.
3. Phase-end growth on every review path (the D-09 items; table above).
4. C-locale refusal line for a saved-progress file that is not valid UTF-8: `refused: state is not valid JSON` instead of `refused: malformed state: passes`.
5. Carried review items (63-REVIEW WR-02/WR-03/WR-04/SA-01/C2/SA-03; R2-WR-01..03 and set-aside items) → backlog 999.36/999.38.
6. D-27: 60-second limit on each helper git call; a slower git leaves that file out (the finding stays open).
7. D-19: from a subfolder, a file with unsaved or staged edits is not fingerprinted (a fix-obsolete verdict no longer closes on changed code).

Also named in 63-EQUIVALENCE but not user-visible: gate diagnostics are no longer written to a side file; fewer "Ran a shell command" entries; a `{}` fingerprint file is refused; `-I` on inline Python (D-22); `--all` prints its state path (D-23); Close out and the fix loop substitute the printed state path (D-20). Items 1, 2, 4, 6 and 7 are the user-visible ones for the D-11 "same behaviour as 2.14.1 except:" list.

## D-07: WR-02 offline reproduction

**Where the code is:** `plugins/vibe-check/phases/review/05-state.md` lines 8–14 (GSD state-key fence) reads `${PHASE_ID}`. No fence sets or prints it. `phases/review/00-scope.md:125` sets it in prose only: "Set `$PHASE_ID = $(basename "$PHASE_DIR")`". The one rule `scripts/statepath.py::_resolve_gsd` **refuses** an empty `phase_id` (line 161), but the fence is a transcription of it and has no such refusal.

**The Phase 60 fresh-shell standard** (60-CONTEXT D-09, `test_finalize_card.py::TestFinalizeFreshShellWalk` docstring): each fence is extracted from the instruction file and run in its own `bash -s` with only `PATH`, `VC_ROOT`, `TMPDIR` (and `STATE_FILE` where the file says to substitute the printed literal), in a scratch cwd or temp repo. Only the substitutions the instruction text tells the model to make are made.

**Step 1 (mechanism) — reproduced in this session:**
```
$ env -i PATH=/usr/bin:/bin HOME=$HOME bash <05-state.md GSD fence, verbatim>
LEGACY_STATE_FILE=.turingmind/state/.json
STATE_FILE=.turingmind/state/format-53/.json
exit 0
```
The unsafe-name guard does not catch an empty id (it rejects characters, not emptiness).

**What the reproduction must still show to qualify (data loss or wrong close):**
1. **Chain to a wrong close.** In one temp git repo with two GSD phase folders (e.g. `.planning/phases/01-a`, `02-b`): walk phase A's 05-state fence as written (prints `…/format-53/.json`) and write a pass-1 state there with an outstanding warning that is later decided, or with a clean pass. Then walk phase B's fences the same way: the same `.json` path is printed, so phase B's Finalize-inputs fence (`90-finalize.md` lines 14–29, three slots typed as `false`, the printed `STATE_FILE` literal substituted, as the text instructs) reads phase A's state. Record the `next` value. A `write-review-md` (approve) for phase B based on A's findings is a **wrong close**. A carried pass-2 that overwrites A's state with B's findings is **data loss** for A.
2. **Like-for-like 2.14.1 walk** (Phase 63 D-13 style): run the same fence from `git show v2.14.1:plugins/vibe-check/phases/review/05-state.md`. At 2.14.1 the fence printed nothing and later fences used `"$STATE_FILE"` as a shell variable, which is empty in a fresh shell. So 2.14.1 fails differently, with an empty path rather than a shared `.json`. The candidate's printed-literal fix (X3, D-20) makes the shared path the thing that gets pasted. This matters for classification: 999.38 says "none is a regression from 2.14.1", and the reproduction must check that claim. It is not proven yet [ASSUMED from reading only].
3. **Realism caveat (record honestly):** `test_cross_call_vars.py` (line ~1236) models `${PHASE_ID}` as a value **the model types in** (`02-code-review`). A live model that follows the prose at `00-scope.md:125` would usually substitute it. The fresh-shell standard runs the fence as written, which is the worst case. The repro should state both readings. Whether a live model leaves `${PHASE_ID}` raw is not tested by the D-02 smoke (default route, not GSD).

**Classification rule:** if step 1 above produces a wrong close or data loss under the fresh-shell standard, it qualifies (four-class rule) and goes to the owner as the D-08 fix round, with the reproduction in front of them (D-09). The shape of the fix is already written in 63-REVIEW WR-02: print `PHASE_ID` in the `00-scope.md` fence and refuse an empty one in `05-state.md`. That adds bytes to every review path, which becomes a new named-growth row. Otherwise carry it and name it as a known limit only if a user can see it.

**Mutant requirement (standing rule):** if a fix lands, its before/after test must fail with the empty-id refusal removed.

## Live smoke (GATE-06, D-01–D-03)

### Proposal (`65-LIVE-SMOKE-PROPOSAL.md`) — copy the 61 structure
Sections: Status line (`Status: APPROVED (owner, <date>)` / `DECLINED`), Why, Scope, Method, Estimated cost, Stop rules, What this does NOT trigger, If declined, Owner ruling (channel AskUserQuestion, verbatim selection). Cost basis from 54-BUDGET.md (verified): live review run median **$7.30–9.50** (deep review, Fable top tier); containment-proof session **$6.30–8.50**; coordinator time separate. Three sessions ≈ **$20–30, an estimate, not a cap** (owner rejected caps). Default `/vibe-check:review` costing at or below the deep-review unit is [ASSUMED] (61 A1, still unmeasured).

### Suggested session design (Claude's discretion)
The Finalize instructions changed, so the evidence strings differ from 2.14.0:
- **S1 `/vibe-check:review`** on a throwaway repo with one committed file and one uncommitted SQL-built-from-input defect (reuse the Phase 61 fixture shape: `app/store.py`, planted line ≈42; the 2.14.1 live check reused fixture sha `29f9f088…`). Pass needs: the defect flagged, a `STATE_FILE=` line printed by 05-state and later fences using that literal, and the decision recorded. **Decide by defer** (exercises "Findings deferred" at Close out). Then exit. If the fix-loop Rerun runs in-session, that is fine. If it stops on a typed defer, that is known item 999.32 (carry, not qualifying).
- **S2 `/vibe-check:review --finalize`** in a fresh process. Pass needs: one `BLOBFILE=` line (two if the one automatic rebuild fired; record which), the three `"<true|false>"` slots substituted (no "slot left as written" refusal), the helper's JSON line `{"action", "reason", "next", "counts", "report"}` printed, `next` = `write-review-md` (or `finalize-card` then, after answering, `write-review-md`), `.turingmind/REVIEW.md` written with `**State format:** 53`, `python3 "$VC_ROOT/scripts/finalize_gate.py" review-closed < .turingmind/REVIEW.md` exit 0, `state archived as …` printed, and **no** "Finalize stopped — nothing was written or archived" sentence outside the session's own Read of `90-finalize.md`.
- **S3 (optional third session, inside the estimate):** a `card-first` close. A second review that leaves one finding undecided, then `--finalize` shows the finalize card, records via `record-decisions`, re-runs the Finalize-inputs fence (new `BLOBFILE=`, never a reused one) and writes. This proves "act on the structured result" on the card branch, which S2 alone may not reach. The alternative is the 61 shape (review, nearby edit, re-review), but the re-ask behaviour is not what changed in 2.15. Recommend the card-first S3.
- **Provenance:** every `plugins/vibe-check/` path in every transcript (main + subagents) is under the snapshot or the cache. Zero under `/Users/julianamacbook/turingmind-code-review/plugins`.

### Mechanics (verified paths; adapt 61-04 Task 1/2)
- Snapshot: `SNAP=$HOME/.vibe-check-snapshots/rel65-<C7>`; `git -C <repo> worktree add --detach "$SNAP" "$C"`; `chmod -R a-w "$SNAP"`; assert `"version": "2.15.0"` in `$SNAP/plugins/vibe-check/.claude-plugin/plugin.json`.
- Cache: installed today = `~/.claude/plugins/cache/thejuran/vibe-check/2.14.1` (installed_plugins.json: version 2.14.1, gitCommitSha `eb790e4…`; verified). `CACHE_BAK=$HOME/.b3/vibe-check-2.14.1.bak-pre-phase65` (refuse if it exists); `cp -Rp`, empty `diff -rq -x .in_use`; `rsync -a --delete --exclude .in_use --exclude __pycache__ --exclude '*.pyc' --exclude .pytest_cache "$SNAP/plugins/vibe-check/" "$CACHE/"`; `chmod -R u+w "$CACHE"`; parity = empty `diff -rq -x .in_use -x __pycache__ -x '*.pyc' -x .pytest_cache` both ways.
- Throwaway repo: `SMOKE=$HOME/.b3/smoke65-$(date +%s)`; `git init -q -b main`; local user `smoke65 <smoke65@example.invalid>`; `.turingmind/` in `.git/info/exclude`.
- Auto-memory: slug `-Users-julianamacbook--b3-smoke65-<epoch>`; assert `~/.claude/projects/<slug>/memory` absent before each session; between sessions move it to `~/.b3/automemory-parked-phase65-<epoch>-sN`.
- Launch (fresh process per session, tmux `s65-N`, no `--model`, never bypass): `cd "$SMOKE" && claude --permission-mode manual --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent" --plugin-dir "$SNAP/plugins/vibe-check"`.
- tmux tips (memory v2.14.1): the trust prompt defaults to "No, exit", so press Down before Enter. Wait on `Enter to select|Type something`, not on `◯`. Keep the lid open; a sleep makes the run invalid (one retry).
- Evidence: sha256 of each `~/.claude/projects/<slug>/*.jsonl` (and subagent files), never contents. Printed `STATE_FILE=`/`BLOBFILE=` lines (paths only), the helper's `next`, REVIEW.md sha256, `review-closed` exit code, provenance counts.
- Restore always (also on failure/invalid): rsync back from `CACHE_BAK`, empty diff, kill tmux sessions, `chmod -R u+w "$SNAP"`, `git worktree remove --force`, `git worktree prune`.
- After the smoke, the **post-release** install check runs separately in the runbook (`claude plugin update vibe-check@thejuran` + full relaunch + installed_plugins.json version/sha check).

### Classification
PASS / QUALIFYING FAILURE — <class> / INVALID — <reason>. Qualifying examples: `--finalize` stops after its one rebuild with nothing malformed (broken required workflow); the decided finding is missing from REVIEW.md (silent loss); state damaged (data loss). Carry, don't block (D-10): wording, one extra question, harness write-retry (61 C5), the 999.32 Rerun stop.

### If declined — waiver text (for the sign-off page)
"The rewritten Close out (one helper call and its structured result) and the printed state path were proven only by offline fresh-shell walks (`finalize_capture.py compare`, `TestFinalizeFreshShellWalk`, `test_cross_call_vars.py`), not in a live model session. No route was run live for 2.15.0." The routes waived in every case (D-02): GSD, range, PR, incremental, `--all`, the fix loop.

## Release mechanics

- **Version bump locations:** `plugins/vibe-check/.claude-plugin/plugin.json` `"version": "2.14.1"` → `"2.15.0"` is the only version field (verified: `git grep 2.14.1` outside docs/.planning finds only plugin.json, README prose, and comments in `finalize_inputs.py` / `fixtures/finalize_step1_2141.sh` that refer to the 2.14.1 behaviour and must **not** change). The README "Measured Efficacy" block gains a `v2.15.0 (this release)` entry, the 2.14.1 entry loses "(this release)", and a "Known limitations (2.15.0)" bullet group goes into the Limitations list.
- **README test count:** prior releases quote `pytest` run inside `plugins/vibe-check/scripts` (memory: "README count = `pytest` inside plugins/vibe-check/scripts"; the 2.14.1 count 3,886 = suite record). Use G1a's count and say which command it came from.
- **README-coupled tests:** `test_recovery_pairs.py` (README limitation wording) and `test_gitguard.py` (one shared sentence). Run them on the edited README before committing C (61 Pitfall 1).
- **Tag name:** milestone releases are tagged `v2.13`, `v2.14`; the patch was `v2.14.1`. For 2.15.0 use **`v2.15`**, title pattern `v2.15 — Lean orchestration` (matching `v2.14 — Decision reliability`). [ASSUMED from naming history; confirm on the sign-off page.]
- **2.14.1 sequence (precedent):** one release PR (#8, "release: vibe-check 2.14.1 — …"), squash `dd8e4ab`, tag `v2.14.1`, GitHub release. **2.14.0 sequence** (61-CLOSE-RUNBOOK): verify-work → audit-milestone → complete-milestone with its in-branch tag step skipped → freshness assert (`git diff --quiet "$C" HEAD -- . ':(exclude).planning'`) → push branch + `gh pr create` with gate summary in body → owner OK in the owner's own message → `gh pr merge --squash` → tree-identity assert (`origin/main:plugins/vibe-check` and `:README.md` equal C's) → `git tag -a v2.15 origin/main` + push → `gh release create v2.15 --verify-tag --latest --notes-file 65-RELEASE-NOTES.md` → remote verify → `claude plugin update vibe-check@thejuran` + full relaunch + installed_plugins.json check (version 2.15.0, sha = origin/main; on lag uninstall + reinstall) → `git branch -D` + `git fetch --prune` (GitHub auto-deletes merged branches) → STATE/ROADMAP shipped.
- **Dependabot:** re-run the two commands on release day and quote the outputs (both failed today as above). Shipped runtime is stdlib-only (G8: 34 files); pytest 9.0.3 is test-only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bytes per path | ad-hoc `wc -c` sums | `footprint.py --rev <sha> --json` | `MODE_PATHS` is the one declared list; `wc` differs by locale (the D-18 footprint tests exist because of that) |
| Step counts | grep for fences | `step_count.py --rev --mode --json` (rule v1) | indented and four-backtick blocks, inline leads and FILE-name pastes are subtle |
| Situation comparison | re-walking Finalize by hand | `finalize_capture.py compare --driver helper --commit <C>` | normalisation, fault stand-ins and like-for-like are already built and tested |
| Replay equivalence | comparing reports by eye | `replay.py diff --base rev:v2.14.1` (no `--allow`) + `candidate` guardrail | complete-output diff over 170 runs; guardrail denominator fixed at 26 |
| Baseline integrity | trusting `baseline_records.py verify` alone | direct sha256 vs MANIFEST + direct recount (D-06) | 999.34 WR-02/WR-03: the two lenient checks can pass bad inputs |
| Cache parity | version string | two-direction `diff -rq` | same-version stale cache has bitten before |

## Runtime State Inventory

Not a rename/refactor phase. One runtime item matters for the release: **the installed plugin cache** (`~/.claude/plugins/cache/thejuran/vibe-check/2.14.1`, registry entry version 2.14.1). It is temporarily overwritten during the smoke and must be restored. After publish it must be updated (`claude plugin update` + full relaunch) or sessions keep running 2.14.1. Stored data: none (2.15.0 adds no state field; Finalize reads the same Phase-53 state). Downgrade 2.15.0 → 2.14.1 is expected to be harmless for the same reason [ASSUMED: not tested; say so in known limits if mentioned]. OS-registered state, secrets/env vars, build artifacts: none.

## Common Pitfalls

### Pitfall 1: Suite run in a linked worktree
**What goes wrong:** 5 `TestPhase53SameLineRegressionCases` failures and 1 `TestReconstruction` skip (private Phase-40/43 recordings are gitignored and exist only in the main checkout). **How to avoid:** G1/G2 run in `/Users/julianamacbook/turingmind-code-review` on branch `feat/v2.15-phase-65` checked out at C. **Warning sign:** `replay.py census` prints `transcripts: 0`.

### Pitfall 2: `PYTHONDONTWRITEBYTECODE=1` in the environment
63-VERIFICATION: `test_batchsnap.py::TestSnapshotImmutable::test_verify_survives_cache_churn` fails when it is set. Run the suite with a clean env (no such export).

### Pitfall 3: README not final before the gated suite
README is read by tests and holds the test count. Any README edit after C means a new candidate and a full re-run (D-12 pattern). Fact-check every README claim against shipped code and records before committing C.

### Pitfall 4: Smoke on a stale install
A version string does not prove content. Use rsync to the 2.14.1 cache dir + parity diff, a fresh `claude` process per session (counts as the relaunch), and `--plugin-dir` pointing at the snapshot.

### Pitfall 5: Auto-memory confound
Measurement sessions keep notes across runs. Park the slug's `memory` dir before every session.

### Pitfall 6: Owner approval relayed by an agent
Smoke spend, fix-round go, waiver and release go must come from the owner's own selection in the main session. Record the verbatim selection.

### Pitfall 7: complete-milestone tags the branch tip
Skip its tag step; tag `origin/main` after the tree-identity check.

### Pitfall 8: Forgetting `gh release create`
The tag alone leaves the release page on 2.14.1 (missed for v2.13).

### Pitfall 9: Understating review-path growth
See D-05 note: bytes +0.41–0.63% and +2 steps per review path. "~0.6%" alone is inaccurate for four of five paths.

### Pitfall 10: Treating the higher pass count as a difference
The suite gained tests in Phases 62–63. Equivalence means 0 failed/errors/skipped and the D-15 outcome fields. Name the pass-count change with its source.

## Code Examples

See §Gate Commands, §Fingerprint fence, §Counts fence, §D-07, Pattern 1. All were run in this session except the parts that need C, which does not exist yet.

## State of the Art

| Old (2.14.1) | Now (candidate) | Phase | Impact |
|---|---|---|---|
| Finalize: 18 bash blocks, per-file git loop, GATEFILE, separate counts/gate/report commands | one `finalize_inputs.py` call returning `{"action","reason","next","counts","report"}` | 63 | 92 → 85 steps, 136,114 → 130,886 bytes on the Finalize path |
| `STATE_FILE` assumed to survive between Bash calls | printed `STATE_FILE=` literal substituted in later fences | 63 X3/D-20/D-23 | +bytes on all review paths (itemised) |
| unsafe names went through | "Review halted" stop | 63 D-21 | visible behaviour change (release notes) |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A default `/vibe-check:review` session costs at or below the measured deep-review unit ($7.30–9.50) | Live smoke | Smoke estimate low; it is an estimate, not a cap, and the owner sees actual spend |
| A2 | Release tag/title `v2.15` / "v2.15 — Lean orchestration" | Release mechanics | Cosmetic; confirm on sign-off |
| A3 | WR-02 behaves differently at 2.14.1 (empty path, not shared `.json`), so "not a regression" needs checking | D-07 | Classification of WR-02 could change; the repro decides |
| A4 | Downgrade 2.15.0 → 2.14.1 is harmless (no new state field) | Runtime State | Only matters if stated in notes; mark untested |
| A5 | Candidate C changes only `plugin.json` under `plugins/`, so G6/G11 figures equal today's | Counts | If D-07 opens a fix round, new named-growth rows are needed |

## Open Questions (RESOLVED)

1. **Does WR-02 reach a wrong close under the fresh-shell standard?** Known: the fence prints `.json` when run as written. Unclear: the full two-phase chain, and 2.14.1's behaviour on the same input. Recommendation: plan 65-01 runs both before C is built.
   RESOLVED: plan 65-01 walks the mechanism and the two-phase chain on the current code and on 2.14.1 before C exists; a QUALIFYING verdict goes to the owner as the one fix round (65-03).
2. **Smoke S3 shape:** card-first close (recommended, exercises the structured result's card branch) or the 61 re-review shape. Decide in the proposal; the owner approves the proposal.
   RESOLVED: card-first S3 is written into the 65-02 proposal (and run by 65-06 if approved).
3. **Suite form for the README count:** G1a (scripts dir, like 3,886) is the precedent. The record also reports G1b (with `.github/scripts` and the lean tools). The README should say which.
   RESOLVED: G1a is the README count (65-04 fills it, 65-05 asserts it equals the G1a pass count); G1b is reported alongside in the record; tag/title are confirmed by the owner at sign-off in 65-07.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest (bare) | G1–G3 | yes | 9.0.3 on Python 3.12.12 | — |
| python3 | tools | yes | 3.14.5 | — |
| git | recount, snapshot | yes | 2.55.0 | — |
| tmux | live smoke | yes | 3.7c | — |
| claude CLI | validate, smoke, update | yes | 2.1.325 | — |
| gh (authenticated) | PR/tag/release | yes | 2.86.0; Dependabot scope missing (expected, recorded) | — |
| Private replay recordings | G1, G2, G4c | yes in main checkout | census `transcripts: 12` | none in worktrees, so run in the main checkout |
| Installed vibe-check cache | smoke | yes | 2.14.1 | — |

Missing with no fallback: none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (unittest-style tests) |
| Config file | none (no pytest.ini/conftest/pyproject); always `-p no:cacheprovider` |
| Quick run command | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_finalize_inputs.py test_finalize_card.py test_cross_call_vars.py` |
| Full suite command | repo root: `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools -rs` (main checkout) |

### Phase Requirements → Test Map
| Req / criterion | Behavior | Type | Automated command | Exists? |
|---|---|---|---|---|
| GATE-04 suite | full offline suite passes on C, 0 skipped on Mac | suite | G1a + G1b | ✅ |
| GATE-04 Mac-only | D-18 five + D-20 two run and pass | suite (ids) | G2 | ✅ |
| GATE-04 replay | 170 runs, 0 differing vs v2.14.1; guardrail REGRESSED 0; manifest ok; `baseline holds` | tool | G4a–G4e | ✅ |
| GATE-04 situations | five situations match the record; only command lists differ | tool | G5a, G5b | ✅ |
| GATE-04 mode/recovery | every route and recovery path class passes | suite subset | G3 selector | ✅ |
| GATE-04 unexpected difference | instruction diff touches only the 9 itemised files | git | G11 | ✅ |
| GATE-05 reduction | Finalize steps and bytes both lower at C than dd8e4ab | tool | G6 counts fence (assert 85 < 92 and 130886 < 136114, recomputed) | ✅ |
| GATE-05 named growth | each review path Δ == itemised D-09 sum | tool + table | G6 per-file fence vs reconciliation table | ✅ (fence; table check by script or by hand in the record) |
| GATE-05 safeguards | GOLDEN_DIGEST frozen; fix-verification tests pass; fingerprints 10/10 | suite + script | G7, G1 (`test_score.py::TestStableHashGolden`, `test_verified_fixes.py`, `test_confirmed_fix.py`) | ✅ |
| GATE-05 no cost claim | release notes/record contain no `$`, "token", "cheaper", "cost" savings claim | grep | `grep -nEi '\$[0-9]|token|cheaper|cost sav|billing' 65-RELEASE-NOTES.md` must show none in the savings block | ✅ (grep) |
| GATE-06 approval | smoke runs only after `Status: APPROVED (owner, …)` | file check | `grep -q '^Status: APPROVED (owner, ' 65-LIVE-SMOKE-PROPOSAL.md` before any session | ✅ |
| GATE-06 smoke | REVIEW.md written, `review-closed` exit 0, no stop sentence, provenance clean | live (manual-only, needs the model) | evidence greps on 65-LIVE-SMOKE.md (`^Status: DONE`, `^## Verdict`, `^## Cache restored`, `BLOBFILE=`, `STATE_FILE=`) | ✅ |
| GATE-06 waiver | waiver text present when declined, signed on 65-SIGNOFF.md | file check | `grep -q 'waiver: granted (owner, ' 65-SIGNOFF.md` | ✅ |
| D-07 | WR-02 reproduction recorded with a verdict | script | 65-01 scratch walk; `grep -q '^Verdict: ' 65-REPRO-WR02.md` | ❌ Wave 0 (scratch script; not added to the suite unless a fix lands) |
| Stdlib / manifest | 34 files stdlib-only; manifest valid | script | G8, G9 | ✅ |
| CI | offline-suite green on PR head | CI | G12 | ✅ |

### Sampling Rate
- **Per task commit:** quick run command (seconds).
- **Per wave merge:** G1b in the main checkout (about 4–6 minutes).
- **Phase gate:** G1–G12 all green on C before the sign-off; any production change → new C → all of G1–G12 again.

### Wave 0 Gaps
- [ ] D-07 reproduction script (scratchpad only, as in 63-REPRO; enters the suite only with a fix plus mutant)
- Otherwise none: the existing infrastructure covers every requirement.

### Observed suite result (main checkout, this session)
G1b form, run from `/Users/julianamacbook/turingmind-code-review` at `6d9bae3` (plugins tree = Phase 63 code), default env:
`4595 passed, 2 warnings, 6474 subtests passed in 359.99s (0:05:59)`, exit 0, **0 skipped** (junit `<skipped>` count 0), 0 failed. The 2 warnings are the parity-grid summary lines that 63-RESULT says are printed on purpose. The 5 D-18 tests and the 2 D-20 tests ran and passed here. The working tree was unchanged afterwards. Budget about 6 minutes for G1b. G1a (scripts dir only) was not timed separately.

## Security Domain

`security_enforcement` is absent from config, so this section is enabled. The phase changes no runtime code unless D-07 opens the fix round.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | yes (release actions) | owner-only approvals via AskUserQuestion; executors never push on relayed approval |
| V5 Input Validation | yes (only if the WR-02 fix lands) | refuse empty `PHASE_ID` like `statepath.py::_resolve_gsd`; keep the D-21 unsafe-name guard |
| V6 Cryptography | no (sha256 used only as fingerprints, via hashlib) | — |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Transcripts with private instructions committed | Information disclosure | hash only; `git ls-files '*.jsonl'` empty check |
| Smoke overwrites the shared plugin cache | Tampering | verified backup + unconditional restore + diff |
| Live session touches files outside the throwaway repo | Elevation | manual permission mode; decline paths outside `$SMOKE`, `$TMPDIR`, the snapshot or the cache |
| Spend without approval | Elevation (spend) | Status-line gate before any session |
| Tag on unmerged commit | Tampering (supply chain) | tree-identity assert, tag `origin/main` only |

## Sources

### Primary (HIGH confidence — repo, run this session)
- `.planning/phases/65-…/65-CONTEXT.md`; `.planning/REQUIREMENTS.md`; `.planning/ROADMAP.md` (Phase 65, 999.34–999.38); `.planning/STATE.md`
- `.planning/phases/63-…/63-COUNTS.md`, `63-EQUIVALENCE.md`, `63-RESULT.md`, `63-REVIEW.md`
- `.planning/milestones/v2.14-phases/61-…/61-0{1..5}-PLAN.md`, `61-RESEARCH.md`, `61-RELEASE-RECORD.md`, `61-LIVE-SMOKE-PROPOSAL.md`, `61-LIVE-SMOKE.md`, `61-CLOSE-RUNBOOK.md`, `61-SIGNOFF.md`, `61-CANDIDATE.md`, `61-RELEASE-NOTES.md`
- `.planning/milestones/v2.12-phases/54-…/54-BUDGET.md` (unit costs)
- `docs/design/lean-v2.15/` (README, CRITERION, BASELINE-v2.14.1, baseline/MANIFEST.json, tools)
- `.github/workflows/offline-suite.yml`, `.github/ci-left-out-tests.txt`, `.github/scripts/left_out_guard.py` (RECORDED_SKIPS)
- Commands executed: footprint/step_count at dd8e4ab and HEAD; finalize_capture verify/compare; baseline_records verify; replay diff/candidate/check-manifest/census; stdlib_only; left_out_guard check-list; claude plugin validate; fingerprint check; WR-02 fence walk; Dependabot API and PR list; installed_plugins.json read

### Secondary / Tertiary
- Project memory files (v2.14.1-shipped, one-branch-pr-per-phase, vibe-check-dependabot-disabled, orchestrator-fences-zsh, release-gates-before-publish, milestone-close-always-publishes)

## Metadata

**Confidence breakdown:**
- Gate commands and baselines: HIGH (executed this session)
- Counts and D-09 reconciliation: HIGH (recounted directly; exact match)
- Live smoke mechanics: HIGH for the procedure (ran in 61 and 2.14.1); MEDIUM for the new pass strings (from the current `90-finalize.md`, not yet seen live)
- D-07 classification: MEDIUM (mechanism reproduced; the chain and the 2.14.1 comparison are not yet run)

**Research date:** 2026-11-15
**Valid until:** until any commit changes `plugins/`, `docs/design/lean-v2.15/` or `.github/` (then re-run the gate dry-runs)
