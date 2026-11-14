# Phase 63: Finalize extraction and cross-call variable check - Research

**Researched:** 2026-11-14
**Domain:** Moving model-run shell steps into a stdlib Python helper (Finalize gate inputs), offline behaviour equivalence, and a static lint over bash fences in Markdown instruction files
**Confidence:** HIGH for the codebase facts (all read or run in this session); MEDIUM for the projected counts (computed with the real counting rule on a proposed design, not on a written candidate)

> **Superseded in one respect by D-18 (owner, 2026-11-14).** Wherever this file says the helper's stderr is sent to `<BLOBFILE>.err` (Project Constraints, the architecture diagram, Pattern 2, Pitfall 5 "How to avoid", "The candidate fence", Security Domain V7), read instead: the fence does not redirect the helper's stderr. On a counting-stage refusal the helper writes exactly the one line the 2.14.1 counting command printed, so the owner sees the same line above the same sentence; on every other exit it writes nothing. No traceback and no path, hash or title is ever written. Plans 63-02 and 63-06 carry the exact contract.

## Summary

Everything this phase needs already exists except two things: one new helper module that does the HEAD-fingerprint git calls, the counts, the seven-key flags and the gate in a single call, and one new whole-tree test that finds cross-call shell variables. `carry_state.finalize_counts`, `finalize_gate.run`, `batch_card.decisions_report`, `guard.contained` and the `PATH_RE` pattern are all importable library functions today [VERIFIED: codebase read]. The 2.14.1 gate-input part of `90-finalize.md` is four bash blocks, two Write-tool writes and three hand-copied values (9 counted steps). It also includes up to three git calls and a guard call per fix-verdict file, which the counting rule does not count because they are written in prose rather than in fences. Folding all of it into one fence that mints and prints `BLOBFILE=` and then calls the helper gives 1 counted step. Also folding the `decisions-report` fence into the helper's `write` result (D-02) takes the Finalize path from **92 to 83 steps**. About 5–7 KB of the 10.9 KB gate-input section can go, and D-12 moves the 3.7 KB "What the helper counts" passage out of loaded prose [VERIFIED: step_count.py run on the current tree, which is byte-identical to `dd8e4ab` for `phases/`].

Proving the same behaviour is the hard part. `finalize_capture.py` drives the five situations by searching for fence text and injecting faults *between* fences: "the printed BLOBFILE is gone", and "the GATEFILE holds `not json`". Once the extraction lands, the GATEFILE no longer exists and the BLOBFILE is written and read inside one process. So the candidate needs its own driver, with an explicit and honest mapping for each fault. One situation (`fresh-shell-restart`) also feeds a fake blob id (`blob-pre-card`) that real git can never produce. Once git runs inside the helper, that situation needs a real git work directory and a real `verified_blob`. That is a named difference in the *prepared inputs*. The outcome fields are not affected, but the owner page (D-14) must say so.

The cross-call check is cheap to build: a probe written in this session over all 27 phase files flags **10 sites in 6 file/variable pairs**, all in three shared files on the Finalize path (`00-scope.md` `PHASE_DIR`; `05-state.md` `STATE_FILE`, `LEGACY_STATE_FILE`; `06-config.md` `CONFIG_REPO_ROOT`, `MIN_CONFIDENCE_FLAG_VAL`, `CODEX_FLAG_VAL`) [VERIFIED: probe run]. Those files count toward the Finalize criterion. If any of them reproduces as a real failure and is fixed under D-08/D-09, the fix can *add* counted steps to the same path whose drop this phase must show. Before the plan commits to a pass/fail reading, it must settle how XVAR fixes are counted (Open Question 1).

**Primary recommendation:** Add `plugins/vibe-check/scripts/finalize_inputs.py`, one call that returns `{action, reason, next, counts, report}`. The fence keeps `mktemp` and `printf 'BLOBFILE=%s\n'`, so the unchanged card still reads the printed literal. Map each helper exit code to an existing stop sentence inside the fence. Add a `HelperWalk` driver to `finalize_capture.py` without touching `SITUATIONS` or the 2.14.1 record. Add `test_cross_call_vars.py` with a by-name, shrink-only exceptions set.

## Architectural Responsibility Map

This is a CLI plugin. The "tiers" are: the model reading Markdown (host), bash fences the model runs, stdlib Python helpers, and on-disk state.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HEAD fingerprints (path validation + 3 git calls per file) | Python helper (new) | — | Mechanical and deterministic. The validation must stay fail-closed and is easier to test in code (D-01, discretion) |
| The three counts and hash lists | Python helper (`carry_state.finalize_counts`, reused) | — | Already the single source of the closure rule |
| Seven-key flags + gate decision | Python helper (`finalize_gate.run`, reused in-process) | Host passes `noninteractive` / `pr_mode` / `range_mode` | The truthiness of `$TURINGMIND_NONINTERACTIVE` and the PR/range resolution are host judgments today; keep them there, passed as explicit required args |
| Report data bundle (counts + owner-decision entries) | Python helper (`batch_card.decisions_report`, reused) | Host writes REVIEW.md | D-02: the model still writes the report from the template |
| Stop sentences, messages, card, AskUserQuestion | Host (prose) | — | D-05: byte-identical owner text stays in the loaded file; the helper never prints owner text |
| `record-decisions` (the only pre-report state write) | Existing fence (unchanged) | — | D-01 and the single-writer rule |
| Archive of prior REVIEW.md / state | Existing fences (unchanged) | — | Order is prior archive → Write → state archive; the Write sits between them, so they cannot fold into one call |
| Cross-call variable check | Test (`test_*.py`, static) | — | A lint over instruction text, run in CI |

## User Constraints (from CONTEXT.md)

<user_constraints>

### Locked Decisions

#### Carried forward (locked — do not re-litigate)
- **Pass rule (Phase 62 D-01/D-02):** the slice passes if bytes loaded or model-run steps on the Finalize path drops and neither grows, with identical behaviour. No percentage target. Nothing is cut to reach a number.
- **Maintenance added (Phase 62 D-03):** new helper code and tests are reported as their own labelled figure; they do not decide pass or fail.
- **No drop (Phase 62 D-04):** default is revert; the owner gets one plain-terms page first and may keep the slice by explicit waiver. No automatic second attempt.
- **Same behaviour (Phase 62 D-07/D-08):** the five recorded Finalize situations (`clean-close`, `card-first`, `one-rebuild`, `refused-close`, `fresh-shell-restart`), the offline suite and the archived replay match 2.14.1 byte for byte; any difference is named and explained or it blocks.
- **Counting (Phase 62 D-05):** the same `step_count.py` rule (rule version 1) and `footprint.py` are used; a change to the script, phrase list or lead-in list must be recorded with the figures it gives on 2.14.1 before and after.
- **Retry rule (Phase 60 D-07/D-08):** one automatic rebuild from the current HEAD, index and working tree, then stop with the plain no-write message; a refusal is never retried automatically; a failed or refused attempt writes no report and archives nothing; inputs from an earlier attempt or session are never reused.
- **Standing rules:** no growth per round (work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow); each change starts by recording current behaviour on current code; every lock lands with a mutant that trips it; shipped scripts stay stdlib-only; `stable_hash` / GOLDEN_DIGEST stay frozen; paid or live runs need a separately approved bounded proposal; byte and step counts are reported separately from tokens or dollars.
- **Branch:** `feat/v2.15-phase-63` from `main`, one PR, deleted locally and on GitHub after merge.

