---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 01
subsystem: efficacy-evidence
tags: [b3, guardrail, manifest, supersessions, axis, h-lane]
requires: []
provides:
  - "docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json — guardrail ground truth (29 catch runs, 188 AXIS-labelled survivors at SITE)"
  - "SUPERSESSIONS-v2.10.md entry 007 — member titles on a collapsed row satisfy AXIS (D-14)"
affects: [41-02 replay harness, 41-03+ scorer candidates, Phase 43 scoring]
tech-stack:
  added: []
  patterns: ["_purpose/_scope header keys on a committed JSON fixture", "append-only ledger entry with raw-bytes sealed quotes"]
key-files:
  created:
    - docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json
  modified:
    - docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md
decisions:
  - "AXIS labels calibrated against the sealed v2.9 autoescape run-1 MISS: a title that only says a prior autoescape fix was reverted/undone is NOT axis; it must name escaping-off or XSS"
  - "Titleless archived findings (2, runs-v2.10/third-organic run-1) are labelled axis=false: a title-based gate cannot pass on them"
  - "Revert/convention/divergence/test-breakage framings are axis=false on every diff; naming the leaked content (credential, key, URL, response payload) is axis=true on secret-in-logs"
  - "Findings quoted in a sealed winning column or a Phase-40 PASS.json CWE-532 citation are kept axis=true, never relabelled"
metrics:
  duration: "~25 min"
  completed: 2026-09-29
  tasks: 2
  files: 2
---

# Phase 41 Plan 01: Catch manifest + ledger entry 007 Summary

The zero-catch-regression guardrail now has committed, machine-checkable ground truth: 29 archived
catch runs with every one of the 188 findings at SITE labelled for the sealed AXIS clause, plus
ledger entry 007 recording that any member title on a surviving collapsed row satisfies AXIS. Both
were committed before any harness or scorer candidate exists.

## What was built

**Task 1: `REPLAY-CATCH-MANIFEST-v2.10.json`** (commit `4632208`)
- `catch_runs`: 29 entries. 26 are guardrail rows: v2.9 has 8 (secret-in-logs 1-3, autoescape 2-3,
  third-organic 1-3; autoescape run-1 was the v2.9 MISS and is not a key). Phase-38 has 15 and
  Phase-40 final has 3. The other 3 are the Phase-40 batch spot-check runs (guardrail=false). The
  21 runs under `runs-v2.10*` are calibration=true.
- Each entry carries `diff`, `archive`, `key_blob` (`ef0ab67` carried / `5f687d9` new), `floor`,
  `site` (session-rotation at 1564-1588 per entry 002; settings-form-split four ranges;
  secret-in-logs two ranges) and `survivors_at_site`. `survivors_at_site` holds every finding at
  SITE from `state.passes[-1].findings[]`, with agent/line/title/stable_hash/band copied byte-exact
  (`ensure_ascii=False`), plus `axis` and a `why` naming the deciding phrase.
- Totals: 188 survivors, 113 axis=true, 75 axis=false.
- `quiet_runs`: 18 headline, 6 phase40, 9 v29_informational. `excluded_runs.should-quiet-7`: 3,
  per entry 001 (D-06). No `.failed-*` directory is listed anywhere.

**Task 2: SUPERSESSIONS-v2.10.md entry 007** (commit `7dce172`)
- The entry is appended at EOF in the ledger's four-block form. Its fenced raw-bytes quotes are
  SCORING-v2.10.md 279-282 (the three-gate sentence), ANSWER-KEY-b3.md 5-6 (the scoring input) and
  ANSWER-KEY-b3.md 31-32 (AXIS). A script confirmed all three blocks are exact substrings of their
  sources.
- Effect: the AXIS gate passes on the row's own title OR any `members[].title`. SITE and BAND stay
  on the surviving row, `findings[]` remains the scoring input, and `filtered[]` is still not
  scored. The rule applies to the Phase-41 spot-check and Phase 43.

## Verification (observed output)

Scratch resolution check (`scratchpad/resolve_check.py`, stdlib, read-only over the archives)
printed:

```
catch_runs=29 guardrail=26 calibration=21 quiet headline=18 phase40=6 v29=9 excluded=3
survivors=188 axis_true=113 axis_false=75 unresolved=0 missing_at_site=0 runs_without_axis_true=0
RESOLUTION CHECK PASS
```

It asserts a dir + `state.json` exists for every run, `len(passes)==1`, and that each survivor
matches exactly one archived finding on (agent, line, title, stable_hash, band). It also checks
completeness (every archived finding at SITE is listed, and the counts are equal), at least one
axis=true per run, the run-dir regex on every listed path, and no `.failed`.

I mutation-tested it (so the check is not decorative). Dropping a survivor, editing a title,
clearing all axis flags, and editing a band each made it print `RESOLUTION CHECK FAIL`.

- Plan Task 1 `<verify>`: printed `MANIFEST OK` and `SEALED-UNCHANGED`.
- `grep -c '"axis": true'` = 113 (≥ 29). `grep -c '"why":'` = 188, which equals the survivor count.
- Plan Task 2 `<verify>`: printed `LEDGER-OK`. The diff has zero deleted lines, and 007 is the last
  `## ` heading.
- Entry 007 over-100 check: exactly one line exceeds 100 bytes: `(rendered band ≥ the row's
  floor). ... detected-below-threshold`. It sits inside the fenced sealed quote: SCORING-v2.10.md
  line 281, 100 characters, with `≥` multi-byte. Every non-quote line is ≤ 99 characters.
- `members` appears after line 236: 2 lines.
- Sealed artifacts: `git diff --quiet HEAD~2 HEAD` covers the three run archives,
  PREREGISTRATION-v2.10.md and both answer keys, and it exits 0.

## Deviations from Plan

**1. [Rule 1 - Accuracy] ANSWER-KEY-b3.md scoring-input quote spans lines 5-6, not line 5 alone**
- Found during: Task 2
- Issue: the scoring-input sentence starts on line 5 and ends on line 6. Quoting line 5 alone
  would cut the sealed sentence off mid-way.
- Fix: quoted lines 5-6 verbatim and cited "lines 5-6" beside the block.
- Commit: `7dce172`

**2. [Rule 2 - Correctness] Two archived findings at SITE carry no `title`**
- Found during: Task 1
- Issue: in `runs-v2.10/third-organic-should-catch/run-1`, `architecture` L307 and
  `language-typescript` L307 have no title and share stable_hash `3bb2479f…`.
- Fix: listed with `"title": null`, which copies the absence byte-exact, and labelled axis=false
  because a title-based gate cannot pass on them. They stay distinguishable by agent, so the
  resolution key is unique. The run still has 3 axis=true survivors.

## Assumption Drift (advisory)

- Found during: Task 1. The plan's example list implied "names escaping/XSS" could include titles
  that only say an autoescape fix was reverted. Actually, the sealed v2.9 autoescape run-1 MISS
  judged "undoes prior autoescape fix" and "revert of prior autoescape-regression fix" as NOT axis.
  I applied that stricter reading to every autoescape survivor so the manifest cannot contradict
  the sealed MISS. Two survivors keep axis=true only because a sealed column names them:
  `runs/…/run-3` framework-fastapi ("autoescape fragility") and the compliance
  never-disable-autoescaping titles. Across all diffs, revert-only framings are axis=false (for
  example session-rotation architecture "reverts the documented v2.8.1 CWE-613 fix"). This
  direction makes the guardrail stricter, never more lenient.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json
- FOUND: docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md (entry 007 last)
- FOUND: commit 4632208
- FOUND: commit 7dce172
