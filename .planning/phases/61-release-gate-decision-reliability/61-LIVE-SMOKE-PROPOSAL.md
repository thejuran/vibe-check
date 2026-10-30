# Proposal: Phase 61 live smoke of the 2.14.0 candidate (NOT APPROVED)

Status: PROPOSED

Written 2026-10-30. Nothing runs and nothing is spent until the owner explicitly approves this proposal. This proposal does not authorize publishing.

Candidate under test: commit `0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d` (vibe-check 2.14.0, see 61-CANDIDATE.md). If a fix round produces a new candidate, the smoke runs on that one instead.

## Why

Phase 60 repaired Close out (`--finalize`). The repaired steps work by having Claude run a helper that prints a temp-file path, then pass that exact path to the next helper in a fresh command step. The offline tests run these steps in fresh shells and pass. They cannot show that Claude, reading the instructions in a real session, actually carries the printed paths across steps correctly. That is the class of failure that broke Close out in 2.13: the instructions passed tests but ran wrong live. This smoke checks exactly that, on a real session, before 2.14.0 ships (D-01).

It also checks the main 2.14 promise on the default route: a finding you already decided on is asked again, with the right reason, when the code next to it changes.

## Scope

Live, in this smoke (D-02):

- the default review route (`/vibe-check:review` on uncommitted changes);
- Close out (`/vibe-check:review --finalize`).

Not run live: the GSD route, range reviews, PR reviews, incremental pass 2 and later, and `--all`. These rest on the offline tests, plus one free scripted check that fetches a real PR's changes from GitHub and runs them through the real range builder (D-03; network only, no model, no cost). The release record and release notes will say which routes were run live and which were not.

## Method

The assistant runs everything; the owner approves this proposal and sees the results (D-01, D-04).

Setup (no model, no cost):

- Make a throwaway project under `~/.b3/` with one committed file and one uncommitted change containing one clear planted defect (for example, a database query built by pasting in user input).
- Load a sealed, read-only copy of the candidate commit. Bring the installed vibe-check copy to match it exactly, taking a backup of the current installed 2.13.0 copy first and restoring it after the smoke. Fully quit and relaunch Claude Code so the new copy is the one in use.
- Before each session, move aside any notes Claude's auto-memory kept for the throwaway project, so one session cannot carry notes into the next (the Phase 40 problem).
- Every session is a fresh Claude Code process in tmux, in manual permission mode (no bypass), using the owner's configured default model (no model override).

The three sessions:

1. **Session 1 — review and decide.** Run a review. The planted defect should be flagged. Defer that one finding.
2. **Between sessions (no model).** Edit a line 2–4 lines away from the flagged line, without touching the flagged line itself.
3. **Session 2 — re-review.** Run a review again. Pass: the card asks about that finding again and says the code next to it changed since the decision. Decide it again.
4. **Session 3 — Close out.** Run `--finalize`. Pass: `REVIEW.md` is written and the review is archived, and the sentence "Finalize stopped — nothing was written" does not appear.

Evidence kept for the release record: the card line from session 2, whether `REVIEW.md` exists plus its fingerprint, the printed temp-file path lines from session 3, a check that every helper the sessions ran came from the candidate copy (not the working repo), and a fingerprint of each session log. The session logs themselves stay out of git.

## Estimated cost

These are estimates, not spending caps (the owner rejected caps).

| Part | Estimate | Basis |
|---|---|---|
| Session 1: review + defer | about $6–9 | 54-BUDGET.md measured units: live review run median $7.30–9.50; containment-proof session $6.30–8.50 |
| Session 2: re-review + decide again | about $6–9 | same units |
| Session 3: Close out | about $6–9 | same units (Close out is likely cheaper than a review) |
| **Total for the three sessions** | **est. $20–30** | sum, rounded |
| Coordinator time (the session driving the smoke) | separate, not included above | 54-BUDGET.md: coordinator $5–60 per working day |

Assumption: a default `/vibe-check:review` costs at or below the measured deep-review unit, because it runs smaller reviewer models. This was not separately measured (61-RESEARCH assumption A1). The planned setup, memory parking and evidence checks are free.

## Stop rules

- **Invalid run, one retry.** A run is invalid, not failed, if something outside vibe-check spoils it: the wrong plugin copy was loaded (the provenance check shows it did not use the candidate), login expired, or the machine slept. One retry is allowed for an invalid run.
- **Qualifying failure, stop.** If the smoke shows a failure in one of the four qualifying classes — a mandatory gate failing, data loss, a qualifying finding silently lost, or a required workflow broken (for example, Close out cannot complete) — the smoke stops. That triggers the phase's single fix round (D-05): a test that reproduces the failure, the fix, and a full gate re-run, after which the smoke runs again on the new candidate. If it still fails, 2.14.0 does not ship.
- **Anything else, carry and continue.** Wording problems, or one extra question that errs toward asking, are recorded as named known limits in the release record and backlog, and the release continues (D-07).

## What this does NOT trigger

- No live runs of the other routes (GSD, range, PR, incremental, `--all`) (D-02).
- No second fix round without the owner's explicit go-ahead, given with the reproduction in front of them (D-06).
- No publish.
- No repo setting changes.

## If declined

The smoke does not run and nothing is spent. The release record states the gap plainly: the repaired Close-out path is proven only by offline fresh-shell walks, not by a real session. At sign-off the owner is asked to waive the live check (GATE-03), and the release notes say that no live check was run.
