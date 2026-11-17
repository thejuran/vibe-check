---
phase: 62-baseline-and-continuous-test-run
reviewed: 2026-11-14T07:29:15Z
depth: standard
files_reviewed: 21
files_reviewed_list:
  - .github/ci-left-out-tests.txt
  - .github/scripts/left_out_guard.py
  - .github/scripts/stdlib_only.py
  - .github/scripts/test_left_out_guard.py
  - .github/scripts/test_stdlib_only.py
  - .github/scripts/test_workflow_shape.py
  - .github/workflows/offline-suite.yml
  - docs/design/lean-v2.15/tools/baseline_records.py
  - docs/design/lean-v2.15/tools/finalize_capture.py
  - docs/design/lean-v2.15/tools/path_records.py
  - docs/design/lean-v2.15/tools/step_count.py
  - docs/design/lean-v2.15/tools/usage_fields.py
  - docs/design/lean-v2.15/tools/test_baseline_page.py
  - docs/design/lean-v2.15/tools/test_baseline_records.py
  - docs/design/lean-v2.15/tools/test_finalize_capture.py
  - docs/design/lean-v2.15/tools/test_path_records.py
  - docs/design/lean-v2.15/tools/test_step_count.py
  - docs/design/lean-v2.15/tools/test_usage_fields.py
  - docs/design/lean-v2.15/BASELINE-v2.14.1.md
  - docs/design/lean-v2.15/CRITERION.md
  - docs/design/lean-v2.15/README.md
findings:
  critical: 0
  warning: 6
  info: 6
  convention: 1
  total: 13
status: issues_found
---

# Phase 62: Code Review Report

**Reviewed:** 2026-11-14T07:29:15Z
**Depth:** standard
**Files Reviewed:** 21
**Status:** issues_found

## Summary

Scope: the CI workflow, its two guard scripts and their tests, the five baseline tools and their
tests, and the three kit documents, on `feat/v2.15-phase-62` at `93f13ab`. The generated records
under `baseline/` were read only where a tool or test depends on them.

How this was checked: every source file was read in full; the three guard-style test files
(`test_workflow_shape.py`, `test_baseline_page.py`) were read in full and the other five test
files were scanned for skips, swallowed exceptions and temp-dir handling rather than read line by
line. The suite was run (`pytest -q -p no:cacheprovider .github/scripts docs/design/lean-v2.15/tools`:
445 passed, 250 subtests passed). Every warning below was reproduced with a small read-only
experiment in a temp directory outside the repo; the observed output is quoted in each finding.
No source file was changed.

Result by the five priorities:

1. **CI workflow as a security surface: no defect found.** `pull_request` only (no
   `pull_request_target`), one top-level `permissions: contents: read`, `persist-credentials: false`,
   no `${{ }}` expansion in any `run:` step, no secret read. Both action pins were checked against
   GitHub: `actions/checkout@3d3c42e…` is the commit tag `v7.0.1` points at, and
   `actions/setup-python@6d4fd22…` is the commit tag `v7.1.0` points at. A pull request from a fork
   can run tests with a read-only token and nothing more.
2. **Guards that cannot fail: six confirmed holes (WR-01 to WR-06), no blocker.** None lets a
   failing test run show green today. Five of the six are record checks that prove a record agrees
   with itself rather than with the 2.14.1 commit; one is the CI skip guard accepting a repeated
   skip.
3. **Ordinary correctness: no defect found.** Subprocess calls are argument lists with timeouts,
   temp directories are removed in `finally` or `addCleanup`, files are opened with `with`.
4. **Privacy: committed records are clean.** No home path, account name or session-log path in the
   three documents or any record; trace `tool_calls` hold only `Agent`, `AskUserQuestion`, `Bash`,
   `Read`, `Write`. Three small inconsistencies in the checkers are under IN-04.
5. **Portability: one robustness item (IN-02).**

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: The CI skip guard passes when one recorded skip appears twice

