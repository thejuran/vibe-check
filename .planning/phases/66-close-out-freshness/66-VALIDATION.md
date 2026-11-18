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
| FRESH-03 / SC3 | Shape 1 deleted-original vs D-21 control | integration | `pytest -q test_decision_continuity.py -k deleted_original` | ✅ | ❌ red (FRESH-03) — shape 1 is an owner-accepted known limit, not a repair: the two `test_shape1_*_known_limit` tests are expectedFailure (command exits 0 with 2 xfailed); controls `test_d21_identical_copy_added_while_original_remains_keeps` and `test_shape1_pure_shift_keeps` pass |
| FRESH-03 / SC3 | Shape 2 covering-order: repair or committed counterexample | integration | `pytest -q test_decision_continuity.py -k covering_order` | ✅ | ✅ green — `TestShape2CoveringOrder` (4 passed, 18 subtests); shape 2 repaired (75e4a1da) |
| SC4 | Scorer replay vs 2.15.0 identical | replay | `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>/replay-66.md` | ✅ tool | ✅ green — 170 runs compared, 0 differing, on candidate cf1ea0bd (66-REPLAY.md, offline) |
| SC4 | Finalize differential: only intended refusals differ, asserted both directions | differential | `pytest -q test_closeout_fresh.py -k only_intended` | ✅ | ✅ green — `TestOnlyIntendedDifferences` (3 passed, 390 subtests: 312 fixture runs; 76 named refusals and 2 shape 2 repair differences, all others byte-identical) |

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

**Red rows:** FRESH-03 / SC3 shape 1 (`-k deleted_original`). It is an owner-accepted known limit (66-07 Task 3), not a repair, safe refusal or non-reproduction, so the FRESH-03 gate item is NOT fully satisfied offline; carried to the milestone audit. The Wave 0 work itself is done (boxes above).

**Evidence class:** OFFLINE. No live reviewer run (GATE-08). The full suite (4706 passed, 2 xfailed, 7173 subtests, exit 0), the stdlib check (35 files, exit 0), the scorer replay (170 compared, 0 differing) and the `-k only_intended` run were done on the main checkout at candidate commit cf1ea0bd on 2026-11-18. The per-row counts above were taken on 25bcbbb1. Every commit after that touches only `.github/scripts/test_stdlib_only.py` and `docs/design/lean-v2.15/tools/`, and the cf1ea0bd full run covers every row. See 66-REPLAY.md.

**Test-harness note:** the lean-v2.15 Finalize capture (`docs/design/lean-v2.15/tools/finalize_capture.py`) now runs its candidate walks on a reviewed git tree with `reviewed_tree` stamped (cf1ea0bd). Outcome fields still match the committed 2.14.1 record, and the record itself is unchanged.

**Known behaviour, not a defect:** on `--all`, an edit near (not on) a decided line makes Close out refuse once. The fresh `--all` review keeps the decision without re-asking, because that route sends no nearby ranges (D-12), so the next Close out writes. Same-line edits are re-asked. Pinned by `TestAllRouteClearable.test_all_route_refuses_then_clears`.
