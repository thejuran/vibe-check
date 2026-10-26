# Phase 57 deferred items

## test_replay.py::TestDiffMode::test_member_only_mutation_exits_one (found during 57-05)

- **Status:** pre-existing red, out of 57-05 scope (57-05 changes no Python under test here; score.py untouched).
- **Cause:** the `"member"` mutant in `test_replay._MUTANTS` (line ~697) anchors on the score.py text
  `carried_obligations[id(m)]["obligation"], m, pass_number)\n            members.append(ref)\n`.
  57-04 (`04e2c65` / `273a1e4`) rewrote that region of score.py, so the anchor now matches 0 times
  (`AssertionError: 0 != 1 : mutation anchor moved: member`).
- **Fix owner:** re-anchor the mutant on the current score.py member-append line (a test-only change);
  belongs with 57-04 follow-up or the 57-07 cross-check.
- **Note:** earlier waves reported 7 red because the holdout-barrier hook skipped test_replay.py; in
  the 57-05 full run it was collected (3182 passed / 8 failed: the 7 known card-wording/57-06 reds + this one).
