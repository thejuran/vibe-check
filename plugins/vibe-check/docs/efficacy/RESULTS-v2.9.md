# v2.8-Knob & Phase-33-Gate Evidence — RESULTS (v2.9, Phase 35)

**Verdict: PROOF-01/PROOF-02 PASS** — every *deterministic* v2.8 knob (`min_confidence`,
`idiom_floor`, `thresholds`, `vibe-ignore` reasoned/bare, malformed-config per-key degrade, `codex`
off/auto/on + precedence) has a PASS row below, each proven by a one-command `score.py`/`config.py`
invocation with its exact recipe and observed output recorded for reproduction; the three LIVE
`/deep-review` runs (PROOF-01 config-honored-end-to-end / v2.7-parity back-compat / off-via-config
against the REAL 33-02 wiring, after a CONTENT-asserted cache resync + relaunch) all PASS; and the
Phase-33 surface passed a clean deep-review gate via TWO scoped reviews (PROOF-02 Review A = the 33-02
diff range, Review B = the 33-01 config surface), both clean of unresolved critical/warning. The
OWNER-SIGNOFF marker is intentionally left for Phase 37 (milestone close).

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
  - **Live (`/deep-review`, PASS):** the three D-04 runs need the REAL orchestrator; they
    ran in-session after a CONTENT-asserted cache resync + relaunch (D-08) and are recorded below.
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
| L1 | LIVE run 1 — planted `.vibe-check.toml` (config honored end-to-end + knob visible in render + Codex announce line) | live (`/deep-review`) | Plant `vc_live_fixture.py` (SQLi + fd-leak defects) + repo-root `.vibe-check.toml` (`[agents] disabled=["architecture"]`, `[noise] min_confidence=40`), uncommitted; run `/vibe-check:deep-review` (default diff scope) in-session; revert (`git reset HEAD` + `rm`) + per-path absence gate | config honored end-to-end: `architecture` subtracted from dispatch (5 native agents, not 6); one finding dropped `below-min-confidence`; exactly ONE Codex outcome line | Phase 0.6 resolved `{disabled:["architecture"], min_confidence:40, codex:auto}`; dispatched **bugs/security/impact/test-sufficiency/language-python** (architecture subtracted — non-core, silent); score.py `filtered[]` carried **1× `below-min-confidence`** (the conf-20 type-hints finding, dropped pre-scoring); `✓ Codex joined — 2 findings` (verdict needs-attention, both targeting the planted scaffolding: `.vibe-check.toml` coverage-drop + staged fixture); `scored_by_script:true`; fixtures reverted, per-path absence + baseline clean | **PASS** |
| L2 | LIVE run 2 — no config (v2.7-parity back-compat + one Codex outcome line under `auto`) | live (`/deep-review`) | Plant same `vc_live_fixture.py`, NO `.vibe-check.toml`, uncommitted; run `/vibe-check:deep-review`; revert + per-path gate | v2.7-parity: `architecture` NOT subtracted (6 native agents); NO config-health line; ZERO `below-min-confidence` drops; exactly ONE Codex outcome line | Phase 0.6 resolved all-defaults `{disabled:[], min_confidence:null, codex:auto}`, `warnings:[]` → config-health line renders NOTHING; **architecture DISPATCHED** (6 agents); score.py `filtered[]` carried **0× `below-min-confidence`** (no `min_confidence` envelope key → filter never runs; the conf-20 finding instead lands in `sub-threshold`); `✓ Codex joined — 1 finding` (needs-attention, staged fixture only — no config-coverage finding, the L1↔L2 difference); `scored_by_script:true`; reverted clean | **PASS** |
| L3 | LIVE run 3 — `codex = "off"` (off-via-config line; no probe, no launch) | live (`/deep-review`) | Plant `vc_live_fixture.py` + repo-root `.vibe-check.toml` (`[noise] codex="off"`), uncommitted; run `/vibe-check:deep-review`; revert + per-path gate | `⊘ Codex off via [noise] codex=off`; NO `setup --json` probe, NO launch, NO smoke gate; native review completes normally | Phase 0.6 resolved `codex:"off"` → Phase-2c step-0 OFF short-circuit fired FIRST: `CODEX_SKIPPED=1`+`CODEX_OFF=1`, and ZERO Codex Bash executed this run (no `${CODEX_PLUGIN_ROOT}` resolve, no probe, no launch guard, no smoke check); native fan-out proceeded; scored survivors contained **no `codex-adversarial` attribution** (confirming no join); outcome line `⊘ Codex off via [noise] codex=off` rendered QUIET (D-12 off style); `scored_by_script:true`; reverted clean | **PASS** |

