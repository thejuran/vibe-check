---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 04
subsystem: test-suite / instruction lint
tags: [xvar, cross-call, reproduction, fresh-shell, tdd]
requires:
  - "63-03: test_cross_call_vars.py EXCEPTIONS X1-X6 and KNOWN_LIMITS"
provides:
  - "test_cross_call_vars.py: fence_holding, substitute, tree_files, ShellRun, classify, OUTCOMES, REPRO_63, PROPOSED_FOR, record_problems, TestRepro63, TestRepro63Record"
  - "63-REPRO.md: repro standard, known limits, one section per flagged place, proposed split"
affects: [63-09, 63-10]
tech-stack:
  added: []
  patterns: ["fresh bash -s per block next to a one-shell control (test_finalize_card _run_fresh shape)", "identical repo copies named repo for fresh and control", "record lock with exact-message mutants (TestRepro60Record shape)"]
key-files:
  created:
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REPRO.md
  modified:
    - plugins/vibe-check/scripts/test_cross_call_vars.py
decisions:
  - "All six flagged places reproduce: X1 and X3 stop, X2 wrong-file, X4/X5/X6 ignored-setting"
  - "Proposed split (owner confirms in 63-09): X1, X2, X3 fix; X4, X5, X6 owner decides; none pinned"
  - "An empty repo root does not make config.py refuse; it reads no settings file and returns defaults, so X5 is ignored-setting, not stop"
metrics:
  duration: "~40 min"
  completed: 2026-11-14
requirements: [XVAR-02]
---

# Phase 63 Plan 04: Fresh-shell reproductions of the flagged places Summary

Each of the six places the cross-call check flags now has an executable fresh-shell reproduction. The test takes the real Bash blocks from the live instruction file and runs each one in its own shell. A control runs the same blocks in one shell and must finish as intended. The outcome class comes from exit codes, output and files on disk. Result: 6 flagged, 6 reproduced (2 stop, 1 wrong-file, 3 ignored-setting). No instruction file was changed.

## Proposed split (owner confirms in 63-09)

| Id | File | Variable | Outcome | What the owner would see | Proposed |
|----|------|----------|---------|---------------------------|----------|
| X1 | phases/review/00-scope.md | PHASE_DIR | stop | A GSD-phase review stops at the safety check ("Phase resolution escaped .planning/ — refusing.") although the phase exists | fix |
| X2 | phases/review/05-state.md | LEGACY_STATE_FILE | wrong-file | Saved progress in the old location is not moved forward, so the review restarts at pass 1 | fix |
| X3 | phases/review/05-state.md | STATE_FILE | stop | A second pass stops with "last-pass head_sha is not a commit sha" although the saved progress is fine (Close-out also stops) | fix |
| X4 | phases/review/06-config.md | CODEX_FLAG_VAL | ignored-setting | `--codex off` has no effect; Codex stays on auto | owner decides |
| X5 | phases/review/06-config.md | CONFIG_REPO_ROOT | ignored-setting | The repo's settings file is never read; everything falls back to defaults | owner decides |
| X6 | phases/review/06-config.md | MIN_CONFIDENCE_FLAG_VAL | ignored-setting | `--min-confidence 45` has no effect; nothing is filtered | owner decides |

Full commands and real outputs, with exit codes for the fresh run and the control, are in `63-REPRO.md`.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Fresh-shell reproductions for 00-scope.md and 05-state.md | 7a520bb (test, RED), 2aa59df (feat, GREEN) |
| 2 | Reproductions for 06-config.md, the record lock and 63-REPRO.md | c34bad8 (test, RED), 9efb67d (feat, GREEN), 52cd356 (docs, record) |

## Verification (observed)

