---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 07
subsystem: review-spine / Phase 0 scope normalizer
tags: [fix-loop, close-out, finalize, scope-args, D-17, ANSR-01, ANSR-02]
requires: []
provides:
  - "whole-token re-entry marker --close-out-after-rerun, stripped from $SCOPE_ARGS"
  - "Phase 0 printed line CLOSE_OUT_AFTER_RERUN=<0|1>"
  - "spines' Phase 5 no-findings skip re-enters with ${original_args} --finalize when the carrier is set"
affects: [58-04 (carried paragraph reads CLOSE_OUT_AFTER_RERUN), 58-08 (Rerun writes the marker; ${original_args} definition)]
tech-stack:
  added: []
  patterns: ["same whole-token padding strip + case match as --finalize", "reviewed-edit undo in the digest pin"]
key-files:
  created: []
  modified:
    - plugins/vibe-check/phases/review/00-scope.md
    - plugins/vibe-check/commands/review.md
    - plugins/vibe-check/commands/deep-review.md
    - plugins/vibe-check/scripts/test_scope_args.py
    - plugins/vibe-check/scripts/test_pause_batching.py
decisions:
  - "The D-17 close-out carrier is a whole-token --close-out-after-rerun marker in $ARGUMENTS; Phase 0 prints CLOSE_OUT_AFTER_RERUN=<0|1> and it never sets FINALIZE_MODE"
  - "The skip-section digest pin (116f14a) accepts the carried-close-out clause as a second reviewed edit, undone byte-for-byte, instead of regenerating the digests"
requirements: [ANSR-01, ANSR-02]
metrics:
  completed: 2026-10-27
  tasks: 2
  commits: 3
  suite: "3358 passed / 0 failed (was 3344)"
---

# Phase 58 Plan 07: Close-out Carrier Across the Rerun Summary

Phase 0's normalizer fence now recognizes the whole-token `--close-out-after-rerun` marker. It strips the marker from `$SCOPE_ARGS` and prints one `CLOSE_OUT_AFTER_RERUN=<0|1>` line. Both command spines' Phase 5 no-findings skip honors it: a run that sees the carrier set and finds nothing re-enters Finalize instead of stopping. So when the owner says "close out" and the Rerun then fixes everything, the close-out still happens.

## Final fence (verbatim, 00-scope.md; 58-04 and 58-08 copy the token and the printed-line name from here)

```bash
# Strip the universal value-carrying flags (--codex / --min-confidence and their value token,
# both `--flag val` and `--flag=val` forms) out of $ARGUMENTS into $SCOPE_ARGS, then trim,
# so a flag-only invocation yields an EMPTY $SCOPE_ARGS. Also strip the value-less --finalize and
# --close-out-after-rerun tokens, whole token only (spine-level mode flags; $ARGUMENTS keeps them):
# after the squeeze every token is single-space delimited, so padding the ends gives whole-token
# matching. Leaves --all/--full/--fix/--include-docs intact.
SCOPE_ARGS=$(printf '%s' "$ARGUMENTS" \
  | sed -E 's/--codex[[:space:]]+[^[:space:]]+//g; s/--codex=[^[:space:]]+//g; s/--min-confidence[[:space:]]+[^[:space:]]+//g; s/--min-confidence=[^[:space:]]+//g' \
  | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/[[:space:]]+/ /g; s/^/ /; s/$/ /; s/ --finalize( --finalize)* / /g; s/ --close-out-after-rerun( --close-out-after-rerun)* / /g; s/^ //; s/ $//')
# Decide finalize mode once, whole token only, on the same squeezed token stream.
SQ=$(printf '%s' "$ARGUMENTS" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/[[:space:]]+/ /g')
case " $SQ " in *" --finalize "*) FINALIZE_MODE=1 ;; *) FINALIZE_MODE=0 ;; esac
printf 'FINALIZE_MODE=%s\n' "$FINALIZE_MODE"
# The fix loop's close-out carrier, decided the same way; never sets FINALIZE_MODE.
case " $SQ " in *" --close-out-after-rerun "*) CLOSE_OUT_AFTER_RERUN=1 ;; *) CLOSE_OUT_AFTER_RERUN=0 ;; esac
printf 'CLOSE_OUT_AFTER_RERUN=%s\n' "$CLOSE_OUT_AFTER_RERUN"
```

Spine clause, identical in `commands/review.md` (Phase 5 skip bullet) and `commands/deep-review.md`. It is appended after `… to ship." and stop`:

> — unless Phase 0 printed `CLOSE_OUT_AFTER_RERUN=1` (the fix loop's Rerun carried the owner's close-out, D-17): then print "✅ No issues to fix — closing out as you asked." and re-enter the orchestrator with `$ARGUMENTS = "${original_args} --finalize"`, exactly as the fix-loop card's Close out does; `${original_args}` is this run's `$ARGUMENTS` minus every whole-token `--finalize` and `--close-out-after-rerun`)

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED: TestCloseOutCarrier* + TestSpineNoFindingsCarry, mutants M4-M7 | 10ae2c6 | scripts/test_scope_args.py |
| 2 | GREEN: normalizer fence + prose; no-findings skip in both spines | e0e175b | phases/review/00-scope.md, commands/review.md, commands/deep-review.md |
| 2 (deviation) | Skip-section digest pin accepts the reviewed clause | b0c8f59 | scripts/test_pause_batching.py |

## Verification (observed)

