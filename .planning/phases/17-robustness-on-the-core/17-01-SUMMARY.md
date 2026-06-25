---
phase: 17-robustness-on-the-core
plan: 01
subsystem: testing
tags: [score.py, cross-confirm, union-find, category-domain, ROBUST-02, unittest, vibe-check]

# Dependency graph
requires:
  - phase: 16-deterministic-core-script
    provides: "score.py extraction + test_score.py pinning suite (the un-hardened title-substring cross_confirm_group that this plan replaces)"
provides:
  - "ORDER-INDEPENDENT category-domain cross-confirm matcher in score.py (ROBUST-02): pairwise domain confirmation decoupled from greedy first-match grouping"
  - "CATEGORY_DOMAIN map + _categories_overlap predicate (missing/non-str/unknown -> NON-overlap, D-02)"
  - "adversarial single-domain bridge: bridges iff EXACTLY one co-located native domain, else stands alone with no +10 (ambiguity-safe)"
  - "11 new test_score.py pins incl. permutation goldens proving identical cross-confirm outcomes across all input orderings"
  - "three prose files no longer coach the title-substring cross-confirm game (D-03 ripple); tree-wide zero-hit"
affects: [17-02, 17-03, 18-close, ROBUST-02, codex-adversarial, framework-fastapi]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Order-independent grouping via hand-rolled union-find (no itertools/extra imports — frozen import set {json,hashlib,re,sys})"
    - "Decouple the +10/attribution decision from the absorption/dedup grouping so outcome is permutation-invariant"
    - "Ambiguity-safe bridge: drop the bonus rather than guess when a co-located site spans 2+ distinct native domains"

key-files:
  created: []
  modified:
    - plugins/vibe-check/scripts/score.py
    - plugins/vibe-check/scripts/test_score.py
    - plugins/vibe-check/agents/codex-adversarial.md
    - plugins/vibe-check/agents/framework-fastapi.md
    - plugins/vibe-check/commands/deep-review.md

key-decisions:
  - "Title text dropped entirely as a cross-confirm signal (D-01); _titles_match left defined but inert/unreferenced"
  - "adversarial is NOT a wildcard domain — it is resolved by a separate single-domain bridge, never via _categories_overlap"
  - "Ambiguous multi-domain co-location (2+ native domains) drops the +10 rather than guessing which native to confirm (T-17-08)"
  - "Native same-domain absorption components built by union-find (all-pairs) so membership is independent of iteration order"
  - "stable_hash input composition untouched (D-07 frozen golden digest preserved)"

patterns-established:
  - "Hand-rolled union-find for order-independent equivalence classes without new imports"
  - "Separate STEP A (native absorption components) from STEP B (adversarial bridge) inside one function, keeping the {members,attribution} return shape so run() is unchanged"

requirements-completed: [ROBUST-02]

# Metrics
duration: ~20min
completed: 2026-06-25
---

# Phase 17 Plan 01: Order-Independent Category-Domain Cross-Confirm Summary

**Replaced the gameable title-substring +10 matcher in `score.py` with an ORDER-INDEPENDENT category-domain confirmation (union-find native absorption components + an ambiguity-safe adversarial single-domain bridge), and corrected the three prose files that still coached the dead title-substring game.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-25 (worktree base 6b646a9)
- **Completed:** 2026-06-25
- **Tasks:** 2 (Task 1 was TDD: test -> feat)
- **Files modified:** 5

