---
phase: 07-walking-skeleton-selection-end-to-end-all
plan: 02
subsystem: vibe-check command orchestrator (review.md Phase 0/0.5/1/2/4)
tags: [select, whole-codebase, all-mode, files-block, state-namespace, pathspec, symlink-filter, no-regression]
requires:
  - "07-01: templates/skip-rules.md (the shared skip snippet mode 5 references by prose-pointer)"
provides:
  - "review.md Phase-0 mode 5: --all branch-flip + whole-tree git ls-files selection + hardened narrow guard + regular-files-only symlink filter"
  - "review.md Phase-0.5: reserved-subdirectory fresh-snapshot state branch (.turingmind/state/by-mode/all/<scope-hash>.json)"
  - "review.md Phase-1: --all triage-input note"
  - "review.md Phase-2: <diff>→<files> dispatch-block swap under $ALL_MODE (both base + intent templates)"
  - "review.md Phase-4: additive reviewed-partial coverage note (D-09)"
  - "downstream vars $ALL_MODE / $REVIEW_SET / $FILES_BLOCK / $NARROW for Phases 8-11"
affects:
  - "plugins/vibe-check/commands/review.md (Phase 0, 0.5, 1, 2, 4)"
  - "plugins/vibe-check/commands/deep-review.md (inherits Phase 0 mode 5 via delegation; its own Phase-2.5 swap is a separate later touch — out of scope for 07-02)"
tech-stack:
  added: []
  patterns:
    - "branch-flip flag (top-of-Phase-0 guard + appended mode, modes 1-4 byte-untouched — RESEARCH Pattern 1 Option A)"
    - "three-stage validate-then-contain guard lifted from deep-review.md Codex path two-check (case pre-reject → regex allowlist → realpath-containment)"
    - "orchestrator-owned pathspec-magic prefix chosen by scope shape (:(literal) for plain path, :(glob) for glob)"
    - "regular-files-only mode filter via git ls-files -s (keep 100644/100755, drop 120000)"
    - "reserved-subdirectory state namespace (structural disjointness from flat <repo>-<branch>.json key)"
    - "prose-pointer cross-reference to templates/skip-rules.md (no @-import)"
    - "position-stable shared prompt block (build $FILES_BLOCK once, substitute identically — D-08)"
key-files:
  created: []
  modified:
    - "plugins/vibe-check/commands/review.md"
decisions:
  - "Used Pattern 1 Option A (top-of-Phase-0 branch-flip guard + appended mode 5) — modes 1-4 stay byte-untouched, strongest no-regression guarantee"
  - "Split pathspec magic by scope SHAPE — :(literal) only for plain paths, :(glob) for globs — fixes FINDING 4 (forcing :(literal) on a glob silently under-selects) while keeping FINDING 2 magic-reject closed"
  - "All-mode state lives under reserved subdirectory by-mode/all/<scope-hash>.json (not a flat all-<hash>.json prefix) — a subdirectory is structurally disjoint from any flat <repo>-<branch>.json filename, closing the FINDING 5 collision class"
  - "Fresh-snapshot bypass forces pass-1/null-SHA/empty-carry-forward unconditionally even if a prior all-mode state file exists (design-spec §4, FINDING 1, D-09)"
  - "Coverage-note overflow heuristic reuses triage's existing LOC-based size_tier/total_lines signal (the same signal the large-diff Haiku downgrade already uses) — conservative 'may be partial', precise threshold deferred to Phase 8"
metrics:
  duration: ~25 min
  completed: 2026-06-22
  tasks: 2
  files: 1
  commits: 2
---

# Phase 7 Plan 02: `--all` whole-codebase front-end (review.md) Summary

Wired the `--all` whole-codebase review path end-to-end into `commands/review.md`: a Phase-0 branch-flip guard + mode 5 (hardened narrow guard with literal/glob pathspec split + regular-files-only symlink filter + skip-rules pointer), a Phase-0.5 reserved-subdirectory fresh-snapshot state branch, an `--all` triage-input note, a Phase-2 `<diff>`→`<files>` dispatch-block swap, and a Phase-4 additive reviewed-partial coverage note — all gated on `$ALL_MODE` so a plain `/review` is provably unchanged.

## What was built

**Task 1 (commit f3c1f42) — Phase-0 mode 5 + Phase-0.5 state branch + Phase-1 triage note:**
- **Branch-flip guard** inserted directly under `Parse $ARGUMENTS:` — any `$ARGUMENTS` containing `--all` routes to mode 5 and skips modes 1-4 (a bare number after `--all` is a path, never a PR ref) (SELECT-01, D-01/D-02).
- **Mode 5** appended after mode 4 (modes 1-4 byte-untouched):
  - Narrow parse: first non-flag token → `$NARROW` (path or glob); `--full`/`--fix` recognized as composable, not the narrow token; empty `$NARROW` = whole tree.
  - **Hardened three-stage `$NARROW` guard** (modeled on deep-review.md Codex path two-check): (i) `case` pre-reject of `..`/absolute/option-like/leading-`:`/pathspec-magic (`:(`,`:!`,`:^`)/shell-metachar; (ii) regex allowlist `^[A-Za-z0-9._*/-]+$` (includes `*`, excludes every pathspec-magic char); (iii) realpath-containment of the literal prefix under `git rev-parse --show-toplevel`.
  - **Orchestrator-owned pathspec split by scope shape**: `:(literal)$NARROW` for a plain path, `:(glob)$NARROW` for a glob — user input can never carry its own magic, yet `*.md`/`src/**/*.ts` still narrow.
  - **Selection + symlink filter**: `git ls-files -s -z` (staged form prints mode bits), keep `100644`/`100755`, drop `120000` symlinks before any content read.
  - Skip rules via prose-pointer to `templates/skip-rules.md` (no inline list).
  - Downstream vars set: `$REVIEW_SET`, `$ALL_MODE=1`; `$PHASE_ID`/`$PHASE_DIR` left UNSET (skips Phase 1.5).
