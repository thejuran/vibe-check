---
phase: 60-exact-change-evidence-and-reliable-finalize
verified: 2026-10-29T00:00:00Z
status: gaps_found
score: 4/6 must-haves verified
has_blocking_gaps: true
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/6
  gaps_closed:
    - "GSD/incremental range source survives into a fresh Bash call (GSD-SHELL-VAR) — fixed by 60-07, independently re-reproduced below"
    - "Range builder halts on, or silently empties, an ordinary diff altered by a legitimate repo-local git setting (CONFIG-ALTERED-DIFF) — fixed by 60-06 + 60-07, independently re-reproduced below"
    - "Finalize's automatic rebuild-once rule cannot complete a retry when the failure is in the gate's own input file (GATEFILE-RETRY) — fixed by 60-08, independently re-reproduced below"
  gaps_remaining: []
  regressions: []
gaps:
  - truth: "Every route reliably uses the exact-range builder from a genuinely fresh Bash call, with no way to subvert the substituted value (EVID-03)"
    status: failed
    severity: blocking
    reason: >
      The GSD-SHELL-VAR gap (silent narrowing when $PHASE_START/$LAST_REVIEWED_SHA
      is left as an unresolved shell variable) is genuinely fixed by 60-07: a
      literal substituted into the quoted placeholder gives the correct ranges,
      and an unsubstituted quoted value now makes git exit 128 and halts through
      pipefail (independently reproduced below). But the fix itself opened a new,
      more severe hole, reported as CR-01 in 60-REVIEW.md (commit cfa473a) and
      independently reproduced by me: 05-state.md step 2 binds
      $LAST_REVIEWED_SHA = state.passes[-1].head_sha with no validation, and
      30-collect-score.md's row has the agent paste that value, as-is, into
      "<last-reviewed-sha>" inside a double-quoted git-diff argument. Double
      quotes stop word-splitting but do not stop $(...) command substitution.
      The state file lives at .turingmind/state/format-53/<key>.json inside the
      reviewed repo; 07-first-run.md only PRINTS a suggestion to add
      .turingmind/ to .gitignore and never auto-edits it (confirmed by reading
      the file), so a contributor can commit a crafted state file with a
      predictable key (GSD mode: <phase-dir-name>.json) and a poisoned
      head_sha. I reproduced the exploit directly: substituting
      "$(touch "$T/pwned")HEAD" for the placeholder in the exact flagged
      command from 30-collect-score.md's row runs the injected command and
      still exits 0 with valid-looking JSON output ({}) — a silent, successful
      command execution with no indication anything happened. "Every route
      reliably uses the exact-range builder" cannot be marked true while the
      value that route substitutes can run arbitrary shell commands.
    artifacts:
      - path: "plugins/vibe-check/phases/review/05-state.md"
        issue: "step 2 binds $LAST_REVIEWED_SHA from the state JSON with no format validation before it is substituted into a shell command elsewhere"
      - path: "plugins/vibe-check/phases/review/30-collect-score.md"
        issue: "the pass >= 2 (and GSD) row instructs substituting the unvalidated literal into a double-quoted git-diff argument, which does not stop $(...) command substitution"
    missing:
      - "Validate head_sha (and, for symmetry, the phase-start sha) against ^[0-9a-f]{40}([0-9a-f]{24})?$ where it is bound, and halt with a fixed message on any other value, before it is ever substituted into a command — per 60-REVIEW.md CR-01's fix"
  - truth: "A failed or refused Finalize attempt stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness (FINL-02)"
    status: failed
    severity: blocking
    reason: >
      The GATEFILE-RETRY gap (the one-rebuild-then-stop rule not recovering
      from a GATEFILE-specific failure) is genuinely fixed by 60-08: the
      rebuild-once paragraph now names the GATEFILE trigger and re-mint,
      and the fresh-shell walk test passes (independently reproduced below
      via the full test_finalize_card.py run, 89 passed). But a different,
      adjacent code path in the SAME file is still broken, reported as WR-02
      in 60-REVIEW.md: the "After the answer" step 3 "fix empty" branch says
      only "Then RE-RUN the counts step and the gate ONCE (the same
      BLOBFILE= literal this attempt printed)" — it names BLOBFILE reuse
      explicitly but never says to rewrite GATEFILE's flags from the
      recomputed $COUNTS_JSON before re-running finalize_gate.py, unlike the
      rebuild-once paragraph 15 lines earlier, which spells this out in full
      ("run the gate-input fence again so it prints a NEW GATEFILE=, write
      the seven-key flags object from the REBUILT $COUNTS_JSON to that new
      path"). I mechanically reproduced the consequence with the real
      carry_state.py/finalize_gate.py helpers and the shipped six-row
      fixture: the gate returns "outstanding-to-phase-5" on the stale,
      pre-decision GATEFILE; after dismissing every open obligation through
      carry_state.record_decisions, the recomputed counts are correctly
      (0, 0, 0), yet re-running finalize_gate.py against the SAME,
      unrewritten GATEFILE still returns "outstanding-to-phase-5" (not
      "write") — only a freshly written GATEFILE from the recomputed counts
      returns "write". No test in test_finalize_card.py walks this: the
      test's own _gate() helper always mints a new GATEFILE with fresh
      flags, so it proves the mechanics CAN work, not that the prose text
      says to do this; test_answer_files (line ~649) checks only ordering,
      per 60-REVIEW.md's own note. This breaks the file's explicit "Card
      budget: Finalize costs one card" promise on the ordinary (non-failure)
      card-answer path: the owner answers the card, every obligation is
      dismissed, and Finalize can still report "stays blocked" instead of
      writing, requiring a second `--finalize` invocation to actually close.
    artifacts:
      - path: "plugins/vibe-check/phases/shared/90-finalize.md"
        issue: "step 3's \"fix empty\" branch (line ~272) re-runs the gate without instructing a GATEFILE rewrite from the recomputed COUNTS_JSON, unlike the rebuild-once paragraph which spells this out"
      - path: "plugins/vibe-check/scripts/test_finalize_card.py"
        issue: "test_card_route_records_then_writes exercises the re-run through its own _gate() helper, which always mints a fresh GATEFILE regardless of what the prose text instructs, so it does not catch this gap"
    missing:
      - "Step 3's \"fix empty\" branch must explicitly say to re-run the gate-input fence (new or rewritten GATEFILE) with flags built from the recomputed COUNTS_JSON before re-running finalize_gate.py, mirroring the rebuild-once paragraph's wording, plus a fresh-shell walk test that records decisions, recomputes counts to (0,0,0), and shows the stale GATEFILE still fails while a rewritten one succeeds"
deferred: []
human_verification:
  - test: "Confirm whether Claude Code's Write tool refuses the first write to a path that `mktemp` just created but the agent never Read (SA-01 in 60-REVIEW.md, carried as R16 in 60-REPRO.md)"
    expected: "Either the Write succeeds (the existing ROWSFILE/SUGGESTFILE/REFSFILE pattern already relies on this), or it is refused and every --finalize attempt (and its one retry) fails at the BLOBFILE/GATEFILE write step"
    why_human: "Depends on live Claude Code harness Write-tool behavior that cannot be exercised from a pytest fixture"
  - test: "Decide whether the PR route's hard failure on very large PRs (SA-02: gh pr diff over ~300 files / 20k lines) needs a fallback or is an accepted limit"
    expected: "An owner ruling, not a reproduction — the reviewer notes failing closed is the intended behavior here"
    why_human: "Product/scope decision, not a code defect"
---

# Phase 60: Exact change evidence and reliable Finalize Verification Report

**Phase Goal:** The nearby window is exactly what the decision rules say on every review route, and Finalize either completes from a fresh shell or stops safely without writing (999.24, 999.25)
**Verified:** 2026-10-29
**Status:** gaps_found
**Re-verification:** Yes — after the gap-closure round (plans 60-06, 60-07, 60-08, 60-09), re-verifying against the 3 gaps found at commit `2f84d2e`, plus the gap-round's own code review (`60-REVIEW.md`, commit `cfa473a`)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1/EVID-01 core: ranges are built only from a hunk's `+`/`-` body markers, not display context | ✓ VERIFIED (regression-checked) | `diff_ranges.py` unchanged in its marker-walk core since the first close except the gap-round's additive fixes; `test_diff_ranges.py` full file: `100 passed, 75 subtests passed` (run by me just now). Unaffected by the gap round. |
| 2 | SC2/EVID-02: fixtures that run a real `git diff` produce correct ranges for ordinary, deletion-only, insertion and relocated-finding shapes | ✓ VERIFIED (regression-checked) | Same run as above; `TestShapesRealGit`/`TestMutants` present and green, unaffected by the gap round. |
| 3 | SC3/EVID-03: every route reliably uses the exact-range builder from a genuinely fresh Bash call, including the value substituted into it | ✗ FAILED | The original GSD-SHELL-VAR gap is fixed (see below), but the fix introduced CR-01 — a reproduced command-injection hole in the same substitution. See `gaps` above. |
| 4 | Range mechanism fails closed (halts, never silently empties) when the diff text is altered by a legitimate repo-local git setting (T-60-13) | ✓ VERIFIED | Independently reproduced in a scratch repo: `diff.suppressBlankEmpty=true` on an ordinary edit next to a blank context line now gives `{"g.txt": [[14, 14]]}` rc 0 (no halt, correct range) instead of the pre-fix `RangeError`; `git -c color.ui=always diff HEAD` (no `--no-color`) now refuses with `colored or escaped diff` rc 2 instead of `{}` rc 0; `printf 'fatal: bad revision\n'` refuses with `not a unified diff` rc 2. All three match 60-06/07's claims exactly. WR-01 (`diff.submodule`, a narrower, not-previously-scoped edge case) is a carried residual in 60-REVIEW.md, not independently re-opened here. |
| 5 | SC4/FINL-01: a fresh-shell walk through every Finalize fence reaches counts → gate → report using the printed, literally reused `BLOBFILE=` path | ✓ VERIFIED (regression-checked) | `test_finalize_card.py` full file: `89 passed, 132 subtests passed` (run by me just now). `TestFinalizeFreshShellWalk` unaffected by the gap round. |
| 6 | SC5/FINL-02: a failed or refused attempt stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness | ✗ FAILED | The GATEFILE-RETRY gap (failure-path retry) is fixed (rebuild-once paragraph now names GATEFILE, confirmed by reading the file and by the green test suite). But WR-02 — a stale-GATEFILE defect in the ordinary post-decision gate re-run (a different code path in the same file) — is reproduced mechanically below and is not fixed by any plan in this round. See `gaps` above. |

**Score:** 4/6 truths verified (up from 3/6 at the prior close; both remaining failures are new findings on the fixed code, not the original three gaps, which are closed)

### Independent re-reproduction of the three original gaps (all CLOSED)

**GSD-SHELL-VAR (60-07).** Built a repo with a committed edit at line 3 and an uncommitted edit at line 5. Running the literal GSD row text from `30-collect-score.md` in a genuinely fresh `bash -c` shell:
- With the base sha substituted for `"<phase-start-sha>"`: `{"f.txt": [[3, 3], [5, 5]]}` rc 0 — correct, includes the committed change.
- With `"$PHASE_START"` left in place and unset: `fatal: ambiguous argument ''` → the pipeline exits 128 under `pipefail` — halts, does not silently narrow.
Matches 60-07-SUMMARY.md and 60-REPRO.md V10 exactly.

**CONFIG-ALTERED-DIFF (60-06 + 60-07).** In a scratch repo with a committed blank line and an adjacent edit: `git -c diff.suppressBlankEmpty=true diff <six flags> HEAD -- g.txt | python3 diff_ranges.py` → `{"g.txt": [[14, 14]]}` rc 0 (reads the empty body line as context, no halt). `git -c color.ui=always diff HEAD` (bare, no `--no-color`) → `colored or escaped diff` rc 2 (refuses, does not silently return `{}`). `printf 'fatal: bad revision\n' | diff_ranges.py` → `not a unified diff` rc 2. Matches 60-06-SUMMARY.md / 60-07-SUMMARY.md and 60-REPRO.md V11 exactly.

**GATEFILE-RETRY (60-08).** Read `90-finalize.md`'s rebuild-once paragraph: it now names `GATEFILE=` missing/empty as a trigger, instructs re-running the gate-input fence for a NEW `GATEFILE=`, writing the seven-key flags from the REBUILT `$COUNTS_JSON`, and never reusing an earlier attempt's/session's `GATEFILE=`. `pytest -q test_finalize_card.py` → `89 passed, 132 subtests passed`, 0 failed, run by me just now. Matches 60-08-SUMMARY.md and 60-REPRO.md V12.

### New findings on the fixed code (not covered by any 60-06..60-09 plan)

**CR-01 — command injection via the unvalidated `head_sha` literal substitution (reported in 60-REVIEW.md, commit `cfa473a`; independently reproduced by me).**

```bash
# Exact flagged command from 30-collect-score.md's pass>=2 row, with the
# placeholder filled from an attacker-controlled state-file value:
set -o pipefail
RANGES_JSON=$(git diff --no-color --no-ext-diff --no-textconv --no-relative \
  --src-prefix=a/ --dst-prefix=b/ "$(touch "$T/pwned")HEAD" | python3 diff_ranges.py)
# exit code: 0
# output: {}
# pwned file exists: YES   <-- the injected command ran
```
`05-state.md` step 2 binds `$LAST_REVIEWED_SHA = state.passes[-1].head_sha` straight from the state JSON with no format check, and `30-collect-score.md`'s row has the agent paste that value verbatim into a double-quoted git-diff argument — double quotes block word-splitting, not `$(...)`. I independently confirmed the attack surface is real, not theoretical: `07-first-run.md` only *prints* a tip to add `.turingmind/` to `.gitignore` and never auto-edits it, so a state file (key `<phase-dir-name>.json` in GSD mode, predictable) can be committed to a reviewed repo by a contributor.

**WR-02 — Finalize's post-decision gate re-run can decide on stale, pre-decision flags (reported in 60-REVIEW.md; independently reproduced by me with the real helpers).**

```
Initial counts: 5 1 0
First gate run (pre-decision): {"action": "outstanding-to-phase-5", ...}
Hashes to dismiss: 6
Recomputed counts after decisions: 0 0 0
Second gate run reusing ORIGINAL GATEFILE (stale flags): {"action": "outstanding-to-phase-5", ...}   <-- still blocked
Second gate run with a FRESH GATEFILE (recomputed flags): {"action": "write", ...}                    <-- correct
```
Using the shipped `fixtures/iplayarr45-six-row-state.json`, `carry_state.finalize_counts` and `finalize_gate.py` directly: dismissing every open obligation correctly zeroes the recomputed counts, but re-running the gate against the GATEFILE that was written *before* those decisions (exactly what `90-finalize.md` step 3's literal text instructs — it names reusing `BLOBFILE` explicitly and says nothing about GATEFILE) reproduces the stale "still blocked" outcome every time. Only writing a fresh GATEFILE from the recomputed counts (what the rebuild-once paragraph 15 lines earlier explicitly spells out, but step 3 does not) returns `write`.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/scripts/diff_ranges.py` | Exact-range builder; now also reads `diff.suppressBlankEmpty` context and refuses colored/non-diff text | ✓ VERIFIED | Read in full; `REASON_ESCAPE`, `REASON_NOT_A_DIFF` present; import set still `{json, re, sys}` |
| `plugins/vibe-check/scripts/test_diff_ranges.py` | `TestHazards`, `TestRefusals`, `TestProseRangeFence`, `TestScopePhaseStartFence`, `TestRangeSourceLines`, M20–M22 | ✓ VERIFIED | 100 passed, 75 subtests passed (run by me) |
| `plugins/vibe-check/phases/review/30-collect-score.md` | Literal quoted-sha rows, six fixed flags | ⚠️ PARTIAL | Rows are correct for fresh-shell survival and fixed flags, but the substituted literal is unvalidated — CR-01 |
| `plugins/vibe-check/phases/review/00-scope.md` | Prints `PHASE_START=`; six-flag range-source line | ✓ VERIFIED | `printf 'PHASE_START=%s\n' "$PHASE_START"` present; confirmed by fence read and by direct fresh-shell reproduction |
| `plugins/vibe-check/phases/review/05-state.md` | Six-flag incremental range-source line | ⚠️ PARTIAL | Flags correct; `$LAST_REVIEWED_SHA` binding has no validation before downstream substitution — CR-01 |
| `plugins/vibe-check/phases/shared/90-finalize.md` | Rebuild-once rule re-mints GATEFILE; printed BLOBFILE/GATEFILE fences | ⚠️ PARTIAL | Rebuild-once (failure-retry) path is now correct; the separate post-decision re-run (step 3) is not — WR-02 |
| `plugins/vibe-check/scripts/test_finalize_card.py` | GATEFILE retry walk + needles | ✓ VERIFIED for its own scope | 89 passed, 132 subtests passed; does not cover the step-3 post-decision re-run (WR-02 is outside what any 60-06..09 plan's must-haves asked for) |
| `.planning/phases/.../60-REPRO.md` | V10–V12 ledger, residuals R12-R17 | ✓ VERIFIED (internally consistent) | Matches git history; does not (and could not, since 60-REVIEW.md post-dates it) cover CR-01/WR-02 |
| `.planning/phases/.../60-REVIEW.md` | Gap-round code review | ✓ VERIFIED | Present at commit `cfa473a`; CR-01 and WR-02 independently re-reproduced by me above, not just taken on faith |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `30-collect-score.md` GSD/pass≥2 rows | `scripts/diff_ranges.py` | fresh-shell pipe, literal substituted sha | ✓ WIRED for fresh-shell survival / ✗ UNSAFE for the substituted value | Fresh-shell correctness reproduced; injection also reproduced (CR-01) |
| `00-scope.md` phase-range fence | `30-collect-score.md` GSD row | printed `PHASE_START=` literal | ✓ WIRED | Confirmed by reading and by fresh-shell reproduction |
| `90-finalize.md` rebuild-once paragraph | gate-input fence + `finalize_gate.py` | re-mint GATEFILE, rewrite flags from rebuilt counts | ✓ WIRED (failure-retry path) | Confirmed by reading + green test suite |
| `90-finalize.md` step 3 ("fix empty" branch) | `finalize_gate.py` | re-run the gate | ✗ NOT RE-WIRED (flags never rewritten from the recomputed counts) | WR-02, mechanically reproduced above |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `test_diff_ranges.py` full file | `pytest -q test_diff_ranges.py` | `100 passed, 75 subtests passed` | ✓ PASS |
| `test_finalize_card.py` full file | `pytest -q test_finalize_card.py` | `89 passed, 132 subtests passed` | ✓ PASS |
| GSD route, fresh shell, literal substituted | manual real-git repro | `{"f.txt": [[3, 3], [5, 5]]}` rc 0 | ✓ PASS |
| GSD route, fresh shell, quoted var unsubstituted | manual real-git repro | git exit 128, pipeline halts | ✓ PASS |
| `diff.suppressBlankEmpty=true` ordinary edit | manual real-git repro | `{"g.txt": [[14, 14]]}` rc 0, no halt | ✓ PASS |
| Colored diff, no `--no-color` | manual real-git repro | `colored or escaped diff` rc 2 | ✓ PASS |
| Non-diff text | manual repro | `not a unified diff` rc 2 | ✓ PASS |
| CR-01 injection via quoted literal substitution | manual real-git repro (see above) | exit 0, `{}`, injected file created | ✗ FAIL (vulnerability confirmed) |
| WR-02 stale-GATEFILE post-decision re-run | manual repro with `carry_state.py`/`finalize_gate.py` (see above) | stale GATEFILE → `outstanding-to-phase-5`; fresh GATEFILE from the same recomputed counts → `write` | ✗ FAIL (defect confirmed) |

### Probe Execution

SKIPPED — no `scripts/*/tests/probe-*.sh` convention in this repo and none declared by the Phase 60 PLAN/SUMMARY files; verification used the project's own `pytest` suite and direct reproduction (shown above) instead, per the prior verification's own approach.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| EVID-01 | 60-01, 60-02, 60-04, 60-06, 60-07 | Ranges from added/deleted lines only, boundary-exact, fails closed on hostile-but-legitimate config | ✓ SATISFIED | Truths 1, 4 |
| EVID-02 | 60-01, 60-02 | Correct ranges for ordinary/deletion/insertion/relocated shapes via real git diff | ✓ SATISFIED | Truth 2 |
| EVID-03 | 60-04, 60-07 | Every route uses exact ranges reliably from a fresh Bash call | ✗ BLOCKED | Truth 3; CR-01 |
| FINL-01 | 60-03 | Printed BLOBFILE literal reused; fresh-shell walk reaches write/report | ✓ SATISFIED | Truth 5 |
| FINL-02 | 60-03, 60-05, 60-08 | No-write-on-failure; a later retry/re-run may complete; independent fix verification unchanged | ✗ BLOCKED | Truth 6; WR-02 |

No orphaned requirement IDs: REQUIREMENTS.md maps exactly EVID-01, EVID-02, EVID-03, FINL-01, FINL-02 to Phase 60; all five appear in at least one plan's `requirements:` frontmatter across 60-01 through 60-09.

**On REQUIREMENTS.md's current wording:** it correctly says EVID-03 and FINL-02 are "Gap closure landed... awaiting re-verification" (not Complete) — this re-verification finds that the landed gap closure is real but incomplete: the three originally-identified gaps are genuinely closed, and two new, independently-reproduced defects (one critical) remain in the same mechanisms. EVID-03 and FINL-02 should stay unchecked.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No `TBD`/`FIXME`/`XXX` debt markers in any file touched by 60-06..60-09 (`vc.XXXXXX` mktemp templates are not debt markers) | — | checked directly, none found |
| `plugins/vibe-check/phases/review/05-state.md` / `30-collect-score.md` | step 2 / pass≥2 row | Unvalidated attacker-reachable value substituted into a shell command | 🛑 blocking | CR-01 — command injection, reproduced |
| `plugins/vibe-check/phases/shared/90-finalize.md` | step 3 ("fix empty" branch) | Gate re-run omits the GATEFILE rewrite the analogous rebuild-once paragraph spells out | 🛑 blocking | WR-02 — stale decision, reproduced |
| `plugins/vibe-check/phases/review/30-collect-score.md` | `diff.submodule` not neutralized | WR-01 (60-REVIEW.md, carried) | warning (not independently re-opened here; outside this verification's assigned scope) | false refusal / silent range loss on submodule-only or mixed changes |
| `plugins/vibe-check/phases/shared/90-finalize.md` | temp files never `rm -f`'d | WR-03 (60-REVIEW.md, carried as R12) | info/minor | resource hygiene, not a functional break |

### Human Verification Required

### 1. Write-tool refusal risk on freshly-minted temp files (SA-01, carried as R16)

**Test:** Run a live `--finalize` in Claude Code and observe whether the Write tool accepts the first write to the path printed after `BLOBFILE=`/`GATEFILE=` (a file `mktemp` just created but the agent never `Read`).
**Expected:** The write succeeds (consistent with the pre-existing ROWSFILE/SUGGESTFILE/REFSFILE pattern), or — if refused — every `--finalize` attempt and its one retry both fail at the same step.
**Why human:** Harness Write-tool behavior cannot be exercised from a pytest fixture.

### 2. PR size-limit fallback decision (SA-02, carried as R17)

**Test:** None — this is a scope/product decision.
**Expected:** An explicit owner ruling on whether `gh pr diff` failing closed on very large PRs (~300+ files / 20k+ lines) is an accepted limit or needs a fallback.
**Why human:** Not a code defect; the reviewer calls the current fail-closed behavior intended.

### Gaps Summary

The gap-closure round did what it set out to do: all three gaps from the prior verification (`2f84d2e`) are genuinely fixed, and I independently re-reproduced each one's closure rather than trusting the SUMMARYs — the GSD/incremental fresh-shell range source is now correct and fails closed on an unsubstituted variable, the range builder now reads `diff.suppressBlankEmpty` context and refuses colored/non-diff text instead of silently emptying, and Finalize's one-rebuild retry now recovers from a GATEFILE-specific failure. The full targeted test suites (`test_diff_ranges.py`, `test_finalize_card.py`) are green with no regressions.

However, this phase cannot close yet. The gap round's own code review (`60-REVIEW.md`, committed at `cfa473a` — the current HEAD, after all gap-closure work) found two further problems in the exact mechanisms the gap round touched, and I independently reproduced both with working exploits/scripts, not just by reading the review's prose:

1. **CR-01 (critical).** The literal-substitution fix that closed GSD-SHELL-VAR introduced a command-injection path: an unvalidated `head_sha` from the (not-necessarily-gitignored) state file, substituted into a double-quoted git-diff argument, runs arbitrary shell commands via `$(...)`. I reproduced this with a working exploit (a `touch` payload that executed and left its marker file, with the overall command still exiting 0). This is a regression introduced by this phase's own 60-07 fix, not a pre-existing residual, and it directly contradicts the plan's own threat model, which claimed (incorrectly) that quoting already prevented this.
2. **WR-02.** Finalize's post-decision gate re-run (a different code path from the one 60-08 fixed) can decide on stale, pre-decision GATEFILE flags, because the "fix empty" branch's text never says to rewrite GATEFILE from the recomputed counts — unlike the rebuild-once paragraph 15 lines above it, which spells this out in full. I reproduced the consequence mechanically with the real helpers: dismissing every open obligation correctly zeroes the recomputed counts, but the gate re-run against the stale file still reports "stays blocked." This breaks the file's own "Finalize costs one card" promise on the ordinary card-answer path, not just on a failure-retry.

Both are concrete, reproduced, and fixable with a scoped follow-up (closing the same way 60-06/07/08 closed the first three): validate `head_sha`/`<phase-start-sha>` at the point of binding before any substitution (CR-01's own suggested fix), and extend step 3's "fix empty" branch to rewrite GATEFILE from the recomputed counts before re-running the gate, with a fresh-shell test that proves it (mirroring 60-08's own pattern for the rebuild-once paragraph).

**Recommendation:** route to a follow-up gap-closure plan before closing EVID-03/FINL-02 as Complete. These are not candidates for a waiver/override — CR-01 is a working remote-code-execution path in a review tool that processes untrusted repository content, and WR-02 breaks the core "Finalize completes" promise on an ordinary, non-adversarial usage path.

---

_Verified: 2026-10-29_
_Verifier: Claude (bm-verifier)_
