# Phase 57 deferred items

## test_replay.py::TestDiffMode::test_member_only_mutation_exits_one (found during 57-05)

- **Status:** RESOLVED by the orchestrator after 57-05 (re-anchored the mutant on the current `changed_line_ranges)` / `members.append(ref)` / `kept_by_ident[ident] = ref` lines; test_replay.py 64 passed). Was a 57-04 regression, not pre-existing; originally logged as out of 57-05 scope (57-05 changes no Python under test here; score.py untouched).
- **Cause:** the `"member"` mutant in `test_replay._MUTANTS` (line ~697) anchors on the score.py text
  `carried_obligations[id(m)]["obligation"], m, pass_number)\n            members.append(ref)\n`.
  57-04 (`04e2c65` / `273a1e4`) rewrote that region of score.py, so the anchor now matches 0 times
  (`AssertionError: 0 != 1 : mutation anchor moved: member`).
- **Fix owner:** re-anchor the mutant on the current score.py member-append line (a test-only change);
  belongs with 57-04 follow-up or the 57-07 cross-check.
- **Note:** earlier waves reported 7 red because the holdout-barrier hook skipped test_replay.py; in
  the 57-05 full run it was collected (3182 passed / 8 failed: the 7 known card-wording/57-06 reds + this one).

## Observed during 57-07 (not fixed; outside the four scope classes)

