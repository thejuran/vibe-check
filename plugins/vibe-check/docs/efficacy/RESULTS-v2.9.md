# v2.8-Knob & Phase-33-Gate Evidence — RESULTS (v2.9, Phase 35)

**Verdict: PENDING — PROOF-01 script rows complete; live rows and PROOF-02 pending** — every
*deterministic* v2.8 knob (`min_confidence`, `idiom_floor`, `thresholds`, `vibe-ignore`
reasoned/bare, malformed-config per-key degrade, `codex` off/auto/on + precedence) now has a
PASS row below, each proven by a one-command `score.py`/`config.py` invocation with its exact
recipe and observed output recorded for reproduction. The three LIVE `/deep-review` runs (PROOF-01
config-honored-end-to-end / v2.7-parity back-compat / off-via-config against the REAL 33-02 wiring)
and the two scoped PROOF-02 deep reviews are driven by the orchestrator session (the `/deep-review`
skill is user-level and cannot be invoked from a subagent) and remain `PENDING` until Tasks 2 and 3
complete. Only Task 3 flips this top verdict line to `PROOF-01/PROOF-02 PASS`, after both the live
rows and the PROOF-02 section are filled.

This is the v2.9 milestone results doc. Phase 36's B3 catch-rate / false-positive-rate report
appends to THIS SAME doc later (D-01) — the smoke-proof section below is structured so that append
is clean.

## Method

- **Two proof classes (D-04 script-vs-live split).**
  - **Script-level (deterministic, no cache dependency, filled in this task):** each knob is
    exercised by piping a single JSON envelope into `scripts/score.py` (the envelope reader,
    `score.py:1579` `json.load(sys.stdin)` → `:1585` `json.dump(result, sys.stdout)`) or by running
    `scripts/config.py` with a throwaway `.vibe-check.toml` under `REPO_ROOT` plus the transient
    `CODEX_FLAG`/`MIN_CONFIDENCE_FLAG` env. These surfaces have been live since v2.8, so the proofs
    do NOT depend on the installed plugin cache or the 33-02 orchestrator wiring — they may run
    before or after Wave 1.
  - **Live (`/deep-review`, PENDING Task 2):** the three D-04 runs need the REAL orchestrator; they
    run in-session after a CONTENT-asserted cache resync + relaunch (D-08) and are recorded below.
- **Throwaway fixtures (D-02).** Every fixture (the score.py envelopes, the config.py
  `.vibe-check.toml` files, and — in Task 2 — the planted defects) is a scratch artifact under the
  session scratchpad / `/tmp`, never committed. Only this `RESULTS-v2.9.md` persists. The exact
  fixture content + command + observed output is recorded per proof so each recipe is reproducible
  without the fixture.
- **Cache-resync pre-flight (D-08, applies to the LIVE runs only).** Before any live `/deep-review`
  run, the INSTALLED plugin cache is asserted to contain the new 33-02 wiring BY CONTENT
  (`grep SCOPE_ARGS` in the installed `commands/review.md`; `grep 'Codex off via'` in the installed
  `commands/deep-review.md`) and the process relaunched — version parity alone is NOT sufficient
  because 33-02 is prose-only and does not bump the version string. Recorded in the live-run section.
- **`score.py` / `test_score.py` byte-unchanged; `config.py` read-only.** All proofs invoke these as
  read-only CLI surfaces. `git diff --quiet -- plugins/vibe-check/scripts/score.py
  plugins/vibe-check/scripts/test_score.py plugins/vibe-check/scripts/config.py` exits 0 after every
  proof run, and `pytest -q` in `plugins/vibe-check/scripts` stays green (356 passed, 221 subtests).

## PROOF-01 — Per-knob smoke table

Scoring context (so the recipes below are self-explanatory): `score.py`'s formula is
`orchestrator_score = agent_confidence + (in_diff ? +20 : 0) + (silenced ? -50 : 0) + severity_weight`
where `severity_weight = {critical:0, high:-3, medium:-8, low:-20}` and `+20` fires only when the
finding's line falls inside `changed_line_ranges[file]`. Default band floors are
`{critical:95, warning:80, medium:70}`; the per-command surface cutoff is `{review:80, deep-review:70}`.

