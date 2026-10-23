# Phase 56: Verified fixes close - Research

**Researched:** 2026-10-23
**Domain:** vibe-check carry-forward closure (score.py verdict guard, carry_state.py, dispatch/collect/render prose)
**Confidence:** HIGH (all findings are from this repo's code, tests, and the owner's real iPlayarr state; no external libraries involved)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Reproduce first (owner rule, locked):** before any closure code changes, each failure path gets a recorded verdict on current code — a failing regression fixture, or a written "did not reproduce; dropped" note. No closure change ships for a path without a failing fixture. A path that does not reproduce is dropped, not replaced with invented work.

Not in this phase: decision identity/regrouping (Phase 57), "Fix all" label, broad recovery-guidance reconciliation, plain-English card answers, finalize `fix N` re-ask (Phase 58). Do not rebuild v2.12's initial confirmed-fix routing — extend it.

#### Current behavior (scouted 2026-10-23 — the baseline these decisions change)
- Ordinary carried findings are pinned by stored line number + first-line text (3-line window for low-entropy lines); no hunk/file/sha binding, no relocation (`score.py:1050-1114`, `phases/review/30-collect-score.md:52`).
- Auto-closure routes today: line gone → fixed-since-last; line text changed + the *originating* agent answers "resolved" (only for `needs-recheck`, `score.py:1254-1316`); fix-agent "obsolete" verdict with matching blob. A **persisted** (unchanged-line) finding cannot be closed by any recheck (`test_score.py:5343`).
- Recheck hints go only to the originating agent, never rerouted (`phases/review/20-dispatch.md:84,99`). Codex never receives hints. `/review` never runs Codex or deep-only lanes; both commands share one state file.
- v2.12 Phase 54 independent re-check exists **only for Needs-verification items** (`score.py:1326`): ladder own agent → `bugs` → `security` → first dispatched (`20-dispatch.md:94`); `fix` and `codex-adversarial` never eligible (`score.py:143-144,1229`); reviewer snapshot blob must equal repaired blob == HEAD (`30-collect-score.md:34`); only fix verdicts from the previous pass are honored, older ones rejected as stale (`score.py:1329`, `05-state.md:55,61`) — the "one pass" limit.
- Correction to the 52-11 deferred note: with an unchanged pinned line the status is `persisted`, not `needs-recheck` — even the right agent can't close it.

#### Who may confirm a fix
- **D-01:** When the originating agent can't re-check (always for Codex; deep-only lanes under `/review`), the v2.12 ladder applies to **ordinary carried findings too**, not just NV items: originating agent if dispatched → else `bugs` → else `security` → else first dispatched reviewer. `fix` and `codex-adversarial` are never eligible confirmers. One consistent rule everywhere.
- **D-02:** Closure bar = the confirmer's "resolved" verdict **plus** fresh-code proof (the code it reviewed is byte-identical to current HEAD for that file — reuse the existing blob check). Any "still applies" from an asked agent keeps it open. No passing-test-run requirement.
- **D-03:** A finding closed this way is **listed as closed** in the report — e.g. "Closed — fix confirmed by <reviewer>" with the commit where known — auditable without a confirmation prompt. No "accept these N?" step.

