---
phase: 21-test-sufficiency-agent
plan: 02
subsystem: deep-review-orchestration
tags: [vibe-check, deep-review, coverage, test-sufficiency, wiring, prompt-injection, budget-gate, prose-orchestration]

# Dependency graph
requires:
  - phase: 21-test-sufficiency-agent
    plan: 01
    provides: the consume-only test-sufficiency agent that reads an injected <coverage-artifacts> block
  - phase: 16-deterministic-core-script
    provides: score.py in_reviewed_set run-level gate that the per-chunk coverage filter defends against
provides:
  - Phase 1d coverage-artifact discovery pre-step in deep-review.md (STAGE-A repo-level gate + STAGE-B per-chunk assembly) that builds and injects the <coverage-artifacts> block — the orchestrator-injection mechanism (path b) the agent consumes
  - test-sufficiency wired into the /deep-review dispatch roster (deep-review.md Phase 2 table + agents/index.md matrix), deep-only (NOT /review)
  - Phase 0.3 budget gate updated to count test-sufficiency as a second always-on opus agent (deep floor 5->6 / 6->7, cost ~$2-4 -> ~$2-5)
  - impact.md carve-out (coverage bullet removed) so impact and test-sufficiency don't double-report
affects: [22-close, deep-review.md, index.md, impact.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-agent prompt injection OUTSIDE the shared position-stable <diff>/<files> block (mirrors Phase 1c <related-files> into impact, <intent-context> into architecture/compliance) — preserves review.md's byte-identical prompt-cache invariant"
    - "Two-stage coverage assembly: STAGE A repo-level gate (pre-Phase-2, named in the execution-order list) + STAGE B per-chunk filter to $CHUNK_REVIEW_FILES_i (inside Site C, after L658, before L661) — closes the cross-chunk in_reviewed_set leak"
    - "USABLE ARTIFACT GATE: byte cap (40KB) + reject empty/binary/malformed + reviewed-set match + single empty-block fallback (no non-empty unusable variant)"
    - "Consume-only path-contained discovery (symlink-drop mode 120000 + realpath-containment), never runs a coverage command (D-01)"

key-files:
  created: []
  modified:
    - plugins/vibe-check/commands/deep-review.md
    - plugins/vibe-check/agents/index.md
    - plugins/vibe-check/agents/impact.md

key-decisions:
  - "Reordered the top-level execution-order list to be CHRONOLOGICAL (Finding 1): Phase 1c AND Phase 1d now both precede the Phase 2 dispatch entry; renumbered steps 3-9 and updated all stale 'step N' back-references (step 3->5, step 6->7)"
  - "Phase 1d authored as STAGE-A repo-level gate (top-level list entry) + STAGE-B per-chunk assembly (Site C sub-step), pinned to review.md L658/L661 so the per-chunk filter binds to the variable that only exists inside the loop (round-3 HIGH)"
  - "Injected <coverage-artifacts> into test-sufficiency prompt ONLY, OUTSIDE the shared block (Finding 1b) — shared <diff>/<files> stays byte-identical/position-stable"
  - "Budget gate (round-4 HIGH): floor names test-sufficiency = **6** (or **7** w/ compliance); both '6 with compliance' back-refs -> '7'; cost anchors count two always-on opus agents; ~$2-4 -> ~$2-5 in both the Cost note and the step-2 reference"
  - "impact.md carve-out is a pure single-line deletion (0 added / 1 removed) — no hand-off note, no restructuring (D-07)"
  - "output-format.md left UNCHANGED (verify-not-modify): the L90 'Test coverage' token is agent-source-agnostic and is the only coverage mention; the carve-out is what prevents a double-render"
  - "review.md and score.py/test_score.py untouched (D-08 + verify-not-modify)"

requirements-completed: [TESTSUF-01, TESTSUF-04]

# Metrics
duration: ~25min
completed: 2026-06-27
---

# Phase 21 Plan 02: Test-Sufficiency Agent Wiring Summary

**Wires the Plan 21-01 test-sufficiency agent into `/deep-review`: a Phase 1d coverage-artifact discovery pre-step (two-stage repo-level gate + per-chunk assembly) that injects a gated `<coverage-artifacts>` block into the agent's prompt only, the dispatch-roster rows (deep-only), a budget-gate update counting the new always-on opus agent, and a surgical impact.md carve-out so the two agents don't double-report.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 4 (3 with commits; Task 4 was verify-not-modify, no change)
- **Files modified:** 3

## Accomplishments

- **Task 1 — Phase 1d coverage pre-step (deep-review.md).** Added a `### Phase 1d — Coverage artifacts (for test-sufficiency agent)` section (between Phase 1c and Phase 2.5) and wired it into the top-level execution order:
  - **Execution-order chronology (Finding 1):** reordered the "Concretely, your execution order is:" numbered list so Phase 1c and the new Phase 1d both appear BEFORE the Phase 2 agent-dispatch entry; renumbered steps 3-9 and updated every stale `step N` back-reference (the per-chunk-loop reference `step 3`->`step 5`, the Phase-10-inheritance `step 6 above`->`step 7`, `step 3 confirms`->`step 5`). The awk ordering gate (Phase 1d entry line < Phase 2 dispatch entry line) passes for both 1c and 1d.
  - **Two-stage split (round-3 HIGH):** STAGE A = repo-level discovery + parse + USABLE ARTIFACT GATE -> a repo-level usable coverage dataset, runs pre-Phase-2 (the named list entry). STAGE B = per-chunk `<coverage-artifacts>` assembly INSIDE the Site C loop, after `$CHUNK_REVIEW_FILES_i` is derived (review.md L658) and before the chunk's fan-out turn (review.md L661). The prose forbids building the per-chunk block at STAGE A (no `$CHUNK_REVIEW_FILES_i` there) and names diff-mode as a no-op (STAGE A's dataset filtered to the diff reviewed set IS the block).
  - **Consume-only discovery (D-01):** repo-relative globs for lcov / cobertura / istanbul JSON / clover / Go `coverage.out` / Python `.coverage`; reads pre-existing files only, never runs a coverage/test command.
  - **Path containment (T-21-01):** symlink-drop (git mode `120000`) + realpath-containment vs `git rev-parse --show-toplevel`, mirroring review.md L194-211.
  - **USABLE ARTIFACT GATE (Finding 3 / T-21-04):** all four arms — (a) 40KB byte cap, (b) reject empty/binary/malformed, (c) reviewed-set relevance (STAGE-A test in diff-mode, STAGE-B per-chunk test in --all), (d) single empty-block fallback `<coverage-artifacts></coverage-artifacts>`. Forbids a non-empty rejection-annotated block variant; rejection reasons are recorded OUTSIDE the block.
  - **Injection slot (Finding 1b):** the block is injected into the test-sufficiency prompt ONLY, as a per-agent addition OUTSIDE the shared position-stable `<diff>`/`<files>` block — explicitly preserving review.md's byte-identical/position-stable prompt-cache invariant (L619/L645).
  - **--all chunk scoping (Finding 2 / T-21-05):** STAGE B filters STAGE A's dataset to the current chunk's `$CHUNK_REVIEW_FILES_i` so each chunk's agent sees only its own files — closing the cross-chunk `in_reviewed_set` leak (score.py validates against the run-level `$REVIEWED_UNION`, review.md L689).
