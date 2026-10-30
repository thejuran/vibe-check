# Phase 61: Release gate — decision reliability - Research

**Researched:** 2026-10-30
**Domain:** Release verification and publishing for a Claude Code plugin (Python stdlib helpers + markdown orchestration prose), repo `thejuran/vibe-check`
**Confidence:** HIGH. Every offline gate command below was run in this session at HEAD `19df905`, whose plugin tree is identical to main `d587c72`. The live-smoke mechanics are MEDIUM: they follow the Phase 49 precedent, but the exact `--plugin-dir` vs installed-plugin precedence was not re-probed.

## Summary

This phase builds nothing. Every gate already has an executable check in the repo. In this session I ran the checks against current HEAD, which has the same plugin tree as the candidate minus the version bump. Results:

- Full suite: **3821 passed, 0 failed** (178 s).
- Targeted real-chain selector: **193 passed**.
- Mode/recovery selector: **520 passed**.
- `test_replay.py`: **64 passed**.
- `replay.py diff --base rev:v2.13`: **170 archived runs, 0 differing**.
- `replay.py candidate` guardrail: **REGRESSED 0** of 26 protected catches.
- Live `gh pr diff` → `diff_ranges.py` on PRs #4, #5 and #6: **byte-identical** to the ranges built from local commits. PR #4 includes 132 pure renames and 1 rename with edits.
- Shipped-script import scan: **0 third-party imports**.
- `claude plugin validate plugins/vibe-check`: **passed**.

So the planner can treat GATE-01/02 as "re-run on the bumped commit and record the result". No discovery work is needed.

The real planning work is ordering and release mechanics:

