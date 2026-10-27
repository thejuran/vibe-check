# Phase 57: Decision continuity within closure - Context

**Gathered:** 2026-10-25
**Status:** Ready for planning

<domain>
## Phase Boundary

An owner's defer/dismiss decision stays bound to its evidence: it survives regrouping and edits unrelated to the finding, and the finding reopens only when its relevant evidence changes (DECN-01..03). Reproduce-first: no identity/decision-binding rule changes unless a lost or wrongly-kept decision reproduces on current code as a failing fixture; a path that does not reproduce is recorded as "did not reproduce; dropped". Broader duplicate presentation, cross-repo gate consumers, and recovery wording (Phase 58) are excluded.

</domain>

<decisions>
## Implementation Decisions

### Current behavior (scouted 2026-10-25 — the baseline these decisions change)
- Decisions live in the root `decisions` family keyed by `stable_hash` (file + canonical line content + title), written only by `carry_state.py record-decisions`. Kinds: `dismiss`, `defer` (`carry_state.py:111`).
- Evidence binding (`carry_state.decision_state`, `carry_state.py:457`): an ordinary finding's decision stays current only while `file`, `line`, `canonical_line_content`, `band` all equal the decision-time evidence. So a **pure line shift** (code added above) and **any band move (up or down)** make it stale → re-asked. An edit to the flagged line re-hashes it (new hash, no decision); the finalize helper links an edited finding to the earlier decision when exactly one row matches (`90-finalize.md:106`).
- Needs-verification decisions use `_NV_EVIDENCE_KEYS` = file, canonical_line_content, band, `current_code` fingerprint (no line): a line shift keeps the decision, a body change re-asks (`carry_state.py:393`).
- Rows: a decision on a LEAD row closes nothing for its `members[].obligation` records — each member is its own finding deduped by its own `stable_hash` (`90-finalize.md:25`, `carry_state.py:25-29`).
- Reopen card already shows the earlier decision and reason: "code changed since your decision on pass N (was: dismissed — reason)" / "severity changed (A → B) since your decision on pass N" (`90-finalize.md:101-104`).
- Phase 56 added the D-04 "nearby change" window (5 lines beneath the pinned line) and file/associated-test touch triggers in `score.py` for re-checks.

