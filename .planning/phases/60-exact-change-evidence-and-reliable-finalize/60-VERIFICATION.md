---
phase: 60-exact-change-evidence-and-reliable-finalize
verified: 2026-10-30T20:40:00Z
status: human_needed
score: 6/6 must-haves verified
has_blocking_gaps: false
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "A failed or refused Finalize attempt stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness (FINL-02) — both third-round regressions closed and independently re-reproduced below: WR-01 (step 3's post-decision recount now re-fingerprints HEAD into a NEW BLOBFILE instead of reusing the pre-card snapshot, fixed by 60-14) and WR-02 (the head_sha bind fence now skips on the printed FINALIZE_MODE=1 literal instead of wedging --finalize, fixed by 60-15)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Confirm whether Claude Code's Write tool refuses the first write to a path that `mktemp` just created but the agent never Read (SA-01, carried as R16 in 60-REPRO.md)"
    expected: "Either the Write succeeds (the existing ROWSFILE/SUGGESTFILE/REFSFILE pattern already relies on this), or it is refused and every --finalize attempt (and its one retry) fails at the BLOBFILE/GATEFILE write step"
    why_human: "Depends on live Claude Code harness Write-tool behavior that cannot be exercised from a pytest fixture"
  - test: "Decide whether the PR route's hard failure on very large PRs (SA-02: gh pr diff over ~300 files / 20k lines) needs a fallback or is an accepted limit"
    expected: "An owner ruling, not a reproduction — the reviewer notes failing closed is the intended behavior here"
    why_human: "Product/scope decision, not a code defect"
  - test: "Rule on 60-REVIEW.md's second-round SA-01 (distinct from the item above): is a state file's head_sha trusted to scope the incremental range (accept), or should scope binding be hardened against a crafted-but-well-formed 40/64-hex head_sha that narrows what gets reviewed (defer as a hardening item)?"
    expected: "An explicit owner ruling. CR-01's fix (format validation) closes the command-injection path but does not address whether a committed state file should be allowed to narrow review scope at all."
    why_human: "Product/scope/trust-boundary decision, not a code defect — the reviewer explicitly set this aside pending a ruling"
---

# Phase 60: Exact change evidence and reliable Finalize Verification Report

**Phase Goal:** The nearby window is exactly what the decision rules say on every review route, and Finalize either completes from a fresh shell or stops safely without writing (999.24, 999.25)
**Verified:** 2026-10-30
**Status:** human_needed
**Re-verification:** Yes — after the THIRD gap-closure round (plans 60-14, 60-15, 60-16), re-verifying against the 2 blocking gaps found at the prior re-verification (`2de0fc9`), plus the third round's own code review (`60-REVIEW.md`, commit `af37636`)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1/EVID-01 core: ranges are built only from a hunk's `+`/`-` body markers, not display context | ✓ VERIFIED (regression-checked) | Untouched by this round. Full-suite run at `af37636` (below) includes `test_diff_ranges.py` green with 0 failures |
| 2 | SC2/EVID-02: fixtures that run a real `git diff` produce correct ranges for ordinary, deletion-only, insertion and relocated-finding shapes | ✓ VERIFIED (regression-checked) | Same, unaffected by this round |
| 3 | SC3/EVID-03: every route reliably uses the exact-range builder from a genuinely fresh Bash call, including the value substituted into it | ✓ VERIFIED | Unchanged from the prior re-verification (CR-01 closed). The round-3 review's new finding (its own "WR-01") concerns Finalize's interaction with 05-state.md step 3, not a review-route range-builder defect — it does not touch this truth (see "New findings" below) |
| 4 | Range mechanism fails closed (halts, never silently empties) when the diff text is altered by a legitimate repo-local git setting (T-60-13) | ✓ VERIFIED (regression-checked) | Unaffected by this round; green in the full-suite run |
| 5 | SC4/FINL-01: a fresh-shell walk through every Finalize fence reaches counts → gate → report using the printed, literally reused `BLOBFILE=` path | ✓ VERIFIED (regression-checked) | Unaffected by this round; `test_finalize_card.py` green in the full-suite run |
| 6 | SC5/FINL-02: a failed or refused attempt stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness | ✓ VERIFIED | Both gaps from the prior re-verification are closed and independently re-reproduced below with working code, not SUMMARY prose: WR-01 (stale pre-card BLOBFILE) by 60-14, WR-02 (head_sha bind fence wedge) by 60-15. See "Independent re-reproduction" below. |

