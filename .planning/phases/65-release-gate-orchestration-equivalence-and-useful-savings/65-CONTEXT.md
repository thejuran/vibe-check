# Phase 65: Release gate — orchestration equivalence and useful savings - Context

**Gathered:** 2026-11-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the 2.15.0 release candidate is equivalent to plugin 2.14.1 (`dd8e4ab`, tag `v2.14.1`) in behaviour, report its reduction in loaded prose / model-run steps without any unsupported cost claim, and ship it through the existing close workflow (GATE-04, GATE-05, GATE-06). The candidate carries the Phase 63 Finalize extraction alone (Phase 64 closed as a recorded skip, 64-CONTEXT D-01/D-03). No new extraction, no reviewer-efficiency work, no new capability.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked — do not re-litigate)
- **Pass rule (Phase 62 D-01–D-03):** at least one of the two Finalize-path counts (`footprint.py` bytes loaded; `step_count.py` rule v1 model-run steps) drops and neither grows. No percentage target; nothing is cut to reach a number. Helper code and tests are a separate "maintenance added" figure. Byte/step figures are always reported separately from tokens or dollars; no billing-savings claim without comparable usage evidence (Phase 62 cost note D-12).
- **Same behaviour (Phase 62 D-07/D-08, Phase 63 D-15):** the five Finalize situations (`clean-close`, `card-first`, `one-rebuild`, `refused-close`, `fresh-shell-restart`), the full offline suite and the archived replay match the pinned 2.14.1 baseline (`docs/design/lean-v2.15/baseline/`) on every outcome field; the recorded command lists are the intended difference. Any other difference is named and explained or it blocks. `stable_hash` / GOLDEN_DIGEST frozen.
- **Accepted differences (Phase 63 owner go + D-19, D-24–D-28):** the deliberate differences already accepted by name in `63-RESULT.md` ("Your decision" items 1–5, the D-27 60-second git limit as the sixth, and the D-19 subfolder behaviour) are expected and do not block. Anything not on that list does.
- **Mac-only tests (Phase 62 D-18/D-20):** the five CI-deselected tests and the Linux self-skipping tests run on the owner's Mac at this gate, where the baseline has 0 skips.
- **Gate placement and candidate:** every gate check runs on the final release commit (version already bumped to 2.15.0, the commit that will be tagged); any later production-code change re-runs all checks (Phase 61 D-12 pattern). Gates run before the publish plan (owner, 2026-10-01). Install resync to the candidate + relaunch before any manual/live check.
- **Release mechanics:** a completed milestone always publishes (ff/merge `main`, push main + tag, `gh release create`; marketplace pins `ref: main`). One branch/PR: `feat/v2.15-phase-65` from `main`, deleted locally and on GitHub after merge. Dependabot alerts are disabled on thejuran/vibe-check and `gh` lacks the scope; the release record states this plus that shipped scripts are stdlib-only (test tooling such as pytest separated), no setting change.
- **Standing rules:** no growth per round; work added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow; each check starts by recording current behaviour; every lock lands with a mutant; paid/live runs need a separately approved bounded proposal.

### Live validation (GATE-06)
- **D-01:** The gate includes one bounded live smoke run, under a written proposal the owner approves before anything is spent. Shape as in 2.14 (Phase 61 D-01): about 3 sessions, est. $20–30 (unit cost ~$6–9 per review session, 54-BUDGET.md). Purpose: prove the model follows the rewritten Finalize instructions (call the helper, act on its structured result) and the shared state-path printing from fresh shells — which offline tests cannot show.
- **D-02:** Smoke scope is the **default route + Finalize** only: resync install → on a throwaway repo, review → decide a finding → `--finalize` writes REVIEW.md. The fix loop (X8), `--all` (C1) and the other routes rest on offline proof; the release record and notes name them as not run live, under an explicit owner waiver.
- **D-03:** The assistant drives the sessions via tmux, manual permission mode, with the clone's auto-memory parked before any measurement session (Phase 61 D-04 pattern). The owner approves the proposal and sees the results.

### Review-path growth
- **D-04:** The plain/deep review (and other review-path) growth from the Phase 63 owner-chosen fixes (plain 192,057 → 193,267 bytes; deep 268,997 → 270,219 at `d56232b`) is **accepted as named growth**, not a block. Phase 62 D-06's "prove they did not grow" check becomes: re-measure every review path on the candidate and show it grew by nothing beyond the itemised Phase 63 D-09 items (file, bytes, steps, commit, reason). Any unitemised growth blocks. The owner signs it on the sign-off page.
- **D-05:** The release notes carry one short "What changed in size" block showing both sides: the Finalize drop (steps and bytes, 2.14.1 → candidate) and every review path's ~0.6% growth from the named safety/state-path fixes. Labelled as bytes and steps, not tokens or cost.

### Carried review items
- **D-06 (999.34 WR-02/WR-03):** Bypass and carry. The gate does not rely on the two lenient Phase 62 checks: it recounts 2.14.1 and the candidate directly from their commits with `step_count.py` and `footprint.py` and confirms the fingerprints in `docs/design/lean-v2.15/baseline/MANIFEST.json` are unchanged (same method as Phase 63 D-13). The two checks stay in backlog.
- **D-07 (999.38):** One offline attempt to reproduce WR-02 (an empty phase id making every phase in a repo share one saved-progress file), by the Phase 60 fresh-shell standard. If it reproduces as data loss or a wrong close, it qualifies under the four-class rule and goes to the owner as the D-08 fix round. Otherwise it is carried. WR-03, WR-04, SA-01, SA-03 are carried as accepted at the Phase 63 go; any that a user can see is named as a known limit.

