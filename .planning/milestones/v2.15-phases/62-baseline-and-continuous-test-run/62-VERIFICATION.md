---
phase: 62-baseline-and-continuous-test-run
verified: 2026-11-14T16:03:53Z
status: passed
score: 5/5 roadmap success criteria verified (1 by recorded owner decision); must-haves of all 11 plans hold
has_blocking_gaps: false
overrides_applied: 1
overrides:
  - must_have: "Current mode-path bytes and actual loaded-file traces are recorded for plain review, deep review and Finalize, kept separate from any token or price estimate"
    reason: "Deep review has no recorded 2.14.x session, so its trace is the declared file list labelled 'declared, not observed' with the gap named. Owner decisions D-09 and D-19 in 62-CONTEXT.md rule that a gap is named and never filled by running a session. Plain review (4 sessions) and Finalize (1 session) are observed."
    accepted_by: "owner (62-CONTEXT.md D-09, D-19)"
    accepted_at: "2026-11-13"
---

# Phase 62: Baseline and continuous test run — Verification Report

**Phase Goal:** Before any extraction starts, the owner has a go/no-go note on cost visibility built from existing records, the 2.14.1 behaviour and footprint are pinned as the comparison baseline with the improvement criterion written down, and every push and pull request to `main` runs the offline suite automatically (999.12)
**Verified:** 2026-11-14T16:03:53Z
**Status:** passed
**Re-verification:** No — initial verification
**Checked at:** local `main` `149c1d0` (= `origin/main` `d0adb5b` plus two unpushed planning-only commits)

## Goal Achievement

Every claim below was checked against the repository, the committed records or GitHub. No SUMMARY claim was used as evidence.

### Observable Truths (roadmap success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A go/no-go note from existing local records names trustworthy usage fields per run and per lane, states missing attribution and names the smallest useful report; nothing reconstructed or invented, no paid run | VERIFIED | `62-COST-NOTE.md`: verdict first (NO-GO), a field table per run and per lane for model, input, output, cache-creation, cache-read, retries and elapsed time, a `What is missing` section, a `Smallest useful report` section, and the owner's recorded decision. I re-ran `usage_fields.py` on the five named sessions: every token total and message count in the note's `Numbers` table matched the logs exactly (for example Finalize 38 / 9,574 / 105,309 / 1,997,183 over 19 messages; smoke2141/b0294925 run 170 / 56,751 / 524,046 / 9,498,841 over 77). `usage_fields.py check-note` on the note prints `note clean`. |
| 2 | Mode-path bytes and actual loaded-file traces recorded for plain review, deep review and Finalize, separate from any token or price estimate | PASSED (override) | Bytes: I recounted every file of all six paths in `footprint-v2.14.1.json` with `git cat-file -s` at `dd8e4ab`: 0 mismatches (plain 192,057 / 13 files, deep 268,997 / 19, Finalize 136,114 / 7). Proxy token figures sit in their own `proxies` block labelled `PROXY — derived from bytes, not measured, not a bill`. Traces: `traces-v2.14.1.json` has plain review `observed` (4 sessions), Finalize `observed` (1 session), deep review `declared, not observed` with the gap named. Override: owner decisions D-09 and D-19. |
| 3 | A pinned behavioural baseline of the 2.14.1 code and its archived replay results are retained before any refactoring starts | VERIFIED | `baseline/` holds the suite record (3886 passed, 0 failed, 0 skipped at plugin tree `90e0697…`), two replay reports with fingerprints, the five-situation Finalize record with its fingerprint, and `MANIFEST.json`. All ten manifest hashes match my own `shasum`. `baseline_records.py verify --repo .` prints `baseline holds` here and in a clean clone without the private recordings. "Before any refactoring": `git rev-parse dd8e4ab:plugins HEAD:plugins origin/main:plugins` gives `90e0697363ee5c09bb7942a963cf670e16717c4a` three times; `git diff dd8e4ab HEAD -- plugins` is empty. |
| 4 | Comparison workload and improvement criterion written down before any extraction; if attribution is unavailable, accounting stops and labelled footprint/operation counts are named as the evidence | VERIFIED | `docs/design/lean-v2.15/CRITERION.md`: the two measures (bytes loaded, model-run steps), the pass rule (at least one drops, neither grows, identical behaviour), no percentage target, the revert default, the five named Finalize situations, and the `Usage and cost` section naming the two labelled counts as the evidence. Baseline figures 136,114 bytes and 92 steps. My own regex recount at `dd8e4ab` gives 42 bash blocks over the record's seven files, 18 of them in `90-finalize.md`, as stated. Plugin tree unchanged, so no extraction has begun. |
| 5 | One workflow runs the offline suite and the stdlib-only check on every push and every pull request to `main`; no secrets, no paid runs, no live model calls, no branch-protection change; `main` green on the release baseline, a deliberately failing commit on a throwaway branch red | VERIFIED | See the GitHub evidence table below. |

