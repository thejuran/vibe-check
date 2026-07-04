---
phase: 36-b3-first-measured-quality-numbers
plan: 01
subsystem: efficacy-measurement
tags: [b3, ground-truth, answer-key, pre-registration, run-checklist, organic-only]
requires: []
provides:
  - "Committed organic ground-truth test set: 3 should-catch reversed-fix patches + 3 should-quiet feature patches, each with a .provenance sidecar (base_sha, EXPECTED_TREE_DIFF_SHA256, EXPECTED_TOUCHED_PATHS, pure-M name-status, fail-closed organic-regex snippet)"
  - "ANSWER-KEY-b3.md — SITE+AXIS+BAND three-gate key, per-row base_sha, A8/A16 folded, D-07/D-08/D-09 + head-check rules, D-11 decision table (pre-registered before any run)"
  - "PREREGISTRATION.md — separate fail-closed manifest: ANSWER_KEY_COMMIT=ef0ab67cb45957167c99eff468077348432e1474, ANSWER_KEY_SHA256=1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1"
  - "RUN-CHECKLIST.md — 18-run owner copy-paste sweep (fail-closed, resumable at run boundaries, sentinel-keyed resume + failed-run recovery)"
affects: [36-02 (owner runs), 36-03 (scoring + report)]
tech-stack:
  added: []
  patterns: [reversed-fix patch reconstruction, full-worktree sha256 proof pair, separate-manifest pre-registration, fail-closed owner checklist]
key-files:
  created:
    - docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch (+ .BUGGY.py + .provenance)
    - docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch (+ .provenance)
    - docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch (+ .provenance)
    - docs/design/b3-ground-truth/diffs/should-quiet-{1,2,3}.patch (+ .provenance)
    - docs/design/b3-ground-truth/ANSWER-KEY-b3.md
    - docs/design/b3-ground-truth/PREREGISTRATION.md
    - docs/design/b3-ground-truth/RUN-CHECKLIST.md
  modified:
    - docs/design/b3-ground-truth/B3-STATUS.md
decisions:
  - "Third organic should-catch = seedsyncarr 879266c (unclamped >100% progress percentage, TS product code) — dashboard 052845e EXCLUDED per D-12 (DR3m-01 is a live fail-closed-regex hit); no checkpoint needed, a clean third existed"
  - "Should-quiet picks (owner_confirmed: true, Task-2b confirm-all): triggarr 1a8c9f9 (SSRF hardening, Py), seedsyncarr 3c27e17 (optional POST body, TS), roonseek 2a6bbd9 (transfer cancel boundary, Py) — D-03 target of 3 met"
  - "roonseek 355c57f REJECTED at the line-survival gate (its library.py hunk was rewritten by later ed1c23d) — the subject-agnostic git log -L check caught what the old subject-filtered grep would have missed"
  - "Third should-catch expected band floor = medium (honest severity for a UI display defect; warning floor would punish correct severity assessment); the two security catches carry warning floors"
  - "ANSWER_KEY_COMMIT = ef0ab67 (the Task-4 commit — the last commit whose tree holds the final key before the manifest); digest computed over the committed blob, not the working file"
metrics:
  duration: "~21 min execution (22:53-23:14 EDT commit span) + checkpoint pause at Task 2b"
  completed: "2026-07-04"
  tasks: 5 (4 auto + 1 checkpoint:decision)
  files: 19 committed under docs/design/b3-ground-truth/
---

# Phase 36 Plan 01: B3 Run-Kit (Ground-Truth Test Set + Answer Key + Pre-Registration + Run-Checklist) Summary

Committed organic-only B3 run-kit: 6 patches with sha256-proofed provenance sidecars, a
pre-registered SITE+AXIS+BAND answer key (A8/A16 folded), a separate fail-closed
PREREGISTRATION.md manifest, and an 18-run fail-closed owner checklist — score.py byte-frozen.

## What was built

- **3 should-catch reversed-fix patches** (all organic, pure-M, fail-closed regex clean):
  - `triggarr-secret-in-logs` — reversed `d47b4c2`; re-plants `logger.warning(..., exc=exc)`
    (API key/PII into logs). base_sha `f4366a2` (clone HEAD, --check exit 0). BUGGY.py parent
    captured to match the existing convention.
  - `triggarr-autoescape` — reversed `e11187e`; removes the preconfigured autoescape
    `jinja2.Environment` (XSS surface silently re-enabled on current Starlette). base_sha
    PINNED to `e11187e` — verified the patch FAILS `--check` at current triggarr HEAD
    (routes.py:43), exactly as researched.
  - `third-organic-should-catch` — reversed seedsyncarr `879266c`; removes the
    `Math.min(100, ...)` clamp (extracted files render "199%"). Replaces the D-12-excluded
    dashboard case. base_sha `3db8b48` (clone HEAD, --check exit 0).
