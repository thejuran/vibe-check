# Phase 61 release record — vibe-check 2.14.0

This record proves the 2.14.0 release candidate against the scope Phases 59 and 60 delivered (decision continuity, exact-change ranges, reliable Close out). It adds no feature. Every gate below was re-run on the exact commit that will ship; results from earlier sessions are not carried forward.

**Code under consideration:** candidate `0d2be77` (0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d), plugin.json 2.14.0; gates ran on a checkout whose tree equals C outside .planning (D-12).

Precondition (checked before any gate, 2026-10-30): `git diff --quiet 0d2be77 HEAD -- . ':(exclude).planning'` exit 0 and `git status --porcelain -- plugins README.md` empty. Working HEAD was `9b8b909` (commits after C touch only `.planning/`), which is why the replay reports below print `head: 9b8b909…`.

## Gate results

| # | Gate | Requirement | Command | Result | Verdict |
|---|------|-------------|---------|--------|---------|
| G1 | Full offline suite | GATE-01 | `pytest -q -p no:cacheprovider` | `3821 passed, 5039 subtests passed in 177.81s (0:02:57)` — equals README count in C ("3,821 passing at release") | PASS |
| G2 | Targeted real-chain regressions | GATE-01 | 61-RESEARCH G2 selector (10 node ids) | `193 passed, 200 subtests passed in 13.20s` | PASS |
| G3 | Mode/recovery integration | GATE-01, D-11 | 61-RESEARCH G3 selector (13 node ids) | `520 passed, 1062 subtests passed in 7.73s` | PASS |
| G4 | Replay tests | GATE-02 | `pytest -q -p no:cacheprovider test_replay.py` | `64 passed, 10 subtests passed in 10.06s` | PASS |
| G5a | Replay complete-output diff vs released 2.13 scorer | GATE-02 | `python3 replay.py diff --base rev:v2.13 --scorer path:$PWD/score.py --out <scratch>` (no `--allow`) | exit 0; `runs compared: 170`, `runs differing: 0`, `runs with unallowed differences: 0`; `## Differences — none` | PASS |
| G5b | Replay catch guardrail | GATE-02 | `python3 replay.py candidate --name gate61 --scorer path:$PWD/score.py --out <scratch>` | exit 0; `kept 25 / protected 26`, `REGRESSED 0`, `UNEVALUABLE 0`, `AMENDED 1` | PASS |
| G5c | Replay manifest integrity | GATE-02 | `python3 replay.py check-manifest` | exit 0, no output | PASS |
| G6 | D-03 live PR fetch | GATE-03, D-03 | 61-RESEARCH §D-03 fence, `check 6; check 4`, using C's `diff_ranges.py` | `PR #6: IDENTICAL (11255 diff lines)` `renames=0 binary=0`; `PR #4: IDENTICAL (1431 diff lines)` `renames=133 binary=0` | PASS |
| G7 | Manifest validity | GATE-03 | `claude plugin validate plugins/vibe-check` (repo root) | `✔ Validation passed` (3 non-blocking directory warnings, see Carried) | PASS |
| G8 | Stdlib-only runtime | D-10 | 61-RESEARCH §Code Examples ast scan (`python3 -I`) | `32 shipped .py files; third-party imports: none`; no requirements.txt / pyproject.toml / package.json under plugins/vibe-check | PASS |
| G9 | Frozen replay machinery | GATE-02 | `git diff --stat v2.13 0d2be77 -- plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/test_replay.py` | empty output (unchanged since v2.13) | PASS |

## Raw output

```
All runs are from plugins/vibe-check/scripts at candidate 0d2be77.
G1  3821 passed, 5039 subtests passed in 177.81s (0:02:57)
G4  64 passed, 10 subtests passed in 10.06s
G5a - base: rev:v2.13 (sha256 3504d2da79e9ebab26bfedd01c7614c9b7cc06ade99c12b7e24e90003edd22fb)
    - candidate: path:.../plugins/vibe-check/scripts/score.py (sha256 a4a02a246ff696f3301c48145d31c6edf119bd396a7dc8f14013b372f50b71ee)
    - roots: all (7 roots)
    - allowances: none
    - runs compared: 170
    - runs differing: 0
    - runs differing (allowed): 0
    - runs with unallowed differences: 0
    ## Differences
    - none
G5b kept 25 / protected 26
    REGRESSED 0
    UNEVALUABLE 0
    AMENDED 1
```

- 0 failed in every pytest run (G1–G4).
- Replay differences: none (expected-difference list: empty; no --allow used).
- GOLDEN_DIGEST unchanged (TestGolden passes inside G1).
- G5b's one AMENDED run (`runs/triggarr-secret-in-logs/run-2`, amendment 008) is the manifest's standing amendment, not a new difference.
- Full logs stayed in the session scratchpad; nothing was written into the repo (`git status --porcelain -- plugins` empty after the runs).

## Live PR fetch (D-03)

Run from the repo root on a checkout equal to C outside `.planning`: `gh pr diff <N> --color never` piped through C's `plugins/vibe-check/scripts/diff_ranges.py`, compared with `cmp` against the same builder fed `git diff <baseRefOid> <mergeCommit>` from local history.

