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

## Parked by the fourth gap closure (57-20..57-23; final round, D-19)

Recorded by 57-23. Sources: 57-CONTEXT.md (D-19, D-20), 57-REVIEW-GAPS3.md, and the 57-20..57-22 SUMMARYs.

- **D-19 hard stop (owner, 2026-10-27).** Verbatim from 57-CONTEXT.md:
  > **D-19 (owner, 2026-10-27, after round-3 review):** One FINAL structural gap round. Fix the mechanism, not the shape: collect every carried record of a finding's identity (stable_hash) BEFORE any filtering (min_confidence, sub-threshold, dedup), pool their evidence (reopen if ANY carried copy's line saw a nearby change; keep the latest owed stamp), and make row lead order deterministic (tie-break by line, never arrival order). HARD STOP: if the review after this round still finds a wrong-keep, close Phase 57 with it documented as a known limit (backlog) rather than opening another round.
  - **Operating rule.** Run `/bm:code-review 57` and then `/bm:verify-work 57` after this round. If either still reproduces a wrong-keep (a decided finding that should be re-asked and is not), Phase 57 closes with that finding documented as a known limit:
    - Add a backlog item 999.x with `/bm:add-backlog`. Its acceptance fixture is the review's repro.
    - Mark the DECN-03 traceability row `Complete with known limit (999.x)`.
    - Do NOT plan a fifth structural round.
  - Only a reproduced data-loss or silent-finding-loss class (the scope-discipline rule) may still add work.
- **57-REVIEW-GAPS3.md resolutions.**
  - **CR-01** (both variants: a cross-lane same-hash record at another line, and same-lane arrival order) and **CR-02** (a carried twin removed by min_confidence before grouping): closed by 57-21 (1ff5702, 333a5cd).
    - score.py builds a carried-by-hash index before any filter runs.
    - A row's nearby check runs at every carried copy's line, and its prior is pooled (latest owed stamp first, then oldest at_pass).
    - The lead is deterministic: ties break on line.
    - Fixtures are 57-20's p1, p2 (both orders), p3 and p4, plus the three new invariance scenarios. 57-23 reverse-ran them: red at 8a0563a, green at 92b135d.
  - **IN-01:** closed in code by 57-21. One hash gate now covers every prior source, the lead's own snapshot included. Fixture: in01.
  - **WR-01:** closed by 57-20 Task 2 (9fe0e0f). The lead-order invariance guard now covers nine shapes, and the coverage lock was widened from six to nine.
  - **WR-02:** closed under D-20 by 57-22 (70e0719, 6626edb, 92b135d).
    - A deferred covered member below threshold stays open as a kept-open row under its own hash. It travels via `carry_state.py deferred`, then `$DEFERRED_HASHES`, then the envelope key `deferred_hashes`.
    - A dismissed one still drops by design. The dismiss lock is test_dismissed_covered_member_below_threshold_may_drop.
    - The third-round parked entry above ("Covered low-entropy member filtered sub-threshold on its split pass") is therefore RESOLVED for defer and CONFIRMED intended for dismiss. That entry is left as written.
- **OPEN D-20 edge for an owner ruling: a deferred covered member removed by min_confidence still drops.**
  - **What happens.** 57-22's keep-open runs only on the sub-threshold branch. If the owner has set `min_confidence` (an opt-in setting, off by default) and it removes the deferred covered member before grouping, nothing synthesizes a kept-open row. The finding leaves the open list with no card and Finalize writes. D-20 says a deferral never disappears without the owner closing it, so this is a deferral leaving the open list. It lies outside what this round reproduced: the 57-20 fixtures and the 57-22 plan cover the threshold branch only.
  - **Repro (57-23, at HEAD 33a951e).** This is test_decision_continuity.py's `deferred_covered_sub_threshold_scenario("defer", min_confidence=80)`; the member's conf is 75. Scratch script, run from plugins/vibe-check/scripts:
    ```
    pass-2 override: {}
      rows: [('845f88b7', 'sub-threshold; deferred-by: 3449f4b5…')]
      filtered: [(10, 'sub-threshold')]
      open record for hA: True
      outstanding_cw: 1  gate: outstanding-to-phase-5
    pass-2 override: {'min_confidence': 80}
      rows: []
      filtered: [(10, 'below-min-confidence')]
      open record for hA: False
      outstanding_cw: 0  gate: write
    ```
  - **Failure direction:** silent loss of a deferred finding. It is not a wrong-keep of a decided row. It is reachable only when the owner has opted into `min_confidence` at or above the member's confidence.
  - **Candidate backlog item 999.x.** Acceptance: the repro above becomes a real-chain fixture asserting a kept-open row (or a filtered reason naming the covering deferral that keeps the record open), with a mutant on the new branch. Not fixed in 57-23 (scope rule). This needs the owner's ruling: fix in Phase 57 as a reproduced silent-finding-loss class, or park as 999.x.
- **Observed, not acted on (57-20..57-22 deviations and drift outside the four scope classes).**
  - 57-21 Deviation 2: a carried snapshot whose stored stable_hash differs from this pass's computed hash is no longer a prior. If a real carried row ever stores a hash that differs while its line is unchanged (for example, canonical-text drift between passes), its at_pass resets to this pass. Fails toward asking.
  - 57-22 Deviation 3: within a group, the drop order is source order, not covered-first. Reasons and rows are unchanged; presentation only.
  - 57-22 Deviation 1: the decided "Never bind" prose lock now targets a longer phrase. If that sentence is reworded later, the lock must be updated with it. Maintenance only.

## Phase close (2026-10-27): D-19 hard stop applied

Round-4 review (57-REVIEW-GAPS4.md) reproduced wrong-keeps CR-01, CR-02, CR-04 (CR-01 independently re-run by the orchestrator: edit@12 → nearby_at 2, edit@33 → None). Owner rulings D-21 (a new identical copy is not new evidence → CR-03 is not a wrong-keep; the pass-3 re-ask is an over-ask) and D-22 (close under D-19; park both deferral-loss edges). Everything open is carried as backlog **999.23** in ROADMAP.md. The min_confidence repro above must use min_confidence ≤49 (config maximum), e.g. 45 (round-4 IN-03).
