Result: MATCH

# Phase 63: Finalize on the new instructions compared with 2.14.1

**Commit walked:** `f8f655e40d91e8aa01c4989fff3da397aaec3d2b` (the 63-08 commit that added `compare`; its `plugins/vibe-check` is the new Finalize instructions and helper as left by 63-07).
**Reference:** `docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json` (the 2.14.1 record, driver `fence-walk-2.14.1`, commit `dd8e4ab`). The record, the situation definitions and the 2.14.1 driver were not changed. `finalize_capture.py verify` still prints `finalize baseline matches (5 situations)`.

**Command:**

```
python3 docs/design/lean-v2.15/tools/finalize_capture.py compare --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json --driver helper --commit f8f655e40d91e8aa01c4989fff3da397aaec3d2b
```

Exit code: **0**. Full output:

```
compared with finalize-situations-v2.14.1.json; driver helper-walk-2.15; tree: commit f8f655e40d91e8aa01c4989fff3da397aaec3d2b
clean-close: outcome fields match
card-first: outcome fields match
one-rebuild: outcome fields match
one-rebuild/second-failure: outcome fields match
refused-close: outcome fields match
refused-close/unarchivable-report: outcome fields match
fresh-shell-restart: outcome fields match
intended differences (the lists of commands run, D-15):
  clean-close: steps: before 8 (blobfile, counts, state-present, gatefile, gate, decisions-report, prior-review-archive, archive-state), after 3 (finalize-inputs, prior-review-archive, archive-state)
  clean-close: tally.commands_run: before 8, after 3
  clean-close: tally.values_carried: before 2, after 0
  clean-close: tally.writes: before 3, after 1
  card-first: steps: before 18 (blobfile, counts, state-present, gatefile, gate, rows, card, parse, decfile, record-decisions, blobfile, counts, state-present, gatefile, gate, decisions-report, prior-review-archive, archive-state), after 9 (finalize-inputs, rows, card, parse, decfile, record-decisions, finalize-inputs, prior-review-archive, archive-state)
  card-first: tally.commands_run: before 17, after 8
  card-first: tally.values_carried: before 9, after 5
  card-first: tally.writes: before 6, after 2
  one-rebuild: steps: before 10 (blobfile, counts, blobfile, counts, state-present, gatefile, gate, decisions-report, prior-review-archive, archive-state), after 4 (finalize-inputs, finalize-inputs, prior-review-archive, archive-state)
  one-rebuild: tally.commands_run: before 10, after 4
  one-rebuild: tally.values_carried: before 3, after 0
  one-rebuild: tally.writes: before 3, after 1
  one-rebuild/second-failure: steps: before 4 (blobfile, counts, blobfile, counts), after 2 (finalize-inputs, finalize-inputs)
  one-rebuild/second-failure: tally.commands_run: before 4, after 2
  one-rebuild/second-failure: tally.values_carried: before 2, after 0
  refused-close: steps: before 10 (blobfile, counts, state-present, gatefile, gate, blobfile, counts, state-present, gatefile, gate), after 2 (finalize-inputs, finalize-inputs)
  refused-close: tally.commands_run: before 10, after 2
  refused-close: tally.values_carried: before 4, after 0
  refused-close: tally.writes: before 4, after 0
  refused-close/unarchivable-report: steps: before 7 (blobfile, counts, state-present, gatefile, gate, decisions-report, prior-review-archive), after 2 (finalize-inputs, prior-review-archive)
  refused-close/unarchivable-report: tally.commands_run: before 7, after 2
  refused-close/unarchivable-report: tally.values_carried: before 2, after 0
  refused-close/unarchivable-report: tally.writes: before 2, after 0
  fresh-shell-restart: steps: before 18 (blobfile, counts, state-present, gatefile, gate, rows, card, parse, decfile, record-decisions, blobfile, counts, state-present, gatefile, gate, decisions-report, prior-review-archive, archive-state), after 9 (finalize-inputs, rows, card, parse, decfile, record-decisions, finalize-inputs, prior-review-archive, archive-state)
  fresh-shell-restart: tally.commands_run: before 17, after 8
  fresh-shell-restart: tally.values_carried: before 9, after 5
  fresh-shell-restart: tally.writes: before 6, after 2
fault stand-ins and refusal lines:
  like for like: the 2.14.1 tree's refused-close with `not json` in the printed BLOBFILE on both attempts: outcome fields match the record
  refusal line, counting refused, printed BLOBFILE removed: 2.14.1 and now identical: "refused: head-blobs file is missing or not a JSON object" / "I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived."
  refusal line, counting refused, `not json` in the printed BLOBFILE: 2.14.1 and now identical: "refused: head-blobs file is missing or not a JSON object" / "I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived."
  refusal line, report data refused (state file made `not json` after the count): 2.14.1 and now identical: "refused: state is not valid JSON" / "I'm uncertain about Finalize mode — batch_card.py decisions-report failed; nothing was written or archived."
finalize outcome fields match (5 situations, 7 walks)
```