**Score:** 5/5 (4 verified, 1 passed by recorded owner decision)

### GitHub evidence (read-only `gh`)

| Check | Result |
|-------|--------|
| Workflows registered | One: `offline-suite`, `.github/workflows/offline-suite.yml`, active |
| Triggers | `push` on `branches: ['**']`; `pull_request` on `branches: [main]` |
| Token and secrets | `permissions: contents: read`; no `secrets.` reference; `persist-credentials: false`; both actions pinned to full commit ids; `gh secret list` prints nothing |
| Paid or live calls | Steps are checkout, Python setup, `apt-get install zsh`, `pip install pytest==9.0.3`, two guard scripts, pytest, two guard scripts. No model call. |
| Branch protection | `branches/main` `.protected` is `false`; `rulesets` is `[]` |
| `main` first run 43611870373 | `success`, event `push`, head `d0adb5b…`, every step `success`. Log: `33 shipped .py files; third-party imports: none`, `4324 passed, 2 skipped, 5 deselected, 5300 subtests passed`, `skipped set matches the recorded 2`. It is the only run listed for `main`. |
| Red proof 43568391505 | `failure`, branch `ci-red-proof`, head `29f9acd…`. Failing step `Offline suite`; stdlib check and list guard `success`. Log: `test_footprint.py:145: AssertionError: 84534 != 84535`, `1 failed, 4323 passed`. The commit is a one-line change to one assertion. Branch no longer exists on GitHub; no pull request was opened from it. |
| Green branch run 43567045328 | `success`, branch `feat/v2.15-phase-62`, head `4231836…`, every step `success` |
| Pull request #9 | `MERGED` into `main` at 2026-11-14T15:45:18Z, merge commit `d0adb5b…`, head `1659a99…` |
| Release baseline | `d0adb5b:plugins` = `90e0697363ee5c09bb7942a963cf670e16717c4a`, the 2.14.1 plugin tree |

### Plan must-haves

The 11 plans carry about 80 detailed truths. The load-bearing ones were checked directly (above and in the spot-checks). The rest are each locked by a test in `.github/scripts` or `docs/design/lean-v2.15/tools`; I ran that whole set once (445 passed, 250 subtests passed, 0 failed, 0 skipped) and broke eleven things by hand in a throwaway clone to confirm the locks trip.

