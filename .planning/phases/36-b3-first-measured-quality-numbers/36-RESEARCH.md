# Phase 36: B3 — first measured quality numbers - Research

**Researched:** 2026-07-02
**Domain:** Efficacy measurement / ground-truth test-set construction (git patch reconstruction, answer-key scoring against machine-readable review state, catch-rate/FP-rate reporting)
**Confidence:** HIGH

## Summary

This phase is **procedure and evidence construction**, not software engineering. It installs no packages, edits no scoring code (`score.py`/`test_score.py`/`config.py` are byte-frozen this milestone), and builds three deliverable layers strictly split by executor: (1) the assistant builds a run-kit — the third should-catch patch, ≥2 should-quiet patches, a per-diff answer key, and a copy-paste owner run-checklist; (2) the **owner** drives `/deep-review` N=3 per diff (~15–18 runs — the skill is user-triggered, the assistant CANNOT invoke it, so plans must structure the owner-run stage as a hard WAIT point); (3) the assistant scores each archived `.turingmind/state/<id>.json` against the key and writes the catch/FP report into `RESULTS-v2.9.md`.

The mechanics are all verified against real repo state. All four source repos (triggarr, seedsyncarr, dashboard, roonseek) are local git work trees on `main` at `~/<repo>`. All three should-catch fix commits exist and the fix diffs are small and clean. The scoring input is fully specified: `/deep-review` persists `state.passes[-1].findings[]` to `.turingmind/state/<PHASE_ID>.json`, each finding carrying `file`, `line`, `title`, `category`, `agent`, `orchestrator_score`, `band`, `status`, `stable_hash`, `attribution` — the exact fields the D-07 catch rule (site + axis + band) reads.

