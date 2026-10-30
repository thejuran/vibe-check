---
phase: 61-release-gate-decision-reliability
verified: 2026-10-30T23:10:00Z
status: passed
score: 10/10 must-haves verified (1 warning needs an owner decision)
has_blocking_gaps: false
overrides_applied: 0
human_verification:
  - test: "Re-confirm Decision 1 (option A) against the corrected framing: the README is not silent on C1. It makes positive claims that C1 contradicts for uncommitted code. README:38 (v2.13 'Your decisions stick ... when you edit unrelated code', still a live claim) and README:33 (default route uses the exact five-line window), and the 'Known limitations (2.14)' list (README:350-358) omits C1."
    expected: "Owner says either 'A stands' (ship README unchanged; C1 disclosed in the release notes, first bullet, and 999.28), or picks B (one-clause README edit, new candidate, re-run G1-G9, re-sign)."
    why_human: "Product/disclosure decision. The sign-off page described option A as 'the README stays silent on it', but 61-RELEASE-RECORD.md §Carried C1 and 61-REVIEW.md WR-01 both record that the README contradicts it. The waiver was granted on the softer description. Only the owner can say whether that changes the ruling."
---

# Phase 61: Release gate — decision reliability. Verification report

**Phase goal:** The release candidate is proven against the accepted scope with nothing unrelated changed, its limits are stated plainly, and it ships through the existing close workflow without waiting for Lean orchestration.
**Verified:** 2026-10-30T23:10:00Z
**Status:** human_needed
**Re-verification:** No. This is the initial verification.

## Goal achievement

### Observable truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: on candidate C, the targeted real-chain regressions, the full offline suite and the mode/recovery checks pass (GATE-01) | VERIFIED | 61-RELEASE-RECORD.md G1 3821 passed / G2 193 / G3 520, 0 failed, raw tails recorded against `0d2be77`. HEAD equals C outside `.planning`, so the results apply. Own spot-checks on HEAD: `test_recovery_pairs.py test_gitguard.py` gave 185 passed, 708 subtests. `test_diff_ranges.py -k "TestRouteDefault or TestRouteRange or TestRoutePR"` gave 10 passed. Full suite not re-run (per instruction). |
| 2 | SC2: archived replay differs only in named, expected repairs. Any unrelated change in detection, filtering or closure blocks (GATE-02) | VERIFIED | G5a: 170 runs vs `rev:v2.13`, 0 differing, no `--allow`. That is stricter than the SC, which would have allowed named differences. G5b: REGRESSED 0. Own re-runs: `replay.py check-manifest` exit 0. `git diff --stat v2.13 0d2be77 -- replay.py test_replay.py` is empty (G9). |
| 3 | Nothing unrelated changed | VERIFIED | `git diff --stat 0d2be77^ 0d2be77` shows only `README.md` and `plugin.json`. `git diff --stat 0d2be77 HEAD -- . ':(exclude).planning'` is empty. All 18 commits after C are `docs(61…)`. `git diff --stat origin/main 0d2be77 -- plugins README.md` shows the same two files only. `origin/main` is an ancestor of HEAD, so a squash merge ships exactly C's tree. `git status --porcelain -- plugins README.md` is clean. |
| 4 | Version and README match the candidate | VERIFIED | `plugin.json:4` reads `"version": "2.14.0"`. README:30 has "v2.14 (this release)" and "3,821 passing at release", which equals G1. 61-CANDIDATE.md has a 22-row fact-check table with an evidence pointer per claim. |
| 5 | SC3a: the release record states unsupported fixtures, residuals and validation gaps explicitly (GATE-03) | VERIFIED | 61-RELEASE-RECORD.md has §Unsupported fixtures and stated limits (9 items incl. C1), §Residuals (34 items linked: 59 R1-R8, 60 R1-R26), §Carried C1-C5 each with a reopen trigger, §Validation gaps and waivers (6 items, each "waiver: granted (owner, 2026-10-30)"), and the D-11 route map with the thin spots named (range, pause/resume). |
| 6 | SC3b: live checks ran only under an approved bounded proposal. Gaps are documented with an owner waiver. | VERIFIED | 61-LIVE-SMOKE-PROPOSAL.md:3 `Status: APPROVED (owner, 2026-10-30)`. 61-LIVE-SMOKE.md `## Verdict` PASS with caveat C1, scoped to the default route and `--finalize`. Waivers are recorded in 61-SIGNOFF.md "Not proven live — waiver requested", granted at sign-off. |
| 7 | Limits are stated plainly to users | VERIFIED (WARNING) | 61-RELEASE-NOTES.md "Known limits" has 6 plain bullets, C1 first, and says which routes ran live and which rest on tests. The notes also say "the first limit above is listed only in these notes". **Warning WR-01, see below:** the README makes positive claims that C1 contradicts, and its 2.14 limitations list omits C1. |
| 8 | Owner signed off on one plain-terms page | VERIFIED | 61-SIGNOFF.md `Status: SIGNED OFF (owner, 2026-10-30)`. Verbatim "A: Ship, known limit (Recommended)". Per-gate table, smoke result, Dependabot note and waivers are present. |
| 9 | SC3c: ships through the existing close workflow without waiting for Lean (judged as: the runbook is ready and nothing blocks it) | VERIFIED (pending close by design) | 61-CLOSE-RUNBOOK.md steps 1-10 cover: verify/audit/complete-milestone with its in-branch tag skipped and asserted, D-12 freshness assert, PR, squash, tree-identity `origin/main:<p> == C:<p>` for `plugins/vibe-check README.md`, tag on `origin/main`, `gh release create --notes-file`, remote check, cache update with registry check, and cleanup. No Lean step or dependency (61-CONTEXT:109: Lean starts only after this ships). Preconditions hold today: no local `v2.14` tag, origin/main is an ancestor of HEAD, and the repo has `delete_branch_on_merge: true`, so step 10's remote-branch check will pass. |
| 10 | The D-03 live PR fetch matches local, so R6 is checked once | VERIFIED (from record) | G6: PR #6 IDENTICAL (11,255 lines), PR #4 IDENTICAL (1,431 lines, 133 renames). Not re-run because it needs the network and gh. The raw result lines are in the record. |

