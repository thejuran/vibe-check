---
phase: 36-b3-first-measured-quality-numbers
plan: 02
subsystem: testing
tags: [b3, efficacy, ground-truth, deep-review, measurement, codex, pre-registration]

# Dependency graph
requires:
  - phase: 36-01
    provides: "The committed run-kit — 3 should-catch + 3 should-quiet .patch files with .provenance sidecars (base_sha + EXPECTED_TREE_DIFF_SHA256 + EXPECTED_TOUCHED_PATHS), the pre-registered ANSWER-KEY-b3.md, the SEPARATE PREREGISTRATION.md manifest, and the copy-paste RUN-CHECKLIST.md"
provides:
  - "18 SCOREABLE, COMMITTED per-run findings states (state.json + tree.diff + tree.diff.sha256) under docs/design/b3-ground-truth/runs/<id>/run-<n>/ — 6 diffs x N=3, each with len(passes)==1 and head_sha == the diff's base_sha, each tree.diff.sha256 == the kit-build EXPECTED_TREE_DIFF_SHA256"
  - "Owner-attested measurement integrity: patch applied ONCE at base_sha per diff, kept applied across all 3 runs, apply --reverse --check before each review, Phase-5 fixes declined on every run, no re-run, no --finalize, no fix-agent commit into the source repo, codex=auto (shipped default) measured"
  - "Two archived FAILED-RUN RECOVERY dirs on should-quiet-1 (run-2.failed-*) documenting D-06 unscoreable-and-repeat"
affects: [36-03, wave-3-scoring, RESULTS-v2.9, b3-catch-fp-report]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-run boundary commits (one commit per run — codex pass-4 fix 3): 'runs(36-02): <id> run <n> captured', so stopping after any run is safe"
    - "Fail-closed pre-registration: ANSWER_KEY_COMMIT is an ancestor of HEAD; committed answer-key blob digest == PREREGISTRATION.md ANSWER_KEY_SHA256; the manifest is touched only ONCE, strictly preceding the first runs/ commit (immutable)"

key-files:
  created:
    - "docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-{1,2,3}/ (state.json + tree.diff + tree.diff.sha256)"
    - "docs/design/b3-ground-truth/runs/triggarr-autoescape/run-{1,2,3}/"
    - "docs/design/b3-ground-truth/runs/third-organic-should-catch/run-{1,2,3}/"
    - "docs/design/b3-ground-truth/runs/should-quiet-1/run-{1,2,3}/ (+ run-2.failed-1783177664, run-2.failed-1783179419)"
    - "docs/design/b3-ground-truth/runs/should-quiet-2/run-{1,2,3}/"
    - "docs/design/b3-ground-truth/runs/should-quiet-3/run-{1,2,3}/"
  modified:
    - ".planning/STATE.md"
    - ".planning/ROADMAP.md"

key-decisions:
  - "Owner-attested resume signal 'runs archived' accepted after mechanical re-verification of all 18 scoreable runs on disk (the single WAIT task is a user-triggered /deep-review the assistant CANNOT invoke — D-06 completeness is owner-attested, mechanically corroborated)"
  - "should-quiet-1 run-2 was captured, marked unscoreable, and repeated per D-06 (incidents N-01/N-04, uv.lock mid-review rewrites); the two bad attempts are archived as run-2.failed-* and the clean run-2 is the scoreable capture"
  - "Codex outcome recorded honestly from state evidence: codex-adversarial attribution present in 16/18 runs; should-quiet-2 (0 findings all 3 runs) archived nothing to attribute; should-quiet-3 run-1 had Codex in agents_run but contributed no surviving finding"

patterns-established:
  - "Pattern: independent N=3 empty-state sampling of the SAME planted tree — each run's state isolated (len(passes)==1), the patched tree unchanged (tree.diff.sha256 constant across all 3 runs of a diff)"
  - "Pattern: mechanical corroboration of an owner attestation — len(passes)==1 in every state + head_sha==base_sha proves no fix commit moved HEAD, corroborating the declined-Phase-5 / no-rerun / no-finalize attestation"

