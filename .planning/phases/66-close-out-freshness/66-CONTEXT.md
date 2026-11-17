# Phase 66: Close out freshness - Context

**Gathered:** 2026-11-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Close out (Finalize) must never complete on a deferred or dismissed owner decision whose reviewed code changed since the review. On a stale decision it refuses and asks for a fresh review; it never starts paid reviewers itself. Unchanged reviewed code still closes exactly as on 2.15.0. The three bounded legacy wrong-keep shapes in 999.44 each end with an evidence-backed outcome. Requirements: FRESH-01, FRESH-02, FRESH-03. Backlog: 999.40, 999.44.

Not in this phase: decision-identity redesign (999.31), scorer retuning, new reviewer lanes, any automatic paid review, the other v2.16 items (incremental scope, phase binding, helper invocation, packaging).

</domain>

<decisions>
## Implementation Decisions

### Refusal message
- **D-01:** The refusal lists each stale decision on its own line: `file:line`, finding title, decision kind (deferred / dismissed), and the cause ("that line changed" or "code near it changed"; deleted/renamed file says so). Cap at about 10 rows, then "+N more".
- **D-02:** The refusal names the exact next command, mirroring the route the user reviewed with (default, GSD phase, PR, range, `--all`), e.g. "Run /review again (same scope), then Close out." It states that a review starts the (paid) reviewers. Close out itself never starts them.
- **D-03:** Any stale decision refuses the whole Close out: no report is written and state is left untouched, consistent with how Close out already refuses on other failed gates. No partial report that flags stale items.

### What counts as changed
- **D-04:** Staleness is judged against the code as it is on disk now: committed, staged and unsaved working-tree edits all count (consistent with 999.28, which compares working-tree content, not HEAD).
- **D-05:** "Nearby" uses the same window the review already uses to reopen decisions (no new window definition).
- **D-06:** A decided file that was deleted or renamed after the review makes that decision stale (refuse; a rename is reviewed again, not guessed).
- **D-07:** Any byte change counts, including whitespace-only and comment-only edits. No language-aware "trivial edit" rules.

### Legacy wrong-keep shapes (999.44)
- **D-08:** When a shape reproduces as a real wrong keep through the documented collection/persistence flow, prefer the smallest safe refusal (Close out asks for a fresh review). Repair only where the fix is equally small and clearly correct. No matching-logic redesign.
- **D-09:** Decisions on untracked files are judged by comparing the file's current bytes against what was reviewed; if they differ, or no reviewed content was saved to compare against, the decision is stale and Close out refuses.
- **D-10:** A shape that does not reproduce through the real flow is dropped with recorded proof: a committed test or counterexample/control showing the real flow cannot produce it, plus a note in the 999.44 backlog entry. No defensive code is added for unreproduced shapes.
- **D-11:** Deleted-original relocation (identical text left elsewhere after the decided line is deleted) must be distinguished from the owner-accepted D-21 behaviour of adding a new identical copy while the original remains.

### Carried from the milestone (locked, not re-asked)
- Each repair starts with a reproduction that fails on 2.15.0; unchanged-code controls pass on both 2.15.0 and the candidate (GATE-07).
- Fix-verdict freshness, 999.28 unchanged-worktree score parity and real-edit reopening keep passing.
- Replay against 2.15.0 differs only by the intended refusals.
- One branch/PR for this phase: `feat/v2.16-phase-66` (milestone setup and this discussion ride with it).

### Claude's Discretion
- Where in the helper chain the freshness check lives (e.g. `finalize_inputs.py` vs `carry_state.decision_state` / `_closed`), and how the current-content comparison is computed (snapshot store vs `git` blob/tree comparison), provided D-04..D-07 hold.
- Exact refusal wording and exit code, within D-01..D-03 and existing Finalize refusal conventions (`next: stop-refused`).
- Fixture design for the three 999.44 shapes and the exact-line / nearby / unchanged controls for both decision kinds.

</decisions>

<specifics>
## Specific Ideas

- Re-create the 999.40 assessment reproduction as the first committed fixture: temporary git repo with `test_decision_continuity.base_file()` at `src/a.py`, pass-1 state via `pass1(lines, conf=95, kind=...)`, edit line 10 to `line_10 = danger()`, run the real `finalize_inputs.py` CLI with a fresh empty blob file and all three switches false. On 2.15.0 both `defer` and `dismiss` return `action: write` / `next: write-review-md` with zero outstanding counts; after the repair both refuse.
- The refusal should read like a to-do list the owner can act on without reading code.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and acceptance
- `.planning/ROADMAP.md` §"Phase 66: Close out freshness" — goal and success criteria
- `.planning/REQUIREMENTS.md` — FRESH-01..03, GATE-07..08 wording (owner-corrected)
- `.planning/ROADMAP.md` §"999.40" — assessment reproduction and mechanism
- `.planning/ROADMAP.md` §"999.44" — the three bounded legacy shapes and their fresh evidence
- `.planning/ROADMAP.md` §"999.28" and §"999.31" — what must not regress / what is out of scope

### Historical evidence for 999.44 shapes
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/deferred-items.md` — original WR-01 (unbounded relocation)
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/57-REVIEW-GAPS4.md` — REVIEW-GAPS IN-03 (old covering decision wins), D-21 context
- `.planning/milestones/v2.14-phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md` R7 — untracked files lack change ranges

### Code
- `plugins/vibe-check/commands/review.md` — Finalize skips scoring/carry-forward
- `plugins/vibe-check/scripts/finalize_inputs.py` — Close out inputs CLI (counts, gate decision, `next` action, `_refuse`)
- `plugins/vibe-check/scripts/finalize_gate.py` — gate actions/decide
- `plugins/vibe-check/scripts/carry_state.py` — `decision_state`, `_closed` (accepts a current decision before fix checks), `finalize_counts`, `_nearby_since`, `_covering`
- `plugins/vibe-check/scripts/worktree_snap.py` — working-tree snapshot store (999.28)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `test_decision_continuity.py`: `base_file()`, `pass1(...)` and the simulated-relocation helpers used in the 999.40/999.44 probes.
- `gitfixture.py`: temporary git repo fixtures for real-chain tests.
- `worktree_snap.py` / `gitsnap.py`: existing content snapshots of what was reviewed (candidate source for the D-04/D-09 comparison).
- `test_finalize_inputs.py`, `test_finalize_gate.py`, `test_finalize_parity_grid.py`: existing Finalize test harnesses, including the permanent 2.14.1 side-by-side.

### Established Patterns
- `carry_state._closed` returns True when `decision_state(...) == "current"` before any fix check; `decision_state` compares saved decision evidence with saved finding data only, never current code (the 999.40 cause).
- Finalize refuses via a gate action whose `next` is `stop-refused`; a refused attempt writes no report and a retry revalidates freshness (v2.14).
- Every repair ships with a real-chain fixture and a mutation check (decorative-guard lesson: mutation-test every new guard).

### Integration Points
- `finalize_inputs.py` result bundle (`action`, `reason`, `next`, counts) consumed by `commands/review.md` Finalize prose.
- Replay harness (`replay.py`) against 2.15.0: the only allowed differences are the new refusals.

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 66-close-out-freshness*
*Context gathered: 2026-11-16*