| Plan | Requirement | Status | Basis |
|------|-------------|--------|-------|
| 62-01 stdlib check and guards | CI-01 | VERIFIED | Real tree: exit 0, `33 shipped .py files`. Planted `import requests` in `gitfixture.py`: exit 1, names file and module. Wrong path: exit 2, `PLUGIN ROOT NOT FOUND … STOPPING`. List minus one id: exit 1. Log with 4 deselected: exit 1. Log with a failure: exit 1. Result file with an unlisted skip: exit 1, names the unexpected and the missing entry. |
| 62-02 the workflow and its shape locks | CI-01 | VERIFIED | Workflow read in full. Adding a secrets reference, a second workflow file, or a macOS runner each fails a named test in `test_workflow_shape.py`. No `conftest.py` or pytest config file is tracked. |
| 62-03 step rule and criterion | BASE-04 | VERIFIED | `step_count.py`, `steps-v2.14.1.json` (rev `dd8e4ab`, labelled `operation count — not tokens, not price`), `CRITERION.md`. Independent recount agrees (42 / 18). |
| 62-04 Finalize capture harness | BASE-03, BASE-04 | VERIFIED | `finalize_capture.py` present and substantive (45 KB); its tests pass locally and on the Linux runner; situation ids match `CRITERION.md`. |
| 62-05 bytes and traces | BASE-02 | VERIFIED | Independent byte recount; labels and gap text read from the record. |
| 62-06 usage reader and cost note | BASE-01 | VERIFIED | Numbers reproduced from the logs; note clean of prices and private paths per `check-note`. |
| 62-07 suite and replay baseline, manifest | BASE-03 | VERIFIED | Manifest hashes recomputed; `verify` trips on an edited record, a removed record and an edited replay report, each named by file. |
| 62-08 CI proof before merge | CI-02, CI-01 | VERIFIED | Green branch run and red run confirmed on GitHub; `RECORDED_SKIPS` in `left_out_guard.py` holds the two entries the `main` run printed. |
| 62-09 pull request and close | CI-02, BASE-01 | VERIFIED | PR #9 merged; `main` first run green; owner decision recorded in the note; protection unchanged; no secret. |
| 62-10 five-situation record | BASE-03, BASE-04 | VERIFIED | Record and fingerprint present and in the manifest; re-derived by `test_finalize_capture.py` on macOS (here) and on Linux (run 43611870373, where only two tests skipped and neither is in that file). |
| 62-11 baseline page and README | BASE-03, BASE-02, BASE-04 | VERIFIED | `BASELINE-v2.14.1.md` and `README.md` present; changing one figure on the page (Finalize bytes 136,114 to 136,113) fails `test_baseline_page.py` by name. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.github/workflows/offline-suite.yml` | The one CI workflow | VERIFIED | 63 lines, active on GitHub, has run on `main` |
| `.github/ci-left-out-tests.txt` | The five left-out test ids | VERIFIED | Five ids, equal to `RECORDED_FIVE`; read by the workflow |
| `.github/scripts/stdlib_only.py`, `left_out_guard.py` | Stdlib check and guards | VERIFIED | Called by the workflow as named steps; standard-library imports only |
| `.github/scripts/test_*.py` (3 files) | Mutant tests for the above | VERIFIED | Run in CI and locally |
| `docs/design/lean-v2.15/CRITERION.md` | Criterion and workload | VERIFIED | Figures tie to the records |
| `docs/design/lean-v2.15/BASELINE-v2.14.1.md` | Plain-terms baseline page | VERIFIED | Figures locked to the records by test |
| `docs/design/lean-v2.15/baseline/` (10 records + manifest) | Pinned 2.14.1 records | VERIFIED | Hashes match the manifest |
| `docs/design/lean-v2.15/tools/` (5 tools, 6 test files) | Capture and verify tools | VERIFIED | Wired through `baseline_records.py verify` and the CI suite path |
| `62-COST-NOTE.md`, `62-CI-RECORD.md` | Phase records | VERIFIED | Every run id, commit and conclusion in the CI record that I checked matches GitHub |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| Workflow | `stdlib_only.py` | step `Stdlib-only check` | WIRED |
| Workflow | `left_out_guard.py` | `check-list` before the suite, `args` to build the deselects, `check-log` and `check-skips` after | WIRED |
| Workflow suite step | pipe status | `test "${PIPESTATUS[0]}" -eq 0` (a failing suite is not hidden by `tee`; the red run proves it) | WIRED |
| `RECORDED_SKIPS` | runner's result file | `check-skips` on `suite.xml` | WIRED |
| `baseline_records.py verify` | `MANIFEST.json` and every record | file-set and hash comparison | WIRED |
| `CRITERION.md` / baseline page | records | figures locked by `test_step_count.py` and `test_baseline_page.py` | WIRED |
| Cost note numbers | `usage_fields.py` output | reproduced by re-running the reader | WIRED |

### Data-Flow Trace (Level 4)

Not applicable: the phase ships no component that renders dynamic data. The records' data sources were traced instead (bytes to git blobs, usage numbers to session logs, CI results to GitHub runs).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Baseline holds | `python3 docs/design/lean-v2.15/tools/baseline_records.py verify --repo .` | `baseline holds`, exit 0 | PASS |
| Stdlib-only check | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` | `33 shipped .py files; third-party imports: none`, exit 0 | PASS |
| Left-out list guard | `left_out_guard.py check-list .github/ci-left-out-tests.txt` | `left-out list matches the recorded five`, exit 0 | PASS |
| Guard and tool tests | `pytest -q -p no:cacheprovider .github/scripts docs/design/lean-v2.15/tools` | `445 passed, 250 subtests passed in 75.97s` | PASS |
| Eleven hand-made breaks in a throwaway clone | see plan table | all eleven tripped with a named message | PASS |
| Full plugin suite | not re-run (passed minutes earlier at this commit per the orchestrator; green on `main` in run 43611870373) | 4324 passed on the runner | not re-run |

