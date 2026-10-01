# B3 v2.10 — Claude-5 pre-change baseline on the grown set (Phase 38, SET-03)

**Headline: catch-rate 15/15 · false-positive-rate 19/21** (no rounding — exact fractions).

This is the **pre-change baseline on the UNCHANGED v2.9.0 plugin, measured under a Claude 5
harness**. Nothing in this milestone's scorer, agent, or orchestration work had happened yet: the
plugin measured here is byte-identical (executable and prompt surface) to shipped tag `v2.9`. It
scores **36 owner-driven `/deep-review` runs** — the grown B3 set of 12 diffs × N=3 — against two
answer-key blobs that were committed and cryptographically sealed BEFORE any run existed. The full
per-run worksheet (every gate result and every SITE/AXIS/BAND verdict) lives at
`docs/design/b3-ground-truth/SCORING-v2.10.md`; every number in this section is transcribed from
that worksheet, never re-derived here.

This is the v2.10 milestone results doc. Later phases (41, 43) append their sections to THIS SAME
file (D-07, one results doc per milestone) — the structure below, `---` then a new H1, is the
RESULTS-v2.9.md precedent and is what those appends attach to.

## Method

- **Grown set: 6 carried + 6 new, sealed at TWO independent seals.** The 6 v2.9 diffs are carried
  over unchanged and scored against the v2.9 key blob; 6 new organic diffs (2 should-catch, 4
  should-quiet) were built this phase and scored against a separate v2.10 key blob. The two seals
  never touch each other: the v2.9 manifest, key, `runs/`, and existing kit files under `diffs/` are
  byte-unchanged. Final composition: **5 should-catch diffs (15 runs) + 7 should-quiet diffs (21
  runs) = 36**.
- **Organic-only sourcing (D-03), carried forward.** All diffs are real shipped commits from the
  owner's own repos — **three** contributing repos: triggarr, seedsyncarr (including its Angular
  front-end under `src/angular/`), and roonseek — selected by the same
  FAIL-CLOSED provenance regex so no vibe-check-found bug can enter the set. The D-03 mining pool
  was four repos (triggarr, seedsyncarr, dashboard, roonseek); dashboard yielded no qualifying
  candidate and contributed zero diffs to the measured set. should-catch diffs are
  *reversed* fix patches (the bug the fix removed); should-quiet diffs are shipped feature commits
  whose selected lines no later commit rewrote.
- **Independence via state isolation (N=3, genuinely independent).** Every run happened on a
  DETACHED checkout of the diff's pinned `base_sha` with the patch applied once and kept applied
  across the diff's 3 runs. All 36 archived states carry `len(passes) == 1` (a fresh empty-state
  sample, never a carry-forward) AND `passes[-1].head_sha == the sealed row's base_sha`. The FULL
  tracked worktree diff sha (`git diff`, NO pathspec) is identical across each diff's 3 runs AND
  equals the kit-build `EXPECTED_TREE_DIFF_SHA256` in its sealed sidecar — for all 12 diffs. Phase-5
  auto-fixes were declined (report-only) so the reviewed tree stays the planted tree.
- **Pinned-base scope.** Each diff was reviewed against its recorded `base_sha` tree, not the repo's
  current HEAD (e.g. autoescape at `e11187e`, secret-in-logs at `f4366a2`, settings-form-split at
  `542d5dd`). The answer-key line numbers are keyed to those exact trees.
- **Scored from state, not transcript (D-06).** Every verdict was read from
  `state.passes[-1].findings[]` (`file`/`line`/`title`/`category`/`band`/`attribution`), never the
  chat transcript. Bands were read, never recomputed (`score.py` single-writer, ROBUST-01).
- **Score-from-blob gate, both blobs.** Scoring read the keys ONLY from committed blobs whose
  digests were read from the committed manifest blob: carried rows from
  `ANSWER_KEY_COMMIT = ef0ab67cb45957167c99eff468077348432e1474`
  (`ANSWER-KEY-b3.md`, sha256 `1463544803309db0…`), new rows from
  `NEW_ANSWER_KEY_COMMIT = 5f687d95f9be4fef2c0fcd78491c308d4c3861e8`
  (`ANSWER-KEY-v2.10.md`, sha256 `f58f888c9f4dc86d…`). Both digest-verified twice, both key commits
  ancestors of HEAD, every run commit descending from SEAL1 (new-diff runs additionally from SEAL2).
  The live working keys were drift-free, but scoring read only the blobs regardless.
- **Two-commit manifest, byte-append seal.** `PREREGISTRATION-v2.10.md` has exactly 2 commits —
  SEAL1 `4c67283b46540f997b8a5c6b530996da880b53ed` (pass bar, decision rule, denominator rule,
  ordering attestations) and SEAL2 `633f1dd0daa24b823d8abab7cff00823a3c2b256` (the five whitelisted
  literal lines). A PINNED canonical verifier (`verify-seal2-append.py` @
  `a407539115872137dc55d99aef439a9c5a4f16d9`, sha256 `7be8ed39…75daaf`, executed from its
  introducing-commit blob) proved on raw bytes that SEAL2 is SEAL1 plus exactly that ordered
  five-line suffix — no seal-1 byte was modified after the bar was set.
- **Complete denominator (no aggregation over holes).** All 36 expected runs passed the
  isolation + pin + tree.diff checks → 3/3 scoreable per diff, **ZERO holes, NO owner waiver**. The
  headline denominators are the SEALED literals from the SEAL2 blob — `DENOM_CATCH_RUNS: 15`,
  `DENOM_QUIET_RUNS: 21`, `DENOM_TOTAL_RUNS: 36` — never a scored-runs-only subset. The diff
  universe was asserted by set-equality against the committed inventory (every `diffs/*.provenance`
  basename), not derived from `runs-v2.10/` globs.
- **Codex = shipped default (D-13).** Runs measured `codex=auto` (no `--codex` forcing, no toml
  overrides). A codex-attributed finding is present in **all 15** should-catch runs and in **7 of
  the 21** should-quiet runs. Absence of a codex-attributed finding is NOT skip evidence — several
  runs record a codex `verdict: approve` with 0 findings.
- **Frozen scoring surface.** `score.py` / `test_score.py` / `config.py` are byte-identical to tag
  `v2.9`, as are `review.md` / `deep-review.md`. This phase measures; it changes nothing measurable.
- **ONE PINNED HARNESS TUPLE across every run.** The tuple was recorded in
  `RUN-METHOD-NOTES-v2.10.md` before the first run (WAIT 1) and is:
  `pin-claude-code: 2.1.261 (Claude Code)` · `pin-codex: codex-cli 0.153.4` · `pin-model: fable 5`.
  Twelve per-session fingerprints are committed; for all 36 runs the run's `session.txt` names a
  fingerprint commit that **introduced** that block (absent at its parent), touched only the notes
  file, is a strict ancestor of the run-capture commit, and whose field lines byte-equal HEAD's.
  Every `claude-code:` and `codex:` value byte-equals its pin line, every `model:` value full-line
  matches the sealed Claude-5 grammar, and the **normalized model value is `fable 5.1` across ALL
  sessions** — one model, one CLI, no cohort split and no silent aggregation. Both commits that ever
  set a `pin-*` line precede the first fingerprint and every run capture. Had any session drifted,
  the runs would have been split into recorded cohorts and reported separately; **no drift
  occurred, so there is a single cohort.**
- **The codex-cli shift is explicit.** The v2.9 baseline ran **codex-cli 0.133.0**; this baseline ran
  the pinned **codex-cli 0.153.4**. That is an explicit component of the harness shift alongside the
  model-generation change, and the two cannot be decomposed from these runs (see Honest limitations).

## Scoring rules (pre-registered, from the committed key blobs)

- **Catch (should-catch, D-07 three-gate):** SITE (right file + within the planted hunk) AND AXIS
  (the finding names the required MECHANISM, not merely a defect at the right location) AND BAND
  (rendered band ≥ the row's floor). SITE-only, or SITE+AXIS-below-band, = `detected-below-threshold`
  = a MISS in the headline.
- **FP (should-quiet, D-08):** any finding with band **critical OR warning**; medium/low =
  noise-notes (not FPs).

Both rules are read from the sealed key blobs named above, not from a live working file.

## Per-diff baseline — should-catch (catch-rate)

New diffs are baseline-only: they have no prior measurement to compare against.

| # | diff-id | origin | AXIS the finding must name | floor | Observed | Verdict |
|---|---|---|---|---|---|---|
| 1 | triggarr-secret-in-logs | carried | secret/API-key/PII leaked into logs (NOT "log formatting") | warning | catch, catch, catch | **3/3** |
| 2 | triggarr-autoescape | carried | XSS surface re-enabled / autoescape NO-OPs (NOT "deprecation"/"breaks startup") | warning | catch, catch, catch | **3/3** |
| 3 | third-organic-should-catch | carried | unclamped percentage / missing `Math.min(100,…)` clamp | medium | catch, catch, catch | **3/3** |
| 4 | triggarr-session-rotation | new | stale-session survival — password change no longer evicts existing sessions | warning | catch, catch, catch | **3/3** |
| 5 | triggarr-settings-form-split | new | silent data loss on save — General fields no longer submitted | warning | catch, catch, catch | **3/3** |

**Headline catch-rate = 15/15** over the sealed `DENOM_CATCH_RUNS: 15`. Zero
`detected-below-threshold`, zero miss, zero unscoreable.

## Per-diff baseline — should-quiet (false-positive-rate)

| # | diff-id | origin | Safe ON axis (what makes silence correct) | Observed | Verdict |
|---|---|---|---|---|---|
| 6 | should-quiet-1 | carried | SSRF / input-validation — the diff TIGHTENS the host block-list | FP, FP, FP | **3/3 FP** |
| 7 | should-quiet-2 | carried | API contract / typing — `post(url)` widened to `post(url, body?)` | FP, FP, FP | **3/3 FP** |
| 8 | should-quiet-3 | carried | HTTP-client / path-injection / error-handling boundary-add | FP, FP, FP | **3/3 FP** |
| 9 | should-quiet-4 | new | SSRF / input-validation — ADDS `validate_url_ssrf`, tightening the guard | FP, FP, FP | **3/3 FP** |
| 10 | should-quiet-5 | new | log-sanitization / secret-handling — wraps file-name interpolation in `sanitize_log_value` | clean, FP, clean | **1/3 FP** |
| 11 | should-quiet-6 | new | input-validation / config bounds — `shutdown_drain_timeout` with `ge=1.0` | FP, FP, FP | **3/3 FP** |
| 12 | should-quiet-7 | new | settings input-parse path — bounded `safe_float` mirroring the adjacent `safe_int` | FP, FP, FP | **3/3 FP** |

**Headline false-positive-rate = 19/21** over the sealed `DENOM_QUIET_RUNS: 21`. Six of the seven
should-quiet diffs fired a critical or warning in **every** run; should-quiet-5 is the only diff with
any silence (2 of its 3 runs clean), and even its single FP is not about the diff's own lines — it is
an unused-import lint concern in a neighbouring test file.

> Superseded 2026-09-08 — should-quiet-7 excluded by recorded supersession: FP **16/18** over the
superseded quiet denominator (the sealed 19/21 above is the sealed literal and stands); see
`docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md` #001.

Two recurring FP shapes are worth naming, because they are what the noise work has to move:

- **Out-of-diff reach.** should-quiet-2 and should-quiet-5 FP'd on *neighbouring* files (the caller,
  a test file, a mock) rather than the diff's own lines.
