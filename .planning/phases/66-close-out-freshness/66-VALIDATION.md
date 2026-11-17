---
phase: 66
slug: close-out-freshness
status: draft
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
| FRESH-01 / SC1 | 999.40 repro: defer + dismiss × {exact, nearby}: 2.15.0 writes, candidate refuses, no REVIEW.md, state unchanged | integration | `pytest -q test_closeout_fresh.py -k repro_999_40` | ❌ W0 | ⬜ pending |
| FRESH-01 / SC1 | Real prose-fence chain with uncommitted reviewed block | integration | `pytest -q test_closeout_fresh.py -k real_chain` | ❌ W0 | ⬜ pending |
| FRESH-01 / SC1 | Refusal never starts reviewers; names same-scope command; says review is paid | prose lock | `pytest -q test_finalize_card.py -k review_again` | ❌ W0 | ⬜ pending |
| FRESH-01 | D-06 delete/rename, D-07 whitespace, window edges, pure-shift keep | unit+integration | `pytest -q test_closeout_fresh.py -k window` | ❌ W0 | ⬜ pending |
| FRESH-01 | Missing/unknown baseline or git failure → fail closed | integration | `pytest -q test_closeout_fresh.py -k unverifiable` | ❌ W0 | ⬜ pending |
| FRESH-01 | Every refusal cause clearable (refuse → review → re-decide → write) | integration | `pytest -q test_closeout_fresh.py -k clearable` | ❌ W0 | ⬜ pending |
| FRESH-02 / SC2 | Unchanged code == literal v2.15 output byte-for-byte; no git call when no decision-closed record | two-sided differential | `pytest -q test_closeout_fresh.py -k differential` | ❌ W0 | ⬜ pending |
| FRESH-02 | Fix-verdict freshness | regression | `pytest -q test_finalize_inputs.py -k "Freshness or Fingerprint"` | ✅ | ⬜ pending |
| FRESH-02 | 999.28 parity + real-edit reopening | regression | `pytest -q test_worktree_snap.py test_decision_continuity.py -k "999_28 or Uncommitted or NearbyEdit or ReReview"` | ✅ | ⬜ pending |
| FRESH-02 | 2.14.1 parity grid | regression | `pytest -q test_finalize_parity_grid.py` | ✅ (fixture edit) | ⬜ pending |
| FRESH-03 / SC3 | Shape 3 untracked: repro → refuse; control clears | integration | `pytest -q test_closeout_fresh.py -k untracked` | ❌ W0 | ⬜ pending |
| FRESH-03 / SC3 | Shape 1 deleted-original vs D-21 control | integration | `pytest -q test_decision_continuity.py -k deleted_original` | ❌ W0 | ⬜ pending |
| FRESH-03 / SC3 | Shape 2 covering-order: repair or committed counterexample | integration | `pytest -q test_decision_continuity.py -k covering_order` | ❌ W0 | ⬜ pending |
| SC4 | Scorer replay vs 2.15.0 identical | replay | `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out <scratch>/replay-66.md` | ✅ tool | ⬜ pending |
| SC4 | Finalize differential: only intended refusals differ, asserted both directions | differential | `pytest -q test_closeout_fresh.py -k only_intended` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

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

- [ ] `plugins/vibe-check/scripts/test_closeout_fresh.py` — repro, window, unverifiable, clearable, untracked, differential, mutation tests
- [ ] v2.15 materializer helper (git show d5acc19 modules into temp dir) for the differential
- [ ] Re-home ~48 decision-bearing CLI fixtures (and parity-grid state) onto temp repos with a real `reviewed_tree`
- [ ] Shape 1/2 reproduction fixtures in `test_decision_continuity.py`

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

**Approval:** pending
