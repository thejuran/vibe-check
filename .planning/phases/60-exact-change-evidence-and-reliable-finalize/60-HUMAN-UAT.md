---
status: partial
phase: 60-exact-change-evidence-and-reliable-finalize
source: [60-VERIFICATION.md]
started: 2026-10-30T19:54:10Z
updated: 2026-10-30T19:54:10Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Write tool accepts the first write to a freshly mktemp'd BLOBFILE/GATEFILE path (R16)
expected: In a live `--finalize` run, the Write to the printed `BLOBFILE=`/`GATEFILE=` path succeeds (as the existing ROWSFILE/SUGGESTFILE/REFSFILE pattern already relies on); if it is refused, every --finalize attempt and its one retry fail at that write step
result: [pending]

### 2. Owner ruling: PR route fails closed on very large PRs (R17 — gh pr diff over ~300 files / 20k lines)
expected: Explicit ruling — accepted limit, or fallback needed
result: [pending]

### 3. Owner ruling: may a well-formed state-file head_sha narrow the incremental review range? (R25)
expected: Explicit ruling — accept the status quo, or defer scope-binding hardening as a backlog item
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
