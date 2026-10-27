# Requirements: vibe-check v2.13 Reliable fix closure and recovery

**Defined:** 2026-10-23
**Core Value:** Catch real defects in a developer's changes before they ship — with high coverage and low noise — so a reviewer who can't manually audit the code can trust the agent's output as their safety net.

**Working rule:** reproduce each failure on current code before fixing it. A path that does not reproduce is recorded and dropped — never replaced with invented work. Local tests and existing replay evidence first; any live workflow check is separately bounded and owner-approved.

Detailed source context (owner examples, file paths, repro steps): ROADMAP.md items 1–3 as of 2026-10-21, preserved in the v2.13 phase details. Phase 52 deferred-items source moved to `.planning/milestones/v2.12-phases/52-hardening-accepted-fix-harness/deferred-items.md`.

## v2.13 Requirements

### Verified fixes close (VFIX) — remaining 999.22

- [x] **VFIX-01**: Before any closure change, each closure failure path — the one-pass independent re-check limit, the reported six-row case, and `/review` unable to close a `/deep-review`-only finding — is reproduced on current code as a failing fixture; a path that does not reproduce is recorded and dropped
- [x] **VFIX-02**: After an inconclusive independent re-check, a later run retries the re-check on unchanged repaired code and closes the finding when confirmed — no dummy code change and no repeated owner confirmation
- [x] **VFIX-03**: A fix that adds code beneath an unchanged pinned line, or adds only tests (the `arrFacade` case), can be closed by eligible independent evidence without manual "fixed in <sha>" dismissal
- [x] **VFIX-04**: A Codex-origin finding can be closed by eligible independent evidence even though Codex cannot recheck its own finding
- [x] **VFIX-05**: Under `/review`, a finding raised only by a `/deep-review` agent either closes via an eligible independent recheck or shows a clear, bounded explanation of why it cannot close there
- [x] **VFIX-06**: Closure safeguards hold under regression coverage — evidence from changed code is rejected as stale, and a "still applies" verdict keeps the finding open

### Decision continuity (DECN)

- [x] **DECN-01**: A lost defer/dismiss decision on regrouping or unrelated edits is reproduced before any identity rule changes; if it does not reproduce, that is recorded and the work dropped
- [x] **DECN-02**: Owner defer/dismiss decisions survive regrouping and edits unrelated to the finding's evidence
- [ ] **DECN-03**: A decided finding reopens when its relevant evidence changes

### Clear actions and recovery (RECV) — 999.13 subset

- [ ] **RECV-01**: The "Fix all" label states what it actually does, and the card says which findings need individual decisions
- [ ] **RECV-02**: An inconclusive re-check shows a clear, bounded recovery path (what happens next run, what the owner can do now) with no automatic closure and no new manual; existing recovery guidance and rejection/orphan explanations match actual behavior

### Answers acted on (ANSR)

- [ ] **ANSR-01**: An unambiguous plain-English answer to a decision card is translated into that card's validated grammar (preserving targets and reason, bound to the current card) and the authorized fix/dismiss/close-out workflow continues without re-showing the card
- [ ] **ANSR-02**: When a reference or reason is ambiguous or missing, or the card is stale, only the missing detail is asked — no guessing, no broadening the decision, no full re-show
- [ ] **ANSR-03**: Whether finalize `fix N` still re-asks Apply/Skip is checked on current code; if it does, the decided row proceeds to fixing without re-asking (regression fixture); if not, that is recorded and not filed

## Future Requirements

None deferred from this scoping. Separate nonblocking task: 999.12 cost visibility feasibility (ROADMAP Backlog).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cost visibility / budget control (999.12) | Separate bounded local investigation; does not block this milestone |
| Broad duplicate presentation / reviewed-set rewrite | Archived 2026-10-18 with reopening conditions; outside closure path |
| Cross-repo gate consumers | Excluded from decision-continuity scope |
| Scoring retune or new reviewer lane | Not a closure/recovery problem |
| Orchestrator implementation changes | Separate plugin; cross-repo |
| Full B3 / holdout measurement campaign | v2.12 measurement deferred; paid work needs an approved bounded proposal |
| Rebuilding v2.12 initial confirmed-fix routing | Already shipped in v2.12 |
| Automatic closure without independent verification | Would weaken the core safety guarantee |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| VFIX-01 | Phase 56 | Complete |
| VFIX-02 | Phase 56 | Complete |
| VFIX-03 | Phase 56 | Complete |
| VFIX-04 | Phase 56 | Complete |
| VFIX-05 | Phase 56 | Complete |
| VFIX-06 | Phase 56 | Complete |
| DECN-01 | Phase 57 | Complete |
| DECN-02 | Phase 57 | Complete (gap closure 57-08..57-16) |
| DECN-03 | Phase 57 | In Progress (re-verification 2: same-lane re-report drops nearby stamp) |
| RECV-01 | Phase 58 | Pending |
| RECV-02 | Phase 58 | Pending |
| ANSR-01 | Phase 58 | Pending |
| ANSR-02 | Phase 58 | Pending |
| ANSR-03 | Phase 58 | Pending |

**Coverage:**
- v2.13 requirements: 14 total
- Mapped to phases: 14 (Phase 56: 6, Phase 57: 3, Phase 58: 5)
- Unmapped: 0

---
*Requirements defined: 2026-10-23*
*Last updated: 2026-10-26 after Phase 57 second gap closure (DECN-03 complete on the 57-16 gate)*
