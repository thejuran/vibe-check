# Phase 63 result: Finalize extraction and cross-call check

Every figure on this page is copied from the phase records and names the commit it was taken at. Nothing here was recounted for this page. Sources: `63-COUNTS.md`, `63-EQUIVALENCE.md`, `63-REMOVAL-LEDGER.md`, `63-REPRO.md`, `63-REVIEW.md`, `63-CONTEXT.md` (decisions D-19 to D-23) and `63-10-SUMMARY.md`.

## Result

Finalize extraction: PASS

- **The verdict.** On the extraction alone (commit `c7d92c9`), Finalize went from 92 to 83 steps the model runs and from 136114 to 129451 bytes loaded. Both dropped and neither grew (`63-COUNTS.md`).
- **Same behaviour.** All five recorded Finalize situations match 2.14.1 on every outcome field. Fewer commands run, which is the purpose. Some things on screen do differ, and they are named below. One of them needs your acceptance: when the saved-progress file cannot be read at all, the shell's "Permission denied" line no longer shows.
- **Cross-call check.** The check is in place and passes. It found six places where a value did not carry from one command to the next (X1 to X6), and all six reproduced. You chose to fix all six, and none were pinned. Three more were found and fixed later: Close out (X7), the fix loop (X8) and Close out and the fix loop on `--all` (C1). One flagged place remains on the exceptions list (C2). It has not been reproduced.
- **What grew.** You chose to fix things the extraction did not need. Those fixes make the phase end larger than 2.14.1 on every review path: the plain review now loads 193267 bytes against 192057, and the deep review 270219 against 268997. The verdict is not affected (D-16). The growth is itemised below.
- **Tests.** The full suite passed in the main checkout after each merge. The last completed run recorded before this page was **6,496 passed, 0 failed**, after the D-20/D-21 follow-up. That figure was reported by the main session and is not in the phase records. A run on the final commit, which includes the review fixes, is in progress. Its result is pending and will be added under `## Pull request`.
- **What you are asked to decide.** "Go" to merge, accepting the four items listed under `## Your decision`. You can also ask for a revert or for changes.

## The two counts

| Measure | 2.14.1 (`dd8e4ab`) | Extraction alone (`c7d92c9`) | Phase end (`d56232b`) |
|---|---|---|---|
| Steps the model runs, Finalize path | 92 | 83 | 85 |
| Bytes loaded, Finalize path | 136114 | 129451 | 130886 |
| Steps in `90-finalize.md` alone | 68 | 59 | 59 |

**The rule.** The slice passes if at least one count drops and neither grows, with the same behaviour. Under D-16 it is judged on the extraction alone, at `c7d92c9`. Everything after that commit is fixes you chose, and it is reported below as named growth (D-09).

`d56232b` is the last commit that changes an instruction file. Later commits change only tests and records (`63-COUNTS.md`, "Phase end after the review fixes").

### Bytes on every review path

| Path | 2.14.1 `dd8e4ab` | Extraction `c7d92c9` | After X1–X6 `85a086c` | After D-20/D-21 `9a01055` | Phase end `d56232b` |
|---|---|---|---|---|---|
| Finalize | 136114 | 129451 | 130060 | 130846 | 130886 |
| Plain review | 192057 | 192057 | 192666 | 193267 | 193267 |
| Deep review | 268997 | 268997 | 269606 | 270207 | 270219 |
| Plain review `--all` | not recorded | 284926 | 285535 | 286136 | 286385 |
| Deep review `--all` | not recorded | 361866 | 362475 | 363076 | 363337 |
| Fix loop | not recorded | 255070 | 255679 | 256404 | 256444 |

The extraction left the plain and deep review paths unchanged. At phase end every review path is larger than at 2.14.1. The plain review is 193267 bytes against 192057, and the deep review is 270219 against 268997. All of that growth comes from the fixes you chose. The records do not give the `--all` and fix-loop sizes at 2.14.1.

Steps on the other paths at the phase end (`d56232b`): fix loop 114, plain review 38, deep review 44, plain review `--all` 47, deep review `--all` 53. None of these changed after `85a086c`. The records do not give these step figures at 2.14.1.

