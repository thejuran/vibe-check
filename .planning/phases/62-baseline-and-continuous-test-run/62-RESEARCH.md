# Phase 62: Baseline and continuous test run - Research

**Researched:** 2026-11-13
**Domain:** GitHub Actions CI for a stdlib-only Python plugin test suite; offline behavioural and footprint baselining; usage-field feasibility from local Claude Code session logs
**Confidence:** HIGH for the repo facts. Every repo claim below was run in this session at HEAD `aa31ccd`, whose `plugins/` tree equals `v2.14.1` (`90e0697…` both). MEDIUM for GitHub runner behaviour: it was reproduced in an `ubuntu:24.04` container on arm64, not yet on a real x64 GitHub runner.

## Summary

**The main finding: the suite is not green on Linux as it stands.** At `v2.14.1` the suite passes in full on the owner's Mac: **3886 passed, 0 skipped** under both `pytest` and `python3 -m unittest discover` (195 s and 204 s). I ran it in an Ubuntu 24.04 container as a non-root user with zsh, node and pytest installed. **Five tests can never pass on a GitHub Linux runner using workflow setup alone:**

- Three in `test_replay.TestPhase53SameLineRegressionCases` read the gitignored Phase-43 session transcripts. Those files exist only in the owner's primary checkout.
- Two in `test_footprint.TestWordCountLocaleDrift` assert BSD `wc -w` counts. GNU coreutils 9.4 counts differently.

Three more replay tests (`TestCensus`, `TestReconstruction`, `TestGuardrail`) expect 12 private transcripts in a primary checkout. They pass if the suite runs from a **linked git worktree**, which is the suite's own documented "no private transcripts" mode. Every other Linux failure seen in a naive run was caused by the environment and is fixed by setup: no `/bin/zsh`, no `pytest` for `batchsnap`, running as root. So CI-02 ("green on the baseline") needs an **owner decision**. D-17 forbids skipping tests to get green, and editing the tests would break D-16's "plugin tree byte-identical to 2.14.1". This research recommends one option, stated below.

The baseline work is mostly assembly of existing tools:

- **`footprint.py`.** It exits 0 at `--rev v2.14.1` and prints exactly the CONTEXT numbers. Its only exit-2 path is an argument error, which prints usage and no table, so the earlier "exit 2" came from a different invocation. Not a defect.
- **`replay.py`.** `baseline`, `diff` and `candidate` are deterministic except for two header lines (`HEAD`/`head` and `generated`). The fingerprints must exclude those lines.
- **`tracecheck.events()` / `successful_reads()`.** These already pull loaded-file traces out of recorded sessions.

Recorded 2.14.x sessions exist on this machine:

- Four plain reviews: two at the 2.14.0 candidate in `~/.b3/smoke61`, two at 2.14.1 in `~/.b3/smoke2141`.
- One Finalize, at the 2.14.0 candidate.
- **No deep review.** The deep-review trace is therefore "declared, not observed".

The observed traces differ from footprint's declared lists. Finalize also reads `templates/review-md-schema.md` (5,035 bytes), and plain review reads `templates/output-format.md` (14,226 bytes). Neither file is in `MODE_PATHS`. BASE-02 must report declared and observed separately.

**Cost visibility.** The 2.14.x session logs carry per-message `model` and `usage` (input, output, cache-creation and cache-read tokens). Per-lane attribution is possible through `subagents/*.meta.json` `agentType` (`vibe-check:security` and others). There are three traps:

- Each API message is logged once per content block. 104 records cover 56 unique `message.id`, so naive summing doubles the totals.
- Agents run async, so the parent's Agent tool result carries no token or duration totals. No independent run total exists to check lane sums against, which is D-11 condition (3).
- No retry field exists.

The archived b3 transcripts are main-session-only copies (no subagent files), and the freeze-v2.12 SDK harness transcripts carry no usage at all. This points toward a narrow result: "go for model and token fields per run and per lane on interactive 2.14.x sessions; missing for retries and for an independent run total". The plan must reach that verdict on its fixed D-13 sample, not take it from this research.

**Primary recommendation:**

- **CI.** Add `.github/workflows/offline-suite.yml` on `ubuntu-24.04` with SHA-pinned `actions/checkout` v7.0.1 (`fetch-depth: 0`) and `actions/setup-python` v7.1.0 (Python 3.14). Install zsh and `pytest==9.0.3`. Run a dedicated stdlib-only scan as its own step. Run the suite from a linked worktree, with exactly five named tests deselected, and only after the owner approves that list.
- **Baseline.** Put it under `docs/design/lean-v2.15/` with stdlib tools and their mutant tests beside it.
- **Counting rule.** Make the D-05 rule a script, not prose.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Continuous test run (CI-01/02) | GitHub Actions (hosted Linux runner) | Repo (`.github/workflows/`) | Runs on push/PR with no secrets; adds a check only, no branch protection |
| Stdlib-only check | CI step running a repo script | — | Must run explicitly and be mutation-checked; lives outside `plugins/` to keep the plugin tree byte-identical |
| Behavioural baseline capture (BASE-03) | Local offline tools (stdlib Python + git) | Committed evidence `docs/design/lean-v2.15/` | Pinned at `v2.14.1`; read by later phases' tests |
| Footprint bytes + traces (BASE-02) | `footprint.py --rev v2.14.1` (declared) + `tracecheck` over recorded sessions (observed) | Committed evidence | Bytes/ops never mixed with token/price |
| Counting rule (BASE-04, D-05) | Stdlib script over the Finalize path prose | Written procedure in the criterion doc | Must be repeatable unchanged in Phase 63 |
| Cost note (BASE-01) | Local read-only stdlib script over `~/.claude/projects/…` | Phase record (`62-COST-NOTE.md`) | Only field names and aggregate numbers leave the logs (D-10) |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Carried forward (locked — do not re-litigate)
- No growth per round (owner, 2026-10-17, restated 2026-10-28). Work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow. Everything else is carried.
- Paid or live runs need a separately bounded proposal that the owner explicitly approves. This phase starts none.
- Each phase starts by recording the current behaviour or measurement on current code. A path that does not reproduce is recorded and dropped, never replaced with invented work. Every lock lands with a mutant that trips it.
- Missing cost attribution ends accounting work, not the milestone; labelled footprint/operation counts are the evidence instead.
- Byte and operation counts are always reported separately from token or price estimates. Token figures derived from bytes are proxies and are labelled as proxies. Subscription usage is not a bill.
- Shipped scripts stay stdlib-only. `stable_hash` / GOLDEN_DIGEST stay frozen.
- One branch and one PR per phase: `feat/v2.15-phase-62`, deleted locally and on GitHub after its PR merges.
- CI adds a check only: no secrets, no branch-protection change (enforcement is a separate owner decision).

