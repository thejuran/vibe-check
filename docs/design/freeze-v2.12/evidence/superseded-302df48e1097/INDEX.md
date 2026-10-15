# Superseded evidence: freeze candidate 302df48e1097

These files are byte-identical copies of the evidence 54-10 produced on candidate
`302df48e1097212aa334a21c8f2683ed810eb496` (commits 9901ffe, c0c4d91, f1ba535, bd5884c). They are
kept for the audit record. They do not describe the current candidate, and no gate may use them
(D-21: superseded results stay on record but never satisfy a passing gate).

Why the candidate was superseded: the 54-11 live sweep stopped at the first case's `pre` check.
`freeze_common.live_files` hashed Claude Code's `.in_use/<pid>` session-marker directory inside
installed plugin folders, so the identity check refused whenever a measured session was running.
See `docs/design/reachability-dev/NOTES-phase54-live.md` (`## Deviations`, commits d30f6a9 and
24894fe). The fix, commit 24c0c00, changes covered freeze-kit files. That moves the candidate
(D-23), so 54-10 was re-run on a new candidate. The current candidate and this superseded
record are both in `../CANDIDATE.json`.

| file | original path |
|---|---|
| `R4-BEFORE-AFTER.md` | `docs/design/freeze-v2.12/evidence/R4-BEFORE-AFTER.md` |
| `live-finalize-archive.md` | `docs/design/freeze-v2.12/evidence/live-finalize-archive.md` |
| `live-harness-clean-tree.md` | `docs/design/freeze-v2.12/evidence/live-harness-clean-tree.md` |
| `FREEZE-MANIFEST-draft-54-10.json` | `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` (draft manifest_id b6abbae38b9c…) |
| `REPLAY-REPORT-phase54-freeze-guardrail.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-guardrail.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md.changes.json` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md.changes.json` |

The original paths now hold the evidence for the current candidate.