- **RED (Task 1):** `pytest -q scripts/test_scope_args.py -k "CloseOutCarrier or NoFindingsCarry"` gave `119 failed, 9 passed` (subtests included). Example: `'49-foo --close-out-after-rerun' != '49-foo'`. M4-M7 failed their `assertIn`/`assertNotEqual` precondition because the fence and spine text were not there yet. `-k "not CloseOutCarrier and not NoFindingsCarry"` gave `28 passed, 190 subtests passed`, so the older locks were unchanged.
- **GREEN (Task 2):** `pytest -q scripts/test_scope_args.py scripts/test_fix_loop_card.py scripts/test_card_text.py scripts/test_tracecheck.py scripts/test_foreground_dispatch.py` gave `201 passed, 506 subtests passed`.
- **Full suite:** the first run after GREEN gave `2 failed, 3357 passed`. Both failures were in `test_pause_batching.py::TestSkipSectionsByteIdentical` (see Deviations). After the fix: **`3358 passed, 4543 subtests passed`, 0 failed**.
- **Acceptance greps:**
  - `grep -c 'CLOSE_OUT_AFTER_RERUN' 00-scope.md` = 3 lines. The prose sits on one long line, alongside the case line and the printf line. Counting occurrences instead, `grep -o … | wc -l` = 8. So "≥ 4" holds for occurrences, not for lines.
  - `printf 'CLOSE_OUT_AFTER_RERUN=%s` count = 1.
  - `CLOSE_OUT_AFTER_RERUN=1` count = 1 in review.md and 1 in deep-review.md.
  - `No changes to review` count = 1, same as HEAD (the stop line was not touched).
- **Live fence smoke** (the real fence pulled out with `normalizer_block`, run under bash and zsh, same output from both):
  - `ARGUMENTS='49-foo --close-out-after-rerun'` → `FINALIZE_MODE=0`, `CLOSE_OUT_AFTER_RERUN=1`, `SCOPE_ARGS=[49-foo]`
  - `ARGUMENTS='foo--close-out-after-rerun'` → `FINALIZE_MODE=0`, `CLOSE_OUT_AFTER_RERUN=0`, `SCOPE_ARGS=[foo--close-out-after-rerun]`

## Mutants applied to the real files (each observed failing, then reverted with `git checkout -- <file>`)

| Mutant | Edit to the real file | Observed |
| ------ | --------------------- | -------- |
| M4 | Removed `s/ --close-out-after-rerun( --close-out-after-rerun)* / /g; ` from the 00-scope.md fence | test_scope_args: 17 failed |
| M5 | Removed the marker `case` line and its `printf` from the fence | 99 failed |
| M6 | `*" --close-out-after-rerun "*)` → `*"--close-out-after-rerun"*)` (substring match) | 9 failed |
| M7 | review.md no-findings bullet with the ` — unless …` clause removed | 2 failed |
| M7b | Same edit in deep-review.md | 1 failed |
| M8 | review.md clause `closing out as you asked` → `closing out as asked` | test_pause_batching: 2 failed (digest + new clause mutant test) |
| M9 | deep-review.md: appended ` Extra.` after the clause | test_pause_batching: 1 failed (digest) |

After the reverts, `git status` was clean for those files and `test_scope_args.py` showed 41 passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The Phase 5 skip-section digest pin rejected the new spine clause**
- **Found during:** Task 2, full suite
- **Issue:** `test_pause_batching.py::TestSkipSectionsByteIdentical` pins the `### Skip conditions` sections of both spines to sha256 digests of HEAD 116f14a, which says "never regenerate". The plan's required edit to the no-findings bullet changes those bytes, so 2 subtests failed. The plan's list of spine-reader tests did not include this file.
- **Fix:** Followed the file's existing "one reviewed edit" pattern. Added `SKIP_CARRY_CLAUSE` (the exact D-17 clause) and changed `pinned_skip_section()` to undo `"and stop" + clause` → `"and stop)"` when the clause appears exactly once. The digests are unchanged, and every other byte in the section is still pinned. Any change to the clause wording breaks the digest (new test `test_skip_digest_mutant_inside_carry_clause`; mutants M8 and M9 on the real files). Removing the clause entirely still matches the digest, because that is the 116f14a text. That case is caught by `TestSpineNoFindingsCarry` (M7/M7b).
- **Cost if wrong:** if the owner wanted the skip sections frozen with no exceptions, the D-17 spine clause would have to move out of the skip section, and both this test change and the spine edit would need redoing.
- **Files modified:** plugins/vibe-check/scripts/test_pause_batching.py
- **Commit:** b0c8f59

## Known Stubs

None. `${original_args}` is used in the spine clause and defined inline there. The formal definition in `50-fix-loop.md` and the Rerun that writes the marker belong to 58-08. Until 58-08 lands, nothing writes `--close-out-after-rerun`, so the new branch is wired and tested but cannot be reached from the fix loop yet.

## Threat Flags

None beyond the plan's register. T-58-23 is covered by the whole-token strip and match, the negatives table, and M4/M6. T-58-25 is covered by the spine clause using the stripped `${original_args}`.

## Self-Check: PASSED

- FOUND: plugins/vibe-check/phases/review/00-scope.md, commands/review.md, commands/deep-review.md, scripts/test_scope_args.py, scripts/test_pause_batching.py
- FOUND commits: 10ae2c6, e0e175b, b0c8f59
