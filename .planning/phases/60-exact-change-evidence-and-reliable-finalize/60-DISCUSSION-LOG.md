# Phase 60: Exact change evidence and reliable Finalize - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 60-CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-10-29
**Phase:** 60-exact-change-evidence-and-reliable-finalize
**Areas discussed:** One-line edge miss, Finalize when it stops, PR route evidence, Review/fix rounds

Claude decided without asking (technical): build ranges from `+`/`-` markers rather than `-U0`, because `gh pr diff` has no context option.

## One-line edge miss (57 IN-04)
| Option | Selected |
|---|---|
| Fix here: a net-deletion replace also covers the line after the hunk | ✓ |
| Carry as a known limit | |

## Finalize when it stops
| Option | Selected |
|---|---|
| Rebuild fingerprints once, then stop with a plain message | ✓ |
| Always stop and tell the owner | |

## PR route evidence
| Option | Selected |
|---|---|
| Saved real PR diff, report says live fetch not exercised | ✓ |
| Saved diff + one live check | |

## Review/fix rounds
| Option | Selected |
|---|---|
| Same as Phase 59 (one review, one fix pass, carry the rest) | ✓ |
| Allow a second round | |

## Claude's Discretion
- Location and shape of the range builder; the fresh-shell walk test structure; stop-message wording; repro ledger location.
- Interpretation: an owner-refused step is not auto-retried (D-08).

## Deferred Ideas
- 999.23 residuals WR-01/WR-02; 57 IN-01/02/03/05; Finalize extraction (Lean orchestration).
