# vibe-check 2.14.0 — release sign-off

Candidate: 0d2be77 (version 2.14.0). Nothing outside planning files has changed since the checks ran (re-checked 2026-10-30 just before this page was written). Nothing has been published.

**What ships:** decided findings are asked again when their code changes, including in the uncommon layouts 2.13 missed. Deferred findings no longer vanish under `min_confidence`. The "nearby edit" window is the stated five lines. Close out completes. Reviewers and scoring are unchanged.

## Checks

| Check | What it shows | Result |
|---|---|---|
| All automated tests | 3,821 tests pass on the exact release commit; 0 fail | PASS |
| Decision re-ask regressions | The real-chain cases fixed in this milestone stay fixed (193 pass) | PASS |
| Every review route and recovery path | Default, GSD, range, PR, incremental, `--all`, Close out with its retry and safe stop, pause/resume and the fix loop all pass offline (520 pass) | PASS |
| Past reviews re-scored the same as 2.13 | 170 archived runs, 0 differences; no differences were allowed in advance | PASS |
| No previously caught defect lost | 25 of 26 protected catches kept, 0 regressed, 0 unevaluable; 1 run counted under a standing, documented amendment | PASS |
| Replay tooling untouched and intact | Replay tests pass, the run manifest is intact, and the machinery is unchanged since 2.13 | PASS |
| PR diff fetch from GitHub matches local | Live fetch of PR #6 and PR #4 identical to local history (PR #4 has 133 renames) | PASS |
| Plugin manifest valid | Claude Code accepts the plugin (3 cosmetic warnings: no icon, untracked macOS files) | PASS |
| No third-party code shipped | 32 shipped Python files use only the standard library | PASS |

## Live smoke

PASS. In three real sessions on the release candidate, a deferred finding was asked again after an edit near it, and Close out wrote the final report with both deferred findings listed. **But see Decision 1:** the same finding was also asked again on a pass where nothing had changed. So the live run does not prove the "edit near it" trigger on its own; that rests on the automated tests.

## Decision 1 — the "asked again on every pass" behavior (your call)

**What happens:** when you review code you haven't committed yet (the default review), a finding you defer or dismiss is asked again on the very next pass, even if you changed nothing, and the card says "code next to it changed", which is false. Nothing is lost, and Close out still completes with your decisions. It is extra questions and a misleading reason, not a missed defect. It probably also happens in 2.13 today (inferred from 2.13's instructions, not tested), so 2.14 does not make it worse. It does undercut the "your decisions stick" promise for uncommitted code, and the README does not mention it.

| Option | User impact | Risk | Time / cost |
|---|---|---|---|
| **A. Ship now; list it as a known limit** (recommended) | Users get the 2.14 fixes now. The limit appears in the GitHub release notes (first bullet) and the backlog; the README stays silent on it. | Low. Nothing is lost. Users who read only the README miss the caveat. | None |
| B. Ship, but also add it to the README first | Same as A, and the README is complete. | Low. Any README change makes a new release commit, so every automated check re-runs on it. Plugin files would be identical, so the live smoke result carries over unless you want it re-run. | About 45 minutes, no paid spend. You re-sign this page. |
| C. Treat it as release-blocking and fix it first | The fix lands in 2.14 instead of later. | Medium-high. It sits in the same decision logic that took three repair rounds in Phase 60. If the one allowed fix round fails, the rule is: don't ship, re-scope. | Likely a day or more, plus a new live smoke (about $20–30, needs a new approved proposal). |

I recommend A. 2.14 is strictly better than 2.13 here, holding it delays four real fixes, and C1 becomes backlog item 999.28 for the next milestone. Choose B if you want the README to carry every limit.

## What users should know

- On the default review, a finding you deferred or dismissed in code you have not committed yet is asked again on every pass, even when nothing changed, and the card says the code next to it changed. Nothing is lost, and Close out still completes with your decisions.
- A finding in a new file that git does not track yet is not asked again after you edit near it.
- PR reviews stop with an error on PRs above GitHub's diff size limits (about 300 files or 20,000 changed lines) instead of reviewing part of the PR.
- `--all` reviews do not keep your decisions between runs; each `--all` run starts fresh.
- After upgrading from 2.13, a finding you already decided may be asked again once, the next time code near it changes.
- Only the default review and Close out were run live; the other routes are covered by tests, and the PR diff fetch was checked once against real PRs. The live run confirmed that Close out completes; the re-ask after a nearby edit is proven by tests, because the first limit above re-asks in that live setup anyway.

## Dependabot

Dependabot alerts are turned off on this repo and the command-line tool can't list Dependabot PRs, so that review couldn't run. The shipped code uses only Python's standard library, so there are no third-party runtime packages to patch (pytest is used only to run tests). No settings were changed.

## Not proven live — waiver requested

Approving the release also waives these:
- GSD, range, PR, incremental (second pass onward) and `--all` reviews: tested automatically, not run live.
- The PR diff fetch was checked live on two real PRs only; PRs with binary files or very large PRs were not.
- The "edit near a decided finding" trigger: proven by tests only (see Decision 1).
- Claude's reading of plain-English answers in a live session.
- Catch and false-alarm rates: not measured for 2.14 (v2.11 is still the last measured result).
- Pausing and later resuming a review: no full walk-through, live or automated.

## Owner sign-off

Status: SIGNED OFF (owner, 2026-10-30)

Owner's words, verbatim: "A: Ship, known limit (Recommended)". Given by the owner directly in the main session (AskUserQuestion, 2026-10-30), with no added conditions. **Decision 1 = A:** ship now; C1 is the first Known limit in the GitHub release notes and goes on the backlog as 999.28; the README stays unchanged. The waivers listed above are granted. Approval means "proceed", not code review; the evidence is the test and live-smoke results. After sign-off, this phase is release-ready, and publishing happens at milestone close from [61-CLOSE-RUNBOOK.md](61-CLOSE-RUNBOOK.md).

Full record: [61-RELEASE-RECORD.md](61-RELEASE-RECORD.md) · live smoke: [61-LIVE-SMOKE.md](61-LIVE-SMOKE.md) · residual ledgers (34 items, linked, not walked): [59-REPRO.md](../59-stale-decisions-and-lost-deferrals/59-REPRO.md), [60-REPRO.md](../60-exact-change-evidence-and-reliable-finalize/60-REPRO.md), [60-HUMAN-UAT.md](../60-exact-change-evidence-and-reliable-finalize/60-HUMAN-UAT.md).
