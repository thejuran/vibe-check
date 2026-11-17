---
phase: 62-baseline-and-continuous-test-run
plan: 10
subsystem: baseline-tools
tags: [finalize, capture, baseline, pinned-commit, determinism, fingerprint]
requires:
  - "62-04: finalize_capture.py harness (materialize, normalise, FenceWalk2141, capture_one)"
provides:
  - "docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json: the five D-07 situations recorded at dd8e4ab, sha256 04a453ffa7cdc965964c694dcad9873c9239e4ebd9cb7e136c06516d21203c55"
  - "finalize_capture.py: situation_inputs, stop_sentence, capture_situation, capture, record_text, verify, machine_path_problems, current_account; CLI capture/verify"
affects:
  - "Phase 63: a helper driver must implement run(situation_id, vc_root, workdir, leg=None) and return the same outputs (legs included); verify() is the comparison"
tech-stack:
  added: []
  patterns: ["situation legs: further walks of one situation stored under `legs` in the same schema", "rebuild-once rule as a driver constant (REBUILDS=1) so a mutant can switch it off"]
key-files:
  created:
    - docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json
    - docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json.sha256
  modified:
    - docs/design/lean-v2.15/tools/finalize_capture.py
    - docs/design/lean-v2.15/tools/test_finalize_capture.py
decisions:
  - "card-first (and fresh-shell-restart) step 3 re-mints BLOBFILE after the owner's answer, following the 2.14.1 prose rather than the older test's reuse of the pre-card file"
  - "All write routes run the full close tail (prior-report archive, stand-in REVIEW.md, state archive) so files_archived/state_closed carry real values"
  - "A situation's further walks are recorded under a `legs` key (one-rebuild/second-failure, refused-close/unarchivable-report)"
  - "mktemp scratch files are not Finalize's writes and are not listed in files_written; the walk's TMPDIR is <WORK>/scratch"
metrics:
  duration: "~45 min"
  completed: 2026-11-14
  tasks: 2
  files: 4
---

# Phase 62 Plan 10: Five Finalize situations recorded at 2.14.1 Summary

The capture tool now walks all five Finalize situations from the pinned v2.14.1 commit (dd8e4ab). The new ones are the one automatic rebuild, the refused close and the fresh-shell restart. The five-situation record is committed with its fingerprint and re-derives byte for byte. `verify` names any difference by situation, and a lock keeps machine paths out of the record. That lock trips on planted paths.

## What was built

- **Three new walks** in `FenceWalk2141`. All five situations go through one rebuild-once rule: `gated()` with `REBUILDS = 1`. After that, the stop sentence is read from the pinned `90-finalize.md`.
  - `one-rebuild`: the first BLOBFILE is gone, so counts fails. One rebuild mints a new BLOBFILE, recounts, and the gate returns `write` on a new GATEFILE. Leg `second-failure`: the BLOBFILE is gone on both attempts, so the walk stops.
  - `refused-close`: the gate input is malformed ("not json") on both attempts. Each gate fence exits 1 with empty stdout and keeps its traceback in `<GATEFILE>.err`. Finalize stops with the stop sentence. Leg `unarchivable-report`: a stamped earlier REVIEW.md sits in a read-only `.turingmind`. The prior-report archive fence (the four-backtick one) fails, and Finalize stops with that fence's own message. The directory's permissions are restored on every path. Running as root raises a named `UsageError`; the walk is never skipped silently.
  - `fresh-shell-restart`: the six-row fixture plus a last-pass fix-obsolete verdict, bound to an unchanged HEAD blob. Before the card the gate returns `outstanding-to-phase-5`. The owner dismisses rows 1-5. A new BLOBFILE is re-fingerprinted, the counts are redone (the verdict is still honoured), a new GATEFILE is made, and the gate returns `write`.
