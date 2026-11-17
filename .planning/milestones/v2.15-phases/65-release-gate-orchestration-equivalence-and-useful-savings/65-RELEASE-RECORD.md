# Phase 65 release record — vibe-check 2.15.0

This record proves the 2.15.0 release candidate behaves like 2.14.1 except for the accepted differences, and shows the Close out (Finalize) reduction and the named review-path growth from a direct recount. Every gate below was run on the candidate in this session; no result is carried from an earlier session.

**Code under consideration:** b073e31fb77f3f5ca32747f8c549ec552687b1be (version 2.15.0)

Precondition (checked before every gate fence, 2026-11-16): C was read with `sed -n 's/^candidate: //p'` from 65-CANDIDATE.md and asserted 40-hex and a commit. Working HEAD was `1e04b60` (C plus planning-only commits), and `git diff --quiet "$C" HEAD -- . ':(exclude).planning'` exited 0, so the tree equals C outside `.planning`. `git status --porcelain -- plugins README.md docs .github` was empty, the run was in the main checkout `/Users/julianamacbook/turingmind-code-review` (`git rev-parse --git-dir` = `.git`, not a linked worktree), and `PYTHONDONTWRITEBYTECODE` was unset. Gates that take a revision (G5b `--commit`, G6, G7, G10, G11) were passed C explicitly. After the runs, `git status --porcelain -- plugins README.md docs .github` was still empty.

## Gate results — C (b073e31), 2026-11-16

| # | Gate | Requirement | Result on C | Verdict |
|---|------|-------------|-------------|---------|
| G1a | Full suite, README form (`plugins/vibe-check/scripts`) | GATE-04 | `4126 passed, 2 warnings, 6207 subtests passed in 246.50s`; junit `errors="0" failures="0" skipped="0"`, `<skipped` count 0; equals `suite_on_edited_tree` (4126) in 65-CANDIDATE.md | PASS |
| G1b | Full suite, CI set without the deselect (repo root) | GATE-04 | `4599 passed, 2 warnings, 6481 subtests passed in 451.99s`; junit `errors="0" failures="0" skipped="0"`, `<skipped` count 0 | PASS |
| G2 | Mac-only tests by id (5 CI-left-out + 2 Linux self-skipping) | GATE-04 | `7 passed, 10 subtests passed in 0.34s`; no skip lines under `-rs` | PASS |
| G3 | Mode/recovery integration selector | GATE-04 | `898 passed, 2 warnings, 2316 subtests passed in 110.98s`, 0 failed | PASS |
| G4a | Replay complete-output diff vs 2.14.1 (no `--allow`) | GATE-04 | exit 0; `runs compared: 170`, `runs differing: 0`, `runs with unallowed differences: 0`; `## Differences` `- none`; base and candidate score.py sha256 both `c6488729…f725` | PASS |
| G4b | Replay catch guardrail | GATE-04, GATE-05 | exit 0; `kept 25 / protected 26`, `REGRESSED 0`, `UNEVALUABLE 0`; `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1` (standing amendment 008) | PASS |
| G4c | Replay manifest + census | GATE-04 | `check-manifest` exit 0; census `transcripts: 12`, `scoreable: 66` | PASS |
| G4d | Baseline kit replay re-derive | GATE-04 | `baseline holds`, exit 0 | PASS |
| G4e | Replay tests | GATE-04 | inside G1; also run alone: `64 passed, 10 subtests passed in 11.71s` | PASS |
| G5a | Five Finalize situations: record intact | GATE-04 | `finalize baseline matches (5 situations)`, exit 0 | PASS |
| G5b | Five Finalize situations on C | GATE-04 | exit 0; every walk `outcome fields match`; 0 `differs` lines; last line `finalize outcome fields match (5 situations, 7 walks)` | PASS |
| G6 | Direct recount, six paths, dd8e4ab vs C | GATE-05 | Finalize 136,114 → 131,381 bytes, 92 → 85 steps (both lower); review paths +1,705 to +1,966 bytes and +2 steps each; all growth itemised (`Unitemised growth: 0`) | PASS |
| G7 | Fingerprints, baseline folder, GOLDEN_DIGEST | GATE-05 | `10 of 10 match MANIFEST.json`; `git diff --quiet d0adb5b "$C" -- docs/design/lean-v2.15/baseline` exit 0; GOLDEN_DIGEST `7a516d01…3124` at C and v2.14.1; `baseline_commit` = dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4 | PASS |
| G8 | Stdlib-only runtime + left-out list | GATE-04 | `34 shipped .py files; third-party imports: none`; `left-out list matches the recorded five` | PASS |
| G9 | Plugin manifest valid | GATE-04 | `✔ Validation passed`; version `2.15.0`; same 3 non-blocking directory warnings as 2.14 (ICON_MISSING, `.DS_Store`, `docs/.DS_Store`; both `.DS_Store` files are untracked and gitignored) | PASS |
| G10 | Frozen scorer/replay | GATE-05 | `git diff --quiet v2.14.1 "$C" -- …/score.py …/replay.py …/test_replay.py` exit 0 | PASS |
| G11 | Instruction-diff surface | GATE-04 | exactly the 9 D-09 files (list below) | PASS |
| G12 | CI offline-suite green on the PR head | GATE-04 | pending close — runbook step 4 | PENDING |

