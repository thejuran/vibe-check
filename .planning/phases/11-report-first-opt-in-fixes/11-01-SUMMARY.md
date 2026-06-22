---
phase: 11-report-first-opt-in-fixes
plan: 01
subsystem: review-orchestrator
tags: [vibe-check, review, all-mode, fix-loop, report-first, opt-in, markdown-spec]

# Dependency graph
requires:
  - phase: 07-walking-skeleton-selection-end-to-end-all
    provides: "$ALL_MODE / mode-5 --all parse and the --full→$FULL binding pattern that $FIX mirrors"
  - phase: 10-reviewed-set-filter-cross-chunk-merge-noise-control
    provides: "$ALL_MODE-guarded additive-branch discipline (diff path byte-stable); Phase 4.5 $ALL_STATE_FILE pass-entry write that FIX-01 relies on"
provides:
  - "A $FIX Phase-0 mode-5 boolean binding (mirrors $FULL), $ALL_MODE-only"
  - "A fifth Phase-5 skip AND-clause: NOT ($ALL_MODE && $FIX==0) — report-first posture for plain --all"
  - "A first-match-in-list-order disambiguation sentence on the shared skip-stop mechanism (the BLOCKER fix making list order load-bearing for D-04/D-05 precedence)"
  - "The D-01 report-only exit one-liner (finding count + --all --fix + --finalize paths, vibe-check: namespace, single-command positional self-identity)"
affects: [12-dogfood-efficacy-run, deep-review-inheritance]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Skip conditions are an ANDed conjunction; adding a skip reason = appending one AND-clause"
    - "Precedence between skip one-liners = list order + a first-match-in-list-order rule (no bespoke precedence prose)"
    - "$ALL_MODE-guarded additive branch keeps the diff path byte-stable"

key-files:
  created: []
  modified:
    - plugins/vibe-check/commands/review.md

key-decisions:
  - "D-01: plain --all prints a report-only line naming both --all --fix and --finalize paths plus a 'nothing changed' note; the --all --fix hint renders the SINGLE running command positionally (vibe-check: namespace)"
  - "D-02: report-first is ONE new AND-clause appended LAST to the existing Phase-5 skip conjunction"
  - "D-03: $FIX is a Phase-0-bound boolean (mirrors $FULL), not a re-scan of $ARGUMENTS in the skip list"
  - "D-04: --all --fix never overrides $TURINGMIND_NONINTERACTIVE — the non-interactive bullet (4th) precedes the report-first bullet (5th), so it wins by list order"
  - "D-05: zero-findings bullet (2nd) precedes report-first (5th), so a plain --all with zero findings prints ONLY the existing '✅ No issues to fix…' line — exactly one message per run"

patterns-established:
  - "First-match-in-list-order skip resolution: when multiple skip conditions are simultaneously satisfied, only the first applicable one-liner (top-to-bottom) prints — converts list ORDER into a precedence property"

requirements-completed: [FIX-01, FIX-02]

# Metrics
duration: ~10min
completed: 2026-06-22
---

# Phase 11 Plan 01: Report-First / Opt-In Fixes Summary

**`--all` is now REPORT-FIRST — a plain `--all` renders the audit, persists state, and stops with a discoverable next-step line (no auto "apply all?" prompt); `--all --fix` is the deliberate opt-in into the existing, unchanged Phase-5 fix loop — implemented as four additive, `$ALL_MODE`-guarded edits to `review.md` with the diff path byte-stable.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-22T22:18Z (approx)
- **Completed:** 2026-06-22T22:28Z
- **Tasks:** 2 (Task 1 = four edits; Task 2 = two read-only confirmations)
- **Files modified:** 1 (`plugins/vibe-check/commands/review.md`)

## Accomplishments