The same command with `--root plugins/vibe-check` (the working tree) also exits 0. Without `--commit` or `--root` it exits 2.

**The comparison drives the new instructions.** Two deliberate breaks, each made only in a temporary copy of the plugin, each made `compare` fail (`TestCompare::test_compare_drives_the_new_instructions`, and a one-off run at this commit):

- The stop sentence in the copied `90-finalize.md` changed ("again" → "once more"): 2 outcome problems, `one-rebuild/second-failure: stop_sentence differs` and `refused-close: stop_sentence differs`.
- The copied `finalize_inputs.py` adding `!` to the gate's reason: 5 outcome problems, `gate differs` in clean-close, card-first, one-rebuild, refused-close/unarchivable-report and fresh-shell-restart.

The driver mutants (`TestHelperWalk`) also trip: no rebuild makes one-rebuild differ, a re-used BLOBFILE after the card makes the edit-during-card check differ, and ignoring exit 5 changes the report-failure stop sentence. The live tree was unchanged afterwards (`git status` clean).

## Situations

Each outcome field compared byte for byte after the record's normalisation.

| Walk | gate | stop sentence | report | files written | files archived | state closed |
|------|------|---------------|--------|---------------|----------------|--------------|
| clean-close | match | match | match | match | match | match |
| card-first | match | match | match | match | match | match |
| one-rebuild | match | match | match | match | match | match |
| one-rebuild / second-failure | match | match | match | match | match | match |
| refused-close | match | match | match | match | match | match |
| refused-close / unarchivable-report | match | match | match | match | match | match |
| fresh-shell-restart | match | match | match | match | match | match |

## Intended differences

Only `steps` and `tally` differ: the commands the model runs. Commands the model runs (`tally.commands_run`), before (2.14.1) and after (now):

| Walk | Commands the model runs | Values copied between commands | Files the model writes |
|------|-------------------------|-------------------------------|------------------------|
| clean-close | before 8, after 3 | before 2, after 0 | before 3, after 1 |
| card-first | before 17, after 8 | before 9, after 5 | before 6, after 2 |
| one-rebuild | before 10, after 4 | before 3, after 0 | before 3, after 1 |
| one-rebuild / second-failure | before 4, after 2 | before 2, after 0 | before 0, after 0 |
| refused-close | before 10, after 2 | before 4, after 0 | before 4, after 0 |
| refused-close / unarchivable-report | before 7, after 2 | before 2, after 0 | before 2, after 0 |
| fresh-shell-restart | before 17, after 8 | before 9, after 5 | before 6, after 2 |

Each 2.14.1 counting attempt (blob file, counts, state check, gate file, gate) and the separate report command became one Finalize-inputs command. The card steps (rows, parse, the decisions copy, record-decisions) and the archive steps are unchanged. (card-first and fresh-shell-restart list 18 and 9 steps but count 17 and 8 commands: the card the owner reads is a step, not a command.)

## Fault stand-ins

The 2.14.1 capture made its faults by acting between separate commands. Those commands are now one, so each fault has a stand-in, put directly after the fence's `printf 'BLOBFILE=%s\n'` line:

