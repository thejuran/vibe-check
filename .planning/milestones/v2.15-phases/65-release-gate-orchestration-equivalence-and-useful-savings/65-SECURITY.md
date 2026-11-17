---
phase: 65
slug: release-gate-orchestration-equivalence-and-useful-savings
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-16
---

# Phase 65 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| scratch repro → repo | WR-02 fence walks ran in temp repos / scratch cwd under `env -i` | synthetic paths only |
| agent → owner authority | Fix round, live-smoke spend, sign-off and merge are owner-only (AskUserQuestion in the main session; relayed approvals rejected) | owner rulings |
| GSD state key (shipped) | `05-state.md` GSD fence binds `.turingmind/state/format-53/${PHASE_ID}.json`; empty id now refused before the binds | saved review progress |
| live sessions → host | Three tmux sessions on a throwaway repo against a read-only snapshot at C; installed cache backed up and restored | session transcripts (hash-only in records) |
| branch → public main/tag | Close runbook: freshness, CI green, tree identity, tag on origin/main | published plugin tree |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-65-01 | Tampering | real checkout during fence walks | mitigate | Every walk runs in a `gitfixture` temp repo or scratch cwd under `env -i`; acceptance asserts `git status --porcelain -- plugins README.md docs .github` is empty | closed |
| T-65-02 | Elevation of privilege | fix-round authorization | mitigate | QUALIFYING stops the plan; `Owner go:` defaults to PENDING; only an AskUserQuestion selection in the main session sets GRANTED; relayed approvals rejected | closed |
| T-65-03 | Information disclosure | repro record | accept | Contains fence outputs from temp repos only (synthetic paths); no secrets or transcripts | closed |
| T-65-04 | Elevation of privilege | spend authorization | mitigate | Status defaults to PROPOSED; 65-06 refuses to start any session unless the line reads `Status: APPROVED (owner, …)`; relayed approvals rejected | closed |
| T-65-05 | Information disclosure | proposal file | accept | Plain-language scope and estimates only; no secrets or transcripts | closed |
| T-65-06 | Tampering | saved-progress files of other GSD phases | mitigate | Empty-id refusal before the binds (same rule as `statepath.py::_resolve_gsd`); mutant test proves the refusal is load-bearing | closed |
| T-65-07 | Tampering (input validation, ASVS V5) | 05-state.md unsafe-name guard | mitigate | Guard line left byte-identical; existing `TestStateFileGuard` bad cases must still pass | closed |
| T-65-08 | Elevation of privilege | fix-round authorization | mitigate | Task 1 gate refuses any edit unless `Owner go: GRANTED (owner, …)` is recorded | closed |
| T-65-09 | Tampering | commit C | mitigate | Explicit-path staging; acceptance asserts `git diff --name-only C^ C` is exactly the two files and `origin/main..C` under `plugins/` is only plugin.json (+ 65-03 files) | closed |
| T-65-10 | Repudiation | README claims | mitigate | Fact-check table binds each claim to evidence; size figures copied from a recount, never from a record | closed |
| T-65-11 | Information disclosure | README / commit / Dependabot note | mitigate | No tokens, emails, transcript text or local paths; Dependabot outputs quoted as status lines only | closed |
| T-65-12 | Spoofing | savings claims | mitigate | Size block grep forbids `$`, token, cheaper, cost, billing (GATE-05) | closed |
| T-65-13 | Spoofing | which code was gated | mitigate | Preamble reads C (40-hex from 65-CANDIDATE.md), asserts HEAD's tree equals C outside .planning (`git diff --quiet "$C" HEAD -- . ':(exclude).planning'`) and a clean shipped tree before every fence; revision-taking gat… | closed |
| T-65-14 | Tampering | baseline kit | mitigate | Direct sha256 vs MANIFEST.json (10 of 10), folder unchanged since d0adb5b, GOLDEN_DIGEST equal to v2.14.1 (D-06) | closed |
| T-65-15 | Repudiation | savings claim | mitigate | Figures printed by the tools at both commits; record forbids cost/billing wording (GATE-05) | closed |
| T-65-16 | Information disclosure | record | mitigate | Only summary lines and hashes; no transcript text, tokens or secrets | closed |
| T-65-17 | Elevation of privilege | live sessions | mitigate | Pre-approved tools in `--allowedTools` (Bash, Write, Edit and others) run without a prompt, so per-call declines are NOT claimed for them; `--permission-mode manual` still prompts for anything unlisted and bypass is n… | closed |
| T-65-18 | Tampering | installed plugin cache | mitigate | Verified backup before rsync; unconditional restore with verified empty diff in Task 2 step 6 | closed |
| T-65-19 | Information disclosure | transcripts | mitigate | sha256 and extracted path lines only; the Task 2 verify asserts no `.jsonl` was added since C | closed |
| T-65-20 | Spoofing | which code ran | mitigate | Sealed read-only worktree at C, two-direction parity cache, provenance count; wrong provenance = INVALID | closed |
| T-65-21 | Elevation of privilege | spend | mitigate | Task 1 refuses any session unless the proposal reads `Status: APPROVED (owner, …)` and the gate record shows G1–G11 PASS; sessions are capped at the proposal's three plus its one invalid-run retry and no further sessi… | closed |
| T-65-22 | Tampering (supply chain) | published tree and tag | mitigate | Runbook freshness assert, CI green on the PR head, tree-identity assert for `plugins/vibe-check` and `README.md` before tagging; tag `origin/main`, never the branch tip; skip complete-milestone's tag | closed (runbook text; execution evidence captured at close) |
| T-65-23 | Information disclosure | notes / sign-off | mitigate | No secrets, emails, local paths or transcript text; notes forbid planning ids; transcripts only by hash in 65-LIVE-SMOKE.md | closed |
| T-65-24 | Repudiation | sign-off and waivers | mitigate | Dated `SIGNED OFF (owner, date)` and per-item `waiver: granted (owner, date)` lines with the verbatim selection, committed | closed |
| T-65-25 | Elevation of privilege | release and merge authority | mitigate | Blocking checkpoint; relayed approvals rejected; runbook runs from the main session only | closed (runbook text; execution evidence captured at close) |
| T-65-26 | Tampering | local main realignment | mitigate | `git merge-base --is-ancestor main feat/v2.15-phase-65` before `git reset --keep origin/main`; never `--hard` | closed (runbook text; execution evidence captured at close) |
| T-65-27 | Spoofing | savings claims in public notes | mitigate | Notes grep forbids `$<digit>`, token, cheaper, cost sav, billing (GATE-05) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

