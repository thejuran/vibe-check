---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 08
subsystem: decision-cards / fix-loop prose
tags: [fix-loop, follow-up, stale-card, close-out-carrier, bottom-line, ANSR-01, ANSR-02]
requires:
  - "58-03 (batch_card.py resolve contract, --prior-rows)"
  - "58-04 (Translate the answer paragraph, carried close-out paragraph, Bottom line slot)"
  - "58-07 (Phase 0 --close-out-after-rerun normalizer + CLOSE_OUT_AFTER_RERUN line)"
provides:
  - "50-fix-loop.md **Stale card (D-07).** paragraph with the --prior-rows twin resolve fence"
  - "50-fix-loop.md **Ask only what is missing (D-05, D-06).** paragraph incl. the D-08 full-card fallback"
  - "D-17 routing in steps 2/3 (Close out directly when nothing to review)"
  - "The Rerun re-enters with ${original_args} --close-out-after-rerun only for a close-out answer; ${original_args} defined once in the Close out bullet"
  - "Typed 'bottom line' / 'do what it says' copies $SUGGESTFILE file-to-file"
  - "test_fix_loop_card.py: followup/stale_card/close_out_routing/rerun_marker/original_args/typed_bottom_line checks + TestCarrierRoundTrip through the real 00-scope.md fence"
