# Whole-Codebase Review Mode (`--all`) Efficacy Test — RESULTS (v2.3, Phase 12)

**Verdict: all five design-spec §6 success criteria `PASS` · owner sign-off `APPROVED`** — `/vibe-check:deep-review --all` ran end-to-end on this repo, surfaced genuine real defects with acceptable noise and an honest coverage line, and every criterion was demonstrated live.

Run as a human-in-the-loop main session (the `--all` estimate gate is an interactive `AskUserQuestion` with no pre-answer flag, so it cannot be driven by an automated executor — same posture as v2.2 Phase 6's `--interactive` run). Dogfood target: **this repo itself** (vibe-check), whole tree. Findings scored deterministically with `templates/scoring.md`; `/deep-review` surfaces at score ≥ 70, with the plain-`--all` Critical/Warning listing bar narrowing the default render to C+W (`--full` reveals Medium). Codex correctly fail-closed (a whole-repo set is not a representable diff range).

## Scope reviewed

- **32 tracked files**, all regular (0 symlinks dropped, 0 skip-rule exclusions). Because `.planning/` is gitignored, the tracked tree is the plugin source + docs — a prompt-only Markdown plugin + `plugin.json`.
- **2 risk-ranked chunks** (riskiest first). Every file landed in tier 3 (docs/config): a prompt-only repo has no auth/crypto/api/source *paths* to tier on, so path-tier risk-ranking collapsed to within-tier churn ordering (`review.md`, 26 commits, seeded chunk 1). This is a real, honestly-noted characteristic of auditing a prompt-only codebase — not a bug.

## Criterion 1 — end-to-end run + estimate gate + coverage line

| Evidence | Observed |
|----------|----------|
| Risk-rank announce | `✓ Phase 0.2 — Risk-rank & chunk-plan: 2 chunks (riskiest first)` |
| Estimate block | 32 files / 2 chunks / 5–11 agents per chunk / 10–22 dispatches (upper bound 22) / ~$2–$5 / a few minutes + caveat |
| Four-way gate | `AskUserQuestion` Run full / Narrow / Cap top-K / Cancel → owner chose **Run full** |
| Coverage line | `Reviewed 32 of 32 files (whole-codebase, --all mode; 0 skipped); all 2 chunks` |
| Findings produced | 43 canonical (51 raw, 1 dropped not-in-reviewed-set, 7 same-site merged): **3 Critical / 6 Warning / 9 Medium / 25 Filtered** |

## Criterion 3 — per-chunk triage skips irrelevant agents (NATURAL)

| Chunk | Triage result | Agents dispatched | Language/framework agents |
|-------|---------------|-------------------|---------------------------|
| 1 (10 files) | `languages:[markdown,json,yaml] frameworks:[]` | bugs, security, architecture, impact | **none** (correctly skipped) |
| 2 (22 files) | `languages:[markdown] frameworks:[]` | bugs, security, architecture, impact | **none** (correctly skipped) |

A markdown-only chunk demonstrably did NOT dispatch `language-python` (or any language/framework agent) — CHUNK-03 proven on the real tree. **Inverse confirmed** in the criterion-5a staged proof: a chunk containing `.py` files WOULD trigger `language-python`.

## Criterion 4 — `--all --full` Medium reveal + cross-file dedup occurrence count

- **4a (natural):** Plain `--all` listed only Critical+Warning and printed `9 Medium not shown — re-run with --full`. Re-rendering with `--all --full` listed all 9 Medium findings (scored ≥70, render-suppressed under the default bar). The ≥70 threshold was unchanged — only the listing widened.
- **4b (staged, labeled, never merged — D-02):** Cross-file dedup did not surface naturally (real defects were file-specific). Per D-02, two tiny files (`staged-proof/alpha.py`, `staged-proof/beta.py`) with the SAME `subprocess.run(cmd, shell=True)` injection were staged on a throwaway branch. The security agent flagged both (CWE-78, same call, 2 distinct files) → cross-file render grouping collapsed to ONE row: `staged-proof/alpha.py:5 (+ 1 more occurrence)` with the full occurrence list. Staged input flagged as staged and discarded with the branch.

## Criterion 5 — `--all --fix` applies+commits (throwaway) while plain `--all` is report-first

- **5b (report-first):** Plain `--all` rendered + persisted state, then SKIPPED Phase 5 (no "apply all?" prompt) and printed the report-only one-liner naming both `--all --fix` and `--all --finalize` — "Nothing was changed." State file still written (`.turingmind/state/by-mode/all/<hash>.json`).
- **5a (opt-in fix, D-03):** On throwaway branch `efftest/all-fix-v2.3`, `--all --fix` entered the Phase-5 fix loop and the `fix` agent applied + committed BOTH whole-repo-chunk findings atomically: `fix(review-pass-1): Drop shell invocation in subprocess run (command injection)` at SHAs `ab8005e` (alpha.py) and `61a3677` (beta.py). The branch was verified UNMERGED and deleted — the fix commits never reached main.

## Criterion 2 — diff-mode non-regression (D-07)

A plain `/vibe-check:review` (no `--all`): the branch-flip guard does not fire → `$ALL_MODE` stays unset → Phase 0.2 (risk-rank) and Phase 0.3 (estimate gate) are SKIPPED → the orchestrator resolves a `<diff>` block over the changed file, applies the `in_diff` filter, and renders the diff-mode `Reviewed N files, L lines changed` summary (NOT the `--all` coverage variant). The `--all` machinery is additive and `$ALL_MODE`-guarded; the diff path is structurally unchanged.

## What the audit actually found (the usefulness bar)

The findings are genuine, not hallucinated. Real Critical/Warning defects in the tool's own orchestration prose — the cross-file-drift class vibe-check exists to catch, found in vibe-check itself:
- **Abandon-resume hint** (`review.md:893`) prints the OLD `/turingmind-code-review:` namespace + an unfilled `{{command}}` placeholder — a copy-paste-broken resume command (cross-confirmed by bugs + architecture).
- **Stale line-number citations** (`deep-review.md:36`) into `review.md` (~454 / ~581 off by 70–80 lines) that silently misdirect the orchestrator (cross-confirmed by bugs + architecture).
- **`false-positive-rules.md`** defines a whole second scoring contract that contradicts canonical `scoring.md` and is referenced by no file (cross-confirmed by bugs + architecture + impact).
- **`--all --finalize`** archives the wrong/nonexistent state file (`$PHASE_ID` is unset in `--all`).

Cross-model confirmation (+10) fired on the multi-agent clusters, floating the most-agreed findings to Critical. Noise was acceptable — 25 lower-confidence items correctly held below the ≥70 threshold. **Bonus finding the dogfood itself surfaced:** the `fix` agent's commit-message title allowlist `[A-Za-z0-9 ._:/()#-]` rejects a title containing `=` (e.g. `shell=True`), so a legitimate finding whose title quotes `flag=value` cannot be committed until the orchestrator re-phrases it — a real usability gap (candidate backlog item).

## Plain-language summary (for the owner)

We pointed the tool at its own codebase and ran the whole-repo audit end-to-end: it showed the cost estimate and asked for approval before spending anything, reviewed all 32 files in 2 risk-ordered batches, only ran the reviewers that fit each batch (it correctly skipped the Python/JS reviewers on the Markdown-only files), and produced a clean Critical/Warning report with an honest "reviewed 32 of 32" line. The findings were real — genuine bugs in the tool's own instructions, including a couple the built-in reviewers and the cross-checker all independently agreed on. We confirmed the opt-in fix mode actually fixes and commits (on a throwaway branch we threw away), that a plain audit never auto-changes anything, and that ordinary diff reviews still work exactly as before. In short: whole-codebase mode works, it's honest about what it did and didn't review, and the findings were worth reading.

<!-- The owner sign-off task (12-02 Task 2) is the SOLE author of the OWNER-SIGNOFF marker below this line. -->

OWNER-SIGNOFF: approved 2026-06-22
