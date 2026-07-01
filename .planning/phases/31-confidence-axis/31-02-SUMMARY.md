---
phase: 31-confidence-axis
plan: 02
subsystem: render-orchestration
tags: [markdown, output-format, review.md, deep-review.md, confidence-render, min_confidence, flag-threading, envelope-key, byte-stable]

# Dependency graph
requires:
  - phase: 31-confidence-axis
    plan: 01
    provides: "score.py min_confidence envelope key + below-min-confidence filtered reason + config.py MIN_CONFIDENCE_FLAG env interface (the three frozen Wave-1 contracts)"
provides:
  - "output-format.md: Conf column rebound from {{score}} (orchestrator_score) to {{agent_confidence}} (D-01, CONF-01) + a visible Confidence line in the detail block + a distinct 'Below min_confidence' filtered-summary row in BOTH tables (D-02, CONF-03)"
  - "review.md Phase 0.6: --min-confidence flag parse (mode-independent) threaded through config.py via MIN_CONFIDENCE_FLAG for validated flag>config>default precedence; $CONFIG_MIN_CONFIDENCE carried-forward var"
  - "review.md Phase 3: min_confidence envelope bullet mirroring thresholds — OMIT on the default/no-flag path (byte-stable), inject the scalar int only when valid"
  - "review.md Phase 4: {{min_confidence_count}} bound to filtered[] reason=='below-min-confidence', distinct from the post-scoring sub-threshold {{low_confidence_count}} row"
  - "deep-review.md: documentation-only inheritance note (min_confidence flag + envelope key + render all inherit via delegation, no deep-review behavior edit)"
affects: [32-idiom-floor-vibe-ignore, 33-codex-legibility]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Flag threading option (a): --min-confidence parsed at Phase 0.6, passed as MIN_CONFIDENCE_FLAG env on the config.py invocation so config.py's tested _apply_flags/_validate_min_confidence owns validation + precedence — NO 0-100 re-check or precedence prose in the orchestrator"
    - "Phase 3 min_confidence envelope key mirrors thresholds VERBATIM: OMIT the key entirely when $CONFIG_MIN_CONFIDENCE is None → score.py filter never runs → GOLDEN_DIGEST byte-stable"
    - "Two-layer filter-summary honesty: below-min-confidence (pre-scoring knob) and sub-threshold (post-scoring band cutoff) counted from DISTINCT reasons into SEPARATE rows so neither conflates the other (RESEARCH Pitfall 4)"

key-files:
  created: []
  modified:
    - "plugins/vibe-check/templates/output-format.md — Conf column binding {{score}}→{{agent_confidence}}; Confidence: {{agent_confidence}} detail line; 'Below min_confidence' row added to BOTH filtered-summary tables"
    - "plugins/vibe-check/commands/review.md — Phase 0.6 flag parse + MIN_CONFIDENCE_FLAG threading + $CONFIG_MIN_CONFIDENCE binding (parse block, both invariant lists, both degrade arms, zero-config back-compat); Phase 3 min_confidence envelope bullet; Phase 4 {{min_confidence_count}} binding note"
    - "plugins/vibe-check/commands/deep-review.md — parallel min_confidence inheritance note next to the existing thresholds no-deep-review-edit note"

key-decisions:
  - "--min-confidence lives at review.md Phase 0.6 (mode-independent, delegated to /deep-review) — NOT the $ALL_MODE-only mode-5 flag block; so all 5 modes + /deep-review inherit it"
  - "Precedence resolved INSIDE config.py (option a), not in orchestrator prose: the flag rides the config invocation via MIN_CONFIDENCE_FLAG, so a bad flag degrades identically to a bad toml value (one warning, no filter)"
  - "Envelope key OMITTED on the None path (mirrors thresholds) — omission, not an explicit default, is what keeps the zero-config/no-flag run byte-identical to v2.7"
  - "Conf HEADER text left as 'Conf' (it always implied confidence; the column now literally shows agent_confidence) — only the binding was rebound"

patterns-established:
  - "A universal (mode-independent) CLI flag belongs in the unconditional Phase 0.6 config-resolution step, threaded through config.py for validated precedence — the reusable template for future --knob flags"
  - "Render + orchestrator surfacing of a non-scored field (agent_confidence, min_confidence, min_confidence_count) never trips the single-writer-lock guard, which only fires on by-hand WRITES to band/orchestrator_score/stable_hash/attribution/status"

requirements-completed: [CONF-01, CONF-03]

# Metrics
duration: ~35min
completed: 2026-07-01
---

# Phase 31 Plan 02: Confidence-render wiring Summary