- **Record API.** `capture()` returns `{schema, baseline_commit, driver: "fence-walk-2.14.1", normalisation, situations, sha256}`. `record_text()` writes it with sorted keys, two-space indent and a trailing newline, keeping the situations in D-07 order. `verify(repo, record_path, driver=None, fresh=None)` returns `[]` or one line per difference, prefixed with the situation id, `sha256`, `record` or the top-level key. It also checks the `.sha256` sidecar and the D-07 order. `machine_path_problems(text, account=None)` flags `/Users/`, `/private/`, `/tmp/`, `/home/`, and the account name when it is longer than three characters and appears as a whole word.
- **CLI.** `capture` refuses to write a record that holds a machine path (exit 1, `RECORD HOLDS A MACHINE PATH — STOPPING`, no file written). Otherwise it writes the record and its `.sha256`. `verify` exits 0 when the record matches, 1 with `FINALIZE BASELINE DIFFERS — STOPPING` and the difference lines, and 2 on unusable input.

### Per-situation results (committed record, pinned dd8e4ab)

| Situation / leg | Gate decisions | Stop sentence | Report entries | Files written | Files archived | state_closed | Tally (commands / values / writes) |
|---|---|---|---|---|---|---|---|
| clean-close | `write` | none | 2 | REVIEW.md | state `.archived-<TIME>` | true | 8 / 2 / 3 |
| card-first | `outstanding-to-phase-5`, `write` | none | 6 | REVIEW.md | state `.archived-<TIME>` | true | 17 / 9 / 6 |
| one-rebuild | `write` (after one rebuild) | none | 2 | REVIEW.md | state `.archived-<TIME>` | true | 10 / 3 / 3 |
| one-rebuild / second-failure | none | "Finalize stopped — nothing was written or archived; run `--finalize` again." | none | none | none | false | 4 / 2 / 0 |
| refused-close | none (both gate runs exit 1) | same stop sentence | none | none | none | false | 10 / 4 / 4 |
| refused-close / unarchivable-report | `write` | "Finalize stopped — the earlier REVIEW.md could not be archived (the line above says why). …both kept." | none | none | none | false | 7 / 2 / 2 |
| fresh-shell-restart | `outstanding-to-phase-5`, `write` | none | 5 | REVIEW.md | state `.archived-<TIME>` | true | 17 / 9 / 6 |

## Verification (observed)

- `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_finalize_capture.py`: **82 passed, 10 subtests passed**. After Task 1 it was 59 passed.
- RED was observed for both tasks:
  - Task 1: 5 failed, 17 errors (`capture_situation`, `stop_sentence` and `SCRATCH_DIR` did not exist yet).
  - Task 2: 1 failed, 22 errors (no record, `capture` or `verify` yet).
- I ran the plan's full Task 2 `<verify>` command from a script file. It exited 0, and the output included `finalize baseline matches (5 situations)` and `break-test-ok`. The planted `/Users/x/work` copy made `verify` exit non-zero.
- I captured twice, once into the repo and once into the session scratchpad. `cmp` found the record and the `.sha256` files byte-identical, with the same sha256 `04a453ff…`.
- `grep -E "/Users/|/private/|/home/|/tmp/|<account>"` on the committed record matched nothing.
- `git status --porcelain -- plugins`: empty after each task.
- Each mutant was run in the suite and tripped its check:
  - **REBUILDS = 0.** The one-rebuild outcome check fails, and the normalised outputs differ. Against the committed record, `verify` names `one-rebuild` and not `clean-close`.
  - **`_Walk.stop` patched to write REVIEW.md.** `refused-close` records `files_written == [".turingmind/REVIEW.md"]`.
  - **Four tamper mutants.** I changed one stdout character, one gate action, removed one situation, and changed the stored sha256. Each was named by its situation, or by `sha256` only.
  - **Three planted paths** (`/Users/x/work`, `/home/runner/work`, `/private/tmp/vc.abc`). Each was reported.
  - **`machine_path_problems` patched to return `[]`.** All three planted-path checks then fail.
  - **Root.** With `os.geteuid` patched to 0, the unarchivable leg raises a `UsageError` naming root.
