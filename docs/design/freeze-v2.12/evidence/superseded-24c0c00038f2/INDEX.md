# Superseded evidence: freeze candidate 24c0c00038f2

These files are byte-identical copies, taken at commit 535f488, of the 54-10 evidence produced on
candidate `24c0c00038f2d15af4b55f178ea44e680c1f2c58` (54-10 commits f37ae90, 964b402, f469978,
c3f3114, 5bcc1f0; `R4-BEFORE-AFTER.md` also carries the 54-11 rows and the owner's R4 approval,
last changed in 26eaf78). They are kept for the audit record. They do not describe the current
candidate, and no gate may use them (D-21: superseded results stay on record but never satisfy a
passing gate).

Why the candidate was superseded: the release deep review (54-13) and the acceptance list led to an
owner-approved batched fix (A1, A2, B1-B7, P1, S5-S10, S11 narrowed): plugin part 1
401c82f..73792c8, tooling part 2 725f1c1..6df185e, follow-up 1b 1d71044..09bdf61. The owner's
decisions are in `../acceptance-list.md` (through commit 535f488). The fix changes covered plugin,
freeze-kit, B3-runner, fix-harness and holdout-launcher files. That moves the candidate (D-23), so
54-10 was re-run on a new candidate. The current candidate and every superseded record are in
`../CANDIDATE.json`.

| file | original path |
|---|---|
| `R4-BEFORE-AFTER.md` | `docs/design/freeze-v2.12/evidence/R4-BEFORE-AFTER.md` |
| `live-finalize-archive.md` | `docs/design/freeze-v2.12/evidence/live-finalize-archive.md` |
| `live-harness-clean-tree.md` | `docs/design/freeze-v2.12/evidence/live-harness-clean-tree.md` |
| `FREEZE-MANIFEST-draft-54-10.json` | `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` (draft manifest_id 98af8754…) |
| `REPLAY-REPORT-phase54-freeze-guardrail.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-guardrail.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md.changes.json` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md.changes.json` |

The original paths now hold the evidence for the current candidate.

Other evidence bound to 24c0c00 is NOT copied here, because 54-10 does not overwrite it. It stays at
its original path until the plan that regenerates it preserves it: the 54-11 sweep
(`docs/design/reachability-dev/NOTES-phase54-live.md`, `runs-phase54-live/**`), the 54-12 gates
(`test-gate.json`, `security-gate.json`, `semgrep-*`), and the 54-13 deep review
(`deep-review-release.json`, `deep-review-release-raw/**`).
