# Phase 59: Stale decisions and lost deferrals - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-28
**Phase:** 59-stale-decisions-and-lost-deferrals
**Areas discussed:** D-21 over-asks, Copy/member reopen wording, Min-confidence deferrals, What "one cycle" means

---

## D-21 over-asks

| Option | Description | Selected |
|--------|-------------|----------|
| Fix #1 only, as part of pooling | Pooling counts only copies that existed at decision time; #2 stays carried | ✓ |
| Fix neither | Keep today's behaviour (new copies count) | |
| Fix both | Separate work for #2; doesn't qualify under the four classes | |

| Option | Description | Selected |
|--------|-------------|----------|
| Drop it and carry it (if #1 needs its own task) | Keep the cycle bounded | ✓ |
| Do it anyway | Accept the extra task | |

## Copy/member reopen wording

| Option | Description | Selected |
|--------|-------------|----------|
| Name the line | "code next to line 30 (another copy of this line) changed…" | ✓ |
| Generic reason | Existing "code next to it changed" | |

| Option | Description | Selected |
|--------|-------------|----------|
| First spot + count | "line 30 and 2 other spots" | ✓ |
| List every line | Complete but long | |

## Min-confidence deferrals

| Option | Description | Selected |
|--------|-------------|----------|
| Same as below-threshold deferrals | Open deferred item + note "below your min_confidence (45); still deferred" | ✓ |
| Quieter: count line only | No own card | |

| Option | Description | Selected |
|--------|-------------|----------|
| SA-02: same rule | Stays open with out-of-scope note (if it reproduces) | ✓ |
| Scope wins | Out-of-scope deferrals return on a covering review | |

## What "one cycle" means

| Option | Description | Selected |
|--------|-------------|----------|
| One fix pass, qualifying only, no re-review | Fixtures + mutants + full suite confirm; rest carried | ✓ |
| Record only, no fixes | Strictest | |
| One fix pass + one confirming review | Effectively a second round | |

| Option | Description | Selected |
|--------|-------------|----------|
| Close with residual recorded; release names it | Ship possible under owner waiver | ✓ |
| Hold Phase 59 for owner call | | |

## Claude's Discretion
- Pooling implementation, decision-time copy tracking, verdict ledger location, fixture layout, exact note phrasing.

## Deferred Ideas
- Over-ask #2 (WR-01) stays in 999.23.

## Side note
- Owner asked what "Default mode, no advisor" meant: workflow plumbing (interactive questions; no USER-PROFILE.md → no research comparison tables). No decision impact.