### Probe Execution

No probe scripts are declared by this phase. Step 7c: not applicable.

### Requirements Coverage

| Requirement | Source plans | Status | Evidence supports ticking? |
|-------------|-------------|--------|----------------------------|
| BASE-01 | 62-06, 62-09 | SATISFIED | Yes. Note exists, is verdict-first, covers every named field per run and per lane, and its numbers reproduce from the logs. |
| BASE-02 | 62-05, 62-11 | SATISFIED (owner decision on deep review) | Yes, with the recorded limit: deep review is declared, not observed (D-09, D-19). |
| BASE-03 | 62-04, 62-07, 62-10, 62-11 | SATISFIED | Yes. Suite, replay and five-situation records pinned, hashed and re-checkable with one command; plugin tree unchanged. |
| BASE-04 | 62-03, 62-04, 62-10, 62-11 | SATISFIED | Yes. Criterion and workload written before any plugin change; labelled counts named as the evidence. |
| CI-01 | 62-01, 62-02, 62-08 | SATISFIED | Yes. One workflow, both triggers, read-only token, no secret, protection unchanged. |
| CI-02 | 62-08, 62-09 | SATISFIED | Yes. `main` green at `d0adb5b` (run 43611870373); `ci-red-proof` red in the suite step (run 43568391505). |

No orphaned requirement: REQUIREMENTS.md maps exactly these six ids to Phase 62 and every one is claimed by a plan. The six still show `Pending` in REQUIREMENTS.md; that is the orchestrator's tick to make after this verdict.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `docs/design/lean-v2.15/tools/finalize_capture.py` | 93, 318 | `XXXXXX` | Info | Not a debt marker: it is the placeholder that replaces a `mktemp` suffix (`vc.XXXXXX`). No `TBD`, `FIXME`, `TODO`, `HACK` or `PLACEHOLDER` in any file the phase added. |
| `docs/design/lean-v2.15/BASELINE-v2.14.1.md` | Finalize situations, `Limit` | Out-of-date sentence | Info | Says the capture's Linux result "has not been checked yet". It has since passed on the Linux runner in every CI run. The page understates the evidence; nothing is overstated. |
| `docs/design/lean-v2.15/BASELINE-v2.14.1.md`; `62-COST-NOTE.md` line 3 | Cost visibility | Out-of-date sentence | Info | Both still say the owner's decision is pending. The decision (NO-GO) is recorded under `## Owner decision` in the note, which the page points to. |

Known and already accepted by the owner, noted and not raised as gaps: review warnings WR-01 to WR-06 and SA-01/SA-02 (backlog 999.34, present in ROADMAP.md); cost visibility NO-GO; deep-review footprint declared, not observed.

One search was not run: a recursive scan of the new files for private paths was stopped by the repository's holdout guard hook, and I did not route around it. The same property is covered by the phase's own privacy locks, which passed (`check-note` on the cost note, and the planted-path tests in `test_path_records.py` and `test_finalize_capture.py`).

### Human Verification Required

None. Every must-have was checkable from the repository, the committed records or GitHub. No plan carries a deferred `<human-check>` block.

### Gaps Summary

No gaps. The phase goal is achieved: the cost note exists and is honest to the logs, the 2.14.1 baseline is pinned and re-checkable with one command, the criterion is written down, the plugin code is byte-identical to 2.14.1, and the one workflow is green on `main` and demonstrably goes red on a broken test.

---

_Verified: 2026-11-14T16:03:53Z_
_Verifier: Claude (bm-verifier)_
