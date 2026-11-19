---
phase: 66
slug: close-out-freshness
status: complete (offline)
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-16
---

# Phase 66 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 66-RESEARCH.md §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 (CI), stdlib `unittest` test classes |
| **Config file** | none (CI command in `.github/workflows/offline-suite.yml`; left-out list `.github/ci-left-out-tests.txt`) |
| **Quick run command** | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_closeout_fresh.py test_finalize_inputs.py test_finalize_card.py` |
| **Full suite command** | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` |
| **Stdlib check** | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` |
| **Estimated runtime** | quick ~30 s; full ~260 s (baseline 4126 passed) |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command + stdlib check
- **Before `/bm:verify-work`:** Full suite green, replay diff clean, differential test green
- **Max feedback latency:** ~30 seconds (quick)

---

## Per-Requirement Verification Map

| Req / SC | Behavior | Test Type | Automated Command | File Exists | Status |
|----------|----------|-----------|-------------------|-------------|--------|
| FRESH-01 / SC1 | 999.40 repro: defer + dismiss × {exact, nearby}: 2.15.0 writes, candidate refuses, no REVIEW.md, state unchanged | integration | `pytest -q test_closeout_fresh.py -k repro_999_40` | ✅ | ✅ green — `TestRepro999_40` (2 passed, 12 subtests) |
| FRESH-01 / SC1 | Real prose-fence chain with uncommitted reviewed block | integration | `pytest -q test_closeout_fresh.py -k real_chain` | ✅ | ✅ green — `TestStorePath.test_real_chain_store_tree_*` (2 passed) |
| FRESH-01 / SC1 | Refusal never starts reviewers; names same-scope command; says review is paid | prose lock | `pytest -q test_finalize_card.py -k review_again` | ✅ | ✅ green — review-again prose locks (2 passed) |
| FRESH-01 | D-06 delete/rename, D-07 whitespace, window edges, pure-shift keep | unit+integration | `pytest -q test_closeout_fresh.py -k window` | ✅ | ✅ green — `TestWindow` + window mutants (11 passed, 29 subtests) |
| FRESH-01 | Missing/unknown baseline or git failure → fail closed | integration | `pytest -q test_closeout_fresh.py -k unverifiable` | ✅ | ✅ green — `TestUnverifiable`, `test_clearable_unverifiable_store_removed`, `test_pr_head_absent_locally_is_unverifiable` (9 passed) |
| FRESH-01 | Every refusal cause clearable (refuse → review → re-decide → write) | integration | `pytest -q test_closeout_fresh.py -k clearable` | ✅ | ✅ green — `TestClearable`, `TestAllRouteClearable` (7 passed, 16 subtests) |
| FRESH-02 / SC2 | Unchanged code == literal v2.15 output byte-for-byte; no git call when no decision-closed record | two-sided differential | `pytest -q test_closeout_fresh.py -k differential` | ✅ | ✅ green — `test_differential_*` (3 passed, 16 subtests) |
| FRESH-02 | Fix-verdict freshness | regression | `pytest -q test_finalize_inputs.py -k "Freshness or Fingerprint"` | ✅ | ✅ green — `TestCliFreshness`, `TestFingerprints` (31 passed) |
| FRESH-02 | 999.28 parity + real-edit reopening | regression | `pytest -q test_worktree_snap.py test_decision_continuity.py -k "999_28 or Uncommitted or NearbyEdit or ReReview"` | ✅ | ✅ green — 24 passed, 11 subtests |
| FRESH-02 | 2.14.1 parity grid | regression | `pytest -q test_finalize_parity_grid.py` | ✅ (fixture edit) | ✅ green — 23 passed, 760 subtests (56 named D-09 refusals, 0 unexpected) |
| FRESH-03 / SC3 | Shape 3 untracked: repro → refuse; control clears | integration | `pytest -q test_closeout_fresh.py -k untracked` | ✅ | ✅ green — `TestShape3Untracked`, `TestUntrackedCause`, `test_clearable_untracked` (7 passed); shape 3 safe refusal |
| FRESH-03 / SC3 | Shape 1 deleted-original vs D-21 control | integration | `pytest -q test_decision_continuity.py -k deleted_original` | ✅ | ✅ green — repaired in the gap closure (66-10..12): `test_shape1_deleted_original_is_reasked_at_pass2`, `test_shape1_closeout_does_not_write_on_deleted_original`; controls `test_d21_identical_copy_added_while_original_remains_keeps`, `test_shape1_pure_shift_keeps`, `test_shape1_copy_written_by_the_same_change_reasks_control` (these 5: 5 passed, 12 subtests, 0 xfailed, on 475b2e32) |
| FRESH-03 / SC3 | Shape 1 through the real fences and Close out, both kinds | integration | `pytest -q test_worktree_snap.py test_closeout_fresh.py -k Shape1` | ✅ | ✅ green — `TestShape1ThroughFences`, `TestShape1ThroughFencesRange`, `TestShape1Clearable` (10 passed, 4 subtests, on 475b2e32) |
| FRESH-03 / SC3 | Shape 1 differentials vs literal 2.15.0 (collect output; relocation) | two-sided differential | `pytest -q test_worktree_snap.py test_decision_continuity.py -k "DifferentialV215"` | ✅ | ✅ green — `TestCollectDifferentialV215`, `TestShape1DifferentialV215` (7 passed, 38 subtests, on 475b2e32); only `shape1_kept`, `shape1_edited`, `no_evidence_shape1`, `no_evidence_shift` differ |
| FRESH-03 / SC3 | Shape 1 removed lines for special names (review CR-01): non-ASCII names listed under their real names; names git still quotes and non-UTF-8 names make the removed lines unknown (re-ask) | integration (real git) | `pytest -q test_worktree_snap.py -k "QuotedNamesCR01 or RemovedRiskyInputs"` | ✅ | ✅ green — `TestQuotedNamesCR01` (5 passed), `TestRemovedRiskyInputs` (10 passed), on fa5afc55 |
| FRESH-03 / SC3 | Non-ASCII name difference vs literal 2.15.0 (owner-accepted 2026-11-19); still-quoted name keeps the first two lines identical | two-sided differential | `pytest -q test_worktree_snap.py -k QuotedNamesDifferentialV215` | ✅ | ✅ green — `TestQuotedNamesDifferentialV215` (2 passed, on fa5afc55): `test_non_ascii_name_intended_second_line_difference`, `test_still_quoted_name_first_two_lines_identical_third_empty` |
| FRESH-03 / SC3 | Parser quote/tab/no-newline/U+FFFD mutants (review WR-02, M6-M10) | mutation | `pytest -q test_worktree_snap.py -k QuoteAndBodyMutants` | ✅ | ✅ green — `TestQuoteAndBodyMutants` (5 passed, on fa5afc55) |
| FRESH-03 / SC3 | WR-01 neighbour re-ask (owner-accepted 2026-11-19): a decision 3 lines from the relocated line is re-asked, one 20 lines away keeps; moved-record-only mutant and never-force mutant both fail the lock | integration + mutation | `pytest -q test_decision_continuity.py -k "test_wr01_neighbour or trips_the_neighbour_lock"` | ✅ | ✅ green — `test_wr01_neighbour_of_forced_reask_is_reasked_owner_accepted`, `test_mutant_moved_record_only_trips_the_neighbour_lock`, `test_mutant_a_never_forces_trips_the_neighbour_lock` (3 passed, 6 subtests, on fa5afc55) |
| FRESH-03 / SC3 | Shape 2 covering-order: repair or committed counterexample | integration | `pytest -q test_decision_continuity.py -k covering_order` | ✅ | ✅ green — `TestShape2CoveringOrder` (4 passed, 18 subtests); shape 2 repaired (75e4a1da) |
| SC4 | Scorer replay vs 2.15.0 identical | replay | `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>/replay-66.md` | ✅ tool | ✅ green — 170 runs compared, 0 differing, on candidate cf1ea0bd (66-REPLAY.md, offline); re-run on fa5afc55 (2026-11-19): 170 compared, 0 differing (66-REPLAY.md section 6) |
| SC4 | Finalize differential: only intended refusals differ, asserted both directions | differential | `pytest -q test_closeout_fresh.py -k only_intended` | ✅ | ✅ green — `TestOnlyIntendedDifferences` (3 passed, 390 subtests: 312 fixture runs; 76 named refusals and 2 shape 2 repair differences, all others byte-identical); on fa5afc55, `-k "DifferentialV215 or only_intended"` across the plugin scripts: 12 passed, 428 subtests |

*Status key: ⬜ = pending · ✅ = green · ❌ = red · ⚠️ = flaky*

---

## Mutation Checks (each must make a named test fail)

1. Remove the freshness call → repro test fails.
2. Forward diff (drop `-R`) → pure-shift and delete/rename tests fail.
3. Normal prefixes under `-R` → repro fails.
4. Drop `--no-renames` → `git mv` test fails.
5. Window 5 → 4 or 6 → edge tests fail.
6. Skip "file absent from reviewed tree" → untracked test fails.
7. Treat git failure / missing tree as unchanged → unverifiable test fails.
8. Freshness check before `_fix_closes` precedence → fix-obsolete control fails.
9. Always run git / always add `stale` key → differential test fails.
10. Removed-lines helper mutants (66-10, M1-M5: `+` lines, new-side numbers, `+++` path, body line read as header, `{}` for unknown) → named `TestRemovedFromDiff` / `TestCollectRemoved` tests fail.
11. Forced re-ask rule mutants (66-11, Ma-Mg: never force, empty read as `{}`, force every move, look up the relocated line, pair into `changed_line_ranges`, pairs replace the map, member moves not recorded) → `TestForcedReaskMutants` bodies fail.
12. Fence-wiring mutants (66-12: forced re-ask off; printed evidence not threaded, `NOTHING_REMOVED` instead) → `TestShape1ThroughFences` shape 1 body fails and the decision is kept.
13. Review CR-01/WR-02 parser mutants (M6-M10: still-quoted name skipped, `core.quotePath=false` dropped, trailing-tab strip dropped, `\` skip dropped, U+FFFD name accepted) → named `TestQuotedNamesCR01` / `TestRemovedRiskyInputs` tests fail (66-REVIEW-FIX.md).
14. WR-01 lock mutants (2026-11-19): forced stamp limited to the moved record (simulated in-process by patching `score._nearby_changed` so the forced one-line ranges count only at their exact line; `score.py` on disk unchanged) → the neighbour comes back `current` and `_body_neighbour` fails; forced pair never added → the moved decision and the neighbour are kept and the lock fails.

---

## Wave 0 Requirements

- [x] `plugins/vibe-check/scripts/test_closeout_fresh.py` — repro, window, unverifiable, clearable, untracked, differential, mutation tests
- [x] v2.15 materializer helper (git show d5acc19 modules into temp dir) for the differential
- [x] Re-home ~48 decision-bearing CLI fixtures (and parity-grid state) onto temp repos with a real `reviewed_tree`
- [x] Shape 1/2 reproduction fixtures in `test_decision_continuity.py`

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s (quick)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending. Not every row is green, so `nyquist_compliant` and `wave_0_complete` stay false.

**Red rows:** none. The 2026-11-18 known-limit record for shape 1 (66-07 Task 3) is superseded by the owner-chosen wider repair (gap closure 66-10..12): shape 1 is repaired, offline. The Wave 0 work itself is done (boxes above). Sign-off is left to the validation audit.

**Evidence class:** OFFLINE. No live reviewer run (GATE-08). The full suite (4706 passed, 2 xfailed, 7173 subtests, exit 0), the stdlib check (35 files, exit 0), the scorer replay (170 compared, 0 differing) and the `-k only_intended` run were done on the main checkout at candidate commit cf1ea0bd on 2026-11-18. The per-row counts above were taken on 25bcbbb1. Every commit after that touches only `.github/scripts/test_stdlib_only.py` and `docs/design/lean-v2.15/tools/`, and the cf1ea0bd full run covers every row. Gap closure: on candidate 475b2e32 (2026-11-19 UTC, clean tree) the full suite (4790 passed, 0 xfailed, 2 warnings, 7400 subtests passed in 617.94s, exit 0), the stdlib check (35 files, exit 0), the scorer replay (170 compared, 0 differing) and `-k only_intended` (3 passed, 390 subtests) were re-run; the shape 1 row counts above were taken there. See 66-REPLAY.md section 5. Review fixes and owner rulings: on candidate fa5afc55 (2026-11-19, clean tree; includes review fixes e3888c9c and cb2da984 and the WR-01 lock) the plugin suite `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider` (4340 passed, 0 xfailed, 2 warnings, 7132 subtests passed in 438.70s, exit 0; plugin scripts only, the three-root command was not re-run), the stdlib check (35 files, exit 0), the scorer replay (170 compared, 0 differing), `-k "DifferentialV215 or only_intended"` (12 passed, 428 subtests) and the byte-identity of `score.py` and `diff_ranges.py` vs d5acc19 (`git diff --quiet`, exit 0) were re-run; the counts in rows that name fa5afc55 were taken there. See 66-REPLAY.md section 6.

**Test-harness note:** the lean-v2.15 Finalize capture (`docs/design/lean-v2.15/tools/finalize_capture.py`) now runs its candidate walks on a reviewed git tree with `reviewed_tree` stamped (cf1ea0bd). Outcome fields still match the committed 2.14.1 record, and the record itself is unchanged.

**Known behaviour, not a defect:** on `--all`, an edit near (not on) a decided line makes Close out refuse once. The fresh `--all` review keeps the decision without re-asking, because that route sends no nearby ranges (D-12), so the next Close out writes. Same-line edits are re-asked. Pinned by `TestAllRouteClearable.test_all_route_refuses_then_clears`.

**Known behaviour (owner decision 2026-11-18):** a deferred or dismissed decision whose line only shifted is asked again when the removal evidence is missing: the code changed during the pass, or the prior pass recorded no reviewed tree, which also leaves the following pass without evidence. 2.15.0 kept that decision. The owner chose the re-ask on 2026-11-18 ("Re-ask them") as a deliberate, tested difference. Pinned by `test_shape1_no_removal_evidence_reasks`, `test_shape1_without_recorded_tree_reasks` and the differential scenarios `no_evidence_shape1` and `no_evidence_shift`.

**Known behaviour (owner decision 2026-11-19), non-ASCII names:** since review fix e3888c9c the since-review diff runs with `core.quotePath=false`, so `NEARBY_LINE_RANGES=` and `REMOVED_LINE_RANGES=` list files with non-ASCII names under their real names; 2.15.0 omitted them. The owner kept this as an intended difference from 2.15.0. Names git still C-quotes (quotes, backslashes, control characters) and names that are not valid UTF-8 stay unsupported and fail safe (removed lines unknown, so the moved decision is re-asked). Pinned by `TestQuotedNamesDifferentialV215::test_non_ascii_name_intended_second_line_difference`, `TestQuotedNamesCR01` and `TestRemovedRiskyInputs`.

**Known behaviour (owner decision 2026-11-19), WR-01 neighbour re-ask:** when a moved decision is force-re-asked, another deferred or dismissed decision within 5 lines of the relocated line is also asked again, even though its own code only shifted. It only over-asks and never keeps a decision silently; `score.py` is not changed to narrow it. Pinned by `test_wr01_neighbour_of_forced_reask_is_reasked_owner_accepted` (3 lines away re-asked, 20 lines away kept) and its two mutants.
