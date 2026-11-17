---
phase: 62-baseline-and-continuous-test-run
plan: 11
subsystem: design-evidence (lean-v2.15 kit)
tags: [BASE-03, BASE-02, BASE-04, baseline-page, figure-locks]
requires:
  - "62-03: steps-v2.14.1.json"
  - "62-05: footprint-v2.14.1.json, traces-v2.14.1.json"
  - "62-06: 62-COST-NOTE.md verdict"
  - "62-07: suite record, replay fingerprints, MANIFEST.json, baseline_records.py verify"
  - "62-10: finalize-situations-v2.14.1.json"
provides:
  - docs/design/lean-v2.15/BASELINE-v2.14.1.md (owner-facing plain-terms baseline page)
  - docs/design/lean-v2.15/README.md (kit tool table and layout)
  - docs/design/lean-v2.15/tools/test_baseline_page.py (page_problems, 25 clauses, page and record mutants, TestReadme)
affects: [62-09 closing checkpoint (owner reads this page), phase PR description]
tech-stack:
  added: []
  patterns: [problems-list lock with clause-id prefixes, page mutant plus record mutant per figure, completeness test with break test]
key-files:
  created:
    - docs/design/lean-v2.15/BASELINE-v2.14.1.md
    - docs/design/lean-v2.15/README.md
    - docs/design/lean-v2.15/tools/test_baseline_page.py
  modified: []
decisions:
  - "The page lock covers more than the plan's 12 clauses: 25 clauses so every figure on the page (tallies, file counts, proxy figures, trace session counts, out-of-list bytes, step parts, the 91-vs-92 judgement figure) is tied to a record"
  - "Record mutants run on an in-memory copy of the loaded records (no temp files), keeping the test to json/os/re/unittest"
metrics:
  duration: ~40 min
  completed: 2026-11-14
  tasks: 2
  files: 3
---

# Phase 62 Plan 11: Plain-terms 2.14.1 baseline page Summary

The owner now has one page, `BASELINE-v2.14.1.md`, with the whole 2.14.1 baseline, numbers first. A standing test checks every figure on it against the committed records: each clause has page mutants and record mutants, and each mutant must be reported by its clause name. The kit also has a README listing its five tools.

## Tasks

| # | Task | Commit |
|---|------|--------|
| 1 | `page_problems()` and the figure locks (RED) | d704148 |
| 2 | Baseline page, kit README, `TestReadme` (GREEN) | f58bcc5 |

## What the page shows (copied from the records)

- **Suite:** 3886 passed, 0 failed, 0 skipped. Run with pytest 9.0.3 on Python 3.12.12, Darwin 27.2.0. Plugin tree `90e0697…`.
- **Replay:** fingerprint `142de13d…` with the 12 private recordings present and `3eb053ca…` with none. `runs compared: 170, runs differing: 0`. The page quotes the removed-line rule word for word.
- **Finalize:** five situations recorded, with commands/values/writes tallies of 8/2/3, 17/9/6, 10/3/3, 10/4/4 and 17/9/6. Record fingerprint `04a453ff…`.
- **Bytes:** plain review 192,057 bytes over 13 files, deep review 268,997 over 19, Finalize 136,114 over 7. The proxy token figures sit only under a `### Proxy figures` sub-heading, which carries the record's PROXY label.
- **Traces:** plain review is observed (4 sessions) and Finalize is observed (1 session). Deep review is `declared, not observed`, and the page quotes the record's gap sentence. The page lists the files read outside the declared lists with their bytes and how many sessions read them.
- **Steps:** 42 + 5 + 7 + 38 = 92.
- **Cost visibility:** `The cost note's recommendation, not the decision: **NO-GO**`.

The page states these limits:
- Deep review traces are declared, not observed.
- The recorded sessions read files outside the declared lists.
- Finalize's only observed session ran the 2.14.0 candidate.
- Identical Finalize captures have only been checked on macOS; Linux is not checked yet.
- The replay fingerprint does not move when `score.py` changes.
- Counting the line-180 inline command is a judgement call: the total is 92, or 91 if that line is treated as a mention.
- The go/no-go decision is still the owner's and is still open. The page says the decision may overrule the note's recommendation, and that a no-go ends accounting work, leaving the byte and step counts as the milestone's evidence.

