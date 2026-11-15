---
phase: 63-finalize-extraction-and-cross-call-variable-check
reviewed: 2026-11-15T21:03:28Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - .github/scripts/test_stdlib_only.py
  - docs/design/lean-v2.15/finalize-counts-explained.md
  - docs/design/lean-v2.15/tools/finalize_capture.py
  - docs/design/lean-v2.15/tools/test_finalize_capture.py
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/review/06-config.md
  - plugins/vibe-check/phases/review/50-fix-loop.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/finalize_inputs.py
  - plugins/vibe-check/scripts/test_carry_state.py
  - plugins/vibe-check/scripts/test_confirmed_fix.py
  - plugins/vibe-check/scripts/test_cross_call_vars.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_diff_ranges.py
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_finalize_inputs.py
  - plugins/vibe-check/scripts/test_pasted_name_guard.py
  - plugins/vibe-check/scripts/test_pause_batching.py
  - plugins/vibe-check/scripts/test_score.py
findings:
  critical: 1
  warning: 5
  info: 4
  total: 10
status: issues_found
---

# Phase 63: Code Review Report

**Reviewed:** 2026-11-15T21:03:28Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Reviewed the phase diff `ff8ab99..HEAD`. Read in full: `finalize_inputs.py`, the diff of the five instruction files, `test_pasted_name_guard.py`, and the rule/exception sections of `test_cross_call_vars.py`. `test_finalize_inputs.py` was read by outline plus selected sections. The remaining files were only pattern-scanned (see SA-03).

What was run, not just read:

- The `case` guard under `/bin/bash` 3.2.57, zsh and `/bin/sh`: it refuses `$`, backtick, `"`, `\`, newline and carriage return, and passes plain names. The pattern does what it claims on all three shells.
- A per-character mutation of the guard in a scratch copy of the plugin (12 mutants, both files).
- `finalize_inputs.py` through its CLI on odd states (deeply nested JSON, directory, unreadable file, empty path).
- `test_finalize_inputs.py` (108), `test_pasted_name_guard.py` (6), `test_cross_call_vars.py` (70): all pass.
- The convention check (`gsd-tools.cjs verify conventions --check`): zero findings.

Headline results:

- **The new helper's git handling is sound.** Every call is an argv list with a timeout and no shell; the file name is validated and contained before any git call; it sits after `HEAD:` or after `--`, so a leading `-` cannot become an option; the checks run from the repo root. No injection or traversal path was found in it.
- **All three print sites are behind the guard**, and the guard matches every character it claims.
- **One critical item, which predates this phase** but sits in two of the reviewed files: six `python3 -c 'import json…'` fences run a `json.py` planted at the root of the reviewed repo (CR-01, reproduced).
- The remaining gaps are around the guard rather than in it: a `--all` close-out has no printed state path to paste, an empty phase id passes the guard, and the guard's safety depends on the model always pasting inside double quotes.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: `python3 -c` fences import a `json.py` planted in the reviewed repo (pre-existing, not introduced by this phase)

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:188`, `:226`, `:236`; `plugins/vibe-check/phases/review/50-fix-loop.md:142`, `:151`, `:189`
**Issue:** Each of these fences runs `python3 -c 'import json,sys; …'` in the session's working directory, which is the reviewed repository. With `-c`, Python puts the current directory first on its module search path, so a file named `json.py` at the reviewed repo's root is executed in place of the standard library. Reproduced: in a folder holding a `json.py` that writes a marker, `python3 -c "import json"` printed the marker; `python3 -I -c "import json"` did not. Anyone who can get a file into the reviewed checkout (a contributor branch, a cloned third-party repo) gets code execution as the owner the moment the finalize card or the fix loop parses an answer. The helper scripts are not affected: `python3 "$VC_ROOT/scripts/x.py"` puts the script's own folder first, not the working directory.

