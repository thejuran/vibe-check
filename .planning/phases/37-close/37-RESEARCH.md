# Phase 37: Close - Research

**Researched:** 2026-07-05
**Domain:** Release / publish ritual (git version bump + annotated tag + push + hash-verify)
**Confidence:** HIGH — every git fact below was verified live against this repo this session.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Publish AS-IS. The committed B3 ground-truth kit (`docs/design/b3-ground-truth/` —
  reversed-fix patches, provenance sidecars naming triggarr/seedsyncarr/roonseek, BUGGY.py,
  18 captured run states) goes public intact with the push. NO history rewrite, NO scrub, NO
  relocation — the pre-registration evidence chain (ANSWER_KEY_COMMIT ancestry through every
  runs/ commit) MUST survive publish byte-identical; rewriting history would destroy the proof
  behind the measured numbers. All underlying bugs are already fixed in the source repos.
- **D-02:** Add a SMALL honest README pointer (3–6 lines): v2.9 ships the first measured
  catch-rate / false-positive-rate — exact fractions (catch 8/9, FP 6/9), the small-N caveat,
  and a link to `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md`. Honesty-first framing; no
  marketing language; do NOT create a CHANGELOG file (no such convention in this repo).
- **D-03:** The ~38 stale deleted-but-uncommitted `.planning` files stay UNTOUCHED this phase —
  no housekeeping commit; they cannot affect the publish (uncommitted changes never merge).
- **D-04:** Publish per the standing directive: merge/ff `main`, push main + tag + branch;
  annotated tag `v2.9`; after push, EXACT-HASH verify local == remote for main, the tag, and
  the branch (the v2.7 gate that caught a real partial-publish).
