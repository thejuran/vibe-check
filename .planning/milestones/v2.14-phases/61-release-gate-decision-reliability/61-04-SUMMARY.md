---
phase: 61-release-gate-decision-reliability
plan: 04
subsystem: release
tags: [release, live-smoke, tmux, finalize, stale-decisions, provenance]
requires:
  - "61-LIVE-SMOKE-PROPOSAL.md Status: APPROVED (owner, 2026-10-30) (61-02)"
  - "61-CANDIDATE.md candidate 0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d (61-01), gates G1-G9 PASS (61-03)"
provides:
  - "61-LIVE-SMOKE.md: live smoke of candidate 0d2be77, verdict PASS, hash-bound evidence, five carried D-07 items (C1 is owner-relevant)"
affects: [61-05]
tech-stack:
  added: []
  patterns: ["sealed read-only worktree snapshot + content-parity cache + per-session provenance grep; cache restored with a verified empty diff"]
key-files:
  created:
    - .planning/phases/61-release-gate-decision-reliability/61-LIVE-SMOKE.md
  modified: []
decisions:
  - "Live smoke verdict PASS: S2 re-asked the deferred finding with 'code next to it changed since your decision on pass 1'; S3 --finalize carried the printed BLOBFILE=/GATEFILE= paths and wrote REVIEW.md without the 'Finalize stopped' sentence; all sessions loaded the snapshot"
  - "C1 carried under D-07, not a fix round: on the default route a decision on uncommitted code is re-asked on every pass even with no change (pass>=2 ranges come from git diff <last-reviewed-sha> = HEAD while uncommitted). It fails toward asking and Close out completes, so no qualifying class applies; flagged for the owner at 61-05 sign-off"
metrics:
  duration: "~22 min"
  completed: 2026-10-30
  tasks: 2
  files: 1
requirements: [GATE-03]
---

# Phase 61 Plan 04: Live smoke of candidate C Summary

The owner-approved live smoke ran three fresh Claude Code sessions in tmux on a sealed snapshot of `0d2be77`, with the installed cache at content parity, and passed.

- **Re-ask:** the deferred SQL-injection finding was re-asked after a nearby edit, with the reopen reason "code next to it changed since your decision on pass 1".
- **Close out:** `--finalize` carried its printed temp-file paths across steps and wrote `.turingmind/REVIEW.md` (APPROVED, findings listed under deferred). The "Finalize stopped" sentence never appeared.
- **Provenance:** every plugin path in every transcript came from the snapshot.
- **Cleanup:** the installed 2.13.0 cache was restored with an empty diff, and the snapshot worktree was removed.

## Tasks

| Task | Name | Commit | Files |
|---|---|---|---|
| 1 | Approval check; sealed snapshot, cache parity, throwaway repo | 0866858 | 61-LIVE-SMOKE.md |
| 2 | Sessions S1-S3, evidence, classification, cache restore | 5784b37 | 61-LIVE-SMOKE.md |

## Verification (observed)

- Task 1 `<verify>` printed `SETUP-OK`. `git status --porcelain -- plugins` was empty.
- Task 2 `<verify>` exited 1. Its first five greps passed (Status DONE, Verdict, Cache restored, the reopen phrase, `GATEFILE=`). Its last check, `! git ls-files -- "*.jsonl" | grep -q .`, fails because the repo already tracked 15 `.jsonl` files from Phase 49/52 (`docs/design/fix-harness/runs/phase52/...`, `docs/design/b3-ground-truth/runs-v2.11-phase49/...`), last touched in c85e3b8. This plan added no `.jsonl`: `git diff --name-only 6495dbf HEAD` lists only 61-LIVE-SMOKE.md, and no smoke session id (5caa5cec / 15a3be6d / b1bb3036) or `smoke61` path is tracked.
- Cache restore: `diff -rq -x .in_use CACHE_BAK CACHE` was empty, and the cache plugin.json reads 2.13.0. `git worktree list` no longer shows `rel61-0d2be77`.

## Deviations from Plan

**1. [Rule 3 - Blocking] The Task 2 verify's `.jsonl` check could not pass on this repo**
- **Found during:** Task 2 verify.
- **Issue:** the check asserts that no `.jsonl` is tracked anywhere, but 15 pre-existing harness transcripts from Phases 49 and 52 are tracked.
- **Fix:** none to the repo (out of scope). I checked the intent directly instead: no transcript from this smoke is tracked, and this plan's commits add no `.jsonl`.
- **Cost if wrong:** low. If a stricter "no jsonl at all" policy was intended, that is a separate cleanup of Phase 49/52 artifacts.
- **Commit:** 5784b37.

**2. [Rule 3 - Blocking] S1 ran two passes and ended with Abandon**
- **Found during:** Task 2, S1.
- **Issue:** per `50-fix-loop.md`, a typed defer automatically reruns, so S1 produced pass 2 in the same session. I ended S1 with Stop here… → Abandon so that state was kept and no extra rerun was paid for.
- **Cost if wrong:** low. The decision was recorded at pass 1 as planned.

## Assumption Drift (advisory)

- **REVIEW.md location.**
  - Found during: S3.
  - Planned: `shasum "$SMOKE/REVIEW.md"`.
  - Actual: the product writes `$SMOKE/.turingmind/REVIEW.md`; nothing is written at the repo root.
  - Why: that is the product's documented output path.
  - Cost if wrong: none. The hash was taken of the real file.
- **S2 isolates the nearby edit.**
  - Found during: S1 pass 2.
  - Planned: S2's re-ask proves that a nearby edit reopens a decision.
  - Actual: the same reopen fires with no edit at all while the code is uncommitted (C1), so S2 shows that the reopen happens, not that the edit caused it.
  - Why: on the default route, pass ≥ 2 ranges are `git diff HEAD` until a commit.
  - Cost if wrong: the nearby-edit trigger itself is still covered by the offline real-chain tests (59/60). The live run neither adds to nor subtracts from that.

## Carried items (D-07, details in 61-LIVE-SMOKE.md)

- **C1 — owner-relevant:** on the default route, a dismiss or defer of a finding in uncommitted code is re-asked on every pass, and the card claims "code next to it changed" when it did not. Extra questions, never lost findings; Close out still completes.
- **C2:** the band rose from warning to critical between passes with unchanged code.
- **C3:** the lead row was regrouped and retitled between passes; both rows carried the decision context.
- **C4:** in S2 the model stopped instead of taking the protocol's Rerun. It fails toward stopping.
- **C5:** read-before-write retries on fresh temp files. Harmless.

## Known Stubs

None.

## Threat Flags

None. The live sessions ran in manual mode with explicit allowedTools. The cache was backed up and restored with verified diffs, and only hashes and extracted lines were committed.

## Self-Check: PASSED

- FOUND: .planning/phases/61-release-gate-decision-reliability/61-LIVE-SMOKE.md
- FOUND: commit 0866858
- FOUND: commit 5784b37
