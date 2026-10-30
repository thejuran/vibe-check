# Phase 61 close runbook — vibe-check 2.14.0

Run these steps at milestone close, after the owner has signed off in 61-SIGNOFF.md (`Status: SIGNED OFF`). They are listed in order, and each one stops on failure. Run every fence through `bash -s <<'BASH' … BASH`, because the shell here is zsh. The candidate C is read from 61-CANDIDATE.md in every fence, never retyped. complete-milestone may move the phase directory under `.planning/milestones/`, so each fence looks in both places.

The common preamble below is repeated at the top of each fence that needs C:

```bash
cd /Users/julianamacbook/turingmind-code-review
CAND=$(ls .planning/phases/61-release-gate-decision-reliability/61-CANDIDATE.md \
          .planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-CANDIDATE.md 2>/dev/null | head -1)
test -n "$CAND" || { echo "61-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
```

## 1. Verify, audit, complete the milestone (skip its tag)

Run `/bm:verify-work 61`, then `/bm:audit-milestone v2.14`, then `/bm:complete-milestone v2.14` on `feat/v2.14-phase-61`.

**Skip complete-milestone's in-branch `git_tag` step and its tag push.** That step tags the local branch tip, and a squash merge leaves that commit off main's ancestry. The tag is made in step 6, on `origin/main`, after the tree-identity check.

Confirm afterwards that no tag was made:

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
test "$(git branch --show-current)" = "feat/v2.14-phase-61" || { echo "WRONG BRANCH — STOPPING"; exit 1; }
if git rev-parse -q --verify refs/tags/v2.14 >/dev/null; then echo "LOCAL TAG v2.14 EXISTS (complete-milestone tagged the branch) — delete it with 'git tag -d v2.14' before continuing — STOPPING"; exit 1; fi
if git ls-remote --tags origin | grep -q 'refs/tags/v2.14$'; then echo "REMOTE TAG v2.14 ALREADY EXISTS — STOPPING"; exit 1; fi
echo "no v2.14 tag yet — OK"
BASH
```

## 2. Freshness assert: nothing shipped changed since C

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
CAND=$(ls .planning/phases/61-release-gate-decision-reliability/61-CANDIDATE.md \
          .planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-CANDIDATE.md 2>/dev/null | head -1)
test -n "$CAND" || { echo "61-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
if ! git diff --quiet "$C" HEAD -- . ':(exclude).planning'; then
  echo "TREE CHANGED SINCE CANDIDATE — STOPPING"
  git diff --name-only "$C" HEAD -- . ':(exclude).planning'
  exit 1
fi
test -z "$(git status --porcelain -- plugins README.md)" || { echo "UNCOMMITTED CHANGES UNDER plugins/ OR README.md — STOPPING"; exit 1; }
echo "HEAD equals C outside .planning — OK"
BASH
```

If it fails: re-run the affected gates from 61-RELEASE-RECORD.md on the new commit, and all of them (G1-G9) if production code changed. The owner then signs off again on the new candidate.

## 3. Dependabot note (no action)

Re-state in the close summary: Dependabot alerts are disabled on thejuran/vibe-check (HTTP 403), and the CLI lacks the scope to list Dependabot PRs, so the release-time review could not run. The shipped scripts use only the Python standard library (G8: 32 files, 0 third-party imports), and pytest is test-only. No repository or account settings are changed.

## 4. Release PR, owner OK, squash merge

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
CAND=$(ls .planning/phases/61-release-gate-decision-reliability/61-CANDIDATE.md \
          .planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-CANDIDATE.md 2>/dev/null | head -1)
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
test "$(git branch --show-current)" = "feat/v2.14-phase-61" || { echo "WRONG BRANCH — STOPPING"; exit 1; }
BODY=$(mktemp "${TMPDIR:-/tmp}/pr7.XXXXXX")
{
  git log -1 --format=%B "$C" | grep -v '^Co-Authored-By:'
  printf '\n## Release gates (candidate %s)\n\n' "${C:0:7}"
  printf -- '- Full offline suite: 3821 passed, 0 failed\n'
  printf -- '- Real-chain regressions 193 passed; mode/recovery checks 520 passed\n'
  printf -- '- Replay vs released 2.13: 170 runs, 0 differences; no previously caught defect lost\n'
  printf -- '- Live PR diff fetch (PR #6, PR #4): identical to local; manifest valid; stdlib-only runtime\n'
  printf -- '- Live smoke (default review + Close out): PASS, with known limits listed in the release notes\n'
  printf '\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n'
} > "$BODY"
git push -u origin feat/v2.14-phase-61
gh pr create --base main --head feat/v2.14-phase-61 --title "release: vibe-check 2.14.0 — decision reliability" --body-file "$BODY"
rm -f "$BODY"
BASH
```

Show the PR to the owner. **Only after the owner OKs it in their own message:**

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
PR=$(gh pr view feat/v2.14-phase-61 --json number --jq .number)
test -n "$PR" || { echo "NO PR FOUND — STOPPING"; exit 1; }
gh pr merge "$PR" --squash
BASH
```