### Named growth after the extraction (D-09)

Each row is one file's change, in bytes and counted steps, measured at the commit that made it against the commit before.

| Item | Why | File | Bytes | Steps (Finalize path) | Commit |
|---|---|---|---|---|---|
| X1 | phase folder name carried by printing it | phases/review/00-scope.md | +211 | 0 | `85a086c` record |
| X2 | old state-file name printed | phases/review/05-state.md | +110 | +1 | `85a086c` record |
| X3 | state-file name printed | phases/review/05-state.md | +82 | +4 | `85a086c` record |
| X2 + X3 | shared "use the printed name" sentence | phases/review/05-state.md | +245 | 0 | `85a086c` record |
| X4 | `--codex` read merged into the settings block | phases/review/06-config.md | −13 | −1 | `85a086c` record |
| X5 | repo root read merged into the settings block | phases/review/06-config.md | −13 | −1 | `85a086c` record |
| X6 | `--min-confidence` read merged into the settings block | phases/review/06-config.md | −13 | −1 | `85a086c` record |
| **X1–X6 total** | | | **+609** | **+2** | |
| D-21 | unsafe-name stop before the phase folder is printed | phases/review/00-scope.md | +169 | 0 | `9a01055` |
| D-21 | unsafe-name stop in both state-file name blocks | phases/review/05-state.md | +432 | 0 | `9a01055` |
| D-20 (X7) | Close out uses the printed state-file name | phases/shared/90-finalize.md | +185 | 0 | `9a01055` |
| D-20 (X8) | fix loop uses the printed state-file name | phases/review/50-fix-loop.md | +124 | 0 | `9a01055` |
| **D-20 / D-21 total** | | | **+910** | **0** | |
| D-22 | `-I` on inline Python (3 places) | phases/shared/90-finalize.md | +9 | 0 | `750870f` |
| D-22 | `-I` (3 places) | phases/review/50-fix-loop.md | +9 | 0 | `750870f` |
| D-22 | `-I` (2 places) | phases/review/05-state-all.md | +6 | 0 | `750870f` |
| D-22 | `-I` (2 places) | phases/deep-review/2c-codex-kickoff.md | +6 | 0 | `750870f` |
| D-22 | `-I` (1 place) | phases/deep-review/30-codex-collect.md | +3 | 0 | `750870f` |
| D-22 | `-I` (1 place) | phases/deep-review/01d-coverage.md | +3 | 0 | `750870f` |
| D-23 (C1) | `--all` prints its state-file name, behind the unsafe-name stop | phases/review/05-state-all.md | +243 | 0 | `d56232b` |
| D-23 (C1) | Close out sentence also names the `--all` file | phases/shared/90-finalize.md | +31 | 0 | `d56232b` |
| D-23 (C1) | fix-loop sentence also names the `--all` file | phases/review/50-fix-loop.md | +31 | 0 | `d56232b` |
| **D-22 / D-23 total** | | | **+341** | **0** | |

Growth per path, as recorded:

| Path | X1–X6 | D-20 / D-21 | D-22 / D-23 |
|---|---|---|---|
| Finalize | +609 | +786 | +40 |
| Plain review | +609 | +601 | 0 |
| Deep review | +609 | +601 | +12 |
| Plain review `--all` | +609 | +601 | +249 |
| Deep review `--all` | +609 | +601 | +261 |
| Fix loop | +609 | +725 | +40 |

The extraction's own commits changed nothing on the plain and deep review paths. Every byte of growth on those paths is in the table above. Nothing else changed the instruction files.

## Maintenance added

New helper code and tests do not decide pass or fail. The figures below are from `git diff --numstat ff8ab99 c7d92c9` and the files at `c7d92c9` (`63-COUNTS.md`).