#### Improvement criterion (BASE-04)
- **D-01:** Two labelled counts are the milestone's measures, both on the Finalize path: (a) bytes of instructions loaded, as measured by `footprint.py`; (b) the number of mechanical steps the model must carry out itself (commands it runs and values it copies between them). The slice passes if at least one count drops and neither grows.
- **D-02:** There is no percentage target. Pass means any real, measured drop on the same paths with identical behaviour. The release notes report the actual figure. Nothing is ever cut to reach a number (the v2.10 rule recorded in `footprint.py`).
- **D-03:** New helper code and its tests are reported next to the result as a separate labelled "maintenance added" figure. They are not subtracted from the saving and do not decide pass or fail.
- **D-04:** If Phase 63's Finalize slice matches behaviour but shows no drop in either count, the default is revert (FINX-05). Before reverting, the owner gets one plain-terms page with the two counts and any reliability evidence, and may keep the slice by explicit waiver. There is no automatic second attempt.
- **D-05:** The counting rule for "model-run mechanical steps" must be written down in this phase, applied to 2.14.1 to produce the baseline number, and be repeatable by a script or a fixed written procedure, so Phase 63 counts the same way.

#### Comparison workload (BASE-02, BASE-03, BASE-04)
- **D-06:** The baseline records bytes and loaded-file traces for all three paths (plain review, deep review, Finalize). The pass/fail comparison in Phase 63 uses Finalize only. Plain and deep review are re-measured at the Phase 65 release gate only to prove they did not grow.
- **D-07:** The fixed Finalize comparison set is five named situations, re-run unchanged after the extraction:
  1. Clean close that writes the report.
  2. Close with open decisions that shows the card first.
  3. The one automatic rebuild after a missing input.
  4. A refused or failed close that writes nothing and archives nothing.
  5. Restart in a fresh shell.
- **D-08:** The pinned behavioural baseline is an offline record taken at the exact `v2.14.1` commit: the full offline suite result (count, pass/fail), the archived replay output, and the gate decisions and report text produced for the five situations in D-07, each saved with a fingerprint. "Same behaviour" in later phases means these match byte for byte; any difference is named and explained or it blocks.
- **D-09:** Loaded-file traces come only from sessions already recorded on this machine. Where a recorded 2.14.x session exists for a path, its trace is marked "observed". Where none exists, the baseline records the file list the tool declares for that path, marked "declared, not observed", and names the gap. No session is run to fill a gap, and older-version sessions are not used as a stand-in.

#### Cost note: sources and what "go" means (BASE-01)
- **D-10:** Records that may be inspected: the repo's archived runs and Claude Code's local session logs for this project. Only field names, counts and aggregate numbers leave the logs. No transcript text, file contents, private instructions or account details are quoted, and no log is copied into the repo. No third-party usage tool is installed; reading is done with a short stdlib script.
- **D-11:** A usage field is "trustworthy" only if it is (1) present in every sampled session of that kind, (2) tied to a specific review run and a specific reviewer lane without guessing, and (3) consistent (lane totals match the run total). Every field gets one of three labels: measured, estimated, missing. Nothing is priced in dollars.
- **D-12:** A "go" builds nothing in v2.15. The note names the smallest useful report and it is filed as its own backlog item for the owner to schedule. The only use inside this milestone: if attribution is reliable, the Phase 65 release record may quote before/after usage from sessions that already exist, labelled as such. Usage is not a third pass/fail criterion.
- **D-13:** The investigation is one plan and one pass over a fixed, named sample: the most recent recorded plain review, deep review and Finalize sessions (up to about 5 each, whatever exists) plus the repo archives. If attribution is not reliable on that sample, the answer is no-go and the work stops. No second pass, no wider search, no workaround.

#### Where records live and the CI proof (CI-01, CI-02)
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

### Deferred Ideas (OUT OF SCOPE)
- The smallest useful usage report, if the note says "go": its own backlog item, scheduled by the owner (D-12).
- Token usage as a pass/fail measure: would need comparable live runs under an approved paid proposal; not in this milestone.
- Branch protection requiring the CI check: separate owner decision (already Out of Scope in REQUIREMENTS.md).
- A live Finalize capture on 2.14.1: only under a separately approved bounded proposal.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BASE-01 | Go/no-go note from existing local records; trustworthy usage fields per run and per lane; missing attribution; smallest useful report | §Cost-Note Source Inventory (sessions found, field names, dedupe trap, async-agent no-totals, retries absent); §Pattern 5 (read-only stdlib reader); Pitfalls 6–9 |
| BASE-02 | Mode-path bytes and actual loaded-file traces for plain review, deep review and Finalize, separate from token/price | §footprint.py findings (exit-2 resolved; numbers verified); §Observed vs declared traces (2.14.x sessions located; deep review has none); Pattern 3 |
| BASE-03 | Pinned behavioural baseline of 2.14.1 + archived replay results retained | §Suite baseline (3886/0, both runners); §Replay determinism (volatile header lines); Pattern 2 (five Finalize situations → existing walk mechanics) |
| BASE-04 | Comparison workload + improvement criterion written before extraction | D-01..D-07 locked; §Pattern 4 counting-rule prototype (2.14.1 static counts; observed 12 Bash / 4 Write in the 2.14.0 Finalize session) |
| CI-01 | One workflow; offline suite + stdlib-only check on every push and PR to `main`; no secrets/paid/live; no branch protection | §Code Examples workflow; §Linux reproduction; Security Domain |
| CI-02 | `main` green on release baseline; deliberate failing commit on throwaway branch red | §Linux reproduction (5 tests need owner decision); §Pattern 6 red/green proof; Open Question 1 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

No `./CLAUDE.md` exists in the repo. From the owner's global instructions that apply here:

- **Security (absolute):**
  - Never hardcode secrets. The workflow uses none.
  - Never log sensitive data. The cost reader prints field names and aggregates only, never transcript text.
  - Never pass untrusted input to a shell. The workflow must not interpolate `${{ github.event.* }}` into `run:` lines.
