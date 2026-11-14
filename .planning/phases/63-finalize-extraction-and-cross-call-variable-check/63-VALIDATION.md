---
phase: 63
slug: finalize-extraction-and-cross-call-variable-check
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-14
---

# Phase 63 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `63-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest.TestCase` collected by pytest 9.0.3 (bare `pytest`; `python3 -m pytest` does not work in this repo) |
| **Config file** | none (defaults) |
| **Quick run command** | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_finalize_inputs.py test_cross_call_vars.py test_finalize_card.py test_finalize_gate.py test_finalize_archive_prose.py` |
| **Full suite command** | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` (from the repo root) |
| **Equivalence command** | `python3 docs/design/lean-v2.15/tools/finalize_capture.py verify --repo . --record docs/design/lean-v2.15/baseline/finalize-situations-v2.14.1.json` → `finalize baseline matches (5 situations)`, plus the new candidate `compare` |
| **Stdlib gate** | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` |
| **Estimated runtime** | quick ~2–5 seconds; full suite under 2 minutes |

---

## Sampling Rate

- **After every task commit:** Run the quick run command
- **After every plan wave:** Run the full suite command + the equivalence command + the stdlib gate
- **Before `/bm:verify-work`:** Full suite green; capture verify green at `dd8e4ab`; candidate compare green except the named step/tally differences; CI green on the PR
- **Max feedback latency:** 10 seconds (quick run)

---

## Per-Task Verification Map

*Task IDs are assigned by the planner; rows below are keyed by requirement until plans exist.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | FINX-01 | — | N/A | unit + CLI | `pytest -q test_finalize_inputs.py -k parity` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | FINX-01 | — | N/A | integration | `finalize_capture.py compare --driver helper …` | ❌ W0 (driver) | ⬜ pending |
| TBD | TBD | TBD | FINX-01 | TBD | file paths validated and contained before git sees them | unit (git fixture) | `pytest -q test_finalize_inputs.py -k fingerprint` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | FINX-02 | TBD | bad input stops with the existing sentence; nothing written or archived; helper diagnostics not shown to the owner | unit + fresh-shell | `pytest -q test_finalize_inputs.py -k refuse; pytest -q test_finalize_card.py -k FreshShell` | ❌ W0 / rewrite | ⬜ pending |
| TBD | TBD | TBD | FINX-03 | — | N/A | fresh-shell walk | `pytest -q test_finalize_card.py -k FreshShell` | rewrite | ⬜ pending |
| TBD | TBD | TBD | FINX-04 | — | N/A | lock + mutant | `pytest -q test_finalize_card.py test_finalize_inputs.py` | rewrite | ⬜ pending |
| TBD | TBD | TBD | FINX-04 | — | N/A | prose lock + mutant | `pytest -q test_finalize_inputs.py -k prose` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | FINX-05 | — | N/A | script run (recorded) | `step_count.py --rev …`, `footprint.py --rev …`, sha256 vs `MANIFEST.json` | ✅ tools exist | ⬜ pending |
| TBD | TBD | TBD | XVAR-01 | — | N/A | lint + mutant | `pytest -q test_cross_call_vars.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | XVAR-02 | — | N/A | record + test | `pytest -q test_cross_call_vars.py -k record` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `plugins/vibe-check/scripts/test_finalize_inputs.py` — red tests for helper parity and fingerprint rules before `finalize_inputs.py` exists
- [ ] `plugins/vibe-check/scripts/test_cross_call_vars.py` — red until the check function exists; first run produces the flagged list for XVAR-02
- [ ] `HelperWalk` tests in `docs/design/lean-v2.15/tools/test_finalize_capture.py`
- [ ] Record current behaviour first (standing rule): capture verify, step and footprint figures at `dd8e4ab` and at the branch base, MANIFEST hashes

No framework install is needed.

---

## Mutation Discipline (every new lock needs a mutant that trips it)

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
| `next` vocabulary in prose == `NEXT_ACTIONS` | add or drop a value on either side → the prose lock trips |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Owner reads the plain-terms result page and gives the go before merge (D-14) | FINX-05 | Owner decision; on a fail this is the waiver page | Present the page; merge waits for the owner's answer |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