- `pytest -q -p no:cacheprovider test_cross_call_vars.py`: 58 passed, 78 subtests passed (was 44 passed / 73 subtests after 63-03).
- Task 1 check: REPRO_63 rows for 00-scope.md and 05-state.md equal the EXCEPTIONS pairs for those files, and every outcome is one of the four classes. Printed `OK`.
- Task 2 check: the REPRO_63 ids equal the EXCEPTIONS ids (`X1 X2 X3 X4 X5 X6`). 63-REPRO.md has `## Repro standard`, `## Known limits` and `## Proposed split`, plus one `## Xn — ` section per id, each carrying all five bold fields (6 of each).
- `git diff --quiet dd8e4ab… HEAD -- plugins/vibe-check/phases` exited 0 after every commit. No instruction file changed.
- Mutants were checked by their exact messages: removing the X1 row gives `no record row for X1`, a misspelled fixture gives `X1: no fixture …_typo`, an unknown outcome gives `X1: unknown outcome 'flaky'`, and a proposal off the rule gives `X1: proposed 'pin' does not follow the rule`. The fourth mutant goes beyond the three the plan asked for.
- `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_cross_call_vars.py .github/scripts docs/design/lean-v2.15/tools`: 503 passed, 328 subtests passed.
- `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`: "34 shipped .py files; third-party imports: none", exit 0.
- **Not run here:** the full ~16-minute suite. Per the orchestrator's instructions, it runs in the main checkout after the wave merges. No skip decorator was added.
- RED runs: Task 1 RED failed 3 tests on `NameError: fence_holding`. Task 2 RED failed the 5 record-lock tests on `NameError: record_problems`. The X4–X6 fixtures passed at Task 2 RED because they only use the Task 1 runner and observe today's behaviour.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fresh and control repos copied from one base, both named `repo`**
- **Found during:** Task 1 probe.
- **Issue:** The repo-and-branch state key is built from the repo folder's name. With copies named `fresh`/`control`, the control looked for `control-main.json` and failed. That was a broken fixture, not a reproduction.
- **Fix:** `ShellRun` builds one base repo and copies it to `fresh/repo` and `control/repo`. The commit ids and the key are then identical in both runs.
- **Cost if wrong:** none for the verdicts. A fixture whose control fails raises instead of classifying.
- **Commit:** 2aa59df

**2. [Rule 2 - Isolation] Two git-config variables added to the fixture environment**
- The plan names PATH, VC_ROOT, TMPDIR, GUARD_PY and CONFIG_PY. The runner also sets `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`, the same isolation every `gitfixture` test uses (T-63-12), so the owner's git config never leaks in. No flagged variable is supplied.
- **Cost if wrong:** none. These variables only switch off the user's own git config.

**3. [Rule 3 - Observation] One print line added after the 06-config invoke block in both runs**
- The settings block prints nothing, so neither run would show `CONFIG_JSON`. The same `printf 'CONFIG_JSON=%s\n' "$CONFIG_JSON"` line is appended in the fresh run and in the control. It is stated in 63-REPRO.md.
- **Cost if wrong:** low. Because the line is added the same way to both runs, it cannot cause the difference between them.

**4. [Rule 3 - Blocking] Verify commands split**
- The harness refuses compound `git` commands in this worktree, so each `<verify>` was run as plain separate commands with the same content. Results are above.

## Assumption Drift (advisory)

**X5's outcome is ignored-setting, not stop**
- **Found during:** Task 2
- **Planned:** The behavior list allowed that an empty `CONFIG_REPO_ROOT` might make the helper refuse (`stop`).
- **Actual:** `config.py` treats an empty `REPO_ROOT` as "no settings file". It exits 0 with the defaults and no warning, so the repo's `.vibe-check.toml` is silently ignored.
- **Why it matters:** X5 lands in "owner decides" rather than "fix" under the rule.
- **Cost if wrong:** The owner might under-rate X5. Every setting in the repo file is lost on every review, which makes it the broadest of the three ignored settings.

**X2 is wrong-file, not stop**
- **Found during:** Task 1
- **Planned:** No class was predicted.
- **Actual:** With empty names, the move-forward helper finds nothing, exits 0 and says nothing. The review does not halt; it carries on with the saved progress left behind.
- **Cost if wrong:** low. Under the rule, wrong-file is still proposed as fix.

## Known Stubs

None.

## TDD Gate Compliance

`test(63-04)` 7a520bb → `feat(63-04)` 2aa59df → `test(63-04)` c34bad8 → `feat(63-04)` 9efb67d. RED came before GREEN for both tasks.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/test_cross_call_vars.py
- FOUND: .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REPRO.md
- FOUND commits: 7a520bb, 2aa59df, c34bad8, 9efb67d, 52cd356
