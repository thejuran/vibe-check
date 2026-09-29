---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 07
status: complete-with-blocker
subsystem: measurement-runbook
tags: [scorer-05, d-10, d-11, d-12, d-13, d-16, batchsnap, spot-check, runbook]
requires: ["41-04 B-SEV (c02d9b1)", "41-05 B-REWEIGHT (0ee3818)", "41-06 H-LANE (ccf69fc) + D-16 picks"]
provides:
  - "batchsnap.py BATCH_PLANS[4] = 41-04/05/06; NEVER_REVERT += 41-01/02/03/07/08; KNOWN_PLANS = 40-01..14 + 41-01..08; generic 'unknown plan id' refusal"
  - "docs/design/b3-ground-truth/runs-v2.10-phase41/PLAN-COMMITS.json (c02d9b1, 0ee3818, ccf69fc)"
  - "docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase41.md (pins + empty fingerprints heading)"
  - "docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase41.md (owner runbook, 19 named blocks)"
  - "snapshot ~/.vibe-check-snapshots/batch4-cd8f5b00de73 (verified, 110 files, suite 1119 passed / 1 skipped)"
affects: [41-08 adjudication, Phase 43 snapshots (test_replay now passes in a linked worktree)]
tech-stack:
  added: []
  patterns: ["runbook per-diff blocks generated from one template, values read from the provenance sidecars", "local-only evidence tests expect zero in a linked worktree, all in the primary checkout"]
key-files:
  created:
    - docs/design/b3-ground-truth/runs-v2.10-phase41/PLAN-COMMITS.json
    - docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase41.md
    - docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase41.md
  modified:
    - plugins/vibe-check/scripts/batchsnap.py
    - plugins/vibe-check/scripts/test_batchsnap.py
    - plugins/vibe-check/scripts/test_replay.py
    - .gitignore
decisions:
  - "Spot-check pair = should-quiet-3 (predicted 2/3) + should-quiet-1 (3/3, D-16 tie to the lower number); predicted FP for the 6 runs = 5; D-11 passes at <= 5 firing runs"
  - "Phase-41 STEP 0 re-adds the installed-cache parity gate and adds clone-clean + N-02 memory-park gates; auto-memory written mid-check is moved aside before each run"
  - "Phase-41 run transcripts are gitignored like Phase 40's (private instructions in a published repo)"
metrics:
  duration: "~13 min"
  completed: 2026-09-29
  tasks: "3/3"
  files: 7
---

# Phase 41 Plan 07: SCORER-05 spot-check hand-over — Summary

The owner now has a runbook for the six live runs that test the Wave-1 scorer. The two diffs and
the predicted count are written into it before run 1: **should-quiet-3 (predicted 2/3) and
should-quiet-1 (predicted 3/3), so at most 5 of the 6 runs may fire.** The runbook runs against a
verified snapshot, `~/.vibe-check-snapshots/batch4-cd8f5b00de73`. The snapshot tooling now treats
the three scorer commits as one rollback unit (batch 4).

**Hand-over is blocked on one owner action.** The STEP 0 pre-flight ran on this machine and every
snapshot, seal, parity, CLI and memory gate passed. It then stopped at the clone-clean gate: the
owner's `~/roonseek` has an uncommitted `.planning/ROADMAP.md` edit (a "UI review remediation"
backlog line) and an untracked `.codex-review/` folder. That is the owner's own work, so the
runbook does not touch it. Committing it or moving it aside clears the gate. Because of that stop,
`~/.b3/phase41-active.env` was not written, so the Task 3 `<verify>` chain exits 1 at its last
check (`test -f ~/.b3/phase41-active.env`). Every check before that one passed.

**Hand-over line:** snapshot `~/.vibe-check-snapshots/batch4-cd8f5b00de73` (`verify` exit 0,
110 files, last line `plugin_root: …/batch4-cd8f5b00de73/plugins/vibe-check`); picks
should-quiet-3 + should-quiet-1, predicted FP 5/6. Once `~/roonseek` is clean, the owner runs
6 × `/vibe-check:deep-review` per `docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase41.md`, and
41-08 adjudicates.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | `86c1914` | batchsnap.py batch 4 + generic allowlist, tests, PLAN-COMMITS.json |
| 2 | `1a1f02b` | RUN-METHOD-NOTES-phase41.md, SPOT-CHECK-v2.10-phase41.md, .gitignore |
| 3 (Rule 3) | `cd8f5b0` | test_replay.py: expect zero local-only transcripts in a linked worktree |
| 3 | `057880a` | runbook: snapshot batch4-cd8f5b00de73 pinned |
| 3 (Rule 1) | `76a646c` | runbook: restore-memory no longer needs the active-check file |

## Task 1: batchsnap batch 4 (observed)

