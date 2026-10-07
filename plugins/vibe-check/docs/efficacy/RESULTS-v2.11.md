# B3 v2.11 — Phase 49 release-candidate measurement (REL-01/REL-02)

## Phase-49 pre-registration

**Written before any Phase-49 measured run.** Every bar, rule and counting method below is fixed
in this committed text before any data exists. The measurement body (results, scoring, release
decision) is appended below this section after the runs; nothing in this section is edited once
the first measured run is committed.

### 1. The deciding bar (REL-01)

The release candidate PASSES when, on the corrected cohort, **false alarms are ≤ 3 of 18 AND
catches are 15 of 15**. The corrected cohort excludes should-quiet-7 per `SUPERSESSIONS-v2.10.md`
#001 (it carries a real config-loss defect), exactly as in Phase 43. The comparison point is
Phase 43's combined result, 3/18 and 15/15: v2.11 must keep every catch and add no false alarm.
In headline terms that is `bar ≤ 3` on the false-alarm arm and `bar 15` on the catch arm.

### 2. The sealed literal (reported, never deciding)

The sealed-literal figure over all 21 quiet runs (should-quiet-7 included) is reported beside the
verdict against a pre-registered bar of ≤ 6, which is Phase 43's combined literal (6/21). It
NEVER decides the verdict: a literal above 6 with a corrected-cohort PASS is still a PASS, and is
disclosed.

### 3. The retune rule (D-04)

On a miss: diagnose, then make **one** targeted fix and build it as snapshot S2 (batch 8). Then
re-run **ALL 12 diffs ×3 once on S2** (36 runs). The fix changes behaviour shared by every diff,
so a change that cures one failed diff could break a passing one; re-running only the failed
diffs would hide that.

- The release verdict is the **S2-only full-cohort verdict**:
  `score43.py aggregate --profile phase49 --label retune-full`, with the same bars (≤ 3 of 18,
  15 of 15) and the sealed literal ≤ 6 still never deciding.
- It is **never** a combine of S runs and S2 runs.
- The first-pass S verdict stays on the record and is printed beside it as `untuned first pass:`.
- On a second miss, STOP: the owner decides ship / no-ship. There is no release on a miss without
  the owner's recorded approval.

### 4. The AXIS basis

Catch verdicts are hand calls on the Phase-43 title/member-title basis (`SCORING-v2.10-phase43.md`
§7.3): a candidate row at the catch site counts only when its survivor title or a member title
names the mechanism. The same basis is used for every pass, so first-pass and retune numbers stay
comparable with each other and with Phase 43.

### 5. The expected residual and the zero-headroom warning

- **Expected residual:** should-quiet-6 is expected to fire 3/3 ("declared but never wired",
  backlog 999.19), exactly as in Phase 43. That alone uses the whole ≤ 3 false-alarm budget.
- **Zero headroom:** one new false alarm anywhere else is a MISS. The nine quiet and catch diffs
  that were not retuned in Phase 43 have never been measured on the shipped Rule-1/Rule-2 prompts,
  so a regression there is possible and would show up first as exactly that one extra alarm.

### 6. The pause metric (REL-02)

**Method.** `plugins/vibe-check/scripts/count_cards.py` counts main-session `AskUserQuestion`
tool_use blocks in each run's local transcript, deduplicated by tool_use id; sidechain (subagent)
records and the answer records are not cards. Each transcript is bound to its committed
`transcript.jsonl.sha256`, and the tool prints counts only. A *firing* is one scored run; a
*fix-loop firing* is a run with at least one card.

**Two baselines, both stated before any data:**

- **Like-for-like (same harness, same decline path):** Phase-43 B3, 2.0 cards per fix-loop firing —
  first pass 52/26 and retune 18/9 — and 52/36 per firing over the first pass.
  `count_cards.py tally` reproduces these from the committed Phase-43 transcripts.
- **Cited:** 5.5 cards per firing, the gate-log figure from the 2026-09-30 roadmap spec. That
  figure measures a different path (GSD phase-mode firings: apply / rerun / finalize, multi-pass),
  which B3 does not exercise, so it is quoted for context and not compared like-for-like.

**Expected value.** The v2.11 B3 value is expected to be 2 cards per fix-loop firing on the
decline path, by design (the "Pass N" card, then the "Stop here" card). B3 therefore cannot show
a pause saving; the metric checks that the new cards did not add pauses.

**Gate-log 2.11.0 figure: unavailable at release.** No deep-review firing on the 2.11.0 build will
exist in the orchestrator gate log before publish, so that figure is pre-declared unavailable.
Nothing is inferred from pass counts.