0 failed and 0 errors in every pytest run. Suite form per gate: G1a, G3, G4e and the fix-verification run used `pytest -q -p no:cacheprovider` from `plugins/vibe-check/scripts`; G1b and G2 ran from the repo root. All used bare `pytest`.

**Fix verification (GATE-05).** `test_verified_fixes.py`, `test_confirmed_fix.py` and `test_fixcheck.py` pass inside G1a/G1b, and alone: `248 passed, 223 subtests passed in 13.69s`.

**Suite equivalence.** Equivalence here means 0 failed, 0 errors, 0 skipped, not equal pass counts. The README-form count rose from 2.14.1's 3,886 to 4,126 because tests were added. Phase 63 added `test_finalize_inputs.py`, `test_finalize_parity_grid.py`, `test_cross_call_vars.py`, `test_pasted_name_guard.py` and `test_inline_python_isolated.py`, and reworked `test_finalize_card.py`. The 65-03 WR-02 fix added cases to `test_pasted_name_guard.py` and `test_cross_call_vars.py`. Phase 62's baseline-kit tests live under `docs/design/lean-v2.15/tools` and `.github/scripts`, so they count only in the G1b form (4,599).

**Environment notes (not gate failures).**
- Under the Mac default locale, plain `sort` orders the file list differently from the plan's checks, so G11's list was sorted with `LC_ALL=C sort`.
- A G6 attempt started while G1a was running hit `DIRTY TREE — STOPPING`, because a test's temporary file briefly appeared under the shipped tree. The tree was clean once G1a finished, and G6 was re-run with the full preamble. Gates were then run one at a time.

## Raw output

