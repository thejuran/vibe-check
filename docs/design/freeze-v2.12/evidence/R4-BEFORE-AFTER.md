# R4 — Before/after outcomes for the v2.12 freeze candidate

Requirement: FRZ-01 / R4 (D-05, D-06, D-07, D-19, D-27). Built in 54-10; the live-check rows and the owner decision are completed in 54-11.

This is 54-10 re-run #5, on candidate `22ef678fb884`. Earlier candidates were superseded in this order:

- `302df48e1097`: the `.in_use` identity defect, fixed in 24c0c00.
- `24c0c00038f2`: the owner-approved batched fix from the release deep review.
- `535f48861cd8`: the holdout card was denied under `dontAsk`, fixed by follow-up 2b.
- `14808a961d02`: 2b's premise was wrong, so follow-up 2c moved the holdout launcher to manual mode.
- `2a6dbb4874b7`: the 54-11 sweep's lane archive refused the sandbox Codex temp dir, fixed by follow-up 2d.

The superseded tables are kept unchanged:

- `evidence/superseded-302df48e1097/R4-BEFORE-AFTER.md`;
- `evidence/superseded-24c0c00038f2/R4-BEFORE-AFTER.md`, which holds the 54-11 live rehearsal on 24c0c00 and the owner's R4 decision for that candidate;
- `evidence/superseded-2a6dbb4874b7/R4-BEFORE-AFTER.md`, the 54-10 draft on 2a6dbb4 with its three live-check rows (the 54-11 sweep on it stopped at its first case and added no row).

The 535f488 and 14808a9 re-runs stopped before this step and wrote no table.

## Candidate

- candidate: `22ef678fb88418f22419867bed81ff89283fa7fb` (from `evidence/CANDIDATE.json`, selected once by 54-10 re-run #5; every superseded selection is recorded in the same file)
- PATH-MAP blob at candidate: `0966dc263d9170d0fa94a4952909a8def82dc305`
- candidate guard (before the replay commands):
  `CANDIDATE OK candidate=22ef678fb88418f22419867bed81ff89283fa7fb head=87f4d7b3c7a9f85dbcbc65cfa86a62d268c90796 descendant_commits=5 (reporting-only)`
- scorer base for the complete-output diff: `rev:ebcd3e4` (Phase 53 FINAL_HEAD; score.py sha256 525c5e83…)
- candidate score.py sha256: 8b8839a4c25aa0dc9f4218fad13af578010692d8db092d4cd3d336384ba7088e (git blob ebad9ba9), the same blob as at 2a6dbb4 (follow-up 2d changed only `lanearchive.py` and its test).
  - This differs from 24c0c00 (blob b9a1e900). Four 54-16 commits from the batched fix changed it: 1af4f53 and 1d71044 (the placeholder NV rule matches only the whole field, and ignores trailing periods only); 1394c75 and 09bdf61 (a Needs-verification item closes on an evidence-bound confirmed fix, only after an independent re-check of the repaired code).
- supersedes the Phase 53 dev-rehearsal fingerprint `5bee4c11…`

## Replay guard

Report: `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-guardrail.md`
(`replay.py candidate --name phase54-freeze --scorer rev:22ef678fb88418f22419867bed81ff89283fa7fb`; exit 0)

| measure | value |
|---|---|
| protected catch runs | 26 |
| kept | 25 |
| amended (existing ledger entry 008) | 1 |
| regressed | 0 |
| unevaluable | 0 |
| baseline reproduction | REPRODUCED 25 / 26, AMENDED 1, UNEVALUABLE 0 |

No lost protected catch, so no blocking section is needed. The report body matches the superseded 2a6dbb4 and 24c0c00 reports byte for byte, apart from the candidate scorer, its sha256, the HEAD line and the timestamp. That includes the headline quiet-set FP prediction, baseline 16/18 -> candidate 14/18.

## Complete-output diff

Report: `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md` (+ `.changes.json`)
(`replay.py diff --base rev:ebcd3e4 --scorer rev:22ef678fb884… --roots all --allow docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json`; exit 0)

| measure | value |
|---|---|
| roots | 7 (all DIFF_ROOTS, including `runs-phase53-dev/final`) |
| runs compared | 170 (= `len(replay.iter_runs(roots=DIFF_ROOTS))`; 16 of them are the signed-off dev rehearsal runs) |
| runs differing | 0 |
| runs differing (allowed) | 0 |
| runs with unallowed differences | 0 |
| allowances unused | 65 (expected: the Phase 53 NV allowances describe changes between the v2.10 baseline and ebcd3e4; ebcd3e4 is now the base, so none of them is exercised) |

No allowances were added. `.changes.json` is `{"allow": []}`, with the same bytes as the 24c0c00 and 2a6dbb4 runs.

## Before/after

**No changed outcomes.** Re-scoring all 170 archived and signed-off rehearsal runs through the candidate scorer gives output byte-identical to the Phase 53 final scorer (ebcd3e4). `.changes.json` lists no entries (`"allow": []`), so replay contributes zero rows.

The candidate scorer carries these Phase 54 changes:

- **54-01 (R1), narrowed in 54-16:** a `needs_verification` field whose whole value is a placeholder (`n/a`, `none`, `-`, with trailing periods ignored) is treated as blank.
- **54-16:** a Needs-verification item closes on an evidence-bound confirmed fix, after an independent re-check.

Neither changes an archived outcome:

- no archived or rehearsal lane output has a placeholder-only NV field that reaches the scorer;
- no archived run records a confirmed fix.

The rules are proven by tests, not by replay:

- `TestNeedsVerificationPlaceholders` in `plugins/vibe-check/scripts/test_score.py`;
- `TestScoreConfirmedFix`, `TestIndependentRecheck` and `TestIndependentRecheckMutants` in `plugins/vibe-check/scripts/test_confirmed_fix.py`.

The live rehearsal rows (one run per case on the candidate) are added by 54-11. The 24c0c00 rehearsal rows and the owner decision on them stay in `evidence/superseded-24c0c00038f2/R4-BEFORE-AFTER.md`. They describe a superseded build and never satisfy a gate here (D-21).

## Unchanged

- Archived replay: 170 of 170 runs are byte-identical between base and candidate. No further runs fall within existing allowances.
- Live rehearsal: filled by 54-11.

## Live checks (54-10/54-11)

Archived-output replay covers scorer changes only (D-07). The workflow-prose and close-out changes are checked live: 90-finalize.md archive routing, the agent-output-schema.md placeholder sentence, and the 54-16 batched-fix changes to 90-finalize.md, `review_archive.py` and `carry_state.py`.

The follow-up 2d change (`lanearchive.py` accepts the current uid's sandbox Codex temp dir) is measurement tooling, not review output. It was checked live on both containment-proof runs of this candidate (`archive_step_check` in `containment-proof-b3.json` and `containment-proof-holdout.json`: extract succeeds, while the pre-fix tool refuses the same input).

| check | candidate | outcome | vs Phase 53 | changed? | cause |
|---|---|---|---|---|---|

## Owner decision

_Empty until 54-11 (the owner's decision on the 24c0c00 table is kept in the superseded copy and does not carry over to this candidate)._
