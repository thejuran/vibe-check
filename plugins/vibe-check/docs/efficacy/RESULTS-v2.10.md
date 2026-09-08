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
  should-quiet) were built this phase and scored against a separate v2.10 key blob. The two seals never touch each other: the
  v2.9 manifest, key, `runs/`, and existing kit files under `diffs/` are byte-unchanged. Final
  composition: **5 should-catch diffs (15 runs) + 7 should-quiet diffs (21 runs) = 36**.
- **Organic-only sourcing (D-03), carried forward.** All diffs are real shipped commits from the
  owner's own repos (triggarr, seedsyncarr, roonseek + the angular front-end), selected by the same
  FAIL-CLOSED provenance regex so no vibe-check-found bug can enter the set. should-catch diffs are
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
2. **Four repos, twelve diffs.** triggarr, seedsyncarr, roonseek, and the angular front-end — the
   owner's own stack, not a broad multi-project or multi-language trial. It measures these defect
   classes on these repos; it does not measure recall across the whole surface.
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
