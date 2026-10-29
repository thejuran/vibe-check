---
phase: 60-exact-change-evidence-and-reliable-finalize
reviewed: 2026-10-29T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/review/30-collect-score.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/diff_ranges.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_diff_ranges.py
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_nv_render.py
findings:
  critical: 0
  warning: 6
  info: 3
  total: 9
status: issues_found
---

# Phase 60: Code Review Report

**Reviewed:** 2026-10-29
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

I reviewed `git diff 98aa9cc..HEAD` for the nine files. The core of `diff_ranges.py` (marker-driven ranges, budget accounting, pure-deletion pair, net-deletion extension, `\ No newline` handling, quoted/dev-null paths) is correct on every edge shape I traced, and the test suite pins those shapes against real git under three context widths.

The defects sit at the edges, in what reaches the helper. Three git settings change the diff text even with the prose flags applied. One of them makes every review halt. Another silently shifts the ranges. A third input class, a colored or non-diff stream, gives `{}` with exit 0, which is fail-open. The range fence also relies on shell variables surviving across fresh shells, which is the same failure mode this phase fixes in Finalize. In Finalize, the new once-only rebuild does not rebuild the gate input file. The mktemp files are never cleaned up.

I reproduced every WARNING about the helper's input against real git in a scratch repo (commands in each finding).

## Warnings

### WR-01: `diff.suppressBlankEmpty=true` makes every review halt

**File:** `plugins/vibe-check/scripts/diff_ranges.py:146-148`, `plugins/vibe-check/phases/review/30-collect-score.md:68-75`
**Issue:** With the git config `diff.suppressBlankEmpty=true` (user-global or repo-local), git prints a blank context line as an empty line instead of `" "`. `_walk_hunk` reads tag `""` and raises `REASON_BAD_BODY_LINE`. Any diff whose hunk context holds a blank line gets this, which is nearly every real diff. Each pass halts with "Review halted — the changed lines could not be read". None of the prose flags (`--no-color --no-ext-diff --src-prefix --dst-prefix`) override this setting. Reproduced with `git -c diff.suppressBlankEmpty=true diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ HEAD | python3 diff_ranges.py`, which printed `unexpected line in hunk body` and exited 2. The same diff without the setting gives `{"f": [[3, 3]]}`. The effect is that a required workflow breaks for any user who has this common setting.
**Fix:** Pin the setting in every range-source call, and/or accept an empty line inside a hunk as a context line (GNU patch does the same):
```bash
git -c diff.suppressBlankEmpty=false diff --no-color --no-ext-diff --no-textconv --src-prefix=a/ --dst-prefix=b/ HEAD
```
```python
tag = body[:1]
if body == "":          # diff.suppressBlankEmpty prints blank context as ""
    tag = " "
```
Add `diff.suppressBlankEmpty` to `test_hostile_repo_config_does_not_change_ranges`.

### WR-02: Colored or non-diff input gives `{}` with exit 0 (fail-open); the per-route lines in 00-scope/05-state omit the mandatory flags

**File:** `plugins/vibe-check/scripts/diff_ranges.py:166-187`; `plugins/vibe-check/phases/review/00-scope.md:43,99`; `plugins/vibe-check/phases/review/05-state.md:86`; `plugins/vibe-check/phases/review/30-collect-score.md:87`
**Issue:** `ranges_from_diff` skips every line it does not recognise outside a hunk. A colored diff (`\x1b[36m@@ …`) has no line that matches `_HUNK`, so the whole diff is skipped and the result is `{}` with exit 0. A diff from an external-diff driver or any other non-unified text does the same. 30-collect-score.md:87 says "An empty diff prints `{}` and is not a failure", so the pass scores with no in-diff term. That is exactly the silent loss the fence exists to prevent. Reproduced: `git -c color.ui=always diff HEAD | python3 diff_ranges.py` gave `{}` and `rc=0` on a diff with a real change.