| What | Size |
|---|---|
| New helper, `finalize_inputs.py` | 391 lines, 15092 bytes |
| Its tests, `test_finalize_inputs.py` | 1841 lines, 83451 bytes |
| Capture tool, `finalize_capture.py` | +635 / −12 lines |
| Capture tool tests | +486 lines |
| `test_finalize_card.py` | +806 / −576 lines (net +230) |
| Other re-pointed tests | `test_carry_state.py` +45/−6, `test_score.py` +42/−28, `test_confirmed_fix.py` +37/−8, `test_diff_ranges.py` +17/−12, `test_decision_continuity.py` +5/−4, `test_pause_batching.py` +4/−2, `test_stdlib_only.py` +2/−2 (shipped module count 33 → 34) |
| Design document with the moved explanation | +14 lines |
| Cross-call check, `test_cross_call_vars.py` (separate from the extraction) | 1195 lines, 51398 bytes at `c7d92c9` |

Test code was added after `c7d92c9` as well: two new test files (`test_pasted_name_guard.py` and `test_inline_python_isolated.py`) and growth in `test_cross_call_vars.py`. The records do not give their line counts.

## Same behaviour: the five situations

The five situations were compared field by field against the 2.14.1 record at `f8f655e`, then re-run at `85a086c`, `9a01055` and `d56232b`. Each run printed `finalize outcome fields match (5 situations, 7 walks)`.

| Situation | In plain words | Result |
|---|---|---|
| clean-close | a clean close that writes the report | match |
| card-first | open decisions, so the card is shown first | match |
| one-rebuild (two walks) | a missing input, one automatic rebuild | match |
| refused-close (two walks) | a refused close that writes and archives nothing | match |
| fresh-shell-restart | restart in a fresh shell | match |

The fields that match are the gate decision, the stop sentence, the report text, the files written, the files archived, and whether the review was closed.

### The intended difference: fewer commands

Commands the model runs, before (2.14.1) and after:

| Walk | Commands run | Values copied by hand | Files the model writes |
|---|---|---|---|
| clean-close | 8 → 3 | 2 → 0 | 3 → 1 |
| card-first | 17 → 8 | 9 → 5 | 6 → 2 |
| one-rebuild | 10 → 4 | 3 → 0 | 3 → 1 |
| one-rebuild, second failure | 4 → 2 | 2 → 0 | 0 → 0 |
| refused-close | 10 → 2 | 4 → 0 | 4 → 0 |
| refused-close, report cannot be archived | 7 → 2 | 2 → 0 | 2 → 0 |
| fresh-shell-restart | 17 → 8 | 9 → 5 | 6 → 2 |

### For your acceptance: unreadable state file

When the saved-progress (state) file cannot be read at all, for example because of its permissions, 2.14.1 showed the shell's own line ending in `Permission denied`, with the file's path, above the stop sentence. Now the stop sentence appears on its own. The stop is unchanged and so is the one automatic rebuild. The same applies when the report step cannot read the file: 2.14.1 showed the `Permission denied` line above the report sentence, and now the report sentence appears alone.

- Reproduction: `test_finalize_inputs.py::TestCliStderrParity::test_named_difference_unreadable_state` (state file with permissions 000). For the report read: `test_report_second_read_unreadable_is_a_silent_report_stop`.
- Why it cannot be made identical: that line came from the shell, not from vibe-check, and its wording depends on the command it came from. Matching it would mean making up a shell message and printing the file's path.
- None of the five situations exercises this case.

### Other differences on screen

Not everything on screen is the same as in 2.14.1. These are the differences:

1. **Commands the model no longer runs show no output (intended).** The per-file git and safety checks, the counting command and the gate command now run inside the helper. Their output no longer appears on screen, and neither do their error messages. You will see fewer "ran a command" entries.
2. **Unsafe names stop the review (D-21, new).** See the cross-call section. Not exercised by the five situations.
3. **`--all` prints one extra line.** The `--all` state step now shows a `STATE_FILE=` line (D-23).

### Kept the same on screen

When the counting step or the report-data step refuses, the owner sees the same one-line refusal above the same sentence as in 2.14.1 (D-18). Each case was given the same fault on 2.14.1 and on the new version, and the screen text was compared exactly:

- Counting refused because the fingerprint file was removed: identical. `refused: head-blobs file is missing or not a JSON object`, then `I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived.`
- Counting refused because the fingerprint file held `not json`: identical, same two lines.
- Report data refused: identical. `refused: state is not valid JSON`, then `I'm uncertain about Finalize mode — batch_card.py decisions-report failed; nothing was written or archived.`

