---
phase: 41-wave-1-scorer-side-noise-interventions
plan: 03
status: complete
subsystem: efficacy-evidence
tags: [b3, b-reweight, calibration, scorer-03, d-15, d-16]
requires: ["41-01 REPLAY-CATCH-MANIFEST-v2.10.json", "41-02 replay.py (iter_runs / load_manifest)"]
provides:
  - "plugins/vibe-check/scripts/calibrate.py: counts / pooled_precision / offsets_from_table / derive / run (counts | derive | --check)"
  - "plugins/vibe-check/scripts/test_calibrate.py: 26 tests"
  - "docs/design/b3-ground-truth/CALIBRATION-v2.10.md: D-15 method record + verbatim counts/offsets + D-16 tie-break"
affects: [41-04 (git-ancestry test: this record predates every candidate report), 41-05 (embeds AGENT_CONFIDENCE_OFFSET; --check must exit 0)]
tech-stack:
  added: []
  patterns: ["exact Fraction arithmetic for derived constants", "method record whose pasted CLI output is locked verbatim by a test"]
key-files:
  created:
    - plugins/vibe-check/scripts/calibrate.py
    - plugins/vibe-check/scripts/test_calibrate.py
    - docs/design/b3-ground-truth/CALIBRATION-v2.10.md
  modified: []
decisions:
  - "B-REWEIGHT offsets derived over the committed manifest: impact -12, architecture -6, bugs -2 (pool 96/147); the plan's label rule was applied as written and not revisited after seeing the counts"
  - "Derivation uses exact fractions.Fraction arithmetic so half-to-even rounding is exact (not subject to float noise)"
metrics:
  duration: "~12 min"
  completed: 2026-09-29
  tasks: "3/3"
  files: 3
---

# Phase 41 Plan 03: B-REWEIGHT method record and derivation — Summary

The B-REWEIGHT method is now fixed in code (`calibrate.py`) and in a committed record
(`CALIBRATION-v2.10.md`), and both were committed before any candidate replay. Over the 48
Claude-5-era runs (should-quiet-7 excluded) the pooled precision is **96/147**, and the derived
offsets are **`{"architecture": -6, "bugs": -2, "impact": -12}`**. `calibrate.py --check` exits 1
until 41-05 embeds them in `score.py`.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | `58bd89e` | calibrate.py: counts / derive / --check, D-04/D-06 boundary raises |
| 2 | `e56f6bf` | test_calibrate.py: constants, recorded counts, boundary / lower-only / thin / rounding proofs |
| 3 | `8b37b88` | CALIBRATION-v2.10.md + a test locking its pasted blocks to fresh CLI output |

## Verification (observed, this session)

- `calibrate.py counts`: exit 0. It prints the 8-agent table, `pooled precision = ΣTP/Σ(TP+FP) = 96/147`
  and `ALPHA=20 MIN_LABELED=5`.
- `calibrate.py derive`: `{"architecture": -6, "bugs": -2, "impact": -12}`. Every value is a
  negative int, and every key has n >= 5.
- `calibrate.py --check`: exit 1, `score.py has no AGENT_CONFIDENCE_OFFSET`. No arguments: exit 2.
- `pytest test_calibrate.py -q`: **26 passed**, 0 skipped. Four `assertRaises(calibrate.CalibrationError`
  sites (v2.9 quiet path, sq7 path, v2.9 catch flagged calibration, a missing quiet run), plus
  success on the untouched manifest.
- Mutation proofs (each applied to calibrate.py or the doc, then reverted):
  - Boundary call removed from the quiet loop: 1 failed.
  - Archive check disabled: 1 failed.
  - `MIN_LABELED` gate disabled: 2 failed.
  - Float in place of Fraction: 1 failed (the rounding pin).
  - Lower-only removed (both `min(0, …)` and the `off < 0` filter): 6 failed.
  - One digit changed in the doc's counts block and derive block: 2 failed.
  - Removing only `min(0, …)` changes nothing, because the `off < 0` filter also enforces
    lower-only. That is intentional belt-and-braces.
- Task 3 verify: 8 H2 sections, all greps pass, `DOC MATCHES DERIVE`, 0 non-table lines over 100
  columns, the record has exactly one commit, and the only `REPLAY-REPORT-phase41-*.md` is the
  baseline.
- Full suite (`plugins/vibe-check/scripts`, bare `pytest -q`): **1059 passed**, 1146 subtests passed.
- Sealed roots (`runs`, `runs-v2.10`, `runs-v2.10-phase40`, PREREGISTRATION-v2.10):
  `git diff --quiet HEAD`, so SEALED-UNCHANGED.

## Deviations from Plan

1. **[Rule 1 - Bug] Exact Fraction arithmetic in place of `100.0 * float`.** The plan specified
   `int(round(100.0 * (p_hat - p_pool)))`. In floats, an exact half such as 19/40 − 1/2 becomes
   −2.5000000000000027, which rounds to −3. That breaks the half-to-even rule the record states.
   `fractions.Fraction` makes the stated rule exact, and `fractions` is in the pinned import set.
   The real offsets are the same either way; only exact-half cases differ.
2. **[Rule 2] Added `offsets_from_table(table)`.** `derive` delegates to it, so the lower-only,
   thin-agent and rounding tests can run on synthetic tables, as Task 2 requires.
3. **[Rule 2] A quiet run missing from the archive raises `CalibrationError`.** Without this it
   would be silently uncounted. The manifest `archive` must also match the walk for catch runs.
4. **[Rule 2] Added `TestMethodRecord`.** It locks the doc's pasted `counts` and `derive` blocks
   to fresh CLI output, so the "verbatim" acceptance criterion is enforced, not just claimed.
   It is committed with the doc in `8b37b88`.
5. **Verify-script quirk.** On macOS, `wc -l` left-pads its output, so the plan's
   `wc -l | grep -qx 1` never matches. I re-checked with `tr -d ' '`: the record has exactly one
   commit.

## Assumption Drift (advisory)

- **Found during:** Task 1.
- **Planned:** research's indicative counts (impact 6/26, architecture 0/6, pool 46/97) give the
  offsets impact −18 and architecture −11. The plan said to treat these as the expected shape only.
- **Actual:** the committed 41-01 manifest gives impact 24/26, architecture 6/6, compliance 7/0,
  bugs 22/13, codex 18/4, and pool **96/147**. The offsets are impact **−12**, architecture
  **−6** and bugs **−2**.
- **Why:** 41-01 labels every finding at SITE for AXIS, where research hand-listed one qualifier
  per run. As a result, more catch-run survivors count as TP and the pool rises. Four TPs sit at
  band `medium`, because the TP rule has no band filter while the FP rule requires
  critical/warning. The record discloses this asymmetry.
- **Consequence for later plans:** the offsets are smaller than research assumed. B-REWEIGHT
  should therefore be safer against the guardrail (impact −12 is well inside research's −20
  single-agent bound). Its predicted FP reduction is likely smaller than the prototype's 16/18 to
  12/18. D-15 forbids revisiting α or the label rule because of this, and nothing was changed.
  41-04's replay will measure the actual effect.

## Known Stubs

None.

## Threat Flags

None. calibrate.py reads the committed manifest and archives through replay.py. It prints agent
names, integers and fractions only. The import set is pinned (no `subprocess`), and no
`.turingmind` literal appears.

## Self-Check: PASSED

- FOUND: calibrate.py, test_calibrate.py, CALIBRATION-v2.10.md
- FOUND commits: 58bd89e, e56f6bf, 8b37b88