These lines are unchanged by this phase. They are graded by effect because they sit in two reviewed files and in the class the review was asked to prioritise (repo content reaching execution). `05-state-all.md:18-21` has the same pattern and is outside the file list.
**Fix:** Add isolated mode to every `python3 -c` in the phase files:
```bash
if python3 -I -c 'import json,sys; json.dump(json.load(sys.stdin)["payload"], sys.stdout)' < "$PARSEFILE" > "$DECFILE"; then
```
`-I` is available on the Python 3 that macOS ships. Add a test that scans every Bash fence for `python3 -c` without `-I`, plus one behavioural case with a planted `json.py`.

## Warnings

### WR-01: A `--all` close-out or fix loop has no printed `STATE_FILE=` to paste, and an empty paste reads as "no prior review"

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:11`, `:21`; `plugins/vibe-check/phases/review/50-fix-loop.md:18`; `plugins/vibe-check/phases/review/05-state-all.md:17-22`
**Issue:** The new sentences say `"$STATE_FILE"` is "the literal printed after `STATE_FILE=` by `05-state.md`". In `--all` mode `05-state-all.md` replaces that resolution and prints nothing (no `printf` in the file). The phase records this as exception C1, "flagged, not reproduced / not decided".

The effect is concrete. If the model follows the sentence and has no literal, the fence runs with `--state-file ""`. The helper treats an empty path as "no state file" and exits 0 with `next: stop-no-state` (reproduced: `--state-file ""` gives rc 0 and the no-state result). The owner is told "No prior review passes. Run `/review` first." after a completed `--all` review, and the automatic rebuild never fires because nothing failed. In the fix loop the same empty paste gives `< ""`, a shell redirect error.
**Fix:** Print the key in `05-state-all.md` after the assignment (the value is a 12-hex path from `statepath.py`, so it needs no guard), and name both sources in the two sentences:
```bash
    STATE_FILE="$ALL_STATE_FILE"
    printf 'STATE_FILE=%s\n' "$STATE_FILE"
