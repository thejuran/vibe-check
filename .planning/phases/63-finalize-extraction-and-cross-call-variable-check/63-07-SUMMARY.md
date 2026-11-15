---
phase: 63-finalize-extraction-and-cross-call-variable-check
plan: 07
subsystem: finalize
tags: [finalize, extraction, design-record, removal-ledger, d-02, d-12, d-18]
requires:
  - "63-06: the Finalize-inputs fence, _stand_in_root, the 63-06 ledger rows"
provides:
  - "docs/design/lean-v2.15/finalize-counts-explained.md: the 2.14.1 'What the helper counts' passage, byte for byte between two markers"
  - "90-finalize.md: no counts explanation, no decisions-report fence; one binding sentence for $COUNTS_JSON / $DECISIONS_JSON"
  - "test_finalize_card.py: COUNTS_PASSAGE_SHA256 lock, TestReportFromTheResult, report-line D-18 walk, report/counts parity in the walks"
  - "63-REMOVAL-LEDGER.md: every row filled; named difference (5)"
affects: [63-08, 63-09, 63-11]
tech-stack:
  added: []
  patterns: ["sha256 of moved text pinned as a literal (no git at test time)", "2.14.1 fence body kept as a test constant and run fresh for parity"]
key-files:
  created:
    - docs/design/lean-v2.15/finalize-counts-explained.md
  modified:
    - plugins/vibe-check/phases/shared/90-finalize.md
    - plugins/vibe-check/scripts/test_finalize_card.py
    - plugins/vibe-check/scripts/test_confirmed_fix.py
    - .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-REMOVAL-LEDGER.md
decisions:
  - "Phase-57 needles split by owner file: 9 read from the moved passage (between the markers, not the whole document), 3 from 90-finalize.md"
  - "The fill rules (from `Fill from state:` to the end) are pinned by a sha256 of the dd8e4ab text, so the D-02 'byte-identical' rule is a test, not only a verify command"
  - "The 2.14.1 report fence is kept as the test constant P7_FENCE_2141 (checked equal to the dd8e4ab fence body) so the walks compare against it without git"
  - "The line-35 sentence '`$COUNTS_JSON` below means that object' from 63-06 is left in place; the new Writing-section sentence binds both names again where the fill rules use them"
metrics:
  duration: "about 75 min"
  completed: 2026-11-14
requirements: [FINX-01, FINX-04]
---

# Phase 63 Plan 07: Finish the Finalize extraction Summary

The "What the helper counts" explanation moved word for word into a design document that the model does not load, and a sha256 lock pins it to the 2.14.1 bytes. The REVIEW.md fill now takes its counts and decisions from the Finalize-inputs result instead of running its own `decisions-report` fence. The fill rules are byte-identical to 2.14.1. The report step's one-line refusal still shows above the report sentence (D-18). With this plan the extraction is complete: 83 steps (92 at 2.14.1) and 129,451 bytes on the Finalize path (136,114 at 2.14.1).

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Lock the counts passage word for word; re-point the P3 needles | 2414bad | test_finalize_card.py, test_confirmed_fix.py |
| 1 (GREEN) | Move the passage to the design document | 8d395f5 | finalize-counts-explained.md, 90-finalize.md (6 deletions, 0 insertions) |
| 1 (ledger) | P3 rows filled | 0e225e5 | 63-REMOVAL-LEDGER.md |
| 2 (RED) | Report data from the result; fill-rules pin; D-18 report-line walk | 59feb98 | test_finalize_card.py |
| 2 (GREEN) | Replace the decisions-report fence with one binding sentence | c337e63 | 90-finalize.md (1 insertion, 10 deletions) |
| 2 (ledger) | P7 rows filled; named difference (5); state counts | fbad28c | 63-REMOVAL-LEDGER.md |

## What each lock checks, and the mutant that trips it

