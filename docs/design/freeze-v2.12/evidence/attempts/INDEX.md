# Attempt records (not results)

Byte-identical copies of run records that were produced outside the repo and
would otherwise be lost. An attempt is a record of what happened, not a
measured result.

## harness-clean-default-22ef678fb884/ — FAILED (stop)

The fix-harness clean-tree run in the default (non-GSD) mode on freeze
candidate `22ef678fb88418f22419867bed81ff89283fa7fb`, draft manifest
`ec070ea1e852bd8f92811d70cd28578f07eaf665ec535cc083940cdc12e38198`.
Command: `fixharness.py run --case py-clamp-01 --kind clean --manifest <draft>`.

- Verdict FAILED, exit 1, 242.7 s. Reasons: `.turingmind/REVIEW.md missing`,
  `state not archived`, `turn ended on unrecognised text`,
  `clean-tree checkpoint never reached`.
- Identity, model and containment held (sandbox denials 0).
- Cause: the session's final message contained both a "no issues to fix"
  line and a sentence telling the owner to run `--finalize` again to write
  `.turingmind/REVIEW.md` (which is gitignored). The harness turn-end
  classifier matched both the `no-issues` and `review-written` endings, failed
  closed on the double match, and never sent the `--finalize` owner command.
  This is a harness classifier defect, not a plugin behavior change.

Files: `run.json`, `obligations.json`, `transcript.jsonl` (the run's out dir)
and `fixharness-stdout.log` (the command's stdout).

## harness-clean-gsd-22ef678fb884/ — COMPLETE (context)

The GSD-mode run of the same pair on the same candidate and draft, kept next
to the failed run for comparison. Verdict COMPLETE, reasons [], 387.3 s.

## Checks

- Each file was compared with `cmp` against its source; all equal.
- `lanearchive.py scan` over all eight files: clean.
