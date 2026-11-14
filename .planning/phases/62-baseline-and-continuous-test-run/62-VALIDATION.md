---
phase: 62
slug: baseline-and-continuous-test-run
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-13
---

# Phase 62 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `62-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | stdlib `unittest.TestCase`, run with pytest 9.0.3 |
| **Config file** | none (repo-wide). Do not add one: it would change collection for the existing suite. |
| **Quick run command** | `cd <dir> && pytest -q -p no:cacheprovider test_<tool>.py` (new tools under `docs/design/lean-v2.15/tools/` and `.github/scripts/`) |
| **Full suite command** | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` |
| **Estimated runtime** | ~200 seconds (full suite, owner Mac) |

Use bare `pytest`, never `python3 -m pytest` (fails locally). The test-verify allowlist rejects `python3 -m unittest`. Wrap multi-line shell in `bash -s <<'BASH'`.

---

## Sampling Rate

- **After every task commit:** Run the quick command for the touched tool
- **After every plan wave:** Run the full suite command
- **Before `/bm:verify-work`:** Full suite green locally, phase-branch CI green, red-proof run recorded, `main` run green
- **Max feedback latency:** ~200 seconds

---

## Per-Task Verification Map

Task IDs are `<phase>-<plan>-<task>`, assigned by the planner on 2026-11-13.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 62-01-01 | 01 | 1 | CI-01 | T-62-04, T-62-05 | Stdlib scan passes on the real tree (33 files, gitfixture.py included) and trips on a planted third-party import | unit + mutant | `pytest -q -p no:cacheprovider .github/scripts/test_stdlib_only.py` | ❌ W0 | ⬜ pending |
| 62-01-02 | 01 | 1 | CI-01 | T-62-01, T-62-02, T-62-03 | Left-out list equals the recorded five (D-18); a suite log without exactly 5 deselected trips | unit + mutant | `pytest -q -p no:cacheprovider .github/scripts/test_left_out_guard.py` | ❌ W0 | ⬜ pending |
| 62-02-01 | 02 | 1 | CI-01 | T-62-07..T-62-11 | Workflow-shape locks written first (RED) | static YAML-text check + mutant | `pytest -q -p no:cacheprovider .github/scripts/test_workflow_shape.py` (expected red until 62-02-02) | ❌ W0 | ⬜ pending |
| 62-02-02 | 02 | 1 | CI-01 | T-62-07..T-62-11, T-62-SC | Workflow: push + PR→main triggers, `permissions: contents: read`, no `secrets.`, SHA-pinned actions, `fetch-depth: 0`, guarded deselects | static YAML-text check + mutant | `pytest -q -p no:cacheprovider .github/scripts/test_workflow_shape.py` | ❌ W0 | ⬜ pending |
| 62-03-01 | 03 | 1 | BASE-04 | T-62-13 | Counting rule: +1 fence / +1 paste site / +1 Write phrase gives +1 | unit + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_step_count.py` | ❌ W0 | ⬜ pending |
| 62-03-02 | 03 | 1 | BASE-04 | T-62-14, T-62-15 | Committed 2.14.1 step counts re-derive; CRITERION.md figures equal the record | unit + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_step_count.py` | ❌ W0 | ⬜ pending |
| 62-04-01 | 04 | 1 | BASE-03 | T-62-17, T-62-20 | Pinned-tree driver; clean-close and card-first outcomes | unit | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_finalize_capture.py` | ❌ W0 | ⬜ pending |
| 62-04-02 | 04 | 1 | BASE-03, BASE-04 | T-62-18, T-62-19 | Five Finalize situations re-derive from v2.14.1; tamper and driver mutants | unit + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_finalize_capture.py` | ❌ W0 | ⬜ pending |
| 62-05-01 | 05 | 1 | BASE-02 | T-62-25 | Footprint record recounts from git at v2.14.1; proxies held apart | unit + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_path_records.py` | ❌ W0 | ⬜ pending |
| 62-05-02 | 05 | 1 | BASE-02 | T-62-22, T-62-23, T-62-24 | Every path labelled observed or declared-not-observed; never-echo | unit on synthetic fixtures + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_path_records.py` | ❌ W0 | ⬜ pending |
| 62-06-01 | 06 | 1 | BASE-01 | T-62-27, T-62-28, T-62-30 | Cost reader dedupes by message id, maps lanes by meta.json, never emits content strings | unit on synthetic fixtures + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_usage_fields.py` | ❌ W0 | ⬜ pending |
| 62-06-02 | 06 | 1 | BASE-01 | T-62-29, T-62-31 | Go/no-go note: verdict, D-11 field table, no price, no private path | document check (grep) | verify command in 62-06-PLAN.md Task 2 | n/a | ⬜ pending |
| 62-07-01 | 07 | 2 | BASE-03 | T-62-33, T-62-36, T-62-37 | Replay fingerprints for both recording conditions; manifest tamper mutants; no skip | unit + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_baseline_records.py` | ❌ W0 | ⬜ pending |
| 62-07-02 | 07 | 2 | BASE-03, BASE-02, BASE-04 | T-62-34, T-62-35 | Committed suite/replay records and manifest re-derive; baseline page figures equal the records | unit + mutant | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools` | ❌ W0 | ⬜ pending |
| 62-08-01 | 08 | 3 | CI-02 | T-62-40 | Tree identity with v2.14.1; D-18 reproductions; local run of the exact CI commands | local run + record check | verify command in 62-08-PLAN.md Task 1 | manual-record | ⬜ pending |
| 62-08-02 | 08 | 3 | CI-02 | T-62-40, T-62-43, T-62-44 | Green on the phase branch, or stop and escalate (D-17) | live CI (free, no model) | `gh run list --workflow offline-suite.yml --branch feat/v2.15-phase-62` | manual-record | ⬜ pending |
| 62-08-03 | 08 | 3 | CI-02 | T-62-39, T-62-41 | Red on one broken test on `ci-red-proof`; branch deleted | live CI (free, no model) | `gh run list --workflow offline-suite.yml --branch ci-red-proof` | manual-record | ⬜ pending |
| 62-09-01 | 09 | 4 | CI-02 | T-62-49 | Pull request green on its final commit | live CI (free, no model) | `gh pr list --head feat/v2.15-phase-62 --state all` | manual-record | ⬜ pending |
| 62-09-02 | 09 | 4 | BASE-01, CI-02 | T-62-45 | Owner records go or no-go and merges | owner checkpoint | — | manual | ⬜ pending |
| 62-09-03 | 09 | 4 | CI-02 | T-62-46, T-62-47, T-62-48 | `main`'s first run recorded; phase ticked only if green | live CI (free, no model) + planning-file check | `gh run list --workflow offline-suite.yml --branch main --event push` | manual-record | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.github/scripts/test_stdlib_only.py` — CI-01 stdlib lock + mutant
- [ ] `.github/scripts/test_workflow_shape.py` — CI-01 trigger/permission/pin locks + mutants
- [ ] `docs/design/lean-v2.15/tools/test_*.py` — BASE-02/03/04 fingerprint and counting-rule locks + mutants
- [ ] Synthetic JSONL fixtures for the cost reader (never real logs)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Phase-branch run green, throwaway-branch run red, first `main` run green | CI-02 | Result lives on GitHub Actions, not in the repo | Record run URLs and conclusions from `gh run list` for each branch in the phase records |
| Go/no-go note reviewed by owner | BASE-01 | Owner decision | Owner reads the note and records go or no-go |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 200s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