- The revert set is schema-consistent. `git show --stat=200 --format= ccf69fc -- plugins/vibe-check`
  lists all seven files: `score.py`, `fixtures/future-schema.json`, `test_state_shape.py`,
  `phases/review/30-collect-score.md`, `test_score.py`, `templates/output-format.md` and
  `templates/scoring.md`. The grep for the three named files returned 3.
  - Note: the plan's literal command (`git show --stat` without `--format=`) returns 5, because
    the commit message also names those files.
  - Each of the three recorded commits touches `plugins/vibe-check/scripts/score.py` (1 each).
- `record-commit` wrote `PLAN-COMMITS.json` with the full shas. `commit-set --batch 4` emits
  newest-first: `ccf69fc…`, `0ee3818…`, `c02d9b1…`.
- `pytest test_batchsnap.py -q`: **89 passed**. The plan's verify chain printed `BATCHSNAP OK` and
  `RECORDED-OK`. The full suite after the commit: **1120 passed, 1123 subtests**.
- **Mutation proofs** (each applied to batchsnap.py, `TestCommitSet` + `TestRecordCommit` run,
  file restored and `cmp`-checked):

  | mutation | result |
  |---|---|
  | `41-01` planted in `BATCH_PLANS[4]` | 4 failed |
  | `41-01` dropped from `NEVER_REVERT` | 3 failed |
  | `KNOWN_PLANS` extended to `41-09` | 3 failed |
  | refusal text reverted to `unknown Phase-40 plan id` | 1 failed |

- `timeout=120` count is 3 against 2 `subprocess.run(` calls, which was already true at HEAD~
  because the docstring mentions it once. Both real calls carry it. `TestImportSet` is unchanged.
- `test_refuses_unknown_plan_id` used `41-01` as its unknown id. That id is now valid, so the
  test uses `41-09`.

## Task 2: notes + runbook (observed)

- The Task 2 `<verify>` chain printed `RUNBOOK-OK`.
- The notes file has exactly one anchored match for each of the three pins and ends with
  `## Harness fingerprints — Phase 41`.
- The runbook has the 12 numbered sections plus the MEASUREMENT-RUN RULE, in the Phase-40 order.
  All **17 fenced bash blocks parse** (`bash -n`, one per block). There are 19 `# BLOCK:` names
  (some fences hold two), 19 `BLOCK OK` lines and 223 `STOPPING` lines.
- `plugins/cache/` occurs 5 times, and all 5 are `plugins/cache/thejuran/vibe-check`.
- The sidecar values (base_sha, EXPECTED_TREE_DIFF_SHA256, EXPECTED_TOUCHED_PATHS) are read from
  `diffs/should-quiet-{1,3}.provenance` by a generator, and each appears in the runbook (7/4/4
  occurrences per diff).
- The `Plugin rollback (batch 4)` paragraph sits outside every fence (awk fence-state check).
- The §3 table matches the combined report: sq1-sq6 baseline 3,3,3,3,1,3 → combined 3,3,2,3,0,3;
  sq5 is skipped (0/3 post-diet) and sq7 is ineligible (ledger 001).

## Task 3: snapshot + smoke + STEP 0 (observed)

- `batchsnap.py build --batch 4 --commit cd8f5b0…` exited 0 and created
  `~/.vibe-check-snapshots/batch4-cd8f5b00de73`, with the commit set `ccf69fc`, `0ee3818`,
  `c02d9b1`. The manifest's `suite_green` is `1119 passed, 1 skipped, 1123 subtests passed`. The
  skip is the transcript-recovery test, which cannot run in a worktree.
- `verify --snap` exited 0 and printed `snapshot verified: 110 files`, then
  `plugin_root: …/batch4-cd8f5b00de73/plugins/vibe-check`.
- The snapshot's `score.py` is `cmp`-identical to HEAD's. `"status": "joined"` appears once in
  its `30-collect-score.md`, and `"members"` appears once in its `future-schema.json`.
- **Snapshot smoke:** the archived `runs-v2.10/should-quiet-1/run-3` envelope has **5 rows**.
  Run through the snapshot's scorer it comes out as **2 rows**, and both carry `members`:
  - `bugs` warning at :84, with 4 members (bugs:84, bugs:85, security:85, impact:85)
  - `impact` medium at :77
- **STEP 0, run by the assistant.** It was extracted with the runbook's own awk helper and fed
  `final` on stdin. It never launches Claude Code.
  1. As written, with memory in place, it passed gates (a)-(g) and stopped at the N-02 memory
     gate: `~/roonseek AUTO-MEMORY IS NOT PARKED — run p41 park-memory — STOPPING`. That gate is
     working as intended.
  2. After `p41 park-memory` (`BLOCK OK`), the tail was:
     ```
     Which check is this? Type exactly one of final or final-2:  M .planning/ROADMAP.md
     ?? .codex-review/
     CLONE ~/roonseek NOT CLEAN — commit or move YOUR work aside first — STOPPING
     ```
     The rc was 1, and `~/.b3/phase41-active.env` was not written. Gates (a)-(h) had all passed
     by then:
     - the Phase-40 final PASS.json is valid
     - the snapshot is verified; its manifest says batch 4 and a green suite, and the folder
       name matches its commit
     - the installed vibe-check 2.9.0 equals the repo's 2.9.0
     - the sealed trees for v2.9 `runs/`, `runs-v2.10` (`82c412b…`) and `runs-v2.10-phase40`
       (`29d1344…`) are intact
     - both CLIs answer
     - memory is parked

     `~/triggarr` was checked by hand afterwards: clean, on `main`, exclude present, `uv.lock`
     present.
  3. The owner's memory was restored. After the Rule-1 fix, the `park-memory` → `restore-memory`
     round trip also ran to `BLOCK OK` twice. Both memory dirs are back in place and the
     `~/.b3/automemory-parked-phase41-final` folder was removed.
