---
phase: 56-verified-fixes-close
plan: 03
subsystem: scorer closure (independent route)
tags: [score, independent-route, trigger, schema, mutants]
requires: ["56-01 (RED fixtures + contract strings)", "56-02 (RED retry/prose locks)"]
provides:
  - "score.py independent closure route (`route: \"independent\"`), bound-plain persisted path, D-04 trigger, D-06 test association, D-09 `recheck_settled` memory with D-08 fresh start, D-11 no-reviewer reason"
  - "envelope ingress for `head_blobs` / `touched_paths` (fail-closed containers, normalized values)"
  - "future-schema.json: `recheck_settled` in finding_optional + `_rollback.phase56_added`"
  - "test_verified_fixes.py: TestAssociatedTest, TestEnvelopeIngress56, TestIndependentRouteMutants (15 tests, 14 mutants)"
affects: [56-04 (age gate; `_R_CF_SETTLED` already sits after the age check), 56-05 (prose must forward head_blobs/touched_paths and issue independent/bound requests), 56-06 (end-to-end over the six-row fixture)]
tech-stack:
  added: []
  patterns: ["three-bucket verdict partition (confirmed-fix / independent / plain)", "uniqueness-checked mutant targets (count == 1 before mutating)"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/fixtures/future-schema.json
    - plugins/vibe-check/scripts/test_state_shape.py
    - plugins/vibe-check/scripts/test_verified_fixes.py
decisions:
  - "A plain request is 'bound' when it carries the `snapshot_blob` KEY (null included); a bound null snapshot on a persisted record is rejected with the snapshot reason, not `record not needs-recheck`"
  - "D-11 is suppressed when ANY record in the lead's row was asked, and when a fix verdict names the lead (the confirmed-fix reasons already explain it)"
  - "`recheck_settled` is written only on leads (stored hash present); members never get it"
  - "Bound-plain still-applies on a persisted record emits `_R_IR_STILL` and records the memory, even with no `resolved` in the batch"
metrics:
  duration: "~45 min"
  completed: 2026-10-23
  tasks: 3
  files: 4
---

# Phase 56 Plan 03: Independent closure route in the scorer Summary

The scorer now closes a carried finding when an eligible reviewer confirms it on the code at HEAD. An independent request goes to a ladder confirmer when the raising lane is not dispatched. A bound plain request goes to the raising lane, held to the same rule for a persisted record. Both need a `resolved` answer, nobody asked saying it still applies, the judged blob equal to HEAD's blob, and (for `persisted`) a change near the line, in the file, or in an associated test. A still-applies answer is remembered until the code changes. All 33 RED lines from 56-01 are green and no 56-01 or 56-02 test string was edited. The unbound plain gate, the confirmed-fix path, `carry_forward_status`, GOLDEN_DIGEST and the +15 persisted path are unchanged. Replay shows 0 differing runs.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Constants, helpers, ingress and the schema decision | 0be902e | score.py, future-schema.json, test_state_shape.py, test_verified_fixes.py |
| 2 | Independent branch, bound-plain members, settled memory, D-11 reason | c093cce | score.py, test_verified_fixes.py |
| 3 | Mutant tests for every new guard; replay/golden gates | 7f3858c | test_verified_fixes.py |

## What changed in score.py

- **Vocabulary:** `_INDEPENDENT_ROUTE`, `_NEVER_CONFIRMERS`, `_NEARBY_LINES = 5`, `_FIX_COMMIT_RE` (applied with `fullmatch`), `_R_IR_*` ×6, `_R_CF_SETTLED`. All strings are byte-identical to the 56-01 contract. `_FIXER_AGENTS` is untouched.
- **Pure helpers:**
  - `_is_associated_test(path, src_file)` uses only `str.split` / `rsplit` and `re`.
  - `_independent_trigger(record, touched, ranges)` reuses `_line_in_ranges` over `[line, line+5]`.
- **Request validation (`_routed_request_ok`):**
  - The confirmed-fix branch is byte-identical, so the `score_m5` target still exists.
  - Unbound plain requests are unchanged.
  - A bound plain request needs a valid snapshot, a valid `test_paths` and no never-confirmer.
  - An independent request needs a str `stable_hash`, the snapshot key, agents with no never-confirmer, an optional `test_paths` (list of str) and an optional hex `fix_commit` of 7 to 40 characters.
- **`_accept_verdict(..., facts)`** splits verdicts three ways (confirmed-fix / independent / plain):
  - The plain filter line `if requests_by_token[v["token"]].get("route") is None]` is kept, so `score_m6` still targets it.
  - On a persisted record with bound plain requests, `_bound_plain_recheck` checks in this order: settled, trigger, still-applies, snapshot.
  - Otherwise the original `if status != "needs-recheck":` gate runs unchanged.
  - Independent requests go through `_independent_recheck`, which checks: not issued (None, None), settled, persisted without trigger, no answer, still-applies, snapshot.
  - A closure records `commit_sha` only when the request named `fix_commit`.
  - In the fix loop, a confirmed fix on a settled record is rejected with `_R_CF_SETTLED`. This check runs after the age and evidence checks, and `routed_judged` is set first, so no orphan reason appears.
- **`run()`:**
  - Reads `head_blobs` / `touched_paths` fail-closed.
  - The carry loop applies the fresh-start rule before `_judge` and passes the lead's `touched` list to the lead and its members.
  - `_judge` no longer returns early when an independent request names the lead, so a silent reviewer is reported.
  - `_judge` writes `recheck_settled` on `_R_IR_STILL` / `_R_CF_STILL` when HEAD's blob is known.
  - D-11 is emitted after the carry loop, only when `"head_blobs" in envelope`.
  - `recheck_settled` is added to the NEW-finding scrub, `FINDING_OPTIONAL_KEYS` and `_MEMBER_EXCLUDED_KEYS`. `MEMBER_KEYS` is unchanged.

## Acceptance checks (each run individually)

### Task 1

- `grep -c '^_INDEPENDENT_ROUTE = "independent"' score.py` → `1`
- `grep -c '_NEVER_CONFIRMERS = frozenset({"fix", "codex-adversarial"})' score.py` → `1`
- `grep -c '^_FIXER_AGENTS = frozenset({"fix"})' score.py` → `1`
- AST import one-liner → `['hashlib', 'json', 're', 'sys']`
- `grep -c '"recheck_settled"' fixtures/future-schema.json` → `2`
- `pytest -q test_verified_fixes.py -k "AssociatedTest or EnvelopeIngress56"` → `6 passed, 35 deselected, 42 subtests passed`
- `pytest -q test_state_shape.py -k "phase56 or phase53"` → `3 passed, 97 deselected`
- `pytest -q test_score.py -k "ImportSet or key_sets_match or Golden or golden"` → `11 passed, 466 deselected`
- test_score + test_state_shape + test_confirmed_fix + test_carry_state → `13 failed, 796 passed`. These are exactly the 13 pre-existing 56-02 RED tests.

### Task 2 (run before committing c093cce)

- `pytest -q test_verified_fixes.py` → `41 passed, 56 subtests passed` (0 failed). After the two extra ingress tests and the D-11 de-dup test: `44 passed, 60 subtests passed`.
- `pytest -q "test_score.py::TestVerdictGuard::test_persisted_record_cannot_be_recheck_resolved"` → `1 passed`
- `grep -c 'if status != "needs-recheck":' score.py` → `1`. `git show HEAD:…score.py | grep -c …` → `1` (unchanged).
- `pytest -q test_confirmed_fix.py -k "IndependentRecheck or ScoreConfirmedFix"` → `31 passed, 61 deselected, 15 subtests passed`, with nothing remaining in that selection.
- `pytest -q test_verified_fixes.py -k test_no_confirmer_reason_absent_without_head_blobs` → `1 passed`
- `<verify>` test_score selection (`VerdictGuard or VerdictFixObsolete or KeptOpenMultiPass or NeedsVerificationCarry or SiteGrouping or Rollback`) → `83 passed, 58 subtests passed`
- Full suite before commit: `13 failed, 3019 passed, 4026 subtests passed in 212.06s`. All 13 failures are the 56-02 set.

### Task 3

- `pytest -q test_verified_fixes.py -k Mutants` → `15 passed, 44 deselected`: 14 mutants plus the golden test, 0 skipped.
- Full suite on 7f3858c: **`13 failed, 3034 passed, 4026 subtests passed in 233.80s`**. That is 2986 + 48 new green tests: the 33 former RED lines no longer count as failures, and 15 new tests were added.
- `python3 replay.py candidate --name phase56-gate --scorer rev:7f3858c --out $SCRATCHPAD/phase56-candidate.md` → **exit 0**. `REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1`, **`REGRESSED 0`**.
- `python3 replay.py diff --base rev:24c0c00 --scorer rev:7f3858c --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json --out $SCRATCHPAD/phase56-diff.md` → **exit 0**:
  ```
  - runs compared: 170
  - runs differing: 0
  - runs differing (allowed): 0
  - runs with unallowed differences: 0
  ```
  That is 0 differing and 0 unallowed. No archived envelope carries `head_blobs`, so the D-11 gate added nothing to `filtered[]`. Nothing was written under docs/design.
- GOLDEN_DIGEST: `TestSixRowClosure::test_stable_hash_and_golden_digest_unchanged`, `TestIndependentRouteMutants::test_stable_hash_and_golden_digest_unchanged` (an independent closure reports the carried stable_hash) and the test_score golden tests all pass.

### Mutants (each target asserted unique in score.py before mutating)

| Mutant | Guard removed | Real scorer | Mutant |
|--------|---------------|-------------|--------|
| m10 | independent blob binding | open (`_R_IR_SNAPSHOT`) | closes |
| m11 | `_NEVER_CONFIRMERS` on independent ingress | malformed | codex-adversarial closes |
| m12 | independent trigger (persisted `22d360d9`, nothing touched) | open | closes |
| m13 | independent still-applies | open | closes |
| m14 | independent settled memory (needs-recheck, unchanged blobs) | open | closes |
| m15 | bound-plain blob binding (member `bugs`, wrong blob) | open | closes |
| m16 | bound-plain trigger (`2a01829c`, nothing touched, far ranges) | open | closes |
| m17 | `recheck_settled` NEW-finding scrub | key absent | forged key survives |
| m18 | fresh-start drop (blob changed) | closes | stays blocked |
| m19 | `_NEVER_CONFIRMERS` on bound-plain ingress | malformed | codex-adversarial closes |
| m20 | fresh-start on a new touching commit | closes | stays blocked |
| m21 | `"head_blobs" in envelope` gate on D-11 | no reason | reason on an old envelope |
| m22 | `_R_CF_SETTLED` check in the confirmed-fix loop | open | closes |
| m23 | the `recheck_settled` write | memory recorded | none |

## Remaining RED (13, all owned by later plans)

| Test | Owner | Note |
|------|-------|------|
| `TestFinalizeCountsConfirmedFix::test_awaiting_listed_at_any_later_pass` | 56-04 | carry_state awaiting |
| `TestFinalizeCountsConfirmedFix::test_settled_row_not_awaiting` | 56-04 | carry_state awaiting |
| `TestFinalizeCountsConfirmedFix::test_stale_pass_never_closes` (rewritten in 56-02) | 56-04 | carry_state awaiting |
| `TestRetryAfterInconclusive::test_inconclusive_then_retry_closes_on_unchanged_code` | 56-04 | age gate (`stale fix verdict`) |
| `TestRetryAfterInconclusive::test_retry_after_still_applies_waits_for_code_change` | 56-04 | Now passes the pass-2 `recheck_settled` assertion (this plan writes it). It fails later at pass 3 on `stale fix verdict` instead of `_R_CF_SETTLED`; the age gate (56-04) unblocks it. |
| `TestProse56::{test_carry_state_docstring_says_any_age, test_collect_forwards_independent, test_dispatch_never_rerouted_sentence_gone, test_dispatch_routes_independent, test_output_format_bounded_reason, test_phase05_forwards_applied_any_age, test_phase05_touched_paths, test_render_not_yet_confirmed}` | 56-05 (docstring one: 56-04) | prose |

Ownership was confirmed in 56-04-PLAN.md (lines 82, 113, 132) and 56-05-PLAN.md (line 166).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Contract conflict] D-11 suppressed when any record in the lead's row was asked**
- **Found during:** Task 2
- **Issue:** The plan said "a carried lead that matched NO request". The 56-01 lock `test_member_closes_only_bound` asserts that the `0249b52c` site's rejections are exactly `[record not needs-recheck]` when only the member `bugs` was asked. The lead itself had no request, so the literal rule would add a D-11 reason at the same site and break a 56-01 test.
- **Fix:** A lead counts as asked when any request matches the lead or any member of its row. The reasoning: a reviewer did run on that row this pass.
- **Cost if wrong:** If the owner wants a Codex lead to be explained even when only its members were asked, the render loses one line in that case. The finding stays open either way.
- **Commit:** c093cce