| PR | Diff lines | Renames | Binary | Result |
|----|-----------|---------|--------|--------|
| #6 | 11,255 | 0 | 0 | IDENTICAL |
| #4 | 1,431 | 133 | 0 | IDENTICAL |

R6 (PR route never exercised against a live `gh pr diff`) is now "checked once": the live gh fetch matched the local commits byte-for-byte on PR #6 and PR #4, the latter covering 133 renames. Binary files and very large PRs (R17, about 300 files / 20k lines, where GitHub's diff endpoint errors) remain stated limits, because no merged PR in this repo contains either.

## Dependencies and Dependabot (D-10)

- Dependabot alerts are disabled on thejuran/vibe-check: `gh api repos/thejuran/vibe-check/dependabot/alerts?state=open` returned `Dependabot alerts are disabled for this repository. (HTTP 403)` (2026-10-30).
- The CLI lacks the scope to list Dependabot PRs: `gh pr list --repo thejuran/vibe-check --author app/dependabot` returned `This API operation needs the "admin:repo_hook" scope`.
- So the release-time Dependabot review could not run. In its place: the shipped scripts import only the Python standard library and sibling helpers (G8: 32 shipped `.py` files, 0 third-party imports), and the plugin ships no dependency manifest.
- pytest is the test runner only and is not shipped.
- Runtime external tools: `python3`, `git`, `gh` (PR route only) and optionally the Codex plugin (`/deep-review` only).
- No repository or account settings were changed.

## Route and recovery coverage (D-11)

Every class below was confirmed to exist on C with `grep -n "^class <Name>" plugins/vibe-check/scripts/<file>`. Two file attributions are corrected from 61-RESEARCH: `TestScopePhaseStartFence` and `TestStateHeadShaFence` live in `test_diff_ranges.py` (lines 1445 and 1725), not `test_scope_args.py`.

| Route / path | Existing offline proof (confirmed on C) | Strength |
|---|---|---|
| Default (uncommitted) | `test_diff_ranges.py::TestRouteDefault`, `test_diff_ranges.py::TestShapesRealGit`, `test_statepath.py::TestDefaultModes` | Good |
| GSD | `test_diff_ranges.py::TestRouteGSD`, `test_diff_ranges.py::TestScopePhaseStartFence`, `test_statepath.py::TestGsdMode`, `test_codex_gate.py::TestGsdRange` | Adequate |
| Range (`A..B`) | `test_diff_ranges.py::TestRouteRange` (1 test: `test_range_between_commits_matches_u0`), `test_codex_gate.py::TestRange` (deep-review) | **Thin** |
| PR | `test_diff_ranges.py::TestRoutePR` (checked-in PR #5 capture), `test_diff_ranges.py::TestRefusals`, plus G6 live fetch above | Good |
| `--all` | `test_diff_ranges.py::TestRouteAll`, `test_statepath.py::TestAllMode`, `test_state_shape.py::TestAllOnlyKeys`, `test_nv_render.py` | Unsupported fixture (see below) |
| Incremental pass ≥2 | `test_diff_ranges.py::TestRouteIncremental`, `test_diff_ranges.py::TestStateHeadShaFence`, `test_carry_state.py::TestLastHeadSha` | Good |
| `--finalize` happy path | `test_finalize_card.py` (all classes), `test_finalize_gate.py`, `test_finalize_archive_prose.py`, `test_scope_args.py::TestFinalizeMode`, `test_scope_args.py::TestFinalizeStrip` | Good |
| `--finalize` one rebuild | `test_finalize_card.py::TestFinalizeFreshShellWalk` (`test_retry_mints_new_blobfile_after_missing_path` and siblings) | Good |
| `--finalize` no-write stop | `TestFinalizeFreshShellWalk::test_malformed_gatefile_shows_only_stop_sentence`, `test_carry_state.py::TestNoWritePath`, `test_state_shape.py::TestNoWritePath` | Good |
| Pause/resume | `test_fix_loop_card.py::TestFixLoopCard::test_paused_lines_exactly_once`, `test_fix_loop_card.py::TestCarrierRoundTrip`, `test_pause_batching.py` | **Thin** |
| Fix loop | `test_fix_loop_card.py`, `test_confirmed_fix.py`, `test_verified_fixes.py`, `test_fixcheck.py`, `test_fixcommit.py`, `test_fixstage.py` | Good |

No route has zero offline coverage. Every file above ran inside G1 on C (3821 passed); the mode/recovery subset also ran as G3 (520 passed).

Limits (stated, not new work — no-growth rule, D-07):
- `--all` is a recorded unsupported fixture: it carries no decisions between runs (60 R10), so decision continuity does not apply to it.
- Range route: one range-builder test (`TestRouteRange`).
- Pause/resume: prose pins and a state round trip, but no end-to-end pause-then-resume walk. Resume is an ordinary next pass, which the carry tests cover.

## Carried (D-07)

- `claude plugin validate` printed 3 plugin-directory warnings that do not change the result (`✔ Validation passed`): no plugin icon (`ICON_MISSING`), and `.DS_Store` / `docs/.DS_Store` on disk under `plugins/vibe-check`. `git ls-files` shows neither `.DS_Store` file is tracked, so neither ships. Not a qualifying class; carried, no action in this phase.
