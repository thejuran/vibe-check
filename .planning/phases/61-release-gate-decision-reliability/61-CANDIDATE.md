# Phase 61 release candidate
candidate: 0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d
parent: f4bba0a995fe71fcaa30d7f6e1e08d7f41bce86e
version: 2.14.0
suite_on_edited_tree: 3821 passed, 0 failed

Suite run from `plugins/vibe-check/scripts` on the edited working tree (README holding the `N_PASSING` placeholder; only that number changed before commit):
- `pytest -q -p no:cacheprovider test_recovery_pairs.py test_gitguard.py` -> `185 passed, 708 subtests passed in 4.93s`
- `pytest -q -p no:cacheprovider` -> `3821 passed, 5039 subtests passed in 173.89s (0:02:53)`

Commit C changes exactly `README.md` and `plugins/vibe-check/.claude-plugin/plugin.json` (`git diff --name-only C^ C`).

## README fact-check

| README claim (short) | Evidence | Result (kept / reworded / removed) |
|---|---|---|
| plugin.json `"version": "2.14.0"` | `plugins/vibe-check/.claude-plugin/plugin.json` L4; 61-RESEARCH §Version Bump (only version pin, no test asserts it, marketplace pins `ref: main`) | kept |
| v2.14 lead: "decisions are re-asked when their code changes, and Close out completes. Not measured." | 59-VERIFICATION SC1/STALE-01..05 VERIFIED; 60-VERIFICATION truths 5-6 (FINL-01/02 SATISFIED); no B3 run in v2.14 (61-CONTEXT, no RESULTS-v2.14) | kept |
| Does not change what reviewers look for or the scoring formula | 59-REPRO L231 "Replay deltas ... none observed"; 60-REPRO R11 `replay.hunk_ranges` unchanged, pinned by `TestReplayPin`; no agent prompt changes in 59/60 scope (ranges and decision continuity only, 60-REPRO R3 "agents' diff commands are unchanged") | kept |
| Not B3- or holdout-measured; v2.11 still last measured | 61-CONTEXT D-02/D-12 (no measurement in this gate); README v2.11 paragraph | kept |
| Each change first reproduced as a failing test on the previous code | 59-REPRO V1-V5 "REPRODUCED at `82ec58b`" (reverse run confirmed in 59-VERIFICATION truth 1); 60-REPRO V1-V15 each "REPRODUCED at" a pre-fix SHA | kept |
| "(3,821 passing at release)" | Full suite on the edited tree: `3821 passed, 5039 subtests passed` (this file, above) | kept (number filled from run) |
| Fix 1: 2.13 missed re-asking in uncommon layouts (same flagged code twice, edit beside second copy, listed alone or grouped; edit beside a grouped finding not the lead); now re-asked so Finalize does not write without asking | 59-REPRO V1 (CR-01 second kept-open copy), V3 (CR-02 second member sidecar), V4 (CR-04 covered member beside removed guard); `TestStaleDecisions59.test_cr01_edit_beside_the_second_copy_reasks`, `test_cr02_edit_beside_the_second_sidecar_reasks`, `test_cr04_removed_guard_beside_covered_member_reasks`; `TestLeadOrderInvariance` | reworded: first draft's examples ("two identical flagged lines both below threshold", "the same finding recorded more than once") were replaced with the exact reproduced shapes; card-reason wording deliberately not claimed (59 WR-01 multi-spot wording parked to 999.23) |
| Fix 2: deferred member under `min_confidence` stays open with its own card and blocks Finalize, not dropped to Filtered | 59-REPRO V5; `TestDeferredStaysOpen.test_dmc_deferred_covered_member_below_min_confidence_stays_open`; 59-VERIFICATION DEFR-01 "Row/card persists"; gate holds on pass 3+ (WR-02 is note wording only) | kept; no claim about the explanatory note (59 WR-02 residual) |
| Fix 3: nearby window is the five lines, measured only from added/removed lines, not context | `score.py:177 _NEARBY_LINES = 5` (same value at tag v2.13, so the widening came from ranges); 60-REPRO V1 (999.24-WIDEN ~8 lines), V2; `diff_ranges.py` builds ranges from `+`/`-` body lines (60-VERIFICATION truth 1, EVID-01 SATISFIED) | kept |
| Fix 3: applies on default, GSD, range, PR and incremental routes; `--all` keeps no decisions so has no window | 60-VERIFICATION truth 3 / EVID-03 "every route uses the exact-range builder"; 60-REPRO V4-V6, V10 (PR, GSD/incremental, default); 60-REPRO R10 / `TestRouteAll` (`--all` never stamps `nearby_at`) | reworded from plan's "every review route" to the named routes plus the `--all` exception |
| Fix 4: Close out no longer loses its temp file between steps | 60-REPRO V8 (999.25-BLOBFILE), V9; 60-VERIFICATION truth 5 / FINL-01; `test_finalize_card.py` | kept |
| Fix 4: on failure/refusal it stops without writing `REVIEW.md` or archiving; running again can complete after re-checking nothing changed | 60-VERIFICATION truth 6 / FINL-02 "stops and writes nothing; a later successful retry or re-run may complete after revalidating freshness"; 60-REPRO V12, V14, V15 | reworded from plan's "a later retry completes" to "can complete after it re-checks" (evidence says "may complete after revalidating freshness") |
| Relabels: v2.13 "previous release", v2.12 "earlier release" | Ordering only; v2.10 already uses "(earlier release)" | kept |
| Config row: removed "(except a finding grouped under a deferred row; see Known limitations)" | DEFR-01 fix (row above) | removed clause |
| Limit kept verbatim: wordier plain-English references get one follow-up (999.26) | ROADMAP backlog 999.26 still open (2.13 known limit, unchanged code) | kept verbatim |
| Limit kept verbatim: Claude's own reading of free-text answers not release-tested | No live plain-English check in this gate (61-CONTEXT D-02 scope = default route + Close out) | kept verbatim |
| Limit: finding in an untracked file is not asked again after a nearby edit | 60-REPRO R7 "a finding in a new untracked file has no ranges ... no decision there is ever stamped `nearby`" | kept; a draft "stage the file with `git add`" workaround was removed as unverified |
| Limit: PR reviews stop with an error above GitHub's diff limits (~300 files / 20,000 lines) instead of reviewing part | 60-REPRO R17 (`gh pr diff` errors, fence halts through `pipefail`, fails closed); 60-HUMAN-UAT test 2 (owner: accepted limit, no fallback). Threshold is GitHub's, not in `diff_ranges.py` (its refusal reasons are format-only, L59-65) | reworded to attribute the limit to GitHub |
| Limit: `--all` does not keep decisions between runs | 60-REPRO R10 / V7; `05-state-all.md` (ii) forces pass 1 with empty carry-forward; `TestRouteAll` | kept |
| Limit: after upgrading from 2.13, a decided finding may be asked again once | 60-REPRO R4 (old `nearby_at` stamps not migrated; "fails toward asking, one extra re-ask on the next run and never a silent keep") | kept, scoped to "the next time code near it changes" |
| Limit: only default review and Close out in scope for a live check; other routes tests only; PR fetch tested on a saved real PR diff; live outcome in release notes | 61-CONTEXT D-02, D-03; 60-REPRO R6 (PR route proven on checked-in `fixtures/pr-cumulative.diff`, PR #5) | reworded: the plan's text ("were run live", "checked once against real PRs") describes 61-03/61-04 work that has not happened at C and the live smoke may be declined (61-02); README now states scope only and defers the outcome to the release notes |
| Limit: 2.14 -> 2.13 downgrade untested; 2.13 ignores `nearby_spots`; expected effect is re-asks, not lost data | `git show v2.13:plugins/vibe-check/scripts/carry_state.py` and `score.py` contain 0 occurrences of `nearby_spots`; current `carry_state.py:319-400` reads/writes it; "expected", untested, mirrors the 2.13 downgrade bullet | kept |
| Untouched test-coupled text: "every later run that reviews changes"; git-guard boundary sentence | `test_recovery_pairs.py`, `test_gitguard.py::TestBoundaryDecision` (185 passed on the edited tree) | kept unchanged |
