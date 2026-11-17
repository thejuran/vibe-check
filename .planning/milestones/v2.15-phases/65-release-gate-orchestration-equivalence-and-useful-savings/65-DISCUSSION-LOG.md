# Phase 65: Release gate — orchestration equivalence and useful savings - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 65-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-15
**Phase:** 65-release-gate-orchestration-equivalence-and-useful-savings
**Areas discussed:** Live check or waiver, Review-path growth, Carried items first, Failures & release notes

---

## Live check or waiver

| Option | Description | Selected |
|--------|-------------|----------|
| Bounded smoke | As 2.14: proposal ~3 sessions, est. $20–30, owner approves first, tmux-driven | ✓ |
| Waiver, no live run | Ship on offline proof; record states Finalize prose not run live | |

| Option (smoke scope) | Description | Selected |
|--------|-------------|----------|
| Default + Finalize | review → decide → --finalize writes REVIEW.md; fix loop/--all on offline proof | ✓ |
| Add fix loop | ~4 sessions, est. $26–36 | |
| Add fix loop + --all | ~5 sessions, est. $32–45 | |

**User's choice:** Bounded smoke; default + Finalize.

---

## Review-path growth

| Option | Description | Selected |
|--------|-------------|----------|
| Accept as named growth | Itemised by file/fix; check reworded to "no growth beyond named items" | ✓ |
| Block until offset | Trim shared files back to 2.14.1 size | |

| Option (notes) | Description | Selected |
|--------|-------------|----------|
| Both, side by side | Finalize drop and ~0.6% review-path growth in one size block | ✓ |
| Finalize saving only | Growth only in the release record | |

**Notes:** Resolves the conflict with Phase 62 D-06 ("prove they did not grow").

---

## Carried items first

| Option (999.34 WR-02/WR-03) | Description | Selected |
|--------|-------------|----------|
| Bypass + carry | Recount both commits directly, as Phase 63 D-13 | ✓ |
| Fix them first | Tighten both checks with mutants | |

| Option (999.38) | Description | Selected |
|--------|-------------|----------|
| Reproduce WR-02, carry rest | One offline repro; qualifies for fix round only if data loss/wrong close | ✓ |
| Carry all as-is | No new work | |
| Fix WR-02 regardless | Guard empty phase id before release | |

---

## Failures & release notes

| Option (on failure) | Description | Selected |
|--------|-------------|----------|
| One round, hard cap | As 2.14 D-05/D-06 | ✓ |
| Stop and ask | Every qualifying failure to owner first | |

| Option (differences) | Description | Selected |
|--------|-------------|----------|
| In notes + record | "Same as 2.14.1 except:" + 3–6 Known limits | ✓ |
| Record only | Notes say "same behaviour" only | |

| Option (sign-off) | Description | Selected |
|--------|-------------|----------|
| One plain-terms page | As 2.14 D-09; ledgers linked | ✓ |
| Page + walk-through | Also walk through each item | |

---

## Claude's Discretion

- Smoke throwaway-repo design and pass checks; grouping of mode/recovery checks; release record/sign-off/notes wording; version-bump/release-PR mechanics; plan split.

## Deferred Ideas

- 999.34 WR-02/WR-03 tightening; 999.38 remainder; live runs of fix loop and `--all`.
