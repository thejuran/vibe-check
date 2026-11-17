# vibe-check 2.15.0 — release sign-off

Candidate: b073e31 (version 2.15.0). Nothing outside planning files has changed since the checks ran.

**What ships:** Close out's mechanical work (fingerprints, counts and the decision on what to do next) now runs as one tested helper that returns one result, instead of Claude running each command itself. Close out got smaller; every review path grew slightly from the safety fixes you chose. Reviewers, scoring and scores are unchanged. Nothing has been published.

## Checks (re-run on b073e31)

| Check | What it shows | Result |
|---|---|---|
| All automated tests on this Mac | 4,126 pass from the plugin's scripts folder, 4,599 from the repo root; 0 fail, 0 skipped | PASS |
| Mac-only tests | The 7 tests GitHub's Linux run leaves out or skips all pass here | PASS |
| Every review route and recovery path | Default, GSD, range, PR, incremental, `--all`, Close out with its retry and safe stop, pause/resume and the fix loop pass offline (898 pass) | PASS |
| Past reviews re-scored the same as 2.14.1 | 170 archived runs, 0 differences; none allowed in advance | PASS |
| No previously caught defect lost | 25 of 26 protected catches kept, 0 lost; 1 under a standing, documented amendment | PASS |
| The five Close-out situations | Same outcomes as 2.14.1 in all 7 walks; only the list of commands run differs | PASS |
| Baseline records untouched | The 2.14.1 baseline files and the test fingerprint are unchanged | PASS |
| Scorer and replay unchanged | Byte-identical to 2.14.1 | PASS |
| No third-party code shipped | 34 shipped Python files use only the standard library | PASS |
| Plugin manifest valid | Claude Code accepts the plugin (same 3 cosmetic warnings as 2.14) | PASS |
| GitHub's automatic test run | Runs when the pull request opens; must be green before merge | PENDING (at close) |

## Live smoke

PASS on this candidate. Three fresh sessions ran the exact release snapshot under the proposal you approved. The default review flagged the planted defect first. Close out with nothing open wrote the final report in one helper call. Close out with two open findings showed its decision card, recorded your typed answer and then wrote the report, keeping the earlier report and archive. All three sessions provably ran the candidate, not the installed 2.14.1. Four small items were seen and carried; none loses work. One is user-visible: after you defer every finding in the fix loop, the review may stop and ask instead of continuing (one extra step).

## The two counts

These are size counts, not tokens or cost.
- **Close out:** 136,114 → 131,381 bytes (−4,733) and 92 → 85 steps (−7).
- **Review paths:** each grew by +1,705 to +1,966 bytes (+0.54% to +0.89%) and by +2 counted steps: plain review 36 → 38, deep review 42 → 44, plain `--all` 45 → 47, deep `--all` 51 → 53, fix loop 112 → 114 steps.
- All growth is itemised to the safety and saved-progress-path fixes (the cross-call safety fixes you chose before this release, plus the empty-phase-id fix: +495 bytes per path, 0 steps); nothing is unitemised.

**Approving signs this named growth.** Earlier notes quoted "about +0.6%"; the measured range is +0.54% to +0.89%.

## Differences seen

Only the accepted ones; unexpected differences: none.
- An unreadable saved-progress file shows the stop sentence alone, without the shell's "Permission denied" line.
- A folder, branch or phase name containing `$`, a backtick, `"`, `\` or a line break stops the review with one "Review halted" line.
- An empty GSD phase id stops the review with one "Review halted" line.
- On C/POSIX locales, a saved-progress file that is not valid UTF-8 is refused as "state is not valid JSON".
- A git call slower than 60 seconds during Close out leaves that finding open.
- Close out from a subfolder no longer fingerprints a file with unsaved or staged edits, so it no longer closes a finding on changed code.
- Inline Python runs isolated, so a planted `json.py` in the reviewed repo no longer runs (a hole present in 2.14.1).

## WR-02 (empty phase id) outcome

An earlier 2.15 build could let two GSD phases share one saved-progress file and close one phase on another's findings; 2.14.1 stopped safely instead, so it was a new regression, never shipped. It was fixed test-first in the one fix round you approved, and the release candidate contains the fix.

## What users should know

- Only the default review and Close out ran live (including Close out's decision card); GSD, range, PR, incremental, `--all` and the fix loop's fix-and-verify path are covered by tests only.
- A git call slower than 60 seconds during Close out leaves that file's finding open; each Close out fingerprints again from scratch.
- If the Close out helper itself fails, the message names `finalize_gate.py` and no detail is recorded.
- The unsafe-name stop covers `$`, a backtick, `"`, `\` and line breaks only; `;`, `&` and `'` pass, which is safe only while every pasted name stays in double quotes.
- Downgrading to 2.14.1 is untested (no saved-progress field was added, so no effect is expected).
- After you defer every finding in the fix loop, the review may stop and ask instead of continuing; decisions are saved. This one is in the release notes only: adding it to the README would change the shipped files and mean a new candidate and every check again.

## Dependabot

Dependabot alerts are turned off on this repository, so the alerts list could not be read. The Dependabot pull-request listing did run and found no open Dependabot PRs. The shipped scripts use only Python's standard library; pytest is used only for tests. No setting was changed.

## Not proven live — waivers

- GSD, range, PR, incremental (second pass onward) and `--all` reviews: tested automatically, not run live; this includes the empty-phase-id stop — waiver: granted (owner, 2026-11-16)
- The fix loop's fix-and-verify path: tested automatically; the live run only reached its card and rerun — waiver: granted (owner, 2026-11-16)
- Pausing and later resuming a review: no full walk-through, live or automated — waiver: granted (owner, 2026-11-16)
- Catch and false-alarm rates: not measured for 2.15 (v2.11 is still the last measured result) — waiver: granted (owner, 2026-11-16)

## Tag and title

Tag `v2.15`, title `v2.15 — Lean orchestration` (confirm or change).

## Owner sign-off

Status: SIGNED OFF (owner, 2026-11-16)

**Channel:** AskUserQuestion in the main session (not relayed by any agent)
**Selection, verbatim:** "Go (Recommended)"
**Description shown with the selection, verbatim:** "Sign off with tag v2.15 and title 'v2.15 — Lean orchestration', and grant the 4 waivers. Next: verify-work, then the close runbook. Merging still waits for CI to pass and your OK."
**Tag / title / message:** `v2.15` / `v2.15 — Lean orchestration` / `vibe-check 2.15.0 — lean orchestration` (unchanged)
**Waivers:** all four granted (owner, 2026-11-16)
**Named growth:** signed (+0.54% to +0.89% bytes, +2 steps per review path)
**Still gated:** G12 (CI green on the PR head) and the owner's OK to merge, per 65-CLOSE-RUNBOOK.md

Full record: [65-RELEASE-RECORD.md](65-RELEASE-RECORD.md) · live smoke: [65-LIVE-SMOKE.md](65-LIVE-SMOKE.md) · empty phase id: [65-REPRO-WR02.md](65-REPRO-WR02.md) · notes: [65-RELEASE-NOTES.md](65-RELEASE-NOTES.md) · close steps: [65-CLOSE-RUNBOOK.md](65-CLOSE-RUNBOOK.md)
