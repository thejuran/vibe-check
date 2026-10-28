# Phase 58: Clear actions, recovery and answers acted on - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-27
**Phase:** 58-clear-actions-recovery-and-answers-acted-on
**Areas discussed:** Acting on plain English, Asking only what's missing, "Fix all" label, Recovery guidance + bug C

---

## Acting on plain English

| Option | Description | Selected |
|--------|-------------|----------|
| Act now, show translation | Print "Read your answer as: …" and carry it out; no confirm card | ✓ |
| One quick yes/no first | Show the translation, ask "Go ahead?" | |
| Confirm only risky parts | Confirm only critical/warning dismiss/defer | |

| Option | Description | Selected |
|--------|-------------|----------|
| Anything matching one set | Numbers, titles/title words, card-supported descriptions; counts must match | ✓ |
| Numbers and titles only | "the 7 fixed rows" would need a follow-up | |

| Option | Description | Selected |
|--------|-------------|----------|
| Use it, quoted from your words | Implied why becomes the reason, keeping the owner's wording | ✓ |
| Always ask for a reason | Never derive a reason | |
| Use the Reason dropdown | Q2 on Finalize, else ask | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fix-loop + Finalize cards | Both typed-decision cards | ✓ |
| Fix-loop card only | Only where the bug was seen | |

**Notes:** none beyond selections.

---

## Asking only what's missing

| Option | Description | Selected |
|--------|-------------|----------|
| Hold all, ask the gap | Record nothing until the gap is answered; act on the whole answer together | ✓ |
| Do the clear part now | Act on the clear part, then ask | |

| Option | Description | Selected |
|--------|-------------|----------|
| Short question, choices | Candidate rows / reason choices as buttons; no full card | ✓ |
| Plain-text question | Typed reply only | |

| Option | Description | Selected |
|--------|-------------|----------|
| Re-map by finding, ask if unsure | Map stale references by identity; ask only about unmapped ones | ✓ |
| Always ask on a stale card | Never re-map | |

| Option | Description | Selected |
|--------|-------------|----------|
| One more try, then card | One follow-up per gap, then the full card once with a note | ✓ |
| Keep asking the gap | Unbounded narrowing | |

**User's addition (free text):** "one other clarification -- often there is a recommendation of what to do in the 'bottom Line' section of the report - that should be a choice I can pick"

| Option | Description | Selected |
|--------|-------------|----------|
| Card shows it as row grammar | Suggestion line under the list; type "bottom line" to take it; no button change | ✓ |
| Replace a button with it | Swap an existing option for "Follow the Bottom line" | |
| Just accept typing it | No card hint | |

---

## "Fix all" label

| Option | Description | Selected |
|--------|-------------|----------|
| Relabel + name the left-out rows | Keep behavior; description names the excluded NV rows by number; test-locked | ✓ |
| Make Fix all include them | Undo the v2.12 by-number rule | |

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, same wording rule | Apply all & rerun gets the same treatment; NV note folds in | ✓ |
| Leave it as is | Only fix Finalize | |

---

## Recovery guidance + bug C

| Option | Description | Selected |
|--------|-------------|----------|
| Per-reason, two parts | "Next run: …" + "You can: …" per reason, test-checked | ✓ |
| Fix only the wrong ones | Keep the shared tail, patch false cases | |

| Option | Description | Selected |
|--------|-------------|----------|
| Report + cards + README | Reconcile everything that disagrees with code; no new page | ✓ |
| Report and cards only | Runtime text only | |

| Option | Description | Selected |
|--------|-------------|----------|
| Trace + test, no live run | Static trace + lock test; record verdict | ✓ |
| Also one bounded live run | Needs a separately approved, priced proposal | |

---

## Claude's Discretion

- Prose-only vs helper-assisted translation (strict parser stays the gate)
- Exact echo, follow-up and fallback wording; per-reason recovery wording
- Which row markers count as card-supported descriptions
- Whether the "Fix all" label string itself changes (constants + tests together)
- How tests exercise LLM-performed translation

## Deferred Ideas

- One-click "Follow the Bottom line" button
- Bounded live run for bug C (needs an approved proposal)
- Broader 999.13 docs reconciliation (MAINTENANCE.md)