- **Correctness:** release resources on every path (temp dirs, worktrees: `try/finally` / `addCleanup`), and don't swallow exceptions silently.
- **Follow existing conventions:** flat `unittest.TestCase` tests, a `TestImportSet` per module, `bash -s <<'BASH'` fences, refusal messages in caps ending `— STOPPING`, and evidence under `docs/design/`.
- **Division of labour:** the owner decides product questions (the five-test CI question is one) and gets the tradeoff in plain terms. Technical choices are made by the planner and recorded.
- **Planning format:** `/Users/julianamacbook/Documents/Codex/planning/PLANNING-FORMAT.md` for STATE.md and ROADMAP.md edits. Refresh `last_updated`.
- **Releases:** Dependabot review applies at release planning, not in this phase. The alerts API is disabled on this repo (memory).

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| GitHub Actions hosted runner `ubuntu-24.04` | image 20261111 (coreutils 9.4, bash 5.2.21, git 2.56.1, node 22.23.4, python 3.12.3; **no zsh**) | CI host | Free for public repos; pin `ubuntu-24.04` rather than `ubuntu-latest` so a future 26.04 label move cannot change the result silently [VERIFIED: actions/runner-images README + Ubuntu2404-Readme.md via gh api] |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` (2026-07-20) | Clone with full history | `fetch-depth: 0` is mandatory (Pitfall 1) [VERIFIED: gh api repos/actions/checkout releases/latest + git ref] |
| `actions/setup-python` | v7.1.0 = `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` (2026-10-22) | Python 3.14 to match the owner's 3.14.5 baseline | Same interpreter major as the recorded baseline [VERIFIED: gh api]; 3.14 availability on 24.04 [ASSUMED] (fallback: runner's system 3.12.3, which I ran the suite on in a container) |
| pytest (runner only) | 9.0.3 (2026-04-07, requires-python ≥3.10) | Runs the unittest suite; **required by `test_batchsnap`**, which shells out to `pytest` inside a snapshot | Same version that produced the local 3886 count [VERIFIED: local `pytest --version`; PyPI JSON]. Test-only tooling, never shipped (Phase 61 D-10 split) |
| zsh (apt) | Ubuntu 24.04 package (5.9) | `test_scope_args.TestShellParity` executes `/bin/zsh` unguarded (27 errors without it) | Reproduced in container [VERIFIED] |
| python3 stdlib | `ast`, `sys.stdlib_module_names`, `hashlib`, `json` | Stdlib-only scan, fingerprints, counting rule, cost reader | No new runtime dependency |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `footprint.py --rev v2.14.1 --json` | Declared per-mode-path bytes/words/proxy tokens | BASE-02 declared numbers |
| `replay.py baseline / diff / candidate / check-manifest` | Archived replay output | BASE-03 replay baseline |
| `tracecheck.events(path, subagent_dir)` + `successful_reads(evts, main_only=True)` | Observed loaded-file traces from a recorded session | BASE-02 observed traces |
| `gh run list / gh run view --json conclusion,url,headSha` | Recording the red and green run links | CI-02 evidence |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pytest` runner in CI | `python3 -m unittest discover` | Avoids installing anything, but `test_batchsnap` needs pytest anyway, and unittest has no `--deselect`. Use pytest. |
| Dedicated stdlib scan | Run the `TestImportSet` classes with `-k TestImportSet` | Only 23 of 33 production modules have an import-set pin. A whole-tree scan covers all shipped `.py` (Phase 61 G8 precedent). Run the scan as the named CI step; the `TestImportSet` classes still run inside the suite. |
| Python 3.14 via setup-python | Runner's system 3.12.3 | 3.12 ran the suite in a container with identical failure classes. Choose 3.14 for parity with the recorded baseline. |
| macOS runner | — | Forbidden by D-17, and it would still fail the 3 Phase-43 transcript tests. |

**Installation (CI only, test tooling):**
```bash
sudo apt-get update -q && sudo apt-get install -y -q zsh
python -m pip install pytest==9.0.3
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| pytest 9.0.3 | PyPI | 9.0.3 released 2026-04-07; project >15 yrs | very high (core Python tool) | github.com/pytest-dev/pytest | [OK] | Approved (CI test runner only; already used locally) |
| zsh | Ubuntu apt | distro package | — | Ubuntu archive | n/a (apt) | Approved (system shell for an existing test) |
| actions/checkout, actions/setup-python | GitHub Actions | official `actions/` org | — | github.com/actions/* | n/a | Approved, pinned by full commit SHA |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Key Repo Findings (verified this session)

### Suite baseline at v2.14.1 (macOS, owner machine)
- `pytest -q plugins/vibe-check/scripts` gives **3886 passed, 5060 subtests passed in 195.67 s**, 0 skipped.
- `python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'` gives **Ran 3886 tests … OK**, 0 skipped (204 s).
- `git rev-parse v2.14.1:plugins` = `HEAD:plugins` = `90e0697363ee5c09bb7942a963cf670e16717c4a`, so the plugin tree is already byte-identical. The D-16 check is a one-line tree-hash comparison.
- `origin/main` is `eb790e4`, one `.planning/`-only commit past the tag, with the same plugin tree.

### Linux reproduction (ubuntu:24.04 container, arm64, non-root, zsh + node 18 + pytest 9.2.0, at `dd8e4ab`)

| Failure group | Count | Cause | Workflow-only fix? |
|---|---|---|---|
| `test_scope_args.TestShellParity.test_bash_equals_zsh` | 27 errors | `/bin/zsh` absent (only some classes guard on it) | Yes: install zsh |
| `test_batchsnap.*` (Completeness, Drop, NeverEcho, SnapshotImmutable, TwoRoots), `test_fixcheck.TestRunnerLost.test_u4_unreadable_target`, root-permission skips | ~23 | No `pytest` in the interpreter; running as root (chmod-based tests) | Yes: install pytest; GitHub runners run as non-root `runner` |
| `test_replay.TestCensus`, `TestReconstruction.test_transcript_recovery…`, `TestGuardrail.test_baseline_report` | 3 | Expect 12 gitignored Phase-40 transcripts in a primary checkout | Yes: run from a **linked worktree** (`IN_LINKED_WORKTREE` → expects 0) |
| `test_replay.TestPhase53SameLineRegressionCases` (`test_a2_pair…`, `test_off_line_credit_mutation_trips`, `test_pre_same_line_scorer_gave_critical_100`) | 3 tests | Read gitignored **Phase-43** transcripts; no linked-worktree guard. They also fail in a fresh macOS clone. | **No** |
| `test_footprint.TestWordCountLocaleDrift` (`test_c_locale_wc…`, `test_utf8_locale_wc…`) | 2 tests | Assert BSD `wc -w` counts (27146/27148); GNU wc 9.4 under `LC_ALL=C` gives 26365 | **No** |

