---
phase: 60-exact-change-evidence-and-reliable-finalize
verified: 2026-10-29T00:00:00Z
status: gaps_found
score: 3/6 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
gaps:
  - truth: "GSD/incremental range source survives into the fresh Bash call that runs 30-collect-score.md's range fence (part of EVID-03 / SC3)"
    status: failed
    severity: blocking
    reason: >
      30-collect-score.md's range-source table puts `$PHASE_START` and
      `$LAST_REVIEWED_SHA` directly into the git-diff command for the GSD and
      incremental routes, with no instruction to substitute the literal value
      the way BLOBFILE/GATEFILE now require. 00-scope.md and 05-state.md bind
      these variables in earlier bash fences, not by printing a path. A fresh
      Bash call (the review's own established convention, and the exact
      lesson this phase applied to Finalize) does not inherit the variable,
      so `git diff $PHASE_START` silently becomes `git diff ` (index vs
      working tree). Reproduced directly: a repo with a committed edit plus
      an uncommitted edit, run through the literal row text in a fresh `bash
      -c` shell with the variable unset, returned `{"f.txt": [[5, 5]]}` (rc 0)
      instead of the correct `{"f.txt": [[3, 3], [5, 5]]}` — the committed
      change silently disappears from the range, which can silently drop a
      qualifying finding's +20 in_diff term or a nearby-change re-ask on
      exactly the two routes (MIXED-COORD) this phase's own fix targeted.
      TestRouteGSD/TestRouteIncremental only call `ranges_from_diff` with an
      already-substituted SHA; TestProseRangeFence (the only test that
      executes the real fence in a fresh shell) covers the default route
      only. Not listed in 60-REPRO.md's Residuals.
    artifacts:
      - path: "plugins/vibe-check/phases/review/30-collect-score.md"
        issue: "GSD/incremental range-source rows use $PHASE_START / $LAST_REVIEWED_SHA directly; no printed-literal substitution instruction"
      - path: "plugins/vibe-check/phases/review/00-scope.md"
        issue: "$PHASE_START bound by a raw bash assignment, never printed as a literal path the way BLOBFILE/GATEFILE are"
      - path: "plugins/vibe-check/phases/review/05-state.md"
        issue: "$LAST_REVIEWED_SHA bound the same way, same gap"
    missing:
      - "An explicit instruction (and a fresh-shell TestProseRangeFence-style test) that the GSD/incremental range source is a literal SHA substituted by the agent, not a bash variable reference, before the range fence runs"
  - truth: "The exact-range builder does not halt on, or silently empty ranges for, an ordinary diff altered by a legitimate repo-local git setting (part of the T-60-13 threat mitigation this phase's own plans committed to, and of the EVID-01/EVID-03 goal text 'ranges come from actual added/deleted lines on every route')"
    status: failed
    severity: blocking
    reason: >
      Reproduced directly: with `git -c diff.suppressBlankEmpty=true`, a
      completely ordinary diff whose 3-line default context includes one
      blank line (an extremely common shape — any edit near a blank line
      separating functions) makes diff_ranges.py raise
      REASON_BAD_BODY_LINE and the review-halted fence stop the ENTIRE pass,
      every time, for as long as that setting is active. This is not a
      malformed/attacker diff (the class the refusal exists for) — it is an
      ordinary diff the parser cannot read because it assumes every context
      line prints a leading space. None of the prose's fixed flags
      (--no-color --no-ext-diff --src-prefix --dst-prefix) touch this
      setting. A second, narrower issue in the same area: a colored or
      textconv-altered diff that doesn't match `_HUNK`/`+++` patterns is
      silently skipped and yields `{}` with exit 0 (fail-open), which
      30-collect-score.md's own prose says must never happen ("fail closed —
      a pass scored with missing ranges silently drops the in-diff term").
      The primary fence in 30-collect-score.md does carry --no-color, which
      defeats a plain color.ui=always repro; but the abbreviated "Range
      source for 30-collect-score" lines added to 00-scope.md/05-state.md
      give the bare command without those flags, and diff.suppressBlankEmpty
      is not covered by any of the four fixed flags regardless. Neither
      textconv nor diff.relative is mitigated at all. Not listed in
      60-REPRO.md's Residuals; TestHazards only covers color.ui,
      diff.noprefix and diff.mnemonicPrefix.
    artifacts:
      - path: "plugins/vibe-check/scripts/diff_ranges.py"
        issue: "_walk_hunk requires every context line's first byte to be a literal space; diff.suppressBlankEmpty prints a true empty line for a blank context line, which the walker cannot distinguish from a malformed body line"
    missing:
      - "Treat an empty line inside a hunk body as a context line (tag defaults to ' ' when the line is ''), plus a diff.suppressBlankEmpty case in TestHazards; and/or pin diff.suppressBlankEmpty=false alongside the other fixed flags"
  - truth: "Finalize's automatic rebuild-once rule can actually complete a retry when the failure is in the gate's own input file (part of FINL-02: 'a later successful retry may complete after revalidating snapshot freshness')"
    status: failed
    severity: blocking
    reason: >
      90-finalize.md's "One automatic rebuild, then stop" paragraph mints a
      NEW BLOBFILE and rebuilds HEAD fingerprints on retry, then says to
      "re-run the counts fence and the gate once with the new literal" — it
      never instructs re-minting GATEFILE or rewriting it with the rebuilt
      counts. GATEFILE is minted exactly once in the file (grep confirms a
      single `GATEFILE=$(mktemp ...)` fence, outside any retry structure).
      If the GATEFILE write itself is the point of failure (an empty or
      stale GATEFILE causing the gate fence's non-zero exit — exactly the
      trigger condition the rebuild rule names), the documented retry reuses
      the same broken file and fails identically; the rebuilt, more-current
      COUNTS_JSON never reaches the gate. No test in test_finalize_card.py
      exercises a GATEFILE-specific failure-then-retry path (only
      test_retry_mints_new_blobfile_after_missing_path, which is a
      BLOBFILE-only scenario, and test_malformed_gatefile_shows_only_stop_sentence,
      which checks the owner-visible message for ONE attempt, not recovery
      across a retry). Not listed in 60-REPRO.md's Residuals.
    artifacts:
      - path: "plugins/vibe-check/phases/shared/90-finalize.md"
        issue: "Rebuild-once paragraph (the 'One automatic rebuild, then stop' text) names only BLOBFILE; GATEFILE is minted once outside the retry path"
    missing:
      - "An explicit instruction to re-mint GATEFILE and rewrite the seven-key flags object from the rebuilt COUNTS_JSON on the one retry, plus a test that a GATEFILE-specific failure actually recovers"
