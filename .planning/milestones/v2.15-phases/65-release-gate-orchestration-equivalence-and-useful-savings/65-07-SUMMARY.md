---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
plan: 07
subsystem: release
tags: [release-gate, sign-off, release-notes, close-runbook, v2.15]
requires:
  - phase: 65-05
    provides: G1–G11 PASS on C b073e31, G6 recount, D-09 reconciliation
  - phase: 65-06
    provides: live smoke verdict PASS on C, carried K1–K4
provides:
  - 65-RELEASE-RECORD.md completed (live smoke, stated limits, waivers granted, publish status)
  - 65-RELEASE-NOTES.md (gh release --notes-file body)
  - 65-CLOSE-RUNBOOK.md (10-step publish procedure from the main session)
  - 65-SIGNOFF.md with Status SIGNED OFF (owner, 2026-11-16)
affects: [verify-work 65, audit-milestone v2.15, complete-milestone v2.15, publish]
tech-stack:
  added: []
  patterns: [effective-smoke-outcome derivation from the last run section, tree-identity assert before tagging origin/main]
key-files:
  created:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-RELEASE-NOTES.md
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CLOSE-RUNBOOK.md
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-SIGNOFF.md
  modified:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-RELEASE-RECORD.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
decisions:
  - "Owner signed off 2.15.0 on b073e31 (Go (Recommended), 2026-11-16): four waivers granted, named review-path growth signed, tag v2.15 / title v2.15 — Lean orchestration"
  - "Live-smoke K1 (fix loop may stop on an empty card after deferring everything) is a Known limit in the release notes only; adding it to the README would mean a new candidate"
  - "ROADMAP 999.38 corrected: WR-02 was a regression introduced during v2.15, fixed before release by b281042, never shipped"
metrics:
  duration: "about 25 min of executor time across two sessions, plus the owner checkpoint"
  completed: 2026-11-16
---

# Phase 65 Plan 07: Release record, notes, runbook and owner sign-off Summary

The owner signed off vibe-check 2.15.0 on candidate b073e31 on one plain-terms page. The release record is complete, the `gh release` notes are written (size block in bytes and steps, six Known limits, no cost claims), and a 10-step close runbook is ready to publish from the main session. Nothing has been pushed, tagged or released.

## Tasks

| Task | Name | Commit | Verify |
|---|---|---|---|
| 1 | Release record, notes, close runbook | ac0d8c5 | Plan verify printed `OK` (Known limits = 6); all 15 runbook fences passed `bash -n` |
| 2 | Freshness, sign-off page, STATE/ROADMAP | dbbd6a3 | `git diff --quiet C HEAD -- . ':(exclude).planning'` exit 0; plan verify printed `OK`; sign-off 79 lines |
| 3 | Owner go/no-go (checkpoint) | 93313b8 (ruling recorded by the main session) + this plan's close commit | Plan verify printed `VERIFY-OK`: `Status: SIGNED OFF (owner, 2026-11-16)`, no `waiver: pending` left, `waiver: granted (owner, ` present |

The effective live-smoke outcome was derived as the plan specifies. 65-LIVE-SMOKE.md has no `## Run N` sections, its Verdict is `PASS`, and its `C:` equals `candidate:`, so EFFECTIVE = `PASS`. No live-smoke waiver line was needed.

## Owner ruling

Asked in the main session with AskUserQuestion. Selection, verbatim: "Go (Recommended)". The ruling was recorded in 65-SIGNOFF.md by the main session in 93313b8: tag `v2.15`, title `v2.15 — Lean orchestration`, message `vibe-check 2.15.0 — lean orchestration`, unchanged. Four waivers were granted: the routes not run live, the fix loop's fix-and-verify path, pause/resume, and no B3/holdout measurement. The runbook needed no tag/title change.

## Deviations from Plan

**1. [Rule 1 - Accuracy] Catch-guardrail wording made consistent in the record**
- **Found during:** close-out (coordinator note)
- **Issue:** The record's G4b row says `kept 25 / protected 26`, `REGRESSED 0`, `AMENDED 1`. Its Fingerprints paragraph said only "the protected catches still hold", which can read as 26 of 26. The tool output and 65-05-SUMMARY (`kept 25/26, REGRESSED 0, AMENDED 1`) agree with the sign-off's "25 of 26 kept, 1 under a standing amendment".
- **Fix:** The record's line 101 now states 25 of 26 kept, the 26th counted under standing amendment 008, `REGRESSED 0`, `UNEVALUABLE 0`. The sign-off was already correct.
- **Cost if wrong:** low; planning text only, the gate verdict is unchanged.

**2. [Rule 1 - Accuracy] Sign-off Dependabot wording corrected**
- **Found during:** close-out (coordinator note)
- **Issue:** The sign-off said the CLI "cannot list Dependabot PRs". 65-CANDIDATE.md shows `gh pr list --author app/dependabot --state open` ran (exit 0) and found none. Only the alerts call failed (HTTP 403, alerts disabled).
- **Fix:** The sign-off now says the alerts list could not be read and the PR listing ran and found no open Dependabot PRs. The record's Dependabot section was already correct.
- **Cost if wrong:** low; planning text only, made after the owner's go and not touching the ruling, the waiver lines or anything shipped.

**3. [Rule 2 - Completeness] Extra waiver and limit lines beyond the plan's minimum list**
- The record and sign-off waive the fix loop's fix-and-verify path separately, because the live run reached the fix-loop card and Rerun but not a fix. Pause/resume is also waived, as in Phase 61. The notes carry live-smoke K1 as a sixth Known limit, marked "listed only in these notes". The owner saw all three on the sign-off page before the go.
- **Cost if wrong:** one extra notes bullet; it can be removed without a new candidate.

**4. [Rule 3 - Blocking] STATE.md frontmatter quoting**
- The first `last_activity` value had unescaped inner double quotes. It was rewritten without them and the frontmatter quote balance was checked.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: 65-RELEASE-NOTES.md, 65-CLOSE-RUNBOOK.md, 65-SIGNOFF.md, 65-RELEASE-RECORD.md
- FOUND commits: ac0d8c5, dbbd6a3, 93313b8
- Shipped tree unchanged since C (`git diff --quiet b073e31 HEAD -- . ':(exclude).planning'` exit 0 at Task 2)