**2. [Rule 2 - Duplicate reason] D-11 skipped for a lead named by a fix verdict**
- **Found during:** Task 2
- **Issue:** A Needs-verification lead under a confirmed fix with no routed request already gets `_R_CF_NO_REVIEWER`. The literal rule would add `_R_IR_NO_REVIEWER` too, giving two near-identical lines.
- **Fix:** Skip D-11 when any fix verdict names the lead's stored hash. This is pinned by `test_no_confirmer_reason_not_doubled_under_a_confirmed_fix`, which has a control showing the same lead does get D-11 when there is no fix verdict.
- **Cost if wrong:** One explanatory line fewer on a confirmed-fix lead. The record stays open.
- **Commit:** c093cce

**3. [Rule 1] Bound = `snapshot_blob` key present, not "non-null"**
- **Found during:** Task 2
- **Issue:** The plan text says "every resolving verdict's request carries a non-null `snapshot_blob`". Under that rule, a bound request with a null snapshot on a persisted record would fall back to `record not needs-recheck`, but the interfaces block says a null snapshot is `_R_IR_SNAPSHOT`.
- **Fix:** Any matched plain request carrying the key is bound. A null snapshot then rejects with the snapshot reason. Both behaviours reject; this one gives the accurate reason.
- **Cost if wrong:** Reason text only. Closure is never widened.
- **Commit:** c093cce

