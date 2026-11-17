# Phase 66: Close out freshness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-16
**Phase:** 66-close-out-freshness
**Areas discussed:** Refusal message, What counts as changed, Legacy shapes policy

---

## Refusal message

| Question | Options | Selected |
|----------|---------|----------|
| Detail level | List each one (file:line, title, kind, cause; cap ~10) / Short summary | List each one |
| Next step | Name the exact command (mirrors route, notes paid reviewers) / Generic instruction | Name the exact command |
| Partial staleness | Refuse it all / Write report, flag stale | Refuse it all |

**User's choice:** all recommended options.

---

## What counts as changed

| Question | Options | Selected |
|----------|---------|----------|
| Which edits count | Anything on disk (committed, staged, unsaved) / Committed only | Anything on disk |
| Deleted or renamed decided file | Treat as stale / Treat as resolved | Treat as stale |
| Whitespace/comment-only edits | Still stale / Ignore trivial edits | Still stale |

**User's choice:** all recommended options.

---

## Legacy shapes policy (999.44)

| Question | Options | Selected |
|----------|---------|----------|
| Outcome when a shape reproduces | Refuse by default / Repair by default | Refuse by default |
| Untracked files | Compare saved content / Always refuse | Compare saved content |
| Non-reproducing shape | Recorded proof / Guard it anyway | Recorded proof |

**User's choice:** all recommended options.

---

## Claude's Discretion

- Location of the freshness check in the helper chain and how current content is compared.
- Exact refusal wording/exit code within existing Finalize refusal conventions.
- Fixture design for the three 999.44 shapes and the exact-line / nearby / unchanged controls.

## Deferred Ideas

None.
