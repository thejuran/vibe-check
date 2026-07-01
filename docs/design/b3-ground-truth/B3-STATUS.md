# B3 — Product-quality ground-truth harness (SHELVED, resume-ready)

> **Status:** Opus, 2026-07-01. SHELVED by owner decision — B3 is its own sub-project (needs a
> real corpus + many `/deep-review` runs the owner must drive). This banks the verified work so
> it resumes cleanly. Do NOT treat as complete.

## What B3 measures
The gap vibe-check self-documents (`RESULTS.md:64`): no aggregate catch-rate / false-positive-
rate across a realistic surface. B3 runs vibe-check on real diffs with **known outcomes** and
scores: does it catch the real bug (should-catch), and stay quiet on clean code (should-quiet)?

## The hard blocker (why it's shelved)
Measurement = run `/deep-review` on each diff, N=3, score output vs answer key. `/deep-review`
is a **user-triggered skill** — the assistant CANNOT invoke it. So the catch-rate step
inherently requires the owner to run the reviews. Running `score.py` directly tests only the
scoring half (needs mock agent findings), which measures nothing about catch-rate. So B3 cannot
be fully automated; it needs owner run-time.

## Decisions locked
- **Repos:** triggarr (Py/FastAPI), seedsyncarr (Py+TS), dashboard (Py+React), + roonseek
  (pure Py, buggy history) — the languages/frameworks the owner relies on vibe-check for.
- **Ground-truth sourcing:** ORGANIC-ONLY. Exclude any fix tagged CR-/WR-/DR-/review-pass/codex
  — those bugs were *found by vibe-check itself*, so using them is circular (re-asking it to
  find what it already found). Only human/other-tool-found bugs count as an honest "catches
  unseen bugs" test.
- **Test set:** committed (reusable — re-run each milestone to catch review-quality regression).

## Verified should-catch diffs (parent = the buggy state, before the fix removed it)

| File in diffs/ | Repo | Bug | Fix commit | What SHOULD catch it |
|---|---|---|---|---|
| `dashboard-unbounded-dict.BUGGY.py` | dashboard | `_machine_alert_last_sent: dict = {}` grows unbounded (~10MB @ 100k entries); fix adds OrderedDict FIFO eviction | `052845e` | `bugs` / `impact` (memory leak visible in diff) — the ANCHOR case |
| `triggarr-autoescape.BUGGY.py` | triggarr | Jinja2 autoescape config; fix moves to a preconfigured env | `e11187e` | `security` / framework (XSS surface) |
| *(not yet captured)* triggarr secret-in-logs | triggarr | `logger.warning(..., exc=exc)` where `exc` is an httpx error whose URL carries the *arr API key + a pydantic ValidationError echoing the payload; fix → safe scalars (`status_code`, `error_count()`) | `d47b4c2` | `security` (PII/secret-in-logs) — SUBTLE, high-value; a naive reviewer misses it |

**Note on the buggy `.py` files:** these are the *whole parent file* at `<fix>^`. For a diff-mode
review, reconstruct the diff as `git show <fix>` REVERSED (the fix's removal = the bug's
addition), or review the buggy file against its fixed successor. The answer key is "the review
must surface the bug the fix later removed, ≥ threshold."

## To resume B3 (the run-kit that still needs building)
1. Capture the triggarr secret-in-logs parent file + reconstruct all three as reviewable diffs.
2. Add 2-3 should-STAY-QUIET diffs (clean feature commits that shipped fine) — the FP side.
3. Optionally mine roonseek walkthrough transcripts (scattered across session `.jsonl` dirs) for
   real user-facing bugs — highest-quality but laborious; deferred.
4. Write a per-diff answer key (expected findings + expected band).
5. Owner runs `/deep-review` on each, N=3; assistant scores vs key → first catch/FP numbers.

## Cross-references
- Method template (single-agent): `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md`
- The self-documented gap: `plugins/vibe-check/docs/efficacy/RESULTS.md:64`
- Full harness design: `../product-quality-harness.md`