Per-threat evidence (file:line, commits, re-run commands, independent mutant on `git archive b073e31` with the refusal deleted → 4 mutant-specific failures; 86 pass unmutated) is in the bm-security-auditor return of 2026-11-16, summarised here: authorization threats rest on f3f8a6b (WR-02 go) → 976e3fe/b281042, 368ba54 (smoke approval) → b804e13, 93313b8 (sign-off); cache restored with empty `diff -rq`; no `.jsonl` added since C; notes/record greps for cost/token/billing wording return 0.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-65-01 | T-65-03 | WR-02 repro record holds fence outputs from temp repos only (synthetic paths, a scratch script path and sha256); no secrets or transcript text | plan-time disposition (65-01-PLAN), verified by bm-security-auditor | 2026-11-16 |
| AR-65-02 | T-65-05 | Live-smoke proposal holds plain-language scope and a spend estimate only; no secrets or transcripts | plan-time disposition (65-02-PLAN), verified by bm-security-auditor | 2026-11-16 |

*Accepted risks do not resurface in future audit runs.*

**Observation (not a registered threat):** tracked `.planning/` files in this phase (e.g. 65-LIVE-SMOKE.md, 65-CLOSE-RUNBOOK.md, plans) contain absolute home-directory paths and ride the release PR to public `main`. This is existing practice — 118 `.planning/` files on `origin/main` already contain them — and is left to the owner; no credential, token or email is involved.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-16 | 27 | 27 | 0 | bm-security-auditor (opus) via /bm:secure-phase 65 |

Publish-time threats T-65-22, T-65-25 and T-65-26 are closed on runbook text; their execution evidence (G12 run URL, tree-identity output, tag SHA, main realignment output) is to be captured in 65-RELEASE-RECORD.md when 65-CLOSE-RUNBOOK.md runs.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-16
