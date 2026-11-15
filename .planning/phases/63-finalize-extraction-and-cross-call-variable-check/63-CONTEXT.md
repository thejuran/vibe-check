# Phase 63: Finalize extraction and cross-call variable check - Context

**Gathered:** 2026-11-14
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers two things and nothing else:

1. **Finalize extraction (FINX-01..05).** The mechanical steps that work out Finalize's gate inputs and hand the result on (HEAD fingerprints, the three counts, the seven-key flags, the gate call, and the data the report step reads) run through tested stdlib helpers on the existing single-writer state path, instead of being carried out by the model step by step. Gate decisions, reports and stop messages are the same as 2.14.1 (`dd8e4ab`, tag `v2.14.1`). Superseded instructions and their locks are removed; behavioural invariants and recovery guidance stay. The result is compared with the Phase 62 baseline (136,114 bytes, 92 model-run steps) and reverted if it shows no benefit.
2. **Cross-call variable check (XVAR-01..02).** One general check walks every phase file and fails when a Bash block reads a shell variable set in an earlier block without the printed-path rule. A mutant proves it trips. Any file it flags is recorded with its reproduction before it is changed.

Not in this phase: the decision card's plumbing, a helper-generated REVIEW.md, changes to the instructions ordinary reviews load (other than a fix for a reproduced failure, D-09), any new orchestration framework, state rewrite, changed model defaults, paid or live runs.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked — do not re-litigate)
- **Pass rule (Phase 62 D-01/D-02):** the slice passes if bytes loaded or model-run steps on the Finalize path drops and neither grows, with identical behaviour. No percentage target. Nothing is cut to reach a number.
- **Maintenance added (Phase 62 D-03):** new helper code and tests are reported as their own labelled figure; they do not decide pass or fail.
- **No drop (Phase 62 D-04):** default is revert; the owner gets one plain-terms page first and may keep the slice by explicit waiver. No automatic second attempt.
- **Same behaviour (Phase 62 D-07/D-08):** the five recorded Finalize situations (`clean-close`, `card-first`, `one-rebuild`, `refused-close`, `fresh-shell-restart`), the offline suite and the archived replay match 2.14.1 byte for byte; any difference is named and explained or it blocks.
- **Counting (Phase 62 D-05):** the same `step_count.py` rule (rule version 1) and `footprint.py` are used; a change to the script, phrase list or lead-in list must be recorded with the figures it gives on 2.14.1 before and after.
- **Retry rule (Phase 60 D-07/D-08):** one automatic rebuild from the current HEAD, index and working tree, then stop with the plain no-write message; a refusal is never retried automatically; a failed or refused attempt writes no report and archives nothing; inputs from an earlier attempt or session are never reused.
- **Standing rules:** no growth per round (work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or a broken required workflow); each change starts by recording current behaviour on current code; every lock lands with a mutant that trips it; shipped scripts stay stdlib-only; `stable_hash` / GOLDEN_DIGEST stay frozen; paid or live runs need a separately approved bounded proposal; byte and step counts are reported separately from tokens or dollars.
- **Branch:** `feat/v2.15-phase-63` from `main`, one PR, deleted locally and on GitHub after merge.

### How far the extraction reaches
- **D-01:** Only the gate inputs and the gate handoff move into helpers: the HEAD fingerprints, the counts, the seven-key flags and the gate call. The model gets one compact structured result with the gate's action and an explicit next action. The decision card (its rows, suggestion, answer, parse, resolve and decision temp files) and the record-decisions step stay exactly as in 2.14.1.
- **D-02:** REVIEW.md is still written by the model from `templates/review-md-schema.md`. The helper hands it one ready bundle of the data the report fill reads (the counts, including the verified-obsolete hashes, and the owner-decision entries), so the model does not look these up in separate steps. The report's text rules do not change.
- **D-03:** The extraction does not change the files ordinary reviews also load: `phases/review/00-scope.md`, `phases/review/05-state.md`, `phases/review/06-config.md`, `commands/review.md`, `phases/shared/00-contract.md`, `phases/shared/01-bootstrap.md`. Of the 92 baseline steps, 68 are in `90-finalize.md`; the other 24 are out of reach for this slice. Plain and deep review paths stay byte-identical unless D-09 applies.
- **D-04:** Extracting the card's temp-file plumbing is not done here. It is filed at phase close as a backlog item with this phase's step numbers, to be weighed later together with the fix loop's matching card. It is not scheduled and is not added to Phase 64's three candidate families.