**Script-level proof provenance (reproducible without fixtures).** All eight+ script rows above ran
this session against the byte-frozen `score.py` / read-only `config.py` at the Wave-1 tree
(`<phase-base>` = `d2ec9fcf60387119ac540a9a05d350bc7627a533`, plus the 35-01 wiring commits). The
`score.py`/`test_score.py`/`config.py` byte-frozen assertion held before and after every proof, and
`pytest -q` in `plugins/vibe-check/scripts` reported **356 passed, 221 subtests passed**.

## Live runs (D-04) — PASS

The three live `/deep-review` runs (planted-toml / no-config / codex=off) were driven by the
orchestrator session against the REAL 33-02 wiring after the CONTENT-asserted cache resync + relaunch
(D-08). All three passed; the `L1`/`L2`/`L3` rows above are PASS.

- **Cache pre-flight (D-08):** PASS. The installed cache
  (`~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/`) was CONTENT-asserted before run 1 —
  `grep -c 'SCOPE_ARGS' commands/review.md` = **13** and `grep -c 'Codex off via' commands/deep-review.md`
  = **2** (both non-zero → the 33-02 wiring is present in the INSTALLED cache, not just the repo).
  The process was relaunched before this session (the D-08 pause the resume doc was written for), and
  the greps were re-verified at the top of this session to guard against a marketplace re-sync
  overwriting the rsync. Version parity alone was NOT relied on — 33-02 is prose-only and does not bump
  the version string.
- **Host Codex state (runs 1-2 interpretability):** installed AND authenticated —
  `setup --json` returned `ready:true` (`codex-cli 0.133.0`, ChatGPT login active). So runs 1-2
  legitimately show `✓ Codex joined` (not a `not-installed`/`unauthenticated` skip slug). `timeout`
  binary present (`/opt/homebrew/bin/timeout`), so the 300s self-contained watchdog was expressible
  (no `no-timeout-binary` skip).
- **Run 1 (planted `.vibe-check.toml`, config honored):** PASS. Planted paths: `vc_live_fixture.py`
  (root) + `.vibe-check.toml` (root), both uncommitted. `.vibe-check.toml` = `[agents]
  disabled=["architecture"]` + `[noise] min_confidence=40`. Both knobs visibly changed the run:
  **architecture subtracted** from the deep dispatch (5 native agents dispatched, not the deep default
  6), and the confidence-20 `language-python` type-hints finding **dropped `below-min-confidence`** in
  score.py's `filtered[]` (1 entry). Codex launched (smoke-check PASS, `__SMOKE_OK__` observed via
  `BashOutput`), joined with `verdict:needs-attention` and 2 findings — both targeting the planted
  proof scaffolding (the root `.vibe-check.toml` silently dropping the architecture reviewer, and the
  staged throwaway fixture) — which cross-confirmed against the native SQLi finding. Exactly ONE Codex
  outcome line (`✓ Codex joined — 2 findings`). `scored_by_script:true`. Reverted; per-path absence +
  filtered repo-wide baseline both clean.
- **Run 2 (no config, v2.7-parity):** PASS. Planted path: `vc_live_fixture.py` only; NO
  `.vibe-check.toml`. Phase 0.6 resolved all-defaults with an EMPTY `warnings` list → the config-health
  line rendered NOTHING (CONFIG-01 silence). **architecture was NOT subtracted** (6 native agents
  dispatched — the deep default), and there were **ZERO `below-min-confidence` drops** (no
  `min_confidence` envelope key → the pre-scoring filter never ran; the same conf-20 finding instead
  landed in `sub-threshold`). This is the crisp L1↔L2 contrast that proves the knobs — not some other
  effect — drove L1's behavior. Codex joined with `verdict:needs-attention` and 1 finding (the staged
  fixture only — no config-coverage finding, since there was no `.vibe-check.toml` to flag), exactly
  ONE Codex outcome line. `scored_by_script:true`. Reverted clean.
