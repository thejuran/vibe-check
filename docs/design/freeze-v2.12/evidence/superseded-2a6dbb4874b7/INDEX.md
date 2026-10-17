# Superseded evidence: freeze candidate 2a6dbb4874b7

These files are byte-identical copies, taken from commit 1010c4d (checked with `cmp` against the
working tree and against `git show HEAD:<path>` at the re-run #5 selection), of the 54-10 evidence
produced on candidate `2a6dbb4874b7521b66d53b2fbb1406dfb46dc230` (54-10 commits a1a4338, 568d515,
539cae2, 4c8fbde, 696bed6, 2028974, e14f6c9, d3af6ad). They are kept for the audit record. They do
not describe the current candidate, and no gate may use them (D-21: superseded results stay on
record but never satisfy a passing gate).

Why the candidate was superseded: the 54-11 restart sweep on 2a6dbb4 (commits 146fc0a, 1ba9c79,
b85a7bb, b66e578) stopped at its first case. reach-new-1 run-1 was a VALID run, but `post`'s lane
archive (`lanearchive.py extract`) refused it with `ValueError: codex directory outside the temp
root`. Inside the measured sandbox TMPDIR is `/tmp/claude-<uid>`, so the Codex kickoff's
`mktemp -d "${TMPDIR:-/tmp}/vc-codex.XXXXXX"` lands there, and `locate_codex_dir` accepted only the
runner shell's temp dir and `/var/folders`. Every Codex-joined measured run was un-archivable.
Follow-up 2d (54-17: bc5738e, 22ef678) additionally accepts only the current uid's sandbox temp root
`/tmp/claude-<os.getuid()>`. `lanearchive.py` is a covered file, so the candidate moved (D-23) and
54-10 was re-run on a new candidate. The current candidate and every superseded record are in
`../CANDIDATE.json`.

| file | original path |
|---|---|
| `FREEZE-MANIFEST-draft-54-10.json` | `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json` (draft manifest_id 3491dd4c…) |
| `containment-proof-b3.json` | `docs/design/freeze-v2.12/evidence/containment-proof-b3.json` (B3 runner proof, OK under the 2c verify) |
| `containment-proof-holdout.json` | `docs/design/freeze-v2.12/evidence/containment-proof-holdout.json` (owner-run holdout proof, OK; review run VALID) |
| `R4-BEFORE-AFTER.md` | `docs/design/freeze-v2.12/evidence/R4-BEFORE-AFTER.md` (54-10 draft; no 54-11 live rows or owner decision on 2a6dbb4) |
| `live-finalize-archive.md` | `docs/design/freeze-v2.12/evidence/live-finalize-archive.md` |
| `live-harness-clean-tree.md` | `docs/design/freeze-v2.12/evidence/live-harness-clean-tree.md` |
| `REPLAY-REPORT-phase54-freeze-guardrail.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-guardrail.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md` |
| `REPLAY-REPORT-phase54-freeze-diff.md.changes.json` | `docs/design/b3-ground-truth/REPLAY-REPORT-phase54-freeze-diff.md.changes.json` (byte-equal to the 24c0c00 copy, `{"allow": []}`) |

The original paths now hold (or will hold) the evidence for the current candidate.

Not copied:

- The 54-11 restart records on 2a6dbb4: `docs/design/reachability-dev/NOTES-phase54-live.md`
  (pre-registration 146fc0a, candidate record b85a7bb, stop record b66e578), the 24c0c00 live run
  dirs moved aside in 1ba9c79, and the stopped attempt
  `docs/design/reachability-dev/runs-phase54-live/attempts/live-reach-new-1-run-1-1792251211/`.
  54-10 does not overwrite them; they stay at their original paths until the 54-11 restart on the
  new candidate pre-registers again.
- The proof fixtures `~/.b3/containment-proof/b3-1792241870` and
  `~/.b3/containment-proof/holdout-2a6dbb4874b7/` live outside the repo and hold a planted canary
  secret, so they are not copied into the repo.
- The owner decision on the holdout launch procedure (`../acceptance-list.md`,
  `## Owner decision (holdout launch procedure)`, f4b77d6) stays in place; it is a standing owner
  decision, not candidate-bound evidence.
