# Phase 63 — Cross-call reproduction record

**6 places flagged. 6 reproduced. 0 did not reproduce.**

| Outcome class | Places |
|---------------|--------|
| stop | 2 (X1, X3) |
| wrong-file | 1 (X2) |
| ignored-setting | 3 (X4, X5, X6) |
| harmless | 0 |

Proposed split: 3 fix (X1, X2, X3), 3 for the owner to decide (X4, X5, X6), 0 pin.

**All six fixed in plan 63-10** (owner decision below: fix all six). Before 63-10 nothing had been changed and the three files were byte-identical to `dd8e4ab`. The cross-call exceptions list in `test_cross_call_vars.py` is now empty. Each `TestRepro63` fixture now asserts the repaired behaviour (fresh calls, with each printed literal substituted, match the one-shell control) and fails on the pre-fix files (see "Reverse run" at the end). One cross-file read that the same-file check cannot see does reproduce and awaits an owner decision (see "Open item" at the end).

**Follow-up (D-20, D-21), 2026-11-15.** The open item is fixed (X7), the fix loop reproduced the same gap and is fixed (X8), a cross-file companion check now flags a read of a name only another file sets (two places flagged and not decided: C1, C2), and the printed names are guarded against shell-live characters (D-21). See the four sections at the end.

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
- The check is same-file: a read whose setter is in another file is not checked. **Since the D-20 follow-up** a companion check covers that case in part: it requires the reading file to name the printed literal (`NAME=`) and the setting file to print it, but it does not check the order in which the files run (`test_cross_call_vars.py::TestCrossFile`).

---

## X1 — phases/review/00-scope.md: PHASE_DIR

**Verdict:** REPRODUCED at `c7d92c9` → fixed by 63-10 (stop; first recorded at `9efb67d`)

- **Fix shape:** print and substitute
- **Green at:** `c4c84a3`
- **Reverse run:** `TestRepro63.test_x1_phase_dir`, flipped to the repaired expectation, fails on the pre-fix files at `c7d92c9` and passes at `c4c84a3`.

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

**Verdict:** REPRODUCED at `c7d92c9` → fixed by 63-10 (wrong-file; first recorded at `9efb67d`)

- **Fix shape:** print and substitute (one edit with X3)
- **Green at:** `7bd3274`
- **Reverse run:** `TestRepro63.test_x2_legacy_state_file`, flipped to the repaired expectation, fails on the pre-fix files at `c7d92c9` and passes at `7bd3274`.

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

**Verdict:** REPRODUCED at `c7d92c9` → fixed by 63-10 (stop; first recorded at `9efb67d`)

- **Fix shape:** print and substitute (one edit with X2)
- **Green at:** `7bd3274`
- **Reverse run:** `TestRepro63.test_x3_state_file`, flipped to the repaired expectation, fails on the pre-fix files at `c7d92c9` and passes at `7bd3274`.

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

**Verdict:** REPRODUCED at `c7d92c9` → fixed by 63-10 (ignored-setting; first recorded at `9efb67d`)

- **Fix shape:** merge (one edit with X5 and X6)
- **Green at:** `936d29e`
- **Reverse run:** `TestRepro63.test_x4_codex_flag_val`, flipped to the repaired expectation, fails on the pre-fix files at `c7d92c9` and passes at `936d29e`.

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

**Verdict:** REPRODUCED at `c7d92c9` → fixed by 63-10 (ignored-setting; first recorded at `9efb67d`)

- **Fix shape:** merge (one edit with X4 and X6)
- **Green at:** `936d29e`
- **Reverse run:** `TestRepro63.test_x5_config_repo_root`, flipped to the repaired expectation, fails on the pre-fix files at `c7d92c9` and passes at `936d29e`.

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

**Verdict:** REPRODUCED at `c7d92c9` → fixed by 63-10 (ignored-setting; first recorded at `9efb67d`)

- **Fix shape:** merge (one edit with X4 and X5)
- **Green at:** `936d29e`
- **Reverse run:** `TestRepro63.test_x6_min_confidence_flag_val`, flipped to the repaired expectation, fails on the pre-fix files at `c7d92c9` and passes at `936d29e`.

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

---

## Owner decision

- **Date:** 2026-11-15
- **Option chosen, in the owner's words:** "Fix all six (Recommended)" (option `fix-all-reproduced`).
- **How it arrived:** the owner's answer to the phase coordinator's question, relayed to the 63-09 executor by the coordinator with the exact quote above. The question stated: all six were reproduced; fixing all adds roughly 600 to 1,450 bytes to every review and a net +2 counted steps; the settings fixes are the cheapest and each removes a step; X5 matters most.
- **Effect:** every reproduced place is fixed in this phase (plan 63-10); none is pinned. No place was harmless, so nothing is pinned by rule either. The exceptions list is expected to end empty once 63-10 lands.

| Id | File | Variable | Disposition |
|----|------|----------|-------------|
| X1 | phases/review/00-scope.md | PHASE_DIR | fix |
| X2 | phases/review/05-state.md | LEGACY_STATE_FILE | fix |
| X3 | phases/review/05-state.md | STATE_FILE | fix |
| X4 | phases/review/06-config.md | CODEX_FLAG_VAL | fix |
| X5 | phases/review/06-config.md | CONFIG_REPO_ROOT | fix |
| X6 | phases/review/06-config.md | MIN_CONFIDENCE_FLAG_VAL | fix |

---

## Reverse run (63-10)

- **Date:** 2026-11-15
- **How:** a detached scratch worktree at `c7d92c9` (the extraction-only commit, before any fix), with the 63-10 `test_cross_call_vars.py` copied in; `pytest -q -p no:cacheprovider test_cross_call_vars.py -k "TestRepro63 and not Record"`; the worktree was then removed.
- **Result:** every flipped fixture fails on the pre-fix files:

```
FAILED TestRepro63::test_x1_phase_dir                       (0 PHASE_DIR= lines printed)
SUBFAILED(mode='gsd')    TestRepro63::test_x2_legacy_state_file
SUBFAILED(mode='branch') TestRepro63::test_x2_legacy_state_file
SUBFAILED(mode='gsd')    TestRepro63::test_x3_state_file
SUBFAILED(mode='branch') TestRepro63::test_x3_state_file
SUBFAILED(mode='gsd, --finalize') TestRepro63::test_x3_state_file
FAILED TestRepro63::test_x4_codex_flag_val                  ('auto' != 'off')
FAILED TestRepro63::test_x5_config_repo_root                ([] != ['style'])
FAILED TestRepro63::test_x6_min_confidence_flag_val         (None != 45)
9 failed, 2 passed, 57 deselected
```

(The 2 passed are the X2 and X3 parent tests, whose subtests carry the failures.) At the 63-10 fix commits the same fixtures pass.

| Id | Disposition |
|----|-------------|
| X1 | reproduced; fixed by 63-10 |
| X2 | reproduced; fixed by 63-10 |
| X3 | reproduced; fixed by 63-10 |
| X4 | reproduced; fixed by 63-10 |
| X5 | reproduced; fixed by 63-10 |
| X6 | reproduced; fixed by 63-10 |

---

## Open item: `$STATE_FILE` read in `phases/shared/90-finalize.md` (needs an owner decision)

**Verdict:** REPRODUCED at `936d29e` (the last 63-10 fix commit). → **Fixed by the 63-10 follow-up (owner decision D-20), recorded as X7** — see "X7 — Close out (D-20)" below. The text of this section is kept as first written.

**What the owner would see.** `--finalize` (Close out) on a review with saved progress says there are no prior review passes and stops without writing `REVIEW.md`, although the state file is there.

**Why the check missed it.** `90-finalize.md` reads `"$STATE_FILE"`, but the value is set in `phases/review/05-state.md`. The cross-call check looks within one file only (its known limit), so this read was never flagged.

**How it was checked.** The same standard as above: the 05-state GSD-key block (`02-code-review` typed in for `${PHASE_ID}`; it now prints `STATE_FILE=`) and the 90-finalize Finalize-inputs block (its three `"<true|false>"` slots typed in as `"false"`), taken from the live files, in a temp git repo holding a pass-1 state file at `.turingmind/state/format-53/02-code-review.json`. `90-finalize.md` gives no instruction to substitute the printed `STATE_FILE=` literal, so the fresh Finalize block gets none. Scratch script only; nothing was added to the suite.

```
Fresh run:
--- block 1 (05-state, GSD key): exit 0
LEGACY_STATE_FILE=.turingmind/state/02-code-review.json
STATE_FILE=.turingmind/state/format-53/02-code-review.json
--- block 2 (90-finalize, Finalize inputs): exit 0
BLOBFILE=<tmp>/vc.XXXXXX
{"action": "error", "reason": "no prior review passes", "next": "stop-no-state", ...}
--- the archive block alone, fresh: exit 1
review_archive: could not archive : no file to archive: ;  was left in place
Finalize stopped — REVIEW.md was written, but the review state could not be archived and is still live at  (the line above says why). ...

Control (blocks 1 and 2 in one shell): exit 0
{"action": "write", "reason": "no outstanding findings; finalization may proceed", "next": "write-review-md", ...}
```

Outcome class by the rule above: the fresh exit codes are 0, the files agree and the output differs, so the classifier says ignored-setting. In effect it is a stop, because `stop-no-state` ends Close out before anything is written.

**Related, not run:** `phases/review/50-fix-loop.md` also reads `"$STATE_FILE"` in its own blocks (rows, record-decisions, payload, record-fix-verdicts) with no substitution sentence; `phases/review/30-collect-score.md` already says to substitute the literal state path. The same cross-file gap likely applies to the fix loop.

