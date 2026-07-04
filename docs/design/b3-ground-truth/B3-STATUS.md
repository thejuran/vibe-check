# B3 — Product-quality ground-truth harness (RUN-KIT BUILT — Wave 2 owner runs pending)

> **Status:** Phase 36 Plan 36-01 (2026-07-03) built the complete run-kit. Wave 1 (assistant)
> is DONE; Wave 2 (owner-driven `/deep-review` runs, N=3 per diff) is the current gate; Wave 3
> (assistant scores + reports into `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md`) follows.
> Superseded history: originally SHELVED 2026-07-01 (Opus) pending owner runtime.

## What B3 measures

The gap vibe-check self-documents (`RESULTS.md:64`): no aggregate catch-rate / false-positive-
rate across a realistic surface. B3 runs vibe-check on real diffs with **known outcomes** and
scores: does it catch the real bug (should-catch), and stay quiet on clean code (should-quiet)?

## The hard gate (why Wave 2 waits on the owner)

Measurement = run `/deep-review` on each diff, N=3, score output vs answer key. `/deep-review`
is a **user-triggered skill** — the assistant CANNOT invoke it. The owner drives all 18 runs
from `RUN-CHECKLIST.md` (pure copy-paste; resumable at any run boundary across days).

## Decisions locked

- **Repos:** triggarr (Py/FastAPI), seedsyncarr (Py+TS), dashboard (Py+React), + roonseek
  (pure Py, buggy history) — the languages/frameworks the owner relies on vibe-check for.
- **Ground-truth sourcing:** ORGANIC-ONLY, enforced by the FAIL-CLOSED regex
  `DR[0-9]|DR-|CR-|WR-|review-pass|codex` (comment-stripped, case-insensitive) — any hit =
  vibe-check-found = EXCLUDED (circular self-testing). Evidence persisted per patch in
  `diffs/<id>.provenance`.
- **Test set:** committed (reusable — re-run each milestone to catch review-quality regression).
- **D-12:** the dashboard-unbounded-dict "anchor" (`052845e`, subject `fix(42): DR3m-01 ...`)
  is EXCLUDED — a live regex hit. Replaced by a clean-organic third catch (seedsyncarr).
- **D-02:** owner_confirmed: true — should-quiet picks confirmed as-is (2026-07-03).

## The committed test set (6 diffs, all with .provenance sidecars)

| diffs/ file | Repo | Role | Source commit | base_sha (runs detach here) |
|---|---|---|---|---|
| `triggarr-secret-in-logs.patch` (+`.BUGGY.py`) | triggarr | should-catch: secret/PII (API key) in logs via `exc=exc` | `d47b4c2` reversed | `f4366a2...` (clone HEAD at build) |
| `triggarr-autoescape.patch` (+`.BUGGY.py`) | triggarr | should-catch: XSS surface — preconfigured autoescape env removed | `e11187e` reversed | `e11187e...` (PINNED — fails current HEAD) |
| `third-organic-should-catch.patch` | seedsyncarr | should-catch: unclamped >100% progress percentage | `879266c` reversed | `3db8b48...` (clone HEAD at build) |
| `should-quiet-1.patch` | triggarr | should-quiet: SSRF-hardening feature | `1a8c9f9` forward | `98eb419...` (= `1a8c9f9^`) |
| `should-quiet-2.patch` | seedsyncarr | should-quiet: optional-JSON-body feature | `3c27e17` forward | `84aff27...` (= `3c27e17^`) |
| `should-quiet-3.patch` | roonseek | should-quiet: transfer-cancel boundary feature | `2a6bbd9` forward | `1027691...` (= `2a6bbd9^`) |

`dashboard-unbounded-dict.BUGGY.py` remains in `diffs/` as a captured asset but is NOT in the
measured set (D-12 — non-organic).

Every `.provenance` sidecar records: fix/feature sha + checked subject/body snippet
(fail-closed regex clean), base_sha (`git apply --check` exit 0 verified), the FULL-worktree
proof pair (EXPECTED_TREE_DIFF_SHA256 over the full no-pathspec diff + EXPECTED_TOUCHED_PATHS),
pure-M `name-status:` evidence, and (should-quiet) per-hunk subject-agnostic `git log -L`
line-survival output.

## To resume B3 (current state → next steps)

Wave 1 artifacts (ALL COMMITTED, Plan 36-01):

1. ✅ 3 should-catch + 3 should-quiet patches + `.provenance` sidecars (base_shas, tree-diff
   sha256 proof pairs, pure-M gates, organic gates).
2. ✅ `ANSWER-KEY-b3.md` — SITE+AXIS+BAND three-gate key, per-row base_sha, A8/A16 folded,
   D-07/D-08/D-09 + head-check rules, D-11 decision table. Pre-registered BEFORE any run.
3. ✅ `PREREGISTRATION.md` — the SEPARATE fail-closed manifest (follow-up commit) recording the
   key's committing commit + committed-blob SHA-256. IMMUTABLE once the first `runs/` commit
   exists; Wave 3 scores only from the committed blob and exits non-zero on mismatch.
   Mirror of the recorded values (the manifest is authoritative):
   ANSWER_KEY_COMMIT = `ef0ab67cb45957167c99eff468077348432e1474`,
   ANSWER_KEY_SHA256 = `1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1`.
4. ✅ `RUN-CHECKLIST.md` — owner copy-paste sweep: `set -euo pipefail` fail-closed blocks,
   pre-registration gate + cache CONTENT-assert (STEP 0), uniform detach-to-base_sha
   apply-ONCE blocks, per-run `apply --reverse --check` pre-review proof + FULL-worktree proof
   (tree.diff + sha256 + name-only + no-untracked), unconditional `.b3-inprogress` sentinel,
   exact Phase-5 fix-loop decline instructions, EXPECTED_HEAD argv assert, per-run boundary
   commits (`runs(36-02): <id> run <n> captured`), revert-once-after-run-3,
   sentinel-keyed RESUME-AT-NEXT-RUN + FAILED-RUN RECOVERY blocks per diff.

Next:

5. **Wave 2 (OWNER):** drive the 18 runs from `RUN-CHECKLIST.md` (3 per diff; resumable at any
   run boundary). The single non-copy-paste action per run is `/vibe-check:deep-review`.
6. **Wave 3 (assistant, Plan 36-03):** score every archived `runs/<id>/run-<n>/state.json`
   against the committed key blob at the pre-registered commit; write the catch/FP report +
   D-11 proceed/don't/need-more-data verdicts into
   `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md`. Hard-stop before aggregation on any
   unscoreable run (owner waiver required, recorded in the report).

## Cross-references

- Answer key: `docs/design/b3-ground-truth/ANSWER-KEY-b3.md`
- Pre-registration manifest: `docs/design/b3-ground-truth/PREREGISTRATION.md`
- Run checklist: `docs/design/b3-ground-truth/RUN-CHECKLIST.md`
- Method template (single-agent): `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md`
- The self-documented gap: `plugins/vibe-check/docs/efficacy/RESULTS.md:64`
- Full harness design: `../product-quality-harness.md`