| # | Knob | Proof type | Exact recipe (envelope/config + command) | Expected | Observed | Verdict |
|---|------|-----------|------------------------------------------|----------|----------|---------|
| 1 | `min_confidence` pre-scoring drop + honesty count | script (score.py stdin) | `printf '%s' '{"command":"review","findings":[{"id":"t1","file":"a.py","line":1,"title":"x","problem":"p","severity":"warning","category":"bugs","agent":"bugs","agent_confidence":30}],"min_confidence":50}' \| python3 scripts/score.py` | finding dropped BEFORE scoring → `filtered[]` one entry `reason:"below-min-confidence"`; `scored_by_script:true`; the dropped entry is the honesty-summary count source | `filtered:[{"file":"a.py","line":1,"title":"x","reason":"below-min-confidence"}]`; `findings_count:0`; `scored_by_script:true`. Two-finding variant (`agent_confidence:30` dropped, `agent_confidence:90` kept) → exactly one `below-min-confidence` entry in `filtered[]` + the keeper surfaces — so the honesty count = `len([f for f in filtered if f.reason=="below-min-confidence"])` | **PASS** |
| 2 | `idiom_floor` cap (default/explicit) | script (score.py stdin) | envelope with an `idiom`-category finding (`agent_confidence:80, severity:"critical"`) whose natural band is `warning` (80+0+0=80) + a non-idiom `bugs` control; run once with `idiom_floor` absent and once `"idiom_floor":"medium"` | idiom finding's band capped at `medium`; the non-idiom `bugs` finding unaffected (`warning`) | absent → `[('idiom','medium',80),('bugs','warning',80)]`; `"medium"` → `[('idiom','medium',80),('bugs','warning',80)]` — idiom lowered `warning`→`medium`, bugs untouched | **PASS** |
| 3 | `idiom_floor` explicit-off sentinel | script (score.py stdin) | same envelope as row 2 with `"idiom_floor":"off"` | idiom finding NOT capped — rides its natural `warning` band | `"off"` → `[('idiom','warning',80),('bugs','warning',80)]` — idiom stays `warning` (uncapped), proving absent≠off is distinguishable at the scorer | **PASS** |
| 4 | `thresholds` band parameterization | script (score.py stdin) | one `bugs` finding `agent_confidence:65, severity:"high"` in-diff (`changed_line_ranges:{"a.py":[[1,5]]}`) → score 65+20−3=82, `command:"deep-review"` (cutoff 70 so it surfaces); run once default, once `"thresholds":{"critical":95,"warning":85,"medium":70}` | default (warning≥80) → band `warning`; custom warning floor 85 → same score-82 finding bands `medium` | default → `findings:[('warning',82)]`; custom → `findings:[('medium',82)]` — identical finding, custom floor moved the band | **PASS** |
| 5 | `vibe-ignore` reasoned suppress | script (score.py stdin) | finding `agent_confidence:30, severity:"medium"`, NOT in-diff, `source_window:["x = 1","// vibe-ignore: legacy shim, tracked in JIRA-123","risky()"]` → score 30−50−8=−28 (pre-clamp<0 → drop, `silenced` precedence) | rides the −50 silenced path → `filtered[].reason == "silenced"` | with marker → `filtered:[{"file":"a.ts","line":3,"title":"legacy","reason":"silenced"}]`; CONTROL (same finding, marker replaced by a plain line) → `filtered:['sub-threshold']` — the marker specifically drives the silenced label | **PASS** |
| 6 | `vibe-ignore` bare self-flag | script (score.py stdin) | real `bugs` finding `agent_confidence:90, severity:"critical"` in-diff, `source_window:["x = 1","// vibe-ignore","risky()"]` (BARE marker, no reason), `command:"deep-review"` | does NOT suppress the real finding; emits ONE synthetic `suppression` finding titled "suppression without reason" (`vibe-ignore (no reason)`), band `low` | `findings:[('realbug','bugs','critical',100),('suppression without reason','suppression','low',0)]` — real bug survives AND the bare-marker audit finding is emitted | **PASS** |
| 7 | malformed-config per-key degrade | script (config.py) | `.vibe-check.toml` = `[noise]\ncodex = "banana"\nidiom_floor = "warning"\n` under `REPO_ROOT`; `REPO_ROOT=<scratch> python3 scripts/config.py` | bad key → default + one warning naming it; good key applies; `exit 0` | `values.codex:"auto"` (bad→default), `values.idiom_floor:"warning"` (good→APPLIED), `warnings:["config: codex invalid — using default"]`, `__main__` exit `0` | **PASS** |
| 7b | `min_confidence` ≥50 refusal (Fable A3) | script (config.py) | `.vibe-check.toml` = `[noise]\nmin_confidence = 60\n`; `REPO_ROOT=<scratch> python3 scripts/config.py` | `min_confidence` 60 refused → `None` (default) + a warning (the filter runs before scoring, so ≥50 can annihilate criticals) | `values.min_confidence:None`; `warnings:["config: min_confidence >= 50 can silently drop critical findings (the filter runs before scoring) — using default"]`; exit `0` | **PASS** |
| 8 | `codex` off / auto / on + precedence | script (config.py) | (a) `[noise]\ncodex="off"`; (b) same toml + `CODEX_FLAG=on`; (c) empty repo (no toml); (d) `[noise]\ncodex="on"`; `REPO_ROOT=<scratch> [CODEX_FLAG=on] python3 scripts/config.py` | (a) `values.codex=="off"`; (b) `=="on"` (flag>config); (c) `=="auto"` (default); (d) `=="on"` | (a) `codex:off, warnings:[]`; (b) `codex:on, warnings:[]` (flag over toml `off`); (c) `codex:auto, warnings:[]`; (d) `codex:on, warnings:[]` — malformed→auto+warning already covered by row 7 | **PASS** |
| L1 | LIVE run 1 — planted `.vibe-check.toml` (config honored end-to-end + knob visible in render + Codex announce line) | live (`/deep-review`) | PENDING (Task 2) | PENDING (Task 2) | PENDING (Task 2) | PENDING (Task 2) |
| L2 | LIVE run 2 — no config (v2.7-parity back-compat + one Codex outcome line under `auto`) | live (`/deep-review`) | PENDING (Task 2) | PENDING (Task 2) | PENDING (Task 2) | PENDING (Task 2) |
| L3 | LIVE run 3 — `codex = "off"` (off-via-config line; no probe, no launch) | live (`/deep-review`) | PENDING (Task 2) | PENDING (Task 2) | PENDING (Task 2) | PENDING (Task 2) |

