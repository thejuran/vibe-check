# Superseded evidence: freeze candidate 14808a961d02

These files are byte-identical copies, taken from commit a1a4338 (checked with `cmp` against the
working tree and against `git show HEAD:<path>` at the re-run #4 selection), of the 54-10 evidence
produced on candidate `14808a961d0217bc39d6461d3cb9e695743316f8` (54-10 commits ea9b999, 9b8a011,
dc61619, da55908). They are kept for the audit record. They do not describe the current candidate,
and no gate may use them (D-21: superseded results stay on record but never satisfy a passing gate).

Why the candidate was superseded: the owner-run holdout-launcher containment proof on 14808a9
(fixture `~/.b3/containment-proof/holdout-14808a961d02/run-1`) reproduced the card failure again.
Under the launcher's `--permission-mode dontAsk` the fix-loop card (AskUserQuestion) is denied even
though `settings-measured.json` pre-approved it, so follow-up 2b's premise was wrong and every
holdout-eval review that reaches the card is still an invalid run. `containment_proof.py verify`
(as fixed by 2b) reported that fixture as FAILED: `permission failure: AskUserQuestion`, no card.
Follow-up 2c (54-17: f7e19a4..2a6dbb4) runs holdout-eval sessions in B3's `--permission-mode manual`
with B3's pre-approved tool list, removes the 2b AskUserQuestion allow entry, and makes any
unexpected permission prompt (including in subagent transcripts) an invalid run. Those are covered
files, so the candidate moved (D-23) and 54-10 was re-run on a new candidate. The current candidate
and every superseded record are in `../CANDIDATE.json`.

| file | original path |
|---|---|
| `FREEZE-MANIFEST-draft-54-10.json` | `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` (draft manifest_id 6e9e61a0…) |
| `containment-proof-b3.json` | `docs/design/freeze-v2.12/evidence/containment-proof-b3.json` (B3 runner proof, OK under the 2b verify) |

The original paths now hold (or will hold) the evidence for the current candidate.

Not copied:

- `containment-proof-holdout.json`: no holdout proof was ever committed for 14808a9. The owner-run
  proof failed `verify`, so 54-10 re-run #3 stopped before writing it. The file at the plan path is
  still the 535f488 version, byte-identical to `../superseded-535f48861cd8/containment-proof-holdout.json`.
  The failed fixture itself lives outside the repo (`~/.b3/containment-proof/holdout-14808a961d02/`)
  and holds a planted canary secret, so it is not copied into the repo.
- The replay reports, `R4-BEFORE-AFTER.md`, `live-finalize-archive.md` and
  `live-harness-clean-tree.md`: 54-10 re-run #3 stopped before Step 2 and never rewrote them on
  14808a9. They are still the 24c0c00 versions, byte-identical to `../superseded-24c0c00038f2/`.
- The owner decision on the holdout launch procedure (`../acceptance-list.md`,
  `## Owner decision (holdout launch procedure)`, f4b77d6) stays in place; it is a standing owner
  decision, not candidate-bound evidence.
