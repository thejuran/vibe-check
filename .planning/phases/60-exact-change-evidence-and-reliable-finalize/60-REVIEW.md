---
phase: 60-exact-change-evidence-and-reliable-finalize
reviewed: 2026-10-29T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - plugins/vibe-check/scripts/diff_ranges.py
  - plugins/vibe-check/scripts/test_diff_ranges.py
  - plugins/vibe-check/phases/review/00-scope.md
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/review/30-collect-score.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/test_finalize_card.py
  - plugins/vibe-check/scripts/test_decision_continuity.py
findings:
  critical: 1
  warning: 3
  info: 5
  total: 9
status: issues_found
---

# Phase 60: Code Review Report (gap round 60-06..60-09)

**Reviewed:** 2026-10-29
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

> This report replaces the f442464 review (range `98aa9cc..HEAD`) for the gap-round changes. Scope: `git diff 2f84d2e..HEAD` on the eight files listed above, plus the surrounding code those changes touch. Findings from the earlier review that are still open in the changed code are carried forward and marked "(carried)".

## Summary

The gap round fixes what it set out to fix. Of the earlier findings, WR-01 (suppressBlankEmpty), WR-02 (colored or non-diff text gives `{}`), WR-03 (textconv / relative), WR-04 (GATEFILE not rebuilt) and WR-06 (cross-call shell variable) are closed. I checked each against real git in a scratch repo. Binary-only and mode-only diffs still give `{}` and are not falsely refused. The six flags are identical, in the same order, on every git range-source line in 00-scope, 05-state and the 30-collect-score table. The suite passes: `pytest -q test_diff_ranges.py test_finalize_card.py test_decision_continuity.py` gives 347 passed, 379 subtests passed.

Remaining problems:

1. **The literal-sha fix opened a command-injection path (CR-01).** The agent now pastes `head_sha` from the state file into a double-quoted shell argument. Double quotes do not stop `$(...)`. I reproduced it: the fence ran the payload and still printed valid ranges with exit 0.
2. **The six flags do not cover every setting that changes the diff (WR-01).** With `diff.submodule=log`, a change to a submodule alone is refused as "not a unified diff", so the review halts. When other files also change, the submodule's range is silently dropped.
3. **The new GATEFILE rule is not applied to the post-answer gate re-run (WR-02).** The rebuild paragraph now says the gate must read flags written from fresh counts. The step-3 re-run after recording decisions never says so. If the agent reuses the earlier GATEFILE, the gate decides on counts from before the decisions.
4. **Temp files are still never removed (WR-03, carried).** The rebuild now leaves even more of them behind.

The new tests are mostly real guards: each new mutant (M20–M22) trips against the real module. Two are weaker than they look (IN-02, IN-03).

## Critical Issues

### CR-01: Substituting the literal `head_sha` into a double-quoted argument allows command execution

**File:** `plugins/vibe-check/phases/review/05-state.md:52,86`; `plugins/vibe-check/phases/review/30-collect-score.md:72,77`
**Issue:** 05-state step 2 binds `$LAST_REVIEWED_SHA` from `state.passes[-1].head_sha` in the state JSON. It does not validate the value. The pass ≥ 2 range-source row then has the agent paste that value as a literal into `"<last-reviewed-sha>"`. Double quotes stop word-splitting, but they do not stop `$(...)` or backtick command substitution.

The state file lives at `.turingmind/state/format-53/<key>.json` inside the reviewed repo. Phase 0.7 only *suggests* adding `.turingmind/` to `.gitignore`. A contributor can therefore commit a state file with a predictable key: GSD mode uses `<phase-dir-name>.json`. Its last `head_sha` could be `$(curl … | sh)HEAD`. 90-finalize.md already treats state-derived file paths as possibly attacker-written and checks them with PATH_RE and guard.py before any git call. `head_sha` gets no such check.

Before this round, the row used an unquoted `$LAST_REVIEWED_SHA` that was never bound in the fence's shell. Expanding a variable's value never re-runs `$()`, so the old exposure was option injection at most (earlier IN-02). Literal substitution turns it into command execution. The new paragraph at 30-collect-score.md:77 says the quotes make a bad value fail. That holds for empty and unsubstituted values, but not for this one.

Reproduced in a scratch repo:
```bash
set -o pipefail
RANGES_JSON=$(git diff --no-color --no-ext-diff --no-textconv --no-relative \
  --src-prefix=a/ --dst-prefix=b/ "$(touch "$T/pwned")HEAD" | python3 diff_ranges.py)
# -> exit 0, valid ranges printed, and $T/pwned was created
```
**Fix:** Validate the value where it is bound, and fail closed:
```text
05-state.md step 2: `$LAST_REVIEWED_SHA = state.passes[-1].head_sha` only when it
matches ^[0-9a-f]{40}([0-9a-f]{24})?$ ; any other value (including null) halts the
run with a fixed message — never substitute an unvalidated value into a command.
```
Also switch the placeholder to single quotes (`'<last-reviewed-sha>'`), or have the fence check it before use with `git rev-parse --verify --quiet --end-of-options '<sha>^{commit}'`. Add a test that substitutes `$(touch marker)HEAD` into the row as the prose directs and asserts the marker file is not created and the fence halts. `<phase-start-sha>` comes from `git log --format=%H`, so it is always hex. Applying the same check to it is cheap and keeps the two rows symmetric.

