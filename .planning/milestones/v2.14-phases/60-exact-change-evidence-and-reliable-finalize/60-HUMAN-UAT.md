---
status: complete
phase: 60-exact-change-evidence-and-reliable-finalize
source: [60-VERIFICATION.md]
started: 2026-10-30T19:54:10Z
updated: 2026-10-30T20:58:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Write tool accepts the first write to a freshly mktemp'd BLOBFILE/GATEFILE path (R16)
expected: In a live `--finalize` run, the Write to the printed `BLOBFILE=`/`GATEFILE=` path succeeds (as the existing ROWSFILE/SUGGESTFILE/REFSFILE pattern already relies on); if it is refused, every --finalize attempt and its one retry fail at that write step
result: pass
evidence: Live check in Claude Code 2026-10-30. `mktemp` minted a fresh empty file under `$TMPDIR` (/var/folders/.../T/tmp.XXXXXX, the same location as 90-finalize.md's `mktemp "${TMPDIR:-/tmp}/vc.XXXXXX"`); the Write tool's first write to it, with no prior Read, succeeded and `cat` showed the content. Repeated on a scratchpad path with the same result. Run in bypass-permissions mode; a stricter permission mode may prompt for a write outside the project (a prompt, not a refusal).

### 2. Owner ruling: PR route fails closed on very large PRs (R17 — gh pr diff over ~300 files / 20k lines)
expected: Explicit ruling — accepted limit, or fallback needed
result: pass
ruling: Accepted known limit, no fallback. Fails closed and loudly; recorded in 60-REPRO.md R17 and ROADMAP 999.24 carried list; Phase 61 names it in the release record.

### 3. Owner ruling: may a well-formed state-file head_sha narrow the incremental review range? (R25)
expected: Explicit ruling — accept the status quo, or defer scope-binding hardening as a backlog item
result: pass
ruling: Status quo accepted for v2.14; scope-binding hardening deferred as backlog 999.27 (ROADMAP). Recorded in 60-REPRO.md R25.

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
