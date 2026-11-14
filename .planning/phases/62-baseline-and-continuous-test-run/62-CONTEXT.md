# Phase 62: Baseline and continuous test run - Context

**Gathered:** 2026-11-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Before any extraction starts, this phase delivers three things and nothing else:

1. A go/no-go note on cost visibility, built from existing local records only (BASE-01, backlog 999.12).
2. The pinned 2.14.1 comparison baseline: behaviour, mode-path bytes and loaded-file traces for plain review, deep review and Finalize, plus the written comparison workload and improvement criterion (BASE-02, BASE-03, BASE-04).
3. One GitHub Actions workflow that runs the existing offline suite and the stdlib-only check on every push and every pull request to `main`, proven green on the baseline and red on a deliberately failing commit (CI-01, CI-02).

No plugin behaviour changes in this phase. The plugin code stays byte-identical to 2.14.1 (`dd8e4ab`, tag `v2.14.1`). No paid run, no live model call, no new telemetry, no report built, no branch-protection change.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked — do not re-litigate)
- No growth per round (owner, 2026-10-17, restated 2026-10-28). Work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow. Everything else is carried.
- Paid or live runs need a separately bounded proposal that the owner explicitly approves. This phase starts none.
- Each phase starts by recording the current behaviour or measurement on current code. A path that does not reproduce is recorded and dropped, never replaced with invented work. Every lock lands with a mutant that trips it.
- Missing cost attribution ends accounting work, not the milestone; labelled footprint/operation counts are the evidence instead.
- Byte and operation counts are always reported separately from token or price estimates. Token figures derived from bytes are proxies and are labelled as proxies. Subscription usage is not a bill.
- Shipped scripts stay stdlib-only. `stable_hash` / GOLDEN_DIGEST stay frozen.
- One branch and one PR per phase: `feat/v2.15-phase-62`, deleted locally and on GitHub after its PR merges.
- CI adds a check only: no secrets, no branch-protection change (enforcement is a separate owner decision).

### Improvement criterion (BASE-04)
- **D-01:** Two labelled counts are the milestone's measures, both on the Finalize path: (a) bytes of instructions loaded, as measured by `footprint.py`; (b) the number of mechanical steps the model must carry out itself (commands it runs and values it copies between them). The slice passes if at least one count drops and neither grows.
- **D-02:** There is no percentage target. Pass means any real, measured drop on the same paths with identical behaviour. The release notes report the actual figure. Nothing is ever cut to reach a number (the v2.10 rule recorded in `footprint.py`).
- **D-03:** New helper code and its tests are reported next to the result as a separate labelled "maintenance added" figure. They are not subtracted from the saving and do not decide pass or fail.
- **D-04:** If Phase 63's Finalize slice matches behaviour but shows no drop in either count, the default is revert (FINX-05). Before reverting, the owner gets one plain-terms page with the two counts and any reliability evidence, and may keep the slice by explicit waiver. There is no automatic second attempt.
- **D-05:** The counting rule for "model-run mechanical steps" must be written down in this phase, applied to 2.14.1 to produce the baseline number, and be repeatable by a script or a fixed written procedure, so Phase 63 counts the same way.

### Comparison workload (BASE-02, BASE-03, BASE-04)
- **D-06:** The baseline records bytes and loaded-file traces for all three paths (plain review, deep review, Finalize). The pass/fail comparison in Phase 63 uses Finalize only. Plain and deep review are re-measured at the Phase 65 release gate only to prove they did not grow.
- **D-07:** The fixed Finalize comparison set is five named situations, re-run unchanged after the extraction:
  1. Clean close that writes the report.
  2. Close with open decisions that shows the card first.
  3. The one automatic rebuild after a missing input.
  4. A refused or failed close that writes nothing and archives nothing.
  5. Restart in a fresh shell.
- **D-08:** The pinned behavioural baseline is an offline record taken at the exact `v2.14.1` commit: the full offline suite result (count, pass/fail), the archived replay output, and the gate decisions and report text produced for the five situations in D-07, each saved with a fingerprint. "Same behaviour" in later phases means these match byte for byte; any difference is named and explained or it blocks.
- **D-09:** Loaded-file traces come only from sessions already recorded on this machine. Where a recorded 2.14.x session exists for a path, its trace is marked "observed". Where none exists, the baseline records the file list the tool declares for that path, marked "declared, not observed", and names the gap. No session is run to fill a gap, and older-version sessions are not used as a stand-in.