After installing zsh and pytest, running as non-root and using a linked worktree, the result is **9 failed lines = 5 distinct tests (with subtests), 3883 passed, 2 skipped**. Without the linked worktree it is 12 failed, which adds the 3 replay tests.

Skips visible on Linux: the `test_codex_collect` executable tests skip when `node` is absent (node is on the GitHub image), `lanearchive` skips with "no sandbox temp root", and `test_transcript_recovery…` is an existing `skipIf(IN_LINKED_WORKTREE)`. The CI record must list each skip and its stated reason. A skip count that differs from the Mac's 0 is disclosed, not hidden.

### footprint.py "exit 2" resolved
- `footprint.py --rev v2.14.1` and `footprint.py` (worktree) both **exit 0** with the CONTEXT numbers: review-plain 192,057 bytes / 13 files; deep-plain 268,997 / 19; finalize 136,114 / 7; fix-loop 255,070 / 14; plus review-all 284,926 / 20 and deep-all 361,866 / 26.
- `run()` returns 2 only from `_parse` (unknown argument or `--rev` with no value), and that path prints usage and **no table**. A run that printed the table cannot have exited 2 from footprint itself. Record it as "did not reproduce; the only exit-2 path is a usage error" and use the output.
- `footprint.py` measures the **declared orchestrator prose only**. It excludes `templates/*.md` that phases read, agent prompts loaded by subagents, and anything the slash-command expansion adds.

### Observed vs declared traces (2.14.x sessions on this machine)

| Path | Recorded 2.14.x session | Observed successful plugin Reads (main session) | Declared (`MODE_PATHS`) differences |
|---|---|---|---|
| Finalize | `~/.claude/projects/-Users-julianamacbook--b3-smoke61-1793397516/b1bb3036…` (2.14.0 candidate `0d2be77`, `/vibe-check:review --finalize`) | 00-contract, 01-bootstrap, 00-scope, 05-state, 06-config, 90-finalize, **templates/review-md-schema.md** | Observed adds review-md-schema.md (5,035 B). `commands/review.md` arrives by command expansion, not a Read. Note: `00-scope.md` content differs between 2.14.0 and 2.14.1; the file set is the same. |
| Plain review | smoke61 `5caa5cec`, `15a3be6d` (2.14.0 cand.); smoke2141 `b0294925`, `6a70827e` (2.14.1) | b0294925: …07-first-run, 10-triage, 20-dispatch, 30-collect-score, 40-render, **templates/output-format.md**, 45-persist, 50-fix-loop | Observed adds output-format.md (14,226 B); 15-intent skipped (non-GSD); 50-fix-loop read (fix loop entered) |
| Deep review | **none at 2.14.x** | — | Record as "declared, not observed" (D-09) |

Tool-call counts in the recorded 2.14.0 Finalize session: **Bash 12, Write 4, Read 9**. This is the observed counterpart to the static counting rule.

### Replay determinism
- `replay.py baseline --out X` run twice gives identical bytes within the same second.
- The headers carry `- HEAD: <sha>` and `- generated (UTC): <ts>` (`diff` uses `- head:` and `- generated:`). Those lines change with every commit and every run, so **fingerprint the report with those lines removed** and record the stripped-line rule next to the hash.
- `replay.py diff --base rev:v2.14.1 --scorer rev:v2.14.1` gives `runs compared: 170, runs differing: 0`. `census`: `scoreable: 66`, `transcripts: 12` (primary checkout).
- Replay output also depends on whether the gitignored transcripts are present (the "Transcript coverage (disclosed)" section). **Capture the replay baseline in the owner's primary checkout and record `transcripts: 12` with it.** A CI-side comparison would see 0.

## Architecture Patterns

### System Architecture Diagram

```
                ┌───────────────────────── local, owner machine (no network, no model) ─────────────────────────┐
 v2.14.1 tag ──►│ pinned tree (worktree/`--rev`) ─► footprint.py ─► declared bytes per path ─┐                 │
                │                                 ─► counting-rule script ─► step counts ────┤                 │
                │                                 ─► replay.py baseline/diff ─► strip HEAD/ts ─► sha256 ──────┤
                │                                 ─► full suite (pytest) ─► count/pass ──────┤                 │
                │                                 ─► Finalize capture (5 situations, fresh   │                 │
                │                                     bash, fixture state) ─► normalize ─► sha256            │
 ~/.claude/     │ recorded 2.14.x sessions ─► tracecheck reads ─► observed traces (labelled) ─┤                 │
 projects/      │                          ─► usage reader (dedupe by message.id, lane via   │                 │
                │                             meta.json) ─► field table: measured/estimated/missing ─► 62-COST-NOTE.md
                └──────────────────────────────────────────────────────────────────────────────┼─────────────────┘
                                                                                               ▼
                                                          docs/design/lean-v2.15/ (committed, public, no transcript text)
 git push (any branch) / PR→main
        │
        ▼
 GitHub Actions ubuntu-24.04 ─► checkout (full history) ─► setup-python 3.14 ─► apt zsh + pip pytest
        ─► stdlib-only scan (exit≠0 on any third-party import) ─► linked worktree ─► pytest suite (−5 named, owner-approved)
        ─► + new tool tests ─► green/red ─► run URL recorded in phase record
```

### Recommended Project Structure
```
.github/
├── workflows/offline-suite.yml       # the one workflow (CI-01)
└── scripts/
    ├── stdlib_only.py                # whole-tree import scan; exit 1 on any non-stdlib, non-sibling import
    └── test_stdlib_only.py           # passes on the real tree; mutant (temp module importing a fake third-party) trips it
docs/design/lean-v2.15/
├── BASELINE-v2.14.1.md               # plain-terms summary: suite result, replay, 5 situations, bytes, traces, step counts
├── baseline/                         # machine-readable records + fingerprints (json, *.sha256)
│   ├── suite-v2.14.1.json
│   ├── replay-baseline-v2.14.1.md (+ .sha256 over normalized body)
│   ├── finalize-situations-v2.14.1.json (+ .sha256)
│   ├── footprint-v2.14.1.json
│   ├── traces-v2.14.1.json            # each path labelled observed / declared-not-observed
│   └── steps-v2.14.1.json             # counting-rule output
├── CRITERION.md                      # D-01..D-07 written down + counting rule (D-05) + comparison workload
└── tools/                            # stdlib scripts + their mutant tests (freeze-v2.12/tools precedent)
.planning/phases/62-…/62-COST-NOTE.md # go/no-go (BASE-01), field names and aggregates only
```
Keep the new evidence out of `docs/design/b3-ground-truth/` and `docs/design/reachability-dev/`. `replay.py` scans those roots, and `test_replay` pins their census, so new files there would change the archived-replay result.