**Verdict check (done by hand, as the plan requires):** I read both files. The first verdict line of `62-COST-NOTE.md` (line 7) is `**NO-GO**`. The page's only bold verdict (line 205) is `**NO-GO**`, on the line that begins "The cost note's recommendation, not the decision:". The two match, and the page never calls the verdict decided, final or settled.

## Verification (observed)

- RED: `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_baseline_page.py` gave 27 failed, 8 passed. Every one of the 27 failures was `AssertionError: baseline page missing: docs/design/lean-v2.15/BASELINE-v2.14.1.md …`, so none was a skip and none failed for another reason.
- Task 1 verify checks, run as separate commands: `def page_problems(` is present; the skip-pattern count is 0; the `test(62-11)` commit is in the log; `git status --porcelain -- plugins docs/design/lean-v2.15/baseline` printed nothing.
- GREEN, page file: **37 passed, 168 subtests passed**, 0 failed, 0 skipped.
- Whole kit, `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools`: **327 passed, 178 subtests passed** (70 s).
- `python3 docs/design/lean-v2.15/tools/baseline_records.py verify --repo .` printed `baseline holds`, exit 0.
- The page has all 9 headings (grep count 9) and the README names all 5 tools (grep count 5). `grep -c "\.planning" test_baseline_page.py` gives 0, and `grep -c '\$[0-9]' BASELINE-v2.14.1.md` gives 0.
- Nothing under `plugins/` or `docs/design/lean-v2.15/baseline/` changed.
- **Decorative-guard check:** I replaced each of the 25 clauses in turn with `lambda p, r: []` and ran its test method. All 25 tests failed. No clause is decorative.
- Every page mutant asserts that the page text changed, and every record mutant asserts that the record copy changed. Each mutant must produce a problem line starting with its own clause id. The completeness break test drops each clause's mutants in turn and confirms that `uncovered_clauses` names exactly that clause. The README mutant removes each tool's row and must get exactly that tool reported.

## Deviations from Plan

**1. [Rule 2 - Missing check] More clauses than the plan listed (12 → 25)**
- **Found during:** Task 1
- **Issue:** The plan's clause list left some figures on the page unlocked: the situation tallies, file counts, proxy figures, replay diff and rule, trace session counts and versions, out-of-list bytes, step parts, and the headline figures. The must-have requires every figure to equal its record.
- **Fix:** Added these clauses: `headline`, `commit`, `suite-env`, `replay-diff`, `situation-tallies`, `file-counts`, `proxy-figures`, `step-parts`, `step-judgement`, `trace-extras`, `limits`, `verdict-not-settled` and `recheck-command`. Each has its own page mutants, and most have record mutants as well.
- **Cost if wrong:** The page is stricter to edit. Any rewording of a locked row or phrase needs a matching lock change.
- **Commit:** d704148

**2. [Rule 2 - Stronger check] "All occurrences" rule for labelled figures**
- **Found during:** Task 1
- **Issue:** Under a "figure appears somewhere" rule, a changed `3886 passed` would still pass, because the verbatim summary line also contains `3886 passed`.
- **Fix:** In the headline and the Suite section, every `<number> passed/failed/skipped/runs/differing` must equal the record. Figures in tables are checked by row and column, not by searching the whole section.
- **Commit:** d704148

**3. Record mutants run in memory**
- `page_problems(page_text, baseline_dir)` keeps the plan's signature. It loads the records and calls `problems_for(page, records)`. The record mutants change a deep copy of the loaded records, so the test stays within `json/os/re/unittest` and writes nothing.

No lock had to be loosened to fit the page.

## Known Stubs

None. `62-CI-RECORD.md`, which the Suite section refers to, comes from plan 62-08 and is not in this worktree. The page names it as the place the CI lists live, following the plan's wording.

## Threat Flags

None. The page is built only from the committed records and the cost note's verdict paragraph, and no session file was opened. T-62-58 is handled by 25 clauses with mutants and the completeness test, T-62-59 by `proxies-apart` and `no-price`, and T-62-61 by the `trace-labels` relabel mutant.

## Self-Check: PASSED

- FOUND: docs/design/lean-v2.15/BASELINE-v2.14.1.md
- FOUND: docs/design/lean-v2.15/README.md
- FOUND: docs/design/lean-v2.15/tools/test_baseline_page.py
- FOUND commits: d704148, f58bcc5
