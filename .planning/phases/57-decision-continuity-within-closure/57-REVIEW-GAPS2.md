---
phase: 57-decision-continuity-within-closure
scope: second gap closure (git diff d419dc2..HEAD -- plugins/, plans 57-14..57-16)
reviewed: 2026-10-27T00:51:48Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - plugins/vibe-check/scripts/score.py
  - plugins/vibe-check/scripts/test_carry_state.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_score.py
findings:
  critical: 1
  warning: 1
  info: 2
  total: 4
status: issues_found
---

# Phase 57: Code Review Report (second gap closure, 57-14..57-16)

**Reviewed:** 2026-10-27T00:51:48Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Scope: `score.py` (the `carried=` arm of `_snapshot_for`, the lead-obligation prior seed, and the `carried=` call site) and the new tests. The three reviewed modules pass: 767 tests, 709 subtests.

How the five checks came out:

| Check | Result |
|---|---|
| (1) Blocker closed for both shapes | **Closed for the shapes the fixtures use.** Inherited split with a nearby fix: stale/nearby. Own-decision absorbed split: stale/nearby. Owed stamp kept across a quiet split. A split with an edit outside the window does not stamp (reproduced with an edit at line 40). Two covered members splitting at once both stamp and both re-ask. **Not closed when the split row is led by a fresh re-report of the same finding from the same lane** (CR-01). |
| (2) The `carried=` arm cannot stamp a fresh finding and cannot be forged | Holds. `status` is scrubbed at ingress (`score.py:2187-2190`). A survivor with no status defaults to `"new"`. An expanded member's status is always recomputed (`_expand_members`, `status=st`). `status` and `snapshot` are both in `_MEMBER_EXCLUDED_KEYS`, so a raw member cannot inject either one. The `obligation` sidecar comes only from orchestrator carryforward. One caveat is in IN-01: a `needs-recheck` lead whose hash changed is stamped, which is harmless. |
| (3) No change to `stable_hash` or snapshot fields beyond `nearby_at`/`at_pass` | Holds. The hash code is untouched (the golden test passes). The seed passes an obligation snapshot only as the *prior*, and `_snapshot_for` rebuilds the output dict from the same five keys plus `nearby_at`. |
| (4) The end-to-end mutants target shipped lines | Yes. Both target strings are unique in `score.py`. `patch.object(score, "_snapshot_for"/"run")` is resolved at call time by `run_pass -> score.run`. In my own mutation run, dropping the carried arm, forcing `carried=False`, forcing `carried=True` and removing the seed were all killed. **Two new guards survive mutation** (WR-01). |
| (5) The pass-7 owner-journey change matches D-17 | Yes. Pass 7 now expects stale/nearby with `nearby_at == 7`, shows only hD on the card, and blocks the gate. After the owner decides, pass 8 is quiet and the decision stays current. This is D-17's "re-asks once, no exemption" behaviour. |

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: A split row led by a same-lane re-report of the carried finding loses both the split-pass stamp and the stamp already owed, so the decision closes silently