**What a fix would look like (for the owner's decision).** `05-state.md` now prints `STATE_FILE=` (63-10, X3), so a fix is one substitution sentence in `90-finalize.md` (and likewise in `50-fix-loop.md`). Because the name ends in `FILE`, counting rule v1 would count every `"$STATE_FILE"` use in those files as a paste step. That raises the Finalize step count above the extraction-only figure and changes bytes the equivalence record covers. Options: fix it in a follow-up plan (recommended, because Close out is a required workflow), or carry it to the backlog.

---

## X7 — phases/shared/90-finalize.md: STATE_FILE (Close out, D-20)

**Verdict:** REPRODUCED at `25dcb9d` (the open item above, now in the suite) → fixed at `9a01055` (wrong-file).

- **Fixture:** `TestRepro63.test_x7_finalize_state_file`. The 05-state GSD-key block (`02-code-review` typed in) runs fresh and prints `STATE_FILE=`; the Finalize-inputs block (its three slots typed in as `"false"`) runs fresh with the printed literal substituted **only if `90-finalize.md` names `STATE_FILE=`**; when the gate says `write` the harness writes `.turingmind/REVIEW.md` in the model's place and runs the archive block fresh the same way. Control: the same blocks in one shell, with one line standing in for the Write-tool step. The repo holds a pass-1 state file with no findings.
- **RED at `25dcb9d`:** `AssertionError: 'stop-no-state' != 'write-review-md'` — the Finalize JSON was `{"action": "error", "reason": "no prior review passes", "next": "stop-no-state", ...}`; no REVIEW.md, state not archived, while the control wrote REVIEW.md and archived the state (outcome class wrong-file: exit codes 0, files differ).
- **Fix:** one sentence added to the first bullet of `## Finalize mode`, mirroring the 63-10 sentence in `05-state.md`: "In every fence of this file, `"$STATE_FILE"` is the literal printed after `STATE_FILE=` by `05-state.md` — substitute it; a shell variable does not survive into a separate Bash call." (+185 bytes, 0 counted steps.) Nothing else in `90-finalize.md` changed: stop sentences, report text and fill rules are byte-identical; `test_finalize_card.py` (fill-rules checksum, moved-passage pin) passes.
- **GREEN at `9a01055`:** the fresh run returns `write-review-md`, exit codes `[0, 0, 0]`, REVIEW.md written, state archived, files identical to the control.
- **Five situations re-run:** `finalize_capture.py compare … --driver helper --commit 9a01055`: `finalize outcome fields match (5 situations, 7 walks)`. The driver supplies the state path itself, so the sentence changes no walk; `finalize_capture.py` and its tests needed no change.

## X8 — phases/review/50-fix-loop.md: STATE_FILE (fix loop, D-20)

**Verdict:** REPRODUCED at `25dcb9d` → fixed at `9a01055` (stop).

**What the owner would see.** The fix-loop card is never shown: the fix loop stops with "batch_card.py refused — fix loop cannot render its card; nothing was changed" although the saved progress is fine.

- **Fixture:** `TestRepro63.test_x8_fix_loop_state_file`. The same 05-state block, then the ordinary fix-loop rows block (with one observation line printing the rows file as `ROWS=`), fresh, substituting the printed literal only where `50-fix-loop.md` names `STATE_FILE=`; control in one shell.
- **RED at `25dcb9d`:** fresh exit codes `[0, 1]`; stderr `bash: line 6: : No such file or directory` then `batch_card.py refused — fix loop cannot render its card; nothing was changed`. Control exit 0.
- **Fix:** one sentence appended to the "Temp paths are literals" paragraph: "In every fence of this file, `"$STATE_FILE"` is the literal printed after `STATE_FILE=` by `05-state.md` — substitute it." (+124 bytes, 0 counted steps.) The same sentence covers the record-decisions, payload and record-fix-verdicts blocks of that file, which read the same name; only the rows block was run.
- **GREEN at `9a01055`:** fresh exit codes `[0, 0]`, the same `ROWS=` line as the control, the same files.

| Id | Disposition |
|----|-------------|
| X7 | reproduced; fixed by 63-10 (follow-up, D-20) |
| X8 | reproduced; fixed by 63-10 (follow-up, D-20) |

## Cross-file check (D-20)

`test_cross_call_vars.py::TestCrossFile` (`cross_file_flags`). Rule: a read in a phase file of a name that neither an earlier block of that file nor the same block before it sets, and that another phase file sets, is flagged unless the reading file names the printed literal (`` `NAME=` ``); a file that sets such a name and never prints it is flagged too. The four bootstrap names (`VC_ROOT`, `GUARD_PY`, `CONFIG_PY`, `SCORE_PY`) are left out: `01-bootstrap.md` prints them and tells every later phase to substitute the resolved paths. The flagged set must equal `CROSS_FILE_EXCEPTIONS`; a new flag and a stale entry both fail, so the list can only shrink. Mutants: the D-20 sentence removed from either file trips; an unlisted pair and a stale entry trip; synthetic files cover each rule.

Before the fix it flagged four places: X7, X8 and the two below. After it, the two below remain on the list.

| Id | File | Name | Why flagged | Status |
|----|------|------|-------------|--------|
| C1 | phases/review/05-state-all.md | STATE_FILE | sets `STATE_FILE` for `--all` (from `statepath.py`, a 12-hex key) and never prints it, while three other files read it | flagged, not reproduced / not decided |
| C2 | phases/review/30-collect-score.md | STATE_FILE | reads `"$STATE_FILE"` in the since-review fences; its prose says to substitute "the literal state path bound in Phase 0.5" but does not name `STATE_FILE=` | flagged, not reproduced / not decided |

Notes for the decision, not run: C1 means a `--all` review's Close out and fix loop have no printed `STATE_FILE=` to substitute, so the D-20 sentences point at a line `--all` does not print; the value itself is hex and cannot carry a shell-live character. C2 already tells the model to substitute the state path, so it is likely harmless; it is listed because it does not name the printed line.

## Pasted-name guard (D-21)

**What changed.** The `PHASE_DIR` block in `00-scope.md` and both state-file key blocks in `05-state.md` now refuse, before printing, a value holding `$`, a backtick, `"`, `\`, a newline or a carriage return: one `case` line per block (bash 3.2 safe, no `eval`, every expansion quoted) prints one line to stderr and exits 1, and no `NAME=` line is printed. Messages:

- `Review halted — the phase folder path holds $, `, ", \ or a line break; nothing was scored.`
- `Review halted — the state-file name (repo folder, branch or phase) holds $, `, ", \ or a line break; nothing was scored.`

**Tests** (`plugins/vibe-check/scripts/test_pasted_name_guard.py`, RED `dd9db3e`, GREEN `d168b85`). Real blocks, each in a fresh `/bin/bash -s` (3.2.57) inside a temp repo. A harness pastes whatever the setter printed into the later blocks and the test looks for a marker file the payload would `touch`.

- `00-scope.md`: phase folders `02-x$(touch${IFS}PWNED)`, ``02-x`touch PWNED` ``, `02-x";touch${IFS}PWNED;"`, `02-a\b`, `02-a<CR>b`, and a milestone folder `v1x$(touch${IFS}PWNED)-phases`. Each: exit 1, no `PHASE_DIR=` line, no marker after the guard and phase-range blocks run. Good names `02-code-review`, `02-my phase` (space) and `v1.2_(a)-phases/02-x+y,z` print and round-trip (guard `contained`, the right `PHASE_START=`).
- `05-state.md`, GSD key (`${PHASE_ID}` supplied raw from the environment): `$(…)`, backtick, `"`, `\`, newline, carriage return — each refused, no marker after the migrate, last-commit, decided and deferred blocks. Repo-and-branch key: branches `x$(touch${IFS}PWNED)`, ``x`touch${IFS}PWNED` ``, `x";touch${IFS}PWNED;"`, and repo folders holding `$(…)` or a backtick — each refused, no marker. (git refuses `\`, newline and carriage return in a branch name; `xargs basename` strips or splits them in a folder name, so they cannot reach that key.) Good names (`02-code-review`, `02-my phase`, branch `feat/x-1.2_(y)` in folder `repo.v2_(a)`) print, migrate and carry the last reviewed commit.
- **Mutation:** with the guard line removed, every bad case prints its `NAME=` line or creates the marker, and every `$(…)` / backtick case creates the marker (`test_without_the_guard_the_cases_fail`, passing on the guarded files).

**Paste sites of these names, and whether the print-site guard covers them:**

| Where the literal is pasted | Name | Covered |
|-----------------------------|------|---------|
| `00-scope.md` containment-guard and phase-range blocks | `PHASE_DIR` | yes (guard in the `PHASE_DIR` block) |
| `05-state.md` GSD key block, `${PHASE_ID}` typed in by the model | `PHASE_ID` (basename of `PHASE_DIR`) | yes, upstream: `PHASE_ID` is part of the guarded `PHASE_DIR`, so a bad name stops in `00-scope.md` first. The `05-state.md` guard runs after the assignment, so on its own it would not stop a `$(…)` typed into that block. |
| `05-state.md` migrate, last-commit, decided and deferred blocks | `LEGACY_STATE_FILE`, `STATE_FILE` | yes |
| `30-collect-score.md` since-review blocks (`--state "$STATE_FILE"`) — the scoring step's state-path paste | `STATE_FILE` | yes (the printed value is guarded) |
| `90-finalize.md` Finalize-inputs, rows, record-decisions and archive blocks | `STATE_FILE` | yes |
| `50-fix-loop.md` rows, record-decisions, payload and record-fix-verdicts blocks | `STATE_FILE` | yes |
| `05-state-all.md` (`--all`) | `STATE_FILE` | not needed: not printed (C1), and the value is a 12-hex key from `statepath.py`, which refuses unsafe components |
| `10-triage.md` `{{$PHASE_DIR}}`, `15-intent.md` `$PHASE_DIR/<doc>` | `PHASE_DIR` | not shell pastes (prompt text and a Read-tool path); they only ever see a value the guard let through |
| `00-scope.md` / `30-collect-score.md` `<ref>`, `<range>` | owner-typed arguments | not covered: they come from the owner's own command line, not from repo, branch or PR names; outside D-21 |

Names derived from a PR (`PR_HEAD`) were already filtered to hex where bound (`00-scope.md`); no other block tells the model to paste a literal derived from repo, branch or PR names.

## Review fixes (D-22, D-23), 2026-11-15

The sections above stay as recorded. This section supersedes the C1 row of "Cross-file check (D-20)" and the `05-state-all.md` row of the paste-site table.

### C1 — phases/review/05-state-all.md: STATE_FILE (`--all`, 63-REVIEW WR-01): reproduced; fixed

- **Reproduction** (`test_cross_call_vars.py::TestRepro63::test_c1_all_mode_close_out_state_file` and `test_c1_all_mode_fix_loop_state_file`, RED at `769fd8a`). A temp repo holds a pass-1 `--all` state file at the key `statepath.py` gives it (`.turingmind/state/format-53/by-mode/all/<12hex>.json`). The real `05-state-all.md` key block runs as its own `bash -s`; it printed no `STATE_FILE=` line, so the paste is empty. Close out (the Finalize-inputs block, run fresh with that empty paste) returned `{"action": "error", "reason": "no prior review passes", "next": "stop-no-state"}`; the one-shell control returned `write-review-md`. The fix-loop rows block run fresh exited 1 (`[0, 1]`) where the control exited 0. Outcome class: `wrong-file` (Close out writes nothing) and `stop` (fix loop).
- **Fix** (`d56232b`). `05-state-all.md` prints `STATE_FILE=` after binding the `--all` key, behind the same guard line as `05-state.md` (the value is a 12-hex key, but one rule at every print site is simpler to check). The Close-out and fix-loop sentences now read "printed after `STATE_FILE=` by `05-state.md` (`05-state-all.md` on `--all`)". C1 is off `CROSS_FILE_EXCEPTIONS` (only C2 remains) and has a `REPRO_63` row with disposition fixed.
- **After the fix:** Close out on `--all` gets `write-review-md`, writes REVIEW.md and archives the state, files identical to the control; the fix-loop rows block numbers the same card as the control.
- **Defence in depth, not changed (D-06).** The helper still reads `--state-file ""` as "no state file" (exit 0, `stop-no-state`), as 2.14.1 did; that gap stays carried (`test_gap_empty_state_file_path_is_no_state`). WR-01's root cause is fixed at the print site.

### CR-01 — inline Python imported a planted module from the reviewed repo (D-22): reproduced; fixed

- **Where.** Twelve inline `python3 -c` invocations, all run with the reviewed repo as the working directory: `phases/shared/90-finalize.md` (3), `phases/review/50-fix-loop.md` (3), `phases/review/05-state-all.md` (2), `phases/deep-review/2c-codex-kickoff.md` (2, one fed by `printf … |`), `phases/deep-review/30-codex-collect.md` (1), `phases/deep-review/01d-coverage.md` (1). No `python -c`, `python3 -m` or stdin-script (`python3 -`) form exists in any shipped instruction file (commands, agents, phases, templates, hooks, docs). Present at 2.14.1.
- **Reproduction** (`test_inline_python_isolated.py`, RED at `b67463a`). Each real program text, taken from the live files, run under `/bin/bash` in a temp folder holding a `json.py` that creates a marker file in that folder: the marker appeared for all twelve.
- **Fix** (`750870f`). `python3 -c` → `python3 -I -c` in all twelve. Every program imports only `json` and `sys`, so `-I` (no current folder, no user site folder, no `PYTHON*` variables) changes nothing else; output is ASCII (`json.dumps` default), so ignoring `PYTHONIOENCODING` does not change it.
- **After the fix:** no marker for any of the twelve; the six Finalize and fix-loop one-liners still print exactly their normal output; the same commands with `-I` taken out create the marker (the mutant). A scan of every shipped non-Python file under `plugins/vibe-check/` finds the twelve invocations, each with `-I`.
- **Not affected:** `python3 "$VC_ROOT/scripts/x.py"` (and the hook's `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gitguard.py`) put the script's own folder first, not the working directory; `test_a_shipped_script_puts_its_own_folder_first_not_the_cwd` runs `statepath.py` in the planted folder and the marker does not appear.

### Pasted-name guard, each character on its own (63-REVIEW WR-05)

`test_pasted_name_guard.py::TestEachCharacterAtEachSite` (`e2f0997`). For each of `$`, backtick, `"`, `\`, newline and carriage return, and each of the four print sites, a name holding only that one bad character (`x<c>y`) is refused: exit 1, no `NAME=` line, "Review halted" on stderr. How each value reaches the block: `00-scope.md` real phase folders, except newline (find's output is read a line at a time, so a `head` function hands the value over); `05-state.md` GSD key `PHASE_ID` from the environment (as before); `05-state.md` repo-and-branch key real branches for `$`, backtick and `"`, a real repo folder for carriage return, and a `git branch` function for `\` and newline (git refuses them in a branch name and `xargs basename` drops or splits them in a folder name); `05-state-all.md` a stub `statepath.py` under a stand-in `VC_ROOT` (the real key is 12-hex, so nothing else can carry a character into it). Mutation: taking only that character out of only that site's guard line makes exactly that site-and-character case fail, 24 of 24 (matrix in 63-10-SUMMARY "Review fixes"). The mutant check now requires the exact bad value on a printed `NAME=` line, so it cannot pass on a refused run or a harmless value.

| Where the literal is pasted | Name | Covered |
|-----------------------------|------|---------|
| `90-finalize.md`, `50-fix-loop.md` blocks on `--all` | `STATE_FILE` | yes (guard in the `05-state-all.md` key block, added by `d56232b`) |

## CI run on the pull request: locale-dependent tests

**What failed.** The offline suite (ubuntu-24.04, Python 3.14, locale C.UTF-8) failed two subtests that pass on macOS (en_US.UTF-8): `test_finalize_inputs.py::TestCliStderrParity::test_parity_counting_stage_stderr` (subtest `state not utf-8`, line 1183) and `test_parity_report_stage_stderr` (subtest `not utf-8`, line 1220), each `b'refused: state is not valid JSON\n' != b'refused: malformed state: passes\n'`. Reproduced locally with `LC_ALL=C LANG=C pytest … -k parity` (2 failed); without the override all pass.

**Why.** The 2.14.1 commands (`carry_state.py finalize-counts`, `batch_card.py decisions-report`) read the state from stdin as text, and Python picks stdin's error handler from the locale. Checked directly with Python 3.14.5 on the state `{"passes": "\xff\xfe"}`:

| Locale | `sys.stdin.errors` | 2.14.1 counting and report line |
|--------|--------------------|---------------------------------|
| C, POSIX (UTF-8 mode on) | `surrogateescape` | `refused: malformed state: passes` |
| C.UTF-8 | `surrogateescape` | `refused: malformed state: passes` |
| en_US.UTF-8 | `strict` | `refused: state is not valid JSON` |

The helper reads the file itself as strict UTF-8 and prints `refused: state is not valid JSON` on every locale. The tests were comparing against 2.14.1 on whatever locale the machine had.

**Fix (`dd69542`, test-only; no shipped file changed).** The shared runner for the 2.14.1 commands (`CliCase.old`) now sets `PYTHONIOENCODING=utf-8:strict` in the subprocess environment. That gives strict UTF-8 stdin on every locale and in UTF-8 mode (checked on Python 3.9, 3.12, 3.13 and 3.14 under C, C.UTF-8 and en_US.UTF-8). Every other input passed to that runner is valid UTF-8, so no other comparison changes. Removing the pin brings the failures back under `LC_ALL=C`. The new `test_named_difference_non_utf8_state_under_c_locale` pins both sides. Under C and C.UTF-8 (each checked to be in force with `surrogateescape` stdin, so a missing locale fails rather than skips) both 2.14.1 commands print the malformed line, and the helper as a subprocess exits 3 with empty stdout and the not-JSON line. With strict input both 2.14.1 commands print the not-JSON line. The report stage, run in-process as the parity test runs it, exits 5 with the not-JSON line. Named difference 10 in 63-REMOVAL-LEDGER.md and 63-EQUIVALENCE.md.

**Checks.** `test_finalize_inputs.py`: 109 passed, 191 subtests, under the default locale, `LC_ALL=C LANG=C`, `LC_ALL=C.UTF-8` and `LC_ALL=en_US.UTF-8`. Mutation: making the helper print `refused: state is not UTF-8` for a non-UTF-8 state fails both parity subtests and both locale subtests of the new test, under the default locale and under C (restored). The other phase test files (`test_finalize_card.py`, `test_cross_call_vars.py`, `test_pasted_name_guard.py`, `test_inline_python_isolated.py`, `docs/design/lean-v2.15/tools/test_finalize_capture.py`): 298 passed, 424 subtests, under `LC_ALL=C LANG=C` and under `LC_ALL=C.UTF-8`. None feeds bytes that are not valid UTF-8 to a 2.14.1 command, so no other locale-only failure.

**`test_codex_collect.py::test_abnormal_exit_is_a_timeout_skip` (`'124' != '3'` once in CI).** Five runs in a row locally: 12 passed each time, 16.9–17.0 s each. The `-I` change did not cause it. The test runs only two fences: the launch fence in `2c-codex-kickoff.md` (the one holding the `ARGS=` line) and the wait fence in `30-codex-collect.md` (the one holding the `REMAIN=` line). Neither runs Python. `-I` was added at `30-codex-collect.md` line 41, in the next fence (the payload translation), and at lines 37 and 80 of `2c-codex-kickoff.md`, in the step-2/3 fences. The test runs none of them. The launch fence writes the rc file as the exit status of `timeout -k 1 2 node <stub>`. In `fail` mode the stub writes one line and exits 3 at once (about 0.05 s here). An rc of `124` means `timeout` hit the test's 2-second cap before node exited, which can only mean the runner was slow to start node. It is a wall-clock race in the test's shortened cap, not a code change. The test and the fence were left unchanged.

### Codex collect timing test: a flake from before this phase (main session, 2026-11-15)

`test_codex_collect.py::TestCodexCollectExecutable::test_abnormal_exit_is_a_timeout_skip` failed with `'124' != '3'` in 3 of the first 6 runs on this branch's pull request (runs 43765243417, 43766691154 attempts 1 and 2). It is the suite's first launch of node, under a 2-second test cap. To see whether the branch caused it, five green runs of code from before the phase were re-run on the same day: 43614339306, 43613884499 and 43611870373 (`main`) and 43611421379 passed; 43611416017 (`1659a99`, the Phase 62 branch) failed with the identical error. So the flake exists in pre-phase code and shows on that day's runners. Fix, test-only: the class starts node once, untimed, before its timed runs, so the cap measures the stub and not node's cold start. No shipped file and no timing constant changed. That the cause is a cold start is the best-supported explanation (always the first node launch), not a proven one; the pull request's runs after the fix are the check.


## Leading-dash file names (D-24), 2026-11-15

Found by phase verification after PR #10 merged (63-VERIFICATION.md, gap 1). Owner decision D-24: match 2.14.1.

**Mechanism, confirmed on the real `guard.py`** (byte-identical to `dd8e4ab`). The 2.14.1 step 1 text (`dd8e4ab:plugins/vibe-check/phases/shared/90-finalize.md` line 13) validates each finding's file with `python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"` and requires exit 0. For `-x.ts`:

```
$ python3 guard.py --root <dir> --path "-x.ts"
usage: guard.py [-h] --root ROOT --path PATH
guard.py: error: argument --path: expected one argument
exit 2
$ python3 guard.py --root <dir> --path "x.ts"
contained
exit 0
```

argparse reads the value as an option, so the file was left out of `$BLOBFILE`. The merged helper called `guard.contained()` in-process, which skips the argument parsing.

**End to end, before the fix** (temp repo; state = the phase-45 loop fixture with the medium dismissed and the warning row's file set to the name, carrying a last-pass fix-obsolete verdict whose `verified_blob` is the file's HEAD blob, code unchanged; 2.14.1 side = the literal per-file procedure, then the `dd8e4ab` `carry_state.py finalize-counts` and `finalize_gate.py` commands; helper side = `finalize_inputs.py` at `c1541b1`; same output on Python 3.14.5 and 3.9.6):

| File | guard exit | 2.14.1 counts | 2.14.1 gate | 2.14.1 fingerprints | helper counts | helper gate | helper fingerprints |
|---|---|---|---|---|---|---|---|
| `x.ts` | 0 | [0,0,0] | `write` | `x.ts` | [0,0,0] | `write` | `x.ts` |
| `-x.ts` | 2 | [1,0,0] | `outstanding-to-phase-5` | none | [0,0,0] | `write` | `-x.ts` |

After the fix (`72a2f94`) the `-x.ts` row on the helper side is [1,0,0], `outstanding-to-phase-5`, no fingerprints, on both interpreters; `x.ts` is unchanged.

**Name matrix.** 51 names, each compared under Python 3.14.5 and 3.9.6 (102 comparisons), from the repo root (so the D-19 subfolder difference does not apply). 2.14.1 side: the PATH_RE pre-filter (`^[A-Za-z0-9._/-]+$`), then the guard command and the three git commands run through `bash -c` with the name pasted into the command text as the fence writes it; a file counts as fingerprinted only when all exit 0. Helper side: `finalize_inputs.head_blobs` on a one-finding state, same interpreter. Names are shown JSON-escaped; "yes" means fingerprinted.

| # | Name | 2.14.1 procedure, Python 3.14.5 | 2.14.1, Python 3.9.6 | Helper before fix (3.14 / 3.9) | Helper after fix (3.14 / 3.9) |
|---|---|---|---|---|---|
| 1 | control `x.ts` | yes | yes | yes / yes | yes / yes |
| 2 | leading - top `-x.ts` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 3 | leading - in subfolder file `sub/-x.ts` | yes | yes | yes / yes | yes / yes |
| 4 | folder starts with - `-d/x.ts` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 5 | -- `--` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 6 | - alone `-` | yes | yes | yes / yes | yes / yes |
| 7 | -x single `-x` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 8 | --root `--root` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 9 | --path `--path` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 10 | -h `-h` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 11 | --help `--help` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 12 | --ro (abbrev of --root) `--ro` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 13 | --pa (abbrev of --path) `--pa` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 14 | --pathx `--pathx` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 15 | -1 (negative int) `-1` | yes | yes | yes / yes | yes / yes |
| 16 | -1.5 (negative float) `-1.5` | yes | yes | yes / yes | yes / yes |
| 17 | -.5 (negative float) `-.5` | yes | yes | yes / yes | yes / yes |
| 18 | -1.ts `-1.ts` | yes | no (guard exit 2) | yes / yes | yes / no |
| 19 | -1_0 `-1_0` | yes | no (guard exit 2) | yes / yes | yes / no |
| 20 | -1e5 `-1e5` | yes | no (guard exit 2) | yes / yes | yes / no |
| 21 | -2/x.ts (folder -2) `-2/x.ts` | yes | no (guard exit 2) | yes / yes | yes / no |
| 22 | -hx `-hx` | no (guard exit 2) | no (guard exit 2) | yes / yes | no / no |
| 23 | --= `--=x` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 24 | space `a b.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 25 | leading space dash ` -x.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 26 | equals `a=b.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 27 | --root=x `--root=x` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 28 | double quote `a\"b.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 29 | single quote `a'b.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 30 | dollar `$x.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 31 | backtick ``a`b.ts`` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 32 | backslash `a\\b.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 33 | newline inside `a\nb.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 34 | trailing newline `t.ts\n` | yes | yes | yes / yes | yes / yes |
| 35 | leading colon `:x.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 36 | HEAD: like `HEAD:x.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 37 | star `*.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 38 | question `a?.ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 39 | bracket `[a].ts` | no (PATH_RE) | no (PATH_RE) | no / no | no / no |
| 40 | abs inside repo `<ROOT>/x.ts` | no (rev-parse 128) | no (rev-parse 128) | no / no | no / no |
| 41 | abs outside repo `/etc/hosts` | no (guard exit 1) | no (guard exit 1) | no / no | no / no |
| 42 | dotdot inside `sub/../x.ts` | no (rev-parse 128) | no (rev-parse 128) | no / no | no / no |
| 43 | dotdot outside `../x.ts` | no (guard exit 1) | no (guard exit 1) | no / no | no / no |
| 44 | ./ prefix `./x.ts` | yes | yes | yes / yes | yes / yes |
| 45 | directory `sub` | yes | yes | yes / yes | yes / yes |
| 46 | missing at HEAD `missing.ts` | no (rev-parse 128) | no (rev-parse 128) | no / no | no / no |
| 47 | symlink in repo `link.ts` | yes | yes | yes / yes | yes / yes |
| 48 | symlink out of repo `outlink` | no (guard exit 1) | no (guard exit 1) | no / no | no / no |
| 49 | .git/config `.git/config` | no (rev-parse 128) | no (rev-parse 128) | no / no | no / no |
| 50 | double slash `sub//c.ts` | no (rev-parse 128) | no (rev-parse 128) | no / no | no / no |
| 51 | trailing slash `sub/` | yes | yes | yes / yes | yes / yes |

**Result.** Before the fix: 28 disagreements (12 under 3.14.5, 16 under 3.9.6). Every one has the same mechanism: the 2.14.1 guard command exits 2 while parsing its arguments, and the helper fingerprints the file. After the fix: 0 of 102. No disagreement with a different mechanism was found in either direction.

**The rule is not "starts with `-`".** `-` alone and negative-number-like names (`-1`, `-1.5`, `-.5`) are accepted by the command. Names such as `-1.ts`, `-1_0`, `-1e5` and `-2/x.ts` are accepted under Python 3.14.5 and refused under 3.9.6, because newer argparse treats more names as negative numbers. So the fix uses the command's own parser under the interpreter that runs the helper (the same `python3` the 2.14.1 fence called), rather than a hand-written prefix test.

**Same on both sides, noted only.** A directory name (`sub`, `sub/`) is fingerprinted with its tree id by both. A name ending in a newline (`t.ts\n`) passes PATH_RE on both sides because Python's `$` matches before a final newline; whether a model checking the prose regex would have accepted it cannot be determined from the text. Neither is a disagreement and neither was changed.

**Fix (`72a2f94`).** The per-file check calls `guard.main(["--root", root, "--path", f])` in-process, with its stdout and stderr captured and dropped, and keeps the file only on exit 0. This is the command's own code path, including argparse, so the two cannot drift. No subprocess was added per finding. Test first at `c1541b1`: `test_finalize_inputs.py::TestGuardCommandParity` (22 names compared with the real guard command run as a subprocess, plus the `-x.ts` end-to-end run against the 2.14.1 counting and gate commands). Both tests failed on the unfixed helper and pass after the fix.

**Mutation checks** (scratch copy). Putting the old `guard.contained(root, f)[0]` line back fails both new tests. Replacing the test's 2.14.1-side subprocess with the helper's in-process `guard.contained` check fails both tests, with the unfixed helper and with the fixed one: the 2.14.1 side really runs the command.

## Repo folder names ending in whitespace (D-25), 2026-11-15

Found by phase re-verification (63-VERIFICATION.md, "The new gap in detail"). Present since PR #10 merged; not caused by the D-24 fix. Owner's D-24 ruling (match 2.14.1) applied by the main session as D-25.

**Mechanism, confirmed.** 2.14.1 step 1 passes `--root "$(git rev-parse --show-toplevel)"`. Command substitution removes every trailing `\n` and nothing else: no spaces, tabs or `\r`, and the bytes go through untouched. The helper's `_toplevel` returned `result[1].strip()`, which also removes spaces, tabs, `\r`, `\x0b`, `\x0c` and Unicode whitespace (no-break space, em space, ideographic space) from both ends. With the root trimmed, `guard.main` checks a folder that does not exist (file refused, finding stays open) or, when a repo of the trimmed name sits beside it, the neighbour (the helper's three git calls then run there too).

