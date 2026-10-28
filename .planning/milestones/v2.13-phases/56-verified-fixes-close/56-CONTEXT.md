# Phase 56: Verified fixes close - Context

**Gathered:** 2026-10-23
**Status:** Ready for planning

<domain>
## Phase Boundary

A fix that independent evidence confirms closes its carried finding on a later run — without a dummy code change, a "fixed in <sha>" dismissal, or a repeated owner confirmation — while stale evidence is still rejected and still-applicable findings stay open. Covers VFIX-01..06 (remaining 999.22): the one-pass independent re-check limit, the reported six-row case (code added beneath an unchanged pinned line, tests-only `arrFacade` fix, four Codex-origin rows), and `/review` unable to close a `/deep-review`-only finding.

Not in this phase: decision identity/regrouping (Phase 57), "Fix all" label, broad recovery-guidance reconciliation, plain-English card answers, finalize `fix N` re-ask (Phase 58). Do not rebuild v2.12's initial confirmed-fix routing — extend it.

**Reproduce first (owner rule, locked):** before any closure code changes, each failure path gets a recorded verdict on current code — a failing regression fixture, or a written "did not reproduce; dropped" note. No closure change ships for a path without a failing fixture. A path that does not reproduce is dropped, not replaced with invented work.
</domain>

<decisions>
## Implementation Decisions

### Current behavior (scouted 2026-10-23 — the baseline these decisions change)
- Ordinary carried findings are pinned by stored line number + first-line text (3-line window for low-entropy lines); no hunk/file/sha binding, no relocation (`score.py:1050-1114`, `phases/review/30-collect-score.md:52`).
- Auto-closure routes today: line gone → fixed-since-last; line text changed + the *originating* agent answers "resolved" (only for `needs-recheck`, `score.py:1254-1316`); fix-agent "obsolete" verdict with matching blob. A **persisted** (unchanged-line) finding cannot be closed by any recheck (`test_score.py:5343`).
- Recheck hints go only to the originating agent, never rerouted (`phases/review/20-dispatch.md:84,99`). Codex never receives hints. `/review` never runs Codex or deep-only lanes; both commands share one state file.
- v2.12 Phase 54 independent re-check exists **only for Needs-verification items** (`score.py:1326`): ladder own agent → `bugs` → `security` → first dispatched (`20-dispatch.md:94`); `fix` and `codex-adversarial` never eligible (`score.py:143-144,1229`); reviewer snapshot blob must equal repaired blob == HEAD (`30-collect-score.md:34`); only fix verdicts from the previous pass are honored, older ones rejected as stale (`score.py:1329`, `05-state.md:55,61`) — the "one pass" limit.
- Correction to the 52-11 deferred note: with an unchanged pinned line the status is `persisted`, not `needs-recheck` — even the right agent can't close it.

### Who may confirm a fix
- **D-01:** When the originating agent can't re-check (always for Codex; deep-only lanes under `/review`), the v2.12 ladder applies to **ordinary carried findings too**, not just NV items: originating agent if dispatched → else `bugs` → else `security` → else first dispatched reviewer. `fix` and `codex-adversarial` are never eligible confirmers. One consistent rule everywhere.
- **D-02:** Closure bar = the confirmer's "resolved" verdict **plus** fresh-code proof (the code it reviewed is byte-identical to current HEAD for that file — reuse the existing blob check). Any "still applies" from an asked agent keeps it open. No passing-test-run requirement.
- **D-03:** A finding closed this way is **listed as closed** in the report — e.g. "Closed — fix confirmed by <reviewer>" with the commit where known — auditable without a confirmation prompt. No "accept these N?" step.