### 7. The scoring and headline commands

The verdict is computed only by:

    score43.py aggregate --profile phase49 --fp-bar 3 --sealed-fp-bar 6 --catch-bar 15

(with `--label first` for the first pass, or `--label retune-full` for a full-cohort retune). The
`phase49` profile refuses any other bar triple and refuses the `combined` and `retune` labels.
The transcription of the result into the headline is checked by
`score43.py headline-check --profile phase49` against the artifact of record. The headline block
that 49-08 writes below must use exactly this grammar (`<N>`, `<M>`, `<K>`, `<X>`, `<x>`, `<Y>` are
placeholders for the numbers in the artifact):

```text
**<PASS|MISS>** — false alarms 3→<N> of 18 (corrected cohort, bar ≤ 3; should-quiet-7 excluded per SUPERSESSIONS-v2.10.md #001); catches 15→<M> of 15 (bar 15) (no rounding — exact fractions).
Sealed literal (never deciding): false alarms 6→<K> of 21 vs the sealed bar ≤ 6 — would be <PASS|MISS>
Retune: not used
```

or, after a full-cohort retune, the last line reads:

```text
Retune: used — full-cohort S2 headline above (retune/VERDICT.json, label retune-full); untuned first pass: <X>/18, <x>/21, <Y>/15 (see §Retune)
```

### 8. The measured surface

The measured snapshot S is batch 7 (49-01, 49-02, 49-03 on top of the Phase-48 head `3a9c819`).
After S is cut, only `plugins/vibe-check/.claude-plugin/plugin.json`'s version line and files
under `plugins/vibe-check/docs/**` may change before release. Any other change to the plugin is
disclosed in the body below, with its effect on the measurement.

---

## Headline