- **Run 3 (`codex = "off"`, host-independent):** PASS. Planted paths: `vc_live_fixture.py` +
  `.vibe-check.toml` = `[noise] codex="off"`. Phase 0.6 resolved `codex:"off"`, so the Phase-2c step-0
  OFF short-circuit fired FIRST: **zero Codex plumbing ran this session** — no `${CODEX_PLUGIN_ROOT}`
  resolve, no `setup --json` probe, no launch guard, no `BashOutput` smoke check, no launch (the
  orchestrator executed NO codex Bash for this run at all). The native fan-out proceeded normally; the
  scored survivors carried **no `codex-adversarial` attribution** (confirming no join). The single
  Codex outcome line was `⊘ Codex off via [noise] codex=off`, rendered QUIET per D-12 (off style, not
  the prominent `on` style, and NOT a skip slug that would falsely imply an availability failure).
  `scored_by_script:true`. Reverted clean.

**Cleanup gate (blocking, all three runs):** after each run's revert, every planted path individually
passed its content/absence check — `vc_live_fixture.py` (git reset + rm → absent), `.vibe-check.toml`
(rm → absent) — and the filtered repo-wide `git status --porcelain` (RESULTS-v2.9.md excluded)
matched the pre-run baseline captured at STEP 0. `score.py` / `test_score.py` / `config.py` stayed
byte-frozen (`git diff --quiet` exit 0) across all three runs. Only this `RESULTS-v2.9.md` persists.

## PROOF-02 — Two scoped deep-review gates — PASS

The Phase-33 surface passes a clean deep-review gate via TWO scoped reviews, both cited here with
their scope expression and clean verdict. Both came back with **no unresolved critical/warning
findings** (each reviewer-raised finding was adjudicated to a false positive, a refuted-as-blocking
legibility nit, or a non-blocking backlog item — recorded honestly below).