**Surfaced the confidence axis at the render + orchestrator layer — rebound the `Conf` column to the raw `agent_confidence` (+ a detail-block Confidence line), parsed `--min-confidence N` at review.md's mode-independent Phase 0.6 threaded through config.py for validated `flag > config > default` precedence into the score.py envelope, and added a distinct "Below min_confidence" filtered-summary row — with the zero-config/no-flag path proven byte-identical to v2.7 (envelope key omitted, `min_confidence_count`=0) and the single-writer-lock guard held green.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-07-01
- **Tasks:** 2 (both `type="auto"`)
- **Files modified:** 3

## Accomplishments

- **output-format.md (D-01/D-02, CONF-01/CONF-03):** rebound the sole numeric Conf-column binding `{{score}}` (orchestrator_score) → `{{agent_confidence}}` (the raw 0-100 the agent reported) at the Critical summary table — propagating to Warning/Medium automatically via the "[same table + per-finding format as Critical]" references, so NO separate Warning/Medium edit. Added a visible `Confidence: {{agent_confidence}}` line to the detailed per-finding block. Added `| Below min_confidence | {{min_confidence_count}} |` to BOTH filtered-summary tables (with-issues + no-issues copies), directly below the existing `Below confidence threshold` / `{{low_confidence_count}}` score-threshold row, which was left untouched (still present twice).
- **review.md Phase 0.6:** parse `--min-confidence N` (both `--min-confidence 75` and `--min-confidence=75` forms) from `$ARGUMENTS` mode-independently into `$MIN_CONFIDENCE_FLAG_VAL`; pass it as `MIN_CONFIDENCE_FLAG` on the existing `config.py` invocation so config.py's tested `_apply_flags` / `_validate_min_confidence` resolves `flag > config > default` AND validation — no 0-100 re-check or precedence prose in the orchestrator. Bound `$CONFIG_MIN_CONFIDENCE` ← `values.min_confidence` in the parse-once block; added it to BOTH Phase-0.6-invariant carried-forward lists (step 1's absent-state jump prose + step 5's carry-forward-only jump), BOTH degrade arms ($CONFIG_PY-empty and reader-failure), and the zero-config back-compat statement.
- **review.md Phase 3:** added a `min_confidence` envelope bullet mirroring the `thresholds` bullet EXACTLY — source from the carried-forward `$CONFIG_MIN_CONFIDENCE`, OMIT the key entirely on the None/no-flag path (byte-stable — score.py's filter never runs, GOLDEN_DIGEST unmoved), inject the scalar int only when valid.
- **review.md Phase 4:** added a filtered-summary binding note tying `{{min_confidence_count}}` to `filtered[]` entries whose `reason == "below-min-confidence"` (Plan 31-01's pre-scoring drops), explicitly kept DISTINCT from the post-scoring `sub-threshold` reason behind `{{low_confidence_count}}` (the two-layer trap, RESEARCH Pitfall 4).
- **deep-review.md:** added a documentation-only note parallel to the existing `thresholds` "no deep-review edit" note, stating that the `min_confidence` flag + envelope key + render all inherit via review.md delegation with zero deep-review behavior change.
- **Guards + integration proven:** full suite 224 tests green (unchanged from Wave-1 baseline); the single-writer-lock guard class (`TestSingleWriterLock`, 10 tests) green — the render/prose edits touch no scored-field writer. End-to-end flag threading verified against config.py: no-flag → `min_confidence: null`; `70` → `70`; `999` → `null` + one warning; `abc` → `null` (no warning).

## Where the flag is parsed / envelope-omit / row wording / deep-review inheritance (per plan `<output>`)

- **Flag parse site:** review.md **Phase 0.6 (Resolve config)** — the unconditional, mode-independent config-resolution step (delegated to `/deep-review`), NOT the `$ALL_MODE`-only mode-5 flag block. Parsed via `sed` into `$MIN_CONFIDENCE_FLAG_VAL`, then threaded through `config.py` via the `MIN_CONFIDENCE_FLAG` env var so config.py owns precedence + validation.
- **Envelope-omit-on-default:** review.md Phase 3 OMITS the `min_confidence` key from the score.py envelope ENTIRELY when `$CONFIG_MIN_CONFIDENCE` is None (no flag AND no valid config value). Omission — not an explicit default int — is what keeps the zero-config run byte-identical to v2.7 (the score.py filter never runs; GOLDEN_DIGEST unmoved).
- **Filtered-row wording chosen:** `| Below min_confidence | {{min_confidence_count}} |` (matches output-format.md), placed directly below the existing `| Below confidence threshold | {{low_confidence_count}} |` row in both filtered-summary tables. The existing row keeps its meaning (the post-scoring `sub-threshold` count) and wording untouched.
- **/deep-review inheritance:** confirmed with NO behavior edit. The flag is parsed at review.md's unconditional Phase 0.6 (deep-review runs it by delegation, deep-review.md step 2), the envelope key is sourced at review.md's Phase 3 (delegated at step 7), and the render comes from output-format.md — so all three inherit through delegation. deep-review.md gained ONLY a one-line documentation note; no config-read or envelope logic was added to it.

## Files Created/Modified

- `plugins/vibe-check/templates/output-format.md` — Conf column binding rebind + detail Confidence line + `Below min_confidence` row in both filtered-summary tables.
- `plugins/vibe-check/commands/review.md` — Phase 0.6 flag parse (`$MIN_CONFIDENCE_FLAG_VAL`) + `MIN_CONFIDENCE_FLAG` on the config.py invocation + `$CONFIG_MIN_CONFIDENCE` binding (parse block, both invariant lists, both degrade arms, zero-config back-compat) + a `$CONFIG_PY`-empty-with-flag degrade note; Phase 3 `min_confidence` envelope bullet; Phase 4 `{{min_confidence_count}}` distinct-reason binding note.
- `plugins/vibe-check/commands/deep-review.md` — parallel `min_confidence` inheritance note (documentation-only).

## Task Commits

1. **Task 1: Conf→agent_confidence rebind + detail line + Below min_confidence rows (output-format.md)** — `d0fb7a5` (feat)
2. **Task 2: --min-confidence Phase 0.6 parse + envelope threading + Phase 4 count + deep-review note** — `1ee90c6` (feat)

## Decisions Made

- **Flag home = Phase 0.6, not mode-5.** `--min-confidence` is mode-independent (applies to diff/PR/range/GSD/`--all`) and is delegated to `/deep-review`, so it belongs in the unconditional config-resolution step. The `$ALL_MODE`-only mode-5 flag block (which "adds NOTHING to the four diff handlers") would have made a universal flag silently inert on the common modes.
- **Precedence via config.py (option a), not prose.** Threading `--min-confidence` through config.py's tested `_apply_flags` (via `MIN_CONFIDENCE_FLAG`) reuses the SAME `_validate_min_confidence` 0-100 bound a toml value gets — so a bad flag (`999`) degrades identically (None + one warning through `$CONFIG_WARNINGS`), with no duplicated validation and no precedence prose in the orchestrator.
- **Conf header text kept as `Conf`.** Per the plan/CONTEXT D-01 latitude, the header still means "confidence" and the column now literally shows `agent_confidence` — only the binding was rebound. No cosmetic relabel of the pre-existing `Below confidence threshold` row (behavior-neutral, left as-is to avoid touching its meaning).

## Deviations from Plan

None — plan executed exactly as written. All three render sites and both command wiring points followed the RESEARCH Insertion Recipe (steps 3-5), the Q5/Q6 findings, and CONTEXT D-01/D-02/D-04 verbatim. The `$CONFIG_PY`-empty-with-a-flag case (a partial install where the reader is absent but `--min-confidence` was passed) was covered by an explicit degrade note ($CONFIG_MIN_CONFIDENCE stays None → no filter) — this is a clarifying elaboration of the plan's existing degrade posture, not a behavior change or a new decision.

## Issues Encountered

- `pytest` is not a python3.14 module (`python3 -m pytest` fails) but the `pytest` CLI (`~/.local/bin/pytest`) runs the suite fine — used `pytest -q` (the project gate per `<critical_invariants>`), NOT `python3 -m unittest`.
- The wave-1 SUMMARY was tracked in this worktree but the PLAN/CONTEXT/RESEARCH files were not (`.planning/` is gitignored; only force-added files are present). Read those authoritative planning files from the main repo checkout, and confirmed all edited code files (output-format.md, review.md, deep-review.md, config.py, test_score.py) are tracked and present in the worktree.

## Known Stubs

None — no placeholder/empty-value stubs introduced. `{{agent_confidence}}` and `{{min_confidence_count}}` are template tokens bound to real data (an existing per-finding field and the score.py `filtered[]` count respectively), not hardcoded empties.

## Self-Check: PASSED

All three modified files exist on disk in the worktree; both task commits (d0fb7a5, 1ee90c6) verified present in git log. Task-1 verify passed (`Below min_confidence` ×2, `{{agent_confidence}}` present, old `{{score}}` binding gone, detail Confidence line present, existing score-threshold row untouched ×2). Task-2 verify passed (`CONFIG_MIN_CONFIDENCE` + `MIN_CONFIDENCE_FLAG` in review.md, `min_confidence` in deep-review.md, full suite 224 green incl. the single-writer-lock guard class). End-to-end flag threading through config.py confirmed for the valid / out-of-range / non-int / no-flag cases.

---
*Phase: 31-confidence-axis*
*Completed: 2026-07-01*