**One material contradiction surfaced that the planner MUST resolve before B3-01:** the dashboard-unbounded-dict case, listed in B3-STATUS as the verified "ANCHOR" should-catch, is **NOT organic** — its fix commit `052845e` carries the `DR3m-01` prefix (Deep-Review Medium finding #01), i.e. it was found by vibe-check's own `/deep-review`. The organic-only exclusion rule (B3-STATUS: "any fix tagged CR-/WR-/DR-/review-pass/codex is vibe-check-found and therefore EXCLUDED") disqualifies it. The two triggarr cases (secret-in-logs `d47b4c2`, autoescape `e11187e`) are clean-organic. See Open Question 1 — this needs an owner/planner call, because dropping dashboard leaves only 2 should-catch diffs against B3-01's ≥3 floor.

**Primary recommendation:** Plan three waves — (W1) assistant builds the run-kit (capture triggarr `d47b4c2^` parent + reconstruct all patches as reversed fix diffs, mechanically select should-quiet feature commits, write the answer key with A8/A16 semantics folded in, write the checklist); (W2) a hard WAIT-for-owner gate (owner runs N=3, archives state); (W3) assistant scores from archived state and appends the report to `RESULTS-v2.9.md` with the D-11 proceed/don't/need-more-data table. Resolve the organic-only dashboard contradiction (Open Q1) inside W1 planning, before any patch is committed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Should-quiet diff selection**
- **D-01:** The assistant selects should-quiet candidates MECHANICALLY from the four locked repos (triggarr, seedsyncarr, dashboard, roonseek): shipped FEATURE commits (never bug fixes), organic-only, whose touched lines were not modified by any later fix commit (verified via `git log`/`git blame` on the touched files from the commit to HEAD). Size-comparable to the should-catch diffs so diff size doesn't confound the FP number.
- **D-02:** The owner CONFIRMS the picks from a one-line-each summary before they are committed into the test set (a seconds-cost checkpoint; if the owner is AFK the picks land marked `owner_confirmed: false` and the run-checklist's first line asks for confirmation before run 1).
- **D-03:** Target 3 should-quiet diffs when strong candidates exist (3 catch + 3 quiet × N=3 = 18 runs, the budgeted ceiling from the design spec); hard floor 2 (B3-01).

**Run mechanics & evidence capture**
- **D-04:** Each test diff is committed in THIS repo as an applyable `.patch` under `docs/design/b3-ground-truth/diffs/` (should-catch = the fix commit REVERSED, per B3-STATUS). Runs happen in the source repo's local clone with the patch applied as UNCOMMITTED changes — vibe-check's default review target, simplest and most realistic.
- **D-05:** The run-checklist gives per-run copy-paste blocks: clean-tree check → `git apply <patch>` → `/deep-review` → ONE archival command that copies the run's `.turingmind/state/*.json` (and rendered report if present) into `docs/design/b3-ground-truth/runs/<diff-id>/run-<n>/` in this repo → revert (`git checkout -- . && git clean -fd` scoped to touched files). One command per step, resumable at any run boundary.
- **D-06:** The assistant scores from the ARCHIVED machine-readable state files, never from pasted transcripts. Missing/corrupt state for a run = that run is recorded `unscoreable` and repeated (never guessed).

**Scoring protocol — locked into the answer key BEFORE any run**
- **D-07:** A **catch** requires all three: (a) SITE — correct file + within the planted hunk; (b) AXIS — the finding names the defect mechanism in the key (this is the A16 fix applied: the key specifies site AND axis explicitly, and both are required); (c) BAND — rendered band ≥ the key's expected band. Right-site-wrong-axis or right-axis-below-band is recorded as `detected-below-threshold` — reported honestly, but a MISS in the headline number.
- **D-08:** An **FP** on a should-quiet diff = any critical or warning finding (the tool's own action bar). Medium/low findings on should-quiet diffs are recorded as noise-notes, NOT FPs.
- **D-09:** N=3 aggregation: per-run and per-diff fractions reported; headline catch-rate = total catches / total should-catch runs; headline FP-rate = FP runs / total should-quiet runs. No rounding rule (2/3 never becomes "caught").
- **D-10:** The A8 fix folds into the key as written in FABLE-REVIEW-FINDINGS.md §A8 (the `/health` name-exemption is not gameable-by-naming; the planner reads that section for exact semantics).

**Design-challenge decision rule**
- **D-11:** Pre-register COARSE decision rules in the answer key doc before runs: a table mapping each B3-gated challenge (H-CORE/H-DUP/H-LANE/B-SEV/B-XCONF/B-PROX/B-REWEIGHT) to the measured failure mode that would implicate it (e.g. right-site-below-band misses → B-SEV/B-REWEIGHT; duplicate-driven noise → H-DUP). Coarse thresholds: high catch + ~zero FP → "don't proceed — park the challenges"; low catch or high FP → "proceed on the implicated challenge(s)"; middle → "need more data — grow the committed set next milestone". Coarse on purpose: small N cannot support fine thresholds, and the report must say so.

### Claude's Discretion
- Exact should-quiet candidate commits (within the D-01 mechanical criteria).
- Patch/answer-key/checklist file naming and layout under `docs/design/b3-ground-truth/`.
- Report table shapes inside RESULTS-v2.9.md.
- Whether roonseek transcript mining happens (B3-STATUS marks it deferred-optional — default SKIP; only if should-quiet candidates come up short).

### Deferred Ideas (OUT OF SCOPE)
- roonseek walkthrough-transcript mining for additional organic bugs — default SKIP this phase unless should-quiet candidates come up short.
- Scorer design challenges + `CATEGORY_DOMAIN` twins — explicitly GATED on this phase's numbers (milestone D-05); the report's proceed/don't/need-more-data statement is the input to next-milestone scoping, never in-phase work.
- `security.md` critique pass — needs a dedicated Opus session (standing deferral).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **B3-01** | A committed ground-truth test set exists: ≥3 should-catch + ≥2 should-quiet reviewable diffs, ORGANIC-ONLY, with a per-diff answer key (expected finding + expected band) folding in the A8 (`/health` name-exemption) and A16 (axis-vs-site ambiguity) fixes | Patch-reconstruction mechanics verified (all fix commits exist locally); A8/A16 semantics extracted below; answer-key template (`ANSWER-KEY.md`) and finding schema mapped. **BLOCKER: dashboard "ANCHOR" is non-organic (`DR3m-01`) — see Open Q1; the ≥3 floor is at risk with only 2 clean-organic should-catch diffs.** |
| **B3-02** | The owner runs `/deep-review` on each test diff (N=3 per diff) and every run is scored against the answer key | `/deep-review` is user-triggered → plans MUST structure the owner-run stage as a WAIT point. State-file schema (`state.passes[-1].findings[]`) and archival command mapped. D-07 catch rule maps directly onto the persisted fields. |
| **B3-03** | A catch/FP report lands in `plugins/vibe-check/docs/efficacy/` with honest limitations and an explicit proceed/don't/need-more-data statement for the B3-gated design challenges | `RESULTS-v2.9.md` is the append target (Phase-35 D-01 — one doc per milestone; the smoke-proof section is structured for a clean append). D-11 decision-rule table pre-registered before runs. Limitations pattern proven in `RESULTS.md`/`RESULTS-v2.7.md`. |
</phase_requirements>

## Architectural Responsibility Map

This phase has no runtime tiers to assign — it is a measurement/evidence phase. The relevant "tiers" are the three executor layers, which the plan MUST keep strictly separated (mis-assigning a run step to the assistant is the single biggest failure mode).

| Capability | Primary Owner | Secondary | Rationale |
|------------|--------------|-----------|-----------|
| Patch reconstruction (reverse fix diffs → `.patch`) | Assistant (this repo) | — | Pure git; deterministic; assistant can fully verify with `git apply --check` |
| Should-quiet candidate selection | Assistant (mechanical, D-01) | Owner confirms (D-02) | Assistant mines; owner gives a seconds-cost one-line confirm |
| Answer-key authoring (site+axis+band, A8/A16) | Assistant | — | Pre-registered BEFORE any run so scoring can't be reverse-fit |
| Run-checklist authoring | Assistant | — | Pure copy-paste for a PM owner; no mid-run judgment |
| **Running `/deep-review` N=3** | **Owner ONLY** | — | **User-triggered skill; assistant CANNOT invoke it. This is a hard WAIT gate.** |
| State archival (state.json → this repo) | Owner (one copy-paste cmd) | — | Runs in source-repo clone; checklist bridges back to this repo |
| Scoring archived state vs key | Assistant | — | Reads machine-readable state (D-06), never transcripts |
| Report authoring (append to RESULTS-v2.9.md) | Assistant | — | Extends the milestone doc (D-01); plain-language + tables |

## Standard Stack

**No external packages. No installs. This phase adds zero dependencies.**

Tooling is git + the already-installed vibe-check plugin + a text editor (the assistant's Write/Edit tools). There is no `## Package Legitimacy Audit` section because nothing is installed — the Package Legitimacy Gate is N/A for this phase.

### Tools in play (all present, verified)
| Tool | Purpose | Verified |
|------|---------|----------|
| `git` (source repos) | Reconstruct reversed fix patches; mine feature commits; `git apply` in the clone | `[VERIFIED: git rev-parse]` all four repos are work trees on `main` |
| `git apply` / `git apply -R` | Apply the reversed-fix patch as uncommitted changes | `[ASSUMED]` standard git; validate with `git apply --check` in the checklist |
| vibe-check `/deep-review` | The measured system (owner-run) | `[VERIFIED]` installed cache `~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/` exists; matches repo `plugin.json` 2.8.0 |
| `.turingmind/state/<id>.json` | Machine-readable per-run findings (scoring input) | `[CITED: commands/review.md Phase 4.5, commands/deep-review.md Phase 4.5]` |

## Runtime State Inventory

> This phase writes files into THIS repo (patches, answer key, checklist, archived state, report) and runs reviews in OTHER repos on uncommitted changes. There is no rename/refactor, but there IS cross-repo state to track — the inventory is adapted to that.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no databases or datastores hold a renamed key. B3 produces new committed files only. | None — verified: this phase creates `docs/design/b3-ground-truth/{diffs,runs}/` + appends to `RESULTS-v2.9.md`; touches no datastore. |
| Live service config | `/deep-review` writes `.turingmind/state/<PHASE_ID>.json` + optional `.turingmind/reviews/<ts>/` **in the source-repo clone**, not this repo. The archival step (D-05) copies state BACK into this repo's `docs/design/b3-ground-truth/runs/`. | Checklist must (a) name the exact source-clone state path and (b) copy it back — the state does NOT auto-land in this repo. |
| OS-registered state | None. | None — verified: no scheduler/daemon involvement. |
| Secrets/env vars | The triggarr secret-in-logs bug logs a real *arr API key pattern. The captured `.BUGGY.py`/patch contains the buggy log line but NOT a live secret (the key is runtime-injected, not in source). | Verify the captured patch/BUGGY file contains no literal secret before committing (it won't — the leak is a runtime `exc` object, not a hardcoded value). |
| Build artifacts | None. `score.py`/`test_score.py`/`config.py` byte-frozen; no package rebuild. | None. |

**The key cross-repo question:** after the owner runs `/deep-review` in `~/triggarr`, the findings live in `~/triggarr/.turingmind/state/…json` — NOT in this repo. The checklist's archival command is what bridges the two. If it's missing or wrong, the assistant has nothing to score (D-06 → run recorded `unscoreable`, repeated).

## Architecture Patterns

### System flow (input → measured number)

```
                       ┌─────────────── ASSISTANT (this repo, Wave 1) ───────────────┐
  fix commit           │  git show <fix>  ──REVERSE──►  <diff-id>.patch              │
  (organic)            │       │                              │                       │
  d47b4c2 (triggarr)   │       │  parent = <fix>^  ──►  <diff-id>.BUGGY.<ext> (opt)   │
  e11187e (triggarr)   │       ▼                              ▼                       │
  [dashboard? Open Q1] │  feature commits ──D-01 mechanical select──► should-quiet   │
                       │       │                     patches (owner confirms, D-02)   │
                       │       ▼                                                       │
                       │  ANSWER KEY (per-diff: site + axis + expected band;          │
                       │   A8/A16 folded; D-11 decision-rule table) ── pre-registered │
                       │       │                                                       │
                       │       ▼                                                       │
                       │  RUN-CHECKLIST (copy-paste, per-run, resumable)              │
                       └──────────────────────────┬──────────────────────────────────┘
                                                  │  ⇩ HARD WAIT GATE ⇩
                       ┌────────────── OWNER (source-repo clones, Wave 2) ────────────┐
                       │  STEP 0: cache CONTENT-assert == repo plugin.json            │
                       │  per diff, per run n∈1..3:                                   │
                       │    clean-tree check → git apply <patch> → /deep-review       │
                       │    → copy .turingmind/state/*.json → runs/<id>/run-<n>/      │
                       │    → revert (checkout + clean, scoped)                       │
                       └──────────────────────────┬──────────────────────────────────┘
                                                  │  ⇩ archived state back in THIS repo ⇩
                       ┌────────────── ASSISTANT (this repo, Wave 3) ─────────────────┐
                       │  read state.passes[-1].findings[] per run                    │
                       │  D-07 score: SITE ∧ AXIS ∧ BAND≥expected → catch             │
                       │  D-08 score: any C/W on should-quiet → FP                    │
                       │  D-09 aggregate: catch-rate, FP-rate (no rounding)           │
                       │  D-11 map failure modes → proceed/don't/need-more-data       │
                       │  APPEND report to RESULTS-v2.9.md (honest limitations)       │
                       └──────────────────────────────────────────────────────────────┘
```

### Component responsibilities

| Artifact | Path (this repo) | Produced by | Consumed by |
|----------|------------------|-------------|-------------|
| Reversed-fix should-catch patches | `docs/design/b3-ground-truth/diffs/<id>.patch` | Assistant W1 | Owner (git apply) |
| Captured parent (buggy) file — triggarr secret-in-logs | `docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.BUGGY.py` (discretion) | Assistant W1 | Reference/reconstruction |
| Should-quiet patches | `docs/design/b3-ground-truth/diffs/<id>.patch` | Assistant W1 | Owner (git apply) |
| Per-diff answer key | `docs/design/b3-ground-truth/ANSWER-KEY-b3.md` (discretion) | Assistant W1 | Assistant W3 (scoring) |
| Owner run-checklist | `docs/design/b3-ground-truth/RUN-CHECKLIST.md` (discretion) | Assistant W1 | Owner W2 |
| Archived per-run state | `docs/design/b3-ground-truth/runs/<id>/run-<n>/state.json` | Owner W2 | Assistant W3 (scoring) |
| Catch/FP report | `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` (append) | Assistant W3 | Owner / next milestone |

### Pattern 1: Reversed-fix patch = the planted bug (D-04)
**What:** A should-catch diff is `git show <fix>` REVERSED — the fix's removal of the bug becomes the diff's addition of the bug. Applied to the clone HEAD (which contains the fix), a reversed patch re-introduces the bug as an uncommitted change.
**When to use:** All three should-catch diffs.
**Mechanics (verified):**
```bash
# In the SOURCE repo clone (e.g. ~/triggarr). Produce a patch that ADDS the bug back:
git -C ~/triggarr show d47b4c2 -- triggarr/clients/base.py > /tmp/fwd.patch   # the FIX (removes bug)
# Reverse it so applying re-introduces the bug on top of current HEAD (which has the fix):
git -C ~/triggarr diff d47b4c2 d47b4c2^ -- triggarr/clients/base.py > <id>.patch
# ^ diff FROM fixed TO buggy = the patch that, applied to fixed HEAD, yields the buggy state.
# Validate it applies cleanly to the clone's current tree:
git -C ~/triggarr apply --check <id>.patch
```
> **Caveat the planner must build in:** `git diff <fix> <fix>^` produces a patch relative to the `<fix>` tree, which is NOT the clone's current HEAD (HEAD has advanced past the fix). If the touched file changed between `<fix>` and HEAD, the patch won't apply. Verified for these three: the touched files (`triggarr/clients/base.py`, `triggarr/web/routes.py`) are small and the fixes are recent; `git apply --check` in the checklist is the gate. If a patch fails `--check` against current HEAD, the fallback is to reconstruct against a pinned base SHA (the checklist can `git checkout <fix>` detached, apply the reverse, review there) — but the D-04 default (apply to current-HEAD uncommitted tree) is preferred and should be validated in W1 before the checklist ships.

### Pattern 2: Mechanical should-quiet selection (D-01)
**What:** A shipped FEATURE commit (not a fix) whose touched lines no later commit modified — so reviewing it as a diff surfaces no real defect, making any critical/warning an FP.
**Verified candidate pool (abundant across all four repos):**
```
triggarr:    0adb833, 5b5cb4d, 0ec174b, cde32d3, 36dd6ba, 9f2c238  (feat(76-*))
seedsyncarr: f497cd2, cb92dbd, 80ab3ba                             (feat(114-*))
dashboard:   b31a699, d5c81c3, fa27a8b, 94ba30f, 47f23d5          (feat(74-*))
roonseek:    a45cad5, ed1c23d, 355c57f, ebfff5a, 45d7319, 022880f (feat(30-*))
```
**Selection procedure (per candidate):**
```bash
# 1. Confirm it's a feature, not a fix, and organic (no DR-/CR-/WR-/review-pass/codex tag):
git -C ~/<repo> show -s --format='%s%n%n%b' <sha> | grep -iE 'DR[0-9]|CR-|WR-|review-pass|codex' && echo "EXCLUDE" || echo "organic-ok"
# 2. Confirm no later fix touched its lines (untouched-since):
git -C ~/<repo> log --oneline <sha>..HEAD -- <touched-files> | grep -iE 'fix' # any fix hit → weaker candidate
# 3. Size-comparable to should-catch diffs (D-01):
git -C ~/<repo> show --stat <sha>
```
> **Note:** Some `feat(76-03)` commits *delete tests* or *strip fixtures* — those touch test/fixture files, which is a weaker should-quiet surface (a reviewer legitimately has less to say). Prefer feature commits that add product code (e.g. seedsyncarr `f497cd2` "shared bounded name-resolution retry", roonseek `a45cad5` "render discography codec badges") over test-only churn, and prefer Python/TS product files matching the languages the owner relies on vibe-check for.

### Pattern 3: The answer key encodes SITE + AXIS + BAND (D-07, A16 fix)
**What:** Each should-catch entry pre-registers three fields the scorer checks independently: the SITE (file + planted hunk line range), the AXIS (the defect mechanism the finding must name — e.g. "secret/PII in logs", not just "logging issue"), and the expected BAND floor. All three required for a catch; two-out-of-three is `detected-below-threshold` (a MISS in the headline). This is the A16 fix made mechanical (see A16 semantics below).
**Answer-key row shape (extends `ANSWER-KEY.md`'s S-item model):**
```
| diff-id | file:hunk-lines | AXIS (mechanism the finding must name) | expected band | A8/A16 note |
```

### Anti-Patterns to Avoid
- **Scoring from the chat transcript** (D-06 violation): the transcript shows only a Filtered *count*, not per-finding site/axis/band — it cannot separate a catch from a below-threshold detection. Always score from `state.passes[-1].findings[]`.
- **Reverse-fitting the key to the runs:** the key MUST be committed before any run (D-07/D-11 both say "before any run"). A key edited after seeing output is not measurement.
- **Assistant invoking `/deep-review`:** it is user-triggered. Any plan task whose action is "run `/deep-review`" is invalid — it must be an owner-checklist step behind a WAIT gate.
- **Rounding N=3** (D-09): 2/3 is 2/3, never "caught."
- **Using a non-organic diff as ground truth:** the dashboard `DR3m-01` case (see Open Q1) is the live instance of this trap.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reproducing the planted bug | A hand-typed buggy file | `git diff <fix> <fix>^ > .patch` (reversed fix) | Byte-exact, provenance-traceable, `git apply --check`-validated |
| Reading per-run findings | Parse the chat transcript | `state.passes[-1].findings[]` from `.turingmind/state/<id>.json` | The transcript loses site/axis/band; the state JSON is the single source (D-06) |
| Computing the band | Re-derive from `agent_confidence` | Read the persisted `band` field | `score.py` is the single writer of `band`/`orchestrator_score`/`stable_hash` (ROBUST-01); recomputing risks drift |
| A new results doc | `RESULTS-v3.md` or a fresh file | Append to `RESULTS-v2.9.md` | Phase-35 D-01: ONE results doc per milestone; the smoke-proof section is structured for a clean append |
| A new answer-key format | Invent a schema | Extend `ANSWER-KEY.md`'s S-item/B-item + expected-band model | Proven template; reviewers already understand it |

**Key insight:** every deliverable in this phase already has a template or a git primitive that produces it deterministically. The *only* non-deterministic input is the owner's `/deep-review` output — which is exactly why N=3 stability and no-rounding aggregation exist.

## The A8 and A16 answer-key fix semantics (folds into the key — B3-01)

Both are `[VERIFIED: docs/design/FABLE-REVIEW-FINDINGS.md]` (read at lines 111-114 for A8, 135-136 for A16).

### A8 — `/health` name-exemption is gameable (§A8, line 111)
> "D-09 exempts auth findings by endpoint **name** (`/health`, `/healthz`, `/metrics`). Content, not name, determines safety — name a data-leaking route `/health` and the fleet is trained silent. An exploitable false-negative baked into the ground truth."

**What must change in the key:** the existing `ANSWER-KEY.md` B4 bait exempts a `/health` route *by name* (its expected behavior is `silent`). The A8 fix says an exemption must be justified by **content** (the route genuinely exposes nothing sensitive), not by the string `/health`. **Fold into the B3 key:** any should-quiet entry that relies on an auth-exemption must state the *content* reason it's safe (e.g. "returns a static liveness bool, touches no ORM row"), and the key must NOT grant a silent-pass to a route merely because it is named `/health`. Concretely: if a B3 should-quiet diff includes a `/health`-named route, the key documents WHY its silence is correct on content grounds — and if a should-catch diff ever hid a real leak behind a `/health` name, naming alone would NOT downgrade the expected band. For B3's actual diffs (triggarr secret-in-logs, autoescape, feature commits) there is likely no `/health` route in scope, so the A8 fold is a *documented rule in the key's preamble* ("exemptions are content-justified, never name-justified") rather than a per-row change — but the planner must state that rule explicitly so the key is not itself gameable.

### A16 — answer-key gate is axis-vs-site ambiguous (§A16, line 135)
> "the 'one mechanical line' isn't mechanical; B1/B3 mislabeled as globally safe (AK-2/AK-4)."

**What must change in the key:** the old `ANSWER-KEY.md` "one mechanical line" (`EFF-02 PASS = S1,S2,S3 surface ≥70 AND B1-B5 stay <70`) conflates *right site* with *right axis* — a finding at the right file:line but naming the wrong defect mechanism was implicitly credited. **Fold into the B3 key (this is D-07's origin):** a catch requires SITE **and** AXIS **and** BAND as three independent gates. The key must name, per should-catch entry, the specific AXIS (defect mechanism) the finding must identify — not just the location. A finding that lands on `base.py:230` but calls it "log formatting inconsistency" instead of "API key / secret leaked into logs" is right-site-wrong-axis → `detected-below-threshold`, a MISS. And a bait/should-quiet diff is not "globally safe" — the key states which axis it is safe *on* (per D-08, only critical/warning on that diff is an FP). This is the single most important semantic in the phase: it is what makes the catch-rate number honest.

## Common Pitfalls

### Pitfall 1: Stale installed-plugin cache poisons every run
**What goes wrong:** The owner runs `/deep-review` against an installed cache that isn't the fixed post-Fable/post-35 system, so the measured numbers describe old code.
**Why it happens:** 33-02 wiring is prose-only and does NOT bump the version string — version parity (installed 2.8.0 == repo 2.8.0, which currently HOLDS) is NECESSARY but NOT SUFFICIENT.
**How to avoid:** Checklist STEP 0 must be a **CONTENT** assertion, not a version check — the exact pattern Phase 35 used and recorded: `grep -c 'SCOPE_ARGS' <installed>/commands/review.md` (expect ≥1, Phase 35 saw 13) and `grep -c 'Codex off via' <installed>/commands/deep-review.md` (expect ≥1, Phase 35 saw 2), against `~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/`. If either is 0, resync (rsync repo → cache) and **relaunch the process** before run 1.
**Warning signs:** "poisoned 4 of the last 5 milestones" (STATE.md). This is the recurring risk of this codebase.

### Pitfall 2: The dashboard "ANCHOR" case is not organic
**What goes wrong:** Using `dashboard-unbounded-dict` (`052845e`) as a should-catch diff silently violates the organic-only rule — the bug was found by vibe-check's own `/deep-review` (`DR3m-01`). Scoring a catch on it is circular self-testing, exactly what B3-STATUS forbids.
**Why it happens:** B3-STATUS lists it as the verified "ANCHOR" and its parent file is already captured in `diffs/` — it looks done. The `DR3m-01` provenance is only visible in the fix commit body, not in B3-STATUS's summary table.
**How to avoid:** Resolve Open Q1 in W1 planning before committing any dashboard patch. Options: (a) drop dashboard, source a third organic should-catch from another repo (triggarr/seedsyncarr/roonseek); (b) keep it explicitly as a *non-headline* extra and exclude it from the catch-rate denominator; (c) owner rules it organic-enough (it was a human/Opus fix even if a DR pass surfaced it — but the rule as written excludes DR-tagged fixes categorically).
**Warning signs:** any should-catch fix commit whose message contains `DR[0-9]`, `CR-`, `WR-`, `review-pass`, or `codex`.

### Pitfall 3: A reversed patch won't apply to current HEAD
**What goes wrong:** `git apply <id>.patch` fails in the clone because the touched file drifted between `<fix>` and HEAD.
**Why it happens:** The patch is generated relative to the `<fix>` tree; the clone is at `main` HEAD, ahead of `<fix>`.
**How to avoid:** W1 must run `git apply --check <id>.patch` against the clone's current HEAD for every patch and fix or re-base any that fail (pin a base SHA in the checklist for that diff). Bake `git apply --check` as the checklist's pre-apply gate so the owner never hits a dirty half-apply.
**Warning signs:** `error: patch does not apply` / `error: while searching for:`.

### Pitfall 4: Missing/corrupt state file → silent scoring gap
**What goes wrong:** The owner's run didn't write (or the copy-back missed) `.turingmind/state/<id>.json`, and the assistant scores a run it can't actually see.
**Why it happens:** State writes to the SOURCE clone; the archival copy-back is a separate step; `/deep-review` writes state under the resolved `$PHASE_ID` filename (from Phase 0.5), which on a plain uncommitted-diff run is a default key, not a GSD phase name — the checklist must name the exact glob (`.turingmind/state/*.json`) so no run is missed.
**How to avoid:** D-06 is the rule — missing/corrupt state = record the run `unscoreable` and repeat it, never guess. The archival command must copy the whole `.turingmind/state/` glob, and the assistant's scoring step must assert the file exists + parses before scoring.
**Warning signs:** empty `runs/<id>/run-<n>/`, or a state JSON that doesn't parse / lacks `passes[-1].findings`.

### Pitfall 5: Diff size confounds the FP number
**What goes wrong:** should-quiet diffs much larger than should-catch diffs inflate or deflate FP rate (more lines = more surface for a stray warning).
**Why it happens:** feature commits can be large; fix commits are small.
**How to avoid:** D-01's size-comparability clause — pick should-quiet feature commits whose stat is comparable to the should-catch diffs (the three should-catch fixes are ~4-8 lines each — very small; pick small, focused feature commits or a coherent slice).

## Code Examples

### The scoring input — what `/deep-review` persists (D-06 reads this)
```json
// Source: commands/review.md Phase 4.5 (pass entry) + templates/agent-output-schema.md
// .turingmind/state/<PHASE_ID>.json → state.passes[-1] :
{
  "pass_number": 1,
  "head_sha": "<clone HEAD>",
  "timestamp": "<ISO 8601 UTC>",
  "mode": "review",
  "diff_range": "<resolved range>",
  "agents_run": ["bugs", "security", "impact", "..."],
  "findings": [
    {
      "id": "sec-001",
      "file": "triggarr/clients/base.py",   // ← D-07 SITE check
      "line": 233,                          // ← D-07 SITE check (within planted hunk?)
      "title": "API key leaked into warning log via exc",  // ← D-07 AXIS check (names the mechanism?)
      "category": "security",               // ← corroborates AXIS
      "agent": "security",
      "orchestrator_score": 92,
      "band": "critical",                   // ← D-07 BAND check (≥ expected?)
      "status": "new",
      "stable_hash": "…",                   // ← identity across passes (do NOT recompute)
      "attribution": "…"
    }
  ]
}
```
> The scorer reads `file`+`line` (SITE), `title`+`category` (AXIS), and `band` (BAND). `orchestrator_score`/`band`/`stable_hash` are score.py's single-writer fields — read them, never recompute (ROBUST-01, Phase 4.5 note).

### Should-catch #3 — triggarr secret-in-logs, the bug the reversed patch re-adds
```python
# Source: git show d47b4c2 (REVERSED = the planted bug). triggarr/clients/base.py:230-233
# The BUG (what the reversed patch adds back):
logger.warning(
    "{app}: Unexpected HTTP error: {exc}",   # exc is an httpx error whose URL carries the *arr API key
    app=self._app_name,
    exc=exc,                                  # ← full exception, leaks the key + (elsewhere) the payload
)
# The FIX (d47b4c2, what the clone HEAD has): logs {status}=exc.response.status_code / {count}=exc.error_count()
# ANSWER-KEY AXIS: "secret/PII (API key) leaked into logs" — NOT "log formatting". Expected band: warning+ (security).
```

### Checklist per-run block shape (D-05 — copy-paste, resumable)
```bash
# Source: derived from D-05 + commands/review.md Phase 4.5 + owner-is-PM constraint (36-CONTEXT specifics)
# --- diff <id>, run <n> ---
cd ~/<repo>
git status --porcelain                                  # STEP: must be clean before apply
git apply --check docs/…/<id>.patch && git apply docs/…/<id>.patch   # apply the planted bug
# → owner runs: /vibe-check:deep-review        (ONE user action — the only non-copy-paste step)
mkdir -p <this-repo>/docs/design/b3-ground-truth/runs/<id>/run-<n>
cp .turingmind/state/*.json <this-repo>/docs/design/b3-ground-truth/runs/<id>/run-<n>/   # archive
git checkout -- . && git clean -fd <touched-paths>      # revert to clean HEAD
```
> The `/deep-review` line is the ONLY step the owner performs by hand; everything else is copy-paste. STEP 0 (cache content-assert) runs once before run 1 of the whole session.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-agent, single-repo, throwaway, planted fixture (`ANSWER-KEY.md`) | Multi-repo, organic, **committed** ground-truth set with catch/FP aggregation | This phase (B3) | First aggregate catch-rate/FP-rate the tool has ever had (closes `RESULTS.md:64` gap) |
| Answer-key "one mechanical line" (site conflated with axis) | Three-gate catch: SITE ∧ AXIS ∧ BAND (A16 fix, D-07) | This phase | Right-site-wrong-axis correctly counts as a MISS — honest number |
| `/health` exempt by name | Exempt by content (A8 fix, D-10) | This phase | Ground truth not gameable-by-naming |
| Cross-confirm +10 keyed on title substring | Keyed on `(file, line ±2)` + category-domain overlap (ROBUST-02) | v2.4 | AXIS-based dedup; a shared title token fires nothing — relevant when scoring co-located findings |

**Deprecated/outdated:**
- Scoring from transcripts (loses site/axis/band) — superseded by state-JSON scoring (D-06).
- Title-substring cross-confirm — superseded by category-domain overlap (ROBUST-02); do not assume a shared title implies a duplicate when reading co-located findings.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `git apply -R` / `git diff <fix> <fix>^` reverse-patch mechanics behave as standard git | Pattern 1 | LOW — validated by `git apply --check` in W1 before the checklist ships; a failing patch is caught, not shipped |
| A2 | The three should-catch reversed patches apply cleanly to their clones' current HEAD | Pattern 1 / Pitfall 3 | MEDIUM — touched files may have drifted since `<fix>`; W1 must run `--check` per patch; fallback is a pinned-base reconstruction |
| A3 | Feature-commit candidates listed are organic and untouched-since (only shas confirmed to exist + carry `feat`; per-candidate organic + untouched-since checks not yet run) | Pattern 2 | MEDIUM — the D-01 procedure (grep for DR-/CR-/WR-, `git log <sha>..HEAD -- files`) must run per final pick; some `feat(76-03)` commits are test/fixture churn (weaker surface) |
| A4 | On a plain uncommitted-diff `/deep-review`, state writes to `.turingmind/state/<default-key>.json` (not a GSD phase name) | Pitfall 4 / Code Examples | LOW — checklist copies the whole `.turingmind/state/*.json` glob, so the exact filename doesn't matter |
| A5 | The triggarr autoescape fix (`e11187e`) is a strong should-catch (XSS surface visible in diff) | Standard Stack / B3-STATUS | LOW-MEDIUM — B3-STATUS lists it verified; but the fix is a Starlette-API migration (`Jinja2Templates(env=…)`), and the reversed diff shows `autoescape=True` being REMOVED — a reviewer must recognize that losing the preconfigured env re-enables the XSS surface, which is subtler than a raw `autoescape=False`. Answer-key AXIS wording must be precise. |

## Open Questions

1. **The dashboard "ANCHOR" should-catch is non-organic — resolve before B3-01.** [HIGH IMPACT]
   - What we know: `052845e` (dashboard-unbounded-dict) is listed in B3-STATUS as the verified ANCHOR should-catch, and its parent file is already captured in `diffs/`. But its commit message is `fix(42): DR3m-01 …` and its body references `DR3w-01` — `DR` = Deep-Review finding, i.e. vibe-check found this bug. The organic-only rule (B3-STATUS) categorically excludes `DR-`-tagged fixes.
   - What's unclear: whether the owner intends the categorical DR-exclusion to override the ANCHOR listing (the two locked sources contradict), or whether "the bug was a real memory leak a human/Opus fixed after a DR pass surfaced it" counts as organic-enough.
   - Recommendation: **Treat as EXCLUDED per the rule as written.** Plan for two clean-organic should-catch diffs (triggarr `d47b4c2` secret-in-logs, triggarr `e11187e` autoescape) plus a THIRD sourced from a non-vibe-check-found fix in another repo (mine seedsyncarr/roonseek/triggarr for a human-found `fix(...)` with no DR-/CR-/WR- tag). Surface this to the owner as a D-02-style one-line confirm before committing. If no clean third exists, either (a) keep dashboard as a labeled non-headline extra outside the catch-rate denominator, or (b) accept a 2-should-catch set and note it in the B3-03 limitations (below the B3-01 ≥3 floor — this is a requirements risk the owner must sign off).

2. **Does `/deep-review` on a plain uncommitted diff dispatch Codex, and should B3 runs include it?** [MEDIUM]
   - What we know: `/deep-review` defaults to `codex=auto`; the host is Codex-installed+authenticated (Phase 35 confirmed `ready:true`). Codex findings would be attributed `codex-adversarial` in the scored survivors.
   - What's unclear: whether B3 measures native-only or native+Codex catch-rate. Codex non-determinism adds variance to an already-small N.
   - Recommendation: measure the **default** configuration (`codex=auto`) since that is what the owner actually runs — but the checklist should record the per-run Codex outcome line (joined/skipped) so the report can note whether Codex contributed to any catch. Do NOT force `--codex off` (that measures a config the owner doesn't use). State this choice in the report's method section.

3. **Should `/review` (≥80) also run, or only `/deep-review` (≥70)?** [LOW]
   - What we know: the harness design (product-quality-harness.md) suggested reporting at both thresholds; CONTEXT/REQUIREMENTS specify only `/deep-review` N=3 (~15-18 runs).
   - Recommendation: `/deep-review` ONLY, per B3-02's exact text and the run budget. Reporting both thresholds would double the owner's run count. Note the single-threshold scope in limitations.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `git` | Patch reconstruction, mining, apply | ✓ | system | — |
| triggarr clone | 2 should-catch diffs (`d47b4c2`, `e11187e`) | ✓ | `~/triggarr` @ `main` f4366a2 | — |
| dashboard clone | ANCHOR case (⚠ non-organic — Open Q1) | ✓ | `~/dashboard` @ `main` 52650a2 | — |
| seedsyncarr clone | should-quiet / third should-catch source | ✓ | `~/seedsyncarr` @ `main` 3db8b48 | — |
| roonseek clone | should-quiet / optional mining | ✓ | `~/roonseek` @ `main` da2b0c0 | — |
| vibe-check installed cache | owner `/deep-review` runs | ✓ | `2.8.0` (== repo plugin.json 2.8.0) | Resync+relaunch if content-assert fails (Pitfall 1) |
| Codex CLI | `/deep-review` codex=auto (Open Q2) | ✓ | codex-cli 0.133.0 (Phase 35) | `auto` degrades to native-only if unavailable |
| `timeout`/`gtimeout` | Codex 300s watchdog | ✓ | `/opt/homebrew/bin/timeout` (Phase 35) | Codex skips with `no-timeout-binary` slug |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** Codex (degrades to native-only under `auto`); stale cache (resync+relaunch).

## Validation Architecture

> `.planning/config.json` was not found in this repo (checked — no config.json under `.planning/`). Per the "absent = enabled" rule the section is included, but B3 is a measurement/evidence phase, not a code-change phase — there is no new code to unit-test. The "validation" here is the *scoring protocol itself*, which is pre-registered in the answer key.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` (existing, `plugins/vibe-check/scripts/`) — but NOT exercised this phase (score.py byte-frozen) |
| Config file | `plugins/vibe-check/scripts/` (existing suite: 356 passed, 221 subtests per Phase 35) |
| Quick run command | `cd plugins/vibe-check/scripts && pytest -q` (regression guard only — nothing new to add) |
| Full suite command | same |

### Phase Requirements → Validation Map
| Req ID | Behavior | Validation Type | Command / Method | Exists? |
|--------|----------|-----------------|------------------|---------|
| B3-01 | Test set exists, organic, ≥3+≥2, keyed, A8/A16 folded | manual-structural | `git apply --check` per patch; organic-grep per source commit; key-review checklist | ✅ (git primitives) |
| B3-02 | N=3 per diff, every run scored vs key | manual (owner-run) + assistant-scored | owner checklist + assistant reads `state.passes[-1].findings[]` per run | ✅ (state schema) |
| B3-03 | Report with honest limitations + proceed/don't/need-more-data | manual-authoring | append to RESULTS-v2.9.md; D-11 decision table | ✅ (append target) |

### Sampling Rate
- **Per patch (W1):** `git apply --check <id>.patch` against the clone HEAD — the mechanical gate that a patch is usable.
- **Per run (W2, owner):** clean-tree assertion before apply; state-file existence+parse assertion after.
- **Phase gate:** `git diff --quiet -- score.py test_score.py config.py` exits 0 (byte-frozen invariant held); existing suite green.

### Wave 0 Gaps
- None — no new test files. The score.py/config.py suite is a regression guard only (assert byte-frozen). The novel "validation" is the answer-key protocol (D-07/D-08/D-09), authored as a deliverable, not as code.

## Security Domain

> `security_enforcement` config not found (no `.planning/config.json`) — treated as enabled. This phase writes no application code and installs nothing, so the ASVS surface is minimal. The one real security consideration is **not leaking a live secret into a committed artifact**.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no | — |
| V6 Cryptography | no | — |
| V7 Errors & Logging | **yes (subject matter)** | The triggarr should-catch bug IS a logging-secrets defect (V7.3 — no sensitive data in logs). The captured patch documents the bug; it must not embed a live key. Verified: the leak is a runtime `exc` object (API key injected at runtime), so the source/patch carries no literal secret. |

### Known Threat Patterns for this phase
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Committing a live *arr API key inside the secret-in-logs BUGGY file/patch | Information Disclosure | The key is runtime-injected, not in source — verify the captured artifact contains no literal secret before commit (it won't; the bug is `exc=exc`, an object) |
| Archived `.turingmind/state/*.json` echoing a secret from a run | Information Disclosure | State findings quote `current_code` snippets; the buggy line is `exc=exc` (no literal key) — but W1 should spot-check the first archived state before bulk-archiving to confirm no runtime secret was captured into a committed file |

## Sources

### Primary (HIGH confidence)
- `docs/design/b3-ground-truth/B3-STATUS.md` — locked decisions, verified should-catch table, 5-step resume plan `[CITED]`
- `docs/design/FABLE-REVIEW-FINDINGS.md` §A8 (line 111), §A16 (line 135) — answer-key fix semantics `[VERIFIED: read in-session]`
- `plugins/vibe-check/commands/review.md` Phase 0.6, Phase 4.5 — config resolution + state persistence schema `[VERIFIED: read in-session]`
- `plugins/vibe-check/commands/deep-review.md` Phase 4.5, Phase 2c — state write + codex dispatch `[VERIFIED: read in-session]`
- `plugins/vibe-check/templates/agent-output-schema.md` + `templates/output-format.md` — finding field shape `[VERIFIED: read in-session]`
- `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md` — S-item/B-item template + scoring math `[VERIFIED: read in-session]`
- `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` — append target, structured-for-append `[VERIFIED: read in-session]`
- `docs/design/product-quality-harness.md` — full harness design `[CITED]`
- Source repos on disk — all four are git work trees on `main`; fix commits `d47b4c2`/`e11187e`/`052845e` verified present; feature-commit candidates enumerated `[VERIFIED: git]`
- `~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/` exists; repo plugin.json = 2.8.0 `[VERIFIED: filesystem + grep]`

### Secondary (MEDIUM confidence)
- Feature-commit candidate shas (existence + `feat` prefix confirmed; per-candidate organic + untouched-since checks deferred to W1 per D-01) `[VERIFIED existence: git; organic status ASSUMED pending per-pick check]`

### Tertiary (LOW confidence)
- None material.

## Metadata

**Confidence breakdown:**
- Standard stack (tools/no-installs): HIGH — nothing to install; all git primitives and the state schema verified in-session.
- Architecture (three-wave, executor split, WAIT gate): HIGH — the user-triggered `/deep-review` constraint and state-file scoring path are documented and verified.
- Patch mechanics: HIGH for existence/shape (all fix commits + diffs read); MEDIUM for clean-apply-to-current-HEAD (must `--check` per patch in W1 — Pitfall 3 / A2).
- Answer-key semantics (A8/A16): HIGH — both Fable sections read verbatim; D-07 is the mechanical A16 fix.
- Organic-only compliance: HIGH-confidence finding that the dashboard ANCHOR is NON-organic (`DR3m-01` verified in the commit body) — this is the phase's one real planning blocker (Open Q1).
- Pitfalls: HIGH — the cache-content-assert and organic-exclusion pitfalls are both grounded in verified repo state, not training knowledge.

**Research date:** 2026-07-02
**Valid until:** 2026-08-01 (stable — no fast-moving dependencies; the only volatility is source-repo HEAD advancing, which would only affect patch clean-apply, caught by `git apply --check`).
