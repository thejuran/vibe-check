# Phase 37: Close - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the discussion.

**Date:** 2026-07-05
**Phase:** 37-close
**Mode:** default (via /julian-orchestrator:milestone)
**Areas discussed:** B3 kit publicity, Release notes touch, Stale worktree leftovers

## Areas & Selections

### B3 kit goes public
- Context presented: first-ever push of `feat/v2.9` (55 local-only commits) publishes
  `docs/design/b3-ground-truth/` — 6 reversed-fix patches + provenance naming
  triggarr/seedsyncarr/roonseek, BUGGY.py, 18 captured run states. All underlying bugs
  already fixed upstream; scrubbing would require history rewrite that destroys the
  pre-registration evidence chain behind the measured numbers.
- Options: Publish as-is (Recommended) / Publish + backlog privacy item / Hold the publish
- **Selected: Publish as-is.** (Owner explicitly passed on the standing privacy backlog item.)

### Release notes touch
- Context presented: v2.8 closed with a bare bump; v2.9 is the first release with measured
  numbers — a 3–6 line README pointer makes the public repo's efficacy claims self-consistent.
- Options: Small README pointer (Recommended) / Bare bump (v2.8 convention)
- **Selected: Small README pointer** — exact fractions, small-N caveat, link to RESULTS-v2.9.md.

### Stale worktree leftovers
- Context presented: ~38 tracked `.planning` files from shipped milestones deleted-but-
  uncommitted in the worktree; zero effect on publish.
- Options: Leave untouched (Recommended) / Commit cleanup pre-merge
- **Selected: Leave untouched.**

## Deferred Ideas
- Future ground-truth kits' privacy location — considered, declined as a backlog item.

## Claude's Discretion (granted)
- README pointer wording/placement; bump-vs-README commit split; tag message style.
