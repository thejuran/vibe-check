---
phase: 65
slug: release-gate-orchestration-equivalence-and-useful-savings
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-15
---

# Phase 65 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Gate ids G1–G12 refer to the command fences in `65-RESEARCH.md`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 (unittest-style tests); bare `pytest` only — `python3 -m pytest` fails under Homebrew 3.14 |
| **Config file** | none — always pass `-p no:cacheprovider` |
| **Quick run command** | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_finalize_inputs.py test_finalize_card.py test_cross_call_vars.py` |
| **Full suite command** | repo root, MAIN checkout (not a worktree — private recordings live only there): `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools -rs` |
| **Estimated runtime** | quick ~10 s; full ~360 s (observed 4595 passed, 0 skipped, 359.99 s) |

Run every fence as `bash -s <<'BASH' … BASH` (the Bash tool is zsh).

---

## Sampling Rate

- **After every task commit:** quick run command
- **After every plan wave:** full suite (G1b) in the main checkout
- **Before `/bm:verify-work`:** G1–G12 all green on the exact release commit C; any production-code change → new C → G1–G12 again
- **Max feedback latency:** 360 seconds

---

## Per-Task Verification Map

| Req / criterion | Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|
| GATE-04 suite | full offline suite passes on C, 0 skipped on Mac | suite | G1a + G1b | ✅ | ⬜ pending |
| GATE-04 Mac-only | D-18 five + D-20 two run and pass | suite (ids) | G2 | ✅ | ⬜ pending |
| GATE-04 replay | 170 runs, 0 differing vs v2.14.1; guardrail REGRESSED 0; manifest ok; `baseline holds` | tool | G4a–G4e | ✅ | ⬜ pending |
| GATE-04 situations | five situations match; only command lists differ | tool | G5a, G5b | ✅ | ⬜ pending |
| GATE-04 mode/recovery | every route and recovery path class passes | suite subset | G3 selector | ✅ | ⬜ pending |
| GATE-04 unexpected diff | instruction diff touches only the 9 itemised files | git | G11 | ✅ | ⬜ pending |
| GATE-05 reduction | Finalize steps and bytes both lower at C than dd8e4ab (92→85, 136114→130886, recomputed) | tool | G6 | ✅ | ⬜ pending |
| GATE-05 named growth | each review path Δ bytes == itemised D-09 sum; +2 steps per path stated | tool + table | G6 per-file fence | ✅ | ⬜ pending |
| GATE-05 safeguards | GOLDEN_DIGEST frozen; fix-verification tests pass; fingerprints 10/10 | suite + script | G7, G1 | ✅ | ⬜ pending |
| GATE-05 no cost claim | no `$`/token/cheaper/cost/billing savings claim | grep | `grep -nEi '\$[0-9]\|token\|cheaper\|cost sav\|billing' 65-RELEASE-NOTES.md` (none in size block) | ✅ | ⬜ pending |
| GATE-06 approval | smoke runs only after owner approval | file check | `grep -q '^Status: APPROVED (owner, ' 65-LIVE-SMOKE-PROPOSAL.md` | ✅ | ⬜ pending |
| GATE-06 smoke | REVIEW.md written, `review-closed` exit 0, no stop, provenance clean | live | evidence greps on 65-LIVE-SMOKE.md | ✅ | ⬜ pending |
| GATE-06 waiver | waiver text for routes not run live, signed | file check | `grep -q 'waiver: granted (owner, ' 65-SIGNOFF.md` | ✅ | ⬜ pending |
| D-07 | WR-02 reproduction recorded with a verdict (incl. 2.14.1 comparison) | script | `grep -q '^Verdict: ' 65-REPRO-WR02.md` | ❌ W0 | ⬜ pending |
| Stdlib / manifest | 34 shipped scripts stdlib-only; manifest valid | script | G8, G9 | ✅ | ⬜ pending |
| CI | offline-suite green on PR head | CI | G12 | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] D-07 WR-02 reproduction script — scratchpad only (63-REPRO pattern); enters the suite only if a fix lands, with a mutant

*Otherwise existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Model follows rewritten Finalize instructions from fresh shells | GATE-06 | needs a live model; paid | tmux-driven bounded smoke (~3 sessions) under the approved proposal; default route + Finalize only |
| Owner go/no-go | GATE-04/05/06 | product decision | 65-SIGNOFF.md plain-terms page |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 360s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