- **3 should-quiet feature patches** (organic, pure-M, per-hunk line-survival clean,
  size-comparable, owner-confirmed): triggarr `1a8c9f9` (+6), seedsyncarr `3c27e17` (+3/-2),
  roonseek `2a6bbd9` (+15). Each records base_sha = `<feat>^` (the forward diff's natural
  pre-image; verified `--check` exit 0 on a detached checkout).
- **Every sidecar** carries the FULL-worktree proof pair — EXPECTED_TREE_DIFF_SHA256 over the
  full no-pathspec `git diff` on the patched detached base + sorted EXPECTED_TOUCHED_PATHS —
  plus pure-M `name-status:` evidence and the checked subject/body snippet.
- **ANSWER-KEY-b3.md**: three independent gates (SITE ∧ AXIS ∧ BAND) per D-07; secret-in-logs
  AXIS = "secret/PII (API key) leaked into logs" at warning floor; autoescape AXIS names the
  lost-preconfigured-env XSS mechanism at warning floor; third at medium floor.
  A8 content-justified-exemption preamble; A16 safe-on-axis naming per should-quiet row;
  D-08 FP rule; D-09 no-rounding aggregation; head-check (`passes[-1].head_sha == base_sha`,
  `len(passes)==1`); full 7-row D-11 table; owner_confirmed: true recorded.
- **PREREGISTRATION.md** (follow-up commit `cca63e2`): ANSWER_KEY_COMMIT `ef0ab67...1474`,
  ANSWER_KEY_SHA256 `1463...fca1` — digest recomputed from the committed blob and verified
  equal; immutability + MANIFEST_COMMIT derivation stated; no `runs/` dir exists (ordering
  attested). Values mirrored into RUN-CHECKLIST.md header and B3-STATUS.md.
- **RUN-CHECKLIST.md** (2,203 lines, 63 bash blocks — ALL pass `bash -n`): per-diff uniform
  blocks with literal ids/repos/base_shas/sha256s/touched-paths (zero unresolved
  placeholders); pre-registration gate reads the manifest (porcelain-asserted immutable);
  STEP 0 cache CONTENT-assert (SCOPE_ARGS / "Codex off via"); apply-ONCE / three
  state-isolated runs / revert-once-after-run-3; per-run `apply --reverse --check` proof +
  full-worktree proof (tree.diff + sha256 + name-only + no-untracked) + real EXPECTED_HEAD
  sys.argv assert (functionally tested on 4 synthetic paths: good / 2-pass / wrong-head /
  missing); run-boundary commits `runs(36-02): <id> run <n> captured`; unconditional
  `.b3-inprogress` sentinel; RESUME-AT-NEXT-RUN + FAILED-RUN RECOVERY blocks per diff; exact
  Phase-5 decline labels ("Skip fixes this pass" / "Abandon for now") in header AND inline.

## Task → commit map

| Task | Name | Commit |
|---|---|---|
| 1 | 3 organic should-catch patches + sidecars | `435d563` |
| 2 | 3 organic should-quiet patches + line-survival sidecars | `98e5aff` |
| 2b | checkpoint:decision — owner confirmed picks (confirm-all) | (no commit — decision recorded) |
| 3 | ANSWER-KEY-b3.md | `cea17e6` |
| 4 | RUN-CHECKLIST.md + B3-STATUS.md resume record | `ef0ab67` (= ANSWER_KEY_COMMIT) |
| 5 | PREREGISTRATION.md follow-up manifest + mirrors | `cca63e2` |

## Deviations from Plan

### Auto-fixed / auto-added

**1. [Rule 2 - Missing critical] Sentinel persists `start_branch`/`start_sha`**
- **Found during:** Task 4 (authoring the step-9 revert block)
- **Issue:** step 9 restores via `$START_BRANCH`/`$START_SHA`, captured as shell vars in the
  fresh block — but the plan's own multi-day resumability means step 9 can run in a different
  shell session, where `set -u` would kill the block on unbound vars (or silently restore the
  wrong ref without `-u`).
