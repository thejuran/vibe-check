# Fable code review — vibe-check v2.7 stable (Pass B1)

> **Status:** Opus, 2026-07-01. Copy-paste prompt for a FRESH Fable session at the vibe-check
> repo root, pinned to the v2.7 stable surface. This is the **variant-D** data point: a
> different frontier model, fresh context, adversarial — reviewing code that vibe-check's own
> dogfood + codex stack has already been over. The measure of value is whether Fable catches
> anything that stack missed.
>
> **How to use:**
> - Run in a FRESH session at `/Users/julianamacbook/turingmind-code-review`.
> - `git checkout v2.7` first so Fable reviews the frozen shipped surface (the working tree is
>   mid-v2.8; you want the tag).
> - This pass is CODE CORRECTNESS only. Design/efficacy questions are Pass B2 — a separate doc.

---

```
You are Fable, a second frontier model, doing a cold adversarial code review of vibe-check —
a Claude Code plugin that reviews git diffs by dispatching per-domain subagents whose JSON
findings are scored, filtered, and rendered by a deterministic Python engine. You are the
independent second-model reviewer: this code has already been reviewed by the tool's own
deep-review and by GPT-5-codex adversarial passes across many milestones. Your job is to
find what THEY missed. A finding that merely re-states what their tests already cover is not
useful; a finding that survives because you read the code differently is exactly the point.

## Scope — CODE CORRECTNESS ONLY
Find real latent bugs, edge cases, and correctness/maintainability defects. This is NOT a
design review (is the scoring model sound? does each agent earn its place?) — that's a
separate pass. Stay on: does this code do what it claims, on all inputs?

## Read (repo root, checked out at tag v2.7)
Core engine (highest priority — most logic, most reliance):
- plugins/vibe-check/scripts/score.py        (the scoring engine, ~1083 lines)
- plugins/vibe-check/scripts/test_score.py    (what's already tested — DON'T re-report covered cases)
- plugins/vibe-check/scripts/config.py        (the .vibe-check.toml reader)
- plugins/vibe-check/scripts/test_config.py
Contracts the engine assumes:
- plugins/vibe-check/templates/agent-output-schema.md   (the JSON contract agents emit)
- plugins/vibe-check/templates/scoring.md               (the scoring rules score.py implements)

## Specific smells to confirm or refute (found by a prior structural read — verify independently, don't take on trust)
1. **Tie-break order-dependence (score.py ~line 904-906).** The comment says "keep first on
   ties," but among same-score members of a cross-confirm group, which member becomes the
   emitted representative (its title/file/current_code/stable_hash, and its persisted
   dismissal key) appears input-order-dependent. Grouping is order-independent and tested; the
   representative choice among tied members is NOT tested. Confirm whether two same-score
   members with different titles can yield different emitted output depending on input order.
   This is the highest-priority item.
2. **Cross-file constant drift.** config.py defines `_MEDIUM_FLOOR = 70` (rejects
   `medium < 70`) BECAUSE score.py's `THRESHOLDS["deep-review"] = 70`. The two 70s are linked
   only by a prose comment; no test asserts they stay equal. Confirm this is a real drift
   hazard (change one, the other silently becomes wrong).
3. **`persisted` detection via `id(member)` (score.py ~1055).** Identity-based state that
   works only because no intermediate dict-copy occurs today. Is the `status=="persisted"`
   fallback actually sufficient, or can a path reach here where BOTH miss?
4. **`min_confidence` filter drop label (score.py ~1064).** A finding dropped for a non-
   silenced, non-threshold reason (e.g. intent-doc −100) is still labeled "sub-threshold" in
   filtered[]. Reporting-accuracy: does this mislead the honesty summary?
5. **Case-sensitive silenced-marker match (score.py ~40, ~160).** `eslint-disable` won't
   match `ESLint-disable`. Does a genuinely-silenced finding escape the −50 and surface?
6. **Band/threshold boundaries.** The range endpoints of `_line_in_ranges` (inclusive
   `pair[0] <= line <= pair[1]`) are not tested at the exact endpoints; malformed range pairs
   (`len < 2`, inverted, 3-element) are guarded but under-tested. Any off-by-one or lossy
   handling?

## Beyond the list
The six above are leads, not a ceiling. Read score.py's scoring pipeline end-to-end
(compute_score, cross_confirm_group, the min_confidence filter, carry_forward, the envelope
run()) and config.py's per-key validation, and report any OTHER real defect. Prioritize:
float/int coercion boundaries, order-dependence, guards that don't guard, fail-open where
fail-closed was intended, and any place a malformed agent JSON could produce a wrong score
rather than a dropped finding.

## Output format
For each finding: file:line | one-line defect | the concrete input/state that triggers it →
the wrong output/crash | whether test_score.py/test_config.py already covers it (if yes, say
so and DROP it) | severity (does it change a verdict the owner relies on, or is it cosmetic?).
Rank by whether it can silently change a review verdict — that's the failure class that
matters most, because the owner (a PM who can't read code) cannot catch a wrong verdict.
Do NOT edit code. Report only. If you can write a failing test that proves a finding, include
it — a failing test is ground truth and settles the finding.
```
