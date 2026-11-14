---
phase: 62-baseline-and-continuous-test-run
plan: 03
subsystem: design-evidence (lean-v2.15 tool kit)
tags: [baseline, criterion, step-count, D-05, BASE-04]
requires: [plugins/vibe-check/scripts/footprint.py MODE_PATHS]
provides:
  - docs/design/lean-v2.15/tools/step_count.py (count_text, count_files, count_path, verify_steps, CLI)
  - docs/design/lean-v2.15/baseline/steps-v2.14.1.json (92 model-run steps at dd8e4ab)
  - docs/design/lean-v2.15/CRITERION.md (pass rule, baseline, counting rule, workload)
affects: [62-04 capture driver fence agreement, 62-07 verify_baseline, Phase 63 FINX-05 comparison]
tech-stack:
  added: []
  patterns: [freeze-v2.12 tool-kit style, problems-list verifier, lock plus mutant with mutation-happened guard]
key-files:
  created:
    - docs/design/lean-v2.15/tools/step_count.py
    - docs/design/lean-v2.15/tools/test_step_count.py
    - docs/design/lean-v2.15/baseline/steps-v2.14.1.json
    - docs/design/lean-v2.15/CRITERION.md
  modified: []
decisions:
  - "WRITE_PHRASES = (\"with the Write tool\", \"Use Write to create\"): all 7 Write-tool lines on the Finalize path at 2.14.1 instruct a write"
  - "INLINE_RUN_LEADS = (\"run \", \"Run \", \"→ \", \"file-to-file with \"): all 5 candidate inline spans instruct a run"
  - "2.14.1 Finalize baseline: 136,114 bytes over 7 files; 92 model-run steps (42 bash blocks + 5 inline commands + 7 writes + 38 copied values)"
metrics:
  duration: ~35 min
  completed: 2026-11-14
  tasks: 2
  files: 4
---

# Phase 62 Plan 03: Improvement criterion and step-count rule Summary

The D-05 counting rule is now a stdlib script, `step_count.py`. At the 2.14.1 commit `dd8e4ab` it counts 92 model-run mechanical steps on the Finalize path: 42 bash blocks, 5 inline commands, 7 Write-tool writes and 38 copied values. That figure is committed in `steps-v2.14.1.json` and re-derived on every test run from the record's own file list. `CRITERION.md` sets out the pass rule (at least one of bytes 136,114 or steps 92 drops, and neither grows), the comparison workload and the waiver path.

## Tasks

| # | Task | Commits |
|---|------|---------|
| 1 | Counting-rule script, pinned fence figures, +1 mutants | 744152d (test, RED), ac8a4f9 (feat, GREEN) |
| 2 | Settle phrase and lead-in lists, record 2.14.1 counts, CRITERION.md | 249ba10 |

## Verification (observed)

- RED: `pytest` on the new test file failed at collection with `ModuleNotFoundError: No module named 'step_count'` before the module existed.
- GREEN (Task 1): `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_step_count.py` gave 38 passed. The CLI check printed `OK {'bash_fences': 42, ..., 'model_run_steps': 82}` with per-file fences `[1,0,1,10,7,5,18]`. Task 2 later extended the phrase and lead-in lists, which raised the total to 92. `git status --porcelain -- plugins` was empty, and `grep -c "90-finalize.md" step_count.py` gave 0.
- Task 2: the same pytest command gave 57 passed. The JSON check printed `ok 92 7`. All 5 situation ids and all 4 grepped headings are present, `grep -c '\$[0-9]' CRITERION.md` gave 0, and `git status --porcelain -- plugins` was empty.
- Per-file fence figures matched the planner's 1, 0, 1, 10, 7, 5, 18 (42 total). Both independent recounts agree: a plain `^\s*`{3,4}bash$` line loop over `git show`, and the house expression copied from `test_finalize_card.bash_fences`.
- `footprint.py --rev dd8e4ab --json` gave finalize at 136114 bytes over 7 files with nothing missing, which matches the expected figure.
- Mutants run and confirmed to trip:
  - the seven +1 mutants (column-0 fence, indented fence, four-backtick fence, paste site, inline command, Write phrase, printed literal), each asserting exact deltas
  - the wrong-rule mutant (`FENCE_OPEN` set to `^```bash$`): total 18, equal to the test's own line count, BLOBFILE lost, pinned-figures test fails
  - the same-fence-exclusion mutant
  - the lead-list and phrase-list rollback mutants
  - the record tampers: total +1 is named, a 00-scope.md fence +1 is named with its file, and a removed row is caught by the path-list check
  - the doc mutants: total +1, a situation renamed, a heading renamed
- Decoupling test: with `MODE_PATHS["finalize"]` patched to 6 entries, `verify_steps` still returns `[]` on the committed record, and `count_path` really sees 6 files.

## Deviations from Plan

**1. [Rule 1 - Bug] The pinned-figures test counts inside the test, not in `setUpClass`**
- **Found during:** Task 1 (before RED commit)
- **Issue:** the wrong-rule mutant runs `test_pinned_fence_figures` on its own through `TestCase.run`, which skips class fixtures. A record built in `setUpClass` would make that test fail even without the patch, so the mutant would be decorative.
- **Fix:** the test computes its own record. `TestClassification` reads its texts lazily for the same reason. Each `_passes` mutant first asserts the unpatched test passes.
- **Cost if wrong:** none for behaviour; this only affects how the test is wired.
- **Files modified:** docs/design/lean-v2.15/tools/test_step_count.py
- **Commit:** 744152d

**2. [Rule 2 - Missing check] Two extra rollback mutants, a heading mutant and a `verify_steps` rule-field check**
- **Found during:** Task 2
- **Fix:** added three mutants: lead list back to `("run ",)`, phrase list back to one phrase, and a renamed heading. `verify_steps` also reports a changed `rule_version`, `write_phrases`, `inline_run_leads` or `kind`. These were added so a silent rule change cannot pass.
- **Cost if wrong:** a slightly stricter verifier, so any rule change must re-record the baseline. The plan's doc already requires that.
- **Commit:** 249ba10

## Assumption Drift (advisory)

- **Inline lead-ins.**
  - **Found during:** Task 2
  - **Planned:** the plan's Task 1 started from the single lead-in `run `.
  - **Actual:** all five candidate spans (lines 180, 184, 243, 271, 272, which match the planner's scan) instruct a run. Their lead-ins are `→ `, `file-to-file with `, `run ` (twice) and `Run `, so the smallest exact list has four entries. No upper-bound fallback was needed.
  - **Cost if wrong:** if line 180 (`→ `) were judged a mention, the baseline would be 91, not 92.

## Known Stubs

None. CRITERION.md names `baseline/traces-v2.14.1.json`, `baseline/finalize-situations-v2.14.1.json` and `62-COST-NOTE.md`. Sibling plans in this wave produce those files, so they are absent in this worktree by design.

## Threat Flags

None. The script reads git objects only, through an argument list with a timeout (T-62-13 mitigated). The committed numbers are re-derived by `verify_steps` and tamper mutants (T-62-14). Rule version, phrases and lead-ins are recorded in the JSON and the doc (T-62-15). The fence rule is pinned per file with two recounts and a wrong-rule mutant (T-62-54).

## Self-Check: PASSED

- FOUND: docs/design/lean-v2.15/tools/step_count.py
- FOUND: docs/design/lean-v2.15/tools/test_step_count.py
- FOUND: docs/design/lean-v2.15/baseline/steps-v2.14.1.json
- FOUND: docs/design/lean-v2.15/CRITERION.md
- FOUND commits: 744152d, ac8a4f9, 249ba10
