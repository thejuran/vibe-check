# Phase 61 release record — vibe-check 2.14.0

This record proves the 2.14.0 release candidate against the scope Phases 59 and 60 delivered (decision continuity, exact-change ranges, reliable Close out). It adds no feature. Every gate below was re-run on the exact commit that will ship; results from earlier sessions are not carried forward.

**Code under consideration:** candidate C2 `47978aa` (47978aad41eccc13c594820a8ab8386904439f31), plugin.json 2.14.0. It supersedes `0d2be77` because the owner switched Decision 1 to B on 2026-10-30 ("Switch to B (Recommended)"): C2 adds the README correction for known limit C1 and changes nothing else (61-CANDIDATE.md). Gates ran on a checkout whose tree equals C2 outside .planning (D-12). The 0d2be77 gate run is kept below as history.

## Gate results — C2 (47978aa), 2026-10-30

Precondition (checked before any gate): `HEAD` = 47978aad41eccc13c594820a8ab8386904439f31 (C2 itself), `git diff --quiet 47978aa HEAD -- . ':(exclude).planning'` exit 0, `git status --porcelain -- plugins README.md` empty. After the runs, `git status --porcelain -- plugins` was still empty. All commands are the same as in the 0d2be77 run below (61-RESEARCH §Gate Commands); G5b used the run name `gate61c2`.

