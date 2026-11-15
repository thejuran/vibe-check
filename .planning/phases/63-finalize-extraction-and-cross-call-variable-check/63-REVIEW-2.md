---
phase: 63-finalize-extraction-and-cross-call-variable-check
reviewed: 2026-11-15T21:39:16Z
depth: standard
diff_base: aedda02dfd385451f20ef1f3050b9cdc9359bb5d
files_reviewed: 9
files_reviewed_list:
  - plugins/vibe-check/phases/review/05-state-all.md
  - plugins/vibe-check/phases/review/50-fix-loop.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/phases/deep-review/01d-coverage.md
  - plugins/vibe-check/phases/deep-review/2c-codex-kickoff.md
  - plugins/vibe-check/phases/deep-review/30-codex-collect.md
  - plugins/vibe-check/scripts/test_inline_python_isolated.py
  - plugins/vibe-check/scripts/test_pasted_name_guard.py
  - plugins/vibe-check/scripts/test_cross_call_vars.py
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 63: Code Review Report (second pass, range aedda02..HEAD)

**Reviewed:** 2026-11-15T21:39:16Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Scope: `git diff aedda02dfd385451f20ef1f3050b9cdc9359bb5d HEAD -- plugins` (five commits, 63-10). The range does three things: every inline `python3 -c` became `python3 -I -c` (12 commands in 6 files); `05-state-all.md` now prints `STATE_FILE=` behind the pasted-name guard, with two sentences reworded to name it; tests were added or changed.

What held up under experiment (all run in a scratch directory, on `/usr/bin/python3` 3.9.6 and Homebrew 3.14.5, under `/bin/bash` 3.2):

- `-I` does what the range claims. A planted `json.py`, `os.py`, `hashlib.py`, `sitecustomize.py`, `usercustomize.py`, a `.pth` file, `PYTHONPATH=.`, `PYTHONSTARTUP` and `PYTHONINSPECT` were all ignored by the `-I -c` form, and all 12 commands keep working: multi-line `-c` bodies, the piped-stdin forms, and argv with non-ASCII text.
- `-I` changes nothing about text encoding under `LC_ALL=C`, `POSIX`, `en_US.UTF-8` or `en_US.ISO8859-1`. The only difference is that `PYTHONUTF8` and `PYTHONIOENCODING` are now ignored (IN-01).
- The real `05-state-all.md` fence ran correctly on a plain repo, a folder with a space and an accent, a branch holding `"` and `$`, a narrowed scope, a detached HEAD, outside a git repo (halts) and with `VC_ROOT` unset (halts). The guard precedes the print on the only path that prints; every expansion in the changed lines is quoted; the `else` arm prints no `STATE_FILE=` line.
- Mutating the fence in a scratch copy was caught each time: print removed, print moved before the guard, guard pointed at another variable, guard's `exit 1` removed, print unquoted, wrong value printed.
- The reworded sentences in `90-finalize.md:11` and `50-fix-loop.md:18` create no contradiction for non-`--all` modes.
- The stand-ins in `test_pasted_name_guard.py` (fake `head`, fake `git branch`, stub `statepath.py`) are sound: the refusal case and the one-character-dropped case together show the guard is what refuses, and an unrelated failure of the `--all` fence prints a differently-cased message (`review HALTED`) that the assertion would not accept.
- All three test files pass in a clean copy of HEAD (90 tests, 216 subtests). The convention check returned no findings.

What did not hold up: isolation is uneven. The inline commands are now immune, but the helper scripts next to them in the same pipelines are not (WR-01), an empty helper path executes a file from the reviewed repo (WR-02), and the scan that is meant to keep unisolated commands out cannot see several ordinary ways of writing one (WR-03).

No structural (fallow) findings were supplied for this review.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Helper scripts still import from the reviewed repo when the owner's `PYTHONPATH` has a relative entry