- **Feature-incompleteness framing.** should-quiet-6 and should-quiet-7 FP'd on "declared but not
  wired" — the fleet reaches past the diff into whether the surrounding feature is finished. That is
  a scope/axis question, not a defect judgment. should-quiet-6 is the most stable FP in the set: a
  byte-identical codex title at critical/100 in all three runs.

## The Claude 5 re-measure (Fable 5) — v2.9 vs Claude 5, carried 6 only

The section title carries the family the harness pin actually recorded (`pin-model: fable 5`,
normalized `fable 5.1` across every session), not a hardcoded family name.

The six carried diffs are **the only apples-to-apples cell in this document**: the SAME six diffs,
the SAME sealed v2.9 key blob, and the SAME unchanged 2.9.0 plugin as the v2.9 baseline. The six new
diffs have no prior measurement and cannot participate in any comparison. Restricted to the carried
six, the only thing that changed between the two measurements is the **harness** — the model
generation plus the codex-cli version.

| measure | v2.9 baseline (2026-07) | v2.10 baseline (Claude 5 harness) |
|---|---|---|
| catch-rate (carried 6) | **8/9** | **9/9** |
| FP-rate (carried 6) | **6/9** | **9/9** |

| diff-id | v2.9 | Claude 5 (this run) | movement |
|---|---|---|---|
| triggarr-secret-in-logs | 3/3 catch | 3/3 catch | unchanged |
| triggarr-autoescape | 2/3 catch | **3/3 catch** | +1 — the v2.9 right-site-wrong-axis MISS did not recur |
| third-organic-should-catch | 3/3 catch | 3/3 catch | unchanged |
| should-quiet-1 | 3/3 FP | 3/3 FP | unchanged |
| should-quiet-2 | **0/3 FP** (clean, 0 findings all runs) | **3/3 FP** | +3 FP — the largest single movement in the set |
| should-quiet-3 | 3/3 FP | 3/3 FP | unchanged |

**Reading it.** On the identical six diffs, the identical sealed key, and an unchanged plugin, the
model-generation shift moved the false-alarm rate from 6/9 to **9/9** — every carried should-quiet
run now draws a critical or warning. The whole of that movement is should-quiet-2, which produced
zero findings on all three v2.9 runs and now FPs 3/3: the newer harness reaches beyond the changed
lines into the caller (`config.service.ts` still GETs a removed route) and into test-coverage gaps on
the changed method. The catch side moved 8/9 → 9/9, because v2.9's single axis-flapping miss on
autoescape did not reproduce. Both movements point the same way: **this harness says more.** More
words on a real bug reads as a better catch number; the same tendency on clean code reads as a worse
FP number, and on this set the FP arm is where the movement is unambiguous — one carried diff going
from perfectly silent to alarming on every run. The catch improvement (+1 run) is within what N=3 can
produce by chance; the FP regression (+3 runs, all on one diff, deterministic across three runs) is
not so easily dismissed. **The harness is the variable, and it moved in the noisier direction.**

## Pass bar (sealed — evaluated in Phase 43, not evaluated here)

Quoted from the sealed seal-1 blob of `docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md`:

> v2.10 FP-rate on the full grown set ≤ ½ × the SET-03 baseline FP-rate, AND catch-rate on the same
> diffs no worse than baseline.

> **Decision rule (sealed at seal-1, evaluated in Phase 43, not this phase):** At most ONE retune, on
> failed diffs only (×3); whether it was used or not is recorded.

Combining the sealed bar with the baseline measured above, the IMPLIED literal targets for Phase 43,
over the sealed denominators `DENOM_CATCH_RUNS: 15` and `DENOM_QUIET_RUNS: 21`, are:

| arm | baseline | implied v2.10 target |
|---|---|---|
| FP-rate (full grown set) | 19/21 | **≤ 9/21** (½ × 19/21 = 9.5/21; ≤ ½ means at most 9 of the 21 quiet runs may fire a critical/warning) |
| catch-rate (same diffs) | 15/15 | **≥ 15/15** — "no worse than baseline" means the catch arm has zero headroom: any single catch lost fails the bar |

**The bar is NOT evaluated in this phase.** These targets are recorded now, from the pre-change
baseline, precisely so that Phase 43's evaluation cannot be tuned to a number chosen after the fact.
Phase 43 evaluates; this document only anchors.

## Honest limitations

1. **Small N.** N=3 per diff (15 catch runs, 21 quiet runs). This cannot support fine thresholds or
   stable rates — a single run flipping moves a diff's fraction by 1/3. Every number here is coarse
   by construction. The set is twice v2.9's size, which helps the aggregate, but not the per-diff
   resolution.
2. **Three repos, twelve diffs.** triggarr, seedsyncarr (including its Angular front-end), and
   roonseek — the owner's own stack, not a broad multi-project or multi-language trial. Four repos
   were mined under D-03, but the fourth (dashboard) yielded no qualifying candidate, so the
   measured set draws on three. It measures these defect classes on these repos; it does not
   measure recall across the whole surface.
3. **Organic-only sourcing.** Diffs are real shipped commits (fail-closed provenance regex), which
   keeps the test honest but constrains the set to defects that actually shipped-then-fixed (or
   shipped-clean) — not an adversarially designed difficulty curve. The reversed-diff construction
   for should-catch rows is itself recognizable as a revert in some runs.
4. **Single threshold.** These are `/deep-review` runs (surface cutoff ≥70), not `/review` (≥80).
   The FP-rate in particular would differ at the stricter `/review` bar.
5. **The harness bundles model + CLI versions, and the re-measure cannot decompose them.** The
   pinned tuple proves ONE harness across all 36 runs (single `fable 5.1` cohort, byte-equal
   claude-code and codex pins on every fingerprint), which is what makes the v2.9 comparison a clean
   *single* shift rather than an average over mixed conditions. But that shift contains **two**
   changes at once: the model generation AND codex-cli 0.133.0 → 0.153.4. These runs cannot say how
   much of the 6/9 → 9/9 FP movement belongs to which. It is a harness shift, reported as one.
6. **Self-scored against a sealed key.** The scoring was done by the assistant, not an independent
   party. What is independent is the *key* (committed and digest-sealed before any run, read only
   from git blobs) and the gate ladder (nine fail-closed gates derived from git history). The
   judgment of whether a given finding "names the mechanism" is still a human-ish call recorded in
   the worksheet for audit, not a mechanical string match.
7. **Pinned-base scope.** Every diff was reviewed against its recorded `base_sha` tree, not the
   repo's live HEAD. A scope-bound of the ground-truth method, not a tool defect.
8. **Driver split across the campaign.** Runs 1-10 were owner-pasted from the run checklist; for
   runs 11-36 the assistant executed the checklist blocks (fence-validated, byte-exact) at explicit
   owner direction, with the owner performing session launch, `/model`, `/clear`, `/deep-review`, and
   the fix-loop decline. The artifacts are identical in form either way and the gate ladder is the
   independent check — but the campaign was not uniformly owner-driven, and that is recorded rather
   than smoothed over.
9. **Tool-side nondeterminism observed during the campaign (Phase-40 input, not scoring defects).**
   On 3 of the 36 runs the shipped command wrote state to `<repo>-HEAD.json` / `<repo>-main.json`
   instead of the expected detached-key `<repo>-.json`; each was captured via a recorded one-line
   `STATE_FILE` substitution with both block digests logged, never a re-run or a hand edit. The
   pass-level codex record is schema-nondeterministic across passes of the same shipped command (≥6
   shapes observed, including a plain string and outright absence *with* a codex-adversarial finding
   present) — codex participation is therefore inferred from `findings[].agent`, and the "7 of 21"
   figure inherits that inference. One archived finding carries an empty `title` and was scored on
   file:line + explanation. Codex results were collected via an output-file fallback on some runs
   after the deprecated TaskOutput reader failed.
10. **An advisory docs-only drift exists against tag v2.9.** `git diff v2.9 -- plugins/vibe-check/`
    is not empty: it contains `docs/efficacy/ULTRAREVIEW-SHADOW.md`, a non-executable backlog/status
    document added during the phase. The *measured* surface is unchanged — excluding
    `docs/efficacy/`, the diff against tag v2.9 is empty — and independently, all 12 committed
    fingerprints record `cache-root: …/thejuran/vibe-check/2.9.0`, so every run resolved its helpers
    from the installed 2.9.0 cache rather than the repo tree. Noted here so a re-deriver is not
    surprised by a non-empty diff.
11. **No D-04 shortfall and no owner waiver.** All 36 slots are filled, zero unscoreable, zero holes.
    Nothing in this baseline rests on a partial denominator.

## Plain-language summary (for the owner)