- `git status --porcelain docs/design/b3-ground-truth plugins/vibe-check` is empty after the last
  commit.

## Deviations from Plan

1. **[Rule 3 - Blocking] `batchsnap build` refused every batch-4 snapshot.**
   - **Issue:** 3 `test_replay.py` tests failed inside the snapshot. The 12 Phase-40 transcripts
     are gitignored, so they never exist in a linked worktree, and the Phase-40 snapshots predate
     41-02's tests.
   - **Fix:** in a linked worktree the census and baseline-report tests now expect **0**
     transcripts, and the recovery test skips. The primary checkout still requires all 12.
   - **Mutation:** forcing worktree mode in the primary checkout gives 2 failed.
   - **Commit:** `cd8f5b0`. Phase 43's snapshots would have hit the same refusal.
2. **[Rule 2 - Security] Phase-41 transcripts gitignored.**
   - **Issue:** `.gitignore` covered only `runs-v2.10-phase40/**/transcript.jsonl`. The post-run
     block runs `git add "$RP/"`, which would have committed a transcript carrying the owner's
     private instructions to a published repo.
   - **Fix:** added the `runs-v2.10-phase41/**/transcript.jsonl` line. The post block also now
     checks `check-ignore` BEFORE staging; Phase 40 checked after the commit.
   - **Commit:** `1a1f02b`.
3. **[Rule 1 - Bug] `restore-memory` could not undo a park when pre-flight stopped.**
   - **Issue:** found by the proof run. The block read the active-check file, which is not
     written when pre-flight stops.
   - **Fix:** the block now asks for the label, the same way `park-memory` does.
   - **Commit:** `76a646c`.
4. **[Plan AC wording] The `git show --stat <sha> | grep -c` = 3 check.** Without `--format=` it
   counts 5, because the commit message names the files. It was checked with `--format=` (= 3),
   and the full file list is quoted above.
5. **[Runbook additions beyond the Phase-40 copy, each stricter]:**
   - `park-memory` / `restore-memory` blocks
   - pre-run blocks move any auto-memory a session wrote since launch into an evidence folder,
     so run 2/3 cannot read what run 1 learned
   - the launch blocks refuse while memory is present
   - pre-flight pins the closed `runs-v2.10-phase40` tree
   - the post block prints the codex status, puts it in the run's commit message, and PASS.json
     gets a `codex_status` field per run (`check_pass_artifact` ignores extra keys)

## Assumption Drift (advisory)

- **Found during:** Task 2.
- **Planned:** the plan's read_first expected the picks should-quiet-2 + should-quiet-3.
- **Actual:** the picks are should-quiet-3 + should-quiet-1.
- **Why:** among eligible diffs, the combined replay moved only should-quiet-3. sq1, sq2, sq4 and
  sq6 tie at 0 movement, and D-16 gives the tie to the lower number. The research prediction for
  the combined headline was 12/18; the replay measured 14/18. The runbook §3 records both as
  observed.

## Known Stubs

- The runbook's `FINAL2_SNAP=''` is intentionally empty. It is pinned by the assistant only after
  a D-11 miss and the one D-12 re-tune, and pre-flight STOPS on `final-2` while it is empty.

## Threat model

- T-41-31: verify in every block; the narrowed provenance grep plus the positive `$PLUGIN_ROOT`
  check.
- T-41-32: the STEP 0 parity gate (observed passing: 2.9.0 == 2.9.0).
- T-41-33: the fingerprint block is unchanged in form (committed-blob binding).
- T-41-34: the N-02 gate was observed tripping, and the park/restore round trip was proven.
- T-41-35: `NEVER_REVERT` asserted inside `commit_set`, with mutation proofs.
- T-41-39: the §11 rollback paragraph.
- New surface: the transcript gitignore gap (deviation 2), closed.

## Self-Check: PASSED

- FOUND: docs/design/b3-ground-truth/runs-v2.10-phase41/PLAN-COMMITS.json
- FOUND: docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase41.md
- FOUND: docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase41.md
- FOUND: ~/.vibe-check-snapshots/batch4-cd8f5b00de73
- FOUND: commits 86c1914, 1a1f02b, cd8f5b0, 057880a, 76a646c
- NOT MET (environmental, owner action): STEP 0 `BLOCK OK` / `~/.b3/phase41-active.env`
