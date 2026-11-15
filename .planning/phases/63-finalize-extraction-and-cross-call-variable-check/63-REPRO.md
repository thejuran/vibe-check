# Phase 63 — Cross-call reproduction record

**6 places flagged. 6 reproduced. 0 did not reproduce.**

| Outcome class | Places |
|---------------|--------|
| stop | 2 (X1, X3) |
| wrong-file | 1 (X2) |
| ignored-setting | 3 (X4, X5, X6) |
| harmless | 0 |

Proposed split: 3 fix (X1, X2, X3), 3 for the owner to decide (X4, X5, X6), 0 pin.

**Nothing has been changed.** No instruction file under `plugins/vibe-check/phases/` was edited; the three files are byte-identical to `dd8e4ab`. The owner confirms the fix/pin split in plan 63-09, and the fixes land in plan 63-10.

- **Date:** 2026-11-14
- **HEAD when recorded:** `9efb67d` (the commit that completed `REPRO_63` and its fixtures; added in `7a520bb` / `2aa59df` for X1 to X3 and `c34bad8` / `9efb67d` for X4 to X6).
- **Scope of evidence:** local pytest runs only. No live review, no paid run, no network. Each Bash block was taken from the live instruction file and run in throwaway git repos built with `gitfixture` (null global and system git config).
- **In-suite record:** `test_cross_call_vars.REPRO_63` (six rows), locked by `TestRepro63Record`: every exception id has exactly one row with the same file and variable, every row names a `TestRepro63` test that exists, every outcome is one of the four classes, and every proposal follows the rule below. Mutants: a removed row, a misspelled fixture name, an unknown outcome word and a proposal off the rule each trip the lock with their own message.

## Repro standard

The same four steps were applied to every flagged place (D-17):