- **Not verified: determinism on Linux.** Both captures ran on macOS only. The must-have says "on the owner's Mac and on Linux"; the Linux half needs a CI or Linux run, for example the continuous test run planned elsewhere in this phase.

## How the two carried judgement calls were settled

1. **Card-first step 3 re-mints BLOBFILE: kept (faithful to 2.14.1).** The pinned `90-finalize.md` step 3 says to "run step 1 again — a new mktemp fence printing a NEW `BLOBFILE=` … the pre-card `BLOBFILE=` is never reused". The pinned test `test_post_decision_recount_refingerprints_head` locks that. This plan's own behaviour for `fresh-shell-restart` also requires "a newly minted BLOBFILE" after the answers. The older tests (`test_card_route_records_then_writes`, and the recount inside `test_post_decision_rerun_decides_on_a_fresh_gatefile`) still recount on the same file. Their text lags the prose. D-08 records what 2.14.1 produces when its instructions are followed, so the prose wins. Cost: card-first records 3 more commands, 1 more write and 1 more carried value than the older sequence would.
2. **Both close routes run the full close tail: kept.** D-07 situation 4 is defined by "writes nothing and archives nothing". That is only a real comparison if the write routes show what writing and archiving look like. This plan's own `unarchivable-report` leg also runs the prior-report archive fence, which exists only in that tail. Without the tail, `files_archived` and `state_closed` would be constant on every route, so they would be decorative. The stand-in REVIEW.md holds only the verdict and format-stamp lines, because the prose is written by the model. Nothing in the plan or in D-07/D-08 limits the walk to the report.

Neither call needed a checkpoint: the plan text, D-07/D-08 and the pinned prose all point the same way.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The fixed outputs schema had no place for a situation's second leg**
- **Found during:** Task 1
- **Issue:** The plan asks for a second walk in `one-rebuild` ("recorded as the situation's second leg") and an unarchivable-report walk in `refused-close`. The 8-key outputs schema cannot hold two outcomes, and the record must keep exactly five situation ids.
- **Fix:** Each situation record is the main walk's 8 keys plus `legs: {name: <same 8 keys>}`, which is `{}` for single-walk situations. `driver.run(..., leg=None)` and `capture_one(..., leg=None)` take a leg name. Legs are declared in `SITUATIONS[sid]["legs"]` as input overrides.
- **Cost if wrong:** Phase 63's driver must accept `leg=` and reproduce the legs. If legs are judged out of place, two situation ids would have to be added instead, which breaks the five-id record.
- **Files modified:** finalize_capture.py, test_finalize_capture.py
- **Commit:** 691180c

**2. [Rule 1 - Bug] Scratch temp files counted as "files written", and the walk's `tmp` dir would trip the `/tmp/` lock**
- **Found during:** Task 1 and Task 2 design
- **Issue:** In 62-04, `files_written` listed the fences' mktemp files (`tmp/vc.XXXXXX`). So `refused-close` could never record an empty `files_written`, although the stop sentence itself says "nothing was written". Separately, the recorded paths `<WORK>/tmp/vc.XXXXXX` contain `/tmp/`, which the machine-path lock must reject.
- **Fix:** The walk's TMPDIR is now `<WORK>/scratch`. Files under it are not listed in `files_written`; they still appear in the steps' printed paths and the tally. The rule is written into `NORMALISATION`.
- **Cost if wrong:** clean-close and card-first no longer list their 3 and 6 scratch files. Phase 63 must apply the same exclusion.
- **Commits:** 691180c, 43d1b7e

**3. [Rule 3 - Blocking] "Sorted keys" conflicted with the required situation order**
- **Found during:** Task 2
- **Issue:** The action asks for sorted keys, but the verify command asserts `list(situations)` is in D-07 order. Fully sorted keys would put card-first first.
- **Fix:** `record_text` sorts keys everywhere except the situations mapping, which keeps the D-07 order. The fingerprint is over canonical JSON, so the layout does not affect it.
- **Cost if wrong:** None to the fingerprint; only the file layout.
- **Commit:** 43d1b7e