requirements-completed: [B3-02]

# Metrics
duration: "~38h wall (owner-paced across days, resumable; assistant close-out ~10min)"
completed: 2026-07-05
---

# Phase 36 Plan 02: B3 owner measurement runs archived (18/18 scoreable) Summary

**Owner drove `/deep-review` N=3 across all 6 committed test diffs; every run's isolated fresh state (len(passes)==1, head_sha==base_sha) + full-worktree diff (tree.diff.sha256 == kit-build value) is committed at its run boundary — 18/18 scoreable, verified on disk, ready for Wave 3 scoring.**

## Performance

- **Duration:** ~38h wall (owner-paced 2026-07-03 → 2026-07-05, resumable across days); assistant close-out ~10 min
- **Started:** 2026-07-03T23:39:28-04:00 (first run commit `eca98ec`)
- **Completed:** 2026-07-05T13:47:13-04:00 (last run commit `9a4810d`)
- **Tasks:** 1 (checkpoint:human-action WAIT gate — owner-completed, assistant verified + closed out)
- **Files modified:** 18 run dirs (54 artifacts) committed across Wave 2; this close-out touches 2 planning docs

## Accomplishments

- **18 SCOREABLE runs committed** — 6 diffs × N=3, each `runs/<id>/run-<n>/state.json` a parseable JSON with `len(passes)==1` and `head_sha == the diff's base_sha`.
- **Full-worktree integrity proven per run** — each `tree.diff.sha256` recomputes correctly AND equals the kit-build `EXPECTED_TREE_DIFF_SHA256` from the `.provenance` sidecar; the sha is constant across all 3 runs of a diff (the same planted tree was reviewed each time).
- **Pre-registration ordering holds** — `ANSWER_KEY_COMMIT ef0ab67` is an ancestor of HEAD; the committed answer-key blob digest matches `PREREGISTRATION.md` `ANSWER_KEY_SHA256` exactly; the manifest was touched only once (`cca63e2`), strictly preceding the first runs/ commit (`eca98ec`) — MANIFEST_COMMIT ordering intact.
- **D-06 exercised** — should-quiet-1 run-2 was captured, marked unscoreable, and repeated (two archived `run-2.failed-*` dirs); the clean run-2 is the scoreable capture.
- **`git status --porcelain docs/design/b3-ground-truth/runs/` is empty** — every artifact committed at its run boundary; nothing under `docs/design/b3-ground-truth/` was modified during close-out.

## Per-diff base_sha (the run block detaches here; head_sha == this in every run)

| diff | repo | role | base_sha | EXPECTED_TREE_DIFF_SHA256 (kit-build) | touched path |
|---|---|---|---|---|---|
| triggarr-secret-in-logs | triggarr | should-catch (secret/PII in logs, `exc=exc`) | `f4366a2` | `f0c70a0…` | triggarr/clients/base.py |
| triggarr-autoescape | triggarr | should-catch (XSS surface, autoescape removed) | `e11187e` (PINNED) | `4fdadb7…` | triggarr/web/routes.py |
| third-organic-should-catch | seedsyncarr | should-catch (unclamped >100% progress) | `3db8b48` | `d991803…` | src/angular/…/view-file.service.ts |
| should-quiet-1 | triggarr | should-quiet (SSRF-hardening feature) | `98eb419` | `a8137f5…` | triggarr/web/validation.py |
| should-quiet-2 | seedsyncarr | should-quiet (optional-JSON-body feature) | `84aff27` | `3cb198d…` | src/angular/…/rest.service.ts |
| should-quiet-3 | roonseek | should-quiet (transfer-cancel boundary feature) | `1027691` | `66fe142…` | src/roonseek/transfer.py |

## Per-run verification result (assistant read-only loop, all 18)

Every run: `state.json` parses, `len(passes)==1`, `passes[-1].head_sha == base_sha`, `tree.diff` recomputes to `tree.diff.sha256`, and `tree.diff.sha256 == kit EXPECTED_TREE_DIFF_SHA256`. **All 18 PASSED.**

