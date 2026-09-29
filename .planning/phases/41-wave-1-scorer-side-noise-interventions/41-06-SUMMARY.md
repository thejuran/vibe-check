---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 06
status: complete
subsystem: scorer
tags: [h-lane, scorer-04, d-01, d-03, d-14, d-09, d-10, d-16, replay-guardrail]
requires: ["41-04 B-SEV (c02d9b1)", "41-05 B-REWEIGHT (0ee3818)", "41-02 replay.py + load_scorer blob:", "41-01 SUPERSESSIONS 007 (member titles satisfy AXIS)"]
provides:
  - "score.py: proximity-only cross_confirm_group, D-01 +10 via _codex_corroborated, per-member _effective_band, `members` on survivors (MEMBER_KEYS / _MEMBER_EXCLUDED_KEYS), _canonical_for_hash, _finding_identity, _member_ref, _expand_members"
  - "fixtures/future-schema.json finding_optional += members (state_shape allowance) + rollback note"
  - "phases/review/30-collect-score.md step 0: per-member HEAD read (canonical_line_content + canonical_window)"
  - "templates/output-format.md {{members_list}}; templates/scoring.md line 18 (D-01) + Site grouping block + Freeze lift paragraph"
  - "docs/design/b3-ground-truth/REPLAY-REPORT-phase41-h-lane.md (ALONE) and REPLAY-REPORT-phase41-combined.md (COMBINED, the D-10 evidence)"
  - ".planning/phases/41-wave-1-scorer-side-noise-interventions/41-deferred-items.md (Phase-42 prose carry, Phase-43 envelopes, BashOutput)"
affects: [41-07 runbook (spot-check picks, PLAN-COMMITS.json batch 4), Phase 42 prompt-only wave (agent cross-confirm prose), Phase 43 measurement]
tech-stack:
  added: []
  patterns: ["one mechanism for carry-forward of collapsed rows: expand every carried row into member findings before scoring", "lane-aware occurrence identity (agent, stable_hash, line) for member dedup; stable_hash itself frozen", "per-member band adjustments before representative selection"]
key-files:
  created:
    - docs/design/b3-ground-truth/REPLAY-REPORT-phase41-h-lane.md
    - docs/design/b3-ground-truth/REPLAY-REPORT-phase41-combined.md
    - .planning/phases/41-wave-1-scorer-side-noise-interventions/41-deferred-items.md
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/scripts/test_state_shape.py
    - plugins/vibe-check/scripts/fixtures/future-schema.json
    - plugins/vibe-check/templates/output-format.md
    - plugins/vibe-check/templates/scoring.md
    - plugins/vibe-check/phases/review/30-collect-score.md
decisions:
  - "H-LANE groups by site only (same file, ±2 lines) across all lanes; category never affects grouping; CATEGORY_DOMAIN and the codex STEP-B bridge are removed (twin remapping moot)"
  - "The +10 fires only for a Codex member + a Claude-lane member with envelope codex.status == joined (D-01); Claude<->Claude agreement earns nothing"
  - "Representative sort key is (effective band, capped score, UNCAPPED score, stable_hash, agent); the uncapped key keeps 41-04's never-drop-by-ceiling guarantee when the lone-lane cap equalizes members"
  - "D-10/D-16 spot-check picks from the COMBINED replay: should-quiet-3 and should-quiet-1; predicted FP over their 6 runs = 5/6"
metrics:
  duration: "~18 min"
  completed: 2026-09-29
  tasks: "3/3"
  files: 10
---

# Phase 41 Plan 06: H-LANE site grouping — Summary

Findings from different lanes at the same site (same file, within ±2 lines) now collapse into one
row, whatever their categories. The row lists every lane in `attribution` and keeps each lane's
own finding record in `members`, which the report renders as "flagged by: agent — title; …". The
+10 bonus now fires only when a Codex finding and a Claude finding share a site and the
orchestrator's `codex` block says Codex joined. On a later pass every collapsed row is expanded
back into its members, so an absorbed defect whose own line is still there is not lost when its
lead is fixed, silenced or falls below the threshold. Both replays kept all protected catches:
**H-LANE ALONE: REGRESSED 0, FP 16/18 → 16/18. COMBINED Wave 1: REGRESSED 0, FP 16/18 → 14/18.**

## Commits

| Task | Commit | What |
|---|---|---|
| 1 + 2 + 3 (one commit, D-09 revert unit) | `ccf69fc` | score.py, test_score.py, test_state_shape.py, future-schema.json, output-format.md, scoring.md, 30-collect-score.md, both replay reports, 41-deferred-items.md |

