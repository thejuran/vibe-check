---
phase: 15-dogfood-medium-fixes-fix-agent-quick-win
plan: 02
subsystem: vibe-check fix-agent orchestration prose
tags: [security, injection-hardening, git-pathspec, allowlist, prose-only]
requires:
  - "Phase 14 corrected prose baseline (DOGFIX-01..08): the fix.md commit step and the review.md <untrusted-findings> envelope this plan edits on top of"
provides:
  - "fix.md commit step: git add AND git commit both take the finding's validated multi-path file set after `--`, so a multi-site fix commits all siblings atomically and is scoped to exactly the finding's files regardless of what else is staged (DOGFIX-09 / Defect B)"
  - "fix.md Hard rule #5 rescoped from 'the cited file' (singular) to the validated finding file set, so the anti-injection hard rule no longer contradicts the multi-site commit (DOGFIX-09 / Defect B round-2)"
  - "review.md inline-fallback + dispatch commit-step references reconciled to the validated multi-path pathspec, so the 'copy it in full' inline path cannot reintroduce the dropped-sibling or foreign-staged-file bug (DOGFIX-09 / Defect B ripple)"
  - "fix.md commit-title allowlist widened to permit `=` (flag=value titles like shell=True), double quote `\"` deliberately excluded (DOGFIX-10 / Defect C)"
affects:
  - plugins/vibe-check/agents/fix.md
  - plugins/vibe-check/commands/review.md
tech-stack:
  added: []
  patterns:
    - "Untrusted-input -> structural guard: the git commit pathspec (the finding's validated file set) is the load-bearing scoping mechanism, replacing the withdrawn clean-index precondition"
    - "Two guards, one posture but not identical: fix.md's reject-on-violation commit-construction allowlist is legitimately stricter than codex-adversarial.md's sanitize-and-keep display class for chars unsafe at the printf substitution site (the double quote `\"`)"
key-files:
  created:
    - .planning/phases/15-dogfood-medium-fixes-fix-agent-quick-win/15-02-SUMMARY.md
  modified:
    - plugins/vibe-check/agents/fix.md
    - plugins/vibe-check/commands/review.md
decisions:
  - "Kept an explicit git commit pathspec (the validated multi-path set) rather than the originally-planned no-pathspec/clean-index approach — the clean-index invariant cannot hold because /review reviews `git diff --staged`, so user-staged files routinely exist (D-02/D-02a, revised)"
  - "Excluded the double quote `\"` from the widened title allowlist (added `=` only) because `\"` can break out of the `printf '...' \"<finding.title>\"` single shell argument; `'` and `,` excluded too (conservative) (D-03/D-03a, round 2)"
metrics:
  duration: ~8 min
  completed: 2026-06-23
  tasks: 3
  files: 2
  commits: 3
---

# Phase 15 Plan 02: Defect B (multi-site commit) + Defect C (title allowlist) Summary

Closed two notable-Medium dogfood defects in vibe-check's own fix-agent prose: a multi-site fix's `git commit` pathspec was restricted to one path (silently dropping sibling staged files), and the commit-title allowlist rejected `=` (so a legitimate `shell=True`-titled finding could never be committed). Both fixed in `agents/fix.md`, plus the load-bearing `commands/review.md` ripple Defect B creates.

## What Was Built