### Failure wording and the retry
- **D-05:** Every stop sentence the owner sees is byte-identical to 2.14.1. No reason clause and no pointer to a detail file is added. The helper's own diagnostics stay out of what the owner reads, as today. Any failure path inside the helper maps to one of the existing sentences.
- **D-06:** Where the helper could catch a bad input that 2.14.1 would have let through, it behaves as 2.14.1 does. Each such gap is recorded with its reproduction and carried to backlog. A gap that reproduces as data loss, a wrong close, silent loss of a qualifying finding or a broken required workflow goes to the owner under the four-class rule before anything changes.
- **D-07:** The Phase 60 retry rule (carried forward above) is kept as behaviour. Whether the one rebuild is the model calling the helper a second time or something the helper does itself is Claude's discretion, provided the `one-rebuild` and `refused-close` outcomes match the baseline and restart works across fresh shell calls (FINX-03).

### Files the new check flags
- **D-08:** Every place the check flags is first recorded with a fresh-shell reproduction (XVAR-02). A flagged place that reproduces as a real failure under the four-class rule is fixed in this phase. Every other flagged place goes on a named exceptions list that can only shrink, with entries identified by file and variable (not a count), and is carried to backlog. The check fails on any new case. The check is green in CI at phase end.
- **D-09:** A fix for a reproduced failure in a shared file may add bytes to the plain and deep review paths. Each is listed by file, byte count and reproduction, and Phase 65 reports it as named growth, separate from the Finalize saving. Nothing else may grow those paths.
- **D-10:** The check covers every file under `plugins/vibe-check/phases/` (27 files), as the approved scope says. Command and agent files are not covered; that is recorded as a known limit, not added to scope.

### Proof for removed safeguards
- **D-11:** A removal ledger is kept. Every removed instruction passage and every removed or rewritten test is listed with the helper test that now protects the same rule, or "no longer applies" with the reason. Each replacement is proven by a deliberate break that it catches. A rule with no replacement is not removed. The replacement lands before the removal.
- **D-12:** The explanation of what the helper counts as open and closed (the "What the helper counts" passage in `90-finalize.md`) moves word for word to a design document under `docs/design/` that the model does not load during a review. Rules the model still acts on stay in the loaded file: what to do on each gate result, the recovery guidance, the no-write rule.
- **D-13:** The two weak Phase 62 baseline checks (backlog 999.34 WR-02 and WR-03) stay carried for Phase 65. Phase 63 does not rely on them: it recounts 2.14.1 and the candidate directly from their commits with `step_count.py` and `footprint.py`, and confirms the fingerprints in `docs/design/lean-v2.15/baseline/MANIFEST.json` are unchanged.
- **D-14:** Before the PR merges, pass or fail, the owner gets one plain-terms page: the two counts before and after, "maintenance added", the five situations' match result with every named difference, a summary of the removal ledger, the flagged-files list with which were fixed and which pinned, and any gaps recorded under D-06. The merge waits for the owner's go. On a fail, this page is the Phase 62 D-04 waiver page.
- **D-15 (follows from Phase 62 D-08; not separately asked):** In the five situations, the outcome fields must match the baseline byte for byte: the gate decision, the report text, the stop sentence, the files written, the files archived and whether the state closed. The recorded lists of commands run are expected to change, since fewer model-run commands is the purpose; that change is named as the intended difference, field by field, and nothing else may differ.