deferred: []
human_verification:
  - test: "Confirm whether Claude Code's Write tool refuses the first write to a path that `mktemp` just created but the agent never Read (SA-01 in 60-REVIEW.md)"
    expected: "Either the Write succeeds (the existing ROWSFILE/SUGGESTFILE/REFSFILE pattern already relies on this), or it is refused and every --finalize attempt (and its one retry) fails at the BLOBFILE/GATEFILE write step"
    why_human: "Depends on live Claude Code harness Write-tool behavior that cannot be exercised from a pytest fixture; the reviewer explicitly set this aside as needing a ruling rather than asserting it reproduces"
  - test: "Decide whether the PR route's hard failure on very large PRs (SA-02: gh pr diff over ~300 files / 20k lines) needs a fallback or is an accepted limit"
    expected: "An owner ruling, not a reproduction — the reviewer notes failing closed is the intended behavior here"
    why_human: "Product/scope decision, not a code defect"
---

# Phase 60: Exact change evidence and reliable Finalize Verification Report

**Phase Goal:** Nearby/in-diff ranges come from actual added/deleted lines on every review route, and Finalize's blob-file path survives fresh Bash calls (999.24, 999.25).
**Verified:** 2026-10-29
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1/EVID-01 core: ranges are built only from a hunk's `+`/`-` body markers, not display context; an edit at the intended 5-line boundary reopens a decision and an edit just outside does not | ✓ VERIFIED | `diff_ranges.py` read in full; marker-walk, D-02 net-deletion `+1`, pure-deletion `[max(T,1), T+1]` all match the documented contract. `TestRealDiffRanges60` (10 tests, five boundary pairs) passes at HEAD. Full suite run by me: `3765 passed, 4930 subtests passed, 0 failed` (`plugins/vibe-check/scripts`, `pytest -q -p no:cacheprovider`). |
| 2 | SC2/EVID-02: fixtures that run a real `git diff` produce correct ranges for ordinary, deletion-only, insertion and relocated-finding shapes | ✓ VERIFIED | Same full-suite evidence; `test_diff_ranges.py` (`TestShapesRealGit`, `TestMutants` — 19 mutants, each shown to trip only after the real module passes) read and confirmed present; `TestRepro60Evidence` documenting repros pass. |
| 3 | SC3/EVID-03: every route (default, GSD, incremental, range, PR, `--all`) reliably uses the exact-range builder from a genuinely fresh Bash call | ✗ FAILED | GSD/incremental rows in `30-collect-score.md` reference `$PHASE_START`/`$LAST_REVIEWED_SHA` directly, bound in an earlier, separate bash fence (`00-scope.md`, `05-state.md`). Reproduced: run the literal row text in a fresh `bash -c` shell with the variable unset → silently returns a wrong, narrower range (`{"f.txt": [[5, 5]]}` instead of `{"f.txt": [[3, 3], [5, 5]]}`), rc 0, no halt. Default/range/PR/`--all` routes are unaffected (default is covered end-to-end by `TestProseRangeFence`, which substitutes a literal). |
| 4 | Range mechanism fails closed (halts, never silently empties) when the diff text is altered by a legitimate repo-local git setting — the class of threat Phase 60's own T-60-13 mitigation commits to | ✗ FAILED | Reproduced: `git -c diff.suppressBlankEmpty=true diff <prose flags> HEAD \| python3 diff_ranges.py` on an ordinary diff with one blank context line raises `REASON_BAD_BODY_LINE`, halting every pass under that setting. Separately, `git -c color.ui=always diff HEAD` (no `--no-color`, i.e. the bare command the abbreviated "Range source" lines in `00-scope.md`/`05-state.md` show) through `diff_ranges.py` gives `{}` rc 0 — fail-open, contradicting the prose's own "fail closed" sentence. The fully-flagged fence actually executed from `30-collect-score.md`'s table does carry `--no-color`, which defeats the plain `color.ui` repro, but `diff.suppressBlankEmpty`/textconv/`diff.relative` are not covered by any of the four fixed flags. |
| 5 | SC4/FINL-01: a fresh-shell walk through every Finalize fence reaches counts → gate → report using the printed, literally reused `BLOBFILE=` path | ✓ VERIFIED | `90-finalize.md` read: `BLOBFILE=$(mktemp ...)` / `printf 'BLOBFILE=%s\n'` fence present; counts fence substitutes the literal; gate reads a printed `GATEFILE=`, stderr to `<GATEFILE>.err`. `TestFinalizeFreshShellWalk` (7+ tests) passes in the full-suite run; reverse run in 60-REPRO.md shows the pre-fix walk failing at the RED SHA and the SUMMARY's green SHAs (`b8fb21a`, `fd8c1b9`) match commits present on this branch. |
| 6 | SC5/FINL-02: a failed or refused attempt stops and writes nothing; a later retry may complete after revalidating freshness; no-write-on-failure and independent fix verification are unchanged | ✗ FAILED | The "no write before `write`" half is solid (`write_boundary_holds` + 3 mutants; stale-attempt walk proves independent fix verification unaffected). The "a later retry may complete" half is not: the rebuild-once paragraph re-mints only `BLOBFILE`; `GATEFILE` is minted exactly once in the file, outside any retry structure, and the rebuilt `COUNTS_JSON` is never shown to be rewritten into a fresh `GATEFILE` before the gate is re-run. No test exercises a GATEFILE-specific failure followed by a retry. |

