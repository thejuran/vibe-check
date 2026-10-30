---
phase: 61-release-gate-decision-reliability
plan: 01
subsystem: release
tags: [release, readme, version-bump, candidate]
requires: []
provides:
  - "candidate C = 0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d (plugin 2.14.0 + fact-checked README)"
  - "61-CANDIDATE.md with candidate:/parent:/version:/suite_on_edited_tree: lines and the README fact-check table"
affects: [61-03, 61-04, 61-05]
tech-stack:
  added: []
  patterns: ["release surface frozen in one candidate commit before any gate runs (D-12)"]
key-files:
  created:
    - .planning/phases/61-release-gate-decision-reliability/61-CANDIDATE.md
  modified:
    - README.md
    - plugins/vibe-check/.claude-plugin/plugin.json
decisions:
  - "README live-check bullet states scope only (default review + Close out in scope; others tests-only; PR fetch tested on a saved real PR diff) and defers the outcome to the release notes, because the live smoke (61-04) and D-03 PR fetch (61-03) run after C and the smoke may be declined"
  - "v2.12 relabelled '(earlier release)', mirroring the existing v2.10 label"
metrics:
  duration: "~6 min (excluding pre-read)"
  completed: 2026-10-30
  tasks: 2
  files: 3
requirements: [GATE-01, GATE-03]
---

# Phase 61 Plan 01: Release candidate C (2.14.0 bump + fact-checked README) Summary

Candidate commit C `0d2be77` bumps vibe-check to 2.14.0 and adds the v2.14 release paragraph (four fixes, 3,821 tests passing) and a `Known limitations (2.14)` list tied to the 59/60 residual ledgers. Each new claim was fact-checked against code, tests or phase records before the commit.

## Tasks

| Task | Name | Commit | Files |
|---|---|---|---|
| 1 | Bump plugin.json, rewrite README release section | 0d2be77 (committed with Task 2 as C, per plan) | README.md, plugin.json |
| 2 | Fact-check, suite on edited tree, commit C, record SHA | 0d2be77 (C), 2a337d3 (61-CANDIDATE.md) | README.md, 61-CANDIDATE.md |

## Verification (observed)

- Task 1 verify fence: `OK`. `grep -c "this release)"` = 1; `N_PASSING` count was 1 before the fill and is 0 after; `gets **one** automatic` count = 0.
- README-coupled tests on the edited tree: `185 passed, 708 subtests passed in 4.93s`.
- Full suite on the edited tree: `3821 passed, 5039 subtests passed in 173.89s` (0 failed). README reads `(3,821 passing at release)`.
- `git diff --name-only C^ C` = README.md and plugin.json only. Commit C ends with the attribution trailer.
- Task 2 verify fence: it failed under the default macOS locale because `sort` put `plugins/...` before `README.md`, so the string compare did not match. Re-run with `LC_ALL=C`, it printed `OK`. Every component check also passed when run on its own (cat-file 0, version count 1, no N_PASSING, `git diff --quiet C HEAD -- . ':(exclude).planning'` exit 0).

## Deviations from Plan

**1. [Rule 1 - Bug] Wording changed by the fact-check to match the evidence**
- **Found during:** Task 2
- **Issue:** Some text the plan dictated said more than the records support. It said "every review route" (`--all` has no window, 60 R10). It said "a later retry completes" (the record says "may complete after revalidating freshness"). It said the default route and Close out "were run live" and the PR fetch "was checked once against real PRs", but those checks run in later plans (61-03 and 61-04) and the live smoke may be declined (61-02). It also gave some uncommon-layout examples that were not the reproduced shapes.
- **Fix:** I reworded each one to match its evidence (see the fact-check table in 61-CANDIDATE.md). The live-check bullet now gives only the scope and leaves the outcome to the release notes. I also removed a `git add` workaround from my own draft because nothing verifies it.
- **Cost if wrong:** If 61-05 wants the README to say the live smoke passed, the README must change after C, and under D-12 every gate re-runs.
- **Files modified:** README.md
- **Commit:** 0d2be77

**2. [Rule 3 - Blocking] Task 2 verify fence depends on the locale**
- **Found during:** Task 2 verify
- **Issue:** The fence uses `sort` with the default macOS locale, which ignores case, so `plugins/...` sorts before `README.md` and the exact-string compare fails.
- **Fix:** I ran the fence with `LC_ALL=C` and it passed. The fence itself is unchanged. Plans 61-03 to 61-05 should use `LC_ALL=C sort` wherever they reuse this check.
- **Cost if wrong:** Low. A later plan that copies the fence without `LC_ALL=C` would report a false failure.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** the README says only the default route and Close out "were run live" and the PR fetch "was checked once". **Actual:** neither check has run at C, and the smoke may be declined. **Why:** wave order (61-03 and 61-04 depend on 61-01). **Cost if wrong:** the release notes (61-05) must carry the live-check outcome; the README does not.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: README.md, plugins/vibe-check/.claude-plugin/plugin.json, .planning/phases/61-release-gate-decision-reliability/61-CANDIDATE.md
- FOUND commits: 0d2be77, 2a337d3
