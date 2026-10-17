# R4 — Before/after outcomes for the v2.12 freeze candidate

Requirement: FRZ-01 / R4 (D-05, D-06, D-07, D-19, D-27). Built in 54-10; the live-check rows and the owner decision are completed in 54-11.

This is the 54-10 re-run on candidate `24c0c00038f2`. The first 54-10 run used candidate `302df48e1097`. That candidate was superseded when the 54-11 live sweep found the `.in_use` identity-check defect, which was fixed in commit 24c0c00 (D-23). The superseded table is kept unchanged in `evidence/superseded-302df48e1097/R4-BEFORE-AFTER.md`.

## Candidate

- candidate: `24c0c00038f2d15af4b55f178ea44e680c1f2c58` (from `evidence/CANDIDATE.json`, selected once by the 54-10 re-run; the superseded `302df48e1097…` selection is recorded in the same file)
- PATH-MAP blob at candidate: `027bb8567327f78e09cf708e3a7458c22bf982a7` (unchanged from 302df48)
- candidate guard (once the replay report commit sequence started):
  `CANDIDATE OK candidate=24c0c00038f2d15af4b55f178ea44e680c1f2c58 head=964b40201eb28eb81d4107b17e0b8fd4a0f216ff descendant_commits=2 (reporting-only)`
- scorer base for the complete-output diff: `rev:ebcd3e4` (Phase 53 FINAL_HEAD; score.py sha256 525c5e83…)
- candidate score.py sha256: ea6b041779c626b40607d4ba65ee0cc1c9522d2bd0c7cdd8995be4969768c233. This is the same file as at 302df48 (git blob b9a1e900 at both commits). The 302df48 → 24c0c00 change touches only freeze-kit files, and `git diff 302df48 24c0c00 -- plugins/` is empty.
- supersedes the Phase 53 dev-rehearsal fingerprint `5bee4c11…`

## Replay guard

Report: `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-guardrail.md`
(`replay.py candidate --name phase54-freeze --scorer rev:24c0c00038f2d15af4b55f178ea44e680c1f2c58`; exit 0)

| measure | value |
|---|---|
| protected catch runs | 26 |
| kept | 25 |
| amended (existing ledger entry 008) | 1 |
| regressed | 0 |
| unevaluable | 0 |
| baseline reproduction | REPRODUCED 25 / 26, AMENDED 1, UNEVALUABLE 0 |

No lost protected catch, so no blocking section is needed. The report body matches the superseded 302df48 report byte for byte, apart from the candidate, HEAD and timestamp lines.

## Complete-output diff

Report: `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md` (+ `.changes.json`)
(`replay.py diff --base rev:ebcd3e4 --scorer rev:24c0c00038f2… --roots all --allow docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json`; exit 0)

| measure | value |
|---|---|
| roots | 7 (all DIFF_ROOTS, including `runs-phase53-dev/final`) |
| runs compared | 170 (= `len(replay.iter_runs(roots=DIFF_ROOTS))`; 16 of them are the signed-off dev rehearsal runs) |
| runs differing | 0 |
| runs differing (allowed) | 0 |
| runs with unallowed differences | 0 |
| allowances unused | 65 (expected: the Phase 53 NV allowances describe changes between the v2.10 baseline and ebcd3e4; ebcd3e4 is now the base, so none of them is exercised) |

No allowances were added.

## Before/after

**Archived replay: no changed outcomes.** Re-scoring all 170 archived and signed-off rehearsal runs through the candidate scorer gives output byte-identical to the Phase 53 final scorer (ebcd3e4). `.changes.json` lists no entries (`"allow": []`), so replay contributes zero rows.

**Live rehearsal (54-11, one run per case on 24c0c00): 8 changed outcomes, one row each below.** Before = the Phase-53 signed-off final run (fingerprint `5bee4c11…`); after = the live run on candidate 24c0c00 (fingerprint `c046f0cf…`, manifest `98af8754…`). Per-run detail and the investigation are in `docs/design/reachability-dev/NOTES-phase54-live.md` (`## Per case`, `## Changed quiet-shaped outcomes`, `## Lost catch investigation`).

