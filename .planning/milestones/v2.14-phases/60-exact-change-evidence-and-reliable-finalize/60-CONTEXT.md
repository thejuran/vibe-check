# Phase 60: Exact change evidence and reliable Finalize - Context

**Gathered:** 2026-10-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Two repairs on the score → carry → card → finalize chain (999.24, 999.25):

1. **Exact change evidence (EVID-01..03).** `changed_line_ranges` (which feed `in_diff` and `snapshot.nearby_at`) must come only from lines actually added or deleted, never from the 3 unchanged context lines git prints around each hunk. Today every route builds them from default-context diffs, so the effective nearby window is ~8 lines, not 5, and the deletion-only rule in `30-collect-score.md` never fires on a real diff. Every review route (default, GSD, range, PR, `--all`) either uses the exact ranges or explicitly reports an unsupported fixture, and nothing else in the pipeline still assumes 3-line context.
2. **Reliable Finalize (FINL-01..02).** `90-finalize.md`'s `$BLOBFILE` comes under the printed-path rule Phase 58 applied to every other temp file, so a fresh-shell walk through every fence reaches counts → gate → report. A missing path or a failed/refused step stops that attempt and writes nothing.

Out of scope: cost reporting, orchestration extraction (Lean orchestration milestone), reviewer/model changes, scoring-weight changes, 999.26, Phase 59's parked residuals (999.23 WR-01/WR-02).
</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked — do not re-litigate)
- Reproduce first on current code: 999.24 (a real `git diff` shows default-context ranges ~8 lines wide and a pure deletion read as an ordinary hunk) and 999.25 (a fresh-shell fence walk sees an empty `$BLOBFILE`). Record each verdict before any fix lands; a non-reproducing path is recorded and dropped, never replaced with invented work.
- Every fix: failing-before/passing-after fixture plus a mutation check that trips it (mutation-test every guard; no decorative locks). `stable_hash` / GOLDEN_DIGEST frozen. Single-writer rule for `decisions` unchanged.
- Nearby window = symmetric 5 lines, one constant shared with the re-check trigger (57 D-14). Deletion-only rule `+T,0` → `[max(T,1), T+1]` stays the documented semantics.
- No-write-on-failure and independent fix verification (`verified_blob == head_blob`, Phase 56) are not weakened.
- Printed-path convention (Phase 58): a temp file prints `NAME=<path>` when created and later fences reuse the literal path, never `"$NAME"`.
- No growth per round: work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow. Live or paid checks need a separately approved, bounded proposal.

### Range construction
- **D-01:** Ranges are built from the actual `+` / `-` line markers of each hunk, not from git's display-context setting. Reason: `gh pr diff` has no context/`-U0` option, so marker-based construction is the only approach that works the same on every route. Whether this lives in a small deterministic helper (preferred: mechanical work out of prose, consistent with the Lean-orchestration direction) or in score.py is Claude's discretion. It must not add an agent.
- **D-02 (IN-04 folded in, owner 2026-10-29):** A replace hunk that removes more lines than it adds (net deletion, e.g. `-10,3 +10,1`) also covers the new-side line just after the hunk, matching the pure-deletion rule's `T+1`. Reason: once ranges are exact, this edge becomes a reachable silent keep at the 5-line boundary. Same range rule, with its own failing-first fixture and mutant.
- **D-03:** Required end-to-end fixtures run a real `git diff` (in a temp repo) through the actual range builder and assert the resulting ranges for ordinary, deletion-only, insertion, net-deletion replace and relocated-finding hunks, including an at-boundary (reopens) and just-outside (keeps) pair (SC1/SC2). Hand-built range dicts don't count as proof for EVID-02.
- **D-04:** Audit for any other 3-line-context assumption (e.g. silenced-marker windows, re-check trigger, incremental `$LAST_REVIEWED_SHA..HEAD` + staged + unstaged diff in `05-state.md`, `--all` reruns). Fix each one or record why it's unaffected (EVID-03).

### Route coverage
- **D-05 (owner 2026-10-29):** The PR route is proven with a checked-in real PR-format patch (captured once) run through the same range builder. The phase report states plainly that the live `gh pr diff` fetch was not exercised. No network in the suite; no live PR check required.
- **D-06:** Default, GSD, range and `--all` routes each get a fixture through the same builder, or an explicit "unsupported fixture" record with the reason (e.g. `--all` has no diff on pass 1; its incremental rerun diff, if any, is covered). Silent omission doesn't count.

### Finalize failure and retry
- **D-07 (owner 2026-10-29):** When `$BLOBFILE`'s path is missing/empty or the counts/gate step fails, Finalize rebuilds the HEAD fingerprints from current code ONCE in the same session (the rebuild is the snapshot-freshness revalidation) and continues only if the rebuild succeeds. A second failure stops with one plain sentence: nothing was written and the owner can run `--finalize` again. No partial REVIEW.md, archive or decision write on any failed attempt.
- **D-08:** A step the owner refused (permission denied) is not auto-retried. It stops the attempt with the same plain no-write message. The automatic rebuild covers only a lost or empty path or a failed step.
- **D-09:** `BLOBFILE=<path>` is printed when created and reused literally by the counts fence, the rows fence and the re-run-counts step (`90-finalize.md` lines ~16, ~85, ~249). A fresh-shell walk test covers every Finalize fence, and a mutant that reverts to `"$BLOBFILE"` must trip it (FINL-01).