### Cost note: sources and what "go" means (BASE-01)
- **D-10:** Records that may be inspected: the repo's archived runs and Claude Code's local session logs for this project. Only field names, counts and aggregate numbers leave the logs. No transcript text, file contents, private instructions or account details are quoted, and no log is copied into the repo. No third-party usage tool is installed; reading is done with a short stdlib script.
- **D-11:** A usage field is "trustworthy" only if it is (1) present in every sampled session of that kind, (2) tied to a specific review run and a specific reviewer lane without guessing, and (3) consistent (lane totals match the run total). Every field gets one of three labels: measured, estimated, missing. Nothing is priced in dollars.
- **D-12:** A "go" builds nothing in v2.15. The note names the smallest useful report and it is filed as its own backlog item for the owner to schedule. The only use inside this milestone: if attribution is reliable, the Phase 65 release record may quote before/after usage from sessions that already exist, labelled as such. Usage is not a third pass/fail criterion.
- **D-13:** The investigation is one plan and one pass over a fixed, named sample: the most recent recorded plain review, deep review and Finalize sessions (up to about 5 each, whatever exists) plus the repo archives. If attribution is not reliable on that sample, the answer is no-go and the work stops. No second pass, no wider search, no workaround.

### Where records live and the CI proof (CI-01, CI-02)
- **D-14:** The baseline (suite result, replay output, Finalize outputs, byte counts, traces) is committed to the public repo under the design-evidence area (`docs/design/`), at a path the test run can read. The go/no-go note is committed with the phase records, as earlier phases were. It holds only field names and aggregate token counts.
- **D-15:** The red proof is one commit that breaks a single test, pushed to a throwaway branch named for the purpose (for example `ci-red-proof`). No pull request is opened. The run link and result are saved in the phase record, then the branch is deleted. Nothing touches `main`.
- **D-16:** Green is proven in two steps. Before merge: the phase branch shows green, and a recorded comparison proves the plugin code is byte-identical to 2.14.1 (only the workflow and records were added). After the one phase PR merges: `main`'s first run is recorded as the closing step. The phase is marked complete only after that run is green.
- **D-17:** If tests fail on GitHub's Linux machines for environment reasons, each failure is recorded with its reproduction first. Fixes may change the workflow's setup or a test's own environment assumptions. No test is skipped, deleted or weakened to get green, the runner is not switched to macOS to hide the problem, and no plugin code changes. If green would require touching plugin code, work stops and goes to the owner, because the 2.14.1 baseline would no longer be untouched.

