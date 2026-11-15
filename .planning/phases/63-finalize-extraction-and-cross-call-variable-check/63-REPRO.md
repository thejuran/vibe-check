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
