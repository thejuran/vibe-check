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

Task IDs are assigned by the planner; rows are keyed by requirement until plans exist.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | CI-01 | — | Stdlib scan passes on the real tree and trips on a planted third-party import | unit + mutant | `pytest -q .github/scripts/test_stdlib_only.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CI-01 | — | Workflow: push + PR→main triggers, `permissions: contents: read`, no `secrets.`, SHA-pinned actions, `fetch-depth: 0` | static YAML-text check + mutant | `pytest -q .github/scripts/test_workflow_shape.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CI-02 | — | Red on a broken test; green on the baseline and on `main` | live CI (free, no model) | `gh run list --branch <branch>` | manual-record | ⬜ pending |
| TBD | TBD | TBD | BASE-02 | — | Footprint and trace records match `footprint.py --rev v2.14.1 --json` and label every path | unit + mutant | `pytest -q docs/design/lean-v2.15/tools/test_baseline_records.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | BASE-03 | — | Committed replay and Finalize-situation fingerprints re-derive from v2.14.1 | unit + mutant | `pytest -q docs/design/lean-v2.15/tools/test_baseline_records.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | BASE-04 | — | Counting rule gives the committed 2.14.1 numbers; +1 fence / +1 literal gives +1 | unit + mutant | `pytest -q docs/design/lean-v2.15/tools/test_step_count.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | BASE-01 | — | Cost reader dedupes by message id, maps lanes by meta.json, never emits content strings | unit on synthetic fixtures + mutant | `pytest -q docs/design/lean-v2.15/tools/test_usage_fields.py` | ❌ W0 | ⬜ pending |

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