**Score:** 3/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/diff_ranges.py` | `ranges_from_diff`, `RangeError`, `REASON_*`, `run`, CLI shim, stdlib-only | ✓ VERIFIED | 219 lines, read in full; import set `{json, re, sys}` confirmed by direct `ast` walk in 60-02-SUMMARY and by code read |
| `plugins/vibe-check/scripts/test_diff_ranges.py` | Contract tests, route classes, mutants | ✓ VERIFIED | 1110 lines; `TestRouteDefault/GSD/Incremental/Range/PR/All`, `TestProseRangeFence` all present (`grep -c "^class TestRoute"` = 6, confirmed in 60-04-SUMMARY and by reading) |
| `plugins/vibe-check/scripts/fixtures/pr-cumulative.diff` | Real `gh pr diff` capture, provenance documented | ✓ VERIFIED | 286 lines, 4 `diff --git` sections, 0 mbox lines — confirmed directly (`wc -l`, `grep -c`) |
| `plugins/vibe-check/phases/shared/90-finalize.md` | Printed BLOBFILE/GATEFILE fences, rebuild-once/refused-step rules | ⚠️ PARTIAL | Printed-path fences correct and wired; the rebuild-once rule is incomplete for GATEFILE-specific failures (gap 3 above) |
| `plugins/vibe-check/phases/review/30-collect-score.md` | One range source per route through `diff_ranges.py`, fail-closed fence | ⚠️ PARTIAL | Default/range/PR/`--all` rows are sound and fully flagged; GSD/incremental rows carry an unresolved cross-call variable (gap 1 above) |
| `plugins/vibe-check/scripts/test_nv_render.py` | Retargeted prose lock | ✓ VERIFIED | Phrases/mutant loop confirmed passing in full suite |
| `.planning/phases/.../60-REPRO.md` | Verdict ledger, reverse run, residuals | ✓ VERIFIED (as a ledger of what it tested) | Internally consistent, SHAs match `git log`; does not mention the three gaps above (not something the ledger could have caught — none of them were in the 60-01 reproduction set) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `test_decision_continuity.TestRealDiffRanges60._builder` | `diff_ranges.ranges_from_diff` | lazy import | ✓ WIRED | Confirmed green in full suite |
| `30-collect-score.md` range fence | `scripts/diff_ranges.py` | `... \| python3 "$VC_ROOT/scripts/diff_ranges.py"` under `set -o pipefail` | ✓ WIRED (default/range/PR/`--all`) / ⚠️ fragile (GSD/incremental — see gap 1) | Confirmed by reading the fence and by direct reproduction of the GSD-route failure mode |
| `90-finalize.md` counts/rows fences | `carry_state.py finalize-counts` | literal `"$BLOBFILE"` substitution | ✓ WIRED | Confirmed by code read + passing walk tests |
| `90-finalize.md` gate fence | `finalize_gate.py` | `< "$GATEFILE"`, stderr to `<GATEFILE>.err` | ✓ WIRED (first attempt) / ✗ NOT RE-WIRED on retry | See gap 3 |

### Data-Flow Trace (Level 4)

Not applicable in the UI-rendering sense — this phase is a backend/CLI/prose mechanism, not a rendered component. The equivalent trace (range source → helper → score.py consumer) is covered by the Key Link table above and the gaps found therein.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider` | `3765 passed, 4930 subtests passed in 180.14s, 0 failed` | ✓ PASS |
| diff_ranges.py correct on ordinary edit | manual real-git repro in scratch dir | `{"f.txt": [[2, 2]]}` | ✓ PASS |
| diff_ranges.py on colored diff without `--no-color` | `git -c color.ui=always diff HEAD \| diff_ranges.py` | `{}` rc 0 | ✗ FAIL (fail-open; mitigated on the primary fully-flagged fence only) |
| diff_ranges.py with `--no-color` flag present | `git -c color.ui=always diff --no-color ... HEAD \| diff_ranges.py` | `{"f.txt": [[2,2]]}` | ✓ PASS (confirms the primary fence's flags work) |
| diff_ranges.py under `diff.suppressBlankEmpty=true` on an ordinary diff with a blank context line | manual real-git repro | `unexpected line in hunk body`, rc 2 (halts) | ✗ FAIL |
| GSD range-source row run literally in a fresh shell with `$PHASE_START` unset | manual real-git repro, two commits + working-tree edit | `{"f.txt": [[5, 5]]}` instead of `{"f.txt": [[3, 3], [5, 5]]}` | ✗ FAIL (silent, wrong, non-halting) |
| TestRouteGSD / TestRouteIncremental / TestProseRangeFence | `pytest -q test_diff_ranges.py test_decision_continuity.py -k "TestRouteGSD or TestRouteIncremental or TestProseRangeFence"` | `11 passed, 2 subtests passed` | ✓ PASS (but does not exercise the fresh-shell cross-call scenario above — confirms the gap is untested, not refuted) |
| GATEFILE-specific retry test existence | `grep -n "def test_retry\|GATEFILE" test_finalize_card.py` | only `test_retry_mints_new_blobfile_after_missing_path` (BLOBFILE-only) | ✗ FAIL (no coverage for the GATEFILE retry gap) |

### Probe Execution

SKIPPED — no `scripts/*/tests/probe-*.sh` convention in this repo and none declared by the Phase 60 PLAN/SUMMARY files; verification used the project's own `pytest` suite and direct reproduction instead.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| EVID-01 | 60-01, 60-02, 60-04 | Ranges from added/deleted lines only, boundary-exact | ⚠️ Mostly satisfied — core math verified; robustness gap (diff.suppressBlankEmpty halt) found | Truths 1, 4 above |
| EVID-02 | 60-01, 60-02 | Correct ranges for ordinary/deletion/insertion/relocated shapes via real git diff | ✓ SATISFIED | Truth 2 above |
| EVID-03 | 60-04 | Every route uses exact ranges or reports unsupported fixture; nothing else assumes 3-line context | ✗ BLOCKED (GSD/incremental fresh-shell gap) | Truth 3 above |
| FINL-01 | 60-03 | Printed BLOBFILE literal reused; fresh-shell walk reaches write/report | ✓ SATISFIED | Truth 5 above |
| FINL-02 | 60-03, 60-05 | No-write-on-failure; retry completes after revalidating freshness; independent fix verification unchanged | ⚠️ PARTIALLY SATISFIED — no-write-on-failure and fix-verification halves solid; retry-completes half has a reproduced gap | Truth 6 above |

No orphaned requirement IDs: REQUIREMENTS.md maps exactly EVID-01, EVID-02, EVID-03, FINL-01, FINL-02 to Phase 60, and all five appear in at least one plan's `requirements:` frontmatter (60-01, 60-02, 60-03, 60-04, 60-05).

**Note on REQUIREMENTS.md/ROADMAP.md claims:** both currently mark EVID-01/02/03 and FINL-01/02 as `Complete` (EVID-03 with one disclosed known limit — the live `gh pr diff` fetch, D-05/R6). That status is premature for EVID-03 and FINL-02 given gaps 1 and 3 above, and should be revisited — these two were not in 60-01's reproduction set and are not in 60-REPRO.md's Residuals, so the ledger's own internal consistency is not in question; its *coverage* is incomplete relative to what the advisory code review (60-REVIEW.md) and my own reproduction found afterward.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No `TBD`/`FIXME`/`XXX` debt markers found in any file this phase modified | — | n/a (checked directly) |
| `plugins/vibe-check/phases/shared/90-finalize.md` | 15, 48 | `mktemp "..."` instances flagged by a naive grep for `XXX` are the `vc.XXXXXX` mktemp template, not a debt marker | info | false positive, confirmed by reading |
| `plugins/vibe-check/scripts/diff_ranges.py` | 128-150 | Parser assumes every context line in a hunk body starts with a literal space | warning→blocking | WR-01 above (halts on `diff.suppressBlankEmpty`) |
| `plugins/vibe-check/phases/shared/90-finalize.md` | ~15-67 | Temp files (`BLOBFILE`, `GATEFILE`, `GATEFILE.err`, plus a second set on retry) are never `rm -f`'d | info/minor | matches 60-REVIEW.md WR-05; resource-hygiene, not a functional break; not in Residuals |

### Human Verification Required

### 1. Write-tool refusal risk on freshly-minted temp files (SA-01)

**Test:** Run a live `--finalize` in Claude Code and observe whether the Write tool accepts the first write to the path printed after `BLOBFILE=`/`GATEFILE=` (a file `mktemp` just created but the agent never `Read`).
**Expected:** The write succeeds (consistent with the pre-existing ROWSFILE/SUGGESTFILE/REFSFILE pattern), or — if it is refused — every `--finalize` attempt and its one retry both fail at the same step.
**Why human:** Harness Write-tool behavior cannot be exercised from a pytest fixture; 60-REVIEW.md itself set this aside as needing a ruling rather than asserting it reproduces.

### 2. PR size-limit fallback decision (SA-02)

**Test:** None — this is a scope/product decision.
**Expected:** An explicit owner ruling on whether `gh pr diff` failing closed on very large PRs (~300+ files / 20k+ lines) is an accepted limit or needs a fallback.
**Why human:** Not a code defect; the reviewer calls the current fail-closed behavior intended.

### Gaps Summary

The bulk of Phase 60's deliverable is solid and well-evidenced: the exact-range marker-walk algorithm (`diff_ranges.py`) is correct on every documented shape, mutation-tested, and matches real `git diff` output at every context width; the default/range/PR/`--all` review routes and the Finalize happy path (printed `BLOBFILE=`/`GATEFILE=`, fresh-shell walk to `write`) are genuinely fixed and tested — the full suite passes (3765 passed, 0 failed), and I independently reproduced the correct behavior for the non-gap cases.

Three gaps, each independently reproduced by me (not just taken from the advisory review), defeat specific parts of the stated goal and success criteria and were not caught by the phase's own reproduce-first fixtures or disclosed in 60-REPRO.md's Residuals:

1. **GSD/incremental routes use an unresolved shell variable as their range source** (`$PHASE_START`, `$LAST_REVIEWED_SHA`), reintroducing — in this phase's own new mechanism — the exact cross-call-variable defect class (999.25) that this same phase fixed for Finalize's `$BLOBFILE`. In a genuinely fresh shell this silently drops committed changes from the range (a silent loss of a qualifying finding), rather than halting.
2. **The range builder halts on an ordinary diff** under the real, user-settable git config `diff.suppressBlankEmpty=true` (any diff with a blank context line — extremely common), and can silently return `{}` for diff text altered by settings the fixed flags don't cover (textconv, `diff.relative`), contradicting the prose's own stated fail-closed design.
3. **Finalize's one-retry rebuild does not re-mint or refresh `GATEFILE`**, so a GATEFILE-specific failure (the exact trigger the rebuild rule is written to catch) is not actually recoverable by the documented retry.

None of these were part of 60-01's reproduction set (they are new edge cases, not the ones 999.24/999.25 originally named), so 60-REPRO.md's internal red/green bookkeeping is not inconsistent — but the phase's closing claim ("Complete" for EVID-03 and FINL-02, with only the live-`gh`-fetch limit disclosed) overstates what was actually hardened. These are exactly the "broken required workflow" / "silent loss of a qualifying finding" classes the project's own working rule treats as requiring a fix rather than a carried residual.

**This looks like it could be either fixed in a short follow-up or formally accepted as residuals.** If the owner judges these acceptable to carry (as `60-REPRO.md` already carries R1-R11), add overrides to this file's frontmatter citing each truth above; otherwise route to a follow-up plan before closing EVID-03/FINL-02 as Complete.

---

_Verified: 2026-10-29_
_Verifier: Claude (bm-verifier)_
