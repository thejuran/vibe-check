---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
reviewed: 2026-11-16T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - README.md
  - plugins/vibe-check/.claude-plugin/plugin.json
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/scripts/test_cross_call_vars.py
  - plugins/vibe-check/scripts/test_pasted_name_guard.py
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Phase 65: Code Review Report

**Reviewed:** 2026-11-16
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Scope: `git diff a6d29d2..HEAD` on the six files. The code change is the WR-02 fix (b281042): an empty-id refusal at the top of the GSD state-key fence in `05-state.md`, and a `PHASE_ID=` print in the `00-scope.md` resolution fence. There are also two lock suites, the 2.15.0 README block, and the version bump.

**Shell correctness of the new lines.** I found no defect.
- `[ -n "${PHASE_ID}" ] || { ...; exit 1; }` trips on an empty literal, an empty variable and an unset variable. It runs before any `STATE_FILE=` line is printed, so nothing is bound on a stop.
- `PHASE_ID=$(basename "$PHASE_DIR")` runs after the `PHASE_DIR` character guard, so the printed id cannot carry `$`, a backtick, `"`, `\`, CR or LF.
- `basename ""` prints an empty line on macOS/BSD (checked) and on GNU, so a failed resolution prints `PHASE_ID=`. That empty value is exactly what the new refusal stops on.
- The guard does not trip falsely when a non-empty literal is substituted. It is only in the GSD block; `--all` replaces that block via `05-state-all.md`, and the branch-key block has no guard.

**The locks can fail.** I ran six mutants in a scratch worktree against both suites. Each one tripped:
- remove the refusal line: 4 failed
- `${PHASE_ID-x}` (lets an unset id through): 3 failed
- `${PHASE_ID:-x}`: 5 failed
- warn without exit: 5 failed
- `exit 0` instead of `exit 1`: 5 failed
- remove the `printf 'PHASE_ID=%s\n'` in `00-scope.md`: 4 failed

Unmutated: 86 passed, 191 subtests passed. The test harness env is built from scratch (`PATH`, `VC_ROOT`, `TMPDIR` and the git config only), so a `PHASE_ID` exported in the runner's shell cannot hide the unset case. None of these locks is decorative.

**README claims checked against code.**
- `carry_state.py` and `score.py` are unchanged since `v2.14.1` (empty `git diff --stat`).
- `GIT_TIMEOUT = 60` is in `finalize_inputs.py`.
- No non-`-I` `python3 -c` remains in `phases/` or `commands/`.
- The `finalize_gate.py failed` message exists at `90-finalize.md:24`.
- 4,126 tests are collected, which matches the claim.
- The "never shipped" claim for the shared-file bug matches 65-REPRO-WR02.md: 2.14.1 failed closed instead.

I did not re-derive the byte and step counts.

The one real problem is that the new prose promises more than the fence enforces (WR-01).

## Warnings

### WR-01: New guarantee "two GSD phases never share one state file" is false for phases with the same folder name

**File:** `plugins/vibe-check/phases/review/05-state.md:16` (also `00-scope.md:127`, which now ties `$PHASE_ID` to the printed `basename` of the resolved folder)

**Issue:** The new sentence says "An empty id stops the review here, so two GSD phases never share one state file." The refusal only rules out the *empty* id. The key is still `basename "$PHASE_DIR"`, and the exact-name branch of the resolution fence (`00-scope.md:85-86`, `find ... -name "<arg>" | head -1`) silently takes the first of several matches. I ran the fence in a fixture holding `.planning/milestones/v1-phases/01-setup` and `.planning/milestones/v2-phases/01-setup`. With arg `01-setup` it printed:
```
PHASE_DIR=.planning/milestones/v2-phases/01-setup
PHASE_ID=01-setup
rc=0
```
No multiple-match error appeared, even though the instructions at `00-scope.md:99` say "Multiple matches → error". Both phases map to `.turingmind/state/format-53/01-setup.json`. That is the same harm WR-02 was opened for: Close out on one phase can approve on the other phase's findings, and a pass on one phase replaces the other's saved progress. The behaviour predates this phase, but the sentence added here states it cannot happen. A maintainer or a later reviewer will rely on that statement.

**Fix:** Make the sentence say only what the line does:
```markdown
An empty id stops the review here, so a missing phase id can never fall back to the shared `.turingmind/state/format-53/.json` key.
```
Whether to also fix the duplicate-name resolution is a scope question (SA-01).

## Info

### IN-01: `TestPhaseIdPrinted` borrows another class's method with a foreign `self`

**File:** `plugins/vibe-check/scripts/test_pasted_name_guard.py:400` (`repo = TestPhaseDirGuard.phase_repo(self, rel)`)

**Issue:** This calls an instance method of `TestPhaseDirGuard` with a `TestPhaseIdPrinted` instance as `self`. It works today only because `phase_repo` uses nothing beyond `self.repo()` from the shared `GuardCase`. If `phase_repo` ever reads a `TestPhaseDirGuard`-only attribute, the failure will appear in an unrelated suite.

**Fix:** Move `phase_repo` up to `GuardCase`, or make it a module-level helper that takes the repo factory.

### IN-02: Empty-id stderr assertion is keyed on a label suffix

**File:** `plugins/vibe-check/scripts/test_pasted_name_guard.py:334-335` (`if label.endswith("-id"):`)

**Issue:** The exact `EMPTY_ID_STOP` stderr check runs only for labels ending in `-id`. A future bad-name case whose label happens to end in `-id` (for example "branch with odd-id") would be held to the empty-id sentence and fail for the wrong reason. Renaming the `GSD_EMPTY` labels would silently drop the exact-message check from this test. `test_without_the_empty_id_refusal_the_shared_file_returns` still pins the message, so this is not a lost lock.

**Fix:** Have the case generator yield the expected stderr (or a flag) as part of each case tuple, instead of inferring it from the label text.

## Set aside (needs ruling)

### SA-01: Phase resolution can map two phases, or a non-phase folder, to one key

**Where:** `plugins/vibe-check/phases/review/00-scope.md:85-91`
**Why excluded:** These lines were not changed in this phase. The behaviour predates 2.15, and under the owner's scope rule (new work only for reproduced gate failures, data loss, silent finding loss, or a broken required workflow) a new fix needs a ruling.
**Effect if left as is:**
1. Two milestone folders that hold a phase with the same name (for example `v1-phases/01-setup` and `v2-phases/01-setup`) resolve silently to one of them. Both share one saved-progress file, so Close out on one can approve on the other's findings.
2. The args `phases`, `milestones` and `v1-phases` pass the `[A-Za-z0-9._-]+` sandbox and resolve to container folders (`PHASE_DIR=.planning/phases`, `PHASE_ID=phases`; confirmed by running the fence). The review then treats the whole folder as one phase.
**Needs:** A ruling: fix now (count exact-name matches the same way as prefix matches and error on more than one, and require at least `-mindepth 1` plus a parent named `phases` or `*-phases`), defer to the backlog, or accept.

### SA-02: GSD path with the new halt has no live check

**Where:** `plugins/vibe-check/phases/review/05-state.md:9`, `README.md` known limitations (2.15.0)
**Why excluded:** This is a test-coverage and release-process matter, not a code defect. The README already discloses that only the default review and Close out were live-checked.
**Effect if left as is:** If a real model runs the GSD key fence without typing in the printed `PHASE_ID=` literal, every GSD review and GSD Close out now stops with "Review halted — the phase id is empty". That is safe, since it fails closed, but it would make GSD mode unusable until noticed. Only fixture runs show what the fence does; none shows what a model actually does on this path.
**Needs:** A ruling: one live GSD-mode smoke before the next release, or accept the risk as disclosed.

---

_Reviewed: 2026-11-16_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