### Pattern 1: Stdlib-only scan as its own CI step (lock + mutant)
**What:** An AST scan of every non-test `.py` under `plugins/vibe-check/`. It accepts `sys.stdlib_module_names` plus sibling module names, and any other top-level import exits 1. It extends the Phase 61 G8 snippet into a script with an exit code.
**When:** A named CI step before the suite. Its own test runs the real tree (expects 0) and a temp tree with a planted `import requests` (expects 1). That planted import is the "mutant that trips it".

### Pattern 2: Five Finalize situations captured through the existing fresh-shell mechanics
**What:** Reuse what `test_finalize_card.TestFinalizeFreshShellWalk` already does at 2.14.1. Extract each fence from `90-finalize.md`, run it in its own `bash -s` with only `PATH`, `VC_ROOT`, `TMPDIR` and `STATE_FILE`, simulate Write by writing JSON to the printed path, and collect each step's exit code, stdout, stderr and the files written or archived. Existing tests already cover each D-07 situation:

| D-07 situation | Existing 2.14.1 test that walks it |
|---|---|
| 1 Clean close writes report | `TestFinalizeFreshShellWalk.test_walk_reaches_counts_gate_report` (gate `{"action": "write"}`, decisions-report entries, closed stamp) |
| 2 Open decisions → card first | `…test_card_route_records_then_writes` (SIX_ROW fixture → card → parse → record-decisions → recount → `write`) |
| 3 One automatic rebuild | `…test_retry_mints_new_blobfile_after_missing_path`, `…test_retry_mints_new_gatefile_after_gate_input_failure` |
| 4 Refused/failed close writes nothing | `…test_malformed_gatefile_shows_only_stop_sentence`; `test_finalize_archive_prose.TestArchiveFenceRuns.test_unarchivable_*_stops`; gate `{"action":"refuse","reason":"malformed gate input"}` |
| 5 Restart in a fresh shell | `…test_post_decision_rerun_decides_on_a_fresh_gatefile`, `…test_post_decision_recount_refingerprints_head` |

**Record:** the gate decision JSON, the one stop sentence (or none), the `batch_card.py decisions-report` JSON (this is the deterministic "report text"; REVIEW.md prose is written by the model), the archive moves made, and the `review-closed` result. Before hashing, normalize the `mktemp` paths (`vc.XXXXXX`) and any epoch or time stamps to placeholders.

**Phase 63 design constraint:** Phase 63 replaces these fences with helpers. The capture tool must therefore define each situation by its **inputs** (fixture state, HEAD/worktree fixture repo, owner answers) and its **observable outputs**, with a thin per-version driver. Do not build a harness that only works by parsing 2.14.1's fence text.

### Pattern 3: Traces labelled at the source
Run `tracecheck.events()` + `successful_reads(main_only=True)` on each recorded 2.14.x session. Map absolute paths to plugin-relative ones using the session's own plugin root: the snapshot path in the 61 smoke record, or `…/cache/thejuran/vibe-check/<ver>/`. Label every path record `observed (version, session id prefix)` or `declared, not observed`. Store observed and declared lists side by side and never merge them.

### Pattern 4: Counting rule as a script (D-05)
A rule written as prose would let Phase 63 count differently. Prototype structural counts on the 2.14.1 Finalize path files (`MODE_PATHS["finalize"]`):

| File | bash fences | printed path literals (`printf 'NAME=%s'`) | literal uses in other fences (`"$NAME"`, `"$NAME.ext"`) |
|---|---|---|---|
| commands/review.md | 1 | 0 | 0 |
| shared/01-bootstrap.md | 1 | 0 | 0 |
| review/00-scope.md | 10 | 0 | 0 |
| review/05-state.md | 7 | 0 | 0 |
| review/06-config.md | 5 | 0 | 0 |
| shared/90-finalize.md | 18 | 11 (BLOBFILE, GATEFILE, ROWSFILE, CARDROWSFILE, ANSWERFILE, PARSEFILE, REFSFILE, RESOLVEFILE, SUGGESTFILE, DECFILE, SUBSETFILE) | 27 |

These figures are a research prototype, not the baseline. The plan's script defines the official ones. Recommended rule:

> model-run mechanical steps = (bash fences the model runs) + (distinct printed literals it must carry) + (sites where a carried literal is pasted into a later fence) + (Write-tool file writes the prose instructs)

Count the Write-tool term structurally if possible. A wording grep is fragile: 7 "Write tool/Use Write" mentions in 90-finalize.md. Report the count **statically over the path files** (an upper bound) and also **per D-07 situation** where the walk makes it countable. Each figure needs a mutant test: add one fence or one printed literal to a temp copy and the count must rise by exactly 1.

### Pattern 5: Cost reader (D-10/D-11/D-13)
A stdlib script run with `python3 -I`. Input is a fixed list of session files named in the plan. Output is field names, presence counts and aggregates per session and per lane. It never prints message content. Rules:

- Dedupe by `message.id` (or `requestId`).
- Map lanes from `subagents/*.meta.json` `agentType`.
- Label every field measured, estimated or missing.
- Price nothing.
- Commit the script's test (built from synthetic fixtures), never a real log.

### Pattern 6: Red/green proof (D-15/D-16)
- **Red.** Create `ci-red-proof` from the phase branch, make one commit that flips one assertion in one test, and push. Record `gh run list --branch ci-red-proof --json databaseId,conclusion,url,headSha`. No PR. Delete the remote and local branch.
- **Green before merge.** Record the phase-branch run, plus `git rev-parse v2.14.1:plugins` = `HEAD:plugins`.
- **Green after merge.** Record `main`'s first run. Mark the phase complete only after it is green.

