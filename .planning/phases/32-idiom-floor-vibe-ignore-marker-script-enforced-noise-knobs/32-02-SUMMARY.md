---
phase: 32-idiom-floor-vibe-ignore-marker-script-enforced-noise-knobs
plan: 02
subsystem: scoring
tags: [vibe-ignore, noise-controls, silenced-marker, synthetic-finding, score.py, vibe-check, NOISE-02, NOISE-03]

# Dependency graph
requires:
  - phase: 32-idiom-floor-vibe-ignore-marker-script-enforced-noise-knobs
    plan: 01
    provides: "the idiom_floor band cap + _as_line usage precedent + the score.py surface this plan extends alongside (disjoint: silenced_nearby + a synthetic-finding path)"
  - phase: 16-deterministic-core-script
    provides: "silenced_nearby + SILENCED_MARKERS + the -50 silenced path + stable_hash + run() envelope pipeline this plan rides"
provides:
  - "score.py per-token reason-aware vibe-ignore scan: _VIBE_IGNORE constant + _vibe_ignore_scan(source_window) returning one occurrence per TOKEN (window index + kind reasoned/bare), iterating every token per line (Finding #2); reasoned occurrences OR-ed into silenced_nearby (rides the existing -50 path); bare do NOT suppress"
  - "score.py synthetic bare-marker low 'suppression' finding: emitted from run() per BARE occurrence, de-duped by (file, marker_line), appended to kept AFTER the sub-threshold loop (A2 exemption -> guaranteed visible), carrying the FULL survivor shape (band 'low' + fixed non-null orchestrator_score + stable_hash + attribution<=1 + status) so review.md Phase 3/4 gates never halt (Finding #1)"
  - "NEW-1 crash guard: the marker-line arithmetic resolves member.get('line') through _as_line FIRST; a null/str/float/bool line yields a line:null synthetic finding (no arithmetic, no TypeError halt)"
  - "the 'suppression' category maps to no domain (never cross-confirms, never idiom-capped); FIXED title/category/canonical (no repo text echoed, T-32-04)"
affects: [phase-32-plan-03-render-split, phase-33-codex-legibility-fix-loop, phase-34-efficacy-close]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reason-aware suppression marker folded into an existing fixed-string marker scan WITHOUT becoming a plain member (a bare occurrence must not suppress) — a per-token structured scan returns occurrence records (index + kind) rather than a single bool"
    - "score.py's FIRST synthetic-finding path: a hand-assembled kept entry carrying the full survivor shape, exempt from the sub-threshold drop by being appended AFTER the threshold loop yet structurally gate-complete (both hold) — the ONE clearly-commented exemption"
    - "Crash-safe line arithmetic: resolve a finding's line through the existing _as_line normalizer BEFORE any arithmetic, emitting line:null on a null/odd line rather than raising a run-halting TypeError"

key-files:
  created: []
  modified:
    - "plugins/vibe-check/scripts/score.py — _VIBE_IGNORE + _vibe_ignore_scan (per-token reason-aware) + silenced_nearby reasoned-OR; _SUPPRESSION_* constants + run() bare-marker collection (NEW-1 _as_line guard, (file,marker_line) de-dup) + synthetic-finding emission after the threshold loop"
    - "plugins/vibe-check/scripts/test_score.py — TestVibeIgnore (14 cases) + TestSuppressionFinding (12 cases); defensive g.get('id') where synthetic findings (no id) now appear in findings[]"

key-decisions:
  - "Bare-marker collection scans `working` (all findings that reached scoring) directly, independent of each member's kept/dropped fate — the marker's presence is a fact about the SOURCE, so a member suppressed/dropped for other reasons still contributes its bare-marker audit"
  - "Synthetic finding carries the FULL survivor shape with a hand-set literal 'low' band + fixed orchestrator_score=0 (never flows through band_for) — the omit-orchestrator_score option is REMOVED (it would halt the whole run at review.md Phase 3/4)"
  - "marker_line = _as_line(member.line) - 2 + occurrence.index when line is a usable int; None -> line:null (Finding NEW-1); de-dup key (file, marker_line) with (file, None) a valid collapsing key"
  - "silenced_nearby's SILENCED_MARKERS scan also gained an isinstance(line, str) guard (Rule 2 correctness, byte-stable: run() windows are pre-filtered to strings by _safe_window) to match _vibe_ignore_scan's non-str skip"

