---
phase: 61-release-gate-decision-reliability
plan: 05
subsystem: release
tags: [release, sign-off, waiver, release-notes, close-runbook, known-limits]
requires:
  - "61-CANDIDATE.md candidate 0d2be77 (61-01), gates G1-G9 PASS (61-03)"
  - "61-LIVE-SMOKE.md verdict PASS with carried C1-C5 (61-04)"
provides:
  - "61-RELEASE-RECORD.md complete: live smoke, unsupported fixtures, residuals (linked), carried, validation gaps with granted waivers, publish status pending close"
  - "61-RELEASE-NOTES.md: gh release --notes-file body for v2.14 with a Known limits list"
  - "61-CLOSE-RUNBOOK.md: close steps incl. skip in-branch tag, D-12 freshness, PR + squash, tree-identity assert vs C, tag origin/main, gh release create, installed-cache update"
  - "61-SIGNOFF.md: one-page sign-off, Status SIGNED OFF (owner, 2026-10-30), Decision 1 = A"
  - "ROADMAP backlog 999.28 for C1 (C4 folded in)"
affects: [milestone-close-v2.14]
tech-stack:
  added: []
  patterns: ["one-page plain-terms sign-off with a costed A/B/C decision table; per-item dated waiver lines"]
key-files:
  created:
    - .planning/phases/61-release-gate-decision-reliability/61-RELEASE-NOTES.md
    - .planning/phases/61-release-gate-decision-reliability/61-CLOSE-RUNBOOK.md
    - .planning/phases/61-release-gate-decision-reliability/61-SIGNOFF.md
  modified:
    - .planning/phases/61-release-gate-decision-reliability/61-RELEASE-RECORD.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "Owner signed off 2026-10-30 (own AskUserQuestion selection in the main session, verbatim 'A: Ship, known limit (Recommended)', no conditions): ship 2.14.0 with C1 as the first Known limit in the release notes, README unchanged, no fix round"
  - "All six validation-gap waivers granted (owner, 2026-10-30): non-default routes offline only; live PR fetch on 2 PRs only; nearby-edit trigger proven by tests only; live plain-English answer reading; no catch/false-alarm measurement; no pause/resume walk"
  - "C1 (uncommitted-code decisions re-asked every pass with a false 'code next to it changed' reason) recorded as backlog 999.28, with C4 (model stopped instead of Rerun) folded in"
metrics:
  duration: "~35 min across two sessions (Tasks 1-2, then sign-off continuation)"
  completed: 2026-10-30
  tasks: 3
  files: 6
requirements: [GATE-01, GATE-02, GATE-03]
---

# Phase 61 Plan 05: Release record, notes, runbook and owner sign-off Summary

The 2.14.0 candidate `0d2be77` is release-ready and signed off by the owner. Nothing has been published. Publishing happens at milestone close, following 61-CLOSE-RUNBOOK.md.

- **Record:** 61-RELEASE-RECORD.md covers the live smoke (PASS), the unsupported fixtures and stated limits, links to the residual ledgers (34 items, not restated), the carried items C1-C5, six validation gaps with waivers, and the publish status. GATE-03's "ships" clause stays pending until close.
- **Release notes:** 61-RELEASE-NOTES.md follows the v2.13 format. It includes a Known limits list (C1 first), the routes that ran live and those that rest on tests, and the test count (3,821).
- **Runbook:** 61-CLOSE-RUNBOOK.md lists the close steps in order:
  1. Run verify-work, audit and complete-milestone, skipping complete-milestone's in-branch tag.
  2. D-12 freshness assert.
  3. Dependabot note.
  4. PR and squash merge.
  5. Tree-identity assert, comparing `origin/main` with C for `plugins/vibe-check` and `README.md`.
  6. Tag `origin/main` and push the tag.
  7. `gh release create v2.14 --verify-tag --latest`.
  8. Verify the remote.
  9. Update the installed cache and verify it.
  10. Delete the branch.
- **Sign-off:** on 2026-10-30 the owner chose "A: Ship, known limit (Recommended)" in the main session, with no conditions. 61-SIGNOFF.md shows `Status: SIGNED OFF (owner, 2026-10-30)` and records Decision 1 = A. All six `waiver: pending owner sign-off` lines are now `waiver: granted (owner, 2026-10-30)`. Backlog item 999.28 was added to ROADMAP.md for C1.

## Tasks

| Task | Name | Commit | Files |
|---|---|---|---|
| 1 | Release record, release notes, close runbook | f29e9e7 | 61-RELEASE-RECORD.md, 61-RELEASE-NOTES.md, 61-CLOSE-RUNBOOK.md |
| 2 | D-12 freshness check and plain-terms sign-off page | 06f6cd8 | 61-SIGNOFF.md, STATE.md |
| 3 | Owner sign-off (checkpoint) recorded | 4ab5d2d | 61-SIGNOFF.md, 61-RELEASE-RECORD.md, ROADMAP.md, STATE.md |

## Verification (observed)

- Task 3 verify: `Status: SIGNED OFF (owner, 2026-10-30)` is present, and no `waiver: pending owner sign-off` remains. The check printed OK.
- 61-SIGNOFF.md is 66 lines, within the limit of 80.
- Task 1 check re-run: printed OK. There are 6 Known-limits bullets (allowed range 3-6), no D-/R- tokens in the notes, and the runbook has the tree-identity and `gh release create v2.14 --verify-tag --latest` lines.
- Task 2 check re-run: printed OK. The D-12 freshness check `git diff --quiet 0d2be77 HEAD -- . ':(exclude).planning'` exited 0, so nothing outside `.planning` has changed since the candidate. All six sign-off sections are present.
- The ROADMAP has exactly one `### 999.28` heading.

## Deviations from Plan

**1. [Rule 2 - Bookkeeping] Backlog 999.28 created at sign-off instead of at close**
- **Found during:** Task 3
- **Issue:** the release record said to create 999.28 "at close". However, the owner-approved option A says C1 "goes on the backlog as 999.28".
- **Fix:** added the 999.28 entry under `## Backlog` in ROADMAP.md now, in the existing format, with C4 folded in. Updated the record's C1 line to match.
- **Cost if wrong:** low. It is one planning entry, and the close session should skip creating it a second time.
- **Files modified:** .planning/ROADMAP.md, 61-RELEASE-RECORD.md
- **Commit:** 4ab5d2d

## Known Stubs

None. The close runbook is intentionally pending until close. It is not a stub.

## Next

`/bm:verify-work 61`, then close following 61-CLOSE-RUNBOOK.md. Publishing, tagging, merging and the GitHub release all belong to that step.

## Self-Check: PASSED

- FOUND: 61-SIGNOFF.md, 61-RELEASE-RECORD.md, 61-RELEASE-NOTES.md, 61-CLOSE-RUNBOOK.md, 61-05-SUMMARY.md
- FOUND commits: f29e9e7, 06f6cd8, 4ab5d2d
