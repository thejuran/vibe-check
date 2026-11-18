---
phase: 66-close-out-freshness
reviewed: 2026-11-18T00:00:00Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - plugins/vibe-check/scripts/closeout_fresh.py
  - plugins/vibe-check/scripts/finalize_inputs.py
  - plugins/vibe-check/scripts/carry_state.py
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/phases/review/00-scope-all.md
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/30-collect-score.md
  - plugins/vibe-check/phases/review/45-persist-all.md
  - plugins/vibe-check/phases/review/45-persist.md
  - plugins/vibe-check/scripts/fixtures/future-schema.json
  - docs/design/lean-v2.15/tools/finalize_capture.py
  - .github/scripts/test_stdlib_only.py
  - plugins/vibe-check/scripts/test_closeout_fresh.py
  - plugins/vibe-check/scripts/test_finalize_inputs.py
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_finalize_parity_grid.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
  - plugins/vibe-check/scripts/test_worktree_snap.py
  - plugins/vibe-check/scripts/test_confirmed_fix.py
  - docs/design/lean-v2.15/tools/test_finalize_capture.py
findings:
  critical: 1
  warning: 2
  info: 4
  total: 7
status: issues_found
---

# Phase 66: Code Review Report

**Reviewed:** 2026-11-18
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Reviewed the 346f67c3..HEAD changes: the new `closeout_fresh.py` freshness check, its wiring in `finalize_inputs.py`, the `_covering` newest-wins change in `carry_state.py`, the `--all` `reviewed_tree` prose, the refusal prose in `90-finalize.md`, the capture tool, and the tests. `test_closeout_fresh.py` passes (67 tests, 535 subtests). Its mutant tests are real: they swap in the broken variant and assert the opposite outcome. The git argv is clean. No finding path reaches git, `reviewed_tree` is checked against an anchored hex regex before use, and the explicit prefix flags held up when I tried `diff.noprefix` and `diff.mnemonicPrefix` (git 2.55).

Main problems:
1. The `PATH_RE` pre-filter makes Close out refuse forever on any decision about a file whose name has `+`, `[`, `(`, `@`, a space or non-ASCII characters. These names are common in SvelteKit and Next.js projects. Reviewing again does not clear the refusal, which breaks D-16.
2. Close out does not see edits to files flagged `assume-unchanged` or `skip-worktree`. I reproduced this, so these edits can still let Close out write.
3. If anything goes wrong while the candidates are being worked out, the check returns "nothing stale" and the error is not logged.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Decisions on files with common characters in their names (`+page.svelte`, `[slug]`, `(group)`, spaces, non-ASCII) refuse Close out forever

**File:** `plugins/vibe-check/scripts/closeout_fresh.py:114-115, 202-203` (locked in by `plugins/vibe-check/scripts/test_closeout_fresh.py:528-535`)
**Issue:** `_cause` returns `unverifiable` for any record whose `file` fails `fixcommit.PATH_RE` (`^[A-Za-z0-9._/-]+$`). The path never reaches a git argv. The whole tree is diffed and paths are only dictionary keys, so this filter blocks no injection. What it does is mark the decision stale no matter what is on disk. A fresh review does not change the filename, so the decision stays `current` and the next Close out refuses again with `unverifiable`. The user cannot get out of this loop, which breaks D-16 ("every refusal cause must be clearable"). `score.py` does not filter findings by `PATH_RE`, so these records really do reach Close out. Reproduced with no change on disk, the file present in the reviewed tree and on disk:

```
src/routes/+page.svelte   -> [{'cause': 'unverifiable', ...}]
app/blog/[slug]/page.tsx  -> [{'cause': 'unverifiable', ...}]
app/(group)/x.ts          -> [{'cause': 'unverifiable', ...}]
my file.py                -> [{'cause': 'unverifiable', ...}]
src/a.py                  -> []
```

Any SvelteKit or Next.js app-router repo where the owner defers or dismisses a finding can never Close out. In 2.15.0 the same Close out wrote REVIEW.md. `test_unverifiable_path_failing_PATH_RE` asserts `"src/a b.py"` is unverifiable, so the test suite locks the loop in.
**Fix:** Only fail closed on paths that git would C-quote in a diff header, because those are the ones `diff_ranges` cannot key. Run the diff with `core.quotePath=false` so UTF-8 names come out raw:

```python
def _path_ok(path):
    # git C-quotes a header only for control chars, '"' and '\\' once
    # core.quotePath=false; diff_ranges cannot key those, so fail closed.
    return (isinstance(path, str) and path and not path.startswith("/")
            and not any(c in path for c in '"\\') and
            all(ord(c) >= 0x20 and c != "\x7f" for c in path))

# _git(): ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
#          "-c", "core.quotePath=false", *args]
```

Then change `test_unverifiable_path_failing_PATH_RE` to assert that `+page.svelte`, `[slug]` and `my file.py` are checked normally (both stale and kept outcomes). Add a clearability test (refuse, review again, write) for one of these names. A filename with a space gets a trailing tab in the diff header. `_file_path` already strips it, but a test should pin that too.

## Warnings

### WR-01: Edits to files flagged `assume-unchanged` or `skip-worktree` are invisible, so Close out keeps a stale decision

