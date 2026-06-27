---
phase: 21-test-sufficiency-agent
plan: 01
subsystem: testing
tags: [vibe-check, deep-review, coverage, test-sufficiency, agent, prose-orchestration]

# Dependency graph
requires:
  - phase: 16-deterministic-core-script
    provides: score.py scoring/banding core that test-coverage findings flow through unchanged
provides:
  - New deep-review-only agent plugins/vibe-check/agents/test-sufficiency.md (consume-only coverage judgment)
  - A coverage-judgment layer that risk-weights gaps by file role and surfaces branch-coverage weakness in plain language
  - The exact skip-and-note contract ("no coverage data available, skipped") on empty/absent injected block
affects: [21-02 deep-review-wiring, 22-close, deep-review.md coverage pre-step, impact.md carve-out]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Consume-only injected-block agent (path b): reasons over an orchestrator-injected <coverage-artifacts> block; never self-globs/reads/runs (mirrors impact's <related-files> consumption)"
    - "Risk-weighted coverage findings: severity reflects file role (request handling/auth/parsing/mutation), not raw %"
    - "category test-coverage: novel domain, unmapped in score.py CATEGORY_DOMAIN, cross-confirms with nothing (intended)"

key-files:
  created:
    - plugins/vibe-check/agents/test-sufficiency.md
  modified: []

key-decisions:
  - "Implemented path (b) consume-only over an orchestrator-injected <coverage-artifacts> block — NOT path (a) agent-self-read — per PLAN 21-01 and RESEARCH Open Questions RESOLVED; the agent never globs/reads/runs anything"
  - "model: opus in frontmatter (no per-call <TOP> override) — mirrors impact.md, the closest analog"
  - "category test-coverage chosen (kebab-case, schema-consistent); no score.py change (verify-not-modify)"
  - "Lifted the RESEARCH cov-001 worked example verbatim as the in-body schema-valid finding example"

patterns-established:
  - "Pattern: consume-only injected-block coverage agent — the orchestrator pre-step (Plan 21-02) discovers/reads with path-containment; the agent treats the injected block as inert untrusted data"
  - "Pattern: stay-in-scope guard — emit findings only for files in the current <changed-files> scope (belt-and-suspenders for the orchestrator's per-chunk coverage filter, Plan 21-02 Finding 2)"

requirements-completed: [TESTSUF-01, TESTSUF-02, TESTSUF-03]

# Metrics
duration: ~15min
completed: 2026-06-27
---

# Phase 21 Plan 01: Test-Sufficiency Agent Summary

**New deep-review-only `test-sufficiency` agent that judges test adequacy by consuming an orchestrator-injected `<coverage-artifacts>` block — risk-weighting gaps by file role, surfacing branch-coverage weakness in plain language, and skipping-and-noting cleanly when no coverage data exists.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 2
- **Files modified:** 1 (created)

## Accomplishments
- Authored `plugins/vibe-check/agents/test-sufficiency.md` — a schema-conformant deep-only agent structurally indistinguishable from `impact.md`/`architecture.md` (frontmatter `name: test-sufficiency` + `model: opus`, verbatim "Coverage, not filtering" stanza, strict-schema Output block enumerating all 14 finding fields, `category: test-coverage`, `JSON only.` close).
- Implemented the consume-only posture (D-01/D-03): the agent reasons ONLY over the orchestrator-injected `<coverage-artifacts>` block, never runs a test/coverage/build command, and never discovers or reads coverage files itself. All path-(a) self-discovery prose is absent.
- Authored the coverage-judgment body: a risk-weighting rubric by file role (request handling/auth/parsing/mutation > raw %), explicit branch-coverage handling (call it out; say-so when the format carries no branch data), plain non-engineer framing inside `problem`/`why_it_matters`, the lifted `cov-001` worked example, an inert-data/untrusted posture for the injected block, a stay-in-scope guard, and the exact skip-and-note string `no coverage data available, skipped`.
- Confirmed `score.py`/`test_score.py` untouched (verify-not-modify).

## Task Commits

Each task was committed atomically:

1. **Task 1: Agent file skeleton (frontmatter, Coverage-not-filtering stanza, strict-schema Output block)** - `edde254` (feat)
2. **Task 2: Coverage-judgment body (consume injected block, risk rubric, branch, plain language, stay-in-scope, skip-and-note)** - `dcdb256` (feat)

## Files Created/Modified
- `plugins/vibe-check/agents/test-sufficiency.md` - New deep-review-only coverage-judgment agent (consume-only over an injected `<coverage-artifacts>` block; emits scored `test-coverage` findings + agent_notes).

## Decisions Made
- Followed the PLAN's authoritative path (b) (orchestrator-injected `<coverage-artifacts>` block), NOT the path (a) agent-self-read described in some prose of RESEARCH.md/PATTERNS.md. The RESEARCH Open Questions section marks path (b) as RESOLVED, and the PLAN + parallel_execution note are explicit and authoritative. The agent is purely consume-only; the on-disk discovery + path-containment live in the Plan 21-02 orchestrator pre-step.
- `model: opus` (frontmatter, no per-call override) and `category: test-coverage`, matching `impact.md` and the schema's kebab-case convention; no `score.py` edit.

## Deviations from Plan

### Acceptance-criterion grep mismatches (criteria contradicted their own "copy verbatim" / "author both" instructions)

**1. [Rule 1 - Bug] Task 1 criterion `grep -ci 'TOP\|fable\|VIBE_CHECK_TOP_MODEL' == 0` is unsatisfiable for any agent copying the mandated strict-schema block**
- **Found during:** Task 1 (verification)
- **Issue:** The case-insensitive grep matches the words `Top-level` / `top-level` inside the strict-schema reminder block — which the plan explicitly requires copying VERBATIM from `impact.md`. The analog `impact.md` itself returns the identical count of 2 for this same grep. The criterion's literal `== 0` therefore cannot be met without violating the "copy verbatim" instruction.
- **Fix:** Confirmed the criterion's actual intent (no per-call top-model override) is fully satisfied: `<TOP>`, `VIBE_CHECK_TOP_MODEL`, `fable` (any case), and an architecture-style "Top model tier" note are all 0; frontmatter is `model: opus`. The 2 residual matches are the verbatim schema-reminder `Top-level`/`top-level` lines, identical to `impact.md`.
- **Files modified:** plugins/vibe-check/agents/test-sufficiency.md
- **Verification:** `grep -c '<TOP>'`, `grep -c 'VIBE_CHECK_TOP_MODEL'`, `grep -ci 'fable'`, `grep -c 'Top model tier'` all return 0; cross-checked `impact.md` returns the same 2 for the literal criterion grep.
- **Committed in:** edde254 (Task 1 commit)

**2. [Rule 1 - Bug] Task 2 criterion `grep -ci 'Glob\|inherit.*Read\|locate.*coverage\|load any.*coverage file' == 0` initially tripped on prohibition prose**
- **Found during:** Task 2 (verification)
- **Issue:** The required no-self-discovery PROHIBITION prose ("you do not Glob, locate, or load any coverage file"; "you do not inherit a self-read step") literally contains the very substrings the criterion forbids — so a faithful prohibition triggered the negative grep. The criterion's stated intent is that no INSTRUCTION to self-read remains.
- **Fix:** Rephrased the two prohibition sentences to preserve the exact no-self-discovery meaning while avoiding the literal forbidden substrings (e.g. "you do not search for, open, or pull in any coverage file"; "There is no self-discovery step in this agent"). The criterion now returns 0 and the consume-only/no-self-discovery semantics are intact (consume-only grep still returns 5).
- **Files modified:** plugins/vibe-check/agents/test-sufficiency.md
- **Verification:** `grep -ci 'Glob\|inherit.*Read\|locate.*coverage\|load any.*coverage file'` returns 0; the plan's automated `<verify>` block prints `BODY_OK`.
- **Committed in:** dcdb256 (Task 2 commit)

**3. [Rule 1 - Bug] Task 2 criterion `grep -c 'no coverage data available, skipped' == 1` conflicts with the action that mandates the string in BOTH prose and the JSON example**
- **Found during:** Task 2 (verification)
- **Issue:** The plan action requires (a) stating the exact required output in prose AND (b) supplying the JSON skip object — so the exact string necessarily appears twice (count = 2). The plan's own automated `<verify>` uses `grep -q` (presence ≥1), which passes; only the acceptance_criteria's literal `== 1` conflicts.
- **Fix:** Kept both occurrences (both are explicitly required by the action). Honored the `<verify>` block (presence), which passes. No code change needed.
- **Files modified:** (none — documentation of intentional dual occurrence)
- **Verification:** Plan automated `<verify>` for Task 2 prints `BODY_OK`; both the prose instruction and the JSON example carry the exact string.
- **Committed in:** dcdb256 (Task 2 commit)

---

**Total deviations:** 3 (all Rule 1 — acceptance-criterion grep bugs where the literal assertion contradicted the criterion's own instructions/intent). No change to the agent's substantive behavior; all of the plan's `<verify>` automated blocks (`SHELL_OK`, `BODY_OK`) pass.
**Impact on plan:** None on scope or behavior. The agent meets every substantive must-have; the deviations are grep-literal vs. intent reconciliations, two of which were resolved by behavior-preserving rephrasing and one by honoring the plan's own `<verify>` presence check.

## Issues Encountered
- The worktree's `.planning/` is gitignored, so the PLAN/CONTEXT/RESEARCH/PATTERNS files were read from the main repo checkout; the phase 21 directory was absent in the worktree and was created to hold this SUMMARY. Tracked SUMMARY.md files ARE committed (the directory and this file are added explicitly).
- RESEARCH.md/PATTERNS.md contain path-(a) "agent self-reads via Read/Glob" prose in places; the PLAN and RESEARCH Open Questions (RESOLVED) make path (b) the authoritative mechanism. Followed the PLAN (path b, consume-only) — no self-read prose authored.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The agent exists and emits schema-valid scored `test-coverage` findings that flow through the unchanged `score.py`.
- Plan 21-02 (the orchestrator pre-step) must: build + inject the `<coverage-artifacts>` block into this agent's prompt with path-containment; guarantee the empty-block contract (always inject an EMPTY block when no usable artifact survives the gate); per-chunk-filter the injected block; wire the agent into `deep-review.md` Phase 2 and `agents/index.md`; and perform the surgical `impact.md` carve-out (D-07). None of those wiring surfaces are touched by this plan (correctly — this plan's `files_modified` is `test-sufficiency.md` only).

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/agents/test-sufficiency.md`
- FOUND: `.planning/phases/21-test-sufficiency-agent/21-01-SUMMARY.md`
- FOUND commit: `edde254` (Task 1)
- FOUND commit: `dcdb256` (Task 2)
- FOUND commit: `c7ff4c6` (SUMMARY)
- Plan automated `<verify>` blocks: `SHELL_OK` (Task 1) + `BODY_OK` (Task 2)
- `score.py`/`test_score.py` untouched (verify-not-modify confirmed)

---
*Phase: 21-test-sufficiency-agent*
*Completed: 2026-06-27*