### What triggers a re-check
- **D-04:** A finding whose pinned line is unchanged earns an independent re-check when **(a)** the code near the pinned line changed (e.g. lines added just beneath it — exact window is Claude's discretion), **or (b)** a commit since the finding was raised touched that file or its tests. Findings with no nearby change and no touching commit are not re-checked every run.
- **D-05:** Fixes made by hand or by Claude outside the fix agent (like the owner's review-pass commits) use the **same path** as fix-agent fixes. Closure depends on independent confirmation of current code, not on who authored the fix.
- **D-06:** Tests-only fixes (`arrFacade` case): the confirmer is shown both the flagged code **and the added tests** and judges whether the finding is resolved. Tests alone cannot close a finding the code still has.

### Retry after inconclusive
- **D-07:** Inconclusive (no eligible reviewer dispatched, no answer, or blob mismatch) → retry on **every later run** while the code is unchanged and an eligible confirmer is dispatched. Ends only with "resolved" (closes) or "still applies" (stays open, stops auto-retrying). Removes the previous-pass-only limit for this case; cost is one re-check per such finding per run.
- **D-08:** If the code changes after an inconclusive check → **fresh start**: old evidence discarded as stale; the new code gets its own re-check under normal rules. Never close on evidence from older code.
- **D-09:** After "still applies", the finding is re-checked again **only after its code changes again** (v2.11 rule: never re-asked without new evidence).

### /review vs /deep-review-only findings
- **D-10:** Under `/review`, `bugs`/`security` may confirm fixes for findings raised only by deep-review agents (`test-sufficiency`, `impact`, `architecture`, Codex) via the same ladder (D-01). E.g. a test-sufficiency finding closes when the confirmer sees the tests now exist.
- **D-11:** When a finding can't be re-checked in this run (no eligible confirmer), the report says the reason and the bounded ways forward — e.g. "Fix not yet confirmed — no eligible reviewer ran; will retry next run, or run /deep-review, or dismiss." Replaces the bare "awaiting your decision" for this path only; broader recovery-guidance reconciliation stays in Phase 58 (RECV-02).

### Safeguards (locked, VFIX-06)
- **D-12:** Must keep regression coverage that (1) evidence from changed code is rejected as stale, (2) "still applies" keeps the finding open, (3) the existing suite stays green. Independence is never weakened: no self-confirmation by Codex or the fix agent; no closure without a fresh "resolved" verdict.

### Claude's Discretion
- Exact "nearby" window for D-04(a) and how "its tests" are associated with a file for D-04(b).
- How D-04/D-07 state is stored (extend carry-state fields vs new verdict kind), as long as single-writer and no-overwrite rules hold.
- Whether the six-row fixture is rebuilt synthetically (owner did not supply row IDs/SHAs) — recover from iPlayarr state if available locally, else synthesize an equivalent fixture covering all three shapes + four Codex-origin rows.
- Exact closed-row and not-yet-confirmed wording, within D-03/D-11.
</decisions>

<specifics>
## Specific Ideas

- Owner's reported case (2026-10-20, iPlayarr phase 45, vibe-check 2.12.0): six open rows already fixed; pinned lines unchanged (fixes added code beneath; `arrFacade` fix was tests-only); four of six were Codex-origin; reviewers + full test runs confirmed each fix, yet each row needed a "fixed in <sha>" dismissal. This is the primary reproduction target.
- Success = the owner never has to type "fixed in <sha>" for a fix an eligible reviewer has confirmed on current code.
- Local tests and existing replay evidence first; no paid runs. Any live workflow check needs a separately bounded, owner-approved proposal.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §"Phase 56: Verified fixes close" — goal, success criteria, preserved source context (six-row example, /review path)
- `.planning/REQUIREMENTS.md` — VFIX-01..06
- `.planning/milestones/v2.12-phases/52-hardening-accepted-fix-harness/deferred-items.md` lines 39-47 — "/review can't close deep-only finding" origin
- `.planning/milestones/v2.12-ROADMAP.md` — what v2.12 Phase 54 shipped (confirmed-fix re-check) and must not be rebuilt

### Closure logic (code)
- `plugins/vibe-check/scripts/score.py` — `carry_forward_status` :1050-1114, NV relocation :1117-1136, independent recheck :1229-1251, verdict guard :1254-1316, confirmed-fix :1326-1329, persistence bonus :1870
- `plugins/vibe-check/scripts/carry_state.py` — closure rules :31-59, fix verdict handling :315-331, decision evidence :358-368
- `plugins/vibe-check/phases/review/05-state.md` (:53-68), `20-dispatch.md` (:18-34, :84-99), `30-collect-score.md` (:34-52, :74), `40-render.md` (:43, :81), `50-fix-loop.md` (:221-225)
- `plugins/vibe-check/phases/shared/90-finalize.md` (:53) — closed-in-commit render
- `plugins/vibe-check/phases/deep-review/20-selection.md` — deep-only lanes, coverage gate
- `plugins/vibe-check/templates/review-md-schema.md` (:27)

### Tests and harness to reuse
- `plugins/vibe-check/scripts/test_score.py` — TestCarryForwardStatus :964, TestVerdictGuard :5295, TestVerdictFixObsolete :5416, TestKeptOpenMultiPass :6100, TestNeedsVerificationCarry :6651
- `plugins/vibe-check/scripts/test_confirmed_fix.py` — TestIndependentRecheck :447 (+ mutant tests)
- `plugins/vibe-check/scripts/test_carry_state.py` — TestPhase45EndToEnd :1850, TestDecisionEvidence :1222
- `plugins/vibe-check/scripts/fixtures/phase45-loop-state.json`
- `docs/design/fix-harness/` — accepted-fix SDK harness (tools/fixharness.py, harness_seed.py refuses non-rechecking agents; fixtures/py-clamp-01). Not `scripts/replay.py` (runs with no carry-forward).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- v2.12 independent-recheck ladder + blob-freshness check (NV path) — extend to ordinary carried findings rather than build a parallel mechanism.
- `carry_state.py record-decisions` / single-writer state families — new verdict/retry fields go through these.
- Mutant-test pattern in `test_confirmed_fix.py` — use to prove each new guard can trip (decorative-guard lesson).

### Established Patterns
- Deterministic logic lives in tested scripts (`score.py`, `carry_state.py`); phase prose only orchestrates.
- Single writer per state field family; no-overwrite archives; format-53 state dir.
- Evidence-bound decisions: nothing re-asked without new evidence; nothing expires by age/pass count.

### Integration Points
- Dispatch hint issuance (`20-dispatch.md`) — must issue re-check hints to the ladder confirmer for persisted-but-touched findings and Codex/deep-only findings.
- Scoring guard (`score.py` verdict guard) — must accept a ladder confirmer's "resolved" for persisted findings that met D-04, with freshness.
- Render (`40-render.md`, `review-md-schema.md`) — closed-by-confirmation rows (D-03) and not-yet-confirmed reason (D-11).
</code_context>

<deferred>
## Deferred Ideas

- Structured "fixed-in <sha>" dismissal reason — not needed if D-01..D-07 work; revisit only if manual fixed-dismissals remain common.
- Wider evidence binding (hunk/semantic) for ordinary findings beyond the D-04 trigger — out of scope; identity rules are Phase 57's concern and only on reproduced failures.
- Broader recovery wording across all cards — Phase 58 (RECV-02).
</deferred>

---

*Phase: 56-verified-fixes-close*
*Context gathered: 2026-10-23*