**4. [Rule 2] `_judge` no longer returns early when an independent request names the lead**
- **Found during:** Task 2
- **Issue:** `_judge` returned False whenever no verdict was pending, so `test_silent_reviewer_keeps_open` (issued, no verdict → `_R_IR_NO_ANSWER`) could never pass.
- **Fix:** The guard also runs when an independent request matches the lead.
- **Commit:** c093cce

**5. [Rule 2] Extra mutants beyond m10-m18**
- **Found during:** Task 3
- m19 covers bound-plain never-confirmers, m20 the fresh-start-on-touch rule, m21 the D-11 head_blobs gate, m22 `_R_CF_SETTLED` and m23 the memory write. Each is a separate guard that the plan's list did not cover.
- `_mod` asserts that every mutation target occurs exactly once in score.py, so no mutant silently disables two guards.
- **Commit:** 7f3858c

**6. [Sequencing] Normalization tests landed with Task 2**
- `head_blobs={F: 5}` → treated as None, and `touched_paths={H: "x"}` → treated as `[]`. Both are only observable through the closure route, so the two tests were committed with Task 2 (c093cce). Task 1 shipped the TypeError and no-crash ingress tests.

## Assumption Drift (advisory)

- **m12 fixture.**
  - Planned: m12 uses "persisted `2a01829c`".
  - Actual: `2a01829c` is asked on a bound plain request (R7), not an independent one, so that case is m16. m12 uses `22d360d9` instead: the persisted Codex row on its independent request R4, with nothing touched.
  - Found during: Task 3.
  - Cost if wrong: none. Both guards are mutated.
