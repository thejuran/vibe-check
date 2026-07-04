# B3 RUN-CHECKLIST — owner-driven `/deep-review` measurement runs (N=3 per diff)

**Kit built:** 2026-07-03 (Phase 36 Plan 36-01). 6 diffs x 3 runs = 18 runs, resumable at ANY
run boundary across days. Every step is copy-paste EXCEPT the single `/vibe-check:deep-review`
line per run (the one user action — the assistant cannot invoke it).

**owner_confirmed: true** — the should-quiet picks were confirmed as-is at the Task-2b
checkpoint (D-02), so runs may start once the gates below pass.

**Answer key:** `docs/design/b3-ground-truth/ANSWER-KEY-b3.md` (pre-registered; scoring rules
D-07/D-08/D-09 live there). **Proof manifest:** `docs/design/b3-ground-truth/PREREGISTRATION.md`.

---

## MEASUREMENT-RUN RULE — the `/deep-review` fix loop (read this FIRST)

**When `/deep-review` finds something it will enter an interactive Phase 5 fix loop. On EVERY
run you DECLINE/SKIP all fixes and EXIT the loop WITHOUT applying:** at Step A ("How do you
want to handle the N finding(s) above?") pick **"Skip fixes this pass"** (option 4); at Step C
("Pass N loop — what's next?") pick **"Abandon for now"** (option 3). Do NOT pick "Rerun
review on the new diff" (a re-run appends a second pass and breaks the `len(passes)==1`
sample). Do NOT pick "Close out and document" / `--finalize`. Do NOT let the fix agent commit
anything into the source repo (a commit moves HEAD off the pinned base_sha and fails the head
assert). You are MEASURING the tool, not fixing the code.

## Pre-registration gate (before ANY run)

Read the pre-registration values from `docs/design/b3-ground-truth/PREREGISTRATION.md` (NOT
from the key file — the key blob never contains its own hash). **PREREGISTRATION.md is
IMMUTABLE from your first run commit onward — never edit it; Wave 3 derives MANIFEST_COMMIT
(the last manifest commit strictly preceding the first `runs/` commit) and hard-fails on any
manifest commit after (or landing together with) the first `runs/` commit.**

Mirror of the manifest values (recorded at pre-registration, 2026-07-03 — the gate below
still READS them from PREREGISTRATION.md; this mirror is for eyeball cross-checking only):
`ANSWER_KEY_COMMIT = ef0ab67cb45957167c99eff468077348432e1474` ·
`ANSWER_KEY_SHA256 = 1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1`

Do not start runs unless this fail-closed block passes:

```bash
set -euo pipefail
cd ~/turingmind-code-review
M=docs/design/b3-ground-truth/PREREGISTRATION.md
test -s "$M" || { echo 'PREREGISTRATION.md MISSING — STOPPING'; exit 1; }
ANSWER_KEY_COMMIT=$(grep -oE 'ANSWER_KEY_COMMIT:[[:space:]]*[0-9a-f]{7,40}' "$M" | awk '{print $2}')
ANSWER_KEY_SHA256=$(grep -oE 'ANSWER_KEY_SHA256:[[:space:]]*[0-9a-f]{64}' "$M" | awk '{print $2}')
test -n "$ANSWER_KEY_COMMIT" || { echo 'NO ANSWER_KEY_COMMIT IN MANIFEST — STOPPING'; exit 1; }
test -n "$ANSWER_KEY_SHA256" || { echo 'NO ANSWER_KEY_SHA256 IN MANIFEST — STOPPING'; exit 1; }
git merge-base --is-ancestor "$ANSWER_KEY_COMMIT" HEAD || { echo 'KEY COMMIT NOT AN ANCESTOR OF HEAD — STOPPING'; exit 1; }
test -z "$(git status --porcelain docs/design/b3-ground-truth/ANSWER-KEY-b3.md)" || { echo 'KEY FILE MODIFIED SINCE PRE-REGISTRATION — STOPPING'; exit 1; }
test -z "$(git status --porcelain docs/design/b3-ground-truth/PREREGISTRATION.md)" || { echo 'MANIFEST MODIFIED — PREREGISTRATION.md is IMMUTABLE once runs begin; STOPPING'; exit 1; }
test "$(git show "$ANSWER_KEY_COMMIT":docs/design/b3-ground-truth/ANSWER-KEY-b3.md | shasum -a 256 | awk '{print $1}')" = "$ANSWER_KEY_SHA256" || { echo 'KEY BLOB DIGEST != PREREGISTRATION.md — STOPPING'; exit 1; }
echo "pre-registration gate OK — key $ANSWER_KEY_COMMIT digest verified"
```

## STEP 0 (once, before run 1) — installed-cache CONTENT-assert

A version check is NOT sufficient — the 33-02 wiring is prose-only and does not bump the
version string (a stale cache poisoned 4 of the last 5 milestones). Assert CONTENT:

```bash
set -euo pipefail
test "$(grep -c 'SCOPE_ARGS' ~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/commands/review.md)" -ge 1 || { echo 'STALE CACHE (review.md) — rsync repo->cache AND relaunch before run 1'; exit 1; }
test "$(grep -c 'Codex off via' ~/.claude/plugins/cache/thejuran/vibe-check/2.8.0/commands/deep-review.md)" -ge 1 || { echo 'STALE CACHE (deep-review.md) — rsync+relaunch'; exit 1; }
echo "cache content-assert OK (Phase 35 saw SCOPE_ARGS=13 and Codex-off-via=2)"
```

## STEP 0.5 (once per source repo) — local `.turingmind/` exclude

`/deep-review` writes its state under `<repo>/.turingmind/` — in a repo where that dir is not
git-ignored, the clean-tree guard (STEP 1) and the no-untracked assert (step 8f3's allowed
exception aside) would otherwise trip on the tool's own state dir. This one-time line adds a
LOCAL exclude (`.git/info/exclude` — no working-tree change, nothing committed to the source
repo):

```bash
set -euo pipefail
for r in ~/triggarr ~/seedsyncarr ~/roonseek; do
  grep -qx '.turingmind/' "$r/.git/info/exclude" 2>/dev/null || echo '.turingmind/' >> "$r/.git/info/exclude"
done
echo "local .turingmind/ excludes in place"
```

## The run-ordering rule

**Apply ONCE per diff. The tree stays patched for all 3 runs. Revert ONCE, after run 3.**
State (not the patch) is what isolates runs: your real state file moves to `.b3-backup` once
per diff, each run starts from an asserted-empty state and captures exactly ONE fresh JSON,
and the backup is restored once after run 3.

## D-06 integrity rule (inline)

Missing/corrupt state OR a failed step-8f/8g assert for a run = record that run
**unscoreable** and REPEAT it via the FAILED-RUN RECOVERY block for that diff (it clears the
leftover failed `$STATE_FILE` the exited block left behind, re-proves the live full-worktree
shape, and restarts the same run number). Never guess a run's outcome. Wave 3 hard-stops
before aggregation if any expected run is unscoreable (the only escape is an explicit owner
waiver recorded visibly in the report).

## D-13 method note (inline)

Runs measure **codex=auto** (the shipped default — never force `--codex off`/`on`). Note the
one-line Codex outcome (joined / skipped) per run so Wave 3 can report whether Codex
contributed to any catch.

---

## Diff: `triggarr-secret-in-logs` (should-catch #1, repo `~/triggarr`)

- **What it plants:** reversed d47b4c2 — re-plants the secret/PII-in-logs bug (exc=exc)
- **BASE_SHA:** `f4366a261fcf9bab01b48ad89279aac973a7d9b1`
- **EXPECTED_TREE_DIFF_SHA256:** `f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2` (FULL `git diff`, no pathspec)
- **EXPECTED_TOUCHED_PATHS:** `triggarr/clients/base.py`
- **STATE_FILE:** `~/triggarr/.turingmind/state/triggarr-.json`
- **Patch:** `~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch` · **Runs land in:** `~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-<n>/`

### triggarr-secret-in-logs — fresh per-diff block (paste ONCE, before run 1)