| 2.14.1 fault | Stand-in now | Why |
|---|---|---|
| The printed fingerprint file is gone before the counts step reads it (one-rebuild, both legs) | `rm -f "$BLOBFILE"`: the printed file is removed before the helper reads it | The same fault: the printed file is gone before it is read. |
| The gate input file holds `not json` (refused-close) | `not json` written into the printed fingerprint file | There is no gate input file any more; the nearest equivalent is a malformed input file the attempt depends on. |
| A made-up blob id `blob-pre-card` (fresh-shell-restart) | A real git folder with `src/utils/integrationDeadline.ts` committed; the prepared fix verdict's `verified_blob` is that file's real blob id; the git data lives in a folder beside the walked folder (`git init --separate-git-dir`) | The helper runs real git and cannot produce a made-up id. The prepared input differs; the outcome fields do not. Keeping git's data outside the walked folder means git's own rewrites (its index) cannot show up as files the walk wrote. Only the one-line `.git` pointer file sits in the walked folder; it is in the before-snapshot and never changes. |

**Like-for-like result.** The malformed-input stand-in was also given to the 2.14.1 tree: its refused-close, with `not json` in the printed fingerprint file on both attempts, ends with exactly the recorded refused-close outcome fields (no gate decision, the one stop sentence, nothing written, nothing archived, the state still live). Test: `TestLikeForLike::test_refused_close_outcome_equals_the_record`. So the stand-in is shown to end where the recorded fault ended, on both versions. That the stand-in is a fair replacement for a fault that cannot happen any more (a bad gate input file) is argued, not proven: the file no longer exists. A failure inside the gate stage now exits 4 and shows the gate sentence; that path is tested in 63-07 (`test_report_failure_stops_at_once`, control subtest).

The missing-file stand-in is the recorded fault itself, so it needs no argument. The real-git preparation changes one prepared value (the blob id) and no outcome field.

## The refusal lines (D-18)

What the owner sees, compared byte for byte on the pinned 2.14.1 tree and on the new instructions, with the same fault given to both:

- **Counting fails, printed fingerprint file removed.** 2.14.1 and now: `refused: head-blobs file is missing or not a JSON object`, then `I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived.` Same two lines, same order.
- **Counting fails, `not json` in the printed fingerprint file.** 2.14.1 and now: the same two lines as above.
- **Report data fails.** 2.14.1 and now: `refused: state is not valid JSON`, then `I'm uncertain about Finalize mode — batch_card.py decisions-report failed; nothing was written or archived.` Same two lines, same order.

How the report case was driven: on 2.14.1, the walk reached the gate's `write`, then the state file was made `not json`, then the 2.14.1 report command ran. The new helper does the count and the report in one call, so it cannot be interrupted from outside between its two reads of the state file. Instead a copy of the new plugin tree runs the real helper through a small wrapper that makes the state file `not json` right after the count. The helper's own second read then refuses (exit 5), and the real fence prints the line. The line comes from the helper's code, not from the wrapper. Tests: `TestScreenText::test_counting_lines_are_byte_identical` (a one-character change to the new line makes the comparison fail) and `TestScreenText::test_report_lines_are_byte_identical`. On every failed attempt in the walks themselves (5 attempts across one-rebuild, its second-failure leg and refused-close), the screen is that one counting line then the counting sentence, and nothing else (`TestHelperWalk::test_counting_line_on_every_failed_attempt`). The text is held in memory only; the record's step shape is unchanged.

Note for the owner: in the recorded 2.14.1 refused-close, the fault was in the gate stage, whose diagnostics went to a side file, so the owner saw only the gate sentence. The stand-in fault is in the counting stage, so now the owner sees the counting line and sentence. Given the same fault, the 2.14.1 tree shows exactly the same two lines (above). The text differs because the fault differs, not because the version does.

## Named differences