**File:** `plugins/vibe-check/phases/review/05-state-all.md:20` (same shape at roughly 70 `python3 "$VC_ROOT/scripts/…"` call sites, and `hooks/hooks.json:10`); test claim at `plugins/vibe-check/scripts/test_inline_python_isolated.py:8-10` and `:237-249`
**Issue:** The range isolates the two inline commands in this pipeline but leaves the helper between them as plain `python3 "$VC_ROOT/scripts/statepath.py"`. Reproduced: running the real fence in a scratch repo holding a planted `os.py`, with `PYTHONPATH=.` in the environment, printed `PLANTED os RAN` from the helper process and the fence then halted. The same run without `PYTHONPATH` was clean. So a file in the reviewed repo is still imported and executed whenever the owner's shell exports a `PYTHONPATH` with a relative entry (`.`, `src`, `lib` — a common development setup). The precondition is the owner's environment, not the repo, which is why this is a warning and not a blocker.

The new test `test_a_shipped_script_puts_its_own_folder_first_not_the_cwd` passes for a narrower reason than its docstring states: it runs with an environment stripped to `PATH`, so it shows only that the working directory is not first on the path, not that the helper is "not affected".
**Fix:** Run the helpers with `-E -s` (ignore `PYTHON*` variables and the user site folder, keep the script's own folder so sibling imports still work). Verified on both interpreters: `PYTHONPATH=. python3 -E -s <script>` ignores the planted module. `-I` is not a drop-in here because it also removes the script's folder on newer versions.
```bash
| python3 -E -s "$VC_ROOT/scripts/statepath.py" \
```
Add a test case that runs a shipped helper in the planted directory with `PYTHONPATH=.` set and asserts the marker is absent.

### WR-02: An empty helper path makes `python3` execute `__main__.py` from the reviewed repo

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:133`; prose commands at `plugins/vibe-check/phases/review/05-state.md:73`, `plugins/vibe-check/phases/shared/90-finalize.md:284`, `plugins/vibe-check/phases/review/50-fix-loop.md:263`, `plugins/vibe-check/phases/deep-review/01d-coverage.md:28`
**Issue:** These lines are outside the changed hunks; they are reported because the review brief asked for any remaining way a repo file can be executed by the lines around the inline commands. Reproduced on both interpreters: `python3 "" --root x`, with a `__main__.py` in the working directory, runs that file. `-I`, `-E -s` and `-P` do not prevent it. The same happens with an unset variable (`python3 "$NOPE" …`).

`$GUARD_PY`, `$CONFIG_PY` and `$SCORE_PY` are empty whenever the plugin root does not resolve (the bootstrap prints them empty by design), and they are empty in any fresh Bash call where the printed path was not pasted in. The fenced call sites in `00-scope.md`, `00-scope-all.md`, `06-config.md` and `agents/fix.md` test `[ -n "$GUARD_PY" ]` in the same command, so they are safe. The five sites above are not: `30-collect-score.md:133` relies on a check in an earlier, separate fence, and the four prose commands rely on a sentence ("an unresolved/empty `$GUARD_PY` refuses"). If one of them runs with the value empty, the reviewed repo's `__main__.py` runs, and for the guard calls its exit code is then taken as the containment verdict, so a hostile repo both runs code and approves its own path. For the scorer, its output would be taken as the scored findings.

`test_cross_call_vars.py` exempts these four names from the cross-call check (`BOOTSTRAP_NAMES`, line 333) and its harness always supplies them, so nothing tests this case. I did not show that a model leaves the value unpasted; I showed what happens when it does. Graded as a warning on that basis; the effect, if triggered, is code execution from the reviewed repo.
**Fix:** Make each call refuse an empty path in the same command, as the fenced sites already do:
```bash
SCORED=$(printf '%s' "$FINDINGS_ENVELOPE_JSON" | python3 -E -s "${SCORE_PY:?score.py path is empty}")
[ -n "$GUARD_PY" ] && python3 -E -s "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"
```
and extend the isolation test to assert that no `python3 "$GUARD_PY"|"$CONFIG_PY"|"$SCORE_PY"` appears without a same-command emptiness check.

### WR-03: The isolation scan cannot see several ordinary ways of writing an unisolated command

**File:** `plugins/vibe-check/scripts/test_inline_python_isolated.py:36-38` (`_PY`), used by `test_every_inline_invocation_carries_dash_capital_i` (line 148) and the count pin (line 140)
**Issue:** The docstring says every inline invocation, "(and `-m`, or a script read from stdin)", must carry `-I`, and the count pin says a change "must be seen". Calling `inline_invocations` / `missing_isolation` directly on the following text returned zero invocations and zero misses for each, so both tests would stay green if any of them were added to an instruction file:

| Text | Why it matters |
|---|---|
| `python3 -X utf8 -c '…'`, `python3 -W ignore -c '…'` | any option that takes a value hides the command |
| `python3 -Bc '…'` | combined short options |
| `python3 \`⏎`  -c '…'` | line continuation before `-c` |
| `python3 <<'PY'` … `PY`, `printf x \| python3`, `python3 < prog.py` | a script on stdin without the `-` word; confirmed to import a planted `json.py` |
| `"$PYTHON" -c '…'`, `${PYTHON:-python3} -c '…'` | interpreter named through a variable |
| `python3 scripts/score.py`, `python3 helper.py` | a relative script path resolves inside the reviewed repo |

`30-collect-score.md:119` still describes "the mode-5 `python3` heredoc" as the reference shape, so the heredoc form is a plausible thing to be written again.

Two smaller holes in the same scan: it accepts `python3 -I -c 'import sys; sys.path.insert(0, ""); …'` and `PYTHONPATH=. python3 -I -c …` as isolated (harmless today, both are), and `instruction_files()` (lines 54-69) only reads files with seven listed extensions, so a fence in a file with any other extension is never scanned.
**Fix:** Invert the rule: find every command word `python`/`python3`/`python3.N` (and `"$…"`-named interpreters if any are ever introduced) in Bash fences, and require each to be either `-I -c` / `-I -m`, or followed by a double-quoted argument starting with `$VC_ROOT/`, `$GUARD_PY`, `$CONFIG_PY` or `$SCORE_PY`. Anything else fails. Add the table rows above to `test_the_scan_catches_each_form` with an expected count of 1.

## Info

### IN-01: `-I` drops `PYTHONUTF8` / `PYTHONIOENCODING`, so inline commands and helpers can now disagree on encoding

**File:** `plugins/vibe-check/phases/deep-review/30-codex-collect.md:44` (also the stdin readers at `50-fix-loop.md:142,151,189`, `90-finalize.md:188,226,236`, `2c-codex-kickoff.md:37`)
**Issue:** Measured: with `LC_ALL=en_US.ISO8859-1 PYTHONUTF8=1`, the bare command read UTF-8 and the `-I` command read ISO-8859-1 (text arrives garbled, or fails to decode under other non-UTF-8 locales). Under UTF-8 and C locales there is no difference, which covers a normal macOS setup. The Codex payload is the one input likely to hold non-ASCII text, and `open(sys.argv[1])` uses the locale default; a decode failure there exits 3 and Codex's findings are dropped as "untranslatable".
**Fix:** Name the encoding where files are opened or stdin is read as JSON: `open(sys.argv[1], encoding="utf-8")`; for stdin, `json.load(sys.stdin.buffer)`.

### IN-02: `05-state.md` tells an `--all` run about its replacement key only after both default key fences

**File:** `plugins/vibe-check/phases/review/05-state.md:30` (context for the new print at `05-state-all.md:24`)
**Issue:** The instruction to read `05-state-all.md` comes after the two default fences and says it "REPLACES the state-key resolution above". If a run executes the "Other modes" fence before reaching that line, the conversation holds two `STATE_FILE=` lines (the flat key and the `--all` key). The reworded sentences in `90-finalize.md` and `50-fix-loop.md` say which one to use, so the harm is limited; before this range the flat one was the only one. Not reproduced: it depends on reading order.
**Fix:** Move the `--all` sentence above the two key bullets, or open each bullet with "not on `--all`".

### IN-03: The `--all` guard cannot trip on real input, and its message names causes that cannot apply

**File:** `plugins/vibe-check/phases/review/05-state-all.md:23-25`
**Issue:** `statepath.py` returns a fixed prefix plus a 12-hex digest, so no folder, branch or phase name reaches `$STATE_FILE`; the test needs a stub `statepath.py` to trip the guard. Keeping the guard as defence in depth is reasonable, but the message ("repo folder, branch or phase") would mislead if it ever fired. Separately, `STATE_FILE=` is printed before `mkdir -p`; if `mkdir` fails the fence exits non-zero with a printed path and no halt message.
**Fix:** Reword the message for this site ("the state path returned by statepath.py holds …"), and run `mkdir -p … || { echo "… review HALTED." >&2; exit 1; }` before the print.

### IN-04: Six of the twelve inline programs are tested for "does not import the planted module" only

**File:** `plugins/vibe-check/scripts/test_inline_python_isolated.py:217-235`
**Issue:** `test_every_other_program_in_the_fences` feeds placeholder arguments and ignores the exit code and output, so it proves the planted module is not imported but not that the program still works under `-I`. The two `05-state-all.md` programs are covered end to end by the new C1 tests; the four in `01d-coverage.md`, `2c-codex-kickoff.md` and `30-codex-collect.md` are not covered by this file. I ran those shapes by hand and they work.
**Fix:** Give each of the four a real input and assert its output, as `test_finalize_and_fix_loop_commands` does.

## Set aside (needs ruling)

### SA-01: A narrowed `--all` run can share the whole-tree key if `$NARROW` is not pasted into the fence

**Where:** `plugins/vibe-check/phases/review/05-state-all.md:19`
**Why excluded:** The line is unchanged in this range. `"${NARROW:-}"` falls back to empty in a fresh Bash call, silently. `$NARROW` is a value the model remembers from the arguments, not one a fence prints, so the cross-call check does not cover it, and the new C1 tests only exercise the whole-tree case.
**Effect if left as is:** `--all src/**` and a whole-tree `--all` on the same branch would write the same state file; a later close-out could act on the other run's findings.
**Needs:** ruling from the developer: in scope / defer / accept.

### SA-02: `python3` itself may be chosen or extended by files in the reviewed repo

**Where:** every `python3` call; not specific to a line
**Why excluded:** Not testable here (no version manager shim installed on this machine) and not part of the range. Version managers (pyenv, asdf, mise) pick the interpreter from `.python-version` / `.tool-versions` in the working directory, and an owner who starts the session with the reviewed repo's virtual environment active runs that environment's `python3`, whose `site-packages` `.pth` files execute even under `-I`.
**Effect if left as is:** In those setups a reviewed repo influences which interpreter, and which startup files, run the review's commands.
**Needs:** ruling from the developer: in scope / defer / accept (an absolute interpreter path resolved once at bootstrap would close it).

### SA-03: `git` and `node` calls beside the inline commands were not examined for repo-controlled execution

**Where:** `plugins/vibe-check/phases/deep-review/2c-codex-kickoff.md:36,60-74`, `30-codex-collect.md:39-40`
**Why excluded:** Outside the range and outside what I tested. A repo received as an archive (not a clone) can carry a `.git/config` that names programs for git to run. `node` is started on a path under `$HOME/.claude/plugins`, which the repo does not control.
**Effect if left as is:** Unknown; not assessed.
**Needs:** ruling from the developer: in scope / defer / accept.

### SA-04: Carried from the first review, unchanged by this range

**Where:** `63-REVIEW.md` SA-01 (folder names with a space or quote in non-`--all` modes), SA-02 (`30-collect-score.md` reads `"$STATE_FILE"` without naming the literal; pinned exception C2), WR-02 (empty phase id), WR-03 (deny-list guard)
**Why excluded:** Not touched by this range; listed so they are not read as resolved.
**Effect if left as is:** As recorded there.
**Needs:** ruling from the developer: in scope / defer / accept.

---

_Reviewed: 2026-11-15T21:39:16Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