```bash
set -euo pipefail
# STEP 1 — clean-tree check (fail-closed; commit or move aside ANY local work first)
cd ~/triggarr
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
# STEP 2 — record the starting point (persisted into the sentinel below so the
#          after-run-3 revert works even across multi-day sessions)
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
# STEP 3 — PIN the clone to this diff's recorded base_sha (EVERY diff detaches, even ones built at a then-current HEAD)
git switch --detach f4366a261fcf9bab01b48ad89279aac973a7d9b1
test "$(git rev-parse HEAD)" = "f4366a261fcf9bab01b48ad89279aac973a7d9b1" || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE. The tree now carries the planted diff and KEEPS it
#          until after run 3 — do NOT revert between runs.
git apply --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch
git apply ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch
# STEP 5 — resolve the ONE state file
STATE_DIR=~/triggarr/.turingmind/state
mkdir -p "$STATE_DIR"
STATE_FILE=$STATE_DIR/triggarr-.json   # the literal resolved default key on a detached checkout
# STEP 6 — guards, move the owner's real state aside ONCE, write the in-progress
#          sentinel UNCONDITIONALLY (it exists for EVERY in-progress diff, prior state or not)
test ! -e "$STATE_DIR/.b3-inprogress" || { echo 'IN-PROGRESS DIFF DETECTED (.b3-inprogress exists) — do NOT re-run this fresh block; use the RESUME-AT-NEXT-RUN block for this diff'; exit 1; }
test ! -e "$STATE_FILE.b3-backup" || { echo 'STALE .b3-backup WITHOUT a sentinel — earlier session state is inconsistent; STOPPING (surface to the assistant)'; exit 1; }
if test -f "$STATE_FILE"; then mv "$STATE_FILE" "$STATE_FILE.b3-backup"; HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=triggarr-secret-in-logs\nbase_sha=f4366a261fcf9bab01b48ad89279aac973a7d9b1\nhad_prior_state=%s\nstart_branch=%s\nstart_sha=%s\n' "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" > "$STATE_DIR/.b3-inprogress"
# STEP 7 — capture the expected head ONCE for this block (equals the base_sha; HEAD
#          never moves during the 3 runs because the planted diff is uncommitted)
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "ready — triggarr-secret-in-logs pinned at $EXPECTED_HEAD with the patch applied; proceed to Run 1"
```

### triggarr-secret-in-logs — Run 1

**Pre-run 1 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 1 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 1 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-1
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/clients/base.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-1/
git -C ~/turingmind-code-review commit -m "runs(36-02): triggarr-secret-in-logs run 1 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 1 of triggarr-secret-in-logs captured and committed"
```

### triggarr-secret-in-logs — Run 2

**Pre-run 2 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 2 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 2 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-2
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/clients/base.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-2/
git -C ~/turingmind-code-review commit -m "runs(36-02): triggarr-secret-in-logs run 2 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 2 of triggarr-secret-in-logs captured and committed"
```

### triggarr-secret-in-logs — Run 3

**Pre-run 3 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 3 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 3 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-3
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/clients/base.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-3/
git -C ~/turingmind-code-review commit -m "runs(36-02): triggarr-secret-in-logs run 3 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 3 of triggarr-secret-in-logs captured and committed"
```

### triggarr-secret-in-logs — ONCE after run 3 (step 9: revert + restore)

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# ONCE after run 3 — revert the planted diff and restore the clone + your state, in order.
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert here; STOPPING'; exit 1; }
grep -q 'diff_id=triggarr-secret-in-logs' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd triggarr/clients/base.py
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore-or-clear your real state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then mv "$STATE_FILE.b3-backup" "$STATE_FILE"; else test ! -e "$STATE_FILE" || rm "$STATE_FILE"; fi
# remove the sentinel — this diff is complete
rm "$STATE_DIR/.b3-inprogress"
echo "triggarr-secret-in-logs complete — clone restored to $START_BRANCH@$START_SHA"
```

### triggarr-secret-in-logs — RESUME-AT-NEXT-RUN block (multi-day stops)