- **Task 2 — dispatch roster + budget gate (deep-review.md, index.md).**
  - Phase 2 table: `| ✓ | — | \`test-sufficiency\` | opus (frontmatter) |` directly after the impact row.
  - index.md matrix: `| Deep review mode | \`@agents/test-sufficiency.md\` |` adjacent to the architecture row, with the Codex row still last.
  - Phase 0.3 budget gate (round-4 HIGH): deep floor now names `test-sufficiency` and reads `= **6** (or **7** when \`compliance\` fires)`; both narrative "6 with compliance" back-references -> "7 with compliance"; the cost bracket names `impact` AND `test-sufficiency` at opus (two always-on opus agents per chunk); the Cost note and the step-2 reference both nudged `~$2–4` -> `~$2–5`. The `/review` floor of 3 (or 4) and review.md are untouched (D-08).
- **Task 3 — impact.md carve-out (D-07).** Deleted exactly the single `- Test coverage gaps` bullet (0 added / 1 removed); surrounding bullets and frontmatter intact.
- **Task 4 — output-format.md reconciliation (verify-not-modify).** Confirmed the L90 `- Test coverage: {{icon}} {{observation}}` line is the ONLY coverage mention and is agent-source-agnostic; no token names `impact` as the coverage source. The Task 3 carve-out is precisely what prevents a double-render, so NO template change was needed. output-format.md is unchanged.