**Script-level proof provenance (reproducible without fixtures).** All eight+ script rows above ran
this session against the byte-frozen `score.py` / read-only `config.py` at the Wave-1 tree
(`<phase-base>` = `d2ec9fcf60387119ac540a9a05d350bc7627a533`, plus the 35-01 wiring commits). The
`score.py`/`test_score.py`/`config.py` byte-frozen assertion held before and after every proof, and
`pytest -q` in `plugins/vibe-check/scripts` reported **356 passed, 221 subtests passed**.

## Live runs (D-04) — PENDING (Task 2)

PENDING (Task 2). The three live `/deep-review` runs (planted-toml / no-config / codex=off) are
driven by the orchestrator session against the REAL 33-02 wiring after the CONTENT-asserted cache
resync + relaunch (D-08). Each run's recipe (planted fixture paths, host Codex state, the one Codex
outcome line, the knob's render effect) and transcript are recorded here, and the three `L1`/`L2`/`L3`
rows above are flipped from `PENDING (Task 2)` to `PASS`.

- **Cache pre-flight (D-08):** PENDING (Task 2) — `grep SCOPE_ARGS` in installed `commands/review.md`
  AND `grep 'Codex off via'` in installed `commands/deep-review.md`, both asserted before run 1;
  process relaunched; host Codex state recorded.
