# Codex Adversarial Reviewer Efficacy Test — RESULTS (v2.2, Phase 06)

**Verdict: `EFF-01: PASS` · `EFF-02: PASS`** — Codex ran and was attributed, cross-confirm (+10)
fired on the planted defect, and a de-authenticated run degraded cleanly to native-only.

Run on a throwaway branch (`efftest/codex-v2.2`) in this Codex-authenticated repo, against a single
committed planted-defect file (`plugins/vibe-check/_efftest/handler.py`) reviewed via
`/deep-review --base main` (branch mode). The branch is never merged to main; the planted file never
ships. Scored deterministically with `templates/scoring.md`
(`score = agent_confidence + 20 [in_diff] + 10 [cross-confirm] + severity_weight`; `/deep-review`
surfaces at score ≥ 70).

## The planted fixture

`get_user_by_email(conn, email)` with two high-agreement defects:
- **D1 (line 13):** f-string SQL injection — `f"SELECT … WHERE email = '{email}'"` (CWE-89).
- **D2 (line 16-17):** unguarded `None` deref of `cursor.fetchone()` (CWE-476) — backup cross-confirm site.

## EFF-01 — Codex actually ran and its findings are attributed

| Evidence | Observed |
|----------|----------|
| Disclosure line printed at kickoff | `▶ Running Codex adversarial review in parallel (GPT-5-codex, ~1–3 min, deep-review only)…` |
| Job visible in `/codex:status` | `review-mqode6iz-b176o8 \| kind: adversarial-review \| 2026-06-21T22:40:35Z` |
| Codex result | `verdict: needs-attention`, exit 0, no timeout, 2 findings |
| Findings attributed `agent: codex-adversarial` in merged report | **2** |

## EFF-02a — cross-confirm (+10, dual attribution) fired on the planted defect

| Site | Native agents | Codex title (line) | Merged attribution | Bonus | Band |
|------|---------------|--------------------|--------------------|-------|------|
| **D1 SQLi** (line 13) | security ("SQL injection via f-string interpolation"), language-python, bugs | "Email lookup is directly SQL injectable" (line 12) | `[security, language-python, bugs, codex-adversarial]` | **+10** | Critical (100) |
| **D2 null-deref** (line 16-17) | bugs, language-python, security | "Missing-result path crashes on None row" (line 14) | `[bugs, language-python, security, codex-adversarial]` | **+10** | Critical (100) |

Merge rule **as it ran in v2.2 (Phase 6)**: `(file, line ±2)` + title-substring ("sql"/"inject"). Both
sites cross-confirmed on the first authenticated run — no D-06 weak-run fallback needed. Hard structured
gate (≥1 codex-adversarial finding AND ≥1 dual-attribution +10) passed fail-closed.

> **Mechanism note (added v2.4):** this run predates ROBUST-02. As of v2.4 the +10 cross-confirm keys on
> `(file, line ±2)` + **category-domain overlap** (`scripts/score.py` `CATEGORY_DOMAIN`), **not** title
> substring — a shared title token no longer fires anything. The *outcome* recorded above (both sites
> cross-confirmed to Critical) is unchanged under the new matcher, because injection/null-access map to the
> security/correctness domains the co-located agents shared; only the stated *mechanism* changed.

## EFF-02b — de-authenticated run degrades cleanly (Codex outage never blocks the review)

| Step | Observed |
|------|----------|
| De-auth (broker teardown + `~/.codex/auth.json` moved aside; NOT `codex logout`) | probe flips to `ready:false` / `loggedIn:false` |
| `/deep-review --base main` de-authenticated | one-line skip-and-note: `⊘ Codex adversarial review skipped (reason: unauthenticated) — completing with native findings only.`; native review completes |
| Restore (recovery-first: auth.json back + stale per-project broker pin cleared) | `ready:true` / `loggedIn:true`, account fingerprint matches pre-de-auth (`b23a6a8439c0`) — user ends logged in |

## Plain-language summary (for the owner)

We ran the new reviewer for real on a file with a deliberately-planted SQL-injection bug. Codex ran,
its finding showed up in the report tagged as Codex's, and — the key thing — both Codex *and* the
built-in reviewers independently flagged the same bug, so it got the cross-confirmation boost that
makes the most-agreed-on findings rise to the top. We then logged Codex out and re-ran: the review
still finished using just the built-in reviewers and printed a one-line "Codex skipped" note instead
of failing. Afterward your Codex login was restored automatically. In short: Codex adds a second
independent opinion when available, and its absence never blocks a review.

<!-- The owner sign-off task (06-02 Task 3) is the SOLE author of the OWNER-SIGNOFF marker below this line. -->

OWNER-SIGNOFF: approved 2026-06-21