**H-LANE commit sha for 41-07's PLAN-COMMITS.json: `ccf69fcd90ec484c8f4c24a78d64c4b2d9366bfb`.**
The scorer, the `members` schema allowance, the state_shape lock and the step-0 member HEAD-read
paragraph are in this one sha, so batch 4 reverts all of them together (checked:
`git show --stat HEAD -- plugins/vibe-check` lists all seven plugin files).

## Replays (observed; both `replay.py candidate` runs exited 0)

Both report headers show scorer sha256
`11303a24a5f4091a5aeb8c6d6b0559bd958560fd0ace4dc0a8fd57bc24ed05ff`, which equals
`git show HEAD:plugins/vibe-check/scripts/score.py | shasum -a 256`. Baseline:
`blob: b21f7f3d…`.

**H-LANE ALONE** (`overrides: {"AGENT_CONFIDENCE_OFFSET": {}, "LONE_LANE_BAND_CEILING": null}`):
- `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1` (ledger 008, unchanged)
- Guardrail: `kept 25 / protected 26 · REGRESSED 0 · UNEVALUABLE 0`; 8 `member-title` guardrail rows
- Headline FP **16/18 → 16/18** (the plan expected this: fewer rows, same runs firing). Phase-40
  sq5 **0/6 → 0/6**. v2.9 quiet **6/9 → 6/9**.

**COMBINED** (`overrides: {}`; B-SEV + B-REWEIGHT + H-LANE):
- `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`
- Guardrail: `kept 25 / protected 26 · REGRESSED 0 · UNEVALUABLE 0`. `member-title` is the basis
  on 8 guardrail rows (the D-14 mechanism at work). 7 are kept catches: phase40 secret-in-logs
  run-1/2, third-organic run-1, autoescape v2.10 run-2/3, session-rotation run-1, v2.9
  autoescape run-2. The 8th is the AMENDED ledger-008 run, `runs/triggarr-secret-in-logs/run-2`.
  The H-LANE ALONE report also has 8 `member-title` guardrail rows.
  Most kept catches are critical/100. `runs/triggarr-secret-in-logs/run-1,3` are warning/94,
  which still clears the floor.
- Headline FP **16/18 → 14/18**. Phase-40 sq5 **0/6 → 0/6**. v2.9 quiet **6/9 → 6/9**. sq7
  (informational) **3/3 → 3/3**.