**Score:** 10/10 truths verified. One carries a warning that needs an owner decision.

### Required artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/vibe-check/.claude-plugin/plugin.json` | 2.14.0 | VERIFIED | Line 4 |
| `README.md` | "v2.14 (this release)", 2.14 limits, min_confidence clause removed | VERIFIED | Lines 30-34, 350-358. See WR-01/WR-02. |
| `61-CANDIDATE.md` | `candidate: <40-hex>` | VERIFIED | `candidate: 0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d` |
| `61-LIVE-SMOKE-PROPOSAL.md` | Status line | VERIFIED | APPROVED 2026-10-30 |
| `61-LIVE-SMOKE.md` | `## Verdict` | VERIFIED | PASS with C1-C5 classified |
| `61-RELEASE-RECORD.md` | `## Gate results`, `## Validation gaps and waivers` | VERIFIED | Both present, G1-G9 all PASS |
| `61-RELEASE-NOTES.md` | "Known limits" | VERIFIED | 6 bullets |
| `61-SIGNOFF.md` | `## Owner sign-off` | VERIFIED | SIGNED OFF |
| `61-CLOSE-RUNBOOK.md` | `rev-parse "origin/main:` | VERIFIED | Step 5 |

### Key link verification

| From | To | Via | Status |
|------|----|-----|--------|
| 61-CANDIDATE.md | commit C | `^candidate: [0-9a-f]{40}$` | WIRED (the SHA resolves; it is the gated commit) |
| README | test_recovery_pairs / test_gitguard | untouched coupled phrases | WIRED (185 passed, re-run here) |
| Record header | candidate SHA | "Code under consideration" line | WIRED |
| Runbook steps 2/4/5 | 61-CANDIDATE.md | `sed -n 's/^candidate: //p'`, never retyped | WIRED |
| Runbook step 7 | 61-RELEASE-NOTES.md | `--notes-file` | WIRED |
| SIGNOFF | RELEASE-RECORD / LIVE-SMOKE | links | WIRED |
| Smoke | proposal Status | approval gate | WIRED |

### Data-flow trace (Level 4)

Not applicable. This is a release-gate phase with no rendering artifacts.

### Behavioral spot-checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| README-coupled tests pass on the shipped tree | `pytest -q -p no:cacheprovider test_recovery_pairs.py test_gitguard.py` | 185 passed, 708 subtests | PASS |
| Route tests for default/range/PR | `pytest -q test_diff_ranges.py -k "TestRouteDefault or TestRouteRange or TestRoutePR"` | 10 passed | PASS |
| Replay manifest intact | `python3 replay.py check-manifest` | exit 0 | PASS |
| Replay machinery frozen since v2.13 | `git diff --stat v2.13 0d2be77 -- replay.py test_replay.py` | empty | PASS |
| Nothing outside .planning differs C→HEAD | `git diff --stat 0d2be77 HEAD -- . ':(exclude).planning'` | empty | PASS |
| Squash ships only C's change | `git diff --stat origin/main 0d2be77 -- plugins README.md` | README.md, plugin.json only | PASS |

