---
phase: 62-baseline-and-continuous-test-run
plan: 07
subsystem: baseline-evidence (lean-v2.15 tool kit)
tags: [BASE-03, D-08, suite, replay, manifest, fingerprint]
requires:
  - "62-03: step_count.verify_steps"
  - "62-05: path_records.verify_footprint / verify_traces_record"
  - "62-10: finalize_capture.verify"
provides:
  - docs/design/lean-v2.15/tools/baseline_records.py (normalise_replay, replay_fingerprint, recording_count, capture_replay, expected_replay_file, build_manifest, write_manifest, verify_manifest, verify_replay, parse_summary_line, suite_record, verify_suite_record, check_steps, verify_baseline, main)
  - docs/design/lean-v2.15/baseline/suite-v2.14.1.json
  - docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.md (+ .sha256), 12 recordings
  - docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.no-private.md (+ .sha256), 0 recordings
  - docs/design/lean-v2.15/baseline/MANIFEST.json (10 files)
affects: [62-11 baseline page and kit README, Phase 63 comparison, Phase 65 equivalence gate, CI test run]
tech-stack:
  added: []
  patterns: [two-condition replay fingerprint chosen by census count, stand-in replay.py for unit tests, manifest file-set equality + per-file sha256]
key-files:
  created:
    - docs/design/lean-v2.15/tools/baseline_records.py
    - docs/design/lean-v2.15/tools/test_baseline_records.py
    - docs/design/lean-v2.15/baseline/suite-v2.14.1.json
    - docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.md
    - docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.md.sha256
    - docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.no-private.md
    - docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.no-private.md.sha256
    - docs/design/lean-v2.15/baseline/MANIFEST.json
  modified: []
decisions:
  - "Replay fingerprint = sha256 of the report with lines matching ^- (HEAD|head|generated( \\(UTC\\))?): removed; 12-recording fingerprint 142de13d…, 0-recording fingerprint 3eb053ca…"
  - "Suite record stores the Python version of the interpreter pytest itself runs under (3.12.12, read from the pytest launcher's shebang), not the python3 that runs the record tool (3.14.5)"
  - "verify_baseline also cross-checks the traces record's declared lists against the footprint record, as path_records verify does"
metrics:
  duration: ~40 min
  completed: 2026-11-14
  tasks: 2
  files: 8
---

# Phase 62 Plan 07: Suite and replay baseline with manifest Summary

The 2.14.1 suite result and the archived replay output are now pinned under `docs/design/lean-v2.15/baseline/`. The replay output has one fingerprint for each recording condition. All ten record files are tied together in `MANIFEST.json`, and one `baseline_records.py verify` command re-derives every record on every test run. With the 12 private recordings that means the primary checkout; with none it means a linked worktree or CI. No test is skipped in either condition.

## Figures for plan 62-11 (the baseline page)

