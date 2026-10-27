# Phase 57: Decision continuity within closure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 57-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-25
**Phase:** 57-decision-continuity-within-closure
**Areas discussed:** What reopens a decision, Severity changes, Regrouping rows, Defer vs dismiss on reopen

---

## What reopens a decision

| Question | Options | Selected |
|----------|---------|----------|
| Line shift (code added above, flagged line unchanged) | No, keep decision (Recommended) / Yes, re-ask | No, keep decision |
| Code right around the flagged line changes | Yes, reopen (Recommended) / No, only the flagged line | Yes, reopen |
| Edit elsewhere in the same file | No (Recommended) / Yes | No |
| NV item body changes, first line same | Keep re-asking (Recommended) / Treat like ordinary findings | Keep re-asking |

## Severity changes

| Question | Options | Selected |
|----------|---------|----------|
| Band rises on unchanged code | Yes, re-ask on a rise (Recommended) / No, keep decision | Yes, re-ask on a rise |
| Band drops on unchanged code | No, keep decision (Recommended) / Yes, re-ask | No, keep decision |
| Deferred finding rises | Same as dismiss (Recommended) / Always re-ask deferred | Same as dismiss |

## Regrouping rows

| Question | Options | Selected |
|----------|---------|----------|
| Decided finding merged into a row | Ask only about the new ones (Recommended) / Dismissal covers the row / Re-ask the whole row | Ask only about the new ones |
| Decided row split | Each part keeps it (Recommended) / Re-ask each part | Each part keeps it |
| Row display of earlier decision | One short note (Recommended) / Hide it | One short note |

## Defer vs dismiss on reopen

| Question | Options | Selected |
|----------|---------|----------|
| Deferred finding resurfaces on its own | No, same as dismiss (Recommended) / Yes, resurface later | No, same as dismiss |
| Reopen card content | Earlier decision + what changed (Recommended) / Treat as brand new | Earlier decision + what changed |
| Deferred finding later fixed | Close it normally (Recommended) / Keep deferred | Close it normally |

## Claude's Discretion

- Mechanism for a decision following a shifted line; band rise/drop detection and storage; member-level coverage tracking; exact nearby window (shared with Phase 56 D-04); card wording.

## Deferred Ideas

- Timed reminders/expiry for deferred findings (new capability; declined for this phase).
