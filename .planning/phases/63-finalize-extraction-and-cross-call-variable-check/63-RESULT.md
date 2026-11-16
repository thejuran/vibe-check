# Phase 63 result: Finalize extraction and cross-call check

Every figure on this page is copied from the phase records and names the commit it was taken at. Nothing here was recounted for this page. Sources: `63-COUNTS.md`, `63-EQUIVALENCE.md`, `63-REMOVAL-LEDGER.md`, `63-REPRO.md`, `63-REVIEW.md`, `63-CONTEXT.md` (decisions D-19 to D-23) and `63-10-SUMMARY.md`.

## Result

Finalize extraction: PASS

- **The verdict.** On the extraction alone (commit `c7d92c9`), Finalize went from 92 to 83 steps the model runs and from 136114 to 129451 bytes loaded. Both dropped and neither grew (`63-COUNTS.md`).
- **Same behaviour.** All five recorded Finalize situations match 2.14.1 on every outcome field. Fewer commands run, which is the purpose. Some things on screen do differ, and they are named below. One of them needs your acceptance: when the saved-progress file cannot be read at all, the shell's "Permission denied" line no longer shows.
- **Cross-call check.** The check is in place and passes. It found six places where a value did not carry from one command to the next (X1 to X6), and all six reproduced. You chose to fix all six, and none were pinned. Three more were found and fixed later: Close out (X7), the fix loop (X8) and Close out and the fix loop on `--all` (C1). One flagged place remains on the exceptions list (C2). It has not been reproduced.
- **What grew.** You chose to fix things the extraction did not need. Those fixes make the phase end larger than 2.14.1 on every review path: the plain review now loads 193267 bytes against 192057, and the deep review 270219 against 268997. The verdict is not affected (D-16). The growth is itemised below.
- **Tests.** The full suite passed in the main checkout after each merge. The run on the final code, which includes the review fixes (merge `533daf9`), was **6,510 passed, 0 failed**. The run before it, after the D-20/D-21 follow-up, was 6,496 passed, 0 failed. Both figures are from the main session's runs, not from the phase records. The pull request's own run is recorded under `## Pull request`.
- **What you are asked to decide.** "Go" to merge, accepting the five items listed under `## Your decision`. You can also ask for a revert or for changes.

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
4. **A different refusal line for a corrupted state file on some machines (found by the pull request's test run).** This applies only when the saved-progress file is not valid UTF-8 text and the machine's locale is C, POSIX or C.UTF-8 (common on Linux servers, not on a Mac). There, 2.14.1 read the bad bytes leniently and showed `refused: malformed state: passes` above the stop sentence. The new version shows `refused: state is not valid JSON`. On a UTF-8 locale both show the same line. The refusal, the stop sentence and the one rebuild are unchanged. The new version shows the same line on every machine, where 2.14.1 varied. Test: `test_finalize_inputs.py::TestCliStderrParity::test_named_difference_non_utf8_state_under_c_locale`. Not exercised by the five situations.

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

No second pass was run over those eleven files. The first review also happened before the review-fix round, so that round got its own review afterwards (`63-REVIEW-2.md`): the `-I` change and its new test, the `--all` print, and the per-character tests.

**Second review, of the review-fix round only (`63-REVIEW-2.md`).** It found no critical issue, 3 warnings and 4 minor notes, and changed nothing.

- **What held up.** Isolated mode ignored a planted `json.py`, `os.py`, `sitecustomize.py`, `usercustomize.py`, a `.pth` file, `PYTHONPATH=.` and `PYTHONSTARTUP` on Python 3.9.6 and 3.14.5, and broke none of the 12 commands. The new `--all` print sits behind the stop on its only path. The reworded sentences do not contradict the other modes. Six deliberate breaks of the new `--all` step were each caught by the tests.
- **Its own coverage.** It read `05-state-all.md` and the two new test files in full; the other five instruction files only around the changed lines; and `test_cross_call_vars.py` only in the changed parts and the helpers the new tests use.

| Item | Plain meaning | Status |
|---|---|---|
| R2-WR-01 | The helper scripts (not the inline commands) still honour a `PYTHONPATH` set in the owner's own environment. A reviewed repo cannot set it. About 70 call sites share the shape | carried |
| R2-WR-02 | If a helper's path were left empty, Python would run a `__main__.py` from the reviewed repo. The review showed what would happen, not that a path is ever left empty. Five sites have no emptiness check in the same command. These lines predate the phase | carried |
| R2-WR-03 | The check that no inline Python lacks isolated mode recognises today's command shapes. It would miss other shapes (for example `python3 -X utf8 -c`, or a script fed on standard input) if one were added later. None exists today | carried |
| R2 notes | Isolated mode also ignores two encoding settings, which could matter for the Codex payload under a non-UTF-8 locale; an `--all` run might print two `STATE_FILE=` lines depending on reading order (not reproduced); the `--all` stop cannot trip on real input, because the key is always hex digits; six of the twelve commands are tested only for "planted file not run", not for their output | left as they are |
| R2 set aside | A narrowed `--all` run may lose its narrowing value in a fresh shell and share the whole-tree key (unchanged line, not tested); version managers or an active virtual environment in the reviewed repo could choose `python3` (not testable on this machine); the `git` and `node` calls beside the inline commands were not assessed | carried, not reproduced |

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
- The test suite runs in the executors' linked worktrees each showed 5 known failures. These are tests whose recordings exist only in the main checkout. At the last of those runs, on `e2f0997`, the result was 4558 passed, 5 failed. The main-checkout run on the final code was 6,510 passed, 0 failed.

## Your decision

The verdict is PASS. A "go" accepts these five things:

1. **The item headed "For your acceptance"**: when the saved-progress file cannot be read at all, the "Permission denied" line no longer shows. The stop sentence appears alone.
2. **The new stop for unsafe names (D-21)**: a review on a folder, branch or phase name containing `$`, a backtick, `"`, `\` or a line break now stops with one "Review halted" line, where 2.14.1 carried on.
3. **Phase-end growth on every review path**: for example, the plain review is 193267 bytes against 192057 at 2.14.1, and the deep review is 270219 against 268997. This comes from the fixes you chose. The extraction alone grew nothing.
4. **The different refusal line for a corrupted state file on C-locale machines**, item 4 under "Other differences on screen".
5. **The carried review items**: from the first review WR-02, WR-03, WR-04, SA-01 and C2 (SA-02), plus its uneven coverage (SA-03); from the second review R2-WR-01, R2-WR-02, R2-WR-03 and its set-aside items. All are described above. They go to backlog and are not fixed in this phase.

On PASS, "go" merges the pull request.

If instead you answer "revert", the extraction commits listed in `63-COUNTS.md` are undone, and the cross-call check and its fixes stay. If you answer "keep under waiver", that wording is meant for a FAIL; on a FAIL this page would be the waiver page, the default would be revert, and there is no automatic second attempt. You can also describe what needs changing first. That would be new work, not a second automatic attempt.

## Pull request

- Pull request: #10, https://github.com/thejuran/vibe-check/pull/10 (`feat/v2.15-phase-63` into `main`). Open, not merged.
- The runs recorded here are on commit `296657d`, the last commit that changes any code or test. This section was added in a later, records-only commit; its own runs are checked before the merge and recorded under `## Merge`.

Runs of `offline-suite` on `296657d`, both green:

| Run | Trigger | Conclusion | Suite summary line |
|---|---|---|---|
| https://github.com/thejuran/vibe-check/actions/runs/43768899519 | push | success | 4554 passed, 2 skipped, 5 deselected, 5762 subtests passed in 288.07s |
| https://github.com/thejuran/vibe-check/actions/runs/43768905498 | pull_request | success | 4554 passed, 2 skipped, 5 deselected, 5762 subtests passed in 204.31s |

The CI suite is narrower than the main-checkout run (6,510 passed, 0 failed, at merge `533daf9`): it leaves out the 5 tests on the left-out list and the design folders outside `docs/design/lean-v2.15/tools`.

**The runs before these were red, for two reasons. Neither was hidden or re-run away.**

| Commit | Run | Conclusion | What failed |
|---|---|---|---|
| `4ad3509` | 43765224199 (push) | failure | 2 failed: the two refusal-line comparison tests (reason 1) |
| `4ad3509` | 43765243417 (pull_request) | failure | 3 failed: the same two, plus the Codex timing test (reason 2) |
| `a45a01f` | 43766695429 (pull_request) | success | 4554 passed |
| `a45a01f` | 43766691154 (push), attempts 1 and 2 | failure | 1 failed each time: the Codex timing test (reason 2) |

1. **Two comparison tests assumed a UTF-8 locale.** They compare the refusal line the new helper shows with the line the 2.14.1 command shows for a saved-progress file that is not valid UTF-8. On the CI machine's C.UTF-8 locale, 2.14.1 itself shows a different line than it does on a Mac. The helper was not changed. The tests now pin the 2.14.1 side to strict UTF-8, and a new test states the difference outright. It is item 4 under "Other differences on screen" and one of the things a "go" accepts. Fixed at `dd69542`; `test_finalize_inputs.py` passes under the default, C, C.UTF-8 and en_US.UTF-8 locales (109 passed each).
2. **A timing test from before this phase is flaky on CI.** `test_codex_collect.py::test_abnormal_exit_is_a_timeout_skip` gives a stub program 2 seconds; it is the suite's first launch of node, and it failed with `'124' != '3'` in 3 of the first 6 runs here. To check whether this phase caused it, five green runs of pre-phase code were re-run the same day: four passed and one (43611416017, commit `1659a99`) failed with the identical error. So the flake is in pre-phase code. The fix is test-only (`296657d`): node is started once, untimed, before the timed runs. No shipped file and no time limit changed. That a cold start is the cause is the best-supported explanation, not a proven one; two green runs after the fix are not enough to prove it gone. Re-running the old runs left them green again (43611416017 is at attempt 3, success).

## Owner decision

2026-11-15. The owner's answer at the checkpoint, in the owner's own words: "go".

The checkpoint named the five things a "go" accepts (listed under `## Your decision`) and showed the verdict (PASS), the two counts, and the pull request with both runs green on its head commit `7cf8e22`. No condition was added. Nothing was merged before this section was written.


## Correction after the merge (D-24)

**What this page got wrong.** Under "Input gaps carried", the row for a finding's file name starting with `-` said the new helper behaves as 2.14.1 does. It did not. For a file at the top of the repo named like `-x.ts`, with a "fix made this obsolete" verdict on unchanged code, 2.14.1 kept the finding open and did not approve the review. The new helper closed the finding and approved the review (Finalize would have written REVIEW.md). Your "go" was given on a page that called this "no difference", so it did not cover it.

**How it was found.** Phase verification, after pull request #10 had merged. The verifier reproduced it on a temporary repo: 2.14.1 left the finding open (`outstanding-to-phase-5`); the new helper approved (`write`). The cause: 2.14.1 ran its file-name safety check as a command, and that command fails on a name starting with `-` because it reads the name as an option, so the file was left out. The new helper ran the same check as a function, which does not read names that way. The test cited for the row only checked the new helper's own output and never ran the 2.14.1 command.

**Your decision.** 2026-11-15, in your words: "Match 2.14.1 (Recommended)".

**What changed.** The helper now runs the 2.14.1 check exactly as the command did, including how it reads the name, and leaves out the same files the command left out. Such a finding now stays open as at 2.14.1. Nothing else changed: the five Finalize situations still match 2.14.1 (`finalize outcome fields match (5 situations, 7 walks)`), and the Finalize path is still 85 steps and 130,886 bytes (the helper is not an instruction file the model loads). The "Input gaps carried" row is corrected in `63-REMOVAL-LEDGER.md`; the text above is left as approved.

**The test.** `test_finalize_inputs.py::TestGuardCommandParity`. It runs the real 2.14.1 check command next to the new helper on a temporary repo for 22 file names, and runs `-x.ts` end to end through the 2.14.1 counting and gate commands. It failed before the fix and passes after it. It also fails if its 2.14.1 side is swapped for the helper's own check, so it really compares against 2.14.1.

**The wider check.** 51 file names compared between the 2.14.1 steps and the helper, on Python 3.14.5 and 3.9.6 (102 comparisons): names starting with `-` at the top or in a folder name, `--`, `-` alone, option-like names (`--root`, `--path`, `-h`, `--help`), number-like names, spaces, `=`, quotes, `$`, backtick, backslash, line breaks, `:`, `*`, `?`, `[`, absolute paths, `..`, a folder, a missing file and symlinks. Before the fix 28 comparisons disagreed, all from this one cause. After the fix none do. No other file name differed; two different kinds of input did (a repo folder whose name ends in a space, see "Second correction" below; and where the three per-file checks run, see "Third correction" below). One detail: which names starting with `-` the command refuses depends on the Python version (for example `-1.ts` is accepted on 3.14 and refused on 3.9). The fix follows the Python that runs the review, as 2.14.1 did.

**Carried to backlog.** Honouring a "fix made this obsolete" verdict for such a file (closing the finding, which 2.14.1 never did) as a possible later improvement.

### Second correction: repo folder names ending in a space (D-25)

**What differed.** Before checking a finding's file, 2.14.1 asked git for the repo's folder and passed git's answer on the way the shell hands it over: only the line break at the end is removed. The new helper also trimmed spaces, tabs and other blank characters from the ends. So for a repo kept in a folder whose name ends in such a character (for example `repo ` with a space at the end), the helper checked a different folder from the one 2.14.1 checked.

**The two reproduced cases**, each with a finding marked "fix made this obsolete":
- Repo folder name ending in a space, a tab or another blank character (also a no-break space or a carriage return), code unchanged: 2.14.1 closes the finding and approves the review (`write`); the helper kept it open and sent it to the finalize card (`outstanding-to-phase-5`). The safe direction.
- The unsafe direction needs a second folder beside the repo with the same name minus the trailing space (`repo ` beside `repo`), holding a repo with the same file, and the real file edited after the verdict. 2.14.1 keeps the finding open; the helper looked in the neighbouring repo, found the file unchanged there and approved the review (`write`), an approval 2.14.1 would not give. The author of a reviewed change cannot arrange this: it depends on folder names on the reviewer's machine.

**How it was found.** The phase re-verification after the first correction (63-VERIFICATION.md, "The new gap in detail"). It was present since pull request #10 merged and was not caused by the first correction. The comparison test added by the first correction trimmed the folder name the same way, so it could not see it.

**Decision.** Your "Match 2.14.1" ruling (D-24) was applied to this case by the main session as D-25, and you were told. You can overrule it.

**What changed.** The helper now removes only the line breaks at the end of git's answer, exactly as the shell does (fix `92ae038`). Nothing else changed: the five Finalize situations still match 2.14.1 (`finalize outcome fields match (5 situations, 7 walks)`), and no instruction file changed, so the 85 steps and 130,886 bytes stand.

**The tests** (written first at `5fe021c`; they failed on the old helper). `test_finalize_inputs.py::TestRepoFolderNameParity` runs the whole Finalize input step against the 2.14.1 commands on temporary repos in folders ending in a space and a tab, in eight further folder-name endings, and in the `repo ` beside `repo` case, which must not approve. The comparison test's 2.14.1 side (`TestGuardCommandParity`) now runs the 2.14.1 check line through a real shell instead of trimming in Python, and has a new case in a folder ending in a space. Putting the old trim back makes the new tests fail; with the old trim put back on the test's 2.14.1 side as well, the space, tab and neighbouring-repo tests still fail, because they check fixed expected results.

**Audit.** Every place the helper reworks git's output or a path was compared with what the 2.14.1 shell did, and the ones that could matter were tried on temporary repos (21 folder cases, on Python 3.9, 3.12, 3.13 and 3.14, under bash and zsh). Among those 21 cases only the repo-folder trim differed, and all 21 now match. The audit did not try a second folder beside one whose name ends in a line break, or a repo whose git settings point its files elsewhere; both give a different decision through where the per-file checks run (see "Third correction" below). A folder name holding a byte that is not valid text could not be created on this Mac's disk, so that case was not tried here; the side-by-side test below runs it wherever the disk allows it.

### Third correction: where the three per-file checks run (gap 3, D-26)

**What differed.** For each finding with a "fix made this obsolete" verdict, Finalize asks git three questions about the file: what HEAD holds, and whether the working copy or the staged copy differ from it. 2.14.1 asked them in the folder the session is in, so git answered about the session's own repository. Since your D-19 decision (an edited file in a subfolder must not be fingerprinted), the new helper asked them in the folder git names as the repo's top, the same text it gives the file-name safety check. Normally that is the same repository. In two unusual set-ups it is not, and then the helper read another repository or none:
- a repo folder whose name ends in a line break, with a second folder beside it under the same name without the line break (the shell's way of passing the folder name drops the line break, so that text names the neighbour);
- a repo whose git setting `core.worktree` points at a different folder.

**The four reproduced cases**, each with the session at the repo's top and a "fix made this obsolete" verdict on `x.ts`:

| Set-up | 2.14.1 | Helper before the fix |
|---|---|---|
| Folder name ending in a line break, a repo with the same file beside it, real file edited after the verdict | finding open (`outstanding-to-phase-5`) | approved (`write`): an approval 2.14.1 would not give |
| The same folder name, a plain folder beside it, file unchanged | approved (`write`) | finding open (`outstanding-to-phase-5`) |
| `core.worktree` pointing at another folder, file unchanged | approved (`write`) | finding open (`outstanding-to-phase-5`) |
| `core.worktree` pointing at a separate repo, a staged edit in the session's own repo | finding open (`outstanding-to-phase-5`) | approved (`write`): an approval 2.14.1 would not give |

**How it was found.** The third verification round (63-VERIFICATION.md, "Gap 3 in detail"). It was present since pull request #10 merged; neither earlier correction caused it, and neither earlier verification found it. The author of a reviewed change cannot arrange either set-up: both depend on folder names or git settings on the reviewer's machine.

**Your decision.** 2026-11-15, in your words: "Fix gap 3 + add the side-by-side test (Recommended)".

**What changed** (fix `08f0018`). The three checks run in the session's folder again, as at 2.14.1, so git finds the session's own repository there with its own settings. The repo's top is still the text given to the file-name safety check, as at 2.14.1. Your D-19 rule is kept a different way: the helper asks git how many folder levels the session sits below the top and puts that many `../` in front of the file name in the two "is it changed" checks, so they check the same file the fingerprint was taken from. (Corrected after the fourth verification round: as first written in `08f0018` the helper did this for every file name, and for a name starting with `./` or `../`, which git reads from the session's folder rather than from the top, the checks then looked at a different file. See "Fourth correction" below; since that fix such a name is given to the checks as written.) At the top nothing is added and the three checks are exactly 2.14.1's. Nothing else changed: the five Finalize situations still match 2.14.1 (`finalize outcome fields match (5 situations, 7 walks)`), and no instruction file changed, so the 85 steps and 130,886 bytes stand.

**The tests.** The side-by-side test below (written first at `d2d604c`, where it failed on the old helper; run against the old helper, its final version disagrees with 2.14.1 in 20 scenarios, these four and 16 more of the same kind, five of them further wrong approvals; all are listed in 63-REPRO.md, and all agree after the fix). In `test_finalize_inputs.py`: `TestSessionRepository` (both `core.worktree` directions; each fails when the checks are moved back to the repo-top folder), the exact git calls from a nested subfolder, and a failing folder-level query leaving every file out. The existing subfolder (D-19) tests still pass.

### Accepted difference: a 60-second limit on each git call (gap 4, D-27)

**What differs.** The helper stops waiting for any one of its git questions after 60 seconds and leaves that file out. 2.14.1 had no limit of its own; the only limit was the session's own limit on a shell call (two minutes unless changed). So the two can differ only when git takes between one and two minutes to answer about a single file.

**What you would see.** On a machine where git is that slow, a finding stays open and goes to the finalize card, where 2.14.1 would have closed it after the long wait. It can only err on the safe side: a timed-out file is never fingerprinted, so it can never cause an approval.

**Reproduction.** The verifier made real git slow with a `core.fsmonitor` hook that waits 65 seconds. The 2.14.1 commands all finished and gave `write`; the helper gave `outstanding-to-phase-5` after 60 seconds (63-VERIFICATION.md, "Gap 4 in detail").

**Your decision.** 2026-11-15, in your words: "Keep the limit, accept by name (Recommended)". Without the limit a stuck git would hang Finalize until the session kills it. No code change. This is a sixth accepted difference, beside the five under "Your decision".

### Fourth correction: file names starting with `./` from a subfolder (gap 5, D-28)

**What it was.** A mistake made by the fix for gap 3 (`08f0018`), on the follow-up pull request only. It was never on `main`, and it was fixed before that pull request merged. git reads a finding's file name in two ways: a plain name like `dir/y.ts` from the top of the repo, but a name starting with `./` or `../` from the folder the session is in. The gap 3 fix pointed the two "is it changed" checks at the top for every name. For a `./` name with the session in a subfolder, the fingerprint therefore came from the subfolder's file while the two checks looked at a same-named file at the top.

**What it did.** Session in a subfolder `dir`, a finding on `./y.ts`, a "fix made this obsolete" verdict, and `dir/y.ts` then edited or staged: 2.14.1 (and `main`) keep the finding open; the helper approved the review (`write`), an approval 2.14.1 would not give. The other way round (only the top-level `y.ts` edited) the helper kept open a finding 2.14.1 closes. Whether any reviewer ever writes a file name starting with `./` is not known; nothing on this path removes it.

**How it was found.** The fourth verification round (63-VERIFICATION.md, "Gap 5 in detail"). The side-by-side test passed with the mistake in place: its only `./` name was `./x.ts`, and no test repo had a file with the same name at the top and in a subfolder.

**Decision.** None needed from you: it broke your D-19 decision ("with the session in a subfolder, a file with unsaved or staged edits is never fingerprinted"), so it was fixed (D-28; you were told).

**What changed** (fix `7079ab0`). A name starting with `./` or `../` is given to the two checks exactly as written, as at 2.14.1: git then reads it from the session's folder in all three questions, so they are about one file. Every other name is still pointed at the top, as D-19 requires. Nothing else changed: the five Finalize situations still match 2.14.1, and no instruction file changed, so the 85 steps and 130,886 bytes stand.

**How the test was strengthened** (written first at `4f89006`, where it failed with 38 differences, 15 of them wrong approvals, all `./` or `../` names from a subfolder). A second grid puts one file name at the top, in the subfolder and one level deeper, each with different content (or only at the top, or only in the subfolder), names it 17 ways (`name`, `./name`, `../name`, `dir/name`, `./dir/name`, `dir/../name`, `../dir/name`, `dir/./name`, names leaving the repo, and others), and changes the top file, the subfolder file, the deeper one, or several (clean, unsaved edit, staged edit, staged edit with the working copy put back), with the session at the top, in the subfolder and deeper: 549 more scenarios. It also checks, against real git, which file each of the three questions reads for every name, so its expectations are not guesses. After the fix all `./` and `../` names agree with 2.14.1 and the only differences are the D-19 ones.

### The side-by-side test

`plugins/vibe-check/scripts/test_finalize_parity_grid.py` keeps the 2.14.1 step that builds the fingerprints as a small shell script (`fixtures/finalize_step1_2141.sh`, transcribed from `dd8e4ab`, `90-finalize.md` lines 13–22). A test checks every command line of that script against the `dd8e4ab` text, word for word and in order, and checks that the four Python files both sides share are byte-identical to `dd8e4ab`; editing the script away from 2.14.1 fails it.

The test builds temporary repos and runs both the 2.14.1 script (followed by the 2.14.1 counting and gate commands) and the new helper in each, then compares the fingerprints, the three counts and the gate's decision. The scenarios cover every pair of these settings at least once: how the repo folder name ends (plain, space, tab, carriage return, no-break space, one or two line breaks, space and line break, a byte that is not valid text); what sits at the name without that ending (nothing, a plain folder, a repo with the same files, a repo with different files); where the session is (top, a subfolder, a deeper subfolder with a non-ASCII name, outside the repo, inside `.git`); git settings and variables (`core.worktree` to a folder or a repo, `GIT_DIR` absolute and relative, `GIT_DIR` with `GIT_WORK_TREE` on the repo or elsewhere, two `GIT_CEILING_DIRECTORIES` values, `core.quotepath`, a linked worktree, a symlinked path, a path through `..`, the three pathspec variables, `GIT_PREFIX`, no git on the path); 14 file-name shapes; six content states (unchanged, edited, staged, staged then put back, deleted, untracked); and four verdict shapes. Named rows from all three verification rounds are added. 284 scenarios. Since gap 5 (see "Fourth correction" above) a second grid adds 549 scenarios on file names and same-named files at several folder levels, so the test now runs 833 scenarios. Updated figures: each grid takes about 15 to 25 seconds on this Mac; the whole test file about 37 seconds on a quiet machine and about 55 seconds while other work is running.

The only allowed difference is D-19: with the session below the repo's top and the file edited or staged, 2.14.1 fingerprints it and the helper must not; for those rows the test checks both sides' exact results. D-19 also works the other way round (verification note N-13): with the session in a subfolder, when the file a finding names is unchanged at the top but a different file with the same name in the session's subfolder was edited, 2.14.1 looks at that other file and keeps the finding open by accident, while the helper looks at the named file and approves the review; `main` already behaves this way, and the test holds it as a D-19 row, not as a new difference. Every other scenario must agree exactly. The list of known differences awaiting your decision is empty: after the fix the grid found none. That held for the 284 scenarios but not for differences they could not build: gap 5 passed them unseen. After the gap 5 fix the second grid also finds none outside D-19, so the list is still empty. One D-19 row is unusual: with `GIT_DIR` and `GIT_WORK_TREE` set and the session inside `.git`, git treats `.git` as a subfolder of the repo, so D-19 applies there too. A scenario this disk cannot create (on this Mac, the folder name holding a byte that is not valid text: 18 scenarios) is listed and counted, not skipped; the Linux CI machine can create it, and there it must agree like any other. Since gap 5 the test fails if any scenario is not creatable on Linux, so those 18 cannot silently stop running in CI; in a Linux container (Python 3.12, git 2.47) all 833 scenarios were created and none differed outside D-19. Each grid's summary line is now shown in the test output even when every test passes (as a warning line), so the CI log records how many scenarios ran. The 60-second limit is not exercised (no scenario makes git slow).

Follow-up pull request: (added by the main session)
