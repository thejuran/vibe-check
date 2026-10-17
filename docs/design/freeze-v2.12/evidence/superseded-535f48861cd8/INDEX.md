# Superseded evidence: freeze candidate 535f48861cd8

These files are byte-identical copies, taken from commit 97261b1 (checked with `cmp` against the
working tree at the re-run #3 selection, ea9b999), of the 54-10 evidence produced on candidate
`535f48861cd8ce09d4e67c00319ea023de294e70` (54-10 commits af31fd8, 42fd446, 025540a, 7c68094,
f4b77d6, 97261b1). They are kept for the audit record. They do not describe the current candidate,
and no gate may use them (D-21: superseded results stay on record but never satisfy a passing gate).

Why the candidate was superseded: the holdout-launcher containment proof on 535f488 reproduced a
gate failure. The fix-loop card (AskUserQuestion) was denied under the launcher's
`--permission-mode dontAsk`, so every holdout-eval review that reaches the card is an invalid run,
and `containment_proof.py verify` printed `CONTAINMENT PROOF OK` over that invalid review
(`containment-proof-holdout.json` below). Follow-up 2b (54-17: 78a07f9, 0568c1f, 14808a9)
pre-approves AskUserQuestion in the measured settings and makes `verify` judge the review session
with the invalid-run rule and require the card shown and answered. Those are covered files, so the
candidate moved (D-23) and 54-10 was re-run on a new candidate. The current candidate and every
superseded record are in `../CANDIDATE.json`.

| file | original path |
|---|---|
| `FREEZE-MANIFEST-draft-54-10.json` | `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` (draft manifest_id 2ff153d6…) |
| `containment-proof-b3.json` | `docs/design/freeze-v2.12/evidence/containment-proof-b3.json` (B3 runner proof, OK under the pre-2b verify) |
| `containment-proof-holdout.json` | `docs/design/freeze-v2.12/evidence/containment-proof-holdout.json` (holdout proof: contained, review run INVALID) |

The original paths now hold (or will hold) the evidence for the current candidate.

Not copied, because 54-10 re-run #2 stopped before Step 2 and never rewrote them on 535f488: the
replay reports, `R4-BEFORE-AFTER.md`, `live-finalize-archive.md` and `live-harness-clean-tree.md`
at their plan paths were still the 24c0c00 versions at the re-run #3 selection (byte-identical to
`../superseded-24c0c00038f2/`). The owner decision on the holdout launch procedure
(`../acceptance-list.md`, `## Owner decision (holdout launch procedure)`, f4b77d6) stays in place;
it is a standing owner decision, not candidate-bound evidence.