**Score:** 6/6 truths verified (up from 5/6 at the prior re-verification; both third-round gaps — the stale BLOBFILE recount and the head_sha finalize-wedge — are genuinely closed)

### Independent re-reproduction of the two third-round gaps (both CLOSED)

**WR-01 — step-3 stale BLOBFILE recount (60-14).** I built a scratch state file from the real `fixtures/iplayarr45-six-row-state.json` (confirmed: last pass `pass_number == 3`; exactly one finding with `stable_hash` `22d360d9…` has `band == "critical"` and `file == "src/utils/integrationDeadline.ts"`; no pre-existing `fix_verdicts` key), added a pass-3 `fix_verdicts` "obsolete" entry for that hash with `verified_blob: "blob-pre-card"`, and ran the REAL `carry_state.py finalize-counts --head-blobs` CLI directly (not the test file's internals):

```
step1 (pre-card) blob={"...":"blob-pre-card"}:
  outstanding_cw=4, verified_obsolete_hashes=["22d360d9…"]   (verdict honoured, matches blob)
step3-OLD-BEHAVIOR: reuse the SAME stale blob after the real file changed:
  outstanding_cw=4, verified_obsolete_hashes=["22d360d9…"]   (still honoured — WRONG: the real file changed, this snapshot never saw it)
step3-NEW-BEHAVIOR (60-14 fix): re-mint BLOBFILE, re-fingerprint the now-changed file ("blob-post-card"):
  outstanding_cw=5, verified_obsolete_hashes=[]              (correctly REOPENED)
```

This reproduces the exact causal mechanism WR-01 named: a stale pre-card blob snapshot lets a fix-obsolete verdict survive a real edit made during the card-answer wait; re-fingerprinting HEAD (what 90-finalize.md step 3 now says to do) catches it. I also confirmed the prose directly: `grep -c "the fingerprints have not changed" 90-finalize.md` → 0; `grep -cF 'BLOBFILE=$(mktemp'` → 1 and `grep -cF 'GATEFILE=$(mktemp'` → 1 (no duplicate fence was added — step 3 re-runs step 1's existing fence, as the plan required). Ran the plan's own test classes fresh: `pytest -q test_finalize_card.py -k "step3 or post_decision or refingerprint"` → `6 passed, 89 deselected, 14 subtests passed`, 0 failed. Matches 60-14-SUMMARY.md.

**WR-02 — head_sha bind fence wedges `--finalize` (60-15).** I ran the EXACT fence text from 05-state.md step 2 in a genuinely fresh `bash -s`, with the state file's last-pass `head_sha` set to the literal `HEAD` (a plausible unvalidated write by 45-persist.md) and `FINALIZE_MODE` substituted as the literal `"1"` (simulating Phase 0's printed value):

```
FINALIZE_MODE substituted as literal 1
rc_after_step2=0
(fence printed nothing to stdout or stderr — the skip branch ran)
```

Then I ran 90-finalize.md's REAL counts fence (`carry_state.py finalize-counts --head-blobs`) on the SAME state file, fresh:

```
{"outstanding_cw": 5, "unacknowledged_medium": 1, "undecided_nv": 0, ...}
```

This directly confirms: a state file whose `head_sha` would have halted every `--finalize` before this fix now lets Finalize reach its own counts step and complete, without the bind fence ever consuming (or needing) `$LAST_REVIEWED_SHA`. Ran the plan's own test classes fresh: `pytest -q test_diff_ranges.py -k "StateHeadSha or SubstitutedValue"` → `16 passed, 105 deselected, 17 subtests passed`, 0 failed. Matches 60-15-SUMMARY.md.

**Ledger and record.** `pytest -q test_decision_continuity.py -k TestRepro60Record` → `3 passed, 155 deselected, 67 subtests passed` (REPRO_60 at 16 rows, both new rows resolve through `_suite_defines`). `git diff --stat 2de0fc9 HEAD -- plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/finalize_gate.py plugins/vibe-check/scripts/carry_state.py` is empty — no production helper changed this round, only the two prose files and three test files, confirmed by `git diff --stat 2de0fc9 HEAD -- plugins/` (exactly `05-state.md`, `90-finalize.md`, `test_decision_continuity.py`, `test_diff_ranges.py`, `test_finalize_card.py`). Full offline suite, run by me from `plugins/vibe-check/scripts`: `pytest -q -p no:cacheprovider` → `3821 passed, 5039 subtests passed in 170.92s`, 0 failed — matches the orchestrator's own close-of-round run cited in 60-16-SUMMARY.md (`3821 passed, 5039 subtests passed in 174.64s`).

### Independent assessment of the fresh round-3 code review's new WR-01 (its own numbering — distinct from the now-closed WR-01 above)

The round-3 code review (`60-REVIEW.md`, commit `af37636`, reviewed AFTER 60-16 landed) found a new WARNING: the 60-15 fix makes 05-state.md step 2 print no `LAST_REVIEWED_SHA=` line on `FINALIZE_MODE=1`, but step 3 ("Narrow diff to incremental … substitute [the literal printed after `LAST_REVIEWED_SHA=`]") has no explicit `FINALIZE_MODE=1` exemption of its own, unlike step 2 and step 4. The review asks: does a live `--finalize` run actually reach step 3 and get stuck, or is step 3 already unreachable/irrelevant on finalize?

**I independently reproduced the REAL, reachable path and refute the blocking interpretation:**
1. `90-finalize.md`'s own "Finalize mode" section — the file Finalize actually reads, right after Phase 0.5 — states exactly what it needs from Phase 0.5 in finalize mode: "Run Phase 0 and 0.5 to resolve scope and read state… Phase 0.5 binds `$STATE_FILE`… Finalize consumes that one variable." It never mentions step 3's incremental diff.
2. Step 3's own text names its consumer explicitly: "Range source **for 30-collect-score**." `30-collect-score.md` is Phase 3 (confirmed: `commands/review.md`/`deep-review.md`'s phase table lists `30-collect-score.md` as `3`), and BOTH command spines explicitly exclude Phase 3 from the finalize flow ("Do NOT run Phases 0.2, 0.3, 0.7, 1, 1.5, 2, **3**, 4 or 4.5"). Step 3's sole downstream consumer never runs on `--finalize`.
3. I ran the actual reachable path fresh, end to end, with the SAME hostile input (`head_sha: "HEAD"`, `FINALIZE_MODE=1`): step 2's fence exits 0 printing nothing (confirmed above), and 90-finalize.md's step 1 → counts fence runs immediately after and returns real counts — `{"outstanding_cw": 5, ...}` — without step 3 of 05-state.md ever being invoked. Nothing stops, nothing is stuck, nothing is misled.