| Item | Value |
|---|---|
| Suite summary line | `3886 passed, 5060 subtests passed in 187.57s (0:03:07)` (0 failed, 0 skipped, 0 errors; wall time 188 s) |
| Suite command | bare `pytest -q -p no:cacheprovider` from `plugins/vibe-check/scripts` in the primary checkout |
| Runner / Python / platform | pytest 9.0.3 / Python 3.12.12 (pytest's own interpreter) / Darwin 27.2.0 (macOS 27.2.1) |
| Plugin tree | `90e0697363ee5c09bb7942a963cf670e16717c4a`. It is the same at `dd8e4ab` (v2.14.1) and at the run commit `e1881b3`. |
| Replay, 12 recordings (primary checkout) | `replay-baseline-v2.14.1.md`, fingerprint `142de13d56c61c5794d24bb432332db1deaf06ae1c102ee742f32fff59c1ae24` |
| Replay, 0 recordings (linked worktree / CI) | `replay-baseline-v2.14.1.no-private.md`, fingerprint `3eb053ca81f283401f7b1296bbd28b3d2cc157d1ac528323de68e488c3dbb1f0` |
| Normalisation rule | drop every line matching `^- (HEAD|head|generated( \(UTC\))?): `, then sha256 the remaining bytes |
| `replay.py diff --base rev:v2.14.1 --scorer rev:v2.14.1` (primary) | `runs compared: 170`, `runs differing: 0`, `roots: all (7 roots)`, exit 0 |
| census | `scoreable: 66` in both conditions; `transcripts: 12` in the primary checkout, `transcripts: 0` in the worktree |

## Tasks

| # | Task | Commits |
|---|------|---------|
| 1 | baseline_records.py: replay fingerprints, manifest, verify_baseline, tamper mutants | 1b19875 (test, RED), 5143060 (feat, GREEN) |
| 2 | Capture the suite and replay records at 2.14.1, build the manifest, committed-baseline tests | 10b6f76 |

## Verification (observed)

- **RED.** `pytest` on the new test file failed at collection with `ModuleNotFoundError: No module named 'baseline_records'`.
- **GREEN.** The test file passed 51 tests. Every part of the Task 1 verify command passed:
  - skip count 0
  - `MODE_PATHS|count_path` count 0
  - `verify_steps` present
  - `import replay` count 0
  - `git status --porcelain -- plugins` empty
- **Primary-checkout preconditions.** The tool blocks git commands that target the primary checkout, so I ran these from the worktree, which shares the object store:
  - `feat/v2.15-phase-62` = `e1881b3`. `e1881b3:plugins`, `dd8e4ab:plugins` and the worktree's `HEAD:plugins` all equal `90e0697…`.
  - I could not run `git status` in the primary checkout. Instead, a scratch script compared the git blob hash of every one of the 167 tracked files under `plugins/` with tree `90e0697`. All matched before the suite and again after the suite and the replay runs.
  - The only extra files were ones that git already ignores, and they were there before the run: `.ruff_cache/*` and `plugins/vibe-check/.planning/…`.
- **Suite.** `3886 passed, 5060 subtests passed in 187.57s (0:03:07)`, rc 0. This matches the released count.
- **Replay determinism.**
  - I captured each condition twice: the committed file plus a scratch copy. The fingerprints were equal: 12 recordings `142de13d…` both times, 0 recordings `3eb053ca…` both times.
  - Neither report holds `/Users/`, `/private/`, `/home/` or `/tmp/`.
  - Longest line: 327 characters with recordings (fixed prose from replay.py), 195 without.
  - The two reports differ only in the HEAD line, the transcript-coverage counts and the per-run `recovered: N` column. Nothing in either report is transcript text.
- **Full test run.** `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools` gave **290 passed, 10 subtests passed**, 0 failed, 0 skipped.
- **verify (0 recordings).** `python3 docs/design/lean-v2.15/tools/baseline_records.py verify --repo .` printed `baseline holds`, **exit 0**, both before and after the Task 2 commit.
- **verify (12 recordings).** The same command with `--scripts-dir <primary checkout>/plugins/vibe-check/scripts` printed `baseline holds`, **exit 0**.
- **Recording counts exercised.** Both. 0 through the test file and `verify` in the worktree. 12 through `verify --scripts-dir` pointed at the primary checkout's replay.py, which sees the 12 recordings. I did not run the test file itself from the primary checkout: it is a linked worktree's file, and the plan only asks for that when W is the primary.
- **Task 2 JSON assertions.** Passed: `json-ok 10`, which means 10 manifest files.
- **Mutants run and seen to trip.**
  - **In-suite mutants:**
    - four manifest tampers: byte changed, record deleted, extra file, hash edited
    - replay: report body character changed, `.sha256` text changed, re-derived body differs, normaliser patched to keep the `generated` line (a clean check first, then a named failure), missing sidecar
    - unexpected count 3 and 7, each named `UNEXPECTED RECORDING COUNT <N> — STOPPING`
    - suite: plugins_tree altered, failed=1 with a consistent summary line, passed in (0, -1, "3886", True), counts that disagree with the summary line
    - fence agreement: column-0 pattern patched into `finalize_capture.FENCE_RE` (18 → 9) and separately into `step_count.FENCE_OPEN`
    - `verify_manifest` patched to `[]`, after which `verify_baseline` misses a byte-level tamper of a `.sha256`
    - committed-record tampers on the suite, steps and replay records, each named by file
  - **Source mutants**, each applied to `baseline_records.py` and then restored, with a byte-compare afterwards. Each one failed at least one test:
    - manifest hash compare disabled: 4 failed
    - re-derivation compare disabled: 2 failed
    - unexpected-count check disabled: 3 failed
    - failed-is-zero check removed: 1 failed
    - passed-positive check weakened: 1 failed
    - steps check dropped from `verify_baseline`: 1 failed
    - suite check dropped from `verify_baseline`: 1 failed
- **Decoupling.** With `footprint.MODE_PATHS["finalize"]` patched to 6 entries, the change was confirmed live (`count_path` sees 6 files), and `check_steps` still returned `[]`.
- **Fence agreement.** `step_count` counts 18 bash blocks in `90-finalize.md` at `dd8e4ab`, and `finalize_capture.extract_fences` finds 18.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two suite-record mutants were decorative at first**
- **Found during:** Task 1, while running source mutants by hand
- **Issue:** I removed the `failed == 0` rule from the source, and the "failed is nonzero" test still passed. The summary-line consistency check also reports a changed `failed`, so it hid the missing rule. The `passed is positive` test had the same weakness.
- **Fix:** The failed mutant now uses a consistent `1 failed, …` summary line and asserts exactly `["failed is 1, not 0"]`. The passed mutant asserts a line starting `passed is `. I re-ran both source mutants, and each failed 1 test.
- **Cost if wrong:** none; test-only.
- **Files modified:** test_baseline_records.py
- **Commit:** 5143060

**2. [Rule 3 - Blocking] I could not run git against the primary checkout from this worktree**
- **Found during:** Task 2 step 1
- **Issue:** The agent sandbox refuses `git -C <primary>` and `cd <primary> && git …`, so I could not run the plan's `git -C "$P" rev-parse HEAD:plugins` and `git -C "$P" status --porcelain -- plugins`.
- **Fix:**
  - Tree ids: I resolved them from the worktree, which shares refs and objects. The primary's branch tip `feat/v2.15-phase-62` was `e1881b3`, and its `:plugins` tree equals `90e0697`.
  - Cleanliness: a scratch script compared the blob hash of every tracked file under the primary's `plugins/` with tree `90e0697`, before the suite and again after the suite and the replay runs.
- **Cost if wrong:** If the primary's HEAD were not the branch tip, the tree-id check would not prove anything about it. The file-by-file blob comparison is the stronger check, and it is independent of that.

**3. [Rule 2 - Missing check] Extra consistency checks**
- `verify_suite_record` re-parses `summary_line` and requires the stored counts to agree with it.
- `verify_manifest` checks `schema`, `baseline_commit` and `plugins_tree`.
- `verify_baseline` also runs `path_records.private_content_problems` on the footprint record, and the traces-declared vs footprint-files cross-check from `path_records verify`.
- **Cost if wrong:** a stricter verifier; a re-capture must keep these consistent, which the tools already do.

**4. CLI additions**
- `suite-record` and `manifest` take `--captured YYYY-MM-DD`, because the module's allowed import set has no date source.
- `manifest` takes `--replay-diff <text>`, so the figures written are the ones actually seen.
- `verify` takes `--baseline-dir` and `--scripts-dir`. `--scripts-dir` is how the 12-recording condition was checked from the worktree.
- `capture-replay` writes the `.sha256` itself, the same pattern as `finalize_capture capture`.
- **Cost if wrong:** cosmetic.

## Assumption Drift (advisory)

**1. Python version in the suite record**
- **Found during:** Task 2
- **Planned:** `python` = `platform.python_version()`.
- **Actual:** pytest runs from a pipx venv on Python 3.12.12, while `python3` on PATH is 3.14.5. The record stores pytest's interpreter, read from the launcher shebang, and falls back to `platform.python_version()` when the shebang is not an absolute interpreter path.
- **Cost if wrong:** One field would read 3.14.5 instead of 3.12.12, which is not the Python the suite actually ran on.

**2. The replay fingerprint does not move when the live scorer changes**
- **Found during:** Task 2, reading `replay.py _cmd_baseline`
- **Planned:** The plan says Phase 65's equivalence gate relies on re-deriving the replay result.
- **Actual:** `replay.py baseline` scores with the pinned blob `BASELINE_SCORE_BLOB` (`b21f7f3…`), not the working-tree `score.py`. The fingerprint therefore pins replay.py's own logic, the archived runs, the recordings and the b3 manifest. A change to `plugins/vibe-check/scripts/score.py` alone does not move it.
- **Cost if wrong:** If Phase 65 expects this fingerprint to catch scorer changes, it also needs `replay.py diff --base rev:v2.14.1 --scorer path:<live>`. The manifest records that figure (170 compared, 0 differing), but the standing verify does not re-run it.

## Known Stubs

None.

## Threat Flags

None. The register's mitigations are all in place:
- **T-62-33:** the manifest, the re-derivation and the tamper mutants.
- **T-62-34:** tree-id checks, plus the blob-level clean check before and after the run.
- **T-62-35:** the reports hold no machine path, their longest line is 327 characters, and they are the same kind of output as the `b3-ground-truth/REPLAY-REPORT-*` files.
- **T-62-36:** the second fingerprint and the named count failure; the test file has no skip.
- **T-62-37:** replay.py runs from an argument list with a timeout of 300 seconds, and a test checks that every `subprocess.run` call has a timeout.
- **T-62-38:** `-p no:cacheprovider`, the clean check after the run, and nothing else was run in the primary checkout during the suite.

## TDD Gate Compliance

- Task 1: `1b19875` test (RED, collection error) → `5143060` feat (GREEN, 51 passed).

## Self-Check: PASSED

- FOUND: docs/design/lean-v2.15/tools/baseline_records.py
- FOUND: docs/design/lean-v2.15/tools/test_baseline_records.py
- FOUND: docs/design/lean-v2.15/baseline/suite-v2.14.1.json
- FOUND: docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.md (+ .sha256)
- FOUND: docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.no-private.md (+ .sha256)
- FOUND: docs/design/lean-v2.15/baseline/MANIFEST.json
- FOUND commits: 1b19875, 5143060, 10b6f76
