---
phase: 63
slug: finalize-extraction-and-cross-call-variable-check
status: draft
nyquist_compliant: true
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

*Task IDs are `<plan>-T<n>`. Commands run from the repo root.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 63-01-T1 | 01 | 1 | FINX-05 | — | N/A | script run (recorded) | `step_count.py --rev dd8e4ab…`, `footprint.py --rev dd8e4ab…`, capture `verify`, sha256 vs `MANIFEST.json` → `63-COUNTS.md` `## Before` | ✅ tools exist | ⬜ pending |
| 63-01-T2 | 01 | 1 | FINX-01 | T-63-01..04 | file names validated and contained before git sees them; omit on any difference | unit (git fixture) + mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_inputs.py` | ❌ created by this task (test first) | ⬜ pending |
| 63-02-T1 | 02 | 2 | FINX-01 | T-63-08 | result assembled only from the three existing library calls | unit + parity + mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_inputs.py -k "parity or next or mutant"` | extends 63-01 file | ⬜ pending |
| 63-02-T2 | 02 | 2 | FINX-02 | T-63-05..07 | bad input → fixed exit code, nothing written, no owner text, no path/title echoed | CLI subprocess + mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_inputs.py` | extends 63-01 file | ⬜ pending |
| 63-03-T1 | 03 | 1 | XVAR-01 | T-63-09 | N/A | lint unit + mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_cross_call_vars.py` | ❌ created by this task (test first) | ⬜ pending |
| 63-03-T2 | 03 | 1 | XVAR-01 | T-63-09, T-63-10 | exceptions by name, shrink-only | whole-tree lint + live-file mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_cross_call_vars.py` | same file | ⬜ pending |
| 63-04-T1 | 04 | 2 | XVAR-02 | T-63-11, T-63-12 | N/A | fresh-shell repro fixtures with control | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_cross_call_vars.py -k Repro63` | same file | ⬜ pending |
| 63-04-T2 | 04 | 2 | XVAR-02 | T-63-13 | every flagged place recorded before change | record lock + mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_cross_call_vars.py -k Record` | same file | ⬜ pending |
| 63-05-T1 | 05 | 3 | FINX-04 | T-63-14 | no safeguard removed without a replacement | scratch-copy red list (recorded) | ledger section greps (see plan verify) | n/a (record) | ⬜ pending |
| 63-05-T2 | 05 | 3 | FINX-04 | T-63-14, T-63-15 | replacement with tripping mutant lands first | unit + mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_inputs.py plugins/vibe-check/scripts/test_carry_state.py plugins/vibe-check/scripts/test_score.py` | ✅ | ⬜ pending |
| 63-06-T1 | 06 | 4 | FINX-02, FINX-03 | T-63-16..19 | fail closed on unsubstituted switches; nothing written on failure | fresh-shell walk + text locks (RED) | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_card.py -k FreshShell` (expected red until T2) | rewrite | ⬜ pending |
| 63-06-T2 | 06 | 4 | FINX-01, FINX-02, FINX-03, FINX-04 | T-63-16..20 | owner sentences byte-identical; diagnostics kept in a file | fresh-shell walk + text locks (GREEN) | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_inputs.py plugins/vibe-check/scripts/test_cross_call_vars.py plugins/vibe-check/scripts/test_finalize_card.py plugins/vibe-check/scripts/test_finalize_gate.py plugins/vibe-check/scripts/test_finalize_archive_prose.py` | ✅ | ⬜ pending |
| 63-07-T1 | 07 | 5 | FINX-04 | T-63-22 | moved text proven identical | sha256 lock + mutants | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_card.py` | ✅ | ⬜ pending |
| 63-07-T2 | 07 | 5 | FINX-01 | T-63-21, T-63-23 | report failure stops before any write | fresh-shell walk + text locks | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_finalize_card.py plugins/vibe-check/scripts/test_finalize_inputs.py` | ✅ | ⬜ pending |
| 63-08-T1 | 08 | 6 | FINX-01, FINX-02, FINX-03 | T-63-24, T-63-25 | baseline record untouched | integration (five situations) + mutants | `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_finalize_capture.py`; `finalize_capture.py verify …` → `finalize baseline matches (5 situations)` | extends existing file | ⬜ pending |
| 63-08-T2 | 08 | 6 | FINX-01 | T-63-26 | argued mappings stated as such | integration | `finalize_capture.py compare --repo . --record …/finalize-situations-v2.14.1.json --driver helper --root plugins/vibe-check` | ❌ created by this task | ⬜ pending |
| 63-09-T1 | 09 | 7 | FINX-05 | T-63-28, T-63-29 | figures from named commits; no reliance on WR-02/WR-03 | script run (recorded) | `step_count.py --rev <X>` recomputed against `63-COUNTS.md` (see plan verify) | ✅ tools exist | ⬜ pending |
| 63-09-T2 | 09 | 7 | XVAR-02 | T-63-30 | owner decides the fix/pin split | manual (owner decision) + record check | `## Owner decision` rows checked against `EXCEPTIONS` ids (see plan verify) | n/a | ⬜ pending |
| 63-10-T1 | 10 | 8 | XVAR-02 | T-63-31..33 | review behaviour unchanged beyond the repair | fresh-shell fixtures + reverse run + lint | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts/test_cross_call_vars.py` | ✅ | ⬜ pending |
| 63-10-T2 | 10 | 8 | FINX-05 | T-63-34 | named growth itemised | script run (recorded) | `step_count.py --rev <E>` recomputed; `finalize_capture.py compare … --commit <E>` | ✅ | ⬜ pending |
| 63-11-T1 | 11 | 9 | FINX-05, XVAR-01 | T-63-35, T-63-37, T-63-38 | page equals the records; CI green on the PR | record check + CI | page section greps; `gh pr checks` all pass (see plan verify) | n/a | ⬜ pending |
| 63-11-T2 | 11 | 9 | FINX-05 | T-63-36 | merge waits for the owner | manual (owner go) | `## Owner decision` present in `63-RESULT.md` | n/a | ⬜ pending |
| 63-11-T3 | 11 | 9 | FINX-05 | T-63-36, T-63-38 | truthful planning files | record check | merge, branch deletion, backlog and STATE freshness checks (see plan verify) | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `plugins/vibe-check/scripts/test_finalize_inputs.py` — red tests before `finalize_inputs.py` exists (63-01-T2, test-first commit)
- [ ] `plugins/vibe-check/scripts/test_cross_call_vars.py` — red until the check functions exist; first run produces the flagged list for XVAR-02 (63-03-T1/T2)
- [ ] `HelperWalk` tests in `docs/design/lean-v2.15/tools/test_finalize_capture.py` (63-08-T1; they need the rewritten instructions, so they land in wave 6, test-first inside that task)
- [ ] Record current behaviour first (standing rule): capture verify, step and footprint figures at `dd8e4ab` and at the branch base, MANIFEST hashes (63-01-T1)

No framework install is needed. There is no separate Wave 0 plan: each new test file is created test-first by the first task that uses it.

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
| Owner confirms which flagged cross-call places are fixed and which pinned (D-08, D-17) | XVAR-02 | Classing a silently ignored setting under the four-class rule is the owner's call | 63-09 Task 2: present `63-REPRO.md` split and per-fix additions; record the answer by id |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [ ] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