**End to end, before the fix** (helper at `5fe021c`, which is the unfixed helper; 2.14.1 side = the PATH_RE filter, the `dd8e4ab` guard line run through a real shell from the repo folder, the three git calls in the same folder, then the `dd8e4ab` `carry_state.py finalize-counts` and `finalize_gate.py`; state = the phase-45 loop fixture, medium dismissed, warning row on a clean committed `x.ts` with a last-pass fix-obsolete verdict on its HEAD blob). Identical on Python 3.9.6 (bash), 3.12.12 (bash), 3.13.14 (bash) and 3.14.5 (bash and zsh). Scratch script, temp folders only, removed afterwards.

| Repo folder (session in it) | 2.14.1 | Helper before fix | Same? |
|---|---|---|---|
| `repo` (control) | [0,0,0] `write` | [0,0,0] `write` | yes |
| `my repo` (space inside) | [0,0,0] `write` | [0,0,0] `write` | yes |
| ` repo` (leading space) | [0,0,0] `write` | [0,0,0] `write` | yes |
| `repo ` (trailing space) | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| `repo` + tab | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| `repo` + no-break space | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| `repo` + `\r` | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| `repo` + `\x0b` / + `\x0c` | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| `repo` + em space / + ideographic space | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| `repo` + `\n`, + `\n\n`, + ` \n`, + `\r\n` | [1,0,0] `outstanding-to-phase-5` | [1,0,0] `outstanding-to-phase-5` | yes (both name another folder) |
| `repo ` beside a repo `repo` with the same `x.ts`; real `x.ts` edited after the verdict | [1,0,0] `outstanding-to-phase-5` | [0,0,0] `write` | **no (wrong approval)** |
| `repo` + tab, same neighbour set-up | [1,0,0] `outstanding-to-phase-5` | [0,0,0] `write` | **no (wrong approval)** |
| `repo` reached through a symlink | [0,0,0] `write` | [0,0,0] `write` | yes |
| `repo` reached through `other/../repo` | [0,0,0] `write` | [0,0,0] `write` | yes |
| `repo ` reached through a symlink | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| `repo ` reached through `other/../repo ` | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` | **no** |
| folder name with byte `\xff` | not testable: APFS refuses the name (`Errno 92 Illegal byte sequence`) | | |

After the fix (`92ae038`) all 21 rows are the same on both sides, on the four interpreters, under bash and under zsh.

**Audit of every post-processing site in `finalize_inputs.py`.** "Shell" is what the 2.14.1 fence or prose step did with the same output.

| Site | 2.14.1 | Helper | Match? | Can a difference change a fingerprint, count or gate decision? |
|---|---|---|---|---|
| `_toplevel`: root text from `git rev-parse --show-toplevel` | `$(...)`: every trailing `\n` removed, nothing else | was `.strip()` (both ends, all whitespace); now `.rstrip("\n")` | was **no**; now yes | **Yes** (reproduced above). Fixed. |
| Leading whitespace of the root | kept | kept: git prints an absolute path, so the string starts with `/` and no folder-name character is ever at the front; probed with ` repo` | yes | No |
| Trailing `\r` of the root | kept | was removed; now kept | was **no**; now yes | Yes (reproduced). Fixed by the same change. |
| Several trailing `\n` (folder name ending in line breaks) | all removed | `.rstrip("\n")` removes all | yes | No (both give another folder; probed) **Correction 2026-11-15 (gap 3): wrong when a folder exists at the trimmed name.** The trim matches, but the helper also ran its three per-file git calls in that folder, so a neighbour at the trimmed name was read instead of the session's repository: a wrong approval with a neighbour repo and an edited file, a finding left open with a plain-folder neighbour. Only nothing at the trimmed name was probed. See "Per-file git checks in the session's repository (gap 3, D-26)" below. |
| Decoding of git's output, `os.fsdecode` (UTF-8 + surrogateescape on macOS) | bytes passed through the shell into `guard.py`'s argv, which Python decodes with the same filesystem encoding and error handler | `os.fsdecode`, then `guard.main` re-encodes in `realpath` | yes on macOS | Not on macOS: a non-UTF-8 folder name cannot exist on APFS. On a Linux host with a non-UTF-8 legacy locale, argv decoding and `fsdecode` could in principle differ; not probed (no such host) |
| `_ok(result)` empty root on a git failure | `$(...)` gives `""`, guard refuses an empty root | returns `""`, guard refuses | yes | No |
| Blob id, `rev[1].strip()` | the model reads `git rev-parse "HEAD:<file>"` output and writes it with the Write tool | `.strip()` | yes | No: the output is only hex digits and a line break, so `.strip()` and dropping the line break give the same text |
| `if blob:` | n/a (rev-parse exit 0 always prints an id) | skip empty | yes | No |
| Finding file name `f` | passed verbatim as `"<file>"` | passed verbatim to `guard.main` and git argv; no strip, no case change | yes | No |
| `os.path.realpath` / containment compare | inside `guard.py`, unchanged since `dd8e4ab` | the same `guard.main` | yes | No (same code) |
| `guard.contained` `root.strip()` blank check | same code | same code | yes | No: only decides "blank or not"; a root ending in a space is not blank |
| Case handling | none | none | yes | No |
| Symlinked path, `..` in the path | git prints the resolved root on both sides | same | yes | No (probed) |
| Folder the three per-file git calls run in | the session folder | the root (accepted D-19 difference) | no, by owner decision | Not this mechanism; unchanged **Correction 2026-11-15 (gap 3): this row stopped too early.** D-19 covers reading the file from the top of the same repository. When the root text is not the session's repository (a folder name ending in a line break beside a folder of the trimmed name; `core.worktree` pointing elsewhere) the decision differed from 2.14.1 in both directions. Fixed at `08f0018`; see "Per-file git checks in the session's repository (gap 3, D-26)" below. |
| State file decoding | stdin text, locale-dependent | strict UTF-8 | named difference (row 10 of the change list) | Not this mechanism; unchanged |

No disagreement with a different mechanism was found.

**Correction 2026-11-15 (gap 3).** True of the cases this audit ran. A different mechanism existed: the folder the three per-file git calls ran in (the two rows corrected above). The third verification round found it; see the section below.

**Fix (`92ae038`).** `_toplevel` returns `result[1].rstrip("\n")`: the trailing line breaks are removed, exactly as `$(...)` does; nothing else changed. Test first at `5fe021c`: `test_finalize_inputs.py::TestRepoFolderNameParity` (folder ending in a space and in a tab, end to end against the 2.14.1 commands with fixed expectations `{"x.ts": <blob>}`, [0,0,0], `write`; eight further endings; `repo ` beside `repo`, asserting the helper does not write and equals 2.14.1's [1,0,0] `outstanding-to-phase-5`) and `TestGuardCommandParity::test_parity_names_in_a_repo_folder_ending_in_a_space`. `TestGuardCommandParity`'s 2.14.1 side (`fingerprint_2141`) now runs the guard line `"$0" "$1" --root "$(git rev-parse --show-toplevel)" --path "$2"` through `/bin/sh` instead of trimming the root in Python. On the unfixed helper: 2 tests and 6 subtests failed (space, tab, no-break space, `\r`, `\x0b`, `\x0c`); the line-break and leading-space subtests passed, as they should.

Also corrected in the same test commit: the `TestGuardCommandParity` docstring now says what was observed (3.14 accepts `-1.ts`; 3.9, 3.12 and 3.13 refuse it), not "3.13+".

**Mutation checks** (scratch copy of the scripts folder; only the new tests selected).

| Mutant | Result |
|---|---|
| Helper `.strip()` restored | 8 failures: the new `TestGuardCommandParity` case, the neighbouring-repo test, and 6 subtests (space, tab, no-break space, `\r`, `\x0b`, `\x0c`) |
| Helper `.rstrip()` (all trailing whitespace) | the same 8 failures |
| Helper removes one trailing `\n` only | 3 subtests fail (`\n`, `\n\n`, ` \n` endings) |
| Helper `.strip()` AND the test's 2.14.1 side trimming in Python with `.strip()` | still 8 failures. The space/tab and neighbouring-repo tests fail on their fixed expectations. The `TestGuardCommandParity` case's helper-versus-2.14.1 comparison cannot see the bug in this mutant (both sides give `{}`); it fails only on its own fixed check that the clean files are kept (`'x.ts' not found in {}`) |
| Test's 2.14.1 side `.strip()` only, helper fixed | 7 failures: the test notices its own 2.14.1 side is wrong |

In a whole-file run of each mutant, 3 more failures appear (`TestNextVocabularyProse`): those tests read the phase prose by path and cannot find it from the scratch copy; they fail the same way with no mutation applied in that location, and they pass in the worktree.

**Runs after the fix.** `test_finalize_inputs.py`: 114 passed (pytest, Python 3.12.12 venv, default locale and `LC_ALL=C`; `/usr/bin/python3 -m pytest`, 3.9.6, default and `LC_ALL=C`); `python3.12`, `python3.13`, `python3.14 -m unittest test_finalize_inputs`: 114 tests OK each, default locale and `LC_ALL=C`. `test_finalize_card.py`, `test_carry_state.py`, `test_confirmed_fix.py`, `test_cross_call_vars.py`: 500 passed. `docs/design/lean-v2.15/tools`: 355 passed. `finalize_capture.py verify`: `finalize baseline matches (5 situations)`. `finalize_capture.py compare --driver helper --commit HEAD`: `finalize outcome fields match (5 situations, 7 walks)` on Python 3.14.5 and 3.9.6. `stdlib_only.py plugins/vibe-check`: `34 shipped .py files; third-party imports: none`.

## Per-file git checks in the session's repository (gap 3, D-26), 2026-11-15

Found by the third verification round (63-VERIFICATION.md, "Gap 3 in detail"). Present since PR #10 merged; not caused by the D-24 or D-25 fixes. Owner decision D-26, in the owner's words: "Fix gap 3 + add the side-by-side test (Recommended)".

**Mechanism, confirmed.** 2.14.1 step 1 gave the root text from `$(git rev-parse --show-toplevel)` to the guard command only, then ran `git rev-parse "HEAD:<file>"`, `git diff --quiet HEAD -- <file>` and `git diff --cached --quiet -- <file>` in the session folder. Since D-19 the helper ran those three calls with `cwd=root`. When the root text does not name the session's repository, git there reads another repository or none:
- a repo folder whose name ends in `\n` (`$(...)` drops it, so the root text names the folder of the trimmed name) with a folder or repo at the trimmed name;
- `core.worktree` pointing elsewhere: `--show-toplevel` names the configured work tree, and git run there does not find the session's `.git` (or finds a different repository).

**Reproduction.** The side-by-side test below, run against the helper at `38ed24f` (the pre-fix helper; scratch copy beside the current sibling modules): 284 scenarios, 232 agree, 14 D-19, **20 disagree**. All 20 have this mechanism (the folder the per-file checks address):

| Scenario (ending \| neighbour \| session \| setting \| name \| content \| verdict) | 2.14.1 | Helper before the fix |
|---|---|---|
| `lf` \| repo-same \| root \| none \| `x.ts` \| edit \| obsolete-head (verifier case a) | [1,0,0] `outstanding-to-phase-5` | [0,0,0] `write` |
| `lf` \| folder \| root \| none \| `x.ts` \| clean \| obsolete-head (case b) | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` |
| plain \| none \| root \| worktree-folder \| `x.ts` \| clean \| obsolete-head (case c) | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` |
| plain \| none \| root \| worktree-repo \| `x.ts` \| staged \| obsolete-head (case d) | [1,0,0] `outstanding-to-phase-5` | [0,0,0] `write` |
| `lflf` and `space-lf` \| repo-same \| root \| none \| `x.ts` \| edit | [1,0,0] `outstanding-to-phase-5` | [0,0,0] `write` |
| `lf` \| repo-diff \| root \| none \| `x.ts` \| clean | [0,0,0] `write` | [1,0,0] (blob read from the neighbour) |
| `lf` \| repo-diff \| root \| none \| `x.ts` \| edit | [1,0,0] | [1,0,0], neighbour's blob in the map |
| `lflf` \| repo-diff \| root \| `GIT_PREFIX` \| `dir/y.ts` \| staged-restored | `{}` | neighbour's blob in the map (same counts) |
| `space-lf` \| repo-diff \| sub \| `GIT_ICASE_PATHSPECS` \| `-1.ts` \| untracked | `{}` | neighbour's blob in the map (same counts) |
| worktree-folder with `dir`, `dir/`, `-1.ts`, `nl.ts⏎`, `link.ts` (no-break-space folder), `x.ts` (tab folder), all clean | [0,0,0] `write` | [1,0,0] `outstanding-to-phase-5` |
| worktree-repo, and `GIT_DIR`+`GIT_WORK_TREE` elsewhere, with `./x.ts`, clean | [1,0,0] `outstanding-to-phase-5` | [0,0,0] `write` (cwd-relative `HEAD:./x.ts` read in the other folder) |
| `nbsp` \| none \| inside `.git` \| worktree-repo \| `nl.ts⏎` \| staged-restored \| obsolete-head | [1,0,0] `outstanding-to-phase-5` | [0,0,0] `write` |
| `lflf` \| repo-same \| deeper \| literal pathspecs \| `x.ts` \| untracked \| obsolete-old | `{}`, [1,0,0] | neighbour's blob in the map, [1,0,0] |

One more row failed only the D-19 assertion: `lf` \| repo-same \| sub \| none \| `x.ts` \| edit. The pre-fix helper read the neighbour from the subfolder and fingerprinted the edited file, the very thing D-19 rules out; it happened to agree with 2.14.1, which fingerprints it too (D-19 shape).

**Fix (`08f0018`).** The three calls run in the session folder (`_git(..., cwd)`), so git's own repository discovery, `core.worktree` and every `GIT_*` variable apply exactly as at 2.14.1. The root text stays the guard command's `--root`, as at 2.14.1. D-19 is kept by `_up_to_top`: `git rev-parse --show-prefix` in the session folder, its `/`-separated parts counted, one `../` per part prefixed to the name in the two `git diff` calls (`HEAD:<file>` is already read from the top; `HEAD:./x` would be cwd-relative, and the grid's `./x.ts` row agrees with 2.14.1 because both read it in the session folder) *[Note added 2026-11-16, gap 5: this holds only with the session at the repo top. From a subfolder the helper at `08f0018` gave the two checks `.././x.ts` (the top-level file) while `HEAD:./x.ts` read the subfolder's file, so the checks and the blob addressed different files. The grid's `./x.ts` row agreed only because no fixture subfolder held an `x.ts`: `HEAD:./x.ts` failed there on both sides. See "File names read from the session folder (gap 5, D-28)" below.]*. At the top the prefix is empty and the three calls are exactly 2.14.1's. Probed on git 2.55.0 before choosing: `../` pathspecs work under `GIT_LITERAL_PATHSPECS`, `GIT_ICASE_PATHSPECS` and `GIT_NOGLOB_PATHSPECS`; the `:/` top magic does NOT (under `GIT_LITERAL_PATHSPECS=1`, `git diff --quiet HEAD -- :/x.ts` exits 0 on an edited file, which would fingerprint it), so magic is not used. With `core.worktree` pointing elsewhere and the session in the folder holding `.git`, `--show-prefix` prints an empty line (`--show-cdup` prints the absolute work-tree path, which is why the prefix is counted instead). The character filter admits no `:`, so no file name can carry pathspec magic itself. The prefix query runs once, only after the first file passes the guard; if it fails, every file is left out (the fail-closed omission). The containment check still takes the textual root, so D-24 and D-25 behaviour is unchanged (their grid rows and `TestGuardCommandParity`, `TestRepoFolderNameParity` pass).

**The side-by-side test** (`plugins/vibe-check/scripts/test_finalize_parity_grid.py`, first at `d2d604c`, further rows at `06fd54e` and `ace05a8`).
- *2.14.1 side:* `plugins/vibe-check/scripts/fixtures/finalize_step1_2141.sh`, the `dd8e4ab` `90-finalize.md` lines 13–22 per-file procedure (the `^[A-Za-z0-9._/-]+$` filter applied with Python `re.match`, the guard line `python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "$f"`, `blob=$(git rev-parse "HEAD:$f")`, the two `git diff` calls, the blob kept only when all exit 0), run through `/bin/sh` in the session folder with `python3` on PATH resolving to the test's interpreter; then `carry_state.py finalize-counts` and `finalize_gate.py` as commands. The verdict-to-file selection (last-pass verdicts, first matching row) is the test's Python, as the step's prose describes it. `.sh` is not a shipped `.py` module: the stdlib gate still reports 34 files.
- *Pin:* `TestStep1ScriptIsPinned` reads `dd8e4ab:plugins/vibe-check/phases/shared/90-finalize.md` with `git show`, requires the script's eight command lines to be exactly the expected scaffold plus the filter pattern and the four commands found verbatim (backtick-quoted) in lines 13–22, in order, and requires `guard.py`, `carry_state.py`, `finalize_gate.py` and `fixcommit.py` to hash to their `dd8e4ab` blobs (they do; `batch_card.py` too, though only the helper uses it).
- *Grid design:* seven axes: folder-name ending (plain, space, tab, `\r`, no-break space, `\n`, `\n\n`, space+`\n`, byte `\xff`); what sits at the trimmed name (nothing, plain folder, repo with the same files, repo with different files); session (top, `dir`, `dir/deep é`, a folder outside the repo, inside `.git`); setting (none, `core.worktree` to a folder / a repo, `GIT_DIR` absolute / relative, `GIT_DIR`+`GIT_WORK_TREE` on the repo / elsewhere, `GIT_CEILING_DIRECTORIES` at the parent / the repo, `core.quotepath=true`, linked worktree, symlinked path, path through `..`, `GIT_LITERAL_PATHSPECS`, `GIT_ICASE_PATHSPECS`, `GIT_NOGLOB_PATHSPECS`, `GIT_PREFIX`, no git on PATH); file name (`x.ts`, `dir/y.ts`, `-x.ts`, `-1.ts`, `dir`, `dir/`, missing, symlink in, symlink out, `a b.ts`, `dir/../x.ts`, `./x.ts`, `.git/config`, `nl.ts⏎`); content (clean, edit, staged, staged then working copy restored, deleted, untracked); verdict (obsolete on HEAD's blob, obsolete on a stale blob, at an earlier pass, `applied`). A deterministic greedy covering array (seed 63) covers every valid pair of axis values (a plain folder name has no trimmed neighbour), 253 rows, plus 32 named rows (the three rounds' cases and the further gap 3 rows) and 7 D-19 rows: 284 scenarios after de-duplication. 8 worker threads; each scenario in its own temp folder, every `GIT_*` variable dropped, global/system config off, `GIT_CEILING_DIRECTORIES` at the temp root; all removed afterwards.
- *Allowed differences:* only the D-19 shape (session below the repo folder, file edited/staged/staged-restored/deleted, 2.14.1 fingerprints exactly that file with its HEAD blob, the helper leaves exactly it out, and the decisions follow: `write` vs `outstanding-to-phase-5` for a verdict on HEAD's blob, both open otherwise); 7 named D-19 rows assert both sides exactly. `KNOWN_DIFFERENCES` is empty and shrink-only: an entry must still be found with exactly its recorded outcomes.
- *Not creatable here:* scenarios whose folder name holds the byte `\xff` (APFS: `Errno 92 Illegal byte sequence`): 18 on this Mac, counted and asserted to be only that axis value (or the line-break file name), not skipped. A filesystem that accepts them (Linux CI) runs them and they must agree.
- *Not exercised:* D-27's 60-second limit (no scenario makes git slow).
- *Result after the fix:* 284 scenarios, 252 agree, 14 D-19, 0 known, 0 unexpected, 18 not creatable; about 23–33 s for the grid on this Mac (Python 3.14.5 driver: 23.0 s alone, ~32 s with other load); the module (grid + pin + bash re-run of the named rows) about 30–60 s under pytest. The 14 D-19 rows include one with `GIT_DIR`+`GIT_WORK_TREE` on the repo and the session inside `.git`: git then treats `.git` as a subfolder of the work tree, 2.14.1's pathspec misses, and the helper lifts it, so D-19 applies there too; the test counts the session inside `.git` as "below the repo folder" for that reason.

**Mutation matrix** (helper mutants in scratch copies of `plugins/vibe-check`; grid counts from `test_finalize_parity_grid.py --grid <mutant>`, failures from `pytest -k TestParityGrid` on Python 3.12.12):

| Mutant | Grid | Tests failing |
|---|---|---|
| none | 0 unexpected | 0 (6 passed) |
| in-process `guard.contained` instead of the command (gap 1) | 7 unexpected | agreement test + regression row `-x.ts` |
| `.strip()` on the root (gap 2) | 9 unexpected | agreement test + regression row space-ending |
| root as cwd for the three checks (gap 3, the pre-fix form) | 20 unexpected | agreement test + 11 regression rows + D-19 row `lf`/sub |
| fingerprints every candidate (no filter, guard or diff checks) | 77 unexpected, 0 D-19 | agreement test + 12 regression rows + all 7 D-19 rows |
| fingerprints nothing | 76 unexpected | agreement test + 12 regression rows |
| D-19 lift removed (2.14.1 pathspec) | 0 unexpected, 0 D-19 | the D-19 test: all 7 rows |
| drops one final `\n` only | 14 unexpected | agreement test + regression row `lf`/none |

Pin mutants (edit applied to the worktree script, pin class run, original bytes restored and checked): delete the `--cached` check; `":/$f"` in the diff check; `rev-parse` moved after the diff checks; pattern admitting a space; root piped through `tr`; `HEAD:./$f`; an extra line. Each fails `test_script_lines_are_the_dd8e4ab_commands`; unedited passes.

**Triage of what the grid found.** Before the fix: the 20 rows above and the D-19 row, all the gap 3 mechanism, fixed together; 19 of the 20 rows are named in `REGRESSION_ROWS` with their 2.14.1 outcome (`06fd54e`, `ace05a8`); the twentieth (`core.worktree` at a folder, `-1.ts`) is left to the pairwise grid because its 2.14.1 outcome depends on the Python version (argparse refuses `-1.ts` before 3.14). After the fix: none outside the D-19 shape. No new mechanism, so `KNOWN_DIFFERENCES` is empty and nothing awaits an owner decision.

**Also in `test_finalize_inputs.py`.** `TestSessionRepository` (both `core.worktree` directions, each with a root-as-cwd mutant that must flip the result); `TestFingerprints::test_exact_git_calls` now includes `rev-parse --show-prefix`; `test_exact_git_calls_from_a_nested_subfolder` (`../../src/a.ts` in the two diff calls); `test_prefix_query_failing_leaves_every_file_out`. The two D-19 mutants now remove the `../` lift and were renamed `test_mutant_name_read_from_session_folder_fingerprints_edit_from_subfolder` and `test_mutant_index_name_read_from_session_folder_fingerprints_staged_file`.

The mutation matrix above was run on the test file at `06fd54e` (25 named rows); `ace05a8` adds 7 named rows from the same grid, so the grid counts are unchanged and each helper mutant fails at least the tests listed.

**Runs after the fix (2026-11-15).** `test_finalize_parity_grid.py` + `test_finalize_inputs.py`: 127 passed, 0 skipped (pytest on Python 3.12.12, default locale and `LC_ALL=C`; `/usr/bin/python3 -m pytest`, 3.9.6, default and `LC_ALL=C`); `python3.13` and `python3.14 -m unittest`: 127 tests OK, default and `LC_ALL=C` (D-19 rows: 14 on 3.12 and 3.14, 12 on 3.9 and 3.13, where argparse refuses `-1.ts` on both sides alike). After `ace05a8`: the grid file again on 3.12 (pytest), 3.9 (pytest, both locales) and 3.13 (unittest): passed. `test_finalize_card.py`, `test_carry_state.py`, `test_confirmed_fix.py`, `test_cross_call_vars.py`: 500 passed. `.github/scripts/test_stdlib_only.py` + `docs/design/lean-v2.15/tools`: 376 passed. `finalize_capture.py verify`: `finalize baseline matches (5 situations)`; `compare --driver helper` by commit (Python 3.14.5 and 3.9.6) and by folder: `finalize outcome fields match (5 situations, 7 walks)`. `stdlib_only.py plugins/vibe-check`: `34 shipped .py files; third-party imports: none` (the `.sh` fixture and `test_*.py` are not counted). `left_out_guard.py check-list`: `left-out list matches the recorded five`; the new tests record no skip (junit `skipped="0"`). `step_count.py --rev HEAD`: 85 Finalize steps; `footprint.py --rev HEAD`: Finalize 130,886 bytes (unchanged). Not checked here: the Linux CI run (a filesystem that can create the `\xff` folder rows, dash as `/bin/sh`, fewer cores); the full suite (left to the main session and CI).

## File names read from the session folder (gap 5, D-28), 2026-11-16

Found by the fourth verification round (63-VERIFICATION.md, "Gap 5 in detail"). A regression made by the gap 3 fix (`08f0018`), present only on the unmerged follow-up pull request: `main` (`4ac7ee4`) and the helper at `48b307f` do not have it. It breaks D-19, which the owner already decided, so it was fixed without a new owner decision (D-28; the owner was told).

**Mechanism, confirmed with real git** (git 2.55.0; the per-form table below). `08f0018` put `up` (one `../` per folder level from `git rev-parse --show-prefix`) in front of every name in the two `git diff` calls, on the premise that `HEAD:<file>` is read from the top. That premise holds only for a name that does not start with `./` or `../`. git resolves `HEAD:./y.ts` and `HEAD:../y.ts` from the session folder, so from `dir` the blob came from `dir/y.ts` while the checks were given `.././y.ts`, the top-level `y.ts`: the blob and the change checks addressed different files.

**Reproduction** (the strengthened grid, `TestNameFormGrid`, run against the helper at `4f89006`, which is `08f0018`'s `_head_blobs`): 549 scenarios, 470 agree, 35 D-19, 6 D-19 second direction (N-13), **38 differ**, every one a `./` or `../` name with the session below the top; 15 are wrong approvals. Layout `all` = `n.ts`, `dir/n.ts`, `dir/deep/n.ts` committed with different content; fix-obsolete verdict on the blob `HEAD:<name>` gives in the session folder; key = repo folder name | layout | changed file(s) | how | session | name.

| Scenario | 2.14.1 | Helper at `4f89006` |
|---|---|---|
| repo \| all \| sub \| edit / staged / staged-restored \| `dir` \| `./n.ts` (verifier case a) | [1,0,0] `outstanding-to-phase-5` | **[0,0,0] `write`** |
| repo \| sub-only \| sub \| edit / staged / staged-restored \| `dir` \| `./n.ts` | [1,0,0] | **[0,0,0] `write`** |
| repo \| all \| deep \| edit / staged / staged-restored \| `dir/deep` \| `./n.ts`, and from `dir` \| `./deep/n.ts` | [1,0,0] | **[0,0,0] `write`** |
| repo \| all \| sub \| edit / staged \| `dir` \| `./dir/../n.ts`; deep \| staged-restored \| `dir/deep` \| `./dir/../n.ts` | [1,0,0] | **[0,0,0] `write`** |
| repo \| all \| top \| edit / staged / staged-restored \| `dir`, `dir/deep` \| `./n.ts` (verifier case b) | [0,0,0] `write` | [1,0,0] (safe) |
| repo \| all \| top+sub \| edit / staged / staged-restored \| `dir/deep` \| `./n.ts` | [0,0,0] `write` | [1,0,0] (safe) |
| repo \| all \| top \| edit \| `dir`, `dir/deep` \| `./dir/../n.ts`; top+sub \| staged-restored \| `dir/deep` \| `./dir/../n.ts` | [0,0,0] `write` | [1,0,0] (safe) |
| dir \| all \| clean, top edit, deep staged-restored, … \| `dir` \| `../dir/n.ts`, `./../dir/n.ts`, `../dir/deep/n.ts` (verifier case c: the lifted name leaves the repo and git refuses it) | [0,0,0] `write` | [1,0,0] (safe) |

**Per-form semantics** (task 2; each claim checked with real git 2.55.0 by `TestNameFormGrid::test_model_is_what_git_does` for every session and form, and in a scratch probe with more forms). git's rules: `HEAD:<name>` is resolved from the session folder and normalised (`.`, `..`, `//` collapsed; refused when it climbs above the top) exactly when the name starts with `./` or `../`; any other name is looked up from the top as written, with no normalisation, so an empty, `.` or `..` part makes it name nothing (`HEAD:dir/../x.ts`, `HEAD:dir/./x.ts`, `HEAD:dir//x.ts` all fail, at the top and in a subfolder). A pathspec after `--` is always resolved from the session folder and normalised the same way; above the top git exits 128. The guard command resolves every name against the repo root, so a `../` name passes it only when it comes back into the repo (`../<repo folder name>/…`).