- **Run 1 (planted `.vibe-check.toml`):** PENDING (Task 2).
- **Run 2 (no config):** PENDING (Task 2).
- **Run 3 (`codex = "off"`):** PENDING (Task 2).

## PROOF-02 — Two scoped deep-review gates — PENDING (Task 3)

PENDING (Task 3). The Phase-33 surface passes a clean deep-review gate via TWO scoped reviews, both
cited here with their scope expression and clean verdict:

- **Review A — the NEW 33-02 diff:** explicit range `<phase-base>..HEAD` where `<phase-base>` =
  `d2ec9fcf60387119ac540a9a05d350bc7627a533` (from 35-01-SUMMARY, the commit immediately before the
  first 35-01 execution commit). Covers only the `commands/review.md` + `commands/deep-review.md`
  edits. NOT GSD-phase-mode scoping (broken on this repo's gitignored `.planning`). Verdict: PENDING
  (Task 3).
- **Review B — the 33-01 surface as it exists today:** narrowed `--all` over the REPO-ROOT paths
  `plugins/vibe-check/scripts/config.py` + `plugins/vibe-check/scripts/test_config.py` (the repo
  tracks these under `plugins/vibe-check/scripts/`, NOT a top-level `scripts/`), run from the repo
  root. 33-01 shas for provenance: `83cbfae` (feat), `80155e9` (test), `a1f44bc` (Fable A3
  min_confidence≥50 refusal). Verdict: PENDING (Task 3).

## Provenance (honest history)

- **Script-level proofs (this task, Wave 2):** ran against the byte-frozen `score.py` / read-only
  `config.py` at `<phase-base>` = `d2ec9fcf60387119ac540a9a05d350bc7627a533` plus the three 35-01
  wiring commits (`01df9db`, `46817b8`, `29825e0`). No fix was applied during the script-level proofs
  — every recipe's observed output matched the expected behavior on the first run. The three A1-A3
  ASSUMED recipes (idiom_floor, thresholds, vibe-ignore) were confirmed against the live `score.py`
  helpers (`_cap_idiom_band`/`_usable_idiom_floor` `score.py:224-274`, `band_for` `:180`,
  `_vibe_ignore_scan`/`silenced_nearby` `:359-436`, the `silenced`-reason emit `:1560`) BEFORE their
  rows were finalized; the recorded envelopes match what actually ran, not the pre-verification
  assumption.
- **Live-run + PROOF-02 provenance:** PENDING (Tasks 2–3) — any fix landed during those proofs is
  recorded here, not papered over.
- **Byte-frozen assertion:** `git diff --quiet -- plugins/vibe-check/scripts/score.py
  plugins/vibe-check/scripts/test_score.py plugins/vibe-check/scripts/config.py` exits 0 across the
  whole task; the proofs invoked these as read-only CLI surfaces only.

## Plain-language summary (for the owner)

v2.8 shipped a set of "knobs" — the confidence floor (`min_confidence`), the idiom-noise cap
(`idiom_floor`), the band tuner (`thresholds`), the `// vibe-ignore` marker, per-key config
degradation, and the Codex on/off/auto control — but it shipped them WITHOUT planted-test proof that
each one actually does what it says. This task pays down the first half of that debt: for every knob
whose behavior lives in the deterministic scoring/config scripts, we fed it a tiny hand-built input
and confirmed the exact output — the low-confidence finding gets dropped and counted, the noisy idiom
gets capped (and rides free when you turn the cap off), a custom threshold really does move a
finding's band, a `vibe-ignore` WITH a reason silences the finding while a BARE one does NOT (and gets
flagged itself), a broken config key falls back to its default with a warning while the good keys next
to it still work, and the Codex control resolves off/auto/on with a command-line flag overriding the
config file. Every one of these passed, and none of the tool's frozen scoring code was touched (its
356-test suite stayed green). What's still outstanding — and will be filled in by the orchestrator
session, which can actually run a full `/deep-review` — is the three live end-to-end runs (proving the
config is honored through a real review and that Codex announces itself on every run) and the two
scoped code reviews of the Phase-33 wiring surface. Until those land, this doc's headline stays
PENDING; it flips to PASS only when all of it is done.