```
Then remove C1 from `CROSS_FILE_EXCEPTIONS`. Separately, consider having the Finalize fence refuse an empty `--state-file` literal rather than letting it mean "no state".

### WR-02: An empty phase id passes the guard and gives every phase the same state file

**File:** `plugins/vibe-check/phases/review/05-state.md:9-13`; `plugins/vibe-check/phases/review/00-scope.md:125`
**Issue:** `${PHASE_ID}` is read in the 05-state fence but no fence sets or prints it; `00-scope.md:125` sets it in prose only. This is exactly the cross-call read the phase set out to close, and the checker cannot see it because it only flags names that some fence assigns. If the fence runs as written, the result is `STATE_FILE=.turingmind/state/format-53/.json`, and the guard prints it (reproduced). Every GSD phase would then share one hidden state file, so a close-out for one phase could be decided on another phase's findings.
**Fix:** Derive and print the id in the `00-scope.md` fence, and refuse an empty one in `05-state.md`:
```bash
# 00-scope.md, after the PHASE_DIR print
PHASE_ID=$(basename "$PHASE_DIR")
printf 'PHASE_ID=%s\n' "$PHASE_ID"
# 05-state.md, first line of the GSD fence ("<PHASE_ID>" is the pasted literal)
[ -n "<PHASE_ID>" ] || { echo "Review halted — the phase id is empty; nothing was scored." >&2; exit 1; }
```
Add "a name set only in prose" to `KNOWN_LIMITS`, or extend the checker to flag a fence read of a name no fence sets.

### WR-03: The guard is a deny-list for one quoting context; safety depends on every paste being inside double quotes

**File:** `plugins/vibe-check/phases/review/00-scope.md:93`; `plugins/vibe-check/phases/review/05-state.md:11`, `:23`
**Issue:** The pattern refuses the six characters that are live inside double quotes. It passes `'`, space, `;`, `&`, `|`, `(`, `)`, `*`, tab, ESC and form feed (verified). That is correct only while the model pastes the value inside double quotes at every site. Two uses have no fence to hold the quoting: the `basename` at `00-scope.md:125` is prose, and `10-triage.md:39` / `15-intent.md:8` use `$PHASE_DIR` in text. A phase folder named `02-x;touch PWNED` is printed, and one unquoted paste runs it. The prefix lookup (`<arg>-*`) means the owner typing `02` is enough to select such a folder. The tests deliberately keep spaces and `()+,` working, so a strict allowlist is a product choice, not a pure code fix.
**Fix:** Either (a) refuse the shell-live characters of every context, keeping space and the punctuation the tests name:
```bash
case "$PHASE_DIR" in *[\$\`\"\\\'\;\&\|\<\>\*\?$'\n\r\t\033']*) echo "Review halted — …" >&2; exit 1;; esac
```
or (b) keep the pattern and close the unfenced uses (WR-02's fix removes the prose `basename`). Option (b) is the smaller change.

### WR-04: The helper swallows every internal failure as exit 4 with no diagnostic, and the owner is told the wrong component failed

**File:** `plugins/vibe-check/scripts/finalize_inputs.py:378-381`; `plugins/vibe-check/phases/shared/90-finalize.md:24-25`
**Issue:** `run` catches `Exception` and returns exit 4 with nothing on stderr. The fence maps 4 to "finalize_gate.py failed". Any bug or unexpected input in `carry_state`, `batch_card`, the JSON encoder or the helper itself is therefore reported as a gate failure, with no trace anywhere. Reproduced: a state file of 200,000 nested brackets raises `RecursionError` in the loader (not a `ValueError`, so not the "state is not valid JSON" exit 3) and comes out as rc 4 with empty stderr. The retry then fails identically and the owner sees "Finalize stopped" with nothing to act on. The contract ("on every other exit nothing") is deliberate and tested, but it leaves a real failure with no evidence.
**Fix:** Treat loader failures as the state refusal, and leave a non-disclosing trace for the catch-all:
```python
    try:
        state = carry_state.load_json_text(text)
    except (ValueError, RecursionError):
        return None, carry_state.REASON_STATE_JSON
```
```python
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("finalize_inputs: internal failure (%s)\n" % type(exc).__name__)
        return EXIT_GATE, ""
```
The exception class name carries no path, hash or title. This changes `test_stderr_empty_on_every_other_exit` and needs an owner ruling on the "nothing on stderr" contract.

### WR-05: The guard tests do not independently prove `"` is refused at any site, and the mutant assertion holds for any input

**File:** `plugins/vibe-check/scripts/test_pasted_name_guard.py:93-95`, `:138-142`, `:164-170`, `:227-237`
**Issue:** Two weaknesses, shown by mutation in a scratch copy:

1. The `"` payload is `x";touch${IFS}PWNED;"`, which also contains `$`. With `\"` dropped from the guard, `test_bad_names_are_refused_and_nothing_runs` still passes at all three sites. The same holds for the backtick in `05-state.md` (payload contains `${IFS}`) and for newline in `00-scope.md` (no newline case in `BAD`). Mutants that survived the behavioural test: `00-scope.md` drop-`"`, drop-newline; `05-state.md` drop-backtick, drop-`"`.
2. `assert_mutant_trips` passes when a `NAME=` line is printed. Without the guard the fence prints that line for every value, including harmless ones, so for the quote, backslash, newline and carriage-return cases the assertion cannot fail.

The only thing that catches these mutants today is `GUARD_NEEDLE`: `unguarded()` raises when the exact guard text is not found. That is a text pin, not a behaviour check, and a functionally different pattern with the same failure would need the needle updated, at which point nothing behavioural covers `"`.
**Fix:** Use single-character payloads so each class member is tested alone, and add the missing newline case:
```python
QUOTE = 'x"y'          # no $, no backtick
BACKTICK_ONLY = "x`y"
("newline", ".planning/phases/02-a\nb", "02"),
```
In `assert_mutant_trips`, require for the non-executing characters that the printed value contains the bad character, not merely that a line was printed.

## Info

### IN-01: `PATH_RE` accepts a trailing newline

**File:** `plugins/vibe-check/scripts/finalize_inputs.py:173` (constant defined at `fixcommit.py:101`)
**Issue:** `^[A-Za-z0-9._/-]+$` with `.match` accepts `"a.ts\n"` (verified), because `$` matches before a final newline. Harmless here: the value goes to git as one argv element, and git finds no such file, so it is left out. The helper's docstring describes the filter as stricter than it is.
**Fix:** Use `PATH_RE.fullmatch(f)` in the helper, or `\Z` in the constant.

### IN-02: "It writes only `--blob-out`" is not strictly true

**File:** `plugins/vibe-check/scripts/finalize_inputs.py:29-30`, `:178-180`
**Issue:** `git diff` may refresh and rewrite `.git/index` as a side effect. `test_git_runner_mirrors_the_named_calls` pins the absence of `--no-optional-locks`, so this is a recorded choice, but the docstring overstates.
**Fix:** Reword the docstring to "writes no file of its own other than `--blob-out`", or set `GIT_OPTIONAL_LOCKS=0` in the child environment and drop the pin.

### IN-03: Fingerprint temp files are never removed

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:15`, `:38`, `:244`
**Issue:** Every attempt mints a new `BLOBFILE` (first run, the automatic rebuild, the post-card re-run) and no step removes any of them. Each holds repo file paths and blob ids, mode 0600, in the temp folder. The card's other temp files are removed explicitly. The behaviour predates this phase; the phase kept it.
**Fix:** Remove the printed `BLOBFILE=` literal at each terminal branch, alongside the existing `rm -f "$SUGGESTFILE" …` lines.

### IN-04: One test loop runs zero times

**File:** `plugins/vibe-check/scripts/test_cross_call_vars.py:285`, `:715-722`
**Issue:** `EXCEPTIONS = {}`, so the loop in `test_exception_ids_are_unique_repro_ids` has no iterations and its three assertions never run. It is correct while the list is empty and cannot fail.
**Fix:** None needed while the list is empty; delete the loop, or note in the test that it is inert until an entry is added.

## Set aside (needs ruling)

### SA-01: Repo folders with a space or a quote get a truncated or empty state key

**Where:** `plugins/vibe-check/phases/review/05-state.md:21-22`
**Why excluded:** The `git rev-parse --show-toplevel | xargs basename` line predates this phase and is byte-untouched by it; it is not a security issue.
**Effect if left as is:** Reproduced: folder `my repo` gives `my-main.json`; folders `it's` and `a"b` give `-main.json` after `xargs: unterminated quote`. The guard never sees the `"` because `xargs` consumes it first. The key is still inside that repo's own `.turingmind/`, so the visible effect is an odd file name, not cross-repo mixing. `05-state-all.md:15` already uses the safe form `basename "$(git rev-parse --show-toplevel)"`.
**Needs:** ruling from the developer: in scope / defer / accept. Changing the form changes the key for existing reviews in such folders, which would need a migration.

### SA-02: `30-collect-score.md` reads `"$STATE_FILE"` without naming the printed literal (recorded exception C2)

**Where:** `plugins/vibe-check/phases/review/30-collect-score.md:95`, `:100`, `:106`
**Why excluded:** The file is outside the review list and the phase records it as "flagged, not reproduced / not decided".
**Effect if left as is:** If the model runs the fence without pasting, `--state ""` reaches `worktree_snap.py collect`, which always exits 0; the since-review ranges would be computed without the state, with no visible failure.
**Needs:** ruling from the developer: in scope / defer / accept.

### SA-03: Files covered by pattern scan only

**Where:** `docs/design/lean-v2.15/tools/finalize_capture.py`, `docs/design/lean-v2.15/tools/test_finalize_capture.py`, `plugins/vibe-check/scripts/test_finalize_card.py`, `test_carry_state.py`, `test_confirmed_fix.py`, `test_score.py`, `test_diff_ranges.py`, `test_decision_continuity.py`, `test_pause_batching.py`, `.github/scripts/test_stdlib_only.py`, `docs/design/lean-v2.15/finalize-counts-explained.md`
**Why excluded:** Time was spent on the three stated priorities (the helper, the fences, the guard and its tests). These files had their diffs grepped for subprocess/shell use, broad excepts, skips and always-true assertions; nothing was flagged, but they were not read line by line. `finalize_capture.py` is a design-folder tool, not shipped plugin code.
**Effect if left as is:** A cannot-fail test or a resource leak in these files would not have been found by this review.
**Needs:** ruling from the developer: accept, or request a second pass limited to these files.

---

_Reviewed: 2026-11-15T21:03:28Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
