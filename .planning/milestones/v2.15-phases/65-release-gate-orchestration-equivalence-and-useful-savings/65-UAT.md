---
status: complete
phase: 65-release-gate-orchestration-equivalence-and-useful-savings
source: [65-01-SUMMARY.md, 65-02-SUMMARY.md, 65-03-SUMMARY.md, 65-04-SUMMARY.md, 65-05-SUMMARY.md, 65-06-SUMMARY.md, 65-07-SUMMARY.md]
started: 2026-11-16T00:00:00Z
updated: 2026-11-17T03:04:41Z
---

## Current Test

[testing complete]

## Tests

### 1. README v2.15.0 release block reads correctly
expected: Top entry "v2.15.0 (this release)", marked not measured, scores unchanged (170-run replay), 7 "Same behaviour as 2.14.1 except:" bullets, size line in bytes and steps only (Close out 136,114 → 131,381 bytes, 92 → 85 steps), no token/dollar/cheaper claim; v2.14.1 labelled "(previous release)".
result: pass

### 2. README Known limitations (2.15.0) are accurate and plain
expected: README has a "Known limitations (2.15.0)" group of 3–6 bullets covering what was not run live, the 60-second git limit, the helper-failure message without detail, the unsafe-name stop's character coverage, and the untested downgrade to 2.14.1 — each understandable without reading code.
result: pass

### 3. Release notes match what you want on the GitHub release page
expected: 65-RELEASE-NOTES.md opens with "Same behaviour as 2.14.1 except:" (7 bullets), has a "What changed in size" block in bytes and steps, says "These are size counts, not usage or price figures.", and lists the Known limits (including the duplicate-folder limit you ruled on after sign-off). Nothing in it claims savings in tokens or money.
result: pass
note: "Owner observed the file opens with a lead \"Lean-orchestration release…\" paragraph, not the exception line. That ordering is what 65-07-PLAN.md Task 1 step 3 specifies (lead paragraph, then \"Same behaviour as 2.14.1 except:\"); the test wording \"opens with\" was wrong, not the deliverable. All other content confirmed."

### 4. Sign-off page matches the release you approved
expected: 65-SIGNOFF.md reads "Status: SIGNED OFF (owner, 2026-11-16)", names tag v2.15 and title "v2.15 — Lean orchestration", shows all gates passing and the live smoke PASS, and carries exactly four "waiver: granted (owner, 2026-11-16)" lines (routes not run live, fix-loop fix-and-verify, pause/resume, no B3/holdout measurement) — matching what you agreed to.
result: pass
note: "Owner observed G12 (GitHub CI) reads PENDING (at close), not PASS. By design: G12 runs on the PR head and is gated before the merge OK in 65-CLOSE-RUNBOOK.md step 4 (VERIFICATION publish_status: pending close). Test wording \"all gates passing\" should have read G1–G11 PASS, G12 pending. All other content confirmed."

### 5. Nothing published yet; close runbook is the next step
expected: No v2.15 tag on GitHub, no v2.15 release page, branch feat/v2.15-phase-65 not yet merged; 65-CLOSE-RUNBOOK.md lays out the publish steps (PR with CI green, your merge OK, tag v2.15 on main, GitHub release, plugin update + relaunch, branch cleanup) for the main session to run at close.
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
