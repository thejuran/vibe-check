# Phase 65 close runbook — vibe-check 2.15.0

**Run from the main session only.** Executor agents must not push, merge, tag or release; a relayed approval does not count. Every owner OK below is the owner's own AskUserQuestion selection in the main session.

Run these steps at milestone close, after the owner has signed off in 65-SIGNOFF.md (`Status: SIGNED OFF (owner, <date>)`). They are listed in order, and each one stops on failure (`— STOPPING`). Run every fence through `bash -s <<'BASH' … BASH`, because the shell here is zsh. The candidate C is read from 65-CANDIDATE.md in every fence, never retyped (currently b073e31fb77f3f5ca32747f8c549ec552687b1be). complete-milestone may move the phase directory under `.planning/milestones/`, so each lookup checks both places and tolerates the missing one (`|| true`; under `set -o pipefail` a failing `ls` otherwise aborts the fence silently).

Tag and title: `v2.15`, `v2.15 — Lean orchestration`, tag message `vibe-check 2.15.0 — lean orchestration`, unless the owner chose otherwise at sign-off (65-SIGNOFF.md `## Tag and title`; if changed, update every fence below before running it).

Common preamble (repeated at the top of each fence that needs C):

```bash
cd /Users/julianamacbook/turingmind-code-review
CAND=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md \
          .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md 2>/dev/null || true; } | head -1)
test -n "$CAND" || { echo "65-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
```

## 1. Entry gate, then verify, audit and complete the milestone (skip its tag)

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
SIGN=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-SIGNOFF.md \
          .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-SIGNOFF.md 2>/dev/null || true; } | head -1)
test -n "$SIGN" || { echo "65-SIGNOFF.md NOT FOUND — STOPPING"; exit 1; }
grep -q '^Status: SIGNED OFF (owner, ' "$SIGN" || { echo "NOT SIGNED OFF — STOPPING"; exit 1; }
test "$(git branch --show-current)" = "feat/v2.15-phase-65" || { echo "WRONG BRANCH — STOPPING"; exit 1; }
echo "signed off, on feat/v2.15-phase-65 — OK"
BASH
```

Then run `/bm:verify-work 65`, then `/bm:audit-milestone v2.15`, then `/bm:complete-milestone v2.15` on `feat/v2.15-phase-65`.

**Skip complete-milestone's in-branch tag step and its tag push.** That step tags the local branch tip, and a squash merge leaves that commit off main's ancestry. The tag is made in step 6, on `origin/main`, after the tree-identity check. Confirm afterwards that no tag was made:

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
test "$(git branch --show-current)" = "feat/v2.15-phase-65" || { echo "WRONG BRANCH — STOPPING"; exit 1; }
if git rev-parse -q --verify refs/tags/v2.15 >/dev/null; then echo "LOCAL TAG v2.15 EXISTS (complete-milestone tagged the branch) — delete it with 'git tag -d v2.15' before continuing — STOPPING"; exit 1; fi
if [ -n "$(git ls-remote --tags origin refs/tags/v2.15)" ]; then echo "REMOTE TAG v2.15 ALREADY EXISTS — STOPPING"; exit 1; fi
echo "no v2.15 tag yet — OK"
BASH
```

## 2. Freshness assert: nothing shipped changed since C

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
CAND=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md \
          .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md 2>/dev/null || true; } | head -1)
test -n "$CAND" || { echo "65-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
if ! git diff --quiet "$C" HEAD -- . ':(exclude).planning'; then
  echo "TREE CHANGED SINCE CANDIDATE — STOPPING"
  git diff --name-only "$C" HEAD -- . ':(exclude).planning'
  exit 1
fi
test -z "$(git status --porcelain -- plugins README.md docs .github)" || { echo "UNCOMMITTED CHANGES UNDER SHIPPED PATHS — STOPPING"; exit 1; }
echo "HEAD equals C outside .planning — OK"
BASH
```

If it fails: a shipped file changed after the gates ran. That is a new candidate: rebuild 65-CANDIDATE.md, re-run all gates G1–G11 from 65-RELEASE-RECORD.md on it, and the owner signs off again.

## 3. Dependabot re-check (no action)

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
echo "== open Dependabot alerts"
gh api repos/thejuran/vibe-check/dependabot/alerts --jq '[.[] | select(.state=="open")] | length' 2>&1 || echo "(exit $?)"
echo "== open Dependabot PRs"
gh pr list --repo thejuran/vibe-check --author app/dependabot --state open 2>&1 || echo "(exit $?)"
echo "== shipped runtime"
python3 -I .github/scripts/stdlib_only.py plugins/vibe-check
BASH
```

Quote the outputs in the close summary. Expected (65-CANDIDATE.md, 2026-11-16): alerts HTTP 403 "Dependabot alerts are disabled for this repository", no open Dependabot PRs, `34 shipped .py files; third-party imports: none`. The shipped scripts use only Python's standard library; pytest is test-only. No repository or account settings are changed. If an open Dependabot PR or a readable open alert appears, surface it to the owner before step 4 (a runtime dependency fix would be a new candidate).

## 4. Release PR, CI on its head (G12), owner OK, squash merge

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
CAND=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md \
          .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md 2>/dev/null || true; } | head -1)
