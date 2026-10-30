Decision-reliability release. Not measured: no B3 or holdout run, so there are no v2.14 false-alarm or catch numbers. v2.11 (5/18 · 15/15, MISS) remains the last measured result. Reviewer prompts and the scoring formula are unchanged.

Contents:
- **Decided findings are asked again when their code changes.** 2.13 missed this in a few uncommon layouts: the same flagged code in two places with the edit next to the second copy, or an edit next to a finding grouped under another row. In these layouts a deferred or dismissed finding is now asked again, so Finalize no longer writes `REVIEW.md` without asking.
- **Deferred findings no longer disappear under `min_confidence`.** A finding grouped under a row you deferred stays open with its own card and still blocks Finalize, instead of dropping into the Filtered section.
- **The "nearby edit" window is the five lines the rules state.** Nearness is measured only from lines actually added or removed, not from the unchanged lines `git diff` shows around them, on the default, GSD, range, PR and incremental routes.
- **Close out completes.** Close out no longer loses its temporary file between steps. If a step fails or is refused, it stops without writing `REVIEW.md` or archiving, and running Close out again can complete after it re-checks that nothing changed.

Known limits:
- On the default review, a finding you deferred or dismissed in code you have not committed yet is asked again on every pass, even when nothing changed, and the card says the code next to it changed. Nothing is lost, and Close out still completes with your decisions.
- A finding in a new file that git does not track yet is not asked again after you edit near it.
- PR reviews stop with an error on PRs above GitHub's diff size limits (about 300 files or 20,000 changed lines) instead of reviewing part of the PR.
- `--all` reviews do not keep your decisions between runs; each `--all` run starts fresh.
- After upgrading from 2.13, a finding you already decided may be asked again once, the next time code near it changes.
- Only the default review and Close out were run live; the other routes are covered by tests, and the PR diff fetch was checked once against real PRs. The live run confirmed that Close out completes; the re-ask after a nearby edit is proven by tests, because the first limit above re-asks in that live setup anyway.

Full list in the README (the first limit above is listed only in these notes).

Each change was first reproduced as a failing test on the previous code. 3,821 tests passing at release.
