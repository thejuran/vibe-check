# Phase-49 dress rehearsal record (2026-10-06, LABEL=rehearsal, never scored)

The whole Phase-49 kit (`RUN-PHASE49-v2.11.md`) was run end to end on the scratch diff
`rehearsal-scratch` (one f-string SQL query appended to the tracked `triggarr/db.py`;
`rehearsal/diff/`), on the batch-7 build of the S-candidate tree, before snapshot S is cut. Driver:
assistant via tmux; every measured-session keystroke came from the fixed set.

A4-commit: 9e095611c719e18cc8cdaa3af4c73e1f9f00ed50

That is the commit whose batch-7 build (`~/.vibe-check-snapshots/batch7-9e095611c719`, recorded by
the one `rehearsal-snapshot: batch7` line in `RUN-METHOD-NOTES-phase49.md`) the installed cache ran
during `a4-smoke`, and the `--plugin-dir` the measured session loaded.

## A4 — the installed-cache git guard (Phase-48 carry)

A4: PASS (installed-cache guard saw vibe-check:compliance)

- Launch WITHOUT `--plugin-dir` in the throwaway repo `~/.b3/a4-scratch-1791332596` (one commit,
  one stash entry), after `resync-cache` put the batch-7 build into the installed
  `~/.claude/plugins/cache/thejuran/vibe-check/2.10.0`.
- The fixed owner-framed prompt was sent once; the model dispatched `vibe-check:compliance` on the
  first try (no refusal, no rewording needed).
- `blocks.jsonl` row (`a4/blocks-row.jsonl`):
  `{"agent": "compliance", "command": "git stash pop", "reason": "refused: git subcommand form is not read-only (fail closed)", "tool": "Bash"}`
- Hook line (`a4/hook-line.txt`, from the session's local sub-transcript):
  `PreToolUse:Bash hook error: [python3 ~/.claude/plugins/cache/thejuran/vibe-check/2.10.0/scripts/gitguard.py hook]`
- No inline-plugin (`--plugin-dir`) marker anywhere in the A4 transcripts; no gitguard line names
  any other path.
- The scratch HEAD and the stash were unchanged; the agent's separate `git log --oneline -1` ran.

## Captured fix-loop labels (Phase-47 decline path)

From the rehearsal run's local transcript (`toolUseResult.answers`, printed with `ascii()`):

- `'Stop here…'` (the "Pass 1" card, option 4 at capture time)
- `'Abandon'` (the "Stop here" card, option 2 at capture time)

Both annotations were empty. These are byte-identical to the runbook's committed
`ALLOWED_ANSWERS = {"Stop here…", "Abandon"}` line, so that line was not edited. Selection was BY
LABEL: the driver read the numbered line carrying the exact label and sent that digit alone (no
Enter; the digit selects and submits).

## The rehearsal run (`rehearsal-scratch/run-1`, commit 61d970a8d2edbf04d2ea36c8aa3b71c57a63c025)

- `post`: `OK pre-run records precede the pass timestamp`; `OK one isolated pass at 4a154be…`;
  tree.diff sha and touched path matched; no untracked files.
- The non-snapshot-plugin-path gate passed: the transcript never names the installed cache or the
  repo plugin path, and names the snapshot plugin root. The snapshot loaded alone (flagged risk 1,
  "snapshot + installed cache both loading", did not occur).
- driver-check: `driver contamination: none (typed=2 harness-skipped=14 answers=2)`; the
  Phase-43 reference transcript re-asserted clean first.
- Card count: `cards: 2`, `malformed: 0` (the designed decline path: one "Pass 1" card, one "Stop
  here" card). Re-running the generated driver-check and `count_cards.py count` over the local
  transcript gave the same values; its sha256 equals the committed `transcript.jsonl.sha256`, and
  the transcript is gitignored.
- `state_shape.py --schema future`: PASS.
- Codex: `joined reason=null lanes=7/7`; peak context 221481.
- Gitsnap halt: none. Git-guard blocks during the measured run: 0 (`git-guard blocks: 0`).

## Cache parity

- At resync: `forward=134/134 reverse=0 extra` against the snapshot MANIFEST (committed in
  `REHEARSAL-NOTES.md`; `preflight` re-checked the same).
- After restore: the installed 2.10.0 cache was re-hashed and compared with a sha256 manifest of the
  backup taken just before `restore-cache`: 120 files each side, 0 differing or missing, 0 extra
  (byte-identical manifests). `installed_plugins.json` still reports vibe-check 2.10.0 at that path.

## Restore checks

- `restore-memory`: all three clones' auto-memory restored; the empty `memory/` dir Claude Code
  created in `~/triggarr`'s project at session start was moved aside as evidence by `pre` (and a
  later one at `restore-memory`), never merged back.
- `unfreeze`: the recorded state restored (`Auto-updates: disabled (set by env:
  DISABLE_AUTOUPDATER)`, unchanged; the Codex `check_for_update_on_startup` line removed, the
  config byte-equal to its backup); both `phase49-bak` backups removed.
- `restore-cache`: restored, `parity: restored released 2.10.0` recorded last.
- `close-window`: closed (on its second run, see below); `batchsnap.py drop --repo .` removed the
  rehearsal snapshot and its worktree registration.
- No `~/.b3/phase49-*.env` marker remains; `~/triggarr` is back on `main@4a154be` and clean.

## Defects found and fixed during the rehearsal (runbook/kit only; no plugin behaviour defect)

1. `batchsnap build` refused the snapshot: the suite (about 130 s) outgrew the 120 s cap on the
   suite run. Fixed pre-snapshot (5280202 RED, 97b4eeb `SUITE_TIMEOUT = 900` for the suite run
   only), recorded under 49-04.
2. `a4-check` read the hook path from the tmux pane, but the TUI redraws the pane and its history
   never keeps a subagent's hook-error line (flagged risk 2). The unfixed block STOPPED on a guard
   that had held. Fixed (d4faf44): read from the A4 session's local transcripts, with a new stop
   if any gitguard line names another path; then re-run once on the same smoke: PASS.
3. `close-window` refused because `a4-check` left `rehearsal/a4/` uncommitted. Fixed (f7242b5):
   `a4-check` commits its evidence pathspec-scoped; this rehearsal's evidence was committed with the
   same message, then `close-window` re-run: closed.
4. Not a kit defect: the plan's `batchsnap.py drop --snap <root>` needs `--repo .` (without it the
   snapshot's parent dir is taken as the repo). `drop --repo .` succeeded.

Also noted: the A4 scratch dir is new, so its session first shows Claude Code's workspace-trust
prompt (`Yes, I trust this folder` was selected; the runbook now says so), and the status bar's
`/200k` is the known mislabel; `/context` showed the 1M window (960k free) before the first `/clear`.

## Wall time per step (EDT)

| step | time |
|---|---|
| park-memory, freeze | 20:23:05–20:23:06 |
| resync-cache | 20:23:10 |
| a4-smoke → A4 agent done | 20:23:16 → 20:24 |
| a4-check (unfixed STOP / fixed PASS) | 20:25:17 / 20:26:06 |
| preflight, fresh, launch | 20:26:12–20:26:17 |
| fingerprint, /clear, pre | 20:27:26–20:27:40 |
| deep-review → "Pass 1" card → "Stop here" card → idle | 20:27:46 → 20:35:56 → 20:36:10 → 20:36 (8 m 35 s) |
| post, revert | 20:39:27, 20:39:41 |
| restore-memory, unfreeze, restore-cache | 20:39:57 |
| close-window (refused / closed), drop | 20:40:13 / 20:40:53 |
