# Phase 56: Verified fixes close - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 56-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-23
**Phase:** 56-verified-fixes-close
**Areas discussed:** Who may confirm a fix, What triggers a re-check, Retry after inconclusive, /review vs deep-only

Pre-discussion: Explore scout mapped current closure mechanics (line-pinned evidence; originating-agent-only recheck; persisted findings unclosable; NV-only independent ladder with previous-pass limit; Codex never rechecks; /review lacks deep lanes).

## Who may confirm a fix
| Question | Options | Selected |
|---|---|---|
| Confirmer when originating agent can't recheck | v2.12 ladder / Same-domain only / Original agent only | v2.12 ladder (rec.) |
| Closure bar | Verdict + fresh code / Also require tests pass | Verdict + fresh code (rec.) |
| Visibility of auto-closed findings | Listed as closed / Ask me once to accept | Listed as closed (rec.) |

## What triggers a re-check
| Question | Options | Selected |
|---|---|---|
| Trigger when pinned line unchanged | Nearby change or fix commit / Any change to the file / Only when I ask | Nearby change or fix commit (rec.) |
| Hand fixes outside fix agent | Yes, same path / Fix-agent fixes only | Yes, same path (rec.) |
| Tests-only fix evidence | Code + the new tests / Treat like any change | Code + the new tests (rec.) |

## Retry after inconclusive
| Question | Options | Selected |
|---|---|---|
| Retries while code unchanged | Every run until settled / Two more tries / One more try | Every run until settled (rec.) |
| Code changes after inconclusive | Fresh start / Stays open for you | Fresh start (rec.) |
| Re-check after "still applies" | Only after new changes / Never automatically | Only after new changes (rec.) |

## /review vs deep-only
| Question | Options | Selected |
|---|---|---|
| /review confirms deep-only findings | Yes, all via ladder / Codex yes, deep lanes no / None — explain only | Yes, all via ladder (rec.) |
| Wording when no eligible reviewer | Reason + how to close / Keep today's wording | Reason + how to close (rec.) |

## Claude's Discretion
- Nearby window size; test-file association; state storage shape; six-row fixture recovery vs synthesis; exact wording.

## Deferred Ideas
- Structured "fixed-in" reason; wider evidence binding (Phase 57 territory); broad recovery wording (Phase 58).
