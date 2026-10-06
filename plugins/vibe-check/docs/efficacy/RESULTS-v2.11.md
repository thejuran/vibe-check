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