### Cycle bound
- **D-10 (owner 2026-10-29, same as Phase 59 D-08):** One cycle = build → one review (code-review + verify-work) → ONE fix pass limited to reproduced findings in the four qualifying classes → confirmation by each fix's before/after fixture, its mutant and the full offline suite. No second review round. Everything else is carried with rationale. A wrong-keep still open at the end closes the phase "with known limit" (backlog entry with its repro), and Phase 61's release record names it.

### Claude's Discretion
- Where the range builder lives (new helper script vs score.py vs carry_state), its input and output shape, and how prose hands it the raw diff, all within the no-new-agent rule.
- How the fresh-shell walk test is structured (e.g. extracting fences from `90-finalize.md` and running each in a separate `bash -s`).
- Exact wording of the plain stop message.
- Where reproduction verdicts are recorded (e.g. `60-REPRO.md`, as in Phase 59).
</decisions>

<specifics>
## Specific Ideas

- Re-verification reproduction from v2.13 (reuse as the seed repro): deleting one line in a 30-line file gives `@@ -6,7 +6,6 @@` under default `git diff` (new-side count 6) but `@@ -9 +8,0 @@` under `-U0`.
- Expected owner-visible effect: decisions 6–8 lines from an unrelated edit stop being re-asked; at-boundary edits still re-ask.
- Run every shell fence in tests as `bash -s <<'BASH' … BASH` (the Bash tool runs zsh here; unquoted lists don't word-split).
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §"Phase 60" and backlog entries 999.24 / 999.25 — goal, success criteria 1–5, approved scope
- `.planning/REQUIREMENTS.md` — EVID-01..03, FINL-01..02
- `.planning/milestones/v2.13-phases/57-decision-continuity-within-closure/deferred-items.md` — 999.24 origin, acceptance (a)/(b)/(c), IN-04 description
- `.planning/phases/59-stale-decisions-and-lost-deferrals/59-CONTEXT.md` — carried decisions, cycle rule (D-08/D-09)
- `.planning/phases/59-stale-decisions-and-lost-deferrals/59-VERIFICATION.md` — parked residuals (do not fold in)

### Range construction (999.24)
- `plugins/vibe-check/phases/review/30-collect-score.md` §step 2, "changed-line ranges" bullet (~line 64) — current hunk-header rule incl. the deletion rule
- `plugins/vibe-check/phases/review/00-scope.md` — route diff commands (default `git diff HEAD` / `--staged`, PR `gh pr diff --patch`, range `git diff <range>`, GSD)
- `plugins/vibe-check/phases/review/05-state.md` §step 3 — incremental diff `$LAST_REVIEWED_SHA..HEAD` + staged + unstaged
- `plugins/vibe-check/phases/review/00-scope-all.md`, `05-state-all.md` — `--all` route
- `plugins/vibe-check/scripts/score.py` — `in_diff`, `_nearby_changed`, `nearby_at` consumers of `changed_line_ranges`

### Finalize path (999.25)
- `plugins/vibe-check/phases/shared/90-finalize.md` — HEAD fingerprints step (~13), counts fence (~16), rows fence (~85), "Temp paths are literals" rule (~95), re-run counts (~249)
- `.planning/milestones/v2.13-phases/58-*/58-REVIEW-GAPS.md` — where 999.25 was found
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 58 printed-path pattern (`ROWSFILE=`, `SUBSETFILE=`, `ANSWERFILE=` in `90-finalize.md` / `50-fix-loop.md`): template for `BLOBFILE=`.
- `carry_state.py finalize-counts --head-blobs` and `batch_card.py rows --head-blobs`: the two consumers of the blob file; they already fail closed for an absent file.
- `test_decision_continuity.py` / `test_verified_fixes.py` real-chain fixtures: pattern for score → carry → card fixtures; existing `changed_line_ranges` fixtures are hand-built and remain valid as unit tests.

### Established Patterns
- Orchestrator prose collects facts; scripts are pure functions (score.py runs no git). A range builder that parses diff text keeps that split: prose runs git, the helper parses.
- Fail-closed: helpers exit non-zero on bad input, and prose branches on the exit code.
- Mutation-locked guards (`_EXPECTED_RED_UNTIL_*` red-fixture ledgers, reverse runs at a recorded RED SHA).

### Integration Points
- Envelope key `changed_line_ranges` into score.py (shape `{file: [[start,end],…]}`) stays unchanged; only how it is built changes.
- `90-finalize.md` fences ↔ `carry_state.py` / `batch_card.py` / `finalize_gate.py`.
</code_context>

<deferred>
## Deferred Ideas

- Phase 59 residuals WR-01 (own-line spot omitted from the card wording) and WR-02 (deferred-by note lost from pass 3): already parked to 999.23 by the owner, not in this phase.
- 57 IN-01/IN-02/IN-03/IN-05 (presentation or unlikely-shape items): stay carried. Only IN-04 is folded in (D-02).
- Broader Finalize extraction into a script: Lean orchestration milestone.
</deferred>

---

*Phase: 60-exact-change-evidence-and-reliable-finalize*
*Context gathered: 2026-10-29*