### Probe execution

Not applicable. The phase declares no `probe-*.sh` scripts.

### Requirements coverage

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| GATE-01 | 61-01, 61-03, 61-05 | SATISFIED | Truths 1, 4 |
| GATE-02 | 61-03, 61-05 | SATISFIED | Truth 2 |
| GATE-03 | 61-01..61-05 | SATISFIED through sign-off. The "ships" clause is pending close by design. | Truths 5-9. REQUIREMENTS.md:84 records the same. |

There are no orphaned requirements. REQUIREMENTS.md maps only GATE-01..03 to Phase 61, and all three are claimed by plans.

### Anti-patterns found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| README.md | 33, 38, 350-358 | User-facing claim contradicted by observed behavior (C1) | Warning | See WR-01 below |
| README.md | 57 | Stale "Known limitations of this release" pointer in the v2.12 block (61-REVIEW WR-02) | Info | Navigation only; the Limitations section is still reachable |
| README.md / plugin.json (C diff) | — | TBD/FIXME/XXX/TODO | None found | — |

### WR-01 assessment: does it undermine "limits are stated plainly"?

What is true:
- C1 is stated plainly in every gate artifact and in the user-facing release notes, as the first bullet. The notes are honest that the README does not carry it. The release record (§Carried C1) explicitly says C1 "contradicts the README's standing claim that a decision is kept 'when you edit unrelated code'". So the SC3 contract, "the release record states … explicitly", is met. Under option A, the release notes are the agreed disclosure channel.
- The effect is extra questions and a false "code next to it changed" reason on the card. Nothing is lost, Close out completes, and it probably predates 2.14. It fails toward asking. This is not a qualifying class, so it is not a BLOCKER.

What weakens it:
- The README is the document marketplace users read, and the marketplace pins `ref: main`. It is not silent: line 38 says decisions are kept "when you edit unrelated code". On the default route, for uncommitted code, that is false on every pass. Line 33 says the exact window "applies on the default … route". The window mechanics are technically right, but the baseline makes the whole uncommitted block count as changed, so a reader takes away the wrong expectation. The "Known limitations (2.14)" list, which the release notes call the "Full list", omits C1.
- The owner's waiver was given on the sign-off page's framing: "the README does not mention it" and "the README stays silent on it". That framing is inaccurate, and the inaccuracy runs in the direction that makes A look cheaper.

Classification: **WARNING, needs an owner decision.** It is not a BLOCKER, because the contracted disclosure exists and the effect fails safe. It is not dismissed either, because a README-only user on the most common route is told the opposite of what happens, and the ruling was made on an understated description. Re-asking the owner with the accurate framing is the honest close. If A stands, nothing else is required.

### Human verification required

#### 1. Re-confirm Decision 1 with accurate framing

**Test:** Show the owner that the README positively claims decisions stick when unrelated code is edited (line 38), and that the default route uses the exact window (line 33). Also show that its 2.14 limitations list omits C1. Then ask whether A (README unchanged, C1 in the release notes plus 999.28) still stands, or whether B is preferred: a one-clause README edit, a new candidate, G1-G9 re-run, and a re-sign. B costs about 45 minutes and no paid spend.
**Expected:** An explicit "A stands" or "B".
**Why human:** This is a disclosure and product call. The waiver was granted on a softer description than the facts.

### Gaps summary

There are no blocking gaps. The candidate is proven: the gates pass on C, replay shows 0 differences, and the replay machinery is frozen. The record covers residuals, fixtures, waivers and the live smoke. Nothing outside `.planning` differs between C and HEAD, or between origin/main and C beyond C's two files. The close runbook is complete, has no Lean dependency, and none of its preconditions is currently violated. Publishing is correctly pending at milestone close. One warning remains (WR-01): the README contradicts limit C1, and the owner's ruling was framed as if the README were silent. The owner should re-confirm. WR-02, IN-01..03 from 61-REVIEW.md are cosmetic README carries and do not affect the goal.

---

_Verified: 2026-10-30T23:10:00Z_
_Verifier: Claude (bm-verifier)_


## Owner resolution (2026-10-30)

WR-01 human-verification item resolved: owner switched Decision 1 to B; README-only candidate 47978aa (plugins/ byte-identical to 0d2be77, tree 9387dcd) re-gated G1-G9 PASS; owner re-signed. Status updated human_needed → passed. See 61-HUMAN-UAT.md and 61-SIGNOFF.md.