1. **fresh-shell-restart is prepared in a real git folder** with a real blob id, and its git data is kept outside the walked folder (see Fault stand-ins). What the owner would notice: nothing visible. It changes how the test situation is set up, not what Finalize does.
2. **The entries of the removal ledger's "Named differences" section** (63-REMOVAL-LEDGER.md):
   - **D-19, the subfolder fix (owner decision).** From a subfolder, a file with unsaved or staged edits is no longer fingerprinted. What the owner would notice: a fix-obsolete verdict no longer closes on changed code when Finalize runs from a subfolder. **Not exercised by any of the five situations:** every walk runs from the work folder's top level. It is covered by `test_finalize_inputs.py::TestSubdirectoryCwd` (63-02).
   - **Gate-stage diagnostics no longer written to a side file.** At 2.14.1 they went to `<GATEFILE>.err` and were never shown. What the owner would notice: nothing visible. The five situations do not reach a gate-stage failure on the new instructions (refused-close's stand-in fails in counting; see above).
   - **Unreadable state file: the shell's own `Permission denied` line is no longer shown.** At 2.14.1 a state file that could not be read printed the shell's `Permission denied` line, naming the path, above the counting (or report) sentence. Now the owner sees the sentence alone, with the same stop and the same one rebuild. **For the owner to accept on the D-14 page.** **Not exercised by any of the five situations:** none makes the state file unreadable. It is covered by `test_finalize_inputs.py::TestCliStderrParity::test_named_difference_unreadable_state` (63-02).
   - **The output of commands the model no longer runs.** The per-file git and guard calls, the counts command and the gate command now run inside the helper and print nothing of their own. What the owner would notice: fewer "Ran a shell command" entries; this is the intended difference listed above.
   - **The two refusal lines: no difference.** The counting step's line and the report step's line both still show above their sentences. Checked like for like above.
   - **A fingerprint file holding `{}` is refused** (stricter than 2.14.1's counting command, by contract: the map is always rebuilt into an empty file). What the owner would notice: nothing in normal use, because the instructions always pass a fresh empty file. Not exercised by the five situations.
   - **A review on an unsafe folder, branch or phase name stops (D-21, added by the 63-10 follow-up).** A name holding `$`, a backtick, `"`, `\`, a newline or a carriage return now stops the review at Phase 0 or 0.5 with one "Review halted — … nothing was scored." line, where 2.14.1 went on (and a crafted name could run as a command when pasted). What the owner would notice: that stop, only on such a name. **Not exercised by any of the five situations:** their names are ordinary and the Finalize walks start after the state path is known. Covered by `test_pasted_name_guard.py`.
   - **Close out and the fix loop substitute the printed state path (D-20, added by the 63-10 follow-up).** What the owner would notice: Close out on a saved review writes REVIEW.md, and the fix-loop card appears, even when each block runs as a separate call. **The five situations do not change:** the driver supplies the state path; re-run at `9a01055`, `finalize outcome fields match (5 situations, 7 walks)`. Covered by `test_cross_call_vars.py::TestRepro63::test_x7_finalize_state_file` and `test_x8_fix_loop_state_file`.
   - **Inline Python no longer imports from the reviewed repo's folder (`-I`) (D-22, added by the 63-10 review fixes).** The twelve inline `python3 -c` commands now run as `python3 -I -c`, so a `json.py` planted at the reviewed repo's root is no longer run. What the owner would notice: nothing on a normal repo. **Not exercised by any of the five situations:** the walked Finalize blocks hold no inline `python3 -c`, and no situation plants a module; re-run after the change, `finalize outcome fields match (5 situations, 7 walks)`. Covered by `test_inline_python_isolated.py`.
   - **`--all` prints its state path (D-23, added by the 63-10 review fixes).** What the owner would notice: Close out and the fix loop after an `--all` review work when each block runs as a separate call. **Not exercised by any of the five situations:** none is an `--all` review. Covered by `test_cross_call_vars.py::TestRepro63::test_c1_all_mode_close_out_state_file` and `test_c1_all_mode_fix_loop_state_file`.
   - **A saved-progress file that is not valid UTF-8, on a C locale (entry 10, found by the CI run on the pull request).** On a machine whose locale is C, POSIX or C.UTF-8, 2.14.1 showed `refused: malformed state: passes` above the stop sentence; the new version shows `refused: state is not valid JSON`. On a UTF-8 locale such as en_US.UTF-8 both show `refused: state is not valid JSON`. What the owner would notice: only on such a file and such a machine, a different refusal line; the stop sentence, the refusal and the one rebuild are unchanged, and the helper shows the same line on every locale where 2.14.1 varied. **Not exercised by any of the five situations:** none holds a state file that is not valid UTF-8. Covered by `test_finalize_inputs.py::TestCliStderrParity::test_named_difference_non_utf8_state_under_c_locale`.
3. **Anything else found:** none. No outcome field differed in any walk, and no difference appeared that is not listed above.

## Not checked here

- **Live model behaviour.** These walks act in the model's place: they substitute the printed paths, fill the three switch slots and follow the branches as written. Whether a live model reads the new instructions the same way is not checked here.
- **The installed plugin copy.** An installed copy of vibe-check keeps running the old instructions until it is updated and the session relaunched. This comparison reads the repository, not the installed copy.