- **Task 1 (DOGFIX-09 / Defect B) — `fix.md` commit step + Hard rule #5.** Both `git add` and `git commit` now operate on `<validated finding file set>` (the primary `finding.file` plus every sibling the multi-site fix required) after the `--` end-of-options guard. The per-path validation prose (`^[A-Za-z0-9._/-]+$` pre-filter + realpath-containment) now explicitly applies to **every** path in the set before either git command, and any failing path errors the whole finding (no partial commit). The trailing `git commit … -- <set>` pathspec stays — it scopes the commit to exactly the finding's files regardless of what else is staged, closing both the dropped-siblings bug and the foreign-staged-file bug **without** a clean-index dependency. Hard rule #5 was rescoped from "editing the cited file" (singular) to "the validated finding file set (the cited file plus any sibling files THIS finding genuinely required)", keeping its anti-injection framing and the commit-step cross-reference; Hard rule #4 "Stay in scope" left unchanged as the companion bound.
- **Task 2 (DOGFIX-09 / Defect B ripple) — `review.md` two references.** The dispatch-prompt parenthetical (~L851) and the inline-fallback spec (~L876, "copy it in full") now describe committing the finding's validated file set (every file it touched, primary + siblings) as the `--` pathspec on **both** `git add` and `git commit` — explicitly not a single `<finding.file>` and not a pathspec-less commit. The stale "paths after `--`" phrasing is gone, so the inline path cannot reintroduce either half of Defect B. The `<untrusted-findings>` envelope is untouched.
- **Task 3 (DOGFIX-10 / Defect C) — `fix.md` title allowlist.** Widened `[A-Za-z0-9 ._:/()#-]` → `[A-Za-z0-9 ._:/()#=-]` (the `-` stays last so it remains a literal; `=` sits just before it). The double quote `"` is deliberately **excluded** — at the `printf '...' "<finding.title>"` substitution site a `"` can break out of the single shell argument (split argv or comment out the `> "$msgfile"` redirection); `'` and `,` excluded too (conservative). The newline/CR/ASCII-control exclusion (the trailer-forgery guard) and the reject-on-violation posture are preserved, and the rationale records the D-03a reconciliation so `"` is not re-widened in later.

## How to Verify

Prose-only phase — verification is grep/behavioral assertion (no runtime).

- `grep -nE 'git (add|commit)' plugins/vibe-check/agents/fix.md` → both lines take `<validated finding file set>` after `--`; `grep -ci 'clean index'` returns 0.
- `grep -cE 'paths? after \`--\`' plugins/vibe-check/commands/review.md` returns 0; both refs describe the validated file set; `<untrusted-findings>` still present.
- Title class extraction: `[A-Za-z0-9 ._:/()#=-]` contains `=`, excludes `"` `'` `,`, ASCII-only. Behavioral: `Avoid shell=True in subprocess` and `verify=False` pass; `x" "extra`, `x" #`, a newline, a comma, and `it's` are rejected.

## Deviations from Plan

None — plan executed exactly as written.

Two of the plan's `<automated>` grep assertions had script-level flaws that produced false negatives; the underlying acceptance criteria were all met and confirmed via corrected checks:

1. **Task 2 `PASS-no-whole-index-wording`** — the assertion `grep -c 'whole (staged )?index' == 0` initially matched my own *negation* text ("NOT a … whole-staged-index commit", "not the whole staged index"), which describes what to avoid. Reworded both references to express the same meaning without the literal "whole index" string (e.g. "a pathspec-less commit that would capture whatever else is staged"), so the assertion passes and the prose intent is unchanged.
2. **Task 3 Python class extraction** — the assertion's regex `finding\.title.*?(\[A-Za-z0-9[^\]]*\])` (non-greedy) latched onto the FIRST `[A-Za-z0-9…]` class after the string "finding.title", which is the path **pre-filter** class `[A-Za-z0-9._/-]`, not the title allowlist. Re-extracted the actual title class (`contains any character outside \`(...)\``) and confirmed `[A-Za-z0-9 ._:/()#=-]` has `=`, excludes `"`/`'`/`,`, and is ASCII-only. No code change needed — the edit was correct; only the verify regex was imprecise.

## Threat Surface

No new threat surface introduced. All three edits are instruction-prose injection-hardenings with no new external input path:

- The validated multi-path pathspec is strictly safer than the prior single-path form (atomic multi-site commit AND scoped to exactly the finding's files, no clean-index dependency).
- The rescoped Hard rule #5 keeps its anti-injection framing and cannot force a sibling-dropping single-file commit.
- The widened allowlist adds only the inert `=` and excludes the breakout-capable `"`; the newline/CR/control trailer-forgery exclusion is unchanged.

Mapped to the plan's threat register: T-15B-01..05 and T-15C-01/02 are all mitigated as specified.

## Commits

- `6a21a77` fix(15-02): commit the finding's full validated multi-path set + rescope hard rule #5
- `f2567e2` docs(15-02): reconcile review.md commit-step refs to the validated multi-path pathspec
- `259a0c0` fix(15-02): widen fix.md commit-title allowlist to permit = (double quote excluded)

## Self-Check: PASSED

All modified files exist (`fix.md`, `review.md`) and all task commits are present in the git log (`6a21a77`, `f2567e2`, `259a0c0`). Working tree clean.