| diff | run | assert (passes==1 & head==base) | tree.diff.sha256 == kit | #findings | Codex outcome (from state) |
|---|---|---|---|---|---|
| triggarr-secret-in-logs | 1 | PASS | PASS | 2 | codex-adversarial contributed |
| triggarr-secret-in-logs | 2 | PASS | PASS | 2 | codex-adversarial contributed |
| triggarr-secret-in-logs | 3 | PASS | PASS | 2 | codex-adversarial contributed |
| triggarr-autoescape | 1 | PASS | PASS | 5 | codex-adversarial contributed |
| triggarr-autoescape | 2 | PASS | PASS | 4 | codex-adversarial contributed |
| triggarr-autoescape | 3 | PASS | PASS | 4 | codex-adversarial contributed |
| third-organic-should-catch | 1 | PASS | PASS | 5 | codex-adversarial contributed |
| third-organic-should-catch | 2 | PASS | PASS | 5 | codex-adversarial contributed |
| third-organic-should-catch | 3 | PASS | PASS | 7 | codex-adversarial contributed |
| should-quiet-1 | 1 | PASS | PASS | 4 | codex-adversarial contributed |
| should-quiet-1 | 2 | PASS | PASS | 3 | codex-adversarial contributed |
| should-quiet-1 | 3 | PASS | PASS | 5 | codex-adversarial contributed |
| should-quiet-2 | 1 | PASS | PASS | 0 | no findings archived (nothing to attribute) |
| should-quiet-2 | 2 | PASS | PASS | 0 | no findings archived (nothing to attribute) |
| should-quiet-2 | 3 | PASS | PASS | 0 | no findings archived (nothing to attribute) |
| should-quiet-3 | 1 | PASS | PASS | 3 | Codex in agents_run; no surviving codex-attributed finding |
| should-quiet-3 | 2 | PASS | PASS | 1 | codex-adversarial contributed |
| should-quiet-3 | 3 | PASS | PASS | 2 | codex-adversarial contributed |

**Codex outcome, stated honestly:** the plan asked for a per-run "Codex joined/skipped" line, but the literal outcome line was not separately archived into `state.json`. What IS archived is the finding-level attribution and `agents_run`. From that evidence: Codex contributed at least one finding (`agent: codex-adversarial`) in **16 of 18** runs. `should-quiet-2` produced **0 findings on all 3 runs** (the run correctly stayed quiet; with no findings, there is nothing to attribute — this is NOT evidence Codex was skipped). `should-quiet-3 run-1` listed Codex in `agents_run` but had no surviving `codex-adversarial` finding. Wave 3 should treat the archived findings, not this attribution tally, as the scoring input; the Codex-participation picture is recorded here for the report's method notes.

## Unscoreable + repeated runs (D-06)