The new "Range source for 30-collect-score" lines at 00-scope.md:43/99 and 05-state.md:86 give the bare command (`git diff HEAD`, `git diff $PHASE_START`, `git diff $LAST_REVIEWED_SHA`) without the flags. An agent that copies the command from the phase it is reading gets this failure in any repo with `color.ui=always`.
**Fix:** Make the helper refuse instead of returning empty. For example, add a new fixed reason when the input holds a `diff --git `/`+++ ` header line but no hunk was parsed for it, and when any line starts with `\x1b`. In the three prose lines, either give the full flagged command or write "the route's row in 30-collect-score.md step 2 (flags included)" instead of a bare command.

### WR-03: textconv (and `diff.relative`) still change the diff text, which silently shifts or drops ranges

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:66,70-73`
**Issue:** The prose says the flags make sure "a repo-local color, prefix or external-diff setting cannot change the text the helper reads". Porcelain `git diff` also applies textconv filters (`.gitattributes` `diff=<drv>` plus `diff.<drv>.textconv`). Line numbers then refer to the converted text, not the file, and the helper cannot detect it. Reproduced: with a textconv that prepends two lines, a change on line 3 came out as `{"f": [[5, 5]]}` with exit 0. Separately, with `diff.relative=true`, a fence run from a subdirectory prints `{}` for changes outside that subdirectory.
**Fix:** Add `--no-textconv --no-relative` to every git row in the table, the prose claim and `PROSE_FLAGS` in the tests, and add a textconv case to the hostile-config test.

### WR-04: The once-only rebuild does not rebuild the gate input, so a failed GATEFILE write fails again and stops

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:47-67`
**Issue:** The rebuild rule (line 67) mints a new `BLOBFILE=` and then says "re-run the counts fence and the gate once with the new literal". The gate reads `GATEFILE`, and its contents come from the counts. The rule never says to create a new GATEFILE or rewrite it with the fresh counts. It also does not list a missing or empty `GATEFILE=` file as a trigger. Case 1: the GATEFILE Write failed (empty file, which is exactly the fresh-shell failure this phase targets). Then `finalize_gate.py` crashes on empty stdin (verified: `JSONDecodeError` traceback, rc=1), the rebuild runs the gate again on the same empty file, and Finalize stops even though nothing in the state is wrong. Case 2: the first counts fence failed and the agent reuses a GATEFILE written earlier. Then the gate decides on counts that do not match the rebuilt fingerprints.
**Fix:** In line 67, say that the rebuild also runs the GATEFILE mktemp fence again (a new `GATEFILE=` printed), writes the flags from the rebuilt `$COUNTS_JSON` into it, and never reuses an earlier `GATEFILE=`. Add "the `GATEFILE=` path is missing or empty" to the trigger list, and lock this with a mutant in `TestFinalizeFreshShellWalk`.

### WR-05: Finalize temp files are never removed; gate diagnostics go into an orphan `.err` file

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:15,48,57,64`
**Issue:** Each Finalize attempt now creates `BLOBFILE`, `GATEFILE` and `GATEFILE.err` with mktemp, and a rebuild creates a second set. No `rm -f` anywhere in the finalize or fix-loop prose touches these files. The card files (`SUGGESTFILE`, `REFSFILE`, `RESOLVEFILE`) do get explicit cleanup. So every `--finalize` leaves 3 to 6 files in `$TMPDIR`. Stale `vc.*` BLOBFILEs from earlier attempts are exactly what line 67 warns must never be reused, and leaving them around makes that mistake more likely. `GATEFILE.err` captures the helper's traceback, but nothing ever reads, logs or names it, so the failure detail is lost to the owner and to any later debugging.
**Fix:** After the gate's action is consumed (and on each stop path), run `rm -f "<BLOBFILE>" "<GATEFILE>" "<GATEFILE>.err"` with the literal paths, as the card cleanup does. On gate failure, print the `.err` path in the halt line (path only, not its contents), or keep the `.err` file only when the gate exits non-zero.

### WR-06: Range fence relies on `$LAST_REVIEWED_SHA` / `$PHASE_START` across fresh shells; an empty variable silently gives an unstaged-only diff

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:71-72,77-86`
**Issue:** The fence runs in a fresh shell. `$LAST_REVIEWED_SHA` is set by the agent from state JSON (05-state.md:52), and `$PHASE_START` by a separate 00-scope fence. Neither survives into this call. If the agent pastes the row as written, the unquoted empty variable disappears and the command becomes `git diff --no-color … ` with no revision. That compares the index with the working tree: it succeeds, and it leaves out every committed and staged change in the range. The helper returns a well-formed subset, so nothing halts and in-diff evidence is silently lost for those lines. This phase made the same point explicitly for `BLOBFILE`/`GATEFILE` ("a shell variable does not survive into a separate Bash call") but did not apply it here.
**Fix:** Tell the agent to substitute the literal SHA, and guard it inside the fence:
```bash
set -o pipefail
REV='<literal sha, or HEAD>'
git rev-parse --verify --quiet "$REV^{commit}" >/dev/null || { echo "Review halted — the changed lines could not be read from the diff; nothing was scored." >&2; exit 1; }
if RANGES_JSON=$(git diff --no-color --no-ext-diff --no-textconv --src-prefix=a/ --dst-prefix=b/ "$REV" | python3 "<VC_ROOT literal>/scripts/diff_ranges.py"); then …
```