#### What triggers a re-check
- **D-04:** A finding whose pinned line is unchanged earns an independent re-check when **(a)** the code near the pinned line changed (e.g. lines added just beneath it — exact window is Claude's discretion), **or (b)** a commit since the finding was raised touched that file or its tests. Findings with no nearby change and no touching commit are not re-checked every run.
- **D-05:** Fixes made by hand or by Claude outside the fix agent (like the owner's review-pass commits) use the **same path** as fix-agent fixes. Closure depends on independent confirmation of current code, not on who authored the fix.
- **D-06:** Tests-only fixes (`arrFacade` case): the confirmer is shown both the flagged code **and the added tests** and judges whether the finding is resolved. Tests alone cannot close a finding the code still has.

#### Retry after inconclusive
- **D-07:** Inconclusive (no eligible reviewer dispatched, no answer, or blob mismatch) → retry on **every later run** while the code is unchanged and an eligible confirmer is dispatched. Ends only with "resolved" (closes) or "still applies" (stays open, stops auto-retrying). Removes the previous-pass-only limit for this case; cost is one re-check per such finding per run.
- **D-08:** If the code changes after an inconclusive check → **fresh start**: old evidence discarded as stale; the new code gets its own re-check under normal rules. Never close on evidence from older code.
- **D-09:** After "still applies", the finding is re-checked again **only after its code changes again** (v2.11 rule: never re-asked without new evidence).

#### /review vs /deep-review-only findings
- **D-10:** Under `/review`, `bugs`/`security` may confirm fixes for findings raised only by deep-review agents (`test-sufficiency`, `impact`, `architecture`, Codex) via the same ladder (D-01). E.g. a test-sufficiency finding closes when the confirmer sees the tests now exist.
- **D-11:** When a finding can't be re-checked in this run (no eligible confirmer), the report says the reason and the bounded ways forward — e.g. "Fix not yet confirmed — no eligible reviewer ran; will retry next run, or run /deep-review, or dismiss." Replaces the bare "awaiting your decision" for this path only; broader recovery-guidance reconciliation stays in Phase 58 (RECV-02).

#### Safeguards (locked, VFIX-06)
- **D-12:** Must keep regression coverage that (1) evidence from changed code is rejected as stale, (2) "still applies" keeps the finding open, (3) the existing suite stays green. Independence is never weakened: no self-confirmation by Codex or the fix agent; no closure without a fresh "resolved" verdict.

### Claude's Discretion
- Exact "nearby" window for D-04(a) and how "its tests" are associated with a file for D-04(b).
- How D-04/D-07 state is stored (extend carry-state fields vs new verdict kind), as long as single-writer and no-overwrite rules hold.
- Whether the six-row fixture is rebuilt synthetically (owner did not supply row IDs/SHAs) — recover from iPlayarr state if available locally, else synthesize an equivalent fixture covering all three shapes + four Codex-origin rows.
- Exact closed-row and not-yet-confirmed wording, within D-03/D-11.

### Deferred Ideas (OUT OF SCOPE)
- Structured "fixed-in <sha>" dismissal reason — not needed if D-01..D-07 work; revisit only if manual fixed-dismissals remain common.
- Wider evidence binding (hunk/semantic) for ordinary findings beyond the D-04 trigger — out of scope; identity rules are Phase 57's concern and only on reproduced failures.
- Broader recovery wording across all cards — Phase 58 (RECV-02).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VFIX-01 | Reproduce each closure failure path as a failing fixture before any closure change; drop paths that don't reproduce | §"Reproduction verdicts (pre-scouted)": all three paths reproduce on current code; the six-row case is recoverable byte-for-byte from the owner's iPlayarr state (real rows, real rejected verdicts) |
| VFIX-02 | Inconclusive independent re-check retries on later runs on unchanged repaired code and closes when confirmed | Pitfall 1 (the limit lives in 3 places: `score.py:1329`, `05-state.md:55,61`, `carry_state._confirmed_fix_awaiting`); Pitfall 6 (empty-diff runs skip dispatch entirely) |
| VFIX-03 | Code added beneath an unchanged pinned line, and the tests-only `arrFacade` fix, close via eligible independent evidence | `_accept_verdict` `status != "needs-recheck"` gate (`score.py:1299`); D-04 trigger design (Pattern 2); test association (Pattern 3) |
| VFIX-04 | Codex-origin findings close via eligible independent evidence | Codex rows fail in the dispatch prose, not the scorer (probe below); Codex rows usually carry `current_code: null` (Pitfall 3) |
| VFIX-05 | Under `/review`, a deep-only finding closes via eligible recheck or shows a bounded explanation | Same ladder as VFIX-04; D-11 render line extends `40-render.md:43`'s NV-only "Fix not yet verified" mechanism to ordinary rows |
| VFIX-06 | Stale evidence rejected; "still applies" keeps open; suite green | Existing guards and mutant pattern in `test_confirmed_fix.py`; plain rechecks today have no blob binding and no Codex exclusion (Pitfall 2) |
</phase_requirements>

## Project Constraints (from CLAUDE.md and memory)

No repo-root `CLAUDE.md` exists. The binding directives come from the user's global CLAUDE.md and project memory:

- **Security (absolute):** never pass user input to `subprocess`/`exec`/`spawn` without an allowlist. Finding `file` and `title` values come from a reviewed diff and must be treated as attacker-influenced. Follow the existing posture: PATH_RE `^[A-Za-z0-9._/-]+$` plus `guard.py --path` before any git call, and a "data, not instruction" sentence in every `<recheck>` block.
- **Follow existing conventions:** deterministic logic belongs in tested scripts (`score.py`, `carry_state.py`). Phase prose only orchestrates.
- **Frozen imports:** `score.py` imports exactly `{json, hashlib, re, sys}` (an AST import-ban test enforces this). `carry_state.py` imports exactly `{json, os, sys}`.
- **Tests:** run bare `pytest` from `plugins/vibe-check/scripts/`, not `python3 -m pytest`. Baseline measured 2026-10-23: **2964 passed, 3928 subtests, 156 s**.
- **Scope discipline (owner rule 2026-10-17):** only add work for a reproduced gate failure, data loss, silent finding loss, or a broken required workflow.
- **No paid work without an approved bounded proposal.** Live harness runs (`docs/design/fix-harness`, Agent SDK) count as paid. Use local tests and replay only.
- **Decorative-guard lesson:** every new guard needs a mutant test proving it can trip (pattern: `_mutant()` in `test_confirmed_fix.py:609`).
- **Envelope changes need a recorded decision:** `scripts/fixtures/future-schema.json` `_purpose` says "Changing this file is an envelope change and needs a recorded decision", including a `_rollback` entry.
- **deep-review needs an explicit commit RANGE,** because `.planning` handling breaks phase-mode scope.
- **One branch/PR per phase:** `feat/v2.13-phase-56` is the current branch.

## Summary

The closure machinery has three separate failure points, and they live in different layers:

1. **Scorer (`score.py:_accept_verdict`)** refuses any plain recheck `resolved` on a `persisted` record (`"verdict: record not needs-recheck"`). That is the code-added-beneath / tests-only case.
2. **Dispatch prose (`20-dispatch.md:99`)** never issues a hint for a record whose originating agent isn't dispatched (Codex always; deep-only lanes under `/review`). The scorer itself would already accept a `bugs` verdict on a Codex record's plain token, and also a `codex-adversarial` one. Probe run 2026-10-23: a plain request `{agent: codex-adversarial, agents: [bugs]}` on a needs-recheck record resolves; the same on a persisted record is rejected.
3. **One-pass limit for NV confirmed fixes,** enforced in three places: `score.py:1329` (`v["at_pass"] != pass_number - 1` → stale), `05-state.md:55` (forward only `at_pass == last pass`), and `carry_state._confirmed_fix_awaiting` (`at_pass == last["pass_number"]`).

The owner's six-row case is **recoverable from real local state**. `/Users/julianamacbook/iplayarr/.turingmind/state/format-53/45-bounded-integration-requests.json.archived-2026-10-20` holds passes 1–3:
- **Four Codex-origin rows:** `3dd41363`, `0249b52c`, `a264e9e9` (needs-recheck), and `22d360d9` (persisted on a blank pinned line).
- **One compliance row:** `2a01829c` (persisted).
- **One test-sufficiency `arrFacade` row:** `7bc336e7` (persisted). It was fixed by tests-only commit `64ac1c67`.
- Each pass's `filtered[]` records the actual failure: `verdict: record not needs-recheck` twice per row for AddFileEndpoint:204 (members `bugs`/`impact`), ArrDiscoveryHandoffService:201, and arrFacade:80, on both pass 2 and pass 3.
- The owner then dismissed all of them with "fixed in review-pass commits, verified on recheck".

The fix commits are in the iPlayarr git history (`a5a75387`, `8bb33807`, `a38f8cfd`, `849fc202`, `addc547a`, `64ac1c67`). The fixture should be built from this state, not synthesized.

**Primary recommendation:** Add one new routed request kind for ordinary carried records, e.g. `route: "independent"`, alongside the existing `confirmed-fix` route:
- **Who answers:** the ladder-chosen confirmer (D-01).
- **Freshness:** the request binds `snapshot_blob`, compared in `score.py` against a collect-time `head_blob` (D-02).
- **Status:** allowed on `persisted` records only when the orchestrator-supplied D-04 trigger fact holds, and on `needs-recheck` records whose origin lane isn't dispatched.
- **Closure label:** recorded as resolution source `recheck` with `verified_blob`, so the resolution enum doesn't change.
- **NV limit:** relax the `applied` age check from "previous pass" to "blob still equal and no settled still-applies".
- **D-09 memory:** add one scorer-written per-row field. This needs the recorded envelope decision.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Decide closure (accept/reject verdict) | `score.py` (pure script) | — | Single deterministic judge; prose never decides (`30-collect-score.md:36`) |
| Choose confirmer (ladder) | Dispatch prose (`20-dispatch.md`) | `score.py` re-validates (no `fix`/`codex-adversarial`) | Dispatch-time selection depends on the dispatched set. The scorer must enforce exclusions because prose can't be trusted alone (Pitfall 2) |
| Collect git facts (blobs, touched paths, cleanliness) | Orchestrator prose (Phase 0.5 / 2 / 3) | `guard.py` path validation | `score.py` / `carry_state.py` do no git I/O by contract |
| D-04 trigger evaluation | `score.py` (from orchestrator-supplied facts) | Orchestrator computes `git diff --name-only <anchor>..HEAD` | Keep the decision in the tested script; the prose only supplies raw paths |
| D-09 still-applies memory | `score.py` output (per-row field) | `state_shape` / `future-schema.json` | Single writer = scorer, like `snapshot` / `kept_open` |
| NV confirmed-fix age gate | `score.py` + `carry_state.py` + `05-state.md` | — | All three hold the one-pass rule today |
| Closed / not-yet-confirmed wording | Render prose (`40-render.md`, `templates/output-format.md`, `review-md-schema.md`) | `90-finalize.md` "Resolved by verification" | Rendering only; reads `resolved[]` / `filtered[]` reasons |

## Standard Stack

No new libraries. The phase is entirely inside the plugin's stdlib-only scripts and markdown phase prose.

### Core (existing, reuse)
| Component | Location | Purpose |
|-----------|----------|---------|
| `score.run` / `_accept_verdict` / `_confirmed_fix_recheck` / `_routed_request_ok` / `_request_matches` | `plugins/vibe-check/scripts/score.py:1199-1373, 1574-1910` | Verdict partition and guard. Extend, don't fork |
| `carry_forward_status` | `score.py:1050-1114` | Status (persisted / needs-recheck / fixed-since-last). **Do not change**: it feeds `stable_hash` goldens indirectly and the `persisted` +15 |
| `carry_state.record_fix_verdicts`, `_confirmed_fix_awaiting`, `_fix_closes`, `finalize_counts` | `scripts/carry_state.py:315-345, 501-536, 694-768` | `fix_verdicts` single writer and finalize counts |
| `state_shape` + `fixtures/future-schema.json` | `scripts/state_shape.py`, `scripts/fixtures/future-schema.json` | Closed envelope schema. Any new finding key goes here with a recorded decision |
| pytest (bare) + unittest classes | `plugins/vibe-check/scripts/test_*.py` | Existing framework |

**Installation:** none.

## Package Legitimacy Audit

No external packages are installed by this phase. Slopcheck isn't applicable. **Packages removed:** none. **Packages flagged:** none.

## Reproduction verdicts (pre-scouted — planner turns each into a failing fixture in Wave 0)

| Path | Reproduces on current code? | Failing layer | Evidence |
|------|-----------------------------|---------------|----------|
| P1: one-pass independent re-check limit (NV confirmed fix) | **YES** | `score.py:1329`; `05-state.md:55,61` ("Older `fix_verdicts` entries … are ignored"); `carry_state.py:329` | Pass-3 envelope with `confirmed_verdict(at_pass=1)` + routed request + `resolved` → `"verdict: stale fix verdict"` (existing test `test_confirmed_fix.py:563` asserts exactly this; it is the behavior to invert *for the inconclusive case*) |
| P2a: code added beneath an unchanged pinned line (persisted) | **YES** | `score.py:1299` `status != "needs-recheck"` | iPlayarr pass 2 & 3 `filtered[]`: `ArrDiscoveryHandoffService.ts:201` (compliance, dispatched, answered resolved) rejected `record not needs-recheck`; `test_score.py:5343` pins it |
| P2b: tests-only `arrFacade` fix | **YES** | Same gate; plus no D-04 trigger (only `tests/facade/arrFacade.test.ts` changed, `64ac1c67`) | iPlayarr pass 2 & 3: test-sufficiency answered resolved under `/deep-review`, rejected `record not needs-recheck` |
| P2c: Codex-origin rows (4) | **YES** | Dispatch prose `20-dispatch.md:99` (no hint is ever issued). Score-level acceptance already exists for plain tokens on needs-recheck records | iPlayarr: 3 Codex rows needs-recheck across passes 2–3 with no request/verdict; 1 Codex row (`22d360d9`, blank pinned line) persisted → also blocked by P2a gate |
| P3: `/review` cannot close a deep-only finding | **YES** (by construction; same mechanism as P2c) | `20-dispatch.md:99` + `/review` selection table never dispatches `test-sufficiency` / `impact` / `architecture` | `52-hardening…/deferred-items.md:39-47`. A score-level failing fixture: a test-sufficiency record under `command: "review"` with a ladder request to `bugs` and a fresh blob must close; today the request has no route kind to express it and, if persisted, is rejected |

**Planner note:** P2c and P3 fail in *prose*, so their failing fixtures need two legs:
1. A prose-contract test (pattern: `dispatch_routes_confirmed_fix_holds` in `test_confirmed_fix.py:782`) asserting the new ladder wording for ordinary records. It fails today because `20-dispatch.md:99` says "never rerouted".
2. A score-level test asserting the new route closes with a fresh blob and rejects without one.

## Architecture Patterns

### System Architecture Diagram

```
Phase 0.5 (05-state.md)
  state.passes[-1].findings ──filter status∈{new,persisted,needs-recheck}──► $CARRYFORWARD
  state.fix_verdicts (applied/obsolete) ──[TODAY: at_pass==last only]──► $FIX_VERDICTS_PREV
  NEW: per carried record → anchor sha (raised pass, or last still-applies pass)
       one `git diff --name-only <anchor>..HEAD` per distinct anchor → touched paths
        │
        ▼
Phase 2 dispatch (20-dispatch.md) — dispatched set known here
  for each carried record:
    origin dispatched AND status needs-recheck ─► plain <recheck> to origin (unchanged)
    NV + applied fix verdict ────────────────────► confirmed-fix routed block (existing ladder)
    NEW: eligible-for-independent (see Pattern 2) ─► ladder pick: origin→bugs→security→first
         (never fix / codex-adversarial) ─► routed block {route:"independent", snapshot_blob}
         + D-06: list touched associated test paths in the block
    no eligible confirmer ─► no block; scorer emits D-11 reason
        │  $RECHECK_REQUESTS
        ▼
Phase 3 collect (30-collect-score.md)
  agent JSON recheck_verdicts ─► verdicts[] (dispatch identity overrides self-claim)
  NEW: collect-time head_blob per routed-independent request file (same path validation +
       2 cleanliness checks as Phase 0.5) ─► envelope
        │
        ▼
score.py run() ── carry loop: status = carry_forward_status(...)   (unchanged)
               ── _judge → _accept_verdict
                    plain resolved: needs-recheck only (unchanged)
                    NEW independent route: asked agent ∉ {fix, codex-adversarial};
                        trigger fact true (persisted) or status needs-recheck;
                        snapshot_blob == head_blob (non-null); no still-applies
                        → resolution {source:"recheck", agents:[confirmer], verified_blob, commit_sha?}
                    still-applies → stays open + NEW memory field {fingerprint, at_pass}
                    no answer / no confirmer / blob mismatch → open + fixed `verdict: …` reason
        │ resolved[] / filtered[] / findings[]
        ▼
Phase 4 render (40-render.md) ── "✅ Resolved on recheck" (D-03 wording) / "Fix not yet confirmed: <reason>; ways forward" (D-11)
Phase 4.5 persist ── passes[] append (scorer output persisted unchanged)
Finalize (90-finalize.md) ── "Resolved by verification" = union of passes[].resolved[]
```

### Pattern 1: Extend the routed-request mechanism; don't build a parallel one
**What:** `_routed_request_ok` (`score.py:1216`) already validates `route`, `stable_hash`, `snapshot_blob`, and the `agents` exclusion. Add a second route constant next to `_CONFIRMED_ROUTE = "confirmed-fix"` and branch on it in `_accept_verdict`. Today, verdicts on routed tokens never act as plain rechecks (`score.py:1293-1296`), and an orphan routed verdict is rejected with `_R_ROUTED_ORPHAN`. The new route needs its own acceptance branch so it doesn't fall into the orphan rejection.
**Requirements for the new route:**
- `stable_hash` must be required. Routed requests already must name one (`_request_matches` line 1209), so **members (no stored hash) can't be routed**; see Pitfall 4.
- `snapshot_blob` must be a non-null string. A null means inconclusive (`_R_*_SNAPSHOT`-style reason).
- A collect-time `head_blob` must equal `snapshot_blob`. Recommended shape: the orchestrator adds `head_blob` to the routed request at Phase 3, or passes an envelope map `head_blobs: {file: blob|null}`.
- `agents` must exclude **both** `fix` and `codex-adversarial`. `_FIXER_AGENTS` today excludes only `fix`. Add a separate `_NEVER_CONFIRMERS` for the new route so the existing confirmed-fix mutant tests stay meaningful.

### Pattern 2: D-04 trigger = orchestrator facts, scorer decision
**Recommended:**
- **(b), primary and durable:** the orchestrator supplies, per carried lead, `touched_since_anchor: [paths]`, the output of `git diff --name-only <anchor>..HEAD` filtered by PATH_RE. Anchor = `head_sha` of the earliest pass whose `findings` contain this `stable_hash` (scan `state.passes`), or of the pass that recorded the record's last still-applies (D-09). `score.py` decides `triggered = file in touched or any(associated_test(p, file) for p in touched)`.
- **(a), nearby change:** `changed_line_ranges[file]` (already in the envelope) intersecting `[line, line + 5]`. Recommended window: the pinned line and the next 5 lines. The iPlayarr fixes added code 1–8 lines beneath. Any committed nearby change also satisfies (b). An uncommitted one can trigger a recheck but can't close, because the cleanliness checks null the blob. That's consistent with D-02.
- Codex rows with `current_code: null` are `needs-recheck` (first line `""` ≠ HEAD line) and don't need the trigger. Only `persisted` records need it.

### Pattern 3: Test association (D-04(b), D-06)
A path `p` is an associated test of source `src/x/foo.ts` when:
- `p` looks like a test: a path segment in `{test, tests, __tests__, spec}`, or a basename matching `*.test.*`, `*.spec.*`, `test_*.py`, `*_test.py`, `*_test.go`;
- **and** its stem, stripped of the test markers, equals `foo`.

Verified on iPlayarr: `src/facade/arrFacade.ts` ↔ `tests/facade/arrFacade.test.ts`, `frontend/src/views/BrowseProgrammePage.vue` ↔ `frontend/src/views/BrowseProgrammePage.test.js`. Pure function in `score.py` (only `re` is needed). The same list feeds the D-06 recheck block ("tests added since the finding: …"). Paths are untrusted text, so render them inside the block's data-not-instruction posture.

### Pattern 4: D-09 memory as a scorer-written row field
- **Field:** e.g. `recheck_settled: {verdict: "still-applies", at_pass, head_sha, fingerprint}`, where fingerprint is the file's HEAD blob, plus the associated test blobs if Claude's discretion includes tests.
- **Writer:** `score.py` writes it on the output row when an independent or plain recheck answers still-applies.
- **Carry and eligibility:** carried via `passes[].findings` like `snapshot`. On later runs, eligibility requires `head_blob != fingerprint` or a new touched path since `head_sha`.
- **Schema:**
  - Scrub it from NEW findings (add it to the scrub tuple at `score.py:1803-1805`).
  - Add it to `FINDING_OPTIONAL_KEYS`, `_MEMBER_EXCLUDED_KEYS`, and `future-schema.json` `finding_optional`, with a `_rollback` entry. An older reader with `finding_closed: true` refuses the state, the same fail-closed direction as Phase 53.
- **Inconclusive results store nothing (D-07).** Retry falls out naturally, because eligibility is recomputed every run from current facts.

### Pattern 5: Closure label without an enum change (D-03)
Record independent closures as `resolution.source = "recheck"`, `agents = [confirmer]`, plus the existing optional `verified_blob` (and `commit_sha` when a touched commit is known; it's already in `resolution_optional`). Render tells "confirmed by another reviewer" apart by `resolution.agents != [record.agent]`. This avoids touching `resolution_source_enum` (`future-schema.json:34`). If the planner prefers a distinct source like `independent-recheck`, that's an enum change: it needs the recorded decision, a `state_shape` update, render, and `90-finalize.md:214`.

### Anti-Patterns to Avoid
- **Relaxing `carry_forward_status` to call unchanged lines "needs-recheck".** This would move every persisted row's status, drop the +15 persistence bonus (`score.py:1870`), change scores and bands across the replay corpus, and churn `snapshot`. The scorer change must sit in the verdict guard, not the status function.
- **Making the plain (unrouted) path accept `resolved` on persisted records.** It has no blob binding, so it would close on stale evidence and break D-02 / VFIX-06.
- **Reusing the `confirmed-fix` route for ordinary findings.** That route requires an `applied` fix verdict (`_R_ROUTED_ORPHAN` otherwise) and NV band (`score.py:1325`). D-05 says hand fixes have no fix verdict.
- **Changing `fix-obsolete` pass-age semantics.** Out of scope. The D-07 relaxation applies to `applied` and the new route only.
- **Trusting prose for exclusions.** The scorer must reject `codex-adversarial` / `fix` confirmers on the new route itself.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HEAD blob read with safety | New git snippet | Phase 0.5's `head_blob` recipe (`05-state.md:55-61`: PATH_RE + `guard.py --path` + `rev-parse HEAD:<file>` + two `git diff --quiet` checks) | Already reviewed, includes attacker-path refusal and dirty-file nulling |
| Ladder choice text | New ladder | `20-dispatch.md` step 3 ladder sentence (locked by `dispatch_routes_confirmed_fix_holds`) | D-01 "one consistent rule everywhere" |
| Mutant tests | Ad-hoc monkeypatch | `_mutant(path, name, old, new)` (`test_confirmed_fix.py:609`) + `_trips` pattern | Proves each guard can trip |
| NV/score fixtures | New builders | `_nv`, `_nv_env`, `_nv_cf`, `_nv_rows` (`test_score.py:6238-6280`), `make_finding` (`:63`), `confirmed_verdict`/`routed_request`/`reviewer_verdict` (`test_confirmed_fix.py:283-325`) | Consistency with 54-16 tests |
| Replay-from-state fixture | Synthetic six rows | `_phase45_pass2`/`_p45_carryforward`/`_pass3_envelope` pattern (`test_score.py:5146-5215`) over a committed JSON in `scripts/fixtures/` | Same proven pattern as `phase45-loop-state.json` |
| State writes | Direct JSON edits in prose | `carry_state.py record-*` subcommands (only if a root family is chosen; Pattern 4 avoids needing one) | Single-writer rule |

## Common Pitfalls

### Pitfall 1: The one-pass limit lives in three places
**What goes wrong:** relaxing only `score.py:1329` does nothing, because `05-state.md:55` never forwards older `applied` entries, and `carry_state._confirmed_fix_awaiting` stops listing the item as awaiting after one pass.
**How to avoid:** change all three together, with a failing test per layer:
- `score.py`: an `applied` verdict honored at any age while `verified_blob == head_blob` and no settled still-applies;
- `05-state.md`: a prose lock;
- `carry_state.py`: `confirmed_fix_awaiting_recheck_hashes` still lists it at a later pass.

Existing tests `test_confirmed_fix.py:374` (`test_stale_verdict_stays_open`), `:563`, and `:248` (`test_stale_pass_never_closes`) assert the old behavior. Rewrite them into "stale = blob changed" tests rather than deleting them, so VFIX-06 stays covered.

### Pitfall 2: Plain rechecks have no blob binding and no Codex exclusion
Verified by probe on 2026-10-23:
- `score.run` resolves a needs-recheck record from a plain request with `agents: ["codex-adversarial"]`.
- It also resolves from `agents: ["bugs"]` on a Codex record.

Today, only the prose keeps this from happening. **Do not widen the plain path.** Put every new closure on the routed path, with scorer-enforced exclusions and a blob check. Whether to *also* harden the plain path against a `codex-adversarial` answer is in scope only if a failing fixture shows it's reachable. It isn't reachable today, because Codex receives no hints.

### Pitfall 3: Codex rows usually have `current_code: null`
In iPlayarr, 5 of 6 Codex leads stored `current_code: None`. `30-codex-collect.md` says Phase 3 backfills it, but the real state shows it didn't happen. Consequences:
- Status is `needs-recheck` on any non-blank pinned line, so "pinned line unchanged" is meaningless for Codex rows.
- On a blank pinned line it's `persisted` (`22d360d9`, canonical `''`).

The six-row fixture must preserve these null/blank shapes. Don't "fix" the backfill in this phase; that's not a reproduced closure failure.

### Pitfall 4: Members can't be routed, but they keep rows alive
Row `0249b52c` (Codex lead, AddFileEndpoint:204) carries members `bugs` and `impact` (persisted, no obligation hash). Both answered `resolved` and were rejected. Closing the Codex lead alone leaves the members, which regroup into a row (`_expand_members`; "a resolved lead never takes an unresolved member with it").

**How to avoid:** decide explicitly how members reach closure.
- **Recommended:** a member whose origin lane is dispatched gets its plain hint as today. When the D-04 trigger holds for its file, the plain request also carries `snapshot_blob`, and the scorer accepts `resolved` on a persisted member only with that blob binding (a "bound plain" request).
- **Alternative:** route by the member's obligation hash when present.

The six-row fixture must assert that the whole row disappears, not just the lead.

### Pitfall 5: The envelope schema is closed
Any new finding key (Pattern 4) or resolution source makes an older plugin refuse the state (`finding_closed`, `resolved_closed`). That's acceptable and consistent with Phase 53's fail-closed rollback, but it **requires a recorded decision** in `future-schema.json` `_purpose`/`_rollback`. It also needs a `test_state_shape.py` update, plus the `FINDING_OPTIONAL_KEYS` ↔ schema equality lock in `test_score.py`.

### Pitfall 6: A run with an empty incremental diff dispatches nobody
`05-state.md` step 5: an empty diff with a non-empty carryforward skips agent dispatch and goes straight to Phase 3. A "later run on unchanged repaired code" with no new commits therefore can't retry: there is no confirmer. Under `/review`, `bugs` and `security` are always on, so this is the **main real-world D-11 case**.

**Recommendation:** at minimum, D-11 wording must cover it ("no reviewer ran this pass"). Making it retry needs a recheck-only dispatch of ladder confirmers when pending independent rechecks exist. That's new runtime cost and a prose change to step 5, so it's listed under Open Questions for the owner.

### Pitfall 7: The fix is not always in the pinned file
`a264e9e9` (Codex, `V3ArrService.ts:412`) was fixed by `a38f8cfd`, which touched `ArrDiscoveryHandoffService.ts` and not `V3ArrService.ts`. Because it's `needs-recheck` (null current_code), it needs no trigger. The confirmer must still be allowed to judge via other files. The freshness bind stays on the pinned file's blob (D-02 "for that file"). Don't require that the touched commit includes the pinned file for needs-recheck records.

### Pitfall 8: Golden digest / stable_hash must not move
Every test file re-asserts `GOLDEN_DIGEST` (`test_score.py:43`). The new route adds verdict-guard branches only. Hash inputs are untouched.

### Pitfall 9: Replay must show no outcome change
54-16 ran `replay.py candidate` and `replay.py diff --roots all` (170 runs, 0 differing). The new route only fires on new request kinds, so the archived envelopes shouldn't change. Re-run the replay diff as the phase gate.

## Code Examples

### The gate that blocks persisted closure (current)
```python
# Source: plugins/vibe-check/scripts/score.py:1297-1302
resolving = [v for v in matched if v["verdict"] == "resolved"]
if resolving:
    if status != "needs-recheck":
        rejected.extend((v, "verdict: record not needs-recheck") for v in resolving)
```

### The one-pass limit (current)
```python
# Source: score.py:1329-1331
if v["at_pass"] != pass_number - 1:
    rejected.append((v, "verdict: stale fix verdict"))
    continue
```

### Fixture skeleton for the six-row reproduction (pattern, not final code)
```python
# Pattern: test_score.py:5146-5215 (_phase45_pass2 / _pass3_envelope)
SIX = os.path.join(HERE, "fixtures", "iplayarr45-six-row-state.json")  # trimmed copy of the archived pass 1-3 state
def _six_cf():
    st = json.load(open(SIX)); rows = st["passes"][2]["findings"]
    keep = {"3dd41363","0249b52c","a264e9e9","22d360d9","2a01829c","7bc336e7"}
    cf = [json.loads(json.dumps(f)) for f in rows if f["stable_hash"][:8] in keep]
    for e in cf:            # HEAD unchanged since pass 3: canonical = stored canonical
        e["canonical_window"] = None
        for m in e.get("members", []): m["canonical_line_content"] = e["canonical_line_content"]
    return cf
# Failing-first assertion (fails today): pass-4 envelope with ladder requests
# (bugs for Codex rows; compliance for 2a01829c; bugs under command="review" for 7bc336e7),
# fresh blobs, touched paths from the recorded fix commits, all verdicts "resolved"
# -> expect resolved[] covers all six hashes AND no finding row remains for those sites
# AND no decisions/dismissal needed.
```

## State of the Art (within this repo)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Only the originating agent closes; persisted never closes | Same (baseline) | v2.11 Phase 46 | Root cause of 999.22 |
| NV confirmed fix closes via independent ladder, one pass only | Same (baseline) | v2.12 Phase 54-16 (`1394c75`) | P1 to relax |
| Render "Fix not yet verified: …" for NV rows only | Same | 54-16 + F2 wording | Extend to ordinary rows for D-11 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The six rows the owner reported are `3dd41363, 0249b52c, a264e9e9, 22d360d9, 2a01829c, 7bc336e7` (4 Codex + compliance + test-sufficiency, all fixed by review-pass-1 commits). Rows `3e317388` and `70832798` were later Codex rows fixed separately | Summary / fixture | Fixture covers the wrong set; low risk, since the shapes match the roadmap description exactly. Owner can confirm |
| A2 | A nearby window of pinned line + 5 lines below is enough for D-04(a) | Pattern 2 | Too small → some fixes rely on (b) only. Harmless, because (b) covers committed changes |
| A3 | Recording independent closures under source `recheck` (no enum change) is acceptable to the owner as "Closed — fix confirmed by <reviewer>" | Pattern 5 | Planner may prefer a distinct source. Then it's an enum change plus a recorded decision |
| A4 | The trimmed iPlayarr state can be committed as a test fixture (it's the owner's own repo, with paths and titles only) | Fixture | If the owner objects, synthesize equivalent rows with the same shapes |

## Open Questions

1. **Retry on an empty-diff run (Pitfall 6)**
   - What we know: step 5 of `05-state.md` dispatches nobody when nothing changed since the last pass, so no retry can happen there.
   - What's unclear: whether the owner wants a recheck-only dispatch (one cheap Sonnet `bugs` call carrying only `<recheck>` blocks) on such runs.
   - Recommendation: in scope, D-11 wording names the reason ("no reviewer ran — nothing changed since the last pass; the next run with changes retries, or dismiss"). Raise the recheck-only dispatch to the owner as a product choice. It's a small new cost per run, so don't plan it silently.
2. **Members of a closing row (Pitfall 4)**
   - Recommendation: a "bound plain" request (adds `snapshot_blob`) for members when the trigger holds. The planner should lock this in the plan, because the six-row fixture's AddFileEndpoint row depends on it.
3. **Should D-09 fingerprints include associated test blobs?**
   - Recommendation: yes for findings whose trigger came from a test path (the `arrFacade` shape), so new tests re-earn a recheck after a still-applies.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 + pytest | test suite | ✓ | suite runs: 2964 passed / 156 s | — |
| git | fixture fact recovery | ✓ | — | — |
| iPlayarr repo + archived state | six-row fixture recovery | ✓ | `/Users/julianamacbook/iplayarr` (`.turingmind/state/format-53/45-bounded-integration-requests.json.archived-2026-10-20`; `.turingmind/tmp-45/` holds round-2 envelopes, not the six-row pass) | Synthesize |
| Agent SDK fix harness | live check | not used | — | Not needed; paid work, requires an approved proposal |

Note: a broad `find ~` is blocked by the holdout guard hook (`docs/design/holdout-v2.12/tools/holdout_guard.py`). Use explicit paths.

## Validation Architecture

(`workflow.nyquist_validation` is `false` in `.planning/config.json`. This section is included because the orchestrator asked for it.)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (bare) over unittest classes |
| Config file | none (run from `plugins/vibe-check/scripts/`) |
| Quick run command | `cd plugins/vibe-check/scripts && pytest -q test_confirmed_fix.py test_carry_state.py test_score.py -k "Verdict or Recheck or Confirmed or SixRow or Independent"` |
| Full suite command | `cd plugins/vibe-check/scripts && pytest -q` (≈2.5 min) |
| Replay gate | `replay.py candidate` + `replay.py diff --roots all` as in 54-16 (expect 0 differing) |

### Failing-first fixture plan (one per path; each must be RED on current HEAD `9ce6ad1` and recorded as such before the closure commit)

| Req | Fixture | Layer | Red-today assertion |
|-----|---------|-------|---------------------|
| VFIX-01/02 (P1) | `TestRetryAfterInconclusive` in `test_confirmed_fix.py`: pass 2 has no routed reviewer (`R_NO_REVIEWER`); pass 3 has the same `applied` verdict (at_pass 1), a routed `resolved`, and equal blobs | score | expects `resolved[0].resolution.source == "confirmed-fix"`; today: `verdict: stale fix verdict` |
| VFIX-02 (P1) | `carry_state.finalize_counts` on a 2-pass state whose `applied` is at pass 1 | carry_state | expects the hash in `confirmed_fix_awaiting_recheck_hashes`; today `[]` |
| VFIX-02 (P1) | prose lock on `05-state.md` (forward `applied` of any age) | prose | today the text says older entries are ignored |
| VFIX-02 (ordinary) | inconclusive (no answer) at pass N, then `resolved` at N+1 with unchanged blob, no new commit, no decision written | score | today persisted → rejected |
| VFIX-03 | six-row fixture (`fixtures/iplayarr45-six-row-state.json`): the `2a01829c` and `7bc336e7` rows | score | today `record not needs-recheck` (matches the real `filtered[]`) |
| VFIX-04 | six-row fixture: the 4 Codex rows with ladder→`bugs` routed requests | score + prose | prose lock fails (`never rerouted`); score: new route kind not accepted (`verdict: malformed`) |
| VFIX-05 | test-sufficiency record under `command: "review"`, ladder→`bugs`; and a no-confirmer variant expecting a fixed D-11 reason in `filtered[]` | score + render prose | no route; no D-11 reason string exists |
| VFIX-06 | (1) blob changed between dispatch and collect → open + reason; (2) still-applies → open + memory field; next run with unchanged blob issues no request (prose/eligibility) and is not closed by a stray `resolved`; (3) `fix` / `codex-adversarial` as confirmer → malformed | score | partly green today (existing tests); new-route variants red |
| VFIX-06 | mutants: remove blob check / trigger check / confirmer exclusion / still-applies check on the new route → each mutant closes | score | via `_mutant` |

### Sampling Rate
- **Per task commit:** the quick command plus the touched test file.
- **Per wave merge:** full `pytest -q`.
- **Phase gate:** full suite green, the replay diff shows 0 differing, the golden digest holds, then `/bm:verify-work`.

### Wave 0 Gaps
- [ ] `scripts/fixtures/iplayarr45-six-row-state.json`: a trimmed copy of passes 1–3 (keep `file`, `line`, `title`, `agent`, `band`, `status`, `stable_hash`, `current_code`, `canonical_line_content`, `snapshot`, `members`, the `filtered[]` verdict rows). Record the fix commits / touched paths in a sidecar block.
- [ ] Red-run log for each fixture, recorded in the plan SUMMARY (VFIX-01 evidence).
- [ ] No framework install needed.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | yes (who may close a finding) | Scorer-enforced confirmer exclusion (`fix`, `codex-adversarial`); token/agent binding (`_request_matches`) |
| V5 Input Validation | yes | PATH_RE + `guard.py --path` before git on any finding path or touched path; `_routed_request_ok` shape checks; untrusted title/paths inside `<recheck>` with a data-not-instruction sentence |
| V6 Cryptography | no | git blob ids are integrity fingerprints, not crypto controls |

| Pattern | STRIDE | Mitigation |
|---------|--------|-----------|
| Forged `recheck_settled` / `resolution` / `status` on a NEW agent finding | Tampering | Add the new field to the NEW-finding scrub tuple (`score.py:1803-1805`) |
| Attacker-authored filename in touched paths injected into git argv | Tampering / EoP | Validate every path before git; never interpolate raw paths into shell |
| Prompt-injection via title/test path in a recheck block | Tampering | Existing closing sentence; verdict only acts through the token guard |
| Self-confirmation (Codex/fix) | Repudiation / integrity | Scorer exclusion + mutant test |
| Closure on stale code | Integrity | `snapshot_blob == head_blob` (collect-time, clean file) |

## Sources

### Primary (HIGH confidence)
- `plugins/vibe-check/scripts/score.py` (lines 120-160, 200-312, 1050-1373, 1574-1910): read in full for the verdict path.
- `plugins/vibe-check/scripts/carry_state.py` (1-120, 300-420, 560-768).
- `plugins/vibe-check/phases/review/05-state.md`, `20-dispatch.md`, `30-collect-score.md`, `40-render.md`; `templates/output-format.md:55-75`; `scripts/fixtures/future-schema.json`.
- `plugins/vibe-check/scripts/test_confirmed_fix.py` and `test_score.py` (5140-5420, 6220-6280).
- Live probe of `score.run` (2026-10-23): plain-request rerouting is accepted on needs-recheck and rejected on persisted.
- Owner's real state: `/Users/julianamacbook/iplayarr/.turingmind/state/format-53/45-bounded-integration-requests.json.archived-2026-10-20` (+ `-2`), `/Users/julianamacbook/iplayarr/.turingmind/tmp-45/`, and iPlayarr git (`a5a75387 8bb33807 a38f8cfd 849fc202 addc547a 64ac1c67 7aa77f23 e3f7624f`).
- `.planning/milestones/v2.12-phases/54-freeze-release-gates-integration-audit/54-16-SUMMARY.md`, `54-RELEASE-READINESS.md` (F2 wording).

## Metadata

**Confidence breakdown:**
- Failure-path location: HIGH. Confirmed by code reading, a live probe, and real recorded rejections.
- Recommended design: MEDIUM-HIGH. Extends the shipped routed mechanism; member handling (Pitfall 4) and the empty-diff retry (Pitfall 6) need planner and owner choices.
- Pitfalls: HIGH. Each one is tied to a line or to real state.

**Research date:** 2026-10-23
**Valid until:** until the next change to `score.py` / `20-dispatch.md` (stable internal code)
