# vibe-check 2.14.1 baseline, in plain terms

**The baseline is vibe-check at commit `dd8e4ab`, tag `v2.14.1`.**
**Suite 3886 passed, 0 failed; replay 170 runs, 0 differing; five Finalize situations recorded.**

This page is what later work in v2.15 is compared with. When a later phase changes how Finalize
works, it must show that every record below still matches, or name and explain each difference.

## How to read this

**Where each figure comes from.** Every figure on this page is copied from a committed record in
`docs/design/lean-v2.15/baseline/`, all taken at the full commit
`dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4`. A test (`tools/test_baseline_page.py`) re-reads the
records each time the test suite runs and fails if any figure here differs from its record.

| Section | Record | Made by |
|---|---|---|
| Suite | `suite-v2.14.1.json` | the plugin's own test suite, run once on the owner's Mac |
| Archived replay | `replay-baseline-v2.14.1.md`, `replay-baseline-v2.14.1.no-private.md` and their `.sha256` files | `replay.py`, the plugin's re-scoring tool, through `tools/baseline_records.py` |
| Finalize situations | `finalize-situations-v2.14.1.json` and its `.sha256` file | `tools/finalize_capture.py` |
| Instructions loaded (bytes) | `footprint-v2.14.1.json` | `tools/path_records.py`, recounting each file at the commit |
| Files actually loaded (traces) | `traces-v2.14.1.json` | `tools/path_records.py`, reading recorded test sessions |
| Model-run mechanical steps | `steps-v2.14.1.json` | `tools/step_count.py` |

`MANIFEST.json` ties the records together: it holds a fingerprint of every file in the folder.

**Words used below.**

- A *fingerprint* is a 64-character code computed from a file's exact contents (a SHA-256 hash).
  Change one character of the file and the fingerprint changes, so two equal fingerprints mean
  two identical files.
- *Bytes* are the size of the instruction files the model is given, a plain count of characters.
- *Steps* are the mechanical actions the instructions ask the model itself to carry out.

**Measured counts versus proxies.** Every figure on this page is a count, except one clearly
labelled table of *proxy* token figures. A proxy is a rough estimate worked out from the byte
count; nobody measured it, and it is not a bill. Byte and step counts are never mixed with token
or price figures, and there are no prices anywhere on this page.

## Suite

**3886 passed, 0 failed, 0 skipped.**

- Summary line as printed: `3886 passed, 5060 subtests passed in 187.57s (0:03:07)`
- Runner pytest 9.0.3, Python 3.12.12, on Darwin 27.2.0 (macOS).
- Plugin tree id `90e0697363ee5c09bb7942a963cf670e16717c4a`. This one id identifies the exact
  contents of the whole `plugins/` folder at the baseline commit.

This run was on the owner's Mac, in the main copy of the repository (the one that holds the
private test recordings), where no test skips.

On GitHub's Linux machines (the continuous test run this phase sets up) the same suite runs
with two owner-approved exceptions: five named tests are left out by owner ruling D-18, and a small recorded set of tests
skips itself by owner ruling D-20. Both lists are in `62-CI-RECORD.md` in the phase records.

## Archived replay

The replay tool re-scores the review runs archived from earlier milestones with the 2.14.1
scorer and writes a report. The report's fingerprint is the baseline.