## Warnings

### WR-01: `diff.submodule` is not neutralized: a submodule-only change halts the review, and otherwise its range is silently dropped

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:66,70-73`; `plugins/vibe-check/scripts/diff_ranges.py:204-216`; `plugins/vibe-check/scripts/test_diff_ranges.py:74-76`
**Issue:** 30-collect-score.md:66 says the six flags mean "a repo-local … setting cannot change the text the helper reads". `diff.submodule` (user-global or repo-local, values `log` or `diff`) still changes `git diff` output. With `log`, a submodule pointer change prints as `Submodule sub 366ee10..c6092ce:` / `  > c` with no `diff --` header. Reproduced in a scratch repo with the six flags:
- **Only the submodule changed:** the helper sees no diff structure and raises `REASON_NOT_A_DIFF`, exit 2, so the review pass halts ("Review halted — the changed lines could not be read"). This is a false refusal introduced by this round's not-a-diff rule. Every pass halts for that user until they change their git config.
- **Submodule plus other files:** exit 0, and the `sub: [[1, 1]]` range the default setting gives is silently dropped.
- **`diff.submodule=diff`:** the submodule's inner diff is printed under keys such as `sub/f`, which is a different line space from the superproject.
**Fix:** Add `--submodule=short` to the fixed flag set everywhere it appears: the three 00-scope/05-state lines, the 30-collect-score table and prose, the diff_ranges docstring CLI, and `PROSE_FLAGS`. Add `diff.submodule=log` to `test_hostile_repo_config_does_not_change_ranges`, using a fixture that contains a submodule change, and assert that the raw output really differs, as the other hostile cases do.

### WR-02: The post-answer gate re-run does not rewrite GATEFILE, so the gate can decide on counts from before the decisions

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:272` (cf. `:55`, `:67`)
**Issue:** After `record-decisions`, step 3 says: "RE-RUN the counts step and the gate ONCE (the same `BLOBFILE=` literal this attempt printed)". The gate reads only GATEFILE (line 57), and GATEFILE holds the counts written *before* the owner's answers. Step 3 never says to write the recounted `outstanding_cw` / `unacknowledged_medium` / `undecided_nv` into a GATEFILE.

This round's rebuild rule (line 67) says outright that a GATEFILE built from counts that may predate the current state must not be reused. But it covers only the failure rebuild, and this re-run is "this attempt", so the wording does not forbid reuse here. An agent that re-runs the gate fence as written gets the pre-decision verdict. The result is a "Finalize stays blocked" stop, and the list printed under it comes from the *new* counts, which may be empty. The owner then has to run `--finalize` a second time to get a close-out that should have finished in this turn. `test_finalize_card.py:649` checks only the ordering of this step; nothing walks the re-run against a GATEFILE.
**Fix:** In step 3, write: "RE-RUN the counts step (the same `BLOBFILE=` literal), then run the gate-input fence again so it prints a NEW `GATEFILE=`, write the seven-key `flags` from the re-counted `$COUNTS_JSON` to it, and run the gate on that literal." Add a fresh-shell walk test in `TestFinalizeFreshShellWalk`: record decisions that close every row, run the gate on the attempt's original GATEFILE, and show it stays blocked. Then run it on a newly written GATEFILE and show it returns `write`. Add a needle or mutant on the new sentence.