affects: [58-05 (mirrors the Ask only what is missing paragraph in 90-finalize.md), 58-09]
tech-stack:
  added: []
  patterns: ["prose string extracted by regex and run through the real shell fence", "real-file mutant driver in scratchpad"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/50-fix-loop.md
    - plugins/vibe-check/scripts/test_fix_loop_card.py
decisions:
  - "$PRIORROWSFILE is bound to the answered card's own $ROWSFILE path, used as is — not rewritten with the Write tool (no retyped rows JSON)"
  - "The Rerun says `CLOSE_OUT_AFTER_RERUN=` with value 1 rather than the literal `CLOSE_OUT_AFTER_RERUN=1`, so 58-04's lock that the literal appears exactly once (in the carry paragraph) still holds"
  - "Several unclear pieces each get their own question inside the one AskUserQuestion call; a `blocked` ref is never asked about"
metrics:
  duration: ~20 min
  completed: 2026-10-27
  tasks: 3
  files: 2
  suite: "3448 passed / 0 failed (was 3433; +15 tests)"
requirements: [ANSR-01, ANSR-02]
---

# Phase 58 Plan 08: Ask only the gap, stale re-map, close-out carried across the Rerun Summary

The fix loop now handles a plain-English answer it can only partly read. It holds the whole answer and asks one small question about only the unclear piece. If the reply is still unclear, it shows the full card once with a note and stops asking. Numbers from an older card are re-mapped by finding identity. "Fix X, then close out" now survives the automatic Rerun: the Rerun re-enters with the one-shot `--close-out-after-rerun` marker, and Close out's re-entry drops it. Typing "bottom line" takes the parser-checked suggestion file-to-file.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | 0ecd1f2 | test(58-08): add failing fix-loop locks for the missing-piece follow-up, stale re-map, close-out routing, the Rerun's one-shot marker and typed bottom line; carrier round-trip through the real Phase 0 fence |
| 2 | 0a12d61 | fix(58-08): fix-loop asks only the missing piece once, falls back to the full card once, re-maps stale cards by identity (D-05..D-08) |
| 3 | 42e5d1d | fix(58-08): close-out rides the Rerun as --close-out-after-rerun, consumed once; typed "bottom line" takes the suggestion (D-09, D-17) |

## RED (Task 1, observed)

`pytest -q scripts/test_fix_loop_card.py -k "Phase58Routing or CarrierRoundTrip"` → `13 failed, 2 passed`. All 6 `_holds` tests and all 6 mutant tests failed (the needles were absent). `test_rerun_marker_is_read_back` failed with `no marker re-entry found`. The 2 that passed (`test_close_out_drops_the_marker`, `test_non_stripping_original_args_would_carry`) only need the 58-04 Close out re-entry and the 58-07 fence, which were already there. `-k "not Phase58Routing and not CarrierRoundTrip"` → `92 passed`.

## The `**Ask only what is missing (D-05, D-06).**` paragraph (verbatim; 58-05/58-09 mirror it)

It sits in the **Typed answer via Other** bullet, after the **Stale card (D-07)** paragraph and before `- Stop here… →`. The `ok` false bullet of **Translate the answer** points to it.

````
  **Ask only what is missing (D-05, D-06).** Hold the whole answer and record nothing — never half-apply: no clause of the answer is recorded or sent to the fix agent while another clause of it is unclear, so "fix X, then close out" is carried out together or not at all. Ask ONE short AskUserQuestion about only the unclear piece — never the full card; when more than one piece is unclear, each gets its own question inside that same AskUserQuestion call. Single-select; the tool adds Other.
  - A `many` or `conflict` ref → header "Which row"; the question names the verb and asks which listed row was meant. Options = the ref's `candidates`: each `label` (`#n file:line`) as an option, its `title` as the description. More than 4 candidates → list the labels in the question text instead and take the number through Other; exactly 1 → add a "None of these" option.
  - A `none` or `count_mismatch` ref → header "Which rows"; the question says what did not match (the reference matched no row, or the stated count differs from the rows it matched) and that the rest of the answer is held until this is settled. Options = up to 4 `#n file:line` labels — the ref's `candidates` when it has them, else rows no other ref claimed; typed row numbers arrive through Other.
  - `needs_reason` true → header "Reason"; options exactly `False positive`, `Accepted risk` and `Out of scope for this milestone` (the owner's own words arrive through Other).
  - A `blocked` ref is never asked about — it resolves once the ref it waits on is answered. A `resolve` refusal or a copy refusal has no piece to narrow — go straight to the full-card fallback at the end of this paragraph.

  Then write the completed refs to `$REFSFILE` with the Write tool — the same refs, each unclear one replaced by `number` refs for the chosen rows, and the chosen reason as `reason` — and re-run the resolve fence (its `--prior-rows` twin while any `prior_number` ref remains). `ok` true → the `ok` true branch above: the whole answer together, with its echo. There is one follow-up per gap (D-08): when the reply is still unclear — `resolve` is still not `ok`, or the reply names nothing on the list — still nothing is recorded; show the full card once, its question led by a note built from the resolve output that says what could not be matched (e.g. "Could not match: dismiss reference 2 — matched 0 rows; nothing from your answer was recorded"), then stop asking: the owner's answer to that card is taken as a new answer.
````

## The Stale card paragraph (verbatim)

````
  **Stale card (D-07).** When the card the owner answered is not the current one (the review re-ran since they read it, so its rows may be renumbered or changed), write every row number in the answer as a `prior_number` ref — `{"verb": V, "kind": "prior_number", "n": N}` — and bind `$PRIORROWSFILE` to the rows file of the card they answered (that pass's `$ROWSFILE` path, used as is — never retyped or rebuilt). Run this twin of the resolve fence in its place, then branch on its output exactly as above:
  ```bash
  if python3 "$VC_ROOT/scripts/batch_card.py" resolve --rows "$ROWSFILE" --answer "$REFSFILE" --prior-rows "$PRIORROWSFILE" > "$RESOLVEFILE"; then
    cat "$RESOLVEFILE"
  else
    echo "— nothing was recorded; the answer could not be read." >&2
  fi
  ```
  `resolve` re-maps each old number by finding identity (`stable_hash`, then file and title), never by position, so the grammar and the echo use the current rows and the owner sees where each one went: when `stale` is true, append ` (your numbers re-mapped to the current card)` to the `Read your answer as:` line, so the echo shows the new numbers. A `prior_number` that maps to no current row, or to more than one, comes back `none` or `many` and is asked about alone, below.
````

## The Rerun paragraph (verbatim)

````
**The Rerun.** Clear the subset first: `$SUBSETFILE` is consumed by this one card — `rm -f "$SUBSETFILE"; unset SUBSETFILE` before every automatic rerun (substituting the literal subset path for `"$SUBSETFILE"`, as in the subset fence), and every later pass's card uses the ordinary fence, so a Finalize-routed subset never carries into the next pass's card. Then loop back to Phase 0 of the current command with `$ARGUMENTS = "${original_args}"` — or, when the answer that started this Rerun carried close out (`close_out` true in `$RESOLVEFILE`, D-17), with `$ARGUMENTS = "${original_args} --close-out-after-rerun"`: Phase 0 strips that whole token from the scope and prints `CLOSE_OUT_AFTER_RERUN=` with value 1, which the next pass's card section (or the spine's no-findings skip) turns into Close out. Because `${original_args}` never contains the marker, it is never carried into a second Rerun — it lives for exactly one re-entry. State file persists; Phase 0's empty-diff stop does not apply to this Rerun when Step B committed at least one fix (a clean tree is the normal result of committed fixes), so Phase 0.5 detects the new commits since the last pass's `head_sha`; when nothing was committed the stop applies as usual; Phase 3 carry-forward marks fixed findings as `fixed-since-last`; the M7 multi-pass summary shows the diff. Do not re-run Phase 0.7 first-run setup, since state exists.
````

The Close out bullet keeps `$ARGUMENTS = "${original_args} --finalize"` and now ends with the one definition: "`${original_args}` is this pass's `$ARGUMENTS` minus every whole-token `--finalize` and `--close-out-after-rerun` (the same shell-style var the Abandon line and the Rerun use), so a carried close-out marker is dropped here and never reaches Finalize or a later pass."

Step 2 now ends with the D-17 routing: the Rerun carries `close_out` as the marker, and when Step B committed nothing and `close_out` is true, the loop skips the Rerun and goes to **Close out** directly. Step 3 reads "`fix_targets` empty → the Rerun, or **Close out** directly when `close_out` is true (D-17)."

## Verification (observed)

- Task 2 verify: `pytest -q scripts/test_fix_loop_card.py scripts/test_card_text.py -k "<not routing/marker…>"` → `123 passed, 11 deselected`.
- Task 3 verify (neighbours): `pytest -q scripts/test_fix_loop_card.py scripts/test_scope_args.py scripts/test_card_text.py scripts/test_pause_batching.py scripts/test_git_safety_prose.py scripts/test_foreground_dispatch.py scripts/test_tracecheck.py` → `295 passed, 670 subtests passed`. No neighbour file needed an edit.
- Full suite: bare `pytest -q` from plugins/vibe-check → `3448 passed, 4588 subtests passed` (3433 before; +15).
- Greps:
  - `resolve --rows "$ROWSFILE" --answer "$REFSFILE"`: 2
  - `record nothing`: 1
  - `full card once`: 2
  - `never half-apply`: 1
  - `prior_number`: 3
  - `${original_args} --close-out-after-rerun`: 1
  - `minus every whole-token…`: 1
  - `Close out** directly`: 2 lines
  - `cp "$SUGGESTFILE" "$ANSWERFILE"`: 1
  - `${original_args} --finalize`: 2. The plan expected 1; see deviation 2.
  - `from test_scope_args import`: 1
  - `def rerun_marker_problems`: 1

`pytest scripts/test_fix_loop_card.py -k "Phase58Routing or RoundTrip" -v`:
```
TestPhase58Routing::test_close_out_routing_holds PASSED
TestPhase58Routing::test_followup_holds PASSED
TestPhase58Routing::test_mutant_close_out_routing_step3_reruns PASSED
TestPhase58Routing::test_mutant_followup_records_partial PASSED
TestPhase58Routing::test_mutant_marker_carried PASSED
TestPhase58Routing::test_mutant_marker_not_appended PASSED
TestPhase58Routing::test_mutant_stale_without_prior_rows PASSED
TestPhase58Routing::test_mutant_typed_bottom_line_no_copy PASSED
TestPhase58Routing::test_original_args_holds PASSED
TestPhase58Routing::test_rerun_marker_holds PASSED
TestPhase58Routing::test_stale_card_holds PASSED
TestPhase58Routing::test_typed_bottom_line_holds PASSED
TestCarrierRoundTrip::test_close_out_drops_the_marker PASSED
TestCarrierRoundTrip::test_non_stripping_original_args_would_carry PASSED
TestCarrierRoundTrip::test_rerun_marker_is_read_back PASSED
15 passed, 92 deselected, 6 subtests passed
```

## Named mutants applied to the real file (owner rule)

A scratchpad driver (`scratchpad/mutants.py`, with explicit paths) applied each mutant to the real `50-fix-loop.md`, ran the named test(s), and restored the original bytes. A sha256 check after the run confirmed the restore (`restored: True`).

| Mutant | Edit to the real file | Test(s) | Observed |
|--------|-----------------------|---------|----------|
| M1 follow-up records partial | delete " and record nothing" | test_followup_holds | 1 failed |
| M2 stale without --prior-rows | delete ` --prior-rows "$PRIORROWSFILE"` | test_stale_card_holds | 1 failed |
| M3 step 3 never closes out | delete ", or **Close out** directly when `close_out` is true" | test_close_out_routing_holds | 1 failed |
| M4 marker not appended | delete the whole " — or, when the answer that started this Rerun … `--close-out-after-rerun"`" clause | test_rerun_marker_holds + test_rerun_marker_is_read_back | 2 failed |
| M5 marker carried | delete " and `--close-out-after-rerun`" from the `${original_args}` definition | test_original_args_holds | 1 failed |
| M6 typed bottom line without copy | replace the `cp "$SUGGESTFILE" "$ANSWERFILE"` clause with "write it to `$ANSWERFILE`" | test_typed_bottom_line_holds | 1 failed |

The same six also exist as in-memory `test_mutant_*` tests, and all six pass. `test_non_stripping_original_args_would_carry` shows why the definition sentence matters: `49-foo --close-out-after-rerun --finalize`, which a non-stripping `${original_args}` would produce, gives `CLOSE_OUT_AFTER_RERUN=1` on the Finalize entry.

## Walkthrough (static trace plus the real fence; not a live LLM run)

The iPlayarr answer translates to `fix 5; dismiss 1,2,3,4,6,7,8 -- …` with `close_out` true. The steps below are a prose trace from 58-04's verified translation:

1. Step 1 records the 7 dismissals.
2. Step 2 sends #5 through the subset fence to Step B, which fixes and commits it.
3. Because `close_out` is true, the Rerun re-enters with the marker.
4. The next pass's carry paragraph prints "Closing out as you asked — the rerun's report is above." and goes to Close out. That holds even if the rerun reported new findings, and the spine's no-findings skip covers the no-findings case.
5. Close out re-enters with `${original_args} --finalize`, and Finalize's card lists any undecided rows.

No fix-loop card appears at any point after the owner's answer.

I ran the real 00-scope.md normalizer fence on the re-entry strings in both /bin/bash and /bin/zsh. The output was identical in both shells:

| Re-entry string | `CLOSE_OUT_AFTER_RERUN` | `FINALIZE_MODE` | scope |
|-----------------|-------------------------|-----------------|-------|
| `49-foo --close-out-after-rerun` | 1 | 0 | `49-foo` |
| `--close-out-after-rerun` (default diff) | 1 | 0 | `''` |
| `49-foo --finalize` | 0 | 1 | `49-foo` |
| `--finalize` | 0 | 1 | `''` |

Not verified: a live interactive run of the fix loop with a model. This phase rules that out (D-15; paid runs need an approved proposal).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The Rerun's planned wording would break 58-04's carry lock**
- **Found during:** Task 3
- **Issue:** The planned Rerun text says Phase 0 "prints `CLOSE_OUT_AFTER_RERUN=1`". 58-04's `close_out_carry_problems` requires that literal to appear exactly once in the file, in the carry paragraph.
- **Fix:** The Rerun now says "prints `CLOSE_OUT_AFTER_RERUN=` with value 1". The meaning is unchanged and both locks hold.
- **Cost if wrong:** low. This is wording only.
- **Commit:** 42e5d1d

**2. [Rule 1 - Plan inconsistency] `grep -c '${original_args} --finalize'` is 2, not 1**
- **Found during:** Task 3
- **Issue:** 58-04's carried close-out paragraph already says "Close out re-enters with `${original_args} --finalize`", and its lock requires it (CARRY_NEEDLES). The plan's count of 1 predates that paragraph.
- **Fix:** I left both occurrences. The lock that matters, `original_args_problems`, checks `REENTRY` in the Close out bullet and the definition exactly once.
- **Cost if wrong:** low.

**3. [Rule 1 - Test needle] Typed bottom-line needle `(D-09)`**
- **Found during:** Task 3
- **Issue:** The plan's own prose wording is "(same gate, same bulk rules; D-09)", so the needle `(D-09)` could never match.
- **Fix:** The needle is now `same gate, same bulk rules; D-09`. Mutant M6 still trips.
- **Commit:** 42e5d1d

## Assumption Drift (advisory)

- **Found during:** Task 2.
  - **Planned:** "Write the rows file the owner saw as `$PRIORROWSFILE`."
  - **Actual:** `$PRIORROWSFILE` is bound to that pass's own `$ROWSFILE` path, used as is.
  - **Why:** Writing it with the Write tool would mean retyping the rows JSON, which goes against the file-to-file rule.
  - **Cost if wrong:** if the older rows file is gone, the twin refuses with `refused: prior rows file is missing or malformed`. That refusal goes to the full-card fallback, so nothing is recorded wrongly.

## Known Stubs

None in the fix loop. Mirroring the Ask-only-what-is-missing paragraph into `90-finalize.md` belongs to 58-05/58-09.

## Threat Flags

None beyond the register. The plan's threats are covered:
- **T-58-16:** M1, plus the D-08 fallback needles.
- **T-58-25:** M5, plus the round trip that shows Close out prints 0.
- **T-58-26:** M4.
- **T-58-27:** M2.

No new fence puts owner text on a command line. The follow-up note shows only the verb, the ref position and the match count.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/50-fix-loop.md (`--close-out-after-rerun`, `**Ask only what is missing (D-05, D-06).**`, `--prior-rows "$PRIORROWSFILE"`)
- FOUND: plugins/vibe-check/scripts/test_fix_loop_card.py (`def rerun_marker_problems`, `TestCarrierRoundTrip`)
- FOUND commits: 0ecd1f2, 0a12d61, 42e5d1d
- STATE.md / ROADMAP.md / HANDOFF.json untouched