We now have a proper before-picture, taken on the *unchanged* tool. We ran the reviewer on twelve
real diffs from your own repos — five that hide a genuine bug (a leaked API key in the logs, a lost
XSS protection, a progress bar that can read over 100%, a password change that no longer kicks out
old sessions, and a settings form that silently drops half the fields when you save) and seven that
are perfectly fine changes — three times each, thirty-six runs in total, all scored against answer
keys we locked and cryptographically sealed BEFORE any run happened.

**On the buggy diffs it caught the bug in all 15 of the 15 runs.** Every planted bug, every run. As a
safety net for real problems, this is as good as the measurement can show.

**On the clean diffs it raised a false alarm in 19 of the 21 runs.** Only one of the seven clean
diffs was left alone in any run (two of its three runs were silent, and its single alarm was about an
unused import in a *different* file). The other six drew a critical or a warning every single time.
That is the problem this milestone exists to fix, and it is now measured rather than suspected.

**The part that matters most: we re-measured the six diffs from last time on the exact same
unchanged tool, and the false alarms got worse, not better.** Last measurement: 6 false alarms out of
9 clean runs. This measurement: **9 out of 9** — every clean run now draws an alarm. The entire
increase comes from one diff that was completely silent all three times before and now fires all
three times. The tool did not change; only the model and CLI versions underneath it did. On the
buggy side the same shift nudged us from 8 out of 9 to 9 out of 9, which is one run's worth of
movement and could easily be luck. The honest reading is that the newer model *says more* — which
flatters the catch number and hurts the false-alarm number, and the false-alarm side is where the
evidence is strongest.

**What happens next:** we already sealed a target before taking this picture — cut the false alarms
at least in half (to at most 9 of the 21 clean runs) without losing a single catch. We are NOT
judging against that target in this phase; that judgement is deliberately held for later so nobody
can be accused of picking a bar that the result happens to clear. This document is the anchor
everything after it gets measured against.

---

# B3 v2.10 — Phase 41 Wave 1 (scorer) replay + spot-check

**Headline: guardrail 25/26 protected catches kept under the combined Wave 1 (the 26th AMENDED per ledger 008, REGRESSED 0) · replay-predicted FP runs 16/18 → 14/18 · live spot-check 3/6 firing vs 5 predicted (PASS)** (no rounding — exact fractions).

Wave 1 changes only the scorer (`scripts/score.py`), not any agent prompt. Each of the three
changes was replayed offline against the archived B3 runs before it landed, then the combined
scorer was checked live on a pair of clean diffs, six runs in total. Every number below is
transcribed from the committed replay reports and from
`docs/design/b3-ground-truth/runs-v2.10-phase41/final/PASS.json`, never re-derived here. The sealed
pass bar (halve the false alarms, lose no catch) is **not evaluated** in this section. It is judged
once, in Phase 43, after both waves.

## What changed (Wave 1, scorer only)

**B-SEV — no red critical from a single lane** (`c02d9b1`; alone: `docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-sev.md`).
A finding group that has no second opinion is capped at the critical floor minus 1 (94 by default),
so it bands Warning at most. A second opinion is Codex in the group while the envelope's
`codex.status` is `joined`, or the finding persisting from an earlier pass. Warning still blocks
finalize, so the cap lowers a label and never drops a finding.

**B-REWEIGHT — derived, lower-only confidence offsets per agent** (`0ee3818`; alone:
`docs/design/b3-ground-truth/REPLAY-REPORT-phase41-b-reweight.md`). Offsets come from each agent's
labeled precision on the archived runs, shrunk toward the pool, and only ever lower confidence.
Transcribed from `docs/design/b3-ground-truth/CALIBRATION-v2.10.md` § Derived offsets:

| agent | offset | labeled n (TP / FP) |
|---|---|---|
| impact | −12 | 50 (24 / 26) |
| architecture | −6 | 12 (6 / 6) |
| bugs | −2 | 35 (22 / 13) |
| codex-adversarial, compliance, security | 0 (above the pool; lower-only) | 22 / 7 / 17 |
| framework-fastapi, language-typescript | 0 (n = 2 < 5, thin data) | 2 / 2 |

**H-LANE — one row per site, every lane listed** (`ccf69fc`; alone:
`docs/design/b3-ground-truth/REPLAY-REPORT-phase41-h-lane.md`). Findings at the same site (same
file, ±2 lines, any category) collapse into one row that carries a `members` list of every lane
that raised it. The +10 cross-confirm bonus now fires only for a Codex member plus a Claude-lane
member while Codex joined (D-01). Two Claude lanes agreeing is not an independent second opinion.

The formula freeze lifted for exactly these three changes (`templates/scoring.md` § Wave 1). No
other constant moved; GOLDEN_DIGEST unchanged.

## Replay method and fidelity (D-07)

`scripts/replay.py` re-scores the archived runs through the baseline scorer blob (`b21f7f3d…`) and
through each candidate. From `docs/design/b3-ground-truth/REPLAY-REPORT-phase41-baseline.md`:
**56/66 exact** — 56 of the 66 scoreable archived runs are reproduced byte-exact by the baseline
replay. The 10 drift runs, by path:

- `runs-v2.10/should-quiet-1/run-2`, `runs/should-quiet-1/run-2`, `runs/should-quiet-1/run-3`,
  `runs-v2.10/triggarr-settings-form-split/run-2`, `runs/triggarr-secret-in-logs/run-1`,
  `runs/triggarr-secret-in-logs/run-2` — score/band moved
- `runs-v2.10/should-quiet-7/run-1..3` — archived row not re-emitted
- `runs/should-quiet-3/run-2` — stable_hash only (band and score multisets agree)

Three causes sit behind the drift: the orchestrator set `in_diff` inconsistently in some archived
runs; v2.9-era runs were grouped differently from today's scorer; and absorbed members were never
archived. Every candidate is therefore compared against the **baseline replay**, never against the
recorded bands. 12 of the 66 runs carry a session transcript (the Phase-40 archives); the other 54
carry survivors only, so the findings the original scorer absorbed or dropped are unrecoverable for
them. Deferred to the Phase-43 runbook: archive the raw agent envelopes per run so replays stop
depending on transcripts.

## Per-candidate replay (alone and combined)

Transcribed from `REPLAY-REPORT-phase41-{b-sev,b-reweight,h-lane,combined}.md`. The headline FP
set is Phase-38 should-quiet-1..6 ×3. Firing-row counts are over all replayed runs; the baseline
firing set is 84 rows (44 critical / 40 warning, from the 41-04 record).

| candidate | overrides | guardrail kept/26 | REGRESSED | UNEVALUABLE | headline FP baseline → candidate | critical/warning rows before → after |
|---|---|---|---|---|---|---|
| b-sev | `{}` (scorer at `c02d9b1`) | 25/26 (+1 AMENDED) | 0 | 0 | 16/18 → 16/18 | 44 / 40 → 3 / 81 |
| b-reweight | `{"LONE_LANE_BAND_CEILING": null}` | 25/26 (+1 AMENDED) | 0 | 0 | 16/18 → 14/18 | 44 / 40 → 32 / 28 |
| h-lane | `{"AGENT_CONFIDENCE_OFFSET": {}, "LONE_LANE_BAND_CEILING": null}` | 25/26 (+1 AMENDED) | 0 | 0 | 16/18 → 16/18 | 44 / 40 → 28 / 27 |
| combined | `{}` | 25/26 (+1 AMENDED) | 0 | 0 | 16/18 → 14/18 | 44 / 40 → 8 / 27 |

Only B-REWEIGHT moves the per-run FP rate. H-LANE collapses rows (84 → 55 alone, 84 → 35 combined)
without quieting a run, and B-SEV recolors critical → warning without quieting a run. Phase-40
should-quiet-5 stays **0/6 → 0/6** and the informational v2.9 quiet set **6/9 → 6/9** under every
candidate.

> Planned vs observed: the research predicted a combined headline of 12/18; the replay measured
14/18, because the committed derivation gives smaller offsets (impact −12, not the indicative −18).
Recorded as observed, not tuned (D-08).

## Guardrail basis

The guardrail runs on the strict-axis basis of `docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md`
entry 007: a collapsed row counts as a catch when any member's title names the bug, not only the
row's leading title. Under the combined candidate, 7 of the 25 kept catch runs are kept on the
`member-title` basis (`REPLAY-REPORT-phase41-combined.md` § Guardrail). The baseline replay
reproduces 25 of the 26 protected catches; the 26th, `runs/triggarr-secret-in-logs/run-2`, is
AMENDED under ledger entry 008 (its archive is too thin to reconstruct) and passes through the
guardrail unchanged. The sealed catch verdicts are untouched. Fidelity drift is disclosed in the
method section above; it never removes a catch from the guardrail (D-05).

## Live spot-check (SCORER-05)

The pair was chosen by the D-16 rule from the combined replay
(`docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase41.md` §3):

| diff | baseline-replay fired /3 | combined fired /3 | movement | picked? |
|---|---|---|---|---|
| should-quiet-1 | 3/3 | 3/3 | 0 | **yes** (0-movement tie; lowest number) |
| should-quiet-2 | 3/3 | 3/3 | 0 | no |
| should-quiet-3 | 3/3 | 2/3 | **1** | **yes** (largest movement) |
| should-quiet-4 | 3/3 | 3/3 | 0 | no |
| should-quiet-5 | 1/3 | 0/3 | 1 | no (already 0/3 post-diet) |
| should-quiet-6 | 3/3 | 3/3 | 0 | no |

**Predicted FP count for the 6 runs = 5** (should-quiet-3 2/3 + should-quiet-1 3/3), fixed before
run 1. The runs used the immutable snapshot `batch4-cd8f5b00de73` (commit `cd8f5b00`), Claude Code
2.1.281, Fable 5.1, codex-cli 0.153.4. Per run, from `final/PASS.json` and each run's `state.json`:

| diff | run | fired? | firing rows (agent band score) | codex | replay-agreement (info) |
|---|---|---|---|---|---|
| should-quiet-3 | 1 | no (clean) | none | joined (approve) | agrees (predicted quiet) |
| should-quiet-3 | 2 | no (clean) | none | skipped (`unavailable`) | disagrees (predicted firing) |
| should-quiet-3 | 3 | no (clean) | none | skipped (`unavailable`) | disagrees (predicted firing) |
| should-quiet-1 | 1 | yes (fp) | bugs critical 100, security warning 88 | joined (needs-attention) | agrees |
| should-quiet-1 | 2 | yes (fp) | impact critical 100 | joined (needs-attention) | agrees |
| should-quiet-1 | 3 | yes (fp) | bugs warning 94, security warning 89 | joined (approve) | agrees |

**Observed 3/6 firing vs predicted 5 → PASS (D-11).** D-12 was not needed. Every surviving row in
all six runs carries `members`, confirming the Wave-1 scorer was live. Both criticals include a
Codex member while Codex joined, the one path B-SEV allows. Per-run agreement with the replay is
information, not the gate.

- **Codex condition.** Codex joined in 4 runs and was skipped (`unavailable`) in should-quiet-3
  runs 2 and 3. Under Claude Code 2.1.281 the `BashOutput` launch gate makes Codex joining depend
  on the session's improvisation (a Phase-40 deferred item). The prediction assumed the archived
  Codex condition. The two skipped runs are both quiet, but should-quiet-3 run 1 is quiet with
  Codex joined, and should-quiet-3 is not a Codex-driven diff, so the skips do not explain the
  result on their own.
- **`state_shape` waiver (ledger entry 009).** Five runs record `state_shape: FAIL` for one reason
  only: the state file is missing the root key `medium_acknowledgments`. The persist prose never
  told the model to create that key on a new state file, so its presence was luck; this gap
  predates Wave 1. The key is outside the measured quantity (the FP rule reads only the bands of
  `passes[-1].findings`). By owner decision on 2026-09-29 the runs count, the recorded FAILs stay
  in `PASS.json`, and `batchsnap.py check-pass` exits non-zero on this artifact by design (its only
  reasons are those five failures). See `docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md` entry
  009. The persist prose is fixed in the same plan (41-08), with a test that locks the new-state
  root to the schema.
- **Launch line.** The sessions were started with `--model claude-fable-5-1` added to the
  runbook's launch line, because the pin is Fable 5 and the owner's default model had changed.
  The fingerprint blocks record `model: Fable 5.1`, matching the pin.
- **Context pressure.** Each run's session ran near 96–100% of the 200k context window. No run was
  cut short, and each wrote a complete state and report, but the review ran close to its ceiling.
- **Voided attempt.** should-quiet-3 run 3's first attempt was voided before any review ran (Fable
  usage credits exhausted) and redone. Its empty auto-memory evidence folder was kept, renamed
  `roonseek-written-before-sq3-run-3-voided-attempt`.

## Honest limitations

- **No Wave-1 FP target (D-08).** The sealed halving bar is **not evaluated** here. It is judged in
  Phase 43, after both waves, on the full ×3 set. The replay's 14/18 and the live 3/6 are evidence
  about direction, not a verdict against the bar.
- **The prediction is pre-diet (Pitfall 5).** The replay re-scores Phase-38 runs, whose agents ran
  the pre-diet prose. The live runs ran the post-diet (Phase 40) prose plus Wave 1. should-quiet-3
  going 0/3 against a 2/3 prediction therefore cannot be credited to the scorer alone.
- **should-quiet-6 is untouched by design.** Its byte-identical Codex critical in all three
  baseline runs stays firing (now warning 94): D-01 keeps Codex as the independent voter. Whether
  Codex's own contract should be ceilinged is Wave 2's question.
- **Two agent-side FP shapes remain.** Out-of-diff reach and feature-incompleteness framing are
  prompt problems for Phase 42; a scorer cannot fix them without guessing.
- **Labels are a lower bound on precision.** Only axis-qualifying findings on catch runs count as
  TP, so every agent's precision is undercounted (`CALIBRATION-v2.10.md` § Undercount).
- **Small N.** Six live runs over two diffs.
- **Harness confound.** Claude Code 2.1.281 vs the 2.1.261 baseline pin (ledger 006) remains a
  named confound. Auto-memory was parked for these runs, while the Phase-38 baseline ran with
  memory active.
- **Codex was skipped in 2 of the 6 runs** (see above). Recorded, not voided (D-13).

## Plain-language summary (for the owner)

This phase changed only how the tool scores what its reviewers say, not what the reviewers look
for. Three rules changed. A single reviewer can no longer raise a red "critical" on its own; it
needs Codex agreeing, or the problem to still be there on a second pass. Reviewers that have been
wrong a lot in the past (the "impact" and "architecture" reviewers especially) get their
confidence trimmed by an amount worked out from their track record, not picked by hand. And when
several reviewers flag the same line, you now get one row that lists all of them instead of three
near-duplicate rows.

**Nothing we already catch was lost.** We replayed every archived run that caught a real bug
through the new scoring. All of them still catch it (one old run is too thinly archived to replay
and is recorded as such).

**On paper, false alarms went from 16 of 18 clean runs to 14 of 18.** Almost all of that comes
from the confidence trimming. The other two rules make the report quieter and less alarming (far
fewer red criticals, far fewer duplicate rows) but do not by themselves turn a noisy run into a
silent one.

**Then we checked it for real: 3 of 6 fresh runs raised an alarm, against a prediction of 5.** The
roonseek diff went completely quiet in all three runs (predicted: quiet in one). The triggarr diff
still fired all three times, as predicted; its alarms are driven by the "bugs" reviewer, which has
a good track record, so the new scoring deliberately leaves it alone. That clears the check we set
before the runs.

Some caveats. Codex failed to join in two of the six runs. Five of the six saved results were
missing a bookkeeping field unrelated to the alarm count; you decided to count them, the decision
is on the record (ledger entry 009), and the underlying bug is fixed. The sessions ran very close
to their memory limit. And the fresh runs also carry the earlier prompt slimming, so not all of
the roonseek improvement can be credited to this phase.

**What happens next:** Wave 2 changes the reviewer prompts themselves, to go after the alarms the
scoring cannot touch, such as reviewers reaching outside the diff or complaining that a feature
is unfinished. Then Phase 43 runs the full set three times and judges the result against the
sealed target for the first time.

# B3 v2.10 — Phase 42 Wave 2 (prompts and one launch gate) pre-registration

**Headline: no measurement in this section.** Wave 2 changes reviewer prompts and orchestrator
prose, plus one launch-gate fact and slug in `scripts/codex_gate.py` (no scorer change). It is
written down here, before any Phase 43 run, so that the Phase 43 comparison can be
read honestly: what changed, which change can move the catch rate as well as the false-alarm rate,
which false alarms are expected to remain, and what must be true before a measured run starts.
The sealed pass bar is **not evaluated** here. It is judged once, in Phase 43.

## What changed (Wave 2, prompts plus one launch gate)

- **A shared "Safe-change recognition" block in the bugs, security and impact prompts.** When a
  diff *tightens* a control (it reduces what can get through), the lane treats it as presumptively
  safe **on that axis**. Four generic classes are named: adding an allowlist/denylist validator on
  an input, wrapping output in an existing sanitizer or escaper, adding a bound or finite-only
  check to a numeric field, and routing an input through an existing clamping/parse helper.
- **A sensitive-area ceiling.** A finding whose only basis is that the changed code touches a
  sensitive area (auth, secrets, SSRF, injection, logging, validation, serialization), with no
  defect demonstrated
  on a changed line, is still reported, but capped at `agent_confidence ≤ 45` with
  `severity: low` and a note saying what would demonstrate it.
- **The lift condition.** The cap lifts only for a concrete bypass: a specific input AND the path
  by which it defeats the new check, cited at `file:line`. A bypass the pre-change code equally
  allowed, in a case the diff never addressed, is a pre-existing gap and stays capped. A
  demonstrated failure of the new control's intended protection is exempt from that rule and lifts
  the cap.
- **Removal or loosening IS a defect when a protected path is left without the control.** A diff
  that removes, reverts, loosens, disables or bypasses a control, or makes it depend on fragile or
  version-dependent configuration, IS a demonstrated defect on a changed line when a path the
  control used to protect is left without it. It is reported at honest confidence; the ceiling does
  not apply. A control moved rather than lost is judged by what the reviewer FOUND, not by what the
  diff claims, and the moved-control rule has exactly three branches. A same-purpose replacement is
  code at `file:line` (shared middleware, a decorator, a schema or an upstream layer) that guards
  the same property as the removed check.
  (1) **No same-purpose replacement found and read** — including when only a comment, docstring or
  commit message asserts a move, or when the only code found guards a different property (logging
  or rate-limiting middleware for a removed auth check): the removal rule applies at honest
  confidence; no cap. A move claim in the diff text is never evidence of a replacement.
  (2) **A same-purpose replacement found and read, and the reviewer can trace a formerly protected
  path that bypasses it:** that is a demonstrated protection loss, reported at honest confidence
  with no cap. Demonstrated loss always takes precedence over the cap.
  (3) **A same-purpose replacement found and read whose coverage of every formerly protected path
  remains unverified:** the removal is reported as a capped note (`agent_confidence ≤ 45`,
  `severity: low`) with `pending: confirm <file:line> covers every path the old check guarded`.
  (In the Codex literal, branch 3 is reported at or below 0.45 confidence with severity low, and
  Codex is told to "say to confirm that file:line covers every path the old check guarded" — a
  different wording from the Claude lanes' `pending:` line; branches 1 and 2 are reported at honest
  confidence with no cap.) A branch-3 note on its own scores below the report threshold, so it is
  filtered: it is not listed as a row, but it still counts in the report's Filtered summary. It can
  reach exactly 70 (Medium: listed, acknowledgeable, never Warning) only when, in the earlier pass,
  it rode as a member of a listed row at the same site, and that row then persists into a later
  pass while Codex independently flags the same site again while joined — as `TestTwoPassCeiling`
  in `scripts/test_agent_prompts.py` proves (persisted without Codex re-corroboration, it scores 60
  and is filtered). The note's text (its `pending:` line) survives only in the raw per-lane outputs
  (the agent envelopes and Codex output).
- **Security confidence anchors.** The security prompt gets the calibrated confidence scale the
  bugs and impact prompts already had, so the ceiling sits on a defined scale.