#### How far the extraction reaches
- **D-01:** Only the gate inputs and the gate handoff move into helpers: the HEAD fingerprints, the counts, the seven-key flags and the gate call. The model gets one compact structured result with the gate's action and an explicit next action. The decision card (its rows, suggestion, answer, parse, resolve and decision temp files) and the record-decisions step stay exactly as in 2.14.1.
- **D-02:** REVIEW.md is still written by the model from `templates/review-md-schema.md`. The helper hands it one ready bundle of the data the report fill reads (the counts, including the verified-obsolete hashes, and the owner-decision entries), so the model does not look these up in separate steps. The report's text rules do not change.
- **D-03:** The extraction does not change the files ordinary reviews also load: `phases/review/00-scope.md`, `phases/review/05-state.md`, `phases/review/06-config.md`, `commands/review.md`, `phases/shared/00-contract.md`, `phases/shared/01-bootstrap.md`. Of the 92 baseline steps, 68 are in `90-finalize.md`; the other 24 are out of reach for this slice. Plain and deep review paths stay byte-identical unless D-09 applies.
- **D-04:** Extracting the card's temp-file plumbing is not done here. It is filed at phase close as a backlog item with this phase's step numbers, to be weighed later together with the fix loop's matching card. It is not scheduled and is not added to Phase 64's three candidate families.

#### Failure wording and the retry
- **D-05:** Every stop sentence the owner sees is byte-identical to 2.14.1. No reason clause and no pointer to a detail file is added. The helper's own diagnostics stay out of what the owner reads, as today. Any failure path inside the helper maps to one of the existing sentences.
- **D-06:** Where the helper could catch a bad input that 2.14.1 would have let through, it behaves as 2.14.1 does. Each such gap is recorded with its reproduction and carried to backlog. A gap that reproduces as data loss, a wrong close, silent loss of a qualifying finding or a broken required workflow goes to the owner under the four-class rule before anything changes.
- **D-07:** The Phase 60 retry rule (carried forward above) is kept as behaviour. Whether the one rebuild is the model calling the helper a second time or something the helper does itself is Claude's discretion, provided the `one-rebuild` and `refused-close` outcomes match the baseline and restart works across fresh shell calls (FINX-03).

#### Files the new check flags
- **D-08:** Every place the check flags is first recorded with a fresh-shell reproduction (XVAR-02). A flagged place that reproduces as a real failure under the four-class rule is fixed in this phase. Every other flagged place goes on a named exceptions list that can only shrink, with entries identified by file and variable (not a count), and is carried to backlog. The check fails on any new case. The check is green in CI at phase end.
- **D-09:** A fix for a reproduced failure in a shared file may add bytes to the plain and deep review paths. Each is listed by file, byte count and reproduction, and Phase 65 reports it as named growth, separate from the Finalize saving. Nothing else may grow those paths.
- **D-10:** The check covers every file under `plugins/vibe-check/phases/` (27 files), as the approved scope says. Command and agent files are not covered; that is recorded as a known limit, not added to scope.

#### Proof for removed safeguards
- **D-11:** A removal ledger is kept. Every removed instruction passage and every removed or rewritten test is listed with the helper test that now protects the same rule, or "no longer applies" with the reason. Each replacement is proven by a deliberate break that it catches. A rule with no replacement is not removed. The replacement lands before the removal.
- **D-12:** The explanation of what the helper counts as open and closed (the "What the helper counts" passage in `90-finalize.md`) moves word for word to a design document under `docs/design/` that the model does not load during a review. Rules the model still acts on stay in the loaded file: what to do on each gate result, the recovery guidance, the no-write rule.
- **D-13:** The two weak Phase 62 baseline checks (backlog 999.34 WR-02 and WR-03) stay carried for Phase 65. Phase 63 does not rely on them: it recounts 2.14.1 and the candidate directly from their commits with `step_count.py` and `footprint.py`, and confirms the fingerprints in `docs/design/lean-v2.15/baseline/MANIFEST.json` are unchanged.
- **D-14:** Before the PR merges, pass or fail, the owner gets one plain-terms page: the two counts before and after, "maintenance added", the five situations' match result with every named difference, a summary of the removal ledger, the flagged-files list with which were fixed and which pinned, and any gaps recorded under D-06. The merge waits for the owner's go. On a fail, this page is the Phase 62 D-04 waiver page.
- **D-15 (follows from Phase 62 D-08; not separately asked):** In the five situations, the outcome fields must match the baseline byte for byte: the gate decision, the report text, the stop sentence, the files written, the files archived and whether the state closed. The recorded lists of commands run are expected to change, since fewer model-run commands is the purpose; that change is named as the intended difference, field by field, and nothing else may differ.

### Claude's Discretion
- Helper shape: a new module or additions to `finalize_gate.py` / `carry_state.py`, how many calls, the result's field names, and how temp files are handled. The single-writer state path and `record-decisions` as Finalize's only state write before REVIEW.md must hold.
- Whether the HEAD fingerprint git calls move inside a helper. Today the counting helper never runs git itself and the instructions validate each file first (the `^[A-Za-z0-9._/-]+$` filter, then `guard.py`, before any git call; a failing file is omitted, fail closed). Whatever moves, that validation and the omit-on-any-difference rule must be preserved and tested.
- Whether the archive commands (earlier REVIEW.md before the write, state after the write) fold into a helper call, provided their order, no-clobber behaviour and messages stay identical.
- The check's implementation and location, how it treats names carried forward by the documented bootstrap rule (`$VC_ROOT`, `$GUARD_PY`, `$CONFIG_PY`, `$SCORE_PY`) and reads that span two files, whether a stale exceptions entry fails the check, and whether the three Finalize-only checks in `test_finalize_card.py` are folded into it (under the D-11 ledger).
- How `finalize_capture.py` is adapted to drive the candidate, within the Phase 62 D-05 recording rule.
- Names and locations of the design document (D-12), the removal ledger (D-11) and the result page (D-14); plan count and split.

### Deferred Ideas (OUT OF SCOPE)
- Extract the Finalize card's temp-file plumbing, together with the fix loop's matching card: backlog item filed at phase close with this phase's numbers, not scheduled (D-04).
- A helper-generated REVIEW.md (identical output for the same state): not chosen for this phase; reopen as its own proposal.
- A short reason, or a pointer to the detail file, after a stop sentence: not chosen; would be a named behaviour change.
- Stricter input checks than 2.14.1: each gap found is recorded and carried (D-06).
- Extending the cross-call check to command and agent files: known limit (D-10).
- Fixing flagged places that do not reproduce as a real failure: pinned and carried (D-08).
- 999.34 WR-02 and WR-03 (and the other carried review items): stay with Phase 65 (D-13).
- The 24 Finalize-path steps in shared files: out of reach for this slice (D-03).
</user_constraints>

## Project Constraints (from CLAUDE.md)

There is no project-level `./CLAUDE.md` in the repo [VERIFIED: ls]. These directives come from the owner's global CLAUDE.md:

- **Security (absolute):** never pass untrusted input to `subprocess` without structured args or an allowlist. Finding `file` values come from the reviewed diff and are attacker-influenced, so they go to git only as list-form argv, after `PATH_RE` + `guard.contained`, with `--` before pathspecs. Never log sensitive data. Never expose stack traces or internal error details to the end user: the helper's stderr goes to a `.err` file and the owner sees only the fixed sentence.
- **Correctness:** guard nullable returns; validate external data at the boundary (the state JSON, the blob-out path). Release resources on every path: `with open(...)`, subprocess timeouts. Don't swallow exceptions silently: map them to an exit code and write a fixed diagnostic line to stderr.
- **Follow existing conventions:** flat co-located `test_<module>.py`, `unittest.TestCase`, a `TestImportSet` class pinning imports, prose locks as `check_*` functions with `assert_holds` / `assert_trips` mutants (`LockCase` in `test_finalize_card.py`).
- **Division of labor:** technical choices are Claude's. Product questions go to the owner in plain terms (D-14 page; Open Question 1).
- **Planning format:** STATE.md/ROADMAP.md edits follow `/Users/julianamacbook/Documents/Codex/planning/PLANNING-FORMAT.md`.
- **Repo memory (project):** bare `pytest` works and `python3 -m pytest` does not. Every lock needs a mutant ("decorative guards" lesson). The Bash tool is zsh, so run multi-line shell as `bash -s <<'BASH' … BASH`. `.planning` is partly gitignored, but this phase dir is tracked [VERIFIED: git ls-files].

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FINX-01 | Input assembly and gate/report handoff through stdlib helpers on the single-writer state path; same gate decisions and reports as baseline | Helper design (Pattern 1), reuse map (Don't Hand-Roll), `HelperWalk` comparison (Pattern 3) |
| FINX-02 | Missing/malformed/stale inputs fail visibly; failed/refused attempt writes no report, archives nothing | Exit-code → sentence map (Pattern 2), blob-out freshness rule, fault mapping table, Pitfalls 3–5 |
| FINX-03 | Restart and retry work across fresh shell calls | One self-contained fence per attempt; `TestFinalizeFreshShellWalk` rewritten against the new fence; `fresh-shell-restart` situation |
| FINX-04 | Superseded prose and locks removed; invariants and recovery guidance kept; judgment stays in host | Removal ledger seed (§ Removal Ledger Seed), D-12 move, lock inventory |
| FINX-05 | Before/after comparison against the Phase 62 criterion; revert if no benefit | Projected counts table, exact commands, Open Question 1 |
| XVAR-01 | One general check over every phase file; mutant proves it trips | Pattern 4, probe results, mutant list |
| XVAR-02 | Every flagged file recorded with its reproduction before change | Flagged-site table, repro recipe |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`json`, `os`, `re`, `subprocess`, `sys`) | runtime 3.14.5 local; CI pins 3.14; baseline recorded on 3.12.12 | New helper module | The plugin is stdlib-only, enforced by `.github/scripts/stdlib_only.py` [VERIFIED: file read] |
| `carry_state.finalize_counts(state, head_blobs)` | in-repo | The three counts + 5 hash lists | The one closure rule, already tested (174 Finalize tests + `test_carry_state.py`) |
| `finalize_gate.run({"flags": …})` | in-repo | Gate decision | Pure; import set pinned to `{json, sys}`, so it must stay pure. Call it in-process; don't add git to it |
| `batch_card.decisions_report(state)` | in-repo (`batch_card.py:1465`) | Owner-decision entries for REVIEW.md | Already the report source |
| `guard.contained(root, path)` | in-repo | Containment check | "The ONE tested path-containment check"; never re-inline |
| `fixcommit.PATH_RE` (`^[A-Za-z0-9._/-]+$`) | in-repo | Character pre-filter | Import the constant. Do NOT use `fixcommit.validate_paths`: it also refuses a leading `-`, which is stricter than 2.14.1 (D-06) |
| `gitfixture.py` | in-repo test support | Real temp git repos with isolated config | Used by every git-driving test |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `docs/design/lean-v2.15/tools/step_count.py` (rule v1) | Step counts at `--rev` | Before/after comparison (FINX-05) |
| `plugins/vibe-check/scripts/footprint.py --rev <sha> --json` | Bytes on the `finalize` mode path | Before/after comparison |
| `docs/design/lean-v2.15/tools/finalize_capture.py` | Five-situation walk and verify | Equivalence (FINX-01/02/03) |
| pytest 9.0.3 (test-only, already installed and pinned in CI) | Runner | All tests |

**Installation:** none. No external packages are added in this phase.

## Package Legitimacy Audit

No external packages are installed in this phase. The helper and tests use only the Python standard library and sibling modules (CI gate: `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check`). slopcheck was not run because there is nothing to check.

## Architecture Patterns

### System Architecture Diagram

```
 --finalize (host reads 90-finalize.md)
        │  host decides: noninteractive? pr_mode? range_mode?   (judgment stays in host)
        ▼
 ┌─ ONE bash fence (fresh shell each attempt) ─────────────────────────────────────────┐
 │ mktemp → BLOBFILE ; printf 'BLOBFILE=%s\n'                                          │
 │ python3 finalize_inputs.py --state-file "$STATE_FILE" --blob-out "$BLOBFILE"        │
 │        --noninteractive <b> --pr-mode <b> --range-mode <b>   2>"$BLOBFILE.err"      │
 │   ├─ state file absent? ── yes ─▶ counts=0, present=false ───────────────┐          │
 │   ├─ parse state (fail → exit 3)                                           │          │
 │   ├─ last-pass fix_verdicts → join findings by stable_hash → file          │          │
 │   │     PATH_RE? guard.contained(toplevel)? ─ no ─▶ omit (fail closed)     │          │
 │   │     git rev-parse HEAD:f ; git diff --quiet HEAD -- f ;                │          │
 │   │     git diff --cached --quiet -- f  ── any ≠0 ─▶ omit                  │          │
 │   ├─ write {file: blob} to BLOBFILE (must exist, be empty)                 │          │
 │   ├─ carry_state.finalize_counts(state, blobs)  (None → exit 3)            │          │
 │   ├─ flags (7 keys) ─▶ finalize_gate.run ◀────────────────────────────────┘          │
 │   ├─ action == write → batch_card.decisions_report(state) (None → exit 5)            │
 │   └─ stdout: {"action","reason","next","counts","report"}                            │
 │ case $? → 0 print │ 2,3 "…carry_state.py failed…" │ 4 "…finalize_gate.py failed…" │   │
 │                     5 "…decisions-report failed…" (no rebuild)                        │
 └──────────────────────────────────────────────────────────────────────────────────────┘
        │ non-zero (2/3/4) → rebuild ONCE (same fence, NEW BLOBFILE) → second failure:
        │                    "Finalize stopped — nothing was written or archived; run `--finalize` again."
        ▼ branch on `next`
   write-review-md ─▶ prior REVIEW.md archive fence ─▶ Write REVIEW.md (from report bundle) ─▶ state archive fence
   finalize-card   ─▶ rows fence (reads printed BLOBFILE literal) ─▶ card ─▶ parse ─▶ record-decisions
                       └─▶ step 3: run the SAME fence again (new BLOBFILE) → branch on `next`
   stop-fallback-cw / stop-fallback-nv / stop-fallback-medium / stop-no-state / stop-refused ─▶ prose message, stop
```

### Recommended Project Structure
```
plugins/vibe-check/scripts/
├── finalize_inputs.py          # NEW: fingerprints + counts + flags + gate + report bundle (one call)
├── test_finalize_inputs.py     # NEW: unit + CLI + git-fixture parity + TestImportSet + mutants
├── test_cross_call_vars.py     # NEW: XVAR-01 whole-tree check, mutants, named exceptions
├── finalize_gate.py            # unchanged (stays {json, sys})
├── carry_state.py              # unchanged
├── batch_card.py               # unchanged
plugins/vibe-check/phases/shared/90-finalize.md   # gate-input section rewritten; card untouched
docs/design/lean-v2.15/
├── finalize-counts-explained.md   # NEW (D-12): "What the helper counts", moved word for word
├── tools/finalize_capture.py      # + HelperWalk driver, + compare of outcome fields
└── (phase evidence: ledger, flagged-file record, result page — see Open Question 3)
.github/scripts/test_stdlib_only.py # 33 → 34 shipped files (ledger entry)
```