**MISS** — false alarms 3→5 of 18 (corrected cohort, bar ≤ 3; should-quiet-7 excluded per SUPERSESSIONS-v2.10.md #001); catches 15→15 of 15 (bar 15) (no rounding — exact fractions).
Sealed literal (never deciding): false alarms 6→8 of 21 vs the sealed bar ≤ 6 — would be MISS; should-quiet-7 fired 3/3 (reported descriptively — it contains a real config-loss defect, #001)
Retune: not used (owner declined the diagnosed fix; see §Changes made after measurement)

**The release candidate missed the pre-registered bar, and 2.11.0 ships anyway by owner
decision.** On the corrected cohort the tool raised a false alarm on 5/18 clean runs against a bar
of ≤ 3; it kept every catch, 15/15. The sealed literal over all 21 quiet runs was 8/21 (bar ≤ 6,
never deciding). The miss is on the false-alarm arm only: should-quiet-6 fired 3/3 (the
pre-registered expected residual, which alone uses the whole budget), plus one new single-run
alarm each on should-quiet-3 (run 1) and should-quiet-4 (run 2). The one allowed retune was
diagnosed and scoped but declined by the owner, so there is no S2, no retune run and no
`retune/VERDICT.json`. The owner's release decision is committed in
`docs/design/b3-ground-truth/RUN-METHOD-NOTES-phase49.md` §Retune, verbatim:

    retune: declined by owner (fix-class PROMPT, 2026-10-07T12:41:00-0400; first-pass verdict MISS stands)
    ship-decision: ship-as-measured (owner, 2026-10-07T12:41:11-0400, verdict of record MISS 5/18 15/15)

There is no `ship-revert:` line, because no fix was made.

Every number in this section is transcribed from the artifact of record,
`docs/design/b3-ground-truth/runs-v2.11-phase49/first/VERDICT.json` (label `first`, verdict `MISS`,
`quiet_fraction` 5/18, `catch_fraction` 15/15, sealed literal 8/21), committed in `14fded8` before
any retune decision. Nothing is re-derived here. `score43.py headline-check --profile phase49`
checks this block against that artifact.

## What was measured

- **The measured system.** The v2.11 release candidate (Phases 45–48 plus 49-01..49-03) frozen in
  snapshot S = `e6eafbd3b8c4242064997f82fad5edd058d65a1c` (batch 7). Sessions loaded the snapshot
  with `--plugin-dir`. Install-cache parity against S was 134/134 forward with 0 reverse extras in
  both sittings, and the released 2.10.0 cache was restored after each sitting.
- **The harness tuple, identical for all 36 runs and identical to Phase 43.** Claude Code 2.1.281,
  codex-cli 0.153.4, codex companion 1.0.4, model EXACT `fable 5.1`, 1M context window, auto-update
  frozen for the window. Each run is bound to one of 14 committed fingerprint blocks in
  `RUN-METHOD-NOTES-phase49.md` (12 diff sessions plus 2 relaunches).
- **The runs.** 36 `/vibe-check:deep-review` runs (12 sealed diffs × 3), all on S, over two
  sittings. The ledger is complete (`12 diffs x 3`, no holes, no extras). 0 runs were voided. Two
  attempts failed before any review began and were redone in the same slot
  (should-quiet-2 run 2, should-quiet-3 run 1): each stopped at an unplanned first-run `Migration`
  card (a pre-existing 2.10.0 misfire), with nothing answered and no state written. Both are
  archived as `*.failed-*` siblings with a committed `reason.txt` and are not scored.
- **Who drove them.** Assistant-driven via tmux. Each measured session was a separate `claude`
  process with its own context. The driving session sent only the fixed keystroke set (launch line,
  `/clear`, `/vibe-check:deep-review`, the fix-loop `Stop here…` and `Abandon` options selected by
  label, `/exit`) and never fed findings. The `post` check printed `driver contamination: none` on
  every run.
- **Codex.** Codex `joined` on 36/36 runs. Dropouts: 0 on every diff.
- **New measured surface vs Phase 43.** This is the first B3 measurement with the 2.11 git-safety
  layer active: the review-agent git guard (a PreToolUse hook) and the before/after git-state
  fingerprint that halts a pass if the repo changed. Across the 36 runs it recorded 0 guard blocks
  and 0 halts. It also includes the 2.11 lane gating, carry-forward integrity and pause-batching
  changes.

## Per-diff results

Transcribed from `first/VERDICT.json` `per_diff`. Quiet diffs report runs that fired; catch diffs
report runs that caught.

| diff | role | result | Codex | dropouts |
|---|---|---|---|---|
| should-quiet-1 | quiet | fired 0/3 | joined 3/3 | 0 |
| should-quiet-2 | quiet | fired 0/3 | joined 3/3 | 0 |
| should-quiet-3 | quiet | fired 1/3 | joined 3/3 | 0 |
| should-quiet-4 | quiet | fired 1/3 | joined 3/3 | 0 |
| should-quiet-5 | quiet | fired 0/3 | joined 3/3 | 0 |
| should-quiet-6 | quiet | fired 3/3 | joined 3/3 | 0 |
| should-quiet-7 | quiet (excluded, #001) | fired 3/3 | joined 3/3 | 0 |
| third-organic-should-catch | catch | caught 3/3 | joined 3/3 | 0 |
| triggarr-autoescape | catch | caught 3/3 | joined 3/3 | 0 |
| triggarr-secret-in-logs | catch | caught 3/3 | joined 3/3 | 0 |
| triggarr-session-rotation | catch | caught 3/3 | joined 3/3 | 0 |
| triggarr-settings-form-split | catch | caught 3/3 | joined 3/3 | 0 |

The fired runs: should-quiet-6 runs 1–3 (Codex-led critical rows on a declared-but-not-yet-read
setting, backlog class 999.19 (a), the pre-registered residual); should-quiet-3 run 1 (a
language-python warning just outside the hunk); should-quiet-4 run 2 (a single-lane security
warning inside the hunk, backlog class 999.19 (b)). Details: `SCORING-v2.11-phase49.md` §4–§6.

## Decision cards per firing (REL-02)

Counted with the pre-registered counter, `plugins/vibe-check/scripts/count_cards.py tally`, over
the local transcripts. Each transcript was first checked against its committed
`transcript.jsonl.sha256`: **36/36 matched, 0 mismatched, 0 missing** (the two failed-attempt
siblings are not scored runs and carry no sha file). The counter prints counts only.

| window | firings | fix-loop firings (≥ 1 card) | cards | cards per fix-loop firing | cards per firing |
|---|---|---|---|---|---|
| **v2.11, Phase 49 first pass on S (the shipped build)** | 36 | 24 | 48 | 48/24 (2.00) | 48/36 (1.33) |
| v2.10, Phase 43 first pass (same counter, recount) | 36 | 26 | 52 | 52/26 (2.00) | 52/36 (1.44) |
| v2.10, Phase 43 retune (same counter, recount) | 9 | 9 | 18 | 18/9 (2.00) | 18/9 (2.00) |

Per-run histogram, Phase 49: 24 runs with 2 cards, 12 runs with 0 cards, none with any other
count. The Phase-43 recount reproduces the pre-registered baseline exactly (52/26 and 18/9; 70
cards over 35 fix-loop firings and 45 runs combined).

- **Like-for-like (same harness, same decline path):** 2.00 cards per fix-loop firing on v2.11
  vs 2.00 on Phase 43. This is the expected value: on the B3 decline path a fix-loop firing shows
  exactly the "Pass N" card and the "Stop here" card, by the card budget in `50-fix-loop.md`. B3
  therefore cannot show a pause saving on this path; it shows that the new cards added no pauses.
  Cards per firing overall fell from 52/36 to 48/36 only because two fewer runs reached the fix
  loop.
- **Cited baseline:** 5.5 cards per firing, the gate-log figure (all time, as of 2026-09-30) from
  the v2.11 roadmap spec. It is not comparable: those are GSD phase-mode multi-pass firings
  (apply / rerun / finalize), a path B3 does not exercise.

Gate-log 2.11.0 firings: unavailable at release (every v2.11 gate-log deep-review ran the 2.10.0 build).

Nothing here is inferred from pass counts.

### Changes made after measurement (disclosed)

- **Measured surface:** `git log S..HEAD -- plugins/vibe-check ':!plugins/vibe-check/docs'` is
  empty at the release commits, apart from the 2.11.0 version bump in
  `plugins/vibe-check/.claude-plugin/plugin.json` (version line only). The six behavioural
  directories (`agents`, `commands`, `phases`, `templates`, `scripts`, `hooks`) are byte-identical
  between S and the release commit (`git diff --quiet S HEAD` over those six paths exits 0). The
  shipped 2.11.0 is the measured build.
- **The declined fix.** 49-07 diagnosed the miss and scoped one PROMPT-class fix: a calibration
  rule in `templates/codex-focus.txt` for settings that are declared but not yet read (backlog
  class 999.19 (a), aimed at the should-quiet-6 residual). It is recorded in
  `runs-v2.11-phase49/retune/FIX-SCOPE.json` and `SCORING-v2.11-phase49.md` §6. The owner declined
  it, so it was never written, built or measured, and nothing in the shipped plugin comes from it.
  The diagnosis found no v2.11 code path implicated: the two new alarms are lane sampling of
  pre-existing behaviour.
- **After this commit:** if the release gates force any change to the six behavioural directories,
  publication is blocked. It is never a disclosure-only pass: either the final tree is re-measured
  (and this verdict then binds to the new snapshot), or the owner records a release waiver and this
  document then states that the release itself is not B3-measured.

## Honest limitations

1. **The bar was missed.** 5/18 false alarms against ≤ 3. 2.11.0 ships on an owner decision, not
   on a PASS.
2. **Small N.** 12 diffs, 36 runs. One run moves a diff by 1/3. The false-alarm arm had zero
   headroom by pre-registration (should-quiet-6's expected 3/3 used the whole budget), so any one
   new alarm was a miss, and two appeared.
3. **Not a held-out set.** These are the same 12 diffs Phases 40–43 were tuned against.
4. **The A4 basis.** The live check that the git guard reaches the installed build's review
   sub-agents (A4) ran on the installed 2.10.0 cache during the 49-04 dress rehearsal, not inside
   the measured window, where the snapshot was loaded with `--plugin-dir`.
5. **The gate reviewer is still 2.10.0.** Every v2.11 orchestrator gate-log deep-review ran the
   2.10.0 build, so there is no real-use 2.11.0 card figure yet.
6. **Self-scored AXIS.** Catch calls are the assistant's hand judgements on the pre-registered
   title/member-title basis, recorded before any aggregate. The autoescape calls are
   basis-sensitive: a stricter reading gives 12/15. That does not change the verdict, which the
   false-alarm arm already decides.
7. **Three repos, all the owner's.** This measures these defect classes on this stack, not recall
   in general.

## Plain-language summary (for the owner)

**2.11 missed its target, and it ships anyway because you decided it should.** We ran the same
twelve sealed diffs three times each on the finished 2.11 build. It caught every real defect,
15 of 15. On the clean diffs it raised a false alarm in 5 of 18 runs; the target was at most 3.
Three of those five are the one known weak spot we predicted before running anything (a setting
that is declared but not used yet, which the Codex reviewer keeps calling a bug). The other two are
one-off alarms on two different diffs, each in one run out of three.

We found a likely fix for the known weak spot, but you chose not to apply it, so 2.11.0 is exactly
the build we measured. Nothing in the reviewer changed after the measurement except the version
number.

On pauses: when a review reaches the fix loop and you decline, you still see exactly two decision
cards, the same as in 2.10. The new pause batching did not add any. The bigger saving it was built
for (fewer cards across multi-pass phase reviews) cannot be measured by this test, and no real
2.11.0 reviews exist yet to count.
