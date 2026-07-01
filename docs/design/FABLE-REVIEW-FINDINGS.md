# vibe-check — Consolidated second-model review findings (v2.7)

> **What this is:** the combined result of a multi-pass independent review of vibe-check at tag
> `v2.7`, using a second frontier model (Fable) as the cross-model lens plus Opus verification of
> every finding against real code. This single doc consolidates four passes (B1 code, B1 bash, B2
> design, B4 agents) and describes the one pass that was scoped out (B3 product-quality).
>
> **Source docs (this doc supersedes none of them — they hold the full detail):**
> - `fable-findings-score-py-v2.7.md` — B1 Python engine
> - `fable-findings-bash-v2.7.md` — B1 shell/security
> - `fable-findings-design-v2.7.md` — B2 design + answer-key
> - `fable-findings-agents-v2.7.md` — B4 subagent efficacy
> - `b3-ground-truth/B3-STATUS.md` — B3 (shelved) status + verified diffs
>
> **Owner context (shapes every severity call):** the owner is a PM who understands software but
> cannot verify a diff by reading it. vibe-check is his **sole reviewer**. So a wrong verdict is
> one he cannot catch: false negatives ship silently; noise he can't triage is nearly as costly.
>
> **Verification standard:** every "confirmed" finding was checked against the real code extracted
> at tag `v2.7` (`git show v2.7:…`). Design challenges route to the B3 harness to settle
> empirically. Provenance (Fable vs Opus) is recorded per pass — it affects the cross-model weight
> of a finding, not whether it's real.

---

## Executive summary

| Pass | What it reviewed | Author | Result |
|---|---|---|---|
| B1 score.py | the Python scoring engine | **Fable** | 8/9 confirmed real, 1 overstated |
| B1 bash | security-critical inline shell | Opus¹ | 5/5 confirmed real |
| B2 design | design hypotheses + the answer key | **Fable** | 2 confirmed real bugs + 6 answer-key findings + design challenges |
| B4 agents | the 18 detection-agent prompts | **Fable** | two-generations thesis (confirmed); calibration retrofit = highest leverage |

¹ Fable's content-safety safeguards flagged the security/bash prompt and hard-switched to Opus.
So the bash pass is Opus-authored — real findings, but not an independent cross-model data point.
The B4 pass avoided this by skipping `security.md` (which still owes its own critique).