### Claude's Discretion
- Workflow details: Python version(s), runner image, test runner invocation, file name, job layout, caching. The push trigger must fire on the throwaway branch in D-15 (so push is not limited to `main`), and pull requests targeting `main` must trigger it.
- Which existing test or command is "the stdlib-only check" (the `TestImportSet` classes or a single dedicated check), provided CI runs it explicitly and it is mutation-checked.
- Exact folder and file names for the baseline under `docs/design/`, the fingerprint method, and how the five Finalize outputs are captured from 2.14.1 (existing tests and fixtures first).
- The exact wording and layout of the go/no-go note and of the counting rule in D-05.
- Plan count and split. The cost note is one plan (D-13).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` — "Phase 62: Baseline and continuous test run" (goal, approved scope, 5 success criteria) and backlog "999.12: Narrow: Cost visibility feasibility"
- `.planning/REQUIREMENTS.md` — BASE-01..04, CI-01..02, the working rule, the no-growth rule, the equivalence baseline, Out of Scope table
- `.planning/STATE.md` — current position and deferred items
- `/Users/julianamacbook/Documents/Codex/planning/PLANNING-FORMAT.md` — required format for STATE.md and ROADMAP.md edits

### Footprint and traces
- `plugins/vibe-check/scripts/footprint.py` — `MODE_PATHS` (the declared file set per mode path), byte/word counts, proxy-token labelling rule
- `plugins/vibe-check/scripts/tracecheck.py` and `plugins/vibe-check/scripts/fixtures/mode-path-expectations.json` — how recorded sessions are checked for which files were loaded
- `docs/design/prose-diet-footprint-v2.10.md` and `docs/design/mode-path-validation-v2.10.md` — the v2.10 precedent for a footprint table and observed mode-path traces
- `docs/design/prose-to-code-inventory.md` — earlier inventory of prose that could move to code

### Behavioural baseline and replay
- `plugins/vibe-check/scripts/replay.py` — offline re-scoring of archived runs; evidence and output rules
- `docs/design/b3-ground-truth/` — committed archives and `REPLAY-REPORT-*` files (replay input and prior outputs)
- `plugins/vibe-check/phases/shared/90-finalize.md` — the Finalize instructions being baselined
- `plugins/vibe-check/scripts/finalize_gate.py`, `test_finalize_gate.py`, `test_finalize_card.py`, `test_finalize_archive_prose.py` — existing Finalize gate and walks covering the five situations in D-07
- `.planning/milestones/v2.14-phases/60-exact-change-evidence-and-reliable-finalize/60-CONTEXT.md` — Finalize hardening decisions (printed-path rule, one rebuild, no write on failure)
- `.planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-CONTEXT.md` and `61-RELEASE-RECORD.md` — release-gate precedent, stdlib-only claim (D-10), what was run live

### Cost evidence
- `.planning/milestones/v2.12-phases/54-freeze-release-gates-integration-audit/54-BUDGET.md` — prior unit-cost estimates (estimates, not measurements)

### Testing
- `.planning/codebase/TESTING.md` — runner commands, flat co-located test layout, `TestImportSet` pattern
- `.planning/codebase/STRUCTURE.md` — where scripts, phases and design evidence live

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `footprint.py`: already prints bytes, words and labelled proxy tokens per mode path, at the worktree or at a revision (`--rev`). Reading at 2.14.1 on 2026-11-13: review-plain 192,057 bytes / 13 files; deep-plain 268,997 / 19; finalize 136,114 / 7; fix-loop 255,070 / 14. It exited 2 on this run; the reason was not investigated and must be understood before its output is used as the baseline.
- `replay.py` + `test_replay.py` (64 tests): the archived-replay check the baseline pins.
- `tracecheck.py`: checks a recorded session against expected phase sequence and lazy reads; the source for "observed" traces.
- Finalize tests: `test_finalize_card.py` (95), `test_finalize_gate.py` (62), `test_finalize_archive_prose.py` (17), including fresh-shell walks from Phase 60.
- `gitfixture.py`: shared test helper for building real git repos in tests.

### Established Patterns
- Tests are `unittest.TestCase`, flat and co-located in `plugins/vibe-check/scripts/`. Both `python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'` and `pytest` run them. No runner config file exists.
- Each module pins its own import set with a `TestImportSet` class; that is the existing stdlib-only evidence.
- Blob/commit pinning (`replay.load_scorer("blob:<sha>")`) is the house way to compare old code with new.
- Evidence that tests read lives under `docs/design/` and is committed; session transcripts are gitignored and bound by hash.
- The suite has only run on macOS (Python 3.14 locally). Tests shell out to `git`. Linux runner behaviour is unknown.

### Integration Points
- `.github/workflows/` does not exist yet; the workflow is the first file there.
- Repo is `thejuran/vibe-check`, public, default branch `main`.
- `.planning/` is gitignored, but phase records are committed by the planning tool (239 files tracked), so the go/no-go note becomes public with the phase.
- Local usage evidence: the one archived transcript sampled (`docs/design/freeze-v2.12/...`) carried no usage fields. Claude Code session logs for this project (39 sessions, 33 with subagent folders) under `~/.claude/projects/` are the other source allowed by D-10.

</code_context>

<specifics>
## Specific Ideas

- The owner reads results in plain terms: the go/no-go note and any waiver page must be readable without code knowledge, with pass/fail and numbers up front.
- "Fewer model-run steps is where reliability comes from; bytes is what the tool already measures" is the reasoning behind D-01.

</specifics>

<deferred>
## Deferred Ideas

- The smallest useful usage report, if the note says "go": its own backlog item, scheduled by the owner (D-12).
- Token usage as a pass/fail measure: would need comparable live runs under an approved paid proposal; not in this milestone.
- Branch protection requiring the CI check: separate owner decision (already Out of Scope in REQUIREMENTS.md).
- A live Finalize capture on 2.14.1: only under a separately approved bounded proposal.

</deferred>

---

*Phase: 62-baseline-and-continuous-test-run*
*Context gathered: 2026-11-13*
