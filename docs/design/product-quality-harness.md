# vibe-check — Product-Quality Ground-Truth Harness (Pass B3, plan)

> **Status:** Opus, 2026-07-01. This is the plan for measuring the question that matters most
> to a tool the owner relies on: **is vibe-check actually a good reviewer?** — catch-rate on
> real bugs, false-positive-rate on clean-but-suspicious code. It fills vibe-check's
> self-documented efficacy gap (no aggregate catch/FP number is ever computed — `RESULTS.md:64`).
>
> Unlike B1/B2 (Fable-facing prompts, ready now), this needs two inputs before it can run:
> the owner's real past diffs with known outcomes, and a running vibe-check. So it's staged.

## Why this and not just the existing answer-key

vibe-check already has `ANSWER-KEY.md`: a rigorous **single-agent** (framework-fastapi),
**single-repo**, **manually-scored** planted-bug set with S-items (should fire) and B-items
(bait, must stay silent). It's the right template. Its limits, and how this harness extends it:

| ANSWER-KEY.md today | This harness adds |
|---|---|
| One agent (framework-fastapi) | Breadth across the fleet via the owner's real diffs (TS, Python, framework variety) |
| One throwaway fixture (uncommitted) | Real diffs from shipped projects — realistic, not synthetic |
| Manual scoring vs a table | Same manual/agent scoring, but aggregated into a **catch-rate / FP-rate number** the tool has never had |
| Proves a new agent works | Proves the *product* is trustworthy across the surface the owner actually reviews |

The two sources **compose**: the answer-key gives rigor (known planted items, N=3 stability);
the real diffs give breadth and realism. Neither alone answers "is it good across my work."

## The ground-truth sources

### Source 1 — the owner's real past diffs (chosen 2026-07-01)
Real diffs from the owner's repos where the outcome is known:
- **Should-be-quiet:** a diff that shipped clean and stayed clean → vibe-check should produce
  few/no ≥70 findings (false-positive test).
- **Should-have-caught:** a diff that shipped with a bug later found → vibe-check *should*
  surface it (catch test). The later-found bug is the ground-truth positive.

### Source 2 — vibe-check's own memory already catalogs known-outcome diffs (low owner burden)
The vibe-check project memory records specific diffs with known outcomes — mine these FIRST
before asking the owner to recall:
- The "DOGFOOD WIN #1–8" entries — each names a diff where deep-review caught a real self-defect
  (e.g. WIN #6: caught 2W+3M self-contradictions in RESULTS-v2.7 prose; P27: stray harness tags;
  P20: coverage-reader-robustness defects). These are **confirmed catches** — ground-truth
  positives already documented.
- `12-DOGFOOD-FINDINGS-BACKLOG.md` — 9 real self-defects `--all` caught.
- The `ANSWER-KEY.md` fixture (regenerable from the dashboard slice it describes).

## The measurement (the number vibe-check has never had)

Run vibe-check on the assembled set; score each finding against known truth:

```
CATCH RATE   = (real bugs surfaced ≥ threshold) / (known real bugs in the set)
FALSE-POS RATE = (findings ≥ threshold that are NOT real bugs) / (total findings ≥ threshold)
SILENCE (bait) = (B-items that stayed < threshold) / (total B-items)      [from answer-key]
```

- Report at both thresholds (`/review` ≥80, `/deep-review` ≥70) — they answer different
  questions (does the quick gate over-filter? does the deep gate over-report?).
- Keep the answer-key's **three-state bait rubric** (truly-silent / fired-but-filtered /
  surfaced-≥70) — "fired-but-filtered" is a partial pass and the honest middle the binary
  gate hides.
- N=3 stability per diff (vibe-check output is LLM-driven → non-deterministic); a flaky 2/3 is
  analyzed, not auto-scored.

## Staged execution

**Stage 0 — assemble the set (needs owner).** Mine memory (Source 2) for documented
known-outcome diffs; then ask the owner for 3–5 real diffs (Source 1) spanning the languages
he most relies on vibe-check for. Target ~8–12 diffs total; each labeled with its known
outcome and (for should-have-caught) the specific bug.

**Stage 1 — confirm the running version.** Install cache is `2.7.0` == repo `plugin.json 2.7.0`
(verified — not stale). So a run reflects the reviewed code. Re-verify before running.

**Stage 2 — run + score.** Run `/deep-review` (and `/review`) on each diff, N=3. Score each
finding vs truth into the rubric. Aggregate into catch/FP/silence numbers.

**Stage 3 — Fable as variant-D (the cross-model check).** Hand Fable the SAME diffs cold and
have it independently review them. Compare: where vibe-check and Fable agree = high-confidence
signal; where they diverge = the interesting cases (a vibe-check miss Fable caught = a real
gap; a Fable miss vibe-check caught = vibe-check earning its keep). This de-confounds "is
vibe-check good" from "is any LLM reviewer good on this diff."

**Stage 4 — attack the answer key.** Have Fable review `ANSWER-KEY.md`'s S/B classification.
A disagreement (Fable thinks a B-item bait IS a real bug, or an S-item shouldn't fire) is
either a vibe-check blind spot or an answer-key error — a finding either way.

## What this produces

- The **first aggregate catch-rate / FP-rate** for vibe-check across a realistic surface —
  the number `RESULTS.md:64` says doesn't exist.
- A **reusable, committed** ground-truth set (unlike the throwaway fixture) that future
  milestones can re-run to detect regression in review quality.
- A **cross-model baseline** (vibe-check vs Fable on identical diffs) — the honest answer to
  "should I keep relying on this," grounded in outcomes, not opinion.

## Owner decisions needed before Stage 0

1. **Which repos/diffs.** Which of the owner's projects does he rely on vibe-check for most
   (the languages/frameworks that matter)? That's where the real diffs should come from.
2. **Committed vs throwaway.** The answer-key fixture is deliberately uncommitted (throwaway).
   Should this extended set be **committed** (reusable, regression-catching) or kept throwaway
   (realistic but one-shot)? Recommendation: committed, sanitized — the reusability is the
   whole point of filling the recall gap.

## Cross-references
- Leverage map: `fable-review-leverage-map.md`
- Existing ground truth: `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md`
- Efficacy method: `plugins/vibe-check/docs/efficacy/RESULTS*.md`
- Design hypotheses these diffs help adjudicate: `design-hypotheses.md`