**Classification:** WARNING
**File:** `.github/scripts/left_out_guard.py:262-268`, `:293-302`
**Issue:** `cmd_check_skips` compares the skip *count* on the observed list (`logged != len(observed)`)
but compares the skip *set* through dicts (`skip_differences` builds `{pair: pair}`), which
collapses repeats. A result file holding three skipped test cases, two of them the same recorded
pair, with a log saying `3 skipped`, passes against a recorded list of two.
Reproduced: result file with the lane-archive pair twice plus the replay pair, log
`4000 passed, 3 skipped, 5 deselected` gave exit 0 and `skipped set matches the recorded 2`.
The trigger is narrow (pytest has to write the same test id twice), but the guard's stated rule is
"the set of pairs must equal the recorded list", and three skips is not the recorded two.
**Fix:** Compare lists, not sets, and compare the count with the recorded list as well:
```python
if sorted(observed) != sorted(recorded):   # after the existing unexpected/missing report
    ...
if len(observed) != len(set(observed)):
    _stop("A SKIPPED TEST APPEARS TWICE IN THE RESULT FILE", [...]); return 1
```
Add the repeated-pair case to `test_left_out_guard.py` as a mutant.

### WR-02: `verify_steps` accepts a step record that covers any file list, including none

**Classification:** WARNING
**File:** `docs/design/lean-v2.15/tools/step_count.py:267-298` (list taken from the record at `:280-281`)
**Issue:** The recount runs over `record["files"]` and nothing ties that list to the seven files
the Finalize path declared at 2.14.1. Reproduced:
- a record with `files: []`, all totals 0 and `rev: "not-a-commit"` verifies clean (`[]`); with an
  empty list no git call is made, so the revision is never even resolved;
- a record holding one of the seven files, with its own totals (1 step instead of 92), verifies clean.

If the record, the manifest and the page are regenerated together, `verify_steps`,
`verify_manifest` and `test_baseline_page.py` all pass, because each compares the record with
itself or with the page copied from it. The step total is one of the two figures CRITERION.md's pass
rule uses, so a shrunken baseline makes later work look worse or better than it is with every check
green. `path_records.verify_footprint` already does this correctly for bytes (it reads
`MODE_PATHS` at the pinned commit).
**Fix:** In `verify_steps`, require `record["rev"] == BASELINE_COMMIT`, and require the file list
to equal the Finalize list at that commit (reuse `path_records.baseline_mode_paths(repo,
BASELINE_COMMIT)["finalize"]`, or pin the seven paths as a constant). Reject an empty list. Add
mutants: empty list, one file dropped, revision changed.

### WR-03: Footprint and traces checks trust the commit written in the record

