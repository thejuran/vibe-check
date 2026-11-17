Lean-orchestration release. Close out (`--finalize`) used to have Claude run each of its fingerprint, counting and decision commands itself; one checked helper script now does that mechanical work and returns one result, and Claude acts on that result. Reviewers, the scoring formula and scores are unchanged: an archived replay of 170 past runs re-scores with no differences. Not measured: no B3 or holdout run, so there are no 2.15 false-alarm or catch numbers. v2.11 (5/18 · 15/15, MISS) remains the last measured result.

Same behaviour as 2.14.1 except:
- If the saved-progress file cannot be read at all (for example because of its permissions), Close out shows its stop sentence on its own; the shell's "Permission denied" line no longer appears above it. The stop and the one automatic retry are unchanged.
- If a folder, branch or phase name that the review prints contains `$`, a backtick, `"`, `\` or a line break, the review stops before scoring anything, with one "Review halted" line.
- A GSD review that reaches the saved-progress step with an empty phase id stops there with one "Review halted" line. (A pre-release 2.15 build could instead let two GSD phases share one saved-progress file; this was fixed before release and never shipped.)
- On a machine whose locale is C, POSIX or C.UTF-8 (common on Linux servers, not on a Mac), a saved-progress file that is not valid UTF-8 is refused with `state is not valid JSON` instead of a `malformed state` line. The refusal and the stop are unchanged.
- Each git call Close out makes to fingerprint a fixed file has a 60-second limit. If git is slower, that file is left out, so its finding stays open rather than closing.
- When Close out runs from a subfolder, a file with unsaved or staged edits is no longer fingerprinted, so a "fix obsolete" verdict no longer closes a finding on code that has changed.
- Inline Python commands in the review steps run in isolated mode, so a file such as `json.py` at the root of the reviewed repo no longer runs during a review (a security hole present in 2.14.1).

**What changed in size** (bytes of instruction files Claude loads, and counted steps Claude runs, 2.14.1 → 2.15.0):
- Close out: 136,114 → 131,381 bytes (−4,733) and 92 → 85 steps (−7).
- Each review path grew by +1,705 to +1,966 bytes (+0.54% to +0.89%) and by +2 counted steps, from the safety and saved-progress-path fixes above:
  - plain review: 192,057 → 193,762 bytes (+1,705), 36 → 38 steps (+2 counted steps)
  - deep review: 268,997 → 270,714 bytes (+1,717), 42 → 44 steps (+2 counted steps)
  - plain review `--all`: 284,926 → 286,880 bytes (+1,954), 45 → 47 steps (+2 counted steps)
  - deep review `--all`: 361,866 → 363,832 bytes (+1,966), 51 → 53 steps (+2 counted steps)
  - fix loop: 255,070 → 256,939 bytes (+1,869), 112 → 114 steps (+2 counted steps)

These are size counts, not usage or price figures.

Known limits:
- Only the default review and Close out ran live for 2.15.0 (including Close out's decision card); GSD, range, PR, incremental, `--all` and the fix loop's fix-and-verify path are covered by tests only.
- During Close out, a git call slower than 60 seconds leaves that file out of the fingerprints, so a "fix obsolete" verdict on it closes nothing and the finding stays open. Each `--finalize` run fingerprints again from scratch.
- If the Close out helper itself fails, the message is "I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived.", and no detail about the failure is recorded.
- The unsafe-name stop covers `$`, a backtick, `"`, `\` and line breaks only. Names containing `;`, `&` or `'` are not stopped; this is safe only as long as every pasted name stays inside double quotes.
- In GSD mode, if two phase folders share a name (for example `v1-phases/01-setup` and `v2-phases/01-setup`), or a container folder such as `phases` is given as the phase, the review picks one folder without warning and both can share one saved-progress file. This predates 2.15.0. Keep phase folder names unique.
- Downgrading from 2.15.0 to 2.14.1 has not been tested. 2.15.0 adds no saved-progress field, so no effect is expected.
- Seen in the live check: after you defer every finding in the fix loop, the review may stop and ask instead of continuing. Your decisions are saved and Close out completes; it takes one extra step. (This limit is listed only in these notes.)

Full list in the README.

4,126 tests passing at release.