- G1a: `4126 passed, 2 warnings, 6207 subtests passed in 246.50s (0:04:06)`; `exit 0`; junit `testsuite … errors="0" failures="0" skipped="0" tests="10333"`; `grep -c '<skipped'` → 0.
- G1b: `4599 passed, 2 warnings, 6481 subtests passed in 451.99s (0:07:31)`; `exit 0`; junit `testsuite … errors="0" failures="0" skipped="0" tests="11080"`; `grep -c '<skipped'` → 0.
- G2: `7 passed, 10 subtests passed in 0.34s`; `exit 0`.
- G3: `898 passed, 2 warnings, 2316 subtests passed in 110.98s (0:01:50)`; `exit 0`.
- G4a (`diff.md` header): `base: rev:v2.14.1 (sha256 c648872979e9bf3fd5e5f56f64f229de783c8e47258e45651cb5a06742f5e725)`; `candidate: path:…/score.py (sha256 c648872979e9bf3fd5e5f56f64f229de783c8e47258e45651cb5a06742f5e725)`; `allowances: none`; `runs compared: 170`; `runs differing: 0`; `runs differing (allowed): 0`; `runs with unallowed differences: 0`; `head: 1e04b60f885bf8bf07af005e87ff5a686f22312c`; `## Differences` `- none`; exit 0.
- G4b (`cand.md`): `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`; `## Guardrail — 26 protected catch runs`; `kept 25 / protected 26`; `REGRESSED 0`; `UNEVALUABLE 0`; exit 0.
- G4c: `check-manifest exit 0`; census `runs: 18`, `runs-v2.10: 36`, `runs-v2.10-phase40: 12`, 3 `excluded:` failed-run dirs, `transcripts: 12`, `scoreable: 66`.
- G4d: `baseline holds`.
- G4e: `64 passed, 10 subtests passed in 11.71s`.
- G5a: `finalize baseline matches (5 situations)`.
- G5b: `compared with finalize-situations-v2.14.1.json; driver helper-walk-2.15; tree: commit b073e31fb77f3f5ca32747f8c549ec552687b1be`; 7 lines `<walk>: outcome fields match`; `intended differences (the lists of commands run, D-15):` (per-walk `steps` and `tally.*` before/after lines); fault stand-ins: like for like, and 3 refusal lines `2.14.1 and now identical`; `finalize outcome fields match (5 situations, 7 walks)`; exit 0.
- G6: see Counts below (tool output at both commits).
- G7: `10 of 10 match MANIFEST.json`; `baseline folder unchanged since Phase 62 merge d0adb5b (exit 0)`; `C: 44:GOLDEN_DIGEST = "7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124"`; `v2.14.1: 43:GOLDEN_DIGEST = "7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124"`.
- G8: `34 shipped .py files; third-party imports: none`; `left-out list matches the recorded five`.
- G9: `✔ Validation passed`; `"version": "2.15.0",`.
- G10: `G10 exit 0 (identical to v2.14.1)`.
- G11 (`LC_ALL=C sort`, count 9):
  - `plugins/vibe-check/phases/deep-review/01d-coverage.md`
  - `plugins/vibe-check/phases/deep-review/2c-codex-kickoff.md`
  - `plugins/vibe-check/phases/deep-review/30-codex-collect.md`
  - `plugins/vibe-check/phases/review/00-scope.md`
  - `plugins/vibe-check/phases/review/05-state-all.md`
  - `plugins/vibe-check/phases/review/05-state.md`
  - `plugins/vibe-check/phases/review/06-config.md`
  - `plugins/vibe-check/phases/review/50-fix-loop.md`
  - `plugins/vibe-check/phases/shared/90-finalize.md`
- Fix verification: `248 passed, 223 subtests passed in 13.69s`.

PR diff fetch: `git diff --quiet v2.14.1 "$C" -- plugins/vibe-check/scripts/diff_ranges.py` exit 0. `diff_ranges.py` is unchanged since 2.14.1, so the 2.14.0 live PR-fetch check still stands and was not re-run.

## Route and recovery coverage

G3 ran the 65-RESEARCH §Mode/recovery map selector as one run: 898 passed, 0 failed. Per route:

| Route / path | Tests in G3 | Strength |
|---|---|---|
| Default (uncommitted) | `test_diff_ranges.py::TestRouteDefault`, `::TestShapesRealGit`, `test_statepath.py::TestDefaultModes` | Good (also the live-smoke route) |
| GSD | `test_diff_ranges.py::TestRouteGSD`, `::TestScopePhaseStartFence`, `test_statepath.py::TestGsdMode`, `test_codex_gate.py::TestGsdRange`, `test_pasted_name_guard.py` (GSD key, incl. WR-02 empty/unset id) | Adequate |
| Range (`A..B`) | `test_diff_ranges.py::TestRouteRange`, `test_codex_gate.py::TestRange` | Thin (stated limit, unchanged since 2.14) |
| PR | `test_diff_ranges.py::TestRoutePR`, `::TestRefusals` | Good (live fetch from 2.14.0 stands; `diff_ranges.py` unchanged) |
| `--all` | `test_diff_ranges.py::TestRouteAll`, `test_statepath.py::TestAllMode`, `test_state_shape.py::TestAllOnlyKeys`, `test_nv_render.py`, `test_cross_call_vars.py` C1 `--all` cases | Adequate; `--all` keeps no decisions (stated limit) |
| Incremental pass ≥2 | `test_diff_ranges.py::TestRouteIncremental`, `::TestStateHeadShaFence`, `test_carry_state.py::TestLastHeadSha` | Good |
| `--finalize` happy path | `test_finalize_card.py`, `test_finalize_gate.py`, `test_finalize_archive_prose.py`, `test_finalize_inputs.py`, `test_finalize_parity_grid.py`, `test_scope_args.py` | Good |
| `--finalize` one rebuild | `test_finalize_card.py::TestFinalizeFreshShellWalk` retry/rerun walks | Good |
| `--finalize` no-write stop | `TestFinalizeFreshShellWalk` stop walks, `test_carry_state.py::TestNoWritePath`, `test_state_shape.py::TestNoWritePath` | Good |
| Pause/resume | `test_fix_loop_card.py`, `test_pause_batching.py` | Thin (stated limit, unchanged) |
| Fix loop | `test_fix_loop_card.py`, `test_cross_call_vars.py` X8; plus `test_confirmed_fix.py`, `test_verified_fixes.py`, `test_fixcheck.py` (in G1 and the fix-verification run) | Good |
| Cross-call / printed state path | `test_cross_call_vars.py`, `test_inline_python_isolated.py`, `test_pasted_name_guard.py` | Good |