- **should-quiet-1 run-2** — captured, marked unscoreable, and repeated. Two archived attempts remain as evidence: `runs/should-quiet-1/run-2.failed-1783177664/` and `runs/should-quiet-1/run-2.failed-1783179419/` (each carries `passes:1` at the correct base head `98eb419`). Root cause per the method notes: incidents **N-01 / N-04** — a `uv.lock` mid-review rewrite polluted the full-worktree diff; the remedy was the `chflags`/immutable-flag prevention documented in commit `4eff2aa` ("should-quiet-1 run-2 failed attempts archived + N-04 uv.lock immutable-flag prevention (D-06)"). The clean `run-2` is the scoreable capture; all 3 should-quiet-1 runs pass the assert and sha compare.
- No other unscoreable runs. Every diff has exactly 3 scoreable runs at the resume signal — no holes (Wave 3's aggregation bar is met without a waiver).

## Method-note incidents on record (from the docs(36-02) history)

- **N-01 / N-04** — `uv.lock` mid-review rewrites (2 lost should-quiet-1 run-2 attempts) → `chflags`/immutable-flag prevention applied.
- **N-05 (+ addendum, commits `03e2230`, `dd42088`)** — old-base untracked false-positives in the full-worktree proof; the exclude remedy was applied so the no-untracked assert did not trip on pre-existing base-tree files.

## Phase-5 decline + no-rerun/no-finalize (owner-attested, mechanically corroborated)

- **Owner attestation** (resume signal "runs archived"): every diff has exactly 3 scoreable committed runs; all Phase-5 fixes were declined on every run; no run was re-run or `--finalize`d; the fix agent never committed into the source repo; runs measured the shipped `codex=auto` default (no `--codex` forcing).
- **Mechanical corroboration:** `len(passes)==1` in every one of the 18 states means no run carried a second (post-fix) pass; `head_sha == base_sha` in every state means HEAD never moved off the pinned base — a declined-and-not-committed fix loop is exactly what produces this shape, and a re-run or a fix commit would have broken it. The clean `runs/` porcelain and the constant per-diff `tree.diff.sha256` corroborate that no fix mutated the reviewed tree.

## Task Commits

This plan's single task (checkpoint:human-action WAIT gate) was owner-driven; its artifacts landed as 20 `runs(36-02)` commits during Wave 2 (18 per-run boundary commits + the should-quiet-1 failed-attempts archive + method-note addenda), the earliest being `eca98ec` and the latest `9a4810d`. No new source commits were made in this close-out.

**Plan metadata:** committed with this SUMMARY (docs: complete plan).

## Files Created/Modified

- `docs/design/b3-ground-truth/runs/**` — 18 scoreable run dirs (state.json + tree.diff + tree.diff.sha256) + 2 archived failed-run recovery dirs on should-quiet-1 (all committed in Wave 2; unchanged by this close-out).
- `.planning/phases/36-b3-first-measured-quality-numbers/36-02-SUMMARY.md` — this file.
- `.planning/STATE.md`, `.planning/ROADMAP.md` — position/progress advanced to 36-02 complete (2/3 plans).

## Decisions Made

- Accepted the owner's "runs archived" attestation after independently re-verifying all 18 scoreable runs on disk (parse + isolation assert + tree-sha compare) and the pre-registration/immutability ordering. The WAIT task is a user-triggered `/deep-review` the assistant cannot invoke; D-06 completeness is owner-attested and here mechanically corroborated.
- Recorded the Codex outcome from the archived attribution evidence rather than inventing a per-run "joined/skipped" line that was not separately archived — honest to what the state supports.

## Deviations from Plan

None — plan executed exactly as written. The single task is a WAIT gate; the owner completed it per RUN-CHECKLIST.md and the assistant verified + closed it out. The two archived `run-2.failed-*` dirs are not a deviation — they are the D-06 unscoreable-and-repeat path the plan explicitly provisions (FAILED-RUN RECOVERY block).

## Issues Encountered

- The initial read-only verification script counted `findings` at the top level of `state.json` and reported 0 for every run; the findings actually live at `passes[0].findings`. Corrected the Codex/findings tally (the isolation assert — `passes[-1].head_sha`, `len(passes)==1` — was already reading the correct key, so the 18/18 pass result stands). Root cause was a script-shape assumption, not a data problem.

## Next Phase Readiness

- **Wave 3 (36-03) can score with no holes.** Inputs ready: 18 scoreable committed runs; the pre-registered committed key blob at `ANSWER_KEY_COMMIT ef0ab67` (digest matches PREREGISTRATION.md); every runs/ commit descends from the key and from MANIFEST_COMMIT.
- **Wave 3 guard reminder:** T-36-05 — spot-check the first captured triggarr-secret-in-logs state confirms no runtime secret was captured into a committed file before bulk scoring (the buggy line is `exc=exc`, an object with no literal key).
- **For the report:** the Codex-participation picture (16/18 with a codex-adversarial finding; should-quiet-2 silent on all 3; should-quiet-3 run-1 Codex-present-no-finding) belongs in the method notes, not the catch/FP math.

---
*Phase: 36-b3-first-measured-quality-numbers*
*Completed: 2026-07-05*
