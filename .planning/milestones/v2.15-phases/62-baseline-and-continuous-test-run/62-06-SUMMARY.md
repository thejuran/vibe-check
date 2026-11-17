---
phase: 62-baseline-and-continuous-test-run
plan: 06
subsystem: design-evidence
tags: [python-stdlib, jsonl, usage, cost-visibility, never-echo]

requires: []
provides:
  - "docs/design/lean-v2.15/tools/usage_fields.py: read-only usage-field reader (dedupe per message id, lanes from meta files, check-note mode)"
  - "62-COST-NOTE.md: BASE-01 go/no-go recommendation (NO-GO, D-11 rule case)"
affects: [62-09 closing checkpoint (owner records go/no-go), 999.12 backlog entry, CRITERION.md evidence choice]

tech-stack:
  added: []
  patterns:
    - "Reader self-checks its output with price_problems and stops instead of printing"
    - "Withheld-key counter named without price words so the JSON passes its own lock"

key-files:
  created:
    - docs/design/lean-v2.15/tools/usage_fields.py
    - docs/design/lean-v2.15/tools/test_usage_fields.py
    - .planning/phases/62-baseline-and-continuous-test-run/62-COST-NOTE.md
  modified: []

key-decisions:
  - "Recommendation NO-GO: 0 measured / 15 estimated / 0 missing deciding cells; caused by the D-11 rule and no independent run total, not by bad data"
  - "Archive census run against the owner's primary checkout because the b3 transcripts are gitignored and absent from the worktree"

patterns-established:
  - "Usage reader: names, counts and sums only; lanes never guessed; sentinel never-echo in four positions"

requirements-completed: [BASE-01]

duration: 25min
completed: 2026-11-14
---

# Phase 62 Plan 06: Cost visibility feasibility Summary

**Stdlib usage-field reader (once-per-message dedupe, lanes from subagent meta files, self-enforced no-price output) plus a NO-GO cost note: all fifteen deciding cells are `estimated` because the records have no independent run total**

## Performance

- **Duration:** about 25 min
- **Started:** 2026-11-14T05:17:08Z
- **Completed:** 2026-11-14
- **Tasks:** 2
- **Files created:** 3

## Accomplishments
- `usage_fields.py`: reads session JSONL plus `subagents/*.meta.json`. It sums usage once per message id, reports field presence, usage key names, retry key names, wall clock (labelled as including owner wait), malformed lines and `run_total_source`. It has a `check-note` mode.
- 34 tests, all synthetic and built in temp dirs. They cover dedupe, lanes, unattributed and unsafe lanes, census, never-echo (sentinel in four places, CLI under `python3 -I`, text and `--json`), the no-price lock with four planted mutants, refuse-to-print, check-note and the import set. `TestMutants` runs dedupe-off, price-check-off and `_safe`-off, and each mutant makes its target tests fail.
- One pass over the five fixed smoke sessions and the two archive roots produced `62-COST-NOTE.md`, with the verdict first and the seven required sections.

## Task Commits

1. **Task 1 RED:** `62eeb07` test(62-06): add failing tests for the usage-field reader. Observed: collection error, `ModuleNotFoundError: usage_fields`.
2. **Task 1 GREEN:** `9cacbef` feat(62-06): read-only usage-field reader. Observed: `34 passed`.
3. **Task 2:** `2e42ab1` docs(62-06): cost visibility go/no-go note (BASE-01, 999.12)

## Verification observed
- `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_usage_fields.py` → 34 passed, 0 failed.
- Sibling and plugin import grep → 0. `git status --porcelain -- plugins` → empty. No `.jsonl` in git status.
- Task 2 verify script (the plan's command, run from a file) → `note clean` and `OK`, exit 0. Headings appear in the required order.
- Break test: a scratchpad copy of the note with `Usage cost: $5` appended. grep found 1 match, and `check-note` exited 1 naming the line. The copy was deleted.
- Reader runs: sessions `--json` exit 0, text exit 0, archives exit 0. All five sample files were found.

## Results (from the reader)
- Plain review (4 sessions) and Finalize (1): model and all four token fields were present on every unique message (for example 75 of 75 and 19 of 19). Every subagent file had a lane, so 0 were unattributed. Results: 264 duplicate records dropped, 0 conflicting duplicates, 0 malformed lines, 0 cross-file duplicate ids.
- `run_total_source`: `none found` for all five. Retry key names: none.
- Archives: b3-ground-truth has 102 files, all 102 with usage, 0 with subagents. freeze-v2.12 has 3 files, 0 with usage, 0 with subagents.
- Deep review: no recorded 2.14.x session, so every field is `missing`.
- The owner-decision step is left to plan 62-09, as specified. ROADMAP and STATE were not touched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Renamed `price_like_keys_withheld` to `charge_like_keys_withheld`**
- **Found during:** Task 1 GREEN
- **Issue:** The plan's field name `price_like_keys_withheld` contains "price". As a JSON key it trips the plan's own no-price lock, so the reader refused to print its `--json` output (7 tests failed).
- **Fix:** Renamed the key in the reader and the test. The meaning is unchanged: a count of usage key names holding cost, price or usd, withheld from output.
- **Cost if wrong:** Low. A later consumer expecting the plan's key name would need a one-word rename.
- **Files modified:** usage_fields.py, test_usage_fields.py
- **Committed in:** 9cacbef

**2. [Rule 3 - Blocking] Archive census pointed at the primary checkout**
- **Found during:** Task 2
- **Issue:** `docs/design/b3-ground-truth/**/transcript.jsonl` is gitignored, so the worktree had 0 such files. The archive exists only in the owner's primary checkout, which has 102.
- **Fix:** Ran the census read-only against the primary checkout's `docs/design/b3-ground-truth` and `docs/design/freeze-v2.12`. The note says so.
- **Cost if wrong:** Low. These are counts only and do not feed the verdict.

**3. [Additive] Extra output fields:** `other_keys_withheld`, `run.cross_file_duplicate_ids`, `files`, `meta`-unreadable handling. A `TestMutants.test_mutant_echo` mutant turns off the safe-pattern check.
- **Cost if wrong:** None. These fields are informational.

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking) and 1 additive.

## Assumption Drift (advisory)
- **Found during:** Task 2. **Planned:** one subagent file per lane. **Actual:** in two of the four plain reviews, each lane has two subagent files (the lane ran twice). The reader pools them under the lane, so the lane's elapsed time spans both runs and the gap between them. The note says this. **Cost if wrong:** Per-lane elapsed figures could be misread as one run's duration. They are already labelled `estimated`.

## Known Stubs
None.

## Threat Flags
None. The reader is read-only, local, and prints names and numbers only.

## Self-Check: PASSED
- FOUND: docs/design/lean-v2.15/tools/usage_fields.py
- FOUND: docs/design/lean-v2.15/tools/test_usage_fields.py
- FOUND: .planning/phases/62-baseline-and-continuous-test-run/62-COST-NOTE.md
- FOUND commits: 62eeb07, 9cacbef, 2e42ab1