- **A fixed Codex calibration literal.** `phases/deep-review/2c-codex-kickoff.md` reads
  `CODEX_FOCUS` byte-for-byte from the fixed file `templates/codex-focus.txt` (skipping the launch
  if it cannot be read) and passes it as the last argument to the Codex
  `adversarial-review` call. It carries the same safe-change rule and ceiling, in Codex's own
  confidence unit (`≤ 0.45`), phrased as calibration rules for every finding rather than a focus
  area.
- **A Codex launch-gate fact for the focus file.** `scripts/codex_gate.py` gained a
  `focus_readable` fact and a tenth sealed skip slug, `focus-unreadable`: the kickoff checks that
  `templates/codex-focus.txt` can be read before the disclosure line, and when it cannot, Codex is
  skipped with that slug rather than launched without its calibration text. This changes when
  Codex runs, not how any finding is scored.
- **The stale +10 prose sweep (D-06).** Prompt and orchestrator prose that still described the
  retired same-domain +10 rule now matches the Phase-41 scorer: grouping is by site only, and +10
  fires only for a Codex member plus a Claude-lane member while Codex is joined.
- **Unchanged (R7):** `scripts/score.py`, `scripts/test_score.py`, `scripts/config.py` and
  `scripts/codex_translate.py`. The Codex translation stays verbatim; no scorer constant moved.

## Pre-registered confound (before any Phase 43 run)

**The Codex focus text changed in Phase 42.** The companion injects `CODEX_FOCUS` into Codex's
prompt on EVERY diff, not only on the quiet ones. So it can move catch-diff results as well as
quiet-diff results. Codex matters on the catch side: 21 of the 26 protected catch runs carry a
Codex member, and in 2 v2.9 runs Codex is the only lane that names the right axis.

Therefore: **any catch regression in Phase 43 must be examined against this change first**, before
it is attributed to the Claude-lane prompt changes, the Phase-41 scorer, or run-to-run variance.
Phase 43's single allowed retune (D-03) is the safety net if the focus text turns out to narrow
Codex's attention. No offline replay can predict this effect, because replays re-score archived
findings and cannot re-run Codex against a new prompt (D-08).

**The removal rule gained a moved-control qualifier in Phase 42.** Removal or loosening is a
defect at honest confidence when a protected path is left without the control. The qualifier keys
on what the reviewer found, in exactly three branches: (1) no same-purpose replacement found and
read — including when a comment, docstring or commit message merely asserts a move, or when the
only code found guards a different property than the removed check (logging or rate-limiting
middleware for a removed auth check) — leaves the removal at honest confidence, uncapped; (2) a
same-purpose replacement found and read, with a traced formerly protected path that bypasses it,
is a demonstrated protection loss at honest confidence, uncapped (demonstrated loss always takes
precedence over the cap); (3) only a same-purpose replacement found and read whose coverage of
every formerly protected path remains unverified is capped (`agent_confidence ≤ 45`,
`severity: low`, with `pending: confirm <file:line> covers every path the old check guarded`).
This qualifier is in the bugs, security and impact prompts AND in the Codex focus text (at or
below 0.45 confidence with severity low for branch 3 only), so it reaches every Claude lane that
carries the safe-change block and Codex on every diff. It can move results in both directions:

- **Catch diffs.** These are, for the most part, literally removals or loosenings of a control. A
  lane that finds a real same-purpose replacement but cannot trace the path that bypasses it
  (branch 3 where branch 2 was true) would cap a real removal at `≤ 45` / `severity: low` —
  filtered alone (not listed as a row, but counted in the Filtered summary); it reaches at most
  70 (Medium, never Warning) only when it rode as a member of a listed row at the same site in the
  earlier pass and that row then persists with Codex re-corroborating the site while joined.
- **Quiet diffs.** A genuine relocation of a check into middleware, a decorator or a schema now
  emits a capped note rather than nothing, which is normally filtered (counted in the Filtered
  summary, not listed) but can surface as a Medium row under the same ride-along, persisted and
  re-corroborated path.