| Name form | Session at the top: `HEAD:` / both 2.14.1 checks | Session in `dir`: `HEAD:` reads | 2.14.1 checks (`dir/` + name) | Helper checks | "Matches 2.14.1" / "D-19" means |
|---|---|---|---|---|---|
| `n.ts` | `n.ts` / `n.ts` | `n.ts` | `dir/n.ts` | `../n.ts` = `n.ts` | the plain-name hole: D-19 (`n.ts` changed) and N-13 (`dir/n.ts` changed) |
| `dir/n.ts` | `dir/n.ts` / `dir/n.ts` | `dir/n.ts` | `dir/dir/n.ts` (absent: always passes) | `../dir/n.ts` | the hole: D-19 only |
| `./n.ts` | `n.ts` / `n.ts` | `dir/n.ts` | `dir/n.ts` | `./n.ts` = `dir/n.ts` | no hole: must equal 2.14.1 |
| `./dir/n.ts` | `dir/n.ts` / `dir/n.ts` | `dir/dir/n.ts` (absent: fails) | — | — | must equal 2.14.1 |
| `./dir/../n.ts` | `n.ts` / `n.ts` | `dir/n.ts` | `dir/n.ts` | as written | must equal 2.14.1 |
| `./deep/n.ts` (from `dir`) | absent / — | `dir/deep/n.ts` | `dir/deep/n.ts` | as written | must equal 2.14.1 |
| `../n.ts`, `./../n.ts` | fails (above the top) / exit 128 | `n.ts` | `n.ts` | as written | guard refuses (outside the root) on both sides |
| `../dir/n.ts` (repo folder `dir`) | fails / exit 128 | `dir/n.ts` | `dir/n.ts` | as written | guard passes (`<root>/../dir/n.ts` is `<root>/n.ts`); must equal 2.14.1 |
| `../dir/n.ts` (repo folder `repo`) | fails | `dir/n.ts` | `dir/n.ts` | as written | guard refuses on both sides |
| `dir/../n.ts`, `dir/./n.ts` | fails (no normalisation) / pathspec normalised | fails | — | — | left out on both sides |
| `../../n.ts` | fails | fails (above the top) | exit 128 | — | left out on both sides |
| `deep/n.ts`, `dir/deep/n.ts` | plain names: as `dir/n.ts` (looked up from the top) | | | | `dir/deep/n.ts` is the hole (D-19 only); `deep/n.ts` names nothing |