### Anti-Patterns to Avoid
- **Shallow checkout:** the default `fetch-depth: 1` breaks `replay.load_scorer("blob:…")`, the `rev:` specs, `footprint --rev 7a386ed` and the `test_score` blob pins.
- **`on: push: branches: [main]`:** the red-proof branch would never run. Use `branches: ['**']` for push and `branches: [main]` for pull_request.
- **Fingerprinting raw replay reports:** they carry the HEAD and a timestamp.
- **Treating `MODE_PATHS` as the loaded set:** it is the declared set, and the observed set is larger.
- **Summing `usage` over every assistant record:** each message is logged once per content block, so that doubles the totals.
- **Putting the baseline tools or the stdlib check under `plugins/vibe-check/`:** that breaks the D-16 tree identity.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Footprint bytes | New byte counter | `footprint.py --rev v2.14.1 --json` | Already locale-independent and git-pinned (F11) |
| Replay baseline | Re-scoring code | `replay.py baseline/diff/candidate/check-manifest` | Frozen since v2.13 (G9), with its own 64 tests |
| Read-event extraction | JSONL parser for tool_use/tool_result pairing | `tracecheck.events` / `successful_reads` | Handles failed reads, truncation and subagent meta linking |
| Fresh-shell Finalize execution | New prose interpreter | Mechanics of `TestFinalizeFreshShellWalk` (`_run_fresh`, `_literal`, fence extractors) | Already proven at 2.14.1 |
| Git fixture repos | Ad-hoc `git init` | `gitfixture.make_repo` / `helper_env` | Isolates global git config (gpgsign, hooks) |
| Stdlib module list | Hard-coded list | `sys.stdlib_module_names` (3.10+) | Version-correct |

**Key insight:** this phase is assembly and pinning. All the measuring code already exists and is tested. New code is limited to thin, tested drivers.

## Common Pitfalls

### Pitfall 1: Shallow clone in CI
**What goes wrong:** the replay, score and footprint tests fail on `git cat-file`/`git show` of historical objects. **Avoid:** `fetch-depth: 0`. **Warning sign:** `ReplayError: git cat-file failed`.

### Pitfall 2: Private-data tests on CI
**What goes wrong:** the 3 + 3 transcript tests fail on any checkout without the owner's gitignored transcripts. A fresh macOS clone fails them too. **Avoid:** run from a linked worktree (fixes 3), and take the remaining 3 Phase-43 tests to the owner (Open Question 1). **Warning sign:** `0 != 12`, or `('architecture', 233) not found in []`.

### Pitfall 3: BSD-vs-GNU `wc`
**What goes wrong:** `TestWordCountLocaleDrift` encodes macOS `wc`. **Avoid:** nothing in workflow setup can fix it, so it goes into the owner decision. Never "fix" it by changing `footprint.py`.

### Pitfall 4: Root or no-pytest containers mislead local reproduction
**What goes wrong:** running the suite as root in Docker produces about 20 false failures (chmod-based immutability tests, "root ignores directory permissions" skips). **Avoid:** reproduce as a non-root user. GitHub runners run as `runner`.

### Pitfall 5: Workflow-file push rejected
**What goes wrong:** git rejects a push touching `.github/workflows/` unless the credential has `workflow` scope. The `gh` token has it ('gist', 'read:org', 'repo', 'workflow'), but git uses `osxkeychain`, which may hold a different token. **Avoid:** if the push is refused, run `gh auth setup-git`. Memory says executors refuse relayed push approval, so push from the main session.

### Pitfall 6: Double-counted usage
Covered in Pattern 5: dedupe by `message.id`. Verified on all 5 recorded 2.14.x sessions (for example 104 records → 56 ids), with 0 ids whose usage differs between duplicates.

### Pitfall 7: No independent run total (D-11 condition 3)
**What goes wrong:** async Agent tool results carry `agentId/status/outputFile/resolvedModel` but no token or duration totals. The "run total" can only be the sum of the parts, and checking lane sums against it would be circular. **Avoid:** the note must say so plainly and label any run total "estimated (sum of parts)" or treat condition (3) as unmet. Do not invent a reconciliation.

### Pitfall 8: Elapsed time includes the human
**What goes wrong:** first-to-last timestamps include time the owner spent answering cards. **Avoid:** label it "wall-clock including owner wait". It is not a performance measure.

### Pitfall 9: Older or partial archives as stand-ins
**What goes wrong:** the b3 archives (v2.10/2.11) are main-session copies with no `subagents/`. The freeze-v2.12 SDK harness transcripts have **no usage fields at all**. Neither can supply per-lane usage for 2.14.x, and D-09 forbids older-version traces. **Avoid:** count them in the note as "present but not attributable", not as evidence.

### Pitfall 10: Replay-baseline environment drift
**What goes wrong:** a baseline captured where transcripts are present (`transcripts: 12`) differs from one captured in CI (0). **Avoid:** capture locally in the primary checkout and record the environment fact with the hash.

## Code Examples