| Condition the report was taken in | Report file | Fingerprint |
|---|---|---|
| 12 private recordings present (the owner's main copy of the repository) | `replay-baseline-v2.14.1.md` | `142de13d56c61c5794d24bb432332db1deaf06ae1c102ee742f32fff59c1ae24` |
| 0 private recordings present (a linked worktree, or GitHub's machines) | `replay-baseline-v2.14.1.no-private.md` | `3eb053ca81f283401f7b1296bbd28b3d2cc157d1ac528323de68e488c3dbb1f0` |

Two lines of every report change on every run: the commit the report was run at and the time it
was written. They are removed before the fingerprint is taken. The rule, as recorded:

> drop every line matching `^- (HEAD|head|generated( \(UTC\))?): ` (the commit the report was run at and the time it was written), then sha256 the remaining bytes

Comparing the 2.14.1 scorer's results with the archived baseline gave
`runs compared: 170, runs differing: 0`.

**A fingerprint only matches a report captured in the same condition.** The report includes a
section that depends on whether the private recordings are present, so a report taken on GitHub
(0 recordings) never matches the main-copy fingerprint, and that is expected. Compare a new report
with the fingerprint for its own condition. Do not take a new report in one condition and compare
it with the other.

**Limit.** The replay tool scores with its own pinned copy of the 2.14.1 scorer, not the live
`score.py`. So a change to `plugins/vibe-check/scripts/score.py` alone does not move this
fingerprint. Catching a scorer change needs a separate replay comparison against the live scorer,
which the standing check below does not re-run.

## Finalize situations

Finalize is the closing step of a review: it settles the open findings, writes `REVIEW.md` and
closes the review's saved state. Five situations were walked offline at the baseline commit. No
model was involved: a script ran each command block from the 2.14.1 instructions as written and
recorded what came out.

| Situation | What was recorded | Commands run | Values carried | Writes |
|---|---|---|---|---|
| `clean-close` | a clean close with nothing outstanding: the report is written and the state archived | 8 | 2 | 3 |
| `card-first` | open decisions: the decision card is shown first, then the report is written | 17 | 9 | 6 |
| `one-rebuild` | a missing input triggers the one automatic rebuild, then the close succeeds; a second walk where the rebuild also fails is recorded too | 10 | 3 | 3 |
| `refused-close` | a refused close: Finalize stops and writes and archives nothing; a second walk where the earlier report cannot be archived is recorded too | 10 | 4 | 4 |
| `fresh-shell-restart` | Finalize restarted in a fresh shell, then closed | 17 | 9 | 6 |

The three right-hand columns count, for each situation's main walk, the commands run, the values
copied from one command's output into a later command, and the files written in the model's
place. The second walks are recorded in the file but not counted in this table.

Fingerprint of the whole five-situation record: `04a453ffa7cdc965964c694dcad9873c9239e4ebd9cb7e136c06516d21203c55`.

Before the fingerprint is taken, the parts that differ from machine to machine or from minute to
minute are replaced by fixed placeholders: the work folder's location, the plugin's location,
random temporary-file suffixes, dates and times, and clock stamps. The full list is stored in the
record itself under `normalisation`.

**Limit.** The capture was repeated and came out byte-identical, but only on macOS so far. Whether
it also comes out identical on Linux has not been checked yet.

## Instructions loaded (bytes)

The total size of the instruction files each path declares, counted at the baseline commit.

| Path | Bytes | Files |
|---|---|---|
| plain review | 192,057 | 13 |
| deep review | 268,997 | 19 |
| Finalize | 136,114 | 7 |

These are the files the tool's own list (`MODE_PATHS` in `footprint.py`) names for each path.
They are upper bounds: a given run does not necessarily load every file on its list, and a run can
also open files the list leaves out (see the traces section below).

An earlier note said `footprint.py` "exited 2". That did not reproduce: at this commit it exits 0
and prints these figures. Its only exit-2 path is a usage error (a mistyped option), which prints
a usage message and no table, so the earlier observation came from a different command line.

### Proxy figures (estimates derived from bytes, not measured)

Record label: PROXY — derived from bytes, not measured, not a bill

Each proxy is the byte count divided by an assumed number of bytes per token, rounded down. Two
assumptions are shown because the real ratio is not known.

| Path | Proxy tokens at 2.7 bytes per token | Proxy tokens at 3.5 bytes per token |
|---|---|---|
| plain review | 71,132 | 54,873 |
| deep review | 99,628 | 76,856 |
| Finalize | 50,412 | 38,889 |

## Files actually loaded (traces)

Which instruction files a recorded session actually opened, compared with the declared lists
above. The sessions are short test runs ("smoke sessions") recorded on the owner's machine during
the 2.14 releases; no session was run for this baseline.

| Path | Label | Recorded sessions | Versions those sessions ran |
|---|---|---|---|
| plain review | observed | 4 | 2.14.0 candidate 0d2be77 (smoke session); 2.14.1 (smoke session) |
| deep review | declared, not observed | 0 | none |
| Finalize | observed | 1 | 2.14.0 candidate 0d2be77 (smoke session) |

*Observed* means a recorded session's file reads are on record. *Declared, not observed* means
only the tool's declared list exists. For deep review the record names the gap, in its own
words: `no recorded 2.14.x session for this path; nothing was run to fill it (D-09)`. D-09 is the
owner's ruling that gaps are named, never filled by running a new session.

`commands/review.md` never shows up as a file read: it reaches the model as the command itself.

### Files read that the declared list leaves out

| Path | File the session read | Bytes at 2.14.1 | Sessions that read it |
|---|---|---|---|
| plain review | `phases/review/50-fix-loop.md` | 63,013 | 4 of 4 |
| plain review | `templates/output-format.md` | 14,226 | 3 of 4 |
| Finalize | `templates/review-md-schema.md` | 5,035 | 1 of 1 |

The plain review sessions went on into the fix loop, which is why they opened the fix-loop file.
None of these files is counted in the byte table above.

**Limits.**

- Deep review is declared, not observed: no deep-review session at a 2.14.x version was recorded,
  so its file list is the tool's declaration only.
- The recorded sessions read files outside the declared lists (the table above), so the declared
  byte figures do not describe everything a session opens.
- Finalize's only observed session ran the 2.14.0 release candidate, not 2.14.1 itself; the byte
  sizes in this section are taken at 2.14.1.

## Model-run mechanical steps

On the Finalize path, the instructions ask the model itself to carry out mechanical actions.
`tools/step_count.py` counts them over the Finalize path's declared files at the baseline commit.

| Step kind | Count |
|---|---|
| Commands in blocks (bash blocks the model runs) | 42 |
| Commands written inline (a command named in a sentence that the model runs) | 5 |
| Files written (with the Write tool, in a script's place) | 7 |
| Values copied between commands (a value one command prints, pasted into a later one) | 38 |
| **Total model-run steps** | **92** |

**Judgement call.** One of the inline commands, at line 180 of `phases/shared/90-finalize.md`,
is introduced by an arrow rather than by the word "run". It was judged to be an instruction to
run a command. Judged as a mere mention, the total would be 91 instead of 92.

The pass rule that uses this figure and the byte figure for Finalize is in `CRITERION.md`.

## Cost visibility

The cost note's recommendation, not the decision: **NO-GO**

Why: under the rule agreed in D-11, a usage figure is trusted only if the per-reviewer totals
can be checked against a run total that was not made by adding up those same parts, and the
recorded sessions hold no such run total. The note is explicit that this is not a finding that
the usage numbers look wrong.

The decision is the owner's. It is recorded under `## Owner decision` in the cost note
(`62-COST-NOTE.md`, in the phase records) at the phase's closing checkpoint, and it may overrule
the recommendation. Until then, nothing here is decided.

If the owner's decision is no-go, accounting work stops, and the byte and step counts above are
the milestone's evidence. If it is go, nothing is built for usage reporting in v2.15 either; the
smallest useful report is filed as its own backlog item.

## Checking this baseline later

Run, from the repository root:

```
python3 docs/design/lean-v2.15/tools/baseline_records.py verify --repo .
```

If every record still holds, it prints `baseline holds` and exits 0. Otherwise it prints
`BASELINE DIFFERS — STOPPING`, then one line per difference naming the record and what changed,
and exits with a non-zero code. Under the agreed rule (D-08), each difference must be named and
explained, or it blocks the work.

The command chooses the replay report that fits where it runs (the main copy with the private
recordings, or a copy without them). It does not re-run the replay comparison against the live
scorer (see the limit under Archived replay).
