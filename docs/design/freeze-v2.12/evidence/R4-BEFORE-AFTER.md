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

No lost protected catch, so no BLOCKING section is needed. The report body matches the superseded 302df48 report byte for byte, apart from the candidate, HEAD and timestamp lines.

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

**No changed outcomes.** Re-scoring all 170 archived and signed-off rehearsal runs through the candidate scorer gives output byte-identical to the Phase 53 final scorer (ebcd3e4). `.changes.json` lists no entries (`"allow": []`), so the table has zero rows.

| Run | Finding (file:line, stable_hash short) | Before | After | Cause (54-NN change) | Severity effect | Alarm status effect (fires/quiet) | Catch credit effect | Owner burden effect (cards/NV items) |
|---|---|---|---|---|---|---|---|---|

Phase 54 makes one scorer change, 54-01 (R1): a `needs_verification` field whose whole value is a placeholder (`n/a`, `none`, `-`) is treated as blank. It changes no archived outcome, because no archived or rehearsal lane output has a placeholder-only NV field that reaches the scorer. The rule is proven by `TestNeedsVerificationPlaceholders` in `plugins/vibe-check/scripts/test_score.py` (including the bcd15ef blank case), not by replay.

## Unchanged

170 of 170 runs are byte-identical between base and candidate (0 more fall within existing allowances).

## Live checks (54-10/54-11)

The workflow-prose changes (90-finalize.md archive routing; agent-output-schema.md placeholder sentence) are checked live, because archived-output replay covers scorer changes only (D-07).

| check | candidate | outcome | vs Phase 53 | changed? | cause |
|---|---|---|---|---|---|

## Owner decision

_(empty until 54-11)_