### Gate failure handling
- **D-08:** A qualifying failure (four classes) in any gate check — offline suite, archived replay, the five Finalize situations, mode/recovery checks, review-path growth, or the live smoke — gets ONE fix round: a before/after case plus a mutant per fix, then a full gate re-run on the new candidate. If it still fails, do not ship; record and re-scope.
- **D-09 (hard cap):** No second fix round without the owner's explicit go, given with the reproduction in front of them. The workflow never opens one on its own.
- **D-10:** Anything outside the four classes is carried as a named known limit in the release record and backlog, and the release continues.

### Release record and sign-off
- **D-11:** The 2.15.0 release notes say "same behaviour as 2.14.1 except:" followed by the user-visible accepted differences in plain words (e.g. a review on a folder/branch name containing `$`, a backtick, `"` or `\` now stops with a message; Finalize from a subfolder now closes findings correctly; a git call slower than 60 seconds leaves a finding open; one "Permission denied" line no longer shows), plus a 3–6 bullet "Known limits" section (e.g. fix loop and `--all` not run live). The full difference and residual lists live in the release record.
- **D-12:** Before release the owner signs off on one plain-terms page: pass/fail per gate check, the live-smoke outcome, the two counts (Finalize down; review paths' named growth), replay and situation differences (expected: only the accepted ones), the D-07 outcome, user-visible limits, the Dependabot/stdlib note, and waiver text for routes not run live. Detailed ledgers are linked, not walked through. The owner gives go or no-go.

### Claude's Discretion
- Throwaway-repo design for the smoke and what the smoke checks to call it a pass (e.g. REVIEW.md written, gate result and card behaviour as expected, no stop).
- Which existing tests make up the mode/recovery integration checks (default, GSD, range, PR, `--all` recorded status, incremental pass ≥2, `--finalize` incl. one rebuild and the no-write stop, pause/resume, fix loop) and how results are grouped.
- Release record file name/layout (e.g. `65-RELEASE-RECORD.md`), sign-off page wording, release-notes wording.
- How the version bump and release PR ride with the close workflow, provided every check runs on the commit that is tagged.
- Plan count and split (gates-first, publish plan last with the owner's pre-push checkpoint).

</decisions>

<specifics>
## Specific Ideas

- Follow the v2.14 Phase 61 gate as the model (`.planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-CONTEXT.md`): bounded smoke, one capped fix round, one sign-off page, Known limits in the notes.
- The release notes must not read as "identical to 2.14.1"; the unsafe-name stop is a visible behaviour change and is stated.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` — Phase 65 section (goal, approved scope, success criteria) and backlog 999.34, 999.36, 999.37, 999.38
- `.planning/REQUIREMENTS.md` — GATE-04, GATE-05, GATE-06; equivalence baseline definition; out-of-scope table

### Baseline and counting rules
- `docs/design/lean-v2.15/BASELINE-v2.14.1.md` — pinned 2.14.1 counts, traces, situations
- `docs/design/lean-v2.15/CRITERION.md` — improvement criterion and comparison workload
- `docs/design/lean-v2.15/baseline/MANIFEST.json` — fingerprints the gate confirms unchanged (D-06)
- `docs/design/lean-v2.15/tools/step_count.py`, `plugins/vibe-check/scripts/footprint.py` — the counting tools (rule v1)
- `docs/design/lean-v2.15/tools/finalize_capture.py` — five-situation capture harness
- `.planning/phases/62-baseline-and-continuous-test-run/62-CONTEXT.md` — D-01–D-09, D-18, D-20

### Phase 63 outcome (what the candidate contains)
- `.planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-RESULT.md` — counts, accepted differences, named growth, carried items
- `.planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-COUNTS.md`, `63-EQUIVALENCE.md`, `63-REMOVAL-LEDGER.md`, `63-REPRO.md`, `63-REVIEW.md`, `63-REVIEW-2.md`
- `.planning/phases/63-finalize-extraction-and-cross-call-variable-check/63-CONTEXT.md` — D-09, D-13, D-16, D-19–D-28
- `.planning/phases/64-optional-bounded-extension-conditional/64-CONTEXT.md` — recorded skip

### Release-gate precedent
- `.planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-CONTEXT.md` — gate shape this phase follows
- `.planning/milestones/v2.12-phases/54-freeze-release-gates-integration-audit/54-BUDGET.md` — per-session unit cost for the smoke proposal

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `step_count.py`, `footprint.py`, `finalize_capture.py`, `baseline_records.py`, `path_records.py`: recount and re-capture tools already pinned to 2.14.1.
- `plugins/vibe-check/scripts/test_replay.py` / `replay.py`: archived replay; `test_finalize_inputs.py` incl. the side-by-side 2.14.1 grid (D-26/D-28).
- `.github/workflows/offline-suite.yml` CI run (Phase 62) with deselect/skip guards — the standing check behind the gate.

### Established Patterns
- Release record + one plain-terms sign-off page + Known limits notes (v2.14 Phase 61).
- Equivalence = recount both commits directly, never trust a typed record figure (Phase 63 D-13).

### Integration Points
- `plugins/vibe-check/.claude-plugin/plugin.json` version 2.14.1 → 2.15.0 on the candidate.
- Milestone close workflow (`/bm:complete-milestone`) and `gh release create` after the gate passes.

</code_context>

<deferred>
## Deferred Ideas

- 999.34 WR-02/WR-03 tightening of the lenient baseline checks — carried (D-06).
- 999.38 WR-03, WR-04, SA-01, SA-03 — carried; WR-02 carried unless D-07 reproduces it.
- Live runs of the fix loop and `--all` — not in this smoke (D-02); waived.

</deferred>

---

*Phase: 65-release-gate-orchestration-equivalence-and-useful-savings*
*Context gathered: 2026-11-15*