patterns-established:
  - "A structured per-token occurrence list ({index, kind}) lets callers ask 'any reasoned?' and 'the bare occurrences' without re-scanning, and handles same-line multi-token markers (bare-then-reasoned AND reasoned-then-bare) that a first-token-only scan mis-classifies"
  - "The synthetic audit finding is de-duped by resolved (file, marker_line), so one physical marker near many co-located findings collapses to one, while two distinct markers each self-flag"

requirements-completed: [NOISE-02, NOISE-03]

# Metrics
duration: 8min
completed: 2026-07-01
---

# Phase 32 Plan 02: `vibe-ignore` marker + bare-marker synthetic finding Summary

**The `// vibe-ignore` marker — a reasoned `// vibe-ignore: <reason>` within ±2 lines suppresses a finding by riding the existing −50 silenced path (identical to the 5 fixed-string markers), while a BARE `// vibe-ignore` does NOT suppress but instead emits ONE guaranteed-visible synthetic low "suppression" finding per bare occurrence, carrying the full survivor shape so it never halts the run, resolved crash-safely against null/odd lines, and de-duped by (file, marker_line).**

## Performance

- **Duration:** ~8 min
- **Tasks:** 2 (both TDD)
- **Files modified:** 2

## Accomplishments

- **NOISE-02 (Task 1):** Added `_VIBE_IGNORE` + `_vibe_ignore_scan`, a per-TOKEN reason-aware scanner returning one occurrence record per `vibe-ignore` token (window `index` + `kind` of `reasoned`/`bare`), iterating EVERY token on each line (Finding #2), not first-token-only. A reasoned occurrence OR-s into `silenced_nearby` so the nearby finding takes the existing −50 and drops with reason `silenced` — behaviorally identical to the 5 existing markers. Reasoned within ±2 suppresses; at ±3 (absent from the window) does not. Same-line `// vibe-ignore // vibe-ignore: reason` in BOTH orders yields two occurrences at one index and still suppresses (any reasoned).
- **NOISE-03 (Task 2):** Added the synthetic bare-marker `suppression` finding — score.py's FIRST synthesized finding. `run()` collects bare occurrences from every working member's window into a `(file, marker_line)` de-dup set, then appends ONE synthetic low finding per unique key to `kept` AFTER the sub-threshold loop (A2 exemption → guaranteed visible in `findings[]`, never `filtered[]`).
- **Finding #1 (structural gate):** The synthetic finding carries the FULL survivor shape — band literal `"low"`, a fixed non-null `orchestrator_score` (0, inert w.r.t. band math), `stable_hash(file, canonical, title)`, `attribution` length ≤1, `status "new"` — so review.md's Phase 3 fail-closed check and Phase 4 render gate never halt on it.
- **Finding NEW-1 (crash guard):** The marker-line arithmetic resolves `member.get("line")` through the EXISTING `_as_line` helper FIRST; a usable int → `finding_line - 2 + index`, a null/str/float/bool line → `line: null` (no arithmetic, no TypeError halt). A file-level marker is still audited with an honest null line, which passes both gates (neither requires a non-null line).
- **No cross-confirm / no cap:** category `suppression` is deliberately absent from `CATEGORY_DOMAIN` → maps to no domain → never earns +10, never capped by idiom_floor. Title/category/canonical are FIXED strings (T-32-04 Information Disclosure — no repo text echoed, no untrusted text in the hash).
- **Byte-stable:** GOLDEN_DIGEST, TestBandBoundaries, and the AST import-set are all unchanged — the no-marker path produces zero suppression entries and identical output. Full suite **283 passed** (was 257 after Plan 01; +26 new).

## Task Commits

Each task was committed atomically (TDD: failing test + implementation folded per task):

1. **Task 1: per-token reason-aware vibe-ignore scan (NOISE-02)** — `adeba73` (feat)
2. **Task 2: synthetic bare-marker low suppression finding (NOISE-03)** — `3914385` (feat)

## Files Created/Modified

- `plugins/vibe-check/scripts/score.py` — `_VIBE_IGNORE` constant; `_vibe_ignore_scan` (per-token, `_VIBE_IGNORE_REASON_RE`); `silenced_nearby` reasoned-OR + non-str guard; `_SUPPRESSION_CATEGORY`/`_TITLE`/`_CANONICAL`/`_SCORE` constants; run() bare-marker collection (NEW-1 `_as_line` guard, `(file, marker_line)` de-dup) + synthetic-finding emission after the threshold loop.
- `plugins/vibe-check/scripts/test_score.py` — `TestVibeIgnore` (14 cases) + `TestSuppressionFinding` (12 cases); four `g["id"]` → `g.get("id")` reads where synthetic findings (which carry no `id`) now appear in `findings[]`.

## Decisions Made

- **Collect from `working`, not from the drop/keep loop:** a bare marker's presence is a fact about the source_window, independent of whether the host finding survives — so the scan iterates `working` directly (all findings that reached scoring after the min_confidence filter), keeping the audit orthogonal to the survivor pipeline.
- **`silenced_nearby` non-str guard (Rule 2, byte-stable):** added `if isinstance(line, str)` to the SILENCED_MARKERS scan to match `_vibe_ignore_scan`'s non-str skip. This is byte-stable because run() windows are already pre-filtered to strings by `_safe_window`, and every direct `silenced_nearby` test passes string lines — GOLDEN_DIGEST + TestSilencedNearby unchanged.

## Deviations from Plan

None — plan executed exactly as written. The plan's `<automated>` verify blocks use `python3 -m unittest`, which the executor instructions flag as non-working on this machine; used the sanctioned `pytest -q` equivalent (from `plugins/vibe-check/scripts`) for every verification, as directed. The four `g["id"]` → `g.get("id")` test-read adjustments are the direct, expected consequence of Task 2 introducing id-less synthetic findings into `findings[]` (covered by the plan's own multi-finding assertions), not a scope deviation.