**File:** `plugins/vibe-check/scripts/score.py:2600-2604` (the seed is keyed on `best_member` only), `:2622-2636` (the dedup branch skips a same-identity carried record without seeding `same_hash_prior`), `:2687` (`carried=` reads only the lead's status)

**Issue:** Reviewer lanes run again on every pass. On the split pass the `bugs` lane can report A again: same file, line, title and canonical text, so the same `_finding_identity` and the same hash. If that re-report scores higher than the carried copy, the fresh record leads the row. A higher confidence is enough to beat the +15 persisted bonus (reproduced at conf 100 against 75, and at conf 90 with severity `critical`). Then:
- `best_member` is the fresh record, so the survivor's status is `"new"` and `carried=False`;
- the seed at 2600 does not fire, because `best_member` is not in `carried_obligations`;
- the carried A is handled in the `ident in kept_by_ident` branch (`ref_kept is members[0]`), which `continue`s before the `same_hash_prior` lookup.

So the row gets a fresh snapshot with no `nearby_at`. `TestSameHashLeadKeepsNearbyStamp` (test_decision_continuity.py:1420) fixed this class only for a *different* lane with the same hash. The same-lane case, which is the more common one, is still open.

Reproduced on the real chain (`score.run -> append_pass -> carry_state`), using `split_scenario`/`absorbed_split_scenario` with one extra fresh finding on the split pass:

```
inherited split, real diff {F:[[12,12]]}, + fresh bugs A conf=100 critical
  row bugs 10 status=new snap{at_pass:2, nearby_at:None}
  decision_state -> current, outstanding -> False        (expected stale/nearby)

own decision, owed nearby_at=2, quiet split pass 3, + same fresh re-report
  row bugs 10 status=new snap{at_pass:3, nearby_at:None}
  decision_state -> current, outstanding -> False        (expected stale/nearby: the owed re-ask is erased)

own decision, nearby split pass 3, + same fresh re-report -> current (expected stale)
control: the same re-report at conf 75/80/90 warning -> carried copy leads -> stale/nearby (correct)
```

The same root cause also affects a decided row that does **not** split: a same-lane re-report that out-ranks the carried row drops the D-02 nearby stamp. This already happened at d419dc2 (see SA-01).

Effect: the owner's re-ask is silently lost. This is the same false-closure harm as the original CR-01, and whether it happens depends on how confident the model happens to be on that pass.

**Fix:** Decide "carried" and seed the prior from any source record with the row's hash, not only from the lead:

```python
# group loop, replacing the best_member-only seed
if "snapshot" not in survivor:
    for _, m, _, _, _ in scored_members:
        obl = carried_obligations.get(id(m), {}).get("obligation")
        if (obl and obl.get("stable_hash") == survivor["stable_hash"]
                and isinstance(obl.get("snapshot"), dict)):
            survivor["snapshot"] = obl["snapshot"]
            break
# threshold loop: carried = the row's own finding existed before this pass
carried = any(m.get("status") in _CARRIED_STATUSES
              and stable_hash(m.get("file", ""), score_canon(m), m.get("title", ""))
                  == survivor["stable_hash"]
              for m in sources)
```

Cache the per-member canonical-for-hash from the scoring decision so the hash is not recomputed. Keep the hash-equality condition so s4 (a fresh lead with a *different* hash over a carried member) stays unstamped. Add the three reproductions above as fixtures, each with a mutant.

## Warnings

### WR-01: Two new guards survive mutation: the `needs-recheck` arm of `_CARRIED_STATUSES`, and the hash-equality check on the seed

**File:** `plugins/vibe-check/scripts/score.py:362` and `:2602`

**Issue:** I mutated each line and ran all three modules, diffing the failures against an unmutated copy:
- `_CARRIED_STATUSES = ("persisted",)` (drop `needs-recheck`): **survives**, with zero new failures. The arm is reachable on a hash-preserving path. `carry_forward_status` returns `needs-recheck` when the canonical first line is unchanged but its widened window changed, which happens for a low-entropy line such as `}` (`score.py:1180-1186`). The hash is built from the first line only, so the row keeps its hash and any decision on it. Without the arm, that split row would lose its D-17 stamp. No test exercises it.
- `lead_obl.get("stable_hash") == survivor["stable_hash"]` → `True`: **survives**. Without it, a lead whose line changed (a new hash) would inherit the old record's `nearby_at`/`at_pass` on the refresh branch.
- The `"snapshot" not in survivor` guard also survives, but that is an equivalent mutant: a carried lead rep's obligation snapshot is its own `cf["snapshot"]`.

Project rule (decorative-guard lesson): every lock must be mutation-tested.

**Fix:** Add a split fixture with a low-entropy member line whose next line changes on the split pass. Assert `status == "needs-recheck"`, an unchanged hash, `nearby_at == split pass` and stale/nearby, and kill `("persisted",)`. Add a fixture where the lead member carries an obligation, its line is edited (a new hash), and the diff omits that line. Assert the new row has no inherited `nearby_at`, and kill the hash-guard mutant.

## Info

### IN-01: The `carried=` arm stamps a `needs-recheck` lead whose hash is new, which contradicts its own docstring

**File:** `plugins/vibe-check/scripts/score.py:319-330`, `:2687`
**Issue:** When an expanded member's own line changed, it re-hashes into a finding that has never been a row. It still gets `nearby_at` = this pass, because its status is `needs-recheck`. I observed this in a probe: a row with a new hash, status `needs-recheck`, and `nearby_at: 2`. The docstring says the change a finding is first raised on "is the code it is about, not a change since". The outcome is harmless: no decision or `covers` entry can match the new hash or code, so the row is asked as new either way. The stamp is noise in persisted state, though, and the docstring overstates the invariant.
**Fix:** If CR-01's hash-matched `carried` is adopted, this goes away. Otherwise, reword the docstring: "a record that existed before this pass, under any hash".

### IN-02: Over-long call line

**File:** `plugins/vibe-check/scripts/score.py:2687` (135 columns, the longest new line in the file)
**Fix:** Bind `carried = survivor.get("status") in _CARRIED_STATUSES` on its own line, or wrap the arguments.

## Set aside (needs ruling)

### SA-01: The same-lane fresh-lead stamp loss also happens without a split (pre-existing)

**Where:** `plugins/vibe-check/scripts/score.py:2576-2636`, `:2687`
**Why excluded:** This happened before the reviewed diff (reproduced at d419dc2). Pass 1: A dismissed. Pass 2: an edit at line 12 plus a `bugs` re-report of A at conf 100/critical. The row becomes `status=new` with no `nearby_at`, and `decision_state` is `current`. This review is scoped to the split-pass gap.
**Effect if left as is:** A decided finding's "code next to it changed" re-ask (D-02/D-14) is skipped whenever its own lane happens to report it again with higher confidence on the pass of the nearby edit. This is a silent keep, which falls under the owner's "silent finding loss" class for new work.
**Needs:** A ruling: fold it into the CR-01 fix (the same code change closes both, so the extra cost is one fixture), or defer it.

---

_Reviewed: 2026-10-27T00:51:48Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