- **Bound-plain still-applies with no `resolved`.**
  - Planned: the bound rule is evaluated "when status == persisted and every resolving verdict's request carries…".
  - Actual: it is evaluated whenever all matched plain requests on a persisted record are bound. A lone still-applies therefore yields `_R_IR_STILL` and writes the memory on a lead, matching the independent route.
  - Found during: Task 2.
  - Cost if wrong: one extra explanatory reason and a memory that delays a re-ask until the code changes.
- **`recheck_settled` is lost on the kept-open path.**
  - Observed: a lead that drops below threshold and is re-emitted via `_kept_open_rows` rebuilds from `_OBLIGATION_ROW_KEYS + snapshot`, so its memory is not carried.
  - Effect: at worst one extra re-ask. Closure is not widened.
  - Not changed (out of scope).

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-56-08 is covered by m17, T-56-09 by m11/m19, T-56-10 by m10/m15, T-56-11 by `TestEnvelopeIngress56`, T-56-12 by the `fix_commit` subtests (`zz`, 5 hex chars, trailing newline) and T-56-13 by the three-bucket partition with the m6 target preserved.

## Requirements

VFIX-03 and VFIX-04 are marked complete. VFIX-05 (closure half done here; the render half is 56-05) and VFIX-06 (the stale-at-any-age leg is 56-04; the phase-level gate is 56-06) stay Pending.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/scripts/score.py, fixtures/future-schema.json, test_state_shape.py, test_verified_fixes.py
- FOUND commits: 0be902e, c093cce, 7f3858c