- `TestFinalizeCard::test_counts_passage_moved_word_for_word`: the text between the markers has sha256 `7665e580…c730d707`, the digest of `git show dd8e4ab:…/90-finalize.md | sed -n '34,39p'`. Mutants: one character changed ("no expiry" → "No expiry"), the trailing newline dropped, the end marker removed.
- `test_counts_passage_not_in_the_loaded_file`: 90-finalize.md contains neither `What the helper counts` nor the document's name. Mutants: the passage head appended, and a Read of the document appended.
- `test_counts_doc_not_on_any_mode_path`: no `footprint.MODE_PATHS` entry names the document.
- `test_phase57_decision_contract`: 9 needles are looked up in the moved passage and 3 in 90-finalize.md. There is one mutant per needle, each run on the file that owns that needle.
- `test_confirmed_fix.py::TestProse::test_finalize_renders_confirmed_fix`: "never closes here" is read from the document. Its mutant removes it from the document.
- `TestFinalizeCard::test_helper_calls_present`: no fence runs `decisions-report`, and rows, parse and record-decisions each appear once. Mutants: the 2.14.1 fence put back, record-decisions removed.
- `TestReportFromTheResult::test_report_binding_holds`: the binding sentence sits before `Fill from state:`, the report sentence appears exactly once, and it is in the `5)` arm. Mutants: each part of the binding sentence removed, the 2.14.1 fence put back, the `5)` arm removed, the report sentence left twice.
- `TestReportFromTheResult::test_fill_rules_unchanged`: the sha256 of the fill rules equals the dd8e4ab digest. Mutants: one rule reworded, the `Fill from state:` line removed.
- `TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report`: the result's `report` equals what the 2.14.1 report fence prints when run fresh, and its `counts` (including `verified_obsolete_hashes`) equal the 2.14.1 counting command on the same fingerprint file.
- `test_card_route_records_then_writes`: after `record-decisions`, the re-run's report holds every decision just recorded and equals the 2.14.1 fence's output (T-63-21).
- `test_post_decision_recount_refingerprints_head` (control subtest): `verified_obsolete_hashes == [ARCH_HASH]` and equals the 2.14.1 counting command's list.
- `test_report_line_stays_on_screen` (D-18): the real fence runs over a stand-in that writes `carry_state.REASON_STATE_JSON` and exits 5. It exits 5 with stderr of exactly that line followed by the report sentence. That stderr equals the stderr of the saved 2.14.1 report fence run fresh on a state that is not JSON. Mutants: `2>"$BLOBFILE.err"` and `2>/dev/null` appended to the helper call line each make the walk lose the line.

## Figures (as the tools printed them, at c337e63)

| Measure | 2.14.1 (dd8e4ab) | before 63-07 (39736a8) | after 63-07 |
|---------|------------------|------------------------|-------------|
| `step_count.py` `totals.model_run_steps` (finalize) | 92 | 84 | **83** |
| `footprint.py` finalize-mode bytes | 136,114 | 133,387 | **129,451** |
| `90-finalize.md` bytes | — | 53,196 | 49,260 |

Commands: `python3 docs/design/lean-v2.15/tools/step_count.py --root plugins/vibe-check --json` and `python3 plugins/vibe-check/scripts/footprint.py --json`. The before and baseline figures came from the same tools with `--rev`. The step total matches the expected 83, and both figures are below 92 and 136,114.

## Verification (observed)