**4. [Rule 2 - Missing] `capture` writes the `.sha256` sidecar itself, and `verify` checks the sidecar and the situation order**
- **Found during:** Task 2
- **Fix:** The sidecar is no longer a separate manual step, so it cannot drift from the record. `verify` reports a sidecar mismatch and an out-of-order situations object.
- **Cost if wrong:** Low; this adds checks only.
- **Commit:** 43d1b7e

**5. [Scope] Dropped the `--situation` option and `capture_record` from 62-04**
- **Found during:** Task 2
- **Issue:** The record is always all five situations. The partial-capture path wrote an older schema (`commit`, per-situation `inputs`/`sha256`) that nothing reads.
- **Fix:** Both are replaced by `capture()`.
- **Cost if wrong:** Partial captures for debugging now go through `capture_situation()` in Python, not the CLI.
- **Commit:** 43d1b7e

## Assumption Drift (advisory)

**1. one-rebuild's trigger is a missing BLOBFILE, not an empty gate input**
- **Found during:** Task 1
- **Planned:** 62-04's placeholder `SITUATIONS` text said the first attempt's gate input is left empty. This plan's behaviour says "the first counts step fails on a missing path".
- **Actual:** The trigger follows this plan: the BLOBFILE is gone before counts. The bad-gate-input path is covered by `refused-close` (malformed on both attempts).
- **Cost if wrong:** If Phase 63 expects the empty-GATEFILE rebuild in one-rebuild, the situation inputs change and the record must be re-captured.

**2. fresh-shell-restart uses the 2.14.1 walk's literal HEAD blob, not a real git repository**
- **Found during:** Task 1
- **Planned:** The plan expected a real git repo with fixed author and dates "where a walk needs" a HEAD re-fingerprint.
- **Actual:** The walks this situation mirrors (`test_post_decision_recount_refingerprints_head`) write the blob value straight into each BLOBFILE (`blob-pre-card`) and run no git. The HEAD-fingerprint commands in step 1 are prose, not fences, and depend on `$GUARD_PY` from another file. So the driver writes the same value as the existing walk, and no git repo or `gitfixture` import was needed. The situation gained a last-pass fix-obsolete verdict, so the re-fingerprint shows up in the record (`verified_obsolete_hashes` on both counts). Because that verdict closes one finding, the answer is `dismiss 1,2,3,4,5`.
- **Cost if wrong:** If a real `git rev-parse` walk is wanted, step 1's prose commands would have to be simulated (including the guard), and the record re-captured.

**3. A stopped walk records `report: null` even when the decisions-report step ran**
- **Found during:** Task 1 (unarchivable-report leg)
- **Planned:** `report` is the decisions-report JSON.
- **Actual:** When Finalize stops before the Write, nothing is reported to the owner, so `report` is null. The report JSON is still visible in that step's stdout.
- **Cost if wrong:** One field in one leg changes on re-capture.

## Known Stubs

None. The "not walked yet" usage error from 62-04 and the missing `verify` subcommand are both gone.

## Threat Flags

None beyond the plan's register:
- T-62-17: fences come only from the `git archive` of the fixed commit.
- T-62-18: the machine-path lock, with the capture refusal and planted-path mutants.
- T-62-19: `verify` and the tamper mutants.
- T-62-56: running as root is a named usage error.

The read-only directory leg chmods only a directory inside the walk's own temp work dir and restores it in a `finally`.

## TDD Gate Compliance

- Task 1: `77fe838` test → `691180c` feat
- Task 2: `c3a4eed` test → `43d1b7e` feat

## Self-Check: PASSED

- FOUND: docs/design/lean-v2.15/tools/finalize_capture.py
- FOUND: docs/design/lean-v2.15/tools/test_finalize_capture.py
- FOUND: docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json
- FOUND: docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json.sha256
- FOUND commits: 77fe838, 691180c, c3a4eed, 43d1b7e