Therefore **any catch regression or new quiet-diff row in Phase 43 must also be examined against
this qualifier**, alongside the Codex focus change, before it is attributed to anything else. To
audit it, look in the raw per-lane outputs (the agent envelopes and the Codex output — a filtered
note is only counted in the report's Filtered summary; its text is not listed) for the Claude-lane
form
`pending: confirm <file:line> covers every path the old check guarded` and, additionally, the
Codex form, which words it as confirming "that file:line covers every path the old check
guarded" with no `pending:` prefix.

## Expected residuals (not claimed as fixed)

- **should-quiet-6 (feature-incompleteness framing).** The dominant alarm is "declared but never
  wired": a value added in one step of a staged change whose consumer is not in the diff. It is a
  concrete claim, not a sensitive-area note, so the ceiling does not touch it. The owner scoped it
  out of Phase 42; it is recorded as backlog 999.19. Expected: should-quiet-6 likely stays 3/3.
- **should-quiet-1 (pre-existing bypass framing).** Its recurring alarms name concrete inputs the
  pre-change code equally allowed. Those are now capped as pre-existing gaps, but no live run has
  confirmed the lanes follow that rule.
- **should-quiet-4 (the tightening's intended consequence flagged on another axis).** "The new
  validator rejects a value the old code accepted" gets a consequence-of-tightening clause; our
  confidence that this clears it is MEDIUM. The broader "stricter validator breaks a legacy
  config" class is also in backlog 999.19.
- **How loud a capped note can get.** Capped notes carry `severity: low`. A Claude note at ≤ 45
  paired with a Codex note at ≤ 45 while Codex is joined scores 55, which is filtered (not the 75 /
  Medium the research first computed at critical severity). The worst reachable path is a capped
  note carried as a member of a surviving row, then persisted AND re-corroborated on the next pass:
  it tops out at 70, the Medium floor, which is acknowledgeable and never Warning.
  `scripts/test_agent_prompts.py` proves this by driving the real scorer over two passes.

## Phase-43 pre-flight carries

- **Resync the installed plugin cache and relaunch before any measured run.** Agents dispatch from
  the installed cache, not the repo, so the Wave-2 prompts are inert until the cache is resynced
  and the process relaunched. Verify the installed version matches the repo before the first
  session.
- **Standing carries from Phase 41** (`41-deferred-items`): fix the Codex `BashOutput` launch gate;
  put the `--model` pin into the runbook's launch line; archive the raw agent envelope per run; add
  a voided-attempt step to the runbook; check context headroom before the ×3 sessions and record
  it in the fingerprint block.

## Honest limitations

- **No live spot-check in Phase 42 (D-08).** Prompt changes cannot be replayed offline, and the
  owner-run budget is reserved for Phase 43's full ×3 measurement.
- **Prompt-lock tests prove presence of wording, not model behavior.** The Phase-42 tests show that
  each loud lane carries the rule, the ceiling, the lift condition and the classes, that no B3
  identifier leaked into a prompt, and that no stale +10 prose remains. They cannot show that a
  model obeys the wording. Only Phase 43 can.
- **The Codex focus change is a confound** on both catch and quiet diffs (see above).
- **The moved-control qualifier (three branches: no same-purpose replacement found, or a traced
  bypass of one, leaves the removal uncapped; only unverified coverage of a same-purpose
  replacement caps it) is a confound** on catch and quiet diffs for every lane that carries it,
  Claude and Codex alike (see above).
- **A misjudged real replacement is nearly invisible.** A reviewer that finds and reads a real
  same-purpose replacement but misses the path that bypasses it leaves only a capped note, which is
  usually filtered — counted in the Filtered summary, not listed — and whose text survives only in
  the raw per-lane outputs. Making that case visible in the report would need a
  scoring or report change, which is out of scope for this prompt-only phase; it is carried to the
  v2.11 backlog.

## Plain-language summary (for the owner)

This phase changed what the reviewers are told, not how their findings are scored. The main new
rule: when a change makes a check stricter, reviewers should not raise a loud alarm just because the
area is sensitive; they can leave a quiet note unless they can show exactly how the new check is
beaten. Removing or weakening a check is still treated as a real problem.

One change needs flagging before the big measurement: Codex now gets a short fixed instruction on
every review, including the reviews where we expect it to catch a real bug. If Phase 43 shows a
lost catch, that instruction is the first suspect. Two kinds of false alarm ("this setting isn't
used yet" and "the stricter check rejects an old value") were deliberately left for later, so at
least one clean diff is expected to keep raising an alarm.

## Phase-43 retune pre-registration

**Written before any retune run.** The Phase-43 first pass missed the sealed bar on the catch arm
alone (quiet 6/18 against ≤ 8, so that arm passes; catches 13/15 against 15/15, a miss). The one
allowed retune changes prompts only: the shared Safe-change recognition block in the bugs,
security and impact prompts, and the Codex calibration literal `templates/codex-focus.txt`. The
scorer and the five frozen scoring files do not change. Only the three failed diffs are re-run, ×3
each: should-quiet-4, should-quiet-6 and triggarr-autoescape. Every other diff keeps its first-pass
runs in the combined headline.

**What changed: two rules, each worded as an abstract class (no B3 names, paths or code).**

1. **A guarantee made conditional is a loss even if it holds today.** The new rule says that
   replacing a protection that held unconditionally with one that holds only through a library
   default, a deprecated path, or the currently installed dependency version is a loss of that
   guarantee. This applies even when the reviewer verifies that the protection still works
   today. Such a finding is reported at honest confidence, not under the sensitive-area cap. Its
   title names the attack the control prevents once the protection lapses, for example
   injection, script execution or data exposure. A revert, deprecation or startup symptom alone
   is not enough.
   - **Targets:** triggarr-autoescape runs 1 and 2. In those runs every lane verified that the
     locked dependency still escapes output, rated the change "no demonstrated defect", and
     titled it as a revert, a deprecation or a startup crash. Codex run 1 approved.
   - **Wording:** the removal rule already listed "makes it depend on fragile or
     version-dependent configuration". Its condition "a path … is left without it" read as false
     once a lane had verified the current version. The new sentence closes that reading.
2. **A bypass inside an existing helper that the change only calls is a pre-existing gap.** When
   the new check calls an existing validator or helper, and the bypass lies in that helper's
   unchanged logic, the bypass is a pre-existing gap. Every existing caller of the helper already
   has it. It is reported under the cap with the bypass input named. The cap still lifts when
   the diff's own changed lines let the input through, so the Phase-42 exemption ("an input the
   new check is written to block and demonstrably fails to block") stays for logic the diff
   writes itself.
   - **Targets:** should-quiet-4. All three runs carried a Codex-led critical claiming that an
     alternate numeric spelling of the metadata address passes the new block. Codex located the
     failing logic in the unchanged helper, and the diff only calls that helper at a new point.
     Under the Phase-42 wording that claim lifted the cap.

**Expected effect per failed diff (pre-registered):**

| diff | first pass | expected after retune | confidence | why |
|---|---|---|---|---|
| triggarr-autoescape | 1/3 catch | 3/3 catch | MEDIUM | Rule 1 targets the observed mechanism directly. The risk is that lanes still title the startup symptom first. |
| should-quiet-4 | 3/3 fired | ≤ 1/3 fired | MEDIUM | Rule 2 caps the observed bypass claim. A lane may still rate the claim high if it judges the helper call as the diff's own logic. Separate members on other axes (startup traceback, medium severity) are expected to stay at or below the Medium band. |
| should-quiet-6 | 3/3 fired | 3/3 fired (unchanged) | HIGH | Not targeted. "Declared but never wired" remains the pre-registered expected residual (backlog 999.19). |

**What decides the combined verdict.** The quiet arm already passes, and the retune can only keep
it at or below 6/18 on these diffs. So the combined verdict is PASS only if triggarr-autoescape goes
3/3. A 2/3 result leaves the catch arm at 14/15, a MISS.

**Disclosed limits:**

- **Tune-vs-measure overlap.** The retune was designed after seeing these same diffs fail, so
  the untuned first-pass numbers remain the cleaner estimate. Both are reported.
- **Unmeasured side effects.** The other nine diffs are not re-run. If Rule 1 or Rule 2 would
  move them, the combined headline cannot show it. Rule 1 could plausibly add loud findings on
  diffs that rely on a library default. Rule 2 could quiet a real bypass of a helper on a future
  diff. That bypass would still be reported, but as a capped note that is normally filtered.
- **Confound order is unchanged.** Any surprise in the retune runs is examined first against
  these two sentences, then against the Phase-42 focus text and moved-control qualifier.

---

# B3 v2.10 — Phase 43 post-change measurement (PROVE-01/02/03)

## Headline

**PASS** — false alarms 16→3 of 18 (corrected cohort, bar ≤ 8; should-quiet-7 excluded per SUPERSESSIONS-v2.10.md #001); catches 15→15 of 15 (bar 15) (no rounding — exact fractions).
Sealed literal (never deciding): false alarms 19→6 of 21 vs the sealed bar ≤ 9 — would be PASS; should-quiet-7 fired 3/3 (reported descriptively — it contains a real config-loss defect, #001)
Retune: used — combined headline above (retune/COMBINED-VERDICT.json); untuned first pass: 6/18, 9/21, 13/15 (see §Retune)

**Read this before the PASS.** The PASS is the combined result after the one allowed retune. That
retune was designed after we saw these exact diffs fail, and the other nine diffs were not re-run on
the retuned prompts (the tune-vs-measure overlap). So the **untuned first pass is the cleaner estimate of how the changed tool
does on diffs it was not tuned against: it MISSED the bar** (false alarms 16→6 of 18, which clears
the ≤ 8 bar; catches 15→13 of 15, which fails it). The combined PASS is what the pre-registered
decision rule allows ("at most ONE retune, on failed diffs only (×3)"). It is not evidence that the
retune generalizes.

Every number in this section is transcribed from `docs/design/b3-ground-truth/SCORING-v2.10-phase43.md`
(§3–§7) and from the artifact of record, `docs/design/b3-ground-truth/runs-v2.10-phase43/retune/COMBINED-VERDICT.json`
(label `combined`). The untuned figures come from `runs-v2.10-phase43/first/VERDICT.json` (label
`first`), which the combined artifact carries as its `untuned` triple. Nothing is re-derived here.
`score43.py headline-check` checks this block against the artifact.

## What was measured

- **The measured system.** The fully changed plugin (Phases 40–42 plus the Phase-43 launch-gate
  fix `8ae33da`) frozen in snapshot S = `be6b0fcd9a4c2794dd3351ea054a65f3ab91e536` (batch-5). For
  the retune it was frozen in snapshot S2 = retune commit R = `8df25c7c792448792162072aa89fe46ad5875ae9`
  (batch-6). Sessions loaded the snapshot with `--plugin-dir`. Install-cache parity against each
  snapshot was 106/106 forward with 0 reverse extras. The released 2.9.0 cache was restored after
  each window.
- **The harness tuple, identical for all 45 runs.** Claude Code 2.1.281, codex-cli 0.153.4,
  codex companion 1.0.4, model EXACT `fable 5.1`, 1M context window, auto-update frozen for the
  window. Each run is bound to a committed fingerprint block in `RUN-METHOD-NOTES-phase43.md`.
- **The runs.** First pass: 36 `/vibe-check:deep-review` runs (12 sealed diffs × 3), diff by diff in
  the Phase-38 order, all on S. Retune: 9 runs (the 3 failed diffs × 3) on S2. No run was voided or
  failed, and the ledger is complete for both (`ledger complete: 12 diffs x 3` and
  `3 diffs x 3`, no holes, no extras). The N-01/N-02 integrity gates (isolation, tree.diff triple,
  `state_shape --schema future`) passed on every run.
- **Who drove them.** Assistant-driven via tmux (43-CONTEXT D-13). Each measured session was a
  separate `claude` process with its own context. The driving session sent only the fixed keystroke
  set (launch line, `/clear`, `/vibe-check:deep-review`, Step A 4, Step C 3, `/exit`) and never fed
  findings. The `post` check printed `driver contamination: none` on every run.
- **Codex.** Codex was collected deterministically through the file-owned launch gate. That gate is
  itself a measured-surface change: commit `8ae33da` (43-01) replaced the `BashOutput` gate, which
  current Claude Code cannot satisfy, and it landed before run 1. Codex `joined` on 36/36 first-pass
  runs and 9/9 retune runs. Dropouts: 0 on every diff.
- **What each run archived (committed).** `state.json`, `report.md`, `tree.diff` plus its sha256,
  `lanes.json` (raw per-lane returns), `codex-payload.json` with `codex-rc.txt`, `context.txt` (peak
  context), `session.txt` (fingerprint binding), `clear.txt` (attestation), and
  `transcript.jsonl.sha256`. The transcript itself stays local. The privacy scan was clean on all
  90 archived lane/Codex files (72 first pass, 18 retune).
- **Scoring.** The verdict is scored from `state.passes[-1].findings[]` against the two sealed key
  blobs (`ef0ab67` for carried rows, `5f687d9` for new rows). The quiet arm is mechanical
  (`score43.py fp`). The catch AXIS calls are hand judgements recorded in
  `first/CATCH-VERDICTS.json` and `retune/CATCH-VERDICTS.json`. All nine gates of the integrity
  ladder passed before any scoring.

### Kit, tooling and gate fixes made during the windows (runbook and scoring only)

None of these touched the measured surface (S or S2) or any committed run:

- `a3f240b`: the privacy scan's email exemption was widened to RFC 6762 private-use labels (`.lan`,
  …) after a finding used an invented `user:pass@radarr.lan` example. This followed the pre-window
  fix `185a9fa`. The scanner runs from the repo, not the snapshot.
- `67b2ea3`: the runbook parks any auto-memory directory a measured session recreates. All 47
  recreated directories were empty, so there was no cross-run memory.
- `8f63681`: the runbook now answers the fix-loop menu by label, not by position. In should-quiet-6
  retune runs 2 and 3, the Step C menu was reordered with "Abandon for now" as option 1, and the
  driver answered that option by its position. `post` validates by label and recorded no
  contamination. Step C comes after findings are persisted, so the scored cells are unaffected.
- `23c5b34`: retune-gate fix, disclosed. The S..S2 allowlist check failed on two runbook-tooling
  files (`lanearchive.py`, `test_lanearchive.py`) because the first-pass privacy-scan fixes had
  changed them between S and the FAILED-DIFFS commit. The gate now tolerates exactly those
  pre-verdict tooling paths, and only if their blobs are unchanged from FAILED-DIFFS to S2. The fix
  is mutation-tested and prints the tolerated paths. The orchestrator reviewed it and kept it.
  The five frozen scoring files are blob-equal at S and S2.

### Anomaly: a review agent ran a state-mutating git command in the reviewed repo (product defect)

During first-pass triggarr-session-rotation run 3 (run commit `825bd49`), the measured review's
compliance agent ran `git stash pop` in the reviewed triggarr clone. That popped the owner's
pre-existing, unrelated stash. The agent then re-stashed identical content under a new label
("restore: undo accidental stash pop (compliance-agent review, config.json unrelated)"). The content
was verified identical; only the stash label changed. The run's own checks (tree diff equals the
planted diff, isolation, provenance, no contamination) all passed, and it is scored as recorded (a
CATCH). The runbook's tree-diff checks cannot see the stash list.

**A review tool must never run state-mutating git commands in the repo it is reviewing.** This is a
product safety defect. It does not affect any number in this section, and it is carried to the
v2.11 backlog.

## Pass bar (sealed)

Quoted from the sealed blob `633f1dd` of `docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md`:

> v2.10 FP-rate on the full grown set ≤ ½ × the SET-03 baseline FP-rate, AND catch-rate on the same
> diffs no worse than baseline.

> **Decision rule (sealed at seal-1, evaluated in Phase 43, not this phase):** At most ONE retune, on
> failed diffs only (×3); whether it was used or not is recorded.

Over the sealed denominators `DENOM_CATCH_RUNS: 15` and `DENOM_QUIET_RUNS: 21`, the implied literal
targets from the Phase-38 baseline (19/21, 15/15) are **≤ 9/21** quiet runs firing and **15/15**
catches.

**The deciding line moved to the corrected cohort (D-00a2, SUPERSESSIONS-v2.10.md #001).**
should-quiet-7 contains a real config-loss defect (an absent form field resets the saved value), so
it is not a clean diff. Excluding it gives a superseded baseline of 16/18. The DECIDING bar is
therefore **≤ 8/18** quiet runs firing (½ × 16/18) **AND 15/15** catches, as a single AND. The
sealed-literal x/21 against ≤ 9/21 is printed beside it and never decides. should-quiet-7's runs are
reported descriptively, never appear in FAILED-DIFFS and never drive the retune.

## Per-diff results — should-catch

Baseline is the Phase-38 pre-change baseline. "Combined" uses the retune runs for retuned diffs and
the first-pass runs for every other diff (D-07).

| # | diff-id | origin | AXIS the finding must name | floor | baseline | first pass (run 1, 2, 3) | first | retune | combined | Codex (status per run) | dropouts | direction vs baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | triggarr-secret-in-logs | carried | secret/API-key/PII leaked into logs | warning | 3/3 | catch, catch, catch | **3/3** | — | **3/3** | joined, joined, joined | 0 | held |
| 2 | triggarr-autoescape | carried | XSS surface re-enabled / autoescape not in effect | warning | 3/3 | MISS, MISS, catch | **1/3** | **3/3** (joined ×3) | **3/3** | first: joined, joined, joined | 0 / 0 | first pass −2; combined held |
| 3 | third-organic-should-catch | carried | unclamped percentage / missing clamp | medium | 3/3 | catch, catch, catch | **3/3** | — | **3/3** | joined, joined, joined | 0 | held |
| 4 | triggarr-session-rotation | new | stale-session survival after password change | warning | 3/3 | catch, catch, catch | **3/3** | — | **3/3** | joined, joined, joined | 0 | held |
| 5 | triggarr-settings-form-split | new | silent data loss on save | warning | 3/3 | catch, catch, catch | **3/3** | — | **3/3** | joined, joined, joined | 0 | held |

**Catch arm:** first pass **13/15** (MISS against 15); combined **15/15** (meets the bar).
The two first-pass misses (autoescape runs 1 and 2) are `detected-below-threshold`: the right site
at the right band, but no title or member title names the escaping/XSS consequence.

## Per-diff results — should-quiet

| # | diff-id | origin | Safe ON axis | baseline | first pass (run 1, 2, 3) | first | retune | combined | Codex (status per run) | dropouts | direction vs baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | should-quiet-1 | carried | SSRF / input-validation (tightens the block-list) | 3/3 FP | clean, clean, clean | **0/3** | — | **0/3** | joined, joined, joined | 0 | 3→0 |
| 7 | should-quiet-2 | carried | API contract / typing | 3/3 FP | clean, clean, clean | **0/3** | — | **0/3** | joined, joined, joined | 0 | 3→0 |
| 8 | should-quiet-3 | carried | HTTP-client / path-injection / error-handling | 3/3 FP | clean, clean, clean | **0/3** | — | **0/3** | joined, joined, joined | 0 | 3→0 |
| 9 | should-quiet-4 | new | SSRF / input-validation (adds `validate_url_ssrf`) | 3/3 FP | FP, FP, FP (codex-led) | **3/3** | **0/3** (joined ×3, Codex `approve`) | **0/3** | first: joined, joined, joined | 0 / 0 | first held 3/3; combined 3→0 |
| 10 | should-quiet-5 | new | log-sanitization / secret-handling | 1/3 FP | clean, clean, clean | **0/3** | — | **0/3** | joined, joined, joined | 0 | 1→0 |
| 11 | should-quiet-6 | new | input-validation / config bounds | 3/3 FP | FP, FP, FP (codex-led) | **3/3** | **3/3** (joined ×3) | **3/3** | first: joined, joined, joined | 0 / 0 | held 3/3 (pre-registered residual) |
| 12 | should-quiet-7 | new | settings input-parse path | 3/3 FP | FP, FP, FP | 3/3 | — | 3/3 | joined, joined, joined | 0 | **excluded — descriptive (#001 / D-00a2)** |

**Quiet arm, corrected cohort (rows 6–11, 18 runs):** first pass **6/18**; combined **3/18**. Both
are within the ≤ 8 bar. **Sealed literal (rows 6–12, 21 runs, never deciding):** first pass 9/21;
combined 6/21. Both are within ≤ 9. should-quiet-7's L550 rows name the real config-loss defect that
#001 recorded.

## Confounds examined first (D-00c)

The pre-registered order is: (a) the Phase-42 Codex focus text, then (b) the moved-control
qualifier, then (c) Codex dropouts (D-08), and only after those, anything else. The evidence is the
committed per-run `lanes.json` and `codex-payload.json`.

**Catch arm: one regression, triggarr-autoescape first-pass runs 1 and 2.**

- **(a) Codex focus text: does not explain the loss under the scoring basis.** Clause (2) of
  `templates/codex-focus.txt` at S names a change that makes a control "depend on fragile or
  version-dependent configuration" as a real defect, so it pushes Codex toward this diff, not away
  from it. Codex approved in run 1 (`first/triggarr-autoescape/run-1/codex-payload.json` →
  `result.verdict`: approve, "HTML autoescaping remains enabled and verified"). Codex led runs 2 and
  3 with startup-failure titles. Under ledger entry 007 every member title is judged, so Codex's
  wording cannot hide an axis-naming Claude member. In run 2 no lane named the axis. Whether the
  pre-Phase-42 focus text would have produced an XSS-titled Codex finding cannot be tested offline,
  because replays cannot re-run Codex.
- **(b) Moved-control qualifier: did not fire.** Its capped-note forms ("…covers every path the old
  check guarded", in both the Claude and the Codex wording) have **0 hits** across all 72 first-pass
  and 18 retune `lanes.json`/`codex-payload.json` files. The `pending:` notes in the autoescape runs
  all concern which Starlette release removes the passthrough, and none claims a same-purpose
  replacement:
  - `first/triggarr-autoescape/run-1/lanes.json`: architecture `lanes[3].parsed.findings[0]`
    (`triggarr/web/routes.py:45`, 80/medium); impact `lanes[4].parsed.findings[0]` (routes.py:45,
    65/high) and `lanes[4].parsed.findings[1]` (routes.py:45, 35/low).
  - `first/triggarr-autoescape/run-2/lanes.json`: impact `lanes[4].parsed.findings[0]`
    (routes.py:45, 72/medium): `pending: confirm which Starlette release removes **env_options.`
  - `first/triggarr-autoescape/run-3/lanes.json`: bugs `lanes[1].parsed.findings[0]` (routes.py:45,
    60/high); impact `lanes[4].parsed.findings[0]` (routes.py:45, 58/high) and
    `lanes[4].parsed.findings[1]` (routes.py:45, 35/low).
- **(c) Codex dropouts: none** (joined 3/3 on this diff, 0 on every diff).
- **Then, the most likely proximate cause (a candidate, not established).** In first-pass run 2 the
  security lane rated its own finding 35/low ("no bypass demonstrated / forward-looking risk"), and
  so did the impact lane's version-dependence notes in runs 1 and 3. That is the shape of the
  Phase-42 sensitive-area ceiling. Behind it is a mechanism fact. **In all three runs the reviewing
  lanes ran the base tree's locked dependency themselves and verified that Starlette 0.52.1 from
  `uv.lock` still turns escaping on** (`env.autoescape == True`, rendering checked). That
  contradicts the sealed key's premise that on current Starlette the call "silently NO-OPs
  autoescape". The key is sealed and is **not reopened**: the verdict stands as scored. But some of
  the first-pass "loss" may be the reviewers being right about today's behavior while the key is
  strict about the consequence it wants named. A separate environment question is also unresolved.
  In retune run 2 the language-python lane recorded an installed `.venv` Starlette 0.49.3 against
  0.52.1 pinned in `uv.lock`. In retune run 1 Codex claimed the constructor crashes at startup "in
  the installed environment", which contradicts the Claude lanes' verified 0.52.1 behavior.

**Quiet arm: no NEW quiet-diff row.** should-quiet-4 and should-quiet-6 also fired 3/3 at baseline.
should-quiet-1, -2, -3 and -5 went silent.

- **should-quiet-4, first pass: (a) the Codex focus text is a direct, documented contributor.** The
  alarm changed shape from the baseline's startup-crash/layering complaints to one codex-led
  concrete-bypass claim in each run: numeric IPv4 aliases of the metadata address get past the new
  block (`first/should-quiet-4/run-<n>/codex-payload.json` → `result.findings[0]`, confidence 0.99).
  Clause (1)'s exemption ("an input the new check is written to block and demonstrably fails to
  block") lifted the cap, even though the failing logic is in an unchanged helper the diff only
  calls. (b) Moved-control qualifier: 0 hits. The `pending:` notes in
  `first/should-quiet-4/run-1/lanes.json` (`triggarr/models/config.py:93`, :107, :110) are
  sensitive-area and caller-handling caps, not replacement-coverage caps. (c) Dropouts: 0.
- **should-quiet-6:** this is the pre-registered expected residual ("declared but never wired",
  codex-led at `triggarr/models/config.py:139`). (a) The focus text does not address this framing.
  (b) 0 hits. (c) 0 dropouts.
- **Lane-set irregularities** (a missing framework lane in 4 runs, Codex archived twice in one run,
  two prose lane returns in one run): none moves a scored cell (SCORING §2).

## Retune (PROVE-03)

**Used.** The first pass missed on the catch arm alone, which triggered the one allowed retune
(D-04).

- **Failed diffs** (`first/FAILED-DIFFS.json`, committed once in the verdict commit `ff8ab4c`, before
  any retune edit): should-quiet-4, should-quiet-6, triggarr-autoescape. should-quiet-7 is excluded
  (D-00a2).
- **What changed (R = S2 = `8df25c7`, prompts only).** The shared Safe-change recognition block in
  `agents/bugs.md`, `agents/security.md` and `agents/impact.md`, plus `templates/codex-focus.txt`.
  New mutation-tested locks were added in `scripts/test_agent_prompts.py`, and the pre-registration
  was written to this file (§"Phase-43 retune pre-registration" above) before any retune run.
  - **Rule 1:** a guarantee made conditional (on a library default, a deprecated path or the
    installed version) is a loss even when it is verified to hold today. Its title names the attack.
  - **Rule 2:** a bypass that lives inside an unchanged helper the change only calls is a
    pre-existing gap and stays capped.
  - The five frozen scoring files are blob-equal at S and S2.
- **Ordering proof.** FAILED-DIFFS (`ff8ab4c`) → R (`8df25c7`) → S2 → retune fingerprints and runs →
  RUNS-COMPLETE (`8de5075`). `score43.py retune-gate` returned PASS in both its pre-run and full
  forms, with the two tolerated tooling paths disclosed (`23c5b34`, above).
- **Results side by side:**

| | quiet, corrected (bar ≤ 8/18) | sealed literal (≤ 9/21, never deciding) | catch (bar 15/15) | verdict |
|---|---|---|---|---|
| untuned first pass (`first/VERDICT.json`) | 6/18 | 9/21 | 13/15 | **MISS** |
| combined, after the retune (`retune/COMBINED-VERDICT.json`) | 3/18 | 6/21 | 15/15 | **PASS** |

- **Tune-vs-measure caveat.** The retune was written after seeing these exact diffs fail, and it
  was measured only on them. The nine other diffs were not re-run on R, so any side effect there is
  invisible: Rule 1 could add alarms on clean diffs that rely on a library default. **The untuned
  first pass is the cleaner generalization estimate.**
- **Rule 2's tradeoff.** On should-quiet-4, Codex went from a 0.99 critical bypass claim to
  `approve` with 0 findings in all three runs. The Claude lanes still found the bypass class and
  titled it as a capped "pre-existing helper gap". The tradeoff is that **a real bypass of a reused
  helper is now usually filtered too**: it is reported only as a capped note, counted in the
  Filtered summary but not listed. Whether a helper bypass is the change's problem or a
  pre-existing one is a judgement this rule makes in the quiet direction.
- **Autoescape credit basis (SCORING §7.3).** All three retune autoescape CATCHes, and first-pass
  run 3, use the same title/member-title basis: a title that names XSS protection as made fragile
  or version-dependent meets AXIS. Under a **stricter** basis (the title must say escaping lapses or
  XSS results), retune run 3 is contestable. The combined catch arm would then be 14/15, a **MISS**,
  and the untuned arm would be 12/15. The calls of record use the one basis applied to both passes,
  which keeps the two comparable. The retuned autoescape catches are best read as "titled by the
  protected attack under a rule written for this case", not as "detected that escaping is off".

## Expected residuals check

The Phase-42 section pre-registered three residuals (§"Expected residuals (not claimed as fixed)"):

| pre-registered residual | expected | observed | held? |
|---|---|---|---|
| should-quiet-6 (feature-incompleteness, "declared but never wired") | likely stays 3/3 | first 3/3; retune 3/3 (byte-identical codex-led row at config.py:139 in several runs) | **yes**, observed as predicted |
| should-quiet-1 (pre-existing bypass framing, now capped) | unconfirmed whether lanes follow the cap | 0/3 fired; capped `pending:` notes are present in all three runs' `lanes.json`, and no critical/warning row survived | **not observed**: the residual cleared |
| should-quiet-4 (tightening flagged on another axis; MEDIUM confidence) | may keep firing | first 3/3, in a new shape (codex-led numeric-alias bypass claim, not the predicted "rejects a legacy value"); retune 0/3 | **observed in the first pass** (in a different shape); cleared by the retune's Rule 2 |

The retune's own pre-registered expectations (autoescape 3/3, should-quiet-4 ≤ 1/3, should-quiet-6
3/3) all held. The autoescape one holds under the stated basis (see §Retune).

## Honest limitations

1. **Tune-vs-measure overlap. This is the largest caveat.** The retune was designed after seeing
   these same three diffs fail, and only those diffs were re-run. The other nine never saw R. So the
   untuned first pass (6/18, 13/15 — MISS) is the cleaner generalization estimate, and the combined
   PASS is what the pre-registered decision rule permits. Phases 40–42 were also designed while
   looking at this set, so even the first pass is not a held-out test.
2. **Small N.** 12 diffs, 36 first-pass runs plus 9 retune runs. One run moves a diff by 1/3, and
   the catch arm has zero headroom.
3. **Claude-5 harness parity, but not identical CLIs.** The baseline and the post-change runs both
   used Claude 5 (`fable 5.1`), so the comparison is clean across the model-generation shift. But
   Claude Code was 2.1.281 here and 2.1.261 at baseline (ledger 006).
4. **1M context window vs the baseline's 200k (D-03).** First-pass peak context ran from 180 542 to
   235 051 tokens (mean 204 681), with 26 of 36 runs above 200 000. Retune peaks ran from 200 020 to
   221 430 (9/9 above 200 000). Runs of this size would have hit the 200k limit at baseline, so
   compaction risk differed materially between the two measurements.
5. **Auto-memory parked here, active at baseline.** During Phase 43 the project memory was parked.
   The 47 directories that sessions recreated held 0 files.
6. **Codex collected deterministically here, improvised or sometimes skipped at baseline.** At
   baseline, Codex participation was inferred from `findings[].agent`, and some results came via an
   output-file fallback. Here, the file-owned launch gate (`8ae33da`) gave `joined` on 45/45 runs.
   That gate is a measured-surface change, and it is the **one measured-surface change beyond
   Phases 40–42**.
7. **Plugin resolution differs.** The baseline resolved the installed 2.9.0 cache. The post-change
   runs loaded a `--plugin-dir` snapshot, with an install-cache parity gate of 106/106 forward and
   0 reverse extras so that nothing loaded by a side path differed.
8. **Self-scored AXIS.** The catch AXIS calls are the assistant's hand judgements. They were
   recorded before any aggregate, and the basis is disclosed. The autoescape calls are
   basis-sensitive: under a stricter basis, the combined arm is 14/15 (MISS) and the untuned arm
   12/15 (SCORING §7.3).
9. **The autoescape key's premise vs what the reviewers verified.** Every lane verified that the
   locked Starlette 0.52.1 keeps escaping on, which contradicts the sealed key's "silently NO-OPs"
   premise. The key is not reopened. One lane saw `.venv` 0.49.3 against `uv.lock` 0.52.1, which is
   unresolved.
10. **Three repos, all the owner's.** triggarr, seedsyncarr and roonseek. This measures these defect
    classes on this stack, not recall in general.
11. **Runs were assistant-driven via tmux** (43-CONTEXT D-13; owner decision 2026-09-30; Phase-40/41
    precedent). Each measured session was a separate `claude` process with its own context. The
    driving session sent only the fixed keystroke set (launch line, `/clear`,
    `/vibe-check:deep-review`, Step A 4, Step C 3, `/exit`) and never fed findings:
    `driver contamination: none` on every run. At baseline the owner typed the same commands (with
    assistant-executed checklist blocks on runs 11–36, per Phase-38 limitation 8).
12. **The decision path (D-11).** The first pass missed the bar on the catch arm (13/15). The bar
    was missed because two of three autoescape runs titled the change as a revert, deprecation or
    startup crash instead of naming the XSS consequence. The one allowed retune then brought the
    combined result to PASS. There is no second tuning loop. Phase 44 ships 2.10.0 with these
    numbers, quoting both the combined PASS and the untuned MISS.
13. **Kit fixes during the windows** (`a3f240b`, `67b2ea3`, `8f63681`) and the retune-gate fix
    (`23c5b34`) were runbook and scoring tooling only. The measured surface was unchanged.
14. **A product safety defect surfaced in the measurement.** A review agent ran `git stash pop` in
    the reviewed repo (see §Anomaly). It is carried to v2.11.

## Plain-language summary (for the owner)

**The honest headline first: on its first, untuned attempt the changed tool missed the target.** We
ran the twelve sealed diffs three times each on the finished v2.10 tool. False alarms on clean diffs
fell sharply, from 16 of 18 runs to 6 of 18, comfortably inside the "at least half" target. But the
tool lost two catches out of 15 on one diff: the change that silently weakens the app's XSS
protection. In two of three runs every reviewer saw the change but described it as "reverts a fix"
or "uses a deprecated option" instead of saying "this weakens your XSS protection". The bar allows
zero lost catches, so the first pass is a MISS.

The rules we sealed in advance allow one retune, on the failed diffs only. We used it. We added two
general rules to the reviewer prompts: a protection that now only holds "because of the library's
default today" is still a loss; and a weakness inside an old helper the change merely calls is not
the change's fault. Re-running only the three failed diffs, the XSS diff was caught 3 of 3 times and
one false alarm disappeared. **Combined, that clears the bar: 3 of 18 false alarms, 15 of 15
catches. That is a PASS, but a weaker one than it sounds.** We wrote the retune after seeing those
exact diffs fail, and we did not re-run the other nine. So the untuned MISS is the better guide to
how the tool will behave on your next real change. The PASS is what our own pre-agreed rules
permit.

Three things to keep in mind:

- **The XSS "miss" is partly a key question.** The reviewers actually checked the locked library
  version and found escaping is still on today. Our answer key assumes it is silently off. The key
  is sealed and we did not change it, but some of that first-pass "loss" may be the reviewers being
  right and the key being strict.
- **The XSS credit is somewhat generous.** Under a stricter reading, one retune catch would not
  count, and the combined result would be a MISS (14 of 15).
- **The second retune rule has a cost.** Real bypasses inside reused helpers will now usually be
  filed as quiet notes rather than shown as alarms.

**One real product bug turned up during the runs.** A review agent ran `git stash pop` in the repo
it was reviewing, then put the stash back. Nothing was lost, but a reviewer must never change your
repo's state. That is filed for v2.11, together with the still-open "declared but not yet wired"
false alarm (should-quiet-6, 3 of 3 in both passes, as predicted).

**What happens next:** Phase 44 ships 2.10.0 with exactly these numbers, both the combined PASS and
the untuned MISS, side by side.