## Task Commits

1. **Task 1: Phase 1d coverage-artifact discovery pre-step + execution-order chronology** — `24a9ad5` (feat)
2. **Task 2: dispatch roster rows + Phase 0.3 budget-gate update** — `4ff2da5` (feat)
3. **Task 3: impact.md coverage-bullet carve-out** — `93c35a8` (refactor)
4. **Task 4: output-format.md verify-not-modify** — no commit (no file change; conclusion recorded here)

## Files Created/Modified

- `plugins/vibe-check/commands/deep-review.md` — added Phase 1d pre-step (STAGE-A gate + STAGE-B per-chunk assembly), reordered/renumbered the execution-order list, added the Phase 2 test-sufficiency dispatch row, updated the Phase 0.3 budget gate + Cost note.
- `plugins/vibe-check/agents/index.md` — added the "Deep review mode" matrix row for `@agents/test-sufficiency.md` (Codex row still last).
- `plugins/vibe-check/agents/impact.md` — removed the single `- Test coverage gaps` agent_notes bullet (pure 1-line deletion).

## Decisions Made

- **Execution-order list reorder replaces the old "do not reorder" constraint.** The list was non-chronological (Phase 1c was listed AFTER the Phase 2 dispatch step, with only its prose pinning the real run point). To make the Phase 1d pre-step actually ordered before Phase 2 (not merely claimed-before-it), I moved Phase 1c up, inserted Phase 1d after it, renumbered steps 3-9, and updated all literal `step N` back-references in surrounding prose.
- **STAGE-A list entry vs STAGE-B Site-C sub-step coexist.** The chronological list names only the STAGE-A repo-level step before Phase 2; the per-chunk assembly is a sub-step of the Phase 2 Site C loop. This keeps the chronology fix and the per-chunk-filter fix from re-colliding.
- **output-format.md left untouched.** Per the plan's verify-not-modify default — there is no concrete double-render (single agent-source-agnostic token), so no edit was made.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 1 acceptance-criterion grep `found-but-unusable.*note == 0` tripped on the mandated prohibition prose**
- **Found during:** Task 1 (verification)
- **Issue:** The plan's `<action>` REQUIRES prose that explicitly forbids a non-empty "found-but-unusable" / `<note>` block variant, but the acceptance criterion `grep -ci 'found-but-unusable.*note\|<note>.*coverage' == 0` matches that very prohibition (the forbidden substring `found-but-unusable ... note` appears inside the sentence that FORBIDS it). The criterion's stated intent is "no surviving INSTRUCTION to put an unusable note INSIDE the block" — and a prohibition is the opposite of such an instruction. This is the same class of grep-vs-intent contradiction the Wave-1 SUMMARY documented.
- **Fix:** Rephrased the two prohibition sentences to preserve the exact forbidding meaning while avoiding the literal `found-but-unusable`-then-`note` collocation: "Do NOT emit a non-empty rejection-annotated block variant — a non-empty `<coverage-artifacts>` carrying an explanatory annotation about why the data was unusable is content the agent does NOT recognize as a skip trigger …" and "never substitute a non-empty rejection-annotated block for it". The forbidding semantics are intact; the criterion grep now returns 0 and the positive single-path-fallback grep (`never inside\|single.*path\|sole skip\|do NOT emit a non-empty\|never a non-empty`) still returns ≥1.
- **Files modified:** plugins/vibe-check/commands/deep-review.md
- **Verification:** `grep -ci 'found-but-unusable.*note\|<note>.*coverage'` returns 0; the plan's automated `<verify>` for Task 1 prints `PRESTEP_OK`.
- **Committed in:** `24a9ad5` (Task 1 commit)

