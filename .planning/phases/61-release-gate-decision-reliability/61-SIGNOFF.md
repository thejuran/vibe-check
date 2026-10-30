# vibe-check 2.14.0 — release sign-off

Candidate: 47978aa (C2, version 2.14.0). It replaces the earlier candidate 0d2be77. The only change is the README fix you chose under Decision 1 (option B). Every plugin file is byte-identical to 0d2be77. All nine automated checks were re-run on 47978aa on 2026-10-30. Nothing outside planning files has changed since. Nothing has been published.

**What ships:** decided findings are asked again when their code changes, including in the uncommon layouts 2.13 missed. Deferred findings no longer vanish under `min_confidence`. The "nearby edit" window is the stated five lines. Close out completes. Reviewers and scoring are unchanged. The README now states the "asked again on every pass" limit for uncommitted code (see Decision 1).

## Checks (re-run on 47978aa)

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

PASS, carried over unchanged. The three live sessions ran on 0d2be77. The plugin files they loaded are byte-identical in 47978aa: git reports no difference under `plugins/`, and both commits have the same plugin tree id. The README is not part of what the plugin runs. In those sessions, a deferred finding was asked again after an edit near it, and Close out wrote the final report with both deferred findings listed. The same finding was also asked again on a pass where nothing had changed (Decision 1). So the live run does not prove the "edit near it" trigger on its own; that rests on the automated tests.

## Decision 1 — the "asked again on every pass" behavior

**What happens:** when you review code you haven't committed yet, a finding you defer or dismiss is asked again on the very next pass, even if you changed nothing. The card also says "code next to it changed", which is false. This was seen live on the default review. A GSD review that includes uncommitted changes uses the same step, so it should behave the same way; that is from reading the code, not a live run. Nothing is lost, and Close out still completes with your decisions. It means extra questions and a misleading reason, not a missed defect. It probably also happens in 2.13 today (inferred, not tested). It is backlog item 999.28 for the next milestone.

**Your ruling: B — ship, with the README corrected first** (owner, 2026-10-30). Your selection, verbatim: "Switch to B (Recommended)". You chose this in the main session (AskUserQuestion) after verification showed that the README contradicted the limit rather than being silent on it. The earlier ruling, A, is kept below as history.

**What changed in the README (candidate 47978aa):**
- The 2.14 "nearby edit window" bullet now ends: "One exception: code you have not committed yet counts as changed again on every pass, so a decided finding in or next to it is asked again each time (see Limitations)."
- The 2.13 "Your decisions stick" bullet now says decisions hold "when you edit unrelated code (but see Limitations for findings in code you have not committed yet)."
- "Known limitations (2.14)" has a new first bullet with the limit, the same wording as the first item below.

Nothing else in the README changed. The other review notes (a stale "this release" pointer in the 2.12 entry, the 2.11 "previous release" label, and the dropped 2.13→2.12 downgrade note) stay as they are and are carried in the review record.

## What users should know

- When you review code you have not committed yet (the default review, or a GSD review that includes uncommitted changes), a finding you deferred or dismissed in or next to that code is asked again on every pass, even when nothing changed. The card says the code next to it changed. Nothing is lost, and Close out still completes with your decisions. (Now in both the README and the GitHub release notes.)
- A finding in a new file that git does not track yet is not asked again after you edit near it.
- PR reviews stop with an error on PRs above GitHub's diff size limits (about 300 files or 20,000 changed lines) instead of reviewing part of the PR.
- `--all` reviews do not keep your decisions between runs; each `--all` run starts fresh.
- After upgrading from 2.13, a finding you already decided may be asked again once, the next time code near it changes.
- Only the default review and Close out were run live; the other routes are covered by tests, and the PR diff fetch was checked once against real PRs. The live run confirmed that Close out completes; the re-ask after a nearby edit is proven by tests, because the first limit above re-asks in that live setup anyway.

## Dependabot

Dependabot alerts are turned off on this repo (re-checked 2026-10-30, still off), and the command-line tool can't list Dependabot PRs, so that review couldn't run. The shipped code uses only Python's standard library, so there are no third-party runtime packages to patch (pytest is used only to run tests). No settings were changed.

## Not proven live — waivers (granted; please re-confirm)

You granted these at the first sign-off. They stand as granted for 47978aa, and re-signing re-confirms them:
- GSD, range, PR, incremental (second pass onward) and `--all` reviews: tested automatically, not run live.
- The PR diff fetch was checked live on two real PRs only; PRs with binary files or very large PRs were not.
- The "edit near a decided finding" trigger: proven by tests only (see Decision 1).
- Claude's reading of plain-English answers in a live session.
- Catch and false-alarm rates: not measured for 2.14 (v2.11 is still the last measured result).
- Pausing and later resuming a review: no full walk-through, live or automated.

## Owner sign-off

Status: AWAITING RE-SIGN (owner)

Re-sign on candidate 47978aa: _(not yet recorded)_. Approval means "proceed", not code review; the evidence is the test and live-smoke results. After re-sign, this phase is release-ready, and publishing happens at milestone close from [61-CLOSE-RUNBOOK.md](61-CLOSE-RUNBOOK.md).

### History — first sign-off on 0d2be77 (superseded)

Status then: SIGNED OFF (owner, 2026-10-30). Owner's words, verbatim: "A: Ship, known limit (Recommended)". Given by the owner directly in the main session (AskUserQuestion, 2026-10-30), with no added conditions. **Decision 1 = A:** ship now; C1 is the first Known limit in the GitHub release notes and goes on the backlog as 999.28; the README stays unchanged. The waivers listed above were granted.

That ruling was framed as "the README stays silent on it". Verification (61-VERIFICATION.md, 61-REVIEW.md WR-01) found the README was not silent: it made claims the limit contradicts. Shown that, the owner switched to B the same day ("Switch to B (Recommended)"). Candidate 0d2be77 is superseded by 47978aa.

Full record: [61-RELEASE-RECORD.md](61-RELEASE-RECORD.md) · candidate and README fact-check: [61-CANDIDATE.md](61-CANDIDATE.md) · live smoke: [61-LIVE-SMOKE.md](61-LIVE-SMOKE.md) · residual ledgers (34 items, linked, not walked): [59-REPRO.md](../59-stale-decisions-and-lost-deferrals/59-REPRO.md), [60-REPRO.md](../60-exact-change-evidence-and-reliable-finalize/60-REPRO.md), [60-HUMAN-UAT.md](../60-exact-change-evidence-and-reliable-finalize/60-HUMAN-UAT.md).