test -n "$CAND" || { echo "65-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
test "$(git branch --show-current)" = "feat/v2.15-phase-65" || { echo "WRONG BRANCH — STOPPING"; exit 1; }
BODY=$(mktemp "${TMPDIR:-/tmp}/pr65.XXXXXX")
{
  git log -1 --format=%B "$C" | grep -v '^Co-Authored-By:'
  printf '\n## Release gates (candidate %s)\n\n' "${C:0:7}"
  printf -- '- Full offline suite: 4126 passed (scripts folder), 4599 passed (repo root); 0 failed, 0 skipped\n'
  printf -- '- Mac-only tests 7 passed; mode/recovery checks 898 passed\n'
  printf -- '- Replay vs released 2.14.1: 170 runs, 0 differences; no previously caught defect lost (25/26 kept, 0 regressed)\n'
  printf -- '- Five Close-out situations match 2.14.1 apart from the commands run; baseline kit and scorer unchanged\n'
  printf -- '- Close out 136,114 -> 131,381 bytes, 92 -> 85 steps; each review path +1,705 to +1,966 bytes and +2 counted steps (named growth, owner-signed)\n'
  printf -- '- Live smoke (default review + Close out incl. its decision card): PASS on this candidate\n'
  printf -- '- Manifest valid; stdlib-only runtime\n'
  printf '\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n'
} > "$BODY"
git push -u origin feat/v2.15-phase-65
gh pr create --base main --head feat/v2.15-phase-65 --title "release: vibe-check 2.15.0 — lean orchestration" --body-file "$BODY"
rm -f "$BODY"
BASH
```

Wait for CI, then check G12: `offline-suite` must be green on the PR's head commit.

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
PR=$(gh pr view feat/v2.15-phase-65 --json number --jq .number)
test -n "$PR" || { echo "NO PR FOUND — STOPPING"; exit 1; }
HEAD_SHA=$(gh pr view "$PR" --json headRefOid --jq .headRefOid)
test "$HEAD_SHA" = "$(git rev-parse HEAD)" || { echo "PR HEAD $HEAD_SHA IS NOT LOCAL HEAD — STOPPING"; exit 1; }
gh pr checks "$PR" --watch || true
N_PASS=$(gh pr checks "$PR" --json workflow,bucket --jq '[.[] | select(.workflow=="offline-suite" and .bucket=="pass")] | length')
N_ALL=$(gh pr checks "$PR" --json workflow,bucket --jq '[.[] | select(.workflow=="offline-suite")] | length')
test "$N_ALL" -ge 1 -a "$N_PASS" = "$N_ALL" || { echo "offline-suite NOT GREEN ON PR HEAD ($N_PASS of $N_ALL pass) — STOPPING"; exit 1; }
gh run list --commit "$HEAD_SHA" --workflow offline-suite.yml --json event,conclusion,headSha,url \
  --jq '.[] | "\(.event) \(.conclusion) \(.headSha) \(.url)"'
OK=$(gh run list --commit "$HEAD_SHA" --workflow offline-suite.yml --json event,conclusion,headSha \
  --jq "[.[] | select(.event==\"pull_request\" and .conclusion==\"success\" and .headSha==\"$HEAD_SHA\")] | length")
test "$OK" -ge 1 || { echo "NO GREEN pull_request RUN ON $HEAD_SHA — STOPPING"; exit 1; }
echo "G12 PASS: offline-suite green on PR #$PR head $HEAD_SHA"
BASH
```

Record G12 in 65-RELEASE-RECORD.md: replace the G12 row's `pending close — runbook step 4` / `PENDING` with the run URL, the summary line from the log (expect `… passed, 2 skipped, 5 deselected` on Linux) and `PASS`, commit it on the branch (`git add -f`, `.planning` only; this does not touch the shipped tree) and `git push`. That push moves the PR head, so run the G12 fence above again and require it to pass on the new head before asking the owner. If G12 is red, stop: a qualifying failure needs the owner's explicit go for a second fix round (the one D-08 round is spent) and a new candidate.

Show the PR and the G12 result to the owner. **Only after the owner's own OK (AskUserQuestion in the main session):**

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
PR=$(gh pr view feat/v2.15-phase-65 --json number --jq .number)
test -n "$PR" || { echo "NO PR FOUND — STOPPING"; exit 1; }
gh pr merge "$PR" --squash
BASH
```

## 5. Tree-identity assert: origin/main ships C byte-for-byte

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
CAND=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md \
          .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md 2>/dev/null || true; } | head -1)
test -n "$CAND" || { echo "65-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
git fetch origin
for p in plugins/vibe-check README.md; do
  test "$(git rev-parse "origin/main:$p")" = "$(git rev-parse "$C:$p")" || { echo "TREE DIFFERS: $p — STOPPING"; exit 1; }
done
echo "origin/main ships the gated candidate byte-for-byte"
BASH
```

Do not tag if this fails. Find out what differs (`git diff "$C" origin/main -- plugins/vibe-check README.md`) and treat it as a new candidate.

## 6. Tag origin/main (never the branch tip)

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
git fetch origin
if git rev-parse -q --verify refs/tags/v2.15 >/dev/null; then echo "LOCAL TAG v2.15 EXISTS — STOPPING"; exit 1; fi
if [ -n "$(git ls-remote --tags origin refs/tags/v2.15)" ]; then echo "REMOTE TAG v2.15 EXISTS — STOPPING"; exit 1; fi
git tag -a v2.15 origin/main -m "vibe-check 2.15.0 — lean orchestration"
test "$(git rev-parse 'v2.15^{commit}')" = "$(git rev-parse origin/main)" || { echo "TAG NOT ON origin/main — STOPPING"; exit 1; }
git push origin v2.15
BASH
```

## 7. GitHub release (do not skip — the tag alone leaves the release page on 2.14.1)

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
NOTES=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-RELEASE-NOTES.md \
           .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-RELEASE-NOTES.md 2>/dev/null || true; } | head -1)
test -n "$NOTES" || { echo "65-RELEASE-NOTES.md NOT FOUND — STOPPING"; exit 1; }
gh release create v2.15 --verify-tag --latest --title "v2.15 — Lean orchestration" --notes-file "$NOTES"
BASH
```

Use the notes file exactly as signed off.

## 8. Remote verification

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
git fetch origin --tags
git show origin/main:plugins/vibe-check/.claude-plugin/plugin.json | grep -q '"version": "2.15.0"' || { echo "origin/main plugin.json NOT 2.15.0 — STOPPING"; exit 1; }
test -n "$(git ls-remote --tags origin refs/tags/v2.15)" || { echo "TAG v2.15 NOT ON REMOTE — STOPPING"; exit 1; }
gh release view v2.15 >/dev/null || { echo "GITHUB RELEASE v2.15 MISSING — STOPPING"; exit 1; }
LATEST=$(gh release list --exclude-drafts --limit 20 --json tagName,isLatest --jq '.[] | select(.isLatest) | .tagName')
test "$LATEST" = "v2.15" || { echo "LATEST RELEASE IS '$LATEST', NOT v2.15 — STOPPING"; exit 1; }
echo "remote: main 2.15.0, tag v2.15, release v2.15 (Latest) — OK"
BASH
```

## 9. Update the installed plugin

```bash
bash -s <<'BASH'
set -euo pipefail
claude plugin update vibe-check@thejuran
BASH
```

Then do a **full relaunch** of Claude Code (a same-process reload does not pick up a new plugin version). After the relaunch, verify:

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
git fetch origin
MAIN=$(git rev-parse origin/main)
python3 -I - "$MAIN" <<'PY'
import json, os, sys
main = sys.argv[1]
d = json.load(open(os.path.expanduser("~/.claude/plugins/installed_plugins.json")))
entries = d.get("plugins", d).get("vibe-check@thejuran", [])
if not entries:
    sys.exit("vibe-check@thejuran NOT INSTALLED — STOPPING")
e = entries[0]
ok = e.get("version") == "2.15.0" and e.get("gitCommitSha") == main
print("installed", e.get("version"), e.get("gitCommitSha"), "origin/main", main)
sys.exit(0 if ok else "INSTALLED PLUGIN NOT 2.15.0 AT origin/main — STOPPING")
PY
BASH
```

If the version is still 2.14.1 or the SHA lags, the registry is stale: uninstall and reinstall `vibe-check@thejuran`, relaunch, and re-check.

## 10. Clean up and record

Local `main` holds local-only `.planning/` commits (7384e89 onward) that are not on `origin/main`; they rode in the release PR because `feat/v2.15-phase-65` was branched from `main`. Realign `main` only after asserting every one of them is in the merged branch, and never with `--hard`.

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
git fetch origin
git merge-base --is-ancestor main feat/v2.15-phase-65 || { echo "LOCAL main HAS COMMITS NOT IN feat/v2.15-phase-65 — STOPPING"; exit 1; }
git switch main
git reset --keep origin/main
test "$(git rev-parse main)" = "$(git rev-parse origin/main)" || { echo "main NOT AT origin/main — STOPPING"; exit 1; }
git branch -D feat/v2.15-phase-65
if [ -n "$(git ls-remote --heads origin feat/v2.15-phase-65)" ]; then
  git push origin --delete feat/v2.15-phase-65
fi
git fetch --prune
if git branch -a | grep -q 'feat/v2.15-phase-65'; then echo "BRANCH STILL PRESENT — STOPPING"; exit 1; fi
echo "branch removed locally and on GitHub; main realigned to origin/main"
BASH
```

Then update STATE.md and ROADMAP.md to shipped per PLANNING-FORMAT.md (v2.15 shipped as 2.15.0 on the merge date; tag v2.15 on the squash commit; refresh `last_updated`; ROADMAP has no active milestone until the next one starts), record publish status and G12 in 65-RELEASE-RECORD.md (or its milestone archive copy), and mark GATE-04/05/06's "ships" clause complete in REQUIREMENTS.md or its milestone archive.