### The workflow (recommended shape; deselect list subject to owner approval)
```yaml
# .github/workflows/offline-suite.yml
name: offline-suite
on:
  push:
    branches: ['**']        # fires on the throwaway red-proof branch too (D-15)
  pull_request:
    branches: [main]
permissions:
  contents: read            # no secrets, no write token
jobs:
  offline:
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
        with:
          fetch-depth: 0              # blob/rev pins need full history
          persist-credentials: false
      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0
        with:
          python-version: '3.14'
      - name: Test-only tools (zsh for shell-parity tests, pytest runner)
        run: |
          sudo apt-get update -q
          sudo apt-get install -y -q zsh
          python -m pip install pytest==9.0.3
      - name: Stdlib-only check
        run: python3 -I .github/scripts/stdlib_only.py plugins/vibe-check
      - name: Offline suite (linked worktree — no private transcripts, by construction)
        run: |
          git worktree add --detach "$RUNNER_TEMP/wt" HEAD
          cd "$RUNNER_TEMP/wt"
          pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools \
            --deselect plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_a2_pair_sits_on_adjacent_lines_of_one_statement \
            --deselect plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_off_line_credit_mutation_trips \
            --deselect plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_pre_same_line_scorer_gave_critical_100 \
            --deselect plugins/vibe-check/scripts/test_footprint.py::TestWordCountLocaleDrift::test_c_locale_wc_matches_the_recorded_number \
            --deselect plugins/vibe-check/scripts/test_footprint.py::TestWordCountLocaleDrift::test_utf8_locale_wc_is_the_plans_figure_and_differs_by_two \
            -rs 2>&1 | tee "$RUNNER_TEMP/suite.log"
          test "${PIPESTATUS[0]}" -eq 0
          grep -q ' 5 deselected' "$RUNNER_TEMP/suite.log" || { echo 'DESELECT LIST DRIFTED — STOPPING'; exit 1; }
```
(GitHub's default `bash` shell runs with `-e -o pipefail`, so the `PIPESTATUS` check is belt-and-braces. Keep it: the `tee` must not hide a red suite.)

### Stdlib-only scan (from Phase 61 G8, turned into a gate)
```python
# .github/scripts/stdlib_only.py — python3 -I stdlib_only.py <plugin root>; exit 0 clean / 1 violation / 2 usage
import ast, glob, os, sys
def scan(root):
    std = set(sys.stdlib_module_names)
    files = [f for f in glob.glob(os.path.join(root, "**", "*.py"), recursive=True)
             if not os.path.basename(f).startswith("test_")]
    local = {os.path.basename(f)[:-3] for f in files}
    bad = {}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for n in ast.walk(tree):
            mods = ([a.name.split(".")[0] for a in n.names] if isinstance(n, ast.Import)
                    else [n.module.split(".")[0]] if isinstance(n, ast.ImportFrom) and not n.level and n.module else [])
            for m in mods:
                if m not in std and m not in local:
                    bad.setdefault(os.path.relpath(f, root), set()).add(m)
    return files, bad
```
Decide in the plan whether `test_*.py` files are also scanned (they import only stdlib plus siblings today), and whether `gitfixture.py` counts as shipped. It is non-test-named and ships in the tree.

### Replay fingerprint over the normalized body
```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review/plugins/vibe-check/scripts
OUT=/Users/julianamacbook/turingmind-code-review/docs/design/lean-v2.15/baseline/replay-baseline-v2.14.1.md
python3 replay.py baseline --out "$OUT"
grep -vE '^- (HEAD|head|generated( \(UTC\))?): ' "$OUT" | shasum -a 256 | cut -d' ' -f1 > "$OUT.sha256"
BASH
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `actions/checkout@v4` era tags | v7.0.1 (Jul 2026); setup-python v7.1.0 (Oct 2026) | 2026 | Pin by SHA with a version comment |
| `ubuntu-latest` = 22.04 | `ubuntu-latest` = 24.04; 26.04 images now exist | — | Pin `ubuntu-24.04` explicitly |
| Usage priced from logs (54-BUDGET, v2.12) | This phase: labels only, no dollars (D-11) | 2026-11-13 | The note never prints a price |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `actions/setup-python` v7.1.0 provides Python 3.14 on ubuntu-24.04 | Standard Stack | Setup step fails. Fallback: drop setup-python and use system 3.12.3 (container-verified) |
| A2 | Real x64 GitHub runner reproduces the arm64 container result (same 5 irreducible failures, no new ones) | Linux reproduction | More environment failures to record per D-17. The first phase-branch run is the check. |
| A3 | Recorded smoke sessions under `~/.claude/projects/-Users-julianamacbook--b3-smoke61-*` and `--b3-smoke2141-*` count as "this project's" session logs (D-10) and as "recorded 2.14.x sessions" (D-09) | Cost note / traces | If the owner reads D-10 as this repo's slug only: that slug holds no `/vibe-check:*` command invocations (0 `<command-name>/vibe-check:` matches across 40 sessions), so the note becomes an immediate no-go and every trace becomes declared-only |
| A4 | `commands/review.md` reaches the model by slash-command expansion, so its absence from Read events is expected | Traces | Trace note slightly wrong; label it "loaded by command expansion (not a Read)" |
| A5 | The `usage.iterations` and `cache_creation` sub-object semantics are not documented here | Cost note | Label those fields "present, meaning unverified". Do not use them. |
| A6 | `git push` of a workflow file succeeds with the keychain credential | Pitfall 5 | Run `gh auth setup-git`, then retry |

## Open Questions

1. **The 5 tests that cannot pass on GitHub Linux (blocks CI-02).**
   - What we know: 3 need the owner's private Phase-43 transcripts and 2 assert the Mac's `wc` behaviour. Workflow setup cannot fix either group. Editing the tests changes files inside `plugins/vibe-check/`, which breaks D-16, and D-17 forbids skipping.
   - Options for the owner, in plain terms:
     - **(A) Recommended:** CI leaves out exactly these 5 checks by name, a guard step fails if the list ever changes, and they still run on the Mac at every release gate. The plugin stays untouched. The cost is that CI does not cover those 5 checks, which test archived private recordings and a Mac tool quirk rather than plugin behaviour on Linux.
     - **(B)** Edit the 5 tests so they behave differently without the private data or on GNU `wc`. CI then runs "everything", but plugin files change and the 2.14.1 baseline is no longer untouched.
     - **(C)** Stop the CI half of the phase.
   - Recommendation: the plan puts a `checkpoint:decision` on this before the workflow is final. The baseline plans proceed in parallel.
2. **Which sessions form the D-13 sample.** Recommendation: the plan names them up front:
   - plain review: the 4 smoke sessions;
   - Finalize: smoke61 `b1bb3036` (the only one);
   - deep review: the most recent deep-review transcripts in the repo archives (v2.11 phase49 and reachability-dev, at older versions, main-session only), labelled as such;
   - plus this repo's slug for completeness.
3. **Does `gitfixture.py` count as shipped for the stdlib check?** It is test support that ships in the plugin directory. Recommendation: scan it. It is stdlib-only today.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 (local) | All tools | ✓ | 3.14.5 | — |
| pytest (local, bare command only) | Suite runs | ✓ | 9.0.3 | `python3 -m unittest discover` (count identical: 3886) |
| git | Replay, footprint `--rev`, worktrees | ✓ | system | — |
| zsh / node / timeout (local) | Shell-parity, codex-collect tests | ✓ | /bin/zsh, node (Homebrew), coreutils timeout | — |
| gh CLI | Run links, branch delete, PR | ✓ | 2.86.0, scopes include `workflow` | — |
| GitHub Actions on `thejuran/vibe-check` | CI-01/02 | ✓ | enabled, `allowed_actions: all`, default token `read`; `main` not protected | — |
| Docker (local) | Optional Linux pre-check | ✓ | 29.9.3 (arm64) | Skip; the real runner is authoritative |
| zsh on GitHub runner | TestShellParity | ✗ | — | `apt-get install zsh` (in workflow) |
| pytest on GitHub runner | Suite + batchsnap | ✗ | — | `pip install pytest==9.0.3` |
| Recorded 2.14.x deep-review session | BASE-02 observed deep trace | ✗ | — | "declared, not observed" (D-09) |

**Missing dependencies with no fallback:** none that block. The deep-review trace gap is handled by D-09.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | stdlib `unittest.TestCase`, run with pytest 9.0.3 |
| Config file | none (repo-wide). Do not add one: it would change collection for the existing suite. |
| Quick run command | `cd <dir> && pytest -q -p no:cacheprovider test_<tool>.py` (new tools under `docs/design/lean-v2.15/tools/` and `.github/scripts/`) |
| Full suite command | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` (~200 s on the Mac) |

Use bare `pytest`, never `python3 -m pytest` (that fails locally). The test-verify allowlist rejects `python3 -m unittest`. Wrap multi-line shell in `bash -s <<'BASH'`.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CI-01 | Stdlib scan passes on the real tree and trips on a planted third-party import | unit + mutant | `pytest -q .github/scripts/test_stdlib_only.py` | ❌ Wave 0 |
| CI-01 | Workflow triggers: push `**`, PR→main; `permissions: contents: read`; no `secrets.`; SHA-pinned actions; `fetch-depth: 0` | static check of the YAML text (stdlib, no YAML lib: line/regex asserts) + mutant | `pytest -q .github/scripts/test_workflow_shape.py` | ❌ Wave 0 |
| CI-02 | Red on a broken test; green on the baseline and on `main` | live CI (free, no model) | `gh run list --branch ci-red-proof …` / `--branch main` | manual-record |
| BASE-02 | Footprint and trace records match `footprint.py --rev v2.14.1 --json` and label every path | unit (reads the committed JSON) + mutant (relabel or alter a byte count) | `pytest -q docs/design/lean-v2.15/tools/test_baseline_records.py` | ❌ Wave 0 |
| BASE-03 | Committed replay and Finalize-situation fingerprints re-derive from v2.14.1 | unit (recompute the normalized sha256) + mutant | same file | ❌ Wave 0 |
| BASE-04 | Counting rule script gives the committed 2.14.1 numbers; a temp prose copy with +1 fence / +1 literal gives +1 | unit + mutant | `pytest -q docs/design/lean-v2.15/tools/test_step_count.py` | ❌ Wave 0 |
| BASE-01 | Cost reader dedupes by message id, maps lanes by meta.json, never emits content strings | unit on **synthetic** fixtures + mutant (disable dedupe → 2× totals) | `pytest -q docs/design/lean-v2.15/tools/test_usage_fields.py` (or under the phase dir if kept private) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** the quick command for the touched tool.
- **Per wave merge:** the full suite command.
- **Phase gate:** full suite green locally, phase-branch CI green, red-proof run recorded, `main` run green, before `/bm:verify-work`.

### Wave 0 Gaps
- [ ] `.github/scripts/test_stdlib_only.py` covers CI-01 (stdlib lock + mutant)
- [ ] `.github/scripts/test_workflow_shape.py` covers CI-01 (trigger/permission/pin locks + mutants)
- [ ] `docs/design/lean-v2.15/tools/test_*.py` covers BASE-02/03/04 (fingerprint and counting-rule locks + mutants)
- [ ] Synthetic JSONL fixtures for the cost reader. Never real logs.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no secrets, token `contents: read`) |
| V3 Session Management | no | — |
| V4 Access Control | yes (CI token scope) | `permissions: contents: read`; `persist-credentials: false`; `pull_request` (never `pull_request_target`) |
| V5 Input Validation | yes | No `${{ github.event.* }}` in `run:`; the cost reader treats JSONL as data and prints names and counts only |
| V6 Cryptography | minimal | `hashlib.sha256` for fingerprints. Never hand-roll. |
| V8 Data Protection | yes | D-10: no transcript text, file contents, private instructions or account details in the repo or the note. Logs are never copied. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Compromised or moved action tag | Tampering | Pin `uses:` to full commit SHAs (repo setting does not require it; do it anyway) |
| Script injection via PR title or branch name in `run:` | Tampering / Elevation | Never interpolate event fields into shell |
| Fork PR exfiltrating a token | Info disclosure | `pull_request` trigger + read-only token + no secrets |
| Private transcript text leaking into the public repo via the note or fixtures | Info disclosure | Reader emits only field names and aggregates; synthetic fixtures; review the diff for any quoted content before commit |
| Supply chain via pip | Tampering | Pin `pytest==9.0.3` (test-only). The shipped runtime stays stdlib-only, enforced by the scan. |