- **Review A — the NEW 33-02 diff — CLEAN.** Scope: explicit range
  `d2ec9fcf60387119ac540a9a05d350bc7627a533..HEAD` (the `<phase-base>` from 35-01-SUMMARY, the commit
  immediately before the first 35-01 execution commit). Substantive targets: the 33-02 edits to
  `commands/review.md` + `commands/deep-review.md` (the `.planning/*` files in the range are gitignored
  orchestrator state; `RESULTS-v2.9.md` is this phase's own evidence doc — neither is code). NOT
  GSD-phase-mode scoping (broken on this repo's gitignored `.planning`). This review DOUBLES as the
  orchestrator's Sub-step 5 per-phase deep-review gate (one review, two purposes). Agents: architecture
  + bugs (both at opus), each adversarially reviewing the codex-knob wiring. **Adjudication (4 raised,
  0 blocking):**
  - *arch — `CODEX_ON` "has no executable set-site" (medium)* → **FALSE POSITIVE.** The Phase-3
    prominence selector (deep-review.md:357) keys on `$CONFIG_CODEX == on`, which config.py binds
    reliably on every path — `CODEX_ON` is a parenthetical alias, not the load-bearing key. No defect.
  - *bugs-001 — collection-time `timeout` doesn't set `CODEX_SKIPPED`, so the one-outcome-line
    invariant could emit zero/two lines (medium)* → **REFUTED as blocking** by a 1-vote adversarial
    verify. Step 7 selects the line "by the Phase-2c/**Phase-3** outcome" and explicitly enumerates the
    `timeout` slug, so an executor that observed `__CODEX_TIMEOUT__` emits exactly one
    `⊘ Codex skipped: timeout`. Worst case is a cosmetic doubled/missing status line on the rare
    launched-then-timed-out path; degrades safe (native review completes, no finding dropped). A
    one-line prose clarification, not a correctness break.
  - *bugs-002 — smoke-check FAIL-CLOSED sets no marker / has no slug (medium)* → **REFUTED as
    blocking.** Fires only when `BashOutput` (a Claude Code built-in) is non-callable on a genuine
    launch path — effectively "the harness is broken." Fails safe (native-only), drops no finding,
    and step 6 already says to "surface the blocker." A completeness nit on a near-impossible,
    already-safe path.
  - *bugs-003 — `$SCOPE`/`$BASE` "never explicitly assigned" (low, conf 40, self-marked pending)* →
    **FALSE POSITIVE.** Step 4 (deep-review.md:238-250) resolves scope/base per mode and step 5's
    comment confirms "`$BASE/$SCOPE already resolved above`"; the `off` path returns before step 4 and
    step 5 is `CODEX_SKIPPED`-guarded, so the references are never reached unbound.
- **Review B — the 33-01 config surface as it exists today — CLEAN.** Scope: narrowed `--all` over the
  REPO-ROOT paths `plugins/vibe-check/scripts/config.py` + `plugins/vibe-check/scripts/test_config.py`
  (the repo tracks these under `plugins/vibe-check/scripts/`, NOT a top-level `scripts/`), run from the
  repo root. The two-file narrow is a single-confirm on the `--all` Phase-0.3 estimate gate. 33-01 shas
  for provenance: `83cbfae` (feat), `80155e9` (test), `a1f44bc` (Fable A3 min_confidence≥50 refusal).
  Agents: security + language-python. **Adjudication (3 raised, 0 blocking):**
  - *sec-001 — symlinked `.vibe-check.toml` read without realpath-containment vs `$REPO_ROOT`
    (CWE-61, medium, conf 62)* → **NON-BLOCKING BACKLOG ITEM.** Real observation, but (1) the config
    file is the OWNER's own repo config read from `$REPO_ROOT` (a different trust surface than the
    untrusted-PR coverage/codex-path surfaces that DO carry guard.py containment); (2) no exfiltration
    channel — warnings name only the KEY + a fixed reason, never the raw parsed VALUE (both reviewers
    confirmed), and non-TOML content degrades to `unparseable`; (3) config.py is byte-frozen this phase
    (a `realpath` guard is a code change to a frozen surface, out of scope for a proofs-only phase).
    Filed as a hardening backlog item, not an unresolved C/W. → see [[fable-findings-buckets-1-3-shipped]].
  - *sec-002 — TOCTOU between `isfile`/`getsize`/`open` (CWE-367, low, conf 35)* → sub-warning; same
    frozen-surface + owner-trust reasoning. Non-blocking.
  - *language-python — no findings*; agent_notes verified the deep-copy anti-aliasing, bool-is-int
    guards, the named-exception never-raise boundary, flag-precedence, and the degrade-path test
    coverage; ran the suite (all green). One stale COMMENT in test_config.py (says `[0,100]` where the
    code enforces `[0,49]`) — cosmetic, zero behavioral impact, non-blocking.

Both scoped reviews are clean of unresolved critical/warning. `score.py`/`test_score.py`/`config.py`
stayed byte-frozen across both reviews, and `pytest -q` in `plugins/vibe-check/scripts` reported
**356 passed, 221 subtests passed** afterward.

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
- **Live-run provenance (Task 2, Wave 2):** the three live `/deep-review` runs ran in-session against
  the REAL 33-02 wiring after the D-08 CONTENT-asserted cache resync + process relaunch (the installed
  cache `~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/` grepped `SCOPE_ARGS`=13 in review.md and
  `Codex off via`=2 in deep-review.md before run 1). Host Codex state: installed + authenticated
  (`ready:true`, codex-cli 0.133.0), `timeout` binary present. **NO fix was landed during the live
  runs** — each run behaved exactly as the wiring predicts (L1 config-honored, L2 v2.7-parity, L3
  off-short-circuit). All fixtures were throwaway and reverted (per-path content/absence gate + filtered
  repo-wide baseline, all clean); only this doc persists.
- **PROOF-02 provenance (Task 3):** Review A ran over `d2ec9fcf60387119ac540a9a05d350bc7627a533..HEAD`
  (the 33-02 command-file diff); Review B ran a narrowed `--all` over `config.py` + `test_config.py`
  (33-01 surface, shas `83cbfae`/`80155e9`/`a1f44bc`). **NO fix was landed during either review** — all
  seven raised findings were adjudicated to false positives, refuted-as-blocking legibility nits, or
  non-blocking backlog items (full adjudication in the PROOF-02 section above; honest history — nothing
  papered over). Two items were noted for the backlog (config-read symlink containment; a stale
  test_config.py comment), neither an unresolved critical/warning.
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
356-test suite stayed green). The second half of the debt is now paid too: the orchestrator session ran
three live end-to-end `/deep-review` passes against the real wiring — one WITH a config file (the tool
honored it: it dropped a reviewer from the run and filtered a low-confidence finding, exactly as the
config asked), one with NO config file (the tool behaved identically to the previous release — proving
we didn't break anyone who never writes a config), and one with the Codex helper turned OFF (the tool
skipped Codex entirely and said so in one clean line, no wasted probing). Each run announced its Codex
status in exactly one line, as designed. Finally, the tool reviewed its OWN new wiring code twice
(once the fresh changes, once the shipped config-reader), and both reviews came back clean — every
issue a reviewer raised turned out to be a false alarm, a cosmetic wording nit that fails safe, or a
minor hardening idea for the backlog, none of them a real bug. So the whole debt is paid and this doc's
headline is PASS. The one thing deliberately left for later is the owner's formal sign-off, which
happens when the v2.9 milestone is closed (Phase 37).