## Issues Encountered

- Two iterative TDD fixes during authoring (test-only, no implementation change): (1) the reasoned-drop end-to-end test initially used conf 100 + in_diff, which nets 70 and survives — corrected to conf 40 / severity medium / out-of-diff line so the −50 pushes pre-clamp negative and the finding genuinely drops (mirrors the frozen TestDropRule arithmetic); (2) list comprehensions reading `g["id"]` over `result["findings"]` broke once synthetic findings (no `id`) were present — switched to `g.get("id")`.

## Verification Evidence

- Full suite: `pytest -q` → **283 passed, 202 subtests passed**.
- Plan anchors: `pytest -q test_score.py::TestVibeIgnore test_score.py::TestSuppressionFinding test_score.py::TestSilencedNearby test_score.py::TestStableHashGolden test_score.py::TestBandBoundaries test_score.py::TestCategoriesOverlap test_score.py::TestNullLineDefensive test_score.py::TestMalformedInputMatrix test_score.py::TestImportSet` → all pass.
- Byte-stability: GOLDEN_DIGEST + TestBandBoundaries unchanged (no-marker path identical).
- Import ban: TestImportSet passes — score.py stays stdlib-only `{json, hashlib, re, sys}`, no new imports (`re` was already imported).
- No stray harness tags; both modules `ast.parse` clean; no source-file deletions in either commit.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- NOISE-02 and NOISE-03 satisfied and locked by tests. The `vibe-ignore` marker is live: reasoned suppresses, bare self-flags as a guaranteed-visible low audit finding.
- Plan 03 (render split) owns the ACTUAL visible "Suppression (audit)" render section in output-format.md / review.md Phase 4, disambiguating the synthetic `category=="suppression"` finding from a low-capped `category=="idiom"` finding BY CATEGORY. This plan delivered exactly the DATA SHAPE (full survivor shape + line:null tolerance) that lets that render happen without a halt.
- review.md prose still needs `vibe-ignore` added to the silenced-marker list (:685) so the orchestrator includes it when resolving the ±2 source_window — flagged in 32-CONTEXT.md as a Plan 03 / prose-wiring item (score.py only sees markers the orchestrator puts in the window). This is orchestrator-prose, out of this script-only plan's scope.

## Self-Check: PASSED

- `32-02-SUMMARY.md` present.
- Both task commits exist in history: `adeba73` (Task 1), `3914385` (Task 2).
- Both modified source files present; key artifacts verified: `score._vibe_ignore_scan`, `score._VIBE_IGNORE`, `score._SUPPRESSION_TITLE`, `test_score.TestVibeIgnore`, `test_score.TestSuppressionFinding`.
- Full suite green under `pytest -q`: 283 passed, 202 subtests passed.

---
*Phase: 32-idiom-floor-vibe-ignore-marker-script-enforced-noise-knobs*
*Completed: 2026-07-01*
