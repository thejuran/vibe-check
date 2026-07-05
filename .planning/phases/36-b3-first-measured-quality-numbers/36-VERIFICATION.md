---
phase: 36-b3-first-measured-quality-numbers
verified: 2026-07-05T18:21:55Z
status: passed
score: 12/12 must-haves verified
has_blocking_gaps: false
overrides_applied: 0
---

# Phase 36: B3 — First Measured Quality Numbers Verification Report

**Phase Goal:** vibe-check gets its first measured catch-rate and false-positive-rate against
organic bugs from the owner's own repos, with a committed reusable test set. Build the run-kit
(3rd should-catch diff = triggarr secret-in-logs; ≥2 should-quiet diffs; per-diff answer key
folding in A8 /health name-exemption + A16 axis-vs-site ambiguity; owner run-checklist), owner
drives /deep-review N=3 per diff, assistant scores vs key and writes the catch/FP report into
plugins/vibe-check/docs/efficacy/.

**Verified:** 2026-07-05T18:21:55Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A committed organic ground-truth test set exists (≥3 should-catch + ≥2 should-quiet, ORGANIC-ONLY, per-diff answer key with A8/A16 folded), pre-registered before any run | ✓ VERIFIED | 3 should-catch (`triggarr-secret-in-logs`, `triggarr-autoescape`, `third-organic-should-catch`) + 3 should-quiet (`should-quiet-{1,2,3}`) patches exist under `docs/design/b3-ground-truth/diffs/`, each with a `.provenance` sidecar recording the fail-closed organic regex check, base_sha, pure-M name-status, and the full-worktree proof pair. `ANSWER-KEY-b3.md` contains explicit SITE/AXIS/BAND rows and an A8 preamble ("an exemption must be justified by content... never by name — a route named `/health`...") plus an A16 three-gate rule section — both independently read from the committed blob at `ef0ab67`. |
| 2 | Answer key is provably pre-registered via a SEPARATE manifest (PREREGISTRATION.md), immutable once runs begin | ✓ VERIFIED | Independently recomputed: `git show ef0ab67:...ANSWER-KEY-b3.md \| shasum -a 256` = `1463544803...` — matches `PREREGISTRATION.md`'s recorded `ANSWER_KEY_SHA256` exactly. `git merge-base --is-ancestor ef0ab67 HEAD` exits 0. Manifest commit `cca63e2` is the ONLY commit ever touching `PREREGISTRATION.md`, and it strictly precedes `FIRST_RUNS_COMMIT` (`eca98ec`) — `git log eca98ec..HEAD -- PREREGISTRATION.md` prints nothing (no post-run edit). |
| 3 | Every diff is run N=3 and scored (owner ran /deep-review on each test diff three times; every run scored against the answer key) | ✓ VERIFIED | All 18 `runs/<id>/run-<n>/state.json` exist (6 diffs × 3 runs) and independently parse: every one has `len(passes)==1` and `head_sha` equal to its diff's recorded base_sha (spot-checked all 18 programmatically, all PASS). `git status --porcelain docs/design/b3-ground-truth/runs/` is empty; all 19 commits touching `runs/` descend from both `ANSWER_KEY_COMMIT` and `MANIFEST_COMMIT` (independently verified via `git merge-base --is-ancestor` loop over all 19 commits — all PASS). |
| 4 | A measured catch-rate/FP-rate report lands in plugins/vibe-check/docs/efficacy/ with limitations stated honestly | ✓ VERIFIED | `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` has an appended top-level "B3" section (line 246+) with headline catch-rate 8/9, FP-rate 6/9 as exact fractions, a "Method" section, per-diff scoring tables, and a "Honest limitations" section enumerating small-N, four-repos, organic-only, single-threshold, Codex-nondeterminism, and pinned-base-scope caveats. No `RESULTS-v3.md` was created (confirmed absent). |
| 5 | The report states what the numbers imply for the B3-gated scorer design challenges (proceed/don't/need-more-data per D-11) | ✓ VERIFIED | RESULTS-v2.9.md's "D-11 verdict" section states PROCEED on H-CORE/H-LANE/B-SEV/B-REWEIGHT and NEED-MORE-DATA on the coarse N=3 rate, explicitly not an in-phase scorer change. Cross-checked: all six challenge codes (H-CORE, H-DUP, H-LANE, B-SEV, B-XCONF, B-PROX, B-REWEIGHT) are pre-registered verbatim in the committed key blob's D-11 table (`git show ef0ab67:...ANSWER-KEY-b3.md`) with matching trigger definitions — the mapping in the report was not invented post-hoc. |
| 6 | Scoring reads ONLY from the committed answer-key blob at ANSWER_KEY_COMMIT (never the live working file) | ✓ VERIFIED | `SCORING-b3.md` §1(c) documents materializing the blob to a scratch path and scoring only from it; §1(d) records the live-file identity check as a WARNING-only sanity check (empty diff found — no drift, but scoring didn't depend on that). Independently confirmed the manifest-ordering derivation, ancestry, and digest match against live git history (see truth #2). |
| 7 | Aggregation only over complete denominators (18/18 scoreable runs, no waiver) | ✓ VERIFIED | SCORING-b3.md §2 scoreable-completeness ledger shows 3/3 per diff for all 6 diffs, "Owner waiver: NONE (and none needed)". Independently confirmed all 18 runs pass isolation+pin gate; headline catch-rate denominator = 9 (3 should-catch diffs × 3), FP-rate denominator = 9 (3 should-quiet diffs × 3) — the full pre-registered set, not a subset. The two `should-quiet-1/run-2.failed-*` dirs are correctly excluded by construction (only run-1/2/3 enumerated). |
| 8 | score.py/test_score.py/config.py are byte-frozen this phase | ✓ VERIFIED | `git diff --quiet -- plugins/vibe-check/scripts/{score.py,test_score.py,config.py}` exits 0 (no uncommitted changes). No commit in the phase's date range (2026-07-02 through 2026-07-05) touches any of these three files (`git log --since=2026-07-03 --until=2026-07-06 -- <files>` returns empty). `pytest -q` in `plugins/vibe-check/scripts` independently re-run: 356 passed, 221 subtests — matches the SUMMARY's claimed regression-guard result exactly. |
| 9 | Every committed patch (should-catch AND should-quiet) is PURE-M (no A/D/R/C) | ✓ VERIFIED | Every `.provenance` sidecar contains a `name-status:` block; spot-checked `triggarr-secret-in-logs.provenance` shows `M\ttriggarr/clients/base.py` only. All 6 sidecars carry this evidence. |
| 10 | No committed patch or BUGGY file contains a literal *arr API key | ✓ VERIFIED | `grep -rn -iE "api[_-]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9]{16,}"` across all `.patch`/`.BUGGY.py` files returns nothing. Additionally spot-checked the archived `triggarr-secret-in-logs/run-1/state.json` findings for 20+-char tokens in finding text/current_code — only `stable_hash` values (expected) appear; no secret-shaped tokens. |
| 11 | Planted-diff integrity verified over the WHOLE worktree (tree.diff sha consistent across all 3 runs per diff, matching kit-build EXPECTED_TREE_DIFF_SHA256) | ✓ VERIFIED | Independently recomputed `shasum -a 256` on all 18 `tree.diff` files and compared against both the sibling `tree.diff.sha256` file and the diff's `.provenance` `EXPECTED_TREE_DIFF_SHA256` value — all 18 match exactly (6 diffs × 3 runs, zero mismatches). |
| 12 | Requirements B3-01/B3-02/B3-03 are satisfied and correctly traced | ✓ VERIFIED | REQUIREMENTS.md marks all three `Complete` under Phase 36; plan frontmatter declares `requirements: [B3-01]` (36-01), `[B3-02]` (36-02), `[B3-02, B3-03]` (36-03) — union covers exactly the three IDs REQUIREMENTS.md maps to Phase 36. No orphaned requirement IDs found. |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/design/b3-ground-truth/diffs/*.patch` (+`.provenance`) | 6 organic patches, byte-exact git output, sidecar provenance | ✓ VERIFIED | All 6 exist; sidecars carry base_sha, EXPECTED_TREE_DIFF_SHA256, EXPECTED_TOUCHED_PATHS, name-status, organic-regex check |
| `docs/design/b3-ground-truth/ANSWER-KEY-b3.md` | SITE+AXIS+BAND key, A8/A16 folded, D-11 table | ✓ VERIFIED | Present, digest-verified against committed blob at `ef0ab67`; A8/A16 sections present; D-11 table present with all 7 challenge rows |
| `docs/design/b3-ground-truth/PREREGISTRATION.md` | Separate fail-closed manifest | ✓ VERIFIED | Present, single commit `cca63e2`, strictly precedes first runs/ commit, immutability held (no post-run edit) |
| `docs/design/b3-ground-truth/RUN-CHECKLIST.md` | Owner copy-paste checklist | ✓ VERIFIED | Present (162KB); referenced correctly by 36-02 SUMMARY as the followed procedure |
| `docs/design/b3-ground-truth/runs/` | 18 scoreable per-run artifacts | ✓ VERIFIED | All 18 `run-<n>/{state.json,tree.diff,tree.diff.sha256}` present and pass isolation/pin/integrity checks; `git status --porcelain` clean |
| `docs/design/b3-ground-truth/SCORING-b3.md` | Auditable per-run scoring worksheet with gate header | ✓ VERIFIED | Present (17.6KB); all gate results independently re-derived and matched; per-run SITE/AXIS/BAND verdicts present for all 18 runs |
| `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` | Appended B3 catch/FP report | ✓ VERIFIED | New top-level section appended (no new file created); contains headline numbers, method, limitations, D-11 verdict, plain-language summary |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `diffs/*.patch` | source-repo clone detached at base_sha | `git switch --detach` + HEAD-assert + `git apply --check` | ✓ WIRED | Per-run `head_sha` in every state.json equals the diff's recorded base_sha (18/18) |
| Applied patch | `runs/<id>/run-<n>/tree.diff` (+sha256) | full `git diff` archival + sha256 match across all 3 runs | ✓ WIRED | Independently recomputed; all 18 shas match sibling sha256 file and `.provenance` kit-build value |
| `ANSWER-KEY-b3.md` (committed blob) | `SCORING-b3.md` | score-from-blob pre-registration gate (MANIFEST_COMMIT derivation + digest + ancestry) | ✓ WIRED | Independently re-derived MANIFEST_COMMIT (`cca63e2`), re-verified digest match and ancestry — all hold |
| `PREREGISTRATION.md` | `git show ANSWER_KEY_COMMIT:...ANSWER-KEY-b3.md` | shasum -a 256 == ANSWER_KEY_SHA256 | ✓ WIRED | Recomputed digest matches exactly |
| `SCORING-b3.md` | `RESULTS-v2.9.md` | D-09 aggregation → headline numbers + D-11 verdict | ✓ WIRED | Aggregation in RESULTS-v2.9.md (8/9, 6/9) matches SCORING-b3.md §5 arithmetic exactly |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| RESULTS-v2.9.md B3 section | catch-rate 8/9, FP-rate 6/9 | SCORING-b3.md per-run verdicts, derived from `state.passes[-1].findings[]` in 18 real committed `state.json` files | Yes — traced to real `/deep-review` output, not static/hardcoded | ✓ FLOWING |
| SCORING-b3.md verdicts | SITE/AXIS/BAND per finding | Real archived findings (spot-checked `triggarr-autoescape/run-1` and `triggarr-secret-in-logs/run-1` finding text directly) | Yes — finding titles/categories/bands independently read and cross-checked against the reported verdict | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| score.py/test_score.py/config.py byte-frozen | `git diff --quiet -- <3 files>` | exit 0 | ✓ PASS |
| No commits touch frozen files within phase range | `git log --since=2026-07-03 --until=2026-07-06 -- <3 files>` | empty | ✓ PASS |
| Regression suite green | `pytest -q` (plugins/vibe-check/scripts) | 356 passed, 221 subtests | ✓ PASS |
| Manifest ordering derivation | `git log --reverse -- runs/`, `git log FIRST_RUNS_COMMIT..HEAD -- PREREGISTRATION.md` | FIRST_RUNS_COMMIT=`eca98ec`; post-run edit check empty | ✓ PASS |
| Key ancestry + digest | `git merge-base --is-ancestor ef0ab67 HEAD`; `git show ef0ab67:...\|shasum -a 256` | exit 0; digest matches manifest exactly | ✓ PASS |
| runs/ clean + full descent (19 commits) | `git status --porcelain runs/`; merge-base loop over all 19 commits | empty; all 19 pass both key+manifest ancestry | ✓ PASS |
| Per-run isolation/pin gate (18 runs) | Python: `len(passes)==1`, `head_sha==base_sha` | All 18 PASS | ✓ PASS |
| tree.diff integrity (18 runs) | `shasum -a 256` recompute vs sibling `.sha256` vs `.provenance` value | All 18 match (zero mismatches) | ✓ PASS |
| Literal secret scan | grep for API-key-shaped tokens in patches/BUGGY files + spot-checked state.json | Clean | ✓ PASS |
| No RESULTS-v3.md created | `test -e RESULTS-v3.md` | Does not exist | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| B3-01 | 36-01 | Committed ground-truth test set + answer key with A8/A16 folded | ✓ SATISFIED | 6 patches + sidecars + ANSWER-KEY-b3.md all present, digest-verified, A8/A16 sections present |
| B3-02 | 36-02, 36-03 | Owner runs /deep-review N=3 per diff; every run scored against answer key | ✓ SATISFIED | 18/18 runs archived, committed, isolation/pin/integrity-verified; all scored in SCORING-b3.md |
| B3-03 | 36-03 | Catch-rate/FP-rate report with honest limitations + D-11 verdict | ✓ SATISFIED | RESULTS-v2.9.md B3 section: 8/9, 6/9, 6 numbered limitations, D-11 verdict with challenge mapping |

No orphaned requirements — REQUIREMENTS.md lists exactly B3-01/B3-02/B3-03 for Phase 36, and all three appear in plan frontmatter `requirements:` fields.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| docs/design/b3-ground-truth/B3-STATUS.md | 1-3 | Stale status header ("RUN-KIT BUILT — Wave 2 owner runs pending") not updated after 36-02/36-03 completed | ℹ️ Info | Not a scored deliverable of any plan's `files_modified`; cosmetic only — the authoritative status lives in SCORING-b3.md/RESULTS-v2.9.md/REQUIREMENTS.md, all of which are current and correct |

No debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER) found in any scored deliverable file (SCORING-b3.md, RESULTS-v2.9.md, ANSWER-KEY-b3.md, PREREGISTRATION.md). The one grep hit was a documentation sentence in ANSWER-KEY-b3.md explaining the ABSENCE of self-referential placeholders, not an actual stub.

### Human Verification Required

None. All must-haves are independently verifiable via git history, file content, and hash recomputation. No visual, real-time, or subjective-judgment items remain — the one subtle judgment call in the phase (autoescape run-1 catch-vs-miss) was independently re-derived from the raw finding text and matches the documented verdict.

### Gaps Summary

No gaps. All 12 derived observable truths (roadmap's 4 success criteria plus 8 supporting technical
truths drawn from PLAN frontmatter must_haves) verify against the actual codebase — not just
SUMMARY.md narrative. Independent recomputation (not trust) was used throughout: git history
ancestry/ordering, SHA-256 digests on both the answer-key blob and all 18 tree.diff archives, the
isolation/pin gate on all 18 raw state.json files, and direct inspection of finding text behind
the two most consequential scoring judgments (the autoescape MISS and the secret-in-logs security
spot-check). The one minor finding (stale B3-STATUS.md header) is cosmetic and does not affect any
must-have.

---

*Verified: 2026-07-05T18:21:55Z*
*Verifier: Claude (gsd-verifier)*