**Classification:** WARNING
**File:** `docs/design/lean-v2.15/tools/path_records.py:219-224` (`verify_footprint`), `:514-519`
(`verify_traces_record`); `docs/design/lean-v2.15/tools/step_count.py:281`
**Issue:** Each check resolves `record["baseline_commit"]` (or `rev`) and verifies the record
against *that* commit; none compares it with `BASELINE_COMMIT`. Reproduced: a footprint record
generated at `dd8e4ab~1` (Finalize 133,123 bytes, not the baseline's 136,114) verifies clean; a
steps record re-counted at `dd8e4ab~1` plus a regenerated manifest gives `[]` from both
`verify_manifest` and `check_steps`. So the command the page tells the owner to run
(`baseline_records.py verify --repo .`) can print `baseline holds` for records that are no longer
the 2.14.1 baseline. Inside the test suite this is caught, but only by
`test_baseline_page.py:327-338` (`clause_commit`), not by the verify command itself.
**Fix:** In `verify_footprint`, `verify_traces_record` and `verify_steps`, add
`if commit != BASELINE_COMMIT: problems.append(...)` before recounting, as
`verify_suite_record` (`baseline_records.py:316`) and `finalize_capture.verify` already do.

### WR-04: The proxy token figures in the footprint record are never recomputed

**Classification:** WARNING
**File:** `docs/design/lean-v2.15/tools/path_records.py:232-234`
**Issue:** `verify_footprint` checks only that `proxies.label` is the PROXY label. The numbers
under `proxies.modes` are not compared with `total_bytes`. Reproduced: setting
`proxies.modes.finalize["tokens@2.7"]` to `1` and the rule text to `"anything"` verifies clean;
deleting `proxies.modes` entirely also verifies clean. `test_baseline_page.py`
(`clause_proxy_figures`) copies the page figures from the same record, so a wrong proxy figure in
the record is shown to the owner as checked.
**Fix:** Recompute in `verify_footprint`: for each mode and each key `tokens@<ratio>`, require
`value == int(total_bytes / float(ratio))`, require `proxies.modes` to hold exactly the declared
modes, and require the rule text to equal the one `footprint_record` writes.

### WR-05: The suite record check accepts a baseline run that had errors or skips

**Classification:** WARNING
**File:** `docs/design/lean-v2.15/tools/baseline_records.py:318-322`
**Issue:** `verify_suite_record` requires `failed == 0` and `passed > 0`, then only checks that
`errors` and `skipped` match the summary line. Reproduced: a record with summary line
`3886 passed, 7 skipped, 4 errors in 1.00s`, `errors: 4`, `skipped: 7` verifies clean. The same
function gates `suite-record` at capture (`:509`), so a run with collection errors would be written
as the baseline. The page states the baseline run had no skips; nothing enforces it.
**Fix:**
```python
for key in ("failed", "errors", "skipped"):
    if record.get(key) != 0:
        problems.append("%s is %r, not 0" % (key, record.get(key)))
```
Add an errors mutant and a skipped mutant to `test_baseline_records.py`.

### WR-06: The stdlib-only gate passes imports that a stock Python does not have

**Classification:** WARNING
**File:** `.github/scripts/stdlib_only.py:38-40`, `:92-97`
**Issue:** Two ways a real violation passes. Reproduced with one planted module importing
`tomllib`, `annotationlib`, `requests` and `yaml`: only `requests` was reported.
1. The allowed list is `sys.stdlib_module_names` of the interpreter running the gate, which in CI
   is Python 3.14. A module that exists only in newer Pythons (`annotationlib` is 3.14-only,
   `tomllib` is 3.11+) passes, yet fails on an older stock Python such as the 3.9 that ships with
   macOS. The gate's stated promise is "runs on a stock Python with nothing installed".
2. A sibling is any `.py` basename anywhere under the plugin root (`local`, line 92), including
   folders that are not on the import path. A file `vendor/yaml.py` made `import yaml` pass.

**Fix:** For 1, the plugin names no minimum Python version, so the floor needs an owner ruling;
once named, pin the allowed set to that version's module list (a constant in the script) and
intersect it with `sys.stdlib_module_names`. For 2, accept a sibling only when it sits in the same
directory as the importing file.

## Info

### IN-01: `finalize_capture.verify` skips the sidecar check when the sidecar file is missing

**Classification:** INFO (advisory, below WARNING)
**File:** `docs/design/lean-v2.15/tools/finalize_capture.py:957-962`
**Issue:** `if os.path.exists(sidecar)` means a deleted `.sha256` file is not reported by the
standalone `finalize_capture.py verify`. Inside the whole-baseline check it is caught twice (the
manifest lists the file; `test_baseline_page.load_records` requires it), so nothing is lost today.
**Fix:** Report a missing sidecar as a problem instead of skipping.

### IN-02: `tar` is called without `-f -`

**Classification:** INFO (advisory, below WARNING)
**File:** `docs/design/lean-v2.15/tools/finalize_capture.py:290`
**Issue:** `["tar", "-x", "-C", dest]` relies on tar's default archive being standard input.
Reproduced on macOS: with `TAPE=/nonexistent/tape` in the environment the unpack fails
(`tar: /nonexistent/tape: No such file or directory`). It fails loudly (exit 2, "cannot unpack"),
and works on the owner's Mac and on ubuntu-24.04 as they are. Behaviour on a GNU tar built with a
different default device is unverified.
**Fix:** `["tar", "-x", "-f", "-", "-C", dest]`.

### IN-03: Three future workflow edits would get past the workflow text locks

**Classification:** INFO (advisory, below WARNING)
**File:** `.github/scripts/test_workflow_shape.py:232-234`, `:316-338`
**Issue:** The workflow itself is sound; these are gaps in the locks that guard later edits.
Reproduced by running the check functions on edited workflow text:
- `${{ toJSON(secrets) }}` in a run line: `no_secrets_holds` returns `[]` (the pattern wants
  `secrets.` or `secrets[`).
- `${{ github.ref_name }}` in a run line: `[]` (only `github.event` and `github.head_ref` are named).
  A branch name can carry shell characters.
- A job-level `env: PYTEST_ADDOPTS: --noconftest -o python_files=test_none*.py`: every text check
  returns `[]`. Nothing locks a floor on how many tests run; `-o` overrides are not on the
  refused-option list. Whether a narrowed run would also satisfy the three log guards was not run
  end to end (unverified).
**Fix:** Refuse any `${{` inside a `run:` block and any mention of `secrets`; refuse
`PYTEST_ADDOPTS` and `-o`/`--override-ini` outright; consider a minimum passed count in `check-log`.

### IN-04: The privacy checkers disagree on what counts as a private path

**Classification:** INFO (advisory, below WARNING)
**File:** `docs/design/lean-v2.15/tools/usage_fields.py:430`, `:167-172`, `:470-473`;
`docs/design/lean-v2.15/tools/path_records.py:59`; `docs/design/lean-v2.15/tools/finalize_capture.py:878-901`
**Issue:** No leak was found in any committed file. Confirmed inconsistencies:
- `usage_fields.py check-note` flags only `/Users/` and `.claude/projects`. A note holding
  `/home/runner/work/x` and `/private/var/folders/ab/T/s.jsonl` printed `note clean`, exit 0. The
  other two tools also flag `/home/` and `/private/` (and `/tmp/` in one of them).
- A mistyped flag echoes its value: `--sesion a=b=/Users/someone/secret/s.jsonl` printed the full
  path on standard error (argparse's own message). Standard error only, not a record.
- A key name holding both `retry` and a price word is printed: `retry_cost_usd` appeared under
  "retry key names" with exit 0, although the docstring says output naming cost, price or usd is
  stopped. It is a name, never a figure.
- `machine_path_problems` checks the account name of whichever machine runs it, so on GitHub it
  looks for `runner`, not the owner's account. The committed situations record holds neither.
**Fix:** One shared marker tuple for all three tools; route `usage_fields.py` argument errors
through a parser subclass that prints a fixed message (as `path_records.py` does); apply
`PRICE_WORD` to retry key names.

### IN-05: The page's no-price clause only sees a dollar sign followed by a digit

**Classification:** INFO (advisory, below WARNING)
**File:** `docs/design/lean-v2.15/tools/test_baseline_page.py:638-640`
**Issue:** `clause_no_price` matches `\$\s*\d`. A page line "About 5 USD a run, or $ five, or
5 dollars." returned `[]`. `usage_fields.price_problems` is stricter (any `$`).
**Fix:** Also flag `\bUSD\b`, `\bdollars?\b` and any `$`.

### IN-06: Test-only tools are version-pinned but not hash-pinned

**Classification:** INFO (advisory, below WARNING)
**File:** `.github/workflows/offline-suite.yml:33-35`, `:29`
**Issue:** `pip install pytest==9.0.3` pins pytest but not the packages it pulls in, with no
`--require-hashes`; `apt-get install zsh` and `python-version: '3.14'` float. With a read-only
token and no secrets the exposure is a wrong test result, not a compromise of the repository.
Practical impact unverified.
**Fix:** If wanted, install from a hash-locked requirements file and pin the full Python version.

## Convention

### CV-01: Workflow file name casing

**Classification:** CONVENTION (advisory; never blocks)
**File:** `.github/workflows/offline-suite.yml:1`
**Deviation:** file name casing is kebab (`offline-suite`).
**Convention:** file-name-casing should be snake (derived by `verify conventions --check`).
**Suggested fix:** rename to a snake-cased basename. Note: the name `offline-suite.yml` is locked
by `test_workflow_shape.py:184` and is the usual style for workflow files, so leaving it is
reasonable. The tool has no rule pack for Python; the other files were skipped by it.

## Set aside (needs ruling)

### SA-01: The headline replay figure is a hand-typed string that no check re-derives

**Where:** `docs/design/lean-v2.15/tools/baseline_records.py:359-385` (`verify_manifest` ignores
`facts`), `:530-539` (`replay_diff` comes from `--replay-diff <text>`)
**Why excluded:** The page says the verify command does not re-run the replay comparison, so this
is a stated limit rather than a hidden one.
**Effect if left as is:** "replay 170 runs, 0 differing" on the page is backed only by the text
typed when the manifest was made. Reproduced: a manifest whose `replay_diff` reads
`runs compared: 9999, runs differing: 0` gives `[]` from `verify_manifest`; the page lock then
checks the page against that string.
**Needs:** ruling from the developer: accept as a recorded one-time figure, or have the tool derive
the string from the replay run itself.

### SA-02: The stdlib-only gate does not look at Python run from instruction files

**Where:** `.github/scripts/stdlib_only.py:43-55`
**Why excluded:** The script's stated scope is every shipped `*.py` file, and it meets that scope
(33 files, none third-party).
**Effect if left as is:** Instruction files under `phases/` (for example
`phases/review/50-fix-loop.md`, `phases/deep-review/01d-coverage.md`) run inline `python3`
commands. A third-party import written there would break a stock install and the gate would stay
green.
**Needs:** ruling from the developer: in scope / defer / accept.

---

_Reviewed: 2026-11-14T07:29:15Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