### Pattern 1: One helper call returning a compact, branchable result
**What:** `finalize_inputs.py` takes `--state-file PATH --blob-out PATH --noninteractive true|false --pr-mode true|false --range-mode true|false`. All five arguments are required, with no defaults: a missing switch must refuse (exit 2) and never default to `false`, which would fail open. It prints one JSON object.
```json
{"action": "write", "reason": "no outstanding findings; finalization may proceed",
 "next": "write-review-md",
 "counts": {"outstanding_cw": 0, "...": "the 8 finalize-counts keys verbatim"},
 "report": {"entries": ["... batch_card.decisions_report output, only when action == write ..."]}}
```
`next` is a pure function of `action` and the counts. The values are `write-review-md`, `finalize-card`, `stop-fallback-cw` (cw>0), `stop-fallback-nv` (cw==0, nv>0), `stop-fallback-medium`, `stop-no-state` (`error`) and `stop-refused`. These match the three `fallback` bullets of 2.14.1 one-to-one, so the model no longer works out which bullet applies. Keep `action` and `reason`, because the capture's `gate` outcome field is exactly `{action, reason}`.
**Why one call:** the step count falls only when fences, Write-tool writes and printed-name pastes go away. Two calls would keep a paste and a fence (see the projection table).
**Fingerprint parity rules (must equal the 2.14.1 prose, `90-finalize.md:13-22`):**
- Iterate root `fix_verdicts` entries with `at_pass == passes[-1].pass_number`, of **any** verdict kind. `applied` entries are fingerprinted too, and `_confirmed_fix_awaiting` reads them.
- Join each one to `passes[-1].findings` **by `stable_hash` only**. A hash that names only an absorbed member, or nothing, gets no file and is skipped. Don't "helpfully" search `members[]`: that would change `test_counts_lead_fix_obsolete_never_closes_member` territory (D-06).
- Don't fingerprint `recheck_settled.fingerprint` paths. `_settled_unchanged` treats an absent path as unchanged, and adding those paths would change outcomes.
- Run validation before any git call: `PATH_RE.match(file)`, then `guard.contained(toplevel, file)`, where `toplevel` is `git rev-parse --show-toplevel` from the process cwd. Run git **only if there is at least one candidate file**: 2.14.1 runs no git at all when there are no last-pass verdicts, and four of the five situations run in a non-git directory.
- If `--show-toplevel` fails or the root is empty, `guard` refuses: omit the file and continue. This is not an error.
- The three calls are exactly `["git","rev-parse","HEAD:"+f]`, `["git","diff","--quiet","HEAD","--",f]` and `["git","diff","--cached","--quiet","--",f]`. Use list argv, `cwd` = the process cwd, and a timeout. Include the file only when all three exit 0. A timeout or OSError means omit.
- Write `{file: blob}` (or `{}`) to `--blob-out` *before* counting, so the card's rows fence reads the same map.

### Pattern 2: Owner text stays in the fence; the helper returns codes
Keep the house rule from `finalize_gate.py`: "This module decides; the prose renders." The helper never prints an owner sentence. The fence maps exit codes to the existing sentences byte for byte:

| Exit | Meaning | Sentence (unchanged 2.14.1 text) | Rebuild? |
|------|---------|----------------------------------|----------|
| 0 | result on stdout | — | — |
| 2 | usage, or `--blob-out` missing / not a regular file / not empty | `I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived.` (what a missing BLOBFILE produced at 2.14.1) | yes, once |
| 3 | state unreadable/malformed (`finalize_counts` → None) | same carry_state sentence | yes, once |
| 4 | internal gate-stage failure (should be unreachable) | `I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived.` | yes, once |
| 5 | `decisions_report` → None on `write` | `I'm uncertain about Finalize mode — batch_card.py decisions-report failed; nothing was written or archived.` | **no**: at 2.14.1 a report failure is a plain stop, outside the rebuild rule |
| mktemp fails | — | `Finalize stopped — nothing was written or archived; run \`--finalize\` again.` | stop (as today) |

Use only bash-3.2 constructs (`case $?`). macOS ships bash 3.2.57 [VERIFIED: `bash --version`]. Send stderr to `"$BLOBFILE.err"`, matching the gate fence's existing `.err` convention.