Stated limits, unchanged: the range route is thin, pause/resume is thin, and `--all` keeps no decisions. G1 is the binding suite gate. G3 exists so this record can report each route.

## Fingerprints and frozen files

- `docs/design/lean-v2.15/baseline`: 10 of 10 files match MANIFEST.json by sha256. `baseline_commit` = dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4 (v2.14.1).
- The folder is unchanged since the Phase 62 merge: `git diff --quiet d0adb5b "$C" -- docs/design/lean-v2.15/baseline` exit 0.
- GOLDEN_DIGEST in `plugins/vibe-check/scripts/test_score.py` is `7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124` at both C and v2.14.1.
- G10: `score.py`, `replay.py` and `test_replay.py` are byte-identical to v2.14.1. G4a confirms both scorers hash to the same sha256 (`c6488729…f725`).
- Together these show that the scoring formula, the replay safeguard and the baseline kit used to judge this release were not changed by the release. G4b shows no protected catch was lost: 25 of 26 kept, the 26th counted under standing amendment 008, `REGRESSED 0`, `UNEVALUABLE 0`.

## Accepted differences

From 65-RESEARCH §Accepted differences (63-RESULT decisions 1–5, D-27, D-19; owner go 2026-11-15):

1. Unreadable state file: the shell's "Permission denied" line no longer shows; the stop sentence shows alone.
2. Unsafe-name stop (D-21): a folder, branch or phase name with `$`, a backtick, `"`, `\` or a line break stops the review with one "Review halted" line.
3. Phase-end growth on every review path (the D-09 items; see D-09 reconciliation).
4. C-locale refusal line for a saved-progress file that is not valid UTF-8: `refused: state is not valid JSON` instead of `refused: malformed state: passes`.
5. Carried review items (63-REVIEW WR-02/WR-03/WR-04/SA-01/C2/SA-03; R2-WR-01..03 and set-aside items) → backlog 999.36/999.38.
6. D-27: 60-second limit on each helper git call; a slower git leaves that file out (the finding stays open).
7. D-19: from a subfolder, a file with unsaved or staged edits is not fingerprinted (a fix-obsolete verdict no longer closes on changed code).

Observed in G5b:
- `differs` lines: none. All 7 walks print `outcome fields match`.
- Intended differences: only the command lists (D-15). For each walk, these are the `steps` before/after lines and the `tally.commands_run`, `tally.values_carried` and `tally.writes` lines. Example: clean-close goes from 8 steps (blobfile, counts, state-present, gatefile, gate, decisions-report, prior-review-archive, archive-state) to 3 (finalize-inputs, prior-review-archive, archive-state).
- Fault stand-ins: like-for-like outcome fields match the record. All three refusal lines are `2.14.1 and now identical`.
- Item 3 is observed in G6 and reconciled there. Items 1, 2, 4, 6 and 7 are covered by named tests inside G1, not by the five situations.

Unmapped differences: 0

## Counts (direct recount, D-06)

Printed in this session by `plugins/vibe-check/scripts/footprint.py --rev <r> --json` (bytes) and `docs/design/lean-v2.15/tools/step_count.py --rev <r> --mode <m> --json` (`totals.model_run_steps`) at dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4 (2.14.1) and b073e31fb77f3f5ca32747f8c549ec552687b1be (C). No figure was copied from a record.

Raw tool output:

```
== dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4
{'review-plain': 192057, 'review-all': 284926, 'deep-plain': 268997, 'deep-all': 361866, 'finalize': 136114, 'fix-loop': 255070}
finalize 92 · review-plain 36 · deep-plain 42 · review-all 45 · deep-all 51 · fix-loop 112 (steps)
== b073e31fb77f3f5ca32747f8c549ec552687b1be
{'review-plain': 193762, 'review-all': 286880, 'deep-plain': 270714, 'deep-all': 363832, 'finalize': 131381, 'fix-loop': 256939}
finalize 85 · review-plain 38 · deep-plain 44 · review-all 47 · deep-all 53 · fix-loop 114 (steps)
```

| Path | Bytes 2.14.1 | Bytes C | Δ bytes | Δ % | Steps 2.14.1 | Steps C | Δ steps |
|------|-------------|---------|---------|-----|-------------|---------|---------|
| Finalize | 136,114 | 131,381 | −4,733 | −3.48% | 92 | 85 | −7 |
| Plain review | 192,057 | 193,762 | +1,705 | +0.89% | 36 | 38 | +2 |
| Deep review | 268,997 | 270,714 | +1,717 | +0.64% | 42 | 44 | +2 |
| Plain review `--all` | 284,926 | 286,880 | +1,954 | +0.69% | 45 | 47 | +2 |
| Deep review `--all` | 361,866 | 363,832 | +1,966 | +0.54% | 51 | 53 | +2 |
| Fix loop | 255,070 | 256,939 | +1,869 | +0.73% | 112 | 114 | +2 |

Byte and step counts only; these are size counts of the instruction text and of the commands the model runs, not usage or price figures, and no lower bill is claimed.

The recount equals the 65-CANDIDATE.md table, which was counted at d31787d.

## D-09 reconciliation

Per changed instruction file, bytes at dd8e4ab → C (`git show <rev>:<file> | wc -c`). Itemised rows: Phase 63 D-09 rows from 63-COUNTS (via 65-RESEARCH), plus 65-03 named growth from 65-REPRO-WR02.md "## Named growth from the fix".

| File | Δ bytes measured | Itemised rows | Sum | Match |
|------|------------------|---------------|-----|-------|
| phases/review/00-scope.md (20,088 → 20,617) | +529 | X1 +211, D-21 +169, 65-03 WR-02 +149 | +529 | yes |
| phases/review/05-state.md (19,484 → 20,699) | +1,215 | X2 +110, X3 +82, X2+X3 +245, D-21 +432, 65-03 WR-02 +346 | +1,215 | yes |
| phases/review/06-config.md (15,463 → 15,424) | −39 | X4/X5/X6 −13 each | −39 | yes |
| phases/review/05-state-all.md (5,753 → 6,002) | +249 | D-22 +6, D-23 +243 | +249 | yes |
| phases/review/50-fix-loop.md (63,013 → 63,177) | +164 | D-20 +124, D-22 +9, D-23 +31 | +164 | yes |
| phases/shared/90-finalize.md (55,923 → 49,485) | −6,438 | extraction −6,663, D-20 +185, D-22 +9, D-23 +31 | −6,438 | yes |
| phases/deep-review/2c-codex-kickoff.md (17,667 → 17,673) | +6 | D-22 +6 | +6 | yes |
| phases/deep-review/30-codex-collect.md (13,440 → 13,443) | +3 | D-22 +3 | +3 | yes |
| phases/deep-review/01d-coverage.md (26,021 → 26,024) | +3 | D-22 +3 | +3 | yes |

Per path: the Phase 63 end figure plus the 65-03 +495 bytes (both files load on every path) equals the recount on every path. Plain review +1,210 + 495 = +1,705; deep review +1,222 + 495 = +1,717; plain `--all` +1,459 + 495 = +1,954; deep `--all` +1,471 + 495 = +1,966; fix loop +1,374 + 495 = +1,869; Finalize −5,228 + 495 = −4,733.

Steps: every path loads `05-state.md` and `06-config.md`, so each gets X2 +1, X3 +4 and X4–X6 −3, net +2. Finalize also gets the extraction (−9), so −9 + 2 = −7. The 65-03 fix added no Bash fence (0 steps). The measured Δ steps (+2 on each of the five review paths, −7 on Finalize) equal these sums.

Unitemised growth: 0

**Note for the owner (Pitfall 9).** "~0.6%" describes only one path and is not accurate here. Measured on C, review-path growth runs from +0.54% (deep `--all`) to +0.89% (plain review) in bytes. Every review path also gains 2 counted steps: the 5 review paths go from 36/42/45/51/112 steps to 38/44/47/53/114 (plain review +5.6% in steps). That is +2 from the Phase 63 cross-call fixes, and the 65-03 fix added 0 steps. Research expected +0.41% to +0.63% before the 65-03 fix. The fix adds 495 bytes to every path, which accounts for the higher range. The README size line (65-CANDIDATE.md fact-check) already uses +0.5% to +0.9% and +2 steps.

**Maintenance added** (helper and test code, at C, reported separately from the instruction counts as Phase 62 D-03 requires; all new since 2.14.1):

| File | Lines | Bytes |
|------|-------|-------|
| `scripts/finalize_inputs.py` (shipped helper) | 481 | 19,723 |
| `scripts/test_finalize_inputs.py` | 2,343 | 107,989 |
| `scripts/test_finalize_parity_grid.py` | 1,387 | 60,594 |
| `scripts/test_cross_call_vars.py` | 1,732 | 78,883 |
| `scripts/test_pasted_name_guard.py` | 542 | 25,699 |
| `scripts/test_inline_python_isolated.py` | 253 | 10,552 |

`git diff --stat v2.14.1 "$C" -- plugins/vibe-check/scripts`: 15 files changed, 7,746 insertions, 636 deletions. This includes the files above plus `fixtures/finalize_step1_2141.sh` (+43) and reworked existing tests (`test_finalize_card.py`, `test_score.py`, `test_carry_state.py`, `test_confirmed_fix.py`, `test_diff_ranges.py` and others).

## D-07 outcome (WR-02)

From [65-REPRO-WR02.md](65-REPRO-WR02.md):

- Verdict: QUALIFYING — wrong close — owner D-08 go required
- Owner go: GRANTED (owner, 2026-11-16)
- Fix round: RAN — the one D-08 round (plan 65-03), test-first. RED `976e3fe`, GREEN `b281042`.

C contains the fix. Its tests (`TestStateFileGuard` empty/unset id, `TestPhaseIdPrinted`, `TestRepro63::test_wr02_empty_phase_id`) pass inside G1 and G3. The one fix round is spent: any later qualifying gate failure needs the owner's explicit go for a second round (D-09).

## Dependencies and Dependabot

From [65-CANDIDATE.md](65-CANDIDATE.md) "## Dependabot (before the bump)", run 2026-11-16 at d31787d:

- Open-alerts call: HTTP 403, "Dependabot alerts are disabled for this repository". The CLI also lacks the `admin:repo_hook` scope.
- `gh pr list --author app/dependabot --state open`: no open Dependabot pull requests.
- No setting was changed.

G8 on C confirms the shipped runtime is standard-library only (`34 shipped .py files; third-party imports: none`); pytest is test-only. There is nothing to roll into this release.

## Carried

No gate in this run produced a non-qualifying difference to carry (D-10). Standing carries, unchanged by this gate:

- 999.34: Phase 62 review carry. Baseline checks pass inputs they should reject. This gate bypassed them by recounting both commits directly (G6) and hashing the kit directly (G7).
- 999.36: cross-call variable check, remaining exception and known limits.
- 999.38: Phase 63 review carry (WR-03, WR-04 and others). WR-02 is fixed by `b281042`. The correction to 999.38's "none is a regression from 2.14.1" wording belongs to 65-07, per 65-REPRO-WR02.md.
- G9 directory warnings (ICON_MISSING, untracked `.DS_Store` files): same as at 2.14; they do not block the validation result.

## Residuals (linked)

- [63-RESULT.md](../63-finalize-extraction-and-cross-call-variable-check/63-RESULT.md)
- [63-REVIEW.md](../63-finalize-extraction-and-cross-call-variable-check/63-REVIEW.md)
- [63-REVIEW-2.md](../63-finalize-extraction-and-cross-call-variable-check/63-REVIEW-2.md)

## Live smoke (D-01/D-02)

Effective outcome: PASS

Source: [65-LIVE-SMOKE.md](65-LIVE-SMOKE.md), its only run (the file has no `## Run N` re-run sections, so the top-level `## Verdict` is the last run), on `C: b073e31fb77f3f5ca32747f8c549ec552687b1be`, which equals `candidate:` in 65-CANDIDATE.md. Run 2026-11-16 under the owner-approved proposal (65-LIVE-SMOKE-PROPOSAL.md, `Status: APPROVED (owner, 2026-11-16)`): three fresh sessions on a sealed snapshot of C, all three VALID (every plugin path in every transcript under the snapshot; 0 under the repo or the cache).