- **Phase-0.5 reserved-subdirectory fresh-snapshot branch** (additive; the two default state-key lines byte-untouched): all-mode state at `.turingmind/state/by-mode/all/<scope-hash>.json` (`whole-tree` token or `shasum`-of-`$NARROW`), a reserved-path guard (default-mode resolution can't touch `by-mode/all/` and vice-versa), and a forced pass-1 / `$LAST_REVIEWED_SHA = null` / empty-carry-forward bypass of steps 2-5.
- **Phase-1 `--all` triage note**: feed `$REVIEW_SET` as `<changed-files>`, drop `<diff-stat>`; triage.md needs no edit.

**Task 2 (commit d89460b) — Phase-2 `<files>` swap + Phase-4 coverage note:**
- `$ALL_MODE` conditional swaps `<diff>`→`<files>` in BOTH prompt templates (base + architecture/compliance intent variant), `<files>` in the exact `<diff>` position (after intent-context for the variant).
- Documented `<files>` format: per-file `### <path>` header + extension→fence-language hint table; built ONLY from `$REVIEW_SET` (regular-files-only — dropped symlinks contribute nothing, FINDING 3 end-to-end).
- `$FILES_BLOCK` built once, position-stable; the position-stability sentence extended to name `<files>` (D-08); substitution bindings extended in-place to cover `--all`.
- Phase-4 additive coverage note: whole-codebase Summary variant + a visible `> ⚠ Coverage:` reviewed-partial caveat on overflow (heuristic = triage `size_tier`/`total_lines`) + dropped-symlink reporting. Never silent truncation (D-09).

## The three hardened security/correctness properties (all present)

1. **Pathspec-magic rejection + literal/glob split (SELECT-04 / FINDING 2+4):** narrow guard rejects leading `:` and `:(`/`:!`/`:^` via the allowlist `^[A-Za-z0-9._*/-]+$`; orchestrator prepends `:(literal)` for plain paths and `:(glob)` for globs. `--all '*.md'` works; `--all ':(top)*'` / `--all ':!plugins/**'` fail closed. Literal prefix realpath-contained.
2. **Fresh-snapshot state isolation (FINDING 1+5):** all-mode state under the reserved subdirectory `.turingmind/state/by-mode/all/<scope-hash>.json` (structurally disjoint from the flat default key), forced pass-1 / `$LAST_REVIEWED_SHA=null`, reserved-path guard both directions. The two default state-key lines stay byte-untouched.
3. **Symlink containment (FINDING 3):** selection keeps only regular-file git modes (`100644`/`100755`) via `git ls-files -s`, dropping `120000` symlinks before any content read; dropped symlinks reported in the Phase-4 coverage note.

## Deviations from Plan

None — plan executed exactly as written. The only modified (non-additive) lines are the position-stability sentence (plan-mandated D-08 extension) and the two Phase-2 binding lines (extended in-place per Pattern 2, original semantics preserved). All other changes are pure insertions.

## No-regression verification (structural)

- `git diff` over the whole feature (base → HEAD) shows only additions to `review.md` plus the three plan-mandated in-place extends above. Modes 1-4, the two default Phase-0.5 state-key lines, the MANDATORY DISPATCH SHAPE block, and the diff-mode Summary line all remain as unmodified context.
- `git diff plugins/vibe-check/agents/triage.md` — empty (byte-untouched).
- `git diff plugins/vibe-check/templates/output-format.md` — empty (byte-untouched).
- Both `<diff>` blocks (base + intent variant) still present; diff-mode Summary line intact; no flat `all-*.json` / `state/all-` key remains.
- No chunk/budget/estimate/in_reviewed_set/top-k logic added (the two `in_reviewed_set` mentions are explicit "do NOT build it now" scope notes).

## Verification results

Both `<verify>` automated blocks return PASS:
- Task 1: `--all` guard + mode 5, `git ls-files -s`, `:(literal)`, `:(glob)`, `120000`, `by-mode/all`, no flat `all-` key, fresh-snapshot prose, skip-rules pointer, `$ALL_MODE`, `rev-parse --show-toplevel`, triage.md untouched — all satisfied.
- Task 2: `<files>` present, position-stable sentence, reviewed-partial/coverage, output-format.md untouched — all satisfied.

## Out of scope (deferred to later phases / separate plan)

- `deep-review.md` `--all` recognition note + its Phase-2.5 architecture `<diff>`→`<files>` swap (it inherits Phase 0 mode 5 via delegation; its own block swap is a separate touch — not part of 07-02's `files_modified`).
- Risk-ranked chunker (Phase 8), estimate/budget gate (Phase 9), `in_reviewed_set` filter / noise control (Phase 10), `--fix` posture (Phase 11), Codex `--all` fail-closed wiring (Phase 10). Mode 5 sets up ONE review unit and stops.

## Commits

- `f3c1f42` — feat(07-02): add Phase-0 --all mode 5 + reserved-subdir fresh-snapshot state + --all triage input
- `d89460b` — feat(07-02): swap Phase-2 dispatch to <files> under $ALL_MODE + add Phase-4 coverage note
- `45bbffc` — docs(07-02): add 07-02-SUMMARY.md (force-added; .planning gitignored)

## Self-Check: PASSED

- FOUND: `.planning/phases/07-walking-skeleton-selection-end-to-end-all/07-02-SUMMARY.md`
- FOUND commits: `f3c1f42`, `d89460b`, `45bbffc`
- STATE.md / ROADMAP.md NOT modified (orchestrator owns those writes after wave merge)
