---
phase: 37-close
plan: 01
subsystem: release
tags: [release, publish, versioning, git-ritual, efficacy-pointer]
requires:
  - "feat/v2.9 branch complete (Phases 35 + 36 landed: LEGIBLE wiring + B3 measured numbers)"
  - "plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md committed (catch-rate 8/9 · false-positive-rate 6/9)"
provides:
  - "plugin.json @ 2.9.0 (published)"
  - "annotated tag v2.9 on the 2.9.0 main tip (published, immutable)"
  - "main fast-forwarded + pushed; feat/v2.9 branch pushed (first push, 69 commits public)"
  - "README ## 📊 Measured Efficacy pointer (honest 8/9 · 6/9 + small-N caveat + RESULTS-v2.9.md link)"
affects:
  - "public GitHub repo github.com/thejuran/vibe-check (marketplace pins ref:main)"
tech-stack:
  added: []
  patterns:
    - "same-repo FF via `git push . feat/v2.9:main` (no checkout, no merge commit, non-FF refused = STOP gate)"
    - "annotated tag with EXPLICIT main target (`git tag -a v2.9 main`) — can never tag drifted HEAD"
    - "ONE `git push --atomic origin main refs/tags/v2.9 feat/v2.9` — all-or-none, no partial public deploy"
    - "exact-hash verify gate (local == remote for all three refs, tag compared on non-^{} line)"
    - "classify-then-capture anchor policy (anchor written only after STATE=A/B classifier, from the classifier snapshot)"
key-files:
  created:
    - ".planning/phases/37-close/37-01-SUMMARY.md"
  modified:
    - "plugins/vibe-check/.claude-plugin/plugin.json (version 2.8.0 → 2.9.0)"
    - "README.md (added ## 📊 Measured Efficacy section)"
decisions:
  - "Fresh run classified STATE=A (main at merge-base, remote pre-publish, tag/branch absent) — full FF/tag/push/verify path"
  - "Anchor $OLD_REMOTE_MAIN = bbecf559 captured create-only from the still-pre-publish origin (race guard passed)"
  - "Combined bump + README pointer in ONE commit (17950c0) — permitted per plan Discretion"
metrics:
  duration: "~9 min"
  completed: "2026-07-08"
  tasks: 2
  files: 2
---

# Phase 37 Plan 01: Close (v2.9 Release) Summary

Shipped vibe-check v2.9 "Prove it": bumped `plugin.json` 2.8.0 → 2.9.0, added an honest README measured-efficacy pointer (catch-rate 8/9 · false-positive-rate 6/9, small-N caveat, RESULTS-v2.9.md link), fast-forwarded `main` to the `feat/v2.9` tip, created the annotated `v2.9` tag on the 2.9.0 tree, atomic-pushed all three refs to public GitHub, and exact-hash verified the publish (PUBLISH-VERIFIED).

## What Was Built

### Task 1 — Version bump + README efficacy pointer
- **Pre-flight gate (D-05):** `pytest -q` in `plugins/vibe-check/scripts` reported `356 passed, 221 subtests passed` (baseline) before any commit.
- **plugin.json:** the single line `"version": "2.8.0",` → `"version": "2.9.0",`; no other field touched.
- **README.md:** new `## 📊 Measured Efficacy` section inserted between `## 📦 What is This?` (closing `---` at L26) and `## 🚀 Quick Start` (now L36). Emoji-prefixed heading, exact fractions `catch-rate 8/9, false-positive-rate 6/9` (no rounding), small-N caveat (N=3 per diff, 9 catch + 9 quiet runs, four repos, organic-only), repo-root-relative link `[docs/efficacy/RESULTS-v2.9.md](plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md)`, closing `---` rule. Honesty-first framing, no marketing language.
- **Commit:** `17950c0` — `chore(release): bump plugin to 2.9.0`. EXPLICIT-PATH staging only (`git add plugins/vibe-check/.claude-plugin/plugin.json README.md`); pre-commit `git status` and post-commit `git log --name-only` over the `PRE_RELEASE_TIP..HEAD` range both confirmed EXACTLY those two files and NO `.planning/` path. The ~41 stale `.planning/` worktree changes were left untouched.
- **Verify:** automated check printed `clean-staging-ok`.