- S1, default review: the planted SQL-injection defect was flagged as row #1; both rows deferred with one `record-decisions` call; the Rerun ran pass 2 and the deferrals held.
- S2, Close out with nothing open: one `finalize_inputs.py` call, `next = write-review-md`, REVIEW.md written with `**State format:** 53`, state archived, `review-closed` exit 0, the "Finalize stopped" sentence never printed.
- S3, Close out through the decision card: the card listed both undecided rows, the typed defer was recorded, the inputs were re-run with a new BLOBFILE, `next = write-review-md`, REVIEW.md lists both deferred findings; the earlier REVIEW.md and archive were kept, not overwritten; `review-closed` exit 0.

So the default review, Close out and Close out's decision card all ran live on C. The printed `STATE_FILE=` path was carried as the same literal in all three sessions. Carried items K1–K4 are in 65-LIVE-SMOKE.md `## Carried (D-10)`; none qualifies.

## Unsupported fixtures and stated limits

Stated limits, unchanged from 2.14 and listed in the README:
- The range route (`A..B`) has thin test coverage (G3 route table).
- Pause/resume has thin test coverage and no end-to-end walk, live or offline.
- `--all` keeps no decisions between runs; each `--all` run starts fresh.

User-visible items carried from the live smoke (not qualifying; 65-LIVE-SMOKE.md `## Carried`):
- K1: after every finding is deferred in the fix loop, the Rerun pass has an empty card and the model may stop and ask instead of continuing. Decisions and state are saved; Close out then completes. One extra step, nothing lost. Listed as a Known limit in the release notes only (the README is part of the gated tree and was not changed).
- K3: Close out can write REVIEW.md's audit-trail line naming the archive before the final archive name is known; in S3 the model corrected the line itself. Wording only; no state lost.
- K2 (band rise between passes with no code change) is designed behaviour (same as Phase 61 C2) and never hides a finding; K4 is a harness retry, not user-visible.