- **Fix:** the fresh block writes `start_branch=`/`start_sha=` into `.b3-inprogress` (two
  extra fields beyond the plan's diff_id/base_sha/had_prior_state), and step 9 reads them from
  the sentinel with fail-closed `test -n` guards. No guard weakened; the sentinel remains the
  single resume marker.
- **Commit:** `ef0ab67`

**2. [Rule 3 - Blocking] STEP 0.5 one-time local `.turingmind/` exclude per source repo**
- **Found during:** Task 4 (roonseek working-tree inspection)
- **Issue:** `~/roonseek`'s `.turingmind/` is untracked-and-NOT-ignored (verified `?? .turingmind/`
  in porcelain). The plan's own STEP-1 clean-tree guard and 8f3 no-untracked assert would be
  permanently unsatisfiable in any repo where `/deep-review`'s state dir isn't ignored.
- **Fix:** STEP 0.5 appends `.turingmind/` to each source repo's `.git/info/exclude`
  (idempotent, purely local, NO working-tree change, nothing committed to source repos).
  Plus a prose PREP NOTE in the roonseek section: its pre-existing dirty state (modified
  `.planning/config.json`, untracked `.orchestrator.json` + a `.planning` file) must be
  committed or moved aside by the owner before its diff block — the guard stays fail-closed.
- **Commit:** `ef0ab67`

**3. [Method note] roonseek proof pair computed via a temporary linked worktree**
- **Found during:** Task 2 — the proof-pair procedure requires a clean detach, but roonseek's
  main checkout carried the owner's uncommitted `.planning/config.json`.
- **Fix:** `git worktree add --detach` at base_sha in the scratchpad, apply + hash there,
  `git worktree remove` after. The owner's checkout was verified byte-untouched before/after.
  No plan output differs; only the computation venue.
- **Commit:** `98e5aff`

**4. [Minor] FAILED-RUN RECOVERY block carries one owner-edited digit (`N=1`)**
- The plan's recovery block is itself parameterized by `<n>` (the failed run number). The
  generated block makes that the single clearly-commented edit (`N=1  # <-- EDIT THIS ONE
  DIGIT...`); everything else is literal. RESUME blocks have zero substitutions as required.

### Checkpoint outcome

Task 2b (`checkpoint:decision`, gate=blocking): returned to orchestrator; owner selected
**confirm-all** → `owner_confirmed: true` recorded in ANSWER-KEY-b3.md and RUN-CHECKLIST.md.

### Candidate-pool findings worth keeping

- roonseek `355c57f` (initially the strongest small product-code quiet candidate) was
  DISQUALIFIED by the line-level survival gate — later commit `ed1c23d` rewrote its
  `library.py` hunk. This validates the codex second-pass fix: the old subject-filtered grep
  would not have caught it (`ed1c23d` is a `feat`).
- Verified `D-10` in should-quiet-1's body does NOT match the fail-closed regex (`DR[0-9]`
  needs `DR`+digit; `DR-` needs the literal hyphen form) — explicitly tested and recorded in
  the sidecar.

## Verification

- All 5 per-task automated verify blocks: PASS (run verbatim from the plan).
- Task-5 digest proof: `git show ef0ab67:...ANSWER-KEY-b3.md | shasum -a 256` ==
  manifest value; `merge-base --is-ancestor` holds.
- 63/63 checklist bash blocks pass `bash -n`; the 8g python assert functionally tested on
  good / carry-forward / wrong-head / missing-file synthetic states (correct exit codes all 4).
- `git diff --quiet -- plugins/vibe-check/scripts/score.py .../test_score.py .../config.py`
  exits 0 — byte-frozen invariant held.
- No committed artifact contains a literal *arr API key (grep gate per artifact; the
  BUGGY.py's only 20+-char runs are comment separators).
- No `runs/` directory exists — pre-registration strictly precedes every future run artifact.

## Known Stubs

None — every artifact is complete git output or fully-authored markdown; no placeholder,
no TODO, no empty value remains (the two proof values live in PREREGISTRATION.md, filled
from git before any run).

## Next steps (Wave 2 → Wave 3)

- **36-02 (owner):** drive the 18 `/deep-review` runs from RUN-CHECKLIST.md. Hard WAIT gate —
  the assistant cannot invoke the skill.
- **36-03 (assistant):** score archived `runs/<id>/run-<n>/state.json` against the committed
  key blob at `ef0ab67`; enforce the manifest gates; write the catch/FP report + D-11
  verdicts into `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md`.