## 5. Tree-identity assert: origin/main ships C byte-for-byte

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
CAND=$(ls .planning/phases/61-release-gate-decision-reliability/61-CANDIDATE.md \
          .planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-CANDIDATE.md 2>/dev/null | head -1)
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
if git rev-parse -q --verify refs/tags/v2.14 >/dev/null; then echo "LOCAL TAG v2.14 EXISTS — STOPPING"; exit 1; fi
git tag -a v2.14 origin/main -m "vibe-check 2.14.0 — decision reliability"
test "$(git rev-parse 'v2.14^{commit}')" = "$(git rev-parse origin/main)" || { echo "TAG NOT ON origin/main — STOPPING"; exit 1; }
git push origin v2.14
BASH
```

## 7. GitHub release (do not skip — it was missed for v2.13)

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
NOTES=$(ls .planning/phases/61-release-gate-decision-reliability/61-RELEASE-NOTES.md \
           .planning/milestones/v2.14-phases/61-release-gate-decision-reliability/61-RELEASE-NOTES.md 2>/dev/null | head -1)
test -n "$NOTES" || { echo "61-RELEASE-NOTES.md NOT FOUND — STOPPING"; exit 1; }
gh release create v2.14 --verify-tag --latest --title "v2.14 — Decision reliability" --notes-file "$NOTES"
BASH
```

The notes file to use is `.planning/phases/61-release-gate-decision-reliability/61-RELEASE-NOTES.md`, or its archived copy. Use it exactly as signed off. If the owner chose to add the uncommitted-code limit to the README, drop that file's "(the first limit above is listed only in these notes)" parenthetical.

## 8. Remote verification

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
git fetch origin --tags
git show origin/main:plugins/vibe-check/.claude-plugin/plugin.json | grep -q '"version": "2.14.0"' || { echo "origin/main plugin.json NOT 2.14.0 — STOPPING"; exit 1; }
git ls-remote --tags origin | grep -q 'refs/tags/v2.14' || { echo "TAG v2.14 NOT ON REMOTE — STOPPING"; exit 1; }
gh release view v2.14 >/dev/null || { echo "GITHUB RELEASE v2.14 MISSING — STOPPING"; exit 1; }
echo "remote: main 2.14.0, tag v2.14, release v2.14 — OK"
BASH
```

## 9. Update the installed plugin

```bash
bash -s <<'BASH'
set -euo pipefail
claude plugin update vibe-check@thejuran
BASH
```

Then do a **full relaunch** of Claude Code. A same-process reload does not pick up a new plugin version. After the relaunch, verify:

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
ok = e.get("version") == "2.14.0" and e.get("gitCommitSha") == main
print("installed", e.get("version"), e.get("gitCommitSha"), "origin/main", main)
sys.exit(0 if ok else "INSTALLED PLUGIN NOT 2.14.0 AT origin/main — STOPPING")
PY
BASH
```

If the version is still 2.13.0 or the SHA lags, the registry is stale: uninstall and reinstall `vibe-check@thejuran`, relaunch, and re-check.

## 10. Clean up and record

```bash
bash -s <<'BASH'
set -euo pipefail
cd /Users/julianamacbook/turingmind-code-review
git checkout main
git pull --ff-only origin main
git branch -D feat/v2.14-phase-61
git fetch --prune
git branch -a | grep -q 'feat/v2.14-phase-61' && { echo "BRANCH STILL PRESENT — check remote deletion"; exit 1; } || echo "branch removed locally and remotely"
BASH
```

Update STATE.md and ROADMAP.md to shipped (v2.14 shipped as 2.14.0 on the merge date; tag v2.14 on the squash commit) per PLANNING-FORMAT.md, refreshing `last_updated`. Create the ROADMAP backlog entry 999.28 named in 61-RELEASE-RECORD.md §Carried, unless the owner's sign-off ruling changed it. Mark GATE-03's "ships" clause complete in REQUIREMENTS.md, or in its milestone archive.