**Firing rows** (counted from each report's "Rows that fire" section):

| report | all firing rows | headline set (sq1-6) rows |
|---|---|---|
| B-SEV alone (= baseline firing set) | 84 | 51 |
| B-REWEIGHT alone | 60 | 32 |
| H-LANE alone | 55 | 34 |
| COMBINED | 35 | 18 |

## D-10 / D-16 spot-check ranking (from the COMBINED report)

Rule (CALIBRATION-v2.10.md § D-16): movement = baseline fired runs minus combined fired runs over
each diff's Phase-38 triplet. A diff already quiet post-diet is skipped (should-quiet-5), sq7 is
ineligible, and ties go to the lower diff number.

| diff | baseline fired | combined fired | movement | eligible? |
|---|---|---|---|---|
| should-quiet-1 | 3/3 | 3/3 | 0 | yes |
| should-quiet-2 | 3/3 | 3/3 | 0 | yes |
| should-quiet-3 | 3/3 | 2/3 | **1** | yes |
| should-quiet-4 | 3/3 | 3/3 | 0 | yes |
| should-quiet-5 | 1/3 | 0/3 | 1 | **no**, already quiet post-diet (0/3 Phase-40 final) |
| should-quiet-6 | 3/3 | 3/3 | 0 | yes (codex-driven; the replay agrees Wave 1 does not move it) |
| should-quiet-7 | — | — | — | no (ledger 001) |

**Picks: should-quiet-3 (movement 1) and should-quiet-1 (0-movement tie goes to the lower
number). Predicted FP over their 6 runs: 2 + 3 = 5/6.**

## Verification (observed)

- Task 1 `<verify>` chain (extracted from the plan and run as a script): exit 0. It printed
  `H-LANE SMOKE OK` and `IDIOM-CAP-NO-LEAK + FORGED-MEMBERS-STRIPPED + EXPANSION OK`. That run
  covers all 6 permutations, the idiom/security cap under the default and `low` floors, the
  forged-members strip, fixed/silenced lead expansion, the pass-4/5/6 identity cases with their
  mutation proofs, and the window case.
- AC grep counts: domain names 0; `def _titles_match` 1; `"status", "members"` 1;
  `_cap_idiom_band(survivor` 0; `_expand_members|_effective_band` defs 2; `_prior_members|
  _promote_members` 0; `^MEMBER_KEYS = ` 1; `^_MEMBER_EXCLUDED_KEYS = ` 1;
  `_canonical_for_hash|_finding_identity` defs 2; `_finding_identity` uses 6; `^import` 4.
- scoring.md: `diff` of lines 1-64 against HEAD~ shows only line 18 changed; line 18 contains
  `D-01`. All `scoring.md:NN` citations in score.py were re-checked; `:86` still points at the
  B-REWEIGHT offset line.
- 30-collect-score.md: insert only (0 removed lines); 05-state.md and archive-compat-schema.json
  untouched.
- Task 2 `<verify>` chain: printed `H-LANE-TESTS-OK`. `test_score.py + test_state_shape.py`:
  368 passed. `TestMembersAcrossPasses`: 17 passed. `v2.10 Wave 1 H-LANE (D-03)` reason
  comments: 9.
- Task 3 `<verify>` chain: printed `H-LANE-LANDED`. `test_replay.py -k Ordering`: 1 passed,
  4 subtests (four reports).
- Full suite `pytest plugins/vibe-check/scripts -q` after the commit: **1116 passed, 1123
  subtests, 0 failed**. The `GOLDEN_DIGEST` line is not in the diff.
- `git diff HEAD~1 --stat -- plugins/vibe-check/agents` is empty. Sealed roots (`runs`,
  `runs-v2.10`, `runs-v2.10-phase40`, PREREGISTRATION-v2.10.md) are unchanged.
- `PRE_HLANE_SCORER_BLOB = 0f6852ad24a199ee1a556d5595d7f69ce64663cc` equals
  `git rev-parse 0ee3818:plugins/vibe-check/scripts/score.py`. `git cat-file -e` resolves it.
  `TestRollbackStateCompat` and the three expansion tests load it through
  `replay.load_scorer("blob:…")` in `setUpClass`, so a load failure is a test error, not a skip.
- **Mutation proofs against score.py** (each applied to a copy, the targeted classes run with
  `-x`, then restored; `cmp` confirmed the restore):

  | mutation | result |
  |---|---|
  | drop the uncapped tie-break key | 1 failed |
  | `(agent, title)` member dedup | 2 failed |
  | drop the agent tie-break | 1 failed |
  | +10 back on `len(attribution) >= 2` | 1 failed |
  | idiom cap keyed on the representative | 1 failed |
  | window dropped in `_expand_members` | 1 failed |
  | member carried without a HEAD read | 1 failed |
  | category-gated grouping | 1 failed |
  | ingress `members` strip removed | 0 failed at first (see deviation 3), 1 failed after the new lock |

## Re-pinned and retired tests

- **Retired** (STEP B and CATEGORY_DOMAIN removed, so the async-discipline / input-validation
  twin remapping is moot): `TestCategoriesOverlap` (whole class),
  `test_ambiguous_multi_domain_adversarial_bridges_nothing`,
  `test_second_adversarial_does_not_relay_via_first_every_ordering`,
  `test_single_domain_two_components_adversarial_deterministic`.
- **Re-pinned to one site** (each with the `# v2.10 Wave 1 H-LANE (D-03)` reason comment):
  - `test_different_domain_co_located_is_one_site`
  - `test_identical_title_different_domain_one_site_no_plus_ten`, which also asserts no +10
  - `test_missing_category_co_located_groups_by_site`
  - `test_unknown_category_co_located_groups_by_site`
- **`test_single_co_located_domain_adversarial_bridges_every_ordering`:** the survivor is now B
  (Codex), not A. Band, score and stable_hash all tie, and the new agent tie-break decides.
  A rides on the row as a member.
- **`TestRunMinConfidence.test_dropped_neighbor_supplies_no_cross_confirm`:** the twin is now a
  Codex lane with a `codex: joined` block. A Claude twin could no longer supply +10 at all, which
  would make the test vacuous.
- **`TestAgentConfidenceOffset.test_unverified_codex_pair_is_lone_and_offset`:** native conf
  60 → 70. Without the block the pair no longer gets +10, and at 60 the row would fall below the
  deep-review cutoff.
- **`TestMalformedInputMatrix`:** the "keep" probe sibling moved to its own site (`src/keep.py`).
  The malformed neighbours sit at the same file:line, and under H-LANE the probe would be
  absorbed rather than surviving as its own row.
- **`TestSuppressionFinding`:** `test_suppression_category_maps_to_no_domain` became
  `…_never_joins_a_site_row`.
- **`TestTieBreakDeterministic._two_tied`:** comment fixed (no +10 for Claude↔Claude).
- **`TestAbsorbedMembersRecorded`:** now asserts `members` titles, plus a new cross-domain
  (injection + perf) case.

## Deviations from Plan

1. **[Rule 1 - Bug] The representative sort key gained an uncapped-score key:
   `(-band, -capped, -uncapped, stable_hash, agent)`.**
   - **Found during:** Task 1.
   - **Issue:** the plan's key `(-band, -capped, stable_hash, agent)` breaks a 41-04 guarantee.
     With a config-tuned critical floor below the /review cutoff (for example critical 75, so the
     cap is 74), members at raw 85 and 78 both cap to 74. The hash can then pick the 78 member.
     The finalize cutoff judges the representative's uncapped score, so 78 < 80 drops the whole
     row. 41-04 guarantees the ceiling never drops a finding.
   - **Fix:** the uncapped score breaks capped ties before the hash does. The key is still
     arrival-independent. It is unchanged for every plan test (those ties are at raw 100, so the
     agent still decides the pass-6 case).
   - **Lock:** `test_capped_tie_keeps_highest_uncapped_leading` (mutation: 1 failed).
   - **Commit:** ccf69fc.
2. **[Plan structure] One commit instead of per-task commits.** The plan's Task 3 step 4 names
   ONE commit carrying every file (the batch-4 revert unit), and says not to commit score.py
   unless the replays pass. This follows the 41-04 and 41-05 precedent.
3. **[Rule 2 - decorative-guard fix] The ingress `members` strip had no output-visible lock.**
   - **Issue:** removing the strip still passed every test, because the group loop always
     overwrites `members`. The strip is defense in depth.
   - **Fix:** added `test_working_findings_never_carry_members`. It spies on
     `cross_confirm_group`'s input and asserts that no working finding (fresh or carried) carries
     `members`. It fails with the strip removed and passes on the real code.
4. **[Rule 3] `TestMalformedInputMatrix` probe relocation** (see Re-pinned). The co-located
   fixtures had depended on the retired "unknown category never groups" rule.
5. **[Scope carry] `phases/deep-review/30-codex-collect.md` lines 6 and 46** still describe the
   category-domain +10 and "no Codex special-casing". These lines are outside this plan's file
   list, so they were recorded in 41-deferred-items.md and not edited. The same applies to the
   agent prompts (T-41-30).
6. **[AC wording] `| {{agents_csv}} |` table rows:** the plan says "all three tables". The file
   has two such table rows plus the "[same table …]" reference for the Warning/Medium sections.
   None were changed.

## Assumption Drift (advisory)

- **Found during:** Task 3.
- **Planned:** COMBINED FP **16/18 → 12/18**, rows 51 → 34 (research, indicative).
- **Actual:** COMBINED FP **16/18 → 14/18**, which is the same as B-REWEIGHT alone. Headline-set
  rows went 51 → 18 (all firing rows 84 → 35). H-LANE collapses rows much harder than predicted,
  but no additional run goes quiet.
- **Why:** the 12/18 prediction came from research's larger indicative offsets (impact −18,
  architecture −11). 41-05 recorded that the committed derivation gives smaller offsets. H-LANE
  merges rows within a run; it does not remove a run's last firing row. Recorded as observed per
  D-08; nothing was retuned.