- **EDIT 1 (D-03/FIX-02) — `$FIX` binding (review.md L155):** Added a `$FIX=1 iff '--fix' ∈ $ARGUMENTS else $FIX=0` boolean adjacent to the existing `$FULL` binding, in identical parenthetical shape, carrying the `$ALL_MODE`-only / "adds NOTHING to the four diff handlers (Phase 0 modes 1-4)" clause verbatim. The recognition sentence was left byte-unchanged.
- **EDIT 2 (D-02/FIX-01/FIX-02) — report-first skip AND-clause (review.md L823):** Appended a FIFTH bullet, LAST in the "Phase 5 runs ONLY when ALL of these are true" conjunction (after the `$TURINGMIND_NONINTERACTIVE` bullet): `NOT ($ALL_MODE is set AND $FIX is 0)` — in `--all`, the fix loop runs only when `--all --fix` was passed. References ONLY `$ALL_MODE` and `$FIX` (never `$TURINGMIND_NONINTERACTIVE`, never a finding count). The four existing bullets are byte-unchanged and keep their order.
- **EDIT 3 (D-04/D-05 — THE BLOCKER FIX) — first-match-in-list-order disambiguation (review.md L825):** Appended one sentence to the existing "If any skip condition fires, print the contextual one-liner and stop normally." line: "If MORE THAN ONE skip condition applies to a run, print ONLY the first applicable condition's one-liner in list order (top-to-bottom) and stop — never two messages." This makes list ORDER load-bearing: D-05 (zero-findings, 2nd) and D-04 (non-interactive, 4th) each win over the new report-first bullet (5th) by position alone — no bespoke precedence prose.
- **EDIT 4 (D-01/FIX-01) — report-only exit one-liner (review.md L827):** Specified (via the EXISTING stop mechanism, no new branch) that the EDIT-2 clause's contextual one-liner IS the D-01 report-only line: Critical/Warning finding count + BOTH follow-up paths (`--all --fix` to fix interactively, `--finalize` to write `.turingmind/REVIEW.md`) + a "report-only — nothing was changed" note. The `--all --fix` hint renders the SINGLE running command by positional self-identity (`/vibe-check:review --all --fix` under `/review`, `/vibe-check:deep-review --all --fix` under `/deep-review`) — `vibe-check:` namespace, never the stale `/turingmind-code-review:`, never a `$COMMAND`/`{{command}}` variable, never a static both-commands list.
- **Task 2 — two read-only confirmations recorded** (see "Task 2 Confirmations" below). `deep-review.md` received ZERO edits.

## Task Commits

1. **Task 1: the four additive edits in review.md** — `e372dbe` (feat)
2. **Task 2: two read-only confirmations** — no commit (verification gate, zero edits; evidence recorded in this SUMMARY)

_Note: the `.planning/` tree is gitignored in this repo (`.gitignore` line 9: `.planning/`), so this SUMMARY cannot be committed in the worktree; the orchestrator owns its handling after the wave (consistent with the GSD gitignored-planning convention)._

## Files Created/Modified

- `plugins/vibe-check/commands/review.md` — four additive edits: the `$FIX` Phase-0 mode-5 binding (L155), the fifth Phase-5 skip AND-clause appended LAST (L823), the first-match-in-list-order disambiguation sentence on the shared stop mechanism (L825), and the D-01 report-only exit one-liner (L827). `git diff --stat`: 1 file changed, 5 insertions(+), 2 deletions(-). No hunk below the skip block; the fix-loop Steps A–C, `agents/fix.md`, the four existing skip bullets (content + order), the Phase 4.5 state write (L771-795), and the `allowed-tools` frontmatter line are all byte-unchanged.

## Task 2 Confirmations (evidence trail for Phase 12 non-regression + `/deep-review --all`)

### CONFIRM 1 — FIX-01 "state still written" (anchor L771-795, NOT L398)

The ACTUAL Phase 4.5 state write is present and unconditional in `plugins/vibe-check/commands/review.md`:

- **L793 (verbatim):** "Append to `state.passes`, write to state file. Create parent dirs as needed (`.turingmind/state/`)."
- **L795 (the `--all` pass-entry write, verbatim excerpt):** "…the SAME pass entry that is appended to `state.passes` and written to `$ALL_STATE_FILE` (the `--all` reserved-subdir state defined in Phase 0.5) ALSO carries the capped-run facts…"

This write sits in Phase 4.5, **before** the Phase 5 header (`## Phase 5 — Interactive fix loop` at **L811**), and is NOT gated behind `--fix`/`$FIX` (it is `$ALL_MODE`-conditioned, never `--fix`-conditioned). Therefore a plain `--all` run that stops at the new report-first skip clause has ALREADY persisted state, so a follow-up `--all --fix` or `--finalize` can pick it up — this IS FIX-01's "state still written," with no new write added.

**L398 is NOT the write site** — it is only the Phase-0.5 carry-forward-bypass forward-pointer note ("The run still PROCEEDS to write its state file at `$ALL_STATE_FILE` in Phase 4.5"). The prior plan revision mis-cited L398; corrected here to L771-795 per the adversarial review.

### CONFIRM 2 — FIX-01/FIX-02 deep-review inheritance (zero deep edits)