### Task 2 — FF main, annotated tag, atomic push, exact-hash verify
- **State classification:** fresh run classified `STATE=A` (LOCAL_MAIN=bbecf55 at merge-base, FEAT=17950c0, behind=0, REMOTE_MAIN=bbecf55 == local main pre-publish, remote tag absent, remote branch absent, anchor_preexisted=no). The anchor file was NOT created before the classifier ran (classify-then-capture, codex pass 6).
- **Anchor (back-out / audit anchor):** `$OLD_REMOTE_MAIN = bbecf5591a7b61e7ad177c4f561234ae8dbda327` — **captured FRESH** under STATE=A create-only, from the still-pre-publish origin, recording the CLASSIFIER snapshot (not a re-read). A fresh-remote equality race guard (`FRESH_REMOTE_MAIN == $REMOTE_MAIN`) passed before the write (no TOCTOU drift, codex pass 7). Persisted at `.git/OLD_REMOTE_MAIN_V2_9`.
- **STEP 2 — FF:** `git push . feat/v2.9:main` advanced local `main` `bbecf55..17950c0` (fast-forward, NO merge commit, NO checkout — remained on `feat/v2.9`). Post-FF assertion `main == feat/v2.9` held. `git rev-list --count feat/v2.9..main` was `0` at execution time (valid FF, not a `--no-ff` merge).
- **STEP 3 — annotated tag:** `git tag -a v2.9 main` (EXPLICIT main target). `git cat-file -t v2.9` → `tag` (annotated). Hard-verify `v2.9^{} == main` held BEFORE push. `git show v2.9:...plugin.json` shows 2.9.0. Tag message subject `v2.9 — Prove it`; body contains `8/9`, `6/9`, `356 tests + 221 subtests`. Tag object SHA `b1c343424e087320c2e6c9b43b5a066ef03122b3`.
- **STEP 4a — pre-push assertions (guarded, capture-then-test):** remote main == `$OLD_REMOTE_MAIN` (unmoved), remote tag absent, remote branch absent — all via `remote_required`/`remote_optional` with rc-preserving `VAR="$(...)" || {STOP}` capture (codex pass 9). All passed.
- **STEP 4b — atomic push:** `git push --atomic origin main refs/tags/v2.9 feat/v2.9` succeeded (rc=0): `main bbecf55..17950c0`, `[new tag] v2.9`, `[new branch] feat/v2.9`. First push of `feat/v2.9` — 69 local-only commits (incl. the B3 ground-truth kit, D-01 owner-approved) became public.
- **STEP 5 — exact-hash verify gate (D-04):** `main OK`, `tag OK` (tag OBJECT sha vs non-`^{}` remote line), `branch OK`. Combined `<automated>` verify printed **PUBLISH-VERIFIED**.

## Published Refs (exact hashes, local == remote)

| Ref | Local SHA | Remote SHA | Result |
|-----|-----------|------------|--------|
| `main` | `17950c0f6e38702987277c6c9c53d372401c8095` | `17950c0f...` | OK |
| tag `v2.9` (object) | `b1c343424e087320c2e6c9b43b5a066ef03122b3` | `b1c34342...` | OK |
| branch `feat/v2.9` | `17950c0f6e38702987277c6c9c53d372401c8095` | `17950c0f...` | OK |

- Pre-publish remote-main anchor (back-out / audit only, never a reset target): `bbecf5591a7b61e7ad177c4f561234ae8dbda327` (captured FRESH under STATE=A; `ANCHOR_PREEXISTED=no`, not read from a pre-existing file, not reflog-recovered).
- Tag peels to main: `v2.9^{}` = `17950c0f...` = `main`.

## Deviations from Plan

None — plan executed exactly as written. Classified STATE=A on a fresh run and followed the full FF → tag → atomic-push → verify path. The branch was 69 commits ahead of main at execution (plan `<facts>` cited 57 at plan-time); the additional commits are the plan-doc commits made on `feat/v2.9` since plan-time and publish with the branch as sanctioned (execution notes).

## Notes / Boundaries

- **Installed-cache lag (D-05, NOT a gate):** the installed plugin cache at `~/.claude/plugins/cache/thejuran/vibe-check/` still reads 2.8.0 (not readable / not present in this session) and updates only on the user's next `/plugin update` + process relaunch. Expected for the publish; not a failure.
- **Milestone-audit boundary (D-06):** CLOSE-01 criterion 3 ("audited") is delegated to the WRAPPER orchestrator via `/gsd:audit-milestone` at milestone-end. This plan did NOT run `/gsd:audit-milestone` or archive.
- **Byte-frozen this phase:** `score.py` / `test_score.py` / `config.py` untouched.
- **Anchor cleanup:** after this SUMMARY records the anchor SHA, `.git/OLD_REMOTE_MAIN_V2_9` is removed (crash-survival purpose served).

## Self-Check: PASSED
