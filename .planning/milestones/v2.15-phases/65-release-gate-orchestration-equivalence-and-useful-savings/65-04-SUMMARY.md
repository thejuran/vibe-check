---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
plan: 04
subsystem: release-gate
tags: [release-candidate, version-bump, readme, dependabot, recount]
requires:
  - "65-03: WR-02 fix at b281042 (named growth +495 bytes per path, 0 steps)"
  - "65-02: live smoke proposal APPROVED (owner, 2026-11-16)"
provides:
  - "Release candidate C = b073e31fb77f3f5ca32747f8c549ec552687b1be (plugin.json 2.15.0 + README)"
  - "65-CANDIDATE.md: candidate/parent/version/suite lines, Dependabot note, recount, README fact-check"
affects:
  - "65-05..65-07 and the close runbook read C from 65-CANDIDATE.md"
  - "65-05 G6 recount should reproduce the 65-CANDIDATE.md table on C"
tech-stack:
  added: []
  patterns: ["README N_PASSING placeholder filled from the suite run on the edited tree"]
key-files:
  created:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md
  modified:
    - plugins/vibe-check/.claude-plugin/plugin.json
    - README.md
decisions:
  - "Release candidate C is b073e31 (plugin 2.15.0); README count 4,126 from pytest in plugins/vibe-check/scripts"
  - "README size line uses the recount (+0.54% to +0.89% bytes, +2 steps per review path), not the pre-fix +0.4-0.6% range"
  - "WR-02 appears in the README only as a pre-release fix that never shipped, not as a known limit"
metrics:
  duration: "~25 min"
  completed: 2026-11-16
  tasks: 2
  files: 3
---

# Phase 65 Plan 04: Release candidate C Summary

Candidate C is `b073e31fb77f3f5ca32747f8c549ec552687b1be`. It changes exactly two files: plugin.json now reads `2.15.0`, and the README has a fact-checked v2.15.0 block, a size line in bytes and steps, and a "Known limitations (2.15.0)" group. The suite passed on the tree that became C: 4,126 passed, 0 failed, 0 errors, 0 skipped.

## Task 1: Dependabot, recount, bump, README

**Dependabot (before the bump).**
- Open alerts call: exit 1, `Dependabot alerts are disabled for this repository. (HTTP 403)`, plus a hint that the call needs the `admin:repo_hook` scope.
- `gh pr list --author app/dependabot --state open`: exit 0, with no output (no open Dependabot pull requests).
- `stdlib_only.py`: `34 shipped .py files; third-party imports: none`.
- No setting was changed.

**Recount** at `d31787d` against 2.14.1 `dd8e4ab`:

| Path | Bytes | Steps |
|---|---|---|
| Finalize | 136,114 → 131,381 (−3.48%) | 92 → 85 |
| Plain review | +1,705 (+0.89%) | +2 |
| Deep review | +1,717 (+0.64%) | +2 |
| Plain review `--all` | +1,954 (+0.69%) | +2 |
| Deep review `--all` | +1,966 (+0.54%) | +2 |
| Fix loop | +1,869 (+0.73%) | +2 |

These equal the Phase 63 end figures plus the 65-03 named growth (+495 bytes, 0 steps) on every path.

**README.**
- New block `v2.15.0 (this release)`. It is followed by "Same behaviour as 2.14.1 except:" with 7 bullets: Permission denied, unsafe-name stop, empty phase id, C-locale UTF-8 refusal, 60-second git limit, subfolder fingerprint (D-19) and isolated inline Python (D-22).
- Then the "What changed in size" line.
- v2.14.1 is now labelled `(previous release)`, and the old label was removed from v2.13.
- "Known limitations (2.15.0)" has 5 bullets: live-check scope (APPROVED wording), the 60-second git limit, the helper-failure message with no detail recorded (WR-04), the unsafe-name stop's character coverage (WR-03), and an untested downgrade to 2.14.1.

## Task 2: Fact-check, tests, commit

- The fact-check table in 65-CANDIDATE.md has 23 rows. Each row has an evidence pointer.
- 6 claims were reworded against their evidence:
  - The header no longer claims "one checked step".
  - The locale condition was added to the UTF-8 bullet.
  - The size range changed from the planned +0.4–0.6% to the recounted +0.54–0.89%.
  - "Run again once git responds" became the evidenced rebuild fact.
  - The WR-03 wording now follows the record's "safe only while".
  - The downgrade claim is limited to "no field added".
- The README-coupled tests (`test_recovery_pairs.py`, `test_gitguard.py`) gave 185 passed. That was before the count was filled in, and again after.
- The full suite, `pytest -q -p no:cacheprovider -rs` in `plugins/vibe-check/scripts`, gave `4126 passed, 2 warnings, 6207 subtests passed in 260.19s`. After that run, the only change was replacing the `N_PASSING` token with `4,126`.
- C was committed with explicit paths. `.planning/HANDOFF.json` was not staged.

| Task | Commit | Files |
|---|---|---|
| 1+2 (C) | `b073e31` | README.md, plugins/vibe-check/.claude-plugin/plugin.json |
| 2 (record) | `3632632` | 65-CANDIDATE.md |

## Deviations from Plan

**1. [Rule 1 - Accuracy] The size range was recounted rather than taken from the planned literal.**
- **Found during:** Task 1.
- **Issue:** the plan's "+0.4% to +0.6%" predates the WR-02 fix. The fix added +495 bytes to every path.
- **Fix:** the README gives the recounted +0.5% to +0.9%, with figures for each path.
- **Cost if wrong:** 65-05 G6 recounts on C, so a mismatch would fail that gate and force a new candidate.

**2. [Rule 2 - Correctness] Added a seventh "except" bullet for D-22 (isolated inline Python).**
- **Found during:** Task 1.
- **Issue:** a user-visible security difference from 2.14.1 was missing from the planned list. The evidence is 63-RESULT L206 and `test_inline_python_isolated.py`.
- **Cost if wrong:** one extra README bullet. Changing it now needs a new candidate.

**3. [Verify quirk] The Task 2 automated check's `sort` follows the machine locale.**
- **Issue:** under the default macOS locale, `plugins/…` sorts before `README.md`, so the literal string comparison fails even though the file set is correct.
- **Result:** under `LC_ALL=C` the check prints OK.
- **Cost if wrong:** none. The file set was confirmed directly: exactly the two files.

## Assumption Drift (advisory)

**Dependabot PR listing.**
- **Found during:** Task 1.
- **Planned:** `gh pr list --author app/dependabot` fails with a scope error.
- **Actual:** it ran and returned no open PRs. The scope hint (`admin:repo_hook`) came from the alerts call instead.
- **Why:** the gh token can list PRs.
- **Recording:** 65-CANDIDATE.md records what actually happened, not the planned sentence.
- **Cost if wrong:** low. Release-day notes should quote this result.

**README count form.**
- **Planned:** none recorded; the orchestrator note cites 65-03's 4,599.
- **Actual:** the README uses 4,126, the count from the scripts-folder form, which is what the plan and every earlier README count use.
- **Recording:** 65-CANDIDATE.md explains the gap. 4,599 is the repo-root G1b form, which also collects `.github/scripts` and the lean-v2.15 tools.
- **Cost if wrong:** a reader comparing the two figures could think tests went missing.

## Known Stubs

None.

## Self-Check: PASSED

- 65-CANDIDATE.md and 65-04-SUMMARY.md exist.
- Commits `b073e31` and `3632632` are in `git log`.
- The `candidate:` line resolves with `git cat-file -e`.
- `git diff --quiet C HEAD -- . ':(exclude).planning'` exits 0.
