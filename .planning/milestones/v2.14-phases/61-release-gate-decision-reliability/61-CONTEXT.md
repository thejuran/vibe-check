# Phase 61: Release gate — decision reliability - Context

**Gathered:** 2026-10-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the 2.14.0 release candidate against the v2.14 accepted scope (Phases 59 and 60) with nothing unrelated changed, state its limits plainly, and ship it through the existing milestone close workflow (GATE-01..03). This phase adds no feature. It fixes nothing unless a gate check reproduces a failure in one of the four qualifying classes. It does not wait for Lean orchestration.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked — do not re-litigate)
- No growth per round (owner, 2026-10-28). Work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow, and the reproduction is cited. Everything else is carried with its rationale.
- Paid or live runs need a separately bounded proposal that the owner explicitly approves. Estimates are not spending caps.
- Archived replay may differ only in named, expected reopen/retention repairs. Phases 59 and 60 both closed with replay unchanged (`test_replay` 64 passed, GOLDEN unmoved), so the expected-difference list is probably empty. Any difference blocks release unless it is named and traced to a 59/60 repair. `replay.hunk_ranges` stays context-inclusive and unchanged (60 R11).
- `stable_hash` / GOLDEN_DIGEST frozen; single-writer rule for `decisions`; no-write-on-failure and independent fix verification are not weakened.
- Install resync before any manual or live check (60 R5): the cache currently runs **2.13.0**. Confirm the installed vibe-check equals the repo `plugin.json` version, and relaunch after a resync.
- A completed milestone always publishes: ff/merge main, push main and tag, then `gh release create`. Marketplace pins `ref: main`.
- One branch/PR per phase: `feat/v2.14-phase-61` (cut from main d587c72 after PR #6 merged).

### Live validation
- **D-01:** The gate includes one small live smoke run under a bounded proposal that the owner approves before anything is spent. Shape: about 3 sessions, est. $20–30 (unit cost from 54-BUDGET.md: ~$6–9 per review session). Resync the install. On a throwaway repo, run review → decide a finding → edit near it → re-review shows the correct reopen reason on the card → `--finalize` writes REVIEW.md. Purpose: prove that the model follows the Phase 60 printed-path Finalize prose from fresh shells, which offline tests cannot show.
- **D-02:** The live smoke covers the **default route + Finalize only**. GSD, range, PR, incremental pass 2+ and `--all` rest on offline proof (plus D-03 for the PR fetch). The release record and notes say so.
- **D-03:** A free scripted check (network, no model) fetches a real PR's diff live with `gh pr diff` (e.g. PR #6) and runs it through the real range builder (`diff_ranges.py`), cross-checked against the local commits. R6 changes from "not exercised" to "checked once". The behaviour on renames, binary files and very large PRs stays a stated limit unless that PR happens to cover it.
- **D-04:** The assistant drives the live sessions via tmux, as in earlier measurement runs. Park the clone's auto-memory before any measurement session (`~/.claude/projects/-Users-julianamacbook-<clone>/memory`). Use manual permission mode as before. The owner approves the proposal and sees the results.

### Gate failure handling
- **D-05:** If any gate check (offline suite, real-chain regressions, replay, mode/recovery checks, live smoke) reproduces a failure in the four qualifying classes, Phase 61 gets ONE fix round: a before/after fixture plus a mutation check per fix, then a full gate re-run on the new candidate. If it still fails, do not ship. Record the failure and re-scope.
- **D-06 (hard cap):** No second fix round without the owner's explicit go-ahead, given with the reproduction in front of them. The workflow never opens one on its own (Phase 60 ran three gap rounds under a one-cycle rule; this must not repeat).
- **D-07:** Anything outside the four classes, from the live smoke or anywhere else (wording, one extra re-ask that fails toward asking, etc.), is carried as a named known limit in the release record and the backlog, and the release continues.

### Release record and sign-off
- **D-08:** The 2.14.0 GitHub release notes include a short **"Known limits"** section: 3–6 plain-language, user-visible bullets (e.g. untracked files never trigger a re-ask (R7); very large PRs stop the review (R17); the live PR route was checked once (R6/D-03); routes not run live). The full residual ledger stays in `.planning`.
- **D-09:** Before release, the owner signs off on **one plain-terms page**: pass/fail per gate check, the live-smoke outcome, replay differences (expected: none), user-visible limits, the Dependabot note (D-10), and waiver text for everything not proven live. The full ~34-item residual ledger (59-REPRO R1–R8, 60-REPRO R1–R26) is linked, not walked through.
- **D-10:** Dependabot alerts are disabled on thejuran/vibe-check, and `gh pr list --author app/dependabot` needs a token scope the CLI lacks. The release record states this and that the shipped scripts have no third-party runtime dependencies (stdlib only). The planner verifies this claim, separating test-only tooling such as pytest. No repo setting change.

### Mode and candidate scope
- **D-11:** Offline integration checks cover **all routes and recovery paths**: default, GSD, range, PR, `--all` (its recorded unsupported-fixture status, `TestRouteAll`), incremental pass ≥2; `--finalize` including its one rebuild and the plain no-write stop; pause/resume; the fix loop. Mostly existing tests, run on the exact candidate commit.
- **D-12:** Every gate check runs on the **final release commit**: version already bumped to 2.14.0, the commit that will be tagged. Any later change re-runs the affected checks (all of them if production code changes).

### Claude's Discretion
- Throwaway-repo design for the live smoke, and the exact finding/edit used to trigger the reopen.
- Which existing tests make up "targeted real-chain regressions" (e.g. `TestStaleDecisions59`, the 60 route/coordinate/Finalize walk classes) and how the mode/recovery checks are grouped and reported.
- Release record file name/layout (e.g. `61-RELEASE-RECORD.md`) and the wording of the plain-terms page and the release-notes bullets.
- How the version bump and the release PR ride with the close workflow (the v2.13 precedent was a release PR from a separate branch). Must satisfy D-12.

</decisions>

<specifics>
## Specific Ideas

- The live smoke exists specifically to catch the Phase 60 failure class: prose that works in tests but that the model runs wrong across fresh Bash calls (BLOBFILE/GATEFILE printed paths, re-mint on rebuild).
- The owner reads results in plain terms. Show pass/fail and user impact, not code.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §"Phase 61: Release gate — decision reliability" — goal, approved scope, success criteria
- `.planning/REQUIREMENTS.md` §"Release gate (GATE)" — GATE-01..03
- `.planning/STATE.md` — Phase 61 inputs from Phase 60 (R5, R6, R17, replay deltas none)

### Residuals and limits to state in the release record
- `.planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md` §Residuals — R1–R8
- `.planning/phases/60-exact-change-evidence-and-reliable-finalize/60-REPRO.md` §Residuals — R1–R26 (R5 install resync, R6 live PR fetch, R7 untracked files, R10 `--all` unsupported, R11 replay pin, R17 PR size limit)
- `.planning/phases/60-exact-change-evidence-and-reliable-finalize/60-HUMAN-UAT.md` — owner rulings (R16, R17 accepted, R25 → backlog 999.27)
- `.planning/phases/60-exact-change-evidence-and-reliable-finalize/60-VERIFICATION.md` — final verification state
- `.planning/phases/59-stale-decisions-and-lost-deferrals/59-CONTEXT.md`, `.planning/phases/60-exact-change-evidence-and-reliable-finalize/60-CONTEXT.md` — locked rules carried here

### Cost and release precedent
- `.planning/milestones/v2.12-phases/54-freeze-release-gates-integration-audit/54-BUDGET.md` — measured unit costs for the live-smoke proposal
- `.planning/milestones/v2.13-MILESTONE-AUDIT.md` — prior close: integration checks, human_needed waiver pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `plugins/vibe-check/scripts/test_replay.py` + `replay.py`: archived replay (GATE-02), pinned by `TestReplayPin`.
- `plugins/vibe-check/scripts/diff_ranges.py`: the range builder for the D-03 live PR-fetch check.
- `plugins/vibe-check/scripts/fixtures/pr-cumulative.diff`: checked-in PR #5 capture, the offline counterpart of D-03.
- `test_decision_continuity.py` (`TestStaleDecisions59`, real-chain fixtures), `test_diff_ranges.py` (route classes `TestRoute*`, `TestRouteAll`), `test_finalize_card.py` (fresh-shell Finalize walks): the targeted real-chain regressions.
- `~/.b3/b3` block runner and the tmux-driven session pattern from earlier measurement runs (memory: b3-block-runner, phase40 batch validation).

### Established Patterns
- Suite runs as bare `pytest -q` from `plugins/vibe-check/scripts` (last full run 3821 passed at cef9a1e). `python3 -m pytest` is known not to work there.
- Reverse runs / REPRO ledgers record red and green SHAs for every verdict.

### Integration Points
- Version lives in `plugins/vibe-check/.claude-plugin/plugin.json` (currently 2.13.0), plus any marketplace manifest that pins a version.
- Install cache: `~/.claude/plugins/cache/thejuran/vibe-check/<version>`. A resync needs `claude plugin update` (or uninstall+install for same-version staleness) and a process relaunch.

</code_context>

<deferred>
## Deferred Ideas

- Live runs of GSD, range, PR and incremental routes: not in this gate (D-02). Revisit only if the default-route smoke fails in a way that implicates shared range-source prose.
- Enabling Dependabot on the repo: not done (D-10).
- All 59/60 residuals not in the four qualifying classes stay carried. Lean orchestration (Finalize extraction) starts only after this release ships.

</deferred>

---

*Phase: 61-release-gate-decision-reliability*
*Context gathered: 2026-10-30*