**File:** `plugins/vibe-check/scripts/closeout_fresh.py:311-321`
**Issue:** `git diff <tree>` compared against the working tree goes through the index, and git does not stat entries flagged assume-unchanged or skip-worktree. It reports the index copy instead of what is on disk. Reproduced: three files each got the same edit on line 10. One was marked `--assume-unchanged` and one `--skip-worktree`. `changed_ranges` returned only `{'c.py': [[10, 10]]}`. A deferred or dismissed decision on either flagged file passes as unchanged and Close out writes REVIEW.md. That breaks D-04 ("judged against the code as it is on disk now") and is the exact wrong keep 999.40 exists to stop. Developers commonly use `skip-worktree` to hide local config edits.
**Fix:** Fail closed on these entries. Read `git ls-files -v -z` once (no paths on the argv) and treat a candidate file as `unverifiable` when its tag is lowercase (assume-unchanged) or `S` (skip-worktree):

```python
def flagged_files(root):
    out = _git(root, ["ls-files", "-v", "-z"])
    return {e[2:] for e in out.split("\0")
            if len(e) > 2 and (e[0].islower() or e[0] == "S")}
# in _cause, after the untracked check:
#     if file in flagged: return "unverifiable"
```

Add a test for each flag.

### WR-02: An unexpected error while finding the decided records lets Close out write, with nothing logged

**File:** `plugins/vibe-check/scripts/closeout_fresh.py:350-353`
**Issue:** `stale_decisions` catches every exception from `decided_records` and returns `[]`, which means "nothing stale". `finalize_inputs._run` then goes on to the gate and can write REVIEW.md. The module promises to fail closed, and it does for everything after the candidates are known, but this step fails open. `finalize_inputs` has already run `state_reason`, so a raise here can only come from a defect in `_spots`, `carry_state.covering_decision` or `_fix_closes`, or from an odd state shape that `state_reason` accepts. In those cases the decisions should not be trusted. The exception is also swallowed with no log, which goes against the project rule on silent exception handling. `test_malformed_state_returns_empty_and_runs_no_git` covers only states that `finalize_inputs` refuses earlier anyway, so the fail-open path for a valid state is untested.
**Fix:** Keep the `[]` result for states `carry_state.open_findings` already treats as malformed (it returns `[]` and does not raise). Let any other exception propagate so `finalize_inputs.run` turns it into `EXIT_GATE` (fail closed):

```python
def stale_decisions(state, blobs, cwd=None):
    candidates = decided_records(state, blobs)   # let it raise -> EXIT_GATE
    if not candidates:
        return []
    ...
```

Add a test that patches `_spots` to raise and asserts the helper does not return `write`.

## Info

### IN-01: `OBJECT_ID_RE` uses `$`, which also matches before a trailing newline

**File:** `plugins/vibe-check/scripts/closeout_fresh.py:299, 305` (regex in `worktree_snap.py:98`)
**Issue:** `"<40 hex>\n"` passes `OBJECT_ID_RE.match` and is passed to git. git rejects it, so the result is `unverifiable` (fail closed and harmless), but the check is weaker than it reads.
**Fix:** Use `OBJECT_ID_RE.fullmatch(value)`, or `\Z` in the regex.

### IN-02: Line-ending-only edits disappear under `core.autocrlf` or `text` attributes

**File:** `plugins/vibe-check/scripts/closeout_fresh.py:316`
**Issue:** Diffing against the working tree runs git's clean (EOL) conversion first. A CRLF/LF-only change on the decided line produces no diff, although D-07 says any byte change counts. The review snapshot (`add -u`) normalizes the same way, so the two sides agree. The gap is small.
**Fix:** Accept and document it, or add `-c core.autocrlf=false` and check that `text`/`eol` attributes cannot hide a change.

### IN-03: Misleading cause after `git rm --cached`

**File:** `plugins/vibe-check/scripts/closeout_fresh.py:206-213`
**Issue:** If a file is removed from the index but left on disk unchanged, the diff shows a whole-file range. The refusal then says "that line changed" (`line`), but the code did not change. The right advice is the untracked path ("add the file to git"). The outcome still fails closed.
**Fix:** If a hit file has the same content on disk as in the reviewed tree but is missing from the index, report `untracked`. Or document that `line` covers this case.

### IN-04: Environment can still redirect what git compares

**File:** `plugins/vibe-check/scripts/closeout_fresh.py:274, 281-293`
**Issue:** `_store_env_ro` clears the index and object-directory variables. It leaves `GIT_DIR`, `GIT_WORK_TREE` and replace refs active (`refs/replace/*` can stand in for the reviewed tree object). This matches `worktree_snap.py`, so the two sides stay consistent and I found no fail-open path. It is just more exposure than needed for a check that only reads.
**Fix:** Add `--no-replace-objects` to the git calls. Optionally note that `GIT_DIR`/`GIT_WORK_TREE` are deliberately kept so the snapshot and the check point at the same repository.

## Set aside (needs ruling)

### SA-01: The review itself also misses edits to assume-unchanged and skip-worktree files

**Where:** `plugins/vibe-check/scripts/worktree_snap.py:166-174` (not in this phase's changed files)
**Why excluded:** `take` copies the real index, flags included, before `add -u`, so the review snapshot records HEAD's copy of such files. The reviewers' `git diff HEAD` misses them too. This predates Phase 66.
**Effect if left as is:** Decisions can rest on code the reviewers never saw. Fixing only WR-01 would make Close out refuse on these files, and a fresh review would record the same stale snapshot, so the refusal could loop (D-16).
**Needs:** A ruling on whether WR-01's fix should also clear these flags on the snapshot side (copy the index without them), or simply fail closed and tell the user to clear the flag. Fix in this phase or defer.

---

_Reviewed: 2026-11-18_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