1. **Version surface.** The bump touches exactly one file, `plugins/vibe-check/.claude-plugin/plugin.json`. The README release section must also be rewritten: four of the seven 2.13 "Known limitations" bullets and one config-table caveat are fixed by Phases 59/60. **Two tests read the root README** (`test_recovery_pairs.py`, `test_gitguard.py`), so README edits must land before the gated full-suite run.
2. **D-12 vs squash merge.** Every prior PR (#1–#6) was squash-merged, which creates a new SHA on main. The tag therefore lands on a commit whose SHA differs from the gated one. Satisfy D-12 by asserting **tree identity** before tagging: the squash commit's tree must equal the gated candidate's tree, apart from `.planning/`-only archive commits.
3. **The live smoke cannot use `claude plugin update`.** The marketplace pins `ref: main`, and the candidate is not on main until the release is published. Use the Phase 49 pattern: a sealed `git worktree` snapshot of the candidate, `claude --plugin-dir <snapshot>/plugins/vibe-check`, the installed cache rsynced to parity (with a backup), a full relaunch, and the clone's auto-memory parked.
4. **`/bm:complete-milestone` cannot run inside Phase 61.** It requires every phase to be complete. Phase 61 therefore ends release-ready and owner-signed-off. Publishing (audit → close → PR → tag → `gh release create` → post-publish install update) runs after Phase 61 verification. GATE-03's "ships" clause is satisfied at close.

**Primary recommendation:** Structure the work in four parts:

- Wave 1: README + bump candidate commit, then all free gates on that exact commit.
- Live-smoke proposal as an owner checkpoint, then the smoke against a sealed snapshot of the same commit.
- Release record + one-page owner sign-off checkpoint.
- Post-phase: audit → complete-milestone → PR #7 squash → tree-identity assert → tag → push → `gh release create` → `claude plugin update` + relaunch.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Carried forward (locked — do not re-litigate)
- No growth per round (owner, 2026-10-28). Work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow, and the reproduction is cited. Everything else is carried with its rationale.
- Paid or live runs need a separately bounded proposal that the owner explicitly approves. Estimates are not spending caps.
- Archived replay may differ only in named, expected reopen/retention repairs. Phases 59 and 60 both closed with replay unchanged (`test_replay` 64 passed, GOLDEN unmoved), so the expected-difference list is probably empty. Any difference blocks release unless it is named and traced to a 59/60 repair. `replay.hunk_ranges` stays context-inclusive and unchanged (60 R11).
- `stable_hash` / GOLDEN_DIGEST frozen; single-writer rule for `decisions`; no-write-on-failure and independent fix verification are not weakened.
- Install resync before any manual or live check (60 R5): the cache currently runs **2.13.0**. Confirm the installed vibe-check equals the repo `plugin.json` version, and relaunch after a resync.
- A completed milestone always publishes: ff/merge main, push main and tag, then `gh release create`. Marketplace pins `ref: main`.
- One branch/PR per phase: `feat/v2.14-phase-61` (cut from main d587c72 after PR #6 merged).

#### Live validation
- **D-01:** The gate includes one small live smoke run under a bounded proposal that the owner approves before anything is spent. Shape: about 3 sessions, est. $20–30 (unit cost from 54-BUDGET.md: ~$6–9 per review session). Resync the install. On a throwaway repo, run review → decide a finding → edit near it → re-review shows the correct reopen reason on the card → `--finalize` writes REVIEW.md. Purpose: prove that the model follows the Phase 60 printed-path Finalize prose from fresh shells, which offline tests cannot show.
- **D-02:** The live smoke covers the **default route + Finalize only**. GSD, range, PR, incremental pass 2+ and `--all` rest on offline proof (plus D-03 for the PR fetch). The release record and notes say so.
- **D-03:** A free scripted check (network, no model) fetches a real PR's diff live with `gh pr diff` (e.g. PR #6) and runs it through the real range builder (`diff_ranges.py`), cross-checked against the local commits. R6 changes from "not exercised" to "checked once". The behaviour on renames, binary files and very large PRs stays a stated limit unless that PR happens to cover it.
- **D-04:** The assistant drives the live sessions via tmux, as in earlier measurement runs. Park the clone's auto-memory before any measurement session (`~/.claude/projects/-Users-julianamacbook-<clone>/memory`). Use manual permission mode as before. The owner approves the proposal and sees the results.

#### Gate failure handling
- **D-05:** If any gate check (offline suite, real-chain regressions, replay, mode/recovery checks, live smoke) reproduces a failure in the four qualifying classes, Phase 61 gets ONE fix round: a before/after fixture plus a mutation check per fix, then a full gate re-run on the new candidate. If it still fails, do not ship. Record the failure and re-scope.
- **D-06 (hard cap):** No second fix round without the owner's explicit go-ahead, given with the reproduction in front of them. The workflow never opens one on its own (Phase 60 ran three gap rounds under a one-cycle rule; this must not repeat).
- **D-07:** Anything outside the four classes, from the live smoke or anywhere else (wording, one extra re-ask that fails toward asking, etc.), is carried as a named known limit in the release record and the backlog, and the release continues.

#### Release record and sign-off
- **D-08:** The 2.14.0 GitHub release notes include a short **"Known limits"** section: 3–6 plain-language, user-visible bullets (e.g. untracked files never trigger a re-ask (R7); very large PRs stop the review (R17); the live PR route was checked once (R6/D-03); routes not run live). The full residual ledger stays in `.planning`.
- **D-09:** Before release, the owner signs off on **one plain-terms page**: pass/fail per gate check, the live-smoke outcome, replay differences (expected: none), user-visible limits, the Dependabot note (D-10), and waiver text for everything not proven live. The full ~34-item residual ledger (59-REPRO R1–R8, 60-REPRO R1–R26) is linked, not walked through.
- **D-10:** Dependabot alerts are disabled on thejuran/vibe-check, and `gh pr list --author app/dependabot` needs a token scope the CLI lacks. The release record states this and that the shipped scripts have no third-party runtime dependencies (stdlib only). The planner verifies this claim, separating test-only tooling such as pytest. No repo setting change.

#### Mode and candidate scope
- **D-11:** Offline integration checks cover **all routes and recovery paths**: default, GSD, range, PR, `--all` (its recorded unsupported-fixture status, `TestRouteAll`), incremental pass ≥2; `--finalize` including its one rebuild and the plain no-write stop; pause/resume; the fix loop. Mostly existing tests, run on the exact candidate commit.
- **D-12:** Every gate check runs on the **final release commit**: version already bumped to 2.14.0, the commit that will be tagged. Any later change re-runs the affected checks (all of them if production code changes).

### Claude's Discretion
- Throwaway-repo design for the live smoke, and the exact finding/edit used to trigger the reopen.
- Which existing tests make up "targeted real-chain regressions" (e.g. `TestStaleDecisions59`, the 60 route/coordinate/Finalize walk classes) and how the mode/recovery checks are grouped and reported.
- Release record file name/layout (e.g. `61-RELEASE-RECORD.md`) and the wording of the plain-terms page and the release-notes bullets.
- How the version bump and the release PR ride with the close workflow (the v2.13 precedent was a release PR from a separate branch). Must satisfy D-12.

### Deferred Ideas (OUT OF SCOPE)
- Live runs of GSD, range, PR and incremental routes: not in this gate (D-02). Revisit only if the default-route smoke fails in a way that implicates shared range-source prose.
- Enabling Dependabot on the repo: not done (D-10).
- All 59/60 residuals not in the four qualifying classes stay carried. Lean orchestration (Finalize extraction) starts only after this release ships.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GATE-01 | On the release candidate, the targeted real-chain regressions, full offline suite, and mode/recovery integration checks pass | §Gate Commands G1–G3 (selectors verified: 193 / 3821 / 520 passed at 19df905); §D-11 Route Coverage Map (every route mapped to classes; thin spots named) |
| GATE-02 | Archived replay differs only in the named, expected reopen/retention repairs | §Gate Commands G4–G5: `replay.py diff --base rev:v2.13 --scorer path:<abs>/score.py` → 170 runs, 0 differing; `replay.py candidate` → REGRESSED 0; `test_replay.py` 64 passed. Expected-difference allowance list = empty |
| GATE-03 | Release record states unsupported fixtures, residuals, validation gaps; live checks only under approved proposal, else waiver; ships through existing close workflow | §Live Smoke (proposal inputs, procedure), §D-03 PR fetch (verified free check), §Release Record Inputs, §Release Mechanics (close workflow, squash/tag tree-identity, `gh release create`) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

There is no `./CLAUDE.md` in the repo. These directives come from the owner's global `~/.claude/CLAUDE.md` and project memory, and apply here:

- **Releases:** before the version bump/tag, review open Dependabot alerts and PRs and roll fixes in. This repo cannot run that review: alerts are disabled (HTTP 403, re-verified this session) and the CLI lacks the `admin:repo_hook` scope. The owner ruled (D-10): state this in the release record, change no settings.
- **Division of labor:** the owner's approval is not code review. Verification comes from tests and runs. Present the sign-off page in plain terms: pass/fail and user impact, not code.
- **Planning files:** follow `/Users/julianamacbook/Documents/Codex/planning/PLANNING-FORMAT.md`. Refresh STATE.md `last_updated` on every edit, and keep the milestone and status truthful.
- **Security (absolute):** no secrets in release notes or records. Never commit Claude Code transcripts; they carry the owner's global instructions verbatim (repo `.gitignore` precedent). Bind them by sha256 instead.
- **Interaction:** no wellbeing commentary. Technical stopping points (cost checkpoints, publish checkpoint) are fine.
- **Memory rules in force:**
  - Proceed through specified gates without "shall I proceed?" prompts. Reserve questions for real forks: proposal approval, sign-off, publish.
  - A milestone close always publishes.
  - One branch/PR per phase; delete the branch after merge.
  - Run release gates before publish.
  - `.planning/` is gitignored, so tracked planning files need `git add -f`, and `bm-sdk query commit` refuses them.
  - Run fences as `bash -s <<'BASH' … BASH`: the Bash tool runs zsh here, and unquoted lists don't word-split.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Offline gate (suite, selectors, replay) | Local test runner (`pytest` in `plugins/vibe-check/scripts`) | git (replay reads committed archives + `rev:v2.13` blob) | Deterministic; no model, no network |
| D-03 PR fetch check | GitHub API via `gh` | `diff_ranges.py` (pure stdlib) + local git | Network but free; the code under test is the range builder |
| Live smoke | Claude Code CLI session (tmux) loading candidate snapshot | Installed plugin cache (parity) | Only tier that exercises model-followed prose across fresh Bash calls |
| Version + release notes | Repo files (`plugin.json`, root `README.md`) | GitHub Release object | Marketplace serves `plugins/vibe-check` from `main`; README is the long-form notes |
| Publish | `main` branch on GitHub (marketplace `ref: main`) | Tag `v2.14` + `gh release create` | Merging to main IS the publish |
| Planning archive | `.planning/` (gitignored, force-added) | — | Never touches plugin runtime, so it never invalidates gates |

## Standard Stack

No new packages. Everything is already in the repo or on the machine.

### Core (verified present this session)
| Tool | Version | Purpose |
|------|---------|---------|
| pytest (runner only) | 9.0.3 at `~/.local/bin/pytest` | Runs the unittest-based suite. **Bare `pytest` only.** `python3 -m pytest` fails: "No module named pytest" under Homebrew python3.14 [VERIFIED: ran it] |
| python3 | 3.14.5 | Helpers. `config.py` needs ≥3.11 for `tomllib` and degrades to defaults otherwise |
| git | system | Replay `rev:` specs, range cross-checks, worktree snapshot |
| gh | authenticated as thejuran | `gh pr diff`, `gh pr create/merge`, `gh release create` |
| claude CLI | 2.1.314 | `--plugin-dir`, `--permission-mode manual`, `--allowedTools`, `claude plugin validate/update` [VERIFIED: `claude --help`] |
| tmux | 3.7c | Drives live sessions |

### Package Legitimacy Audit
Not applicable. This phase installs no external packages. D-10 scan result: the 32 shipped non-test `.py` files under `plugins/vibe-check/{scripts,hooks,agents}` import only stdlib modules plus sibling helpers (`batch_parse`, `carry_state`, `fixcommit`, `guard`, `replay`, `score`). The test files also import no third-party modules; they are `unittest`-based, and pytest is only the runner [VERIFIED: ast scan this session]. Runtime external *tools* (not packages) are `python3`, `git`, `gh` (PR route only) and, optionally, the Codex plugin (`/deep-review` only). The plugin has no `requirements.txt`, `pyproject.toml` or `package.json`.

## Gate Commands (verified at HEAD 19df905, plugin tree == d587c72)

Run all of these from `/Users/julianamacbook/turingmind-code-review/plugins/vibe-check/scripts`, wrapped in `bash -s <<'BASH' … BASH`. Always pass `-p no:cacheprovider`, as the Phase 60 plans did.

| # | Gate | Command | Result now |
|---|------|---------|-----------|
| G1 | Full offline suite (GATE-01) | `pytest -q -p no:cacheprovider` | `3821 passed, 5039 subtests passed in 178.12s` |
| G2 | Targeted real-chain regressions (GATE-01) | see selector below | `193 passed, 200 subtests passed in 13.24s` |
| G3 | Mode/recovery integration (GATE-01, D-11) | see selector below | `520 passed, 1062 subtests passed in 7.72s` |
| G4 | Replay tests (GATE-02) | `pytest -q -p no:cacheprovider test_replay.py` | `64 passed, 10 subtests passed` |
| G5a | Replay complete-output diff vs released 2.13 scorer (GATE-02) | `python3 replay.py diff --base rev:v2.13 --scorer path:$PWD/score.py --out <md>` | exit 0; `runs compared: 170`, `runs differing: 0`, `runs with unallowed differences: 0`; "## Differences — none" |
| G5b | Replay catch guardrail (GATE-02) | `python3 replay.py candidate --name gate61 --scorer path:$PWD/score.py --out <md>` | exit 0; "Guardrail — 26 protected catch runs … REGRESSED 0" |
| G5c | Manifest integrity | `python3 replay.py check-manifest` | exit 0 |
| G6 | D-03 live PR fetch | see §D-03 | PRs #4/#5/#6 byte-identical |
| G7 | Manifest validity | `claude plugin validate plugins/vibe-check` (from repo root) | "✔ Validation passed" |
| G8 | Stdlib-only (D-10) | ast import scan (§Code Examples) | 0 third-party |
| G9 | Frozen invariants | `git diff --stat v2.13 <C> -- plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/test_replay.py` must be empty; `TestGolden`/GOLDEN_DIGEST `7a516d01…3124` pass inside G1 | replay.py/test_replay.py untouched since v2.13 |

**G2 selector (targeted real-chain regressions):**
```
pytest -q -p no:cacheprovider \
  test_decision_continuity.py::TestStaleDecisions59 \
  test_decision_continuity.py::TestPhase59CarryStateMutants \
  test_decision_continuity.py::TestRepro59Record \
  test_decision_continuity.py::TestDeferredStaysOpen \
  test_decision_continuity.py::TestRealDiffRanges60 \
  test_decision_continuity.py::TestCoordinateSpaces60 \
  test_decision_continuity.py::TestRepro60Record \
  test_decision_continuity.py::TestRepro60Evidence \
  test_finalize_card.py::TestFinalizeFreshShellWalk \
  test_diff_ranges.py
```

**G3 selector (mode/recovery):**
```
pytest -q -p no:cacheprovider test_statepath.py test_scope_args.py test_finalize_card.py \
  test_finalize_gate.py test_finalize_archive_prose.py test_fix_loop_card.py test_pause_batching.py \
  test_recovery_pairs.py test_carry_state.py::TestNoWritePath test_state_shape.py::TestNoWritePath \
  test_state_shape.py::TestAllOnlyKeys test_nv_render.py test_first_run.py
```

G2 and G3 overlap G1. They exist so the release record can report per-category pass/fail. G1 is the binding gate.

**Why G5a is the real GATE-02 check (not only G4):** `score.py` changed by 149 lines since v2.13 (Phase 59-02 producers). `test_replay.py` pins the replay *machinery*. `replay.py diff` re-scores every archived run (7 roots, 170 runs) through the released 2.13 scorer and through the candidate scorer, then compares the complete output. It reports zero differences, which is consistent with 60-REPRO's note: archived envelopes carry no carry-forward, so the 59/60 reopen/retention repairs cannot appear in them. **The expected-difference allowance list is empty. Run without `--allow`.** Any nonzero `runs differing` blocks release (locked rule). The planner should not pre-author an allowance file.

## D-11 Route Coverage Map

| Route / path | Existing offline proof | Strength |
|---|---|---|
| Default (uncommitted) | `test_diff_ranges.py::TestRouteDefault` (4), `TestShapesRealGit` (13), `test_statepath.py::TestDefaultModes` (6) | Good. Also the live smoke route |
| GSD | `TestRouteGSD` (2), `TestScopePhaseStartFence` (5), `test_statepath.py::TestGsdMode` (5), `test_codex_gate.py::TestGsdRange` | Adequate |
| Range (`A..B`) | `TestRouteRange` (**1 test**), `test_codex_gate.py::TestRange` (4, deep-review) | **Thin:** one range-builder test. Name it in the record; do not add tests (no-growth) |
| PR | `TestRoutePR` (5, on checked-in PR #5 capture `fixtures/pr-cumulative.diff`), `TestRefusals` (series/mbox) + **D-03 live** | Good after D-03 |
| `--all` | `TestRouteAll` (3: no diff → no ranges; reviewed-set finding kept; state forces fresh pass), `test_statepath.py::TestAllMode` (5), `test_state_shape.py::TestAllOnlyKeys`, `test_nv_render.py` all-carryforward-bypass pin | Recorded **unsupported fixture** (60 R10): `--all` carries no decisions. State as a limit |
| Incremental pass ≥2 | `TestRouteIncremental` (2), `TestStateHeadShaFence` (10), `test_carry_state.py::TestLastHeadSha` (8) | Good |
| `--finalize` happy path | `test_finalize_card.py` (all classes), `test_finalize_gate.py`, `test_finalize_archive_prose.py`, `test_scope_args.py::TestFinalizeMode/TestFinalizeStrip` | Good |
| `--finalize` one rebuild | `TestFinalizeFreshShellWalk::test_retry_mints_new_blobfile_after_missing_path`, `…new_gatefile_after_gate_input_failure`, `…post_decision_recount_refingerprints_head`, `…post_decision_rerun_decides_on_a_fresh_gatefile` | Good (fresh-shell walks) |
| `--finalize` no-write stop | `TestFinalizeFreshShellWalk::test_malformed_gatefile_shows_only_stop_sentence`, `…counts_fence_without_literal_exits_two`, `test_carry_state.py::TestNoWritePath`, `test_state_shape.py::TestNoWritePath` | Good |
| Pause/resume | `test_fix_loop_card.py::TestFixLoopCard::test_paused_lines_exactly_once` (prose pin), `TestCarrierRoundTrip` (re-entry strings through the real 00-scope normalizer), `test_pause_batching.py` (NONINTERACTIVE byte pins), `test_carry_state.py` resumed-severity test | **Thin:** prose pins plus state round trip. No end-to-end "pause, then resume reproduces the card" walk. Resume is an ordinary next pass, which the carry tests cover. Name it in the record; no new work |
| Fix loop | `test_fix_loop_card.py` (11 classes, ~150 tests), `test_confirmed_fix.py`, `test_verified_fixes.py`, `test_fixcheck/fixcommit/fixstage.py` | Good |

No route has zero offline coverage. The two thin spots (range: 1 test; pause/resume: no end-to-end walk) are reported as stated limits under D-07.

## D-03 Live PR Fetch Check (verified free, run this session)

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
OUT=$(mktemp -d)
H=plugins/vibe-check/scripts/diff_ranges.py
check() {  # $1 = PR number
  base=$(gh pr view "$1" --json baseRefOid -q .baseRefOid)
  merge=$(gh pr view "$1" --json mergeCommit -q .mergeCommit.oid)
  gh pr diff "$1" --color never > "$OUT/pr$1.diff"            # the exact range source 30-collect-score.md names for the PR route
  python3 "$H" < "$OUT/pr$1.diff" > "$OUT/pr$1.gh.json"
  git diff --no-color --no-ext-diff --no-textconv --no-relative --src-prefix=a/ --dst-prefix=b/ \
    "$base" "$merge" | python3 "$H" > "$OUT/pr$1.local.json"
  cmp "$OUT/pr$1.gh.json" "$OUT/pr$1.local.json" && echo "PR #$1: IDENTICAL ($(wc -l < "$OUT/pr$1.diff") diff lines)"
  printf 'renames=%s binary=%s\n' "$(grep -c '^rename from' "$OUT/pr$1.diff" || true)" "$(grep -c '^Binary files' "$OUT/pr$1.diff" || true)"
}
check 6; check 4
BASH
```

Results this session:

| PR | Files | Diff lines | Renames | Binary | Result |
|---|---|---|---|---|---|
| #6 | 50 | 11,255 | 0 | 0 | IDENTICAL |
| #5 | 34 | 7,076 | 0 | 0 | IDENTICAL |
| #4 | 141 | 1,431 | 132 at 100% similarity + 1 at 97% | 0 | IDENTICAL |

**Recommendation: run PR #6 (as D-03 names) and PR #4.** PR #4 covers renames for free. **No merged PR in this repo contains a binary file** (the repo has no committed images), so binary stays a stated limit. Very large PRs (R17, ~300 files / 20k lines) stay a stated limit; the largest merged PR is #2 at 77 files and ~17k additions, under the limit. Each squash commit's tree equals its PR head tree (no conflicts), which is why `base..merge` is the right local counterpart.

## Live Smoke (D-01/D-02/D-04)

### Proposal inputs (owner checkpoint BEFORE any spend)
- **Unit cost:** 54-BUDGET.md gives $7.30–9.50 median per *deep-review* run (Fable top tier, ~6 subagents) and $6.30–8.50 per containment-proof session. The coordinator session costs $5–60 per working day.
- **This smoke uses `/vibe-check:review`** (default route; Sonnet agents, Haiku triage), which should cost at or below the deep-review unit [ASSUMED: not separately measured].
- **Proposal shape:** 3 sessions, est. $20–30 plus coordinator time. One retry allowed only for an *invalid* run (wrong plugin root, auth expiry, lid closed). Not a spending cap.
- **Stop rule:** a qualifying failure triggers D-05 (one fix round). A non-qualifying oddity is carried (D-07).

### Candidate loading (the important mechanic)
The marketplace entry (`~/.claude/plugins/marketplaces/thejuran/.claude-plugin/marketplace.json`) pins `git-subdir … ref: "main"` with no version field [VERIFIED]. `claude plugin update` therefore cannot install the candidate before it is merged, and merging is publishing. The installed copy is 2.13.0 at `~/.claude/plugins/cache/thejuran/vibe-check/2.13.0`, `gitCommitSha f2b6a36` [VERIFIED: installed_plugins.json]. Use the Phase 49 pattern (`docs/design/b3-ground-truth/RUN-PHASE49-v2.11.md` §resync-cache):

1. Build a sealed snapshot of the gated candidate commit `C`: `git worktree add --detach ~/.vibe-check-snapshots/rel61-<short> C`, then `chmod -R a-w`. Never pass the working repo, and never the snapshot root, to `--plugin-dir` (BATCH-LIFECYCLE §3). `PLUGIN_ROOT=<snapshot>/plugins/vibe-check`; assert `$PLUGIN_ROOT/.claude-plugin/plugin.json` says 2.14.0.
2. Back up the installed cache **outside** the plugin cache (`cp -Rp … ~/.b3/vibe-check-2.13.0.bak-pre-phase61`). Then `rsync -a --delete --exclude .in_use --exclude __pycache__ --exclude '*.pyc' --exclude .pytest_cache "$PLUGIN_ROOT/" "$CACHE/"`, `chmod -R u+w "$CACHE"`, and run a two-direction content check (version strings prove nothing). This removes the ambiguity over whether agents dispatch from the cache or from `--plugin-dir`. Agents dispatch from the installed cache (memory: vibe-check-agent-install-sync).
3. **Fully quit and relaunch** Claude Code. A new conversation is not enough.
4. After the smoke, restore the backup into the cache. After publish, run `claude plugin update vibe-check@thejuran` (2.13.0→2.14.0 is a real version bump, so update works) and relaunch. Then verify `installed_plugins.json` shows 2.14.0 and `gitCommitSha` equals main. This is where R5's "installed == repo" is confirmed for users.

### Session pattern
- **Throwaway repo:** `~/.b3/smoke61-<epoch>` (the A4 precedent), with `git init`, one commit, and then an uncommitted change containing one unmistakable defect. Example: a Python function building SQL with f-string user input, roughly 30 lines long, with the defect line ~15. The reviewer should flag it at warning or critical.
- **Auto-memory:** the throwaway's memory dir is `~/.claude/projects/-Users-julianamacbook--b3-smoke61-<epoch>/memory` (path separators and dots become `-`) [ASSUMED: slug rule inferred from existing dirs]. Assert it is absent before S1. **Move it aside between S1→S2→S3** to `~/.b3/automemory-parked-phase61-<epoch>-sN` (precedent: `~/.b3/automemory-parked-*`). One repo across three sessions would otherwise carry notes forward, which is the Phase 40 confound.
- **Launch line:** `cd <throwaway> && claude --permission-mode manual --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent" --plugin-dir "$PLUGIN_ROOT"`, inside tmux (`tmux new -s s61-N`), driven with `send-keys`/`capture-pane`. Accept the workspace-trust prompt on first launch. Do not use bypass mode.
- **S1:** `/vibe-check:review` → card → **defer** (or dismiss) the SQL finding.
- **Between S1 and S2 (no model):** edit a line **2–4 lines from** the flagged line without touching the flagged line, and leave it uncommitted.
- **S2:** fresh process, `/vibe-check:review` → the card must show the row re-asked with " — code next to it changed since your decision on pass 1" (`batch_card.py` ~L591; or the "code next to line N (…) changed" variant ~L554). Decide again.
- **S3:** fresh process, `/vibe-check:review --finalize` → `REVIEW.md` written and state archived. Must not show "Finalize stopped — nothing was written or archived; run `--finalize` again."
- **Evidence (keep transcripts OUT of git):**
  - sha256 of each `~/.claude/projects/<slug>/*.jsonl`
  - captured pane text of the card line
  - `REVIEW.md` sha256 and its existence
  - a provenance grep: every helper/phase path in the transcript is under `$PLUGIN_ROOT` or the parity cache, never the repo working tree
  - BLOBFILE=/GATEFILE= printed-path lines seen in S3, which is the Phase 60 class the smoke exists for
- **Machine:** keep the lid open (Phase 40 run voided by sleep).

## Version Bump and Release Notes Surface

| File | Change | Verified |
|---|---|---|
| `plugins/vibe-check/.claude-plugin/plugin.json` | `"version": "2.13.0"` → `"2.14.0"` | Only `2.13.0` pin outside `.planning`/`docs/design` [VERIFIED: git grep] |
| Marketplace `thejuran/marketplace` | **No edit**: no version field, pins `ref: main` | [VERIFIED] |
| Tests asserting the plugin version | **None** (`test_batchsnap.py` uses a synthetic 2.10.0 manifest) | [VERIFIED] |
| Root `README.md` §Measured Efficacy | Add a "v2.14 (this release) — decisions re-asked correctly, Finalize completes. Not measured." paragraph; relabel 2.13 as "previous release" (v2.13 precedent, commit f2b6a36) | — |
| Root `README.md` §Limitations "Known limitations (2.13)" | Fixed in 2.14, so remove or replace: bullet 1 (uncommon layouts not re-asked: 59 CR-01/02/04), bullet 2 (min_confidence deferred member: DEFR-01), bullet 3 (~8-line window: 60 EVID-01), bullet 6 (Finalize temp-file stop: 999.25/FINL). Keep: 999.26 wordy references; live plain-English reading untested. Downgrade bullet becomes "2.14 → 2.13 untested" (2.14 adds `nearby_spots` to snapshots, 59-04) | — |
| Root `README.md` config table `min_confidence` row | Remove "(except a finding grouped under a deferred row; see Known limitations)" (fixed by DEFR-01) | — |

**README is test-coupled:**
- `test_recovery_pairs.py` reads root README and requires the phrase "every later run that reviews changes", and forbids "gets **one** automatic independent re-check".
- `test_gitguard.py::TestBoundaryDecision` reads root README for the boundary sentence.

Commit README and bump together **before** G1. Follow the v2.13 precedent of a README fact-check against shipped code (a fact-check agent found 5 overstated claims in 2.13 notes) before the candidate is frozen.

## Release Mechanics (D-12 + close workflow)

**Precedent (v2.13, verified from `git show f2b6a36`):** a separate `feat/v2.13-release` branch carried three commits: archive, `rm REQUIREMENTS.md`, and bump + README. PR #4 was squash-merged to main `f2b6a36`. The annotated tag `v2.13` points at that squash commit, and `gh release create` was run afterwards (the owner noticed it had been missed). The repo allows squash, merge and rebase, with `deleteBranchOnMerge: true` [VERIFIED: gh repo view]. There is no CI; the local suite is the merge gate.

**Recommended flow for v2.14 (one branch, satisfies the one-branch-per-phase rule):**
1. On `feat/v2.14-phase-61`: README + bump commit → **candidate `C`**. Run G1–G9 on `C`, record SHA and outputs. Run the live smoke on a snapshot of `C`.
2. Release record + sign-off page (`.planning`, force-added). Owner sign-off checkpoint.
3. `/bm:verify-work 61` (or verifier). GATE-03's "shipped" clause is pending close, as in the v2.13 human_needed/waiver pattern.
4. `/bm:audit-milestone v2.14` → `/bm:complete-milestone v2.14` on the same branch. **Skip the workflow's in-branch tag push.** Its `git_tag` step tags the local branch commit, which a squash merge leaves off main's ancestry. Archive commits touch only `.planning/`.
5. **D-12 freshness assert before PR:** `git diff --quiet C HEAD -- . ':(exclude).planning'` must succeed. If anything outside `.planning` changed, re-run the affected gates; production code means all of them.
6. PR #7 (owner OK) → squash merge → `git fetch origin`.
7. **Tree-identity assert:** `test "$(git rev-parse origin/main:plugins/vibe-check)" = "$(git rev-parse C:plugins/vibe-check)"` and the same for `README.md`. Equal tree hashes mean byte-identical content, so the tagged commit is the gated candidate in everything that ships.
8. `git tag -a v2.14 origin/main -m …` → `git push origin v2.14` → `gh release create v2.14 --verify-tag --latest --title "v2.14 — Decision reliability" --notes-file <notes>`. The notes follow the v2.13 body format (verified via `gh release view v2.13`) plus a "Known limits" section (D-08).
9. Verify on the remote: `git show origin/main:plugins/vibe-check/.claude-plugin/plugin.json` shows 2.14.0, `git ls-remote --tags origin | grep v2.14` finds the tag, and `gh release view v2.14` succeeds. Then `claude plugin update vibe-check@thejuran` + relaunch, and confirm the installed version is 2.14.0.
10. Delete the local branch; `git fetch --prune`.

An alternative that keeps the SHA (a local `git merge --ff-only` + push main, the older memory note) bypasses the PR the owner has used for every phase since v2.13. Stick with squash + tree-identity.

## Release Record Inputs

- **59-REPRO §Residuals R1–R8:** R1/R2 over-asks (fail toward asking); R3 SA-02 dropped; R4–R6 unexercised observations; R7 close line; R8 wording tie.
- **60-REPRO §Residuals R1–R26.** User-visible candidates:
  - R4: old `nearby_at` stamps → one extra re-ask after upgrade
  - R6: live PR fetch, now checked by D-03
  - R7: untracked files never re-ask
  - R10: `--all` carries no decisions
  - R17: large PRs fail closed; owner-accepted, 60-HUMAN-UAT test 2
  - R18: `diff.submodule=log` submodule-only change halts the pass
  - R25 → backlog 999.27
- **60-HUMAN-UAT rulings:** R16 live Write-tool pass; R17 accepted limit; R25 status quo + 999.27.
- **Audit template:** `.planning/milestones/v2.13-MILESTONE-AUDIT.md` frontmatter (`status`, `scores`, `judgement_calls`, `tech_debt`, `nyquist: skipped`) and sections (Definition of done, Phases, Requirements 3-source, Cross-phase integration, E2E flows, Tech debt).
- **Suggested Known-limits bullets (3–6, D-08):**
  1. A finding in a new, untracked file is never re-asked after edits (R7).
  2. PR reviews stop on very large PRs (~300 files / 20k lines) (R17).
  3. Only the default review and Close out were run live. GSD, range, PR, incremental and `--all` are covered by tests, and the PR diff fetch was checked once against real PRs (D-02/D-03).
  4. `--all` does not keep decisions between runs (R10).
  5. After upgrading, a decided finding may be asked again once (R4).
  6. Wordier plain-English references still ask a follow-up (999.26).

## Common Pitfalls

### Pitfall 1: Gating a commit that is not the shipped tree
Gates run before the README fact-check fixes, or before the bump, so the tagged tree differs. **Avoid:** freeze `C` only after README and bump. Assert `git diff --quiet C HEAD -- . ':(exclude).planning'` before the PR, and tree identity after the squash.

### Pitfall 2: `python3 -m pytest` / zsh fences
`python3 -m pytest` reports "No module named pytest" (re-verified). zsh does not word-split unquoted lists. **Avoid:** use bare `pytest -q -p no:cacheprovider` inside `bash -s <<'BASH'`.

### Pitfall 3: Transient mutant files in `scripts/`
While the suite runs, replay tests write `scripts/_score_mutant_drop_<pid>.py` and remove it afterwards (seen mid-run this session; gone when the run finished). **Avoid:** never `git add -A`, build a snapshot, or rsync from the working tree while a suite runs. Snapshot from the committed `C` via worktree.

### Pitfall 4: Live smoke silently runs 2.13.0
The cache is stale (R5), and `--plugin-dir` set to the repo root or the working tree measures the wrong thing. **Avoid:** use a sealed worktree snapshot plus cache parity and a full relaunch, then confirm with a provenance grep after each session. A run with the wrong provenance is invalid; it is not a failure.

### Pitfall 5: Auto-memory confound across the 3 smoke sessions
**Avoid:** park the throwaway project's memory dir before each session and assert it is absent at launch.

### Pitfall 6: Replay allowance pre-authoring
Writing an allowance file "just in case" would mask a real delta. **Avoid:** run G5a with no `--allow`. Expected-difference list = empty.

### Pitfall 7: Close workflow tags the wrong commit
`complete-milestone`'s `git_tag` tags the branch tip, which leaves main's ancestry after a squash. **Avoid:** tag `origin/main` after the tree-identity assert.

### Pitfall 8: Forgetting the GitHub Release object
This happened for v2.13. **Avoid:** make `gh release create … --verify-tag --latest` an explicit step with verification.

### Pitfall 9: Transcripts or owner instructions committed
**Avoid:** keep transcripts local and record only sha256 and extracted lines.

### Pitfall 10: Treating a non-qualifying smoke oddity as a fix trigger
**Avoid:** classify against the four classes first. Anything else follows D-07 (carry and continue). At most one fix round (D-05), and never a second without the owner (D-06).

## Code Examples

### D-10 stdlib scan (verified this session)
```bash
bash -s <<'BASH'
cd /Users/julianamacbook/turingmind-code-review/plugins/vibe-check
python3 -I - <<'PY'
import ast, glob, os, sys
std = set(sys.stdlib_module_names)
local = {os.path.basename(f)[:-3] for f in glob.glob('scripts/*.py')}
files = [f for f in glob.glob('scripts/*.py') + glob.glob('hooks/**/*.py', recursive=True)
         + glob.glob('agents/**/*.py', recursive=True) if not os.path.basename(f).startswith('test_')]
bad = {}
for f in files:
    for n in ast.walk(ast.parse(open(f).read())):
        mods = ([a.name.split('.')[0] for a in n.names] if isinstance(n, ast.Import)
                else [n.module.split('.')[0]] if isinstance(n, ast.ImportFrom) and not n.level else [])
        for m in mods:
            if m not in std and m not in local:
                bad.setdefault(f, set()).add(m)
print(len(files), "shipped .py files; third-party imports:", bad or "none")
PY
BASH
```

### Tree-identity assert before tagging
```bash
bash -s <<'BASH'
set -euo pipefail
C=<gated candidate sha>
git fetch origin
for p in plugins/vibe-check README.md; do
  test "$(git rev-parse "origin/main:$p")" = "$(git rev-parse "$C:$p")" || { echo "TREE DIFFERS: $p"; exit 1; }
done
echo "origin/main ships the gated candidate byte-for-byte"
BASH
```

## State of the Art

| Old approach | Current approach | When | Impact |
|---|---|---|---|
| ff-only merge of milestone branch to main (memory, v2.5–v2.11) | Squash PR per phase, tag on main's squash commit (v2.13) | 2026-10-23 | D-12 satisfied by tree identity, not SHA identity |
| Release notes only in README | README + `gh release create` body | v2.12/v2.13 | Must be an explicit step |
| R6 PR fetch "not exercised" | Checked live on #4/#5/#6 | this research | Record says "checked once" |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `/vibe-check:review` sessions cost at or below the $6–9 deep-review unit | Live Smoke | Estimate low; not a cap, but the owner should see a range |
| A2 | Auto-memory slug for `~/.b3/smoke61-<epoch>` is `-Users-julianamacbook--b3-smoke61-<epoch>` | Live Smoke | Parking the wrong dir, so memory confounds S2/S3. Mitigation: `ls ~/.claude/projects | grep smoke61` after S1 |
| A3 | With cache parity, it does not matter whether `--plugin-dir` or the installed copy wins name resolution | Live Smoke | If parity is skipped, the run could exercise 2.13.0. Parity + provenance grep makes this moot |
| A4 | A nearby edit 2–4 lines from the flagged line yields the "code next to it changed" wording rather than "code changed" | Live Smoke | Card wording differs. Still a correct reopen (D-07 territory, not a failure) |
| A5 | 2.14 state fields make an untested 2.14→2.13 downgrade re-ask rather than lose data | Release notes | Wording of one README bullet |

## Open Questions (RESOLVED)

1. **Where does GATE-03's "ships" clause get verified?** RESOLVED: adopted in 61-05 (ships clause pending close; steps in 61-CLOSE-RUNBOOK.md).
   - Known: `complete-milestone` refuses until all phases are complete, so it cannot run inside Phase 61.
   - Recommendation: Phase 61 verification marks the publish step human_needed/pending-close. The milestone audit and close then complete it, as in the v2.13 audit pattern. The planner should not put `complete-milestone` inside a Phase 61 plan.
2. **Does the README need the gated suite count ("N passing at release")?** RESOLVED: adopted in 61-01 Task 2 (count from G1 on the edited tree) and re-asserted on C in 61-03.
   - The v2.13 README cites 3,588. If the count goes in README, it must be the G1 count on `C`, and it is the same number on main because the trees are identical. Recommendation: fill it in from G1, and re-run G1 after any README edit, because README is test-coupled.
3. **Defer vs dismiss in smoke S1.** RESOLVED: adopted in 61-04 Task 2 step 1 (defer). Both are deliberate decisions under STALE rules. Recommendation: defer, because it also exercises deferred-obligation visibility at Finalize (REVIEW.md "Findings deferred" list).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest (bare) | G1–G4 | ✓ | 9.0.3 | — |
| python3 ≥3.11 | helpers, replay | ✓ | 3.14.5 | — |
| gh (authenticated) | D-03, PR, release | ✓ | — | — |
| claude CLI | live smoke, validate, update | ✓ | 2.1.314 | — |
| tmux | live smoke | ✓ | 3.7c | — |
| Dependabot API | release rule | ✗ (403 disabled; scope missing) | — | D-10: state it in the record |

No missing dependency blocks execution.

## Security Domain

| ASVS Category | Applies | Control |
|---|---|---|
| V2/V3/V4 | no | — |
| V5 Input Validation | indirect | `diff_ranges.py` fail-closed refusals (exercised by D-03) |
| V6 Cryptography | no | — |
| V14 Config / supply chain | yes | stdlib-only runtime (D-10 scan); `claude plugin validate`; tree-identity before tag |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Publishing a tree other than the gated one | Tampering | Tree-identity assert; tag `origin/main` only after it |
| Owner instructions/PII leaked via committed transcripts | Information disclosure | Transcripts stay local; commit sha256 only |
| Live session approving tools silently | Elevation | `--permission-mode manual` + explicit `--allowedTools`; never bypass in the smoke |

## Sources

### Primary (HIGH, verified by running in this session)
- Repo: `plugins/vibe-check/scripts/{replay.py,diff_ranges.py,batch_card.py,test_*.py}`, `phases/shared/{01-bootstrap.md,90-finalize.md}`, `phases/review/{00-scope.md,30-collect-score.md}`, `hooks/hooks.json`, `.claude-plugin/plugin.json`
- Commands run: pytest G1–G4 selectors, `replay.py diff/candidate/check-manifest`, `gh pr diff` 4/5/6 cross-check, `claude plugin validate`, `claude --help`, `gh api …/dependabot/alerts`, `gh repo view`, `gh release view v2.13`, `git show f2b6a36`
- `~/.claude/plugins/{installed_plugins.json,known_marketplaces.json,marketplaces/thejuran/.claude-plugin/marketplace.json}`
- Planning: 61-CONTEXT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, 59-REPRO.md, 60-REPRO.md, 60-HUMAN-UAT.md, 60-VERIFICATION.md, v2.13-MILESTONE-AUDIT.md, 54-BUDGET.md, bm `workflows/complete-milestone.md` (5.0.4)
- Precedent docs: `docs/design/b3-ground-truth/RUN-PHASE49-v2.11.md` (§resync-cache, §a4-smoke), `BATCH-LIFECYCLE-v2.10-phase40.md` §3

### Secondary (MEDIUM: project memory)
- milestone-close-always-publishes, one-branch-pr-per-phase, v2.13 SHIPPED, install-chronically-stale, vibe-check-agent-install-sync, phase40-batch1-validation-findings (manual mode + allowedTools; memory confound; lid), vibe-check-dependabot-disabled, release-gates-before-publish

## Metadata

**Confidence breakdown:**
- Gate commands/results: HIGH (executed)
- Release mechanics: HIGH for repo facts, MEDIUM for the recommended squash + tree-identity flow (owner precedent, not yet exercised with that assert)
- Live smoke: MEDIUM (precedent-based; A2–A4 open)

**Research date:** 2026-10-30
**Valid until:** until any commit touches `plugins/vibe-check/` or README. Re-run G1–G9 on `C` regardless (D-12).