## Validation gaps and waivers

Everything below was not proven live for 2.15.0. Each needs the owner's waiver at sign-off.
- GSD, range, PR, incremental pass 2+ and `--all` reviews are proven offline only (D-02; G1–G3); the GSD route carries the WR-02 empty-phase-id stop, which is proven by tests only — waiver: granted (owner, 2026-11-16) (65-SIGNOFF.md)
- The fix loop's fix-and-verify path is proven offline only (D-02; G1, G3 and the fix-verification run); the live smoke reached only its card and Rerun with deferrals — waiver: granted (owner, 2026-11-16) (65-SIGNOFF.md)
- Pause/resume has no end-to-end walk, live or offline — waiver: granted (owner, 2026-11-16) (65-SIGNOFF.md)
- No B3 or holdout measurement, so there are no 2.15 catch or false-alarm numbers; v2.11 remains the last measured result — waiver: granted (owner, 2026-11-16) (65-SIGNOFF.md)

WR-02 is not carried: it was fixed before release (b281042) and is covered by tests inside G1 and G3.

## Publish status

GATE-04/05/06 "ships through the existing close workflow": pending close — see [65-CLOSE-RUNBOOK.md](65-CLOSE-RUNBOOK.md).
G12 (CI `offline-suite` green on the PR head): pending close — runbook step 4.
Nothing has been pushed, tagged, merged or released from this phase.

## Post-sign-off review carry (2026-11-16)

The phase code review (65-REVIEW.md: 0 critical, 1 warning, 2 info) and security audit (65-SECURITY.md: 27/27 closed, threats_open 0) ran after sign-off. Owner ruling (AskUserQuestion, main session, 2026-11-16): "Ship + backlog (Recommended)". Candidate C (b073e31) is unchanged; the pre-2.15 duplicate-phase-folder lookup gap (SA-01) is added to the release notes as a known limit (notes are not part of the gated tree) and, with the 05-state.md wording overclaim (WR-01), carried as backlog 999.39.
