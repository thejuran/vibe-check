# Phase 52 live runs

Four live runs of the accepted-fix harness on the synthetic case `py-clamp-01`
(an off-by-one in `clamp()`), driven through the real plugin loaded from this
working tree. Every run passed the containment preflight first (probe record
37/37, fingerprint `2590e9f6…`, no MCP server loaded). All four ran on one
plugin build: the tree at `ad7e5be`, recorded as `plugin_sha` `b4f7212`
(a docs-only commit on top of it), `plugin_tree_dirty: false`.

Run command (from the repository root):

```
H=docs/design/fix-harness
env -u CLAUDECODE $H/.venv/bin/python $H/tools/fixharness.py run \
  --case py-clamp-01 --mode <default|gsd> --kind <preservation|clean> --out $H/runs/phase52/<ID>
```

## Results

| id | mode | kind | entry | verdict | cards | questions | turn_end_questions | owner_commands | repeats | deferred_non_seeded | would_be_owner_questions | execution_seconds (automated execution time) | clean_tree_checkpoint | plugin_sha | attempts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P-D | default | preservation | review | COMPLETE | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 395.9 | n/a (sentinels) | `b4f7212` | 3 |
| P-G | gsd | preservation | review | COMPLETE | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 413.9 | n/a (sentinels) | `b4f7212` | 3 |
| C-D | default | clean | finalize | COMPLETE | 1 | 2 | 0 | 1 | 0 | 0 | 2 | 288.9 | passed | `b4f7212` | 3 |
| C-G | gsd | clean | review | COMPLETE | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 307.4 | passed | `b4f7212` | 2 |

**Waiting-on-owner time was not measured.** These are scripted runs with no
human in the loop (D-13). Every record carries `waiting_on_owner_seconds:
null` with the note "not measured — scripted run, no human in the loop". The
seconds above are automated execution time only, never a human-time saving.

`would_be_owner_questions` counts every question a person would have had to
answer: each card question, each turn that ended on unrecognised text, and
each repeat. The one owner command per run is the `--finalize` the harness
types after the loop ends on its one-liner (D-24, Pitfall 6). It is recorded
as a normal owner command, not as repair.

What each run did:

- **P-D** (`/vibe-check:review`): pass 2 reviewed the planted sentinels and
  carried the seeded finding. One fix-loop card listed `#1 src/clamp.py:13 —
  clamp returns hi - 1 at the upper bound (off-by-one)`, answered `Apply all
  & rerun`. Commit `fix(review-pass-2): clamp returns hi - 1 at the upper
  bound (off-by-one)` touched only `src/clamp.py`. On pass 3 the `bugs`
  reviewer rechecked the finding and resolved it. The loop ended on "No issues
  to fix", and `--finalize` wrote `.turingmind/REVIEW.md` and archived the
  state. All three sentinels were byte-identical afterwards.
- **P-G** (`/vibe-check:review 52-harness-case`): same flow in GSD mode.
  Same card, one `fix(review-pass-2): …` commit touching only
  `src/clamp.py`, closed by `--finalize` with the phase id.
- **C-D** (`/vibe-check:review --finalize`, clean tree): the Finalize card
  (2 questions: the finding row and the shared reason) was answered `Fix
  all`. The fix-loop subset asked no card (D-06), and one
  `fix(review-pass-2): …` commit landed. The rerun reviewed that commit, and
  `bugs` resolved the finding. The tree was clean before the second
  `--finalize`, which wrote REVIEW.md.
- **C-G** (`/vibe-check:review 52-harness-case`, clean tree): pass 2 had no
  new diff, so it took the carry-forward-only path (snapshot, then scoring).
  One fix-loop card, one `fix(review-pass-2): …` commit, a rerun that
  resolved the finding, the clean-tree checkpoint, then `--finalize`.

Each record holds 6 obligation snapshots and 1 tracked hash (the seeded
finding), disposed `resolved`. Nothing ended missing, ambiguous, downgraded
or regressed. Containment: 0 backstop denials, 0 protected-path denials,
sandbox enabled, `failIfUnavailable` true, no unsandboxed retry.
`fixharness.py check --run` exits 0 for all four directories.

## Attempts

Failed and superseded attempts are kept under `attempts/<ID>-<n>/` with
their `run.json`:

| attempt | verdict | what happened |
|---|---|---|
| P-D-1 | COMPLETE | First P-D. COMPLETE, but on an earlier plugin build (before the dispatch and rerun fixes below). Superseded so that all four records come from one build. |
| P-G-1 | FAILED | The three review agents were dispatched without `run_in_background: false`, ran in the background, and the turn ended mid-pass ("running in the background … Phase 3 starts once all three have returned"). |
| C-D-1 | FAILED | After the Finalize-routed fix was committed, the rerun stopped on "No changes to review." and nothing rechecked the fix. The next `--finalize` asked the same Fix card again, and then the session asked for another `--finalize`. |
| P-D-2, P-G-2, C-D-2 | COMPLETE | Runs on build `4f124b2`. Superseded after the carry-forward snapshot fix so that all four records come from one build. |
| C-G-1 | FAILED | The carry-forward-only path skipped Phase 1, so no git-safety snapshot existed. Phase 3's fail-closed gate halted the pass ("before snapshot is missing or unreadable"). |

## Defects found and fixed

Plugin (`plugins/vibe-check/`). Each fix has a test, landed before the Phase 54 freeze:

1. **Bare `mktemp` fails under a sandbox.** macOS `mktemp` without a
   template ignores `$TMPDIR` and writes to `/var/folders`, which Claude
   Code's sandbox does not allow. Every fence now passes
   `"${TMPDIR:-/tmp}/vc.XXXXXX"`. Test `a1ae5f5`, fix `93b2a50`.
2. **Subagent dispatches could run in the background** (P-G-1). The hard
   contract and the triage, Phase-2 and fix dispatch sites now require
   `run_in_background: false`. Test `32f49b3`, fix `4469239`.
3. **The fix loop's rerun never reviewed a committed fix in default-diff
   mode** (C-D-1). This forced a redundant Fix card (D-22) and an extra
   `--finalize`. Phase 0 now lets that rerun through to Phase 0.5, as the
   Rerun paragraph already promised. Every other clean default-diff run
   still stops. Test `32f49b3`, fix `4f124b2`.
4. **The carry-forward-only path had no git-safety snapshot** (C-G-1). Step 5
   of Phase 0.5 now takes the same snapshot, with the same fail-closed stop,
   before Phase 3. The gate itself is unchanged. Test `0c80861`, fix
   `ad7e5be`.

Harness (`docs/design/fix-harness/`):

5. **The case key named a `logic` agent the plugin does not have**, so the
   seeded finding could never be rechecked (52-10 smoke). The key now names
   `bugs`, and seeding refuses any agent without a plugin reviewer file.
   Test `f2dcd29`, fix `014d102`.
6. **Sessions could read and write Claude Code's shared per-uid temp dir**
   (52-10 threat flag). Each session now gets a private 0700 temp root
   (`CLAUDE_CODE_TMPDIR`, created before launch). The shared
   `/tmp/claude-<uid>` is read- and write-denied in Seatbelt and in the
   permission rules. Test `ecb09fc`, fix `355ffd5`, probe re-recorded
   `c92b98c`.

## 52-10 carry-overs

- **Obsolete fix verdict while the fixed file differs from HEAD:** not a
  defect. The plugin refuses to record an "already fixed" verdict on a dirty
  file by design. Otherwise reverting an uncommitted edit could close a
  finding whose HEAD still has the defect. With a real reviewer (`bugs`) the
  seeded finding closes through the normal recheck, so the preservation runs
  never needed the obsolete route.
- **Re-hashed seeded finding after the fix:** not seen in these runs. Each
  record tracked exactly one hash, which ended `resolved`.
- **"REVIEW.md written" turn-end wording:** observed live, and it varies from
  run to run: "The review is finalized: `.turingmind/REVIEW.md` is written…"
  (P-D), "Phase 52-harness-case is finalized and approved…" (P-G), "I wrote
  `.turingmind/REVIEW.md`. The review is finalized…" (C-D), "…the report is
  written to `.turingmind/REVIEW.md`" (C-G). The harness classified all four
  as done, and the verdict independently checked that REVIEW.md exists and
  the state was archived.
- **Split "Apply selected…" card sub-questions:** still not confirmed live.
  `py-clamp-01` seeds one finding, so no run can produce a split selection
  card. This needs a multi-finding case (Phase 55 or later).
