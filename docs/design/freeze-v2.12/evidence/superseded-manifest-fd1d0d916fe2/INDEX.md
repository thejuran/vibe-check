# Superseded evidence: draft manifest fd1d0d916fe2 (same candidate ddbfff402816)

These files are byte-identical copies, taken from commit 345134e (checked with `cmp` against the
working tree and against `git show HEAD:<path>` at the start of 54-10 re-run #7), of the 54-10
evidence bound to the draft manifest
`fd1d0d916fe27de81f3c697673bbce65e6ab2c201a653e49875f0d6218cc81d3` (generated 2026-10-17T16:56:13Z
on candidate `ddbfff402816805136e95393c98a3cc17196daeb`; 54-10 re-run #6 commits 9a2c634, 479493f,
c85e3b8, ed3f9f8, 75e8860, f12704a). They are kept for the audit record. No gate may use them
(D-21: superseded results stay on record but never satisfy a passing gate).

**The candidate did not change.** Only the manifest was superseded, and the change is in the
environment only. The 54-11 identity check refused this manifest before the first sweep case
(`file differs: codex-config (manifest 6b7088521d37 live 8acb87bdf978)`, IDENTITY MISMATCH). The
ChatGPT desktop app, an owner-side application, rewrote `~/.codex/config.toml` at
2026-10-17T17:37:28Z and again at 17:47:48Z. No `setting differs: codex.config.*` line was
printed, so the parsed Codex settings the manifest records were equal; only the file bytes
changed. The owner chose (2026-10-17) a new draft manifest on the same candidate, with the checks
bound to the manifest redone. The owner's Codex config was not edited or restored. See
`docs/design/reachability-dev/NOTES-phase54-live.md` ("SWEEP NOT STARTED — … the Codex config
file changed after the manifest was generated").

`CANDIDATE.json` records candidate supersessions only. It has no field for a manifest
supersession on the same candidate, so this supersession is recorded here and in the 54-10
SUMMARY (re-run #7), and `CANDIDATE.json` is unchanged.

| file | original path |
|---|---|
| `FREEZE-MANIFEST-draft-54-10.json` | `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` (draft manifest_id fd1d0d91…) |
| `containment-proof-b3.json` | `docs/design/freeze-v2.12/evidence/containment-proof-b3.json` (B3 runner proof, OK; with `archive_step_check`; 479493f) |
| `containment-proof-holdout.json` | `docs/design/freeze-v2.12/evidence/containment-proof-holdout.json` (owner-run holdout proof, OK; review run VALID; with `archive_step_check`; ed3f9f8) |
| `live-harness-clean-tree.md` | `docs/design/freeze-v2.12/evidence/live-harness-clean-tree.md` (default and gsd clean-tree runs, both COMPLETE, identity stamps fd1d0d91…; f12704a) |
| `R4-BEFORE-AFTER.md` | `docs/design/freeze-v2.12/evidence/R4-BEFORE-AFTER.md` (54-10 draft with the archive row and the two harness rows citing fd1d0d91…; no 54-11 live rows, no owner decision) |

The original paths now hold (or will hold) the evidence for the new draft manifest.

Not copied, because they are bound to the candidate and not to the manifest (they carry over
unchanged from re-run #6 on the same candidate; none of them embeds the freeze manifest id):

- `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-guardrail.md`, `REPLAY-REPORT-phase54-freeze-diff.md`
  and its `.changes.json` (75e8860);
- `docs/design/freeze-v2.12/evidence/live-finalize-archive.md` (ad9fa43).

Also not copied:

- the invalid-environment harness attempt on fd1d0d91… already committed in `../attempts/`
  (c85e3b8); see `../attempts/INDEX.md`;
- the proof fixtures `~/.b3/containment-proof/b3-1792256204` and
  `~/.b3/containment-proof/holdout-ddbfff402816/`, which live outside the repo and hold a planted
  canary secret.