### WR-03 (carried, earlier WR-05): Finalize temp files are never removed; the rebuild now leaves twice as many

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:15-22,48-57,67`
**Issue:** There is still no `rm -f` for `BLOBFILE`, `GATEFILE` or `<GATEFILE>.err`. Card files do get cleanup (lines 175, 243, 271-272). The new rule makes the rebuild mint a second GATEFILE as well as a second BLOBFILE, so a failed-then-rebuilt Finalize leaves up to six `vc.*` files. The same paragraph warns against reusing stale files from "an earlier attempt or an earlier session", and leaving them around invites exactly that. The traceback in `.err` is still never shown or named anywhere.
**Fix:** As before: after the gate's action is consumed, and on each stop path, run `rm -f '<BLOBFILE>' '<GATEFILE>' '<GATEFILE>.err'` with the printed literals (for the rebuild, both attempts' files). Name the `.err` path in the halt sentence, or keep the file only when the gate exits non-zero.

## Info

### IN-01: "`{}` is printed only for a genuinely empty diff" is not true

**File:** `plugins/vibe-check/phases/review/30-collect-score.md:89`
**Issue:** By the helper's own contract (diff_ranges.py:23-25, 33) and test (`test_binary_only_and_mode_only_diffs_are_empty`), binary-only, mode-only, deletion-only (`+++ /dev/null`) and C-quoted-path-only diffs also give `{}` with exit 0. The sentence could lead an agent to treat a `{}` from a non-empty diff as an anomaly, or to state that the diff was empty.
**Fix:** "…so `{}` means no changed text lines the helper can range: an empty diff, or one that changes only binary files, modes, deleted files or C-quoted paths."

### IN-02: The escape-refusal tests cover only fully colored diffs, so the fail-open case the rule exists for is not locked

**File:** `plugins/vibe-check/scripts/test_diff_ranges.py:437-445,839-843`
**Issue:** With `color.ui=always`, every line, including `diff --git`, starts with ESC. In that case the new not-a-diff rule refuses the text anyway. M21 (`if False:`) trips only because the expected *reason* changes from `REASON_ESCAPE` to `REASON_NOT_A_DIFF`. The case where the escape rule is the only protection is a partly colored diff, and no test covers it. Example: `color.diff.meta=normal`, so the headers are plain but `@@` is cyan. Reproduced: on that input, the M21 mutant returns `{}` with exit 0 (fail-open), while the real module refuses. A weakened rule, for example one that checks only the first line, would pass the current tests.
**Fix:** Add a case using `git -c color.ui=always -c color.diff.meta=normal diff HEAD`. Assert that the plain `diff --git` line is present, that the `@@` line starts with ESC, and that the helper refuses with `REASON_ESCAPE`. Point M21 at it.

### IN-03: Two new checks assert less than they claim

**File:** `plugins/vibe-check/scripts/test_diff_ranges.py:1141-1152`; `plugins/vibe-check/scripts/test_finalize_card.py:2213-2214`
**Issue:**
- `literal_sha_rule_holds` checks that `"substitute"` appears *anywhere* in the range bullet. The word appears four or more times ("substitute it" in both rows, "the agent substitutes" in the new paragraph), and only the sentence mutant is exercised. Deleting the "substitute it" instruction from either row would not trip it.
- The subtest "old rule: same GATEFILE reused fails identically" runs the same empty file twice and asserts the same halt. Nothing in it reads the prose, so it documents behaviour but guards no rule. The rule itself is guarded only by the RETRY_NEEDLES presence check.
**Fix:** Assert "substitute" per row (on `prose_range_row(text, "GSD")` and `prose_range_row(text, "default or GSD")`), with a mutant for each. Rename the subtest to say it illustrates the old behaviour, or drop it.

### IN-04 (carried, earlier IN-01): The commit-series refusal recognises only SHA-1 mbox separators

**File:** `plugins/vibe-check/scripts/diff_ranges.py:52`
**Issue:** `^From [0-9a-f]{40} ` does not match a 64-hex SHA-256 `format-patch` separator. This is unchanged in this round.
**Fix:** `re.compile(r"^From (?:[0-9a-f]{40}|[0-9a-f]{64}) ")`, plus a mutant test.

### IN-05 (carried, earlier IN-03): The counts fence leaves stderr uncaptured, unlike the gate fence

**File:** `plugins/vibe-check/phases/shared/90-finalize.md:25`
**Issue:** This is unchanged in this round. The rebuild path now runs the counts fence up to twice, so a `carry_state.py` traceback can reach the owner twice.
**Fix:** Redirect stderr to a printed file, as the gate fence does, and clean it up under WR-03.

## Set aside (needs ruling)

### SA-01 (carried): The Write tool on a file mktemp has already created

**Where:** `plugins/vibe-check/phases/shared/90-finalize.md:15-22,48-55,67`
**Why excluded:** This depends on how the harness behaves, not on code in the diff.
**Effect if left as is:** If Write refuses to overwrite an existing file that has not been Read, both the first attempt and the single rebuild fail at the BLOBFILE/GATEFILE write, and Finalize stops. The rebuild now re-mints GATEFILE, so it would hit the same refusal a second time.
**Needs:** A ruling on whether to confirm with a live run, or to add a "Read the printed path first" step.

### SA-02 (carried): The PR-mode range source fails outright on PRs over GitHub's diff limits

**Where:** `plugins/vibe-check/phases/review/30-collect-score.md:74`
**Why excluded:** This is an external API limit, and failing closed is the intended behaviour.
**Effect if left as is:** On very large PRs, every pass halts and nothing is scored.
**Needs:** A ruling: accept the limit, or add a fallback (fetch the PR refs and run a local `git diff <base>...<head>`).

---

_Reviewed: 2026-10-29_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