- Task 1 verify: the digest between the markers equals the dd8e4ab digest and is the literal in `test_finalize_card.py`. `90-finalize.md` has 0 `What the helper counts`. No `.md` file under `plugins/vibe-check/` and not `footprint.py` names the document (0). `test_finalize_card.py` + `test_confirmed_fix.py` gave 191 passed.
- After the P3 move, every module that reads `90-finalize.md` passed, along with `docs/design/lean-v2.15/tools` (which includes `test_baseline_page.py`) and `.github/scripts`: 2380 passed. The one failure was `docs/design/fix-harness/tools/test_harness_sandbox.py::test_checkout_root_is_the_repo`, which expects `.git` to be a directory; in a worktree it is a file. That suite is outside the plan's suite and has nothing to do with this change.
- Task 2 verify: 0 `decisions-report < "$STATE_FILE"`, exactly 1 report sentence, and the text from `Fill from state:` to the end is identical to dd8e4ab (diff empty). `DECISIONS_JSON` is present and the ledger has no `MISSING`. `test_finalize_card.py test_finalize_inputs.py test_cross_call_vars.py test_confirmed_fix.py` gave 360 passed, 562 subtests passed.
- **Full suite** (`pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools`, run on the final instruction text): **5 failed, 4498 passed, 1 skipped, 5604 subtests passed** in 309.87s. The only failures are the known `test_replay.py::TestPhase53SameLineRegressionCases` ids, which need local-only transcripts: `test_a2_pair_sits_on_adjacent_lines_of_one_statement`, plus `test_off_line_credit_mutation_trips` and `test_pre_same_line_scorer_gave_critical_100` with 2 subtests each. The stdlib gate is part of that run and passed.
- `finalize_capture.py verify --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json` printed `finalize baseline matches (5 situations)`.
- The six D-03 files are byte-identical to dd8e4ab: `git diff --stat dd8e4ab -- <the six>` was empty.
- No new hidden locks. After each instruction change, no test outside the ledger's P3 and P7 lists went red.

## Deviations from Plan

### Auto-fixed Issues

None. The plan ran as written. Small choices made along the way:

**1. [Rule 2 - Lock strength] The fill rules are pinned by a digest in a test**
- **Found during:** Task 2
- **Issue:** The plan's behavior list asks that the fill rules be byte-identical, with a mutant for each lock. The plan's verify command checks this with git, but no test held it.
- **Fix:** Added `FILL_RULES_SHA256`, the digest of the dd8e4ab text from `Fill from state:` to the end, with a mutant.
- **Cost if wrong:** A later phase that changes a fill rule on purpose must update one constant.
- **Files modified:** test_finalize_card.py
- **Commit:** 59feb98

**2. [Rule 2 - Lock strength] The clean walk compares all of `counts`, not only `verified_obsolete_hashes`**
- **Found during:** Task 2
- **Issue:** The plan named only `verified_obsolete_hashes`. Comparing the whole object against the 2.14.1 counting command is a stronger check and costs nothing.
- **Fix:** The clean-route walk and the refingerprint control compare the whole `counts` object as well as that list.
- **Cost if wrong:** None. The helper's `counts` already holds exactly the counting command's eight keys (63-02 parity).
- **Commit:** 59feb98

## Assumption Drift (advisory)

- **Found during:** Task 2 RED. **Planned:** the walk and D-18 assertions go red before the instruction edit. **Actual:** only the text locks went red: `test_helper_calls_present` and `test_report_binding_holds`. The walk parity checks and the report-line walk already passed, because the behaviour they check (the result's `report` and the fence's stderr) landed in 63-06. These tests check behaviour that already existed; they guard against regression rather than drive new behaviour. Their mutants show they can trip. **Cost if wrong:** none. The RED gate is carried by the two text locks.

## Known Stubs

None.

## Threat Flags

None. The threat register's mitigations are in place: T-63-21 (the card-route re-run's report holds the recorded decisions), T-63-22 (sha256 lock with a one-character mutant), and T-63-23 (the `5)` arm lock and mutant, plus the D-18 report-line walk and its redirect mutants).

## TDD Gate Compliance

- Task 1: RED `2414bad` (`test(63-07)`, 4 failing), then GREEN `8d395f5` (`feat(63-07)`).
- Task 2: RED `59feb98` (`test(63-07)`, 2 failing), then GREEN `c337e63` (`feat(63-07)`).

## Self-Check: PASSED

- FOUND: docs/design/lean-v2.15/finalize-counts-explained.md
- FOUND: .planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-07-SUMMARY.md
- FOUND commits: 2414bad, 8d395f5, 0e225e5, 59feb98, c337e63, fbad28c
