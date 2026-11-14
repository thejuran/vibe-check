# Lean orchestration (v2.15): improvement criterion and comparison workload

**Baseline at 2.14.1 (commit `dd8e4ab`), Finalize path: 136,114 bytes of instructions loaded
across 7 files, and 92 model-run mechanical steps.** The Finalize extraction in Phase 63 passes
if at least one of these two counts drops and neither grows, with identical behaviour.

## The rule in one paragraph

The milestone has two measures, both taken on the Finalize path: (a) the bytes of instructions
the model loads, as measured by `footprint.py`; and (b) the number of mechanical steps the model
has to carry out itself (commands it runs, files it writes in the tool's place, and values it
copies from one command's output into a later command), as counted by `step_count.py`. The
Finalize slice passes if at least one drops and neither grows, and behaviour is identical (D-01).
There is no percentage target. Any real, measured drop on the same paths counts; the release notes
report the actual figure; and nothing is ever cut just to reach a number (D-02).

## Baseline numbers (2.14.1)

| Measure | 2.14.1 figure | Parts | Source |
|---|---|---|---|
| Instructions loaded (bytes) | 136,114 | 7 files | `footprint.py --rev dd8e4ab` |
| Model-run mechanical steps | 92 | 42 bash blocks, 5 inline commands, 7 files written, 38 values copied | `step_count.py --rev dd8e4ab` |

Both figures are counts over the declared Finalize file list, and both are upper bounds: a given
Finalize run does not load or execute everything on the list. Neither is a token count or a price.
Known gap: the recorded Finalize session also read `templates/review-md-schema.md`, which the
declared list leaves out; the declared-versus-observed record is `baseline/traces-v2.14.1.json`.

The step figure is stored, per file and in total, in `baseline/steps-v2.14.1.json` as
`model_run_steps`.

## Counting rule

The count is produced by one script, `tools/step_count.py`, rule version `RULE_VERSION = 1`:

    python3 docs/design/lean-v2.15/tools/step_count.py --rev dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4 --json

It reads the seven Finalize path files at the given commit (the list in `footprint.py`,
`MODE_PATHS["finalize"]`) and counts four things in each:

1. **Bash blocks.** Every command block marked `bash`. A block opens on a line made of optional
   indentation, three or four backticks and the word `bash`, and closes on the next line made of
   optional indentation and the same number of backticks. Indented blocks count, and so does the
   one block that opens with four backticks (the earlier-report archive step in
   `90-finalize.md`). Blocks in any other language count for nothing. Each block is one command
   the model runs. At 2.14.1 there are 42, per file:

   | File | Bash blocks |
   |---|---|
   | `commands/review.md` | 1 |
   | `phases/shared/00-contract.md` | 0 |
   | `phases/shared/01-bootstrap.md` | 1 |
   | `phases/review/00-scope.md` | 10 |
   | `phases/review/05-state.md` | 7 |
   | `phases/review/06-config.md` | 5 |
   | `phases/shared/90-finalize.md` | 18 |

   A rule that saw only unindented three-backtick blocks would find 18 of the 42 and would miss,
   among others, the blocks that print `BLOBFILE`, `GATEFILE`, `DECFILE` and `SUBSETFILE`. The
   tests prove the script does not use that rule.

2. **Inline commands.** A command written in the running text rather than in a block: an inline
   code span, outside every block, that starts with a lowercase command word, uses a value printed
   by an earlier block (`"$NAME"`), and is directly preceded by one of the lead-ins in
   `INLINE_RUN_LEADS`. Each is one command the model runs. The lead-in list is
   `run `, `Run `, `→ ` and `file-to-file with `. Every candidate span in the seven files at
   2.14.1, classified by reading its sentence:

   | File:line | Span | Lead-in | Classification |
   |---|---|---|---|
   | `90-finalize.md:180` | `rm -f "$SUGGESTFILE"` | `→ ` | instructs a run |
   | `90-finalize.md:184` | `cp "$SUGGESTFILE" "$ANSWERFILE"` | `file-to-file with ` | instructs a run |
   | `90-finalize.md:243` | `rm -f "$REFSFILE" "$RESOLVEFILE"` | `run ` | instructs a run |
   | `90-finalize.md:271` | `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` | `Run ` | instructs a run |
   | `90-finalize.md:272` | `rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"` | `run ` | instructs a run |

   All five candidates instruct a run and all five are counted: 5 inline commands. No other file
   on the path has a candidate span.

3. **Files written.** Each occurrence of a phrase in `WRITE_PHRASES` is one file the model writes
   with the Write tool. The phrase list is `with the Write tool` and `Use Write to create`. Every
   line in the seven files that names the Write tool at 2.14.1:

   | File:line | Phrase | What it writes | Classification |
   |---|---|---|---|
   | `90-finalize.md:22` | with the Write tool | HEAD fingerprints to the `BLOBFILE` path | instructs a write |
   | `90-finalize.md:55` | with the Write tool | gate flags to the `GATEFILE` path | instructs a write |
   | `90-finalize.md:169` | with the Write tool | Bottom line suggestion to `SUGGESTFILE` | instructs a write |
   | `90-finalize.md:184` | with the Write tool | owner's answer to `ANSWERFILE` | instructs a write |
   | `90-finalize.md:198` | with the Write tool | translated references to `REFSFILE` | instructs a write |
   | `90-finalize.md:243` | with the Write tool | completed references to `REFSFILE` | instructs a write |
   | `90-finalize.md:301` | Use Write to create | `.turingmind/REVIEW.md` | instructs a write |

   All seven lines instruct a write; there are no mention-only lines. Total: 7 files written. (The
   `write` bullet near line 80 describes the same REVIEW.md write as line 301 without naming the
   tool, so it is not counted a second time.)

4. **Values copied.** A block that creates a temporary file prints its path as `NAME=<path>`,
   because a shell variable does not survive into the next command. Every later use of that
   value, `"$NAME"` in another block or in a counted inline command, is one value the model copies
   by hand. Uses inside the block that printed the name are not counted. At 2.14.1, 11 distinct
   names are printed (`BLOBFILE` and `GATEFILE` among them) and there are 38 copies. The number of
   distinct names is reported but not added to the total, because every copy is already counted.

`model_run_steps` = bash blocks + inline commands + files written + values copied = 42 + 5 + 7 +
38 = 92.

The count is static over the declared files, so like the byte figure it is an upper bound.

**The baseline does not move.** `baseline/steps-v2.14.1.json` stores the seven file paths, the
phrase list and the lead-in list. Every later check (the standing test, the baseline verifier and
Phase 63's comparison) recounts the files named in that record at commit `dd8e4ab`, not the live
list in `footprint.py`, so a later change to that list cannot shift the 2.14.1 figure.

**Phase 63 runs the same script** at its candidate commit, with `--rev <candidate>`, and compares
its total with the 92 above. A change to the script, the phrase list or the lead-in list must be
recorded with the figures it gives on 2.14.1 before and after the change (D-05).

## Maintenance added

Helper code and tests added by the extraction are reported next to the result as their own
labelled figure, "maintenance added" (files and lines added). That figure is not subtracted from
the saving and does not decide pass or fail (D-03).

## If neither count drops

If the Finalize slice matches behaviour but neither count drops, the default is revert (FINX-05).
Before reverting, the owner gets one plain-terms page with the two counts and any reliability
evidence, and may keep the slice by explicit waiver. There is no automatic second attempt (D-04).

## Comparison workload

Bytes and loaded-file traces are recorded for plain review, deep review and Finalize. The Phase 63
pass/fail comparison uses Finalize only. Plain and deep review are re-measured at the Phase 65
release gate only to prove they did not grow (D-06).

The fixed Finalize comparison set is five named situations (D-07):

1. `clean-close` — clean close that writes the report.
2. `card-first` — close with open decisions that shows the card first.
3. `one-rebuild` — the one automatic rebuild after a missing input.
4. `refused-close` — a refused or failed close that writes nothing and archives nothing.
5. `fresh-shell-restart` — restart in a fresh shell.

They are re-run unchanged after the extraction. Their 2.14.1 record is
`baseline/finalize-situations-v2.14.1.json`.

## What "same behaviour" means

The offline record taken at the exact 2.14.1 commit (the offline suite result, the archived
replay output, and the five situations' gate decisions and report text, each with a fingerprint)
must match byte for byte after the extraction. Any difference is named and explained, or it
blocks (D-08).

## Usage and cost

Usage is not a pass/fail measure (D-12). The go/no-go on whether cost can be seen reliably is
`.planning/phases/62-baseline-and-continuous-test-run/62-COST-NOTE.md`. If reliable attribution is
unavailable, accounting work stops and the two labelled counts above are the evidence. Byte and
step counts are always reported separately from any token or price figure, and any token figure
derived from bytes is a proxy and is labelled as one.
