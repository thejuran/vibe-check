# Phase 62: Baseline and continuous test run - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-13
**Phase:** 62-baseline-and-continuous-test-run
**Areas discussed:** Improvement criterion, Comparison workload, Cost note: sources and 'go', Where records live + red proof

---

## Improvement criterion

### What the improvement is measured in

| Option | Description | Selected |
|--------|-------------|----------|
| Both, either can pass | Loaded Finalize-path bytes and model-run mechanical steps; pass if at least one drops and neither grows | ✓ |
| Loaded bytes only | One number from the existing tool; a reliability gain without shrinkage would fail | |
| Model-run steps only | Counts what causes failures; needs a new counting rule; prose could grow | |
| You decide | Leave to planning | |

### How big the reduction must be

| Option | Description | Selected |
|--------|-------------|----------|
| Any real drop, no target | Measured reduction in at least one count, other not growing, identical behaviour | ✓ |
| Fixed minimum, e.g. 10% | Clear bar; pressure to trim safeguards | |
| Soft target, hard floor | Reported aspiration that never gates | |

### Whether helper code counts against the saving

| Option | Description | Selected |
|--------|-------------|----------|
| Report it, don't net it | Separate labelled "maintenance added" figure | ✓ |
| Net it against the saving | Strictest; likely fails any extraction | |
| Ignore helper size | Simplest; hides new code owned | |

### Slice matches behaviour but shows no drop

| Option | Description | Selected |
|--------|-------------|----------|
| Revert, unless you waive | Default revert; one plain-terms page; owner may keep by waiver; no automatic second attempt | ✓ |
| Revert, no exceptions | Cleanest rule | |
| One rework round, then revert | One bounded attempt first | |

**User's choice:** Recommended option on all four.
**Notes:** Footprint read before the questions: Finalize loads about 136,000 bytes across 7 files.

---

## Comparison workload

### Which paths are compared

| Option | Description | Selected |
|--------|-------------|----------|
| Record all 3, compare Finalize | Baseline all three; pass/fail on Finalize; plain/deep re-measured at release gate for no growth | ✓ |
| Compare all three | Every path gets its own before/after at Phase 63 | |
| Finalize only, everywhere | Would need BASE-02 amended | |

### Fixed Finalize comparison set

| Option | Description | Selected |
|--------|-------------|----------|
| Five named situations | Clean close; card route; one automatic rebuild; refused/failed close writes nothing; fresh-shell restart | ✓ |
| Clean close + card only | Everyday routes only | |
| You decide | Planning picks from existing tests | |

### What the pinned behavioural baseline is

| Option | Description | Selected |
|--------|-------------|----------|
| Offline record at the tag | Suite result, replay output, gate decisions and report text for the five situations, fingerprinted | ✓ |
| Suite + replay only | No separate Finalize outputs | |
| Add one live run | Paid; needs an approved proposal | |

### Path with no recorded 2.14.x session

| Option | Description | Selected |
|--------|-------------|----------|
| Label the gap, use the declared list | "observed" vs "declared, not observed"; no session run | ✓ |
| Use older recorded sessions | Marked with version; may mislead | |
| Propose a live run for gaps | Paid proposal per gap | |

**User's choice:** Recommended option on all four.

---

## Cost note: sources and 'go'

### Which records may be inspected

| Option | Description | Selected |
|--------|-------------|----------|
| Both; only totals leave the logs | Repo archives and Claude Code session logs; aggregates only; nothing copied into the repo | ✓ |
| Repo archives only | Most private; likely immediate no-go | |
| Both, plus ccusage-style tools | Third-party tool reads private logs | |

### Bar for "trustworthy"

| Option | Description | Selected |
|--------|-------------|----------|
| Present, attributable, consistent | All three; labels measured/estimated/missing; no dollars | ✓ |
| Present is enough | More fields "available"; attribution may be wrong | |
| You decide | Planning sets the bar | |

### What a "go" commits to

| Option | Description | Selected |
|--------|-------------|----------|
| Nothing built; backlog it | Smallest report filed as a backlog item; Phase 65 may quote existing-session usage | ✓ |
| Build the small report in v2.15 | New capability; roadmap change | |
| Use it as a third criterion | Needs comparable live runs | |

### How much digging

| Option | Description | Selected |
|--------|-------------|----------|
| One pass, fixed sample, then stop | One plan; up to ~5 recent sessions per path plus repo archives | ✓ |
| Every recorded session | All 39 sessions and all archives | |
| You decide | Planning sets sample size | |

**User's choice:** Recommended option on all four.
**Notes:** The one archived transcript sampled during the scout carried no usage fields.

---

## Where records live + red proof

### Where the baseline and cost note live

| Option | Description | Selected |
|--------|-------------|----------|
| Baseline public, cost note too | Baseline under design evidence; note with the phase records; aggregates only | ✓ |
| Baseline public, cost note local | Note not committed | |
| Public note, numbers redacted | Figures in a local-only appendix | |

### Red proof on a public repo

| Option | Description | Selected |
|--------|-------------|----------|
| Throwaway branch, no PR, deleted after | One failing commit; run link saved; branch deleted | ✓ |
| Draft PR, closed unmerged | Also proves the PR trigger | |
| Both push and PR proofs | Most complete | |

### Proving main green

| Option | Description | Selected |
|--------|-------------|----------|
| Green on branch, then on main after merge | Byte-identical proof before merge; main's first run recorded as the closing step | ✓ |
| Small CI-only PR first | Second PR; breaks one-PR-per-phase | |
| Branch green is enough | Not literally CI-02 | |

### Environment-only failures on Linux runners

| Option | Description | Selected |
|--------|-------------|----------|
| Fix the setup, never skip | Reproduce first; no skips; no plugin code change; stop and ask if plugin code would need to change | ✓ |
| Run on a Mac runner instead | Hides Linux-only problems | |
| Allow a named skip list | Standing check covers less | |

**User's choice:** Recommended option on all four.

---

## Claude's Discretion

- Workflow details (Python version, runner, invocation, file name), subject to the triggers needed by the red proof and PRs to `main`.
- Which existing check is "the stdlib-only check".
- Baseline folder names, fingerprint method, capture method for the five Finalize outputs.
- Wording of the go/no-go note and of the model-run-steps counting rule.
- Plan count and split (cost note is one plan).

## Deferred Ideas

- Smallest useful usage report (backlog item if the note says "go").
- Token usage as a pass/fail measure (needs an approved paid proposal).
- Branch protection requiring the CI check.
- A live Finalize capture on 2.14.1.