### Settled at planning (owner, 2026-11-14)
- **D-16:** Pass or fail is judged on the Finalize extraction alone: the counts taken at the extraction-only commit against 2.14.1. Growth that cross-call fixes add to shared files on the same path (`00-scope.md`, `05-state.md`, `06-config.md`) does not decide pass or fail; it is itemised by file, byte count and reproduction per D-09. The D-14 page shows both figures, the extraction alone and the phase end.
- **D-17:** A flagged place counts as "reproduced" only by the Phase 60 fresh-shell standard: the instruction blocks are run as separate fresh shell calls and show an observable wrong outcome (a stop, a wrong file, or a setting silently ignored). A silently ignored setting counts as a reproduction. A reproduced place is then fixed or pinned by the four-class rule as D-08 says.
- **D-18:** Where 2.14.1 shows a step's own one-line refusal on screen above the fixed sentence, the candidate shows the same line in the same place. This covers both steps that do so at 2.14.1: the counting step (`carry_state.py`'s line above the counting sentence) and the report-data step (`batch_card.py`'s line above the report sentence; extended by the owner 2026-11-14, "Yes, same as 2.14.1"). Neither line is redirected to a side file, so nothing on screen differs from 2.14.1 anywhere on the Finalize path. D-05 still holds for everything else: the stop sentences are byte-identical and no new reason clause or pointer is added. If keeping the line visible costs a counted step, the figure is recorded as it falls; nothing is reworded to reach a number.
- **D-19 (owner, 2026-11-14, raised by 63-01 under D-06):** The subfolder gap is fixed in the helper, not carried. At 2.14.1, when Finalize runs from a subfolder of the repo, the two "does this file differ from the last commit" checks read the finding's file name relative to the current folder and match nothing, so an edited file is still fingerprinted and a "fix made this obsolete" verdict can close wrongly (reproduced on a real temporary repo; `test_gap_subdirectory_cwd`). The helper reads the file from the repo root in all three checks, so an edited file is never fingerprinted. This is the one deliberate behaviour difference from 2.14.1 in the helper; it is named on the D-14 page and in the D-15 comparison as an intended difference. The other two D-06 gaps (leading-dash file name, pass recorded as `true`) are harmless and stay matched to 2.14.1.
- **D-20 (owner, 2026-11-15, raised by 63-10):** The Close-out cross-file gap is fixed in Phase 63, not carried ("Fix in Phase 63 (Recommended)"). `90-finalize.md` uses the state-file name that `05-state.md` sets; run as separate calls, Close-out on a review with saved progress says "no prior review passes" and stops without writing REVIEW.md (reproduced in 63-REPRO.md, "Open item"). The fix tells `90-finalize.md` to use the name `05-state.md` now prints. The fix loop (`50-fix-loop.md`) is tested the same way and fixed only if it reproduces. The growth is named at phase end per D-09; the extraction verdict stays judged at the extraction-only commit per D-16, and the five-situation comparison is re-run.
- **D-21 (technical, orchestrator, 2026-11-15; owner informed):** Names that are printed in one Bash call and pasted into later ones (`PHASE_DIR`, `LEGACY_STATE_FILE`, `STATE_FILE`) come from the reviewed repo's folder and branch names. Before any such name is printed it is refused if it contains a character that is live inside double quotes (`$`, backtick, `"`, `\\`) or a newline, so a crafted name cannot run as a command when pasted. A review on a branch or folder with such a character stops with a clear message. This follows the owner's absolute security rule; the added bytes are named at phase end per D-09.
- **D-22 (owner, 2026-11-15, raised by the phase code review CR-01):** The planted-`json.py` hole is fixed in Phase 63 ("Fix in Phase 63 (Recommended)"). Inline `python3 -c` commands in the instruction files run from the reviewed repo's folder, so a file named `json.py` at the repo root is executed (mechanism reproduced; present at 2.14.1). Every inline `python3 -c` in the phase files gets `-I`, with a test that a planted module is not run and a check that no inline Python without `-I` remains. Where a changed line sits inside text pinned to its 2.14.1 bytes, the pin is updated and the change is a named difference. Growth is named per D-09.
- **D-23 (technical, orchestrator, 2026-11-15; owner informed):** From the same review: WR-01 (in `--all` mode the state path is never printed, so Close-out and the fix loop on `--all` still lose it; reproduced) is fixed as the remainder of D-20; WR-05 (the guard's tests do not prove each blocked character on its own) is fixed in the tests. WR-02, WR-03, WR-04 and SA-01 predate the phase or are design limits and are carried to backlog with 63-REVIEW.md.
- **D-24 (owner, 2026-11-15, raised by phase verification after the merge of PR #10):** The leading-dash gap is closed by matching 2.14.1 ("Match 2.14.1 (Recommended)"). For a finding in a top-level file whose name starts with `-`, with a last-pass fix-obsolete verdict on unchanged code, 2.14.1 leaves the file out of the HEAD fingerprints (its containment check ran as a command, which exits 2 on such a name), so the finding stays open and the gate does not approve; the merged helper fingerprinted the file, closed the finding and returned `write`. The records and the result page said the two matched; they did not, and the owner's go did not cover it. The helper leaves such a file out, as 2.14.1 does; a test runs the real 2.14.1 containment command to hold the match; the records are corrected. Honouring the verdict for such a file is carried to backlog as a possible later improvement. Ships as a follow-up pull request to `main`.

### Claude's Discretion
- Helper shape: a new module or additions to `finalize_gate.py` / `carry_state.py`, how many calls, the result's field names, and how temp files are handled. The single-writer state path and `record-decisions` as Finalize's only state write before REVIEW.md must hold.
- Whether the HEAD fingerprint git calls move inside a helper. Today the counting helper never runs git itself and the instructions validate each file first (the `^[A-Za-z0-9._/-]+$` filter, then `guard.py`, before any git call; a failing file is omitted, fail closed). Whatever moves, that validation and the omit-on-any-difference rule must be preserved and tested.
- Whether the archive commands (earlier REVIEW.md before the write, state after the write) fold into a helper call, provided their order, no-clobber behaviour and messages stay identical.
- The check's implementation and location, how it treats names carried forward by the documented bootstrap rule (`$VC_ROOT`, `$GUARD_PY`, `$CONFIG_PY`, `$SCORE_PY`) and reads that span two files, whether a stale exceptions entry fails the check, and whether the three Finalize-only checks in `test_finalize_card.py` are folded into it (under the D-11 ledger).
- How `finalize_capture.py` is adapted to drive the candidate, within the Phase 62 D-05 recording rule.
- Names and locations of the design document (D-12), the removal ledger (D-11) and the result page (D-14); plan count and split.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` — "Phase 63: Finalize extraction and cross-call variable check" (goal, approved scope, 5 success criteria); backlog 999.25 (the original cross-call defect), 999.34 (Phase 62 review carry)
- `.planning/REQUIREMENTS.md` — FINX-01..05, XVAR-01..02, the working rule, the no-growth rule, the equivalence baseline, Out of Scope table
- `.planning/STATE.md` — current position, deferred items, standing boundaries
- `/Users/julianamacbook/Documents/Codex/planning/PLANNING-FORMAT.md` — required format for STATE.md and ROADMAP.md edits

### Baseline and criterion (Phase 62)
- `docs/design/lean-v2.15/CRITERION.md` — the two counts, the counting rule, the five situations, what "same behaviour" means
- `docs/design/lean-v2.15/BASELINE-v2.14.1.md` — the baseline in plain terms
- `docs/design/lean-v2.15/baseline/` — `finalize-situations-v2.14.1.json`, `steps-v2.14.1.json`, `footprint-v2.14.1.json`, `traces-v2.14.1.json`, `suite-v2.14.1.json`, replay reports, `MANIFEST.json`
- `docs/design/lean-v2.15/tools/step_count.py`, `finalize_capture.py`, `path_records.py`, `baseline_records.py` and their tests — the counting and capture tools Phase 63 re-runs
- `.planning/phases/62-baseline-and-continuous-test-run/62-CONTEXT.md` — D-01..D-20 (criterion, workload, CI exceptions)
- `.planning/phases/62-baseline-and-continuous-test-run/62-REVIEW.md` — WR-02, WR-03 (D-13)
- `.planning/phases/62-baseline-and-continuous-test-run/62-CI-RECORD.md` — the five left-out tests and the two recorded skips the CI run pins
- `.github/workflows/offline-suite.yml` — the standing check

### Finalize as it is today
- `plugins/vibe-check/phases/shared/90-finalize.md` — the instructions being extracted from
- `plugins/vibe-check/scripts/finalize_gate.py`, `carry_state.py` (`finalize-counts`, `record-decisions`), `batch_card.py` (`decisions-report`, card subcommands), `review_archive.py`, `guard.py`, `statepath.py` — existing helpers to reuse
- `plugins/vibe-check/templates/review-md-schema.md` — the report template the model fills
- `plugins/vibe-check/scripts/test_finalize_card.py`, `test_finalize_gate.py`, `test_finalize_archive_prose.py` — existing locks and fresh-shell walks; `check_printed_paths`, `check_file_refs_created`, `no_cross_call_gate_input` in `test_finalize_card.py` are the two repaired 999.25 cases the general check generalises
- `.planning/milestones/v2.14-phases/60-exact-change-evidence-and-reliable-finalize/60-CONTEXT.md` and `60-REPRO.md` — printed-path rule, one rebuild, no write on failure, residuals
- `docs/design/state-single-writer-verify-v2.10.md` — the single-writer state path
- `docs/design/prose-to-code-inventory.md` — earlier inventory of instructions that could move to code

### Footprint
- `plugins/vibe-check/scripts/footprint.py` — `MODE_PATHS["finalize"]` (the seven declared files), byte counts, proxy labelling

### Testing
- `.planning/codebase/TESTING.md` — runner commands, flat co-located layout, `TestImportSet` pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `carry_state.py finalize-counts --head-blobs <file>`: already computes the three counts and the hash lists from state plus a fingerprint file; fails closed for an absent file.
- `finalize_gate.py`: already decides the action from the seven-key flags, and `review-closed` checks the state-format stamp.
- `batch_card.py decisions-report`: already returns the owner-decision entries the report needs.
- `review_archive.py`: no-clobber archive of state, earlier report and unstamped report.
- `guard.py`: path validation used before any git call.
- `gitfixture.py`: builds real git repos in tests; used by the fresh-shell walks.
- `docs/design/lean-v2.15/tools/step_count.py` and `finalize_capture.py`: the counting rule and the five-situation capture.

### Established Patterns
- Step breakdown at 2.14.1 (from `steps-v2.14.1.json`): `90-finalize.md` 68 steps (18 bash blocks, 5 inline commands, 7 Write-tool writes, 38 hand-copied paths over 11 printed names); `00-scope.md` 10, `05-state.md` 7, `06-config.md` 5, `commands/review.md` 1, `01-bootstrap.md` 1.
- The gate-input part of `90-finalize.md` uses two printed paths (`BLOBFILE`, `GATEFILE`), two Write-tool writes and three bash blocks; the card uses the other nine printed names.
- Printed-path rule: a block that creates a temp file prints `NAME=<path>`; later blocks use that literal, because a shell variable does not survive into a separate Bash call. Bootstrap names are bound once and substituted by the same idea.
- Tests are `unittest.TestCase`, flat in `plugins/vibe-check/scripts/`; each module pins its imports with a `TestImportSet` class; prose locks read the instruction files and are each mutation-tested.
- 174 tests in the three Finalize test files; eleven other test modules also read `90-finalize.md` (`test_card_text`, `test_carry_state`, `test_carry_writers`, `test_confirmed_fix`, `test_decision_continuity`, `test_diff_ranges`, `test_fixcommit`, `test_pause_batching`, `test_scope_args`, `test_score`, `test_tracecheck`).

### Integration Points
- `finalize_capture.py` drives the five situations by pulling bash blocks out of `90-finalize.md` by a search string and running them. Once those blocks change it will not find them, so the capture has to be adapted to drive the candidate while still producing comparable outcome fields.
- `footprint.py` `MODE_PATHS["finalize"]` and the baseline record list the seven files; the baseline recount uses the record's list at `dd8e4ab`, so a change to the live list cannot move the 2.14.1 figure.
- CI (`.github/workflows/offline-suite.yml`) runs the suite on every push and PR; the new check and helper tests run there, with the five named left-out tests and the pinned skip set unchanged.
- Discussion-time probe for the check (rough, unverified, same-file reads only): about 11 places in 4 files where a later block reads a variable an earlier block set without printing it: `review/05-state.md` (`STATE_FILE`, `LEGACY_STATE_FILE`), `review/06-config.md` (`CONFIG_REPO_ROOT`, `CODEX_FLAG_VAL`, `MIN_CONFIDENCE_FLAG_VAL`), `review/00-scope.md` (`PHASE_DIR`), `deep-review/2c-codex-kickoff.md` (`TIMEOUT_BIN`, which a later block re-binds from a printed value). `90-finalize.md` and `50-fix-loop.md` showed only printed-path reads. Some candidates may be harmless; each needs the D-08 reproduction. Treat this as a starting point, not a result.

</code_context>

<specifics>
## Specific Ideas

- The owner chose the smallest-surface option in every area: keep "same behaviour" clean, add nothing a reproduced failure did not ask for, and carry the rest with a record.
- Owner-facing pages (the result page, any gap or flagged-file record brought to the owner) are written in plain terms with pass/fail and numbers first, readable without code knowledge.
- Exceptions lists name each case; a count is not acceptable, so one fixed case cannot be traded for a new one.

</specifics>

<deferred>
## Deferred Ideas

- Extract the Finalize card's temp-file plumbing, together with the fix loop's matching card: backlog item filed at phase close with this phase's numbers, not scheduled (D-04).
- A helper-generated REVIEW.md (identical output for the same state): not chosen for this phase; reopen as its own proposal.
- A short reason, or a pointer to the detail file, after a stop sentence: not chosen; would be a named behaviour change.
- Stricter input checks than 2.14.1: each gap found is recorded and carried (D-06).
- Extending the cross-call check to command and agent files: known limit (D-10).
- Fixing flagged places that do not reproduce as a real failure: pinned and carried (D-08).
- 999.34 WR-02 and WR-03 (and the other carried review items): stay with Phase 65 (D-13).
- The 24 Finalize-path steps in shared files: out of reach for this slice (D-03).

</deferred>

---

*Phase: 63-finalize-extraction-and-cross-call-variable-check*
*Context gathered: 2026-11-14*