## Sources

### Primary (HIGH confidence, run in this session)
- Local suite runs at `v2.14.1` (pytest and unittest); `footprint.py` reruns; `replay.py baseline/diff/census`.
- `ubuntu:24.04` and `python:3.12` container runs of a fresh clone at `dd8e4ab` (root and non-root; primary clone vs linked worktree).
- Repo code: `footprint.py`, `replay.py`, `tracecheck.py`, `gitfixture.py`, `test_replay.py`, `test_footprint.py`, `test_scope_args.py`, `test_codex_collect.py`, `test_finalize_card.py`, `phases/shared/90-finalize.md`, `.gitignore`.
- `gh api`: `repos/thejuran/vibe-check` (public, Actions enabled, `allowed_actions: all`, default workflow token `read`, `main` unprotected); `actions/checkout` and `actions/setup-python` latest releases and tag SHAs; `actions/runner-images` README and Ubuntu2404-Readme.
- PyPI JSON for pytest 9.0.3/9.2.0; slopcheck `[OK]` for pytest.
- Local session logs: field names and counts only (read-only stdlib scripts under the session scratchpad; nothing copied).

### Secondary (MEDIUM)
- Phase 61 RESEARCH and RELEASE-RECORD (G8 stdlib scan, replay gate commands); 54-BUDGET (dedupe precedent "counted once per message").

### Tertiary (LOW)
- None relied on.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. Versions and SHAs come from the GitHub API, and the pytest version is the local one.
- Architecture: HIGH. Every reused tool was exercised.
- Linux behaviour: MEDIUM. Container on arm64, not a real runner (A2).
- Cost-note feasibility: MEDIUM. The fields were verified on 5 sessions; the formal verdict belongs to the D-13 plan.

**Research date:** 2026-11-13
**Valid until:** 2026-12-13 (action versions and runner image move monthly; the repo facts hold while the plugin tree stays at `90e0697`)
