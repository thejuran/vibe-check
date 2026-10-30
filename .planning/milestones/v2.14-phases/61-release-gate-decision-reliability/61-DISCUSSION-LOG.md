# Phase 61: Release gate — decision reliability - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-30
**Phase:** 61-release-gate-decision-reliability
**Areas discussed:** Live check vs waiver, If the gate fails, Release record + sign-off, Which modes count

---

## Live check vs waiver

| Option | Description | Selected |
|--------|-------------|----------|
| Small live smoke | ~3 sessions, est. $20–30, default review → decide → edit → reopen → --finalize | ✓ |
| No live run, waiver | Offline proof only, as 2.13 | |
| Broader live pass | Several routes + Finalize recovery, ~6–8 sessions, est. $45–70 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, free scripted PR-fetch check | Live `gh pr diff` of PR #6 through the real range builder | ✓ |
| No, keep as known limit | R6 stays "not exercised" | |

| Option | Description | Selected |
|--------|-------------|----------|
| Assistant via tmux | Assistant drives, auto-memory parked | ✓ |
| Owner runs it | Short script for the owner | |

---

## If the gate fails

| Option | Description | Selected |
|--------|-------------|----------|
| One fix round, then stop | Fix with before/after + mutant, re-run gate once; still failing → don't ship, re-scope | ✓ |
| Stop immediately, re-scope | Phase 61 fixes nothing; failure → 61.1 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Hard stop, ask me | Second round only with explicit owner go-ahead | ✓ |
| Your judgment | Assistant may open another round, report after | |

| Option | Description | Selected |
|--------|-------------|----------|
| Carry it, still ship | Non-qualifying finds become named known limits | ✓ |
| Bring each one to me | Pause per finding | |

---

## Release record + sign-off

| Option | Description | Selected |
|--------|-------------|----------|
| Short "Known limits" in release notes | 3–6 plain bullets; full ledger in .planning | ✓ |
| Internal record only | Limits only in .planning | |

| Option | Description | Selected |
|--------|-------------|----------|
| One plain-terms page | Gate results, smoke outcome, replay diffs, limits, Dependabot note, waiver text | ✓ |
| Full ledger walk-through | Every 59/60 residual reviewed | |

| Option | Description | Selected |
|--------|-------------|----------|
| Note it, no action | Record Dependabot disabled + stdlib-only runtime | ✓ |
| Enable it first | Turn on alerts, triage before release | |

---

## Which modes count

| Option | Description | Selected |
|--------|-------------|----------|
| All routes + recovery | Every route, --finalize rebuild/stop, pause/resume, fix loop | ✓ |
| Only what v2.14 touched | Range routes + Finalize | |

| Option | Description | Selected |
|--------|-------------|----------|
| Default + Finalize only (live) | Other routes on offline proof | ✓ |
| Add pass-2 incremental | One more session | |

| Option | Description | Selected |
|--------|-------------|----------|
| Final release commit | Version bumped, exact tagged commit | ✓ |
| Current main, bump after | Faster; tagged commit untested | |

---

## Claude's Discretion

- Throwaway-repo design for the smoke; selection of targeted regression tests; release record layout and wording; how the version bump and release PR ride with the close workflow (within D-12).

## Deferred Ideas

- Live runs of other routes; enabling Dependabot; all non-qualifying 59/60 residuals stay carried.