Per the owner's scope rule (new work only for a *reproduced* mandatory-gate failure, data loss, silent finding loss, or broken required workflow), I could not reproduce a failure here — the opposite: I reproduced that Finalize completes cleanly along the path its own governing files describe. I therefore agree with the reviewer's own WARNING (not BLOCKER) grade, but go further: the "ambiguity" is in a paragraph of 05-state.md that a `--finalize` run never has reason to execute, given the command spine's Phase-3 exclusion and 90-finalize.md's self-contained recap. This is a real prose clarity gap worth a cheap one-line fix (mirroring step 2/step 4's explicit `FINALIZE_MODE=1` language) in a future housekeeping pass, but it is not a blocking defect against FINL-02 and does not reopen truth 6. The review's other three findings (IN-01: the halt remedy's "restore from git" clause is misleading when `.turingmind/` is gitignored per convention; IN-02: a Finalize-routed fix-loop Rerun could theoretically carry a stale `FINALIZE_MODE=1` literal into a genuine review pass; IN-03: the new walk test proves the helper, not literally a live agent's HEAD re-fingerprint) are all graded Info by the reviewer, and I independently agree none meet the reproduced-failure bar — they are legitimate carries for the ledger, not gaps.

**Recommendation for the next housekeeping touch (non-blocking):** add one sentence to 05-state.md step 3 exempting `FINALIZE_MODE=1` (as the review's suggested fix shows), add the `.turingmind/`-is-gitignored caveat to the halt remedy, and tie `FINALIZE_MODE` substitution in step 2 explicitly to "this pass's" printed literal. None of this blocks the phase goal.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/phases/shared/90-finalize.md` | step 3 re-fingerprints HEAD into a NEW BLOBFILE before the post-answer recount (not a stale reuse) | ✓ VERIFIED | Read in full; `grep -c "the fingerprints have not changed"` → 0; the step-3 line now says "run step 1 again — a new mktemp fence printing a NEW `BLOBFILE=`, with the fingerprints rebuilt from the current HEAD, index and working tree… RE-RUN the counts step ONCE with that NEW `BLOBFILE=` literal"; exactly 1 BLOBFILE mktemp fence and 1 GATEFILE mktemp fence (no duplicate) |
| `plugins/vibe-check/scripts/test_finalize_card.py` | `test_post_decision_recount_refingerprints_head`, `test_mutant_step3_reinserts_stale_fingerprint_claim`, 8 `STEP3_NEEDLES` | ✓ VERIFIED | Present; `pytest -q -k "step3 or post_decision or refingerprint"` → 6 passed, 14 subtests, 0 failed (run by me) |
| `plugins/vibe-check/phases/review/05-state.md` | step-2 fence skips the `last-head-sha` validation on `FINALIZE_MODE=1`; halt line names a remedy | ✓ VERIFIED | Read in full; `grep -c 'if \[ "\$FINALIZE_MODE" = "1" \]'` → 1; `grep -c "restore the state file from git"` → 1; `grep -c 'A \`FINALIZE_MODE=1\` run skips this binding'` → 1; fresh-shell repro above confirms behavior (skip prints nothing, rc 0) |
| `plugins/vibe-check/scripts/test_diff_ranges.py` | `TestStateHeadShaFence` finalize-mode tests, `test_halt_names_a_remedy`, mutants for the new needles | ✓ VERIFIED | Present; `pytest -q -k "StateHeadSha or SubstitutedValue"` → 16 passed, 17 subtests, 0 failed (run by me) |
| `plugins/vibe-check/scripts/test_decision_continuity.py` | `REPRO_60` at 16 rows (STALE-BLOBFILE-RECOUNT, FINALIZE-HEAD-SHA-WEDGE); `TestRepro60Record` locks 16 | ✓ VERIFIED | `pytest -q -k TestRepro60Record` → 3 passed, 67 subtests, 0 failed (run by me); `len(REPRO_60) == 16` confirmed via the SUMMARY's python check, re-derivable from the test module |
| `.planning/phases/.../60-REPRO.md` | Third gap-round section with V15/V16, red/green table, reverse run at `2de0fc9`, suite at close, R22-R26 | ✓ VERIFIED (internally consistent and checked against git) | Read in full; `git cat-file -e` checked on the cited SHAs (7796476, 9b3f055, 3c7814e, 07bb448, 2de0fc9, c112ca6 all resolve — spot-checked below); residuals R22-R26 present and match 60-REVIEW.md's "Carried" section verbatim in substance |
| `.planning/phases/.../60-REVIEW.md` | Fresh third-round code review | ✓ VERIFIED | Present at `af37636`; 0 critical, 1 warning, 3 info; the warning independently assessed above (non-blocking) |
| `.planning/REQUIREMENTS.md` | EVID-03 Complete; FINL-02 traceability row cites third round, stays "awaiting re-verification" (this verification now settles it) | ✓ VERIFIED | `[x] EVID-03` with the 2026-10-30 citation; `[ ] FINL-02` row cites 60-14/60-15 GREEN SHAs and says "awaiting re-verification" — this verification supplies that re-verification and FINDS FINL-02 now holds (see Requirements Coverage below) |
| `.planning/ROADMAP.md` | Phase 60 plans 16/16, third-round sub-heading checked, 999.24/999.25 paragraphs updated | ✓ VERIFIED | `**Plans:** 16/16 plans executed`; all `60-14`/`60-15`/`60-16` entries checked; 999.25 paragraph names V15/V16 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `90-finalize.md` step 3 ("fix empty") | `90-finalize.md` step 1 (HEAD fingerprints) | "run step 1 again — a new mktemp fence printing a NEW `BLOBFILE=`" | ✓ WIRED | Fresh CLI repro above: stale blob wrongly honours a fix-obsolete verdict over an edited file; re-minted blob correctly reopens it |
| `05-state.md` step-2 fence | `carry_state.py last-head-sha` | `elif LAST_REVIEWED_SHA=$(... last-head-sha ...)` — now gated by `if [ "$FINALIZE_MODE" = "1" ]` | ✓ WIRED (both modes) | Fresh-shell repro: `FINALIZE_MODE=1` → skip, rc 0, nothing printed; `0`/unsubstituted → validates as before (review-mode CR-01 protection intact) |
| `05-state.md` step 2 | `90-finalize.md` entry (counts fence) | FINALIZE_MODE=1 skip → Finalize proceeds without `$LAST_REVIEWED_SHA` | ✓ WIRED | Fresh-shell repro: the real counts fence runs immediately after the skip and returns real counts on a state file whose `head_sha` would have halted the run before 60-15 |
| `05-state.md` step 3 (incremental diff) | `30-collect-score.md` (Phase 3) | "Range source for 30-collect-score" | ✓ CONFIRMED UNREACHABLE ON FINALIZE | Phase 3 is explicitly excluded from the finalize flow by both command spines; step 3's sole consumer never runs on `--finalize` — the round-3 review's new WARNING is about unclear prose in a branch that is never actually exercised by Finalize, not a broken link |

### Data-Flow Trace (Level 4)

Not applicable in the dynamic-rendering sense (this phase changes prose procedures and their test harnesses, not a UI/data-rendering component). The equivalent trace — does the fixed prose's literal reuse rule actually feed real recomputed counts into the gate, rather than a static/stale value — is covered above (WR-01/WR-02 fresh-shell reproductions) and is FLOWING in both cases: the post-fix path recomputes from a freshly re-fingerprinted BLOBFILE and reaches `finalize_gate.py` with those real counts.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| WR-01 fix: stale vs. fresh BLOBFILE against the real `carry_state.py` CLI (not a mock) | manual repro (shown above) | stale reuse → verdict wrongly honoured (`outstanding_cw` unchanged, verdict closed); fresh re-mint → correctly reopened | ✓ PASS |
| WR-02 fix: `head_sha: "HEAD"` + `FINALIZE_MODE=1`, genuinely fresh `bash -s`, real 05-state.md fence text | manual repro (shown above) | rc 0, nothing printed, no halt | ✓ PASS |
| WR-02 fix reaches Finalize's real counts step | manual repro (shown above), `carry_state.py finalize-counts` | `{"outstanding_cw": 5, "unacknowledged_medium": 1, "undecided_nv": 0, ...}` | ✓ PASS |
| `test_finalize_card.py` WR-01 classes | `pytest -q test_finalize_card.py -k "step3 or post_decision or refingerprint"` | `6 passed, 89 deselected, 14 subtests passed` | ✓ PASS |
| `test_diff_ranges.py` WR-02 classes | `pytest -q test_diff_ranges.py -k "StateHeadSha or SubstitutedValue"` | `16 passed, 105 deselected, 17 subtests passed` | ✓ PASS |
| `test_decision_continuity.py` ledger lock | `pytest -q test_decision_continuity.py -k TestRepro60Record` | `3 passed, 155 deselected, 67 subtests passed` | ✓ PASS |
| No production helper changed this round | `git diff --stat 2de0fc9 HEAD -- replay.py score.py finalize_gate.py carry_state.py` | empty | ✓ PASS |
| `plugins/` diff-stat matches the claimed 5 files | `git diff --stat 2de0fc9 HEAD -- plugins/` | `05-state.md, 90-finalize.md, test_decision_continuity.py, test_diff_ranges.py, test_finalize_card.py` | ✓ PASS |
| Full offline suite at `af37636` | `pytest -q -p no:cacheprovider` (plugins/vibe-check/scripts) | `3821 passed, 5039 subtests passed in 170.92s`, 0 failed (run by me, once) | ✓ PASS |
| Round-3 review's new WR-01: does `--finalize` actually reach/get stuck at 05-state.md step 3? | fresh-shell repro of the REAL reachable path (step 2 skip → 90-finalize.md step 1/counts) | step 3 never invoked; counts fence returns real data | ✓ PASS (refutes the blocking interpretation) |

### Probe Execution

SKIPPED — no `scripts/*/tests/probe-*.sh` convention in this repo and none declared by the Phase 60 PLAN/SUMMARY files; verification used the project's own `pytest` suite and direct fresh-shell/CLI reproduction instead, consistent with the prior verifications' approach.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| EVID-01 | 60-01, 60-02, 60-04, 60-06, 60-07 | Ranges from added/deleted lines only, boundary-exact, fails closed on hostile-but-legitimate config | ✓ SATISFIED | Truths 1, 4 (regression-checked; unaffected by this round) |
| EVID-02 | 60-01, 60-02 | Correct ranges for ordinary/deletion/insertion/relocated shapes via real git diff | ✓ SATISFIED | Truth 2 (regression-checked) |
| EVID-03 | 60-04, 60-07, 60-10, 60-11 | Every route uses exact ranges reliably from a fresh Bash call, with no way to subvert the substituted value | ✓ SATISFIED | Truth 3; already marked Complete in REQUIREMENTS.md citing the prior re-verification, reconfirmed here |
| FINL-01 | 60-03 | Printed BLOBFILE literal reused; fresh-shell walk reaches write/report | ✓ SATISFIED | Truth 5 (regression-checked) |
| FINL-02 | 60-03, 60-05, 60-08, 60-12, 60-14, 60-15 | No-write-on-failure; a later retry/re-run may complete; revalidates freshness | ✓ SATISFIED | Truth 6; both third-round regressions (WR-01, WR-02) independently re-reproduced as closed above. **This verification finds FINL-02 now holds and may be marked Complete in REQUIREMENTS.md.** |

No orphaned requirement IDs: REQUIREMENTS.md maps exactly EVID-01, EVID-02, EVID-03, FINL-01, FINL-02 to Phase 60; all five appear in at least one plan's `requirements:` frontmatter across 60-01 through 60-16.

**On REQUIREMENTS.md's current wording:** it correctly leaves FINL-02 unchecked, noting "third round 60-14, 60-15 … awaiting re-verification." This re-verification supplies that re-verification and finds FINL-02 satisfied: both regressions the prior re-verification found blocking are closed, independently reproduced against real code (not SUMMARY prose), the full offline suite is green (3821 passed, 0 failed), and no production helper changed. FINL-02 can now move to Complete.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No `TBD`/`FIXME`/`XXX` debt markers in any file touched by 60-14..60-16 (`vc.XXXXXX` mktemp templates are not debt markers; ROADMAP.md's `TBD` hits are for the unrelated, not-yet-started Phase 61) | — | checked directly, none found |
| `plugins/vibe-check/phases/review/05-state.md` | step 3 ("Narrow diff to incremental") | New this round (60-REVIEW.md WR-01, `af37636`): no explicit `FINALIZE_MODE=1` exemption, unlike step 2 and step 4 | ⚠️ warning (non-blocking) | Independently assessed above: step 3's only consumer (`30-collect-score.md`/Phase 3) never runs on `--finalize`, and 90-finalize.md's own recap of what it needs from Phase 0.5 never calls for it. Fresh-shell repro of the real reachable path shows no stuck/misled state. Recommend a cheap follow-up (one sentence, mirroring step 2/4's style) but not a phase-blocking gap |
| `plugins/vibe-check/phases/review/05-state.md` | halt remedy line (`IN-01` in 60-REVIEW.md) | "restore the state file from git" is misleading when `.turingmind/` is gitignored per the project's own first-run guidance | ℹ️ info | Carried; the primary remedy (hand-set `head_sha` to `git rev-parse <sha>`) remains valid regardless |
| `plugins/vibe-check/phases/review/05-state.md` | `"$FINALIZE_MODE"` substitution (`IN-02` in 60-REVIEW.md) | A Finalize-routed fix-loop Rerun could theoretically carry a stale `FINALIZE_MODE=1` literal into a genuine review pass that does need the diff | ℹ️ info | Carried; same risk class as every other printed-literal rule in this file; fails closed on empty/unsubstituted, so the risk is narrow |
| `plugins/vibe-check/scripts/test_finalize_card.py` | `test_post_decision_recount_refingerprints_head` (`IN-03` in 60-REVIEW.md) | Proves the `finalize_counts` helper's behavior on hand-written blob maps, not literally a live agent's `git rev-parse`/`git diff --quiet` re-fingerprint | ℹ️ info | Carried; the reviewer notes "Fix: None required for this round" |
| `plugins/vibe-check/phases/review/05-state.md` / `carry_state.py` | `SA-01` (second round) | A well-formed 40/64-hex `head_sha` committed into the reviewed repo can still narrow the incremental range | — (owner ruling) | Carried in Human Verification below; not a code defect |
| `plugins/vibe-check/phases/review/30-collect-score.md` | `diff.submodule` not neutralized (60-REPRO.md R18, carried) | not independently re-opened here; outside this verification's assigned scope | warning | false refusal / silent range loss on submodule-only or mixed changes |
| `plugins/vibe-check/phases/shared/90-finalize.md` | temp files never `rm -f`'d (60-REPRO.md R12, carried) | not independently re-opened here | info/minor | resource hygiene, not a functional break |

### Human Verification Required

### 1. Write-tool refusal risk on freshly-minted temp files (SA-01, carried as R16)

**Test:** Run a live `--finalize` in Claude Code and observe whether the Write tool accepts the first write to the path printed after `BLOBFILE=`/`GATEFILE=` (a file `mktemp` just created but the agent never `Read`).
**Expected:** The write succeeds (consistent with the pre-existing ROWSFILE/SUGGESTFILE/REFSFILE pattern), or — if refused — every `--finalize` attempt and its one retry both fail at the same step.
**Why human:** Harness Write-tool behavior cannot be exercised from a pytest fixture. Now that both third-round regressions are closed, this is the main remaining way `--finalize` could still fail in a live session — worth checking in the same pass as the owner's next live run.

### 2. PR size-limit fallback decision (SA-02, carried as R17)

**Test:** None — this is a scope/product decision.
**Expected:** An explicit owner ruling on whether `gh pr diff` failing closed on very large PRs (~300+ files / 20k+ lines) is an accepted limit or needs a fallback.
**Why human:** Not a code defect; the reviewer calls the current fail-closed behavior intended.

### 3. State-file `head_sha` trust boundary for scope (60-REVIEW.md second-round SA-01, carried as R25)

**Test:** None — this is a scope/product/trust-boundary decision.
**Expected:** An explicit owner ruling: is a committed state file's `head_sha` trusted to scope the incremental range (accept the status quo), or should scope binding be hardened against a well-formed-but-crafted value that narrows review coverage without telling the owner (plan as a hardening item)?
**Why human:** CR-01's fix closes the command-injection path but does not, and was not meant to, settle this separate trust question; the reviewer explicitly set it aside pending a ruling.

### Gaps Summary

No gaps remain. The third gap round closed both blocking defects the prior re-verification found:

1. **WR-01 (closed by 60-14).** Step 3's post-decision recount now re-fingerprints HEAD into a NEW `BLOBFILE=` before recounting, instead of reusing the pre-card snapshot. I independently reproduced the mechanism against the real `carry_state.py` CLI: a stale blob wrongly keeps a fix-obsolete verdict honoured after a real edit; a freshly re-minted blob correctly reopens it.
2. **WR-02 (closed by 60-15).** The `head_sha` bind fence now skips validation on the printed `FINALIZE_MODE=1` literal. I independently reproduced this in a genuinely fresh `bash -s`: a state file with `head_sha: "HEAD"` (which would have halted every `--finalize` before this fix) now lets the run reach and complete the real counts fence, while review mode (`0`/unsubstituted) still validates and refuses the CR-01 payload exactly as before.

The fresh round-3 code review (`60-REVIEW.md`, `af37636`) surfaced one new WARNING and three new INFO items, all found in the exact mechanisms this round touched. I independently assessed the WARNING (step 3 of 05-state.md has no explicit `FINALIZE_MODE=1` exemption) rather than taking either the review's or the SUMMARYs' word for it: I traced that step 3's only consumer (Phase 3 / `30-collect-score.md`) is explicitly excluded from the finalize flow by both command spines, that `90-finalize.md`'s own self-contained "Finalize mode" section never calls for step 3's output, and I reproduced the actual reachable path end to end in a fresh shell — it never touches step 3 and completes cleanly. Per the owner's scope rule (new work only for a reproduced mandatory-gate failure, data loss, silent finding loss, or broken required workflow), this does not qualify: it is a legitimate prose-clarity residual, not a blocker, and I agree with the reviewer's own WARNING-not-BLOCKER grade. The three INFO items are test-coverage/wording nits already correctly graded non-blocking by the reviewer.

**Recommendation:** The phase goal is achieved. EVID-03 and FINL-02 can both be recorded Complete in REQUIREMENTS.md. The round-3 review's new findings (its WR-01, IN-01, IN-02, IN-03) should be added to 60-REPRO.md's residuals (e.g., R27-R30) by whatever plan or close-out touches that file next — they do not require a fourth gap-closure round. Three human-verification items remain open (Write-tool refusal, PR size-limit ruling, head_sha scope-trust ruling) and are carried forward unchanged; none block the phase goal, which is a code-level claim these items do not contradict.

---

_Verified: 2026-10-30_
_Verifier: Claude (bm-verifier)_