### Pattern 3: A candidate driver beside the 2.14.1 driver (don't touch the baseline)
`finalize_capture.py` was built for this: "a later driver that calls helpers instead of walking fences can produce the same outputs for the same inputs" [VERIFIED: module docstring]. Add a `HelperWalk` class (`NAME = "helper-walk-2.15"`) and a way to choose it (a CLI `--driver helper`, or registration keyed on the candidate's fence text). Then:
- **Leave `SITUATIONS`, `OUTPUT_KEYS`, `NORMALISATION` and `FenceWalk2141` unchanged.** Then `verify --record baseline/finalize-situations-v2.14.1.json` still prints `finalize baseline matches (5 situations)` at `dd8e4ab`. That is the D-05 "figures before and after" proof for the tool change.
- Add a `compare` mode that checks only the outcome fields (`gate`, `stop_sentence`, `report`, `files_written`, `files_archived`, `state_closed`) and lists `steps` / `tally` differences as the named intended difference (D-15).
- **Fault mapping (each must be named on the D-14 page):**

| 2.14.1 fault | Why it cannot recur as-is | Candidate injection | Expected outcome |
|---|---|---|---|
| `blobfile: missing` (one-rebuild; second-failure leg) | The model no longer writes BLOBFILE between fences | The driver adds `rm -f "$BLOBFILE"` after the fence's `printf` line for that attempt, so "the printed file is gone before the helper reads it" → exit 2 | identical: rebuild → write; two faults → stop sentence |
| `gate_input: not json` (refused-close) | No GATEFILE exists; the model never writes gate input | The driver adds `printf 'not json' > "$BLOBFILE"` after the `printf` line, so the fresh-file rule refuses a non-empty blob-out → exit 2. This is the closest analogue: "a malformed input file the attempt depends on" | identical: gate `[]`, stop sentence, nothing written or archived |
| `fresh-shell-restart` `head_blobs: {ARCH_FILE: "blob-pre-card"}` | Real git cannot produce the id `blob-pre-card` | The driver `git init`s the work dir, commits `ARCH_FILE`, and the prepared state's `verified_blob` = that real blob | identical outcome fields (the report is decisions-report JSON and carries no blob) |

  Also run the two new injections against 2.14.1 with `FenceWalk2141` as a supplementary record (kept separate from the pinned record). That shows 2.14.1 gives the same outcome for the same fault, so the comparison is like-for-like rather than resting on an argued mapping.

### Pattern 4: The cross-call check (XVAR-01)
A whole-tree walk in the style of `test_mktemp_template.py`, with `check_*` functions and `LockCase` mutants in the style of `test_finalize_card.py`.
- **Fences:** the same rule as `step_count.py`: optional indent, 3 or 4 backticks + `bash`, closed by the same tick count. Fences in other languages are skipped. The check must also see indented fences: a column-0-only scan finds 9 of 18 in `90-finalize.md` [CITED: finalize_capture.py docstring].
- **Assignments in a fence:** `NAME=`, `NAME+=`, `if NAME=$(`, `export/local/readonly/declare NAME=`, `for NAME in`, `read [-r] NAME…`. Ignore text inside single quotes, quoted-delimiter heredoc bodies and comments.
- **Reads:** `$NAME` / `${NAME…}`, excluding special parameters (`$1`, `$?`, `$@`, `$$`, `$#`) and escaped `\$`.
- **Rule:** a read in fence *j* of a NAME that is not assigned earlier in fence *j* (by line order) but is assigned in an earlier fence *i* of the **same file** is a violation, unless fence *i* prints it: `printf` with a format containing `NAME=%s` (including multi-name formats such as bootstrap's `VC_ROOT=%s\nGUARD_PY=%s…`) or `echo "NAME=$NAME"`. Both forms exist in the tree today [VERIFIED: grep].
- **Cross-file names** (`VC_ROOT`, `GUARD_PY`, `CONFIG_PY`, `SCORE_PY`, `STATE_FILE`, `FINALIZE_MODE`…) are never assigned in the reading file's earlier fences, so the same-file rule does not flag them. Keep the check same-file. Record "a read whose setter is in another file" as a known limit next to D-10. Don't build a cross-file pass: the order in which files load is mode-dependent, so it would need a model of the spine.
- **Exceptions:** a literal frozenset of `(relpath, NAME)` pairs that starts as exactly the recorded non-fixed flags. Assert `current_flags == exceptions`. That way a new flag fails, and a stale entry (fixed but still listed) also fails, which enforces shrink-only by name rather than by count.
- **Mutants (each its own subTest):** (a) a copy of a real file with an injected setter fence and a later reader fence trips; (b) the same with `printf 'X=%s\n' "$X"` holds; (c) delete `printf 'BLOBFILE=%s\n'` from `90-finalize.md` text → trips (the 999.25 generalisation); (d) re-insert a `FINALIZE_GATE_INPUT_JSON` setter fence plus a reader → trips (V9 generalisation); (e) a single-quoted `'$X'` and a quoted heredoc don't trip; (f) reassign-before-read doesn't trip; (g) an indented fence and a four-backtick fence are both scanned; (h) adding an unlisted pair trips, and a listed-but-absent pair trips; (i) the walk sees 27 files and ≥ N fences (guards against a scan that finds nothing).

### Anti-Patterns to Avoid
- **Adding git to `carry_state.py` or `finalize_gate.py`.** Their docstrings promise "never runs git" and `{json, sys}`, and `TestImportSet` pins that.
- **A test-only override such as `--head-blobs` on the new helper.** It would be a fail-open backdoor in shipped code. Drive tests through `gitfixture` repos instead.
- **Printing BLOBFILE from Python only.** `step_count` recognises printed names only from `printf 'NAME=%s\n' "$…"` inside a fence. If the helper printed it, the rows fence's `"$BLOBFILE"` paste would silently stop being counted: an undercount that flatters the result. Keep `mktemp` + `printf` in the fence.
- **Folding the archive fences into the helper.** The REVIEW.md Write sits between them (prior archive → Write → state archive), and their messages are owner-visible. The step gain is at most 1–2 and the risk to D-05 is real.
- **Using `fixcommit.validate_paths`.** It refuses leading-`-` paths that 2.14.1 would fingerprint (D-06: behave as 2.14.1; record the gap).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Open/closed counting | any re-derivation | `carry_state.finalize_counts` | Phases 46–59 rules (evidence, covers, members, NV) live there |
| Gate branch order | an if-chain in the new helper | `finalize_gate.run` | Fail-closed type checks, fixed reasons |
| Containment | path string checks | `guard.contained` | Symlink and sibling-dir masquerade handling |
| Report entries | joins over state | `batch_card.decisions_report` | Join rule for absorbed members already implemented |
| Temp git repos in tests | ad-hoc `git init` | `gitfixture.make_repo` / `git` / `helper_env` | Isolates global config (gpgsign, hooks) |
| Archive no-clobber | anything | existing `review_archive.py` fences, unchanged | Hard-link/copy fallback, `-N` suffixes |
| Step/byte counting | a new counter | `step_count.py` rule v1, `footprint.py` | D-05: a rule change must be recorded |

**Key insight:** every rule this phase touches already has one tested home. The new module should be glue (about 150–250 lines) plus the git fingerprint loop, which is the only genuinely new logic.

## Runtime State Inventory

This is a refactor of instructions and helpers, not a rename. Answered for completeness:

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | `.turingmind/state/format-53/*.json`: format unchanged; the helper reads it and writes nothing | None. Verified: `record-decisions` stays the only pre-report writer |
| Live service config | None. The plugin has no services | None |
| OS-registered state | None | None |
| Secrets/env vars | `TURINGMIND_NONINTERACTIVE`: still judged by the host and passed as `--noninteractive` | None (no rename) |
| Build artifacts | The installed plugin cache (`~/.claude/plugins/cache`) runs the OLD prose until resync and relaunch (Phase 60 R5; memory "install chronically stale") | Only matters for a live check, and live runs are out of scope without an approved proposal. Name it on the D-14 page |

## Common Pitfalls

### Pitfall 1: Breaking the `test_decision_continuity` repro record
**What goes wrong:** `TestRepro60Record.test_every_fixture_exists` requires every fixture test named in `REPRO_60` to exist in the suite. Rows `999.25-BLOBFILE`, `GATE-INPUT-CROSS-CALL`, `GATEFILE-RETRY`, `STALE-GATEFILE-RERUN`, `STALE-BLOBFILE-RECOUNT` and `FINALIZE-HEAD-SHA-WEDGE` name 15 tests in `test_finalize_card.py` / `test_diff_ranges.py`, many of which walk the fences being removed [VERIFIED: printed in this session].
**How to avoid:** for each row, either keep a test of that name that proves the same rule against the new fence, or rewrite the row's `fixture` to the replacement test. Either way it is a D-11 ledger entry. Never just delete.

### Pitfall 2: Hidden prose locks outside the three Finalize test files
**What goes wrong:** removing gate-input prose turns tests red in other modules: `test_carry_state.py::test_fix_obsolete_unbound_when_working_tree_dirty` asserts that `90-finalize.md` contains `git diff --quiet HEAD --` and `git diff --cached --quiet --`; `test_score.py::test_old_reader_refuses_open_nv_state` indexes the counts fence text (`if COUNTS_JSON=$(python3 … finalize-counts`); `test_diff_ranges.py` (`COUNTS_CALL`, `test_finalize_mode_skips_the_bind_and_reaches_the_counts_step`); `test_finalize_card.py::check_phase57_decisions` needs 12 needles, most of them in the D-12 passage; `test_confirmed_fix.py` (2 tests). `finalize_capture.py`'s needles `COUNTS_CALL` / `GATE_CALL` / `STATE_PRESENT` / `REPORT_CALL` are a further coupling, but only to the pinned tree.
**How to avoid:** before editing the prose, run the full suite against a scratch copy of the prose with the section removed, and turn the red list into the ledger. Where a needle moves to the D-12 doc, point the check at the doc and keep its mutant.

### Pitfall 3: The one-rebuild rule applied to the report failure
**What goes wrong:** once `decisions-report` is folded into the helper call, a report failure becomes a helper non-zero exit and gets rebuilt. At 2.14.1 it is a plain stop, so behaviour drifts.
**How to avoid:** use a distinct exit code (5) with its own sentence, and prose that says it stops without a rebuild. Test it with a state on which `decisions_report` returns None while `finalize_counts` succeeds. If no such state exists, record the path as unreachable and keep the mapping anyway.

### Pitfall 4: Helper stricter than 2.14.1 (D-06)
**Examples found:** a leading-`-` path (`validate_paths` refuses it; 2.14.1 would fingerprint it); `at_pass` given as `True` (equals 1 under Python `==`, as `carry_state` already compares); a non-sha `verified_blob`.
**How to avoid:** mirror 2.14.1, write one parity test per case, and record each gap with its reproduction in the D-06 list.

### Pitfall 5: Visible stderr changes (R15)
**What goes wrong:** at 2.14.1 the counts fence does not capture stderr, so the owner sees `carry_state.py`'s one-line refusal above the sentence (Phase 60 R15). If the new fence sends stderr to `.err`, that line disappears.
**How to avoid:** the outcome fields record stderr only as present or absent, and D-05 says "diagnostics stay out of what the owner reads". Treat this as an *intended, named* difference on the D-14 page. Don't silently claim byte-identical owner output.

### Pitfall 6: `stop_sentence()` extraction in the capture
`finalize_capture.stop_sentence` finds the stop text with the regex `The stop is exactly one sentence: "…"`. Keep that sentence form in the rewritten rebuild paragraph, or `HelperWalk` needs another source for it.

### Pitfall 7: Module-count lock
`.github/scripts/test_stdlib_only.py` asserts exactly **33** shipped `.py` files and the exact stdout `33 shipped .py files; third-party imports: none` [VERIFIED: lines 81, 95]. A new module makes it 34, which needs a ledger entry ("count updated; the stdlib rule itself unchanged") plus the stdlib gate run. `test_baseline_page.py` also keeps the `lean-v2.15/README.md` tool table complete: a new tool file there needs a row.

### Pitfall 8: XVAR fixes land on the Finalize path
`00-scope.md`, `05-state.md` and `06-config.md` are in `MODE_PATHS["finalize"]`. Fixing a flagged site by adding `printf 'STATE_FILE=%s\n'` adds counted paste sites, because `step_count`'s `_PRINT_RE` matches names ending in `FILE`, which includes `STATE_FILE` and `LEGACY_STATE_FILE`. Fixes for names that don't end in `FILE` (`PHASE_DIR`, `CONFIG_REPO_ROOT`, the two `*_FLAG_VAL`) add bytes but no counted steps under rule v1, an asymmetry the page must state. See Open Question 1.

### Pitfall 9: "Reproduces" must be defined before repro work starts
Under the 999.25 standard (60-REPRO V8: run the fences as written, each in its own fresh `bash -s` with only PATH/VC_ROOT/TMPDIR/STATE_FILE), most of the 10 sites will "fail". Most fail safe: an empty path makes a guard or helper refuse, and the review stops. A fail-safe stop on every run is a "broken required workflow" under the four-class rule, which is exactly how 999.25 was classed and fixed. Some sites are probably masked in live use, because the model substitutes known values or merges fences. Make the plan state the repro standard up front, so that D-08's fixed-versus-pinned split is decided by evidence and not argued case by case.

## Code Examples

### The candidate fence (shape; wording of sentences copied byte-for-byte from 2.14.1)
*D-18: drop `2>"$BLOBFILE.err"` from the helper call below; plan 63-06's interfaces block is the authority.*
```bash
if BLOBFILE=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX"); then
  printf 'BLOBFILE=%s\n' "$BLOBFILE"
else
  echo 'Finalize stopped — nothing was written or archived; run `--finalize` again.' >&2
  exit 1
fi
FINALIZE_JSON=$(python3 "$VC_ROOT/scripts/finalize_inputs.py" --state-file "$STATE_FILE" --blob-out "$BLOBFILE" \
  --noninteractive false --pr-mode false --range-mode false 2>"$BLOBFILE.err")
case $? in
  0) printf '%s\n' "$FINALIZE_JSON" ;;
  4) echo "I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived." >&2; exit 1 ;;
  5) echo "I'm uncertain about Finalize mode — batch_card.py decisions-report failed; nothing was written or archived." >&2; exit 5 ;;
  *) echo "I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived." >&2; exit 1 ;;
esac
```
(Distinct shell exit 5 lets the prose say "exit 5 stops at once; any other non-zero gets the one rebuild". The planner may choose another signal, but the rebuild/no-rebuild split must be machine-visible to the capture driver.) This contains no `with the Write tool` phrase and no `"$NAME"` read of a name printed elsewhere, so under rule v1 it counts as exactly one step.

### Fingerprint loop (sketch)
```python
# Source: transcribes 90-finalize.md:13-22 at dd8e4ab; guard/PATH_RE reused, never re-inlined
def head_blobs(state, run=subprocess.run):
    last = state["passes"][-1]
    rows = {f.get("stable_hash"): f for f in last.get("findings", []) if isinstance(f, dict)}
    files = []
    for h, v in sorted(state.get("fix_verdicts", {}).items()):
        if isinstance(v, dict) and v.get("at_pass") == last.get("pass_number"):
            f = rows.get(h, {}).get("file")
            if isinstance(f, str) and f not in files:
                files.append(f)
    if not files:
        return {}                      # no git at all, as 2.14.1
    root = _git_out(["git", "rev-parse", "--show-toplevel"])   # None on failure
    out = {}
    for f in files:
        if not fixcommit.PATH_RE.match(f) or not guard.contained(root or "", f)[0]:
            continue                   # omitted: fail closed, never passed to git
        blob = _git_out(["git", "rev-parse", "HEAD:" + f])
        if blob and _git_ok(["git", "diff", "--quiet", "HEAD", "--", f]) \
                and _git_ok(["git", "diff", "--cached", "--quiet", "--", f]):
            out[f] = blob
    return out
```

### Counting the candidate exactly as the baseline was counted
```bash
bash -s <<'BASH'
cd /Users/julianamacbook/turingmind-code-review
python3 docs/design/lean-v2.15/tools/step_count.py --rev dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4 --json > "$TMPDIR/steps-base.json"
python3 docs/design/lean-v2.15/tools/step_count.py --rev "$(git rev-parse HEAD)" --json > "$TMPDIR/steps-cand.json"
python3 plugins/vibe-check/scripts/footprint.py --rev "$(git rev-parse HEAD)" --json > "$TMPDIR/fp-cand.json"
BASH
```

## Projected Counts (rule v1, computed in this session)

| Region of `90-finalize.md` | 2.14.1 | Candidate (one call + report folded) |
|---|---|---|
| Bash fences | 18 | 14 (BLOBFILE, counts, GATEFILE and gate fences → 1; decisions-report fence → 0) |
| Inline commands | 5 | 5 (card, untouched) |
| Write-tool writes | 7 | 5 (BLOBFILE and GATEFILE writes gone) |
| Paste sites | 38 (BLOBFILE 2, GATEFILE 2, card names 34) | 35 (BLOBFILE 1, the rows fence; GATEFILE 0) |
| **File total** | **68** | **59** |
| **Finalize path total** | **92** | **83** (84 if the report is not folded) |

Bytes: the gate-input section (lines 10–67) is 10,892 B. The D-12 passage (lines 34–39) is 3,694 B and moves out whole. The fingerprint procedure (1,899 B) and the GATEFILE write/flags prose shrink to a short fence contract. The candidate's real figure comes from `footprint.py --rev <candidate>`; the baseline path is 136,114 B. A two-call design (fingerprints, then counts+gate) would give about 87 steps: still a drop, but half the benefit.

## Removal Ledger Seed (D-11)

The tests below lock the prose being replaced [VERIFIED: grep/AST scan]. Each needs a replacement test with a mutant, or "no longer applies" with a reason. Replacement first, then removal.

| Current lock | Rule it protects | Likely replacement |
|---|---|---|
| `test_finalize_card.py`: `TestFinalizeFreshShellWalk` (~13 tests: walk, card route, counts-without-literal, cross-call gate var, retry new BLOBFILE / GATEFILE, stale earlier attempt, post-decision fresh GATEFILE, post-decision re-fingerprint, missing GATEFILE trigger, malformed GATEFILE stop sentence) | fresh-shell completion, one rebuild, never reuse, re-fingerprint after the card | The same walks rewritten over the new single fence (plus the unchanged card fences); helper tests for blob-out freshness (non-empty or missing → exit 2); a re-fingerprint test with `gitfixture` (edit during the card reopens) |
| `check_printed_paths`, `check_file_refs_created` | mktemp files printed; reads created | Keep (the card is unchanged); they still hold for the new fence |
| `no_cross_call_gate_input` | the gate reads a printed GATEFILE | "No longer applies" (no gate input file; flags are built in-process), plus XVAR mutant (d) as the general replacement |
| retry / step-3 rule needle locks (`test_mutant_retry_rule`, `test_step3_rerun_rule_holds`, `test_mutant_step3_*`) | the rebuild and step-3 wording | Rewritten needles for the new wording; mutants kept |
| `check_phase57_decisions` | Open/Closed contract wording | Re-pointed at the D-12 design doc for the moved needles; card needles stay on `90-finalize.md` |
| `test_carry_state.py::test_fix_obsolete_unbound_when_working_tree_dirty` (prose half) | Finalize checks both `git diff` cleanliness forms | Helper parity test: a dirty working tree or a dirty index each omit the file (gitfixture), with a mutant that drops one check |
| `test_score.py::test_old_reader_refuses_open_nv_state` (fence lookup) | the downgrade refusal reads the counts fence | Point it at the helper call, or at `carry_state.finalize_counts` directly |
| `test_diff_ranges.py` `COUNTS_CALL` walk (`test_finalize_mode_skips_the_bind_and_reaches_the_counts_step`) | `--finalize` reaches counts with the bind skipped | The same walk reaching the new fence |
| `test_decision_continuity.py` `REPRO_60` fixtures (Pitfall 1) | the historical repro record stays executable | Rename fixture references to the replacements |
| `.github/scripts/test_stdlib_only.py` (33) | the shipped module count | 34; stdlib rule unchanged |

## State of the Art

| Old Approach (2.14.1) | Current Approach (this phase) | Impact |
|---|---|---|
| The model runs git per file, writes the blob JSON, copies paths, writes the flags JSON and runs the gate (4 fences, 2 writes, 3 pastes) | One fence plus one helper call | −9 counted steps, plus uncounted git/guard calls |
| Cross-call variables caught only for BLOBFILE/GATEFILE (two 999.25 cases) | One whole-tree check, with named exceptions | New cases fail CI |

**Deprecated/outdated:** `GATEFILE` and `FINALIZE_GATE_JSON` disappear from the prose. `COUNTS_JSON` is replaced by the helper result's `counts`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `batch_card.decisions_report` can return None on a state that `finalize_counts` accepts (or else exit 5 is unreachable) | Pattern 2, Pitfall 3 | Low: the mapping is harmless either way; test or record as unreachable |
| A2 | The live model substitutes `$STATE_FILE`-style cross-file names correctly (Finalize has worked live since v2.14) | Pattern 4 (same-file scope) | Medium: if not, there is a cross-file defect the D-10 scope leaves out. Name it as a known limit |
| A3 | Most XVAR candidate sites fail safe (stop) rather than silently mis-behave | Pitfall 9 | Medium: `06-config.md` `MIN_CONFIDENCE_FLAG_VAL` / `CODEX_FLAG_VAL` empty in a fresh shell may silently *ignore the owner's flag* (not a stop). That is a possible "broken required workflow" or silent behaviour change. Repro decides |
| A4 | Projected 83 steps holds for the final prose wording | Projected Counts | Low: recount at the candidate commit is the authority |
| A5 | `git diff` with or without `--no-optional-locks` gives the same exit codes as the model's 2.14.1 calls | Pattern 1 | Low: pin with gitfixture parity tests (clean, dirty tree, dirty index, absent at HEAD) |

## Open Questions (RESOLVED)

1. **Do XVAR fixes in `00-scope.md` / `05-state.md` / `06-config.md` count toward the Phase 63 pass/fail figure?** (owner, product)
   - What we know: those files are on the Finalize path and in the 92. D-09 says shared-file growth is reported as named growth by Phase 65, "separate from the Finalize saving". Fixing `STATE_FILE` by printing it adds counted pastes.
   - What's unclear: whether "neither grows" is judged on the extraction alone or on the phase-end tree.
   - Recommendation: report both figures, (a) the extraction-only commit and (b) the phase end, with XVAR growth itemised per D-09, and judge pass/fail on (a). Put this on the D-14 page explicitly. Prefer fixes that merge fences or substitute a printed literal, so growth stays minimal.
   - RESOLVED: D-16 (owner, 2026-11-14). Pass or fail is judged on the extraction-only commit; both figures go on the D-14 page; cross-call growth is itemised per D-09. Planned in 63-09 (figures at the extraction-only commit), 63-10 (phase-end figures and named growth) and 63-11 (the page).
2. **The fault mappings for `one-rebuild` / `refused-close`** are argued equivalents, not the same faults. Recommendation: the supplementary 2.14.1 run of the new injections (Pattern 3) gives a true like-for-like result. The owner sees both on the D-14 page.
   - RESOLVED: plan 63-08 runs the stand-ins against the pinned 2.14.1 tree (outcome fields, and under D-18 the screen text of the failed attempt) and records each mapping as proven or argued in `63-EQUIVALENCE.md`; 63-11 puts it on the page.
3. **Where phase evidence lives.** The ledger, the flagged-file record and the result page could go under `.planning/phases/63-…/` (tracked) or `docs/design/lean-v2.15/`. Recommendation: put the D-12 doc in `docs/design/lean-v2.15/` (shipped design record, not loaded) and the ledger, repro record and result page in the phase dir, mirroring `60-REPRO.md`.
   - RESOLVED: as recommended. The D-12 document is `docs/design/lean-v2.15/finalize-counts-explained.md` (63-07); `63-REMOVAL-LEDGER.md` (63-05), `63-REPRO.md` (63-04), `63-COUNTS.md` (63-01), `63-EQUIVALENCE.md` (63-08) and `63-RESULT.md` (63-11) live in the phase directory.
4. **The `next` field vocabulary** is new surface the prose must branch on. Keep it to the seven values above, test it as a pure function, and lock the prose's branch list against `finalize_inputs.NEXT_ACTIONS` with a mutant.
   - RESOLVED: the seven values are fixed in plan 63-02 (`NEXT_ACTIONS`, `next_action` as a tested pure function) and the prose lock with its two mutants lands in plan 63-06 Task 1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | helper, tests | ✓ | 3.14.5 | — |
| pytest | suite | ✓ | 9.0.3 | `python3 -m unittest` per file |
| git | fingerprints, gitfixture, `--rev` counts | ✓ | 2.55.0 | — |
| bash | fresh-shell walks | ✓ | 3.2.57 (macOS) | — (fences must stay 3.2-compatible) |
| GitHub Actions CI | XVAR green in CI (D-08) | ✓ (`offline-suite.yml`, ubuntu-24.04, Python 3.14) | — | — |

No blocking gaps.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `unittest.TestCase` collected by pytest 9.0.3 |
| Config file | none (defaults) |
| Quick run command | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_finalize_inputs.py test_cross_call_vars.py test_finalize_card.py test_finalize_gate.py test_finalize_archive_prose.py` (current three files: 174 tests in about 2 s) |
| Full suite command | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` from the repo root (the CI set; locally the 5 left-out tests also run) |
| Equivalence | `python3 docs/design/lean-v2.15/tools/finalize_capture.py verify --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json` must still print `finalize baseline matches (5 situations)` (about 2 s today), plus the new candidate `compare` |
| Stdlib gate | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FINX-01 | helper result equals the 2.14.1 gate decision + report on the same state (fixtures: six-row, loop-state, dismissed-all, NV, fix-obsolete) | unit + CLI | `pytest -q test_finalize_inputs.py -k parity` | ❌ Wave 0 |
| FINX-01 | five situations' outcome fields equal the record | integration | `finalize_capture.py compare --driver helper …` | ❌ (driver) |
| FINX-01 | fingerprint parity: clean / dirty tree / dirty index / absent at HEAD / PATH_RE fail / escape / no verdicts → no git / non-repo | unit (gitfixture) | `pytest -q test_finalize_inputs.py -k fingerprint` | ❌ Wave 0 |
| FINX-02 | missing / non-empty blob-out, malformed state, missing args → exit codes; fence prints the exact sentence; nothing written or archived | unit + fresh-shell | `pytest -q test_finalize_inputs.py -k refuse; pytest -q test_finalize_card.py -k FreshShell` | ❌ / rewrite |
| FINX-03 | rebuild once, then stop; step 3 re-run on a NEW BLOBFILE in a fresh shell; an edit during the card reopens | fresh-shell walk | `pytest -q test_finalize_card.py -k FreshShell` | rewrite |
| FINX-04 | ledger complete: every removed lock has a replacement whose mutant trips | lock + mutant | `pytest -q test_finalize_card.py test_finalize_inputs.py` | rewrite |
| FINX-04 | `next` vocabulary in prose == `NEXT_ACTIONS` | prose lock + mutant | `pytest -q test_finalize_inputs.py -k prose` | ❌ |
| FINX-05 | counts at candidate vs `dd8e4ab`; MANIFEST fingerprints unchanged | script run (recorded) | `step_count.py --rev …`, `footprint.py --rev …`, `sha256` vs `MANIFEST.json` | tools exist |
| XVAR-01 | the walk flags exactly the named exceptions; mutants (a)–(i) trip | lint + mutant | `pytest -q test_cross_call_vars.py` | ❌ Wave 0 |
| XVAR-02 | each flagged pair has a recorded fresh-shell repro before any change | record + test that each exception names a repro id | `pytest -q test_cross_call_vars.py -k record` | ❌ |

### Sampling Rate
- **Per task commit:** the quick run command.
- **Per wave merge:** full suite + capture verify + stdlib gate.
- **Phase gate:** full suite green; capture verify green at `dd8e4ab`; candidate compare green except the named step/tally differences; CI green on the PR.

### Wave 0 Gaps
- [ ] `plugins/vibe-check/scripts/test_finalize_inputs.py`: red tests for Pattern 1/2 before `finalize_inputs.py` exists
- [ ] `plugins/vibe-check/scripts/test_cross_call_vars.py`: red until the check function exists; first run produces the flagged list for XVAR-02
- [ ] `HelperWalk` tests in `docs/design/lean-v2.15/tools/test_finalize_capture.py`
- [ ] Recording the current behaviour first (standing rule): capture verify, step and footprint figures at `dd8e4ab` and at the branch base, MANIFEST hashes. No framework install is needed.

### Mutation discipline (every new lock)
| Lock | Mutant that must trip it |
|------|--------------------------|
| blob-out must exist and be empty | the helper accepts a non-empty file → `refused-close` analogue reaches `write` |
| PATH_RE before git | drop the regex → a `a b.ts` file reaches git (assert via a recording `run` stub) |
| guard before git | drop `contained` → `../x` reaches git |
| omit on dirty tree / dirty index | drop either `git diff` check → a dirty-file fix-obsolete closes |
| no git without candidates | an unconditional `--show-toplevel` → the non-git work dir fails |
| required switches | default `--noninteractive` to false → a missing arg returns 0 |
| exit 5 no-rebuild | map 5 to the carry_state sentence → the walk rebuilds |
| exceptions set exact | add a fake pair / remove a real pair → the check trips |

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | yes (filesystem containment) | `guard.contained` under `git rev-parse --show-toplevel`; fail closed on an empty root |
| V5 Input Validation | yes | `PATH_RE` pre-filter; strict `true`/`false` switch parsing; state shape validated by `carry_state._check_state`; blob-out must be an existing empty regular file |
| V6 Cryptography | no | — (git blob ids are compared, never computed) |
| V7 Errors/Logging | yes | Fixed diagnostics to `.err`; never echo a path or a title; no traceback to the owner |
| V12 Files | yes | No new file creation except the minted BLOBFILE; no writes to state |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Attacker-authored `file` in a finding → git option or command injection | Tampering / EoP | List argv, no shell, `HEAD:`-prefixed rev arg, `--` before pathspec, PATH_RE + guard first |
| Symlink or `..` escape to fingerprint files outside the repo | Info disclosure | `guard.contained` (realpath of existing prefixes) |
| Stale blob map closing a fix-obsolete verdict on edited code | Tampering (wrong close) | A fresh BLOBFILE per attempt; the helper refuses a non-empty blob-out; re-fingerprint after the card |
| Diff-derived titles in stderr | Info leak / spoofing | Fixed reason strings only (house rule in `carry_state` / `guard`) |
| A git hang stalling Finalize | DoS | Subprocess timeout → omit file (fail closed) |

## Sources

### Primary (HIGH confidence)
- `plugins/vibe-check/phases/shared/90-finalize.md` (read in full): gate-input section L10–67, card, report, archives
- `plugins/vibe-check/scripts/finalize_gate.py`, `carry_state.py` (L100–234, L470–540, L1094–1130), `fixcommit.py` (L95–205), `guard.py`, `gitguard.py` (hook scope: never the main session, per `hooks/hooks.json`), `gitfixture.py`
- `docs/design/lean-v2.15/CRITERION.md`, `baseline/steps-v2.14.1.json`, `baseline/MANIFEST.json`, `tools/step_count.py`, `tools/finalize_capture.py`
- Runs in this session: `step_count.py --root` (68 / 92, identical to the baseline), per-name paste breakdown, `finalize_capture.py verify` (matches), Finalize test files (174 passed), XVAR probe (10 sites / 6 pairs), byte measurement of the prose regions
- `.planning/milestones/v2.14-phases/60-…/60-REPRO.md` V8, V9, residuals R1–R26
- `.github/workflows/offline-suite.yml`, `.github/scripts/stdlib_only.py`, `test_stdlib_only.py`

### Secondary (MEDIUM confidence)
- Projected candidate counts (the real counting rule applied to a design, not to written prose)

### Tertiary (LOW confidence)
- Whether each XVAR candidate fails safe or silently (A3): needs the XVAR-02 repros

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. Everything is in-repo and read.
- Architecture: HIGH for the reuse map and the fence/count mechanics; MEDIUM for the fault-mapping design (new, argued)
- Pitfalls: HIGH. Each was found by grep or scan in this session.

**Research date:** 2026-11-14
**Valid until:** until `90-finalize.md`, `finalize_capture.py` or `step_count.py` change (the codebase moves; there are no external dependencies)
