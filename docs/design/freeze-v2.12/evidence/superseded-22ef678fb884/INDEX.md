# Superseded evidence: freeze candidate 22ef678fb884

These files are byte-identical copies, taken from commit e52d37b (checked with `cmp` against the
working tree and against `git show HEAD:<path>` at the re-run #6 selection), of the 54-10 evidence
produced on candidate `22ef678fb88418f22419867bed81ff89283fa7fb` (54-10 commits 1010c4d, 40557f9,
5864a7c, a71e953, 87f4d7b, ea01a8b, 7f5a124, 8954c62). They are kept for the audit record. They do
not describe the current candidate, and no gate may use them (D-21: superseded results stay on
record but never satisfy a passing gate).

Why the candidate was superseded: 54-10 re-run #5 on 22ef678 stopped in Task 3. The fix-harness
default clean-tree run ended FAILED with `turn ended on unrecognised text`. The session's final
text held the plugin's `No issues to fix.` line and a closing sentence telling the owner to run
`--finalize` again to write `.turingmind/REVIEW.md`, which it called gitignored. No REVIEW.md
existed. The harness turn-end classifier matched both `no-issues` and `review-written`, failed
closed on the double match, and never sent the `--finalize` owner command. Follow-up 2e (54-17:
fd40e29, ddbfff4) makes `review-written` require the run's `.turingmind/REVIEW.md` to exist.
`fixharness.py` and `harness_cards.py` are covered files, so the candidate moved (D-23) and 54-10
was re-run on a new candidate. The current candidate and every superseded record are in
`../CANDIDATE.json`.

| file | original path |
|---|---|
| `FREEZE-MANIFEST-draft-54-10.json` | `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` (draft manifest_id ec070ea1…) |
| `containment-proof-b3.json` | `docs/design/freeze-v2.12/evidence/containment-proof-b3.json` (B3 runner proof, OK; with `archive_step_check`) |
| `containment-proof-holdout.json` | `docs/design/freeze-v2.12/evidence/containment-proof-holdout.json` (owner-run holdout proof, OK; review run VALID; with `archive_step_check`) |
| `R4-BEFORE-AFTER.md` | `docs/design/freeze-v2.12/evidence/R4-BEFORE-AFTER.md` (54-10 draft with the archive row only; no harness rows, no 54-11 live rows, no owner decision on 22ef678) |
| `live-finalize-archive.md` | `docs/design/freeze-v2.12/evidence/live-finalize-archive.md` |
| `REPLAY-REPORT-phase54-freeze-guardrail.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-guardrail.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md.changes.json` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md.changes.json` (byte-equal to the 2a6dbb4 copy, `{"allow": []}`) |

The original paths now hold (or will hold) the evidence for the current candidate.

Not copied:

- `live-harness-clean-tree.md`: it was never rewritten on 22ef678 (Task 3 stopped), so the file at
  its path is still the 2a6dbb4 version, `cmp`-equal to `../superseded-2a6dbb4874b7/`.
- The failed default harness run and the COMPLETE gsd run on 22ef678 are already committed as
  attempt records in `../attempts/` (8954c62); see `../attempts/INDEX.md`.
- The proof fixtures `~/.b3/containment-proof/b3-1792252361` and
  `~/.b3/containment-proof/holdout-22ef678fb884/` live outside the repo and hold a planted canary
  secret, so they are not copied into the repo.
- The 54-11 restart records stay at their original paths, as listed in
  `../superseded-2a6dbb4874b7/INDEX.md`.