`plugins/vibe-check/commands/deep-review.md` step 7 (**L41**, verbatim):

> "7. Execute Phase 5 (Interactive fix loop) per `commands/review.md` verbatim — when the loop's "rerun" option fires, it re-enters `/deep-review` (this command), not `/review`. When "close out" fires, it routes to Finalize mode per `commands/review.md`."

This line (a) carries the review.md skip-list edit to `/deep-review --all` for FREE, and (b) is the in-file evidence for the positional command self-identity the D-01 hint leans on. A whole-file grep of `deep-review.md` for `$FIX|report-only|--all --fix` returns **0** matches — confirming there is NO deep-specific Phase-5 `--all`/`--fix` skip or report-only line (adding one would be the duplicate-path anti-pattern the milestone forbids). `git diff` of `deep-review.md` is EMPTY — zero edits this phase.

## Decisions Made

None beyond the locked D-01..D-05 decisions, all implemented as specified. Claude's-discretion items resolved: variable name `$FIX` (matching `$FULL`/`$FIX` symmetry); exact wording of the disambiguation sentence and the D-01 line (content locked, wording chosen to match the file's house style).

## Deviations from Plan

None - plan executed exactly as written. All four edits are additive, in top-to-bottom file order, each `$ALL_MODE`-guarded (EDITs 1/2/4) or precedence-neutral for single-skip runs (EDIT 3). No deviation rules (1-4) were triggered; no auth gates; no checkpoints.

## Issues Encountered

The `.planning/` tree is gitignored and exists only in the main checkout (not the worktree); planning inputs were read from the main repo path. The worktree harness restricts writes to the worktree, and `.planning/` is gitignored, so this SUMMARY is written under the worktree's `.planning/` path but cannot be git-committed there — the orchestrator handles it post-wave per the GSD gitignored-planning convention. The target files (`review.md`, `deep-review.md`) are git-tracked and present in the worktree, so all edits committed normally.

## Scope-Guardrail Verification (the milestone bar)

- Edited ONLY `plugins/vibe-check/commands/review.md`. `deep-review.md` got ZERO edits (Task 2 read-only confirmation).
- Did NOT touch the fix-loop body (Steps A–C, L826+), `agents/fix.md`, the four existing skip bullets (byte-unchanged + in order), the Phase 4.5 state write (L771-795), or the `allowed-tools` frontmatter line.
- The new report-first bullet is the LAST (5th) bullet — its last position yields D-04 (non-interactive 4th wins) and D-05 (zero-findings 2nd wins) by list order via the EDIT-3 first-match rule.
- The new skip clause references ONLY `$ALL_MODE` and `$FIX` — never `$TURINGMIND_NONINTERACTIVE`, never a finding count.
- The D-01 line uses the `vibe-check:` namespace and renders the SINGLE running command positionally; the only `/turingmind-code-review:` occurrence in the file is the pre-existing L893 (shifted from L890 by the insertions), which is OUT OF SCOPE and untouched.
- `git diff --stat` = exactly one file changed (`review.md`), 5 insertions / 2 deletions; `$FIX` appears exactly twice (binding + skip clause); the first-match disambiguation sentence is present; the four existing bullets are byte-unchanged and in order.

## Next Phase Readiness

- FIX-01 and FIX-02 are satisfied; `--all` is report-first with an `--all --fix` opt-in, and `/deep-review --all` inherits the behavior with zero deep edits.
- Phase 12 (dogfood efficacy run + v2.3 tag) is unblocked: the fix posture is now correct. The Task 2 confirmations above give Phase 12's "diff-mode non-regressed + `/deep-review --all` works" check its evidence trail.
- This is a prompt-only markdown-spec change; behavioral validation is by LLM execution (no test suite — `nyquist_validation: false`). The behavioral assertions are documented in the plan's acceptance criteria and hold by construction.

## Self-Check: PASSED

- FOUND: `plugins/vibe-check/commands/review.md`
- FOUND: `.planning/phases/11-report-first-opt-in-fixes/11-01-SUMMARY.md`
- FOUND commit `e372dbe` (Task 1 — feat)
- FOUND commit `e1b71ea` (SUMMARY — docs)
- Scope vs base (257f527..HEAD): exactly two paths changed — `review.md` and this SUMMARY; `deep-review.md` byte-unchanged; working tree clean.

---
*Phase: 11-report-first-opt-in-fixes*
*Completed: 2026-06-22*