**ONE selector test — does `$STATE_DIR/.b3-inprogress` exist in this repo?**
**NO** -> use the fresh per-diff block above. **YES** -> this diff is in progress; use THIS block.

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# (1) the sentinel must exist and identify THIS diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — this diff is NOT in progress; use the fresh per-diff block; STOPPING'; exit 1; }
grep -q 'diff_id=triggarr-secret-in-logs' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=f4366a261fcf9bab01b48ad89279aac973a7d9b1' "$STATE_DIR/.b3-inprogress" || { echo 'RESUME FAILED: sentinel is for a different diff/base — STOPPING'; exit 1; }
# (2) re-verify the pin
test "$(git rev-parse HEAD)" = "f4366a261fcf9bab01b48ad89279aac973a7d9b1" || { echo 'RESUME FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
# (3) the planted diff must still be applied
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch || { echo 'RESUME FAILED: patch not applied — STOPPING'; exit 1; }
# (4) LIVE full-worktree proof (prove the CURRENT tree, not just the archives)
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2" || { echo 'RESUME FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/clients/base.py" || { echo 'RESUME FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RESUME FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) captured runs so far — the NEXT run is the first missing of run-1 / run-2 / run-3
ls ~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/ 2>/dev/null || true   # no listing = no runs captured yet -> next is run 1
# (6) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo 'resume OK — continue at the PRE-RUN block of the next missing run number.'
echo 'The patch is ALREADY applied: do NOT re-apply it, do NOT re-run the fresh block.'
```

### triggarr-secret-in-logs — FAILED-RUN RECOVERY block

Use THIS block when a run's step-8f/8g assert FAILED (an `unscoreable` run left `$STATE_FILE`
behind — the block exits BEFORE step 8h's `rm` and step 9's restore, so neither the fresh
block (sentinel guard) nor the RESUME block (step-8a empty-state assert) can restart it).
It archives the bad run dir, removes the failed state file, KEEPS the patch + sentinel, and
restarts the SAME run number.

```bash
set -euo pipefail
N=1   # <-- EDIT THIS ONE DIGIT to the run number that FAILED (1, 2, or 3), then paste the whole block
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# (1) confirm this is a failed-state recovery, not a fresh diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO IN-PROGRESS SENTINEL — use the fresh per-diff block, not recovery; STOPPING'; exit 1; }
grep -q 'diff_id=triggarr-secret-in-logs' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=f4366a261fcf9bab01b48ad89279aac973a7d9b1' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF/BASE — STOPPING'; exit 1; }
# (2) ARCHIVE the bad run dir out of the way (or delete it if empty) so its partial/failed
#     artifacts never get scored
TS=$(date +%s)
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-secret-in-logs/run-$N
if test -d "$RUN_DIR" && test -n "$(ls -A "$RUN_DIR" 2>/dev/null)"; then mv "$RUN_DIR" "$RUN_DIR.failed-$TS"; else rm -rf "$RUN_DIR"; fi
# (3) remove the failed state file so step 8a's empty-start assert can pass on the retry
rm -f "$STATE_FILE"
test ! -e "$STATE_FILE" || { echo 'FAILED STATE FILE STILL PRESENT — STOPPING'; exit 1; }
# (4) KEEP the patch and the .b3-inprogress sentinel intact (do NOT re-apply, do NOT re-run
#     step 6) and re-prove the LIVE full-worktree shape, fail-closed
test "$(git rev-parse HEAD)" = "f4366a261fcf9bab01b48ad89279aac973a7d9b1" || { echo 'RECOVERY FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-secret-in-logs.patch || { echo 'RECOVERY FAILED: patch not applied — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "f0c70a02398b2fd5672d9cc15e337362054de6e0d54e490988f6760980424ff2" || { echo 'RECOVERY FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/clients/base.py" || { echo 'RECOVERY FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RECOVERY FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "recovery OK — RESTART run $N at its PRE-RUN block (step 8a); the patch and sentinel are intact"
```

---

## Diff: `triggarr-autoescape` (should-catch #2, repo `~/triggarr`)

- **What it plants:** reversed e11187e — removes the preconfigured autoescape env (XSS surface); base is PINNED to e11187e (the patch FAILS at current triggarr HEAD — expected)
- **BASE_SHA:** `e11187e190b82f281543039e8c3857c6343c54a2`
- **EXPECTED_TREE_DIFF_SHA256:** `4fdadb707be17419f294383df421d2fcaad4bb9df6e7536a32029420670bb89a` (FULL `git diff`, no pathspec)
- **EXPECTED_TOUCHED_PATHS:** `triggarr/web/routes.py`
- **STATE_FILE:** `~/triggarr/.turingmind/state/triggarr-.json`
- **Patch:** `~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch` · **Runs land in:** `~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-autoescape/run-<n>/`

### triggarr-autoescape — fresh per-diff block (paste ONCE, before run 1)

```bash
set -euo pipefail
# STEP 1 — clean-tree check (fail-closed; commit or move aside ANY local work first)
cd ~/triggarr
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
# STEP 2 — record the starting point (persisted into the sentinel below so the
#          after-run-3 revert works even across multi-day sessions)
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
# STEP 3 — PIN the clone to this diff's recorded base_sha (EVERY diff detaches, even ones built at a then-current HEAD)
git switch --detach e11187e190b82f281543039e8c3857c6343c54a2
test "$(git rev-parse HEAD)" = "e11187e190b82f281543039e8c3857c6343c54a2" || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE. The tree now carries the planted diff and KEEPS it
#          until after run 3 — do NOT revert between runs.
git apply --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch
git apply ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch
# STEP 5 — resolve the ONE state file
STATE_DIR=~/triggarr/.turingmind/state
mkdir -p "$STATE_DIR"
STATE_FILE=$STATE_DIR/triggarr-.json   # the literal resolved default key on a detached checkout
# STEP 6 — guards, move the owner's real state aside ONCE, write the in-progress
#          sentinel UNCONDITIONALLY (it exists for EVERY in-progress diff, prior state or not)
test ! -e "$STATE_DIR/.b3-inprogress" || { echo 'IN-PROGRESS DIFF DETECTED (.b3-inprogress exists) — do NOT re-run this fresh block; use the RESUME-AT-NEXT-RUN block for this diff'; exit 1; }
test ! -e "$STATE_FILE.b3-backup" || { echo 'STALE .b3-backup WITHOUT a sentinel — earlier session state is inconsistent; STOPPING (surface to the assistant)'; exit 1; }
if test -f "$STATE_FILE"; then mv "$STATE_FILE" "$STATE_FILE.b3-backup"; HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=triggarr-autoescape\nbase_sha=e11187e190b82f281543039e8c3857c6343c54a2\nhad_prior_state=%s\nstart_branch=%s\nstart_sha=%s\n' "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" > "$STATE_DIR/.b3-inprogress"
# STEP 7 — capture the expected head ONCE for this block (equals the base_sha; HEAD
#          never moves during the 3 runs because the planted diff is uncommitted)
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "ready — triggarr-autoescape pinned at $EXPECTED_HEAD with the patch applied; proceed to Run 1"
```

### triggarr-autoescape — Run 1

**Pre-run 1 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 1 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 1 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-autoescape/run-1
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "4fdadb707be17419f294383df421d2fcaad4bb9df6e7536a32029420670bb89a" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/routes.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/triggarr-autoescape/run-1/
git -C ~/turingmind-code-review commit -m "runs(36-02): triggarr-autoescape run 1 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 1 of triggarr-autoescape captured and committed"
```

### triggarr-autoescape — Run 2

**Pre-run 2 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 2 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 2 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-autoescape/run-2
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "4fdadb707be17419f294383df421d2fcaad4bb9df6e7536a32029420670bb89a" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/routes.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/triggarr-autoescape/run-2/
git -C ~/turingmind-code-review commit -m "runs(36-02): triggarr-autoescape run 2 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 2 of triggarr-autoescape captured and committed"
```

### triggarr-autoescape — Run 3

**Pre-run 3 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 3 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 3 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-autoescape/run-3
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "4fdadb707be17419f294383df421d2fcaad4bb9df6e7536a32029420670bb89a" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/routes.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/triggarr-autoescape/run-3/
git -C ~/turingmind-code-review commit -m "runs(36-02): triggarr-autoescape run 3 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 3 of triggarr-autoescape captured and committed"
```

### triggarr-autoescape — ONCE after run 3 (step 9: revert + restore)

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# ONCE after run 3 — revert the planted diff and restore the clone + your state, in order.
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert here; STOPPING'; exit 1; }
grep -q 'diff_id=triggarr-autoescape' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd triggarr/web/routes.py
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore-or-clear your real state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then mv "$STATE_FILE.b3-backup" "$STATE_FILE"; else test ! -e "$STATE_FILE" || rm "$STATE_FILE"; fi
# remove the sentinel — this diff is complete
rm "$STATE_DIR/.b3-inprogress"
echo "triggarr-autoescape complete — clone restored to $START_BRANCH@$START_SHA"
```

### triggarr-autoescape — RESUME-AT-NEXT-RUN block (multi-day stops)

**ONE selector test — does `$STATE_DIR/.b3-inprogress` exist in this repo?**
**NO** -> use the fresh per-diff block above. **YES** -> this diff is in progress; use THIS block.

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# (1) the sentinel must exist and identify THIS diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — this diff is NOT in progress; use the fresh per-diff block; STOPPING'; exit 1; }
grep -q 'diff_id=triggarr-autoescape' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=e11187e190b82f281543039e8c3857c6343c54a2' "$STATE_DIR/.b3-inprogress" || { echo 'RESUME FAILED: sentinel is for a different diff/base — STOPPING'; exit 1; }
# (2) re-verify the pin
test "$(git rev-parse HEAD)" = "e11187e190b82f281543039e8c3857c6343c54a2" || { echo 'RESUME FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
# (3) the planted diff must still be applied
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch || { echo 'RESUME FAILED: patch not applied — STOPPING'; exit 1; }
# (4) LIVE full-worktree proof (prove the CURRENT tree, not just the archives)
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "4fdadb707be17419f294383df421d2fcaad4bb9df6e7536a32029420670bb89a" || { echo 'RESUME FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/routes.py" || { echo 'RESUME FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RESUME FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) captured runs so far — the NEXT run is the first missing of run-1 / run-2 / run-3
ls ~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-autoescape/ 2>/dev/null || true   # no listing = no runs captured yet -> next is run 1
# (6) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo 'resume OK — continue at the PRE-RUN block of the next missing run number.'
echo 'The patch is ALREADY applied: do NOT re-apply it, do NOT re-run the fresh block.'
```

### triggarr-autoescape — FAILED-RUN RECOVERY block

Use THIS block when a run's step-8f/8g assert FAILED (an `unscoreable` run left `$STATE_FILE`
behind — the block exits BEFORE step 8h's `rm` and step 9's restore, so neither the fresh
block (sentinel guard) nor the RESUME block (step-8a empty-state assert) can restart it).
It archives the bad run dir, removes the failed state file, KEEPS the patch + sentinel, and
restarts the SAME run number.

```bash
set -euo pipefail
N=1   # <-- EDIT THIS ONE DIGIT to the run number that FAILED (1, 2, or 3), then paste the whole block
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# (1) confirm this is a failed-state recovery, not a fresh diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO IN-PROGRESS SENTINEL — use the fresh per-diff block, not recovery; STOPPING'; exit 1; }
grep -q 'diff_id=triggarr-autoescape' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=e11187e190b82f281543039e8c3857c6343c54a2' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF/BASE — STOPPING'; exit 1; }
# (2) ARCHIVE the bad run dir out of the way (or delete it if empty) so its partial/failed
#     artifacts never get scored
TS=$(date +%s)
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/triggarr-autoescape/run-$N
if test -d "$RUN_DIR" && test -n "$(ls -A "$RUN_DIR" 2>/dev/null)"; then mv "$RUN_DIR" "$RUN_DIR.failed-$TS"; else rm -rf "$RUN_DIR"; fi
# (3) remove the failed state file so step 8a's empty-start assert can pass on the retry
rm -f "$STATE_FILE"
test ! -e "$STATE_FILE" || { echo 'FAILED STATE FILE STILL PRESENT — STOPPING'; exit 1; }
# (4) KEEP the patch and the .b3-inprogress sentinel intact (do NOT re-apply, do NOT re-run
#     step 6) and re-prove the LIVE full-worktree shape, fail-closed
test "$(git rev-parse HEAD)" = "e11187e190b82f281543039e8c3857c6343c54a2" || { echo 'RECOVERY FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/triggarr-autoescape.patch || { echo 'RECOVERY FAILED: patch not applied — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "4fdadb707be17419f294383df421d2fcaad4bb9df6e7536a32029420670bb89a" || { echo 'RECOVERY FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/routes.py" || { echo 'RECOVERY FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RECOVERY FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "recovery OK — RESTART run $N at its PRE-RUN block (step 8a); the patch and sentinel are intact"
```

---

## Diff: `third-organic-should-catch` (should-catch #3, repo `~/seedsyncarr`)

- **What it plants:** reversed seedsyncarr 879266c — removes the Math.min(100, ...) clamp (>100% progress bug)
- **BASE_SHA:** `3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e`
- **EXPECTED_TREE_DIFF_SHA256:** `d99180365a66f9efef72f7e01afb3c23ad707c6e6f1917d378df75e5b1ad7790` (FULL `git diff`, no pathspec)
- **EXPECTED_TOUCHED_PATHS:** `src/angular/src/app/services/files/view-file.service.ts`
- **STATE_FILE:** `~/seedsyncarr/.turingmind/state/seedsyncarr-.json`
- **Patch:** `~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch` · **Runs land in:** `~/turingmind-code-review/docs/design/b3-ground-truth/runs/third-organic-should-catch/run-<n>/`

### third-organic-should-catch — fresh per-diff block (paste ONCE, before run 1)

```bash
set -euo pipefail
# STEP 1 — clean-tree check (fail-closed; commit or move aside ANY local work first)
cd ~/seedsyncarr
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
# STEP 2 — record the starting point (persisted into the sentinel below so the
#          after-run-3 revert works even across multi-day sessions)
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
# STEP 3 — PIN the clone to this diff's recorded base_sha (EVERY diff detaches, even ones built at a then-current HEAD)
git switch --detach 3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e
test "$(git rev-parse HEAD)" = "3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e" || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE. The tree now carries the planted diff and KEEPS it
#          until after run 3 — do NOT revert between runs.
git apply --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch
git apply ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch
# STEP 5 — resolve the ONE state file
STATE_DIR=~/seedsyncarr/.turingmind/state
mkdir -p "$STATE_DIR"
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # the literal resolved default key on a detached checkout
# STEP 6 — guards, move the owner's real state aside ONCE, write the in-progress
#          sentinel UNCONDITIONALLY (it exists for EVERY in-progress diff, prior state or not)
test ! -e "$STATE_DIR/.b3-inprogress" || { echo 'IN-PROGRESS DIFF DETECTED (.b3-inprogress exists) — do NOT re-run this fresh block; use the RESUME-AT-NEXT-RUN block for this diff'; exit 1; }
test ! -e "$STATE_FILE.b3-backup" || { echo 'STALE .b3-backup WITHOUT a sentinel — earlier session state is inconsistent; STOPPING (surface to the assistant)'; exit 1; }
if test -f "$STATE_FILE"; then mv "$STATE_FILE" "$STATE_FILE.b3-backup"; HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=third-organic-should-catch\nbase_sha=3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e\nhad_prior_state=%s\nstart_branch=%s\nstart_sha=%s\n' "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" > "$STATE_DIR/.b3-inprogress"
# STEP 7 — capture the expected head ONCE for this block (equals the base_sha; HEAD
#          never moves during the 3 runs because the planted diff is uncommitted)
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "ready — third-organic-should-catch pinned at $EXPECTED_HEAD with the patch applied; proceed to Run 1"
```

### third-organic-should-catch — Run 1

**Pre-run 1 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 1 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/seedsyncarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 1 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/third-organic-should-catch/run-1
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "d99180365a66f9efef72f7e01afb3c23ad707c6e6f1917d378df75e5b1ad7790" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/files/view-file.service.ts" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/third-organic-should-catch/run-1/
git -C ~/turingmind-code-review commit -m "runs(36-02): third-organic-should-catch run 1 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 1 of third-organic-should-catch captured and committed"
```

### third-organic-should-catch — Run 2

**Pre-run 2 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 2 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/seedsyncarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 2 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/third-organic-should-catch/run-2
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "d99180365a66f9efef72f7e01afb3c23ad707c6e6f1917d378df75e5b1ad7790" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/files/view-file.service.ts" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/third-organic-should-catch/run-2/
git -C ~/turingmind-code-review commit -m "runs(36-02): third-organic-should-catch run 2 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 2 of third-organic-should-catch captured and committed"
```

### third-organic-should-catch — Run 3

**Pre-run 3 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 3 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/seedsyncarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 3 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/third-organic-should-catch/run-3
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "d99180365a66f9efef72f7e01afb3c23ad707c6e6f1917d378df75e5b1ad7790" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/files/view-file.service.ts" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/third-organic-should-catch/run-3/
git -C ~/turingmind-code-review commit -m "runs(36-02): third-organic-should-catch run 3 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 3 of third-organic-should-catch captured and committed"
```

### third-organic-should-catch — ONCE after run 3 (step 9: revert + restore)

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# ONCE after run 3 — revert the planted diff and restore the clone + your state, in order.
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert here; STOPPING'; exit 1; }
grep -q 'diff_id=third-organic-should-catch' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd src/angular/src/app/services/files/view-file.service.ts
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore-or-clear your real state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then mv "$STATE_FILE.b3-backup" "$STATE_FILE"; else test ! -e "$STATE_FILE" || rm "$STATE_FILE"; fi
# remove the sentinel — this diff is complete
rm "$STATE_DIR/.b3-inprogress"
echo "third-organic-should-catch complete — clone restored to $START_BRANCH@$START_SHA"
```

### third-organic-should-catch — RESUME-AT-NEXT-RUN block (multi-day stops)

**ONE selector test — does `$STATE_DIR/.b3-inprogress` exist in this repo?**
**NO** -> use the fresh per-diff block above. **YES** -> this diff is in progress; use THIS block.

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# (1) the sentinel must exist and identify THIS diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — this diff is NOT in progress; use the fresh per-diff block; STOPPING'; exit 1; }
grep -q 'diff_id=third-organic-should-catch' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e' "$STATE_DIR/.b3-inprogress" || { echo 'RESUME FAILED: sentinel is for a different diff/base — STOPPING'; exit 1; }
# (2) re-verify the pin
test "$(git rev-parse HEAD)" = "3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e" || { echo 'RESUME FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
# (3) the planted diff must still be applied
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch || { echo 'RESUME FAILED: patch not applied — STOPPING'; exit 1; }
# (4) LIVE full-worktree proof (prove the CURRENT tree, not just the archives)
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "d99180365a66f9efef72f7e01afb3c23ad707c6e6f1917d378df75e5b1ad7790" || { echo 'RESUME FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/files/view-file.service.ts" || { echo 'RESUME FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RESUME FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) captured runs so far — the NEXT run is the first missing of run-1 / run-2 / run-3
ls ~/turingmind-code-review/docs/design/b3-ground-truth/runs/third-organic-should-catch/ 2>/dev/null || true   # no listing = no runs captured yet -> next is run 1
# (6) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo 'resume OK — continue at the PRE-RUN block of the next missing run number.'
echo 'The patch is ALREADY applied: do NOT re-apply it, do NOT re-run the fresh block.'
```

### third-organic-should-catch — FAILED-RUN RECOVERY block

Use THIS block when a run's step-8f/8g assert FAILED (an `unscoreable` run left `$STATE_FILE`
behind — the block exits BEFORE step 8h's `rm` and step 9's restore, so neither the fresh
block (sentinel guard) nor the RESUME block (step-8a empty-state assert) can restart it).
It archives the bad run dir, removes the failed state file, KEEPS the patch + sentinel, and
restarts the SAME run number.

```bash
set -euo pipefail
N=1   # <-- EDIT THIS ONE DIGIT to the run number that FAILED (1, 2, or 3), then paste the whole block
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# (1) confirm this is a failed-state recovery, not a fresh diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO IN-PROGRESS SENTINEL — use the fresh per-diff block, not recovery; STOPPING'; exit 1; }
grep -q 'diff_id=third-organic-should-catch' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF/BASE — STOPPING'; exit 1; }
# (2) ARCHIVE the bad run dir out of the way (or delete it if empty) so its partial/failed
#     artifacts never get scored
TS=$(date +%s)
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/third-organic-should-catch/run-$N
if test -d "$RUN_DIR" && test -n "$(ls -A "$RUN_DIR" 2>/dev/null)"; then mv "$RUN_DIR" "$RUN_DIR.failed-$TS"; else rm -rf "$RUN_DIR"; fi
# (3) remove the failed state file so step 8a's empty-start assert can pass on the retry
rm -f "$STATE_FILE"
test ! -e "$STATE_FILE" || { echo 'FAILED STATE FILE STILL PRESENT — STOPPING'; exit 1; }
# (4) KEEP the patch and the .b3-inprogress sentinel intact (do NOT re-apply, do NOT re-run
#     step 6) and re-prove the LIVE full-worktree shape, fail-closed
test "$(git rev-parse HEAD)" = "3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e" || { echo 'RECOVERY FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/third-organic-should-catch.patch || { echo 'RECOVERY FAILED: patch not applied — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "d99180365a66f9efef72f7e01afb3c23ad707c6e6f1917d378df75e5b1ad7790" || { echo 'RECOVERY FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/files/view-file.service.ts" || { echo 'RECOVERY FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RECOVERY FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "recovery OK — RESTART run $N at its PRE-RUN block (step 8a); the patch and sentinel are intact"
```

---

## Diff: `should-quiet-1` (should-quiet #1, repo `~/triggarr`)

- **What it plants:** forward 1a8c9f9 on its parent — clean SSRF-hardening feature (any critical/warning = FP)
- **BASE_SHA:** `98eb4196e2c060b38775ab40d6d23e2dc2bee024`
- **EXPECTED_TREE_DIFF_SHA256:** `a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a` (FULL `git diff`, no pathspec)
- **EXPECTED_TOUCHED_PATHS:** `triggarr/web/validation.py`
- **STATE_FILE:** `~/triggarr/.turingmind/state/triggarr-.json`
- **Patch:** `~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch` · **Runs land in:** `~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-1/run-<n>/`

### should-quiet-1 — fresh per-diff block (paste ONCE, before run 1)

```bash
set -euo pipefail
# STEP 1 — clean-tree check (fail-closed; commit or move aside ANY local work first)
cd ~/triggarr
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
# STEP 2 — record the starting point (persisted into the sentinel below so the
#          after-run-3 revert works even across multi-day sessions)
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
# STEP 3 — PIN the clone to this diff's recorded base_sha (EVERY diff detaches, even ones built at a then-current HEAD)
git switch --detach 98eb4196e2c060b38775ab40d6d23e2dc2bee024
test "$(git rev-parse HEAD)" = "98eb4196e2c060b38775ab40d6d23e2dc2bee024" || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE. The tree now carries the planted diff and KEEPS it
#          until after run 3 — do NOT revert between runs.
git apply --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch
git apply ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch
# STEP 5 — resolve the ONE state file
STATE_DIR=~/triggarr/.turingmind/state
mkdir -p "$STATE_DIR"
STATE_FILE=$STATE_DIR/triggarr-.json   # the literal resolved default key on a detached checkout
# STEP 6 — guards, move the owner's real state aside ONCE, write the in-progress
#          sentinel UNCONDITIONALLY (it exists for EVERY in-progress diff, prior state or not)
test ! -e "$STATE_DIR/.b3-inprogress" || { echo 'IN-PROGRESS DIFF DETECTED (.b3-inprogress exists) — do NOT re-run this fresh block; use the RESUME-AT-NEXT-RUN block for this diff'; exit 1; }
test ! -e "$STATE_FILE.b3-backup" || { echo 'STALE .b3-backup WITHOUT a sentinel — earlier session state is inconsistent; STOPPING (surface to the assistant)'; exit 1; }
if test -f "$STATE_FILE"; then mv "$STATE_FILE" "$STATE_FILE.b3-backup"; HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=should-quiet-1\nbase_sha=98eb4196e2c060b38775ab40d6d23e2dc2bee024\nhad_prior_state=%s\nstart_branch=%s\nstart_sha=%s\n' "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" > "$STATE_DIR/.b3-inprogress"
# STEP 7 — capture the expected head ONCE for this block (equals the base_sha; HEAD
#          never moves during the 3 runs because the planted diff is uncommitted)
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "ready — should-quiet-1 pinned at $EXPECTED_HEAD with the patch applied; proceed to Run 1"
```

### should-quiet-1 — Run 1

**Pre-run 1 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 1 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 1 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-1/run-1
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/validation.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-1/run-1/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-1 run 1 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 1 of should-quiet-1 captured and committed"
```

### should-quiet-1 — Run 2

**Pre-run 2 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 2 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 2 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-1/run-2
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/validation.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-1/run-2/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-1 run 2 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 2 of should-quiet-1 captured and committed"
```

### should-quiet-1 — Run 3

**Pre-run 3 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 3 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/triggarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 3 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-1/run-3
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/validation.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-1/run-3/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-1 run 3 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 3 of should-quiet-1 captured and committed"
```

### should-quiet-1 — ONCE after run 3 (step 9: revert + restore)

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# ONCE after run 3 — revert the planted diff and restore the clone + your state, in order.
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert here; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-1' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd triggarr/web/validation.py
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore-or-clear your real state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then mv "$STATE_FILE.b3-backup" "$STATE_FILE"; else test ! -e "$STATE_FILE" || rm "$STATE_FILE"; fi
# remove the sentinel — this diff is complete
rm "$STATE_DIR/.b3-inprogress"
echo "should-quiet-1 complete — clone restored to $START_BRANCH@$START_SHA"
```

### should-quiet-1 — RESUME-AT-NEXT-RUN block (multi-day stops)

**ONE selector test — does `$STATE_DIR/.b3-inprogress` exist in this repo?**
**NO** -> use the fresh per-diff block above. **YES** -> this diff is in progress; use THIS block.

```bash
set -euo pipefail
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# (1) the sentinel must exist and identify THIS diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — this diff is NOT in progress; use the fresh per-diff block; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-1' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=98eb4196e2c060b38775ab40d6d23e2dc2bee024' "$STATE_DIR/.b3-inprogress" || { echo 'RESUME FAILED: sentinel is for a different diff/base — STOPPING'; exit 1; }
# (2) re-verify the pin
test "$(git rev-parse HEAD)" = "98eb4196e2c060b38775ab40d6d23e2dc2bee024" || { echo 'RESUME FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
# (3) the planted diff must still be applied
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch || { echo 'RESUME FAILED: patch not applied — STOPPING'; exit 1; }
# (4) LIVE full-worktree proof (prove the CURRENT tree, not just the archives)
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a" || { echo 'RESUME FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/validation.py" || { echo 'RESUME FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RESUME FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) captured runs so far — the NEXT run is the first missing of run-1 / run-2 / run-3
ls ~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-1/ 2>/dev/null || true   # no listing = no runs captured yet -> next is run 1
# (6) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo 'resume OK — continue at the PRE-RUN block of the next missing run number.'
echo 'The patch is ALREADY applied: do NOT re-apply it, do NOT re-run the fresh block.'
```

### should-quiet-1 — FAILED-RUN RECOVERY block

Use THIS block when a run's step-8f/8g assert FAILED (an `unscoreable` run left `$STATE_FILE`
behind — the block exits BEFORE step 8h's `rm` and step 9's restore, so neither the fresh
block (sentinel guard) nor the RESUME block (step-8a empty-state assert) can restart it).
It archives the bad run dir, removes the failed state file, KEEPS the patch + sentinel, and
restarts the SAME run number.

```bash
set -euo pipefail
N=1   # <-- EDIT THIS ONE DIGIT to the run number that FAILED (1, 2, or 3), then paste the whole block
cd ~/triggarr
STATE_DIR=~/triggarr/.turingmind/state
STATE_FILE=$STATE_DIR/triggarr-.json   # detached checkout -> branch slug is empty -> the default key is triggarr-.json
# (1) confirm this is a failed-state recovery, not a fresh diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO IN-PROGRESS SENTINEL — use the fresh per-diff block, not recovery; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-1' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=98eb4196e2c060b38775ab40d6d23e2dc2bee024' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF/BASE — STOPPING'; exit 1; }
# (2) ARCHIVE the bad run dir out of the way (or delete it if empty) so its partial/failed
#     artifacts never get scored
TS=$(date +%s)
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-1/run-$N
if test -d "$RUN_DIR" && test -n "$(ls -A "$RUN_DIR" 2>/dev/null)"; then mv "$RUN_DIR" "$RUN_DIR.failed-$TS"; else rm -rf "$RUN_DIR"; fi
# (3) remove the failed state file so step 8a's empty-start assert can pass on the retry
rm -f "$STATE_FILE"
test ! -e "$STATE_FILE" || { echo 'FAILED STATE FILE STILL PRESENT — STOPPING'; exit 1; }
# (4) KEEP the patch and the .b3-inprogress sentinel intact (do NOT re-apply, do NOT re-run
#     step 6) and re-prove the LIVE full-worktree shape, fail-closed
test "$(git rev-parse HEAD)" = "98eb4196e2c060b38775ab40d6d23e2dc2bee024" || { echo 'RECOVERY FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-1.patch || { echo 'RECOVERY FAILED: patch not applied — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a" || { echo 'RECOVERY FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "triggarr/web/validation.py" || { echo 'RECOVERY FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RECOVERY FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "recovery OK — RESTART run $N at its PRE-RUN block (step 8a); the patch and sentinel are intact"
```

---

## Diff: `should-quiet-2` (should-quiet #2, repo `~/seedsyncarr`)

- **What it plants:** forward 3c27e17 on its parent — clean optional-body feature (any critical/warning = FP)
- **BASE_SHA:** `84aff278f2b735dffef0e91d58bb597b1986caf2`
- **EXPECTED_TREE_DIFF_SHA256:** `3cb198dc37a4780e61eef0fd4d6b2817733b8796aa80769feb0d08f24d731f0d` (FULL `git diff`, no pathspec)
- **EXPECTED_TOUCHED_PATHS:** `src/angular/src/app/services/utils/rest.service.ts`
- **STATE_FILE:** `~/seedsyncarr/.turingmind/state/seedsyncarr-.json`
- **Patch:** `~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch` · **Runs land in:** `~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-2/run-<n>/`

### should-quiet-2 — fresh per-diff block (paste ONCE, before run 1)

```bash
set -euo pipefail
# STEP 1 — clean-tree check (fail-closed; commit or move aside ANY local work first)
cd ~/seedsyncarr
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
# STEP 2 — record the starting point (persisted into the sentinel below so the
#          after-run-3 revert works even across multi-day sessions)
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
# STEP 3 — PIN the clone to this diff's recorded base_sha (EVERY diff detaches, even ones built at a then-current HEAD)
git switch --detach 84aff278f2b735dffef0e91d58bb597b1986caf2
test "$(git rev-parse HEAD)" = "84aff278f2b735dffef0e91d58bb597b1986caf2" || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE. The tree now carries the planted diff and KEEPS it
#          until after run 3 — do NOT revert between runs.
git apply --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch
git apply ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch
# STEP 5 — resolve the ONE state file
STATE_DIR=~/seedsyncarr/.turingmind/state
mkdir -p "$STATE_DIR"
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # the literal resolved default key on a detached checkout
# STEP 6 — guards, move the owner's real state aside ONCE, write the in-progress
#          sentinel UNCONDITIONALLY (it exists for EVERY in-progress diff, prior state or not)
test ! -e "$STATE_DIR/.b3-inprogress" || { echo 'IN-PROGRESS DIFF DETECTED (.b3-inprogress exists) — do NOT re-run this fresh block; use the RESUME-AT-NEXT-RUN block for this diff'; exit 1; }
test ! -e "$STATE_FILE.b3-backup" || { echo 'STALE .b3-backup WITHOUT a sentinel — earlier session state is inconsistent; STOPPING (surface to the assistant)'; exit 1; }
if test -f "$STATE_FILE"; then mv "$STATE_FILE" "$STATE_FILE.b3-backup"; HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=should-quiet-2\nbase_sha=84aff278f2b735dffef0e91d58bb597b1986caf2\nhad_prior_state=%s\nstart_branch=%s\nstart_sha=%s\n' "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" > "$STATE_DIR/.b3-inprogress"
# STEP 7 — capture the expected head ONCE for this block (equals the base_sha; HEAD
#          never moves during the 3 runs because the planted diff is uncommitted)
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "ready — should-quiet-2 pinned at $EXPECTED_HEAD with the patch applied; proceed to Run 1"
```

### should-quiet-2 — Run 1

**Pre-run 1 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 1 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/seedsyncarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 1 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-2/run-1
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "3cb198dc37a4780e61eef0fd4d6b2817733b8796aa80769feb0d08f24d731f0d" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/utils/rest.service.ts" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-2/run-1/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-2 run 1 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 1 of should-quiet-2 captured and committed"
```

### should-quiet-2 — Run 2

**Pre-run 2 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 2 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/seedsyncarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 2 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-2/run-2
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "3cb198dc37a4780e61eef0fd4d6b2817733b8796aa80769feb0d08f24d731f0d" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/utils/rest.service.ts" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-2/run-2/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-2 run 2 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 2 of should-quiet-2 captured and committed"
```

### should-quiet-2 — Run 3

**Pre-run 3 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 3 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/seedsyncarr`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 3 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-2/run-3
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "3cb198dc37a4780e61eef0fd4d6b2817733b8796aa80769feb0d08f24d731f0d" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/utils/rest.service.ts" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-2/run-3/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-2 run 3 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 3 of should-quiet-2 captured and committed"
```

### should-quiet-2 — ONCE after run 3 (step 9: revert + restore)

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# ONCE after run 3 — revert the planted diff and restore the clone + your state, in order.
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert here; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-2' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd src/angular/src/app/services/utils/rest.service.ts
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore-or-clear your real state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then mv "$STATE_FILE.b3-backup" "$STATE_FILE"; else test ! -e "$STATE_FILE" || rm "$STATE_FILE"; fi
# remove the sentinel — this diff is complete
rm "$STATE_DIR/.b3-inprogress"
echo "should-quiet-2 complete — clone restored to $START_BRANCH@$START_SHA"
```

### should-quiet-2 — RESUME-AT-NEXT-RUN block (multi-day stops)

**ONE selector test — does `$STATE_DIR/.b3-inprogress` exist in this repo?**
**NO** -> use the fresh per-diff block above. **YES** -> this diff is in progress; use THIS block.

```bash
set -euo pipefail
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# (1) the sentinel must exist and identify THIS diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — this diff is NOT in progress; use the fresh per-diff block; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-2' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=84aff278f2b735dffef0e91d58bb597b1986caf2' "$STATE_DIR/.b3-inprogress" || { echo 'RESUME FAILED: sentinel is for a different diff/base — STOPPING'; exit 1; }
# (2) re-verify the pin
test "$(git rev-parse HEAD)" = "84aff278f2b735dffef0e91d58bb597b1986caf2" || { echo 'RESUME FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
# (3) the planted diff must still be applied
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch || { echo 'RESUME FAILED: patch not applied — STOPPING'; exit 1; }
# (4) LIVE full-worktree proof (prove the CURRENT tree, not just the archives)
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "3cb198dc37a4780e61eef0fd4d6b2817733b8796aa80769feb0d08f24d731f0d" || { echo 'RESUME FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/utils/rest.service.ts" || { echo 'RESUME FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RESUME FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) captured runs so far — the NEXT run is the first missing of run-1 / run-2 / run-3
ls ~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-2/ 2>/dev/null || true   # no listing = no runs captured yet -> next is run 1
# (6) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo 'resume OK — continue at the PRE-RUN block of the next missing run number.'
echo 'The patch is ALREADY applied: do NOT re-apply it, do NOT re-run the fresh block.'
```

### should-quiet-2 — FAILED-RUN RECOVERY block

Use THIS block when a run's step-8f/8g assert FAILED (an `unscoreable` run left `$STATE_FILE`
behind — the block exits BEFORE step 8h's `rm` and step 9's restore, so neither the fresh
block (sentinel guard) nor the RESUME block (step-8a empty-state assert) can restart it).
It archives the bad run dir, removes the failed state file, KEEPS the patch + sentinel, and
restarts the SAME run number.

```bash
set -euo pipefail
N=1   # <-- EDIT THIS ONE DIGIT to the run number that FAILED (1, 2, or 3), then paste the whole block
cd ~/seedsyncarr
STATE_DIR=~/seedsyncarr/.turingmind/state
STATE_FILE=$STATE_DIR/seedsyncarr-.json   # detached checkout -> branch slug is empty -> the default key is seedsyncarr-.json
# (1) confirm this is a failed-state recovery, not a fresh diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO IN-PROGRESS SENTINEL — use the fresh per-diff block, not recovery; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-2' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=84aff278f2b735dffef0e91d58bb597b1986caf2' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF/BASE — STOPPING'; exit 1; }
# (2) ARCHIVE the bad run dir out of the way (or delete it if empty) so its partial/failed
#     artifacts never get scored
TS=$(date +%s)
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-2/run-$N
if test -d "$RUN_DIR" && test -n "$(ls -A "$RUN_DIR" 2>/dev/null)"; then mv "$RUN_DIR" "$RUN_DIR.failed-$TS"; else rm -rf "$RUN_DIR"; fi
# (3) remove the failed state file so step 8a's empty-start assert can pass on the retry
rm -f "$STATE_FILE"
test ! -e "$STATE_FILE" || { echo 'FAILED STATE FILE STILL PRESENT — STOPPING'; exit 1; }
# (4) KEEP the patch and the .b3-inprogress sentinel intact (do NOT re-apply, do NOT re-run
#     step 6) and re-prove the LIVE full-worktree shape, fail-closed
test "$(git rev-parse HEAD)" = "84aff278f2b735dffef0e91d58bb597b1986caf2" || { echo 'RECOVERY FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-2.patch || { echo 'RECOVERY FAILED: patch not applied — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "3cb198dc37a4780e61eef0fd4d6b2817733b8796aa80769feb0d08f24d731f0d" || { echo 'RECOVERY FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/angular/src/app/services/utils/rest.service.ts" || { echo 'RECOVERY FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RECOVERY FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "recovery OK — RESTART run $N at its PRE-RUN block (step 8a); the patch and sentinel are intact"
```

---

## Diff: `should-quiet-3` (should-quiet #3, repo `~/roonseek`)

- **What it plants:** forward 2a6bbd9 on its parent — clean cancel-boundary feature (any critical/warning = FP)
- **BASE_SHA:** `10276919fc2f1123cf0d8da7c0d43488087f1bc7`
- **EXPECTED_TREE_DIFF_SHA256:** `66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69` (FULL `git diff`, no pathspec)
- **EXPECTED_TOUCHED_PATHS:** `src/roonseek/transfer.py`
- **STATE_FILE:** `~/roonseek/.turingmind/state/roonseek-.json`
- **Patch:** `~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch` · **Runs land in:** `~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-3/run-<n>/`

> **PREP NOTE (roonseek only):** at kit-build time `~/roonseek` carried uncommitted local
> state (modified `.planning/config.json`; untracked `.orchestrator.json`,
> `.planning/phases/30-library-quality-visibility/30-PATTERNS.md`). STEP 1 will STOP until
> you commit or move that work aside (your call — it is YOUR working state, the kit never
> touches it). The one-time STEP 0.5 exclude below already handles `.turingmind/`.

### should-quiet-3 — fresh per-diff block (paste ONCE, before run 1)

```bash
set -euo pipefail
# STEP 1 — clean-tree check (fail-closed; commit or move aside ANY local work first)
cd ~/roonseek
test -z "$(git status --porcelain)" || { echo 'CLONE NOT CLEAN — STOPPING'; exit 1; }
# STEP 2 — record the starting point (persisted into the sentinel below so the
#          after-run-3 revert works even across multi-day sessions)
START_BRANCH=$(git branch --show-current)
START_SHA=$(git rev-parse HEAD)
# STEP 3 — PIN the clone to this diff's recorded base_sha (EVERY diff detaches, even ones built at a then-current HEAD)
git switch --detach 10276919fc2f1123cf0d8da7c0d43488087f1bc7
test "$(git rev-parse HEAD)" = "10276919fc2f1123cf0d8da7c0d43488087f1bc7" || { echo 'WRONG BASE — STOPPING'; exit 1; }
# STEP 4 — apply the patch ONCE. The tree now carries the planted diff and KEEPS it
#          until after run 3 — do NOT revert between runs.
git apply --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch
git apply ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch
# STEP 5 — resolve the ONE state file
STATE_DIR=~/roonseek/.turingmind/state
mkdir -p "$STATE_DIR"
STATE_FILE=$STATE_DIR/roonseek-.json   # the literal resolved default key on a detached checkout
# STEP 6 — guards, move the owner's real state aside ONCE, write the in-progress
#          sentinel UNCONDITIONALLY (it exists for EVERY in-progress diff, prior state or not)
test ! -e "$STATE_DIR/.b3-inprogress" || { echo 'IN-PROGRESS DIFF DETECTED (.b3-inprogress exists) — do NOT re-run this fresh block; use the RESUME-AT-NEXT-RUN block for this diff'; exit 1; }
test ! -e "$STATE_FILE.b3-backup" || { echo 'STALE .b3-backup WITHOUT a sentinel — earlier session state is inconsistent; STOPPING (surface to the assistant)'; exit 1; }
if test -f "$STATE_FILE"; then mv "$STATE_FILE" "$STATE_FILE.b3-backup"; HAD_PRIOR=true; else HAD_PRIOR=false; fi
printf 'diff_id=should-quiet-3\nbase_sha=10276919fc2f1123cf0d8da7c0d43488087f1bc7\nhad_prior_state=%s\nstart_branch=%s\nstart_sha=%s\n' "$HAD_PRIOR" "$START_BRANCH" "$START_SHA" > "$STATE_DIR/.b3-inprogress"
# STEP 7 — capture the expected head ONCE for this block (equals the base_sha; HEAD
#          never moves during the 3 runs because the planted diff is uncommitted)
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "ready — should-quiet-3 pinned at $EXPECTED_HEAD with the patch applied; proceed to Run 1"
```

### should-quiet-3 — Run 1

**Pre-run 1 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 1 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/roonseek`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 1 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-3/run-1
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/roonseek/transfer.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-3/run-1/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-3 run 1 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 1 of should-quiet-3 captured and committed"
```

### should-quiet-3 — Run 2

**Pre-run 2 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 2 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/roonseek`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 2 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-3/run-2
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/roonseek/transfer.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-3/run-2/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-3 run 2 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 2 of should-quiet-3 captured and committed"
```

### should-quiet-3 — Run 3

**Pre-run 3 (steps 8a-8b):**

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
# STEP 8a — assert an empty start (run 1: just moved aside; runs 2-3: removed at step 8h)
test ! -e "$STATE_FILE" || { echo 'STATE NOT EMPTY — STOPPING'; exit 1; }
# STEP 8b — PROVE THE PATCH IS CURRENTLY APPLIED, immediately before /deep-review
#           (apply --reverse --check succeeds ONLY if the patch's post-image IS present
#            in the tree — i.e. the planted diff is really there; it makes NO change)
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch || { echo 'PATCH IS NOT APPLIED — the tree is unpatched or drifted; STOPPING'; exit 1; }
echo "run 3 pre-flight OK — now run /vibe-check:deep-review in this repo"
```

**Step 8c — the ONE user action:** run `/vibe-check:deep-review` in `~/roonseek`
(default diff scope; the SHIPPED default codex=auto per D-13 — do NOT pass `--codex off`
or `--codex on`). Jot down the one-line Codex outcome (joined / skipped-with-reason) for
this run — Wave 3 reports whether Codex contributed.

**Step 8d — fix loop (inline restatement of the header rule):** if `/deep-review` enters
its interactive Phase 5 fix loop, DECLINE/SKIP all fixes and EXIT WITHOUT applying —
at Step A pick **"Skip fixes this pass"** (option 4), at Step C pick **"Abandon for
now"** (option 3). Do NOT pick "Rerun review on the new diff" (a re-run appends a
second pass and breaks the len(passes)==1 sample), do NOT pick "Close out and document"
(that is `--finalize`), do NOT let the fix agent commit into the source repo. This is a
measurement run.

**Post-run 3 (steps 8e-8i):**

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
EXPECTED_HEAD=$(git rev-parse HEAD)   # equals the pinned base_sha; re-derived so this block is paste-independent
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-3/run-3
# STEP 8e — capture EXACTLY ONE fresh JSON (the ONE resolved file, NEVER the glob —
#           the state dir holds ~19 unrelated old JSONs that must not be dragged in)
mkdir -p "$RUN_DIR"
cp "$STATE_FILE" "$RUN_DIR/state.json"
# STEP 8f1 — FULL-WORKTREE PROOF: archive the FULL tracked diff (git diff, NO pathspec)
#            and assert it equals the kit-build EXPECTED_TREE_DIFF_SHA256 — proves the
#            reviewed tree carries EXACTLY the planted diff and nothing else (no fix-agent
#            side effect, no generated file, no concurrent edit); Wave 3 re-checks this
#            sha is identical across all 3 runs
git diff > "$RUN_DIR/tree.diff"
shasum -a 256 "$RUN_DIR/tree.diff" | awk '{print $1}' > "$RUN_DIR/tree.diff.sha256"
test "$(cat "$RUN_DIR/tree.diff.sha256")" = "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69" || { echo 'FULL WORKTREE DIFF != EXPECTED PLANTED DIFF — an out-of-path change leaked in or the patch drifted; STOPPING'; exit 1; }
# STEP 8f2 — assert the touched-path SET equals EXPECTED_TOUCHED_PATHS (kit-build value)
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/roonseek/transfer.py" || { echo 'TOUCHED-PATH SET MISMATCH — STOPPING'; exit 1; }
# STEP 8f3 — assert no stray untracked files (the state dir is the ONLY allowed untracked path)
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'UNTRACKED FILES OUTSIDE THE STATE DIR — a side effect leaked; STOPPING'; exit 1; }
# STEP 8g — REAL freshness assert (state path + EXPECTED_HEAD passed as sys.argv; string
#           equality — fails loudly on a missing file, accumulated passes, or wrong head)
python3 -c 'import json,os,sys; p=sys.argv[1]; e=sys.argv[2]; assert os.path.isfile(p), "MISSING "+p; s=json.load(open(p)); n=len(s["passes"]); assert n==1, "NOT ISOLATED: passes=%d" % n; h=s["passes"][-1]["head_sha"]; assert h==e, "HEAD MISMATCH: state=%s expected=%s" % (h,e); print("OK fresh isolated run at", h)' "$RUN_DIR/state.json" "$EXPECTED_HEAD" || { echo 'FRESHNESS ASSERT FAILED — mark this run unscoreable and use the FAILED-RUN RECOVERY block below (D-06)'; exit 1; }
# STEP 8h — clear for the next run (this pass is captured+asserted under the run dir;
#           your real state is safe in .b3-backup). Do NOT touch the applied patch.
rm "$STATE_FILE"
# STEP 8i — COMMIT THIS RUN'S ARTIFACTS at the run boundary (one commit per RUN, so
#           stopping after ANY run is safe)
git -C ~/turingmind-code-review add docs/design/b3-ground-truth/runs/should-quiet-3/run-3/
git -C ~/turingmind-code-review commit -m "runs(36-02): should-quiet-3 run 3 captured"
test -z "$(git -C ~/turingmind-code-review status --porcelain docs/design/b3-ground-truth/runs/)" || { echo 'RUN ARTIFACTS NOT FULLY COMMITTED — STOPPING'; exit 1; }
echo "run 3 of should-quiet-3 captured and committed"
```

### should-quiet-3 — ONCE after run 3 (step 9: revert + restore)

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
# ONCE after run 3 — revert the planted diff and restore the clone + your state, in order.
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — nothing to revert here; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-3' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF — STOPPING'; exit 1; }
START_BRANCH=$(grep '^start_branch=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
START_SHA=$(grep '^start_sha=' "$STATE_DIR/.b3-inprogress" | cut -d= -f2)
test -n "$START_BRANCH" || { echo 'SENTINEL MISSING start_branch — STOPPING'; exit 1; }
test -n "$START_SHA" || { echo 'SENTINEL MISSING start_sha — STOPPING'; exit 1; }
# scoped revert of the planted diff
git checkout -- .
git clean -fd src/roonseek/transfer.py
git switch "$START_BRANCH"
test "$(git rev-parse HEAD)" = "$START_SHA" || { echo 'BRANCH NOT RESTORED — STOPPING'; exit 1; }
# restore-or-clear your real state per the sentinel's had_prior_state
if grep -q 'had_prior_state=true' "$STATE_DIR/.b3-inprogress"; then mv "$STATE_FILE.b3-backup" "$STATE_FILE"; else test ! -e "$STATE_FILE" || rm "$STATE_FILE"; fi
# remove the sentinel — this diff is complete
rm "$STATE_DIR/.b3-inprogress"
echo "should-quiet-3 complete — clone restored to $START_BRANCH@$START_SHA"
```

### should-quiet-3 — RESUME-AT-NEXT-RUN block (multi-day stops)

**ONE selector test — does `$STATE_DIR/.b3-inprogress` exist in this repo?**
**NO** -> use the fresh per-diff block above. **YES** -> this diff is in progress; use THIS block.

```bash
set -euo pipefail
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
# (1) the sentinel must exist and identify THIS diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO SENTINEL — this diff is NOT in progress; use the fresh per-diff block; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-3' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=10276919fc2f1123cf0d8da7c0d43488087f1bc7' "$STATE_DIR/.b3-inprogress" || { echo 'RESUME FAILED: sentinel is for a different diff/base — STOPPING'; exit 1; }
# (2) re-verify the pin
test "$(git rev-parse HEAD)" = "10276919fc2f1123cf0d8da7c0d43488087f1bc7" || { echo 'RESUME FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
# (3) the planted diff must still be applied
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch || { echo 'RESUME FAILED: patch not applied — STOPPING'; exit 1; }
# (4) LIVE full-worktree proof (prove the CURRENT tree, not just the archives)
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69" || { echo 'RESUME FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/roonseek/transfer.py" || { echo 'RESUME FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RESUME FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) captured runs so far — the NEXT run is the first missing of run-1 / run-2 / run-3
ls ~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-3/ 2>/dev/null || true   # no listing = no runs captured yet -> next is run 1
# (6) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo 'resume OK — continue at the PRE-RUN block of the next missing run number.'
echo 'The patch is ALREADY applied: do NOT re-apply it, do NOT re-run the fresh block.'
```

### should-quiet-3 — FAILED-RUN RECOVERY block

Use THIS block when a run's step-8f/8g assert FAILED (an `unscoreable` run left `$STATE_FILE`
behind — the block exits BEFORE step 8h's `rm` and step 9's restore, so neither the fresh
block (sentinel guard) nor the RESUME block (step-8a empty-state assert) can restart it).
It archives the bad run dir, removes the failed state file, KEEPS the patch + sentinel, and
restarts the SAME run number.

```bash
set -euo pipefail
N=1   # <-- EDIT THIS ONE DIGIT to the run number that FAILED (1, 2, or 3), then paste the whole block
cd ~/roonseek
STATE_DIR=~/roonseek/.turingmind/state
STATE_FILE=$STATE_DIR/roonseek-.json   # detached checkout -> branch slug is empty -> the default key is roonseek-.json
# (1) confirm this is a failed-state recovery, not a fresh diff
test -e "$STATE_DIR/.b3-inprogress" || { echo 'NO IN-PROGRESS SENTINEL — use the fresh per-diff block, not recovery; STOPPING'; exit 1; }
grep -q 'diff_id=should-quiet-3' "$STATE_DIR/.b3-inprogress" && grep -q 'base_sha=10276919fc2f1123cf0d8da7c0d43488087f1bc7' "$STATE_DIR/.b3-inprogress" || { echo 'SENTINEL IS FOR A DIFFERENT DIFF/BASE — STOPPING'; exit 1; }
# (2) ARCHIVE the bad run dir out of the way (or delete it if empty) so its partial/failed
#     artifacts never get scored
TS=$(date +%s)
RUN_DIR=~/turingmind-code-review/docs/design/b3-ground-truth/runs/should-quiet-3/run-$N
if test -d "$RUN_DIR" && test -n "$(ls -A "$RUN_DIR" 2>/dev/null)"; then mv "$RUN_DIR" "$RUN_DIR.failed-$TS"; else rm -rf "$RUN_DIR"; fi
# (3) remove the failed state file so step 8a's empty-start assert can pass on the retry
rm -f "$STATE_FILE"
test ! -e "$STATE_FILE" || { echo 'FAILED STATE FILE STILL PRESENT — STOPPING'; exit 1; }
# (4) KEEP the patch and the .b3-inprogress sentinel intact (do NOT re-apply, do NOT re-run
#     step 6) and re-prove the LIVE full-worktree shape, fail-closed
test "$(git rev-parse HEAD)" = "10276919fc2f1123cf0d8da7c0d43488087f1bc7" || { echo 'RECOVERY FAILED: HEAD != BASE_SHA — STOPPING'; exit 1; }
git apply --reverse --check ~/turingmind-code-review/docs/design/b3-ground-truth/diffs/should-quiet-3.patch || { echo 'RECOVERY FAILED: patch not applied — STOPPING'; exit 1; }
test "$(git diff | shasum -a 256 | awk '{print $1}')" = "66fe1425076d445854818d56e9010bac80a3a6e0b75e8d8225881bed8dfeae69" || { echo 'RECOVERY FAILED: live full-diff sha mismatch — STOPPING'; exit 1; }
test "$(git diff --name-only | sort | paste -sd' ' -)" = "src/roonseek/transfer.py" || { echo 'RECOVERY FAILED: touched-path set mismatch — STOPPING'; exit 1; }
test -z "$(git status --porcelain --untracked-files=all | grep '^??' | grep -v '\.turingmind/')" || { echo 'RECOVERY FAILED: stray untracked files — STOPPING'; exit 1; }
# (5) re-capture the expected head
EXPECTED_HEAD=$(git rev-parse HEAD)
echo "recovery OK — RESTART run $N at its PRE-RUN block (step 8a); the patch and sentinel are intact"
```

---

## After all 6 diffs — hand off to Wave 3

All 18 run dirs committed (`runs(36-02): <id> run <n> captured` x 18), every source clone
restored to its starting branch, every sentinel removed. Tell the assistant "B3 runs are
complete" — Wave 3 (36-03) scores the archived state files against the committed answer-key
blob at ANSWER_KEY_COMMIT and writes the catch/FP report into
`plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md`.