**The convergence story (the strongest signal):** three independent passes point at the same
structural gap. B2 found the answer key tests only *agent-side* gates (AK-5). B4 found 8 of 18
agents have *no* agent-side calibration at all. And NEW-ABSORB shows up in both (B2 in the core
scorer, B4 in framework-electron's ipc-twin). The tool's own efficacy fixture structurally cannot
see its two most serious scorer-path bugs.

**The two highest-leverage takeaways:**
1. **Retrofit calibration onto the 8 gen-1 agents** (B4) — cheap, no new checks, the framework
   fleet already proved the pattern. Fixes the largest noise source and the enforcement problem.
2. **Fix the two confirmed scorer bugs** (B2): NEW-ABSORB (silent finding deletion) and the
   H-KNOB kill-shot (the flagship noise knob annihilates real criticals at its documented value).

---

## ACT-NOW items (confirmed real, ranked by leverage)

### A1 — Retrofit gen-2 calibration onto the 8 gen-1 agents  [highest leverage] · B4
**Confirmed against code.** The fleet is two prompt generations and the scorer can't tell them
apart. Gen-2 agents (vue/angular/electron/fastapi/express/react-native/skill/test-sufficiency)
carry 19–30 calibration markers each — off-hunk confidence ceilings, SAFE never-flag lists,
per-check severity, confidence anchors. The gen-1 agents (bugs, architecture, compliance, impact,
framework-react) carry **zero**; the language agents near-zero.

Why it bites: with `+20 in_diff` (scoring.md:14) and bugs.md:49's *only* confidence example being
`95`, uncalibrated agents land findings in the Warning/Critical bands — which **"block finalize,
no acknowledgment path"** (scoring.md:50-51). So gen-1 output is enforcement-grade noise the
scorer structurally cannot discount, because its only discounting inputs (agent_confidence,
severity) are the exact fields these agents get no guidance on.

**Fix:** retrofit the gen-2 calibration block onto bugs, architecture, compliance, impact, and
the 4 language agents. Not new checks — calibration. Start with bugs + architecture (highest
volume / vaguest rubric).

### A2 — NEW-ABSORB: the scorer silently deletes distinct co-located findings  [HIGH] · B2
**Confirmed by the code's own comment** (`score.py:807`: "Members that lost the dedup are absorbed
into the survivor (not emitted)"). When two *distinct* same-domain defects land within ±2 lines,
`cross_confirm_group` keeps only the highest-scored member; the loser is appended to **neither**
`findings` nor `filtered[]` — it vanishes. A real second bug is unrecoverable, directly violating
the design's own "never silently drop" principle. Same root cause surfaces in framework-electron's
ipc-validation twin (B4). **Fix (within lock):** absorbed members → `filtered[]` with
`reason: "absorbed-into: <survivor-hash>"`.

### A3 — H-KNOB kill-shot: min_confidence above the critical floor annihilates real criticals  [HIGH] · B2
**Arithmetic confirmed.** `ANSWER-KEY.md:25` documents a critical surfaces at conf ≥ 50; the spec's
own illustrative config (`design.md:53`) is `min_confidence = 60`; `config.py:90` accepts `[0,100]`
with no warning. So a repo configured *exactly as the spec's example shows* silently drops criticals
at conf 50–59 that v2.7 surfaced — and because `min_confidence` filters **before** scoring, the
trust-adders (in_diff, cross-confirm) can never rescue them. Violates the v2.8 definition-of-done
("nothing real silently vanishes"). **Fix:** `config.py` warns/refuses when `min_confidence ≥ 50`.

### A4 — Tie-break representative is input-order-dependent  [HIGH] · B1 score.py
`score.py:805-808` — stable sort + `[0]`, so among equal-score cross-confirm members the emitted
representative (and its `stable_hash`, the medium-acknowledgment key) depends on agent-return
order. A Medium the owner dismissed can silently re-surface as unacknowledged next pass. Untested.

### A5 — Agent-forged `status:"persisted"` grants +15  [HIGH, security] · B1 score.py
`score.py:955` — `_valid_finding` (853) is crash-safety-only and never scrubs `status`, so an agent
(or attacker-authored diff) emitting `"status":"persisted"` forges the +15 persisted bonus — enough
to flip a band or resurrect a filtered finding.

### A6 — Malformed finding crashes the whole review  [HIGH] · B1 score.py
`_valid_finding` is dict-check-only; a non-hashable `severity`/`file` or lone-surrogate text crashes
`run()` (`SEVERITY_WEIGHT.get` :292 / `stable_hash.encode()` :59), and the fail-closed gate then
loses the entire batch. (Partially overlaps a post-v2.7 Phase-32 fix; two field types + surrogates
remain open at v2.7.)

### A7 — Path-containment fails open on empty $ROOT; copies have drifted  [Medium, security] · B1 bash
`case "$REAL/" in "$ROOT/"*` becomes `/*` (matches any absolute path) when `$ROOT` is empty. Four
bash copies fail open; the one Python copy (review.md:185-193) fails safe. **Five hand-copied sites
that disagree** — live drift in the family that guards the auto-committing path. Direct evidence for
extracting one tested `guard.py` (see the prose-to-code inventory).

### A8 — B4 (`/health`) answer-key exemption is gameable  [Medium→High as fleet-training risk] · B2
D-09 exempts auth findings by endpoint **name** (`/health`, `/healthz`, `/metrics`). Content, not
name, determines safety — name a data-leaking route `/health` and the fleet is trained silent. An
exploitable false-negative baked into the ground truth.

---

## Confirmed, lower severity

- **A9 · state-key raw branch name** (B1 bash) — `review.md:385` interpolates `$(git branch
  --show-current)` raw; a slashed branch (like the current dev branch) breaks the "flat filename"
  disjointness proof and restarts carry-forward. HIGH-correctness / Med-security.
- **A10 · deleted-file Codex downgrade** (B1 bash) — deep-review.md/fix.md lack review.md's
  missing-path-tolerant realpath, so a legit Codex finding about deleted code is withheld. Copy drift.
- **A11 · NaN → invalid JSON** (B1 score.py) — `json.dump` w/o `allow_nan=False`; a non-finite
  passthrough value emits the bare token `NaN`. MED–HIGH.
- **A12 · out-of-diff findings emitted despite docstring** (B1 score.py) — `in_diff` never drives a
  drop; contradicts "never report pre-existing." MED.
- **A13 · `//nolint`/`#noqa` marker misses** (B1 score.py) — SILENCED_MARKERS has spaced/one-case
  spellings; Go's `//nolint` and `#noqa`/`# NOQA` escape the −50. MED.
- **A14 · language-go deterministic FPs** (B4) — :17 flags idiomatic blocking channel sends; :18
  flags loopvar capture fixed in Go 1.22 (no version gate).
- **A15 · framework-angular :37 contradiction** (B4) — "plausibly off-hunk" (always true) can delete
  the hedged path so rxjs-leaks fires only on fully-visible components.
- **A16 · answer-key gate is axis-vs-site ambiguous** (B2 AK-1) — the "one mechanical line" isn't
  mechanical; B1/B3 mislabeled as globally safe (AK-2/AK-4).
- **A17 · codex sanitization is field-scoped** (B1 bash B5 / B2 H-CODEX-TRUST) — `problem`/`fix_hint`
  get no bidi/control-char strip yet flow to REVIEW.md and the fix-agent prompt; codex conf rides in
  floor-free and can win the dedup representative slot.

**Overstated (did NOT survive verification):** B1 score.py F5 (window-widen misalignment) — the code
already guards it; review.md:686 documents that a single-line `}` vs unchanged HEAD stays
`persisted`. Fable's one miss — a plausible claim where an explicit documented guard exists.

---

## Design challenges (sound, route to the B3 harness to settle)

From B2, all falsifiable with fixtures, all within-lock unless noted:
- **H-CORE reframe** — "agents over-report, scorer filters" mis-states the shipped system;
  filtering is substantially *agent-side*, in unverified prompt text, with no eval-CI. (Converges
  with B4's two-generations finding.)
- **H-DUP1** — the +10 hooks↔react-hook twin rewards *correlated* error (same base model, overlapping
  checklists), rescuing borderline FPs neither agent alone would surface.
- **H-DUP2 / H-LANE** — architecture↔impact and bugs↔RN-native double-report the same defect with no
  shared attribution, even under perfect obedience.
- **H-COUPLE restate** — config *does* change a surviving finding's score via cross-confirm set
  membership; the honest invariant is "zero-config output is byte-identical," not "config only
  relabels/filters."
- **O3** — the fix loop has no post-apply verification (typecheck/test); region-reread misses a fix
  needing an out-of-region call site. The only non-LLM reader for an owner who can't read diffs.

Parked (§B, post-v2.8, all falsifiable): B-SEV (severity-label instability swings score ±12),
B-XCONF (flat +10 prices same-model twins = cross-model codex equally), B-PROX (one ±2 radius serves
two behaviors that need different ones), B-REWEIGHT (raw agent confidence is the formula's noisiest
input — RESULTS shows the same item at conf 22/57/42).

---

## B3 — Product-quality harness (SCOPED, then SHELVED — never run)

**What B3 would have been:** the pass that measures the number vibe-check has never computed and
self-documents as missing (`RESULTS.md:64` — "does not measure recall across the full surface"). It
runs vibe-check on **real diffs with known outcomes** and scores two rates: **catch-rate** (does it
flag the real bug?) and **false-positive-rate** (does it stay quiet on clean code?). Method: the
`ANSWER-KEY` S-item/B-item model generalized beyond its single framework-fastapi fixture, using the
owner's real past diffs across triggarr, seedsyncarr, dashboard, and roonseek.

**Locked decisions:** organic-only sourcing (exclude bugs vibe-check itself found — circular);
committed reusable test set (re-run each milestone to catch review-quality regression);
`/deep-review` run N=3 per diff for stability.

**Why it was shelved:** the measurement step requires running `/deep-review`, a user-triggered
skill the assistant cannot invoke — so catch-rate inherently needs owner run-time (~30 runs for a
10-diff set). Running `score.py` directly tests only the scoring half. B3 is genuinely its own
sub-project, so it was banked clean rather than faked thin.

**What's already assembled (resume-ready):** 2–3 verified organic should-catch diffs — the anchor
is dashboard's unbounded-dict memory leak (`052845e`), plus triggarr's autoescape (`e11187e`) and
the subtle secret-in-logs case (`d47b4c2`, where an httpx exception stringifies the *arr API key
into a log line). Fable **volunteered as the variant-D reviewer** with a good protocol: give it the
diffs *without* the answer expectations, and score both reviewers against the same post-hoc
adjudication so neither is anchored.

**What B3 would settle that nothing else can:** the empirical half of H-DUP1/H-DUP2/H-LANE (twin
precision), B-XCONF (confirmation pricing), B-REWEIGHT (per-agent confidence calibration curves),
and the per-agent catch/FP rates seeded by B4's fixture recommendations. Combined with B4's
per-agent view, it would finally cover the whole pipeline — closing exactly the AK-5 gap (the answer
key tests only agent-side gates, never the scorer path).

**Status/location:** shelved, resume-ready at `docs/design/b3-ground-truth/B3-STATUS.md` (with the
verified buggy diffs under `b3-ground-truth/diffs/`).

---

## Still owed

- **`security.md` critique** — skipped from B4 (it trips Fable's safeguards); owes its own pass,
  likely Opus, like the bash review.
- **B3 execution** — needs an owner-driven run session; resume-ready per above.

## Where everything is saved

All on branch **`design/fable-review-prep`**, under **`docs/design/`**:

| File | Contents |
|---|---|
| **`FABLE-REVIEW-FINDINGS.md`** | **← this consolidated doc** |
| `fable-findings-score-py-v2.7.md` | B1 Python engine (full detail) |
| `fable-findings-bash-v2.7.md` | B1 shell/security (full detail) |
| `fable-findings-design-v2.7.md` | B2 design + answer-key (full detail) |
| `fable-findings-agents-v2.7.md` | B4 subagent efficacy (full detail) |
| `b3-ground-truth/B3-STATUS.md` | B3 shelved status + verified diffs |
| `agent-efficacy-critique.md`, `design-hypotheses.md`, `fable-code-review-prompt.md`, `product-quality-harness.md`, `fable-review-leverage-map.md`, `prose-to-code-inventory.md` | the prompts + prep that produced the above |