**Cause, for every live row:** no difference attributable to Phase 54 was demonstrated; identical re-scoring rules out scorer effects, but the runtime schema-wording change (agent-output-schema.md) is not isolated from lane behavior. All 16 live runs were re-scored through both the Phase-53 scorer and the candidate scorer: 0 of 16 differ, which rules out the R1 scorer change. No lane wrote a placeholder NV value, so the R1 rule had nothing to act on. The schema sentence is part of the prompt every lane reads, and one run per case cannot separate its influence on what the lanes wrote from run-to-run variation. Finalize routing (R2) runs only at close-out, which no measured run reaches. Each row is the owner's decision.

**Burden (owner correction, 2026-10-16):** This rehearsal shows no owner-burden improvement (owner questions 24 → 24; headline quiet cases alarmed 3/6 vs 1/6) and a substantial risk of missing Phase 55's false-alarm target (≤3/18). should-quiet-2 stays counted as a fire on a should-quiet case; its pre-existing nature earns no exemption.

| Run | Finding (file:line, stable_hash short) | Before | After | Cause (54-NN change) | Severity effect | Alarm status effect (fires/quiet) | Catch credit effect | Owner burden effect (cards/NV items) |
|---|---|---|---|---|---|---|---|---|
| live/should-quiet-2/run-1 (should-quiet) | rest.service.ts:59, f2c7d4d9ed83 (bugs, NV): saving settings fails because `ConfigService.set` still sends GET to a POST-only route | quiet: 0 alarms, 0 NV | 0 alarms, 1 NV | no difference attributable to Phase 54 demonstrated (see above). The NV fields are concrete. The item describes a GET/POST mismatch already present at the case base `84aff27`, which the diff does not touch | none (NV band, no alarm) | quiet -> **fires** (a should-quiet fail; first fire on this case: Phase 49 0/3, Phase 53 quiet) | none | NV items +1; cards 2 -> 2 |
| live/should-quiet-6/run-1 (should-quiet) | models/config.py:139, 5646e628420f (codex-adversarial warning 94): new timeout field has no consumer | quiet: 0 alarms, 0 NV, no card | 1 alarm, 0 NV | no difference attributable to Phase 54 demonstrated (see above). The Phase-53 targeted run on the signed-off build fired the same way (codex critical + bugs NV) | new warning row | quiet -> **fires** (Phase 49 3/3; Phase 53 targeted fired, final quiet) | none | alarms +1; cards 0 -> 2 |
| live/should-quiet-7/run-1 (should-quiet, excluded #001) | routes.py:550, fcc0b38c0558 (bugs, NV): saved timeout has no consumer | 1 alarm, 0 NV | 1 alarm, 1 NV | no difference attributable to Phase 54 demonstrated (see above) | none (alarm row unchanged: settings-save overwrite, critical 100) | fires -> fires (exclusion retained) | none | NV items +1; cards 2 -> 2 |
| live/should-quiet-4/run-1 (should-quiet, known residual) | models/config.py:108, edb7d2b25e80 (bugs, NV) — before: b04b099a1960 (bugs) + 5ded17410c7d (impact) | 1 alarm, 2 NV | 1 alarm, 1 NV | no difference attributable to Phase 54 demonstrated (see above). The two legacy-value NV items now arrive as one item naming both shapes | none (numeric-host bypass alarm unchanged, codex warning 94) | fires -> fires | none | NV items -1; cards 2 -> 2 |
| live/reach-unchanged-1/run-1 (dev quiet) | _filter_overrides.py:73, b1c765a372c6 (codex-adversarial critical 100) — before: 2dab2c1b1e61 (bugs critical) + fe03e1c9ca8c (architecture warning, test import) | 2 alarms | 1 alarm | no difference attributable to Phase 54 demonstrated (see above). It is the same key-correction defect (deleted `parse_optional_int` still imported by the tests), now one merged row | the warning row is gone; critical stays | fires -> fires (quiet expectation retained) | none | alarms -1; cards 2 -> 2 |
| live/reach-new-1/run-1 (dev catch) | routes.py:1617, 53b1a7cd70a4 (codex-adversarial warning 94): "The newly exposed recovery flow has no token consumer" | 4 alarms | 5 alarms | no difference attributable to Phase 54 demonstrated (see above) | new warning row, off the keyed defect | fires -> fires | none (catch kept: 1307c74d1331, critical 100, routes.py:1689) | alarms +1; cards 2 -> 2 |
| live/triggarr-secret-in-logs/run-1 (B3 catch) | base.py:252, 0dbc67cd110e (architecture) — before: 021700bd8847: raw pydantic ValidationError logged | warning 91 | critical 100 | no difference attributable to Phase 54 demonstrated (see above) | warning -> critical on the non-credited row | fires -> fires | none (catch kept: 7867fa5685ed, critical 100, base.py:233) | none (alarms 2 -> 2) |
| live/should-quiet-1/run-1 (should-quiet) | no row (the card listed sub-Warning rows) | quiet; fix-loop card shown (2 cards) | quiet; clean review, no card | no difference attributable to Phase 54 demonstrated (see above) | none | quiet -> quiet | none | cards 2 -> 0 |

Phase 54 makes one scorer change, 54-01 (R1): a `needs_verification` field whose whole value is a placeholder (`n/a`, `none`, `-`) is treated as blank. It changes no archived outcome, because no archived or rehearsal lane output has a placeholder-only NV field that reaches the scorer. The rule is proven by `TestNeedsVerificationPlaceholders` in `plugins/vibe-check/scripts/test_score.py` (including the bcd15ef blank case), not by replay.

## Unchanged

- Archived replay: 170 of 170 runs are byte-identical between base and candidate (0 more fall within existing allowances).
- Live rehearsal: 8 of 16 cases are unchanged in every tracked outcome (fired/quiet, catch credit, severity band of the keyed finding, NV item count, owner questions): `reach-new-2`, `reach-unchanged-2`, `triggarr-autoescape`, `third-organic-should-catch`, `triggarr-session-rotation`, `triggarr-settings-form-split`, `should-quiet-3`, `should-quiet-5`. In all 7 catch cases the credited row has a new stable hash (a different lead lane, or another line in the keyed hunk), but it is at the same keyed site, names the same defect and is critical 100 on both sides.
- Catches: 7 of 7 kept (5 B3 + 2 development). No lost catch, no protected catch at risk.

Live totals, reported separately and never summed (R13). Before (Phase 53 final) -> after (24c0c00):
- visible alarms 17 -> 18
- Needs-verification items 2 -> 3
- owner questions 24 -> 24
- fired runs 10 -> 12
- headline quiet set (should-quiet-1..6) fired 1/6 -> 3/6

Weak co-located remarks dropped: 16 -> 12 (separate count). These are single runs, so they are not evidence of improvement or regression. Phase 55 repeats each case x3 on the frozen build.

## Live checks (54-10/54-11)

The workflow-prose changes (90-finalize.md archive routing; agent-output-schema.md placeholder sentence) are checked live, because archived-output replay covers scorer changes only (D-07).

| check | candidate | outcome | vs Phase 53 | changed? | cause |
|---|---|---|---|---|---|
| two same-day close-outs (finalize archive fences; `live-finalize-archive.md`) | 24c0c00038f2 | PASS: `REVIEW-54-<date>.md` + `-2.md`, `54.json.archived-<date>` + `-2`, `REVIEW-unstamped-<date>.md` + `-2.md`; first-pass bytes intact (all sha256 values equal the superseded 302df48 run) | Phase 53 finalize used a bare `mv` to a fixed `-<date>` name and skipped archiving a same-phase prior REVIEW.md, so a second same-day close-out lost the first report / state archive | yes (intended) | 54-02 no-clobber `review_archive.py` routing (R2) |
| fix-harness clean-tree, default-diff (`live-harness-clean-tree.md`) | 24c0c00038f2 | COMPLETE under the identity check (manifest_id 98af8754d5ae…, draft); model claude-opus-5-5[1m]; undecided_nv 0; state archived under `format-53/`; cards 1 / questions 2 / owner_commands 1 / would-be questions 2 | Phase 52 C-D COMPLETE with the same counts (no Phase 53 clean-tree run) | no | none (the outcome is unchanged; the run now goes through the 54-07 identity preflight and 54-02 archive routing) |
| fix-harness clean-tree, GSD (`live-harness-clean-tree.md`) | 24c0c00038f2 | COMPLETE under the identity check; model claude-opus-5-5[1m]; undecided_nv 0; state archived under `format-53/`; cards 1 / questions 1 / owner_commands 1 / would-be questions 1 | Phase 52 C-G COMPLETE with the same counts | no | none (as above) |

| live sweep, 16 signed-off dev cases through the B3 runner layer (`NOTES-phase54-live.md`) | 24c0c00038f2 | 16/16 runs completed, one run each; every run stamped manifest_id 98af8754… + candidate 24c0c00…; `freeze_tally.py dev-tally --manifest <draft>` exit 0, stale 0, missing 0, runs 16; no exit-4 stop | Phase 53 final sweep: 16/16 on fingerprint 5bee4c11… | outcomes: see `## Before/after` (8 rows) | — |
| B3 identity layer live, with the measured session running | 24c0c00038f2 | IDENTITY OK at `preflight`, `launch`, in-pane `session`, `pre` and `post` on all 16 cases; the 32 `pre`/`post` checks ran while the session was alive | the 302df48 attempt refused at its first `pre` (`.in_use/<pid>` markers hashed) | yes (intended) | 24c0c00 `.in_use` directory exclusion (D-23 fix) |
| schema sentence / R1 placeholder rule, live | 24c0c00038f2 | not exercised: 0 placeholder NV fields and 0 empty NV dicts across 16 transcripts; the 3 NV dicts that reached the scorer are concrete; live runs re-scored with the ebcd3e4 and 24c0c00 scorers differ in 0 of 16 | — | no | proven by `TestNeedsVerificationPlaceholders` (54-01), not live |

## Owner decision

Candidate: `24c0c00038f2d15af4b55f178ea44e680c1f2c58` (equal to `evidence/CANDIDATE.json`), draft manifest `98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99`. Recorded 2026-10-16, relayed by the coordinator.

Owner's words, verbatim:

> “1 — Approve the R4 comparison and continue to the release gates, with two corrections to the record.- “No difference attributable to Phase 54 was demonstrated” is supported. “None was caused by Phase 54” is too strong: identical rescoring rules out scorer effects, but doesn’t isolate the runtime schema wording’s influence on what reviewers wrote.- 3/6 quiet cases alarmed, and owner questions stayed at 24. Record that plainly: this rehearsal shows no burden improvement and a substantial risk of missing Phase 55’s false-alarm target.Keep should-quiet-2 counted as an alarm; its pre-existing nature earns no exemption. Don’t change keys, tune prompts, or rerun selectively for better results.This approves proceeding—not declaring the milestone met. The remaining release gates, including the separate live close-out checks, must still pass before freeze.”

Applied to the record: the cause wording in this file, NOTES-phase54-live.md and the 54-11 SUMMARY now reads "no difference attributable to Phase 54 was demonstrated; identical re-scoring rules out scorer effects, but the runtime schema-wording change (agent-output-schema.md) is not isolated from lane behavior"; the burden statement is in `## Before/after` above and in NOTES `## Tally`. should-quiet-2 stays counted (no exemption). No key changed, no prompt tuned, no case rerun. This approval lets the remaining Phase-54 plans proceed; it does not declare the milestone met, and the remaining release gates (including the separate live close-out checks) must still pass before the freeze.