So "matches 2.14.1" for a `./` or `../` name means the same three calls with the same name (git addresses one file in all three); "D-19" applies only to a plain name with the session below the top, where 2.14.1 read the blob from the top and checked `<prefix><name>`.

**Fix (`7079ab0`).** `_pathspec_for_blob(f, up)`: a name starting with `./` or `../` is given to the two checks as written; any other name gets `up + f`. Why this and not deriving a top-relative path: it is the principle "the checks address the file the blob was read from", expressed with git's own resolution. For a `./`/`../` name git resolves the pathspec exactly as it resolved `HEAD:<name>` (same session-relative normalisation, confirmed above), so the name as written is that file, and the three calls are then literally 2.14.1's. For any other name, `rev-parse HEAD:<name>` succeeding means the name has no empty, `.` or `..` part, so `up + name` is exactly the file read. Deriving the path by re-implementing git's normalisation in the helper would reach the same files with more code that could drift from git (`//`, a trailing `/`, an empty result giving an empty pathspec). Tried as a scratch variant (normalise `<prefix><name>` and lift it): see the matrix row "ALT" below.

**Strengthened grid** (`TestNameFormGrid`, first at `4f89006`, where it failed as above). One name at up to three levels (`n.ts` at the top, in `dir`, in `dir/deep`, each with different content); layouts `all`, `top-only`, `sub-only`; sessions top, `dir`, `dir/deep`; content: clean, or one of unsaved edit / staged edit / staged edit with the working copy restored applied to the top file, the `dir` file, the `dir/deep` file, or top and `dir` together. Full cross for the five forms that name an existing file somewhere (`n.ts`, `./n.ts`, `dir/n.ts`, `./dir/n.ts`, `./deep/n.ts`): 3 layouts' contents (13 + 4 + 4) × 3 sessions × 5 = 315. Ten further forms (`./dir/../n.ts`, `dir/deep/n.ts`, `./dir/deep/n.ts`, `../n.ts`, `./../n.ts`, `../dir/n.ts`, `../../n.ts`, `dir/../n.ts`, `dir/./n.ts`, `deep/n.ts`) × 3 sessions × six contents covering every target and every state: 180. With the repo folder itself named `dir`, three re-entering forms (`../dir/n.ts`, `../dir/deep/n.ts`, `./../dir/n.ts`) × 3 sessions × the same six contents: 54. Total 549 (17 distinct names); one repo per (folder name, layout, content), shared by its sessions and forms; the 2.14.1 counting and gate commands memoised per (state bytes, fingerprint map), step 1 always run. Every form passes the 2.14.1 character filter (asserted). Each side is predicted from the git model above, and the test asserts the 2.14.1 side equals the prediction for all 549 (so the model and the script are both checked) and that the model equals real git for every session × form. A difference is tolerated only when the session is below the top, the name is plain, the model says `HEAD:` and the checks address different files, and the helper's result is exactly the D-19 prediction; it is then D-19 (the file read was changed) or N-13 (only the session folder's same-named file was changed). Named rows: 15 regression rows (cases a, b, c, `./../n.ts` refused by the guard, clean controls) that must agree with fixed 2.14.1 outcomes, and 7 D-19 rows with both outcomes asserted, 3 of them N-13. Separate assertions: no `./` or `../` name ever differs; nothing differs at the repo top. `KNOWN_DIFFERENCES` stays empty: the grid found no difference with a new mechanism.

**Also.** `test_finalize_inputs.py::TestSessionRelativeNames` (five tests: clean `./c.ts` from `sub` fingerprinted with the exact calls; `sub/c.ts` edited, staged-then-restored: left out; top `c.ts` edited: still fingerprinted; `../c.ts` and `./../c.ts` refused by the guard), and `TestMutants::test_mutant_lifting_every_name_fingerprints_an_edited_dot_slash_file`. The first grid's `d19_difference` now also requires a plain name. The first grid asserts "not creatable here" is empty on Linux. Both grids print their summary and raise it as a `GridSummary` warning: CI runs `pytest -q … -rs --junitxml=…` and keeps only the log (no junit upload), `-q` hides a passing test's print, but the warnings section is printed on success, so the two summary lines reach the CI log without a workflow change (the left-out guard reads only the last `… passed …` line, which a warning count does not disturb: its failure pattern is `failed|errors?`). `--grid [helper.py]` now runs every assertion of both grid classes and exits 1 on any failure (with the `../` lift removed it exited 0 before).

**Mutation matrix** (scratch copies of `plugins/vibe-check/scripts` with `finalize_inputs.py` changed, run through `test_finalize_parity_grid.py --grid <copy>/finalize_inputs.py` on Python 3.14.5; 2026-11-16):

| Mutant | First grid (284) | Name-form grid (549) | `--grid` exit | Tests failing |
|---|---|---|---|---|
| none (the fix) | 252 agree, 14 D-19, 0 unexpected | 508 agree, 35 D-19, 6 N-13, 0 unexpected | 0 | none |
| always lift (gap 5 restored) | 0 unexpected | **38 unexpected** | 1 | agreement, regression rows, `./`/`../` names never differ |
| never lift (pre-D-19) | 0 unexpected, 0 D-19 | 549 agree, 0 D-19 | 1 | D-19 rows (both grids) |
| root as cwd (gap 3) | 20 unexpected | 84 unexpected | 1 | agreement (both), regression rows, D-19 rows, `./` names |
| `.strip()` on the root (gap 2) | 9 unexpected | 0 unexpected | 1 | agreement, regression rows (first grid) |
| in-process `guard.contained` (gap 1) | 7 unexpected | 0 unexpected | 1 | agreement, regression rows (first grid) |
| fingerprint every validated file | 23 unexpected, 0 D-19 | 69 unexpected | 1 | agreement (both), regression rows, D-19 rows, nothing differs at the top, `./` names |
| fingerprint nothing | 76 unexpected | 129 unexpected | 1 | agreement (both), regression rows, D-19 rows, nothing differs at the top, `./` names |
| ALT, not a defect: normalise `<prefix><name>` for a `./`/`../` name in the helper and lift it | 252 agree, 14 D-19, 0 unexpected | 508 agree, 35 D-19, 6 N-13, 0 unexpected | 0 | none: the same files as the fix, so the grid cannot tell the two apart; the fix was kept for the reasons above |

Every defect mutant above makes `--grid` exit 1 and fails at least one named-row assertion. "never lift" leaves the agreement tests passing on both grids (it is 2.14.1's own behaviour) and is caught only by the D-19 rows, as intended.

**Runs after the fix (2026-11-16, at `7079ab0`).** `test_finalize_parity_grid.py` + `test_finalize_inputs.py`: 143 passed, default locale and `LC_ALL=C`, on Python 3.12.12 (pytest), 3.9.6 (`/usr/bin/python3 -m pytest`), 3.13.14 and 3.14.5 (`-m unittest`, 143 tests OK). Grid summaries: name-form 549, 508 agree, 35 D-19, 6 N-13, 0 unexpected, 0 off the git model on all four; first grid 284, 0 unexpected, 18 not creatable, with 254 agree / 12 D-19 on 3.9, 3.12 and 3.13 and 252 / 14 on 3.14 (argparse's reading of `-1.ts` differs by version on both sides alike). Linux (Docker `python:3.12`, Python 3.12.16, git 2.47.3, non-root user, a clone at `7079ab0`): `--grid` exit 0, 16 tests OK; unittest default and `LC_ALL=C` 143 OK; `pytest==9.0.3 -q -rs` as CI runs it: 143 passed, and its warnings section shows both summary lines (`284 scenarios … 272 agree, 12 D-19, 0 known differences, 0 unexpected, 0 not creatable here`; `549 name-form scenarios … 0 unexpected, 0 off the git model`). Wall time on this Mac: the grid file alone about 37 s at low load and 55 s with a load average near 12 from other work (each grid 15–25 s); the two files together 63–87 s; on Linux the grid file's two grids took 6–9 s each. `test_finalize_card.py`, `test_carry_state.py`, `test_confirmed_fix.py`, `test_cross_call_vars.py`: 500 passed. `docs/design/lean-v2.15/tools`: 355 passed. `.github/scripts/test_stdlib_only.py`: 21 passed. `stdlib_only.py plugins/vibe-check`: `34 shipped .py files; third-party imports: none`. `left_out_guard.py check-list`: `left-out list matches the recorded five`. `finalize_capture.py verify`: `finalize baseline matches (5 situations)`; `compare --driver helper` by commit (Python 3.14.5 and 3.9.6) and by folder: `finalize outcome fields match (5 situations, 7 walks)`. `step_count.py --rev HEAD --mode finalize`: 85 steps; `footprint.py --rev HEAD`: Finalize 130,886 bytes (unchanged; no instruction file changed). The full suite was not run.