### How the test faults were made

The 2.14.1 recording created its faults between separate commands. Those commands are now one, so each fault needed a stand-in:

| 2.14.1 fault | Stand-in now | Checked against 2.14.1? |
|---|---|---|
| Fingerprint file gone before counting (one-rebuild) | The printed file is removed before the helper reads it | Not needed: it is the same fault. |
| Gate input file holds `not json` (refused-close) | `not json` written into the fingerprint file | Yes. Given to the 2.14.1 version, it ends with exactly the recorded outcome. Whether it is a fair stand-in is argued, not proven, because the gate input file no longer exists. |
| Made-up file id (fresh-shell-restart) | A real git folder with a real file id | Not run on 2.14.1. One prepared value changes and no outcome field does. |

In the recorded 2.14.1 refused-close the fault was in the gate step, whose messages were hidden, so the owner saw only the gate sentence. The stand-in fault is in the counting step, so the owner now sees the counting line and sentence. Given the same fault, 2.14.1 shows the same two lines. The text differs because the fault differs, not because the version does.

### Behaviour changes not covered by the five situations

- **Subfolder fix (D-19, the one deliberate change inside the helper).** Before: when Finalize ran from a subfolder, a file with unsaved or staged edits could still be fingerprinted, so a "fix made this obsolete" verdict could close on changed code. Now that cannot happen. Tests: `test_finalize_inputs.py::TestSubdirectoryCwd` (two tests, with mutants). Not exercised by the five situations, which all run from the top-level folder.
- **Close out and the fix loop keep the saved-progress path (D-20, D-23).** Before: when each step ran as a separate command, Close out on a saved review said "no prior review passes" and wrote nothing, and the fix loop stopped with `batch_card.py refused`. Now both work, including after an `--all` review. See X7, X8 and C1.
- **Inline Python is isolated (D-22).** On a normal repo nothing visible changes.
- **A fingerprint file that already holds `{}` is refused.** This is stricter than 2.14.1, and you will not notice it: the instructions always pass a fresh, empty file.

## Safeguards removed and what replaced them

From `63-REMOVAL-LEDGER.md`, state after the extraction was complete.

- **Instruction passages:** 9 rows. 7 were removed or rewritten, at `1ced383`, `8d395f5` and `c337e63`. The other 2 are the on-screen refusal lines, which were kept (D-18).
- **Tests:** 46 rows. 14 were kept as they are and 25 were rewritten or pointed at the new code. 7 were removed because they no longer apply: they guarded the gate input file, which no longer exists.
- **Proof:** every rule that was removed or rewritten has a test protecting it. Each of those tests was proven by a deliberate break that it catches. No rule was removed without a replacement, and each replacement landed before the removal. Five rules had no such test when the ledger was first written; their tests were added at `5f6474e`, before anything was removed.
- **Moved explanation:** the passage explaining what counts as open and closed was moved word for word to `docs/design/lean-v2.15/finalize-counts-explained.md`. That file is not loaded during a review, and a test checks the wording is unchanged.
- **Count lock:** shipped Python modules went from 33 to 34 with the new helper, and they are still standard-library only.

## Cross-call check: flagged places

A new check scans every file under `plugins/vibe-check/phases/`. It fails when a command reads a value that an earlier, separate command set without printing it. Each such value is lost when the commands run as separate calls. Every flagged place was first reproduced by running the real commands as separate fresh calls (`63-REPRO.md`).