---

**Total deviations:** 1 (Rule 1 — acceptance-criterion grep-literal vs. intent reconciliation; behavior-preserving rephrase). No change to substantive behavior; all four task `<verify>` blocks pass (`PRESTEP_OK`, `WIRING_AND_GATE_OK`, `CARVE_OK`, `RECONCILE_OK`).
**Impact on plan:** None on scope or behavior. The Phase 1d prose still mandatorily forbids a non-empty unusable block; only the wording moved off the grep-forbidden substring.

## Threat Surface

The only new surface is the Phase 1d discovery pre-step, fully covered by the plan's existing threat register:
- **T-21-01** (path-containment) — symlink-drop + realpath-containment authored into STAGE A.
- **T-21-04** (oversized/malformed/irrelevant artifact DoS/tampering) — the USABLE ARTIFACT GATE (40KB cap, reject empty/binary/malformed, reviewed-set match, single empty-block fallback).
- **T-21-05** (cross-chunk finding survival) — the STAGE-A/STAGE-B split filters the injected block per chunk to `$CHUNK_REVIEW_FILES_i`.

No NEW security-relevant surface beyond the plan's `<threat_model>`. The dispatch-wiring (Task 2), carve-out (Task 3), and template verify (Task 4) add no input-handling, network, DB, auth, or subprocess surface. No threat flags.

## Issues Encountered

- The worktree's `.planning/` is gitignored (root `.gitignore` line 9), so the PLAN/CONTEXT/SUMMARY files were read from the main repo checkout and the phase 21 directory in the worktree held only `21-01-SUMMARY.md`. This SUMMARY is force-added (`git add -f`) like the Wave-1 SUMMARY, which was committed the same way (commits `c7ff4c6` / `820b9cb`).
- At agent start the worktree base was corrected from `05f7af3` to the plan's expected base `2e7de00` (the `<worktree_branch_check>` `git reset --hard`); after the reset the worktree `.planning` was a partial copy (HANDOFF.json + the phase dir), consistent with the gitignored-planning situation.

## Known Stubs

None — these are prose-orchestration edits (Markdown command/agent files); no empty data values flow to any UI rendering.

## Next Phase Readiness

- The test-sufficiency agent (Plan 21-01) is now fully wired: `/deep-review` discovers on-disk coverage in a path-contained, consume-only, usable-artifact-gated Phase 1d pre-step and injects a per-chunk-filtered `<coverage-artifacts>` block into the agent's prompt only; the agent is in the deep dispatch roster (NOT /review); the budget gate counts it; and impact.md no longer double-reports coverage.
- TESTSUF-01 (wiring + injection) and TESTSUF-04 (carve-out) are complete.
- Phase 22 (close / efficacy) verifies skip-and-note (not command-running, per D-03) and exercises the full deep-review path with the new agent.

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/commands/deep-review.md`
- FOUND: `plugins/vibe-check/agents/index.md`
- FOUND: `plugins/vibe-check/agents/impact.md`
- FOUND: `.planning/phases/21-test-sufficiency-agent/21-02-SUMMARY.md`
- FOUND commit: `24a9ad5` (Task 1 — Phase 1d pre-step)
- FOUND commit: `4ff2da5` (Task 2 — roster + budget gate)
- FOUND commit: `93c35a8` (Task 3 — impact.md carve-out)
- All four task `<verify>` blocks pass: `PRESTEP_OK` (T1), `WIRING_AND_GATE_OK` (T2), `CARVE_OK` (T3), `RECONCILE_OK` (T4)
- review.md, score.py/test_score.py, output-format.md untouched (D-08 + verify-not-modify confirmed)

---
*Phase: 21-test-sufficiency-agent*
*Completed: 2026-06-27*