- **D-05:** Pre-publish gates: `pytest -q` green in `plugins/vibe-check/scripts` (baseline
  356 passed + 221 subtests); after the bump, installed-cache vs repo `plugin.json` parity
  noted (a resync needs a process relaunch — flag it, don't silently skip); version bump is
  exactly 2.8.0 → 2.9.0.
- **D-06:** The milestone audit (CLOSE-01 criterion 3) runs via `/gsd:audit-milestone` and must
  be clean before `complete-milestone`; the wrapper orchestrator drives audit + archive at
  milestone-end — this phase's execution delivers bump + README pointer + tag + publish.

### Claude's Discretion
- Exact README wording and placement of the pointer (keep it in the efficacy/README claims
  neighborhood if one exists; otherwise a short "Measured efficacy" note near the top).
- Whether bump and README pointer land as one commit or two (atomic-per-concern preferred).
- Tag message content — mirror the v2.8 annotated-tag style.

### Deferred Ideas (OUT OF SCOPE)
- Future ground-truth kits' privacy location — owner chose plain publish-as-is, declined a
  standing backlog item. Revisit only if a future kit sources from repos to keep private.
- Post-v2.9 items already on record in STATE.md: security.md critique pass, B3-gated scorer
  design challenges (D-11 PROCEED on H-CORE/H-LANE/B-SEV/B-REWEIGHT at next-milestone scoping),
  CATEGORY_DOMAIN twin proposals, config.py symlink-follow hardening (CWE-61).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLOSE-01 | `plugins/vibe-check/.claude-plugin/plugin.json` bumped 2.8.0 → 2.9.0; annotated tag `v2.9` created; milestone published (merge/ff `main`, push main + tag + branch) | This research supplies the exact bump/tag/push/hash-verify command sequence (replicated from the v2.8 close ritual), the current git-state facts that change the merge step from `--no-ff` to fast-forward, and the exact-hash verification recipe. |
</phase_requirements>

## Summary

Phase 37 is a **pure git release ritual** — no library research, no new code. Bump one JSON
version field (2.8.0 → 2.9.0), add a 3–6 line honest README efficacy pointer, create an
annotated tag `v2.9`, advance `main`, push main + tag + branch, then exact-hash verify
local == remote for all three refs. The v2.8 close is the byte-for-byte template.

**One material difference from the v2.8 close must drive the plan.** v2.8 required a *real
merge* (`--no-ff`) because its source branch had diverged from `main`. For v2.9, this is NOT
the case: `main` (bbecf55) is the exact merge-base of `feat/v2.9` — the branch is **57 commits
ahead and 0 behind**. `main` can therefore **fast-forward** to `feat/v2.9`. Both a fast-forward
and a `--no-ff` merge are valid; the plan should pick fast-forward (cleaner, and the standing
directive says "merge/ff") but must state the choice explicitly so the executor doesn't
blindly copy v2.8's `--no-ff` and produce an unnecessary merge commit. Either way, the plan
must run the bump commit FIRST (on `feat/v2.9`), so the tag lands on the commit that carries
version 2.9.0.

**Primary recommendation:** On `feat/v2.9`: (1) run `pytest -q` gate, (2) commit the version
bump + README pointer, (3) fast-forward `main` to `feat/v2.9`, (4) annotated-tag `v2.9` on the
new `main` tip, (5) push main + tag + `feat/v2.9` branch, (6) exact-hash verify all three refs
local == remote, (7) note the installed-cache lag (expected, not a gate). Leave the
`.planning` worktree churn untouched (D-03). Do NOT put `/gsd:audit-milestone` or archive in an
executor task — the wrapper orchestrator owns those at milestone-end (D-06).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Version bump | Repo / build metadata | — | Single field in `plugins/vibe-check/.claude-plugin/plugin.json`; the marketplace reads it at install time |
| README efficacy pointer | Docs | — | Root `README.md`; user-facing honesty statement, no code impact |
| Advance `main` | Git / release | — | Marketplace pins `ref:main`; advancing main IS the release |
| Annotated tag `v2.9` | Git / release | — | Immutable milestone marker, mirrors v2.1–v2.8 |
| Push + hash-verify | Git / remote (GitHub) | — | The publish + the v2.7 partial-publish safety gate |
| Milestone audit + archive | GSD orchestrator (wrapper) | — | D-06: driven at milestone-end, NOT an executor task |

## Current Git State (verified live 2026-07-05)

These are the load-bearing facts. Every one was confirmed with a command this session.

| Fact | Value | How verified |
|------|-------|--------------|
| Current branch | `feat/v2.9` | `git branch --show-current` |
| `feat/v2.9` tip | `be690f0` | `git rev-parse feat/v2.9` |
| local `main` | `bbecf55` | `git rev-parse main` |
| `origin/main` | `bbecf55` (== local main) | `git ls-remote origin main` |
| merge-base(main, feat/v2.9) | `bbecf55` (== main) → **FF possible** | `git merge-base main feat/v2.9` |
| commits ahead (main..feat/v2.9) | **57** | `git rev-list --count main..feat/v2.9` |
| commits behind (feat/v2.9..main) | **0** | `git rev-list --count feat/v2.9..main` |
| `feat/v2.9` pushed to origin? | **NO — never pushed, no upstream set** | `git ls-remote origin refs/heads/feat/v2.9` (empty); `git rev-parse @{upstream}` → "no upstream configured" |
| remote origin | `https://github.com/thejuran/vibe-check.git` | `git remote -v` |
| plugin.json version on tip | `2.8.0` | `git show feat/v2.9:...plugin.json` |
| source commits ahead touching `plugins/` | 6 (LEGIBLE wiring + RESULTS-v2.9.md; +482/−31 lines, 3 files) | `git log --oneline main..feat/v2.9 -- plugins/` |
| `v2.9` tag exists locally? | **NO** (highest existing tag = `v2.8`) | `git tag --sort=version:refname` |
| `v2.9` tag exists on remote? | **NO** | `git ls-remote --tags origin` |

**Interpretation for the plan:**
- `main` is a strict ancestor of `feat/v2.9` ⇒ advancing `main` is a **fast-forward**, not a
  real merge. (Contrast v2.8, which needed `--no-ff` — see State of the Art below.)
- This publish is the **first push of `feat/v2.9`** — 57 local-only commits become public.
- No `v2.9` tag or remote branch exists yet — nothing to force-overwrite; all pushes are creates.

## The v2.8 Close Ritual (the exact template to replicate)

Reconstructed from `git show` / `git tag -n99` / `git cat-file` this session. The v2.8 release
was two commits + a tag + three pushes:

### 1. Bump commit (v2.8 precedent: `6002cae`)
- **Subject:** `chore(release): bump plugin to 2.8.0`
- **Body:** one paragraph summarizing the milestone's headline changes.
- **Diff:** a single-line change in `plugins/vibe-check/.claude-plugin/plugin.json`:
  `"version": "2.7.0",` → `"version": "2.8.0",`
- Trailer: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

### 2. Merge to main (v2.8 precedent: `f19be14`, a `--no-ff` merge)
- v2.8 was `git merge --no-ff` (parents `294ae43` + `6002cae`) because its source branch had
  diverged. **v2.9 does NOT need this** — `main` fast-forwards. See State of the Art.
- Merge-commit subject style: `Merge v2.8 'Tunable, quieter reviews' (feat/framework-skill-reviewer)`
  followed by a phase-by-phase body. (Only relevant if the plan chooses `--no-ff`; a FF has no
  merge commit and no message.)

### 3. Annotated tag (v2.8 precedent: tag object `dcaa255` → target `f19be14`)
- **Annotated** (`git tag -a`), confirmed: `git cat-file -t v2.8` → `tag` (all of v2.1–v2.8 are
  annotated tag objects, never lightweight).
- Tagger: `thejuran <thejuran@users.noreply.github.com>`.
- **Message style (v2.8, the one to mirror per D-02 discretion):**
  ```
  v2.8 — Tunable, quieter reviews

  .vibe-check.toml config surface (thresholds, disabled, top_model,
  min_confidence, idiom_floor, codex), vibe-ignore reason-aware marker +
  suppression audit, --all legibility, and the Fable second-model review
  remediation: scorer bug fixes, min_confidence critical-floor guard,
  guard.py path-containment extraction, gen-1 agent calibration retrofit.
  356 tests + 221 subtests.
  ```
  Pattern: **subject line `vX.Y — <milestone tagline>`**, blank line, then a wrapped paragraph
  naming the headline features, ending with the test count. (v2.6 also appended the audit verdict
  and a fixed-warning note; v2.7 used a single subject line only. v2.8's format is the richest and
  the one D-02 says to mirror.)

### 4. Push order and refs
- Push `main`, push the tag, push the branch. (The marketplace only reads `main`, but the tag is
  the immutable record and the branch is the traceable source-of-truth.)

### 5. Exact-hash verify (the v2.7 gate that caught a real partial-publish)
- After pushing, compare local vs remote SHAs for **all three refs**. A partial push (e.g. main
  pushed but tag not, or vice-versa) is the exact failure mode this catches.

## Recommended v2.9 Command Sequence

Concrete, ready for the planner to turn into task actions. `$PLUGIN_JSON =
plugins/vibe-check/.claude-plugin/plugin.json`.

```bash
# --- PRE-FLIGHT GATE (D-05) ---
cd plugins/vibe-check/scripts && pytest -q          # expect: 356 passed, 221 subtests passed
cd -                                                # back to repo root

# --- STEP 1: bump + README pointer, on feat/v2.9 ---
git branch --show-current                           # MUST be feat/v2.9 before committing
# edit $PLUGIN_JSON:  "version": "2.8.0"  ->  "version": "2.9.0"
# edit README.md: add the 3-6 line efficacy pointer (see README Pointer section)
git add plugins/vibe-check/.claude-plugin/plugin.json README.md
git commit -m "chore(release): bump plugin to 2.9.0" -m "<milestone summary paragraph>" \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
#   (Discretion D: atomic-per-concern is preferred — the planner may split into two commits,
#    one for the bump and one for the README pointer. Either is acceptable.)

# --- STEP 2: advance main by FAST-FORWARD (main is 0 behind feat/v2.9) ---
git checkout main
git merge --ff-only feat/v2.9                        # pure fast-forward; no merge commit
#   Rationale: merge-base(main, feat/v2.9) == main, so --ff-only succeeds. If it ever errors
#   "not possible to fast-forward", STOP — the state assumption changed; do not silently --no-ff.

# --- STEP 3: annotated tag on the new main tip ---
git tag -a v2.9 -m "v2.9 — Prove it" -m "<mirror the v2.8 tag body: headline features + 8/9 · 6/9 numbers + 356 tests + 221 subtests>"
git cat-file -t v2.9                                 # expect: tag  (proves annotated, not lightweight)

# --- STEP 4: push main, tag, branch ---
git push origin main
git push origin v2.9
git push origin feat/v2.9

# --- STEP 5: EXACT-HASH VERIFY (D-04) — local == remote for all three refs ---
# main:
test "$(git rev-parse main)" = "$(git ls-remote origin main | cut -f1)" && echo "main OK" || echo "main MISMATCH"
# tag (compare the tag OBJECT sha, i.e. refs/tags/v2.9 not the ^{} peel):
test "$(git rev-parse v2.9)" = "$(git ls-remote origin refs/tags/v2.9 | grep -v '\^{}' | cut -f1)" && echo "tag OK" || echo "tag MISMATCH"
# branch:
test "$(git rev-parse feat/v2.9)" = "$(git ls-remote origin refs/heads/feat/v2.9 | cut -f1)" && echo "branch OK" || echo "branch MISMATCH"
```

**Tag SHA gotcha (verified):** `git ls-remote --tags` returns TWO lines per annotated tag —
`refs/tags/v2.9` (the tag object) and `refs/tags/v2.9^{}` (the peeled commit). `git rev-parse
v2.9` returns the **tag object** sha. So compare against the non-`^{}` line (grep -v). For v2.8
these were `dcaa255` (object) and `f19be14` (peeled commit) — different SHAs. Comparing the wrong
one produces a false MISMATCH.

## README Pointer (D-02) — placement and content

**README structure (root `/README.md`, 295 lines, verified):**
- L18 `## 📦 What is This?` (ends ~L26)
- L28 `## 🚀 Quick Start`
- L59 `## ⚙️ Configuration`
- L115 `## ✨ Features`
- L195 `## 📸 Example Output`
- L246 `## 🏗️ Architecture`
- L273 `## ⚠️ Limitations`
- L285 `## 📄 License`

**There is no existing "efficacy" or "claims" section** in the README. Per D-02 discretion, the
best fit is a **short "Measured efficacy" note near the top** — recommended placement: a new
section between `## 📦 What is This?` (ends L26) and `## 🚀 Quick Start` (L28), OR appended to
the `## ⚠️ Limitations` section (L273–281), which already frames honest capability boundaries and
is thematically adjacent to a small-N caveat. The near-top placement gives the honesty statement
prominence; the Limitations placement co-locates it with the existing caveats. **Recommend
near-top** (a reader should see the measured number before the marketing-adjacent Features table).

**Content facts to cite (all verified in `RESULTS-v2.9.md` this session):**
- Headline line in the doc (L248): **"Headline: catch-rate 8/9 · false-positive-rate 6/9"** (exact
  fractions, no rounding).
- Small-N caveat present (L344): "Small N. N=3 per diff (9 catch runs, 9 quiet runs total)."
- Sourcing caveat: organic-only, four repos.
- Link target: `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` (tracked in git — confirmed via
  `git ls-files`; 40 KB).

**Sample pointer (planner may reword — no marketing language, D-02):**
```markdown
## 📊 Measured Efficacy

v2.9 ships vibe-check's first measured quality numbers, from 18 owner-run `/deep-review`
passes over an organic ground-truth set: **catch-rate 8/9, false-positive-rate 6/9**.
These are small-N (N=3 per diff, four repos, organic-only) — indicative, not statistically
tight. Full method, per-diff scoring, and limitations:
[`docs/efficacy/RESULTS-v2.9.md`](plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md).
```
(5 lines of prose + heading. Do NOT create a CHANGELOG file — no such convention here, D-02.)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Advance main | A scripted rebase/cherry-pick pipeline | `git merge --ff-only feat/v2.9` | main is 0 behind; a plain fast-forward is the whole operation |
| Verify publish landed | Trust `git push` exit code alone | Exact-SHA `git rev-parse` vs `git ls-remote` per ref | v2.7 caught a real partial-publish this way; exit code 0 is not proof all three refs landed |
| Milestone audit | An executor task running `/gsd:audit-milestone` | Let the wrapper orchestrator drive it at milestone-end (D-06) | Duplicating it fights the orchestrator; the audit runs once, after this phase's bump/tag/publish |
| Worktree cleanup | A housekeeping commit for the 38 stale `.planning` deletions | Leave them untouched (D-03) | They are gitignored/unstaged — they never merge and cannot affect the publish |

**Key insight:** This phase's only real risk is a *partial* publish or a *wrong-ref* comparison
in the verify step — not anything in the bump itself. Spend the rigor on the hash-verify, not on
elaborate merge machinery.

## Common Pitfalls

### Pitfall 1: Blindly copying v2.8's `--no-ff` merge
**What goes wrong:** v2.8's SUMMARY/tag shows a real merge commit (`f19be14`). Copying that for
v2.9 creates an unnecessary merge commit and a non-linear main.
**Why it happens:** The v2.8 close is the template, and its merge was `--no-ff`.
**How to avoid:** Verified: `main` is 0 commits behind `feat/v2.9`, so `--ff-only` is correct and
cleaner. Use `git merge --ff-only feat/v2.9`. If it errors, STOP and re-check state — do not fall
back to `--no-ff` silently.
**Warning signs:** `git merge` opens an editor for a merge-commit message → you're not on the FF path.

### Pitfall 2: Comparing the wrong tag SHA in the verify step
**What goes wrong:** `git ls-remote --tags` lists both `v2.9` (tag object) and `v2.9^{}` (peeled
commit). Comparing `git rev-parse v2.9` (tag object) against the `^{}` line reports a false MISMATCH.
**How to avoid:** Compare against `refs/tags/v2.9` WITHOUT the `^{}` suffix (grep -v '\^{}').
**Warning signs:** A "tag MISMATCH" while main and branch both verify OK — almost always this.

### Pitfall 3: Tag lands on the pre-bump commit
**What goes wrong:** Tagging before the bump commit is created (or before FF), so `v2.9` points at
a commit whose plugin.json still says 2.8.0.
**How to avoid:** Order is fixed — bump commit FIRST, FF main SECOND, tag THIRD (on the new tip).
Sanity: `git show v2.9:plugins/vibe-check/.claude-plugin/plugin.json | grep version` must read 2.9.0.
**Warning signs:** The tagged tree shows 2.8.0.

### Pitfall 4: Partial push (main without tag, or tag without main)
**What goes wrong:** The marketplace pins `ref:main`, so pushing main alone technically "releases",
but the immutable tag and the public branch are the traceable record. A half-push leaves the
release under-documented and is the exact defect the v2.7 gate caught.
**How to avoid:** Push all three; then run the three-way exact-hash verify. Do not declare the
phase done until all three print OK.
**Warning signs:** Any of the three verify comparisons prints MISMATCH.

### Pitfall 5: Accidentally committing the stale `.planning` churn (D-03)
**What goes wrong:** `git add -A` or `git commit -a` sweeps in the 38 deleted + 3 modified
`.planning` files, polluting the release commit.
**How to avoid:** Stage ONLY `plugin.json` and `README.md` explicitly (`git add <paths>`), never
`-A`/`-a`. Verified: all 41 pending worktree changes are inside `.planning/` and none is staged —
they will not merge unless explicitly added.
**Warning signs:** `git status` after staging shows `.planning/...` in "Changes to be committed".

### Pitfall 6: Treating the installed-cache lag as a failure
**What goes wrong:** After the bump, the installed plugin cache (latest = `2.8.0` at
`~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/`, verified) still lags the repo's 2.9.0.
Someone gates on parity and blocks the release.
**Why it happens:** Chronic-stale-cache gotcha (poisoned 4 of the last 5 milestones) — but that
pre-flight applies to *dogfood/smoke runs*, not to the publish.
**How to avoid:** This is EXPECTED post-publish. The cache updates on the user's next
`/plugin update` + process RELAUNCH. NOTE it (D-05), do not gate on it. The pytest gate runs
against the repo `scripts/`, not the cache, so it is unaffected.

## Runtime State Inventory

This is a release phase (version bump + docs + git refs), not a rename/refactor. No stored data,
service config, OS registrations, secrets, or build artifacts embed a renamed string. The one
"runtime state" analog:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastore keys change | None |
| Live service config | Claude Code **marketplace** (`thejuran/marketplace`) pins `"ref": "main"` — verified via the marketplace.json on GitHub. Pushing `main` IS the release; no marketplace edit needed. | None — advancing main auto-publishes |
| OS-registered state | Installed plugin cache at `~/.claude/plugins/cache/thejuran/vibe-check/` (latest 2.8.0). Updates only on user `/plugin update` + relaunch. | None this phase — EXPECTED lag (D-05); note, don't gate |
| Secrets/env vars | None | None |
| Build artifacts | `plugins/vibe-check/scripts/__pycache__` — irrelevant to publish | None |

**Nothing found requiring migration.** The only externally-visible state is `main` and the tag,
both handled by the push + verify.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The wrapper orchestrator (not an executor task) runs `/gsd:audit-milestone` + archive at milestone-end | D-06 / Don't Hand-Roll | If the plan omits the audit AND the orchestrator doesn't run it, CLOSE-01 criterion 3 (audited) is unmet. Mitigation: D-06 states this explicitly; the plan should note the boundary, not the task. LOW risk — matches every prior milestone close. |
| A2 | Fast-forward is preferred over `--no-ff` for advancing main | Command Sequence / Pitfall 1 | If the owner prefers a merge commit for milestone visibility (as v2.8 had), the plan should use `--no-ff` instead. Both satisfy "merge/ff" in D-04. This is a reversible one-line choice; flagged for the planner. |
| A3 | README pointer belongs near-top (new `## 📊 Measured Efficacy` section after "What is This?") | README Pointer | Placement is explicit Claude's-discretion (D-02); the alternative (append to Limitations) is equally valid. Low risk — cosmetic. |

**Everything else in this research is VERIFIED live against the repo or CITED from tracked files.**

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| git | Every step | ✓ | (system) | — |
| pytest | Pre-flight gate (D-05) | ✓ | ran clean: 356 passed + 221 subtests in 0.73s | — |
| Network / GitHub push access | Push + verify | Assumed ✓ (origin is HTTPS `github.com/thejuran/vibe-check`) | — | If push auth fails, this is the one true blocker; not testable non-destructively pre-push |

**Missing dependencies with no fallback:** None identified. Push authentication to
`github.com/thejuran/vibe-check` is the only unverifiable-without-executing prerequisite.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (with pytest-subtests) |
| Config file | none dedicated; tests live in `plugins/vibe-check/scripts/` (test_score.py, test_config.py, test_guard.py) |
| Quick run command | `cd plugins/vibe-check/scripts && pytest -q` |
| Full suite command | same — `pytest -q` in that dir IS the full suite for this repo |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLOSE-01 | plugin.json reads 2.9.0 | assertion | `grep '"version": "2.9.0"' plugins/vibe-check/.claude-plugin/plugin.json` | ✅ (file exists; value bumped in-phase) |
| CLOSE-01 | annotated tag `v2.9` exists | assertion | `git cat-file -t v2.9` → `tag` | ✅ (created in-phase) |
| CLOSE-01 | tag points at 2.9.0 tree | assertion | `git show v2.9:plugins/vibe-check/.claude-plugin/plugin.json \| grep 2.9.0` | ✅ |
| CLOSE-01 | main published (local==remote) | assertion | exact-hash verify block (Command Sequence Step 5) | ✅ |
| D-05 | scorer suite still green | regression | `cd plugins/vibe-check/scripts && pytest -q` | ✅ (356+221 baseline, verified green this session) |

### Sampling Rate
- **Per task commit:** `git status` (confirm only plugin.json/README.md staged, no `.planning`).
- **Pre-publish gate:** `pytest -q` green in `plugins/vibe-check/scripts`.
- **Phase gate:** all three refs verify local == remote before declaring done.

### Wave 0 Gaps
None — no new test files needed. The release ritual is validated by the pytest baseline (already
green) plus the git-state assertions above. `score.py` / `test_score.py` / `config.py` stay
byte-frozen this phase (standing constraint; nothing in Phase 37 touches them).

## Security Domain

Release-ritual phase; no application code changes. ASVS input-validation / crypto / auth
categories do not apply to a version bump + tag + push. The one security-adjacent point is the
**D-01 publish-as-is decision**: the B3 ground-truth kit (81 tracked files under
`docs/design/b3-ground-truth/`, including reversed-fix `.BUGGY.py` files and provenance sidecars
naming triggarr/seedsyncarr/roonseek) goes public.

| Consideration | Assessment |
|---------------|------------|
| Does the kit leak live secrets? | The triggarr-secret-in-logs case is a **reversed fix** — the "secret" is a demonstration of a leak pattern, and the owner states all underlying bugs are already fixed in the source repos (D-01). Not a live credential. |
| Does publishing rewrite/expose history? | D-01 forbids any rewrite; the pre-registration ancestry (ANSWER_KEY_COMMIT `ef0ab67` → runs) MUST survive byte-identical. A rewrite would DESTROY the evidence chain — so the security posture is: **do nothing to history**, push as-is. |
| Any secrets in the release commit itself? | No — the release commit is a one-line version bump + a README pointer. Stage explicitly (Pitfall 5) so nothing unexpected rides along. |

**STRIDE:** The only relevant category is *Information Disclosure* (the kit going public), which
the owner has explicitly adjudicated and accepted (D-01). No mitigation action for this phase.

## State of the Art

| Old Approach (v2.8 close) | Current Approach (v2.9 close) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `git merge --no-ff` (source branch had diverged from main) | `git merge --ff-only` (main is 0 behind feat/v2.9) | This milestone — verified state | No merge commit; linear main. The plan must NOT copy v2.8's `--no-ff`. |
| Merge into main from a branch main was behind | First-ever push of feat/v2.9 (57 local-only commits) | This milestone | The publish moment for the entire milestone; branch push is a create, not an update |
| Tag message: single line (v2.7) | Rich body: tagline + feature paragraph + test count (v2.8) | v2.8 | D-02 says mirror v2.8's style; add the 8/9 · 6/9 numbers |

**Deprecated/outdated for this phase:**
- Do not create a `CHANGELOG` file — no such convention in this repo (D-02).
- Do not run `/gsd:audit-milestone` or archive as an executor task — the wrapper orchestrator owns
  them at milestone-end (D-06).

## Open Questions (RESOLVED)

1. **Fast-forward vs. `--no-ff` merge for advancing main**
   - RESOLVED: `git merge --ff-only feat/v2.9` (locked in 37-01 Task 2; STOP if not fast-forwardable — do not fall back to `--no-ff` silently).
   - What we know: main is 0 behind feat/v2.9, so both are valid; D-04 says "merge/ff".
   - What's unclear: whether the owner wants a visible merge commit on main for milestone
     legibility (v2.8 had one) or a clean linear history (FF).
   - Recommendation: use `--ff-only` (cleaner, and there's nothing to merge). Flag the choice in
     the plan so the executor makes it deliberately, not by copying v2.8.

2. **README pointer placement — near-top vs. Limitations section**
   - RESOLVED: near-top `## 📊 Measured Efficacy` section between "What is This?" and "Quick Start" (locked in 37-01 Task 1).
   - What we know: no existing efficacy section; D-02 leaves placement to discretion.
   - What's unclear: owner's aesthetic preference.
   - Recommendation: near-top (`## 📊 Measured Efficacy` after "What is This?"). Reversible.

## Sources

### Primary (HIGH confidence — verified live this session)
- Local git repo `github.com/thejuran/vibe-check` @ `feat/v2.9` — `git rev-parse`, `git ls-remote`,
  `git merge-base`, `git rev-list --count`, `git tag --sort`, `git cat-file`, `git show`,
  `git log`, `git status --porcelain`, `git remote -v` (all commands + outputs captured this session)
- `git tag -n99 v2.8 v2.7 v2.6` — exact annotated-tag message styles
- `git show 6002cae` / `git show f19be14` — the v2.8 bump commit and merge commit (the ritual template)
- `pytest -q` in `plugins/vibe-check/scripts/` — baseline confirmed: **356 passed, 221 subtests passed**
- `plugins/vibe-check/.claude-plugin/plugin.json` — current version `2.8.0` (the field to bump)
- `README.md` (root, 295 lines) — full section map for pointer placement
- `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` — headline "catch-rate 8/9 · false-positive-rate 6/9" (L248), small-N caveat (L344); tracked in git
- `git ls-files docs/design/b3-ground-truth/*` — 81 tracked files (the D-01 publish-as-is kit)
- `~/.claude/plugins/cache/thejuran/vibe-check/` — installed cache latest = 2.8.0 (the lag gotcha)

### Secondary (MEDIUM confidence)
- `github.com/thejuran/marketplace` marketplace.json (via WebFetch) — vibe-check entry pins
  `"ref": "main"`, `"source": "git-subdir"`, `"path": "plugins/vibe-check"`. Confirms pushing main
  IS the release.

### Tertiary (LOW confidence)
- None. No unverified claims in this research.

## Metadata

**Confidence breakdown:**
- Git state facts: HIGH — every value verified with a live command, outputs captured.
- Ritual template: HIGH — reconstructed directly from the v2.8 commit/tag objects.
- README pointer content: HIGH — fractions and caveats read from the tracked RESULTS-v2.9.md.
- FF-vs-merge choice: HIGH on the mechanics (main is 0 behind, verified), MEDIUM on the
  preference (owner aesthetic — flagged as Open Question 1).

**Research date:** 2026-07-05
**Valid until:** Until the next commit lands on `feat/v2.9` or `main` moves — the SHA facts
(bbecf55, be690f0, "57 ahead / 0 behind") are point-in-time. Re-verify `git rev-parse main
feat/v2.9` and `git rev-list --count feat/v2.9..main` at execution time. The ritual template and
README structure are stable.
