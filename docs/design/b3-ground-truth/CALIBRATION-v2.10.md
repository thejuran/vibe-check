# CALIBRATION-v2.10 — B-REWEIGHT method record (fixed before any candidate replay)

This record fixes the method behind the per-agent confidence offsets that `score.py` embeds as
`AGENT_CONFIDENCE_OFFSET`. It also records the labeled counts and the offsets the method yields
on the committed archives, and the spot-check tie-break. All of it was written before any
candidate scorer was replayed.

## Why this record exists (D-15)

The method, its parameters and the labeled counts are committed BEFORE any candidate scorer is
replayed, so nothing is tuned to the guardrail. The ordering is checkable by git ancestry: this
file's first commit must be an ancestor of the first commit of every
`REPLAY-REPORT-phase41-{b-sev,b-reweight,h-lane,combined}.md` (plan 41-04 adds that test). If
the guardrail rejects this method, the rejection is recorded here as REJECTED. The next method
then needs its own principled reason; it may not be this method with a different prior strength.
The guardrail is a gate, not an optimizer (D-08).

## Method (fixed)

- **Per-agent.** One offset per agent name. It is not a per-bucket curve.
- **Lower-only.** An offset never raises confidence. An agent at or above the pool is identity.
- **Lone-lane only.** `score.py` applies the offset only to groups with no second opinion
  (D-01/D-15). Independent corroboration restores the raw confidence.
- **Empirical-Bayes shrinkage** toward the pooled precision, with prior strength `ALPHA = 20`.
- **Minimum labeled sample** `MIN_LABELED = 5`. Below it the agent is identity (D-06).
- **Zero offsets are omitted.** An absent agent means 0.

```
p_pool   = ΣTP / Σ(TP + FP)                       over every labeled agent
p̂_a      = (TP_a + 20 · p_pool) / (n_a + 20)       n_a = TP_a + FP_a ≥ 5
offset_a = min(0, round(100 · (p̂_a − p_pool)))    absent when 0 or when n_a < 5
```

Arithmetic is exact (`fractions.Fraction`). `round` is Python 3's, which rounds half-to-even:
an exact −5/2 becomes −2 and an exact −7/2 becomes −4. `test_calibrate.py` pins both cases.

**Why α = 20.** α = 20 was fixed at plan time, from research's indicative counts, and no search
was run. Two reasons were given. First, a prior of 20 is about the size of the smallest
well-sampled agent. Second, on research's counts α = 10 put impact at −22, which fails the
guardrail alone (the largest single-agent-safe impact offset was −20 under baseline grouping),
while α = 20 put impact at −18, inside that bound. That is the reason the value was fixed a
priori. It is not a search result, and it was not revisited after the committed manifest
produced different counts (see Labeled counts).

**Why a per-agent offset, not a per-bucket curve.** Confidence does not separate TP from FP
within an agent: impact's TPs sit at 82–95 and its FPs at 72–95. A curve over confidence buckets
would fit noise. A base-rate shift per agent is what the data supports.

## Inputs (D-04, D-06)

- `runs-v2.10/` (36 scoreable runs) + `runs-v2.10-phase40/` (12) = 48 runs on the model
  generation that ships. These are the only archives that teach the calibration.
- `runs/` (v2.9, the previous model generation) teaches nothing. `calibrate.py counts` raises
  `CalibrationError` if a v2.9 path is labeled.
- should-quiet-7 is excluded (ledger 001, D-06). `counts` raises if any path in
  `excluded_runs` is labeled.
- **TP:** a `survivors_at_site` entry with `axis: true` on a manifest catch run marked
  `calibration: true` (21 runs), counted for its `agent`. Every axis-qualifying survivor at SITE
  counts, whatever its band.
- **FP:** a last-pass survivor (`passes[-1].findings[]`) with archived band `critical` or
  `warning` on a quiet run in `quiet_runs.headline` (18) or `quiet_runs.phase40` (6), counted for
  its `agent`.
- **Unlabeled:** everything else. That covers axis-false findings at SITE, anything off SITE on a
  catch run, medium or lower findings on quiet runs, and every `filtered[]` stub.
- Survivors only: filtered stubs carry no confidence.
- Labels use the ARCHIVED band, which is the adjudicated ground truth, never a replay.

## Labeled counts (verbatim `calibrate.py counts` output)

```
| agent | TP | FP | n | labeled? |
|---|---|---|---|---|
| architecture | 6 | 6 | 12 | yes |
| bugs | 22 | 13 | 35 | yes |
| codex-adversarial | 18 | 4 | 22 | yes |
| compliance | 7 | 0 | 7 | yes |
| framework-fastapi | 2 | 0 | 2 | no (identity) |
| impact | 24 | 26 | 50 | yes |
| language-typescript | 2 | 0 | 2 | no (identity) |
| security | 15 | 2 | 17 | yes |

pooled precision = ΣTP/Σ(TP+FP) = 96/147
ALPHA=20 MIN_LABELED=5
```

These counts differ from research's indicative table (impact 6/26, architecture 0/6, pool 46/97).
Research used a hand-coded list of qualifiers. The committed manifest (41-01) labels every
finding at SITE for AXIS, so more survivors on catch runs are TPs. Four of the 96 TPs are at band
`medium` (impact 2, security 1, language-typescript 1), because the TP rule has no band filter.
The rule was applied as written and was not changed after these counts were seen.

## Derived offsets (verbatim `calibrate.py derive` output)

```
{"architecture": -6, "bugs": -2, "impact": -12}
```

- **impact** (n = 50: TP 24, FP 26): p̂ ≈ 0.529 against p_pool = 96/147 ≈ 0.653, so the offset
  is −12.
- **architecture** (n = 12: TP 6, FP 6): p̂ ≈ 0.596, so the offset is −6.
- **bugs** (n = 35: TP 22, FP 13): p̂ ≈ 0.638, so the offset is −2.
- codex-adversarial, compliance and security sit above the pool, so they are identity (lower-only).
  framework-fastapi and language-typescript have n = 2 < 5, so they are identity (thin data).

## Undercount disclosure (Pitfall 4)

TP counts only axis-qualifying findings on catch runs. Other real issues an agent found on a
catch run are unlabeled, not TP. Precision is therefore a LOWER bound for every agent. That is an
argument for shrinking toward the pool rather than using raw precision, and for lower-only
offsets: an undercounted agent is pulled toward the pool, not pushed below it by a thin sample.

## Re-derive

```
python3 plugins/vibe-check/scripts/calibrate.py derive
python3 plugins/vibe-check/scripts/calibrate.py --check
```

`--check` exits 0 only when `score.AGENT_CONFIDENCE_OFFSET` equals the derivation over the
committed archives. It exits 1 on a mismatch, or when the constant is absent (expected until
plan 41-05 lands). The next milestone re-runs both commands after it archives new runs and
updates the catch manifest. The method above does not change when that happens.

## Spot-check tie-break (D-16, stated before the replay ranks)

The two spot-check diffs are the eligible should-quiet diffs with the largest predicted movement.
Predicted movement is the number of FP runs in the baseline replay minus the number in the
combined-candidate replay, over the diff's archived triplet. A diff that is already quiet in its
post-diet runs carries no signal and is skipped: should-quiet-5 was 0/3 in the Phase-40 final
check. Any remaining ties go to the lower diff number. should-quiet-7 is ineligible (ledger 001).
should-quiet-6 is codex-driven, and D-01 keeps codex as the independent voter, so Wave 1 is not
expected to move it. If the replay agrees, that is recorded as-is, not tuned away.