- **Reopened row also shows "unchanged since pass N, decision pending".** On the end-to-end journey's
  pass 6 the joined row's card line reads `... (critical) — unchanged since pass 5, decision pending —
  2 findings here already dismissed ...`. The pending suffix is the pre-existing `carry_state.pending`
  read (snapshot older than the last pass, record not closed); it stacks with the stale suffix on a
  reopened decided row. Presentation only; no finding is lost or wrongly closed.
- **A row and its own member obligation can share one hash.** When a second lane re-reports a decided
  finding on the same code and out-ranks it, the fresh lead and the absorbed carried record's obligation
  carry the same `stable_hash` (pre-existing Phase 46 shape). 57-07 fixed the one consequence that lost
  an owed re-ask (ea3dab1); the duplicate hash itself is left as is. A hash-bearing re-check request
  reaches only the lead, so closing the member needs a second, hash-less request for its lane.

## Parked by the gap closure (outside the four scope classes; to backlog)

Recorded by 57-13 for the orchestrator to park in the backlog. Not implemented. Source: 57-REVIEW.md; weighed as minor in 57-VERIFICATION.md.

- **WR-01: unbounded relocation search.** A decided ordinary record whose line was deleted can relocate to an identical line elsewhere in the file (no distance bound in the 30-collect-score.md case 2 reuse). Failure direction: the finding stays open (`persisted` instead of `fixed-since-last`), so nothing is closed silently. Caveat: it is not a re-ask. The decision stays `current` on the wrong code until the owner acts or the duplicate line changes, so this one fails toward "kept open, not re-asked", not toward asking.
- **WR-04: snippet first line vs flagged line.** `covers[].code` is the first non-blank line of a member's quoted `current_code`, which may be context above the flagged line. Failure direction: the covered finding, once split out, does not match its entry and is asked again (re-ask, not a silent close).
- **IN-03: relocation simulator only in the test file.** Decided-record relocation is prose-driven; the end-to-end journey checks a Python re-implementation (`relocate_decided`) guarded by phrase locks. This is a test-coverage gap, not a behaviour defect: the shipped prose and the simulator agree today, and the phrase-lock tests (`decided_relocation_holds` in test_nv_render.py) fail if a case is removed from the prose. The review's named consequence of a missed lead-member move is a phantom row (an extra row shown to the owner), not a silent close. 57-13 did not establish a failure direction for every possible drift, so this one is "caught by locks" rather than "proven fail-safe".

## Parked by the second gap closure (57-14..57-16; to backlog)

Recorded by 57-16 for the orchestrator to park in the backlog. Not implemented. Sources: 57-VERIFICATION.md (re-verification 2026-10-26, gap 2, severity minor) and 57-REVIEW-GAPS.md.

- **Diff context: changed_line_ranges from plain `git diff` (3 context lines), not `-U0`.** 30-collect-score.md (step 2, the changed-line-ranges bullet, line ~64) builds `changed_line_ranges` from each hunk's new-side header `+start,count`, including the deletion-only rule `+T,0` -> `[max(T, 1), T + 1]`. That only works for zero-context diffs. The scope phase never asks for one: 00-scope.md lines 36-37, 44 and 51 run `git diff HEAD`, `git diff --staged`, `gh pr diff <ref> --patch` and `git diff <range>`, all with git's default 3 lines of context. The re-verification reproduced it: deleting one line in a 30-line file gives `@@ -6,7 +6,6 @@` under default `git diff` (new-side count 6) but `@@ -9 +8,0 @@` under `-U0` (new-side count 0). Effects: (1) the 30-collect-score.md deletion rule never fires against real diffs (a pure deletion reads as an ordinary 6-line hunk); (2) the 3 unchanged context lines on each side of every hunk count as "changed", so the effective nearby window is about 8 lines, not 5, and the `in_diff` bonus lands on unchanged context lines.
  - **Failure direction:** asks, never drops. A decided finding 6-8 lines from an unrelated edit can be re-asked. A decision is never silently closed by this gap.
  - **Why it is outside this round:** the root cause (no `-U0` on any orchestrator diff, and no upstream rule for building ranges from hunks) predates Phase 57. The Phase 56 re-check trigger already used the same commands. Fixing it changes every diff the orchestrator builds, and this suite cannot exercise it on its own because every committed fixture builds `changed_line_ranges` by hand.
  - **Backlog acceptance (the verification's three `missing` items):** (a) either require `-U0`/`--unified=0` for every diff the scope phase builds `changed_line_ranges` from, or build the ranges from the `+`/`-` line markers rather than hunk-header counts, so context lines never enter `in_diff` or the nearby window; (b) if `-U0` is adopted, check whether any other prose or scoring step assumes the default 3-line context (for example silenced-marker windows); (c) prove the real construction end to end: a small integration fixture that runs `git diff` through the documented hunk rule and asserts the resulting ranges, not a hand-built dict.
- **57-REVIEW-GAPS.md IN-01..IN-05** (Info). 57-15 changed none of them; score.py's split-pass stamp is the only production change in this round.
  - **IN-01:** the inherited `band: null` predicate differs between the card and the comparator. `_inherited_was_band` uses `entry["band"]` even when it is `None` and re-asks with cause `severity`; the card falls back to the decision's band. Failure direction: asks (re-ask with misleading "severity changed" wording); presentation mismatch, nothing closes.
  - **IN-02:** `covered_count` counts by title, so two different covered concerns with the same generic title count once. Failure direction: presentation only (the card under-counts dismissed findings); nothing closes.
  - **IN-03:** `_covering` picks the first matching covering decision in sorted-hash order, not the most recent. Failure direction: an older decision taken at a higher band can mask a band rise against a newer one, which is a keep, not an ask. The review rates it unlikely (needs re-decided overlapping rows).
  - **IN-04:** a replace hunk with a net deletion (under `-U0`, `@@ -10,3 +10,1 @@` -> `[10, 10]`) does not also cover the line after the hunk, unlike the pure-deletion rule's `T+1`. Failure direction: a flagged line exactly at the window's edge below it is missed by one line (a keep at the boundary). Moot until the diff-context item above is fixed, because real diffs are not `-U0` today.
  - **IN-05:** D-05 corroboration ("now also reports it") needs byte-identical titles across lanes, so a second lane confirming the same defect usually shows up as a newcomer. Failure direction: asks (the card says "a new concern from X joined it"); not a wrong-keep.
- **SA-01 — resolved by owner ruling D-17** (strict: the neighbour's fix re-asks; no exemption for the lead's own resolved line), implemented in 57-15 (3b78957) and proven by TestSplitPassNearby s1-s3 and the split-row shape guard. Not parked.

## Parked by the third gap closure (57-17..57-19; to backlog)

Recorded by 57-19 for the orchestrator to park in the backlog. Not implemented. Sources: the 57-17 planner's probe (57-17-PLAN.md Task 1 "Scope note") and 57-REVIEW-GAPS2.md.

- **Covered low-entropy member filtered sub-threshold on its split pass.** This comes from the planner's probe. A `}`-line member (conf 75, 3-line `current_code`) is covered by a dismissed row. The lead's fix at line 12 (diff `[[12,12]]`) splits it out. It comes back `needs-recheck` because of the widened carry compare, scores below the deep-review threshold once it is out of the diff, and is filtered as `sub-threshold`. It carries no obligation because it was never a row. So no kept-open row is emitted, and it is not re-asked.
  - **Failure direction:** the finding leaves the open set without a decision card. That is a keep, not an ask. The row decision that covered it stands.
  - **Why it is outside this round:** this is the sub-threshold rule on a weak finding, not the lead-only carried detection that 57-18 fixed. It was not reproduced as a gate failure. It needs an owner ruling on whether a covered member that falls sub-threshold after its window changed should be kept open under the covering decision.
  - **Backlog acceptance:** a real-chain fixture of the probe shape (conf 75) asserting either a kept-open row or a documented drop reason that names the covering decision.
- **57-REVIEW-GAPS2.md resolutions.** Nothing from the second gap-closure review is parked.
  - **CR-01 + SA-01:** closed by 57-18 (8bd75ec). Carried-ness and the prior snapshot now come from any source record carried under the row's hash, and the prior is seeded before member dedup. This covers both the split shape (CR-01) and the non-split shape (SA-01). The 57-17 fixtures prove it (TestSameLaneRereport a/a2/b/c/d, and the TestLeadOrderInvariance same-lane fresh-leads permutations), reverse-run red at 584f7bb and green at 90228be (57-19 ledger).
  - **WR-01:** closed by 57-18 Task 2 (90228be). TestWr01Guards w1 (the needs-recheck arm of `_CARRIED_STATUSES`) and w2 (seed hash equality) each have a mutant that trips the named guard.
  - **IN-01:** resolved by docstring in 57-18. Quoting 57-18-SUMMARY.md: "a covered member carries no stored hash, so score.py cannot tell a hash-preserving needs-recheck (a low-entropy line whose window changed) from a hash-changing one. It therefore keeps stamping under any carried status. When a carried record's own line has changed, it re-hashes into a finding that no decision or covers entry can match, so a stamp there is inert."
  - **IN-02:** resolved in 57-18. The over-long `_snapshot_for(...)` call is split over two lines, and no touched line is over 100 columns.
