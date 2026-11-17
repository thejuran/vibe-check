---
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
plan: 06
subsystem: release-gate
tags: [release-gate, live-smoke, finalize, tmux, provenance]
requires:
  - "65-05: 65-RELEASE-RECORD.md with G1-G11 PASS on C = b073e31"
  - "65-LIVE-SMOKE-PROPOSAL.md: Status: APPROVED (owner, 2026-11-16)"
provides:
  - "65-LIVE-SMOKE.md: three live sessions on a sealed snapshot of C, hash-bound evidence, verdict PASS, cache restored"
affects:
  - "65-07 reads the verdict line (PASS) and the carried items K1-K4"
tech-stack:
  added: []
  patterns: ["second planted defect registered with git add -N so the default route sees a new file"]
key-files:
  created:
    - .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-LIVE-SMOKE.md
  modified: []
decisions:
  - "Live smoke of 2.15.0 candidate b073e31: PASS (S2 write-review-md, S3 finalize-card -> record-decisions -> new BLOBFILE -> write-review-md; provenance 0 repo refs)"
  - "Carried, not blocking (D-10): K1 empty fix-loop card after deferring every row makes the model stop; K2 band rise at pass 2; K3 REVIEW.md audit-trail path fixed by the model after archiving; K4 harness write retry"
metrics:
  duration: "~40 min"
  completed: 2026-11-16
  tasks: 2
  files: 1
---

# Phase 65 Plan 06: Live smoke of candidate C Summary

The owner-approved three-session live smoke of 2.15.0 (C = `b073e31`) passed. It ran on a sealed read-only snapshot, with the installed cache at two-direction parity. The rewritten Close out made one helper call and acted on its `next` value in both live Close outs, reused the printed `STATE_FILE=` literal, and wrote REVIEW.md with `**State format:** 53` (`review-closed` exit 0). S3 went through the finalize card branch end to end. The 2.14.1 cache is restored with an empty diff, and the snapshot worktree has been removed.

## What ran

| Session | Command | Outcome |
|---|---|---|
| S1 (`s65-1`, d5db779a) | `/vibe-check:review` | Planted SQL defect flagged (`app/store.py:38`), plus a dead-code warning. Both deferred by a typed answer. The Rerun ran (999.32 not reproduced), and pass 2 kept both deferrals. The model then stopped at an empty fix-loop card (K1). |
| S2 (`s65-2`, acdd5b0d) | `/vibe-check:review --finalize` | One `finalize_inputs.py` call, one BLOBFILE, `next=write-review-md`. REVIEW.md written (State format 53, both deferrals listed). State archived. `review-closed` exit 0. The stop sentence appeared only in the Read of 90-finalize.md. |
| S3 (`s65-3`, 85d23574) | review, then `--finalize` | New path-traversal finding plus the SQL finding were left undecided (Stop here, then Abandon). Finalize ran `finalize-card` → card → `record-decisions` → re-run with a NEW BLOBFILE → `write-review-md`. REVIEW.md lists both deferred findings. S2's report was moved aside unchanged. `review-closed` exit 0. |

Provenance: S1 had 112 plugin-path references, S2 33 and S3 131, all under the snapshot. There were 0 under the repo `plugins/` and 0 under the cache. Containment was clean after every session.

## Verification (observed)

- Task 1 verify: `SETUP-OK`. Setup commit `b804e13`.
- Task 2 verify: `DONE-OK`. Result commit `e2c1a5c`.
- Cache restore: `diff -rq -x .in_use CACHE_BAK CACHE` was empty, and cache plugin.json reads 2.14.1. `git worktree list | grep -c rel65-` = 0.
- No `.jsonl` added to the repo. Raw pane captures and the extraction script are in the executor scratchpad only.

## Deviations from Plan

**1. [Rule 3 - Blocking] Second defect registered with `git add -N`.**
- **Found during:** Task 2 (S3)
- **Issue:** the plan called for a second file, but nothing in the default route's scope prose clearly says it includes untracked files, so a plain new file might not reach the reviewers.
- **Fix:** copied `app/export.py` in and ran `git add -N` (intent-to-add) so it appears in `git diff`. The file content matched the prepared sha256.
- **Cost if wrong:** none for the verdict. S3 flagged the new file's defect, which shows it was in scope.
- **Commit:** e2c1a5c (recorded under S3)

**2. [Plan detail] S1 deferred both rows, not just the planted one.**
- **Found during:** Task 2 (S1)
- **Issue:** pass 1 raised a second warning (dead re-truncation, `app/store.py:43`). Leaving it undecided would have sent S2 to the card branch instead of `write-review-md`.
- **Fix:** typed `defer 1,2 -- tracked for a follow-up change`.
- **Cost if wrong:** none. S3 covers the card branch.

## Assumption Drift (advisory)

- **Found during:** S1. **Planned:** a typed defer might trigger the 999.32 stop instead of the Rerun. **Actual:** the Rerun ran. The model stopped one step later, at the empty pass-2 card (K1). **Why:** the prose covers the Rerun but not a card with 0 open rows. **Cost if wrong:** low. The item is carried as K1 for 65-07 and the backlog.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: 65-LIVE-SMOKE.md (Status: DONE, `## Verdict` first body line `PASS`, `## Cache restored`)
- FOUND: commits b804e13, e2c1a5c
- Snapshot worktree absent; cache at 2.14.1 with an empty diff against the backup