## Accomplishments
- `cross_confirm_group` is now permutation-invariant: the +10/attribution outcome is identical for every input ordering, closing round-2 BLOCKER 2 (greedy first-match order-dependence) and round-1 BLOCKER 2 (over-grouping silently deleting a distinct co-located bug via run()'s keep-highest absorption).
- Cross-confirmation keys on category-DOMAIN overlap (`CATEGORY_DOMAIN` map + `_categories_overlap`), not title text — a crafted title can no longer fire the +10 (T-17-01 mitigated).
- `adversarial` (Codex) bridges into a native group iff EXACTLY ONE distinct native domain is co-located; on an ambiguous 2+-domain site it stands alone with no +10 (T-17-08 mitigated). security<->adversarial confirms in every ordering.
- Missing / null / non-str / unknown categories map to NON-overlap (D-02) and never raise (T-17-02 / Pattern 1 mitigated).
- 11 new test pins incl. two `itertools.permutations` goldens (ambiguous-multi-domain-no-bridge + single-co-located-domain-bridge) and a `_categories_overlap` predicate class; full suite 80 -> 91 tests, all green.
- The three stale cross-confirm hints (codex-adversarial.md, framework-fastapi.md, deep-review.md) now describe category-domain overlap; tree-wide grep for the title-substring claim is zero-hit (D-03 ripple), with unrelated patch-site/render-grouping substring prose untouched.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): failing ROBUST-02 category-domain pins** - `6e996d3` (test)
2. **Task 1 (GREEN): order-independent category-domain cross-confirm** - `eead598` (feat)
3. **Task 2: fix stale title-substring cross-confirm hints (D-03 ripple)** - `34a0d54` (docs)

_TDD task 1 produced a test commit then a feat commit; no refactor commit was needed (the GREEN implementation was already clean)._

## Files Created/Modified
- `plugins/vibe-check/scripts/score.py` - Added `CATEGORY_DOMAIN`, `_category_domain`, `_categories_overlap`, `_line_close`, `_is_adversarial`; re-architected `cross_confirm_group` into STEP A (union-find native same-domain absorption components) + STEP B (ambiguity-safe adversarial single-domain bridge). `_titles_match` left defined but inert. Import set unchanged.
- `plugins/vibe-check/scripts/test_score.py` - Rewrote the title-substring-dependent goldens to key on category; added Tests 1-7 (same-domain confirm, different-domain no-confirm, title-game-dead, security<->adversarial confirm across all permutations, D-02 missing/unknown NON-overlap, BLOCKER-2 permutation pins, category=None through run()); added `TestCategoriesOverlap`; imported `itertools`.
- `plugins/vibe-check/agents/codex-adversarial.md` - Cross-confirm enabler (line ~73) now describes category-domain overlap + single-domain bridge; title row (line ~53) drops the cross-confirm rationale.
- `plugins/vibe-check/agents/framework-fastapi.md` - Data-exposure/auth-security twin confirms via category-domain overlap, not shared title substring (line ~106).
- `plugins/vibe-check/commands/deep-review.md` - "+10 cross-confirm fires on (file, line ±2) + category-domain overlap (per scripts/score.py)" (line ~280).

## Decisions Made
- Followed the plan's locked Option-A domain map and behavior exactly. No discretionary deviations.
- The W2 null-line non-grouping test was updated to use OVERLAPPING category domains (both security) so it now proves line-gating alone prevents grouping even when domains would otherwise overlap — strictly stronger than the prior title-based assertion.
- Survivor identity on a native<->adversarial tie: members are appended natives-first (STEP A) then the bridged adversarial (STEP B); Python's stable sort keeps the native first on a score tie, so the native is the emitted survivor (pinned by the single-co-located-domain permutation test asserting `"A" in result`).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `.planning/` is gitignored in the worktree, but prior-phase SUMMARYs are tracked in git (tracked files override gitignore). This new phase-17 SUMMARY is therefore force-added (`git add -f`) to match the existing tracked-SUMMARY convention so it survives the worktree teardown.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ROBUST-02 is complete and pinned. 17-02 (ROBUST-03 carry-forward windowing) and 17-03 (ROBUST-04 render gate / dispatch warn) are independent of this matcher change and unblocked.
- Verification gate green: `cd plugins/vibe-check/scripts && python3 -m unittest` -> Ran 91 tests, OK (TestImportSet still green; no itertools in score.py; stable_hash golden digest unmoved).

## Self-Check: PASSED

- `17-01-SUMMARY.md` exists and is tracked.
- All commits present: `6e996d3` (test), `eead598` (feat), `34a0d54` (docs prose), `68efa2a` (docs SUMMARY).
- `cd plugins/vibe-check/scripts && python3 -m unittest` -> Ran 91 tests, OK.
- STATE.md / ROADMAP.md untouched by this worktree (orchestrator owns those writes).

---
*Phase: 17-robustness-on-the-core*
*Completed: 2026-06-25*