| # | Gate | Requirement | Result on C2 | Verdict |
|---|------|-------------|--------------|---------|
| G1 | Full offline suite | GATE-01 | `3821 passed, 5039 subtests passed in 190.43s (0:03:10)`, equals README count in C2 ("3,821 passing at release") | PASS |
| G2 | Targeted real-chain regressions | GATE-01 | `193 passed, 200 subtests passed in 14.32s` | PASS |
| G3 | Mode/recovery integration | GATE-01, D-11 | `520 passed, 1062 subtests passed in 8.68s` | PASS |
| G4 | Replay tests | GATE-02 | `64 passed, 10 subtests passed in 11.43s` | PASS |
| G5a | Replay complete-output diff vs released 2.13 scorer (no `--allow`) | GATE-02 | exit 0; `runs compared: 170`, `runs differing: 0`, `runs with unallowed differences: 0`; `## Differences` `- none`; candidate score.py sha256 `a4a02a24…b71ee` (same as 0d2be77) | PASS |
| G5b | Replay catch guardrail | GATE-02 | exit 0; `kept 25 / protected 26`, `REGRESSED 0`, `UNEVALUABLE 0`, `AMENDED 1` (standing amendment 008, `runs/triggarr-secret-in-logs/run-2`) | PASS |
| G5c | Replay manifest integrity | GATE-02 | exit 0, no output | PASS |
| G6 | D-03 live PR fetch (C2's `diff_ranges.py`) | GATE-03, D-03 | `PR #6: IDENTICAL (11255 diff lines)` `renames=0 binary=0`; `PR #4: IDENTICAL (1431 diff lines)` `renames=133 binary=0` | PASS |
| G7 | Manifest validity | GATE-03 | `✔ Validation passed`, same 3 non-blocking directory warnings (ICON_MISSING, `.DS_Store`, `docs/.DS_Store`; `git ls-files plugins/vibe-check` has 0 `.DS_Store` entries) | PASS |
| G8 | Stdlib-only runtime | D-10 | `32 shipped .py files; third-party imports: none`; no requirements.txt / pyproject.toml / package.json under plugins/vibe-check | PASS |
| G9 | Frozen replay machinery | GATE-02 | `git diff --stat v2.13 47978aa -- plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/test_replay.py` empty | PASS |

0 failed in every pytest run. Dependabot re-checked the same day: `gh api repos/thejuran/vibe-check/dependabot/alerts?state=open` still returns HTTP 403 "Dependabot alerts are disabled for this repository"; `gh pr list --author app/dependabot` still needs the `admin:repo_hook` scope. No settings changed; the runtime is stdlib-only (G8).

**Plugin tree identity, 0d2be77 → C2:** `git diff --quiet 0d2be77 47978aa -- plugins/` exit 0; `git diff --stat 0d2be77 47978aa -- plugins/` empty; `git rev-parse 0d2be77:plugins 47978aa:plugins` both `9387dcd3858160c44c0970fcb6a4621e223b7d4e`. The only path outside `.planning/` that differs is `README.md`.

## Gate results — superseded candidate 0d2be77 (history)

Precondition (checked before any gate, 2026-10-30): `git diff --quiet 0d2be77 HEAD -- . ':(exclude).planning'` exit 0 and `git status --porcelain -- plugins README.md` empty. Working HEAD was `9b8b909` (commits after C touch only `.planning/`), which is why the replay reports below print `head: 9b8b909…`.

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

## Live smoke (D-01/D-02)

**Verdict: PASS** (with carried item C1 below, which the owner rules on at sign-off). Full record: [61-LIVE-SMOKE.md](61-LIVE-SMOKE.md).

Under the owner-approved proposal ([61-LIVE-SMOKE-PROPOSAL.md](61-LIVE-SMOKE-PROPOSAL.md), APPROVED 2026-10-30), three fresh Claude Code sessions ran on a sealed read-only snapshot of C, with the installed cache at content parity (restored afterwards with an empty diff). Only the default review route and `--finalize` were in scope (D-02). S1 reviewed an uncommitted SQL-injection plant and the finding was deferred. S2 ran after an edit 3 lines above the flagged line and re-asked the decision with the reopen reason "code next to it changed since your decision on pass 1". S3's `--finalize` carried its printed BLOBFILE=/GATEFILE= paths across steps and wrote REVIEW.md (APPROVED, both deferred findings listed) without the "Finalize stopped" sentence. Every plugin path in every transcript came from the snapshot, so all three sessions were VALID. **Caveat (C1):** S1 also re-asked the same decision on pass 2 with no code change at all. So S2's re-ask would have happened without the nearby edit, and the live run does not isolate the nearby-edit trigger. That trigger rests on the offline tests (59/60 real-chain regressions, G2).

**Carry-over to C2:** the sessions ran on 0d2be77. The plugin tree they loaded is byte-identical in C2 (`git diff --quiet 0d2be77 47978aa -- plugins/` exit 0; both trees `9387dcd3…`; see the C2 gate section above), and the only other change is the repo-root README, which the plugin does not read. So the PASS verdict applies to C2 unchanged; no session was re-run and nothing was spent. Recorded in 61-LIVE-SMOKE.md §Carry-over to candidate C2.

## Unsupported fixtures and stated limits

- `--all` carries no decisions between runs (60 R10; `test_diff_ranges.py::TestRouteAll`), so decision continuity does not apply to it. This is a recorded unsupported fixture.
- Range route: one range-builder test (`TestRouteRange::test_range_between_commits_matches_u0`).
- Pause/resume: there is no end-to-end pause-then-resume walk, only prose pins and a state round trip.
- Binary files in PRs: untested (neither PR #6 nor PR #4 contains one).
- Very large PRs (about 300 files / 20,000 lines, GitHub's diff limit) fail closed: the review stops with an error (60 R17; owner-accepted limit, 60-HUMAN-UAT test 2).
- A finding in an untracked file is never re-asked after a nearby edit (60 R7).
- After upgrading from 2.13, one extra re-ask can happen the next time code near a decided finding changes (60 R4).
- With `diff.submodule=log` set, a change that touches only a submodule halts the pass (60 R18). It fails closed.
- On the default route, a decision on uncommitted code is re-asked on every pass even when nothing changed (live smoke C1; see Carried). The same pass ≥ 2 range source applies to a GSD review with uncommitted changes (read from `30-collect-score.md` L72, not run live). Stated in C2's README (first "Known limitations (2.14)" bullet) and in the release notes (first Known limit).

## Residuals (linked)

The full residual ledger is linked here, not restated (D-09). Total: 34 items, 8 + 26.
- Phase 59: [59-REPRO.md §Residuals](../59-stale-decisions-and-lost-deferrals/59-REPRO.md) — R1-R8 (8 items).
- Phase 60: [60-REPRO.md §Residuals](../60-exact-change-evidence-and-reliable-finalize/60-REPRO.md) — R1-R26 (26 items).
- Owner rulings: [60-HUMAN-UAT.md](../60-exact-change-evidence-and-reliable-finalize/60-HUMAN-UAT.md). R16: the live Write-tool check passed. R17: accepted limit. R25: status quo, hardening deferred as backlog 999.27.
- R6 (live `gh pr diff` never exercised) is now "checked once" by G6 above.

## Carried (D-07)

Each item was classified against the four qualifying classes: a mandatory gate failing, data loss, silent loss of a qualifying finding, or a broken required workflow. None qualifies. Each one is listed with the check that would reopen it.

- `claude plugin validate` printed 3 plugin-directory warnings that do not change the result (`✔ Validation passed`): no plugin icon (`ICON_MISSING`), and `.DS_Store` / `docs/.DS_Store` on disk under `plugins/vibe-check`. `git ls-files` shows neither `.DS_Store` file is tracked, so neither ships. Not a qualifying class; carried, no action in this phase. **Reopens if:** `claude plugin validate` fails, or a `.DS_Store` becomes tracked.
- **C1 — On the default route, a decision on uncommitted code is re-asked on every pass, with a false "code next to it changed" reason** (61-LIVE-SMOKE.md C1). On pass ≥ 2, the ranges come from `git diff <last-reviewed-sha>`. Before any commit that SHA is still HEAD, so the whole uncommitted block counts as changed on every pass. The effect is extra questions: a dismiss or defer holds only until the next pass, Close out still completes, and nothing is lost. The 2.13 default route also took its ranges from `git diff HEAD` on every pass, so this probably predates 2.14. That conclusion comes from reading the 2.13 instructions and has not been tested. Its rationale for carrying is that it fails toward asking. It contradicts the README's standing claim that a decision is kept "when you edit unrelated code" for findings in uncommitted code, and it touches the 2.14 headline promise. **Owner decision at first sign-off (2026-10-30, Decision 1 = A, 61-SIGNOFF.md):** ship with C1 as a documented limit (first Known limit in the release notes; README unchanged); no fix round. **Superseded the same day by Decision 1 = B** ("Switch to B (Recommended)", owner, AskUserQuestion in the main session) after verification (61-VERIFICATION.md, 61-REVIEW.md WR-01) showed the README was not silent but contradicted C1: new candidate C2 (47978aa) qualifies README:33 and README:38 and adds C1 as the first "Known limitations (2.14)" bullet; still no fix round; awaiting re-sign. **Reopens if:** the owner rules it qualifying, or a re-ask on unchanged committed code is reproduced, which would be a different and worse defect. **Backlog:** ROADMAP backlog entry 999.28 "Default route: decisions on uncommitted code re-asked every pass (false nearby reason)" added at sign-off (2026-10-30).
- **C2 — The band rose from warning to critical between passes with no code change** (61-LIVE-SMOKE.md C2). A second reviewer re-confirmed the finding. The severity-rise re-ask is designed behavior and never hides a finding, so there is no backlog entry. **Reopens if:** a band rise is reproduced with only one reviewer reporting.
- **C3 — The row regrouped between passes** (61-LIVE-SMOKE.md C3). The lead changed, and the old lead became an absorbed member "decided on its own". Both rows carried their deferral and were re-asked, and REVIEW.md lists both. Regrouping is existing behavior that 2.13 covered, so there is no backlog entry. **Reopens if:** a regroup drops a decided member from the card or from REVIEW.md.
- **C4 — In S2 the model did not take the protocol's Rerun after a typed defer** (61-LIVE-SMOKE.md C4). It stopped and listed choices. This is a model deviation that fails toward stopping: no spend, no loss, and the decisions were saved. It is user-visible (the user must say "continue"). **Backlog note:** fold into the 999.28 entry as a second observation, not a separate item. **Reopens if:** it recurs, or the stop loses a decision.
- **C5 — Harness retries** (61-LIVE-SMOKE.md C5). The first Write to a fresh `mktemp` file failed once and then succeeded after a Read. This is Claude Code's read-before-write rule, and the printed paths were still carried correctly. It is not user-visible beyond a retry line, so there is no backlog entry. **Reopens if:** the Write is refused outright (that is 60 R16's failure mode).

## Validation gaps and waivers

Everything below was not proven live for 2.14.0. Each waiver was granted at the first sign-off on 0d2be77 and stands as granted for C2; the owner re-confirms them at re-sign.
- GSD, range, PR, incremental pass 2+ and `--all` routes are proven offline only (D-02; G1-G3) — waiver: granted (owner, 2026-10-30)
- The live PR diff fetch was checked once, on PR #6 and PR #4 only (G6, D-03); binary files and very large PRs remain untested — waiver: granted (owner, 2026-10-30)
- The nearby-edit re-ask trigger is not isolated live: the live re-ask also happens without an edit (C1), so the trigger rests on offline tests — waiver: granted (owner, 2026-10-30)
- Claude's live reading of plain-English (free-text) answers is not release-tested — waiver: granted (owner, 2026-10-30)
- No B3 or holdout measurement, so there are no v2.14 catch or false-alarm numbers; v2.11 remains the last measured result — waiver: granted (owner, 2026-10-30)
- Pause/resume has no end-to-end walk, live or offline — waiver: granted (owner, 2026-10-30)

## Publish status

GATE-03 "ships through the existing close workflow": pending close — see [61-CLOSE-RUNBOOK.md](61-CLOSE-RUNBOOK.md). Nothing has been pushed, tagged, merged or released from this phase.