| Id | File | What went wrong as separate calls | Status |
|---|---|---|---|
| X1 | phases/review/00-scope.md (phase folder) | A phase review stopped with "Phase resolution escaped .planning/ — refusing." although the phase exists | fixed, `c4c84a3` |
| X2 | phases/review/05-state.md (old state-file name) | Saved progress in the old location was not moved forward, so the review started again at pass 1 | fixed, `7bd3274` |
| X3 | phases/review/05-state.md (state-file name) | A second pass stopped with "the state file's last-pass head_sha is not a commit sha" although the saved progress was fine | fixed, `7bd3274` |
| X4 | phases/review/06-config.md (`--codex`) | `--codex off` had no effect | fixed, `936d29e` |
| X5 | phases/review/06-config.md (repo root) | The repo's settings file was not read, so every setting fell back to its default | fixed, `936d29e` |
| X6 | phases/review/06-config.md (`--min-confidence`) | `--min-confidence 45` had no effect | fixed, `936d29e` |
| X7 | phases/shared/90-finalize.md (state-file name) | Close out on a saved review said "no prior review passes" and wrote no REVIEW.md | fixed, `9a01055` (D-20) |
| X8 | phases/review/50-fix-loop.md (state-file name) | The fix-loop card was never shown; it stopped with `batch_card.py refused` | fixed, `9a01055` (D-20) |
| C1 | phases/review/05-state-all.md (state-file name on `--all`) | After an `--all` review, Close out wrote nothing and the fix loop stopped | fixed, `d56232b` (D-23) |
| C2 | phases/review/30-collect-score.md (state-file name) | Not reproduced. Its text already says to use the state path, but it does not name the printed line. If skipped, the "since last review" ranges would be worked out without the saved state, and no error would show | **remains on the exceptions list**, carried |

Your decision in plan 63-09, in your words: "Fix all six (Recommended)". As a result, X1 to X6 were fixed and none were pinned. The same-file exceptions list is empty. The cross-file list holds only C2, and both lists can only shrink.

**Unsafe names now stop the review (D-21, new compared with 2.14.1).** The folder, branch and phase names that get printed and pasted into later commands come from the reviewed repo. If one of them contains `$`, a backtick, `"`, `\` or a line break, the review now stops before the name is printed. It stops at the scope step or the state step, before anything is scored or written, and shows one line, for example "Review halted — the phase folder path holds $, `, ", \ or a line break; nothing was scored." 2.14.1 carried on with such a name, and a crafted name could have run as a command when pasted. Names with spaces and ordinary punctuation are not affected. Tests: `test_pasted_name_guard.py`, which checks each character on its own at each of the 4 places a name is printed. A matrix of 24 deliberate breaks was used, and all 24 were caught.

**Planted-module security hole closed (D-22).** This was a security hole, and it was already there in 2.14.1. Twelve inline Python commands in the instruction files ran from the reviewed repo's folder. A file named `json.py` at that repo's root would therefore run as the owner during a review. All twelve now run in isolated mode, and the hole is closed. Test: `test_inline_python_isolated.py` places a planted module next to each command and checks that it does not run. It also checks that no inline Python command without isolated mode is left.

**Known limits of the check, as they stand now:**

- Only files under `phases/` are checked. Command and agent files are not.
- The main check looks within one file. Since the D-20 follow-up, a second check covers values that cross files. It requires the file that reads a value to name the printed line, and the file that sets the value to print it. It does not check the order in which the files run.
- A value that is set only in the prose, and never in a command, is not seen by either check (code review WR-02).

**Code review (`63-REVIEW.md`).** The review found 1 critical issue, 5 warnings and 4 minor notes.

| Item | Plain meaning | Status |
|---|---|---|
| CR-01 | The planted `json.py` hole above | fixed (D-22) |
| WR-01 | `--all` had no printed state path (C1) | fixed (D-23) |
| WR-05 | The unsafe-name tests did not prove each character on its own | fixed (D-23) |
| WR-02 | If the phase id comes through empty, every phase in a repo shares one saved-progress file. Close out for one phase could then be decided on another phase's findings | carried |
| WR-03 | The unsafe-name stop blocks only the characters that are dangerous inside double quotes. It is safe only while every paste is double-quoted, and `;`, `&` and `'` pass | carried |
| WR-04 | An internal fault in the helper is reported as "finalize_gate.py failed", with no detail recorded anywhere | carried |
| SA-01 | A repo folder whose name contains a space or a quote gets a cut-short or odd saved-progress file name. The file still stays inside that repo. Changing this would need a migration | carried |
| SA-02 | C2 above | carried, still on the exceptions list |
| IN-01 to IN-04 | Minor notes | left as they are |

**The review's own coverage was uneven (SA-03).** The review read the new helper, the instruction changes and the unsafe-name tests in full. It read the helper's own tests only in part. Eleven files were only pattern-scanned and never read line by line:

- `finalize_capture.py` and its tests
- `test_finalize_card.py`
- `test_carry_state.py`
- `test_confirmed_fix.py`
- `test_score.py`
- `test_diff_ranges.py`
- `test_decision_continuity.py`
- `test_pause_batching.py`
- `test_stdlib_only.py`
- the design document

No second pass was run. The review also happened before the review-fix round. The changes made in that round have not been reviewed: the `-I` change and its new test, and the `--all` print.

## Input gaps carried

These are places where the helper behaves as 2.14.1 does on an input it could have refused. Each is carried to backlog (`63-REMOVAL-LEDGER.md`, "Input gaps carried (D-06)").

| Gap | What happens (same as 2.14.1) | Test |
|---|---|---|
| A finding's file name starting with `-` | It is fingerprinted. This is harmless, because git cannot read it as an option | `test_gap_leading_dash_path_is_fingerprinted` |
| A fix verdict whose pass is recorded as `true` | It is treated as pass 1 | `test_gap_at_pass_true_matches_pass_one` |
| An empty state-file path | It is read as "no saved progress", so Close out says there are no prior passes | `test_gap_empty_state_file_path_is_no_state` |

There is one case where the helper is stricter than 2.14.1: a fingerprint file that already holds `{}` is refused. You will not notice it in normal use.

The subfolder gap was not carried, because you had it fixed (D-19, above).

## Not measured

- No live review was run, and nothing was paid for. All the checks act in the model's place on the real instruction text. Whether a live model reads the new instructions the same way has not been checked.
- An installed copy of vibe-check keeps running the old instructions until it is updated and the session is relaunched.
- Tokens and dollars are not claimed. The figures on this page are bytes and counted steps only.
- Some behaviour rests on its own tests rather than the five situations, which do not exercise it: the subfolder fix (D-19), the "Permission denied" difference, the unsafe-name stop (D-21) and the isolated-Python change (D-22).
- Only the commands the records name were run in the reproductions. In the fix loop, only the card-rows step was run as separate calls. The record-decisions, payload and fix-verdict steps are covered by the same sentence but were not run. The `--all` reproductions ran only the Finalize-inputs, archive and fix-loop rows steps.
- The refused-close stand-in was checked against 2.14.1, but whether it is a fair replacement is argued, not proven.
- The step counter undercounts the D-20 change. It counts a pasted name only in the file that prints it. So the 4 uses of the state-file name in `90-finalize.md` and the 4 in `50-fix-loop.md` are not counted as steps. Their bytes are counted.
- The records do not give the 2.14.1 byte figures for the `--all` and fix-loop paths, or the 2.14.1 step figures for any path other than Finalize.
- The test suite runs in the executors' linked worktrees each showed 5 known failures. These are tests whose recordings exist only in the main checkout. At the last of those runs, on `e2f0997`, the result was 4558 passed, 5 failed. The main-checkout run on the final commit is still pending.

## Your decision

The verdict is PASS. A "go" accepts these four things:

1. **The item headed "For your acceptance"**: when the saved-progress file cannot be read at all, the "Permission denied" line no longer shows. The stop sentence appears alone.
2. **The new stop for unsafe names (D-21)**: a review on a folder, branch or phase name containing `$`, a backtick, `"`, `\` or a line break now stops with one "Review halted" line, where 2.14.1 carried on.
3. **Phase-end growth on every review path**: for example, the plain review is 193267 bytes against 192057 at 2.14.1, and the deep review is 270219 against 268997. This comes from the fixes you chose. The extraction alone grew nothing.
4. **The carried review items**: WR-02, WR-03, WR-04, SA-01 and C2 (SA-02), as described above, plus the uneven review coverage (SA-03). They go to backlog and are not fixed in this phase.

On PASS, "go" merges the pull request.

If instead you answer "revert", the extraction commits listed in `63-COUNTS.md` are undone, and the cross-call check and its fixes stay. If you answer "keep under waiver", that wording is meant for a FAIL; on a FAIL this page would be the waiver page, the default would be revert, and there is no automatic second attempt. You can also describe what needs changing first. That would be new work, not a second automatic attempt.