1. **Fresh run.** The Bash block that sets the shell variable and each Bash block that later reads it are taken from the real file (each found by a piece of its own text; the test fails if that text is gone). Each block runs as its own shell, the way each Bash call runs during a review. The shell gets only the program search path, the plugin folder, a private temp folder and the two helper paths the bootstrap step sets up (the path-safety helper and the settings reader), inside a temp git repo prepared as the instruction expects. Where the instruction tells the model to type in a value (the phase name, the Close-out flag, the owner's command-line options), that value is typed in. The shell variable under test is not supplied.
2. **Control run.** The same blocks, same setup, all in one shell. The control must finish as the instruction intends; if it does not, the test fails as a broken fixture rather than counting as a reproduction.
3. **Outcome class**, from exit codes, printed output and the files on disk:
   - **stop**: a fresh block fails where the control does not; the review halts.
   - **wrong-file**: the fresh run leaves different files on disk than the control (it reads, writes or moves the wrong thing, or nothing).
   - **ignored-setting**: everything finishes and the files agree, but the printed result shows a setting had no effect where the control's shows it did.
   - **harmless**: same exit codes, same output, same files.
4. **Reproduced** means any class other than harmless. A silently ignored setting counts as reproduced.

Proposed disposition rule (the owner confirms it in 63-09): stop and wrong-file → fix (a broken required workflow or a wrong file, as 999.25 was classed); ignored-setting → owner decides; harmless → pin.

Two notes on the setup. The settings block (06-config.md) prints nothing, so the same one observation line, `printf 'CONFIG_JSON=%s\n' "$CONFIG_JSON"`, is added after it in both runs; it changes nothing the block does. Both copies of the repo are named `repo`, so a state-file name built from the repo's folder name is the same in both runs.

## Known limits

- The check covers plugins/vibe-check/phases/ only; command and agent files are not scanned.
- The check is same-file: a read whose setter is in another file is not checked.

---

## X1 — phases/review/00-scope.md: PHASE_DIR

**Verdict:** REPRODUCED at `9efb67d` — stop

**What the owner would see.** A review of a GSD phase stops at the safety check with "Phase resolution escaped .planning/ — refusing." even though the phase exists.

**Proposed:** fix

**Fixture.** `TestRepro63.test_x1_phase_dir`

The block that finds the phase folder keeps it in a shell variable. The next block, the containment check, runs in a new shell where that variable is empty, so it checks the repo root instead of the phase folder, and refuses. Had the third block been reached, git refuses an empty path, and the phase would be reviewed as uncommitted changes only, with no commits counted.

**Command and output:**

```
$ pytest -q -p no:cacheprovider "test_cross_call_vars.py::TestRepro63::test_x1_phase_dir"
1 passed in 0.19s

Fresh run (phase id "02" typed in for <arg>; repo has .planning/phases/02-code-review committed):
--- block 1 (lines 86-92): PHASE_DIR=$(find ... -name "02" ...) ...
exit 0
--- block 2 (lines 100-101): [ -n "$GUARD_PY" ] && python3 "$GUARD_PY" --root "$PWD/.planning" --path "$PWD/$PHASE_DIR" || { ...; exit 1; }
exit 1
stdout:
refused: path resolves outside root
Phase resolution escaped .planning/ — refusing.
--- block 3 (lines 109-118): PHASE_START=$(git log --reverse --format=%H -- "$PHASE_DIR" | head -1) ...
exit 0
stdout:
ℹ Phase dir '' has no commit history yet — using staged + unstaged diff only for this pass.
PHASE_START=
stderr:
fatal: empty string is not a valid pathspec. please use . instead if you meant to match all paths

Control (the same 3 blocks in one shell):
exit 0
stdout:
contained
PHASE_START=d0ff18fd95380c824ce718609c638be39738583a
```

---

## X2 — phases/review/05-state.md: LEGACY_STATE_FILE

**Verdict:** REPRODUCED at `9efb67d` — wrong-file

**What the owner would see.** A review whose saved progress is still in the old location is not moved forward, so it starts again at pass 1 instead of carrying on.

**Proposed:** fix

**Fixture.** `TestRepro63.test_x2_legacy_state_file` (two cases: the GSD phase key and the repo-and-branch key)

The block that names the old and new state files keeps both names in shell variables. The move-forward block runs in a new shell, gets two empty names, finds nothing to move and says nothing. The old file stays where it was and no file is made in the new location. The new-location name (`STATE_FILE`) is empty in the same block; that variable's own effect is recorded under X3.

**Command and output:**

```
$ pytest -q -p no:cacheprovider "test_cross_call_vars.py::TestRepro63::test_x2_legacy_state_file"
1 passed, 2 subtests passed in 0.32s

GSD phase key (02-code-review typed in for ${PHASE_ID}; old file .turingmind/state/02-code-review.json present):
Fresh run:
--- block 1 (lines 9-10): LEGACY_STATE_FILE=".turingmind/state/02-code-review.json" / STATE_FILE=".turingmind/state/format-53/02-code-review.json"
exit 0
--- block 2 (lines 28-33): if python3 "$VC_ROOT/scripts/review_archive.py" migrate --legacy "$LEGACY_STATE_FILE" --current "$STATE_FILE"; then ...
exit 0
(no output)
files after: .turingmind/state/02-code-review.json, src/a.txt

Control (the same 2 blocks in one shell):
exit 0
stdout:
state migrated forward to .turingmind/state/format-53/02-code-review.json; the previous file was archived as .turingmind/state/02-code-review.json.migrated-format-53
files after: .turingmind/state/02-code-review.json.migrated-format-53, .turingmind/state/format-53/02-code-review.json, src/a.txt

Repo-and-branch key (lines 17-19; repo "repo", branch "main"):
Fresh run: block 1 exit 0, block 2 exit 0, no output; files after: .turingmind/state/repo-main.json, src/a.txt
Control: exit 0
stdout:
state migrated forward to .turingmind/state/format-53/repo-main.json; the previous file was archived as .turingmind/state/repo-main.json.migrated-format-53
files after: .turingmind/state/format-53/repo-main.json, .turingmind/state/repo-main.json.migrated-format-53, src/a.txt
```

---

## X3 — phases/review/05-state.md: STATE_FILE

**Verdict:** REPRODUCED at `9efb67d` — stop

**What the owner would see.** A second pass of a review stops with "the state file's last-pass head_sha is not a commit sha" although the saved progress is fine.

**Proposed:** fix

**Fixture.** `TestRepro63.test_x3_state_file` (three cases: the GSD phase key, the repo-and-branch key, and a Close-out run on the GSD key)

The three blocks that read the saved state (the last reviewed commit, the decided list, the deferred list) each run in a new shell where the state-file name is empty, so the shell cannot open it and each block halts with its own message. The first halt blames the commit id in the file, which is not the cause. On a Close-out run the commit block does nothing, but the decided and deferred blocks still halt, so Close-out stops too.

**Command and output:**

```
$ pytest -q -p no:cacheprovider "test_cross_call_vars.py::TestRepro63::test_x3_state_file"
1 passed, 3 subtests passed in 0.69s

GSD phase key (02-code-review typed in for ${PHASE_ID}; "0" typed in for "$FINALIZE_MODE"):
Fresh run:
--- block 1 (lines 9-10): the two state-file names
exit 0
--- block 2 (lines 28-33): migrate
exit 0
--- block 3 (lines 54-61): elif LAST_REVIEWED_SHA=$(python3 "$VC_ROOT/scripts/carry_state.py" last-head-sha < "$STATE_FILE"); then ...
exit 1
stderr:
bash: line 3: : No such file or directory
Review halted — the state file's last-pass head_sha is not a commit sha; nothing was scored. Set that pass's head_sha to the full 40-hex sha of the last reviewed commit (or restore the state file from git) and re-run; --finalize does not read this value and still works.
--- block 4 (lines 76-81): if DECIDED_HASHES=$(python3 "$VC_ROOT/scripts/carry_state.py" decided < "$STATE_FILE"); then ...
exit 1
stderr:
bash: line 1: : No such file or directory
I'm uncertain about the carry-forward — carry_state.py decided failed; stopping before any HEAD read.
--- block 5 (lines 87-92): if DEFERRED_HASHES=$(python3 "$VC_ROOT/scripts/carry_state.py" deferred < "$STATE_FILE"); then ...
exit 1
stderr:
bash: line 1: : No such file or directory
I'm uncertain about the carry-forward — carry_state.py deferred failed; stopping before any HEAD read.

Control (the same 5 blocks in one shell):
exit 0
stdout:
state migrated forward to .turingmind/state/format-53/02-code-review.json; the previous file was archived as .turingmind/state/02-code-review.json.migrated-format-53
LAST_REVIEWED_SHA=b5015d510ac3358c26b507cf03ae33ef61f5e3b8
[]
[]

Repo-and-branch key (lines 17-19): fresh exits 0, 0, 1, 1, 1 with the same three halt messages; control exit 0 with
LAST_REVIEWED_SHA=b5015d510ac3358c26b507cf03ae33ef61f5e3b8, [], [].

Close-out on the GSD key ("1" typed in for "$FINALIZE_MODE"): fresh exits 0, 0, 0, 1, 1 (the decided and deferred
halts above); control exit 0, prints the migrate line then [] and [] and no LAST_REVIEWED_SHA= line.
```

---

## X4 — phases/review/06-config.md: CODEX_FLAG_VAL

**Verdict:** REPRODUCED at `9efb67d` — ignored-setting

**What the owner would see.** Asking for "--codex off" has no effect: the review runs with the Codex setting on its default instead.

**Proposed:** owner decides

**Fixture.** `TestRepro63.test_x4_codex_flag_val`

The block that reads the Codex option from the command keeps it in a shell variable. The block that calls the settings reader runs in a new shell, passes an empty option, and the reader returns its default, "auto".

**Command and output:**

```
$ pytest -q -p no:cacheprovider "test_cross_call_vars.py::TestRepro63::test_x4_codex_flag_val"
1 passed in 0.12s

Fresh run ("--min-confidence 45 --codex off" typed in for "$ARGUMENTS"):
--- block 1 (line 27): CODEX_FLAG_VAL=$(printf '%s' "--min-confidence 45 --codex off" | sed -n 's/.*--codex[ =]\([^ ]*\).*/\1/p')
exit 0
--- block 2 (lines 44-50, plus the observation line): CONFIG_JSON=$(REPO_ROOT="$CONFIG_REPO_ROOT" ... CODEX_FLAG="$CODEX_FLAG_VAL" python3 "$CONFIG_PY") ...
exit 0
stdout:
CONFIG_JSON={"values": {"thresholds": null, "disabled": [], "top_model": null, "min_confidence": null, "idiom_floor": "medium", "codex": "auto"}, "warnings": []}

Control (the same 2 blocks in one shell):
exit 0
stdout:
CONFIG_JSON={"values": {"thresholds": null, "disabled": [], "top_model": null, "min_confidence": null, "idiom_floor": "medium", "codex": "off"}, "warnings": []}
```

---

## X5 — phases/review/06-config.md: CONFIG_REPO_ROOT

**Verdict:** REPRODUCED at `9efb67d` — ignored-setting

**What the owner would see.** The repo's settings file is not read at all, so every setting in it is silently replaced by the defaults.

**Proposed:** owner decides

**Fixture.** `TestRepro63.test_x5_config_repo_root`

The block that finds the repo root keeps it in a shell variable. The settings-reader block runs in a new shell with an empty root. The reader does not refuse (the plan expected a refusal might count as a stop): it treats an empty root as "no settings file" and returns the defaults with no warning. The fixture's repo settings file disables one agent (`[agents] disabled = ["style"]`); the fresh run drops that.

**Command and output:**

```
$ pytest -q -p no:cacheprovider "test_cross_call_vars.py::TestRepro63::test_x5_config_repo_root"
1 passed in 0.13s

Fresh run (repo has .vibe-check.toml with [agents] disabled = ["style"]):
--- block 1 (line 15): CONFIG_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
exit 0
--- block 2 (lines 44-50, plus the observation line): CONFIG_JSON=$(REPO_ROOT="$CONFIG_REPO_ROOT" ... python3 "$CONFIG_PY") ...
exit 0
stdout:
CONFIG_JSON={"values": {"thresholds": null, "disabled": [], "top_model": null, "min_confidence": null, "idiom_floor": "medium", "codex": "auto"}, "warnings": []}

Control (the same 2 blocks in one shell):
exit 0
stdout:
CONFIG_JSON={"values": {"thresholds": null, "disabled": ["style"], "top_model": null, "min_confidence": null, "idiom_floor": "medium", "codex": "auto"}, "warnings": []}
```

---

## X6 — phases/review/06-config.md: MIN_CONFIDENCE_FLAG_VAL

**Verdict:** REPRODUCED at `9efb67d` — ignored-setting

**What the owner would see.** Asking for "--min-confidence 45" has no effect: no low-confidence finding is filtered out.

**Proposed:** owner decides

**Fixture.** `TestRepro63.test_x6_min_confidence_flag_val`

The block that reads the minimum-confidence option keeps it in a shell variable. The settings-reader block runs in a new shell, passes an empty option, and the reader returns no filter.

**Command and output:**

```
$ pytest -q -p no:cacheprovider "test_cross_call_vars.py::TestRepro63::test_x6_min_confidence_flag_val"
1 passed in 0.12s

Fresh run ("--min-confidence 45 --codex off" typed in for "$ARGUMENTS"):
--- block 1 (line 21): MIN_CONFIDENCE_FLAG_VAL=$(printf '%s' "--min-confidence 45 --codex off" | sed -n 's/.*--min-confidence[ =]\([^ ]*\).*/\1/p')
exit 0
--- block 2 (lines 44-50, plus the observation line): CONFIG_JSON=$(... MIN_CONFIDENCE_FLAG="$MIN_CONFIDENCE_FLAG_VAL" ... python3 "$CONFIG_PY") ...
exit 0
stdout:
CONFIG_JSON={"values": {"thresholds": null, "disabled": [], "top_model": null, "min_confidence": null, "idiom_floor": "medium", "codex": "auto"}, "warnings": []}

Control (the same 2 blocks in one shell):
exit 0
stdout:
CONFIG_JSON={"values": {"thresholds": null, "disabled": [], "top_model": null, "min_confidence": 45, "idiom_floor": "medium", "codex": "auto"}, "warnings": []}
```

---

## Proposed split

| Id | File | Variable | Outcome | Proposed |
|----|------|----------|---------|----------|
| X1 | phases/review/00-scope.md | PHASE_DIR | stop | fix |
| X2 | phases/review/05-state.md | LEGACY_STATE_FILE | wrong-file | fix |
| X3 | phases/review/05-state.md | STATE_FILE | stop | fix |
| X4 | phases/review/06-config.md | CODEX_FLAG_VAL | ignored-setting | owner decides |
| X5 | phases/review/06-config.md | CONFIG_REPO_ROOT | ignored-setting | owner decides |
| X6 | phases/review/06-config.md | MIN_CONFIDENCE_FLAG_VAL | ignored-setting | owner decides |

---

## What each fix would add

Written 2026-11-15 in plan 63-09, before the owner decides. The extraction is judged on its own (D-16): at the extraction-only commit `c7d92c9` the Finalize path went from 92 to 83 counted steps and from 136114 to 129451 bytes, verdict PASS (63-COUNTS.md, `## After the extraction alone`). Any fix below lands later (plan 63-10) and is reported as named growth by file, bytes and reproduction (D-09); it does not change that verdict.

**Which paths load these files.** All three files are loaded by every review path `footprint.py` knows at `c7d92c9`: plain review, plain review `--all`, deep review, deep review `--all`, Finalize and the fix loop. Bytes added to any of them are added to all six.

**How the figures are estimated.** These are estimates of a likely fix, not measurements; plan 63-10 measures the real ones with `step_count.py` and `footprint.py`. Steps: the counting rule (rule v1, per file) counts a pasted value only for printed names ending in `FILE`, so a fix that prints such a name adds one counted step for each later Bash block in the same file that uses it; a fix for any other name adds bytes but no counted step; a fix that merges two Bash blocks removes one. Bytes: a fix of the "print the value, then paste it into the later block" kind adds one `printf` line per setting block (about 40-50 bytes each) and a sentence telling the model to substitute the printed value (about 150-250 bytes, once per file if one sentence covers every later block). A merge removes the fence lines (about 12 bytes per removed block) and adds little or no text.

| Id | File | Likely fix | Paths that load it | Bytes added (est.) | Counted steps added on the Finalize path (est.) |
|----|------|-----------|--------------------|--------------------|-------------------------------------------------|
| X1 | phases/review/00-scope.md (`PHASE_DIR`) | print `PHASE_DIR=` after the phase is found; the containment check and the phase-range block substitute the printed value | all six | about +250 to +450 | 0 (the name does not end in `FILE`) |
| X2 | phases/review/05-state.md (`LEGACY_STATE_FILE`) | print `LEGACY_STATE_FILE=` in both naming blocks; the move-forward block substitutes it | all six | about +100 to +250 (shares the X3 sentence) | +1 (the move-forward block) |
| X3 | phases/review/05-state.md (`STATE_FILE`) | print `STATE_FILE=` in both naming blocks; the move-forward, last-commit, decided and deferred blocks substitute it | all six | about +250 to +450 | +4 (move-forward, last-commit, decided, deferred) |
| X4 | phases/review/06-config.md (`CODEX_FLAG_VAL`) | move the `--codex` read into the settings-reader block (merge) | all six | about 0 to +100 | −1 (one block merged away) |
| X5 | phases/review/06-config.md (`CONFIG_REPO_ROOT`) | move the repo-root read into the settings-reader block (merge) | all six | about 0 to +100 | −1 |
| X6 | phases/review/06-config.md (`MIN_CONFIDENCE_FLAG_VAL`) | move the `--min-confidence` read into the settings-reader block (merge) | all six | about 0 to +100 | −1 |

Totals if every place is fixed: about +600 to +1450 bytes on each of the six paths, and about +5 − 3 = +2 counted steps on the Finalize path (the same +2 on every path, since all six load these files). Fixing X1-X3 only: about +600 to +1150 bytes and +5 counted steps. The X4-X6 fixes are cheapest because the settings-reader block can read the three values itself; a fix of the print-and-paste kind instead would add about +300 to +500 bytes and no counted step.

Known limit that bears on X3: `phases/shared/90-finalize.md` also reads `"$STATE_FILE"` in its own Bash blocks, but its setter is in `05-state.md`, and the check is same-file only, so that read is not flagged or reproduced here. A fix that prints `STATE_FILE=` would give the Finalize blocks a value to substitute as well; whether 63-10 extends the substitution there is a measurement for 63-10, not part of this estimate.
