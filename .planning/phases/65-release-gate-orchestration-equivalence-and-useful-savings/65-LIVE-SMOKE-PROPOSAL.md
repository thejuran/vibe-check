# Proposal: Phase 65 live smoke of the 2.15.0 candidate (NOT APPROVED)

Status: PROPOSED

Written 2026-11-16. Nothing runs and nothing is spent until the owner explicitly approves this proposal. This proposal does not authorize publishing.

Candidate under test: the gated release commit recorded in 65-CANDIDATE.md (vibe-check 2.15.0, built after the WR-02 fix in plan 65-03 lands). If a later fix round produces a new candidate, the smoke runs on that one instead, under the rules below.

## Why

2.15.0 rewrites Close out (`--finalize`). In 2.14.1 Claude worked through many separate steps; in 2.15.0 it makes one helper call and then acts on the helper's structured result (write the report, show a decision card, or stop with a message). Reviews also now print the saved-progress file path once, and later steps are told to reuse that exact printed path in fresh command steps.

The offline tests run these steps in fresh shells and pass. They cannot show that Claude, reading the rewritten instructions in a real session, actually makes the one helper call, acts on its result correctly, and reuses the printed path across steps. That is the kind of failure that broke Close out in 2.13: the instructions passed tests but ran wrong live. This smoke checks exactly that, in real sessions, before 2.15.0 ships (D-01).

## Scope

Live, in this smoke (D-02):

- the default review route (`/vibe-check:review` on uncommitted changes);
- Close out (`/vibe-check:review --finalize`), including its decision card.

Not run live: the GSD route, range reviews, PR reviews, incremental pass 2 and later, `--all`, and the fix loop. These rest on the offline tests only. The release record and release notes will name them as not run live, and they are listed for an owner waiver at sign-off.

## Method

The assistant runs everything; the owner approves this proposal and sees the results (D-03).

Setup (no model, no cost):

- Make a throwaway project under `~/.b3/` with one committed file and one uncommitted change containing one clear planted defect (a database query built by pasting in user input).
- Load a sealed, read-only copy of the gated candidate commit (the one recorded in 65-CANDIDATE.md). Back up the installed vibe-check copy, bring it to a byte-for-byte match with the candidate, and restore the backup after the smoke. Fully quit and relaunch Claude Code so the candidate copy is the one in use.
- Before each session, move aside any notes Claude's auto-memory kept for the throwaway project, so one session cannot carry notes into the next.
- Every session is a fresh Claude Code process in tmux, in manual permission mode (never bypass), using the owner's configured default model (no `--model` override). Keep the machine awake for the whole smoke.

The three sessions:

1. **Session 1 (S1) — review and defer.** Run `/vibe-check:review`. Pass: the planted defect is flagged, the finding is deferred, and the saved-progress path the review prints is the one later steps use.
2. **Session 2 (S2) — Close out.** In a fresh process, run `/vibe-check:review --finalize`. Pass: `REVIEW.md` is written through the helper's structured result, Close out's check passes, the sentence "Finalize stopped — nothing was written or archived" does not appear, and the printed state path is reused rather than rebuilt.
3. **Session 3 (S3) — Close out with a decision card.** Run a second review that ends with one finding left undecided, then run `--finalize`. Pass: Close out shows the decision card, records the answer and writes `REVIEW.md`, with the same checks as S2.

Evidence kept for the release record: whether `REVIEW.md` exists in S2 and S3 plus its fingerprint, the printed state-path lines from each session, the decision card line from S3, a check that every helper the sessions ran came from the candidate copy (not the working repo), and a fingerprint of each session log. The session logs themselves stay out of git.

## Estimated cost

These are estimates, not spending limits (the owner rejected caps).

| Part | Estimate | Basis |
|---|---|---|
| S1: review + defer | about $6–9 | 54-BUDGET.md measured units: live review run median $7.30–9.50; containment-proof session $6.30–8.50 |
| S2: Close out | about $6–9 | same units (Close out is likely cheaper than a review) |
| S3: second review + Close out with decision card | about $6–9 | same units |
| **Total for the three sessions** | **est. $20–30** | sum, rounded |
| Coordinator time (the session driving the smoke) | separate, not included above | 54-BUDGET.md: coordinator $5–60 per working day |

Assumption A1: a default `/vibe-check:review` costs at or below the measured deep-review unit, because it runs smaller reviewer models. This was not separately measured. Setup, memory parking and evidence checks are free.

## Stop rules

- **Starts only after the free gates pass.** The smoke starts only after the free gates have passed on the candidate.
- **Invalid run, one retry.** A run is invalid, not failed, if something outside vibe-check spoils it: the wrong plugin copy was loaded, login expired, the machine slept, or the provenance check fails. One retry is allowed for an invalid run. No session beyond the three named sessions and that one retry opens under this approval. If the retry is also invalid, the result is recorded as invalid and the live check goes to the waiver list at sign-off.
- **Decision card not reached.** If S3 cannot reach the decision card (for example, the review will not end with a finding left undecided), no further session opens. The smoke still finishes and records the result as "passed, decision card not run live" when everything else passes, and the decision card goes to the waiver list at sign-off.
- **Qualifying failure, stop.** If the smoke shows a failure in one of the four qualifying classes — a mandatory gate failing, data loss, a qualifying finding silently lost, or a required workflow broken (for example, Close out cannot complete) — the smoke stops. That would normally go to the phase's one fix round (D-08), after which all gates re-run on the new candidate. The one fix round is already used: 65-REPRO-WR02.md records the owner's go (2026-11-16) for the WR-02 fix in plan 65-03. So a qualifying smoke failure needs a second fix round, which needs the owner's explicit go with the reproduction in front of them (D-09); the workflow never opens one on its own. A re-run of the smoke after a fix round needs a separate owner go, with its own added estimate of about $20–30, and its record is appended to 65-LIVE-SMOKE.md as a new run section, never overwriting the failed run.
- **Anything else, carry and continue.** Problems outside the four classes (wording, an extra question that errs toward asking) are carried as named known limits in the release record and backlog, and the release continues (D-10). The 999.32 fix-loop stop after a typed defer is a known carried item, not a failure.

## What this does NOT trigger

- No live runs of the other routes (GSD, range, PR, incremental, `--all`, fix loop) (D-02).
- No second fix round without the owner's explicit go (D-09).
- No publish.
- No repo setting changes.

## If declined

The smoke does not run and nothing is spent. The release record and sign-off carry this waiver text:

"The rewritten Close out (one helper call and its structured result) and the printed state path were proven only by offline fresh-shell walks, not in a live model session. No route was run live for 2.15.0."

At sign-off the owner is asked to waive the live check, and the release notes say that no live check was run.