## Known Stubs

None.

## Threat model

- T-41-25 (T1 +10 spoof): `_codex_corroborated`, tested with and without the block
  (`test_codex_plus_claude_plus_ten_*`).
- T-41-26 (order dependence): union-find, the permutation test, and the greedy counter-example.
- T-41-28 (non-str member fields): `_member_ref` coercion, locked by the crash-row test.
- T-41-29 (`stable_hash` input): `test_members_never_feed_stable_hash`; archive-compat untouched.
- T-41-30 (agent prompts): untouched; carry recorded.
- T-41-32 (forged members): ingress strip plus the new working-set lock.
- T-41-33 (idiom cap leak): tested under the default floor and `low`, with the mutation proof.
- T-41-37 (member without a HEAD read): fail closed, `test_promotion_requires_orchestrator_head_read`.
- T-41-38 (rollback): `TestRollbackStateCompat` against the real pre-H-LANE blob.
- T-41-39 (a lead's fate dropping its members): silenced and sub-threshold tests, each with the
  stubbed-helper and blob mutation proofs.
- T-41-40 (identity collapse): the pass-4/5/6 tests with their mutation proofs.
- T-41-41 (one-line projection): the window test with its two mutation proofs.

No new threat surface outside the register.

## Self-Check: PASSED

- FOUND: docs/design/b3-ground-truth/REPLAY-REPORT-phase41-h-lane.md
- FOUND: docs/design/b3-ground-truth/REPLAY-REPORT-phase41-combined.md
- FOUND: .planning/phases/41-wave-1-scorer-side-noise-interventions/41-deferred-items.md
- FOUND: commit ccf69fc (feat(41-06))