### What reopens a decision (target behavior; change only where a failure reproduces)
- **D-01:** A pure line shift (code added/removed above; the flagged line itself unchanged) does NOT reopen a decided finding — the decision follows the code. (Today it re-asks → reproduce as a lost decision.)
- **D-02:** A change to code immediately around the flagged line (same nearby window as Phase 56's D-04 trigger) DOES reopen it — relevant evidence changed (DECN-03).
- **D-03:** An edit elsewhere in the same file, outside that nearby window (e.g. a different function), does NOT reopen it (DECN-02).
- **D-04:** Needs-verification decisions keep today's rule: any change to the recorded code body re-asks; a line shift does not.

### Severity changes
- **D-05:** A band RISE on unchanged code (e.g. corroboration by another reviewer) reopens the decision — stronger evidence counts as new evidence; the card says it rose and why.
  - **D-05 refinement (owner, 2026-10-25, after research):** only a rise backed by NEW CORROBORATION (another reviewer now also reports the finding) reopens; the card names that reviewer. A rise caused only by the persisted-scoring bonus / single-reviewer-cap lift (no new reviewer) keeps the decision. Option "any rise re-asks" was rejected.
- **D-06:** A band DROP on unchanged code does NOT reopen it — weaker evidence never needs the owner again. (Today any band move re-asks → reproduce.)
- **D-07:** Defer and dismiss follow the same severity rule.

### Regrouping rows
- **D-08:** When a decided finding is merged into a row with other findings, the decision still covers that finding (it shows as already decided); the owner is asked only about findings the decision did not cover. A decision never silently covers a different reviewer's new concern at the same spot.
  - **D-08 refinement (owner, 2026-10-26, after plan-check):** when a newcomer concern from an uncovered reviewer lane joins a decided row, the WHOLE row reopens once with the D-10 note (earlier decision + reason shown) — not a separate ask for the newcomer alone. Accepted because the card cannot give the newcomer its own line today; "ask only about the new one" was the original pick and is superseded.
- **D-09:** When a decided row is split into separate rows, every finding the decision covered stays decided; only genuinely new findings are asked.
- **D-10:** A row mixing a decided finding with new ones shows a short note, e.g. "1 finding here already dismissed (your reason: …)".

### Defer vs dismiss on reopen
- **D-11:** A deferred finding does NOT resurface on its own (no timer/expiry) — defer and dismiss both stay put until relevant evidence changes.
- **D-12:** When a decided finding reopens because evidence changed, the card shows the earlier decision, its reason, and what changed (line-near-edit / severity rise / code body) — extend the existing stale suffix rather than presenting it as brand new.
- **D-13:** A deferred finding that later gets fixed closes normally through the Phase 56 path ("Closed — fix confirmed …"); the deferral does not block closure.

### Gap-closure rulings (owner, 2026-10-26, after verification gaps_found)
- **D-14 (SA-01):** The nearby window is SYMMETRIC: an edit within 5 lines ABOVE or BELOW the flagged line reopens a decided finding (D-02). Motivating case: a "guarded upstream" dismissal must be re-asked when the guard just above the line is deleted. The window stays ONE constant shared with Phase 56's re-check trigger (the trigger widens too). Supersedes the discretion bullet below on window shape.
- **D-15 (card count):** The D-10 note counts decided CONCERNS, not reviewer reports — two reviewers reporting the same already-dismissed concern read "1 finding here already dismissed".
- **D-16 (from verification gaps, restating D-08/D-05 intent):** A row decision covers only findings the owner was actually deciding: a member that carries its own separately-owed obligation is never covered by the row decision (CR-01). An inherited (covered-member) decision obeys the same reopen rules as an own decision — nearby edit, lane-backed severity rise, joined newcomer (CR-02). "New reviewer" means a lane newly reporting THIS concern, not any lane newly present on the row (WR-03).

- **D-17 (owner, 2026-10-26, after re-verification):** When a covered or absorbed finding splits into its own row on the pass whose edit caused the split (typically the neighbouring lead's fix), that edit counts as a nearby change under D-14 if it is within the window: the finding reopens once with "code next to it changed". No exemption for the neighbour's own fix. A newly split row must therefore get the nearby stamp on its split pass even though it has no prior snapshot of its own.

- **D-18 (orchestrator scope call, 2026-10-27, under the owner's standing rule that silent finding loss justifies new work):** The non-split shape of 57-REVIEW-GAPS2 CR-01/SA-01 (a same-lane fresh re-report out-ranks the carried record of a decided row that never splits, dropping its nearby evidence) is folded into the third gap closure rather than deferred. Same root cause, same code change; fixed at the root: a row's carried status and prior evidence come from any carried same-hash record in it, not only the lead. Not a product ruling; reversible by the owner.

- **D-19 (owner, 2026-10-27, after round-3 review):** One FINAL structural gap round. Fix the mechanism, not the shape: collect every carried record of a finding's identity (stable_hash) BEFORE any filtering (min_confidence, sub-threshold, dedup), pool their evidence (reopen if ANY carried copy's line saw a nearby change; keep the latest owed stamp), and make row lead order deterministic (tie-break by line, never arrival order). HARD STOP: if the review after this round still finds a wrong-keep, close Phase 57 with it documented as a known limit (backlog) rather than opening another round.
- **D-20 (owner, 2026-10-27):** A DEFERRED finding stays on the owner's open list even when it (or its split-out row) scores below the reporting threshold — a deferral can never disappear without the owner closing it. A DISMISSED finding below threshold may drop (intended).
- **D-21 (owner, 2026-10-27, round-4 review SA-01):** A new occurrence of an already-decided finding (same file, line text and title, at another line) is NOT new evidence. An edit beside the new copy does not re-ask the existing decision; only edits beside the decided copy do. Effect: round-4 CR-03 is not a wrong-keep. The shipped pass-3 re-ask (locked by test_p4_far_twin_latest_stamp_reaches_the_first_copy) is an over-ask, to be aligned under backlog 999.23 (not changed in Phase 57, per the D-19 hard stop).
- **D-22 (owner, 2026-10-27):** D-19 hard stop applied after the round-4 review (57-REVIEW-GAPS4.md) reproduced wrong-keeps (CR-01, CR-02, CR-04). Phase 57 closes with them documented as a known limit in backlog 999.23. The two deferral-loss edges also park in 999.23 rather than being fixed in Phase 57: min_confidence removing a deferred covered member (reproduced), and `--all` scope dropping one (SA-02, not reproduced).

### Carried forward (locked from earlier phases)
- Reproduce first; non-reproducing paths are recorded and dropped, never replaced with invented work (owner rule, v2.13).
- Never re-ask without new evidence (v2.11 rule; Phase 56 D-09).
- Single-writer rule: only `carry_state.py record-decisions` writes `decisions`; old records are never rewritten (superseded ones go to `history`). Legacy decisions without `evidence` keep closing as before.
- Mutation-test every new guard; existing suite and replay gate stay green; GOLDEN_DIGEST / `stable_hash` frozen (changing the hash would orphan every persisted dismissal).

### Claude's Discretion
- How a decision "follows" a shifted line (relocation by canonical content, a line-free evidence key set for ordinary findings, or similar) — as long as `stable_hash` stays frozen and legacy records still read correctly.
- How "band rise vs drop" is detected and stored (ordering of bands, evidence comparison) and the exact card wording for D-05/D-10/D-12.
- How member-level decision coverage is tracked across merges/splits (per-member decision records vs lead coverage list), within the single-writer rule.
- Whether D-02's window is literally Phase 56's 5-line-beneath window or a symmetric window, as long as it is shared with the re-check trigger and documented.

</decisions>

<specifics>
## Specific Ideas

- Card example for D-12: "You dismissed this on pass 4 ('false positive, guarded upstream'). Reopened: code next to it changed."
- Row note example for D-10: "1 finding here already dismissed (your reason: …)".
- Real data may exist: the iPlayarr state used in Phase 56 (`/Users/julianamacbook/iplayarr/.turingmind/state/`) and the six-row fixture `plugins/vibe-check/scripts/fixtures/iplayarr45-six-row-state.json` — check for real lost-decision cases before synthesizing; any committed real data is trimmed to paths/titles/minimal fields (owner ruling 2026-10-25).

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` §"Phase 57: Decision continuity within closure" — goal, success criteria 1-4, source context
- `.planning/REQUIREMENTS.md` — DECN-01, DECN-02, DECN-03

### Decision binding contract (current behavior)
- `plugins/vibe-check/scripts/carry_state.py` — module docstring "WHAT CLOSES", `DECISIONS`, `_NV_EVIDENCE_KEYS`, `decision_state`, `stale_cause`, `record-decisions` (single writer)
- `plugins/vibe-check/phases/shared/90-finalize.md` — Open/Closed definitions, stale-suffix card wording (lines ~25-29, 101-106)
- `plugins/vibe-check/scripts/score.py` — `stable_hash` (frozen; GOLDEN_DIGEST), row/member expansion (`_expand_members`), carry-forward relocation

### Prior phase (closure behavior this phase is tested against)
- `.planning/phases/56-verified-fixes-close/56-CONTEXT.md` — D-04 nearby-change trigger, D-09 never re-ask without new evidence
- `.planning/phases/56-verified-fixes-close/56-VERIFICATION.md` and `56-REVIEW-FIX.md` — final Phase 56 closure behavior (recheck_settled, SA-01 NV rule)
- `.planning/milestones/v2.12-phases/` — earlier evidence-binding history (v2.11/v2.12 decisions D-13 stale cause)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `carry_state.decision_state` / `stale_cause`: the single comparison point for decision currency — extend here rather than adding a second comparator.
- Phase 56 `score.py` helpers for the nearby-change window and associated tests (`_independent_trigger`, `_is_associated_test`, `_dir_affine`) — reuse for D-02 so re-check and reopen share one definition of "relevant change".
- Test patterns: `test_verified_fixes.py` (RED-first fixtures, mutant tests), `test_carry_state.py` (finalize-counts end-to-end), `_p45_*` replay helpers in `test_score.py`.

### Established Patterns
- Evidence-bound decisions with fail-closed handling of malformed evidence; legacy records never rewritten.
- Prose contracts locked by `*_holds(text)` tests with one mutant per phrase.
- `score.py` may not import `os`/`pathlib` (AST test).

### Integration Points
- `carry_state.py finalize-counts` / `pending` (what counts as open/decided), the finalize card (`90-finalize.md`, `batch_card.py`), and score.py's row grouping (members/lead).

</code_context>

<deferred>
## Deferred Ideas

- Timed reminders / expiry for deferred findings (resurface after N runs or at milestone close-out) — owner declined for this phase; would be a new capability.
- Broader duplicate presentation and cross-repo gate consumers — excluded by ROADMAP.
- Recovery wording across all cards — Phase 58 (RECV-02).

</deferred>

---

*Phase: 57-decision-continuity-within-closure*
*Context gathered: 2026-10-25*