## Info

### IN-01: Commit-series refusal only recognises SHA-1 mbox separators

**File:** `plugins/vibe-check/scripts/diff_ranges.py:47`
**Issue:** `^From [0-9a-f]{40} ` does not match a 64-hex SHA-256 `format-patch` separator. A series from a SHA-256 repo therefore gets past the mbox guard. If no later budget check trips, it gives merged per-commit coordinates, the exact case the guard is there to stop.
**Fix:** `re.compile(r"^From (?:[0-9a-f]{40}|[0-9a-f]{64}) ")`, plus a mutant test.

### IN-02: `head_sha` from the state file becomes a bare git argument with no validation

**File:** `plugins/vibe-check/phases/review/05-state.md:52,86`; `plugins/vibe-check/phases/review/30-collect-score.md:72`
**Issue:** The new range source `git diff … $LAST_REVIEWED_SHA` puts a value read from `.turingmind/state/…json` in option position. The state file lives inside the reviewed working tree, and nothing checks `head_sha` against a hex pattern. A crafted value like `--output=<path>` would be read as a git option (an earlier `..HEAD` form had the same exposure).
**Fix:** Validate `^[0-9a-f]{40}([0-9a-f]{24})?$` when binding `$LAST_REVIEWED_SHA`, and resolve it with `git rev-parse --verify --end-of-options "<sha>^{commit}"` before the diff.

### IN-03: Counts fence leaves stderr uncaptured, unlike the gate fence

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:25`
**Issue:** The gate fence now captures helper diagnostics (`2>"$GATEFILE.err"`) so only the stop sentence shows. The counts fence still passes `carry_state.py` stderr straight through, so an unexpected exception shows a Python traceback to the owner on the same path the rebuild rule covers.
**Fix:** Redirect the counts fence's stderr the same way, to a printed file, and clean it up as in WR-05.

## Set aside (needs ruling)

### SA-01: Write tool on a mktemp-created (existing, unread) file

**Where:** `plugins/vibe-check/phases/shared/90-finalize.md:15-22,48-55`
**Why excluded:** It depends on harness behaviour, not on code in the diff. The same pattern was already used for ROWSFILE/SUGGESTFILE/REFSFILE before this phase.
**Effect if left as is:** In Claude Code, Write refuses to overwrite an existing file that has not been Read. mktemp creates the file, so the first Write to `BLOBFILE=`/`GATEFILE=` may be rejected. That attempt and the single rebuild would then both fail and stop.
**Needs:** A ruling on whether to confirm with a live run (or add an explicit "Read the printed path first" instruction) before ship.

### SA-02: PR-mode range source hard-fails on PRs above GitHub's diff limits

**Where:** `plugins/vibe-check/phases/review/30-collect-score.md:74`
**Why excluded:** The limit is an external API constraint. Failing closed is the intended behaviour.
**Effect if left as is:** Very large PRs (over about 300 files or 20k lines) make `gh pr diff --color never` fail, so every pass on them halts and cannot be scored.
**Needs:** A ruling: accept the limit, or add a fallback (for example a local `git diff <base>...<head>` after fetching the PR refs).

---

_Reviewed: 2026-10-29_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
